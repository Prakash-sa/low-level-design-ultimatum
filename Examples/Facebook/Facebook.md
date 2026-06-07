# Facebook — Complete Design Guide

> User profiles, bidirectional friendships, post timelines, personalized feed generation, like/comment interactions, and real-time notifications at social-network scale.

**Scale**: 2B+ users, 500M+ daily active users, 1M+ QPS, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Feed generation, friendship graph, engagement ranking, feed caching, real-time notifications

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
A user creates a profile → adds friends (bidirectional) → publishes posts → friends see posts in their personalized feed ranked by engagement → likes and comments trigger real-time notifications → feed is cached for 5 minutes and invalidated on new posts. Core concerns: efficient feed generation, friendship graph traversal, atomic like counters, and decoupled notifications.

### Core Flow
```
Register User → Add Friends (bidirectional) → Create Post → Feed Generation
                                                               ↓
                                              Fetch friends' posts → Rank (engagement + recency)
                                                               ↓
                                              Cache feed (5 min TTL) → Return top 50

Like / Comment on Post → Increment Counter → Notify Author (Observer)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed, 500M+ daily active users across regions"
2. **What types of posts?** → "Text posts for the interview; mention images/video as extension"
3. **Friends or followers model?** → "Bidirectional friendship (mutual follow)"
4. **Real-time or near-real-time feed?** → "Near-real-time, 5-second notification latency acceptable"
5. **Feed ranking — recency or ML?** → "Engagement + recency for interview; mention ML as extension"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User** | Creates content & interacts | Post, like, comment, add friends, read feed |
| **Platform (Facebook)** | Singleton coordinator | Store users/posts, generate feeds, deliver notifications |
| **System** | Background jobs | Cache invalidation, notification queue, feed pre-computation |

### Functional Requirements (What does the system do?)

✅ **User Profiles**
  - Create user profiles with name and user ID
  - View friend list

✅ **Friendships**
  - Send/accept friend requests (bidirectional)
  - Remove friends

✅ **Posts & Timelines**
  - Create and publish posts (text, visibility: PUBLIC / FRIENDS_ONLY / PRIVATE)
  - Delete/edit posts (soft delete preserves analytics)
  - View own timeline (author's own posts)

✅ **Likes & Comments**
  - Like/unlike posts and comments
  - Add comments to posts
  - Atomic counters (no race conditions)

✅ **Feed Generation**
  - Personalized feed: posts from all friends
  - Rank by engagement (likes + 2×comments) and recency
  - Paginate: top 50 posts per request
  - Cache feed (5-minute TTL, invalidate on new post)

✅ **Notifications**
  - Notify on like, comment, friend request, new post
  - At-least-once delivery
  - Async delivery via observer/pub-sub

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 500M+ simultaneous users  
✅ **Feed Latency**: Feed generation < 200ms (95th percentile)  
✅ **Notification Latency**: Real-time (<5s latency)  
✅ **Consistency**: Consistent read (data accuracy for feeds)  
✅ **Availability**: 99.9% uptime, geographic distribution  
✅ **Throughput**: 1M+ QPS sustained with caching + sharding  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Friends list max** | 10K per user |
| **Feed size** | 50–200 posts per request |
| **Notification delivery** | At-least-once |
| **Comment depth** | Unlimited but display nested |
| **Post visibility** | PUBLIC / FRIENDS_ONLY / PRIVATE |
| **Feed cache TTL** | 5 minutes (invalidate on new post) |
| **Real payment / ad system** | Out of scope for interview |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
User, Post, Comment, FriendRequest, Feed, Notification, Facebook, ...
```

### Step 2.2: Define Core Classes

#### **User** — A person on the platform
```
Properties:
  - user_id: str
  - name: str
  - friends: Set[str] (friend user IDs)
  - posts: List[Post] (own posts)
  - notifications: List[Notification]
  - feed_cache: List[Post] (cached personalized feed)
  - feed_cache_timestamp: Optional[datetime]
  - lock: threading.Lock

Behaviors:
  - add_friend(friend_id): Add to friends set
  - remove_friend(friend_id): Remove from friends set
  - add_post(post): Append to own timeline
  - add_notification(notification): Append alert
  - get_friends(): Thread-safe copy of friends set
```

#### **Post** — A piece of content published by a user
```
Properties:
  - post_id: str
  - author_id: str
  - content: str
  - visibility: Visibility (PUBLIC, FRIENDS_ONLY, PRIVATE)
  - timestamp: datetime
  - likes: Set[str] (user IDs who liked)
  - comments: List[Comment]

Behaviors:
  - like(user_id): Add to likes set
  - unlike(user_id): Remove from likes set
  - add_comment(comment): Append comment
  - get_like_count(): len(likes)
  - get_comment_count(): len(comments)
```

#### **Comment** — A reply to a post
```
Properties:
  - comment_id: str
  - author_id: str
  - post_id: str
  - text: str
  - timestamp: datetime
  - likes: Set[str]

Behaviors:
  - like(user_id): Add to likes set
  - unlike(user_id): Remove from likes set
```

#### **FriendRequest** — A pending friendship invitation
```
Properties:
  - request_id: str
  - sender_id: str
  - receiver_id: str
  - status: RequestStatus (PENDING, ACCEPTED, DECLINED)
  - timestamp: datetime

Behaviors:
  - accept(): Transition to ACCEPTED
  - decline(): Transition to DECLINED
```

#### **Feed** — Personalized aggregated timeline
```
Properties:
  - user_id: str
  - posts: List[Post] (ranked, up to 50)
  - generated_at: datetime
  - ttl_seconds: int (default 300)

Behaviors:
  - is_stale(): now - generated_at > ttl_seconds
  - refresh(posts): Update with newly ranked posts
```

#### **Notification** — An alert for a user
```
Properties:
  - notification_id: str
  - user_id: str (recipient)
  - type: NotificationType (LIKE, COMMENT, FRIEND_REQUEST, POST)
  - actor_id: str (who triggered it)
  - post_id: Optional[str]
  - comment_id: Optional[str]
  - timestamp: datetime
  - read: bool

Behaviors:
  - mark_read(): Set read = True
```

#### **Facebook** — Main controller (Singleton)
```
Properties:
  - users: Dict[str, User]
  - posts: Dict[str, Post]
  - post_counter: int
  - comment_counter: int
  - notification_counter: int
  - lock: threading.RLock  (re-entrant — _notify_user called inside held lock)

Behaviors:
  - create_user(user_id, name): Register user
  - add_friend(user_id, friend_id): Bidirectional friend link
  - create_post(user_id, content, visibility): Publish post
  - like_post(user_id, post_id): Like + notify author
  - unlike_post(user_id, post_id): Remove like
  - comment_post(user_id, post_id, text): Comment + notify author
  - get_feed(user_id): Generate / return cached feed
  - delete_post(user_id, post_id): Soft-delete post
  - get_notifications(user_id): Fetch recent notifications
  - _notify_user(...): Internal: create + deliver notification
```

### Step 2.3: Define Enumerations (State & Type)

```python
class Visibility(Enum):
    PUBLIC = 1          # Anyone can see
    FRIENDS_ONLY = 2    # Only friends see in feed
    PRIVATE = 3         # Only author sees

class NotificationType(Enum):
    LIKE = 1
    COMMENT = 2
    FRIEND_REQUEST = 3
    POST = 4
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **User** | Profile + friendship graph root | Can't link friends, posts, or feeds |
| **Post** | Core content unit | Nothing to feed, like, or comment on |
| **Comment** | Replies create engagement | No threaded conversation |
| **FriendRequest** | Pending state before friendship | No way to model accept/decline flow |
| **Feed** | Aggregated + ranked view | Must recompute every request (O(n·m)) |
| **Notification** | Alert delivery model | No async event propagation |
| **Facebook** | Central coordinator Singleton | No thread-safe single source of truth |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Create User**
```python
def create_user(user_id: str, name: str) -> User:
    """
    Register a new user on the platform.
    Returns: User object.
    Raises: UserAlreadyExistsError if user_id taken.
    Concurrency: THREAD-SAFE
    """
    pass
```

#### **2. Add Friend** ⭐ CRITICAL
```python
def add_friend(user_id: str, friend_id: str) -> bool:
    """
    Create a bidirectional friendship between two users.

    Postcondition: user_id in friend.friends AND friend_id in user.friends

    Returns: True if success, False if either user not found.
    Concurrency: THREAD-SAFE
    Idempotency: YES (adding same friend twice is a no-op via Set)
    """
    pass
```

#### **3. Create Post** ⭐ CRITICAL
```python
def create_post(user_id: str, content: str,
                visibility: Visibility = Visibility.PUBLIC) -> Optional[Post]:
    """
    Publish a post on the user's timeline.

    Returns: Post object with auto-generated post_id.
    Raises: UserNotFoundError if user_id invalid.

    Side Effects:
      - Adds post to user.posts
      - Invalidates friends' feed caches (production: async)
    Concurrency: THREAD-SAFE
    """
    pass
```

#### **4. Like / Unlike Post**
```python
def like_post(user_id: str, post_id: str) -> bool:
    """
    Like a post; atomically add user to post.likes.

    Side Effects: Sends notification to post author (unless self-like).
    Returns: True on success.
    Idempotency: YES (Set.add is idempotent)
    Concurrency: THREAD-SAFE (RLock)
    """
    pass

def unlike_post(user_id: str, post_id: str) -> bool:
    """Remove like; Set.discard is idempotent."""
    pass
```

#### **5. Comment on Post**
```python
def comment_post(user_id: str, post_id: str, text: str) -> Optional[Comment]:
    """
    Add a comment to a post.

    Returns: Comment object with auto-generated comment_id.
    Side Effects: Sends notification to post author.
    Concurrency: THREAD-SAFE (RLock)
    """
    pass
```

#### **6. Get Feed** ⭐ CRITICAL
```python
def get_feed(user_id: str) -> List[Post]:
    """
    Return a personalized, ranked feed of up to 50 posts.

    Algorithm:
      1. Check feed cache (5-min TTL); return cached if fresh.
      2. Collect posts from all friends.
      3. Filter by visibility (PUBLIC or FRIENDS_ONLY).
      4. Rank: primary by engagement (likes + 2×comments), secondary by recency.
      5. Cache result; return top 50.

    Returns: List[Post] sorted by rank.
    Response Time: <200ms (cache hit <5ms)
    """
    pass
```

#### **7. Delete Post**
```python
def delete_post(user_id: str, post_id: str) -> bool:
    """
    Remove a post (author-only).

    Precondition: posts[post_id].author_id == user_id
    Postcondition: post removed from posts dict (soft delete in production)
    Returns: True on success, False on auth failure or not found.
    """
    pass
```

#### **8. Get Notifications**
```python
def get_notifications(user_id: str) -> List[Notification]:
    """
    Fetch the 10 most recent notifications for a user.
    Returns: List[Notification] (newest first).
    """
    pass
```

### Step 3.2: Failure Model

```python
class FacebookException(Exception):
    """Base exception"""
    pass

class UserNotFoundError(FacebookException):
    """user_id does not exist"""
    pass

class PostNotFoundError(FacebookException):
    """post_id does not exist"""
    pass

class UnauthorizedError(FacebookException):
    """User doesn't own the resource"""
    pass
```

### Step 3.3: API Usage Example

```python
fb = Facebook()   # Singleton

# 1. Setup users
john = fb.create_user("U1", "John")
sarah = fb.create_user("U2", "Sarah")

# 2. Friendship
fb.add_friend("U1", "U2")

# 3. Create posts
post = fb.create_post("U2", "Hello world!", Visibility.PUBLIC)

# 4. Interact
fb.like_post("U1", post.post_id)
fb.comment_post("U1", post.post_id, "Great post!")

# 5. Feed
feed = fb.get_feed("U1")
for p in feed:
    print(p.content, p.get_like_count())

# 6. Notifications
for n in fb.get_notifications("U2"):
    print(n.type, n.actor_id)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
Facebook HAS-A users (1:N Composition)
  └─ Facebook owns and manages all User lifecycles

Facebook HAS-A posts (1:N Composition)
  └─ Central post registry for O(1) lookup

User HAS-A posts (1:N Composition)
  └─ User owns their own timeline (author copies)

User HAS-A notifications (1:N Composition)
  └─ User owns their notification inbox

Post HAS-A comments (1:N Composition)
  └─ Post owns its comment thread

Post REFERENCES author via author_id (1:1 Association)
  └─ Post links to User by ID (no ownership)

Comment REFERENCES author via author_id (1:1 Association)
  └─ Comment links to User by ID (no ownership)

User REFERENCES friends via Set[str] (N:M Association)
  └─ Bidirectional friendship graph (friend IDs only, no ownership)
```

### Step 4.2: Complete UML Class Diagram

```
┌───────────────────────────────────────┐
│       Facebook (Singleton)            │
├───────────────────────────────────────┤
│ - _instance: Facebook                 │
│ - users: Dict[str, User]             │
│ - posts: Dict[str, Post]             │
│ - post_counter: int                   │
│ - comment_counter: int                │
│ - notification_counter: int           │
│ - lock: threading.RLock              │
├───────────────────────────────────────┤
│ + create_user(id, name): User         │
│ + add_friend(uid, fid): bool          │
│ + create_post(uid, content): Post     │
│ + like_post(uid, pid): bool           │
│ + unlike_post(uid, pid): bool         │
│ + comment_post(uid, pid, text): Cmt   │
│ + get_feed(uid): List[Post]           │
│ + delete_post(uid, pid): bool         │
│ + get_notifications(uid): List[Notif] │
│ - _notify_user(...): void             │
└──────────────┬────────────────────────┘
       manages 1:N
   ┌──────────┴────────────┐
   ▼                       ▼
┌─────────────────────┐  ┌─────────────────────────┐
│        User         │  │          Post            │
├─────────────────────┤  ├─────────────────────────┤
│ - user_id: str      │  │ - post_id: str           │
│ - name: str         │  │ - author_id: str         │
│ - friends: Set[str] │  │ - content: str           │
│ - posts: List[Post] │  │ - visibility: Visibility │
│ - notifications[]   │  │ - timestamp: datetime    │
│ - feed_cache[]      │  │ - likes: Set[str]        │
│ - lock: Lock        │  │ - comments: List[Comment]│
├─────────────────────┤  ├─────────────────────────┤
│ + add_friend()      │  │ + like(uid): void        │
│ + remove_friend()   │  │ + unlike(uid): void      │
│ + add_post()        │  │ + add_comment(): void    │
│ + get_friends()     │  │ + get_like_count(): int  │
└─────────────────────┘  └────────────┬────────────┘
                                      │ contains 1:N
                                      ▼
                         ┌────────────────────────┐
                         │       Comment          │
                         ├────────────────────────┤
                         │ - comment_id: str      │
                         │ - author_id: str       │
                         │ - post_id: str         │
                         │ - text: str            │
                         │ - timestamp: datetime  │
                         │ - likes: Set[str]      │
                         ├────────────────────────┤
                         │ + like(uid): void      │
                         │ + unlike(uid): void    │
                         └────────────────────────┘

┌────────────────────────┐   ┌────────────────────────┐
│     Notification       │   │    FriendRequest       │
├────────────────────────┤   ├────────────────────────┤
│ - notification_id: str │   │ - request_id: str      │
│ - user_id: str         │   │ - sender_id: str       │
│ - type: NotifType      │   │ - receiver_id: str     │
│ - actor_id: str        │   │ - status: ReqStatus    │
│ - post_id: Optional    │   │ - timestamp: datetime  │
│ - read: bool           │   ├────────────────────────┤
└────────────────────────┘   │ + accept(): void       │
                             │ + decline(): void      │
                             └────────────────────────┘

ENUMERATIONS:
┌──────────────────────┐   ┌─────────────────────────┐
│   Visibility         │   │   NotificationType      │
├──────────────────────┤   ├─────────────────────────┤
│ PUBLIC = 1           │   │ LIKE = 1                │
│ FRIENDS_ONLY = 2     │   │ COMMENT = 2             │
│ PRIVATE = 3          │   │ FRIEND_REQUEST = 3      │
└──────────────────────┘   │ POST = 4                │
                           └─────────────────────────┘

FEED GENERATION FLOW:
REQUEST FEED
  └─→ Check feed_cache (5-min TTL) → HIT: return cached
      └─→ MISS: Get user.friends Set
          └─→ Fetch posts from each friend (visibility filter)
              └─→ Rank: primary=engagement(likes+2×comments),
                         secondary=recency (newest)
                  └─→ Store in feed_cache + set cache timestamp
                      └─→ Return top 50 posts

NOTIFICATION FLOW:
EVENT (LIKE / COMMENT / FRIEND_REQUEST)
  └─→ _notify_user() creates Notification object
      └─→ Append to recipient user.notifications
          └─→ (production: push to Kafka → delivery workers)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| Facebook → Users | 1:N | Composition | Platform owns all users |
| Facebook → Posts | 1:N | Composition | Central post registry |
| User → Posts (own) | 1:N | Composition | User owns their timeline |
| User → Notifications | 1:N | Composition | User owns their inbox |
| User → Friends | N:M | Association | Bidirectional friendship graph |
| Post → Comments | 1:N | Composition | Post owns its thread |
| Post → Author | N:1 | Association | Many posts reference one author |
| Comment → Author | N:1 | Association | Many comments reference one author |
| Notification → Actor/Post | N:1 | Association | Notification references existing entities |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For Facebook)

**Problem**: Multiple threads need one consistent view of users, posts, and friendship graph.

**Solution**: One global Facebook instance with thread-safe initialization.

```python
class Facebook:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):   # *args/**kwargs required — see bug fix note
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
        self.posts: Dict[str, Post] = {}
        self.lock = threading.RLock()   # Re-entrant: _notify_user called inside held lock
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (hard to test), ⚠️ Harder to scale across machines

---

### Pattern 2: **Observer** (For Notifications)

**Problem**: Like/comment/friend events need to trigger notifications without coupling core logic to delivery.

**Solution**: Observer pattern decouples event producer (Facebook) from consumers (notification handlers).

```python
class NotificationObserver(ABC):
    @abstractmethod
    def update(self, event: str, notification: Notification):
        pass

class InAppNotifier(NotificationObserver):
    def update(self, event: str, notification: Notification):
        print(f"  [IN-APP] {event}: notify user {notification.user_id}")

class PushNotifier(NotificationObserver):
    def update(self, event: str, notification: Notification):
        print(f"  [PUSH] {event}: notify user {notification.user_id}")

# Usage
fb.add_observer(InAppNotifier())
fb.add_observer(PushNotifier())
fb.notify_observers("LIKE", notification)
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add email/SMS/push channels  
**Trade-off**: ⚠️ Observer lifecycle management; ⚠️ Synchronous in demo (async in production via Kafka)

---

### Pattern 3: **Strategy** (For Feed Ranking)

**Problem**: Feed ranking varies (recency, engagement, ML-based) and may change.

**Solution**: Pluggable ranking algorithms, swap without modifying feed logic.

```python
class FeedRankingStrategy(ABC):
    @abstractmethod
    def rank(self, posts: List[Post]) -> List[Post]:
        pass

class RecencyRanking(FeedRankingStrategy):
    def rank(self, posts: List[Post]) -> List[Post]:
        return sorted(posts, key=lambda p: p.timestamp, reverse=True)

class EngagementRanking(FeedRankingStrategy):
    def rank(self, posts: List[Post]) -> List[Post]:
        return sorted(posts,
            key=lambda p: p.get_like_count() + p.get_comment_count() * 2,
            reverse=True)

# Usage: Switch ranking at runtime
fb.set_ranking_strategy(EngagementRanking())
feed = fb.get_feed("U1")
```

**Benefit**: ✅ Easy to add ML ranking, seasonal ranking, etc. without touching feed generation  
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 4: **Cache** (For Feed Performance)

**Problem**: Recomputing a feed by scanning all friends' posts on every request is O(friends × posts_per_friend).

**Solution**: Cache the ranked feed per user with a 5-minute TTL; invalidate on new post from a friend.

```python
# On get_feed():
if user.feed_cache and user.feed_cache_timestamp:
    if (datetime.now() - user.feed_cache_timestamp).seconds < 300:
        return user.feed_cache[:50]   # Cache hit — O(1)

# Cache miss: compute, store, return
feed = compute_feed(user)
user.feed_cache = feed
user.feed_cache_timestamp = datetime.now()
```

**Benefit**: ✅ Reduces feed latency from ~200ms → <5ms on cache hit; ✅ Reduces DB load  
**Trade-off**: ⚠️ Up to 5-minute staleness; ⚠️ Cache invalidation complexity (celebrity problem)

---

### Pattern 5: **Pub-Sub** (For Notification Delivery)

**Problem**: Notifications must be delivered to potentially millions of subscribers asynchronously without blocking post/like operations.

**Solution**: Pub-Sub (Kafka in production): event producer publishes to topic; notification workers consume and deliver.

```python
# Producer (inside like_post):
event_bus.publish("like_event", {
    "actor_id": user_id,
    "post_id": post_id,
    "author_id": post.author_id
})

# Consumer (separate notification worker):
for message in event_bus.subscribe("like_event"):
    notify_user(message["author_id"], NotificationType.LIKE, message)
```

**Benefit**: ✅ Decoupled async delivery, ✅ Scales notification workers independently  
**Trade-off**: ⚠️ At-least-once (may duplicate); ⚠️ Adds broker dependency

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Need single global Facebook instance | Consistent state across all clients |
| **Observer** | Like/comment events trigger notifications | Loose coupling, multi-channel delivery |
| **Strategy** | Varying feed ranking algorithms | Pluggable, easy to extend (add ML) |
| **Cache** | Feed recomputation is expensive | Sub-5ms feed reads on cache hit |
| **Pub-Sub** | Async notification delivery at scale | Decoupled, horizontally scalable |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Facebook - Interview Implementation
Demonstrates:
1. User profiles and friendships
2. Posts and timelines
3. Likes and comments
4. Feed generation with caching
5. Notifications
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from collections import defaultdict
import heapq

# ============================================================================
# ENUMERATIONS
# ============================================================================

class Visibility(Enum):
    PUBLIC = 1
    FRIENDS_ONLY = 2
    PRIVATE = 3

class NotificationType(Enum):
    LIKE = 1
    COMMENT = 2
    FRIEND_REQUEST = 3
    POST = 4

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Comment:
    comment_id: str
    author_id: str
    post_id: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    likes: Set[str] = field(default_factory=set)

    def like(self, user_id: str):
        self.likes.add(user_id)

    def unlike(self, user_id: str):
        self.likes.discard(user_id)

@dataclass
class Post:
    post_id: str
    author_id: str
    content: str
    visibility: Visibility = Visibility.PUBLIC
    timestamp: datetime = field(default_factory=datetime.now)
    likes: Set[str] = field(default_factory=set)
    comments: List[Comment] = field(default_factory=list)

    def like(self, user_id: str):
        self.likes.add(user_id)

    def unlike(self, user_id: str):
        self.likes.discard(user_id)

    def add_comment(self, comment: Comment):
        self.comments.append(comment)

    def get_like_count(self) -> int:
        return len(self.likes)

    def get_comment_count(self) -> int:
        return len(self.comments)

@dataclass
class Notification:
    notification_id: str
    user_id: str
    type: NotificationType
    actor_id: str
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False

# ============================================================================
# USER
# ============================================================================

class User:
    def __init__(self, user_id: str, name: str):
        self.user_id = user_id
        self.name = name
        self.friends: Set[str] = set()
        self.posts: List[Post] = []
        self.notifications: List[Notification] = []
        self.feed_cache: List[Post] = []
        self.feed_cache_timestamp: Optional[datetime] = None
        self.lock = threading.Lock()

    def add_friend(self, friend_id: str):
        with self.lock:
            self.friends.add(friend_id)

    def remove_friend(self, friend_id: str):
        with self.lock:
            self.friends.discard(friend_id)

    def add_post(self, post: Post):
        with self.lock:
            self.posts.append(post)

    def add_notification(self, notification: Notification):
        with self.lock:
            self.notifications.append(notification)

    def get_friends(self) -> Set[str]:
        with self.lock:
            return self.friends.copy()

    def __repr__(self):
        return f"User({self.user_id}, {self.name}, Friends: {len(self.friends)})"

# ============================================================================
# FACEBOOK (SINGLETON)
# ============================================================================

class Facebook:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # BUG FIX: Accept *args/**kwargs so Python does not reject the call
        # when __init__ also has a signature — without this, object.__new__
        # raises TypeError when called from __init__ via Singleton.__new__.
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
        self.posts: Dict[str, Post] = {}
        self.post_counter = 0
        self.comment_counter = 0
        self.notification_counter = 0
        # BUG FIX: Use RLock (re-entrant) instead of Lock.
        # _notify_user() is called from inside like_post() and comment_post()
        # which already hold self.lock — a plain Lock would deadlock.
        self.lock = threading.RLock()

    def create_user(self, user_id: str, name: str) -> User:
        with self.lock:
            user = User(user_id, name)
            self.users[user_id] = user
            print(f"+ Created user: {user}")
            return user

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        """Bidirectional friendship"""
        with self.lock:
            if user_id not in self.users or friend_id not in self.users:
                return False

            user = self.users[user_id]
            friend = self.users[friend_id]

            user.add_friend(friend_id)
            friend.add_friend(user_id)

            print(f"+ {user.name} and {friend.name} are now friends")
            return True

    def create_post(self, user_id: str, content: str,
                    visibility: Visibility = Visibility.PUBLIC) -> Optional[Post]:
        with self.lock:
            if user_id not in self.users:
                return None

            self.post_counter += 1
            post_id = f"POST_{self.post_counter}"
            post = Post(post_id, user_id, content, visibility)
            self.posts[post_id] = post
            self.users[user_id].add_post(post)

            print(f"+ Post created: {post_id} by {self.users[user_id].name}")
            return post

    def like_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if post_id not in self.posts or user_id not in self.users:
                return False

            post = self.posts[post_id]
            post.like(user_id)

            # Notify post author (RLock allows re-entry into _notify_user)
            if user_id != post.author_id:
                self._notify_user(post.author_id, NotificationType.LIKE,
                                  user_id, post_id)

            print(f"+ {self.users[user_id].name} liked post {post_id} "
                  f"(Likes: {post.get_like_count()})")
            return True

    def unlike_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if post_id not in self.posts:
                return False

            post = self.posts[post_id]
            post.unlike(user_id)
            print(f"+ {self.users[user_id].name} unliked post {post_id} "
                  f"(Likes: {post.get_like_count()})")
            return True

    def comment_post(self, user_id: str, post_id: str,
                     text: str) -> Optional[Comment]:
        with self.lock:
            if post_id not in self.posts or user_id not in self.users:
                return None

            self.comment_counter += 1
            comment_id = f"COMMENT_{self.comment_counter}"
            comment = Comment(comment_id, user_id, post_id, text)

            post = self.posts[post_id]
            post.add_comment(comment)

            # Notify post author (RLock allows re-entry into _notify_user)
            if user_id != post.author_id:
                self._notify_user(post.author_id, NotificationType.COMMENT,
                                  user_id, post_id, comment_id)

            print(f"+ {self.users[user_id].name} commented on post {post_id} "
                  f"(Comments: {post.get_comment_count()})")
            return comment

    def get_feed(self, user_id: str) -> List[Post]:
        """Generate personalized feed with 5-minute cache"""
        with self.lock:
            if user_id not in self.users:
                return []

            user = self.users[user_id]

            # Cache hit
            if user.feed_cache and user.feed_cache_timestamp:
                age = (datetime.now() - user.feed_cache_timestamp).seconds
                if age < 300:
                    return user.feed_cache[:50]

            # Cache miss — compute feed
            feed = []
            friends = user.get_friends()

            for friend_id in friends:
                if friend_id in self.users:
                    friend = self.users[friend_id]
                    for post in friend.posts:
                        if post.visibility in (Visibility.PUBLIC,
                                               Visibility.FRIENDS_ONLY):
                            feed.append(post)

            # Rank: primary = engagement, secondary = recency
            feed.sort(key=lambda p: p.timestamp, reverse=True)
            feed.sort(
                key=lambda p: p.get_like_count() + p.get_comment_count() * 2,
                reverse=True
            )

            # Store cache
            user.feed_cache = feed
            user.feed_cache_timestamp = datetime.now()

            return feed[:50]

    def delete_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if (post_id not in self.posts or
                    user_id != self.posts[post_id].author_id):
                return False

            del self.posts[post_id]
            print(f"+ Post {post_id} deleted")
            return True

    def _notify_user(self, user_id: str, notification_type: NotificationType,
                     actor_id: str, post_id: Optional[str] = None,
                     comment_id: Optional[str] = None):
        """Internal: create and deliver a notification (called inside lock)."""
        if user_id not in self.users:
            return

        self.notification_counter += 1
        notification = Notification(
            f"NOTIF_{self.notification_counter}",
            user_id,
            notification_type,
            actor_id,
            post_id,
            comment_id
        )
        self.users[user_id].add_notification(notification)
        print(f"  -> Notification sent to {self.users[user_id].name}")

    def get_notifications(self, user_id: str) -> List[Notification]:
        with self.lock:
            if user_id not in self.users:
                return []
            return self.users[user_id].notifications[:10]

    def display_status(self):
        print("\n" + "="*70)
        print("FACEBOOK STATUS")
        print("="*70)
        print(f"Total users: {len(self.users)}")
        print(f"Total posts: {len(self.posts)}")
        total_likes = sum(len(p.likes) for p in self.posts.values())
        total_comments = sum(len(p.comments) for p in self.posts.values())
        print(f"Total likes: {total_likes}")
        print(f"Total comments: {total_comments}")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_users_friendship():
    print("\n" + "="*70)
    print("DEMO 1: CREATE USERS & FRIENDSHIP")
    print("="*70)

    fb = Facebook()
    # Reset singleton state for clean demo
    fb.users.clear(); fb.posts.clear()
    fb.post_counter = 0; fb.comment_counter = 0; fb.notification_counter = 0

    john = fb.create_user("U1", "John")
    sarah = fb.create_user("U2", "Sarah")
    mike = fb.create_user("U3", "Mike")

    fb.add_friend("U1", "U2")
    fb.add_friend("U1", "U3")
    fb.add_friend("U2", "U3")

    fb.display_status()

def demo_2_posts_timeline():
    print("\n" + "="*70)
    print("DEMO 2: CREATE POSTS & TIMELINE")
    print("="*70)

    fb = Facebook()
    fb.users.clear(); fb.posts.clear()
    fb.post_counter = 0; fb.comment_counter = 0; fb.notification_counter = 0

    fb.create_user("U1", "John")
    fb.create_user("U2", "Sarah")

    fb.add_friend("U1", "U2")

    fb.create_post("U2", "Hello world!")
    fb.create_post("U2", "Having a great day!")
    fb.create_post("U1", "Just coding...")

def demo_3_likes_comments():
    print("\n" + "="*70)
    print("DEMO 3: LIKES & COMMENTS")
    print("="*70)

    fb = Facebook()
    fb.users.clear(); fb.posts.clear()
    fb.post_counter = 0; fb.comment_counter = 0; fb.notification_counter = 0

    fb.create_user("U1", "John")
    fb.create_user("U2", "Sarah")
    fb.create_user("U3", "Mike")

    fb.add_friend("U1", "U2")
    fb.add_friend("U3", "U2")

    post = fb.create_post("U2", "Beautiful sunset!")

    print("\nLiking post:")
    fb.like_post("U1", post.post_id)
    fb.like_post("U3", post.post_id)

    print("\nCommenting on post:")
    fb.comment_post("U1", post.post_id, "Amazing!")
    fb.comment_post("U3", post.post_id, "Love this!")

def demo_4_feed_generation():
    print("\n" + "="*70)
    print("DEMO 4: FEED GENERATION")
    print("="*70)

    fb = Facebook()
    fb.users.clear(); fb.posts.clear()
    fb.post_counter = 0; fb.comment_counter = 0; fb.notification_counter = 0

    fb.create_user("U1", "John")
    fb.create_user("U2", "Sarah")
    fb.create_user("U3", "Mike")

    fb.add_friend("U1", "U2")
    fb.add_friend("U1", "U3")

    post1 = fb.create_post("U2", "Coffee time!")
    post2 = fb.create_post("U3", "Gym session!")
    post3 = fb.create_post("U2", "Movie night!")

    fb.like_post("U1", post1.post_id)
    fb.like_post("U1", post3.post_id)
    fb.comment_post("U1", post2.post_id, "Nice!")

    print("\n+ Generating feed for John...")
    feed = fb.get_feed("U1")
    print(f"+ Feed contains {len(feed)} posts")
    for post in feed:
        author = fb.users[post.author_id].name
        print(f"  - {author}: '{post.content}' "
              f"(Likes: {post.get_like_count()}, Comments: {post.get_comment_count()})")

def demo_5_notifications():
    print("\n" + "="*70)
    print("DEMO 5: NOTIFICATIONS")
    print("="*70)

    fb = Facebook()
    fb.users.clear(); fb.posts.clear()
    fb.post_counter = 0; fb.comment_counter = 0; fb.notification_counter = 0

    fb.create_user("U1", "John")
    fb.create_user("U2", "Sarah")

    fb.add_friend("U1", "U2")

    post = fb.create_post("U2", "New photo!")

    print("\nLiking post (notification sent to Sarah):")
    fb.like_post("U1", post.post_id)

    print("\nCommenting (notification sent to Sarah):")
    fb.comment_post("U1", post.post_id, "Beautiful!")

    print("\nSarah's notifications:")
    notifications = fb.get_notifications("U2")
    for notif in notifications:
        actor_name = fb.users[notif.actor_id].name
        print(f"  - {actor_name} {notif.type.name}d your post")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("FACEBOOK - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_users_friendship()
    demo_2_posts_timeline()
    demo_3_likes_comments()
    demo_4_feed_generation()
    demo_5_notifications()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **create_user / add_friend** | RLock on Facebook | Atomic registration + bidirectional link |
| **like_post / comment_post** | RLock on Facebook (re-entrant for _notify_user) | Atomic: mutate + notify without deadlock |
| **get_feed** | RLock on Facebook | Consistent read of friends + posts + cache |
| **User state (friends, posts, notifications)** | Per-user Lock | Fine-grained protection per user object |
| **Singleton init** | Class-level Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` on Facebook allows `_notify_user` to re-enter the same lock
2. ✅ Per-user locks provide fine-grained isolation for user mutations
3. ✅ Observers notified inside lock (safe because RLock); in production, use async queue
4. ✅ Double-checked locking for Singleton with `*args/**kwargs` in `__new__`

---

## Demo Scenarios

### Demo 1: Create User & Friendship
```
+ Created user: User(U1, John, Friends: 0)
+ Created user: User(U2, Sarah, Friends: 0)
+ John and Sarah are now friends
+ John and Mike are now friends
+ Sarah and Mike are now friends
FACEBOOK STATUS: 3 users, 0 posts, 0 likes, 0 comments
```

### Demo 2: Posts & Timeline
```
+ Post created: POST_1 by Sarah  ("Hello world!")
+ Post created: POST_2 by Sarah  ("Having a great day!")
+ Post created: POST_3 by John   ("Just coding...")
```

### Demo 3: Likes & Comments
```
+ John liked post POST_1 (Likes: 1)
  -> Notification sent to Sarah
+ Mike liked post POST_1 (Likes: 2)
  -> Notification sent to Sarah
+ John commented on post POST_1 (Comments: 1)
  -> Notification sent to Sarah
+ Mike commented on post POST_1 (Comments: 2)
  -> Notification sent to Sarah
```

### Demo 4: Feed Generation
```
Generating feed for John...
Feed contains 3 posts (ranked by engagement + recency):
  - Sarah: 'Movie night!'  (Likes: 1, Comments: 0)
  - Sarah: 'Coffee time!'  (Likes: 1, Comments: 0)
  - Mike:  'Gym session!'  (Likes: 0, Comments: 1)
```

### Demo 5: Notifications
```
+ John liked post POST_1
  -> Notification sent to Sarah
+ John commented on post POST_1
  -> Notification sent to Sarah

Sarah's notifications:
  - John LIKEd your post
  - John COMMENTd your post
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you store and retrieve posts?**

A: Store posts in a central dict keyed by `post_id` for O(1) lookup. User timelines hold references to their own Post objects. For feed: iterate over friends' `user.posts` lists, filter by visibility, rank, and cache. In production: indexed DB columns `(author_id, timestamp)` with `ORDER BY timestamp DESC LIMIT 50`.

**Q2: What's the difference between a timeline and a feed?**

A: **Timeline** — all posts by one user (author's own posts, chronological). **Feed** — posts from all friends, aggregated and ranked by engagement + recency. Timeline is 1:1 per author; feed is personalized per viewer based on their friendship graph.

**Q3: How do you handle like/comment operations efficiently?**

A: Likes are stored in a `Set[str]` per post — O(1) add/remove, O(1) count via `len()`. In production: cache the counter in Redis with atomic `INCR`/`DECR`, persist to DB asynchronously every N seconds to avoid O(n) counting.

**Q4: How do you delete a post?**

A: In this implementation: remove from `posts` dict (hard delete). In production: soft delete — mark `deleted=True`, exclude from feed/search, retain for analytics. Hard delete loses engagement history.

**Q5: How do you generate a personalized feed?**

A: (1) Get user's friend list (Set), (2) Collect posts from each friend (filter by visibility), (3) Rank by engagement score (`likes + 2×comments`) with recency as tiebreaker, (4) Cache for 5 minutes, (5) Return top 50.

### Intermediate Questions

**Q6: What about scalability with 500M daily active users?**

A: Fan-out strategies: **Fan-out on Write** — when user posts, push to all followers' feed caches (heavy write, easy read; problem: celebrity with 10M followers = 10M writes). **Fan-out on Read** — compute feed on-the-fly (light write, heavy read). **Hybrid**: fan-out for regular users, lazy-load celebrity posts on read. Use Redis for feed storage with 5-min TTL.

**Q7: How to handle notifications efficiently?**

A: Use a message broker (Kafka/RabbitMQ). On like/comment: produce event → notification workers consume and deliver. Async delivery decouples producer from consumer. Scale: thousands of notification workers consuming from partitioned topic.

**Q8: What about duplicate posts or race conditions?**

A: Use UUID or Snowflake IDs for posts (globally unique). On creation: idempotency key prevents duplicates. For like counters: Redis `INCR` is atomic; no race condition. Optimistic locking on DB rows: increment with version, retry on mismatch.

**Q9: How to handle friend request accept/decline lifecycle?**

A: `FriendRequest` object tracks `status: RequestStatus (PENDING/ACCEPTED/DECLINED)`. On accept: call `add_friend(sender, receiver)` — bidirectional. On decline: mark DECLINED and notify sender. Prevents duplicate requests via Set membership check.

**Q10: What metrics would you track?**

A: Feed cache hit rate, feed generation latency (p50/p95/p99), notification delivery latency, like/comment QPS, friendship graph edge count, DAU/MAU ratio.

### Advanced Questions

**Q11: How to optimize feed ranking with machine learning?**

A: Collect features: author engagement history, post recency, user interaction patterns (liked similar posts?), content signals. Train CTR prediction model. Rank by predicted click-through rate. Trade-off: ML inference adds ~20ms latency vs better relevance. Run offline batch scoring, serve from Redis.

**Q12: How to ensure data consistency in distributed system?**

A: (1) ACID transactions within single shard, (2) Eventual consistency across shards (2-3s lag acceptable for feeds), (3) Event sourcing — store all events, replay to reconstruct state, (4) CQRS — separate read/write models so feed reads don't compete with write throughput.

---

## Scaling Q&A

**Q1: Can you handle 500M daily active users?**

A: Yes, with geographic sharding. Partition users by region (US/EU/ASIA). Each region has its own DB cluster and application servers. Global load balancer routes requests. Cross-region friendships use eventual consistency (2-3s lag). Expected QPS per region: 5-10K.

**Q2: How to prevent feed generation from becoming a bottleneck?**

A: Cache heavily: Redis cluster stores pre-computed user feeds (update on new post). Cache hit rate: 80-90% for active users. For cache misses: async generation (queue), serve stale cache while regenerating. Pre-rank top 50 posts offline every 5 minutes for top users.

**Q3: What if a user has 10M followers and posts once?**

A: Fan-out on write problem. Solution: (1) Celebrity detection: don't fan-out for users with >1M followers, (2) Lazy load: include celebrity post dynamically when followers request feed, (3) Hybrid: fan-out to first 1K followers, lazy-load for the rest. Prevents 10M cascade writes.

**Q4: How to handle timeline inconsistency (post appears then disappears)?**

A: Write-through cache: (1) Write to primary DB, (2) Write to cache, (3) Respond to client. If read hits a stale replica: acceptable lag (couple of seconds). For critical writes: read from primary after write (read-your-writes consistency).

**Q5: Can you support 1M QPS?**

A: Single DB: ~1K QPS. Scale: (1) Read replicas for feed queries, (2) Redis for feed/like caches, (3) N application servers behind load balancer, (4) CDN for static content, (5) Shard DB by user_id. Expected: 100+ servers, 10+ cache nodes, 3+ read replicas per region.

**Q6: What if a comment thread has 100K comments?**

A: Store `parent_comment_id` for nesting. Fetch only top-level comments (20) initially; load replies on demand. Pagination: 10 replies per expand. Prevents full 100K load. Pre-compute `comment_count` counter to avoid O(n) counting.

**Q7: How to archive old posts (data retention)?**

A: Posts older than 1 year: move to cold storage (S3/Glacier). Keep hot DB for recent 1 year. Archived posts: viewable by direct link but not surfaced in feed or search. Reduces hot DB size, improves query performance. Delete after 7 years per policy.

**Q8: How to optimize likes counter for 1M likes per post?**

A: Never query `COUNT(*)`. Maintain a cached counter: `INCR` in Redis on like, `DECR` on unlike. Persist to DB every 1 minute in batch. Up to 1-minute staleness is acceptable. Redis `INCR` is atomic and handles concurrent likes without race conditions.

**Q9: What if notification queue grows to 10M messages?**

A: Scale message broker: add Kafka partitions and consumers. Parallel processing: 1,000 consumers each handling 10K messages/second. If still backing up: reduce delivery guarantee to best-effort, alert ops team, scale horizontally.

**Q10: How to handle friend graph with billions of edges?**

A: Store in graph DB (Neo4j) or denormalize in Redis sorted sets. For 1-hop queries (direct friends): O(1) Redis lookup. For 2-hop (friends of friends): pre-compute offline, store results in cache. Real-time queries: return approximate (sample top 100 friends-of-friends).

**Q11: Can you detect trending topics in real-time?**

A: Stream processing pipeline: Kafka → Flink/Spark Streaming. Count hashtag mentions per minute. Rank top 50. Update every 60 seconds. Store in Redis sorted set (`ZADD`). Serve trending page from Redis cache. Accuracy lag: 1-2 minutes (acceptable for trends).

**Q12: How to handle data migration (moving DBs)?**

A: Dual-write strategy: (1) Write to old DB + new DB simultaneously, (2) Run parallel for 1-2 weeks and verify row counts match, (3) Switch reads to new DB, (4) Keep dual writes until confident, (5) Rollback: switch reads back to old DB if anomalies detected.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships (Facebook → User → Post → Comment)
- [ ] Discuss feed generation algorithm (friendship graph traversal, engagement ranking, cache)
- [ ] Explain bidirectional friendship and the friend request lifecycle
- [ ] Explain like/comment with atomic counters and notification side effects
- [ ] Explain feed cache (5-min TTL, cache miss vs hit path)
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety (RLock re-entrancy, per-user locks, Singleton double-checked lock)
- [ ] Discuss fan-out on write vs read trade-off for celebrity users

---

**Ready for interview? Post something and generate that feed!**
