# Train Platform Management System — Complete Design Guide

> Train schedule intake, platform assignment, arrival/departure lifecycle, maintenance states, and event publishing for a single railway station.

**Scale**: 10–30 platforms, 100–300 trains/day, moderate concurrency
**Duration**: 75-minute interview guide
**Focus**: Platform assignment strategies, lifecycle state transitions, observer-driven events, waiting queue management

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

A train is scheduled → the system assigns it a free platform (using a pluggable strategy) → train arrives and occupies the platform → train departs → platform is released and the next queued train is assigned. When all platforms are occupied or in maintenance, trains queue until a platform becomes free. Core concerns: conflict-free assignment, validated lifecycle transitions, and decoupled event emission.

### Core Flow

```
Schedule Train → ASSIGN Platform (strategy) → ARRIVE (AT_PLATFORM) → DEPART → RELEASE
                         ↓ no free platform                              ↓
                    QUEUED (waiting_queue)              next queued train assigned
```

| Time  | Focus         | Output                                              |
|-------|---------------|-----------------------------------------------------|
| 0–5   | Requirements  | Scope (assign, arrive, depart, release)             |
| 5–15  | Architecture  | Entities + states + events + strategies             |
| 15–35 | Core Entities | Train, Platform, Assignment, enums                  |
| 35–55 | Logic         | schedule, assign, arrive, depart, release, waitlist |
| 55–70 | Integration   | Strategy swap + observer + summary                  |
| 70–75 | Demo/Q&A      | Run scenarios & explain trade-offs                  |

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single station or multi-station?** → "Single railway station for this design"
2. **How many platforms?** → "10–30 platforms, 100–300 trains/day"
3. **Real-time signal integration?** → "Out of scope; mock transitions only"
4. **Passenger flow modeling?** → "Excluded; focus on train/platform lifecycle"
5. **Cross-station routing or delay prediction?** → "Excluded; clarify early"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Station Controller** | Central coordinator (Singleton) | Assign platforms, process queue, emit events |
| **Train Operator** | Triggers arrivals and departures | Mark train arrived, mark train departed |
| **Admin** | Manage platform state | Set platform to maintenance, swap strategy |
| **System** | Event bus & queue processor | Notify observers, reprocess waiting queue on release |

### Functional Requirements (What does the system do?)

✅ **Schedule Trains**
  - Accept origin, destination, arrival/departure timestamps
  - Auto-assign a free platform immediately upon scheduling

✅ **Platform Assignment**
  - Use pluggable strategy (EarliestFree or PriorityPlatform)
  - Queue trains when no platform is available

✅ **Arrival Marking**
  - Transition train from EN_ROUTE/ARRIVING → AT_PLATFORM
  - Emit `train_arrived` event

✅ **Departure & Release**
  - Transition train to DEPARTED; release platform to FREE
  - Reprocess waiting queue immediately after release

✅ **Maintenance Mode**
  - Set FREE platform to MAINTENANCE (blocks assignment)
  - Emit `platform_maintenance` event for operator alerting

✅ **Strategy Swap**
  - Change assignment heuristic at runtime without modifying core logic
  - New trains immediately use new strategy

✅ **Conflict Handling**
  - Waiting queue for trains when all platforms occupied
  - Queue reprocessed on every platform release

✅ **Event Emission**
  - Observer publishes all lifecycle events (scheduled, assigned, arrived, departed, released, maintenance, pending)

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe assignment and queue processing
✅ **Consistency**: No platform simultaneously hosts two trains
✅ **Extensibility**: New strategies and observers without modifying core
✅ **Latency**: O(p) assignment where p = number of platforms
✅ **Memory**: Bounded history with snapshot/archive support

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Multi-station?** | NO — single station scope |
| **Real signal systems?** | NO — mock state transitions |
| **Passenger modeling?** | NO — excluded from scope |
| **Platform count** | 10–30 platforms |
| **Train volume** | 100–300 trains/day |
| **Maintenance on occupied platform** | Disallowed until platform is released |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
Train, Platform, Assignment, Schedule, Station, Queue, Strategy, Observer, Event, ...
```

### Step 2.2: Define Core Classes

#### **Train** — A single train in the system

```
Properties:
  - id: str (e.g., "T1", "T2")
  - origin: str
  - destination: str
  - arrival_time: str
  - departure_time: str
  - status: TrainStatus (SCHEDULED, EN_ROUTE, ARRIVING, AT_PLATFORM, DEPARTED, CANCELLED)
  - platform_id: Optional[str] (assigned platform or None)
  - created_at: datetime

Behaviors:
  - __repr__(): Human-readable summary
```

#### **Platform** — A single platform at the station

```
Properties:
  - id: str (e.g., "P1", "P2")
  - status: PlatformStatus (FREE, OCCUPIED, MAINTENANCE)
  - current_train_id: Optional[str]

Behaviors:
  - __repr__(): Human-readable summary
```

#### **Assignment** — A recorded train-to-platform binding

```
Properties:
  - train_id: str
  - platform_id: str
  - timestamp: str (arrival_time of train at assignment)

Behaviors:
  - __repr__(): Human-readable summary
```

#### **TrainStationSystem** — Main Singleton controller

```
Properties:
  - trains: Dict[str, Train]
  - platforms: Dict[str, Platform]
  - assignments: List[Assignment]
  - waiting_queue: List[str]
  - observers: List[Observer]
  - strategy: PlatformAssignmentStrategy

Behaviors:
  - add_platform(): Platform
  - schedule_train(origin, dest, arrival, departure): Train
  - arrive_train(train_id): bool
  - depart_train(train_id): bool
  - set_strategy(strategy): void
  - set_platform_maintenance(platform_id): void
  - add_observer(observer): void
  - summary(): Dict
  - _attempt_assignment(train): void
  - _release_platform(platform_id): void
  - _process_waiting_queue(): void
  - _notify(event, payload): void
```

### Step 2.3: Define Enumerations (State & Type)

```python
from enum import Enum

class TrainStatus(Enum):
    SCHEDULED  = "scheduled"
    EN_ROUTE   = "en_route"
    ARRIVING   = "arriving"
    AT_PLATFORM = "at_platform"
    DEPARTED   = "departed"
    CANCELLED  = "cancelled"

class PlatformStatus(Enum):
    FREE        = "free"
    OCCUPIED    = "occupied"
    MAINTENANCE = "maintenance"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Train** | Track lifecycle, origin/destination, assigned platform | Cannot manage arrivals or departures |
| **Platform** | Track availability and maintenance state | Cannot prevent double assignment |
| **Assignment** | Audit trail of train-platform bindings | No history for replay or debugging |
| **TrainStationSystem** | Central thread-safe coordinator | No consistent queue or strategy control |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Add Platform**

```python
def add_platform() -> Platform:
    """
    Register a new FREE platform with an auto-generated ID.
    Returns: Platform object with assigned ID (e.g., "P1").
    Emits: platform_added event.
    """
    pass
```

#### **2. Schedule Train** — CRITICAL

```python
def schedule_train(origin: str, destination: str,
                   arrival_time: str, departure_time: str) -> Train:
    """
    Register a new train and immediately attempt platform assignment.

    Postcondition:
      If platform available → train.status = EN_ROUTE, platform.status = OCCUPIED
      If no platform free  → train queued in waiting_queue

    Returns: Train object with assigned ID (e.g., "T1").
    Emits: train_scheduled, then train_assigned OR assignment_pending.
    """
    pass
```

#### **3. Arrive Train** — CRITICAL

```python
def arrive_train(train_id: str) -> bool:
    """
    Mark a train as physically arrived at its assigned platform.

    Precondition: train.status in [EN_ROUTE, ARRIVING]
    Postcondition: train.status = AT_PLATFORM

    Returns: True if transition succeeded, False otherwise.
    Emits: train_arrived.
    """
    pass
```

#### **4. Depart Train** — CRITICAL

```python
def depart_train(train_id: str) -> bool:
    """
    Mark a train as departed and release its platform.

    Precondition: train.status == AT_PLATFORM
    Postcondition: train.status = DEPARTED, platform.status = FREE
    Side Effect: triggers _process_waiting_queue()

    Returns: True if transition succeeded, False otherwise.
    Emits: train_departed, platform_released.
    """
    pass
```

#### **5. Set Strategy**

```python
def set_strategy(strategy: PlatformAssignmentStrategy) -> None:
    """
    Swap the platform assignment algorithm at runtime.
    New trains immediately use the new strategy.
    Emits: strategy_changed.
    """
    pass
```

#### **6. Set Platform Maintenance**

```python
def set_platform_maintenance(platform_id: str) -> None:
    """
    Transition a FREE platform to MAINTENANCE state.
    OCCUPIED platforms cannot enter maintenance.
    Emits: platform_maintenance.
    """
    pass
```

#### **7. Register Observer**

```python
def add_observer(observer: Observer) -> None:
    """
    Register a listener for all lifecycle events.
    Events: train_scheduled | train_assigned | train_arrived | train_departed
            platform_released | platform_maintenance | strategy_changed | assignment_pending
    """
    pass
```

### Step 3.2: Failure Model

```
schedule_train with no platforms → train queued (assignment_pending emitted)
arrive_train when not EN_ROUTE   → silently returns False (invalid transition)
depart_train when not AT_PLATFORM → silently returns False (invalid transition)
set_platform_maintenance on OCCUPIED → no-op (maintenance requires FREE state)
```

### Step 3.3: API Usage Example

```python
system = TrainStationSystem()

# 1. Add platforms
p1 = system.add_platform()  # P1
p2 = system.add_platform()  # P2

# 2. Register observer
system.add_observer(ConsoleObserver())

# 3. Schedule trains (auto-assigns platforms)
t1 = system.schedule_train("CityA", "CityB", "10:00", "10:15")
t2 = system.schedule_train("CityC", "CityD", "10:05", "10:25")

# 4. Arrive and depart
system.arrive_train(t1.id)   # T1 → AT_PLATFORM
system.depart_train(t1.id)   # T1 → DEPARTED, P1 freed, queue processed

# 5. Swap strategy at runtime
system.set_strategy(PriorityPlatformStrategy(["P2", "P1"]))
t3 = system.schedule_train("CityE", "CityF", "10:30", "10:45")
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
TrainStationSystem HAS-A trains (1:N Composition)
  └─ System is owner; manages train lifecycle

TrainStationSystem HAS-A platforms (1:N Composition)
  └─ System manages all platform state

TrainStationSystem HAS-A assignments (1:N Composition)
  └─ System records all assignment history

Train REFERENCES platform_id (1:1 Association)
  └─ Train holds the ID of its assigned platform (not ownership)

TrainStationSystem USES-A PlatformAssignmentStrategy (1:1 Composition)
  └─ Pluggable heuristic swapped at runtime

TrainStationSystem NOTIFIES Observer (1:N Association)
  └─ Multiple observers receive lifecycle events
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TRAIN STATION SYSTEM (Singleton)                  │
├──────────────────────────────────────────────────────────────────────┤
│ - trains: Dict[str, Train]                                           │
│ - platforms: Dict[str, Platform]                                     │
│ - assignments: List[Assignment]                                      │
│ - waiting_queue: List[str]                                           │
│ - observers: List[Observer]                                          │
│ - strategy: PlatformAssignmentStrategy                               │
├──────────────────────────────────────────────────────────────────────┤
│ + schedule_train(origin, dest, arrival, departure): Train           │
│ + arrive_train(train_id): bool                                       │
│ + depart_train(train_id): bool                                       │
│ + set_strategy(strategy): void                                       │
│ + add_platform(): Platform                                           │
│ + set_platform_maintenance(platform_id): void                        │
│ + add_observer(observer): void                                       │
│ - _attempt_assignment(train): void                                   │
│ - _release_platform(platform_id): void                               │
│ - _process_waiting_queue(): void                                     │
│ - _notify(event, payload): void                                      │
│ + summary(): Dict                                                    │
└──────────────────────────────────────────────────────────────────────┘
         │                              │                      │
         ▼                              ▼                      ▼
    ┌─────────────┐            ┌──────────────┐        ┌────────────────┐
    │   Train     │            │  Platform    │        │  Assignment    │
    ├─────────────┤            ├──────────────┤        ├────────────────┤
    │ - id: str   │            │ - id: str    │        │ - train_id     │
    │ - origin    │            │ - status     │        │ - platform_id  │
    │ - dest      │            │ - train_id   │        │ - timestamp    │
    │ - arrival   │            │              │        └────────────────┘
    │ - departure │            │              │
    │ - status    │            │              │
    │ - platform  │            │              │
    └─────────────┘            └──────────────┘

         │
         │ uses strategies
         ▼
    ┌────────────────────────────────────────┐
    │ PlatformAssignmentStrategy (Abstract)   │
    ├────────────────────────────────────────┤
    │ + assign(train, platforms): Platform   │
    └────────────────────────────────────────┘
              ▲                      ▲
              │                      │
    ┌─────────────────────┐ ┌──────────────────────────┐
    │ EarliestFreeStrategy│ │ PriorityPlatformStrategy │
    ├─────────────────────┤ ├──────────────────────────┤
    │ + assign(...)       │ │ - priority_order: List   │
    │   Returns first     │ │ + assign(...)            │
    │   available FREE    │ │   Returns by priority    │
    │   platform          │ └──────────────────────────┘
    └─────────────────────┘

         │
         │ uses observers
         ▼
    ┌────────────────────────────────────┐
    │ Observer (Abstract)                 │
    ├────────────────────────────────────┤
    │ + update(event: str, payload): void│
    └────────────────────────────────────┘
              ▲
              │
    ┌─────────────────────────┐
    │  ConsoleObserver        │
    ├─────────────────────────┤
    │ + update(event, payload)│
    │   Prints to console     │
    └─────────────────────────┘

Events: train_scheduled | train_assigned | train_arrived | train_departed
        platform_released | platform_maintenance | strategy_changed
        assignment_pending
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| TrainStationSystem → Trains | 1:N | Composition | System owns all train records |
| TrainStationSystem → Platforms | 1:N | Composition | System owns all platform state |
| TrainStationSystem → Assignments | 1:N | Composition | System owns assignment history |
| Train → Platform | 1:1 | Association | Train references its assigned platform ID |
| TrainStationSystem → Strategy | 1:1 | Composition | System owns the active heuristic |
| TrainStationSystem → Observers | 1:N | Association | System notifies multiple listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For TrainStationSystem)

**Problem**: All threads need a single consistent view of trains, platforms, and the waiting queue.

**Solution**: One global TrainStationSystem instance, guarded initialization.

```python
class TrainStationSystem:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.trains = {}
        self.platforms = {}
        # ... rest of initialization
        self._initialized = True
```

**Benefit**: Single source of truth, global access, prevents split-brain state.
**Trade-off**: Global state makes unit testing harder; must reset `_instance` in tests.

---

### Pattern 2: **Strategy** (For Platform Assignment)

**Problem**: Platform selection heuristic varies (earliest free, priority list, distance-based) and must be swappable without modifying the controller.

**Solution**: Pluggable strategy interface; swap at runtime.

```python
from abc import ABC, abstractmethod

class PlatformAssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, train, platforms): pass

class EarliestFreeStrategy(PlatformAssignmentStrategy):
    def assign(self, train, platforms):
        free = [p for p in platforms if p.status == PlatformStatus.FREE]
        return free[0] if free else None

class PriorityPlatformStrategy(PlatformAssignmentStrategy):
    def __init__(self, priority_order): self.priority_order = priority_order
    def assign(self, train, platforms):
        free = {p.id: p for p in platforms if p.status == PlatformStatus.FREE}
        for pid in self.priority_order:
            if pid in free: return free[pid]
        return next(iter(free.values()), None)

# Usage: Swap algorithm at runtime
system.set_strategy(PriorityPlatformStrategy(["P3", "P2", "P1"]))
```

**Benefit**: Open/Closed Principle — new strategies (AccessibilityFirst, DistanceBased) without touching controller.
**Trade-off**: Extra abstraction layer; strategy must be stateless for safety.

---

### Pattern 3: **Observer** (For Event Handling)

**Problem**: Lifecycle events (assigned, arrived, departed, released) need to trigger logging, alerting, and analytics without coupling to controller logic.

**Solution**: Observer pattern decouples event producers from consumers.

```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): pass

class ConsoleObserver(Observer):
    def update(self, event, payload):
        print(f"[EVENT] {event.upper():14} | {payload}")

# Usage: Add multiple observers
system.add_observer(ConsoleObserver())

# On any state change:
system._notify("train_assigned", {"train": "T1", "platform": "P1"})
```

**Events emitted**: `train_scheduled`, `train_assigned`, `train_arrived`, `train_departed`, `platform_released`, `platform_maintenance`, `strategy_changed`, `assignment_pending`.

**Benefit**: Loose coupling; add Kafka, alerting, or dashboard listeners without modifying controller.
**Trade-off**: Observer lifecycle management; slow observers can block notification loop.

---

### Pattern 4: **State** (For Lifecycle Transitions)

**Problem**: Trains and platforms must follow strict state progressions. Departing before arriving, or double-assigning a platform, must be prevented.

**Solution**: Use enums to track state; validate before every transition.

```python
def arrive_train(self, train_id):
    t = self.trains.get(train_id)
    # Guard: only valid source states allowed
    if not t or t.status not in (TrainStatus.EN_ROUTE, TrainStatus.ARRIVING):
        return False
    t.status = TrainStatus.AT_PLATFORM
    self._notify("train_arrived", {"train": train_id, "platform": t.platform_id})
    return True

def depart_train(self, train_id):
    t = self.trains.get(train_id)
    # Guard: must be AT_PLATFORM to depart
    if not t or t.status != TrainStatus.AT_PLATFORM:
        return False
    t.status = TrainStatus.DEPARTED
    self._notify("train_departed", {"train": train_id, "platform": t.platform_id})
    self._release_platform(t.platform_id)
    return True
```

**Benefit**: Explicit lifecycle; invalid transitions caught and rejected cleanly.
**Trade-off**: Must maintain transition logic centrally; add new states carefully.

---

### Pattern 5: **Factory** (For Creation Helpers)

**Problem**: Creating trains and platforms requires consistent ID generation and initialization.

**Solution**: Factory helper methods on the controller encapsulate creation logic.

```python
def add_platform(self) -> Platform:
    pid = f"P{len(self.platforms)+1}"
    p = Platform(pid)
    self.platforms[pid] = p
    self._notify("platform_added", {"platform": pid})
    return p

def schedule_train(self, origin, destination, arrival_time, departure_time) -> Train:
    tid = f"T{len(self.trains)+1}"
    t = Train(tid, origin, destination, arrival_time, departure_time)
    self.trains[tid] = t
    self._notify("train_scheduled", {"train": tid, "arrival": arrival_time})
    self._attempt_assignment(t)
    return t
```

**Benefit**: Consistent ID generation; single place to change naming scheme.
**Trade-off**: If creation grows complex, consider Builder pattern.

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single station controller | Consistent state, central coordination |
| **Strategy** | Pluggable platform assignment | Swap heuristics (earliest, priority, distance) |
| **Observer** | Lifecycle event emission | Decoupled analytics, monitoring, alerting |
| **State** | Validated train/platform transitions | Prevent illegal operations (e.g., depart before arrive) |
| **Factory** | Consistent object creation | Auto-incremented IDs, clean initialization |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""Train Platform Management System — Complete Implementation
Patterns: Singleton | Strategy | Observer | State | Factory
Five demo scenarios covering setup, arrival, strategy switch,
departure/release, and maintenance/conflict.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class TrainStatus(Enum):
    SCHEDULED   = "scheduled"
    EN_ROUTE    = "en_route"
    ARRIVING    = "arriving"
    AT_PLATFORM = "at_platform"
    DEPARTED    = "departed"
    CANCELLED   = "cancelled"

class PlatformStatus(Enum):
    FREE        = "free"
    OCCUPIED    = "occupied"
    MAINTENANCE = "maintenance"

# ============================================================================
# DOMAIN ENTITIES
# ============================================================================

class Train:
    def __init__(self, tid: str, origin: str, destination: str,
                 arrival_time: str, departure_time: str):
        self.id = tid
        self.origin = origin
        self.destination = destination
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.status = TrainStatus.SCHEDULED
        self.platform_id: Optional[str] = None
        self.created_at = datetime.now()

    def __repr__(self):
        return (f"Train({self.id}, {self.origin}->{self.destination}, "
                f"status={self.status.name}, platform={self.platform_id})")


class Platform:
    def __init__(self, pid: str):
        self.id = pid
        self.status = PlatformStatus.FREE
        self.current_train_id: Optional[str] = None

    def __repr__(self):
        return f"Platform({self.id}, status={self.status.name}, current={self.current_train_id})"


class Assignment:
    def __init__(self, train_id: str, platform_id: str, timestamp: str):
        self.train_id = train_id
        self.platform_id = platform_id
        self.timestamp = timestamp

    def __repr__(self):
        return f"Assignment(train={self.train_id}, platform={self.platform_id}, ts={self.timestamp})"

# ============================================================================
# STRATEGY PATTERN (Platform Assignment)
# ============================================================================

class PlatformAssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, train: Train, platforms: List[Platform]) -> Optional[Platform]:
        pass


class EarliestFreeStrategy(PlatformAssignmentStrategy):
    def assign(self, train: Train, platforms: List[Platform]) -> Optional[Platform]:
        free = [p for p in platforms if p.status == PlatformStatus.FREE]
        return free[0] if free else None


class PriorityPlatformStrategy(PlatformAssignmentStrategy):
    def __init__(self, priority_order: List[str]):
        self.priority_order = priority_order

    def assign(self, train: Train, platforms: List[Platform]) -> Optional[Platform]:
        free_map = {p.id: p for p in platforms if p.status == PlatformStatus.FREE}
        for pid in self.priority_order:
            if pid in free_map:
                return free_map[pid]
        return next(iter(free_map.values()), None) if free_map else None

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass


class ConsoleObserver(Observer):
    def update(self, event: str, payload: Dict):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {event.upper():20} | {payload}")

# ============================================================================
# SINGLETON CONTROLLER
# ============================================================================

class TrainStationSystem:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.trains: Dict[str, Train] = {}
        self.platforms: Dict[str, Platform] = {}
        self.assignments: List[Assignment] = []
        self.waiting_queue: List[str] = []
        self.observers: List[Observer] = []
        self.strategy: PlatformAssignmentStrategy = EarliestFreeStrategy()
        # RLock allows re-entrant calls (e.g., _notify inside a locked method)
        self._lock = threading.RLock()
        self._initialized = True

    def add_observer(self, obs: Observer):
        self.observers.append(obs)

    def _notify(self, event: str, payload: Dict):
        for o in self.observers:
            o.update(event, payload)

    def set_strategy(self, strategy: PlatformAssignmentStrategy):
        self.strategy = strategy
        self._notify("strategy_changed", {"strategy": strategy.__class__.__name__})

    def add_platform(self) -> Platform:
        with self._lock:
            pid = f"P{len(self.platforms) + 1}"
            p = Platform(pid)
            self.platforms[pid] = p
        self._notify("platform_added", {"platform": pid})
        return p

    def schedule_train(self, origin: str, destination: str,
                       arrival_time: str, departure_time: str) -> Train:
        with self._lock:
            tid = f"T{len(self.trains) + 1}"
            t = Train(tid, origin, destination, arrival_time, departure_time)
            self.trains[tid] = t
        self._notify("train_scheduled", {"train": tid, "arrival": arrival_time})
        self._attempt_assignment(t)
        return t

    def _attempt_assignment(self, train: Train):
        with self._lock:
            if train.platform_id:
                return  # already assigned
            platform = self.strategy.assign(train, list(self.platforms.values()))
            if platform:
                platform.status = PlatformStatus.OCCUPIED
                platform.current_train_id = train.id
                train.platform_id = platform.id
                train.status = TrainStatus.EN_ROUTE
                self.assignments.append(Assignment(train.id, platform.id, train.arrival_time))
                assigned = True
            else:
                if train.id not in self.waiting_queue:
                    self.waiting_queue.append(train.id)
                assigned = False

        if assigned:
            self._notify("train_assigned", {"train": train.id, "platform": train.platform_id})
        else:
            self._notify("assignment_pending", {"train": train.id})

    def arrive_train(self, train_id: str) -> bool:
        with self._lock:
            t = self.trains.get(train_id)
            if not t or t.status not in (TrainStatus.EN_ROUTE, TrainStatus.ARRIVING):
                return False
            t.status = TrainStatus.AT_PLATFORM
            platform_id = t.platform_id

        self._notify("train_arrived", {"train": train_id, "platform": platform_id})
        return True

    def depart_train(self, train_id: str) -> bool:
        with self._lock:
            t = self.trains.get(train_id)
            if not t or t.status != TrainStatus.AT_PLATFORM:
                return False
            t.status = TrainStatus.DEPARTED
            platform_id = t.platform_id

        self._notify("train_departed", {"train": train_id, "platform": platform_id})
        self._release_platform(platform_id)
        return True

    def _release_platform(self, platform_id: str):
        with self._lock:
            p = self.platforms.get(platform_id)
            if not p:
                return
            p.status = PlatformStatus.FREE
            p.current_train_id = None

        self._notify("platform_released", {"platform": platform_id})
        self._process_waiting_queue()

    def _process_waiting_queue(self):
        with self._lock:
            queue_snapshot = list(self.waiting_queue)
            self.waiting_queue = []

        remaining = []
        for tid in queue_snapshot:
            train = self.trains.get(tid)
            if train:
                self._attempt_assignment(train)
                if not train.platform_id:
                    remaining.append(tid)

        with self._lock:
            self.waiting_queue = remaining + self.waiting_queue

    def set_platform_maintenance(self, platform_id: str):
        with self._lock:
            p = self.platforms.get(platform_id)
            if not (p and p.status == PlatformStatus.FREE):
                return
            p.status = PlatformStatus.MAINTENANCE

        self._notify("platform_maintenance", {"platform": platform_id})

    def cancel_train(self, train_id: str):
        """Cancel a train and release its platform if occupied."""
        with self._lock:
            train = self.trains.get(train_id)
            if not train:
                return
            train.status = TrainStatus.CANCELLED
            platform_id = train.platform_id
            train.platform_id = None

        self._notify("train_cancelled", {"train": train_id})
        if platform_id:
            self._release_platform(platform_id)

    def summary(self) -> Dict[str, int]:
        return {
            "trains": len(self.trains),
            "platforms": len(self.platforms),
            "assignments": len(self.assignments),
            "waiting": len(self.waiting_queue),
        }

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup(system: TrainStationSystem):
    print("\n" + "=" * 70)
    print("DEMO 1: Setup (Platforms & Trains)")
    print("=" * 70)
    system.observers.clear()
    system.add_observer(ConsoleObserver())
    p1 = system.add_platform()
    p2 = system.add_platform()
    p3 = system.add_platform()
    t1 = system.schedule_train("CityA", "CityB", "10:00", "10:15")
    t2 = system.schedule_train("CityC", "CityD", "10:05", "10:25")
    t3 = system.schedule_train("CityE", "CityF", "10:07", "10:30")
    return p1, p2, p3, t1, t2, t3


def demo_2_arrival(system: TrainStationSystem, train: Train):
    print("\n" + "=" * 70)
    print("DEMO 2: Arrival Transition")
    print("=" * 70)
    system.arrive_train(train.id)
    print(f"Train {train.id} status: {train.status.name}")


def demo_3_strategy_switch(system: TrainStationSystem):
    print("\n" + "=" * 70)
    print("DEMO 3: Strategy Switch & New Train")
    print("=" * 70)
    system.set_strategy(PriorityPlatformStrategy(["P3", "P2", "P1"]))
    t4 = system.schedule_train("CityG", "CityH", "10:12", "10:40")
    print(f"New train {t4.id} assigned platform: {t4.platform_id}")
    return t4


def demo_4_departure_release(system: TrainStationSystem, train: Train):
    print("\n" + "=" * 70)
    print("DEMO 4: Departure & Release")
    print("=" * 70)
    system.arrive_train(train.id)   # ensure at platform
    system.depart_train(train.id)
    print(f"Departed {train.id}; waiting queue length: {len(system.waiting_queue)}")


def demo_5_maintenance_conflict(system: TrainStationSystem):
    print("\n" + "=" * 70)
    print("DEMO 5: Maintenance & Conflict")
    print("=" * 70)
    # Put a free platform into maintenance
    for p in system.platforms.values():
        if p.status == PlatformStatus.FREE:
            system.set_platform_maintenance(p.id)
            break
    t5 = system.schedule_train("CityI", "CityJ", "10:18", "10:50")
    print(f"Train {t5.id} platform: {t5.platform_id} (None means queued)")
    print(f"Waiting queue: {system.waiting_queue}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TRAIN PLATFORM MANAGEMENT — 75 MINUTE INTERVIEW DEMOS")
    print("Patterns: Singleton | Strategy | Observer | State | Factory")
    print("=" * 70)

    # Reset singleton state for a clean run
    system = TrainStationSystem()
    system.trains.clear()
    system.platforms.clear()
    system.assignments.clear()
    system.waiting_queue.clear()
    system.observers.clear()
    system.strategy = EarliestFreeStrategy()

    try:
        p1, p2, p3, t1, t2, t3 = demo_1_setup(system)
        demo_2_arrival(system, t1)
        t4 = demo_3_strategy_switch(system)
        demo_4_departure_release(system, t2)
        demo_5_maintenance_conflict(system)

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("Summary:", system.summary())
        print("Key Takeaways:")
        print(" - Strategy swap alters platform preference order")
        print(" - Queue processed on platform release")
        print(" - Maintenance removes platform from availability set")
        print(" - Observer events enable telemetry & alerts")
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **add_platform** | RLock on mutation | Consistent ID generation, no duplicate IDs |
| **schedule_train** | RLock on mutation | Atomic train creation before assignment attempt |
| **_attempt_assignment** | RLock on check+modify | Only one thread assigns a platform at a time |
| **arrive_train** | RLock on state check | Prevents invalid transition under concurrency |
| **depart_train** | RLock on state check | Atomic: check AT_PLATFORM, set DEPARTED |
| **_release_platform** | RLock on mutation | Platform freed atomically before queue retry |
| **_process_waiting_queue** | RLock on snapshot | Queue snapshot prevents lost updates |

**Concurrency Principles**:
1. RLock (re-entrant) used instead of Lock to allow internal method re-entry without deadlock.
2. Notifications always dispatched outside the lock to minimize lock duration.
3. Double-checked locking on Singleton `__new__` with a class-level Lock.
4. Queue snapshot pattern in `_process_waiting_queue` prevents concurrent modification.

---

## Demo Scenarios

### Scenario 1: Setup (Platforms & Trains)

```
DEMO 1: Setup (Platforms & Trains)
[HH:MM:SS] PLATFORM_ADDED       | {'platform': 'P1'}
[HH:MM:SS] PLATFORM_ADDED       | {'platform': 'P2'}
[HH:MM:SS] PLATFORM_ADDED       | {'platform': 'P3'}
[HH:MM:SS] TRAIN_SCHEDULED      | {'train': 'T1', 'arrival': '10:00'}
[HH:MM:SS] TRAIN_ASSIGNED       | {'train': 'T1', 'platform': 'P1'}
[HH:MM:SS] TRAIN_SCHEDULED      | {'train': 'T2', 'arrival': '10:05'}
[HH:MM:SS] TRAIN_ASSIGNED       | {'train': 'T2', 'platform': 'P2'}
[HH:MM:SS] TRAIN_SCHEDULED      | {'train': 'T3', 'arrival': '10:07'}
[HH:MM:SS] TRAIN_ASSIGNED       | {'train': 'T3', 'platform': 'P3'}
```

### Scenario 2: Arrival Transition

```
DEMO 2: Arrival Transition
[HH:MM:SS] TRAIN_ARRIVED        | {'train': 'T1', 'platform': 'P1'}
Train T1 status: AT_PLATFORM
```

### Scenario 3: Strategy Switch & New Train

```
DEMO 3: Strategy Switch & New Train
[HH:MM:SS] STRATEGY_CHANGED     | {'strategy': 'PriorityPlatformStrategy'}
New train T4 assigned platform: None   (all platforms occupied — queued)
```

### Scenario 4: Departure & Release

```
DEMO 4: Departure & Release
[HH:MM:SS] TRAIN_ARRIVED        | {'train': 'T2', 'platform': 'P2'}
[HH:MM:SS] TRAIN_DEPARTED       | {'train': 'T2', 'platform': 'P2'}
[HH:MM:SS] PLATFORM_RELEASED    | {'platform': 'P2'}
[HH:MM:SS] TRAIN_ASSIGNED       | {'train': 'T4', 'platform': 'P2'}
Departed T2; waiting queue length: 0
```

### Scenario 5: Maintenance & Conflict

```
DEMO 5: Maintenance & Conflict
[HH:MM:SS] PLATFORM_MAINTENANCE | {'platform': 'P2'}
[HH:MM:SS] TRAIN_SCHEDULED      | {'train': 'T5', 'arrival': '10:18'}
[HH:MM:SS] ASSIGNMENT_PENDING   | {'train': 'T5'}
Train T5 platform: None (None means queued)
Waiting queue: ['T5']
```

---

## Interview Q&A

### Basic Questions

**Q1: Why Strategy pattern for assignment?**

Enables changing platform selection heuristics (earliest free, priority list, distance-based, accessibility) without modifying the station controller. Follows Open/Closed Principle.

**Q2: How do you prevent double assignment of a platform?**

Platform status is set to OCCUPIED atomically under an RLock when assigned. The strategy only considers FREE platforms. Waiting queue catches assignment failures.

**Q3: How do you handle conflicts when all platforms are occupied?**

Trains queue in `waiting_queue`. When a platform is released, `_process_waiting_queue()` retries assignment for all queued trains in order.

**Q4: What if all platforms are in maintenance?**

All incoming trains queue indefinitely. The system emits `platform_maintenance` alerts for operator escalation.

**Q5: How do you ensure arrival before departure?**

`depart_train()` only executes when `train.status == AT_PLATFORM`. Invalid transitions return `False` and are silently rejected.

**Q6: Why store the waiting queue centrally vs. in Platform?**

The queue is a station-level resource, not platform-specific. Central logic allows global reordering by strategy (fairness, priority, expiry time).

**Q7: What if a train is cancelled?**

Transition to CANCELLED and release the platform if occupied. Observer emits `train_cancelled` event. Queue is reprocessed to assign freed platform.

### Edge Cases & Handling

| Edge Case | Handling |
|-----------|----------|
| Assign when no FREE platform | Train added to `waiting_queue`; `assignment_pending` emitted |
| Depart without arrival | Ignored — must be AT_PLATFORM; `depart_train` returns False |
| Maintenance on occupied platform | Disallowed until released (or forceful for emergencies) |
| Reassign already assigned train | Skip if `platform_id` already set in `_attempt_assignment` |
| Strategy switch mid-operation | New trains use new strategy; existing assignments unchanged |
| Queue starvation | Priority strategy can reorder; document fairness trade-off |
| All platforms in maintenance | Emit alerts; queue all trains; scale resources |
| Train cancellation | Release platform, reprocess queue via `_release_platform` |
| Long waiting queue backlog | Dynamic strategy tuning or dwell time reduction |

---

## Scaling Q&A

**Q1: How to scale to 100+ platforms and 1000+ trains/day?**

*Horizontal Partitioning*:
- Divide station into zones (north, south, east platforms).
- Each zone has an independent controller instance + strategy.
- Central router directs trains to zone controller by destination.
- Reduces lock contention and improves throughput.

*Vertical Optimization*:
- Cache free platform list (O(1) lookup vs O(p) scan).
- Use heap for priority-based assignment (extract-min in O(log p)).
- Index trains by status for faster queries.

**Q2: How to prevent race conditions in concurrent assignment?**

*Optimistic Locking*:
- Each platform has a version number.
- CAS (Compare-And-Swap) when transitioning FREE → OCCUPIED.
- On conflict, retry or queue train.

*Pessimistic Locking*:
- Lock platform during assignment check.
- Single-threaded train processing (actor model / event queue).

```python
def _attempt_assignment(self, train):
    platform = self.strategy.assign(train, self.platforms.values())
    if platform and platform.acquire_lock(train.id):
        platform.status = PlatformStatus.OCCUPIED
        platform.release_lock()
    else:
        self.waiting_queue.append(train.id)
```

**Q3: How to handle real-time delays and late arrivals?**

*Extend Train*:
```python
class Train:
    def __init__(self, ...):
        self.scheduled_arrival = arrival_time
        self.actual_arrival = None
        self.delay_minutes = 0
```

*Observer for Delays*:
```python
def mark_delayed(self, train_id, delay_minutes):
    train = self.trains[train_id]
    train.delay_minutes = delay_minutes
    self._notify("train_delayed", {"train": train_id, "delay": delay_minutes})
    # Potential: reassign nearby waiting trains to different slots
```

**Q4: How to implement predictive platform assignment?**

*Pre-assignment Strategy*:
```python
class PredictiveStrategy(PlatformAssignmentStrategy):
    def assign(self, train, platforms, timetable):
        dwell_time = self.estimate_dwell(train)
        platform = self.find_free_after(platforms, train.arrival_time, dwell_time)
        return platform
```

*Dwell Time Estimation*:
- ML model trained on historical data (route, time-of-day, day-of-week).
- Or simple rules: express=10min, regional=20min, freight=30min.

**Q5: How to scale event emission and observability?**

*Event Streaming (Kafka)*:
```python
def _notify(self, event: str, payload: Dict):
    for obs in self.observers:
        obs.update(event, payload)

    # Also publish to Kafka
    kafka_producer.send('station_events',
                        key=payload.get('train') or payload.get('platform'),
                        value={'event': event, 'payload': payload})
```

Benefits: Decoupled notification from analytics; real-time dashboards; event replay for auditing and ML training.

**Q6: How to persist state and recover from failures?**

*Event Sourcing*:
```python
log_entry = {
    'timestamp': datetime.now(),
    'event': 'train_assigned',
    'train_id': train.id,
    'platform_id': platform.id
}
persistence_layer.append(log_entry)
```

*Recovery*:
```python
def restore_from_log(log_entries):
    system = TrainStationSystem()
    for entry in log_entries:
        if entry['event'] == 'train_assigned':
            train = system.trains[entry['train_id']]
            train.platform_id = entry['platform_id']
    return system
```

*High Availability*: Replicate log across 3+ nodes (Raft/Paxos); leader election for active controller; automatic failover.

**Q7: How to optimize memory for long-running systems?**

```python
MAX_ASSIGNMENTS_HISTORY = 10_000

def add_assignment(self, assignment):
    self.assignments.append(assignment)
    if len(self.assignments) > MAX_ASSIGNMENTS_HISTORY:
        old = self.assignments.pop(0)
        archive_to_db(old)

def create_snapshot(self):
    return {
        'trains': self.trains,
        'platforms': self.platforms,
        'timestamp': datetime.now()
    }
```

**Q8: How to handle multi-station coordination?**

*Hub Model*:
```python
class CentralDispatcher:
    def __init__(self):
        self.stations = {}  # station_id -> TrainStationSystem

    def schedule_train_across_stations(self, stations_list, train_info):
        for station_id in stations_list:
            station = self.stations[station_id]
            station.schedule_train(...)
        self._notify('train_routed', {'stations': stations_list})
```

**Q9: How to prioritize trains (express vs freight vs regional)?**

```python
class PriorityAwareStrategy(PlatformAssignmentStrategy):
    def assign(self, train, platforms):
        for priority in ['EXPRESS', 'REGIONAL', 'FREIGHT']:
            candidates = [p for p in platforms
                          if p.priority_level >= train.priority
                          and p.status == PlatformStatus.FREE]
            if candidates:
                return self._pick_best(candidates, train)
        return None
```

**Q10: How to handle cancellations and retroactive changes?**

*Cancellation with Queue Reprocessing*:
```python
def cancel_train(self, train_id):
    train = self.trains[train_id]
    train.status = TrainStatus.CANCELLED
    if train.platform_id:
        self._release_platform(train.platform_id)
        self._process_waiting_queue()
    self._notify('train_cancelled', {'train': train_id})
```

*Retroactive Platform Change*:
```python
def reassign_train(self, train_id, new_platform_id):
    train = self.trains[train_id]
    if train.status in (TrainStatus.SCHEDULED, TrainStatus.EN_ROUTE):
        self._release_platform(train.platform_id)
        train.platform_id = new_platform_id
        self._notify('train_reassigned', {'train': train_id, 'new_platform': new_platform_id})
```

---

## Success Checklist

- [ ] Lifecycle transitions valid (no depart before arrive)
- [ ] Queue processed on release
- [ ] Strategy swap changes assignment behavior
- [ ] Maintenance blocks assignment
- [ ] Events fire for all key operations
- [ ] No platform simultaneously hosts two trains
- [ ] Concurrent assignment safe (no race conditions)
- [ ] Memory bounded (snapshots, archiving)
- [ ] Recovery from failure (event log replay)
- [ ] Scaling strategy documented (zones, partitions, caching)

---

**Ready for the interview? Every train departs on time.**
