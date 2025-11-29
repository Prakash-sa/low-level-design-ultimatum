# Facebook Social Network - 75 Minute Interview Implementation Guide

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

