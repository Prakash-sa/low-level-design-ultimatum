# Airline Management System — Complete Design Guide

> Flight scheduling, seat inventory management, booking lifecycle, overbooking prevention, and dynamic pricing.

**Scale**: 500-1,000+ concurrent users, 1M+ flights/day, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Seat hold/confirm lifecycle, overbooking prevention, dynamic pricing, event notifications

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
Customers search flights → hold seat (temporary 5-min reservation) → pay → confirm booking → or hold expires → seat released. Prevent overbooking through atomic seat status transitions and hold timeout management.

### Key Design Patterns
| Pattern | Why | Used For |
|---------|-----|----------|
| **Singleton** | Single consistent state | AirlineSystem (thread-safe) |
| **Strategy (Pricing)** | Pluggable algorithms | Fixed price vs Demand-based pricing |
| **Observer** | Decouple notifications | Email/SMS/Console on hold/confirm events |
| **State** | Valid transitions | BookingStatus & SeatStatus enums |
| **Factory** | Centralized creation | Seat/Flight/Booking creation |

### Critical Interview Points
- ✅ How to prevent overbooking? → Status transition (AVAILABLE → HOLD → BOOKED) with TTL expiry
- ✅ Hold vs Confirmed? → Hold = temporary (5 min); Confirmed = permanent after payment
- ✅ Handle hold expiry? → Background job checks hold_until timestamp, expires stale holds
- ✅ Concurrency? → Singleton + threading.Lock for atomic operations

---

## System Overview

### Core Problem
```
Customer searches flights
        ↓
SELECT FLIGHT & SEAT (browse available seats)
        ↓
HOLD SEAT (temporary 5-minute reservation, seat status = HOLD)
        ↓
PAYMENT (validate pricing via strategy)
        ↓
CONFIRM (if hold still valid: seat status = BOOKED, booking = CONFIRMED)
        ↓
or HOLD EXPIRES (if > 5 min: release seat, booking = EXPIRED)
        ↓
Result: Either CONFIRMED with booked seat OR EXPIRED with available seat
```

### Key Constraints
- **Concurrency**: 500-1000+ users simultaneously holding/confirming seats
- **Consistency**: No overbooking (seat can only be held/booked by one user)
- **Availability**: Real-time seat status updates, fast searches
- **Pricing**: Different prices for Economy/Business + demand-based surcharges
- **Notifications**: Async updates on hold/confirm/expire/cancel events

---

## Requirements & Scope

### Functional Requirements
✅ Browse flights (search by route, date, aircraft)  
✅ View seat inventory with real-time availability  
✅ Hold seat temporarily (5-minute timeout)  
✅ Confirm booking after payment  
✅ Cancel booking (release seat back to available)  
✅ Automatic hold expiry and seat release  
✅ Dynamic pricing (fixed vs demand-based)  
✅ Event notifications (held, confirmed, expired, cancelled)  
✅ Overbooking prevention (atomic seat operations)  

### Non-Functional Requirements
✅ Support 500-1000+ concurrent users  
✅ <100ms flight search response  
✅ <200ms hold/confirm response  
✅ 99.9% uptime  
✅ No overbooking (0% violation)  
✅ Hold expiry within ±30 seconds  

### Out of Scope
❌ Passenger check-in or boarding  
❌ Real payment gateway  
❌ Loyalty programs  
❌ Baggage management  
❌ Flight cancellation (only booking cancellation)  
❌ Multi-airline federation  

---

## Architecture Diagram

### UML Class Diagram

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
├──────────────────────────────────────┤
│ + get_instance(): AirlineSystem      │
│ + hold_seat(...): Booking            │
│ + confirm_booking(booking_id): bool  │
│ + cancel_booking(booking_id): bool   │
│ + check_and_expire_holds(): void     │
│ + set_pricing_strategy(strategy)     │
│ + notify_observers(event, booking)   │
└──────────────────────────────────────┘
           │ manages
           ▼
    ┌─────────────────────┐
    │      Flight         │
    ├─────────────────────┤
    │ - flight_id: str    │
    │ - origin: str       │
    │ - destination: str  │
    │ - departure: dt     │
    │ - aircraft_type: str│
    │ - seats: Dict       │
    ├─────────────────────┤
    │ + add_seat(seat)    │
    │ + get_seat(id)      │
    │ + available_count() │
    └─────────────────────┘
           │ contains
           ▼
    ┌─────────────────────────────────┐
    │         Seat                    │
    ├─────────────────────────────────┤
    │ - seat_id: str (e.g., "1A")     │
    │ - seat_class: SeatClass         │
    │ - status: SeatStatus            │
    │ - booked_by: Optional[str]      │
    ├─────────────────────────────────┤
    │ + is_available(): bool          │
    │ + hold(): void                  │
    │ + book(): void                  │
    │ + release(): void               │
    └─────────────────────────────────┘
           │ linked in
           ▼
    ┌──────────────────────────────────┐
    │        Booking                   │
    ├──────────────────────────────────┤
    │ - booking_id: str                │
    │ - passenger: Passenger           │
    │ - flight: Flight                 │
    │ - seat: Seat                     │
    │ - price: float                   │
    │ - status: BookingStatus          │
    │ - hold_until: datetime           │
    ├──────────────────────────────────┤
    │ + confirm(): void                │
    │ + cancel(): void                 │
    │ + expire(): void                 │
    └──────────────────────────────────┘
           │ references
           ▼
    ┌──────────────────────┐
    │     Passenger        │
    ├──────────────────────┤
    │ - passenger_id: str  │
    │ - name: str          │
    │ - email: str         │
    └──────────────────────┘

STRATEGY PATTERN (Pricing):
┌────────────────────────────────┐
│ PricingStrategy (Abstract)     │
│ + calculate_price(flight, seat)│
└──┬─────────────────────────────┘
   │
   ├─→ FixedPricing (Economy $100, Business $200)
   └─→ DemandBasedPricing (1.0x - 1.5x multiplier)

OBSERVER PATTERN (Notifications):
┌────────────────────────────────┐
│ Observer (Abstract)            │
│ + update(event, booking)       │
└──┬─────────────────────────────┘
   │
   ├─→ ConsoleObserver (logging)
   ├─→ EmailNotifier
   └─→ SMSNotifier

ENUMS:
SeatStatus: AVAILABLE → HOLD → BOOKED
BookingStatus: HOLD → CONFIRMED | EXPIRED | CANCELLED
SeatClass: ECONOMY | BUSINESS
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent overbooking of a seat?**

A: Atomic status transitions with atomicity guarantee:

1. **Seat Status Enum**: AVAILABLE → HOLD → BOOKED (explicit state)
2. **Atomic Hold Operation**: Before holding, check `seat.status == AVAILABLE`. If true, immediately set to HOLD in one transaction.
3. **Database Uniqueness**: In real systems, enforce `(flight_id, seat_id)` unique constraint with no duplicates
4. **Optimistic Locking**: Each seat has version number; on hold, increment version; if version mismatch, retry

```python
def hold_seat(user_id, flight_id, seat_id):
    seat = flight.get_seat(seat_id)
    
    if seat.status != SeatStatus.AVAILABLE:
        raise AlreadyHeldError()  # Another user holding/booked
    
    # Atomic: status AVAILABLE → HOLD
    seat.status = SeatStatus.HOLD
    seat.booked_by = user_id
    
    # Create booking with 5-min hold window
    booking = Booking(..., hold_until=now + 300s)
    return booking
```

**Q2: What's the difference between HOLD and CONFIRMED?**

A:
- **HOLD**: Temporary 5-minute reservation while user is in checkout. Seat status = HOLD. If payment not completed by 5 min, booking EXPIRED and seat released.
- **CONFIRMED**: Permanent booking after successful payment. Seat status = BOOKED. Booking status = CONFIRMED.

Timeline: Browse → Hold (5-min window) → If payment succeeds → Confirm (permanent) → Or timeout → Expire (seat releases)

**Q3: How do you handle hold expiry?**

A: Two approaches:

1. **Lazy Expiry**: When user tries to confirm, check `if now > booking.hold_until` and expire if stale
2. **Eager Cleanup**: Background job runs every minute, scans HOLD bookings, expires stale ones, releases seats

```python
def check_and_expire_holds(self):
    now = datetime.now()
    for booking in self.bookings.values():
        if booking.status == BookingStatus.HOLD and now > booking.hold_until:
            booking.expire()  # seat.status = AVAILABLE, booking.status = EXPIRED
            self.notify_observers("expired", booking)
```

**Q4: Why use Strategy pattern for pricing?**

A: Pricing varies by seat class + demand:
- Fixed: Economy $100, Business $200 (predictable, simple)
- Demand-based: Base × (1.0 to 1.5) based on occupancy rate (dynamic surcharges)
- Future: Seasonal, early-bird discount, fuel surcharge

Strategy lets us swap algorithms without modifying booking logic:
```python
system.set_pricing_strategy(DemandBasedPricing())
price = strategy.calculate_price(flight, seat)  # Uses new strategy
```

---

### Intermediate Questions

**Q5: How would you scale this to 1M concurrent users and 1M flights/day?**

A: Multi-tier distributed architecture:

```
Layer 1: API Gateway (Nginx)
  └─ Route by user_id hash (consistent hashing)
  
Layer 2: AirlineSystem Replicas (100K users each, 10 instances)
  ├─ Instance 1 (users 0-100K)
  ├─ Instance 2 (users 100K-200K)
  ├─ ...
  └─ Instance 10 (users 900K-1M)
  └─ Session affinity (same user → same instance)
  
Layer 3: Distributed Locks (Redis Cluster)
  └─ Key: "lock:flight_id:seat_id" with 15-min TTL
  └─ Ensures atomic status transition across replicas
  
Layer 4: Database (Sharded by flight_id)
  ├─ Shard 1: Flights 0-250K
  ├─ Shard 2: Flights 250K-500K
  ├─ Shard 3: Flights 500K-750K
  └─ Shard 4: Flights 750K-1M
  └─ Each shard: 1 primary + 2 read replicas
  
Layer 5: Notifications (Kafka + Workers)
  ├─ Topic: booking_events (1M+ messages/day)
  ├─ Email worker (100 msgs/sec)
  ├─ SMS worker (50 msgs/sec)
  └─ Worker auto-scale based on Kafka lag
  
Layer 6: Caching (Redis)
  └─ Popular routes (5-min TTL)
  └─ Flight metadata
  └─ Seat availability (updated on every hold/release)
```

**Throughput Estimate**: 
- 1M flights/day = ~12 events/sec (easily handled)
- Per-flight: average 150 bookings/day
- Peak: 5,000 holds/sec (during holiday rush)
- Each hold: 50ms (distributed lock + DB write)

---

**Q6: How do you handle payment failure gracefully?**

A:

```
User clicks "Confirm"
    ↓
Check if hold still valid: if now > hold_until → EXPIRED, seat released, error
    ↓
Call payment_gateway.charge(card)
    ↓
If success → Set booking.status = CONFIRMED, seat.status = BOOKED
    ↓
If failure → Retry 3x with exponential backoff (1s, 2s, 4s)
    ↓
On final failure → booking.status = PAYMENT_FAILED
                → Automatically expire booking
                → Release seat (seat.status = AVAILABLE)
                → Notify user: "Payment declined. Hold released. Try again."
                → Log for manual review
```

**Key**: Payment failure must trigger hold expiry, not leave seat in HOLD limbo.

---

**Q7: How to handle race condition: 2 users holding same seat simultaneously?**

A: Atomicity with locks:

```python
with distributed_lock.acquire(f"flight:{flight_id}:seat:{seat_id}", timeout=5):
    seat = flight.get_seat(seat_id)
    
    if seat.status != SeatStatus.AVAILABLE:
        raise SeatNotAvailableError()  # Already held by another user
    
    # Atomic transition
    seat.status = SeatStatus.HOLD
    seat.booked_by = user_id
    booking = Booking(...)
```

**Guarantees**: Only one user per seat at a time. Lock ensures serialization. TTL prevents deadlocks.

---

**Q8: How to implement per-seat upgrades (Economy → Business)?**

A:

```python
def upgrade_booking(booking_id: str, new_seat_id: str) -> bool:
    booking = bookings[booking_id]
    
    if booking.status != BookingStatus.CONFIRMED:
        raise ValueError("Can only upgrade confirmed bookings")
    
    old_seat = booking.seat
    new_seat = booking.flight.get_seat(new_seat_id)
    
    # Calculate upgrade charge
    upgrade_price = pricing_strategy.calculate_price(...) - booking.price
    
    if upgrade_price <= 0:
        raise ValueError("Downgrade not allowed")
    
    # Charge user for upgrade
    charge_success = payment_service.charge(booking.user, upgrade_price)
    
    if charge_success:
        old_seat.release()
        new_seat.book()
        booking.seat = new_seat
        booking.price += upgrade_price
        notify_observers("upgraded", booking)
        return True
    
    return False
```

---

**Q9: How to handle overbooking (intentionally oversell by 5%)?**

A: Controlled overbooking for no-shows:

```python
def get_available_seats(flight: Flight, show_all: bool = False) -> List[Seat]:
    booked_seats = sum(1 for s in flight.seats.values() if s.status == SeatStatus.BOOKED)
    available_seats = sum(1 for s in flight.seats.values() if s.status == SeatStatus.AVAILABLE)
    
    if show_all:
        return [s for s in flight.seats.values() if s.status in [AVAILABLE, HOLD]]
    
    # Calculate oversell threshold (5% of capacity)
    capacity = len(flight.seats)
    oversell_threshold = int(capacity * 0.05)
    max_bookable = capacity + oversell_threshold
    
    if booked_seats >= max_bookable:
        # Stop selling, but allow holds (for revenue management)
        return []
    
    return available_seats
```

**Key**: Overbooking is policy decision; track oversold passengers separately; offer compensation if needed.

---

**Q10: What metrics would you track for this system?**

A:

| Metric | Alert Threshold |
|--------|-----------------|
| Seat hold success rate | < 99% |
| Booking confirmation rate | < 98% |
| Hold expiry auto-release success | < 99% |
| Overbooking incidents | > 1 per 10K flights |
| API latency (p99) | > 500ms |
| Database query latency | > 100ms |
| Cache hit ratio | < 80% |
| Kafka consumer lag | > 5 min |
| Payment success rate | < 95% |
| Uptime | < 99.9% |

```python
# Prometheus metrics
booking_holds_total = Counter('booking_holds_total', 'Total seat holds')
booking_confirms_total = Counter('booking_confirms_total', 'Total confirmations')
booking_expires_total = Counter('booking_expires_total', 'Total expirations')
overbooking_incidents = Counter('overbooking_incidents_total', 'Overbooking count')
```

---

## Scaling Q&A

### Q1: How to scale to 10M concurrent users with 100M bookings/day?

**Problem**: Single system can't handle 100M bookings/day (1,157 bookings/sec).

**Solution**: Extreme horizontal scaling:

```
Tier 1: Global Load Balancer
  ├─ Region: US-East (40M bookings/day)
  ├─ Region: EU (35M bookings/day)
  ├─ Region: APAC (25M bookings/day)
  └─ Route by user geolocation + consistent hashing
  
Tier 2: Per-Region Cluster (1,000 API servers)
  ├─ Each handles 100K bookings/day
  └─ Session affinity (same user → same server)
  
Tier 3: Distributed Locks (Redis Cluster, 100 nodes)
  └─ Per-shard: "lock:flight_id:seat_id"
  
Tier 4: Database (Multi-shard, 1,000 shards)
  └─ Shard key: flight_id % 1000
  └─ Each shard: primary + 5 replicas
  └─ Replication lag: 100ms
  
Tier 5: Cache (Memcached Cluster, 500 nodes)
  └─ Popular routes, seat layouts, flight metadata
  └─ Invalidation on booking status change
  
Tier 6: Message Queue (Kafka, 1,000 partitions)
  └─ booking_events topic (100M+ messages/day)
  └─ Email/SMS/Analytics workers consume in parallel
```

**Throughput**: 100M / 86400s = 1,157 bookings/sec
- Per shard: 1,157 / 1000 = 1.2 bookings/sec (easily handled)

---

### Q2: How to prevent overbooking in distributed system?

**Problem**: Distributed replicas can't share seat status in real-time.

**Solution**: Pessimistic locking + version control:

```
User A at replica-1 holds seat 1A
    ↓
Acquire lock: Redis.SET("lock:FL123:1A", "USER_A", NX, EX=15s)
    ↓
Check seat version: DB.GET(flight_id, seat_id, version=5)
    ↓
Update: DB.UPDATE(...) WHERE version=5 SET version=6, status=HOLD
    ↓
On success: Release lock, return booking

User B at replica-2 tries same seat
    ↓
Acquire lock: Redis.SET("lock:FL123:1A", "USER_B", NX, EX=15s) → FAIL
    ↓
Wait & retry (exponential backoff)
    ↓
On retry: Seat version=6, status=HOLD → SeatNotAvailableError
```

**Guarantees**: 
- Lock prevents concurrent holds
- Version control detects stale reads
- No seat can be booked twice

---

### Q3: How to scale hold expiry checks?

**Problem**: 100M holds/day with 5-min timeout = 1.2M expiries to check per second at peak.

**Solution**: Decentralized expiry with delay queues:

```
When hold created: Put (booking_id, expire_time) into Redis
    ↓
Delay Queue (Kafka Topic with 5-min retention)
    ├─ Partition 0: Expiries for 00:00-00:05
    ├─ Partition 1: Expiries for 00:05-00:10
    ├─ Partition 2: Expiries for 00:10-00:15
    └─ ...
    
Expiry Worker (100 instances)
    ├─ Consume from 1 partition each
    ├─ Check: if now > expire_time → expire booking
    ├─ Release seat
    └─ Notify observers (async via Kafka)
    
Throughput: 1.2M / 100 = 12K expiries per worker per second (easily handled)
```

**Advantages**: No background job scanning all bookings. Distributed. Scalable.

---

### Q4: How to cache seat availability?

**Problem**: Every hold/release invalidates cache. Invalidation storms at scale.

**Solution**: Cache with TTL + versioning:

```
Cache Key: "flight:{flight_id}:seats"
Value: {
    version: 42,
    capacity: 180,
    available_count: 45,
    booked_count: 135,
    held_count: 0,
    timestamp: 1234567890
}
TTL: 5 seconds (refresh automatically)

On hold/release:
    1. Update DB
    2. Increment version: version = 43
    3. Broadcast version to all replicas
    4. Replicas invalidate cache (or let TTL expire)
    5. Next query fetches fresh data
    
Benefits: 5-sec staleness acceptable for "Available seats: 45"
Cost: 5% stale data vs 99.9% cache hit ratio
```

---

### Q5: How to implement real-time seat availability updates?

**Solution**: WebSocket + Redis Pub/Sub:

```python
# When hold succeeds
def on_hold_success(flight_id, seat_id, user_id):
    redis_pub.publish(
        f"flight:{flight_id}:updates",
        json.dumps({"event": "seat_held", "seat": seat_id})
    )

# Client-side (WebSocket)
def on_message(msg):
    if msg['event'] == 'seat_held':
        mark_seat_unavailable(msg['seat'])  # UI update in 100ms
```

**Latency**: 
- Broadcast: 10ms
- Network: 50ms
- UI update: 40ms
- **Total**: ~100ms (near real-time)

---

### Q6: How to handle high-load scenarios (holiday rush)?

**Solution**: Load shedding + graceful degradation:

```python
def hold_seat(user_id, flight_id, seat_id):
    # Check system load
    current_throughput = get_current_tps()
    
    if current_throughput > threshold (e.g., 3000 TPS):
        # Graceful degradation
        if priority_queue.length() > 100000:
            raise TooManyRequestsError("System busy. Try again in 30s.")
        
        # Enqueue request
        priority_queue.enqueue({
            user_id, flight_id, seat_id,
            priority: user.loyalty_score  # VIP gets priority
        })
        return {"status": "queued", "position": priority_queue.length()}
    
    # Normal path
    return do_hold_seat(user_id, flight_id, seat_id)
```

**Benefits**: Graceful degradation vs total failure. Queue-based fairness.

---

### Q7: How to ensure exactly-once booking semantics?

**Problem**: Retry storm during network failures can double-charge or double-book.

**Solution**: Idempotency keys:

```python
# Client generates unique idempotency_key
def hold_seat(user_id, flight_id, seat_id, idempotency_key):
    
    # Check idempotency cache
    cached_result = redis.get(f"idempotency:{idempotency_key}")
    if cached_result:
        return json.loads(cached_result)  # Return cached result
    
    # Do hold
    booking = do_hold_seat(user_id, flight_id, seat_id)
    
    # Cache result with 1-hour TTL
    redis.setex(f"idempotency:{idempotency_key}", 3600, json.dumps(booking))
    
    return booking

# Client can retry 10x with same idempotency_key → always get same result
```

**Guarantees**: Exactly-once semantics despite network failures.

---

### Q8: How to recover from database failure?

**Solution**: Multi-region failover:

```
Primary Region (US-East) - ACTIVE
  └─ 1000 DB shards (primary + 5 replicas)
  └─ Replication lag: 100ms

Secondary Region (US-West) - STANDBY
  └─ 1000 DB shards (read-only replicas from primary)
  └─ Replication lag: 500ms

Failover Mechanism:
  - Health check every 10s
  - If primary down for 30s → promote secondary
  - Redirect all traffic to US-West
  - RTO: 30s, RPO: 500ms (acceptable for bookings)
```

---

### Q9: How to handle regulatory compliance (seat caps, refund policies)?

**Solution**: Policy engine + audit logs:

```python
class RefundPolicy:
    FULL_REFUND = 1.0     # Full refund anytime
    50_PERCENT = 0.5       # 50% refund if > 24h before flight
    NO_REFUND = 0.0        # No refund if < 6h before flight

def calculate_refund(booking):
    policy = get_refund_policy(booking.flight.airline)
    time_remaining = booking.flight.departure - datetime.now()
    
    if time_remaining > 24h:
        refund_pct = policy.FULL_REFUND
    elif time_remaining > 6h:
        refund_pct = policy.FIFTY_PERCENT
    else:
        refund_pct = policy.NO_REFUND
    
    return booking.price * refund_pct

# Audit log all refunds
audit_log.record({
    booking_id: "BK123",
    original_price: 150.0,
    refund_amount: 150.0,
    refund_pct: 1.0,
    policy: "FULL_REFUND",
    timestamp: now()
})
```

---

### Q10: How to implement revenue optimization (overbooking + surge pricing)?

**Solution**: Revenue management system:

```python
class RevenueOptimizer:
    def __init__(self, flight: Flight):
        self.flight = flight
        self.target_occupancy = 0.95  # 95% = some oversell buffer
        self.base_price = flight.base_price
    
    def get_dynamic_price(self) -> float:
        current_occupancy = 1.0 - (self.flight.available_count() / len(self.flight.seats))
        
        if current_occupancy < 0.5:
            return self.base_price * 0.7  # Discount to fill seats
        elif current_occupancy < 0.8:
            return self.base_price * 1.0  # Normal price
        elif current_occupancy < 0.95:
            return self.base_price * 1.3  # Premium
        else:
            return self.base_price * 1.8  # Last-minute surge
    
    def should_accept_booking(self) -> bool:
        booked = len([s for s in self.flight.seats.values() if s.status == SeatStatus.BOOKED])
        capacity = len(self.flight.seats)
        max_bookable = int(capacity * 1.05)  # 5% overbooking
        
        return booked < max_bookable
```

**Result**: Airlines maximize revenue while managing overbooking risk.

---

## Demo Scenarios

### Demo 1: Setup - Create Flights & Seats

```python
def demo_setup():
    system = AirlineSystem.get_instance()
    system.observers.clear()
    system.flights.clear()
    system.passengers.clear()
    system.bookings.clear()
    
    system.add_observer(ConsoleObserver())
    
    # Create flight
    flight = Flight(
        "AA101", "NYC", "LAX",
        datetime.now() + timedelta(hours=2),
        "Boeing 737"
    )
    
    # Add seats (10 Business, 20 Economy)
    for i in range(1, 11):
        flight.add_seat(Seat(f"{i}A", SeatClass.BUSINESS))
    for i in range(1, 21):
        flight.add_seat(Seat(f"{i}B", SeatClass.ECONOMY))
    
    system.add_flight(flight)
    
    # Register passengers
    p1 = Passenger("P001", "John Doe", "john@example.com")
    p2 = Passenger("P002", "Jane Smith", "jane@example.com")
    system.register_passenger(p1)
    system.register_passenger(p2)
    
    print(f"✅ Setup: Flight AA101 with 30 seats (10 Business, 20 Economy)")
    print(f"✅ Registered 2 passengers")
    
    return system, flight, p1, p2
```

### Demo 2: Search & Browse

```
Browse Flights:
  AA101: NYC → LAX at 2:00 PM (2 hours from now)
  Aircraft: Boeing 737
  Available seats: 30 (10 Business, 20 Economy)
  
Fixed Pricing:
  Business: $200
  Economy: $100
```

### Demo 3: Hold Seat

```
John holds seat 1A (Business) for 5 minutes
  Booking: BK001
  Status: HOLD
  Price: $200
  Hold until: 2:15 PM

Jane holds seat 1B (Economy) for 5 minutes
  Booking: BK002
  Status: HOLD
  Price: $100
  Hold until: 2:15 PM
```

### Demo 4: Dynamic Pricing

```
Current occupancy: 2/30 (6.7%)
Price: Economy $100, Business $200 (low demand discount applied)

After 20 more bookings (73% occupancy):
Price: Economy $130 (30% surge), Business $260 (30% surge)

After 28 bookings (93% occupancy, near capacity):
Price: Economy $150 (50% surge), Business $300 (50% surge)
Last-minute premium pricing kicks in!
```

### Demo 5: Full Booking Flow

```
John (BK001):
  [00:00] HOLD - Seat 1A for 5 minutes ($200)
  [01:30] CONFIRM - Payment processed
  [01:31] CONFIRMED - Seat booked permanently
  📧 Email: Booking confirmation to john@example.com

Jane (BK002):
  [00:10] HOLD - Seat 1B for 5 minutes ($100)
  [04:00] EXPIRED - Hold expired, seat released back to AVAILABLE
  Booking status: EXPIRED
  📧 Email: Hold expired notification to jane@example.com
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
        occupancy_rate = 1.0 - (available / total)
        multiplier = 1.0 + (occupancy_rate * 0.5)  # up to 1.5x
        return base * multiplier

# ============ OBSERVERS ============

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, booking: Booking):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event.upper():12} | "
              f"Passenger: {booking.passenger.name:15} | "
              f"Flight: {booking.flight.flight_id:8} | "
              f"Seat: {booking.seat.seat_id:4} | "
              f"Price: ${booking.price:.2f}")

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
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'AirlineSystem':
        return AirlineSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: Observer):
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        for obs in self.observers:
            obs.update(event, booking)
    
    def add_flight(self, flight: Flight):
        self.flights[flight.flight_id] = flight
    
    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.passenger_id] = passenger
    
    def hold_seat(self, passenger_id: str, flight_id: str, seat_id: str, 
                  hold_seconds: int = 300) -> Optional[Booking]:
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

# ============ DEMO ============

if __name__ == "__main__":
    print("="*70)
    print("AIRLINE MANAGEMENT SYSTEM")
    print("="*70)
    
    system = AirlineSystem.get_instance()
    system.observers.clear()
    system.flights.clear()
    system.passengers.clear()
    system.bookings.clear()
    
    system.add_observer(ConsoleObserver())
    system.add_observer(EmailNotifier())
    
    # Create flight with seats
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

---

## Design Patterns Summary

| Pattern | Purpose | Benefit |
|---------|---------|---------|
| **Singleton** | AirlineSystem controller | Single state, thread-safe, global access |
| **Strategy (Pricing)** | Fixed vs Demand-based | Pluggable algorithms, easy to add Surge pricing |
| **Observer** | Email/SMS/Console notifications | Loose coupling, event-driven |
| **State** | BookingStatus, SeatStatus | Explicit lifecycle, invalid states prevented |
| **Factory** | Seat/Flight/Booking creation | Centralized creation logic |

---

## Interview Tips

✅ **Start with clarifications**: Single airline? Multi-seat bookings? Cancellations allowed?  
✅ **Sketch first**: Draw flight layout, entity relationships  
✅ **Explain patterns**: Singleton ensures consistency, Strategy enables pricing flexibility  
✅ **Handle edge cases**: Hold expiry, concurrent holds, payment failure  
✅ **Demo incrementally**: Search → Hold → Confirm → Notify  
✅ **Discuss trade-offs**: In-memory vs DB, pessimistic vs optimistic locking  
✅ **Mention monitoring**: Alert thresholds, metrics, health checks  

---

## Success Checklist

- [ ] Explain 5 design patterns in < 1 minute each
- [ ] Draw UML class diagram from memory
- [ ] Walk through booking lifecycle: hold → confirm → notify
- [ ] Discuss hold expiry (5-min timeout, auto-release)
- [ ] Explain how to prevent overbooking
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs (locking, pricing, notifications)

---

**Ready for interview? Let's book some flights! 🛫**
