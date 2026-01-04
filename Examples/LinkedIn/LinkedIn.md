# LinkedIn — 75-Minute Interview Guide

## Quick Start Overview

## ⏱️ 75-Minute Interview Breakdown
| Time | What to Do | Duration |
|------|-----------|----------|
| 0-10 min | Requirements & Architecture | 10 min |
| 10-30 min | Core Entities & Classes | 20 min |
| 30-50 min | Patterns & Business Logic | 20 min |
| 50-70 min | System Integration | 20 min |
| 70-75 min | Demos & Q&A | 5 min |

## 📋 Core Entities (6 Main Classes)
| Entity | Key Attributes | Key Methods |
|--------|---------------|-------------|
| **User** | user_id, name, headline, skills, experience | add_skill(), add_experience() |
| **Connection** | from_user, to_user, status, timestamp | accept(), reject() |
| **Post** | post_id, author, content, likes, comments | add_like(), add_comment() |
| **Job** | job_id, company, title, requirements | apply(), close() |
| **Message** | message_id, sender, receiver, content | mark_read(), reply() |
| **Company** | company_id, name, industry, followers | add_job(), follow() |

## 🎨 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (5 Patterns)
| Pattern | Usage | Example |
|---------|-------|---------|
| **Singleton** | LinkedIn system instance | `LinkedInSystem.get_instance()` |
| **Observer** | Feed updates & notifications | User posts → followers notified |
| **Strategy** | Job matching algorithms | Skill-based, Location-based, Experience-based |
| **Factory** | Post/Message creation | CreatePost(), CreateMessage() |
| **State** | Connection request lifecycle | Pending → Accepted/Rejected |

## 🎯 Demo Scenarios (5 Scenarios)
1. **User Profile Management** - Create profile, add skills, add experience
2. **Connection System** - Send request, accept/reject, view connections
3. **Job Posting & Application** - Post job, apply, match candidates
4. **Feed & Interactions** - Create post, like, comment, share
5. **Messaging System** - Send message, create conversation, notifications

## 🔑 Key Algorithms

### 1. Connection Recommendation Algorithm
```python
# Mutual connections scoring
score = len(mutual_connections) * 10
score += len(common_skills) * 5
score += (1 if same_company else 0) * 15
# Returns top N recommendations sorted by score
```

### 2. Job Matching Algorithm (Strategy Pattern)
```python
# Skill-based matching
match_score = (matched_skills / required_skills) * 100
# Location-based matching
match_score = distance < 50km ? 100 : 50
# Experience-based matching
match_score = abs(years_exp - required_exp) < 2 ? 100 : 70
```

### 3. Feed Ranking Algorithm
```python
# Engagement score
score = likes * 1 + comments * 3 + shares * 5
# Recency decay
score *= exp(-time_since_post / decay_factor)
# Connection strength
score *= connection_strength (0.1 to 1.0)
```

## 💡 Key Talking Points

### Pattern Explanations
**Singleton Pattern**: "We use Singleton for LinkedInSystem to ensure all users interact with the same system instance. This prevents data inconsistency and provides centralized state management."

**Observer Pattern**: "When a user creates a post, all their connections are automatically notified through the Observer pattern. The Post is the Subject, and Followers are Observers. This decouples post creation from notification logic."

**Strategy Pattern**: "Job matching uses Strategy pattern with 3 algorithms: SkillBasedMatcher, LocationBasedMatcher, and ExperienceBasedMatcher. Companies can choose which strategy to use, and we can add new matchers without modifying existing code."

**Factory Pattern**: "PostFactory creates different post types (TextPost, ImagePost, VideoPost, ArticlePost) based on content. This encapsulates creation logic and makes it easy to add new post types."

**State Pattern**: "Connection requests follow State pattern: Pending → Accepted/Rejected. Each state has specific behaviors (send notification, update connection count, etc.)."

### SOLID Principles in Action
**Single Responsibility**: User class handles profile data, ConnectionManager handles connections separately

**Open/Closed**: Strategy pattern allows new job matchers without modifying existing code

**Liskov Substitution**: All post types (TextPost, ImagePost) can substitute base Post class

**Interface Segregation**: Separate interfaces for Likeable, Commentable, Shareable

**Dependency Inversion**: Feed depends on abstract Post interface, not concrete implementations

## ✅ Success Criteria
- [ ] All 6 core entities implemented with proper attributes
- [ ] 5 design patterns clearly demonstrated with code
- [ ] At least 3 demo scenarios run successfully
- [ ] Can explain Observer pattern for feed updates
- [ ] Can explain Strategy pattern for job matching
- [ ] Connection state machine working (Pending → Accepted/Rejected)
- [ ] Feed ranking algorithm implemented
- [ ] Code follows SOLID principles

## 🚀 Quick Commands
```bash
# Run the complete working implementation
python3 INTERVIEW_COMPACT.py

# Run specific demo
python3 -c "from INTERVIEW_COMPACT import demo1_profile_management; demo1_profile_management()"

# Read detailed implementation guide
cat 75_MINUTE_GUIDE.md

# Study complete reference with UML diagrams
cat README.md
```

## 🆘 If You Get Stuck
- **Early phase (< 20 min)**: Focus on User, Connection, Post entities first. Skip Message and Job initially.
- **Mid phase (20-50 min)**: Implement Singleton and Observer patterns. Skip Strategy initially.
- **Late phase (> 50 min)**: Show 2 working demos (Profile + Connections). Explain Feed algorithm verbally.

### Minimum Viable Implementation
1. User entity with skills
2. Connection with Pending/Accepted states
3. Basic Post with likes
4. Singleton LinkedInSystem
5. Observer for post notifications
6. One demo showing user creates post → followers notified

## 📊 Complexity Reference
| Component | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Add Connection | O(1) | O(N) connections |
| Get Feed | O(N log N) | O(N) posts |
| Search Users | O(N) or O(log N) with index | O(N) |
| Job Matching | O(N*M) N=jobs, M=users | O(1) |
| Mutual Connections | O(N) | O(N) |

## 🎓 Interview Tips
1. **Start with User & Connection** - These are the foundation
2. **Explain Observer early** - Shows you understand event-driven design
3. **Draw state diagram** - For connection request lifecycle
4. **Mention scalability** - "We'd use Redis for feed caching in production"
5. **Code defensively** - Check null, validate inputs
6. **Name variables clearly** - `pending_connection_requests` not `pcr`

---
**Remember**: LinkedIn is about **connections** and **content**. Focus on the social graph (User-Connection network) and content distribution (Post-Feed system). Show working code for these core flows!


## 75-Minute Guide

## Quick System Overview
Professional networking platform connecting professionals worldwide with profiles, connections, job postings, messaging, and personalized feed.

**Core Features**: User Profiles | Connections | Job Matching | Feed | Messaging | Recommendations

## Complete Requirements Analysis

### Functional Requirements
1. **User Management**
   - Create/update professional profiles
   - Add skills, experience, education
   - Profile visibility settings
   - Profile view tracking

2. **Connection Management**
   - Send/accept/reject connection requests
   - View connection network (1st, 2nd, 3rd degree)
   - Find mutual connections
   - Connection recommendations

3. **Content & Feed**
   - Create posts (text, image, video, article)
   - Like, comment, share posts
   - Personalized feed generation
   - Content visibility control

4. **Job Management**
   - Company profiles
   - Post job openings
   - Apply for jobs
   - Job matching based on skills/location/experience
   - Track application status

5. **Messaging**
   - Direct messaging between connections
   - Conversation threads
   - Read receipts
   - Message search

6. **Recommendations**
   - Connection recommendations
   - Job recommendations
   - Skill endorsements
   - People you may know

### Non-Functional Requirements
- **Scalability**: Support millions of users
- **Performance**: Feed generation < 500ms, Search < 200ms
- **Availability**: 99.9% uptime
- **Consistency**: Eventual consistency for feeds
- **Security**: Data encryption, privacy controls

### Core Entities (6 Main)
1. **User** - Professional profile with skills/experience
2. **Connection** - Relationship between users
3. **Post** - Content shared on platform
4. **Job** - Job posting with requirements
5. **Company** - Organization profile
6. **Message** - Communication between users

---

## 75-Minute Implementation Timeline

### Phase 0: Requirements Clarification (0-5 minutes)
**Goal**: Understand scope and define boundaries

**Questions to Ask Interviewer**:
```
Q1: "Should we support different post types (text, image, video)?"
    → Yes, use Factory pattern for post creation

Q2: "How should connection requests be handled?"
    → State machine: Pending → Accepted/Rejected

Q3: "What job matching strategy should we use?"
    → Multiple strategies: Skill-based, Location-based, Experience-based

Q4: "Should we implement real-time notifications?"
    → Yes, use Observer pattern for event notifications

Q5: "What about privacy settings for posts?"
    → Support PUBLIC, CONNECTIONS, PRIVATE visibility
```

**Clarify Scope**:
- ✅ Core features: Profiles, Connections, Jobs, Posts, Messages
- ✅ Design patterns: Singleton, Factory, Strategy, Observer, State
- ✅ Algorithms: Feed ranking, Job matching, Connection recommendations
- ❌ Advanced features: Groups, Learning, Ads (out of scope)

**Expected Output**: Clear requirements document + entity list

---

### Phase 1: Architecture & Design (5-15 minutes)
**Goal**: Design system architecture and class relationships

**System Architecture**:
```
┌─────────────────────────────────────────────────┐
│           LinkedInSystem (Singleton)            │
├─────────────────────────────────────────────────┤
│ • UserManager                                   │
│ • ConnectionManager                             │
│ • PostManager (Factory)                         │
│ • JobManager (Strategy)                         │
│ • MessageManager                                │
│ • FeedGenerator                                 │
│ • NotificationManager (Observer)                │
└─────────────────────────────────────────────────┘
```

**Design Patterns to Use**:
1. **Singleton** - LinkedInSystem (single system instance)
2. **Factory** - PostFactory (create Text/Image/Video/Article posts)
3. **Strategy** - JobMatchingStrategy (Skill/Location/Experience)
4. **Observer** - Event notifications (Feed/Connection/Job/Message)
5. **State** - ConnectionState (Pending/Accepted/Rejected transitions)

**Initial Code Structure**:
```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from datetime import datetime
import threading
import math

# Enumerations (Lines 1-50)
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

# Supporting classes (Lines 50-150)
class Skill:
    def __init__(self, skill_id: str, name: str, category: str):
        self.skill_id = skill_id
        self.name = name
        self.category = category
        self.endorsements = 0

class Experience:
    def __init__(self, company: str, title: str, start_date: datetime):
        self.company = company
        self.title = title
        self.start_date = start_date
        self.end_date = None
        self.is_current = True

class Location:
    def __init__(self, city: str, country: str, lat: float, lon: float):
        self.city = city
        self.country = country
        self.latitude = lat
        self.longitude = lon
    
    def distance_to(self, other: 'Location') -> float:
        # Haversine formula
        lat_diff = abs(self.latitude - other.latitude)
        lon_diff = abs(self.longitude - other.longitude)
        return math.sqrt(lat_diff**2 + lon_diff**2) * 111
```

**Expected Output**: Whiteboard diagram + 150 lines of setup code

**Time Check**: Should be at 15-minute mark with enums and supporting classes done

---

### Phase 2: Core Entities Implementation (15-40 minutes)
**Goal**: Implement all 6 main entities with complete functionality

**2A: User Entity (Lines 150-250)**
```python
class User:
    """Professional user profile"""
    def __init__(self, user_id: str, name: str, email: str, headline: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.headline = headline
        self.summary = ""
        self.location = None
        
        # Professional info
        self.skills: List[Skill] = []
        self.experiences: List[Experience] = []
        self.education: List[Education] = []
        
        # Network
        self.connections: Set[str] = set()
        self.pending_sent: Set[str] = set()
        self.pending_received: Set[str] = set()
        
        # Activity
        self.posts: List[str] = []
        self.job_applications: List[str] = []
        
        self.created_at = datetime.now()
    
    def add_skill(self, skill: Skill):
        if skill not in self.skills:
            self.skills.append(skill)
            return True
        return False
    
    def get_total_experience_years(self) -> float:
        return sum(exp.get_duration_years() for exp in self.experiences)
    
    def has_skill(self, skill_name: str) -> bool:
        return any(s.name.lower() == skill_name.lower() for s in self.skills)
    
    def get_common_skills(self, other: 'User') -> List[Skill]:
        return [s for s in self.skills if s in other.skills]
```

**2B: Connection Entity with State Pattern (Lines 250-350)**
```python
# State Pattern for Connection lifecycle
class ConnectionState(ABC):
    @abstractmethod
    def accept(self, connection: 'Connection'):
        pass
    
    @abstractmethod
    def reject(self, connection: 'Connection'):
        pass

class PendingState(ConnectionState):
    def accept(self, connection: 'Connection'):
        connection.status = ConnectionStatus.ACCEPTED
        connection.state = AcceptedState()
        connection.updated_at = datetime.now()
        return True
    
    def reject(self, connection: 'Connection'):
        connection.status = ConnectionStatus.REJECTED
        connection.state = RejectedState()
        return True

class AcceptedState(ConnectionState):
    def accept(self, connection: 'Connection'):
        return False  # Already accepted
    
    def reject(self, connection: 'Connection'):
        return False  # Cannot reject after acceptance

class Connection:
    """Connection between two users"""
    def __init__(self, connection_id: str, from_user_id: str, 
                 to_user_id: str, message: str = ""):
        self.connection_id = connection_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.message = message
        self.status = ConnectionStatus.PENDING
        self.state = PendingState()  # State pattern
        self.created_at = datetime.now()
    
    def accept(self) -> bool:
        return self.state.accept(self)
    
    def reject(self) -> bool:
        return self.state.reject(self)
```

**2C: Post Entity with Factory Pattern (Lines 350-500)**
```python
# Factory Pattern for different post types
class Post(ABC):
    def __init__(self, post_id: str, author_id: str, content: str, 
                 visibility: Visibility):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.visibility = visibility
        self.likes: List[str] = []
        self.comments: List[Comment] = []
        self.shares: List[str] = []
        self.created_at = datetime.now()
    
    def add_like(self, user_id: str) -> bool:
        if user_id not in self.likes:
            self.likes.append(user_id)
            return True
        return False
    
    def get_engagement_score(self) -> float:
        # Weighted engagement: likes=1, comments=3, shares=5
        return len(self.likes) + 3*len(self.comments) + 5*len(self.shares)
    
    @abstractmethod
    def get_type(self) -> PostType:
        pass

class TextPost(Post):
    def get_type(self) -> PostType:
        return PostType.TEXT

class ImagePost(Post):
    def __init__(self, post_id: str, author_id: str, content: str, 
                 visibility: Visibility, image_urls: List[str]):
        super().__init__(post_id, author_id, content, visibility)
        self.image_urls = image_urls
    
    def get_type(self) -> PostType:
        return PostType.IMAGE

class PostFactory:
    """Factory for creating posts"""
    _post_counter = 0
    
    @staticmethod
    def create_post(post_type: PostType, author_id: str, content: str,
                   visibility: Visibility = Visibility.PUBLIC, **kwargs) -> Post:
        PostFactory._post_counter += 1
        post_id = f"POST_{PostFactory._post_counter:06d}"
        
        if post_type == PostType.TEXT:
            return TextPost(post_id, author_id, content, visibility)
        elif post_type == PostType.IMAGE:
            return ImagePost(post_id, author_id, content, visibility, 
                           kwargs.get('image_urls', []))
        # ... other types
```

**2D: Job Entity (Lines 500-600)**
```python
class Job:
    def __init__(self, job_id: str, company_id: str, title: str, 
                 description: str, location: Location, job_type: JobType):
        self.job_id = job_id
        self.company_id = company_id
        self.title = title
        self.description = description
        self.location = location
        self.job_type = job_type
        self.required_skills: List[str] = []
        self.experience_years = 0
        self.salary_range = None
        self.applications: List[str] = []
        self.status = JobStatus.OPEN
        self.created_at = datetime.now()
    
    def add_application(self, application_id: str):
        if self.status == JobStatus.OPEN:
            self.applications.append(application_id)
            return True
        return False

class JobApplication:
    def __init__(self, application_id: str, job_id: str, 
                 user_id: str, resume_url: str):
        self.application_id = application_id
        self.job_id = job_id
        self.user_id = user_id
        self.resume_url = resume_url
        self.status = ApplicationStatus.SUBMITTED
        self.applied_at = datetime.now()
```

**Line Count at Phase 2 End**: ~600 lines
**Time Check**: Should be at 35-40 minute mark

---

### Phase 3: Design Patterns & Algorithms (40-60 minutes)
**Goal**: Implement Strategy, Observer patterns and core algorithms

**3A: Strategy Pattern - Job Matching (Lines 600-750)**
```python
class JobMatchingStrategy(ABC):
    """Strategy pattern for different matching algorithms"""
    @abstractmethod
    def calculate_match_score(self, job: Job, user: User) -> float:
        pass

class SkillBasedMatcher(JobMatchingStrategy):
    """Match based on skill overlap"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        if not job.required_skills:
            return 50.0
        
        user_skills = {s.name.lower() for s in user.skills}
        required = {s.lower() for s in job.required_skills}
        matched = user_skills.intersection(required)
        
        match_pct = (len(matched) / len(required)) * 100
        return min(100.0, match_pct)

class LocationBasedMatcher(JobMatchingStrategy):
    """Match based on location proximity"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        if not user.location or not job.location:
            return 50.0
        
        distance = user.location.distance_to(job.location)
        
        if distance < 25:    # Within 25 km
            return 100.0
        elif distance < 50:  # Within 50 km
            return 80.0
        elif distance < 100: # Within 100 km
            return 60.0
        else:
            return 30.0

class ExperienceBasedMatcher(JobMatchingStrategy):
    """Match based on years of experience"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        user_years = user.get_total_experience_years()
        required_years = job.experience_years
        diff = abs(user_years - required_years)
        
        if diff == 0:
            return 100.0
        elif diff <= 1:
            return 90.0
        elif diff <= 2:
            return 75.0
        else:
            return max(30.0, 100 - (diff * 10))

class HybridMatcher(JobMatchingStrategy):
    """Combines multiple matchers with weights"""
    def __init__(self):
        self.skill_matcher = SkillBasedMatcher()
        self.location_matcher = LocationBasedMatcher()
        self.experience_matcher = ExperienceBasedMatcher()
    
    def calculate_match_score(self, job: Job, user: User) -> float:
        skill_score = self.skill_matcher.calculate_match_score(job, user)
        location_score = self.location_matcher.calculate_match_score(job, user)
        experience_score = self.experience_matcher.calculate_match_score(job, user)
        
        # Weighted: skills 50%, location 30%, experience 20%
        final = (skill_score*0.5 + location_score*0.3 + experience_score*0.2)
        return round(final, 1)
```

**3B: Observer Pattern - Notifications (Lines 750-850)**
```python
class LinkedInObserver(ABC):
    """Observer interface for events"""
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass

class FeedNotifier(LinkedInObserver):
    """Notifies about feed updates"""
    def update(self, event: str, data: Dict):
        if event == "post_created":
            print(f"📝 {data['author']} created: {data['content'][:50]}...")
        elif event == "post_liked":
            print(f"👍 {data['liker']} liked post")

class ConnectionNotifier(LinkedInObserver):
    """Notifies about connections"""
    def update(self, event: str, data: Dict):
        if event == "connection_requested":
            print(f"🤝 {data['from_user']} → {data['to_user']}")
        elif event == "connection_accepted":
            print(f"✅ Connection accepted")

class JobNotifier(LinkedInObserver):
    """Notifies about jobs"""
    def update(self, event: str, data: Dict):
        if event == "job_posted":
            print(f"💼 {data['company']}: {data['title']}")
        elif event == "job_match":
            print(f"🎯 Match: {data['title']} ({data['score']}%)")
```

**3C: Feed Generation Algorithm (Lines 850-900)**
```python
def generate_feed(self, user_id: str, limit: int = 20) -> List[Post]:
    """Generate personalized feed with ranking algorithm"""
    user = self.users.get(user_id)
    if not user:
        return []
    
    feed_posts = []
    for post in self.posts.values():
        # Filter by visibility
        if post.visibility == Visibility.PUBLIC or \
           post.author_id in user.connections:
            feed_posts.append(post)
    
    # Ranking algorithm: engagement × recency × connection_strength
    def feed_score(post: Post) -> float:
        engagement = post.get_engagement_score()
        hours_ago = (datetime.now() - post.created_at).total_seconds() / 3600
        recency_factor = math.exp(-hours_ago / 24)  # 24-hour decay
        
        # Connection strength
        connection_strength = 1.0 if post.author_id in user.connections else 0.3
        
        return engagement * recency_factor * connection_strength
    
    feed_posts.sort(key=feed_score, reverse=True)
    return feed_posts[:limit]
```

**Line Count at Phase 3 End**: ~900 lines
**Time Check**: Should be at 55-60 minute mark

---

### Phase 4: Singleton System Integration (60-70 minutes)
**Goal**: Integrate everything into thread-safe Singleton system

**Complete LinkedInSystem (Lines 900-1100)**
```python
class LinkedInSystem:
    """Singleton controller (Thread-safe)"""
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
            # Storage
            self.users: Dict[str, User] = {}
            self.connections: Dict[str, Connection] = {}
            self.posts: Dict[str, Post] = {}
            self.jobs: Dict[str, Job] = {}
            self.messages: Dict[str, Message] = {}
            
            # Observers
            self.observers: List[LinkedInObserver] = []
            
            # Strategy
            self.job_matcher: JobMatchingStrategy = HybridMatcher()
            
            self.lock = threading.Lock()
            self.initialized = True
    
    def add_observer(self, observer: LinkedInObserver):
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: Dict):
        for observer in self.observers:
            observer.update(event, data)
    
    # User Management
    def register_user(self, user: User):
        with self.lock:
            if user.user_id in self.users:
                return False
            self.users[user.user_id] = user
            return True
    
    # Connection Management
    def send_connection_request(self, from_id: str, to_id: str, 
                               message: str = "") -> Optional[Connection]:
        with self.lock:
            if from_id not in self.users or to_id not in self.users:
                return None
            
            connection = Connection(f"CONN_{len(self.connections)}", 
                                  from_id, to_id, message)
            self.connections[connection.connection_id] = connection
            
            self.users[from_id].pending_sent.add(to_id)
            self.users[to_id].pending_received.add(from_id)
            
            self._notify_observers("connection_requested", {
                'from_user': self.users[from_id].name,
                'to_user': self.users[to_id].name
            })
            
            return connection
    
    def accept_connection(self, connection_id: str) -> bool:
        connection = self.connections.get(connection_id)
        if connection and connection.accept():
            # Update both users
            from_user = self.users[connection.from_user_id]
            to_user = self.users[connection.to_user_id]
            
            from_user.connections.add(connection.to_user_id)
            to_user.connections.add(connection.from_user_id)
            
            self._notify_observers("connection_accepted", {
                'from_user': from_user.name,
                'to_user': to_user.name
            })
            return True
        return False
    
    # Post Management
    def create_post(self, post: Post) -> bool:
        with self.lock:
            author = self.users.get(post.author_id)
            if not author:
                return False
            
            self.posts[post.post_id] = post
            author.posts.append(post.post_id)
            
            self._notify_observers("post_created", {
                'author': author.name,
                'content': post.content
            })
            return True
    
    # Job Management
    def match_jobs_for_user(self, user_id: str, limit: int = 10) -> List[tuple]:
        user = self.users.get(user_id)
        if not user:
            return []
        
        matches = []
        for job in self.jobs.values():
            if job.status == JobStatus.OPEN:
                score = self.job_matcher.calculate_match_score(job, user)
                matches.append((job, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    # Connection Recommendations
    def recommend_connections(self, user_id: str, limit: int = 5) -> List[tuple]:
        user = self.users.get(user_id)
        if not user:
            return []
        
        scores = {}
        for candidate_id, candidate in self.users.items():
            if candidate_id == user_id or candidate_id in user.connections:
                continue
            
            score = 0
            
            # Mutual connections
            mutual = len(user.connections.intersection(candidate.connections))
            score += mutual * 10
            
            # Common skills
            common_skills = len(user.get_common_skills(candidate))
            score += common_skills * 5
            
            # Same company
            if user.experiences and candidate.experiences:
                user_current = next((e for e in user.experiences if e.is_current), None)
                cand_current = next((e for e in candidate.experiences if e.is_current), None)
                if user_current and cand_current and \
                   user_current.company == cand_current.company:
                    score += 15
            
            scores[candidate_id] = score
        
        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.users[uid], score) for uid, score in sorted_candidates[:limit]]
```

**Line Count at Phase 4 End**: ~1100 lines
**Time Check**: Should be at 68-70 minute mark

---

### Phase 5: Demo Scenarios & Testing (70-75 minutes)
**Goal**: Demonstrate working system with 5 comprehensive scenarios

**Demo Code (Lines 1100-1226)**
```python
def demo1_user_profile_management():
    """Demo 1: Profile creation and management"""
    print("="*70)
    print("DEMO 1: User Profile Management")
    print("="*70)
    
    system = LinkedInSystem()
    
    # Create users
    alice = User("U001", "Alice Johnson", "alice@email.com", 
                "Senior Software Engineer")
    alice.location = Location("San Francisco", "USA", 37.77, -122.41)
    alice.add_skill(Skill("S1", "Python", "Programming"))
    alice.add_skill(Skill("S2", "System Design", "Architecture"))
    alice.add_experience(Experience("TechCorp", "Senior Engineer", 
                                   datetime(2020, 1, 1)))
    
    system.register_user(alice)
    
    print(f"✓ Created user: {alice}")
    print(f"  Skills: {[s.name for s in alice.skills]}")
    print(f"  Experience: {alice.get_total_experience_years():.1f} years")

def demo2_connection_system():
    """Demo 2: Connection requests with State pattern"""
    print("\nDEMO 2: Connection System")
    system = LinkedInSystem()
    
    conn = system.send_connection_request("U001", "U002", "Let's connect!")
    print(f"✓ Connection request: {conn.status.value}")
    
    system.accept_connection(conn.connection_id)
    print(f"✓ After acceptance: {conn.status.value}")

def demo3_job_matching():
    """Demo 3: Job matching with Strategy pattern"""
    print("\nDEMO 3: Job Matching (Strategy Pattern)")
    system = LinkedInSystem()
    
    # Test different matchers
    skill_matcher = SkillBasedMatcher()
    score = skill_matcher.calculate_match_score(job, user)
    print(f"✓ Skill-based match: {score:.1f}%")
    
    # Find matches
    matches = system.match_jobs_for_user("U001", limit=5)
    for job, score in matches:
        print(f"  → {job.title}: {score:.1f}% match")

def demo4_feed_generation():
    """Demo 4: Post creation and feed"""
    print("\nDEMO 4: Feed & Posts (Factory + Observer)")
    system = LinkedInSystem()
    system.add_observer(FeedNotifier())
    
    # Create posts with Factory
    text_post = PostFactory.create_post(PostType.TEXT, "U001",
                                       "Excited about new project!")
    system.create_post(text_post)
    
    # Generate feed
    feed = system.generate_feed("U002", limit=10)
    print(f"✓ Generated feed with {len(feed)} posts")

def demo5_messaging():
    """Demo 5: Messaging system"""
    print("\nDEMO 5: Messaging")
    system = LinkedInSystem()
    system.add_observer(MessageNotifier())
    
    msg = system.send_message("U001", "U002", "Hi Bob!")
    print(f"✓ Message sent: {msg.message_id}")

if __name__ == "__main__":
    print("LINKEDIN SYSTEM - COMPLETE DEMONSTRATION\n")
    
    demo1_user_profile_management()
    demo2_connection_system()
    demo3_job_matching()
    demo4_feed_generation()
    demo5_messaging()
    
    print("\n✅ ALL DEMOS COMPLETED")
```

**Final Line Count**: ~1226 lines
**Time Check**: Finish at 75 minutes

---

## Critical Implementation Checklist

### Must-Have Features (In Order)
1. ✅ **Enumerations** (ConnectionStatus, PostType, JobType, Visibility)
2. ✅ **Supporting Classes** (Skill, Experience, Location)
3. ✅ **User Entity** (profiles, skills, connections)
4. ✅ **Connection + State Pattern** (Pending → Accepted/Rejected)
5. ✅ **Post + Factory Pattern** (Text/Image/Video/Article creation)
6. ✅ **Job Entity** (postings, applications)
7. ✅ **Strategy Pattern** (SkillBasedMatcher, LocationBasedMatcher, ExperienceBasedMatcher, HybridMatcher)
8. ✅ **Observer Pattern** (FeedNotifier, ConnectionNotifier, JobNotifier)
9. ✅ **Feed Algorithm** (engagement × recency × connection strength)
10. ✅ **Singleton System** (LinkedInSystem with thread-safety)
11. ✅ **Connection Recommendations** (mutual connections + common skills)
12. ✅ **5 Demo Scenarios** (Profile, Connection, Jobs, Feed, Messaging)

---

## Key Points to Remember

### Design Patterns
- **Singleton**: Ensure only one instance of system
- **Strategy**: Different algorithms for same operation
- **Observer**: Notify multiple listeners of changes
- **Factory**: Encapsulate object creation
- **State**: Represent state transitions

### SOLID Principles
- **Single Responsibility**: Each class one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable
- **Interface Segregation**: Depend on specific interfaces
- **Dependency Inversion**: Depend on abstractions

### Common Pitfalls
- ❌ Not using Singleton - leads to multiple instances
- ❌ Tight coupling - hard to extend
- ❌ Not using abstractions - not flexible
- ❌ No error handling - crashes on edge cases
- ✅ Always use design patterns
- ✅ Keep classes focused
- ✅ Use abstractions and interfaces

## Interview Tips

1. **Talk through your design** - Explain patterns as you implement
2. **Ask clarifying questions** - "Should we support...?"
3. **Handle edge cases** - Show you think about errors
4. **Optimize incrementally** - Start simple, then optimize
5. **Use design patterns** - Shows you know when to apply them
6. **Write clean code** - Good naming and structure
7. **Test as you go** - Run demos after each phase
8. **Discuss trade-offs** - Why you chose this approach

## Success Criteria

✅ All core entities implemented
✅ Design patterns clearly used
✅ At least 3 demo scenarios work
✅ Code is clean and readable
✅ Error handling present
✅ Can explain design decisions
✅ SOLID principles applied
✅ 75 minutes used efficiently
# LinkedIn System - Extended Guide

## Key Algorithms & Their Implementation

### 1. Feed Ranking Algorithm
```python
def calculate_feed_score(post: Post, user: User) -> float:
    """
    Score = Engagement × Recency × Connection_Strength
    
    Engagement: likes + 3×comments + 5×shares
    Recency: exp(-hours_ago/24) for 24-hour decay
    Connection: 1.0 for connections, 0.3 for public
    """
    engagement = len(post.likes) + 3*len(post.comments) + 5*len(post.shares)
    hours_ago = (now - post.created_at).total_seconds() / 3600
    recency = math.exp(-hours_ago / 24)
    connection = 1.0 if post.author_id in user.connections else 0.3
    
    return engagement * recency * connection
```

**Complexity**: O(n log n) for n posts (sorting dominates)

### 2. Connection Recommendation Algorithm
```python
def recommend_connections(user: User) -> List[tuple]:
    """
    Score = 10×mutual_connections + 5×common_skills + 15×same_company
    """
    for candidate in all_users:
        score = 0
        
        # Mutual connections (strongest signal)
        mutual = len(user.connections ∩ candidate.connections)
        score += mutual * 10
        
        # Common skills
        common_skills = len(user.skills ∩ candidate.skills)
        score += common_skills * 5
        
        # Same current company (very strong signal)
        if same_company(user, candidate):
            score += 15
        
        recommendations.append((candidate, score))
    
    return sorted(recommendations, reverse=True)[:limit]
```

**Complexity**: O(n×m) where n=users, m=avg_connections

### 3. Job Matching with Hybrid Strategy
```python
def hybrid_match(job: Job, user: User) -> float:
    """
    Combined score: 50% skills + 30% location + 20% experience
    """
    skill_score = calculate_skill_match(job, user)
    location_score = calculate_location_match(job, user)
    experience_score = calculate_experience_match(job, user)
    
    return 0.5*skill_score + 0.3*location_score + 0.2*experience_score
```

**Complexity**: O(1) per job-user pair

### 4. Connection Degrees (BFS)
```python
def get_connection_degree(user1: User, user2: User) -> int:
    """
    BFS to find shortest path in connection graph
    Returns 1 for direct, 2 for 2nd degree, etc.
    """
    if user2.id in user1.connections:
        return 1
    
    visited = {user1.id}
    queue = [(conn_id, 2) for conn_id in user1.connections]
    
    while queue:
        current_id, degree = queue.pop(0)
        if current_id == user2.id:
            return degree
        
        if current_id not in visited:
            visited.add(current_id)
            current = get_user(current_id)
            for next_id in current.connections:
                if next_id not in visited:
                    queue.append((next_id, degree + 1))
    
    return -1  # Not connected
```

**Complexity**: O(V + E) where V=users, E=connections

---

## Design Pattern Deep Dive

### 1. Singleton Pattern - LinkedInSystem
**Why**: Ensure single source of truth for all data
```python
class LinkedInSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Thread-safe
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefits**: 
- Single system instance
- Thread-safe with double-checked locking
- Global access point

### 2. Factory Pattern - PostFactory
**Why**: Encapsulate post type creation logic
```python
class PostFactory:
    @staticmethod
    def create_post(type: PostType, **kwargs) -> Post:
        if type == PostType.TEXT:
            return TextPost(...)
        elif type == PostType.IMAGE:
            return ImagePost(..., image_urls)
        # ...
```

**Benefits**:
- Easy to add new post types
- Client doesn't know concrete classes
- Centralized creation logic

### 3. Strategy Pattern - JobMatchingStrategy
**Why**: Swap matching algorithms at runtime
```python
class JobMatchingStrategy(ABC):
    @abstractmethod
    def calculate_match_score(job, user) -> float:
        pass

# Can switch: system.set_job_matcher(SkillBasedMatcher())
```

**Benefits**:
- Algorithm independence
- Runtime flexibility
- Easy A/B testing

### 4. Observer Pattern - Event Notifications
**Why**: Decouple event producers from consumers
```python
class LinkedInObserver(ABC):
    @abstractmethod
    def update(event: str, data: Dict):
        pass

# system.add_observer(FeedNotifier())
# system._notify_observers("post_created", {...})
```

**Benefits**:
- Loose coupling
- Multiple subscribers
- Easy to add new observers

### 5. State Pattern - Connection Lifecycle
**Why**: Manage state transitions cleanly
```python
class ConnectionState(ABC):
    @abstractmethod
    def accept(connection): pass
    
    @abstractmethod
    def reject(connection): pass

# States: Pending → Accepted/Rejected
# Each state controls valid transitions
```

**Benefits**:
- Clear state transitions
- Prevents invalid operations
- Encapsulated state behavior

---

## SOLID Principles Application

### Single Responsibility Principle (SRP)
```python
# ✅ Good: Each class has one responsibility
class User:           # Manages user profile
class Connection:     # Manages connection state
class PostFactory:    # Creates posts
class FeedNotifier:   # Notifies about feed events

# ❌ Bad: God class doing everything
class LinkedInUser:
    def create_post(self): pass
    def send_connection(self): pass
    def match_jobs(self): pass
    def generate_feed(self): pass
```

### Open/Closed Principle (OCP)
```python
# ✅ Good: Open for extension (new matchers), closed for modification
class JobMatchingStrategy(ABC):
    @abstractmethod
    def calculate_match_score(job, user): pass

class NewCustomMatcher(JobMatchingStrategy):  # Extend without modifying
    def calculate_match_score(job, user):
        # New algorithm
        pass

# ❌ Bad: Must modify existing code to add new matching
def match_job(job, user, match_type):
    if match_type == "skill":
        # ...
    elif match_type == "location":
        # ...
    # Need to modify this function for new types
```

### Liskov Substitution Principle (LSP)
```python
# ✅ Good: All Post subtypes can replace Post
post: Post = TextPost(...)
post: Post = ImagePost(...)
post: Post = VideoPost(...)
# All work the same way: add_like(), add_comment(), etc.

# ❌ Bad: ImagePost violates contract
class ImagePost(Post):
    def add_like(self, user_id):
        raise NotImplementedError("Images can't be liked")
```

### Interface Segregation Principle (ISP)
```python
# ✅ Good: Specific interfaces
class JobMatchingStrategy(ABC):
    @abstractmethod
    def calculate_match_score(job, user): pass

class LinkedInObserver(ABC):
    @abstractmethod
    def update(event, data): pass

# ❌ Bad: Fat interface
class AllInOne(ABC):
    @abstractmethod
    def calculate_match_score(job, user): pass
    @abstractmethod
    def update(event, data): pass
    @abstractmethod
    def generate_feed(user): pass
    # Forces implementers to implement everything
```

### Dependency Inversion Principle (DIP)
```python
# ✅ Good: Depend on abstraction (JobMatchingStrategy)
class LinkedInSystem:
    def __init__(self):
        self.job_matcher: JobMatchingStrategy = HybridMatcher()
    
    def set_job_matcher(self, matcher: JobMatchingStrategy):
        self.job_matcher = matcher  # Any strategy works

# ❌ Bad: Depend on concrete class
class LinkedInSystem:
    def __init__(self):
        self.matcher = SkillBasedMatcher()  # Tightly coupled
```

---

## Scalability Considerations

### Database Design
```
Users Table (Sharded by user_id):
├── user_id (PK)
├── name, email, headline
├── location_id (FK)
└── created_at

Connections Table (Sharded by from_user_id):
├── connection_id (PK)
├── from_user_id (FK, Indexed)
├── to_user_id (FK, Indexed)
├── status
└── created_at

Posts Table (Sharded by author_id, Partitioned by date):
├── post_id (PK)
├── author_id (FK, Indexed)
├── content
├── type
└── created_at (Partition key)

Jobs Table (Sharded by company_id):
├── job_id (PK)
├── company_id (FK, Indexed)
├── location_id (FK, Indexed)
└── required_skills (JSON)
```

### Caching Strategy
```python
# Redis for hot data
- User profiles: TTL 1 hour
- Feed cache: TTL 15 minutes
- Connection graph: TTL 30 minutes
- Job matches: TTL 1 hour

# Cache invalidation
- User update → invalidate user_profile:{user_id}
- New post → invalidate feed:{user_id} for all connections
- Connection accept → invalidate connection_graph:{user_id}
```

### Architecture
```
                     ┌─────────────┐
                     │ Load Balancer│
                     └──────┬──────┘
              ┌─────────────┼─────────────┐
              │             │             │
         ┌────▼───┐    ┌────▼───┐   ┌────▼───┐
         │ API    │    │ API    │   │ API    │
         │ Server │    │ Server │   │ Server │
         └────┬───┘    └────┬───┘   └────┬───┘
              │             │             │
         ┌────▼─────────────▼─────────────▼────┐
         │         Redis Cache Cluster          │
         └──────────────────┬───────────────────┘
                            │
         ┌──────────────────▼───────────────────┐
         │      Database Shards (Postgres)      │
         ├──────────────────────────────────────┤
         │ Shard 1  │ Shard 2  │ Shard 3        │
         │ users    │ users    │ users          │
         │ A-F      │ G-M      │ N-Z            │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │      Graph DB (Neo4j) for            │
         │      Connection Network              │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │      Message Queue (Kafka)           │
         │      - Feed updates                  │
         │      - Notifications                 │
         │      - Job matches                   │
         └──────────────────────────────────────┘
```

---

## Common Interview Questions & Answers

### Q1: How would you handle the feed at scale?
**A**: Feed generation is expensive, so we'd use:
1. **Pre-computed feeds**: Background jobs generate feeds for active users
2. **Redis cache**: Cache top 100 posts per user (TTL 15 min)
3. **Fanout on write**: When user posts, push to all connections' feeds
4. **Hybrid approach**: Pre-compute for active users, compute on-demand for inactive
5. **Pagination**: Return feed in chunks (20-50 posts)

### Q2: How do you prevent N+1 queries in connection recommendations?
**A**: 
1. **Batch loading**: Load all user data in one query
2. **Graph database**: Use Neo4j for connection traversal
3. **Materialized views**: Pre-compute mutual connections
4. **Caching**: Cache connection graphs in Redis
5. **Limit depth**: Only search up to 3rd degree connections

### Q3: How would you implement real-time notifications?
**A**:
1. **WebSockets**: Persistent connection for real-time updates
2. **Message queue**: Kafka for event streaming
3. **Observer pattern**: Decouple event generation from notification
4. **Fan-out service**: Dedicated service to push notifications
5. **Mobile push**: APNs/FCM for mobile notifications

### Q4: What's your strategy for job matching at scale?
**A**:
1. **Inverted index**: Skills → Job IDs for fast lookup
2. **Elasticsearch**: Full-text search with scoring
3. **Background jobs**: Pre-compute matches for active job seekers
4. **Strategy pattern**: Different algorithms for different user segments
5. **A/B testing**: Test different matching strategies

### Q5: How do you handle privacy in connections?
**A**:
1. **Visibility enum**: PUBLIC, CONNECTIONS, PRIVATE
2. **Access control**: Check relationship before showing data
3. **Filtered queries**: Only return visible posts in feed
4. **Connection degrees**: Limit data visibility by connection depth
5. **Privacy settings**: User-configurable privacy controls

### Q6: Explain your State pattern for connections
**A**:
- **States**: Pending, Accepted, Rejected, Withdrawn
- **Transitions**: 
  - Pending → Accepted (accept())
  - Pending → Rejected (reject())
  - Pending → Withdrawn (withdraw())
- **Benefits**: 
  - Prevents invalid operations (can't reject after accept)
  - Clear state transitions
  - Easy to add new states

### Q7: Why use Factory pattern for posts?
**A**:
- **Encapsulation**: Hide concrete post type creation
- **Extensibility**: Easy to add new post types (PollPost, LiveVideoPost)
- **Consistency**: Centralized ID generation and validation
- **Type safety**: Return correct Post subtype
- **Single responsibility**: Creation logic separate from business logic

### Q8: How would you implement messaging at scale?
**A**:
1. **Sharding**: Shard conversations by conversation_id
2. **Message queue**: Kafka for reliable delivery
3. **Read receipts**: Async update via event stream
4. **Pagination**: Load messages in chunks
5. **WebSocket**: Real-time message delivery
6. **Storage**: Hot messages in Postgres, cold in S3

### Q9: How do you optimize the feed ranking algorithm?
**A**:
1. **Pre-scoring**: Calculate engagement scores periodically
2. **Incremental updates**: Update scores on each interaction
3. **Time bucketing**: Group posts by time windows
4. **Machine learning**: Use ML model for personalized ranking
5. **Feature store**: Cache user features for fast scoring

### Q10: What metrics would you track?
**A**:
- **User engagement**: DAU, MAU, session time
- **Connection metrics**: Acceptance rate, avg connections per user
- **Feed metrics**: Click-through rate, time spent, engagement rate
- **Job metrics**: Application rate, match quality
- **Performance**: API latency (p50, p95, p99), error rates
- **System health**: Cache hit rate, DB query time, queue lag

---

## Interview Tips & Best Practices

### Communication Strategy
1. **Start with clarification**: "Should we support group messaging?"
2. **Think aloud**: "I'm using State pattern here because..."
3. **Discuss trade-offs**: "Factory adds overhead but improves extensibility"
4. **Ask for feedback**: "Does this approach make sense?"
5. **Explain patterns**: "Observer pattern decouples event producers"

### Time Management
```
Phase 0 (0-5 min):   Requirements clarification
Phase 1 (5-15 min):  Architecture + enums + supporting classes
Phase 2 (15-40 min): Core entities (User, Connection, Post, Job)
Phase 3 (40-60 min): Patterns (Strategy, Observer) + algorithms
Phase 4 (60-70 min): Singleton system integration
Phase 5 (70-75 min): 5 working demos
```

### Code Quality Checklist
- ✅ Type hints: `def match_jobs(user_id: str) -> List[tuple]:`
- ✅ Docstrings: `"""Calculate match score based on skills"""`
- ✅ Meaningful names: `HybridMatcher` not `Matcher3`
- ✅ Single responsibility: Each class does one thing
- ✅ DRY principle: Extract common logic
- ✅ Error handling: Check None, validate input
- ✅ Thread safety: Use locks in Singleton
- ✅ Clean structure: Logical grouping of methods

### Common Pitfalls to Avoid
- ❌ **Skipping patterns**: "I'll just make it work" → Use patterns!
- ❌ **Over-engineering**: Don't implement every feature
- ❌ **No demos**: Code without running demo is risky
- ❌ **Ignoring edge cases**: What if user has no connections?
- ❌ **Poor naming**: `calc()` vs `calculate_match_score()`
- ❌ **Tight coupling**: Depend on abstractions, not concrete classes
- ❌ **Magic numbers**: Use constants: `FEED_LIMIT = 20`
- ❌ **No time check**: Monitor time at each phase

### What Interviewers Look For
1. **Design pattern knowledge**: Can you apply patterns correctly?
2. **SOLID principles**: Is code maintainable and extensible?
3. **Algorithm thinking**: Feed ranking, recommendations
4. **Scalability awareness**: "At scale, we'd cache this"
5. **Code organization**: Clean, readable structure
6. **Communication**: Can you explain your decisions?
7. **Problem-solving**: How do you handle requirements?
8. **Testing mindset**: Demo scenarios show it works

---

## Quick Reference Card

**Line Count Guide**:
- Phase 1 (15 min): 150 lines (enums + supporting classes)
- Phase 2 (40 min): 600 lines (core entities)
- Phase 3 (60 min): 900 lines (patterns + algorithms)
- Phase 4 (70 min): 1100 lines (system integration)
- Phase 5 (75 min): 1226 lines (demos)

**Pattern Quick Reference**:
- **Singleton**: `_instance`, `_lock`, `__new__` with double-check
- **Factory**: `create_post(type, **kwargs)` returns Post subtype
- **Strategy**: Interface + 4 implementations (Skill/Location/Exp/Hybrid)
- **Observer**: `add_observer()`, `_notify_observers(event, data)`
- **State**: `ConnectionState` → Pending/Accepted/Rejected

**Algorithm Complexity**:
- Feed generation: O(n log n)
- Job matching: O(1) per pair
- Connection recommendation: O(n×m)
- BFS connection degree: O(V + E)

**Run Command**: `python3 INTERVIEW_COMPACT.py`

---

**Remember**: The goal is working code demonstrating design patterns, not perfect production code. Focus on correctness, clarity, and communication!

**Good luck! 🚀**


## Detailed Design Reference

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


## Compact Code

```python
#!/usr/bin/env python3
"""
LinkedIn System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action

Design Patterns Demonstrated:
1. Singleton - LinkedInSystem (centralized system control)
2. Factory - PostFactory, ContentFactory (content creation)
3. Strategy - JobMatchingStrategy (Skill/Location/Experience based)
4. Observer - Notifications (Feed updates, connections, messages)
5. State - ConnectionState (Pending/Accepted/Rejected lifecycle)
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import threading
import random
import time
import math


# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class ConnectionStatus(Enum):
    """Connection request status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PostType(Enum):
    """Types of posts"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ARTICLE = "article"
    POLL = "poll"


class Visibility(Enum):
    """Post visibility settings"""
    PUBLIC = "public"
    CONNECTIONS = "connections"
    PRIVATE = "private"


class JobType(Enum):
    """Job types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class JobStatus(Enum):
    """Job posting status"""
    OPEN = "open"
    CLOSED = "closed"
    FILLED = "filled"


class CompanySize(Enum):
    """Company size ranges"""
    SMALL = "1-10"
    MEDIUM = "11-50"
    LARGE = "51-200"
    ENTERPRISE = "201-1000"
    MEGA = "1000+"


class ApplicationStatus(Enum):
    """Job application status"""
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ============================================================================
# SECTION 2: CORE ENTITIES - SUPPORTING CLASSES
# ============================================================================

class Skill:
    """Represents a professional skill"""
    def __init__(self, skill_id: str, name: str, category: str = "General"):
        self.skill_id = skill_id
        self.name = name
        self.category = category
        self.endorsements = 0
    
    def endorse(self):
        """Add endorsement to skill"""
        self.endorsements += 1
    
    def __str__(self):
        return f"{self.name} ({self.endorsements} endorsements)"
    
    def __eq__(self, other):
        return isinstance(other, Skill) and self.skill_id == other.skill_id
    
    def __hash__(self):
        return hash(self.skill_id)


class Experience:
    """Represents work experience"""
    def __init__(self, company: str, title: str, start_date: datetime, end_date: Optional[datetime] = None):
        self.company = company
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.description = ""
        self.is_current = end_date is None
    
    def get_duration_years(self) -> float:
        """Calculate duration in years"""
        end = self.end_date if self.end_date else datetime.now()
        duration = end - self.start_date
        return duration.days / 365.25
    
    def __str__(self):
        status = "Present" if self.is_current else self.end_date.strftime("%Y-%m")
        return f"{self.title} at {self.company} ({self.start_date.strftime('%Y-%m')} - {status})"


class Education:
    """Represents educational background"""
    def __init__(self, school: str, degree: str, field: str, year: int):
        self.school = school
        self.degree = degree
        self.field = field
        self.year = year
    
    def __str__(self):
        return f"{self.degree} in {self.field} from {self.school} ({self.year})"


class Location:
    """Represents geographical location"""
    def __init__(self, city: str, country: str, latitude: float = 0.0, longitude: float = 0.0):
        self.city = city
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance in kilometers (simplified)"""
        # Haversine formula simplified
        lat_diff = abs(self.latitude - other.latitude)
        lon_diff = abs(self.longitude - other.longitude)
        return math.sqrt(lat_diff**2 + lon_diff**2) * 111  # Rough km conversion
    
    def __str__(self):
        return f"{self.city}, {self.country}"


class Comment:
    """Represents a comment on a post"""
    def __init__(self, comment_id: str, author_id: str, content: str):
        self.comment_id = comment_id
        self.author_id = author_id
        self.content = content
        self.created_at = datetime.now()
        self.likes = []
    
    def add_like(self, user_id: str):
        """Like a comment"""
        if user_id not in self.likes:
            self.likes.append(user_id)


# ============================================================================
# SECTION 3: CORE ENTITIES - USER
# ============================================================================

class User:
    """Represents a LinkedIn user profile"""
    def __init__(self, user_id: str, name: str, email: str, headline: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.headline = headline
        self.summary = ""
        self.location = None
        self.profile_image_url = ""
        
        # Professional info
        self.skills: List[Skill] = []
        self.experiences: List[Experience] = []
        self.education: List[Education] = []
        
        # Network
        self.connections: Set[str] = set()  # Connected user IDs
        self.pending_sent: Set[str] = set()  # Sent pending requests
        self.pending_received: Set[str] = set()  # Received pending requests
        self.followers: Set[str] = set()  # Follower user IDs
        self.following: Set[str] = set()  # Following user IDs
        
        # Activity
        self.posts: List[str] = []  # Post IDs
        self.job_applications: List[str] = []  # Application IDs
        
        # Stats
        self.profile_views = 0
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    def add_skill(self, skill: Skill):
        """Add a skill to profile"""
        if skill not in self.skills:
            self.skills.append(skill)
            return True
        return False
    
    def remove_skill(self, skill_id: str):
        """Remove a skill from profile"""
        self.skills = [s for s in self.skills if s.skill_id != skill_id]
    
    def add_experience(self, experience: Experience):
        """Add work experience"""
        self.experiences.append(experience)
        return True
    
    def add_education(self, education: Education):
        """Add education"""
        self.education.append(education)
        return True
    
    def get_total_experience_years(self) -> float:
        """Calculate total years of experience"""
        return sum(exp.get_duration_years() for exp in self.experiences)
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if user has a specific skill"""
        return any(s.name.lower() == skill_name.lower() for s in self.skills)
    
    def get_common_skills(self, other: 'User') -> List[Skill]:
        """Find common skills with another user"""
        return [s for s in self.skills if s in other.skills]
    
    def update_activity(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()
    
    def __str__(self):
        return f"{self.name} - {self.headline} ({len(self.connections)} connections)"


# ============================================================================
# SECTION 4: CONNECTION & STATE PATTERN
# ============================================================================

class ConnectionState(ABC):
    """Abstract state for connection (State Pattern)"""
    @abstractmethod
    def accept(self, connection: 'Connection'):
        pass
    
    @abstractmethod
    def reject(self, connection: 'Connection'):
        pass
    
    @abstractmethod
    def withdraw(self, connection: 'Connection'):
        pass


class PendingState(ConnectionState):
    """Pending connection state"""
    def accept(self, connection: 'Connection'):
        connection.status = ConnectionStatus.ACCEPTED
        connection.state = AcceptedState()
        connection.updated_at = datetime.now()
        return True
    
    def reject(self, connection: 'Connection'):
        connection.status = ConnectionStatus.REJECTED
        connection.state = RejectedState()
        connection.updated_at = datetime.now()
        return True
    
    def withdraw(self, connection: 'Connection'):
        connection.status = ConnectionStatus.WITHDRAWN
        connection.state = WithdrawnState()
        connection.updated_at = datetime.now()
        return True


class AcceptedState(ConnectionState):
    """Accepted connection state"""
    def accept(self, connection: 'Connection'):
        return False  # Already accepted
    
    def reject(self, connection: 'Connection'):
        return False  # Cannot reject after acceptance
    
    def withdraw(self, connection: 'Connection'):
        return False  # Cannot withdraw after acceptance


class RejectedState(ConnectionState):
    """Rejected connection state"""
    def accept(self, connection: 'Connection'):
        return False  # Cannot accept after rejection
    
    def reject(self, connection: 'Connection'):
        return False  # Already rejected
    
    def withdraw(self, connection: 'Connection'):
        return False  # Cannot withdraw after rejection


class WithdrawnState(ConnectionState):
    """Withdrawn connection state"""
    def accept(self, connection: 'Connection'):
        return False
    
    def reject(self, connection: 'Connection'):
        return False
    
    def withdraw(self, connection: 'Connection'):
        return False  # Already withdrawn


class Connection:
    """Represents a connection between two users"""
    def __init__(self, connection_id: str, from_user_id: str, to_user_id: str, message: str = ""):
        self.connection_id = connection_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.message = message
        self.status = ConnectionStatus.PENDING
        self.state = PendingState()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def accept(self) -> bool:
        """Accept connection request"""
        return self.state.accept(self)
    
    def reject(self) -> bool:
        """Reject connection request"""
        return self.state.reject(self)
    
    def withdraw(self) -> bool:
        """Withdraw connection request"""
        return self.state.withdraw(self)
    
    def __str__(self):
        return f"Connection({self.from_user_id} → {self.to_user_id}, {self.status.value})"


# ============================================================================
# SECTION 5: POST ENTITIES & FACTORY PATTERN
# ============================================================================

class Post(ABC):
    """Abstract base class for posts"""
    def __init__(self, post_id: str, author_id: str, content: str, visibility: Visibility):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.visibility = visibility
        self.likes: List[str] = []
        self.comments: List[Comment] = []
        self.shares: List[str] = []
        self.tags: List[str] = []
        self.created_at = datetime.now()
    
    def add_like(self, user_id: str) -> bool:
        """Add a like to the post"""
        if user_id not in self.likes:
            self.likes.append(user_id)
            return True
        return False
    
    def remove_like(self, user_id: str) -> bool:
        """Remove a like from the post"""
        if user_id in self.likes:
            self.likes.remove(user_id)
            return True
        return False
    
    def add_comment(self, comment: Comment) -> bool:
        """Add a comment to the post"""
        self.comments.append(comment)
        return True
    
    def share(self, user_id: str) -> bool:
        """Share the post"""
        if user_id not in self.shares:
            self.shares.append(user_id)
            return True
        return False
    
    def get_engagement_score(self) -> float:
        """Calculate engagement score"""
        return len(self.likes) + 3 * len(self.comments) + 5 * len(self.shares)
    
    @abstractmethod
    def get_type(self) -> PostType:
        pass


class TextPost(Post):
    """Text-only post"""
    def get_type(self) -> PostType:
        return PostType.TEXT


class ImagePost(Post):
    """Post with images"""
    def __init__(self, post_id: str, author_id: str, content: str, visibility: Visibility, image_urls: List[str]):
        super().__init__(post_id, author_id, content, visibility)
        self.image_urls = image_urls
    
    def get_type(self) -> PostType:
        return PostType.IMAGE


class VideoPost(Post):
    """Post with video"""
    def __init__(self, post_id: str, author_id: str, content: str, visibility: Visibility, video_url: str):
        super().__init__(post_id, author_id, content, visibility)
        self.video_url = video_url
        self.duration_seconds = 0
    
    def get_type(self) -> PostType:
        return PostType.VIDEO


class ArticlePost(Post):
    """Long-form article post"""
    def __init__(self, post_id: str, author_id: str, content: str, visibility: Visibility, title: str):
        super().__init__(post_id, author_id, content, visibility)
        self.title = title
        self.article_content = ""
    
    def get_type(self) -> PostType:
        return PostType.ARTICLE


class PostFactory:
    """Factory for creating different types of posts (Factory Pattern)"""
    _post_counter = 0
    
    @staticmethod
    def create_post(post_type: PostType, author_id: str, content: str, 
                   visibility: Visibility = Visibility.PUBLIC, **kwargs) -> Post:
        """Create a post based on type"""
        PostFactory._post_counter += 1
        post_id = f"POST_{PostFactory._post_counter:06d}"
        
        if post_type == PostType.TEXT:
            return TextPost(post_id, author_id, content, visibility)
        elif post_type == PostType.IMAGE:
            image_urls = kwargs.get('image_urls', [])
            return ImagePost(post_id, author_id, content, visibility, image_urls)
        elif post_type == PostType.VIDEO:
            video_url = kwargs.get('video_url', '')
            return VideoPost(post_id, author_id, content, visibility, video_url)
        elif post_type == PostType.ARTICLE:
            title = kwargs.get('title', 'Untitled Article')
            return ArticlePost(post_id, author_id, content, visibility, title)
        else:
            return TextPost(post_id, author_id, content, visibility)


# ============================================================================
# SECTION 6: JOB ENTITIES
# ============================================================================

class SalaryRange:
    """Represents salary range"""
    def __init__(self, min_salary: float, max_salary: float, currency: str = "USD"):
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.currency = currency
    
    def __str__(self):
        return f"{self.currency} {self.min_salary:,.0f} - {self.max_salary:,.0f}"


class JobApplication:
    """Represents a job application"""
    def __init__(self, application_id: str, job_id: str, user_id: str, resume_url: str):
        self.application_id = application_id
        self.job_id = job_id
        self.user_id = user_id
        self.resume_url = resume_url
        self.cover_letter = ""
        self.status = ApplicationStatus.SUBMITTED
        self.applied_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_status(self, new_status: ApplicationStatus):
        """Update application status"""
        self.status = new_status
        self.updated_at = datetime.now()


class Job:
    """Represents a job posting"""
    def __init__(self, job_id: str, company_id: str, title: str, description: str, 
                 location: Location, job_type: JobType):
        self.job_id = job_id
        self.company_id = company_id
        self.title = title
        self.description = description
        self.location = location
        self.job_type = job_type
        self.required_skills: List[str] = []
        self.experience_years = 0
        self.salary_range: Optional[SalaryRange] = None
        self.applications: List[str] = []  # Application IDs
        self.status = JobStatus.OPEN
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=30)
    
    def add_application(self, application_id: str):
        """Add job application"""
        if self.status == JobStatus.OPEN:
            self.applications.append(application_id)
            return True
        return False
    
    def close(self):
        """Close job posting"""
        self.status = JobStatus.CLOSED
    
    def mark_filled(self):
        """Mark job as filled"""
        self.status = JobStatus.FILLED


# ============================================================================
# SECTION 7: STRATEGY PATTERN - JOB MATCHING
# ============================================================================

class JobMatchingStrategy(ABC):
    """Abstract strategy for job matching (Strategy Pattern)"""
    @abstractmethod
    def calculate_match_score(self, job: Job, user: User) -> float:
        pass


class SkillBasedMatcher(JobMatchingStrategy):
    """Match based on skills"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        """Calculate match score based on skills"""
        if not job.required_skills:
            return 50.0
        
        user_skill_names = {s.name.lower() for s in user.skills}
        required_skills_lower = {s.lower() for s in job.required_skills}
        
        matched_skills = user_skill_names.intersection(required_skills_lower)
        
        if len(job.required_skills) == 0:
            return 50.0
        
        match_percentage = (len(matched_skills) / len(job.required_skills)) * 100
        return min(100.0, match_percentage)


class LocationBasedMatcher(JobMatchingStrategy):
    """Match based on location proximity"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        """Calculate match score based on location"""
        if not user.location or not job.location:
            return 50.0
        
        distance = user.location.distance_to(job.location)
        
        if distance < 25:  # Within 25 km
            return 100.0
        elif distance < 50:  # Within 50 km
            return 80.0
        elif distance < 100:  # Within 100 km
            return 60.0
        else:
            return 30.0


class ExperienceBasedMatcher(JobMatchingStrategy):
    """Match based on years of experience"""
    def calculate_match_score(self, job: Job, user: User) -> float:
        """Calculate match score based on experience"""
        user_years = user.get_total_experience_years()
        required_years = job.experience_years
        
        diff = abs(user_years - required_years)
        
        if diff == 0:
            return 100.0
        elif diff <= 1:
            return 90.0
        elif diff <= 2:
            return 75.0
        elif diff <= 3:
            return 60.0
        else:
            return max(30.0, 100 - (diff * 10))


class HybridMatcher(JobMatchingStrategy):
    """Combined matcher using multiple strategies"""
    def __init__(self):
        self.skill_matcher = SkillBasedMatcher()
        self.location_matcher = LocationBasedMatcher()
        self.experience_matcher = ExperienceBasedMatcher()
    
    def calculate_match_score(self, job: Job, user: User) -> float:
        """Calculate weighted average of all matchers"""
        skill_score = self.skill_matcher.calculate_match_score(job, user)
        location_score = self.location_matcher.calculate_match_score(job, user)
        experience_score = self.experience_matcher.calculate_match_score(job, user)
        
        # Weighted average: skills 50%, location 30%, experience 20%
        final_score = (skill_score * 0.5 + location_score * 0.3 + experience_score * 0.2)
        return round(final_score, 1)


# ============================================================================
# SECTION 8: COMPANY
# ============================================================================

class Company:
    """Represents a company profile"""
    def __init__(self, company_id: str, name: str, industry: str, size: CompanySize):
        self.company_id = company_id
        self.name = name
        self.industry = industry
        self.size = size
        self.description = ""
        self.website = ""
        self.location: Optional[Location] = None
        self.followers: Set[str] = set()  # User IDs
        self.jobs: List[str] = []  # Job IDs
        self.created_at = datetime.now()
    
    def add_follower(self, user_id: str):
        """Add a follower"""
        self.followers.add(user_id)
    
    def remove_follower(self, user_id: str):
        """Remove a follower"""
        self.followers.discard(user_id)
    
    def post_job(self, job_id: str):
        """Post a new job"""
        self.jobs.append(job_id)


# ============================================================================
# SECTION 9: MESSAGE
# ============================================================================

class Message:
    """Represents a message between users"""
    def __init__(self, message_id: str, conversation_id: str, sender_id: str, 
                 receiver_id: str, content: str):
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.is_read = False
        self.created_at = datetime.now()
        self.read_at: Optional[datetime] = None
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now()
            return True
        return False


class Conversation:
    """Represents a conversation thread"""
    def __init__(self, conversation_id: str, participant_ids: List[str]):
        self.conversation_id = conversation_id
        self.participant_ids = participant_ids
        self.messages: List[str] = []  # Message IDs
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(self, message_id: str):
        """Add message to conversation"""
        self.messages.append(message_id)
        self.updated_at = datetime.now()


# ============================================================================
# SECTION 10: OBSERVER PATTERN - NOTIFICATIONS
# ============================================================================

class LinkedInObserver(ABC):
    """Observer interface for LinkedIn events (Observer Pattern)"""
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass


class FeedNotifier(LinkedInObserver):
    """Notify users about feed updates"""
    def update(self, event: str, data: Dict):
        if event == "post_created":
            print(f"  [FEED] 📝 {data['author']} created a new post: \"{data['content'][:50]}...\"")
        elif event == "post_liked":
            print(f"  [FEED] 👍 {data['liker']} liked {data['author']}'s post")
        elif event == "post_commented":
            print(f"  [FEED] 💬 {data['commenter']} commented on {data['author']}'s post")
        elif event == "post_shared":
            print(f"  [FEED] 🔄 {data['sharer']} shared {data['author']}'s post")


class ConnectionNotifier(LinkedInObserver):
    """Notify users about connection events"""
    def update(self, event: str, data: Dict):
        if event == "connection_requested":
            print(f"  [CONNECTION] 🤝 {data['from_user']} sent connection request to {data['to_user']}")
        elif event == "connection_accepted":
            print(f"  [CONNECTION] ✅ {data['to_user']} accepted {data['from_user']}'s connection request")
        elif event == "connection_rejected":
            print(f"  [CONNECTION] ❌ {data['to_user']} rejected {data['from_user']}'s connection request")


class JobNotifier(LinkedInObserver):
    """Notify users about job events"""
    def update(self, event: str, data: Dict):
        if event == "job_posted":
            print(f"  [JOB] 💼 {data['company']} posted: {data['title']}")
        elif event == "job_applied":
            print(f"  [JOB] 📄 {data['user']} applied for {data['title']}")
        elif event == "job_match":
            print(f"  [JOB] 🎯 Found match: {data['title']} ({data['score']:.0f}% match)")


class MessageNotifier(LinkedInObserver):
    """Notify users about messages"""
    def update(self, event: str, data: Dict):
        if event == "message_sent":
            print(f"  [MESSAGE] ✉️ {data['sender']} → {data['receiver']}: \"{data['content'][:30]}...\"")
        elif event == "message_read":
            print(f"  [MESSAGE] 👁️ {data['receiver']} read message from {data['sender']}")


class ActivityTracker(LinkedInObserver):
    """Track user activities and statistics"""
    def update(self, event: str, data: Dict):
        if event in ["post_created", "connection_requested", "job_applied"]:
            activity_type = event.replace("_", " ").title()
            print(f"  [ACTIVITY] 📊 Activity: {activity_type}")


# ============================================================================
# SECTION 11: SINGLETON - LINKEDIN SYSTEM
# ============================================================================

class LinkedInSystem:
    """Singleton controller for LinkedIn system (Singleton Pattern)"""
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
            # Storage
            self.users: Dict[str, User] = {}
            self.connections: Dict[str, Connection] = {}
            self.posts: Dict[str, Post] = {}
            self.jobs: Dict[str, Job] = {}
            self.companies: Dict[str, Company] = {}
            self.messages: Dict[str, Message] = {}
            self.conversations: Dict[str, Conversation] = {}
            self.applications: Dict[str, JobApplication] = {}
            
            # Observers
            self.observers: List[LinkedInObserver] = []
            
            # Strategy for job matching
            self.job_matcher: JobMatchingStrategy = HybridMatcher()
            
            # Counters
            self.connection_counter = 0
            self.message_counter = 0
            self.conversation_counter = 0
            self.application_counter = 0
            self.job_counter = 0
            self.company_counter = 0
            self.comment_counter = 0
            
            self.lock = threading.Lock()
            self.initialized = True
    
    def add_observer(self, observer: LinkedInObserver):
        """Add event observer"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: Dict):
        """Notify all observers of event"""
        for observer in self.observers:
            observer.update(event, data)
    
    def set_job_matcher(self, matcher: JobMatchingStrategy):
        """Set job matching strategy"""
        self.job_matcher = matcher
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    def register_user(self, user: User):
        """Register a new user"""
        with self.lock:
            if user.user_id in self.users:
                return False
            self.users[user.user_id] = user
            return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def send_connection_request(self, from_user_id: str, to_user_id: str, message: str = "") -> Optional[Connection]:
        """Send connection request"""
        with self.lock:
            if from_user_id not in self.users or to_user_id not in self.users:
                return None
            
            if from_user_id == to_user_id:
                return None
            
            # Check if already connected
            from_user = self.users[from_user_id]
            if to_user_id in from_user.connections:
                return None
            
            # Create connection
            self.connection_counter += 1
            connection_id = f"CONN_{self.connection_counter:06d}"
            connection = Connection(connection_id, from_user_id, to_user_id, message)
            
            self.connections[connection_id] = connection
            from_user.pending_sent.add(to_user_id)
            self.users[to_user_id].pending_received.add(from_user_id)
            
            # Notify
            self._notify_observers("connection_requested", {
                'from_user': from_user.name,
                'to_user': self.users[to_user_id].name,
                'message': message
            })
            
            return connection
    
    def accept_connection(self, connection_id: str) -> bool:
        """Accept connection request"""
        with self.lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            if connection.accept():
                # Update user connections
                from_user = self.users[connection.from_user_id]
                to_user = self.users[connection.to_user_id]
                
                from_user.connections.add(connection.to_user_id)
                to_user.connections.add(connection.from_user_id)
                
                from_user.pending_sent.discard(connection.to_user_id)
                to_user.pending_received.discard(connection.from_user_id)
                
                # Notify
                self._notify_observers("connection_accepted", {
                    'from_user': from_user.name,
                    'to_user': to_user.name
                })
                
                return True
            return False
    
    def reject_connection(self, connection_id: str) -> bool:
        """Reject connection request"""
        with self.lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            if connection.reject():
                # Update pending lists
                from_user = self.users[connection.from_user_id]
                to_user = self.users[connection.to_user_id]
                
                from_user.pending_sent.discard(connection.to_user_id)
                to_user.pending_received.discard(connection.from_user_id)
                
                # Notify
                self._notify_observers("connection_rejected", {
                    'from_user': from_user.name,
                    'to_user': to_user.name
                })
                
                return True
            return False
    
    def get_mutual_connections(self, user1_id: str, user2_id: str) -> List[User]:
        """Get mutual connections between two users"""
        user1 = self.users.get(user1_id)
        user2 = self.users.get(user2_id)
        
        if not user1 or not user2:
            return []
        
        mutual_ids = user1.connections.intersection(user2.connections)
        return [self.users[uid] for uid in mutual_ids]
    
    def recommend_connections(self, user_id: str, limit: int = 5) -> List[tuple]:
        """Recommend connections for a user"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        scores = {}
        
        for candidate_id, candidate in self.users.items():
            if candidate_id == user_id:
                continue
            if candidate_id in user.connections:
                continue
            if candidate_id in user.pending_sent or candidate_id in user.pending_received:
                continue
            
            score = 0
            
            # Mutual connections
            mutual = len(user.connections.intersection(candidate.connections))
            score += mutual * 10
            
            # Common skills
            common_skills = len(user.get_common_skills(candidate))
            score += common_skills * 5
            
            # Same current company
            if user.experiences and candidate.experiences:
                user_current = next((e for e in user.experiences if e.is_current), None)
                candidate_current = next((e for e in candidate.experiences if e.is_current), None)
                if user_current and candidate_current and user_current.company == candidate_current.company:
                    score += 15
            
            scores[candidate_id] = score
        
        # Sort by score and return top N
        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.users[uid], score) for uid, score in sorted_candidates[:limit]]
    
    # ========================================================================
    # POST MANAGEMENT
    # ========================================================================
    
    def create_post(self, post: Post) -> bool:
        """Create a new post"""
        with self.lock:
            author = self.users.get(post.author_id)
            if not author:
                return False
            
            self.posts[post.post_id] = post
            author.posts.append(post.post_id)
            
            # Notify
            self._notify_observers("post_created", {
                'author': author.name,
                'content': post.content,
                'type': post.get_type().value
            })
            
            return True
    
    def like_post(self, post_id: str, user_id: str) -> bool:
        """Like a post"""
        post = self.posts.get(post_id)
        user = self.users.get(user_id)
        
        if not post or not user:
            return False
        
        if post.add_like(user_id):
            author = self.users.get(post.author_id)
            self._notify_observers("post_liked", {
                'liker': user.name,
                'author': author.name if author else 'Unknown'
            })
            return True
        return False
    
    def comment_on_post(self, post_id: str, user_id: str, content: str) -> Optional[Comment]:
        """Add comment to a post"""
        post = self.posts.get(post_id)
        user = self.users.get(user_id)
        
        if not post or not user:
            return None
        
        self.comment_counter += 1
        comment_id = f"COMMENT_{self.comment_counter:06d}"
        comment = Comment(comment_id, user_id, content)
        
        post.add_comment(comment)
        
        author = self.users.get(post.author_id)
        self._notify_observers("post_commented", {
            'commenter': user.name,
            'author': author.name if author else 'Unknown',
            'content': content
        })
        
        return comment
    
    def share_post(self, post_id: str, user_id: str) -> bool:
        """Share a post"""
        post = self.posts.get(post_id)
        user = self.users.get(user_id)
        
        if not post or not user:
            return False
        
        if post.share(user_id):
            author = self.users.get(post.author_id)
            self._notify_observers("post_shared", {
                'sharer': user.name,
                'author': author.name if author else 'Unknown'
            })
            return True
        return False
    
    def generate_feed(self, user_id: str, limit: int = 20) -> List[Post]:
        """Generate personalized feed for user"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        # Get posts from connections
        feed_posts = []
        for post_id, post in self.posts.items():
            # Public posts or posts from connections
            if post.visibility == Visibility.PUBLIC or post.author_id in user.connections:
                feed_posts.append(post)
        
        # Sort by engagement and recency
        def feed_score(post: Post) -> float:
            engagement = post.get_engagement_score()
            hours_ago = (datetime.now() - post.created_at).total_seconds() / 3600
            recency_factor = math.exp(-hours_ago / 24)  # Decay with 24-hour half-life
            
            # Connection strength
            if post.author_id in user.connections:
                connection_strength = 1.0
            else:
                connection_strength = 0.3
            
            return engagement * recency_factor * connection_strength
        
        feed_posts.sort(key=feed_score, reverse=True)
        return feed_posts[:limit]
    
    # ========================================================================
    # JOB MANAGEMENT
    # ========================================================================
    
    def create_company(self, company: Company) -> bool:
        """Create a company profile"""
        with self.lock:
            if company.company_id in self.companies:
                return False
            self.companies[company.company_id] = company
            return True
    
    def post_job(self, job: Job) -> bool:
        """Post a new job"""
        with self.lock:
            company = self.companies.get(job.company_id)
            if not company:
                return False
            
            self.jobs[job.job_id] = job
            company.post_job(job.job_id)
            
            # Notify
            self._notify_observers("job_posted", {
                'company': company.name,
                'title': job.title,
                'location': str(job.location)
            })
            
            return True
    
    def apply_for_job(self, job_id: str, user_id: str, resume_url: str) -> Optional[JobApplication]:
        """Apply for a job"""
        with self.lock:
            job = self.jobs.get(job_id)
            user = self.users.get(user_id)
            
            if not job or not user or job.status != JobStatus.OPEN:
                return None
            
            self.application_counter += 1
            application_id = f"APP_{self.application_counter:06d}"
            application = JobApplication(application_id, job_id, user_id, resume_url)
            
            self.applications[application_id] = application
            job.add_application(application_id)
            user.job_applications.append(application_id)
            
            # Notify
            self._notify_observers("job_applied", {
                'user': user.name,
                'title': job.title
            })
            
            return application
    
    def match_jobs_for_user(self, user_id: str, limit: int = 10) -> List[tuple]:
        """Find matching jobs for a user"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        matches = []
        for job_id, job in self.jobs.items():
            if job.status != JobStatus.OPEN:
                continue
            
            score = self.job_matcher.calculate_match_score(job, user)
            matches.append((job, score))
            
            if score >= 70:  # Only notify for good matches
                self._notify_observers("job_match", {
                    'title': job.title,
                    'score': score
                })
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    # ========================================================================
    # MESSAGING
    # ========================================================================
    
    def send_message(self, sender_id: str, receiver_id: str, content: str) -> Optional[Message]:
        """Send a message"""
        with self.lock:
            sender = self.users.get(sender_id)
            receiver = self.users.get(receiver_id)
            
            if not sender or not receiver:
                return None
            
            # Find or create conversation
            conversation = self._find_or_create_conversation([sender_id, receiver_id])
            
            # Create message
            self.message_counter += 1
            message_id = f"MSG_{self.message_counter:06d}"
            message = Message(message_id, conversation.conversation_id, sender_id, receiver_id, content)
            
            self.messages[message_id] = message
            conversation.add_message(message_id)
            
            # Notify
            self._notify_observers("message_sent", {
                'sender': sender.name,
                'receiver': receiver.name,
                'content': content
            })
            
            return message
    
    def _find_or_create_conversation(self, participant_ids: List[str]) -> Conversation:
        """Find existing conversation or create new one"""
        participant_set = set(participant_ids)
        
        for conv in self.conversations.values():
            if set(conv.participant_ids) == participant_set:
                return conv
        
        # Create new conversation
        self.conversation_counter += 1
        conversation_id = f"CONV_{self.conversation_counter:06d}"
        conversation = Conversation(conversation_id, participant_ids)
        self.conversations[conversation_id] = conversation
        
        return conversation


# ============================================================================
# SECTION 12: DEMO SCENARIOS
# ============================================================================

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def demo1_user_profile_management():
    """Demo 1: User Profile Management"""
    print_section("DEMO 1: User Profile Management")
    
    system = LinkedInSystem()
    
    # Add observers
    system.add_observer(FeedNotifier())
    system.add_observer(ConnectionNotifier())
    system.add_observer(JobNotifier())
    system.add_observer(ActivityTracker())
    
    print("\n1. Creating user profiles...")
    
    # Create users
    alice = User("U001", "Alice Johnson", "alice@email.com", "Senior Software Engineer")
    alice.summary = "Passionate about building scalable systems"
    alice.location = Location("San Francisco", "USA", 37.7749, -122.4194)
    
    bob = User("U002", "Bob Smith", "bob@email.com", "Product Manager")
    bob.location = Location("San Francisco", "USA", 37.7749, -122.4194)
    
    charlie = User("U003", "Charlie Brown", "charlie@email.com", "Data Scientist")
    charlie.location = Location("New York", "USA", 40.7128, -74.0060)
    
    # Register users
    system.register_user(alice)
    system.register_user(bob)
    system.register_user(charlie)
    
    print(f"   ✓ Created {len(system.users)} users")
    
    print("\n2. Adding skills and experience...")
    
    # Add skills
    alice.add_skill(Skill("S1", "Python", "Programming"))
    alice.add_skill(Skill("S2", "Java", "Programming"))
    alice.add_skill(Skill("S3", "System Design", "Architecture"))
    
    bob.add_skill(Skill("S4", "Product Management", "Business"))
    bob.add_skill(Skill("S5", "Agile", "Methodology"))
    
    charlie.add_skill(Skill("S1", "Python", "Programming"))  # Same skill as Alice
    charlie.add_skill(Skill("S6", "Machine Learning", "AI"))
    charlie.add_skill(Skill("S7", "Statistics", "Math"))
    
    # Add experience
    alice.add_experience(Experience("TechCorp", "Senior Engineer", datetime(2020, 1, 1)))
    alice.add_experience(Experience("StartupXYZ", "Software Engineer", datetime(2017, 6, 1), datetime(2019, 12, 31)))
    
    bob.add_experience(Experience("TechCorp", "Product Manager", datetime(2019, 3, 1)))  # Same company as Alice
    
    charlie.add_experience(Experience("DataCo", "Data Scientist", datetime(2018, 1, 1)))
    
    print(f"   ✓ Alice has {len(alice.skills)} skills, {alice.get_total_experience_years():.1f} years experience")
    print(f"   ✓ Bob has {len(bob.skills)} skills, {bob.get_total_experience_years():.1f} years experience")
    print(f"   ✓ Charlie has {len(charlie.skills)} skills, {charlie.get_total_experience_years():.1f} years experience")
    
    # Common skills
    common = alice.get_common_skills(charlie)
    print(f"\n3. Alice and Charlie share {len(common)} common skill(s): {[s.name for s in common]}")


def demo2_connection_system():
    """Demo 2: Connection System with State Pattern"""
    print_section("DEMO 2: Connection System (State Pattern)")
    
    system = LinkedInSystem()
    
    print("\n1. Sending connection requests...")
    
    # Send requests
    conn1 = system.send_connection_request("U001", "U002", "Hi Bob, let's connect!")
    conn2 = system.send_connection_request("U001", "U003", "Hi Charlie!")
    conn3 = system.send_connection_request("U002", "U003", "")
    
    print(f"   ✓ Sent 3 connection requests")
    print(f"   ✓ Connection 1: {conn1}")
    
    print("\n2. Accepting/rejecting connections...")
    
    # Accept connection
    if system.accept_connection(conn1.connection_id):
        print(f"   ✓ Connection accepted: {conn1.status.value}")
    
    # Reject connection
    if system.reject_connection(conn2.connection_id):
        print(f"   ✓ Connection rejected: {conn2.status.value}")
    
    # Accept another
    if system.accept_connection(conn3.connection_id):
        print(f"   ✓ Connection accepted: {conn3.status.value}")
    
    alice = system.get_user("U001")
    bob = system.get_user("U002")
    charlie = system.get_user("U003")
    
    print(f"\n3. Connection counts:")
    print(f"   ✓ Alice: {len(alice.connections)} connections")
    print(f"   ✓ Bob: {len(bob.connections)} connections")
    print(f"   ✓ Charlie: {len(charlie.connections)} connections")
    
    print("\n4. Finding mutual connections...")
    mutual = system.get_mutual_connections("U001", "U003")
    print(f"   ✓ Alice and Charlie have {len(mutual)} mutual connection(s)")
    
    print("\n5. Connection recommendations for Alice...")
    recommendations = system.recommend_connections("U001", limit=3)
    for user, score in recommendations:
        print(f"   → {user.name}: score {score}")


def demo3_job_posting_application():
    """Demo 3: Job Posting & Application with Strategy Pattern"""
    print_section("DEMO 3: Job Posting & Application (Strategy Pattern)")
    
    system = LinkedInSystem()
    
    print("\n1. Creating company...")
    
    company = Company("C001", "TechCorp", "Technology", CompanySize.LARGE)
    company.description = "Leading technology company"
    company.location = Location("San Francisco", "USA", 37.7749, -122.4194)
    system.create_company(company)
    
    print(f"   ✓ Created company: {company.name}")
    
    print("\n2. Posting jobs...")
    
    # Create job
    job1 = Job("J001", "C001", "Senior Python Developer", 
               "Build scalable backend systems", 
               Location("San Francisco", "USA", 37.7749, -122.4194),
               JobType.FULL_TIME)
    job1.required_skills = ["Python", "System Design", "AWS"]
    job1.experience_years = 5
    job1.salary_range = SalaryRange(120000, 180000)
    
    job2 = Job("J002", "C001", "Product Manager",
               "Lead product development",
               Location("San Francisco", "USA", 37.7749, -122.4194),
               JobType.FULL_TIME)
    job2.required_skills = ["Product Management", "Agile"]
    job2.experience_years = 3
    job2.salary_range = SalaryRange(100000, 150000)
    
    system.post_job(job1)
    system.post_job(job2)
    
    print(f"   ✓ Posted 2 jobs")
    
    print("\n3. Testing job matching strategies...")
    
    alice = system.get_user("U001")
    
    # Test different matchers
    skill_matcher = SkillBasedMatcher()
    location_matcher = LocationBasedMatcher()
    experience_matcher = ExperienceBasedMatcher()
    
    skill_score = skill_matcher.calculate_match_score(job1, alice)
    location_score = location_matcher.calculate_match_score(job1, alice)
    experience_score = experience_matcher.calculate_match_score(job1, alice)
    
    print(f"   → Skill-based match: {skill_score:.1f}%")
    print(f"   → Location-based match: {location_score:.1f}%")
    print(f"   → Experience-based match: {experience_score:.1f}%")
    
    print("\n4. Finding job matches for Alice (Hybrid Strategy)...")
    system.set_job_matcher(HybridMatcher())
    matches = system.match_jobs_for_user("U001", limit=5)
    
    for job, score in matches:
        print(f"   → {job.title}: {score:.1f}% match")
    
    print("\n5. Applying for jobs...")
    app = system.apply_for_job("J001", "U001", "https://resume.com/alice.pdf")
    if app:
        print(f"   ✓ Application submitted: {app.application_id}")
        print(f"   ✓ Status: {app.status.value}")


def demo4_feed_interactions():
    """Demo 4: Feed & Post Interactions with Factory & Observer"""
    print_section("DEMO 4: Feed & Post Interactions (Factory & Observer)")
    
    system = LinkedInSystem()
    
    print("\n1. Creating posts using Factory Pattern...")
    
    # Create different types of posts
    text_post = PostFactory.create_post(
        PostType.TEXT, "U001", 
        "Excited to share that I just completed a challenging project on distributed systems!",
        Visibility.PUBLIC
    )
    
    image_post = PostFactory.create_post(
        PostType.IMAGE, "U002",
        "Team outing photos from our annual retreat!",
        Visibility.CONNECTIONS,
        image_urls=["https://photos.com/img1.jpg", "https://photos.com/img2.jpg"]
    )
    
    article_post = PostFactory.create_post(
        PostType.ARTICLE, "U003",
        "Deep dive into machine learning algorithms and their practical applications...",
        Visibility.PUBLIC,
        title="Understanding ML Algorithms"
    )
    
    system.create_post(text_post)
    system.create_post(image_post)
    system.create_post(article_post)
    
    print(f"   ✓ Created 3 posts ({text_post.get_type().value}, {image_post.get_type().value}, {article_post.get_type().value})")
    
    print("\n2. Engaging with posts...")
    
    # Likes
    system.like_post(text_post.post_id, "U002")
    system.like_post(text_post.post_id, "U003")
    
    # Comments
    system.comment_on_post(text_post.post_id, "U002", "Congratulations Alice! Amazing work!")
    system.comment_on_post(text_post.post_id, "U003", "Very impressive project!")
    
    # Shares
    system.share_post(text_post.post_id, "U002")
    
    engagement = text_post.get_engagement_score()
    print(f"\n3. Post engagement:")
    print(f"   ✓ Likes: {len(text_post.likes)}")
    print(f"   ✓ Comments: {len(text_post.comments)}")
    print(f"   ✓ Shares: {len(text_post.shares)}")
    print(f"   ✓ Total engagement score: {engagement}")
    
    print("\n4. Generating personalized feed...")
    
    # Generate feed for Bob
    feed = system.generate_feed("U002", limit=10)
    print(f"   ✓ Generated feed with {len(feed)} posts for Bob")
    
    for i, post in enumerate(feed[:3], 1):
        author = system.get_user(post.author_id)
        print(f"   {i}. {author.name}: \"{post.content[:50]}...\" ({post.get_type().value})")


def demo5_messaging_system():
    """Demo 5: Messaging System with Observer"""
    print_section("DEMO 5: Messaging System")
    
    system = LinkedInSystem()
    system.add_observer(MessageNotifier())
    
    print("\n1. Sending messages...")
    
    # Send messages
    msg1 = system.send_message("U001", "U002", "Hi Bob, how's the new product feature coming along?")
    msg2 = system.send_message("U002", "U001", "Hey Alice! It's going great, we're launching next week!")
    msg3 = system.send_message("U001", "U002", "That's awesome! Let me know if you need any help with the backend.")
    
    print(f"\n2. Conversation details:")
    print(f"   ✓ Total messages: {len(system.messages)}")
    print(f"   ✓ Total conversations: {len(system.conversations)}")
    
    # Find conversation
    for conv_id, conv in system.conversations.items():
        print(f"   ✓ Conversation {conv_id}: {len(conv.messages)} messages")
        print(f"      Participants: {', '.join(conv.participant_ids)}")
    
    print("\n3. Marking messages as read...")
    
    msg1.mark_as_read()
    msg2.mark_as_read()
    
    read_count = sum(1 for msg in system.messages.values() if msg.is_read)
    print(f"   ✓ {read_count}/{len(system.messages)} messages read")
    
    print("\n4. Message timeline:")
    for msg_id, msg in list(system.messages.items())[:3]:
        sender = system.get_user(msg.sender_id)
        receiver = system.get_user(msg.receiver_id)
        status = "✓✓" if msg.is_read else "✓"
        print(f"   {status} {sender.name} → {receiver.name}: \"{msg.content[:40]}...\"")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LINKEDIN SYSTEM - COMPLETE DEMONSTRATION")
    print("="*70)
    print("\nDesign Patterns:")
    print("1. Singleton - LinkedInSystem (centralized system control)")
    print("2. Factory - PostFactory (different post types creation)")
    print("3. Strategy - JobMatchingStrategy (Skill/Location/Experience based)")
    print("4. Observer - Event notifications (Feed/Connection/Job/Message)")
    print("5. State - ConnectionState (Pending → Accepted/Rejected lifecycle)")
    
    time.sleep(1)
    
    demo1_user_profile_management()
    time.sleep(1)
    
    demo2_connection_system()
    time.sleep(1)
    
    demo3_job_posting_application()
    time.sleep(1)
    
    demo4_feed_interactions()
    time.sleep(1)
    
    demo5_messaging_system()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("• User profiles with skills and experience")
    print("• Connection system with state machine (Pending → Accepted/Rejected)")
    print("• Job matching with multiple strategies (Skill/Location/Experience)")
    print("• Post creation with Factory pattern (Text/Image/Video/Article)")
    print("• Feed generation with engagement-based ranking")
    print("• Messaging system with conversations")
    print("• Observer pattern for real-time notifications")
    print("• Connection recommendations with scoring")
    print("\nRun 'python3 INTERVIEW_COMPACT.py' to see all demos")

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
