"""
Direction.py - Enums for elevator system states
Implements SOLID: Single Responsibility (each enum has one purpose)
"""

from enum import Enum


class Direction(Enum):
    """
    Represents the direction of travel for an elevator or call.
    
    SOLID Principle Applied:
    - Single Responsibility: Only represents direction, nothing else
    """
    UP = 1
    DOWN = 2
    IDLE = 3

    def __str__(self):
        return self.name

    def opposite(self):
        """Get the opposite direction."""
        if self == Direction.UP:
            return Direction.DOWN
        elif self == Direction.DOWN:
            return Direction.UP
        return Direction.IDLE


class ElevatorState(Enum):
    """
    Represents the operational state of an elevator car.
    
    States:
    - IDLE: Not moving, waiting for requests
    - MOVING_UP: Currently moving upward
    - MOVING_DOWN: Currently moving downward
    - DOOR_OPEN: At a floor with door open for boarding/exiting
    - MAINTENANCE: Out of service for maintenance
    - EMERGENCY: Emergency stop activated
    
    SOLID Principle Applied:
    - Single Responsibility: Only defines elevator operational states
    - Liskov Substitution: All states are equivalent enum members
    """
    IDLE = 1
    MOVING_UP = 2
    MOVING_DOWN = 3
    DOOR_OPEN = 4
    MAINTENANCE = 5
    EMERGENCY = 6

    def __str__(self):
        return self.name

    def is_moving(self):
        """Check if elevator is in motion."""
        return self in (ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN)

    def can_accept_request(self):
        """Check if elevator can accept new requests in this state."""
        return self not in (ElevatorState.MAINTENANCE, ElevatorState.EMERGENCY)


class DoorState(Enum):
    """
    Represents the physical state of an elevator door.
    
    SOLID Principle Applied:
    - Single Responsibility: Only manages door state
    - Immutability: Enum prevents invalid state transitions at creation
    """
    CLOSED = 1
    OPEN = 2
    OPENING = 3
    CLOSING = 4

    def __str__(self):
        return self.name

    def is_accessible(self):
        """Check if passengers can enter/exit (door open or opening)."""
        return self in (DoorState.OPEN, DoorState.OPENING)
