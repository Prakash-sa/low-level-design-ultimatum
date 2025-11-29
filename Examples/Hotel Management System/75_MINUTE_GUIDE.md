# Hotel Management System - 75 Minute Interview Guide

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
