# LinkedIn — Complete Design Guide

> Professional networking platform with profiles, connections, job postings, content feed, messaging, and match recommendations.

**Scale**: 500M+ DAU, 10M+ jobs, 1B messages/day, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Connection state machine, job-matching strategy, event-driven feed, observer-based notifications

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
Users create professional profiles → connect with peers → publish content (factory-created posts) → consume a ranked feed → discover and apply for jobs via pluggable matching strategies → message connections. Every event notifies subscribers via Observer pattern. The entire system is coordinated through a single thread-safe Singleton.

### Core Flow
```
Create Profile → Add Skills / Experience → Send Connection Request
    → PENDING → Accept → ACCEPTED (state machine)
         ↓
    Create Post (Factory) → Notify Followers (Observer) → Ranked Feed
         ↓
    Post Job → Set Matcher Strategy → Apply → Match Score Calculated
         ↓
    Send Message → MessageNotifier → Recipient notified
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Single-process demo; production is distributed microservices"
2. **Real payment / identity verification?** → "Out of scope; mock data only"
3. **What post types to support?** → "Text, Image, Video, Article — extensible via Factory"
4. **How are feeds ranked?** → "Engagement × recency × connection-strength score"
5. **Job matching algorithm fixed or pluggable?** → "Pluggable Strategy pattern; skill/location/experience/hybrid"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User (Professional)** | Create profile, connect, post, apply for jobs | Add skills, send connection request, publish post, apply |
| **Recruiter / Company** | Post jobs, find candidates | Post job listing, browse matching candidates |
| **System** | Coordinator & notifier | Rank feed, emit events, notify observers, recommend connections |

### Functional Requirements (What does the system do?)

✅ **Profile Management**
  - Create user profile with name, headline, location
  - Add skills and work experiences
  - Track connections and followers

✅ **Connection System**
  - Send connection requests (Pending state)
  - Accept or reject requests (state transitions)
  - Query mutual connections
  - Recommend new connections based on network + skill overlap

✅ **Content Feed**
  - Create posts (TextPost, ImagePost, VideoPost, ArticlePost) via Factory
  - Like, comment, share posts
  - Generate personalized ranked feed (engagement × recency × connection strength)

✅ **Job Management**
  - Post jobs with required skills, location, experience level
  - Apply for jobs
  - Match candidates using pluggable strategy (skill / location / experience / hybrid)
  - Swap matching algorithm at runtime

✅ **Messaging**
  - Send direct messages between users
  - Track read/unread status

✅ **Notifications (Observer)**
  - FeedNotifier, ConnectionNotifier, JobNotifier, MessageNotifier
  - Decouple event producers from consumers

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe Singleton; RLock on shared state  
✅ **Feed Latency**: < 500ms feed generation (in-memory demo)  
✅ **Search Latency**: < 200ms (production: Elasticsearch)  
✅ **Message Delivery**: < 1s (production: WebSocket + Kafka)  
✅ **Availability**: 99.9% uptime  
✅ **Consistency**: Eventual consistency for feeds; strong for connections  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Storage** | In-memory for demo (production: PostgreSQL + Redis + Elasticsearch) |
| **Auth / Security** | Out of scope |
| **Real payments** | NO — mock service |
| **Post types extensible?** | YES — Factory pattern |
| **Matching algorithm fixed?** | NO — Strategy pattern, runtime-swappable |
| **Connection requests** | One pending request per pair |
| **Feed size** | Return top 20 posts per request |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
User, Connection, Post (TextPost/ImagePost/VideoPost/ArticlePost),
Job, Company, Message, Feed, Skill, Experience, Location, ...
```

### Step 2.2: Define Core Classes

#### **User** — Professional profile
```
Properties:
  - user_id: str
  - name: str
  - headline: str
  - location: Location
  - skills: List[Skill]
  - experiences: List[Experience]
  - connections: Set[str]  (user_ids of 1st-degree connections)
  - followers: Set[str]

Behaviors:
  - add_skill(skill): Add unique skill
  - add_experience(exp): Append work experience
  - total_experience_years(): Sum all experience durations
```

#### **Connection** — Relationship with state machine
```
Properties:
  - connection_id: str
  - from_user_id: str
  - to_user_id: str
  - status: ConnectionStatus (PENDING, ACCEPTED, REJECTED, WITHDRAWN)
  - message: str
  - created_at: datetime

Behaviors:
  - (transitions controlled by LinkedInSystem)
  - Valid: PENDING → ACCEPTED or REJECTED
```

#### **Post** — Base content class (polymorphic via Factory)
```
Properties:
  - post_id: str
  - author_id: str
  - content: str
  - visibility: Visibility (PUBLIC, CONNECTIONS, PRIVATE)
  - likes: Set[str]
  - comments: List[Dict]
  - shares: List[Dict]
  - created_at: datetime

Behaviors:
  - post_type(): Return PostType enum
  - engagement_score(): likes + 3×comments + 5×shares

Subtypes: TextPost, ImagePost (image_urls), VideoPost (video_url), ArticlePost (full_text)
```

#### **Job** — Job posting
```
Properties:
  - job_id: str
  - company_id: str
  - title: str
  - description: str
  - location: Location
  - required_skills: List[str]
  - required_experience_years: int
  - job_type: JobType
  - applications: List[str]  (user_ids)

Behaviors:
  - (data holder; matching logic in Strategy)
```

#### **Message** — Direct message between users
```
Properties:
  - message_id: str
  - sender_id: str
  - receiver_id: str
  - content: str
  - is_read: bool
  - created_at: datetime
```

#### **LinkedInSystem** — Main controller (Singleton)
```
Properties:
  - users: Dict[str, User]
  - connections: Dict[str, Connection]
  - posts: Dict[str, Post]
  - jobs: Dict[str, Job]
  - messages: Dict[str, Message]
  - job_matcher: JobMatchingStrategy
  - observers: List[LinkedInObserver]
  - _lock: threading.RLock

Behaviors:
  - create_user / get_user
  - send_connection_request / accept_connection / reject_connection
  - create_post / like_post / generate_feed
  - post_job / apply_for_job / get_matching_candidates / set_job_matcher
  - send_message
  - recommend_connections
  - register_observer / _emit
```

### Step 2.3: Define Enumerations (State & Type)

```python
class ConnectionStatus(Enum):
    PENDING = "pending"       # Request sent, awaiting response
    ACCEPTED = "accepted"     # Both parties connected
    REJECTED = "rejected"     # Request declined
    WITHDRAWN = "withdrawn"   # Sender withdrew request

class PostType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ARTICLE = "article"

class Visibility(Enum):
    PUBLIC = "public"          # Anyone can see
    CONNECTIONS = "connections" # 1st-degree only
    PRIVATE = "private"        # Owner only

class JobType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **User** | Core identity; holds skills, experiences, connections | No profile, no network |
| **Connection** | State machine for relationship lifecycle | No PENDING → ACCEPTED guard; invalid transitions |
| **Post + subtypes** | Polymorphic content; Factory extensibility | Rigid post creation, hard to add types |
| **Job** | Job posting data + applicant list | No job board |
| **Message** | Conversation history + read status | No messaging |
| **LinkedInSystem** | Thread-safe single coordinator | Inconsistent state across threads |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Create User**
```python
def create_user(user_id: str, name: str, headline: str, location: Location) -> User:
    """
    Register a new professional profile.
    Returns: User object.
    Side Effects: Emits "user_created" event.
    """
    pass
```

#### **2. Send Connection Request** ⭐ CRITICAL
```python
def send_connection_request(from_user_id: str, to_user_id: str, message: str = "") -> Connection:
    """
    Create a PENDING connection between two users.
    Precondition: No active connection between the pair.
    Returns: Connection with status=PENDING.
    Side Effects: Emits "connection_requested" event.
    """
    pass
```

#### **3. Accept / Reject Connection** ⭐ CRITICAL
```python
def accept_connection(connection_id: str) -> bool:
    """
    Transition PENDING → ACCEPTED. Adds each user to the other's connections set.
    Raises: Returns False if connection not found or not in PENDING state.
    Side Effects: Emits "connection_accepted".
    """
    pass

def reject_connection(connection_id: str) -> bool:
    """
    Transition PENDING → REJECTED.
    Returns False if not found or not PENDING.
    """
    pass
```

#### **4. Create Post (Factory Entry Point)** ⭐ CRITICAL
```python
def create_post(post_id: str, author_id: str, post_type: PostType,
                content: str, visibility: Visibility = Visibility.PUBLIC, **kwargs) -> Post:
    """
    Factory-style creation of the correct Post subclass.
    kwargs: image_urls (ImagePost), video_url (VideoPost), full_text (ArticlePost)
    Returns: Appropriate Post subclass.
    Side Effects: Emits "post_created", notifies followers.
    """
    pass
```

#### **5. Generate Feed**
```python
def generate_feed(user_id: str, limit: int = 20) -> List[Post]:
    """
    Return top-N ranked posts for the user.
    Score = engagement_score × exp(-age_seconds / 86400) × connection_strength
    Filters by visibility rules.
    Response Time: O(P log P) where P = total posts.
    """
    pass
```

#### **6. Post Job & Apply** ⭐ CRITICAL
```python
def post_job(job_id: str, company_id: str, title: str, description: str,
             location: Location, required_skills: List[str],
             required_experience_years: int) -> Job:
    """Post a new job listing. Emits "job_posted"."""
    pass

def apply_for_job(job_id: str, user_id: str) -> bool:
    """
    Record application. Calculate match score using active strategy.
    Returns False if job not found or already applied.
    Emits "job_applied" with match_score.
    """
    pass
```

#### **7. Set Job Matching Strategy**
```python
def set_job_matcher(strategy: JobMatchingStrategy) -> None:
    """
    Swap job matching algorithm at runtime.
    New strategy applied on next apply_for_job / get_matching_candidates call.
    """
    pass
```

#### **8. Register Observer**
```python
def register_observer(observer: LinkedInObserver) -> None:
    """
    Subscribe to all system events.
    Events: user_created, connection_requested, connection_accepted,
            post_created, post_liked, job_posted, job_applied, message_sent, ...
    """
    pass
```

### Step 3.2: Failure Model

```python
class LinkedInException(Exception): ...
class UserNotFoundError(LinkedInException): ...
class ConnectionNotFoundError(LinkedInException): ...
class InvalidStateTransitionError(LinkedInException): ...
class JobNotFoundError(LinkedInException): ...
class DuplicateApplicationError(LinkedInException): ...
```

> Demo code returns `False` / `None` for brevity; production code raises typed exceptions.

### Step 3.3: API Usage Example

```python
system = LinkedInSystem()   # returns singleton

# Setup
loc = Location("San Francisco", "USA", 37.7749, -122.4194)
alice = system.create_user("alice_1", "Alice", "Engineer @ Google", loc)
alice.add_skill(Skill("s1", "Python", "Programming"))

bob = system.create_user("bob_1", "Bob", "PM @ Meta", loc)

# Connect
conn = system.send_connection_request("alice_1", "bob_1")
system.accept_connection(conn.connection_id)

# Post
post = system.create_post("p1", "alice_1", PostType.TEXT, "Hello LinkedIn!")
system.like_post("p1", "bob_1")

# Feed
feed = system.generate_feed("bob_1", limit=10)

# Job
job = system.post_job("j1", "google", "SWE", "Build things", loc, ["Python"], 3)
system.set_job_matcher(HybridMatcher())
system.apply_for_job("j1", "alice_1")
candidates = system.get_matching_candidates("j1", threshold=70)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
LinkedInSystem HAS-A users / connections / posts / jobs / messages (1:N Composition)
  └─ System owns lifecycle of all domain objects

User HAS-A skills (1:N Composition)
  └─ Skills list owned by User

User HAS-A experiences (1:N Composition)
  └─ Experience history owned by User

Connection REFERENCES from_user / to_user (1:1 Association)
  └─ Connection links User entities (no ownership)

Post REFERENCES author (1:1 Association)
  └─ Post links to User (no ownership)

Post IS-A TextPost / ImagePost / VideoPost / ArticlePost (Inheritance)
  └─ Factory creates appropriate subclass

LinkedInSystem USES-A JobMatchingStrategy (1:1 Composition, swappable)
  └─ Strategy algorithm owned but replaceable at runtime

LinkedInSystem NOTIFIES LinkedInObserver (1:N Association)
  └─ Multiple observers listen to events
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────────────────────────────┐
│           LinkedInSystem (Singleton)                       │
├────────────────────────────────────────────────────────────┤
│ - _instance: LinkedInSystem                                │
│ - users: Dict[str, User]                                   │
│ - connections: Dict[str, Connection]                       │
│ - posts: Dict[str, Post]                                   │
│ - jobs: Dict[str, Job]                                     │
│ - messages: Dict[str, Message]                             │
│ - job_matcher: JobMatchingStrategy                         │
│ - observers: List[LinkedInObserver]                        │
│ - _lock: threading.RLock                                   │
├────────────────────────────────────────────────────────────┤
│ + create_user(...): User                                   │
│ + send_connection_request(...): Connection                 │
│ + accept_connection(id): bool                             │
│ + reject_connection(id): bool                             │
│ + create_post(...): Post                                   │
│ + like_post(id, user_id): bool                            │
│ + generate_feed(user_id, limit): List[Post]               │
│ + post_job(...): Job                                       │
│ + apply_for_job(job_id, user_id): bool                    │
│ + get_matching_candidates(job_id, threshold): List[Tuple] │
│ + set_job_matcher(strategy): void                         │
│ + send_message(...): Message                               │
│ + recommend_connections(user_id, limit): List[Tuple]      │
│ + register_observer(observer): void                       │
└──────────┬────────────────────────────────────────────────┘
           │ manages 1:N
    ┌──────┼──────────────┬──────────────┬──────────────┐
    ▼      ▼              ▼              ▼              ▼
┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│  User  │ │Connection│ │  Post  │ │  Job   │ │ Message  │
├────────┤ ├──────────┤ ├────────┤ ├────────┤ ├──────────┤
│user_id │ │conn_id   │ │post_id │ │job_id  │ │msg_id    │
│name    │ │from_user │ │author  │ │company │ │sender    │
│headline│ │to_user   │ │content │ │skills[]│ │receiver  │
│location│ │status:   │ │type    │ │exp_req │ │content   │
│skills[]│ │ PENDING  │ │likes{} │ │apps[]  │ │is_read   │
│exps[]  │ │ ACCEPTED │ │comments│ └────────┘ └──────────┘
│conns{} │ │ REJECTED │ │shares  │
│followers│ │ WITHDRAWN│ │created │
└────────┘ └──────────┘ └───┬────┘
                             │ subclasses (Factory)
                    ┌────────┼────────────┐
                    ▼        ▼            ▼            ▼
               TextPost  ImagePost   VideoPost   ArticlePost
               (content) (image_urls)(video_url) (full_text)

STRATEGY PATTERN (Job Matching):
┌──────────────────────────────────────────┐
│ JobMatchingStrategy (Abstract)           │
├──────────────────────────────────────────┤
│ + calculate_match_score(job, user): float│
└──┬───────────────────────────────────────┘
   │ implemented by
   ├─→ SkillBasedMatcher    (% required skills matched)
   ├─→ LocationBasedMatcher (distance < 50km → 100%)
   ├─→ ExperienceBasedMatcher (years diff × 10 penalty)
   └─→ HybridMatcher        (0.5×skill + 0.3×location + 0.2×exp)

OBSERVER PATTERN (Notifications):
┌──────────────────────────────────────────┐
│ LinkedInObserver (Abstract)              │
├──────────────────────────────────────────┤
│ + update(event, payload): void           │
└──┬───────────────────────────────────────┘
   │ implemented by
   ├─→ FeedNotifier         (post_created events)
   ├─→ ConnectionNotifier   (connection_accepted events)
   ├─→ JobNotifier          (job_posted events)
   └─→ MessageNotifier      (message_sent events)

CONNECTION STATE MACHINE:
PENDING ──accept()──→ ACCEPTED
PENDING ──reject()──→ REJECTED
PENDING ──withdraw()─→ WITHDRAWN
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| LinkedInSystem → Users | 1:N | Composition | System owns all users |
| LinkedInSystem → Connections | 1:N | Composition | System owns all connections |
| LinkedInSystem → Posts | 1:N | Composition | System owns all posts |
| LinkedInSystem → Jobs | 1:N | Composition | System owns all jobs |
| LinkedInSystem → Messages | 1:N | Composition | System owns all messages |
| User → Skills | 1:N | Composition | User owns skill list |
| User → Experiences | 1:N | Composition | User owns experience history |
| Connection → Users | 1:1 × 2 | Association | Connection links two Users |
| Post → User (author) | 1:1 | Association | Post references author |
| Job → User (applicants) | 1:N | Association | Job references applicant IDs |
| LinkedInSystem → JobMatchingStrategy | 1:1 | Composition | System owns active strategy |
| LinkedInSystem → Observers | 1:N | Association | System notifies many listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For LinkedInSystem)

**Problem**: Multiple threads need one consistent view of users, connections, posts, jobs.

**Solution**: One global LinkedInSystem instance with thread-safe double-checked locking.

```python
class LinkedInSystem:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):       # *args/**kwargs: accept (and ignore) any init args
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._data_lock = threading.RLock()  # RLock: re-entrant, no self-deadlock
        # ... initialize dicts ...
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Harder to scale across machines

---

### Pattern 2: **Strategy** (For Job Matching)

**Problem**: Job matching criteria vary (skill overlap, location proximity, experience level) and may change at runtime.

**Solution**: Pluggable `JobMatchingStrategy` ABC; swap algorithm without modifying core booking logic.

```python
class JobMatchingStrategy(ABC):
    @abstractmethod
    def calculate_match_score(self, job: Job, user: User) -> float:
        pass

class SkillBasedMatcher(JobMatchingStrategy):
    def calculate_match_score(self, job: Job, user: User) -> float:
        user_skills = {s.name.lower() for s in user.skills}
        matched = sum(1 for r in job.required_skills if r.lower() in user_skills)
        return (matched / len(job.required_skills)) * 100 if job.required_skills else 0.0

class HybridMatcher(JobMatchingStrategy):
    def calculate_match_score(self, job: Job, user: User) -> float:
        s = SkillBasedMatcher().calculate_match_score(job, user)
        l = LocationBasedMatcher().calculate_match_score(job, user)
        e = ExperienceBasedMatcher().calculate_match_score(job, user)
        return s * 0.5 + l * 0.3 + e * 0.2

# Runtime swap:
system.set_job_matcher(HybridMatcher())
```

**Benefit**: ✅ Easy to add new matchers (salary-based, industry-based), ✅ No core-logic change  
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Post creation, connection acceptance, job posting, and messaging each need to trigger different notifications without coupling.

**Solution**: `LinkedInObserver` ABC; event producer calls `_emit(event, payload)`; each observer reacts independently.

```python
class LinkedInObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict) -> None: pass

class FeedNotifier(LinkedInObserver):
    def update(self, event: str, payload: dict) -> None:
        if event == "post_created":
            print(f"  [FEED] New post from {payload['author_id']}")

class ConnectionNotifier(LinkedInObserver):
    def update(self, event: str, payload: dict) -> None:
        if event == "connection_accepted":
            print(f"  [CONNECTION] {payload['user1']} ↔ {payload['user2']} connected")

# Usage: Add multiple observers
system.register_observer(FeedNotifier())
system.register_observer(ConnectionNotifier())
system._emit("post_created", {"author_id": "alice_1", "content": "Hello!"})
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new channels (SMS, Push, Slack)  
**Trade-off**: ⚠️ Observer lifecycle management, ⚠️ Unhandled exceptions in one observer affect others

---

### Pattern 4: **Factory** (For Post Types)

**Problem**: Creating posts requires selecting the right subclass (TextPost, ImagePost, VideoPost, ArticlePost) and initializing type-specific fields.

**Solution**: `create_post()` acts as a factory method; caller passes `PostType` enum; factory returns correct subclass.

```python
def create_post(self, post_id, author_id, post_type, content, **kwargs) -> Post:
    if post_type == PostType.TEXT:
        return TextPost(post_id, author_id, content)
    elif post_type == PostType.IMAGE:
        return ImagePost(post_id, author_id, content,
                         image_urls=kwargs.get('image_urls', []))
    elif post_type == PostType.VIDEO:
        return VideoPost(post_id, author_id, content,
                         video_url=kwargs.get('video_url', ''))
    else:  # ARTICLE
        return ArticlePost(post_id, author_id, content,
                           full_text=kwargs.get('full_text', ''))
```

**Benefit**: ✅ Centralized creation, ✅ Easy to add new post types  
**Trade-off**: ⚠️ Factory method grows; consider dedicated `PostFactory` class if many types

---

### Pattern 5: **State Machine** (For Connection Lifecycle)

**Problem**: A connection can be PENDING, ACCEPTED, REJECTED, or WITHDRAWN. Invalid transitions (e.g., accept after reject) must be blocked.

**Solution**: `ConnectionStatus` enum enforces valid transitions at the application level.

```python
def accept_connection(self, connection_id: str) -> bool:
    conn = self.connections.get(connection_id)
    if not conn or conn.status != ConnectionStatus.PENDING:
        return False   # Invalid transition blocked
    conn.status = ConnectionStatus.ACCEPTED
    self.users[conn.from_user_id].connections.add(conn.to_user_id)
    self.users[conn.to_user_id].connections.add(conn.from_user_id)
    return True
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions caught at runtime  
**Trade-off**: ⚠️ State logic spread across methods; can graduate to full State pattern if more states added

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | One global LinkedInSystem | Consistent state across all clients |
| **Strategy** | Varying job-matching algorithms | Pluggable, runtime-swappable |
| **Observer** | Events trigger notifications | Loose coupling, event-driven |
| **Factory** | Correct Post subclass creation | Centralized, easy to extend |
| **State Machine** | Connection lifecycle correctness | Invalid transitions prevented |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
LinkedIn System - Interview Implementation
Demonstrates:
1. Singleton pattern (one system instance, RLock for re-entrancy safety)
2. Factory pattern (create different post types)
3. Strategy pattern (pluggable job matching algorithms)
4. Observer pattern (event notifications)
5. State machine pattern (connection lifecycle)

Bug fixes applied vs original:
  - LinkedInSystem.__new__ now accepts *args, **kwargs to avoid TypeError
    when Python calls __new__(cls) during singleton creation via __init__.
  - threading.Lock replaced with threading.RLock throughout to prevent
    self-deadlock when methods re-enter the same lock (e.g. notify inside lock).
  - Demo functions call LinkedInSystem() (the correct singleton accessor)
    instead of the non-existent LinkedInSystem.instance() class method.
"""

from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import threading
import math

# ============================================================================
# ENUMERATIONS
# ============================================================================

class ConnectionStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class PostType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ARTICLE = "article"

class Visibility(Enum):
    PUBLIC = "public"
    CONNECTIONS = "connections"
    PRIVATE = "private"

class JobType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"

# ============================================================================
# SUPPORTING CLASSES
# ============================================================================

@dataclass
class Skill:
    skill_id: str
    name: str
    category: str

@dataclass
class Experience:
    company: str
    title: str
    start_date: datetime
    end_date: Optional[datetime] = None

    def duration_years(self) -> float:
        end = self.end_date or datetime.now()
        return (end - self.start_date).days / 365.25

@dataclass
class Location:
    city: str
    country: str
    lat: float
    lon: float

    def distance_to(self, other: Location) -> float:
        """Haversine distance in km"""
        R = 6371
        lat1, lon1 = math.radians(self.lat), math.radians(self.lon)
        lat2, lon2 = math.radians(other.lat), math.radians(other.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

# ============================================================================
# CORE ENTITIES
# ============================================================================

@dataclass
class User:
    """Professional user profile"""
    user_id: str
    name: str
    headline: str
    location: Location
    skills: List[Skill] = field(default_factory=list)
    experiences: List[Experience] = field(default_factory=list)
    connections: Set[str] = field(default_factory=set)
    followers: Set[str] = field(default_factory=set)

    def add_skill(self, skill: Skill) -> None:
        if not any(s.skill_id == skill.skill_id for s in self.skills):
            self.skills.append(skill)

    def add_experience(self, exp: Experience) -> None:
        self.experiences.append(exp)

    def total_experience_years(self) -> float:
        return sum(exp.duration_years() for exp in self.experiences)

@dataclass
class Connection:
    """Connection between two users with state machine"""
    connection_id: str
    from_user_id: str
    to_user_id: str
    status: ConnectionStatus = ConnectionStatus.PENDING
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Post:
    """Base post class"""
    post_id: str
    author_id: str
    content: str
    visibility: Visibility = Visibility.PUBLIC
    likes: Set[str] = field(default_factory=set)
    comments: List[Dict] = field(default_factory=list)
    shares: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def post_type(self) -> PostType:
        raise NotImplementedError

    def engagement_score(self) -> int:
        return len(self.likes) + 3 * len(self.comments) + 5 * len(self.shares)

@dataclass
class TextPost(Post):
    def post_type(self) -> PostType:
        return PostType.TEXT

@dataclass
class ImagePost(Post):
    image_urls: List[str] = field(default_factory=list)

    def post_type(self) -> PostType:
        return PostType.IMAGE

@dataclass
class VideoPost(Post):
    video_url: str = ""

    def post_type(self) -> PostType:
        return PostType.VIDEO

@dataclass
class ArticlePost(Post):
    full_text: str = ""

    def post_type(self) -> PostType:
        return PostType.ARTICLE

@dataclass
class Job:
    """Job posting"""
    job_id: str
    company_id: str
    title: str
    description: str
    location: Location
    required_skills: List[str] = field(default_factory=list)
    required_experience_years: int = 0
    job_type: JobType = JobType.FULL_TIME
    applications: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Message:
    """Direct message"""
    message_id: str
    sender_id: str
    receiver_id: str
    content: str
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)

# ============================================================================
# JOB MATCHING STRATEGIES (STRATEGY PATTERN)
# ============================================================================

class JobMatchingStrategy(ABC):
    """Abstract strategy for job matching"""

    @abstractmethod
    def calculate_match_score(self, job: Job, user: User) -> float:
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__

class SkillBasedMatcher(JobMatchingStrategy):
    """Match based on skill overlap"""

    def calculate_match_score(self, job: Job, user: User) -> float:
        if not job.required_skills:
            return 0.0
        user_skill_names = {s.name.lower() for s in user.skills}
        matched = sum(1 for req in job.required_skills if req.lower() in user_skill_names)
        return (matched / len(job.required_skills)) * 100

class LocationBasedMatcher(JobMatchingStrategy):
    """Match based on location proximity"""

    def calculate_match_score(self, job: Job, user: User) -> float:
        distance = user.location.distance_to(job.location)
        return 100.0 if distance < 50 else 50.0

class ExperienceBasedMatcher(JobMatchingStrategy):
    """Match based on years of experience"""

    def calculate_match_score(self, job: Job, user: User) -> float:
        user_years = user.total_experience_years()
        diff = abs(user_years - job.required_experience_years)
        return max(0, 100 - (diff * 10))

class HybridMatcher(JobMatchingStrategy):
    """Combine multiple strategies with weights"""

    def __init__(self, skill_weight=0.5, location_weight=0.3, exp_weight=0.2):
        self.skill_matcher = SkillBasedMatcher()
        self.location_matcher = LocationBasedMatcher()
        self.exp_matcher = ExperienceBasedMatcher()
        self.weights = (skill_weight, location_weight, exp_weight)

    def calculate_match_score(self, job: Job, user: User) -> float:
        skill_score = self.skill_matcher.calculate_match_score(job, user)
        location_score = self.location_matcher.calculate_match_score(job, user)
        exp_score = self.exp_matcher.calculate_match_score(job, user)
        return (skill_score * self.weights[0] +
                location_score * self.weights[1] +
                exp_score * self.weights[2])

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class LinkedInObserver(ABC):
    """Abstract observer for events"""

    @abstractmethod
    def update(self, event: str, payload: Dict) -> None:
        raise NotImplementedError

class FeedNotifier(LinkedInObserver):
    """Notifies about feed updates"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "post_created":
            print(f"  [FEED] New post from {payload['author_id']}: {payload['content'][:50]}")

class ConnectionNotifier(LinkedInObserver):
    """Notifies about connection changes"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "connection_accepted":
            print(f"  [CONNECTION] {payload['user1']} and {payload['user2']} are now connected")

class JobNotifier(LinkedInObserver):
    """Notifies about job events"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "job_posted":
            print(f"  [JOB] New job posted: {payload['title']}")

class MessageNotifier(LinkedInObserver):
    """Notifies about messages"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "message_sent":
            print(f"  [MSG] {payload['sender']} -> {payload['receiver']}: message delivered")

# ============================================================================
# LINKEDIN SYSTEM (SINGLETON)
# ============================================================================

class LinkedInSystem:
    """Centralized LinkedIn system (thread-safe Singleton)"""

    _instance: Optional[LinkedInSystem] = None
    _lock = threading.RLock()   # RLock: avoids self-deadlock in re-entrant calls

    def __new__(cls, *args, **kwargs) -> LinkedInSystem:
        # *args / **kwargs required so Python does not raise TypeError when
        # __init__ signature differs from __new__ during first construction.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.users: Dict[str, User] = {}
        self.connections: Dict[str, Connection] = {}
        self.posts: Dict[str, Post] = {}
        self.jobs: Dict[str, Job] = {}
        self.messages: Dict[str, Message] = {}
        self.job_matcher: JobMatchingStrategy = HybridMatcher()
        self.observers: List[LinkedInObserver] = []
        self._data_lock = threading.RLock()   # RLock: safe for re-entrant acquisition
        print("LinkedIn System initialized")

    def register_observer(self, observer: LinkedInObserver) -> None:
        self.observers.append(observer)

    def _emit(self, event: str, payload: Dict) -> None:
        for observer in self.observers:
            observer.update(event, payload)

    # ---- USER MANAGEMENT ----

    def create_user(self, user_id: str, name: str, headline: str, location: Location) -> User:
        user = User(user_id, name, headline, location)
        with self._data_lock:
            self.users[user_id] = user
        self._emit("user_created", {"user_id": user_id, "name": name})
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    # ---- CONNECTION MANAGEMENT ----

    def send_connection_request(self, from_user_id: str, to_user_id: str,
                                message: str = "") -> Connection:
        conn_id = f"conn_{from_user_id}_{to_user_id}"
        conn = Connection(conn_id, from_user_id, to_user_id, message=message)
        with self._data_lock:
            self.connections[conn_id] = conn
        self._emit("connection_requested", {"from": from_user_id, "to": to_user_id})
        return conn

    def accept_connection(self, connection_id: str) -> bool:
        with self._data_lock:
            if connection_id not in self.connections:
                return False
            conn = self.connections[connection_id]
            if conn.status != ConnectionStatus.PENDING:
                return False
            conn.status = ConnectionStatus.ACCEPTED
            self.users[conn.from_user_id].connections.add(conn.to_user_id)
            self.users[conn.to_user_id].connections.add(conn.from_user_id)
        self._emit("connection_accepted", {"user1": conn.from_user_id, "user2": conn.to_user_id})
        return True

    def reject_connection(self, connection_id: str) -> bool:
        with self._data_lock:
            if connection_id not in self.connections:
                return False
            conn = self.connections[connection_id]
            if conn.status != ConnectionStatus.PENDING:
                return False
            conn.status = ConnectionStatus.REJECTED
        self._emit("connection_rejected", {"from": conn.from_user_id, "to": conn.to_user_id})
        return True

    def get_mutual_connections(self, user1_id: str, user2_id: str) -> Set[str]:
        u1 = self.users.get(user1_id)
        u2 = self.users.get(user2_id)
        if not u1 or not u2:
            return set()
        return u1.connections & u2.connections

    # ---- POST MANAGEMENT (Factory) ----

    def create_post(self, post_id: str, author_id: str, post_type: PostType,
                    content: str, visibility: Visibility = Visibility.PUBLIC,
                    **kwargs) -> Post:
        if post_type == PostType.TEXT:
            post = TextPost(post_id, author_id, content, visibility)
        elif post_type == PostType.IMAGE:
            post = ImagePost(post_id, author_id, content, visibility,
                             image_urls=kwargs.get('image_urls', []))
        elif post_type == PostType.VIDEO:
            post = VideoPost(post_id, author_id, content, visibility,
                             video_url=kwargs.get('video_url', ''))
        else:  # ARTICLE
            post = ArticlePost(post_id, author_id, content, visibility,
                               full_text=kwargs.get('full_text', ''))

        with self._data_lock:
            self.posts[post_id] = post

        self._emit("post_created", {
            "post_id": post_id, "author_id": author_id, "content": content[:50]
        })
        return post

    def like_post(self, post_id: str, user_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.likes.add(user_id)
        self._emit("post_liked", {"post_id": post_id, "user_id": user_id})
        return True

    def generate_feed(self, user_id: str, limit: int = 20) -> List[Post]:
        user = self.users.get(user_id)
        if not user:
            return []

        feed_posts = []
        now = datetime.now()

        for post in self.posts.values():
            if post.visibility == Visibility.PRIVATE and post.author_id != user_id:
                continue
            if post.visibility == Visibility.CONNECTIONS:
                if post.author_id not in user.connections and post.author_id != user_id:
                    continue

            engagement = post.engagement_score()
            recency = math.exp(-(now - post.created_at).total_seconds() / (24 * 3600))
            connection_strength = 1.0 if post.author_id in user.connections else 0.5
            score = engagement * recency * connection_strength
            feed_posts.append((score, post))

        feed_posts.sort(reverse=True, key=lambda x: x[0])
        return [p for _, p in feed_posts[:limit]]

    # ---- JOB MANAGEMENT ----

    def post_job(self, job_id: str, company_id: str, title: str, description: str,
                 location: Location, required_skills: List[str],
                 required_experience_years: int) -> Job:
        job = Job(job_id, company_id, title, description, location,
                  required_skills, required_experience_years)
        with self._data_lock:
            self.jobs[job_id] = job
        self._emit("job_posted", {"job_id": job_id, "title": title})
        return job

    def apply_for_job(self, job_id: str, user_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or user_id in job.applications:
            return False
        job.applications.append(user_id)
        score = self.job_matcher.calculate_match_score(job, self.users[user_id])
        self._emit("job_applied", {"job_id": job_id, "user_id": user_id, "match_score": score})
        return True

    def get_matching_candidates(self, job_id: str, threshold: float = 70.0) -> List[Tuple[str, float]]:
        job = self.jobs.get(job_id)
        if not job:
            return []
        candidates = []
        for user_id, user in self.users.items():
            score = self.job_matcher.calculate_match_score(job, user)
            if score >= threshold:
                candidates.append((user_id, score))
        candidates.sort(reverse=True, key=lambda x: x[1])
        return candidates

    def set_job_matcher(self, strategy: JobMatchingStrategy) -> None:
        old = self.job_matcher.name()
        with self._data_lock:
            self.job_matcher = strategy
        self._emit("matcher_changed", {"from": old, "to": strategy.name()})

    # ---- MESSAGING ----

    def send_message(self, msg_id: str, sender_id: str, receiver_id: str,
                     content: str) -> Message:
        msg = Message(msg_id, sender_id, receiver_id, content)
        with self._data_lock:
            self.messages[msg_id] = msg
        self._emit("message_sent", {"sender": sender_id, "receiver": receiver_id})
        return msg

    # ---- RECOMMENDATIONS ----

    def recommend_connections(self, user_id: str, limit: int = 10) -> List[Tuple[str, int]]:
        user = self.users.get(user_id)
        if not user:
            return []

        scores: Dict[str, int] = {}

        # Mutual-connection score
        for conn_id in user.connections:
            for potential_id in self.users[conn_id].connections:
                if potential_id != user_id and potential_id not in user.connections:
                    scores[potential_id] = scores.get(potential_id, 0) + 10

        # Skill overlap score
        user_skill_names = {s.name for s in user.skills}
        for other_id, other_user in self.users.items():
            if other_id == user_id or other_id in user.connections:
                continue
            common = len(user_skill_names & {s.name for s in other_user.skills})
            scores[other_id] = scores.get(other_id, 0) + common * 5

        sorted_recs = sorted(scores.items(), reverse=True, key=lambda x: x[1])
        return sorted_recs[:limit]

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def demo_1_profiles_and_connections() -> None:
    print_section("DEMO 1: USER PROFILES & CONNECTION REQUEST")

    linkedin = LinkedInSystem()   # singleton — same instance each call
    linkedin.register_observer(ConnectionNotifier())

    loc_sf = Location("San Francisco", "USA", 37.7749, -122.4194)
    loc_la = Location("Los Angeles", "USA", 34.0522, -118.2437)

    alice = linkedin.create_user("alice_1", "Alice Johnson", "Senior Engineer @ Google", loc_sf)
    bob   = linkedin.create_user("bob_1",   "Bob Smith",     "Product Manager @ Meta",  loc_la)

    alice.add_skill(Skill("skill_py",   "Python", "Programming"))
    alice.add_skill(Skill("skill_java", "Java",   "Programming"))
    alice.add_skill(Skill("skill_aws",  "AWS",    "Cloud"))

    bob.add_skill(Skill("skill_py",  "Python", "Programming"))
    bob.add_skill(Skill("skill_sql", "SQL",    "Database"))

    alice.add_experience(Experience("Google", "Senior Engineer", datetime(2019, 1, 1)))
    bob.add_experience(Experience("Meta", "PM", datetime(2020, 6, 1)))

    print(f"\n  Alice: {alice.total_experience_years():.1f} years experience")
    print(f"  Bob:   {bob.total_experience_years():.1f} years experience")

    conn = linkedin.send_connection_request("alice_1", "bob_1", "Great to connect!")
    print(f"\n  Connection status: {conn.status.value}")

    linkedin.accept_connection(conn.connection_id)
    print(f"  After acceptance:  {conn.status.value}")
    print(f"  Alice connections: {len(alice.connections)}")
    print(f"  Bob connections:   {len(bob.connections)}")

def demo_2_factory_pattern_posts() -> None:
    print_section("DEMO 2: FACTORY PATTERN - CREATE POST TYPES")

    linkedin = LinkedInSystem()
    linkedin.register_observer(FeedNotifier())

    text_post    = linkedin.create_post("post_1", "alice_1", PostType.TEXT,
                                        "Excited to share my thoughts on cloud architecture!")
    image_post   = linkedin.create_post("post_2", "alice_1", PostType.IMAGE,
                                        "Team photo from our summit",
                                        image_urls=["url1", "url2"])
    article_post = linkedin.create_post("post_3", "alice_1", PostType.ARTICLE,
                                        "Advanced Python Techniques",
                                        full_text="Full article content here...")

    print(f"\n  TextPost type:    {text_post.post_type().value}")
    print(f"  ImagePost type:   {image_post.post_type().value}")
    print(f"  ArticlePost type: {article_post.post_type().value}")

def demo_3_strategy_pattern_job_matching() -> None:
    print_section("DEMO 3: STRATEGY PATTERN - JOB MATCHING")

    linkedin = LinkedInSystem()
    linkedin.register_observer(JobNotifier())

    alice = linkedin.get_user("alice_1")
    bob   = linkedin.get_user("bob_1")

    loc_sf = Location("San Francisco", "USA", 37.7749, -122.4194)

    job = linkedin.post_job("job_1", "comp_google", "Senior Python Engineer",
                            "Build amazing systems", loc_sf,
                            required_skills=["Python", "Java", "AWS"],
                            required_experience_years=5)

    strategies = [SkillBasedMatcher(), LocationBasedMatcher(), HybridMatcher()]
    print(f"\n  Job requires: {', '.join(job.required_skills)}, {job.required_experience_years}+ yrs\n")

    for strategy in strategies:
        linkedin.set_job_matcher(strategy)
        alice_score = strategy.calculate_match_score(job, alice)
        bob_score   = strategy.calculate_match_score(job, bob)
        print(f"  {strategy.name():25} Alice={alice_score:.0f}%  Bob={bob_score:.0f}%")

def demo_4_observer_pattern_feed() -> None:
    print_section("DEMO 4: OBSERVER PATTERN - FEED & ENGAGEMENT")

    linkedin = LinkedInSystem()

    post = linkedin.create_post("post_feed", "alice_1", PostType.TEXT, "Great insights!")
    linkedin.like_post("post_feed", "bob_1")
    print(f"\n  Post engagement score: {post.engagement_score()}")

    feed = linkedin.generate_feed("bob_1", limit=5)
    print(f"  Bob's feed: {len(feed)} posts")
    for i, p in enumerate(feed, 1):
        print(f"    {i}. {p.content[:40]} (engagement: {p.engagement_score()})")

def demo_5_recommendations() -> None:
    print_section("DEMO 5: CONNECTION RECOMMENDATIONS")

    linkedin = LinkedInSystem()

    loc_sf  = Location("San Francisco", "USA", 37.7749, -122.4194)
    charlie = linkedin.create_user("charlie_1", "Charlie Brown", "ML Engineer", loc_sf)
    charlie.add_skill(Skill("skill_py", "Python",          "Programming"))
    charlie.add_skill(Skill("skill_ml", "Machine Learning","AI"))

    conn2 = linkedin.send_connection_request("charlie_1", "bob_1")
    linkedin.accept_connection(conn2.connection_id)

    recs = linkedin.recommend_connections("alice_1", limit=5)
    print(f"\n  Recommendations for Alice:")
    for user_id, score in recs:
        user = linkedin.get_user(user_id)
        print(f"    - {user.name} (score: {score})")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LINKEDIN SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_profiles_and_connections()
    demo_2_factory_pattern_posts()
    demo_3_strategy_pattern_job_matching()
    demo_4_observer_pattern_feed()
    demo_5_recommendations()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **create_user** | RLock on data | Atomic insertion into users dict |
| **accept_connection** | RLock on data | Atomic: check PENDING status + mutual connection add |
| **create_post** | RLock on data | Atomic insertion; notify fires outside lock |
| **set_job_matcher** | RLock on data | Atomic strategy swap |
| **Singleton init** | Class-level RLock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` used throughout (re-entrant — no self-deadlock when methods call each other)
2. ✅ Notifications fire **outside** the data lock (keeps critical sections short)
3. ✅ Double-checked locking for Singleton
4. ✅ `__new__` accepts `*args, **kwargs` to avoid `TypeError` during construction

---

## Demo Scenarios

### Scenario 1: User Profile & Connection Request
```
Create Alice (Python, Java, AWS — 5+ years) and Bob (Python, SQL)
Alice sends connection request → status: pending
Bob accepts → status: accepted
Both appear in each other's connections set
  [CONNECTION] alice_1 and bob_1 are now connected
```

### Scenario 2: Factory Pattern — Create Different Post Types
```
TextPost:    type = text
ImagePost:   type = image   (image_urls attached)
ArticlePost: type = article (full_text attached)
All subtypes share: engagement_score(), likes, comments, shares
  [FEED] New post from alice_1: Excited to share my thoughts...
```

### Scenario 3: Strategy Pattern — Job Matching
```
Job: Senior Python Engineer | Requires: Python, Java, AWS | 5+ years | SF

SkillBasedMatcher:      Alice=100%  Bob=33%
LocationBasedMatcher:   Alice=100%  Bob=50%   (Bob in LA, >50km)
HybridMatcher:          Alice=100%  Bob=43%
```

### Scenario 4: Observer Pattern — Feed & Engagement
```
Alice posts "Great insights!"
Bob likes the post → engagement_score = 1
Bob's feed: 1+ posts ranked by score
```

### Scenario 5: Recommendation Engine
```
Network: Alice ↔ Bob ↔ Charlie
Charlie has [Python, ML]
Recommendations for Alice:
  - Charlie Brown (score: 15)  ← mutual connection (Bob) + skill overlap (Python)
```

---

## Interview Q&A

### Basic Questions

**Q1: How does the Singleton pattern ensure one LinkedInSystem instance?**

A: `LinkedInSystem` uses `__new__` with thread-safe double-checked locking. `_instance` class variable holds the single instance. On the first call, the lock is acquired and the instance created; subsequent calls return the same instance without locking.

**Q2: How does the Factory pattern work for creating posts?**

A: `create_post(post_type, content, **kwargs)` selects the correct subclass based on `PostType` enum — returning `TextPost`, `ImagePost`, `VideoPost`, or `ArticlePost`. This centralizes creation logic and makes adding new post types easy without changing callers.

**Q3: What's the Connection state machine lifecycle?**

A: Connection starts in `PENDING`. From PENDING: `accept_connection()` → `ACCEPTED` (bilateral connection added), `reject_connection()` → `REJECTED`. State check in the method body prevents invalid transitions (e.g., cannot accept after reject).

**Q4: How does Observer pattern notify followers of new posts?**

A: Post creation triggers `_emit("post_created", {...})`. Each registered observer (FeedNotifier, ConnectionNotifier, etc.) receives the event and reacts independently. Producer is fully decoupled from consumers.

**Q5: How do the three job matching strategies differ?**

A: `SkillBasedMatcher` scores the percentage of required skills matched. `LocationBasedMatcher` scores 100% if distance < 50km, else 50%. `ExperienceBasedMatcher` scores 100 minus 10× the year-count delta. `HybridMatcher` combines all three with configurable weights (default 0.5 / 0.3 / 0.2).

### Intermediate Questions

**Q6: How does feed ranking balance engagement, recency, and connection strength?**

A: `score = engagement_score × exp(−age_seconds / 86400) × connection_strength`. Engagement weighs interactions (shares weight 5×). Recency exponentially decays old posts (half-life ≈ 17 hours). Connection strength (1.0 for 1st-degree, 0.5 otherwise) personalises the ranking.

**Q7: How do you handle connection recommendations efficiently?**

A: Iterate the user's 1st-degree connections, collect their connections as candidates (excluding existing connections). Score each candidate: mutual connections × 10 + common skills × 5. Return top 10. Complexity O(D×M) where D = degree, M = mutual set size — manageable in demo; production uses pre-computed graphs.

**Q8: Why use State pattern instead of simple status enum?**

A: The `ConnectionStatus` enum explicitly models lifecycle. State-transition methods (`accept_connection`, `reject_connection`) guard against invalid transitions at the method level — no scattered if-statements. Can graduate to a full State-class pattern if transitions carry complex behaviour.

**Q9: How do you ensure message delivery between users?**

A: Message stored in `self.messages`. Observer pattern (`MessageNotifier`) sends a real-time notification. In production: WebSocket for real-time delivery, Kafka for durability, read-receipt batching for eventual consistency.

**Q10: How does the feed generation algorithm scale?**

A: Collect posts (filtered by visibility), score each, sort in O(P log P). Production strategy: fan-out on write (push to followers' Redis lists), cache feeds for 30 min, use Elasticsearch for full-text search. For celebrity accounts (millions of followers) use pull-based hybrid.

### Advanced Questions

**Q11: How would you distribute the system across multiple servers?**

A: Shard users by `user_id` hash. Connections sharded by `from_user_id`. Posts sharded by `author_id`. Jobs sharded by `company_id`. Cross-shard queries (feed generation) fan out to relevant shards and aggregate. Consistency: eventual for feeds, strong for balance-sensitive operations.

**Q12: How to handle 500M daily active users efficiently?**

A: Decompose into microservices: UserService, ConnectionService, FeedService, JobService, MessageService. Cache layers: Redis for user profiles (1h TTL), posts (30m TTL), connection graph. Elasticsearch for job search. Kafka for async processing (feed generation, notifications). PostgreSQL with read replicas for most reads; sharded writes.

---

## Scaling Q&A

**Q1: Can you handle 1B users with in-memory storage?**
A: No. 1B users × 100 bytes = 100GB metadata alone. Production: PostgreSQL (sharded) for users, Neo4j for the connection graph, Elasticsearch for jobs. In-memory: cache only hot data (top 10K users, feeds for active users). TTL-based invalidation.

**Q2: How to generate personalized feed for 500M DAU in real-time?**
A: Fan-out on write — when a user posts, asynchronously push to followers' feed caches (Redis lists). Hybrid approach: fan-out for accounts with <10K followers, pull-based for celebrities. Pre-compute feeds during low traffic. Cache TTL 30 min. Paginate at 20–50 posts per request.

**Q3: How to make job matching efficient with 10M jobs and 100M users?**
A: Pre-index jobs by (skills, location, experience) in Elasticsearch. Batch 100 applications per background job. Calculate scores in parallel. For recommendations: only consider jobs posted in the last 10 days per user. Score threshold: show only >70% matches.

**Q4: What's the memory footprint if you cache all posts?**
A: 1B posts × 2KB each = 2TB. Unacceptable for in-memory. Cache only recent 1M posts (~20GB). Archive older posts in S3. Elasticsearch indexes searchable metadata. Hot cache stores trending posts only.

**Q5: How to handle 100K concurrent WebSocket connections for messaging?**
A: Connection pooling on server (1000–5000 connections per server). Load-balance across 20+ servers. Kafka for reliable delivery. Redis for presence (online status). Read receipts batch-update (eventual consistency).

**Q6: Can you support recommendations for all users continuously?**
A: Compute on-demand for DAU; batch-compute overnight for inactive users. Cache top 10 recommendations per user. Invalidate on new connection. O(n²) cold-start solved by: pre-computing mutual connections, skill indexing, and incremental updates.

**Q7: How to ensure consistency when a user accepts a connection from two sources?**
A: Optimistic locking with version numbers. `Connection.version` increments on state change. Accept checks: if version != expected → conflict detected. Either retry or use distributed locks (Redis SETNX). Eventual consistency acceptable: "accepted" eventually visible everywhere.

**Q8: How to handle geographic distribution (US, EU, APAC) without high latency?**
A: Multi-region deployment. Regional databases (us-east, eu-west, ap-southeast). Home region is authoritative. Cross-region sync lag <5 min. Users route to closest region. Cross-region friends served via CDN-cached feeds.

**Q9: How much storage for 1 year of posts (1B users, 5 posts/user/year)?**
A: 5B posts × 2KB = 10TB uncompressed. With zlib compression: ~3TB. Sharded across 30 servers = 100GB each. Archive posts >1 year old to cold storage (S3 Glacier = $0.004/GB/month).

**Q10: How to prevent spam and bot accounts creating fake connections?**
A: Rate limiting (max 100 connection requests/day). Honeypot fields. CAPTCHA after 5 failed logins. Review queue for flagged accounts. ML model: detect bot patterns (same message blasted to many users, instant accepts).

**Q11: How to compute recommendations for 500M users?**
A: Nightly batch: 500M ÷ 100 machines = 5M users/machine. 5M × 5ms = 25K seconds ≈ 7 hours. Parallel Spark job. Cache in Redis (compressed). Invalidate incrementally on new connections.

**Q12: How to scale messaging to 1B messages/day?**
A: 1B/day ÷ 86400s ≈ 11.5K msg/sec. Kafka handles 1M msg/sec per cluster. Partition by `conversation_id`. 100 Kafka partitions × 10K msg/sec = 1M msg/sec (safe headroom). Hot messages (7 days) in PostgreSQL; cold in S3. Replication factor 3 for durability.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships and cardinalities
- [ ] Walk through the connection state machine (PENDING → ACCEPTED/REJECTED)
- [ ] Explain feed ranking formula: engagement × recency × connection strength
- [ ] Demonstrate Strategy pattern — swap job matcher at runtime
- [ ] Explain Factory pattern — create TextPost / ImagePost / ArticlePost
- [ ] Explain Observer pattern — decouple post events from notification channels
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety: RLock, double-checked Singleton, notifications outside lock
- [ ] Discuss trade-offs (in-memory vs distributed, fan-out on write vs pull-based feed)

---

**Ready for interview? Build your network and land that job.**
