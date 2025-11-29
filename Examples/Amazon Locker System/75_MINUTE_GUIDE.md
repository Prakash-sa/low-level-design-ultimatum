# Amazon Locker System - 75 Minute Interview Guide

## System Overview

Self-service package pickup system with locker management, authentication, tracking, and notifications.

**Scale**: 100+ concurrent users, 1000+ lockers, peak: 50 pickups/min.  
**Focus**: State management, notification system, slot allocation, user authentication.

---

## 75-Minute Timeline

| Time | Phase | Deliverable |
|------|-------|-------------|
| 0–5 min | **Requirements Clarification** | Scope & assumptions confirmed |
| 5–15 min | **Architecture & Design Patterns** | System diagram + class skeleton |
| 15–35 min | **Core Entities** | Location, Locker, LockerSlot, Package, User classes |
| 35–55 min | **Package Operations** | Store, retrieve, cancel + notifications |
| 55–70 min | **System Integration** | LockerSystem (Singleton) + authentication |
| 70–75 min | **Demo & Q&A** | Working example + trade-off discussion |

---

## Requirements Clarification (0–5 min)

**Key Questions**:
1. What lockers store? → **Small packages only (max weight/size)**
2. Authentication? → **Pickup code + OTP verification**
3. Package expiry? → **3-7 days before auto-discard**
4. Notifications? → **Email/SMS on delivery, reminder before expiry**
5. Locker selection? → **Automatic based on package size**

**Scope Agreement**:
- ✅ Locker inventory with slot management
- ✅ Package storage and retrieval flow
- ✅ Pickup code generation & validation
- ✅ User authentication & tracking
- ✅ Notifications (Observer pattern)
- ✅ Available slot search
- ❌ Payment, returns, multi-day holds

---

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Singleton** | Single system instance | `LockerSystem.get_instance()` |
| **Strategy** | Locker slot allocation strategy | `AllocationStrategy` + `BestFitAllocation` |
| **Observer** | Event notifications | `Observer` interface + `EmailNotifier`, `SMSNotifier` |
| **State** | Package/Locker lifecycle | Enums: `PackageStatus`, `LockerSlotStatus` |
| **Factory** | Create packages/users | Factory methods in `LockerSystem` |

---

## Core Classes & Implementation

### Enumerations

```python
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import threading
import uuid

class LockerSlotStatus(Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    RESERVED = "reserved"

class PackageStatus(Enum):
    PENDING = "pending"
    STORED = "stored"
    RETRIEVED = "retrieved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class LockerSize(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class UserRole(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
```

### 1. Location Class

```python
class Location:
    """Represents a physical locker location"""
    def __init__(self, location_id: str, name: str, address: str, city: str):
        self.location_id = location_id
        self.name = name
        self.address = address
        self.city = city
        self.created_at = datetime.now()
```

### 2. LockerSlot Class

```python
class LockerSlot:
    """Represents a single slot in a locker"""
    def __init__(self, slot_id: str, size: LockerSize):
        self.slot_id = slot_id
        self.size = size
        self.status = LockerSlotStatus.EMPTY
        self.package_id: Optional[str] = None
    
    def is_available(self) -> bool:
        return self.status == LockerSlotStatus.EMPTY
    
    def occupy(self, package_id: str):
        if not self.is_available():
            raise ValueError(f"Slot {self.slot_id} is not empty")
        self.status = LockerSlotStatus.OCCUPIED
        self.package_id = package_id
    
    def release(self):
        self.status = LockerSlotStatus.EMPTY
        self.package_id = None
```

### 3. Locker Class

```python
class Locker:
    """Represents a physical locker with multiple slots"""
    def __init__(self, locker_id: str, location: Location, capacity: int):
        self.locker_id = locker_id
        self.location = location
        self.slots: Dict[str, LockerSlot] = {}
        self.created_at = datetime.now()
        
        # Create slots: distributed by size
        for i in range(capacity // 3):
            self.slots[f"S{i}"] = LockerSlot(f"S{i}", LockerSize.SMALL)
        for i in range(capacity // 3, 2 * capacity // 3):
            self.slots[f"M{i}"] = LockerSlot(f"M{i}", LockerSize.MEDIUM)
        for i in range(2 * capacity // 3, capacity):
            self.slots[f"L{i}"] = LockerSlot(f"L{i}", LockerSize.LARGE)
    
    def get_available_slots(self, size: LockerSize) -> List[LockerSlot]:
        return [s for s in self.slots.values() 
                if s.is_available() and s.size == size]
    
    def total_available(self) -> int:
        return sum(1 for s in self.slots.values() if s.is_available())
```

### 4. Package Class

```python
class Package:
    """Represents a package to be stored"""
    def __init__(self, package_id: str, user_id: str, 
                 size: LockerSize, weight: float):
        self.package_id = package_id
        self.user_id = user_id
        self.size = size
        self.weight = weight
        self.status = PackageStatus.PENDING
        self.created_at = datetime.now()
        self.stored_at: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None
        self.pickup_code: Optional[str] = None
        self.retrieved_at: Optional[datetime] = None
    
    def store(self, expiry_days: int = 7):
        """Mark package as stored"""
        self.status = PackageStatus.STORED
        self.stored_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=expiry_days)
        self.pickup_code = str(uuid.uuid4())[:6].upper()
    
    def retrieve(self):
        """Mark package as retrieved"""
        self.status = PackageStatus.RETRIEVED
        self.retrieved_at = datetime.now()
    
    def is_expired(self) -> bool:
        return (self.expires_at and 
                datetime.now() > self.expires_at)
```

### 5. User Class

```python
class User:
    """Represents a user/customer"""
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = UserRole.CUSTOMER
        self.created_at = datetime.now()
```

---

## Allocation Strategy (Strategy Pattern)

```python
class AllocationStrategy(ABC):
    """Abstract strategy for locker slot allocation"""
    @abstractmethod
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        pass

class BestFitAllocation(AllocationStrategy):
    """Allocate the smallest suitable slot"""
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        available = locker.get_available_slots(size)
        return available[0] if available else None

class FirstAvailableAllocation(AllocationStrategy):
    """Allocate first available slot of the size"""
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        available = locker.get_available_slots(size)
        return available[0] if available else None
```

---

## Observer Pattern (Notifications)

```python
class Notifier(ABC):
    """Observer interface for package events"""
    @abstractmethod
    def notify(self, event: str, user: User, package: Package):
        pass

class EmailNotifier(Notifier):
    """Email notifications"""
    def notify(self, event: str, user: User, package: Package):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📧 EMAIL: {user.email} | "
              f"Event: {event} | Package: {package.package_id} | "
              f"Code: {package.pickup_code}")

class SMSNotifier(Notifier):
    """SMS notifications"""
    def notify(self, event: str, user: User, package: Package):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📱 SMS: {user.phone} | "
              f"Event: {event} | Package: {package.package_id} | "
              f"Code: {package.pickup_code}")
```

---

## LockerSystem (Singleton + Controller)

```python
class LockerSystem:
    """Singleton controller for locker operations"""
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
            self.locations: Dict[str, Location] = {}
            self.lockers: Dict[str, Locker] = {}
            self.packages: Dict[str, Package] = {}
            self.users: Dict[str, User] = {}
            self.notifiers: List[Notifier] = []
            self.allocation_strategy: AllocationStrategy = BestFitAllocation()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'LockerSystem':
        """Get singleton instance"""
        return LockerSystem()
    
    def set_allocation_strategy(self, strategy: AllocationStrategy):
        """Switch allocation strategy"""
        self.allocation_strategy = strategy
    
    def add_notifier(self, notifier: Notifier):
        """Subscribe to events"""
        self.notifiers.append(notifier)
    
    def notify_all(self, event: str, user: User, package: Package):
        """Notify all subscribers"""
        for notifier in self.notifiers:
            notifier.notify(event, user, package)
    
    def create_location(self, location_id: str, name: str, 
                       address: str, city: str) -> Location:
        location = Location(location_id, name, address, city)
        self.locations[location_id] = location
        return location
    
    def create_locker(self, locker_id: str, location_id: str, 
                     capacity: int) -> Optional[Locker]:
        if location_id not in self.locations:
            return None
        locker = Locker(locker_id, self.locations[location_id], capacity)
        self.lockers[locker_id] = locker
        return locker
    
    def register_user(self, user_id: str, name: str, 
                     email: str, phone: str) -> User:
        user = User(user_id, name, email, phone)
        self.users[user_id] = user
        return user
    
    def store_package(self, package_id: str, user_id: str, 
                     locker_id: str, size: LockerSize, 
                     weight: float) -> Optional[str]:
        """Store package in locker and return pickup code"""
        if locker_id not in self.lockers:
            print(f"❌ Locker {locker_id} not found")
            return None
        
        if user_id not in self.users:
            print(f"❌ User {user_id} not found")
            return None
        
        locker = self.lockers[locker_id]
        user = self.users[user_id]
        
        # Find available slot
        slot = self.allocation_strategy.allocate(locker, size)
        if not slot:
            print(f"❌ No available slot for size {size.name}")
            return None
        
        # Create and store package
        package = Package(package_id, user_id, size, weight)
        package.store(expiry_days=7)
        slot.occupy(package_id)
        
        self.packages[package_id] = package
        self.notify_all("STORED", user, package)
        
        return package.pickup_code
    
    def retrieve_package(self, package_id: str, user_id: str, 
                        pickup_code: str) -> bool:
        """Retrieve package with verification"""
        if package_id not in self.packages:
            print(f"❌ Package {package_id} not found")
            return False
        
        package = self.packages[package_id]
        user = self.users.get(user_id)
        
        if package.user_id != user_id:
            print(f"❌ Unauthorized access")
            return False
        
        if package.pickup_code != pickup_code:
            print(f"❌ Invalid pickup code")
            return False
        
        if package.is_expired():
            package.status = PackageStatus.EXPIRED
            self.notify_all("EXPIRED", user, package)
            return False
        
        if package.status != PackageStatus.STORED:
            print(f"❌ Package already retrieved or cancelled")
            return False
        
        # Mark as retrieved
        package.retrieve()
        
        # Release slot
        for locker in self.lockers.values():
            for slot in locker.slots.values():
                if slot.package_id == package_id:
                    slot.release()
        
        self.notify_all("RETRIEVED", user, package)
        return True
    
    def cancel_package(self, package_id: str, user_id: str) -> bool:
        """Cancel package before retrieval"""
        if package_id not in self.packages:
            return False
        
        package = self.packages[package_id]
        user = self.users.get(user_id)
        
        if package.user_id != user_id or package.status != PackageStatus.STORED:
            return False
        
        package.status = PackageStatus.CANCELLED
        
        # Release slot
        for locker in self.lockers.values():
            for slot in locker.slots.values():
                if slot.package_id == package_id:
                    slot.release()
        
        self.notify_all("CANCELLED", user, package)
        return True
    
    def get_available_slots(self, locker_id: str, size: LockerSize) -> int:
        """Get count of available slots"""
        if locker_id not in self.lockers:
            return 0
        return len(self.lockers[locker_id].get_available_slots(size))
```

---

## UML Class Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     AMAZON LOCKER SYSTEM                          │
└──────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   LockerSystem       │ ◄─── Singleton (Thread-safe)
                    │   (Controller)       │
                    ├──────────────────────┤
                    │ - locations: Dict    │
                    │ - lockers: Dict      │
                    │ - packages: Dict     │
                    │ - users: Dict        │
                    │ - notifiers: List    │
                    │ - alloc_strategy     │
                    ├──────────────────────┤
                    │ + store_package()    │
                    │ + retrieve_package() │
                    │ + cancel_package()   │
                    │ + get_available()    │
                    └────┬────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────────┐
        │                │                │                  │
        ▼                ▼                ▼                  ▼
    ┌─────────┐     ┌────────┐      ┌────────┐        ┌──────────┐
    │Location │     │ Locker │      │ User   │        │ Package  │
    ├─────────┤     ├────────┤      ├────────┤        ├──────────┤
    │- id     │     │- id    │      │- id    │        │- id      │
    │- name   │     │- loc   │      │- name  │        │- user_id │
    │- address│     │- slots◇│      │- email │        │- size    │
    │- city   │     └────────┘      │- phone │        │- status  │
    └─────────┘         │           └────────┘        │- code    │
                        │                            │- expires │
                        │ HAS-A                      └──────────┘
                        │ 1..*
                        ▼
                    ┌─────────────┐
                    │ LockerSlot  │
                    ├─────────────┤
                    │- id         │
                    │- size       │ ◄─── LockerSize Enum
                    │- status     │ ◄─── LockerSlotStatus Enum
                    │- package_id │ ◄─── PackageStatus Enum
                    └─────────────┘

    ┌──────────────────────────────────────┐
    │ AllocationStrategy (Abstract)        │
    ├──────────────────────────────────────┤
    │ + allocate(locker, size)             │
    └────────────┬─────────────────────────┘
                 │
         ┌───────┴──────────────┐
         ▼                      ▼
    ┌──────────┐        ┌──────────────┐
    │ BestFit  │        │FirstAvailable│
    │Allocation│        │ Allocation   │
    └──────────┘        └──────────────┘

    ┌──────────────────────────────────────┐
    │  Notifier (Abstract)                 │
    ├──────────────────────────────────────┤
    │ + notify(event, user, package)       │
    └────────────┬─────────────────────────┘
                 │
         ┌───────┴──────────────┐
         ▼                      ▼
    ┌──────────┐        ┌──────────────┐
    │ Email    │        │   SMS        │
    │Notifier  │        │  Notifier    │
    └──────────┘        └──────────────┘
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-allocation of the same locker slot?**

A: Use slot status enum (EMPTY → OCCUPIED → EMPTY). Each allocation operation atomically checks status and marks as occupied. For concurrency, use locks around the check-and-allocate operation.

**Q2: What's the difference between STORED and RETRIEVED package status?**

A: STORED means package is in the locker waiting for pickup. RETRIEVED means customer successfully retrieved it. EXPIRED means the storage period ended without retrieval.

**Q3: Why use Strategy pattern for slot allocation?**

A: Different allocation strategies (best-fit, first-available, round-robin) can be swapped without changing the core package storage logic. Easy to test and optimize.

### Intermediate Questions

**Q4: How do you handle pickup code generation and validation?**

A: Generate random 6-char code when storing package. User must provide exact code + user_id + package_id to retrieve. Code is single-use and expires with the package.

**Q5: How would you scale this to 1000+ lockers across multiple cities?**

A: 
- Shard lockers by location/city
- Use distributed locks for slot allocation (Redis)
- Cache available slot counts with TTL
- Use message queues for async notifications (Kafka)
- Database transactions ensure slot uniqueness

**Q6: How to handle package expiry?**

A: Store expiry timestamp when package is stored (now + 7 days). Before retrieval, check if now > expiry. If expired, trigger expiry event, lock slot for admin cleanup, notify user.

### Advanced Questions

**Q7: How to prevent race conditions during concurrent storage?**

A: Use database-level row locks or optimistic versioning. When allocating: read slot version, check status, write new owner if version matches. On conflict, retry with different slot.

**Q8: How to handle notification delivery failures?**

A: Implement retry logic with exponential backoff. Store failed notifications in queue. Use circuit breaker pattern to prevent cascading failures. Log and alert on repeated failures.

**Q9: What if a slot malfunctions?**

A: Mark slot as RESERVED/OUT_OF_SERVICE. Exclude from allocation. Send alert to admin. Redirect packages to nearby locker at same location.

**Q10: How to track locker usage metrics?**

A: Log all events (store, retrieve, expiry, cancel). Aggregate: storage rate, retrieval rate, expiry rate, slot utilization per locker. Use time-series DB for metrics.

**Q11: How would you handle a user losing their pickup code?**

A: Implement recovery: user provides user_id + package_id, system sends new code via email/SMS. Alternative: QR code scan to retrieve without code.

**Q12: How to optimize for high concurrency (100+ simultaneous pickups)?**

A: Use read replicas for queries, write replicas for mutations. Cache available slots (update on change). Use async processing for notifications. Add load balancing.

---

## Demo Script

```python
from datetime import datetime, timedelta

def run_demo():
    print("=" * 70)
    print("AMAZON LOCKER SYSTEM - DEMO")
    print("=" * 70)
    
    system = LockerSystem.get_instance()
    system.add_notifier(EmailNotifier())
    system.add_notifier(SMSNotifier())
    
    # Setup: Create location and locker
    loc = system.create_location("LOC001", "NYC Downtown", "123 Main St", "NYC")
    locker = system.create_locker("LOCK001", "LOC001", 15)
    
    # Create users
    user1 = system.register_user("U001", "John Doe", "john@example.com", "555-1234")
    user2 = system.register_user("U002", "Jane Smith", "jane@example.com", "555-5678")
    
    print("\n[DEMO 1] Store & Retrieve Package")
    print("-" * 70)
    code1 = system.store_package("PKG001", "U001", "LOCK001", LockerSize.SMALL, 2.5)
    print(f"✅ Package stored with code: {code1}")
    
    if system.retrieve_package("PKG001", "U001", code1):
        print(f"✅ Package retrieved successfully")
    
    print("\n[DEMO 2] Multiple Packages & Notifications")
    print("-" * 70)
    code2 = system.store_package("PKG002", "U002", "LOCK001", LockerSize.MEDIUM, 5.0)
    code3 = system.store_package("PKG003", "U002", "LOCK001", LockerSize.LARGE, 8.0)
    
    print("\n[DEMO 3] Cancel Package")
    print("-" * 70)
    system.cancel_package("PKG002", "U002")
    print(f"✅ Package cancelled - slot freed")
    
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total packages: {len(system.packages)}")
    print(f"Available slots in LOCK001: {locker.total_available()}")

if __name__ == "__main__":
    run_demo()
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Concurrency** | Thread-safe Singleton; use locks for slot allocation |
| **Extensibility** | Strategy pattern for allocation; Notifier interface for events |
| **Reliability** | Enums for state; explicit status transitions; pickup code validation |
| **Scalability** | Distributed locks, caching, sharding by location, async notifications |
| **Testing** | Mock Notifiers; mock Allocation strategies; unit tests per component |

---

## Interview Tips

1. **Clarify scope first** — Ask about scale, supported package sizes, expiry policy
2. **Draw architecture** — Sketch locker/slot relationships before coding
3. **Explain patterns** — Show why Singleton, Strategy, Observer matter
4. **Handle edge cases** — Expired packages, malfunction, lost pickup codes
5. **Discuss trade-offs** — Consistency vs availability, strong vs eventual consistency
6. **Demo incrementally** — Show store → retrieve → notify flow
7. **Mention scalability** — But don't over-engineer for interview
