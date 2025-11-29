````markdown
# 🎬 Movie Ticket Booking System - 75 Minute Interview Guide

## System Overview

Multi-theater booking platform with seat management, dynamic pricing, and real-time availability.

**Scale**: 1,000 concurrent users, 100+ theaters, 10k+ bookings/day.  
**Duration**: 75 minutes | **Focus**: Design patterns, seat locking, pricing strategies.

---

## Core Entities

| Entity | Purpose | Relationships |
|--------|---------|---------------|
| **Movie** | Film information | Referenced by Shows |
| **Theater** | Cinema complex | Contains multiple Halls |
| **Hall** | Screening room | Has Seat layout (2D grid) |
| **Show** | Movie screening | Links Movie + Hall + time |
| **Seat** | Individual seat | Has type (Regular/Premium/VIP) + status |
| **Booking** | Reservation | Links User + Show + Seats |
| **User** | Customer | Creates Bookings |
| **Payment** | Transaction | Linked to Booking |

---

## Design Patterns Implemented

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single system instance | `BookingSystem.get_instance()` |
| **Strategy** | Pluggable pricing | `RegularPricing` vs `WeekendPricing` vs `HolidayPricing` |
| **Observer** | Event notifications | `EmailNotifier`, `SMSNotifier` for booking events |
| **State** | Status transitions | `BookingStatus` enum (PENDING → CONFIRMED → COMPLETED) |
| **Factory** | Object creation | `SeatFactory.create_layout()` for seat grids |
| **Decorator** | Add features | `DiscountDecorator` for dynamic pricing |

---

## SOLID Principles in Action

- **S**ingle Responsibility: Seat manages status; Booking manages reservations; Payment handles transactions
- **O**pen/Closed: Add new pricing strategies without modifying booking logic
- **L**iskov Substitution: `RegularPricing` and `WeekendPricing` are interchangeable
- **I**nterface Segregation: `Observer` interface focused on update notifications
- **D**ependency Inversion: System depends on `PricingStrategy` abstraction, not concrete classes

---

## 75-Minute Timeline

| Time | Phase | What to Code |
|------|-------|------------|
| 0–5 min | **Requirements** | Clarify scope, features, scale |
| 5–15 min | **Architecture** | Sketch class diagram, identify patterns |
| 15–35 min | **Core Entities** | Movie, Theater, Hall, Show, Seat, Booking classes |
| 35–55 min | **Booking Logic** | search_movies, lock_seats, create_booking, process_payment |
| 55–70 min | **System Integration** | BookingSystem (Singleton), Observer, Strategy patterns |
| 70–75 min | **Demo & Q&A** | Run INTERVIEW_COMPACT.py, discuss patterns |

---

## Demo Scenarios (5 included)

1. **Setup**: Create movies, theaters, shows with seat layout
2. **Search & Browse**: Find movies by title/genre, list shows
3. **Seat Selection**: Lock seats temporarily, prevent double-booking
4. **Pricing Strategies**: Switch between Regular/Weekend/Holiday pricing
5. **Full Booking Flow**: Browse → Select → Lock → Pay → Confirm

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Preparation Checklist

- [ ] Understand 6 design patterns and their purpose
- [ ] Memorize 75-minute timeline phases
- [ ] Know core entity relationships and attributes
- [ ] Explain seat locking mechanism (10-minute timeout)
- [ ] Can walk through booking flow step-by-step
- [ ] Practiced explaining trade-offs (locking strategies, pricing)
- [ ] Ran and understood INTERVIEW_COMPACT.py demos
- [ ] Prepared answers to 10 Q&A scenarios

---

## Key Concepts to Explain

**Singleton Pattern**: Ensures only one `BookingSystem` instance exists, managing all bookings, movies, shows centrally.

**Strategy Pattern**: Pricing algorithms are pluggable—switch between `RegularPricing`, `WeekendPricing`, `HolidayPricing` at runtime based on show date.

**Observer Pattern**: Booking events (created, confirmed, cancelled) notify all registered observers (Email, SMS, Push), enabling loose coupling.

**State Management**: Booking lifecycle explicitly modeled as `BookingStatus` enum with transitions (PENDING → LOCKED → CONFIRMED → COMPLETED/CANCELLED).

**Seat Locking**: Temporary 10-minute reservation prevents concurrent bookings. Lock expires automatically if payment not completed.

---

## File Structure

| File | Purpose |
|------|---------|
| **75_MINUTE_GUIDE.md** | Detailed implementation guide with code + UML + Q&A |
| **INTERVIEW_COMPACT.py** | Working implementation with 5 demo scenarios |
| **README.md** | This file—overview and checklist |
| **START_HERE.md** | Quick reference and talking points |

---

## Tips for Success

✅ **Start with clarifying questions** — Define scope and assumptions  
✅ **Sketch before coding** — Draw seat layout and relationships  
✅ **Explain patterns as you code** — Show design thinking  
✅ **Handle edge cases** — Seat locking expiry, double-booking, payment failure  
✅ **Demo incrementally** — Show browse → select → lock → pay flow  
✅ **Discuss trade-offs** — Optimistic vs pessimistic locking, cache invalidation  
✅ **Mention scaling** — Database sharding by theater, Redis for locks

````
