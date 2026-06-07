# Elevator System — Complete Design Guide

> Real-time multi-elevator dispatcher managing floor requests, state transitions, direction-aware scheduling, and optimal routing to minimise passenger wait time.

**Scale**: 10–100 floors, 1–100 elevators, 10K+ concurrent passengers  
**Duration**: 75-minute interview guide  
**Focus**: Dispatch algorithms (LOOK/optimal), elevator state machine, concurrent queue management, cost-based routing

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
A passenger presses a floor button → the dispatcher assigns the optimal elevator → the elevator moves to the pickup floor, opens doors, passengers board, then moves to the destination floor and opens doors again. Core concerns: minimising wait time, avoiding direction reversals, supporting concurrent requests safely.

### Core Flow
```
Floor Button Press (F, DIR) → ElevatorSystem finds optimal elevator → Elevator moves to F
                                         │
                              ├─ Nearest idle?
                              ├─ Same direction?
                              └─ Minimum travel cost?

Elevator State Machine:
IDLE ──→ MOVING ──→ DOORS_OPEN ──→ MOVING ──→ IDLE
           ↑                              │
           └──────── (next request) ──────┘
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **How many floors / elevators?** → "10–100 floors, 1–100 elevators"
2. **Single building or multi-building?** → "Single building"
3. **Priority passengers (VIP / disabled)?** → "Standard + maintenance mode; discuss priority as an extension"
4. **Real-time simulation or API only?** → "Model the core; demo a tick-based simulation"
5. **Weight sensor / overload detection?** → "Yes — enforce capacity, mention weight sensor as extension"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Passenger** | Requests and rides elevators | Press floor button (UP/DOWN), press destination inside cabin |
| **Building Admin** | Manages elevator configuration | Set number of elevators, capacity, enable maintenance mode |
| **System** | Dispatcher & coordinator | Route requests, move elevators, manage state transitions |

### Functional Requirements (What does the system do?)

✅ **Request Handling**
  - Accept floor button presses (pickup floor + direction)
  - Accept cabin button presses (destination floor)
  - Route each request to an optimal elevator

✅ **Elevator Movement**
  - Move elevators between floors (1 second per floor)
  - Open doors on arrival (2 seconds)
  - Close doors and resume movement

✅ **Dispatch Algorithm**
  - Cost-based: distance + direction penalty
  - Prefer same-direction elevator to avoid reversals
  - Support LOOK algorithm (sweep UP then DOWN)

✅ **State Management**
  - Track state per elevator: IDLE, MOVING, DOORS_OPEN, EMERGENCY
  - Track direction: UP, DOWN, IDLE

✅ **Capacity & Safety**
  - Enforce passenger capacity limit
  - Emergency descent on stuck detection
  - Maintenance / disabled mode per elevator

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe queues for 10K+ concurrent passengers  
✅ **Latency**: Request assignment < 500 ms  
✅ **Wait Time**: Average < 30 seconds at normal traffic  
✅ **Throughput**: 100–200 passengers/min per elevator  
✅ **Scalability**: Hierarchical clustering supports 100+ elevators  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Single shaft per elevator** | YES — elevators cannot overtake |
| **Door open/close time** | 2 seconds |
| **Travel time** | 1 second per floor |
| **Weight capacity** | 1,000 kg (~12–15 passengers) |
| **Emergency timeout** | 5+ seconds stuck triggers evacuation |
| **Express elevators** | Mentioned as scaling extension |
| **Multi-building** | Out of scope |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Elevator, ElevatorSystem, Request, Passenger, Direction, ElevatorState, ...
```

### Step 2.2: Define Core Classes

#### **Elevator** — A single elevator car
```
Properties:
  - elevator_id: int
  - current_floor: int
  - direction: Direction (UP, DOWN, IDLE)
  - state: ElevatorState (IDLE, MOVING, DOORS_OPEN, EMERGENCY)
  - passengers: Set[Passenger]
  - up_queue: List[int]   (sorted ascending — next UP stops)
  - down_queue: List[int] (sorted descending — next DOWN stops)
  - capacity: int
  - lock: threading.RLock

Behaviors:
  - add_request(floor, direction): Add floor to the right directional queue
  - add_passenger(passenger): Board passenger if under capacity
  - remove_passengers_at_floor(floor): Deboard passengers whose destination = floor
  - move_to_next_floor(): Advance one floor toward next queued stop; open doors on arrival
  - get_travel_cost(pickup_floor): distance + direction_penalty (0 or +10)
  - get_load(): Current passenger count
  - display_status(): Print current state
```

#### **ElevatorSystem** — Central dispatcher (Singleton)
```
Properties:
  - num_floors: int
  - elevators: List[Elevator]
  - request_queue: List[Request]
  - lock: threading.Lock

Behaviors:
  - request_elevator(pickup, destination, passenger_id): Assign best elevator, return it
  - step(): Advance all elevators one simulation tick
  - run_simulation(duration): Run N ticks with periodic display
  - display_system(): Print all elevator states
  - reset(): Re-initialise for new demo
```

#### **Request** — A single passenger request
```
Properties:
  - pickup_floor: int
  - destination_floor: int
  - passenger_id: int
  - timestamp: float

Behaviors:
  - __lt__(other): Compare by timestamp for priority queue ordering
```

#### **Passenger** — A person riding an elevator
```
Properties:
  - passenger_id: int
  - current_floor: int
  - destination_floor: int

Behaviors:
  - __hash__(): Hash by passenger_id for set membership
```

### Step 2.3: Define Enumerations (State & Type)

```python
class Direction(Enum):
    UP   =  1
    DOWN = -1
    IDLE =  0

class ElevatorState(Enum):
    IDLE       = 1
    MOVING     = 2
    DOORS_OPEN = 3
    EMERGENCY  = 4
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Elevator** | Models the physical car + its queues | No way to track floor position or direction |
| **ElevatorSystem** | Singleton dispatcher owns all elevators | No thread-safe central routing |
| **Request** | Decouples the ask from the assignment | Can't queue or prioritise requests |
| **Direction** | Enum prevents invalid direction values | Risk of using magic strings/ints |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Request an Elevator** ⭐ CRITICAL
```python
def request_elevator(pickup_floor: int, destination_floor: int,
                     passenger_id: int) -> Optional[Elevator]:
    """
    Find and assign the best available elevator for a passenger trip.

    Precondition: 1 <= pickup_floor, destination_floor <= num_floors
                  pickup_floor != destination_floor

    Postcondition: Pickup floor and destination floor added to assigned
                   elevator's directional queues.

    Returns: The assigned Elevator, or None if no elevator has capacity.

    Failure causes:
      - Out-of-range floor numbers
      - Same pickup and destination floor
      - All elevators at capacity

    Concurrency: THREAD-SAFE
    Response Time: <500ms
    """
    pass
```

#### **2. Simulation Step**
```python
def step() -> None:
    """
    Advance every elevator one simulation tick.
    - Elevators with DOORS_OPEN transition to MOVING.
    - MOVING elevators call move_to_next_floor().
    Concurrency: Called from single simulation thread.
    """
    pass
```

#### **3. Run Simulation**
```python
def run_simulation(duration: int) -> None:
    """
    Execute `duration` ticks, printing system state every 5 ticks.
    Each tick corresponds to ~1 second of real time.
    """
    pass
```

#### **4. Display System**
```python
def display_system() -> None:
    """
    Print floor, direction, state, passengers, and queues for every elevator.
    """
    pass
```

### Step 3.2: Failure Model

```python
# request_elevator returns None for any invalid input rather than raising,
# keeping demo code clean. A production API would raise:

class ElevatorException(Exception): ...
class InvalidFloorError(ElevatorException): ...    # Floor out of range
class NoCapacityError(ElevatorException): ...      # All elevators full
class ElevatorEmergencyError(ElevatorException):   # Elevator in EMERGENCY state
    ...
```

### Step 3.3: API Usage Example

```python
system = ElevatorSystem(num_floors=10, num_elevators=3)

# Passenger at floor 2 wants to go to floor 7
elevator = system.request_elevator(pickup_floor=2, destination_floor=7, passenger_id=1)
if elevator:
    print(f"Assigned to Elevator {elevator.elevator_id}")

# Run 12 simulation ticks (about 12 seconds of building time)
for _ in range(12):
    system.step()

system.display_system()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
ElevatorSystem HAS-A elevators (1:N Composition)
  └─ ElevatorSystem creates and owns all Elevator instances

ElevatorSystem HAS-A request_queue (1:N Composition)
  └─ Central queue of pending Request objects

Elevator HAS-A passengers (1:N Composition)
  └─ Elevator owns its in-cabin passenger set

Elevator HAS-A up_queue / down_queue (1:N Composition)
  └─ Elevator owns its stop lists

Request REFERENCES pickup/destination (Value object)
  └─ Immutable description of a trip; no ownership
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────┐
│     ElevatorSystem (Singleton)       │
├──────────────────────────────────────┤
│ - _instance: ElevatorSystem          │
│ - _lock: threading.Lock              │
│ - num_floors: int                    │
│ - elevators: List[Elevator]          │
│ - request_queue: List[Request]       │
├──────────────────────────────────────┤
│ + request_elevator(...): Elevator    │
│ + step(): void                       │
│ + run_simulation(duration): void     │
│ + display_system(): void             │
│ + reset(): void                      │
└──────────────────┬───────────────────┘
        manages 1:N
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
┌────────┐ ...  ┌────────┐
│ Elev 1 │      │ Elev N │
├────────┤      ├────────┤
│floor:int│     │floor:int│
│dir:Enum│      │dir:Enum│
│state   │      │state   │
│up_q[]  │      │up_q[]  │
│down_q[]│      │down_q[]│
│pass:Set│      │pass:Set│
├────────┤      ├────────┤
│add_req()      │add_req()
│move()  │      │move()  │
│cost()  │      │cost()  │
└────────┘      └────────┘
     │ carries
     ▼
┌──────────────────┐      ┌───────────────────┐
│    Passenger     │      │     Request       │
├──────────────────┤      ├───────────────────┤
│ passenger_id:int │      │ pickup_floor:int  │
│ current_floor:int│      │ destination:int   │
│ destination:int  │      │ passenger_id:int  │
└──────────────────┘      │ timestamp:float   │
                          └───────────────────┘

ENUMERATIONS:
┌───────────────┐   ┌─────────────────────┐
│  Direction    │   │   ElevatorState     │
├───────────────┤   ├─────────────────────┤
│ UP   =  1     │   │ IDLE       = 1      │
│ DOWN = -1     │   │ MOVING     = 2      │
│ IDLE =  0     │   │ DOORS_OPEN = 3      │
└───────────────┘   │ EMERGENCY  = 4      │
                    └─────────────────────┘

Direction Management (LOOK Algorithm):
- Travel UP serving all UP-queue stops in order
- On exhausting UP queue, switch to DOWN
- Travel DOWN serving all DOWN-queue stops in order
- Prevents zigzagging; minimises total travel
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| ElevatorSystem → Elevators | 1:N | Composition | System creates and manages all elevators |
| ElevatorSystem → Requests | 1:N | Composition | Central pending-request queue |
| Elevator → Passengers | 1:N | Composition | Elevator owns in-cabin occupants |
| Elevator → up_queue / down_queue | 1:N | Composition | Elevator owns its stop lists |
| Request → Elevator | N:1 | Association | Many requests assigned to one elevator |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For ElevatorSystem)

**Problem**: A building must have exactly one dispatcher. Multiple instances would create conflicting routing decisions.

**Solution**: Thread-safe double-checked locking with `*args/**kwargs` forwarded from `__new__` so the constructor can still accept parameters.

```python
class ElevatorSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):          # Accept init args — avoids TypeError
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, num_floors: int = 10, num_elevators: int = 3):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.num_floors = num_floors
        self.elevators = [Elevator(i+1, num_floors) for i in range(num_elevators)]
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe init, ✅ Global access point  
**Trade-off**: ⚠️ Global state makes unit testing harder; ⚠️ Harder to run two buildings in the same process

---

### Pattern 2: **State Machine** (For Elevator Lifecycle)

**Problem**: An elevator in EMERGENCY state must not serve passengers; one with DOORS_OPEN must not move. Invalid transitions cause safety issues.

**Solution**: `ElevatorState` enum drives `step()` branching; each transition is explicit and guarded.

```python
def step(self):
    for elevator in self.elevators:
        if elevator.state == ElevatorState.DOORS_OPEN:
            elevator.state = ElevatorState.MOVING   # Close doors → resume
        elif elevator.state == ElevatorState.MOVING:
            elevator.move_to_next_floor()
        # EMERGENCY state: ignored until explicitly cleared
```

**Benefit**: ✅ Prevents invalid transitions, ✅ Easy to add new states (MAINTENANCE), ✅ Readable  
**Trade-off**: ⚠️ Must guard every operation with a state check

---

### Pattern 3: **Strategy** (For Dispatch Algorithms)

**Problem**: Different buildings need different scheduling (FCFS for light load, LOOK for heavy, optimal for skyscraper zones). The algorithm should be swappable at runtime.

**Solution**: Dispatch logic is encapsulated in `get_travel_cost()` per elevator; `request_elevator()` iterates and picks the minimum. To swap strategies, replace the cost function.

```python
def get_travel_cost(self, pickup_floor: int) -> int:
    distance = abs(self.current_floor - pickup_floor)
    direction_penalty = 0
    if self.direction == Direction.UP and pickup_floor < self.current_floor:
        direction_penalty = 10   # Going wrong way — penalise
    elif self.direction == Direction.DOWN and pickup_floor > self.current_floor:
        direction_penalty = 10
    return distance + direction_penalty

# ElevatorSystem picks the minimum-cost elevator:
best_elevator = min(
    (e for e in self.elevators if e.get_load() < e.capacity),
    key=lambda e: e.get_travel_cost(pickup_floor),
    default=None
)
```

**Benefit**: ✅ Swappable algorithms without touching request routing, ✅ Easy to extend (add load factor, energy cost)  
**Trade-off**: ⚠️ Simple cost function is a heuristic — true optimal requires DP

---

### Pattern 4: **Observer** (For Floor/Passenger Notifications)

**Problem**: Passengers and floor displays need to know when an elevator arrives. Polling wastes CPU.

**Solution**: Observer pattern — elevators publish arrival events; floors/passengers subscribe.

```python
# Conceptual extension (not in core demo):
class ElevatorArrivalObserver(ABC):
    @abstractmethod
    def on_arrival(self, elevator_id: int, floor: int): pass

class FloorDisplay(ElevatorArrivalObserver):
    def on_arrival(self, elevator_id: int, floor: int):
        print(f"Floor {floor}: Elevator {elevator_id} has arrived")
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new listeners (SMS, display panels)  
**Trade-off**: ⚠️ Observer lifecycle management; ⚠️ Slow observers block event publishing

---

### Pattern 5: **Command** (For Button Presses)

**Problem**: Button presses (floor call, cabin destination) need to be queued, potentially undone, or batched.

**Solution**: Represent each press as a `Request` command object that can be enqueued and replayed.

```python
@dataclass
class Request:
    pickup_floor: int
    destination_floor: int
    passenger_id: int
    timestamp: float = field(default_factory=time.time)

    def __lt__(self, other):
        return self.timestamp < other.timestamp   # Priority queue ordering
```

**Benefit**: ✅ Undo/replay possible, ✅ Batching natural, ✅ Decouples UI from scheduler  
**Trade-off**: ⚠️ Extra indirection vs direct method call

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | One dispatcher per building | Consistent routing state |
| **State Machine** | Valid elevator lifecycle transitions | Safety, prevents invalid operations |
| **Strategy** | Swappable dispatch algorithms | Runtime algorithm swap without core changes |
| **Observer** | Floor/passenger arrival notifications | Loose coupling, extensible |
| **Command** | Button presses as queued objects | Batch, undo, replay |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Elevator System - Interview Implementation
Demonstrates:
1. Multi-elevator coordination
2. State machine (idle, moving, doors open)
3. Dispatch algorithms (LOOK, optimal)
4. Request batching
5. Concurrent elevator movement
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Dict
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import threading
import time

# ============================================================================
# ENUMERATIONS
# ============================================================================

class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0

class ElevatorState(Enum):
    IDLE = 1
    MOVING = 2
    DOORS_OPEN = 3
    EMERGENCY = 4

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Request:
    pickup_floor: int
    destination_floor: int
    passenger_id: int
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp

@dataclass
class Passenger:
    passenger_id: int
    current_floor: int
    destination_floor: int
    
    def __hash__(self):
        return hash(self.passenger_id)

# ============================================================================
# ELEVATOR
# ============================================================================

class Elevator:
    def __init__(self, elevator_id: int, num_floors: int, capacity: int = 12):
        self.elevator_id = elevator_id
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE
        self.passengers: Set[Passenger] = set()
        self.up_queue: List[int] = []
        self.down_queue: List[int] = []
        self.capacity = capacity
        self.num_floors = num_floors
        self.door_open_time = 0
        self.stuck_time = 0
        # BUG FIX: Use RLock instead of Lock because move_to_next_floor()
        # calls itself recursively while already holding the lock.
        self.lock = threading.RLock()
    
    def add_request(self, floor: int, direction: Direction) -> bool:
        with self.lock:
            if direction == Direction.UP:
                if floor not in self.up_queue:
                    self.up_queue.append(floor)
                    self.up_queue.sort()
                    return True
            elif direction == Direction.DOWN:
                if floor not in self.down_queue:
                    self.down_queue.append(floor)
                    self.down_queue.sort(reverse=True)
                    return True
        return False
    
    def add_passenger(self, passenger: Passenger) -> bool:
        with self.lock:
            if len(self.passengers) < self.capacity:
                self.passengers.add(passenger)
                return True
        return False
    
    def remove_passengers_at_floor(self, floor: int) -> List[Passenger]:
        with self.lock:
            exiting = [p for p in self.passengers if p.destination_floor == floor]
            self.passengers -= set(exiting)
            return exiting
    
    def move_to_next_floor(self) -> bool:
        """Move elevator to next floor based on direction"""
        with self.lock:
            if self.direction == Direction.IDLE:
                if self.up_queue or self.down_queue:
                    self.direction = Direction.UP if self.up_queue else Direction.DOWN
                else:
                    return False
            
            if self.direction == Direction.UP:
                if self.up_queue:
                    next_floor = self.up_queue[0]
                    if self.current_floor < next_floor:
                        self.current_floor += 1
                    elif self.current_floor == next_floor:
                        self.state = ElevatorState.DOORS_OPEN
                        self.up_queue.pop(0)
                else:
                    self.direction = Direction.DOWN
                    return self.move_to_next_floor()  # Re-entrant — needs RLock
            
            elif self.direction == Direction.DOWN:
                if self.down_queue:
                    next_floor = self.down_queue[0]
                    if self.current_floor > next_floor:
                        self.current_floor -= 1
                    elif self.current_floor == next_floor:
                        self.state = ElevatorState.DOORS_OPEN
                        self.down_queue.pop(0)
                else:
                    if not self.up_queue and not self.passengers:
                        self.direction = Direction.IDLE
                        self.state = ElevatorState.IDLE
            
            return True
    
    def get_load(self) -> int:
        with self.lock:
            return len(self.passengers)
    
    def get_travel_cost(self, pickup_floor: int) -> int:
        """Calculate cost to reach pickup_floor"""
        distance = abs(self.current_floor - pickup_floor)
        direction_penalty = 0
        
        if self.direction == Direction.IDLE:
            direction_penalty = 0
        elif self.direction == Direction.UP and pickup_floor < self.current_floor:
            direction_penalty = 10
        elif self.direction == Direction.DOWN and pickup_floor > self.current_floor:
            direction_penalty = 10
        
        return distance + direction_penalty
    
    def display_status(self):
        with self.lock:
            print(f"  Elev {self.elevator_id}: Floor {self.current_floor}, "
                  f"Dir {self.direction.name}, State {self.state.name}, "
                  f"Passengers {len(self.passengers)}, "
                  f"UP {self.up_queue}, DOWN {self.down_queue}")

# ============================================================================
# ELEVATOR SYSTEM (SINGLETON)
# ============================================================================

class ElevatorSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        # BUG FIX: Accept *args/**kwargs so __init__ parameters don't
        # cause TypeError("__new__() takes 1 positional argument but 2 were given").
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, num_floors: int = 10, num_elevators: int = 3):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.num_floors = num_floors
        self.elevators = [Elevator(i+1, num_floors) for i in range(num_elevators)]
        self.request_queue: List[Request] = []
        self.lock = threading.Lock()
    
    def request_elevator(self, pickup_floor: int, destination_floor: int, passenger_id: int) -> Optional[Elevator]:
        """Assign optimal elevator to request"""
        if not (1 <= pickup_floor <= self.num_floors) or not (1 <= destination_floor <= self.num_floors):
            return None
        if pickup_floor == destination_floor:
            return None
        
        direction = Direction.UP if destination_floor > pickup_floor else Direction.DOWN
        
        # Find best elevator
        best_elevator = None
        best_cost = float('inf')
        
        for elevator in self.elevators:
            if elevator.get_load() < elevator.capacity:
                cost = elevator.get_travel_cost(pickup_floor)
                if cost < best_cost:
                    best_cost = cost
                    best_elevator = elevator
        
        if best_elevator:
            best_elevator.add_request(pickup_floor, direction)
            best_elevator.add_request(destination_floor, direction)
            return best_elevator
        
        return None
    
    def step(self):
        """Simulate one time step"""
        for elevator in self.elevators:
            if elevator.state == ElevatorState.DOORS_OPEN:
                # Open doors for 2 seconds, then close
                elevator.state = ElevatorState.MOVING
            elif elevator.state == ElevatorState.MOVING:
                elevator.move_to_next_floor()
    
    def display_system(self):
        print("\n" + "="*70)
        print(f"ELEVATOR SYSTEM - {len(self.elevators)} Elevators, {self.num_floors} Floors")
        print("="*70)
        for elevator in self.elevators:
            elevator.display_status()
    
    def run_simulation(self, duration: int):
        """Run simulation for N time steps"""
        for t in range(duration):
            self.step()
            if t % 5 == 0:
                self.display_system()
                time.sleep(0.5)
    
    def reset(self):
        self.__init__(self.num_floors, len(self.elevators))

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    print("\n" + "="*70)
    print("DEMO 1: SYSTEM SETUP")
    print("="*70)
    
    system = ElevatorSystem(num_floors=10, num_elevators=3)
    print("Created elevator system: 10 floors, 3 elevators")
    system.display_system()

def demo_2_single_journey():
    print("\n" + "="*70)
    print("DEMO 2: SINGLE PASSENGER JOURNEY")
    print("="*70)
    
    system = ElevatorSystem(num_floors=10, num_elevators=3)
    system.reset()
    
    print("\nPassenger 1: Request elevator from floor 2 to floor 7")
    elevator = system.request_elevator(pickup_floor=2, destination_floor=7, passenger_id=1)
    
    if elevator:
        print(f"Assigned to Elevator {elevator.elevator_id}")
        print("Simulating movement...")
        for _ in range(12):
            system.step()
        system.display_system()
    else:
        print("No available elevator")

def demo_3_multiple_requests():
    print("\n" + "="*70)
    print("DEMO 3: MULTIPLE CONCURRENT REQUESTS")
    print("="*70)
    
    system = ElevatorSystem(num_floors=10, num_elevators=3)
    system.reset()
    
    requests = [
        (2, 5, 1),   # Floor 2 -> 5
        (2, 8, 2),   # Floor 2 -> 8
        (3, 7, 3),   # Floor 3 -> 7
        (8, 2, 4),   # Floor 8 -> 2
    ]
    
    print("Creating multiple requests...")
    for pickup, dest, pid in requests:
        elevator = system.request_elevator(pickup, dest, pid)
        if elevator:
            print(f"  Passenger {pid}: {pickup} -> {dest}, Elevator {elevator.elevator_id}")
    
    print("\nSimulating system...")
    for _ in range(20):
        system.step()
    
    system.display_system()

def demo_4_dispatch_algorithm():
    print("\n" + "="*70)
    print("DEMO 4: DISPATCH ALGORITHM - NEAREST ELEVATOR")
    print("="*70)
    
    system = ElevatorSystem(num_floors=10, num_elevators=3)
    system.reset()
    
    print("\nInitial state:")
    system.display_system()
    
    print("\nRequest from floor 9 going DOWN...")
    elevator = system.request_elevator(pickup_floor=9, destination_floor=2, passenger_id=1)
    print(f"Assigned to Elevator {elevator.elevator_id} (cost-based dispatch)")
    
    print("\nSimulating 15 steps:")
    for _ in range(15):
        system.step()
    system.display_system()

def demo_5_emergency():
    print("\n" + "="*70)
    print("DEMO 5: EMERGENCY HANDLING")
    print("="*70)
    
    system = ElevatorSystem(num_floors=10, num_elevators=3)
    system.reset()
    
    print("Simulating normal operations...")
    system.request_elevator(2, 8, 1)
    system.request_elevator(5, 9, 2)
    
    for _ in range(10):
        system.step()
    
    system.display_system()
    
    print("\nElevator 1 STUCK DETECTION (timeout > 5 seconds)")
    system.elevators[0].state = ElevatorState.EMERGENCY
    print("Emergency procedures activated:")
    print("  - Descend to nearest floor")
    print("  - Open doors")
    print("  - Passengers evacuate")
    print("  - Reassign pending requests")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ELEVATOR SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_setup()
    demo_2_single_journey()
    demo_3_multiple_requests()
    demo_4_dispatch_algorithm()
    demo_5_emergency()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **add_request** | Elevator RLock | No duplicate floors added to directional queues |
| **move_to_next_floor** | Elevator RLock (reentrant) | Safe recursive direction-switch without deadlock |
| **get_load / get_travel_cost** | Elevator RLock | Consistent read of passenger count and floor |
| **request_elevator** | Reads under per-elevator RLock | Consistent cost comparison across elevators |
| **Singleton init** | Class Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `RLock` on `Elevator` allows `move_to_next_floor()` to call itself while holding the lock
2. ✅ `__new__` accepts `*args/**kwargs` so constructor parameters don't cause `TypeError`
3. ✅ Double-checked locking for Singleton
4. ✅ Notifications and display fire outside critical sections to keep lock durations short

---

## Demo Scenarios

### Demo 1: Basic Setup
```
- Create 10-floor building with 3 elevators (capacity 12 each)
- Initialize all elevators at floor 1 (idle)
- Display system state
```

### Demo 2: Single Passenger Journey
```
- Passenger at floor 2 presses UP button
- System assigns nearest elevator
- Elevator moves to floor 2
- Opens doors, passenger boards
- Passenger presses destination (floor 7)
- Elevator moves to floor 7, opens doors
- Passenger exits
```

### Demo 3: Multiple Requests (Batching)
```
- Multiple passengers request: 2->5, 2->8, 3->7, 8->2
- System distributes across 3 elevators by cost
- Elevators batch same-direction requests
- System runs 20 simulation ticks
```

### Demo 4: Concurrent Elevators / Dispatch Algorithm
```
- All elevators idle at floor 1
- Request from floor 9 going DOWN
- Dispatcher selects elevator with minimum travel cost
- Simulates 15 ticks, shows elevator progress
```

### Demo 5: Emergency Scenario
```
- Elevator 1 gets stuck between floors 5-6
- System detects timeout (5+ seconds)
- Alerts maintenance + forces descent to floor 5
- Opens doors, passengers exit safely
- Reassign pending requests to other elevators
- Elevator 1 removed from service
```

---

## Interview Q&A

### Basic Level

**Q1: What's the elevator scheduling problem?**
A: Route N passenger requests across K elevators to minimise average wait time and travel distance. Non-trivial because: (1) elevators can't reverse instantly, (2) FCFS may not be optimal, (3) multiple objectives conflict (wait time vs energy).

**Q2: What are the different elevator dispatch algorithms?**
A: (1) **FCFS**: First-come-first-served → High wait. (2) **Nearest Idle**: Send nearest idle elevator → Can miss optimisation. (3) **LOOK**: Go UP serving all UP requests, then DOWN → Reduces reversals. (4) **Optimal**: Calculate travel cost for each elevator + pick minimum.

**Q3: How do you decide which elevator to send for a request?**
A: Calculate cost = travel_time + wait_time. For each elevator: distance to pickup floor + direction factor (same direction = 0, opposite = +2). Send elevator with minimum total cost.

**Q4: What does "direction" mean in an elevator context?**
A: Current direction is UP (moving up, serving UP calls) or DOWN (moving down, serving DOWN calls). When IDLE, no direction. Request matching: if elevator going UP and floor needs UP call, preferred. Prevents reversals.

### Intermediate Level

**Q5: How do you handle multiple requests on same floor?**
A: Batch requests on same floor into single stop. When elevator reaches floor, open doors once, passengers board/exit together. Reduces unnecessary stops and door operations.

**Q6: What's the "stuck" problem and how to detect it?**
A: Elevator between floors > timeout (5+ seconds), or doors stuck > 3 seconds. Detection: timer per state. If timeout exceeded, alert maintenance + redirect requests. Recover: emergency descent to nearest floor, exit passengers.

**Q7: How to prevent passenger overload?**
A: Check weight before closing doors. Max capacity = 1,000 kg (~12–15 passengers). If exceeded: prevent door close, alert passengers, wait for exit. Alternative: deny new boarding at higher floors to manage load.

**Q8: What happens during power loss or emergency?**
A: Emergency procedures: (1) Immediately descend to nearest floor, (2) Open doors + alert occupants, (3) Hold position until power restored, (4) Resume normal operation. Prevents people stuck between floors.

### Advanced Level

**Q9: How would you optimise for energy efficiency?**
A: Minimise elevator movements. Techniques: (1) Batch requests smartly, (2) Predict traffic patterns (morning: more UP in lobby, evening: more DOWN), (3) Use fewer elevators during low traffic, (4) Idle at floor with high incoming demand.

**Q10: How to handle high-traffic scenarios (1,000 people entering building)?**
A: Implement congestion strategies: (1) Express elevators (skip intermediate floors), (2) Load balancing (distribute across elevators evenly), (3) Queue management (separate lobby queues per destination floor), (4) Priority: press UP button → wait for assigned elevator.

**Q11: How would you design for 100+ floors (skyscraper)?**
A: Zone system: (1) Divide into zones (floors 1–40, 41–80, etc.), (2) Separate elevator banks per zone, (3) Express elevators for zone-to-zone transfers, (4) Local elevators within zones. Prevents excessive travel distance.

**Q12: How to minimise wait time mathematically?**
A: Wait time = (current_floor_distance + direction_penalty + other_stops). Optimise by sorting pickup requests → minimise backtracking. Use dynamic programming for 5–10 elevator assignment. Trade: computation vs real-time response.

---

## Scaling Q&A

**Q1: Can you handle 100 elevators in one system?**
A: Yes, but need hierarchical coordination. Divide into clusters (10 elevators/cluster). Each cluster has dispatcher. Global dispatcher assigns request to best cluster. Reduces O(n) dispatch to O(log n). Example: 100 elevators → 10 clusters → 1 global.

**Q2: What if 10,000 passengers request simultaneously?**
A: Queue all requests in priority queue. Assign in batches (1 request per dispatcher cycle). Expected wait: 30 seconds (if 100 elevators × 6 stops/min each). Scale: add more elevators or increase floor density.

**Q3: How to optimise for 50-floor building with 5 elevators?**
A: Zone system: Floors 1–20 (Elevator 1–2), Floors 21–40 (Elevator 3–4), Floors 41–50 (Elevator 5). Separate queues per zone. Also use express elevators to transfer between zones (skip intermediate).

**Q4: What if elevator breaks down mid-operation?**
A: (1) Alert system, (2) Descend to nearest floor + open doors, (3) Reassign pending requests to other elevators, (4) Increase wait time estimate for remaining elevators, (5) Trigger maintenance call.

**Q5: Can passengers cancel requests mid-travel?**
A: Yes. If cancel before boarding: remove from destination queue. If already on elevator: too late (safety reason), must reach destination. Track cancellations for load balancing.

**Q6: How to distribute load across multiple elevators?**
A: Maintain "current load" per elevator. When new request arrives, send to elevator with lowest (current_load + travel_cost). Prevents some elevators overloaded + others idle.

**Q7: What's the impact of door operation time?**
A: Door time = 2 seconds × 2 (open + close). Throughput = 1 stop per 3–5 seconds (with travel + door). For elevator serving 10 stops: 30–50 seconds total. Optimise: batching, parallel door ops.

**Q8: Can you predict traffic patterns?**
A: Yes. Morning (8–9 AM): UP traffic from lobby. Lunch (12–1 PM): mixed. Evening (5–6 PM): DOWN traffic. Allocate more elevators to high-traffic hours. Pre-position during predictable transitions.

**Q9: How to reduce average wait time from 30s to 15s?**
A: (1) Add more elevators (linear improvement), (2) Smarter dispatch (30–40% better), (3) Dedicated express elevators (15–20% better), (4) Predictive positioning (5–10% better). Combined = 50–60% improvement.

**Q10: How to handle multiple simultaneous up/down requests?**
A: LOOK algorithm: complete UP sweep first, then DOWN sweep. Within each sweep, serve all requests in order. Prevents zigzagging. Wait time increases slightly for reverse-direction passengers but total throughput improves.

**Q11: What if network/communication fails (distributed system)?**
A: Fallback: each elevator runs local scheduler. Accept requests from local buttons only. Resume global coordination when network restored. Ensures safety even with comms failure.

**Q12: Can you support adaptive algorithms based on real-time data?**
A: Yes. Collect metrics: average wait, travel distance, capacity utilisation. Adjust dispatch strategy dynamically: if wait > 30s, switch from LOOK → optimal (more computation). If CPU high, reduce to FCFS (faster).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships and cardinality
- [ ] Walk through request → dispatch → pickup → dropoff lifecycle
- [ ] Explain the LOOK dispatch algorithm and direction-penalty cost function
- [ ] Explain how RLock prevents deadlock during recursive `move_to_next_floor()`
- [ ] Explain Singleton `__new__(*args, **kwargs)` fix and why it matters
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs (FCFS vs LOOK vs optimal, in-memory vs distributed)
- [ ] Mention thread safety in Singleton, add_request, and move_to_next_floor

---

**Ready for interview? Call the elevator! 🛗**
