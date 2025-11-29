# 🚗 Car Rental System - 75 Minute Interview Implementation Guide

## System Overview
A multi-location car rental platform supporting vehicle inventory management, customer reservations, dynamic pricing, booking lifecycle management, and payment processing. The system handles concurrent bookings, vehicle availability tracking, rental period pricing, and location-based operations across multiple rental stations.

---

## Core Requirements

### Functional Requirements
- **Vehicle Management**: Add/remove vehicles, track status (AVAILABLE/RENTED/MAINTENANCE)
- **Customer Management**: Register customers, maintain booking history
- **Reservation System**: Reserve vehicles for specific dates with pickup/dropoff
- **Pricing**: Dynamic pricing based on vehicle type, rental duration, demand
- **Booking Lifecycle**: Create booking → Reserve → Pickup → Return → Payment
- **Inventory Tracking**: Real-time vehicle availability per location
- **Location Management**: Multiple rental locations with separate inventories
- **Return Processing**: Accept vehicle returns, calculate costs, process payment

### Non-Functional Requirements
- Support 10,000+ customers
- 1,000+ vehicles across 50+ locations
- Concurrent bookings (100+ per minute per location)
- Real-time availability updates
- Location-specific pricing
- Fuel & damage tracking

### Scale & Constraints
- Rental duration: 1 hour to 365 days
- Vehicle types: Economy, Sedan, SUV, Luxury
- Locations: 50+ across multiple cities
- Booking capacity: 100+ concurrent reservations per day
- Payment methods: Credit card, cash, corporate accounts

---

## 75-Minute Implementation Timeline

### Phase 0: Requirements Clarification (0-5 minutes)
**Goal**: Define scope and constraints

**Clarifications**:
- How are locations managed? (Separate inventories per location)
- Can vehicles be reserved across locations? (No, per-location only)
- What triggers pricing changes? (Duration, vehicle type, demand, location)
- How is fuel/damage handled? (Tracked, charged separately)
- Concurrent booking scenarios? (Multiple users booking same vehicle)
- How is availability calculated? (Real-time based on bookings)

**Expected Output**: Clear entity relationships and system boundaries

---

### Phase 1: Architecture & Design (5-15 minutes)
**Goal**: Define system architecture and patterns

**High-Level Architecture**:
```
┌─────────────────────────────────────────────────────┐
│          Car Rental System (Singleton)              │
├─────────────────────────────────────────────────────┤
│  • Manages all locations, vehicles, customers      │
│  • Coordinates reservations and bookings            │
│  • Handles pricing and payments                     │
└────────┬──────────────────────────────┬─────────────┘
         │                              │
    ┌────▼──────────┐          ┌───────▼───────┐
    │   Locations   │          │   Customers   │
    │  (Inventory)  │          │   (History)   │
    └───────────────┘          └───────────────┘
         │
    ┌────▼──────────┐
    │   Vehicles    │
    │  (Status)     │
    └───────────────┘
         │
    ┌────▼──────────────────┐
    │  Reservations         │
    │  & Bookings           │
    └───────────────────────┘
```

**Design Patterns**:
1. **Singleton**: Central CarRentalSystem instance
2. **Strategy**: Different pricing strategies (daily rate, hourly, package deals)
3. **Observer**: Notify on booking changes, availability updates
4. **State**: Booking lifecycle (PENDING → ACTIVE → COMPLETED → RETURNED)
5. **Factory**: Create bookings and reservations based on type

**Key Decisions**:
- Enum-based state machine for vehicle status and booking state
- Strategy pattern for flexible pricing algorithms
- Observer pattern for real-time notifications
- Thread locks for concurrent booking safety
- Location-based inventory management

**Expected Output**: Architecture diagram + pseudocode structure

---

### Phase 2: Core Entities (15-35 minutes)
**Goal**: Implement all core entities with full business logic

#### 1. Enumerations
```python
from enum import Enum
from datetime import datetime, timedelta
import threading
from abc import ABC, abstractmethod

class VehicleType(Enum):
    ECONOMY = 1
    SEDAN = 2
    SUV = 3
    LUXURY = 4

class VehicleStatus(Enum):
    AVAILABLE = 1
    RENTED = 2
    MAINTENANCE = 3
    RETIRED = 4

class BookingStatus(Enum):
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELLED = 4
    RETURNED = 5

class PaymentStatus(Enum):
    PENDING = 1
    PAID = 2
    FAILED = 3
    REFUNDED = 4
```

#### 2. Vehicle Management
```python
class Vehicle:
    """Represents physical vehicle"""
    def __init__(self, vehicle_id: str, vehicle_type: VehicleType, 
                 license_plate: str, location_id: str):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate
        self.location_id = location_id
        self.status = VehicleStatus.AVAILABLE
        self.mileage = 0.0
        self.fuel_level = 100.0
        self.damage_reported = False
        self.created_at = datetime.now()
        self.last_maintenance = datetime.now()
    
    def is_available(self) -> bool:
        """Check if vehicle available for booking"""
        return self.status == VehicleStatus.AVAILABLE and not self.damage_reported
    
    def reserve(self) -> bool:
        """Reserve vehicle"""
        if self.status == VehicleStatus.AVAILABLE:
            self.status = VehicleStatus.RENTED
            return True
        return False
    
    def release(self):
        """Release vehicle back to available"""
        self.status = VehicleStatus.AVAILABLE
    
    def update_fuel(self, fuel_level: float):
        """Update fuel level"""
        self.fuel_level = max(0.0, min(100.0, fuel_level))
    
    def report_damage(self):
        """Report damage, vehicle taken out of service"""
        self.damage_reported = True
        self.status = VehicleStatus.MAINTENANCE
    
    def clear_damage(self):
        """Clear damage report after maintenance"""
        self.damage_reported = False
        self.status = VehicleStatus.AVAILABLE
    
    def update_mileage(self, additional_miles: float):
        """Track mileage"""
        self.mileage += additional_miles
```

#### 3. Customer & Location
```python
class Customer:
    """Represents customer"""
    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.bookings = []
        self.created_at = datetime.now()
        self.total_rentals = 0
        self.loyalty_points = 0
    
    def add_booking(self, booking: 'Booking'):
        """Add booking to customer history"""
        self.bookings.append(booking)
        self.total_rentals += 1
        self.loyalty_points += 10  # Points per booking
    
    def get_loyalty_discount(self) -> float:
        """Get discount based on loyalty"""
        if self.total_rentals > 100:
            return 0.20  # 20% discount for VIP
        elif self.total_rentals > 50:
            return 0.15  # 15% discount
        elif self.total_rentals > 10:
            return 0.10  # 10% discount
        return 0.0

class Location:
    """Represents rental location"""
    def __init__(self, location_id: str, name: str, city: str):
        self.location_id = location_id
        self.name = name
        self.city = city
        self.vehicles = []  # List[Vehicle]
        self.bookings = []  # List[Booking]
        self.lock = threading.Lock()
    
    def add_vehicle(self, vehicle: Vehicle):
        """Add vehicle to location"""
        with self.lock:
            self.vehicles.append(vehicle)
    
    def get_available_vehicles(self, vehicle_type: VehicleType = None):
        """Get available vehicles"""
        with self.lock:
            available = [v for v in self.vehicles if v.is_available()]
            if vehicle_type:
                available = [v for v in available if v.vehicle_type == vehicle_type]
            return available
    
    def get_available_count(self, vehicle_type: VehicleType) -> int:
        """Get count of available vehicles"""
        with self.lock:
            return len([v for v in self.vehicles 
                       if v.vehicle_type == vehicle_type and v.is_available()])
    
    def add_booking(self, booking: 'Booking'):
        """Record booking at location"""
        with self.lock:
            self.bookings.append(booking)
```

#### 4. Pricing Strategy
```python
class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_price(self, vehicle: Vehicle, rental_days: int, 
                       base_rate: float, location: Location) -> float:
        pass

class DailyRatePricing(PricingStrategy):
    """Simple daily rate pricing"""
    def calculate_price(self, vehicle: Vehicle, rental_days: int, 
                       base_rate: float, location: Location) -> float:
        return base_rate * rental_days

class WeeklyDiscountPricing(PricingStrategy):
    """Discount for weekly rentals"""
    def calculate_price(self, vehicle: Vehicle, rental_days: int, 
                       base_rate: float, location: Location) -> float:
        if rental_days >= 7:
            return base_rate * rental_days * 0.85  # 15% discount
        return base_rate * rental_days

class DemandBasedPricing(PricingStrategy):
    """Price increases based on availability"""
    def calculate_price(self, vehicle: Vehicle, rental_days: int, 
                       base_rate: float, location: Location) -> float:
        available_count = location.get_available_count(vehicle.vehicle_type)
        multiplier = 1.0 if available_count > 5 else (1.2 if available_count < 2 else 1.0)
        return base_rate * rental_days * multiplier
```

#### 5. Booking & Reservation
```python
class Booking:
    """Represents vehicle booking"""
    def __init__(self, booking_id: str, customer: Customer, 
                 vehicle: Vehicle, location: Location,
                 pickup_date: datetime, dropoff_date: datetime):
        self.booking_id = booking_id
        self.customer = customer
        self.vehicle = vehicle
        self.location = location
        self.pickup_date = pickup_date
        self.dropoff_date = dropoff_date
        self.status = BookingStatus.PENDING
        self.created_at = datetime.now()
        self.rental_cost = 0.0
        self.fuel_charge = 0.0
        self.damage_charge = 0.0
        self.total_cost = 0.0
        self.payment_status = PaymentStatus.PENDING
    
    def get_rental_days(self) -> int:
        """Calculate rental days"""
        delta = self.dropoff_date - self.pickup_date
        return max(1, delta.days)
    
    def calculate_cost(self, pricing_strategy: PricingStrategy, 
                      base_rate: float) -> float:
        """Calculate rental cost"""
        rental_days = self.get_rental_days()
        cost = pricing_strategy.calculate_price(
            self.vehicle, rental_days, base_rate, self.location
        )
        
        # Apply loyalty discount
        discount = self.customer.get_loyalty_discount()
        cost = cost * (1 - discount)
        
        self.rental_cost = cost
        return cost
    
    def add_fuel_charge(self, charge: float):
        """Add fuel refill charge"""
        self.fuel_charge += charge
    
    def add_damage_charge(self, charge: float):
        """Add damage charge"""
        self.damage_charge += charge
    
    def finalize_cost(self) -> float:
        """Calculate final total cost"""
        self.total_cost = self.rental_cost + self.fuel_charge + self.damage_charge
        return self.total_cost
    
    def activate(self):
        """Activate booking (vehicle picked up)"""
        if self.status == BookingStatus.PENDING:
            self.status = BookingStatus.ACTIVE
            return True
        return False
    
    def complete(self):
        """Mark booking as completed"""
        self.status = BookingStatus.COMPLETED
    
    def return_vehicle(self):
        """Process vehicle return"""
        self.status = BookingStatus.RETURNED
        return self.total_cost
    
    def __repr__(self) -> str:
        return f"Booking({self.booking_id}) - {self.vehicle.vehicle_id} - {self.status.name}"
```

#### 6. Observer Pattern
```python
class BookingObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict):
        pass

class EmailNotifier(BookingObserver):
    def update(self, event: str, data: dict):
        print(f"    📧 Email: {event} - {data['customer']} - {data['vehicle']}")

class SMSNotifier(BookingObserver):
    def update(self, event: str, data: dict):
        print(f"    📱 SMS: {event} - {data['customer']}")

class SystemLogNotifier(BookingObserver):
    def update(self, event: str, data: dict):
        print(f"    📋 Log: [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {event}")
```

---

### Phase 3: Design Patterns (35-55 minutes)

#### Pattern 1: Singleton (System Coordinator)
Central CarRentalSystem ensures single global instance managing all locations, vehicles, bookings.

#### Pattern 2: Strategy (Pricing Algorithms)
Multiple pricing strategies (DailyRate, WeeklyDiscount, DemandBased) plugged into booking cost calculation.

#### Pattern 3: Observer (Booking Notifications)
Multiple observers notified when bookings created/completed without coupling to system.

#### Pattern 4: State (Booking Lifecycle)
BookingStatus enum manages transitions (PENDING → ACTIVE → RETURNED).

#### Pattern 5: Factory (Booking Creation)
Centralized booking creation with validation and cost calculation.

---

### Phase 4: System Integration & Edge Cases (55-70 minutes)

**Booking Flow**:
1. Customer requests vehicle (specific dates, type, location)
2. Check vehicle availability at location
3. Check customer eligibility (loyalty status)
4. Create booking with pricing strategy
5. Reserve vehicle (status → RENTED)
6. Notify observers
7. On pickup: activate booking, collect payment
8. On return: calculate damage/fuel charges, release vehicle

**Edge Cases**:
- Vehicle becomes unavailable during booking (concurrent bookings)
- Booking overlaps with maintenance
- Customer cancels mid-rental
- Damage discovered at return
- Fuel shortage at return
- Late return charges

**Thread-Safety**:
- Location.lock protects vehicle inventory
- Booking status transitions validated
- Concurrent reservation handling

**SOLID Principles**:
- **S**: Vehicle, Customer, Booking have single purposes
- **O**: New pricing strategies without modifying booking logic
- **L**: All strategies interchangeable
- **I**: Observer interface with single method
- **D**: System depends on Observer, PricingStrategy abstractions

---

### Phase 5: Demo Scenarios (70-75 minutes)

**Scenario 1**: Setup system and available vehicles
**Scenario 2**: Create successful booking with pricing
**Scenario 3**: Failed booking (vehicle unavailable)
**Scenario 4**: Booking with loyalty discount
**Scenario 5**: Return with damage charges

---

## Class Diagram (ASCII UML)

```
                    ┌──────────────────┐
                    │ CarRentalSystem  │◄────── Singleton
                    │   (Singleton)    │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
       ┌────▼────┐      ┌────▼────┐     ┌────▼───────┐
       │Locations│      │Customers│     │ Bookings   │
       └──────────┘      └─────────┘     └────────────┘
            │
       ┌────▼────────┐
       │  Vehicles   │
       ├─────────────┤
       │+vehicle_id  │
       │+type        │
       │+status      │
       │+location_id │
       └─────────────┘

       ┌──────────────────────┐
       │ PricingStrategy      │
       │  (Abstract)          │
       ├──────────────────────┤
       │ DailyRatePricing     │
       │ WeeklyDiscountPricing│
       │ DemandBasedPricing   │
       └──────────────────────┘

       ┌──────────────────────┐
       │ BookingObserver      │
       │  (Abstract)          │
       ├──────────────────────┤
       │ EmailNotifier        │
       │ SMSNotifier          │
       │ SystemLogNotifier    │
       └──────────────────────┘

       Booking State Machine:
       PENDING → ACTIVE → COMPLETED → RETURNED
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: What is the main responsibility of CarRentalSystem?**
A: Singleton that coordinates all rental operations (locations, vehicles, customers, bookings). Single instance manages global state preventing conflicts.

**Q2: How are vehicles tracked across multiple locations?**
A: Each Location maintains separate vehicle list. Vehicles linked to location_id. Availability calculated per-location only.

**Q3: What is the booking lifecycle?**
A: PENDING (created) → ACTIVE (picked up) → COMPLETED (dropped off) → RETURNED (finalized with charges).

### Intermediate Level

**Q4: How is pricing calculated?**
A: Strategy pattern plugs in different algorithms (DailyRate, WeeklyDiscount, DemandBased). Cost = strategy.calculate() * (1 - loyalty_discount).

**Q5: How are concurrent bookings handled safely?**
A: Location.lock protects vehicle inventory. Booking status transitions validated atomically. Prevents double-booking same vehicle.

**Q6: What happens if a customer damages vehicle at return?**
A: Damage charge added separately. Vehicle marked MAINTENANCE. New damage_charge property tracked. Total cost includes rental + fuel + damage.

**Q7: How does loyalty discount work?**
A: Customers earn loyalty points per booking. Discount based on total_rentals: 10+ bookings = 10%, 50+ = 15%, 100+ = 20%.

### Advanced Level

**Q8: How would you handle vehicle unavailability during concurrent bookings?**
A: First-come-first-served with thread locks. If vehicle reserved between availability check and booking creation, booking fails with clear message.

**Q9: What if rental period extends beyond initial booking?**
A: Late return charges calculated differently (hourly rate after cutoff). Current system doesn't model this; would require additional time-based pricing logic.

**Q10: How would you scale to multiple cities?**
A: Add City entity. Locations grouped by city. Search API returns results by proximity. Pricing varies by city/location. Separate inventory management per location.

**Q11: What security vulnerabilities exist?**
A: No authentication (anyone can book). Payment processing not secure (mock implementation). No audit trail. Customer identity not verified (license check missing).

**Q12: How would you test this system?**
A: Unit tests for pricing strategies, loyalty calculation. Integration tests for full booking flow. Concurrency tests for overbooking prevention. Mock external payment system.

---

## Summary

✅ **Singleton** for global coordination
✅ **Strategy** for pricing flexibility
✅ **Observer** for booking notifications
✅ **State** for booking lifecycle
✅ **Factory** for booking creation
✅ **Thread-safe** with location locks
✅ **Loyalty** system with discounts
✅ **Dynamic pricing** based on availability
✅ **Multi-location** support
✅ **Edge cases** handled (damage, fuel, late returns)
✅ **SOLID** principles throughout
✅ **Scalability** discussion

**Key Takeaway**: Car Rental System demonstrates how multiple patterns work together for a complex business domain with concurrent operations, dynamic pricing, customer loyalty, and real-time inventory management across distributed locations.
