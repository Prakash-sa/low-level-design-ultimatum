# Elevator System - 75 Minute Interview Guide

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
