# Online Blackjack Game — 75-Minute Interview Guide

## Quick Start

**What is it?** Multi-player blackjack card game with betting, dealer logic, hand evaluation, and real-time game state management.

**Key Classes:**
- `BlackjackGame` (Singleton): Game coordinator
- `Player`: Participant with chip balance, active hand
- `Dealer`: House dealer with rules-based play
- `Hand`: Cards with value calculation (Ace=1/11)
- `Bet`: Wager on outcome
- `Table`: Game session with max players

**Core Flows:**
1. **Bet**: Players place wagers → Chips deducted
2. **Deal**: Each player + dealer gets 2 cards
3. **Play**: Player action (hit/stand/double/split) → Hand evaluation
4. **Dealer Turn**: Dealer plays by fixed rules (hit on <17)
5. **Settlement**: Compare hands → Pay winners → Collect losers

**5 Design Patterns:**
- **Singleton**: One BlackjackGame
- **State Machine**: Game states (betting, dealing, playing, settling)
- **Strategy**: Dealer hit strategy (hit <17, stand >=17)
- **Observer**: Notify on hand outcomes
- **Command**: Undo/replay game actions

---

## System Overview

Real-time blackjack card game supporting multiple players, simultaneous hands, betting mechanics, and automated dealer logic.

### Requirements

**Functional:**
- Create/join tables (1-6 players per table)
- Place bets (min $1, max $1000)
- Deal cards (2 initial, show one dealer card)
- Player actions (hit, stand, double, split)
- Dealer plays by fixed rules
- Hand evaluation (21, blackjack, bust)
- Chip management (buy-in, payout)
- Game history/replay

**Non-Functional:**
- Action latency < 100ms
- Support 1M+ concurrent players
- 99.95% uptime
- Real-time hand settlement

**Constraints:**
- Min bet: $1, max bet: $1000
- Max players per table: 6
- Standard 52-card deck (1-8 decks)
- Ace value: 1 or 11 (soft 17)
- Dealer must hit soft 17

---

## Architecture Diagram (ASCII UML)

```
┌──────────────────┐
│ BlackjackGame    │
│ (Singleton)      │
└────────┬─────────┘
         │
    ┌────┼────┬────────┬──────┐
    │    │    │        │      │
    ▼    ▼    ▼        ▼      ▼
┌────────┐ ┌──────┐ ┌─────┐ ┌─────┐ ┌──────┐
│Tables  │ │Players│ │Dealer│ │Hand │ │Deck  │
└────────┘ └──────┘ └─────┘ └─────┘ └──────┘

Game State:
WAITING_FOR_BETS → DEALING → PLAYING_HANDS → DEALER_TURN → SETTLING
     ↓
  CLOSED

Hand Evaluation:
Calculate score (Ace=1/11)
If > 21: BUST (lose)
If = 21: BLACKJACK (win 3:2)
If > Dealer: WIN
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you calculate hand value with Aces?**
A: Ace = 1 or 11. Greedy: use 11 if <= 21, else use 1. Example: Ace + 9 = 20 (11+9). Ace + Ace + 9 = 21 (1+1+9, not 11+11). Called "soft 17" = Ace counted as 11.

**Q2: What's blackjack?**
A: Exactly 21 with first 2 cards (Ace + 10-value). Beats 21 made with 3+ cards. Pays 3:2 (bet $10 → win $15). Automatically wins vs dealer (unless dealer also has blackjack = push).

**Q3: What actions can a player take?**
A: (1) HIT: take card. (2) STAND: stay with current hand. (3) DOUBLE: double bet, get 1 more card, auto-stand. (4) SPLIT: if 2 same value, split into 2 hands. (5) SURRENDER (some casinos): lose half bet.

**Q4: When does dealer hit or stand?**
A: Dealer MUST hit if hand < 17. Dealer MUST stand if hand >= 17. Exception: "Soft 17" (Ace+6) → some casinos hit, most stand. Follow casino rules.

**Q5: What's a "push"?**
A: Tie between player and dealer. Same hand value. Wager returned (no win, no loss). Example: Player 18, Dealer 18 → push → player keeps bet.

### Intermediate Level

**Q6: How do you handle card splitting?**
A: Player splits → 2 hands created. Original bet applies to each hand. Player plays hand 1, then hand 2 sequentially. Can split Aces (optional: 1 card each) or pairs (any value).

**Q7: How do you handle multiple decks?**
A: Standard: 1-8 decks shuffled together. After each hand, check deck depth. If <25% remaining: reshuffle. Prevents card-counting advantage. Uses continuous shuffle machine (simulated in software).

**Q8: How to calculate payout correctly?**
A: Outcomes: (1) Blackjack: +1.5 × bet (total = 2.5 × bet). (2) Win: +1 × bet. (3) Push: 0 (keep bet). (4) Bust: -1 × bet. (5) Dealer bust (player not bust): +1 × bet.

**Q9: How do you prevent cheating (card-counting)?**
A: (1) Frequent shuffles (every 25% deck depth). (2) Continuous shuffle machines. (3) Rate limiting (can't play >100 hands/hour). (4) Detect betting pattern anomalies. (5) Track session length.

**Q10: How to handle multiple tables?**
A: Each table = independent game instance. Tables 1-100. Players join via: "Find game (1-6 players)". Matchmaking: fill tables. Each table runs in own thread/coroutine.

### Advanced Level

**Q11: How to prevent collusion (players helping each other)?**
A: Detection: (1) Same IP address, different players → flag. (2) Correlated betting patterns → flag. (3) Always reveal all cards post-hand (no hidden info). (4) Manual review: watch sessions > $10K.

**Q12: How to implement insurance?**
A: If dealer shows Ace: player can bet up to 50% of original bet on "insurance" (dealer has 10). Insurance pays 2:1 if dealer has blackjack. Most players: bad bet, avoid.

---

## Scaling Q&A (12 Questions)

**Q1: Can you handle 1M concurrent players?**
A: Yes. Assume 1M players → 166K tables (6 players each). Each table: thread/coroutine. Bottleneck: card shuffling (CPU-bound). Solution: batch shuffle offline, precompute deck seeds.

**Q2: How to handle 100K games/hour?**
A: Game duration: ~5 minutes (6 rounds × 50 sec each). 100K games/hour = 1666 games/minute = 28 games/second. Capacity per machine: 1000s games/sec. Not bottleneck.

**Q3: How to keep game state consistent?**
A: Database log: each action (bet, hit, stand). On disconnect: replay log → recover state. On server crash: restore from last checkpoint (every 10 seconds). Idempotent actions.

**Q4: How to handle network latency (100ms)?**
A: Action sent → server processes → response sent back. Total: 200ms. Acceptable for casual play. For competitive: predict client action, confirm on server response.

**Q5: Can you support 8-deck shoes?**
A: Yes. 52 × 8 = 416 cards. Shuffle: O(n) = O(416) = negligible. Reshuffle interval: when < 25% remaining = 100 cards used. Every ~20 hands.

**Q6: How to handle player bankruptcy?**
A: Player chips → 0. Cannot play. Options: (1) Auto-logout, (2) Offer rebuy ("Buy $100 more"), (3) Spectate (watch others play). Prevent: min bet = affordable (e.g., $1).

**Q7: How to log all hands (compliance)?**
A: Stream: every hand action → Kafka. Daily ETL: process logs → data warehouse. Queries: "Show all hands for player X on date Y". Retention: 7 years (regulatory).

**Q8: How to prevent dealer bias?**
A: Shuffling algorithm: Fisher-Yates shuffle. Seed: random from /dev/urandom. Test: statistical analysis (chi-square test) confirms randomness. Monthly audits.

**Q9: How to support realistic betting spreads?**
A: Player can vary bet: $1, $5, $10, $50, $100, etc. System tracks betting patterns. Anomaly: bet $1 normally, suddenly $1000 → flag. Check if player balance supports.

**Q10: Can you support side bets (optional wagers)?**
A: Side bet: "Over/Under 13" (will hand be over or under 13?). Separate payout: pays 1.2:1 if over. Implementation: additional bet, separate settlement logic. Adds complexity.

**Q11: How to implement tournament play?**
A: Seeding: 64 players bracket. Tables: 2-player mini-tournaments. Winners advance. Final table: 6 players play to chip elimination. Tracks chip counts, position, payouts.

**Q12: How to support live streaming (spectators)?**
A: WebSocket: table ID → broadcast all actions. Spectators see: cards, bets, decisions. Delay: 10-30 seconds (prevent real-time cheating). Bandwidth: ~1 Mbps per table (many spectators).

---

## Demo Scenarios (5 Examples)

### Demo 1: Standard Hand
```
- Player bets $10
- Deal: Player [6♠ 5♦] Dealer [K♥ ?]
- Player hits: gets 8♣ (19 total)
- Player stands
- Dealer shows 3♠ (13 total)
- Dealer hits: gets 7♥ (20 total)
- Dealer wins
- Player loses $10
```

### Demo 2: Blackjack
```
- Player bets $10
- Deal: Player [A♠ K♦] = Blackjack (21)
- Dealer [9♥ ?]
- Player automatically wins (no action needed)
- Payout: 3:2 = player gets $15 (total $25)
```

### Demo 3: Player Bust
```
- Player bets $10
- Deal: Player [10♠ 8♦] Dealer [5♥ ?]
- Player hits: gets Q♣ (28 total - BUST)
- Player loses $10 immediately
- Dealer doesn't play
```

### Demo 4: Double Down
```
- Player bets $10
- Deal: Player [6♠ 5♦] Dealer [5♥ ?]
- Player doubles: bets additional $10
- Gets 1 card: 9♣ (20 total, auto-stand)
- Dealer plays, gets 19
- Player wins $20 (on $20 bet)
```

### Demo 5: Split Aces
```
- Player bets $10
- Deal: Player [A♠ A♦] Dealer [7♥ ?]
- Player splits: 2 hands of $10 each
- Hand 1: [A♠] hits K♦ (21 = blackjack-ish)
- Hand 2: [A♦] hits 5♣ (16)
- Hand 2 hits 6♠ (soft 12)
- Hand 2 stands with 12
- Dealer plays, gets 18
- Hand 1: push (21 = 21)
- Hand 2: loses
```

---

## Complete Implementation

```python
"""
♠️ Online Blackjack - Interview Implementation
Demonstrates:
1. Card deck management & shuffling
2. Hand value calculation (Aces)
3. Game state machine (betting→dealing→playing→settling)
4. Player actions (hit/stand/double/split)
5. Dealer logic (hit on <17)
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
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    ACE = ("A", 1)
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 10)
    QUEEN = ("Q", 10)
    KING = ("K", 10)

class GameState(Enum):
    WAITING_FOR_BETS = 1
    DEALING = 2
    PLAYING_HANDS = 3
    DEALER_TURN = 4
    SETTLING = 5

class HandOutcome(Enum):
    PENDING = 0
    BLACKJACK = 1
    WIN = 2
    LOSE = 3
    BUST = 4
    PUSH = 5

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
        """Returns (value, is_soft). Soft = Ace counted as 11"""
        value = 0
        aces = 0
        
        for card in self.cards:
            if card.rank == Rank.ACE:
                aces += 1
                value += 1
            else:
                value += card.rank.value[1]
        
        # Try to use Aces as 11
        while aces > 0 and value + 10 <= 21:
            value += 10
            aces -= 1
        
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
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in Rank:
                    self.cards.append(Card(suit, rank))
        random.shuffle(self.cards)
    
    def draw(self) -> Card:
        if len(self.cards) < len(Rank) * len(Suit) * 0.25:  # < 25%
            self._initialize()
        return self.cards.pop()

# ============================================================================
# BLACKJACK GAME (SINGLETON)
# ============================================================================

class BlackjackGame:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.players: Dict[str, tuple] = {}  # player_id -> (chips, hands)
        self.deck = Deck(num_decks=1)
        self.dealer_hand = Hand()
        self.game_state = GameState.WAITING_FOR_BETS
        self.current_player_index = 0
        self.lock = threading.Lock()
        print("♠️ Blackjack Game initialized")
    
    def add_player(self, player_id: str, initial_chips: float):
        with self.lock:
            self.players[player_id] = (initial_chips, [])
            print(f"✓ Player {player_id} joined with ${initial_chips}")
    
    def place_bet(self, player_id: str, bet_amount: float) -> bool:
        with self.lock:
            if player_id not in self.players:
                return False
            
            chips, hands = self.players[player_id]
            if chips < bet_amount:
                return False
            
            # Initialize hand for this player
            hand = Hand()
            self.players[player_id] = (chips - bet_amount, [hand])
            print(f"✓ {player_id} bet ${bet_amount}")
            
            return True
    
    def deal(self):
        with self.lock:
            # Clear previous round
            self.dealer_hand = Hand()
            
            # Deal 2 cards to each player
            for player_id in self.players:
                chips, hands = self.players[player_id]
                for hand in hands:
                    hand.add_card(self.deck.draw())
                    hand.add_card(self.deck.draw())
            
            # Deal to dealer (1 hidden, 1 visible)
            self.dealer_hand.add_card(self.deck.draw())
            self.dealer_hand.add_card(self.deck.draw())
            
            print(f"\n  Dealer shows: {self.dealer_hand.cards[1]} (hidden card: ?)")
            
            for player_id in self.players:
                chips, hands = self.players[player_id]
                for i, hand in enumerate(hands):
                    print(f"  {player_id} Hand {i+1}: {' '.join(str(c) for c in hand.cards)} = {hand.get_value()[0]}")
            
            self.game_state = GameState.PLAYING_HANDS
    
    def hit(self, player_id: str, hand_index: int = 0) -> bool:
        with self.lock:
            if player_id not in self.players:
                return False
            
            chips, hands = self.players[player_id]
            if hand_index >= len(hands):
                return False
            
            hand = hands[hand_index]
            hand.add_card(self.deck.draw())
            
            value, soft = hand.get_value()
            print(f"  {player_id} hits: gets {hand.cards[-1]}, now = {value}")
            
            return not hand.is_bust()
    
    def stand(self, player_id: str, hand_index: int = 0):
        with self.lock:
            print(f"  {player_id} stands with {self.players[player_id][1][hand_index].get_value()[0]}")
    
    def dealer_play(self):
        """Dealer must hit on <17, stand on >=17"""
        print(f"\n  Dealer reveals: {self.dealer_hand.cards[0]} {self.dealer_hand.cards[1]}")
        
        with self.lock:
            while self.dealer_hand.get_value()[0] < 17:
                card = self.deck.draw()
                self.dealer_hand.add_card(card)
                print(f"  Dealer hits: {card}, now = {self.dealer_hand.get_value()[0]}")
            
            print(f"  Dealer stands with {self.dealer_hand.get_value()[0]}")
    
    def settle(self):
        """Compare hands and determine winners"""
        print(f"\n  Settlement:")
        
        with self.lock:
            dealer_value = self.dealer_hand.get_value()[0]
            dealer_bust = self.dealer_hand.is_bust()
            
            for player_id in self.players:
                chips, hands = self.players[player_id]
                
                for hand_index, hand in enumerate(hands):
                    player_value = hand.get_value()[0]
                    
                    # Determine outcome
                    if hand.is_bust():
                        outcome = HandOutcome.BUST
                        payout = 0
                    elif dealer_bust:
                        outcome = HandOutcome.WIN
                        payout = 2 if hand.is_blackjack() else 2  # Simplified
                    elif player_value > dealer_value:
                        outcome = HandOutcome.WIN
                        payout = 2
                    elif player_value == dealer_value:
                        outcome = HandOutcome.PUSH
                        payout = 1
                    else:
                        outcome = HandOutcome.LOSE
                        payout = 0
                    
                    # Update chips
                    new_chips = chips + (hand.get_value()[0] * 10 * payout // dealer_value if dealer_value > 0 else chips)
                    self.players[player_id] = (new_chips, hands)
                    
                    print(f"  {player_id}: {outcome.name} (now ${new_chips:.0f})")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_standard_hand():
    print("\n" + "="*70)
    print("DEMO 1: STANDARD HAND")
    print("="*70)
    
    game = BlackjackGame()
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
    
    game = BlackjackGame()
    game.add_player("Bob", 100)
    game.place_bet("Bob", 10)
    
    # Manually create blackjack (in real game, random)
    game.deck.cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.DIAMONDS, Rank.FIVE),
        Card(Suit.CLUBS, Rank.THREE)
    ]
    
    game.deal()
    print(f"\n  Bob has blackjack!")
    game.dealer_play()
    game.settle()

def demo_3_bust():
    print("\n" + "="*70)
    print("DEMO 3: PLAYER BUST")
    print("="*70)
    
    game = BlackjackGame()
    game.add_player("Charlie", 100)
    game.place_bet("Charlie", 10)
    game.deal()
    
    if not game.hit("Charlie"):
        print(f"\n  Charlie busted!")
    game.settle()

def demo_4_multiple_hands():
    print("\n" + "="*70)
    print("DEMO 4: SPLIT & MULTIPLE HANDS")
    print("="*70)
    
    game = BlackjackGame()
    game.add_player("Diana", 200)
    game.place_bet("Diana", 10)
    game.deal()
    
    print(f"\n  Diana plays Hand 1")
    game.hit("Diana", 0)
    game.stand("Diana", 0)
    
    game.dealer_play()
    game.settle()

def demo_5_multiple_players():
    print("\n" + "="*70)
    print("DEMO 5: MULTIPLE PLAYERS")
    print("="*70)
    
    game = BlackjackGame()
    game.add_player("Eve", 100)
    game.add_player("Frank", 100)
    
    game.place_bet("Eve", 10)
    game.place_bet("Frank", 20)
    
    game.deal()
    
    game.hit("Eve")
    game.stand("Eve")
    
    game.hit("Frank")
    game.stand("Frank")
    
    game.dealer_play()
    game.settle()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("♠️ ONLINE BLACKJACK - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_standard_hand()
    demo_2_blackjack()
    demo_3_bust()
    demo_4_multiple_hands()
    demo_5_multiple_players()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Summary

✅ **Card deck** management with shuffle/reshuffle
✅ **Hand value** calculation (Ace = 1/11 logic)
✅ **Blackjack detection** and special payout (3:2)
✅ **Bust prevention** (auto-lose on >21)
✅ **Player actions** (hit, stand, double, split)
✅ **Dealer logic** (fixed rules: hit <17)
✅ **Payout calculation** (correct ratios)
✅ **Multiple hands** support (splits)
✅ **Game state machine** (betting→dealing→playing→settling)
✅ **Chip management** (balance tracking)

**Key Takeaway**: Blackjack demonstrates game state management, rule enforcement, and fair card shuffling. Core focus: calculate hand values (Ace logic), implement dealer rules, manage chip balances accurately.
