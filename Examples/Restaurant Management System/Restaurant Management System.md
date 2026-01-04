# Restaurant Management System — 75-Minute Interview Guide

## Quick Start

### 5-Minute Overview
A restaurant management platform handling reservations, table management, menu ordering, kitchen coordination, bill calculation, and payment processing. Core flow: **Reservation → Seating → Order → Kitchen → Billing → Payment**.

### Key Entities
| Entity | Purpose |
|--------|---------|
| **Table** | Physical seating (status: FREE/RESERVED/OCCUPIED) |
| **Reservation** | Customer hold on table |
| **MenuItem** | Menu item with price & availability |
| **Order** | Customer order lifecycle |
| **KitchenTicket** | Preparation task tracking |
| **Payment** | Bill processing |

### 6 Design Patterns
1. **Singleton**: Central `RestaurantSystem` coordinator
2. **Strategy**: `PricingStrategy` (Regular, HappyHour, Member)
3. **Observer**: Events (OrderPlaced, KitchenReady, BillPrepared)
4. **State**: `OrderStatus` enum (RECEIVED→PREPARING→READY→SERVED→PAID)
5. **Factory**: `OrderFactory.create()` for order creation
6. **Command**: `PlaceOrderCommand`, `PayBillCommand` operations

### Critical Points
✅ Prevent double-booking → Atomic table reservation + lock  
✅ Kitchen coordination → KitchenTicket with status tracking  
✅ Bill calculation → ItemPrice × Qty + Tax + Service - Discount  
✅ Concurrent orders → Thread-safe Singleton  
✅ Scaling → Microservices, Kafka, distributed locks  

---

## System Overview

### Problem Statement
Restaurants manage multiple concurrent operations: reservations, table occupancy, food ordering, kitchen coordination, and payment. System must prevent table double-booking, ensure kitchen workflow, and provide accurate billing with flexible pricing.

### Core Workflow
```
Reservation → Check-in → Order → Kitchen → Billing → Payment → Cleanup
```

---

## Requirements & Scope

### Functional Requirements
✅ Customer reservation with availability checking  
✅ Table management (status tracking)  
✅ Order management (add items, modify, cancel)  
✅ Menu pricing with strategy-based discounts  
✅ Kitchen ticket generation and tracking  
✅ Bill calculation (tax, service charge, discounts)  
✅ Payment processing  
✅ Notifications (reservation, order status)  

### Non-Functional Requirements
✅ Support 100+ concurrent customers  
✅ <500ms reservation lookup  
✅ <200ms order placement  
✅ <1s bill calculation  
✅ 99.9% uptime  

### Out of Scope
❌ Payment gateway integration  
❌ Multi-location synchronization  
❌ Inventory management  
❌ Delivery orders  

---

## Architecture & Design Patterns

### 1. Singleton Pattern
**Problem**: Race conditions on table assignment  
**Solution**: Thread-safe single `RestaurantSystem` instance

```python
class RestaurantSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

---

### 2. Strategy Pattern (Pricing)
**Problem**: Multiple pricing models need to coexist  
**Solution**: Pluggable strategies

```python
class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float) -> float:
        pass

class HappyHourPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.8  # 20% off

class MemberPricing(PricingStrategy):
    def apply(self, subtotal: float) -> float:
        return subtotal * 0.85  # 15% off
```

---

### 3. Observer Pattern
**Problem**: Kitchen, billing, notifications need real-time updates  
**Solution**: Abstract Observer interface

```python
class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class KitchenObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        if event == "ORDER_PLACED":
            # Send to kitchen display
            pass
```

---

### 4. State Pattern
**Problem**: Orders have valid & invalid state transitions  
**Solution**: Enum-based state management

```python
class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    PAID = "paid"
    CANCELLED = "cancelled"
```

---

### 5. Factory Pattern
**Problem**: Order creation scattered in code  
**Solution**: Centralized factory

```python
class OrderFactory:
    _counter = 0
    
    @staticmethod
    def create_order(table: Table, items: List[MenuItem]) -> Order:
        OrderFactory._counter += 1
        order_id = f"ORD{OrderFactory._counter}"
        return Order(order_id, table, items)
```

---

### 6. Command Pattern
**Problem**: Operations need logging and undo  
**Solution**: Command objects

```python
class PlaceOrderCommand:
    def __init__(self, system, table, items):
        self.system = system
        self.table = table
        self.items = items
    
    def execute(self):
        return self.system.place_order(self.table, self.items)
```

---

## Core Entities & UML Diagram

```
┌──────────────────────────────────────────────┐
│     RestaurantSystem (Singleton)             │
├──────────────────────────────────────────────┤
│ - tables: Dict[str, Table]                   │
│ - reservations: Dict[str, Reservation]       │
│ - orders: Dict[str, Order]                   │
│ - pricing_strategy: PricingStrategy          │
├──────────────────────────────────────────────┤
│ + reserve_table(): Reservation               │
│ + check_in(): bool                           │
│ + place_order(): Order                       │
│ + process_payment(): Payment                 │
│ + calculate_bill(): Bill                     │
└──────────────────────────────────────────────┘
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
  Table  Customer MenuItem
    │       │
    └─ Reservation
        │
    Order
        │
    KitchenTicket
```

---

## Interview Q&A

### Q1: How prevent double-booking?
**A**: Atomic reservation with thread locks. Only one replica can mark table RESERVED at a time.

### Q2: Reservation vs Order difference?
**A**: Reservation is time-limited hold (30-60 min). Order is actual food ordered after check-in.

### Q3: How coordinate kitchen?
**A**: KitchenTicket workflow (PENDING → PREPARING → READY → SERVED).

### Q4: Calculate bills accurately?
**A**: `subtotal → pricing_strategy.apply() → add tax + service → total`.

### Q5: Why Strategy for pricing?
**A**: Different rules (happy hour, member, group) swapped without modifying Order.

### Q6: Scale to multiple restaurants?
**A**: Each restaurant gets own RestaurantSystem instance. Independent operation.

### Q7: Handle no-show reservations?
**A**: Background job checks time. After 15 min: status=NO_SHOW, table=FREE.

### Q8: Prevent order modification after kitchen receives?
**A**: Only modify in RECEIVED state. PREPARING status locks order.

### Q9: Handle payment failures?
**A**: Retry 3x. On fail: Bill status=FAILED, customer notified.

### Q10: What metrics to track?
**A**: Table utilization, avg order value, processing time, payment success rate, reservation conversion.

---

## Scaling Q&A

### Q1: Scale to 1000+ tables across 100 restaurants?
**A**: Each restaurant independent RestaurantSystem. Shared analytics DB aggregates.

### Q2: Handle 1000 orders/hour peak?
**A**: Queue orders if latency > 500ms. Async kitchen tickets. Cache menu prices.

### Q3: Prevent table overbooking across replicas?
**A**: Distributed lock (Redis) for atomic reservation globally.

### Q4: Payment concurrency?
**A**: Optimistic locking with version numbers. Read → attempt update if version matches.

### Q5: Scale kitchen operations?
**A**: Kafka topic with multiple partition workers. Parallel prep stations.

### Q6: Ensure 99.9% uptime?
**A**: Multi-replica setup, health checks, RTO < 30s, RPO < 5min.

### Q7: Test at scale?
**A**: Load test 1000 concurrent orders. Monitor latency p99, error rate, DB connections.

---

## Demo Scenarios

**Demo 1**: Reservation & check-in  
**Demo 2**: Order placement & kitchen  
**Demo 3**: Bill calculation with pricing  
**Demo 4**: Payment processing  
**Demo 5**: Pricing strategy switch  

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| Table Management | Singleton + locks |
| Pricing | Strategy pattern |
| Kitchen Coordination | Observer pattern |
| Order Flow | State machine |
| Bill Accuracy | Clear calculation |
| Scalability | Multiple instances + events |

---

**Ready for your interview! 👨‍🍳**
