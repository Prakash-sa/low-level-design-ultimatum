"""
ElevatorRequest.py - Data structure for elevator requests
Implements SOLID: Single Responsibility (request representation only)
"""

from dataclasses import dataclass
from typing import Optional
from Direction import Direction


@dataclass
class ElevatorRequest:
    """
    Represents a request to move the elevator to a specific floor.
    
    Design Pattern: Value Object
    - Immutable data structure representing a request
    - Can be easily compared, hashed, and stored in queues
    
    SOLID Principles:
    - Single Responsibility: Only represents a request, no behavior
    """

    floor: int
    direction: Direction
    priority: int = 0  # 0 = normal, higher = more important
    requested_at: Optional[float] = None  # Timestamp when requested

    def __hash__(self):
        """Make request hashable for deduplication."""
        return hash((self.floor, self.direction))

    def __eq__(self, other):
        """Compare requests."""
        if not isinstance(other, ElevatorRequest):
            return False
        return self.floor == other.floor and self.direction == other.direction

    def __lt__(self, other):
        """Support priority queue ordering."""
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority first
        return self.requested_at < other.requested_at if self.requested_at and other.requested_at else False

    def __str__(self) -> str:
        return f"Request(floor={self.floor}, dir={self.direction}, priority={self.priority})"

    def is_going_up(self) -> bool:
        """Check if request is for upward direction."""
        return self.direction == Direction.UP

    def is_going_down(self) -> bool:
        """Check if request is for downward direction."""
        return self.direction == Direction.DOWN

    @property
    def destination(self) -> int:
        """Get destination floor."""
        return self.floor
