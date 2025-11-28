# 75-Minute Interview - Quick Start Guide

## 🎯 Your Interview Kit

You have **TWO resources** for the 75-minute elevator system interview:

### Resource 1: 75_MINUTE_GUIDE.md
- **What it is**: Step-by-step implementation plan with code snippets
- **When to use**: Read this FIRST to understand what to build
- **Time**: 10 minutes to read and understand
- **Contains**: 
  - Exact time breakdown (0-5 min problem, 5-15 min design, 15-60 min code, 60-75 min demo)
  - Code for each phase with explanations
  - Interview talking points
  - Extension points for follow-up questions

### Resource 2: INTERVIEW_COMPACT.py
- **What it is**: Complete runnable implementation in ONE file (440 lines)
- **When to use**: Reference during coding, run to verify your implementation
- **Features**: 5 working demo scenarios
- **Can be**: Copy-pasted directly into interview if needed (but better to code yourself!)

---

## ⏱️ 75-Minute Timeline

### **Minutes 0-5: Problem Clarification**
Ask interviewer:
- How many floors? (assume 10)
- How many elevators? (assume 3) 
- Main algorithm? (nearest car)
- Need emergency? (yes)
- Load management? (for demo)

### **Minutes 5-15: Design Discussion (10 min)**
Draw on whiteboard:
```
Building → Floors → Elevators → Requests
   ↓
ElevatorSystem (Singleton)
   ├─ Building (num_floors, num_cars)
   ├─ ElevatorCar[] (state machine)
   └─ Dispatcher (strategy pattern)

ElevatorCar
   ├─ State: IDLE, MOVING_UP, MOVING_DOWN, DOOR_OPEN, MAINTENANCE
   ├─ request_queue (deque)
   ├─ Door (state machine)
   └─ Observers (Display)
```

**Design Patterns to mention:**
- ✅ Singleton - ElevatorSystem
- ✅ Observer - Display updates
- ✅ Strategy - Dispatcher algorithm
- ✅ State - ElevatorState enum
- ✅ Command - Button classes

### **Minutes 15-60: Implementation (45 min)**

Start coding THESE 6 sections in order:

#### **Phase 1 (5 min): Enums**
```python
class Direction(Enum): UP, DOWN, IDLE
class ElevatorState(Enum): IDLE, MOVING_UP, MOVING_DOWN, DOOR_OPEN, MAINTENANCE
class DoorState(Enum): OPEN, CLOSED
```

#### **Phase 2 (10 min): ElevatorCar class**
- Constructor: car_id, current_floor, state, request_queue
- `register_request(floor)` - add to queue
- `move_one_floor()` - simulation
- `_check_arrival()` - detect when at target floor
- `depart_floor()` - move to next request
- `enter_maintenance()` / `exit_maintenance()`
- `get_status()` - return dict

#### **Phase 3 (10 min): ElevatorSystem class**
- Singleton pattern: `get_instance()`
- Constructor: create N cars
- `call_elevator(floor, direction)` - main API
- `_find_best_car()` - dispatcher (strategy)
- `move_all_cars()` - simulation
- `print_status()` - debug output

#### **Phase 4 (8 min): Buttons & Observers**
- `Button` (abstract) + `HallButton`, `ElevatorButton`
- `Observer` (interface) + `Display` (implementation)
- Add `subscribe()` to ElevatorCar

#### **Phase 5 (7 min): Control methods**
- `depart_floor(car_id)`
- `put_in_maintenance(car_id)`
- `release_from_maintenance(car_id)`

#### **Phase 6 (5 min): Demo code**
```python
system = ElevatorSystem.get_instance(10, 3)
car = system.call_elevator(floor=5, direction=Direction.UP)
system.print_status()
```

### **Minutes 60-75: Testing & Walk-through (15 min)**

Run these 5 demo scenarios:

1. **Basic Call** (2 min)
   - Call from floor 3
   - Verify assigned to nearest car

2. **Movement** (2 min)
   - Call from floor 5
   - Move car 3 steps
   - Show state transitions

3. **Multiple Calls** (2 min)
   - 3 simultaneous calls
   - Show dispatch to different cars

4. **Maintenance** (2 min)
   - Put car in maintenance
   - Verify new calls go to other cars
   - Release and verify

5. **Interior Selection** (2 min)
   - Call from floor 2
   - Select floor 7 inside car
   - Show queue has 2 requests

**Talk through (5 min):**
- Design patterns used (5)
- SOLID principles (5)
- Time complexity (dispatch O(N))
- How to extend (new dispatcher, priority queue)

---

## 💻 How to Code It

### Option A: From Scratch (Recommended for interview)
1. Use 75_MINUTE_GUIDE.md as reference
2. Type the code yourself
3. Test as you go
4. Show working demos

### Option B: Use INTERVIEW_COMPACT.py
1. Reference it to see structure
2. Type it out piece by piece
3. Run it to verify
4. Show understanding of each part

### Option C: Copy-Paste (Last resort)
1. Use INTERVIEW_COMPACT.py
2. Copy into interview environment
3. Run demos
4. Explain each section
5. Handle follow-up questions

---

## 🎓 Key Talking Points

### When asked "What patterns does this use?"
- **Singleton**: ElevatorSystem.get_instance() ensures single instance
- **Observer**: Display subscribes to car state changes (loose coupling)
- **Strategy**: Dispatcher algorithm can be swapped (_find_best_car)
- **State**: ElevatorState enum ensures type-safe states
- **Command**: Button classes encapsulate actions

### When asked "How would you extend this?"
- **New dispatcher**: Create new class, implement _find_best_car logic
- **Priority floors**: Add priority to (floor, direction) tuple
- **Concurrent requests**: Use thread-safe queue
- **Load management**: Add load tracking to ElevatorCar
- **Monitoring**: Add more observers (logging, analytics)

### When asked "What's the complexity?"
- **Dispatch**: O(N) where N = number of cars
- **Movement**: O(1) per floor
- **Memory**: O(N*M) for N cars with M pending requests
- **Scalable**: Works for 100 floors, 50 cars

### When asked "How would you test?"
```python
# Test 1: Singleton
assert ElevatorSystem.get_instance() is ElevatorSystem.get_instance()

# Test 2: Dispatch
car = system.call_elevator(5, Direction.UP)
assert car is not None

# Test 3: Movement
car.register_request(5)
for _ in range(5):
    car.move_one_floor()
assert car.current_floor == 5

# Test 4: Maintenance
car.enter_maintenance()
assert car.maintenance == True
assert car.request_queue.empty()
```

---

## 📝 Quick Checklist

- [ ] **Problem understood** - Ask clarifying questions (2 min)
- [ ] **Design sketched** - Draw architecture on whiteboard (8 min)
- [ ] **Enums created** - Direction, ElevatorState, DoorState (5 min)
- [ ] **ElevatorCar done** - State machine working (10 min)
- [ ] **ElevatorSystem done** - Singleton + dispatcher (10 min)
- [ ] **Buttons/Display** - Observer pattern (8 min)
- [ ] **Control methods** - Maintenance, queries (7 min)
- [ ] **Demo running** - 5 scenarios pass (10 min)
- [ ] **Explained patterns** - All 5 mentioned (3 min)
- [ ] **Answered follow-ups** - Extensions, complexity, testing (5 min)

---

## 🚀 During the Interview

### Start
"I'll build an elevator system with:
- State machine for each car
- Singleton for the system
- Observer pattern for displays
- Strategy for dispatch
- SOLID principles throughout"

### Build in order
"Let me start with enums for type safety..."
"Now the main ElevatorCar state machine..."
"Then the orchestrator ElevatorSystem as singleton..."
"Add observer pattern for displays..."
"Finally, test scenarios..."

### Show working code
"Let me run a quick test..."
"See how car gets dispatched?"
"Door opens/closes automatically..."
"Maintenance mode works..."

### Handle "Tell me more"
"The patterns we used:
- Singleton ensures single instance
- Observer decouples display from car
- Strategy lets us swap dispatch algorithm
- State enums prevent invalid transitions
- SOLID keeps each class focused"

### Handle "How would you..."
"Great question! For [extension], I would...
- Add a new class for that
- Keep the main logic unchanged
- That's the Open/Closed principle"

---

## 📞 Emergency Options

### If you get stuck on coding
- Switch to explaining what you would write
- Draw pseudocode
- Reference INTERVIEW_COMPACT.py
- Talk about design patterns

### If you run out of time
- Summarize what's been built
- Explain what's next
- Answer any follow-up questions
- Show you understand the architecture

### If there are bugs
- Debug together with interviewer
- Show your debugging process
- Fix incrementally
- Verify with test cases

---

## ✅ Final Verification

Before you start the interview, verify the setup:

```bash
# Test INTERVIEW_COMPACT.py works
python3 INTERVIEW_COMPACT.py

# Check 75_MINUTE_GUIDE.md is readable
cat 75_MINUTE_GUIDE.md | head -50

# Verify you can create files in IDE
# (create a test.py file)
```

---

## 💡 Pro Tips

1. **Code incrementally** - Test after each phase
2. **Use typing** - Add type hints as you code
3. **Name clearly** - Use descriptive variable names
4. **Comment code** - Explain complex logic
5. **Ask questions** - Show engagement with interviewer
6. **Discuss trade-offs** - Show you think about design
7. **Be ready to extend** - Have follow-up answers ready
8. **Show confidence** - You know what you're building

---

## 🎯 Success Criteria

You'll ace the interview if you:

✅ Implement working system in time
✅ Explain design patterns clearly
✅ Show SOLID principles applied
✅ Handle follow-up questions well
✅ Write clean, readable code
✅ Verify with working tests
✅ Discuss trade-offs intelligently
✅ Show you can extend the design

---

**You've got this! 💪**

Start with reading 75_MINUTE_GUIDE.md, reference INTERVIEW_COMPACT.py as you code, and you'll be ready!
