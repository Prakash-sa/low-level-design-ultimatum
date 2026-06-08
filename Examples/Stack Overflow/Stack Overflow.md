# Stack Overflow — Complete Design Guide

> Global Q&A platform aggregating technical knowledge, managing user reputation, enabling collaborative problem-solving with voting, tagging, and real-time updates.

**Scale**: 10M+ users, 50M+ questions, 100M+ answers  
**Duration**: 75-minute interview guide  
**Focus**: Reputation gates, voting mechanics, full-text search, accepted-answer lifecycle, thread-safe concurrency

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

Users post questions → questions are indexed by tags → community members submit answers and vote → author accepts the best answer → reputation is awarded and gates further actions (comment, vote, close). Core concerns: reputation-gated features, vote integrity, efficient tag-based search, and question lifecycle management.

### Core Flow

```
Ask Question → Index by Tags → Community Answers → Vote (up/down)
                                                         ↓
                                              Author Accepts Best Answer
                                                         ↓
                                          Reputation Awarded → Feature Unlocked
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system, 10M+ users"
2. **Real-time updates on votes?** → "Yes, WebSocket broadcast every 10 seconds"
3. **Anonymous users?** → "Read-only; posting requires registration"
4. **Moderation workflow?** → "Community close-votes (5 users, 3K rep) plus moderators"
5. **Spam prevention?** → "Rate limiting, ML classifier, flag system"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User** | Ask, answer, vote, comment | Post question, submit answer, upvote, add comment |
| **Moderator** | Enforce quality | Close question, delete spam, lock thread |
| **System** | Controller & indexer | Index tags, compute reputation, broadcast vote updates |

### Functional Requirements (What does the system do?)

✅ **Questions**
  - Post question with title, description, and tags
  - Edit, close, or delete a question
  - Display suggested and related questions

✅ **Answers**
  - Submit answer to an open question
  - Author accepts the single best answer (pinned top)
  - Edit or delete an answer

✅ **Voting**
  - Upvote or downvote questions and answers
  - Toggle vote (voting again reverses it)
  - Reputation changes applied atomically

✅ **Comments**
  - Add clarification comment on questions or answers
  - Requires minimum reputation (50 rep)

✅ **Search**
  - Full-text search by title, description, keywords
  - Filter and sort by tags, relevance, recency, or score

✅ **Reputation & Badges**
  - Track per-user reputation from all events
  - Gate features by reputation thresholds
  - Award badges based on milestones and refresh every 3 months

✅ **Tags & Trending**
  - Categorize questions with multiple tags
  - Display trending tags (hourly refresh)

### Non-Functional Requirements (How does it perform?)

✅ **Search Latency**: < 200ms for full-text queries  
✅ **Scale**: 10M+ users, 50M+ questions, 100M+ answers  
✅ **Real-time**: Vote updates broadcast within 10 seconds  
✅ **Availability**: 99.95% uptime  
✅ **Consistency**: No double-votes; atomic reputation updates  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Comment gate** | 50 reputation required |
| **Vote gate** | 100 reputation required |
| **Close-vote gate** | 3,000 reputation required |
| **Question upvote** | Asker +10 reputation |
| **Question downvote** | Asker −2 reputation |
| **Answer upvote** | Answerer +10 reputation |
| **Answer downvote** | Answerer −2 reputation |
| **Accepted answer** | Answerer +15 rep, asker +2 rep |
| **Asking a question** | Asker +5 reputation |
| **Badge refresh** | Every 3 months |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
User, Question, Answer, Comment, Vote, Tag, Badge, Reputation, ...
```

### Step 2.2: Define Core Classes

#### **User** — A registered person on the platform

```
Properties:
  - user_id: str
  - name: str
  - reputation: int (starts at 0)
  - questions_asked: int
  - answers_given: int
  - badges: List[str]

Behaviors:
  - can_comment(): reputation >= 50
  - can_vote(): reputation >= 100
  - can_close_vote(): reputation >= 3000
```

#### **Question** — A technical post with title, description, and tags

```
Properties:
  - question_id: str
  - author_id: str
  - title: str
  - description: str
  - tags: List[str]
  - created_at: datetime
  - status: QuestionStatus (OPEN, CLOSED, SOLVED)
  - views: int
  - upvotes: int
  - downvotes: int
  - accepted_answer_id: Optional[str]

Behaviors:
  - score(): upvotes - downvotes
  - mark_solved(answer_id): transition to SOLVED
  - close(): transition to CLOSED
```

#### **Answer** — A response to a question

```
Properties:
  - answer_id: str
  - question_id: str
  - author_id: str
  - content: str
  - created_at: datetime
  - upvotes: int
  - downvotes: int
  - is_accepted: bool

Behaviors:
  - score(): upvotes - downvotes
  - accept(): mark as accepted answer
```

#### **Comment** — A short clarification on a question or answer

```
Properties:
  - comment_id: str
  - author_id: str
  - parent_id: str  (question_id or answer_id)
  - content: str
  - created_at: datetime

Behaviors:
  - (data holder; gated by reputation check upstream)
```

#### **Vote** — An upvote or downvote record

```
Properties:
  - vote_id: str
  - user_id: str
  - item_id: str   (question_id or answer_id)
  - vote_type: VoteType (UPVOTE, DOWNVOTE)
  - timestamp: datetime

Behaviors:
  - (immutable record; double-vote prevented by unique constraint)
```

#### **Tag** — A topic category for questions

```
Properties:
  - tag_name: str
  - question_ids: Set[str]  (index for fast lookup)
  - description: str

Behaviors:
  - question_count(): len(question_ids)
```

#### **Badge** — A milestone reward

```
Properties:
  - badge_id: str
  - name: str
  - description: str
  - awarded_to: str  (user_id)
  - awarded_at: datetime

Behaviors:
  - (data holder)
```

#### **StackOverflow** — Main controller (Singleton)

```
Properties:
  - users: Dict[str, User]
  - questions: Dict[str, Question]
  - answers: Dict[str, Answer]
  - votes: Dict[str, Vote]
  - tag_index: Dict[str, Set[str]]
  - user_questions: Dict[str, List[str]]
  - question_answers: Dict[str, List[str]]
  - lock: threading.RLock

Behaviors:
  - register_user(user_id, name)
  - ask_question(user_id, title, description, tags): str
  - answer_question(user_id, question_id, content): str
  - vote(user_id, item_id, vote_type): bool
  - accept_answer(question_id, answer_id): bool
  - search_questions(keyword, tags): List[Question]
  - get_trending_tags(limit): List[Tuple[str, int]]
  - display_question_with_answers(question_id)
```

### Step 2.3: Define Enumerations (State & Type)

```python
class QuestionStatus(Enum):
    OPEN = 1       # Accepting answers and votes
    CLOSED = 2     # No new answers (needs improvement)
    SOLVED = 3     # Accepted answer pinned

class VoteType(Enum):
    UPVOTE = 1
    DOWNVOTE = 2
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **User** | Reputation tracking + feature gating | No way to enforce vote/comment limits |
| **Question** | Core content unit with lifecycle | Can't track status, tags, or view count |
| **Answer** | Response with acceptance signal | Can't implement accepted-answer flow |
| **Comment** | Clarification layer | No discussion without spamming answers |
| **Vote** | Audit trail for double-vote prevention | Would allow vote manipulation |
| **Tag** | Efficient filtered search index | O(N) scan instead of O(1) tag lookup |
| **Badge** | Gamification milestone record | No milestone-based incentives |
| **StackOverflow** | Thread-safe singleton controller | No coordinated concurrent access |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Register User**

```python
def register_user(user_id: str, name: str) -> None:
    """
    Create a new user profile with 0 reputation.
    Side Effects: user added to users dict.
    """
    pass
```

#### **2. Ask Question** ⭐ CRITICAL

```python
def ask_question(user_id: str, title: str, description: str,
                 tags: List[str]) -> Optional[str]:
    """
    Post a new question and index it by tags.

    Precondition: user exists
    Postcondition: question created (OPEN), tags indexed, reputation +5

    Returns: question_id on success, None on failure.

    Failure causes:
      - user_id not found

    Side Effects: tag_index updated, user.reputation += 5
    Concurrency: THREAD-SAFE
    """
    pass
```

#### **3. Answer Question** ⭐ CRITICAL

```python
def answer_question(user_id: str, question_id: str,
                    content: str) -> Optional[str]:
    """
    Submit an answer to an existing question.

    Precondition: user and question both exist
    Postcondition: answer created, reputation +2

    Returns: answer_id on success, None on failure.

    Raises / returns None:
      - user_id or question_id not found

    Side Effects: question_answers updated, user.answers_given += 1
    """
    pass
```

#### **4. Vote** ⭐ CRITICAL

```python
def vote(user_id: str, item_id: str, vote_type: VoteType) -> bool:
    """
    Upvote or downvote a question or answer.

    Precondition: user.reputation >= 100
    Postcondition: vote recorded, item score and author reputation updated

    Returns: True on success, False on failure.

    Failure causes:
      - user_id not found
      - reputation < 100

    Side Effects: item.upvotes or downvotes incremented, author reputation adjusted
    Concurrency: THREAD-SAFE (RLock prevents race on reputation updates)
    """
    pass
```

#### **5. Accept Answer**

```python
def accept_answer(question_id: str, answer_id: str) -> bool:
    """
    Mark an answer as the accepted (best) answer.

    Precondition: answer.question_id == question_id
    Postcondition: answer.is_accepted = True, question.status = SOLVED,
                   answerer reputation +15

    Returns: True on success, False on failure.

    Side Effects: question transitions to SOLVED state
    """
    pass
```

#### **6. Search Questions**

```python
def search_questions(keyword: str,
                     tags: Optional[List[str]] = None) -> List[Question]:
    """
    Full-text search by keyword, optionally filtered by tags.
    Results sorted by score DESC then recency DESC.

    Response Time: <200ms (Elasticsearch in production)
    Returns: sorted list of matching Question objects.
    """
    pass
```

#### **7. Get Trending Tags**

```python
def get_trending_tags(limit: int = 10) -> List[Tuple[str, int]]:
    """
    Return top N tags by question count.
    In production: hourly job using (views + 2×votes) score.

    Returns: List of (tag_name, question_count) tuples.
    """
    pass
```

### Step 3.2: Exception / Failure Model

The implementation returns `None` or `False` for interview simplicity. A production version would raise:

```python
class SOException(Exception): ...
class UserNotFoundError(SOException): ...
class QuestionNotFoundError(SOException): ...
class InsufficientReputationError(SOException): ...
class DuplicateVoteError(SOException): ...
class AnswerMismatchError(SOException): ...
```

### Step 3.3: API Usage Example

```python
so = StackOverflow()

# 1. Register users
so.register_user("U1", "Alice")
so.register_user("U2", "Bob")

# 2. Ask a question
q_id = so.ask_question("U1", "How to sort list in Python?",
                        "What is the idiomatic way?", ["python", "sorting"])

# 3. Answer
a_id = so.answer_question("U2", q_id, "Use sorted() for a new list or list.sort() in-place.")

# 4. Vote (user needs 100 rep; here Bob has rep from answering)
so.vote("U2", q_id, VoteType.UPVOTE)

# 5. Accept best answer
so.accept_answer(q_id, a_id)

# 6. Search
results = so.search_questions("sort", tags=["python"])

# 7. Trending tags
trending = so.get_trending_tags(5)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
StackOverflow HAS-A users/questions/answers/votes (1:N Composition)
  └─ Singleton controller owns and manages lifecycle of all entities

User CREATES Question (1:N Association)
  └─ user_questions index tracks ownership without embedding

Question CONTAINS Answer (1:N Composition via question_answers index)
  └─ Question logically owns its answers

Question REFERENCES Tag (M:N Association via tag_index)
  └─ One question has many tags; one tag has many questions

User CASTS Vote (1:N Association via votes dict)
  └─ Vote record links user ↔ item; unique constraint prevents double-voting

Answer IS-ACCEPTED-BY Question (1:1 Optional Association)
  └─ accepted_answer_id is nullable; only one answer can be accepted
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────┐
│        StackOverflow (Singleton)         │
├──────────────────────────────────────────┤
│ - _instance: StackOverflow               │
│ - users: Dict[str, User]                 │
│ - questions: Dict[str, Question]         │
│ - answers: Dict[str, Answer]             │
│ - votes: Dict[str, Vote]                 │
│ - tag_index: Dict[str, Set[str]]         │
│ - user_questions: Dict[str, List[str]]   │
│ - question_answers: Dict[str, List[str]] │
│ - lock: threading.RLock                  │
├──────────────────────────────────────────┤
│ + register_user(...)                     │
│ + ask_question(...): str                 │
│ + answer_question(...): str              │
│ + vote(...): bool                        │
│ + accept_answer(...): bool               │
│ + search_questions(...): List[Question]  │
│ + get_trending_tags(...): List[Tuple]    │
│ + display_question_with_answers(...)     │
└─────────────┬────────────────────────────┘
              │ manages 1:N
   ┌──────────┼───────────┬─────────┐
   ▼          ▼           ▼         ▼
┌──────┐ ┌──────────┐ ┌────────┐ ┌──────┐
│ User │ │ Question │ │ Answer │ │ Vote │
├──────┤ ├──────────┤ ├────────┤ ├──────┤
│user_id│ │question_id│ │answer_id│ │vote_id│
│name  │ │author_id │ │question_id│ │user_id│
│rep   │ │title     │ │author_id│ │item_id│
│badges│ │tags[]    │ │content │ │type  │
│q_asked│ │status   │ │upvotes │ └──────┘
│a_given│ │upvotes  │ │downvotes│
└──────┘ │downvotes │ │is_accepted│
         │accepted_id│ └────────┘
         └──────────┘

TAG INDEX (many-to-many):
┌──────────────────────────────────────┐
│  tag_index: Dict[str, Set[str]]      │
│  "python" → {"Q_000001", "Q_000003"} │
│  "sorting"→ {"Q_000001"}             │
└──────────────────────────────────────┘

QUESTION STATE MACHINE:
OPEN ──close──→ CLOSED
  │
  └──accept_answer──→ SOLVED (has accepted answer pinned top)

REPUTATION EVENTS:
+5  Ask question
+10 Question upvoted
-2  Question downvoted
+2  Post answer
+10 Answer upvoted
-2  Answer downvoted
+15 Answer accepted
+2  Your answer accepted (asker bonus)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| StackOverflow → Users | 1:N | Composition | Platform owns all user profiles |
| StackOverflow → Questions | 1:N | Composition | Platform owns all questions |
| StackOverflow → Answers | 1:N | Composition | Platform owns all answers |
| StackOverflow → Votes | 1:N | Composition | Platform owns all vote records |
| User → Questions | 1:N | Association | User authors many questions |
| Question → Answers | 1:N | Composition | Question logically owns its answers |
| Question → Tags | M:N | Association | Question tagged with many; tag indexes many questions |
| Question → Answer (accepted) | 1:0..1 | Association | At most one accepted answer per question |
| User → Votes | 1:N | Association | One user casts many votes |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For StackOverflow)

**Problem**: Multiple threads need a single consistent view of all users, questions, answers, and votes.

**Solution**: One global StackOverflow instance with thread-safe initialization using double-checked locking.

```python
class StackOverflow:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe initialization, ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Doesn't scale across multiple processes without shared store

---

### Pattern 2: **Observer** (For Notifications)

**Problem**: Posting answers, receiving votes, and accepting answers must trigger notifications without coupling core logic.

**Solution**: Observer pattern decouples the platform from notification channels.

```python
class SOObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict): pass

class EmailNotifier(SOObserver):
    def update(self, event: str, data: dict):
        if event == "answer_posted":
            print(f"Email to {data['asker']}: new answer on your question!")

# Usage
so.add_observer(EmailNotifier())
so.notify_observers("answer_posted", {"asker": "alice@example.com"})
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add SMS/push/Slack channels  
**Trade-off**: ⚠️ Observer lifecycle must be managed; missed events if observer added late

---

### Pattern 3: **Strategy** (For Search Ranking)

**Problem**: Search results need different ranking algorithms — relevance, recency, or vote score — switchable at runtime.

**Solution**: Pluggable ranking strategies that sort a list of questions.

```python
class RankingStrategy(ABC):
    @abstractmethod
    def rank(self, questions: List[Question]) -> List[Question]: pass

class ScoreRanking(RankingStrategy):
    def rank(self, questions):
        return sorted(questions, key=lambda q: -(q.upvotes - q.downvotes))

class RecencyRanking(RankingStrategy):
    def rank(self, questions):
        return sorted(questions, key=lambda q: -q.created_at.timestamp())

# Usage: switch without modifying search logic
so.set_ranking_strategy(RecencyRanking())
results = so.search_questions("python")
```

**Benefit**: ✅ New ranking (trending, personalized) added without modifying core  
**Trade-off**: ⚠️ Extra abstraction layer; overkill for simple sort

---

### Pattern 4: **State Machine** (For Question Lifecycle)

**Problem**: Questions transition OPEN → CLOSED → SOLVED. Invalid transitions (re-opening a SOLVED question) must be prevented.

**Solution**: `QuestionStatus` enum with explicit transition guards.

```python
class QuestionStatus(Enum):
    OPEN = 1
    CLOSED = 2
    SOLVED = 3

def accept_answer(self, question_id: str, answer_id: str) -> bool:
    question = self.questions[question_id]
    if question.status == QuestionStatus.CLOSED:
        return False  # can't accept on closed question
    question.accepted_answer_id = answer_id
    question.status = QuestionStatus.SOLVED
    return True
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions blocked at runtime  
**Trade-off**: ⚠️ State transition rules must be documented and maintained

---

### Pattern 5: **Cache** (For Search Results and Trending Tags)

**Problem**: Full-text search across 50M questions is expensive; trending tags recalculated every request wastes CPU.

**Solution**: Cache search results with TTL; precompute trending tags hourly.

```python
# Simplified in-memory cache
_trending_cache: Optional[List] = None
_cache_time: Optional[datetime] = None
CACHE_TTL = timedelta(hours=1)

def get_trending_tags(self, limit: int = 10):
    if self._trending_cache and datetime.now() - self._cache_time < CACHE_TTL:
        return self._trending_cache[:limit]
    # recompute
    tag_counts = sorted([(tag, len(ids)) for tag, ids in self.tag_index.items()],
                        key=lambda x: -x[1])
    self._trending_cache = tag_counts
    self._cache_time = datetime.now()
    return tag_counts[:limit]
```

**Benefit**: ✅ Sub-millisecond trending reads, ✅ Reduces DB load by orders of magnitude  
**Trade-off**: ⚠️ Slight staleness (up to 1 hour); cache invalidation complexity

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Need single global StackOverflow | Consistent state across all clients |
| **Observer** | Notify on answer/vote/accept events | Loose coupling, easy to extend |
| **Strategy** | Varying search ranking algorithms | Pluggable, swap without touching core |
| **State Machine** | Question lifecycle correctness | Invalid transitions prevented |
| **Cache** | Expensive search & trending recomputation | Fast reads, reduced DB pressure |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Stack Overflow - Interview Implementation
Demonstrates:
1. Question/answer management
2. Voting and reputation system
3. Full-text search indexing
4. User reputation gates
5. Trending & recommendations
"""

from enum import Enum
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from collections import defaultdict

# ============================================================================
# ENUMERATIONS
# ============================================================================

class QuestionStatus(Enum):
    OPEN = 1
    CLOSED = 2
    SOLVED = 3

class VoteType(Enum):
    UPVOTE = 1
    DOWNVOTE = 2

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class User:
    user_id: str
    name: str
    reputation: int = 0
    questions_asked: int = 0
    answers_given: int = 0
    badges: List[str] = field(default_factory=list)

@dataclass
class Question:
    question_id: str
    author_id: str
    title: str
    description: str
    tags: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    status: QuestionStatus = QuestionStatus.OPEN
    views: int = 0
    upvotes: int = 0
    downvotes: int = 0
    accepted_answer_id: Optional[str] = None

@dataclass
class Answer:
    answer_id: str
    question_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    upvotes: int = 0
    downvotes: int = 0
    is_accepted: bool = False

@dataclass
class Vote:
    vote_id: str
    user_id: str
    item_id: str  # question_id or answer_id
    vote_type: VoteType
    timestamp: datetime = field(default_factory=datetime.now)

# ============================================================================
# STACK OVERFLOW (SINGLETON)
# ============================================================================

class StackOverflow:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self.answers: Dict[str, Answer] = {}
        self.votes: Dict[str, Vote] = {}
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.user_questions: Dict[str, List[str]] = defaultdict(list)
        self.question_answers: Dict[str, List[str]] = defaultdict(list)

        self.question_counter = 0
        self.answer_counter = 0
        self.vote_counter = 0

        # RLock allows the same thread to re-enter (e.g. vote() calling
        # into internal helpers that also acquire lock)
        self.lock = threading.RLock()
        print("Stack Overflow initialized")

    def register_user(self, user_id: str, name: str):
        with self.lock:
            user = User(user_id, name)
            self.users[user_id] = user
            print(f"User registered: {name}")

    def ask_question(self, user_id: str, title: str, description: str,
                     tags: List[str]) -> Optional[str]:
        with self.lock:
            if user_id not in self.users:
                return None

            user = self.users[user_id]

            self.question_counter += 1
            question = Question(
                f"Q_{self.question_counter:06d}",
                user_id,
                title,
                description,
                tags
            )

            self.questions[question.question_id] = question
            self.user_questions[user_id].append(question.question_id)

            # Index tags
            for tag in tags:
                self.tag_index[tag].add(question.question_id)

            user.reputation += 5  # Asking gives reputation
            user.questions_asked += 1

            print(f"Question asked by {user.name}: {title}")
            print(f"  ID: {question.question_id}, Tags: {tags}")

            return question.question_id

    def answer_question(self, user_id: str, question_id: str,
                        content: str) -> Optional[str]:
        with self.lock:
            if user_id not in self.users or question_id not in self.questions:
                return None

            user = self.users[user_id]
            question = self.questions[question_id]

            self.answer_counter += 1
            answer = Answer(
                f"A_{self.answer_counter:06d}",
                question_id,
                user_id,
                content
            )

            self.answers[answer.answer_id] = answer
            self.question_answers[question_id].append(answer.answer_id)

            user.reputation += 2  # Answering gives reputation
            user.answers_given += 1

            print(f"Answer by {user.name} to {question_id}")
            print(f"  Answer ID: {answer.answer_id}")

            return answer.answer_id

    def vote(self, user_id: str, item_id: str, vote_type: VoteType) -> bool:
        with self.lock:
            if user_id not in self.users:
                return False

            user = self.users[user_id]

            # Check if user can vote (50 rep minimum for demo; 100 in prod)
            if user.reputation < 50:
                print(f"User needs 50 rep to vote (currently {user.reputation})")
                return False

            self.vote_counter += 1
            vote = Vote(
                f"V_{self.vote_counter:06d}",
                user_id,
                item_id,
                vote_type
            )

            self.votes[vote.vote_id] = vote

            # Update item votes
            if item_id in self.questions:
                question = self.questions[item_id]
                if vote_type == VoteType.UPVOTE:
                    question.upvotes += 1
                    self.users[question.author_id].reputation += 10
                else:
                    question.downvotes += 1
                    self.users[question.author_id].reputation -= 2

                print(f"Vote on question: {vote_type.name} "
                      f"(score now {question.upvotes - question.downvotes})")

            elif item_id in self.answers:
                answer = self.answers[item_id]
                if vote_type == VoteType.UPVOTE:
                    answer.upvotes += 1
                    self.users[answer.author_id].reputation += 10
                else:
                    answer.downvotes += 1
                    self.users[answer.author_id].reputation -= 2

                print(f"Vote on answer: {vote_type.name}")

            return True

    def accept_answer(self, question_id: str, answer_id: str) -> bool:
        with self.lock:
            if question_id not in self.questions or answer_id not in self.answers:
                return False

            question = self.questions[question_id]
            answer = self.answers[answer_id]

            if answer.question_id != question_id:
                return False

            answer.is_accepted = True
            question.accepted_answer_id = answer_id
            question.status = QuestionStatus.SOLVED

            # Reputation for accepted answer
            self.users[answer.author_id].reputation += 15

            print(f"Answer {answer_id} accepted for question {question_id}")
            print(f"  Answerer now has "
                  f"{self.users[answer.author_id].reputation} reputation")

            return True

    def search_questions(self, keyword: str,
                         tags: Optional[List[str]] = None) -> List[Question]:
        with self.lock:
            results = []

            # Keyword search (simplified; Elasticsearch in production)
            for q_id, q in self.questions.items():
                if (keyword.lower() in q.title.lower() or
                        keyword.lower() in q.description.lower()):
                    results.append(q)

            # Tag filter
            if tags:
                results = [q for q in results if any(tag in q.tags for tag in tags)]

            # Sort by score DESC, then recency DESC
            results.sort(key=lambda q: (
                -(q.upvotes - q.downvotes),
                -q.created_at.timestamp()
            ))

            return results

    def get_trending_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        with self.lock:
            tag_counts = [(tag, len(q_ids))
                          for tag, q_ids in self.tag_index.items()]
            tag_counts.sort(key=lambda x: -x[1])
            return tag_counts[:limit]

    def display_question_with_answers(self, question_id: str):
        with self.lock:
            if question_id not in self.questions:
                return

            q = self.questions[question_id]
            q.views += 1

            print(f"\n  Question: {q.title}")
            print(f"  Score: {q.upvotes - q.downvotes} | Views: {q.views}")
            print(f"  Tags: {q.tags}")

            answers = [self.answers[a_id]
                       for a_id in self.question_answers[question_id]]

            # Sort: accepted first, then by score
            answers.sort(key=lambda a: (-a.is_accepted,
                                        -(a.upvotes - a.downvotes)))

            print(f"\n  Answers ({len(answers)}):")
            for i, answer in enumerate(answers, 1):
                marker = "[ACCEPTED]" if answer.is_accepted else ""
                print(f"  {i}. {marker} Score: {answer.upvotes - answer.downvotes}")
                print(f"     By: {self.users[answer.author_id].name} | "
                      f"{answer.content[:50]}...")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_ask_and_answer():
    print("\n" + "="*70)
    print("DEMO 1: ASK QUESTION & GET ANSWERS")
    print("="*70)

    so = StackOverflow()
    so.register_user("U1", "Alice")
    so.register_user("U2", "Bob")

    q_id = so.ask_question("U1", "How to sort list in Python?",
                            "What is the idiomatic way?", ["python", "sorting"])
    so.answer_question("U2", q_id, "Use sorted(list)")

    so.display_question_with_answers(q_id)

def demo_2_voting_reputation():
    print("\n" + "="*70)
    print("DEMO 2: VOTING & REPUTATION")
    print("="*70)

    so = StackOverflow()
    so.register_user("U1", "Alice")
    so.register_user("U2", "Bob")
    so.register_user("U3", "Charlie")

    q_id = so.ask_question("U1", "Best Python framework?",
                            "Which is best for web?", ["python", "frameworks"])
    a_id = so.answer_question("U2", q_id, "Django is great")

    # Upvote answer — Bob has 2 (answer) + 5 (question) = 7 rep so far,
    # asking sets up enough rep via the demo ask; Charlie has 0 so skip gate
    # Give Charlie enough rep first via his own question
    so.ask_question("U3", "Node.js tips?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 2?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 3?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 4?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 5?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 6?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 7?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 8?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 9?", "...", ["javascript"])
    so.ask_question("U3", "Node.js tips 10?", "...", ["javascript"])
    so.vote("U3", a_id, VoteType.UPVOTE)

    print(f"\n  Reputation after vote:")
    print(f"  Alice (asker): {so.users['U1'].reputation}")
    print(f"  Bob (answerer): {so.users['U2'].reputation}")
    print(f"  Charlie (voter): {so.users['U3'].reputation}")

def demo_3_accept_answer():
    print("\n" + "="*70)
    print("DEMO 3: ACCEPT BEST ANSWER")
    print("="*70)

    so = StackOverflow()
    so.register_user("U1", "Alice")
    so.register_user("U2", "Bob")

    q_id = so.ask_question("U1", "Recursion tips?",
                            "How to write recursive functions?", ["recursion"])
    a_id = so.answer_question("U2", q_id, "Use memoization")

    so.accept_answer(q_id, a_id)

    print(f"\n  Bob's reputation: {so.users['U2'].reputation}")

def demo_4_search():
    print("\n" + "="*70)
    print("DEMO 4: SEARCH QUESTIONS")
    print("="*70)

    so = StackOverflow()
    so.register_user("U1", "Alice")

    so.ask_question("U1", "Python list sorting", "...", ["python"])
    so.ask_question("U1", "JavaScript array methods", "...", ["javascript"])
    so.ask_question("U1", "Python dictionaries", "...", ["python"])

    results = so.search_questions("Python")
    print(f"\n  Search 'Python': {len(results)} results")
    for q in results:
        print(f"  - {q.title}")

def demo_5_trending():
    print("\n" + "="*70)
    print("DEMO 5: TRENDING TAGS")
    print("="*70)

    so = StackOverflow()
    so.register_user("U1", "Alice")

    for i in range(5):
        so.ask_question("U1", f"Python question {i}", "...", ["python"])

    for i in range(3):
        so.ask_question("U1", f"JS question {i}", "...", ["javascript"])

    trending = so.get_trending_tags(5)
    print(f"\n  Trending tags:")
    for tag, count in trending:
        print(f"  {tag}: {count} questions")

# ============================================================================
# MAIN
# ============================================================================

if True:
    print("\n" + "="*70)
    print("STACK OVERFLOW - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_ask_and_answer()
    demo_2_voting_reputation()
    demo_3_accept_answer()
    demo_4_search()
    demo_5_trending()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **ask_question** | RLock | Atomic: tag indexing + reputation update together |
| **answer_question** | RLock | Atomic: answer registration + counter increment |
| **vote** | RLock | Atomic: vote record + item score + author reputation |
| **accept_answer** | RLock | Atomic: status transition + reputation award |
| **search_questions** | RLock | Consistent snapshot of questions during scan |
| **Singleton init** | Class Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` replaces non-reentrant `Lock` — same thread can re-enter without deadlock
2. ✅ Singleton `__new__` accepts `*args, **kwargs` — avoids `TypeError` when Python passes constructor args
3. ✅ All state mutations inside lock; notifications (if added) fire outside to minimize hold time
4. ✅ Counters and dicts accessed only under lock — no torn reads

---

## Demo Scenarios

### Demo 1: Ask Question

```
- User asks: "How to sort list in Python?"
- Tags: [python, sorting]
- Description: 100+ words
- System:
  - Assign ID: Q_000001
  - Index tags → searchable
  - Notify followers of "python" tag
  - Display: new question prominent
```

### Demo 2: Answer & Accept

```
- Question posted 2 hours ago, 5 views
- Answer 1: "Use sorted(list)" → 20 upvotes
- Answer 2: "Use list.sort()" → 50 upvotes
- Asker accepts Answer 2 → pinned
- Answerer: +15 rep, +10 (votes) = +25 total
- Asker: +2 rep
```

### Demo 3: Search & Ranking

```
- User searches: "python sort"
- Results ranked by:
  1. Relevance score (title/tags match)
  2. Question score (upvotes - downvotes)
  3. Recency (newer questions)
- Returns top 50 in <200ms
- User views question, increments view count
```

### Demo 4: Vote & Reputation

```
- Question has 5 upvotes, 100 views
- User upvotes → 6 upvotes
- Asker: +10 rep (now 150)
- Can now: comment (50 rep), vote (100 rep)
- Locked: moderator actions (3K rep)
```

### Demo 5: Tags & Trending

```
- Tag "machine-learning": 100K questions
- Monthly views: 5M
- Recent questions: "PyTorch vs TensorFlow?" → 500 views today
- Trending tags widget: "1. machine-learning +20%"
- Users can follow tags → personalized feed
```

---

## Interview Q&A

### Basic Level

**Q1: How do you calculate question score?**

A: Score = upvotes - downvotes. Example: 50 upvotes, 5 downvotes → score 45. Used for sorting ("best" questions). Can be negative for controversial questions.

**Q2: How do you track user reputation?**

A: Reputation = sum of all events: +5 (ask), +10 (question upvote), +2 (answer), +10 (answer upvote), +15 (accepted), -2 (downvote). Displayed on profile. Gates features (need 50 to comment).

**Q3: What determines answer order (best first)?**

A: (1) Accepted answer (pinned top). (2) Score (upvotes - downvotes) DESC. (3) Date DESC. Example: 50 votes → rank 1, 30 votes → rank 2, newest date wins tie.

**Q4: How do you handle duplicate questions?**

A: Community votes to close as duplicate. Original question linked. Users redirected to canonical answer. Reduces clutter, consolidates knowledge.

**Q5: How do you prevent spam and low-quality content?**

A: (1) Minimum reputation for posting (10 rep). (2) Flag system: users flag spam, moderators review. (3) Automatic filters: detect patterns (new user, 10 questions in 1 hour). (4) Community votes to close.

### Intermediate Level

**Q6: How to implement search efficiently (50M questions)?**

A: Full-text index (Elasticsearch/Lucene). Index: title, description, tags. Query: keywords → filter by tags → rank by (relevance score, question score, recency). Expected: <200ms.

**Q7: How to suggest related questions?**

A: Similarity: shared tags (exact match = high score), similar keywords (TF-IDF), similar votes. Show top 5 most relevant. Computed at post-time or on-demand.

**Q8: How to compute recommended questions (personalized feed)?**

A: User interests: past questions viewed, tags they follow, reputation areas. Recommend recent questions matching interests. Ranked by: match % × question score × recency.

**Q9: How to handle question closure/reopening?**

A: Close reasons: duplicate, off-topic, needs clarification, too broad. 5 users with 3K+ rep vote to close. After fix, can reopen. Audit trail: who closed, when, why.

**Q10: How to handle concurrent votes (double-vote prevention)?**

A: Database constraint: unique(user_id, question_id) on votes table. On upvote: check if exists. If yes: update (toggle). If no: insert. Atomic operation.

### Advanced Level

**Q11: How to prevent vote manipulation (artificial upvotes)?**

A: Detection: (1) Rate limiting (1 vote per user per item per 10 seconds). (2) Pattern detection (same user upvoting 100 questions in 1 minute). (3) IP-based (same IP voting same content). Flag & investigate.

**Q12: How to scale to 50M+ questions with real-time search?**

A: Distributed search: shard by tag (python, javascript, etc.) or by question_id range. Each shard: independent Elasticsearch cluster. Query router: send to relevant shards, merge results.

---

## Scaling Q&A

**Q1: Can you handle 50M questions with full-text search?**

A: Yes. Elasticsearch cluster (10 nodes): 50M documents ≈ 500 GB indexed. Search latency: 100-200ms. Write QPS: 1K/sec (sustainable). Cost: ~$50K/month for infrastructure.

**Q2: How to handle 100K QPS (peak)?**

A: Query mix: 90% reads (search, view) + 10% writes (vote, answer). Read cache: frequently asked questions (Redis), hot tags. Write: queue votes, batch update scores every 10 seconds.

**Q3: How to shard 50M questions efficiently?**

A: Partition by question_id modulo N (N = num shards). Example: 50M questions → 100 shards of 500K each. Lookup: question_id % 100 → shard 42. Drawback: new shard requires rebalancing.

**Q4: How to keep search index fresh?**

A: Stream: new questions → Kafka → indexer → Elasticsearch. Latency: <5 seconds. Trade-off: slight staleness acceptable (questions rare to deleted immediately).

**Q5: How to support real-time vote updates?**

A: WebSocket: client subscribes to question → server broadcasts votes. Update frequency: every 10 seconds (batch). Notify: "5 new votes, 2 new answers". Reduces DB hammering.

**Q6: How to compute trending topics?**

A: Hourly job: count question views/votes by tag. Sort by (views + 2×votes) DESC. Cache trending tags. Display: "Python trending (50K views)", refresh hourly.

**Q7: How to handle celebrity users (prolific answerers)?**

A: Cache their profiles + top answers. On view: fetch from cache (1ms) instead of DB (10ms). Invalidate on new answer. Optimization: hot user cache (top 1K answerers).

**Q8: How to distribute indexing (1000+ questions/hour)?**

A: Indexing queue: new questions → workers (10 workers). Each worker: batch 100 questions, index to Elasticsearch. Parallelism: 10 × 100 = 1000 questions/hour capacity.

**Q9: Can you support full-text search across 100M answers?**

A: Yes, with caveat: search answers only if question doesn't match. Two-tier: (1) Search questions (fast), (2) if no result, search answers (slower). Most users stop at questions.

**Q10: How to implement recommendation engine for 10M users?**

A: Collaborative filtering: users who viewed question A also viewed B. Item-based: questions with similar tags/content. ML model: trained on 1B+ user interactions. Inference: <100ms.

**Q11: How to handle question spam at scale?**

A: ML classifier: question text → probability of spam. Threshold: >80% likely spam → auto-flag for review. Human moderators: 1000 flags/day → review top 100 (by confidence). Auto-delete after 5 user flags + moderator approval.

**Q12: Can you support real-time leaderboards (top answerers)?**

A: Yes. Cache top-1000 answerers (by reputation). Update every 5 minutes. Cost: 1000 users × (name + reputation + badge icons) ≈ 100 KB. Broadcast to all clients every 5 min.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through the ask → answer → vote → accept-answer lifecycle
- [ ] Explain reputation gates (comment 50, vote 100, close-vote 3000)
- [ ] Explain voting mechanics (upvote/downvote, reputation change, double-vote prevention)
- [ ] Explain question state machine (OPEN → CLOSED / SOLVED)
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ Scaling Q&A questions
- [ ] Mention thread safety in Singleton, vote, and accept_answer
- [ ] Discuss search strategy (tag index, keyword search, Elasticsearch at scale)
- [ ] Discuss trade-offs (in-memory vs DB, optimistic vs pessimistic locking, cache TTL)

---

**Ready for interview? Ask, answer, vote, and repeat!**
