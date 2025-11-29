# Amazon Locker System - Interview Preparation Guide

> **75-Minute System Design Interview Guide** | Complete Implementation with Design Patterns & Real-world Demo

## Table of Contents
- [System Overview](#system-overview)
- [Core Entities](#core-entities)
- [Design Patterns](#design-patterns)
- [SOLID Principles](#solid-principles)
- [75-Minute Timeline](#75-minute-timeline)
- [Demo Scenarios](#demo-scenarios)
- [Interview Preparation](#interview-preparation)

---

## System Overview

**What**: A distributed locker system for receiving and retrieving packages (like Amazon Hub)  
**Scale**: 100+ concurrent operations, 1000+ locker locations worldwide  
**Key Challenge**: Manage slot allocation, prevent double-booking, handle expiry  

**Core Operations**:
- Store package in available slot
- Retrieve package with verification
- Cancel package and release slot
- Notify user via email/SMS

---

## Core Entities

| Entity | Responsibility | State |
|--------|----------------|-------|
| **Location** | Physical locker location (address, city) | Immutable (created once) |
| **Locker** | Container with multiple sized slots | Tracks available/occupied slots |
| **LockerSlot** | Individual storage unit (SMALL/MEDIUM/LARGE) | EMPTY → OCCUPIED → EMPTY or EXPIRED |
| **Package** | Item to store with lifecycle | PENDING → STORED → RETRIEVED/EXPIRED/CANCELLED |
| **User** | Customer/Admin with contact info | Created during registration |
| **LockerSystem** | Central controller (Singleton) | Manages all operations thread-safely |

---

## Design Patterns

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | Single LockerSystem instance (thread-safe) | Ensures consistent state, prevents race conditions |
| **Strategy** | Pluggable slot allocation (BestFit, FirstAvailable) | Easy to add new allocation algorithms |
| **Observer** | Notify users via Email/SMS on package events | Decoupled notification logic, extensible |
| **State** | Package lifecycle (PENDING → STORED → RETRIEVED) | Clear transitions, prevents invalid operations |
| **Factory** | Could create different Notifier types | Encapsulates object creation (optional) |

### Singleton Pattern Example
```python
# Thread-safe lazy initialization
class LockerSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### Strategy Pattern Example
```python
# Pluggable allocation algorithms
allocation_strategy = BestFitAllocation()
slot = allocation_strategy.allocate(locker, size)

# Can switch strategy at runtime
system.set_allocation_strategy(FirstAvailableAllocation())
```

---

## SOLID Principles

| Principle | Implementation |
|-----------|-----------------|
| **S** (Single Responsibility) | Each class has one reason to change (Locker manages slots, Package manages lifecycle) |
| **O** (Open/Closed) | Open for extension (new strategies/notifiers), closed for modification |
| **L** (Liskov Substitution) | Notifiers and Strategies are interchangeable implementations |
| **I** (Interface Segregation) | Minimal interfaces (AllocationStrategy, Notifier only declare needed methods) |
| **D** (Dependency Inversion) | Depend on abstractions (AllocationStrategy, Notifier) not concrete classes |

---

## 75-Minute Timeline

| Time | Section | Topics |
|------|---------|--------|
| **0-5 min** | Requirements Gathering | Scale (100+ concurrent), Features (store/retrieve/cancel), Constraints (24/7 availability) |
| **5-15 min** | Architecture Design | Singleton pattern, multi-location support, concurrency handling, notification system |
| **15-35 min** | Core Entities | Location, Locker, LockerSlot, Package, User (with code snippets and state diagrams) |
| **35-55 min** | Business Logic | Store (allocate slot, generate code, notify), Retrieve (verify code, handle expiry, free slot), Cancel (release slot, notify) |
| **55-70 min** | Integration & Edge Cases | Thread safety, slot double-booking prevention, package expiry, concurrent operations |
| **70-75 min** | Demo & Q&A | Run 5 scenarios, answer interview questions, discuss trade-offs |

---

## Demo Scenarios

| Demo | Purpose | Key Pattern |
|------|---------|------------|
| **Demo 1: Setup** | Create location, locker, register users | System initialization |
| **Demo 2: Store & Retrieve** | Single package workflow with notifications | Observer pattern (email/SMS) |
| **Demo 3: Multiple Sizes** | Different slot sizes, allocation strategy | Strategy pattern (BestFit) |
| **Demo 4: Cancellation** | Cancel and free slot | State transition + slot release |
| **Demo 5: Full Flow** | Multi-user, multi-package, mixed operations | Integration of all patterns |

**Run Demo**:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Preparation

### Files Reference
- **START_HERE.md** → 5-minute quick reference (patterns, code structure)
- **75_MINUTE_GUIDE.md** → Deep dive (complete code, UML, 12 Q&A)
- **INTERVIEW_COMPACT.py** → Executable demo (run to see patterns in action)
- **README.md** → This file (quick overview)

### Success Checklist
- ✅ Can explain all 5 design patterns (Singleton, Strategy, Observer, State, Factory)
- ✅ Can draw entity relationships (Locker HAS-A LockerSlot, Package IS-A StorageItem)
- ✅ Can discuss thread-safety mechanisms (locks in Singleton)
- ✅ Can handle edge cases (double-booking, expiry, invalid codes)
- ✅ Can explain scaling strategy (multiple locations, horizontal scaling)

### Common Interview Questions
1. *How do you prevent double-booking?* → Slot status + atomic occupy/release
2. *How do you handle package expiry?* → Check datetime on retrieve, mark EXPIRED
3. *Why use Strategy pattern?* → Different allocation algorithms without modifying core
4. *How do you notify users?* → Observer pattern with pluggable notifiers
5. *How do you scale to 1000 locations?* → Locker-per-location, replicated LockerSystem, distributed state

---

## Quick Reference

**Core Classes**: 7
- Enumerations (4): LockerSlotStatus, PackageStatus, LockerSize, UserRole
- Entities (4): Location, Locker, Package, User
- Strategies (2): BestFitAllocation, FirstAvailableAllocation
- Notifiers (2): EmailNotifier, SMSNotifier
- Controller (1): LockerSystem

**Key Methods**: 12+
- `store_package()` → Allocate slot, generate code, notify
- `retrieve_package()` → Verify code, check expiry, release slot, notify
- `cancel_package()` → Free slot, update state, notify
- `allocate()` → Find available slot (Strategy)
- `notify()` → Send notification (Observer)

**Design Metrics**:
- Thread-safety: ✅ (Singleton with locks)
- Extensibility: ✅ (Strategy + Observer patterns)
- Maintainability: ✅ (Clear separation of concerns)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              AMAZON LOCKER SYSTEM                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────┐       ┌──────────────────┐    │
│  │  LockerSystem   │       │  AllocationStrategy  │
│  │  (Singleton)    │───→   │  (Abstract)        │
│  │                 │       │  • BestFit         │
│  │ • store_pkg()   │       │  • FirstAvailable  │
│  │ • retrieve()    │       └──────────────────┘    │
│  │ • cancel()      │                               │
│  └────────┬────────┘                               │
│           │                                        │
│           ├─→ ┌──────────────┐                     │
│           │   │ Location     │                     │
│           │   │ • name       │                     │
│           │   │ • address    │                     │
│           │   └──────────────┘                     │
│           │                                        │
│           ├─→ ┌──────────────┐                     │
│           │   │ Locker       │  HAS-A  SMALL      │
│           │   │ • slots[]    │────→ MEDIUM        │
│           │   │ • location   │        LARGE       │
│           │   └──────────────┘                     │
│           │           │                            │
│           │           └─→ ┌──────────────┐        │
│           │               │ LockerSlot   │        │
│           │               │ • status     │        │
│           │               │ • package_id │        │
│           │               └──────────────┘        │
│           │                                        │
│           ├─→ ┌──────────────┐                     │
│           │   │ Package      │                     │
│           │   │ • status     │                     │
│           │   │ • expires_at │                     │
│           │   │ • pickup_code│                     │
│           │   └──────────────┘                     │
│           │                                        │
│           ├─→ ┌──────────────┐                     │
│           │   │ User         │                     │
│           │   │ • email      │                     │
│           │   │ • phone      │                     │
│           │   └──────────────┘                     │
│           │                                        │
│           └─→ ┌──────────────────┐                │
│               │ Notifier (Observer)│               │
│               │ (Abstract)         │               │
│               │ • EmailNotifier    │               │
│               │ • SMSNotifier      │               │
│               └──────────────────┘                │
│                                                    │
└─────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Read START_HERE.md** for 5-minute quick reference
2. **Study 75_MINUTE_GUIDE.md** for complete code walkthrough
3. **Run INTERVIEW_COMPACT.py** to see patterns in action
4. **Practice explaining** each pattern with examples
5. **Mock interview** with focus on edge cases (expiry, double-booking, concurrency)

---

*Last updated: 2024 | For detailed Q&A and code, see 75_MINUTE_GUIDE.md*
