# 💼 LinkedIn System - Complete Design Reference

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Entities](#core-entities)
4. [Design Patterns](#design-patterns)
5. [SOLID Principles](#solid-principles)
6. [Key Algorithms](#key-algorithms)
7. [UML Diagrams](#uml-diagrams)
8. [API Design](#api-design)
9. [Scalability Considerations](#scalability-considerations)
10. [Interview Q&A](#interview-qa)

---

## System Overview

LinkedIn is a professional networking platform that enables users to:
- Create and manage professional profiles
- Build a network through connections
- Share and consume professional content (posts, articles)
- Search and apply for jobs
- Send messages and recommendations
- Follow companies and influencers

### Key Features
- **Profile Management**: Skills, experience, education, certifications
- **Connection System**: 1st, 2nd, 3rd degree connections with requests
- **Content Feed**: Personalized feed with posts, likes, comments, shares
- **Job Platform**: Job postings, applications, matching algorithms
- **Messaging**: Real-time conversations between connections
- **Recommendations**: Endorsements and written recommendations
- **Company Pages**: Company profiles with followers and job postings

---

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                   LinkedIn System                        │
│                    (Singleton)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │   User   │  │Connection│  │   Post   │  │   Job   ││
│  │ Manager  │  │ Manager  │  │ Manager  │  │ Manager ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Message  │  │   Feed   │  │  Search  │             │
│  │ Manager  │  │ Manager  │  │ Manager  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌──────────┐
    │Database│    │  Cache  │    │Notification│
    │        │    │ (Redis) │    │  Service  │
    └────────┘    └─────────┘    └──────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **UserManager** | Profile creation, updates, skill management |
| **ConnectionManager** | Connection requests, acceptance, network graph |
| **PostManager** | Post creation, interactions (like/comment/share) |
| **JobManager** | Job posting, applications, matching |
| **MessageManager** | Conversation threads, message delivery |
| **FeedManager** | Feed generation, ranking, personalization |
| **SearchManager** | User search, job search, indexing |

---

## Core Entities

### 1. User
**Purpose**: Represents a LinkedIn user profile

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| user_id | str | Unique identifier |
| name | str | Full name |
| email | str | Email address (unique) |
| headline | str | Professional headline |
| summary | str | About section |
| skills | List[Skill] | List of skills |
| experiences | List[Experience] | Work history |
| education | List[Education] | Education history |
| connections | List[str] | Connected user IDs |
| followers | List[str] | Follower user IDs |
| created_at | datetime | Account creation timestamp |

**Key Methods**:
```python
add_skill(skill: Skill) -> bool
add_experience(experience: Experience) -> bool
remove_skill(skill_id: str) -> bool
get_connection_degree(other_user_id: str) -> int  # 1st, 2nd, 3rd
```

**Relationships**:
- Has many **Connections** (bidirectional)
- Creates many **Posts**
- Sends/Receives **Messages**
- Creates **JobApplications**

---

### 2. Connection
**Purpose**: Represents a connection relationship between two users

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| connection_id | str | Unique identifier |
| from_user_id | str | Requestor user ID |
| to_user_id | str | Recipient user ID |
| status | ConnectionStatus | PENDING/ACCEPTED/REJECTED |
| message | str | Optional connection message |
| created_at | datetime | Request timestamp |
| updated_at | datetime | Status update timestamp |

**State Transitions**:
```
PENDING ──accept()──> ACCEPTED
    │
    └──reject()──> REJECTED
```

**Key Methods**:
```python
accept() -> bool                    # Change status to ACCEPTED
reject() -> bool                    # Change status to REJECTED
withdraw() -> bool                  # Cancel pending request
get_mutual_connections() -> List[User]  # Find common connections
```

---

### 3. Post
**Purpose**: Represents content shared by users

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| post_id | str | Unique identifier |
| author_id | str | User who created post |
| content | str | Post text content |
| media | List[Media] | Images/videos/documents |
| likes | List[str] | User IDs who liked |
| comments | List[Comment] | Comments on post |
| shares | List[Share] | Share records |
| visibility | Visibility | PUBLIC/CONNECTIONS/PRIVATE |
| created_at | datetime | Post creation time |

**Post Types** (Factory Pattern):
- **TextPost**: Plain text content
- **ImagePost**: Text + images
- **VideoPost**: Text + video
- **ArticlePost**: Long-form article
- **PollPost**: Poll with options

**Key Methods**:
```python
add_like(user_id: str) -> bool
remove_like(user_id: str) -> bool
add_comment(comment: Comment) -> bool
share(user_id: str, message: str) -> Share
get_engagement_score() -> float  # likes + 3*comments + 5*shares
```

---

### 4. Job
**Purpose**: Represents a job posting

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| job_id | str | Unique identifier |
| company_id | str | Posting company |
| title | str | Job title |
| description | str | Job description |
| location | Location | Job location |
| job_type | JobType | FULL_TIME/PART_TIME/CONTRACT |
| required_skills | List[str] | Required skills |
| experience_years | int | Years of experience needed |
| salary_range | SalaryRange | Min/max salary |
| applications | List[Application] | Applications received |
| status | JobStatus | OPEN/CLOSED/FILLED |
| created_at | datetime | Posting timestamp |

**Key Methods**:
```python
apply(user_id: str, resume: str) -> Application
close() -> bool
get_matching_candidates(limit: int) -> List[User]  # Use Strategy pattern
calculate_match_score(user: User) -> float
```

---

### 5. Message
**Purpose**: Represents a message in a conversation

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| message_id | str | Unique identifier |
| conversation_id | str | Conversation thread ID |
| sender_id | str | Sender user ID |
| receiver_id | str | Receiver user ID |
| content | str | Message text |
| is_read | bool | Read status |
| created_at | datetime | Send timestamp |
| read_at | datetime | Read timestamp |

**Key Methods**:
```python
mark_as_read() -> bool
reply(content: str) -> Message
delete() -> bool
```

---

### 6. Company
**Purpose**: Represents a company profile

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| company_id | str | Unique identifier |
| name | str | Company name |
| industry | str | Industry type |
| size | CompanySize | 1-10, 11-50, 51-200, etc. |
| description | str | About the company |
| website | str | Company website |
| followers | List[str] | Following user IDs |
| jobs | List[str] | Posted job IDs |
| created_at | datetime | Creation timestamp |

---

## Design Patterns

### 1. Singleton Pattern
**Purpose**: Ensure single instance of LinkedIn system

**Implementation**:
```python
class LinkedInSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Why**: Centralized state management, single point of access

---

### 2. Observer Pattern
**Purpose**: Notify users of feed updates and activities

**Structure**:
```
Subject (Post)          Observer (User)
├── attach(observer)    ├── update(event)
├── detach(observer)    └── (Receives notifications)
└── notify()
```

**Example**:
```python
class Post(Subject):
    def add_like(self, user_id):
        self.likes.append(user_id)
        self.notify(Event.LIKE_ADDED, user_id)

class User(Observer):
    def update(self, event, data):
        if event == Event.LIKE_ADDED:
            self.send_notification(f"Your post got a like")
```

**Use Cases**:
- Post created → Notify followers
- Comment added → Notify post author
- Connection accepted → Notify both users
- Job application → Notify recruiter

---

### 3. Strategy Pattern
**Purpose**: Interchangeable job matching algorithms

**Interface**:
```python
class JobMatchingStrategy(ABC):
    @abstractmethod
    def calculate_match_score(self, job: Job, user: User) -> float:
        pass
```

**Implementations**:

**a) SkillBasedMatcher**:
```python
score = (matched_skills / total_required_skills) * 100
# Example: 3/5 skills = 60% match
```

**b) LocationBasedMatcher**:
```python
distance = calculate_distance(user.location, job.location)
score = 100 if distance < 50km else 50
```

**c) ExperienceBasedMatcher**:
```python
exp_diff = abs(user.years_experience - job.required_years)
score = 100 - (exp_diff * 10)  # -10 points per year difference
```

**Usage**:
```python
matcher = SkillBasedMatcher()
score = matcher.calculate_match_score(job, user)
```

---

### 4. Factory Pattern
**Purpose**: Create different types of posts and content

**Implementation**:
```python
class PostFactory:
    @staticmethod
    def create_post(post_type: PostType, **kwargs) -> Post:
        if post_type == PostType.TEXT:
            return TextPost(**kwargs)
        elif post_type == PostType.IMAGE:
            return ImagePost(**kwargs)
        elif post_type == PostType.VIDEO:
            return VideoPost(**kwargs)
        elif post_type == PostType.ARTICLE:
            return ArticlePost(**kwargs)
```

**Benefits**:
- Encapsulates creation logic
- Easy to add new post types
- Consistent object creation

---

### 5. State Pattern
**Purpose**: Model connection request lifecycle

**States**:
```
PendingState
├── accept() → AcceptedState
├── reject() → RejectedState
└── withdraw() → WithdrawnState
```

**Implementation**:
```python
class ConnectionState(ABC):
    @abstractmethod
    def accept(self, connection): pass
    
    @abstractmethod
    def reject(self, connection): pass

class PendingState(ConnectionState):
    def accept(self, connection):
        connection.state = AcceptedState()
        connection.update_connections()
    
    def reject(self, connection):
        connection.state = RejectedState()
```

---

## SOLID Principles

### Single Responsibility Principle (SRP)
❌ **Violation**:
```python
class User:
    def send_connection_request(self, to_user): ...
    def create_post(self, content): ...
    def apply_for_job(self, job): ...
    def send_message(self, to_user, message): ...
    # Too many responsibilities!
```

✅ **Correct**:
```python
class User:
    # Only profile data
    def add_skill(self, skill): ...
    def update_headline(self, headline): ...

class ConnectionManager:
    def send_request(self, from_user, to_user): ...
    
class PostManager:
    def create_post(self, user, content): ...
    
class JobManager:
    def apply_for_job(self, user, job): ...
```

---

### Open/Closed Principle (OCP)
✅ **Achieved through Strategy Pattern**:
```python
# Open for extension (add new strategies)
class SeniorityBasedMatcher(JobMatchingStrategy):
    def calculate_match_score(self, job, user):
        # New algorithm without modifying existing code
        ...

# Closed for modification (existing strategies unchanged)
```

---

### Liskov Substitution Principle (LSP)
✅ **All post types can substitute base Post**:
```python
def display_feed(posts: List[Post]):
    for post in posts:  # Works with any Post subtype
        print(post.get_content())
        print(post.get_engagement_score())
```

---

### Interface Segregation Principle (ISP)
✅ **Specific interfaces instead of one large interface**:
```python
class Likeable(ABC):
    @abstractmethod
    def add_like(self, user_id): pass

class Commentable(ABC):
    @abstractmethod
    def add_comment(self, comment): pass

class Shareable(ABC):
    @abstractmethod
    def share(self, user_id): pass

# Posts implement all three
class Post(Likeable, Commentable, Shareable):
    ...

# Jobs only implement Likeable
class Job(Likeable):
    ...
```

---

### Dependency Inversion Principle (DIP)
✅ **Depend on abstractions**:
```python
# High-level module depends on abstraction
class FeedManager:
    def __init__(self, ranker: FeedRankingStrategy):
        self.ranker = ranker  # Abstraction, not concrete class
    
    def generate_feed(self, user):
        posts = self.get_posts()
        return self.ranker.rank(posts, user)

# Low-level modules implement abstraction
class EngagementBasedRanker(FeedRankingStrategy):
    def rank(self, posts, user): ...

class RecencyBasedRanker(FeedRankingStrategy):
    def rank(self, posts, user): ...
```

---

## Key Algorithms

### 1. Connection Degree Calculation
**Purpose**: Find if user is 1st, 2nd, or 3rd degree connection

**Algorithm**: BFS (Breadth-First Search)
```python
def get_connection_degree(from_user_id: str, to_user_id: str) -> int:
    if to_user_id in users[from_user_id].connections:
        return 1  # Direct connection
    
    visited = {from_user_id}
    queue = [(from_user_id, 0)]
    
    while queue:
        current_user, degree = queue.pop(0)
        
        if degree >= 3:
            return -1  # Beyond 3rd degree
        
        for connection_id in users[current_user].connections:
            if connection_id == to_user_id:
                return degree + 1
            
            if connection_id not in visited:
                visited.add(connection_id)
                queue.append((connection_id, degree + 1))
    
    return -1  # Not connected
```

**Complexity**: O(V + E) where V = users, E = connections

---

### 2. Mutual Connections
**Purpose**: Find common connections between two users

**Algorithm**:
```python
def get_mutual_connections(user1_id: str, user2_id: str) -> List[User]:
    connections1 = set(users[user1_id].connections)
    connections2 = set(users[user2_id].connections)
    
    mutual = connections1.intersection(connections2)
    return [users[uid] for uid in mutual]
```

**Complexity**: O(N) where N = average connection count

---

### 3. Feed Ranking Algorithm
**Purpose**: Personalize and rank feed posts

**Scoring Function**:
```python
def calculate_feed_score(post: Post, viewer: User) -> float:
    # Engagement score
    engagement = post.likes_count + 3*post.comments_count + 5*post.shares_count
    
    # Recency decay (exponential)
    hours_since_post = (now - post.created_at).total_seconds() / 3600
    recency_factor = math.exp(-hours_since_post / 24)  # Half-life of 24 hours
    
    # Connection strength
    if post.author_id in viewer.connections:
        connection_strength = 1.0  # 1st degree
    elif get_connection_degree(viewer.user_id, post.author_id) == 2:
        connection_strength = 0.5  # 2nd degree
    else:
        connection_strength = 0.1  # 3rd degree or public
    
    # Content relevance (simplified)
    relevance = calculate_skill_overlap(post.tags, viewer.skills) / 10
    
    # Final score
    score = engagement * recency_factor * connection_strength * (1 + relevance)
    
    return score
```

**Complexity**: O(N log N) for sorting N posts

---

### 4. Connection Recommendations
**Purpose**: Suggest relevant people to connect with

**Scoring Algorithm**:
```python
def recommend_connections(user: User, limit: int = 10) -> List[User]:
    scores = {}
    
    for candidate in all_users:
        if candidate.user_id == user.user_id:
            continue
        if candidate.user_id in user.connections:
            continue
        
        score = 0
        
        # Mutual connections (strongest signal)
        mutual = get_mutual_connections(user.user_id, candidate.user_id)
        score += len(mutual) * 10
        
        # Common skills
        common_skills = set(user.skills) & set(candidate.skills)
        score += len(common_skills) * 5
        
        # Same company
        if any(e1.company == e2.company 
               for e1 in user.experiences 
               for e2 in candidate.experiences):
            score += 15
        
        # Same education
        if any(e1.school == e2.school 
               for e1 in user.education 
               for e2 in candidate.education):
            score += 10
        
        scores[candidate.user_id] = score
    
    # Return top N
    sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [users[uid] for uid, score in sorted_candidates[:limit]]
```

**Complexity**: O(N * M) where N = users, M = connections per user

---

## UML Diagrams

### Class Diagram
```
┌─────────────────────────┐
│         User            │
├─────────────────────────┤
│ - user_id: str          │
│ - name: str             │
│ - headline: str         │
│ - skills: List[Skill]   │
│ - connections: List[str]│
├─────────────────────────┤
│ + add_skill()           │
│ + add_experience()      │
│ + get_degree()          │
└─────────────────────────┘
           │
           │ creates
           ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│      Connection         │         │         Post            │
├─────────────────────────┤         ├─────────────────────────┤
│ - connection_id: str    │         │ - post_id: str          │
│ - from_user: str        │◄────────┤ - author_id: str        │
│ - to_user: str          │ creates │ - content: str          │
│ - status: Status        │         │ - likes: List[str]      │
│ - message: str          │         │ - comments: List        │
├─────────────────────────┤         ├─────────────────────────┤
│ + accept()              │         │ + add_like()            │
│ + reject()              │         │ + add_comment()         │
│ + get_mutual()          │         │ + share()               │
└─────────────────────────┘         └─────────────────────────┘
           │                                   │
           │                                   │ inherits
           │                                   ▼
           │                        ┌─────────────────────┐
           │                        │    TextPost         │
           │                        ├─────────────────────┤
           │                        │    ImagePost        │
           │                        ├─────────────────────┤
           │                        │    VideoPost        │
           │                        ├─────────────────────┤
           │                        │    ArticlePost      │
           │                        └─────────────────────┘
           │
           ▼
┌─────────────────────────┐
│         Job             │
├─────────────────────────┤
│ - job_id: str           │
│ - company_id: str       │
│ - title: str            │
│ - required_skills: List │
│ - applications: List    │
├─────────────────────────┤
│ + apply()               │
│ + close()               │
│ + match_candidates()    │
└─────────────────────────┘
```

---

### State Diagram - Connection Request
```
┌──────────┐
│  Start   │
└────┬─────┘
     │
     │ send_request()
     ▼
┌──────────────┐
│   PENDING    │◄──────────────┐
└──────┬───────┘               │
       │                       │
       ├─── accept() ──────────┼──────┐
       │                       │      │
       │                       │      ▼
       │              ┌────────────────────┐
       │              │     ACCEPTED       │
       │              └────────────────────┘
       │
       ├─── reject() ─────────────────┐
       │                              │
       │                              ▼
       │                     ┌────────────────┐
       │                     │    REJECTED    │
       │                     └────────────────┘
       │
       └─── withdraw() ──────────────┐
                                     │
                                     ▼
                            ┌────────────────┐
                            │   WITHDRAWN    │
                            └────────────────┘
```

---

### Sequence Diagram - Send Connection Request
```
User A          ConnectionManager       User B          NotificationService
  │                    │                   │                    │
  │──send_request()───>│                   │                    │
  │                    │                   │                    │
  │                    │──validate()       │                    │
  │                    │                   │                    │
  │                    │──create_connection()                   │
  │                    │                   │                    │
  │                    │──────────notify()─────────────────────>│
  │                    │                   │                    │
  │                    │                   │<────send_email()───│
  │<──connection_id────│                   │                    │
  │                    │                   │                    │
```

---

### Sequence Diagram - Create Post & Notify Followers
```
User        PostManager     Post      FeedManager    Followers    NotificationService
 │              │            │             │             │                │
 │─create()────>│            │             │             │                │
 │              │            │             │             │                │
 │              │──new()────>│             │             │                │
 │              │            │             │             │                │
 │              │            │──notify()──────────────────────────────────>│
 │              │            │             │             │                │
 │              │            │             │             │<──push()───────│
 │              │            │             │             │                │
 │              │────────────add_to_feed()────────────>  │                │
 │              │            │             │             │                │
 │<─post_id─────│            │             │             │                │
 │              │            │             │             │                │
```

---

## API Design

### RESTful Endpoints

#### User Management
```
POST   /users                    Create new user
GET    /users/{user_id}          Get user profile
PUT    /users/{user_id}          Update user profile
DELETE /users/{user_id}          Delete user
GET    /users/{user_id}/skills   Get user skills
POST   /users/{user_id}/skills   Add skill
```

#### Connections
```
POST   /connections                      Send connection request
GET    /connections/{connection_id}      Get connection details
PUT    /connections/{connection_id}      Accept/Reject request
DELETE /connections/{connection_id}      Remove connection
GET    /users/{user_id}/connections      Get user's connections
GET    /users/{user_id}/recommendations  Get connection recommendations
```

#### Posts
```
POST   /posts                     Create post
GET    /posts/{post_id}           Get post
PUT    /posts/{post_id}           Update post
DELETE /posts/{post_id}           Delete post
POST   /posts/{post_id}/likes     Like post
POST   /posts/{post_id}/comments  Add comment
POST   /posts/{post_id}/shares    Share post
GET    /feed                      Get personalized feed
```

#### Jobs
```
POST   /jobs                      Create job posting
GET    /jobs/{job_id}             Get job details
PUT    /jobs/{job_id}             Update job
DELETE /jobs/{job_id}             Close job
POST   /jobs/{job_id}/apply       Apply for job
GET    /jobs/search               Search jobs
GET    /users/{user_id}/matches   Get matching jobs
```

#### Messages
```
POST   /messages                  Send message
GET    /messages/{message_id}     Get message
GET    /conversations             Get conversations
GET    /conversations/{conv_id}   Get conversation thread
PUT    /messages/{message_id}/read Mark as read
```

---

## Scalability Considerations

### Database Design
```
Users Table (PostgreSQL)
- Indexed on: user_id, email
- Partitioned by: created_at (time-based)

Connections Table (Graph DB - Neo4j)
- Optimized for relationship queries
- Fast BFS for degree calculation

Posts Table (PostgreSQL)
- Indexed on: author_id, created_at
- Partitioned by: created_at

Feed Cache (Redis)
- Key: user_id:feed
- TTL: 30 minutes
- Stores pre-computed feed with scores
```

### Caching Strategy
```python
# 1. Feed Cache (Redis)
feed_cache_key = f"user:{user_id}:feed"
cached_feed = redis.get(feed_cache_key)
if cached_feed:
    return cached_feed
else:
    feed = generate_feed(user_id)
    redis.setex(feed_cache_key, 1800, feed)  # 30 min TTL

# 2. User Profile Cache (Redis)
profile_key = f"user:{user_id}:profile"
redis.setex(profile_key, 3600, user_profile)  # 1 hour TTL

# 3. Connection Cache (Redis Set)
connections_key = f"user:{user_id}:connections"
redis.sadd(connections_key, *connection_ids)
```

### Load Balancing
- **Application Servers**: Round-robin load balancing
- **Database**: Read replicas for queries, write to master
- **Message Queue**: Kafka for async processing (feed generation, notifications)

### Microservices Architecture
```
API Gateway
├── User Service (Profile, Skills, Experience)
├── Connection Service (Requests, Network Graph)
├── Feed Service (Post Feed Generation)
├── Job Service (Postings, Applications, Matching)
├── Message Service (Conversations, Real-time)
└── Notification Service (Email, Push, In-app)
```

---

## Interview Q&A

### Q1: How do you handle the feed generation for millions of users?
**Answer**: 
- **Fan-out on write**: When user creates post, immediately add to followers' feeds (Redis lists)
- **Hybrid approach**: Fan-out for users with < 10k followers, pull-based for celebrities
- **Background jobs**: Use Celery/Kafka to process feed updates asynchronously
- **Caching**: Cache generated feeds in Redis with 30-min TTL
- **Pagination**: Return feeds in pages of 20-50 posts

**Code**:
```python
def create_post(user_id, content):
    post = Post(user_id, content)
    
    # Fan-out to followers (async)
    if user.followers_count < 10000:
        celery.send_task('fanout_to_followers', args=[post.id, user.followers])
    
    # Cache invalidation
    redis.delete(f"user:{user_id}:feed")
```

---

### Q2: How do you calculate connection recommendations efficiently?
**Answer**:
- **Pre-computation**: Nightly batch job computes recommendations
- **Mutual connections index**: Maintain inverted index of connections
- **Scoring**: Use multiple signals (mutual, skills, company, education)
- **Caching**: Store top 100 recommendations per user
- **Real-time updates**: Update when user accepts new connection

**Optimization**:
```python
# Inverted index: skill -> [user_ids]
skill_index = {
    "Python": ["user1", "user2", "user5"],
    "Java": ["user2", "user3", "user7"]
}

# Quick candidate generation
candidates = set()
for skill in user.skills:
    candidates.update(skill_index[skill])
# Then score only candidates, not all users
```

---

### Q3: How do you handle real-time messaging at scale?
**Answer**:
- **WebSocket connections**: Persistent connections for online users
- **Message queue**: RabbitMQ/Kafka for message delivery
- **Presence service**: Redis to track online/offline status
- **Read receipts**: Update in batch, not real-time (eventual consistency)
- **Message storage**: Cassandra for horizontal scalability

**Architecture**:
```
User A ──WebSocket──> Message Gateway ──Kafka──> Message Service
                                                       │
                                                       ▼
                                                   Cassandra
                                                       │
                                                       ▼
User B <──WebSocket── Message Gateway <──Kafka── Notification
```

---

### Q4: How would you implement job matching efficiently?
**Answer**:
- **Elasticsearch**: Index jobs with skills, location, experience
- **Inverted index**: skill -> [job_ids]
- **Multiple strategies**: Allow switching between skill/location/experience matching
- **Score threshold**: Only show matches > 70% score
- **Personalization**: Boost jobs from companies user follows

**Query**:
```python
# Elasticsearch query
{
    "query": {
        "function_score": {
            "query": {
                "bool": {
                    "should": [
                        {"terms": {"skills": user.skills}},
                        {"range": {"experience": {"gte": user.years - 2, "lte": user.years + 2}}}
                    ]
                }
            },
            "functions": [
                {"filter": {"term": {"location": user.location}}, "weight": 2}
            ]
        }
    }
}
```

---

### Q5: How do you ensure data consistency across microservices?
**Answer**:
- **Event sourcing**: Store all events (ConnectionCreated, PostLiked)
- **Saga pattern**: Distributed transactions with compensating actions
- **Eventual consistency**: Accept slight delays for better availability
- **Message queue**: Kafka for reliable event delivery
- **Idempotency**: All operations idempotent (duplicate messages OK)

**Example - Create Connection**:
```
1. ConnectionService: Create PENDING connection
2. Emit ConnectionRequestedEvent → Kafka
3. NotificationService: Send notification (subscribe to event)
4. FeedService: Add to feed (subscribe to event)
5. If notification fails → retry (idempotent)
```

---

### Q6: What design patterns are most important for LinkedIn?
**Answer**:
1. **Observer**: Feed updates, notifications (decouples publishers from subscribers)
2. **Strategy**: Job matching algorithms (easily swap strategies)
3. **Singleton**: System instance (single source of truth)
4. **Factory**: Creating different post types (encapsulates creation)
5. **State**: Connection lifecycle (clean state transitions)

---

### Q7: How do you handle the "People You May Know" feature?
**Answer**:
- **Collaborative filtering**: Users with similar connections/skills
- **Graph algorithms**: Friends-of-friends (2nd degree)
- **Scoring**: Mutual connections (10 pts), common skills (5 pts), same company (15 pts)
- **Privacy**: Respect user privacy settings
- **Diversity**: Mix different recommendation reasons

---

### Q8: How would you implement the LinkedIn feed ranking?
**Answer**:
- **Engagement prediction**: ML model predicts if user will engage
- **Recency decay**: Recent posts ranked higher
- **Connection strength**: 1st degree > 2nd > 3rd
- **Content type**: Boost native content over external links
- **Personalization**: User's past engagement patterns

**Ranking Score**:
```
score = engagement_prediction * 0.4
      + recency_score * 0.3
      + connection_strength * 0.2
      + content_quality * 0.1
```

---

### Q9: How do you handle user privacy and permissions?
**Answer**:
- **Access control**: User can set profile visibility (public/connections/private)
- **Connection degrees**: Show different info based on 1st/2nd/3rd degree
- **Block/Report**: Users can block others, report inappropriate content
- **Data encryption**: Encrypt sensitive data (messages, email)
- **Audit logs**: Track who accessed what data

---

### Q10: What trade-offs did you make in this design?
**Answer**:
1. **Consistency vs Availability**: Chose eventual consistency for feed (AP over CP)
2. **Normalization vs Performance**: Denormalized some data for faster reads
3. **Real-time vs Batch**: Hybrid approach (real-time for < 10k, batch for > 10k followers)
4. **Complexity vs Features**: Started with core features, can extend with patterns
5. **Storage vs Compute**: Cache feeds (more storage) to reduce computation

---

## Summary

This LinkedIn system design demonstrates:
✅ **6 core entities** with clear responsibilities
✅ **5 design patterns** applied appropriately
✅ **SOLID principles** throughout the codebase
✅ **Scalable architecture** with caching and microservices
✅ **Key algorithms** for feed ranking, recommendations, job matching
✅ **Complete UML diagrams** for visualization
✅ **RESTful API design** for clean interfaces

**Key Takeaway**: LinkedIn is fundamentally a **social graph** (connections) with **content distribution** (feed). Focus on these two core systems and extend from there.

---

For detailed implementation, see **75_MINUTE_GUIDE.md**
For runnable code, see **INTERVIEW_COMPACT.py**
For quick reference, see **START_HERE.md**
