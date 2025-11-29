# Movie Ticket Booking System - 75 Minute Interview Guide

## System Overview

Multi-theater booking platform with seat management, dynamic pricing, and real-time availability.

**Scale**: 1,000 concurrent users, 100+ theaters, 10k+ bookings/day.  
**Focus**: Core design patterns, seat locking, pricing strategies, booking lifecycle.

---

## 75-Minute Timeline

| Time | Phase | Deliverable |
|------|-------|-------------|
| 0–5 min | **Requirements Clarification** | Scope & assumptions confirmed |
| 5–15 min | **Architecture & Design Patterns** | System diagram + class skeleton |
| 15–35 min | **Core Entities** | Movie, Theater, Hall, Show, Seat, Booking, User, Payment |
| 35–55 min | **Booking Logic & Pricing** | lock_seats, create_booking, confirm + Strategy pattern |
| 55–70 min | **System Integration & Observer** | BookingSystem (Singleton) + notifications |
| 70–75 min | **Demo & Q&A** | Working example + trade-off discussion |

---

## Requirements Clarification (0–5 min)

**Key Questions**:
1. Single theater or marketplace? → **Multiple theaters**
2. Core features? → **Search, browse, seat selection, booking, payment**
3. Seat types? → **Regular, Premium, VIP with different pricing**
4. Concurrency? → **Basic seat locking (in-memory for demo)**
5. Payments? → **Simulated only**

**Scope Agreement**:
- ✅ Movie listings and search
- ✅ Theater and hall management
- ✅ Show scheduling
- ✅ Seat selection with 2D layout
- ✅ Temporary seat locking (10 minutes)
- ✅ Dynamic pricing (Regular/Weekend/Holiday)
- ✅ Payment processing and booking confirmation
- ❌ Real payment gateway integration, loyalty programs, food ordering

---

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Singleton** | Single system instance | `BookingSystem.get_instance()` |
| **Strategy** | Pluggable pricing algorithms | `PricingStrategy` + `RegularPricing`, `WeekendPricing`, `HolidayPricing` |
| **Observer** | Event notifications | `BookingObserver` interface + `EmailNotifier`, `SMSNotifier` |
| **State** | Booking status transitions | Enums: `BookingStatus` (PENDING → LOCKED → CONFIRMED) |
| **Factory** | Create seats | `SeatFactory` methods in `Hall.generate_seat_layout()` |
| **Decorator** | Apply discounts | `DiscountDecorator` for student/senior/bulk discounts |

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
class SeatType(Enum):
    REGULAR = 1
    PREMIUM = 2
    VIP = 3

class SeatStatus(Enum):
    AVAILABLE = "available"
    LOCKED = "locked"
    BOOKED = "booked"

class BookingStatus(Enum):
    PENDING = "pending"
    LOCKED = "locked"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    UPI = "upi"
    WALLET = "wallet"

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
```

### 1. Movie Class

```python
class Movie:
    """Represents a movie"""
    def __init__(self, movie_id: str, title: str, duration: int, 
                 genre: List[str], language: str, rating: str):
        self.movie_id = movie_id
        self.title = title
        self.duration = duration  # minutes
        self.genre = genre
        self.language = language
        self.rating = rating
        self.created_at = datetime.now()
    
    def get_duration_formatted(self) -> str:
        hours = self.duration // 60
        minutes = self.duration % 60
        return f"{hours}h {minutes}m"
```

### 2. Seat Class

```python
class Seat:
    """Represents a single seat in a hall"""
    def __init__(self, seat_id: str, row: str, number: int, seat_type: SeatType):
        self.seat_id = seat_id
        self.row = row
        self.number = number
        self.seat_type = seat_type
        self.status = SeatStatus.AVAILABLE
        self.locked_until: Optional[datetime] = None
        self.locked_by: Optional[str] = None  # user_id
        self.price_multiplier = self._get_multiplier()
    
    def _get_multiplier(self) -> float:
        if self.seat_type == SeatType.REGULAR:
            return 1.0
        elif self.seat_type == SeatType.PREMIUM:
            return 1.3
        else:  # VIP
            return 1.5
    
    def is_available(self) -> bool:
        if self.status == SeatStatus.AVAILABLE:
            return True
        if self.status == SeatStatus.LOCKED:
            if datetime.now() > self.locked_until:
                self.unlock()
                return True
        return False
    
    def lock(self, user_id: str, duration_minutes: int = 10):
        if not self.is_available():
            raise ValueError(f"Seat {self.seat_id} not available")
        self.status = SeatStatus.LOCKED
        self.locked_by = user_id
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
    
    def unlock(self):
        self.status = SeatStatus.AVAILABLE
        self.locked_by = None
        self.locked_until = None
    
    def book(self):
        self.status = SeatStatus.BOOKED
```

### 3. Hall Class

```python
class Hall:
    """Represents a screening hall in a theater"""
    def __init__(self, hall_id: str, hall_number: str, capacity: int):
        self.hall_id = hall_id
        self.hall_number = hall_number
        self.capacity = capacity
        self.seat_layout: List[List[Seat]] = []
    
    def generate_seat_layout(self, rows: int, cols: int):
        """Generate seat layout with mixed types"""
        row_letters = [chr(65 + i) for i in range(rows)]  # A, B, C...
        
        for idx, row in enumerate(row_letters):
            row_seats = []
            for num in range(1, cols + 1):
                # First 2 rows are VIP, next 2 are Premium, rest Regular
                if idx < 2:
                    seat_type = SeatType.VIP
                elif idx < 4:
                    seat_type = SeatType.PREMIUM
                else:
                    seat_type = SeatType.REGULAR
                
                seat_id = f"{row}{num}"
                seat = Seat(seat_id, row, num, seat_type)
                row_seats.append(seat)
            self.seat_layout.append(row_seats)
    
    def get_seat(self, seat_id: str) -> Optional[Seat]:
        """Get seat by ID like 'A1', 'B5'"""
        for row in self.seat_layout:
            for seat in row:
                if seat.seat_id == seat_id:
                    return seat
        return None
    
    def get_available_seats(self) -> List[Seat]:
        """Get all available seats"""
        available = []
        for row in self.seat_layout:
            for seat in row:
                if seat.is_available():
                    available.append(seat)
        return available
```

### 4. Theater Class

```python
class Theater:
    """Represents a cinema theater"""
    def __init__(self, theater_id: str, name: str, location: str, city: str):
        self.theater_id = theater_id
        self.name = name
        self.location = location
        self.city = city
        self.halls: Dict[str, Hall] = {}
    
    def add_hall(self, hall: Hall):
        self.halls[hall.hall_id] = hall
```

### 5. Show Class

```python
class Show:
    """Represents a movie screening"""
    def __init__(self, show_id: str, movie: Movie, hall: Hall, 
                 start_time: datetime, base_price: float):
        self.show_id = show_id
        self.movie = movie
        self.hall = hall
        self.start_time = start_time
        self.end_time = start_time + timedelta(minutes=movie.duration)
        self.base_price = base_price
    
    def get_available_seats(self) -> List[Seat]:
        return self.hall.get_available_seats()
```

### 6. User Class

```python
class User:
    """Represents a customer"""
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.bookings: List['Booking'] = []
```

### 7. Payment Class

```python
class Payment:
    """Represents a payment transaction"""
    def __init__(self, payment_id: str, amount: float, method: PaymentMethod):
        self.payment_id = payment_id
        self.amount = amount
        self.payment_method = method
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
    
    def process(self) -> bool:
        """Simulate payment processing"""
        # In real system, integrate with payment gateway
        self.status = PaymentStatus.SUCCESS
        return True
```

### 8. Booking Class

```python
class Booking:
    """Represents a booking"""
    def __init__(self, booking_id: str, user: User, show: Show, seats: List[Seat]):
        self.booking_id = booking_id
        self.user = user
        self.show = show
        self.seats = seats
        self.status = BookingStatus.PENDING
        self.total_amount = 0.0
        self.payment: Optional[Payment] = None
        self.booking_time = datetime.now()
    
    def calculate_total(self, pricing_strategy: 'PricingStrategy') -> float:
        """Calculate total price using pricing strategy"""
        total = 0.0
        for seat in self.seats:
            price = pricing_strategy.calculate_price(self.show.base_price, seat)
            total += price
        return total
    
    def confirm(self):
        """Confirm booking after payment"""
        self.status = BookingStatus.CONFIRMED
        for seat in self.seats:
            seat.book()
    
    def cancel(self):
        """Cancel booking and release seats"""
        self.status = BookingStatus.CANCELLED
        for seat in self.seats:
            seat.unlock()
```

---

## Pricing Strategy (Strategy Pattern)

```python
class PricingStrategy(ABC):
    """Abstract strategy for calculating seat price"""
    @abstractmethod
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        pass

class RegularPricing(PricingStrategy):
    """Regular weekday pricing"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier

class WeekendPricing(PricingStrategy):
    """Weekend pricing with 50% markup"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        base = base_price * seat.price_multiplier
        return base * 1.5  # 50% weekend surcharge

class HolidayPricing(PricingStrategy):
    """Holiday pricing with 100% markup"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        base = base_price * seat.price_multiplier
        return base * 2.0  # 100% holiday surcharge
```

---

## Observer Pattern (Notifications)

```python
class BookingObserver(ABC):
    """Observer interface for booking events"""
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class EmailNotifier(BookingObserver):
    """Email notification observer"""
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"📧 Email sent to {booking.user.email}: Booking confirmed!")
        elif event == "booking_cancelled":
            print(f"📧 Email sent to {booking.user.email}: Booking cancelled.")

class SMSNotifier(BookingObserver):
    """SMS notification observer"""
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"📱 SMS sent to {booking.user.phone}: Your booking is confirmed!")

class ConsoleObserver(BookingObserver):
    """Console-based observer for demo purposes"""
    def update(self, event: str, booking: Booking):
        timestamp = datetime.now().strftime("%H:%M:%S")
        seats_str = ", ".join([s.seat_id for s in booking.seats])
        print(f"[{timestamp}] {event.upper():20} | "
              f"User: {booking.user.name:15} | "
              f"Show: {booking.show.show_id:8} | "
              f"Seats: {seats_str:15} | "
              f"Total: ${booking.total_amount:.2f}")
```

---

## BookingSystem (Singleton + Controller)

```python
class BookingSystem:
    """Singleton controller for movie ticket booking"""
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
            self.movies: Dict[str, Movie] = {}
            self.theaters: Dict[str, Theater] = {}
            self.shows: Dict[str, Show] = {}
            self.bookings: Dict[str, Booking] = {}
            self.users: Dict[str, User] = {}
            self.observers: List[BookingObserver] = []
            self.pricing_strategy: PricingStrategy = RegularPricing()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'BookingSystem':
        """Get singleton instance"""
        return BookingSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Switch pricing algorithm dynamically"""
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: BookingObserver):
        """Subscribe to booking events"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(event, booking)
    
    def search_movies(self, query: str = "", genre: str = "") -> List[Movie]:
        """Search movies by title or genre"""
        results = []
        for movie in self.movies.values():
            if query and query.lower() not in movie.title.lower():
                continue
            if genre and genre not in movie.genre:
                continue
            results.append(movie)
        return results
    
    def get_shows_by_movie(self, movie_id: str) -> List[Show]:
        """Get all shows for a movie"""
        return [show for show in self.shows.values() 
                if show.movie.movie_id == movie_id]
    
    def lock_seats(self, user_id: str, show_id: str, 
                   seat_ids: List[str]) -> Optional[Booking]:
        """Lock seats for a user"""
        if show_id not in self.shows:
            print(f"❌ Show {show_id} not found")
            return None
        
        show = self.shows[show_id]
        user = self.users.get(user_id)
        
        if not user:
            print(f"❌ User {user_id} not found")
            return None
        
        # Get seats and check availability
        seats = []
        for seat_id in seat_ids:
            seat = show.hall.get_seat(seat_id)
            if not seat or not seat.is_available():
                print(f"❌ Seat {seat_id} not available")
                return None
            seats.append(seat)
        
        # Lock all seats
        for seat in seats:
            seat.lock(user_id)
        
        # Create booking
        booking_id = f"BK{len(self.bookings)+1:04d}"
        booking = Booking(booking_id, user, show, seats)
        booking.status = BookingStatus.LOCKED
        booking.total_amount = booking.calculate_total(self.pricing_strategy)
        
        self.bookings[booking_id] = booking
        self.notify_observers("seats_locked", booking)
        
        return booking
    
    def confirm_booking(self, booking_id: str, 
                       payment_method: PaymentMethod) -> bool:
        """Confirm booking with payment"""
        booking = self.bookings.get(booking_id)
        if not booking:
            print(f"❌ Booking {booking_id} not found")
            return False
        
        if booking.status != BookingStatus.LOCKED:
            print("❌ Booking not in LOCKED status")
            return False
        
        # Process payment
        payment = Payment(f"PAY{len(self.bookings)}", 
                         booking.total_amount, payment_method)
        if payment.process():
            booking.payment = payment
            booking.confirm()
            self.notify_observers("booking_confirmed", booking)
            return True
        
        return False
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return False
        
        booking.cancel()
        self.notify_observers("booking_cancelled", booking)
        return True
```

---

## UML Class Diagram

```
┌────────────────────────────────────────────┐
│      BookingSystem (Singleton)             │
├────────────────────────────────────────────┤
│ - _instance: BookingSystem                 │
│ - movies: Dict[str, Movie]                 │
│ - theaters: Dict[str, Theater]             │
│ - shows: Dict[str, Show]                   │
│ - bookings: Dict[str, Booking]             │
│ - users: Dict[str, User]                   │
│ - pricing_strategy: PricingStrategy        │
│ - observers: List[BookingObserver]         │
├────────────────────────────────────────────┤
│ + get_instance(): BookingSystem            │
│ + search_movies(query): List[Movie]        │
│ + get_shows_by_movie(movie): List[Show]    │
│ + lock_seats(...): Booking                 │
│ + confirm_booking(...): bool               │
│ + cancel_booking(...): bool                │
│ + notify_observers(event, booking)         │
└────────────────────────────────────────────┘
                    │
                    │ manages
                    ▼
    ┌───────────────────────────────┐
    │          Movie                │
    ├───────────────────────────────┤
    │ - movie_id: str               │
    │ - title: str                  │
    │ - duration: int               │
    │ - genre: List[str]            │
    │ - language: str               │
    │ - rating: str                 │
    ├───────────────────────────────┤
    │ + get_duration_formatted()    │
    └───────────────────────────────┘
                    │
                    │ screened in
                    ▼
    ┌───────────────────────────────┐
    │          Theater              │
    ├───────────────────────────────┤
    │ - theater_id: str             │
    │ - name: str                   │
    │ - location: str               │
    │ - city: str                   │
    │ - halls: Dict[str, Hall]      │
    ├───────────────────────────────┤
    │ + add_hall(hall)              │
    └───────────────────────────────┘
                    │
                    │ contains
                    ▼
    ┌───────────────────────────────┐
    │           Hall                │
    ├───────────────────────────────┤
    │ - hall_id: str                │
    │ - capacity: int               │
    │ - seat_layout: List[List]     │
    ├───────────────────────────────┤
    │ + generate_seat_layout()      │
    │ + get_seat(seat_id)           │
    │ + get_available_seats()       │
    └───────────────────────────────┘
                    │
                    │ has
                    ▼
    ┌───────────────────────────────┐
    │          Show                 │
    ├───────────────────────────────┤
    │ - show_id: str                │
    │ - movie: Movie                │
    │ - hall: Hall                  │
    │ - start_time: datetime        │
    │ - base_price: float           │
    ├───────────────────────────────┤
    │ + get_available_seats()       │
    └───────────────────────────────┘
                    │
                    │ contains
                    ▼
    ┌───────────────────────────────┐
    │          Seat                 │
    ├───────────────────────────────┤
    │ - seat_id: str                │
    │ - row: str                    │
    │ - number: int                 │
    │ - seat_type: SeatType         │
    │ - status: SeatStatus          │
    │ - locked_until: datetime      │
    │ - price_multiplier: float     │
    ├───────────────────────────────┤
    │ + is_available(): bool        │
    │ + lock(user_id)               │
    │ + unlock()                    │
    │ + book()                      │
    └───────────────────────────────┘

    ┌──────────────────────────────────────┐
    │  PricingStrategy (Abstract)          │
    ├──────────────────────────────────────┤
    │ + calculate_price(base, seat)        │
    └────────────┬─────────────────────────┘
                 │
         ┌───────┴──────────┬──────────────┐
         ▼                  ▼              ▼
    ┌──────────┐    ┌──────────┐  ┌──────────────┐
    │ Regular  │    │ Weekend  │  │   Holiday    │
    │ Pricing  │    │ Pricing  │  │   Pricing    │
    └──────────┘    └──────────┘  └──────────────┘

    ┌──────────────────────────────────────┐
    │  BookingObserver (Abstract)          │
    ├──────────────────────────────────────┤
    │ + update(event: str, booking)        │
    └────────────┬─────────────────────────┘
                 │
         ┌───────┴──────────┬──────────────┐
         ▼                  ▼              ▼
    ┌──────────┐    ┌──────────┐  ┌──────────────┐
    │  Email   │    │   SMS    │  │   Console    │
    │ Notifier │    │ Notifier │  │   Observer   │
    └──────────┘    └──────────┘  └──────────────┘
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking of the same seat?**

A: Use enum-based status transitions (AVAILABLE → LOCKED → BOOKED) with timestamp-based locking. Each seat has `locked_until` timestamp. Before locking, check if seat is available or if lock expired. Lock seats atomically within a transaction. For distributed systems, use Redis distributed locks.

**Q2: What's the difference between LOCKED and CONFIRMED booking status?**

A: LOCKED means seats are temporarily reserved (10 minutes) during checkout. User is selecting seats but hasn't paid yet. CONFIRMED finalizes the booking after successful payment. Locked seats automatically expire and release if payment not completed within timeout.

**Q3: Why use Strategy pattern for pricing?**

A: Allows plugging different pricing algorithms (Regular weekday, Weekend +50%, Holiday +100%, Surge pricing) without modifying booking logic. Easy to test each strategy independently, add new strategies, and switch dynamically based on show date/time.

### Intermediate Questions

**Q4: How do you handle seat lock expiry?**

A: Store `locked_until` timestamp when locking seat. Before any operation, check if `now > locked_until`. If expired, automatically call `unlock()` which resets status to AVAILABLE. Also run periodic background job (every minute) to clean up expired locks proactively.

**Q5: How would you scale this to 100+ theaters with 10k concurrent bookings?**

A: 
- Database sharding by theater/city
- Redis for distributed seat locks with TTL
- Cache hot data (popular movies, show times) with 5-min TTL
- Read replicas for search/browse operations
- Message queue (Kafka) for async notifications
- Load balancer across multiple API servers
- CDN for static content (movie posters)

**Q6: How to handle payment failures gracefully?**

A: Implement retry mechanism with exponential backoff (3 attempts). On final failure, release locked seats, update booking status to FAILED, notify user via email/SMS, log for manual review. If partial payment captured, initiate automatic refund.

### Advanced Questions

**Q7: How do you prevent seat hoarding by bots?**

A: Multi-layer protection:
- Rate limiting: Max 5 seat selections per minute per user
- CAPTCHA on booking page
- Require valid payment method before locking seats
- Monitor and flag users with >5 cancelled bookings
- Detect rapid lock/unlock patterns
- IP-based throttling

**Q8: How would you implement a cancellation policy with refunds?**

A: Add `CancellationPolicy` enum (FULL_REFUND, 50%, 25%, NON_REFUNDABLE) based on time before show. On cancel, calculate refund amount, call `PaymentService.refund()`, update booking status to CANCELLED, release seats, send confirmation email. Use idempotent operations.

**Q9: How to handle show scheduling conflicts?**

A: Before creating show, check if hall is occupied:
```python
proposed_end = start_time + movie.duration + buffer_time (30 min)
conflicts = hall.get_shows_between(start_time, proposed_end)
if conflicts:
    raise SchedulingConflictError
```
Maintain buffer time for cleaning between shows.

**Q10: What metrics would you track for this system?**

A: 
**Business**: Bookings/day, Revenue/theater, Occupancy rate, Popular movies, Cancellation rate
**Performance**: API latency (p50, p95, p99), Seat lock success rate, Payment success rate, Cache hit ratio
**System**: Error rate, DB connection pool usage, Queue lag, Redis memory
**User**: Search-to-booking conversion, Average booking value, User retention

---

## Demo Script

```python
from datetime import datetime, timedelta

def run_demo():
    print("=" * 70)
    print("MOVIE TICKET BOOKING SYSTEM - DEMO")
    print("=" * 70)
    
    system = BookingSystem.get_instance()
    system.add_observer(ConsoleObserver())
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    # Setup: Create movie, theater, show
    movie = Movie("MOV001", "Inception", 148, 
                  ["Sci-Fi", "Thriller"], "English", "PG-13")
    system.add_movie(movie)
    
    theater = Theater("THR001", "PVR Cinemas", "Downtown", "NYC")
    hall = Hall("HALL001", "Hall 1", 60)
    hall.generate_seat_layout(6, 10)
    theater.add_hall(hall)
    system.add_theater(theater)
    
    show = Show("SHW001", movie, hall, 
               datetime.now() + timedelta(hours=2), 15.0)
    system.add_show(show)
    
    # Register users
    user1 = User("USR001", "Alice Johnson", "alice@example.com", "+1234567890")
    system.register_user(user1)
    
    print("\n[DEMO 1] Search & Browse")
    print("-" * 70)
    results = system.search_movies(query="Inception")
    print(f"Found {len(results)} movies")
    
    print("\n[DEMO 2] Seat Selection & Locking")
    print("-" * 70)
    booking = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    print(f"Locked seats - Total: ${booking.total_amount:.2f}")
    
    print("\n[DEMO 3] Dynamic Pricing")
    print("-" * 70)
    system.set_pricing_strategy(WeekendPricing())
    print("Switched to Weekend Pricing (+50%)")
    
    print("\n[DEMO 4] Payment & Confirmation")
    print("-" * 70)
    success = system.confirm_booking(booking.booking_id, PaymentMethod.CREDIT_CARD)
    if success:
        print(f"✅ Booking confirmed!")
    
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total bookings: {len(system.bookings)}")
    print(f"Available seats: {len(show.get_available_seats())}")

if __name__ == "__main__":
    run_demo()
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Seat Locking** | 10-minute timeout with auto-expiry; prevents double-booking |
| **Extensibility** | Strategy pattern for pricing; Observer for notifications |
| **Reliability** | Enum-based state transitions; explicit status checks |
| **Scalability** | Redis locks; database sharding; message queues |
| **Testing** | Mock Observer; mock PricingStrategy; unit tests per component |

---

## Interview Tips

1. **Clarify scope early** — Ask questions before designing
2. **Sketch seat layout** — Use 2D grid visualization
3. **Explain patterns as you code** — Show design thinking
4. **Handle edge cases** — Lock expiry, double-booking, payment failure
5. **Discuss trade-offs** — Optimistic vs pessimistic locking, cache invalidation
6. **Demo incrementally** — Show browse → select → lock → pay → confirm
7. **Mention scalability** — But don't over-engineer for interview
8. **Ask follow-up questions** — "Would you want refund policies?" (shows maturity)
