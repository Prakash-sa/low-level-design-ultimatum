# ❓ Stack Overflow - Quick Start (5‑Minute Read)

## 🎯 What You’re Building
Minimal Stack Overflow core: ask questions, answer, vote, accept best answer, update reputation, tag & search. Patterns mirror Airline design for consistency.

---

## ⏱️ 75-Minute Timeline (Memorize This Table)
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Scope, exclusions (no comments, edits) |
| 5–15 | Architecture | Entities + pattern mapping sketch |
| 15–35 | Core Entities | User, Question, Answer, Tag, Vote, enums |
| 35–55 | Logic & Patterns | ask/answer/vote/accept + reputation strategy + observer |
| 55–70 | Integration | Singleton system + search + events + demos |
| 70–75 | Demo & Q&A | Run scenarios, explain trade-offs |

---

## 🧱 Core Entities (Flash Cards)
User(id, name, reputation, badges)
Question(id, title, body, author, tags[], answers[], votes, accepted_answer_id, status)
Answer(id, body, author, question_id, votes, accepted_flag)
Tag(name)
Vote(id, user_id, target_type, target_id, value)

Enums: QuestionStatus (OPEN, CLOSED), VoteValue (+1, -1)

---

## 🛠 Patterns Talking Points
Singleton: One `StackOverflowSystem` for consistent in-memory state.
Strategy (Reputation): Central rule engine for scoring; swap without touching entities.
Observer: Domain events (question_posted, answer_posted, vote_cast, answer_accepted) decouple side-effects.
State: `QuestionStatus` prevents answering CLOSED questions; accepted answer invariant.
Factory: Helper methods centralize creation & validation.

---

## 🏁 Demo Scenarios (Run Order)
1. Setup: Users, tags, initial question
2. Answers: Multiple answers posted
3. Voting: Up/down vote effects + reputation updates
4. Accept: Mark best answer, bonus applied
5. Search & Summary: Keyword search + statistics

Run all:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## ✅ Success Checklist
- [ ] Explain each pattern & why it fits
- [ ] Show one accepted answer only
- [ ] Reputation numbers change correctly
- [ ] Observer prints all events
- [ ] Search returns matching question titles
- [ ] Can discuss scaling: indexing, caching, sharding

---

## 💬 Quick Answers
“Why Strategy?” → Swap reputation rules (e.g., seasonal campaigns) without editing entities.  
“Why Observer?” → Enables analytics, notifications pipelines later.  
“Prevent double accept?” → Guard: only question author + only if none accepted.  
“Downvote penalty?” → Author -2; voter -1 (discourages casual negativity).  

---

## 🆘 If You Stall
< 20 min: Implement just User + Question + Answer + ask/answer.  
20–50 min: Add vote + reputation logic; events minimal.  
> 50 min: Demo flows; narrate missing features instead of panic coding.

---

## 🚀 Commands
```bash
python3 INTERVIEW_COMPACT.py      # Run demos
grep -n 'def demo_' INTERVIEW_COMPACT.py  # See demo sections
```

Review deeper design: `75_MINUTE_GUIDE.md`.

Stay focused: deliver core flows + articulate extensibility.

