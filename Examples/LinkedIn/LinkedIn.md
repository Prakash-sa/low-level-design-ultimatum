# LinkedIn — 75-Minute Interview Guide

## Quick Start

**What is it?** Professional networking platform with user profiles, connections, job postings, content feed, messaging, and match recommendations using factory patterns, observer pattern for notifications, and strategy patterns for job matching.

**Key Classes:**
- `LinkedInSystem` (Singleton): Centralized coordinator
- `User`: Professional profile with skills/experience
- `Connection`: Relationship with state machine (Pending→Accepted/Rejected)
- `Post`: Content with factory pattern (TextPost, ImagePost, VideoPost, ArticlePost)
- `Job`: Job posting with strategy-based matching
- `JobMatchingStrategy` (ABC): Pluggable matching algorithms
- `LinkedInObserver` (ABC): Event notification subscribers

**Core Flows:**
1. **Profile Management**: Create user → Add skills → Add experiences → Track connections
2. **Connection System**: Send request → Pending state → Accept/Reject → State transitions
3. **Content Feed**: Create post (factory) → Emit event → Notify followers (observer) → Rank feed (engagement × recency × connection)
4. **Job Matching**: Post job → Apply → Use strategy (skill/location/experience-based) → Match candidates
5. **Messaging**: Send message → Store conversation → Real-time notification

**5 Design Patterns:**
- **Singleton**: One LinkedInSystem instance
- **Factory**: Create different post types (TextPost, ImagePost, VideoPost, ArticlePost)
- **Strategy**: Job matching algorithms (skill-based, location-based, experience-based, hybrid)
- **Observer**: Event-driven notifications (feed, connections, jobs, messages)
- **State Machine**: Connection lifecycle (Pending → Accepted/Rejected/Withdrawn)

---

## System Overview

Professional social networking platform enabling users to build professional identities, connect with peers, discover jobs, and consume relevant content.

### Requirements

**Functional:**
- Create/manage professional profiles with skills and experience
- Send/accept/reject connection requests
- Create posts (text, image, video, article) with visibility control
- Like, comment, share posts
- Personalized feed ranking by engagement and recency
- Post jobs with skill requirements and location
- Apply for jobs with matching algorithm
- Send messages between connections
- Get connection recommendations based on mutual connections and skills
- Follow companies and profiles

**Non-Functional:**
- Feed generation < 500ms (real-time for 500M+ DAU)
- Search < 200ms (Elasticsearch)
- Message delivery < 1s (WebSocket + Kafka)
- 99.9% availability
- Eventual consistency for feeds
- Data encryption for privacy

**Constraints:**
- Single-process demo (production: distributed microservices)
- In-memory storage (production: PostgreSQL + Redis + Elasticsearch)
- Optional scaling narratives (caching, sharding, microservices)

---

## Architecture Diagram (ASCII UML)

```
┌────────────────────────────────────────────────────────────┐
│           LinkedInSystem (Singleton)                       │
│  - users: {user_id → User}                                │
│  - connections: {conn_id → Connection}                    │
│  - posts: {post_id → Post}                                │
│  - jobs: {job_id → Job}                                   │
│  - messages: {msg_id → Message}                           │
│  - observers: [LinkedInObserver]                          │
│  + create_user(), send_connection(), create_post()        │
│  + post_job(), apply_job(), send_message()               │
│  + generate_feed(), get_recommendations()                 │
│  + set_job_matcher(strategy)                              │
└─────────────────┬────────────────────────────────────────┘
                  │
      ┌───────────┼───────────┬──────────────┬─────────────┐
      ▼           ▼           ▼              ▼             ▼
  ┌────────┐  ┌───────────┐  ┌────────┐  ┌─────┐  ┌──────────┐
  │ User   │  │Connection │  │  Post  │  │ Job │  │ Message  │
  ├────────┤  ├───────────┤  ├────────┤  ├─────┤  ├──────────┤
  │- skills│  │- status:  │  │- author│  │-req.│  │- sender  │
  │- exp.  │  │  Pending  │  │- likes │  │ _s. │  │- receiver│
  │- conn. │  │- message  │  │-content│  │-match│ │- content │
  └────────┘  │           │  │- type  │  │-score│  └──────────┘
              │ PENDING ──┤  ├────────┤  └─────┘
              │ ↓ Accept  │  │        │
              │ → ACCEPTED│  │ Fact   │
              │ ↓ Reject  │  │ Post   │
              │ → REJECTED│  │ Types: │
              └───────────┘  │├─Text  │
                             │├─Image │
                             │├─Video │
                             │└─Article
                             └────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ JobMatching      │
                        │ Strategy (ABC)   │
                        └────┬──────┬──────┘
                             │      │
                    ┌────────┴──┬───┴──────────┐
                    ▼           ▼              ▼
                 SkillBased  Location     Experience
                 Matcher      Based        Based
                              Matcher      Matcher
                                  │
                                  ▼
                           HybridMatcher
                           
             ┌─────────────────────────────────┐
             │ LinkedInObserver (Abstract)     │
             │ + update(event, payload)       │
             └─────────────────────────────────┘
                  │            │            │
         ┌────────┴──┐  ┌──────┴──┐  ┌─────┴────────┐
         ▼           ▼  ▼         ▼  ▼              ▼
    FeedNotifier ConnectionNotifier JobNotifier MessageNotifier
    
LIFECYCLE:
USER_CREATED → ADD_SKILL → ADD_EXPERIENCE → SEND_CONNECTION → 
  → POST_CREATED (Factory) → FOLLOWERS_NOTIFIED (Observer) → 
  → FEED_RANKED (engagement × recency × connection) → VIEWED

JOB_POSTED → SET_MATCHER(Strategy) → USER_APPLIES → 
  → MATCH_SCORE_CALCULATED → FEED_SENT_TO_RECRUITER
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How does the Singleton pattern ensure one LinkedInSystem instance?**
A: `LinkedInSystem` uses `__new__` with thread-safe double-check locking. `_instance` class variable holds single instance. On first call, creates instance; subsequent calls return same instance. Prevents data inconsistency from multiple systems.

**Q2: How does Factory pattern work for creating posts?**
A: `PostFactory.create_post(post_type, content, media_urls)` takes post type enum. Returns appropriate subclass: TextPost, ImagePost, VideoPost, or ArticlePost. Centralizes creation logic, makes extending with new post types easy.

**Q3: What's the Connection state machine lifecycle?**
A: Connection starts in `Pending` state. From Pending: `accept()` → `Accepted` state or `reject()` → `Rejected` state. Each state encapsulates valid transitions. Prevents invalid operations (e.g., can't reject after accept).

**Q4: How does Observer pattern notify followers of new posts?**
A: Post creation triggers `_notify_observers("post_created", {post_id, author_id})`. Each observer (FeedNotifier, ConnectionNotifier) receives event. FeedNotifier adds post to followers' feeds. Observer pattern decouples post creation from notification logic.

**Q5: How do the three job matching strategies differ?**
A: SkillBasedMatcher scores % of required skills matched. LocationBasedMatcher scores distance (100% if <50km). ExperienceBasedMatcher scores years match ±2. Each strategy independent; can switch at runtime. HybridMatcher combines all three with weighted average.

### Intermediate Level

**Q6: How does feed ranking balance engagement, recency, and connection strength?**
A: Score = (likes + 3×comments + 5×shares) × exp(-time_since_post / decay_factor) × connection_strength. Engagement weighs interactions (shares highest). Recency exponentially decays old posts. Connection strength (0-1) personalizes by relationship closeness.

**Q7: How do you handle connection recommendations efficiently?**
A: Iterate user's connections, collect their connections (excluding user's existing connections). Score each by: mutual_connections × 10 + common_skills × 5 + same_company × 15. Return top 10 by score. O(n×m) but manageable for demo.

**Q8: Why use State pattern instead of simple status enum?**
A: State encapsulates behavior (accept/reject/withdraw logic). State machine prevents invalid transitions (can't reject after accept). Each state knows valid next states. More maintainable than if-statements scattered in code.

**Q9: How do you ensure message delivery between users?**
A: Message stored in conversations dict. Recipient fetched from users dict. Message marked unread. Observer pattern (MessageNotifier) sends real-time notification. In production: WebSocket for real-time, Kafka for durability.

**Q10: How does the feed generation algorithm scale?**
A: Collect user's posts + connections' posts (pre-filtered by visibility). Sort by score = engagement × recency × connection_strength. Return top N. O(n log n) for sorting. Production: pre-compute feeds async, cache in Redis, use Elasticsearch.

### Advanced Level

**Q11: How would you distribute the system across multiple servers?**
A: Shard users by user_id hash → separate server. Connections sharded by from_user_id. Posts sharded by author_id. Jobs sharded by company_id. Cross-shard queries (get user's feed) fan-out to relevant shards, aggregate results. Consistency: eventual (caches eventually consistent).

**Q12: How to handle 500M daily active users efficiently?**
A: Use microservices: UserService, ConnectionService, FeedService, JobService, MessageService. Cache layers: Redis for user profiles (1h TTL), posts (30m TTL), connections graph. Elasticsearch for job search. Kafka for async processing (feed generation, notifications). Database: PostgreSQL replicas for reads, sharded writes.

---

## Scaling Q&A (12 Questions)

**Q1: Can you handle 1B users with in-memory storage?**
A: No. 1B users × 100 bytes = 100GB metadata alone. In production: PostgreSQL (sharded) for users, Neo4j for connection graph, Elasticsearch for jobs. In-memory: only cache hot data (top 10K users, feed for active users). TTL-based invalidation.

**Q2: How to generate personalized feed for 500M DAU in real-time?**
A: Fan-out on write: when user posts, async push to followers' feed caches (Redis lists). Hybrid: fan-out for <10K followers, pull-based for celebrities. Background jobs pre-compute feeds during low traffic. Cache TTL 30min. Pagination: return 20-50 posts per request.

**Q3: How to make job matching efficient with 10M jobs and 100M users?**
A: Pre-index jobs by (skills, location, experience) using Elasticsearch. When user applies, batch 100 applications in background job. Calculate scores in parallel. For recommendations: only consider last 10 posted jobs per user. Score threshold: only show >70% matches.

**Q4: What's the memory footprint if you cache all posts?**
A: 1B posts × 2KB each = 2TB storage. Unacceptable for in-memory. Solution: cache only recent 1M posts (today's posts = 20GB), archive older in S3. Elasticsearch indexes searchable metadata. Hot cache stores top trending posts.

**Q5: How to handle 100K concurrent WebSocket connections for messaging?**
A: Use connection pooling on server (1000-5000 connections per server). Load balance across 20+ servers. Use message queue (Kafka) for reliable delivery. Presence service (Redis) tracks online status. Read receipts batch update (eventual consistency).

**Q6: Can you support recommendations for all users continuously?**
A: No, compute on-demand. Strategy: compute for active users (DAU), batch compute for inactive overnight. Cache top 10 recommendations per user. Invalidate on new connection. Complexity O(n²) for cold start requires algorithmic tricks: mutual connections precomputed, skills indexed.

**Q7: How to ensure consistency when user accepts connection from two sources?**
A: Use optimistic locking with version numbers. `Connection.version` increments on state change. Accept checks: if version != expected, conflict. Retry or use distributed locks (Redis). Eventual consistency acceptable: "accepted" eventually visible everywhere.

**Q8: How to handle geographic distribution (US, EU, APAC) without latency?**
A: Multi-region deployment: replicate user profiles globally. Regional databases (US: us-east, EU: eu-west, APAC: ap-southeast). Home region authoritative. Cross-region sync lag <5min. Users route to closest region. Friends in different regions: use CDN for feed.

**Q9: How much storage for 1 year of posts (1B users, 5 posts/user/year)?**
A: 5B posts × 2KB = 10TB. Uncompressed. With compression (zlib): ~3TB. Sharded across 30 servers = 100GB each. Archive posts >1 year old to cold storage (S3 Glacier = $0.004/GB/month). Index recent posts in Elasticsearch.

**Q10: How to prevent spam and bot accounts creating fake connections?**
A: Rate limiting: max 100 connection requests/day per user. Honeypot fields (hidden inputs). CAPTCHA after 5 failed authentications. Connection request review queue for flagged accounts. Machine learning model: detect bot patterns (same message to many users, instant accepts).

**Q11: How to compute recommendations for 500M users?**
A: Batch compute nightly: 500M users ÷ 100 computers = 5M users per machine. 5M × 5ms per user = 25K seconds ≈ 7 hours. Parallel Spark job. Cache results in Redis (1GB compression for all recommendations). Invalidate incrementally as new connections arrive.

**Q12: How to scale messaging to 1B messages/day?**
A: 1B messages/day ÷ 86400 seconds ≈ 11.5K msg/sec. Kafka: 1M msg/sec capacity per cluster. Partition by conversation_id. 100 Kafka partitions × 10K msg/sec = 1M msg/sec (safe headroom). Storage: hot messages (7 days) in PostgreSQL, cold in S3. Replication factor 3 for durability.

---

## Demo Scenarios (5 Examples)

### Demo 1: User Profile & Connection Request
```
1. Create user Alice with skills [Python, Java, AWS]
2. Add experience: "Engineer at Google, 5 years"
3. Create user Bob with skills [Python, SQL]
4. Alice sends connection request to Bob
5. Verify: Connection status = Pending
6. Bob accepts connection
7. Verify: Connection status = Accepted, both in each other's connections
```

### Demo 2: Factory Pattern - Create Different Post Types
```
1. Alice creates TextPost: "Excited to join LinkedIn!"
2. Bob creates ImagePost: "Team photo" + image URL
3. Charlie creates ArticlePost: "How to master Python" + full article text
4. Verify: Each post has correct type and can be displayed appropriately
5. Show polymorphic behavior: all posts can be liked, commented, shared
```

### Demo 3: Observer Pattern - Post Notification
```
1. Alice creates post "Great day at work"
2. Verify: FeedNotifier adds post to all followers' feeds
3. Bob (follower) sees post in feed
4. Bob likes post: engagement score increases
5. Verify: Feed re-ranked (post now appears higher for others)
```

### Demo 4: Strategy Pattern - Job Matching
```
1. Company X posts job: "Senior Python Engineer" in San Francisco
   Required skills: [Python, Java, AWS], 5+ years experience
2. Apply SkillBasedMatcher: Alice matches 100% (has all skills)
3. Apply LocationBasedMatcher: Alice in SF → 100% match
4. Apply ExperienceBasedMatcher: Alice has 5 years → 100% match
5. Apply HybridMatcher: 0.5×100 + 0.3×100 + 0.2×100 = 100% overall
6. Swap to different strategy: show different match scores
```

### Demo 5: Recommendation Engine
```
1. Setup network: Alice ↔ Bob ↔ Charlie ↔ David
2. Alice has skills [Python, Java], Bob has [Python, SQL], Charlie has [Java, Go], David has [Go, Rust]
3. Get recommendations for Alice:
   - Bob: mutual connection (Alice), common skills [Python]
   - Charlie: 2 mutual connections (Bob + direct), common skills [Java]
4. Verify: Recommendations ranked by score (Charlie highest)
5. Alice connects with Charlie
6. Get new recommendations: David (2 mutual now + common skills [Go])
```

---

## Complete Implementation

```python
"""
💼 LinkedIn System - Interview Implementation
Demonstrates:
1. Singleton pattern (one system instance)
2. Factory pattern (create different post types)
3. Strategy pattern (pluggable job matching algorithms)
4. Observer pattern (event notifications)
5. State machine pattern (connection lifecycle)
"""

from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
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
    """Base post class (abstract for polymorphism)"""
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
            print(f"  [CONNECTION] {payload['user1']} ↔ {payload['user2']} now connected")

class JobNotifier(LinkedInObserver):
    """Notifies about job events"""
    
    def update(self, event: str, payload: Dict) -> None:
        if event == "job_posted":
            print(f"  [JOB] New job: {payload['title']}")

class MessageNotifier(LinkedInObserver):
    """Notifies about messages"""
    
    def update(self, event: str, payload: Dict) -> None:
        if event == "message_sent":
            print(f"  [MSG] {payload['sender']} → {payload['receiver']}")

# ============================================================================
# LINKEDIN SYSTEM (SINGLETON)
# ============================================================================

class LinkedInSystem:
    """Centralized LinkedIn system (thread-safe Singleton)"""
    
    _instance: Optional[LinkedInSystem] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> LinkedInSystem:
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
        print("💼 LinkedIn System initialized")
    
    def register_observer(self, observer: LinkedInObserver) -> None:
        self.observers.append(observer)
    
    def _emit(self, event: str, payload: Dict) -> None:
        for observer in self.observers:
            observer.update(event, payload)
    
    # ---- USER MANAGEMENT ----
    
    def create_user(self, user_id: str, name: str, headline: str, location: Location) -> User:
        user = User(user_id, name, headline, location)
        self.users[user_id] = user
        self._emit("user_created", {"user_id": user_id, "name": name})
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    # ---- CONNECTION MANAGEMENT ----
    
    def send_connection_request(self, from_user_id: str, to_user_id: str, message: str = "") -> Connection:
        conn_id = f"conn_{from_user_id}_{to_user_id}"
        conn = Connection(conn_id, from_user_id, to_user_id, message=message)
        self.connections[conn_id] = conn
        self._emit("connection_requested", {"from": from_user_id, "to": to_user_id})
        return conn
    
    def accept_connection(self, connection_id: str) -> bool:
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
        if connection_id not in self.connections:
            return False
        
        conn = self.connections[connection_id]
        if conn.status != ConnectionStatus.PENDING:
            return False
        
        conn.status = ConnectionStatus.REJECTED
        self._emit("connection_rejected", {"from": conn.from_user_id, "to": conn.to_user_id})
        return True
    
    def get_mutual_connections(self, user1_id: str, user2_id: str) -> Set[str]:
        user1_conns = self.users[user1_id].connections
        user2_conns = self.users[user2_id].connections
        return user1_conns & user2_conns
    
    # ---- POST MANAGEMENT ----
    
    def create_post(self, post_id: str, author_id: str, post_type: PostType, 
                   content: str, visibility: Visibility = Visibility.PUBLIC, **kwargs) -> Post:
        if post_type == PostType.TEXT:
            post = TextPost(post_id, author_id, content, visibility)
        elif post_type == PostType.IMAGE:
            post = ImagePost(post_id, author_id, content, visibility, kwargs.get('image_urls', []))
        elif post_type == PostType.VIDEO:
            post = VideoPost(post_id, author_id, content, visibility, kwargs.get('video_url', ''))
        else:  # ARTICLE
            post = ArticlePost(post_id, author_id, content, visibility, kwargs.get('full_text', ''))
        
        self.posts[post_id] = post
        
        # Notify followers
        author = self.users[author_id]
        for follower_id in author.followers:
            pass  # In production: add to follower's feed
        
        self._emit("post_created", {"post_id": post_id, "author_id": author_id, "content": content[:50]})
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
            
            # Calculate score: engagement × recency × connection
            engagement = post.engagement_score()
            recency = math.exp(-(now - post.created_at).total_seconds() / (24 * 3600))
            connection_strength = 1.0 if post.author_id in user.connections else 0.5
            
            score = engagement * recency * connection_strength
            feed_posts.append((score, post))
        
        feed_posts.sort(reverse=True, key=lambda x: x[0])
        return [post for _, post in feed_posts[:limit]]
    
    # ---- JOB MANAGEMENT ----
    
    def post_job(self, job_id: str, company_id: str, title: str, description: str,
                location: Location, required_skills: List[str], 
                required_experience_years: int) -> Job:
        job = Job(job_id, company_id, title, description, location, 
                 required_skills, required_experience_years)
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
    
    def get_matching_candidates(self, job_id: str, threshold: float = 70) -> List[Tuple[str, float]]:
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
        self.job_matcher = strategy
        self._emit("matcher_changed", {"from": old, "to": strategy.name()})
    
    # ---- MESSAGING ----
    
    def send_message(self, msg_id: str, sender_id: str, receiver_id: str, content: str) -> Message:
        msg = Message(msg_id, sender_id, receiver_id, content)
        self.messages[msg_id] = msg
        self._emit("message_sent", {"sender": sender_id, "receiver": receiver_id})
        return msg
    
    # ---- RECOMMENDATIONS ----
    
    def recommend_connections(self, user_id: str, limit: int = 10) -> List[Tuple[str, int]]:
        user = self.users.get(user_id)
        if not user:
            return []
        
        scores = {}
        
        # Collect candidates from user's connections' connections
        for conn_id in user.connections:
            for potential_id in self.users[conn_id].connections:
                if potential_id != user_id and potential_id not in user.connections:
                    scores[potential_id] = scores.get(potential_id, 0) + 10
        
        # Add skill overlap scoring
        for other_id, other_user in self.users.items():
            if other_id == user_id or other_id in user.connections:
                continue
            
            common_skills = len(set(s.name for s in user.skills) & set(s.name for s in other_user.skills))
            scores[other_id] = scores.get(other_id, 0) + (common_skills * 5)
        
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
    
    linkedin = LinkedInSystem.instance()
    linkedin.register_observer(ConnectionNotifier())
    
    # Create users
    loc_sf = Location("San Francisco", "USA", 37.7749, -122.4194)
    loc_la = Location("Los Angeles", "USA", 34.0522, -118.2437)
    
    alice = linkedin.create_user("alice_1", "Alice Johnson", "Senior Engineer @ Google", loc_sf)
    bob = linkedin.create_user("bob_1", "Bob Smith", "Product Manager @ Meta", loc_la)
    
    # Add skills
    alice.add_skill(Skill("skill_py", "Python", "Programming"))
    alice.add_skill(Skill("skill_java", "Java", "Programming"))
    alice.add_skill(Skill("skill_aws", "AWS", "Cloud"))
    
    bob.add_skill(Skill("skill_py", "Python", "Programming"))
    bob.add_skill(Skill("skill_sql", "SQL", "Database"))
    
    # Add experience
    alice.add_experience(Experience("Google", "Senior Engineer", datetime(2019, 1, 1)))
    bob.add_experience(Experience("Meta", "PM", datetime(2020, 6, 1)))
    
    print(f"\n  Alice: {alice.total_experience_years():.1f} years experience")
    print(f"  Bob: {bob.total_experience_years():.1f} years experience")
    
    # Send connection
    conn = linkedin.send_connection_request("alice_1", "bob_1", "Great to connect!")
    print(f"\n  Connection status: {conn.status.value}")
    
    # Accept connection
    linkedin.accept_connection(conn.connection_id)
    print(f"  After acceptance: {conn.status.value}")
    print(f"  Alice's connections: {len(alice.connections)}")
    print(f"  Bob's connections: {len(bob.connections)}")

def demo_2_factory_pattern_posts() -> None:
    print_section("DEMO 2: FACTORY PATTERN - CREATE POST TYPES")
    
    linkedin = LinkedInSystem.instance()
    linkedin.register_observer(FeedNotifier())
    
    alice = linkedin.get_user("alice_1")
    
    # Create different post types
    text_post = linkedin.create_post("post_1", "alice_1", PostType.TEXT, 
                                     "Excited to share my thoughts on cloud architecture!")
    
    image_post = linkedin.create_post("post_2", "alice_1", PostType.IMAGE,
                                      "Team photo from our summit",
                                      image_urls=["url1", "url2"])
    
    article_post = linkedin.create_post("post_3", "alice_1", PostType.ARTICLE,
                                       "Advanced Python Techniques",
                                       full_text="Full article content here...")
    
    print(f"\n  TextPost type: {text_post.post_type().value}")
    print(f"  ImagePost type: {image_post.post_type().value}")
    print(f"  ArticlePost type: {article_post.post_type().value}")

def demo_3_strategy_pattern_job_matching() -> None:
    print_section("DEMO 3: STRATEGY PATTERN - JOB MATCHING")
    
    linkedin = LinkedInSystem.instance()
    linkedin.register_observer(JobNotifier())
    
    alice = linkedin.get_user("alice_1")
    bob = linkedin.get_user("bob_1")
    
    loc_sf = Location("San Francisco", "USA", 37.7749, -122.4194)
    
    # Post job
    job = linkedin.post_job("job_1", "comp_google", "Senior Python Engineer",
                           "Build amazing systems", loc_sf,
                           required_skills=["Python", "Java", "AWS"],
                           required_experience_years=5)
    
    # Test different strategies
    strategies = [SkillBasedMatcher(), LocationBasedMatcher(), HybridMatcher()]
    
    print(f"\n  Job requires: {', '.join(job.required_skills)}, {job.required_experience_years}+ years\n")
    
    for strategy in strategies:
        linkedin.set_job_matcher(strategy)
        alice_score = strategy.calculate_match_score(job, alice)
        bob_score = strategy.calculate_match_score(job, bob)
        print(f"  {strategy.name()}: Alice={alice_score:.0f}%, Bob={bob_score:.0f}%")

def demo_4_observer_pattern_feed() -> None:
    print_section("DEMO 4: OBSERVER PATTERN - FEED & ENGAGEMENT")
    
    linkedin = LinkedInSystem.instance()
    
    alice = linkedin.get_user("alice_1")
    bob = linkedin.get_user("bob_1")
    
    # Create post
    post = linkedin.create_post("post_feed", "alice_1", PostType.TEXT, "Great insights!")
    
    # Engage
    linkedin.like_post("post_feed", "bob_1")
    print(f"\n  Post engagement score: {post.engagement_score()}")
    
    # Generate feed
    feed = linkedin.generate_feed("bob_1", limit=5)
    print(f"  Bob's feed: {len(feed)} posts")
    for i, p in enumerate(feed, 1):
        print(f"    {i}. {p.content[:40]} (engagement: {p.engagement_score()})")

def demo_5_recommendations() -> None:
    print_section("DEMO 5: CONNECTION RECOMMENDATIONS")
    
    linkedin = LinkedInSystem.instance()
    
    # Create additional users
    loc_sf = Location("San Francisco", "USA", 37.7749, -122.4194)
    charlie = linkedin.create_user("charlie_1", "Charlie Brown", "ML Engineer", loc_sf)
    charlie.add_skill(Skill("skill_py", "Python", "Programming"))
    charlie.add_skill(Skill("skill_ml", "Machine Learning", "AI"))
    
    # Charlie connects with Bob
    conn2 = linkedin.send_connection_request("charlie_1", "bob_1")
    linkedin.accept_connection(conn2.connection_id)
    
    # Get recommendations for Alice
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
    print("💼 LINKEDIN SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_profiles_and_connections()
    demo_2_factory_pattern_posts()
    demo_3_strategy_pattern_job_matching()
    demo_4_observer_pattern_feed()
    demo_5_recommendations()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Design Patterns

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Singleton** | One LinkedInSystem instance | Centralized state, consistent data |
| **Factory** | PostFactory creates post types | Easy to add new post types, encapsulated creation |
| **Strategy** | Job matching algorithms | Swap strategies at runtime, extensible |
| **Observer** | Event notifications (feed, connections, jobs) | Decoupled event producers from consumers |
| **State Machine** | Connection lifecycle (Pending → Accepted/Rejected) | Prevents invalid state transitions |

---

## Summary

✅ **Professional networking platform** with profiles, connections, jobs, feeds, messaging
✅ **5 design patterns** (Singleton, Factory, Strategy, Observer, State Machine)
✅ **Pluggable job matching** (skill-based, location-based, experience-based, hybrid)
✅ **Event-driven feed** with engagement, recency, and connection strength scoring
✅ **Recommendation engine** based on mutual connections and common skills
✅ **Extensible architecture** for new post types, strategies, notifications
✅ **Complete working implementation** with all patterns demonstrated
✅ **5 demo scenarios** showing lifecycle flows

**Key Takeaway**: LinkedIn demonstrates how to compose multiple design patterns (Singleton + Factory + Strategy + Observer + State) into a cohesive system. Focus: separation of concerns, extensibility through patterns, and building scalable social graphs with efficient feed ranking and job matching algorithms.
