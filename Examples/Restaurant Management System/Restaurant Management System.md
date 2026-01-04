# Restaurant Management System — 75-Minute Interview Guide

## Quick Start Overview

## Interview 75-Minute Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0-10 min | Requirements, scope | Confirm reservations, orders, billing, notifications |
| 10-30 min | Core classes | Implement MenuItem, Table, Customer, Reservation, Order |
| 30-50 min | Patterns & logic | Strategy (pricing), State (order), Observer (events), Factory, Command |
| 50-70 min | Integration & demos | End-to-end reservation → order → kitchen → payment |
| 70-75 min | Q&A | Scaling, extensions, trade-offs |

## Essential Entities & Responsibilities
| Entity | Responsibility | Key Methods |
|--------|---------------|-------------|
| `MenuItem` | Menu catalog entry | `get_price(strategy)` |
| `Table` | Seating unit & status | `reserve()`, `occupy()`, `release()` |
| `Reservation` | Holds table for customer | `confirm()`, `cancel()` |
| `Order` | Items + lifecycle + billing | `add_item()`, `update_status()`, `calculate_totals()` |
| `KitchenTicket` | Tracks preparation progress | `start()`, `complete()` |
| `Payment` | Finalizes bill | `process()` |

## Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns Cheat Sheet
### Singleton
```python
class RestaurantSystem:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
```
Use for a single orchestrator managing tables, orders, reservations.

### Strategy (Pricing)
```python
class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float, context: dict) -> float: ...

class HappyHourPricingStrategy(PricingStrategy):
    def apply(self, subtotal, context):
        return subtotal * 0.8  # 20% discount on applicable items
```
Swap pricing rules without altering order code.

### Observer (Events)
```python
class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): ...

class ConsoleObserver(RestaurantObserver):
    def update(self, event, payload):
        print(f"[EVENT] {event}: {payload}")
```
Loose coupling between domain events and notification channels.

### State (Order Lifecycle)
```python
class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"
```
Validate transitions to prevent illegal states.

### Factory
```python
class OrderFactory:
    _counter = 0
    @staticmethod
    def create(table, items):
        OrderFactory._counter += 1
        return Order(f"ORD{OrderFactory._counter:04d}", table, items)
```
Central ID generation + validation.

### Command
```python
class PlaceOrderCommand:
    def __init__(self, system, table, items):
        self.system = system; self.table = table; self.items = items
    def execute(self):
        return self.system.place_order(self.table, self.items)
```
Encapsulate high-level operations; enables logging, undo discussion.

## Bill Calculation Flow
```
subtotal = Σ(menu_item.base_price × quantity)
adjusted = pricing_strategy.apply(subtotal, context)
service_charge? discount? → final bill_total
```

## Demo Script Outline (Implemented in INTERVIEW_COMPACT.py)
1. Setup & seed menu, tables
2. Create reservation & confirm
3. Place order (multiple items)
4. Kitchen ticket start & complete
5. Order served & billed with strategy
6. Payment processed & table released

## Talking Points
- "I applied Strategy for pricing so adding Happy Hour is a single class."  
- "Observer decouples notifications: swap ConsoleObserver for EmailObserver easily."  
- "State prevents serving an order that's never prepared."  
- "Factory handles consistent ID generation reducing scattered logic."  
- "Command objects wrap operations enabling audit trails later."  

## Common Edge Cases
| Edge Case | Handling |
|-----------|----------|
| Double reservation same table/time | Check `table.status` before create |
| Order item unavailable | Validate availability before adding |
| Illegal status transition (READY → PREPARING) | Guard in `update_status()` |
| Payment before SERVED | Enforce status check |
| Empty order | Block creation (raise / return False) |

## Formulas
- Subtotal: `Σ(item_price × qty)`  
- Discounted: `subtotal × (1 - discount_rate)`  
- Service Charge: `subtotal × service_rate`  
- Final Bill: `discounted + service_charge`  

## Quick Commands
```bash
python3 INTERVIEW_COMPACT.py       # Run demos
grep -n 'OrderStatus' INTERVIEW_COMPACT.py  # Inspect state enum
```

## Success Checklist Before Time Ends
- [ ] Reservation demo works
- [ ] Order lifecycle moves through statuses
- [ ] Pricing strategy applied
- [ ] Payment recorded
- [ ] Console events visible

## If Running Behind
| Time Left | Action |
|-----------|--------|
| 25 min | Skip inventory & composite pricing, finish order lifecycle |
| 10 min | Hardcode pricing, show single order path |
| 5 min | Verbally describe missed patterns, run minimal demo |

## Stretch Extensions (If time remains)
- Add `EmailObserver`
- Add `CompositePricingStrategy`
- Add partial order cancellation logic
- Add inventory consumption per item

---
Run it now: `python3 INTERVIEW_COMPACT.py`


## 75-Minute Guide

## 0–10 min: Requirements Clarification
Clarify scope quickly:
- Must Have: Reservations, Table status, Order lifecycle, Kitchen prep, Billing + Pricing strategies, Payment, Notifications.
- Nice to Have (mention only if time): Inventory, Composite pricing, Multi-branch support, Analytics.
- Out of Scope (but discussable): Online delivery, Loyalty points, POS hardware integration.

Confirm assumptions:
- Single restaurant location.
- Walk‑in and reservation both allowed.
- Payment after serving only.
- Happy hour discount applies to DRINK category.
- Service charge applied to entire subtotal (dine‑in only).

Scope Agreement:
- ✅ Reservation lifecycle (PENDING → CONFIRMED → CANCELLED)
- ✅ Order lifecycle (RECEIVED → PREPARING → READY → SERVED)
- ✅ Pricing strategies (discount + service charge + composite)
- ✅ Notification events (reservation, order, kitchen, payment)
- ✅ Table status transitions
- ✅ Command/Factory usage
- ❌ Delivery routing, kitchen staff scheduling, loyalty, inventory depletion (can explain extensions)

---
## 10–25 min: Core Entities Skeleton
```python
class TableStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"

class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

class Table:
    def __init__(self, table_id: str, capacity: int):
        self.table_id = table_id
        self.capacity = capacity
        self.status = TableStatus.AVAILABLE
    def reserve(self): ...
    def occupy(self): ...
    def release(self): ...

class MenuItem:
    def __init__(self, item_id, name, category, base_price, is_available=True): ...

class OrderItem:
    def __init__(self, menu_item, quantity): ...

class Order:
    def __init__(self, order_id, table):
        self.items = []
        self.status = OrderStatus.RECEIVED
    def add_item(self, order_item): ...
    def update_status(self, new_status): ...
```
Focus on: correctness > completeness. Add attributes incrementally.

---
## 25–45 min: Patterns & Business Logic
### Pricing (Strategy Pattern)
```python
class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float, context: dict) -> float: ...

class BasePricingStrategy(PricingStrategy):
    def apply(self, subtotal, context): return round(subtotal, 2)

class HappyHourPricingStrategy(PricingStrategy):
    def __init__(self, pct=0.20, start=16, end=18): ...
    def apply(self, subtotal, context):
        hour = context['hour']
        drink_sub = sum(i.line_subtotal() for i in context['items'] if i.menu_item.category == Category.DRINK)
        return round(subtotal - (drink_sub * self.pct) if start <= hour < end else subtotal, 2)
```
### State Validation (Order)
```python
valid_transitions = {
  OrderStatus.RECEIVED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
  OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
  OrderStatus.READY: [OrderStatus.SERVED],
  OrderStatus.SERVED: [],
  OrderStatus.CANCELLED: []
}
```
### Observer Pattern
```python
class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): ...

class ConsoleObserver(RestaurantObserver):
    def update(self, event, payload):
        print(f"[EVENT] {event}: {payload}")
```
### Factory Pattern
```python
class OrderFactory:
    _counter = 0
    @staticmethod
    def create(table: Table) -> Order:
        OrderFactory._counter += 1
        return Order(f"ORD{OrderFactory._counter:05d}", table)
```
### Command Pattern
```python
class PlaceOrderCommand(Command):
    def execute(self): return system.place_order(self.table, self.items)
```
---
## 45–60 min: System Integration (Singleton)
```python
class RestaurantSystem:
    _instance = None
    def __new__(cls):
        if not cls._instance: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if hasattr(self, 'initialized'): return
        self.tables = {}
        self.menu = {}
        self.reservations = {}
        self.orders = {}
        self.observers = []
        self.initialized = True

    def notify(self, event, payload):
        for obs in self.observers: obs.update(event, payload)
```
Add flows: reservation creation, order placement, kitchen ticket creation, payment processing.

---
## 60–70 min: Demo Scenarios Implementation
| Demo | Purpose |
|------|---------|
| 1. Setup | Seed tables & menu, attach observer |
| 2. Reservation | Create & confirm reservation, occupy table |
| 3. Order Lifecycle | Through all states to SERVED |
| 4. Pricing & Payment | Composite strategy (discount + service) |
| 5. Full Flow | End-to-end plus table release |

Pseudo-run:
```python
system = RestaurantSystem.get_instance()
customer = Customer("C001", "Alice", "alice@example.com")
table = system.get_available_table(4)
reservation = system.create_reservation(customer, table, datetime.now())
reservation.confirm(); table.occupy()
order = system.place_order(table, [("ITEM002", 2), ("ITEM005", 3)])
ticket = system.create_kitchen_ticket(order); ticket.start(); ticket.complete()
order.update_status(OrderStatus.SERVED)
payment = system.process_payment(order, PaymentMethod.CARD, CompositePricingStrategy([...]))
```
Show printed events to interviewer.

---
## 70–75 min: Q&A (Prepared Answers)
### Q1: Why use Strategy for pricing?
Different pricing rules (happy hour, service charge, loyalty discounts) can be added without modifying order core—each rule is isolated.

### Q2: How do you enforce valid order state transitions?
Central `valid_transitions` map; `update_status()` checks membership before applying state change. Prevents illegal regressions (READY → PREPARING).

### Q3: How would you scale this system for multiple branches?
Add `branch_id` to entities; partition data by branch; deploy per-branch kitchen service; shared auth & payment gateway; event bus (Kafka) for analytics.

### Q4: How do you guarantee atomic billing + payment?
Wrap compute + persist in a transaction (in production). Here simulated; would use DB transaction (BEGIN → compute final total → insert payment row → COMMIT). Rollback on failure.

### Q5: How to handle inventory deduction?
Introduce `InventoryItem` and deduct quantities when order enters PREPARING state; restore on cancellation (compensating action) before READY.

### Q6: How to extend notifications to real-time dashboards?
Replace `ConsoleObserver` with WebSocket observer broadcasting JSON payloads; observers remain decoupled.

### Q7: What if Happy Hour overlaps service charge—order of operations?
Composite strategy applies sequentially: discount first (reduce base), then service charge (percentage on discounted total). Deterministic layering.

### Q8: Prevent double reservation of same table/time?
Check `table.status == AVAILABLE` before creating reservation; could also maintain time slots; add conflict detection by comparing requested time window.

### Q9: Handling partial order cancellation?
Introduce per-item flags and recompute subtotal; if all items cancelled → order status CANCELLED; adjust billing before payment.

### Q10: Metrics to track?
Throughput: orders/hour; Avg prep time; Table turnover; Discount utilization; Service charge revenue; Order state dwell times; Payment success rate.

---
## UML Overview
```
┌────────────────────────────────┐
│        RestaurantSystem        │ (Singleton)
├────────────────────────────────┤
│ tables: Dict[str, Table]       │
│ menu: Dict[str, MenuItem]      │
│ reservations: Dict[str, Reserv]│
│ orders: Dict[str, Order]       │
│ observers: List[Observer]      │
├────────────────────────────────┤
│ +create_reservation()          │
│ +place_order()                 │
│ +create_kitchen_ticket()       │
│ +process_payment()             │
│ +notify(event,payload)         │
└────────────────────────────────┘
        │ manages
        ▼
┌────────────┐   ┌──────────────┐   ┌──────────────┐
│  Table     │   │ Reservation   │   │   Order       │
└────────────┘   └──────────────┘   └──────────────┘
                                   │ contains
                                   ▼
                               ┌───────────┐
                               │OrderItem  │
                               └───────────┘

PricingStrategy ◄───┐
    ▲               │ (implements)
    │               ├── BasePricingStrategy
    │               ├── HappyHourPricingStrategy
    │               └── ServiceChargePricingStrategy
CompositePricingStrategy (wraps multiple strategies)

Observer Interface → ConsoleObserver (example implementation)
Command → PlaceOrderCommand / CreateReservationCommand / ProcessPaymentCommand
```

---
## Key Interview Sound Bites
- "State map prevents invalid regressions—robust lifecycle control."  
- "Composite strategy lets me layer price transformations cleanly."  
- "Observer keeps presentation concerns out of domain logic."  
- "Factories unify ID generation; avoids scattered counters."  
- "Commands prepare for audit logging & undo semantics later."  

---
## Final Checklist
| Area | Verified |
|------|----------|
| Reservation flow | ✅ |
| Order lifecycle | ✅ |
| Pricing strategies | ✅ |
| Notifications | ✅ |
| Payment & bill | ✅ |
| Patterns explained | ✅ |
| Demo runs | ✅ |

---
Run demos now:
```bash
python3 INTERVIEW_COMPACT.py
```


## Detailed Design Reference

## Overview
A comprehensive system for managing restaurant operations: table reservations, seating, menu catalog, order lifecycle from placement to kitchen preparation and serving, billing with dynamic pricing strategies (happy hour, service charge), payments, and real-time notifications for status changes. Designed for interview demonstration with clear patterns and extensibility.

## Core Domain Entities

### 1. **MenuItem**
- Attributes: `item_id`, `name`, `category` (STARTER / MAIN / DRINK / DESSERT), `base_price`, `is_available`
- Methods: `get_price(strategy)`, `mark_unavailable()`

### 2. **Table**
- Attributes: `table_id`, `capacity`, `status` (AVAILABLE / RESERVED / OCCUPIED)
- Methods: `reserve()`, `occupy()`, `release()`

### 3. **Customer**
- Attributes: `customer_id`, `name`, `contact`
- Methods: `create_reservation()`, `place_order()`

### 4. **Reservation**
- Attributes: `reservation_id`, `customer`, `table`, `time`, `status` (PENDING / CONFIRMED / CANCELLED)
- Methods: `confirm()`, `cancel()`

### 5. **OrderItem**
- Attributes: `menu_item`, `quantity`, `final_price`
- Methods: `calculate(strategy)`

### 6. **Order**
- Attributes: `order_id`, `table`, `items[]`, `status` (RECEIVED / PREPARING / READY / SERVED / CANCELLED), `subtotal`, `bill_total`
- Methods: `add_item()`, `update_status()`, `calculate_totals(strategy)`

### 7. **Payment**
- Attributes: `payment_id`, `order`, `amount`, `method` (CARD / CASH / WALLET), `timestamp`
- Methods: `process()`

### 8. **KitchenTicket**
- Attributes: `ticket_id`, `order`, `queued_at`, `started_at`, `completed_at`
- Methods: `start()`, `complete()`

### 9. **InventoryItem** (Optional Extension)
- Attributes: `sku`, `name`, `quantity`
- Methods: `consume(amount)`, `replenish(amount)`

## Design Patterns Applied

| Pattern | Why | Implementation |
|---------|-----|----------------|
| Singleton | Single system orchestrator | `RestaurantSystem.get_instance()` |
| Strategy | Flexible pricing/service rules | `PricingStrategy` subclasses (Base, HappyHour, ServiceCharge) |
| Observer | Decoupled notifications | `RestaurantObserver` + `ConsoleObserver` events (`reservation_created`, `order_status_changed`, `payment_processed`) |
| State | Order & Reservation lifecycle | `OrderStatus`, `ReservationStatus`, transitions enforced in methods |
| Factory | Clean creation of entities | `OrderFactory`, `ReservationFactory` generate IDs & validate inputs |
| Command | Encapsulated operations | `PlaceOrderCommand`, `UpdateOrderStatusCommand`, `ProcessPaymentCommand`, `CreateReservationCommand`, `CancelReservationCommand` |

## Core Flows

### Reservation Flow
```
Customer requests reservation → RestaurantSystem finds AVAILABLE table → Reservation created (PENDING) → confirm() → Table status RESERVED → Customer arrives → occupy() → status OCCUPIED
```

### Order Lifecycle
```
Order placed (RECEIVED) → KitchenTicket created → status PREPARING → cooking done → READY → waiter serves → SERVED → payment processed → table released
```

### Billing Flow with Strategy
```
order.subtotal = Σ(item.base_price × qty)
strategy adjustments: discount% or service fee → bill_total = strategy.apply(subtotal)
```

## Pricing Strategies (Strategy Pattern)

| Strategy | Rule | Example |
|----------|------|---------|
| BasePricingStrategy | No modification | Lunch standard pricing |
| HappyHourPricingStrategy | Percentage discount on certain categories | 20% off DRINK 4–6 PM |
| ServiceChargePricingStrategy | Add service charge percentage | 10% service fee on dine-in |
| Composite (Interview extension) | Combine discount + charge | Happy hour + service fee |

## Order States (State Pattern)
```
RECEIVED → PREPARING → READY → SERVED
              ↘ CANCELLED (allowed only before READY)
```

## Reservation States
```
PENDING → CONFIRMED → CANCELLED
```

## Success Criteria Checklist
- [x] Reservation & table status transitions
- [x] Order lifecycle with state validation
- [x] Strategy based billing (discount + service charge)
- [x] Observer notifications for key events
- [x] Command pattern for encapsulated actions
- [x] Factory based ID generation & validation
- [x] Demo scenarios runnable (`python3 INTERVIEW_COMPACT.py`)

## Sample Usage
```python
system = RestaurantSystem.get_instance()
customer = Customer("C001", "Alice", "alice@example.com")
table = system.get_available_table(capacity=4)
reservation = system.create_reservation(customer, table, datetime.now())
reservation.confirm()
order = system.place_order(table, [("ITEM001", 2), ("ITEM005", 1)])
order.calculate_totals(HappyHourPricingStrategy())
payment = system.process_payment(order, method="CARD")
```

## Scalability & Extensions
- Multiple branches: Branch identifier inside `RestaurantSystem`
- Distributed kitchen: Separate KitchenService microservice
- Realtime waiter tablets: WebSocket observer implementation
- Inventory deductions on order placement
- Analytics: event streaming (Kafka) for orders & payments

## Files
- `README.md` (this overview)
- `START_HERE.md` (rapid interview guide)
- `INTERVIEW_COMPACT.py` (full runnable implementation with demos)
- `75_MINUTE_GUIDE.md` (step-by-step deep dive + UML + Q&A)

---
**Next**: Open `START_HERE.md` for 5‑minute prep or run demos: `python3 INTERVIEW_COMPACT.py`.


## Compact Code

```python
"""
Restaurant Management System - Complete Interview Implementation
=====================================================================
Design Patterns: Singleton | Strategy | Observer | State | Factory | Command
Time Complexity: O(1) state transitions, O(n) billing where n = items
Space Complexity: O(t + m + r + o) tables + menu items + reservations + orders
=====================================================================
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import threading

# ============================================================================
# SECTION 1: ENUMERATIONS (STATE & TYPES)
# ============================================================================

class TableStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"

class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"

class Category(Enum):
    STARTER = "starter"
    MAIN = "main"
    DRINK = "drink"
    DESSERT = "dessert"

# ============================================================================
# SECTION 2: CORE DOMAIN CLASSES
# ============================================================================

class MenuItem:
    def __init__(self, item_id: str, name: str, category: Category, base_price: float, is_available: bool = True):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.base_price = base_price
        self.is_available = is_available
    
    def mark_unavailable(self):
        self.is_available = False
    
    def get_price(self) -> float:
        return self.base_price
    
    def __str__(self):
        return f"{self.name} (${self.base_price:.2f})"


class Table:
    def __init__(self, table_id: str, capacity: int):
        self.table_id = table_id
        self.capacity = capacity
        self.status = TableStatus.AVAILABLE
    
    def reserve(self) -> bool:
        if self.status != TableStatus.AVAILABLE:
            return False
        self.status = TableStatus.RESERVED
        return True
    
    def occupy(self) -> bool:
        if self.status not in [TableStatus.RESERVED, TableStatus.AVAILABLE]:
            return False
        self.status = TableStatus.OCCUPIED
        return True
    
    def release(self) -> bool:
        self.status = TableStatus.AVAILABLE
        return True
    
    def __str__(self):
        return f"Table {self.table_id} ({self.capacity} seats) - {self.status.value}"


class Customer:
    def __init__(self, customer_id: str, name: str, contact: str):
        self.customer_id = customer_id
        self.name = name
        self.contact = contact
    
    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class Reservation:
    def __init__(self, reservation_id: str, customer: Customer, table: Table, time: datetime):
        self.reservation_id = reservation_id
        self.customer = customer
        self.table = table
        self.time = time
        self.status = ReservationStatus.PENDING
        self.created_at = datetime.now()
    
    def confirm(self) -> bool:
        if self.status != ReservationStatus.PENDING:
            return False
        if not self.table.reserve():  # ensure table can be reserved
            return False
        self.status = ReservationStatus.CONFIRMED
        return True
    
    def cancel(self) -> bool:
        if self.status == ReservationStatus.CANCELLED:
            return False
        self.status = ReservationStatus.CANCELLED
        # release table if it was confirmed
        if self.table.status == TableStatus.RESERVED:
            self.table.release()
        return True
    
    def __str__(self):
        return f"Reservation {self.reservation_id} for Table {self.table.table_id} - {self.status.value}"


class OrderItem:
    def __init__(self, menu_item: MenuItem, quantity: int):
        self.menu_item = menu_item
        self.quantity = quantity
        self.final_price = 0.0  # filled during bill calculation
    
    def line_subtotal(self) -> float:
        return self.menu_item.base_price * self.quantity
    
    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity} (${self.line_subtotal():.2f})"


class Order:
    def __init__(self, order_id: str, table: Table):
        self.order_id = order_id
        self.table = table
        self.items: List[OrderItem] = []
        self.status = OrderStatus.RECEIVED
        self.subtotal = 0.0
        self.bill_total = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_item(self, order_item: OrderItem) -> bool:
        if self.status in [OrderStatus.READY, OrderStatus.SERVED, OrderStatus.CANCELLED]:
            return False
        if not order_item.menu_item.is_available:
            return False
        self.items.append(order_item)
        return True
    
    def update_status(self, new_status: OrderStatus) -> bool:
        valid_transitions = {
            OrderStatus.RECEIVED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.SERVED],
            OrderStatus.SERVED: [],
            OrderStatus.CANCELLED: []
        }
        if new_status in valid_transitions[self.status]:
            self.status = new_status
            self.updated_at = datetime.now()
            return True
        return False
    
    def calculate_totals(self, pricing_strategy: 'PricingStrategy'):
        self.subtotal = sum(item.line_subtotal() for item in self.items)
        context = {
            'items': self.items,
            'table_id': self.table.table_id,
            'hour': datetime.now().hour
        }
        self.bill_total = pricing_strategy.apply(self.subtotal, context)
        return self.bill_total
    
    def __str__(self):
        return f"Order {self.order_id} ({self.status.value}) - {len(self.items)} items"


class KitchenTicket:
    def __init__(self, ticket_id: str, order: Order):
        self.ticket_id = ticket_id
        self.order = order
        self.queued_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def start(self):
        if self.order.status == OrderStatus.RECEIVED:
            self.order.update_status(OrderStatus.PREPARING)
            self.started_at = datetime.now()
            return True
        return False
    
    def complete(self):
        if self.order.status == OrderStatus.PREPARING:
            self.order.update_status(OrderStatus.READY)
            self.completed_at = datetime.now()
            return True
        return False
    
    def __str__(self):
        return f"Ticket {self.ticket_id} for {self.order.order_id} - {self.order.status.value}"


class Payment:
    def __init__(self, payment_id: str, order: Order, amount: float, method: PaymentMethod):
        self.payment_id = payment_id
        self.order = order
        self.amount = amount
        self.method = method
        self.timestamp = datetime.now()
        self.success = False
    
    def process(self) -> bool:
        if self.order.status != OrderStatus.SERVED:
            return False
        # Simplified success
        self.success = True
        return True
    
    def __str__(self):
        return f"Payment {self.payment_id} ${self.amount:.2f} via {self.method.value} ({'OK' if self.success else 'PENDING'})"


# ============================================================================
# SECTION 3: STRATEGY PATTERN (Pricing)
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float, context: Dict) -> float:
        pass

class BasePricingStrategy(PricingStrategy):
    def apply(self, subtotal: float, context: Dict) -> float:
        return round(subtotal, 2)

class HappyHourPricingStrategy(PricingStrategy):
    def __init__(self, discount_percent: float = 0.20, start_hour: int = 16, end_hour: int = 18):
        self.discount_percent = discount_percent
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def apply(self, subtotal: float, context: Dict) -> float:
        hour = context.get('hour', 0)
        if self.start_hour <= hour < self.end_hour:
            # Discount only on drinks lines
            drink_sub = sum(i.line_subtotal() for i in context['items'] if i.menu_item.category == Category.DRINK)
            discount = drink_sub * self.discount_percent
            return round(subtotal - discount, 2)
        return round(subtotal, 2)

class ServiceChargePricingStrategy(PricingStrategy):
    def __init__(self, service_rate: float = 0.10):
        self.service_rate = service_rate
    
    def apply(self, subtotal: float, context: Dict) -> float:
        charge = subtotal * self.service_rate
        return round(subtotal + charge, 2)

class CompositePricingStrategy(PricingStrategy):
    def __init__(self, strategies: List[PricingStrategy]):
        self.strategies = strategies
    
    def apply(self, subtotal: float, context: Dict) -> float:
        total = subtotal
        for strat in self.strategies:
            total = strat.apply(total, context)
        return round(total, 2)

# ============================================================================
# SECTION 4: OBSERVER PATTERN
# ============================================================================

class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 🔔 {event.upper()}: {payload}")

# ============================================================================
# SECTION 5: FACTORY PATTERN
# ============================================================================

class ReservationFactory:
    _counter = 0
    @staticmethod
    def create(customer: Customer, table: Table, time: datetime) -> Reservation:
        ReservationFactory._counter += 1
        return Reservation(f"RSV{ReservationFactory._counter:04d}", customer, table, time)

class OrderFactory:
    _counter = 0
    @staticmethod
    def create(table: Table) -> Order:
        OrderFactory._counter += 1
        return Order(f"ORD{OrderFactory._counter:05d}", table)

class KitchenTicketFactory:
    _counter = 0
    @staticmethod
    def create(order: Order) -> KitchenTicket:
        KitchenTicketFactory._counter += 1
        return KitchenTicket(f"KT{KitchenTicketFactory._counter:04d}", order)

class PaymentFactory:
    _counter = 0
    @staticmethod
    def create(order: Order, amount: float, method: PaymentMethod) -> Payment:
        PaymentFactory._counter += 1
        return Payment(f"PAY{PaymentFactory._counter:05d}", order, amount, method)

# ============================================================================
# SECTION 6: COMMAND PATTERN
# ============================================================================

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class CreateReservationCommand(Command):
    def __init__(self, system: 'RestaurantSystem', customer: Customer, table: Table, time: datetime):
        self.system = system
        self.customer = customer
        self.table = table
        self.time = time
    def execute(self) -> Optional[Reservation]:
        return self.system.create_reservation(self.customer, self.table, self.time)

class CancelReservationCommand(Command):
    def __init__(self, reservation: Reservation):
        self.reservation = reservation
    def execute(self) -> bool:
        return self.reservation.cancel()

class PlaceOrderCommand(Command):
    def __init__(self, system: 'RestaurantSystem', table: Table, items: List[Tuple[str, int]]):
        self.system = system
        self.table = table
        self.items = items
    def execute(self) -> Optional[Order]:
        return self.system.place_order(self.table, self.items)

class UpdateOrderStatusCommand(Command):
    def __init__(self, order: Order, new_status: OrderStatus):
        self.order = order
        self.new_status = new_status
    def execute(self) -> bool:
        return self.order.update_status(self.new_status)

class ProcessPaymentCommand(Command):
    def __init__(self, system: 'RestaurantSystem', order: Order, method: PaymentMethod, strategy: PricingStrategy):
        self.system = system
        self.order = order
        self.method = method
        self.strategy = strategy
    def execute(self) -> Optional[Payment]:
        return self.system.process_payment(self.order, self.method, self.strategy)

# ============================================================================
# SECTION 7: SINGLETON SYSTEM
# ============================================================================

class RestaurantSystem:
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
            self.tables: Dict[str, Table] = {}
            self.menu: Dict[str, MenuItem] = {}
            self.reservations: Dict[str, Reservation] = {}
            self.orders: Dict[str, Order] = {}
            self.tickets: Dict[str, KitchenTicket] = {}
            self.payments: Dict[str, Payment] = {}
            self.observers: List[RestaurantObserver] = []
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'RestaurantSystem':
        return RestaurantSystem()
    
    def add_observer(self, observer: RestaurantObserver):
        self.observers.append(observer)
    
    def notify(self, event: str, payload: Dict):
        for obs in self.observers:
            obs.update(event, payload)
    
    # --- Menu & Tables ---
    def add_table(self, table_id: str, capacity: int):
        self.tables[table_id] = Table(table_id, capacity)
    
    def add_menu_item(self, item_id: str, name: str, category: Category, price: float):
        self.menu[item_id] = MenuItem(item_id, name, category, price)
    
    def get_available_table(self, capacity: int) -> Optional[Table]:
        for t in self.tables.values():
            if t.capacity >= capacity and t.status == TableStatus.AVAILABLE:
                return t
        return None
    
    # --- Reservation ---
    def create_reservation(self, customer: Customer, table: Table, time: datetime) -> Optional[Reservation]:
        if table.status != TableStatus.AVAILABLE:
            return None
        reservation = ReservationFactory.create(customer, table, time)
        self.reservations[reservation.reservation_id] = reservation
        self.notify('reservation_created', {'reservation_id': reservation.reservation_id, 'table': table.table_id, 'customer': customer.name})
        return reservation
    
    # --- Orders ---
    def place_order(self, table: Table, items: List[Tuple[str, int]]) -> Optional[Order]:
        if table.status not in [TableStatus.OCCUPIED, TableStatus.RESERVED]:
            return None
        order = OrderFactory.create(table)
        for item_id, qty in items:
            menu_item = self.menu.get(item_id)
            if not menu_item or not menu_item.is_available:
                continue
            order.add_item(OrderItem(menu_item, qty))
        if not order.items:
            return None
        self.orders[order.order_id] = order
        self.notify('order_placed', {'order_id': order.order_id, 'table': table.table_id, 'items': len(order.items)})
        return order
    
    def create_kitchen_ticket(self, order: Order) -> KitchenTicket:
        ticket = KitchenTicketFactory.create(order)
        self.tickets[ticket.ticket_id] = ticket
        self.notify('kitchen_ticket_created', {'ticket_id': ticket.ticket_id, 'order_id': order.order_id})
        return ticket
    
    # --- Payment ---
    def process_payment(self, order: Order, method: PaymentMethod, pricing_strategy: PricingStrategy) -> Optional[Payment]:
        if order.status != OrderStatus.SERVED:
            return None
        total = order.calculate_totals(pricing_strategy)
        payment = PaymentFactory.create(order, total, method)
        if payment.process():
            self.payments[payment.payment_id] = payment
            self.notify('payment_processed', {'payment_id': payment.payment_id, 'order_id': order.order_id, 'amount': total})
            # release table after payment
            order.table.release()
            return payment
        return None

# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def seed_system() -> RestaurantSystem:
    system = RestaurantSystem.get_instance()
    if not system.tables:  # avoid reseeding on reruns
        # Tables
        for i in range(1, 6):
            system.add_table(f"T{i}", capacity=2 + (i % 3) * 2)  # varied capacities
        # Menu Items
        system.add_menu_item("ITEM001", "Bruschetta", Category.STARTER, 6.50)
        system.add_menu_item("ITEM002", "Margherita Pizza", Category.MAIN, 12.00)
        system.add_menu_item("ITEM003", "Pasta Alfredo", Category.MAIN, 14.00)
        system.add_menu_item("ITEM004", "Tiramisu", Category.DESSERT, 7.00)
        system.add_menu_item("ITEM005", "Lemonade", Category.DRINK, 3.50)
        system.add_menu_item("ITEM006", "Espresso", Category.DRINK, 2.80)
    return system

def demo_1_setup():
    print("\n" + "=" * 70)
    print("DEMO 1: System Setup & Seeding")
    print("=" * 70)
    system = seed_system()
    system.add_observer(ConsoleObserver())
    print(f"✅ Tables: {len(system.tables)} | Menu Items: {len(system.menu)}")
    for t in system.tables.values():
        print(f"  - {t}")


def demo_2_reservation_flow():
    print("\n" + "=" * 70)
    print("DEMO 2: Reservation Lifecycle")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C001", "Alice", "alice@example.com")
    table = system.get_available_table(capacity=4)
    reservation = system.create_reservation(customer, table, datetime.now() + timedelta(hours=1))
    if reservation and reservation.confirm():
        print(f"✅ Confirmed {reservation}")
    # Occupy table
    if table.occupy():
        print(f"✅ Table {table.table_id} occupied")


def demo_3_order_lifecycle():
    print("\n" + "=" * 70)
    print("DEMO 3: Order Placement → Preparation → Ready → Served")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C002", "Bob", "bob@example.com")
    table = system.get_available_table(capacity=2)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM002", 2), ("ITEM005", 3), ("ITEM004", 1)])
    if order:
        print(f"✅ Placed {order}")
        ticket = system.create_kitchen_ticket(order)
        ticket.start()
        print(f"🍳 Started preparation for {order.order_id}")
        ticket.complete()
        print(f"✅ Order {order.order_id} READY")
        order.update_status(OrderStatus.SERVED)
        print(f"✅ Order {order.order_id} SERVED")


def demo_4_pricing_and_payment():
    print("\n" + "=" * 70)
    print("DEMO 4: Pricing Strategy & Payment")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C003", "Carol", "carol@example.com")
    table = system.get_available_table(capacity=2)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM005", 4), ("ITEM006", 2), ("ITEM002", 1)])  # drinks + main
    ticket = system.create_kitchen_ticket(order)
    ticket.start()
    ticket.complete()
    order.update_status(OrderStatus.SERVED)
    # Apply composite: happy hour + service charge
    composite = CompositePricingStrategy([HappyHourPricingStrategy(start_hour=0, end_hour=23), ServiceChargePricingStrategy(0.10)])
    total = order.calculate_totals(composite)
    print(f"Subtotal: ${order.subtotal:.2f} | Final (HH + Service): ${total:.2f}")
    payment = system.process_payment(order, PaymentMethod.CARD, composite)
    if payment:
        print(f"✅ {payment}")


def demo_5_full_flow():
    print("\n" + "=" * 70)
    print("DEMO 5: End-to-End Scenario")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C004", "Dana", "dana@example.com")
    table = system.get_available_table(capacity=4)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM001", 1), ("ITEM002", 1), ("ITEM005", 2)])
    ticket = system.create_kitchen_ticket(order)
    ticket.start()
    ticket.complete()
    order.update_status(OrderStatus.SERVED)
    # Simple pricing
    pricing = BasePricingStrategy()
    billing = order.calculate_totals(pricing)
    payment = system.process_payment(order, PaymentMethod.CASH, pricing)
    print(f"Final Bill: ${billing:.2f} | Payment Success: {payment.success if payment else False}")
    print(f"Table Released: {table.status.value}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RESTAURANT MANAGEMENT SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory | Command")
    print("=" * 70)
    demo_1_setup()
    demo_2_reservation_flow()
    demo_3_order_lifecycle()
    demo_4_pricing_and_payment()
    demo_5_full_flow()
    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • State: Order & reservation transitions enforced")
    print("  • Strategy: Flexible pricing (happy hour, service charge)")
    print("  • Observer: Decoupled notifications for events")
    print("  • Factory: Centralized creation & ID generation")
    print("  • Command: Encapsulated high-level operations")
    print("  • Singleton: Single orchestrator instance")
    print("\nSee 75_MINUTE_GUIDE.md for deep explanations & UML.")

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
