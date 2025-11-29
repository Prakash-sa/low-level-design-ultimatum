# Amazon Locker System - START HERE (5-Minute Quick Reference)

> **Time-Constrained Interview? Read this in 5 minutes before your interview.**

---

## 1. The Problem (30 seconds)

**Amazon Locker System**: Customers order packages → packages stored in smart lockers at convenient locations → customers retrieve with pickup code.

**Your Role**: Design the backend to manage slot allocation, prevent double-booking, handle expiry, and notify customers.

**Scale**: 100+ concurrent operations, 1000+ worldwide locker locations

---

## 2. System Overview (1 minute)

```
User places order
    ↓
Package arrives at Locker Location
    ↓
STORE: Find empty slot (allocation strategy)
       Generate pickup code
       Notify via email/SMS
    ↓
Package sits for up to 7 days
    ↓
RETRIEVE: User enters code
          Verify code matches
          Release slot
          Notify pickup
    ↓
(Or CANCEL if customer changes mind)
```

---

## 3. Five Design Patterns (4 minutes)

### Pattern 1: **SINGLETON** (Consistent State)
**Problem**: Multiple threads accessing locker system → race conditions  
**Solution**: Single LockerSystem instance with thread locks

```python
class LockerSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# Always returns same instance
system = LockerSystem()
```

**Interview Talking Point**: "Singleton ensures consistency. If 10 users store packages simultaneously, all operations are atomic."

---

### Pattern 2: **STRATEGY** (Pluggable Algorithms)
**Problem**: Different ways to allocate slots (BestFit vs FirstAvailable)  
**Solution**: Pluggable allocation strategies

```python
class AllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, locker, size):
        pass

class BestFitAllocation(AllocationStrategy):
    def allocate(self, locker, size):
        return smallest_available_slot(size)

class FirstAvailableAllocation(AllocationStrategy):
    def allocate(self, locker, size):
        return first_slot_with_size(size)

# Switch strategy at runtime
system.set_allocation_strategy(BestFitAllocation())
```

**Interview Talking Point**: "Strategy pattern lets us add new allocation algorithms without modifying LockerSystem code. New requirement? New Strategy class. Done."

---

### Pattern 3: **OBSERVER** (Decouple Notifications)
**Problem**: LockerSystem shouldn't know about email/SMS details  
**Solution**: Notify with abstract Notifier interface

```python
class Notifier(ABC):
    @abstractmethod
    def notify(self, event, user, package):
        pass

class EmailNotifier(Notifier):
    def notify(self, event, user, package):
        send_email(user.email, f"Package {package.id}: {event}")

class SMSNotifier(Notifier):
    def notify(self, event, user, package):
        send_sms(user.phone, f"Package {package.id}: {event}")

# Add notifiers
system.add_notifier(EmailNotifier())
system.add_notifier(SMSNotifier())

# All notifiers fire on events
system.notify_all("STORED", user, package)
```

**Interview Talking Point**: "Observer pattern decouples. LockerSystem doesn't care *how* users are notified. Add Slack notifier? Just create SlackNotifier class."

---

### Pattern 4: **STATE** (Package Lifecycle)
**Problem**: Packages have valid transitions (PENDING → STORED) and invalid ones (STORED → PENDING)  
**Solution**: Enum-based state with validation

```python
class PackageStatus(Enum):
    PENDING = "pending"
    STORED = "stored"
    RETRIEVED = "retrieved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Package:
    def store(self, days=7):
        self.status = PackageStatus.STORED  # Valid transition
        self.expires_at = now() + timedelta(days)
    
    def retrieve(self):
        if self.status != PackageStatus.STORED:
            raise ValueError("Can't retrieve non-stored package")
        self.status = PackageStatus.RETRIEVED
    
    def is_expired(self):
        return datetime.now() > self.expires_at
```

**Interview Talking Point**: "State pattern prevents invalid transitions. Can't retrieve a cancelled package because status validation blocks it."

---

### Pattern 5: **FACTORY** (Create Objects)
**Problem**: Creating different Notifier types scattered in code  
**Solution**: Single factory method

```python
class NotifierFactory:
    @staticmethod
    def create_notifier(notifier_type):
        if notifier_type == "EMAIL":
            return EmailNotifier()
        elif notifier_type == "SMS":
            return SMSNotifier()
        else:
            raise ValueError(f"Unknown notifier: {notifier_type}")

# Usage
notifier = NotifierFactory.create_notifier("EMAIL")
```

**Interview Talking Point**: "Factory encapsulates object creation. Easy to add new notifier types or change instantiation logic in one place."

---

## 4. Core Classes Structure (memorize this)

```
┌─────────────────┐
│  LockerSystem   │ ← Singleton controller
│  (Main)         │
│                 │
│ store()         │
│ retrieve()      │
│ cancel()        │
└────────┬────────┘
         │
         ├─→ Locker ─→ LockerSlot (SMALL/MEDIUM/LARGE)
         │
         ├─→ Location (address)
         │
         ├─→ Package (status, expires_at, pickup_code)
         │
         ├─→ User (email, phone)
         │
         ├─→ AllocationStrategy (BestFit/FirstAvailable)
         │
         └─→ Notifier (Email/SMS)
```

---

## 5. Key Interview Talking Points (1 minute)

### Point 1: **How do you prevent double-booking?**
"LockerSlot has atomic occupy/release. When storing, mark slot OCCUPIED in single operation. When retrieving, release in single operation. Singleton + threading.Lock ensures only one store_package() at a time for same locker."

### Point 2: **How do you handle expiry?**
"Package stores expires_at = now() + 7 days. On retrieve, check `is_expired()`. If expired, mark status EXPIRED and notify user. They have 7-day window."

### Point 3: **Why these patterns?**
- Singleton → consistency + thread-safety
- Strategy → pluggable algorithms
- Observer → decouple notifications
- State → valid transitions
- Factory → centralized object creation

### Point 4: **How do you scale?**
"Create Locker per location. Each location has independent LockerSystem (or shared backend with location-scoped database). Horizontal scaling: add more locations = add more Lockers."

### Point 5: **What about race conditions?**
"Singleton has threading.Lock. If 10 users store simultaneously:
1. All thread.acquire(_lock)
2. Only 1 thread enters __new__() first time
3. _instance created once
4. All subsequent calls return _instance
5. Each operation (store_package, retrieve_package) works on same _instance with implicit locks"

---

## 6. Quick Demo Commands

```bash
# Change to directory
cd Examples/Amazon\ Locker\ System

# Run all 5 demos (2 minutes)
python3 INTERVIEW_COMPACT.py

# Output shows:
# ✅ Demo 1: Setup location, locker, users
# ✅ Demo 2: Store SMALL → Retrieve with code
# ✅ Demo 3: Multiple sizes, allocations
# ✅ Demo 4: Cancel package, free slot
# ✅ Demo 5: Full flow with stats
```

---

## 7. Success Checklist (Before Interview)

- [ ] Can explain Singleton pattern (why + how + threading)
- [ ] Can explain Strategy pattern (pluggable algorithms)
- [ ] Can explain Observer pattern (decouple notifications)
- [ ] Can explain State pattern (valid transitions)
- [ ] Can draw Locker → LockerSlot relationship
- [ ] Can explain how double-booking is prevented
- [ ] Can explain how expiry is handled
- [ ] Can run demo without errors
- [ ] Can answer "Why these patterns?" for each

---

## 8. Emergency Troubleshooting

| Issue | Fix |
|-------|-----|
| "I forgot what Singleton does" | Single instance, thread-safe, prevents race conditions |
| "I don't understand Strategy" | It's just an interface for algorithms. BestFit vs FirstAvailable. |
| "How's Observer different from callbacks?" | Observer is cleaner pattern. Subscribers register, get notified automatically. |
| "Demo won't run" | `cd` to correct directory, ensure Python 3.8+, run `python3 INTERVIEW_COMPACT.py` |
| "I keep confusing State and Strategy" | **State** = object's condition (STORED/PENDING), **Strategy** = algorithm choice |

---

## 9. Deep Dive Reference

| Section | File | Time |
|---------|------|------|
| **Complete Code** | 75_MINUTE_GUIDE.md | 20 min read |
| **Working Demo** | INTERVIEW_COMPACT.py | 5 min run |
| **Full Overview** | README.md | 10 min read |
| **12 Q&A** | 75_MINUTE_GUIDE.md (end) | 15 min prep |

---

## 10. Final Reminders

✅ **You have 5 design patterns memorized**  
✅ **You can run the demo**  
✅ **You can explain thread-safety**  
✅ **You can handle edge cases (expiry, cancellation, double-booking)**  

### During Interview:
1. Start with **high-level architecture** (Locker → LockerSlot → Package)
2. Explain **why each pattern** (Singleton for consistency, Strategy for flexibility)
3. **Deep dive on 1-2 patterns** (interviewer will ask)
4. Discuss **edge cases** (expiry, cancellation, race conditions)
5. Talk **scaling** (multiple locations, load balancing)

---

**NOW: Go back to 75_MINUTE_GUIDE.md for Q&A prep!**

*Ready? Let's ace this interview.* 🚀
