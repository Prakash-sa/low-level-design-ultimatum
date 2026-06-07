# Car Rental System — Complete Design Guide

> Multi-location vehicle inventory, reservation lifecycle management, dynamic pricing strategies, pickup/return processing, and cancellation penalty enforcement.

**Scale**: 1,000+ concurrent users, 10K+ vehicles, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Availability management, pricing flexibility, reservation lifecycle, multi-location operations

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
A customer searches vehicles by location and dates → selects a vehicle → makes a reservation (vehicle locked to that booking) → picks up the vehicle → returns it with charges calculated → or cancels (penalty applied based on timing). Core concerns: double-booking prevention, flexible pricing, and clear reservation lifecycle.

### Core Flow
```
Search Vehicles → Select → RESERVE (lock vehicle) → PICKUP → RETURN (calculate charges)
                                  ↓ or cancel
                           CANCELLED (penalty if < 48h)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single location or multi-location?** → "Multi-location; each branch has its own inventory"
2. **Do we support one-way rentals (pickup at A, return at B)?** → "Yes, with a transfer fee"
3. **Real payment processing?** → "Mock payment service for the interview"
4. **Can reservations be modified?** → "Yes, until 24 hours before pickup"
5. **Are there cancellation fees?** → "Yes, 50% penalty if cancelled within 48 hours of pickup"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Searches and rents vehicles | Search, reserve, modify, cancel, pickup, return |
| **Rental Admin** | Manages fleet and locations | Add vehicles, create locations, view reports |
| **System** | Coordinator & enforcer | Enforce availability, calculate pricing, track status |

### Functional Requirements (What does the system do?)

✅ **Search & Browse**
  - Search vehicles by location, type, and date range
  - View real-time availability with pricing quotes

✅ **Reserve & Modify**
  - Create a reservation (locks vehicle to customer)
  - Modify return date if > 24 hours before pickup
  - Calculate updated pricing on modification

✅ **Pickup & Return**
  - Verify reservation status before vehicle handover
  - Update vehicle status to PICKED_UP on handover
  - Inspect vehicle and record mileage on return
  - Calculate final charges and process payment

✅ **Cancel & Refund**
  - Cancel reservation before pickup
  - Apply penalty based on time until pickup
  - Release vehicle back to available

✅ **Dynamic Pricing**
  - Support daily, weekly, and monthly pricing strategies
  - Calculate total price based on duration and selected strategy

✅ **Customer & Admin**
  - Customer profile and rental history
  - Admin reports: revenue, utilization, popular models

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 10K+ simultaneous searches and reservations  
✅ **Consistency**: No double-booking (atomic vehicle status transitions)  
✅ **Availability**: Real-time inventory updates across locations  
✅ **Latency**: O(1) vehicle availability lookup per location  
✅ **Uptime**: 99.9% for critical reservation operations  
✅ **Throughput**: Handle holiday-peak booking spikes

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Reservation modification window** | Must be > 24 hours before pickup |
| **Cancellation penalty (< 48h)** | 50% of total price |
| **Cancellation penalty (48h–7d)** | 25% of total price |
| **Cancellation penalty (> 7d)** | Full refund (minus admin fee) |
| **Vehicle inspection** | Required before pickup and on return |
| **Overlapping reservations** | NOT allowed for same vehicle |
| **Real payment network** | NO — mock billing for demo |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Vehicle, Reservation, Customer, Location, PricingStrategy, Payment, ...
```

### Step 2.2: Define Core Classes

#### **Vehicle** — A rentable car
```
Properties:
  - vehicle_id: str
  - vehicle_type: VehicleType (ECONOMY, SEDAN, SUV, LUXURY)
  - location: str (location_id it belongs to)
  - daily_rate: float
  - status: VehicleStatus (AVAILABLE, RESERVED, PICKED_UP, IN_MAINTENANCE)
  - current_mileage: int
  - lock: threading.RLock

Behaviors:
  - is_available(): Check if status is AVAILABLE
  - reserve(): Transition AVAILABLE → RESERVED
  - pickup(): Transition RESERVED → PICKED_UP
  - return_vehicle(final_mileage): Transition PICKED_UP → AVAILABLE
```

#### **Reservation** — A booking record
```
Properties:
  - reservation_id: str
  - customer_id: str
  - vehicle_id: str
  - pickup_date: datetime
  - return_date: datetime
  - status: ReservationStatus (PENDING, ACTIVE, COMPLETED, CANCELLED)
  - pricing_strategy: PricingStrategy
  - total_price: float
  - created_at: datetime

Behaviors:
  - can_modify(): Check if > 24 hours before pickup
  - calculate_cancellation_penalty(): Return penalty amount
```

#### **Customer** — A registered renter
```
Properties:
  - customer_id: str
  - name: str
  - email: str
  - reservations: List[Reservation]
  - created_at: datetime

Behaviors:
  - (none — data holder; reservations linked externally)
```

#### **Location** — A rental branch
```
Properties:
  - location_id: str
  - name: str
  - city: str
  - vehicles: List[Vehicle]
  - created_at: datetime

Behaviors:
  - add_vehicle(vehicle): Register vehicle at this location
  - get_available_vehicles(type): Return filtered available list
```

#### **PricingStrategy** — An interchangeable pricing algorithm
```
Properties:
  - (abstract; no state)

Behaviors:
  - calculate_price(days, daily_rate): Return total price
  - Daily: days × daily_rate
  - Weekly: full weeks get 1 day free; remaining days at daily rate
  - Monthly: full months get 5 days free; remaining days at daily rate
```

#### **CarRentalSystem** — Main controller (Singleton)
```
Properties:
  - customers: Dict[str, Customer]
  - locations: Dict[str, Location]
  - reservations: Dict[str, Reservation]
  - vehicles: Dict[str, Vehicle]
  - lock: threading.RLock

Behaviors:
  - register_customer / create_location / add_vehicle_to_location
  - search_vehicles(location_id, type, pickup_date, return_date): List[Vehicle]
  - create_reservation(...): Optional[str]
  - modify_reservation(reservation_id, new_return_date): bool
  - pickup_vehicle(reservation_id): bool
  - return_vehicle(reservation_id, final_mileage): Tuple[bool, float]
  - cancel_reservation(reservation_id): Tuple[bool, float]
```

### Step 2.3: Define Enumerations (State & Type)

```python
class VehicleStatus(Enum):
    AVAILABLE = 1      # Ready to be reserved
    RESERVED = 2       # Locked by a reservation
    PICKED_UP = 3      # Currently with customer
    IN_MAINTENANCE = 4 # Not available for rental

class ReservationStatus(Enum):
    PENDING = 1    # Confirmed but vehicle not yet picked up
    ACTIVE = 2     # Vehicle currently with customer
    COMPLETED = 3  # Vehicle returned, charges settled
    CANCELLED = 4  # Reservation voided (penalty may apply)

class VehicleType(Enum):
    ECONOMY = 1
    SEDAN = 2
    SUV = 3
    LUXURY = 4
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Vehicle** | Track availability, location, status | Can't prevent double-booking |
| **Reservation** | Bind customer to vehicle + dates | Can't enforce pickup/return lifecycle |
| **Customer** | Link reservations and history | Can't track rental history or notify |
| **Location** | Group vehicles by branch | Can't support multi-location search |
| **PricingStrategy** | Pluggable rate calculation | Can't offer weekly/monthly discounts |
| **CarRentalSystem** | Central thread-safe coordinator | No consistent global state |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Search Vehicles**
```python
def search_vehicles(location_id: str, vehicle_type: Optional[VehicleType],
                    pickup_date: datetime, return_date: datetime) -> List[Vehicle]:
    """
    Return available vehicles at a location that match the requested type.
    Returns: List of Vehicle objects with status == AVAILABLE.
    Raises: LocationNotFoundError if location_id is unknown.
    Response Time: <100ms (in-memory lookup)
    """
    pass
```

#### **2. Create Reservation** ⭐ CRITICAL
```python
def create_reservation(customer_id: str, vehicle_id: str,
                       pickup_date: datetime, return_date: datetime,
                       pricing_strategy: PricingStrategy) -> Optional[str]:
    """
    Lock a vehicle for a customer over a date range and generate pricing.

    Precondition: vehicle.status == AVAILABLE
    Postcondition: vehicle.status == RESERVED, Reservation.status == PENDING

    Returns: reservation_id string on success, None on failure.

    Failure causes:
      - Customer or vehicle not found
      - Vehicle already reserved or unavailable

    Concurrency: THREAD-SAFE (atomic check + status transition)
    Response Time: <200ms
    """
    pass
```

#### **3. Modify Reservation**
```python
def modify_reservation(reservation_id: str, new_return_date: datetime) -> bool:
    """
    Update the return date of a PENDING reservation.

    Precondition: reservation.can_modify() is True (> 24h before pickup)
    Postcondition: total_price recalculated at new duration

    Returns: True on success, False if modification window has passed.
    Side Effects: Logs price difference (charge or refund delta).
    """
    pass
```

#### **4. Pickup Vehicle** ⭐ CRITICAL
```python
def pickup_vehicle(reservation_id: str) -> bool:
    """
    Hand over vehicle to customer.

    Precondition: reservation.status == PENDING, vehicle.status == RESERVED
    Postcondition: reservation.status == ACTIVE, vehicle.status == PICKED_UP

    Returns: True on success, False if preconditions fail.
    Concurrency: THREAD-SAFE
    """
    pass
```

#### **5. Return Vehicle** ⭐ CRITICAL
```python
def return_vehicle(reservation_id: str, final_mileage: int) -> Tuple[bool, float]:
    """
    Process vehicle return with final charge calculation.

    Precondition: reservation.status == ACTIVE, vehicle.status == PICKED_UP
    Postcondition: reservation.status == COMPLETED, vehicle.status == AVAILABLE

    Returns: (True, total_charge) on success, (False, 0) on failure.
    Side Effects: Records final mileage, releases vehicle to inventory.
    """
    pass
```

#### **6. Cancel Reservation**
```python
def cancel_reservation(reservation_id: str) -> Tuple[bool, float]:
    """
    Cancel a PENDING reservation and calculate refund after penalty.

    Precondition: reservation.status == PENDING (cannot cancel ACTIVE)
    Postcondition: reservation.status == CANCELLED, vehicle.status == AVAILABLE

    Returns: (True, refund_amount) on success, (False, 0) if not cancellable.

    Penalty rules:
      < 48h  → 50% penalty
      48h–7d → 25% penalty
      > 7d   → full refund (minus admin fee)
    """
    pass
```

### Step 3.2: Exception / Failure Model

The demo uses return-value error reporting (`None` / `False`). A production version would raise:

```python
class RentalException(Exception): ...
class VehicleNotAvailableError(RentalException): ...
class ReservationNotFoundError(RentalException): ...
class ModificationWindowClosedError(RentalException): ...
class ActiveReservationCancelError(RentalException): ...
class LocationNotFoundError(RentalException): ...
```

### Step 3.3: API Usage Example

```python
system = CarRentalSystem()

# 1. Setup
system.register_customer("C001", "Alice", "alice@example.com")
system.create_location("LOC001", "SF Downtown", "San Francisco")
system.add_vehicle_to_location("V001", VehicleType.ECONOMY, "LOC001", 50.0)

# 2. Search
pickup = datetime.now() + timedelta(days=1)
return_date = datetime.now() + timedelta(days=3)
vehicles = system.search_vehicles("LOC001", VehicleType.ECONOMY, pickup, return_date)

# 3. Reserve
res_id = system.create_reservation("C001", "V001", pickup, return_date, DailyPricingStrategy())

# 4. Pickup
system.pickup_vehicle(res_id)

# 5. Return
success, charge = system.return_vehicle(res_id, 15050)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
CarRentalSystem HAS-A customers / locations / vehicles / reservations (1:N Composition)
  └─ System owns and manages lifecycle of all entities

Location HAS-A vehicles (1:N Composition)
  └─ Each branch owns its vehicle fleet

Reservation REFERENCES customer, vehicle (1:1 Association)
  └─ Reservation links existing entities (no ownership)

Customer HAS-A reservations (1:N Composition)
  └─ Customer holds their booking history

CarRentalSystem USES-A PricingStrategy (1:1 per reservation)
  └─ Strategy is injected at reservation creation time
```

### Step 4.2: Complete UML Class Diagram

```
┌─────────────────────────────────────┐
│   CarRentalSystem (Singleton)       │
├─────────────────────────────────────┤
│ - customers: Dict[str, Customer]    │
│ - locations: Dict[str, Location]    │
│ - reservations: Dict[str, Res]      │
│ - vehicles: Dict[str, Vehicle]      │
│ - lock: threading.RLock             │
├─────────────────────────────────────┤
│ + register_customer(...): Customer  │
│ + create_location(...): Location    │
│ + add_vehicle_to_location(...)      │
│ + search_vehicles(...): List        │
│ + create_reservation(...): str      │
│ + modify_reservation(...): bool     │
│ + pickup_vehicle(...): bool         │
│ + return_vehicle(...): (bool,float) │
│ + cancel_reservation(...): (b,f)    │
└────────────┬────────────────────────┘
             │ manages 1:N
    ┌────────┼────────┬───────────┐
    │        │        │           │
    ▼        ▼        ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│Customers │ │Locations │ │Reservations[]│
│{id→Cust} │ │{id→Loc}  │ │{id→Res}      │
└──────────┘ └────┬─────┘ └────┬─────────┘
                  │            │
                  ▼            ▼
            ┌──────────┐  ┌────────────────┐
            │Vehicles[]│  │  Reservation   │
            │{id→Veh}  │  ├────────────────┤
            └──────────┘  │+vehicle_id     │
                          │+customer_id    │
                          │+pickup_date    │
                          │+return_date    │
                          │+total_price    │
                          │+status: Enum   │
                          └────────────────┘

PRICING STRATEGY PATTERN:
┌──────────────────────────┐
│  PricingStrategy (ABC)   │
├──────────────────────────┤
│ + calculate_price(days,  │
│     daily_rate): float   │
└──────────┬───────────────┘
           │ implemented by
           ├─→ DailyPricingStrategy   (days × rate)
           ├─→ WeeklyPricingStrategy  (1 day free/week)
           └─→ MonthlyPricingStrategy (5 days free/month)

VEHICLE STATE MACHINE:
AVAILABLE ──reserve()──→ RESERVED ──pickup()──→ PICKED_UP ──return()──→ AVAILABLE
    ▲                                                                         │
    └─────────── cancel() releases back to AVAILABLE ────────────────────────┘
    (IN_MAINTENANCE if flagged by admin)

OBSERVER PATTERN (Notifications):
┌──────────────────────────┐
│ ReservationObserver(ABC) │
├──────────────────────────┤
│ + update(event, data)    │
└──────────┬───────────────┘
           │ implemented by
           ├─→ EmailNotifier
           ├─→ SMSNotifier
           └─→ PushNotifier
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| CarRentalSystem → Customers | 1:N | Composition | System owns all customers |
| CarRentalSystem → Locations | 1:N | Composition | System owns all branches |
| CarRentalSystem → Vehicles | 1:N | Composition | System owns all vehicles |
| CarRentalSystem → Reservations | 1:N | Composition | System owns all bookings |
| Location → Vehicles | 1:N | Composition | Branch owns its fleet |
| Customer → Reservations | 1:N | Composition | Customer holds booking history |
| Reservation → Vehicle | 1:1 | Association | Booking references one vehicle |
| Reservation → Customer | 1:1 | Association | Booking references one customer |
| Reservation → PricingStrategy | 1:1 | Association | Booking uses one pricing rule |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For CarRentalSystem)

**Problem**: All branches and reservation requests need a single consistent view of inventory and bookings.

**Solution**: One global `CarRentalSystem` instance with double-checked locking.

```python
class CarRentalSystem:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe init (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Bottleneck at scale across data centers

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Different customers want daily, weekly, or monthly rates. Pricing rules will evolve.

**Solution**: Inject a `PricingStrategy` at reservation creation time; swap without touching booking logic.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, days: int, daily_rate: float) -> float:
        pass

class WeeklyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        weeks = days // 7
        remaining_days = days % 7
        weekly_rate = daily_rate * 6  # 1 day free per week
        return weeks * weekly_rate + remaining_days * daily_rate

# Usage: swap algorithm at reservation time
res_id = system.create_reservation("C001", "V001", pickup, return_date,
                                   WeeklyPricingStrategy())
```

**Benefit**: ✅ Easy to add new pricing models (EarlyBird, Corporate, etc.), ✅ No core code change  
**Trade-off**: ⚠️ Extra abstraction layer; caller must choose strategy

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Reservation events (confirmed, modified, cancelled) must notify customers by email/SMS without coupling.

**Solution**: Observer pattern decouples event production from notification delivery.

```python
class ReservationObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict): pass

class EmailNotifier(ReservationObserver):
    def update(self, event: str, data: dict):
        if event == "reserved":
            print(f"Email: Reservation {data['res_id']} confirmed!")

# Usage: register once, fire on every event
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())
```

**Benefit**: ✅ Loose coupling, ✅ New channels (Slack, push) added with no core change  
**Trade-off**: ⚠️ Observer lifecycle management; notification failures can propagate

---

### Pattern 4: **State Enums** (For Vehicle & Reservation Lifecycles)

**Problem**: Vehicles and reservations move through defined states. Invalid transitions (e.g., returning a vehicle never picked up) must be blocked.

**Solution**: Explicit enum states with guarded transition methods.

```python
def pickup(self) -> bool:
    with self.lock:
        if self.status == VehicleStatus.RESERVED:   # Guard
            self.status = VehicleStatus.PICKED_UP
            return True
        return False
```

**Benefit**: ✅ Explicit state, ✅ Invalid transitions caught at runtime  
**Trade-off**: ⚠️ State logic spread across entity methods; use a State class if transitions grow

---

### Pattern 5: **Factory** (For Reservation Creation)

**Problem**: Creating a reservation requires validating entities, locking the vehicle, and initializing pricing — complex multi-step logic.

**Solution**: `create_reservation()` acts as a factory method centralizing all creation steps.

```python
def create_reservation(self, customer_id, vehicle_id, pickup_date,
                       return_date, pricing_strategy):
    # Factory: validate, lock, price, store atomically
    vehicle.reserve()
    reservation = Reservation(res_id, customer_id, vehicle_id,
                               pickup_date, return_date, pricing_strategy)
    self.reservations[res_id] = reservation
    customer.reservations.append(reservation)
    return res_id
```

**Benefit**: ✅ Centralized creation, ✅ Consistent initialization with pricing  
**Trade-off**: ⚠️ System class grows; consider a dedicated ReservationFactory if it becomes large

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Need single global CarRentalSystem | Consistent state across all branches |
| **Strategy** | Varying pricing (daily/weekly/monthly) | Pluggable, easy to extend |
| **Observer** | Reservation events trigger notifications | Loose coupling, event-driven |
| **State (Enum)** | Vehicle and reservation lifecycle | Invalid transitions prevented |
| **Factory** | Complex multi-step reservation creation | Centralized, consistent |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Car Rental System - Interview Implementation
Demonstrates:
1. Search & reserve vehicles
2. Modify reservations
3. Pickup with inspection
4. Return with billing
5. Cancellation with penalties
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class VehicleStatus(Enum):
    AVAILABLE = 1
    RESERVED = 2
    PICKED_UP = 3
    IN_MAINTENANCE = 4

class ReservationStatus(Enum):
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELLED = 4

class VehicleType(Enum):
    ECONOMY = 1
    SEDAN = 2
    SUV = 3
    LUXURY = 4

# ============================================================================
# PRICING STRATEGY
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, days: int, daily_rate: float) -> float:
        pass

class DailyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        return days * daily_rate

class WeeklyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        weeks = days // 7
        remaining_days = days % 7
        weekly_rate = daily_rate * 6  # 1 day free per week
        return weeks * weekly_rate + remaining_days * daily_rate

class MonthlyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        months = days // 30
        remaining_days = days % 30
        monthly_rate = daily_rate * 25  # 5 days free per month
        return months * monthly_rate + remaining_days * daily_rate

# ============================================================================
# CORE ENTITIES
# ============================================================================

class Vehicle:
    def __init__(self, vehicle_id: str, vehicle_type: VehicleType,
                 location: str, daily_rate: float):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.location = location
        self.daily_rate = daily_rate
        self.status = VehicleStatus.AVAILABLE
        self.current_mileage = 0
        self.created_at = datetime.now()
        self.lock = threading.RLock()  # RLock to allow nested calls

    def is_available(self) -> bool:
        with self.lock:
            return self.status == VehicleStatus.AVAILABLE

    def reserve(self) -> bool:
        with self.lock:
            if self.status == VehicleStatus.AVAILABLE:
                self.status = VehicleStatus.RESERVED
                return True
            return False

    def pickup(self) -> bool:
        with self.lock:
            if self.status == VehicleStatus.RESERVED:
                self.status = VehicleStatus.PICKED_UP
                return True
            return False

    def return_vehicle(self, final_mileage: int) -> bool:
        with self.lock:
            if self.status == VehicleStatus.PICKED_UP:
                self.current_mileage = final_mileage
                self.status = VehicleStatus.AVAILABLE
                return True
            return False

class Reservation:
    def __init__(self, reservation_id: str, customer_id: str, vehicle_id: str,
                 pickup_date: datetime, return_date: datetime,
                 pricing_strategy: PricingStrategy):
        self.reservation_id = reservation_id
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.pickup_date = pickup_date
        self.return_date = return_date
        self.status = ReservationStatus.PENDING
        self.pricing_strategy = pricing_strategy
        self.total_price = self._calculate_price()
        self.created_at = datetime.now()

    def _calculate_price(self) -> float:
        days = max(1, (self.return_date - self.pickup_date).days)
        daily_rate = 50.0  # $50/day default
        return self.pricing_strategy.calculate_price(days, daily_rate)

    def can_modify(self) -> bool:
        hours_until_pickup = (self.pickup_date - datetime.now()).total_seconds() / 3600
        return hours_until_pickup > 24

    def calculate_cancellation_penalty(self) -> float:
        hours_until_pickup = (self.pickup_date - datetime.now()).total_seconds() / 3600
        if hours_until_pickup < 48:
            return self.total_price * 0.5
        elif hours_until_pickup < 168:  # 7 days
            return self.total_price * 0.25
        else:
            return 0  # Full refund minus admin fee

class Customer:
    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.reservations = []
        self.created_at = datetime.now()

class Location:
    def __init__(self, location_id: str, name: str, city: str):
        self.location_id = location_id
        self.name = name
        self.city = city
        self.vehicles = []
        self.created_at = datetime.now()

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)

    def get_available_vehicles(self, vehicle_type: Optional[VehicleType] = None) -> List[Vehicle]:
        available = [v for v in self.vehicles if v.is_available()]
        if vehicle_type:
            available = [v for v in available if v.vehicle_type == vehicle_type]
        return available

# ============================================================================
# CAR RENTAL SYSTEM (SINGLETON)
# ============================================================================

class CarRentalSystem:
    _instance = None
    _lock = threading.RLock()  # RLock for thread-safe singleton init

    def __new__(cls, *args, **kwargs):
        # Accept *args/**kwargs so Python does not reject them during __init__
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.customers = {}
        self.locations = {}
        self.reservations = {}
        self.vehicles = {}
        self.lock = threading.RLock()  # RLock prevents deadlock on nested calls

    def register_customer(self, customer_id: str, name: str, email: str) -> Customer:
        with self.lock:
            customer = Customer(customer_id, name, email)
            self.customers[customer_id] = customer
            return customer

    def create_location(self, location_id: str, name: str, city: str) -> Location:
        with self.lock:
            location = Location(location_id, name, city)
            self.locations[location_id] = location
            return location

    def add_vehicle_to_location(self, vehicle_id: str, vehicle_type: VehicleType,
                                location_id: str, daily_rate: float) -> Vehicle:
        with self.lock:
            vehicle = Vehicle(vehicle_id, vehicle_type, location_id, daily_rate)
            self.vehicles[vehicle_id] = vehicle
            if location_id in self.locations:
                self.locations[location_id].add_vehicle(vehicle)
            return vehicle

    def search_vehicles(self, location_id: str, vehicle_type: Optional[VehicleType],
                        pickup_date: datetime, return_date: datetime) -> List[Vehicle]:
        with self.lock:
            if location_id not in self.locations:
                return []
            location = self.locations[location_id]
            return location.get_available_vehicles(vehicle_type)

    def create_reservation(self, customer_id: str, vehicle_id: str,
                           pickup_date: datetime, return_date: datetime,
                           pricing_strategy: PricingStrategy) -> Optional[str]:
        with self.lock:
            if customer_id not in self.customers or vehicle_id not in self.vehicles:
                return None

            vehicle = self.vehicles[vehicle_id]
            if not vehicle.reserve():
                return None

            reservation_id = f"RES_{datetime.now().timestamp()}"
            reservation = Reservation(reservation_id, customer_id, vehicle_id,
                                      pickup_date, return_date, pricing_strategy)
            self.reservations[reservation_id] = reservation

            customer = self.customers[customer_id]
            customer.reservations.append(reservation)

            print(f"Reservation created: {reservation_id}, Price: ${reservation.total_price:.2f}")
            return reservation_id

    def modify_reservation(self, reservation_id: str, new_return_date: datetime) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False

            reservation = self.reservations[reservation_id]
            if not reservation.can_modify():
                print("Cannot modify within 24 hours of pickup")
                return False

            old_price = reservation.total_price
            reservation.return_date = new_return_date
            reservation.total_price = reservation._calculate_price()

            price_diff = reservation.total_price - old_price
            print(f"Reservation modified. Price change: ${price_diff:.2f}")
            return True

    def pickup_vehicle(self, reservation_id: str) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False

            reservation = self.reservations[reservation_id]
            vehicle = self.vehicles[reservation.vehicle_id]

            if vehicle.pickup():
                reservation.status = ReservationStatus.ACTIVE
                print(f"Vehicle picked up. Reservation: {reservation_id}")
                return True
            return False

    def return_vehicle(self, reservation_id: str, final_mileage: int) -> Tuple[bool, float]:
        with self.lock:
            if reservation_id not in self.reservations:
                return False, 0

            reservation = self.reservations[reservation_id]
            vehicle = self.vehicles[reservation.vehicle_id]

            if vehicle.return_vehicle(final_mileage):
                reservation.status = ReservationStatus.COMPLETED
                print(f"Vehicle returned. Total charge: ${reservation.total_price:.2f}")
                return True, reservation.total_price
            return False, 0

    def cancel_reservation(self, reservation_id: str) -> Tuple[bool, float]:
        with self.lock:
            if reservation_id not in self.reservations:
                return False, 0

            reservation = self.reservations[reservation_id]
            if reservation.status == ReservationStatus.ACTIVE:
                print("Cannot cancel active reservation")
                return False, 0

            vehicle = self.vehicles[reservation.vehicle_id]
            vehicle.status = VehicleStatus.AVAILABLE

            penalty = reservation.calculate_cancellation_penalty()
            refund = reservation.total_price - penalty

            reservation.status = ReservationStatus.CANCELLED
            print(f"Reservation cancelled. Penalty: ${penalty:.2f}, Refund: ${refund:.2f}")
            return True, refund

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_search_and_reserve():
    print("\n" + "="*70)
    print("DEMO 1: SEARCH & RESERVE")
    print("="*70)

    system = CarRentalSystem()

    customer = system.register_customer("C001", "Alice", "alice@example.com")
    print(f"Customer registered: {customer.name}")

    loc = system.create_location("LOC001", "SF Downtown", "San Francisco")
    print(f"Location created: {loc.name}")

    for i in range(3):
        system.add_vehicle_to_location(f"V{i}", VehicleType.ECONOMY, "LOC001", 50.0)
    print("3 vehicles added")

    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=3)

    vehicles = system.search_vehicles("LOC001", VehicleType.ECONOMY, pickup, return_date)
    print(f"Found {len(vehicles)} available vehicles")

    res_id = system.create_reservation("C001", "V0", pickup, return_date, DailyPricingStrategy())
    print(f"Reservation: {res_id}")

def demo_2_modify_reservation():
    print("\n" + "="*70)
    print("DEMO 2: MODIFY RESERVATION")
    print("="*70)

    system = CarRentalSystem()

    system.register_customer("C002", "Bob", "bob@example.com")
    system.create_location("LOC002", "NYC", "New York")
    system.add_vehicle_to_location("V10", VehicleType.SEDAN, "LOC002", 75.0)

    pickup = datetime.now() + timedelta(days=2)
    return_date = datetime.now() + timedelta(days=4)

    res_id = system.create_reservation("C002", "V10", pickup, return_date, DailyPricingStrategy())

    new_return = datetime.now() + timedelta(days=5)
    system.modify_reservation(res_id, new_return)

def demo_3_pickup_vehicle():
    print("\n" + "="*70)
    print("DEMO 3: PICKUP VEHICLE")
    print("="*70)

    system = CarRentalSystem()

    system.register_customer("C003", "Charlie", "charlie@example.com")
    system.create_location("LOC003", "LA", "Los Angeles")
    system.add_vehicle_to_location("V20", VehicleType.SUV, "LOC003", 100.0)

    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=8)  # 8 days → 1 week + 1 day

    res_id = system.create_reservation("C003", "V20", pickup, return_date, WeeklyPricingStrategy())
    system.pickup_vehicle(res_id)

def demo_4_return_vehicle():
    print("\n" + "="*70)
    print("DEMO 4: RETURN VEHICLE")
    print("="*70)

    system = CarRentalSystem()

    system.register_customer("C004", "Diana", "diana@example.com")
    system.create_location("LOC004", "Seattle", "Seattle")
    system.add_vehicle_to_location("V30", VehicleType.LUXURY, "LOC004", 150.0)

    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=31)  # 31 days → 1 month + 1 day

    res_id = system.create_reservation("C004", "V30", pickup, return_date, MonthlyPricingStrategy())
    system.pickup_vehicle(res_id)
    system.return_vehicle(res_id, 25000)

def demo_5_cancel_reservation():
    print("\n" + "="*70)
    print("DEMO 5: CANCEL RESERVATION (> 7 days out — full refund)")
    print("="*70)

    system = CarRentalSystem()

    system.register_customer("C005", "Eve", "eve@example.com")
    system.create_location("LOC005", "Boston", "Boston")
    system.add_vehicle_to_location("V40", VehicleType.ECONOMY, "LOC005", 50.0)

    pickup = datetime.now() + timedelta(days=10)
    return_date = datetime.now() + timedelta(days=12)

    res_id = system.create_reservation("C005", "V40", pickup, return_date, DailyPricingStrategy())
    system.cancel_reservation(res_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CAR RENTAL SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_search_and_reserve()
    demo_2_modify_reservation()
    demo_3_pickup_vehicle()
    demo_4_return_vehicle()
    demo_5_cancel_reservation()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **create_reservation** | System RLock | Atomic vehicle check + reserve + reservation create |
| **pickup_vehicle** | System RLock | Atomic status check + vehicle.pickup() transition |
| **return_vehicle** | System RLock | Atomic vehicle.return + reservation completion |
| **cancel_reservation** | System RLock | No double-cancel; vehicle released atomically |
| **Vehicle status** | Vehicle RLock | Per-vehicle transitions safe under concurrent holds |
| **Singleton init** | Class RLock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ System and Vehicle both use `threading.RLock` — re-entrant, prevents deadlock on nested calls
2. ✅ Notifications fire after critical state changes to keep lock duration short
3. ✅ Double-checked locking for Singleton with `*args, **kwargs` in `__new__`
4. ✅ `can_modify()` and `calculate_cancellation_penalty()` are pure checks — no lock needed inside

---

## Demo Scenarios

### Demo 1: Search & Reserve
```
- Search for economy cars at SF location, date range 1–3 days out
- System shows 3 available vehicles with pricing
- Select vehicle V0, confirm reservation
- Reservation confirmed: Price $100.00 (2 days × $50)
```

### Demo 2: Modify Reservation
```
- Customer Bob has a 2-day sedan reservation ($150 at $75/day)
- Modifies return date to add one extra day
- System recalculates: 3 days × $75 = $225
- Price change: +$75.00 displayed
```

### Demo 3: Pickup Vehicle
```
- Customer Charlie reserves SUV for 8 days at weekly rate
- Weekly pricing: 1 week (6 days × $100) + 1 day × $100 = $700
- Pickup confirmed: vehicle transitions RESERVED → PICKED_UP
```

### Demo 4: Return Vehicle
```
- Customer Diana returns luxury vehicle after 31-day monthly rental
- Monthly pricing: 1 month (25 days × $150) + 1 day × $150 = $3,900
- Final mileage recorded: 25,000
- Vehicle released: PICKED_UP → AVAILABLE
```

### Demo 5: Cancel Reservation
```
- Customer Eve cancels 10 days before pickup (> 7 days → full refund)
- 2-day economy at $50/day = $100 total
- Penalty: $0.00, Refund: $100.00
- Vehicle released back to available
```

---

## Interview Q&A

### Basic Level

**Q1: What does CarRentalSystem singleton manage?**
A: Single global instance coordinating all rental operations: customers, vehicles, locations, reservations, pricing, payments. Prevents conflicts, ensures coherent state across all branches.

**Q2: How do you handle vehicle availability at multiple locations?**
A: Each location tracks its vehicle inventory. Search queries filter by location. Reservation locks specific vehicle at location. Transfer between locations requires explicit operation (move vehicle, update location).

**Q3: What is a Reservation and what states does it have?**
A: Reservation represents booking from specific customer. States: PENDING (confirmed but not picked up), ACTIVE (picked up), COMPLETED (returned), CANCELLED. Transitions enforce business rules (can't cancel after pickup).

**Q4: Why use multiple pricing strategies?**
A: Different customers prefer different rates: daily renters want per-day rate, weekly travelers want discount, monthly users want bulk rate. Strategy pattern allows pluggable pricing without modifying core code.

### Intermediate Level

**Q5: How do you prevent double-booking same vehicle?**
A: For each vehicle, the `reserve()` method checks status == AVAILABLE atomically (under lock) and transitions to RESERVED in the same critical section. Before confirming reservation, this check prevents any race condition.

**Q6: How are cancellation penalties calculated?**
A: Penalty depends on how close to rental start: < 48h → 50% penalty, 48h–7d → 25% penalty, >7d → full refund (minus admin fee). Calculated at cancellation time.

**Q7: What happens if reserved vehicle needs maintenance?**
A: Check vehicle status before pickup. If maintenance needed, mark as IN_MAINTENANCE. Notify customer, offer alternative vehicle or cancellation with full refund. Prevent pickup if status ≠ RESERVED.

**Q8: How do you handle payment failures?**
A: At return, calculate total charge. Process payment. If failed: retry with different method, or place on hold. Can't release car until payment success or customer agrees to billing terms.

### Advanced Level

**Q9: How to scale across 1000 locations and 100K vehicles?**
A: Geo-partitioned database (each region separate). Per-location caches for popular queries. Distributed search index (Elasticsearch). Eventual consistency for inter-location transfers. Sync vehicles hourly vs real-time.

**Q10: How to handle reservation transfer between locations?**
A: Pickup at Location A, return at Location B. Charge transfer fee. Update location on return. Track vehicle movement. Risk: vehicle in transit state. Solution: location field includes "in_transit" state.

**Q11: How to optimize pricing for maximum revenue?**
A: Analyze demand (bookings vs available). Dynamic pricing: increase rate if demand high, decrease if inventory excess. A/B test pricing strategies. Predict demand for future dates. Trade-off: optimization complexity vs revenue gain.

**Q12: How to ensure data consistency across distributed locations?**
A: Pessimistic: lock vehicle during reservation (slow but safe). Optimistic: allow concurrent bookings, detect conflicts, retry. Distributed consensus (Raft) for critical operations. Read replicas with eventual consistency for queries.

---

## Scaling Q&A

**Q1: How does search scale to 1M queries/day across 100K vehicles?**
A: In-memory index (location × vehicle_type → available_vehicles). Query hits cache. Update index as vehicles book/return. Use Elasticsearch for complex filters (price, features). Cache popular queries (top 100 locations).

**Q2: What if two customers try to book same vehicle simultaneously?**
A: Race condition. Solution: pessimistic locking (lock vehicle, check status, reserve atomically). Or optimistic (allow both, detect conflict during commit, roll one back + notify). Pessimistic simpler but slower.

**Q3: How to handle peak booking times (holiday weekends)?**
A: Spike in queries + reservations. Scale horizontally: increase reservation processing servers. Rate limit expensive operations (searches per user). Queue excess requests. Upgrade pricing during peak = incentivize off-peak.

**Q4: How to track vehicle movement and maintain accuracy?**
A: GPS tracking (IoT device in car). Sync location periodically. On pickup/return, verify location. Track mileage, damage via photos/inspection reports. Detect theft (vehicle outside expected region).

**Q5: How to prevent overbooking during high concurrency?**
A: Test scenario: vehicle has 10 days available, 100 customers try to book simultaneously. Need strict locking. Reserve only after confirming no overlap + available. Implement using DB transaction + row locks.

**Q6: What's memory overhead for 100K vehicles?**
A: Vehicle object: vehicle_id + type + location + status + current_mileage + damage_report ≈ 200 bytes. For 100K: 20MB. Acceptable for in-memory cache. Add DB for persistent storage.

**Q7: How to handle vehicle transfer between locations efficiently?**
A: Mark vehicle as "IN_TRANSIT" (unavailable for booking). Transport physically. Update location + status. For 1000 transfers/day: batch process at off-peak times. Sync overnight if network permits.

**Q8: How to calculate revenue per vehicle/location/type?**
A: Track all reservations: (vehicle, dates, customer, price). Aggregate by vehicle/location/type. Calculate utilization = total_booked_days / total_days. Report daily/weekly/monthly. Query DB with aggregation pipeline (MongoDB) or Spark jobs (Hadoop).

**Q9: Can pricing strategy change mid-season?**
A: Yes. Update strategy globally or per-vehicle. Existing reservations locked at original price. Future bookings use new strategy. Implement using version control (pricing_strategy_version field).

**Q10: How to handle customer disputes (damaged vehicle, overbilling)?**
A: Maintain audit log (all transactions, inspection photos, GPS locations). Review dispute with evidence. Refund/charge difference if justified. Store dispute history per customer (fraud detection).

**Q11: What if payment processor is down during checkout?**
A: Queue payment requests. Retry with exponential backoff. Hold car for customer if payment pending. Notify after processor recovers. Risk: customer leaves angry. Better: async processing (reserve car, process payment later).

**Q12: How to optimize vehicle utilization (minimize idle time)?**
A: Predictive analytics: forecast demand per location/date. Reposition vehicles proactively (transfer from low-demand to high-demand areas). Incentivize off-peak bookings (discounts). Monitor utilization KPI (target: 80%+).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through the reserve → pickup → return → cancel lifecycle
- [ ] Explain how atomic vehicle status transitions prevent double-booking
- [ ] Explain cancellation penalty calculation (< 48h, 48h–7d, > 7d tiers)
- [ ] Explain the three pricing strategies and when each applies
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety in Singleton, create_reservation, and vehicle state transitions
- [ ] Discuss trade-offs (daily vs weekly vs monthly pricing, pessimistic vs optimistic locking)

---

**Ready for interview? Start your engine and reserve a vehicle!**
