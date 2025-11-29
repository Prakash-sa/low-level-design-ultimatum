# Elevator System - Quick Start (5 Minutes)

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

## 5 Design Patterns (Why Each Matters)

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
