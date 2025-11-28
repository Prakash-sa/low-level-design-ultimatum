# Elevator System - Interview Question

## Problem Statement

Design an **Elevator Control System** for a multi-floor building that manages multiple elevator cars. The system should:
- Accept and process requests from different floors (up/down calls)
- Route elevator cars efficiently to serve requests
- Maintain elevator states (idle, moving, maintenance, overloaded)
- Handle door operations and passenger capacity
- Provide a simple interface for simulation and monitoring

---

## Functional Requirements (FR)

| # | Requirement | Description |
|---|---|---|
| FR1 | Call Elevator | Passengers can call an elevator from any floor with UP/DOWN direction |
| FR2 | Floor Selection | Passengers can select destination floor inside the elevator |
| FR3 | Movement | Elevator cars move between floors based on requests |
| FR4 | Door Control | Doors open/close automatically at each floor; manual controls available |
| FR5 | Display | Real-time display showing current floor, direction, and state |
| FR6 | Maintenance | System supports putting elevators into/out of maintenance mode |
| FR7 | Overload Detection | System detects and handles overloaded capacity |
| FR8 | Emergency Stop | Emergency button halts elevator and alerts system |
| FR9 | State Tracking | System tracks elevator state (moving up/down, idle, maintenance) |
| FR10 | Request Queue | System maintains queue of requests per elevator |

---

## Non-Functional Requirements (NFR)

| # | Requirement | Description |
|---|---|---|
| NFR1 | Scalability | System should support multiple floors (N) and elevator cars (M) |
| NFR2 | Extensibility | Easy to plug in different dispatcher algorithms |
| NFR3 | Maintainability | Clean code separation following SOLID principles |
| NFR4 | Testability | Components are independently testable |
| NFR5 | Performance | Efficient dispatcher algorithm (≤O(N*M)) per request |
| NFR6 | Reliability | No state corruption even with concurrent calls |
| NFR7 | Loose Coupling | Components depend on abstractions, not concrete classes |

---

## Design Patterns Used

### 1. **Singleton Pattern**
- **Class**: `ElevatorSystem`
- **Purpose**: Ensure only one instance of elevator system exists
- **Benefit**: Single point of access to the entire system

```python
system = ElevatorSystem.get_instance(floors=10, cars=3)
```

### 2. **Observer Pattern**
- **Classes**: `ElevatorCar` (Subject), `Display` & `Panel` (Observers)
- **Purpose**: Notify components when elevator state changes
- **Benefit**: Decoupled communication, easy to add new observers

```python
car.subscribe(display)  # Display gets notified of state changes
```

### 3. **Strategy Pattern**
- **Class**: `DispatcherStrategy` (abstract), `NearestIdleDispatcher`, `DirectionAwareDispatcher`
- **Purpose**: Support different elevator dispatch algorithms
- **Benefit**: Runtime algorithm switching without modifying `ElevatorSystem`

```python
system.set_dispatcher(DirectionAwareDispatcher())
```

### 4. **State Pattern**
- **Classes**: `ElevatorState`, `DoorState`
- **Purpose**: Encapsulate state-specific behavior
- **Benefit**: Clean handling of different states and transitions

```python
if car.get_state() == ElevatorState.MOVING_UP:
    car.move_up()
```

### 5. **Command Pattern**
- **Class**: `Button` (abstract), `HallButton`, `ElevatorButton`, `DoorButton`, `EmergencyButton`
- **Purpose**: Encapsulate requests as objects
- **Benefit**: Decouple button presses from execution, support undo/redo

```python
button.execute()  # Polymorphic execution
```

### 6. **Factory Pattern**
- **Class**: `ElevatorSystemFactory`
- **Purpose**: Centralized creation of complex objects
- **Benefit**: Consistent object creation and initialization

### 7. **Template Method Pattern**
- **Purpose**: Define skeleton of dispatching algorithm in base class
- **Benefit**: Subclasses override specific steps

---

## SOLID Principles Applied

### **S - Single Responsibility Principle**
Each class has ONE reason to change:
- `ElevatorCar` → manages car state and movement only
- `Dispatcher` → handles request assignment only
- `Door` → manages door state only
- `Display` → manages display only

### **O - Open/Closed Principle**
Classes are OPEN for extension, CLOSED for modification:
- Add new dispatcher strategies without modifying `ElevatorSystem`
- Add new button types without modifying button handling logic
- Add new observers without changing `ElevatorCar`

### **L - Liskov Substitution Principle**
Subtypes are substitutable for base types:
- All `Button` subclasses can replace `Button` in execute contexts
- All `DispatcherStrategy` implementations can replace each other
- All `Observer` implementations work with `ElevatorCar`

### **I - Interface Segregation Principle**
Many small interfaces instead of one large one:
- `Observer` interface (just `update()`)
- `Button` interface (just `execute()` and `is_pressed()`)
- `Dispatcher` interface (just `dispatch()`)
- `ElevatorRequest` interface (floor, direction)

### **D - Dependency Inversion Principle**
Depend on abstractions, not concrete implementations:
- `ElevatorSystem` depends on `DispatcherStrategy` (abstract)
- `ElevatorCar` depends on `Observer` (interface)
- `Door` depends on `DoorState` (enum, immutable)

---

## System Architecture

### Class Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ElevatorSystem (Singleton)               │
│                                                             │
│  - instance: ElevatorSystem                                │
│  - building: Building                                      │
│  - dispatcher: DispatcherStrategy                          │
│                                                             │
│  + get_instance(): ElevatorSystem                          │
│  + call_elevator(floor, direction): void                  │
│  + set_dispatcher(strategy): void                         │
│  + get_elevator_status(): dict                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ manages
                          ▼
        ┌──────────────────────────────────┐
        │         Building                 │
        │                                 │
        │ - floors: List[Floor]           │
        │ - elevator_cars: List[Car]      │
        │                                 │
        │ + get_floor(index): Floor       │
        │ + get_cars(): List[Car]         │
        └──────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    ┌──────────────────┐    ┌──────────────────────┐
    │      Floor       │    │   ElevatorCar       │
    │                 │    │                      │
    │ - number: int   │    │ - id: int            │
    │ - panels: []    │    │ - current_floor: int │
    │                 │    │ - state: State       │
    │ + call_up()     │    │ - request_queue: []  │
    │ + call_down()   │    │ - door: Door         │
    │                 │    │ - display: Display   │
    └──────────────────┘    │ - panel: Panel       │
                            │ - load: float       │
                            │ - capacity: float   │
                            │                      │
                            │ + register_request()│
                            │ + move()            │
                            │ + stop()            │
                            │ + enter_maintenance()
                            │ + add_observer()    │
                            └──────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌────────────┐   ┌────────────┐   ┌──────────┐
            │    Door    │   │  Display   │   │  Panel   │
            │            │   │            │   │          │
            │ - state    │   │ - floor    │   │ - buttons│
            │            │   │ - direction│   │          │
            │ + open()   │   │ - state    │   │ + press()│
            │ + close()  │   │            │   │          │
            │ + update() │   │ + update() │   │ + reset()│
            └────────────┘   └────────────┘   └──────────┘
```

### Sequence: Passenger Calls Elevator

```
Passenger           HallPanel          ElevatorSystem      ElevatorCar        Door        Display
   │                   │                    │                  │                │            │
   │  Press UP         │                    │                  │                │            │
   ├──────────────────>│                    │                  │                │            │
   │                   │  registerCall      │                  │                │            │
   │                   │  (floor=5, UP)     │                  │                │            │
   │                   ├───────────────────>│                  │                │            │
   │                   │                    │ Dispatch         │                │            │
   │                   │                    │ Algorithm        │                │            │
   │                   │                    ├────────────┐     │                │            │
   │                   │                    │<───────────┘     │                │            │
   │                   │                    │                  │                │            │
   │                   │                    │ assignRequest(5) │                │            │
   │                   │                    ├─────────────────>│                │            │
   │                   │                    │                  │                │            │
   │                   │                    │                  │ enqueue(5)     │            │
   │                   │                    │                  │ + start_moving │            │
   │                   │                    │                  ├─────────────────┐           │
   │                   │                    │                  │ update observers│           │
   │                   │                    │                  ├─────────────────┴──────────>│
   │                   │                    │                  │                │  update()  │
   │                   │                    │                  │                │           │
   │                   │                    │                  │ [moving...]     │   show    │
   │                   │                    │                  │                │  current  │
   │                   │                    │                  │                │   floor   │
   │                   │                    │                  │ [at floor 5]    │           │
   │                   │                    │                  ├────────────────>│  open()   │
   │                   │                    │                  │                │   door    │
   │                   │                    │                  │                │<──opened──┤
   │                   │                    │                  │                            │
   │  Doors Open       │                    │                  │                            │
   │<─────────────────────────────────────────────────────────────────────────────────────│
   │                   │                    │                  │                │            │
```

### Dispatcher Algorithm (Strategy Pattern)

```
┌─────────────────────────────────────────┐
│   DispatcherStrategy (Abstract)         │
│                                        │
│  + dispatch(request, cars): Car        │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
         │         ┌──────────┴──────────┐
         │         │                     │
    ┌────┴────┐ ┌──┴──────────────┐ ┌──┴──────────────┐
    │ Nearest │ │ Direction-Aware │ │ Collective      │
    │ Idle    │ │ Dispatcher      │ │ Dispatcher      │
    │         │ │                 │ │                 │
    │ Select  │ │ Finds car going │ │ Complex algo    │
    │ closest │ │ in same dir     │ │ with look-ahead │
    │ idle    │ │ nearest floor   │ │                 │
    │ car     │ └─────────────────┘ └─────────────────┘
    └─────────┘
```

---

## State Machines

### Elevator State Transitions

```
                    ┌──────────────┐
                    │              │
                    ▼              │
    ┌──────────────────────────┐   │
    │   IDLE                   │───┘ (no requests)
    │                          │
    └──────────┬───────────────┘
               │
        (request received)
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    ┌────────┐   ┌─────────┐
    │MOVING_UP    │MOVING_DN│
    └────┬───┘   └─────┬───┘
         │ (reached target)
         └──────┬───────┘
                │
         ┌──────▼────────┐
         │  DOOR_OPEN    │
         │  (load/unload)│
         └──────┬────────┘
                │
         ┌──────▼──────────────┐
         │                     │
    (has next request)    (no requests)
         │                     │
         ▼                     ▼
    ┌─────────────┐    ┌──────────────┐
    │ MOVING_UP   │    │    IDLE      │
    │ or DOWN     │    │              │
    └─────────────┘    └──────────────┘
         │
         └─────▼──────────────────┐
                                  │
    (maintenance requested)       │
         │                        │
         ▼                        │
    ┌──────────────────────┐      │
    │  MAINTENANCE        │      │
    │  (offline)          │      │
    │                     │◄─────┘ (exit maintenance)
    │                     │
    └──────────────────────┘
```

### Door State Transitions

```
    ┌──────────────┐
    │              │
    ▼              │
┌────────┐    ┌─────────┐
│ CLOSED │───>│  OPEN   │
└────────┘◄───└─────────┘
    ▲           (open timer expires)
    │           or (close button pressed)
    │
    └───────────────┘
```

---

## Key Design Decisions

### 1. **Observer Pattern for State Changes**
- `ElevatorCar` notifies `Display`, `Door`, and `Panel` of state changes
- No circular dependencies; loose coupling maintained
- Easy to add new observers (e.g., monitoring system, analytics)

### 2. **Strategy Pattern for Dispatching**
- Different dispatch algorithms without modifying `ElevatorSystem`
- `NearestIdleDispatcher` - simple approach for interviews
- `DirectionAwareDispatcher` - respects elevator direction preference

### 3. **Separate Concerns: Button vs Button Executor**
- `Button` classes represent UI elements
- `ButtonExecutor` or command handlers execute actions
- Decouple UI events from business logic

### 4. **Immutable State Enums**
- `ElevatorState`, `DoorState`, `Direction` as enums
- No invalid state transitions possible
- Type-safe state representation

### 5. **Capacity Management**
- `current_load` and `max_capacity` tracked per car
- `is_overloaded()` check before accepting requests
- Prevents capacity violations

---

## Implementation Structure

```
Interview/
├── README.md (this file)
├── Direction.py           (enums: Direction, ElevatorState, DoorState)
├── Button.py              (abstract Button, concrete button types)
├── Door.py                (Door class with state management)
├── Display.py             (Display class, observer pattern)
├── ElevatorCar.py         (main car logic, observer subject)
├── ElevatorPanel.py       (elevator panel, hall panel)
├── Dispatcher.py          (abstract strategy, concrete implementations)
├── ElevatorRequest.py     (request data structure)
├── ElevatorSystem.py      (singleton, main orchestrator)
├── Building.py            (building and floor management)
└── main.py                (demo scenarios)
```

---

## How to Run

```bash
cd Interview/
python3 main.py
```

**Expected Output:**
```
=== Elevator System Demo ===
Building created with 10 floors and 3 elevator cars.

--- Scenario 1: Passenger Calls Elevator ---
Floor 3: Passenger pressed UP
ElevatorCar 0 assigned to floor 3
ElevatorCar 0 at floor 3, opening door
[Display] Car 0: Floor 3, Direction: UP, State: IDLE

--- Scenario 2: Inside Elevator Selection ---
ElevatorCar 0: Passenger selected floor 7
ElevatorCar 0 moving...
[Display] Car 0: Floor 5, Direction: UP, State: MOVING_UP
[Display] Car 0: Floor 7, Direction: UP, State: MOVING_UP
ElevatorCar 0 at floor 7, opening door
```

---

## Testing Strategy

```python
# Test 1: Singleton pattern
system1 = ElevatorSystem.get_instance(10, 3)
system2 = ElevatorSystem.get_instance(10, 3)
assert system1 is system2  # Same instance

# Test 2: Dispatcher assigns nearest idle car
system = ElevatorSystem.get_instance(10, 3)
car = system.call_elevator(floor=5, direction=Direction.UP)
assert car.get_id() in [0, 1, 2]

# Test 3: Observer notifications
car = system.get_cars()[0]
display = Display()
car.subscribe(display)
car.register_request(floor=5)
# Display should be updated with new state

# Test 4: Overload detection
car = system.get_cars()[0]
car.add_load(100)  # car capacity = 1000
assert not car.is_overloaded()
car.add_load(950)
assert car.is_overloaded()

# Test 5: Maintenance mode
car = system.get_cars()[0]
car.enter_maintenance()
assert car.is_in_maintenance()
car.exit_maintenance()
assert not car.is_in_maintenance()
```

---

## Extension Points

### Add New Dispatcher Algorithm
```python
class PredictiveDispatcher(DispatcherStrategy):
    def dispatch(self, request, cars):
        # Implement ML-based prediction
        pass

system.set_dispatcher(PredictiveDispatcher())
```

### Add New Observer
```python
class TelemetryMonitor(Observer):
    def update(self, car):
        # Log elevator analytics
        pass

car.subscribe(TelemetryMonitor())
```

### Add New Button Type
```python
class FloorDirectiveButton(Button):
    def execute(self):
        # Special button behavior
        pass
```

---

## Common Interview Questions & Answers

**Q1: How would you handle concurrent requests?**
- Use a thread-safe queue for requests
- Lock state during critical sections
- Consider async/await patterns for scalability

**Q2: How to prioritize requests?**
- Use priority queue instead of regular queue
- Prioritize floors in elevator direction
- Add SCAN algorithm (elevator sweeps up then down)

**Q3: What if an elevator gets stuck?**
- Implement health check mechanism
- Auto-move to maintenance mode
- Reassign requests to other elevators

**Q4: How to handle emergency situations?**
- Emergency button stops car immediately
- Alert system monitoring
- Return to nearest safe floor

**Q5: How to optimize energy consumption?**
- Use predictive algorithms
- Group requests efficiently
- Consider time-of-day patterns

---

## References

- **Patterns**: Singleton, Observer, Strategy, State, Command, Factory
- **Principles**: SOLID (S, O, L, I, D)
- **Architecture**: Observer pattern for loose coupling
- **Python Features**: Abstract base classes, enums, deque for efficiency
