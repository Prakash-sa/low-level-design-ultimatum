# Car Rental System - Reference Guide

## System Overview
Multi-location car rental platform supporting vehicle reservations, dynamic pricing, loyalty programs, and damage/fuel tracking across distributed locations.

## Core Entities

| Entity | Key Attributes | Key Methods |
|--------|----------------|------------|
| **Vehicle** | vehicle_id, type (ECONOMY/SEDAN/SUV/LUXURY), license_plate, location_id, status, fuel_level, damage_reported | is_available(), reserve(), release(), update_fuel(), report_damage(), clear_damage() |
| **Customer** | customer_id, name, email, total_rentals, loyalty_points | add_booking(), get_loyalty_discount() |
| **Location** | location_id, name, city, vehicles[], bookings[], lock | add_vehicle(), get_available_vehicles(), get_available_count(), add_booking() |
| **Booking** | booking_id, customer, vehicle, location, pickup_date, dropoff_date, status, rental_cost, fuel_charge, damage_charge, total_cost | calculate_cost(), add_fuel_charge(), add_damage_charge(), activate(), complete(), return_vehicle() |
| **BookingObserver** | Abstract notifier pattern | update(event, data) |

## Design Patterns Applied

### 1. **Singleton** (CarRentalSystem)
- **Purpose**: Central system coordinator managing all locations, customers, vehicles, and bookings
- **Implementation**: Thread-safe lazy initialization with double-checked locking
- **Interview Points**: 
  - Why singleton? Single system instance prevents duplicate data
  - Thread safety: `_lock` protects initialization
  - Usage: `system = CarRentalSystem()`

### 2. **Strategy** (PricingStrategy)
Three pricing algorithms switchable at runtime:
- **DailyRatePricing**: Base rate × rental days
- **WeeklyDiscountPricing**: 15% off for 7+ day rentals
- **DemandBasedPricing**: 30% surge if <2 vehicles available; 1.0x if >5
- **Interview Points**:
  - Problem solved: Different pricing policies without modifying Booking
  - Runtime switching: `system.set_pricing_strategy(strategy)`
  - How to extend: Add new class inheriting PricingStrategy

### 3. **Observer** (BookingObserver)
Notifications triggered on booking lifecycle events:
- **EmailNotifier**: Sends email notifications
- **SMSNotifier**: Sends SMS notifications  
- **SystemLogNotifier**: Logs to system
- **Interview Points**:
  - Loose coupling between Booking and notifiers
  - Multiple observers can act on same event
  - Adding new notifier: Create class inheriting BookingObserver

### 4. **State** (BookingStatus)
Booking lifecycle: PENDING → ACTIVE → COMPLETED → RETURNED
- **Interview Points**:
  - Why separate enum? Prevents invalid state transitions
  - Example: Can't complete booking not yet active
  - State validation in activate(), complete(), return_vehicle()

### 5. **Factory**
Booking creation encapsulates cost calculation and observer notification
- **Interview Points**:
  - Complex initialization logic in one place
  - Vehicle reservation + booking creation atomic

## Business Logic Highlights

### Loyalty Discount Calculation
```
10+ rentals: 10% discount
50+ rentals: 15% discount
100+ rentals: 20% discount
```
Applied to rental_cost after strategy pricing.

### Cost Breakdown
- **Rental Cost**: From pricing strategy (may include surge/discount)
- **Fuel Charge**: $0.50 per 1% tank deficit (e.g., 40% fuel = $30 charge)
- **Damage Charge**: Manually added at return if damage reported
- **Total Cost**: rental_cost + fuel_charge + damage_charge

### Thread Safety
- **Location.lock**: Protects vehicle inventory during booking creation
- **CarRentalSystem.lock**: Protects system state (locations, customers, vehicles, bookings)
- **Payment transactions**: Atomic with booking creation

## Edge Cases Handled

| Edge Case | Solution |
|-----------|----------|
| Concurrent bookings for same vehicle | Lock-protected inventory check in Location |
| Vehicle becomes unavailable during booking | Vehicle status checked before reservation |
| Booking overlaps with maintenance | Vehicle.damage_reported prevents booking |
| Damage discovered at return | Separate damage_charge added after pickup |
| Fuel shortage at return | Fuel charge calculated as percentage deficit × $0.50 |
| Late returns | Tracked via dropoff_date, can extend with surcharge logic |

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **S**ingle Responsibility | Vehicle handles vehicle state; Booking handles booking lifecycle; Pricing handles cost calculation |
| **O**pen/Closed | New pricing strategies without modifying Booking; new notifiers without modifying Booking |
| **L**iskov Substitution | All PricingStrategy subclasses interchangeable; all BookingObserver subclasses interchangeable |
| **I**nterface Segregation | BookingObserver interface only requires update() method |
| **D**ependency Inversion | CarRentalSystem depends on PricingStrategy (abstract), not concrete implementations |

## Architecture Diagram

```
CarRentalSystem (Singleton)
├── Locations[]
│   ├── Vehicles[] (with thread-safe lock)
│   └── Bookings[]
├── Customers[]
├── Pricing Strategy (runtime switchable)
│   ├── DailyRatePricing
│   ├── WeeklyDiscountPricing
│   └── DemandBasedPricing
├── Observers[]
│   ├── EmailNotifier
│   ├── SMSNotifier
│   └── SystemLogNotifier
└── Booking Lifecycle State Machine
    PENDING → ACTIVE → COMPLETED → RETURNED
```

## Key Talking Points for Interview

### Scaling Considerations
1. **Database**: Store customers, vehicles, bookings in persistent storage
2. **Cache**: Redis for available vehicle count at each location
3. **Message Queue**: Async notification delivery (RabbitMQ/Kafka)
4. **Microservices**: Separate Payment, Location, Notification services

### Concurrency Challenges
1. **Double-booking prevention**: Location.lock ensures first-come-first-served
2. **Race conditions**: Atomic operations in create_booking() and return_vehicle()
3. **Deadlock avoidance**: Single lock per location, ordered acquisition

### Security & Validation
1. **Customer verification**: Email validation before booking
2. **Card processing**: Payment verification in pickup_vehicle()
3. **Vehicle tracking**: GPS integration for real-time location
4. **Access control**: Only customers can access own bookings

### Testing Strategy
1. **Unit tests**: PricingStrategy calculations, loyalty discounts
2. **Integration tests**: Multi-location booking workflows
3. **Concurrency tests**: Multiple simultaneous bookings on same vehicle
4. **Edge cases**: Damage, fuel, late returns

## Improvements & Extensions

### Current Limitations
- No payment processing (stub with PaymentStatus enum)
- No persistent storage (in-memory only)
- No GPS tracking or real-time vehicle location
- No cancellation or modification of existing bookings

### Future Enhancements
1. Add cancellation with refund logic
2. Integrate payment gateway (Stripe/PayPal)
3. Add vehicle tracking with GPS
4. Support multi-day returns with late fees
5. Add vehicle maintenance scheduling
6. Implement customer rating system
7. Add insurance options per booking

## Demo Scenarios Included

1. **Setup & Search**: Register locations/vehicles/customers, search available inventory
2. **Basic Booking**: Create 3-day booking with observer notifications
3. **Loyalty Discount**: VIP customer with 10% discount calculation
4. **Demand Pricing**: Single available vehicle triggers 30% surge pricing
5. **Return with Charges**: Full lifecycle with fuel and damage charges

