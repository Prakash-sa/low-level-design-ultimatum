# Parking Lot System — Complete Design Guide

> Multi-level garage managing spot allocation, vehicle entry/exit, charge calculation, payment, and real-time occupancy tracking.

**Scale**: 1,000+ spots, 100+ concurrent vehicles, entry/exit <30s, 99.9% uptime
**Duration**: 75-minute interview guide
**Focus**: Real-time spot allocation, charge calculation, occupancy tracking, concurrent entry/exit

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
A vehicle enters → the system finds the nearest available spot → issues a ticket → tracks occupancy → on exit calculates the charge (time-based, capped daily) → processes payment → releases the spot. Core concerns: efficient spot finding, accurate charges, and concurrent entry/exit without conflicts.

### Core Flow
```
Enter → FIND nearest spot → Issue Ticket → OCCUPIED
                                              ↓ (park)
Exit → Calculate Charge → PAY → Release Spot → AVAILABLE
   ↓ no spot
LOT FULL (reject entry)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Multi-level?** → "Yes — 1–10 levels, 100–200 spots each"
2. **Spot types?** → "Standard, disabled, reserved, compact"
3. **Pricing model?** → "Time-based ($2/hr, $20/day cap); monthly pass option"
4. **Payment methods?** → "Cash, card, mobile pay, monthly pass"
5. **Concurrency?** → "100+ concurrent vehicles across gates"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Driver** | Parks a vehicle | Enter, take ticket, exit, pay |
| **Attendant** | Handles exceptions | Manual payment, resolve disputes |
| **Admin** | Manages the lot | Configure spots, set pricing, view reports |
| **System** | Coordinator | Allocate spots, issue tickets, compute charges, track occupancy |

### Functional Requirements (What does the system do?)

✅ **Entry**
  - Find an available spot near the entrance
  - Issue a parking ticket

✅ **Exit & Payment**
  - Calculate parking charges
  - Accept multiple payment methods
  - Release the spot

✅ **Occupancy**
  - Track occupancy in real time
  - Display availability; signal "lot full"

✅ **Pricing & Reporting**
  - Support hourly / daily / monthly pricing
  - Support disabled / reserved spots
  - Generate revenue and utilization reports

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Entry/exit < 30 seconds
✅ **Scale**: 1,000+ spots, 100+ concurrent vehicles
✅ **Consistency**: Accurate charges; no double-allocation
✅ **Availability**: 99.9% uptime; real-time occupancy display

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Pricing** | $2/hour, $20/day cap |
| **Max capacity** | 1,000 spots |
| **Levels** | 1–10 |
| **Spots per level** | 100–200 |
| **Monthly pass** | $200 (unlimited) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
ParkingLot, Level, Spot, Vehicle, ParkingTicket, PricingStrategy, PaymentProcessor, ...
```

### Step 2.2: Define Core Classes

#### **Spot** — A single parking space
```
Properties:
  - spot_id: str
  - level: int
  - spot_type: SpotType (STANDARD, DISABLED, RESERVED, COMPACT)
  - status: SpotStatus (AVAILABLE, OCCUPIED, MAINTENANCE)
  - vehicle_license: Optional[str]
  - occupied_since: Optional[datetime]
```

#### **Vehicle** — A car entering the lot
```
Properties:
  - license_plate: str
  - vehicle_type: VehicleType (SEDAN, SUV, MOTORCYCLE)
  - entry_time: datetime
  - entry_gate: str
```

#### **ParkingTicket** — An entry/exit record
```
Properties:
  - ticket_id: str
  - license_plate: str
  - spot_id: str
  - entry_time / exit_time: datetime
  - charge: float
  - status: TicketStatus (ISSUED, PAID, VALIDATED)
  - payment_method: Optional[PaymentMethod]
```

#### **PricingStrategy** — Pluggable charge calculation
```
Behaviors:
  - get_charge(entry, exit, vehicle_type): HourlyPricing / DailyPricing / MonthlyPass
```

#### **PaymentProcessor** — Settles a ticket
```
Behaviors:
  - process_payment(ticket, method): bool
```

#### **ParkingLot** — Main controller (Singleton)
```
Properties:
  - spots: Dict[str, Spot]
  - available_spots: List[str]
  - tickets: Dict[str, ParkingTicket]
  - pricing_strategy: PricingStrategy
  - lock: threading lock

Behaviors:
  - find_available_spot(): Nearest (lowest-level) available spot
  - park_vehicle(plate, type, gate): Allocate + issue ticket
  - exit_vehicle(ticket_id, method): Charge + pay + release
  - get_occupancy() / get_available_count() / display_status()
```

### Step 2.3: Define Enumerations (State & Type)

```python
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
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Spot** | Atomic allocation unit | Can't track availability |
| **Vehicle** | Who is parking | Can't link tickets to cars |
| **ParkingTicket** | Entry/exit + charge record | No billing or audit trail |
| **PricingStrategy** | Flexible charging | Can't change pricing models |
| **PaymentProcessor** | Settle charges | Can't collect revenue |
| **ParkingLot** | Central coordination | No thread-safe occupancy tracking |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Park Vehicle** ⭐ CRITICAL
```python
def park_vehicle(license_plate: str, vehicle_type: VehicleType, entry_gate: str) -> Optional[str]:
    """
    Find a spot, issue a ticket, mark the spot OCCUPIED.

    Precondition: at least one AVAILABLE spot
    Postcondition: spot OCCUPIED, ticket ISSUED

    Returns: ticket_id, or None if the lot is full.

    Concurrency: THREAD-SAFE (lot lock — atomic find + occupy)
    """
    pass
```

#### **2. Exit Vehicle** ⭐ CRITICAL
```python
def exit_vehicle(ticket_id: str, payment_method: PaymentMethod = PaymentMethod.CARD) -> float:
    """
    Calculate charge, process payment, release the spot.

    Precondition: ticket exists
    Postcondition: ticket PAID, spot AVAILABLE

    Returns: charge amount.

    Concurrency: THREAD-SAFE
    """
    pass
```

#### **3. Occupancy & Status**
```python
def find_available_spot() -> Optional[Spot]: ...   # nearest (lowest-level) free spot
def get_occupancy() -> float: ...                  # percent occupied
def get_available_count() -> int: ...
def display_status() -> None: ...
```

### Step 3.2: Failure Model

The reference implementation returns `None`/`0.0` for an interview-friendly flow. Production would raise:

```python
class ParkingException(Exception): ...
class LotFullError(ParkingException): ...
class TicketNotFoundError(ParkingException): ...
class PaymentFailedError(ParkingException): ...
class AlreadyPaidError(ParkingException): ...
```

### Step 3.3: API Usage Example

```python
lot = ParkingLot(levels=3, spots_per_level=50)

ticket_id = lot.park_vehicle("ABC123", VehicleType.SEDAN, "Gate A")
lot.display_status()
charge = lot.exit_vehicle(ticket_id, PaymentMethod.CARD)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
ParkingLot HAS-A spots (1:N Composition)
  └─ Lot owns all spots across levels

ParkingLot HAS-A tickets (1:N Composition)
  └─ Lot owns all tickets

ParkingTicket REFERENCES a spot (1:1 Association)
  └─ Ticket points to the occupied spot

ParkingTicket REFERENCES a vehicle (1:1 Association)
  └─ Ticket records the license plate

ParkingLot USES-A PricingStrategy (1:1 Composition)
  └─ Pluggable charge calculation

ParkingLot USES-A PaymentProcessor (1:1 Composition)
  └─ Settles tickets on exit
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────┐
│   ParkingLot (Singleton)     │
├──────────────────────────────┤
│ - spots: Dict[str, Spot]     │
│ - available_spots: List[str] │
│ - tickets: Dict[str, Ticket] │
│ - pricing_strategy           │
│ - lock: threading.RLock      │
├──────────────────────────────┤
│ + park_vehicle(...): str     │
│ + exit_vehicle(...): float   │
│ + find_available_spot()      │
│ + get_occupancy(): float     │
└──────────┬───────────────────┘
   owns 1:N │
   ┌────────┼────────┐
   ▼        ▼        ▼
┌───────┐ ┌──────────────┐
│ Spot  │ │ParkingTicket │
├───────┤ ├──────────────┤
│type   │ │entry/exit    │
│status │ │charge        │
│level  │ │status        │
└───────┘ └──────────────┘

SPOT STATE MACHINE:
AVAILABLE ──park──→ OCCUPIED ──exit──→ AVAILABLE
                        │
                     MAINTENANCE (out of service)

PRICING STRATEGY:
┌─────────────────────┐
│ PricingStrategy     │
├─────────────────────┤
│ get_charge()        │
└──────────┬──────────┘
   ┌───────┼─────────┐
   ▼       ▼         ▼
HourlyPricing  DailyPricing  MonthlyPass
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| ParkingLot → Spots | 1:N | Composition | Lot owns all spots |
| ParkingLot → Tickets | 1:N | Composition | Lot owns all tickets |
| ParkingTicket → Spot | 1:1 | Association | Ticket references one spot |
| ParkingTicket → Vehicle | 1:1 | Association | Ticket records one vehicle |
| ParkingLot → PricingStrategy | 1:1 | Composition | One active pricing rule |
| ParkingLot → PaymentProcessor | 1:1 | Composition | Settles charges |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For ParkingLot)

**Problem**: All gates need one consistent view of spots, occupancy, and tickets.

**Solution**: One global ParkingLot instance with thread-safe initialization.

```python
class ParkingLot:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe init
**Trade-off**: ⚠️ Global state; use a `ParkingLotManager` for multiple lots

---

### Pattern 2: **State** (For Spot Status)

**Problem**: A spot moves AVAILABLE → OCCUPIED → AVAILABLE, with MAINTENANCE excluded from allocation.

**Solution**: An explicit `SpotStatus` enum driving allocation decisions.

```python
class SpotStatus(Enum):
    AVAILABLE = 1
    OCCUPIED = 2
    MAINTENANCE = 3
```

**Benefit**: ✅ Explicit lifecycle, ✅ Maintenance spots never allocated
**Trade-off**: ⚠️ Must keep `available_spots` index in sync with status

---

### Pattern 3: **Strategy** (For Pricing)

**Problem**: Charging varies (hourly, daily, monthly) and may change.

**Solution**: A `PricingStrategy` interface with pluggable implementations.

```python
class HourlyPricing(PricingStrategy):
    def get_charge(self, entry_time, exit_time, vehicle_type=None):
        minutes = (exit_time - entry_time).total_seconds() / 60
        hours = -(-int(minutes) // 60)          # ceiling division
        return min(hours * self.rate, self.max_charge)
```

**Benefit**: ✅ Swap pricing without touching exit logic
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 4: **Observer** (For "Lot Full" Alerts)

**Problem**: When the lot fills, signage / subscribed members must be notified.

**Solution**: Emit a "lot full" event from the entry path (here a print; in production an observer list).

```python
if not spot:
    print("✗ No available spots. Lot is full.")   # notify signage / members
    return None
```

**Benefit**: ✅ Decoupled alerting, easy to add SMS/email
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 5: **Factory** (For Tickets & Payments)

**Problem**: Ticket creation and payment routing should be centralized and consistent.

**Solution**: Centralize ticket creation in `park_vehicle` and payment in `PaymentProcessor`.

```python
ticket = ParkingTicket(f"T{self.ticket_counter:06d}", license_plate, spot.spot_id,
                       datetime.now(), status=TicketStatus.ISSUED)
```

**Benefit**: ✅ Consistent IDs and initialization
**Trade-off**: ⚠️ If it grows, promote to a dedicated factory/builder

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Single global lot state | Consistent occupancy/tickets |
| **State** | Spot lifecycle | Maintenance spots excluded |
| **Strategy** | Varying pricing | Pluggable, easy to extend |
| **Observer** | Lot-full alerts | Decoupled notifications |
| **Factory** | Ticket/payment creation | Centralized, consistent |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

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

    def __new__(cls, *args, **kwargs):
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
        self.lock = threading.RLock()   # re-entrant: park/display call other locked methods
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

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **park_vehicle** | Lot RLock | Atomic find + occupy + ticket issue (no double-allocation) |
| **exit_vehicle** | Lot RLock | Atomic charge + pay + release |
| **find_available_spot** | Lot RLock | Consistent view of availability |
| **display_status** | Lot RLock | Consistent occupancy snapshot |
| **Singleton init** | Class lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ A re-entrant lock (`RLock`) lets `park_vehicle` call `find_available_spot` and `display_status` call `get_occupancy` without self-deadlock
2. ✅ Find-then-occupy happens in one critical section so two cars can't claim one spot
3. ✅ Double-checked locking for the Singleton
4. ✅ For a fleet, shard locks per level/zone to remove the global bottleneck

---

## Demo Scenarios

### Scenario 1: Single Vehicle Entry & Exit
```
Park ABC123 → spot S1_1 issued ticket → exit → charge computed and paid
```

### Scenario 2: Occupancy Tracking
```
Park 30 vehicles → display: Total / Occupied / Available / Occupancy %
```

### Scenario 3: Charge Calculation
```
30 min → 1 hr × $2 = $2 ; 3.5 hr → 4 × $2 = $8 ; 15 hr → capped at $20
```

### Scenario 4: Lot Full
```
Fill all spots → "Lot is full" rejects entry → one exits → next vehicle parks
```

### Scenario 5: Concurrent Entries
```
10 threads park simultaneously → 10 distinct spots allocated, no conflicts
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you find an available spot?**

A: Query spots with status AVAILABLE, prefer the lowest level (closest to exit), return the first. With an availability index per level it's effectively O(1)/O(k).

**Q2: What's stored in a parking ticket?**

A: Entry/exit time, license plate, spot ID, charge, payment method, and status (ISSUED → PAID → VALIDATED) with a unique ticket ID.

**Q3: How do you calculate the charge?**

A: `ceil(duration_minutes / 60) × $2`, capped at $20/day; monthly pass = $0. e.g. 1.5h → 2h × $2 = $4.

**Q4: What payment methods are supported?**

A: Cash, card, mobile pay, and monthly pass — all routed through a `PaymentProcessor`.

**Q5: How do you handle "lot full"?**

A: When no AVAILABLE spot exists, reject entry, display "Lot Full", and optionally notify subscribed members.

### Intermediate Questions

**Q6: How do you track occupancy in real time?**

A: `occupied = total − available`; occupancy% updated atomically on each entry/exit and displayed on a refresh interval.

**Q7: How do you optimize finding the nearest spot?**

A: Index available spots per level and search lowest-level first; alternatively a priority queue keyed by distance from the entrance.

**Q8: How do you handle reserved/disabled spots?**

A: Tag `spot_type`; allocation filters to the eligible type so reserved/disabled spots aren't given to regular users.

**Q9: How do you prevent fraudulent exit without paying?**

A: Require ticket or plate scan on exit, verify it matches, and block the gate until payment is confirmed; log an audit trail.

### Advanced Questions

**Q10: How would you scale to multiple lots?**

A: A `ParkingLotManager` singleton manages one `ParkingLot` per location with independent accounting and a unified dashboard.

**Q11: How would you implement dynamic pricing?**

A: Time-based (peak vs off-peak) and demand-based surge when occupancy > 80%: `base × occupancy_multiplier`, recomputed periodically.

**Q12: How do you prevent double-billing?**

A: Ticket status guards (ISSUED → PAID → VALIDATED) plus an idempotent `payment_id` the gateway deduplicates.

---

## Scaling Q&A

### Q1: Can you handle 10K vehicles/day across 1,000 spots?

Yes — ~7 vehicles/min; spot lookup is O(1). The bottleneck is payment processing and gate throughput, not spot finding.

### Q2: How to handle concurrent entry/exit?

Lock per spot (or CAS) so transitions AVAILABLE → OCCUPIED are atomic; different spots proceed in parallel, only the same spot serializes.

### Q3: How to process 100+ concurrent payments?

Async payment gateway; queue slow exits and settle in the background (collect, mark PAID, release) without blocking.

### Q4: How to scale to 10× peak (70 vehicles/min)?

Add gates — ~6 vehicles/min/gate means ~12 gates for 70/min; spot query stays O(1).

### Q5: How to support monthly passes?

Link a pass to a license plate; on entry look up the plate, skip payment on exit; pass expires monthly.

### Q6: How to distribute across zones?

Partition spots into zones with independent availability trackers; route entries to the nearest zone with lowest occupancy to balance load.

### Q7: How to track revenue reliably?

Log every transaction (ticket, amount, time, method, status) and reconcile DB totals vs the gateway daily, alerting on mismatch.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through entry → ticket → occupancy → exit → payment → release
- [ ] Explain the spot state machine and availability index
- [ ] Explain the time-based charge with the daily cap
- [ ] Explain how the lock prevents double-allocation under concurrency
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss multi-lot management and zone partitioning
- [ ] Discuss dynamic pricing and double-billing prevention

---

**Ready for interview? Find a spot and park! 🅿️**
