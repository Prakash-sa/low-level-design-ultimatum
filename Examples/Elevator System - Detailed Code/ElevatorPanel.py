"""
ElevatorPanel.py - Elevator panels (interior and hall)
Implements SOLID: Single Responsibility (panel management only)
                  Interface Segregation (minimal panel interfaces)
"""

from typing import List, Callable, Optional
from Button import Button, ElevatorButton, HallButton, DoorOpenButton, DoorCloseButton, EmergencyButton, AlarmButton
from Direction import Direction


class BasePanel:
    """
    Base class for all panels.
    
    SOLID: Single Responsibility - manages buttons only
    """

    def __init__(self, panel_id: int = 0):
        """Initialize base panel."""
        self.panel_id = panel_id
        self.buttons: List[Button] = []

    def add_button(self, button: Button) -> None:
        """Add button to panel."""
        if button not in self.buttons:
            self.buttons.append(button)

    def get_buttons(self) -> List[Button]:
        """Get all buttons."""
        return self.buttons.copy()

    def get_pressed_buttons(self) -> List[Button]:
        """Get all currently pressed buttons."""
        return [btn for btn in self.buttons if btn.is_pressed()]

    def press_button(self, button_index: int) -> bool:
        """
        Press button at index.
        
        Args:
            button_index: Index of button to press
            
        Returns:
            True if button was pressed successfully
        """
        if 0 <= button_index < len(self.buttons):
            self.buttons[button_index].press()
            return True
        return False

    def release_all(self) -> None:
        """Release all buttons."""
        for button in self.buttons:
            button.release()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.panel_id}, buttons={len(self.buttons)})"


class ElevatorPanel(BasePanel):
    """
    Panel inside an elevator car with floor buttons and controls.
    
    Buttons:
    - Floor buttons (0 to N-1): Select destination floor
    - Open door button: Manual door open
    - Close door button: Manual door close
    - Emergency button: Emergency stop
    - Alarm button: Sound alarm
    
    SOLID: Single Responsibility - manages interior car controls only
    """

    def __init__(self, car_id: int, num_floors: int):
        """
        Initialize elevator panel.
        
        Args:
            car_id: ID of elevator this panel belongs to
            num_floors: Number of floors in building
        """
        super().__init__(panel_id=car_id)
        self.car_id = car_id
        self.num_floors = num_floors

        # Floor buttons
        self.floor_buttons: List[ElevatorButton] = []
        for floor in range(num_floors):
            btn = ElevatorButton(floor)
            self.floor_buttons.append(btn)
            self.add_button(btn)

        # Control buttons
        self.open_button = DoorOpenButton()
        self.close_button = DoorCloseButton()
        self.emergency_button = EmergencyButton()
        self.alarm_button = AlarmButton()

        self.add_button(self.open_button)
        self.add_button(self.close_button)
        self.add_button(self.emergency_button)
        self.add_button(self.alarm_button)

    def press_floor_button(self, floor: int) -> bool:
        """
        Press button for specific floor.
        
        Args:
            floor: Floor number (0 to num_floors-1)
            
        Returns:
            True if pressed successfully
        """
        if 0 <= floor < len(self.floor_buttons):
            self.floor_buttons[floor].press()
            return True
        return False

    def get_selected_floors(self) -> List[int]:
        """Get list of currently selected floors."""
        return [btn.get_destination_floor() for btn in self.floor_buttons if btn.is_pressed()]

    def press_emergency(self) -> bool:
        """Press emergency button."""
        self.emergency_button.press()
        return self.emergency_button.is_pressed()

    def press_open_door(self) -> bool:
        """Press open door button."""
        self.open_button.press()
        return self.open_button.is_pressed()

    def press_close_door(self) -> bool:
        """Press close door button."""
        self.close_button.press()
        return self.close_button.is_pressed()

    def press_alarm(self) -> bool:
        """Press alarm button."""
        self.alarm_button.press()
        return self.alarm_button.is_pressed()

    def register_floor_request_callback(self, floor: int, callback: Callable) -> None:
        """
        Register callback for floor button press.
        
        Args:
            floor: Floor number
            callback: Function to call when button pressed
        """
        if 0 <= floor < len(self.floor_buttons):
            self.floor_buttons[floor]._action = callback

    def __str__(self) -> str:
        return f"ElevatorPanel(car_id={self.car_id}, floors={self.num_floors})"


class HallPanel(BasePanel):
    """
    Panel on a floor in the hallway for calling elevator.
    
    Buttons:
    - Up button: Call elevator going UP (if not top floor)
    - Down button: Call elevator going DOWN (if not ground floor)
    
    SOLID: Single Responsibility - manages hall floor controls only
    """

    def __init__(self, floor: int, num_floors: int):
        """
        Initialize hall panel.
        
        Args:
            floor: Which floor this panel is on
            num_floors: Total floors in building
        """
        super().__init__(panel_id=floor)
        self.floor = floor
        self.num_floors = num_floors

        self.up_button: Optional[HallButton] = None
        self.down_button: Optional[HallButton] = None

        # Create appropriate buttons based on floor location
        if floor < num_floors - 1:  # Not top floor
            self.up_button = HallButton(floor, Direction.UP)
            self.add_button(self.up_button)

        if floor > 0:  # Not ground floor
            self.down_button = HallButton(floor, Direction.DOWN)
            self.add_button(self.down_button)

    def press_up(self) -> bool:
        """
        Press up button.
        
        Returns:
            True if button exists and was pressed
        """
        if self.up_button:
            self.up_button.press()
            return True
        return False

    def press_down(self) -> bool:
        """
        Press down button.
        
        Returns:
            True if button exists and was pressed
        """
        if self.down_button:
            self.down_button.press()
            return True
        return False

    def register_up_callback(self, callback: Callable) -> None:
        """Register callback for up button."""
        if self.up_button:
            self.up_button._action = callback

    def register_down_callback(self, callback: Callable) -> None:
        """Register callback for down button."""
        if self.down_button:
            self.down_button._action = callback

    def has_up_button(self) -> bool:
        """Check if this floor has up button."""
        return self.up_button is not None

    def has_down_button(self) -> bool:
        """Check if this floor has down button."""
        return self.down_button is not None

    def get_call_direction(self) -> Optional[Direction]:
        """Get direction if either button is pressed."""
        if self.up_button and self.up_button.is_pressed():
            return Direction.UP
        if self.down_button and self.down_button.is_pressed():
            return Direction.DOWN
        return None

    def __str__(self) -> str:
        buttons = []
        if self.up_button:
            buttons.append("UP")
        if self.down_button:
            buttons.append("DOWN")
        return f"HallPanel(floor={self.floor}, buttons={buttons})"


class Floor:
    """
    Represents a floor with a hall panel.
    
    SOLID: Single Responsibility - manages floor-level controls
    """

    def __init__(self, floor_number: int, num_floors: int):
        """
        Initialize floor.
        
        Args:
            floor_number: Floor number (0 to num_floors-1)
            num_floors: Total floors in building
        """
        self.floor_number = floor_number
        self.hall_panel = HallPanel(floor_number, num_floors)

    def call_up(self, callback: Callable) -> bool:
        """
        Call elevator to go up.
        
        Args:
            callback: Function to call when button pressed
            
        Returns:
            True if successful
        """
        if self.hall_panel.has_up_button():
            self.hall_panel.register_up_callback(callback)
            self.hall_panel.press_up()
            return True
        return False

    def call_down(self, callback: Callable) -> bool:
        """
        Call elevator to go down.
        
        Args:
            callback: Function to call when button pressed
            
        Returns:
            True if successful
        """
        if self.hall_panel.has_down_button():
            self.hall_panel.register_down_callback(callback)
            self.hall_panel.press_down()
            return True
        return False

    def get_panel(self) -> HallPanel:
        """Get hall panel."""
        return self.hall_panel

    def __str__(self) -> str:
        return f"Floor({self.floor_number})"
