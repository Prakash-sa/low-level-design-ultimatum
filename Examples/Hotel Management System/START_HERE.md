# Hotel Management System - Quick Start (5 Minutes)

## What You're Building
Complete hotel management platform handling room inventory, reservations, check-in/check-out, billing, and guest services. Features dynamic pricing, room state management, and service requests.

---

## 75-Minute Timeline

| Time | Phase | Focus |
|------|-------|-------|
| 0-5 min | **Requirements** | Clarify functional (booking, check-in, billing, services) and non-functional (scalability, concurrency) |
| 5-15 min | **Architecture** | Design 6 core entities, choose 5 patterns (Singleton, Factory, Strategy, Observer, State) |
| 15-35 min | **Entities** | Implement Guest, Room, Reservation, Invoice, Payment, RoomService with business logic |
| 35-55 min | **Logic** | Implement pricing strategies, room factory, state machine, service commands |
| 55-70 min | **Integration** | Wire HotelManagementSystem singleton, add observers, demo 5 scenarios |
| 70-75 min | **Demo** | Walk through working code, explain patterns, answer questions |

---

## Core Entities (3-Sentence Each)

### 1. Guest
Registered hotel customer with contact info, loyalty points, and preferences. Tracks booking history and total spending. Rating affects priority for upgrades and special requests.

### 2. Room
Physical hotel room with type (STANDARD/DELUXE/SUITE), number, floor, and amenities. Maintains state machine (AVAILABLE→RESERVED→OCCUPIED→MAINTENANCE). Base price varies by room type.

### 3. Reservation
Booking linking Guest to Room(s) for specific dates. State machine: PENDING→CONFIRMED→CHECKED_IN→CHECKED_OUT. Stores total price calculated via PricingStrategy.

### 4. Invoice
Itemized bill tracking room charges, services, taxes. Aggregates all charges during stay. Generated at check-out with payment processing.

### 5. RoomService
Guest request for housekeeping, room service, or maintenance. Assigned to Staff based on availability and service type. Tracks completion status and charges.

### 6. Payment
Records payment transaction with method (CASH/CARD/ONLINE), amount, and timestamp. Links to Invoice for reconciliation. Supports partial payments.

---

## 5 Design Patterns (Why Each Matters)

### 1. Singleton - HotelManagementSystem
**What**: Single instance coordinates all hotel operations  
**Why**: Centralized room inventory, consistent pricing, thread-safe bookings  
**Talk Point**: "Ensures all reservations see same room availability. Alternative: Dependency injection for testing."

### 2. Factory - RoomFactory
**What**: Creates Standard/Deluxe/Suite rooms with appropriate pricing and amenities  
**Why**: Encapsulates room creation logic, easy to add new room types  
**Talk Point**: "Adding Presidential Suite just requires new factory method. No changes to reservation system."

### 3. Strategy - Pricing Algorithms
**What**: RegularPricing, SeasonalPricing, EventPricing  
**Why**: Runtime flexibility for promotional pricing, A/B testing  
**Talk Point**: "Can switch to weekend pricing without code changes. Easy to add CorporatePricing."

### 4. Observer - Notifications
**What**: GuestNotifier, StaffNotifier, AdminNotifier  
**Why**: Decoupled event handling for reservations, check-ins, service requests  
**Talk Point**: "Adding email notifications just requires new EmailNotifier observer. No changes to HotelManagementSystem."

### 5. State - Room Lifecycle
**What**: AVAILABLE→RESERVED→OCCUPIED→MAINTENANCE  
**Why**: Prevents invalid operations (can't check-in available room, can't reserve occupied room)  
**Talk Point**: "State machine enforces business rules. Can't reserve room with status OCCUPIED. Raises ValueError."

---

## Key Algorithms (30-Second Explanations)

### Room Availability Check
```python
# Check if room available for date range
for reservation in room.reservations:
    if date_ranges_overlap(check_in, check_out, 
                          reservation.check_in, reservation.check_out):
        return False
return room.status == RoomStatus.AVAILABLE
```
**Why**: Prevents double-booking, handles overlapping reservations.

### Dynamic Pricing
```python
base_price = room.base_price_per_night
num_nights = (check_out - check_in).days
strategy_multiplier = pricing_strategy.get_multiplier(check_in)
total = base_price * num_nights * strategy_multiplier
```
**Why**: Flexible pricing for seasons, events, demand.

### Service Assignment
```python
# Find available staff for service type
available_staff = [s for s in staff_list 
                   if s.service_type == request.type 
                   and s.is_available]
return max(available_staff, key=lambda s: s.rating)
```
**Why**: Assigns highest-rated available staff, ensures quality.

---

## Interview Talking Points

### Opening (0-5 min)
- "I'll design a hotel management system with dynamic pricing and concurrent booking support"
- "Core challenge: room availability conflicts, billing accuracy, service coordination"
- "Will use Singleton for system, Factory for rooms, Strategy for pricing, Observer for notifications"

### During Implementation (15-55 min)
- "Using date range overlap detection to prevent double-booking"
- "State machine prevents invalid room transitions like occupying maintenance room"
- "Thread lock protects create_reservation() to prevent race conditions"
- "Pricing strategy allows seasonal rates without changing reservation logic"

### Closing Demo (70-75 min)
- "Demo 1: Setup rooms and guests - shows factory pattern"
- "Demo 2: Successful reservation with dynamic pricing - shows strategy pattern"
- "Demo 3: Check-in to check-out flow with services - shows state machine"
- "Demo 4: Multi-room booking with discount - shows complex pricing"
- "Demo 5: Concurrent booking conflict handling - shows thread safety"

---

## Success Checklist

- [ ] Draw system architecture with 6 entities
- [ ] Explain Factory pattern for room creation
- [ ] Show 2 pricing strategies side-by-side
- [ ] Demonstrate state machine with valid/invalid transitions
- [ ] Describe observer pattern event flow
- [ ] Calculate multi-night pricing on whiteboard
- [ ] Discuss concurrency with lock mechanism
- [ ] Propose 2 scalability improvements (caching, sharding)
- [ ] Answer overbooking question (waitlist, compensation)
- [ ] Run working code with 5 demos

---

## Anti-Patterns to Avoid

**DON'T**:
- Hard-code room prices in HotelManagementSystem (violates Strategy)
- Create multiple HotelManagementSystem instances (violates Singleton)
- Allow direct room state changes without validation (violates State)
- Tightly couple notifications to reservation logic (violates Observer)
- Skip date overlap validation (causes double-booking)

**DO**:
- Make pricing strategies pluggable with abstract base class
- Use thread locks for critical sections (reservation, check-in)
- Validate state transitions in Room methods
- Explain trade-offs (in-memory vs database, synchronous vs async)
- Propose optimizations (room availability cache, event sourcing)

---

## 3 Advanced Follow-Ups (Be Ready)

### 1. Overbooking Strategy
"Add Waitlist when fully booked. Compensate with free upgrade or discount. Predict no-shows based on historical data. Reserve buffer rooms for premium guests."

### 2. Multi-Property Chain
"Add Hotel entity with location. Implement cross-property transfers. Centralized guest profile with loyalty points. Regional pricing strategies. Shared inventory for sister properties."

### 3. Scaling to 1000 Hotels
"Microservices for booking service. Redis cache for room availability. Kafka for async events. Database sharding by hotel_id. CDN for static content. Distributed locks with Redis."

---

## Run Commands

```bash
# Execute all 5 demos
python3 INTERVIEW_COMPACT.py

# Check syntax
python3 -m py_compile INTERVIEW_COMPACT.py

# View guide
cat 75_MINUTE_GUIDE.md
```

---

## The 60-Second Pitch

"I designed a hotel management system with 6 core entities: Guest, Room, Reservation, Invoice, Payment, RoomService. Uses Singleton for system coordination, Factory for room creation (Standard/Deluxe/Suite), Strategy pattern for pricing (Regular/Seasonal/Event), Observer for notifications, and State machine for room lifecycle. Key algorithm is date overlap detection for availability. Handles concurrency with thread locks. Demo shows seasonal pricing (1.3x summer), multi-room reservations, check-in to check-out flow with services, and conflict resolution. Scales with room availability cache and database sharding by hotel_id."

---

## What Interviewers Look For

1. **Clarity**: Can you explain complex booking logic simply?
2. **Patterns**: Do you recognize when to apply design patterns?
3. **Trade-offs**: Do you discuss pros/cons of approaches?
4. **Scalability**: Can you think beyond single-hotel solutions?
5. **Code Quality**: Is code clean, readable, well-structured?
6. **Problem-Solving**: How do you handle edge cases?
7. **Communication**: Do you think out loud?

---

## Final Tips

- **Draw first, code later**: Spend 10 minutes on architecture diagram
- **State assumptions clearly**: "Assuming calendar dates without time zones"
- **Test edge cases**: Double-booking, same-day check-in/out, invalid dates
- **Explain as you code**: "Adding lock here to prevent reservation conflicts"
- **Time management**: Leave 5 minutes for demo, don't over-engineer

**Good luck!** Run the code, understand the patterns, and explain trade-offs confidently.
