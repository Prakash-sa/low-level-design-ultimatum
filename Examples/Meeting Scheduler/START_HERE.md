# 📅 Meeting Scheduler - Quick Start Guide

## System Overview
**Calendar and meeting scheduling system** with room booking, conflict detection, invitations, and recurring meetings support.

**Core Purpose**: Schedule meetings, manage calendars, book rooms, detect conflicts, send notifications

---

## ⏱️ 75-Minute Interview Breakdown
| Phase | Time | Focus | Output |
|-------|------|-------|--------|
| **0** | 0-5 min | Requirements & Scope | Clear entity list, constraints |
| **1** | 5-15 min | Architecture & Enums | 150 lines: Base structure |
| **2** | 15-40 min | Core Entities | 600 lines: Meeting, User, Calendar, Room |
| **3** | 40-60 min | Patterns & Algorithms | 900 lines: Strategy, Observer, State |
| **4** | 60-70 min | System Integration | 1100 lines: Singleton scheduler |
| **5** | 70-75 min | Demos & Testing | 1200+ lines: 5 working scenarios |

---

## 🎯 Core Entities (6 Main)
| Entity | Purpose | Key Methods |
|--------|---------|-------------|
| **Meeting** | Meeting details with time/attendees | `schedule()`, `cancel()`, `add_attendee()` |
| **Calendar** | User's calendar with meetings | `add_meeting()`, `check_availability()`, `get_conflicts()` |
| **User** | System user with calendar | `create_meeting()`, `accept_invite()`, `get_schedule()` |
| **Room** | Meeting room with capacity | `book()`, `release()`, `check_availability()` |
| **Invitation** | Meeting invitation with status | `accept()`, `decline()`, `tentative()` |
| **Notification** | Event notification | `send()`, `schedule_reminder()` |

---

## 📦 Design Patterns Used (5)
| Pattern | Class | Purpose |
|---------|-------|---------|
| **Singleton** | `MeetingScheduler` | Single system instance |
| **Strategy** | `ConflictResolutionStrategy` | Flexible conflict handling |
| **Observer** | `MeetingObserver` | Real-time notifications |
| **State** | `MeetingState` | Meeting lifecycle (Scheduled → Ongoing → Completed) |
| **Factory** | `MeetingFactory` | Create different meeting types |

---

## 🔑 Key Algorithms

### 1. Conflict Detection
```
For each new meeting:
  1. Get all existing meetings in time range
  2. Check room availability
  3. Check attendee availability
  4. If conflict: propose alternatives or fail
Time: O(n log n) with interval tree
```

### 2. Recurring Meeting Expansion
```
For recurring meeting:
  1. Parse recurrence rule (daily/weekly/monthly)
  2. Generate instances up to end date
  3. Apply exceptions (cancelled dates)
  4. Detect conflicts for each instance
Time: O(k) for k instances
```

### 3. Available Time Slots
```
For group availability:
  1. Get all attendees' busy times
  2. Merge overlapping intervals
  3. Find gaps between busy times
  4. Filter by min duration
Time: O(n log n) for n busy slots
```

---

## 💡 Key Talking Points

### Singleton Pattern
> "We use **Singleton** for MeetingScheduler to ensure **single source of truth** for all meetings, rooms, and users. Thread-safe with double-checked locking."

### Observer Pattern
> "**Observer pattern** enables **real-time notifications** without tight coupling. When a meeting is created, all attendees are notified automatically."

### Strategy Pattern
> "**Conflict resolution strategies** can be swapped at runtime: **AutoReject**, **ProposeAlternatives**, or **ForceBook**. This makes the system flexible."

### State Pattern
> "Meeting lifecycle uses **State pattern**: **Scheduled → Ongoing → Completed/Cancelled**. Each state controls valid transitions."

### Conflict Detection
> "We use **interval tree** for O(log n) conflict detection. Alternative: sweep line algorithm for batch conflict checks."

---

## 🎯 Demo Scenarios (5 Essential)

### Demo 1: Basic Meeting Creation
```python
alice = User("U001", "Alice", "alice@email.com")
meeting = alice.create_meeting("Team Sync", start_time, duration)
meeting.add_attendee(bob)
# Shows: Meeting creation, user management, time handling
```

### Demo 2: Conflict Detection
```python
meeting1 = scheduler.schedule_meeting(room, time1)
meeting2 = scheduler.schedule_meeting(room, time1)  # Conflict!
# Shows: Conflict detection, Strategy pattern in action
```

### Demo 3: Invitation Flow (State Pattern)
```python
invitation = meeting.send_invitation(bob)
invitation.accept()  # Pending → Accepted
# Shows: State pattern, invitation lifecycle
```

### Demo 4: Room Booking
```python
room = Room("R001", "Conference A", capacity=10)
success = scheduler.book_room(room, meeting)
# Shows: Resource management, availability checking
```

### Demo 5: Recurring Meetings
```python
recurring = RecurringMeeting("Daily Standup", 
    start_date, recurrence="DAILY", count=30)
instances = recurring.generate_instances()
# Shows: Factory pattern, recurrence logic
```

---

## ✅ Success Criteria Checklist

### Must-Have (Core Requirements)
- [x] Meeting creation with title, time, attendees
- [x] Conflict detection (time + room + attendees)
- [x] Invitation system (send/accept/decline)
- [x] Room booking with capacity
- [x] Calendar view for users
- [x] 5 design patterns implemented
- [x] 5 working demo scenarios
- [x] ~1200 lines of code

### Nice-to-Have (Bonus Points)
- [x] Recurring meetings (daily/weekly/monthly)
- [x] Meeting reminders
- [x] Available time slot finder
- [x] Meeting cancellation
- [x] Observer notifications
- [x] State machine for meeting lifecycle
- [x] SOLID principles applied

---

## 🚀 Quick Commands
```bash
# Run complete implementation
python3 INTERVIEW_COMPACT.py

# Check line count
wc -l INTERVIEW_COMPACT.py

# Read implementation guide
cat 75_MINUTE_GUIDE.md

# Study complete reference
cat README.md
```

---

## 🆘 Emergency Time-Saving Tips

### If Behind Schedule (< 30 min remaining)
1. **Skip recurring meetings** - Focus on single meetings
2. **Simplify conflict detection** - Basic time overlap check
3. **Mock notifications** - Just print statements
4. **Minimal demo** - Show 2-3 scenarios instead of 5

### If Stuck on Patterns
- **Singleton**: Just use class variable `_instance`
- **Observer**: Simple list of listeners
- **Strategy**: Just one strategy initially
- **State**: Use simple enum instead of State classes

### Quick Wins
- ✅ Get basic meeting creation working first
- ✅ Add conflict detection second
- ✅ Demo early and often
- ✅ Explain patterns as you code

---

## 📊 Complexity Analysis
| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Create meeting | O(1) | O(1) | Direct creation |
| Conflict check | O(log n) | O(n) | Interval tree lookup |
| Book room | O(log n) | O(1) | Check room calendar |
| Find free slots | O(n log n) | O(n) | Merge intervals |
| Recurring expand | O(k) | O(k) | k = instance count |

---

## 🎓 Interview Pro Tips

### Communication
1. **Start with clarification**: "Should we support video conferencing integration?"
2. **Think aloud**: "Using interval tree here for efficient conflict detection..."
3. **Explain trade-offs**: "HashMap gives O(1) lookup but no ordering"

### Time Management
- **15 min**: Have enums and basic entities
- **40 min**: Core functionality working
- **60 min**: Patterns implemented
- **70 min**: Demos ready
- **75 min**: Polish and Q&A

### Code Quality
- Type hints: `def book_room(room: Room, meeting: Meeting) -> bool:`
- Docstrings: `"""Check if room is available at given time"""`
- Constants: `MAX_ATTENDEES = 100` not magic numbers
- Clean naming: `ConflictResolutionStrategy` not `CRS`

---

**Remember**: Working code > Perfect code. Ship it! 🚀
