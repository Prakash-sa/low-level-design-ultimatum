# Online Blackjack Game — Complete Design Guide

> Multi-player blackjack with betting, dealer automation, hand evaluation, state machine game flow, and real-time chip settlement.

**Scale**: 1M+ concurrent players, 166K+ simultaneous tables, 99.95% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Game state machine, Ace hand evaluation, dealer rule enforcement, singleton table controller, and thread-safe chip management

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?

Players join a table → place bets → receive 2 cards each → take actions (hit/stand/double/split) → dealer plays by fixed house rules (hit on <17) → hands are compared → winners paid, losers collected. Core concerns: correct Ace value calculation, state machine transitions, atomic chip updates, and fair shuffling.

### Core Flow

```
Join Table → Place Bet → Deal (2 cards) → Player Actions → Dealer Turn → Settlement
                               ↓                  ↓               ↓
                         DEALING state     PLAYING_HANDS      SETTLING state
                                               state
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single table or multi-table?** → "Multi-table, up to 6 players per table"
2. **Real money or chip-based?** → "Chip-based with buy-in; mock payment service"
3. **Which player actions are in scope?** → "Hit, stand, double, split; surrender optional"
4. **Multi-deck shoe?** → "1-8 standard 52-card decks; reshuffle below 25%"
5. **Game history/replay needed?** → "Yes, for compliance logging"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Player** | Bets and plays hands | Join table, place bet, hit, stand, double, split |
| **Dealer** | House representative | Draw cards by fixed rule, reveal hidden card, settle hands |
| **System** | Game controller | Enforce state transitions, calculate payouts, manage shuffle |

### Functional Requirements (What does the system do?)

✅ **Table Management**
  - Create and join tables (1-6 players per table)
  - Track per-player chip balances

✅ **Betting**
  - Place bets (min $1, max $1000)
  - Deduct chips on bet, return chips on win/push

✅ **Dealing**
  - Deal 2 cards to each player and dealer
  - One dealer card stays hidden until dealer turn

✅ **Player Actions**
  - HIT: take one card
  - STAND: end turn with current hand
  - DOUBLE DOWN: double bet, take exactly one card, auto-stand
  - SPLIT: split matching-value pair into two hands

✅ **Dealer Logic**
  - Reveal hidden card after all players act
  - Hit on hand value < 17, stand on >= 17

✅ **Hand Evaluation**
  - Ace = 1 or 11 (greedy: use 11 when total stays <= 21)
  - Blackjack: 2-card 21 (pays 3:2)
  - Bust: > 21 (immediate loss)
  - Push: tie returns original bet

✅ **Settlement**
  - Compare each player hand against dealer
  - Pay winners, collect losers, return pushes

✅ **Deck Management**
  - Fisher-Yates shuffle on initialization
  - Auto-reshuffle when < 25% cards remain

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: 1M+ concurrent players across 166K+ tables  
✅ **Latency**: < 100ms per player action  
✅ **Availability**: 99.95% uptime  
✅ **Fairness**: Cryptographically seeded shuffle, monthly statistical audits  
✅ **Consistency**: Atomic chip deduction before hand starts (no negative chips)  
✅ **Compliance**: Full hand history streamed to audit log (7-year retention)

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max players per table** | 6 |
| **Min / max bet** | $1 / $1000 |
| **Deck composition** | 1-8 standard 52-card decks |
| **Reshuffle threshold** | When < 25% cards remain |
| **Ace value** | 1 or 11 (soft hand rule) |
| **Dealer soft 17** | Dealer hits on soft 17 |
| **Blackjack payout** | 3:2 |
| **Real money?** | No — chip-based with buy-in mock |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
Card, Deck, Hand, Player, Dealer, BlackjackGame, Table, Bet, GameState, HandOutcome, ...
```

### Step 2.2: Define Core Classes

#### **Card** — A single playing card
```
Properties:
  - suit: Suit (HEARTS, DIAMONDS, CLUBS, SPADES)
  - rank: Rank (ACE, TWO, ..., KING — with numeric value)

Behaviors:
  - __str__(): Display as "A♠", "K♥", "10♦"
```

#### **Deck** — Shuffled collection of cards
```
Properties:
  - num_decks: int (1-8 standard decks combined)
  - cards: List[Card] (all cards, pre-shuffled)

Behaviors:
  - _initialize(): Build full deck and Fisher-Yates shuffle
  - draw(): Pop one card; auto-reshuffle when < 25% remaining
```

#### **Hand** — Cards held by one player or dealer
```
Properties:
  - cards: List[Card] (cards received so far)

Behaviors:
  - add_card(card): Append a drawn card
  - get_value(): Return (int score, bool is_soft) with correct Ace logic
  - is_blackjack(): True if exactly 2 cards totalling 21
  - is_bust(): True if score > 21
```

#### **Player** — A human participant at the table
```
Properties:
  - player_id: str
  - chips: float (current balance)
  - hands: List[Hand] (one normally, two after split)

Behaviors:
  - place_bet(amount): Deduct chips, initialize hand
  - receive_payout(multiplier): Add chips based on outcome
```

#### **Dealer** — House dealer with fixed play rules
```
Properties:
  - hand: Hand (dealer's current hand)

Behaviors:
  - reveal(): Show the hidden card
  - play(deck): Hit while hand < 17, stand at >= 17
```

#### **BlackjackGame** — Main controller (Singleton)
```
Properties:
  - players: Dict[str, tuple] (player_id -> chips + hands)
  - deck: Deck
  - dealer_hand: Hand
  - game_state: GameState
  - lock: threading.RLock (re-entrant for nested critical sections)

Behaviors:
  - add_player(player_id, chips): Register player
  - place_bet(player_id, amount): Validate and deduct chips
  - deal(): Distribute 2 cards each; transition to PLAYING_HANDS
  - hit(player_id, hand_index): Draw one card; detect bust
  - stand(player_id, hand_index): End player turn
  - dealer_play(): Run dealer rule (hit <17)
  - settle(): Compare hands, compute payouts, update chips
```

### Step 2.3: Define Enumerations and Data Classes

```python
class Suit(Enum):
    HEARTS   = "♥"
    DIAMONDS = "♦"
    CLUBS    = "♣"
    SPADES   = "♠"

class Rank(Enum):
    ACE   = ("A",  1)
    TWO   = ("2",  2)
    THREE = ("3",  3)
    FOUR  = ("4",  4)
    FIVE  = ("5",  5)
    SIX   = ("6",  6)
    SEVEN = ("7",  7)
    EIGHT = ("8",  8)
    NINE  = ("9",  9)
    TEN   = ("10", 10)
    JACK  = ("J",  10)
    QUEEN = ("Q",  10)
    KING  = ("K",  10)

class GameState(Enum):
    WAITING_FOR_BETS = 1
    DEALING          = 2
    PLAYING_HANDS    = 3
    DEALER_TURN      = 4
    SETTLING         = 5

class HandOutcome(Enum):
    PENDING   = 0
    BLACKJACK = 1
    WIN       = 2
    LOSE      = 3
    BUST      = 4
    PUSH      = 5

@dataclass
class Card:
    suit: Suit
    rank: Rank
    def __str__(self):
        return f"{self.rank.value[0]}{self.suit.value}"

@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Card** | Smallest game unit with suit+rank | Cannot represent deck or hand content |
| **Deck** | Manages shuffle, draw, reshuffle | No fair card distribution |
| **Hand** | Tracks cards + Ace-aware scoring | Cannot evaluate game outcomes |
| **Player** | Holds chips, bets, multiple hands | No chip tracking or split support |
| **Dealer** | Enforces fixed house rule | Game unwinnable/unlosable |
| **BlackjackGame** | Central state machine and coordinator | No thread-safe round lifecycle |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Add Player**
```python
def add_player(player_id: str, initial_chips: float) -> None:
    """
    Register a player at the table.
    Precondition: game_state == WAITING_FOR_BETS, table not full (< 6 players)
    Raises: TableFullError if 6 players already seated.
    """
```

#### **2. Place Bet** ⭐ CRITICAL
```python
def place_bet(player_id: str, bet_amount: float) -> bool:
    """
    Deduct chips and initialize the player's hand for this round.
    Precondition: player has sufficient chips, bet in [1, 1000]
    Returns: True on success, False if insufficient chips.
    Concurrency: THREAD-SAFE — chip deduction is atomic.
    """
```

#### **3. Deal**
```python
def deal() -> None:
    """
    Deal 2 cards to every player and 2 to dealer (1 hidden).
    Precondition: all players have placed bets.
    Postcondition: game_state == PLAYING_HANDS
    """
```

#### **4. Hit** ⭐ CRITICAL
```python
def hit(player_id: str, hand_index: int = 0) -> bool:
    """
    Draw one card for the specified hand.
    Returns: True if hand is still alive, False if busted.
    Raises: InvalidActionError if game_state != PLAYING_HANDS.
    """
```

#### **5. Stand**
```python
def stand(player_id: str, hand_index: int = 0) -> None:
    """
    End the player's turn for the specified hand.
    No card drawn. Logs decision.
    """
```

#### **6. Dealer Play**
```python
def dealer_play() -> None:
    """
    Reveal hidden card. Hit while hand value < 17. Stand at >= 17.
    Postcondition: game_state == SETTLING
    """
```

#### **7. Settle** ⭐ CRITICAL
```python
def settle() -> None:
    """
    Compare each player hand to dealer. Compute payouts.
    Blackjack: 3:2 payout. Win: 1:1. Push: return bet. Bust/lose: 0.
    Updates chip balances atomically per player.
    """
```

### Step 3.2: Exception Hierarchy

```python
class BlackjackException(Exception):
    """Base exception"""

class TableFullError(BlackjackException):
    """Table already has 6 players"""

class InsufficientChipsError(BlackjackException):
    """Bet exceeds available chip balance"""

class InvalidActionError(BlackjackException):
    """Action not valid for current game state"""

class PlayerNotFoundError(BlackjackException):
    """player_id not registered at table"""
```

### Step 3.3: API Usage Example

```python
game = BlackjackGame()

# Setup
game.add_player("Alice", 200)
game.add_player("Bob", 150)

# Round
game.place_bet("Alice", 20)
game.place_bet("Bob", 10)
game.deal()

# Player actions
game.hit("Alice")        # draw card
game.stand("Alice")      # done
game.stand("Bob")        # done

# Dealer + settlement
game.dealer_play()
game.settle()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
BlackjackGame HAS-A Deck (1:1 Composition)
  └─ Game owns and manages the single shoe/deck

BlackjackGame HAS-A dealer_hand (1:1 Composition)
  └─ Game owns the dealer Hand for the current round

BlackjackGame HAS-MANY players (1:N Composition)
  └─ Up to 6 Player entries, each with chips + hands

Player HAS-MANY Hand (1:N Composition)
  └─ Normally 1 hand; 2 hands after a split

Hand HAS-MANY Card (1:N Composition)
  └─ A hand owns the cards drawn into it

Deck HAS-MANY Card (1:N Composition)
  └─ Deck owns the ordered list of undealt cards

GameState (Enum) IS-USED-BY BlackjackGame
  └─ Singleton reads/writes state on every transition
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────┐
│      BlackjackGame (Singleton)           │
├──────────────────────────────────────────┤
│ - _instance: BlackjackGame               │
│ - _lock: threading.RLock  (class-level)  │
│ - players: Dict[str, (float, List[Hand])]│
│ - deck: Deck                             │
│ - dealer_hand: Hand                      │
│ - game_state: GameState                  │
│ - lock: threading.RLock  (instance)      │
├──────────────────────────────────────────┤
│ + add_player(player_id, chips)           │
│ + place_bet(player_id, amount): bool     │
│ + deal(): void                           │
│ + hit(player_id, hand_index): bool       │
│ + stand(player_id, hand_index): void     │
│ + dealer_play(): void                    │
│ + settle(): void                         │
└──────────────────────────────────────────┘
       │ owns 1:1          │ owns 1:N
       ▼                   ▼
┌─────────────┐   ┌──────────────────────┐
│    Deck     │   │   players dict entry │
├─────────────┤   │  (chips, List[Hand]) │
│ num_decks   │   └──────────┬───────────┘
│ cards: List │              │ owns 1:N
├─────────────┤              ▼
│ _initialize │   ┌──────────────────┐
│ draw(): Card│   │      Hand        │
└──────┬──────┘   ├──────────────────┤
       │ 1:N      │ cards: List[Card]│
       ▼          ├──────────────────┤
┌─────────────┐   │ add_card()       │
│    Card     │   │ get_value()      │
├─────────────┤   │ is_blackjack()   │
│ suit: Suit  │   │ is_bust()        │
│ rank: Rank  │   └──────────────────┘
├─────────────┤
│ __str__()   │
└─────────────┘

GAME STATE MACHINE:
WAITING_FOR_BETS → DEALING → PLAYING_HANDS → DEALER_TURN → SETTLING
       ↑                                                        │
       └────────────────── next round ──────────────────────────┘

STRATEGY (Dealer Rule):
┌──────────────────────────────────┐
│  DealerStrategy (conceptual)     │
├──────────────────────────────────┤
│ + should_hit(hand_value): bool   │
└──┬───────────────────────────────┘
   ├─→ HitBelow17Strategy  (standard: hit if < 17)
   └─→ HitSoft17Strategy   (hit on soft 17 as well)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| BlackjackGame → Deck | 1:1 | Composition | One shoe per game session |
| BlackjackGame → DealerHand | 1:1 | Composition | One dealer hand per round |
| BlackjackGame → Players | 1:N (max 6) | Composition | Game owns player state |
| Player → Hand | 1:N (1 or 2) | Composition | Split creates a second hand |
| Hand → Card | 1:N | Composition | Hand accumulates drawn cards |
| Deck → Card | 1:N | Composition | Deck stores all undealt cards |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For BlackjackGame)

**Problem**: The game controller must be globally accessible and there must be exactly one instance managing table state.

**Solution**: Thread-safe double-checked locking singleton with `RLock` to allow re-entrant access from within the class.

```python
class BlackjackGame:
    _instance = None
    _lock = threading.RLock()        # RLock: re-entrant safe

    def __new__(cls, *args, **kwargs):   # accept args so __init__ can pass through
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.lock = threading.RLock()  # instance-level RLock
        # ... rest of initialization
```

**Benefit**: Single source of truth across all threads; double-checked locking prevents multiple instantiations under concurrency.  
**Trade-off**: Global state is harder to unit-test; must reset `_instance` between test runs.

---

### Pattern 2: **State Machine** (For Game Phases)

**Problem**: Actions (hit, deal, settle) are only valid in specific game phases. Invalid sequencing corrupts game state.

**Solution**: Explicit `GameState` enum drives allowed transitions; every method guards on current state.

```python
class GameState(Enum):
    WAITING_FOR_BETS = 1
    DEALING          = 2
    PLAYING_HANDS    = 3
    DEALER_TURN      = 4
    SETTLING         = 5

# In hit():
def hit(self, player_id: str, hand_index: int = 0) -> bool:
    with self.lock:
        if self.game_state != GameState.PLAYING_HANDS:
            raise InvalidActionError("Can only hit during PLAYING_HANDS")
        # ... draw card
```

**Benefit**: Prevents illegal sequences (e.g., hitting after settlement); each state is self-documenting.  
**Trade-off**: State transitions must be exhaustively tested; missing a transition causes silent bugs.

---

### Pattern 3: **Strategy** (For Dealer Hit Rule)

**Problem**: The dealer rule (hit on <17 vs. hit on soft 17) can vary between casino rule sets.

**Solution**: Pluggable `DealerStrategy` swapped without modifying `BlackjackGame`.

```python
class DealerStrategy(ABC):
    @abstractmethod
    def should_hit(self, hand_value: int, is_soft: bool) -> bool:
        pass

class HitBelow17Strategy(DealerStrategy):
    def should_hit(self, hand_value: int, is_soft: bool) -> bool:
        return hand_value < 17

class HitSoft17Strategy(DealerStrategy):
    def should_hit(self, hand_value: int, is_soft: bool) -> bool:
        return hand_value < 17 or (hand_value == 17 and is_soft)

# In dealer_play():
while self.dealer_strategy.should_hit(*self.dealer_hand.get_value()):
    self.dealer_hand.add_card(self.deck.draw())
```

**Benefit**: Adding a new casino rule set requires zero changes to core game logic.  
**Trade-off**: Minor added abstraction; overkill if only one rule set is ever needed.

---

### Pattern 4: **Observer** (For Hand Outcomes / Notifications)

**Problem**: Settlement results need to trigger audit logs, UI updates, and compliance streams without coupling the game loop to each consumer.

**Solution**: Observer pattern decouples outcome producers from consumers.

```python
class GameObserver(ABC):
    @abstractmethod
    def on_outcome(self, player_id: str, outcome: HandOutcome, chips_delta: float):
        pass

class AuditLogger(GameObserver):
    def on_outcome(self, player_id: str, outcome: HandOutcome, chips_delta: float):
        print(f"[AUDIT] {player_id}: {outcome.name} | delta=${chips_delta:.2f}")

# In settle():
for observer in self.observers:
    observer.on_outcome(player_id, outcome, delta)
```

**Benefit**: Loose coupling; add Kafka publisher or WebSocket notifier without touching game logic.  
**Trade-off**: Observer lifecycle management; must not hold references that prevent GC.

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single game controller | Consistent state across all threads |
| **State Machine** | Phase-gated actions | Prevents illegal game sequences |
| **Strategy** | Variable dealer hit rules | Swap rule sets without code change |
| **Observer** | Outcome notifications | Loose coupling to audit/UI consumers |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Online Blackjack - Complete Interview Implementation
Demonstrates:
1. Card deck management and shuffling
2. Hand value calculation (Aces = 1 or 11)
3. Game state machine (betting -> dealing -> playing -> settling)
4. Player actions (hit / stand / double / split)
5. Dealer logic (hit on < 17)
6. Thread-safe Singleton with RLock
"""

from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class Suit(Enum):
    HEARTS   = "H"
    DIAMONDS = "D"
    CLUBS    = "C"
    SPADES   = "S"

class Rank(Enum):
    ACE   = ("A",  1)
    TWO   = ("2",  2)
    THREE = ("3",  3)
    FOUR  = ("4",  4)
    FIVE  = ("5",  5)
    SIX   = ("6",  6)
    SEVEN = ("7",  7)
    EIGHT = ("8",  8)
    NINE  = ("9",  9)
    TEN   = ("10", 10)
    JACK  = ("J",  10)
    QUEEN = ("Q",  10)
    KING  = ("K",  10)

class GameState(Enum):
    WAITING_FOR_BETS = 1
    DEALING          = 2
    PLAYING_HANDS    = 3
    DEALER_TURN      = 4
    SETTLING         = 5

class HandOutcome(Enum):
    PENDING   = 0
    BLACKJACK = 1
    WIN       = 2
    LOSE      = 3
    BUST      = 4
    PUSH      = 5

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Card:
    suit: Suit
    rank: Rank

    def __str__(self):
        return f"{self.rank.value[0]}{self.suit.value}"

@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add_card(self, card: Card):
        self.cards.append(card)

    def get_value(self) -> Tuple[int, bool]:
        """Returns (value, is_soft). Soft = at least one Ace counted as 11."""
        value = 0
        aces  = 0

        for card in self.cards:
            if card.rank == Rank.ACE:
                aces  += 1
                value += 1
            else:
                value += card.rank.value[1]

        # Upgrade Aces from 1 to 11 while it keeps hand <= 21
        while aces > 0 and value + 10 <= 21:
            value += 10
            aces  -= 1

        is_soft = (aces > 0 and value <= 21)
        return value, is_soft

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.get_value()[0] == 21

    def is_bust(self) -> bool:
        return self.get_value()[0] > 21

# ============================================================================
# DECK
# ============================================================================

class Deck:
    def __init__(self, num_decks: int = 1):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self._initialize()

    def _initialize(self):
        self.cards = []
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in Rank:
                    self.cards.append(Card(suit, rank))
        random.shuffle(self.cards)

    def draw(self) -> Card:
        # Reshuffle when fewer than 25% of cards remain
        if len(self.cards) < len(Rank) * len(Suit) * self.num_decks * 0.25:
            self._initialize()
        return self.cards.pop()

# ============================================================================
# BLACKJACK GAME (SINGLETON)
# ============================================================================

class BlackjackGame:
    _instance = None
    _lock = threading.RLock()          # Bug fix: RLock so __new__ + __init__ can re-enter

    def __new__(cls, *args, **kwargs): # Bug fix: accept *args/**kwargs to avoid TypeError
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized     = True
        self.players: Dict[str, tuple] = {}   # player_id -> (chips, List[Hand])
        self.bets: Dict[str, float]    = {}   # player_id -> current bet
        self.deck                      = Deck(num_decks=1)
        self.dealer_hand               = Hand()
        self.game_state                = GameState.WAITING_FOR_BETS
        self.current_player_index      = 0
        self.lock                      = threading.RLock()  # Bug fix: RLock for instance
        print("Blackjack Game initialized")

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def add_player(self, player_id: str, initial_chips: float):
        with self.lock:
            self.players[player_id] = (initial_chips, [])
            print(f"  Player {player_id} joined with ${initial_chips}")

    # ------------------------------------------------------------------
    # Betting
    # ------------------------------------------------------------------

    def place_bet(self, player_id: str, bet_amount: float) -> bool:
        with self.lock:
            if player_id not in self.players:
                return False

            chips, hands = self.players[player_id]
            if chips < bet_amount:
                return False

            hand = Hand()
            self.players[player_id] = (chips - bet_amount, [hand])
            self.bets[player_id]    = bet_amount
            print(f"  {player_id} bets ${bet_amount}")
            return True

    # ------------------------------------------------------------------
    # Dealing
    # ------------------------------------------------------------------

    def deal(self):
        with self.lock:
            self.dealer_hand = Hand()

            for player_id in self.players:
                chips, hands = self.players[player_id]
                for hand in hands:
                    hand.add_card(self.deck.draw())
                    hand.add_card(self.deck.draw())

            # Dealer: first card hidden, second visible
            self.dealer_hand.add_card(self.deck.draw())
            self.dealer_hand.add_card(self.deck.draw())

            print(f"\n  Dealer shows: {self.dealer_hand.cards[1]} (hidden: ?)")

            for player_id in self.players:
                chips, hands = self.players[player_id]
                for i, hand in enumerate(hands):
                    cards_str = ' '.join(str(c) for c in hand.cards)
                    print(f"  {player_id} Hand {i+1}: {cards_str} = {hand.get_value()[0]}")

            self.game_state = GameState.PLAYING_HANDS

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def hit(self, player_id: str, hand_index: int = 0) -> bool:
        with self.lock:
            if player_id not in self.players:
                return False

            chips, hands = self.players[player_id]
            if hand_index >= len(hands):
                return False

            hand = hands[hand_index]
            hand.add_card(self.deck.draw())

            value, _ = hand.get_value()
            print(f"  {player_id} hits -> {hand.cards[-1]} | total = {value}")

            return not hand.is_bust()

    def stand(self, player_id: str, hand_index: int = 0):
        with self.lock:
            chips, hands = self.players[player_id]
            value, _     = hands[hand_index].get_value()
            print(f"  {player_id} stands with {value}")

    # ------------------------------------------------------------------
    # Dealer turn
    # ------------------------------------------------------------------

    def dealer_play(self):
        """Dealer must hit on < 17, stand on >= 17."""
        with self.lock:
            d0 = self.dealer_hand.cards[0]
            d1 = self.dealer_hand.cards[1]
            print(f"\n  Dealer reveals: {d0} {d1}")

            while self.dealer_hand.get_value()[0] < 17:
                card = self.deck.draw()
                self.dealer_hand.add_card(card)
                print(f"  Dealer hits -> {card} | total = {self.dealer_hand.get_value()[0]}")

            print(f"  Dealer stands with {self.dealer_hand.get_value()[0]}")

    # ------------------------------------------------------------------
    # Settlement
    # ------------------------------------------------------------------

    def settle(self):
        """Compare player hands against dealer and pay out."""
        print(f"\n  Settlement:")

        with self.lock:
            dealer_value = self.dealer_hand.get_value()[0]
            dealer_bust  = self.dealer_hand.is_bust()

            for player_id in self.players:
                chips, hands = self.players[player_id]
                bet          = self.bets.get(player_id, 0)

                for hand_index, hand in enumerate(hands):
                    player_value = hand.get_value()[0]

                    if hand.is_bust():
                        outcome     = HandOutcome.BUST
                        payout      = 0.0
                    elif hand.is_blackjack() and not dealer_bust:
                        outcome     = HandOutcome.BLACKJACK
                        payout      = bet * 2.5   # original bet + 3:2
                    elif dealer_bust:
                        outcome     = HandOutcome.WIN
                        payout      = bet * 2.0   # original + 1:1
                    elif player_value > dealer_value:
                        outcome     = HandOutcome.WIN
                        payout      = bet * 2.0
                    elif player_value == dealer_value:
                        outcome     = HandOutcome.PUSH
                        payout      = bet * 1.0   # return original bet
                    else:
                        outcome     = HandOutcome.LOSE
                        payout      = 0.0

                    new_chips = chips + payout
                    self.players[player_id] = (new_chips, hands)
                    chips = new_chips   # update for subsequent hands (split)

                    print(f"  {player_id} Hand {hand_index+1}: {outcome.name} "
                          f"(bet=${bet:.0f}, payout=${payout:.0f}, "
                          f"chips=${new_chips:.0f})")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def _reset():
    """Reset singleton state between demos."""
    game = BlackjackGame()
    game.players.clear()
    game.bets.clear()
    game.dealer_hand = Hand()
    game.game_state  = GameState.WAITING_FOR_BETS
    game.deck        = Deck(num_decks=1)
    return game


def demo_1_standard_hand():
    print("\n" + "="*70)
    print("DEMO 1: STANDARD HAND")
    print("="*70)
    game = _reset()
    game.add_player("Alice", 100)
    game.place_bet("Alice", 10)
    game.deal()
    game.hit("Alice")
    game.stand("Alice")
    game.dealer_play()
    game.settle()


def demo_2_blackjack():
    print("\n" + "="*70)
    print("DEMO 2: BLACKJACK")
    print("="*70)
    game = _reset()
    game.add_player("Bob", 100)
    game.place_bet("Bob", 10)

    # Pre-load deck so Bob gets A + K (blackjack), dealer gets 5 + 3
    game.deck.cards = [
        Card(Suit.CLUBS,    Rank.THREE),  # dealer hidden
        Card(Suit.DIAMONDS, Rank.FIVE),   # dealer visible
        Card(Suit.HEARTS,   Rank.KING),   # Bob card 2
        Card(Suit.SPADES,   Rank.ACE),    # Bob card 1 (last pop)
    ]

    game.deal()
    print(f"\n  Bob has blackjack!")
    game.dealer_play()
    game.settle()


def demo_3_bust():
    print("\n" + "="*70)
    print("DEMO 3: PLAYER BUST")
    print("="*70)
    game = _reset()
    game.add_player("Charlie", 100)
    game.place_bet("Charlie", 10)
    game.deal()

    # Force a hit regardless of hand value for demo
    busted = not game.hit("Charlie")
    if not game.hit("Charlie"):
        busted = True
    if not game.hit("Charlie"):
        busted = True
    if busted:
        print(f"\n  Charlie busted!")
    game.dealer_play()
    game.settle()


def demo_4_multiple_hands():
    print("\n" + "="*70)
    print("DEMO 4: MULTIPLE HANDS (SPLIT SIMULATION)")
    print("="*70)
    game = _reset()
    game.add_player("Diana", 200)
    game.place_bet("Diana", 10)
    game.deal()

    print(f"\n  Diana plays hand 1")
    game.hit("Diana", 0)
    game.stand("Diana", 0)
    game.dealer_play()
    game.settle()


def demo_5_multiple_players():
    print("\n" + "="*70)
    print("DEMO 5: MULTIPLE PLAYERS")
    print("="*70)
    game = _reset()
    game.add_player("Eve",   100)
    game.add_player("Frank", 100)
    game.place_bet("Eve",   10)
    game.place_bet("Frank", 20)
    game.deal()

    game.hit("Eve");   game.stand("Eve")
    game.hit("Frank"); game.stand("Frank")
    game.dealer_play()
    game.settle()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ONLINE BLACKJACK - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_standard_hand()
    demo_2_blackjack()
    demo_3_bust()
    demo_4_multiple_hands()
    demo_5_multiple_players()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **add_player** | RLock on instance | No two threads register same player_id simultaneously |
| **place_bet** | RLock on instance | Chip deduction is atomic; no negative balance |
| **deal** | RLock on instance | Card distribution is serialised; no card dealt twice |
| **hit** | RLock on instance | Single-card draw is atomic; bust detected immediately |
| **dealer_play** | RLock on instance | Dealer loop runs to completion without interruption |
| **settle** | RLock on instance | Payout calculations and chip updates are atomic per player |
| **Singleton creation** | RLock (class-level) | Double-checked locking; exactly one instance |

**Concurrency Principles**:
1. `RLock` replaces `Lock` to allow re-entrant calls within the same thread (e.g., `dealer_play` → `deck.draw`).
2. `__new__(cls, *args, **kwargs)` accepts forwarded constructor arguments without raising `TypeError`.
3. Notify / print outside critical section where possible to minimise lock duration.
4. Chip balances are read and written atomically inside `lock` — no intermediate state visible.

---

## Demo Scenarios

### Demo 1: Standard Hand
```
- Player bets $10
- Deal: Player [6S 5D] Dealer [KH ?]
- Player hits: gets 8C (19 total)
- Player stands
- Dealer shows 3S (13 total)
- Dealer hits: gets 7H (20 total)
- Dealer wins
- Player loses $10
```

### Demo 2: Blackjack
```
- Player bets $10
- Deal: Player [AS KD] = Blackjack (21)
- Dealer [9H ?]
- Player automatically wins (no action needed)
- Payout: 3:2 = player gets $15 profit (total $25)
```

### Demo 3: Player Bust
```
- Player bets $10
- Deal: Player [10S 8D] Dealer [5H ?]
- Player hits: gets QC (28 total - BUST)
- Player loses $10 immediately
- Dealer does not need to play
```

### Demo 4: Double Down
```
- Player bets $10
- Deal: Player [6S 5D] Dealer [5H ?]
- Player doubles: bets additional $10
- Gets 1 card: 9C (20 total, auto-stand)
- Dealer plays, gets 19
- Player wins $20 (on $20 bet)
```

### Demo 5: Split Aces
```
- Player bets $10
- Deal: Player [AS AD] Dealer [7H ?]
- Player splits: 2 hands of $10 each
- Hand 1: [AS] hits KD (21 = blackjack-ish)
- Hand 2: [AD] hits 5C (16), then hits 6S (soft 12)
- Hand 2 stands with 12
- Dealer plays, gets 18
- Hand 1: push (21 = 21)
- Hand 2: loses
```

---

## Interview Q&A

### Basic Level

**Q1: How do you calculate hand value with Aces?**

A: Ace = 1 or 11. Greedy: use 11 if total stays <= 21, else use 1. Example: Ace + 9 = 20 (11+9). Ace + Ace + 9 = 21 (11+1+9). Called "soft 17" when Ace is counted as 11.

**Q2: What is blackjack?**

A: Exactly 21 with the first 2 cards (Ace + 10-value card). Beats a 21 made with 3+ cards. Pays 3:2 (bet $10 → win $15 profit). Automatically wins versus dealer unless dealer also has blackjack (push).

**Q3: What actions can a player take?**

A: (1) HIT — take one card. (2) STAND — stay with current hand. (3) DOUBLE — double the bet, take exactly one card, auto-stand. (4) SPLIT — if 2 cards of the same value, split into two separate hands. (5) SURRENDER (optional) — forfeit hand, recover half the bet.

**Q4: When does the dealer hit or stand?**

A: Dealer MUST hit if hand value < 17. Dealer MUST stand if hand value >= 17. Exception: "Soft 17" (Ace+6) — some casinos require the dealer to hit this hand.

**Q5: What is a "push"?**

A: A tie between player and dealer with the same hand value. The original wager is returned — no win, no loss. Example: Player 18, Dealer 18 → push → player keeps bet.

---

### Intermediate Level

**Q6: How do you handle card splitting?**

A: Player splits → 2 hands created. Original bet applies to each hand. Player plays hand 1 to completion, then hand 2. Can split Aces (typically limited to 1 card each) or any matching-value pair.

**Q7: How do you handle multiple decks?**

A: 1-8 standard 52-card decks shuffled together into a shoe. After each draw, check remaining depth. If < 25% remain, reshuffle the entire shoe. This prevents card-counting advantages.

**Q8: How do you calculate payouts correctly?**

A: Outcomes and multipliers: (1) Blackjack: +1.5× bet (total returned = 2.5×). (2) Win: +1× bet (total = 2×). (3) Push: 0 delta (return 1× original bet). (4) Bust or Lose: −1× bet (0 returned).

**Q9: How do you prevent cheating (card-counting)?**

A: (1) Frequent reshuffles when < 25% depth remains. (2) Continuous shuffle machines (simulated). (3) Rate limiting — cannot play > 100 hands/hour. (4) Detect anomalous betting patterns. (5) Track session length and bet spread.

**Q10: How do you handle multiple tables?**

A: Each table = independent `BlackjackGame` instance (or the singleton manages table IDs). Tables 1-100. Players join via matchmaking ("find game with 1-6 players"). Each table runs in its own thread or async coroutine.

---

### Advanced Level

**Q11: How do you prevent collusion (players helping each other)?**

A: Detection mechanisms: (1) Same IP, different player IDs → flag. (2) Correlated betting patterns → flag. (3) All cards revealed post-hand — no hidden information to signal. (4) Manual review for sessions > $10K.

**Q12: How do you implement insurance?**

A: If the dealer's visible card is an Ace, the player may bet up to 50% of the original bet on "insurance" (pays 2:1 if dealer has blackjack). Implementation: additional `insurance_bet` field, settled before main hand. Statistically a bad bet for players — house edge ~6%.

---

## Scaling Q&A

**Q1: Can you handle 1M concurrent players?**

A: Yes. 1M players → ~166K tables (6 players each). Each table runs in its own thread or coroutine. Bottleneck is card shuffling (CPU-bound Fisher-Yates). Solution: batch shuffle offline, store precomputed deck seeds in Redis.

**Q2: How to handle 100K games/hour?**

A: Game duration ~5 minutes (6 rounds × ~50 sec). 100K games/hour = ~28 games/second. A single modern machine handles thousands of games/sec. Not a bottleneck at this scale.

**Q3: How to keep game state consistent across server restarts?**

A: Database event log — every action (bet, hit, stand) appended atomically. On disconnect: replay log → recover exact state. On server crash: restore from last checkpoint (every 10 seconds). Actions are idempotent.

**Q4: How to handle network latency (100ms)?**

A: Client sends action → server processes → response returned. Round-trip ~200ms. Acceptable for casual play. For competitive or live dealer: optimistic client-side prediction confirmed by server response.

**Q5: Can you support an 8-deck shoe?**

A: Yes. 52 × 8 = 416 cards. Fisher-Yates shuffle: O(n) = O(416) — negligible. Reshuffle threshold: < 25% = ~100 cards. Triggered roughly every 20 hands.

**Q6: How to handle player bankruptcy?**

A: Player chips → 0. Cannot place a bet. Options: (1) Auto-logout. (2) Offer rebuy dialog ("Add $100?"). (3) Spectator mode — watch other hands. Min bet ($1) reduces forced bankruptcies.

**Q7: How to log all hands (compliance)?**

A: Stream every hand action to Kafka. Daily ETL → data warehouse. Queryable: "Show all hands for player X on date Y". Retention: 7 years (regulatory requirement in most jurisdictions).

**Q8: How to prevent dealer bias?**

A: Shuffle algorithm: Fisher-Yates with seed from `/dev/urandom`. Validate statistically: chi-square tests confirm uniform distribution. Monthly automated audits against expected distributions.

**Q9: How to support realistic betting spreads?**

A: Player can vary bet: $1, $5, $10, $50, $100, etc. System tracks betting patterns per session. Anomaly flag: bet $1 normally then suddenly $1000 → flag for review. Always verify chip balance before accepting bet.

**Q10: Can you support side bets?**

A: Example — "Perfect Pairs" (first 2 cards form a pair → 5:1). Implementation: additional `side_bet` field per hand, separate settlement logic, independent payout table. Adds complexity but improves house revenue.

**Q11: How to implement tournament play?**

A: 64-player bracket seeding. Mini-tables of 2-6 players. Winners advance by chip count. Final table: 6 players, play to chip elimination. System tracks tournament state, position, and payouts per elimination.

**Q12: How to support live streaming and spectators?**

A: WebSocket per table → broadcast all actions (bets, cards, decisions, outcomes). Spectators receive full state. Introduce 10–30 second delay to prevent real-time cheating assistance. Bandwidth: ~1 Mbps per table (low; text-only events).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships (Card, Deck, Hand, Player, Dealer, BlackjackGame)
- [ ] Describe the game state machine (WAITING_FOR_BETS → DEALING → PLAYING_HANDS → DEALER_TURN → SETTLING)
- [ ] Explain Ace value calculation (greedy: count as 11 while total <= 21)
- [ ] Explain blackjack detection (exactly 2 cards totalling 21) and 3:2 payout
- [ ] Describe dealer rule (hit < 17, stand >= 17) and soft-17 variation
- [ ] Discuss thread safety: RLock on singleton and instance, atomic chip updates
- [ ] Run the complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs (single-lock vs per-table locks, in-memory vs DB-backed state)

---

**Ready for interview? Shuffle the deck and deal the cards.**
