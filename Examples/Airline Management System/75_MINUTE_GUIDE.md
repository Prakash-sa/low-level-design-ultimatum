# Airline Management System - 75 Minute Interview Guide

## System Overview

Single-airline booking system with seat reservations, dynamic pricing, and event notifications.

**Scale**: 500 concurrent users, 1–10k flights/day, moderate booking volume.  
**Focus**: Core design patterns, extensible architecture, booking lifecycle.

---

## 75-Minute Timeline

| Time | Phase | Deliverable |
|------|-------|-------------|
| 0–5 min | **Requirements Clarification** | Scope & assumptions confirmed |
| 5–15 min | **Architecture & Design Patterns** | System diagram + class skeleton |
| 15–35 min | **Core Entities** | Flight, Seat, Passenger, Booking classes |
| 35–55 min | **Booking Logic & Pricing** | Hold, Confirm, Cancel + Strategy pattern |
| 55–70 min | **System Integration & Observer** | AirlineSystem (Singleton) + notifications |
| 70–75 min | **Demo & Q&A** | Working example + trade-off discussion |

---

## Requirements Clarification (0–5 min)

**Key Questions**:
1. Single airline or marketplace? → **Single airline**
2. Core features? → **Search, hold, confirm, cancel, expiry**
3. Concurrency? → **Basic (in-memory for demo)**
4. Persistence? → **In-memory (no DB required)**
5. Payments? → **Simulated only**

**Scope Agreement**:
- ✅ Flight inventory with seat map
- ✅ Booking flow: hold → confirm → cancel with expiry
- ✅ Dynamic pricing (demand-based)
- ✅ Notifications (Observer pattern)
- ❌ Multi-airline, check-in, baggage, loyalty

---

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Singleton** | Single system instance | `AirlineSystem.get_instance()` |
| **Strategy** | Pluggable pricing algorithms | `PricingStrategy` + `FixedPricing`, `DemandBasedPricing` |
| **Observer** | Event notifications | `Observer` interface + `ConsoleObserver` |
| **State** | Seat/Booking status transitions | Enums: `SeatStatus`, `BookingStatus` |
| **Factory** | Create domain objects | Factory methods in `AirlineSystem` |

---

## Core Classes & Implementation

### Enumerations

```python
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import threading

# Seat and Booking Status
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
```

### 1. Seat Class

```python
class Seat:
    """Represents a single seat on a flight"""
    def __init__(self, seat_id: str, seat_class: SeatClass):
        self.seat_id = seat_id
        self.seat_class = seat_class
        self.status = SeatStatus.AVAILABLE
        self.booked_by = None  # booking_id
    
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
```

### 2. Passenger Class

```python
class Passenger:
    """Represents a passenger"""
    def __init__(self, passenger_id: str, name: str, email: str):
        self.passenger_id = passenger_id
        self.name = name
        self.email = email
```

### 3. Flight Class

```python
class Flight:
    """Represents a flight with seat inventory"""
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
```

### 4. Booking Class

```python
class Booking:
    """Represents a booking with lifecycle (HOLD → CONFIRMED or EXPIRED)"""
    def __init__(self, booking_id: str, passenger: Passenger, 
                 flight: Flight, seat: Seat, price: float):
        self.booking_id = booking_id
        self.passenger = passenger
        self.flight = flight
        self.seat = seat
        self.price = price
        self.status = BookingStatus.HOLD
        self.created_at = datetime.now()
        self.hold_until: Optional[datetime] = None
    
    def confirm(self):
        """Transition to CONFIRMED status and mark seat as BOOKED"""
        self.status = BookingStatus.CONFIRMED
        self.seat.book()
    
    def cancel(self):
        """Transition to CANCELLED status and release seat"""
        self.status = BookingStatus.CANCELLED
        self.seat.release()
    
    def expire(self):
        """Transition to EXPIRED status if hold time exceeded"""
        if self.status == BookingStatus.HOLD:
            self.status = BookingStatus.EXPIRED
            self.seat.release()
```

---

## Pricing Strategy (Strategy Pattern)

```python
class PricingStrategy(ABC):
    """Abstract strategy for calculating seat price"""
    @abstractmethod
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        pass

class FixedPricing(PricingStrategy):
    """Base pricing: Economy $100, Business $200"""
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        return 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0

class DemandBasedPricing(PricingStrategy):
    """Dynamic pricing based on seat occupancy"""
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        base = 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0
        available = flight.available_seats_count()
        total = len(flight.seats)
        
        # Price increases as occupancy increases (up to 1.5x)
        occupancy_rate = 1.0 - (available / total)
        multiplier = 1.0 + (occupancy_rate * 0.5)
        
        return base * multiplier
```

---

## Observer Pattern (Notifications)

```python
class Observer(ABC):
    """Observer interface for booking events"""
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class ConsoleObserver(Observer):
    """Console-based observer for demo purposes"""
    def update(self, event: str, booking: Booking):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event.upper():12} | "
              f"Passenger: {booking.passenger.name:15} | "
              f"Flight: {booking.flight.flight_id:8} | "
              f"Seat: {booking.seat.seat_id:4} | "
              f"Price: ${booking.price:.2f}")
```

---

## AirlineSystem (Singleton + Controller)

```python
class AirlineSystem:
    """Singleton controller for airline operations"""
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
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'AirlineSystem':
        """Get singleton instance"""
        return AirlineSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Switch pricing algorithm dynamically"""
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: Observer):
        """Subscribe to booking events"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(event, booking)
    
    def add_flight(self, flight: Flight):
        self.flights[flight.flight_id] = flight
    
    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.passenger_id] = passenger
    
    def hold_seat(self, passenger_id: str, flight_id: str, 
                  seat_id: str, hold_seconds: int = 300) -> Optional[Booking]:
        """
        Attempt to hold a seat for a passenger.
        Returns Booking if successful, None otherwise.
        """
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
        
        # Hold the seat and create booking
        seat.hold()
        price = self.pricing_strategy.calculate_price(flight, seat)
        
        booking = Booking(f"BK{len(self.bookings)+1}", passenger, flight, seat, price)
        booking.hold_until = datetime.now() + timedelta(seconds=hold_seconds)
        
        self.bookings[booking.booking_id] = booking
        self.notify_observers("held", booking)
        return booking
    
    def confirm_booking(self, booking_id: str) -> bool:
        """
        Confirm a held booking.
        Returns True if successful, False otherwise.
        """
        booking = self.bookings.get(booking_id)
        if not booking:
            print(f"❌ Booking {booking_id} not found")
            return False
        
        if booking.status != BookingStatus.HOLD:
            print(f"❌ Booking not in HOLD status")
            return False
        
        if datetime.now() > booking.hold_until:
            booking.expire()
            self.notify_observers("expired", booking)
            print(f"❌ Hold expired for booking {booking_id}")
            return False
        
        booking.confirm()
        self.notify_observers("confirmed", booking)
        return True
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking and release the seat"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return False
        
        booking.cancel()
        self.notify_observers("cancelled", booking)
        return True
    
    def check_and_expire_holds(self):
        """Expire all timed-out holds (background task)"""
        now = datetime.now()
        for booking in self.bookings.values():
            if (booking.status == BookingStatus.HOLD and 
                booking.hold_until and now > booking.hold_until):
                booking.expire()
                self.notify_observers("expired", booking)
```

---

## UML Class Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                  AIRLINE BOOKING SYSTEM                           │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │  AirlineSystem      │ ◄─── Singleton (Thread-safe)
                    │ (Controller)        │
                    ├─────────────────────┤
                    │ - flights: Dict     │
                    │ - bookings: Dict    │
                    │ - passengers: Dict  │
                    │ - observers: List   │
                    │ - pricing_strategy  │
                    ├─────────────────────┤
                    │ + hold_seat()       │
                    │ + confirm_booking() │
                    │ + cancel_booking()  │
                    │ + notify_observers()│
                    └────┬────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌─────────┐     ┌──────────┐    ┌─────────────┐
    │ Flight  │     │Passenger │    │   Booking   │
    ├─────────┤     ├──────────┤    ├─────────────┤
    │- id     │     │- id      │    │- id         │
    │- origin │     │- name    │    │- passenger  │
    │- dest   │     │- email   │    │- flight     │
    │- seats{}│     └──────────┘    │- seat       │
    │- depart │                     │- price      │
    └────┬────┘                     │- status     │
         │                          │- hold_until │
         │ HAS-A                    └─────────────┘
         │ 1..*
         ▼
    ┌─────────┐
    │  Seat   │
    ├─────────┤
    │- id     │
    │- class  │ ◄─── SeatClass Enum
    │- status │ ◄─── SeatStatus Enum
    └─────────┘

    ┌──────────────────────────────────────┐
    │  PricingStrategy (Abstract)          │
    ├──────────────────────────────────────┤
    │ + calculate_price(flight, seat)      │
    └────────────┬─────────────────────────┘
                 │
         ┌───────┴──────────────┐
         ▼                      ▼
    ┌──────────┐        ┌──────────────┐
    │ Fixed    │        │ DemandBased  │
    │ Pricing  │        │   Pricing    │
    └──────────┘        └──────────────┘

    ┌──────────────────────────────────────┐
    │  Observer (Abstract)                 │
    ├──────────────────────────────────────┤
    │ + update(event: str, booking)        │
    └────────────┬─────────────────────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ ConsoleObserver  │
        └──────────────────┘
```

**Legend**:
- `HAS-A` (1..*): Flight has multiple Seats
- IS-A relationships: Subclasses implement abstract Strategy/Observer
- Singleton: AirlineSystem maintains single instance

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking of the same seat?**

A: Use enum-based status transitions (AVAILABLE → HOLD → BOOKED). Each operation checks current status before updating. For concurrency, use atomic operations or locks around the check-and-set operation. In distributed systems, use optimistic versioning or database locks.

**Q2: What's the difference between HOLD and CONFIRMED?**

A: HOLD temporarily reserves a seat (e.g., 5 minutes) during checkout. CONFIRMED finalizes the booking after payment succeeds. Holds automatically expire and release the seat back to AVAILABLE if not confirmed in time.

**Q3: Why use Strategy pattern for pricing?**

A: Allows plugging different pricing algorithms (fixed, demand-based, time-based surge) without modifying booking logic. Easy to test, add new strategies, and switch dynamically at runtime.

### Intermediate Questions

**Q4: How do you handle hold expiry?**

A: Store `hold_until` timestamp when creating a booking. Before confirming, check if `now > hold_until`. If expired, call `expire()` which transitions status and releases the seat. Periodically call `check_and_expire_holds()` as a background task.

**Q5: How would you scale this to 1M flights with concurrent bookings?**

A: 
- Shard flights by route/date across multiple servers
- Use read replicas for search, write replicas for bookings
- Cache seat availability per flight with TTL
- Use message queues (Kafka) for async notifications
- Database transactions ensure seat uniqueness invariant
- Add rate limiting per passenger to prevent abuse

**Q6: How to handle payment failures gracefully?**

A: Wrap confirm in try-catch. On payment failure, auto-call `cancel_booking()` which releases the seat. Log failures and send compensation email to passenger. Use idempotent payment operations.

### Advanced Questions

**Q7: How do you prevent overbooking?**

A: Maintain hard seat limits per class. Use optimistic locking: read seat count + version, check version on write. On conflict, retry or notify passenger of unavailability. Alternatively, use distributed locks or database-level constraints.

**Q8: How to implement cancellations with refunds?**

A: Add `CancellationPolicy` enum (FULL_REFUND, PARTIAL, NON_REFUNDABLE). On cancel, compute refund amount, call `PaymentService.refund()`, update booking status. Ensure operations are idempotent.

**Q9: What if a passenger wants to change seats?**

A: Treat as cancel + new hold. Release old seat, attempt hold on new seat. If new seat taken, revert cancel and notify. Wrap in transaction.

**Q10: How would you notify users of overbooking situations?**

A: Maintain overbooking ratio (predicted no-shows vs. excess bookings). When threshold exceeded, trigger alerts via Observer, offer rebooking on different flight or 150% compensation. Use the notification pattern already implemented.

**Q11: How to ensure consistent state during concurrent booking operations?**

A: Use database transactions (SERIALIZABLE isolation) for critical sections. Alternatively, use optimistic concurrency control with version fields. In-memory: use thread locks with minimal hold time.

**Q12: How to audit all booking state changes?**

A: Add `AuditLog` table with (booking_id, old_status, new_status, timestamp, user_id). Create entries in every status transition method. Include in observer notifications.

---

## Demo Script

```python
from datetime import datetime, timedelta

def run_demo():
    print("=" * 70)
    print("AIRLINE BOOKING SYSTEM - DEMO")
    print("=" * 70)
    
    system = AirlineSystem.get_instance()
    system.add_observer(ConsoleObserver())
    
    # Setup: Create flight with seats
    flight = Flight("AA101", "NYC", "LAX", 
                   datetime.now() + timedelta(hours=2), "Boeing 737")
    flight.add_seat(Seat("1A", SeatClass.BUSINESS))
    flight.add_seat(Seat("1B", SeatClass.ECONOMY))
    flight.add_seat(Seat("2A", SeatClass.ECONOMY))
    system.add_flight(flight)
    
    # Create passengers
    p1 = Passenger("P001", "John Doe", "john@example.com")
    p2 = Passenger("P002", "Jane Smith", "jane@example.com")
    system.register_passenger(p1)
    system.register_passenger(p2)
    
    print("\n[DEMO 1] Hold & Confirm Booking")
    print("-" * 70)
    booking1 = system.hold_seat("P001", "AA101", "1A", hold_seconds=10)
    if booking1:
        system.confirm_booking(booking1.booking_id)
    
    print("\n[DEMO 2] Dynamic Pricing - Switch to Demand-Based")
    print("-" * 70)
    system.set_pricing_strategy(DemandBasedPricing())
    booking2 = system.hold_seat("P002", "AA101", "1B", hold_seconds=10)
    
    print("\n[DEMO 3] Cancellation - Release Seat")
    print("-" * 70)
    if booking2:
        system.cancel_booking(booking2.booking_id)
    
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total bookings: {len(system.bookings)}")
    print(f"Available seats: {flight.available_seats_count()}")
    print(f"Booked seats: {sum(1 for s in flight.seats.values() if s.status == SeatStatus.BOOKED)}")

if __name__ == "__main__":
    run_demo()
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Concurrency** | Thread-safe Singleton; add locks for critical sections |
| **Extensibility** | Strategy pattern for pricing; Observer for events |
| **Reliability** | Enums for state; explicit status transitions |
| **Scalability** | Message queues for notifications; database sharding |
| **Testing** | Mock Observer; mock PricingStrategy; unit tests per component |

---

## Interview Tips

1. **Clarify scope early** — Ask questions before designing
2. **Sketch architecture** — Use whiteboard for relationships
3. **Explain patterns as you code** — Show design thinking
4. **Handle edge cases** — Hold expiry, cancellation, payment failure
5. **Discuss trade-offs** — Consistency vs. availability, locks vs. async
6. **Demo incrementally** — Show flow: hold → confirm → cancel
7. **Mention scalability** — But don't over-engineer for interview
8. **Ask follow-up questions** — "Would you want audit logs?" (shows maturity)
