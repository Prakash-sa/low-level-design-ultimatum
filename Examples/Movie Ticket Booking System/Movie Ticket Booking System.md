# Movie Ticket Booking System — Complete Design Guide

> Multi-theater booking platform for browsing, seat selection, dynamic pricing, and reservation management.

**Scale**: 1,000+ concurrent users, 100+ theaters, 10K+ bookings/day, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Seat locking, dynamic pricing, booking lifecycle, state management

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
Customers browse movies → select shows → lock seats (temporary 10-min reservation) → pay → confirm booking → receive confirmation. Prevent double-booking through atomic seat locking and status transitions.

### Core Flow
```
Browse Movies → Select Show → LOCK SEATS (10 min) → PAYMENT → CONFIRM (permanent)
                                      ↓ or timeout
                                  AUTO-UNLOCK (seats released)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single theater or multi-theater?** → "Multi-theater, 100+ theaters"
2. **Multiple seat types?** → "Yes — Regular, Premium, VIP with different price multipliers"
3. **Real payment processing?** → "Mock payment service for interview"
4. **Cancellations after confirmation?** → "Yes, time-based refund policy"
5. **Single machine or distributed?** → "Distributed system with 1,000+ concurrent users"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer/User** | Browse & book tickets | Search movies, select seats, lock, pay, confirm, cancel |
| **Theater Admin** | Manage shows & halls | Create shows, configure halls, set base prices |
| **System** | Controller & notifier | Auto-expire locks, send notifications, update seat status |

### Functional Requirements (What does the system do?)

✅ **Movie Listings & Search**
  - Search movies by title, genre, language
  - Browse shows by movie with available seat counts

✅ **Seat Layout & Selection**
  - 2D grid layout (rows A-F, seats 1-10, types: Regular/Premium/VIP)
  - Real-time availability check per show

✅ **Seat Locking (Hold)**
  - Temporarily lock seats for 10 minutes during checkout
  - Atomic lock — prevent double-booking of same seat
  - Auto-expire lock if user abandons checkout

✅ **Dynamic Pricing**
  - Regular weekday: base price × seat multiplier
  - Weekend: base × 1.5 surcharge
  - Holiday: base × 2.0 surcharge

✅ **Payment & Booking Confirmation**
  - Process payment (mock) and confirm booking
  - Permanently mark seats as BOOKED on success
  - Release locks and cancel booking on payment failure

✅ **Cancellation**
  - Cancel confirmed booking with time-based refund
  - Release seats back to AVAILABLE

✅ **Notifications**
  - Notify on lock success, booking confirmation, cancellation
  - Support Email, SMS, Console channels

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 1,000+ simultaneous users locking/confirming seats  
✅ **Consistency**: No double-selling (atomic locking with auto-expiry)  
✅ **Availability**: Real-time seat status, <100ms search, <500ms lock response  
✅ **Uptime**: 99.9% (8.6 hours downtime/month allowed)  
✅ **Lock Expiry Accuracy**: ±1 min tolerance acceptable  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES - multi-region with load-balanced replicas |
| **Single theater?** | NO - 100+ theaters, sharded by theater_id |
| **Real payment?** | NO - mock service (failure path still tested) |
| **Overbooking allowed?** | NO - atomic lock prevents overselling |
| **Seat lock timeout** | Fixed 10 minutes |
| **Cancellation fee?** | Time-based: Full refund if >6h, 50% if >2h, 25% if >30min, 0% otherwise |
| **Food/beverages?** | Out of scope |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
Movie, Cinema/Theater, Hall, Show, Seat, Booking, Payment, User, BookingSystem, ...
```

### Step 2.2: Define Core Classes

#### **Movie** — A film with metadata
```
Properties:
  - movie_id: str (e.g., "MOV001")
  - title: str (e.g., "Inception")
  - duration: int (minutes)
  - genre: List[str] (e.g., ["Sci-Fi", "Thriller"])
  - language: str
  - rating: str (e.g., "PG-13")

Behaviors:
  - get_duration_formatted(): Return "2h 28m" style string
```

#### **Theater** — A physical cinema venue
```
Properties:
  - theater_id: str
  - name: str
  - location: str
  - city: str
  - halls: Dict[str, Hall]

Behaviors:
  - add_hall(hall): Register a hall in this theater
```

#### **Hall** — A screening room inside a theater
```
Properties:
  - hall_id: str
  - hall_number: str
  - capacity: int
  - seat_layout: List[List[Seat]] (2D grid)

Behaviors:
  - generate_seat_layout(rows, cols): Create rows × cols seats with type assignment
  - get_seat(seat_id): Retrieve a seat by ID
  - get_available_seats(): Return all currently AVAILABLE seats
```

#### **Show** — A specific screening of a movie in a hall
```
Properties:
  - show_id: str
  - movie: Movie
  - hall: Hall
  - start_time: datetime
  - end_time: datetime (computed from movie duration)
  - base_price: float

Behaviors:
  - get_available_seats(): Delegate to hall
```

#### **Seat** — A single seat in a hall for a show
```
Properties:
  - seat_id: str (e.g., "A1", "C5")
  - row: str
  - number: int
  - seat_type: SeatType (REGULAR, PREMIUM, VIP)
  - status: SeatStatus (AVAILABLE, LOCKED, BOOKED)
  - locked_until: Optional[datetime]
  - locked_by: Optional[str]
  - price_multiplier: float (1.0 / 1.3 / 1.5)

Behaviors:
  - is_available(): Check status + auto-expire stale lock
  - lock(user_id, duration_minutes): Transition to LOCKED
  - unlock(): Transition back to AVAILABLE
  - book(): Transition to BOOKED (permanent)
```

#### **Booking** — A reservation linking user, show, and seats
```
Properties:
  - booking_id: str
  - user: User
  - show: Show
  - seats: List[Seat]
  - status: BookingStatus (PENDING, LOCKED, CONFIRMED, CANCELLED, COMPLETED)
  - total_amount: float
  - payment: Optional[Payment]

Behaviors:
  - calculate_total(strategy): Sum prices across all booked seats
  - confirm(): Mark CONFIRMED, book all seats permanently
  - cancel(): Mark CANCELLED, unlock all seats
```

#### **Payment** — A payment transaction for a booking
```
Properties:
  - payment_id: str
  - amount: float
  - payment_method: PaymentMethod
  - status: PaymentStatus (PENDING, SUCCESS, FAILED)

Behaviors:
  - process(): Simulate payment; return True on success
```

#### **User** — A registered customer
```
Properties:
  - user_id: str
  - name: str
  - email: str
  - phone: str
  - bookings: List[Booking]

Behaviors:
  - (data holder; bookings tracked by system)
```

#### **BookingSystem** — Main controller (Singleton)
```
Properties:
  - movies: Dict[str, Movie]
  - theaters: Dict[str, Theater]
  - shows: Dict[str, Show]
  - bookings: Dict[str, Booking]
  - users: Dict[str, User]
  - pricing_strategy: PricingStrategy
  - observers: List[BookingObserver]

Behaviors:
  - search_movies(query, genre): Filter movie catalog
  - lock_seats(user_id, show_id, seat_ids): Atomically lock seats, create booking
  - confirm_booking(booking_id, method): Process payment and confirm
  - cancel_booking(booking_id): Release seats and mark cancelled
  - set_pricing_strategy(strategy): Swap pricing algorithm at runtime
  - notify_observers(event, booking): Broadcast event to all listeners
```

### Step 2.3: Define Enumerations (State & Type)

```python
class SeatType(Enum):
    REGULAR = 1        # price_multiplier = 1.0
    PREMIUM = 2        # price_multiplier = 1.3
    VIP = 3            # price_multiplier = 1.5

class SeatStatus(Enum):
    AVAILABLE = "available"   # Can be locked
    LOCKED = "locked"         # Temporarily reserved (10-min window)
    BOOKED = "booked"         # Permanently booked after payment

class BookingStatus(Enum):
    PENDING = "pending"       # Created but not yet locked
    LOCKED = "locked"         # Seats locked; user in checkout
    CONFIRMED = "confirmed"   # Payment succeeded; booking permanent
    CANCELLED = "cancelled"   # User cancelled or payment failed
    COMPLETED = "completed"   # Show has passed

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    UPI = "upi"
    WALLET = "wallet"

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Movie** | Searchable catalog item | Can't browse or filter shows |
| **Theater** | Groups halls by venue | Can't organize inventory geographically |
| **Hall** | Owns the 2D seat grid | Can't represent physical seating |
| **Show** | Links movie + hall + time | Can't schedule or price a screening |
| **Seat** | Granular lock & booking target | Can't prevent double-booking |
| **Booking** | Lock/confirm lifecycle | Can't manage holds or payment state |
| **Payment** | Tracks payment status | Can't distinguish paid from abandoned |
| **User** | Associates bookings to person | Can't send notifications or cancel |
| **BookingSystem** | Central thread-safe controller | No coordinated concurrency control |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Search Movies**
```python
def search_movies(query: str = "", genre: str = "") -> List[Movie]:
    """
    Find movies matching title substring and/or genre.
    Returns: List of Movie objects.
    Response Time: <100ms (cached)
    """
    pass
```

#### **2. Get Shows for a Movie**
```python
def get_shows_by_movie(movie_id: str) -> List[Show]:
    """
    Return all upcoming shows for a given movie.
    Returns: List of Show objects with available seat counts.
    Raises: MovieNotFoundError if movie_id invalid.
    Response Time: <100ms
    """
    pass
```

#### **3. Lock Seats** ⭐ CRITICAL
```python
def lock_seats(user_id: str, show_id: str, seat_ids: List[str],
               lock_minutes: int = 10) -> Booking:
    """
    Atomically reserve a set of seats for 10 minutes.

    Precondition: all seats.status == AVAILABLE
    Postcondition: all seats.status == LOCKED, booking.status == LOCKED

    Returns: Booking object with booking_id, total_amount, lock expiry.

    Raises:
      - SeatNotAvailableError: One or more seats already locked/booked
      - ShowNotFoundError: show_id invalid
      - UserNotFoundError: user_id not registered
      - SeatNotFoundError: seat_id not in hall

    Concurrency: THREAD-SAFE with all-or-nothing rollback
    Response Time: <500ms
    Idempotency: NO (retrying creates a new booking)
    """
    pass
```

#### **4. Confirm Booking** ⭐ CRITICAL
```python
def confirm_booking(booking_id: str, method: PaymentMethod) -> bool:
    """
    Process payment and permanently confirm a LOCKED booking.

    Precondition: booking.status == LOCKED
    Postcondition: booking.status == CONFIRMED, seats.status == BOOKED

    Returns: True if success, False if payment failed or lock expired.

    Raises:
      - BookingNotFoundError: booking_id invalid
      - BookingExpiredError: Lock window closed before confirmation
      - BookingNotLockedError: Booking not in LOCKED state

    Side Effects: Sends confirmation notification to user (email/SMS)
    Response Time: <500ms
    """
    pass
```

#### **5. Cancel Booking**
```python
def cancel_booking(booking_id: str) -> bool:
    """
    Cancel a booking and release seats back to AVAILABLE.

    Precondition: booking.status in [LOCKED, CONFIRMED]
    Postcondition: booking.status == CANCELLED, seats.status == AVAILABLE

    Returns: True if cancelled, False otherwise.

    Raises:
      - BookingNotFoundError: booking_id invalid

    Side Effects:
      - Calculates refund based on time_until_show
      - Sends cancellation notification
    """
    pass
```

#### **6. Set Pricing Strategy**
```python
def set_pricing_strategy(strategy: PricingStrategy) -> None:
    """
    Dynamically switch pricing algorithm at runtime.
    New pricing applies to all subsequent lock_seats() calls.

    Strategy: Pluggable (RegularPricing, WeekendPricing, HolidayPricing)
    """
    pass
```

#### **7. Register Observer** (For Notifications)
```python
def add_observer(observer: BookingObserver) -> None:
    """
    Register a callback for booking lifecycle events.

    Events: "seats_locked", "booking_confirmed", "booking_cancelled"
    Observer called as: observer.update(event, booking)

    Example: Add EmailNotifier and SMSNotifier for multi-channel alerts.
    """
    pass
```

### Step 3.2: Exception Hierarchy

```python
class BookingException(Exception):
    """Base exception for all booking errors"""
    pass

class SeatNotAvailableError(BookingException):
    """One or more seats already locked or booked"""
    pass

class BookingExpiredError(BookingException):
    """Lock window closed before confirmation"""
    pass

class ShowNotFoundError(BookingException):
    """Show ID does not exist"""
    pass

class UserNotFoundError(BookingException):
    """User not registered in system"""
    pass
```

### Step 3.3: API Usage Example

```python
system = BookingSystem.get_instance()

# 1. Search movies
movies = system.search_movies(query="Inception")

# 2. Find shows
shows = system.get_shows_by_movie("MOV001")
show = shows[0]

# 3. LOCK seats
booking = system.lock_seats(
    user_id="USR001",
    show_id="SHW001",
    seat_ids=["A1", "A2"]
)
print(f"Booking ID: {booking.booking_id}, Total: ${booking.total_amount:.2f}")

# 4. CONFIRM booking
success = system.confirm_booking(booking.booking_id, PaymentMethod.CREDIT_CARD)

# 5. CANCEL booking (if needed)
system.cancel_booking(booking.booking_id)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
BookingSystem HAS-A movies (1:N Composition)
  └─ BookingSystem owns all movies; movies die if system resets

BookingSystem HAS-A theaters (1:N Composition)
  └─ BookingSystem owns all theater objects

Theater HAS-A halls (1:N Composition)
  └─ Theater contains and owns multiple Hall objects

Hall HAS-A seat_layout (1:N Composition)
  └─ Hall owns the 2D grid of Seat objects

Show REFERENCES movie (1:1 Association)
  └─ Show links to Movie (no ownership; movie outlives show)

Show REFERENCES hall (1:1 Association)
  └─ Show uses a Hall (no ownership)

Booking REFERENCES user (1:1 Association)
  └─ Booking links to User (no ownership)

Booking REFERENCES show (1:1 Association)
  └─ Booking links to Show (no ownership)

Booking REFERENCES seats (1:N Association)
  └─ Booking links multiple Seat objects (no ownership)

BookingSystem USES-A PricingStrategy (1:1 Composition)
  └─ BookingSystem owns and manages current pricing algorithm

BookingSystem NOTIFIES BookingObserver (1:N Association)
  └─ Multiple observers listen to booking lifecycle events
```

### Step 4.2: Complete UML Class Diagram

```
┌─────────────────────────────────────────┐
│      BookingSystem (Singleton)          │
├─────────────────────────────────────────┤
│ - _instance: BookingSystem              │
│ - movies: Dict[str, Movie]              │
│ - theaters: Dict[str, Theater]          │
│ - shows: Dict[str, Show]                │
│ - bookings: Dict[str, Booking]          │
│ - users: Dict[str, User]                │
│ - pricing_strategy: PricingStrategy     │
│ - observers: List[BookingObserver]      │
├─────────────────────────────────────────┤
│ + get_instance(): BookingSystem         │
│ + search_movies(query, genre)           │
│ + get_shows_by_movie(movie_id)          │
│ + lock_seats(user, show, seat_ids)      │
│ + confirm_booking(booking_id, method)   │
│ + cancel_booking(booking_id)            │
│ + set_pricing_strategy(strategy)        │
│ + notify_observers(event, booking)      │
└─────────────────────────────────────────┘
           │ orchestrates
           ▼
    ┌────────────────────┐
    │     Movie          │
    ├────────────────────┤
    │ - movie_id: str    │
    │ - title: str       │
    │ - duration: int    │
    │ - genre: [str]     │
    │ - language: str    │
    │ - rating: str      │
    └────────────────────┘
           │ screened in
           ▼
    ┌────────────────────┐
    │     Theater        │
    ├────────────────────┤
    │ - theater_id: str  │
    │ - name: str        │
    │ - location: str    │
    │ - city: str        │
    │ - halls: Dict      │
    └────────────────────┘
           │ contains
           ▼
    ┌────────────────────┐
    │      Hall          │
    ├────────────────────┤
    │ - hall_id: str     │
    │ - capacity: int    │
    │ - seat_layout[][]  │
    └────────────────────┘
           │ has
           ▼
    ┌────────────────────┐
    │      Show          │
    ├────────────────────┤
    │ - show_id: str     │
    │ - movie: Movie     │
    │ - hall: Hall       │
    │ - start_time: dt   │
    │ - base_price: float│
    └────────────────────┘
           │ contains
           ▼
    ┌────────────────────────────────┐
    │         Seat                   │
    ├────────────────────────────────┤
    │ - seat_id: str (e.g., "A1")    │
    │ - row: str                     │
    │ - number: int                  │
    │ - seat_type: SeatType          │
    │ - status: SeatStatus           │
    │ - locked_until: datetime       │
    │ - price_multiplier: float      │
    ├────────────────────────────────┤
    │ + is_available(): bool         │
    │ + lock(user_id): void          │
    │ + unlock(): void               │
    │ + book(): void                 │
    └────────────────────────────────┘
           │ linked in
           ▼
    ┌────────────────────────────────┐
    │        Booking                 │
    ├────────────────────────────────┤
    │ - booking_id: str              │
    │ - user: User                   │
    │ - show: Show                   │
    │ - seats: List[Seat]            │
    │ - status: BookingStatus        │
    │ - total_amount: float          │
    │ - payment: Payment             │
    ├────────────────────────────────┤
    │ + calculate_total(strategy)    │
    │ + confirm(): void              │
    │ + cancel(): void               │
    └────────────────────────────────┘

STRATEGY PATTERN (Pricing):
┌──────────────────────────────────┐
│ PricingStrategy (Abstract)       │
│ + calculate_price(base, seat)    │
└──┬───────────────────────────────┘
   │
   ├─→ RegularPricing (base × multiplier)
   ├─→ WeekendPricing (base × 1.5)
   └─→ HolidayPricing (base × 2.0)

OBSERVER PATTERN (Notifications):
┌──────────────────────────────────┐
│ BookingObserver (Abstract)       │
│ + update(event, booking)         │
└──┬───────────────────────────────┘
   │
   ├─→ EmailNotifier
   ├─→ SMSNotifier
   └─→ ConsoleObserver (logs)

ENUMS:
BookingStatus: PENDING → LOCKED → CONFIRMED → CANCELLED/COMPLETED
SeatStatus: AVAILABLE → LOCKED → BOOKED
SeatType: REGULAR (1.0×) | PREMIUM (1.3×) | VIP (1.5×)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| BookingSystem → Movies | 1:N | Composition | System owns all movies |
| BookingSystem → Theaters | 1:N | Composition | System owns all theaters |
| Theater → Halls | 1:N | Composition | Theater owns its halls |
| Hall → Seats | 1:N | Composition | Hall owns the seat grid |
| Show → Movie | 1:1 | Association | Show references a movie |
| Show → Hall | 1:1 | Association | Show uses a hall |
| Booking → User | 1:1 | Association | Booking references one user |
| Booking → Show | 1:1 | Association | Booking references one show |
| Booking → Seats | 1:N | Association | Booking reserves multiple seats |
| BookingSystem → PricingStrategy | 1:1 | Composition | System owns pricing rule |
| BookingSystem → Observers | 1:N | Association | System notifies multiple listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For BookingSystem)

**Problem**: Multiple threads need a single consistent view of shows, bookings, and seat inventory.

**Solution**: One global BookingSystem instance, thread-safe initialization with double-checked locking.

```python
class BookingSystem:
    _instance = None
    _lock = threading.RLock()   # RLock allows re-entrant acquisition

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.movies: Dict[str, Movie] = {}
            # ... other fields
            self.initialized = True
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Harder to scale across machines

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Ticket pricing varies by day/time/demand and must be swappable at runtime.

**Solution**: Pluggable pricing algorithms — Regular, Weekend, Holiday — with a common interface.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier

class WeekendPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier * 1.5

class HolidayPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier * 2.0

# Usage: Switch algorithm at runtime
system.set_pricing_strategy(WeekendPricing())
total = booking.calculate_total(system.pricing_strategy)
```

**Benefit**: ✅ Easy to add new strategies (SurgePricing, MemberDiscount, etc.), ✅ No booking logic change  
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Booking events (lock, confirm, cancel) need to trigger emails/SMS/logging.

**Solution**: Observer pattern decouples event producer (BookingSystem) from consumers (notifiers).

```python
class BookingObserver(ABC):
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class EmailNotifier(BookingObserver):
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"Email: {booking.user.email} - Booking confirmed!")

class SMSNotifier(BookingObserver):
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"SMS: {booking.user.phone} - Booking confirmed!")

class ConsoleObserver(BookingObserver):
    def update(self, event: str, booking: Booking):
        seats = ", ".join([s.seat_id for s in booking.seats])
        print(f"[{event.upper()}] {booking.user.name} | Seats: {seats} | ${booking.total_amount:.2f}")

# Usage
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())
system.notify_observers("booking_confirmed", booking)
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new channels (Push, Slack)  
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 4: **State** (For Seat & Booking Lifecycle)

**Problem**: Seats and bookings move through explicit states; invalid transitions must be caught.

**Solution**: Enums represent states; transition methods enforce valid moves.

```python
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

# Valid transitions enforced in methods:
def lock(self, user_id: str, duration_minutes: int = 10):
    if not self.is_available():          # Guards invalid transitions
        raise ValueError(f"Seat {self.seat_id} not available")
    self.status = SeatStatus.LOCKED
    self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
```

**Benefit**: ✅ Explicit state, ✅ Invalid transitions caught at runtime  
**Trade-off**: ⚠️ Need explicit transition logic in each method

---

### Pattern 5: **Factory** (For Seat Layout Generation)

**Problem**: Creating a full 2D seat grid with correct seat types requires coordination logic.

**Solution**: `generate_seat_layout()` factory method encapsulates creation.

```python
def generate_seat_layout(self, rows: int, cols: int):
    row_letters = [chr(65 + i) for i in range(rows)]
    for idx, row in enumerate(row_letters):
        row_seats = []
        for num in range(1, cols + 1):
            # Assign type based on row position
            seat_type = (SeatType.VIP if idx < 2
                         else SeatType.PREMIUM if idx < 4
                         else SeatType.REGULAR)
            seat = Seat(f"{row}{num}", row, num, seat_type)
            row_seats.append(seat)
        self.seat_layout.append(row_seats)
```

**Benefit**: ✅ Centralized creation, ✅ Consistent type assignment across halls  
**Trade-off**: ⚠️ If layouts grow complex, consider Builder pattern

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---------------|---------|
| **Singleton** | Single global BookingSystem | Consistent state across all clients |
| **Strategy** | Varying pricing algorithms | Pluggable, easy to extend at runtime |
| **Observer** | Events trigger notifications | Loose coupling, event-driven |
| **State (Enum)** | Seat & booking lifecycle | Invalid transitions prevented explicitly |
| **Factory** | 2D seat layout generation | Centralized, consistent initialization |

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

# ============ CORE ENTITIES ============

class Movie:
    def __init__(self, movie_id: str, title: str, duration: int,
                 genre: List[str], language: str, rating: str):
        self.movie_id = movie_id
        self.title = title
        self.duration = duration
        self.genre = genre
        self.language = language
        self.rating = rating

    def get_duration_formatted(self) -> str:
        hours, minutes = divmod(self.duration, 60)
        return f"{hours}h {minutes}m"

class Seat:
    def __init__(self, seat_id: str, row: str, number: int, seat_type: SeatType):
        self.seat_id = seat_id
        self.row = row
        self.number = number
        self.seat_type = seat_type
        self.status = SeatStatus.AVAILABLE
        self.locked_until: Optional[datetime] = None
        self.locked_by: Optional[str] = None
        self.price_multiplier = self._get_multiplier()

    def _get_multiplier(self) -> float:
        return {SeatType.REGULAR: 1.0, SeatType.PREMIUM: 1.3, SeatType.VIP: 1.5}[self.seat_type]

    def is_available(self) -> bool:
        if self.status == SeatStatus.AVAILABLE:
            return True
        if self.status == SeatStatus.LOCKED and self.locked_until and datetime.now() > self.locked_until:
            self.unlock()  # Lazy auto-expiry
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

class Hall:
    def __init__(self, hall_id: str, hall_number: str, capacity: int):
        self.hall_id = hall_id
        self.hall_number = hall_number
        self.capacity = capacity
        self.seat_layout: List[List[Seat]] = []

    def generate_seat_layout(self, rows: int, cols: int):
        row_letters = [chr(65 + i) for i in range(rows)]
        for idx, row in enumerate(row_letters):
            row_seats = []
            for num in range(1, cols + 1):
                seat_type = (SeatType.VIP if idx < 2
                             else SeatType.PREMIUM if idx < 4
                             else SeatType.REGULAR)
                seat = Seat(f"{row}{num}", row, num, seat_type)
                row_seats.append(seat)
            self.seat_layout.append(row_seats)

    def get_seat(self, seat_id: str) -> Optional[Seat]:
        for row in self.seat_layout:
            for seat in row:
                if seat.seat_id == seat_id:
                    return seat
        return None

    def get_available_seats(self) -> List[Seat]:
        return [s for row in self.seat_layout for s in row if s.is_available()]

class Theater:
    def __init__(self, theater_id: str, name: str, location: str, city: str):
        self.theater_id = theater_id
        self.name = name
        self.location = location
        self.city = city
        self.halls: Dict[str, Hall] = {}

    def add_hall(self, hall: Hall):
        self.halls[hall.hall_id] = hall

class Show:
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

class User:
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.bookings: List['Booking'] = []

class Payment:
    def __init__(self, payment_id: str, amount: float, method: PaymentMethod):
        self.payment_id = payment_id
        self.amount = amount
        self.payment_method = method
        self.status = PaymentStatus.PENDING

    def process(self) -> bool:
        self.status = PaymentStatus.SUCCESS
        return True

class Booking:
    def __init__(self, booking_id: str, user: User, show: Show, seats: List[Seat]):
        self.booking_id = booking_id
        self.user = user
        self.show = show
        self.seats = seats
        self.status = BookingStatus.PENDING
        self.total_amount = 0.0
        self.payment: Optional[Payment] = None

    def calculate_total(self, strategy: 'PricingStrategy') -> float:
        return sum(strategy.calculate_price(self.show.base_price, seat) for seat in self.seats)

    def confirm(self):
        self.status = BookingStatus.CONFIRMED
        for seat in self.seats:
            seat.book()

    def cancel(self):
        self.status = BookingStatus.CANCELLED
        for seat in self.seats:
            seat.unlock()

# ============ STRATEGIES ============

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier

class WeekendPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier * 1.5

class HolidayPricing(PricingStrategy):
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier * 2.0

# ============ OBSERVERS ============

class BookingObserver(ABC):
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class EmailNotifier(BookingObserver):
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"Email: {booking.user.email} - Booking confirmed!")

class SMSNotifier(BookingObserver):
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"SMS: {booking.user.phone} - Booking confirmed!")

class ConsoleObserver(BookingObserver):
    def update(self, event: str, booking: Booking):
        seats = ", ".join([s.seat_id for s in booking.seats])
        print(f"[{event.upper()}] {booking.user.name} | Seats: {seats} | ${booking.total_amount:.2f}")

# ============ SINGLETON CONTROLLER ============

class BookingSystem:
    _instance = None
    _lock = threading.RLock()  # RLock: re-entrant safe

    def __new__(cls, *args, **kwargs):
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
            self._data_lock = threading.RLock()  # RLock for re-entrant safety
            self.initialized = True

    @staticmethod
    def get_instance() -> 'BookingSystem':
        return BookingSystem()

    def set_pricing_strategy(self, strategy: PricingStrategy):
        with self._data_lock:
            self.pricing_strategy = strategy

    def add_observer(self, observer: BookingObserver):
        with self._data_lock:
            self.observers.append(observer)

    def notify_observers(self, event: str, booking: Booking):
        with self._data_lock:
            observers_copy = list(self.observers)
        for obs in observers_copy:
            obs.update(event, booking)

    def add_movie(self, movie: Movie):
        with self._data_lock:
            self.movies[movie.movie_id] = movie

    def add_theater(self, theater: Theater):
        with self._data_lock:
            self.theaters[theater.theater_id] = theater

    def add_show(self, show: Show):
        with self._data_lock:
            self.shows[show.show_id] = show

    def register_user(self, user: User):
        with self._data_lock:
            self.users[user.user_id] = user

    def search_movies(self, query: str = "", genre: str = "") -> List[Movie]:
        with self._data_lock:
            results = list(self.movies.values())
        if query:
            results = [m for m in results if query.lower() in m.title.lower()]
        if genre:
            results = [m for m in results if genre in m.genre]
        return results

    def get_shows_by_movie(self, movie_id: str) -> List[Show]:
        with self._data_lock:
            return [s for s in self.shows.values() if s.movie.movie_id == movie_id]

    def lock_seats(self, user_id: str, show_id: str,
                   seat_ids: List[str]) -> Optional[Booking]:
        with self._data_lock:
            show = self.shows.get(show_id)
            user = self.users.get(user_id)
            if not show or not user:
                print(f"Show or user not found")
                return None

            seats = []
            for sid in seat_ids:
                seat = show.hall.get_seat(sid)
                if not seat or not seat.is_available():
                    print(f"Seat {sid} not available")
                    return None
                seats.append(seat)

            # All seats available — lock atomically
            for seat in seats:
                seat.lock(user_id)

            booking_id = f"BK{len(self.bookings)+1:04d}"
            booking = Booking(booking_id, user, show, seats)
            booking.status = BookingStatus.LOCKED
            booking.total_amount = booking.calculate_total(self.pricing_strategy)
            self.bookings[booking_id] = booking
            booking_to_notify = booking

        self.notify_observers("seats_locked", booking_to_notify)
        return booking

    def confirm_booking(self, booking_id: str, method: PaymentMethod) -> bool:
        with self._data_lock:
            booking = self.bookings.get(booking_id)
            if not booking or booking.status != BookingStatus.LOCKED:
                print(f"Booking {booking_id} not found or not in LOCKED state")
                return False

            payment = Payment(f"PAY{len(self.bookings)}", booking.total_amount, method)
            if payment.process():
                booking.payment = payment
                booking.confirm()
                booking_to_notify = booking
            else:
                return False

        self.notify_observers("booking_confirmed", booking_to_notify)
        return True

    def cancel_booking(self, booking_id: str) -> bool:
        with self._data_lock:
            booking = self.bookings.get(booking_id)
            if not booking:
                return False
            booking.cancel()
            booking_to_notify = booking

        self.notify_observers("booking_cancelled", booking_to_notify)
        return True

    def expire_stale_locks(self):
        """Background job: eagerly release expired seat locks."""
        with self._data_lock:
            for show in self.shows.values():
                for row in show.hall.seat_layout:
                    for seat in row:
                        if (seat.status == SeatStatus.LOCKED
                                and seat.locked_until
                                and datetime.now() > seat.locked_until):
                            seat.unlock()

# ============ DEMO ============

if __name__ == "__main__":
    print("=" * 70)
    print("MOVIE TICKET BOOKING SYSTEM")
    print("=" * 70)

    system = BookingSystem.get_instance()
    # Reset state for clean demo
    system.movies.clear()
    system.theaters.clear()
    system.shows.clear()
    system.bookings.clear()
    system.users.clear()
    system.observers.clear()

    system.add_observer(ConsoleObserver())
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())

    # --- Setup ---
    movie = Movie("MOV001", "Inception", 148, ["Sci-Fi", "Thriller"], "English", "PG-13")
    system.add_movie(movie)

    theater = Theater("THR001", "PVR Cinemas", "Downtown", "NYC")
    hall = Hall("HALL001", "Hall 1", 60)
    hall.generate_seat_layout(6, 10)   # 6 rows x 10 seats = 60 seats
    theater.add_hall(hall)
    system.add_theater(theater)

    show = Show("SHW001", movie, hall, datetime.now() + timedelta(hours=2), 15.0)
    system.add_show(show)

    user1 = User("USR001", "Alice", "alice@example.com", "+1234567890")
    user2 = User("USR002", "Bob", "bob@example.com", "+0987654321")
    system.register_user(user1)
    system.register_user(user2)

    print(f"\nSetup: {movie.title} ({movie.get_duration_formatted()}) | "
          f"Hall: {hall.hall_number} | Available: {len(hall.get_available_seats())} seats")

    # --- Demo 1: Search & Lock ---
    print("\n[Demo 1] Search and lock seats:")
    results = system.search_movies(query="Inception")
    print(f"  Found: {len(results)} movie(s)")

    booking1 = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking1:
        print(f"  Locked booking {booking1.booking_id} | Total: ${booking1.total_amount:.2f}")

    # --- Demo 2: Concurrent lock attempt ---
    print("\n[Demo 2] Bob tries same seats (should fail):")
    booking_fail = system.lock_seats("USR002", "SHW001", ["A1", "A2"])
    if not booking_fail:
        print("  Bob's lock rejected - seats already locked by Alice")

    # --- Demo 3: Confirm booking ---
    print("\n[Demo 3] Alice confirms booking:")
    if booking1:
        success = system.confirm_booking(booking1.booking_id, PaymentMethod.CREDIT_CARD)
        print(f"  Confirmation: {'SUCCESS' if success else 'FAILED'}")

    # --- Demo 4: Dynamic pricing ---
    print("\n[Demo 4] Dynamic pricing (Weekend):")
    system.set_pricing_strategy(WeekendPricing())
    booking2 = system.lock_seats("USR002", "SHW001", ["B1", "B2"])
    if booking2:
        print(f"  Weekend price for B1,B2: ${booking2.total_amount:.2f}")
        system.cancel_booking(booking2.booking_id)

    # --- Demo 5: Holiday pricing ---
    print("\n[Demo 5] Dynamic pricing (Holiday):")
    system.set_pricing_strategy(HolidayPricing())
    booking3 = system.lock_seats("USR002", "SHW001", ["C1"])
    if booking3:
        print(f"  Holiday price for C1: ${booking3.total_amount:.2f}")
        system.cancel_booking(booking3.booking_id)

    avail = len(hall.get_available_seats())
    print(f"\nDemo complete! Available seats remaining: {avail}")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **lock_seats** | RLock on data (check + lock all-or-nothing) | Only 1 user can hold any seat at a time |
| **confirm_booking** | RLock on data | Atomic: check LOCKED state, process payment, transition |
| **cancel_booking** | RLock on data | No double-cancel; seats safely released |
| **expire_stale_locks** | RLock on data | Safe scan; no race with lock_seats |
| **notify_observers** | Copy observers under lock, notify outside | No deadlock from observer calling back into system |

**Concurrency Principles**:
1. ✅ `threading.RLock()` used throughout — prevents deadlock on re-entrant calls
2. ✅ All-or-nothing seat locking — checks all seats before locking any
3. ✅ Observers notified outside lock — prevents observer → system re-entry deadlock
4. ✅ Double-checked locking for Singleton initialization
5. ✅ Lazy auto-expiry in `is_available()` + eager `expire_stale_locks()` background job

---

## Demo Scenarios

### Demo 1: Setup - Create Entities

```python
def demo_1_setup():
    system = BookingSystem.get_instance()
    system.observers.clear()
    system.add_observer(ConsoleObserver())

    # Create movies
    movie1 = Movie("MOV001", "Inception", 148,
                   ["Sci-Fi", "Thriller"], "English", "PG-13")
    movie2 = Movie("MOV002", "The Dark Knight", 152,
                   ["Action", "Crime"], "English", "PG-13")
    system.add_movie(movie1)
    system.add_movie(movie2)

    # Create theater with hall
    theater = Theater("THR001", "PVR Cinemas", "Downtown", "NYC")
    hall = Hall("HALL001", "Hall 1", 60)
    hall.generate_seat_layout(6, 10)  # 6 rows x 10 seats
    theater.add_hall(hall)
    system.add_theater(theater)

    # Create shows
    show1 = Show("SHW001", movie1, hall,
                datetime.now() + timedelta(hours=2), 15.0)
    system.add_show(show1)

    # Register users
    user1 = User("USR001", "Alice", "alice@example.com", "+1234567890")
    user2 = User("USR002", "Bob", "bob@example.com", "+0987654321")
    system.register_user(user1)
    system.register_user(user2)

    print("Setup complete: 2 movies, 1 theater, 1 show, 2 users")
```

### Demo 2: Search & Browse

```
Search: Inception
Found: 1 movie (148 min, PG-13)

Shows for Inception:
  Show SHW001 at 02:00 PM - 60 seats available
```

### Demo 3: Seat Selection & Locking

```
Alice selects seats A1, A2 (VIP) → Total: $45.00
  Lock acquired until 02:15 PM

Bob tries seats A1, A2 (same seats)
  Seats unavailable (locked by Alice)

Bob selects seats C5, C6 (Premium) → Total: $39.00
  Lock acquired until 02:15 PM
```

### Demo 4: Dynamic Pricing

```
Regular pricing (weekday): A1=$15, A2=$15 = $30
Switch to Weekend pricing (+50%): A1=$22.50, A2=$22.50 = $45
Switch to Holiday pricing (+100%): A1=$30, A2=$30 = $60
```

### Demo 5: Full Booking Flow

```
Alice browses → Finds Inception
Alice selects A1, A2 (locks)
Alice processes payment (Credit Card)
Alice confirms booking
Booking BK001 confirmed
Email: Booking confirmation sent to alice@example.com
SMS: Booking confirmed sent to +1234567890
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking of the same seat?**

A: Three layers:

1. **Seat Status Enum**: AVAILABLE → LOCKED → BOOKED (explicit state management)
2. **Timestamp-based Locking**: Each seat has `locked_until` field. When locking, set `locked_until = now + 10 min`
3. **Before any operation**, check: if seat.status == LOCKED and now > locked_until, auto-expire by calling unlock()

```python
def is_available(self):
    if self.status == SeatStatus.AVAILABLE:
        return True
    if self.status == SeatStatus.LOCKED and datetime.now() > self.locked_until:
        self.unlock()  # Auto-expire
        return True
    return False
```

**Q2: What's difference between LOCKED and CONFIRMED booking?**

A:
- **LOCKED**: Seats reserved temporarily (10 min). User is in checkout. Can be released if user abandons or payment fails.
- **CONFIRMED**: Booking finalized after successful payment. Seats marked BOOKED permanently (until cancellation).

Timeline: Browse → Lock seats (10 min window) → If no payment, auto-unlock → OR → Payment succeeds → Confirm (permanent)

**Q3: Why use Strategy pattern for pricing?**

A: Pricing varies by day/time/demand:
- Regular weekday: Base price
- Weekend: Base × 1.5 (50% markup)
- Holiday: Base × 2.0 (100% markup)
- Future: Surge, seasonal, member discounts

Strategy lets us swap algorithms without modifying booking logic:
```python
system.set_pricing_strategy(WeekendPricing())  # Change at runtime
total = system.calculate_price(booking)  # Uses WeekendPricing
```

**Q4: How do you handle seat lock expiry?**

A: Two approaches:

1. **Lazy expiry**: When querying availability, check `if now > locked_until` and unlock if expired
2. **Eager cleanup**: Background job runs every minute, scans all LOCKED seats, releases expired ones

For this system, use lazy + periodic cleanup every 5 minutes for consistency.

---

### Intermediate Questions

**Q5: How would you scale this to 100 theaters, 10K bookings/day?**

A: Multi-tier architecture:

```
Layer 1: API Servers (5-10 load-balanced instances)
  └─ BookingSystem replicas per region

Layer 2: Caching (Redis)
  └─ Popular movies cache (5-min TTL)
  └─ Show times cache (10-min TTL)
  └─ Distributed seat locks (with TTL auto-expire)

Layer 3: Database (Sharded by theater_id)
  ├─ Theater 1-10: Shard 1
  ├─ Theater 11-20: Shard 2
  ├─ Theater 21-30: Shard 3
  └─ Theater 31+: Shard 4
  └─ Each shard has read replicas

Layer 4: Notifications (Async Queue)
  └─ Kafka topic for booking events
  └─ Email worker consumes → SendGrid
  └─ SMS worker consumes → Twilio
  └─ Non-blocking from checkout
```

**Q6: How to handle payment failures gracefully?**

A:

```
Booking locked (seats reserved)
    ↓
Call payment_gateway.charge(card)
    ↓
If fails → Retry with exponential backoff (3x)
    ↓
If all fail → Release seats, mark booking FAILED
         → Send email: "Payment declined, try again"
         → Log for manual review
```

**Q7: How to handle race condition: 2 users locking same seat simultaneously?**

A: Use atomic operation:

```python
def lock_seats(user_id, show_id, seat_ids):
    # Atomic block
    with lock.acquire(timeout=5):
        for seat_id in seat_ids:
            seat = show.hall.get_seat(seat_id)
            if not seat.is_available():
                # Rollback: release all previously locked
                for s in seats_locked:
                    s.unlock()
                raise SeatNotAvailableError
            seat.lock(user_id)
```

First user to acquire lock wins. Second user sees seat already LOCKED, gets error.

**Q8: Why not persist locks to database?**

A: Performance:

- **In-memory locks**: O(1) lookup, microseconds
- **DB locks**: Network latency (5-20ms), DB query overhead

For 1,000 concurrent users with 10-min locks, in-memory + periodic flush to DB is better.

---

### Advanced Questions

**Q9: How do you prevent bots from hoarding tickets?**

A: Multi-layer:

1. **Rate limiting**: Max 3 seat locks per minute per user
2. **CAPTCHA**: On booking page before payment
3. **Require payment method**: Force valid card before locking
4. **Monitor patterns**: Flag users with 5+ consecutive cancelled bookings
5. **Blacklist**: Temporarily ban IP after 10 failed attempts
6. **User reputation**: Penalize abandoned carts (lower priority in queue next time)

**Q10: How to implement flexible cancellation policies?**

A:

```python
class CancellationPolicy:
    FULL_REFUND = 0        # Cancel anytime
    50_PERCENT = 1         # 50% refund if < 6h before show
    25_PERCENT = 2         # 25% refund if < 2h before show
    NON_REFUNDABLE = 3     # No refund if < 30min before show

def cancel_booking(booking_id):
    booking = bookings[booking_id]
    time_remaining = booking.show.start_time - datetime.now()

    if time_remaining > 6h:
        refund_percent = 1.0  # 100%
    elif time_remaining > 2h:
        refund_percent = 0.5  # 50%
    elif time_remaining > 30min:
        refund_percent = 0.25  # 25%
    else:
        refund_percent = 0.0   # 0%

    refund_amount = booking.total_amount * refund_percent
    payment_service.refund(booking.payment_id, refund_amount)
    booking.status = BookingStatus.CANCELLED
```

---

## Scaling Q&A

### Q1: How to scale to 1M concurrent users with 100K bookings/day?

**Problem**: Single BookingSystem instance can't handle 1M users, single database bottlenecks.

**Solution**: Distributed architecture:

```
Tier 1: API Gateway (Nginx)
  └─ Route requests by user_id hash (consistent hashing)

Tier 2: BookingSystem Replicas (250K users each)
  ├─ Instance 1 (users 0-250K)
  ├─ Instance 2 (users 250K-500K)
  ├─ Instance 3 (users 500K-750K)
  └─ Instance 4 (users 750K-1M)
  └─ Session affinity (same user → same instance)

Tier 3: Distributed Locks (Redis Cluster)
  ├─ Shard 1: Theater 1-25
  ├─ Shard 2: Theater 26-50
  ├─ Shard 3: Theater 51-75
  └─ Shard 4: Theater 76-100
  └─ Key: "lock:theater_id:show_id:seat_id" with TTL 15min

Tier 4: Database (Postgres with Replication)
  ├─ Shard by theater_id (horizontal scaling)
  ├─ 4 shards handling 25 theaters each
  ├─ Each shard: 1 primary + 2 read replicas
  └─ Cross-region replication for disaster recovery

Tier 5: Notifications (Kafka + Workers)
  ├─ Topic: booking_events (1M+ messages/day)
  ├─ Email partition: 100 msgs/sec
  ├─ SMS partition: 50 msgs/sec
  └─ Worker autoscale based on lag
```

**Metrics**:
- Lock lookup: 5ms (Redis)
- Seat availability check: 50ms (distributed)
- Booking confirmation: 200ms (distributed lock + DB write)
- Concurrent throughput: 5,000 TPS

---

### Q2: How to prevent overselling with 10K concurrent lock requests?

**Problem**: Two users lock same last seat, both think it's reserved.

**Solution**: Pessimistic locking with Redis:

```python
def lock_seats_distributed(user_id, theater_id, show_id, seat_ids):
    redis_client = get_redis_shard(theater_id)

    # Acquire lock for each seat atomically
    pipeline = redis_client.pipeline()
    lock_acquired = True

    for seat_id in seat_ids:
        key = f"lock:{show_id}:{seat_id}"
        # SET if not exists, with 15-min TTL
        result = pipeline.set(key, user_id, nx=True, ex=900)

    responses = pipeline.execute()

    if not all(responses):
        # Rollback: release all locks
        for seat_id in seat_ids:
            redis_client.delete(f"lock:{show_id}:{seat_id}")
        raise SeatNotAvailableError()

    # All locks acquired successfully
    return create_booking(user_id, show_id, seat_ids)
```

**Guarantees**: Only one user per seat. TTL prevents deadlocks. Atomic pipeline ensures all-or-nothing.

---

### Q3: How to cache popular movies without stale data?

**Solution**: Cache-aside with invalidation:

```python
def search_movies(query, genre):
    cache_key = f"movies:{query}:{genre}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from DB
    results = db.query_movies(query, genre)

    # Cache with 5-minute TTL
    redis_client.setex(cache_key, 300, json.dumps(results))

    return results

# Invalidate on new movie added
def add_movie(movie):
    db.insert(movie)
    redis_client.delete("movies:*")  # Flush related cache
```

---

### Q4: How to handle show scheduling conflicts?

**Problem**: Two managers book same hall at overlapping times.

**Solution**: Check occupancy before creating show:

```python
def create_show(movie, hall, start_time):
    duration_ms = movie.duration * 60 * 1000
    buffer_ms = 30 * 60 * 1000  # 30-min cleanup buffer

    proposed_end = start_time + duration_ms + buffer_ms

    # Query: find all shows in hall between start_time and proposed_end
    conflicts = db.query_shows(
        hall_id=hall.id,
        start_time__lt=proposed_end,
        end_time__gt=start_time
    )

    if conflicts:
        raise SchedulingConflictError(f"Conflicts: {conflicts}")

    show = Show(movie, hall, start_time)
    db.insert(show)
    return show
```

---

### Q5: How to implement real-time availability updates?

**Solution**: WebSocket + Redis Pub/Sub:

```python
# When seat status changes
def lock_seats(user_id, show_id, seat_ids):
    # ... locking logic ...

    # Publish event to subscribers watching this show
    redis_client.publish(
        f"show:{show_id}:updates",
        json.dumps({
            "event": "seats_locked",
            "seats": seat_ids,
            "user_id": user_id
        })
    )

# Client side (WebSocket)
def on_availability_change(event):
    if event['event'] == 'seats_locked':
        for seat_id in event['seats']:
            mark_seat_locked(seat_id)  # UI update
```

**Benefits**: Sub-second updates to all connected clients watching show.

---

### Q6: How to scale notifications to 1M/day?

**Solution**: Kafka + worker pool + batch processing:

```
BookingService (publish event)
    ↓
Kafka Topic: booking_events (partitioned by theater_id)
    ├─ Partition 0: Theater 1-25 events
    ├─ Partition 1: Theater 26-50 events
    ├─ Partition 2: Theater 51-75 events
    └─ Partition 3: Theater 76-100 events
    ↓
EmailWorker (consume partition 0-3)
    ├─ Batch 100 events
    ├─ Deduplicate users
    ├─ Send via SendGrid (100 msgs/sec)
    ↓
SMSWorker (consume partition 0-3)
    ├─ Batch 50 events
    ├─ Send via Twilio (50 msgs/sec)
    ↓
Monitoring: Lag < 10 sec, Success rate > 99.9%
```

**Throughput**: 1M events/day = ~12 events/sec, easily handled.

---

### Q7: How to handle database replication lag?

**Problem**: User confirms booking on primary, reads from replica which doesn't have update yet → sees booking not confirmed.

**Solution**: Read consistency patterns:

1. **Write-after-write**: After writing to primary, read from primary for next 5 seconds
2. **Eventual consistency**: Accept 1-2 second lag for non-critical reads (movie list)
3. **Read-your-writes**: Store write timestamp in session, check replica lag

```python
def confirm_booking(booking_id):
    # Write to primary
    db_primary.update(booking_id, status=CONFIRMED)

    # Store write timestamp
    session['last_write'] = datetime.now()

    # Subsequent reads check lag
    def read_booking(booking_id):
        time_since_write = datetime.now() - session.get('last_write', datetime.now())

        if time_since_write < 5 sec:
            # Use primary (strong consistency)
            return db_primary.get(booking_id)
        else:
            # Use replica (eventual consistency acceptable)
            return db_replica.get(booking_id)
```

---

### Q8: How to monitor system health?

**Key Metrics**:

| Metric | Alert Threshold |
|--------|-----------------|
| API latency (p99) | > 1000ms |
| Seat lock success rate | < 99% |
| Payment success rate | < 95% |
| Booking confirmation rate | < 98% |
| Cache hit ratio | < 80% |
| Redis connection pool | > 90% utilized |
| Database query latency (p99) | > 200ms |
| Kafka consumer lag | > 1 minute |
| Notification delivery time | > 5 min |
| Uptime | < 99.9% |

```python
# Monitoring with Prometheus
booking_lock_attempts = Counter(
    'booking_seat_locks_total', 'Total seat lock attempts'
)
booking_lock_failures = Counter(
    'booking_seat_lock_failures_total', 'Failed seat locks'
)

try:
    lock_seats(user_id, show_id, seat_ids)
    booking_lock_attempts.inc()
except SeatNotAvailableError:
    booking_lock_failures.inc()
```

---

### Q9: How to handle user requests during traffic spike?

**Solution**: Circuit breaker + graceful degradation:

```python
def checkout_booking(booking_id):
    # Check circuit breaker
    if payment_service.is_open():
        # Don't call payment service, fail fast
        raise ServiceUnavailableError("Payment service temporarily unavailable")

    try:
        payment_service.charge(booking.amount)
        circuit_breaker.record_success()
        return confirm_booking(booking_id)
    except PaymentServiceError:
        circuit_breaker.record_failure()
        if circuit_breaker.failure_count > 5:
            circuit_breaker.open()  # Stop trying for 30 sec
        raise
```

Alternative: Queue requests:
```python
if queue.length() > 10000:
    # Too many pending → tell user to try again in 30 sec
    raise TooManyRequestsError("System busy")

queue.enqueue_booking(user_id, show_id, seat_ids)
return {"status": "queued", "position": queue.length()}
```

---

### Q10: How to implement disaster recovery?

**Solution**: Multi-region replication:

```
Primary Region (US-East)
  ├─ BookingSystem Replicas (active)
  ├─ Primary Database
  └─ Redis Cluster

Secondary Region (US-West) - Standby
  ├─ BookingSystem Replicas (warm standby)
  ├─ Read-only database replica (from primary)
  └─ Redis Cluster (replicated)

Failover mechanism:
  - Monitor primary health (heartbeat every 10 sec)
  - If primary down for 30 sec:
    - Promote secondary to primary
    - Redirect traffic to US-West
    - Alert on-call engineer
  - RTO: 30 seconds
  - RPO: < 1 minute (database replication lag)
```

**Testing**: Monthly failover drills to ensure readiness.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram from memory with all 9 entities
- [ ] Walk through booking flow end-to-end (browse → lock → pay → confirm)
- [ ] Explain 5 design patterns in < 1 minute each
- [ ] Discuss seat locking (10-min timeout, lazy + eager auto-expiry)
- [ ] Explain how to prevent double-booking (atomic lock, RLock thread safety)
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs (in-memory vs DB locks, pessimistic vs optimistic locking)
- [ ] Mention monitoring (alert thresholds, metrics, health checks)

> **Interview Tips**  
> ✅ **Start with questions**: Clarify single/multi-theater, seat types, scale  
> ✅ **Sketch first**: Draw 2D seat grid, entity relationships  
> ✅ **Explain patterns**: Singleton ensures consistency, Strategy enables pricing flexibility  
> ✅ **Handle edge cases**: Lock expiry, concurrent bookings, payment failure  
> ✅ **Demo incrementally**: Browse → Lock → Pay → Confirm  
> ✅ **Discuss trade-offs**: In-memory vs DB locks, pessimistic vs optimistic locking  
> ✅ **Mention monitoring**: Alert thresholds, metrics, health checks

---

**Ready for interview? Let's go! Book some tickets!**
