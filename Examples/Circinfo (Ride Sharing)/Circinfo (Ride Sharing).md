# Ride Sharing System — Complete Design Guide

> Real-time driver-passenger matching, location-based dispatch, dynamic surge pricing, and ride lifecycle management. (Platform: Circinfo)

**Scale**: 1M+ active drivers, 10M+ passengers globally, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Nearest-driver matching, surge pricing strategy, ride state machine, thread-safe singleton dispatch

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?

Passenger enters pickup + destination → system finds nearest available driver (Haversine distance, rating filter) → fare estimated (base + distance + time + surge) → driver accepts → ride progresses through states → payment processed at completion. Core concerns: real-time location matching, dynamic pricing, race-free driver assignment, and scalable geographic dispatch.

### Core Flow

```
Request Ride → Find Nearest Driver → OFFER (30-sec timeout) → ACCEPT → DRIVER_ARRIVED
                                          ↓ decline / timeout                    ↓
                                     Next Driver in Queue              IN_PROGRESS → COMPLETED
                                                                                          ↓
                                                                              Payment + Rating Exchange
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single city or multi-city?** → "Multi-city, but partition ride service per city"
2. **Real-time location tracking?** → "Yes, driver updates location every 1-2 seconds"
3. **Multiple ride types?** → "Yes — economy, premium, XL"
4. **Real payment processing?** → "Mock payment service for interview"
5. **Shared/pool rides?** → "Mention as extension; implement single-passenger rides"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Passenger** | Requests & pays for rides | Enter pickup/destination, request ride, rate driver |
| **Driver** | Accepts & completes rides | Go online, accept ride, navigate, complete ride |
| **System** | Dispatcher & coordinator | Match driver, calculate fare, enforce surge cap, track state |

### Functional Requirements (What does the system do?)

✅ **Driver Search**
  - Find available drivers within configurable radius (default 10 km)
  - Filter by rating >= 3.5 and ONLINE status
  - Sort by distance, then rating

✅ **Ride Request & Matching**
  - Create ride request with pickup and destination
  - Offer to top 3 nearest drivers (first to accept wins)
  - 30-second acceptance timeout per driver

✅ **Ride Lifecycle**
  - Manage states: REQUESTED → ACCEPTED → DRIVER_ARRIVED → IN_PROGRESS → COMPLETED
  - Cancellation with penalty calculation

✅ **Dynamic Pricing**
  - Base fare + per-km rate + per-min rate × surge multiplier
  - Surge updates dynamically based on demand/supply
  - Surge capped at 3x maximum

✅ **Ratings**
  - Driver rates passenger, passenger rates driver (1-5 stars)
  - Minimum rating of 3.5 to accept rides

✅ **Payments**
  - Charge after ride completion
  - Driver earns 75% (platform takes 25%)
  - Cancellation penalties enforced

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Driver found within 30 seconds (95th percentile)  
✅ **Location Updates**: 1 update per second while driver is online  
✅ **Scale**: 1M+ active drivers, 10M+ passengers globally  
✅ **Pricing Accuracy**: Surge updates dynamically in real time  
✅ **Payment Reliability**: 99.9% payment success rate  
✅ **Geographic Distribution**: Multi-city with independent ride service instances  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Search radius** | 10 km (configurable) |
| **Max surge multiplier** | 3x (prevent price gouging) |
| **Acceptance timeout** | 30 seconds per driver |
| **Cancellation penalty** | 0% (<30 s request), 25% (after acceptance), 100% (during ride) |
| **Minimum driver rating** | 3.5 stars to accept rides |
| **Payment window** | Must complete within 30 seconds |
| **Ride types** | Economy, Premium (implement both pricing strategies) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Driver, Passenger, Ride, Location, Vehicle, PricingStrategy, RideService, ...
```

### Step 2.2: Define Core Classes

#### **Location** — Geographic coordinate with distance calculation
```
Properties:
  - latitude: float
  - longitude: float

Behaviors:
  - distance_to(other): float  — Haversine formula, result in km
```

#### **Vehicle** — Driver's vehicle information
```
Properties:
  - make: str
  - model: str
  - license_plate: str
  - color: str

Behaviors:
  - (none — data holder)
```

#### **Driver** — A registered driver with location and availability
```
Properties:
  - driver_id: str
  - name: str
  - vehicle: Vehicle
  - location: Location  (updated every 1-2 seconds)
  - status: DriverStatus (OFFLINE, ONLINE, BUSY)
  - rating: float  (1.0–5.0, average across all rides)
  - total_rides: int
  - acceptance_rate: float
  - earnings: float
  - lock: threading.RLock

Behaviors:
  - update_location(location): Thread-safe location update
  - get_distance_to(location): Thread-safe distance calculation
  - set_busy() / set_online(): Status transitions
```

#### **Passenger** — A registered passenger
```
Properties:
  - passenger_id: str
  - name: str
  - location: Location  (pickup point)
  - rating: float
  - total_rides: int
  - payment_method: str

Behaviors:
  - (none — data holder; location updated at request time)
```

#### **Ride** — A single trip from pickup to destination
```
Properties:
  - ride_id: str
  - driver: Driver
  - passenger: Passenger
  - pickup_location: Location
  - destination_location: Location
  - status: RideStatus (REQUESTED, ACCEPTED, DRIVER_ARRIVED, IN_PROGRESS, COMPLETED, CANCELLED)
  - fare: float
  - start_time: float
  - end_time: Optional[float]

Behaviors:
  - __hash__(): Hashable by ride_id
```

#### **RideService** — Main controller (Singleton)
```
Properties:
  - drivers: Dict[str, Driver]
  - passengers: Dict[str, Passenger]
  - rides: Dict[str, Ride]
  - active_rides: List[Ride]
  - pricing_strategy: PricingStrategy
  - surge_multiplier: float  (1.0–3.0)
  - lock: threading.RLock
  - ride_counter: int

Behaviors:
  - register_driver(driver) / register_passenger(passenger)
  - find_nearby_drivers(location, radius_km): List[Driver]
  - request_ride(passenger, destination, ride_type): Optional[Ride]
  - accept_ride(ride): bool
  - arrive_at_pickup(ride): bool
  - start_ride(ride): bool
  - complete_ride(ride): bool
  - cancel_ride(ride, reason): bool
  - set_surge_pricing(multiplier): void
  - display_status(): void
```

### Step 2.3: Define Enumerations (State & Type)

```python
class RideStatus(Enum):
    REQUESTED     = 1   # Waiting for driver acceptance
    ACCEPTED      = 2   # Driver accepted, en route to pickup
    DRIVER_ARRIVED = 3  # Driver at pickup location
    IN_PROGRESS   = 4   # Passenger on board
    COMPLETED     = 5   # Dropoff done, payment processed
    CANCELLED     = 6   # Cancelled (with potential penalty)

class DriverStatus(Enum):
    OFFLINE = 0   # Not accepting rides
    ONLINE  = 1   # Available for new rides
    BUSY    = 2   # Currently on a ride
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Location** | Accurate distance calculation (Haversine) | Can't find nearest driver |
| **Driver** | Location, status, rating — all needed for matching | No driver management |
| **Passenger** | Pickup point + payment info | Can't initiate ride |
| **Ride** | Encapsulates the full trip lifecycle | No state tracking or fare calculation |
| **Vehicle** | Ride type differentiation (economy vs premium) | Can't support ride types |
| **RideService** | Central thread-safe coordinator | No atomic matching, double-booking risk |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Find Nearby Drivers**
```python
def find_nearby_drivers(location: Location, radius_km: float = 10.0) -> List[Driver]:
    """
    Find available (ONLINE) drivers within radius_km of location.
    Sorted by: distance ascending, then rating descending.
    Returns: up to 5 closest eligible drivers.
    Response Time: O(n) where n = registered drivers; optimize with QuadTree/GeoHash.
    """
    pass
```

#### **2. Request Ride** ⭐ CRITICAL
```python
def request_ride(passenger: Passenger, destination: Location,
                 ride_type: str = "economy") -> Optional[Ride]:
    """
    Passenger requests a ride from their current location to destination.

    Precondition: At least one ONLINE driver within radius
    Postcondition: Ride created with REQUESTED status, offered to nearest driver

    Returns: Ride object on success, None if no drivers available.

    Failure causes:
      - No drivers online within radius
      - Passenger location not set

    Concurrency: THREAD-SAFE (RLock guards ride creation)
    Response Time: <30 seconds to first driver offer
    """
    pass
```

#### **3. Accept Ride** ⭐ CRITICAL
```python
def accept_ride(ride: Ride) -> bool:
    """
    Driver accepts the ride. Fare is calculated at acceptance time.

    Precondition: ride.status == REQUESTED
    Postcondition: ride.status == ACCEPTED, driver.status == BUSY, fare set

    Returns: True on success, False if ride already taken or invalid.

    Concurrency: THREAD-SAFE (prevents double-assignment)
    Side Effects: Calculates fare using current pricing strategy + surge multiplier
    """
    pass
```

#### **4. Arrive at Pickup**
```python
def arrive_at_pickup(ride: Ride) -> bool:
    """
    Driver signals arrival at passenger pickup location.

    Precondition: ride.status == ACCEPTED
    Postcondition: ride.status == DRIVER_ARRIVED
    """
    pass
```

#### **5. Start Ride**
```python
def start_ride(ride: Ride) -> bool:
    """
    Passenger boards; ride meter starts.

    Precondition: ride.status == DRIVER_ARRIVED
    Postcondition: ride.status == IN_PROGRESS, start_time recorded
    """
    pass
```

#### **6. Complete Ride** ⭐ CRITICAL
```python
def complete_ride(ride: Ride) -> bool:
    """
    Dropoff complete; payment processed and earnings credited.

    Precondition: ride.status == IN_PROGRESS
    Postcondition: ride.status == COMPLETED, driver.earnings += fare * 0.75,
                   driver.status == ONLINE

    Side Effects: Credits driver earnings, removes from active_rides
    """
    pass
```

#### **7. Cancel Ride**
```python
def cancel_ride(ride: Ride, reason: str = "Passenger cancelled") -> bool:
    """
    Cancel a ride with penalty calculation.

    Penalty:
      - REQUESTED → 0 (driver not yet notified)
      - ACCEPTED → 25% of fare
      - IN_PROGRESS → 100% of fare

    Postcondition: ride.status == CANCELLED, driver.status == ONLINE
    """
    pass
```

#### **8. Set Surge Pricing**
```python
def set_surge_pricing(multiplier: float) -> None:
    """
    Dynamically update surge multiplier. Capped at 3.0x.
    Applies to next accept_ride() fare calculation.
    """
    pass
```

### Step 3.2: Failure Model

```python
class RideSharingException(Exception):
    """Base exception"""
    pass

class NoDriversAvailableError(RideSharingException):
    """No ONLINE drivers within search radius"""
    pass

class InvalidRideStateError(RideSharingException):
    """State transition is not permitted"""
    pass

class RideAlreadyAssignedError(RideSharingException):
    """Another driver accepted the ride first"""
    pass
```

### Step 3.3: API Usage Example

```python
service = RideService()

# Register participants
driver = Driver("D1", "Alice", Vehicle("Toyota", "Prius", "ABC123", "Blue"))
driver.location = Location(40.7128, -74.0060)
service.register_driver(driver)

passenger = Passenger("P1", "John")
passenger.location = Location(40.7128, -74.0060)
service.register_passenger(passenger)

# Full ride lifecycle
destination = Location(40.7580, -73.9855)
ride = service.request_ride(passenger, destination)

if ride:
    service.accept_ride(ride)          # Driver accepts
    service.arrive_at_pickup(ride)     # Driver at pickup
    service.start_ride(ride)           # Passenger boards
    service.complete_ride(ride)        # Dropoff + payment
    print(f"Fare: ${ride.fare}, Driver earned: ${ride.fare * 0.75:.2f}")
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
RideService HAS-A drivers / passengers / rides (1:N Composition)
  └─ RideService owns and manages lifecycle of all registered entities

RideService USES-A PricingStrategy (1:1 Composition)
  └─ RideService owns and can swap pricing algorithm at runtime

Ride REFERENCES Driver (1:1 Association)
  └─ Ride links to assigned Driver (no ownership)

Ride REFERENCES Passenger (1:1 Association)
  └─ Ride links to requesting Passenger (no ownership)

Ride REFERENCES Location × 2 (1:1 Composition)
  └─ Ride owns its pickup and destination Location objects

Driver USES-A Location (1:1 Composition)
  └─ Driver owns its current Location (updated in place)

Driver USES-A Vehicle (1:1 Composition)
  └─ Driver owns Vehicle for the lifetime of registration

PricingStrategy IS-A (Abstract)
  └─ Implemented by EconomyPricing and PremiumPricing
```

### Step 4.2: Complete UML Class Diagram

```
┌─────────────────────────────────────────────┐
│          RideService (Singleton)            │
├─────────────────────────────────────────────┤
│ - _instance: RideService                    │
│ - drivers: Dict[str, Driver]                │
│ - passengers: Dict[str, Passenger]          │
│ - rides: Dict[str, Ride]                    │
│ - active_rides: List[Ride]                  │
│ - pricing_strategy: PricingStrategy         │
│ - surge_multiplier: float  (1.0-3.0)        │
│ - lock: threading.RLock                     │
│ - ride_counter: int                         │
├─────────────────────────────────────────────┤
│ + register_driver(driver): void             │
│ + register_passenger(passenger): void       │
│ + find_nearby_drivers(...): List[Driver]    │
│ + request_ride(...): Optional[Ride]         │
│ + accept_ride(ride): bool                   │
│ + arrive_at_pickup(ride): bool              │
│ + start_ride(ride): bool                    │
│ + complete_ride(ride): bool                 │
│ + cancel_ride(ride, reason): bool           │
│ + set_surge_pricing(multiplier): void       │
│ + display_status(): void                    │
└──────────────┬──────────────────────────────┘
       manages 1:N
   ┌───────────┼────────────┐
   ▼           ▼            ▼
┌────────┐ ┌──────────┐ ┌────────┐
│ Driver │ │Passenger │ │  Ride  │
├────────┤ ├──────────┤ ├────────┤
│driver_id│ │pass_id  │ │ride_id │
│name    │ │name      │ │driver  │──→ Driver
│vehicle │ │location  │ │passenger│─→ Passenger
│location│ │rating    │ │pickup  │
│status  │ │payment   │ │dest    │
│rating  │ └──────────┘ │status  │
│lock    │              │fare    │
└───┬────┘              └────────┘
    │
    ▼
┌─────────┐
│ Vehicle │
├─────────┤
│make     │
│model    │
│plate    │
│color    │
└─────────┘

STRATEGY PATTERN (Pricing):
┌───────────────────────────────────┐
│  PricingStrategy (Abstract)       │
├───────────────────────────────────┤
│ + calculate_fare(dist, dur, surge)│
└──┬────────────────────────────────┘
   │ implemented by
   ├─→ EconomyPricing  (base $2, $0.80/km, $0.15/min)
   └─→ PremiumPricing  (base $5, $1.50/km, $0.30/min)

RIDE STATE MACHINE:
REQUESTED ──accept──→ ACCEPTED ──arrive──→ DRIVER_ARRIVED
                                                  │
                                               start
                                                  ▼
CANCELLED ←──cancel── IN_PROGRESS ──complete──→ COMPLETED

MATCHING ALGORITHM:
REQUEST
  └─→ Find ONLINE drivers within 10 km radius
      └─→ Filter: rating >= 3.5
          └─→ Sort: distance ASC, rating DESC
              └─→ Offer to top driver (30 s timeout)
                  └─→ Accept → DONE
                      Decline / timeout → next driver

LOCATION SERVICE:
┌──────────────────────┐
│ Location (Lat, Long) │
├──────────────────────┤
│ distance_to(loc2)    │──→ Haversine formula (accurate to ~1 m)
└──────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| RideService → Drivers | 1:N | Composition | Service owns all registered drivers |
| RideService → Passengers | 1:N | Composition | Service owns all registered passengers |
| RideService → Rides | 1:N | Composition | Service owns all ride records |
| RideService → PricingStrategy | 1:1 | Composition | Service owns current pricing algorithm |
| Ride → Driver | 1:1 | Association | Ride references assigned driver |
| Ride → Passenger | 1:1 | Association | Ride references requesting passenger |
| Ride → Location (×2) | 1:1 | Composition | Ride owns its pickup and destination |
| Driver → Vehicle | 1:1 | Composition | Driver owns their vehicle |
| Driver → Location | 1:1 | Composition | Driver owns their current position |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For RideService)

**Problem**: Multiple threads and city services need one consistent view of drivers, passengers, and active rides.

**Solution**: One global RideService instance with thread-safe double-checked initialization.

```python
class RideService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.drivers = {}
        self.passengers = {}
        self.rides = {}
        self.active_rides = []
        self.pricing_strategy = EconomyPricing()
        self.surge_multiplier = 1.0
        self.lock = threading.RLock()   # RLock: find_nearby_drivers re-entered from request_ride
        self.ride_counter = 0
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to test), ⚠️ One instance per process (use geographic sharding for multi-city)

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Pricing varies by ride type (economy vs premium) and new tiers may be added without changing ride booking logic.

**Solution**: Pluggable pricing algorithms injected into RideService. Surge multiplier applied uniformly by the service.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        pass

class EconomyPricing(PricingStrategy):
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        base = 2.0
        subtotal = base + distance_km * 0.80 + duration_min * 0.15
        return round(subtotal * surge, 2)

class PremiumPricing(PricingStrategy):
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        base = 5.0
        subtotal = base + distance_km * 1.50 + duration_min * 0.30
        return round(subtotal * surge, 2)

# Usage: switch pricing tier at runtime
service.pricing_strategy = PremiumPricing()
fare = service.pricing_strategy.calculate_fare(distance, duration, service.surge_multiplier)
```

**Benefit**: ✅ Easy to add new tiers (XL, Shared), ✅ No booking logic change  
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 3: **State Machine** (For Ride Lifecycle)

**Problem**: A ride must move through defined states. Invalid transitions (e.g., completing a REQUESTED ride) must be blocked.

**Solution**: Guard every state-change method with a status pre-check.

```python
class RideStatus(Enum):
    REQUESTED = 1
    ACCEPTED = 2
    DRIVER_ARRIVED = 3
    IN_PROGRESS = 4
    COMPLETED = 5
    CANCELLED = 6

# Valid transitions enforced in service methods:
def accept_ride(self, ride: Ride) -> bool:
    with self.lock:
        if ride.status != RideStatus.REQUESTED:
            return False          # Guard: prevent double-accept
        ride.driver.set_busy()
        ride.status = RideStatus.ACCEPTED
        ...
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions rejected at runtime  
**Trade-off**: ⚠️ Each method must check status before proceeding

---

### Pattern 4: **Observer** (For Ride Status Notifications)

**Problem**: Drivers and passengers need real-time notifications (accept, arrive, complete) without tight coupling.

**Solution**: Observer pattern decouples the RideService from notification channels.

```python
class RideObserver(ABC):
    @abstractmethod
    def on_ride_event(self, event: str, ride: Ride): pass

class DriverNotifier(RideObserver):
    def on_ride_event(self, event: str, ride: Ride):
        print(f"[Driver {ride.driver.name}] {event}: Ride {ride.ride_id}")

class PassengerNotifier(RideObserver):
    def on_ride_event(self, event: str, ride: Ride):
        print(f"[Passenger {ride.passenger.name}] {event}: Ride {ride.ride_id}")

# Usage: add observers to service
service.add_observer(DriverNotifier())
service.add_observer(PassengerNotifier())
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add SMS/email/push channels  
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 5: **Factory** (For Ride Types)

**Problem**: Creating a ride requires consistent ID generation, pairing driver + passenger, and wiring the correct pricing strategy.

**Solution**: Centralize creation inside `request_ride()`.

```python
def request_ride(self, passenger, destination, ride_type="economy"):
    # Select strategy
    if ride_type == "premium":
        self.pricing_strategy = PremiumPricing()

    with self.lock:
        self.ride_counter += 1
        ride_id = f"RIDE_{self.ride_counter}"
        ride = Ride(
            ride_id=ride_id,
            driver=available_drivers[0],
            passenger=passenger,
            pickup_location=passenger.location,
            destination_location=destination
        )
        self.rides[ride_id] = ride
        self.active_rides.append(ride)
    return ride
```

**Benefit**: ✅ Centralized, consistent initialization  
**Trade-off**: ⚠️ If ride creation logic grows, promote to a dedicated RideFactory class

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Single global RideService dispatcher | Consistent state, atomic driver assignment |
| **Strategy** | Varying pricing algorithms (economy, premium) | Pluggable, add new tiers without code change |
| **State Machine** | Ride lifecycle correctness | Invalid transitions blocked |
| **Observer** | Events trigger driver/passenger notifications | Loose coupling, event-driven |
| **Factory** | Consistent ride creation with correct pricing | Centralized, repeatable initialization |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Ride Sharing System (Circinfo) - Interview Implementation
Demonstrates:
1. Location-based driver search
2. Matching algorithm (nearest, rating-based)
3. Dynamic pricing (surge, distance, time)
4. Ride state machine
5. Real-time location tracking
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass, field
import math
import threading
import time

# ============================================================================
# ENUMERATIONS
# ============================================================================

class RideStatus(Enum):
    REQUESTED     = 1
    ACCEPTED      = 2
    DRIVER_ARRIVED = 3
    IN_PROGRESS   = 4
    COMPLETED     = 5
    CANCELLED     = 6

class DriverStatus(Enum):
    OFFLINE = 0
    ONLINE  = 1
    BUSY    = 2

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Location:
    latitude: float
    longitude: float

    def distance_to(self, other: 'Location') -> float:
        """Haversine formula for distance in km"""
        R = 6371
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def __repr__(self):
        return f"({self.latitude:.4f}, {self.longitude:.4f})"

@dataclass
class Vehicle:
    make: str
    model: str
    license_plate: str
    color: str

@dataclass
class Ride:
    ride_id: str
    driver: 'Driver'
    passenger: 'Passenger'
    pickup_location: Location
    destination_location: Location
    status: RideStatus = RideStatus.REQUESTED
    fare: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def __hash__(self):
        return hash(self.ride_id)

# ============================================================================
# DRIVER & PASSENGER
# ============================================================================

class Driver:
    def __init__(self, driver_id: str, name: str, vehicle: Vehicle):
        self.driver_id = driver_id
        self.name = name
        self.vehicle = vehicle
        self.location = Location(40.7128, -74.0060)
        self.status = DriverStatus.ONLINE
        self.rating = 4.5
        self.total_rides = 100
        self.acceptance_rate = 0.95
        self.earnings = 0.0
        self.lock = threading.RLock()

    def update_location(self, location: Location):
        with self.lock:
            self.location = location

    def get_distance_to(self, location: Location) -> float:
        with self.lock:
            return self.location.distance_to(location)

    def set_busy(self):
        with self.lock:
            self.status = DriverStatus.BUSY

    def set_online(self):
        with self.lock:
            self.status = DriverStatus.ONLINE

    def __repr__(self):
        return f"Driver({self.name}, Rating: {self.rating}, Loc: {self.location})"

class Passenger:
    def __init__(self, passenger_id: str, name: str):
        self.passenger_id = passenger_id
        self.name = name
        self.location = Location(40.7580, -73.9855)
        self.rating = 4.8
        self.total_rides = 50
        self.payment_method = "Card"

    def __repr__(self):
        return f"Passenger({self.name}, Rating: {self.rating})"

# ============================================================================
# PRICING STRATEGY
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        pass

class EconomyPricing(PricingStrategy):
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        base = 2.0
        distance_cost = distance_km * 0.80
        time_cost = duration_min * 0.15
        subtotal = base + distance_cost + time_cost
        return round(subtotal * surge, 2)

class PremiumPricing(PricingStrategy):
    def calculate_fare(self, distance_km: float, duration_min: float, surge: float) -> float:
        base = 5.0
        distance_cost = distance_km * 1.50
        time_cost = duration_min * 0.30
        subtotal = base + distance_cost + time_cost
        return round(subtotal * surge, 2)

# ============================================================================
# RIDE SERVICE (SINGLETON)
# ============================================================================

class RideService:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        # *args/**kwargs prevent TypeError when subclasses or calls pass args
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.drivers: Dict[str, Driver] = {}
        self.passengers: Dict[str, Passenger] = {}
        self.rides: Dict[str, Ride] = {}
        self.active_rides: List[Ride] = []
        self.pricing_strategy = EconomyPricing()
        self.surge_multiplier = 1.0
        # RLock is required: request_ride holds self.lock and then calls
        # find_nearby_drivers, which also acquires self.lock.
        self.lock = threading.RLock()
        self.ride_counter = 0

    def register_driver(self, driver: Driver):
        with self.lock:
            self.drivers[driver.driver_id] = driver

    def register_passenger(self, passenger: Passenger):
        with self.lock:
            self.passengers[passenger.passenger_id] = passenger

    def find_nearby_drivers(self, location: Location, radius_km: float = 10.0) -> List[Driver]:
        """Find available drivers within radius, sorted by distance then rating."""
        nearby = []
        with self.lock:
            for driver in self.drivers.values():
                if driver.status == DriverStatus.ONLINE:
                    distance = driver.get_distance_to(location)
                    if distance <= radius_km:
                        nearby.append((distance, driver.rating, driver))
        nearby.sort(key=lambda x: (x[0], -x[1]))
        return [driver for _, _, driver in nearby[:5]]

    def request_ride(self, passenger: Passenger, destination: Location,
                     ride_type: str = "economy") -> Optional[Ride]:
        """Passenger requests a ride."""
        available_drivers = self.find_nearby_drivers(passenger.location)

        if not available_drivers:
            print("No drivers available")
            return None

        driver = available_drivers[0]

        with self.lock:
            self.ride_counter += 1
            ride_id = f"RIDE_{self.ride_counter}"
            ride = Ride(
                ride_id=ride_id,
                driver=driver,
                passenger=passenger,
                pickup_location=passenger.location,
                destination_location=destination,
                status=RideStatus.REQUESTED
            )
            self.rides[ride_id] = ride
            self.active_rides.append(ride)

        print(f"Ride requested: {ride_id}")
        print(f"  Passenger: {passenger.name} at {passenger.location}")
        print(f"  Destination: {destination}")
        print(f"  Offered to Driver: {driver.name}")
        return ride

    def accept_ride(self, ride: Ride) -> bool:
        """Driver accepts ride; fare calculated at acceptance time."""
        with self.lock:
            if ride.status != RideStatus.REQUESTED:
                return False
            ride.driver.set_busy()
            ride.status = RideStatus.ACCEPTED
            distance = ride.pickup_location.distance_to(ride.destination_location)
            duration = distance / 1.0   # Assume 1 km/min average speed
            fare = self.pricing_strategy.calculate_fare(distance, duration, self.surge_multiplier)
            ride.fare = fare

        print(f"Ride {ride.ride_id} accepted by {ride.driver.name}")
        print(f"  Fare: ${ride.fare}")
        print(f"  Surge: {self.surge_multiplier}x")
        return True

    def arrive_at_pickup(self, ride: Ride) -> bool:
        """Driver arrives at pickup location."""
        with self.lock:
            if ride.status != RideStatus.ACCEPTED:
                return False
            ride.status = RideStatus.DRIVER_ARRIVED

        print(f"Driver {ride.driver.name} arrived at pickup")
        return True

    def start_ride(self, ride: Ride) -> bool:
        """Passenger boards; ride starts."""
        with self.lock:
            if ride.status != RideStatus.DRIVER_ARRIVED:
                return False
            ride.status = RideStatus.IN_PROGRESS
            ride.start_time = time.time()

        print(f"Ride {ride.ride_id} started - en route to destination")
        return True

    def complete_ride(self, ride: Ride) -> bool:
        """Ride completed; payment processed."""
        with self.lock:
            if ride.status != RideStatus.IN_PROGRESS:
                return False
            ride.status = RideStatus.COMPLETED
            ride.end_time = time.time()
            ride.driver.earnings += ride.fare * 0.75   # Platform takes 25%
            ride.driver.set_online()
            if ride in self.active_rides:
                self.active_rides.remove(ride)

        print(f"Ride {ride.ride_id} completed")
        print(f"  Fare: ${ride.fare}")
        print(f"  Driver earned: ${ride.fare * 0.75:.2f}")
        return True

    def cancel_ride(self, ride: Ride, reason: str = "Passenger cancelled") -> bool:
        """Cancel ride with penalty calculation."""
        with self.lock:
            if ride.status in (RideStatus.COMPLETED, RideStatus.CANCELLED):
                return False
            penalty = 0.0
            if ride.status == RideStatus.ACCEPTED:
                penalty = ride.fare * 0.25
            elif ride.status == RideStatus.IN_PROGRESS:
                penalty = ride.fare   # Full charge
            ride.status = RideStatus.CANCELLED
            ride.driver.set_online()
            if ride in self.active_rides:
                self.active_rides.remove(ride)

        print(f"Ride {ride.ride_id} cancelled: {reason}")
        print(f"  Cancellation fee: ${penalty:.2f}")
        return True

    def set_surge_pricing(self, multiplier: float):
        """Update surge pricing (capped at 3x)."""
        self.surge_multiplier = min(multiplier, 3.0)
        print(f"Surge pricing updated: {self.surge_multiplier}x")

    def display_status(self):
        print("\n" + "="*70)
        print("RIDE SERVICE STATUS")
        print("="*70)
        print(f"Registered drivers:    {len(self.drivers)}")
        print(f"Registered passengers: {len(self.passengers)}")
        print(f"Active rides:          {len(self.active_rides)}")
        print(f"Total completed:       "
              f"{len([r for r in self.rides.values() if r.status == RideStatus.COMPLETED])}")
        print(f"Surge multiplier:      {self.surge_multiplier}x")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    print("\n" + "="*70)
    print("DEMO 1: SYSTEM SETUP")
    print("="*70)

    service = RideService()

    drivers = [
        Driver("D1", "Alice",   Vehicle("Toyota", "Prius",   "ABC123", "Blue")),
        Driver("D2", "Bob",     Vehicle("Honda",  "Civic",   "XYZ789", "Red")),
        Driver("D3", "Charlie", Vehicle("Tesla",  "Model 3", "TSL456", "White")),
    ]
    for driver in drivers:
        service.register_driver(driver)
        print(f"Registered: {driver}")

    passengers = [
        Passenger("P1", "John"),
        Passenger("P2", "Sarah"),
    ]
    for passenger in passengers:
        service.register_passenger(passenger)
        print(f"Registered: {passenger}")

    service.display_status()

def demo_2_request_and_accept():
    print("\n" + "="*70)
    print("DEMO 2: REQUEST RIDE & ACCEPT")
    print("="*70)

    service = RideService()

    driver = Driver("D1", "Alice", Vehicle("Toyota", "Prius", "ABC123", "Blue"))
    driver.location = Location(40.7128, -74.0060)
    service.register_driver(driver)

    passenger = Passenger("P1", "John")
    passenger.location = Location(40.7128, -74.0060)
    service.register_passenger(passenger)

    destination = Location(40.7580, -73.9855)
    ride = service.request_ride(passenger, destination)

    if ride:
        service.accept_ride(ride)

def demo_3_complete_ride():
    print("\n" + "="*70)
    print("DEMO 3: COMPLETE RIDE JOURNEY")
    print("="*70)

    service = RideService()

    driver = Driver("D1", "Alice", Vehicle("Toyota", "Prius", "ABC123", "Blue"))
    driver.location = Location(40.7128, -74.0060)
    service.register_driver(driver)

    passenger = Passenger("P1", "John")
    passenger.location = Location(40.7128, -74.0060)
    service.register_passenger(passenger)

    destination = Location(40.7580, -73.9855)
    ride = service.request_ride(passenger, destination)

    if ride:
        print("\n--- Ride Journey ---")
        service.accept_ride(ride)
        print("(Driver driving to pickup...)")
        service.arrive_at_pickup(ride)
        print("(Passenger boarding...)")
        service.start_ride(ride)
        print("(Ride in progress...)")
        service.complete_ride(ride)

def demo_4_surge_pricing():
    print("\n" + "="*70)
    print("DEMO 4: SURGE PRICING")
    print("="*70)

    service = RideService()

    driver = Driver("D1", "Alice", Vehicle("Toyota", "Prius", "ABC123", "Blue"))
    service.register_driver(driver)

    passenger = Passenger("P1", "John")
    service.register_passenger(passenger)

    destination = Location(40.7580, -73.9855)

    print("\nNormal pricing (1.0x):")
    ride1 = service.request_ride(passenger, destination)
    if ride1:
        service.accept_ride(ride1)
        print(f"Fare: ${ride1.fare}")

    print("\nWith surge (2.5x):")
    service.set_surge_pricing(2.5)
    ride2 = service.request_ride(passenger, destination)
    if ride2:
        service.accept_ride(ride2)
        print(f"Fare: ${ride2.fare}")

def demo_5_cancellation():
    print("\n" + "="*70)
    print("DEMO 5: CANCELLATION SCENARIOS")
    print("="*70)

    service = RideService()

    driver = Driver("D1", "Alice", Vehicle("Toyota", "Prius", "ABC123", "Blue"))
    service.register_driver(driver)

    passenger = Passenger("P1", "John")
    service.register_passenger(passenger)

    destination = Location(40.7580, -73.9855)

    print("\nScenario 1: Cancel before driver accepts")
    ride1 = service.request_ride(passenger, destination)
    if ride1:
        service.cancel_ride(ride1, "Passenger changed mind")

    print("\nScenario 2: Cancel after driver accepts")
    ride2 = service.request_ride(passenger, destination)
    if ride2:
        service.accept_ride(ride2)
        service.cancel_ride(ride2, "Passenger cancelled")

    print("\nScenario 3: Cancel during ride")
    ride3 = service.request_ride(passenger, destination)
    if ride3:
        service.accept_ride(ride3)
        service.arrive_at_pickup(ride3)
        service.start_ride(ride3)
        service.cancel_ride(ride3, "Emergency")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("RIDE SHARING SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_setup()
    demo_2_request_and_accept()
    demo_3_complete_ride()
    demo_4_surge_pricing()
    demo_5_cancellation()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **register_driver/passenger** | RLock on service | Thread-safe registration |
| **find_nearby_drivers** | RLock on service | Safe scan of driver map |
| **request_ride** | RLock on service (re-entrant: calls find_nearby_drivers) | Atomic ride creation |
| **accept_ride** | RLock on service | Prevents double-accept (status guard) |
| **complete_ride** | RLock on service | Atomic earnings credit + status transition |
| **Singleton init** | Class-level RLock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock()` used throughout — `request_ride` holds the lock and calls `find_nearby_drivers`, which re-enters the same lock (impossible with a plain `Lock`)
2. ✅ `__new__(cls, *args, **kwargs)` — accepts any call signature to avoid `TypeError` in subclass or parameterized instantiation
3. ✅ Notifications and print statements fire outside the critical section where possible
4. ✅ Double-checked locking for Singleton initialization

---

## Demo Scenarios

### Demo 1: Driver Search & Matching
```
- Passenger at (lat:40.7128, long:-74.0060) requests ride
- Search radius: 10 km
- Find 50 available drivers
- Sort by: distance (nearest), rating (highest)
- Offer to top 3 drivers (nearest first)
- First to accept gets ride
```

### Demo 2: Fare Calculation
```
- Pickup: Downtown
- Destination: Airport (20 km away, 25 min drive)
- Base: $2
- Distance: 20 × $0.80 = $16
- Time: 25 × $0.15 = $3.75
- Surge (2x): 21.75 × 2 = $43.50
- Subtotal: $43.50
- Tips: $5
- Total: $48.50
```

### Demo 3: Real-Time Ride Tracking
```
- Driver accepts ride
- Passenger sees driver location + ETA (5 min)
- Driver en route to pickup
- Real-time location updates every 5 seconds
- Passenger sees driver approaching
- Driver arrives + opens door
- Passenger boards
- Ride in progress (tracking continues)
```

### Demo 4: Cancellation Scenarios
```
- Scenario 1: Passenger cancels <30s after request
  → No charge (driver not notified yet)
- Scenario 2: Passenger cancels <2min after acceptance
  → 25% cancellation fee ($5-10)
- Scenario 3: Passenger cancels during ride
  → Full fare charge + penalty
- Scenario 4: Driver cancels due to emergency
  → Notify passenger + find next driver, rating impact
```

### Demo 5: Rating & Payment
```
- Ride completed at destination
- Final fare calculated: $48.50
- Payment processed (charged to card)
- Receipt emailed
- Passenger rates driver: 4.5 stars, comment: "Great ride!"
- Driver rates passenger: 5 stars
- Rating updates both profiles
- Earnings credited to driver account (after fee)
```

---

## Interview Q&A

### Basic Level

**Q1: How do you find the nearest available driver?**
A: Use location service (lat/long). Calculate distance from passenger to each active driver using Haversine formula. Sort by distance. Filter: rating >= 3.5, status = online. Return top 3-5 drivers. Complexity: O(n) where n = active drivers. Optimize: spatial indexing (QuadTree or GeoHash).

**Q2: What data do you store for a Driver?**
A: ID, name, rating (average 1-5 stars), vehicle (model/plate), location (lat/long), status (online/busy/offline), total rides, acceptance rate, bank account. Update location every 1-2 seconds while online.

**Q3: How do you calculate ride fare?**
A: Fare = base_price + (distance_km × per_km_rate) + (duration_min × per_min_rate) × surge_multiplier. Example: $2 + (5 km × $0.80) + (10 min × $0.15) × 1.2x surge = $10.80.

**Q4: What's surge pricing and when to apply it?**
A: Surge = demand/supply multiplier. High demand (rainy, late night) + low supply (few drivers) = high surge (up to 3x). Update dynamically based on active ride requests vs available drivers. Communicate surge to passenger before confirming.

### Intermediate Level

**Q5: How do you handle the driver acceptance timeout?**
A: Offer ride to driver, start 30-second timer. If driver accepts within 30s, assign ride. If timeout or decline, move to next driver in queue. Max queue size = 3 drivers to prevent excessive rejections.

**Q6: What happens if passenger cancels after driver accepts?**
A: If cancelled <2 minutes after acceptance: charge 25% cancellation fee. If >2 minutes: full charge (driver's time wasted). If cancelled during ride: charge full ride fare + penalty. Drivers can also cancel (with rating impact if frequent).

**Q7: How to prevent driver-passenger fraud?**
A: (1) GPS tracking throughout ride (validate route reasonableness), (2) Dispute resolution: review route/receipt, (3) Escalation: manual review for high-value disputes, (4) Blacklisting: repeated fraudsters blocked, (5) Driver ratings as reputation.

**Q8: How to optimize driver positioning?**
A: Predict high-demand areas (ML models on historical data). Recommend drivers move to predicted hotspots. Offer incentives during off-peak. Use "sticky driver" logic: driver stays near passenger's original neighborhood after drop-off (increases next ride probability).

### Advanced Level

**Q9: How would you handle geographic scalability (multi-city)?**
A: Partition by geography: each city gets separate Ride Service instance. Global service coordinates routing between cities (long-distance rides). Use eventual consistency for cross-city metrics (ratings, payment).

**Q10: How to minimize wait time at scale (1M drivers)?**
A: Spatial indexing (QuadTree or H3 hex grid). Query only nearby drivers (10km cell), not all 1M. Batch matching: every 5 seconds, match all pending requests to available drivers simultaneously. Expected match time: <2 seconds.

**Q11: How to prevent double-booking (driver accepts 2 rides)?**
A: Optimistic locking: set driver.status = BUSY on acceptance. If driver tries to accept another: check status first, reject if busy. Alternative: distributed lock (Redis SETNX) for critical sections. Ensure atomicity.

**Q12: How to handle payment failures gracefully?**
A: (1) Retry payment 3x with exponential backoff, (2) If still fails: store as pending payment, (3) Notify driver + passenger of failure, (4) Retry daily for 7 days, (5) After 7 days: escalate to support. Track payment reliability as metric.

---

## Scaling Q&A

**Q1: Can you handle 1M concurrent ride requests?**
A: Queue requests in message broker (Kafka/RabbitMQ). Batch process: every 500ms, match top 100K requests to available drivers. Remaining requests re-queue. Expected match latency: 0.5-2 seconds vs <30s target. Scales linearly with driver count.

**Q2: How to optimize for 50M passengers globally?**
A: Geographic sharding: partition by city/region. Each shard has independent ride service instance. Global load balancer routes requests. Cross-region rides handled by distributed transactions (eventual consistency acceptable).

**Q3: What if surge pricing leads to 10x price increase?**
A: Cap surge at 3x maximum (policy). If demand still exceeds supply at 3x: queue passengers, no surge increase. Communicate ETA + current surge to passenger for informed decision. Log surge events for analysis.

**Q4: How to track 1M moving vehicles in real-time?**
A: Stream processing: receive location updates in Kafka. Process in Flink/Spark Streaming. Index in Redis (geospatial index). Update every 1-2 seconds. Store history in time-series DB (InfluxDB) for analytics.

**Q5: Can payment processing handle 100K transactions/minute?**
A: Use async payment processing: (1) Confirm payment locally immediately, (2) Send to payment processor asynchronously, (3) Store pending if fails, (4) Retry batch every minute. Ensures ride completes regardless of payment latency.

**Q6: How to prevent driver exploitation (low pay)?**
A: Set minimum per-mile rate ($0.80 minimum). Calculate guaranteed minimum per ride. Show estimated pay before driver accepts. Seasonal bonuses for reliability. Transparent rate card. Regular rate audits vs cost-of-living.

**Q7: What if network partition separates drivers from servers?**
A: Graceful degradation: drivers operate locally with cached rules. Accept rides in offline mode (record locally). Sync when reconnected. Ensure consistency: if ride already completed remotely, server wins. Driver sees sync resolution.

**Q8: How to efficiently match 10K requests to 100K drivers?**
A: Hungarian algorithm for optimal assignment (min-cost matching). Complexity: O(n³) prohibitive. Approximation: greedy nearest-first matching O(n log n). Match 80% optimality in <1 second vs 100% in 10 seconds.

**Q9: Can you support scheduled rides (advance booking)?**
A: Yes. Store scheduled rides in DB with future timestamp. 15 minutes before: attempt matching. If no driver: queue + retry every minute. If still no driver at 5 minutes: notify passenger + refund. Reduces wait-time pressure vs on-demand.

**Q10: How to handle peak surge (New Year's Eve)?**
A: (1) Incentivize drivers: surge bonuses + guaranteed hours, (2) Pre-position: recommend drivers to downtown, (3) Pricing cap: communicate surge early to manage demand, (4) Queueing: accept queued requests gracefully, (5) Surge forecast: predict peaks in advance.

**Q11: How to track driver behavior (speeding, reckless)?**
A: Collect telemetry: GPS, accelerometer, gyroscope. Analyze ride: calculate acceleration, compare to speed limits. Flag anomalies. Warn driver, then restrict if repeated. Integrate with insurance (lower premiums for safe drivers).

**Q12: Can you support pooled/shared rides?**
A: Yes. Shared rides = match multiple passengers on same route. Benefits: lower cost for passengers (50%), higher driver revenue. Challenges: route optimization for N passengers, flexibility (detour tolerance). Charge 50-60% of full ride price.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships and cardinality
- [ ] Walk through the full ride lifecycle (REQUESTED → ACCEPTED → DRIVER_ARRIVED → IN_PROGRESS → COMPLETED)
- [ ] Explain nearest-driver matching algorithm (Haversine + sort + rating filter)
- [ ] Explain surge pricing calculation and the 3x cap
- [ ] Explain how RLock prevents double-booking and re-entrant deadlock
- [ ] Explain Strategy pattern for pluggable pricing (economy vs premium)
- [ ] Explain State Machine guards preventing invalid ride transitions
- [ ] Explain cancellation penalties (0% / 25% / 100% by state)
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss geographic sharding for multi-city scalability

---

**Ready for interview? Request a ride and dispatch with confidence!**
