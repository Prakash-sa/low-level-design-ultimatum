# Movie Ticket Booking System — Complete Design Guide

> Multi-theater booking platform for browsing, seat selection, dynamic pricing, and reservation management.

**Scale**: 1,000+ concurrent users, 100+ theaters, 10K+ bookings/day, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Seat locking, dynamic pricing, booking lifecycle, state management

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [System Overview](#system-overview)
3. [Requirements & Scope](#requirements--scope)
4. [Architecture Diagram](#architecture-diagram)
5. [Interview Q&A](#interview-qa)
6. [Scaling Q&A](#scaling-qa)
7. [Demo Scenarios](#demo-scenarios)
8. [Complete Implementation](#complete-implementation)
9. [Design Patterns Summary](#design-patterns-summary)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Customers browse movies → select shows → lock seats (temporary 10-min reservation) → pay → confirm booking → receive confirmation. Prevent double-booking through atomic seat locking and status transitions.

### Key Design Patterns
| Pattern | Why | Used For |
|---------|-----|----------|
| **Singleton** | Single consistent state | BookingSystem (thread-safe) |
| **Strategy (Pricing)** | Pluggable algorithms | Regular/Weekend/Holiday pricing |
| **Observer** | Decouple notifications | Email/SMS/Push notifiers on events |
| **State** | Valid transitions | BookingStatus & SeatStatus enums |
| **Factory** | Centralized creation | Seat layout generation |

### Critical Interview Points
- ✅ How to prevent double-booking? → Atomic seat locking with timestamp-based expiry
- ✅ Seat lock vs booking status? → Lock = temporary (10 min); Confirmed = final
- ✅ Thread-safety? → Singleton with threading.Lock, seat.lock() atomic operation
- ✅ Pricing flexibility? → Strategy pattern swaps algorithms (Regular/Weekend/Holiday) without code change

---

## System Overview

### Core Problem
```
Customer browsing
        ↓
SEARCH MOVIES & SHOWS (find showtimes, available seats)
        ↓
SELECT SEATS (choose specific seats on 2D layout)
        ↓
LOCK SEATS (temporary 10-minute reservation with status check)
        ↓
PAYMENT (process transaction, calculate price via strategy)
        ↓
CONFIRM BOOKING (atomic: mark seats BOOKED, update order status, send notifications)
        ↓
If anything fails: RELEASE LOCKS, cart unchanged
```

### Key Constraints
- **Concurrency**: 1,000+ users simultaneously selecting/locking seats
- **Consistency**: No double-selling (atomic locking with TTL)
- **Availability**: Seat status must be real-time updated
- **Pricing**: Different prices for Regular/Premium/VIP seats + timing-based surcharges
- **Notifications**: Async Email/SMS without blocking booking

---

## Requirements & Scope

### Functional Requirements
✅ Movie listings and search (by title, genre, language)  
✅ Theater and hall management  
✅ Show scheduling with start times  
✅ Seat layout (2D grid: rows A-F, seats 1-10, types: Regular/Premium/VIP)  
✅ Temporary seat locking (10 minutes auto-expiry)  
✅ Dynamic pricing (Regular vs Weekend +50% vs Holiday +100%)  
✅ Payment processing and booking confirmation  
✅ Event notifications (Email, SMS)  
✅ Booking cancellation with refunds  

### Non-Functional Requirements
✅ Support 1,000+ concurrent users  
✅ <100ms movie search response  
✅ <500ms seat lock response  
✅ 99.9% uptime  
✅ Accurate seat inventory (no overselling)  
✅ Lock auto-expiry within ±1 min  

### Out of Scope
❌ Real payment gateway integration  
❌ Loyalty programs or rewards  
❌ Food/beverage ordering  
❌ Refund processing (auto-grant assumed)  
❌ Video streaming  

---

## Architecture Diagram

### UML Class Diagram

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
   ├─→ EmailNotifier (📧)
   ├─→ SMSNotifier (📱)
   └─→ ConsoleObserver (logs)

ENUMS:
BookingStatus: PENDING → LOCKED → CONFIRMED → CANCELLED/COMPLETED
SeatStatus: AVAILABLE → LOCKED → BOOKED
SeatType: REGULAR (1.0×) | PREMIUM (1.3×) | VIP (1.5×)
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
    hall.generate_seat_layout(6, 10)  # 6 rows × 10 seats
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
    
    print("✅ Setup complete: 2 movies, 1 theater, 1 show, 2 users")
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
  ❌ Seats unavailable (locked by Alice)

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
✅ Booking BK001 confirmed
📧 Email: Booking confirmation sent to alice@example.com
📱 SMS: Booking confirmed sent to +1234567890
```

---

## Complete Implementation

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
        if self.status == SeatStatus.LOCKED and datetime.now() > self.locked_until:
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
                seat_type = SeatType.VIP if idx < 2 else (SeatType.PREMIUM if idx < 4 else SeatType.REGULAR)
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
    def __init__(self, show_id: str, movie: Movie, hall: Hall, start_time: datetime, base_price: float):
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
            print(f"📧 Email: {booking.user.email} - Booking confirmed!")

class SMSNotifier(BookingObserver):
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"📱 SMS: {booking.user.phone} - Booking confirmed!")

class ConsoleObserver(BookingObserver):
    def update(self, event: str, booking: Booking):
        seats = ", ".join([s.seat_id for s in booking.seats])
        print(f"[{event.upper()}] {booking.user.name} | Seats: {seats} | ${booking.total_amount:.2f}")

# ============ SINGLETON CONTROLLER ============

class BookingSystem:
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
        return BookingSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: BookingObserver):
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        for obs in self.observers:
            obs.update(event, booking)
    
    def add_movie(self, movie: Movie):
        self.movies[movie.movie_id] = movie
    
    def add_theater(self, theater: Theater):
        self.theaters[theater.theater_id] = theater
    
    def add_show(self, show: Show):
        self.shows[show.show_id] = show
    
    def register_user(self, user: User):
        self.users[user.user_id] = user
    
    def search_movies(self, query: str = "", genre: str = "") -> List[Movie]:
        results = list(self.movies.values())
        if query:
            results = [m for m in results if query.lower() in m.title.lower()]
        if genre:
            results = [m for m in results if genre in m.genre]
        return results
    
    def lock_seats(self, user_id: str, show_id: str, seat_ids: List[str]) -> Optional[Booking]:
        show = self.shows.get(show_id)
        user = self.users.get(user_id)
        if not show or not user:
            return None
        
        seats = []
        for sid in seat_ids:
            seat = show.hall.get_seat(sid)
            if not seat or not seat.is_available():
                return None
            seats.append(seat)
        
        for seat in seats:
            seat.lock(user_id)
        
        booking_id = f"BK{len(self.bookings)+1:04d}"
        booking = Booking(booking_id, user, show, seats)
        booking.status = BookingStatus.LOCKED
        booking.total_amount = booking.calculate_total(self.pricing_strategy)
        self.bookings[booking_id] = booking
        self.notify_observers("seats_locked", booking)
        return booking
    
    def confirm_booking(self, booking_id: str, method: PaymentMethod) -> bool:
        booking = self.bookings.get(booking_id)
        if not booking or booking.status != BookingStatus.LOCKED:
            return False
        
        payment = Payment(f"PAY{len(self.bookings)}", booking.total_amount, method)
        if payment.process():
            booking.payment = payment
            booking.confirm()
            self.notify_observers("booking_confirmed", booking)
            return True
        return False

# ============ DEMO ============

if __name__ == "__main__":
    print("="*70)
    print("MOVIE TICKET BOOKING SYSTEM")
    print("="*70)
    
    system = BookingSystem.get_instance()
    system.add_observer(ConsoleObserver())
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    # Setup
    movie = Movie("MOV001", "Inception", 148, ["Sci-Fi"], "English", "PG-13")
    system.add_movie(movie)
    
    theater = Theater("THR001", "PVR", "Downtown", "NYC")
    hall = Hall("HALL001", "Hall 1", 60)
    hall.generate_seat_layout(6, 10)
    theater.add_hall(hall)
    system.add_theater(theater)
    
    show = Show("SHW001", movie, hall, datetime.now() + timedelta(hours=2), 15.0)
    system.add_show(show)
    
    user1 = User("USR001", "Alice", "alice@example.com", "+1234567890")
    system.register_user(user1)
    
    # Demo
    print("\n[Demo] Booking flow:")
    booking = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking:
        print(f"Locked seats - Total: ${booking.total_amount:.2f}")
        system.confirm_booking(booking.booking_id, PaymentMethod.CREDIT_CARD)
    
    print("\n✅ Demo complete!")
```

---

## Design Patterns Summary

| Pattern | Purpose | Benefit |
|---------|---------|---------|
| **Singleton** | BookingSystem controller | Single state, thread-safe, global access |
| **Strategy (Pricing)** | Regular/Weekend/Holiday | Pluggable algorithms, extensible |
| **Observer** | Email/SMS/Push notifications | Loose coupling, event-driven |
| **State** | BookingStatus, SeatStatus | Explicit lifecycle, invalid states prevented |
| **Factory** | Seat layout generation | Centralized creation logic |

---

## Interview Tips

✅ **Start with questions**: Clarify single/multi-theater, seat types, scale  
✅ **Sketch first**: Draw 2D seat grid, entity relationships  
✅ **Explain patterns**: Singleton ensures consistency, Strategy enables pricing flexibility  
✅ **Handle edge cases**: Lock expiry, concurrent bookings, payment failure  
✅ **Demo incrementally**: Browse → Lock → Pay → Confirm  
✅ **Discuss trade-offs**: In-memory vs DB locks, pessimistic vs optimistic locking  
✅ **Mention monitoring**: Alert thresholds, metrics, health checks  

---

## Success Checklist

- [ ] Explain 5 design patterns in < 1 minute each
- [ ] Draw UML class diagram from memory
- [ ] Walk through booking flow end-to-end
- [ ] Discuss seat locking (10-min timeout, auto-expiry)
- [ ] Explain how to prevent double-booking
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs (locking strategy, caching, notifications)

---

**Ready for interview? Let's go! 🎬**
