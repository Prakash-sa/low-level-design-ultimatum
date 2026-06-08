# Amazon Locker System — Complete Design Guide

> Self-service package pickup with sized-slot allocation, secure pickup codes, lifecycle tracking, expiry handling, and notifications.

**Scale**: 100+ concurrent users per location, 1000+ locker locations, peak 50 pickups/min
**Duration**: 75-minute interview guide
**Focus**: Atomic slot allocation, package state lifecycle, notification fan-out, concurrency

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
A package arrives at a locker location → the system allocates an appropriately sized slot → generates a secure pickup code → stores the package for 3–7 days → the customer retrieves it with the code → the slot is freed. The system prevents double-booking, handles expiry/cancellation, and notifies users at each step.

### Core Flow
```
Order Package → ALLOCATE Slot (S/M/L) → Generate Pickup Code → STORE (3-7 days)
                                                                    ↓
                          Customer + Code → RETRIEVE → slot freed
                                                                    ↓ not picked up in time
                                                              EXPIRED (slot freed, notify)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single location or fleet?** → "Many independent locations; design one, scale out"
2. **Sized slots?** → "Yes — SMALL / MEDIUM / LARGE"
3. **How is pickup secured?** → "Per-package pickup code + user verification"
4. **Expiry policy?** → "3–7 days, then auto-expire and free the slot"
5. **Payments / returns?** → "Out of scope"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Stores/retrieves packages | Drop-off, retrieve with code, cancel |
| **Courier** | Delivers packages | Store package into an allocated slot |
| **Admin** | Manages lockers | Add locations/lockers, mark slot out-of-service |
| **System** | Coordinator & notifier | Allocate slots, verify codes, expire, notify |

### Functional Requirements (What does the system do?)

✅ **Store**
  - Allocate an appropriately sized slot (SMALL/MEDIUM/LARGE)
  - Generate and return a secure pickup code

✅ **Retrieve**
  - Retrieve a package with pickup code + user verification
  - Free the slot on successful retrieval

✅ **Cancel & Expire**
  - Cancel a package and free its slot
  - Auto-expire packages not retrieved in time

✅ **Notify**
  - Notify users on store / retrieve / expiry / cancellation
  - Support multiple channels (email, SMS)

✅ **Track & Maintain**
  - Track package lifecycle (PENDING → STORED → RETRIEVED/EXPIRED/CANCELLED)
  - Handle slot malfunction / out-of-service

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe access for 100+ simultaneous operations per location
✅ **Consistency**: No double-booking; accurate slot inventory
✅ **Latency**: <100ms allocation
✅ **Availability**: 99.9% uptime; lockers 24/7
✅ **Scalability**: 1000+ locations managed independently

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Slot sizes** | SMALL (≤2kg), MEDIUM (≤10kg), LARGE (≤30kg) |
| **Hold duration** | 3–7 days, then EXPIRED |
| **Pickup security** | Per-package code + user verification |
| **Cross-location allocation** | NO — each location is independent |
| **Payments / returns** | Out of scope |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Location, Locker, LockerSlot, Package, User, AllocationStrategy, Notifier, LockerSystem, ...
```

### Step 2.2: Define Core Classes

#### **User** — A customer or admin
```
Properties:
  - user_id: str
  - name: str
  - email: str
  - phone: str
```

#### **Location** — A physical site holding lockers
```
Properties:
  - location_id: str
  - name / address / city: str
  - lockers: List[Locker]
```

#### **Locker** — A bank of slots at a location
```
Properties:
  - locker_id: str
  - location: Location
  - slots: List[LockerSlot]   (configurable counts of S/M/L)

Behaviors:
  - find_available_slot(size): First EMPTY slot of a given size
  - total_available(): Count of empty slots
```

#### **LockerSlot** — A single storage compartment
```
Properties:
  - slot_id: str
  - size: LockerSize
  - status: LockerSlotStatus (EMPTY, OCCUPIED, RESERVED)
  - package_id: Optional[str]

Behaviors:
  - occupy(package_id): EMPTY → OCCUPIED (raises if not empty)
  - release(): → EMPTY
  - is_available(): status == EMPTY
```

#### **Package** — An item being stored
```
Properties:
  - package_id: str
  - user_id: str
  - size: LockerSize
  - status: PackageStatus (PENDING, STORED, RETRIEVED, EXPIRED, CANCELLED)
  - pickup_code: str
  - created_at / expires_at / retrieved_at: datetime

Behaviors:
  - is_expired(): now > expires_at
  - verify_code(code): code == pickup_code
```

#### **LockerSystem** — Main controller (Singleton)
```
Properties:
  - locations: List[Location]
  - notifiers: List[Notifier]
  - allocation_strategy: AllocationStrategy
  - _lock: threading lock

Behaviors:
  - add_location / add_locker_to_location / add_notifier / set_allocation_strategy
  - store_package(location_id, package, user)
  - retrieve_package(location_id, package_id, code, user)
  - cancel_package(location_id, package_id, user)
  - notify_all(event, user, package)
```

### Step 2.3: Define Enumerations (State & Type)

```python
class LockerSlotStatus(Enum):
    EMPTY = "empty"          # available
    OCCUPIED = "occupied"    # has a package
    RESERVED = "reserved"    # maintenance / out-of-service

class PackageStatus(Enum):
    PENDING = "pending"      # created, awaiting storage
    STORED = "stored"        # in a locker
    RETRIEVED = "retrieved"  # picked up
    EXPIRED = "expired"      # not retrieved in time
    CANCELLED = "cancelled"  # user cancelled

class LockerSize(Enum):
    SMALL = 1                # max 2kg
    MEDIUM = 2               # max 10kg
    LARGE = 3                # max 30kg
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Location** | Group lockers geographically | Can't scale to many sites |
| **Locker** | Bank of slots | Can't organize inventory |
| **LockerSlot** | Atomic allocation unit | Can't prevent double-booking |
| **Package** | Lifecycle + pickup code | No tracking or secure retrieval |
| **User** | Ownership + notifications | Can't verify or notify |
| **LockerSystem** | Central coordination | No thread-safe single source of truth |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Store Package** ⭐ CRITICAL
```python
def store_package(location_id: str, package: Package, user: User) -> dict:
    """
    Allocate a slot and store a package.

    Precondition: location exists and has an EMPTY slot fitting package.size
    Postcondition: slot OCCUPIED, package.status == STORED

    Returns: {"success": True, "code": pickup_code, "slot": slot_id}

    Raises:
      - Location not found
      - No available slots

    Concurrency: THREAD-SAFE (system lock — atomic allocate + occupy)
    """
    pass
```

#### **2. Retrieve Package** ⭐ CRITICAL
```python
def retrieve_package(location_id: str, package_id: str, pickup_code: str, user: User) -> dict:
    """
    Verify the pickup code and release the slot.

    Precondition: package stored at location; pickup_code matches
    Postcondition: slot EMPTY, package.status == RETRIEVED

    Returns: {"success": True, "message": "Package retrieved"}
    Raises: Location not found / Package not found / invalid code

    Concurrency: THREAD-SAFE
    """
    pass
```

#### **3. Cancel Package**
```python
def cancel_package(location_id: str, package_id: str, user: User) -> dict:
    """Cancel a stored package and free its slot. Returns {"success": True}."""
    pass
```

#### **4. Setup & Configuration**
```python
def add_location(location: Location) -> None: ...
def add_locker_to_location(location_id: str, locker: Locker) -> None: ...
def add_notifier(notifier: Notifier) -> None: ...
def set_allocation_strategy(strategy: AllocationStrategy) -> None: ...   # BestFit | FirstAvailable
```

### Step 3.2: Failure Model

The reference implementation raises `Exception` with a message for the interview. Production would use a typed hierarchy:

```python
class LockerException(Exception): ...
class LocationNotFoundError(LockerException): ...
class NoAvailableSlotError(LockerException): ...
class PackageNotFoundError(LockerException): ...
class InvalidPickupCodeError(LockerException): ...
class PackageExpiredError(LockerException): ...
```

### Step 3.3: API Usage Example

```python
system = LockerSystem()
location = Location("LOC001", "Times Square", "42 Times Square, NYC", "New York")
system.add_location(location)
system.add_locker_to_location("LOC001", Locker("LOCK001", location))
system.add_notifier(EmailNotifier())

pkg = Package("PKG001", "USER001", LockerSize.SMALL)
res = system.store_package("LOC001", pkg, user)      # -> pickup code + slot
system.retrieve_package("LOC001", "PKG001", res["code"], user)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
LockerSystem HAS-A locations (1:N Composition)
  └─ System owns all locations

Location HAS-A lockers (1:N Composition)
  └─ Each location owns its lockers

Locker HAS-A slots (1:N Composition)
  └─ Each locker owns its slots

LockerSlot STORES Package (0:1 Association)
  └─ A slot holds at most one package

Package OWNED-BY User (1:1 Association)
  └─ Each package belongs to one user

LockerSystem USES-A AllocationStrategy (1:1 Composition)
  └─ Pluggable slot-allocation algorithm

LockerSystem NOTIFIES Notifier (1:N Association)
  └─ Multiple notifiers listen to events
```

### Step 4.2: Complete UML Class Diagram

```
┌─────────────────────────┐
│   LockerSystem          │ ◆ Singleton
│   (Singleton)           │
├─────────────────────────┤
│ - locations[]           │
│ - allocation_strategy   │
│ - notifiers[]           │
├─────────────────────────┤
│ + store_package()       │
│ + retrieve_package()    │
│ + cancel_package()      │
│ + add_location()        │
│ + add_notifier()        │
└────────┬────────────────┘
         │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌──────────────┐  ┌──────────┐  ┌────────────┐
│  Location    │  │ Strategy │  │ Notifier   │
├──────────────┤  │(Abstract)│  │(Abstract)  │
│ - name       │  ├──────────┤  ├────────────┤
│ - address    │  │allocate()│  │notify()    │
│ - lockers[]  │  └──────────┘  └────────────┘
└──────────────┘        ▲              ▲
       │                │              │
       │   ┌────────────┴──────┐  ┌────┴────────┬────────┐
       │ ┌─────────────────┐ ┌──────────────┐ ┌──────┐ ┌────────┐
       │ │BestFitAllocation│ │FirstAvailable│ │Email │ │SMS     │
       │ └─────────────────┘ └──────────────┘ └──────┘ └────────┘
       ▼
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│   Locker     │ 1:N    │   LockerSlot     │ 0:1    │   Package    │
├──────────────┤───────▶├──────────────────┤───────▶├──────────────┤
│ - id         │        │ - size (S/M/L)   │ stores │ - status     │
│ - slots[]    │        │ - status         │        │ - pickup_code│
│ + store()    │        │ + occupy()       │        │ - expires_at │
│ + retrieve() │        │ + release()      │        │ + is_expired()│
└──────────────┘        └──────────────────┘        └──────┬───────┘
                                                      OWNED-BY │ 1:1
                                                            ▼
                                                     ┌──────────────┐
                                                     │     User     │
                                                     ├──────────────┤
                                                     │ - email/phone│
                                                     └──────────────┘

PACKAGE STATE MACHINE:
PENDING → STORED → RETRIEVED
              ├──→ EXPIRED   (not picked up in time)
              └──→ CANCELLED (user cancels)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| LockerSystem → Locations | 1:N | Composition | System owns all locations |
| Location → Lockers | 1:N | Composition | Location owns its lockers |
| Locker → LockerSlots | 1:N | Composition | Locker owns its slots |
| LockerSlot → Package | 0:1 | Association | A slot stores at most one package |
| Package → User | 1:1 | Association | Package belongs to one user |
| LockerSystem → AllocationStrategy | 1:1 | Composition | One active strategy |
| LockerSystem → Notifiers | 1:N | Association | System notifies many listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For LockerSystem)

**Problem**: Multiple threads accessing the locker system cause race conditions and state corruption.

**Solution**: A single LockerSystem instance with a lock guarding all mutations.

```python
class LockerSystem:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Atomic operations via lock, ✅ Double-checked locking
**Trade-off**: ⚠️ Global state; for a fleet, run one instance per location

---

### Pattern 2: **Strategy** (For Slot Allocation)

**Problem**: Slot allocation has multiple valid algorithms (BestFit vs FirstAvailable).

**Solution**: An `AllocationStrategy` interface with pluggable implementations.

```python
class AllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, locker, size): ...

class BestFitAllocation(AllocationStrategy):
    def allocate(self, locker, size):
        suitable = [s for s in locker.slots
                    if s.size.value >= size.value and s.status == LockerSlotStatus.EMPTY]
        return min(suitable, key=lambda s: s.size.value) if suitable else None
```

**Benefit**: ✅ Swap algorithms without touching core logic, ✅ Easy to test/extend
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: The core shouldn't know about Email/SMS implementation details.

**Solution**: A `Notifier` interface; register multiple observers.

```python
class Notifier(ABC):
    @abstractmethod
    def notify(self, event, user, package): ...

class EmailNotifier(Notifier):
    def notify(self, event, user, package):
        print(f"📧 Email to {user.email}: {event} - Code: {package.pickup_code}")
```

**Benefit**: ✅ Decoupling, ✅ Add SlackNotifier without changing core
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 4: **State** (For Package Lifecycle)

**Problem**: Packages have valid transitions (STORED → RETRIEVED) and invalid ones (RETRIEVED → STORED).

**Solution**: An explicit `PackageStatus` enum with validated transitions.

```python
class PackageStatus(Enum):
    PENDING = "pending"
    STORED = "stored"
    RETRIEVED = "retrieved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions prevented
**Trade-off**: ⚠️ Need explicit transition checks

---

### Pattern 5: **Factory** (For Object Creation)

**Problem**: Creating notifiers scattered across the code is hard to maintain.

**Solution**: A centralized factory.

```python
class NotifierFactory:
    @staticmethod
    def create_notifier(type_name):
        if type_name == "EMAIL":
            return EmailNotifier()
        elif type_name == "SMS":
            return SMSNotifier()
```

**Benefit**: ✅ Centralized, consistent creation
**Trade-off**: ⚠️ Extra indirection for simple cases

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Single global locker state | Consistent, thread-safe coordination |
| **Strategy** | Varying allocation algorithms | Pluggable, easy to extend |
| **Observer** | Events trigger notifications | Loose coupling, event-driven |
| **State** | Package lifecycle correctness | Invalid transitions prevented |
| **Factory** | Scattered object creation | Centralized, consistent |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
📦 Amazon Locker System - Interview Implementation
Demonstrates:
1. Sized-slot allocation (Strategy)
2. Secure pickup codes + lifecycle (State)
3. Notifications (Observer)
4. Thread-safe coordination (Singleton + lock)
"""

from datetime import datetime, timedelta
import uuid
from enum import Enum
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

# ============================================================================
# ENUMERATIONS
# ============================================================================

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

# ============================================================================
# CORE ENTITIES
# ============================================================================

class User:
    def __init__(self, user_id, name, email, phone):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone

class Location:
    def __init__(self, location_id, name, address, city):
        self.location_id = location_id
        self.name = name
        self.address = address
        self.city = city
        self.lockers = []

class Package:
    def __init__(self, package_id, user_id, size, expiry_days=7):
        self.package_id = package_id
        self.user_id = user_id
        self.size = size
        self.status = PackageStatus.PENDING
        self.pickup_code = str(uuid.uuid4())[:6].upper()
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=expiry_days)
        self.retrieved_at = None

    def is_expired(self):
        return datetime.now() > self.expires_at

    def verify_code(self, code):
        return self.pickup_code == code

class LockerSlot:
    def __init__(self, slot_id, size):
        self.slot_id = slot_id
        self.size = size
        self.status = LockerSlotStatus.EMPTY
        self.package_id = None

    def is_available(self):
        return self.status == LockerSlotStatus.EMPTY

    def occupy(self, package_id):
        if self.status != LockerSlotStatus.EMPTY:
            raise Exception("Slot not available")
        self.status = LockerSlotStatus.OCCUPIED
        self.package_id = package_id

    def release(self):
        self.status = LockerSlotStatus.EMPTY
        self.package_id = None

class Locker:
    def __init__(self, locker_id, location, num_small=5, num_medium=3, num_large=2):
        self.locker_id = locker_id
        self.location = location
        self.slots = []

        for i in range(num_small):
            self.slots.append(LockerSlot(f"{locker_id}_S{i}", LockerSize.SMALL))
        for i in range(num_medium):
            self.slots.append(LockerSlot(f"{locker_id}_M{i}", LockerSize.MEDIUM))
        for i in range(num_large):
            self.slots.append(LockerSlot(f"{locker_id}_L{i}", LockerSize.LARGE))

    def find_available_slot(self, size):
        for slot in self.slots:
            if slot.status == LockerSlotStatus.EMPTY and slot.size == size:
                return slot
        return None

    def total_available(self):
        return sum(1 for slot in self.slots if slot.status == LockerSlotStatus.EMPTY)

# ============================================================================
# STRATEGIES (Allocation)
# ============================================================================

class AllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, locker, size):
        pass

class BestFitAllocation(AllocationStrategy):
    def allocate(self, locker, size):
        suitable = [s for s in locker.slots
                    if s.size.value >= size.value and s.status == LockerSlotStatus.EMPTY]
        return min(suitable, key=lambda s: s.size.value) if suitable else None

class FirstAvailableAllocation(AllocationStrategy):
    def allocate(self, locker, size):
        for slot in locker.slots:
            if slot.size == size and slot.status == LockerSlotStatus.EMPTY:
                return slot
        return None

# ============================================================================
# OBSERVERS (Notifications)
# ============================================================================

class Notifier(ABC):
    @abstractmethod
    def notify(self, event, user, package):
        pass

class EmailNotifier(Notifier):
    def notify(self, event, user, package):
        print(f"  📧 Email to {user.email}: {event} - Code: {package.pickup_code}")

class SMSNotifier(Notifier):
    def notify(self, event, user, package):
        print(f"  📱 SMS to {user.phone}: {event} - Code: {package.pickup_code}")

class NotifierFactory:
    @staticmethod
    def create_notifier(type_name):
        if type_name == "EMAIL":
            return EmailNotifier()
        elif type_name == "SMS":
            return SMSNotifier()
        raise ValueError(f"Unknown notifier: {type_name}")

# ============================================================================
# LOCKER SYSTEM (SINGLETON)
# ============================================================================

class LockerSystem:
    _instance = None
    _lock = threading.RLock()   # re-entrant: guards both singleton init and operations

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.locations = []
                    cls._instance.notifiers = []
                    cls._instance.allocation_strategy = BestFitAllocation()
        return cls._instance

    def add_location(self, location):
        self.locations.append(location)

    def add_locker_to_location(self, location_id, locker):
        location = next((l for l in self.locations if l.location_id == location_id), None)
        if location:
            location.lockers.append(locker)

    def add_notifier(self, notifier):
        self.notifiers.append(notifier)

    def set_allocation_strategy(self, strategy):
        self.allocation_strategy = strategy

    def store_package(self, location_id, package, user):
        with self._lock:
            location = next((l for l in self.locations if l.location_id == location_id), None)
            if not location:
                raise Exception("Location not found")

            for locker in location.lockers:
                slot = self.allocation_strategy.allocate(locker, package.size)
                if slot:
                    slot.occupy(package.package_id)
                    package.status = PackageStatus.STORED
                    self.notify_all("STORED", user, package)
                    return {"success": True, "code": package.pickup_code, "slot": slot.slot_id}

            raise Exception("No available slots")

    def retrieve_package(self, location_id, package_id, pickup_code, user, package=None):
        with self._lock:
            location = next((l for l in self.locations if l.location_id == location_id), None)
            if not location:
                raise Exception("Location not found")

            for locker in location.lockers:
                for slot in locker.slots:
                    if slot.package_id == package_id:
                        if package and not package.verify_code(pickup_code):
                            raise Exception("Invalid pickup code")
                        slot.release()
                        if package:
                            package.status = PackageStatus.RETRIEVED
                            package.retrieved_at = datetime.now()
                            self.notify_all("RETRIEVED", user, package)
                        return {"success": True, "message": "Package retrieved"}

            raise Exception("Package not found")

    def cancel_package(self, location_id, package_id, user, package=None):
        with self._lock:
            location = next((l for l in self.locations if l.location_id == location_id), None)
            if not location:
                raise Exception("Location not found")

            for locker in location.lockers:
                for slot in locker.slots:
                    if slot.package_id == package_id:
                        slot.release()
                        if package:
                            package.status = PackageStatus.CANCELLED
                            self.notify_all("CANCELLED", user, package)
                        return {"success": True}

            raise Exception("Package not found")

    def notify_all(self, event, user, package):
        for notifier in self.notifiers:
            notifier.notify(event, user, package)

# ============================================================================
# DEMO
# ============================================================================

def run_demo():
    print("=" * 70)
    print("📦 AMAZON LOCKER SYSTEM - INTERACTIVE DEMO")
    print("=" * 70)

    # Setup
    system = LockerSystem()
    location = Location("LOC001", "Times Square", "42 Times Square, NYC", "New York")
    system.add_location(location)

    locker = Locker("LOCK001", location, num_small=3, num_medium=2, num_large=1)
    system.add_locker_to_location(location.location_id, locker)

    system.add_notifier(EmailNotifier())
    system.add_notifier(SMSNotifier())

    user1 = User("USER001", "Alice", "alice@email.com", "555-0001")

    print("\n✅ Demo 1: System Setup Complete")
    print(f"   Location: {location.name}")
    print(f"   Available slots: {locker.total_available()}")

    # Store Package
    package1 = Package("PKG001", user1.user_id, LockerSize.SMALL)
    result = system.store_package(location.location_id, package1, user1)

    print("\n✅ Demo 2: Store Package")
    print(f"   Pickup Code: {result['code']}")
    print(f"   Slot: {result['slot']}")

    # Wrong code rejected
    print("\n✅ Demo 3: Retrieve with wrong code (rejected)")
    try:
        system.retrieve_package(location.location_id, package1.package_id, "WRONG1", user1, package1)
    except Exception as e:
        print(f"   Rejected: {e}")

    # Retrieve Package with correct code
    system.retrieve_package(location.location_id, package1.package_id, result['code'], user1, package1)
    print("\n✅ Demo 4: Retrieve Package - Success!")
    print(f"   Package status: {package1.status.value}")
    print(f"   Available slots now: {locker.total_available()}")

    # Store + cancel
    package2 = Package("PKG002", user1.user_id, LockerSize.MEDIUM)
    system.store_package(location.location_id, package2, user1)
    system.cancel_package(location.location_id, package2.package_id, user1, package2)
    print("\n✅ Demo 5: Cancel Package")
    print(f"   Package status: {package2.status.value}")
    print(f"   Available slots now: {locker.total_available()}")

    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **store_package** | System RLock | Atomic allocate + occupy (no double-booking) |
| **retrieve_package** | System RLock | Atomic verify + release |
| **cancel_package** | System RLock | No double-free / race on slot |
| **Singleton init** | Class RLock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ Lock guards the allocate-then-occupy critical section so only one thread claims a slot
2. ✅ Re-entrant lock (`RLock`) safely covers both singleton init and operations
3. ✅ Each location is independent → shard locks per location to remove the global bottleneck
4. ✅ Notifications fire after the state change to keep critical sections short

---

## Demo Scenarios

### Scenario 1: System Setup
```
Location "Times Square" with 1 locker (3 small, 2 medium, 1 large) → 6 slots available
```

### Scenario 2: Store Package
```
Store SMALL package → BestFit picks a small slot → pickup code generated, slot occupied
📧 Email / 📱 SMS sent with the code
```

### Scenario 3: Retrieve with Wrong Code (Rejected)
```
Retrieve with "WRONG1" → "Invalid pickup code", slot stays occupied
```

### Scenario 4: Retrieve with Correct Code
```
Retrieve with valid code → slot released, package status = RETRIEVED, available slots restored
```

### Scenario 5: Cancel Package
```
Store MEDIUM package → cancel → slot freed, package status = CANCELLED
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking of the same slot?**

A: Atomic allocation under a lock — acquire lock, check slot is EMPTY, mark OCCUPIED, release. If 10 users race, only the lock holder claims it; the rest find another slot.

**Q2: How do you handle package expiry?**

A: Store `expires_at = now() + N days`. On retrieve, check `is_expired()`; a background sweep marks stale packages EXPIRED, frees the slot, and notifies the user.

**Q3: Why use the Strategy pattern for slot allocation?**

A: BestFit and FirstAvailable can be swapped without changing core logic — easy to test, optimize, and extend.

**Q4: What if a user has multiple packages?**

A: Each package gets a unique ID and pickup code; the user retrieves any independently with the correct code.

### Intermediate Questions

**Q5: How do you handle concurrent operations safely?**

A: A system lock (or DB row lock / optimistic versioning). Read slot version, check status, write owner if version matches; retry on conflict.

**Q6: How do you handle notification failures?**

A: Retry with exponential backoff, queue failed notifications, and use a circuit breaker to avoid cascading failures.

**Q7: How do you handle slot malfunction?**

A: Mark the slot RESERVED (excluded from allocation), redirect packages to nearby slots, alert maintenance with a repair deadline.

**Q8: How do you recover if a user loses the pickup code?**

A: User provides user_id + package_id; verify ownership and re-send a new code via email/SMS.

### Advanced Questions

**Q9: How do you track locker usage metrics?**

A: Log all events (store/retrieve/expiry/cancel) to a time-series DB; aggregate storage rate, retrieval rate, expiry rate, and slot utilization.

**Q10: How do you ensure data consistency?**

A: ACID transactions for slot updates so allocation is atomic — no partial updates; the DB guarantees consistency.

---

## Scaling Q&A

### Q1: How would you scale to 1000+ lockers across cities?

Each location runs an independent service + database, replicated across AZs; a central warehouse aggregates analytics. No cross-location allocation, so locations scale horizontally.

### Q2: How to prevent double-booking across distributed locations?

Strong consistency *within* a location (lock/row-lock); eventual consistency *across* locations. Different databases mean cross-location double-booking is structurally impossible.

### Q3: What databases at scale?

PostgreSQL + row locks for slot inventory (strong consistency), MongoDB for package status, Redis for the notification queue + slot-availability cache, InfluxDB for metrics.

### Q4: How to optimize for 100+ concurrent pickups?

Read replicas for queries, cached slot availability (5-min TTL), async notification queue (return success immediately), and horizontal scaling — ~100 TPS/location × 10 locations = 1000 TPS.

### Q5: How to scale notifications to 1M/day?

Publish events to Kafka; pools of email/SMS workers batch ~100 notifications to SendGrid/Twilio with retries — 99.9% delivery within 30s.

### Q6: How to partition data across 1000+ locations?

Shard by geography (location_id) with consistent hashing — queries for a location always hit one shard, no cross-shard joins, easy rebalancing.

### Q7: How to ensure 99.9% uptime at scale?

Per-location redundancy (primary + warm standbys) with health checks and <5s auto-failover; graceful degradation lets customers use a nearby location.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through store → retrieve → cancel/expire lifecycle and the package state machine
- [ ] Explain how the lock prevents double-booking
- [ ] Explain the BestFit vs FirstAvailable allocation strategies
- [ ] Explain the Observer-based notification fan-out
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss per-location sharding and distributed locks
- [ ] Discuss notification retries and slot-malfunction handling

---

**Ready for your interview? Allocate a slot and ship it! 📦**
