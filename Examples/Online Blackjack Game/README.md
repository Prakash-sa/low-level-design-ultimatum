````markdown
# 🎰 Online Blackjack Game - 75 Minute Interview Guide

## System Overview

Multi-player Blackjack game with betting, card dealing, game rules enforcement, and payout calculation.

**Scale**: 10+ concurrent tables, 100+ players, real-time gameplay.  
**Duration**: 75 minutes | **Focus**: Game rules, state management, design patterns.

---

## Core Entities

| Entity | Purpose | Relationships |
|--------|---------|---------------|
| **Card** | Playing card | Has Rank + Suit |
| **Deck** | 52-card deck | Contains Cards, shuffles |
| **Hand** | Player/Dealer cards | Contains Cards, calculates value |
| **Player** | Game participant | Has Hand + chips + bet |
| **Dealer** | House dealer | Has Hand, follows dealer rules |
| **Game** | Blackjack round | Manages Players + Dealer + Deck |
| **Table** | Game table | Hosts multiple Game rounds |

---

## Design Patterns Implemented

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single table instance | `BlackjackTable.get_instance()` |
| **Strategy** | Dealer/Player behavior | `DealerStrategy` vs `PlayerStrategy` |
| **Observer** | Game event notifications | `GameObserver` for bet, win, bust events |
| **State** | Hand state transitions | `HandStatus` (ACTIVE → BUST/STAND/BLACKJACK) |
| **Factory** | Card/Deck creation | `DeckFactory.create_standard_deck()` |
| **Command** | Player actions | `HitCommand`, `StandCommand`, `DoubleCommand` |

---

## SOLID Principles in Action

- **S**ingle Responsibility: Card manages rank/suit; Hand manages card collection; Game manages round logic
- **O**pen/Closed: Add new strategies (split, surrender) without modifying core game logic
- **L**iskov Substitution: `DealerStrategy` and `PlayerStrategy` are interchangeable
- **I**nterface Segregation: `GameObserver` interface focused on game events
- **D**ependency Inversion: Game depends on `Strategy` abstraction, not concrete classes

---

## 75-Minute Timeline

| Time | Phase | What to Code |
|------|-------|------------|
| 0–5 min | **Requirements** | Clarify rules, betting, payouts |
| 5–15 min | **Architecture** | Sketch class diagram, identify patterns |
| 15–35 min | **Core Entities** | Card, Deck, Hand, Player, Dealer, Game |
| 35–55 min | **Game Logic** | deal_cards, hit, stand, check_bust, calculate_payout |
| 55–70 min | **System Integration** | BlackjackTable (Singleton), Observer, Strategy |
| 70–75 min | **Demo & Q&A** | Run INTERVIEW_COMPACT.py, discuss patterns |

---

## Demo Scenarios (5 included)

1. **Setup**: Create deck, shuffle, initialize players
2. **Betting**: Players place bets
3. **Dealing**: Initial 2 cards to each player and dealer
4. **Playing**: Hit, stand, bust scenarios
5. **Payout**: Determine winners, calculate payouts (2:1 for Blackjack, 1:1 for win)

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Preparation Checklist

- [ ] Understand 6 design patterns and their purpose
- [ ] Memorize Blackjack rules (dealer hits on 16, stands on 17)
- [ ] Know core entity relationships
- [ ] Explain hand value calculation (Ace = 1 or 11)
- [ ] Can walk through game flow: bet → deal → play → payout
- [ ] Practiced explaining trade-offs (single vs multi-deck, betting limits)
- [ ] Ran and understood INTERVIEW_COMPACT.py demos
- [ ] Prepared answers to 10 Q&A scenarios

---

## Key Concepts to Explain

**Singleton Pattern**: Ensures only one `BlackjackTable` instance exists, managing all active games and players.

**Strategy Pattern**: Player decisions (hit/stand) and dealer rules (hit on 16, stand on 17) are implemented as strategies.

**Observer Pattern**: Game events (bet placed, card dealt, bust, win) notify all registered observers for logging/UI updates.

**State Management**: Hand state explicitly modeled (ACTIVE → BUST/STAND/BLACKJACK/WIN/LOSE) preventing invalid actions.

**Card Value**: Ace can be 1 or 11 (soft/hard hands). Hand value calculated dynamically to prevent busting when possible.

---

## File Structure

| File | Purpose |
|------|---------|
| **75_MINUTE_GUIDE.md** | Detailed implementation guide with code + UML + Q&A |
| **INTERVIEW_COMPACT.py** | Working implementation with 5 demo scenarios |
| **README.md** | This file—overview and checklist |
| **START_HERE.md** | Quick reference and talking points |

---

## Tips for Success

✅ **Start with clarifying questions** — Standard Blackjack rules or variants?  
✅ **Sketch card flow** — Draw deck → hand → dealer → player  
✅ **Explain patterns as you code** — Show design thinking  
✅ **Handle edge cases** — Blackjack (21 on first 2 cards), dealer ties, Ace valuation  
✅ **Demo incrementally** — Show bet → deal → hit → stand → payout  
✅ **Discuss trade-offs** — Single deck vs shoe, card counting prevention  
✅ **Mention scaling** — Multiple tables, session management, anti-cheating

````
