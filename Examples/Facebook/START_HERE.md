# Facebook Social Network - START HERE (5-Minute Guide)

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

## Design Patterns (Why Each?)

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
