# Elevator System - 75 Minute Interview Implementation Guide

## ⏱️ Time Breakdown

- **0-5 min**: Problem clarification & requirements
- **5-15 min**: Design discussion & architecture
- **15-60 min**: Implementation (core + patterns)
- **60-75 min**: Testing & walk-through

---

## 📋 PART 1: Problem Clarification (5 minutes)

### What to Ask
1. How many floors? (assume 10)
2. How many elevators? (assume 3)
3. What's the main dispatch strategy? (nearest car)
4. Need emergency stop? (yes)
5. Need load management? (yes, for demo)

### Problem Statement to Confirm
**Design an elevator system for a multi-floor building that:**
- Handles calls from different floors (UP/DOWN)
- Dispatches nearest available elevator
- Manages elevator state (idle, moving, maintenance)
- Opens/closes doors at floors
- Tracks passenger load

---

## 🏗️ PART 2: Design Discussion (10 minutes)

### Entities to Identify
```
Building → Floors → Elevators → Requests
```

### Key Classes
1. **ElevatorCar** - Main entity, state machine
2. **ElevatorSystem** - Orchestrator (singleton)
3. **Floor/HallPanel** - Call buttons
4. **Door** - Door operations
5. **Dispatcher** - Request assignment
6. **Display** - Status display

### Design Patterns
- **Singleton**: ElevatorSystem (one instance)
- **Observer**: Display updates
- **Strategy**: Dispatcher algorithm
- **State**: Elevator states

### SOLID Quick Map
- **S**: Each class = one responsibility
- **O**: New dispatcher = new class, no modification
- **L**: All cars work the same
- **I**: Interfaces are minimal
- **D**: Depend on abstractions

---

## 💻 PART 3: Implementation (45 minutes)

### Phase 1: Enums & Basics (5 min)

```python
# 1. Direction.py
from enum import Enum

class Direction(Enum):
    UP = 1
    DOWN = 2
    IDLE = 3

class ElevatorState(Enum):
    IDLE = 1
    MOVING_UP = 2
    MOVING_DOWN = 3
    DOOR_OPEN = 4
    MAINTENANCE = 5

class DoorState(Enum):
    OPEN = 1
    CLOSED = 2
```

### Phase 2: Core Components (15 min)

```python
# 2. ElevatorCar.py (simplified)
from collections import deque
from Direction import ElevatorState, Direction, DoorState

class ElevatorCar:
    def __init__(self, car_id, num_floors):
        self.car_id = car_id
        self.current_floor = 0
        self.state = ElevatorState.IDLE
        self.direction = Direction.IDLE
        self.request_queue = deque()
        self.maintenance = False
        self.door_state = DoorState.CLOSED
        
    def register_request(self, floor, direction):
        """Add request to queue"""
        if self.maintenance or self.current_floor == floor:
            return False
        self.request_queue.append((floor, direction))
        return True
    
    def move_one_floor(self):
        """Simulate movement"""
        if self.state == ElevatorState.MOVING_UP:
            self.current_floor += 1
            self._check_arrival()
        elif self.state == ElevatorState.MOVING_DOWN:
            self.current_floor -= 1
            self._check_arrival()
    
    def _check_arrival(self):
        """Check if reached target"""
        if self.request_queue and self.current_floor == self.request_queue[0][0]:
            self.state = ElevatorState.DOOR_OPEN
            self.door_state = DoorState.OPEN
            self.request_queue.popleft()
    
    def depart_floor(self):
        """Leave current floor"""
        self.door_state = DoorState.CLOSED
        if self.request_queue:
            target_floor = self.request_queue[0][0]
            self.direction = Direction.UP if target_floor > self.current_floor else Direction.DOWN
            self.state = ElevatorState.MOVING_UP if self.direction == Direction.UP else ElevatorState.MOVING_DOWN
        else:
            self.state = ElevatorState.IDLE
            self.direction = Direction.IDLE
    
    def enter_maintenance(self):
        """Put in maintenance"""
        self.maintenance = True
        self.state = ElevatorState.MAINTENANCE
        self.request_queue.clear()
    
    def exit_maintenance(self):
        """Exit maintenance"""
        self.maintenance = False
        self.state = ElevatorState.IDLE
    
    def get_status(self):
        """Get current status"""
        return {
            'id': self.car_id,
            'floor': self.current_floor,
            'state': self.state.name,
            'direction': self.direction.name,
            'queue_size': len(self.request_queue),
            'in_maintenance': self.maintenance
        }
```

### Phase 3: System Controller (12 min)

```python
# 3. ElevatorSystem.py (singleton + dispatcher)
from Direction import Direction

class ElevatorSystem:
    _instance = None
    
    def __init__(self, num_floors, num_cars):
        self.num_floors = num_floors
        self.cars = [ElevatorCar(i, num_floors) for i in range(num_cars)]
        self.floors = list(range(num_floors))
    
    @staticmethod
    def get_instance(num_floors=10, num_cars=3):
        """Singleton pattern"""
        if ElevatorSystem._instance is None:
            ElevatorSystem._instance = ElevatorSystem(num_floors, num_cars)
        return ElevatorSystem._instance
    
    def call_elevator(self, floor, direction):
        """Main method: call elevator from floor"""
        # Find best car using simple dispatcher
        best_car = self._find_best_car(floor, direction)
        if best_car:
            best_car.register_request(floor, direction)
        return best_car
    
    def _find_best_car(self, floor, direction):
        """Find nearest idle car"""
        available_cars = [c for c in self.cars if not c.maintenance]
        if not available_cars:
            return None
        
        idle_cars = [c for c in available_cars if c.state == ElevatorState.IDLE]
        if idle_cars:
            # Pick closest idle car
            return min(idle_cars, key=lambda c: abs(c.current_floor - floor))
        
        # Pick closest moving car
        return min(available_cars, key=lambda c: abs(c.current_floor - floor))
    
    def move_all_cars(self):
        """Simulate one time step for all cars"""
        for car in self.cars:
            if car.state in (ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN):
                car.move_one_floor()
    
    def depart_from_floor(self, car_id):
        """Car departs from current floor"""
        if 0 <= car_id < len(self.cars):
            self.cars[car_id].depart_floor()
    
    def get_system_status(self):
        """Get status of all cars"""
        return [car.get_status() for car in self.cars]
    
    def print_status(self):
        """Pretty print system status"""
        print("\n" + "="*60)
        print(f"{'ID':<3} {'Floor':<6} {'State':<15} {'Dir':<6} {'Queue':<6} {'Maint':<6}")
        print("="*60)
        for status in self.get_system_status():
            print(f"{status['id']:<3} {status['floor']:<6} {status['state']:<15} {status['direction']:<6} {status['queue_size']:<6} {str(status['in_maintenance']):<6}")
        print("="*60 + "\n")
```

### Phase 4: Button & Panel Classes (8 min)

```python
# 4. Button.py
from abc import ABC, abstractmethod

class Button(ABC):
    def __init__(self):
        self.pressed = False
    
    def press(self):
        self.pressed = True
        self.execute()
    
    @abstractmethod
    def execute(self):
        pass

class HallButton(Button):
    def __init__(self, floor, direction):
        super().__init__()
        self.floor = floor
        self.direction = direction
    
    def execute(self):
        print(f"Hall button pressed: Floor {self.floor}, Direction {self.direction.name}")

class ElevatorButton(Button):
    def __init__(self, floor):
        super().__init__()
        self.floor = floor
    
    def execute(self):
        print(f"Elevator button pressed: Floor {self.floor}")

# 5. ElevatorPanel.py
class ElevatorPanel:
    def __init__(self, car_id, num_floors):
        self.car_id = car_id
        self.buttons = [ElevatorButton(floor) for floor in range(num_floors)]
    
    def press_floor(self, floor):
        if 0 <= floor < len(self.buttons):
            self.buttons[floor].press()

class HallPanel:
    def __init__(self, floor, num_floors):
        self.floor = floor
        self.up_button = HallButton(floor, Direction.UP) if floor < num_floors - 1 else None
        self.down_button = HallButton(floor, Direction.DOWN) if floor > 0 else None
    
    def call_up(self):
        if self.up_button:
            self.up_button.press()
    
    def call_down(self):
        if self.down_button:
            self.down_button.press()
```

### Phase 5: Observer Pattern (5 min)

```python
# 6. Display.py (Observer)
class Observer:
    def update(self, car):
        pass

class Display(Observer):
    def __init__(self, car_id):
        self.car_id = car_id
        self.current_floor = 0
        self.state = None
    
    def update(self, car):
        """Called when car state changes"""
        self.current_floor = car.current_floor
        self.state = car.state
        self.display()
    
    def display(self):
        print(f"[Display Car {self.car_id}] Floor: {self.current_floor}, State: {self.state.name}")

# Add to ElevatorCar:
class ElevatorCar:
    # ... existing code ...
    def __init__(self, car_id, num_floors):
        # ... existing code ...
        self.observers = []
    
    def subscribe(self, observer):
        self.observers.append(observer)
    
    def _notify_observers(self):
        for observer in self.observers:
            observer.update(self)
```

---

## ✅ PART 4: Testing & Demo (15 minutes)

### Test Scenarios (main.py)

```python
# main.py - Demo scenarios for 75 min interview

from ElevatorSystem import ElevatorSystem, ElevatorCar
from Direction import Direction, ElevatorState
from ElevatorPanel import HallPanel
from Display import Display

def scenario_1_basic_call():
    """Basic call from one floor"""
    print("\n" + "="*60)
    print("SCENARIO 1: Basic Hall Call")
    print("="*60)
    
    system = ElevatorSystem.get_instance(floors=10, cars=3)
    
    # Passenger on floor 3 calls elevator UP
    print("\n→ Passenger on floor 3 calls elevator UP")
    car = system.call_elevator(floor=3, direction=Direction.UP)
    print(f"✓ Car {car.car_id} assigned, current floor: {car.current_floor}")
    
    system.print_status()

def scenario_2_movement():
    """Elevator moves to floor"""
    print("\n" + "="*60)
    print("SCENARIO 2: Movement Simulation")
    print("="*60)
    
    ElevatorSystem._instance = None
    system = ElevatorSystem.get_instance(floors=10, cars=2)
    
    # Call from floor 5
    print("\n→ Call from floor 5 (UP)")
    car = system.call_elevator(floor=5, direction=Direction.UP)
    
    # Subscribe to display
    display = Display(car.car_id)
    car.subscribe(display)
    
    print(f"\n→ Car {car.car_id} moving to floor 5...")
    car.move_one_floor()
    car._notify_observers()
    
    print(f"Floor: {car.current_floor}, State: {car.state.name}")

def scenario_3_maintenance():
    """Put car in maintenance"""
    print("\n" + "="*60)
    print("SCENARIO 3: Maintenance Mode")
    print("="*60)
    
    ElevatorSystem._instance = None
    system = ElevatorSystem.get_instance(floors=10, cars=2)
    
    car = system.cars[0]
    print(f"\n→ Putting car {car.car_id} into maintenance")
    car.enter_maintenance()
    
    print(f"Car {car.car_id} state: {car.state.name}")
    print(f"Can accept requests: {not car.maintenance}")
    
    print("\n→ Calling elevator (should go to different car)")
    new_car = system.call_elevator(floor=5, direction=Direction.UP)
    print(f"✓ Car {new_car.car_id} assigned")
    
    system.print_status()

def scenario_4_multiple_calls():
    """Multiple simultaneous calls"""
    print("\n" + "="*60)
    print("SCENARIO 4: Multiple Simultaneous Calls")
    print("="*60)
    
    ElevatorSystem._instance = None
    system = ElevatorSystem.get_instance(floors=10, cars=3)
    
    calls = [(2, Direction.UP), (8, Direction.DOWN), (5, Direction.UP)]
    
    for floor, direction in calls:
        print(f"\n→ Call from floor {floor} ({direction.name})")
        car = system.call_elevator(floor, direction)
        print(f"✓ Assigned to car {car.car_id}")
    
    system.print_status()

def scenario_5_interior_selection():
    """Passenger selects floor inside car"""
    print("\n" + "="*60)
    print("SCENARIO 5: Interior Floor Selection")
    print("="*60)
    
    ElevatorSystem._instance = None
    system = ElevatorSystem.get_instance(floors=10, cars=1)
    
    car = system.cars[0]
    
    print("\n→ Passenger calls from floor 2 (UP)")
    system.call_elevator(floor=2, direction=Direction.UP)
    
    print("→ Passenger boards and selects floor 7")
    car.register_request(floor=7, direction=Direction.IDLE)
    
    print(f"Queue size: {len(car.request_queue)}")
    print(f"Requests: {[(f, d.name) for f, d in car.request_queue]}")

def main():
    print("\n" + "="*60)
    print("ELEVATOR SYSTEM - 75 MINUTE INTERVIEW IMPLEMENTATION")
    print("="*60)
    
    scenarios = [
        scenario_1_basic_call,
        scenario_2_movement,
        scenario_3_maintenance,
        scenario_4_multiple_calls,
        scenario_5_interior_selection,
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        try:
            scenario()
            print(f"\n✓ Scenario {i} completed")
        except Exception as e:
            print(f"\n✗ Scenario {i} failed: {e}")

if __name__ == "__main__":
    main()
```

---

## 📊 What You've Covered

### Design Patterns (Interview Points)
✅ **Singleton** - ElevatorSystem (one instance)
✅ **Observer** - Display subscribes to car changes
✅ **Strategy** - Dispatcher algorithm (_find_best_car)
✅ **State** - ElevatorState enum
✅ **Command** - Button hierarchy

### SOLID Principles
✅ **S**: Each class one responsibility
✅ **O**: Add new strategies without modifying
✅ **L**: All cars interchangeable
✅ **I**: Minimal interfaces
✅ **D**: Depend on abstractions (Observer)

### Features Demonstrated
✅ Call elevator from floor
✅ Dispatch to nearest car
✅ Movement simulation
✅ Door open/close
✅ Maintenance mode
✅ Observer pattern
✅ Multiple requests
✅ State tracking

---

## 💡 Interview Tips

### When Asked "How would you extend this?"
- **New dispatcher**: Create new class, implement `_find_best_car` logic
- **Priority floors**: Add priority to request tuple
- **Concurrent requests**: Add thread-safe queue
- **Load management**: Add `load` and `capacity` to ElevatorCar

### Common Follow-ups
1. **How to handle stuck elevator?** 
   - Add health check, auto-maintenance mode

2. **How to optimize dispatch?**
   - SCAN algorithm (sweep up/down)
   - Look-ahead (consider queue depth)

3. **How to test this?**
   - Unit tests for each class
   - Integration tests for scenarios

4. **Complexity?**
   - Dispatch: O(N) where N = cars
   - Movement: O(1) per floor
   - Memory: O(N*M) for N cars, M requests

---

## 🎯 Implementation Checklist

- [ ] **0-5 min**: Clarify requirements
- [ ] **5-15 min**: Draw architecture on whiteboard
- [ ] **15-20 min**: Create enums (Direction, ElevatorState, DoorState)
- [ ] **20-35 min**: Implement ElevatorCar class
- [ ] **35-50 min**: Implement ElevatorSystem (singleton + dispatcher)
- [ ] **50-60 min**: Add Button & Panel classes
- [ ] **60-65 min**: Add Display (Observer pattern)
- [ ] **65-75 min**: Run demo scenarios & explain design

---

## 📝 Total Lines of Code

- **Direction.py**: ~20 lines
- **ElevatorCar.py**: ~50 lines
- **ElevatorSystem.py**: ~45 lines
- **Button.py**: ~25 lines
- **ElevatorPanel.py**: ~20 lines
- **Display.py**: ~20 lines
- **main.py**: ~80 lines

**Total: ~260 lines** - Perfect for 75-minute interview!

---

## 🚀 Start Coding!

Begin with Phase 1 (enums), then systematically implement each phase. Show working code at each step. Explain design patterns as you implement them.
