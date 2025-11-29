# ✈️ Airline Management System - 75 Minute Interview Guide

## System Overview

Single-airline booking system with seat reservations, dynamic pricing, and event notifications.

**Scale**: 500 concurrent users, 1–10k flights/day, moderate booking volume.  
**Duration**: 75 minutes | **Focus**: Design patterns, extensibility, booking lifecycle.

---

## Core Entities

| Entity | Purpose | Relationships |
|--------|---------|---------------|
| **Flight** | Flight with seat inventory | Owns multiple Seats |
| **Seat** | Individual seat on flight | Has SeatStatus + SeatClass |
| **Passenger** | Passenger information | Referenced by Booking |
| **Booking** | Reservation with lifecycle | Links Passenger + Seat + Flight |

---

## Design Patterns Implemented

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single system instance | `AirlineSystem.get_instance()` |
| **Strategy** | Pluggable algorithms | `FixedPricing` vs `DemandBasedPricing` |
| **Observer** | Event notifications | `ConsoleObserver` for booking events |
| **State** | Status transitions | `BookingStatus` enum (HOLD → CONFIRMED) |
| **Factory** | Object creation | Factory methods in `AirlineSystem` |

---

## SOLID Principles in Action

- **S**ingle Responsibility: Seat handles only seat state; Booking handles booking state
- **O**pen/Closed: Add new pricing strategies without modifying core booking logic
- **L**iskov Substitution: `FixedPricing` and `DemandBasedPricing` are interchangeable
- **I**nterface Segregation: `Observer` interface focused on update notification
- **D**ependency Inversion: System depends on `PricingStrategy` abstraction, not concrete classes

---

## 75-Minute Timeline

| Time | Phase | What to Code |
|------|-------|------------|
| 0–5 min | **Requirements** | Clarify scope, scale, assumptions |
| 5–15 min | **Architecture** | Sketch design, identify patterns |
| 15–35 min | **Core Entities** | Seat, Passenger, Flight, Booking classes |
| 35–55 min | **Booking Logic** | hold_seat, confirm_booking, cancel_booking |
| 55–70 min | **System Integration** | AirlineSystem (Singleton), Observer, Strategy |
| 70–75 min | **Demo & Q&A** | Run INTERVIEW_COMPACT.py, discuss patterns |

---

## Demo Scenarios (5 included)

1. **Setup**: Create flight, passengers, register observer
2. **Hold & Confirm**: Basic booking flow with status transitions
3. **Dynamic Pricing**: Switch between Fixed and Demand-Based strategies
4. **Cancellation**: Release seat and trigger notifications
5. **Full Flow**: Multiple concurrent bookings with pricing updates

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Preparation Checklist

- [ ] Understand 5 design patterns and their purpose
- [ ] Memorize 75-minute timeline phases
- [ ] Know core entity relationships and attributes
- [ ] Explain HOLD vs CONFIRMED lifecycle
- [ ] Can walk through booking flow step-by-step
- [ ] Practiced explaining trade-offs (consistency vs availability)
- [ ] Ran and understood INTERVIEW_COMPACT.py demos
- [ ] Prepared answers to 12 Q&A scenarios

---

## Key Concepts to Explain

**Singleton Pattern**: Ensures only one `AirlineSystem` instance exists, simplifying state management.

**Strategy Pattern**: Pricing algorithms are pluggable—switch between `FixedPricing` and `DemandBasedPricing` at runtime without changing booking code.

**Observer Pattern**: Booking events (held, confirmed, cancelled, expired) notify all registered observers, enabling loose coupling.

**State Management**: Booking lifecycle explicitly modeled as `BookingStatus` enum with transitions, preventing invalid state changes.

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
✅ **Sketch before coding** — Draw relationships on whiteboard  
✅ **Explain patterns as you code** — Show design thinking  
✅ **Handle edge cases** — Hold expiry, double-booking, payment failure  
✅ **Demo incrementally** — Show hold → confirm → cancel flow  
✅ **Discuss trade-offs** — Consistency vs availability, locks vs optimistic updates  
✅ **Mention scaling** — Sharding, caching, message queues (don't over-engineer)
