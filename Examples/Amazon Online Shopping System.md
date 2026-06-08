# Amazon Online Shopping System — Complete Design Guide

> E-commerce platform for browsing, cart management, checkout, order tracking, and notifications.

**Scale**: 100K+ concurrent users, 1M+ products, 24/7 uptime, peak: 10K TPS  
**Duration**: 75-minute interview guide  
**Focus**: Inventory management, cart operations, checkout flow, state transitions

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
Users browse products → add to cart (no inventory deduction) → checkout (reserve inventory atomically) → place order → receive notifications → track shipment.

### Core Flow
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

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system with 100K+ concurrent users"
2. **Do we track order history per user?** → "Yes, past orders for tracking and cancellations"
3. **Multi-seller or single seller?** → "Single seller (Amazon-operated inventory)"
4. **Real payment processing?** → "Assume external payment gateway — out of scope"
5. **Cancellations after shipment?** → "No — only before shipment (PENDING or CONFIRMED)"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Browse & purchase | Search products, add to cart, checkout, track order |
| **System Admin** | Manage catalog & inventory | Add products, update stock, set pricing strategy |
| **System** | Controller & notifications | Reserve inventory, send emails/SMS, update order status |

### Functional Requirements (What does the system do?)

✅ **Browse & Search**
  - Search products by category, price range, and rating
  - View real-time product availability

✅ **Cart Management**
  - Add/remove items from shopping cart
  - View cart total; no inventory deduction at add-time

✅ **Pricing**
  - Apply different pricing strategies (regular, bulk 10% off for 5+, membership 15% off)
  - Switch pricing strategy at runtime

✅ **Checkout**
  - Atomic inventory reservation: all items succeed or none reserved
  - Create order on successful reservation, clear cart

✅ **Order Lifecycle**
  - Track order through PENDING → CONFIRMED → SHIPPED → DELIVERED
  - Cancel order only before shipment

✅ **Notifications**
  - Notify on order placed, status change, cancellation
  - Support multiple channels (email, SMS, push)

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 100K+ simultaneous users  
✅ **Consistency**: No double-selling (atomic inventory reservation)  
✅ **Latency**: <100ms search response time, <500ms checkout response time  
✅ **Availability**: 99.9% uptime  
✅ **Accuracy**: Accurate real-time inventory tracking  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES — multi-region with replicas |
| **Payment processing?** | NO — assume external gateway |
| **Returns/refunds?** | OUT OF SCOPE |
| **Seller portal?** | OUT OF SCOPE |
| **Cancel after ship?** | NO — only PENDING or CONFIRMED orders |
| **Cart expiry?** | 24-hour TTL; background cleanup job |
| **Inventory deduction on add-to-cart?** | NO — only on checkout |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
User, Product, Catalog, Cart, CartItem, Order, Payment, Inventory, ShoppingSystem, ...
```

### Step 2.2: Define Core Classes

#### **User** — A registered customer
```
Properties:
  - user_id: str
  - name: str
  - email: str
  - phone: str
  - orders: List[Order]

Behaviors:
  - (data holder; orders appended on checkout)
```

#### **Product** — A single item for sale
```
Properties:
  - product_id: str
  - name: str
  - category: ProductCategory
  - price: float
  - quantity_available: int
  - rating: float
  - reviews: List

Behaviors:
  - is_available(qty): Check if stock is sufficient
  - reserve(qty): Deduct stock atomically
  - release(qty): Return stock on cancellation/rollback
```

#### **CartItem** — A product + quantity in a user's cart
```
Properties:
  - product: Product
  - quantity: int
  - status: CartItemStatus (ADDED / RESERVED / PURCHASED / REMOVED)

Behaviors:
  - get_total_price(): product.price × quantity
  - reserve(): call product.reserve(), update status → RESERVED
  - release(): call product.release(), update status → REMOVED
```

#### **ShoppingCart** — Per-user temporary item collection
```
Properties:
  - cart_id: str
  - user_id: str
  - items: Dict[product_id, CartItem]

Behaviors:
  - add_item(product, quantity): check availability, add/update CartItem
  - remove_item(product_id): remove CartItem
  - get_total_price(): sum of all CartItem totals
  - clear(): release all reserved items, empty dict
```

#### **Order** — A confirmed purchase
```
Properties:
  - order_id: str
  - user_id: str
  - items: Dict[product_id, CartItem]
  - total_price: float
  - status: OrderStatus
  - created_at: datetime
  - tracking_number: Optional[str]

Behaviors:
  - confirm(): PENDING → CONFIRMED
  - ship(tracking_number): CONFIRMED → SHIPPED
  - deliver(): SHIPPED → DELIVERED
  - cancel(): PENDING|CONFIRMED → CANCELLED, release inventory
```

#### **ShoppingSystem** — Main controller (Singleton)
```
Properties:
  - products: Dict[str, Product]
  - users: Dict[str, User]
  - carts: Dict[user_id, ShoppingCart]
  - orders: Dict[str, Order]
  - observers: List[OrderObserver]
  - pricing_strategy: PricingStrategy

Behaviors:
  - add_product(...): register product in catalog
  - register_user(...): register user
  - search_products(filters): chain filter strategies over products
  - add_to_cart(user_id, product_id, quantity): delegate to cart
  - checkout(user_id): atomic reserve + create order + notify
  - add_observer(observer): register notifier
  - notify_all(event, order): broadcast to all observers
  - set_pricing_strategy(strategy): swap algorithm
```

### Step 2.3: Define Enumerations (State & Type)

```python
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
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **User** | Track identity and purchase history | Can't associate orders or send notifications |
| **Product** | Catalog item with stock tracking | No inventory management |
| **CartItem** | Product + quantity + status in cart | Can't distinguish reserved vs added state |
| **ShoppingCart** | Per-user temporary collection | No separation between browsing and checkout |
| **Order** | Permanent purchase record with lifecycle | No order tracking or cancellation |
| **ShoppingSystem** | Thread-safe central coordinator | No atomic operations across inventory |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Add Product**
```python
def add_product(name: str, category: ProductCategory, price: float, quantity: int) -> Product:
    """
    Register a new product in the catalog.
    Returns: Product with generated product_id.
    Response Time: <50ms
    """
    pass
```

#### **2. Register User**
```python
def register_user(name: str, email: str, phone: str) -> User:
    """
    Register a new customer.
    Returns: User with generated user_id.
    """
    pass
```

#### **3. Search Products**
```python
def search_products(filters: List[SearchFilter]) -> List[Product]:
    """
    Chain multiple filter strategies over the product catalog.
    Returns: Filtered list of Products.
    Response Time: <100ms (cached in production via Elasticsearch)
    """
    pass
```

#### **4. Add to Cart**
```python
def add_to_cart(user_id: str, product_id: str, quantity: int) -> bool:
    """
    Add a product to the user's cart. Does NOT deduct inventory.
    Returns: True if item added, False if product not found.
    Note: Availability checked at checkout, not here.
    """
    pass
```

#### **5. Checkout** ⭐ CRITICAL
```python
def checkout(user_id: str) -> Optional[Order]:
    """
    Atomically reserve all cart items, create order, clear cart.

    Precondition: user has non-empty cart
    Postcondition: all products.quantity_available decremented, Order created

    Returns: Order if successful, None if any item out of stock.

    Raises:
      - No order created if ANY reservation fails (full rollback)

    Concurrency: THREAD-SAFE with threading.RLock
    Response Time: <500ms
    Side Effects: Notifies all observers with ORDER_PLACED event
    """
    pass
```

#### **6. Set Pricing Strategy**
```python
def set_pricing_strategy(strategy: PricingStrategy) -> None:
    """
    Dynamically switch pricing algorithm.
    New pricing applies to the next checkout() call.
    Strategy options: RegularPricing, BulkPricing, MembershipPricing
    """
    pass
```

#### **7. Register Observer**
```python
def add_observer(observer: OrderObserver) -> None:
    """
    Register a notification listener for order events.
    Events fired: "ORDER_PLACED", status transitions, cancellations.
    Observer called: observer.notify(event, order)
    """
    pass
```

### Step 3.2: Failure Model

| Scenario | Behavior |
|----------|----------|
| Product not found in add_to_cart | Return False |
| Cart empty at checkout | Return None |
| Any item out of stock at checkout | Full rollback, return None |
| Order cancel after shipment | Raise / return False |

### Step 3.3: API Usage Example

```python
system = ShoppingSystem()

# 1. Setup catalog
p1 = system.add_product("Laptop", ProductCategory.ELECTRONICS, 999.99, 5)
p2 = system.add_product("Book", ProductCategory.BOOKS, 49.99, 20)
user = system.register_user("Alice", "alice@example.com", "555-1234")

# 2. Search
results = system.search_products([
    CategoryFilter(ProductCategory.ELECTRONICS),
    PriceFilter(500, 1500)
])

# 3. Cart
system.add_to_cart(user.user_id, p1.product_id, 1)
system.add_to_cart(user.user_id, p2.product_id, 2)

# 4. Checkout
system.add_observer(EmailNotifier())
order = system.checkout(user.user_id)
print(f"Order: {order.order_id}, Total: ${order.total_price:.2f}")

# 5. Order lifecycle
order.confirm()
order.ship("TRK123456")
order.deliver()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
ShoppingSystem HAS-A products (1:N Composition)
  └─ ShoppingSystem owns and manages product catalog lifecycle

ShoppingSystem HAS-A carts (1:N Composition)
  └─ Per-user ShoppingCart objects owned by system

ShoppingCart HAS-A CartItems (0..N Composition)
  └─ Cart owns the collection of CartItem objects

CartItem REFERENCES Product (1:1 Association)
  └─ CartItem links to Product (no ownership)

Order CONTAINS CartItems (1..N Composition)
  └─ Snapshot of cart items at checkout

Order OWNED-BY User (N:1 Association)
  └─ Multiple orders per user

ShoppingSystem USES-A PricingStrategy (1:1 Composition)
  └─ Pluggable pricing algorithm

ShoppingSystem NOTIFIES OrderObserver (1:N Association)
  └─ Multiple observers listen to order events
```

### Step 4.2: Complete UML Class Diagram

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

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| ShoppingSystem → Products | 1:N | Composition | System owns catalog |
| ShoppingSystem → Carts | 1:N | Composition | Per-user carts owned by system |
| ShoppingCart → CartItems | 0..N | Composition | Cart owns its item collection |
| CartItem → Product | 1:1 | Association | CartItem references product (no ownership) |
| Order → CartItems | 1..N | Composition | Order snapshot owns items |
| Order → User | N:1 | Association | Many orders belong to one user |
| ShoppingSystem → PricingStrategy | 1:1 | Composition | System owns pricing algorithm |
| ShoppingSystem → OrderObserver | 1:N | Association | System notifies multiple listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only apply them when they solve a specific problem.

### Pattern 1: **Singleton** (For ShoppingSystem)

**Problem**: 100K users accessing shopping system concurrently → race conditions on shared inventory.

**Solution**: Single ShoppingSystem instance with thread-safe initialization and RLock.

```python
class ShoppingSystem:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked locking), ✅ Global access  
**Trade-off**: ⚠️ Global state (hard to unit-test), ⚠️ Requires distributed locks across replicas

---

### Pattern 2: **Strategy** (For Pricing)

**Problem**: Different pricing models (regular, bulk 10% off for 5+, membership 15% off) need different logic.

**Solution**: Pluggable pricing strategies — swap without modifying checkout logic.

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

**Benefit**: ✅ Easy to add new strategies (seasonal, regional) without touching checkout  
**Trade-off**: ⚠️ Extra abstraction layer for simple cases

---

### Pattern 3: **Strategy** (For Search Filters)

**Problem**: Search by category + price + rating simultaneously without nested loops.

**Solution**: Chainable filter strategies — each filter is independent and composable.

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

**Benefit**: ✅ Each filter independent, composable, no coupling  
**Trade-off**: ⚠️ O(n) per filter; production would use Elasticsearch shards

---

### Pattern 4: **Observer** (For Notifications)

**Problem**: System shouldn't know about Email/SMS/Push implementation details.

**Solution**: Abstract Observer interface, pluggable notifiers decoupled from order logic.

```python
class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event, order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event, order):
        print(f"Email: Order {order.order_id} - {event}")

# Add notifiers
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())

# All fire on event
system.notify_all("ORDER_PLACED", order)
```

**Benefit**: ✅ Add SlackNotifier without touching core system  
**Trade-off**: ⚠️ Observer lifecycle management; fire-and-forget (no retry)

---

### Pattern 5: **State** (For Order Lifecycle)

**Problem**: Orders have valid transitions (PENDING → SHIPPED) and invalid ones (DELIVERED → PENDING).

**Solution**: Enum-based state with guard validation in each transition method.

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
            raise ValueError("Can only ship a CONFIRMED order")
        self.status = OrderStatus.SHIPPED
```

**Benefit**: ✅ Invalid transitions caught at runtime, explicit lifecycle  
**Trade-off**: ⚠️ Transition logic spread across methods; full State pattern would centralise it

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single consistent ShoppingSystem state | Thread-safe global coordinator |
| **Strategy (Pricing)** | Multiple pricing models (regular/bulk/membership) | Pluggable, easy to extend |
| **Strategy (Search)** | Category/price/rating filtering without nested loops | Composable, independent filters |
| **Observer** | Email/SMS/Push notifications decoupled from orders | Loose coupling, event-driven |
| **State (Enum)** | Valid order transitions enforced | Invalid transitions prevented at runtime |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
import uuid
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


# ============ ENUMERATIONS ============

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


# ============ CORE ENTITIES ============

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


# ============ STRATEGIES ============

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

class RatingFilter(SearchFilter):
    def __init__(self, min_rating):
        self.min_rating = min_rating

    def filter(self, products):
        return [p for p in products if p.rating >= self.min_rating]


# ============ OBSERVERS ============

class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event, order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event, order):
        print(f"  [Email] Order {order.order_id} - {event}")

class SMSNotifier(OrderObserver):
    def notify(self, event, order):
        print(f"  [SMS]   Order {order.order_id} - {event}")


# ============ SINGLETON CONTROLLER ============

class ShoppingSystem:
    _instance = None
    # Use RLock so checkout (which holds the lock) can call notify_all safely
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.products: Dict[str, Product] = {}
        self.users: Dict[str, User] = {}
        self.carts: Dict[str, ShoppingCart] = {}
        self.orders: Dict[str, Order] = {}
        self.observers: List[OrderObserver] = []
        self.pricing_strategy: PricingStrategy = RegularPricing()
        self._initialized = True

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

            reserved = []
            for item in cart.items.values():
                if not item.reserve():
                    # Rollback all previously reserved items
                    for r in reserved:
                        r.release()
                    return None
                reserved.append(item)

            order_id = str(uuid.uuid4())[:8]
            total = 0
            for item in cart.items.values():
                total += self.pricing_strategy.calculate_price(
                    item.product.price, item.quantity
                )

            order = Order(order_id, user_id, dict(cart.items), total)
            self.orders[order_id] = order
            self.notify_all("ORDER_PLACED", order)
            cart.items.clear()
            if user_id in self.carts:
                del self.carts[user_id]
            return order

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_all(self, event, order):
        for observer in self.observers:
            observer.notify(event, order)

    def set_pricing_strategy(self, strategy):
        self.pricing_strategy = strategy


# ============ DEMO ============

if __name__ == "__main__":
    # Reset singleton state for clean demo run
    ShoppingSystem._instance = None

    print("=" * 70)
    print("AMAZON SHOPPING SYSTEM - COMPLETE DEMO")
    print("=" * 70)

    system = ShoppingSystem()
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())

    p1 = system.add_product("Laptop", ProductCategory.ELECTRONICS, 999.99, 5)
    p2 = system.add_product("Book", ProductCategory.BOOKS, 49.99, 20)
    p3 = system.add_product("T-Shirt", ProductCategory.CLOTHING, 19.99, 100)

    user1 = system.register_user("Alice", "alice@email.com", "555-1234")
    user2 = system.register_user("Bob", "bob@email.com", "555-5678")

    print(f"\n[Setup] Products: {len(system.products)}, Users: {len(system.users)}")

    # Search
    print("\n[Demo 1] Search Electronics")
    filters = [CategoryFilter(ProductCategory.ELECTRONICS)]
    results = system.search_products(filters)
    print(f"  Electronics found: {len(results)}")

    # Add to cart and checkout with regular pricing
    print("\n[Demo 2] Cart & Checkout (Regular Pricing)")
    system.add_to_cart(user1.user_id, p1.product_id, 1)
    system.add_to_cart(user1.user_id, p2.product_id, 2)
    cart = system.carts[user1.user_id]
    print(f"  Cart items: {len(cart.items)}, Total: ${cart.get_total_price():.2f}")
    order1 = system.checkout(user1.user_id)
    if order1:
        print(f"  Order created: {order1.order_id}, Total: ${order1.total_price:.2f}")

    # Bulk pricing
    print("\n[Demo 3] Bulk Pricing (10% off for 5+ qty)")
    system.set_pricing_strategy(BulkPricing())
    for _ in range(5):
        system.add_to_cart(user2.user_id, p3.product_id, 1)
    order2 = system.checkout(user2.user_id)
    if order2:
        print(f"  Order created: {order2.order_id}, Total: ${order2.total_price:.2f}")

    # Order lifecycle
    print("\n[Demo 4] Order Lifecycle")
    if order1:
        print(f"  Status: {order1.status.value}")
        order1.confirm()
        print(f"  After confirm: {order1.status.value}")
        order1.ship("TRK-9876")
        print(f"  After ship: {order1.status.value}, Tracking: {order1.tracking_number}")
        order1.deliver()
        print(f"  After deliver: {order1.status.value}")

    # Cancellation
    print("\n[Demo 5] Order Cancellation")
    system.set_pricing_strategy(RegularPricing())
    system.add_to_cart(user1.user_id, p2.product_id, 1)
    order3 = system.checkout(user1.user_id)
    if order3:
        print(f"  Order: {order3.order_id}, Status: {order3.status.value}")
        cancelled = order3.cancel()
        print(f"  Cancelled: {cancelled}, Status: {order3.status.value}")
        print(f"  Book stock restored: {p2.quantity_available}")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **checkout** | RLock on ShoppingSystem | Only 1 thread reserves inventory at a time; atomic reserve + create order |
| **Singleton init** | Double-checked RLock | One instance created even under concurrent first-calls |
| **notify_all** | Called inside RLock (reentrant-safe) | Notifications fire without deadlock |
| **cancel (Order)** | Caller should hold lock in distributed system | Local: safe; distributed: needs Redis lock |

**Concurrency Principles**:
1. ✅ RLock (re-entrant) prevents deadlock when checkout calls notify_all within the same lock
2. ✅ Full rollback on partial reservation failure — no partial orders
3. ✅ Double-checked locking for Singleton with `*args, **kwargs` in `__new__`
4. ✅ Minimize lock scope — notify outside lock in production, inside here for simplicity

---

## Demo Scenarios

### Scenario 1: Cart & Checkout (Regular Pricing)

```
[Email] Order <id> - ORDER_PLACED
[SMS]   Order <id> - ORDER_PLACED
  Cart items: 2, Total: $1099.97
  Order created: <id>, Total: $1099.97
```

### Scenario 2: Bulk Pricing (5 T-Shirts)

```
[Email] Order <id> - ORDER_PLACED
[SMS]   Order <id> - ORDER_PLACED
  Order total: $89.96  (5 × $19.99 × 0.9 = 10% off)
```

### Scenario 3: Order Lifecycle

```
Status: pending
After confirm: confirmed
After ship: shipped, Tracking: TRK-9876
After deliver: delivered
```

### Scenario 4: Concurrent Checkout (Last Item)

```
100K users browse Laptop (qty=1)
Two users simultaneously call checkout():
  Thread A: reserves Laptop → Order created
  Thread B: reserve() returns False → rollback → None returned
Result: No double-selling
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you prevent double-booking during concurrent checkouts?**

A: Atomic reservation at checkout:
1. RLock acquired (ShoppingSystem with threading.RLock)
2. For each cart item, attempt to reserve inventory
3. If ANY reservation fails, rollback all previously reserved items and return None
4. Lock released after entire operation

If 2 users both have the last item and checkout simultaneously, only 1 succeeds. The other gets `None` (out of stock).

**Q2: What's the difference between adding to cart and checkout?**

A:
- **Add to Cart**: No inventory change, just check availability snapshot. Item stays in cart even if stock later changes.
- **Checkout**: Atomic operation. Reserve inventory, create order, remove from cart.

This prevents showing "out of stock" immediately when a user adds to cart.

**Q3: Why use Strategy pattern for pricing?**

A: Different pricing models (regular, bulk 10%, membership 15%) can coexist. Add seasonal pricing without modifying checkout logic. Switch strategies at runtime.

**Q4: How do search filters work?**

A: Each filter is an independent strategy. CategoryFilter reduces products to category. PriceFilter narrows by price range. Chain them: 1M products → 10K electronics → 2K under $1500 → 500 rated 4+.

**Q5: How do notifications decouple from orders?**

A: Observer pattern. Order doesn't know about EmailNotifier or SMSNotifier. System fires `notify_all("ORDER_PLACED", order)`. Each observer handles independently. Add SlackNotifier = add one observer.

---

### Intermediate Questions

**Q6: How to handle item going out of stock while in cart?**

A: Check availability at checkout. If item unavailable, entire checkout fails (rollback). Cart unchanged. User gets "Item X out of stock" and can remove item and retry.

**Q7: How to prevent customers from gaming bulk pricing?**

A: Enforce bulk pricing only for same product in a single checkout. Each order calculated separately. Track by order_id, not customer.

**Q8: What if customer loses internet during checkout?**

A: Checkout is atomic inside the lock. Either entire order succeeds or entire order fails. No partial orders. If client loses connection mid-checkout, server finishes the operation and returns success/error.

**Q9: How to handle abandoned carts?**

A: Background job clears carts older than 24 hours, releases any reserved items back to inventory, and emails customer: "Your cart is expiring."

**Q10: How do you track order history?**

A: User object maintains `orders[]` list. When order created, append to `user.orders`. Query `user.orders` for history. Add `created_at` timestamp for sorting.

---

### Advanced Questions

**Q11: Why RLock instead of Lock?**

A: The `checkout` method acquires `_lock` and then calls `notify_all` (which iterates observers). If observers ever needed to call back into ShoppingSystem (e.g., log to the system), a plain `Lock` would deadlock. `RLock` allows the same thread to re-acquire the lock safely.

**Q12: How to handle payment failures during checkout?**

A: Payment is external (out of scope), but if order is created BEFORE payment confirmed:
```
1. Create order (status=PENDING)
2. Call payment service
3. If success: set status=CONFIRMED
4. If failure: set status=CANCELLED, release inventory
Background job monitors PENDING orders > 30 min → auto-cancel
```

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
- Redis for distributed locks (not just threading.RLock)
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

**Problem**: Each ShoppingSystem replica has own threading.RLock. Two users on different replicas can reserve same item.

**Solution**: Distributed lock (Redis)

```python
# Instead of threading.RLock
def checkout(self, user_id):
    with redis_lock.acquire(f"inventory-{product_id}", timeout=5):
        # Reserve inventory
        # Create order
        pass
```

Only 1 replica can checkout per product at a time. Prevents double-booking globally.

---

### Q3: How to sync product inventory across replicas?

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

Each shard handles a subset of products. Parallel search. Fast.

---

### Q7: How to handle cart expiry and cleanup?

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

**Blue-Green Deployment**:

Week 1: Deploy v2 to "blue" environment (isolated)  
Week 2-3: Migrate traffic 10% → 25% → 50% → 100%  
Week 4: All traffic on blue, decommission green  

During migration: Monitor error rates, latency. Rollback if issues.

---

### Q10: How to partition products across multiple regions?

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

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with ShoppingSystem, Product, Cart, CartItem, Order, User
- [ ] Discuss cart vs checkout: no inventory change on add, atomic reserve on checkout
- [ ] Explain how to prevent double-selling with atomic locks and rollback
- [ ] Discuss order lifecycle (PENDING → CONFIRMED → SHIPPED → DELIVERED → CANCELLED)
- [ ] Run complete implementation without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety: Singleton RLock, checkout atomicity, full rollback on failure
- [ ] Discuss 5 design patterns: Singleton, Strategy (pricing), Strategy (search), Observer, State
- [ ] Discuss trade-offs (RLock vs Lock, pessimistic vs optimistic locking, in-memory vs distributed)

---

**Ready for your interview? Add to cart and check out! 🛒**
