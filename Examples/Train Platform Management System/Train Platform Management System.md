# Train Platform Management System — 75-Minute Interview Guide

## Quick Start Overview

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Scope (assign, arrive, depart, release) |
| 5–15 | Architecture | Entities + states + events + strategies |
| 15–35 | Core Entities | Train, Platform, Assignment, enums |
| 35–55 | Logic | schedule, assign, arrive, depart, release, wait list |
| 55–70 | Integration | Strategy swap + observer + summary |
| 70–75 | Demo/Q&A | Run scenarios & explain trade-offs |

## 🧱 Core Entities Cheat Sheet
Train(id, origin, destination, arrival_time, departure_time, status)
Platform(id, status, current_train_id)
Assignment(train_id, platform_id, timestamp)
Enums: TrainStatus(SCHEDULED, EN_ROUTE, ARRIVING, AT_PLATFORM, DEPARTED, CANCELLED)
PlatformStatus(FREE, OCCUPIED, MAINTENANCE)

## 🛠 Patterns Talking Points
Singleton: One station controller coordinates assignments.
Strategy: PlatformAssignmentStrategy (EarliestFree vs PriorityPlatform) pluggable.
Observer: Emits events for assignment, arrival, departure, release, maintenance.
State: Prevent illegal transitions (depart before arrive, double assign platform).
Factory: Helper methods create trains/platforms with IDs.

## 🎯 Demo Order
1. Setup: Create platforms & trains + observer.
2. Assignment & Arrival: Auto-assign, mark arrival.
3. Strategy Switch: Change heuristic; attempt reassignment for waiting train.
4. Departure & Release: Train departs; platform freed; next waiting train assigned.
5. Maintenance & Conflict: Put platform into maintenance; observe waiting queue.

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Success Checklist
- [ ] Correct lifecycle transitions
- [ ] Strategy swap changes assignment behavior
- [ ] Waiting queue processed on release
- [ ] Maintenance blocks assignment
- [ ] Events printed for each state change
- [ ] Platform never hosts >1 train simultaneously

## 💬 Quick Answers
Why Strategy? → Swap assignment heuristic (e.g., distance, size) without modifying core.
Why Observer? → External monitoring/analytics decoupled from scheduling logic.
Conflict Handling? → Queue new arrivals until platform FREE.
Maintenance Impact? → Treat platform status != FREE as unavailable; skip in strategy.
Scaling? → Partition station sections; predictive arrival models; event stream (Kafka).

## 🆘 If Behind
<20m: Implement Train + Platform + simple assign & arrive.
20–50m: Add queue + departure + release.
>50m: Add strategy swap & observer events; narrate enhancements.

Focus on clarity: explicit states, events, and extensibility.


## 75-Minute Guide

## 1. Overview
Station controller slice: manages train schedule intake, platform assignment, arrival/departure transitions, maintenance states, and event publishing. Mirrors Airline design: patterns, structured timeline, clear lifecycle.

Excluded (state early): routing beyond single station, passenger flow modeling, delay prediction algorithms, multi-station synchronization, signal safety systems.

---
## 2. Functional Requirements
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
## 3. Patterns Mapping
| Pattern | Domain Use | Benefit |
|---------|------------|---------|
| Singleton | Station controller | Central coordination |
| Strategy | Platform assignment | Pluggable heuristics |
| Observer | Operational events | Decoupled analytics |
| State | Train & Platform status | Validated transitions |
| Factory | Creation helpers | Consistent IDs & setup |

---
## 4. Enumerations & Constants
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
## 5. Core Classes (Condensed)
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
## 6. Strategy Pattern
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
## 7. Observer Pattern
```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): pass

class ConsoleObserver(Observer):
    def update(self, event, payload): print(f"[EVENT] {event.upper():14} | {payload}")
```
Events: `train_scheduled`, `train_assigned`, `train_arrived`, `train_departed`, `platform_released`, `platform_maintenance`, `strategy_changed`, `assignment_pending`.

---
## 8. Singleton Controller
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
## 9. UML ASCII Diagram
```
┌──────────────────────────────────────────────────────────┐
│                 TRAIN STATION CONTROLLER                 │
└──────────────────────────────────────────────────────────┘
                   ┌────────────────────────┐
                   │ TrainStationSystem     │ ◄─ Singleton
                   ├────────────────────────┤
                   │ trains{} platforms{}   │
                   │ waiting_queue[]        │
                   │ assignments[]          │
                   │ strategy               │
                   ├────────────────────────┤
                   │ +schedule_train()      │
                   │ +arrive_train()        │
                   │ +depart_train()        │
                   │ +set_strategy()        │
                   └──────────┬─────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
              Train                    Platform
               │                          │
               └────────── Assignment ────┘

PlatformAssignmentStrategy ◄─ EarliestFreeStrategy / PriorityPlatformStrategy
Observer ◄─ ConsoleObserver
```

---
## 10. Demo Flow Outline
1. Setup: add platforms; schedule trains (assignment attempts).  
2. Arrival: mark first train arrived.  
3. Strategy Switch: change to priority strategy; schedule another train; see different assignment.  
4. Departure & Release: depart a train; queued train gets platform.  
5. Maintenance: mark a free platform maintenance; schedule new train → queued.

---
## 11. Interview Q&A
**Q1: Why Strategy for assignment?** Enables changing heuristics (e.g., shortest walking distance, accessibility priority) without altering core controller.
**Q2: Prevent double assignment?** Only pick platforms with status FREE; set status to OCCUPIED atomically when assigned.
**Q3: How handle conflicts?** Waiting queue; process after each release.
**Q4: What if all platforms in maintenance?** All trains queue; highlight need for escalation/alerts.
**Q5: Ensure arrival before departure?** Depart only from AT_PLATFORM state; invalid transitions ignored or raise.
**Q6: Scaling to larger stations?** Partition platforms by track groups; parallel controllers; event bus for coordination.
**Q7: Delay handling?** Extend Train with expected vs actual arrival; Observer emits `train_delayed` events.
**Q8: Predictive assignment?** Strategy could pre-reserve platforms based on timetable & estimated dwell times.
**Q9: Maintenance window scheduling?** Add schedule & block assignment for planned window.
**Q10: Cancellation?** Transition to CANCELLED and release platform if occupied.
**Q11: Data persistence?** Back station state with DB; use optimistic locking for platform assignment concurrency.
**Q12: Why not store queue in Platform?** Queue is station-level resource; central logic simpler.

---
## 12. Edge Cases & Guards
| Edge Case | Handling |
|-----------|----------|
| Assign when no FREE platform | Train added to waiting_queue |
| Depart without arrival | Ignored (or raise) – must be AT_PLATFORM |
| Maintenance on occupied platform | Disallow until release (simplified) |
| Reassign already assigned train | Skip – platform_id set |
| Duplicate strategy switch | Event still emitted; idempotent |
| Queue starvation | Priority strategy can reorder; note fairness concern |

---
## 13. Scaling Prompts
- Event streaming (Kafka) for analytics and delay propagation.
- Predictive dwell time modeling for smarter pre-assignment.
- High availability: leader election for station controller.
- Partition by platform zone to reduce contention.
- Telemetry observers measuring utilization and turnover.

---
## 14. Demo Snippet
```python
system = TrainStationSystem(); system.add_observer(ConsoleObserver())
for _ in range(2): system.add_platform()
train1 = system.schedule_train("CityA","CityB","10:00","10:15")
system.arrive_train(train1.id)
train2 = system.schedule_train("CityC","CityD","10:05","10:20")
system.depart_train(train1.id)  # releases platform → assigns train2
```

---
## 15. Final Checklist
- [ ] Lifecycle transitions valid
- [ ] Queue processed on release
- [ ] Strategy swap demonstrated
- [ ] Maintenance blocks assignment
- [ ] Events fire for all key operations
- [ ] No platform simultaneously hosts two trains

---
Deliver clarity: pattern motivation, explicit states, safe assignment invariants.


## Detailed Design Reference

Railway station controller that schedules trains, assigns platforms, tracks arrivals/departures, and emits operational events. Modeled in the same structured style as the Airline Management System example (patterns, lifecycle, extensibility).

**Scale (Assumed)**: 10–30 platforms, 100–300 trains/day, moderate concurrency (several simultaneous arrivals).  
**Focus**: Safe platform assignment, clear train & platform lifecycles, strategy swapping for assignment heuristics, event-driven extensibility.

---

## Core Domain Entities
| Entity | Purpose | Relationships |
|--------|---------|--------------|
| **Train** | Scheduled service with times & status | Assigned to at most one Platform |
| **Platform** | Physical track slot | Holds one Train, has status |
| **Assignment** | Mapping train→platform with timestamp | Generated by strategy |
| **Strategy** | Platform selection algorithm | Injected into system controller |
| **Observer** | Receives station events | Subscribed to system |

---

## Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns Implemented
| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single station controller instance | `TrainStationSystem.get_instance()` |
| **Strategy** | Pluggable platform assignment heuristics | `EarliestFreeStrategy` vs `PriorityPlatformStrategy` |
| **Observer** | Operational notifications | `ConsoleObserver` for arrival/departure/low_capacity |
| **State** | Explicit lifecycle modeling | `TrainStatus` (SCHEDULED→EN_ROUTE→ARRIVING→AT_PLATFORM→DEPARTED) |
| **Factory** | Encapsulated creation | System helpers: `schedule_train()`, `add_platform()` |

Optional future: Command for delay adjustments, Decorator for caching prediction results.

---

## 75-Minute Timeline
| Time | Phase | What to Code |
|------|-------|--------------|
| 0–5  | Requirements | Clarify scope (rerouting? delays? conflicts?) |
| 5–15 | Architecture | Entities + status + events + strategies |
| 15–35 | Core Entities | Train, Platform, Assignment, enums |
| 35–55 | Logic | schedule, assign, arrive, depart, release, strategy switch |
| 55–70 | Integration | Singleton controller, observer, conflict handling, summary |
| 70–75 | Demo & Q&A | Run `INTERVIEW_COMPACT.py` scenarios |

---

## Demo Scenarios (5)
1. Setup: Platforms + trains + observer registration  
2. Initial Assignment & Arrival: Auto-assign + arrival transition  
3. Strategy Switch & Reassignment: Change algorithm mid-operation  
4. Departure & Release: Train departs, platform freed  
5. Conflict & Maintenance: All occupied + maintenance platform handling

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Checklist
- [ ] Explain each pattern & justification
- [ ] Recite train lifecycle states & transitions
- [ ] Describe assignment strategy differences
- [ ] Handle conflict when no platform free (queue / wait)
- [ ] Emit events: assignment, arrival, departure, release, maintenance
- [ ] Discuss scaling (prediction, real-time telemetry, delay propagation)

---

## Key Concepts to Explain
**Assignment Strategy**: Swap heuristics (earliest free vs priority list) without changing core station logic.

**Observer Events**: Decouple notification & analytics from scheduling operations (`train_assigned`, `train_arrived`, `train_departed`, `platform_released`, `platform_maintenance`).

**Lifecycle State Management**: Prevent departure before arrival; enforce platform occupancy invariants.

**Conflict Resolution**: Queue trains awaiting free platform; simple demo uses waiting list.

---

## File Roles
| File | Purpose |
|------|---------|
| `README.md` | High-level overview & checklist |
| `START_HERE.md` | Fast timeline & talking points |
| `75_MINUTE_GUIDE.md` | Deep dive: UML, Q&A, edge cases |
| `INTERVIEW_COMPACT.py` | Working implementation & demos |

---

## Tips for Success
✅ Keep assignment heuristic out of Train/Platform (Strategy)  
✅ Emit events immediately after state changes  
✅ Show clear, validated transitions  
✅ Mention delay & prediction as future concerns  
✅ Clarify exclusions (routing, signaling, passenger load modeling) early

---

See `75_MINUTE_GUIDE.md` for in-depth design. Use `START_HERE.md` for rapid recall. Run demos via `python3 INTERVIEW_COMPACT.py`.


## Compact Code

```python
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

## UML Class Diagram (text)
````
(Classes, relationships, strategies/observers, enums)
````


## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
