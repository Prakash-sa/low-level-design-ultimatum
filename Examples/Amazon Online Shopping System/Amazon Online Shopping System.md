# Amazon Online Shopping System — Complete Design Guide

> E-commerce platform for browsing, cart management, checkout, order tracking, and notifications.

**Scale**: 100K+ concurrent users, 1M+ products, 24/7 uptime, peak: 10K TPS  
**Duration**: 75-minute interview guide  
**Focus**: Inventory management, cart operations, checkout flow, state transitions

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [System Overview](#system-overview)
3. [Requirements & Scope](#requirements--scope)
4. [Architecture & Design Patterns](#architecture--design-patterns)
5. [Core Entities & UML Diagram](#core-entities--uml-diagram)
6. [Implementation Guide](#implementation-guide)
7. [Interview Q&A](#interview-qa)
8. [Scaling Q&A](#scaling-qa)
9. [Demo & Running](#demo--running)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Users browse products → add to cart (no inventory deduction) → checkout (reserve inventory atomically) → place order → receive notifications → track shipment.

### Key Design Patterns
| Pattern | Why | Used For |
|---------|-----|----------|
| **Singleton** | Single consistent state | ShoppingSystem (thread-safe) |
| **Strategy (Pricing)** | Pluggable algorithms | Regular/Bulk/Membership pricing |
| **Strategy (Search)** | Chainable filters | Category/Price/Rating filters |
| **Observer** | Decouple notifications | Email/SMS/Push notifiers |
| **State** | Valid transitions | Order lifecycle (PENDING → SHIPPED) |

### Critical Interview Points
- ✅ How to prevent double-booking? → Atomic inventory reservation at checkout
- ✅ Cart vs Order state? → Cart: temporary items, Order: confirmed purchase
- ✅ Thread-safety? → Singleton with threading.Lock for all operations
- ✅ Scaling? → Multiple locations, distributed locks (Redis), async notifications

---

## System Overview

### Core Problem
```
Customer browses products
        ↓
ADD TO CART (no inventory deduction, just collecting items)
        ↓
CHECKOUT (atomic: reserve inventory, create order, lock items)
        ↓
If reservation succeeds → Create order, send notifications
If reservation fails → Release everything, cart unchanged
        ↓
ORDER LIFECYCLE (PENDING → CONFIRMED → SHIPPED → DELIVERED)
        ↓
Track shipment, send status updates
```

### Key Constraints
- **Concurrency**: 100K+ simultaneous users browsing/adding/checking out
- **Inventory**: No double-selling (atomic reservation)
- **Search**: 1M+ products, fast filtering (category/price/rating)
- **State**: Clear order transitions, no invalid state changes

---

## Requirements & Scope

### Functional Requirements
✅ Browse & search products (category, price, rating filters)  
✅ Add/remove items from shopping cart  
✅ Apply different pricing strategies (regular, bulk, membership)  
✅ Checkout with atomic inventory reservation  
✅ Track order lifecycle (PENDING → DELIVERED)  
✅ Receive notifications (email, SMS, push)  
✅ Cancel orders (only before shipment)  

### Non-Functional Requirements
✅ Support 100K+ concurrent users  
✅ <100ms search response time  
✅ <500ms checkout response time  
✅ 99.9% uptime  
✅ Accurate inventory tracking  

### Out of Scope
❌ Payment processing (assume external gateway)  
❌ Returns/refunds  
❌ Customer app frontend  
❌ Seller portal  

---

## Architecture & Design Patterns

### 1. Singleton Pattern (Thread-Safe)

**Problem**: 100K users accessing shopping system concurrently → race conditions on inventory

**Solution**: Single ShoppingSystem instance with thread locks

```python
class ShoppingSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Why It Matters**: 
- All users share same inventory (single source of truth)
- Lock ensures only one user can reserve at a time
- Prevents over-selling last item

---

### 2. Strategy Pattern (Pricing)

**Problem**: Different pricing models (regular, bulk discount 10% for 5+, membership 15% off) need different logic

**Solution**: Pluggable pricing strategies

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price, quantity):
        pass

class BulkPricing(PricingStrategy):
    def calculate_price(self, base_price, qty):
        return base_price * qty * 0.9 if qty >= 5 else base_price * qty

# Switch at checkout
system.set_pricing_strategy(BulkPricing())
total = strategy.calculate_price(100, 5)  # $450 (10% off)
```

**Interview Benefit**: Easy to add new strategies (seasonal, regional) without modifying checkout

---

### 3. Strategy Pattern (Search Filters)

**Problem**: Search by category + price + rating simultaneously without nested loops

**Solution**: Chainable filter strategies

```python
class SearchFilter(ABC):
    @abstractmethod
    def filter(self, products):
        pass

# Chain filters
filters = [
    CategoryFilter(ProductCategory.ELECTRONICS),
    PriceFilter(500, 1500),
    RatingFilter(4.0)
]
results = system.search_products(filters)  # Electronics, $500-1500, 4+ stars
```

**Interview Benefit**: Each filter independent, composable, no coupling

---

### 4. Observer Pattern (Notifications)

**Problem**: System shouldn't know about Email/SMS/Push implementation details

**Solution**: Abstract Observer interface, pluggable notifiers

```python
class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event, order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event, order):
        # Send email
        pass

# Add notifiers
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())

# All fire on event
system.notify_all("ORDER_PLACED", order)
```

**Interview Benefit**: Add Slack notifier without touching core system

---

### 5. State Pattern (Order Lifecycle)

**Problem**: Orders have valid transitions (PENDING → SHIPPED) and invalid ones (DELIVERED → PENDING)

**Solution**: Enum-based state with validation

```python
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order:
    def ship(self, tracking):
        if self.status != OrderStatus.CONFIRMED:
            raise InvalidTransition()
        self.status = OrderStatus.SHIPPED
```

**Interview Benefit**: Prevents invalid state transitions at compile time

---

## Core Entities & UML Diagram

### Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  SHOPPING SYSTEM                                │
│                  (Singleton)                                    │
└─────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌────────────┐
        │ Product  │   │  User    │   │  Order     │
        │ (1M+)    │   │(100K+)   │   │(tracking)  │
        ├──────────┤   ├──────────┤   ├────────────┤
        │ - name   │   │ - email  │   │ - status   │
        │ - price  │   │ - phone  │   │ - items[]  │
        │ - qty    │   │ - orders │   │ - total    │
        │ - reserve│   └──────────┘   │ - confirm()│
        │ - release│        │         │ - ship()   │
        └──────────┘        │         │ - cancel() │
             │              │         └────────────┘
             │ HAS-A        │ CREATES       │
             │              │              │ CONTAINS
             ▼              ▼              ▼
        ┌─────────────────────────────────────┐
        │       ShoppingCart                  │
        │  • items[] (CartItem)               │
        │  • add_item()                       │
        │  • remove_item()                    │
        │  • checkout() → Order               │
        └─────────────────────────────────────┘
                    │
                    │ CONTAINS (1..*)
                    │
                    ▼
        ┌─────────────────────────────────────┐
        │       CartItem                      │
        │  • product (Product)                │
        │  • quantity                         │
        │  • status (ADDED/RESERVED)          │
        │  • reserve()                        │
        │  • release()                        │
        └─────────────────────────────────────┘


STRATEGY PATTERNS:

┌──────────────────────────────────────────────────┐
│    PricingStrategy (Abstract)                    │
│  • calculate_price(base_price, qty)              │
├──────────────────────────────────────────────────┤
│  ├─ RegularPricing (no discount)                 │
│  ├─ BulkPricing (10% off for 5+)                │
│  └─ MembershipPricing (15% off)                 │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│    SearchFilter (Abstract)                       │
│  • filter(products) → List[Product]              │
├──────────────────────────────────────────────────┤
│  ├─ CategoryFilter                               │
│  ├─ PriceFilter                                  │
│  └─ RatingFilter                                 │
└──────────────────────────────────────────────────┘


OBSERVER PATTERN:

┌──────────────────────────────────────────────────┐
│    OrderObserver (Abstract)                      │
│  • notify(event, order)                          │
├──────────────────────────────────────────────────┤
│  ├─ EmailNotifier                                │
│  ├─ SMSNotifier                                  │
│  └─ PushNotifier                                 │
└──────────────────────────────────────────────────┘


ENUMERATIONS:

┌────────────────────────────┐
│ ProductCategory (Enum)     │
├────────────────────────────┤
│ • ELECTRONICS              │
│ • BOOKS                    │
│ • CLOTHING                 │
│ • HOME                     │
│ • SPORTS                   │
└────────────────────────────┘

┌────────────────────────────┐
│ OrderStatus (Enum)         │
├────────────────────────────┤
│ • PENDING                  │
│ • CONFIRMED                │
│ • SHIPPED                  │
│ • DELIVERED                │
│ • CANCELLED                │
└────────────────────────────┘

┌────────────────────────────┐
│ CartItemStatus (Enum)      │
├────────────────────────────┤
│ • ADDED                    │
│ • RESERVED                 │
│ • PURCHASED                │
│ • REMOVED                  │
└────────────────────────────┘
```

### Entity Relationships

| Entity | Relationship | Count | Purpose |
|--------|-------------|-------|---------|
| Product | HAS-A Inventory | 1 | Catalog with stock tracking |
| ShoppingCart | HAS-A CartItem | 0..* | User's temporary collection |
| CartItem | REFERENCES Product | 1 | Product + quantity in cart |
| Order | CONTAINS CartItem | 1..* | Confirmed purchase items |
| Order | OWNED-BY User | 1..1 | Purchase history |
| User | HAS-A ShoppingCart | 1 | Per-user cart |

---

## Implementation Guide

### Step 1: Core Entities

```python
from enum import Enum
from datetime import datetime, timedelta
import uuid
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class ProductCategory(Enum):
    ELECTRONICS = "electronics"
    BOOKS = "books"
    CLOTHING = "clothing"
    HOME = "home"
    SPORTS = "sports"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class CartItemStatus(Enum):
    ADDED = "added"
    RESERVED = "reserved"
    PURCHASED = "purchased"
    REMOVED = "removed"

class Product:
    def __init__(self, product_id, name, category, price, quantity):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.quantity_available = quantity
        self.rating = 0.0
        self.reviews = []

    def is_available(self, qty):
        return self.quantity_available >= qty

    def reserve(self, qty):
        if self.is_available(qty):
            self.quantity_available -= qty
            return True
        return False

    def release(self, qty):
        self.quantity_available += qty

class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity
        self.status = CartItemStatus.ADDED

    def get_total_price(self):
        return self.product.price * self.quantity

    def reserve(self):
        if self.product.reserve(self.quantity):
            self.status = CartItemStatus.RESERVED
            return True
        return False

    def release(self):
        self.product.release(self.quantity)
        self.status = CartItemStatus.REMOVED

class ShoppingCart:
    def __init__(self, user_id):
        self.cart_id = str(uuid.uuid4())[:8]
        self.user_id = user_id
        self.items = {}

    def add_item(self, product, quantity):
        if not product.is_available(quantity):
            return False
        if product.product_id in self.items:
            self.items[product.product_id].quantity += quantity
        else:
            self.items[product.product_id] = CartItem(product, quantity)
        return True

    def remove_item(self, product_id):
        if product_id in self.items:
            del self.items[product_id]
            return True
        return False

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.values())

    def clear(self):
        for item in self.items.values():
            item.release()
        self.items.clear()

class Order:
    def __init__(self, order_id, user_id, items, total_price):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_price = total_price
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.tracking_number = None

    def confirm(self):
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
            return True
        return False

    def ship(self, tracking_number):
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.SHIPPED
            self.tracking_number = tracking_number
            return True
        return False

    def deliver(self):
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.DELIVERED
            return True
        return False

    def cancel(self):
        if self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            for item in self.items.values():
                item.release()
            self.status = OrderStatus.CANCELLED
            return True
        return False

class User:
    def __init__(self, user_id, name, email, phone):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.orders = []
```

### Step 2: Strategies & Observers

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price, quantity):
        pass

class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price, quantity):
        return base_price * quantity

class BulkPricing(PricingStrategy):
    def calculate_price(self, base_price, quantity):
        if quantity >= 5:
            return base_price * quantity * 0.9
        return base_price * quantity

class MembershipPricing(PricingStrategy):
    def calculate_price(self, base_price, quantity):
        return base_price * quantity * 0.85

class SearchFilter(ABC):
    @abstractmethod
    def filter(self, products):
        pass

class CategoryFilter(SearchFilter):
    def __init__(self, category):
        self.category = category

    def filter(self, products):
        return [p for p in products if p.category == self.category]

class PriceFilter(SearchFilter):
    def __init__(self, min_price, max_price):
        self.min_price = min_price
        self.max_price = max_price

    def filter(self, products):
        return [p for p in products if self.min_price <= p.price <= self.max_price]

class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event, order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event, order):
        print(f"📧 Email: Order {order.order_id} - {event}")

class SMSNotifier(OrderObserver):
    def notify(self, event, order):
        print(f"📱 SMS: Order {order.order_id} - {event}")
```

### Step 3: Singleton Controller

```python
class ShoppingSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.products = {}
                    cls._instance.users = {}
                    cls._instance.carts = {}
                    cls._instance.orders = {}
                    cls._instance.observers = []
                    cls._instance.pricing_strategy = RegularPricing()
        return cls._instance

    def add_product(self, name, category, price, quantity):
        product_id = str(uuid.uuid4())[:8]
        product = Product(product_id, name, category, price, quantity)
        self.products[product_id] = product
        return product

    def register_user(self, name, email, phone):
        user_id = str(uuid.uuid4())[:8]
        user = User(user_id, name, email, phone)
        self.users[user_id] = user
        return user

    def search_products(self, filters):
        results = list(self.products.values())
        for filter_strategy in filters:
            results = filter_strategy.filter(results)
        return results

    def add_to_cart(self, user_id, product_id, quantity):
        cart = self.carts.setdefault(user_id, ShoppingCart(user_id))
        product = self.products.get(product_id)
        return cart.add_item(product, quantity) if product else False

    def checkout(self, user_id):
        with self._lock:
            cart = self.carts.get(user_id)
            if not cart or not cart.items:
                return None

            # Reserve all items
            for item in cart.items.values():
                if not item.reserve():
                    for reserved_item in cart.items.values():
                        reserved_item.release()
                    return None

            # Create order
            order_id = str(uuid.uuid4())[:8]
            total = 0
            for item in cart.items.values():
                total += self.pricing_strategy.calculate_price(
                    item.product.price, item.quantity
                )

            order = Order(order_id, user_id, dict(cart.items), total)
            self.orders[order_id] = order
            self.notify_all("ORDER_PLACED", order)
            cart.clear()
            del self.carts[user_id]
            return order

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_all(self, event, order):
        for observer in self.observers:
            observer.notify(event, order)

    def set_pricing_strategy(self, strategy):
        self.pricing_strategy = strategy
```

---

## Interview Q&A

### Q1: How do you prevent double-booking during concurrent checkouts?

**A**: Atomic reservation at checkout:
1. Lock acquired (Singleton with threading.Lock)
2. For each cart item, attempt to reserve inventory
3. If ANY reservation fails, rollback all and return error
4. Lock released after entire operation

If 2 users both have last item in cart and checkout simultaneously, only 1 succeeds in reserving it. Other gets "out of stock" error.

---

### Q2: What's the difference between adding to cart and checkout?

**A**: 
- **Add to Cart**: No inventory change, just check availability. Item stays in cart even if stock changes.
- **Checkout**: Atomic operation. Reserve inventory, create order, remove from cart.

This prevents showing "out of stock" after user adds to cart.

---

### Q3: Why use Strategy pattern for pricing?

**A**: Different pricing models (regular, bulk 10%, membership 15%) can coexist. Add seasonal pricing without modifying checkout logic. Switch strategies at runtime.

---

### Q4: How do search filters work?

**A**: Each filter is independent strategy. CategoryFilter reduces products to category. PriceFilter narrows by price. RatingFilter filters by rating. Chain them: 1M products → 10K electronics → 2K under $1500 → 500 rated 4+.

---

### Q5: How do notifications decouple from orders?

**A**: Observer pattern. Order doesn't know about EmailNotifier, SMSNotifier. Just fires `notify_all("ORDER_PLACED", order)`. Each observer handles independently. Add SlackNotifier = add observer.

---

### Q6: How to handle item going out of stock while in cart?

**A**: Check availability at checkout. If item unavailable, entire checkout fails. Cart unchanged. User gets "Item X out of stock" message. User can remove item and retry.

---

### Q7: How to prevent customers from gaming bulk pricing?

**A**: Enforce bulk pricing only for same product in single checkout. Split across multiple orders? Each order calculated separately. Track by order_id, not customer.

---

### Q8: What if customer loses internet during checkout?

**A**: Checkout is atomic operation inside lock. Either entire order succeeds or entire order fails. No partial orders. If client loses connection mid-checkout, server finishes operation, returns success/error.

---

### Q9: How to handle abandoned carts?

**A**: Background job clears carts older than 24 hours. Release reserved items back to inventory. Email customer: "Your cart is expiring".

---

### Q10: How do you track order history?

**A**: User object maintains orders[] list. When order created, append to user.orders. Query user.orders for history. Add created_at timestamp for sorting.

---

## Scaling Q&A

### Q1: How would you scale to 100K+ concurrent users and 1M+ products?

**A**: Multi-tier architecture:

**Tier 1: Product Catalog**
- Partition by category (sharding)
- Search index (Elasticsearch) for fast filtering
- Cache popular products in memory (Redis)
- Read replicas for inventory checks

**Tier 2: Carts & Checkout**
- ShoppingSystem replica per region
- Session affinity (user always hits same replica)
- Redis for distributed locks (not just threading.Lock)
- Queue checkout operations if peak load

**Tier 3: Orders**
- Distributed database (PostgreSQL with sharding)
- Shard by user_id or order_id
- Replication for backup

```
Load Balancer
    ├─ ShoppingSystem Replica 1 (25K users)
    ├─ ShoppingSystem Replica 2 (25K users)
    ├─ ShoppingSystem Replica 3 (25K users)
    └─ ShoppingSystem Replica 4 (25K users)
    ↓
Shared Product DB (read replicas)
Shared Order DB (sharded by region)
Redis (distributed locks, caching)
```

---

### Q2: How to prevent double-booking across multiple replicas?

**A**: 

**Problem**: Each ShoppingSystem replica has own threading.Lock. Two users on different replicas can reserve same item.

**Solution**: Distributed lock (Redis)

```python
# Instead of threading.Lock
def checkout(self, user_id):
    with redis_lock.acquire(f"inventory-{product_id}", timeout=5):
        # Reserve inventory
        # Create order
        pass
```

Only 1 replica can checkout per product at a time. Prevents double-booking globally.

---

### Q3: How to sync product inventory across replicas?

**A**: 

**Option 1: Pessimistic Locking**
- All inventory stored in central DB
- Check before reserve: `SELECT quantity FROM products WHERE id=X FOR UPDATE`
- Update: `UPDATE products SET quantity=quantity-Y WHERE id=X`
- Consistent but slower (network latency)

**Option 2: Optimistic Locking**
- Products cached in each replica with version number
- Checkout: read version, attempt update if version matches
- If version mismatch: retry with new version
- Fast but eventual consistency

**Option 3: Event Sourcing**
- All checkout events logged to Kafka
- Events replayed to update inventory
- Eventually consistent, audit trail

Most common: **Pessimistic for critical inventory, Optimistic for caching**

---

### Q4: How would you handle peak traffic (holiday sales 10K TPS)?

**A**:

**Before Peak**:
- Auto-scale ShoppingSystem replicas (Kubernetes)
- Pre-warm product cache
- Increase DB connection pool

**During Peak**:
1. **Shedding**: Queue checkouts if latency > 1000ms
2. **Async**: Process orders asynchronously (in-memory queue)
3. **Caching**: Cache product searches (1-minute TTL)
4. **Notifications**: Queue notifications (don't block checkout)

```
Checkout Request
    ↓
Lock acquired
    ↓
Reserve inventory (fast)
    ↓
Create order
    ↓
Release lock
    ↓
Queue notification event (async)
    ↓
Return success immediately
```

Actual email/SMS sent in background worker.

---

### Q5: How to scale notifications to 1M+ orders/day?

**A**:

```
Order Event → Kafka Topic
    ├─ Worker 1: Email notifier (100 msgs/sec)
    ├─ Worker 2: Email notifier (100 msgs/sec)
    ├─ Worker 3: SMS notifier (50 msgs/sec)
    └─ Worker 4: Push notifier (50 msgs/sec)
    ↓
Batch 100 notifications
    ↓
SendGrid/Twilio/Firebase
    ↓
99.9% delivery within 30s
```

Benefits: Parallel processing, batch efficiency, fault isolation, auto-retry on failure.

---

### Q6: How to handle product search across 1M+ items?

**A**:

**Problem**: Filter 1M products by category/price/rating on every search = O(n) = slow

**Solution**: Search Index (Elasticsearch)

```
Elasticsearch Cluster
    ├─ Index 1: Electronics (100K docs)
    ├─ Index 2: Books (200K docs)
    ├─ Index 3: Clothing (300K docs)
    └─ Index 4: Home (400K docs)

Query: category=ELECTRONICS AND price:[500,1500] AND rating:[4,5]
    ↓
ES returns matching docs in <100ms (vs 1000ms with array filtering)
```

Each shard handles subset of products. Parallel search. Fast.

---

### Q7: How to handle cart expiry and cleanup?

**A**:

**Problem**: Carts accumulate indefinitely, memory grows unbounded

**Solution**: TTL-based cleanup

```python
# Background job (runs every hour)
def cleanup_abandoned_carts():
    for user_id, cart in carts.items():
        age = datetime.now() - cart.created_at
        if age > timedelta(days=1):
            cart.clear()  # Release items back
            del carts[user_id]
            notify_user(user_id, "Cart expired")
```

Alternative: Redis with TTL auto-expiry (carts auto-deleted after 24h).

---

### Q8: How to ensure 99.9% uptime for checkout?

**A**:

**Redundancy**:
```
Primary Region
    ├─ ShoppingSystem A (active)
    ├─ ShoppingSystem B (warm standby)
    ├─ DB Primary + 2 replicas
    
Secondary Region (failover)
    ├─ ShoppingSystem C (cold standby)
    ├─ DB replica
```

**Health Checks** (every 10s):
- Response time > 500ms → degrade service
- Error rate > 1% → alert
- DB unavailable → failover to replica

**Graceful Degradation**:
- If primary region fails → switch to secondary
- 1-2 minute RTO (Recovery Time Objective)
- No data loss (replicated to secondary)

---

### Q9: How to perform rolling updates without downtime?

**A**:

**Blue-Green Deployment**:

Week 1: Deploy v2 to "blue" environment (isolated)
Week 2-3: Migrate traffic 10% → 25% → 50% → 100%
Week 4: All traffic on blue, decommission green

During migration: Monitor error rates, latency. Rollback if issues.

---

### Q10: How to partition products across multiple regions?

**A**:

**Shard by Category** (geographic-agnostic):
```
Shard 1: ELECTRONICS (100K products)
    ├─ US warehouse
    ├─ EU warehouse
    ├─ APAC warehouse
    
Shard 2: BOOKS (200K products)
    ├─ US warehouse
    ├─ EU warehouse
    ├─ APAC warehouse
```

Each shard replicated across 3 regions. Fast access from any region.

**Shard by Geography** (if product availability differs):
```
US Shard: Products available in US (800K)
EU Shard: Products available in EU (600K)
APAC Shard: Products available in APAC (400K)
```

User searches only their region's shard. Fast, no cross-region latency.

---

### Q11: How to handle payment failures during checkout?

**A**:

**Assumption**: Payment is external service (not in scope).

But if order created BEFORE payment confirmed:

```
1. Create order (status=PENDING)
2. Call payment service
3. If success: set status=CONFIRMED
4. If failure: set status=CANCELLED, release inventory

# Background job monitors PENDING orders
# If PENDING > 30 min: assume payment timeout, auto-cancel
```

---

### Q12: How to test checkout at scale (100K TPS)?

**A**:

**Load Test**:
```bash
wrk -t12 -c100000 -d60s \
  --script=checkout.lua \
  "https://api.shop.com/checkout"

Monitor:
- Response time p99 < 500ms
- Error rate < 0.1%
- Inventory consistency
```

**Chaos Test**:
1. Kill random replica → system should failover
2. Add 100ms latency to DB → measure degradation
3. Partition network for 30s → test recovery
4. Spike: 10K → 50K TPS → test auto-scaling

**Verify**:
- No double-selling
- No lost orders
- No orphaned carts
- Payment consistency

---

## Demo & Running

### Quick Demo

```python
#!/usr/bin/env python3

def run_demo():
    print("=" * 70)
    print("AMAZON SHOPPING SYSTEM - INTERACTIVE DEMO")
    print("=" * 70)
    
    # Setup
    system = ShoppingSystem()
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    p1 = system.add_product("Laptop", ProductCategory.ELECTRONICS, 999.99, 5)
    p2 = system.add_product("Book", ProductCategory.BOOKS, 49.99, 20)
    p3 = system.add_product("T-Shirt", ProductCategory.CLOTHING, 19.99, 100)
    
    user1 = system.register_user("Alice", "alice@email.com", "555-1234")
    user2 = system.register_user("Bob", "bob@email.com", "555-5678")
    
    print("\n✅ Catalog created")
    print(f"   Products: {len(system.products)}")
    print(f"   Users: {len(system.users)}")
    
    # Search
    print("\n✅ Demo 2: Search")
    filters = [CategoryFilter(ProductCategory.ELECTRONICS)]
    results = system.search_products(filters)
    print(f"   Electronics found: {len(results)}")
    
    # Add to cart
    print("\n✅ Demo 3: Add to cart")
    system.add_to_cart(user1.user_id, p1.product_id, 1)
    system.add_to_cart(user1.user_id, p2.product_id, 2)
    cart = system.carts[user1.user_id]
    print(f"   Cart items: {len(cart.items)}")
    print(f"   Cart total: ${cart.get_total_price():.2f}")
    
    # Checkout with pricing
    print("\n✅ Demo 4: Regular pricing")
    order1 = system.checkout(user1.user_id)
    if order1:
        print(f"   Order: {order1.order_id}")
        print(f"   Total: ${order1.total_price:.2f}")
    
    # Bulk pricing
    print("\n✅ Demo 5: Bulk pricing (10% off for 5+)")
    system.set_pricing_strategy(BulkPricing())
    for _ in range(5):
        system.add_to_cart(user2.user_id, p3.product_id, 1)
    order2 = system.checkout(user2.user_id)
    if order2:
        print(f"   Order: {order2.order_id}")
        print(f"   Total: ${order2.total_price:.2f}")

if __name__ == "__main__":
    run_demo()
```

---

## Success Criteria

| Criterion | Status |
|-----------|--------|
| Can explain 5 design patterns | ✅ |
| Can draw UML diagram | ✅ |
| Understand concurrency handling | ✅ |
| Know scaling strategies | ✅ |
| Can handle edge cases | ✅ |
| Ready for interview | ✅ |

**Ready for your interview? Let's go! 🚀**
