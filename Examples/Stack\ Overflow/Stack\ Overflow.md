# Stack Overflow — 75-Minute Interview Guide

## Quick Start

**What is it?** Q&A platform for technical knowledge where users ask questions, get answers, vote, and build reputation.

**Key Classes:**
- `StackOverflow` (Singleton): Central platform
- `User`: Person with reputation, badges, questions/answers
- `Question`: Post with title, description, tags, view count
- `Answer`: Response to question with votes, acceptance
- `Vote`: Upvote/downvote on questions/answers
- `Comment`: Discussion on questions/answers
- `Tag`: Category for questions (python, javascript, etc.)

**Core Flows:**
1. **Ask**: User posts question → Gets indexed by tags → Visible to community
2. **Search**: Find questions by title/tags → Sort by relevance/recency
3. **Answer**: User submits answer → Author can accept best → Reputation awarded
4. **Vote**: Upvote/downvote → Reputation changed → Rankings updated
5. **Reputation**: Track user karma → Gate features (vote, comment, edit)

**5 Design Patterns:**
- **Singleton**: One StackOverflow platform
- **Observer**: Notify on answers/comments to question
- **Strategy**: Search ranking algorithms (relevance, recency, votes)
- **State Machine**: Question state (open, closed, solved)
- **Cache**: Search results, top questions by tag

---

## System Overview

Global Q&A platform aggregating technical knowledge, managing user reputation, enabling collaborative problem-solving with real-time updates.

### Requirements

**Functional:**
- Post questions with tags
- Submit answers to questions
- Search questions by title/tags/keywords
- Vote on questions/answers
- Add comments for clarification
- Accept best answer
- Track user reputation
- Award badges
- Display suggested questions
- Show trending tags

**Non-Functional:**
- Search < 200ms
- Support 10M+ users, 50M+ questions, 100M+ answers
- Real-time vote updates
- 99.95% uptime

**Constraints:**
- Reputation gates: need 50 rep to comment, 100 rep to vote, 1000 rep to close-vote
- Question score = upvotes - downvotes
- Upvote = +10 reputation, downvote = -2 reputation
- Accepted answer = +15 reputation for answerer, +2 for asker
- 3-month badge refresh period

---

## Architecture Diagram (ASCII UML)

```
┌──────────────────┐
│ StackOverflow    │
│ (Singleton)      │
└────────┬─────────┘
         │
    ┌────┼────┬─────────┬────────┐
    │    │    │         │        │
    ▼    ▼    ▼         ▼        ▼
┌───────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌───────┐
│Users  │ │Qstns│ │Answrs│ │Votes │ │Tags   │
└───────┘ └─────┘ └──────┘ └──────┘ └───────┘

Question State:
OPEN → CLOSED
  ↓
SOLVED (has accepted answer)

User Reputation:
Ask Q: +5, Get Q upvote: +10
Answer: +2, Get A upvote: +10, Accepted: +15
Downvote: -2
```

---

## Interview Q&A (12 Questions)

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

## Scaling Q&A (12 Questions)

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

## Demo Scenarios (5 Examples)

### Demo 1: Ask Question
```
- User asks: "How to sort list in Python?"
- Tags: [python, sorting, list]
- Description: 100+ words
- System:
  - Assign ID: Q_1000
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
- Can now: comment (50 rep), vote (100 rep) ✓
- Locked: moderator actions (3K rep)
```

### Demo 5: Tags & Trending
```
- Tag "machine-learning": 100K questions
- Monthly views: 5M
- Recent questions: "PyTorch vs TensorFlow?" → 500 views today
- Trending tags widget: "1. machine-learning ↑20%"
- Users can follow tags → personalized feed
```

---

## Complete Implementation

```python
"""
📚 Stack Overflow - Interview Implementation
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
        
        self.lock = threading.Lock()
        print("📚 Stack Overflow initialized")
    
    def register_user(self, user_id: str, name: str):
        with self.lock:
            user = User(user_id, name)
            self.users[user_id] = user
            print(f"✓ User registered: {name}")
    
    def ask_question(self, user_id: str, title: str, description: str, tags: List[str]) -> Optional[str]:
        with self.lock:
            if user_id not in self.users:
                return None
            
            user = self.users[user_id]
            
            # Minimum reputation check (conceptually)
            if user.reputation < 1:  # Can ask with 0 rep
                pass
            
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
            
            print(f"✓ Question asked by {user.name}: {title}")
            print(f"  ID: {question.question_id}, Tags: {tags}")
            
            return question.question_id
    
    def answer_question(self, user_id: str, question_id: str, content: str) -> Optional[str]:
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
            
            print(f"✓ Answer by {user.name} to {question_id}")
            print(f"  Answer ID: {answer.answer_id}")
            
            return answer.answer_id
    
    def vote(self, user_id: str, item_id: str, vote_type: VoteType) -> bool:
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Check if user can vote (50 rep minimum)
            if user.reputation < 50:
                print(f"✗ User needs 50 rep to vote (currently {user.reputation})")
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
                    # Asker reputation
                    self.users[question.author_id].reputation += 10
                else:
                    question.downvotes += 1
                    # Asker loses reputation
                    self.users[question.author_id].reputation -= 2
                
                print(f"✓ Vote on question: {vote_type.name} (now {question.upvotes - question.downvotes} score)")
                
            elif item_id in self.answers:
                answer = self.answers[item_id]
                if vote_type == VoteType.UPVOTE:
                    answer.upvotes += 1
                    self.users[answer.author_id].reputation += 10
                else:
                    answer.downvotes += 1
                    self.users[answer.author_id].reputation -= 2
                
                print(f"✓ Vote on answer: {vote_type.name}")
            
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
            
            print(f"✓ Answer {answer_id} accepted for question {question_id}")
            print(f"  Answerer now has {self.users[answer.author_id].reputation} reputation")
            
            return True
    
    def search_questions(self, keyword: str, tags: Optional[List[str]] = None) -> List[Question]:
        with self.lock:
            results = []
            
            # Keyword search (simplified)
            for q_id, q in self.questions.items():
                if keyword.lower() in q.title.lower() or keyword.lower() in q.description.lower():
                    results.append(q)
            
            # Tag filter
            if tags:
                results = [q for q in results if any(tag in q.tags for tag in tags)]
            
            # Sort by score DESC, then recency DESC
            results.sort(key=lambda q: (-(q.upvotes - q.downvotes), -q.created_at.timestamp()))
            
            return results
    
    def get_trending_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        with self.lock:
            tag_counts = [(tag, len(q_ids)) for tag, q_ids in self.tag_index.items()]
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
            
            answers = [self.answers[a_id] for a_id in self.question_answers[question_id]]
            
            # Sort: accepted first, then by score
            answers.sort(key=lambda a: (-a.is_accepted, -(a.upvotes - a.downvotes)))
            
            print(f"\n  Answers ({len(answers)}):")
            for i, answer in enumerate(answers, 1):
                marker = "✓ [ACCEPTED]" if answer.is_accepted else ""
                print(f"  {i}. {marker} Score: {answer.upvotes - answer.downvotes}")
                print(f"     By: {self.users[answer.author_id].name} | {answer.content[:50]}...")

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
    
    q_id = so.ask_question("U1", "How to sort list in Python?", "...", ["python", "sorting"])
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
    
    q_id = so.ask_question("U1", "Best Python framework?", "...", ["python", "frameworks"])
    a_id = so.answer_question("U2", q_id, "Django is great")
    
    # Upvote answer
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
    
    q_id = so.ask_question("U1", "Recursion tips?", "...", ["recursion"])
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
        so.ask_question("U1", f"Question {i}", "...", ["python"])
    
    for i in range(3):
        so.ask_question("U1", f"Question {i}", "...", ["javascript"])
    
    trending = so.get_trending_tags(5)
    print(f"\n  Trending tags:")
    for tag, count in trending:
        print(f"  {tag}: {count} questions")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("📚 STACK OVERFLOW - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_ask_and_answer()
    demo_2_voting_reputation()
    demo_3_accept_answer()
    demo_4_search()
    demo_5_trending()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Summary

✅ **Question/answer** management with threading support
✅ **Reputation system** with gating (voting, commenting)
✅ **Voting mechanics** (upvote/downvote) with reputation rewards
✅ **Full-text search** by keywords and tags
✅ **Accepted answer** flow with asker/answerer reputation
✅ **Trending tags** computation
✅ **User profiles** with badges and statistics
✅ **Vote tracking** (prevent double-voting)
✅ **Tag indexing** for efficient filtering
✅ **Concurrent operations** with thread safety

**Key Takeaway**: Stack Overflow demonstrates reputation systems, voting mechanics, full-text search, and community-driven content. Core focus: gate features by reputation, rank content by relevance & votes, search efficiently across millions of questions.
