# Hotel Management System - Reference Guide

## System Overview
Complete hotel management platform handling room inventory, reservations, guest services, check-in/check-out, and billing. Features dynamic pricing, state management, and real-time notifications.

---

## Core Entities

| Entity | Attributes | Responsibilities |
|--------|-----------|------------------|
| **Guest** | guest_id, name, email, phone, loyalty_points, total_spent, preferences | Make reservations, check-in/out, request services, earn loyalty points |
| **Room** | room_id, room_number, room_type (STANDARD/DELUXE/SUITE), floor, status, base_price, amenities | Track availability, manage state transitions, store reservations |
| **Reservation** | reservation_id, guest, rooms, check_in_date, check_out_date, status, total_price | Link guest to room(s), track booking lifecycle, calculate pricing |
| **Invoice** | invoice_id, reservation, room_charges, service_charges, taxes, total_amount | Itemize all charges, calculate totals, support payment processing |
| **Payment** | payment_id, invoice, amount, payment_method (CASH/CARD/ONLINE), timestamp | Record transactions, track payment status, support partial payments |
| **RoomService** | service_id, room, service_type, description, status, assigned_staff, charge | Handle guest requests, assign to staff, track completion, add to bill |
| **Staff** | staff_id, name, role, service_type, is_available, rating | Process check-in/out, fulfill service requests, update room status |
| **HotelManagementSystem** | rooms, guests, reservations, staff, pricing_strategy, observers | Coordinate all operations, manage inventory, process bookings |

---

## Design Patterns Implementation

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | HotelManagementSystem - single instance coordinates all operations | Centralized state management, consistent room inventory, thread-safe operations |
| **Factory** | RoomFactory creates Standard/Deluxe/Suite with proper config | Encapsulated room creation, easy to add new types, consistent initialization |
| **Strategy** | Pricing algorithms (Regular/Seasonal/Event) | Runtime pricing flexibility, A/B testing support, easy to add promotional pricing |
| **Observer** | Notifications (Guest/Staff/Admin) | Decoupled event handling, extensible notification channels (email, SMS, push) |
| **State** | Room and Reservation lifecycle state machines | Enforces valid transitions, prevents illegal operations, clear business rules |

---

## Pricing Strategies Comparison

| Strategy | Base Logic | Multiplier | Use Case |
|----------|-----------|------------|----------|
| **RegularPricing** | Room base price × nights | 1.0x | Standard bookings, off-season |
| **SeasonalPricing** | Base × season multiplier | Summer: 1.3x, Winter: 0.8x, Spring/Fall: 1.0x | Holiday periods, tourist seasons |
| **EventPricing** | Base × event multiplier | Conference: 1.5x, Concert: 2.0x | Special events in city |
| **LoyaltyPricing** | Base × (1 - loyalty discount) | 5% off per 1000 points | Reward repeat customers |

**Pricing Calculation**:
```python
base_price = room.base_price_per_night
num_nights = (check_out_date - check_in_date).days
multiplier = pricing_strategy.get_multiplier(check_in_date, guest)
total_price = base_price * num_nights * multiplier
```

---

## Room State Machine

```
AVAILABLE → RESERVED → OCCUPIED → AVAILABLE
    ↓           ↓           ↓
MAINTENANCE CANCELLED  MAINTENANCE
```

**Valid Transitions**:
- AVAILABLE → RESERVED: Guest makes reservation
- RESERVED → OCCUPIED: Guest checks in
- OCCUPIED → AVAILABLE: Guest checks out, room cleaned
- Any → MAINTENANCE: Room needs repair
- MAINTENANCE → AVAILABLE: Repairs complete
- RESERVED → CANCELLED: Guest cancels booking

**Invalid Transitions** (throw ValueError):
- RESERVED → RESERVED (already reserved)
- OCCUPIED → RESERVED (must check out first)
- MAINTENANCE → OCCUPIED (must be available first)

---

## Reservation State Machine

```
PENDING → CONFIRMED → CHECKED_IN → CHECKED_OUT
    ↓         ↓
CANCELLED CANCELLED
```

**Valid Transitions**:
- PENDING → CONFIRMED: Payment confirmed
- CONFIRMED → CHECKED_IN: Guest arrives, check-in processed
- CHECKED_IN → CHECKED_OUT: Guest departs, payment settled
- PENDING/CONFIRMED → CANCELLED: Guest or admin cancels

**Invalid Transitions** (throw ValueError):
- CHECKED_OUT → CHECKED_IN (cannot re-check-in)
- CHECKED_IN → CONFIRMED (must check out first)

---

## Room Availability Algorithm

```python
def is_room_available(room, check_in, check_out):
    """Check if room available for date range"""
    # Room must be in available state
    if room.status != RoomStatus.AVAILABLE:
        return False
    
    # Check for overlapping reservations
    for reservation in room.reservations:
        if reservation.status in [ReservationStatus.CONFIRMED, 
                                 ReservationStatus.CHECKED_IN]:
            # Check date range overlap
            if not (check_out <= reservation.check_in_date or 
                   check_in >= reservation.check_out_date):
                return False
    
    return True
```

**Complexity**: O(n) where n = number of reservations for room
**Optimization**: Use interval tree for O(log n) lookup with many reservations

---

## Observer Pattern Event Types

| Event | Triggered When | Notifiers Called | Example Message |
|-------|----------------|------------------|----------------|
| `reservation_created` | New booking made | Guest, Admin | "Reservation R001 confirmed for 3 nights" |
| `check_in_complete` | Guest checks in | Guest, Staff | "Checked in to Room 201. Enjoy your stay!" |
| `service_requested` | Guest requests service | Guest, Staff | "Room service requested for Room 201" |
| `service_completed` | Service fulfilled | Guest, Staff | "Housekeeping completed for Room 201" |
| `check_out_complete` | Guest checks out | Guest, Admin | "Checked out. Total: $450. Thank you!" |
| `payment_received` | Payment processed | Guest, Admin | "Payment of $450 received via CARD" |
| `room_maintenance` | Room needs repair | Staff, Admin | "Room 201 marked for maintenance" |

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Room handles state; Reservation handles booking; Invoice handles billing |
| **Open/Closed** | Add new pricing/room types without modifying HotelManagementSystem |
| **Liskov Substitution** | All PricingStrategy subclasses interchangeable at runtime |
| **Interface Segregation** | Observer requires only `update()`; Strategy requires single method |
| **Dependency Inversion** | HotelManagementSystem depends on abstract Strategy/Observer, not concrete classes |

---

## Concurrency & Thread Safety

**Challenges**:
- Multiple guests booking same room simultaneously
- Room status changes (check-in while another booking processing)
- Invoice calculation during payment processing

**Solutions**:
```python
# System-level lock protects create_reservation()
with self.lock:
    # Check room availability
    # Mark room as reserved
    # Create reservation
    # Update inventory
```

**Alternative Approaches**:
- Database row-level locks on room availability
- Optimistic locking with version numbers
- Event sourcing with append-only log
- Queue-based booking with single consumer per room

---

## System Architecture Diagram

```
┌─────────────────────────────────────────┐
│   HotelManagementSystem (Singleton)     │
├─────────────────────────────────────────┤
│ - rooms: Map<id, Room>                  │
│ - guests: Map<id, Guest>                │
│ - reservations: Map<id, Reservation>    │
│ - staff: Map<id, Staff>                 │
│ - pricing_strategy: Strategy            │
│ - observers: List<Observer>             │
├─────────────────────────────────────────┤
│ + create_reservation()                  │
│ + check_in()                            │
│ + check_out()                           │
│ + request_service()                     │
│ + process_payment()                     │
└─────────────────────────────────────────┘
         │              │
         ▼              ▼
    ┌────────┐    ┌──────────┐
    │  Room  │    │  Guest   │
    ├────────┤    ├──────────┤
    │status  │    │loyalty   │
    │price   │    │spending  │
    └────────┘    └──────────┘
```

---

## Common Interview Follow-Ups

**Q: How would you handle overbooking?**
A: Implement waitlist for fully booked dates. Offer upgrades to higher room types. Compensate with discounts or free nights. Partner with nearby hotels for overflow. Predict no-shows using historical data.

**Q: How to prevent double-booking?**
A: Thread locks during reservation creation. Database transactions with row-level locks. Optimistic locking with version numbers. Two-phase commit for distributed systems. Idempotency keys for API requests.

**Q: How to implement multi-property hotel chain?**
A: Add Hotel entity with location. Centralized guest profile with cross-property loyalty. Regional pricing strategies. Shared inventory for sister properties. Transfer reservations between properties. Corporate rate agreements.

**Q: How to scale to 1000 properties?**
A: Microservices architecture (booking, billing, inventory services). Redis cache for room availability. Kafka for async events. Database sharding by hotel_id or region. CDN for static content. Global load balancer with regional routing.

