# Airline Management System — Complete Design Guide

> Flight scheduling, seat inventory management, booking lifecycle, overbooking prevention, and dynamic pricing.

**Scale**: 500-1,000+ concurrent users, 1M+ flights/day, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Seat hold/confirm lifecycle, overbooking prevention, dynamic pricing, event notifications

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
Customers search flights → hold seat (temporary 5-min reservation) → pay → confirm booking → or hold expires → seat released. Prevent overbooking through atomic seat status transitions and hold timeout management.

### Core Flow
```
Browse Flights → Select Seat → HOLD (5 min) → PAYMENT → CONFIRM (permanent)
                                    ↓ or timeout
                                  EXPIRED (seat released)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system with 500-1K concurrent users"
2. **Do we track passenger history?** → "Yes, past bookings for cancellations"
3. **Multi-airline or single?** → "Single airline"
4. **Real payment processing?** → "Mock payment service for interview"
5. **Cancellations after confirmation?** → "Yes, with refund policies"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Browse & book flights | Search, hold seat, confirm, cancel |
| **Airline Admin** | Manage flights & pricing | Create flights, set pricing strategy, monitor overbooking |
| **System** | Controller & notifications | Expire holds, send emails, update seat status |

### Functional Requirements (What does the system do?)

✅ **Search & Browse**
  - Search flights by route, date, aircraft type
  - View seat inventory with real-time availability
  
✅ **Hold & Reserve**
  - Temporarily hold seat for 5 minutes
  - Prevent double-booking of same seat
  - Generate booking ID & hold expiry time
  
✅ **Confirm & Book**
  - Confirm booking after payment
  - Permanently mark seat as booked
  - Update booking status
  
✅ **Cancel & Release**
  - Cancel confirmed booking
  - Release seat back to available
  - Calculate refund based on policy
  
✅ **Automatic Expiry**
  - Automatically expire holds after 5 minutes
  - Release seat if hold not confirmed
  - Notify passenger of expiry
  
✅ **Dynamic Pricing**
  - Support multiple pricing strategies
  - Adjust price based on occupancy
  - Apply seat class surcharges (Economy vs Business)
  
✅ **Notifications**
  - Notify on hold success, confirmation, expiry, cancellation
  - Support multiple channels (email, SMS, console)

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 500-1000+ simultaneous holds/confirms  
✅ **Consistency**: No overbooking (seat can only be held by ONE user)  
✅ **Availability**: Real-time seat status updates, <100ms searches  
✅ **Latency**: <200ms for hold/confirm operations  
✅ **Uptime**: 99.9% (8.6 hours downtime/month allowed)  
✅ **Throughput**: 1M flights/day = ~12 flights/second average (easily handled)  
✅ **Hold Expiry Accuracy**: ±30 seconds tolerance acceptable  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES - multi-region with replicas |
| **Single airline?** | YES - simplify scope |
| **Real payment?** | NO - mock service (payment failure still tested) |
| **Overbooking allowed?** | YES - controlled 5% oversell for no-shows |
| **Cancellation fee?** | Time-based: Full refund if >24h, 50% if >6h, None if <6h |
| **Seat hold timeout** | Fixed 5 minutes |
| **Max passengers per booking** | 1 (single seat per booking) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
Flight, Seat, Passenger, Booking, Price, Status, Notification, ...
```

### Step 2.2: Define Core Classes

#### **Seat** — A single seat in a flight
```
Properties:
  - seat_id: str (e.g., "1A", "1B", "12C")
  - seat_class: SeatClass (ECONOMY or BUSINESS)
  - status: SeatStatus (AVAILABLE, HOLD, BOOKED)
  - booked_by: Optional[str] (passenger ID or None)

Behaviors:
  - is_available(): Check if seat can be held
  - hold(): Transition to HOLD status
  - book(): Transition to BOOKED status
  - release(): Transition back to AVAILABLE
```

#### **Flight** — A single flight with multiple seats
```
Properties:
  - flight_id: str (e.g., "AA101")
  - origin: str (e.g., "NYC")
  - destination: str (e.g., "LAX")
  - departure: datetime
  - aircraft_type: str (e.g., "Boeing 737")
  - seats: Dict[str, Seat] (collection of 30-180 seats)

Behaviors:
  - add_seat(seat): Register seat in flight
  - get_seat(seat_id): Retrieve seat by ID
  - available_seats_count(): Count available seats for pricing
```

#### **Passenger** — A person booking flights
```
Properties:
  - passenger_id: str
  - name: str
  - email: str

Behaviors:
  - (none - just data holder)
```

#### **Booking** — A single seat reservation
```
Properties:
  - booking_id: str (unique per booking)
  - passenger: Passenger (who booked)
  - flight: Flight (which flight)
  - seat: Seat (which seat)
  - price: float (calculated price)
  - status: BookingStatus (HOLD, CONFIRMED, CANCELLED, EXPIRED)
  - created_at: datetime
  - hold_until: datetime (when hold expires)

Behaviors:
  - confirm(): Mark as CONFIRMED, book the seat
  - cancel(): Mark as CANCELLED, release seat
  - expire(): Mark as EXPIRED, release seat (auto-called after 5 min)
```

#### **AirlineSystem** — Main controller (Singleton)
```
Properties:
  - flights: Dict[str, Flight]
  - passengers: Dict[str, Passenger]
  - bookings: Dict[str, Booking]
  - observers: List[Observer] (for notifications)
  - pricing_strategy: PricingStrategy

Behaviors:
  - hold_seat(passenger_id, flight_id, seat_id): Create booking + hold seat
  - confirm_booking(booking_id): Transition HOLD → CONFIRMED
  - cancel_booking(booking_id): Transition to CANCELLED
  - check_and_expire_holds(): Expire all old HOLD bookings (background job)
  - set_pricing_strategy(strategy): Switch pricing algorithm
  - notify_observers(event, booking): Broadcast event to all listeners
```

### Step 2.3: Define Enumerations (State & Type)

```python
class SeatStatus(Enum):
    AVAILABLE = "available"    # Can be held
    HOLD = "hold"              # Temporarily reserved by user
    BOOKED = "booked"          # Permanently booked after payment

class BookingStatus(Enum):
    HOLD = "hold"              # User in checkout (5-min window)
    CONFIRMED = "confirmed"    # User paid, booking permanent
    CANCELLED = "cancelled"    # User cancelled
    EXPIRED = "expired"        # 5-min hold window closed

class SeatClass(Enum):
    ECONOMY = 1                # $100 base price
    BUSINESS = 2               # $200 base price
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Seat** | Granular seat tracking | Can't prevent overbooking |
| **Flight** | Group seats logically | Can't organize inventory |
| **Passenger** | Track who booked | Can't send notifications |
| **Booking** | Hold lifecycle tracking | Can't manage holds or expiry |
| **AirlineSystem** | Central controller | No thread-safe coordination |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Search Flights**
```python
def search_flights(origin: str, destination: str, date: str) -> List[Flight]:
    """
    Find all flights matching route and date.
    Returns: List of Flight objects with available seat counts.
    Raises: FlightNotFoundError if no matches.
    Response Time: <100ms (cached)
    """
    pass
```

#### **2. Browse Seats**
```python
def get_available_seats(flight_id: str) -> Dict[str, Seat]:
    """
    Get all available (AVAILABLE status) seats in a flight.
    Returns: Dict mapping seat_id → Seat object.
    Raises: FlightNotFoundError if flight doesn't exist.
    Response Time: <50ms (cached)
    """
    pass
```

#### **3. Hold Seat** ⭐ CRITICAL
```python
def hold_seat(passenger_id: str, flight_id: str, seat_id: str, 
              hold_seconds: int = 300) -> Booking:
    """
    Temporarily reserve a seat for 5 minutes (default 300 seconds).
    
    Precondition: seat.status == AVAILABLE
    Postcondition: seat.status == HOLD, booking.status == HOLD
    
    Returns: Booking object with booking_id, price, hold_until timestamp.
    
    Raises:
      - SeatNotAvailableError: Seat already held/booked by another user
      - FlightNotFoundError: Flight doesn't exist
      - PassengerNotFoundError: Passenger not registered
      - SeatNotFoundError: Seat ID invalid
    
    Concurrency: THREAD-SAFE with atomic status transition
    Response Time: <200ms
    Idempotency: NO (multiple calls = multiple bookings)
    """
    pass
```

#### **4. Confirm Booking** ⭐ CRITICAL
```python
def confirm_booking(booking_id: str) -> bool:
    """
    Permanently book a seat after payment succeeds.
    
    Precondition: booking.status == HOLD
    Postcondition: booking.status == CONFIRMED, seat.status == BOOKED
    
    Returns: True if success, False if failed.
    
    Raises:
      - BookingNotFoundError: Booking ID invalid
      - BookingExpiredError: Hold window closed (now > hold_until)
      - BookingNotHeldError: Booking not in HOLD state (already confirmed/cancelled)
    
    Concurrency: THREAD-SAFE
    Response Time: <200ms
    Side Effects: Sends notification to passenger (email/SMS)
    """
    pass
```

#### **5. Cancel Booking**
```python
def cancel_booking(booking_id: str) -> bool:
    """
    Cancel a booking and release seat back to available.
    
    Precondition: booking.status in [HOLD, CONFIRMED]
    Postcondition: booking.status = CANCELLED, seat.status = AVAILABLE
    
    Returns: True if success, False if failed.
    
    Raises:
      - BookingNotFoundError: Booking ID invalid
      - BookingAlreadyExpiredError: Can't cancel expired booking
    
    Side Effects: 
      - Calculates refund based on time_until_departure
      - Sends cancellation email
    """
    pass
```

#### **6. Automatic Hold Expiry** (Background Job)
```python
def check_and_expire_holds() -> None:
    """
    Scan all HOLD bookings and auto-expire stale ones.
    Called every 1 minute by background scheduler.
    
    For each HOLD booking:
      if now > booking.hold_until:
        - Set booking.status = EXPIRED
        - Set seat.status = AVAILABLE
        - Notify passenger
    
    Response Time: O(n) where n = total HOLD bookings (tolerate ~5 min delay)
    Concurrency: Can run in parallel, guarded by distributed locks
    """
    pass
```

#### **7. Set Pricing Strategy**
```python
def set_pricing_strategy(strategy: PricingStrategy) -> None:
    """
    Dynamically switch pricing algorithm.
    New pricing applies to next hold_seat() call.
    
    Strategy: Pluggable (FixedPricing or DemandBasedPricing)
    """
    pass
```

#### **8. Register Observer** (For Notifications)
```python
def add_observer(observer: Observer) -> None:
    """
    Register callback for booking events.
    
    Events: "held", "confirmed", "cancelled", "expired"
    Observer will be called: observer.update(event, booking)
    
    Example: Add EmailNotifier to send emails on confirm/expire
    """
    pass
```

### Step 3.2: Exception Hierarchy

```python
class AirlineException(Exception):
    """Base exception"""
    pass

class SeatNotAvailableError(AirlineException):
    """Seat already held/booked"""
    pass

class BookingExpiredError(AirlineException):
    """Hold window closed"""
    pass

class FlightNotFoundError(AirlineException):
    """Flight ID invalid"""
    pass

class PassengerNotFoundError(AirlineException):
    """Passenger not registered"""
    pass
```

### Step 3.3: API Usage Example

```python
system = AirlineSystem.get_instance()

# 1. Search flights
flights = system.search_flights("NYC", "LAX", "2025-01-15")

# 2. Browse seats
flight = flights[0]
seats = system.get_available_seats(flight.flight_id)

# 3. HOLD seat
booking = system.hold_seat(
    passenger_id="P001",
    flight_id="AA101",
    seat_id="1A"
)
print(f"Booking ID: {booking.booking_id}, Price: ${booking.price}")

# 4. CONFIRM booking
success = system.confirm_booking(booking.booking_id)

# 5. CANCEL booking
system.cancel_booking(booking.booking_id)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
AirlineSystem HAS-A flights (1:N Composition)
  └─ AirlineSystem is "owner", manages lifecycle of flights

Flight HAS-A seats (1:N Composition)
  └─ Flight contains collection of Seat objects

Booking REFERENCES passenger (1:1 Association)
  └─ Booking links to Passenger (no ownership)

Booking REFERENCES flight (1:1 Association)
  └─ Booking links to Flight (no ownership)

Booking REFERENCES seat (1:1 Association)
  └─ Booking links to Seat (no ownership)

AirlineSystem USES-A PricingStrategy (1:1 Composition)
  └─ AirlineSystem owns and manages pricing algorithm

AirlineSystem NOTIFIES Observer (1:N Association)
  └─ Multiple observers listen to events
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────┐
│    AirlineSystem (Singleton)         │
├──────────────────────────────────────┤
│ - _instance: AirlineSystem           │
│ - flights: Dict[str, Flight]         │
│ - passengers: Dict[str, Passenger]   │
│ - bookings: Dict[str, Booking]       │
│ - observers: List[Observer]          │
│ - pricing_strategy: PricingStrategy  │
│ - _lock: threading.Lock              │
├──────────────────────────────────────┤
│ + get_instance(): AirlineSystem      │
│ + hold_seat(...): Booking            │
│ + confirm_booking(booking_id): bool  │
│ + cancel_booking(booking_id): bool   │
│ + check_and_expire_holds(): void     │
│ + set_pricing_strategy(strategy)     │
│ + add_observer(observer): void       │
│ + notify_observers(event, booking)   │
└──────────────────────────────────────┘
           │ manages 1:N
           ▼
    ┌─────────────────────────────────┐
    │      Flight                     │
    ├─────────────────────────────────┤
    │ - flight_id: str                │
    │ - origin: str                   │
    │ - destination: str              │
    │ - departure: datetime           │
    │ - aircraft_type: str            │
    │ - seats: Dict[str, Seat]        │
    ├─────────────────────────────────┤
    │ + add_seat(seat): void          │
    │ + get_seat(seat_id): Seat       │
    │ + available_seats_count(): int  │
    └─────────────────────────────────┘
           │ contains 1:N
           ▼
    ┌─────────────────────────────────┐
    │         Seat                    │
    ├─────────────────────────────────┤
    │ - seat_id: str                  │
    │ - seat_class: SeatClass         │
    │ - status: SeatStatus            │
    │ - booked_by: Optional[str]      │
    ├─────────────────────────────────┤
    │ + is_available(): bool          │
    │ + hold(): void                  │
    │ + book(): void                  │
    │ + release(): void               │
    └─────────────────────────────────┘
           ▲ linked by
           │
    ┌─────────────────────────────────┐
    │        Booking                  │
    ├─────────────────────────────────┤
    │ - booking_id: str               │
    │ - passenger: Passenger          │
    │ - flight: Flight                │
    │ - seat: Seat                    │
    │ - price: float                  │
    │ - status: BookingStatus         │
    │ - hold_until: datetime          │
    ├─────────────────────────────────┤
    │ + confirm(): void               │
    │ + cancel(): void                │
    │ + expire(): void                │
    └─────────────────────────────────┘
           │ references 1:1
           ▼
    ┌─────────────────────┐
    │     Passenger       │
    ├─────────────────────┤
    │ - passenger_id: str │
    │ - name: str         │
    │ - email: str        │
    └─────────────────────┘


STRATEGY PATTERN (Pricing):
┌────────────────────────────────────┐
│ PricingStrategy (Abstract)         │
├────────────────────────────────────┤
│ + calculate_price(flight, seat)    │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ FixedPricing (Economy $100, Business $200)
   └─→ DemandBasedPricing (1.0x - 1.5x multiplier)

OBSERVER PATTERN (Notifications):
┌────────────────────────────────────┐
│ Observer (Abstract)                │
├────────────────────────────────────┤
│ + update(event, booking)           │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ ConsoleObserver (logging)
   ├─→ EmailNotifier
   └─→ SMSNotifier
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| AirlineSystem → Flights | 1:N | Composition | System owns all flights |
| Flight → Seats | 1:N | Composition | Flight owns all its seats |
| Booking → Passenger | 1:1 | Association | Booking references one passenger |
| Booking → Flight | 1:1 | Association | Booking references one flight |
| Booking → Seat | 1:1 | Association | Booking reserves one seat |
| AirlineSystem → PricingStrategy | 1:1 | Composition | System owns pricing rule |
| AirlineSystem → Observers | 1:N | Association | System notifies multiple listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For AirlineSystem)

**Problem**: Multiple threads need single consistent view of flights, bookings, passengers.

**Solution**: One global AirlineSystem instance, thread-safe initialization.

```python
class AirlineSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (hard to test), ⚠️ Harder to scale across machines

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Pricing varies (fixed vs demand-based) and may change in future.

**Solution**: Pluggable pricing algorithms, swap without modifying booking logic.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        pass

class FixedPricing(PricingStrategy):
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        return 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0

class DemandBasedPricing(PricingStrategy):
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        base = 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0
        occupancy_rate = 1.0 - (flight.available_seats_count() / len(flight.seats))
        multiplier = 1.0 + (occupancy_rate * 0.5)  # up to 1.5x surge
        return base * multiplier

# Usage: Switch algorithm at runtime
system.set_pricing_strategy(DemandBasedPricing())
price = system.pricing_strategy.calculate_price(flight, seat)
```

**Benefit**: ✅ Easy to add new pricing (Seasonal, EarlyBird, etc.), ✅ No booking logic change  
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Booking events (hold, confirm, expire) need to trigger emails/SMS/logging.

**Solution**: Observer pattern decouples event producer from consumers.

```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class EmailNotifier(Observer):
    def update(self, event: str, booking: Booking):
        if event == "confirmed":
            send_email(booking.passenger.email, "Booking Confirmed!")

class ConsoleObserver(Observer):
    def update(self, event: str, booking: Booking):
        print(f"[{event.upper()}] Booking {booking.booking_id}")

# Usage: Add multiple observers
system.add_observer(EmailNotifier())
system.add_observer(ConsoleObserver())

# On any event:
system.notify_observers("confirmed", booking)
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new notifiers (SMS, Slack, etc.)  
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 4: **State Enums** (For Status Transitions)

**Problem**: Booking can be in HOLD, CONFIRMED, EXPIRED, CANCELLED. Invalid transitions must be prevented.

**Solution**: Use enums to explicitly track state.

```python
class BookingStatus(Enum):
    HOLD = "hold"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

# Valid transitions:
def confirm_booking(booking_id: str):
    booking = bookings[booking_id]
    if booking.status != BookingStatus.HOLD:
        raise ValueError("Can only confirm HOLD bookings")
    booking.status = BookingStatus.CONFIRMED
```

**Benefit**: ✅ Explicit state, ✅ Invalid transitions caught at runtime  
**Trade-off**: ⚠️ Need explicit state transition logic

---

### Pattern 5: **Factory** (For Creating Bookings)

**Problem**: Creating a booking requires initializing multiple objects (Seat, Booking, notification).

**Solution**: Factory method encapsulates creation logic.

```python
def hold_seat(self, passenger_id: str, flight_id: str, seat_id: str):
    # Factory logic: create booking with all dependencies
    seat.hold()
    price = self.pricing_strategy.calculate_price(flight, seat)
    booking = Booking(f"BK{len(self.bookings)+1}", passenger, flight, seat, price)
    booking.hold_until = datetime.now() + timedelta(seconds=300)
    self.bookings[booking.booking_id] = booking
    return booking
```

**Benefit**: ✅ Centralized creation, ✅ Consistent initialization  
**Trade-off**: ⚠️ If grows, consider Builder pattern

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Need single global AirlineSystem | Consistent state across all clients |
| **Strategy** | Varying pricing algorithms | Pluggable, easy to extend |
| **Observer** | Events trigger notifications | Loose coupling, event-driven |
| **State (Enum)** | Explicit booking lifecycle | Invalid transitions prevented |
| **Factory** | Complex object creation | Centralized, consistent |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

# ============ ENUMERATIONS ============

class SeatStatus(Enum):
    AVAILABLE = "available"
    HOLD = "hold"
    BOOKED = "booked"

class BookingStatus(Enum):
    HOLD = "hold"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SeatClass(Enum):
    ECONOMY = 1
    BUSINESS = 2

# ============ CORE ENTITIES ============

class Seat:
    def __init__(self, seat_id: str, seat_class: SeatClass):
        self.seat_id = seat_id
        self.seat_class = seat_class
        self.status = SeatStatus.AVAILABLE
        self.booked_by = None
    
    def is_available(self) -> bool:
        return self.status == SeatStatus.AVAILABLE
    
    def hold(self):
        if not self.is_available():
            raise ValueError(f"Seat {self.seat_id} not available")
        self.status = SeatStatus.HOLD
    
    def book(self):
        self.status = SeatStatus.BOOKED
    
    def release(self):
        self.status = SeatStatus.AVAILABLE
        self.booked_by = None

class Passenger:
    def __init__(self, passenger_id: str, name: str, email: str):
        self.passenger_id = passenger_id
        self.name = name
        self.email = email

class Flight:
    def __init__(self, flight_id: str, origin: str, destination: str, 
                 departure: datetime, aircraft_type: str):
        self.flight_id = flight_id
        self.origin = origin
        self.destination = destination
        self.departure = departure
        self.aircraft_type = aircraft_type
        self.seats: Dict[str, Seat] = {}
    
    def add_seat(self, seat: Seat):
        self.seats[seat.seat_id] = seat
    
    def get_seat(self, seat_id: str) -> Optional[Seat]:
        return self.seats.get(seat_id)
    
    def available_seats_count(self) -> int:
        return sum(1 for s in self.seats.values() if s.is_available())

class Booking:
    def __init__(self, booking_id: str, passenger: Passenger, flight: Flight, 
                 seat: Seat, price: float):
        self.booking_id = booking_id
        self.passenger = passenger
        self.flight = flight
        self.seat = seat
        self.price = price
        self.status = BookingStatus.HOLD
        self.created_at = datetime.now()
        self.hold_until: Optional[datetime] = None
    
    def confirm(self):
        self.status = BookingStatus.CONFIRMED
        self.seat.book()
    
    def cancel(self):
        self.status = BookingStatus.CANCELLED
        self.seat.release()
    
    def expire(self):
        if self.status == BookingStatus.HOLD:
            self.status = BookingStatus.EXPIRED
            self.seat.release()

# ============ STRATEGIES ============

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        pass

class FixedPricing(PricingStrategy):
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        return 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0

class DemandBasedPricing(PricingStrategy):
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        base = 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0
        available = flight.available_seats_count()
        total = len(flight.seats)
        occupancy_rate = 1.0 - (available / total) if total > 0 else 0
        multiplier = 1.0 + (occupancy_rate * 0.5)
        return base * multiplier

# ============ OBSERVERS ============

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, booking: Booking):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event.upper():12} | Passenger: {booking.passenger.name:15} | "
              f"Flight: {booking.flight.flight_id:8} | Seat: {booking.seat.seat_id:4} | Price: ${booking.price:.2f}")

class EmailNotifier(Observer):
    def update(self, event: str, booking: Booking):
        if event == "confirmed":
            print(f"📧 Email: {booking.passenger.email} - Booking confirmed!")
        elif event == "expired":
            print(f"📧 Email: {booking.passenger.email} - Hold expired!")

# ============ SINGLETON CONTROLLER ============

class AirlineSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.flights: Dict[str, Flight] = {}
            self.passengers: Dict[str, Passenger] = {}
            self.bookings: Dict[str, Booking] = {}
            self.observers: List[Observer] = []
            self.pricing_strategy: PricingStrategy = FixedPricing()
            self._data_lock = threading.Lock()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'AirlineSystem':
        return AirlineSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        with self._data_lock:
            self.pricing_strategy = strategy
    
    def add_observer(self, observer: Observer):
        with self._data_lock:
            self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        with self._data_lock:
            observers_copy = list(self.observers)
        for obs in observers_copy:
            obs.update(event, booking)
    
    def add_flight(self, flight: Flight):
        with self._data_lock:
            self.flights[flight.flight_id] = flight
    
    def register_passenger(self, passenger: Passenger):
        with self._data_lock:
            self.passengers[passenger.passenger_id] = passenger
    
    def hold_seat(self, passenger_id: str, flight_id: str, seat_id: str, 
                  hold_seconds: int = 300) -> Optional[Booking]:
        with self._data_lock:
            if flight_id not in self.flights:
                print(f"❌ Flight {flight_id} not found")
                return None
            
            flight = self.flights[flight_id]
            seat = flight.get_seat(seat_id)
            
            if not seat or not seat.is_available():
                print(f"❌ Seat {seat_id} not available")
                return None
            
            passenger = self.passengers.get(passenger_id)
            if not passenger:
                print(f"❌ Passenger {passenger_id} not found")
                return None
            
            seat.hold()
            price = self.pricing_strategy.calculate_price(flight, seat)
            booking = Booking(f"BK{len(self.bookings)+1}", passenger, flight, seat, price)
            booking.hold_until = datetime.now() + timedelta(seconds=hold_seconds)
            self.bookings[booking.booking_id] = booking
            booking_to_notify = booking
        
        self.notify_observers("held", booking_to_notify)
        return booking
    
    def confirm_booking(self, booking_id: str) -> bool:
        with self._data_lock:
            booking = self.bookings.get(booking_id)
            if not booking:
                print(f"❌ Booking {booking_id} not found")
                return False
            
            if booking.status != BookingStatus.HOLD:
                print(f"❌ Booking not in HOLD status")
                return False
            
            if datetime.now() > booking.hold_until:
                booking.expire()
                booking_to_notify = booking
                expired = True
            else:
                booking.confirm()
                booking_to_notify = booking
                expired = False
        
        if expired:
            self.notify_observers("expired", booking_to_notify)
            print(f"❌ Hold expired for booking {booking_id}")
            return False
        
        self.notify_observers("confirmed", booking_to_notify)
        return True
    
    def cancel_booking(self, booking_id: str) -> bool:
        with self._data_lock:
            booking = self.bookings.get(booking_id)
            if not booking:
                return False
            
            booking.cancel()
            booking_to_notify = booking
        
        self.notify_observers("cancelled", booking_to_notify)
        return True
    
    def check_and_expire_holds(self):
        now = datetime.now()
        expired_bookings = []
        
        with self._data_lock:
            for booking in self.bookings.values():
                if (booking.status == BookingStatus.HOLD and 
                    booking.hold_until and now > booking.hold_until):
                    booking.expire()
                    expired_bookings.append(booking)
        
        for booking in expired_bookings:
            self.notify_observers("expired", booking)

# ============ DEMO ============

if __name__ == "__main__":
    print("="*70)
    print("AIRLINE MANAGEMENT SYSTEM")
    print("="*70)
    
    system = AirlineSystem.get_instance()
    system.flights.clear()
    system.passengers.clear()
    system.bookings.clear()
    system.observers.clear()
    
    system.add_observer(ConsoleObserver())
    system.add_observer(EmailNotifier())
    
    # Create flight
    flight = Flight("AA101", "NYC", "LAX", datetime.now() + timedelta(hours=2), "Boeing 737")
    for i in range(1, 6):
        flight.add_seat(Seat(f"{i}A", SeatClass.BUSINESS))
        flight.add_seat(Seat(f"{i}B", SeatClass.ECONOMY))
    system.add_flight(flight)
    
    # Register passengers
    p1 = Passenger("P001", "John Doe", "john@example.com")
    p2 = Passenger("P002", "Jane Smith", "jane@example.com")
    system.register_passenger(p1)
    system.register_passenger(p2)
    
    print(f"\n✅ Setup: Flight {flight.flight_id} with {len(flight.seats)} seats")
    
    # Demo hold & confirm
    print("\n[Demo] Hold & Confirm:")
    b1 = system.hold_seat("P001", "AA101", "1A", hold_seconds=3)
    if b1:
        print(f"Held booking {b1.booking_id}")
        system.confirm_booking(b1.booking_id)
    
    # Demo pricing
    print("\n[Demo] Dynamic Pricing:")
    system.set_pricing_strategy(DemandBasedPricing())
    b2 = system.hold_seat("P002", "AA101", "1B", hold_seconds=3)
    if b2:
        print(f"Held booking {b2.booking_id}")
        system.cancel_booking(b2.booking_id)
    
    print(f"\n✅ Demo complete! Available seats: {flight.available_seats_count()}")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **hold_seat** | Mutex on data | Only 1 user can hold seat at a time |
| **confirm_booking** | Mutex on data | Atomic: check HOLD, check expiry, transition |
| **cancel_booking** | Mutex on data | No double-cancel |
| **check_and_expire_holds** | Mutex on data | Safe scan, expiry without race condition |

**Concurrency Principles**:
1. ✅ Locks guard critical sections (check + modify)
2. ✅ Minimize lock duration (notify outside lock)
3. ✅ Double-checked locking for Singleton
4. ✅ No nested locks (prevent deadlock)

---

## Demo Scenarios

### Scenario 1: Hold & Confirm

```
[12:30:45] HELD        | Passenger: John Doe         | Flight: AA101    | Seat: 1A   | Price: $200.00
📧 Email: john@example.com - Booking confirmed!
[12:30:46] CONFIRMED   | Passenger: John Doe         | Flight: AA101    | Seat: 1A   | Price: $200.00
```

### Scenario 2: Hold Expiry

```
[12:31:00] HELD        | Passenger: Jane Smith       | Flight: AA101    | Seat: 1B   | Price: $100.00
📧 Email: jane@example.com - Hold expired!
[12:31:05] EXPIRED     | Passenger: Jane Smith       | Flight: AA101    | Seat: 1B   | Price: $100.00
```

### Scenario 3: Dynamic Pricing

```
Current occupancy: 1/10 (10%)
Price: Economy $100, Business $200 (base)

After 7 bookings (80% occupancy):
Price: Economy $140 (40% surge), Business $280 (40% surge)
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent overbooking of a seat?**

A: Atomic status transitions with lock-based concurrency control:

```python
with self._data_lock:  # Atomic critical section
    if seat.status != SeatStatus.AVAILABLE:
        raise SeatNotAvailableError()
    
    seat.status = SeatStatus.HOLD  # Atomic transition
```

**Q2: What's the difference between HOLD and CONFIRMED?**

A: HOLD = temporary 5-min window. CONFIRMED = permanent after payment. Timeline: Browse → Hold → Confirm (or timeout → Expire).

**Q3: How do you handle hold expiry?**

A: Lazy check on confirm + eager background job scanning all HOLD bookings every minute.

**Q4: Why use Strategy pattern for pricing?**

A: Allows swapping pricing algorithms (FixedPricing, DemandBasedPricing) without modifying booking logic.

**Q5: How would you scale to 1M concurrent users and 1M flights/day?**

A: Multi-tier: API Gateway → 1000 API servers → Redis locks → Sharded DB (1000 shards) → Kafka for events.

---

### Intermediate Questions

**Q6: How to handle race condition: 2 users holding same seat simultaneously?**

A: Lock ensures only 1 thread can modify seat status at a time. Lock TTL prevents deadlocks.

**Q7: How to handle payment failure gracefully?**

A: Retry 3x with exponential backoff. On final failure, auto-expire booking and release seat.

**Q8: How to implement seat upgrades (Economy → Business)?**

A: Calculate price difference, charge user, release old seat, book new seat.

**Q9: What metrics would you track?**

A: Hold success rate, confirmation rate, hold expiry rate, overbooking incidents, API latency, cache hit ratio.

**Q10: How to handle regulatory compliance (refund policies)?**

A: Time-based: Full refund if >24h, 50% if >6h, None if <6h. Audit log all refunds.

---

## Scaling Q&A

### Q1: How to prevent overbooking in distributed system?

**Solution**: Pessimistic locking + version control with Redis:

```
Acquire lock: Redis.SET("lock:FL123:1A", "USER_A", NX, EX=15s)
Check seat version: DB.GET(seat, version=5)
Update: DB.UPDATE(...) WHERE version=5 SET version=6, status=HOLD
Release lock
```

### Q2: How to cache seat availability without invalidation storms?

**Solution**: Cache with 5-second TTL + versioning. Broadcast version increments to invalidate.

### Q3: How to implement real-time seat updates?

**Solution**: WebSocket + Redis Pub/Sub. Latency: ~100ms (broadcast + network + UI update).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships
- [ ] Discuss hold/confirm lifecycle and HOLD → CONFIRMED transitions
- [ ] Explain how to prevent overbooking with atomic locks
- [ ] Discuss hold expiry (5-min timeout, auto-release)
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety in Singleton, hold_seat, confirm_booking
- [ ] Discuss trade-offs (in-memory vs DB, pessimistic vs optimistic locking)

---

**Ready for interview? Book some flights! 🛫**
