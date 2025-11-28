"""
Button.py - Button hierarchy implementing Command Pattern
Implements SOLID: Interface Segregation (each button type has specific behavior)
                  Liskov Substitution (all buttons can be executed)
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class Button(ABC):
    """
    Abstract base class for all buttons in the elevator system.
    
    Design Pattern: Command Pattern
    - Each button press can be treated as an object that can be queued, executed, etc.
    
    SOLID Principles:
    - Interface Segregation: Minimal interface (execute, is_pressed)
    - Liskov Substitution: All button types substitute Button transparently
    - Open/Closed: Easy to add new button types without modifying existing code
    """

    def __init__(self, action: Optional[Callable] = None):
        """
        Initialize button with optional action callback.
        
        Args:
            action: Optional callable to execute when button is pressed
        """
        self._pressed = False
        self._action = action

    def press(self) -> None:
        """Mark button as pressed and execute associated action."""
        self._pressed = True
        self.execute()

    def release(self) -> None:
        """Mark button as released."""
        self._pressed = False

    def is_pressed(self) -> bool:
        """Check if button is currently pressed."""
        return self._pressed

    @abstractmethod
    def execute(self) -> None:
        """Execute the action associated with this button press."""
        if self._action:
            self._action()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(pressed={self._pressed})"


class HallButton(Button):
    """
    Button pressed by passenger on a floor to call an elevator.
    
    Attributes:
        floor: Which floor this button is on
        direction: UP or DOWN direction requested
    
    SOLID: Single Responsibility - only handles hall calls
    """

    def __init__(self, floor: int, direction, action: Optional[Callable] = None):
        """
        Initialize hall button.
        
        Args:
            floor: Floor number for this button
            direction: Direction enum (UP or DOWN)
            action: Callback when pressed (typically registered with system)
        """
        super().__init__(action)
        self.floor = floor
        self.direction = direction

    def execute(self) -> None:
        """Execute: notify system of hall call."""
        super().execute()

    def get_floor(self) -> int:
        """Get the floor number."""
        return self.floor

    def get_direction(self):
        """Get the direction (UP/DOWN)."""
        return self.direction

    def __str__(self) -> str:
        return f"HallButton(floor={self.floor}, dir={self.direction}, pressed={self._pressed})"


class ElevatorButton(Button):
    """
    Button pressed inside an elevator to select destination floor.
    
    Attributes:
        floor: Destination floor selected
    
    SOLID: Single Responsibility - only handles interior floor selection
    """

    def __init__(self, floor: int, action: Optional[Callable] = None):
        """
        Initialize elevator button (floor selector).
        
        Args:
            floor: Destination floor number
            action: Callback when pressed (typically registered with car)
        """
        super().__init__(action)
        self.floor = floor

    def execute(self) -> None:
        """Execute: register floor request with elevator car."""
        super().execute()

    def get_destination_floor(self) -> int:
        """Get the destination floor."""
        return self.floor

    def __str__(self) -> str:
        return f"ElevatorButton(floor={self.floor}, pressed={self._pressed})"


class DoorButton(Button):
    """
    Base class for door-related buttons (open/close).
    
    SOLID: Interface Segregation - minimal door control interface
    """

    def __init__(self, door_action: str, action: Optional[Callable] = None):
        """
        Initialize door button.
        
        Args:
            door_action: "OPEN" or "CLOSE"
            action: Callback when pressed
        """
        super().__init__(action)
        self.door_action = door_action

    def execute(self) -> None:
        """Execute: trigger door action."""
        super().execute()

    def get_action(self) -> str:
        """Get the door action type."""
        return self.door_action


class DoorOpenButton(DoorButton):
    """Button to open door manually."""

    def __init__(self, action: Optional[Callable] = None):
        super().__init__("OPEN", action)

    def __str__(self) -> str:
        return f"DoorOpenButton(pressed={self._pressed})"


class DoorCloseButton(DoorButton):
    """Button to close door manually."""

    def __init__(self, action: Optional[Callable] = None):
        super().__init__("CLOSE", action)

    def __str__(self) -> str:
        return f"DoorCloseButton(pressed={self._pressed})"


class EmergencyButton(Button):
    """
    Emergency stop button to halt elevator immediately.
    
    SOLID: Single Responsibility - only triggers emergency stop
    """

    def __init__(self, action: Optional[Callable] = None):
        """
        Initialize emergency button.
        
        Args:
            action: Callback when pressed (typically stops car immediately)
        """
        super().__init__(action)

    def execute(self) -> None:
        """Execute: trigger emergency stop."""
        super().execute()

    def __str__(self) -> str:
        return f"EmergencyButton(emergency_active={self._pressed})"


class AlarmButton(Button):
    """Button to sound alarm and alert maintenance staff."""

    def __init__(self, action: Optional[Callable] = None):
        super().__init__(action)

    def execute(self) -> None:
        """Execute: sound alarm."""
        super().execute()

    def __str__(self) -> str:
        return f"AlarmButton(alarm_active={self._pressed})"
