# Parking Lot System - Interview Guide

## Overview

A comprehensive parking lot management system demonstrating **SOLID principles**, **design patterns**, and scalable architecture.

### Key Metrics
- **Lines of Code**: ~1,200 (production) / ~420 (interview compact)
- **Design Patterns**: 6
- **SOLID Principles**: 5/5
- **Complexity**: O(1) spot assignment, O(N) for search
- **Interview Time**: 75 minutes

---

## Functional Requirements (FR)

| # | Requirement | Details | Priority |
|---|---|---|---|
| FR1 | Entry Gate | Issue ticket on vehicle entry, find available spot | MUST |
| FR2 | Exit Gate | Validate ticket, calculate fee, process payment | MUST |
| FR3 | Spot Management | Support 4 vehicle types, track availability | MUST |
| FR4 | Payment System | Cash/credit card, generate receipt | MUST |
| FR5 | Display Board | Show available spots by type in real-time | MUST |
| FR6 | Multiple Lots | Support multiple independent parking lots | SHOULD |
| FR7 | Admin Features | Add/remove spots, manage rates, user accounts | SHOULD |
| FR8 | Full Lot Handling | Reject entry when lot is full | MUST |

---

## Non-Functional Requirements (NFR)

| # | Requirement | Details | Target |
|---|---|---|---|
| NFR1 | Availability | System up 24/7, fault-tolerant | 99.5% uptime |
| NFR2 | Performance | Spot assignment < 100ms, ticket generation < 50ms | Real-time |
| NFR3 | Concurrency | Handle 100+ simultaneous entries/exits | Thread-safe |
| NFR4 | Scalability | Support 1000s of spots, multiple lots | Horizontal |
| NFR5 | Security | Secure payment, validate tickets | PCI-DSS compliant |
| NFR6 | Auditability | All transactions logged | Full history |
| NFR7 | Usability | Simple API, clear error messages | Developer-friendly |
| NFR8 | Maintainability | Modular design, easy to extend | SOLID adherence |

---

## Design Patterns Used

### 1. **Singleton Pattern** ✓
**Class**: `ParkingLot`
```python
@classmethod
def get_instance(cls):
    if cls._instance is None:
        cls._instance = ParkingLot()
    return cls._instance
```
**Why**: Ensures single parking lot instance across system  
**Benefit**: Prevents duplicate lot creation, centralized access

---

### 2. **Strategy Pattern** ✓
**Classes**: `SpotFinder`, `PricingStrategy`
```python
class SpotFinder(ABC):
    @abstractmethod
    def find_spot(self, lot, vehicle):
        pass

class NearestSpotFinder(SpotFinder):
    def find_spot(self, lot, vehicle):
        # Find nearest available spot
        pass

class LargestSpotFinder(SpotFinder):
    def find_spot(self, lot, vehicle):
        # Find largest available spot
        pass
```
**Why**: Different strategies for spot assignment and pricing  
**Benefit**: Easily swap algorithms without changing core logic

---

### 3. **Factory Pattern** ✓
**Classes**: `VehicleFactory`, `SpotFactory`, `PaymentFactory`
```python
class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_type, license_no):
        if vehicle_type == "car":
            return Car(license_no)
        elif vehicle_type == "motorcycle":
            return Motorcycle(license_no)
        # ...
```
**Why**: Encapsulates vehicle/spot/payment creation  
**Benefit**: Easy to add new types without changing existing code

---

### 4. **Observer Pattern** ✓
**Classes**: `DisplayBoard`, `ParkingLot`
```python
class Observer(ABC):
    @abstractmethod
    def update(self, **kwargs):
        pass

class DisplayBoard(Observer):
    def update(self, **kwargs):
        self.render()
```
**Why**: Notify display boards of parking changes in real-time  
**Benefit**: Loose coupling, multiple observers supported

---

### 5. **State Pattern** ✓
**Classes**: `ParkingSpot`, `ParkingTicket`
- ParkingSpot: FREE → OCCUPIED → FREE
- ParkingTicket: ISSUED → IN_USE → PAID → VALIDATED
**Why**: Encapsulates state transitions  
**Benefit**: Type-safe, prevents invalid transitions

---

### 6. **Decorator Pattern** ✓
**Classes**: `ParkingRate`, `Receipt`
```python
class Receipt:
    def __init__(self, ticket):
        self.ticket = ticket
        
    def generate(self):
        # Decorate ticket with payment info
        pass
```
**Why**: Add pricing/receipt generation without modifying core classes  
**Benefit**: Composable functionality

---

## SOLID Principles

### S - Single Responsibility Principle ✓
```
ParkingSpot      → Manages spot state only
ParkingTicket    → Manages ticket data only
Entrance         → Handles entry logic only
Exit             → Handles exit logic only
Payment          → Handles payment only
```
**Each class has ONE reason to change**

### O - Open/Closed Principle ✓
```
Vehicle (open for extension)
├── Car
├── Van
├── Truck
└── Motorcycle

ParkingSpot (open for extension)
├── Compact
├── Large
├── Handicapped
└── MotorcycleSpot
```
**Open for extension via subclasses, closed for modification**

### L - Liskov Substitution Principle ✓
```python
def assign_vehicle(self, vehicle: Vehicle):
    # Works with any Vehicle subclass
    # Car, Van, Truck, Motorcycle all behave consistently
    pass
```
**All subclasses can replace parent without breaking code**

### I - Interface Segregation Principle ✓
```
Observer (just update)
├── DisplayBoard
├── Logger
└── Notifier

PricingStrategy (just calculate)
├── HourlyRate
├── DailyRate
└── MonthlyRate
```
**Classes only depend on interfaces they use**

### D - Dependency Inversion Principle ✓
```python
class Entrance:
    def __init__(self, spot_finder: SpotFinder):
        self.spot_finder = spot_finder
    
    def get_ticket(self, vehicle):
        # Depends on abstraction, not concrete class
        spot = self.spot_finder.find_spot(...)
```
**Depend on abstractions, not concrete classes**

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                 PARKING LOT SYSTEM                  │
└─────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼───┐         ┌────▼────┐        ┌──▼────┐
    │ENTRANCE│        │PARKING   │        │ EXIT  │
    │ Gate   │        │  LOT     │        │ Gate  │
    └────┬──┘         └────┬─────┘        └──┬───┘
         │                  │                  │
         │ Issue Ticket     │ Manage Spots    │ Validate
         │                  │ Notify Display  │ Calculate Fee
         │                  │                  │
    ┌────▼───────────────────────────────────▼─┐
    │       PARKING LOT (Singleton)             │
    ├───────────────────────────────────────────┤
    │ - spots: Dict[int, ParkingSpot]          │
    │ - tickets: Dict[str, ParkingTicket]      │
    │ - displays: List[DisplayBoard]           │
    │ - pricing_strategy: PricingStrategy      │
    │ - spot_finder: SpotFinder                │
    └───────────────────────────────────────────┘
         │                  │                  │
    ┌────▼─┐        ┌──────▼──────┐      ┌───▼────┐
    │SPOTS │        │  TICKETS    │      │DISPLAYS│
    ├──────┤        ├─────────────┤      ├────────┤
    │Types:│        │ Entry Time  │      │ Type   │
    │ Comp │        │ Exit Time   │      │ Layout │
    │ Large│        │ Amount      │      │ Update │
    │Hand. │        │ Status      │      │ Render │
    │Cycle │        └─────────────┘      └────────┘
    └──────┘
         │
    ┌────▼─────────┐
    │   PAYMENT    │
    ├──────────────┤
    │ Cash         │
    │ CreditCard   │
    │ Debit        │
    └──────────────┘
```

---

## State Machines

### ParkingSpot State Machine
```
    ┌─────────┐
    │  FREE   │◄──────────────┐
    └────┬────┘               │
         │ assign_vehicle()   │
         │                    │
    ┌────▼──────┐    remove_vehicle()
    │ OCCUPIED  ├────────────┐
    └───────────┘            │
                             │
                        (cleanup)
```

### ParkingTicket State Machine
```
    ┌────────┐
    │ ISSUED │
    └───┬────┘
        │ vehicle enters
        ▼
    ┌────────┐
    │ IN_USE │
    └───┬────┘
        │ vehicle exits
        ▼
    ┌────────┐
    │  PAID  │
    └───┬────┘
        │ verify at exit
        ▼
    ┌──────────┐
    │VALIDATED │
    └──────────┘
```

### Vehicle Entry Flow
```
    Vehicle arrives
         │
         ▼
    ┌──────────────────┐
    │ Entrance Gate    │
    │ check_if_full()  │
    └────┬──────┬──────┘
         │      │
        NO     YES
         │      │
         ▼      ▼
    Issue    Reject
    Ticket   Entry
         │
         ▼
    ┌──────────────────┐
    │ Find Spot        │
    │ by Vehicle Type  │
    └────┬──────┬──────┘
         │      │
       Found  Not Found
         │      │
         ▼      ▼
    Assign   Return
    Spot     null
         │
         ▼
    ┌──────────────────┐
    │ Update Display   │
    │ Notify Observers │
    └──────────────────┘
```

---

## Class Hierarchy

```
Vehicle (Abstract)
├── Car
├── Van
├── Truck
└── Motorcycle

ParkingSpot (Abstract)
├── Compact
├── Large
├── Handicapped
└── MotorcycleSpot

Payment (Abstract)
├── Cash
├── CreditCard
└── Debit

PricingStrategy (Abstract)
├── HourlyRate
├── DailyRate
└── MonthlyRate

Observer (Abstract)
├── DisplayBoard
├── Logger
└── EmailNotifier

Account (Abstract)
├── Admin
└── User
```

---

## Key Algorithms

### 1. Spot Finding Algorithm
```
Time: O(N) where N = number of spots
Space: O(1)

Algorithm:
1. Get vehicle type (car → compact/large, motorcycle → motorcycle spot)
2. Iterate through all spots of that type
3. Return first available spot
4. If none found, return null

Optimization:
- Use hash map by spot type for O(K) where K = spots of type
- Cache nearest spot with quick lookup
```

### 2. Payment Calculation
```
Time: O(1)
Space: O(1)

Algorithm:
1. Get ticket entry_time and exit_time
2. Calculate duration in hours
3. Apply pricing strategy
4. Add taxes/fees if any
5. Return total amount

Example:
- Entry: 10:00 AM, Exit: 1:00 PM
- Duration: 3 hours
- Rate: $5/hour
- Total: $15
```

### 3. Spot Assignment Strategy
```
Option 1: Nearest Available (O(N))
- Find closest spot to entrance
- Minimize customer walking distance

Option 2: Largest Available (O(N))
- Prefer large spots for cars
- Reserve small spots for motorcycles

Option 3: Load Balancing (O(N))
- Distribute vehicles evenly across spots
- Prevent hotspots

Option 4: Smart Assignment (O(N log N))
- Consider exit path for faster checkout
- Minimize traffic congestion
```

---

## Time Complexity Analysis

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| get_ticket() | O(N) | O(1) | N = number of spots |
| validate_ticket() | O(1) | O(1) | Direct lookup by ticket_no |
| find_spot() | O(N) | O(1) | Linear search in worst case |
| add_spot() | O(1) | O(1) | Direct insertion |
| update_display() | O(M) | O(1) | M = number of displays |
| calculate_fee() | O(1) | O(1) | Simple arithmetic |

---

## Interview Talking Points

### "Tell me about the patterns you used"
**Answer**: 
"I used 6 design patterns:
1. **Singleton** for ParkingLot (one instance across system)
2. **Strategy** for spot finding and pricing (swap algorithms)
3. **Factory** for vehicle/spot/payment creation (encapsulate creation)
4. **Observer** for display boards (real-time updates)
5. **State** for spot and ticket states (type-safe transitions)
6. **Decorator** for receipts (add functionality)

Each pattern solves a specific problem - Singleton ensures central access, Strategy allows algorithm swapping, etc."

### "How would you handle concurrent entries?"
**Answer**:
"Use thread-safe data structures:
- Use `threading.Lock` or `queue.Queue` for thread safety
- Use `dict` with atomic operations
- Implement double-check locking for spot assignment
- Use `concurrent.futures` for parallel ticket issuance

Example:
```python
with self.lock:
    if self.spots[spot_id].is_free:
        self.spots[spot_id].assign_vehicle(vehicle)
```

This prevents race conditions where two vehicles get same spot."

### "What if the lot is full?"
**Answer**:
"Implement rejection logic:
```python
if self.is_full():
    return None  # or raise exception
```

We could also:
- Implement a waiting queue
- Notify when a spot becomes available
- Implement reservation system
- Redirect to nearby lots

For now, simply reject entry and display 'LOT FULL' on board."

### "How would you extend this for multiple lots?"
**Answer**:
"Instead of Singleton pattern:
```python
class ParkingManager:
    def __init__(self):
        self.lots = {}  # Dict[lot_id, ParkingLot]
    
    def find_nearby_lot(self, location):
        # Find nearest available lot
        pass
```

Benefits:
- Support chain of parking lots
- Distribute load across lots
- Implement failover if one lot full
- Track across multiple locations"

### "How does pricing work?"
**Answer**:
"Uses Strategy pattern:
```python
class PricingStrategy(ABC):
    def calculate(self, ticket):
        pass

class HourlyRate(PricingStrategy):
    def calculate(self, ticket):
        hours = (ticket.exit_time - ticket.entry_time).total_seconds() / 3600
        return hours * self.rate_per_hour
```

We can easily swap:
- Hourly charging
- Daily flat rate
- Monthly subscriptions
- Dynamic pricing (peak/off-peak)"

### "What about payment failures?"
**Answer**:
"Implement retry logic:
```python
class Payment:
    def initiate_transaction(self):
        for attempt in range(3):
            try:
                return self.process()
            except PaymentError:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
```

Also:
- Log all transactions
- Implement rollback if payment fails
- Store partial receipts
- Alert payment processor of failures"

### "How do you test this system?"
**Answer**:
"Unit tests for each component:
```python
def test_spot_assignment():
    lot = ParkingLot()
    car = Car('ABC-123')
    ticket = lot.get_ticket(car)
    assert ticket is not None
    assert lot.spots[ticket.spot_id].is_free == False

def test_payment_calculation():
    ticket = ParkingTicket()
    ticket.entry_time = datetime(2024, 11, 27, 10, 0)
    ticket.exit_time = datetime(2024, 11, 27, 13, 0)
    fee = calculate_fee(ticket)
    assert fee == 15  # 3 hours * $5/hour
```

Integration tests:
- Entry → Assignment → Exit → Payment → Validation"

---

## Edge Cases

| Case | Handling | Code |
|------|----------|------|
| Lot full | Reject entry, return None | `if is_full(): return None` |
| Invalid vehicle type | Use factory with validation | `VehicleFactory.create()` |
| Payment failure | Retry with exponential backoff | `retry(max_attempts=3)` |
| Ticket expired | Check timestamp, enforce limit | `validate_expiry()` |
| Concurrent access | Use locks, atomic operations | `with lock: ...` |
| Lost ticket | Look up by license plate | `find_by_vehicle()` |

---

## Performance Characteristics

### Spot Finding
- **Average**: O(N/4) - on average check 1/4 of spots
- **Best**: O(1) - spot at entrance free
- **Worst**: O(N) - all spots occupied except last one

### Memory Usage
- Per spot: ~200 bytes
- Per ticket: ~300 bytes
- Per vehicle: ~100 bytes
- 1000-spot lot: ~500 KB data

### Throughput
- Entry processing: ~100-500 vehicles/minute (depends on hardware)
- Exit processing: ~50-200 vehicles/minute (includes payment)
- Display updates: Real-time (< 100ms)

---

## Common Interview Extensions

**Q1**: "How would you handle monthly subscriptions?"
**A1**: Create `SubscriptionVehicle` class with flat monthly fee

**Q2**: "What about reserved spots for VIPs?"
**A2**: Add `is_reserved` and `reserved_for` fields to ParkingSpot

**Q3**: "How do you handle peak hour pricing?"
**A3**: Use time-based pricing strategy with peak/off-peak rates

**Q4**: "Can customers reserve spots in advance?"
**A4**: Create `Reservation` class with time-based hold

**Q5**: "How to implement parking validation for retailers?"
**A5**: Add `is_validated` flag, integrate with retail system

**Q6**: "How about electric vehicle charging spots?"
**A6**: Create `ChargingSpot` subclass with charging logic

**Q7**: "How to track lost tickets?"
**A7**: Implement ticket lookup by license plate with penalty fee

**Q8**: "How to implement loyalty program?"
**A8**: Create `Account` class with loyalty points tracking

---

## Summary

**Parking Lot System demonstrates:**
- ✅ 6 Design Patterns (Singleton, Strategy, Factory, Observer, State, Decorator)
- ✅ 5 SOLID Principles (SRP, OCP, LSP, ISP, DIP)
- ✅ Real-world problem solving
- ✅ Clean, modular architecture
- ✅ Scalable design
- ✅ Thread-safe operations
- ✅ Edge case handling
- ✅ Performance optimization

**Perfect for interviews because:**
- Shows system design thinking
- Demonstrates design patterns in practice
- Handles multiple requirements
- Extensible and maintainable
- Real-world applicable
