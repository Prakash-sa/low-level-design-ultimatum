# Elevator System — 75-Minute Interview Guide

## Quick Start Overview

## What You're Building
Multi-elevator dispatching system for high-rise buildings with intelligent request assignment, state machine management, and concurrent operation.

---

## 75-Minute Timeline

| Time | Phase | Focus |
|------|-------|-------|
| 0-5 min | **Requirements** | Clarify floors, elevators, dispatch strategy, safety constraints |
| 5-15 min | **Architecture** | Design 5 core entities, choose 5 patterns (Singleton, Strategy, State, Observer, Command) |
| 15-35 min | **Entities** | Implement ElevatorCar, Door, Display with state machine |
| 35-55 min | **Logic** | Implement dispatcher strategies, queue management |
| 55-70 min | **Integration** | Wire ElevatorSystem, add observers, demo 5 scenarios |
| 70-75 min | **Demo** | Walk through code, explain patterns, answer questions |

---

## Core Entities (3-Sentence Each)

### 1. Door
Controls elevator door with states (OPEN/CLOSED/OPENING/CLOSING). Safety checks prevent opening while moving. Simple API: open(), close(), is_open(), is_closed().

### 2. Display
Shows current floor and direction with visual arrows (↑/↓/•). Updated by elevator during movement. Simple state: floor + direction.

### 3. ElevatorCar (State Machine)
Manages movement, request queues, and state transitions. Has separate up_queue (ascending) and down_queue (descending). State machine: IDLE → MOVING → DOOR_OPEN → IDLE.

### 4. DispatcherStrategy
Selects optimal elevator for incoming requests. Three implementations: Nearest (fastest), LoadBalanced (fair), ZoneBased (tall buildings). Strategy pattern allows runtime switching.

### 5. ElevatorSystem (Singleton)
Coordinates all elevators, routes requests, manages observers. Single instance ensures consistent state. Thread-safe operations with locks.

---

## 5 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Why Each Matters)

### 1. Singleton - ElevatorSystem
**What**: Single instance coordinates all elevators  
**Why**: Centralized control, consistent dispatcher state, prevents conflicts  
**Talk Point**: "Ensures all requests see same elevator availability. Alternative: Dependency injection for testing."

### 2. Strategy - Dispatcher Algorithms
**What**: NearestCarDispatcher, LoadBalancedDispatcher, ZoneBasedDispatcher  
**Why**: Different optimization goals (speed vs fairness vs zones)  
**Talk Point**: "Can switch from Nearest to LoadBalanced during peak hours without code changes. Easy to add PriorityDispatcher."

### 3. State - Elevator State Machine
**What**: IDLE, MOVING_UP, MOVING_DOWN, DOOR_OPEN, MAINTENANCE  
**Why**: Prevents invalid operations (can't open door while moving)  
**Talk Point**: "State machine enforces safety. Can't transition MOVING → DOOR_OPEN directly. Must stop first."

### 4. Observer - System Monitor
**What**: SystemMonitor observes elevator events  
**Why**: Decoupled logging, extensible monitoring (add SMS alerts)  
**Talk Point**: "Adding email alerts just requires new EmailObserver. No changes to ElevatorSystem."

### 5. Command - Button Press
**What**: Button press encapsulates request  
**Why**: Abstract request handling, enable undo/logging  
**Talk Point**: "HallButton and CarButton both execute() request. Easy to add logging or undo functionality."

---

## Key Algorithms (30-Second Explanations)

### Nearest Dispatcher
```python
# Select closest available elevator
available = [e for e in elevators if e.is_available()]
selected = min(available, key=lambda e: abs(e.current_floor - floor))
```
**Why**: Minimizes wait time, greedy approach, simple logic.

### Queue Management
```python
# Separate queues for efficiency
up_queue = [3, 5, 7, 9]      # Serve ascending
down_queue = [8, 6, 4, 2]    # Serve descending
# Elevator serves current direction first, then switches
```
**Why**: Reduces unnecessary direction changes, passengers expect this behavior.

### State Transition Validation
```python
# Only allow door open when stopped
if state == IDLE:
    state = DOOR_OPEN
    door.open()
else:
    raise ValueError("Cannot open door while moving")
```
**Why**: Safety constraint prevents accidents, enforces business rules.

---

## Interview Talking Points

### Opening (0-5 min)
- "I'll design a multi-elevator system with intelligent dispatching"
- "Core challenge: minimize wait time, handle concurrency, ensure safety"
- "Will use Singleton for coordination, Strategy for dispatchers, State for safety"

### During Implementation (15-55 min)
- "Separate up/down queues allow efficient bidirectional travel"
- "State machine prevents opening doors while moving (safety)"
- "Thread locks protect queue operations from race conditions"
- "Nearest dispatcher is greedy but simple; LoadBalanced is fairer"

### Closing Demo (70-75 min)
- "Demo 1: Basic operation - single request dispatched to nearest elevator"
- "Demo 2: Concurrent requests - multiple elevators serve independently"
- "Demo 3: Internal destination - passenger adds floor to elevator queue"
- "Demo 4: Load balancing - requests distributed evenly across elevators"
- "Demo 5: Zone-based - tall building with elevators assigned by zones"

---

## Success Checklist

- [ ] Draw system architecture with 5 entities
- [ ] Explain Singleton justification (centralized control)
- [ ] Show 3 dispatcher strategies side-by-side
- [ ] Demonstrate state machine with valid/invalid transitions
- [ ] Describe queue management (up/down separate)
- [ ] Discuss thread safety with lock mechanism
- [ ] Describe observer pattern for monitoring
- [ ] Propose 2 optimizations (zones, heaps, caching)
- [ ] Answer express elevator question (skip floors, destination dispatch)
- [ ] Run working code with 5 demos

---

## Anti-Patterns to Avoid

**DON'T**:
- Hard-code dispatcher logic in ElevatorSystem (violates Strategy)
- Create multiple ElevatorSystem instances (violates Singleton)
- Allow door to open while state is MOVING (safety violation)
- Mix external/internal requests in same queue (confusing logic)
- Skip concurrency discussion ("I'll handle it later")

**DO**:
- Make dispatchers pluggable with abstract base class
- Use thread locks for critical sections (dispatch, queue modify)
- Validate state transitions in ElevatorCar methods
- Explain trade-offs (Nearest vs LoadBalanced vs ZoneBased)
- Propose optimizations (R-tree indexing, heap queues, zone partitioning)

---

## 3 Advanced Follow-Ups (Be Ready)

### 1. Express Elevators
"Add express_floors set to ElevatorCar. Skip floors 2-10 in move_to_floor(). Dispatcher assigns express elevators for requests >10. Destination dispatch: passengers input floor before boarding, system groups by destination."

### 2. Emergency Handling
"Add EMERGENCY state. Set emergency flag to stop run() loop. Clear all queues. Move to ground floor. Transition to MAINTENANCE. Notify all observers for alert. Require manual reset by admin."

### 3. Destination Dispatch Optimization
"Passengers input floor at lobby kiosk. System assigns elevator and display 'Car E3'. Group passengers going to same floor range (e.g., 10-15). Reduces stops, improves throughput. Used in modern smart buildings."

---

## Run Commands

```bash
# Execute all 5 demos
python3 INTERVIEW_COMPACT.py

# Check syntax
python3 -m py_compile INTERVIEW_COMPACT.py

# View guide
cat 75_MINUTE_GUIDE.md
```

---

## The 60-Second Pitch

"I designed an elevator system with 5 core entities: ElevatorCar, Door, Display, DispatcherStrategy, ElevatorSystem. Uses Singleton for centralized control, Strategy pattern for dispatchers (Nearest/LoadBalanced/ZoneBased), State machine for safety (prevents door opening while moving), and Observer for monitoring. Request queues are split into up/down for efficiency. Handles concurrency with thread locks. Demo shows nearest dispatch, load balancing, zone-based assignment for tall buildings. Scales with R-tree indexing and zone partitioning."

---

## What Interviewers Look For

1. **Safety**: Do you prevent doors opening while moving?
2. **Efficiency**: How do you minimize wait time?
3. **Scalability**: Can your design handle 100 elevators?
4. **Patterns**: Do you recognize when to apply Singleton/Strategy/State?
5. **Trade-offs**: Can you compare Nearest vs LoadBalanced dispatchers?
6. **Concurrency**: How do you handle simultaneous requests?
7. **Extensibility**: How easy to add new dispatcher?

---

## Final Tips

- **Draw first, code later**: Spend 10 minutes on architecture diagram
- **State assumptions clearly**: "Assuming 10 floors, 3 elevators"
- **Test edge cases**: All elevators busy, maintenance mode, floor out of range
- **Explain as you code**: "Adding lock here to prevent race condition"
- **Time management**: Leave 5 minutes for demo, don't over-engineer

**Queue Management is Key**: Interviewers often focus on how you handle up/down queues. Be ready to explain sorting, direction switching, and why separate queues are better than single queue.

**Good luck!** Run the code, understand the patterns, and explain trade-offs confidently.


## 75-Minute Guide

## System Overview
**Multi-elevator dispatching system** for high-rise buildings, featuring intelligent request assignment, concurrent car management, door operations, and load monitoring. Think modern smart building elevators.

**Core Challenge**: Efficient dispatching to minimize average wait time, handle concurrent requests, manage elevator states, and ensure safety constraints.

---

## Requirements Clarification (0-5 min)

### Functional Requirements
1. **Multiple Elevators**: 3+ elevator cars serving N floors (default 10)
2. **Call Management**: External calls (floor + direction) and internal calls (destination floor)
3. **Dispatching**: Assign nearest available elevator to external requests
4. **Movement**: Elevators move floor-by-floor with direction tracking
5. **Door Operations**: Open/close at destination floors with safety timeout
6. **Load Monitoring**: Track current floor, direction, pending requests
7. **Display**: Show current floor and direction for each elevator
8. **State Management**: IDLE, MOVING_UP, MOVING_DOWN, DOOR_OPEN, MAINTENANCE

### Non-Functional Requirements
- **Performance**: Dispatch decision in <100ms for 10 elevators
- **Scale**: Support 50 floors, 20 elevators, 100 concurrent requests
- **Safety**: Never open doors while moving, prevent overloading
- **Availability**: System continues if one elevator in maintenance

### Key Design Decisions
1. **Request Queues**: Separate up_queue and down_queue per elevator
2. **Dispatching**: Strategy pattern (Nearest, LoadBalanced, ZoneBased)
3. **State Machine**: Elevator state transitions with validation
4. **Concurrency**: Thread-safe operations with locks
5. **Coordination**: Singleton ElevatorSystem manages all cars

---

## Architecture & Design (5-15 min)

### System Architecture

```
ElevatorSystem (Singleton)
├── Elevators List
│   └── ElevatorCar → Door → Display → Queues
├── Floors List
│   └── Floor → HallButtons (UP/DOWN)
├── Dispatcher (Strategy)
│   ├── NearestCarDispatcher
│   ├── LoadBalancedDispatcher
│   └── ZoneBasedDispatcher
└── Observers
    └── SystemMonitor
```

### Design Patterns Used

1. **Singleton**: ElevatorSystem (one instance coordinates all elevators)
2. **Strategy**: Dispatcher algorithms (Nearest/LoadBalanced/ZoneBased)
3. **State**: Elevator state machine (IDLE/MOVING/DOOR_OPEN/MAINTENANCE)
4. **Observer**: System monitor for events
5. **Command**: Button press actions encapsulated

---

## Core Entities (15-35 min)

### 1. Direction & State Enums

```python
from enum import Enum

class Direction(Enum):
    UP = "up"
    DOWN = "down"
    IDLE = "idle"

class ElevatorState(Enum):
    IDLE = "idle"
    MOVING_UP = "moving_up"
    MOVING_DOWN = "moving_down"
    DOOR_OPEN = "door_open"
    MAINTENANCE = "maintenance"

class DoorState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
```

**Key Points**:
- Direction tracks movement intent
- State enforces valid operations (can't move with door open)
- Door has intermediate states for animations

### 2. Door Class

```python
import time

class Door:
    """Elevator door with safety operations"""
    def __init__(self, elevator_id: str):
        self.elevator_id = elevator_id
        self.state = DoorState.CLOSED
    
    def open(self):
        """Open door (safety: only when stopped)"""
        if self.state == DoorState.CLOSED:
            self.state = DoorState.OPENING
            time.sleep(0.1)  # Simulate opening
            self.state = DoorState.OPEN
            return True
        return False
    
    def close(self):
        """Close door"""
        if self.state == DoorState.OPEN:
            self.state = DoorState.CLOSING
            time.sleep(0.1)  # Simulate closing
            self.state = DoorState.CLOSED
            return True
        return False
    
    def is_open(self) -> bool:
        return self.state == DoorState.OPEN
    
    def is_closed(self) -> bool:
        return self.state == DoorState.CLOSED
```

**Key Points**:
- Safety checks prevent invalid operations
- Intermediate states for realistic simulation
- Simple API (open/close/is_open/is_closed)

### 3. Display Class

```python
class Display:
    """Elevator display showing floor and direction"""
    def __init__(self, elevator_id: str):
        self.elevator_id = elevator_id
        self.current_floor = 0
        self.direction = Direction.IDLE
    
    def update(self, floor: int, direction: Direction):
        """Update display with current status"""
        self.current_floor = floor
        self.direction = direction
    
    def show(self) -> str:
        """Return display string"""
        arrow = "↑" if self.direction == Direction.UP else "↓" if self.direction == Direction.DOWN else "•"
        return "Floor %d %s" % (self.current_floor, arrow)
```

**Key Points**:
- Simple state tracking (floor + direction)
- Visual representation with arrows
- Updated by elevator during movement

### 4. ElevatorCar Class (State Machine)

```python
import threading
from collections import deque

class ElevatorCar:
    """Elevator car with state machine and request queues"""
    def __init__(self, elevator_id: str, total_floors: int):
        self.elevator_id = elevator_id
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE
        self.total_floors = total_floors
        
        # Components
        self.door = Door(elevator_id)
        self.display = Display(elevator_id)
        
        # Request queues (sorted)
        self.up_queue = []
        self.down_queue = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Metrics
        self.total_trips = 0
        self.total_floors_traveled = 0
    
    def add_request(self, floor: int, direction: Direction):
        """Add floor to appropriate queue"""
        with self.lock:
            if direction == Direction.UP:
                if floor not in self.up_queue:
                    self.up_queue.append(floor)
                    self.up_queue.sort()
            elif direction == Direction.DOWN:
                if floor not in self.down_queue:
                    self.down_queue.append(floor)
                    self.down_queue.sort(reverse=True)
    
    def add_destination(self, floor: int):
        """Add internal destination (from inside elevator)"""
        with self.lock:
            if floor > self.current_floor:
                if floor not in self.up_queue:
                    self.up_queue.append(floor)
                    self.up_queue.sort()
            elif floor < self.current_floor:
                if floor not in self.down_queue:
                    self.down_queue.append(floor)
                    self.down_queue.sort(reverse=True)
    
    def has_requests(self) -> bool:
        """Check if elevator has pending requests"""
        return len(self.up_queue) > 0 or len(self.down_queue) > 0
    
    def get_next_floor(self) -> int:
        """Get next floor to visit based on direction"""
        with self.lock:
            if self.direction == Direction.UP and self.up_queue:
                return self.up_queue[0]
            elif self.direction == Direction.DOWN and self.down_queue:
                return self.down_queue[0]
            elif self.up_queue:
                self.direction = Direction.UP
                return self.up_queue[0]
            elif self.down_queue:
                self.direction = Direction.DOWN
                return self.down_queue[0]
            else:
                self.direction = Direction.IDLE
                return self.current_floor
    
    def move_to_floor(self, target_floor: int):
        """Move elevator to target floor"""
        if target_floor == self.current_floor:
            return
        
        # Determine direction
        if target_floor > self.current_floor:
            self.direction = Direction.UP
            self.state = ElevatorState.MOVING_UP
        else:
            self.direction = Direction.DOWN
            self.state = ElevatorState.MOVING_DOWN
        
        # Move floor by floor
        while self.current_floor != target_floor:
            if self.direction == Direction.UP:
                self.current_floor += 1
            else:
                self.current_floor -= 1
            
            self.total_floors_traveled += 1
            self.display.update(self.current_floor, self.direction)
            time.sleep(0.1)  # Simulate travel time
        
        # Arrived at floor
        self.state = ElevatorState.IDLE
    
    def open_door_at_floor(self):
        """Open door and remove floor from queue"""
        self.state = ElevatorState.DOOR_OPEN
        self.door.open()
        
        # Remove current floor from queues
        with self.lock:
            if self.current_floor in self.up_queue:
                self.up_queue.remove(self.current_floor)
            if self.current_floor in self.down_queue:
                self.down_queue.remove(self.current_floor)
        
        time.sleep(0.2)  # Door open duration
        self.door.close()
        self.state = ElevatorState.IDLE
        self.total_trips += 1
    
    def run(self):
        """Main elevator run loop"""
        while True:
            if self.state == ElevatorState.MAINTENANCE:
                time.sleep(1)
                continue
            
            if not self.has_requests():
                self.state = ElevatorState.IDLE
                self.direction = Direction.IDLE
                self.display.update(self.current_floor, self.direction)
                time.sleep(0.5)
                continue
            
            next_floor = self.get_next_floor()
            self.move_to_floor(next_floor)
            self.open_door_at_floor()
    
    def get_distance_to_floor(self, floor: int) -> int:
        """Calculate distance to floor"""
        return abs(self.current_floor - floor)
    
    def is_available(self) -> bool:
        """Check if elevator is available for dispatch"""
        return (self.state != ElevatorState.MAINTENANCE and 
                self.state != ElevatorState.DOOR_OPEN)
```

**Key Points**:
- Separate queues for up/down requests (sorted for efficiency)
- Thread-safe operations with lock
- State machine prevents invalid transitions
- Metrics tracking for monitoring
- Distance calculation for dispatching

---

## Business Logic (35-55 min)

### Dispatcher Strategy Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class DispatcherStrategy(ABC):
    """Abstract dispatcher strategy"""
    @abstractmethod
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        pass

class NearestCarDispatcher(DispatcherStrategy):
    """Dispatch nearest available elevator"""
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Return nearest elevator
        return min(available, key=lambda e: e.get_distance_to_floor(floor))

class LoadBalancedDispatcher(DispatcherStrategy):
    """Dispatch elevator with fewest pending requests"""
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Return elevator with shortest queue
        return min(available, 
                  key=lambda e: len(e.up_queue) + len(e.down_queue))

class ZoneBasedDispatcher(DispatcherStrategy):
    """Dispatch based on floor zones (low/mid/high)"""
    def __init__(self, total_floors: int, zones: int = 3):
        self.total_floors = total_floors
        self.zone_size = total_floors // zones
    
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Find elevators in same zone
        target_zone = floor // self.zone_size
        same_zone = [e for e in available 
                    if e.current_floor // self.zone_size == target_zone]
        
        if same_zone:
            return min(same_zone, key=lambda e: e.get_distance_to_floor(floor))
        
        # Fallback to nearest
        return min(available, key=lambda e: e.get_distance_to_floor(floor))
```

**Interview Points**:
- Nearest minimizes wait time (greedy approach)
- LoadBalanced prevents overloading single elevator
- ZoneBased optimizes for tall buildings (reduces cross-traffic)

---

## Integration & Patterns (55-70 min)

### Observer Pattern - System Monitor

```python
class ElevatorObserver(ABC):
    """Observer interface for elevator events"""
    @abstractmethod
    def update(self, event: str, elevator: ElevatorCar, data: dict):
        pass

class SystemMonitor(ElevatorObserver):
    """Monitor and log elevator events"""
    def update(self, event: str, elevator: ElevatorCar, data: dict):
        if event == "request_assigned":
            print("[MONITOR] Elevator %s assigned to floor %d" % 
                  (elevator.elevator_id, data['floor']))
        elif event == "floor_reached":
            print("[MONITOR] Elevator %s reached floor %d" % 
                  (elevator.elevator_id, data['floor']))
        elif event == "door_opened":
            print("[MONITOR] Elevator %s door opened at floor %d" % 
                  (elevator.elevator_id, data['floor']))
```

### Singleton - ElevatorSystem

```python
class ElevatorSystem:
    """Singleton controller for elevator system"""
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
            self.elevators = []
            self.floors = []
            self.dispatcher = NearestCarDispatcher()
            self.observers = []
            self.lock = threading.Lock()
            self.initialized = True
    
    def add_elevator(self, elevator: ElevatorCar):
        """Add elevator to system"""
        self.elevators.append(elevator)
    
    def set_dispatcher(self, dispatcher: DispatcherStrategy):
        """Change dispatcher strategy at runtime"""
        self.dispatcher = dispatcher
    
    def add_observer(self, observer: ElevatorObserver):
        """Add observer"""
        self.observers.append(observer)
    
    def request_elevator(self, floor: int, direction: Direction) -> bool:
        """External call - request elevator at floor"""
        with self.lock:
            selected = self.dispatcher.select_elevator(self.elevators, floor, direction)
            
            if not selected:
                print("[SYSTEM] No elevator available for floor %d" % floor)
                return False
            
            selected.add_request(floor, direction)
            self._notify_observers("request_assigned", selected, {'floor': floor})
            
            print("[SYSTEM] Assigned Elevator %s to floor %d %s" % 
                  (selected.elevator_id, floor, direction.value))
            return True
    
    def press_button_inside(self, elevator_id: str, destination_floor: int):
        """Internal call - passenger selects destination"""
        elevator = next((e for e in self.elevators if e.elevator_id == elevator_id), None)
        if elevator:
            elevator.add_destination(destination_floor)
            print("[SYSTEM] Elevator %s: Destination %d added" % 
                  (elevator_id, destination_floor))
    
    def get_system_status(self) -> dict:
        """Get current system status"""
        status = {
            'total_elevators': len(self.elevators),
            'available': len([e for e in self.elevators if e.is_available()]),
            'in_maintenance': len([e for e in self.elevators 
                                  if e.state == ElevatorState.MAINTENANCE]),
            'elevators': []
        }
        
        for e in self.elevators:
            status['elevators'].append({
                'id': e.elevator_id,
                'floor': e.current_floor,
                'state': e.state.value,
                'direction': e.direction.value,
                'pending': len(e.up_queue) + len(e.down_queue)
            })
        
        return status
    
    def _notify_observers(self, event: str, elevator: ElevatorCar, data: dict):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, elevator, data)
```

---

## Interview Q&A (12 Questions)

### Basic (0-5 min)

1. **"What are the core entities in an elevator system?"**
   - Answer: ElevatorCar, Door, Display, Floor, Button, ElevatorSystem (coordinator), Dispatcher (strategy).

2. **"What are the elevator states?"**
   - Answer: IDLE (stopped, no requests), MOVING_UP/DOWN (in transit), DOOR_OPEN (loading passengers), MAINTENANCE (out of service).

3. **"How do you handle external vs internal requests?"**
   - Answer: External (floor + direction) → dispatcher selects elevator. Internal (destination only) → added to current elevator's queue.

### Intermediate (5-10 min)

4. **"Explain the dispatching algorithm."**
   - Answer: Strategy pattern. Nearest finds closest available elevator. LoadBalanced picks elevator with fewest requests. ZoneBased assigns by floor zones.

5. **"How do you prevent doors from opening while moving?"**
   - Answer: State machine. Door.open() only succeeds when state is IDLE or DOOR_OPEN. Moving states block door operations.

6. **"How are request queues managed?"**
   - Answer: Separate up_queue (sorted ascending) and down_queue (sorted descending). Elevator serves requests in current direction first, then switches.

7. **"How do you handle concurrent requests?"**
   - Answer: System-level lock protects dispatcher. Elevator-level locks protect queue operations. Thread-safe state transitions.

### Advanced (10-15 min)

8. **"How would you optimize for tall buildings (50+ floors)?"**
   - Answer: ZoneBased dispatcher partitions floors. Express elevators for top floors. Local elevators for lower floors. Sky lobbies for transfers.

9. **"How would you implement load balancing?"**
   - Answer: Track queue length per elevator. Dispatcher selects elevator with min(pending_requests). Alternative: weight by distance + queue length.

10. **"How to detect and handle stuck elevators?"**
    - Answer: Heartbeat monitoring (elevator reports position every 5s). Timeout detection (no movement for 30s). Auto-transition to MAINTENANCE. Redistribute pending requests.

11. **"How would you add priority for VIP floors?"**
    - Answer: Add priority_queue separate from up/down queues. Process priority requests first. Alternative: Add weight to dispatcher distance calculation.

12. **"How to scale to 100 elevators?"**
    - Answer: Partition elevators by building section. Separate ElevatorSystem per zone. Use message queue (Kafka) for cross-zone requests. Cache dispatcher decisions. Database for state persistence.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **Single Responsibility** | ElevatorCar handles movement; Door handles operations; Dispatcher handles selection |
| **Open/Closed** | New dispatcher strategies without modifying ElevatorSystem |
| **Liskov Substitution** | All DispatcherStrategy subclasses interchangeable at runtime |
| **Interface Segregation** | Observer only requires update(); Strategy only requires select_elevator() |
| **Dependency Inversion** | ElevatorSystem depends on abstract DispatcherStrategy, not concrete classes |

---

## UML Diagram

```
┌────────────────────────────────────────────────────┐
│         ElevatorSystem (Singleton)                 │
├────────────────────────────────────────────────────┤
│ - elevators: List[ElevatorCar]                     │
│ - dispatcher: DispatcherStrategy                   │
│ - observers: List[ElevatorObserver]                │
├────────────────────────────────────────────────────┤
│ + request_elevator(floor, direction)               │
│ + press_button_inside(elevator_id, floor)          │
│ + get_system_status()                              │
└────────────────────────────────────────────────────┘
           │              │
           ▼              ▼
    ┌──────────────┐  ┌──────────────┐
    │ ElevatorCar  │  │ Dispatcher   │
    ├──────────────┤  │ (Strategy)   │
    │ current_floor│  ├──────────────┤
    │ direction    │  │ Nearest      │
    │ state        │  │ LoadBalanced │
    │ up_queue     │  │ ZoneBased    │
    │ down_queue   │  └──────────────┘
    ├──────────────┤
    │ + add_request()    │
    │ + move_to_floor()  │
    │ + run()            │
    └──────────────┘
         │     │
         ▼     ▼
    ┌────┐  ┌─────────┐
    │Door│  │Display  │
    └────┘  └─────────┘

State Machine:
IDLE ──request──> MOVING_UP/DOWN ──arrive──> DOOR_OPEN ──timeout──> IDLE
  │                                                                     │
  └────────────────────> MAINTENANCE <────────────────────────────────┘

┌────────────────────────────────────┐
│   DispatcherStrategy (Abstract)    │
├────────────────────────────────────┤
│ + select_elevator(elevators, floor)│
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────┬──────────────┐
    │                 │              │
NearestCar      LoadBalanced    ZoneBased
```

---

## 5 Demo Scenarios

### Demo 1: Basic Operation
- Initialize 3 elevators at floor 0
- Request elevator at floor 5 (UP)
- System dispatches nearest elevator
- Elevator moves to floor 5, opens door

### Demo 2: Concurrent Requests
- Request floor 3 (UP) and floor 7 (DOWN) simultaneously
- System dispatches 2 different elevators
- Both elevators serve requests independently
- Display status of all elevators

### Demo 3: Internal Destination
- Passenger in Elevator-1 presses button for floor 8
- Elevator adds floor 8 to up_queue
- Elevator serves external floor 5, then internal floor 8
- Verify queue management

### Demo 4: Load Balancing
- Switch to LoadBalancedDispatcher
- Create 10 requests across different floors
- Verify requests distributed evenly
- Compare with NearestCarDispatcher

### Demo 5: Zone-Based Dispatching
- Switch to ZoneBasedDispatcher (3 zones)
- Request floor 2 (low), floor 15 (mid), floor 28 (high)
- Verify elevators assigned to their zones first
- Fallback to nearest if zone empty

---

## Key Implementation Notes

### Request Queue Management
- Use sorted lists (not heaps) for transparency
- up_queue sorted ascending (serve lowest first going up)
- down_queue sorted descending (serve highest first going down)
- Remove duplicates on insertion

### Concurrency Handling
- System-level lock for dispatcher
- Elevator-level lock for queue operations
- Use threading.Thread for elevator run loops
- Daemon threads for background operation

### Performance Optimization
- Cache elevator distances
- Index elevators by zone
- Lazy evaluation of next floor
- Batch request processing

### Testing Strategy
1. Unit test each dispatcher strategy
2. Unit test elevator state transitions
3. Integration test multi-elevator coordination
4. Concurrency test (100 simultaneous requests)
5. Edge cases: all elevators busy, maintenance mode, invalid floors


## Detailed Design Reference

## System Overview
Multi-elevator dispatching system for high-rise buildings. Features intelligent request assignment, state machine management, and multiple dispatching strategies.

---

## Core Entities

| Entity | Attributes | Responsibilities |
|--------|-----------|------------------|
| **ElevatorCar** | elevator_id, current_floor, direction, state, up_queue, down_queue | Move between floors, manage request queues, track state |
| **Door** | state (OPEN/CLOSED/OPENING/CLOSING) | Control door operations with safety checks |
| **Display** | current_floor, direction | Show elevator status visually |
| **ElevatorSystem** | elevators, dispatcher, observers | Coordinate all elevators, dispatch requests |
| **DispatcherStrategy** | Algorithm-specific logic | Select optimal elevator for requests |

---

## Design Patterns Implementation

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | ElevatorSystem - single coordinator | Centralized control, consistent state |
| **Strategy** | Dispatcher algorithms (Nearest/LoadBalanced/ZoneBased) | Runtime algorithm switching, extensible |
| **State** | Elevator state machine (IDLE/MOVING/DOOR_OPEN/MAINTENANCE) | Enforces valid transitions, prevents errors |
| **Observer** | SystemMonitor for event tracking | Decoupled logging, extensible monitoring |
| **Command** | Button press actions encapsulated | Request abstraction, undo support |

---

## Dispatcher Strategies Comparison

| Strategy | Selection Logic | Pros | Cons | Use Case |
|----------|----------------|------|------|----------|
| **NearestCar** | Minimum distance to floor | Fast response, simple | Can overload one elevator | Low-traffic buildings |
| **LoadBalanced** | Minimum pending requests | Even distribution | May not be nearest | High-traffic buildings |
| **ZoneBased** | Floor zones (low/mid/high) | Reduces cross-traffic | Complex setup | Tall buildings (50+ floors) |

**Selection Formula (NearestCar)**:
```
selected = min(available_elevators, key=lambda e: abs(e.current_floor - requested_floor))
```

**Selection Formula (LoadBalanced)**:
```
selected = min(available_elevators, key=lambda e: len(e.up_queue) + len(e.down_queue))
```

**Selection Formula (ZoneBased)**:
```
target_zone = requested_floor // zone_size
same_zone = [e for e in available if e.current_floor // zone_size == target_zone]
selected = min(same_zone or available, key=distance)
```

---

## Elevator State Machine

```
IDLE → MOVING_UP → DOOR_OPEN → IDLE
IDLE → MOVING_DOWN → DOOR_OPEN → IDLE
Any State → MAINTENANCE (emergency)
```

**Valid Transitions**:
- IDLE → MOVING_UP/DOWN: Request received
- MOVING_UP/DOWN → IDLE: Reached floor (no door open)
- IDLE → DOOR_OPEN: At destination floor
- DOOR_OPEN → IDLE: Door closed
- Any → MAINTENANCE: Emergency stop

**Invalid Transitions** (prevented by state checks):
- MOVING → DOOR_OPEN (safety violation)
- DOOR_OPEN → MOVING (must close first)
- MAINTENANCE → MOVING (must return to IDLE)

---

## Request Queue Management

### Queue Structure
```python
up_queue = [3, 5, 7, 9]      # Sorted ascending
down_queue = [8, 6, 4, 2]    # Sorted descending
```

### Queue Operations

| Operation | Logic | Time Complexity |
|-----------|-------|-----------------|
| **Add Request** | Insert if not exists, then sort | O(n log n) |
| **Get Next Floor** | Return queue[0] based on direction | O(1) |
| **Remove Floor** | Remove current_floor from both queues | O(n) |
| **Check Empty** | len(up_queue) + len(down_queue) == 0 | O(1) |

### Direction Switching Logic
```
If moving UP:
  - Serve all up_queue floors first
  - When empty, switch to DOWN, serve down_queue
If moving DOWN:
  - Serve all down_queue floors first
  - When empty, switch to UP, serve up_queue
If IDLE:
  - Pick non-empty queue (prefer up_queue)
```

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | ElevatorCar: movement; Door: operations; Dispatcher: selection |
| **Open/Closed** | New dispatchers via DispatcherStrategy without modifying system |
| **Liskov Substitution** | All DispatcherStrategy subclasses interchangeable |
| **Interface Segregation** | Observer requires only update(); Strategy only select_elevator() |
| **Dependency Inversion** | ElevatorSystem depends on abstract DispatcherStrategy |

---

## System Architecture Diagram

```
┌───────────────────────────────────┐
│   ElevatorSystem (Singleton)      │
├───────────────────────────────────┤
│ - elevators: List<ElevatorCar>    │
│ - dispatcher: DispatcherStrategy  │
│ - observers: List<Observer>       │
├───────────────────────────────────┤
│ + request_elevator()              │
│ + press_button_inside()           │
│ + get_system_status()             │
└───────────────────────────────────┘
         │              │
         ▼              ▼
   ┌──────────┐   ┌──────────────┐
   │Elevator  │   │  Dispatcher  │
   │   Car    │   │  (Strategy)  │
   ├──────────┤   ├──────────────┤
   │floor     │   │Nearest       │
   │direction │   │LoadBalanced  │
   │state     │   │ZoneBased     │
   │up_queue  │   └──────────────┘
   │down_queue│
   ├──────────┤
   │+ run()   │
   └──────────┘
      │    │
      ▼    ▼
   ┌────┐ ┌────────┐
   │Door│ │Display │
   └────┘ └────────┘
```

---

## Concurrency & Thread Safety

**Challenges**:
- Multiple requests arriving simultaneously
- Elevator state changes during dispatch
- Queue modifications from different threads

**Solutions**:
```python
# System-level lock for dispatch
with self.lock:
    elevator = dispatcher.select_elevator(...)
    elevator.add_request(floor, direction)

# Elevator-level lock for queue ops
with self.lock:
    self.up_queue.append(floor)
    self.up_queue.sort()
```

**Thread Model**:
- Each elevator runs in separate daemon thread
- Main thread handles user input/dispatch
- Locks protect critical sections (dispatch, queue modification)

---

## Performance Considerations

### Bottlenecks
1. **Dispatcher Selection**: O(n) scan of all elevators
2. **Queue Sorting**: O(n log n) on every insertion
3. **Lock Contention**: Single system lock blocks concurrent requests

### Optimizations
1. **Spatial Indexing**: Use R-tree for floor-based elevator lookup
2. **Heap Queues**: Replace sorted lists with heaps (O(log n) insert)
3. **Read-Write Locks**: Allow concurrent reads, exclusive writes
4. **Cache Dispatcher**: Memoize distance calculations for 1 second
5. **Partition Zones**: Separate systems for building sections

---

## Interview Success Checklist

- [ ] Explain 5 core entities (ElevatorCar, Door, Display, System, Dispatcher)
- [ ] Draw state machine with valid/invalid transitions
- [ ] Describe 3 dispatcher strategies with trade-offs
- [ ] Explain up/down queue management with sorting
- [ ] Discuss thread safety with lock mechanism
- [ ] Implement door safety (no open while moving)
- [ ] Describe observer pattern for monitoring
- [ ] Justify Singleton for ElevatorSystem
- [ ] Propose 2+ optimizations (zones, heaps, caching)
- [ ] Answer follow-up on express elevators or priority

---

## Quick Commands

```bash
# Run all demos
python3 INTERVIEW_COMPACT.py

# Check syntax
python3 -m py_compile INTERVIEW_COMPACT.py

# View guide
cat 75_MINUTE_GUIDE.md
```

---

## Common Interview Follow-Ups

**Q: How would you implement express elevators (skip floors 2-10)?**
A: Add skip_floors set to ElevatorCar. Modify move_to_floor() to skip intermediate floors. Dispatcher assigns express elevators for high floors (>10).

**Q: How to handle emergency stop?**
A: Add EMERGENCY state. Override run() loop with emergency flag. Clear all queues. Return to ground floor. Notify observers for alert.

**Q: How to optimize for office buildings (morning rush to top floors)?**
A: Use TimeBasedDispatcher. Between 8-10am, pre-position elevators at lobby. Group passengers going to same floor ranges. Implement destination dispatch (passengers input floor before boarding).

**Q: How to prevent overloading (weight limit)?**
A: Add weight_sensor to ElevatorCar. Track current_weight vs max_weight. Reject add_destination() if over limit. Display "OVERWEIGHT" warning. Require passenger exit before door closes.

**Q: How to scale to 100 elevators across 5 buildings?**
A: Partition by building_id. Separate ElevatorSystem per building. Use message queue (Kafka) for cross-building analytics. Database for persistent state. Load balancer with health checks.


## Compact Code

```python
#!/usr/bin/env python3
"""
Elevator System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
import threading
import time


# ===== ENUMS =====

class Direction(Enum):
    UP = "up"
    DOWN = "down"
    IDLE = "idle"


class ElevatorState(Enum):
    IDLE = "idle"
    MOVING_UP = "moving_up"
    MOVING_DOWN = "moving_down"
    DOOR_OPEN = "door_open"
    MAINTENANCE = "maintenance"


class DoorState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"


# ===== DOOR =====

class Door:
    """Elevator door with safety operations"""
    def __init__(self, elevator_id: str):
        self.elevator_id = elevator_id
        self.state = DoorState.CLOSED
    
    def open(self):
        """Open door (safety: only when stopped)"""
        if self.state == DoorState.CLOSED:
            self.state = DoorState.OPENING
            time.sleep(0.05)  # Simulate opening
            self.state = DoorState.OPEN
            return True
        return False
    
    def close(self):
        """Close door"""
        if self.state == DoorState.OPEN:
            self.state = DoorState.CLOSING
            time.sleep(0.05)  # Simulate closing
            self.state = DoorState.CLOSED
            return True
        return False
    
    def is_open(self) -> bool:
        return self.state == DoorState.OPEN
    
    def is_closed(self) -> bool:
        return self.state == DoorState.CLOSED


# ===== DISPLAY =====

class Display:
    """Elevator display showing floor and direction"""
    def __init__(self, elevator_id: str):
        self.elevator_id = elevator_id
        self.current_floor = 0
        self.direction = Direction.IDLE
    
    def update(self, floor: int, direction: Direction):
        """Update display with current status"""
        self.current_floor = floor
        self.direction = direction
    
    def show(self) -> str:
        """Return display string"""
        if self.direction == Direction.UP:
            arrow = "↑"
        elif self.direction == Direction.DOWN:
            arrow = "↓"
        else:
            arrow = "•"
        return "Floor %2d %s" % (self.current_floor, arrow)


# ===== ELEVATOR CAR (STATE MACHINE) =====

class ElevatorCar:
    """Elevator car with state machine and request queues"""
    def __init__(self, elevator_id: str, total_floors: int):
        self.elevator_id = elevator_id
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE
        self.total_floors = total_floors
        
        # Components
        self.door = Door(elevator_id)
        self.display = Display(elevator_id)
        
        # Request queues (sorted)
        self.up_queue = []
        self.down_queue = []
        
        # Thread safety
        self.lock = threading.Lock()
        self.running = True
        
        # Metrics
        self.total_trips = 0
        self.total_floors_traveled = 0
    
    def add_request(self, floor: int, direction: Direction):
        """Add floor to appropriate queue"""
        with self.lock:
            if direction == Direction.UP:
                if floor not in self.up_queue:
                    self.up_queue.append(floor)
                    self.up_queue.sort()
            elif direction == Direction.DOWN:
                if floor not in self.down_queue:
                    self.down_queue.append(floor)
                    self.down_queue.sort(reverse=True)
    
    def add_destination(self, floor: int):
        """Add internal destination (from inside elevator)"""
        with self.lock:
            if floor > self.current_floor:
                if floor not in self.up_queue:
                    self.up_queue.append(floor)
                    self.up_queue.sort()
            elif floor < self.current_floor:
                if floor not in self.down_queue:
                    self.down_queue.append(floor)
                    self.down_queue.sort(reverse=True)
    
    def has_requests(self) -> bool:
        """Check if elevator has pending requests"""
        return len(self.up_queue) > 0 or len(self.down_queue) > 0
    
    def get_next_floor(self) -> int:
        """Get next floor to visit based on direction"""
        with self.lock:
            if self.direction == Direction.UP and self.up_queue:
                return self.up_queue[0]
            elif self.direction == Direction.DOWN and self.down_queue:
                return self.down_queue[0]
            elif self.up_queue:
                self.direction = Direction.UP
                return self.up_queue[0]
            elif self.down_queue:
                self.direction = Direction.DOWN
                return self.down_queue[0]
            else:
                self.direction = Direction.IDLE
                return self.current_floor
    
    def move_to_floor(self, target_floor: int):
        """Move elevator to target floor"""
        if target_floor == self.current_floor:
            return
        
        # Determine direction
        if target_floor > self.current_floor:
            self.direction = Direction.UP
            self.state = ElevatorState.MOVING_UP
        else:
            self.direction = Direction.DOWN
            self.state = ElevatorState.MOVING_DOWN
        
        # Move floor by floor
        while self.current_floor != target_floor:
            if self.direction == Direction.UP:
                self.current_floor += 1
            else:
                self.current_floor -= 1
            
            self.total_floors_traveled += 1
            self.display.update(self.current_floor, self.direction)
            time.sleep(0.05)  # Simulate travel time
        
        # Arrived at floor
        self.state = ElevatorState.IDLE
    
    def open_door_at_floor(self):
        """Open door and remove floor from queue"""
        self.state = ElevatorState.DOOR_OPEN
        self.door.open()
        
        # Remove current floor from queues
        with self.lock:
            if self.current_floor in self.up_queue:
                self.up_queue.remove(self.current_floor)
            if self.current_floor in self.down_queue:
                self.down_queue.remove(self.current_floor)
        
        time.sleep(0.1)  # Door open duration
        self.door.close()
        self.state = ElevatorState.IDLE
        self.total_trips += 1
    
    def run(self):
        """Main elevator run loop"""
        while self.running:
            if self.state == ElevatorState.MAINTENANCE:
                time.sleep(0.5)
                continue
            
            if not self.has_requests():
                self.state = ElevatorState.IDLE
                self.direction = Direction.IDLE
                self.display.update(self.current_floor, self.direction)
                time.sleep(0.2)
                continue
            
            next_floor = self.get_next_floor()
            self.move_to_floor(next_floor)
            self.open_door_at_floor()
    
    def stop(self):
        """Stop the elevator thread"""
        self.running = False
    
    def get_distance_to_floor(self, floor: int) -> int:
        """Calculate distance to floor"""
        return abs(self.current_floor - floor)
    
    def is_available(self) -> bool:
        """Check if elevator is available for dispatch"""
        return (self.state != ElevatorState.MAINTENANCE and 
                self.state != ElevatorState.DOOR_OPEN)
    
    def __str__(self):
        return "%s: %s [%s] (Up:%s Down:%s)" % (
            self.elevator_id, 
            self.display.show(),
            self.state.value,
            self.up_queue,
            self.down_queue
        )


# ===== DISPATCHER STRATEGY =====

class DispatcherStrategy(ABC):
    """Abstract dispatcher strategy"""
    @abstractmethod
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        pass


class NearestCarDispatcher(DispatcherStrategy):
    """Dispatch nearest available elevator"""
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Return nearest elevator
        return min(available, key=lambda e: e.get_distance_to_floor(floor))


class LoadBalancedDispatcher(DispatcherStrategy):
    """Dispatch elevator with fewest pending requests"""
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Return elevator with shortest queue
        return min(available, 
                  key=lambda e: len(e.up_queue) + len(e.down_queue))


class ZoneBasedDispatcher(DispatcherStrategy):
    """Dispatch based on floor zones (low/mid/high)"""
    def __init__(self, total_floors: int, zones: int = 3):
        self.total_floors = total_floors
        self.zone_size = max(1, total_floors // zones)
    
    def select_elevator(self, elevators: List[ElevatorCar], 
                       floor: int, direction: Direction) -> Optional[ElevatorCar]:
        available = [e for e in elevators if e.is_available()]
        if not available:
            return None
        
        # Find elevators in same zone
        target_zone = floor // self.zone_size
        same_zone = [e for e in available 
                    if e.current_floor // self.zone_size == target_zone]
        
        if same_zone:
            return min(same_zone, key=lambda e: e.get_distance_to_floor(floor))
        
        # Fallback to nearest
        return min(available, key=lambda e: e.get_distance_to_floor(floor))


# ===== OBSERVER PATTERN =====

class ElevatorObserver(ABC):
    """Observer interface for elevator events"""
    @abstractmethod
    def update(self, event: str, elevator: ElevatorCar, data: dict):
        pass


class SystemMonitor(ElevatorObserver):
    """Monitor and log elevator events"""
    def update(self, event: str, elevator: ElevatorCar, data: dict):
        if event == "request_assigned":
            print("  [MONITOR] Elevator %s assigned to floor %d" % 
                  (elevator.elevator_id, data['floor']))
        elif event == "floor_reached":
            print("  [MONITOR] Elevator %s reached floor %d" % 
                  (elevator.elevator_id, data['floor']))


# ===== SINGLETON - ELEVATOR SYSTEM =====

class ElevatorSystem:
    """Singleton controller for elevator system"""
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
            self.elevators = []
            self.dispatcher = NearestCarDispatcher()
            self.observers = []
            self.lock = threading.Lock()
            self.threads = []
            self.initialized = True
    
    def add_elevator(self, elevator: ElevatorCar):
        """Add elevator to system"""
        self.elevators.append(elevator)
        # Start elevator thread
        thread = threading.Thread(target=elevator.run, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def set_dispatcher(self, dispatcher: DispatcherStrategy):
        """Change dispatcher strategy at runtime"""
        self.dispatcher = dispatcher
    
    def add_observer(self, observer: ElevatorObserver):
        """Add observer"""
        self.observers.append(observer)
    
    def request_elevator(self, floor: int, direction: Direction) -> bool:
        """External call - request elevator at floor"""
        with self.lock:
            selected = self.dispatcher.select_elevator(self.elevators, floor, direction)
            
            if not selected:
                print("  [SYSTEM] No elevator available for floor %d" % floor)
                return False
            
            selected.add_request(floor, direction)
            self._notify_observers("request_assigned", selected, {'floor': floor})
            
            print("  [SYSTEM] Assigned %s to floor %d %s (distance: %d)" % 
                  (selected.elevator_id, floor, direction.value, 
                   selected.get_distance_to_floor(floor)))
            return True
    
    def press_button_inside(self, elevator_id: str, destination_floor: int):
        """Internal call - passenger selects destination"""
        elevator = next((e for e in self.elevators if e.elevator_id == elevator_id), None)
        if elevator:
            elevator.add_destination(destination_floor)
            print("  [SYSTEM] %s: Internal button %d pressed" % 
                  (elevator_id, destination_floor))
    
    def get_system_status(self) -> dict:
        """Get current system status"""
        status = {
            'total_elevators': len(self.elevators),
            'available': len([e for e in self.elevators if e.is_available()]),
            'in_maintenance': len([e for e in self.elevators 
                                  if e.state == ElevatorState.MAINTENANCE]),
            'elevators': []
        }
        
        for e in self.elevators:
            status['elevators'].append({
                'id': e.elevator_id,
                'floor': e.current_floor,
                'state': e.state.value,
                'direction': e.direction.value,
                'pending': len(e.up_queue) + len(e.down_queue)
            })
        
        return status
    
    def _notify_observers(self, event: str, elevator: ElevatorCar, data: dict):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, elevator, data)
    
    def print_status(self):
        """Print current status of all elevators"""
        for elevator in self.elevators:
            print("    %s" % elevator)


# ===== DEMO SCENARIOS =====

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def demo1_basic_operation():
    """Demo 1: Basic Operation"""
    print_section("DEMO 1: Basic Operation")
    
    system = ElevatorSystem()
    
    # Add monitor
    system.add_observer(SystemMonitor())
    
    # Add 3 elevators
    for i in range(3):
        elevator = ElevatorCar("E%d" % (i+1), total_floors=10)
        system.add_elevator(elevator)
    
    print("\n1. Initial status (all elevators at floor 0):")
    system.print_status()
    
    print("\n2. Requesting elevator at floor 5 (UP):")
    system.request_elevator(5, Direction.UP)
    
    time.sleep(1)  # Wait for elevator to arrive
    
    print("\n3. Status after request:")
    system.print_status()


def demo2_concurrent_requests():
    """Demo 2: Concurrent Requests"""
    print_section("DEMO 2: Concurrent Requests")
    
    system = ElevatorSystem()
    
    print("\n1. Creating multiple concurrent requests:")
    system.request_elevator(3, Direction.UP)
    system.request_elevator(7, Direction.DOWN)
    system.request_elevator(2, Direction.UP)
    
    time.sleep(1.5)
    
    print("\n2. Status after concurrent requests:")
    system.print_status()


def demo3_internal_destination():
    """Demo 3: Internal Destination"""
    print_section("DEMO 3: Internal Destination")
    
    system = ElevatorSystem()
    
    print("\n1. Request elevator at floor 5:")
    system.request_elevator(5, Direction.UP)
    
    time.sleep(0.5)
    
    print("\n2. Passenger inside E1 presses button for floor 8:")
    system.press_button_inside("E1", 8)
    
    time.sleep(1)
    
    print("\n3. Final status:")
    system.print_status()


def demo4_load_balancing():
    """Demo 4: Load Balancing"""
    print_section("DEMO 4: Load Balancing")
    
    system = ElevatorSystem()
    
    print("\n1. Switching to LoadBalancedDispatcher:")
    system.set_dispatcher(LoadBalancedDispatcher())
    
    print("\n2. Creating 6 requests (should distribute evenly):")
    for floor in [2, 4, 6, 3, 7, 9]:
        direction = Direction.UP if floor < 8 else Direction.DOWN
        system.request_elevator(floor, direction)
        time.sleep(0.1)
    
    time.sleep(1)
    
    print("\n3. Status (requests distributed across elevators):")
    system.print_status()
    
    # Show queue distribution
    print("\n4. Queue distribution:")
    for e in system.elevators:
        total = len(e.up_queue) + len(e.down_queue)
        print("    %s: %d pending requests" % (e.elevator_id, total))


def demo5_zone_based():
    """Demo 5: Zone-Based Dispatching"""
    print_section("DEMO 5: Zone-Based Dispatching (30 floors, 3 zones)")
    
    # Reset system with taller building
    ElevatorSystem._instance = None
    system = ElevatorSystem()
    
    # Add 3 elevators for 30-floor building
    for i in range(3):
        elevator = ElevatorCar("E%d" % (i+1), total_floors=30)
        # Position elevators in different zones
        elevator.current_floor = i * 10  # E1:0, E2:10, E3:20
        system.add_elevator(elevator)
    
    print("\n1. Initial positions (elevators in different zones):")
    system.print_status()
    
    print("\n2. Switching to ZoneBasedDispatcher:")
    system.set_dispatcher(ZoneBasedDispatcher(total_floors=30, zones=3))
    
    print("\n3. Requesting floors from different zones:")
    print("   Zone 1 (0-9): Floor 5")
    system.request_elevator(5, Direction.UP)
    time.sleep(0.2)
    
    print("   Zone 2 (10-19): Floor 15")
    system.request_elevator(15, Direction.UP)
    time.sleep(0.2)
    
    print("   Zone 3 (20-29): Floor 25")
    system.request_elevator(25, Direction.UP)
    
    time.sleep(1)
    
    print("\n4. Final status (each zone served by nearest elevator):")
    system.print_status()


# ===== MAIN =====

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ELEVATOR SYSTEM - COMPLETE DEMONSTRATION")
    print("="*70)
    
    demo1_basic_operation()
    time.sleep(0.5)
    
    demo2_concurrent_requests()
    time.sleep(0.5)
    
    demo3_internal_destination()
    time.sleep(0.5)
    
    demo4_load_balancing()
    time.sleep(0.5)
    
    demo5_zone_based()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Patterns Demonstrated:")
    print("1. Singleton: ElevatorSystem (one instance coordinates all)")
    print("2. Strategy: 3 Dispatcher algorithms (Nearest/LoadBalanced/ZoneBased)")
    print("3. State: Elevator state machine (IDLE/MOVING/DOOR_OPEN/MAINTENANCE)")
    print("4. Observer: SystemMonitor for event tracking")
    print("5. Queue Management: Separate up/down queues per elevator")
    print("\nRun 'python3 INTERVIEW_COMPACT.py' to see all demos")

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
