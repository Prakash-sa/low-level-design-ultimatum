# Airline Management System — 75-Minute Interview Guide

Design a single-airline booking platform with seat inventory, hold → confirm → cancel lifecycle, dynamic pricing, and event notifications. Scope: in-memory demo, ~500 concurrent users, 1–10k flights/day; payments simulated.

## Timeline (75 minutes)
| Time | Phase | Output |
|------|-------|--------|
| 0–5 | Requirements | Scope + assumptions agreed |
| 5–15 | Architecture | Class diagram + patterns |
| 15–35 | Core Entities | Flight, Seat, Passenger, Booking |
| 35–55 | Booking Logic | hold_seat, confirm, cancel, expire |
| 55–70 | Integration | Singleton controller, Strategy, Observer |
| 70–75 | Demo & Q&A | Run scenarios, discuss trade-offs |

## Requirements & Assumptions
- Single airline; in-memory storage for interview.
- Seat classes: Economy, Business; statuses: Available → Hold → Booked.
- Booking lifecycle: HOLD → CONFIRMED or EXPIRED/CANCELLED (hold timeout).
- Pricing: pluggable strategies (fixed, demand-based).
- Notifications: console observer for booking events.
- Out of scope: loyalty, check-in, baggage; payments simulated.

## Design Patterns
- **Singleton**: `AirlineSystem` for consistent state.
- **Strategy**: `PricingStrategy` → `FixedPricing`, `DemandBasedPricing`.
- **Observer**: Notify on held/confirmed/cancelled/expired bookings.
- **State**: Seat/Booking lifecycles via enums.
- **Factory (light)**: Creation helpers inside `AirlineSystem`.

## Architecture Sketch
```
Client/UI
  └─→ AirlineSystem (Singleton)
          ├─ flights[id → Flight → seats{}]
          ├─ passengers[id → Passenger]
          ├─ bookings[id → Booking]
          ├─ pricing_strategy (Strategy)
          └─ observers[] (Observer)

Flow: hold_seat → create Booking (HOLD, hold_until) → confirm | expire | cancel → notify observers
Pricing: strategy.calculate_price(flight, seat)
```

## UML Class Diagram (text)
```
┌───────────────────────┐          ┌─────────────────────────┐
│     AirlineSystem     │<>------->│       Observer          │
│  (Singleton, Control) │          ├─────────────────────────┤
├───────────────────────┤          │+ update(event, booking) │
│- flights: Dict        │          └───────────┬─────────────┘
│- bookings: Dict       │                      │
│- passengers: Dict     │                      ▼
│- observers: List      │            ┌────────────────────┐
│- pricing_strategy     │            │  ConsoleObserver   │
├───────────────────────┤            └────────────────────┘
│+ hold_seat()          │
│+ confirm_booking()    │
│+ cancel_booking()     │
│+ set_pricing_strategy()│
│+ notify_observers()   │
└───────┬───────────────┘
        │ HAS
        │ 1..*                        ┌─────────────────────┐
        ▼                             │   PricingStrategy   │
  ┌────────────┐        implements    ├─────────────────────┤
  │   Flight   │--------------------> │+ calculate_price()  │
  ├────────────┤                      └──────┬──────────────┘
  │- seats{}   │                             │
  │- origin    │                  ┌──────────┴────────────┐
  │- destination│                 │                       │
  └────┬───────┘          ┌───────────────┐       ┌───────────────┐
       │ HAS 1..*         │  FixedPricing │       │DemandBasedPricing│
       ▼                  └───────────────┘       └────────────────┘
  ┌────────────┐
  │    Seat    │  ◄──────── SeatClass (Enum)
  ├────────────┤
  │- status    │  ◄──────── SeatStatus (Enum)
  └────────────┘

┌────────────┐      references      ┌────────────┐
│  Booking   │--------------------->│ Passenger  │
├────────────┤                      ├────────────┤
│- status    │◄── BookingStatus     │- name      │
│- hold_until│   (Enum)             │- email     │
│- price     │                      └────────────┘
└────────────┘
```

## Core Model
- **Seat**: `seat_id`, `seat_class`, `status`, hold/book/release.
- **Passenger**: id, name, email.
- **Flight**: id, origin, destination, departure, seats map.
- **Booking**: id, passenger, flight, seat, price, `hold_until`, status transitions.
- **PricingStrategy**: calculates price per seat/flight.
- **Observer**: reacts to booking events.
- **AirlineSystem**: manages flights, passengers, bookings, observers, pricing.

## Compact Implementation (ready to run)
```python
"""
Airline Management System - Interview Implementation
Timeline: 75 minutes | Scale: 500 concurrent users, 1-10k flights/day
Design Patterns: Singleton, Strategy, Observer, State
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

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
    def __init__(self, flight_id: str, origin: str, destination: str, departure: datetime, aircraft_type: str):
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
    def __init__(self, booking_id: str, passenger: Passenger, flight: Flight, seat: Seat, price: float):
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
        occupancy_rate = 1.0 - (available / total)
        multiplier = 1.0 + (occupancy_rate * 0.5)  # up to 1.5x
        return base * multiplier

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, booking: 'Booking'):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, booking: 'Booking'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event.upper():12} | "
              f"Passenger: {booking.passenger.name:15} | "
              f"Flight: {booking.flight.flight_id:8} | "
              f"Seat: {booking.seat.seat_id:4} | "
              f"Price: ${booking.price:.2f}")

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
            self.initialized = True
    @staticmethod
    def get_instance() -> 'AirlineSystem':
        return AirlineSystem()
    def set_pricing_strategy(self, strategy: PricingStrategy):
        self.pricing_strategy = strategy
    def add_observer(self, observer: Observer):
        self.observers.append(observer)
    def notify_observers(self, event: str, booking: 'Booking'):
        for observer in self.observers:
            observer.update(event, booking)
    def add_flight(self, flight: Flight):
        self.flights[flight.flight_id] = flight
    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.passenger_id] = passenger
    def hold_seat(self, passenger_id: str, flight_id: str, seat_id: str, hold_seconds: int = 300) -> Optional[Booking]:
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
        self.notify_observers("held", booking)
        return booking
    def confirm_booking(self, booking_id: str) -> bool:
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
        booking = self.bookings.get(booking_id)
        if not booking:
            return False
        booking.cancel()
        self.notify_observers("cancelled", booking)
        return True
    def check_and_expire_holds(self):
        now = datetime.now()
        for booking in self.bookings.values():
            if booking.status == BookingStatus.HOLD and booking.hold_until and now > booking.hold_until:
                booking.expire()
                self.notify_observers("expired", booking)

def demo_setup():
    system = AirlineSystem.get_instance()
    system.observers.clear()
    system.flights.clear()
    system.passengers.clear()
    system.bookings.clear()
    system.add_observer(ConsoleObserver())
    flight = Flight("AA101", "NYC", "LAX", datetime.now() + timedelta(hours=2), "Boeing 737")
    for seat_id, seat_class in [("1A", SeatClass.BUSINESS), ("1B", SeatClass.ECONOMY), ("2A", SeatClass.ECONOMY)]:
        flight.add_seat(Seat(seat_id, seat_class))
    system.add_flight(flight)
    system.register_passenger(Passenger("P001", "John Doe", "john@example.com"))
    system.register_passenger(Passenger("P002", "Jane Smith", "jane@example.com"))
    return system, flight

if __name__ == "__main__":
    sys, flight = demo_setup()
    b1 = sys.hold_seat("P001", "AA101", "1A", hold_seconds=5)
    if b1:
        sys.confirm_booking(b1.booking_id)
    sys.set_pricing_strategy(DemandBasedPricing())
    b2 = sys.hold_seat("P002", "AA101", "1B", hold_seconds=5)
    if b2:
        sys.cancel_booking(b2.booking_id)
    print(f"Available seats: {flight.available_seats_count()}")
```

## Interview Q&A (cheat sheet)
- **Prevent double booking?** Status transitions (AVAILABLE → HOLD → BOOKED) with checks/locks; optimistic concurrency or DB transactions in real systems.
- **HOLD vs CONFIRMED?** HOLD is temporary reservation with expiry; CONFIRMED after payment. Expire stale holds before confirm.
- **Scaling?** Shard flights by route/date, cache availability, async notifications, idempotent operations.
- **Payments fail?** On failure, cancel booking and release seat; make payment/refund idempotent.
- **Why Strategy for pricing?** Swap algorithms without touching booking logic; test in isolation.

### Scaling-focused Q&A
- **How to scale to 1M flights and heavy concurrency?** Shard flights by route/date; cache seat availability; DB constraints/row locks for seat uniqueness; enqueue notifications via Kafka/SQS; read replicas for search vs write masters for booking; idempotent booking ops with booking_idempotency_key.
- **Prevent overbooking at scale?** Seat-level uniqueness enforced in DB; optimistic locking with version; on conflict, retry or surface alternatives; cap overbooking ratio and alert observers.
- **Expiry at scale?** Store hold_until; background sweeps per shard; delay queue for expiring booking IDs; expire idempotently and notify observers.

## Key Takeaways
- Keep lifecycle explicit with enums and small state transitions.
- Separate concerns: controller vs domain objects vs strategies vs observers.
- Start with requirements, then patterns, then demoable code; narrate trade-offs (consistency vs availability, locks vs optimistic retries).
