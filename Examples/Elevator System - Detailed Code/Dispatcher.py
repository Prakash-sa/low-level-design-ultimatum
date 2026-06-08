"""
Dispatcher.py - Dispatcher strategies for assigning requests to elevators
Implements SOLID: Open/Closed (extensible via new strategies)
                  Dependency Inversion (depends on abstract strategy)
                  Single Responsibility (each strategy has one algorithm)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from Direction import Direction


class DispatcherStrategy(ABC):
    """
    Abstract base class for dispatcher strategies.
    
    Design Pattern: Strategy Pattern
    - Encapsulates different dispatching algorithms
    - Allows runtime selection of strategy
    - Makes algorithms interchangeable
    
    SOLID Principles:
    - Open/Closed: Add new strategies without modifying existing code
    - Dependency Inversion: System depends on abstract strategy
    - Interface Segregation: Minimal interface (dispatch method only)
    """

    @abstractmethod
    def dispatch(self, floor: int, direction: Direction, cars: List) -> Optional[int]:
        """
        Dispatch an elevator to a floor.
        
        Args:
            floor: Target floor
            direction: Direction of call (UP/DOWN/IDLE)
            cars: List of available ElevatorCar objects
            
        Returns:
            Index of selected car, or None if no suitable car found
        """
        pass

    def _get_distance(self, car_floor: int, target_floor: int) -> int:
        """Calculate distance between floors."""
        return abs(car_floor - target_floor)

    def _get_suitable_cars(self, cars: List) -> List[tuple]:
        """
        Filter cars that can accept requests.
        
        Returns:
            List of tuples (index, car) for suitable cars
        """
        suitable = []
        for idx, car in enumerate(cars):
            if car.can_accept_request():
                suitable.append((idx, car))
        return suitable


class NearestIdleDispatcher(DispatcherStrategy):
    """
    Select the nearest idle elevator.
    
    Algorithm:
    1. Find all idle elevators
    2. Select the one closest to the call floor
    3. If no idle cars, find the closest moving car
    
    Pros: Simple, fair distribution
    Cons: Doesn't optimize for direction
    
    Time Complexity: O(N) where N = number of cars
    """

    def dispatch(self, floor: int, direction: Direction, cars: List) -> Optional[int]:
        """Dispatch to nearest idle car, or nearest moving car."""
        suitable_cars = self._get_suitable_cars(cars)

        if not suitable_cars:
            return None

        # Find idle cars
        idle_cars = [(idx, car) for idx, car in suitable_cars if car.get_state().name == "IDLE"]

        if idle_cars:
            # Select nearest idle car
            best_idx, _ = min(
                idle_cars,
                key=lambda x: self._get_distance(x[1].get_current_floor(), floor),
            )
            return best_idx

        # No idle cars, select nearest moving car
        best_idx, _ = min(
            suitable_cars,
            key=lambda x: self._get_distance(x[1].get_current_floor(), floor),
        )
        return best_idx


class DirectionAwareDispatcher(DispatcherStrategy):
    """
    Select elevator going in same direction, closest to floor.
    
    Algorithm:
    1. Find cars already going in same direction and haven't passed floor
    2. If multiple, select closest
    3. If none, fall back to nearest idle car
    4. If still none, select nearest car moving in opposite direction
    
    Pros: Efficient, reduces wait time
    Cons: More complex logic
    
    Time Complexity: O(N) where N = number of cars
    """

    def dispatch(self, floor: int, direction: Direction, cars: List) -> Optional[int]:
        """Dispatch to car going in same direction."""
        suitable_cars = self._get_suitable_cars(cars)

        if not suitable_cars:
            return None

        # Find cars going in same direction
        same_direction_cars = [
            (idx, car)
            for idx, car in suitable_cars
            if self._is_going_towards(car, floor, direction)
        ]

        if same_direction_cars:
            # Select closest among cars going in same direction
            best_idx, _ = min(
                same_direction_cars,
                key=lambda x: self._get_distance(x[1].get_current_floor(), floor),
            )
            return best_idx

        # No cars going in same direction, find idle
        idle_cars = [(idx, car) for idx, car in suitable_cars if car.get_state().name == "IDLE"]

        if idle_cars:
            best_idx, _ = min(
                idle_cars,
                key=lambda x: self._get_distance(x[1].get_current_floor(), floor),
            )
            return best_idx

        # Last resort: nearest car regardless of direction
        best_idx, _ = min(
            suitable_cars,
            key=lambda x: self._get_distance(x[1].get_current_floor(), floor),
        )
        return best_idx

    def _is_going_towards(self, car, floor: int, direction: Direction) -> bool:
        """Check if car is moving towards floor in the requested direction."""
        car_floor = car.get_current_floor()
        car_direction = car.get_direction()

        if car_direction == Direction.IDLE:
            return False  # Car not moving

        # Check if car is going in same direction and hasn't passed the floor
        if direction == Direction.UP:
            return car_direction == Direction.UP and car_floor <= floor
        elif direction == Direction.DOWN:
            return car_direction == Direction.DOWN and car_floor >= floor

        return False


class LookAheadDispatcher(DispatcherStrategy):
    """
    Predictive dispatcher considering queue depth.
    
    Algorithm:
    1. Score each suitable car based on:
       - Distance to floor (lower is better)
       - Queue depth (lower is better)
       - Direction alignment (same direction preferred)
    2. Select car with lowest score
    
    Pros: Balances load, reduces overall wait time
    Cons: More complex calculation
    
    Time Complexity: O(N) where N = number of cars
    """

    def dispatch(self, floor: int, direction: Direction, cars: List) -> Optional[int]:
        """Dispatch using weighted scoring."""
        suitable_cars = self._get_suitable_cars(cars)

        if not suitable_cars:
            return None

        # Score each car
        scores = []
        for idx, car in suitable_cars:
            score = self._calculate_score(car, floor, direction)
            scores.append((idx, score))

        # Select car with lowest score
        best_idx, _ = min(scores, key=lambda x: x[1])
        return best_idx

    def _calculate_score(self, car, target_floor: int, direction: Direction) -> float:
        """
        Calculate dispatch score for a car.
        
        Lower score is better.
        """
        distance = self._get_distance(car.get_current_floor(), target_floor)
        queue_size = car.get_request_queue_size()
        
        # Direction bonus: -10 if going right direction, 0 otherwise
        direction_bonus = -10 if self._is_going_in_direction(car, target_floor, direction) else 0

        # Weighted sum: distance counts more than queue
        score = distance * 1.5 + queue_size * 0.5 + direction_bonus

        return score

    def _is_going_in_direction(self, car, floor: int, direction: Direction) -> bool:
        """Check if car is going in requested direction towards floor."""
        car_floor = car.get_current_floor()
        car_direction = car.get_direction()

        if car_direction == Direction.IDLE:
            return False

        if direction == Direction.UP:
            return car_direction == Direction.UP and car_floor <= floor
        elif direction == Direction.DOWN:
            return car_direction == Direction.DOWN and car_floor >= floor

        return False


class ScanDispatcher(DispatcherStrategy):
    """
    SCAN algorithm: Cars sweep up then down (or vice versa).
    
    Algorithm:
    1. Each car maintains direction
    2. Processes all up requests, then sweeps down
    3. Efficient for heavy loads
    
    Pros: Very efficient for heavy load
    Cons: Can have worst-case wait times
    
    Time Complexity: O(N)
    """

    def dispatch(self, floor: int, direction: Direction, cars: List) -> Optional[int]:
        """Dispatch using SCAN algorithm principles."""
        suitable_cars = self._get_suitable_cars(cars)

        if not suitable_cars:
            return None

        # Prefer cars already going in requested direction
        for idx, car in suitable_cars:
            if car.get_direction() == direction:
                return idx

        # Otherwise pick idle or nearest
        idle_cars = [(idx, car) for idx, car in suitable_cars if car.get_state().name == "IDLE"]

        if idle_cars:
            return idle_cars[0][0]

        return suitable_cars[0][0]
