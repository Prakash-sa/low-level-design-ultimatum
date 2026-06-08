# Quick Reference - File Guide

This document provides a quick reference for understanding the elevator system code structure.

## File Structure & Purpose

### Core State Management
- **`Direction.py`** - Enums defining elevator states, directions, and door states
  - `Direction`: UP, DOWN, IDLE
  - `ElevatorState`: IDLE, MOVING_UP, MOVING_DOWN, DOOR_OPEN, MAINTENANCE, EMERGENCY
  - `DoorState`: CLOSED, OPEN, OPENING, CLOSING

### UI Components
- **`Button.py`** - Command pattern implementation for all button types
  - `Button` (abstract) → `HallButton`, `ElevatorButton`, `DoorOpenButton`, `DoorCloseButton`, `EmergencyButton`, `AlarmButton`
  - Each button encapsulates a command to be executed

- **`Door.py`** - Door state management with observer pattern
  - `Door`: Physical door with state transitions
  - `Observer`: Interface for components subscribing to door changes
  - `ObservedDoor`: Extended door with state change logging

- **`Display.py`** - Display rendering with observer pattern
  - `Display`: Shows current floor, direction, state, load percentage
  - `VerboseDisplay`: Extended display with logging
  - `MinimalDisplay`: Simplified display for hallways

### Request & Movement
- **`ElevatorRequest.py`** - Value object representing an elevator request
  - Immutable request with floor, direction, and priority
  - Hashable for deduplication and queue operations

- **`ElevatorCar.py`** - Main elevator car with complete state machine
  - Request queuing and processing
  - Movement simulation
  - Load management and overload detection
  - Observer pattern for state notifications
  - ~350 lines of well-documented code

### Control Panels
- **`ElevatorPanel.py`** - All panel types and floor management
  - `ElevatorPanel`: Interior car panel with floor buttons and emergency controls
  - `HallPanel`: Hallway panel with UP/DOWN buttons
  - `Floor`: Floor wrapper with hall panel reference
  - Button press callbacks and action registration

### Dispatcher Strategies
- **`Dispatcher.py`** - Strategy pattern for elevator assignment algorithms
  - `DispatcherStrategy` (abstract): Interface all strategies implement
  - `NearestIdleDispatcher`: Simple nearest-car approach
  - `DirectionAwareDispatcher`: Respects direction of travel
  - `LookAheadDispatcher`: Considers queue depth and direction
  - `ScanDispatcher`: SCAN algorithm (sweep up/down)

### Main System
- **`ElevatorSystem.py`** - Singleton pattern controller
  - `Building`: Building structure with floors and cars
  - `ElevatorSystem`: Main orchestrator (singleton)
    - Call handling and dispatching
    - Elevator control (maintenance, emergency)
    - System monitoring and statistics

- **`main.py`** - Comprehensive demo with 10 scenarios
  - All major use cases demonstrated
  - Different dispatcher strategies shown
  - Observer pattern in action
  - Load management and emergency handling

## SOLID Principles Applied

### Single Responsibility
- Each class has exactly one reason to change
- `ElevatorCar` manages car state only
- `Dispatcher` only assigns requests
- `Door` only manages door state

### Open/Closed
- Add new `DispatcherStrategy` without modifying `ElevatorSystem`
- Add new `Button` types without modifying button handling
- Add new `Observer` without changing `ElevatorCar`

### Liskov Substitution
- All `Button` subclasses work identically in code
- All `DispatcherStrategy` implementations substitute transparently
- All `Observer` implementations work with `ElevatorCar`

### Interface Segregation
- `Observer` interface has single method: `update()`
- `Button` interface: `execute()`, `is_pressed()`
- `DispatcherStrategy` interface: `dispatch()`
- Small, focused interfaces

### Dependency Inversion
- `ElevatorSystem` depends on `DispatcherStrategy` (abstract)
- `ElevatorCar` depends on `Observer` (interface)
- `Door` depends on `Observer` (interface)
- No direct dependencies on concrete classes

## Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Singleton** | `ElevatorSystem.get_instance()` | Single system instance |
| **Observer** | `ElevatorCar` + `Observer` | Loose coupling for updates |
| **Strategy** | `Dispatcher` + subclasses | Pluggable algorithms |
| **State** | `ElevatorState`, `DoorState` | Type-safe state management |
| **Command** | `Button` hierarchy | Encapsulate button actions |
| **Factory** | `Building` construction | Create system components |

## Key Classes & Methods

### ElevatorSystem
```python
# Singleton access
system = ElevatorSystem.get_instance(floors=10, cars=3)

# Main operations
car = system.call_elevator(floor=5, direction=Direction.UP)
system.set_dispatcher(DirectionAwareDispatcher())

# Monitoring
print(system.get_system_status())
```

### ElevatorCar
```python
# Check state
if car.get_state() == ElevatorState.IDLE:
    car.register_request(floor=7, direction=Direction.UP)

# Load management
if car.add_load(150):  # kg
    print("Passenger added")
else:
    print("Overloaded - request rejected")

# Observer pattern
car.subscribe(display)  # display gets updated on state change
```

### Dispatcher
```python
# Built-in strategies
NearestIdleDispatcher()      # Simple nearest
DirectionAwareDispatcher()   # Respects direction
LookAheadDispatcher()        # Considers queue
ScanDispatcher()             # SCAN algorithm
```

## Running the Demo

```bash
cd Interview/
python3 main.py
```

This runs all 10 scenarios demonstrating:
1. Basic calls and dispatching
2. Movement and stops
3. Interior floor selection
4. Maintenance mode
5. Emergency stop
6. Load management
7. Dispatcher strategy comparison
8. Observer pattern
9. Complete workflow
10. System statistics

## Extension Points

### Add New Dispatcher
```python
class MyDispatcher(DispatcherStrategy):
    def dispatch(self, floor, direction, cars):
        # Your algorithm here
        return best_car_index

system.set_dispatcher(MyDispatcher())
```

### Add New Observer
```python
class TelemetryMonitor(Observer):
    def update(self, door):
        # Log telemetry
        pass

door.subscribe(TelemetryMonitor())
```

### Add New Button Type
```python
class FloorIndicatorButton(Button):
    def execute(self):
        # Your logic
        pass
```

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|-----------------|-------|
| Call elevator | O(N) | N = number of cars |
| Add request | O(1) | Deque append |
| Move car | O(1) | Single floor movement |
| Get status | O(N) | N = number of cars |

## Testing Guide

```python
# Test singleton
s1 = ElevatorSystem.get_instance(10, 3)
s2 = ElevatorSystem.get_instance(10, 3)
assert s1 is s2  # Same instance

# Test dispatcher
car = system.call_elevator(5, Direction.UP)
assert car is not None

# Test observer
display = Display()
car.subscribe(display)
car.register_request(7)
assert display.get_floor() == car.get_current_floor()

# Test overload
assert car.add_load(900) == True
assert car.add_load(200) == False  # Overloaded
```

## Common Interview Questions & Answers

**Q: How would you handle concurrent requests?**
- Use thread-safe queue for requests
- Lock state during critical sections
- Add async/await support

**Q: How to prioritize requests?**
- Use priority queue instead of deque
- Prioritize floors in same direction
- Implement SCAN algorithm

**Q: How to handle elevator failure?**
- Auto-move to maintenance mode
- Reassign requests to other cars
- Alert monitoring system

**Q: How to optimize energy?**
- Predictive algorithms for calls
- Efficient request grouping
- Time-of-day optimization

## References

- SOLID Principles: https://www.baeldung.com/solid-principles
- Design Patterns: https://refactoring.guru/design-patterns
- UML Class Diagrams: https://en.wikipedia.org/wiki/Class_diagram
- Elevator Algorithms: https://en.wikipedia.org/wiki/Elevator_algorithm
