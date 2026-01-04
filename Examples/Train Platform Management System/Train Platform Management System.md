# Train Platform Management System — 75-Minute Interview Guide

## ⏱️ Quick Start Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Scope (assign, arrive, depart, release) |
| 5–15 | Architecture | Entities + states + events + strategies |
| 15–35 | Core Entities | Train, Platform, Assignment, enums |
| 35–55 | Logic | schedule, assign, arrive, depart, release, wait list |
| 55–70 | Integration | Strategy swap + observer + summary |
| 70–75 | Demo/Q&A | Run scenarios & explain trade-offs |

## 🎯 Quick Reference

### Core Entities
- **Train**: (id, origin, destination, arrival_time, departure_time, status)
- **Platform**: (id, status, current_train_id)
- **Assignment**: (train_id, platform_id, timestamp)
- **Enums**: TrainStatus (SCHEDULED, EN_ROUTE, ARRIVING, AT_PLATFORM, DEPARTED, CANCELLED)
- **PlatformStatus**: (FREE, OCCUPIED, MAINTENANCE)

### Design Patterns
- **Singleton**: One station controller coordinates all assignments
- **Strategy**: PlatformAssignmentStrategy (EarliestFree vs PriorityPlatform) pluggable
- **Observer**: Emits events for assignment, arrival, departure, release, maintenance
- **State**: Enforce valid lifecycle transitions (no depart before arrive, no double assign)
- **Factory**: Helper methods create trains/platforms with auto-incremented IDs

## 📋 System Overview

**Purpose**: Manage train schedule intake, platform assignment, arrival/departure transitions, maintenance states, and event publishing for a single railway station.

**Scale**: 10–30 platforms, 100–300 trains/day, moderate concurrency.

**Excluded (clarify early)**: Cross-station routing, passenger flow modeling, delay prediction, multi-station synchronization, signal safety systems.

---
## Functional Requirements
| Requirement | Included | Notes |
|-------------|----------|-------|
| Schedule trains | ✅ | Provide arrival/departure timestamps |
| Assign platform | ✅ | Based on strategy & availability |
| Arrival marking | ✅ | Transition to AT_PLATFORM |
| Departure & release | ✅ | Free platform, process queue |
| Maintenance mode | ✅ | Platform unavailable while in maintenance |
| Strategy swap | ✅ | Change assignment heuristic at runtime |
| Conflict handling | ✅ | Waiting queue for trains |
| Event emission | ✅ | Observer publishes lifecycle events |

---
## Design Patterns & Benefits
| Pattern | Domain Use | Benefit |
|---------|------------|---------|
| Singleton | Station controller | Central coordination, single source of truth |
| Strategy | Platform assignment | Pluggable heuristics (earliest free, priority, distance-based) |
| Observer | Operational events | Decoupled analytics, monitoring, alerting |
| State | Train & Platform status | Validated transitions, prevent illegal operations |
| Factory | Creation helpers | Consistent ID generation & object initialization |

---
## Data Model: Enumerations & Constants
```python
from enum import Enum

class TrainStatus(Enum):
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    ARRIVING = "arriving"
    AT_PLATFORM = "at_platform"
    DEPARTED = "departed"
    CANCELLED = "cancelled"

class PlatformStatus(Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
```

---
## Core Classes
```python
class Train:
    def __init__(self, tid, origin, destination, arrival_time, departure_time):
        self.id=tid; self.origin=origin; self.destination=destination
        self.arrival_time=arrival_time; self.departure_time=departure_time
        self.status=TrainStatus.SCHEDULED; self.platform_id=None

class Platform:
    def __init__(self, pid):
        self.id=pid; self.status=PlatformStatus.FREE; self.current_train_id=None

class Assignment:
    def __init__(self, train_id, platform_id, timestamp):
        self.train_id=train_id; self.platform_id=platform_id; self.timestamp=timestamp
```

---
## Strategy Pattern: Platform Assignment
```python
from abc import ABC, abstractmethod

class PlatformAssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, train, platforms): pass

class EarliestFreeStrategy(PlatformAssignmentStrategy):
    def assign(self, train, platforms):
        free=[p for p in platforms if p.status==PlatformStatus.FREE]
        return free[0] if free else None

class PriorityPlatformStrategy(PlatformAssignmentStrategy):
    def __init__(self, priority_order): self.priority_order=priority_order
    def assign(self, train, platforms):
        free={p.id:p for p in platforms if p.status==PlatformStatus.FREE}
        for pid in self.priority_order:
            if pid in free: return free[pid]
        return next(iter(free.values()), None)
```

---
## Observer Pattern: Event Handling
```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): pass

class ConsoleObserver(Observer):
    def update(self, event, payload): print(f"[EVENT] {event.upper():14} | {payload}")
```
**Events**: `train_scheduled`, `train_assigned`, `train_arrived`, `train_departed`, `platform_released`, `platform_maintenance`, `strategy_changed`, `assignment_pending`.

---
## Singleton Controller: TrainStationSystem
```python
class TrainStationSystem:
    _instance=None
    def __new__(cls):
        if not cls._instance: cls._instance=super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self,'_init',False): return
        self.trains={}; self.platforms={}; self.waiting_queue=[]; self.assignments=[]
        self.observers=[]; self.strategy=EarliestFreeStrategy(); self._init=True
    def add_observer(self,o): self.observers.append(o)
    def _notify(self,e,p): [obs.update(e,p) for obs in self.observers]
    def add_platform(self):
        pid=f"P{len(self.platforms)+1}"; self.platforms[pid]=Platform(pid); return self.platforms[pid]
    def schedule_train(self, origin, destination, arrival_time, departure_time):
        tid=f"T{len(self.trains)+1}"; t=Train(tid, origin, destination, arrival_time, departure_time)
        self.trains[tid]=t; self._notify("train_scheduled",{"train":tid,"arrival":arrival_time}); self._attempt_assignment(t); return t
```
```python
    def _attempt_assignment(self, train):
        platform=self.strategy.assign(train, self.platforms.values())
        if platform:
            platform.status=PlatformStatus.OCCUPIED; platform.current_train_id=train.id
            train.platform_id=platform.id; train.status=TrainStatus.EN_ROUTE
            self.assignments.append(Assignment(train.id, platform.id, arrival_time=train.arrival_time))
            self._notify("train_assigned",{"train":train.id,"platform":platform.id})
        else:
            self.waiting_queue.append(train.id); self._notify("assignment_pending",{"train":train.id})
    def set_strategy(self,strategy):
        self.strategy=strategy; self._notify("strategy_changed",{"strategy":strategy.__class__.__name__})
    def arrive_train(self, train_id):
        t=self.trains.get(train_id); 
        if t and t.status in (TrainStatus.EN_ROUTE, TrainStatus.ARRIVING):
            t.status=TrainStatus.AT_PLATFORM; self._notify("train_arrived",{"train":train_id,"platform":t.platform_id})
    def depart_train(self, train_id):
        t=self.trains.get(train_id)
        if t and t.status==TrainStatus.AT_PLATFORM:
            t.status=TrainStatus.DEPARTED; self._notify("train_departed",{"train":train_id,"platform":t.platform_id}); self._release_platform(t.platform_id)
    def _release_platform(self, platform_id):
        p=self.platforms.get(platform_id)
        if p:
            p.status=PlatformStatus.FREE; p.current_train_id=None; self._notify("platform_released",{"platform":platform_id})
            self._process_waiting()
    def _process_waiting(self):
        if not self.waiting_queue: return
        remaining=[]
        for tid in self.waiting_queue:
            train=self.trains[tid]; self._attempt_assignment(train)
            if train.platform_id is None: remaining.append(tid)
        self.waiting_queue=remaining
    def set_platform_maintenance(self, platform_id):
        p=self.platforms.get(platform_id)
        if p and p.status==PlatformStatus.FREE:
            p.status=PlatformStatus.MAINTENANCE; self._notify("platform_maintenance",{"platform":platform_id})
```

---
## UML Class Diagram

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

---
## Demo Flow

1. **Setup**: Create platforms (P1, P2, P3) + register observer
2. **Arrival**: Mark train1 as AT_PLATFORM
3. **Strategy Switch**: Change to PriorityPlatformStrategy; schedule train4
4. **Departure & Release**: Train departs; queued train gets assigned platform
5. **Maintenance & Conflict**: Set platform to maintenance; schedule train5 → queued

---
## Demo Execution

Run the compact implementation:
```bash
python3 INTERVIEW_COMPACT.py
```

Expected output:
```
DEMO 1: Setup (Platforms & Trains)
[HH:MM:SS] PLATFORM_ADDED   | {'platform': 'P1'}
[HH:MM:SS] TRAIN_SCHEDULED   | {'train': 'T1', 'arrival': '10:00'}
[HH:MM:SS] TRAIN_ASSIGNED    | {'train': 'T1', 'platform': 'P1'}
...
DEMO 2: Arrival Transition
[HH:MM:SS] TRAIN_ARRIVED     | {'train': 'T1', 'platform': 'P1'}
...
```

---


## Interview Q&A: Core Concepts

**Q1: Why Strategy pattern for assignment?**  
Enables changing platform selection heuristics (earliest free, priority list, distance-based, accessibility) without modifying the station controller. Follows Open/Closed Principle.

**Q2: How to prevent double assignment of a platform?**  
Platform status is set to OCCUPIED atomically when assigned. Strategy only returns FREE platforms. Waiting queue catches assignment failures.

**Q3: How do you handle conflicts when all platforms are occupied?**  
Trains queue in `waiting_queue`. When a platform is released, `_process_waiting_queue()` retries assignment.

**Q4: What if all platforms are in maintenance?**  
All incoming trains queue indefinitely. System should emit alerts (`platform_maintenance`) for operator escalation.

**Q5: Ensure arrival before departure?**  
Only allow `depart_train()` when `train.status == AT_PLATFORM`. Invalid transitions are ignored.

**Q6: Why store the waiting queue centrally vs in Platform?**  
Queue is station-level resource, not platform-specific. Central logic allows global reordering by strategy (fairness, priority).

**Q7: What if a train is cancelled?**  
Transition to CANCELLED and release the platform if occupied. Observer emits `train_cancelled` event.

---
## Interview Q&A: Scaling & Performance

**Q1: How to scale to 100+ platforms and 1000+ trains/day?**

*Horizontal Partitioning*:
- Divide station into zones (north, south, east platforms).
- Each zone has independent controller instance + strategy.
- Central router directs trains to zone controller by destination.
- Reduces lock contention and improves throughput.

*Vertical Optimization*:
- Cache free platform list (O(1) lookup vs O(n) scan).
- Use heap for priority-based assignment (extract-min in O(log p)).
- Index trains by status for faster queries.

**Q2: How to prevent race conditions in concurrent assignment?**

*Optimistic Locking*:
- Each platform has version number.
- CAS (Compare-And-Swap) when transitioning FREE → OCCUPIED.
- On conflict, retry or queue train.

*Pessimistic Locking*:
- Lock platform during assignment check.
- Single-threaded train processing (actor model / event queue).

**Code sketch (optimistic)**:
```python
def _attempt_assignment(self, train):
    platform = self.strategy.assign(train, self.platforms.values())
    if platform and platform.acquire_lock(train.id):
        # Assign successfully
        platform.status = PlatformStatus.OCCUPIED
        platform.release_lock()
    else:
        # Retry or queue
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
        # Look ahead: predict dwell time, arrival conflicts
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

*Benefits*:
- Decouple notification from analytics.
- Enable real-time dashboards, alerting, ML feature pipelines.
- Replay events for auditing & ML training.

**Q6: How to persist state and recover from failures?**

*Event Sourcing*:
```python
# On each state change, log to append-only log
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
        # ... replay all events
    return system
```

*High Availability*:
- Replicate log across 3+ nodes (consensus: Raft/Paxos).
- Leader election for active controller.
- Automatic failover on leader crash.

**Q7: How to optimize memory for long-running systems?**

*Limits & Cleanup*:
```python
MAX_ASSIGNMENTS_HISTORY = 10_000

def add_assignment(self, assignment):
    self.assignments.append(assignment)
    if len(self.assignments) > MAX_ASSIGNMENTS_HISTORY:
        old = self.assignments.pop(0)
        archive_to_db(old)  # Offload to DB
```

*Snapshot State*:
```python
def create_snapshot(self):
    return {
        'trains': self.trains,
        'platforms': self.platforms,
        'timestamp': datetime.now()
    }
```

**Q8: How to handle multi-station coordination?**

*Hub Model*:
- Central dispatcher receives train schedule.
- Routes train to target station controller.
- Each station manages local platform assignment.
- Dispatcher tracks train across stations.

*Code sketch*:
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

*Priority-aware Strategy*:
```python
class PriorityAwareStrategy(PlatformAssignmentStrategy):
    def assign(self, train, platforms):
        # Sort platforms by proximity to destination
        # Prefer "express" platforms for fast trains
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
        self._release_platform(train.platform_id)  # Frees up platform
        self._process_waiting_queue()  # Retry queued trains
    
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
## Edge Cases & Handling
| Edge Case | Handling |
|-----------|----------|
| Assign when no FREE platform | Train added to waiting_queue |
| Depart without arrival | Ignored (must be AT_PLATFORM) |
| Maintenance on occupied platform | Disallow until release (or forceful for emergency) |
| Reassign already assigned train | Skip if already platform_id set |
| Strategy switch mid-operation | New trains use new strategy; existing unchanged |
| Queue starvation | Priority strategy can reorder; note fairness |
| All platforms in maintenance | Emit alert; queue all trains; scale up resources |
| Train cancellation | Release platform, reprocess queue |
| Long waiting queue backlog | Consider dynamic strategy tuning or dwell time reduction |

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
"""Train Platform Management System - Interview Compact Implementation
Patterns: Singleton | Strategy | Observer | State | Factory
Five demo scenarios mirroring Airline example structure.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# ENUMERATIONS
# ============================================================================

class TrainStatus(Enum):
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    ARRIVING = "arriving"
    AT_PLATFORM = "at_platform"
    DEPARTED = "departed"
    CANCELLED = "cancelled"

class PlatformStatus(Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

# ============================================================================
# DOMAIN ENTITIES
# ============================================================================

class Train:
    def __init__(self, tid: str, origin: str, destination: str, arrival_time: str, departure_time: str):
        self.id = tid
        self.origin = origin
        self.destination = destination
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.status = TrainStatus.SCHEDULED
        self.platform_id: Optional[str] = None
        self.created_at = datetime.now()
    def __repr__(self):
        return f"Train({self.id}, {self.origin}->{self.destination}, status={self.status.name}, platform={self.platform_id})"

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
        # fallback earliest free
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
        print(f"[{ts}] {event.upper():16} | {payload}")

# ============================================================================
# SINGLETON CONTROLLER
# ============================================================================

class TrainStationSystem:
    _instance = None
    def __new__(cls):
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
        pid = f"P{len(self.platforms)+1}"
        p = Platform(pid)
        self.platforms[pid] = p
        self._notify("platform_added", {"platform": pid})
        return p
    def schedule_train(self, origin: str, destination: str, arrival_time: str, departure_time: str) -> Train:
        tid = f"T{len(self.trains)+1}"
        t = Train(tid, origin, destination, arrival_time, departure_time)
        self.trains[tid] = t
        self._notify("train_scheduled", {"train": tid, "arrival": arrival_time})
        self._attempt_assignment(t)
        return t
    def _attempt_assignment(self, train: Train):
        if train.platform_id:
            return  # already assigned
        platform = self.strategy.assign(train, list(self.platforms.values()))
        if platform:
            platform.status = PlatformStatus.OCCUPIED
            platform.current_train_id = train.id
            train.platform_id = platform.id
            train.status = TrainStatus.EN_ROUTE
            self.assignments.append(Assignment(train.id, platform.id, train.arrival_time))
            self._notify("train_assigned", {"train": train.id, "platform": platform.id})
        else:
            if train.id not in self.waiting_queue:
                self.waiting_queue.append(train.id)
            self._notify("assignment_pending", {"train": train.id})
    def arrive_train(self, train_id: str):
        t = self.trains.get(train_id)
        if not t or t.status not in (TrainStatus.EN_ROUTE, TrainStatus.ARRIVING):
            return False
        t.status = TrainStatus.AT_PLATFORM
        self._notify("train_arrived", {"train": train_id, "platform": t.platform_id})
        return True
    def depart_train(self, train_id: str):
        t = self.trains.get(train_id)
        if not t or t.status != TrainStatus.AT_PLATFORM:
            return False
        t.status = TrainStatus.DEPARTED
        self._notify("train_departed", {"train": train_id, "platform": t.platform_id})
        self._release_platform(t.platform_id)
        return True
    def _release_platform(self, platform_id: str):
        p = self.platforms.get(platform_id)
        if not p:
            return
        p.status = PlatformStatus.FREE
        p.current_train_id = None
        self._notify("platform_released", {"platform": platform_id})
        self._process_waiting_queue()
    def _process_waiting_queue(self):
        if not self.waiting_queue:
            return
        remaining = []
        for tid in self.waiting_queue:
            train = self.trains.get(tid)
            self._attempt_assignment(train)
            if not train.platform_id:
                remaining.append(tid)
        self.waiting_queue = remaining
    def set_platform_maintenance(self, platform_id: str):
        p = self.platforms.get(platform_id)
        if p and p.status == PlatformStatus.FREE:
            p.status = PlatformStatus.MAINTENANCE
            self._notify("platform_maintenance", {"platform": platform_id})
    def summary(self) -> Dict[str, int]:
        return {
            "trains": len(self.trains),
            "platforms": len(self.platforms),
            "assignments": len(self.assignments),
            "waiting": len(self.waiting_queue)
        }

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup(system: TrainStationSystem):
    print("\n" + "="*70)
    print("DEMO 1: Setup (Platforms & Trains)")
    print("="*70)
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
    print("\n" + "="*70)
    print("DEMO 2: Arrival Transition")
    print("="*70)
    system.arrive_train(train.id)
    print(f"Train {train.id} status: {train.status.name}")

def demo_3_strategy_switch(system: TrainStationSystem):
    print("\n" + "="*70)
    print("DEMO 3: Strategy Switch & New Train")
    print("="*70)
    system.set_strategy(PriorityPlatformStrategy(["P3", "P2", "P1"]))
    t4 = system.schedule_train("CityG", "CityH", "10:12", "10:40")
    print(f"New train {t4.id} assigned platform: {t4.platform_id}")
    return t4

def demo_4_departure_release(system: TrainStationSystem, train: Train):
    print("\n" + "="*70)
    print("DEMO 4: Departure & Release")
    print("="*70)
    system.arrive_train(train.id)  # ensure at platform
    system.depart_train(train.id)
    print(f"Departed {train.id}; waiting queue length: {len(system.waiting_queue)}")

def demo_5_maintenance_conflict(system: TrainStationSystem):
    print("\n" + "="*70)
    print("DEMO 5: Maintenance & Conflict")
    print("="*70)
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
    print("\n" + "="*70)
    print("TRAIN PLATFORM MANAGEMENT - 75 MINUTE INTERVIEW DEMOS")
    print("Patterns: Singleton | Strategy | Observer | State | Factory")
    print("="*70)
    system = TrainStationSystem()
    try:
        p1, p2, p3, t1, t2, t3 = demo_1_setup(system)
        demo_2_arrival(system, t1)
        t4 = demo_3_strategy_switch(system)
        demo_4_departure_release(system, t2)
        demo_5_maintenance_conflict(system)
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("Summary:")
        print(system.summary())
        print("Key Takeaways:")
        print(" • Strategy swap alters platform preference order")
        print(" • Queue processed on platform release")
        print(" • Maintenance removes platform from availability set")
        print(" • Observer events enable telemetry & alerts")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

```

---
## Tips for Success
✅ Keep assignment heuristic out of Train/Platform (Strategy)  
✅ Emit events immediately after state changes  
✅ Show clear, validated transitions  
✅ Mention delay & prediction as future concerns  
✅ Clarify exclusions (routing, signaling) early  
✅ Demonstrate scaling considerations (zones, async, event streams)  
✅ Handle edge cases gracefully (queues, maintenance, cancellations)

---
## Summary

The Train Platform Management System demonstrates:
- **Patterns in Action**: Singleton (central coordination), Strategy (pluggable assignment), Observer (event-driven extensibility), State (lifecycle), Factory (creation).
- **Conflict Resolution**: Waiting queues when no platform is free.
- **Extensibility**: Swap strategies, add observers, extend events without modifying core.
- **Scalability**: Partitioning by zones, optimistic locking, event streaming, snapshots, multi-station coordination.
- **Real-world Considerations**: Delays, cancellations, maintenance windows, predictive assignment.

Run `INTERVIEW_COMPACT.py` to see all 5 demo scenarios in action.
