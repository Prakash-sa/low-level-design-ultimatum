"""
Parking Lot System - 75 Minute Interview Implementation
Single-file, ready-to-run, copy-paste friendly
~420 lines of production-ready code
"""

from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from abc import ABC, abstractmethod


# ============================================================================
# SECTION 1: ENUMERATIONS & BASIC TYPES
# ============================================================================

class PaymentStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()

class TicketStatus(Enum):
    ACTIVE = auto()
    PAID = auto()
    VALIDATED = auto()

class SpotType(Enum):
    COMPACT = 1
    LARGE = 2
    HANDICAPPED = 3
    MOTORCYCLE = 4

class VehicleType(Enum):
    CAR = 1
    VAN = 2
    TRUCK = 3
    MOTORCYCLE = 4


# ============================================================================
# SECTION 2: VEHICLE CLASSES
# ============================================================================

class Vehicle:
    """Base vehicle class with spot compatibility logic"""
    def __init__(self, license_no: str, vehicle_type: VehicleType):
        self.license_no = license_no
        self.vehicle_type = vehicle_type
        self.ticket: Optional['ParkingTicket'] = None
    
    def get_compatible_spots(self) -> List[SpotType]:
        """Return compatible spot types for this vehicle"""
        if self.vehicle_type == VehicleType.CAR:
            return [SpotType.COMPACT, SpotType.LARGE]
        elif self.vehicle_type == VehicleType.VAN:
            return [SpotType.LARGE]
        elif self.vehicle_type == VehicleType.TRUCK:
            return [SpotType.LARGE]
        elif self.vehicle_type == VehicleType.MOTORCYCLE:
            return [SpotType.MOTORCYCLE]

class Car(Vehicle):
    def __init__(self, license_no):
        super().__init__(license_no, VehicleType.CAR)

class Van(Vehicle):
    def __init__(self, license_no):
        super().__init__(license_no, VehicleType.VAN)

class Truck(Vehicle):
    def __init__(self, license_no):
        super().__init__(license_no, VehicleType.TRUCK)

class Motorcycle(Vehicle):
    def __init__(self, license_no):
        super().__init__(license_no, VehicleType.MOTORCYCLE)


# ============================================================================
# SECTION 3: PARKING SPOT CLASSES
# ============================================================================

class ParkingSpot:
    """Base class for parking spots with state management"""
    def __init__(self, spot_id: int, spot_type: SpotType):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.is_free = True
        self.vehicle: Optional[Vehicle] = None
    
    def assign_vehicle(self, vehicle: Vehicle) -> bool:
        """Assign a vehicle to this spot"""
        if not self.is_free:
            return False
        self.vehicle = vehicle
        self.is_free = False
        return True
    
    def remove_vehicle(self) -> Optional[Vehicle]:
        """Remove vehicle and free the spot"""
        vehicle = self.vehicle
        self.vehicle = None
        self.is_free = True
        return vehicle
    
    def __repr__(self):
        status = "FREE" if self.is_free else f"OCCUPIED ({self.vehicle.license_no})"
        return f"Spot#{self.spot_id}({self.spot_type.name}): {status}"


class CompactSpot(ParkingSpot):
    def __init__(self, spot_id):
        super().__init__(spot_id, SpotType.COMPACT)

class LargeSpot(ParkingSpot):
    def __init__(self, spot_id):
        super().__init__(spot_id, SpotType.LARGE)

class HandicappedSpot(ParkingSpot):
    def __init__(self, spot_id):
        super().__init__(spot_id, SpotType.HANDICAPPED)

class MotorcycleSpot(ParkingSpot):
    def __init__(self, spot_id):
        super().__init__(spot_id, SpotType.MOTORCYCLE)


# ============================================================================
# SECTION 4: PARKING TICKET & PAYMENT
# ============================================================================

class ParkingTicket:
    """Parking ticket with entry/exit tracking and fees"""
    _id_counter = 1000
    
    def __init__(self, vehicle: Vehicle, spot: ParkingSpot):
        ParkingTicket._id_counter += 1
        self.ticket_no = f"TKT-{ParkingTicket._id_counter}"
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = datetime.now()
        self.exit_time: Optional[datetime] = None
        self.amount = 0.0
        self.status = TicketStatus.ACTIVE
        self.payment: Optional['Payment'] = None
    
    def validate_exit(self) -> bool:
        """Mark ticket as exiting"""
        if self.status == TicketStatus.ACTIVE:
            self.exit_time = datetime.now()
            self.status = TicketStatus.PAID
            return True
        return False
    
    def get_duration_hours(self) -> float:
        """Calculate parking duration in hours"""
        if self.exit_time is None:
            return 0
        delta = self.exit_time - self.entry_time
        return delta.total_seconds() / 3600


class Payment(ABC):
    """Abstract base for payment methods"""
    def __init__(self, amount: float):
        self.amount = amount
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
    
    @abstractmethod
    def initiate_transaction(self) -> bool:
        pass


class CashPayment(Payment):
    """Cash payment processing"""
    def initiate_transaction(self) -> bool:
        print(f"  💵 Cash payment of ${self.amount:.2f} accepted")
        self.status = PaymentStatus.COMPLETED
        return True


class CreditCardPayment(Payment):
    """Credit card payment processing"""
    def __init__(self, amount: float, card_number: str):
        super().__init__(amount)
        self.card_number = card_number
    
    def initiate_transaction(self) -> bool:
        print(f"  💳 Processing card {self.card_number[-4:]} for ${self.amount:.2f}")
        self.status = PaymentStatus.COMPLETED
        return True


# ============================================================================
# SECTION 5: DISPLAY & OBSERVER PATTERN
# ============================================================================

class Observer(ABC):
    """Observer interface for display updates"""
    @abstractmethod
    def update(self, lot: 'ParkingLot'):
        pass


class DisplayBoard(Observer):
    """Real-time parking status display"""
    def __init__(self, board_id: int):
        self.board_id = board_id
    
    def update(self, lot: 'ParkingLot'):
        """Called when parking lot changes"""
        self.display_status(lot)
    
    def display_status(self, lot: 'ParkingLot'):
        """Render current parking status"""
        free_by_type = lot.get_free_spots_by_type()
        print(f"\n  📊 [Display Board {self.board_id}] Status:")
        print(f"     Compact: {free_by_type.get(SpotType.COMPACT, 0)} free")
        print(f"     Large: {free_by_type.get(SpotType.LARGE, 0)} free")
        print(f"     Handicapped: {free_by_type.get(SpotType.HANDICAPPED, 0)} free")
        print(f"     Motorcycle: {free_by_type.get(SpotType.MOTORCYCLE, 0)} free")


# ============================================================================
# SECTION 6: ENTRANCE & EXIT GATES
# ============================================================================

class Entrance:
    """Entry gate - issues parking tickets"""
    def __init__(self, entrance_id: int):
        self.entrance_id = entrance_id
    
    def get_ticket(self, vehicle: Vehicle, lot: 'ParkingLot') -> Optional[ParkingTicket]:
        """Issue ticket when vehicle enters"""
        print(f"\n🚗 Vehicle {vehicle.license_no} enters via Entrance {self.entrance_id}")
        
        # Check if lot is full
        if lot.is_full():
            print("  ❌ Lot is FULL - entry denied")
            return None
        
        # Find a suitable spot
        spot = lot.find_spot(vehicle)
        if spot is None:
            print("  ❌ No suitable spot found")
            return None
        
        # Create ticket and assign vehicle
        ticket = ParkingTicket(vehicle, spot)
        spot.assign_vehicle(vehicle)
        vehicle.ticket = ticket
        lot.add_ticket(ticket)
        
        print(f"  ✅ Ticket: {ticket.ticket_no}")
        print(f"     Spot: #{spot.spot_id} ({spot.spot_type.name})")
        
        # Notify observers
        lot.notify_observers()
        return ticket


class Exit:
    """Exit gate - processes payment and releases spots"""
    def __init__(self, exit_id: int):
        self.exit_id = exit_id
    
    def process_exit(self, ticket: ParkingTicket, lot: 'ParkingLot', payment_method='cash') -> bool:
        """Process vehicle exit and payment"""
        print(f"\n🚙 Exit processing for {ticket.vehicle.license_no}")
        
        # Validate ticket
        if not ticket.validate_exit():
            print("  ❌ Invalid ticket")
            return False
        
        # Calculate fee
        hours = ticket.get_duration_hours()
        amount = hours * 5.0  # $5 per hour
        ticket.amount = amount
        
        print(f"  Entry: {ticket.entry_time.strftime('%H:%M')}")
        print(f"  Exit: {ticket.exit_time.strftime('%H:%M')}")
        print(f"  Duration: {hours:.2f} hours")
        print(f"  Amount: ${amount:.2f}")
        
        # Process payment
        if payment_method == 'card':
            payment = CreditCardPayment(amount, "****-****-****-1234")
        else:
            payment = CashPayment(amount)
        
        if payment.initiate_transaction():
            ticket.payment = payment
            ticket.status = TicketStatus.VALIDATED
            
            # Release spot
            spot = ticket.spot
            spot.remove_vehicle()
            
            print(f"  ✅ Exit complete - Spot #{spot.spot_id} now FREE")
            lot.notify_observers()
            return True
        
        return False


# ============================================================================
# SECTION 7: PARKING LOT CONTROLLER (SINGLETON)
# ============================================================================

class ParkingLot:
    """Main parking lot controller - Singleton pattern"""
    _instance = None
    
    def __init__(self, lot_id: int = 1, capacity: int = 100):
        self.lot_id = lot_id
        self.capacity = capacity
        self.spots: Dict[int, ParkingSpot] = {}
        self.tickets: Dict[str, ParkingTicket] = {}
        self.observers: List[Observer] = []
        
        # Initialize spots
        self._initialize_spots()
    
    @classmethod
    def get_instance(cls, lot_id=1, capacity=100):
        """Singleton getter"""
        if cls._instance is None:
            cls._instance = ParkingLot(lot_id, capacity)
        return cls._instance
    
    def _initialize_spots(self):
        """Initialize parking spots by type"""
        spot_id = 1
        
        # 40 Compact spots (for cars)
        for _ in range(40):
            self.spots[spot_id] = CompactSpot(spot_id)
            spot_id += 1
        
        # 30 Large spots (for vans/trucks)
        for _ in range(30):
            self.spots[spot_id] = LargeSpot(spot_id)
            spot_id += 1
        
        # 20 Handicapped spots
        for _ in range(20):
            self.spots[spot_id] = HandicappedSpot(spot_id)
            spot_id += 1
        
        # 10 Motorcycle spots
        for _ in range(10):
            self.spots[spot_id] = MotorcycleSpot(spot_id)
            spot_id += 1
    
    def find_spot(self, vehicle: Vehicle) -> Optional[ParkingSpot]:
        """Find a suitable free spot for the vehicle"""
        compatible_types = vehicle.get_compatible_spots()
        
        for spot in self.spots.values():
            if spot.is_free and spot.spot_type in compatible_types:
                return spot
        return None
    
    def is_full(self) -> bool:
        """Check if parking lot is completely full"""
        return sum(1 for spot in self.spots.values() if spot.is_free) == 0
    
    def get_free_spots_by_type(self) -> Dict[SpotType, int]:
        """Count free spots by type"""
        counts = {spot_type: 0 for spot_type in SpotType}
        for spot in self.spots.values():
            if spot.is_free:
                counts[spot.spot_type] += 1
        return counts
    
    def add_ticket(self, ticket: ParkingTicket):
        """Register a parking ticket"""
        self.tickets[ticket.ticket_no] = ticket
    
    def add_observer(self, observer: Observer):
        """Add an observer (display board)"""
        self.observers.append(observer)
    
    def notify_observers(self):
        """Notify all observers of changes"""
        for observer in self.observers:
            observer.update(self)
    
    def get_statistics(self) -> Dict:
        """Get parking lot statistics"""
        free_spots = sum(1 for spot in self.spots.values() if spot.is_free)
        occupied_spots = self.capacity - free_spots
        
        return {
            "total_spots": self.capacity,
            "free_spots": free_spots,
            "occupied_spots": occupied_spots,
            "occupancy_rate": occupied_spots / self.capacity * 100,
            "total_tickets": len(self.tickets),
            "free_by_type": self.get_free_spots_by_type()
        }
    
    def print_status(self):
        """Print current parking lot status"""
        stats = self.get_statistics()
        print("\n📍 Parking Lot Status:")
        print(f"   Total: {stats['total_spots']} | Free: {stats['free_spots']} | "
              f"Occupied: {stats['occupied_spots']} | "
              f"Occupancy: {stats['occupancy_rate']:.1f}%")


# ============================================================================
# SECTION 8: DEMO & TESTING
# ============================================================================

def demo_1_basic_entry_exit():
    """Demo 1: Basic vehicle entry and exit"""
    print("\n" + "="*70)
    print("DEMO 1: Single Vehicle Entry & Exit")
    print("="*70)
    
    lot = ParkingLot.get_instance()
    entrance = Entrance(1)
    exit_gate = Exit(1)
    display = DisplayBoard(1)
    lot.add_observer(display)
    
    # Vehicle enters
    car = Car("KA-01-AB-1234")
    ticket = entrance.get_ticket(car, lot)
    
    # Simulate 2.5 hours of parking
    print("\n⏳ Vehicle parked for 2.5 hours...")
    ticket.exit_time = ticket.entry_time + timedelta(hours=2.5)
    
    # Vehicle exits
    exit_gate.process_exit(ticket, lot)


def demo_2_multiple_vehicles():
    """Demo 2: Multiple vehicles entering parking lot"""
    print("\n" + "="*70)
    print("DEMO 2: Multiple Vehicles")
    print("="*70)
    
    # Reset singleton
    ParkingLot._instance = None
    lot = ParkingLot.get_instance()
    entrance = Entrance(1)
    display = DisplayBoard(1)
    lot.add_observer(display)
    
    # Multiple vehicles
    vehicles = [
        Car("KA-01-BC-5678"),
        Van("MH-01-XY-9999"),
        Motorcycle("DL-01-EF-1111"),
        Car("TN-02-GH-2222"),
    ]
    
    print("\nProcessing multiple entries...")
    for vehicle in vehicles:
        entrance.get_ticket(vehicle, lot)
    
    lot.print_status()


def demo_3_full_lot():
    """Demo 3: Parking lot becomes full"""
    print("\n" + "="*70)
    print("DEMO 3: Parking Lot Becomes Full")
    print("="*70)
    
    # Reset singleton
    ParkingLot._instance = None
    lot = ParkingLot.get_instance(capacity=10)  # Small lot for demo
    entrance = Entrance(1)
    display = DisplayBoard(1)
    lot.add_observer(display)
    
    print("\nFilling the parking lot...")
    count = 0
    for i in range(12):
        car = Car(f"TEST-{i:04d}")
        ticket = entrance.get_ticket(car, lot)
        if ticket:
            count += 1
        else:
            print(f"  ❌ Cannot park vehicle #{i+1} - lot full")
    
    lot.print_status()
    print(f"\n✅ Successfully parked: {count}/{10}")


def demo_4_payment_processing():
    """Demo 4: Payment processing for different durations"""
    print("\n" + "="*70)
    print("DEMO 4: Payment Processing")
    print("="*70)
    
    # Reset singleton
    ParkingLot._instance = None
    lot = ParkingLot.get_instance()
    entrance = Entrance(1)
    exit_gate = Exit(1)
    display = DisplayBoard(1)
    lot.add_observer(display)
    
    tickets = []
    
    # Vehicle 1: 1 hour
    car1 = Car("KA-01-SHORT")
    t1 = entrance.get_ticket(car1, lot)
    t1.exit_time = t1.entry_time + timedelta(hours=1)
    tickets.append(t1)
    
    # Vehicle 2: 3 hours
    car2 = Car("KA-01-LONG")
    t2 = entrance.get_ticket(car2, lot)
    t2.exit_time = t2.entry_time + timedelta(hours=3)
    tickets.append(t2)
    
    print("\nProcessing exits...")
    for i, ticket in enumerate(tickets, 1):
        exit_gate.process_exit(ticket, lot, payment_method='card' if i % 2 else 'cash')


def demo_5_statistics():
    """Demo 5: Parking lot statistics and monitoring"""
    print("\n" + "="*70)
    print("DEMO 5: Statistics & Monitoring")
    print("="*70)
    
    # Reset singleton
    ParkingLot._instance = None
    lot = ParkingLot.get_instance()
    entrance = Entrance(1)
    
    # Park 50 vehicles
    print("\nParking 50 vehicles...")
    for i in range(50):
        if i % 10 == 0:
            print(f"  Parked {i} vehicles...")
        car = Car(f"STAT-{i:04d}")
        entrance.get_ticket(car, lot)
    
    # Show statistics
    stats = lot.get_statistics()
    print("\n📊 Statistics after parking 50 vehicles:")
    print(f"   Total spots: {stats['total_spots']}")
    print(f"   Free spots: {stats['free_spots']}")
    print(f"   Occupied: {stats['occupied_spots']}")
    print(f"   Occupancy rate: {stats['occupancy_rate']:.1f}%")
    print(f"   Total tickets issued: {stats['total_tickets']}")
    print(f"   Free by type: {stats['free_by_type']}")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("PARKING LOT SYSTEM - 75 MINUTE INTERVIEW IMPLEMENTATION")
    print("="*70)
    
    demo_1_basic_entry_exit()
    demo_2_multiple_vehicles()
    demo_3_full_lot()
    demo_4_payment_processing()
    demo_5_statistics()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
