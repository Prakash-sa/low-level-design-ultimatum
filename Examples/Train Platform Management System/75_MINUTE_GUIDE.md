# Train Platform Management System – 75 Minute Deep Guide

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
