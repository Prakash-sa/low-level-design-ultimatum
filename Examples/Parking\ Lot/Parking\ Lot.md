# Parking Lot System — 75-Minute Interview Guide

## Quick Start

**What is it?** Multi-level parking garage system managing spot allocation, vehicle entry/exit, payment, and occupancy tracking.

**Key Classes:**
- `ParkingLot` (Singleton): Central coordinator
- `Level`: Floor in garage (numbered)
- `Spot`: Individual parking space with vehicle/status
- `Vehicle`: Car with license plate, entry time
- `ParkingTicket`: Entry/exit record with charges
- `PaymentProcessor`: Handles payment transactions

**Core Flows:**
1. **Entry**: Vehicle enters → Find nearest available spot → Issue ticket → Update occupancy
2. **Occupancy Check**: Get available spots per level → Compute occupancy percentage
3. **Exit**: Vehicle exits → Calculate charges → Process payment → Release spot
4. **Pricing**: Flat rate or time-based ($2/hour, max $20/day)
5. **Reporting**: Track revenue, utilization, peak hours

**5 Design Patterns:**
- **Singleton**: One `ParkingLot` system
- **State Machine**: Spot status (available/occupied/reserved/maintenance)
- **Strategy**: Different pricing strategies (hourly, daily, monthly)
- **Observer**: Notify when lot full
- **Factory**: Create tickets, process payments

---

## System Overview

Multi-level parking garage optimizing spot utilization, managing entry/exit, calculating charges, and processing payments in real-time.

### Requirements

**Functional:**
- Find available spot near entrance
- Issue parking ticket
- Process vehicle exit
- Calculate parking charges
- Accept multiple payment methods
- Track occupancy
- Generate revenue reports
- Support disabled/reserved spots

**Non-Functional:**
- Entry/exit < 30 seconds
- Support 1000+ spots, 100+ concurrent vehicles
- Accurate charge calculation
- 99.9% uptime
- Real-time occupancy display

**Constraints:**
- Price: $2/hour, max $20/day
- Max capacity: 1000 spots
- Levels: 1-10
- Spots per level: 100-200
- Monthly pass: $200 (unlimited)

---

## Architecture Diagram (ASCII UML)

```
┌──────────────────┐
│ ParkingLot       │
│ (Singleton)      │
└────────┬─────────┘
         │
    ┌────┼─────────┐
    │    │         │
    ▼    ▼         ▼
┌───────┐ ┌─────────┐ ┌──────────┐
│Levels │ │Vehicles │ │Tickets   │
└───────┘ └─────────┘ └──────────┘
    │
    ▼
┌─────────┐
│Spots    │
│- Status │ AVAILABLE → OCCUPIED → AVAILABLE
│- Type   │       ↓
│- Level  │   RESERVED
└─────────┘

Pricing Strategy:
┌─────────────────────┐
│ PricingStrategy     │
├─────────────────────┤
│ get_charge()        │
└─────────────────────┘
        △
        │
    ┌───┴───┬─────────┐
    │       │         │
┌───┴──┐ ┌─┴────┐ ┌──┴──┐
│Hourly│ │Daily │ │Monthly
└──────┘ └──────┘ └──────┘
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you find an available spot?**
A: Query all spots with status=AVAILABLE. Filter by level (prefer level 1 closest to exit). Return first available. If no available on level 1, search level 2, etc. O(1) with hash table of available spots per level.

**Q2: What information is stored in a parking ticket?**
A: Entry time, vehicle license plate, spot ID, entry gate, exit gate (if exited), entry price, exit price, payment status, exit time. Ticket ID = unique identifier.

**Q3: How do you calculate parking charge?**
A: Exit time - Entry time = duration in minutes. Charge = ceil(duration/60) × $2. Cap at $20/day. If monthly pass: $0. Example: 1.5 hours = 2 hours × $2 = $4.

**Q4: What payment methods do you support?**
A: Cash, card (Visa/Mastercard), mobile pay (Apple Pay), monthly pass. Process via PaymentProcessor: validate, confirm, log transaction.

**Q5: How do you handle the "lot full" scenario?**
A: When no available spots: display "Lot Full" at entrance. Notify via SMS/email if member subscribed. Reject entry vehicles. Track peak hours.

### Intermediate Level

**Q6: How do you track occupancy in real-time?**
A: Maintain counter: total_occupied = sum of occupied spots per level. Occupancy % = total_occupied / total_capacity. Update on entry/exit (atomic). Display on sign: "850/1000 occupied (85%)" every 30 seconds.

**Q7: How to optimize finding nearest available spot?**
A: Index available spots per level. On entry: query level 1, if empty return first. If full, query level 2. Hierarchical search: O(k) where k = spots per level. Alternative: priority queue of available spots (distance from entrance).

**Q8: How to handle reserved spots (disabled, VIP)?**
A: Mark spot.type = RESERVED. On entry: filter only type=STANDARD. Reserved spots not available to regular users. Update spot status: AVAILABLE/RESERVED for management.

**Q9: How to integrate multiple payment gateways?**
A: PaymentProcessor has strategies: CashProcessor, CardProcessor, MobilePayProcessor. On exit: pass processor type. Each validates and charges accordingly. Unified interface.

**Q10: How to prevent fraudulent exit (without paying)?**
A: On exit: require ticket OR license plate scan. Verify ticket matches vehicle. If no payment: hold vehicle (alert attendant). Cannot exit without payment confirmation. Audit trail logged.

### Advanced Level

**Q11: How to scale to multiple parking lots?**
A: Global ParkingLotManager (Singleton) → manages multiple ParkingLot instances (one per location). Each lot has independent levels/spots/accounting. Unified dashboard shows all lots' occupancy + revenue.

**Q12: How to implement dynamic pricing?**
A: Time-based: peak hours (9-5 weekdays) = $3/hour, off-peak = $1/hour. Demand-based: if occupancy > 80%, surge pricing. Formula: base_price × occupancy_multiplier. Recalculate every 15 minutes.

---

## Scaling Q&A (12 Questions)

**Q1: Can you handle 10K vehicles/day across 1000 spots?**
A: Yes. Entry rate: 10K/24 hours = ~7 vehicles/minute. Processing time: 10 seconds per entry = 1 vehicle/second capacity. Available spots: O(1) lookup. Bottleneck: payment processing, not spot finding.

**Q2: How to handle concurrent entry/exit?**
A: Use locks on spot availability. On entry: atomic compare-and-swap (CAS) to transition spot from AVAILABLE → OCCUPIED. Multiple threads can execute simultaneously on different spots. Serialized only for same spot.

**Q3: How to process 100+ concurrent payments?**
A: Payment gateway supports 100+ concurrent requests (async). Queue exit requests if payment slow. Process in background: collect $$$, update ticket status (PAID), release spot. Non-blocking.

**Q4: How to prevent double-billing?**
A: Ticket status: ISSUED → PAID → VALIDATED. On exit: check if PAID already. If yes: reject. Idempotency: payment_id unique, gateway deduplicates.

**Q5: Can you handle 10x peak traffic (70 vehicles/min)?**
A: Yes, if hardware scales. Entry: find spot + issue ticket (10 sec each) = 6 vehicles/min per gate. Need 12 gates for 70 vehicles/min. Spot query: O(1), not bottleneck.

**Q6: How to track revenue reliably?**
A: Log every transaction: ticket_id, amount, timestamp, payment_method, status. Store in DB. Reconcile daily: expected revenue (DB) vs actual (payment gateway). Alert if mismatch.

**Q7: How to handle payment failures gracefully?**
A: Payment fails → retry 3x with exponential backoff. If all fail: mark ticket PAYMENT_PENDING. Attendant collects manual payment. Flag for investigation. Don't release spot until PAID.

**Q8: How to integrate with traffic management?**
A: API: GET /lot/1/available_spots → return JSON with occupancy %. External navigation app (Google Maps) calls this. Route drivers based on availability. Reduces searching time.

**Q9: How to support subscription/monthly passes?**
A: Member buys monthly pass ($200) → auto-linked to license plate. On entry: check license plate → find pass → exit free. No payment needed. Pass expires at end of month.

**Q10: How to generate analytics on peak hours?**
A: Log entry/exit with timestamp. Batch job: hourly aggregation (9 AM: 45 entries, 5 PM: 120 entries). Identify peak = 5 PM weekdays. Use for pricing adjustments, staffing.

**Q11: How to implement occupancy forecasting?**
A: Historical data: average occupancy by day/hour. ML model: predict occupancy at time T. Notify drivers ahead: "Lot 70% full at 3 PM, try Lot B". Distribute traffic.

**Q12: How to distribute across multiple zones (100 spots each)?**
A: Partition spots: Zone A (1-100), Zone B (101-200), etc. Each zone has independent availability tracker. On entry: query all zones, return nearest available in Zone with lowest occupancy. Balance load.

---

## Demo Scenarios (5 Examples)

### Demo 1: Vehicle Entry
```
- Vehicle arrives at entrance (Gate A)
- System searches available spots
- Finds Spot 47 (Level 2, near exit)
- Issues ticket: TICKET_001, entry 10:00 AM
- Vehicle proceeds to Level 2, Spot 47
- Spot status: AVAILABLE → OCCUPIED
```

### Demo 2: Charge Calculation
```
- Vehicle exits at 1:30 PM (parked 3.5 hours)
- Duration: 3.5 hours → rounds up to 4 hours
- Charge: 4 × $2/hour = $8.00
- Peak hours (3x) would be: 4 × $6 = $24 → capped at $20
- Member pays via card → PAID
```

### Demo 3: Occupancy Tracking
```
- Lot total capacity: 1000
- Currently occupied: 850
- Occupancy: 85%
- Display: "850/1000 (85% FULL)"
- Status: accepting new entries
- At 950+: alert entrance, display "ALMOST FULL"
```

### Demo 4: Monthly Pass
```
- John has monthly pass ($200)
- License plate: ABC123
- Enters at 9:00 AM
- Ticket issued (no charge)
- Exits at 5:00 PM
- Payment: $0 (pass covers)
- Log: 8-hour free parking
```

### Demo 5: Concurrent Entries
```
- 10 vehicles enter simultaneously (gates 1-10)
- Each searches available spots independently
- 10 different spots allocated (no conflicts)
- 10 tickets issued in parallel
- All complete in 10 seconds
```

---

## Complete Implementation

```python
"""
🅿️ Parking Lot System - Interview Implementation
Demonstrates:
1. Real-time spot allocation
2. Charge calculation
3. Occupancy tracking
4. Payment processing
5. Multi-level management
"""

from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import heapq

# ============================================================================
# ENUMERATIONS
# ============================================================================

class SpotType(Enum):
    STANDARD = 1
    DISABLED = 2
    RESERVED = 3
    COMPACT = 4

class SpotStatus(Enum):
    AVAILABLE = 1
    OCCUPIED = 2
    MAINTENANCE = 3

class VehicleType(Enum):
    SEDAN = 1
    SUV = 2
    MOTORCYCLE = 3

class TicketStatus(Enum):
    ISSUED = 1
    PAID = 2
    VALIDATED = 3

class PaymentMethod(Enum):
    CASH = 1
    CARD = 2
    MOBILE_PAY = 3
    PASS = 4

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Spot:
    spot_id: str
    level: int
    spot_type: SpotType
    status: SpotStatus = SpotStatus.AVAILABLE
    vehicle_license: Optional[str] = None
    occupied_since: Optional[datetime] = None

@dataclass
class Vehicle:
    license_plate: str
    vehicle_type: VehicleType
    entry_time: datetime
    entry_gate: str

@dataclass
class ParkingTicket:
    ticket_id: str
    license_plate: str
    spot_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    charge: float = 0.0
    status: TicketStatus = TicketStatus.ISSUED
    payment_method: Optional[PaymentMethod] = None

# ============================================================================
# PRICING STRATEGIES
# ============================================================================

class PricingStrategy:
    def get_charge(self, entry_time: datetime, exit_time: datetime, vehicle_type: VehicleType) -> float:
        pass

class HourlyPricing(PricingStrategy):
    def __init__(self, rate: float = 2.0, max_charge: float = 20.0):
        self.rate = rate
        self.max_charge = max_charge
    
    def get_charge(self, entry_time: datetime, exit_time: datetime, vehicle_type: VehicleType = None) -> float:
        duration_minutes = (exit_time - entry_time).total_seconds() / 60
        hours = -(-int(duration_minutes) // 60)  # Ceiling division
        charge = min(hours * self.rate, self.max_charge)
        return charge

class DailyPricing(PricingStrategy):
    def __init__(self, daily_rate: float = 15.0):
        self.daily_rate = daily_rate
    
    def get_charge(self, entry_time: datetime, exit_time: datetime, vehicle_type: VehicleType = None) -> float:
        duration_days = (exit_time - entry_time).days + 1
        return duration_days * self.daily_rate

class MonthlyPass(PricingStrategy):
    def get_charge(self, entry_time: datetime, exit_time: datetime, vehicle_type: VehicleType = None) -> float:
        return 0.0

# ============================================================================
# PAYMENT PROCESSOR
# ============================================================================

class PaymentProcessor:
    def process_payment(self, ticket: ParkingTicket, method: PaymentMethod) -> bool:
        print(f"  Processing payment: ${ticket.charge:.2f} via {method.name}")
        return True

# ============================================================================
# PARKING LOT (SINGLETON)
# ============================================================================

class ParkingLot:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, levels: int = 3, spots_per_level: int = 100):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.levels = levels
        self.spots_per_level = spots_per_level
        self.spots: Dict[str, Spot] = {}
        self.available_spots: List[str] = []
        self.tickets: Dict[str, ParkingTicket] = {}
        self.ticket_counter = 0
        self.lock = threading.Lock()
        self.pricing_strategy = HourlyPricing()
        
        # Initialize spots
        spot_id = 0
        for level in range(1, levels + 1):
            for i in range(spots_per_level):
                spot_id += 1
                spot = Spot(
                    f"S{level}_{i+1}",
                    level,
                    SpotType.STANDARD if i < 90 else SpotType.DISABLED,
                    SpotStatus.AVAILABLE
                )
                self.spots[spot.spot_id] = spot
                self.available_spots.append(spot.spot_id)
        
        print(f"🅿️ Parking lot initialized: {levels} levels, {spots_per_level} spots/level")
    
    def find_available_spot(self) -> Optional[Spot]:
        with self.lock:
            # Sort by level (prefer lower levels)
            available = sorted(
                [self.spots[s] for s in self.available_spots],
                key=lambda x: x.level
            )
            
            if available:
                return available[0]
            return None
    
    def park_vehicle(self, license_plate: str, vehicle_type: VehicleType, entry_gate: str) -> Optional[str]:
        with self.lock:
            spot = self.find_available_spot()
            
            if not spot:
                print(f"✗ No available spots. Lot is full.")
                return None
            
            # Issue ticket
            self.ticket_counter += 1
            ticket = ParkingTicket(
                f"T{self.ticket_counter:06d}",
                license_plate,
                spot.spot_id,
                datetime.now(),
                status=TicketStatus.ISSUED,
                payment_method=None
            )
            
            self.tickets[ticket.ticket_id] = ticket
            
            # Update spot
            spot.status = SpotStatus.OCCUPIED
            spot.vehicle_license = license_plate
            spot.occupied_since = datetime.now()
            self.available_spots.remove(spot.spot_id)
            
            print(f"✓ Vehicle {license_plate} parked at {spot.spot_id} (Level {spot.level})")
            print(f"  Ticket: {ticket.ticket_id}")
            
            return ticket.ticket_id
    
    def exit_vehicle(self, ticket_id: str, payment_method: PaymentMethod = PaymentMethod.CARD) -> float:
        with self.lock:
            if ticket_id not in self.tickets:
                return 0.0
            
            ticket = self.tickets[ticket_id]
            ticket.exit_time = datetime.now()
            
            # Calculate charge
            charge = self.pricing_strategy.get_charge(
                ticket.entry_time,
                ticket.exit_time
            )
            ticket.charge = charge
            
            # Process payment
            processor = PaymentProcessor()
            if processor.process_payment(ticket, payment_method):
                ticket.status = TicketStatus.PAID
                ticket.payment_method = payment_method
            
            # Release spot
            spot = self.spots[ticket.spot_id]
            spot.status = SpotStatus.AVAILABLE
            spot.vehicle_license = None
            self.available_spots.append(spot.spot_id)
            
            print(f"✓ Vehicle {ticket.license_plate} exited")
            print(f"  Duration: {(ticket.exit_time - ticket.entry_time).total_seconds()/3600:.1f} hours")
            print(f"  Charge: ${charge:.2f}")
            
            return charge
    
    def get_occupancy(self) -> float:
        with self.lock:
            total = len(self.spots)
            occupied = total - len(self.available_spots)
            return (occupied / total) * 100
    
    def get_available_count(self) -> int:
        with self.lock:
            return len(self.available_spots)
    
    def display_status(self):
        with self.lock:
            occupancy = self.get_occupancy()
            available = self.get_available_count()
            total = len(self.spots)
            
            print(f"\n  Parking Lot Status:")
            print(f"  Total capacity: {total}")
            print(f"  Occupied: {total - available}")
            print(f"  Available: {available}")
            print(f"  Occupancy: {occupancy:.1f}%")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_single_vehicle():
    print("\n" + "="*70)
    print("DEMO 1: SINGLE VEHICLE ENTRY & EXIT")
    print("="*70)
    
    lot = ParkingLot(3, 50)
    
    ticket_id = lot.park_vehicle("ABC123", VehicleType.SEDAN, "Gate A")
    if ticket_id:
        charge = lot.exit_vehicle(ticket_id)
        print(f"  Total charge: ${charge:.2f}")

def demo_2_occupancy():
    print("\n" + "="*70)
    print("DEMO 2: OCCUPANCY TRACKING")
    print("="*70)
    
    lot = ParkingLot(3, 50)
    
    # Park 30 vehicles
    tickets = []
    for i in range(30):
        ticket = lot.park_vehicle(f"CAR{i:03d}", VehicleType.SEDAN, "Gate A")
        if ticket:
            tickets.append(ticket)
    
    lot.display_status()

def demo_3_charge_calculation():
    print("\n" + "="*70)
    print("DEMO 3: CHARGE CALCULATION (Different durations)")
    print("="*70)
    
    lot = ParkingLot(2, 30)
    
    # 30 minutes
    ticket1 = lot.park_vehicle("SHORT", VehicleType.SEDAN, "Gate A")
    if ticket1:
        t = lot.tickets[ticket1]
        t.entry_time = datetime.now() - timedelta(minutes=30)
        charge = lot.exit_vehicle(ticket1)
    
    # 3.5 hours
    ticket2 = lot.park_vehicle("MEDIUM", VehicleType.SUV, "Gate A")
    if ticket2:
        t = lot.tickets[ticket2]
        t.entry_time = datetime.now() - timedelta(hours=3, minutes=30)
        charge = lot.exit_vehicle(ticket2)
    
    # 15 hours (capped)
    ticket3 = lot.park_vehicle("LONG", VehicleType.SEDAN, "Gate A")
    if ticket3:
        t = lot.tickets[ticket3]
        t.entry_time = datetime.now() - timedelta(hours=15)
        charge = lot.exit_vehicle(ticket3)

def demo_4_lot_full():
    print("\n" + "="*70)
    print("DEMO 4: LOT FULL SCENARIO")
    print("="*70)
    
    lot = ParkingLot(1, 5)  # Small lot for demo
    
    tickets = []
    for i in range(5):
        ticket = lot.park_vehicle(f"CAR{i}", VehicleType.SEDAN, "Gate A")
        if ticket:
            tickets.append(ticket)
    
    lot.display_status()
    
    # Try to park when full
    rejected = lot.park_vehicle("OVERFLOW", VehicleType.SEDAN, "Gate A")
    
    # Exit one vehicle
    if tickets:
        lot.exit_vehicle(tickets[0])
    
    lot.display_status()
    
    # Now can park again
    ticket = lot.park_vehicle("OVERFLOW", VehicleType.SEDAN, "Gate A")

def demo_5_concurrent():
    print("\n" + "="*70)
    print("DEMO 5: CONCURRENT ENTRIES (Multi-threading)")
    print("="*70)
    
    lot = ParkingLot(2, 100)
    
    def park_vehicle_concurrent(license_plate):
        lot.park_vehicle(license_plate, VehicleType.SEDAN, "Gate A")
    
    # Simulate 10 concurrent entries
    threads = []
    for i in range(10):
        t = threading.Thread(target=park_vehicle_concurrent, args=(f"CONCURRENT{i}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    lot.display_status()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🅿️ PARKING LOT SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_single_vehicle()
    demo_2_occupancy()
    demo_3_charge_calculation()
    demo_4_lot_full()
    demo_5_concurrent()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Summary

✅ **Real-time spot** finding and allocation
✅ **Charge calculation** with hourly/daily rates & caps
✅ **Occupancy tracking** and reporting
✅ **Payment processing** (cash, card, pass, mobile)
✅ **Multi-level** support (1-10 floors)
✅ **Peak hour** pricing (dynamic multipliers)
✅ **Monthly pass** integration
✅ **Traffic distribution** across zones
✅ **Concurrent entry/exit** without race conditions
✅ **Analytics** (revenue, peak hours, forecasting)

**Key Takeaway**: Parking lot demonstrates real-time resource allocation, charge calculation with dynamic pricing, and high-concurrency transaction processing. Core focus: finding spots efficiently, calculating charges accurately, and managing occupancy.
