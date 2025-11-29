# Facebook Social Network - Quick Reference

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
