# Restaurant Management System — Complete Design Guide

> Reservation lifecycle, table occupancy management, order coordination, kitchen ticketing, flexible pricing strategies, and accurate bill generation.

**Scale**: 100+ concurrent customers, 50+ tables, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Table double-booking prevention, order state machine, kitchen coordination, strategy-based pricing

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
Restaurants manage multiple concurrent operations: reservations, table occupancy, food ordering, kitchen coordination, and payment. A customer reserves a table → checks in → places an order → kitchen prepares → bill is generated with pricing strategy → payment is processed → table is freed. Core concerns: prevent double-booking via atomic reservation, coordinate kitchen workflow via tickets, and compute bills accurately with pluggable pricing.

### Core Flow
```
Reservation → Check-in → Order → Kitchen → Billing → Payment → Cleanup
                              ↓ or no-show (15 min)
                          Table released (FREE)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single location or multi-restaurant?** → "Single restaurant for now; mention multi-location as a scaling concern"
2. **Walk-in only or reservations too?** → "Both — support reservations and walk-in check-in"
3. **Real payment gateway?** → "Mock payment service for interview"
4. **Kitchen display or manual coordination?** → "KitchenTicket objects track preparation status"
5. **Loyalty / membership pricing?** → "Yes — support pluggable pricing strategies (Regular, HappyHour, Member)"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Reserve & dine | Reserve table, check in, place order, pay bill |
| **Waiter / Staff** | Table & order management | Assign tables, take orders, mark items served |
| **Kitchen Staff** | Food preparation | Update ticket status (PREPARING → READY) |
| **Manager / Admin** | System configuration | Set pricing strategy, add menu items, monitor tables |
| **System** | Coordinator & automation | Expire no-show reservations, generate bills, notify observers |

### Functional Requirements (What does the system do?)

✅ **Reservation Management**
  - Customer reserves a table for a time slot
  - Prevent double-booking of the same table at the same time
  - Auto-expire reservation after 15-minute no-show window

✅ **Table Management**
  - Track table status: FREE, RESERVED, OCCUPIED
  - Check in a reservation (RESERVED → OCCUPIED)
  - Release table on payment (OCCUPIED → FREE)

✅ **Order Management**
  - Place an order linked to a table
  - Add/modify items before kitchen receives
  - Order lifecycle: RECEIVED → PREPARING → READY → SERVED → PAID

✅ **Kitchen Coordination**
  - Auto-generate KitchenTicket on order placement
  - Kitchen staff updates ticket status
  - Mark order READY when all items prepared

✅ **Menu & Pricing**
  - Maintain menu with item prices and availability
  - Apply pluggable pricing strategies (Regular, HappyHour, Member)
  - Calculate subtotal, tax, service charge, and discount

✅ **Bill & Payment**
  - Generate accurate bill per order
  - Support multiple payment methods (mock)
  - Mark table FREE after payment

✅ **Notifications**
  - Notify on reservation, order placed, order ready, payment completed
  - Support multiple channels (email, console, kitchen display)

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 100+ concurrent customers  
✅ **Consistency**: No double-booking (table can only be reserved by ONE party at a time)  
✅ **Latency**: <500ms reservation lookup, <200ms order placement, <1s bill calculation  
✅ **Availability**: 99.9% uptime  
✅ **Audit**: All order and payment events logged  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Multi-location?** | NO — single restaurant instance |
| **Real payment?** | NO — mock payment service |
| **Inventory management?** | NO — out of scope |
| **Delivery orders?** | NO — dine-in only |
| **No-show timeout** | 15 minutes after reservation time |
| **Order modification window** | Only in RECEIVED state (locked once PREPARING) |
| **Max party size per table** | Determined by table capacity attribute |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Table, Reservation, MenuItem, Order, KitchenTicket, Bill, Payment, Staff, Restaurant, ...
```

### Step 2.2: Define Core Classes

#### **Table** — A physical seating unit
```
Properties:
  - table_id: str (e.g., "T1", "T2")
  - capacity: int (number of seats)
  - status: TableStatus (FREE, RESERVED, OCCUPIED)
  - location: str (e.g., "window", "patio")

Behaviors:
  - is_free(): Check if available
  - reserve(): Transition FREE → RESERVED
  - check_in(): Transition RESERVED → OCCUPIED
  - release(): Transition OCCUPIED → FREE
```

#### **Reservation** — A customer's time-slot hold on a table
```
Properties:
  - reservation_id: str
  - customer_name: str
  - customer_email: str
  - table: Table
  - party_size: int
  - reserved_at: datetime
  - status: ReservationStatus (PENDING, CHECKED_IN, CANCELLED, NO_SHOW)

Behaviors:
  - check_in(): Mark as CHECKED_IN, transition table to OCCUPIED
  - cancel(): Mark as CANCELLED, release table to FREE
  - is_no_show(timeout_minutes): Check if time has passed with no check-in
```

#### **MenuItem** — A single item on the menu
```
Properties:
  - item_id: str
  - name: str
  - price: float
  - category: str (e.g., "Starter", "Main", "Dessert", "Drink")
  - available: bool

Behaviors:
  - is_available(): Check if can be ordered
```

#### **Order** — A customer order linked to a table
```
Properties:
  - order_id: str
  - table: Table
  - items: List[Tuple[MenuItem, int]] (item + quantity pairs)
  - status: OrderStatus (RECEIVED, PREPARING, READY, SERVED, PAID, CANCELLED)
  - created_at: datetime

Behaviors:
  - add_item(item, qty): Add/update item (only in RECEIVED state)
  - get_subtotal(): Sum of item.price × qty
  - advance_status(): Move to next valid state in workflow
```

#### **Bill** — Financial summary for an order
```
Properties:
  - bill_id: str
  - order: Order
  - subtotal: float
  - discounted_amount: float (after pricing strategy)
  - tax: float
  - service_charge: float
  - total: float
  - paid: bool

Behaviors:
  - calculate(strategy): Apply pricing strategy and compute total
  - mark_paid(): Set paid = True
```

#### **Staff** — A restaurant employee
```
Properties:
  - staff_id: str
  - name: str
  - role: str (e.g., "Waiter", "Chef", "Manager")

Behaviors:
  - (data holder — actions invoked via RestaurantSystem)
```

#### **RestaurantSystem** — Main controller (Singleton)
```
Properties:
  - tables: Dict[str, Table]
  - reservations: Dict[str, Reservation]
  - menu: Dict[str, MenuItem]
  - orders: Dict[str, Order]
  - bills: Dict[str, Bill]
  - pricing_strategy: PricingStrategy
  - observers: List[RestaurantObserver]
  - _lock: threading.RLock

Behaviors:
  - reserve_table(customer, party_size, time): Create Reservation + hold Table
  - check_in(reservation_id): Activate reservation, mark table OCCUPIED
  - place_order(table_id, items): Create Order + KitchenTicket
  - update_order_status(order_id, status): Advance order state machine
  - calculate_bill(order_id): Generate Bill with pricing strategy
  - process_payment(bill_id): Mark bill paid, release table
  - expire_no_shows(): Background job releasing abandoned reservations
  - set_pricing_strategy(strategy): Swap pricing at runtime
  - add_observer / notify_observers
```

### Step 2.3: Define Enumerations (State & Type)

```python
class TableStatus(Enum):
    FREE = "free"           # Available for reservation or walk-in
    RESERVED = "reserved"   # Held by a reservation, awaiting check-in
    OCCUPIED = "occupied"   # Guests seated and ordering

class ReservationStatus(Enum):
    PENDING = "pending"         # Reserved, not yet checked in
    CHECKED_IN = "checked_in"  # Guest arrived, table occupied
    CANCELLED = "cancelled"     # Reservation cancelled by customer
    NO_SHOW = "no_show"         # Guest did not arrive within timeout

class OrderStatus(Enum):
    RECEIVED = "received"       # Order placed, not yet sent to kitchen
    PREPARING = "preparing"     # Kitchen actively preparing
    READY = "ready"             # Food ready, awaiting service
    SERVED = "served"           # Delivered to table
    PAID = "paid"               # Bill settled
    CANCELLED = "cancelled"     # Order cancelled

class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    DIGITAL = "digital"
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Table** | Track physical seating status | Can't prevent double-booking |
| **Reservation** | Time-slot hold with lifecycle | No advance planning, no no-show detection |
| **MenuItem** | Priced, categorized menu items | Can't compute subtotals or enforce availability |
| **Order** | Group items with state machine | No kitchen coordination, no order tracking |
| **Bill** | Financial calculation with strategy | Can't apply discounts or compute accurate totals |
| **Staff** | Actor identity for audit trails | No accountability |
| **RestaurantSystem** | Central thread-safe controller | No single source of truth, race conditions |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Reserve Table** ⭐ CRITICAL
```python
def reserve_table(customer_name: str, customer_email: str,
                  party_size: int, reserved_at: datetime) -> Optional[Reservation]:
    """
    Find a free table of sufficient capacity and reserve it.

    Precondition: at least one table with capacity >= party_size and status == FREE
    Postcondition: table.status == RESERVED, reservation.status == PENDING

    Returns: Reservation object with reservation_id on success, None if no table.

    Raises:
      - NoTableAvailableError: No table fits the party size
      - InvalidPartySizeError: party_size <= 0

    Concurrency: THREAD-SAFE with atomic table status transition
    Response Time: <500ms
    """
    pass
```

#### **2. Check In** ⭐ CRITICAL
```python
def check_in(reservation_id: str) -> bool:
    """
    Activate a reservation — mark table OCCUPIED.

    Precondition: reservation.status == PENDING
    Postcondition: reservation.status == CHECKED_IN, table.status == OCCUPIED

    Returns: True on success, False on failure.

    Raises:
      - ReservationNotFoundError: Invalid reservation ID
      - ReservationAlreadyUsedError: Already checked in / cancelled

    Concurrency: THREAD-SAFE
    Response Time: <200ms
    """
    pass
```

#### **3. Place Order** ⭐ CRITICAL
```python
def place_order(table_id: str,
                items: List[Tuple[str, int]]) -> Optional[Order]:
    """
    Create an order for a table and emit a KitchenTicket.

    Precondition: table.status == OCCUPIED; all item_ids valid and available
    Postcondition: order.status == RECEIVED; KitchenTicket generated

    Returns: Order object with order_id.

    Raises:
      - TableNotOccupiedError: Table is not OCCUPIED
      - MenuItemNotFoundError: Unknown item_id
      - MenuItemUnavailableError: Item marked unavailable

    Concurrency: THREAD-SAFE
    Side Effects: Notifies KitchenObserver with ORDER_PLACED event
    """
    pass
```

#### **4. Update Order Status**
```python
def update_order_status(order_id: str, new_status: OrderStatus) -> bool:
    """
    Advance an order through its state machine.

    Valid transitions: RECEIVED→PREPARING, PREPARING→READY, READY→SERVED

    Returns: True on success, False if transition is invalid.

    Raises:
      - OrderNotFoundError: Unknown order_id
      - InvalidStatusTransitionError: Illegal state change
    """
    pass
```

#### **5. Calculate Bill**
```python
def calculate_bill(order_id: str) -> Bill:
    """
    Generate a Bill for a served order using the active pricing strategy.

    formula: subtotal → strategy.apply(subtotal) → + tax (10%) → + service (5%) → total

    Returns: Bill object with itemised amounts.

    Raises:
      - OrderNotFoundError: Unknown order_id
      - OrderNotServedError: Order must be in SERVED status to bill
    """
    pass
```

#### **6. Process Payment**
```python
def process_payment(bill_id: str, method: PaymentMethod) -> bool:
    """
    Mark bill as paid and release the table.

    Postcondition: bill.paid == True, table.status == FREE, order.status == PAID

    Returns: True on success.

    Raises:
      - BillNotFoundError: Unknown bill_id
      - BillAlreadyPaidError: Bill already settled

    Side Effects: Notifies observers with PAYMENT_COMPLETED event
    """
    pass
```

#### **7. Set Pricing Strategy**
```python
def set_pricing_strategy(strategy: PricingStrategy) -> None:
    """
    Swap pricing algorithm at runtime.
    Affects next calculate_bill() call onward.
    """
    pass
```

#### **8. Expire No-Shows** (Background Job)
```python
def expire_no_shows(timeout_minutes: int = 15) -> None:
    """
    Scan PENDING reservations. If now > reserved_at + timeout, mark NO_SHOW and free table.
    Called every 5 minutes by a scheduler.
    """
    pass
```

### Step 3.2: Exception Hierarchy

```python
class RestaurantException(Exception):
    """Base exception"""
    pass

class NoTableAvailableError(RestaurantException):
    """No table fits the party"""
    pass

class ReservationNotFoundError(RestaurantException):
    """Invalid reservation ID"""
    pass

class TableNotOccupiedError(RestaurantException):
    """Table must be OCCUPIED to place order"""
    pass

class MenuItemUnavailableError(RestaurantException):
    """Item is out of stock / marked unavailable"""
    pass

class InvalidStatusTransitionError(RestaurantException):
    """Illegal order state change"""
    pass

class OrderNotServedError(RestaurantException):
    """Order must be SERVED before billing"""
    pass

class BillAlreadyPaidError(RestaurantException):
    """Duplicate payment attempt"""
    pass
```

### Step 3.3: API Usage Example

```python
system = RestaurantSystem.get_instance()

# 1. Reserve a table
reservation = system.reserve_table("Alice", "alice@example.com", 2, datetime.now())

# 2. Check in
system.check_in(reservation.reservation_id)

# 3. Place order
items = [("M001", 2), ("M003", 1)]   # item_id, quantity pairs
order = system.place_order(reservation.table.table_id, items)

# 4. Kitchen progresses
system.update_order_status(order.order_id, OrderStatus.PREPARING)
system.update_order_status(order.order_id, OrderStatus.READY)
system.update_order_status(order.order_id, OrderStatus.SERVED)

# 5. Calculate and pay bill
bill = system.calculate_bill(order.order_id)
print(f"Total: ${bill.total:.2f}")
system.process_payment(bill.bill_id, PaymentMethod.CARD)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
RestaurantSystem HAS-A tables (1:N Composition)
  └─ System owns all Table objects and manages their lifecycle

RestaurantSystem HAS-A reservations (1:N Composition)
  └─ System creates and expires Reservation objects

RestaurantSystem HAS-A orders (1:N Composition)
  └─ System coordinates Order progression and billing

Reservation REFERENCES table (1:1 Association)
  └─ Reservation links to a Table (no ownership)

Order REFERENCES table (1:1 Association)
  └─ Order is tied to a seated Table

Order CONTAINS items (1:N Composition)
  └─ Order owns its list of MenuItem + quantity tuples

Bill REFERENCES order (1:1 Association)
  └─ Bill is computed from an Order

RestaurantSystem USES-A PricingStrategy (1:1 Composition)
  └─ System owns and applies the active pricing algorithm

RestaurantSystem NOTIFIES RestaurantObserver (1:N Association)
  └─ Multiple observers (Kitchen, Email, Console) listen to events
```

### Step 4.2: Complete UML Class Diagram

```
┌───────────────────────────────────────────────────┐
│        RestaurantSystem (Singleton)               │
├───────────────────────────────────────────────────┤
│ - _instance: RestaurantSystem                     │
│ - tables: Dict[str, Table]                        │
│ - reservations: Dict[str, Reservation]            │
│ - menu: Dict[str, MenuItem]                       │
│ - orders: Dict[str, Order]                        │
│ - bills: Dict[str, Bill]                          │
│ - pricing_strategy: PricingStrategy               │
│ - observers: List[RestaurantObserver]             │
│ - _lock: threading.RLock                          │
├───────────────────────────────────────────────────┤
│ + get_instance(): RestaurantSystem                │
│ + reserve_table(...): Reservation                 │
│ + check_in(reservation_id): bool                  │
│ + place_order(table_id, items): Order             │
│ + update_order_status(order_id, status): bool     │
│ + calculate_bill(order_id): Bill                  │
│ + process_payment(bill_id, method): bool          │
│ + set_pricing_strategy(strategy): void            │
│ + expire_no_shows(): void                         │
│ + add_observer(observer): void                    │
│ + notify_observers(event, payload): void          │
└───────────────────────────────────────────────────┘
       │ manages 1:N          │ manages 1:N
       ▼                      ▼
┌────────────────┐   ┌──────────────────────────┐
│     Table      │   │       Reservation         │
├────────────────┤   ├──────────────────────────┤
│ table_id: str  │   │ reservation_id: str       │
│ capacity: int  │◄──│ table: Table              │
│ status: Enum   │   │ customer_name: str        │
│ location: str  │   │ party_size: int           │
├────────────────┤   │ status: ReservationStatus │
│ + is_free()    │   │ reserved_at: datetime     │
│ + reserve()    │   ├──────────────────────────┤
│ + check_in()   │   │ + check_in(): void        │
│ + release()    │   │ + cancel(): void          │
└────────────────┘   │ + is_no_show(min): bool   │
                     └──────────────────────────┘

┌──────────────────────────────────┐
│           Order                  │
├──────────────────────────────────┤
│ order_id: str                    │
│ table: Table                     │
│ items: List[(MenuItem, qty)]     │
│ status: OrderStatus              │
│ created_at: datetime             │
├──────────────────────────────────┤
│ + add_item(item, qty): void      │
│ + get_subtotal(): float          │
│ + advance_status(): void         │
└──────────┬───────────────────────┘
           │ references
           ▼
┌───────────────────────┐   ┌──────────────────────────┐
│      MenuItem         │   │         Bill             │
├───────────────────────┤   ├──────────────────────────┤
│ item_id: str          │   │ bill_id: str             │
│ name: str             │   │ order: Order             │
│ price: float          │   │ subtotal: float          │
│ category: str         │   │ discounted_amount: float │
│ available: bool       │   │ tax: float               │
└───────────────────────┘   │ service_charge: float    │
                            │ total: float             │
                            │ paid: bool               │
                            ├──────────────────────────┤
                            │ + calculate(strategy)    │
                            │ + mark_paid(): void      │
                            └──────────────────────────┘

STRATEGY PATTERN (Pricing):
┌────────────────────────────────────┐
│ PricingStrategy (Abstract)         │
├────────────────────────────────────┤
│ + apply(subtotal: float): float    │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ RegularPricing  (no discount)
   ├─→ HappyHourPricing (20% off)
   └─→ MemberPricing   (15% off)

OBSERVER PATTERN (Notifications):
┌────────────────────────────────────┐
│ RestaurantObserver (Abstract)      │
├────────────────────────────────────┤
│ + update(event, payload)           │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ ConsoleObserver  (logging)
   ├─→ KitchenObserver  (ticket display)
   └─→ EmailObserver    (customer notifications)

STATE MACHINE (Order):
RECEIVED ──→ PREPARING ──→ READY ──→ SERVED ──→ PAID
    └──────────────────────────────────→ CANCELLED
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| RestaurantSystem → Tables | 1:N | Composition | System owns all tables |
| RestaurantSystem → Reservations | 1:N | Composition | System creates/expires reservations |
| RestaurantSystem → Orders | 1:N | Composition | System coordinates order lifecycle |
| RestaurantSystem → Bills | 1:N | Composition | System generates and stores bills |
| Reservation → Table | 1:1 | Association | Reservation links to one table |
| Order → Table | 1:1 | Association | Order tied to one seated table |
| Order → MenuItems | 1:N | Composition | Order owns its item list |
| Bill → Order | 1:1 | Association | Bill computed from one order |
| RestaurantSystem → PricingStrategy | 1:1 | Composition | System owns pricing rule |
| RestaurantSystem → Observers | 1:N | Association | System notifies multiple listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For RestaurantSystem)

**Problem**: Race conditions on table assignment — multiple threads must share one consistent view of table states, reservations, and orders.

**Solution**: One global RestaurantSystem instance with thread-safe initialization via double-checked locking.

```python
class RestaurantSystem:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit test), ⚠️ Does not scale across separate processes without a shared store

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Multiple pricing models (Regular, HappyHour, Member) must coexist and be swappable at runtime without modifying bill calculation logic.

**Solution**: Pluggable strategies implementing a common `apply()` interface.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float) -> float:
        pass

class HappyHourPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.8   # 20% off

class MemberPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.85  # 15% off

class RegularPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal         # no discount

# Runtime swap — no billing logic changes needed
system.set_pricing_strategy(HappyHourPricing())
```

**Benefit**: ✅ Easy to add new pricing tiers (EarlyBird, GroupDiscount), ✅ No billing code changes  
**Trade-off**: ⚠️ Extra abstraction layer; overkill for a single pricing rule

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Kitchen, billing, and customer notifications need real-time updates when orders change state, but coupling kitchen logic into the order system creates a maintenance nightmare.

**Solution**: Abstract Observer interface decouples producers from consumers.

```python
class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class KitchenObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        if event == "ORDER_PLACED":
            print(f"[KITCHEN] New ticket: {payload['order_id']}")

class EmailObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        if event == "PAYMENT_COMPLETED":
            print(f"[EMAIL] Receipt sent to {payload['customer_email']}")

# Usage: Add multiple observers
system.add_observer(KitchenObserver())
system.add_observer(EmailObserver())
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new notification channels (SMS, Slack)  
**Trade-off**: ⚠️ Observer lifecycle management; failed observers should not block the main flow

---

### Pattern 4: **State Enum** (For Order Lifecycle)

**Problem**: An order has valid and invalid state transitions. Allowing arbitrary transitions (e.g., RECEIVED → PAID directly) would corrupt data.

**Solution**: Enum-based state with explicit valid-transition guards.

```python
class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    PAID = "paid"
    CANCELLED = "cancelled"

VALID_TRANSITIONS = {
    OrderStatus.RECEIVED:   {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING:  {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY:      {OrderStatus.SERVED},
    OrderStatus.SERVED:     {OrderStatus.PAID},
}

def update_order_status(order_id, new_status):
    if new_status not in VALID_TRANSITIONS.get(order.status, set()):
        raise InvalidStatusTransitionError(f"{order.status} → {new_status} not allowed")
    order.status = new_status
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions caught at runtime  
**Trade-off**: ⚠️ Transition map must be maintained as states evolve

---

### Pattern 5: **Factory** (For Order Creation)

**Problem**: Order creation involves generating a unique ID, associating a table, validating items, and creating a KitchenTicket — scattered logic creates inconsistency.

**Solution**: Centralize creation inside `place_order()` acting as a factory method.

```python
class OrderFactory:
    _counter = 0

    @staticmethod
    def create(table: Table, items: List[Tuple[MenuItem, int]]) -> 'Order':
        OrderFactory._counter += 1
        order_id = f"ORD{OrderFactory._counter:04d}"
        return Order(order_id, table, items)
```

**Benefit**: ✅ Centralized, consistent initialization, ✅ ID generation in one place  
**Trade-off**: ⚠️ If creation grows complex, graduate to a Builder pattern

---

### Pattern 6: **Command** (For Auditable Operations)

**Problem**: Operations like placing orders and paying bills need to be logged and potentially undone (order cancellation).

**Solution**: Command objects encapsulate an operation as a first-class object.

```python
class PlaceOrderCommand:
    def __init__(self, system, table_id, items):
        self.system = system
        self.table_id = table_id
        self.items = items

    def execute(self):
        return self.system.place_order(self.table_id, self.items)

class PayBillCommand:
    def __init__(self, system, bill_id, method):
        self.system = system
        self.bill_id = bill_id
        self.method = method

    def execute(self):
        return self.system.process_payment(self.bill_id, self.method)
```

**Benefit**: ✅ Uniform interface for all operations, ✅ Enables undo/redo and audit logs  
**Trade-off**: ⚠️ Adds wrapper classes for every operation

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Race conditions on shared restaurant state | Single consistent source of truth |
| **Strategy** | Multiple pricing rules (Regular, HappyHour, Member) | Pluggable, no core-code changes |
| **Observer** | Kitchen, email, and logging need event updates | Loose coupling, event-driven |
| **State (Enum)** | Order transitions must be valid | Invalid moves caught at runtime |
| **Factory** | Consistent order creation with ID generation | Centralized, predictable |
| **Command** | Operations need audit trails and undo | Uniform, loggable, reversible |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Restaurant Management System - Interview Implementation
Demonstrates:
1. Table reservation and guest check-in
2. Order placement with kitchen notification
3. Order status progression (RECEIVED → SERVED)
4. Bill calculation with pluggable pricing strategy
5. Payment processing and table release
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import threading
import uuid

# ============================================================================
# ENUMERATIONS
# ============================================================================

class TableStatus(Enum):
    FREE = "free"
    RESERVED = "reserved"
    OCCUPIED = "occupied"

class ReservationStatus(Enum):
    PENDING = "pending"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    PAID = "paid"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    DIGITAL = "digital"

# Valid order state transitions
VALID_TRANSITIONS: Dict[OrderStatus, set] = {
    OrderStatus.RECEIVED:   {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING:  {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY:      {OrderStatus.SERVED},
    OrderStatus.SERVED:     {OrderStatus.PAID},
    OrderStatus.PAID:       set(),
    OrderStatus.CANCELLED:  set(),
}

# ============================================================================
# CORE ENTITIES
# ============================================================================

class Table:
    """Physical seating unit."""
    def __init__(self, table_id: str, capacity: int, location: str = "main"):
        self.table_id = table_id
        self.capacity = capacity
        self.location = location
        self.status = TableStatus.FREE

    def is_free(self) -> bool:
        return self.status == TableStatus.FREE

    def reserve(self):
        if not self.is_free():
            raise ValueError(f"Table {self.table_id} is not FREE")
        self.status = TableStatus.RESERVED

    def check_in(self):
        if self.status != TableStatus.RESERVED:
            raise ValueError(f"Table {self.table_id} is not RESERVED")
        self.status = TableStatus.OCCUPIED

    def release(self):
        self.status = TableStatus.FREE

    def __repr__(self):
        return f"Table({self.table_id}, cap={self.capacity}, {self.status.value})"


class MenuItem:
    """A single item on the restaurant menu."""
    def __init__(self, item_id: str, name: str, price: float, category: str = "Main"):
        self.item_id = item_id
        self.name = name
        self.price = price
        self.category = category
        self.available = True

    def is_available(self) -> bool:
        return self.available

    def __repr__(self):
        return f"MenuItem({self.name}, ${self.price:.2f})"


class Reservation:
    """A customer's time-slot hold on a table."""
    def __init__(self, reservation_id: str, customer_name: str,
                 customer_email: str, table: Table,
                 party_size: int, reserved_at: datetime):
        self.reservation_id = reservation_id
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.table = table
        self.party_size = party_size
        self.reserved_at = reserved_at
        self.status = ReservationStatus.PENDING

    def check_in(self):
        """Activate reservation and seat guests."""
        if self.status != ReservationStatus.PENDING:
            raise ValueError(f"Reservation {self.reservation_id} cannot be checked in "
                             f"(status: {self.status.value})")
        self.status = ReservationStatus.CHECKED_IN
        self.table.check_in()

    def cancel(self):
        """Cancel reservation and release table."""
        if self.status in (ReservationStatus.CHECKED_IN, ReservationStatus.CANCELLED,
                           ReservationStatus.NO_SHOW):
            raise ValueError(f"Cannot cancel reservation in state {self.status.value}")
        self.status = ReservationStatus.CANCELLED
        self.table.release()

    def is_no_show(self, timeout_minutes: int = 15) -> bool:
        """Return True if guest has not checked in within the timeout window."""
        return (self.status == ReservationStatus.PENDING and
                datetime.now() > self.reserved_at + timedelta(minutes=timeout_minutes))

    def __repr__(self):
        return f"Reservation({self.reservation_id}, {self.customer_name}, {self.status.value})"


class Order:
    """Customer food order linked to a table."""
    def __init__(self, order_id: str, table: Table):
        self.order_id = order_id
        self.table = table
        self.items: List[Tuple[MenuItem, int]] = []   # (item, qty) pairs
        self.status = OrderStatus.RECEIVED
        self.created_at = datetime.now()

    def add_item(self, item: MenuItem, qty: int = 1):
        if self.status != OrderStatus.RECEIVED:
            raise ValueError(f"Cannot modify order in state {self.status.value}")
        if not item.is_available():
            raise ValueError(f"{item.name} is not available")
        self.items.append((item, qty))

    def get_subtotal(self) -> float:
        return sum(item.price * qty for item, qty in self.items)

    def advance_to(self, new_status: OrderStatus):
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid transition: {self.status.value} → {new_status.value}")
        self.status = new_status

    def __repr__(self):
        return f"Order({self.order_id}, table={self.table.table_id}, {self.status.value})"


class Bill:
    """Financial summary for a served order."""
    def __init__(self, bill_id: str, order: Order, subtotal: float,
                 discounted_amount: float, tax: float,
                 service_charge: float, total: float):
        self.bill_id = bill_id
        self.order = order
        self.subtotal = subtotal
        self.discounted_amount = discounted_amount
        self.tax = tax
        self.service_charge = service_charge
        self.total = total
        self.paid = False

    def mark_paid(self):
        if self.paid:
            raise ValueError(f"Bill {self.bill_id} already paid")
        self.paid = True

    def __repr__(self):
        return (f"Bill({self.bill_id}, subtotal=${self.subtotal:.2f}, "
                f"total=${self.total:.2f}, paid={self.paid})")


class Staff:
    """Restaurant employee (data holder for audit trails)."""
    def __init__(self, staff_id: str, name: str, role: str):
        self.staff_id = staff_id
        self.name = name
        self.role = role

    def __repr__(self):
        return f"Staff({self.name}, {self.role})"

# ============================================================================
# PRICING STRATEGIES
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float) -> float:
        pass

class RegularPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal

class HappyHourPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.80   # 20% off

class MemberPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.85   # 15% off

# ============================================================================
# OBSERVER PATTERN
# ============================================================================

class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {event:30s} | {payload}")

class KitchenObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        if event in ("ORDER_PLACED", "ORDER_STATUS_UPDATED"):
            print(f"  [KITCHEN] {event} | order={payload.get('order_id')} "
                  f"status={payload.get('status', 'new')}")

class EmailObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        if event in ("RESERVATION_CREATED", "PAYMENT_COMPLETED"):
            email = payload.get("customer_email", "")
            print(f"  [EMAIL -> {email}] Event: {event}")

# ============================================================================
# ORDER FACTORY
# ============================================================================

class OrderFactory:
    _counter = 0
    _lock = threading.Lock()

    @staticmethod
    def create(table: Table) -> Order:
        with OrderFactory._lock:
            OrderFactory._counter += 1
            order_id = f"ORD{OrderFactory._counter:04d}"
        return Order(order_id, table)

# ============================================================================
# RESTAURANT SYSTEM (SINGLETON)
# ============================================================================

class RestaurantSystem:
    """Singleton: Central coordinator for all restaurant operations."""
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Fix: accept *args/**kwargs so __init__ args don't raise TypeError
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.tables: Dict[str, Table] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.menu: Dict[str, MenuItem] = {}
        self.orders: Dict[str, Order] = {}
        self.bills: Dict[str, Bill] = {}
        self.pricing_strategy: PricingStrategy = RegularPricing()
        self.observers: List[RestaurantObserver] = []
        # RLock: prevents deadlock if internal methods call each other
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "RestaurantSystem":
        return cls()

    # --- Setup helpers ---

    def add_table(self, table: Table):
        with self._lock:
            self.tables[table.table_id] = table

    def add_menu_item(self, item: MenuItem):
        with self._lock:
            self.menu[item.item_id] = item

    def set_pricing_strategy(self, strategy: PricingStrategy):
        with self._lock:
            self.pricing_strategy = strategy

    def add_observer(self, observer: RestaurantObserver):
        with self._lock:
            self.observers.append(observer)

    def notify_observers(self, event: str, payload: Dict):
        with self._lock:
            obs_copy = list(self.observers)
        for obs in obs_copy:
            obs.update(event, payload)

    # --- Core operations ---

    def reserve_table(self, customer_name: str, customer_email: str,
                      party_size: int,
                      reserved_at: Optional[datetime] = None) -> Optional[Reservation]:
        """Find a free table and create a reservation."""
        if reserved_at is None:
            reserved_at = datetime.now()
        with self._lock:
            chosen = None
            for table in sorted(self.tables.values(), key=lambda t: t.capacity):
                if table.is_free() and table.capacity >= party_size:
                    chosen = table
                    break
            if chosen is None:
                print(f"  [WARN] No table available for party of {party_size}")
                return None
            chosen.reserve()
            res_id = f"RES{str(uuid.uuid4())[:8].upper()}"
            reservation = Reservation(res_id, customer_name, customer_email,
                                      chosen, party_size, reserved_at)
            self.reservations[res_id] = reservation
        self.notify_observers("RESERVATION_CREATED", {
            "reservation_id": res_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "table_id": chosen.table_id,
        })
        return reservation

    def check_in(self, reservation_id: str) -> bool:
        """Check in a pending reservation."""
        with self._lock:
            reservation = self.reservations.get(reservation_id)
            if not reservation:
                print(f"  [ERROR] Reservation {reservation_id} not found")
                return False
            try:
                reservation.check_in()
            except ValueError as e:
                print(f"  [ERROR] Check-in failed: {e}")
                return False
        self.notify_observers("GUEST_CHECKED_IN", {
            "reservation_id": reservation_id,
            "table_id": reservation.table.table_id,
        })
        return True

    def place_order(self, table_id: str,
                    items: List[Tuple[str, int]]) -> Optional[Order]:
        """Place an order for an occupied table."""
        with self._lock:
            table = self.tables.get(table_id)
            if not table or table.status != TableStatus.OCCUPIED:
                print(f"  [ERROR] Table {table_id} is not OCCUPIED")
                return None
            order = OrderFactory.create(table)
            for item_id, qty in items:
                menu_item = self.menu.get(item_id)
                if not menu_item:
                    print(f"  [ERROR] Menu item {item_id} not found")
                    return None
                if not menu_item.is_available():
                    print(f"  [ERROR] {menu_item.name} is not available")
                    return None
                order.add_item(menu_item, qty)
            self.orders[order.order_id] = order
        self.notify_observers("ORDER_PLACED", {
            "order_id": order.order_id,
            "table_id": table_id,
            "subtotal": order.get_subtotal(),
            "status": order.status.value,
        })
        return order

    def update_order_status(self, order_id: str, new_status: OrderStatus) -> bool:
        """Advance an order to the next valid state."""
        with self._lock:
            order = self.orders.get(order_id)
            if not order:
                print(f"  [ERROR] Order {order_id} not found")
                return False
            try:
                order.advance_to(new_status)
            except ValueError as e:
                print(f"  [ERROR] Status update failed: {e}")
                return False
        self.notify_observers("ORDER_STATUS_UPDATED", {
            "order_id": order_id,
            "status": new_status.value,
        })
        return True

    def calculate_bill(self, order_id: str) -> Optional[Bill]:
        """Generate a bill for a served order."""
        with self._lock:
            order = self.orders.get(order_id)
            if not order:
                print(f"  [ERROR] Order {order_id} not found")
                return None
            if order.status != OrderStatus.SERVED:
                print(f"  [ERROR] Order must be SERVED to bill (current: {order.status.value})")
                return None
            subtotal = order.get_subtotal()
            discounted = self.pricing_strategy.apply(subtotal)
            tax = discounted * 0.10
            service = discounted * 0.05
            total = discounted + tax + service
            bill_id = f"BILL{str(uuid.uuid4())[:8].upper()}"
            bill = Bill(bill_id, order, subtotal, discounted, tax, service, total)
            self.bills[bill_id] = bill
        self.notify_observers("BILL_GENERATED", {
            "bill_id": bill_id,
            "order_id": order_id,
            "subtotal": round(subtotal, 2),
            "total": round(total, 2),
        })
        return bill

    def process_payment(self, bill_id: str,
                        method: PaymentMethod = PaymentMethod.CARD) -> bool:
        """Mark bill paid and release the table."""
        with self._lock:
            bill = self.bills.get(bill_id)
            if not bill:
                print(f"  [ERROR] Bill {bill_id} not found")
                return False
            if bill.paid:
                print(f"  [ERROR] Bill {bill_id} already paid")
                return False
            bill.mark_paid()
            bill.order.advance_to(OrderStatus.PAID)
            table = bill.order.table
            customer_email = ""
            for res in self.reservations.values():
                if res.table.table_id == table.table_id:
                    customer_email = res.customer_email
                    break
            table.release()
        self.notify_observers("PAYMENT_COMPLETED", {
            "bill_id": bill_id,
            "order_id": bill.order.order_id,
            "total": round(bill.total, 2),
            "method": method.value,
            "customer_email": customer_email,
            "table_id": table.table_id,
        })
        return True

    def expire_no_shows(self, timeout_minutes: int = 15) -> int:
        """Background job: release tables for no-show reservations."""
        expired = []
        with self._lock:
            for res in self.reservations.values():
                if res.is_no_show(timeout_minutes):
                    res.status = ReservationStatus.NO_SHOW
                    res.table.release()
                    expired.append(res)
        for res in expired:
            self.notify_observers("NO_SHOW_EXPIRED", {
                "reservation_id": res.reservation_id,
                "customer_name": res.customer_name,
                "table_id": res.table.table_id,
            })
        return len(expired)

# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("RESTAURANT MANAGEMENT SYSTEM — DEMO")
    print("=" * 65)

    # Fresh instance (reset for demo)
    system = RestaurantSystem.get_instance()
    system.tables.clear()
    system.reservations.clear()
    system.menu.clear()
    system.orders.clear()
    system.bills.clear()
    system.observers.clear()
    system._initialized = True   # keep flag set

    # --- Observers ---
    system.add_observer(ConsoleObserver())
    system.add_observer(KitchenObserver())
    system.add_observer(EmailObserver())

    # --- Tables ---
    for i in range(1, 6):
        system.add_table(Table(f"T{i}", capacity=4))
    system.add_table(Table("T6", capacity=8, location="banquet"))
    print(f"\nSetup: {len(system.tables)} tables added")

    # --- Menu ---
    menu_data = [
        ("M001", "Caesar Salad",    8.50,  "Starter"),
        ("M002", "Tomato Soup",     6.00,  "Starter"),
        ("M003", "Grilled Salmon",  22.00, "Main"),
        ("M004", "Ribeye Steak",    35.00, "Main"),
        ("M005", "Chocolate Cake",  7.50,  "Dessert"),
        ("M006", "House Wine",      9.00,  "Drink"),
    ]
    for mid, name, price, cat in menu_data:
        system.add_menu_item(MenuItem(mid, name, price, cat))
    print(f"Setup: {len(system.menu)} menu items added\n")

    # ----------------------------------------------------------------
    # DEMO 1: Reserve, Check-in, Order, Kitchen, Bill, Pay
    # ----------------------------------------------------------------
    print("=" * 65)
    print("DEMO 1: Full Dining Flow — Reserve → Pay")
    print("=" * 65)

    res = system.reserve_table("Alice Wong", "alice@example.com", 2)
    print(f"\n[1] Reserved: {res}")

    system.check_in(res.reservation_id)
    print(f"[2] Checked in: table status = {res.table.status.value}")

    order = system.place_order(res.table.table_id,
                               [("M001", 2), ("M003", 1), ("M006", 2)])
    print(f"\n[3] Order placed: {order}")
    print(f"    Subtotal: ${order.get_subtotal():.2f}")

    for status in [OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.SERVED]:
        system.update_order_status(order.order_id, status)
    print(f"\n[4] Order status: {order.status.value}")

    bill = system.calculate_bill(order.order_id)
    print(f"\n[5] Bill breakdown:")
    print(f"    Subtotal:         ${bill.subtotal:.2f}")
    print(f"    After discount:   ${bill.discounted_amount:.2f}")
    print(f"    Tax (10%):        ${bill.tax:.2f}")
    print(f"    Service (5%):     ${bill.service_charge:.2f}")
    print(f"    TOTAL:            ${bill.total:.2f}")

    system.process_payment(bill.bill_id, PaymentMethod.CARD)
    print(f"\n[6] Table status after payment: {res.table.status.value}")

    # ----------------------------------------------------------------
    # DEMO 2: Happy Hour Pricing
    # ----------------------------------------------------------------
    print("\n" + "=" * 65)
    print("DEMO 2: Happy Hour Pricing (20% off)")
    print("=" * 65)

    system.set_pricing_strategy(HappyHourPricing())

    res2 = system.reserve_table("Bob Chen", "bob@example.com", 3)
    system.check_in(res2.reservation_id)
    order2 = system.place_order(res2.table.table_id, [("M004", 2), ("M005", 2)])
    for s in [OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.SERVED]:
        system.update_order_status(order2.order_id, s)

    bill2 = system.calculate_bill(order2.order_id)
    print(f"\n  Subtotal:       ${bill2.subtotal:.2f}")
    print(f"  HappyHour (20% off): ${bill2.discounted_amount:.2f}")
    print(f"  TOTAL:          ${bill2.total:.2f}")
    system.process_payment(bill2.bill_id, PaymentMethod.CASH)

    # ----------------------------------------------------------------
    # DEMO 3: Walk-in (no reservation) — direct check for OCCUPIED
    # ----------------------------------------------------------------
    print("\n" + "=" * 65)
    print("DEMO 3: Attempting order on non-occupied table (error guard)")
    print("=" * 65)

    bad_order = system.place_order("T4", [("M002", 1)])
    print(f"  Result: {'blocked (expected)' if bad_order is None else 'unexpected success'}")

    # ----------------------------------------------------------------
    # DEMO 4: Member Pricing
    # ----------------------------------------------------------------
    print("\n" + "=" * 65)
    print("DEMO 4: Member Pricing (15% off)")
    print("=" * 65)

    system.set_pricing_strategy(MemberPricing())

    res4 = system.reserve_table("Carol Li", "carol@example.com", 2)
    system.check_in(res4.reservation_id)
    order4 = system.place_order(res4.table.table_id, [("M003", 1), ("M005", 1), ("M006", 1)])
    for s in [OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.SERVED]:
        system.update_order_status(order4.order_id, s)

    bill4 = system.calculate_bill(order4.order_id)
    print(f"\n  Subtotal:       ${bill4.subtotal:.2f}")
    print(f"  Member (15% off): ${bill4.discounted_amount:.2f}")
    print(f"  TOTAL:          ${bill4.total:.2f}")
    system.process_payment(bill4.bill_id, PaymentMethod.DIGITAL)

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    free_tables = sum(1 for t in system.tables.values() if t.is_free())
    print(f"\n{'=' * 65}")
    print(f"Demo complete. Free tables: {free_tables}/{len(system.tables)}")
    print(f"Total orders processed: {len(system.orders)}")
    print(f"Total bills paid: {sum(1 for b in system.bills.values() if b.paid)}")
    print("=" * 65)
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **reserve_table** | RLock on system | Atomic table scan + reserve (no double-booking) |
| **check_in** | RLock on system | Atomic status check + transition |
| **place_order** | RLock on system | Atomic table check + order creation |
| **update_order_status** | RLock on system | Atomic transition validation + state change |
| **calculate_bill** | RLock on system | Atomic pricing + bill creation |
| **process_payment** | RLock on system | Atomic pay + table release (no double-pay) |
| **Singleton init** | Class-level Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ RLock (re-entrant) used instead of Lock — prevents deadlock if internal methods call each other
2. ✅ Singleton `__new__` accepts `*args, **kwargs` — avoids TypeError when `__init__` is called with args
3. ✅ Observers notified outside the lock — keeps critical sections short
4. ✅ Observer list copied before iteration — safe even if observers modify the list

---

## Demo Scenarios

**Demo 1**: Reservation & check-in — guest reserves T1, checks in, places order (Caesar Salad ×2, Grilled Salmon ×1, Wine ×2), kitchen progresses through PREPARING → READY → SERVED, bill generated at regular pricing, paid by card, table released.

**Demo 2**: Happy Hour Pricing — 20% discount applied to Ribeye Steak ×2 + Chocolate Cake ×2 before tax and service charge are added.

**Demo 3**: Error guard — attempting `place_order` on a FREE (non-OCCUPIED) table is correctly blocked with a clear error message.

**Demo 4**: Member Pricing — 15% discount for loyalty members, paid by digital wallet.

**Demo 5** (configurable): No-show expiry — call `system.expire_no_shows(timeout_minutes=0)` to simulate a guest who never checked in; reservation becomes NO_SHOW and table reverts to FREE.

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking of a table?**

A: Atomic status transition protected by a re-entrant lock:

```python
with self._lock:                        # Only one thread enters
    if table.is_free():                 # Check
        table.reserve()                 # Modify (atomic together)
        reservation = Reservation(...)  # Create under lock
```

Any concurrent thread that reaches the check after the first thread reserved the table sees `TableStatus.RESERVED` and is blocked.

**Q2: What is the difference between a Reservation and an Order?**

A: A Reservation is a time-slot hold on a table (created before arrival, expires on no-show). An Order is the actual food request created after the guest has checked in and the table is OCCUPIED.

**Q3: How does the Order state machine work?**

A: `RECEIVED → PREPARING → READY → SERVED → PAID` with `CANCELLED` reachable from RECEIVED or PREPARING. Invalid transitions (e.g., SERVED → PREPARING) raise `ValueError` via the `VALID_TRANSITIONS` map.

**Q4: Why use Strategy pattern for pricing?**

A: Different rules (Regular, HappyHour, Member) are swapped at runtime without touching bill calculation logic. Adding a new rule (e.g., GroupDiscount) requires only a new class — no changes to `calculate_bill()`.

**Q5: How do you handle a no-show reservation?**

A: A background job calls `expire_no_shows()` every 5 minutes. If `datetime.now() > reserved_at + timeout`, the reservation is marked NO_SHOW and the table released to FREE.

---

### Intermediate Questions

**Q6: How do you coordinate the kitchen without coupling it to the Order class?**

A: The Observer pattern. A `KitchenObserver` subscribes to `ORDER_PLACED` and `ORDER_STATUS_UPDATED` events. When `place_order()` finishes, `notify_observers()` broadcasts the event — the kitchen receives it without the Order class knowing anything about kitchen logic.

**Q7: Can an order be modified after placement?**

A: Only while in RECEIVED state. Once the kitchen marks it PREPARING, `add_item()` raises a `ValueError`. This mirrors real restaurant policy and prevents race conditions between the waiter and kitchen.

**Q8: How is the bill formula structured?**

A: `subtotal → strategy.apply(subtotal) = discounted_amount → + tax (10%) → + service (5%) → total`. The pricing strategy acts only on the subtotal; tax and service are applied after discount.

**Q9: What metrics would you track?**

A: Table utilisation rate, average order value, reservation conversion rate (PENDING → CHECKED_IN), no-show rate, average kitchen turnaround time (RECEIVED → READY), payment success rate.

**Q10: How do you handle payment failure?**

A: Retry up to 3 times with exponential backoff (mock). On final failure, set bill status to FAILED, notify the customer, and keep the table OCCUPIED so they can retry.

---

### Advanced Questions

**Q11: How would you add the Command pattern for undo support?**

A: Wrap `place_order` and `process_payment` in Command objects that store enough state to reverse the action. `PlaceOrderCommand.undo()` would call `update_order_status(CANCELLED)`. Store a command history stack in the system.

**Q12: How would you prevent concurrent billing for the same order?**

A: The `calculate_bill` and `process_payment` operations are both guarded by the same RLock. Additionally, `process_payment` checks `bill.paid` before proceeding and raises `BillAlreadyPaidError` if already settled — the check-and-set is atomic within the lock.

---

## Scaling Q&A

### Q1: Scale to 1000+ tables across 100 restaurants?

**A**: Each restaurant runs its own `RestaurantSystem` instance (independent operation). A shared analytics database aggregates metrics. Use a message broker (Kafka) for cross-restaurant events (e.g., chef sharing).

### Q2: Handle 1000 orders/hour peak?

**A**: Queue orders if kitchen lag > 500ms. Use async kitchen tickets via Kafka topics with multiple partition workers (one per prep station). Cache menu prices in memory — they rarely change.

### Q3: Prevent table overbooking across replicas?

**A**: Use a distributed lock (Redis `SET NX EX`) for atomic reservation globally:
```
LOCK key=table:T1 value=USER_A NX EX=10s
→ check table is FREE in DB
→ write RESERVED to DB
→ release lock
```

### Q4: Payment concurrency across distributed nodes?

**A**: Optimistic locking with version numbers on the Bill row. Each payment attempt reads the version, attempts `UPDATE ... WHERE version = N AND paid = FALSE`, and retries on version mismatch.

### Q5: Scale kitchen operations?

**A**: Kafka topic `kitchen-tickets` with partitions by prep station type (grill, cold, dessert). Each station consumes its partition in parallel. Kitchen display systems subscribe to their own consumer group.

### Q6: Ensure 99.9% uptime?

**A**: Multi-replica deployment behind a load balancer, health checks every 30s, RTO < 30s failover, RPO < 5 min (async replication). Reservations and orders persisted to a durable store (PostgreSQL + WAL).

### Q7: Test at scale?

**A**: Load test with 1000 concurrent virtual customers using k6 or Locust. Monitor latency p99, reservation error rate, database connection pool saturation, and Kafka consumer lag.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships and cardinality
- [ ] Walk through full flow: reserve → check-in → order → kitchen → bill → pay → table free
- [ ] Explain double-booking prevention with atomic lock + status transition
- [ ] Explain order state machine and invalid transition guards
- [ ] Discuss bill formula: subtotal → strategy discount → + tax + service
- [ ] Explain how Observer decouples kitchen coordination from order logic
- [ ] Run complete implementation (4 demos) without errors
- [ ] Answer 5+ scaling Q&A questions confidently
- [ ] Mention thread safety: RLock for re-entrancy, Singleton `__new__` accepting `*args/**kwargs`
- [ ] Discuss trade-offs: in-memory vs DB, pessimistic vs optimistic locking for distributed setup

---

**Ready for your interview? Take the order and fire the ticket!**
