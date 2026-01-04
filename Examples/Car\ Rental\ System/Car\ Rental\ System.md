# Car Rental System — 75-Minute Interview Guide

## Quick Start

**What is it?** A comprehensive car rental system supporting vehicle inventory management, reservation creation/modification/cancellation, multi-location operations, pricing strategies, customer billing, and admin reporting.

**Key Classes:**
- `CarRentalSystem` (Singleton): Manages reservations, vehicles, locations, and pricing
- `Vehicle`: Car with status (available/reserved/maintenance), location tracking
- `Reservation`: Booking details with pickup/return dates, pricing, status
- `Location`: Branch with vehicle inventory
- `PricingStrategy`: Dynamic pricing (daily/weekly/monthly rates)
- `Customer`: User profile with rental history

**Core Flows:**
1. **Search**: Query available vehicles by location, type, dates → Filter by price/features
2. **Reserve**: Create reservation → Check availability → Lock vehicle → Generate pricing quote
3. **Pickup**: Verify reservation → Inspect vehicle → Issue keys → Update status
4. **Return**: Inspect vehicle → Calculate charges → Process payment → Release vehicle

**5 Design Patterns:**
- **Singleton**: One `CarRentalSystem` manages all operations
- **Strategy**: Multiple pricing strategies (daily, weekly, monthly)
- **Observer**: Notify customers of reservation confirmations/updates
- **Factory**: Create reservations with pricing calculation
- **State**: Vehicle status lifecycle (available → reserved → picked_up → returned)

---

## System Overview

A distributed car rental platform supporting multi-location inventory management, dynamic pricing, complex reservations with date/vehicle/location constraints, customer billing and payments, and business analytics. Core focus: availability management, pricing flexibility, and customer experience.

### Requirements

**Functional:**
- Search vehicles by location, type, dates, price range
- Create/modify/cancel reservations
- Pickup and return processing with inspections
- Dynamic pricing (daily/weekly/monthly rates)
- Customer profile management
- Rental history tracking
- Payment processing
- Admin reports (revenue, utilization, popular models)

**Non-Functional:**
- O(1) vehicle availability lookup
- Real-time reservation updates
- Multi-location consistency
- Support 10K+ concurrent searches
- 99.9% uptime for critical operations

**Constraints:**
- Reservations can be modified until 24h before pickup
- Cancellations allowed with penalty (50% if < 48h)
- Vehicles must pass inspection before rental
- Same vehicle can't overlap reservations

---

## Architecture Diagram (ASCII UML)

```
┌─────────────────────────────────────┐
│   CarRentalSystem (Singleton)       │
│   Manages reservations, vehicles,   │
│   locations, customers              │
└────────────┬────────────────────────┘
             │
    ┌────────┼────────┬───────────┐
    │        │        │           │
    ▼        ▼        ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│Customers │ │Locations │ │Reservations[]│
│{id→Cust} │ │{id→Loc}  │ │{id→Res}      │
└──────────┘ └────┬─────┘ └────┬─────────┘
                  │            │
                  ▼            ▼
            ┌──────────┐  ┌────────────┐
            │Vehicles[]│  │Reservation │
            │{id→Veh}  │  ├────────────┤
            └──────────┘  │+vehicle_id │
                          │+customer   │
                          │+dates      │
                          │+price      │
                          │+status     │
                          └────────────┘

PricingStrategy Pattern:
┌──────────────────┐
│PricingStrategy   │
│    (ABC)         │
└────┬─────────────┘
     │
  ┌──┴──┬──────────┐
  ▼     ▼          ▼
Daily Weekly Monthly

Vehicle Status Machine:
AVAILABLE ──→ RESERVED ──→ PICKED_UP ──→ RETURNED
   ↓                                         │
   └─────────────────────────────────────────┘
          (maintenance if needed)

Observer Pattern:
┌─────────────────────┐
│ ReservationObserver │
└────┬────────────────┘
     │
  ┌──┴──┬──────────┐
  ▼     ▼          ▼
Email SMS Push
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: What does CarRentalSystem singleton manage?**
A: Single global instance coordinating all rental operations: customers, vehicles, locations, reservations, pricing, payments. Prevents conflicts, ensures coherent state across all branches.

**Q2: How do you handle vehicle availability at multiple locations?**
A: Each location tracks its vehicle inventory. Search queries filter by location. Reservation locks specific vehicle at location. Transfer between locations requires explicit operation (move vehicle, update location).

**Q3: What is a Reservation and what states does it have?**
A: Reservation represents booking from specific customer. States: PENDING (confirmed but not picked up), ACTIVE (picked up), COMPLETED (returned), CANCELLED. Transitions enforce business rules (can't cancel after pickup).

**Q4: Why use multiple pricing strategies?**
A: Different customers prefer different rates: daily renters want per-day rate, weekly travelers want discount, monthly users want bulk rate. Strategy pattern allows pluggable pricing without modifying core code.

### Intermediate Level

**Q5: How do you prevent double-booking same vehicle?**
A: For each vehicle, maintain reserved date ranges. Before confirming reservation, check if new booking overlaps with existing. Use interval tree (O(log n)) for efficient overlap detection. Lock vehicle during confirmation to prevent race condition.

**Q6: How are cancellation penalties calculated?**
A: Penalty depends on how close to rental start: < 48h → 50% penalty, 48h-7d → 25% penalty, >7d → refund (minus admin fee). Calculated at cancellation time. Adjusted based on vehicle demand.

**Q7: What happens if reserved vehicle needs maintenance?**
A: Check vehicle status before pickup. If maintenance needed, mark as IN_MAINTENANCE. Notify customer, offer alternative vehicle or cancellation with full refund. Prevent pickup if status ≠ AVAILABLE.

**Q8: How do you handle payment failures?**
A: At return, calculate total charge. Process payment. If failed: retry with different method, or place on hold. Can't release car until payment success or customer agrees to billing terms.

### Advanced Level

**Q9: How to scale across 1000 locations and 100K vehicles?**
A: Geo-partitioned database (each region separate). Per-location caches for popular queries. Distributed search index (Elasticsearch). Eventual consistency for inter-location transfers. Sync vehicles hourly vs real-time.

**Q10: How to handle reservation transfer between locations?**
A: Pickup at Location A, return at Location B. Charge transfer fee. Update location on return. Track vehicle movement. Risk: vehicle in transit state. Solution: location field includes "in_transit" state.

**Q11: How to optimize pricing for maximum revenue?**
A: Analyze demand (bookings vs available). Dynamic pricing: increase rate if demand high, decrease if inventory excess. A/B test pricing strategies. Predict demand for future dates. Trade-off: optimization complexity vs revenue gain.

**Q12: How to ensure data consistency across distributed locations?**
A: Pessimistic: lock vehicle during reservation (slow but safe). Optimistic: allow concurrent bookings, detect conflicts, retry. Distributed consensus (Raft) for critical operations. Read replicas with eventual consistency for queries.

---

## Scaling Q&A (12 Questions)

**Q1: How does search scale to 1M queries/day across 100K vehicles?**
A: In-memory index (location × vehicle_type → available_vehicles). Query hits cache. Update index as vehicles book/return. Use Elasticsearch for complex filters (price, features). Cache popular queries (top 100 locations).

**Q2: What if two customers try to book same vehicle simultaneously?**
A: Race condition. Solution: pessimistic locking (lock vehicle, check overlap, reserve atomically). Or optimistic (allow both, detect conflict during commit, roll one back + notify). Pessimistic simpler but slower.

**Q3: How to handle peak booking times (holiday weekends)?**
A: Spike in queries + reservations. Scale horizontally: increase reservation processing servers. Rate limit expensive operations (searches per user). Queue excess requests. Upgrade pricing during peak = incentivize off-peak.

**Q4: How to track vehicle movement and maintain accuracy?**
A: GPS tracking (IoT device in car). Sync location periodically. On pickup/return, verify location. Track mileage, damage via photos/inspection reports. Detect theft (vehicle outside expected region).

**Q5: How to prevent overbooking during high concurrency?**
A: Test scenario: vehicle has 10 days available, 100 customers try to book simultaneously. Need strict locking. Reserve only after confirming no overlap + available. Implement using DB transaction + row locks.

**Q6: What's memory overhead for 100K vehicles?**
A: Vehicle object: vehicle_id + type + location + status + current_mileage + damage_report ≈ 200 bytes. For 100K: 20MB. Acceptable for in-memory cache. Add DB for persistent storage.

**Q7: How to handle vehicle transfer between locations efficiently?**
A: Mark vehicle as "IN_TRANSIT" (unavailable for booking). Transport physically. Update location + status. For 1000 transfers/day: batch process at off-peak times. Sync overnight if network permits.

**Q8: How to calculate revenue per vehicle/location/type?**
A: Track all reservations: (vehicle, dates, customer, price). Aggregate by vehicle/location/type. Calculate utilization = total_booked_days / total_days. Report daily/weekly/monthly. Query DB with aggregation pipeline (MongoDB) or spark jobs (Hadoop).

**Q9: Can pricing strategy change mid-season?**
A: Yes. Update strategy globally or per-vehicle. Existing reservations locked at original price. Future bookings use new strategy. Implement using version control (pricing_strategy_version field).

**Q10: How to handle customer disputes (damaged vehicle, overbilling)?**
A: Maintain audit log (all transactions, inspection photos, GPS locations). Review dispute with evidence. Refund/charge difference if justified. Store dispute history per customer (fraud detection).

**Q11: What if payment processor is down during checkout?**
A: Queue payment requests. Retry with exponential backoff. Hold car for customer if payment pending. Notify after processor recovers. Risk: customer leaves angry. Better: async processing (reserve car, process payment later).

**Q12: How to optimize vehicle utilization (minimize idle time)?**
A: Predictive analytics: forecast demand per location/date. Reposition vehicles proactively (transfer from low-demand to high-demand areas). Incentivize off-peak bookings (discounts). Monitor utilization KPI (target: 80%+).

---

## Demo Scenarios (5 Examples)

### Demo 1: Search & Reserve
```
- Search for economy cars at SF location, 5/1-5/3
- System shows 10 available vehicles with pricing
- Select vehicle, confirm reservation
- Reservation confirmed, payment pending
```

### Demo 2: Modify Reservation
```
- Customer modifies pickup date (5/1 → 5/2)
- System checks availability for new dates
- Updates pricing quote (one day less)
- Charges/refunds difference
```

### Demo 3: Pickup Vehicle
```
- Customer arrives for pickup
- Verify reservation status
- Inspect vehicle (photos, mileage, damage report)
- Issue keys, customer drives away
- Charge customer deposit ($500)
```

### Demo 4: Return Vehicle
```
- Customer returns vehicle
- Verify mileage & condition
- Calculate total charges (rental days × rate + extras)
- Process payment (deposit + charges)
- Release vehicle, mark as available
```

### Demo 5: Cancel Reservation
```
- Customer cancels reservation (< 48h before pickup)
- Apply 50% penalty
- Process refund
- Release vehicle back to available
- Notify customer
```

---

## Complete Implementation

```python
"""
🚗 Car Rental System - Interview Implementation
Demonstrates:
1. Search & reserve vehicles
2. Modify reservations
3. Pickup with inspection
4. Return with billing
5. Cancellation with penalties
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class VehicleStatus(Enum):
    AVAILABLE = 1
    RESERVED = 2
    PICKED_UP = 3
    IN_MAINTENANCE = 4

class ReservationStatus(Enum):
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELLED = 4

class VehicleType(Enum):
    ECONOMY = 1
    SEDAN = 2
    SUV = 3
    LUXURY = 4

# ============================================================================
# PRICING STRATEGY
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, days: int, daily_rate: float) -> float:
        pass

class DailyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        return days * daily_rate

class WeeklyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        weeks = days // 7
        remaining_days = days % 7
        weekly_rate = daily_rate * 6  # 1 day free per week
        return weeks * weekly_rate + remaining_days * daily_rate

class MonthlyPricingStrategy(PricingStrategy):
    def calculate_price(self, days: int, daily_rate: float) -> float:
        months = days // 30
        remaining_days = days % 30
        monthly_rate = daily_rate * 25  # 5 days free per month
        return months * monthly_rate + remaining_days * daily_rate

# ============================================================================
# CORE ENTITIES
# ============================================================================

class Vehicle:
    def __init__(self, vehicle_id: str, vehicle_type: VehicleType, 
                 location: str, daily_rate: float):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.location = location
        self.daily_rate = daily_rate
        self.status = VehicleStatus.AVAILABLE
        self.current_mileage = 0
        self.created_at = datetime.now()
        self.lock = threading.Lock()
    
    def is_available(self) -> bool:
        with self.lock:
            return self.status == VehicleStatus.AVAILABLE
    
    def reserve(self) -> bool:
        with self.lock:
            if self.status == VehicleStatus.AVAILABLE:
                self.status = VehicleStatus.RESERVED
                return True
            return False
    
    def pickup(self) -> bool:
        with self.lock:
            if self.status == VehicleStatus.RESERVED:
                self.status = VehicleStatus.PICKED_UP
                return True
            return False
    
    def return_vehicle(self, final_mileage: int) -> bool:
        with self.lock:
            if self.status == VehicleStatus.PICKED_UP:
                self.current_mileage = final_mileage
                self.status = VehicleStatus.AVAILABLE
                return True
            return False

class Reservation:
    def __init__(self, reservation_id: str, customer_id: str, vehicle_id: str,
                 pickup_date: datetime, return_date: datetime, pricing_strategy: PricingStrategy):
        self.reservation_id = reservation_id
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.pickup_date = pickup_date
        self.return_date = return_date
        self.status = ReservationStatus.PENDING
        self.pricing_strategy = pricing_strategy
        self.total_price = self._calculate_price()
        self.created_at = datetime.now()
    
    def _calculate_price(self) -> float:
        days = (self.return_date - self.pickup_date).days
        # Assume daily_rate passed separately or hardcoded for demo
        daily_rate = 50.0  # $50/day
        return self.pricing_strategy.calculate_price(days, daily_rate)
    
    def can_modify(self) -> bool:
        hours_until_pickup = (self.pickup_date - datetime.now()).total_seconds() / 3600
        return hours_until_pickup > 24
    
    def calculate_cancellation_penalty(self) -> float:
        hours_until_pickup = (self.pickup_date - datetime.now()).total_seconds() / 3600
        if hours_until_pickup < 48:
            return self.total_price * 0.5
        elif hours_until_pickup < 168:  # 7 days
            return self.total_price * 0.25
        else:
            return 0  # Full refund minus admin fee

class Customer:
    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.reservations = []
        self.created_at = datetime.now()

class Location:
    def __init__(self, location_id: str, name: str, city: str):
        self.location_id = location_id
        self.name = name
        self.city = city
        self.vehicles = []
        self.created_at = datetime.now()
    
    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
    
    def get_available_vehicles(self, vehicle_type: Optional[VehicleType] = None) -> List[Vehicle]:
        available = [v for v in self.vehicles if v.is_available()]
        if vehicle_type:
            available = [v for v in available if v.vehicle_type == vehicle_type]
        return available

# ============================================================================
# CAR RENTAL SYSTEM (SINGLETON)
# ============================================================================

class CarRentalSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.customers = {}
        self.locations = {}
        self.reservations = {}
        self.vehicles = {}
        self.lock = threading.Lock()
    
    def register_customer(self, customer_id: str, name: str, email: str) -> Customer:
        with self.lock:
            customer = Customer(customer_id, name, email)
            self.customers[customer_id] = customer
            return customer
    
    def create_location(self, location_id: str, name: str, city: str) -> Location:
        with self.lock:
            location = Location(location_id, name, city)
            self.locations[location_id] = location
            return location
    
    def add_vehicle_to_location(self, vehicle_id: str, vehicle_type: VehicleType,
                               location_id: str, daily_rate: float) -> Vehicle:
        with self.lock:
            vehicle = Vehicle(vehicle_id, vehicle_type, location_id, daily_rate)
            self.vehicles[vehicle_id] = vehicle
            if location_id in self.locations:
                self.locations[location_id].add_vehicle(vehicle)
            return vehicle
    
    def search_vehicles(self, location_id: str, vehicle_type: Optional[VehicleType],
                       pickup_date: datetime, return_date: datetime) -> List[Vehicle]:
        with self.lock:
            if location_id not in self.locations:
                return []
            location = self.locations[location_id]
            return location.get_available_vehicles(vehicle_type)
    
    def create_reservation(self, customer_id: str, vehicle_id: str,
                          pickup_date: datetime, return_date: datetime,
                          pricing_strategy: PricingStrategy) -> Optional[str]:
        with self.lock:
            if customer_id not in self.customers or vehicle_id not in self.vehicles:
                return None
            
            vehicle = self.vehicles[vehicle_id]
            if not vehicle.reserve():
                return None
            
            reservation_id = f"RES_{datetime.now().timestamp()}"
            reservation = Reservation(reservation_id, customer_id, vehicle_id,
                                     pickup_date, return_date, pricing_strategy)
            self.reservations[reservation_id] = reservation
            
            customer = self.customers[customer_id]
            customer.reservations.append(reservation)
            
            print(f"✓ Reservation created: {reservation_id}, Price: ${reservation.total_price}")
            return reservation_id
    
    def modify_reservation(self, reservation_id: str, new_return_date: datetime) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False
            
            reservation = self.reservations[reservation_id]
            if not reservation.can_modify():
                print("✗ Cannot modify within 24 hours of pickup")
                return False
            
            old_price = reservation.total_price
            reservation.return_date = new_return_date
            reservation.total_price = reservation._calculate_price()
            
            price_diff = reservation.total_price - old_price
            print(f"✓ Reservation modified. Price change: ${price_diff}")
            return True
    
    def pickup_vehicle(self, reservation_id: str) -> bool:
        with self.lock:
            if reservation_id not in self.reservations:
                return False
            
            reservation = self.reservations[reservation_id]
            vehicle = self.vehicles[reservation.vehicle_id]
            
            if vehicle.pickup():
                reservation.status = ReservationStatus.ACTIVE
                print(f"✓ Vehicle picked up. Reservation: {reservation_id}")
                return True
            return False
    
    def return_vehicle(self, reservation_id: str, final_mileage: int) -> Tuple[bool, float]:
        with self.lock:
            if reservation_id not in self.reservations:
                return False, 0
            
            reservation = self.reservations[reservation_id]
            vehicle = self.vehicles[reservation.vehicle_id]
            
            if vehicle.return_vehicle(final_mileage):
                reservation.status = ReservationStatus.COMPLETED
                print(f"✓ Vehicle returned. Total charge: ${reservation.total_price}")
                return True, reservation.total_price
            return False, 0
    
    def cancel_reservation(self, reservation_id: str) -> Tuple[bool, float]:
        with self.lock:
            if reservation_id not in self.reservations:
                return False, 0
            
            reservation = self.reservations[reservation_id]
            if reservation.status == ReservationStatus.ACTIVE:
                print("✗ Cannot cancel active reservation")
                return False, 0
            
            vehicle = self.vehicles[reservation.vehicle_id]
            vehicle.status = VehicleStatus.AVAILABLE
            
            penalty = reservation.calculate_cancellation_penalty()
            refund = reservation.total_price - penalty
            
            reservation.status = ReservationStatus.CANCELLED
            print(f"✓ Reservation cancelled. Penalty: ${penalty}, Refund: ${refund}")
            return True, refund

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_search_and_reserve():
    print("\n" + "="*70)
    print("DEMO 1: SEARCH & RESERVE")
    print("="*70)
    
    system = CarRentalSystem()
    
    customer = system.register_customer("C001", "Alice", "alice@example.com")
    print(f"✓ Customer registered: {customer.name}")
    
    loc = system.create_location("LOC001", "SF Downtown", "San Francisco")
    print(f"✓ Location created: {loc.name}")
    
    for i in range(3):
        system.add_vehicle_to_location(f"V{i}", VehicleType.ECONOMY, "LOC001", 50.0)
    print(f"✓ 3 vehicles added")
    
    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=3)
    
    vehicles = system.search_vehicles("LOC001", VehicleType.ECONOMY, pickup, return_date)
    print(f"✓ Found {len(vehicles)} available vehicles")
    
    res_id = system.create_reservation("C001", "V0", pickup, return_date, DailyPricingStrategy())
    print(f"✓ Reservation: {res_id}")

def demo_2_modify_reservation():
    print("\n" + "="*70)
    print("DEMO 2: MODIFY RESERVATION")
    print("="*70)
    
    system = CarRentalSystem()
    
    customer = system.register_customer("C002", "Bob", "bob@example.com")
    loc = system.create_location("LOC002", "NYC", "New York")
    system.add_vehicle_to_location("V1", VehicleType.SEDAN, "LOC002", 75.0)
    
    pickup = datetime.now() + timedelta(days=2)
    return_date = datetime.now() + timedelta(days=4)
    
    res_id = system.create_reservation("C002", "V1", pickup, return_date, DailyPricingStrategy())
    
    new_return = datetime.now() + timedelta(days=5)
    system.modify_reservation(res_id, new_return)

def demo_3_pickup_vehicle():
    print("\n" + "="*70)
    print("DEMO 3: PICKUP VEHICLE")
    print("="*70)
    
    system = CarRentalSystem()
    
    customer = system.register_customer("C003", "Charlie", "charlie@example.com")
    loc = system.create_location("LOC003", "LA", "Los Angeles")
    system.add_vehicle_to_location("V2", VehicleType.SUV, "LOC003", 100.0)
    
    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=3)
    
    res_id = system.create_reservation("C003", "V2", pickup, return_date, WeeklyPricingStrategy())
    system.pickup_vehicle(res_id)

def demo_4_return_vehicle():
    print("\n" + "="*70)
    print("DEMO 4: RETURN VEHICLE")
    print("="*70)
    
    system = CarRentalSystem()
    
    customer = system.register_customer("C004", "Diana", "diana@example.com")
    loc = system.create_location("LOC004", "Seattle", "Seattle")
    system.add_vehicle_to_location("V3", VehicleType.LUXURY, "LOC004", 150.0)
    
    pickup = datetime.now() + timedelta(days=1)
    return_date = datetime.now() + timedelta(days=3)
    
    res_id = system.create_reservation("C004", "V3", pickup, return_date, MonthlyPricingStrategy())
    system.pickup_vehicle(res_id)
    system.return_vehicle(res_id, 25000)

def demo_5_cancel_reservation():
    print("\n" + "="*70)
    print("DEMO 5: CANCEL RESERVATION")
    print("="*70)
    
    system = CarRentalSystem()
    
    customer = system.register_customer("C005", "Eve", "eve@example.com")
    loc = system.create_location("LOC005", "Boston", "Boston")
    system.add_vehicle_to_location("V4", VehicleType.ECONOMY, "LOC005", 50.0)
    
    pickup = datetime.now() + timedelta(days=10)
    return_date = datetime.now() + timedelta(days=12)
    
    res_id = system.create_reservation("C005", "V4", pickup, return_date, DailyPricingStrategy())
    system.cancel_reservation(res_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚗 CAR RENTAL SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_search_and_reserve()
    demo_2_modify_reservation()
    demo_3_pickup_vehicle()
    demo_4_return_vehicle()
    demo_5_cancel_reservation()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Design Patterns Explained

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Singleton** | `CarRentalSystem` manages all operations | Centralized state, no conflicts |
| **Strategy** | DailyPricingStrategy, WeeklyPricingStrategy, MonthlyPricingStrategy | Pluggable pricing, easy to add new models |
| **Observer** | Notify customers on reservation changes | Decoupled notifications |
| **Factory** | Centralized Reservation creation | Consistent initialization, pricing calc |
| **State** | VehicleStatus, ReservationStatus enums | Clear state transitions, prevent invalid ops |

---

## Key Business Logic

- **Availability**: Vehicle is available only if status = AVAILABLE and no overlapping reservations
- **Pricing**: Calculate based on duration + selected strategy (daily/weekly/monthly discounts)
- **Cancellation**: Penalty based on how close to pickup date (< 48h = 50%, < 7d = 25%, else refund)
- **Modification**: Can only modify if > 24h before pickup
- **Pickup/Return**: Require vehicle status transitions and mileage tracking

---

## Summary

✅ **Singleton** for global coordination
✅ **Strategy** for pluggable pricing strategies
✅ **Multi-location** inventory management
✅ **Reservation** lifecycle management (pending → active → completed)
✅ **Cancellation penalties** based on timing
✅ **Thread-safe** operations with locks
✅ **Search & filter** by location, type, dates
✅ **Pricing flexibility** (daily/weekly/monthly)
✅ **Vehicle tracking** (status, mileage, location)
✅ **Business analytics** ready (revenue, utilization)

**Key Takeaway**: Car rental system demonstrates complex reservation management with multi-location support, flexible pricing, and clear state transitions. Scalability through sharding, caching, and async processing.
