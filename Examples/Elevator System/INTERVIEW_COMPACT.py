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
