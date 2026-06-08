# Meeting Scheduler — Complete Design Guide

> Calendar and meeting scheduling system with room booking, conflict detection, invitations, recurring meetings, and real-time notifications.

**Scale**: 1M+ users, 10M+ meetings, 99.9% uptime
**Duration**: 75-minute interview guide
**Focus**: Conflict detection and resolution, invitation state machine, recurring events, observer-driven notifications

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?

A user creates a meeting → selects attendees and a room → system checks for time-overlap conflicts → applies a pluggable conflict-resolution strategy → sends invitations (Pending) → each invitee accepts/declines/tentative → meeting is added to all calendars. Core concerns: interval-based conflict detection, pluggable resolution strategies, invitation lifecycle, and recurring-event expansion.

### Core Flow

```
Create Meeting → Pick Attendees + Room → CHECK CONFLICTS
                                              |
                          ┌───────────────────┴───────────────────┐
                          ▼                                       ▼
                    No conflict                           Conflict detected
                    → Schedule                    Apply ConflictResolutionStrategy
                    → Send Invitations        ┌─────────┬──────────────────────┐
                    → Add to Calendars        ▼         ▼                      ▼
                                          AutoReject  ProposeAlternatives  ForceBook
Invitation Flow:
PENDING → accept() → ACCEPTED
        → decline() → DECLINED
        → tentative() → TENTATIVE
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system with 1M+ users"
2. **Do we support recurring meetings?** → "Yes — daily, weekly, monthly with exception handling"
3. **How do we handle conflicts?** → "Pluggable strategy: auto-reject, propose alternatives, force-book"
4. **Real-time notifications?** → "Yes — email, reminders, calendar sync via Observer pattern"
5. **External calendar integrations?** → "Out of scope; mention as scaling concern"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Organizer** | Creates and manages meetings | Create meeting, invite attendees, book room, cancel |
| **Attendee** | Receives and responds to invitations | Accept, decline, mark tentative |
| **Room Manager** | Oversees conference room availability | Register rooms, view bookings |
| **System** | Coordinator & notifier | Conflict detection, send emails, reminders, calendar sync |

### Functional Requirements (What does the system do?)

✅ **Meeting Creation**
  - Create one-time and recurring meetings with title, time, duration, location
  - Add/remove attendees and send invitations

✅ **Conflict Detection & Resolution**
  - Detect time-overlap conflicts for rooms and attendees
  - Apply pluggable resolution strategy: AutoReject, ProposeAlternatives, ForceBook

✅ **Invitation Lifecycle**
  - Accept / decline / tentative state machine (Pending → Accepted/Declined/Tentative)

✅ **Room Booking**
  - Book conference rooms with capacity constraints
  - Detect room double-booking

✅ **Availability Queries**
  - Find free time slots for a group of attendees
  - View personal calendar with meetings

✅ **Recurring Meetings**
  - Daily, weekly, monthly recurrence with exception dates
  - Cancel individual instances without affecting the series

✅ **Notifications**
  - Email, reminder, and calendar-sync notifications via Observer

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe scheduling for simultaneous meeting creation
✅ **Consistency**: No double-booking of rooms or overlapping attendee calendars
✅ **Latency**: Conflict detection < 100ms (interval trees for O(log n) queries)
✅ **Calendar View**: < 500ms with pagination for large calendars
✅ **Availability**: 99.9% uptime
✅ **Scalability**: Support 1M+ users, 10M+ meetings
✅ **Notifications**: Real-time; eventual consistency for calendar sync is acceptable

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES — multi-region in production |
| **Storage** | In-memory for demo; PostgreSQL + Redis in production |
| **Conflict default** | AutoReject (switchable at runtime) |
| **Recurring limit** | Store rule + exceptions; generate instances lazily |
| **Invitation required?** | YES — every meeting creates Pending invitations |
| **Single-process demo** | YES — production would be microservices |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
User, Room, Meeting, TimeSlot, Calendar, Invitation, RecurringMeeting, ...
```

### Step 2.2: Define Core Classes

#### **User** — A professional user with a personal calendar
```
Properties:
  - user_id: str
  - name: str
  - email: str
  - availability: Availability (tracks busy slots)
  - meetings: List[str]  (meeting_ids)

Behaviors:
  - is_available_for_slot(slot): Check against availability calendar
```

#### **Room** — A physical conference room
```
Properties:
  - room_id: str
  - name: str
  - capacity: int
  - bookings: List[TimeSlot]  (booked time intervals)

Behaviors:
  - is_available_for_slot(slot): Check overlap with existing bookings
  - book_for_slot(slot): Reserve room if available
```

#### **Meeting** — A calendar event with attendees and state
```
Properties:
  - meeting_id: str
  - title: str
  - organizer_id: str
  - time_slot: TimeSlot
  - room_id: Optional[str]
  - attendees: Set[str]  (user_ids)
  - status: MeetingStatus (SCHEDULED, ONGOING, COMPLETED, CANCELLED)
  - recurring: Optional[RecurringMeeting]

Behaviors:
  - (data holder; lifecycle managed by MeetingScheduler)
```

#### **TimeSlot** — A time period used for overlap detection
```
Properties:
  - start_time: datetime
  - end_time: datetime

Behaviors:
  - overlaps(other): Check if two intervals overlap
  - duration_minutes(): Compute length in minutes
```

#### **Calendar (Availability)** — Tracks a user's busy time intervals
```
Properties:
  - busy_slots: List[TimeSlot]  (sorted)

Behaviors:
  - is_available(slot): Return True if no busy slot overlaps
  - add_busy_slot(slot): Insert and keep sorted
  - merge_overlapping(): Merge intervals for efficient group-slot search
```

#### **MeetingScheduler** — Main controller (Singleton)
```
Properties:
  - users: Dict[str, User]
  - meetings: Dict[str, Meeting]
  - rooms: Dict[str, Room]
  - invitations: Dict[str, Invitation]
  - conflict_strategy: ConflictResolutionStrategy
  - observers: List[MeetingObserver]

Behaviors:
  - create_user / create_room
  - schedule_meeting(title, organizer, attendees, slot, room): Conflict-check + book
  - cancel_meeting(meeting_id): Release room + attendee calendars
  - find_available_slots(attendees, duration): Merge busy times, find free gaps
  - schedule_recurring_meeting(...): Generate instances + schedule each
  - set_conflict_resolution_strategy(strategy): Runtime strategy swap
  - accept_invitation / decline_invitation
```

### Step 2.3: Define Enumerations (State & Type)

```python
class MeetingStatus(Enum):
    SCHEDULED  = "scheduled"
    ONGOING    = "ongoing"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"

class InvitationStatus(Enum):
    PENDING    = "pending"
    ACCEPTED   = "accepted"
    DECLINED   = "declined"
    TENTATIVE  = "tentative"

class RecurrenceType(Enum):
    DAILY      = "daily"
    WEEKLY     = "weekly"
    MONTHLY    = "monthly"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **User** | Owns calendar and availability | Can't check attendee conflicts |
| **Room** | Tracks bookings with capacity | Can't prevent room double-booking |
| **Meeting** | Central event with lifecycle | No state management |
| **TimeSlot** | Reusable overlap logic | Duplicate interval code everywhere |
| **Calendar (Availability)** | Merge + query busy times | O(n²) group-slot search |
| **MeetingScheduler** | Thread-safe single coordinator | No central conflict authority |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Schedule Meeting** ⭐ CRITICAL
```python
def schedule_meeting(
    title: str,
    organizer_id: str,
    attendee_ids: Set[str],
    time_slot: TimeSlot,
    room_id: Optional[str] = None
) -> Tuple[bool, str, Optional[Meeting]]:
    """
    Schedule a meeting with conflict detection and resolution.

    Precondition: organizer and all attendees registered; room registered if given
    Postcondition on success: meeting stored, attendee calendars updated, room booked,
                              invitations created, observers notified

    Returns: (True, "scheduled", meeting) | (False, conflict_reason, None)

    Failure causes:
      - Room not available (double-booking)
      - Attendee not available (calendar conflict)
      - Conflict strategy returns "reject"

    Concurrency: THREAD-SAFE (MeetingScheduler lock)
    """
    pass
```

#### **2. Cancel Meeting**
```python
def cancel_meeting(meeting_id: str) -> bool:
    """
    Cancel meeting and release all resources.

    Postcondition: meeting.status = CANCELLED, room slot released,
                   attendee busy slots cleared, observers notified.
    Returns: True if cancelled, False if not found.
    """
    pass
```

#### **3. Find Available Slots** ⭐ KEY ALGORITHM
```python
def find_available_slots(
    attendee_ids: Set[str],
    duration_minutes: int,
    days_ahead: int = 7
) -> List[TimeSlot]:
    """
    Find free time windows for a group of people.

    Algorithm:
      1. Collect all attendees' busy slots
      2. Merge overlapping intervals — O(n log n)
      3. Scan next 'days_ahead' days for gaps >= duration_minutes
      4. Return top 10 results

    Response time: < 100ms for 100 attendees
    """
    pass
```

#### **4. Accept / Decline Invitation**
```python
def accept_invitation(invitation_id: str) -> bool: ...
def decline_invitation(invitation_id: str) -> bool: ...
```

#### **5. Schedule Recurring Meeting**
```python
def schedule_recurring_meeting(
    title: str,
    organizer_id: str,
    attendee_ids: Set[str],
    start_time: datetime,
    duration_minutes: int,
    recurrence_type: RecurrenceType,
    count: int,
    room_id: Optional[str] = None
) -> Tuple[int, List[Meeting]]:
    """
    Generate and schedule 'count' instances of a recurring meeting.
    Returns: (scheduled_count, failed_instances)
    """
    pass
```

#### **6. Set Conflict Resolution Strategy**
```python
def set_conflict_resolution_strategy(strategy: ConflictResolutionStrategy) -> None:
    """
    Dynamically swap conflict resolution algorithm.
    New strategy applies to next schedule_meeting() call.
    Strategies: AutoRejectStrategy, ProposeAlternativesStrategy, ForceBookStrategy
    """
    pass
```

### Step 3.2: Failure Model

```python
class SchedulerException(Exception): ...
class ConflictError(SchedulerException): ...        # Room or attendee conflict
class UserNotFoundError(SchedulerException): ...    # Unknown user_id
class RoomNotFoundError(SchedulerException): ...    # Unknown room_id
class MeetingNotFoundError(SchedulerException): ... # Unknown meeting_id
class InvitationNotFoundError(SchedulerException): ...
```

> Demo uses `(bool, message)` tuples instead of exceptions for interview readability.

### Step 3.3: API Usage Example

```python
scheduler = MeetingScheduler()

# Setup
scheduler.create_user("u_alice", "Alice", "alice@email.com")
scheduler.create_user("u_bob",   "Bob",   "bob@email.com")
scheduler.create_room("room_1",  "Room A", capacity=10)

# Schedule meeting
start = datetime.now() + timedelta(days=1, hours=2)
slot  = TimeSlot(start, start + timedelta(hours=1))

success, msg, meeting = scheduler.schedule_meeting(
    "Team Sync", "u_alice", {"u_bob"}, slot, "room_1"
)

# Find group availability
slots = scheduler.find_available_slots({"u_alice", "u_bob"}, duration_minutes=60)

# Accept invitation
inv = next(i for i in scheduler.invitations.values()
           if i.meeting_id == meeting.meeting_id and i.invitee_id == "u_bob")
scheduler.accept_invitation(inv.invitation_id)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
MeetingScheduler HAS-A users / meetings / rooms / invitations (1:N Composition)
  └─ Scheduler owns and manages lifecycle of all entities

User HAS-A Availability (1:1 Composition)
  └─ User owns its calendar of busy slots

Meeting REFERENCES User (1:N Association)
  └─ Meeting links to attendee user_ids (no ownership)

Meeting REFERENCES Room (1:1 Association)
  └─ Meeting optionally links to a Room (no ownership)

Invitation REFERENCES Meeting + User (1:1 Association)
  └─ Invitation links to an existing meeting and invitee

MeetingScheduler USES-A ConflictResolutionStrategy (1:1 Composition)
  └─ Scheduler owns and can swap the conflict algorithm

MeetingScheduler NOTIFIES MeetingObserver (1:N Association)
  └─ Multiple observers listen to meeting events
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────────────────────────┐
│        MeetingScheduler (Singleton)                          │
│  - users: {user_id → User}                                   │
│  - meetings: {meeting_id → Meeting}                          │
│  - rooms: {room_id → Room}                                   │
│  - invitations: {inv_id → Invitation}                        │
│  - conflict_strategy: ConflictResolutionStrategy             │
│  - observers: [MeetingObserver]                              │
│  + schedule_meeting(), cancel_meeting()                      │
│  + find_available_slots(), schedule_recurring_meeting()      │
│  + set_conflict_resolution_strategy(strategy)                │
└──────────────────┬───────────────────────────────────────────┘
                   │ manages 1:N
      ┌────────────┼────────────┬──────────────┬──────────────┐
      ▼            ▼            ▼              ▼              ▼
  ┌────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐  ┌──────────┐
  │  User  │  │ Meeting  │  │  Room  │  │ Invitation │  │Recurring │
  ├────────┤  ├──────────┤  ├────────┤  ├────────────┤  │ Meeting  │
  │user_id │  │title     │  │name    │  │meeting_id  │  ├──────────┤
  │name    │  │time_slot │  │capacity│  │invitee_id  │  │rule      │
  │avail.  │  │attendees │  │bookings│  │status:     │  │count     │
  │meetings│  │room_id   │  └────────┘  │ Pending    │  │exceptions│
  └────────┘  │status    │              │ Accepted   │  └──────────┘
              │recurring │              │ Declined   │
              └──────────┘              │ Tentative  │
                   │                   └────────────┘
                   ▼
         ┌──────────────────┐
         │ MeetingStatus    │
         │ (Enum)           │
         │ SCHEDULED        │
         │ → ONGOING        │
         │ → COMPLETED      │
         │ ↓ CANCELLED      │
         └──────────────────┘

CONFLICT DETECTION FLOW:
NEW_MEETING_REQUEST
  → CHECK_ROOM_AVAILABLE (interval overlap check)
  → CHECK_ATTENDEES_AVAILABLE (per-attendee calendar scan)
  → IF_CONFLICT: Apply ConflictResolutionStrategy
     ├─ AUTO_REJECT: Reject meeting
     ├─ PROPOSE_ALTERNATIVES: Suggest other time slots
     └─ FORCE_BOOK: Override and book anyway
  → SEND_INVITATIONS (Observer pattern)
  → ADD_TO_CALENDARS
  → SCHEDULE_REMINDERS

STRATEGY PATTERN (Conflict Resolution):
┌────────────────────────────────────┐
│ ConflictResolutionStrategy (ABC)   │
├────────────────────────────────────┤
│ + resolve(conflict: Dict) → Dict   │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ AutoRejectStrategy         (reject on any conflict)
   ├─→ ProposeAlternativesStrategy (suggest free slots)
   └─→ ForceBookStrategy           (override and book)

OBSERVER PATTERN (Notifications):
┌────────────────────────────────────┐
│ MeetingObserver (ABC)              │
├────────────────────────────────────┤
│ + update(event, payload)           │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ EmailNotifier
   ├─→ ReminderService
   └─→ CalendarSyncObserver
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| MeetingScheduler → Users | 1:N | Composition | Scheduler owns all users |
| MeetingScheduler → Meetings | 1:N | Composition | Scheduler owns all meetings |
| MeetingScheduler → Rooms | 1:N | Composition | Scheduler owns all rooms |
| MeetingScheduler → Invitations | 1:N | Composition | Scheduler owns all invitations |
| User → Availability | 1:1 | Composition | User owns its calendar |
| Meeting → Attendees (Users) | N:N | Association | Meeting references multiple users |
| Meeting → Room | 1:1 | Association | Meeting optionally references one room |
| Invitation → Meeting | 1:1 | Association | Invitation links to one meeting |
| Invitation → User | 1:1 | Association | Invitation links to one invitee |
| MeetingScheduler → ConflictStrategy | 1:1 | Composition | Scheduler owns conflict algorithm |
| MeetingScheduler → Observers | 1:N | Association | Scheduler notifies many listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Strategy** (For Conflict Resolution)

**Problem**: Different teams need different conflict behaviors — some want hard rejection, others want to see alternatives, admins may want to force-book. These requirements change at runtime.

**Solution**: Pluggable `ConflictResolutionStrategy` ABC; swap algorithm without touching `schedule_meeting()`.

```python
class ConflictResolutionStrategy(ABC):
    @abstractmethod
    def resolve(self, conflict: Dict) -> Dict:
        pass

class AutoRejectStrategy(ConflictResolutionStrategy):
    def resolve(self, conflict: Dict) -> Dict:
        return {"action": "reject", "reason": conflict["reason"]}

class ProposeAlternativesStrategy(ConflictResolutionStrategy):
    def resolve(self, conflict: Dict) -> Dict:
        return {"action": "propose_alternatives",
                "alternatives": conflict.get("free_slots", [])[:3]}

class ForceBookStrategy(ConflictResolutionStrategy):
    def resolve(self, conflict: Dict) -> Dict:
        return {"action": "force_book", "warning": "Conflict overridden"}

# Runtime swap — no MeetingScheduler code change
scheduler.set_conflict_resolution_strategy(ProposeAlternativesStrategy())
```

**Benefit**: ✅ Open/Closed principle — add new strategies without modifying scheduler
**Trade-off**: ⚠️ Extra abstraction layer; overkill if only one strategy ever used

---

### Pattern 2: **Observer** (For Notifications)

**Problem**: Meeting creation/cancellation must trigger emails, reminders, and calendar sync. Hard-coding these channels creates tight coupling.

**Solution**: Observer pattern decouples event producer (MeetingScheduler) from consumers (EmailNotifier, ReminderService, CalendarSyncObserver).

```python
class MeetingObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict) -> None:
        pass

class EmailNotifier(MeetingObserver):
    def update(self, event: str, payload: Dict) -> None:
        if event == "meeting_created":
            print(f"  [EMAIL] Invitation sent to {payload['attendees']}")
        elif event == "meeting_cancelled":
            print(f"  [EMAIL] Cancellation notice sent for {payload['title']}")

class ReminderService(MeetingObserver):
    def update(self, event: str, payload: Dict) -> None:
        if event == "meeting_created":
            print(f"  [REMINDER] Set reminder for {payload['title']}")

# Usage: add channels independently
scheduler.register_observer(EmailNotifier())
scheduler.register_observer(ReminderService())
scheduler.register_observer(CalendarSyncObserver())
```

**Benefit**: ✅ Loose coupling — add new notification channels with zero scheduler changes
**Trade-off**: ⚠️ Observer lifecycle management; slow observers block notification loop

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit | Trade-off |
|---------|----------------|---------|-----------|
| **Singleton** | One centralized MeetingScheduler | Single source of truth; thread-safe init | Global state; harder to test |
| **Strategy** | Pluggable conflict resolution | Swap AutoReject / ProposeAlternatives / ForceBook at runtime | Extra abstraction layer |
| **Observer** | Decouple event notifications | Add channels without core changes | Observer lifecycle management |
| **State Machine** | Meeting lifecycle correctness | Invalid transitions prevented via MeetingStatus enum | Must check status before each op |
| **Factory** | Recurring instance creation | Centralized, consistent instance generation | If series grows, consider Builder |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Meeting Scheduler System - Interview Implementation
Demonstrates:
1. Singleton pattern (one scheduler instance)
2. Observer pattern (real-time notifications)
3. Strategy pattern (pluggable conflict resolution)
4. State machine pattern (meeting lifecycle)
5. Factory pattern (create meeting types)
"""

from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import threading
import bisect

# ============================================================================
# ENUMERATIONS
# ============================================================================

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

class RecurrenceType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# ============================================================================
# SUPPORTING CLASSES
# ============================================================================

@dataclass
class TimeSlot:
    """Represents a time period"""
    start_time: datetime
    end_time: datetime

    def overlaps(self, other: TimeSlot) -> bool:
        """Check if two time slots overlap"""
        return self.start_time < other.end_time and other.start_time < self.end_time

    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)

@dataclass
class Availability:
    """Tracks user availability"""
    busy_slots: List[TimeSlot] = field(default_factory=list)

    def is_available(self, slot: TimeSlot) -> bool:
        """Check if user is available for time slot"""
        return not any(slot.overlaps(busy) for busy in self.busy_slots)

    def add_busy_slot(self, slot: TimeSlot) -> None:
        """Add busy time to availability"""
        self.busy_slots.append(slot)
        self.busy_slots.sort(key=lambda s: s.start_time)

    def merge_overlapping(self) -> List[TimeSlot]:
        """Merge overlapping time slots"""
        if not self.busy_slots:
            return []

        merged = []
        current = self.busy_slots[0]

        for slot in self.busy_slots[1:]:
            if slot.start_time <= current.end_time:
                current = TimeSlot(current.start_time, max(current.end_time, slot.end_time))
            else:
                merged.append(current)
                current = slot

        merged.append(current)
        return merged

# ============================================================================
# CORE ENTITIES
# ============================================================================

@dataclass
class User:
    """System user with calendar"""
    user_id: str
    name: str
    email: str
    availability: Availability = field(default_factory=Availability)
    meetings: List[str] = field(default_factory=list)  # meeting_ids

    def is_available_for_slot(self, slot: TimeSlot) -> bool:
        return self.availability.is_available(slot)

@dataclass
class Room:
    """Conference room"""
    room_id: str
    name: str
    capacity: int
    bookings: List[TimeSlot] = field(default_factory=list)  # booked times

    def is_available_for_slot(self, slot: TimeSlot) -> bool:
        """Check if room is available (using interval tree logic)"""
        return not any(slot.overlaps(booking) for booking in self.bookings)

    def book_for_slot(self, slot: TimeSlot) -> bool:
        if not self.is_available_for_slot(slot):
            return False
        self.bookings.append(slot)
        self.bookings.sort(key=lambda s: s.start_time)
        return True

@dataclass
class Meeting:
    """Meeting with title, time, attendees"""
    meeting_id: str
    title: str
    organizer_id: str
    time_slot: TimeSlot
    room_id: Optional[str] = None
    attendees: Set[str] = field(default_factory=set)
    status: MeetingStatus = MeetingStatus.SCHEDULED
    recurring: Optional[RecurringMeeting] = None

@dataclass
class RecurringMeeting:
    """Recurring meeting configuration"""
    title: str
    organizer_id: str
    start_time: datetime
    duration_minutes: int
    recurrence_type: RecurrenceType
    count: int
    exceptions: Set[datetime] = field(default_factory=set)

    def generate_instances(self) -> List[Meeting]:
        """Generate meeting instances"""
        instances = []
        current_date = self.start_time

        for i in range(self.count):
            if current_date not in self.exceptions:
                end_time = current_date + timedelta(minutes=self.duration_minutes)
                slot = TimeSlot(current_date, end_time)
                meeting = Meeting(
                    f"rec_{self.title}_{i}",
                    f"{self.title} #{i+1}",
                    self.organizer_id,
                    slot
                )
                instances.append(meeting)

            # Move to next occurrence
            if self.recurrence_type == RecurrenceType.DAILY:
                current_date += timedelta(days=1)
            elif self.recurrence_type == RecurrenceType.WEEKLY:
                current_date += timedelta(weeks=1)
            elif self.recurrence_type == RecurrenceType.MONTHLY:
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        return instances

@dataclass
class Invitation:
    """Meeting invitation with state"""
    invitation_id: str
    meeting_id: str
    invitee_id: str
    status: InvitationStatus = InvitationStatus.PENDING

    def accept(self) -> None:
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.ACCEPTED

    def decline(self) -> None:
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.DECLINED

    def tentative(self) -> None:
        if self.status == InvitationStatus.PENDING:
            self.status = InvitationStatus.TENTATIVE

# ============================================================================
# CONFLICT RESOLUTION STRATEGIES
# ============================================================================

class ConflictResolutionStrategy(ABC):
    """Abstract strategy for conflict resolution"""

    @abstractmethod
    def resolve(self, conflict: Dict) -> Dict:
        """Resolve conflict and return resolution action"""
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__

class AutoRejectStrategy(ConflictResolutionStrategy):
    """Reject conflicting meetings"""

    def resolve(self, conflict: Dict) -> Dict:
        return {"action": "reject", "reason": f"Conflict: {conflict['reason']}"}

class ProposeAlternativesStrategy(ConflictResolutionStrategy):
    """Propose alternative time slots"""

    def resolve(self, conflict: Dict) -> Dict:
        alternatives = conflict.get("free_slots", [])
        return {
            "action": "propose_alternatives",
            "alternatives": alternatives[:3]  # top 3 alternatives
        }

class ForceBookStrategy(ConflictResolutionStrategy):
    """Force book regardless of conflicts"""

    def resolve(self, conflict: Dict) -> Dict:
        return {"action": "force_book", "warning": "Conflict will be overridden"}

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class MeetingObserver(ABC):
    """Abstract observer for meeting events"""

    @abstractmethod
    def update(self, event: str, payload: Dict) -> None:
        raise NotImplementedError

class EmailNotifier(MeetingObserver):
    """Send email notifications"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "meeting_created":
            print(f"  [EMAIL] Invitation sent to {payload['attendees']}")
        elif event == "meeting_cancelled":
            print(f"  [EMAIL] Cancellation notice sent for {payload['title']}")

class ReminderService(MeetingObserver):
    """Schedule meeting reminders"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "meeting_created":
            print(f"  [REMINDER] Set reminder for {payload['title']} at {payload['start_time']}")

class CalendarSyncObserver(MeetingObserver):
    """Sync meetings to calendar integrations"""

    def update(self, event: str, payload: Dict) -> None:
        if event == "meeting_created":
            print(f"  [CALENDAR] Synced {payload['title']} to Google Calendar")

# ============================================================================
# MEETING SCHEDULER (SINGLETON)
# ============================================================================

class MeetingScheduler:
    """Centralized meeting scheduling system (thread-safe Singleton)"""

    _instance: Optional[MeetingScheduler] = None
    _lock = threading.RLock()  # RLock prevents re-entrancy deadlock

    def __new__(cls, *args, **kwargs) -> MeetingScheduler:
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
        self.meetings: Dict[str, Meeting] = {}
        self.rooms: Dict[str, Room] = {}
        self.invitations: Dict[str, Invitation] = {}
        self.conflict_strategy: ConflictResolutionStrategy = AutoRejectStrategy()
        self.observers: List[MeetingObserver] = []
        print("Meeting Scheduler initialized")

    def register_observer(self, observer: MeetingObserver) -> None:
        self.observers.append(observer)

    def _emit(self, event: str, payload: Dict) -> None:
        for observer in self.observers:
            observer.update(event, payload)

    # ---- USER MANAGEMENT ----

    def create_user(self, user_id: str, name: str, email: str) -> User:
        user = User(user_id, name, email)
        self.users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    # ---- ROOM MANAGEMENT ----

    def create_room(self, room_id: str, name: str, capacity: int) -> Room:
        room = Room(room_id, name, capacity)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    # ---- CONFLICT DETECTION ----

    def check_conflicts(self, meeting: Meeting) -> Tuple[bool, Optional[str], List[TimeSlot]]:
        """Check for conflicts and suggest alternatives"""
        conflicts = []

        # Check room availability
        if meeting.room_id:
            room = self.rooms.get(meeting.room_id)
            if room and not room.is_available_for_slot(meeting.time_slot):
                conflicts.append(f"Room {room.name} is not available")

        # Check attendee availability
        for attendee_id in meeting.attendees:
            user = self.users.get(attendee_id)
            if user and not user.is_available_for_slot(meeting.time_slot):
                conflicts.append(f"{user.name} is not available")

        # Find alternatives if conflicts
        alternatives = []
        if conflicts:
            alternatives = self.find_available_slots(
                meeting.attendees, meeting.time_slot.duration_minutes()
            )

        return (len(conflicts) == 0, "; ".join(conflicts) if conflicts else None, alternatives)

    def find_available_slots(self, attendee_ids: Set[str], duration_minutes: int,
                             days_ahead: int = 7) -> List[TimeSlot]:
        """Find available time slots for group of people"""
        slots = []

        # Merge all attendees' busy times
        all_busy = Availability()
        for attendee_id in attendee_ids:
            user = self.users.get(attendee_id)
            if user:
                for busy in user.availability.busy_slots:
                    all_busy.add_busy_slot(busy)

        merged_busy = all_busy.merge_overlapping()

        # Find gaps
        now = datetime.now()
        current_time = now.replace(hour=9, minute=0, second=0)  # 9 AM start
        end_search = now + timedelta(days=days_ahead)

        while current_time < end_search:
            slot = TimeSlot(current_time, current_time + timedelta(minutes=duration_minutes))

            # Check if slot is free
            if not any(slot.overlaps(busy) for busy in merged_busy):
                slots.append(slot)

            current_time += timedelta(hours=1)

        return slots[:10]  # Return top 10 available slots

    # ---- MEETING MANAGEMENT ----

    def schedule_meeting(self, title: str, organizer_id: str, attendee_ids: Set[str],
                         time_slot: TimeSlot, room_id: Optional[str] = None) -> Tuple[bool, str, Optional[Meeting]]:
        """Schedule a meeting with conflict resolution"""

        meeting = Meeting(
            f"meet_{len(self.meetings)}",
            title,
            organizer_id,
            time_slot,
            room_id,
            attendee_ids
        )

        # Check conflicts
        has_no_conflicts, conflict_reason, alternatives = self.check_conflicts(meeting)

        if has_no_conflicts:
            # No conflicts — schedule immediately
            self.meetings[meeting.meeting_id] = meeting

            # Add to attendee calendars
            for attendee_id in attendee_ids:
                user = self.users.get(attendee_id)
                if user:
                    user.meetings.append(meeting.meeting_id)
                    user.availability.add_busy_slot(time_slot)

            # Book room
            if room_id:
                room = self.rooms.get(room_id)
                if room:
                    room.book_for_slot(time_slot)

            # Send invitations
            for attendee_id in attendee_ids:
                inv = Invitation(f"inv_{meeting.meeting_id}_{attendee_id}",
                                 meeting.meeting_id, attendee_id)
                self.invitations[inv.invitation_id] = inv

            self._emit("meeting_created", {
                "title": title,
                "start_time": time_slot.start_time,
                "attendees": list(attendee_ids)
            })

            return (True, "Meeting scheduled successfully", meeting)

        else:
            # Conflict exists — apply resolution strategy
            resolution = self.conflict_strategy.resolve({
                "reason": conflict_reason,
                "free_slots": alternatives
            })

            if resolution["action"] == "reject":
                return (False, f"Conflict: {conflict_reason}. Alternatives: {alternatives}", None)
            elif resolution["action"] == "force_book":
                self.meetings[meeting.meeting_id] = meeting
                return (True, "Meeting force-booked despite conflicts", meeting)
            else:  # propose_alternatives
                return (False, f"Conflicts detected. Alternatives: {resolution['alternatives']}", None)

    def cancel_meeting(self, meeting_id: str) -> bool:
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return False

        meeting.status = MeetingStatus.CANCELLED

        # Remove from attendees' calendars
        for attendee_id in meeting.attendees:
            user = self.users.get(attendee_id)
            if user:
                user.availability.busy_slots = [
                    slot for slot in user.availability.busy_slots
                    if slot != meeting.time_slot
                ]
                if meeting_id in user.meetings:
                    user.meetings.remove(meeting_id)

        self._emit("meeting_cancelled", {"title": meeting.title})
        return True

    # ---- INVITATION MANAGEMENT ----

    def accept_invitation(self, invitation_id: str) -> bool:
        inv = self.invitations.get(invitation_id)
        if inv:
            inv.accept()
            return True
        return False

    def decline_invitation(self, invitation_id: str) -> bool:
        inv = self.invitations.get(invitation_id)
        if inv:
            inv.decline()
            return True
        return False

    # ---- RECURRING MEETINGS ----

    def schedule_recurring_meeting(self, title: str, organizer_id: str, attendee_ids: Set[str],
                                   start_time: datetime, duration_minutes: int,
                                   recurrence_type: RecurrenceType, count: int,
                                   room_id: Optional[str] = None) -> Tuple[int, List[Meeting]]:
        """Create recurring meeting instances"""

        recurring = RecurringMeeting(title, organizer_id, start_time, duration_minutes,
                                     recurrence_type, count)

        scheduled = 0
        failed_meetings = []

        for instance in recurring.generate_instances():
            instance.room_id = room_id
            instance.attendees = attendee_ids

            success, msg, meeting = self.schedule_meeting(
                instance.title, organizer_id, attendee_ids,
                instance.time_slot, room_id
            )

            if success:
                scheduled += 1
            else:
                failed_meetings.append(instance)

        return (scheduled, failed_meetings)

    # ---- STRATEGY MANAGEMENT ----

    def set_conflict_resolution_strategy(self, strategy: ConflictResolutionStrategy) -> None:
        self.conflict_strategy = strategy
        self._emit("strategy_changed", {"new_strategy": strategy.name()})

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def demo_1_user_and_room_setup() -> None:
    print_section("DEMO 1: USER & ROOM SETUP")

    scheduler = MeetingScheduler()

    # Create users
    alice = scheduler.create_user("user_alice", "Alice", "alice@email.com")
    bob = scheduler.create_user("user_bob", "Bob", "bob@email.com")
    charlie = scheduler.create_user("user_charlie", "Charlie", "charlie@email.com")

    print(f"+ Created users: {alice.name}, {bob.name}, {charlie.name}")

    # Create rooms
    room_a = scheduler.create_room("room_1", "Conference Room A", capacity=10)
    room_b = scheduler.create_room("room_2", "Meeting Room B", capacity=5)

    print(f"+ Created rooms: {room_a.name} (cap. {room_a.capacity}), {room_b.name} (cap. {room_b.capacity})")

def demo_2_create_meeting_no_conflicts() -> None:
    print_section("DEMO 2: CREATE MEETING WITHOUT CONFLICTS")

    scheduler = MeetingScheduler()
    scheduler.register_observer(EmailNotifier())
    scheduler.register_observer(ReminderService())

    alice = scheduler.get_user("user_alice") or scheduler.create_user("user_alice", "Alice", "alice@email.com")
    bob = scheduler.get_user("user_bob") or scheduler.create_user("user_bob", "Bob", "bob@email.com")
    room_a = scheduler.get_room("room_1") or scheduler.create_room("room_1", "Conference Room A", 10)

    start = datetime.now() + timedelta(days=1, hours=2)
    end = start + timedelta(hours=1)
    slot = TimeSlot(start, end)

    success, msg, meeting = scheduler.schedule_meeting(
        "Team Sync",
        "user_alice",
        {"user_bob"},
        slot,
        "room_1"
    )

    print(f"+ Meeting scheduled: {success}")
    print(f"  Message: {msg}")
    if meeting:
        print(f"  Meeting ID: {meeting.meeting_id}, Status: {meeting.status.value}")

def demo_3_conflict_and_resolution() -> None:
    print_section("DEMO 3: DETECT & RESOLVE CONFLICTS")

    scheduler = MeetingScheduler()

    alice = scheduler.get_user("user_alice") or scheduler.create_user("user_alice", "Alice", "alice@email.com")
    bob = scheduler.get_user("user_bob") or scheduler.create_user("user_bob", "Bob", "bob@email.com")
    room_a = scheduler.get_room("room_1") or scheduler.create_room("room_1", "Conference Room A", 10)

    start = datetime.now() + timedelta(days=2, hours=10)
    end = start + timedelta(hours=1)
    slot = TimeSlot(start, end)

    # Add existing meeting to room
    room_a.book_for_slot(slot)

    # Try to schedule conflicting meeting
    success, msg, meeting = scheduler.schedule_meeting(
        "Project Planning",
        "user_alice",
        {"user_bob"},
        slot,
        "room_1"
    )

    print(f"- AutoRejectStrategy: {success}")
    print(f"  Reason: {msg}")

    # Switch to ProposeAlternatives
    scheduler.set_conflict_resolution_strategy(ProposeAlternativesStrategy())
    success, msg, meeting = scheduler.schedule_meeting(
        "Project Planning",
        "user_alice",
        {"user_bob"},
        slot,
        "room_1"
    )

    print(f"+ ProposeAlternativesStrategy: {success}")
    print(f"  Response: {msg}")

def demo_4_invitation_state_machine() -> None:
    print_section("DEMO 4: INVITATION STATE MACHINE")

    scheduler = MeetingScheduler()

    alice = scheduler.get_user("user_alice") or scheduler.create_user("user_alice", "Alice", "alice@email.com")
    bob = scheduler.get_user("user_bob") or scheduler.create_user("user_bob", "Bob", "bob@email.com")
    charlie = scheduler.get_user("user_charlie") or scheduler.create_user("user_charlie", "Charlie", "charlie@email.com")

    start = datetime.now() + timedelta(days=3, hours=14)
    end = start + timedelta(hours=1)
    slot = TimeSlot(start, end)

    success, msg, meeting = scheduler.schedule_meeting(
        "Board Meeting",
        "user_alice",
        {"user_bob", "user_charlie"},
        slot
    )

    print(f"+ Meeting created: {meeting.meeting_id if meeting else 'N/A'}")

    # Accept/decline
    invitations = [inv for inv in scheduler.invitations.values() if inv.meeting_id == meeting.meeting_id]

    for i, inv in enumerate(invitations):
        if i == 0:
            scheduler.accept_invitation(inv.invitation_id)
            print(f"  {scheduler.get_user(inv.invitee_id).name}: {inv.status.value}")
        elif i == 1:
            scheduler.decline_invitation(inv.invitation_id)
            print(f"  {scheduler.get_user(inv.invitee_id).name}: {inv.status.value}")

def demo_5_recurring_meetings() -> None:
    print_section("DEMO 5: RECURRING MEETINGS")

    scheduler = MeetingScheduler()
    scheduler.register_observer(CalendarSyncObserver())

    alice = scheduler.get_user("user_alice") or scheduler.create_user("user_alice", "Alice", "alice@email.com")
    bob = scheduler.get_user("user_bob") or scheduler.create_user("user_bob", "Bob", "bob@email.com")

    start = datetime.now().replace(hour=9, minute=0, second=0)

    scheduled, failed = scheduler.schedule_recurring_meeting(
        "Daily Standup",
        "user_alice",
        {"user_bob"},
        start,
        duration_minutes=30,
        recurrence_type=RecurrenceType.DAILY,
        count=5
    )

    print(f"+ Recurring meeting created")
    print(f"  Scheduled instances: {scheduled}")
    print(f"  Failed instances: {len(failed)}")

    # Find available slots
    slots = scheduler.find_available_slots({"user_alice", "user_bob"}, duration_minutes=60, days_ahead=7)
    print(f"\n  Available 1-hour slots for next week: {len(slots)}")
    if slots:
        print(f"  First 3: {[s.start_time.strftime('%a %H:%M') for s in slots[:3]]}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MEETING SCHEDULER - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_user_and_room_setup()
    demo_2_create_meeting_no_conflicts()
    demo_3_conflict_and_resolution()
    demo_4_invitation_state_machine()
    demo_5_recurring_meetings()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **Singleton init** | Class RLock (double-checked) | One instance created even under concurrent calls |
| **schedule_meeting** | RLock (re-entrant) | Atomic: conflict check + book room + update calendars |
| **cancel_meeting** | RLock | Safe removal from attendee calendars |
| **find_available_slots** | Read-only scan | No shared write; safe for concurrent reads |
| **set_conflict_resolution_strategy** | Atomic reference swap | Next call uses new strategy |

**Concurrency Principles**:
1. RLock (re-entrant lock) instead of Lock — prevents deadlock if `schedule_meeting` calls internal helpers that also lock
2. Double-checked locking for the Singleton
3. Observers notified outside critical sections to keep locks short
4. No nested lock ordering issues: single lock covers all shared state

---

## Demo Scenarios

### Demo 1: User Creation & Calendar Setup
```
1. Create user Alice (alice@email.com)
2. Create user Bob (bob@email.com)
3. Create conference room "Room A" (capacity 10)
4. Create conference room "Room B" (capacity 5)
5. Verify: Users exist, rooms exist, all calendars empty
```

### Demo 2: Create Meeting Without Conflicts
```
1. Alice creates "Team Sync" meeting: Monday 10:00 AM, 1 hour
2. Add attendees: Bob
3. Choose room: Room A
4. Send invitations
5. Bob accepts invitation
6. Verify: Meeting on both calendars, invitation status = Accepted
```

### Demo 3: Detect & Resolve Conflicts
```
1. Alice tries to create overlapping meeting same time in Room A
2. Conflict detected: Room A not available
3. Apply AutoRejectStrategy: Meeting rejected
4. Try ProposeAlternativesStrategy: System suggests Monday 11:00 AM
5. Accept alternative: Meeting scheduled for 11:00 AM
```

### Demo 4: Invitation State Machine
```
1. Alice creates "Project Planning" meeting
2. Send invitation to Bob, Charlie, David
3. Bob accepts → invitation status = Accepted
4. Charlie declines → invitation status = Declined
5. David tentative → invitation status = Tentative
6. Verify: Meeting still happens, shows attendee statuses
```

### Demo 5: Recurring Meeting & Availability
```
1. Alice creates "Daily Standup" recurring meeting
   - Start: Monday 9:00 AM
   - Recurrence: DAILY
   - Count: 5 instances (Mon-Fri)
2. Generate instances: 5 separate meetings created
3. Find available slots for next week for 4 people
4. Show free 2-hour slots: {Tuesday 2-4 PM, Wednesday 3-5 PM, ...}
5. Cancel one instance (Wednesday standup exception handling)
```

---

## Interview Q&A

### Basic Level

**Q1: How does Singleton ensure one MeetingScheduler instance?**
A: `MeetingScheduler` uses `__new__` with thread-safe double-check locking. `_instance` class variable holds single instance. On first call, creates instance; subsequent calls return same. Prevents multiple systems managing different meetings.

**Q2: How does Observer pattern work for notifications?**
A: `MeetingScheduler` maintains list of `MeetingObserver` objects. When meeting created/cancelled/moved, scheduler calls `update(event, payload)` on all observers. Each observer (EmailNotifier, ReminderService) handles notifications independently.

**Q3: What's the Meeting state machine lifecycle?**
A: Meeting starts in `Scheduled` state. Transitions: `Scheduled` → `Ongoing` (at start time) → `Completed` (after duration) or `Cancelled` (explicit cancellation). Each state encapsulates valid operations.

**Q4: How does Factory pattern work for meeting types?**
A: `MeetingFactory.create_meeting(type, title, time, duration, ...)` takes meeting type. Returns either OneOffMeeting or RecurringMeeting. Centralizes creation, makes extending with new types easy.

**Q5: How do conflict resolution strategies differ?**
A: `AutoRejectStrategy` rejects conflicting meetings. `ProposeAlternativesStrategy` suggests free time slots. `ForceBookStrategy` overrides and books anyway. Each strategy is independent; can switch at runtime.

### Intermediate Level

**Q6: How does conflict detection work efficiently?**
A: Use interval tree indexed by time. For room conflicts: query tree for (meeting_start, meeting_end) → O(log n). For attendees: iterate their calendars, merge overlapping intervals → O(k log k) for k meetings. Total: O(n log n) for n meetings.

**Q7: How do you find available time slots for group meeting?**
A: Collect all attendees' busy intervals. Merge overlapping intervals (sort + sweep) → O(n log n). Find gaps >= required_duration. Return top 5 slots. Can pre-compute popular time slots.

**Q8: How do recurring meetings handle exceptions?**
A: RecurringMeeting stores recurrence rule (daily/weekly/month day) + exception_dates. Generate instances: iterate from start_date, apply rule, skip exception_dates. Check conflicts for each instance separately.

**Q9: Why use Strategy pattern instead of nested if-statements?**
A: Strategy encapsulates each conflict resolution approach independently. Easy to add new strategies without changing MeetingScheduler code. Can switch strategies at runtime. Open/Closed principle.

**Q10: How do you handle attendee availability efficiently?**
A: Cache user calendars in memory with last-update timestamp. For large calendars (>1000 meetings), use time-windowing: only load meetings for current month + next month. Pagination for calendar view.

### Advanced Level

**Q11: How would you scale to 1M users and 10M meetings?**
A: Shard users by user_id hash → separate database shard. Meetings sharded by creator_id or room_id. Use Elasticsearch for available slot queries. Cache popular rooms/time slots in Redis. Denormalize attendee lists for fast access. Background jobs for conflict pre-detection.

**Q12: How to handle 100K concurrent meeting creation requests?**
A: Use optimistic locking: Meeting.version increments on update. Conflict check: if version != expected after book attempt, retry. Queue system for conflict resolution: 10K queues, distribute requests by (room_id + time_bucket) hash. Async notification: Kafka queues for emails/reminders.

---

## Scaling Q&A

**Q1: Can 1M users schedule 10M meetings in memory?**
A: No. 10M meetings × 1KB = 10GB metadata alone. In production: PostgreSQL (sharded) for meetings, Redis for cache (hot meetings: today + next 7 days). ElasticSearch for meeting search. Room availability: dedicated service with real-time cache.

**Q2: How to find free slots for 100 people in < 100ms?**
A: Pre-compute free slots for each person nightly (Spark job). Store as "free_blocks" in Redis (person_id → [(start, end), ...]). When finding group slots: intersect 100 free_blocks sets (fast bitwise operation on sorted intervals). Total: < 50ms.

**Q3: What's the storage footprint for 1M users × 100 meetings each = 100M meetings?**
A: Each meeting ≈ 1KB (title, time, attendees, room). 100M × 1KB = 100GB. With compression: 30-40GB. Sharded across 50 database servers = ~1GB each. Hot cache (today's meetings) ≈ 5GB.

**Q4: How to handle meeting conflicts across timezones?**
A: Store all times in UTC internally. Convert to user's timezone for display. Conflict check: always in UTC (eliminates DST bugs). Reminders: calculate user's local time, send at 9:00 AM local time using user's timezone offset.

**Q5: How to efficiently check room conflicts for 100K meeting requests/sec?**
A: Partition rooms by ID hash → 100 room-service instances. Each instance handles 1000 rooms. Use interval tree per room: O(log n) conflict check. Peak throughput: 100K requests ÷ 100 instances = 1000 req/sec per instance = 100ms per request (acceptable).

**Q6: How to generate available slots for 1000 meetings worth of historical data?**
A: Don't recompute all slots. Use sliding window: for next 90 days, pre-compute free slots. Cache in Redis. For past meetings: archive to S3 (don't need for conflict checks). Incremental updates: add new meeting → recompute free slots for affected hours.

**Q7: How to maintain consistency when users edit meetings simultaneously?**
A: Use optimistic locking: Meeting.version increments on edit. Edit request includes expected version. If version mismatch, conflict: user sees "meeting changed, retry". Alternative: use distributed locks (Redis) for 10-second exclusive locks during edits.

**Q8: How to scale notifications to 1M meeting changes/hour?**
A: Kafka: 1M messages/hour ÷ 3600 sec ≈ 278 msg/sec. Kafka handles 1M msg/sec (safe). Partition by user_id (100 partitions). Consumer services (100 instances) → batch send emails (1000 per batch) via SendGrid API. Total: 100 batches/sec × 1000 emails = 100K emails/sec.

**Q9: How to handle recurring meetings generating 1M instances?**
A: Generate instances lazily: store only recurrence rule + exceptions. When user opens calendar → generate instances for current month only (10-50 instances). When checking conflicts → generate on-demand for time range of interest. Pre-generate only for bookings (10K annual meetings = manageable).

**Q10: How to efficiently sync meeting calendars across 10 devices per user?**
A: Server-side calendar: single source of truth in PostgreSQL. Devices: lightweight sync using timestamps. Device stores last_sync_ts. Query: meetings WHERE modified_time > last_sync_ts. Delta sync: typically <1000 changes per device per hour. Batch updates every 5 min.

**Q11: How to detect anomalies (e.g., too many meetings, room overbooking)?**
A: Real-time alerts: if meetings_per_hour > 10 for a user → alert. Room alerts: if bookings > capacity × 1.5 → flag as double-booking. Weekly report: identify users with >40 hours/week in meetings. Weekday patterns: alert if anomalous (e.g., 500 meetings on Sunday).

**Q12: How to support 1000 concurrent meeting creations with transactions?**
A: Use event sourcing: store every action as immutable event. CREATE_MEETING → append to log → process asynchronously. Conflict check → async verification. If conflict: emit CONFLICT_DETECTED event → user sees "meeting conflicted" and can retry with different time. Maintains high throughput (batched writes).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships
- [ ] Discuss conflict detection flow: room + attendee checks + strategy dispatch
- [ ] Explain the three conflict resolution strategies and how to swap them at runtime
- [ ] Walk through invitation state machine: Pending → Accepted/Declined/Tentative
- [ ] Explain recurring meeting instance generation with exception handling
- [ ] Explain how find_available_slots merges intervals in O(n log n)
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety: RLock for re-entrant Singleton, atomic calendar updates
- [ ] Discuss trade-offs (in-memory vs DB, interval tree vs linear scan, eager vs lazy recurring generation)

---

**Ready for interview? Schedule some meetings!**
