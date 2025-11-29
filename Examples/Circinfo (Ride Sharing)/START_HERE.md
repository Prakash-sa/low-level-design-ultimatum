# Ride-Sharing System - Quick Start (5 Minutes)

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

## 5 Design Patterns (Why Each Matters)

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
