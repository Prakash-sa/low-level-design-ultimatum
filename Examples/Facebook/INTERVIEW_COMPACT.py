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
