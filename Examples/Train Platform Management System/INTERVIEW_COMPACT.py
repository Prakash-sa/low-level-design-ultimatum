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
