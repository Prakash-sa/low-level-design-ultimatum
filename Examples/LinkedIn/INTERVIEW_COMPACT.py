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
