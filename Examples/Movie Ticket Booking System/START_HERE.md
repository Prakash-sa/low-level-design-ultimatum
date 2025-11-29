````markdown
# 🎬 Movie Ticket Booking System - Quick Start (5-Min Read)

## 🎯 What You're Building

A multi-theater booking platform with:
- ✅ Movie browsing and search
- ✅ Theater and show management
- ✅ Seat selection with 2D layout
- ✅ Temporary seat locking (10 minutes)
- ✅ Dynamic pricing (Regular/Weekend/Holiday)
- ✅ Payment processing and booking confirmation

**Scale**: 1,000 concurrent users | **Time**: 75 minutes | **Patterns**: 6 core patterns

---

## ⏱️ 75-Minute Timeline

| Time | Phase | Focus | Deliverable |
|------|-------|-------|-------------|
| 0–5 | Requirements | Clarify features & scale | Assumptions confirmed |
| 5–15 | Architecture | Sketch relationships | System diagram |
| 15–35 | Core Entities | Code Movie, Theater, Hall, Show, Seat, Booking | Classes with attributes |
| 35–55 | Business Logic | Booking flow + pricing + seat locking | search, lock_seats, create_booking |
| 55–70 | System Integration | Singleton + Observer + Strategy | BookingSystem controller |
| 70–75 | Demo & Q&A | Show 3-5 scenarios running | Discuss patterns & trade-offs |

---

## 🎨 6 Design Patterns (Learn These!)

### 1. **Singleton** (10 min to explain)
```
Why: Single BookingSystem instance for consistent state
How: _instance + _lock + __new__ method
Where: BookingSystem class
```

### 2. **Strategy** (5 min to explain)
```
Why: Swap pricing algorithms without changing booking code
How: Abstract PricingStrategy + RegularPricing + WeekendPricing + HolidayPricing
Where: system.set_pricing_strategy(strategy)
```

### 3. **Observer** (5 min to explain)
```
Why: Notify listeners of booking events without tight coupling
How: Observer interface + EmailNotifier + SMSNotifier
Where: notify_observers("booking_confirmed", booking)
```

### 4. **State** (5 min to explain)
```
Why: Model booking lifecycle (PENDING → LOCKED → CONFIRMED → COMPLETED)
How: BookingStatus enum with transition methods
Where: Booking.confirm(), Booking.cancel()
```

### 5. **Factory** (3 min)
```
Why: Centralize seat creation
How: SeatFactory.create_seat(row, num, type)
Where: Hall.generate_seat_layout()
```

### 6. **Decorator** (3 min)
```
Why: Add discounts dynamically
How: DiscountDecorator wraps booking
Where: StudentDiscount, BulkDiscount
```

---

## 🏗️ Core Classes (Memorize These!)

```python
# Enums
SeatType: REGULAR, PREMIUM, VIP
SeatStatus: AVAILABLE, LOCKED, BOOKED
BookingStatus: PENDING, LOCKED, CONFIRMED, CANCELLED, COMPLETED

# Core Classes
Movie(movie_id, title, duration, genre, language, rating)
Theater(theater_id, name, location, city) → add_hall()
Hall(hall_id, theater, capacity, seat_layout) → get_available_seats()
Show(show_id, movie, hall, start_time, base_price) → lock_seats()
Seat(seat_id, row, number, seat_type, status) → lock(), unlock(), book()
Booking(booking_id, user, show, seats, status, total) → confirm(), cancel()
User(user_id, name, email, phone, bookings)
Payment(payment_id, booking, amount, method, status) → process(), refund()

# Strategies
PricingStrategy (abstract)
  ├─ RegularPricing (base price)
  ├─ WeekendPricing (+50%)
  └─ HolidayPricing (+100%)

# Observer
BookingObserver (abstract) → update(event, booking)
  ├─ EmailNotifier
  ├─ SMSNotifier
  └─ PushNotificationService

# System
BookingSystem (Singleton) → search_movies(), create_booking(), lock_seats()
```

---

## 💬 Quick Talking Points

**"What design patterns did you use?"**
> Singleton for system controller, Strategy for pricing (Regular/Weekend/Holiday), Observer for notifications (Email/SMS), State for booking lifecycle, Factory for seat creation, Decorator for discounts.

**"How do you prevent double-booking?"**
> Use seat status enum (AVAILABLE → LOCKED → BOOKED) with 10-minute timeout. When user selects seats, they're locked with timestamp. If payment not completed within 10 min, lock expires and seat auto-releases.

**"How would you scale this?"**
> Shard database by theater/city, use Redis for seat locks, cache hot data (popular movies, show times), async message queues for notifications, load balancer for API servers.

**"How do you handle seat lock expiry?"**
> Set locked_until timestamp when locking seat. Background job runs every minute checking expired locks and releasing seats. Also check on-demand when user queries seat availability.

**"Why Strategy pattern for pricing?"**
> Allows plugging different algorithms based on show date without modifying booking code. Easy to test, add new strategies (matinee, senior, surge), and switch at runtime.

---

## 🚀 Quick Commands

```bash
# Run all 5 demo scenarios
python3 INTERVIEW_COMPACT.py

# Expected output:
# DEMO 1: Setup & Movie/Theater Creation
# DEMO 2: Search & Browse Movies
# DEMO 3: Seat Selection & Locking
# DEMO 4: Pricing Strategies (Regular/Weekend/Holiday)
# DEMO 5: Complete Booking Flow
# ✅ ALL DEMOS COMPLETED SUCCESSFULLY
```

---

## ✅ Success Checklist

- [ ] Can draw UML class diagram from memory
- [ ] Explain each of 6 patterns in < 1 minute
- [ ] Walk through booking flow: browse → select → lock → pay → confirm
- [ ] Run INTERVIEW_COMPACT.py without errors
- [ ] Answer 3 of 10 interview Q&A questions correctly
- [ ] Discuss 2 trade-offs (seat locking, pricing, concurrency)
- [ ] Code compiles without errors

---

## 🆘 If You Get Stuck

**At 15 min mark** (still designing):
> Focus on core entities first. Patterns can be simplified—just get classes working.

**At 35 min mark** (mid-implementation):
> Skip fancy features. Implement search_movies, lock_seats, create_booking in basic form.

**At 55 min mark** (need integration):
> Create BookingSystem as simple controller. Observer can be basic (just print events).

**At 70 min mark** (show something):
> Run demo, explain patterns verbally. Even incomplete code is better than silence.

---

## 📚 Deep Dive Resources

| Resource | Time | Content |
|----------|------|---------|
| **75_MINUTE_GUIDE.md** | 20 min | Complete code + UML + 10 Q&A |
| **INTERVIEW_COMPACT.py** | 5 min | Working implementation |
| **README.md** | 10 min | Overview + checklist |
| **This file** | 5 min | Quick reference |

---

## 🎓 Key Takeaway

> Design patterns aren't about complexity—they're about making code extensible, testable, and maintainable. Show the interviewer you understand why each pattern matters, not just how to implement it.

**Ready?** Run `python3 INTERVIEW_COMPACT.py` and then read `75_MINUTE_GUIDE.md`.

````
