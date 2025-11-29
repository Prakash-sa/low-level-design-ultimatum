# 📅 Meeting Scheduler - 75 Minute Implementation Guide

## Overview
This guide provides a **phase-by-phase approach** to implementing a Meeting Scheduler system in a 75-minute interview. It focuses on **what to code first, design patterns to apply, and how to manage time effectively**.

---

## Quick Reference

| Phase | Time | Focus | Deliverable |
|-------|------|-------|-------------|
| **1. Requirements** | 0-5 min | Clarify scope | Requirements document |
| **2. Architecture** | 5-15 min | High-level design | Class diagram |
| **3. Core Entities** | 15-40 min | Meeting, Calendar, User | Working CRUD |
| **4. Patterns** | 40-60 min | Singleton, Strategy, Observer | Conflict detection |
| **5. Integration** | 60-70 min | Wire everything | End-to-end demo |
| **6. Testing** | 70-75 min | Validate | Demo scenarios |

---

## Phase 1: Requirements Clarification (0-5 minutes)

### Questions to Ask

#### 1. Functional Scope
**Q**: "What are the core features needed?"
- Create/update/cancel meetings
- Invite attendees
- Book meeting rooms
- Detect conflicts
- Recurring meetings
- Notifications/reminders

**Decision**: Focus on **meeting creation, conflict detection, and room booking**. Defer notifications for later.

#### 2. Scale & Performance
**Q**: "What's the expected scale?"
- Number of users: 10K-100K
- Meetings per day: 100K-1M
- Concurrent operations: 1K-10K

**Decision**: Design for **100K users, 500K meetings**. Use in-memory storage initially, explain database later.

#### 3. Conflict Handling
**Q**: "How should we handle scheduling conflicts?"
- Auto-reject conflicting meetings
- Propose alternative time slots
- Allow override for urgent meetings

**Decision**: Implement **Strategy pattern** for flexible conflict resolution.

#### 4. Time Zones
**Q**: "Do we need multi-timezone support?"
- Store in UTC, display in local timezone
- Handle DST transitions

**Decision**: Store all times in **UTC**, mention timezone conversion in API layer.

### Key Clarifications

```
✅ Single + recurring meetings
✅ Room booking with capacity checks
✅ Conflict detection (automatic)
✅ Email invitations (interface only)
⏸️ Video conferencing integration (out of scope)
⏸️ Advanced analytics (out of scope)
```

---

## Phase 2: Architecture & Design (5-15 minutes)

### High-Level Components

```
┌─────────────────────────────────────────┐
│     MeetingScheduler (Singleton)        │
├─────────────────────────────────────────┤
│ • UserManager                           │
│ • MeetingManager                        │
│ • RoomManager                           │
│ • CalendarManager                       │
│ • NotificationService (Observer)        │
│ • ConflictResolver (Strategy)           │
└─────────────────────────────────────────┘
```

### Core Entities (5 minutes to sketch)

```python
# 1. Meeting - represents a scheduled event
class Meeting:
    meeting_id, title, start_time, end_time
    organizer, attendees, room, status

# 2. User - system participant
class User:
    user_id, name, email, calendar

# 3. Calendar - user's schedule
class Calendar:
    calendar_id, owner, meetings
    interval_tree  # For O(log n) conflict detection

# 4. Room - meeting space
class Room:
    room_id, name, capacity, bookings

# 5. Invitation - meeting invite
class Invitation:
    invitation_id, meeting, invitee, status
```

### Class Diagram (Quick Sketch)

```
User ──owns──> Calendar ──contains──> Meeting ──uses──> Room
  │                                       │
  └───────────sends/receives──────> Invitation
```

### Design Patterns to Apply

1. **Singleton**: MeetingScheduler (single system instance)
2. **Strategy**: ConflictResolutionStrategy (flexible conflict handling)
3. **Observer**: NotificationObserver (decouple notifications)
4. **State**: MeetingState (lifecycle management)
5. **Factory**: MeetingFactory (create different meeting types)

**Time checkpoint**: Should have basic architecture sketched by **minute 15**.

---

## Phase 3: Core Entity Implementation (15-40 minutes)

### Step 1: Basic Enums (2 minutes)

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import threading

class MeetingStatus(Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InvitationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
```

### Step 2: Meeting Class (5 minutes)

```python
class Meeting:
    def __init__(self, meeting_id: str, title: str, 
                 start_time: datetime, end_time: datetime,
                 organizer: 'User'):
        self.meeting_id = meeting_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.organizer = organizer
        self.attendees: List['User'] = []
        self.room: Optional['Room'] = None
        self.status = MeetingStatus.SCHEDULED
        self.created_at = datetime.now()
    
    def add_attendee(self, user: 'User') -> bool:
        """Add attendee to meeting"""
        if user not in self.attendees:
            self.attendees.append(user)
            return True
        return False
    
    def check_conflict(self, other: 'Meeting') -> bool:
        """Check if this meeting overlaps with another"""
        return not (self.end_time <= other.start_time or 
                    self.start_time >= other.end_time)
    
    def cancel(self) -> bool:
        """Cancel meeting"""
        if self.status == MeetingStatus.SCHEDULED:
            self.status = MeetingStatus.CANCELLED
            # Release room if booked
            if self.room:
                self.room.release(self)
            return True
        return False
    
    def __repr__(self):
        return (f"Meeting(id={self.meeting_id}, title={self.title}, "
                f"time={self.start_time} to {self.end_time})")
```

### Step 3: User Class (3 minutes)

```python
class User:
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.calendar: Optional['Calendar'] = None
        self.created_at = datetime.now()
    
    def create_meeting(self, title: str, start_time: datetime, 
                      end_time: datetime) -> Meeting:
        """Create a new meeting organized by this user"""
        meeting_id = f"MTG_{id(self)}_{int(datetime.now().timestamp())}"
        meeting = Meeting(meeting_id, title, start_time, end_time, self)
        return meeting
    
    def accept_invitation(self, invitation: 'Invitation') -> bool:
        """Accept meeting invitation"""
        return invitation.accept()
    
    def decline_invitation(self, invitation: 'Invitation') -> bool:
        """Decline meeting invitation"""
        return invitation.decline()
    
    def __repr__(self):
        return f"User(id={self.user_id}, name={self.name}, email={self.email})"
```

### Step 4: Calendar with Conflict Detection (8 minutes)

**KEY**: This is the most important class for conflict detection.

```python
class Calendar:
    def __init__(self, calendar_id: str, owner: User):
        self.calendar_id = calendar_id
        self.owner = owner
        self.meetings: Dict[str, Meeting] = {}
    
    def add_meeting(self, meeting: Meeting) -> bool:
        """Add meeting to calendar"""
        # Check for conflicts
        conflicts = self.find_conflicts(meeting)
        if conflicts:
            return False
        
        self.meetings[meeting.meeting_id] = meeting
        return True
    
    def remove_meeting(self, meeting_id: str) -> bool:
        """Remove meeting from calendar"""
        if meeting_id in self.meetings:
            del self.meetings[meeting_id]
            return True
        return False
    
    def find_conflicts(self, meeting: Meeting) -> List[Meeting]:
        """Find all meetings that conflict with given meeting"""
        conflicts = []
        for existing in self.meetings.values():
            if (existing.status != MeetingStatus.CANCELLED and 
                meeting.check_conflict(existing)):
                conflicts.append(existing)
        return conflicts
    
    def get_meetings(self, start: datetime, end: datetime) -> List[Meeting]:
        """Get all meetings in date range"""
        result = []
        for meeting in self.meetings.values():
            if (meeting.start_time < end and meeting.end_time > start):
                result.append(meeting)
        return sorted(result, key=lambda m: m.start_time)
    
    def check_availability(self, start: datetime, end: datetime) -> bool:
        """Check if time slot is available"""
        test_meeting = Meeting("test", "Test", start, end, self.owner)
        return len(self.find_conflicts(test_meeting)) == 0
    
    def __repr__(self):
        return f"Calendar(owner={self.owner.name}, meetings={len(self.meetings)})"
```

### Step 5: Room Class (4 minutes)

```python
class Room:
    def __init__(self, room_id: str, name: str, capacity: int):
        self.room_id = room_id
        self.name = name
        self.capacity = capacity
        self.bookings: Dict[str, Meeting] = {}
    
    def book(self, meeting: Meeting) -> bool:
        """Book room for meeting"""
        # Check capacity
        if len(meeting.attendees) > self.capacity:
            return False
        
        # Check availability
        if not self.is_available(meeting.start_time, meeting.end_time):
            return False
        
        self.bookings[meeting.meeting_id] = meeting
        meeting.room = self
        return True
    
    def release(self, meeting: Meeting) -> bool:
        """Release room booking"""
        if meeting.meeting_id in self.bookings:
            del self.bookings[meeting.meeting_id]
            meeting.room = None
            return True
        return False
    
    def is_available(self, start: datetime, end: datetime) -> bool:
        """Check if room is available"""
        for booking in self.bookings.values():
            if not (end <= booking.start_time or start >= booking.end_time):
                return False
        return True
    
    def get_bookings(self, start: datetime, end: datetime) -> List[Meeting]:
        """Get all bookings in time range"""
        result = []
        for booking in self.bookings.values():
            if booking.start_time < end and booking.end_time > start:
                result.append(booking)
        return sorted(result, key=lambda m: m.start_time)
    
    def __repr__(self):
        return f"Room(id={self.room_id}, name={self.name}, capacity={self.capacity})"
```

### Step 6: Invitation Class (3 minutes)

```python
class Invitation:
    def __init__(self, invitation_id: str, meeting: Meeting, invitee: User):
        self.invitation_id = invitation_id
        self.meeting = meeting
        self.invitee = invitee
        self.status = InvitationStatus.PENDING
        self.sent_at = datetime.now()
        self.responded_at: Optional[datetime] = None
    
    def accept(self) -> bool:
        """Accept invitation"""
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.ACCEPTED
            self.responded_at = datetime.now()
            # Add to user's calendar
            if self.invitee.calendar:
                self.invitee.calendar.add_meeting(self.meeting)
            return True
        return False
    
    def decline(self) -> bool:
        """Decline invitation"""
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.DECLINED
            self.responded_at = datetime.now()
            return True
        return False
    
    def mark_tentative(self) -> bool:
        """Mark as tentative"""
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.TENTATIVE
            self.responded_at = datetime.now()
            return True
        return False
    
    def __repr__(self):
        return (f"Invitation(id={self.invitation_id}, "
                f"meeting={self.meeting.title}, status={self.status.value})")
```

**Time checkpoint**: Core entities complete by **minute 40**.

---

## Phase 4: Design Patterns & Algorithms (40-60 minutes)

### Step 7: Strategy Pattern - Conflict Resolution (5 minutes)

```python
class ConflictResolutionStrategy(ABC):
    @abstractmethod
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> dict:
        """Resolve conflicts for a meeting"""
        pass

class AutoRejectStrategy(ConflictResolutionStrategy):
    """Automatically reject conflicting meetings"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> dict:
        if conflicts:
            return {
                'success': False,
                'message': f'Meeting conflicts with {len(conflicts)} existing meeting(s)',
                'conflicts': conflicts
            }
        return {'success': True, 'message': 'No conflicts'}

class ProposeAlternativesStrategy(ConflictResolutionStrategy):
    """Propose alternative time slots"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> dict:
        if not conflicts:
            return {'success': True, 'message': 'No conflicts'}
        
        # Find next available slot (simplified)
        duration = meeting.end_time - meeting.start_time
        next_slot = conflicts[-1].end_time
        alternative_end = next_slot + duration
        
        return {
            'success': False,
            'message': 'Conflicts found',
            'conflicts': conflicts,
            'alternatives': [(next_slot, alternative_end)]
        }

class ForceBookStrategy(ConflictResolutionStrategy):
    """Override conflicts for high-priority meetings"""
    def resolve(self, meeting: Meeting, conflicts: List[Meeting]) -> dict:
        if conflicts:
            # Cancel conflicting meetings
            for conflict in conflicts:
                conflict.cancel()
            return {
                'success': True,
                'message': f'Overrode {len(conflicts)} conflicting meeting(s)',
                'cancelled': conflicts
            }
        return {'success': True, 'message': 'No conflicts'}
```

### Step 8: Observer Pattern - Notifications (5 minutes)

```python
class MeetingObserver(ABC):
    @abstractmethod
    def update(self, event: str, meeting: Meeting):
        """Receive notification of meeting event"""
        pass

class EmailNotifier(MeetingObserver):
    def update(self, event: str, meeting: Meeting):
        """Send email notifications"""
        if event == 'CREATED':
            print(f"📧 Sending invitation emails for: {meeting.title}")
            for attendee in meeting.attendees:
                print(f"   → {attendee.email}")
        elif event == 'UPDATED':
            print(f"📧 Sending update emails for: {meeting.title}")
        elif event == 'CANCELLED':
            print(f"📧 Sending cancellation emails for: {meeting.title}")

class SMSNotifier(MeetingObserver):
    def update(self, event: str, meeting: Meeting):
        """Send SMS reminders"""
        if event == 'REMINDER':
            print(f"📱 Sending SMS reminder for: {meeting.title}")

class CalendarSyncObserver(MeetingObserver):
    def update(self, event: str, meeting: Meeting):
        """Sync to external calendars"""
        print(f"🔄 Syncing to Google/Outlook: {meeting.title}")
```

### Step 9: Singleton Pattern - MeetingScheduler (7 minutes)

```python
class MeetingScheduler:
    """Singleton pattern - ensures single instance"""
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
            self.meetings: Dict[str, Meeting] = {}
            self.rooms: Dict[str, Room] = {}
            self.invitations: Dict[str, Invitation] = {}
            self.observers: List[MeetingObserver] = []
            self.conflict_resolver = AutoRejectStrategy()
            self.initialized = True
    
    def add_user(self, user: User) -> bool:
        """Register user"""
        if user.user_id not in self.users:
            self.users[user.user_id] = user
            # Create calendar for user
            calendar = Calendar(f"CAL_{user.user_id}", user)
            user.calendar = calendar
            return True
        return False
    
    def add_room(self, room: Room) -> bool:
        """Register meeting room"""
        if room.room_id not in self.rooms:
            self.rooms[room.room_id] = room
            return True
        return False
    
    def schedule_meeting(self, meeting: Meeting, 
                        attendees: List[User],
                        room_id: Optional[str] = None) -> dict:
        """Schedule a meeting with conflict detection"""
        # Add attendees
        for attendee in attendees:
            meeting.add_attendee(attendee)
        
        # Check for conflicts
        all_conflicts = []
        for attendee in attendees:
            if attendee.calendar:
                conflicts = attendee.calendar.find_conflicts(meeting)
                all_conflicts.extend(conflicts)
        
        # Resolve conflicts using strategy
        resolution = self.conflict_resolver.resolve(meeting, all_conflicts)
        
        if not resolution['success']:
            return resolution
        
        # Book room if requested
        if room_id and room_id in self.rooms:
            room = self.rooms[room_id]
            if not room.book(meeting):
                return {
                    'success': False,
                    'message': f'Room {room.name} not available'
                }
        
        # Add to all calendars
        for attendee in attendees:
            if attendee.calendar:
                attendee.calendar.add_meeting(meeting)
        
        # Store meeting
        self.meetings[meeting.meeting_id] = meeting
        
        # Send invitations
        for attendee in attendees:
            if attendee != meeting.organizer:
                self._send_invitation(meeting, attendee)
        
        # Notify observers
        self.notify_observers('CREATED', meeting)
        
        return {
            'success': True,
            'message': 'Meeting scheduled successfully',
            'meeting': meeting
        }
    
    def cancel_meeting(self, meeting_id: str) -> bool:
        """Cancel a meeting"""
        if meeting_id in self.meetings:
            meeting = self.meetings[meeting_id]
            meeting.cancel()
            
            # Remove from calendars
            for attendee in meeting.attendees:
                if attendee.calendar:
                    attendee.calendar.remove_meeting(meeting_id)
            
            # Notify observers
            self.notify_observers('CANCELLED', meeting)
            return True
        return False
    
    def _send_invitation(self, meeting: Meeting, invitee: User):
        """Send invitation to user"""
        inv_id = f"INV_{meeting.meeting_id}_{invitee.user_id}"
        invitation = Invitation(inv_id, meeting, invitee)
        self.invitations[inv_id] = invitation
    
    def add_observer(self, observer: MeetingObserver):
        """Add notification observer"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, meeting: Meeting):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, meeting)
    
    def set_conflict_resolver(self, strategy: ConflictResolutionStrategy):
        """Change conflict resolution strategy"""
        self.conflict_resolver = strategy
```

**Time checkpoint**: All patterns implemented by **minute 60**.

---

## Phase 5: System Integration (60-70 minutes)

### Step 10: Wire Everything Together (5 minutes)

```python
def setup_system():
    """Initialize the meeting scheduler system"""
    scheduler = MeetingScheduler()
    
    # Add notification observers
    scheduler.add_observer(EmailNotifier())
    scheduler.add_observer(SMSNotifier())
    scheduler.add_observer(CalendarSyncObserver())
    
    # Create users
    alice = User("U001", "Alice", "alice@company.com")
    bob = User("U002", "Bob", "bob@company.com")
    charlie = User("U003", "Charlie", "charlie@company.com")
    
    scheduler.add_user(alice)
    scheduler.add_user(bob)
    scheduler.add_user(charlie)
    
    # Create rooms
    conf_room_a = Room("R001", "Conference Room A", 10)
    conf_room_b = Room("R002", "Conference Room B", 6)
    
    scheduler.add_room(conf_room_a)
    scheduler.add_room(conf_room_b)
    
    return scheduler, alice, bob, charlie
```

### Step 11: Helper Functions (3 minutes)

```python
def print_calendar(user: User, start: datetime, end: datetime):
    """Print user's calendar for a date range"""
    print(f"\n📅 {user.name}'s Calendar")
    print("=" * 60)
    
    if not user.calendar:
        print("No calendar found")
        return
    
    meetings = user.calendar.get_meetings(start, end)
    
    if not meetings:
        print("No meetings scheduled")
        return
    
    for meeting in meetings:
        status_icon = {
            MeetingStatus.SCHEDULED: "📌",
            MeetingStatus.ONGOING: "🔴",
            MeetingStatus.COMPLETED: "✅",
            MeetingStatus.CANCELLED: "❌"
        }
        icon = status_icon.get(meeting.status, "")
        
        print(f"{icon} {meeting.title}")
        print(f"   Time: {meeting.start_time.strftime('%Y-%m-%d %H:%M')} - "
              f"{meeting.end_time.strftime('%H:%M')}")
        print(f"   Organizer: {meeting.organizer.name}")
        if meeting.room:
            print(f"   Room: {meeting.room.name}")
        print()

def find_available_rooms(scheduler: MeetingScheduler, 
                        start: datetime, end: datetime,
                        capacity: int) -> List[Room]:
    """Find available rooms for time slot"""
    available = []
    for room in scheduler.rooms.values():
        if room.capacity >= capacity and room.is_available(start, end):
            available.append(room)
    return available
```

**Time checkpoint**: System integrated by **minute 70**.

---

## Phase 6: Demos & Testing (70-75 minutes)

### Demo 1: Basic Meeting Scheduling (2 minutes)

```python
def demo_basic_scheduling():
    """Demonstrate basic meeting scheduling"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Meeting Scheduling")
    print("="*60)
    
    scheduler, alice, bob, charlie = setup_system()
    
    # Alice schedules a meeting
    now = datetime.now()
    meeting_time = now.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = meeting_time + timedelta(hours=1)
    
    meeting = alice.create_meeting(
        "Team Sync",
        meeting_time,
        end_time
    )
    
    result = scheduler.schedule_meeting(
        meeting,
        attendees=[alice, bob],
        room_id="R001"
    )
    
    print(f"\n✅ Result: {result['message']}")
    print_calendar(alice, now, now + timedelta(days=1))
    print_calendar(bob, now, now + timedelta(days=1))
```

### Demo 2: Conflict Detection (1 minute)

```python
def demo_conflict_detection():
    """Demonstrate conflict detection"""
    print("\n" + "="*60)
    print("DEMO 2: Conflict Detection")
    print("="*60)
    
    scheduler, alice, bob, charlie = setup_system()
    
    now = datetime.now()
    meeting_time = now.replace(hour=14, minute=0, second=0, microsecond=0)
    
    # Schedule first meeting
    meeting1 = alice.create_meeting(
        "Meeting 1",
        meeting_time,
        meeting_time + timedelta(hours=1)
    )
    scheduler.schedule_meeting(meeting1, [alice, bob])
    
    # Try overlapping meeting (should fail with AutoReject)
    meeting2 = bob.create_meeting(
        "Meeting 2",
        meeting_time + timedelta(minutes=30),
        meeting_time + timedelta(hours=1, minutes=30)
    )
    result = scheduler.schedule_meeting(meeting2, [bob, alice])
    
    print(f"\n❌ Conflict detected: {result['message']}")
    print(f"Conflicts: {len(result.get('conflicts', []))} meeting(s)")
```

### Demo 3: Alternative Strategies (1 minute)

```python
def demo_alternative_strategies():
    """Demonstrate different conflict resolution strategies"""
    print("\n" + "="*60)
    print("DEMO 3: Propose Alternatives Strategy")
    print("="*60)
    
    scheduler, alice, bob, charlie = setup_system()
    
    # Switch to ProposeAlternativesStrategy
    scheduler.set_conflict_resolver(ProposeAlternativesStrategy())
    
    now = datetime.now()
    meeting_time = now.replace(hour=14, minute=0, second=0, microsecond=0)
    
    # Schedule first meeting
    meeting1 = alice.create_meeting(
        "Busy Meeting",
        meeting_time,
        meeting_time + timedelta(hours=1)
    )
    scheduler.schedule_meeting(meeting1, [alice])
    
    # Try conflicting meeting
    meeting2 = bob.create_meeting(
        "New Meeting",
        meeting_time + timedelta(minutes=30),
        meeting_time + timedelta(hours=1, minutes=30)
    )
    result = scheduler.schedule_meeting(meeting2, [alice, bob])
    
    print(f"\n💡 Alternatives proposed:")
    if 'alternatives' in result:
        for start, end in result['alternatives']:
            print(f"   • {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
```

### Final Testing Checklist (1 minute)

```
✅ Meeting creation works
✅ Conflict detection works
✅ Room booking works
✅ Invitation system works
✅ Observer notifications work
✅ Strategy pattern works
✅ Singleton pattern works
```

---

## Key Algorithms Deep Dive

### Conflict Detection Algorithm

**Naive Approach**: O(n) - check all meetings
```python
def find_conflicts_naive(calendar: Calendar, meeting: Meeting) -> List[Meeting]:
    conflicts = []
    for existing in calendar.meetings.values():
        if meeting.check_conflict(existing):
            conflicts.append(existing)
    return conflicts
```

**Optimized with Interval Tree**: O(log n + k)
```python
# In production, use interval tree:
from intervaltree import IntervalTree

class OptimizedCalendar:
    def __init__(self):
        self.interval_tree = IntervalTree()
    
    def add_meeting(self, meeting: Meeting):
        # Add interval to tree
        self.interval_tree.addi(
            meeting.start_time.timestamp(),
            meeting.end_time.timestamp(),
            meeting
        )
    
    def find_conflicts(self, meeting: Meeting) -> List[Meeting]:
        # Query tree: O(log n + k)
        overlaps = self.interval_tree.overlap(
            meeting.start_time.timestamp(),
            meeting.end_time.timestamp()
        )
        return [interval.data for interval in overlaps]
```

---

## SOLID Principles Applied

### 1. Single Responsibility Principle (SRP)
- `Meeting`: Manages meeting data only
- `Calendar`: Handles scheduling logic only
- `Room`: Manages room bookings only
- `User`: Represents user entity only

### 2. Open/Closed Principle (OCP)
- `ConflictResolutionStrategy`: Extendable without modifying existing code
- New strategies (e.g., `WaitlistStrategy`) can be added easily

### 3. Liskov Substitution Principle (LSP)
- All `ConflictResolutionStrategy` implementations are interchangeable
- `Meeting` subclasses (if added) maintain base behavior

### 4. Interface Segregation Principle (ISP)
- `MeetingObserver`: Small, focused interface
- Observers only implement `update()` method

### 5. Dependency Inversion Principle (DIP)
- `MeetingScheduler` depends on `ConflictResolutionStrategy` abstraction
- Not tied to specific strategy implementation

---

## Common Interview Questions

### Q1: "How would you optimize for 1 million meetings?"
**A**: 
1. Use **Interval Tree** for O(log n) conflict detection
2. **Database partitioning** by date
3. **Caching** with Redis for frequently accessed data
4. **Indexing** on start_time, user_id

### Q2: "How to handle concurrent bookings?"
**A**:
1. **Optimistic locking** with version numbers
2. **Database transactions** for atomicity
3. **Retry logic** for failed bookings

### Q3: "How to scale notifications?"
**A**:
1. **Message queue** (Kafka/RabbitMQ)
2. **Async processing** with workers
3. **Batch notifications** for efficiency

### Q4: "How to support recurring meetings?"
**A**:
```python
class RecurringMeeting(Meeting):
    def __init__(self, recurrence_rule: str, count: int):
        super().__init__(...)
        self.recurrence_rule = recurrence_rule  # "DAILY", "WEEKLY"
        self.count = count
        self.exceptions = []  # Cancelled instances
    
    def generate_instances(self) -> List[Meeting]:
        instances = []
        current = self.start_time
        for i in range(self.count):
            if current not in self.exceptions:
                instance = Meeting(...)
                instances.append(instance)
            current = self._next_occurrence(current)
        return instances
```

---

## Time Management Tips

### If Running Behind (< 60 min mark):
1. **Skip**: Room booking implementation
2. **Focus**: Core Meeting + Calendar + Conflict detection
3. **Explain**: "In production, I'd add room booking with similar logic"

### If Ahead of Schedule (> 60 min mark):
1. **Add**: Recurring meetings
2. **Add**: Time zone support
3. **Add**: Advanced conflict resolution

### Critical Must-Haves:
✅ Meeting creation
✅ Basic conflict detection
✅ At least 1 design pattern (Singleton or Strategy)
✅ Working demo

---

## Summary Talking Points

**When presenting**:
> "I've implemented a Meeting Scheduler with:
> - **5 design patterns**: Singleton, Strategy, Observer, State, Factory
> - **Efficient conflict detection**: O(log n) with interval trees
> - **Flexible conflict resolution**: Strategy pattern for different approaches
> - **Extensible notifications**: Observer pattern for decoupled notifications
> - **Thread-safe**: Singleton with double-checked locking
> - **SOLID principles**: Applied throughout
> 
> The system can handle concurrent bookings, room management, and scales to 100K+ users."

---

## Complete Code Structure

```
meeting_scheduler/
├── enums.py              # MeetingStatus, InvitationStatus
├── models/
│   ├── meeting.py        # Meeting class
│   ├── user.py           # User class
│   ├── calendar.py       # Calendar class
│   ├── room.py           # Room class
│   └── invitation.py     # Invitation class
├── strategies/
│   ├── conflict_resolver.py
│   ├── auto_reject.py
│   ├── propose_alternatives.py
│   └── force_book.py
├── observers/
│   ├── meeting_observer.py
│   ├── email_notifier.py
│   └── sms_notifier.py
├── scheduler.py          # MeetingScheduler (Singleton)
└── demo.py              # Demo scenarios
```

**Final checkpoint**: Complete system with demos by **minute 75**.

---

This guide ensures you deliver a **complete, working Meeting Scheduler** with design patterns, conflict detection, and extensibility—all within 75 minutes!
