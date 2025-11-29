# ❓ Stack Overflow System - 75 Minute Interview Overview

Q&A platform with questions, answers, voting, reputation, tagging, search and answer acceptance. This mirrors the depth and structure of the Airline Management System example while mapping analogous patterns to a social knowledge domain.

**Scale (Interview Assumption)**: 5–50 concurrent active users, 10–100 new questions/day, eventually scalable to millions (discussed, not implemented).  
**Focus**: Core domain modeling, clean lifecycle (ask → answer → vote → accept), reputation updates, extensibility via design patterns.

---

## Core Domain Entities
| Entity | Purpose | Key Relationships |
|--------|---------|------------------|
| **User** | Participant with reputation | Owns Questions & Answers, casts Votes |
| **Question** | Problem statement & discussion root | Has many Answers, Tags, Votes, optional accepted Answer |
| **Answer** | Proposed solution | Belongs to Question & User, can be accepted, has Votes |
| **Tag** | Classification label | Many-to-many with Questions |
| **Vote** | Up/Down feedback | References Voter + Target (Question/Answer) |
| **ReputationEvent** | Internal change log | Generated via Strategy when votes/accepts occur |

---

## Design Patterns Implemented
| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Central coordination, single system state | `StackOverflowSystem.get_instance()` |
| **Strategy** | Pluggable reputation calculation rules | `BasicReputationStrategy` vs future `GamifiedReputationStrategy` |
| **Observer** | Event notification (question posted, answer accepted) | `ConsoleObserver` receives domain events |
| **State** | Explicit lifecycle control | `QuestionStatus` (OPEN → CLOSED), accepted flag on Answer |
| **Factory** | Encapsulated object creation | System factory helpers (`create_user`, `ask_question`) |
| **(Optional) Command** | Encapsulate complex actions (extensible) | Could wrap vote/accept flows (mentioned, not required) |

---

## SOLID Principles Highlight
- **S**: `User` handles only user data & reputation tracking (update via strategy), `Question` focuses on discussion thread state.
- **O**: Add new reputation strategies or observers without modifying core entities.
- **L**: Any `ReputationStrategy` subclass can replace `BasicReputationStrategy` seamlessly.
- **I**: `Observer` interface limited to `update(event, payload)`; no bloated multi-method listener.
- **D**: System depends on `ReputationStrategy` abstraction, not concrete implementation.

---

## 75-Minute Timeline (Guided)
| Time | Phase | What to Deliver |
|------|-------|-----------------|
| 0–5 | Requirements | Clarify scope (features, scale, exclusions) |
| 5–15 | Architecture | Sketch entities, relationships, patterns |
| 15–35 | Core Entities | Implement `User`, `Question`, `Answer`, `Tag`, `Vote` enums & status |
| 35–55 | Business Logic | Ask / Answer / Vote / Accept / Reputation strategy + Observer |
| 55–70 | Integration | Singleton system + demos + search stub |
| 70–75 | Demo & Q&A | Run scenarios; discuss scaling/trade-offs |

---

## Demo Scenarios in `INTERVIEW_COMPACT.py`
1. **Setup**: Users, tags, initial question (events fire)  
2. **Answer Flow**: Multiple answers posted & listed  
3. **Voting & Reputation**: Up/down votes adjust reputation via Strategy  
4. **Accept Answer**: Mark best answer; reputation bonus applied  
5. **Search & Summary**: Keyword search + system summary stats  

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Checklist
- [ ] Can explain each entity & relationship quickly
- [ ] Can map each pattern to domain need (NOT forced)
- [ ] Understand reputation rule constants (+10 Q upvote, +15 A upvote, +30 accepted, -2 downvote impact, -1 voter penalty)
- [ ] Can describe answer acceptance invariants (only author of question, only one accepted)
- [ ] Can explain eventual scalability: search indexing, caching, denormalization, rate limiting
- [ ] Can walk through event flow (ask → observer notify → answer → votes → reputation)

---

## Key Concepts to Explain
**Reputation Strategy**: Centralized rule engine so changing reward mechanics does not touch entity code.  
**Observer Events**: Decouples side-effects (notifications, analytics, audit) from core operations.  
**State Management**: `QuestionStatus` prevents actions (e.g., answering closed question).  
**Accept Logic**: Guard rails ensure only one answer becomes accepted; triggers reputation bonus via strategy.

---

## File Structure (This Module)
| File | Purpose |
|------|---------|
| `README.md` | High-level overview & checklist |
| `START_HERE.md` | Rapid talking points & timeline |
| `75_MINUTE_GUIDE.md` | Deep dive: UML, code fragments, Q&A |
| `INTERVIEW_COMPACT.py` | Working compact implementation + 5 demos |

---

## Tips for Success
✅ Start with relationships before coding lists/dicts  
✅ Keep reputation rules centralized  
✅ Show pattern intent—avoid over-engineering  
✅ Mention real-world scaling (ElasticSearch, Redis, CQRS) as optional future steps  
✅ Use events to hint at analytics pipeline potential  
✅ Clarify anti-features excluded (bounties, edits, comments) to stay focused

---

For deep implementation details see `75_MINUTE_GUIDE.md`.  
For runnable domain demonstration run `python3 INTERVIEW_COMPACT.py`.  
For quick oral prompts reference `START_HERE.md`.

