# 🅿️ Parking Lot System - 75 Minute Interview Guide

## Your 2 Main Resources
1. **README.md** - Complete reference guide covering all design patterns (Singleton, Strategy, Factory, Observer, State, Decorator) and SOLID principles with code examples
2. **75_MINUTE_GUIDE.md** - Step-by-step implementation timeline with exact code for each phase
3. **INTERVIEW_COMPACT.py** - Single runnable file with 5 complete demo scenarios

## 75-Minute Implementation Timeline

| Time | Phase | What to Implement | Lines |
|------|-------|-------------------|-------|
| 0-5 min | Requirements | Clarify: 4 vehicle types, 4 spot types, 100 total spots | 0 |
| 5-15 min | Architecture | Sketch: Singleton, Observer, Strategy patterns | 0 |
| 15-25 min | Phase 1 | Create enums (VehicleType, SpotType, TicketStatus) | 30 |
| 25-40 min | Phase 2 | Build Vehicle/Spot classes with type hierarchies | 100 |
| 40-55 min | Phase 3 | Implement Ticket, Payment, Entrance/Exit gates | 180 |
| 55-70 min | Phase 4 | Complete ParkingLot Singleton with observers | 300 |
| 70-75 min | Demo | Show 5 demo scenarios, explain patterns | 500 |

## Implementation Phases with Milestones

### Phase 1: Enumerations (5 minutes)
```python
- PaymentStatus: SUCCESS, FAIL, PENDING
- TicketStatus: ACTIVE, PAID, LOST
- SpotType: COMPACT, LARGE, HANDICAPPED, MOTORCYCLE
- VehicleType: CAR, VAN, TRUCK, MOTORCYCLE
```
**Milestone**: Clear type definitions established

### Phase 2: Vehicle & Spot Classes (15 minutes)
```python
- Vehicle base class + 4 subclasses (Car, Van, Truck, Motorcycle)
- ParkingSpot base class + 4 subclasses (CompactSpot, LargeSpot, HandicappedSpot, MotorcycleSpot)
- Each spot knows which vehicles it can hold
- Can assign/remove vehicles
```
**Milestone**: Type system with inheritance complete

### Phase 3: Ticket, Payment & Gates (15 minutes)
```python
- ParkingTicket: Auto-incrementing ID, entry/exit times, duration calculation
- Payment base class + 2 subclasses (CashPayment, CreditCardPayment)
- Entrance gate: Issues tickets, assigns spots
- Exit gate: Processes payments, releases spots
```
**Milestone**: Ticket & payment flow working

### Phase 4: ParkingLot Singleton & Observers (15 minutes)
```python
- ParkingLot Singleton: Manages 100 spots across 4 types
- is_full() check, get_available_spot() logic
- DisplayBoard Observer: Updates when spots change
- Notify all observers of changes
```
**Milestone**: Complete end-to-end flow functional

### Phase 5: Demo & Edge Cases (5 minutes)
```python
- Demo 1: Basic entry/exit
- Demo 2: Multiple vehicle types
- Demo 3: Lot becomes full
- Demo 4: Payment processing
- Demo 5: Display statistics
```

## Demo Scenarios to Show

### Demo 1: Basic Entry & Exit
- Vehicle enters, gets assigned spot type (Car → Compact)
- Parking ticket issued with ID
- Display board shows available spots decreasing
- Vehicle exits, payment processed
- Spot becomes available again

### Demo 2: Multiple Vehicle Types
- Car enters → Compact spot ✅
- Truck enters → Large spot ✅
- Motorcycle enters → Motorcycle spot ✅
- Show that Car cannot take Large (too small)

### Demo 3: Lot Becomes Full
- Fill up compact, large, handicapped, motorcycle spots in sequence
- Next vehicle rejected with "No available spot" message
- is_full() returns true

### Demo 4: Payment Processing
- Show Cash payment flow (immediate)
- Show Credit Card payment flow (different handler)
- Display updated ticket status: ACTIVE → PAID

### Demo 5: Statistics
- Show total vehicles parked
- Show available spots per type
- Show total revenue collected
- Show average parking duration

## Talking Points (What Interviewers Want to Hear)

### Design Pattern Discussion
- **Singleton**: "Why ParkingLot is Singleton" → ensures only one lot, consistent state
- **Observer**: "How DisplayBoard stays updated" → loose coupling, real-time notifications
- **Strategy**: "Vehicle/Spot matching logic" → extensible for different spot-finding algorithms
- **Factory**: "Vehicle and Member creation" → encapsulates object creation
- **State**: "Ticket states (Active → Paid)" → clear state transitions
- **Decorator**: "Premium parking features" → reserved spots for VIPs

### SOLID Principles
- **Single Responsibility**: Entrance only issues tickets, Exit only processes payment
- **Open/Closed**: Add new vehicle types without modifying existing code
- **Liskov Substitution**: Car, Van, Truck all substitute for Vehicle
- **Interface Segregation**: DisplayBoard depends only on Observer interface
- **Dependency Inversion**: ParkingLot depends on Vehicle abstraction, not concrete cars

### Architecture Highlights
- Spot assignment is O(1) using type-based buckets
- No nested loops for spot search
- Observable pattern prevents tight coupling
- Extensible payment strategies
- Atomic ticket operations (no double-booking)

## Answer to Follow-Up Questions

### "What if two vehicles arrive simultaneously?"
A: In reality, we'd use locks/mutexes. For interview: mention it, show single-threaded flow.

### "How do you handle lot overflow?"
A: is_full() check before assigning spot. Reject vehicle or queue them (mention but don't implement).

### "What if a vehicle loses its ticket?"
A: ParkingTicket has LOST status. Can query by license plate (mention enhancement).

### "How do different payment types work?"
A: Strategy pattern - Cash is immediate, CreditCard requires authorization.

### "What about reserved/handicapped spots?"
A: Only specific vehicles can use them. Validate in spot.canPark(vehicle).

### "How does the display update in real-time?"
A: Observer pattern - every spot change notifies DisplayBoard subscribers.

## Debugging Tips

### "Segment not available"
- Check: Is the spot type valid? (COMPACT, LARGE, etc.)
- Check: Are there available spots of that type?
- Verify: Vehicle.getSpotType() matches one of 4 types

### "Payment not processing"
- Check: Did exit gate receive valid ticket?
- Check: Is ticket status PAID or ACTIVE?
- Verify: Payment strategy is instantiated correctly

### "Display not updating"
- Check: Is DisplayBoard registered as observer?
- Check: Is notify_all() called after spot changes?
- Verify: Observer list is not empty

### "Lot full too early"
- Check: Are you counting available spots correctly?
- Check: Spot counts match config (40+30+20+10=100)?
- Verify: Spots being properly released on exit

## Emergency Options (If Stuck)

### Stuck on Enums (5 min in)?
→ Skip to basic Vehicle class, add enums later

### Stuck on Spot Matching (25 min in)?
→ Simple linear search for available spot, optimize later

### Stuck on Payment (45 min in)?
→ Skip payment strategies, just call process_payment()

### Stuck on Observer (60 min in)?
→ Simple list of display boards, update each one directly

### Running out of time (70 min in)?
→ Implement 1 demo scenario fully, explain other 4 verbally

## Pro Tips for Maximum Impact

1. **Start with Singleton** - Show get_instance() pattern immediately, explain why
2. **Visualize the architecture** - Draw on whiteboard as you code
3. **Mention patterns by name** - "Now implementing Observer pattern here"
4. **Test as you go** - Run each demo scenario after completing a phase
5. **Show, don't tell** - Execute code instead of just describing it
6. **Handle edge cases** - Show is_full() working correctly
7. **Explain trade-offs** - "We chose this for extensibility"
8. **Ask questions back** - "Should we support reservations?" (shows critical thinking)

## Success Criteria

✅ All 4 vehicle types work (Car, Van, Truck, Motorcycle)
✅ All 4 spot types implemented (Compact, Large, Handicapped, Motorcycle)  
✅ Spot assignment logic correct (vehicles get right spot types)
✅ Entrance/Exit flow complete (ticket issued and paid)
✅ Observer pattern working (display updates on changes)
✅ is_full() prevents overflow
✅ At least 3 demos run without errors
✅ Can explain 2 design patterns and 2 SOLID principles
✅ Handles edge cases (duplicate vehicle, no spots, wrong spot type)
✅ Code is clean, readable, and follows naming conventions

---

**Quick Start**: Run `python3 INTERVIEW_COMPACT.py` to see all 5 demos in action!
