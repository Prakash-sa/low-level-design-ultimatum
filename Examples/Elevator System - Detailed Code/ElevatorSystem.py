"""
ElevatorSystem.py - Main elevator system controller with Singleton pattern
Implements SOLID: Single Responsibility (orchestration only)
                  Open/Closed (dispatcher strategy is pluggable)
                  Dependency Inversion (depends on DispatcherStrategy)
"""

from typing import List, Optional, Dict
from Direction import Direction, ElevatorState
from ElevatorCar import ElevatorCar
from ElevatorPanel import Floor
from Display import Display
from Dispatcher import DispatcherStrategy, NearestIdleDispatcher


class Building:
    """
    Represents a building with multiple floors and elevator cars.
    
    SOLID: Single Responsibility - manages building structure only
    """

    def __init__(self, num_floors: int, num_cars: int):
        """
        Initialize building.
        
        Args:
            num_floors: Number of floors (0 to num_floors-1)
            num_cars: Number of elevator cars
        """
        self.num_floors = num_floors
        self.num_cars = num_cars

        # Create elevator cars
        self.cars: List[ElevatorCar] = []
        for car_id in range(num_cars):
            car = ElevatorCar(car_id=car_id, num_floors=num_floors)
            self.cars.append(car)

        # Create floors with hall panels
        self.floors: List[Floor] = []
        for floor_num in range(num_floors):
            floor = Floor(floor_number=floor_num, num_floors=num_floors)
            self.floors.append(floor)

    def get_floor(self, floor_num: int) -> Optional[Floor]:
        """Get floor by number."""
        if 0 <= floor_num < self.num_floors:
            return self.floors[floor_num]
        return None

    def get_floors(self) -> List[Floor]:
        """Get all floors."""
        return self.floors.copy()

    def get_cars(self) -> List[ElevatorCar]:
        """Get all elevator cars."""
        return self.cars.copy()

    def get_car(self, car_id: int) -> Optional[ElevatorCar]:
        """Get specific car by ID."""
        if 0 <= car_id < len(self.cars):
            return self.cars[car_id]
        return None

    def __str__(self) -> str:
        return f"Building(floors={self.num_floors}, cars={self.num_cars})"


class ElevatorSystem:
    """
    Main elevator system controller.
    
    Design Pattern: Singleton
    - Only one instance of system exists
    - Centralized control and monitoring
    - Single point of access
    
    Design Pattern: Strategy (for dispatcher)
    - Pluggable dispatch algorithms
    - Easy to switch strategies at runtime
    
    SOLID Principles:
    - Single Responsibility: Orchestrates system only
    - Open/Closed: Dispatcher strategy is extensible
    - Dependency Inversion: Depends on DispatcherStrategy interface
    - Liskov Substitution: Any DispatcherStrategy works
    """

    _instance: Optional['ElevatorSystem'] = None

    def __init__(self, num_floors: int, num_cars: int):
        """
        Initialize elevator system (private - use get_instance).
        
        Args:
            num_floors: Number of floors in building
            num_cars: Number of elevator cars
        """
        self.building = Building(num_floors=num_floors, num_cars=num_cars)
        self._dispatcher: DispatcherStrategy = NearestIdleDispatcher()

    @staticmethod
    def get_instance(num_floors: int = 10, num_cars: int = 3) -> 'ElevatorSystem':
        """
        Get singleton instance of elevator system.
        
        SOLID: Factory method - centralized object creation
        
        Args:
            num_floors: Number of floors (used only on first call)
            num_cars: Number of cars (used only on first call)
            
        Returns:
            Singleton ElevatorSystem instance
        """
        if ElevatorSystem._instance is None:
            ElevatorSystem._instance = ElevatorSystem(num_floors, num_cars)
        return ElevatorSystem._instance

    @staticmethod
    def reset_instance() -> None:
        """Reset singleton (useful for testing)."""
        ElevatorSystem._instance = None

    # ==================== Dispatcher Management ====================

    def set_dispatcher(self, dispatcher: DispatcherStrategy) -> None:
        """
        Set the dispatch strategy.
        
        SOLID: Open/Closed - plug in different algorithms
        
        Args:
            dispatcher: New dispatcher strategy to use
        """
        self._dispatcher = dispatcher

    def get_dispatcher(self) -> DispatcherStrategy:
        """Get current dispatcher strategy."""
        return self._dispatcher

    # ==================== Call Handling ====================

    def call_elevator(self, floor: int, direction: Direction) -> Optional[ElevatorCar]:
        """
        Process a hall call from a specific floor.
        
        Args:
            floor: Floor requesting elevator
            direction: Direction requested (UP/DOWN)
            
        Returns:
            Assigned ElevatorCar, or None if no suitable car
        """
        # Validate floor
        if not (0 <= floor < self.building.num_floors):
            return None

        # Dispatch suitable car
        car_index = self._dispatcher.dispatch(floor, direction, self.building.cars)

        if car_index is None:
            return None

        assigned_car = self.building.cars[car_index]

        # Register request with car
        assigned_car.register_request(floor=floor, direction=direction)

        return assigned_car

    def register_floor_request(self, car_id: int, floor: int) -> bool:
        """
        Register a floor selection request inside an elevator.
        
        Args:
            car_id: ID of elevator car
            floor: Destination floor
            
        Returns:
            True if request was accepted
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        return car.register_request(floor=floor, direction=Direction.IDLE)

    # ==================== Elevator Control ====================

    def put_elevator_in_maintenance(self, car_id: int) -> bool:
        """
        Put an elevator into maintenance mode.
        
        Args:
            car_id: ID of elevator to maintain
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.enter_maintenance()
        return True

    def release_elevator_from_maintenance(self, car_id: int) -> bool:
        """
        Release an elevator from maintenance mode.
        
        Args:
            car_id: ID of elevator
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.exit_maintenance()
        return True

    def emergency_stop(self, car_id: int) -> bool:
        """
        Trigger emergency stop on specific car.
        
        Args:
            car_id: ID of elevator
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.emergency_stop()
        return True

    def reset_emergency(self, car_id: int) -> bool:
        """
        Reset emergency stop on specific car.
        
        Args:
            car_id: ID of elevator
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.reset_emergency()
        return True

    # ==================== Movement Simulation ====================

    def move_car_one_floor(self, car_id: int) -> bool:
        """
        Simulate elevator moving one floor.
        
        Args:
            car_id: ID of car to move
            
        Returns:
            True if movement was simulated
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.move_one_floor()
        return True

    def move_all_cars(self) -> int:
        """
        Move all active cars one floor each.
        
        Returns:
            Number of cars moved
        """
        count = 0
        for car in self.building.cars:
            if car.get_state() in (ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN):
                car.move_one_floor()
                count += 1
        return count

    def depart_floor(self, car_id: int) -> bool:
        """
        Depart from current floor and move to next request.
        
        Args:
            car_id: ID of car
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.depart_floor()
        return True

    # ==================== System Status ====================

    def get_system_status(self) -> Dict:
        """
        Get complete system status.
        
        Returns:
            Dictionary with building and all cars status
        """
        return {
            "building": str(self.building),
            "dispatcher": self._dispatcher.__class__.__name__,
            "cars": [car.get_status() for car in self.building.cars],
        }

    def get_car_status(self, car_id: int) -> Optional[Dict]:
        """Get status of specific car."""
        car = self.building.get_car(car_id)
        return car.get_status() if car else None

    def get_all_cars_status(self) -> List[Dict]:
        """Get status of all cars."""
        return [car.get_status() for car in self.building.cars]

    def print_system_status(self) -> None:
        """Print system status to console."""
        print("\n" + "=" * 60)
        print(f"  {self.building}")
        print(f"  Dispatcher: {self._dispatcher.__class__.__name__}")
        print("=" * 60)

        for car in self.building.cars:
            print(f"  {car}")

        print("=" * 60 + "\n")

    # ==================== Building Access ====================

    def get_building(self) -> Building:
        """Get building reference."""
        return self.building

    def get_elevators(self) -> List[ElevatorCar]:
        """Get list of all elevator cars."""
        return self.building.get_cars()

    def get_floors(self) -> List[Floor]:
        """Get list of all floors."""
        return self.building.get_floors()

    def get_floor(self, floor_num: int) -> Optional[Floor]:
        """Get specific floor."""
        return self.building.get_floor(floor_num)

    # ==================== Display Integration ====================

    def subscribe_display_to_car(self, car_id: int, display: Display) -> bool:
        """
        Subscribe a display to elevator car state changes.
        
        Args:
            car_id: ID of car
            display: Display object to subscribe
            
        Returns:
            True if successful
        """
        car = self.building.get_car(car_id)
        if car is None:
            return False

        car.subscribe(display)
        return True

    def get_display_for_car(self, car_id: int) -> Optional[Display]:
        """Get built-in display for a car."""
        car = self.building.get_car(car_id)
        return car.get_display() if car else None

    # ==================== Statistics ====================

    def get_total_pending_requests(self) -> int:
        """Get total requests across all cars."""
        return sum(car.get_request_queue_size() for car in self.building.cars)

    def get_idle_cars_count(self) -> int:
        """Count idle cars."""
        return sum(1 for car in self.building.cars if car.get_state() == ElevatorState.IDLE)

    def get_moving_cars_count(self) -> int:
        """Count cars currently moving."""
        return sum(1 for car in self.building.cars if car.get_state().is_moving())

    def get_maintenance_cars_count(self) -> int:
        """Count cars in maintenance."""
        return sum(1 for car in self.building.cars if car.is_in_maintenance())

    # ==================== String Representation ====================

    def __str__(self) -> str:
        return (
            f"ElevatorSystem(floors={self.building.num_floors}, "
            f"cars={self.building.num_cars}, "
            f"dispatcher={self._dispatcher.__class__.__name__})"
        )
