# Car Rental System - 5 Minute Quick Start

## What Is This?
A multi-location car rental platform where customers can book vehicles with dynamic pricing, loyalty rewards, and damage tracking. Think Hertz/Enterprise but simplified.

## 75-Minute Interview Timeline

| Phase | Time | Focus |
|-------|------|-------|
| Requirements | 0-5 min | Clarify scope: multi-location? pricing strategy? damage handling? |
| Architecture | 5-15 min | Singleton coordinator, location inventory, booking lifecycle |
| Core Entities | 15-35 min | Vehicle, Customer, Location, Booking classes with methods |
| Business Logic | 35-55 min | Pricing strategies, loyalty discounts, cost calculation |
| Integration | 55-70 min | Observer pattern for notifications, thread safety with locks |
| Demo | 70-75 min | Run 5 scenarios showing patterns in action |

## 5 Core Entities (Memorize These)

### Vehicle
- Attributes: id, type, status (AVAILABLE/RENTED/MAINTENANCE), fuel, damage
- Methods: is_available(), reserve(), release()
- Rate: $40-150/day depending on type

### Customer  
- Attributes: id, name, email, total_rentals, loyalty_points
- Methods: add_booking(), get_loyalty_discount()
- Loyalty: 10% off at 10 rentals, 15% at 50, 20% at 100

### Location
- Attributes: id, name, city, vehicles[], bookings[]
- Methods: add_vehicle(), get_available_vehicles(), get_available_count()
- Thread-safe with lock protecting inventory

### Booking
- Attributes: id, customer, vehicle, location, pickup_date, dropoff_date, status, total_cost
- Methods: calculate_cost(), add_fuel_charge(), add_damage_charge(), activate(), return_vehicle()
- Status: PENDING → ACTIVE → COMPLETED → RETURNED

### Observer Pattern
- EmailNotifier, SMSNotifier, SystemLogNotifier
- Notified on: Booking Created, Vehicle Picked Up, Vehicle Returned

## 5 Design Patterns Explained

### 1. Singleton (CarRentalSystem)
**One global coordinator** - Single instance managing all bookings.
```
Why? Prevents duplicate bookings, centralized state
How? Thread-safe lazy initialization with _lock
Interview: "Ensures data consistency, one source of truth"
```

### 2. Strategy (PricingStrategy)  
**Switchable algorithms** - Choose pricing policy at runtime.
```
Policies: DailyRate ($60/day), WeeklyDiscount (15% off 7+), DemandBased (30% surge if low stock)
Why? Different pricing without modifying Booking class
How? Abstract PricingStrategy + 3 implementations
Interview: "Add new pricing without changing Booking code - Open/Closed principle"
```

### 3. Observer (BookingObserver)
**Loose coupling notifications** - Events trigger multiple notifiers.
```
Observers: Email, SMS, SystemLog
Why? Decouple Booking from notification channels
How? Abstract BookingObserver + _notify_observers()
Interview: "Easy to add new notification channels, listeners don't know about each other"
```

### 4. State (BookingStatus)
**Explicit lifecycle** - Enum prevents invalid state transitions.
```
States: PENDING → ACTIVE → COMPLETED → RETURNED
Why? Prevents bugs like completing non-active bookings
How? Validate status in activate(), complete(), return_vehicle()
Interview: "Each method checks preconditions, fail fast on invalid operations"
```

### 5. Factory
**Encapsulated creation** - Booking creation includes reservation + cost calc.
```
Why? Vehicle reservation must be atomic with booking creation
How? create_booking() validates, reserves vehicle, calculates cost, notifies observers
Interview: "Complex initialization logic in one place, ensures consistency"
```

## Key Interview Questions & Talking Points

### Basic (5 min)
1. **"What are the main entities?"**
   - Answer: Vehicle, Customer, Location, Booking, Observer notifiers

2. **"How is pricing calculated?"**
   - Answer: Strategy pattern enables 3 algorithms; apply loyalty discount after

3. **"What happens during booking?"**
   - Answer: Check availability → reserve vehicle → calculate cost → notify observers

### Intermediate (10 min)
4. **"How does loyalty discount work?"**
   - Answer: Based on total_rentals: 10+ = 10%, 50+ = 15%, 100+ = 20%

5. **"How is thread safety handled?"**
   - Answer: Location.lock protects vehicle inventory, System.lock protects bookings

6. **"What charges are added at return?"**
   - Answer: Fuel charge (50 cents per 1% deficit), damage charge (if reported)

7. **"How would you add late fees?"**
   - Answer: Add dropoff_date validation in return_vehicle(), calculate surcharge

### Advanced (15 min)
8. **"How would you prevent double-booking?"**
   - Answer: With.lock() on location during booking creation ensures first-come-first-served

9. **"How to scale to 1000 locations?"**
   - Answer: Database (MySQL) for persistence, Redis cache for availability, async notifications (Kafka)

10. **"How would you handle concurrent damage reports?"**
    - Answer: Same lock protects vehicle damage_reported flag, atomic CAS operation

11. **"What about payment integration?"**
    - Answer: External payment service in pickup_vehicle(), handle async confirmation

12. **"How to test concurrency?"**
    - Answer: Thread pool creating 100 simultaneous bookings on same vehicle, verify only 1 succeeds

## Success Checklist (Must Cover)

- [ ] Explain 5 entities and their relationships
- [ ] Draw state machine for Booking (PENDING → ACTIVE → COMPLETED → RETURNED)
- [ ] Describe Singleton pattern - why one CarRentalSystem?
- [ ] Explain Strategy pattern - show 3 pricing algorithms
- [ ] Show Observer pattern - how notifications work
- [ ] Discuss concurrency - Location.lock protects inventory
- [ ] Calculate example: 5-day SEDAN rental, customer with 15 rentals
  - Base: 5 days × $60 = $300
  - Loyalty: 10% discount = $270
  - If low stock: 30% surge = $351 (before loyalty)
- [ ] Run INTERVIEW_COMPACT.py demo to show all patterns working
- [ ] Answer at least 3 advanced questions about scaling/concurrency/payments

## Demo Commands

```bash
# Run all 5 demo scenarios
python3 INTERVIEW_COMPACT.py

# Expected output:
# DEMO 1: Setup locations/vehicles/customers, search inventory
# DEMO 2: Create booking with notifications
# DEMO 3: Loyalty discount (10% on 15 rentals)
# DEMO 4: Demand-based pricing surge (30% on low stock)
# DEMO 5: Return with fuel + damage charges
```

## If You Get Stuck...

### "I don't remember the entities"
→ Look at INTERVIEW_COMPACT.py classes: Vehicle, Customer, Location, Booking, Observer

### "How does pricing work?"
→ Check demo_3 (loyalty) and demo_4 (demand-based) output

### "Explain the observer pattern"
→ See demo_1 and demo_2 output showing [EMAIL], [SMS], [LOG] notifications

### "What about concurrency?"
→ Location.lock protects get_available_vehicles() and add_booking() with `with self.lock:`

### "Any edge case I'm missing?"
→ See README.md section "Edge Cases Handled" - covers vehicle unavailability, damage, fuel, etc.

## Common Mistakes to Avoid

- ❌ Forgetting thread safety → Location.lock required
- ❌ Calculating total_cost wrong → rental_cost + fuel_charge + damage_charge
- ❌ Loyalty discount applied wrong → Apply AFTER strategy pricing, before damage/fuel
- ❌ State transitions wrong → Check status before activate/complete/return
- ❌ Not resetting vehicle → Must call release() when booking cancelled

## Talking Points Summary

**"This system demonstrates clean architecture with 5 key design patterns. The Singleton coordinates all operations, Strategy enables flexible pricing, Observer decouples notifications, State prevents bugs, and Factory encapsulates complex creation. Thread safety is handled with locks protecting shared resources. Scaling requires database persistence, caching, and async message queues."**

