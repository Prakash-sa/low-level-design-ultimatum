# Circinfo (Ride Sharing) — 75-Minute Interview Guide

## Quick Start Overview

## What You're Building
Real-time ride-sharing platform (Uber/Lyft-style) connecting riders with drivers. Features dynamic surge pricing, intelligent matching, and rating system.

---

## 75-Minute Timeline

| Time | Phase | Focus |
|------|-------|-------|
| 0-5 min | **Requirements** | Clarify functional (ride request, driver matching, pricing, ratings) and non-functional (concurrency, scale) |
| 5-15 min | **Architecture** | Design 5 core entities, choose 5 patterns (Singleton, Strategy×2, Observer, State) |
| 15-35 min | **Entities** | Implement Rider, Driver, Vehicle, Ride, Location with business logic |
| 35-55 min | **Logic** | Implement pricing strategies, matching algorithms, state machine |
| 55-70 min | **Integration** | Wire RideSharingSystem singleton, add observers, demo 5 scenarios |
| 70-75 min | **Demo** | Walk through working code, explain patterns, answer questions |

---

## Core Entities (3-Sentence Each)

### 1. Location
Geographic point with latitude/longitude. Uses Haversine formula to calculate distance to other locations. Foundation for driver matching and fare calculation.

### 2. Vehicle
Represents driver's car with type (ECONOMY/PREMIUM/SHARED), model, and capacity. Tracks current location for matching. Associated one-to-one with Driver.

### 3. Driver
Has Vehicle, current location, availability flag, and rating. Accepts rides (sets unavailable), completes rides (sets available), earns 75% of fare. Rating calculated from total_rating / rides_rated.

### 4. Rider
Has wallet balance and rating. Requests rides (checks affordability), pays fares (deducts from wallet), rates drivers. Tracks total spending.

### 5. Ride (State Machine)
Connects Rider+Driver with pickup/dropoff Locations. State machine: REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED. Stores estimated vs actual distance/fare, both ratings.

---

## 5 Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Why Each Matters)

### 1. Singleton - RideSharingSystem
**What**: Single instance coordinates all rides  
**Why**: Centralized driver/rider pools, consistent demand multiplier, thread-safe state  
**Talk Point**: "Ensures all ride requests see same available driver list. Alternative: Dependency injection for testing."

### 2. Strategy - Pricing Algorithms
**What**: FixedPricing, SurgePricing, PeakHourPricing  
**Why**: Runtime flexibility for A/B testing pricing models  
**Talk Point**: "Can switch from fixed to surge pricing during high demand without code changes. Easy to add SeasonalPricing."

### 3. Strategy - Matching Algorithms
**What**: NearestDriverMatcher, RatingBasedMatcher  
**Why**: Optimize for different goals (speed vs quality)  
**Talk Point**: "Nearest minimizes ETA, Rating-based maximizes satisfaction. System can choose based on rider tier."

### 4. Observer - Notifications
**What**: RiderNotifier, DriverNotifier, AdminNotifier  
**Why**: Decoupled event handling, extensible channels (SMS, push, email)  
**Talk Point**: "Adding SMS notifications just requires new SMSNotifier observer. No changes to RideSharingSystem."

### 5. State - Ride Lifecycle
**What**: REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED  
**Why**: Prevents invalid operations (can't complete ride before starting)  
**Talk Point**: "State machine enforces business rules. Can't accept ride with status COMPLETED. Raises ValueError."

---

## Key Algorithms (30-Second Explanations)

### Haversine Distance
```python
# Calculate distance between two lat/long points
dlat = lat2 - lat1
dlon = lon2 - lon1
a = sin(dlat/2)^2 + cos(lat1) * cos(lat2) * sin(dlon/2)^2
c = 2 * asin(sqrt(a))
distance = 6371 * c  # Earth radius in km
```
**Why**: Accurate for <100km, handles Earth's curvature, fast computation.

### Demand Multiplier
```python
ratio = active_rides / available_drivers
if ratio < 0.5: multiplier = 1.0x
if 0.5 <= ratio < 1.0: multiplier = 1.5x
if ratio >= 1.0: multiplier = 2.0x
```
**Why**: Incentivizes drivers during high demand, balances supply/demand.

### Nearest Driver Matching
```python
# Filter by vehicle type + location exists
matching_drivers = [d for d in available if d.vehicle.type == ride.type]
# Return closest
return min(matching_drivers, key=lambda d: d.location.distance_to(pickup))
```
**Why**: O(n) scan, simple logic, minimizes rider wait time.

---

## Interview Talking Points

### Opening (0-5 min)
- "I'll design a ride-sharing platform with real-time matching and dynamic pricing"
- "Core challenge: concurrent ride requests, driver availability, fair pricing"
- "Will use Singleton for coordination, Strategy for algorithms, Observer for notifications"

### During Implementation (15-55 min)
- "Using Haversine formula for accurate distance calculation"
- "State machine prevents invalid transitions like completing ride before starting"
- "Thread lock protects request_ride() to prevent double-booking drivers"
- "Surge pricing calculated from active rides / available drivers ratio"

### Closing Demo (70-75 min)
- "Demo 1: Setup 3 drivers, 2 riders - shows registration"
- "Demo 2: Successful ride with payment and ratings - shows happy path"
- "Demo 3: Surge pricing during 15 active rides - shows 1.5x multiplier"
- "Demo 4: Rating-based matching picks highest-rated driver - shows strategy swap"
- "Demo 5: Insufficient balance rejection - shows validation"

---

## Success Checklist

- [ ] Draw system architecture with 5 entities
- [ ] Explain Singleton justification (centralized state)
- [ ] Show 2 pricing strategies side-by-side
- [ ] Demonstrate state machine with valid/invalid transitions
- [ ] Describe observer pattern event flow
- [ ] Calculate Haversine distance on whiteboard
- [ ] Discuss concurrency with lock mechanism
- [ ] Propose 2 scalability improvements (geohashing, sharding)
- [ ] Answer fraud detection question (GPS validation, velocity checks)
- [ ] Run working code with 5 demos

---

## Anti-Patterns to Avoid

**DON'T**:
- Hard-code pricing logic in RideSharingSystem (violates Strategy)
- Create multiple RideSharingSystem instances (violates Singleton)
- Allow direct state changes without validation (violates State)
- Tightly couple notifications to ride logic (violates Observer)
- Skip concurrency discussion ("I'll handle it later")

**DO**:
- Make strategies pluggable with abstract base class
- Use thread locks for critical sections (request_ride, complete_ride)
- Validate state transitions in Ride methods
- Explain trade-offs (Haversine vs Vincenty, Nearest vs Rating-based)
- Propose optimizations (geohashing, caching, sharding)

---

## 3 Advanced Follow-Ups (Be Ready)

### 1. Ride-Sharing (Multiple Riders)
"Add Ride.riders[] list. Match riders with similar routes (within 2km detour). Calculate fare split proportional to distance. Implement pickup priority based on ratings."

### 2. Fraud Detection
"Validate GPS accuracy threshold. Compare consecutive location updates for impossible speeds. Flag accounts with high cancellation rates. Require payment method verification."

### 3. Scaling to 1M Concurrent Rides
"Microservices for matching service. Redis cache for driver availability. Kafka for async requests. Database sharding by city_id. CDN for static assets. Load balancer with auto-scaling."

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

"I designed a ride-sharing system with 5 core entities: Rider, Driver, Vehicle, Ride, Location. Uses Singleton for system coordination, Strategy pattern for pricing (Fixed/Surge/PeakHour) and matching (Nearest/RatingBased), Observer for notifications, and State machine for ride lifecycle. Key algorithm is Haversine distance for geo-matching. Handles concurrency with thread locks. Demo shows surge pricing (1.5x during high demand), rating-based matching, and payment validation. Scales with geohashing for driver partitioning and sharding by city."

---

## What Interviewers Look For

1. **Clarity**: Can you explain complex logic simply?
2. **Patterns**: Do you recognize when to apply design patterns?
3. **Trade-offs**: Do you discuss pros/cons of approaches?
4. **Scalability**: Can you think beyond single-machine solutions?
5. **Code Quality**: Is code clean, readable, well-structured?
6. **Problem-Solving**: How do you handle edge cases?
7. **Communication**: Do you think out loud?

---

## Final Tips

- **Draw first, code later**: Spend 10 minutes on architecture diagram
- **State assumptions clearly**: "Assuming lat/long available from GPS"
- **Test edge cases**: No drivers, insufficient balance, concurrent requests
- **Explain as you code**: "Adding lock here to prevent race condition"
- **Time management**: Leave 5 minutes for demo, don't over-engineer

**Good luck!** Run the code, understand the patterns, and explain trade-offs confidently.


## 75-Minute Guide

## System Overview
**Real-time ride-sharing platform** connecting riders with drivers, featuring dynamic pricing, location-based matching, rating system, and ride tracking. Think Uber/Lyft simplified.

**Core Challenge**: Real-time driver-rider matching, surge pricing, location tracking, and concurrent ride management.

---

## Requirements Clarification (0-5 min)

### Functional Requirements
1. **Rider Management**: Register riders, wallet balance, ride history
2. **Driver Management**: Register drivers with vehicles, availability status, earnings tracking
3. **Ride Request**: Riders request rides with pickup/dropoff locations
4. **Driver Matching**: Match nearest available driver (or rating-based)
5. **Pricing**: Dynamic pricing with surge multipliers
6. **Ride Lifecycle**: REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED → RATED
7. **Rating System**: Both riders and drivers rate each other (1-5 stars)
8. **Notifications**: Real-time updates to riders and drivers
9. **Payment**: Deduct from rider wallet, credit to driver

### Non-Functional Requirements
- **Performance**: Match driver in <3 seconds for 10K concurrent requests
- **Scale**: 100K drivers, 1M riders, 10K concurrent rides
- **Availability**: 99.9% uptime
- **Concurrency**: Thread-safe operations

### Key Design Decisions
1. **Location Representation**: Latitude/longitude with Haversine distance calculation
2. **Matching Strategy**: Strategy pattern (Nearest vs Rating-based)
3. **Pricing Strategy**: Strategy pattern (Fixed, Surge, Peak Hour)
4. **Notifications**: Observer pattern for real-time updates
5. **Game Coordination**: Singleton RideSharingSystem

---

## Architecture & Design (5-15 min)

### System Architecture

```
RideSharingSystem (Singleton)
├── Drivers Map
│   └── Driver → Vehicle → Location
├── Riders Map
│   └── Rider → Wallet Balance → Ratings
├── Active Rides
│   └── Ride → Status → Driver/Rider → Locations
├── Pricing Strategy (pluggable)
│   ├── FixedPricing
│   ├── SurgePricing
│   └── PeakHourPricing
├── Matching Strategy (pluggable)
│   ├── NearestDriverMatcher
│   └── RatingBasedMatcher
└── Observers
    ├── RiderNotifier
    ├── DriverNotifier
    └── AdminNotifier
```

### Design Patterns Used

1. **Singleton**: RideSharingSystem (one instance coordinates all rides)
2. **Strategy**: Pricing algorithms (Fixed/Surge/PeakHour)
3. **Strategy**: Matching algorithms (Nearest/RatingBased)
4. **Observer**: Real-time notifications (Rider/Driver/Admin)
5. **State**: Ride lifecycle (REQUESTED/ACCEPTED/IN_PROGRESS/COMPLETED)
6. **Factory**: Ride creation with automatic ID generation

---

## Core Entities (15-35 min)

### 1. Location Class

```python
import math

class Location:
    """Geographic location with distance calculation"""
    def __init__(self, latitude: float, longitude: float, address: str):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance using Haversine formula (in km)"""
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Earth radius in km
```

**Key Points**:
- Haversine formula for accurate distance on sphere
- Returns distance in kilometers
- Used for driver matching and fare calculation

### 2. Vehicle & Driver Classes

```python
from enum import Enum

class VehicleType(Enum):
    ECONOMY = "economy"
    PREMIUM = "premium"
    SHARED = "shared"

class Vehicle:
    """Vehicle with type and capacity"""
    def __init__(self, vehicle_id: str, model: str, vehicle_type: VehicleType, 
                 registration: str, capacity: int):
        self.vehicle_id = vehicle_id
        self.model = model
        self.vehicle_type = vehicle_type
        self.registration = registration
        self.capacity = capacity
        self.current_location = None

class Driver:
    """Driver with availability and ratings"""
    def __init__(self, driver_id: str, name: str, phone: str, vehicle: Vehicle):
        self.driver_id = driver_id
        self.name = name
        self.phone = phone
        self.vehicle = vehicle
        self.current_location = None
        self.is_available = True
        self.total_rides = 0
        self.total_rating = 0.0
        self.rides_rated = 0
        self.earnings = 0.0
    
    def get_average_rating(self) -> float:
        """Calculate average driver rating"""
        if self.rides_rated == 0:
            return 5.0  # Default for new drivers
        return self.total_rating / self.rides_rated
    
    def update_location(self, location: Location):
        """Update driver's current location"""
        self.current_location = location
        self.vehicle.current_location = location
```

**Key Points**:
- Driver has one Vehicle
- Availability flag prevents double-booking
- Rating calculated from total/count
- Earnings track driver's income

### 3. Rider Class

```python
class Rider:
    """Rider with wallet and ratings"""
    def __init__(self, rider_id: str, name: str, phone: str):
        self.rider_id = rider_id
        self.name = name
        self.phone = phone
        self.wallet_balance = 500.0  # Initial balance
        self.total_rides = 0
        self.total_spent = 0.0
        self.total_rating = 0.0
        self.rides_rated = 0
    
    def get_average_rating(self) -> float:
        """Calculate average rider rating"""
        if self.rides_rated == 0:
            return 5.0
        return self.total_rating / self.rides_rated
    
    def can_afford_ride(self, amount: float) -> bool:
        """Check if rider can afford the fare"""
        return self.wallet_balance >= amount
    
    def deduct_payment(self, amount: float) -> bool:
        """Deduct fare from wallet"""
        if self.can_afford_ride(amount):
            self.wallet_balance -= amount
            self.total_spent += amount
            return True
        return False
```

**Key Points**:
- Wallet-based payment (no external payment gateway)
- Track total spending
- Rating affects matching priority

### 4. Ride Class (State Pattern)

```python
from datetime import datetime

class RideStatus(Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Ride:
    """Ride with lifecycle state management"""
    def __init__(self, ride_id: str, rider: Rider, pickup: Location, 
                 dropoff: Location, vehicle_type: VehicleType):
        self.ride_id = ride_id
        self.rider = rider
        self.driver = None
        self.pickup_location = pickup
        self.dropoff_location = dropoff
        self.vehicle_type = vehicle_type
        self.status = RideStatus.REQUESTED
        self.requested_time = datetime.now()
        self.accepted_time = None
        self.completed_time = None
        self.estimated_distance = pickup.distance_to(dropoff)
        self.actual_distance = 0.0
        self.estimated_fare = 0.0
        self.actual_fare = 0.0
        self.driver_rating = None
        self.rider_rating = None
    
    def accept_ride(self, driver: Driver):
        """Transition: REQUESTED → ACCEPTED"""
        if self.status != RideStatus.REQUESTED:
            raise ValueError("Cannot accept ride with status %s" % self.status.value)
        self.driver = driver
        self.status = RideStatus.ACCEPTED
        self.accepted_time = datetime.now()
    
    def start_ride(self):
        """Transition: ACCEPTED → IN_PROGRESS"""
        if self.status != RideStatus.ACCEPTED:
            raise ValueError("Cannot start ride with status %s" % self.status.value)
        self.status = RideStatus.IN_PROGRESS
    
    def complete_ride(self, final_location: Location):
        """Transition: IN_PROGRESS → COMPLETED"""
        if self.status != RideStatus.IN_PROGRESS:
            raise ValueError("Cannot complete ride with status %s" % self.status.value)
        self.status = RideStatus.COMPLETED
        self.completed_time = datetime.now()
        self.actual_distance = self.pickup_location.distance_to(final_location)
```

**Key Points**:
- State machine prevents invalid transitions
- Tracks estimated vs actual distance/fare
- Timestamps for analytics

---

## Business Logic (35-55 min)

### Pricing Strategy Pattern

```python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        pass

class FixedPricing(PricingStrategy):
    """Fixed pricing: base + per-km rate"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * demand_multiplier

class SurgePricing(PricingStrategy):
    """Surge pricing during high demand"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        # demand_multiplier ranges from 1.0 to 3.0+
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * max(1.0, demand_multiplier)

class PeakHourPricing(PricingStrategy):
    """Peak hour pricing (rush hours)"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    PEAK_MULTIPLIER = 1.5  # 50% increase
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        current_hour = datetime.now().hour
        is_peak = current_hour in [7, 8, 9, 17, 18, 19]  # Morning/evening rush
        
        multiplier = self.PEAK_MULTIPLIER if is_peak else 1.0
        multiplier *= demand_multiplier
        
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * multiplier
```

**Interview Points**:
- Strategy pattern allows runtime switching
- Surge multiplier based on demand (active rides / available drivers)
- Peak hour detection based on time of day

### Matching Strategy Pattern

```python
from typing import List, Optional

class MatchingStrategy(ABC):
    """Abstract matching strategy"""
    @abstractmethod
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        pass

class NearestDriverMatcher(MatchingStrategy):
    """Match with nearest available driver"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type]
        
        if not matching_drivers:
            return None
        
        # Return nearest driver
        return min(matching_drivers, 
                  key=lambda d: d.current_location.distance_to(ride.pickup_location))

class RatingBasedMatcher(MatchingStrategy):
    """Match with highest-rated driver (within acceptable distance)"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type and max distance (5km)
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type
                           and d.current_location.distance_to(ride.pickup_location) <= 5.0]
        
        if not matching_drivers:
            return None
        
        # Return highest-rated driver
        return max(matching_drivers, key=lambda d: d.get_average_rating())
```

**Interview Points**:
- Nearest prioritizes speed (lower ETA)
- Rating-based prioritizes quality
- Both filter by vehicle type first

---

## Integration & Patterns (55-70 min)

### Observer Pattern - Notifications

```python
class RideObserver(ABC):
    """Observer interface for ride events"""
    @abstractmethod
    def update(self, event: str, ride: Ride, message: str):
        pass

class RiderNotifier(RideObserver):
    """Notify rider of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        print("[RIDER] %s: %s" % (ride.rider.name, message))

class DriverNotifier(RideObserver):
    """Notify driver of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        if ride.driver:
            print("[DRIVER] %s: %s" % (ride.driver.name, message))

class AdminNotifier(RideObserver):
    """Notify admin of critical events"""
    def update(self, event: str, ride: Ride, message: str):
        if event in ["payment_failed", "no_driver", "ride_cancelled"]:
            print("[ADMIN] Ride %s: %s" % (ride.ride_id, message))
```

### Singleton - RideSharingSystem

```python
import threading

class RideSharingSystem:
    """Singleton controller for ride-sharing platform"""
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
            self.drivers = {}
            self.riders = {}
            self.rides = {}
            self.active_rides = []
            self.completed_rides = []
            self.observers = []
            self.pricing_strategy = SurgePricing()
            self.matching_strategy = NearestDriverMatcher()
            self.demand_multiplier = 1.0
            self.ride_counter = 0
            self.lock = threading.Lock()
            self.initialized = True
    
    def request_ride(self, rider: Rider, pickup: Location, 
                    dropoff: Location, vehicle_type: VehicleType) -> Optional[Ride]:
        """Rider requests a ride"""
        with self.lock:
            # Create ride
            self.ride_counter += 1
            ride_id = "RIDE_%05d" % self.ride_counter
            ride = Ride(ride_id, rider, pickup, dropoff, vehicle_type)
            
            # Calculate estimated fare
            ride.estimated_fare = self.pricing_strategy.calculate_fare(
                ride.estimated_distance, self.demand_multiplier)
            
            # Check affordability
            if not rider.can_afford_ride(ride.estimated_fare):
                self._notify_observers("insufficient_funds", ride, 
                    "Insufficient balance. Required: $%.2f" % ride.estimated_fare)
                return None
            
            # Find and assign driver
            available_drivers = [d for d in self.drivers.values() 
                               if d.is_available and d.current_location]
            matched_driver = self.matching_strategy.find_driver(ride, available_drivers)
            
            if not matched_driver:
                self._notify_observers("no_driver", ride, "No driver available")
                return None
            
            # Auto-accept (for demo)
            matched_driver.accept_ride(ride)
            matched_driver.is_available = False
            self.rides[ride_id] = ride
            self.active_rides.append(ride)
            
            self._notify_observers("ride_accepted", ride, 
                "Driver %s accepted. Fare: $%.2f" % (matched_driver.name, ride.estimated_fare))
            
            return ride
    
    def complete_ride(self, ride: Ride, final_location: Location, 
                     driver_rating: int, rider_rating: int):
        """Complete ride with payment and ratings"""
        with self.lock:
            ride.complete_ride(final_location)
            ride.actual_fare = self.pricing_strategy.calculate_fare(
                ride.actual_distance, self.demand_multiplier)
            
            # Process payment
            if ride.rider.deduct_payment(ride.actual_fare):
                ride.driver.earnings += ride.actual_fare * 0.75  # Driver gets 75%
                
                # Add ratings
                if 1 <= driver_rating <= 5:
                    ride.driver_rating = driver_rating
                    ride.driver.total_rating += driver_rating
                    ride.driver.rides_rated += 1
                
                if 1 <= rider_rating <= 5:
                    ride.rider_rating = rider_rating
                    ride.rider.total_rating += rider_rating
                    ride.rider.rides_rated += 1
                
                ride.driver.is_available = True
                self.active_rides.remove(ride)
                self.completed_rides.append(ride)
                
                self._notify_observers("ride_completed", ride,
                    "Completed. Fare: $%.2f, Ratings: D=%d/5, R=%d/5" % 
                    (ride.actual_fare, driver_rating, rider_rating))
                
                return True
            return False
    
    def _notify_observers(self, event: str, ride: Ride, message: str):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, ride, message)
```

---

## Interview Q&A (12 Questions)

### Basic (0-5 min)

1. **"What are the core entities in a ride-sharing system?"**
   - Answer: Rider, Driver, Vehicle, Ride, Location. Ride connects Rider+Driver with pickup/dropoff Locations.

2. **"How do you calculate distance between two locations?"**
   - Answer: Haversine formula using lat/long. Accounts for Earth's curvature. Returns distance in km.

3. **"What are the ride statuses?"**
   - Answer: REQUESTED (rider creates) → ACCEPTED (driver accepts) → IN_PROGRESS (started) → COMPLETED (finished) → RATED

### Intermediate (5-10 min)

4. **"How does driver matching work?"**
   - Answer: Strategy pattern. NearestDriverMatcher finds closest available driver. RatingBasedMatcher finds highest-rated within 5km. Both filter by vehicle type first.

5. **"Explain surge pricing."**
   - Answer: Demand multiplier (1.0-3.0x) applied to base fare. Calculated from active_rides / available_drivers ratio. Incentivizes more drivers during high demand.

6. **"How do you prevent double-booking a driver?"**
   - Answer: Driver.is_available flag. Set to False when ride accepted. Protected by system-level lock in request_ride(). Reset to True when ride completes.

7. **"How are ratings calculated?"**
   - Answer: total_rating / rides_rated. Each completed ride adds 1-5 stars to total. New drivers/riders default to 5.0. Used for matching priority.

### Advanced (10-15 min)

8. **"How would you handle concurrent ride requests?"**
   - Answer: System-level lock protects request_ride(). Alternative: Use database transactions with row-level locking on driver availability. Queue requests with priority (by rider rating).

9. **"How would you optimize driver matching for 100K drivers?"**
   - Answer: Geohashing to partition by location. Index drivers in R-tree or Quadtree. Only search nearby grid cells. Cache available driver list per region. Use Redis for real-time updates.

10. **"How would you detect and prevent fraud (fake rides)?"**
    - Answer: Validate location GPS accuracy. Check ride distance vs actual path (geofencing). Flag riders with high cancellation rate. Require payment method verification. Monitor velocity (impossible speeds).

11. **"How would you implement ride-sharing (multiple riders)?"**
    - Answer: Add Ride.riders[] list. Match riders with similar routes (origin/destination within 2km, time window <10min). Calculate fare split. Priority-based pickup order.

12. **"How would you scale to multiple cities?"**
    - Answer: Partition by city_id. Separate driver/rider pools per city. Regional pricing strategies. Cross-city coordination for airport pickups. Use sharding on city_id in database.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|------------|
| **Single Responsibility** | Ride handles lifecycle; Driver handles availability; PricingStrategy handles fare calculation |
| **Open/Closed** | New pricing/matching strategies without modifying RideSharingSystem |
| **Liskov Substitution** | All PricingStrategy/MatchingStrategy subclasses interchangeable |
| **Interface Segregation** | Observer only requires update(); Strategy only requires one method |
| **Dependency Inversion** | RideSharingSystem depends on abstract Strategy/Observer, not concrete classes |

---

## UML Diagram

```
┌────────────────────────────────────────────────────┐
│         RideSharingSystem (Singleton)              │
├────────────────────────────────────────────────────┤
│ - drivers: Dict[str, Driver]                       │
│ - riders: Dict[str, Rider]                         │
│ - active_rides: List[Ride]                         │
│ - pricing_strategy: PricingStrategy                │
│ - matching_strategy: MatchingStrategy              │
│ - observers: List[RideObserver]                    │
│ - demand_multiplier: float                         │
├────────────────────────────────────────────────────┤
│ + request_ride()                                   │
│ + complete_ride()                                  │
│ + update_demand_multiplier()                       │
└────────────────────────────────────────────────────┘
           │                   │
           ▼                   ▼
    ┌──────────┐        ┌──────────┐
    │  Driver  │        │  Rider   │
    ├──────────┤        ├──────────┤
    │ vehicle  │        │ wallet   │
    │ location │        │ balance  │
    │ rating   │        │ rating   │
    └──────────┘        └──────────┘
           │
           ▼
    ┌──────────┐
    │ Vehicle  │
    ├──────────┤
    │ type     │
    │ capacity │
    └──────────┘

┌─────────────────────────────────────┐
│           Ride (State)              │
├─────────────────────────────────────┤
│ status: REQUESTED/ACCEPTED/         │
│         IN_PROGRESS/COMPLETED       │
│ rider, driver                       │
│ pickup, dropoff: Location           │
│ estimated_fare, actual_fare         │
├─────────────────────────────────────┤
│ + accept_ride()                     │
│ + start_ride()                      │
│ + complete_ride()                   │
└─────────────────────────────────────┘

┌────────────────────────────────────┐
│    PricingStrategy (Abstract)      │
├────────────────────────────────────┤
│ + calculate_fare(distance, demand) │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴────────────┬──────────────┐
    │                   │              │
FixedPricing    SurgePricing   PeakHourPricing

┌────────────────────────────────────┐
│   MatchingStrategy (Abstract)      │
├────────────────────────────────────┤
│ + find_driver(ride, drivers)       │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────────┐
    │                     │
NearestDriverMatcher  RatingBasedMatcher

┌────────────────────────────────────┐
│    RideObserver (Abstract)         │
├────────────────────────────────────┤
│ + update(event, ride, message)     │
└────────────────────────────────────┘
           △
           │ implements
    ┌──────┴──────────┬──────────────┐
    │                 │              │
RiderNotifier  DriverNotifier  AdminNotifier

State Machine:
REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED
    ↓           ↓           ↓
CANCELLED   CANCELLED   CANCELLED
```

---

## 5 Demo Scenarios

### Demo 1: Setup & Registration
- Register 3 drivers with different vehicle types
- Register 2 riders with wallet balances
- Display system statistics

### Demo 2: Successful Ride
- Rider requests economy ride
- System matches nearest driver
- Display estimated fare with surge pricing
- Complete ride with ratings
- Verify payment processed

### Demo 3: Surge Pricing Effect
- Create 15 active rides (high demand)
- System updates surge multiplier to 1.5x
- Rider requests ride, sees surge fare
- Complete ride, compare base vs surge fare

### Demo 4: Rating-Based Matching
- Switch to RatingBasedMatcher
- Request ride, verify highest-rated driver matched
- Complete ride with 5-star rating
- Verify driver rating updated

### Demo 5: Insufficient Balance
- Rider with low balance requests ride
- System calculates fare
- Request rejected due to insufficient funds
- Notification sent to rider

---

## Key Implementation Notes

### Distance Calculation
- Haversine formula accurate for <100km
- For longer distances, use Vincenty formula
- Returns straight-line distance (not road distance)

### Concurrency Handling
- System-level lock protects request_ride()
- Driver.is_available flag prevents double-booking
- Alternative: Optimistic locking with version numbers

### Performance Optimization
- Cache available drivers per region
- Index drivers by location (geohash/R-tree)
- Lazy load completed rides
- Use connection pooling for database

### Testing Strategy
1. Unit test each pricing strategy
2. Unit test each matching strategy
3. Integration test ride lifecycle
4. Concurrency test (100 simultaneous requests)
5. Edge cases: no drivers, insufficient balance, invalid ratings


## Detailed Design Reference

## System Overview
Real-time ride-sharing platform connecting riders with drivers. Features dynamic pricing, intelligent driver matching, rating system, and concurrent ride management.

---

## Core Entities

| Entity | Attributes | Responsibilities |
|--------|-----------|------------------|
| **Rider** | rider_id, name, phone, wallet_balance, total_rating, rides_rated | Request rides, pay fares, rate drivers |
| **Driver** | driver_id, name, phone, vehicle, current_location, is_available, earnings, total_rating | Accept rides, update location, earn income, get rated |
| **Vehicle** | vehicle_id, model, vehicle_type (ECONOMY/PREMIUM/SHARED), registration, capacity | Represent driver's transportation asset |
| **Ride** | ride_id, rider, driver, pickup_location, dropoff_location, status, estimated_fare, actual_fare, ratings | Track ride lifecycle, store trip details |
| **Location** | latitude, longitude, address | Store geographic coordinates, calculate distances |
| **RideSharingSystem** | drivers, riders, active_rides, pricing_strategy, matching_strategy, observers | Coordinate all operations, manage state |

---

## Design Patterns Implementation

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | RideSharingSystem - single instance coordinates all rides | Centralized state management, thread-safe operations |
| **Strategy** | Pricing algorithms (Fixed/Surge/PeakHour) | Runtime pricing flexibility, A/B testing support |
| **Strategy** | Matching algorithms (Nearest/RatingBased) | Optimize for different goals (speed vs quality) |
| **Observer** | Real-time notifications (Rider/Driver/Admin) | Decoupled event handling, extensible notification channels |
| **State** | Ride lifecycle state machine | Enforces valid transitions, prevents illegal operations |

---

## Pricing Strategies Comparison

| Strategy | Base Fare | Per-KM Rate | Multiplier Logic | Use Case |
|----------|-----------|-------------|------------------|----------|
| **FixedPricing** | $2.00 | $1.50 | Constant 1.0x | Predictable pricing, low-demand periods |
| **SurgePricing** | $2.00 | $1.50 | 1.0x - 3.0x (demand-based) | Peak hours, high demand areas |
| **PeakHourPricing** | $2.00 | $1.50 | 1.5x during 7-9am, 5-7pm | Commute hours, predictable patterns |

**Demand Multiplier Calculation**:
```
ratio = active_rides / available_drivers
if ratio < 0.5: multiplier = 1.0x
if 0.5 <= ratio < 1.0: multiplier = 1.5x
if ratio >= 1.0: multiplier = 2.0x
```

---

## Matching Algorithms

### Nearest Driver Matcher
- **Goal**: Minimize ETA (Estimated Time of Arrival)
- **Logic**: Filter by vehicle type → Select closest driver by Haversine distance
- **Pros**: Fast pickups, lower customer wait time
- **Cons**: May match with lower-rated drivers

### Rating-Based Matcher
- **Goal**: Maximize service quality
- **Logic**: Filter by vehicle type + within 5km → Select highest-rated driver
- **Pros**: Better customer experience, rewards high-performing drivers
- **Cons**: Potentially longer wait times

---

## Ride Lifecycle State Machine

```
REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED
    ↓           ↓           ↓
CANCELLED   CANCELLED   CANCELLED
```

**Valid Transitions**:
- REQUESTED → ACCEPTED: Driver accepts ride
- ACCEPTED → IN_PROGRESS: Driver starts ride
- IN_PROGRESS → COMPLETED: Ride reaches destination
- Any → CANCELLED: Rider/Driver/System cancels

**Invalid Transitions** (throw ValueError):
- ACCEPTED → COMPLETED (must go through IN_PROGRESS)
- COMPLETED → IN_PROGRESS (cannot restart completed ride)

---

## Haversine Distance Formula

```python
def distance_to(self, other):
    lat1, lon1 = radians(self.latitude), radians(self.longitude)
    lat2, lon2 = radians(other.latitude), radians(other.longitude)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth radius in km
```

**Accuracy**: ±0.5% for distances <100km
**Alternative**: Vincenty formula (higher accuracy, more computation)

---

## Observer Pattern Event Types

| Event | Triggered When | Notifiers Called | Example Message |
|-------|----------------|------------------|----------------|
| `ride_accepted` | Driver accepts request | Rider, Driver | "Driver Alice accepted. Fare: $12.50" |
| `ride_started` | Ride begins | Rider, Driver | "Ride started from Union Square" |
| `ride_completed` | Ride finishes successfully | Rider, Driver | "Completed. Fare: $12.50, Ratings: D=5/5" |
| `insufficient_funds` | Rider can't afford ride | Rider, Admin | "Insufficient balance. Required: $15.00" |
| `no_driver` | No available driver | Rider, Admin | "No driver available" |
| `payment_failed` | Payment processing fails | Rider, Driver, Admin | "Payment failed: Insufficient balance" |

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Ride handles lifecycle state; Driver manages availability; PricingStrategy calculates fares |
| **Open/Closed** | Add new pricing/matching strategies without modifying RideSharingSystem |
| **Liskov Substitution** | All PricingStrategy/MatchingStrategy subclasses interchangeable at runtime |
| **Interface Segregation** | Observer requires only `update()`; Strategy requires single method |
| **Dependency Inversion** | RideSharingSystem depends on abstract Strategy/Observer, not concrete classes |

---

## Concurrency & Thread Safety

**Challenges**:
- Multiple riders requesting rides simultaneously
- Driver availability changes (accepted ride while another request processing)
- Wallet balance deduction race conditions

**Solutions**:
```python
# System-level lock protects request_ride()
with self.lock:
    # Find available driver
    # Mark driver unavailable
    # Create ride
```

**Alternative Approaches**:
- Optimistic locking with version numbers
- Database row-level locks on driver availability
- Message queue with single consumer per driver

---

## System Architecture Diagram

```
┌─────────────────────────────────────┐
│   RideSharingSystem (Singleton)     │
├─────────────────────────────────────┤
│ - drivers: Map<id, Driver>          │
│ - riders: Map<id, Rider>            │
│ - active_rides: List<Ride>          │
│ - pricing_strategy: Strategy        │
│ - matching_strategy: Strategy       │
│ - observers: List<Observer>         │
├─────────────────────────────────────┤
│ + request_ride()                    │
│ + complete_ride()                   │
│ + update_demand_multiplier()        │
└─────────────────────────────────────┘
         │              │
         ▼              ▼
    ┌────────┐    ┌────────┐
    │ Driver │    │ Rider  │
    ├────────┤    ├────────┤
    │vehicle │    │wallet  │
    │rating  │    │rating  │
    └────────┘    └────────┘
```

---

## Performance Considerations

### Scalability Bottlenecks
1. **Driver Matching**: O(n) scan of all drivers
2. **Distance Calculation**: O(n) Haversine computations
3. **Lock Contention**: Single system-level lock

### Optimization Strategies
1. **Geohashing**: Partition drivers by location grid
2. **Spatial Indexing**: Use R-tree or Quadtree for proximity search
3. **Caching**: Cache available driver list per region
4. **Database Sharding**: Partition by city_id or region
5. **Async Processing**: Queue ride requests, process asynchronously

---

## Interview Success Checklist

- [ ] Explain all 5 core entities clearly
- [ ] Demonstrate 2+ design patterns with code
- [ ] Describe state machine with valid/invalid transitions
- [ ] Calculate Haversine distance on whiteboard
- [ ] Discuss concurrency challenges and solutions
- [ ] Compare pricing strategies (pros/cons)
- [ ] Explain observer pattern event flow
- [ ] Justify Singleton usage for RideSharingSystem
- [ ] Propose 2+ scalability improvements
- [ ] Answer follow-up on fraud detection or ride-sharing

---

## Quick Commands

```bash
# Run all demos
python3 INTERVIEW_COMPACT.py

# Run with verbose output
python3 -u INTERVIEW_COMPACT.py

# Check for errors
python3 -m py_compile INTERVIEW_COMPACT.py
```

---

## Common Interview Follow-Ups

**Q: How would you handle ride cancellations?**
A: Add cancellation_fee attribute. Charge 50% of estimated fare if cancelled after driver acceptance. Implement grace period (free cancellation within 2 minutes).

**Q: How to prevent driver location spoofing?**
A: Validate GPS accuracy threshold. Compare consecutive location updates (detect impossible speeds). Require background location tracking. Use geofencing around pickup/dropoff.

**Q: How to implement ride-sharing (multiple riders)?**
A: Add Ride.riders[] list. Match riders with similar routes (within 2km detour). Calculate fare split proportional to distance. Implement pickup priority queue.

**Q: How to scale to 1M concurrent rides?**
A: Microservices architecture (separate ride-matching service). Use Redis for driver availability cache. Kafka/RabbitMQ for async ride requests. Database sharding by city_id. CDN for static assets.


## Compact Code

```python
#!/usr/bin/env python3
"""
Ride-Sharing System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import List, Optional
import threading
import math
import time


# ===== ENUMS =====

class VehicleType(Enum):
    ECONOMY = "economy"
    PREMIUM = "premium"
    SHARED = "shared"


class RideStatus(Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ===== LOCATION =====

class Location:
    """Geographic location with distance calculation"""
    def __init__(self, latitude: float, longitude: float, address: str):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance using Haversine formula (in km)"""
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Earth radius in km
    
    def __str__(self):
        return "%s (%.4f, %.4f)" % (self.address, self.latitude, self.longitude)


# ===== VEHICLE & DRIVER =====

class Vehicle:
    """Vehicle with type and capacity"""
    def __init__(self, vehicle_id: str, model: str, vehicle_type: VehicleType, 
                 registration: str, capacity: int):
        self.vehicle_id = vehicle_id
        self.model = model
        self.vehicle_type = vehicle_type
        self.registration = registration
        self.capacity = capacity
        self.current_location = None


class Driver:
    """Driver with availability and ratings"""
    def __init__(self, driver_id: str, name: str, phone: str, vehicle: Vehicle):
        self.driver_id = driver_id
        self.name = name
        self.phone = phone
        self.vehicle = vehicle
        self.current_location = None
        self.is_available = True
        self.total_rides = 0
        self.total_rating = 0.0
        self.rides_rated = 0
        self.earnings = 0.0
    
    def get_average_rating(self) -> float:
        """Calculate average driver rating"""
        if self.rides_rated == 0:
            return 5.0  # Default for new drivers
        return self.total_rating / self.rides_rated
    
    def update_location(self, location: Location):
        """Update driver's current location"""
        self.current_location = location
        self.vehicle.current_location = location
    
    def accept_ride(self, ride: 'Ride'):
        """Accept a ride request"""
        ride.accept_ride(self)
        self.is_available = False
    
    def __str__(self):
        return "%s (%s) - Rating: %.1f/5.0" % (
            self.name, self.vehicle.model, self.get_average_rating())


# ===== RIDER =====

class Rider:
    """Rider with wallet and ratings"""
    def __init__(self, rider_id: str, name: str, phone: str):
        self.rider_id = rider_id
        self.name = name
        self.phone = phone
        self.wallet_balance = 500.0  # Initial balance
        self.total_rides = 0
        self.total_spent = 0.0
        self.total_rating = 0.0
        self.rides_rated = 0
    
    def get_average_rating(self) -> float:
        """Calculate average rider rating"""
        if self.rides_rated == 0:
            return 5.0
        return self.total_rating / self.rides_rated
    
    def can_afford_ride(self, amount: float) -> bool:
        """Check if rider can afford the fare"""
        return self.wallet_balance >= amount
    
    def deduct_payment(self, amount: float) -> bool:
        """Deduct fare from wallet"""
        if self.can_afford_ride(amount):
            self.wallet_balance -= amount
            self.total_spent += amount
            self.total_rides += 1
            return True
        return False
    
    def add_funds(self, amount: float):
        """Add funds to wallet"""
        self.wallet_balance += amount
    
    def __str__(self):
        return "%s - Balance: $%.2f, Rating: %.1f/5.0" % (
            self.name, self.wallet_balance, self.get_average_rating())


# ===== RIDE (STATE PATTERN) =====

class Ride:
    """Ride with lifecycle state management"""
    def __init__(self, ride_id: str, rider: Rider, pickup: Location, 
                 dropoff: Location, vehicle_type: VehicleType):
        self.ride_id = ride_id
        self.rider = rider
        self.driver = None
        self.pickup_location = pickup
        self.dropoff_location = dropoff
        self.vehicle_type = vehicle_type
        self.status = RideStatus.REQUESTED
        self.requested_time = datetime.now()
        self.accepted_time = None
        self.started_time = None
        self.completed_time = None
        self.estimated_distance = pickup.distance_to(dropoff)
        self.actual_distance = 0.0
        self.estimated_fare = 0.0
        self.actual_fare = 0.0
        self.driver_rating = None
        self.rider_rating = None
    
    def accept_ride(self, driver: Driver):
        """Transition: REQUESTED -> ACCEPTED"""
        if self.status != RideStatus.REQUESTED:
            raise ValueError("Cannot accept ride with status %s" % self.status.value)
        self.driver = driver
        self.status = RideStatus.ACCEPTED
        self.accepted_time = datetime.now()
    
    def start_ride(self):
        """Transition: ACCEPTED -> IN_PROGRESS"""
        if self.status != RideStatus.ACCEPTED:
            raise ValueError("Cannot start ride with status %s" % self.status.value)
        self.status = RideStatus.IN_PROGRESS
        self.started_time = datetime.now()
    
    def complete_ride(self, final_location: Location):
        """Transition: IN_PROGRESS -> COMPLETED"""
        if self.status != RideStatus.IN_PROGRESS:
            raise ValueError("Cannot complete ride with status %s" % self.status.value)
        self.status = RideStatus.COMPLETED
        self.completed_time = datetime.now()
        self.actual_distance = self.pickup_location.distance_to(final_location)
    
    def cancel_ride(self):
        """Cancel ride at any state"""
        self.status = RideStatus.CANCELLED


# ===== PRICING STRATEGY =====

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        pass


class FixedPricing(PricingStrategy):
    """Fixed pricing: base + per-km rate"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * demand_multiplier


class SurgePricing(PricingStrategy):
    """Surge pricing during high demand"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        # demand_multiplier ranges from 1.0 to 3.0+
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * max(1.0, demand_multiplier)


class PeakHourPricing(PricingStrategy):
    """Peak hour pricing (rush hours)"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    PEAK_MULTIPLIER = 1.5  # 50% increase
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        current_hour = datetime.now().hour
        is_peak = current_hour in [7, 8, 9, 17, 18, 19]  # Morning/evening rush
        
        multiplier = self.PEAK_MULTIPLIER if is_peak else 1.0
        multiplier *= demand_multiplier
        
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * multiplier


# ===== MATCHING STRATEGY =====

class MatchingStrategy(ABC):
    """Abstract matching strategy"""
    @abstractmethod
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        pass


class NearestDriverMatcher(MatchingStrategy):
    """Match with nearest available driver"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type]
        
        if not matching_drivers:
            return None
        
        # Return nearest driver
        return min(matching_drivers, 
                  key=lambda d: d.current_location.distance_to(ride.pickup_location))


class RatingBasedMatcher(MatchingStrategy):
    """Match with highest-rated driver (within acceptable distance)"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type and max distance (5km)
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type
                           and d.current_location.distance_to(ride.pickup_location) <= 5.0]
        
        if not matching_drivers:
            return None
        
        # Return highest-rated driver
        return max(matching_drivers, key=lambda d: d.get_average_rating())


# ===== OBSERVER PATTERN =====

class RideObserver(ABC):
    """Observer interface for ride events"""
    @abstractmethod
    def update(self, event: str, ride: Ride, message: str):
        pass


class RiderNotifier(RideObserver):
    """Notify rider of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        print("  [RIDER] %s: %s" % (ride.rider.name, message))


class DriverNotifier(RideObserver):
    """Notify driver of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        if ride.driver:
            print("  [DRIVER] %s: %s" % (ride.driver.name, message))


class AdminNotifier(RideObserver):
    """Notify admin of critical events"""
    def update(self, event: str, ride: Ride, message: str):
        if event in ["payment_failed", "no_driver", "ride_cancelled", "insufficient_funds"]:
            print("  [ADMIN] Ride %s: %s" % (ride.ride_id, message))


# ===== SINGLETON - RIDE SHARING SYSTEM =====

class RideSharingSystem:
    """Singleton controller for ride-sharing platform"""
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
            self.drivers = {}
            self.riders = {}
            self.rides = {}
            self.active_rides = []
            self.completed_rides = []
            self.observers = []
            self.pricing_strategy = SurgePricing()
            self.matching_strategy = NearestDriverMatcher()
            self.demand_multiplier = 1.0
            self.ride_counter = 0
            self.lock = threading.Lock()
            self.initialized = True
    
    def register_driver(self, driver: Driver):
        """Register a new driver"""
        self.drivers[driver.driver_id] = driver
    
    def register_rider(self, rider: Rider):
        """Register a new rider"""
        self.riders[rider.rider_id] = rider
    
    def add_observer(self, observer: RideObserver):
        """Add observer for notifications"""
        self.observers.append(observer)
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Change pricing strategy at runtime"""
        self.pricing_strategy = strategy
    
    def set_matching_strategy(self, strategy: MatchingStrategy):
        """Change matching strategy at runtime"""
        self.matching_strategy = strategy
    
    def update_demand_multiplier(self):
        """Update demand multiplier based on active rides vs available drivers"""
        available_count = len([d for d in self.drivers.values() if d.is_available])
        if available_count == 0:
            self.demand_multiplier = 3.0
            return
        
        active_count = len(self.active_rides)
        ratio = active_count / max(available_count, 1)
        
        if ratio < 0.5:
            self.demand_multiplier = 1.0
        elif ratio < 1.0:
            self.demand_multiplier = 1.5
        else:
            self.demand_multiplier = 2.0
    
    def request_ride(self, rider: Rider, pickup: Location, 
                    dropoff: Location, vehicle_type: VehicleType) -> Optional[Ride]:
        """Rider requests a ride"""
        with self.lock:
            # Update demand multiplier
            self.update_demand_multiplier()
            
            # Create ride
            self.ride_counter += 1
            ride_id = "RIDE_%05d" % self.ride_counter
            ride = Ride(ride_id, rider, pickup, dropoff, vehicle_type)
            
            # Calculate estimated fare
            ride.estimated_fare = self.pricing_strategy.calculate_fare(
                ride.estimated_distance, self.demand_multiplier)
            
            # Check affordability
            if not rider.can_afford_ride(ride.estimated_fare):
                self._notify_observers("insufficient_funds", ride, 
                    "Insufficient balance. Required: $%.2f, Available: $%.2f" % 
                    (ride.estimated_fare, rider.wallet_balance))
                return None
            
            # Find and assign driver
            available_drivers = [d for d in self.drivers.values() 
                               if d.is_available and d.current_location]
            matched_driver = self.matching_strategy.find_driver(ride, available_drivers)
            
            if not matched_driver:
                self._notify_observers("no_driver", ride, "No driver available")
                return None
            
            # Auto-accept (for demo)
            matched_driver.accept_ride(ride)
            self.rides[ride_id] = ride
            self.active_rides.append(ride)
            
            self._notify_observers("ride_accepted", ride, 
                "Driver %s accepted. Distance: %.1fkm, Fare: $%.2f (%.1fx surge)" % 
                (matched_driver.name, matched_driver.current_location.distance_to(pickup),
                 ride.estimated_fare, self.demand_multiplier))
            
            return ride
    
    def start_ride(self, ride: Ride):
        """Start a ride"""
        ride.start_ride()
        self._notify_observers("ride_started", ride, "Ride started from %s" % ride.pickup_location.address)
    
    def complete_ride(self, ride: Ride, final_location: Location, 
                     driver_rating: int, rider_rating: int) -> bool:
        """Complete ride with payment and ratings"""
        with self.lock:
            ride.complete_ride(final_location)
            ride.actual_fare = self.pricing_strategy.calculate_fare(
                ride.actual_distance, self.demand_multiplier)
            
            # Process payment
            if ride.rider.deduct_payment(ride.actual_fare):
                ride.driver.earnings += ride.actual_fare * 0.75  # Driver gets 75%
                ride.driver.total_rides += 1
                
                # Add ratings
                if 1 <= driver_rating <= 5:
                    ride.driver_rating = driver_rating
                    ride.driver.total_rating += driver_rating
                    ride.driver.rides_rated += 1
                
                if 1 <= rider_rating <= 5:
                    ride.rider_rating = rider_rating
                    ride.rider.total_rating += rider_rating
                    ride.rider.rides_rated += 1
                
                ride.driver.is_available = True
                self.active_rides.remove(ride)
                self.completed_rides.append(ride)
                
                self._notify_observers("ride_completed", ride,
                    "Completed. Distance: %.1fkm, Fare: $%.2f, Ratings: D=%d/5, R=%d/5" % 
                    (ride.actual_distance, ride.actual_fare, driver_rating, rider_rating))
                
                return True
            else:
                self._notify_observers("payment_failed", ride, "Payment failed: Insufficient balance")
                return False
    
    def _notify_observers(self, event: str, ride: Ride, message: str):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, ride, message)
    
    def get_system_stats(self):
        """Get system statistics"""
        return {
            'total_drivers': len(self.drivers),
            'available_drivers': len([d for d in self.drivers.values() if d.is_available]),
            'total_riders': len(self.riders),
            'active_rides': len(self.active_rides),
            'completed_rides': len(self.completed_rides),
            'demand_multiplier': self.demand_multiplier
        }


# ===== DEMO SCENARIOS =====

def print_section(title):
    """Print section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def demo1_setup():
    """Demo 1: Setup & Registration"""
    print_section("DEMO 1: Setup & Registration")
    
    system = RideSharingSystem()
    
    # Add observers
    system.add_observer(RiderNotifier())
    system.add_observer(DriverNotifier())
    system.add_observer(AdminNotifier())
    
    # Register drivers
    v1 = Vehicle("V001", "Toyota Corolla", VehicleType.ECONOMY, "ABC123", 4)
    d1 = Driver("D001", "Alice", "111-1111", v1)
    d1.update_location(Location(37.7749, -122.4194, "San Francisco Downtown"))
    system.register_driver(d1)
    
    v2 = Vehicle("V002", "Tesla Model S", VehicleType.PREMIUM, "XYZ789", 4)
    d2 = Driver("D002", "Bob", "222-2222", v2)
    d2.update_location(Location(37.7849, -122.4094, "Financial District"))
    system.register_driver(d2)
    
    v3 = Vehicle("V003", "Honda Civic", VehicleType.ECONOMY, "DEF456", 4)
    d3 = Driver("D003", "Charlie", "333-3333", v3)
    d3.update_location(Location(37.7649, -122.4294, "Mission District"))
    system.register_driver(d3)
    
    # Register riders
    r1 = Rider("R001", "Emma", "444-4444")
    system.register_rider(r1)
    
    r2 = Rider("R002", "Frank", "555-5555")
    system.register_rider(r2)
    
    print("\nRegistered Drivers:")
    for driver in system.drivers.values():
        print("  - %s at %s" % (driver, driver.current_location))
    
    print("\nRegistered Riders:")
    for rider in system.riders.values():
        print("  - %s" % rider)
    
    stats = system.get_system_stats()
    print("\nSystem Stats:")
    for key, value in stats.items():
        print("  %s: %s" % (key, value))


def demo2_successful_ride():
    """Demo 2: Successful Ride with Payment and Ratings"""
    print_section("DEMO 2: Successful Ride with Payment and Ratings")
    
    system = RideSharingSystem()
    rider = system.riders["R001"]
    
    pickup = Location(37.7849, -122.4194, "Union Square")
    dropoff = Location(37.8049, -122.4294, "North Beach")
    
    print("\n1. Requesting ride...")
    print("   Pickup: %s" % pickup)
    print("   Dropoff: %s" % dropoff)
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if ride:
        print("\n2. Starting ride...")
        system.start_ride(ride)
        
        print("\n3. Completing ride...")
        system.complete_ride(ride, dropoff, driver_rating=5, rider_rating=4)
        
        print("\n4. Updated balances:")
        print("   Rider balance: $%.2f (spent $%.2f)" % (rider.wallet_balance, ride.actual_fare))
        print("   Driver earnings: $%.2f" % ride.driver.earnings)
        print("   Driver rating: %.1f/5.0" % ride.driver.get_average_rating())


def demo3_surge_pricing():
    """Demo 3: Surge Pricing During High Demand"""
    print_section("DEMO 3: Surge Pricing During High Demand")
    
    system = RideSharingSystem()
    
    # Create multiple active rides to trigger surge
    print("\n1. Creating 15 active rides to simulate high demand...")
    
    # Create temporary drivers and riders
    for i in range(15):
        v = Vehicle("V%03d" % (100+i), "Car %d" % i, VehicleType.ECONOMY, "TMP%03d" % i, 4)
        d = Driver("D%03d" % (100+i), "Driver %d" % i, "999-999%d" % i, v)
        d.update_location(Location(37.7 + i*0.01, -122.4 + i*0.01, "Location %d" % i))
        system.register_driver(d)
        
        r = Rider("R%03d" % (100+i), "Rider %d" % i, "888-888%d" % i)
        system.register_rider(r)
        
        # Request ride (auto-accepted)
        pickup = Location(37.7 + i*0.01, -122.4 + i*0.01, "Pickup %d" % i)
        dropoff = Location(37.7 + i*0.01 + 0.1, -122.4 + i*0.01, "Dropoff %d" % i)
        ride = system.request_ride(r, pickup, dropoff, VehicleType.ECONOMY)
        if ride:
            system.start_ride(ride)  # Start to keep active
    
    print("   Active rides: %d" % len(system.active_rides))
    print("   Available drivers: %d" % len([d for d in system.drivers.values() if d.is_available]))
    
    # Update surge
    system.update_demand_multiplier()
    print("   Surge multiplier: %.1fx" % system.demand_multiplier)
    
    # New rider requests ride
    print("\n2. New rider requesting ride during surge...")
    rider = system.riders["R002"]
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.7949, -122.4394, "Marina")
    
    base_fare = FixedPricing().calculate_fare(pickup.distance_to(dropoff), 1.0)
    print("   Base fare (no surge): $%.2f" % base_fare)
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    if ride:
        print("   Surge fare (%.1fx): $%.2f" % (system.demand_multiplier, ride.estimated_fare))
        print("   Difference: $%.2f (%.0f%% increase)" % 
              (ride.estimated_fare - base_fare, (system.demand_multiplier - 1) * 100))


def demo4_rating_based_matching():
    """Demo 4: Rating-Based Driver Matching"""
    print_section("DEMO 4: Rating-Based Driver Matching")
    
    system = RideSharingSystem()
    
    # Give drivers different ratings
    print("\n1. Setting up drivers with different ratings...")
    
    # Complete some rides to build ratings
    drivers = list(system.drivers.values())[:3]
    
    # Alice: 5 stars (2 rides)
    drivers[0].total_rating = 10.0
    drivers[0].rides_rated = 2
    drivers[0].is_available = True
    
    # Bob: 3 stars (2 rides)
    drivers[1].total_rating = 6.0
    drivers[1].rides_rated = 2
    drivers[1].is_available = True
    
    # Charlie: 4 stars (2 rides)
    drivers[2].total_rating = 8.0
    drivers[2].rides_rated = 2
    drivers[2].is_available = True
    
    for d in drivers:
        print("   %s - Rating: %.1f/5.0" % (d.name, d.get_average_rating()))
    
    # Switch to rating-based matching
    print("\n2. Switching to Rating-Based Matcher...")
    system.set_matching_strategy(RatingBasedMatcher())
    
    print("\n3. Requesting ride (should match highest-rated driver)...")
    rider = system.riders["R001"]
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.7949, -122.4394, "Uptown")
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if ride:
        print("\n   Matched Driver: %s (Rating: %.1f/5.0)" % 
              (ride.driver.name, ride.driver.get_average_rating()))
        
        # Complete with 5-star rating
        system.start_ride(ride)
        system.complete_ride(ride, dropoff, driver_rating=5, rider_rating=5)
        
        print("   Updated Rating: %.1f/5.0" % ride.driver.get_average_rating())


def demo5_insufficient_balance():
    """Demo 5: Insufficient Balance Scenario"""
    print_section("DEMO 5: Insufficient Balance Scenario")
    
    system = RideSharingSystem()
    
    # Create rider with low balance
    low_balance_rider = Rider("R999", "Poor Pete", "999-9999")
    low_balance_rider.wallet_balance = 3.0  # Very low balance
    system.register_rider(low_balance_rider)
    
    print("\n1. Rider with low balance: $%.2f" % low_balance_rider.wallet_balance)
    
    # Request long ride (expensive)
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.8749, -122.5194, "Far Suburb")  # 15km+ away
    
    distance = pickup.distance_to(dropoff)
    estimated_fare = system.pricing_strategy.calculate_fare(distance, system.demand_multiplier)
    
    print("2. Requesting ride...")
    print("   Distance: %.1f km" % distance)
    print("   Estimated fare: $%.2f" % estimated_fare)
    print("   Available balance: $%.2f" % low_balance_rider.wallet_balance)
    
    print("\n3. Attempting to book...")
    ride = system.request_ride(low_balance_rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if not ride:
        print("\n4. Ride request failed (insufficient funds)")
        print("   Need to add: $%.2f to wallet" % (estimated_fare - low_balance_rider.wallet_balance))


# ===== MAIN =====

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RIDE-SHARING SYSTEM - COMPLETE DEMONSTRATION")
    print("="*60)
    
    demo1_setup()
    time.sleep(1)
    
    demo2_successful_ride()
    time.sleep(1)
    
    demo3_surge_pricing()
    time.sleep(1)
    
    demo4_rating_based_matching()
    time.sleep(1)
    
    demo5_insufficient_balance()
    
    print("\n" + "="*60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nKey Patterns Demonstrated:")
    print("1. Singleton: RideSharingSystem (one instance)")
    print("2. Strategy: 3 Pricing algorithms (Fixed/Surge/PeakHour)")
    print("3. Strategy: 2 Matching algorithms (Nearest/RatingBased)")
    print("4. Observer: 3 Notifiers (Rider/Driver/Admin)")
    print("5. State: Ride lifecycle (REQUESTED->ACCEPTED->IN_PROGRESS->COMPLETED)")
    print("\nRun 'python3 INTERVIEW_COMPACT.py' to see all demos")

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
