# Online Blackjack Game - 75 Minute Interview Guide

## System Overview

Multi-player Blackjack game with standard rules, betting, card dealing, and automatic payout calculation.

**Scale**: 10 concurrent tables, 100+ players, real-time gameplay.  
**Focus**: Game rules enforcement, state management, design patterns, card value calculation.

---

## 75-Minute Timeline

| Time | Phase | Deliverable |
|------|-------|-------------|
| 0–5 min | **Requirements Clarification** | Scope & Blackjack rules confirmed |
| 5–15 min | **Architecture & Design Patterns** | System diagram + class skeleton |
| 15–35 min | **Core Entities** | Card, Deck, Hand, Player, Dealer, Game classes |
| 35–55 min | **Game Logic** | deal_cards, hit, stand, bust detection, payout calculation |
| 55–70 min | **System Integration & Observer** | BlackjackTable (Singleton) + notifications |
| 70–75 min | **Demo & Q&A** | Working example + trade-off discussion |

---

## Requirements Clarification (0–5 min)

**Key Questions**:
1. Standard Blackjack rules or variants? → **Standard (dealer hits on 16, stands on 17)**
2. Core features? → **Bet, deal, hit, stand, bust detection, payout**
3. Advanced actions? → **Start with basics (skip split, double, insurance for interview)**
4. Betting limits? → **Configurable min/max**
5. Multiple decks? → **Single deck for demo**

**Scope Agreement**:
- ✅ Standard 52-card deck with shuffle
- ✅ Player betting system
- ✅ Hit/Stand actions
- ✅ Dealer rules (hit < 17, stand >= 17)
- ✅ Blackjack detection (21 with 2 cards)
- ✅ Bust detection (>21)
- ✅ Payout calculation (3:2 for Blackjack, 1:1 for win)
- ❌ Split, double down, insurance, card counting prevention (can discuss)

---

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Singleton** | Single table instance | `BlackjackTable.get_instance()` |
| **Strategy** | Dealer behavior rules | `DealerStrategy` (hit < 17, stand >= 17) |
| **Observer** | Game event notifications | `GameObserver` interface + `ConsoleObserver` |
| **State** | Hand status transitions | Enums: `HandStatus` (ACTIVE → BUST/STAND/WIN) |
| **Factory** | Deck creation | `Deck._initialize_deck()` creates 52 cards |
| **Command** | Player actions | `hit()`, `stand()` as command methods |

---

## Core Classes & Implementation

### Enumerations

```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import random
import threading

# Card Enumerations
class Rank(Enum):
    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class HandStatus(Enum):
    ACTIVE = "active"
    BUST = "bust"
    STAND = "stand"
    BLACKJACK = "blackjack"
    WIN = "win"
    LOSE = "lose"
    PUSH = "push"
```

### 1. Card Class

```python
class Card:
    """Represents a playing card"""
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit
    
    def get_value(self) -> int:
        """Get numeric value of card (Ace=11, Face=10)"""
        if self.rank == Rank.ACE:
            return 11
        elif self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10
        else:
            return int(self.rank.value)
    
    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"
```

### 2. Deck Class

```python
class Deck:
    """Represents a deck of 52 cards"""
    def __init__(self):
        self.cards: List[Card] = []
        self._initialize_deck()
    
    def _initialize_deck(self):
        """Create standard 52-card deck"""
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(rank, suit))
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """Deal one card from the deck"""
        if len(self.cards) > 0:
            return self.cards.pop()
        return None
    
    def cards_remaining(self) -> int:
        return len(self.cards)
```

### 3. Hand Class

```python
class Hand:
    """Represents a hand of cards"""
    def __init__(self):
        self.cards: List[Card] = []
        self.status = HandStatus.ACTIVE
    
    def add_card(self, card: Card):
        """Add a card to the hand"""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """Calculate hand value (handling Aces as 1 or 11)"""
        value = 0
        aces = 0
        
        for card in self.cards:
            value += card.get_value()
            if card.rank == Rank.ACE:
                aces += 1
        
        # Convert Aces from 11 to 1 if busting
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def is_bust(self) -> bool:
        """Check if hand value exceeds 21"""
        return self.get_value() > 21
    
    def is_blackjack(self) -> bool:
        """Check if hand is Blackjack (21 with 2 cards)"""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def __str__(self) -> str:
        cards_str = ", ".join([str(card) for card in self.cards])
        return f"{cards_str} (Value: {self.get_value()})"
```

### 4. Player Class

```python
class Player:
    """Represents a player"""
    def __init__(self, player_id: str, name: str, chips: int = 1000):
        self.player_id = player_id
        self.name = name
        self.chips = chips
        self.hand = Hand()
        self.bet = 0
    
    def place_bet(self, amount: int) -> bool:
        """Place a bet"""
        if amount > self.chips or amount <= 0:
            return False
        self.bet = amount
        self.chips -= amount
        return True
    
    def win(self, multiplier: float = 1.0):
        """Win bet with multiplier (1.0 = even money, 1.5 = blackjack)"""
        winnings = int(self.bet * (1 + multiplier))
        self.chips += winnings
        return winnings
    
    def lose(self):
        """Lose bet (already deducted)"""
        lost = self.bet
        self.bet = 0
        return lost
    
    def push(self):
        """Push (tie) - return bet"""
        self.chips += self.bet
        returned = self.bet
        self.bet = 0
        return returned
    
    def reset_hand(self):
        """Reset hand for new round"""
        self.hand = Hand()
        self.bet = 0
```

### 5. Dealer Class

```python
class Dealer:
    """Represents the dealer"""
    def __init__(self):
        self.hand = Hand()
    
    def should_hit(self) -> bool:
        """Dealer hits on 16, stands on 17"""
        return self.hand.get_value() < 17
    
    def reset_hand(self):
        """Reset hand for new round"""
        self.hand = Hand()
```

### 6. Game Class

```python
class Game:
    """Represents a single game round"""
    def __init__(self, game_id: str, players: List[Player], dealer: Dealer):
        self.game_id = game_id
        self.players = players
        self.dealer = dealer
        self.deck = Deck()
        self.deck.shuffle()
        self.created_at = datetime.now()
    
    def deal_initial_cards(self):
        """Deal 2 cards to each player and dealer"""
        # First card to each player
        for player in self.players:
            card = self.deck.deal_card()
            if card:
                player.hand.add_card(card)
        
        # First card to dealer
        card = self.deck.deal_card()
        if card:
            self.dealer.hand.add_card(card)
        
        # Second card to each player
        for player in self.players:
            card = self.deck.deal_card()
            if card:
                player.hand.add_card(card)
        
        # Second card to dealer
        card = self.deck.deal_card()
        if card:
            self.dealer.hand.add_card(card)
    
    def player_hit(self, player: Player):
        """Player takes a card"""
        card = self.deck.deal_card()
        if card:
            player.hand.add_card(card)
            if player.hand.is_bust():
                player.hand.status = HandStatus.BUST
    
    def player_stand(self, player: Player):
        """Player stands"""
        player.hand.status = HandStatus.STAND
    
    def dealer_play(self):
        """Dealer plays according to rules"""
        while self.dealer.should_hit():
            card = self.deck.deal_card()
            if card:
                self.dealer.hand.add_card(card)
        
        if self.dealer.hand.is_bust():
            self.dealer.hand.status = HandStatus.BUST
        else:
            self.dealer.hand.status = HandStatus.STAND
    
    def determine_winner(self, player: Player) -> str:
        """Determine winner and payout"""
        player_value = player.hand.get_value()
        dealer_value = self.dealer.hand.get_value()
        
        # Player bust
        if player.hand.is_bust():
            player.hand.status = HandStatus.LOSE
            player.lose()
            return "lose"
        
        # Player blackjack
        if player.hand.is_blackjack():
            if self.dealer.hand.is_blackjack():
                player.hand.status = HandStatus.PUSH
                player.push()
                return "push"
            else:
                player.hand.status = HandStatus.WIN
                player.win(1.5)  # Blackjack pays 3:2
                return "blackjack"
        
        # Dealer bust
        if self.dealer.hand.is_bust():
            player.hand.status = HandStatus.WIN
            player.win(1.0)
            return "win"
        
        # Compare values
        if player_value > dealer_value:
            player.hand.status = HandStatus.WIN
            player.win(1.0)
            return "win"
        elif player_value < dealer_value:
            player.hand.status = HandStatus.LOSE
            player.lose()
            return "lose"
        else:
            player.hand.status = HandStatus.PUSH
            player.push()
            return "push"
```

---

## Observer Pattern (Notifications)

```python
class GameObserver(ABC):
    """Observer interface for game events"""
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass

class ConsoleObserver(GameObserver):
    """Console-based observer for demo purposes"""
    def update(self, event: str, data: Dict):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if event == "bet_placed":
            print(f"[{timestamp}] 💰 BET: {data['player']} bet ${data['amount']}")
        elif event == "cards_dealt":
            print(f"[{timestamp}] 🎴 DEAL: {data['player']} → {data['hand']}")
        elif event == "player_hit":
            print(f"[{timestamp}] 👊 HIT: {data['player']} → {data['card']} (Total: {data['value']})")
        elif event == "player_stand":
            print(f"[{timestamp}] ✋ STAND: {data['player']} → {data['value']}")
        elif event == "player_bust":
            print(f"[{timestamp}] 💥 BUST: {data['player']} → {data['value']}")
        elif event == "dealer_play":
            print(f"[{timestamp}] 🎩 DEALER: {data['action']} → {data['hand']}")
        elif event == "game_result":
            print(f"[{timestamp}] 🏆 RESULT: {data['player']} {data['outcome'].upper()} "
                  f"(${data['amount']:+d} chips)")
```

---

## BlackjackTable (Singleton + Controller)

```python
class BlackjackTable:
    """Singleton controller for Blackjack game"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.players: Dict[str, Player] = {}
            self.dealer = Dealer()
            self.current_game: Optional[Game] = None
            self.observers: List[GameObserver] = []
            self.game_count = 0
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'BlackjackTable':
        """Get singleton instance"""
        return BlackjackTable()
    
    def add_observer(self, observer: GameObserver):
        """Subscribe to game events"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: Dict):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(event, data)
    
    def start_new_game(self):
        """Start a new game round"""
        self.game_count += 1
        active_players = [p for p in self.players.values() if p.bet > 0]
        self.dealer.reset_hand()
        self.current_game = Game(f"GAME{self.game_count:03d}", 
                                active_players, self.dealer)
        return self.current_game
    
    def deal_initial_cards(self):
        """Deal initial cards and notify"""
        if not self.current_game:
            return
        
        self.current_game.deal_initial_cards()
        
        for player in self.current_game.players:
            self.notify_observers("cards_dealt", {
                "player": player.name,
                "hand": str(player.hand)
            })
        
        dealer_first_card = str(self.dealer.hand.cards[0])
        self.notify_observers("cards_dealt", {
            "player": "Dealer",
            "hand": f"{dealer_first_card}, ??"
        })
    
    def player_hit(self, player_id: str):
        """Player hits"""
        if not self.current_game:
            return
        
        player = self.players.get(player_id)
        if not player or player.hand.status != HandStatus.ACTIVE:
            return
        
        self.current_game.player_hit(player)
        
        card = player.hand.cards[-1]
        value = player.hand.get_value()
        
        self.notify_observers("player_hit", {
            "player": player.name,
            "card": str(card),
            "value": value
        })
        
        if player.hand.is_bust():
            self.notify_observers("player_bust", {
                "player": player.name,
                "value": value
            })
    
    def dealer_play(self):
        """Dealer plays"""
        if not self.current_game:
            return
        
        self.notify_observers("dealer_play", {
            "action": "reveals",
            "hand": str(self.dealer.hand)
        })
        
        self.current_game.dealer_play()
        
        self.notify_observers("dealer_play", {
            "action": "final",
            "hand": str(self.dealer.hand)
        })
    
    def determine_winners(self):
        """Determine winners and pay out"""
        if not self.current_game:
            return
        
        results = []
        for player in self.current_game.players:
            chips_before = player.chips + player.bet
            outcome = self.current_game.determine_winner(player)
            chips_after = player.chips
            chips_change = chips_after - (chips_before - player.bet)
            
            self.notify_observers("game_result", {
                "player": player.name,
                "outcome": outcome,
                "amount": chips_change
            })
            
            results.append({
                "player": player.name,
                "outcome": outcome,
                "chips": player.chips
            })
        
        return results
```

---

## UML Class Diagram

```
┌────────────────────────────────────────────┐
│      BlackjackTable (Singleton)            │
├────────────────────────────────────────────┤
│ - _instance: BlackjackTable                │
│ - players: Dict[str, Player]               │
│ - dealer: Dealer                           │
│ - current_game: Game                       │
│ - observers: List[GameObserver]            │
├────────────────────────────────────────────┤
│ + get_instance(): BlackjackTable           │
│ + start_new_game(): Game                   │
│ + deal_initial_cards()                     │
│ + player_hit(player_id)                    │
│ + player_stand(player_id)                  │
│ + dealer_play()                            │
│ + determine_winners()                      │
└────────────────────────────────────────────┘
                    │
                    │ manages
                    ▼
        ┌───────────────────┐
        │      Game         │
        ├───────────────────┤
        │ - game_id: str    │
        │ - players: List   │
        │ - dealer: Dealer  │
        │ - deck: Deck      │
        ├───────────────────┤
        │ + deal_initial()  │
        │ + player_hit()    │
        │ + dealer_play()   │
        │ + determine_winner()│
        └───────────────────┘
            │           │
            │           └────────┐
            ▼                    ▼
    ┌───────────┐        ┌──────────┐
    │  Player   │        │  Dealer  │
    ├───────────┤        ├──────────┤
    │ - name    │        │ - hand   │
    │ - chips   │        ├──────────┤
    │ - hand    │        │+should_hit()│
    │ - bet     │        └──────────┘
    ├───────────┤
    │+place_bet()│
    │+ win()    │
    │+ lose()   │
    └───────────┘
         │
         │ HAS-A
         ▼
    ┌────────────┐
    │    Hand    │
    ├────────────┤
    │ - cards    │
    │ - status   │
    ├────────────┤
    │+get_value()│
    │+is_bust()  │
    │+is_blackjack()│
    └────────────┘
         │
         │ CONTAINS
         ▼
    ┌──────────┐
    │   Card   │
    ├──────────┤
    │ - rank   │
    │ - suit   │
    ├──────────┤
    │+get_value()│
    └──────────┘

    ┌──────────────────────────────────────┐
    │  GameObserver (Abstract)             │
    ├──────────────────────────────────────┤
    │ + update(event: str, data: Dict)     │
    └────────────┬─────────────────────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ ConsoleObserver  │
        └──────────────────┘
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you handle Ace valuation (1 or 11)?**

A: Start all Aces as 11. Calculate total hand value. If total > 21 and there are Aces, convert Aces from 11 to 1 one at a time until total <= 21 or no more Aces remain.

```python
def get_value(self) -> int:
    value = 0
    aces = 0
    
    for card in self.cards:
        value += card.get_value()  # Ace initially = 11
        if card.rank == Rank.ACE:
            aces += 1
    
    # Convert Aces from 11 to 1 if busting
    while value > 21 and aces > 0:
        value -= 10  # Convert one Ace from 11 to 1
        aces -= 1
    
    return value
```

**Q2: What's the difference between Blackjack and a regular 21?**

A: Blackjack is 21 with exactly 2 cards (Ace + 10-value card). Regular 21 is achieved with 3+ cards. Blackjack pays 3:2, regular 21 pays 1:1.

**Q3: Why use Observer pattern for game events?**

A: Decouples game logic from UI/logging. Game emits events (bet_placed, card_dealt, bust) and observers react independently. Easy to add new observers (WebSocket, database logging) without modifying game code.

### Intermediate Questions

**Q4: How do you prevent players from hitting after they stand?**

A: Use `HandStatus` enum. Once player stands, status changes from ACTIVE to STAND. All action methods check `if hand.status != HandStatus.ACTIVE: return`. Prevents invalid state transitions.

**Q5: How would you scale this to handle 100+ concurrent tables?**

A: 
- Each table is separate Singleton instance (keyed by table_id)
- Redis for table state persistence
- WebSocket for real-time player actions
- Message queue for async event processing
- Database sharding by table_id
- Load balancer across game servers

**Q6: How to handle dealer rules (hit on 16, stand on 17)?**

A: Implement as Strategy pattern:

```python
class DealerStrategy(ABC):
    @abstractmethod
    def should_hit(self, hand_value: int) -> bool:
        pass

class StandardDealerStrategy(DealerStrategy):
    def should_hit(self, hand_value: int) -> bool:
        return hand_value < 17
```

Easy to test, add variants (hit on soft 17), or A/B test strategies.

### Advanced Questions

**Q7: How do you prevent card counting?**

A: 
- Use multiple decks (6-8 deck shoe)
- Shuffle at random intervals (not just when deck empty)
- Track win rates per player, flag suspicious patterns
- Use cryptographically secure shuffle (not just `random.shuffle`)
- Implement cut card (shuffle when reached)

**Q8: How would you implement split functionality?**

A: When player has pair, create second hand:

```python
def split(self, player: Player):
    if len(player.hand.cards) != 2:
        return False
    if player.hand.cards[0].rank != player.hand.cards[1].rank:
        return False
    
    # Create second hand
    second_hand = Hand()
    second_hand.add_card(player.hand.cards.pop())
    
    # Deal card to each hand
    player.hand.add_card(self.deck.deal_card())
    second_hand.add_card(self.deck.deal_card())
    
    # Track second hand and bet
    player.split_hand = second_hand
    player.split_bet = player.bet
    player.chips -= player.bet
```

**Q9: How to handle payout calculation edge cases?**

A: 
- Player blackjack vs dealer blackjack = PUSH (return bet)
- Player bust = immediate loss (don't wait for dealer)
- Dealer bust = all non-bust players win
- Tie (same value) = PUSH
- Player blackjack pays 3:2 (bet $10, win $15)
- Regular win pays 1:1 (bet $10, win $10)

**Q10: What metrics would you track for this game?**

A: 
**Business**: Games/hour, Average bet size, House edge %, Player retention
**Performance**: Action latency, Shuffle time, Payout calculation time
**Fraud**: Abnormal win rates, Bet pattern analysis, Suspected card counting
**System**: Active tables, Players per table, Memory per table, WebSocket connections

---

## Demo Script

```python
from datetime import datetime

def run_demo():
    print("=" * 70)
    print("ONLINE BLACKJACK GAME - DEMO")
    print("=" * 70)
    
    table = BlackjackTable.get_instance()
    table.add_observer(ConsoleObserver())
    
    # Setup players
    alice = Player("P001", "Alice", 1000)
    bob = Player("P002", "Bob", 1000)
    table.add_player(alice)
    table.add_player(bob)
    
    print("\n[DEMO 1] Betting")
    print("-" * 70)
    alice.place_bet(100)
    bob.place_bet(50)
    
    print("\n[DEMO 2] Deal Initial Cards")
    print("-" * 70)
    table.start_new_game()
    table.deal_initial_cards()
    
    print("\n[DEMO 3] Player Actions")
    print("-" * 70)
    if alice.hand.get_value() < 17:
        table.player_hit("P001")
    table.player_stand("P001")
    
    table.player_stand("P002")
    
    print("\n[DEMO 4] Dealer Plays")
    print("-" * 70)
    table.dealer_play()
    
    print("\n[DEMO 5] Determine Winners & Payout")
    print("-" * 70)
    results = table.determine_winners()
    
    print("\n[SUMMARY]")
    print("-" * 70)
    for result in results:
        print(f"{result['player']}: {result['outcome']} - ${result['chips']} chips")

if __name__ == "__main__":
    run_demo()
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Ace Handling** | Dynamic value calculation (1 or 11); prevent bust when possible |
| **Game Rules** | Dealer hits <17, stands >=17; Blackjack pays 3:2 |
| **Extensibility** | Strategy for dealer rules; Observer for events |
| **State Management** | HandStatus enum prevents invalid actions |
| **Scalability** | Multiple tables; Redis state; WebSocket updates |

---

## Interview Tips

1. **Clarify Blackjack rules early** — Standard vs variants
2. **Explain Ace handling** — Show soft/hard hand logic
3. **Demonstrate patterns** — Strategy for dealer, Observer for events
4. **Handle edge cases** — Dealer/Player both Blackjack, bust detection
5. **Discuss trade-offs** — Single vs multi-deck, betting limits
6. **Demo incrementally** — Show bet → deal → hit → stand → payout
7. **Mention anti-cheating** — Card counting prevention, shuffle frequency
8. **Ask follow-up questions** — "Want to add split/double?" (shows depth)
