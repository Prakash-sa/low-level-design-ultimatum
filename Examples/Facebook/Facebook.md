# Facebook — 75-Minute Interview Guide

## Quick Start Overview

## Quick Overview
Design a social networking platform with users, posts, comments, likes, friend connections, news feed ranking, and notifications.

**Core Challenge**: Bidirectional friendships, personalized feed ranking, privacy controls, and notification fan-out.

---

## 75-Minute Timeline

| Time | Phase | Focus |
|------|-------|-------|
| 0-5 min | Requirements | Clarify features: users, friends, posts, engagement, feed, privacy |
| 5-15 min | Architecture | Draw UML, choose patterns (Singleton, Strategy, Observer, State, Composite) |
| 15-35 min | Core Entities | Implement User, Post, Comment, FriendRequest, Notification |
| 35-45 min | Feed Ranking | Implement 3 strategies: Chronological, Engagement, Affinity |
| 45-55 min | System Logic | Friend requests, post creation, likes, comments, privacy checks |
| 55-65 min | Notifications | Observer pattern for friend requests, likes, comments, tags |
| 65-70 min | Thread Safety | Locks for friend acceptance, post likes, comment creation |
| 70-75 min | Demo & Q&A | Run 5 demos, answer questions on scaling and trade-offs |

---

## Core Entities (30 seconds each)

### 1. User
- **Attributes**: user_id, name, email, friends (Set), posts (List)
- **Methods**: add_friend(), is_friend(), get_mutual_friends()
- **Why Set for friends?** O(1) lookup, auto-uniqueness, efficient intersection

### 2. Post
- **Attributes**: post_id, author_id, content, privacy (PUBLIC/FRIENDS/ONLY_ME), likes (Set), comments (List)
- **Methods**: add_like(), get_engagement_score(), can_view()
- **Engagement**: likes + (comments * 2) - comments weighted higher

### 3. Comment
- **Attributes**: comment_id, author_id, post_id, parent_comment_id, replies (List)
- **Methods**: add_reply(), is_reply()
- **Pattern**: Composite - supports nested replies with unlimited depth

### 4. FriendRequest
- **Attributes**: request_id, from_user_id, to_user_id, state (PENDING/ACCEPTED/REJECTED/BLOCKED)
- **Methods**: accept(), reject(), block()
- **Pattern**: State machine - enforces valid transitions

### 5. Notification
- **Attributes**: notification_id, type (FRIEND_REQUEST/LIKE/COMMENT/TAG), actor_id, target_id
- **Methods**: mark_as_read(), generate_message()
- **Pattern**: Observer - decouples actions from delivery

---

## Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Why Each?)

### 1. Singleton (FacebookSystem)
**Why?** Single system instance, centralized state for users/posts/notifications  
**Alternative?** Dependency injection (but adds complexity for interview)

### 2. Strategy (FeedRankingStrategy)
**Why?** Swap feed algorithms without changing system code  
**Strategies**: ChronologicalFeed, EngagementBasedFeed, FriendAffinityFeed  
**Trade-off**: More classes vs flexibility

### 3. Observer (NotificationObserver)
**Why?** Decouple post/comment actions from notification delivery  
**Observers**: EmailNotifier, PushNotifier, SMSNotifier  
**Trade-off**: Loose coupling vs delivery guarantees

### 4. State (FriendRequestState)
**Why?** Manage request lifecycle transitions clearly  
**States**: PENDING → ACCEPTED/REJECTED/BLOCKED  
**Trade-off**: State explosion for complex workflows

### 5. Composite (Comment)
**Why?** Uniform interface for comments and nested replies  
**Structure**: Comments have replies (List), replies have replies  
**Trade-off**: Unlimited depth vs query complexity

---

## Key Algorithms

### 1. Mutual Friends (O(min(F1, F2)))
```
mutual = user1.friends ∩ user2.friends
```
Use Set intersection for efficiency.

### 2. Engagement Score
```
score = likes_count + (comments_count * 2)
```
Comments weighted 2x because they require more effort.

### 3. Feed Generation (O(F*P + N log N))
```
1. Collect posts from all friends (O(F*P))
2. Filter by privacy can_view() (O(N))
3. Apply ranking strategy - sort (O(N log N))
4. Return top 50 posts (pagination)
```

### 4. Friend Affinity Ranking
```
affinity_score = engagement * friend_weight * recency_factor

friend_weight:
  - Best friends (10+ interactions): 3.0
  - Regular (3-10 interactions): 2.0
  - Distant (<3 interactions): 1.0

recency_factor:
  - Last 24 hours: 1.0
  - 1-7 days: 0.8
  - 7-30 days: 0.5
  - Older: 0.3
```

### 5. Privacy Check
```
if privacy == PUBLIC: return True
if privacy == ONLY_ME: return viewer == author
if privacy == FRIENDS: return viewer == author OR author in viewer.friends
```

---

## Interview Talking Points

### When Asked About Scaling
1. **Feed Generation**: Pre-compute feeds (fan-out on write), cache 5-10 minutes
2. **Database**: Index on (author_id, timestamp), (user_id), pagination
3. **Notifications**: Message queue (Kafka) for async delivery, batch similar notifications
4. **Caching**: Redis for user profiles (1hr), feeds (10min), mutual friends (1 day)
5. **Sharding**: Shard users by user_id, posts by post_id

### When Asked About Privacy
1. **Three Levels**: PUBLIC (anyone), FRIENDS (friends only), ONLY_ME (author only)
2. **Tagged Users Exception**: Tagged users can view FRIENDS posts even if not friends
3. **Feed Filtering**: Always check can_view() before returning posts
4. **Author Override**: Author always can view own posts regardless of privacy

### When Asked About Friendships
1. **Bidirectional**: When A accepts B's request, both A.friends and B.friends updated
2. **Set vs List**: Set for O(1) is_friend() lookup and efficient mutual friends calculation
3. **State Machine**: PENDING → ACCEPTED/REJECTED/BLOCKED (no reversal)
4. **Validation**: Cannot send to self, if already friends, or if blocked

### When Asked About Feed Ranking
1. **Chronological**: Simple, fair, predictable (good for small user base)
2. **Engagement**: Promotes viral content (risk: echo chamber, fake engagement)
3. **Affinity**: Personalized, prioritizes close friends (requires interaction tracking)
4. **Production**: Hybrid with ML models, A/B testing

### When Asked About Thread Safety
1. **Friend Acceptance**: Lock both users' friends sets (system_lock)
2. **Post Likes**: Fine-grained lock per post (post_locks[post_id])
3. **Comment Creation**: Lock per post to update comments list
4. **Feed Generation**: Read-only, no lock needed
5. **Why Fine-Grained?**: Reduces contention, higher concurrency

---

## Common Mistakes to Avoid

1. ❌ Using List for friends (O(n) lookup, duplicates possible)
2. ❌ Hard-coding feed ranking (not extensible)
3. ❌ Forgetting privacy checks in feed generation
4. ❌ Fetching all posts (use pagination, time filters)
5. ❌ Synchronous notification delivery (blocks request)
6. ❌ Global lock for all operations (high contention)
7. ❌ Not validating friend requests (allow self-friend, duplicates)
8. ❌ Ignoring edge cases (deleted posts, blocked users)

---

## 5 Demo Scenarios to Run

1. **Basic User & Friends**: Create users, send requests, accept, view mutual friends
2. **Posts with Privacy**: Create PUBLIC/FRIENDS/ONLY_ME posts, verify visibility
3. **Engagement**: Like posts, add comments, reply to comments, calculate engagement score
4. **Feed Ranking**: Generate feed with 3 strategies, compare order
5. **Notifications**: Trigger friend request, like, comment, tag notifications

---

## Expected Output from Demos

### Demo 1: Friends
```
Created users: Alice, Bob, Charlie
Alice sends friend request to Bob → Bob receives notification
Bob accepts → Alice and Bob are friends (bidirectional)
Mutual friends between Alice and Bob: {Charlie}
```

### Demo 2: Privacy
```
Alice's PUBLIC post → Visible to all
Bob's FRIENDS post → Visible to friends only (Alice yes, stranger no)
Charlie's ONLY_ME post → Visible only to Charlie
```

### Demo 3: Engagement
```
Post P1: 2 likes + 3 comments = 2 + (3*2) = 8 engagement score
Nested comment: Comment → Reply (Composite pattern)
```

### Demo 4: Feed Ranking
```
ChronologicalFeed: [P5, P4, P2, P1] (newest first)
EngagementBasedFeed: [P5(14), P1(8), P2(0), P4(0)] (highest score first)
FriendAffinityFeed: [P5, P1, P2, P4] (weighted by friend closeness)
```

### Demo 5: Notifications
```
Friend request → FRIEND_REQUEST notification
Accept → FRIEND_ACCEPTED notification
Like → LIKE notification
Comment → COMMENT notification
Tag → TAG notification
```

---

## Quick Win Phrases for Interview

1. **"I'll use Set for friends because it provides O(1) lookup for is_friend() and efficient intersection for mutual friends."**

2. **"Feed ranking needs Strategy pattern so we can swap algorithms - start simple with Chronological, then add Engagement and Affinity."**

3. **"Comments 2x weight because they indicate deeper engagement than likes."**

4. **"Privacy check at feed generation: can_view() validates PUBLIC/FRIENDS/ONLY_ME before returning posts."**

5. **"Bidirectional friendship means updating both users' friends sets atomically when request is accepted."**

6. **"Observer pattern decouples post actions from notifications - add EmailNotifier, PushNotifier without changing Post class."**

7. **"Fine-grained locking per post reduces contention vs system-wide lock."**

8. **"For scaling, pre-compute feeds (fan-out on write), cache 10 minutes, paginate 50 posts, pre-filter last 30 days."**

---

## Interview Success Checklist

✅ Explained 5 core entities (User, Post, Comment, FriendRequest, Notification)  
✅ Drew ASCII UML showing relationships  
✅ Implemented 5 design patterns (Singleton, Strategy, Observer, State, Composite)  
✅ Explained Set vs List for friends (O(1) lookup)  
✅ Implemented 3 feed ranking strategies  
✅ Explained privacy levels (PUBLIC/FRIENDS/ONLY_ME)  
✅ Calculated engagement score (likes + comments*2)  
✅ Implemented mutual friends (Set intersection)  
✅ Discussed thread safety (fine-grained locks)  
✅ Optimized with caching, pagination, pre-filtering  
✅ Handled edge cases (self-friend, privacy, deleted content)  
✅ Ran 5 working demos  
✅ Answered scaling questions (fan-out, caching, sharding)  

---

## Final Tip

**Start Simple, Then Extend**: Begin with basic chronological feed and simple friendships. Once working, propose extensions: "We could add engagement-based ranking for viral content" or "For personalization, we could track interaction history for affinity scores." This shows iterative thinking and product sense.

**Time Management**: If running short on time, prioritize Singleton + Strategy patterns and basic feed generation. Skip Observer/Composite if needed - you can describe them verbally.

**Run the Code**: If you wrote Python/Java, actually run it! Seeing output proves correctness and shows attention to detail.


## 75-Minute Guide

## System Overview
Design a social networking platform like Facebook with core features: user profiles, friend connections, posts, comments, likes, news feed generation, and privacy controls. Focus on feed ranking algorithms, friend relationship management, and notification systems.

**Key Challenges**: Bidirectional friend relationships, feed ranking with engagement signals, privacy levels, notification fan-out, and preventing circular dependencies in social graphs.

---

## Requirements Clarification (0-5 minutes)

### Functional Requirements
1. **User Management**: Create profiles, update info, search users
2. **Friend System**: Send/accept/reject friend requests, unfriend, view mutual friends
3. **Posts**: Create text/image posts, edit/delete own posts, tag friends
4. **Engagement**: Like/unlike posts, comment on posts, reply to comments
5. **News Feed**: Generate personalized feed based on friends' posts and engagement
6. **Privacy**: Control post visibility (Public, Friends, Only Me)
7. **Notifications**: Friend requests, likes, comments, mentions

### Non-Functional Requirements
- Handle millions of users and posts
- Feed generation < 500ms
- Notification delivery < 1 second
- Support concurrent user actions (thread-safety)
- Scalable feed ranking algorithm

### Out of Scope
- Messaging, groups, pages, events, marketplace
- Image/video storage (assume URLs)
- Real-time chat, live streaming
- Advanced ML-based recommendations

---

## Architecture & Design Patterns (5-15 minutes)

### Design Patterns to Implement

#### 1. Singleton Pattern
**Usage**: FacebookSystem - centralized coordination
```
FacebookSystem (Singleton)
├─ manages all users
├─ coordinates friend requests
├─ generates feeds
└─ dispatches notifications
```

#### 2. Strategy Pattern
**Usage**: FeedRankingStrategy - different feed algorithms
- **ChronologicalFeed**: Sort by timestamp (simple)
- **EngagementBasedFeed**: Prioritize posts with high likes/comments
- **FriendAffinityFeed**: Weight posts from close friends higher

#### 3. Observer Pattern
**Usage**: NotificationObserver - notify users of events
- User receives notification when: friend request, like, comment, mention
- Decouples post/comment actions from notification logic

#### 4. State Pattern
**Usage**: FriendRequestState - manage request lifecycle
- States: PENDING, ACCEPTED, REJECTED, BLOCKED
- Prevents invalid state transitions

#### 5. Composite Pattern
**Usage**: Comment hierarchy (comments and replies)
- Comments can have nested replies
- Uniform interface for single comment and comment threads

---

## Core Entities & Relationships (15-35 minutes)

### Entity Diagram (ASCII UML)
```
┌─────────────────────────────────────────────────────────────────────┐
│                         FACEBOOK SYSTEM                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              FacebookSystem (Singleton)                     │    │
│  │  - users: Dict[str, User]                                   │    │
│  │  - posts: Dict[str, Post]                                   │    │
│  │  - friend_requests: List[FriendRequest]                     │    │
│  │  - feed_strategy: FeedRankingStrategy                       │    │
│  │  - notification_observers: List[NotificationObserver]       │    │
│  │  + create_user() → User                                     │    │
│  │  + send_friend_request(from_id, to_id) → FriendRequest     │    │
│  │  + create_post(user_id, content, privacy) → Post           │    │
│  │  + generate_feed(user_id) → List[Post]                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────┐         ┌──────────────┐       ┌─────────────┐   │
│  │    User     │         │     Post     │       │   Comment   │   │
│  ├─────────────┤         ├──────────────┤       ├─────────────┤   │
│  │- user_id    │1      * │- post_id     │1    * │- comment_id │   │
│  │- name       │────────>│- author_id   │──────>│- author_id  │   │
│  │- email      │  owns   │- content     │ has   │- content    │   │
│  │- friends: []│         │- privacy     │       │- parent_id  │   │
│  │- posts: []  │         │- timestamp   │       │- timestamp  │   │
│  │- profile    │         │- likes: []   │       │- replies:[] │   │
│  └─────────────┘         │- comments:[] │       └─────────────┘   │
│        │                 └──────────────┘                           │
│        │ *                                                           │
│        │                                                             │
│  ┌─────▼───────────┐    ┌──────────────────────┐                  │
│  │ FriendRequest   │    │ FeedRankingStrategy  │                  │
│  ├─────────────────┤    ├──────────────────────┤                  │
│  │- request_id     │    │<<interface>>         │                  │
│  │- from_user_id   │    │+ rank_feed()         │                  │
│  │- to_user_id     │    └──────────────────────┘                  │
│  │- state          │            ▲                                  │
│  │- timestamp      │            │                                  │
│  └─────────────────┘    ┌───────┴────────┬────────────────┐       │
│                         │                │                │       │
│              ┌──────────┴───┐  ┌────────┴──────┐ ┌───────┴─────┐ │
│              │Chronological │  │EngagementBased│ │FriendAffinity│ │
│              └──────────────┘  └───────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. User Entity
**Responsibility**: Represents a Facebook user with profile and social connections

**Attributes**:
- `user_id: str` - Unique identifier
- `name: str` - Display name
- `email: str` - Contact email
- `bio: str` - Profile bio
- `profile_picture: str` - URL to profile image
- `friends: Set[str]` - Set of friend user IDs (bidirectional)
- `posts: List[str]` - Post IDs created by user
- `created_at: datetime` - Account creation timestamp

**Key Methods**:
- `add_friend(user_id)` - Add to friends set
- `remove_friend(user_id)` - Remove from friends set
- `is_friend(user_id) → bool` - Check friendship status
- `get_mutual_friends(other_user) → Set[str]` - Find common friends

**Business Logic**:
- Friends list is bidirectional (if A friends B, B friends A)
- Cannot add self as friend
- Mutual friends help in friend suggestions

### 2. Post Entity
**Responsibility**: Represents user-generated content with engagement tracking

**Attributes**:
- `post_id: str` - Unique identifier
- `author_id: str` - User who created post
- `content: str` - Post text content
- `image_urls: List[str]` - Attached image URLs
- `privacy: Privacy` - PUBLIC, FRIENDS, ONLY_ME
- `tagged_users: Set[str]` - Users tagged in post
- `likes: Set[str]` - User IDs who liked
- `comments: List[str]` - Comment IDs
- `timestamp: datetime` - Creation time
- `edited_at: Optional[datetime]` - Last edit time

**Key Methods**:
- `add_like(user_id)` - User likes post
- `remove_like(user_id)` - User unlikes post
- `add_comment(comment_id)` - Attach comment
- `get_engagement_score() → float` - Calculate likes + comments count
- `can_view(viewer_id) → bool` - Check privacy permissions

**Business Logic**:
- Privacy levels: PUBLIC (anyone), FRIENDS (friends only), ONLY_ME (author only)
- Tagged users get notification
- Engagement score = likes_count + (comments_count * 2)
- Users can only like once (Set ensures uniqueness)

### 3. Comment Entity
**Responsibility**: User comments on posts with support for nested replies

**Attributes**:
- `comment_id: str` - Unique identifier
- `author_id: str` - User who commented
- `post_id: str` - Parent post
- `content: str` - Comment text
- `parent_comment_id: Optional[str]` - Parent comment (for replies)
- `replies: List[str]` - Child comment IDs
- `likes: Set[str]` - User IDs who liked comment
- `timestamp: datetime` - Creation time

**Key Methods**:
- `add_reply(comment_id)` - Add nested reply
- `add_like(user_id)` - Like comment
- `is_reply() → bool` - Check if this is a reply to another comment
- `get_thread_depth() → int` - Calculate nesting level

**Business Logic**:
- Comments can be top-level (on post) or replies (on comment)
- Supports unlimited nesting depth (Composite pattern)
- Author of parent post/comment gets notification

### 4. FriendRequest Entity
**Responsibility**: Manages friend connection lifecycle with state machine

**Attributes**:
- `request_id: str` - Unique identifier
- `from_user_id: str` - User who sent request
- `to_user_id: str` - User who receives request
- `state: FriendRequestState` - PENDING, ACCEPTED, REJECTED, BLOCKED
- `timestamp: datetime` - Request creation time
- `responded_at: Optional[datetime]` - Response timestamp

**Key Methods**:
- `accept()` - Transition to ACCEPTED, add both users as friends
- `reject()` - Transition to REJECTED
- `block()` - Transition to BLOCKED, prevent future requests
- `is_pending() → bool` - Check if awaiting response

**Business Logic**:
- State transitions: PENDING → ACCEPTED/REJECTED/BLOCKED
- Cannot transition from ACCEPTED/REJECTED/BLOCKED back to PENDING
- Accepting adds bidirectional friendship
- Blocking prevents new requests from same user

### 5. Notification Entity
**Responsibility**: Inform users of social interactions

**Attributes**:
- `notification_id: str` - Unique identifier
- `user_id: str` - Recipient user
- `type: NotificationType` - FRIEND_REQUEST, LIKE, COMMENT, MENTION, TAG
- `actor_id: str` - User who triggered notification
- `target_id: str` - Post/comment/request ID
- `message: str` - Display message
- `is_read: bool` - Read status
- `timestamp: datetime` - Creation time

**Key Methods**:
- `mark_as_read()` - Set is_read = True
- `generate_message() → str` - Create user-friendly message

**Business Logic**:
- Types: FRIEND_REQUEST ("X sent you a friend request"), LIKE ("X liked your post"), COMMENT ("X commented on your post"), MENTION ("X mentioned you"), TAG ("X tagged you")
- Observer pattern: actions trigger notification creation
- Users receive notification only if not the actor (don't notify self)

---

## Feed Ranking Strategies (35-45 minutes)

### Strategy Interface
```python
class FeedRankingStrategy(ABC):
    @abstractmethod
    def rank_feed(self, user: User, posts: List[Post]) -> List[Post]:
        """Rank posts for user's feed"""
        pass
```

### 1. ChronologicalFeed Strategy
**Algorithm**: Sort posts by timestamp (newest first)
```
Input: User U, Posts [P1, P2, P3, ...]
Output: Sorted posts by timestamp DESC

Steps:
1. Filter posts visible to user (based on privacy)
2. Sort by timestamp (newest first)
3. Return sorted list
```

**Time Complexity**: O(n log n) for sorting
**Use Case**: Simple feed, small user base

### 2. EngagementBasedFeed Strategy
**Algorithm**: Rank posts by engagement score
```
Engagement Score = (likes_count * 1.0) + (comments_count * 2.0)

Input: User U, Posts [P1, P2, P3, ...]
Output: Posts sorted by engagement DESC, then timestamp DESC

Steps:
1. Filter posts visible to user
2. Calculate engagement score for each post
3. Sort by (engagement DESC, timestamp DESC)
4. Return top N posts
```

**Time Complexity**: O(n log n)
**Use Case**: Promote viral content

### 3. FriendAffinityFeed Strategy
**Algorithm**: Weight posts from close friends higher
```
Affinity Score = (engagement_score * friend_weight) * recency_factor

friend_weight calculation:
- Best friends (high interaction): 3.0
- Regular friends (medium interaction): 2.0
- Distant friends (low interaction): 1.0

recency_factor:
- Last 24 hours: 1.0
- 1-7 days: 0.8
- 7-30 days: 0.5
- Older: 0.3

Input: User U, Posts [P1, P2, P3, ...]
Output: Posts sorted by affinity score DESC

Steps:
1. Filter posts visible to user
2. For each post:
   a. Calculate engagement_score
   b. Determine friend_weight (based on interaction history)
   c. Calculate recency_factor
   d. affinity_score = engagement * friend_weight * recency
3. Sort by affinity_score DESC
4. Return top N posts
```

**Time Complexity**: O(n log n)
**Use Case**: Personalized feed, large user base

**Friend Weight Calculation** (simplified):
- Track interaction count (likes, comments from user to friend)
- High interaction (>10/week): weight 3.0
- Medium (3-10/week): weight 2.0
- Low (<3/week): weight 1.0

---

## Key Algorithms & Business Logic (45-60 minutes)

### Algorithm 1: Mutual Friends Calculation
```
Input: User A, User B
Output: Set of mutual friend IDs

Steps:
1. Get A's friends set: friends_A
2. Get B's friends set: friends_B
3. Return intersection: friends_A ∩ friends_B

Time Complexity: O(min(|friends_A|, |friends_B|)) using set intersection
```

### Algorithm 2: Friend Suggestion (People You May Know)
```
Input: User U
Output: List of suggested user IDs

Steps:
1. Initialize suggestions = []
2. For each friend F in U.friends:
   a. For each friend_of_friend FOF in F.friends:
      i.  If FOF not in U.friends AND FOF != U:
          - Calculate mutual_count = |U.friends ∩ FOF.friends|
          - Add (FOF, mutual_count) to suggestions
3. Sort suggestions by mutual_count DESC
4. Return top 10 user IDs

Time Complexity: O(F * F^2) worst case, where F = avg friends count
Optimization: Cache mutual friends, limit depth
```

### Algorithm 3: News Feed Generation
```
Input: User U, FeedRankingStrategy strategy
Output: List of Post objects for feed

Steps:
1. Collect all posts from friends:
   posts = []
   For each friend_id in U.friends:
       friend = get_user(friend_id)
       For each post_id in friend.posts:
           post = get_post(post_id)
           If post.can_view(U.user_id):  # Check privacy
               posts.append(post)

2. Apply ranking strategy:
   ranked_posts = strategy.rank_feed(U, posts)

3. Return top N posts (e.g., 50)

Time Complexity: O(F * P + N log N)
- F = friends count, P = avg posts per friend, N = total posts
- Sorting dominates: O(N log N)

Optimization:
- Pre-filter by timestamp (last 30 days)
- Pagination: fetch 50 posts per page
- Cache feed for 5-10 minutes
```

### Algorithm 4: Notification Fan-Out
```
When user U likes post P:

Steps:
1. Add U to P.likes set
2. Get post author: author = get_user(P.author_id)
3. If U != author:  # Don't notify self
   a. Create notification:
      - type: LIKE
      - user_id: author.user_id
      - actor_id: U.user_id
      - target_id: P.post_id
      - message: "U liked your post"
   b. Notify all observers (NotificationObserver)

4. If post has tagged users:
   For each tagged_user_id in P.tagged_users:
       If tagged_user_id != U:
           Create TAG notification

Time Complexity: O(1) for single post like
Fan-out: O(T) where T = tagged users count

Optimization:
- Batch notifications (group multiple likes)
- Use message queue for async delivery
```

### Algorithm 5: Privacy Check
```
Input: Post P, Viewer V
Output: bool (can view or not)

Steps:
1. If P.privacy == PUBLIC:
       return True

2. If P.privacy == ONLY_ME:
       return V.user_id == P.author_id

3. If P.privacy == FRIENDS:
       author = get_user(P.author_id)
       return V.user_id in author.friends OR V.user_id == P.author_id

Time Complexity: O(1) with set lookup for friends
```

---

## Thread Safety & Concurrency (60-65 minutes)

### Critical Sections Requiring Locks

1. **Friend Request Operations**
   - Accepting request: must update both users' friends sets atomically
   - Lock: `friend_request_lock`
   - Operations: accept(), reject(), send_friend_request()

2. **Post Like/Unlike**
   - Concurrent likes on same post: must update likes set atomically
   - Lock: `post_lock` per post (fine-grained locking)
   - Operations: add_like(), remove_like()

3. **Comment Creation**
   - Adding comment to post: must update post's comments list
   - Lock: `post_lock` per post
   - Operations: create_comment(), add_comment()

4. **Feed Generation**
   - Reading friends' posts: no lock needed (read-only)
   - If updating feed cache: `feed_cache_lock` per user

### Locking Strategy
```python
class FacebookSystem:
    def __init__(self):
        self.system_lock = threading.Lock()  # Coarse-grained
        self.post_locks: Dict[str, threading.Lock] = {}  # Fine-grained
        
    def get_post_lock(self, post_id: str) -> threading.Lock:
        if post_id not in self.post_locks:
            self.post_locks[post_id] = threading.Lock()
        return self.post_locks[post_id]
```

**Thread-Safe Operations**:
- Use `threading.Lock()` for mutual exclusion
- Acquire lock before modifying shared state
- Release lock in `finally` block to prevent deadlocks

---

## SOLID Principles Mapping (65-70 minutes)

### Single Responsibility Principle (SRP)
- **User**: Manages user profile and friend list only
- **Post**: Manages post content and engagement only
- **FacebookSystem**: Coordinates operations, doesn't implement business logic
- **FeedRankingStrategy**: Each strategy focuses on one ranking algorithm

### Open/Closed Principle (OCP)
- **FeedRankingStrategy**: Extensible via new strategy classes (EngagementBased, FriendAffinity) without modifying existing code
- **NotificationObserver**: Add new observers without changing notification logic

### Liskov Substitution Principle (LSP)
- All `FeedRankingStrategy` implementations can substitute base interface
- System works with any strategy: `system.set_feed_strategy(new_strategy)`

### Interface Segregation Principle (ISP)
- **FeedRankingStrategy**: Only requires `rank_feed()` method
- **NotificationObserver**: Only requires `on_notify()` method
- Clients depend on minimal interfaces

### Dependency Inversion Principle (DIP)
- **FacebookSystem** depends on `FeedRankingStrategy` abstraction, not concrete implementations
- Strategies injected via constructor/setter: `FacebookSystem(strategy=ChronologicalFeed())`

---

## Demo Scenarios & Testing (70-75 minutes)

### Demo 1: Basic User & Friend Operations
```
Scenario: Create users, send friend request, accept, view mutual friends

Steps:
1. Create users: Alice, Bob, Charlie
2. Alice sends friend request to Bob
3. Bob accepts request
4. Verify: Alice.friends contains Bob, Bob.friends contains Alice
5. Alice sends friend request to Charlie
6. Charlie accepts
7. Bob sends friend request to Charlie
8. Charlie accepts
9. Calculate mutual friends: Alice & Bob → [Charlie]

Expected Output:
- Friend requests: PENDING → ACCEPTED
- Bidirectional friendships established
- Mutual friends: Charlie appears for Alice-Bob pair
```

### Demo 2: Post Creation with Privacy Levels
```
Scenario: Create posts with different privacy, verify visibility

Steps:
1. Alice creates PUBLIC post
2. Bob creates FRIENDS post
3. Charlie creates ONLY_ME post
4. Test visibility:
   - Alice can view: own PUBLIC post, Bob's FRIENDS post (friends), NOT Charlie's ONLY_ME
   - Bob can view: Alice's PUBLIC post, own FRIENDS post, NOT Charlie's ONLY_ME
   - Charlie can view: Alice's PUBLIC post, NOT Bob's FRIENDS (not friends), own ONLY_ME

Expected Output:
- PUBLIC posts visible to all
- FRIENDS posts visible only to friends
- ONLY_ME posts visible only to author
```

### Demo 3: Engagement (Likes, Comments)
```
Scenario: Users like and comment on posts, verify engagement score

Steps:
1. Alice creates post P1
2. Bob likes P1
3. Charlie likes P1
4. Bob comments on P1: "Great post!"
5. Charlie comments on P1: "Awesome!"
6. Alice replies to Bob's comment: "Thanks!"
7. Calculate engagement: 2 likes + 3 comments = 2 + (3 * 2) = 8 points

Expected Output:
- P1.likes = {Bob, Charlie}
- P1.comments = [Comment1, Comment2]
- Comment1.replies = [Reply1]
- Engagement score: 8
```

### Demo 4: Feed Generation with Different Strategies
```
Scenario: Generate feed using 3 ranking strategies

Setup:
1. Alice friends with Bob, Charlie
2. Bob creates post P1 (10 likes, 2 comments) 2 days ago
3. Charlie creates post P2 (3 likes, 1 comment) 1 day ago
4. Bob creates post P3 (1 like, 0 comments) 1 hour ago

Test ChronologicalFeed:
- Alice's feed: [P3, P2, P1] (newest first)

Test EngagementBasedFeed:
- P1 engagement: 10 + (2*2) = 14
- P2 engagement: 3 + (1*2) = 5
- P3 engagement: 1 + (0*2) = 1
- Alice's feed: [P1, P2, P3] (highest engagement first)

Test FriendAffinityFeed:
- Assume Alice interacts more with Charlie (weight 3.0) than Bob (weight 2.0)
- P1: 14 * 2.0 * 0.8 = 22.4 (Bob, 2 days old)
- P2: 5 * 3.0 * 1.0 = 15 (Charlie, 1 day old)
- P3: 1 * 2.0 * 1.0 = 2 (Bob, recent)
- Alice's feed: [P1, P2, P3] (affinity-weighted)

Expected Output:
- Different strategies produce different feed orders
- Strategy pattern allows swapping algorithms easily
```

### Demo 5: Notifications & Observer Pattern
```
Scenario: Trigger notifications on user actions

Steps:
1. Register NotificationObserver for Alice
2. Bob sends friend request to Alice
   → Alice receives FRIEND_REQUEST notification
3. Alice accepts request
   → Bob receives ACCEPTED notification
4. Bob creates post P1
5. Alice likes P1
   → Bob receives LIKE notification
6. Alice comments on P1
   → Bob receives COMMENT notification
7. Bob tags Alice in post P2
   → Alice receives TAG notification

Expected Output:
- 5 notifications created (1 friend request, 1 accept, 1 like, 1 comment, 1 tag)
- Observer pattern decouples actions from notifications
- Notifications contain actor, target, message
```

---

## Interview Q&A - Progressive Difficulty

### Basic Level (Understanding)

**Q1: What are the core entities in Facebook system?**
**A**: User (profiles, friends), Post (content, engagement), Comment (nested replies), FriendRequest (connection lifecycle), Notification (user alerts). User owns posts, posts have comments, users send friend requests, actions trigger notifications.

**Q2: How does the friend relationship work?**
**A**: Bidirectional relationship stored as Set[str] of user IDs in each User. When A sends request and B accepts, both A.friends and B.friends are updated. Using Set ensures uniqueness and O(1) lookup for is_friend() checks.

**Q3: What privacy levels are supported for posts?**
**A**: Three levels - PUBLIC (anyone can view), FRIENDS (only friends can view), ONLY_ME (only author can view). Privacy check performed during feed generation using can_view(viewer_id) method.

**Q4: Explain the FriendRequest state machine.**
**A**: Four states - PENDING (awaiting response), ACCEPTED (friends connected), REJECTED (request denied), BLOCKED (sender blocked). Transitions: PENDING → ACCEPTED/REJECTED/BLOCKED. Cannot revert to PENDING once processed.

### Intermediate Level (Design Decisions)

**Q5: Why use Strategy pattern for feed ranking?**
**A**: Allows swapping ranking algorithms without modifying FacebookSystem. ChronologicalFeed for simplicity, EngagementBasedFeed for viral content, FriendAffinityFeed for personalization. System depends on abstraction (FeedRankingStrategy), concrete strategies injected at runtime.

**Q6: How does the engagement score calculation work?**
**A**: `engagement_score = (likes_count * 1.0) + (comments_count * 2.0)`. Comments weighted higher (2x) because they indicate deeper engagement than likes. Used by EngagementBasedFeed to prioritize viral posts. Can extend with shares, reactions (love, angry) for more nuance.

**Q7: Explain the Observer pattern for notifications.**
**A**: When action occurs (like, comment, friend request), system notifies all registered NotificationObserver instances. Observers create Notification entities and deliver to users. Decouples action logic (like post) from notification logic (send email/push). Supports multiple observers (EmailNotifier, PushNotifier, SMSNotifier).

**Q8: How do you handle nested comments (replies)?**
**A**: Composite pattern - Comment has optional parent_comment_id and list of reply IDs. Top-level comments have parent_comment_id=None. Replies reference parent. Supports unlimited nesting depth. Traverse tree recursively for display.

### Advanced Level (Scalability & Trade-offs)

**Q9: How would you optimize feed generation for millions of users?**
**A**: 
1. **Pre-filtering**: Only fetch posts from last 30 days (reduce dataset)
2. **Pagination**: Fetch 50 posts per page, not all posts
3. **Caching**: Cache feed for 5-10 minutes per user (Redis)
4. **Async processing**: Pre-compute feeds offline for active users
5. **Indexing**: Index posts by author_id, timestamp for fast retrieval
6. **Fan-out on write**: When user creates post, push to all friends' feed caches (trade write latency for read speed)

**Q10: What are the thread safety concerns in this system?**
**A**: 
- **Friend request acceptance**: Must update both users' friends sets atomically (use lock)
- **Post likes**: Concurrent users liking same post (lock per post)
- **Comment creation**: Adding comment to post's list (lock per post)
- **Feed generation**: Read-only, no lock needed (but cache updates need lock)
Use fine-grained locking (per post) instead of coarse-grained (system-wide) to reduce contention.

**Q11: How would you implement friend suggestions (People You May Know)?**
**A**: 
Algorithm: Find friends-of-friends not already friends.
```
1. For each friend F:
   - For each friend_of_friend FOF in F.friends:
     - If FOF not in user.friends AND FOF != user:
       - Count mutual friends
       - Add to suggestions
2. Sort by mutual_count DESC
3. Return top 10
```
Optimization: Precompute suggestions daily (offline job), store in cache. Use graph traversal (BFS) limited to depth 2. Consider factors: mutual friends count, shared groups, work/school info.

**Q12: What are the trade-offs between different feed ranking strategies?**
**A**:
- **ChronologicalFeed**: 
  - Pros: Simple, predictable, fair to all posts
  - Cons: No personalization, viral content buried if old
- **EngagementBasedFeed**:
  - Pros: Promotes popular content, increases user engagement
  - Cons: Echo chamber effect, new posts get no visibility, gaming via fake likes
- **FriendAffinityFeed**:
  - Pros: Personalized, shows close friends first, better user experience
  - Cons: Complex to compute, requires interaction tracking, cold start problem (new users have no history)

Choice depends on product goals: simplicity (Chronological), engagement (EngagementBased), personalization (FriendAffinity). Production systems use hybrid approach with ML models.

---

## System Class Diagram (ASCII UML)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            CLASS DIAGRAM                                    │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    FacebookSystem (Singleton)                            │
├─────────────────────────────────────────────────────────────────────────┤
│ - _instance: FacebookSystem                                              │
│ - users: Dict[str, User]                                                 │
│ - posts: Dict[str, Post]                                                 │
│ - comments: Dict[str, Comment]                                           │
│ - friend_requests: List[FriendRequest]                                   │
│ - notifications: List[Notification]                                      │
│ - feed_strategy: FeedRankingStrategy                                     │
│ - notification_observers: List[NotificationObserver]                     │
│ - system_lock: threading.Lock                                            │
├─────────────────────────────────────────────────────────────────────────┤
│ + get_instance() → FacebookSystem                                        │
│ + create_user(name, email, bio) → User                                   │
│ + send_friend_request(from_id, to_id) → FriendRequest                   │
│ + accept_friend_request(request_id) → bool                               │
│ + create_post(user_id, content, privacy, images, tags) → Post           │
│ + like_post(user_id, post_id) → bool                                     │
│ + create_comment(user_id, post_id, content, parent_id) → Comment        │
│ + generate_feed(user_id, limit) → List[Post]                            │
│ + set_feed_strategy(strategy: FeedRankingStrategy)                       │
│ + add_notification_observer(observer: NotificationObserver)              │
│ + notify_observers(notification: Notification)                           │
└─────────────────────────────────────────────────────────────────────────┘
            │                     │                      │
            │ manages             │ coordinates          │ generates
            ▼                     ▼                      ▼
┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│      User           │  │  FriendRequest   │  │   Notification       │
├─────────────────────┤  ├──────────────────┤  ├──────────────────────┤
│- user_id: str       │  │- request_id: str │  │- notification_id: str│
│- name: str          │  │- from_user_id    │  │- user_id: str        │
│- email: str         │  │- to_user_id: str │  │- type: NotifType     │
│- bio: str           │  │- state: State    │  │- actor_id: str       │
│- profile_picture    │  │- timestamp       │  │- target_id: str      │
│- friends: Set[str]  │  │- responded_at    │  │- message: str        │
│- posts: List[str]   │  ├──────────────────┤  │- is_read: bool       │
│- created_at         │  │+ accept()        │  │- timestamp           │
├─────────────────────┤  │+ reject()        │  ├──────────────────────┤
│+ add_friend(id)     │  │+ block()         │  │+ mark_as_read()      │
│+ remove_friend(id)  │  │+ is_pending()    │  │+ generate_message()  │
│+ is_friend(id)      │  └──────────────────┘  └──────────────────────┘
│+ get_mutual_friends │
│  (other) → Set[str] │
└─────────────────────┘
         │ 1
         │ owns
         │ *
         ▼
┌─────────────────────────────────────────────┐
│              Post                            │
├─────────────────────────────────────────────┤
│- post_id: str                                │
│- author_id: str                              │
│- content: str                                │
│- image_urls: List[str]                       │
│- privacy: Privacy (PUBLIC/FRIENDS/ONLY_ME)  │
│- tagged_users: Set[str]                      │
│- likes: Set[str]                             │
│- comments: List[str]                         │
│- timestamp: datetime                         │
│- edited_at: Optional[datetime]               │
├─────────────────────────────────────────────┤
│+ add_like(user_id)                           │
│+ remove_like(user_id)                        │
│+ add_comment(comment_id)                     │
│+ get_engagement_score() → float              │
│+ can_view(viewer_id) → bool                  │
└─────────────────────────────────────────────┘
         │ 1
         │ has
         │ *
         ▼
┌─────────────────────────────────────────────┐
│              Comment                         │
├─────────────────────────────────────────────┤
│- comment_id: str                             │
│- author_id: str                              │
│- post_id: str                                │
│- content: str                                │
│- parent_comment_id: Optional[str]            │
│- replies: List[str]                          │
│- likes: Set[str]                             │
│- timestamp: datetime                         │
├─────────────────────────────────────────────┤
│+ add_reply(comment_id)                       │
│+ add_like(user_id)                           │
│+ is_reply() → bool                           │
│+ get_thread_depth() → int                    │
└─────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│           FeedRankingStrategy (Abstract)                          │
├──────────────────────────────────────────────────────────────────┤
│ + rank_feed(user: User, posts: List[Post]) → List[Post]          │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ implements
           ┌──────────────────┼──────────────────┐
           │                  │                  │
┌──────────┴──────────┐ ┌─────┴──────────┐ ┌────┴────────────────┐
│ ChronologicalFeed   │ │EngagementBased │ │ FriendAffinityFeed  │
│                     │ │    Feed        │ │                     │
├─────────────────────┤ ├────────────────┤ ├─────────────────────┤
│+ rank_feed()        │ │+ rank_feed()   │ │+ rank_feed()        │
│  → sort by time     │ │  → sort by     │ │  → sort by affinity │
│     DESC            │ │     engagement │ │     score           │
└─────────────────────┘ └────────────────┘ └─────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│       NotificationObserver (Abstract)                             │
├──────────────────────────────────────────────────────────────────┤
│ + on_notify(notification: Notification)                           │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ implements
           ┌──────────────────┼──────────────────┐
           │                  │                  │
┌──────────┴──────────┐ ┌─────┴──────────┐ ┌────┴────────────┐
│  EmailNotifier      │ │  PushNotifier  │ │  SMSNotifier    │
├─────────────────────┤ ├────────────────┤ ├─────────────────┤
│+ on_notify()        │ │+ on_notify()   │ │+ on_notify()    │
│  → send email       │ │  → send push   │ │  → send SMS     │
└─────────────────────┘ └────────────────┘ └─────────────────┘

Enumerations:
┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────┐
│ FriendRequestState│  │      Privacy        │  │ NotificationType │
├──────────────────┤  ├─────────────────────┤  ├──────────────────┤
│ PENDING          │  │ PUBLIC              │  │ FRIEND_REQUEST   │
│ ACCEPTED         │  │ FRIENDS             │  │ LIKE             │
│ REJECTED         │  │ ONLY_ME             │  │ COMMENT          │
│ BLOCKED          │  └─────────────────────┘  │ MENTION          │
└──────────────────┘                            │ TAG              │
                                                └──────────────────┘
```

---

## Performance Optimization Strategies

1. **Database Indexing**:
   - Index on user_id, post_id, timestamp
   - Composite index on (author_id, timestamp) for user's posts
   - Index on friends set for fast is_friend() lookup

2. **Caching**:
   - Cache user profiles (Redis, 1 hour TTL)
   - Cache news feeds (5-10 minutes TTL)
   - Cache mutual friends calculation (1 day TTL)

3. **Feed Generation**:
   - Pre-filter posts by timestamp (last 30 days)
   - Pagination (50 posts per page)
   - Fan-out on write for active users (pre-compute feeds)

4. **Notification Delivery**:
   - Use message queue (Kafka, RabbitMQ) for async delivery
   - Batch notifications (group multiple likes)
   - Rate limiting (max 100 notifications/minute per user)

5. **Concurrency**:
   - Fine-grained locking (per post, per user) vs coarse-grained
   - Read-write locks for feed generation (multiple readers, single writer)
   - Optimistic locking for post likes (retry on conflict)

---

## Edge Cases & Validation

1. **Friend Request**:
   - Cannot send request to self
   - Cannot send duplicate request (check existing PENDING)
   - Cannot send if already friends
   - Cannot send if blocked by recipient

2. **Post Privacy**:
   - Tagged users can view FRIENDS posts even if not friends
   - Author can always view own posts
   - Privacy can be changed after creation (re-validate feed)

3. **Comment Nesting**:
   - Limit nesting depth (e.g., 10 levels) to prevent performance issues
   - Cannot comment on deleted post
   - Cannot reply to deleted comment

4. **Feed Generation**:
   - Empty feed if user has no friends
   - Handle deleted posts (filter out)
   - Handle blocked users (exclude their posts)

5. **Notifications**:
   - Don't notify user of own actions (self-like, self-comment)
   - Batch notifications (if 10 people like, show "10 people liked your post")
   - Mark as read when user views

---

## Anti-Patterns to Avoid

1. ❌ **God Object**: Don't put all business logic in FacebookSystem - delegate to entities
2. ❌ **Tight Coupling**: Don't hard-code feed ranking - use Strategy pattern
3. ❌ **No Privacy Checks**: Always validate can_view() before returning posts
4. ❌ **Unbounded Queries**: Don't fetch all posts - use pagination and time filters
5. ❌ **Synchronous Notifications**: Don't send notifications in request path - use async
6. ❌ **Global Locks**: Don't lock entire system - use fine-grained locks per resource
7. ❌ **No Input Validation**: Validate user inputs (empty content, invalid IDs)

---

## Success Checklist for Interview

- [ ] Explained core entities: User, Post, Comment, FriendRequest, Notification
- [ ] Drew ASCII UML diagram showing relationships
- [ ] Implemented Singleton (FacebookSystem)
- [ ] Implemented Strategy (3 feed ranking algorithms)
- [ ] Implemented Observer (notification system)
- [ ] Implemented State (friend request lifecycle)
- [ ] Implemented Composite (nested comments)
- [ ] Explained bidirectional friendship with Set
- [ ] Explained privacy levels (PUBLIC, FRIENDS, ONLY_ME)
- [ ] Explained engagement score calculation
- [ ] Explained mutual friends algorithm
- [ ] Explained feed generation with ranking
- [ ] Discussed thread safety (locks per post)
- [ ] Discussed performance optimizations (caching, pagination)
- [ ] Handled edge cases (self-friend, privacy, deleted content)
- [ ] Mapped SOLID principles to design
- [ ] Ran 5 demo scenarios successfully
- [ ] Answered Q&A from basic to advanced level

**Interview Tip**: Start with simple chronological feed, then propose engagement-based and affinity-based as extensions. Explain trade-offs clearly.


## Detailed Design Reference

## Entity Summary

| Entity | Responsibility | Key Attributes | Key Methods |
|--------|---------------|----------------|-------------|
| **User** | User profile & social graph | user_id, name, email, friends (Set), posts (List) | add_friend(), is_friend(), get_mutual_friends() |
| **Post** | User content & engagement | post_id, author_id, content, privacy, likes, comments | add_like(), get_engagement_score(), can_view() |
| **Comment** | Post comments & replies | comment_id, author_id, content, parent_comment_id, replies | add_reply(), is_reply() |
| **FriendRequest** | Connection lifecycle | request_id, from/to user_id, state | accept(), reject(), block() |
| **Notification** | User alerts | notification_id, type, actor_id, target_id, message | mark_as_read(), generate_message() |
| **FacebookSystem** | System coordinator | users, posts, feed_strategy, observers | create_post(), generate_feed(), send_friend_request() |

## Design Patterns Comparison

| Pattern | Implementation | Purpose | Trade-offs |
|---------|---------------|---------|------------|
| **Singleton** | FacebookSystem | Single system instance, centralized state | ✓ Global access ✗ Testing complexity |
| **Strategy** | FeedRankingStrategy | Swap feed algorithms dynamically | ✓ Extensible ✗ More classes |
| **Observer** | NotificationObserver | Decouple actions from notifications | ✓ Loose coupling ✗ Delivery guarantees |
| **State** | FriendRequestState | Manage request lifecycle | ✓ Clear transitions ✗ State explosion |
| **Composite** | Comment (nested replies) | Uniform interface for tree structure | ✓ Unlimited depth ✗ Query complexity |

## Feed Ranking Strategies

| Strategy | Algorithm | Time Complexity | Use Case |
|----------|-----------|-----------------|----------|
| **ChronologicalFeed** | Sort by timestamp DESC | O(n log n) | Simple feed, small user base |
| **EngagementBasedFeed** | Sort by (likes + comments*2) DESC | O(n log n) | Viral content promotion |
| **FriendAffinityFeed** | Score = engagement * friend_weight * recency | O(n log n) | Personalized feed, close friends priority |

**Friend Affinity Weights**:
- Best friends (10+ interactions/week): 3.0
- Regular friends (3-10 interactions): 2.0
- Distant friends (<3 interactions): 1.0

**Recency Factors**:
- Last 24 hours: 1.0
- 1-7 days: 0.8
- 7-30 days: 0.5
- Older: 0.3

## Privacy Levels

| Level | Visibility | Use Case |
|-------|-----------|----------|
| **PUBLIC** | Anyone can view | Marketing, public announcements |
| **FRIENDS** | Only friends can view | Personal updates, photos |
| **ONLY_ME** | Only author can view | Private notes, drafts |

**Privacy Check Algorithm**:
```
if privacy == PUBLIC: return True
if privacy == ONLY_ME: return viewer_id == author_id
if privacy == FRIENDS: return viewer_id == author_id OR author_id in viewer.friends
```

## Friend Request State Machine

```
         send_request
              │
              ▼
         ┌─────────┐
         │ PENDING │
         └─────────┘
              │
     ┌────────┼────────┐
     │        │        │
  accept   reject   block
     │        │        │
     ▼        ▼        ▼
┌─────────┐ ┌────────┐ ┌────────┐
│ACCEPTED │ │REJECTED│ │BLOCKED │
└─────────┘ └────────┘ └────────┘
```

**Validation Rules**:
- Cannot send to self
- Cannot send if already friends
- Cannot send duplicate PENDING
- Cannot send if blocked

## Key Algorithms

### 1. Mutual Friends
```
mutual_friends(user1, user2):
  return user1.friends ∩ user2.friends

Time: O(min(|friends1|, |friends2|))
```

### 2. Engagement Score
```
engagement_score = likes_count + (comments_count * 2)

Rationale: Comments indicate deeper engagement
```

### 3. Feed Generation
```
generate_feed(user):
  1. Collect posts from all friends
  2. Filter by privacy (can_view check)
  3. Apply ranking strategy
  4. Return top N posts

Time: O(F*P + N log N)
  F = friends count
  P = avg posts per friend
  N = total posts
```

### 4. Friend Suggestions (People You May Know)
```
suggest_friends(user):
  suggestions = []
  for friend in user.friends:
    for friend_of_friend in friend.friends:
      if FOF not in user.friends AND FOF != user:
        mutual_count = |user.friends ∩ FOF.friends|
        suggestions.append((FOF, mutual_count))
  return top 10 by mutual_count DESC

Time: O(F * F^2) worst case
Optimization: Limit depth, cache results
```

## Thread Safety

### Critical Sections
1. **Friend Request Acceptance**: Lock both users' friends sets
2. **Post Like/Unlike**: Lock per post (fine-grained)
3. **Comment Creation**: Lock per post
4. **Feed Generation**: Read-only (no lock)

### Locking Strategy
```python
# Coarse-grained (system-level)
system_lock = threading.Lock()

# Fine-grained (per resource)
post_locks: Dict[str, threading.Lock] = {}

# Usage
with post_locks[post_id]:
    post.add_like(user_id)
```

**Benefits of Fine-Grained Locking**:
- Reduced contention
- Higher concurrency
- Better performance

## Performance Optimizations

| Technique | Application | Impact |
|-----------|------------|--------|
| **Indexing** | user_id, post_id, timestamp, (author_id, timestamp) composite | Fast queries |
| **Caching** | User profiles (1hr), Feeds (5-10min), Mutual friends (1 day) | Reduce DB load |
| **Pagination** | Feed: 50 posts/page | Lower latency |
| **Pre-filtering** | Posts from last 30 days only | Smaller dataset |
| **Fan-out on write** | Pre-compute feeds for active users | Read speed |
| **Message queue** | Async notification delivery (Kafka/RabbitMQ) | Non-blocking |

## Notification Types

| Type | Trigger | Message Template |
|------|---------|-----------------|
| FRIEND_REQUEST | User sends request | "X sent you a friend request" |
| FRIEND_ACCEPTED | Request accepted | "X accepted your friend request" |
| LIKE | User likes post | "X liked your post" |
| COMMENT | User comments on post | "X commented on your post" |
| MENTION | User mentioned in content | "X mentioned you" |
| TAG | User tagged in post | "X tagged you in a post" |

**Observer Pattern Flow**:
```
Action (like/comment) → Create Notification → Notify Observers → Deliver (Email/Push/SMS)
```

## Edge Cases & Validation

### Friend Requests
- ✗ Send to self
- ✗ Duplicate PENDING request
- ✗ Send if already friends
- ✗ Send if blocked
- ✓ Bidirectional friendship on accept

### Posts
- ✓ Tagged users can view FRIENDS posts even if not friends
- ✓ Author always can view own posts
- ✓ Privacy can change after creation (re-validate feed)

### Comments
- ✓ Limit nesting depth (10 levels) to prevent performance issues
- ✗ Comment on deleted post
- ✗ Reply to deleted comment

### Notifications
- ✗ Don't notify user of own actions
- ✓ Batch notifications ("10 people liked your post")
- ✓ Mark as read when viewed

## SOLID Principles Mapping

| Principle | Implementation |
|-----------|---------------|
| **SRP** | User (profile only), Post (content only), FacebookSystem (coordination only) |
| **OCP** | FeedRankingStrategy extensible via new strategy classes |
| **LSP** | All FeedRankingStrategy implementations substitutable |
| **ISP** | FeedRankingStrategy requires only rank_feed(), NotificationObserver only on_notify() |
| **DIP** | FacebookSystem depends on FeedRankingStrategy abstraction, not concrete classes |

## Interview Success Checklist

- [ ] Explained core entities and relationships
- [ ] Drew ASCII UML class diagram
- [ ] Implemented Singleton (FacebookSystem)
- [ ] Implemented Strategy (3 feed ranking algorithms)
- [ ] Implemented Observer (notification system)
- [ ] Implemented State (friend request lifecycle)
- [ ] Implemented Composite (nested comments)
- [ ] Explained bidirectional friendship using Set
- [ ] Explained privacy levels and can_view() logic
- [ ] Calculated engagement score (likes + comments*2)
- [ ] Explained mutual friends algorithm (Set intersection)
- [ ] Generated feed with different strategies
- [ ] Discussed thread safety (fine-grained locks)
- [ ] Optimized with caching, pagination, pre-filtering
- [ ] Handled edge cases (self-friend, privacy, deleted content)
- [ ] Mapped SOLID principles to design

## Common Interview Questions

**Q: Why Set for friends instead of List?**  
**A**: O(1) lookup for is_friend(), automatic uniqueness, efficient intersection for mutual friends.

**Q: Why weight comments 2x more than likes?**  
**A**: Comments indicate deeper engagement and take more effort than likes.

**Q: How to scale feed generation for millions of users?**  
**A**: Pre-compute feeds (fan-out on write), cache feeds (5-10min TTL), pagination, pre-filter by time, index by (author_id, timestamp).

**Q: What if user has 10,000 friends?**  
**A**: Paginate feed, limit posts per friend (top 10 recent), use fan-out on write for active users only, fall back to pull-based for inactive.

**Q: How to prevent notification spam?**  
**A**: Batch similar notifications, rate limit (100/min), aggregate ("10 people liked your post"), use async delivery.

## Anti-Patterns to Avoid

1. ❌ God Object: Don't put all logic in FacebookSystem
2. ❌ Hard-coded ranking: Use Strategy pattern for flexibility
3. ❌ No privacy checks: Always validate can_view()
4. ❌ Unbounded queries: Always paginate and time-filter
5. ❌ Synchronous notifications: Use async delivery
6. ❌ Global locks: Use fine-grained locking per resource
7. ❌ Missing validation: Check for self-friend, duplicates, blocked users


## Compact Code

```python
"""
Facebook Social Network - Interview Implementation
Complete working system with 5 demo scenarios
Patterns: Singleton, Strategy, Observer, State, Composite
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import threading
import uuid

# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class Privacy(Enum):
    """Post privacy levels"""
    PUBLIC = "public"
    FRIENDS = "friends"
    ONLY_ME = "only_me"

class FriendRequestState(Enum):
    """Friend request lifecycle states"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class NotificationType(Enum):
    """Types of notifications"""
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    LIKE = "like"
    COMMENT = "comment"
    MENTION = "mention"
    TAG = "tag"

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class User:
    """Represents a Facebook user with profile and social connections"""
    
    def __init__(self, user_id: str, name: str, email: str, bio: str = ""):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.bio = bio
        self.profile_picture = ""
        self.friends: Set[str] = set()  # Set of friend user IDs
        self.posts: List[str] = []  # List of post IDs
        self.created_at = datetime.now()
    
    def add_friend(self, user_id: str):
        """Add user to friends set"""
        if user_id != self.user_id:  # Cannot friend self
            self.friends.add(user_id)
    
    def remove_friend(self, user_id: str):
        """Remove user from friends set"""
        self.friends.discard(user_id)
    
    def is_friend(self, user_id: str) -> bool:
        """Check if user is a friend"""
        return user_id in self.friends
    
    def get_mutual_friends(self, other: 'User') -> Set[str]:
        """Find mutual friends with another user"""
        return self.friends.intersection(other.friends)
    
    def __repr__(self):
        return f"User({self.user_id}, {self.name}, {len(self.friends)} friends)"

class Post:
    """Represents user-generated content with engagement tracking"""
    
    def __init__(self, post_id: str, author_id: str, content: str, 
                 privacy: Privacy, image_urls: List[str] = None, 
                 tagged_users: Set[str] = None):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.privacy = privacy
        self.image_urls = image_urls or []
        self.tagged_users = tagged_users or set()
        self.likes: Set[str] = set()  # User IDs who liked
        self.comments: List[str] = []  # Comment IDs
        self.timestamp = datetime.now()
        self.edited_at: Optional[datetime] = None
    
    def add_like(self, user_id: str):
        """User likes post (Set ensures uniqueness)"""
        self.likes.add(user_id)
    
    def remove_like(self, user_id: str):
        """User unlikes post"""
        self.likes.discard(user_id)
    
    def add_comment(self, comment_id: str):
        """Attach comment to post"""
        self.comments.append(comment_id)
    
    def get_engagement_score(self) -> float:
        """Calculate engagement: likes + (comments * 2)"""
        return len(self.likes) + (len(self.comments) * 2.0)
    
    def can_view(self, viewer_id: str, viewer_friends: Set[str]) -> bool:
        """Check if viewer can see this post based on privacy"""
        if self.privacy == Privacy.PUBLIC:
            return True
        elif self.privacy == Privacy.ONLY_ME:
            return viewer_id == self.author_id
        elif self.privacy == Privacy.FRIENDS:
            # Author or friends can view
            return viewer_id == self.author_id or self.author_id in viewer_friends
        return False
    
    def __repr__(self):
        return f"Post({self.post_id}, by {self.author_id}, {len(self.likes)} likes, {len(self.comments)} comments)"

class Comment:
    """User comments on posts with support for nested replies (Composite pattern)"""
    
    def __init__(self, comment_id: str, author_id: str, post_id: str, 
                 content: str, parent_comment_id: Optional[str] = None):
        self.comment_id = comment_id
        self.author_id = author_id
        self.post_id = post_id
        self.content = content
        self.parent_comment_id = parent_comment_id
        self.replies: List[str] = []  # Child comment IDs
        self.likes: Set[str] = set()
        self.timestamp = datetime.now()
    
    def add_reply(self, comment_id: str):
        """Add nested reply"""
        self.replies.append(comment_id)
    
    def add_like(self, user_id: str):
        """Like comment"""
        self.likes.add(user_id)
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment"""
        return self.parent_comment_id is not None
    
    def __repr__(self):
        reply_str = f", reply to {self.parent_comment_id}" if self.is_reply() else ""
        return f"Comment({self.comment_id}, by {self.author_id}{reply_str})"

class FriendRequest:
    """Manages friend connection lifecycle with state machine"""
    
    def __init__(self, request_id: str, from_user_id: str, to_user_id: str):
        self.request_id = request_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.state = FriendRequestState.PENDING
        self.timestamp = datetime.now()
        self.responded_at: Optional[datetime] = None
    
    def accept(self):
        """Transition to ACCEPTED"""
        if self.state == FriendRequestState.PENDING:
            self.state = FriendRequestState.ACCEPTED
            self.responded_at = datetime.now()
            return True
        return False
    
    def reject(self):
        """Transition to REJECTED"""
        if self.state == FriendRequestState.PENDING:
            self.state = FriendRequestState.REJECTED
            self.responded_at = datetime.now()
            return True
        return False
    
    def block(self):
        """Transition to BLOCKED"""
        self.state = FriendRequestState.BLOCKED
        self.responded_at = datetime.now()
    
    def is_pending(self) -> bool:
        """Check if awaiting response"""
        return self.state == FriendRequestState.PENDING
    
    def __repr__(self):
        return f"FriendRequest({self.from_user_id} -> {self.to_user_id}, {self.state.value})"

class Notification:
    """Inform users of social interactions"""
    
    def __init__(self, notification_id: str, user_id: str, 
                 notif_type: NotificationType, actor_id: str, target_id: str):
        self.notification_id = notification_id
        self.user_id = user_id  # Recipient
        self.type = notif_type
        self.actor_id = actor_id  # Who triggered action
        self.target_id = target_id  # Post/comment/request ID
        self.message = self._generate_message()
        self.is_read = False
        self.timestamp = datetime.now()
    
    def _generate_message(self) -> str:
        """Generate user-friendly message"""
        messages = {
            NotificationType.FRIEND_REQUEST: f"User {self.actor_id} sent you a friend request",
            NotificationType.FRIEND_ACCEPTED: f"User {self.actor_id} accepted your friend request",
            NotificationType.LIKE: f"User {self.actor_id} liked your post",
            NotificationType.COMMENT: f"User {self.actor_id} commented on your post",
            NotificationType.MENTION: f"User {self.actor_id} mentioned you",
            NotificationType.TAG: f"User {self.actor_id} tagged you in a post"
        }
        return messages.get(self.type, "New notification")
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
    
    def __repr__(self):
        status = "read" if self.is_read else "unread"
        return f"Notification({self.type.value}, {status})"

# ============================================================================
# SECTION 3: STRATEGY PATTERN - FEED RANKING
# ============================================================================

class FeedRankingStrategy(ABC):
    """Abstract strategy for ranking posts in news feed"""
    
    @abstractmethod
    def rank_feed(self, user: User, posts: List[Post]) -> List[Post]:
        """Rank posts for user's feed"""
        pass

class ChronologicalFeed(FeedRankingStrategy):
    """Sort posts by timestamp (newest first)"""
    
    def rank_feed(self, user: User, posts: List[Post]) -> List[Post]:
        """O(n log n) sorting by timestamp"""
        return sorted(posts, key=lambda p: p.timestamp, reverse=True)

class EngagementBasedFeed(FeedRankingStrategy):
    """Rank posts by engagement score (likes + comments)"""
    
    def rank_feed(self, user: User, posts: List[Post]) -> List[Post]:
        """O(n log n) sorting by engagement, then timestamp"""
        return sorted(posts, 
                     key=lambda p: (p.get_engagement_score(), p.timestamp),
                     reverse=True)

class FriendAffinityFeed(FeedRankingStrategy):
    """Weight posts from close friends higher"""
    
    def __init__(self, interaction_counts: Dict[str, int] = None):
        # Mock interaction tracking: user_id -> interaction count
        self.interaction_counts = interaction_counts or {}
    
    def _get_friend_weight(self, user_id: str) -> float:
        """Calculate friend weight based on interaction history"""
        count = self.interaction_counts.get(user_id, 0)
        if count >= 10:
            return 3.0  # Best friends
        elif count >= 3:
            return 2.0  # Regular friends
        else:
            return 1.0  # Distant friends
    
    def _get_recency_factor(self, post: Post) -> float:
        """Calculate recency factor"""
        age = datetime.now() - post.timestamp
        if age < timedelta(days=1):
            return 1.0
        elif age < timedelta(days=7):
            return 0.8
        elif age < timedelta(days=30):
            return 0.5
        else:
            return 0.3
    
    def rank_feed(self, user: User, posts: List[Post]) -> List[Post]:
        """Rank by affinity score: engagement * friend_weight * recency"""
        def affinity_score(post: Post) -> float:
            engagement = post.get_engagement_score()
            friend_weight = self._get_friend_weight(post.author_id)
            recency = self._get_recency_factor(post)
            return engagement * friend_weight * recency
        
        return sorted(posts, key=affinity_score, reverse=True)

# ============================================================================
# SECTION 4: OBSERVER PATTERN - NOTIFICATIONS
# ============================================================================

class NotificationObserver(ABC):
    """Abstract observer for notification delivery"""
    
    @abstractmethod
    def on_notify(self, notification: Notification):
        """Handle notification delivery"""
        pass

class ConsoleNotifier(NotificationObserver):
    """Print notifications to console (for demo)"""
    
    def on_notify(self, notification: Notification):
        print(f"  [NOTIFICATION] {notification.message}")

class EmailNotifier(NotificationObserver):
    """Send email notifications (mock)"""
    
    def on_notify(self, notification: Notification):
        # In production: send actual email
        pass

class PushNotifier(NotificationObserver):
    """Send push notifications (mock)"""
    
    def on_notify(self, notification: Notification):
        # In production: send push via FCM/APNs
        pass

# ============================================================================
# SECTION 5: SINGLETON PATTERN - FACEBOOK SYSTEM
# ============================================================================

class FacebookSystem:
    """Centralized system coordinator (Singleton pattern)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.users: Dict[str, User] = {}
            self.posts: Dict[str, Post] = {}
            self.comments: Dict[str, Comment] = {}
            self.friend_requests: List[FriendRequest] = []
            self.notifications: List[Notification] = []
            self.feed_strategy: FeedRankingStrategy = ChronologicalFeed()
            self.notification_observers: List[NotificationObserver] = []
            self.system_lock = threading.Lock()
            self.post_locks: Dict[str, threading.Lock] = {}
            self.initialized = True
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        return cls()
    
    # User operations
    def create_user(self, name: str, email: str, bio: str = "") -> User:
        """Create new user"""
        user_id = f"U{len(self.users) + 1}"
        user = User(user_id, name, email, bio)
        self.users[user_id] = user
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    # Friend request operations
    def send_friend_request(self, from_user_id: str, to_user_id: str) -> Optional[FriendRequest]:
        """Send friend request with validation"""
        from_user = self.get_user(from_user_id)
        to_user = self.get_user(to_user_id)
        
        if not from_user or not to_user:
            return None
        
        # Validation: cannot send to self, already friends, or duplicate pending
        if from_user_id == to_user_id:
            return None
        if from_user.is_friend(to_user_id):
            return None
        
        # Check for existing pending request
        for req in self.friend_requests:
            if req.from_user_id == from_user_id and req.to_user_id == to_user_id and req.is_pending():
                return None
        
        request_id = f"FR{len(self.friend_requests) + 1}"
        request = FriendRequest(request_id, from_user_id, to_user_id)
        self.friend_requests.append(request)
        
        # Notify recipient
        notif = Notification(f"N{len(self.notifications) + 1}", to_user_id,
                           NotificationType.FRIEND_REQUEST, from_user_id, request_id)
        self._notify(notif)
        
        return request
    
    def accept_friend_request(self, request_id: str) -> bool:
        """Accept friend request and establish bidirectional friendship"""
        request = next((r for r in self.friend_requests if r.request_id == request_id), None)
        if not request or not request.is_pending():
            return False
        
        with self.system_lock:
            if request.accept():
                # Bidirectional friendship
                from_user = self.get_user(request.from_user_id)
                to_user = self.get_user(request.to_user_id)
                from_user.add_friend(to_user.user_id)
                to_user.add_friend(from_user.user_id)
                
                # Notify sender
                notif = Notification(f"N{len(self.notifications) + 1}", request.from_user_id,
                                   NotificationType.FRIEND_ACCEPTED, request.to_user_id, request_id)
                self._notify(notif)
                return True
        return False
    
    def reject_friend_request(self, request_id: str) -> bool:
        """Reject friend request"""
        request = next((r for r in self.friend_requests if r.request_id == request_id), None)
        if request:
            return request.reject()
        return False
    
    # Post operations
    def create_post(self, user_id: str, content: str, privacy: Privacy,
                   image_urls: List[str] = None, tagged_users: Set[str] = None) -> Optional[Post]:
        """Create new post"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        post_id = f"P{len(self.posts) + 1}"
        post = Post(post_id, user_id, content, privacy, image_urls, tagged_users)
        self.posts[post_id] = post
        user.posts.append(post_id)
        
        # Notify tagged users
        if tagged_users:
            for tagged_id in tagged_users:
                if tagged_id != user_id:
                    notif = Notification(f"N{len(self.notifications) + 1}", tagged_id,
                                       NotificationType.TAG, user_id, post_id)
                    self._notify(notif)
        
        return post
    
    def like_post(self, user_id: str, post_id: str) -> bool:
        """User likes a post"""
        post = self.posts.get(post_id)
        if not post:
            return False
        
        # Thread-safe like operation
        lock = self._get_post_lock(post_id)
        with lock:
            post.add_like(user_id)
            
            # Notify post author (don't notify self)
            if user_id != post.author_id:
                notif = Notification(f"N{len(self.notifications) + 1}", post.author_id,
                                   NotificationType.LIKE, user_id, post_id)
                self._notify(notif)
        return True
    
    def unlike_post(self, user_id: str, post_id: str) -> bool:
        """User unlikes a post"""
        post = self.posts.get(post_id)
        if not post:
            return False
        
        lock = self._get_post_lock(post_id)
        with lock:
            post.remove_like(user_id)
        return True
    
    # Comment operations
    def create_comment(self, user_id: str, post_id: str, content: str,
                      parent_comment_id: Optional[str] = None) -> Optional[Comment]:
        """Create comment or reply"""
        post = self.posts.get(post_id)
        if not post:
            return None
        
        comment_id = f"C{len(self.comments) + 1}"
        comment = Comment(comment_id, user_id, post_id, content, parent_comment_id)
        self.comments[comment_id] = comment
        
        # Add to post or parent comment
        if parent_comment_id:
            parent = self.comments.get(parent_comment_id)
            if parent:
                parent.add_reply(comment_id)
        else:
            post.add_comment(comment_id)
        
        # Notify post author or parent comment author (don't notify self)
        target_user_id = post.author_id
        if parent_comment_id:
            parent = self.comments.get(parent_comment_id)
            if parent:
                target_user_id = parent.author_id
        
        if user_id != target_user_id:
            notif = Notification(f"N{len(self.notifications) + 1}", target_user_id,
                               NotificationType.COMMENT, user_id, comment_id)
            self._notify(notif)
        
        return comment
    
    # Feed generation
    def generate_feed(self, user_id: str, limit: int = 50) -> List[Post]:
        """Generate personalized news feed for user"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        # Collect posts from friends
        visible_posts = []
        for friend_id in user.friends:
            friend = self.get_user(friend_id)
            if friend:
                for post_id in friend.posts:
                    post = self.posts.get(post_id)
                    if post and post.can_view(user_id, user.friends):
                        visible_posts.append(post)
        
        # Apply ranking strategy
        ranked_posts = self.feed_strategy.rank_feed(user, visible_posts)
        return ranked_posts[:limit]
    
    def set_feed_strategy(self, strategy: FeedRankingStrategy):
        """Set feed ranking strategy (Strategy pattern)"""
        self.feed_strategy = strategy
    
    # Notification system
    def add_notification_observer(self, observer: NotificationObserver):
        """Register notification observer"""
        self.notification_observers.append(observer)
    
    def _notify(self, notification: Notification):
        """Notify all observers"""
        self.notifications.append(notification)
        for observer in self.notification_observers:
            observer.on_notify(notification)
    
    # Helper methods
    def _get_post_lock(self, post_id: str) -> threading.Lock:
        """Get or create lock for post (fine-grained locking)"""
        if post_id not in self.post_locks:
            self.post_locks[post_id] = threading.Lock()
        return self.post_locks[post_id]
    
    def get_mutual_friends(self, user_id1: str, user_id2: str) -> Set[str]:
        """Calculate mutual friends between two users"""
        user1 = self.get_user(user_id1)
        user2 = self.get_user(user_id2)
        if user1 and user2:
            return user1.get_mutual_friends(user2)
        return set()

# ============================================================================
# SECTION 6: DEMO SCENARIOS
# ============================================================================

def demo1_basic_user_and_friends():
    """Demo 1: Create users, send friend requests, establish friendships"""
    print("\n" + "="*70)
    print("DEMO 1: Basic User & Friend Operations")
    print("="*70)
    
    system = FacebookSystem.get_instance()
    system.add_notification_observer(ConsoleNotifier())
    
    # Create users
    alice = system.create_user("Alice", "alice@example.com", "Loves photography")
    bob = system.create_user("Bob", "bob@example.com", "Software engineer")
    charlie = system.create_user("Charlie", "charlie@example.com", "Travel blogger")
    
    print(f"Created users: {alice}, {bob}, {charlie}")
    
    # Friend requests
    print(f"\n{alice.name} sends friend request to {bob.name}")
    req1 = system.send_friend_request(alice.user_id, bob.user_id)
    
    print(f"\n{bob.name} accepts request")
    system.accept_friend_request(req1.request_id)
    print(f"Friendship established: Alice friends = {alice.friends}, Bob friends = {bob.friends}")
    
    # More connections
    print(f"\n{alice.name} sends friend request to {charlie.name}")
    req2 = system.send_friend_request(alice.user_id, charlie.user_id)
    system.accept_friend_request(req2.request_id)
    
    print(f"\n{bob.name} sends friend request to {charlie.name}")
    req3 = system.send_friend_request(bob.user_id, charlie.user_id)
    system.accept_friend_request(req3.request_id)
    
    # Mutual friends
    mutual = system.get_mutual_friends(alice.user_id, bob.user_id)
    print(f"\nMutual friends between {alice.name} and {bob.name}: {mutual}")
    print("Expected: Charlie (U3)")

def demo2_posts_with_privacy():
    """Demo 2: Create posts with different privacy levels, verify visibility"""
    print("\n" + "="*70)
    print("DEMO 2: Post Creation with Privacy Levels")
    print("="*70)
    
    system = FacebookSystem.get_instance()
    alice = system.get_user("U1")
    bob = system.get_user("U2")
    charlie = system.get_user("U3")
    
    # Create posts with different privacy
    p1 = system.create_post(alice.user_id, "Public vacation photos!", Privacy.PUBLIC)
    p2 = system.create_post(bob.user_id, "Friends only: New job announcement", Privacy.FRIENDS)
    p3 = system.create_post(charlie.user_id, "Private note to self", Privacy.ONLY_ME)
    
    print(f"Created posts:")
    print(f"  {p1} - {p1.privacy.value}")
    print(f"  {p2} - {p2.privacy.value}")
    print(f"  {p3} - {p3.privacy.value}")
    
    # Test visibility
    print(f"\nVisibility tests:")
    print(f"  Alice can view Bob's FRIENDS post: {p2.can_view(alice.user_id, alice.friends)}")
    print(f"  Alice can view Charlie's ONLY_ME post: {p3.can_view(alice.user_id, alice.friends)}")
    print(f"  Charlie can view own ONLY_ME post: {p3.can_view(charlie.user_id, charlie.friends)}")
    print(f"  Bob can view Alice's PUBLIC post: {p1.can_view(bob.user_id, bob.friends)}")

def demo3_engagement_likes_comments():
    """Demo 3: Users like and comment on posts, verify engagement"""
    print("\n" + "="*70)
    print("DEMO 3: Engagement (Likes, Comments)")
    print("="*70)
    
    system = FacebookSystem.get_instance()
    alice = system.get_user("U1")
    bob = system.get_user("U2")
    charlie = system.get_user("U3")
    
    # Get Alice's post
    p1 = system.posts.get("P1")
    print(f"Post: {p1}")
    
    # Likes
    print(f"\n{bob.name} and {charlie.name} like the post")
    system.like_post(bob.user_id, p1.post_id)
    system.like_post(charlie.user_id, p1.post_id)
    print(f"Likes: {p1.likes} (count: {len(p1.likes)})")
    
    # Comments
    print(f"\n{bob.name} comments on post")
    c1 = system.create_comment(bob.user_id, p1.post_id, "Great photos!")
    
    print(f"{charlie.name} comments on post")
    c2 = system.create_comment(charlie.user_id, p1.post_id, "Awesome trip!")
    
    print(f"\n{alice.name} replies to {bob.name}'s comment")
    c3 = system.create_comment(alice.user_id, p1.post_id, "Thanks Bob!", c1.comment_id)
    
    print(f"\nPost engagement:")
    print(f"  Comments: {p1.comments} (count: {len(p1.comments)})")
    print(f"  {c1} -> Replies: {c1.replies}")
    print(f"  Engagement score: {p1.get_engagement_score()} (2 likes + 3 comments * 2 = 8)")

def demo4_feed_ranking_strategies():
    """Demo 4: Generate feed using different ranking strategies"""
    print("\n" + "="*70)
    print("DEMO 4: Feed Generation with Different Strategies")
    print("="*70)
    
    system = FacebookSystem.get_instance()
    alice = system.get_user("U1")
    bob = system.get_user("U2")
    charlie = system.get_user("U3")
    
    # Create posts with different engagement and times
    import time
    p4 = system.create_post(bob.user_id, "Recent post with little engagement", Privacy.PUBLIC)
    time.sleep(0.1)
    
    p5 = system.create_post(charlie.user_id, "Viral post!", Privacy.PUBLIC)
    # Simulate high engagement
    for i in range(10):
        system.like_post(f"U{i+10}", p5.post_id)  # Mock users
    system.create_comment(alice.user_id, p5.post_id, "Amazing!")
    system.create_comment(bob.user_id, p5.post_id, "Love this!")
    
    print(f"\nPosts created:")
    print(f"  P1 (Alice): engagement={system.posts['P1'].get_engagement_score()}")
    print(f"  P2 (Bob): engagement={system.posts['P2'].get_engagement_score()}")
    print(f"  P4 (Bob): engagement={p4.get_engagement_score()}")
    print(f"  P5 (Charlie): engagement={p5.get_engagement_score()}")
    
    # Test 1: Chronological Feed
    print(f"\nTest 1: ChronologicalFeed (newest first)")
    system.set_feed_strategy(ChronologicalFeed())
    feed1 = system.generate_feed(alice.user_id, limit=5)
    print(f"  Alice's feed: {[p.post_id for p in feed1]}")
    
    # Test 2: Engagement-Based Feed
    print(f"\nTest 2: EngagementBasedFeed (highest engagement first)")
    system.set_feed_strategy(EngagementBasedFeed())
    feed2 = system.generate_feed(alice.user_id, limit=5)
    print(f"  Alice's feed: {[f'{p.post_id}(score={p.get_engagement_score()})' for p in feed2]}")
    
    # Test 3: Friend Affinity Feed
    print(f"\nTest 3: FriendAffinityFeed (weighted by friend closeness)")
    # Mock: Alice interacts more with Charlie (15 times) than Bob (5 times)
    interactions = {charlie.user_id: 15, bob.user_id: 5}
    system.set_feed_strategy(FriendAffinityFeed(interactions))
    feed3 = system.generate_feed(alice.user_id, limit=5)
    print(f"  Alice's feed: {[p.post_id for p in feed3]}")
    print(f"  (Charlie's posts ranked higher due to affinity)")

def demo5_notifications_observer():
    """Demo 5: Trigger notifications on user actions (Observer pattern)"""
    print("\n" + "="*70)
    print("DEMO 5: Notifications & Observer Pattern")
    print("="*70)
    
    system = FacebookSystem.get_instance()
    
    # Create new users for clean notification demo
    dave = system.create_user("Dave", "dave@example.com")
    eve = system.create_user("Eve", "eve@example.com")
    
    print(f"Created users: {dave}, {eve}")
    print(f"\nNotifications triggered:")
    
    # 1. Friend request notification
    print(f"\n1. {dave.name} sends friend request to {eve.name}")
    req = system.send_friend_request(dave.user_id, eve.user_id)
    
    # 2. Friend accepted notification
    print(f"\n2. {eve.name} accepts friend request")
    system.accept_friend_request(req.request_id)
    
    # 3. Post and like notification
    print(f"\n3. {eve.name} creates post, {dave.name} likes it")
    post = system.create_post(eve.user_id, "New post from Eve", Privacy.PUBLIC)
    system.like_post(dave.user_id, post.post_id)
    
    # 4. Comment notification
    print(f"\n4. {dave.name} comments on post")
    system.create_comment(dave.user_id, post.post_id, "Nice post!")
    
    # 5. Tag notification
    print(f"\n5. {eve.name} creates post tagging {dave.name}")
    system.create_post(eve.user_id, "Tagged post", Privacy.PUBLIC, tagged_users={dave.user_id})
    
    print(f"\nTotal notifications created: {len(system.notifications)}")
    print(f"Notification types: {[n.type.value for n in system.notifications[-5:]]}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("FACEBOOK SOCIAL NETWORK - INTERVIEW IMPLEMENTATION")
    print("Demonstrating: Singleton, Strategy, Observer, State, Composite")
    print("="*70)
    
    # Run all demos
    demo1_basic_user_and_friends()
    demo2_posts_with_privacy()
    demo3_engagement_likes_comments()
    demo4_feed_ranking_strategies()
    demo5_notifications_observer()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Singleton: FacebookSystem centralized coordinator")
    print("  ✓ Strategy: 3 feed ranking algorithms (Chronological, Engagement, Affinity)")
    print("  ✓ Observer: Notification system with multiple observers")
    print("  ✓ State: Friend request lifecycle (PENDING → ACCEPTED/REJECTED)")
    print("  ✓ Composite: Nested comments with unlimited depth")
    print("  ✓ Bidirectional friendships with Set")
    print("  ✓ Privacy levels: PUBLIC, FRIENDS, ONLY_ME")
    print("  ✓ Engagement scoring: likes + (comments * 2)")
    print("  ✓ Thread-safe post operations with fine-grained locks")
    print("="*70)

```

## UML Class Diagram (text)
````
(Classes, relationships, strategies/observers, enums)
````


## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
