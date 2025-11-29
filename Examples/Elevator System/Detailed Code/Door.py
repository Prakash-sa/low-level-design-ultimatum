"""
Door.py - Elevator door with state management and Observer pattern
Implements SOLID: Single Responsibility (door management only)
                  Open/Closed (extensible for new door types)
"""

from typing import List
from Direction import DoorState


class Observer:
    """
    Observer interface for door state changes.
    
    SOLID: Interface Segregation - minimal observer interface
    """

    def update(self, door: 'Door') -> None:
        """Called when door state changes."""
        pass


class Door:
    """
    Represents an elevator door with state management.
    
    Design Pattern: Observer (notifies subscribers of state changes)
    
    SOLID Principles:
    - Single Responsibility: Only manages door state
    - Open/Closed: Can extend with new behaviors via observers
    - Dependency Inversion: Depends on Observer interface, not concrete classes
    """

    OPEN_TIME_SECONDS = 3  # Time door stays open
    OPEN_CLOSE_TIME_SECONDS = 2  # Time to open or close

    def __init__(self):
        """Initialize door in closed state."""
        self._state = DoorState.CLOSED
        self._observers: List[Observer] = []
        self._open_timer = 0

    def get_state(self) -> DoorState:
        """Get current door state."""
        return self._state

    def open(self) -> bool:
        """
        Open the door.
        
        Returns:
            True if door opened successfully, False if already open/opening
        """
        if self._state in (DoorState.OPEN, DoorState.OPENING):
            return False

        self._state = DoorState.OPENING
        self._notify_observers()

        # Simulate opening
        self._state = DoorState.OPEN
        self._notify_observers()

        return True

    def close(self) -> bool:
        """
        Close the door.
        
        Returns:
            True if door closed successfully, False if already closed/closing
        """
        if self._state in (DoorState.CLOSED, DoorState.CLOSING):
            return False

        self._state = DoorState.CLOSING
        self._notify_observers()

        # Simulate closing
        self._state = DoorState.CLOSED
        self._notify_observers()

        return True

    def is_open(self) -> bool:
        """Check if door is open."""
        return self._state == DoorState.OPEN

    def is_closed(self) -> bool:
        """Check if door is closed."""
        return self._state == DoorState.CLOSED

    def can_enter_exit(self) -> bool:
        """Check if passengers can safely enter/exit."""
        return self._state == DoorState.OPEN

    def subscribe(self, observer: Observer) -> None:
        """
        Subscribe observer to door state changes.
        
        SOLID: Dependency Injection - observer provided externally
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        """Unsubscribe observer from door state changes."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self) -> None:
        """Notify all observers of state change."""
        for observer in self._observers:
            observer.update(self)

    def __str__(self) -> str:
        return f"Door(state={self._state})"


class ObservedDoor(Door):
    """
    Extended Door with automatic logging of state changes.
    
    Demonstrates SOLID Open/Closed principle - extends Door without modification.
    """

    def __init__(self, door_id: int = 0):
        super().__init__()
        self.door_id = door_id
        self.state_changes = []

    def open(self) -> bool:
        """Open with logging."""
        result = super().open()
        if result:
            self.state_changes.append(f"Door {self.door_id} opened to {self._state}")
        return result

    def close(self) -> bool:
        """Close with logging."""
        result = super().close()
        if result:
            self.state_changes.append(f"Door {self.door_id} closed to {self._state}")
        return result

    def get_state_history(self) -> List[str]:
        """Get history of state changes."""
        return self.state_changes.copy()
