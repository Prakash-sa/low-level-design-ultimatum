"""
Display.py - Elevator display with Observer pattern
Implements SOLID: Single Responsibility (display rendering only)
                  Dependency Inversion (receives data from elevator)
"""

from typing import Optional
from Direction import ElevatorState, Direction


class Display:
    """
    Display unit showing elevator status to passengers.
    
    Design Pattern: Observer
    - Receives updates from ElevatorCar when state changes
    - Displays current floor, direction, and state
    
    SOLID Principles:
    - Single Responsibility: Only manages display output
    - Interface Segregation: Implements update(car) interface
    - Open/Closed: Can extend with new display formats
    """

    def __init__(self, display_id: int = 0):
        """
        Initialize display.
        
        Args:
            display_id: Unique identifier for this display
        """
        self.display_id = display_id
        self.current_floor = 0
        self.current_direction = Direction.IDLE
        self.current_state = ElevatorState.IDLE
        self.destination_floor: Optional[int] = None
        self.load_percentage = 0

    def update(self, car) -> None:
        """
        Update display based on elevator car state.
        
        This method is called by ElevatorCar when its state changes.
        Implements observer pattern.
        
        Args:
            car: ElevatorCar object with current state
        """
        self.current_floor = car.get_current_floor()
        self.current_direction = car.get_direction()
        self.current_state = car.get_state()
        self.destination_floor = car.get_next_destination()
        self.load_percentage = car.get_load_percentage()

    def render(self) -> str:
        """
        Render display output.
        
        Returns:
            String representation of display
        """
        state_symbol = self._get_state_symbol()
        direction_symbol = self._get_direction_symbol()

        return (
            f"┌─── Display #{self.display_id} ─────────┐\n"
            f"│ Floor: {self.current_floor:2d}              │\n"
            f"│ Direction: {direction_symbol}              │\n"
            f"│ State: {state_symbol:10s}        │\n"
            f"│ Load: {self.load_percentage:3d}%             │\n"
            f"│ Destination: {self.destination_floor if self.destination_floor else '-':2} │\n"
            f"└────────────────────────┘"
        )

    def get_floor(self) -> int:
        """Get displayed floor."""
        return self.current_floor

    def get_direction(self) -> Direction:
        """Get displayed direction."""
        return self.current_direction

    def get_state(self) -> ElevatorState:
        """Get displayed state."""
        return self.current_state

    def _get_state_symbol(self) -> str:
        """Get symbol representing current state."""
        state_map = {
            ElevatorState.IDLE: "⊗",
            ElevatorState.MOVING_UP: "↑",
            ElevatorState.MOVING_DOWN: "↓",
            ElevatorState.DOOR_OPEN: "⊙",
            ElevatorState.MAINTENANCE: "⚙",
            ElevatorState.EMERGENCY: "⚠",
        }
        return state_map.get(self.current_state, "?")

    def _get_direction_symbol(self) -> str:
        """Get symbol representing current direction."""
        direction_map = {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.IDLE: "-",
        }
        return direction_map.get(self.current_direction, "?")

    def __str__(self) -> str:
        return (
            f"Display(floor={self.current_floor}, "
            f"dir={self.current_direction}, "
            f"state={self.current_state})"
        )


class VerboseDisplay(Display):
    """
    Extended display with detailed information logging.
    
    Demonstrates SOLID Open/Closed principle - extends Display without modification.
    """

    def __init__(self, display_id: int = 0):
        super().__init__(display_id)
        self.log_history = []

    def update(self, car) -> None:
        """Update with logging."""
        old_floor = self.current_floor
        super().update(car)
        
        if old_floor != self.current_floor:
            log_entry = (
                f"[Display #{self.display_id}] "
                f"Floor changed: {old_floor} → {self.current_floor}"
            )
            self.log_history.append(log_entry)

    def render(self) -> str:
        """Render with additional details."""
        base_render = super().render()
        
        if self.log_history:
            recent_logs = "\n".join(self.log_history[-3:])  # Last 3 logs
            return base_render + "\n" + recent_logs
        
        return base_render

    def get_log_history(self) -> list:
        """Get complete log history."""
        return self.log_history.copy()


class MinimalDisplay(Display):
    """
    Minimal display showing only essential information.
    
    Use case: Hallway displays in building
    """

    def render(self) -> str:
        """Render minimal display."""
        direction = self._get_direction_symbol()
        return f"🛗 Floor: {self.current_floor} {direction}"
