# Elevator System - Reference Guide

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
