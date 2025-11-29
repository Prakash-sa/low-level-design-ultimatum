"""
main.py - Comprehensive demo scenarios for elevator system

This file demonstrates:
1. System initialization with singleton pattern
2. Basic hall calls and dispatching
3. Interior floor selection
4. Maintenance mode
5. Emergency stop
6. Display updates via observer pattern
7. Different dispatcher strategies
"""

from Direction import Direction
from ElevatorSystem import ElevatorSystem
from Dispatcher import (
    NearestIdleDispatcher,
    DirectionAwareDispatcher,
    LookAheadDispatcher,
    ScanDispatcher,
)
from Display import VerboseDisplay


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title):
    """Print formatted subheader."""
    print(f"\n→ {title}")
    print("-" * 70)


def scenario_1_basic_calls():
    """Scenario 1: Basic hall calls and dispatching."""
    print_header("SCENARIO 1: Basic Hall Calls & Dispatching")

    system = ElevatorSystem.get_instance(num_floors=10, num_cars=3)
    system.print_system_status()

    print_subheader("Passenger on Floor 2 calls elevator UP")
    car = system.call_elevator(floor=2, direction=Direction.UP)
    print(f"✓ Assigned: {car}")
    system.print_system_status()

    print_subheader("Passenger on Floor 8 calls elevator DOWN")
    car = system.call_elevator(floor=8, direction=Direction.DOWN)
    print(f"✓ Assigned: {car}")
    system.print_system_status()

    print_subheader("Passenger on Floor 5 calls elevator UP")
    car = system.call_elevator(floor=5, direction=Direction.UP)
    print(f"✓ Assigned: {car}")
    system.print_system_status()


def scenario_2_movement_and_stops():
    """Scenario 2: Elevator movement and floor stops."""
    print_header("SCENARIO 2: Elevator Movement & Floor Stops")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=2)

    print_subheader("Call elevator from floor 2 (UP)")
    car = system.call_elevator(floor=2, direction=Direction.UP)
    print(f"✓ Car {car.get_id()} assigned, current floor: {car.get_current_floor()}")

    print_subheader("Simulate movement (car moves up)")
    for i in range(3):
        system.move_car_one_floor(0)
        car = system.building.get_car(0)
        print(
            f"  Move {i+1}: Floor {car.get_current_floor()}, "
            f"State: {car.get_state().name}, "
            f"Queue size: {car.get_request_queue_size()}"
        )

    print_subheader("Passenger boards at floor 2")
    display = system.get_display_for_car(0)
    if display:
        print(display.render())


def scenario_3_interior_selection():
    """Scenario 3: Interior floor selection inside car."""
    print_header("SCENARIO 3: Interior Floor Selection")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=1)

    print_subheader("Passenger calls from floor 2 (UP)")
    car = system.call_elevator(floor=2, direction=Direction.UP)
    print(f"✓ Car {car.get_id()} assigned")

    print_subheader("Passenger boards, selects floor 7 inside car")
    system.register_floor_request(car_id=0, floor=7)
    print("✓ Floor 7 added to queue")
    print(f"  Queue size: {car.get_request_queue_size()}")
    print(f"  Requests: {[r.floor for r in car._request_queue]}")


def scenario_4_maintenance_mode():
    """Scenario 4: Maintenance mode."""
    print_header("SCENARIO 4: Maintenance Mode")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=3)

    print_subheader("Call from floor 5 (UP)")
    car = system.call_elevator(floor=5, direction=Direction.UP)
    car_id = car.get_id()
    print(f"✓ Car {car_id} assigned, state: {car.get_state().name}")

    print_subheader(f"Put car {car_id} into maintenance")
    system.put_elevator_in_maintenance(car_id)
    car = system.building.get_car(car_id)
    print(f"✓ Car {car_id} state: {car.get_state().name}")
    print(f"  Can accept requests: {car.can_accept_request()}")
    print(f"  Queue cleared: {car.get_request_queue_size() == 0}")

    print_subheader("Next call should go to different car")
    car = system.call_elevator(floor=5, direction=Direction.UP)
    print(f"✓ Car {car.get_id()} assigned (different from car {car_id})")

    print_subheader(f"Release car {car_id} from maintenance")
    system.release_elevator_from_maintenance(car_id)
    car = system.building.get_car(car_id)
    print(f"✓ Car {car_id} state: {car.get_state().name}")
    print(f"  Can accept requests: {car.can_accept_request()}")


def scenario_5_emergency_stop():
    """Scenario 5: Emergency stop."""
    print_header("SCENARIO 5: Emergency Stop")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=1)

    print_subheader("Call from floor 3, passenger boards and selects floor 8")
    system.call_elevator(floor=3, direction=Direction.UP)
    system.register_floor_request(car_id=0, floor=8)

    print_subheader("Car is moving...")
    for _ in range(2):
        system.move_car_one_floor(0)

    car = system.building.get_car(0)
    print(f"  Current floor: {car.get_current_floor()}, state: {car.get_state().name}")

    print_subheader("Emergency button pressed!")
    system.emergency_stop(car_id=0)
    car = system.building.get_car(0)
    print(f"✓ Car emergency state: {car.get_state().name}")
    print(f"  Door state: {car.door.get_state().name}")
    print(f"  Queue cleared: {car.get_request_queue_size() == 0}")
    print(f"  Can accept requests: {car.can_accept_request()}")


def scenario_6_load_management():
    """Scenario 6: Load and overload management."""
    print_header("SCENARIO 6: Load & Overload Management")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=1)

    car = system.building.get_car(0)
    capacity = car.capacity

    print_subheader(f"Car capacity: {capacity} kg")

    print_subheader("Add 200 kg passenger")
    car.add_load(200)
    print(f"✓ Load: {car.get_current_load()} kg ({car.get_load_percentage()}%)")
    print(f"  Can accept requests: {car.can_accept_request()}")

    print_subheader("Add 700 kg more passengers")
    car.add_load(700)
    print(f"✓ Load: {car.get_current_load()} kg ({car.get_load_percentage()}%)")
    print(f"  Is overloaded: {car.is_overloaded()}")
    print(f"  Can accept requests: {car.can_accept_request()}")

    print_subheader("Try to add 150 kg more (should fail)")
    result = car.add_load(150)
    print(f"✓ Result: {result} (rejected due to overload)")

    print_subheader("Passengers exit (remove 500 kg)")
    car.remove_load(500)
    print(f"✓ Load: {car.get_current_load()} kg ({car.get_load_percentage()}%)")
    print(f"  Is overloaded: {car.is_overloaded()}")
    print(f"  Can accept requests: {car.can_accept_request()}")


def scenario_7_dispatcher_strategies():
    """Scenario 7: Different dispatcher strategies."""
    print_header("SCENARIO 7: Dispatcher Strategies Comparison")

    strategies = [
        ("Nearest Idle", NearestIdleDispatcher()),
        ("Direction Aware", DirectionAwareDispatcher()),
        ("Look Ahead", LookAheadDispatcher()),
        ("SCAN", ScanDispatcher()),
    ]

    for strategy_name, strategy in strategies:
        print_subheader(f"Testing {strategy_name} Dispatcher")

        ElevatorSystem.reset_instance()
        system = ElevatorSystem.get_instance(num_floors=10, num_cars=3)
        system.set_dispatcher(strategy)

        # Make several calls
        calls = [(2, Direction.UP), (5, Direction.DOWN), (8, Direction.UP)]

        for floor, direction in calls:
            car = system.call_elevator(floor=floor, direction=direction)
            print(f"  Floor {floor} ({direction.name:4s}) → Car {car.get_id()}")


def scenario_8_observer_pattern():
    """Scenario 8: Observer pattern - Display updates."""
    print_header("SCENARIO 8: Observer Pattern - Display Updates")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=1)

    car = system.building.get_car(0)
    display = VerboseDisplay(display_id=0)
    car.subscribe(display)

    print_subheader("Initial state")
    print(display.render())

    print_subheader("Register request to floor 5")
    car.register_request(floor=5, direction=Direction.UP)
    print(display.render())

    print_subheader("Simulate movement (3 steps)")
    for _ in range(3):
        car.move_one_floor()
        print(display.render())

    print_subheader("Depart floor")
    car.depart_floor()
    print(display.render())


def scenario_9_complete_workflow():
    """Scenario 9: Complete workflow with multiple interactions."""
    print_header("SCENARIO 9: Complete Workflow")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=10, num_cars=2)

    print_subheader("Step 1: Setup display for car 0")
    car0 = system.building.get_car(0)
    display0 = VerboseDisplay(display_id=0)
    car0.subscribe(display0)

    print_subheader("Step 2: Multiple calls")
    print("  Floor 2 UP")
    system.call_elevator(floor=2, direction=Direction.UP)

    print("  Floor 8 DOWN")
    system.call_elevator(floor=8, direction=Direction.DOWN)

    print("  Floor 5 UP")
    system.call_elevator(floor=5, direction=Direction.UP)

    print_subheader("Step 3: System status")
    print(f"  Total pending requests: {system.get_total_pending_requests()}")
    print(f"  Idle cars: {system.get_idle_cars_count()}")
    print(f"  Moving cars: {system.get_moving_cars_count()}")

    print_subheader("Step 4: Car 0 status")
    car0_status = system.get_car_status(0)
    print(f"  Current floor: {car0_status['current_floor']}")
    print(f"  State: {car0_status['state']}")
    print(f"  Pending requests: {car0_status['pending_requests']}")


def scenario_10_system_statistics():
    """Scenario 10: System statistics and monitoring."""
    print_header("SCENARIO 10: System Statistics & Monitoring")

    ElevatorSystem.reset_instance()
    system = ElevatorSystem.get_instance(num_floors=15, num_cars=4)

    # Make various calls
    for floor in [3, 7, 2, 9, 5, 12]:
        direction = Direction.UP if floor < 7 else Direction.DOWN
        system.call_elevator(floor=floor, direction=direction)

    print_subheader("System Overview")
    print(system)

    print_subheader("Statistics")
    print("  Total floors: 15")
    print("  Total cars: 4")
    print(f"  Total pending requests: {system.get_total_pending_requests()}")
    print(f"  Idle cars: {system.get_idle_cars_count()}")
    print(f"  Moving cars: {system.get_moving_cars_count()}")
    print(f"  Maintenance cars: {system.get_maintenance_cars_count()}")

    print_subheader("Individual Car Status")
    for car_status in system.get_all_cars_status():
        print(
            f"  Car {car_status['car_id']}: "
            f"Floor {car_status['current_floor']}, "
            f"{car_status['state']}, "
            f"Queue: {car_status['pending_requests']}"
        )


def main():
    """Run all demo scenarios."""
    print("\n" + "=" * 70)
    print("  ELEVATOR SYSTEM - COMPREHENSIVE DEMO")
    print("  Following SOLID Principles & Design Patterns")
    print("=" * 70)

    scenarios = [
        ("Basic Hall Calls & Dispatching", scenario_1_basic_calls),
        ("Movement & Floor Stops", scenario_2_movement_and_stops),
        ("Interior Floor Selection", scenario_3_interior_selection),
        ("Maintenance Mode", scenario_4_maintenance_mode),
        ("Emergency Stop", scenario_5_emergency_stop),
        ("Load & Overload Management", scenario_6_load_management),
        ("Dispatcher Strategies", scenario_7_dispatcher_strategies),
        ("Observer Pattern", scenario_8_observer_pattern),
        ("Complete Workflow", scenario_9_complete_workflow),
        ("System Statistics", scenario_10_system_statistics),
    ]

    print("\nAvailable Scenarios:")
    for i, (name, _) in enumerate(scenarios, 1):
        print(f"  {i}. {name}")

    print("\nRunning all scenarios...\n")

    for i, (name, scenario_func) in enumerate(scenarios, 1):
        try:
            scenario_func()
            print(f"\n✓ Scenario {i} completed successfully")
        except Exception as e:
            print(f"\n✗ Scenario {i} failed: {e}")
            import traceback
            traceback.print_exc()

    print_header("ALL SCENARIOS COMPLETED")
    print("\nKey Takeaways:")
    print("  ✓ Singleton pattern ensures single system instance")
    print("  ✓ Strategy pattern allows pluggable dispatchers")
    print("  ✓ Observer pattern decouples displays from cars")
    print("  ✓ State enums ensure type-safe state management")
    print("  ✓ Command pattern encapsulates button presses")
    print("  ✓ SOLID principles maintain clean architecture")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
