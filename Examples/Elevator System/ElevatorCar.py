"""
ElevatorCar.py - Main elevator car with state management and Observer pattern
Implements SOLID: Single Responsibility (car state and movement only)
                  Open/Closed (extensible via observers)
                  Liskov Substitution (cars are interchangeable)
                  Interface Segregation (depends on interfaces only)
                  Dependency Inversion (depends on Observer, not concrete observers)
"""

from collections import deque
from typing import List, Optional, Set
from Direction import ElevatorState, Direction
from Door import Door, Observer
from Display import Display
from ElevatorRequest import ElevatorRequest


class ElevatorCar:
    """
    Represents an elevator car with complete state management.
    
    Design Pattern: Observer Subject
    - Maintains state
    - Notifies observers (Display, Door, Panel) of changes
    - Processes requests in order
    
    SOLID Principles:
    - Single Responsibility: Manages car movement and state only
    - Open/Closed: Extensible via observers and strategies
    - Liskov Substitution: All cars behave consistently
    - Interface Segregation: Minimal public interface
    - Dependency Inversion: Depends on Observer interface
    """

    # Car configuration
    DEFAULT_CAPACITY = 1000  # kg
    DEFAULT_MAX_LOAD_PERCENTAGE = 80  # Overload at 80%

    def __init__(
        self,
        car_id: int,
        num_floors: int,
        capacity: int = DEFAULT_CAPACITY,
    ):
        """
        Initialize elevator car.
        
        Args:
            car_id: Unique identifier
            num_floors: Total floors in building (0 to num_floors-1)
            capacity: Maximum weight capacity in kg
        """
        self.car_id = car_id
        self.num_floors = num_floors
        self.capacity = capacity

        # State management
        self._current_floor = 0
        self._state = ElevatorState.IDLE
        self._direction = Direction.IDLE

        # Physical components
        self.door = Door()
        self.display = Display(display_id=car_id)

        # Request management
        self._request_queue: deque = deque()
        self._processed_requests: Set[ElevatorRequest] = set()

        # Passenger management
        self._current_load = 0  # kg
        self._is_overloaded = False
        self._is_in_maintenance = False
        self._is_emergency_stop = False

        # Observer management
        self._observers: List[Observer] = []

    # ==================== State Queries ====================

    def get_id(self) -> int:
        """Get car ID."""
        return self.car_id

    def get_current_floor(self) -> int:
        """Get current floor."""
        return self._current_floor

    def get_state(self) -> ElevatorState:
        """Get current state."""
        return self._state

    def get_direction(self) -> Direction:
        """Get current direction of travel."""
        return self._direction

    def is_in_maintenance(self) -> bool:
        """Check if in maintenance mode."""
        return self._is_in_maintenance

    def is_overloaded(self) -> bool:
        """Check if currently overloaded."""
        return self._is_overloaded

    def is_emergency_stop(self) -> bool:
        """Check if emergency stop is active."""
        return self._is_emergency_stop

    def get_current_load(self) -> float:
        """Get current passenger load in kg."""
        return self._current_load

    def get_load_percentage(self) -> int:
        """Get load as percentage of capacity."""
        if self.capacity == 0:
            return 0
        return int((self._current_load / self.capacity) * 100)

    def get_next_destination(self) -> Optional[int]:
        """Get next floor in queue, or None if empty."""
        if self._request_queue:
            return self._request_queue[0].floor
        return None

    def get_request_queue_size(self) -> int:
        """Get number of pending requests."""
        return len(self._request_queue)

    def is_at_floor(self, floor: int) -> bool:
        """Check if elevator is at specific floor."""
        return self._current_floor == floor

    def can_accept_request(self) -> bool:
        """Check if elevator can accept new requests."""
        return (
            not self._is_in_maintenance
            and not self._is_emergency_stop
            and not self._is_overloaded
            and self._state != ElevatorState.EMERGENCY
        )

    # ==================== Request Management ====================

    def register_request(self, floor: int, direction: Direction = Direction.IDLE) -> bool:
        """
        Register a floor request in the queue.
        
        Args:
            floor: Target floor
            direction: Direction of call (UP/DOWN)
            
        Returns:
            True if request was queued, False if car cannot accept
        """
        if not self.can_accept_request():
            return False

        if not (0 <= floor < self.num_floors):
            return False

        request = ElevatorRequest(floor=floor, direction=direction)

        # Avoid duplicate requests
        if request in self._request_queue:
            return False

        self._request_queue.append(request)
        self._notify_observers()
        return True

    def has_pending_requests(self) -> bool:
        """Check if there are any pending requests."""
        return len(self._request_queue) > 0

    def get_next_request(self) -> Optional[ElevatorRequest]:
        """Get next request without removing it."""
        if self._request_queue:
            return self._request_queue[0]
        return None

    def _pop_next_request(self) -> Optional[ElevatorRequest]:
        """Remove and return next request."""
        if self._request_queue:
            return self._request_queue.popleft()
        return None

    def clear_all_requests(self) -> None:
        """Clear all pending requests (use in emergency)."""
        self._request_queue.clear()
        self._notify_observers()

    # ==================== Movement ====================

    def move_to_floor(self, target_floor: int) -> bool:
        """
        Move elevator to target floor.
        
        Args:
            target_floor: Floor to move to
            
        Returns:
            True if movement started successfully
        """
        if self._is_in_maintenance or self._is_emergency_stop:
            return False

        if self._current_floor == target_floor:
            return self._arrive_at_floor()

        # Determine direction
        if target_floor > self._current_floor:
            self._direction = Direction.UP
            self._state = ElevatorState.MOVING_UP
        else:
            self._direction = Direction.DOWN
            self._state = ElevatorState.MOVING_DOWN

        self._notify_observers()
        return True

    def move_one_floor(self) -> None:
        """Simulate moving one floor."""
        if not self._state.is_moving():
            return

        if self._state == ElevatorState.MOVING_UP and self._current_floor < self.num_floors - 1:
            self._current_floor += 1
        elif self._state == ElevatorState.MOVING_DOWN and self._current_floor > 0:
            self._current_floor -= 1

        self._check_if_arrived()
        self._notify_observers()

    def _check_if_arrived(self) -> None:
        """Check if at next request floor."""
        next_request = self.get_next_request()
        if next_request and self._current_floor == next_request.floor:
            self._arrive_at_floor()

    def _arrive_at_floor(self) -> bool:
        """
        Handle arrival at a floor.
        
        Returns:
            True if floor was reached successfully
        """
        self._state = ElevatorState.DOOR_OPEN
        self._direction = Direction.IDLE
        self.door.open()

        # Process request at this floor
        request = self._pop_next_request()
        if request:
            self._processed_requests.add(request)

        self._notify_observers()
        return True

    def depart_floor(self) -> None:
        """Depart from current floor and close door."""
        self.door.close()
        
        if self.has_pending_requests():
            next_request = self.get_next_request()
            self.move_to_floor(next_request.floor)
        else:
            self._state = ElevatorState.IDLE
            self._direction = Direction.IDLE

        self._notify_observers()

    # ==================== Load Management ====================

    def add_load(self, weight: float) -> bool:
        """
        Add weight when passenger enters.
        
        Args:
            weight: Weight to add in kg
            
        Returns:
            True if load was accepted
        """
        new_load = self._current_load + weight

        if new_load > self.capacity:
            self._is_overloaded = True
            self._notify_observers()
            return False

        self._current_load = new_load
        self._is_overloaded = self._current_load > (
            self.capacity * self.DEFAULT_MAX_LOAD_PERCENTAGE / 100
        )
        self._notify_observers()
        return True

    def remove_load(self, weight: float) -> None:
        """
        Remove weight when passenger exits.
        
        Args:
            weight: Weight to remove in kg
        """
        self._current_load = max(0, self._current_load - weight)
        self._is_overloaded = self._current_load > (
            self.capacity * self.DEFAULT_MAX_LOAD_PERCENTAGE / 100
        )
        self._notify_observers()

    def clear_load(self) -> None:
        """Clear all load."""
        self._current_load = 0
        self._is_overloaded = False
        self._notify_observers()

    # ==================== Maintenance ====================

    def enter_maintenance(self) -> None:
        """Put car into maintenance mode."""
        self._is_in_maintenance = True
        self._state = ElevatorState.MAINTENANCE
        self.door.close()
        self.clear_all_requests()
        self._notify_observers()

    def exit_maintenance(self) -> None:
        """Take car out of maintenance mode."""
        self._is_in_maintenance = False
        self._state = ElevatorState.IDLE
        self._notify_observers()

    # ==================== Emergency ====================

    def emergency_stop(self) -> None:
        """Trigger emergency stop."""
        self._is_emergency_stop = True
        self._state = ElevatorState.EMERGENCY
        self._direction = Direction.IDLE
        self.door.close()
        self.clear_all_requests()
        self._notify_observers()

    def reset_emergency(self) -> None:
        """Reset emergency stop."""
        self._is_emergency_stop = False
        self._state = ElevatorState.IDLE
        self._notify_observers()

    # ==================== Observer Pattern ====================

    def subscribe(self, observer: Observer) -> None:
        """
        Subscribe observer to car state changes.
        
        SOLID: Dependency Injection - observers provided externally
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        """Unsubscribe observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self) -> None:
        """Notify all observers of state change."""
        for observer in self._observers:
            observer.update(self)

    # ==================== Display/Panel ====================

    def get_display(self) -> Display:
        """Get reference to display."""
        return self.display

    def get_door(self) -> Door:
        """Get reference to door."""
        return self.door

    # ==================== String Representation ====================

    def __str__(self) -> str:
        return (
            f"ElevatorCar("
            f"id={self.car_id}, "
            f"floor={self._current_floor}, "
            f"state={self._state.name}, "
            f"dir={self._direction.name}, "
            f"load={self.get_load_percentage()}%, "
            f"queue={self.get_request_queue_size()}"
            f")"
        )

    def get_status(self) -> dict:
        """Get complete status as dictionary."""
        return {
            "car_id": self.car_id,
            "current_floor": self._current_floor,
            "state": self._state.name,
            "direction": self._direction.name,
            "door_state": self.door.get_state().name,
            "load_percentage": self.get_load_percentage(),
            "is_overloaded": self._is_overloaded,
            "is_in_maintenance": self._is_in_maintenance,
            "is_emergency_stop": self._is_emergency_stop,
            "pending_requests": self.get_request_queue_size(),
            "next_destination": self.get_next_destination(),
        }
