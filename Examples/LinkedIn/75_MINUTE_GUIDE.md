# LinkedIn System - 75 Minute Interview Implementation Guide

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
