````markdown
# 🎰 Online Blackjack Game - Quick Start (5-Min Read)

## 🎯 What You're Building

A multiplayer Blackjack game with:
- ✅ Standard 52-card deck with shuffle
- ✅ Player betting system
- ✅ Card dealing (2 cards each)
- ✅ Hit/Stand player actions
- ✅ Dealer rules (hit on 16, stand on 17)
- ✅ Bust/Blackjack detection
- ✅ Payout calculation (2:1 Blackjack, 1:1 win)

**Scale**: 10 concurrent tables | **Time**: 75 minutes | **Patterns**: 6 core patterns

---

## ⏱️ 75-Minute Timeline

| Time | Phase | Focus | Deliverable |
|------|-------|-------|-------------|
| 0–5 | Requirements | Clarify Blackjack rules | Assumptions confirmed |
| 5–15 | Architecture | Sketch relationships | System diagram |
| 15–35 | Core Entities | Code Card, Deck, Hand, Player, Dealer, Game | Classes with game logic |
| 35–55 | Business Logic | Betting, dealing, hit/stand, bust detection | play_round, calculate_payout |
| 55–70 | System Integration | Singleton + Observer + Strategy | BlackjackTable controller |
| 70–75 | Demo & Q&A | Show 3-5 scenarios running | Discuss patterns & rules |

---

## 🎨 6 Design Patterns (Learn These!)

### 1. **Singleton** (10 min to explain)
```
Why: Single BlackjackTable instance for consistent game state
How: _instance + _lock + __new__ method
Where: BlackjackTable class
```

### 2. **Strategy** (5 min to explain)
```
Why: Dealer and player follow different rules
How: Abstract Strategy + DealerStrategy + PlayerStrategy
Where: dealer.play(DealerStrategy), player.decide(PlayerStrategy)
```

### 3. **Observer** (5 min to explain)
```
Why: Notify UI/logs of game events without tight coupling
How: Observer interface + ConsoleObserver
Where: notify_observers("bet_placed", bet_info)
```

### 4. **State** (5 min to explain)
```
Why: Model hand lifecycle (ACTIVE → BUST/STAND/BLACKJACK)
How: HandStatus enum with transition checks
Where: Hand.bust(), Hand.stand(), Hand.is_blackjack()
```

### 5. **Factory** (3 min)
```
Why: Centralize deck creation
How: DeckFactory.create_standard_deck()
Where: Game initialization
```

### 6. **Command** (3 min)
```
Why: Encapsulate player actions
How: HitCommand, StandCommand, DoubleCommand
Where: player.execute_action(command)
```

---

## 🏗️ Core Classes (Memorize These!)

```python
# Enums
Rank: ACE, TWO, THREE, ..., JACK, QUEEN, KING
Suit: HEARTS, DIAMONDS, CLUBS, SPADES
HandStatus: ACTIVE, BUST, STAND, BLACKJACK, WIN, LOSE, PUSH

# Core Classes
Card(rank, suit) → get_value() (Ace=11, Face=10)
Deck(cards) → shuffle(), deal_card()
Hand(cards) → add_card(), get_value(), is_bust(), is_blackjack()
Player(name, chips) → place_bet(), hit(), stand()
Dealer(hand) → play() (hits on 16, stands on 17)
Game(players, dealer, deck) → deal_initial_cards(), play_round(), determine_winners()

# Strategies
DealerStrategy (abstract)
  └─ StandardDealerStrategy (hit < 17, stand >= 17)

# Observer
GameObserver (abstract) → update(event, data)
  └─ ConsoleObserver (prints events)

# System
BlackjackTable (Singleton) → start_game(), add_player(), play_round()
```

---

## 💬 Quick Talking Points

**"What design patterns did you use?"**
> Singleton for table controller, Strategy for dealer/player behavior, Observer for game events, State for hand lifecycle, Factory for deck creation, Command for player actions.

**"How do you calculate hand value with Aces?"**
> Each Ace starts as 11. If total exceeds 21, convert Aces to 1 one at a time until under 21 or no more Aces. This handles soft/hard hands correctly.

**"How would you scale this?"**
> Multiple tables (shard by table_id), Redis for session state, WebSockets for real-time updates, database for player chips/history, rate limiting for bets.

**"How do you prevent cheating?"**
> Server-side deck shuffling, validate all actions server-side, track bet amounts, detect card counting patterns, use cryptographically secure shuffle.

**"Why Strategy pattern for dealer?"**
> Dealer always follows fixed rules (hit on 16, stand on 17). Strategy pattern allows easy testing and potential for different dealer rules (e.g., hit on soft 17).

---

## 🚀 Quick Commands

```bash
# Run all 5 demo scenarios
python3 INTERVIEW_COMPACT.py

# Expected output:
# DEMO 1: Setup & Deck Creation
# DEMO 2: Betting Phase
# DEMO 3: Dealing Initial Cards
# DEMO 4: Player Actions (Hit/Stand)
# DEMO 5: Dealer Play & Payouts
# ✅ ALL DEMOS COMPLETED SUCCESSFULLY
```

---

## ✅ Success Checklist

- [ ] Can draw UML class diagram from memory
- [ ] Explain each of 6 patterns in < 1 minute
- [ ] Walk through game flow: bet → deal → play → payout
- [ ] Run INTERVIEW_COMPACT.py without errors
- [ ] Answer 3 of 10 interview Q&A questions correctly
- [ ] Explain Ace valuation (1 or 11)
- [ ] Discuss 2 trade-offs (single deck, betting limits)

---

## 🆘 If You Get Stuck

**At 15 min mark** (still designing):
> Focus on core entities first. Patterns can be simplified—just get Card, Hand, Game working.

**At 35 min mark** (mid-implementation):
> Skip advanced features (split, double down). Implement basic hit/stand first.

**At 55 min mark** (need integration):
> Create BlackjackTable as simple controller. Observer can be basic (just print events).

**At 70 min mark** (show something):
> Run demo, explain patterns verbally. Even incomplete code is better than silence.

---

## 📚 Deep Dive Resources

| Resource | Time | Content |
|----------|------|---------|
| **75_MINUTE_GUIDE.md** | 20 min | Complete code + UML + 10 Q&A |
| **INTERVIEW_COMPACT.py** | 5 min | Working implementation |
| **README.md** | 10 min | Overview + checklist |
| **This file** | 5 min | Quick reference |

---

## 🎓 Key Takeaway

> Design patterns aren't about complexity—they're about making code extensible, testable, and maintainable. Show the interviewer you understand Blackjack rules AND clean architecture.

**Ready?** Run `python3 INTERVIEW_COMPACT.py` and then read `75_MINUTE_GUIDE.md`.

````
