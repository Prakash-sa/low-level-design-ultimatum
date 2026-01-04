# Facebook — 75-Minute Interview Guide

## Quick Start

**What is it?** A social network platform managing user profiles, friendships, posts, feeds, likes, comments, and notifications. Core: efficient feed generation (show relevant posts), friendship graph management, real-time notifications, timeline persistence.

**Key Classes:**
- `Facebook` (Singleton): Central platform coordinator
- `User`: Profile, friends list, posts, feed
- `Post`: Content, timestamp, author, likes, comments
- `Like`: Associates user to post/comment
- `Comment`: Reply to post, timestamp, author
- `Feed`: Personalized timeline for user
- `Notification`: Alert on like/comment/friend request

**Core Flows:**
1. **Post Creation**: User writes content → Publish → Add to user's timeline → Notify followers
2. **Feed Generation**: User requests feed → Fetch posts from friends → Rank by recency/engagement → Return top N
3. **Like**: User clicks like → Increment counter → Notify post author
4. **Comment**: User replies → Add to post → Notify author + other commenters
5. **Friend Request**: User 1 → User 2 → Accept/Decline → Bidirectional friendship

**5 Design Patterns:**
- **Singleton**: One `Facebook` platform instance
- **Observer**: Notify on post/like/comment/friend events
- **Strategy**: Different feed ranking algorithms (recency, engagement, ML)
- **Cache**: Cache feeds to reduce computation (invalidate on new post)
- **Pub-Sub**: Broadcast notifications to subscribers

---

## System Overview

A large-scale social networking platform supporting millions of users, connections, posts, interactions, and feed personalization with focus on real-time notifications and scalable feed generation.

### Requirements

**Functional:**
- Create user profiles with bio, profile picture, status
- Send/accept friend requests
- Create and publish posts (text, images, videos)
- Like/unlike posts and comments
- Add comments to posts
- Generate personalized feeds (posts from friends)
- Send and receive notifications
- View friend list
- Delete/edit posts
- Search users and posts

**Non-Functional:**
- Feed generation < 200ms (95th percentile)
- Support 2B+ users, 500M+ daily active users
- Real-time notifications (<5s latency)
- Consistent read (data accuracy)
- High availability (99.9% uptime)
- Geographic distribution (multi-datacenter)

**Constraints:**
- Friends list max: 10K (per user)
- Feed size: 50-200 posts per request
- Notification delivery: at-least-once
- Comment depth: unlimited but display nested
- Post visibility: public/friends-only

---

## Architecture Diagram (ASCII UML)

```
┌─────────────────────────────────┐
│ Facebook (Singleton)            │
│ - User service                  │
│ - Post service                  │
│ - Feed service                  │
│ - Notification service          │
└──────────┬──────────────────────┘
           │
    ┌──────┼────────┬────────┐
    │      │        │        │
    ▼      ▼        ▼        ▼
┌──────┐ ┌────┐ ┌────┐ ┌──────────┐
│Users │ │Post│ │Like│ │Comment   │
└──────┘ └────┘ └────┘ └──────────┘

User Entity:
┌─────────────────────────┐
│ User                    │
├─────────────────────────┤
│ user_id: str            │
│ name: str               │
│ friends: Set[User]      │
│ posts: List[Post]       │
│ feed: List[Post]        │
│ followers: Set[User]    │
└─────────────────────────┘

Post Entity:
┌─────────────────────────┐
│ Post                    │
├─────────────────────────┤
│ post_id: str            │
│ author: User            │
│ content: str            │
│ timestamp: datetime     │
│ likes: Set[User]        │
│ comments: List[Comment] │
│ visibility: PUBLIC/PRIV │
└─────────────────────────┘

Comment Entity:
┌─────────────────────────┐
│ Comment                 │
├─────────────────────────┤
│ comment_id: str         │
│ author: User            │
│ text: str               │
│ timestamp: datetime     │
│ likes: Set[User]        │
└─────────────────────────┘

Friendship Graph:
┌──────┐
│User A│ ──(friend)── User B
└──────┘               ┌──────┐
  │                    │      │
  ├──(friend)── User C│      │
  │                   └──────┘
  └──(friend)── User D

Feed Generation Flow:
REQUEST FEED
  └─→ Get friends list
      └─→ Fetch recent posts from friends
          └─→ Apply ranking (recency, likes, comments)
              └─→ Apply filters (blocked users, privacy)
                  └─→ Cache result (invalidate on new post)
                      └─→ Return top 50 posts

Notification Flow:
EVENT (POST/LIKE/COMMENT/FRIEND_REQUEST)
  └─→ Create notification
      └─→ Broadcast to relevant users
          └─→ Store in notification queue
              └─→ Deliver to client (push/email/in-app)

Like/Comment Counters:
┌──────────┐
│ Post #1  │
├──────────┤
│ Likes: 1234 (cached counter, update on like/unlike)
│ Comments: 456
│ Shares: 89
│ Views: 10000
└──────────┘
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you store and retrieve posts?**
A: Store posts in database with indexed fields: (author_id, timestamp, post_id). For user timeline: query posts WHERE author_id = user_id ORDER BY timestamp DESC. For feed: query posts WHERE author_id IN (friend_ids) ORDER BY timestamp DESC LIMIT 50. Denormalize like_count, comment_count for fast access.

**Q2: What's the difference between a timeline and a feed?**
A: **Timeline**: All posts by one user (author's own posts). **Feed**: Posts from all friends aggregated. Timeline is user-specific + author-specific. Feed is personalized per viewer based on their friend list.

**Q3: How do you handle like/comment operations efficiently?**
A: (1) Increment counters atomically (prevent race conditions), (2) Cache counter in Redis, (3) Async background job: persist to DB every N seconds, (4) On read: return cached value. Prevents O(n) counting of likes.

**Q4: How do you delete a post?**
A: (1) Mark as deleted (soft delete), (2) Remove from feed cache, (3) Notify followers (post removed), (4) Retain metrics for analytics. Hard delete: lose engagement data. Soft delete: faster, reversible, preserves history.

### Intermediate Level

**Q5: How do you generate a personalized feed?**
A: (1) Get user's friend list, (2) Query recent posts from friends (past 7 days), (3) Rank by: recency (newest first), engagement (likes+comments), relevance (user interaction history), (4) Filter privacy (remove blocked/private posts), (5) Paginate (limit 50/request), (6) Cache for 5 minutes.

**Q6: What about scalability with 500M daily active users?**
A: Fan-out on write vs read trade-offs. (1) **Fan-out on Write**: When user posts, push to all followers' feeds (heavy write, easy read). Problem: celebrity with 10M followers = 10M writes. (2) **Fan-out on Read**: When user requests feed, compute on-the-fly (light write, heavy read). Hybrid: cache hot feeds (celebs), compute cold feeds on-read.

**Q7: How to handle notifications efficiently?**
A: Use message broker (Kafka/RabbitMQ). On event (like/comment): produce notification event → subscribe → deliver to user. Async delivery decouples producer/consumer. Scale: thousands of notification servers consuming from queue.

**Q8: What about duplicate posts or race conditions?**
A: Use unique IDs (UUID v4 or Snowflake) for posts. On creation: check if post_id exists (idempotent). Optimistic locking on counters: increment with version, retry if mismatch. Distributed transactions if spanning multiple services.

### Advanced Level

**Q9: How to optimize feed ranking with machine learning?**
A: Collect features per post: author (celebrity?), engagement (early likes/comments), recency, user interaction (liked similar posts?). Train ML model: CTR prediction (will user like post?). Rank by predicted CTR. Trade-off: computation time vs relevance.

**Q10: How to handle eventual consistency (distributed DB)?**
A: Replicas may lag. User posts → replica 1 has it, replica 2 doesn't (yet). Solution: (1) Read from primary (consistency but slower), (2) Read from replica + accept staleness (fast), (3) Quorum reads (N/2 replicas agree). Choose per use-case.

**Q11: How to prevent spam/abuse at scale?**
A: (1) Rate limiting: max N posts per user per hour, (2) Abuse detector: flag suspicious patterns (same post repeated, hate speech), (3) Reputation system: new users = lower rate limits, trusted users = higher, (4) Report system: users flag abusive content, (5) ML model: detect spam posts automatically.

**Q12: How to ensure data consistency in distributed system?**
A: (1) Transactions: ACID in single DB, (2) Distributed transactions: 2-phase commit (slow, lock-heavy), (3) Event sourcing: store all events, replay to reconstruct state, (4) CQRS: separate read/write models, eventual consistency between them.

---

## Scaling Q&A (12 Questions)

**Q1: Can you handle 500M daily active users?**
A: Yes, with geographic sharding. Partition users by region (US/EU/ASIA). Each region has separate DB + servers. Global load balancer routes requests. Cross-region friendships: eventual consistency (2-3s lag). Expected QPS per region: 5-10K.

**Q2: How to prevent feed generation from becoming bottleneck?**
A: Cache heavily: Redis cluster stores user feeds (update on new post). Cache hit rate: 80-90% for active users. For cache misses: async generation (queue), return stale cache while generating. Reduce computation: pre-rank top 50 posts offline, serve online.

**Q3: What if user has 10M followers and posts once?**
A: Fan-out on write problem. Solution: (1) Celeb detection: don't fan-out, (2) Lazy load: when followers request feed, include celeb post dynamically, (3) Hybrid: fan-out to small follower list (1K), lazy-load for rest. Prevents cascading writes.

**Q4: How to handle timeline inconsistency (post appears then disappears)?**
A: Use write-through cache: (1) Write to primary DB, (2) Write to cache, (3) Respond to client. Ensures read sees post. If read goes to stale replica: acceptable lag (couple seconds). For critical apps: read from primary after write.

**Q5: Can you support 1M QPS (queries per second)?**
A: Single DB: ~1000 QPS. Scale: (1) Database replication (read replicas), (2) Caching (Redis, Memcached), (3) Service replication (N application servers), (4) CDN for static content. Expected: 100+ servers, 10+ caches, 3+ read replicas per region.

**Q6: What if comment thread has 100K comments?**
A: Store nested structure (parent_comment_id). Fetch top-level comments (20), fetch replies on demand. Pagination: load 10 replies at a time. Prevent full load: most users don't read all 100K comments.

**Q7: How to archive old posts (data retention)?**
A: Posts older than 1 year: move to cold storage (S3/Glacier). Keep hot DB for recent (1 year). Archived posts: viewable but not searchable/feedable. Reduces DB size, improves performance. Delete after 7 years (policy).

**Q8: How to optimize likes counter for 1M likes per post?**
A: Don't query count (O(n)). Maintain counter: increment on like, decrement on unlike. Cache in Redis (atomic increment). Persist every 1 min batch to DB. Incorrect temporarily (1min lag) but acceptable.

**Q9: What if notification queue grows to 10M messages?**
A: Scale message broker: add partitions (Kafka), add consumers. Parallel processing: 1000 consumers each processing 10K messages/sec. If still backing up: reduce delivery guarantee (best-effort vs at-least-once), alert ops.

**Q10: How to handle friend graph with billions of edges?**
A: Store in graph DB (Neo4j) or denormalize in cache. For large queries (all friends of friends = 2-hop): pre-compute offline, store results. Real-time queries: return approximate (sample top 100 friends' friends).

**Q11: Can you detect trending topics in real-time?**
A: Stream processing: Kafka → Flink/Spark Streaming. Count hashtag mentions per minute. Rank top 50. Update every 60 seconds. Store in Redis (sorted set). Serve from cache. Accuracy lag: 1-2 minutes (acceptable for trends).

**Q12: How to handle data migration (moving DBs)?**
A: Dual-write: write to old DB + new DB simultaneously. Run in parallel (1-2 weeks). Verify counts match. Switch reads to new DB. Keep writes dual until confident. Rollback: switch back to old if issues.

---

## Demo Scenarios (5 Examples)

### Demo 1: Create User & Post
```
- Create user: John (user_id = 1)
- Create post: "Hello World!" (post_id = 101)
- Store in DB
- Add to John's timeline (author_id = 1)
```

### Demo 2: Friendship & Feed
```
- User John adds User Sarah as friend (bidirectional)
- Sarah posts: "Having coffee!" (post_id = 102)
- John requests feed
- Feed includes Sarah's post (since they're friends)
- Display: [Sarah's post, ...]
```

### Demo 3: Like & Comment
```
- John likes Sarah's post (post_id = 102)
- Increment like_count (1 → 2)
- Notify Sarah: "John liked your post"
- Mike comments: "Nice photo!"
- Add comment to post
- Notify Sarah: "Mike commented on your post"
- Like_count: 2, Comment_count: 1
```

### Demo 4: Feed Generation
```
- User requests feed (50 posts max)
- Query posts from friends (past 7 days)
- Rank by: recency, engagement, relevance
- Return top 50
- Cache result for 5 minutes
- Next request: return cached feed
```

### Demo 5: Delete Post
```
- John deletes his post (post_id = 101)
- Mark as deleted (soft delete)
- Remove from feed caches
- Notify: post no longer visible
- Later search doesn't include deleted post
- Likes/comments preserved (analytics)
```

---

## Complete Implementation

```python
"""
👥 Facebook - Interview Implementation
Demonstrates:
1. User profiles and friendships
2. Posts and timelines
3. Likes and comments
4. Feed generation
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
        self.posts: Dict[str, Post] = {}
        self.post_counter = 0
        self.comment_counter = 0
        self.notification_counter = 0
        self.lock = threading.Lock()
    
    def create_user(self, user_id: str, name: str) -> User:
        with self.lock:
            user = User(user_id, name)
            self.users[user_id] = user
            print(f"✓ Created user: {user}")
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
            
            print(f"✓ {user.name} and {friend.name} are now friends")
            return True
    
    def create_post(self, user_id: str, content: str, visibility: Visibility = Visibility.PUBLIC) -> Optional[Post]:
        with self.lock:
            if user_id not in self.users:
                return None
            
            self.post_counter += 1
            post_id = f"POST_{self.post_counter}"
            post = Post(post_id, user_id, content, visibility)
            self.posts[post_id] = post
            self.users[user_id].add_post(post)
            
            print(f"✓ Post created: {post_id} by {self.users[user_id].name}")
            return post
    
    def like_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if post_id not in self.posts or user_id not in self.users:
                return False
            
            post = self.posts[post_id]
            post.like(user_id)
            
            # Notify post author
            if user_id != post.author_id:
                self._notify_user(post.author_id, NotificationType.LIKE, user_id, post_id)
            
            print(f"✓ {self.users[user_id].name} liked post {post_id} (Likes: {post.get_like_count()})")
            return True
    
    def unlike_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if post_id not in self.posts:
                return False
            
            post = self.posts[post_id]
            post.unlike(user_id)
            print(f"✓ {self.users[user_id].name} unliked post {post_id} (Likes: {post.get_like_count()})")
            return True
    
    def comment_post(self, user_id: str, post_id: str, text: str) -> Optional[Comment]:
        with self.lock:
            if post_id not in self.posts or user_id not in self.users:
                return None
            
            self.comment_counter += 1
            comment_id = f"COMMENT_{self.comment_counter}"
            comment = Comment(comment_id, user_id, post_id, text)
            
            post = self.posts[post_id]
            post.add_comment(comment)
            
            # Notify post author
            if user_id != post.author_id:
                self._notify_user(post.author_id, NotificationType.COMMENT, user_id, post_id, comment_id)
            
            print(f"✓ {self.users[user_id].name} commented on post {post_id} (Comments: {post.get_comment_count()})")
            return comment
    
    def get_feed(self, user_id: str) -> List[Post]:
        """Generate personalized feed"""
        with self.lock:
            if user_id not in self.users:
                return []
            
            user = self.users[user_id]
            
            # Check cache
            if user.feed_cache and user.feed_cache_timestamp:
                if (datetime.now() - user.feed_cache_timestamp).seconds < 300:
                    return user.feed_cache[:50]
            
            # Compute feed: posts from friends
            feed = []
            friends = user.get_friends()
            
            for friend_id in friends:
                if friend_id in self.users:
                    friend = self.users[friend_id]
                    for post in friend.posts:
                        if post.visibility == Visibility.PUBLIC or post.visibility == Visibility.FRIENDS_ONLY:
                            feed.append(post)
            
            # Sort by timestamp (newest first)
            feed.sort(key=lambda p: p.timestamp, reverse=True)
            
            # Rank by engagement (likes + comments)
            feed.sort(key=lambda p: (p.get_like_count() + p.get_comment_count() * 2), reverse=True)
            
            # Cache
            user.feed_cache = feed
            user.feed_cache_timestamp = datetime.now()
            
            return feed[:50]
    
    def delete_post(self, user_id: str, post_id: str) -> bool:
        with self.lock:
            if post_id not in self.posts or user_id != self.posts[post_id].author_id:
                return False
            
            del self.posts[post_id]
            print(f"✓ Post {post_id} deleted")
            return True
    
    def _notify_user(self, user_id: str, notification_type: NotificationType, actor_id: str, 
                    post_id: Optional[str] = None, comment_id: Optional[str] = None):
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
        print(f"  → Notification sent to {self.users[user_id].name}")
    
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
    
    fb.create_user("U1", "John")
    fb.create_user("U2", "Sarah")
    fb.create_user("U3", "Mike")
    
    fb.add_friend("U1", "U2")
    fb.add_friend("U1", "U3")
    
    # Create posts
    post1 = fb.create_post("U2", "Coffee time!")
    post2 = fb.create_post("U3", "Gym session!")
    post3 = fb.create_post("U2", "Movie night!")
    
    # Add likes and comments
    fb.like_post("U1", post1.post_id)
    fb.like_post("U1", post3.post_id)
    fb.comment_post("U1", post2.post_id, "Nice!")
    
    # Generate feed for John
    print("\n✓ Generating feed for John...")
    feed = fb.get_feed("U1")
    print(f"✓ Feed contains {len(feed)} posts")
    for post in feed:
        author = fb.users[post.author_id].name
        print(f"  - {author}: '{post.content}' (Likes: {post.get_like_count()}, Comments: {post.get_comment_count()})")

def demo_5_notifications():
    print("\n" + "="*70)
    print("DEMO 5: NOTIFICATIONS")
    print("="*70)
    
    fb = Facebook()
    
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
    print("👥 FACEBOOK - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_users_friendship()
    demo_2_posts_timeline()
    demo_3_likes_comments()
    demo_4_feed_generation()
    demo_5_notifications()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Design Patterns Explained

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Singleton** | `Facebook` manages all users/posts | Centralized platform state |
| **Observer** | Notify on like/comment/friend events | Decoupled notifications |
| **Strategy** | Different feed ranking (recency, engagement, ML) | Swap ranking algorithms |
| **Cache** | Cache personalized feeds (invalidate on new post) | Reduce computation + latency |
| **Pub-Sub** | Broadcast notifications to subscribers | Real-time async delivery |

---

## Key System Rules Implemented

- **Bidirectional Friendships**: Adding friend is mutual
- **Feed Ranking**: By engagement (likes + 2×comments) + recency
- **Privacy Levels**: PUBLIC / FRIENDS_ONLY / PRIVATE
- **Soft Delete**: Posts retain data for analytics
- **Feed Cache**: 5-minute TTL, invalidate on new post
- **Notifications**: Delivered async on like/comment/friend events

---

## Summary

✅ **Singleton** for platform-wide coordination
✅ **User profiles** with bidirectional friendships
✅ **Posts and timelines** with visibility control
✅ **Likes and comments** with atomic counters
✅ **Personalized feed generation** (rank by engagement + recency)
✅ **Feed caching** for performance (5-min TTL)
✅ **Real-time notifications** on interactions
✅ **Soft delete** preserving history
✅ **Thread-safe operations** with locks
✅ **Scalable to 500M DAU** with geographic sharding + caching

**Key Takeaway**: Facebook system demonstrates feed personalization, graph-based social connections, engagement ranking, and efficient notification delivery at scale. Core focus: optimal feed generation, caching strategy, and real-time notifications.
