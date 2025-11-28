# Parking Lot System - 75 Minute Interview Guide

## Timeline Overview

```
┌─ 0-5 min   ┐ Problem Clarification
├─ 5-15 min  ┤ System Design & Architecture
├─ 15-65 min ┤ Implementation (5 phases)
└─ 65-75 min ┘ Testing & Discussion
```

---

## Phase 0: Problem Clarification (5 minutes)

### Questions to Ask
1. **Scope**: How many parking spots? (assume 100)
2. **Vehicle types**: Car, motorcycle, etc.? (assume 4: car, van, truck, motorcycle)
3. **Spot types**: Compact, large, handicapped? (assume 4)
4. **Parking fee**: Fixed rate or hourly? (assume hourly: $5/hour)
5. **Payment methods**: Cash, card, both? (assume both)
6. **Multi-lot**: Single lot or chain? (assume single)

### Good Answer
"I'll design a single parking lot system with:
- Up to 100 parking spots (4 types)
- 4 vehicle types
- Hourly billing ($5/hour)
- Both cash and card payment
- Real-time display board
- Singleton pattern for single instance"

---

## Phase 1: System Design (10 minutes, 0 lines of code)

### Architecture Sketch (Draw on whiteboard)

```
                         PARKING LOT
                        (Singleton)
                             │
            ┌────────────────┼────────────────┐
            │                │                │
        ┌───▼────┐       ┌──▼────┐      ┌───▼────┐
        │Entrance│       │ Spots │      │Display │
        │        │       │ Mgmt  │      │ Board  │
        └────┬───┘       └──┬────┘      └───┬────┘
             │              │               │
        Issue Ticket    Spot Finder    Real-time update
        Find Spot       Availability
```

### Key Classes (List on board)

```
Vehicle
  ├─ Car
  ├─ Van
  ├─ Truck
  └─ Motorcycle

ParkingSpot
  ├─ Compact
  ├─ Large
  ├─ Handicapped
  └─ MotorcycleSpot

ParkingLot (Singleton)
  ├─ spots: dict[int, ParkingSpot]
  ├─ tickets: dict[str, ParkingTicket]
  ├─ displays: list[DisplayBoard]

ParkingTicket
  ├─ entry_time
  ├─ exit_time
  ├─ amount
  └─ status

Payment
  ├─ Cash
  └─ CreditCard

DisplayBoard (Observer)
  └─ update()
```

### Design Patterns to Mention
1. **Singleton** - ParkingLot
2. **Strategy** - SpotFinder, PricingStrategy
3. **Observer** - DisplayBoard watches lot changes
4. **Factory** - VehicleFactory, SpotFactory
5. **State** - Spot states (FREE/OCCUPIED)

---

## Phase 2: Enumerations & Basic Classes (10 minutes, ~100 lines)

### Step 1: Enumerations (~40 lines)
```python
from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict, List

# Enumerations
class PaymentStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()

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
```

### Step 2: Vehicle Classes (~30 lines)
```python
# Base Vehicle
class Vehicle:
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

# Subclasses
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
```

### Step 3: Parking Spot Classes (~30 lines)
```python
# Base ParkingSpot
class ParkingSpot:
    def __init__(self, spot_id: int, spot_type: SpotType):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.is_free = True
        self.vehicle: Optional[Vehicle] = None
    
    def assign_vehicle(self, vehicle: Vehicle) -> bool:
        if not self.is_free:
            return False
        self.vehicle = vehicle
        self.is_free = False
        return True
    
    def remove_vehicle(self) -> Optional[Vehicle]:
        vehicle = self.vehicle
        self.vehicle = None
        self.is_free = True
        return vehicle

# Subclasses (minimal, just for documentation)
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
```

**Time so far: 10 minutes, 100 lines written**

---

## Phase 3: Ticket & Payment System (10 minutes, ~80 lines)

### Step 1: Parking Ticket (~40 lines)
```python
class ParkingTicket:
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
        """Validate when vehicle exits"""
        if self.status == TicketStatus.ACTIVE:
            self.exit_time = datetime.now()
            self.status = TicketStatus.PAID
            return True
        return False
    
    def get_duration_hours(self) -> float:
        if self.exit_time is None:
            return 0
        delta = self.exit_time - self.entry_time
        return delta.total_seconds() / 3600
```

### Step 2: Payment System (~40 lines)
```python
from abc import ABC, abstractmethod

class Payment(ABC):
    def __init__(self, amount: float):
        self.amount = amount
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
    
    @abstractmethod
    def initiate_transaction(self) -> bool:
        pass

class CashPayment(Payment):
    def __init__(self, amount: float):
        super().__init__(amount)
    
    def initiate_transaction(self) -> bool:
        print(f"💵 Cash payment of ${self.amount:.2f} accepted")
        self.status = PaymentStatus.COMPLETED
        return True

class CreditCardPayment(Payment):
    def __init__(self, amount: float, card_number: str):
        super().__init__(amount)
        self.card_number = card_number
    
    def initiate_transaction(self) -> bool:
        # Simulate card processing
        print(f"💳 Processing card {self.card_number[-4:]} for ${self.amount:.2f}")
        self.status = PaymentStatus.COMPLETED
        return True
```

**Time so far: 20 minutes, ~180 lines written**

---

## Phase 4: Parking Lot & Entrance/Exit (15 minutes, ~140 lines)

### Step 1: Display Board (Observer) (~30 lines)
```python
from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, lot: 'ParkingLot'):
        pass

class DisplayBoard(Observer):
    def __init__(self, board_id: int):
        self.board_id = board_id
    
    def update(self, lot: 'ParkingLot'):
        """Called when lot changes"""
        self.display_status(lot)
    
    def display_status(self, lot: 'ParkingLot'):
        print(f"\n📊 [Display Board {self.board_id}] Parking Status:")
        free_by_type = lot.get_free_spots_by_type()
        print(f"   Compact: {free_by_type.get(SpotType.COMPACT, 0)} free")
        print(f"   Large: {free_by_type.get(SpotType.LARGE, 0)} free")
        print(f"   Handicapped: {free_by_type.get(SpotType.HANDICAPPED, 0)} free")
        print(f"   Motorcycle: {free_by_type.get(SpotType.MOTORCYCLE, 0)} free")
```

### Step 2: Entrance Gate (~40 lines)
```python
class Entrance:
    def __init__(self, entrance_id: int):
        self.entrance_id = entrance_id
    
    def get_ticket(self, vehicle: Vehicle, lot: 'ParkingLot') -> Optional[ParkingTicket]:
        """Issue ticket when vehicle enters"""
        print(f"\n🚗 Vehicle {vehicle.license_no} enters via Entrance {self.entrance_id}")
        
        # Check if lot is full
        if lot.is_full():
            print("❌ Parking lot is FULL. Entry denied.")
            return None
        
        # Find a spot
        spot = lot.find_spot(vehicle)
        if spot is None:
            print("❌ No suitable spot found")
            return None
        
        # Create ticket and assign vehicle
        ticket = ParkingTicket(vehicle, spot)
        spot.assign_vehicle(vehicle)
        vehicle.ticket = ticket
        lot.add_ticket(ticket)
        
        print(f"✅ Ticket issued: {ticket.ticket_no}")
        print(f"   Spot: {spot.spot_id} (Type: {spot.spot_type.name})")
        
        # Notify observers
        lot.notify_observers()
        
        return ticket
```

### Step 3: Exit Gate (~40 lines)
```python
class Exit:
    def __init__(self, exit_id: int):
        self.exit_id = exit_id
    
    def process_exit(self, ticket: ParkingTicket, lot: 'ParkingLot') -> bool:
        """Process vehicle exit and payment"""
        print(f"\n🚙 Processing exit for {ticket.vehicle.license_no}")
        
        # Validate ticket
        if not ticket.validate_exit():
            print("❌ Invalid ticket")
            return False
        
        # Calculate fee
        hours = ticket.get_duration_hours()
        amount = hours * 5.0  # $5 per hour
        ticket.amount = amount
        
        print(f"   Entry: {ticket.entry_time.strftime('%H:%M')}")
        print(f"   Exit: {ticket.exit_time.strftime('%H:%M')}")
        print(f"   Duration: {hours:.2f} hours")
        print(f"   Amount Due: ${amount:.2f}")
        
        # Process payment
        payment = CashPayment(amount)
        if payment.initiate_transaction():
            ticket.payment = payment
            ticket.status = TicketStatus.VALIDATED
            
            # Release spot
            spot = ticket.spot
            spot.remove_vehicle()
            
            print(f"✅ Exit confirmed. Spot {spot.spot_id} is now FREE")
            lot.notify_observers()
            return True
        
        return False
```

**Time so far: 35 minutes, ~320 lines written**

---

## Phase 5: Parking Lot Controller (15 minutes, ~100 lines)

### Complete ParkingLot Class (~100 lines)
```python
class ParkingLot:
    _instance = None
    
    def __init__(self, lot_id: int, capacity: int):
        self.lot_id = lot_id
        self.capacity = capacity
        self.spots: Dict[int, ParkingSpot] = {}
        self.tickets: Dict[str, ParkingTicket] = {}
        self.observers: List[Observer] = []
        
        # Initialize spots
        self._initialize_spots()
    
    @classmethod
    def get_instance(cls, lot_id=1, capacity=100):
        if cls._instance is None:
            cls._instance = ParkingLot(lot_id, capacity)
        return cls._instance
    
    def _initialize_spots(self):
        """Initialize with different spot types"""
        spot_id = 1
        # 40 Compact spots
        for i in range(40):
            self.spots[spot_id] = CompactSpot(spot_id)
            spot_id += 1
        # 30 Large spots
        for i in range(30):
            self.spots[spot_id] = LargeSpot(spot_id)
            spot_id += 1
        # 20 Handicapped spots
        for i in range(20):
            self.spots[spot_id] = HandicappedSpot(spot_id)
            spot_id += 1
        # 10 Motorcycle spots
        for i in range(10):
            self.spots[spot_id] = MotorcycleSpot(spot_id)
            spot_id += 1
    
    def find_spot(self, vehicle: Vehicle) -> Optional[ParkingSpot]:
        """Find a suitable spot for the vehicle"""
        compatible_types = vehicle.get_compatible_spots()
        
        for spot in self.spots.values():
            if spot.is_free and spot.spot_type in compatible_types:
                return spot
        return None
    
    def is_full(self) -> bool:
        """Check if parking lot is full"""
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
    
    def get_statistics(self):
        """Return parking lot statistics"""
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
        """Print current status"""
        stats = self.get_statistics()
        print(f"\n📍 Parking Lot Status:")
        print(f"   Total Spots: {stats['total_spots']}")
        print(f"   Free: {stats['free_spots']}, Occupied: {stats['occupied_spots']}")
        print(f"   Occupancy: {stats['occupancy_rate']:.1f}%")
```

**Time so far: 50 minutes, ~420 lines written**

---

## Phase 6: Demo & Testing (15 minutes, ~80 lines)

### Complete Main Demo
```python
def main():
    print("=" * 60)
    print("PARKING LOT SYSTEM - 75 MINUTE INTERVIEW")
    print("=" * 60)
    
    # Initialize system
    lot = ParkingLot.get_instance(1, 100)
    entrance = Entrance(1)
    exit_gate = Exit(1)
    display = DisplayBoard(1)
    lot.add_observer(display)
    
    # DEMO 1: Basic entry and exit
    print("\n" + "="*60)
    print("DEMO 1: Single vehicle entry and exit")
    print("="*60)
    car1 = Car("KA-01-AB-1234")
    ticket1 = entrance.get_ticket(car1, lot)
    lot.print_status()
    
    # Simulate parking time
    print("\n⏳ Vehicle parked for 2.5 hours...")
    import time
    ticket1.exit_time = datetime.now()
    ticket1.entry_time = ticket1.exit_time - __import__('datetime').timedelta(hours=2.5)
    
    exit_gate.process_exit(ticket1, lot)
    lot.print_status()
    
    # DEMO 2: Multiple vehicles
    print("\n" + "="*60)
    print("DEMO 2: Multiple vehicles entering")
    print("="*60)
    
    vehicles = [
        Car("KA-01-BC-5678"),
        Van("MH-01-XY-9999"),
        Motorcycle("DL-01-EF-1111"),
    ]
    
    tickets = []
    for vehicle in vehicles:
        ticket = entrance.get_ticket(vehicle, lot)
        if ticket:
            tickets.append(ticket)
    
    lot.print_status()
    
    # DEMO 3: Vehicle exit
    print("\n" + "="*60)
    print("DEMO 3: Vehicle exit and fee payment")
    print("="*60)
    
    if tickets:
        test_ticket = tickets[0]
        test_ticket.exit_time = datetime.now()
        test_ticket.entry_time = test_ticket.exit_time - __import__('datetime').timedelta(hours=1.5)
        exit_gate.process_exit(test_ticket, lot)
    
    lot.print_status()
    
    # DEMO 4: Lot near full
    print("\n" + "="*60)
    print("DEMO 4: Parking lot becomes full")
    print("="*60)
    
    # Add many vehicles
    for i in range(95):
        v = Car(f"TEST-{i}")
        entrance.get_ticket(v, lot)
    
    lot.print_status()
    
    # Try to add one more
    print("\nAttempting to park another vehicle...")
    full_car = Car("FULL-TEST")
    result = entrance.get_ticket(full_car, lot)
    
    # DEMO 5: Statistics
    print("\n" + "="*60)
    print("DEMO 5: System Statistics")
    print("="*60)
    stats = lot.get_statistics()
    print(f"Total Tickets Issued: {stats['total_tickets']}")
    print(f"Current Occupancy: {stats['occupancy_rate']:.1f}%")
    print(f"Free Spots by Type: {stats['free_by_type']}")

if __name__ == "__main__":
    main()
```

**Total time: 65 minutes, ~500 lines written**

---

## Final 10 Minutes: Testing & Discussion (65-75 min)

### Run Demos (3-4 minutes)
```bash
python3 parking_lot_system.py
```

### Expected Output
```
============================================================
PARKING LOT SYSTEM - 75 MINUTE INTERVIEW
============================================================

============================================================
DEMO 1: Single vehicle entry and exit
============================================================

🚗 Vehicle KA-01-AB-1234 enters via Entrance 1
✅ Ticket issued: TKT-1001
   Spot: 1 (Type: COMPACT)

📊 [Display Board 1] Parking Status:
   Compact: 39 free
   Large: 30 free
   Handicapped: 20 free
   Motorcycle: 10 free

⏳ Vehicle parked for 2.5 hours...

🚙 Processing exit for KA-01-AB-1234
   Entry: 14:30
   Exit: 17:00
   Duration: 2.50 hours
   Amount Due: $12.50
💵 Cash payment of $12.50 accepted
✅ Exit confirmed. Spot 1 is now FREE

📍 Parking Lot Status:
   Total Spots: 100
   Free: 100, Occupied: 0
   Occupancy: 0.0%
```

### Discussion Points (5-6 minutes)

**Interviewer might ask:**

**Q1**: "What patterns did you use?"
**A1**: "I used 4 key patterns:
- **Singleton**: ParkingLot ensures single instance
- **Observer**: DisplayBoard gets notified of changes
- **Strategy**: Can swap spot-finding algorithms
- **Factory**: Vehicle/Spot creation (implicit in initialization)"

**Q2**: "How would you handle concurrency?"
**A2**: "I'd add threading locks:
```python
with lock:
    if spot.is_free:
        spot.assign_vehicle(vehicle)
```
This prevents race conditions on spot assignment."

**Q3**: "What about dynamic pricing?"
**A3**: "Create a PricingStrategy pattern:
```python
class PricingStrategy:
    def calculate(self, hours, time_of_day):
        pass

class PeakHourPricing(PricingStrategy):
    # Higher rates during peak
```
Then swap strategies based on time."

**Q4**: "How to scale to multiple lots?"
**A4**: "Replace singleton with manager:
```python
class ParkingManager:
    def __init__(self):
        self.lots = {}  # Multiple lots
    
    def find_available_lot(self, location):
        # Route to nearest available lot
```"

**Q5**: "How to test this?"
**A5**: "Unit tests for each component:
```python
def test_spot_assignment():
    lot = ParkingLot(1, 10)
    car = Car('TEST')
    spot = lot.find_spot(car)
    assert spot is not None

def test_fee_calculation():
    ticket = ParkingTicket(car, spot)
    ticket.entry_time = datetime(2024, 11, 27, 10, 0)
    ticket.exit_time = datetime(2024, 11, 27, 12, 30)
    assert ticket.get_duration_hours() == 2.5
```"

---

## Line Count Summary

| Phase | Time | Lines | Cumulative |
|-------|------|-------|-----------|
| Design | 5 min | - | - |
| Enums/Base | 10 min | 100 | 100 |
| Ticket/Payment | 10 min | 80 | 180 |
| Entrance/Exit | 15 min | 140 | 320 |
| ParkingLot | 15 min | 100 | 420 |
| Demo | 10 min | 80 | 500 |
| Discussion | 10 min | - | - |
| **TOTAL** | **75 min** | **~500** | **~500** |

---

## Pro Tips for Interview

1. **Start simple**: Get basic structure working first
2. **Add incrementally**: Spot finding → Payment → Exit handling
3. **Use print statements**: Show what's happening (debugging)
4. **Explain as you code**: Verbalize your thought process
5. **Ask questions**: "Should I add thread safety?" shows you think about production
6. **Test as you go**: Try each demo scenario immediately
7. **Be ready for extensions**: Have answers ready for new features
8. **Show design patterns**: Mention them as you use them

---

## Checklist

- [ ] Clarified requirements (5 min)
- [ ] Designed architecture (5 min)
- [ ] Created enumerations & base classes (10 min)
- [ ] Implemented parking ticket & payment (10 min)
- [ ] Built entrance/exit gates (15 min)
- [ ] Completed parking lot controller (15 min)
- [ ] Demo 1: Single vehicle entry/exit runs ✅
- [ ] Demo 2: Multiple vehicles works ✅
- [ ] Demo 3: Payment calculation correct ✅
- [ ] Demo 4: Full lot handling works ✅
- [ ] Demo 5: Statistics display works ✅
- [ ] Explained 4+ design patterns ✅
- [ ] Answered follow-up questions ✅
- [ ] Code is clean and well-organized ✅

---

## Success Criteria

✅ **You nailed it if you:**
1. Implemented core system in ~500 lines
2. All 5 demos run successfully
3. Explained design patterns clearly
4. Handled edge cases (full lot, invalid vehicles)
5. Discussed how to extend the system
6. Showed understanding of SOLID principles
7. Code is readable and well-documented
8. You stayed on time!

🚀 **You're interview-ready!**
