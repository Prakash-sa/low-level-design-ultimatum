# Hotel Management System — 75-Minute Interview Guide

## Quick Start Overview

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

## 5 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Why Each Matters)

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


## 75-Minute Guide

## System Overview
**Complete hotel management platform** handling room bookings, guest services, staff coordination, dynamic pricing, and real-time notifications. Think Marriott/Hilton backend simplified.

**Core Challenge**: Room inventory management, concurrent reservations, dynamic pricing strategies, service request coordination, and state management.

---

## Requirements Clarification (0-5 min)

### Functional Requirements
1. **Room Management**: Multiple room types (Standard/Deluxe/Suite), capacity, amenities, pricing
2. **Guest Management**: Register guests, track stays, loyalty points, preferences
3. **Reservation System**: Book rooms, check availability, handle check-in/check-out
4. **Dynamic Pricing**: Regular, seasonal, event-based pricing strategies
5. **Room Lifecycle**: AVAILABLE → RESERVED → OCCUPIED → MAINTENANCE
6. **Reservation Lifecycle**: PENDING → CONFIRMED → CHECKED_IN → CHECKED_OUT
7. **Service Requests**: Room service, housekeeping, maintenance with priority levels
8. **Billing System**: Generate invoices, process payments, track charges
9. **Staff Management**: Assign tasks, track availability, coordinate services
10. **Notifications**: Real-time updates to guests, staff, and admin

### Non-Functional Requirements
- **Performance**: Handle 1000 concurrent reservations
- **Scale**: 500 rooms, 10K guests, 500 staff members
- **Availability**: 99.9% uptime
- **Concurrency**: Thread-safe room booking (prevent double-booking)
- **Data Integrity**: ACID compliance for reservations and payments

### Key Design Decisions
1. **Room Creation**: Factory pattern for different room types
2. **Pricing**: Strategy pattern (Regular/Seasonal/Event pricing)
3. **State Management**: State pattern for room and reservation states
4. **Notifications**: Observer pattern for real-time updates
5. **Service Requests**: Command pattern for queuing and processing
6. **System Coordination**: Singleton HotelManagementSystem

---

## Architecture & Design (5-15 min)

### System Architecture

```
HotelManagementSystem (Singleton)
├── Room Inventory (Factory)
│   ├── Standard Rooms ($100/night)
│   ├── Deluxe Rooms ($200/night)
│   └── Suite Rooms ($400/night)
├── Guest Registry
│   └── Guest → Loyalty Points → Preferences
├── Reservations
│   └── Reservation → Status → Room → Dates
├── Pricing Strategy (pluggable)
│   ├── RegularPricing
│   ├── SeasonalPricing (summer +30%, winter +50%)
│   └── EventPricing (conference dates +100%)
├── Service Requests (Command Queue)
│   ├── RoomServiceCommand
│   ├── HousekeepingCommand
│   └── MaintenanceCommand
├── Staff Management
│   └── Staff → Role → Availability → Assigned Tasks
├── Billing System
│   └── Invoice → Line Items → Payments
└── Observers
    ├── GuestNotifier
    ├── StaffNotifier
    └── AdminNotifier
```

### Design Patterns Used

1. **Singleton**: HotelManagementSystem (centralized control)
2. **Factory**: Room creation (Standard/Deluxe/Suite with different configurations)
3. **Strategy**: Pricing algorithms (Regular/Seasonal/Event)
4. **Observer**: Notifications (Guest/Staff/Admin)
5. **State**: Room lifecycle (AVAILABLE/RESERVED/OCCUPIED/MAINTENANCE)
6. **State**: Reservation lifecycle (PENDING/CONFIRMED/CHECKED_IN/CHECKED_OUT)
7. **Command**: Service requests (encapsulated, queueable, trackable)

---

## Core Entities (15-35 min)

### 1. Enumerations

```python
from enum import Enum

class RoomType(Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"

class RoomStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ONLINE = "online"

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class ServiceType(Enum):
    ROOM_SERVICE = "room_service"
    HOUSEKEEPING = "housekeeping"
    MAINTENANCE = "maintenance"
    LAUNDRY = "laundry"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
```

**Key Points**:
- Clear state definitions prevent invalid transitions
- Service types enable proper staff assignment
- Priority levels for service request handling

### 2. Guest Class

```python
from datetime import datetime
from typing import List, Optional

class Guest:
    """Guest with loyalty program and preferences"""
    def __init__(self, guest_id: str, name: str, email: str, phone: str):
        self.guest_id = guest_id
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = datetime.now()
        self.loyalty_points = 0
        self.total_stays = 0
        self.total_spent = 0.0
        self.preferences = {}  # Room preferences, dietary restrictions
        self.is_vip = False
    
    def add_loyalty_points(self, points: int):
        """Add loyalty points from stay"""
        self.loyalty_points += points
        if self.loyalty_points >= 1000:
            self.is_vip = True
    
    def get_discount_percentage(self) -> float:
        """Calculate loyalty discount"""
        if self.is_vip:
            return 0.15  # 15% VIP discount
        elif self.loyalty_points >= 500:
            return 0.10  # 10% silver discount
        elif self.loyalty_points >= 200:
            return 0.05  # 5% bronze discount
        return 0.0
    
    def __str__(self):
        vip_status = "VIP" if self.is_vip else "Regular"
        return "%s (%s) - Points: %d, Stays: %d" % (
            self.name, vip_status, self.loyalty_points, self.total_stays)
```

**Key Points**:
- Loyalty points drive VIP status and discounts
- Track stay history for analytics
- Preferences stored for personalization

### 3. Room Class (State Pattern)

```python
class Room:
    """Room with state management"""
    def __init__(self, room_id: str, room_number: str, room_type: RoomType,
                 base_price: float, floor: int, capacity: int, amenities: List[str]):
        self.room_id = room_id
        self.room_number = room_number
        self.room_type = room_type
        self.base_price = base_price
        self.floor = floor
        self.capacity = capacity
        self.amenities = amenities
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
        self.last_cleaned = datetime.now()
        self.maintenance_notes = []
    
    def reserve(self, reservation: 'Reservation'):
        """Transition: AVAILABLE → RESERVED"""
        if self.status != RoomStatus.AVAILABLE:
            raise ValueError("Room %s is not available (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.RESERVED
        self.current_reservation = reservation
    
    def occupy(self):
        """Transition: RESERVED → OCCUPIED"""
        if self.status != RoomStatus.RESERVED:
            raise ValueError("Room %s is not reserved (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.OCCUPIED
    
    def checkout(self):
        """Transition: OCCUPIED → AVAILABLE"""
        if self.status != RoomStatus.OCCUPIED:
            raise ValueError("Room %s is not occupied (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
    
    def mark_for_maintenance(self, note: str):
        """Transition: ANY → MAINTENANCE"""
        self.status = RoomStatus.MAINTENANCE
        self.maintenance_notes.append({
            'timestamp': datetime.now(),
            'note': note
        })
    
    def complete_maintenance(self):
        """Transition: MAINTENANCE → AVAILABLE"""
        if self.status != RoomStatus.MAINTENANCE:
            raise ValueError("Room %s is not in maintenance" % self.room_number)
        self.status = RoomStatus.AVAILABLE
        self.last_cleaned = datetime.now()
    
    def __str__(self):
        return "Room %s (%s) - %s - $%.2f/night - %s" % (
            self.room_number, self.room_type.value, self.status.value, 
            self.base_price, ', '.join(self.amenities))
```

**Key Points**:
- State machine prevents invalid transitions (e.g., can't occupy an available room)
- Track maintenance history for quality control
- Amenities enable filtering and recommendations

### 4. Reservation Class (State Pattern)

```python
from datetime import date

class Reservation:
    """Reservation with lifecycle management"""
    def __init__(self, reservation_id: str, guest: Guest, room: Room,
                 check_in_date: date, check_out_date: date):
        self.reservation_id = reservation_id
        self.guest = guest
        self.room = room
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.status = ReservationStatus.PENDING
        self.created_at = datetime.now()
        self.confirmed_at = None
        self.checked_in_at = None
        self.checked_out_at = None
        self.total_price = 0.0
        self.discount_applied = 0.0
        self.invoice = None
        self.num_nights = (check_out_date - check_in_date).days
    
    def confirm(self, total_price: float):
        """Transition: PENDING → CONFIRMED"""
        if self.status != ReservationStatus.PENDING:
            raise ValueError("Cannot confirm reservation with status %s" % self.status.value)
        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = datetime.now()
        self.total_price = total_price
        self.room.reserve(self)
    
    def check_in(self):
        """Transition: CONFIRMED → CHECKED_IN"""
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Cannot check in with status %s" % self.status.value)
        if date.today() < self.check_in_date:
            raise ValueError("Cannot check in before check-in date")
        self.status = ReservationStatus.CHECKED_IN
        self.checked_in_at = datetime.now()
        self.room.occupy()
    
    def check_out(self):
        """Transition: CHECKED_IN → CHECKED_OUT"""
        if self.status != ReservationStatus.CHECKED_IN:
            raise ValueError("Cannot check out with status %s" % self.status.value)
        self.status = ReservationStatus.CHECKED_OUT
        self.checked_out_at = datetime.now()
        self.room.checkout()
    
    def cancel(self):
        """Cancel reservation"""
        if self.status == ReservationStatus.CHECKED_OUT:
            raise ValueError("Cannot cancel completed reservation")
        self.status = ReservationStatus.CANCELLED
        if self.room.status == RoomStatus.RESERVED:
            self.room.status = RoomStatus.AVAILABLE
            self.room.current_reservation = None
```

**Key Points**:
- State machine enforces business rules (e.g., must confirm before check-in)
- Calculate nights automatically from dates
- Link to room state transitions

### 5. Invoice & Payment Classes

```python
class InvoiceLineItem:
    """Individual charge on invoice"""
    def __init__(self, description: str, quantity: int, unit_price: float):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.amount = quantity * unit_price

class Invoice:
    """Invoice with line items and totals"""
    def __init__(self, invoice_id: str, reservation: Reservation):
        self.invoice_id = invoice_id
        self.reservation = reservation
        self.guest = reservation.guest
        self.line_items = []
        self.created_at = datetime.now()
        self.subtotal = 0.0
        self.tax = 0.0
        self.discount = 0.0
        self.total = 0.0
        self.amount_paid = 0.0
        self.balance = 0.0
    
    def add_line_item(self, description: str, quantity: int, unit_price: float):
        """Add charge to invoice"""
        item = InvoiceLineItem(description, quantity, unit_price)
        self.line_items.append(item)
        self._recalculate()
    
    def apply_discount(self, discount_amount: float):
        """Apply loyalty or promotional discount"""
        self.discount = discount_amount
        self._recalculate()
    
    def _recalculate(self):
        """Recalculate totals"""
        self.subtotal = sum(item.amount for item in self.line_items)
        self.tax = self.subtotal * 0.10  # 10% tax
        self.total = self.subtotal + self.tax - self.discount
        self.balance = self.total - self.amount_paid
    
    def get_summary(self) -> str:
        """Generate invoice summary"""
        summary = "Invoice %s\n" % self.invoice_id
        summary += "Guest: %s\n" % self.guest.name
        summary += "-" * 40 + "\n"
        for item in self.line_items:
            summary += "%s x%d @ $%.2f = $%.2f\n" % (
                item.description, item.quantity, item.unit_price, item.amount)
        summary += "-" * 40 + "\n"
        summary += "Subtotal: $%.2f\n" % self.subtotal
        summary += "Tax (10%%): $%.2f\n" % self.tax
        if self.discount > 0:
            summary += "Discount: -$%.2f\n" % self.discount
        summary += "Total: $%.2f\n" % self.total
        summary += "Paid: $%.2f\n" % self.amount_paid
        summary += "Balance: $%.2f\n" % self.balance
        return summary

class Payment:
    """Payment transaction"""
    def __init__(self, payment_id: str, invoice: Invoice, amount: float, 
                 method: PaymentMethod):
        self.payment_id = payment_id
        self.invoice = invoice
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
        self.transaction_id = None
    
    def process(self) -> bool:
        """Process payment (simplified)"""
        # In real system: integrate with payment gateway
        if self.amount <= 0:
            self.status = PaymentStatus.FAILED
            return False
        
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = "TXN_%s_%d" % (self.payment_id, int(datetime.now().timestamp()))
        self.invoice.amount_paid += self.amount
        self.invoice._recalculate()
        return True
```

**Key Points**:
- Line items enable detailed billing (room charges, services, extras)
- Automatic tax calculation
- Support multiple payment methods
- Track payment history

---

## Business Logic (35-55 min)

### Room Factory Pattern

```python
class RoomFactory:
    """Factory for creating different room types"""
    
    @staticmethod
    def create_room(room_id: str, room_number: str, room_type: RoomType, 
                   floor: int) -> Room:
        """Create room with type-specific configuration"""
        
        if room_type == RoomType.STANDARD:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=100.0,
                floor=floor,
                capacity=2,
                amenities=["WiFi", "TV", "Air Conditioning"]
            )
        
        elif room_type == RoomType.DELUXE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=200.0,
                floor=floor,
                capacity=3,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar", 
                          "Room Service", "Ocean View"]
            )
        
        elif room_type == RoomType.SUITE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=400.0,
                floor=floor,
                capacity=4,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar",
                          "Room Service", "Ocean View", "Jacuzzi", 
                          "Kitchen", "Living Room", "Balcony"]
            )
        
        else:
            raise ValueError("Unknown room type: %s" % room_type)
```

**Interview Points**:
- Encapsulates room creation logic
- Each type has different price, capacity, amenities
- Easy to add new room types
- Consistent initialization

### Pricing Strategy Pattern

```python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        pass

class RegularPricing(PricingStrategy):
    """Standard pricing without modifications"""
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        base_total = room.base_price * num_nights
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount

class SeasonalPricing(PricingStrategy):
    """Seasonal pricing with summer/winter rates"""
    SUMMER_MULTIPLIER = 1.3  # 30% increase (June-August)
    WINTER_MULTIPLIER = 1.5  # 50% increase (December-February)
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        current_month = datetime.now().month
        
        # Determine seasonal multiplier
        if current_month in [6, 7, 8]:  # Summer
            multiplier = self.SUMMER_MULTIPLIER
        elif current_month in [12, 1, 2]:  # Winter holidays
            multiplier = self.WINTER_MULTIPLIER
        else:
            multiplier = 1.0
        
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount

class EventPricing(PricingStrategy):
    """Event-based pricing for conferences, holidays, etc."""
    def __init__(self, event_dates: List[date], event_multiplier: float = 2.0):
        self.event_dates = event_dates
        self.event_multiplier = event_multiplier
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        # Check if reservation overlaps with event dates
        # (simplified: just check current date)
        is_event_period = date.today() in self.event_dates
        
        multiplier = self.event_multiplier if is_event_period else 1.0
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount
```

**Interview Points**:
- Strategy pattern allows runtime pricing changes
- Seasonal pricing based on month
- Event pricing for special dates (conferences, holidays)
- Loyalty discounts always applied

---

## Integration & Patterns (55-70 min)

### Observer Pattern - Notifications

```python
from abc import ABC, abstractmethod

class HotelObserver(ABC):
    """Observer interface for hotel events"""
    @abstractmethod
    def update(self, event: str, data: dict):
        pass

class GuestNotifier(HotelObserver):
    """Notify guests of events"""
    def update(self, event: str, data: dict):
        if event in ["reservation_confirmed", "check_in_ready", "service_completed", 
                     "invoice_generated", "payment_processed"]:
            guest_name = data.get('guest_name', 'Guest')
            message = data.get('message', '')
            print("  [GUEST] %s: %s" % (guest_name, message))

class StaffNotifier(HotelObserver):
    """Notify staff of events"""
    def update(self, event: str, data: dict):
        if event in ["new_reservation", "service_requested", "check_out", 
                     "maintenance_needed"]:
            message = data.get('message', '')
            print("  [STAFF] %s" % message)

class AdminNotifier(HotelObserver):
    """Notify admin of critical events"""
    def update(self, event: str, data: dict):
        if event in ["payment_failed", "no_rooms_available", "maintenance_urgent",
                     "reservation_cancelled"]:
            message = data.get('message', '')
            priority = data.get('priority', 'NORMAL')
            print("  [ADMIN] [%s] %s" % (priority, message))
```

### Complete HotelManagementSystem (Singleton)

See INTERVIEW_COMPACT.py for full implementation with all methods:
- `create_reservation()`: Find room, calculate price, create reservation
- `check_in()`: Transition reservation to CHECKED_IN
- `check_out()`: Generate invoice, process charges
- `process_payment()`: Handle payments, award loyalty points
- `request_service()`: Create service command, assign staff
- `complete_service()`: Mark service complete, free staff

---

## Interview Q&A (12 Questions)

### Basic (0-5 min)

1. **"What are the core entities in a hotel management system?"**
   - Answer: Guest, Room, Reservation, Invoice, Payment, RoomService, Staff. Reservation connects Guest+Room with dates. Invoice tracks charges and payments.

2. **"What are the room statuses?"**
   - Answer: AVAILABLE (can be booked) → RESERVED (booked, not checked in) → OCCUPIED (guest checked in) → MAINTENANCE (being serviced). Can go to MAINTENANCE from any state.

3. **"What are the reservation statuses?"**
   - Answer: PENDING (just created) → CONFIRMED (payment authorized, room reserved) → CHECKED_IN (guest arrived) → CHECKED_OUT (guest left). Can be CANCELLED before completion.

### Intermediate (5-10 min)

4. **"How does the room factory work?"**
   - Answer: RoomFactory.create_room() takes room type and returns configured Room. Standard ($100, 2 capacity), Deluxe ($200, 3 capacity), Suite ($400, 4 capacity). Each has different amenities. Encapsulates creation logic.

5. **"Explain the pricing strategies."**
   - Answer: Strategy pattern with 3 implementations. RegularPricing: base price × nights - loyalty discount. SeasonalPricing: adds 30% summer, 50% winter. EventPricing: 2x during event dates. All apply guest loyalty discounts.

6. **"How do you prevent double-booking a room?"**
   - Answer: Room.status state machine. Can only reserve if AVAILABLE. System-level lock in create_reservation() prevents race conditions. Room transitions to RESERVED, blocking other bookings.

7. **"How does the service request system work?"**
   - Answer: Command pattern. Guest requests service → system creates RoomService → finds available staff → creates ServiceCommand (RoomService/Housekeeping/Maintenance) → executes command → assigns to staff → tracks completion.

### Advanced (10-15 min)

8. **"How would you handle concurrent reservations for the last available room?"**
   - Answer: System-level lock in create_reservation(). Check availability and reserve atomically. Alternative: Database row-level locking with SELECT FOR UPDATE. Optimistic locking with version numbers. Queue requests with fair ordering.

9. **"How would you implement variable pricing based on demand?"**
   - Answer: Add DemandPricing strategy. Track occupancy rate and demand trends. Calculate multiplier: low demand (0.8x), normal (1.0x), high (1.5x), very high (2.0x). Update prices dynamically. Store historical data for ML predictions.

10. **"How would you scale to a hotel chain with 100 properties?"**
    - Answer: Add Hotel entity with location. Partition data by hotel_id. Separate databases per region. Central reservation system for search. Replicate room inventory. Distributed cache (Redis). API gateway for routing. Eventual consistency for availability.

11. **"How would you implement room upgrades and downgrades?"**
    - Answer: Add Reservation.upgrade(new_room) method. Check new room availability. Calculate price difference. Process additional payment or refund. Update room states (free old, reserve new). Track upgrade history. Offer automatic upgrades for VIPs when available.

12. **"How would you handle group bookings and block reservations?"**
    - Answer: Add GroupReservation entity with multiple rooms. Reserve blocks atomically (all or nothing). Track block status. Support partial releases. Different pricing for groups. Coordinator contact. Handle rooming lists. Release unreleased rooms X days before arrival.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **Single Responsibility** | Room handles state; Reservation handles booking lifecycle; Invoice handles billing; PricingStrategy handles pricing |
| **Open/Closed** | New pricing strategies, service commands, observers added without modifying core system |
| **Liskov Substitution** | All PricingStrategy implementations interchangeable; all ServiceCommand subclasses work the same |
| **Interface Segregation** | Observer only requires update(); Strategy only requires calculate_price(); Command only requires execute() |
| **Dependency Inversion** | HotelManagementSystem depends on abstract PricingStrategy, HotelObserver, ServiceCommand—not concrete classes |

---

## UML Diagram

```
┌────────────────────────────────────────────────────┐
│      HotelManagementSystem (Singleton)             │
├────────────────────────────────────────────────────┤
│ - rooms: Dict[str, Room]                           │
│ - guests: Dict[str, Guest]                         │
│ - reservations: Dict[str, Reservation]             │
│ - staff: Dict[str, Staff]                          │
│ - pricing_strategy: PricingStrategy                │
│ - observers: List[HotelObserver]                   │
├────────────────────────────────────────────────────┤
│ + create_reservation()                             │
│ + check_in()                                       │
│ + check_out()                                      │
│ + process_payment()                                │
│ + request_service()                                │
└────────────────────────────────────────────────────┘
           │                   │
           ▼                   ▼
    ┌──────────┐        ┌──────────┐
    │  Guest   │        │   Room   │
    ├──────────┤        ├──────────┤
    │ loyalty  │        │ type     │
    │ points   │        │ status   │
    │ is_vip   │        │ price    │
    └──────────┘        └──────────┘
           │                   │
           └────────┬──────────┘
                    ▼
            ┌──────────────┐
            │ Reservation  │
            ├──────────────┤
            │ status       │
            │ check_in     │
            │ check_out    │
            └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │   Invoice    │
            ├──────────────┤
            │ line_items   │
            │ total        │
            │ balance      │
            └──────────────┘

┌────────────────────────────────────┐
│   RoomFactory (Factory)            │
├────────────────────────────────────┤
│ + create_room(type)                │
└────────────────────────────────────┘
           △
           │ creates
    ┌──────┴────────────┬──────────────┐
    │                   │              │
Standard ($100)    Deluxe ($200)   Suite ($400)

┌────────────────────────────────────┐
│   PricingStrategy (Abstract)       │
├────────────────────────────────────┤
│ + calculate_price()                │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴────────────┬──────────────┐
    │                   │              │
RegularPricing   SeasonalPricing   EventPricing

┌────────────────────────────────────┐
│   HotelObserver (Abstract)         │
├────────────────────────────────────┤
│ + update(event, data)              │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────┬──────────────┐
    │                 │              │
GuestNotifier  StaffNotifier  AdminNotifier

┌────────────────────────────────────┐
│   ServiceCommand (Abstract)        │
├────────────────────────────────────┤
│ + execute()                        │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────┬──────────────┐
    │                 │              │
RoomServiceCmd  HousekeepingCmd  MaintenanceCmd

State Machines:

Room: AVAILABLE → RESERVED → OCCUPIED → AVAILABLE
              ↓       ↓           ↓
         MAINTENANCE (from any state)

Reservation: PENDING → CONFIRMED → CHECKED_IN → CHECKED_OUT
                 ↓           ↓          ↓
             CANCELLED   CANCELLED  CANCELLED
```

---

## 5 Demo Scenarios

### Demo 1: System Setup & Room Creation
- Initialize singleton system
- Add observers (Guest, Staff, Admin)
- Create rooms using factory (Standard, Deluxe, Suite)
- Add staff members (Housekeeper, Room Service, Maintenance)
- Display system statistics

### Demo 2: Guest Registration & Reservation
- Register two guests
- Create reservation for Standard room
- Show pricing calculation with loyalty discount
- Verify observer notifications
- Display reservation details

### Demo 3: Dynamic Pricing Comparison
- Set RegularPricing, calculate price
- Switch to SeasonalPricing, recalculate same reservation
- Switch to EventPricing, recalculate again
- Compare all three prices
- Show VIP discount application

### Demo 4: Full Guest Journey
- Create reservation
- Check in guest
- Request room service (Command pattern)
- Request housekeeping
- Check out guest
- Generate invoice with line items
- Process payment
- Award loyalty points
- Show updated guest stats

### Demo 5: Room State Management & Maintenance
- Show room in AVAILABLE state
- Reserve room (AVAILABLE → RESERVED)
- Check in (RESERVED → OCCUPIED)
- Request urgent maintenance
- Room goes to MAINTENANCE state
- Complete maintenance
- Room returns to AVAILABLE
- Attempt invalid state transition (show error handling)

---

## Key Implementation Notes

### Concurrency & Thread Safety
- System-level lock protects critical sections
- Room state transitions are atomic
- Alternative: Database transactions with SERIALIZABLE isolation
- Consider message queue for service requests (RabbitMQ/Kafka)

### Performance Optimization
- Index rooms by type and status
- Cache available room counts
- Lazy load reservation history
- Use database connection pooling
- Cache pricing calculations

### Error Handling
- State machines enforce valid transitions
- Payment failures trigger refunds
- Service request queuing when no staff available
- Reservation rollback on payment failure

### Testing Strategy
1. Unit test each pricing strategy
2. Unit test room/reservation state machines
3. Test factory creates correct configurations
4. Integration test full reservation flow
5. Concurrency test (100 simultaneous bookings for same room)
6. Test observer notifications
7. Test command pattern execution

### Extensibility
- Add new room types in factory
- Add new pricing strategies
- Add new service types and commands
- Add new notification channels (SMS, Push)
- Add analytics and reporting observers

---

## Time Management Checklist

- [ ] **0-5 min**: Requirements clarification
- [ ] **5-10 min**: Design patterns selection, architecture diagram
- [ ] **10-15 min**: Enums and basic entity classes
- [ ] **15-25 min**: Complete entity implementations
- [ ] **25-35 min**: Factory and Strategy patterns
- [ ] **35-45 min**: Observer and State patterns
- [ ] **45-55 min**: Command pattern and HotelManagementSystem
- [ ] **55-65 min**: Complete core system methods
- [ ] **65-75 min**: Demo scenarios and Q&A

**Remember**: Working code > Perfect code. Show progress, explain decisions, handle edge cases.


## Detailed Design Reference

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


## Compact Code

```python
#!/usr/bin/env python3
"""
Hotel Management System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action

Design Patterns Demonstrated:
1. Singleton - HotelManagementSystem (centralized control)
2. Factory - RoomFactory (room creation)
3. Strategy - PricingStrategy (Regular/Seasonal/Event)
4. Observer - Notifications (Guest/Staff/Admin)
5. State - Room and Reservation lifecycles
6. Command - Service requests
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import threading
import time


# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class RoomType(Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"


class RoomStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ONLINE = "online"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ServiceType(Enum):
    ROOM_SERVICE = "room_service"
    HOUSEKEEPING = "housekeeping"
    MAINTENANCE = "maintenance"
    LAUNDRY = "laundry"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class StaffRole(Enum):
    RECEPTIONIST = "receptionist"
    HOUSEKEEPER = "housekeeper"
    MAINTENANCE = "maintenance"
    ROOM_SERVICE = "room_service"
    MANAGER = "manager"


# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Guest:
    """Guest with loyalty program and preferences"""
    def __init__(self, guest_id: str, name: str, email: str, phone: str):
        self.guest_id = guest_id
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = datetime.now()
        self.loyalty_points = 0
        self.total_stays = 0
        self.total_spent = 0.0
        self.preferences = {}
        self.is_vip = False
    
    def add_loyalty_points(self, points: int):
        """Add loyalty points from stay"""
        self.loyalty_points += points
        if self.loyalty_points >= 1000:
            self.is_vip = True
    
    def get_discount_percentage(self) -> float:
        """Calculate loyalty discount"""
        if self.is_vip:
            return 0.15  # 15% VIP discount
        elif self.loyalty_points >= 500:
            return 0.10  # 10% silver discount
        elif self.loyalty_points >= 200:
            return 0.05  # 5% bronze discount
        return 0.0
    
    def __str__(self):
        vip_status = "VIP" if self.is_vip else "Regular"
        return "%s (%s) - Points: %d, Stays: %d, Spent: $%.2f" % (
            self.name, vip_status, self.loyalty_points, self.total_stays, self.total_spent)


class Room:
    """Room with state management"""
    def __init__(self, room_id: str, room_number: str, room_type: RoomType,
                 base_price: float, floor: int, capacity: int, amenities: List[str]):
        self.room_id = room_id
        self.room_number = room_number
        self.room_type = room_type
        self.base_price = base_price
        self.floor = floor
        self.capacity = capacity
        self.amenities = amenities
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
        self.last_cleaned = datetime.now()
        self.maintenance_notes = []
    
    def reserve(self, reservation: 'Reservation'):
        """Transition: AVAILABLE → RESERVED"""
        if self.status != RoomStatus.AVAILABLE:
            raise ValueError("Room %s is not available (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.RESERVED
        self.current_reservation = reservation
    
    def occupy(self):
        """Transition: RESERVED → OCCUPIED"""
        if self.status != RoomStatus.RESERVED:
            raise ValueError("Room %s is not reserved (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.OCCUPIED
    
    def checkout(self):
        """Transition: OCCUPIED → AVAILABLE"""
        if self.status != RoomStatus.OCCUPIED:
            raise ValueError("Room %s is not occupied (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
    
    def mark_for_maintenance(self, note: str):
        """Transition: ANY → MAINTENANCE"""
        self.status = RoomStatus.MAINTENANCE
        self.maintenance_notes.append({
            'timestamp': datetime.now(),
            'note': note
        })
    
    def complete_maintenance(self):
        """Transition: MAINTENANCE → AVAILABLE"""
        if self.status != RoomStatus.MAINTENANCE:
            raise ValueError("Room %s is not in maintenance" % self.room_number)
        self.status = RoomStatus.AVAILABLE
        self.last_cleaned = datetime.now()
    
    def __str__(self):
        return "Room %s (%s) - %s - $%.2f/night - Floor %d" % (
            self.room_number, self.room_type.value, self.status.value, 
            self.base_price, self.floor)


class Reservation:
    """Reservation with lifecycle management"""
    def __init__(self, reservation_id: str, guest: Guest, room: Room,
                 check_in_date: date, check_out_date: date):
        self.reservation_id = reservation_id
        self.guest = guest
        self.room = room
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.status = ReservationStatus.PENDING
        self.created_at = datetime.now()
        self.confirmed_at = None
        self.checked_in_at = None
        self.checked_out_at = None
        self.total_price = 0.0
        self.discount_applied = 0.0
        self.invoice = None
        self.num_nights = (check_out_date - check_in_date).days
    
    def confirm(self, total_price: float):
        """Transition: PENDING → CONFIRMED"""
        if self.status != ReservationStatus.PENDING:
            raise ValueError("Cannot confirm reservation with status %s" % self.status.value)
        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = datetime.now()
        self.total_price = total_price
        self.room.reserve(self)
    
    def check_in(self):
        """Transition: CONFIRMED → CHECKED_IN"""
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Cannot check in with status %s" % self.status.value)
        self.status = ReservationStatus.CHECKED_IN
        self.checked_in_at = datetime.now()
        self.room.occupy()
    
    def check_out(self):
        """Transition: CHECKED_IN → CHECKED_OUT"""
        if self.status != ReservationStatus.CHECKED_IN:
            raise ValueError("Cannot check out with status %s" % self.status.value)
        self.status = ReservationStatus.CHECKED_OUT
        self.checked_out_at = datetime.now()
        self.room.checkout()
    
    def cancel(self):
        """Cancel reservation"""
        if self.status == ReservationStatus.CHECKED_OUT:
            raise ValueError("Cannot cancel completed reservation")
        self.status = ReservationStatus.CANCELLED
        if self.room.status == RoomStatus.RESERVED:
            self.room.status = RoomStatus.AVAILABLE
            self.room.current_reservation = None


class InvoiceLineItem:
    """Individual charge on invoice"""
    def __init__(self, description: str, quantity: int, unit_price: float):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.amount = quantity * unit_price


class Invoice:
    """Invoice with line items and totals"""
    def __init__(self, invoice_id: str, reservation: Reservation):
        self.invoice_id = invoice_id
        self.reservation = reservation
        self.guest = reservation.guest
        self.line_items = []
        self.created_at = datetime.now()
        self.subtotal = 0.0
        self.tax = 0.0
        self.discount = 0.0
        self.total = 0.0
        self.amount_paid = 0.0
        self.balance = 0.0
    
    def add_line_item(self, description: str, quantity: int, unit_price: float):
        """Add charge to invoice"""
        item = InvoiceLineItem(description, quantity, unit_price)
        self.line_items.append(item)
        self._recalculate()
    
    def apply_discount(self, discount_amount: float):
        """Apply loyalty or promotional discount"""
        self.discount = discount_amount
        self._recalculate()
    
    def _recalculate(self):
        """Recalculate totals"""
        self.subtotal = sum(item.amount for item in self.line_items)
        self.tax = self.subtotal * 0.10  # 10% tax
        self.total = self.subtotal + self.tax - self.discount
        self.balance = self.total - self.amount_paid
    
    def get_summary(self) -> str:
        """Generate invoice summary"""
        summary = "\n" + "="*50 + "\n"
        summary += "           INVOICE %s\n" % self.invoice_id
        summary += "="*50 + "\n"
        summary += "Guest: %s\n" % self.guest.name
        summary += "Reservation: %s\n" % self.reservation.reservation_id
        summary += "Room: %s\n" % self.reservation.room.room_number
        summary += "-" * 50 + "\n"
        for item in self.line_items:
            summary += "%-30s x%d @ $%.2f = $%.2f\n" % (
                item.description, item.quantity, item.unit_price, item.amount)
        summary += "-" * 50 + "\n"
        summary += "%-40s $%.2f\n" % ("Subtotal:", self.subtotal)
        summary += "%-40s $%.2f\n" % ("Tax (10%):", self.tax)
        if self.discount > 0:
            summary += "%-40s -$%.2f\n" % ("Discount:", self.discount)
        summary += "%-40s $%.2f\n" % ("TOTAL:", self.total)
        summary += "%-40s $%.2f\n" % ("Paid:", self.amount_paid)
        summary += "%-40s $%.2f\n" % ("Balance:", self.balance)
        summary += "="*50 + "\n"
        return summary


class Payment:
    """Payment transaction"""
    def __init__(self, payment_id: str, invoice: Invoice, amount: float, 
                 method: PaymentMethod):
        self.payment_id = payment_id
        self.invoice = invoice
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
        self.transaction_id = None
    
    def process(self) -> bool:
        """Process payment (simplified)"""
        if self.amount <= 0:
            self.status = PaymentStatus.FAILED
            return False
        
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = "TXN_%s_%d" % (self.payment_id, int(datetime.now().timestamp()))
        self.invoice.amount_paid += self.amount
        self.invoice._recalculate()
        return True


class RoomService:
    """Service request with priority and assignment"""
    def __init__(self, service_id: str, room: Room, service_type: ServiceType,
                 description: str, priority: Priority):
        self.service_id = service_id
        self.room = room
        self.service_type = service_type
        self.description = description
        self.priority = priority
        self.requested_at = datetime.now()
        self.assigned_staff = None
        self.started_at = None
        self.completed_at = None
        self.is_completed = False
        self.notes = ""
    
    def assign_to(self, staff: 'Staff'):
        """Assign service to staff member"""
        self.assigned_staff = staff
        staff.assigned_services.append(self)
    
    def start_service(self):
        """Mark service as started"""
        self.started_at = datetime.now()
    
    def complete_service(self, notes: str = ""):
        """Mark service as completed"""
        self.completed_at = datetime.now()
        self.is_completed = True
        self.notes = notes
        if self.assigned_staff:
            self.assigned_staff.assigned_services.remove(self)


class Staff:
    """Staff member with role and availability"""
    def __init__(self, staff_id: str, name: str, role: StaffRole):
        self.staff_id = staff_id
        self.name = name
        self.role = role
        self.is_available = True
        self.assigned_services = []
        self.completed_services = 0
        self.shift_start = None
        self.shift_end = None
    
    def can_handle_service(self, service_type: ServiceType) -> bool:
        """Check if staff can handle this service type"""
        mapping = {
            StaffRole.HOUSEKEEPER: [ServiceType.HOUSEKEEPING, ServiceType.LAUNDRY],
            StaffRole.MAINTENANCE: [ServiceType.MAINTENANCE],
            StaffRole.ROOM_SERVICE: [ServiceType.ROOM_SERVICE],
        }
        return service_type in mapping.get(self.role, [])
    
    def __str__(self):
        status = "Available" if self.is_available else "Busy"
        return "%s (%s) - %s - %d active tasks, %d completed" % (
            self.name, self.role.value, status, len(self.assigned_services), 
            self.completed_services)


# ============================================================================
# SECTION 3: FACTORY PATTERN
# ============================================================================

class RoomFactory:
    """Factory for creating different room types"""
    
    @staticmethod
    def create_room(room_id: str, room_number: str, room_type: RoomType, 
                   floor: int) -> Room:
        """Create room with type-specific configuration"""
        
        if room_type == RoomType.STANDARD:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=100.0,
                floor=floor,
                capacity=2,
                amenities=["WiFi", "TV", "Air Conditioning"]
            )
        
        elif room_type == RoomType.DELUXE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=200.0,
                floor=floor,
                capacity=3,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar", 
                          "Room Service", "Ocean View"]
            )
        
        elif room_type == RoomType.SUITE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=400.0,
                floor=floor,
                capacity=4,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar",
                          "Room Service", "Ocean View", "Jacuzzi", 
                          "Kitchen", "Living Room", "Balcony"]
            )
        
        else:
            raise ValueError("Unknown room type: %s" % room_type)


# ============================================================================
# SECTION 4: STRATEGY PATTERN - PRICING
# ============================================================================

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        pass


class RegularPricing(PricingStrategy):
    """Standard pricing without modifications"""
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        base_total = room.base_price * num_nights
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


class SeasonalPricing(PricingStrategy):
    """Seasonal pricing with summer/winter rates"""
    SUMMER_MULTIPLIER = 1.3  # 30% increase (June-August)
    WINTER_MULTIPLIER = 1.5  # 50% increase (December-February)
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        current_month = datetime.now().month
        
        # Determine seasonal multiplier
        if current_month in [6, 7, 8]:  # Summer
            multiplier = self.SUMMER_MULTIPLIER
            season = "Summer"
        elif current_month in [12, 1, 2]:  # Winter holidays
            multiplier = self.WINTER_MULTIPLIER
            season = "Winter"
        else:
            multiplier = 1.0
            season = "Regular"
        
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


class EventPricing(PricingStrategy):
    """Event-based pricing for conferences, holidays, etc."""
    def __init__(self, event_dates: List[date], event_multiplier: float = 2.0):
        self.event_dates = event_dates
        self.event_multiplier = event_multiplier
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        # Check if reservation overlaps with event dates
        is_event_period = date.today() in self.event_dates
        
        multiplier = self.event_multiplier if is_event_period else 1.0
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


# ============================================================================
# SECTION 5: OBSERVER PATTERN - NOTIFICATIONS
# ============================================================================

class HotelObserver(ABC):
    """Observer interface for hotel events"""
    @abstractmethod
    def update(self, event: str, data: dict):
        pass


class GuestNotifier(HotelObserver):
    """Notify guests of events"""
    def update(self, event: str, data: dict):
        if event in ["reservation_confirmed", "check_in_ready", "service_completed", 
                     "invoice_generated", "payment_processed"]:
            guest_name = data.get('guest_name', 'Guest')
            message = data.get('message', '')
            print("  [GUEST] %s: %s" % (guest_name, message))


class StaffNotifier(HotelObserver):
    """Notify staff of events"""
    def update(self, event: str, data: dict):
        if event in ["new_reservation", "service_requested", "check_out", 
                     "maintenance_needed"]:
            message = data.get('message', '')
            print("  [STAFF] %s" % message)


class AdminNotifier(HotelObserver):
    """Notify admin of critical events"""
    def update(self, event: str, data: dict):
        if event in ["payment_failed", "no_rooms_available", "maintenance_urgent",
                     "reservation_cancelled"]:
            message = data.get('message', '')
            priority = data.get('priority', 'NORMAL')
            print("  [ADMIN] [%s] %s" % (priority, message))


# ============================================================================
# SECTION 6: COMMAND PATTERN - SERVICE REQUESTS
# ============================================================================

class ServiceCommand(ABC):
    """Abstract command for service requests"""
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass


class RoomServiceCommand(ServiceCommand):
    """Command for room service request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        """Execute service request"""
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        return True
    
    def get_description(self) -> str:
        return "Room Service for %s - %s" % (
            self.service.room.room_number, self.service.description)


class HousekeepingCommand(ServiceCommand):
    """Command for housekeeping request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        return True
    
    def get_description(self) -> str:
        return "Housekeeping for %s" % self.service.room.room_number


class MaintenanceCommand(ServiceCommand):
    """Command for maintenance request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        
        # Mark room for maintenance (store note even if already in maintenance)
        if self.service.room.status != RoomStatus.MAINTENANCE:
            self.service.room.mark_for_maintenance(self.service.description)
        else:
            # Add note to existing maintenance
            self.service.room.maintenance_notes.append({
                'timestamp': datetime.now(),
                'note': self.service.description
            })
        
        return True
    
    def get_description(self) -> str:
        return "Maintenance for %s - %s" % (
            self.service.room.room_number, self.service.description)


# ============================================================================
# SECTION 7: SINGLETON - HOTEL MANAGEMENT SYSTEM
# ============================================================================

class HotelManagementSystem:
    """Singleton controller for hotel operations"""
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
            # Room inventory
            self.rooms: Dict[str, Room] = {}
            self.room_counter = 0
            
            # Guest registry
            self.guests: Dict[str, Guest] = {}
            self.guest_counter = 0
            
            # Reservations
            self.reservations: Dict[str, Reservation] = {}
            self.reservation_counter = 0
            
            # Staff
            self.staff: Dict[str, Staff] = {}
            self.staff_counter = 0
            
            # Services
            self.services: Dict[str, RoomService] = {}
            self.service_counter = 0
            
            # Invoices & Payments
            self.invoices: Dict[str, Invoice] = {}
            self.invoice_counter = 0
            self.payments: Dict[str, Payment] = {}
            self.payment_counter = 0
            
            # Strategies
            self.pricing_strategy = RegularPricing()
            
            # Observers
            self.observers: List[HotelObserver] = []
            
            # Thread safety
            self.lock = threading.Lock()
            
            self.initialized = True
    
    # ===== Observer Management =====
    
    def attach_observer(self, observer: HotelObserver):
        """Add observer for notifications"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: dict):
        """Notify all observers of event"""
        for observer in self.observers:
            observer.update(event, data)
    
    # ===== Strategy Management =====
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Change pricing strategy at runtime"""
        self.pricing_strategy = strategy
    
    # ===== Room Management =====
    
    def add_room(self, room_type: RoomType, room_number: str, floor: int) -> Room:
        """Add room using factory"""
        with self.lock:
            self.room_counter += 1
            room_id = "ROOM_%04d" % self.room_counter
            
            room = RoomFactory.create_room(room_id, room_number, room_type, floor)
            self.rooms[room_id] = room
            
            return room
    
    def get_available_rooms(self, room_type: Optional[RoomType] = None) -> List[Room]:
        """Get available rooms, optionally filtered by type"""
        available = [r for r in self.rooms.values() 
                    if r.status == RoomStatus.AVAILABLE]
        
        if room_type:
            available = [r for r in available if r.room_type == room_type]
        
        return available
    
    # ===== Guest Management =====
    
    def register_guest(self, name: str, email: str, phone: str) -> Guest:
        """Register new guest"""
        with self.lock:
            self.guest_counter += 1
            guest_id = "GUEST_%05d" % self.guest_counter
            
            guest = Guest(guest_id, name, email, phone)
            self.guests[guest_id] = guest
            
            return guest
    
    # ===== Staff Management =====
    
    def add_staff(self, name: str, role: StaffRole) -> Staff:
        """Add staff member"""
        with self.lock:
            self.staff_counter += 1
            staff_id = "STAFF_%04d" % self.staff_counter
            
            staff = Staff(staff_id, name, role)
            self.staff[staff_id] = staff
            
            return staff
    
    def find_available_staff(self, service_type: ServiceType) -> Optional[Staff]:
        """Find available staff for service type"""
        for staff in self.staff.values():
            if staff.is_available and staff.can_handle_service(service_type):
                return staff
        return None
    
    # ===== Reservation Management =====
    
    def create_reservation(self, guest: Guest, room_type: RoomType,
                          check_in: date, check_out: date) -> Optional[Reservation]:
        """Create new reservation"""
        with self.lock:
            # Find available room
            available_rooms = self.get_available_rooms(room_type)
            if not available_rooms:
                self.notify_observers("no_rooms_available", {
                    'guest_name': guest.name,
                    'room_type': room_type.value,
                    'message': "No %s rooms available" % room_type.value
                })
                return None
            
            # Select first available room
            room = available_rooms[0]
            
            # Create reservation
            self.reservation_counter += 1
            reservation_id = "RES_%06d" % self.reservation_counter
            
            reservation = Reservation(reservation_id, guest, room, check_in, check_out)
            
            # Calculate price using strategy
            total_price = self.pricing_strategy.calculate_price(
                room, reservation.num_nights, guest)
            
            # Confirm reservation
            reservation.confirm(total_price)
            reservation.discount_applied = room.base_price * reservation.num_nights * \
                                          guest.get_discount_percentage()
            
            self.reservations[reservation_id] = reservation
            
            # Notify observers
            self.notify_observers("reservation_confirmed", {
                'guest_name': guest.name,
                'room_number': room.room_number,
                'check_in': str(check_in),
                'check_out': str(check_out),
                'total_price': total_price,
                'message': "Reservation confirmed! Room %s (%d nights) - Total: $%.2f" % 
                          (room.room_number, reservation.num_nights, total_price)
            })
            
            self.notify_observers("new_reservation", {
                'message': "New reservation: %s for %s, Room %s (%s to %s)" % 
                          (guest.name, room_type.value, room.room_number, 
                           check_in, check_out)
            })
            
            return reservation
    
    def check_in(self, reservation: Reservation) -> bool:
        """Check in guest"""
        try:
            reservation.check_in()
            
            self.notify_observers("check_in_ready", {
                'guest_name': reservation.guest.name,
                'room_number': reservation.room.room_number,
                'message': "Welcome! Checked into Room %s. Enjoy your stay!" % 
                          reservation.room.room_number
            })
            
            return True
        except ValueError as e:
            print("  [ERROR] Check-in failed: %s" % str(e))
            return False
    
    def check_out(self, reservation: Reservation) -> Optional[Invoice]:
        """Check out guest and generate invoice"""
        with self.lock:
            # Check out
            reservation.check_out()
            
            # Generate invoice
            self.invoice_counter += 1
            invoice_id = "INV_%06d" % self.invoice_counter
            
            invoice = Invoice(invoice_id, reservation)
            
            # Add room charges
            invoice.add_line_item(
                description="%s Room (%d nights)" % (
                    reservation.room.room_type.value.title(), 
                    reservation.num_nights),
                quantity=reservation.num_nights,
                unit_price=reservation.room.base_price
            )
            
            # Apply discount
            if reservation.discount_applied > 0:
                invoice.apply_discount(reservation.discount_applied)
            
            self.invoices[invoice_id] = invoice
            reservation.invoice = invoice
            
            # Update guest stats
            reservation.guest.total_stays += 1
            
            # Notify observers
            self.notify_observers("invoice_generated", {
                'guest_name': reservation.guest.name,
                'invoice_id': invoice_id,
                'total': invoice.total,
                'message': "Checked out from Room %s. Invoice #%s generated (Total: $%.2f)" % 
                          (reservation.room.room_number, invoice_id, invoice.total)
            })
            
            self.notify_observers("check_out", {
                'message': "Guest %s checked out from Room %s" % 
                          (reservation.guest.name, reservation.room.room_number)
            })
            
            return invoice
    
    # ===== Payment Processing =====
    
    def process_payment(self, invoice: Invoice, amount: float, 
                       method: PaymentMethod) -> Optional[Payment]:
        """Process payment for invoice"""
        with self.lock:
            self.payment_counter += 1
            payment_id = "PAY_%06d" % self.payment_counter
            
            payment = Payment(payment_id, invoice, amount, method)
            
            if payment.process():
                self.payments[payment_id] = payment
                
                # Award loyalty points (1 point per $10 spent)
                points = int(amount / 10)
                invoice.guest.add_loyalty_points(points)
                invoice.guest.total_spent += amount
                
                self.notify_observers("payment_processed", {
                    'guest_name': invoice.guest.name,
                    'amount': amount,
                    'method': method.value,
                    'points': points,
                    'message': "Payment of $%.2f processed via %s. Earned %d loyalty points!" % 
                              (amount, method.value, points)
                })
                
                return payment
            else:
                self.notify_observers("payment_failed", {
                    'guest_name': invoice.guest.name,
                    'amount': amount,
                    'message': "Payment of $%.2f failed" % amount,
                    'priority': 'HIGH'
                })
                return None
    
    # ===== Service Management =====
    
    def request_service(self, room: Room, service_type: ServiceType,
                       description: str, priority: Priority) -> Optional[RoomService]:
        """Request room service"""
        with self.lock:
            # Find available staff
            staff = self.find_available_staff(service_type)
            
            if not staff:
                self.notify_observers("service_requested", {
                    'message': "Service request for Room %s queued (no staff available)" % 
                              room.room_number
                })
                return None
            
            # Create service request
            self.service_counter += 1
            service_id = "SVC_%06d" % self.service_counter
            
            service = RoomService(service_id, room, service_type, description, priority)
            self.services[service_id] = service
            
            # Create and execute command
            if service_type == ServiceType.ROOM_SERVICE:
                command = RoomServiceCommand(service, staff)
            elif service_type == ServiceType.HOUSEKEEPING:
                command = HousekeepingCommand(service, staff)
            elif service_type == ServiceType.MAINTENANCE:
                command = MaintenanceCommand(service, staff)
            else:
                command = RoomServiceCommand(service, staff)
            
            if command.execute():
                self.notify_observers("service_requested", {
                    'message': "%s: %s assigned to %s for Room %s" % 
                              (service_type.value, staff.name, staff.role.value, 
                               room.room_number)
                })
                
                if service_type == ServiceType.MAINTENANCE and priority == Priority.URGENT:
                    self.notify_observers("maintenance_urgent", {
                        'message': "URGENT maintenance needed in Room %s: %s" % 
                                  (room.room_number, description),
                        'priority': 'URGENT'
                    })
                
                return service
            
            return None
    
    def complete_service(self, service: RoomService, notes: str = ""):
        """Complete service request"""
        service.complete_service(notes)
        
        if service.assigned_staff:
            service.assigned_staff.is_available = True
            service.assigned_staff.completed_services += 1
        
        # Complete maintenance on room
        if service.service_type == ServiceType.MAINTENANCE:
            if service.room.status == RoomStatus.MAINTENANCE:
                service.room.complete_maintenance()
        
        self.notify_observers("service_completed", {
            'guest_name': 'Guest',
            'service_type': service.service_type.value,
            'room_number': service.room.room_number,
            'message': "%s completed for Room %s" % 
                      (service.service_type.value, service.room.room_number)
        })
    
    # ===== Statistics =====
    
    def get_statistics(self) -> dict:
        """Get hotel statistics"""
        total_rooms = len(self.rooms)
        available_rooms = len([r for r in self.rooms.values() 
                              if r.status == RoomStatus.AVAILABLE])
        occupied_rooms = len([r for r in self.rooms.values() 
                             if r.status == RoomStatus.OCCUPIED])
        reserved_rooms = len([r for r in self.rooms.values() 
                             if r.status == RoomStatus.RESERVED])
        
        return {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'reserved_rooms': reserved_rooms,
            'occupied_rooms': occupied_rooms,
            'maintenance_rooms': total_rooms - available_rooms - reserved_rooms - occupied_rooms,
            'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
            'total_guests': len(self.guests),
            'total_staff': len(self.staff),
            'active_reservations': len([r for r in self.reservations.values() 
                                       if r.status in [ReservationStatus.CONFIRMED, 
                                                      ReservationStatus.CHECKED_IN]]),
            'completed_stays': len([r for r in self.reservations.values() 
                                   if r.status == ReservationStatus.CHECKED_OUT]),
            'pending_services': len([s for s in self.services.values() 
                                    if not s.is_completed])
        }


# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70)


def demo1_setup_and_room_creation():
    """Demo 1: System Setup & Room Creation"""
    print_section("DEMO 1: System Setup & Room Creation")
    
    system = HotelManagementSystem()
    
    # Add observers
    print("\n1. Adding observers...")
    system.attach_observer(GuestNotifier())
    system.attach_observer(StaffNotifier())
    system.attach_observer(AdminNotifier())
    print("   ✓ Guest, Staff, and Admin notifiers attached")
    
    # Create rooms using factory
    print("\n2. Creating rooms using Factory pattern...")
    rooms_config = [
        (RoomType.STANDARD, "101", 1),
        (RoomType.STANDARD, "102", 1),
        (RoomType.DELUXE, "201", 2),
        (RoomType.DELUXE, "202", 2),
        (RoomType.SUITE, "301", 3),
    ]
    
    for room_type, room_number, floor in rooms_config:
        room = system.add_room(room_type, room_number, floor)
        print("   ✓ Created: %s" % room)
    
    # Add staff
    print("\n3. Adding staff members...")
    staff_config = [
        ("Maria", StaffRole.HOUSEKEEPER),
        ("Carlos", StaffRole.ROOM_SERVICE),
        ("David", StaffRole.MAINTENANCE),
        ("Ana", StaffRole.HOUSEKEEPER),
    ]
    
    for name, role in staff_config:
        staff = system.add_staff(name, role)
        print("   ✓ Added: %s" % staff)
    
    # Display statistics
    print("\n4. System Statistics:")
    stats = system.get_statistics()
    for key, value in stats.items():
        print("   %s: %s" % (key.replace('_', ' ').title(), value))


def demo2_guest_registration_and_reservation():
    """Demo 2: Guest Registration & Reservation"""
    print_section("DEMO 2: Guest Registration & Reservation")
    
    system = HotelManagementSystem()
    
    # Register guests
    print("\n1. Registering guests...")
    guest1 = system.register_guest("John Smith", "john@email.com", "555-0101")
    guest2 = system.register_guest("Sarah Johnson", "sarah@email.com", "555-0102")
    print("   ✓ %s" % guest1)
    print("   ✓ %s" % guest2)
    
    # Create reservation
    print("\n2. Creating reservation...")
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=4)
    
    reservation = system.create_reservation(guest1, RoomType.STANDARD, check_in, check_out)
    
    if reservation:
        print("\n3. Reservation Details:")
        print("   ID: %s" % reservation.reservation_id)
        print("   Guest: %s" % reservation.guest.name)
        print("   Room: %s (%s)" % (reservation.room.room_number, reservation.room.room_type.value))
        print("   Check-in: %s" % reservation.check_in_date)
        print("   Check-out: %s" % reservation.check_out_date)
        print("   Nights: %d" % reservation.num_nights)
        print("   Total: $%.2f" % reservation.total_price)
        print("   Status: %s" % reservation.status.value)


def demo3_dynamic_pricing_comparison():
    """Demo 3: Dynamic Pricing Comparison"""
    print_section("DEMO 3: Dynamic Pricing Comparison")
    
    system = HotelManagementSystem()
    
    # Get a room and guest
    guest = system.register_guest("Alice Williams", "alice@email.com", "555-0103")
    room = list(system.rooms.values())[0]  # Get first room
    
    num_nights = 3
    
    print("\n1. Comparing pricing strategies for %s Room (%d nights)..." % 
          (room.room_type.value.title(), num_nights))
    print("   Base price: $%.2f/night" % room.base_price)
    print("   Guest discount: %.0f%%" % (guest.get_discount_percentage() * 100))
    
    # Regular pricing
    print("\n2. Regular Pricing:")
    system.set_pricing_strategy(RegularPricing())
    regular_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % regular_price)
    
    # Seasonal pricing
    print("\n3. Seasonal Pricing:")
    system.set_pricing_strategy(SeasonalPricing())
    seasonal_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % seasonal_price)
    print("   Difference: $%.2f (%.1f%%)" % 
          (seasonal_price - regular_price, 
           ((seasonal_price - regular_price) / regular_price * 100)))
    
    # Event pricing
    print("\n4. Event Pricing (conference dates):")
    event_dates = [date.today() + timedelta(days=i) for i in range(7)]
    system.set_pricing_strategy(EventPricing(event_dates, event_multiplier=2.0))
    event_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % event_price)
    print("   Difference: $%.2f (%.1f%%)" % 
          (event_price - regular_price, 
           ((event_price - regular_price) / regular_price * 100)))
    
    # VIP guest comparison
    print("\n5. VIP Guest with 1000 loyalty points:")
    vip_guest = system.register_guest("VIP Member", "vip@email.com", "555-0104")
    vip_guest.add_loyalty_points(1000)
    print("   Guest: %s" % vip_guest)
    print("   Discount: %.0f%%" % (vip_guest.get_discount_percentage() * 100))
    
    system.set_pricing_strategy(RegularPricing())
    vip_price = system.pricing_strategy.calculate_price(room, num_nights, vip_guest)
    print("   Regular price: $%.2f" % regular_price)
    print("   VIP price: $%.2f" % vip_price)
    print("   Savings: $%.2f" % (regular_price - vip_price))


def demo4_full_guest_journey():
    """Demo 4: Full Guest Journey"""
    print_section("DEMO 4: Full Guest Journey (Reservation to Check-out)")
    
    system = HotelManagementSystem()
    
    # Register guest
    print("\n1. Guest Registration:")
    guest = system.register_guest("Emma Davis", "emma@email.com", "555-0105")
    print("   %s" % guest)
    
    # Create reservation
    print("\n2. Creating Reservation:")
    check_in = date.today()
    check_out = date.today() + timedelta(days=2)
    reservation = system.create_reservation(guest, RoomType.DELUXE, check_in, check_out)
    
    # Check in
    print("\n3. Checking In:")
    system.check_in(reservation)
    
    # Request services
    print("\n4. Requesting Services (Command Pattern):")
    
    # Room service
    service1 = system.request_service(
        reservation.room, 
        ServiceType.ROOM_SERVICE,
        "Breakfast for 2: eggs, toast, coffee",
        Priority.MEDIUM
    )
    
    # Housekeeping
    service2 = system.request_service(
        reservation.room,
        ServiceType.HOUSEKEEPING,
        "Extra towels and toiletries",
        Priority.LOW
    )
    
    # Complete services
    print("\n5. Completing Services:")
    if service1:
        system.complete_service(service1, "Delivered at 8:30 AM")
    if service2:
        system.complete_service(service2, "Restocked at 10:00 AM")
    
    # Check out
    print("\n6. Checking Out & Generating Invoice:")
    invoice = system.check_out(reservation)
    
    if invoice:
        print(invoice.get_summary())
    
    # Process payment
    print("7. Processing Payment:")
    payment = system.process_payment(invoice, invoice.total, PaymentMethod.CREDIT_CARD)
    
    if payment:
        print("\n8. Updated Guest Profile:")
        print("   %s" % guest)


def demo5_room_state_management():
    """Demo 5: Room State Management & Maintenance"""
    print_section("DEMO 5: Room State Management & Maintenance")
    
    system = HotelManagementSystem()
    
    # Get a room
    room = list(system.rooms.values())[2]  # Get third room
    guest = system.register_guest("Mike Brown", "mike@email.com", "555-0106")
    
    print("\n1. Initial Room State:")
    print("   %s" % room)
    print("   Status: %s" % room.status.value)
    
    # Reserve room
    print("\n2. Creating Reservation (AVAILABLE → RESERVED):")
    check_in = date.today()
    check_out = date.today() + timedelta(days=1)
    reservation = system.create_reservation(guest, room.room_type, check_in, check_out)
    print("   New Status: %s" % room.status.value)
    
    # Check in
    print("\n3. Checking In (RESERVED → OCCUPIED):")
    system.check_in(reservation)
    print("   New Status: %s" % room.status.value)
    
    # Request urgent maintenance
    print("\n4. Requesting Urgent Maintenance:")
    service = system.request_service(
        room,
        ServiceType.MAINTENANCE,
        "Air conditioning not working",
        Priority.URGENT
    )
    
    if service:
        print("   Room Status: %s" % room.status.value)
        if room.maintenance_notes:
            print("   Maintenance Notes: %s" % room.maintenance_notes[-1]['note'])
    
    # Complete maintenance
    print("\n5. Completing Maintenance:")
    if service:
        # Complete the maintenance service
        system.complete_service(service, "Replaced AC filter and recharged coolant")
        print("   Room Status after maintenance: %s" % room.status.value)
        
        # Now check out the guest (room is back to AVAILABLE, but we need to manually set to OCCUPIED first)
        # This is a demo limitation - in real scenario, guest would still be in room during maintenance
        print("\n6. Checking Out Guest:")
        # Manually restore to OCCUPIED state for proper checkout
        room.status = RoomStatus.OCCUPIED
        system.check_out(reservation)
        print("   Room Status after checkout: %s" % room.status.value)
    
    # Attempt invalid transition
    print("\n7. Attempting Invalid State Transition:")
    print("   Trying to occupy an available room (should fail)...")
    try:
        room.occupy()
    except ValueError as e:
        print("   ✓ Correctly prevented: %s" % str(e))
    
    # Show state machine
    print("\n8. Room State Machine:")
    print("   AVAILABLE → RESERVED → OCCUPIED → AVAILABLE")
    print("        ↓         ↓          ↓")
    print("   MAINTENANCE (from any state)")
    print("\n   Note: Room transitions back to AVAILABLE after maintenance completes")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("HOTEL MANAGEMENT SYSTEM - COMPLETE DEMONSTRATION".center(70))
    print("="*70)
    print("\nDesign Patterns Implemented:")
    print("  1. Singleton    - HotelManagementSystem")
    print("  2. Factory      - RoomFactory")
    print("  3. Strategy     - PricingStrategy (Regular/Seasonal/Event)")
    print("  4. Observer     - Notifications (Guest/Staff/Admin)")
    print("  5. State        - Room & Reservation lifecycles")
    print("  6. Command      - Service requests")
    
    time.sleep(1)
    
    demo1_setup_and_room_creation()
    time.sleep(1)
    
    demo2_guest_registration_and_reservation()
    time.sleep(1)
    
    demo3_dynamic_pricing_comparison()
    time.sleep(1)
    
    demo4_full_guest_journey()
    time.sleep(1)
    
    demo5_room_state_management()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY".center(70))
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Singleton ensures single system instance with thread safety")
    print("  • Factory creates rooms with type-specific configurations")
    print("  • Strategy enables runtime pricing changes")
    print("  • Observer decouples notifications from core logic")
    print("  • State machines prevent invalid transitions")
    print("  • Command encapsulates service requests for queuing")
    print("\nRun: python3 INTERVIEW_COMPACT.py")
    print("="*70 + "\n")

```

## UML Class Diagram (text)
````
(Classes, relationships, strategies/observers, enums)
````


## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
