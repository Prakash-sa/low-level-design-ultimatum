# Ride-Sharing System - Reference Guide

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
