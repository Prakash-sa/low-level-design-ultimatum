# ✈️ Airline Management System - Quick Start (5-Min Read)

## 🎯 What You're Building

A single-airline booking system with:
- ✅ Seat inventory management
- ✅ Hold → Confirm → Cancel booking flow
- ✅ Dynamic pricing (demand-based)
- ✅ Real-time notifications (Observer pattern)
- ✅ Thread-safe singleton controller

**Scale**: 500 concurrent users | **Time**: 75 minutes | **Patterns**: 5 core patterns

---

## ⏱️ 75-Minute Timeline

| Time | Phase | Focus | Deliverable |
|------|-------|-------|-------------|
| 0–5 | Requirements | Clarify scope & scale | Assumptions confirmed |
| 5–15 | Architecture | Sketch relationships | System diagram |
| 15–35 | Core Entities | Code Flight, Seat, Passenger, Booking | Classes with state management |
| 35–55 | Business Logic | Booking flow + pricing strategy | hold_seat, confirm, cancel |
| 55–70 | System Integration | Singleton + Observer + Strategy | AirlineSystem controller |
| 70–75 | Demo & Q&A | Show 3-5 scenarios running | Discuss patterns & trade-offs |

---

## 🎨 5 Design Patterns (Learn These!)

### 1. **Singleton** (10 min to explain)
```
Why: Single AirlineSystem instance for consistent state
How: _instance + _lock + __new__ method
Where: AirlineSystem class
```

### 2. **Strategy** (5 min to explain)
```
Why: Swap pricing algorithms without changing booking code
How: Abstract PricingStrategy + FixedPricing + DemandBasedPricing
Where: system.set_pricing_strategy(strategy)
```

### 3. **Observer** (5 min to explain)
```
Why: Notify listeners of booking events without tight coupling
How: Observer interface + ConsoleObserver implementation
Where: notify_observers("held", booking)
```

### 4. **State** (5 min to explain)
```
Why: Model booking lifecycle (HOLD → CONFIRMED or EXPIRED)
How: BookingStatus enum with transition methods
Where: Booking.confirm(), Booking.cancel(), Booking.expire()
```

### 5. **Factory** (optional, 3 min)
```
Why: Centralize object creation
How: Static factory methods in AirlineSystem
Where: system.add_flight(flight), system.register_passenger(p)
```

---

## 🏗️ Core Classes (Memorize These!)

```python
# Enums
SeatStatus: AVAILABLE, HOLD, BOOKED
BookingStatus: HOLD, CONFIRMED, CANCELLED, EXPIRED
SeatClass: ECONOMY, BUSINESS

# Core Classes
Seat(seat_id, seat_class) → is_available(), hold(), book(), release()
Passenger(id, name, email)
Flight(id, origin, dest, departure, aircraft) → add_seat(), get_seat()
Booking(id, passenger, flight, seat, price) → confirm(), cancel(), expire()

# Strategies
PricingStrategy (abstract)
  ├─ FixedPricing (Economy $100, Business $200)
  └─ DemandBasedPricing (multiplier based on occupancy)

# Observer
Observer (abstract) → update(event, booking)
  └─ ConsoleObserver (prints to console)

# System
AirlineSystem (Singleton) → hold_seat(), confirm_booking(), cancel_booking()
```

---

## 💬 Quick Talking Points

**"What design patterns did you use?"**
> Singleton for the system controller, Strategy for pricing, Observer for notifications, State model for booking lifecycle.

**"How do you prevent double-booking?"**
> Use seat status enum (AVAILABLE → HOLD → BOOKED) with atomic transitions. Each operation checks status before changing it.

**"How would you scale this?"**
> Shard flights by route/date, cache seat availability, use message queues for async notifications, database transactions for consistency.

**"How do you handle hold expiry?"**
> Set hold_until timestamp when creating booking. Before confirm, check if now > hold_until. If expired, call expire() which releases the seat.

**"Why Strategy pattern for pricing?"**
> Allows plugging different algorithms without modifying booking code. Easy to test, add new strategies, and switch at runtime.

---

## 🚀 Quick Commands

```bash
# Run all 5 demo scenarios
python3 INTERVIEW_COMPACT.py

# Expected output:
# DEMO 1: System Setup & Flight Creation
# DEMO 2: Hold & Confirm Booking
# DEMO 3: Dynamic Pricing - Demand-Based Strategy
# DEMO 4: Cancellation & Seat Release
# DEMO 5: Complete Booking Flow - Multiple Bookings
# ✅ ALL DEMOS COMPLETED SUCCESSFULLY
```

---

## ✅ Success Checklist

- [ ] Can draw UML class diagram from memory
- [ ] Explain each of 5 patterns in < 1 minute
- [ ] Walk through booking flow: hold → confirm → cancel
- [ ] Run INTERVIEW_COMPACT.py without errors
- [ ] Answer 3 of 12 interview Q&A questions correctly
- [ ] Discuss 2 trade-offs (consistency, concurrency, scalability)
- [ ] Code compiles without linting errors

---

## 🆘 If You Get Stuck

**At 15 min mark** (still designing):
> Focus on core entities first. Patterns can be simplified—just get classes working.

**At 35 min mark** (mid-implementation):
> Skip fancy features. Implement hold_seat, confirm_booking, cancel_booking in basic form.

**At 55 min mark** (need integration):
> Create AirlineSystem as simple controller. Observer can be basic (just print events).

**At 70 min mark** (show something):
> Run demo, explain patterns verbally. Even incomplete code is better than silence.

---

## 📚 Deep Dive Resources

| Resource | Time | Content |
|----------|------|---------|
| **75_MINUTE_GUIDE.md** | 20 min | Complete code + UML + 12 Q&A |
| **INTERVIEW_COMPACT.py** | 5 min | Working implementation |
| **README.md** | 10 min | Overview + checklist |
| **This file** | 5 min | Quick reference |

---

## 🎓 Key Takeaway

> Design patterns aren't about complexity—they're about making code extensible, testable, and maintainable. Show the interviewer you understand why each pattern matters, not just how to implement it.

**Ready?** Run `python3 INTERVIEW_COMPACT.py` and then read `75_MINUTE_GUIDE.md`.
