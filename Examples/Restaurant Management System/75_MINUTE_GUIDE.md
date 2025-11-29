# Restaurant Management System - 75 Minute Interview Deep Dive

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
