# 📅 Meeting Scheduler System - Complete Design Document

## Table of Contents
1. [System Overview](#system-overview)
2. [Requirements Analysis](#requirements-analysis)
3. [Architecture & Design](#architecture--design)
4. [Core Entities](#core-entities)
5. [Design Patterns](#design-patterns)
6. [Algorithms](#algorithms)
7. [UML Diagrams](#uml-diagrams)
8. [API Design](#api-design)
9. [Scalability & Performance](#scalability--performance)
10. [Interview Q&A](#interview-qa)

---

## System Overview

### Purpose
A comprehensive **meeting scheduling system** that enables users to:
- Create and manage meetings
- Send and respond to invitations
- Book meeting rooms
- Detect scheduling conflicts
- Handle recurring meetings
- Send reminders and notifications

### Key Features
- ✅ **Meeting Management**: Create, update, cancel meetings
- ✅ **Calendar Integration**: Personal calendars with availability
- ✅ **Room Booking**: Reserve conference rooms with capacity checks
- ✅ **Conflict Detection**: Automatic overlap and double-booking prevention
- ✅ **Invitations**: Send invites with accept/decline/tentative responses
- ✅ **Recurring Meetings**: Daily, weekly, monthly patterns
- ✅ **Notifications**: Email/SMS reminders and updates
- ✅ **Time Zone Support**: Handle multi-timezone scheduling

### Technology Stack
- **Language**: Python 3.9+
- **Patterns**: Singleton, Strategy, Observer, State, Factory
- **Data Structures**: Interval Trees, Hash Maps, Priority Queues
- **Storage**: In-memory (expandable to PostgreSQL/Redis)

---

## Requirements Analysis

### Functional Requirements

#### 1. User Management
- Create user accounts with email and profile
- Manage personal calendar
- Set availability and working hours
- Configure notification preferences

#### 2. Meeting Operations
- **Create Meeting**: Title, time range, location, attendees
- **Update Meeting**: Modify time, add/remove attendees
- **Cancel Meeting**: Cancel with notification to all attendees
- **Recurring Meetings**: Create patterns (daily, weekly, monthly, custom)

#### 3. Invitation System
- Send invitations to attendees
- Track invitation status (Pending, Accepted, Declined, Tentative)
- Allow attendees to propose alternative times
- Notify organizer of responses

#### 4. Room Management
- Register meeting rooms with capacity and amenities
- Book rooms for meetings
- Check room availability
- Release rooms when meetings cancelled

#### 5. Conflict Detection
- Detect time conflicts for attendees
- Detect room double-booking
- Propose alternative time slots
- Allow override for urgent meetings

#### 6. Notifications
- Send meeting invitations
- Reminder notifications (15 min, 1 hour, 1 day before)
- Update notifications when meetings change
- Cancellation notifications

### Non-Functional Requirements

#### Performance
- **Meeting Creation**: < 100ms
- **Conflict Detection**: < 200ms for 1000+ meetings
- **Availability Query**: < 300ms
- **Notification Delivery**: < 5 seconds

#### Scalability
- Support 100,000+ users
- Handle 1 million+ meetings
- Support 10,000+ meeting rooms
- Process 100,000+ notifications/day

#### Reliability
- 99.9% uptime
- Data consistency for concurrent bookings
- Graceful degradation under load

#### Security
- User authentication and authorization
- Meeting privacy controls
- Encrypted communications

---

## Architecture & Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Meeting Scheduler System                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         MeetingScheduler (Singleton)             │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ • UserManager                                    │  │
│  │ • MeetingManager                                 │  │
│  │ • RoomManager                                    │  │
│  │ • CalendarManager                                │  │
│  │ • NotificationManager (Observer)                 │  │
│  │ • ConflictResolver (Strategy)                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│   User     │────▶│  Calendar  │────▶│  Meeting   │
└────────────┘     └────────────┘     └────────────┘
                                             │
                                             ▼
                          ┌────────────────────────────┐
                          │   ConflictDetector        │
                          │   (Interval Tree)         │
                          └────────────────────────────┘
                                             │
                          ┌──────────────────┴────────────────┐
                          ▼                                   ▼
                    ┌────────────┐                    ┌────────────┐
                    │    Room    │                    │ Invitation │
                    └────────────┘                    └────────────┘
                          │                                   │
                          └──────────────┬────────────────────┘
                                         ▼
                                ┌─────────────────┐
                                │ NotificationSvc │
                                │   (Observer)    │
                                └─────────────────┘
```

---

## Core Entities

### 1. Meeting
**Purpose**: Represents a scheduled meeting event

**Attributes**:
```python
class Meeting:
    meeting_id: str          # Unique identifier
    title: str               # Meeting title
    description: str         # Meeting description
    organizer: User          # Meeting organizer
    start_time: datetime     # Start timestamp
    end_time: datetime       # End timestamp
    attendees: List[User]    # List of attendees
    room: Optional[Room]     # Assigned room
    status: MeetingStatus    # Scheduled/Ongoing/Completed/Cancelled
    location: str            # Physical or virtual location
    recurrence: Optional[RecurrenceRule]  # For recurring meetings
    reminders: List[Reminder]             # Meeting reminders
    created_at: datetime
    updated_at: datetime
```

**Key Methods**:
- `add_attendee(user: User) -> bool`: Add attendee to meeting
- `remove_attendee(user: User) -> bool`: Remove attendee
- `reschedule(new_start: datetime, new_end: datetime) -> bool`
- `cancel() -> bool`: Cancel meeting
- `check_conflict(other: Meeting) -> bool`: Check for time overlap

### 2. User
**Purpose**: System user with calendar and preferences

**Attributes**:
```python
class User:
    user_id: str
    name: str
    email: str
    calendar: Calendar
    working_hours: WorkingHours    # e.g., 9 AM - 5 PM
    timezone: str                  # e.g., "America/New_York"
    notification_preferences: NotificationPreferences
    created_at: datetime
```

**Key Methods**:
- `create_meeting(...) -> Meeting`: Create new meeting
- `accept_invitation(invitation: Invitation) -> bool`
- `decline_invitation(invitation: Invitation) -> bool`
- `get_availability(start: datetime, end: datetime) -> List[TimeSlot]`
- `get_busy_times(start: datetime, end: datetime) -> List[TimeRange]`

### 3. Calendar
**Purpose**: User's personal calendar with meetings

**Attributes**:
```python
class Calendar:
    calendar_id: str
    owner: User
    meetings: Dict[str, Meeting]    # meeting_id -> Meeting
    interval_tree: IntervalTree     # For efficient conflict detection
```

**Key Methods**:
- `add_meeting(meeting: Meeting) -> bool`
- `remove_meeting(meeting_id: str) -> bool`
- `get_meetings(start: datetime, end: datetime) -> List[Meeting]`
- `check_availability(start: datetime, end: datetime) -> bool`
- `find_conflicts(meeting: Meeting) -> List[Meeting]`

### 4. Room
**Purpose**: Meeting room resource

**Attributes**:
```python
class Room:
    room_id: str
    name: str
    location: str
    capacity: int
    amenities: List[str]        # e.g., ["projector", "whiteboard"]
    bookings: Dict[str, Meeting]  # meeting_id -> Meeting
    available_hours: WorkingHours
```

**Key Methods**:
- `book(meeting: Meeting) -> bool`: Book room for meeting
- `release(meeting: Meeting) -> bool`: Release room
- `is_available(start: datetime, end: datetime) -> bool`
- `get_bookings(start: datetime, end: datetime) -> List[Meeting]`

### 5. Invitation
**Purpose**: Meeting invitation with response tracking

**Attributes**:
```python
class Invitation:
    invitation_id: str
    meeting: Meeting
    invitee: User
    status: InvitationStatus    # Pending/Accepted/Declined/Tentative
    sent_at: datetime
    responded_at: Optional[datetime]
    response_note: str
```

**Key Methods**:
- `accept(note: str = "") -> bool`
- `decline(note: str = "") -> bool`
- `mark_tentative(note: str = "") -> bool`
- `send() -> bool`: Send invitation to invitee

### 6. RecurringMeeting
**Purpose**: Meeting that repeats on a schedule

**Attributes**:
```python
class RecurringMeeting(Meeting):
    recurrence_rule: RecurrenceRule
    series_id: str                    # Links all instances
    exceptions: List[datetime]        # Cancelled instances
    end_date: Optional[datetime]      # When recurrence ends
```

**Key Methods**:
- `generate_instances(until: datetime) -> List[Meeting]`
- `cancel_instance(date: datetime) -> bool`
- `update_series() -> bool`: Update all future instances

---

## Design Patterns

### 1. Singleton Pattern - MeetingScheduler

**Purpose**: Ensure single system instance with global access

**Implementation**:
```python
class MeetingScheduler:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Thread-safe double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.users: Dict[str, User] = {}
            self.meetings: Dict[str, Meeting] = {}
            self.rooms: Dict[str, Room] = {}
            self.observers: List[Observer] = []
            self.conflict_resolver: ConflictResolutionStrategy = AutoRejectStrategy()
            self.initialized = True
```

**Benefits**:
- Single source of truth for all meetings/rooms
- Global state management
- Thread-safe initialization
- Resource sharing

### 2. Strategy Pattern - Conflict Resolution

**Purpose**: Flexible conflict handling algorithms

**Interface**:
```python
class ConflictResolutionStrategy(ABC):
    @abstractmethod
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> Resolution:
        pass
```

**Implementations**:

#### AutoRejectStrategy
```python
class AutoRejectStrategy(ConflictResolutionStrategy):
    """Automatically reject conflicting meetings"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> Resolution:
        if conflicts:
            return Resolution(success=False, 
                            message="Meeting conflicts detected",
                            conflicts=conflicts)
        return Resolution(success=True)
```

#### ProposeAlternativesStrategy
```python
class ProposeAlternativesStrategy(ConflictResolutionStrategy):
    """Find and propose alternative time slots"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> Resolution:
        if not conflicts:
            return Resolution(success=True)
        
        # Find next available slot
        alternatives = self._find_available_slots(
            meeting.attendees,
            meeting.duration,
            meeting.start_time,
            count=3
        )
        
        return Resolution(
            success=False,
            message="Conflicts found, alternatives proposed",
            alternatives=alternatives
        )
```

#### ForceBookStrategy
```python
class ForceBookStrategy(ConflictResolutionStrategy):
    """Override conflicts for high-priority meetings"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> Resolution:
        if meeting.priority == Priority.HIGH:
            # Cancel conflicting meetings
            for conflict in conflicts:
                conflict.cancel()
            return Resolution(success=True, 
                            message="Conflicts overridden",
                            cancelled=conflicts)
        return Resolution(success=False)
```

**Usage**:
```python
scheduler = MeetingScheduler()
scheduler.set_conflict_resolver(ProposeAlternativesStrategy())
```

### 3. Observer Pattern - Notifications

**Purpose**: Decouple notification system from core logic

**Interface**:
```python
class MeetingObserver(ABC):
    @abstractmethod
    def update(self, event: MeetingEvent, meeting: Meeting):
        pass
```

**Implementations**:

#### EmailNotifier
```python
class EmailNotifier(MeetingObserver):
    def update(self, event: MeetingEvent, meeting: Meeting):
        if event == MeetingEvent.CREATED:
            self._send_invitation_email(meeting)
        elif event == MeetingEvent.UPDATED:
            self._send_update_email(meeting)
        elif event == MeetingEvent.CANCELLED:
            self._send_cancellation_email(meeting)
```

#### SMSNotifier
```python
class SMSNotifier(MeetingObserver):
    def update(self, event: MeetingEvent, meeting: Meeting):
        if event == MeetingEvent.REMINDER:
            self._send_sms_reminder(meeting)
```

#### CalendarSyncObserver
```python
class CalendarSyncObserver(MeetingObserver):
    def update(self, event: MeetingEvent, meeting: Meeting):
        # Sync with external calendar (Google, Outlook)
        self._sync_to_external_calendar(meeting)
```

**Usage**:
```python
scheduler.add_observer(EmailNotifier())
scheduler.add_observer(SMSNotifier())
scheduler.add_observer(CalendarSyncObserver())

# When meeting is created:
scheduler.notify_observers(MeetingEvent.CREATED, meeting)
```

### 4. State Pattern - Meeting Lifecycle

**Purpose**: Manage meeting state transitions

**States**:
```
Scheduled → Ongoing → Completed
    ↓
Cancelled
```

**Implementation**:
```python
class MeetingState(ABC):
    @abstractmethod
    def start(self, meeting: Meeting) -> bool:
        pass
    
    @abstractmethod
    def complete(self, meeting: Meeting) -> bool:
        pass
    
    @abstractmethod
    def cancel(self, meeting: Meeting) -> bool:
        pass

class ScheduledState(MeetingState):
    def start(self, meeting: Meeting) -> bool:
        meeting.state = OngoingState()
        meeting.status = MeetingStatus.ONGOING
        return True
    
    def complete(self, meeting: Meeting) -> bool:
        return False  # Can't complete before starting
    
    def cancel(self, meeting: Meeting) -> bool:
        meeting.state = CancelledState()
        meeting.status = MeetingStatus.CANCELLED
        return True

class OngoingState(MeetingState):
    def start(self, meeting: Meeting) -> bool:
        return False  # Already ongoing
    
    def complete(self, meeting: Meeting) -> bool:
        meeting.state = CompletedState()
        meeting.status = MeetingStatus.COMPLETED
        return True
    
    def cancel(self, meeting: Meeting) -> bool:
        return False  # Can't cancel ongoing meeting
```

### 5. Factory Pattern - Meeting Creation

**Purpose**: Centralize meeting type creation

**Implementation**:
```python
class MeetingFactory:
    @staticmethod
    def create_meeting(meeting_type: MeetingType, **kwargs) -> Meeting:
        if meeting_type == MeetingType.SINGLE:
            return SingleMeeting(**kwargs)
        elif meeting_type == MeetingType.RECURRING:
            return RecurringMeeting(**kwargs)
        elif meeting_type == MeetingType.ALL_DAY:
            return AllDayMeeting(**kwargs)
        else:
            raise ValueError(f"Unknown meeting type: {meeting_type}")
```

**Usage**:
```python
# Create single meeting
meeting = MeetingFactory.create_meeting(
    MeetingType.SINGLE,
    title="Team Sync",
    start_time=start,
    end_time=end
)

# Create recurring meeting
recurring = MeetingFactory.create_meeting(
    MeetingType.RECURRING,
    title="Daily Standup",
    recurrence_rule=RecurrenceRule.DAILY,
    count=30
)
```

---

## Algorithms

### 1. Conflict Detection Algorithm

**Approach**: Interval Tree for O(log n) query time

```python
def detect_conflicts(self, meeting: Meeting) -> List[Meeting]:
    """
    Detect conflicts using interval tree
    Time: O(log n + k) where k = number of conflicts
    Space: O(n) for interval tree
    """
    conflicts = []
    
    # Check each attendee's calendar
    for attendee in meeting.attendees:
        calendar = attendee.calendar
        overlapping = calendar.interval_tree.query(
            meeting.start_time,
            meeting.end_time
        )
        conflicts.extend(overlapping)
    
    # Check room availability
    if meeting.room:
        room_conflicts = meeting.room.interval_tree.query(
            meeting.start_time,
            meeting.end_time
        )
        conflicts.extend(room_conflicts)
    
    return list(set(conflicts))  # Remove duplicates
```

**Complexity**:
- **Time**: O(log n + k) for n meetings, k conflicts
- **Space**: O(n) for storing interval tree

### 2. Find Available Time Slots

**Approach**: Merge intervals and find gaps

```python
def find_available_slots(self, users: List[User], duration: int,
                        search_start: datetime, search_end: datetime,
                        count: int = 5) -> List[TimeSlot]:
    """
    Find common available time slots for all users
    Time: O(m log m) where m = total busy slots
    Space: O(m) for merged intervals
    """
    # Step 1: Collect all busy times
    busy_times = []
    for user in users:
        busy = user.get_busy_times(search_start, search_end)
        busy_times.extend(busy)
    
    # Step 2: Sort by start time
    busy_times.sort(key=lambda x: x.start)
    
    # Step 3: Merge overlapping intervals
    merged = self._merge_intervals(busy_times)
    
    # Step 4: Find gaps
    available = []
    current = search_start
    
    for busy_slot in merged:
        if current < busy_slot.start:
            gap_duration = (busy_slot.start - current).total_seconds() / 60
            if gap_duration >= duration:
                available.append(TimeSlot(current, busy_slot.start))
        current = max(current, busy_slot.end)
    
    # Check final gap
    if current < search_end:
        gap_duration = (search_end - current).total_seconds() / 60
        if gap_duration >= duration:
            available.append(TimeSlot(current, search_end))
    
    return available[:count]

def _merge_intervals(self, intervals: List[TimeRange]) -> List[TimeRange]:
    """Merge overlapping time intervals"""
    if not intervals:
        return []
    
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current.start <= last.end:
            # Overlapping, merge
            last.end = max(last.end, current.end)
        else:
            # Non-overlapping, add new
            merged.append(current)
    
    return merged
```

**Complexity**:
- **Time**: O(m log m) for m busy slots
- **Space**: O(m) for storing and merging

### 3. Recurring Meeting Expansion

**Approach**: Generate instances based on recurrence rule

```python
def generate_instances(self, until: datetime) -> List[Meeting]:
    """
    Generate meeting instances for recurring meeting
    Time: O(k) where k = number of instances
    Space: O(k)
    """
    instances = []
    current = self.start_time
    instance_count = 0
    
    while current < until:
        # Skip if in exceptions list
        if current not in self.exceptions:
            instance = Meeting(
                meeting_id=f"{self.series_id}_{instance_count}",
                title=self.title,
                start_time=current,
                end_time=current + self.duration,
                attendees=self.attendees,
                room=self.room
            )
            instances.append(instance)
            instance_count += 1
        
        # Calculate next occurrence
        if self.recurrence_rule == RecurrenceRule.DAILY:
            current += timedelta(days=1)
        elif self.recurrence_rule == RecurrenceRule.WEEKLY:
            current += timedelta(weeks=1)
        elif self.recurrence_rule == RecurrenceRule.MONTHLY:
            current = self._add_months(current, 1)
        
        # Check count limit
        if self.count and instance_count >= self.count:
            break
    
    return instances
```

**Complexity**:
- **Time**: O(k) for k instances
- **Space**: O(k) to store instances

---

## UML Diagrams

### Class Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   MeetingScheduler                      │
│                     (Singleton)                         │
├─────────────────────────────────────────────────────────┤
│ - _instance: MeetingScheduler                           │
│ - users: Dict[str, User]                                │
│ - meetings: Dict[str, Meeting]                          │
│ - rooms: Dict[str, Room]                                │
│ - observers: List[Observer]                             │
│ - conflict_resolver: ConflictResolutionStrategy         │
├─────────────────────────────────────────────────────────┤
│ + get_instance(): MeetingScheduler                      │
│ + schedule_meeting(meeting: Meeting): bool              │
│ + cancel_meeting(meeting_id: str): bool                 │
│ + add_observer(observer: Observer): void                │
│ + notify_observers(event, data): void                   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ manages
                          ▼
         ┌────────────────────────────────┐
         │          User                  │
         ├────────────────────────────────┤
         │ - user_id: str                 │
         │ - name: str                    │
         │ - email: str                   │
         │ - calendar: Calendar           │
         │ - timezone: str                │
         ├────────────────────────────────┤
         │ + create_meeting(): Meeting    │
         │ + accept_invitation(): bool    │
         │ + get_availability(): List     │
         └────────────────────────────────┘
                          │
                          │ owns
                          ▼
         ┌────────────────────────────────┐
         │         Calendar               │
         ├────────────────────────────────┤
         │ - calendar_id: str             │
         │ - owner: User                  │
         │ - meetings: Dict               │
         │ - interval_tree: IntervalTree  │
         ├────────────────────────────────┤
         │ + add_meeting(): bool          │
         │ + find_conflicts(): List       │
         │ + check_availability(): bool   │
         └────────────────────────────────┘
                          │
                          │ contains
                          ▼
         ┌────────────────────────────────┐
         │         Meeting                │
         ├────────────────────────────────┤
         │ - meeting_id: str              │
         │ - title: str                   │
         │ - start_time: datetime         │
         │ - end_time: datetime           │
         │ - organizer: User              │
         │ - attendees: List[User]        │
         │ - room: Room                   │
         │ - status: MeetingStatus        │
         │ - state: MeetingState          │
         ├────────────────────────────────┤
         │ + add_attendee(): bool         │
         │ + cancel(): bool               │
         │ + check_conflict(): bool       │
         └────────────────────────────────┘
                          │
                          │ uses
                          ▼
         ┌────────────────────────────────┐
         │           Room                 │
         ├────────────────────────────────┤
         │ - room_id: str                 │
         │ - name: str                    │
         │ - capacity: int                │
         │ - bookings: Dict               │
         ├────────────────────────────────┤
         │ + book(): bool                 │
         │ + is_available(): bool         │
         └────────────────────────────────┘
```

### State Diagram - Meeting Lifecycle

```
                    ┌─────────────┐
                    │  Scheduled  │ (Initial State)
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │                     │
         start()│              cancel()│
                ▼                     ▼
         ┌─────────────┐       ┌─────────────┐
         │   Ongoing   │       │  Cancelled  │ (Terminal)
         └──────┬──────┘       └─────────────┘
                │
        complete()│
                ▼
         ┌─────────────┐
         │  Completed  │ (Terminal)
         └─────────────┘

Valid Transitions:
• Scheduled → Ongoing  : Meeting starts
• Scheduled → Cancelled: Meeting cancelled before start
• Ongoing → Completed  : Meeting ends normally
```

### Sequence Diagram - Meeting Creation with Conflict Detection

```
User      Scheduler        Calendar      ConflictDetector      Room      Observer
 │            │                │                │               │           │
 │──create──▶│                │                │               │           │
 │            │──find conflicts─▶              │               │           │
 │            │                │──query tree──▶│               │           │
 │            │                │◀──conflicts───│               │           │
 │            │                │                │               │           │
 │            │──check room────────────────────────────────────▶│           │
 │            │◀──available────────────────────────────────────│           │
 │            │                │                │               │           │
 │            │──add meeting──▶│                │               │           │
 │            │                │──insert tree──▶│               │           │
 │            │                │                │               │           │
 │            │──book room─────────────────────────────────────▶│           │
 │            │                │                │               │           │
 │            │──notify──────────────────────────────────────────────────▶│
 │            │                │                │               │           │
 │◀──meeting──│                │                │               │           │
```

### Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │  Web UI  │  │  Mobile  │  │   API    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
        ┌─────────────────▼─────────────────┐
        │      Business Logic Layer         │
        │  ┌───────────────────────────┐    │
        │  │  MeetingScheduler         │    │
        │  │    (Singleton)            │    │
        │  └───────────────────────────┘    │
        │            │                      │
        │    ┌───────┴───────┐              │
        │    ▼               ▼              │
        │  ┌──────────┐  ┌──────────┐       │
        │  │ Meeting  │  │   Room   │       │
        │  │ Manager  │  │ Manager  │       │
        │  └──────────┘  └──────────┘       │
        └───────────────────────────────────┘
                          │
        ┌─────────────────▼─────────────────┐
        │     Data Access Layer             │
        │  ┌──────────┐  ┌──────────┐       │
        │  │ In-Memory│  │  Cache   │       │
        │  │  Storage │  │  (Redis) │       │
        │  └──────────┘  └──────────┘       │
        └───────────────────────────────────┘
```

---

## API Design

### REST API Endpoints

#### Meeting Operations
```
POST   /api/v1/meetings              - Create meeting
GET    /api/v1/meetings/{id}         - Get meeting details
PUT    /api/v1/meetings/{id}         - Update meeting
DELETE /api/v1/meetings/{id}         - Cancel meeting
GET    /api/v1/meetings              - List meetings (with filters)
POST   /api/v1/meetings/recurring    - Create recurring meeting
```

#### Calendar Operations
```
GET    /api/v1/users/{id}/calendar   - Get user's calendar
GET    /api/v1/users/{id}/availability - Get availability
POST   /api/v1/users/{id}/busy-times - Get busy times
```

#### Room Operations
```
GET    /api/v1/rooms                 - List all rooms
GET    /api/v1/rooms/{id}            - Get room details
GET    /api/v1/rooms/{id}/availability - Check room availability
POST   /api/v1/rooms/{id}/book       - Book room
```

#### Invitation Operations
```
POST   /api/v1/invitations/{id}/accept   - Accept invitation
POST   /api/v1/invitations/{id}/decline  - Decline invitation
POST   /api/v1/invitations/{id}/tentative - Mark tentative
```

### Example API Request/Response

**Create Meeting**:
```json
POST /api/v1/meetings
{
  "title": "Q4 Planning",
  "start_time": "2025-12-01T14:00:00Z",
  "end_time": "2025-12-01T15:30:00Z",
  "attendees": ["user1@email.com", "user2@email.com"],
  "room_id": "room-101",
  "description": "Quarterly planning session",
  "reminders": [15, 60]
}

Response 201 Created:
{
  "meeting_id": "MTG_000123",
  "title": "Q4 Planning",
  "status": "scheduled",
  "invitations_sent": 2,
  "conflicts": [],
  "room_booked": true,
  "created_at": "2025-11-29T10:00:00Z"
}
```

**Check Availability**:
```json
GET /api/v1/users/user1/availability?start=2025-12-01T09:00:00Z&end=2025-12-01T17:00:00Z

Response 200 OK:
{
  "user_id": "user1",
  "available_slots": [
    {
      "start": "2025-12-01T09:00:00Z",
      "end": "2025-12-01T10:30:00Z"
    },
    {
      "start": "2025-12-01T13:00:00Z",
      "end": "2025-12-01T14:00:00Z"
    }
  ],
  "busy_times": [
    {
      "start": "2025-12-01T10:30:00Z",
      "end": "2025-12-01T12:00:00Z",
      "meeting_title": "Team Sync"
    }
  ]
}
```

---

## Scalability & Performance

### Database Schema

**Users Table**:
```sql
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    timezone VARCHAR(50),
    working_hours_start TIME,
    working_hours_end TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);
```

**Meetings Table** (Partitioned by date):
```sql
CREATE TABLE meetings (
    meeting_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    organizer_id VARCHAR(50),
    room_id VARCHAR(50),
    status VARCHAR(20),
    series_id VARCHAR(50),  -- For recurring meetings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_start_time (start_time),
    INDEX idx_organizer (organizer_id),
    INDEX idx_series (series_id),
    FOREIGN KEY (organizer_id) REFERENCES users(user_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
) PARTITION BY RANGE (start_time);
```

**Meeting_Attendees Table**:
```sql
CREATE TABLE meeting_attendees (
    meeting_id VARCHAR(50),
    user_id VARCHAR(50),
    invitation_status VARCHAR(20),
    responded_at TIMESTAMP,
    PRIMARY KEY (meeting_id, user_id),
    INDEX idx_user_meetings (user_id, meeting_id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Caching Strategy

**Redis Caching**:
```python
# Cache user availability (TTL: 5 minutes)
cache_key = f"availability:{user_id}:{date}"
availability = redis.get(cache_key)
if not availability:
    availability = calculate_availability(user_id, date)
    redis.setex(cache_key, 300, availability)

# Cache room bookings (TTL: 10 minutes)
cache_key = f"room_bookings:{room_id}:{date}"

# Cache meeting details (TTL: 1 hour)
cache_key = f"meeting:{meeting_id}"
```

**Cache Invalidation**:
- Meeting created/updated/cancelled → Invalidate all attendees' availability
- Room booked/released → Invalidate room bookings cache
- User updates working hours → Invalidate user availability

### Performance Optimizations

1. **Interval Tree for Conflicts**: O(log n) instead of O(n)
2. **Database Indexing**: On start_time, user_id, room_id
3. **Batch Processing**: Process reminders in batches
4. **Async Notifications**: Use message queue (RabbitMQ/Kafka)
5. **Read Replicas**: Separate read/write databases
6. **Connection Pooling**: Reuse database connections

### Load Balancing Architecture

```
                    ┌─────────────┐
                    │Load Balancer│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────▼─────┐   ┌─────▼─────┐  ┌─────▼─────┐
     │  API      │   │  API      │  │  API      │
     │  Server 1 │   │  Server 2 │  │  Server 3 │
     └─────┬─────┘   └─────┬─────┘  └─────┬─────┘
           └───────────────┼───────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
        ┌─────▼─────┐            ┌─────▼─────┐
        │   Redis   │            │ PostgreSQL│
        │   Cache   │            │  Primary  │
        └───────────┘            └─────┬─────┘
                                       │
                                 ┌─────▼─────┐
                                 │PostgreSQL │
                                 │  Replica  │
                                 └───────────┘
```

---

## Interview Q&A

### Q1: How do you handle concurrent meeting bookings for the same room?

**A**: We use **optimistic locking** with version numbers:

1. **Database-level locking**:
```sql
UPDATE rooms 
SET version = version + 1 
WHERE room_id = ? AND version = ?
```

2. **Application-level**:
```python
def book_room(room: Room, meeting: Meeting) -> bool:
    with transaction():
        current_version = room.version
        if room.is_available(meeting.start_time, meeting.end_time):
            room.add_booking(meeting)
            # Atomic update with version check
            rows = db.execute(
                "UPDATE rooms SET version = version + 1 "
                "WHERE room_id = ? AND version = ?",
                (room.room_id, current_version)
            )
            if rows == 0:
                raise ConcurrentModificationError()
            return True
        return False
```

3. **Retry mechanism**: If version mismatch, retry up to 3 times

**Alternative**: Use **pessimistic locking** with `SELECT FOR UPDATE`

---

### Q2: How do you efficiently find available time slots for multiple attendees?

**A**: Use **interval merging algorithm**:

**Algorithm**:
1. Collect all attendees' busy times: O(k × m) where k=attendees, m=avg meetings
2. Sort all intervals by start time: O(n log n)
3. Merge overlapping intervals: O(n)
4. Find gaps between merged intervals: O(n)
5. Filter by minimum duration

**Optimization**: Use **sweep line algorithm** for O(n log n):
```python
def find_common_free_slots(attendees: List[User], duration: int) -> List[TimeSlot]:
    events = []  # (time, type, user_id)
    
    # Create events for all busy times
    for user in attendees:
        for busy in user.get_busy_times():
            events.append((busy.start, 'start', user.user_id))
            events.append((busy.end, 'end', user.user_id))
    
    events.sort()  # O(n log n)
    
    active_users = set()
    free_slots = []
    last_time = search_start
    
    for time, event_type, user_id in events:
        # If all users free, we have a potential slot
        if len(active_users) == 0 and (time - last_time) >= duration:
            free_slots.append(TimeSlot(last_time, time))
        
        if event_type == 'start':
            active_users.add(user_id)
        else:
            active_users.remove(user_id)
        
        last_time = time
    
    return free_slots
```

**Complexity**: O(n log n) vs naive O(k × m × n)

---

### Q3: How would you implement recurring meetings efficiently?

**A**: Use **series-based approach** with lazy generation:

**Design**:
```python
class RecurringSeries:
    series_id: str
    base_meeting: Meeting
    recurrence_rule: RecurrenceRule
    exceptions: Set[datetime]  # Cancelled instances
    modifications: Dict[datetime, Meeting]  # Modified instances
    
    def get_instance(self, date: datetime) -> Optional[Meeting]:
        """Lazy generation - only create when needed"""
        if date in self.exceptions:
            return None
        
        if date in self.modifications:
            return self.modifications[date]
        
        return self._generate_instance(date)
```

**Storage**:
- Store only the series metadata (1 row)
- Store exceptions and modifications separately
- Generate instances on-the-fly for queries

**Query optimization**:
```sql
-- Get meetings for date range
SELECT * FROM meetings 
WHERE (
    -- Single meetings
    (series_id IS NULL AND start_time BETWEEN ? AND ?)
    OR
    -- Recurring series that overlap range
    (series_id IN (
        SELECT series_id FROM recurring_series
        WHERE series_start <= ? AND (series_end IS NULL OR series_end >= ?)
    ))
)
```

**Benefits**:
- Efficient storage: O(1) instead of O(k) for k instances
- Easy to modify series: Update base, not all instances
- No pre-generation needed

---

### Q4: How do you handle time zones?

**A**: Store all times in **UTC** and convert for display:

**Strategy**:
1. **Storage**: All datetime in UTC
```python
class Meeting:
    start_time: datetime  # Always UTC
    end_time: datetime    # Always UTC
```

2. **User timezone preference**:
```python
class User:
    timezone: str  # e.g., "America/New_York"
    
    def get_local_time(self, utc_time: datetime) -> datetime:
        return utc_time.astimezone(pytz.timezone(self.timezone))
```

3. **API handling**:
```python
# Input: Accept ISO 8601 with timezone
"2025-12-01T14:00:00-05:00"  # EST

# Convert to UTC for storage
utc_time = parse_iso8601(input_time).astimezone(pytz.UTC)

# Output: Return in user's timezone
response_time = utc_time.astimezone(user.timezone)
```

4. **Conflict detection**: Always in UTC to avoid DST issues

**Edge cases**:
- DST transitions: Meeting at 2:30 AM during "fall back"
- Cross-timezone meetings: Show local time for each attendee
- All-day events: Store as date, not datetime

---

### Q5: How would you implement meeting reminders?

**A**: Use **scheduled jobs with priority queue**:

**Architecture**:
```python
class ReminderScheduler:
    def __init__(self):
        self.reminder_queue = PriorityQueue()  # Min heap by time
        self.worker_thread = Thread(target=self._process_reminders)
    
    def schedule_reminder(self, meeting: Meeting, minutes_before: int):
        reminder_time = meeting.start_time - timedelta(minutes=minutes_before)
        self.reminder_queue.put((reminder_time, meeting.meeting_id))
    
    def _process_reminders(self):
        while True:
            # Get next reminder
            reminder_time, meeting_id = self.reminder_queue.get()
            
            # Sleep until reminder time
            wait_seconds = (reminder_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            
            # Send notification
            self._send_reminder(meeting_id)
```

**Scalability**: Use **Celery** or **RabbitMQ** for distributed processing:
```python
from celery import Celery

@celery.task
def send_reminder(meeting_id: str):
    meeting = get_meeting(meeting_id)
    notify_attendees(meeting)

# Schedule task
send_reminder.apply_async(
    args=[meeting.meeting_id],
    eta=meeting.start_time - timedelta(minutes=15)
)
```

**Database approach**: Periodic polling (every minute):
```sql
SELECT meeting_id FROM reminders
WHERE reminder_time <= NOW() AND status = 'pending'
ORDER BY reminder_time
LIMIT 1000;
```

---

### Q6: What's your strategy for conflict resolution?

**A**: **Strategy pattern** with multiple resolution algorithms:

**Strategies**:

1. **AutoRejectStrategy**: Reject conflicting meetings
   - Use case: Strict calendar management
   - Pro: No manual intervention
   - Con: Less flexible

2. **ProposeAlternativesStrategy**: Find alternative slots
   - Use case: Flexible scheduling
   - Pro: User-friendly
   - Con: Computation overhead

3. **PriorityBasedStrategy**: High priority overrides low
   - Use case: Executive calendars
   - Pro: Respects importance
   - Con: May cancel important meetings

4. **InteractiveStrategy**: Ask user to decide
   - Use case: Complex conflicts
   - Pro: User control
   - Con: Requires user action

**Implementation**:
```python
class ConflictResolver:
    def __init__(self, strategy: ConflictResolutionStrategy):
        self.strategy = strategy
    
    def resolve(self, meeting: Meeting) -> Resolution:
        conflicts = self._detect_conflicts(meeting)
        if not conflicts:
            return Resolution(success=True)
        
        return self.strategy.resolve(meeting, conflicts)

# Usage - can swap strategies
resolver = ConflictResolver(ProposeAlternativesStrategy())
result = resolver.resolve(new_meeting)
```

---

### Q7: How do you optimize database queries for calendar views?

**A**: Use **denormalization** and **materialized views**:

**1. Denormalized meeting_attendees**:
```sql
-- Instead of joining, store attendee data
CREATE TABLE meeting_attendees_denorm (
    meeting_id VARCHAR(50),
    user_id VARCHAR(50),
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    meeting_title VARCHAR(500),
    meeting_start TIMESTAMP,
    meeting_end TIMESTAMP,
    status VARCHAR(20),
    PRIMARY KEY (meeting_id, user_id),
    INDEX idx_user_date (user_id, meeting_start)
);
```

**2. Materialized view for user calendars**:
```sql
CREATE MATERIALIZED VIEW user_calendar_mv AS
SELECT 
    u.user_id,
    u.name,
    m.meeting_id,
    m.title,
    m.start_time,
    m.end_time,
    m.status
FROM users u
JOIN meeting_attendees ma ON u.user_id = ma.user_id
JOIN meetings m ON ma.meeting_id = m.meeting_id
WHERE m.status != 'cancelled';

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY user_calendar_mv;
```

**3. Indexed queries**:
```sql
-- Efficient query with composite index
CREATE INDEX idx_user_date_status 
ON meeting_attendees (user_id, meeting_start, status);

-- Query uses index
SELECT * FROM meeting_attendees
WHERE user_id = ? 
  AND meeting_start >= ?
  AND meeting_start < ?
  AND status = 'accepted';
```

**4. Partitioning**:
```sql
-- Partition by month for historical data
CREATE TABLE meetings (
    ...
) PARTITION BY RANGE (DATE_TRUNC('month', start_time));

-- Query only relevant partition
SELECT * FROM meetings
WHERE start_time >= '2025-12-01' AND start_time < '2026-01-01';
```

---

### Q8: How would you design the notification system for scalability?

**A**: **Event-driven architecture** with message queue:

**Architecture**:
```
Meeting Event → Kafka Topic → Multiple Consumers
                                  ├→ Email Service
                                  ├→ SMS Service
                                  ├→ Push Notification Service
                                  └→ Webhook Service
```

**Implementation**:
```python
# Producer
class MeetingScheduler:
    def create_meeting(self, meeting: Meeting):
        # Save meeting
        self.save_meeting(meeting)
        
        # Publish event
        event = MeetingEvent(
            type='MEETING_CREATED',
            meeting_id=meeting.meeting_id,
            attendees=meeting.attendees,
            timestamp=datetime.now()
        )
        kafka_producer.send('meeting-events', event)

# Consumer
class EmailNotificationConsumer:
    def consume(self):
        for message in kafka_consumer:
            event = MeetingEvent.from_json(message.value)
            if event.type == 'MEETING_CREATED':
                self.send_invitation_emails(event.attendees)
            elif event.type == 'MEETING_UPDATED':
                self.send_update_emails(event.attendees)
```

**Benefits**:
- **Scalability**: Add more consumers
- **Reliability**: Kafka guarantees delivery
- **Decoupling**: Services independent
- **Retry**: Failed notifications retry automatically

---

### Q9: How do you handle meeting cancellation cascade?

**A**: **Transaction-based approach** with compensating actions:

**Algorithm**:
```python
def cancel_meeting(meeting_id: str) -> bool:
    with transaction():
        # 1. Get meeting
        meeting = get_meeting(meeting_id)
        
        # 2. Release room booking
        if meeting.room:
            meeting.room.release(meeting)
        
        # 3. Update attendee calendars
        for attendee in meeting.attendees:
            attendee.calendar.remove_meeting(meeting)
        
        # 4. Update invitation statuses
        update_invitations_status(meeting_id, 'CANCELLED')
        
        # 5. Cancel reminders
        cancel_scheduled_reminders(meeting_id)
        
        # 6. Mark meeting as cancelled
        meeting.status = MeetingStatus.CANCELLED
        save_meeting(meeting)
        
        # 7. Notify all attendees (async)
        notify_cancellation.delay(meeting_id)
        
        # 8. If recurring, handle series
        if meeting.series_id:
            handle_recurring_cancellation(meeting)
        
        return True
```

**Recurring meeting cancellation options**:
1. **Cancel this instance**: Add to exceptions
2. **Cancel this and future**: Update series end date
3. **Cancel entire series**: Mark series as cancelled

**Rollback handling**: If any step fails, transaction rolls back

---

### Q10: What metrics would you track for this system?

**A**: **Multi-level monitoring**:

**Business Metrics**:
- Meetings created per day/week/month
- Meeting acceptance rate
- Average meeting duration
- Room utilization rate
- Most active users/rooms
- Conflict resolution success rate

**Performance Metrics**:
- API response time (p50, p95, p99)
  - Meeting creation: < 100ms (p95)
  - Conflict detection: < 200ms (p95)
  - Calendar query: < 300ms (p95)
- Database query time
- Cache hit rate (target: > 80%)
- Notification delivery time

**System Health**:
- Error rate (target: < 0.1%)
- Availability (target: 99.9%)
- Database connection pool usage
- Queue length (Kafka lag)
- Memory/CPU utilization

**Monitoring Implementation**:
```python
import prometheus_client as prom

# Counters
meetings_created = prom.Counter('meetings_created_total', 'Total meetings created')
conflicts_detected = prom.Counter('conflicts_detected_total', 'Total conflicts')

# Histograms
api_latency = prom.Histogram('api_request_duration_seconds', 'API latency')
conflict_check_time = prom.Histogram('conflict_check_duration_seconds', 'Conflict check time')

# Gauges
active_meetings = prom.Gauge('active_meetings', 'Currently ongoing meetings')
room_utilization = prom.Gauge('room_utilization_percent', 'Room utilization')

# Usage
@api_latency.time()
def create_meeting(request):
    meetings_created.inc()
    # ... logic
```

**Alerting Rules**:
- Error rate > 1% for 5 minutes
- p95 latency > 500ms for 10 minutes
- Availability < 99.5% for 30 minutes
- Kafka lag > 10,000 messages

---

## Summary

This Meeting Scheduler system demonstrates:
- ✅ **5 Design Patterns**: Singleton, Strategy, Observer, State, Factory
- ✅ **SOLID Principles**: Applied throughout all classes
- ✅ **Efficient Algorithms**: Interval trees, merge intervals, sweep line
- ✅ **Scalable Architecture**: Message queues, caching, database optimization
- ✅ **Real-world Features**: Recurring meetings, time zones, notifications
- ✅ **Interview-ready**: Complete Q&A with detailed explanations

**Next Steps**: See `INTERVIEW_COMPACT.py` for working implementation and `75_MINUTE_GUIDE.md` for step-by-step coding guide.
