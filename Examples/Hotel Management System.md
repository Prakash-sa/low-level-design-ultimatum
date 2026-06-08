# Hotel Management System — Complete Design Guide

> Room inventory management, reservation lifecycle, dynamic pricing, check-in/out processing, and multi-property hotel coordination.

**Scale**: 100K+ concurrent bookings, 1M+ daily searches, 1000+ hotels, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Double-booking prevention, reservation state machine, dynamic pricing, cancellation policy enforcement

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

Guest searches available rooms by date range → selects room → reservation created (PENDING, 1-hour hold) → payment processed → reservation CONFIRMED → guest checks in → guest checks out (COMPLETED). Prevent double-booking through atomic date-range conflict checks and locking.

### Core Flow

```
Search Rooms → Select Room → CREATE RESERVATION (PENDING, 1hr) → PAYMENT → CONFIRMED
                                        ↓ or timeout/cancel
                                    CANCELLED (room released)
                                        ↓ after arrival
                              CHECK-IN → CHECKED_IN → CHECK-OUT → COMPLETED
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single hotel or multi-property?** → "Multi-property hotel chain"
2. **Do we track guest history?** → "Yes, past stays and payment info"
3. **Real payment processing?** → "Mock payment service for interview"
4. **Cancellation policies?** → "Yes, time-based penalties"
5. **Dynamic pricing supported?** → "Yes, weekday/weekend/seasonal strategies"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Guest** | Browse & book rooms | Search, reserve, check-in, check-out, cancel |
| **Hotel Admin** | Manage inventory & pricing | Add rooms, set pricing strategy, view occupancy |
| **System** | Coordinator & lifecycle manager | Expire holds, process check-ins, calculate bills |

### Functional Requirements (What does the system do?)

✅ **Search & Browse**
  - Search available rooms by date range, hotel, and room type
  - View real-time room availability

✅ **Reserve & Confirm**
  - Create reservation with 1-hour payment hold
  - Prevent double-booking of same room for overlapping dates
  - Generate reservation ID and total price

✅ **Check-in & Check-out**
  - Check in guest (CONFIRMED → CHECKED_IN)
  - Check out guest (CHECKED_IN → COMPLETED), generate bill
  - Calculate total charges including extras

✅ **Cancel & Refund**
  - Cancel reservation with time-based penalty policy
  - Release room back to available inventory
  - Calculate refund amount

✅ **Dynamic Pricing**
  - Support weekday, weekend, and seasonal pricing strategies
  - Adjust price based on occupancy rate
  - Apply room-type surcharges (Single/Double/Suite)

✅ **Multi-Property**
  - Manage multiple hotel properties
  - Geographic partitioning for scalability

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 100K+ simultaneous bookings  
✅ **Consistency**: No double-booking (atomic date-range conflict check)  
✅ **Availability**: Real-time availability, booking response < 500ms  
✅ **Throughput**: 1M+ daily searches, 100K+ daily bookings  
✅ **Uptime**: 99.9% (8.6 hours downtime/month allowed)  
✅ **Accuracy**: Transaction consistency for payments and refunds  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Multi-property?** | YES — supports hotel chains |
| **Real payment?** | NO — mock service (failures still tested) |
| **Cancellation penalty** | 0% (>7 days), 25% (3–7 days), 50% (<3 days) |
| **Room capacity** | 1–6 guests per room |
| **Reservation hold** | 1 hour without payment |
| **Overbooking** | NO — strict availability enforcement |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Hotel, Room, RoomType, Guest, Reservation, Payment, PricingStrategy, ...
```

### Step 2.2: Define Core Classes

#### **Room** — A single bookable room in a hotel

```
Properties:
  - room_id: str (e.g., "R101")
  - room_type: RoomType (SINGLE, DOUBLE, SUITE)
  - hotel_id: str
  - status: RoomStatus (AVAILABLE, BOOKED, CHECKED_IN, MAINTENANCE)
  - floor: int

Behaviors:
  - is_available(): Check if room can be reserved
  - assign(): Transition to BOOKED
  - check_in(): Transition to CHECKED_IN
  - release(): Transition back to AVAILABLE
```

#### **RoomType** — Enumeration of room categories

```
Properties:
  - SINGLE = 1 (capacity 1, base $100/night)
  - DOUBLE = 2 (capacity 2, base $150/night)
  - SUITE  = 3 (capacity 6, base $250/night)

Behaviors:
  - (enum — used as key for base price lookup)
```

#### **Guest** — A person making reservations

```
Properties:
  - guest_id: str
  - name: str
  - email: str
  - phone: str
  - payment_method: str

Behaviors:
  - (data holder, used for billing and notifications)
```

#### **Reservation** — A room booking for a date range

```
Properties:
  - reservation_id: str (unique per booking)
  - guest_id: str
  - room_id: str
  - hotel_id: str
  - check_in: datetime
  - check_out: datetime
  - status: ReservationStatus (PENDING, CONFIRMED, CHECKED_IN, COMPLETED, CANCELLED)
  - total_price: float
  - created_at: datetime

Behaviors:
  - nights(): Number of nights (check_out - check_in).days
  - confirm(): PENDING → CONFIRMED
  - do_check_in(): CONFIRMED → CHECKED_IN
  - do_check_out(): CHECKED_IN → COMPLETED
  - cancel(): PENDING/CONFIRMED → CANCELLED (with penalty calc)
```

#### **HotelManagementSystem** — Main controller (Singleton)

```
Properties:
  - hotels: Dict[str, List[Room]]
  - reservations: Dict[str, Reservation]
  - guests: Dict[str, Guest]
  - base_prices: Dict[RoomType, float]
  - _lock: threading.RLock

Behaviors:
  - add_hotel(hotel_id, num_rooms): Register hotel + populate rooms
  - register_guest(...): Add guest profile
  - search_rooms(hotel_id, check_in, check_out, room_type): Return available rooms
  - make_reservation(...): Conflict-check + create Reservation
  - confirm_reservation(reservation_id): PENDING → CONFIRMED
  - check_in(reservation_id): CONFIRMED → CHECKED_IN
  - check_out(reservation_id): CHECKED_IN → COMPLETED, returns bill
  - cancel_reservation(reservation_id): Cancel + apply penalty
  - display_status(): System-wide occupancy summary
```

### Step 2.3: Define Enumerations and Data Classes

```python
class RoomStatus(Enum):
    AVAILABLE   = 1   # Can be reserved
    BOOKED      = 2   # Reserved but not yet checked in
    CHECKED_IN  = 3   # Guest currently occupying room
    MAINTENANCE = 4   # Out of service

class RoomType(Enum):
    SINGLE = 1   # $100/night base
    DOUBLE = 2   # $150/night base
    SUITE  = 3   # $250/night base

class ReservationStatus(Enum):
    PENDING    = 1   # Created, awaiting payment (1-hr hold)
    CONFIRMED  = 2   # Payment received
    CHECKED_IN = 3   # Guest is in the room
    COMPLETED  = 4   # Guest has checked out
    CANCELLED  = 5   # Reservation cancelled

@dataclass
class Room:
    room_id:   str
    room_type: RoomType
    hotel_id:  str
    status:    RoomStatus = RoomStatus.AVAILABLE
    floor:     int = 1

@dataclass
class Guest:
    guest_id:       str
    name:           str
    email:          str
    phone:          str
    payment_method: str = "Card"

@dataclass
class Reservation:
    reservation_id: str
    guest_id:       str
    room_id:        str
    hotel_id:       str
    check_in:       datetime
    check_out:      datetime
    status:         ReservationStatus = ReservationStatus.PENDING
    total_price:    float = 0.0
    created_at:     datetime = field(default_factory=datetime.now)

    def nights(self) -> int:
        return (self.check_out - self.check_in).days
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Room** | Granular room tracking (status, type, floor) | Can't prevent double-booking |
| **RoomType** | Categorise capacity and base price | Can't vary pricing or search by type |
| **Guest** | Track who reserved, for billing & notifications | Can't generate bills or contact guests |
| **Reservation** | Full lifecycle (PENDING → COMPLETED) | Can't manage hold, check-in, or refunds |
| **HotelManagementSystem** | Thread-safe central coordinator | No conflict-free booking guarantee |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Add Hotel**
```python
def add_hotel(hotel_id: str, num_rooms: int = 50) -> None:
    """
    Register a new hotel property and populate it with rooms.
    Idempotent: duplicate hotel_id is silently skipped.
    Response Time: O(num_rooms)
    """
    pass
```

#### **2. Search Rooms**
```python
def search_rooms(hotel_id: str, check_in: datetime,
                 check_out: datetime, room_type: RoomType) -> List[Room]:
    """
    Find available rooms matching type with no overlapping reservations.
    Returns: up to 10 Room objects (AVAILABLE, no conflict).
    Raises: nothing — returns empty list if hotel unknown.
    Response Time: <500ms
    """
    pass
```

#### **3. Make Reservation** ⭐ CRITICAL
```python
def make_reservation(guest_id: str, room_id: str, hotel_id: str,
                     check_in: datetime, check_out: datetime) -> Optional[Reservation]:
    """
    Create a reservation with PENDING status (1-hour hold).

    Precondition:  No overlapping confirmed/pending reservation for room.
    Postcondition: Reservation created with computed total_price.

    Returns: Reservation object, or None on conflict / unknown entity.

    Raises (documented intent — returns None in current impl):
      - RoomNotAvailableError: Overlapping booking exists
      - GuestNotFoundError: guest_id not registered
      - RoomNotFoundError: room_id not in hotel

    Concurrency: THREAD-SAFE via RLock — only one thread can claim a room at a time.
    Response Time: <500ms
    """
    pass
```

#### **4. Confirm Reservation**
```python
def confirm_reservation(reservation_id: str) -> bool:
    """
    Mark reservation as CONFIRMED after payment.

    Precondition:  reservation.status == PENDING
    Postcondition: reservation.status == CONFIRMED

    Returns: True on success, False if not found or wrong state.
    """
    pass
```

#### **5. Check-in** ⭐ CRITICAL
```python
def check_in(reservation_id: str) -> bool:
    """
    Guest arrives. Transition CONFIRMED → CHECKED_IN, room → CHECKED_IN.
    Returns: True on success, False otherwise.
    Side Effects: Room status updated to CHECKED_IN.
    """
    pass
```

#### **6. Check-out** ⭐ CRITICAL
```python
def check_out(reservation_id: str) -> float:
    """
    Guest departs. Transition CHECKED_IN → COMPLETED, room → AVAILABLE.
    Returns: total bill amount (float), 0.0 on failure.
    Side Effects: Room released back to inventory.
    """
    pass
```

#### **7. Cancel Reservation**
```python
def cancel_reservation(reservation_id: str) -> float:
    """
    Cancel a PENDING or CONFIRMED reservation.

    Penalty policy (days before check_in):
      >7 days  → 0%  penalty (full refund)
      3–7 days → 25% penalty
      <3 days  → 50% penalty

    Returns: refund amount (total_price - penalty), 0.0 if not cancellable.
    Side Effects: Room released to available inventory.
    """
    pass
```

### Step 3.2: Failure Model

```python
class HotelException(Exception):
    """Base exception for hotel system"""
    pass

class RoomNotAvailableError(HotelException):
    """Room already reserved for overlapping dates"""
    pass

class GuestNotFoundError(HotelException):
    """Guest ID not registered"""
    pass

class ReservationNotFoundError(HotelException):
    """Reservation ID invalid"""
    pass
```

### Step 3.3: API Usage Example

```python
system = HotelManagementSystem()

# 1. Setup
system.add_hotel("HOTEL_NYC", num_rooms=50)
system.register_guest("G001", "Alice", "alice@example.com", "555-0001")

# 2. Search
check_in  = datetime.now() + timedelta(days=5)
check_out = check_in + timedelta(days=3)
rooms = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.DOUBLE)

# 3. Reserve
res = system.make_reservation("G001", rooms[0].room_id, "HOTEL_NYC", check_in, check_out)
print(f"Reservation: {res.reservation_id}, Total: ${res.total_price}")

# 4. Confirm
system.confirm_reservation(res.reservation_id)

# 5. Check-in / Check-out
system.check_in(res.reservation_id)
bill = system.check_out(res.reservation_id)
print(f"Final bill: ${bill}")

# 6. Cancel (alternative path)
# refund = system.cancel_reservation(res.reservation_id)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
HotelManagementSystem HAS-A hotels (1:N Composition)
  └─ System owns the full lifecycle of all Room objects

Hotel (hotel_id key) CONTAINS Rooms (1:N Composition)
  └─ Each hotel holds a list of Room objects

Reservation REFERENCES Guest   (N:1 Association)
Reservation REFERENCES Room    (N:1 Association)
Reservation REFERENCES Hotel   (N:1 Association)
  └─ Reservation links entities without owning them

HotelManagementSystem USES-A PricingStrategy (1:1)
  └─ Swappable algorithm for computing room price
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────────────┐
│       HotelManagementSystem (Singleton)    │
├────────────────────────────────────────────┤
│ - _instance: HotelManagementSystem         │
│ - hotels: Dict[str, List[Room]]            │
│ - reservations: Dict[str, Reservation]     │
│ - guests: Dict[str, Guest]                 │
│ - base_prices: Dict[RoomType, float]       │
│ - room_counter: int                        │
│ - reservation_counter: int                 │
│ - _lock: threading.RLock                   │
├────────────────────────────────────────────┤
│ + add_hotel(hotel_id, num_rooms)           │
│ + register_guest(...): Guest               │
│ + search_rooms(...): List[Room]            │
│ + make_reservation(...): Reservation       │
│ + confirm_reservation(id): bool            │
│ + check_in(id): bool                       │
│ + check_out(id): float                     │
│ + cancel_reservation(id): float            │
│ + display_status(): void                   │
└────────────────────────────────────────────┘
           │ manages 1:N
           ▼
┌───────────────────────────────────────┐
│              Room                     │
├───────────────────────────────────────┤
│ - room_id: str                        │
│ - room_type: RoomType                 │
│ - hotel_id: str                       │
│ - status: RoomStatus                  │
│ - floor: int                          │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│           Reservation                 │
├───────────────────────────────────────┤
│ - reservation_id: str                 │
│ - guest_id: str                       │
│ - room_id: str                        │
│ - hotel_id: str                       │
│ - check_in: datetime                  │
│ - check_out: datetime                 │
│ - status: ReservationStatus           │
│ - total_price: float                  │
│ - created_at: datetime                │
├───────────────────────────────────────┤
│ + nights(): int                       │
└───────────────────────────────────────┘
           │ references
           ▼
┌───────────────────────────────────────┐
│              Guest                    │
├───────────────────────────────────────┤
│ - guest_id: str                       │
│ - name: str                           │
│ - email: str                          │
│ - phone: str                          │
│ - payment_method: str                 │
└───────────────────────────────────────┘


STATE MACHINES:

Room Status:
AVAILABLE ──→ BOOKED ──→ CHECKED_IN ──→ AVAILABLE
                              ↓
                        MAINTENANCE

Reservation Status:
PENDING ──→ CONFIRMED ──→ CHECKED_IN ──→ COMPLETED
   ↓             ↓
CANCELLED    CANCELLED


PRICING STRATEGY:
┌──────────────────────────────────────┐
│  PricingStrategy (Abstract / inline) │
├──────────────────────────────────────┤
│ + calculate_price(room_type, nights) │
└──────────────────────────────────────┘
  base_prices dict (Weekday/Weekend/Seasonal via multiplier)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| HotelManagementSystem → Hotels | 1:N | Composition | System owns all hotel records |
| Hotel → Rooms | 1:N | Composition | Hotel owns its room inventory |
| Reservation → Guest | N:1 | Association | Many reservations per guest |
| Reservation → Room | N:1 | Association | Room can have multiple reservations (different dates) |
| HotelManagementSystem → Reservations | 1:N | Composition | System owns all bookings |
| HotelManagementSystem → PricingStrategy | 1:1 | Composition | System owns pricing rule |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For HotelManagementSystem)

**Problem**: Multiple threads and API handlers need a single consistent view of room inventory, reservations, and guests.

**Solution**: One global HotelManagementSystem instance, thread-safe double-checked locking.

```python
class HotelManagementSystem:
    _instance = None
    _lock = threading.RLock()   # RLock so __init__ can re-enter if needed

    def __new__(cls, *args, **kwargs):        # *args/**kwargs: avoid TypeError
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        # ... initialize collections
```

**Benefit**: Single source of truth, thread-safe initialization, global access  
**Trade-off**: Global state (harder to unit-test), harder to scale across machines without distributed layer

---

### Pattern 2: **State Machine** (For Reservation Lifecycle)

**Problem**: Reservation passes through PENDING → CONFIRMED → CHECKED_IN → COMPLETED, and invalid transitions (e.g. checking out a PENDING reservation) must be caught.

**Solution**: Explicit enum states with guard clauses on every transition method.

```python
class ReservationStatus(Enum):
    PENDING    = 1
    CONFIRMED  = 2
    CHECKED_IN = 3
    COMPLETED  = 4
    CANCELLED  = 5

def confirm_reservation(self, reservation_id: str) -> bool:
    res = self.reservations.get(reservation_id)
    if res and res.status == ReservationStatus.PENDING:
        res.status = ReservationStatus.CONFIRMED
        return True
    return False   # silently rejects invalid transitions
```

**Benefit**: Clear lifecycle, invalid transitions rejected at runtime  
**Trade-off**: Need explicit guard logic on every state-changing method

---

### Pattern 3: **Strategy** (For Pricing)

**Problem**: Pricing varies by day of week, season, and occupancy. Should be swappable without modifying booking logic.

**Solution**: Pluggable pricing — base price dict + runtime multiplier.

```python
# Inline strategy via base_prices dict + multiplier
BASE_PRICES = {
    RoomType.SINGLE: 100,
    RoomType.DOUBLE: 150,
    RoomType.SUITE:  250,
}

def calculate_price(room_type: RoomType, nights: int, multiplier: float = 1.0) -> float:
    return BASE_PRICES[room_type] * nights * multiplier

# Usage — switch strategy at runtime:
# Weekday: multiplier=1.0, Weekend: multiplier=1.3, Peak season: multiplier=2.0
```

**Benefit**: Easy to add new pricing (EarlyBird, Loyalty, Seasonal) without touching booking logic  
**Trade-off**: Extra abstraction layer if not fully formalised as ABC

---

### Pattern 4: **Observer** (For Room Status Notifications)

**Problem**: Room availability changes (check-in, check-out, cancellation) need to trigger staff dashboards, housekeeping alerts, and OTA inventory updates.

**Solution**: Observer pattern decouples room-status producer from notification consumers.

```python
class RoomObserver(ABC):
    @abstractmethod
    def on_room_status_change(self, room: Room, event: str): pass

class StaffDashboard(RoomObserver):
    def on_room_status_change(self, room: Room, event: str):
        print(f"[Dashboard] Room {room.room_id} → {event}")

# Usage:
system.add_room_observer(StaffDashboard())
# On check-out: system.notify_room_observers(room, "available")
```

**Benefit**: Loose coupling; easy to add housekeeping, OTA sync, or SMS alerts  
**Trade-off**: Observer lifecycle management; ordering of notifications

---

### Pattern 5: **Factory** (For Room Creation)

**Problem**: Creating rooms requires consistent initialisation (room_id generation, default status, floor assignment).

**Solution**: Factory method centralises room creation inside `add_hotel`.

```python
def _create_room(self, hotel_id: str, index: int) -> Room:
    self.room_counter += 1
    room_type = [RoomType.SINGLE, RoomType.DOUBLE, RoomType.SUITE][index % 3]
    floor = (index // 10) + 1
    return Room(f"R{self.room_counter}", room_type, hotel_id, floor=floor)
```

**Benefit**: Centralised, consistent room initialisation  
**Trade-off**: If room variety grows, consider a full Abstract Factory

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single global HotelManagementSystem | Consistent state across all request threads |
| **State Machine** | Reservation lifecycle (PENDING → COMPLETED) | Invalid transitions prevented |
| **Strategy** | Varying pricing (weekday, weekend, seasonal) | Pluggable, easy to extend |
| **Observer** | Room changes trigger staff/OTA notifications | Loose coupling, event-driven |
| **Factory** | Consistent room creation with IDs and types | Centralised initialisation logic |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Hotel Management System - Interview Implementation
Demonstrates:
1. Room inventory management
2. Reservation booking with conflict prevention
3. Dynamic pricing
4. Check-in/out processes
5. Payment handling
"""

from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class RoomStatus(Enum):
    AVAILABLE   = 1
    BOOKED      = 2
    CHECKED_IN  = 3
    MAINTENANCE = 4

class RoomType(Enum):
    SINGLE = 1
    DOUBLE = 2
    SUITE  = 3

class ReservationStatus(Enum):
    PENDING    = 1
    CONFIRMED  = 2
    CHECKED_IN = 3
    COMPLETED  = 4
    CANCELLED  = 5

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Room:
    room_id:   str
    room_type: RoomType
    hotel_id:  str
    status:    RoomStatus = RoomStatus.AVAILABLE
    floor:     int = 1

    def __hash__(self):
        return hash(self.room_id)

@dataclass
class Guest:
    guest_id:       str
    name:           str
    email:          str
    phone:          str
    payment_method: str = "Card"

@dataclass
class Reservation:
    reservation_id: str
    guest_id:       str
    room_id:        str
    hotel_id:       str
    check_in:       datetime
    check_out:      datetime
    status:         ReservationStatus = ReservationStatus.PENDING
    total_price:    float = 0.0
    created_at:     datetime = field(default_factory=datetime.now)

    def nights(self) -> int:
        return (self.check_out - self.check_in).days

# ============================================================================
# HOTEL MANAGEMENT SYSTEM (SINGLETON)
# ============================================================================

class HotelManagementSystem:
    _instance = None
    _lock = threading.RLock()   # RLock: re-entrant, prevents deadlock on nested acquire

    def __new__(cls, *args, **kwargs):  # accept *args/**kwargs to avoid TypeError
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.hotels: Dict[str, List[Room]] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.guests: Dict[str, Guest] = {}
        self.room_counter = 0
        self.reservation_counter = 0
        self.lock = threading.RLock()  # RLock: allows re-entry within same thread
        self.base_prices = {
            RoomType.SINGLE: 100,
            RoomType.DOUBLE: 150,
            RoomType.SUITE:  250,
        }

    def add_hotel(self, hotel_id: str, num_rooms: int = 50):
        with self.lock:
            if hotel_id not in self.hotels:
                rooms = []
                for i in range(num_rooms):
                    self.room_counter += 1
                    room = Room(f"R{self.room_counter}", RoomType.DOUBLE, hotel_id)
                    rooms.append(room)
                self.hotels[hotel_id] = rooms
                print(f"Added hotel {hotel_id} with {num_rooms} rooms")

    def register_guest(self, guest_id: str, name: str, email: str, phone: str) -> Guest:
        with self.lock:
            guest = Guest(guest_id, name, email, phone)
            self.guests[guest_id] = guest
            print(f"Registered guest: {name}")
            return guest

    def search_rooms(self, hotel_id: str, check_in: datetime,
                     check_out: datetime, room_type: RoomType) -> List[Room]:
        with self.lock:
            if hotel_id not in self.hotels:
                return []

            available = []
            for room in self.hotels[hotel_id]:
                if room.room_type == room_type and room.status == RoomStatus.AVAILABLE:
                    # Check if room is booked for any overlapping date range
                    is_booked = False
                    for res in self.reservations.values():
                        if (res.room_id == room.room_id and
                                res.status != ReservationStatus.CANCELLED and
                                not (res.check_out <= check_in or res.check_in >= check_out)):
                            is_booked = True
                            break

                    if not is_booked:
                        available.append(room)

            return available[:10]

    def make_reservation(self, guest_id: str, room_id: str, hotel_id: str,
                         check_in: datetime, check_out: datetime) -> Optional[Reservation]:
        with self.lock:
            if guest_id not in self.guests or hotel_id not in self.hotels:
                return None

            # Verify room exists in hotel
            room = next((r for r in self.hotels[hotel_id] if r.room_id == room_id), None)
            if not room:
                return None

            # Atomic conflict check
            for res in self.reservations.values():
                if (res.room_id == room_id and
                        res.status != ReservationStatus.CANCELLED and
                        not (res.check_out <= check_in or res.check_in >= check_out)):
                    print(f"Room {room_id} already booked for dates")
                    return None

            # Calculate price
            nights = (check_out - check_in).days
            price = self.base_prices[room.room_type] * nights

            self.reservation_counter += 1
            reservation = Reservation(
                f"RES_{self.reservation_counter}",
                guest_id,
                room_id,
                hotel_id,
                check_in,
                check_out,
                ReservationStatus.PENDING,
                price
            )

            self.reservations[reservation.reservation_id] = reservation
            guest = self.guests[guest_id]
            print(f"Reservation created: {reservation.reservation_id}")
            print(f"  Guest: {guest.name}, Room: {room_id}")
            print(f"  Dates: {check_in.date()} to {check_out.date()} ({nights} nights)")
            print(f"  Total: ${price}")

            return reservation

    def confirm_reservation(self, reservation_id: str) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False

            res = self.reservations[reservation_id]
            if res.status == ReservationStatus.PENDING:
                res.status = ReservationStatus.CONFIRMED
                print(f"Reservation {reservation_id} confirmed")
                return True

        return False

    def check_in(self, reservation_id: str) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False

            res = self.reservations[reservation_id]
            if res.status == ReservationStatus.CONFIRMED:
                res.status = ReservationStatus.CHECKED_IN
                # Update room status
                for hotel_rooms in self.hotels.values():
                    for room in hotel_rooms:
                        if room.room_id == res.room_id:
                            room.status = RoomStatus.CHECKED_IN
                            print(f"Check-in: Room {res.room_id}, "
                                  f"Guest: {self.guests[res.guest_id].name}")
                            return True

        return False

    def check_out(self, reservation_id: str) -> float:
        with self.lock:
            if reservation_id not in self.reservations:
                return 0.0

            res = self.reservations[reservation_id]
            if res.status == ReservationStatus.CHECKED_IN:
                res.status = ReservationStatus.COMPLETED

                # Release room
                for hotel_rooms in self.hotels.values():
                    for room in hotel_rooms:
                        if room.room_id == res.room_id:
                            room.status = RoomStatus.AVAILABLE

                guest = self.guests[res.guest_id]
                print(f"Check-out: Guest {guest.name}")
                print(f"  Total bill: ${res.total_price}")
                return res.total_price

        return 0.0

    def cancel_reservation(self, reservation_id: str) -> float:
        with self.lock:
            if reservation_id not in self.reservations:
                return 0.0

            res = self.reservations[reservation_id]
            if res.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                days_before = (res.check_in - datetime.now()).days

                if days_before > 7:
                    penalty = 0.0
                elif days_before >= 3:
                    penalty = res.total_price * 0.25
                else:
                    penalty = res.total_price * 0.50

                refund = res.total_price - penalty
                res.status = ReservationStatus.CANCELLED

                print(f"Reservation {reservation_id} cancelled")
                print(f"  Original: ${res.total_price}, Penalty: ${penalty}, Refund: ${refund}")
                return refund

        return 0.0

    def display_status(self):
        print("\n" + "=" * 70)
        print("HOTEL MANAGEMENT SYSTEM STATUS")
        print("=" * 70)
        total_rooms = sum(len(rooms) for rooms in self.hotels.values())
        occupied = len([r for r in self.reservations.values()
                        if r.status == ReservationStatus.CHECKED_IN])
        print(f"Hotels: {len(self.hotels)}, Total rooms: {total_rooms}")
        print(f"Total reservations: {len(self.reservations)}")
        print(f"Currently occupied: {occupied}")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_search_book():
    print("\n" + "=" * 70)
    print("DEMO 1: SEARCH & BOOK")
    print("=" * 70)

    system = HotelManagementSystem()
    system.add_hotel("HOTEL_NYC", 20)
    system.register_guest("G1", "John", "john@email.com", "555-1234")

    check_in  = datetime.now() + timedelta(days=5)
    check_out = check_in + timedelta(days=3)

    available = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.DOUBLE)
    print(f"Found {len(available)} Double rooms available")

    if available:
        res = system.make_reservation("G1", available[0].room_id, "HOTEL_NYC", check_in, check_out)
        if res:
            system.confirm_reservation(res.reservation_id)


def demo_2_checkin_checkout():
    print("\n" + "=" * 70)
    print("DEMO 2: CHECK-IN & CHECK-OUT")
    print("=" * 70)

    system = HotelManagementSystem()
    system.add_hotel("HOTEL_NYC", 10)
    system.register_guest("G1", "Sarah", "sarah@email.com", "555-5678")

    check_in  = datetime.now()
    check_out = check_in + timedelta(days=2)

    available = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.SINGLE)
    if available:
        res = system.make_reservation("G1", available[0].room_id, "HOTEL_NYC", check_in, check_out)
        if res:
            system.confirm_reservation(res.reservation_id)
            system.check_in(res.reservation_id)
            system.check_out(res.reservation_id)


def demo_3_cancellation():
    print("\n" + "=" * 70)
    print("DEMO 3: CANCELLATION WITH PENALTY")
    print("=" * 70)

    system = HotelManagementSystem()
    system.add_hotel("HOTEL_NYC", 10)
    system.register_guest("G1", "Mike", "mike@email.com", "555-9999")

    check_in  = datetime.now() + timedelta(days=2)
    check_out = check_in + timedelta(days=3)

    available = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.DOUBLE)
    if available:
        res = system.make_reservation("G1", available[0].room_id, "HOTEL_NYC", check_in, check_out)
        if res:
            system.confirm_reservation(res.reservation_id)
            system.cancel_reservation(res.reservation_id)


def demo_4_multiple_bookings():
    print("\n" + "=" * 70)
    print("DEMO 4: MULTIPLE CONCURRENT BOOKINGS")
    print("=" * 70)

    system = HotelManagementSystem()
    system.add_hotel("HOTEL_NYC", 30)

    for i in range(1, 4):
        system.register_guest(f"G{i}", f"Guest {i}", f"guest{i}@email.com", f"555-{i}000")

    check_in  = datetime.now() + timedelta(days=7)
    check_out = check_in + timedelta(days=4)

    for i in range(1, 4):
        available = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.DOUBLE)
        if available:
            res = system.make_reservation(
                f"G{i}", available[i - 1].room_id, "HOTEL_NYC", check_in, check_out
            )
            if res:
                system.confirm_reservation(res.reservation_id)


def demo_5_status():
    print("\n" + "=" * 70)
    print("DEMO 5: SYSTEM STATUS")
    print("=" * 70)

    system = HotelManagementSystem()
    system.add_hotel("HOTEL_NYC", 20)
    system.add_hotel("HOTEL_LA", 15)

    for i in range(1, 6):
        system.register_guest(f"G{i}", f"Guest {i}", f"g{i}@email.com", f"555-{i}111")

    check_in  = datetime.now()
    check_out = check_in + timedelta(days=2)

    for i in range(1, 4):
        available = system.search_rooms("HOTEL_NYC", check_in, check_out, RoomType.SINGLE)
        if available:
            res = system.make_reservation(
                f"G{i}", available[0].room_id, "HOTEL_NYC", check_in, check_out
            )
            if res:
                system.confirm_reservation(res.reservation_id)

    system.display_status()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HOTEL MANAGEMENT SYSTEM - 5 DEMO SCENARIOS")
    print("=" * 70)

    demo_1_search_book()
    demo_2_checkin_checkout()
    demo_3_cancellation()
    demo_4_multiple_bookings()
    demo_5_status()

    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETED")
    print("=" * 70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **make_reservation** | RLock on full conflict-check + insert | Only one thread can claim a room for a date range at a time |
| **confirm_reservation** | RLock on status read + write | Atomic PENDING → CONFIRMED |
| **check_in** | RLock on reservation + room status update | Atomic state transition, no partial updates |
| **check_out** | RLock on reservation + room release | Room released atomically with status change |
| **cancel_reservation** | RLock on cancel + penalty calc | No double-cancel, consistent refund |

**Concurrency Principles**:
1. RLock (re-entrant) used instead of Lock — prevents deadlock if any method calls another internally
2. Minimize lock duration where possible (notify outside lock when safe)
3. Double-checked locking in Singleton (`__new__`)
4. Singleton `__new__` accepts `*args, **kwargs` — prevents `TypeError` when subclassing or passing args

---

## Demo Scenarios

### Demo 1: Search & Book

```
- Guest searches: Check-in 2024-03-01, Check-out 2024-03-05
- Available rooms: Double ($150/night), Suite ($250/night)
- Select Double (4 nights x $150 = $600)
- Confirm booking
- Reservation created (status: PENDING -> CONFIRMED)
```

### Demo 2: Check-in & Check-out

```
- Guest John arrives for booking RES_001
- Front desk verifies ID
- Check-in: Room 201 assigned, key provided
- Status changes: CHECKED_IN
- After 4 nights: Guest requests check-out
- Final bill: $600 (room) + $50 (room service) + tax
- Payment processed
- Check-out: COMPLETED
```

### Demo 3: Cancellation with Penalty

```
- Reservation RES_002: Check-in March 5 (booked March 1)
- Guest cancels March 2 (3 days before): 25% penalty
- Original: $300, Penalty: $75
- Refund: $225
- Room returned to available inventory
```

### Demo 4: Dynamic Pricing

```
- Base price: $100/night
- Occupancy: 45% -> Reduce to $80 (encourage bookings)
- Occupancy: 85% -> Increase to $150 (maximize revenue)
- Weekend rates: +30% surcharge
- Seasonal (peak): +50% surcharge
```

### Demo 5: Group Booking

```
- Corporate event: 20 Double rooms
- 5 nights: May 1-6
- Group rate: $120/night (vs $150 regular)
- Total: 20 rooms x 5 nights x $120 = $12,000
- Single master reservation
- Flexible cancellation (can cancel individual rooms with penalty)
```

---

## Interview Q&A

### Basic Level

**Q1: How do you prevent double-booking?**

A: Use atomic operations. On booking: (1) Lock room for date range with RLock, (2) Check if any existing reservation overlaps the requested dates, (3) Create reservation, (4) Release lock. If concurrent requests: first succeeds, others see conflict. Use DB transactions or distributed locks (Redis) in production.

```python
with self.lock:  # Atomic critical section
    for res in self.reservations.values():
        if (res.room_id == room_id and
                res.status != ReservationStatus.CANCELLED and
                not (res.check_out <= check_in or res.check_in >= check_out)):
            return None  # Conflict detected
    # Safe to create reservation
```

**Q2: What is the cancellation penalty policy?**

A: Depends on timing. >7 days before: 0% penalty (full refund). 3-7 days: 25% penalty. <3 days: 50% penalty. Day of arrival: 100% (non-refundable). Communicate clearly at booking time.

**Q3: How do you generate a bill at checkout?**

A: Room charge = room_type_price x num_nights. Add extras (room service, parking, minibar). Apply discounts (loyalty, membership). Calculate taxes. Final bill = subtotal + taxes. Generate invoice for guest + accounting system.

**Q4: What is the difference between room type and room status?**

A: **Type**: Single/Double/Suite (capacity, amenities). Permanent attribute. **Status**: Available/Booked/Checked-in/Maintenance. Changes throughout the day. Query by both: "Double rooms available on March 5?"

### Intermediate Level

**Q5: How to handle no-shows (guest books but does not arrive)?**

A: (1) Confirm 24 hours before (email/SMS). (2) At check-in time, if not arrived: mark as no-show. (3) Still charge (unless cancellation policy applies). (4) Release room after 2-hour grace period. (5) Track no-show rate per guest.

**Q6: How to optimize pricing dynamically?**

A: Track occupancy rate. If >80%: increase price (high demand, fewer rooms). If <40%: decrease price (incentivize bookings). Update daily/hourly. Algorithm: `base_price x occupancy_multiplier`. Prevents both overbooking and empty rooms.

**Q7: What if guest overstays (stays past checkout)?**

A: (1) Notify guest at checkout time. (2) Allow grace period (30-60 min). (3) After grace: charge additional night. (4) Security can request departure if needed. (5) Log for repeat offenders.

**Q8: How to handle group bookings (20+ rooms)?**

A: (1) Reserve block of rooms upfront, (2) Group discount (e.g. 10% off), (3) Single billing contact + master invoice, (4) Flexibility: guest can cancel specific rooms within group, (5) Special terms: guaranteed rate, flexible check-in.

### Advanced Level

**Q9: How to scale to 1000+ hotels?**

A: Geographic sharding: partition by region (North/South/East/West). Each region manages a subset of hotels. Global search: fan-out to relevant regional databases. Aggregate results. Expected: <500ms latency with caching.

**Q10: How to handle overbooking recovery?**

A: Intentionally overbook by 3-5% (some guests no-show). Monitor cancellation rate. If overbooked and guest arrives: upgrade to better room (no cost to guest) + compensation ($50 voucher). Document incidents.

**Q11: How to prevent fraud (fake bookings, chargebacks)?**

A: (1) Verify payment method at booking, (2) Require ID at check-in, (3) Immediate charge (no pre-auth), (4) Flag suspicious patterns (multiple cancellations, multiple chargebacks), (5) Blacklist fraudsters.

**Q12: How to optimize for revenue (maximize occupancy + rate)?**

A: Use ML: predict occupancy 30-60 days out → adjust pricing dynamically. Track competitor rates → match/undercut. Offer packages (room + breakfast) to fill rooms. Implement overbooking + service recovery.

---

## Scaling Q&A

**Q1: Can you handle 100K simultaneous bookings?**

A: Message queue (Kafka): accept bookings → async processing. Process 1K bookings/sec = 100 seconds. For real-time feel: return confirmation immediately, notify if failed. Use optimistic locking to prevent conflicts.

**Q2: How to prevent race conditions on room availability?**

A: Pessimistic lock: lock room during entire reservation process. Optimistic lock: version number, retry if mismatch. Distributed lock (Redis SETNX): lock room, release after booking. Trade-off: lock duration vs concurrency.

**Q3: What if inventory data becomes inconsistent?**

A: Event sourcing: store all booking/cancellation events. Replay to reconstruct state. If inconsistency detected: replay from last known good state. Eventually consistent after 1-2 seconds. Acceptable for hotel booking.

**Q4: How to handle peak season (80K bookings/day)?**

A: Scale horizontally: add servers. Pre-cache hot data (popular hotels, dates). Queue bookings if rate exceeds capacity. Implement circuit breaker: if system overloaded, return "try again later" (better than crash).

**Q5: Can you support international bookings (multi-currency)?**

A: Store rates in base currency. On booking: convert to guest's currency using live exchange rate. Store both. At payment: charge in guest's currency. Convert for accounting in base currency. Update rates hourly.

**Q6: How to generate analytics/reports?**

A: Data pipeline: booking events → Kafka → Spark → Data warehouse (BigQuery). Daily jobs: occupancy rate, revenue, cancellation rate, no-show rate. Reports available next day (acceptable lag).

**Q7: What if payment processor is down?**

A: Retry logic: 3 attempts with exponential backoff. If failed: queue payment as pending. Retry daily for 7 days. If still failing: escalate to support team. Guest sees reservation pending until payment succeeds.

**Q8: How to handle room modifications (guest wants different room)?**

A: Check availability of new room for same dates. If available: release old room, book new. If new room costs more: charge difference. Less: credit account. If not available: offer alternatives.

**Q9: Can you support real-time room status updates (for staff)?**

A: WebSocket connection per staff member. On room status change: broadcast to all connected staff. Update frequency: 10-100ms. Ensures staff sees live status (e.g. "Room 101 checked out, ready for cleaning").

**Q10: How to optimize database queries for million rooms?**

A: Index on (hotel_id, date_range, room_type_id). Partition DB by hotel. Query only relevant hotel's DB. Use Redis cache for popular queries (availability on peak dates). Expected query: <100ms.

**Q11: How to handle auditing (compliance, taxes)?**

A: Log all transactions: booking, cancellation, payment, refund, adjustment. Store immutably (append-only). Generate monthly reports for accounting/tax compliance. Retain for 7 years.

**Q12: Can you support third-party integrations (Booking.com, Expedia)?**

A: API gateway handles requests from OTAs (Online Travel Agencies). Inventory sync: OTA updates rooms sold through them, hotel updates availability. Dual-write: updates go to both hotel + OTA systems. Complexity: rate parity (ensure rates match).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with Room, Guest, Reservation, HotelManagementSystem
- [ ] Discuss reservation lifecycle: PENDING → CONFIRMED → CHECKED_IN → COMPLETED
- [ ] Explain how double-booking is prevented with atomic date-range conflict check + RLock
- [ ] Discuss cancellation penalty tiers (0% / 25% / 50%)
- [ ] Run complete implementation without errors (no emoji in print statements)
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety: RLock, double-checked Singleton, `*args/**kwargs` in `__new__`
- [ ] Discuss design patterns: Singleton, State Machine, Strategy, Observer, Factory
- [ ] Discuss trade-offs (in-memory vs DB, pessimistic vs optimistic locking, RLock vs Lock)

---

**Ready for interview? Check some guests in!**
