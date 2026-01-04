# Stack Overflow — 75-Minute Interview Guide

## Quick Start Overview

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


## 75-Minute Guide

## 1. System Overview
Core Q&A platform slice: users ask questions, others answer, voting adjusts reputation, question author can accept best answer. Tags provide classification; simple keyword search; events broadcast for extensibility.

Excluded (declare early): comments, edits/revisions, bounties, community wiki, rate limiting, full-text indexing (described only), moderation queues.

---

## 2. Core Functional Requirements
| Requirement | Included | Notes |
|-------------|----------|-------|
| Ask Question | ✅ | Title + body + tags |
| Answer Question | ✅ | Multiple answers per question |
| Up/Down Vote Q/A | ✅ | Reputation rules centralized |
| Accept Answer | ✅ | Only by question author; single accepted |
| Reputation Tracking | ✅ | Strategy-based calculations |
| Tagging | ✅ | Many-to-many, stored as names list |
| Search | ✅ (simple) | In-memory substring match |
| Events / Notifications | ✅ | Observer prints to console |
| User Profile (basic) | ✅ | Reputation, counts |

---

## 3. Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns Mapping
| Pattern | Domain Use | Benefit |
|---------|------------|---------|
| Singleton | Central `StackOverflowSystem` | Consistent state, simple memory model |
| Strategy | Reputation calculation | Swap scoring mechanics freely |
| Observer | Publish domain events | Decouple side-effects (analytics, notifications) |
| State | `QuestionStatus` OPEN/CLOSED | Prevent invalid operations |
| Factory | Creation helpers in system | Validation + uniform IDs |

Optional future: Command for complex multi-step operations (vote with audit), Decorator for caching search results.

---

## 4. Enumerations & Constants
```python
from enum import Enum

class QuestionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class VoteValue(Enum):
    UP = 1
    DOWN = -1

# Reputation rule constants (Strategy can override)
REP_Q_UP = 10      # Question author gains
REP_A_UP = 15      # Answer author gains
REP_ACCEPT = 30    # Accepted answer bonus
REP_DOWN_AUTHOR = -2  # Author loses on downvote
REP_DOWN_VOTER = -1   # Cost to cast downvote
```

---

## 5. Core Classes (Condensed)
```python
class User:
    def __init__(self, user_id, name):
        self.id = user_id; self.name = name; self.reputation = 0
        self.questions = []; self.answers = []

class Question:
    def __init__(self, qid, title, body, author, tags):
        self.id=qid; self.title=title; self.body=body; self.author=author
        self.tags=tags; self.answers=[]; self.votes=0; self.accepted_answer_id=None
        self.status=QuestionStatus.OPEN
    def add_answer(self, answer): self.answers.append(answer)

class Answer:
    def __init__(self, aid, body, author, question):
        self.id=aid; self.body=body; self.author=author; self.question=question
        self.votes=0; self.accepted=False

class Vote:
    def __init__(self, vid, user, target_type, target_id, value):
        self.id=vid; self.user=user; self.target_type=target_type
        self.target_id=target_id; self.value=value
```

---

## 6. Reputation Strategy (Strategy Pattern)
```python
from abc import ABC, abstractmethod

class ReputationStrategy(ABC):
    @abstractmethod
    def apply_vote(self, system, vote): pass
    @abstractmethod
    def apply_accept(self, system, question, answer): pass

class BasicReputationStrategy(ReputationStrategy):
    def apply_vote(self, system, vote):
        if vote.target_type == "question":
            q = system.questions[vote.target_id]
            if vote.value == VoteValue.UP: q.author.reputation += REP_Q_UP
            else: q.author.reputation += REP_DOWN_AUTHOR; vote.user.reputation += REP_DOWN_VOTER
        else:  # answer
            a = system.answers[vote.target_id]
            if vote.value == VoteValue.UP: a.author.reputation += REP_A_UP
            else: a.author.reputation += REP_DOWN_AUTHOR; vote.user.reputation += REP_DOWN_VOTER
    def apply_accept(self, system, question, answer):
        answer.author.reputation += REP_ACCEPT
```

---

## 7. Observer Pattern
```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): pass

class ConsoleObserver(Observer):
    def update(self, event, payload):
        print(f"[EVENT] {event.upper():16} | {payload}")
```

Events fired: `question_posted`, `answer_posted`, `vote_cast`, `answer_accepted`, `question_closed`.

---

## 8. Singleton Controller
```python
class StackOverflowSystem:
    _instance = None
    def __new__(cls):
        if not cls._instance: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self, '_init', False): return
        self.users={}; self.questions={}; self.answers={}; self.votes={}
        self.observers=[]; self.reputation_strategy=BasicReputationStrategy(); self._init=True
    def add_observer(self,o): self.observers.append(o)
    def _notify(self,e,p): [o.update(e,p) for o in self.observers]
    def create_user(self, name):
        uid=f"U{len(self.users)+1}"; u=User(uid,name); self.users[uid]=u; return u
    def ask_question(self, user_id, title, body, tags):
        user=self.users[user_id]; qid=f"Q{len(self.questions)+1}"; q=Question(qid,title,body,user,tags)
        user.questions.append(q); self.questions[qid]=q; self._notify("question_posted",{"qid":qid,"author":user.name}); return q
```
```python
    def answer_question(self, user_id, question_id, body):
        user=self.users[user_id]; q=self.questions[question_id]
        aid=f"A{len(self.answers)+1}"; a=Answer(aid,body,user,q); q.add_answer(a)
        user.answers.append(a); self.answers[aid]=a
        self._notify("answer_posted",{"aid":aid,"qid":question_id,"author":user.name}); return a
    def vote(self, user_id, target_type, target_id, up=True):
        voter=self.users[user_id]; vid=f"V{len(self.votes)+1}"; value=VoteValue.UP if up else VoteValue.DOWN
        v=Vote(vid,voter,target_type,target_id,value); self.votes[vid]=v
        # apply counts
        if target_type=="question": self.questions[target_id].votes += value.value
        else: self.answers[target_id].votes += value.value
        self.reputation_strategy.apply_vote(self,v)
        self._notify("vote_cast",{"vid":vid,"target":target_id,"value":value.name}); return v
    def accept_answer(self, user_id, question_id, answer_id):
        q=self.questions[question_id]
        if q.author.id != user_id or q.accepted_answer_id: return False
        a=self.answers[answer_id]; q.accepted_answer_id=answer_id; a.accepted=True
        self.reputation_strategy.apply_accept(self,q,a)
        self._notify("answer_accepted",{"qid":question_id,"aid":answer_id}); return True
    def search(self, keyword):
        k=keyword.lower(); return [q for q in self.questions.values() if k in q.title.lower() or k in q.body.lower()]
```

---

## 9. UML Class Diagram (ASCII)
```
┌────────────────────────────────────────────────────────┐
│                    STACK OVERFLOW CORE                 │
└────────────────────────────────────────────────────────┘
          ┌───────────────────────┐
          │ StackOverflowSystem   │ ◄── Singleton
          ├───────────────────────┤
          │ users{} questions{}   │
          │ answers{} votes{}     │
          │ observers[]           │
          │ reputation_strategy   │
          ├───────────────────────┤
          │ +ask_question()       │
          │ +answer_question()    │
          │ +vote() +accept_answer│
          │ +search()             │
          └──────────┬────────────┘
                     │
   ┌─────────────────┼────────────────┐
   │                 │                │
   ▼                 ▼                ▼
User              Question          Answer
 (reputation)     (answers[])       (accepted flag)
    ▲                ▲                │
    │                │                │
    └──────────── Vote ───────────────┘ (value ±1)

Observer (update) ◄── events fired from system
ReputationStrategy ◄── applied inside vote/accept flows
```

---

## 10. Demo Flow Outline
1. Setup: two users, tags, one question asked.  
2. Answers: both users supply answers (events).  
3. Voting: multiple up/down votes applied; print reputations.  
4. Accept: author accepts best answer; verify bonus.  
5. Search: keyword returns the question; summary stats printed.

---

## 11. Interview Q&A (Prepared Answers)
**Q1: Why a Strategy for reputation?**  To detach scoring rules from domain classes; enables experiments (e.g., seasonal boosts) without touching `User`, `Question`, `Answer`.

**Q2: Prevent multiple accepted answers?**  Store `accepted_answer_id`; guard early: if already set, reject. Only question author ID allowed to accept.

**Q3: Handling abusive downvotes?**  Downvote cost to voter (–1) discourages spam; in production add rate limiting & anomaly detection.

**Q4: Scaling search?**  Replace linear scan with inverted index or external search engine (Elasticsearch). Maintain denormalized question documents (title/body/tags). Observer events feed indexing pipeline.

**Q5: Concurrency concerns?**  Use optimistic locking on vote counters or atomic increments; acceptance would require transactional check (no accepted then set).

**Q6: Prevent vote fraud?**  Store per-user vote history; restrict multiple votes on same target; add delayed aggregation pipeline.

**Q7: Closing questions?**  Add moderator role; transition `QuestionStatus.OPEN → CLOSED`; block `answer_question` if closed.

**Q8: Reputation recalculation?**  Strategy allows batch recompute (e.g., migration) by replaying Vote & Accept events.

**Q9: Observer extension?**  Attach `AnalyticsObserver`, `EmailObserver`; current implementation prints only—swap with async queue publisher.

**Q10: Tag popularity ranking?**  Maintain counter map; update in `ask_question`; eventual caching layer (Redis) for hot tag queries.

**Q11: Security concerns?**  Input sanitization (avoid HTML injection), rate limiting API calls, permission checks on accept/close actions.

**Q12: Why not put reputation logic in User?**  Violates SRP—User should store state, not encode all scoring variants.

---

## 12. Edge Cases & Guards
| Edge Case | Handling |
|-----------|----------|
| Accept non-existent answer | Validate existence before flagging |
| Vote on missing target | Reject & no event fired |
| Downvote own post | Allow or optionally block (clarify) |
| Duplicate tag names | Normalize to lowercase; de-duplicate list |
| Empty search keyword | Return empty or all (clarify) |
| Accept after close | If question closed but unaccepted, still allowed? Clarify policy |

---

## 13. Scaling Discussion Prompts
- Caching: hot question pages (Redis) invalidated on answer/vote events.
- Denormalization: store aggregate counts (votes, answer_count) for fast listing.
- Sharding: by question ID modulo shard count or tag category.
- Event-driven: Observer could push to Kafka; separate consumers update search index & analytics.
- Consistency vs availability: eventual consistency acceptable for reputation totals; strict consistency needed for single accepted answer.

---

## 14. Quick Demo Snippet (from `INTERVIEW_COMPACT.py`)
```python
system = StackOverflowSystem()
system.add_observer(ConsoleObserver())
u1 = system.create_user("Alice"); u2 = system.create_user("Bob")
q = system.ask_question(u1.id, "How to reverse a list in Python?", "Need idiomatic approach", ["python","list"])
a1 = system.answer_question(u2.id, q.id, "Use slicing: lst[::-1]")
system.vote(u1.id, "answer", a1.id, up=True)
system.accept_answer(u1.id, q.id, a1.id)
print(u2.reputation)  # Expect +15 (upvote) +30 (accepted) = 45
```

---

## 15. Final Checklist Before Demo
- [ ] All demos run without exceptions
- [ ] Reputations reflect defined constants
- [ ] Console events appear for each operation
- [ ] Accepted answer invariant holds
- [ ] Search returns expected results
- [ ] You can narrate future improvements (search, caching, moderation)

---

Deliver clarity over breadth: emphasize why each pattern is justified, not merely present.


## Detailed Design Reference

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


## Compact Code

```python
"""Stack Overflow - Interview Compact Implementation
Design Patterns: Singleton | Strategy (Reputation) | Observer | State | Factory
Demonstrates 5 scenarios analogous to Airline example.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# ENUMERATIONS & CONSTANTS
# ============================================================================

class QuestionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class VoteValue(Enum):
    UP = 1
    DOWN = -1

REP_Q_UP = 10
REP_A_UP = 15
REP_ACCEPT = 30
REP_DOWN_AUTHOR = -2
REP_DOWN_VOTER = -1

# ============================================================================
# CORE DOMAIN ENTITIES
# ============================================================================

class User:
    def __init__(self, user_id: str, name: str):
        self.id = user_id
        self.name = name
        self.reputation = 0
        self.questions: List['Question'] = []
        self.answers: List['Answer'] = []
    def __repr__(self):
        return f"User(id={self.id}, rep={self.reputation})"

class Question:
    def __init__(self, qid: str, title: str, body: str, author: User, tags: List[str]):
        self.id = qid
        self.title = title
        self.body = body
        self.author = author
        self.tags = [t.lower() for t in tags]
        self.answers: List['Answer'] = []
        self.votes = 0
        self.accepted_answer_id: Optional[str] = None
        self.status = QuestionStatus.OPEN
        self.created_at = datetime.now()
    def add_answer(self, answer: 'Answer'):
        self.answers.append(answer)
    def __repr__(self):
        return f"Question({self.id}, votes={self.votes}, answers={len(self.answers)})"

class Answer:
    def __init__(self, aid: str, body: str, author: User, question: Question):
        self.id = aid
        self.body = body
        self.author = author
        self.question = question
        self.votes = 0
        self.accepted = False
        self.created_at = datetime.now()
    def __repr__(self):
        return f"Answer({self.id}, votes={self.votes}, accepted={self.accepted})"

class Vote:
    def __init__(self, vid: str, user: User, target_type: str, target_id: str, value: VoteValue):
        self.id = vid
        self.user = user
        self.target_type = target_type  # 'question' or 'answer'
        self.target_id = target_id
        self.value = value
        self.created_at = datetime.now()

# ============================================================================
# REPUTATION STRATEGY (Strategy Pattern)
# ============================================================================

class ReputationStrategy(ABC):
    @abstractmethod
    def apply_vote(self, system: 'StackOverflowSystem', vote: Vote):
        pass
    @abstractmethod
    def apply_accept(self, system: 'StackOverflowSystem', question: Question, answer: Answer):
        pass

class BasicReputationStrategy(ReputationStrategy):
    def apply_vote(self, system: 'StackOverflowSystem', vote: Vote):
        if vote.target_type == "question":
            q = system.questions.get(vote.target_id)
            if not q: return
            if vote.value == VoteValue.UP:
                q.author.reputation += REP_Q_UP
            else:
                q.author.reputation += REP_DOWN_AUTHOR
                vote.user.reputation += REP_DOWN_VOTER
        else:
            a = system.answers.get(vote.target_id)
            if not a: return
            if vote.value == VoteValue.UP:
                a.author.reputation += REP_A_UP
            else:
                a.author.reputation += REP_DOWN_AUTHOR
                vote.user.reputation += REP_DOWN_VOTER
    def apply_accept(self, system: 'StackOverflowSystem', question: Question, answer: Answer):
        answer.author.reputation += REP_ACCEPT

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, payload: Dict):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {event.upper():16} | {payload}")

# ============================================================================
# SINGLETON SYSTEM CONTROLLER
# ============================================================================

class StackOverflowSystem:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self, '_initialized', False): return
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self.answers: Dict[str, Answer] = {}
        self.votes: Dict[str, Vote] = {}
        self.observers: List[Observer] = []
        self.reputation_strategy: ReputationStrategy = BasicReputationStrategy()
        self._initialized = True
    def add_observer(self, obs: Observer):
        self.observers.append(obs)
    def _notify(self, event: str, payload: Dict):
        for o in self.observers: o.update(event, payload)
    def create_user(self, name: str) -> User:
        uid = f"U{len(self.users)+1}"; u = User(uid, name); self.users[uid] = u
        self._notify("user_created", {"user_id": uid, "name": name})
        return u
    def ask_question(self, user_id: str, title: str, body: str, tags: List[str]) -> Optional[Question]:
        user = self.users.get(user_id)
        if not user: return None
        qid = f"Q{len(self.questions)+1}"; q = Question(qid, title, body, user, tags)
        user.questions.append(q); self.questions[qid] = q
        self._notify("question_posted", {"qid": qid, "author": user.name, "title": title})
        return q
    def answer_question(self, user_id: str, question_id: str, body: str) -> Optional[Answer]:
        user = self.users.get(user_id); q = self.questions.get(question_id)
        if not user or not q or q.status != QuestionStatus.OPEN: return None
        aid = f"A{len(self.answers)+1}"; a = Answer(aid, body, user, q); q.add_answer(a)
        user.answers.append(a); self.answers[aid] = a
        self._notify("answer_posted", {"aid": aid, "qid": question_id, "author": user.name})
        return a
    def vote(self, user_id: str, target_type: str, target_id: str, up: bool = True) -> Optional[Vote]:
        voter = self.users.get(user_id)
        if not voter: return None
        if target_type == "question" and target_id not in self.questions: return None
        if target_type == "answer" and target_id not in self.answers: return None
        vid = f"V{len(self.votes)+1}"; value = VoteValue.UP if up else VoteValue.DOWN
        v = Vote(vid, voter, target_type, target_id, value); self.votes[vid] = v
        if target_type == "question": self.questions[target_id].votes += value.value
        else: self.answers[target_id].votes += value.value
        self.reputation_strategy.apply_vote(self, v)
        self._notify("vote_cast", {"vid": vid, "target": target_id, "type": target_type, "value": value.name})
        return v
    def accept_answer(self, user_id: str, question_id: str, answer_id: str) -> bool:
        q = self.questions.get(question_id); a = self.answers.get(answer_id)
        if not q or not a: return False
        if q.author.id != user_id or q.accepted_answer_id is not None or a.question.id != q.id: return False
        q.accepted_answer_id = answer_id; a.accepted = True
        self.reputation_strategy.apply_accept(self, q, a)
        self._notify("answer_accepted", {"qid": question_id, "aid": answer_id})
        return True
    def search(self, keyword: str) -> List[Question]:
        k = keyword.lower()
        return [q for q in self.questions.values() if k in q.title.lower() or k in q.body.lower()]
    def summary(self) -> Dict[str, int]:
        return {
            "users": len(self.users),
            "questions": len(self.questions),
            "answers": len(self.answers),
            "votes": len(self.votes)
        }

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup(system: StackOverflowSystem):
    print("\n" + "="*70); print("DEMO 1: System Setup & Question Posting"); print("="*70)
    system.observers.clear(); system.add_observer(ConsoleObserver())
    u1 = system.create_user("Alice"); u2 = system.create_user("Bob")
    q = system.ask_question(u1.id, "How to reverse a list in Python?", "Looking for idiomatic ways.", ["python", "list"])
    print(f"✅ Users: {u1.id},{u2.id} | Question: {q.id} -> {q.title}")
    return u1, u2, q

def demo_2_answer_flow(system: StackOverflowSystem, u1: User, u2: User, q: Question):
    print("\n" + "="*70); print("DEMO 2: Answer Flow"); print("="*70)
    a1 = system.answer_question(u2.id, q.id, "Use slicing: lst[::-1]")
    a2 = system.answer_question(u1.id, q.id, "Use reversed() and list() for iterator.")
    print(f"✅ Answers posted: {[a.id for a in q.answers]}")
    return a1, a2

def demo_3_voting(system: StackOverflowSystem, q: Question, a1: Answer, a2: Answer, u1: User, u2: User):
    print("\n" + "="*70); print("DEMO 3: Voting & Reputation"); print("="*70)
    system.vote(u2.id, "question", q.id, up=True)   # Bob upvotes Alice's question
    system.vote(u1.id, "answer", a1.id, up=True)     # Alice upvotes Bob's answer
    system.vote(u2.id, "answer", a2.id, up=False)    # Bob downvotes Alice's answer
    print(f"✅ Reputations -> Alice: {u1.reputation}, Bob: {u2.reputation}")

def demo_4_accept(system: StackOverflowSystem, u1: User, q: Question, a1: Answer):
    print("\n" + "="*70); print("DEMO 4: Accept Answer"); print("="*70)
    ok = system.accept_answer(u1.id, q.id, a1.id)
    print(f"✅ Accepted: {ok} | Accepted Answer ID: {q.accepted_answer_id} | Bob Rep: {a1.author.reputation}")

def demo_5_search_summary(system: StackOverflowSystem):
    print("\n" + "="*70); print("DEMO 5: Search & Summary"); print("="*70)
    results = system.search("reverse")
    print(f"✅ Search 'reverse' results: {[q.id for q in results]}")
    print("[SUMMARY]")
    print(system.summary())

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STACK OVERFLOW - 75 MINUTE INTERVIEW DEMOS")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory")
    print("="*70)
    sys = StackOverflowSystem()
    try:
        u1, u2, q = demo_1_setup(sys)
        a1, a2 = demo_2_answer_flow(sys, u1, u2, q)
        demo_3_voting(sys, q, a1, a2, u1, u2)
        demo_4_accept(sys, u1, q, a1)
        demo_5_search_summary(sys)
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("Key Takeaways:")
        print(" • Reputation centralized (Strategy) allows easy rule changes")
        print(" • Observer decouples side-effects from core logic")
        print(" • Single accepted answer invariant enforced")
        print(" • Simple search stub discussable upgrade path")
    except Exception as e:
        print(f"❌ Error during demos: {e}")
        import traceback; traceback.print_exc()

```

## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
