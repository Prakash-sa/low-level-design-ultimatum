# Stack Overflow - 75 Minute Deep Implementation & Interview Guide

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

## 3. Design Patterns Mapping
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

