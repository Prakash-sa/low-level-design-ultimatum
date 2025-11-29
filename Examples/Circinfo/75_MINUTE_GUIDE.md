# Ride-Sharing System (Circinfo) - 75 Minute Interview Guide

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
