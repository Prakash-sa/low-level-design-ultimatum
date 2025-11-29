# Amazon Online Shopping System - 75 Minute Interview Guide

> **Complete System Design** | Production-Grade Implementation | All Design Patterns | 12 Interview Q&A

**Timeline**: 75 minutes | **Scale**: 100K+ concurrent users, 1M+ products | **Challenge**: Cart reservation, inventory management, state transitions

---

## Table of Contents
1. [Requirements Clarification (0-5 min)](#requirements-clarification-0-5-min)
2. [Architecture & Design (5-15 min)](#architecture--design-5-15-min)
3. [Core Entities (15-35 min)](#core-entities-15-35-min)
4. [Business Logic & Patterns (35-55 min)](#business-logic--patterns-35-55-min)
5. [System Integration (55-70 min)](#system-integration-55-70-min)
6. [Demo & Q&A (70-75 min)](#demo--qa-70-75-min)

---

## Requirements Clarification (0-5 min)

**Problem Statement**: Design Amazon's online shopping system that handles product catalog, shopping cart, checkout, orders, and notifications.

**Functional Requirements**:
- Browse and search products (by category, price, rating)
- Add/remove items from shopping cart
- Apply different pricing strategies (regular, bulk, membership)
- Checkout and create orders
- Track order status (PENDING → CONFIRMED → SHIPPED → DELIVERED)
- Receive notifications (email, SMS, push)
- Cancel orders before shipment

**Non-Functional Requirements**:
- Support 100K+ concurrent users
- Manage 1M+ products without slowdown
- Thread-safe cart operations (prevent double-booking)
- Fast search with multiple filters
- Real-time order status updates

**Core Entities**:
- Product (catalog, inventory, ratings)
- ShoppingCart (user items, temporary reservations)
- Order (confirmed purchase, state tracking)
- User (customer profile, order history)
- CartItem (product + quantity in cart)

**Key Challenges**:
1. **Inventory Management**: Prevent overselling (reserve during cart, lock during checkout)
2. **Cart Stability**: Items can go out-of-stock while in cart → graceful removal
3. **Concurrency**: 100K users adding items simultaneously → atomic operations
4. **Price Calculation**: Different strategies (bulk discount, membership) → pluggable pricing
5. **Order Lifecycle**: Clear state transitions with validation

---

## Architecture & Design (5-15 min)

### System Architecture

```
┌─────────────────────────────────────┐
│     AMAZON SHOPPING SYSTEM          │
│        (Singleton)                  │
├─────────────────────────────────────┤
│                                     │
│  Responsibilities:                  │
│  • Manage products & inventory       │
│  • Handle shopping carts             │
│  • Process checkouts                 │
│  • Track orders                      │
│  • Send notifications                │
│                                     │
└─────────────────────────────────────┘
```

### Design Patterns Applied

| Pattern | Purpose | Benefit |
|---------|---------|---------|
| **Singleton** | Single system instance | Thread-safe, consistent state |
| **Strategy (Pricing)** | Different pricing models | Add new strategies without modifying core |
| **Strategy (Search)** | Pluggable filters | Chainable category/price/rating filters |
| **Observer** | Decouple notifications | Email/SMS/Push independently |
| **State (Order)** | Order lifecycle | Prevent invalid state transitions |

### Key Design Decisions

1. **Cart Reservations**: Items reserved at checkout, released if order fails
2. **Product Inventory**: Decremented on reservation, not on cart-add (prevents lost inventory)
3. **Pricing Strategy**: Switch strategies at checkout (regular → bulk → membership)
4. **Thread Safety**: Singleton with locks for concurrent cart access
5. **Notifications**: Observer pattern fires on order events, not cart events

---

## Core Entities (15-35 min)

### 1. Enumerations (State & Categories)

```python
class ProductCategory(Enum):
    ELECTRONICS = "electronics"
    BOOKS = "books"
    CLOTHING = "clothing"
    HOME = "home"
    SPORTS = "sports"

class ProductStatus(Enum):
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class OrderStatus(Enum):
    PENDING = "pending"          # Just placed
    CONFIRMED = "confirmed"      # Payment received
    SHIPPED = "shipped"          # Left warehouse
    DELIVERED = "delivered"      # At doorstep
    CANCELLED = "cancelled"      # Order cancelled
```

### 2. Product Entity

```python
class Product:
    """Represents catalog product with inventory & reviews"""
    def __init__(self, product_id, name, category, price, quantity_available):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.quantity_available = quantity_available  # Available inventory
        self.status = ProductStatus.AVAILABLE
        self.rating = 0.0
        self.reviews = []
    
    def is_available(self, qty: int) -> bool:
        """Check if qty items available"""
        return (self.status == ProductStatus.AVAILABLE and 
                self.quantity_available >= qty)
    
    def reserve(self, qty: int) -> bool:
        """Reserve items for checkout (atomically decrease inventory)"""
        if self.is_available(qty):
            self.quantity_available -= qty
            return True
        return False
    
    def release(self, qty: int):
        """Release items if order cancelled"""
        self.quantity_available += qty
    
    def add_review(self, rating: float, comment: str):
        """Add customer review and update rating"""
        self.reviews.append({"rating": rating, "comment": comment})
        self.rating = sum(r["rating"] for r in self.reviews) / len(self.reviews)
```

**Key Methods**:
- `is_available()`: Check inventory before adding to cart
- `reserve()`: Atomically decrease when checkout confirmed
- `release()`: Increase if order cancelled

### 3. CartItem Entity

```python
class CartItem:
    """Represents product + quantity in user's cart"""
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.status = CartItemStatus.ADDED
        self.added_at = datetime.now()
    
    def get_total_price(self) -> float:
        """Calculate item total (used by cart)"""
        return self.product.price * self.quantity
    
    def reserve(self) -> bool:
        """Reserve from inventory during checkout"""
        if self.product.reserve(self.quantity):
            self.status = CartItemStatus.RESERVED
            return True
        return False
    
    def release(self):
        """Release to inventory if order fails"""
        self.product.release(self.quantity)
        self.status = CartItemStatus.REMOVED
```

### 4. ShoppingCart Entity

```python
class ShoppingCart:
    """User's temporary cart with items"""
    def __init__(self, user_id: str):
        self.cart_id = str(uuid.uuid4())[:8]
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}
        self.created_at = datetime.now()
    
    def add_item(self, product: Product, quantity: int) -> bool:
        """Add/increase item in cart (no inventory deduction yet)"""
        if not product.is_available(quantity):
            return False  # Not available
        
        if product.product_id in self.items:
            self.items[product.product_id].quantity += quantity
        else:
            self.items[product.product_id] = CartItem(product, quantity)
        return True
    
    def remove_item(self, product_id: str) -> bool:
        """Remove item from cart"""
        if product_id in self.items:
            self.items[product_id].release()
            del self.items[product_id]
            return True
        return False
    
    def get_total_price(self) -> float:
        """Sum all items (before pricing strategy applied)"""
        return sum(item.get_total_price() for item in self.items.values())
    
    def get_item_count(self) -> int:
        """Total quantity of items"""
        return sum(item.quantity for item in self.items.values())
    
    def clear(self):
        """Clear cart and release all items"""
        for item in self.items.values():
            item.release()
        self.items.clear()
```

### 5. Order Entity

```python
class Order:
    """Confirmed purchase with lifecycle"""
    def __init__(self, order_id, user_id, items, total_price):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items  # Dict of CartItems
        self.total_price = total_price
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.tracking_number: Optional[str] = None
    
    def confirm(self) -> bool:
        """Transition: PENDING → CONFIRMED (payment received)"""
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
            return True
        return False
    
    def ship(self, tracking_number: str) -> bool:
        """Transition: CONFIRMED → SHIPPED (left warehouse)"""
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.SHIPPED
            self.tracking_number = tracking_number
            return True
        return False
    
    def deliver(self) -> bool:
        """Transition: SHIPPED → DELIVERED (at customer)"""
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.DELIVERED
            return True
        return False
    
    def cancel(self) -> bool:
        """Transition: PENDING/CONFIRMED → CANCELLED (refund inventory)"""
        if self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            self.status = OrderStatus.CANCELLED
            for item in self.items.values():
                item.release()  # Return items to inventory
            return True
        return False
```

### 6. User Entity

```python
class User:
    """Customer profile"""
    def __init__(self, user_id, name, email, phone):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = UserRole.CUSTOMER
        self.orders: List[Order] = []  # Order history
```

---

## Business Logic & Patterns (35-55 min)

### Pattern 1: Pricing Strategy

**Problem**: Different pricing models (regular, bulk discount, membership) shouldn't require modifying core checkout.

**Solution**: Pluggable strategy interface.

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float, quantity: int) -> float:
        pass

class RegularPricing(PricingStrategy):
    """No discount"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

class BulkPricing(PricingStrategy):
    """10% off for 5+ items"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        if quantity >= 5:
            return base_price * quantity * 0.9
        return base_price * quantity

class MembershipPricing(PricingStrategy):
    """15% off for members"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity * 0.85
```

**Usage in Checkout**:
```python
def checkout(self, user_id):
    cart = self.carts[user_id]
    total = 0
    
    # Apply current strategy
    for item in cart.items.values():
        item_price = self.pricing_strategy.calculate_price(
            item.product.price, 
            item.quantity
        )
        total += item_price
    
    order = Order(..., total_price=total)
```

**Interview Talking Point**: "Strategy pattern lets us add new pricing models (seasonal, regional discounts) without touching core checkout logic."

---

### Pattern 2: Search Filters

**Problem**: Search by category + price + rating simultaneously.

**Solution**: Chainable filter strategies.

```python
class SearchFilter(ABC):
    @abstractmethod
    def filter(self, products: List[Product]) -> List[Product]:
        pass

class CategoryFilter(SearchFilter):
    def __init__(self, category: ProductCategory):
        self.category = category
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products if p.category == self.category]

class PriceFilter(SearchFilter):
    def __init__(self, min_price, max_price):
        self.min_price = min_price
        self.max_price = max_price
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products 
                if self.min_price <= p.price <= self.max_price]

class RatingFilter(SearchFilter):
    def __init__(self, min_rating: float):
        self.min_rating = min_rating
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products if p.rating >= self.min_rating]
```

**Usage**:
```python
filters = [
    CategoryFilter(ProductCategory.ELECTRONICS),
    PriceFilter(500, 1500),
    RatingFilter(4.0)
]
results = system.search_products(filters)  # Electronics, $500-1500, 4+ stars
```

---

### Pattern 3: Observer (Notifications)

**Problem**: Notify users via email/SMS/push without coupling order logic to each channel.

**Solution**: Observer pattern with multiple notifiers.

```python
class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event: str, order: Order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event: str, order: Order):
        print(f"[EMAIL] Order {order.order_id}: {event}")
        # Actually send email...

class SMSNotifier(OrderObserver):
    def notify(self, event: str, order: Order):
        print(f"[SMS] Order {order.order_id}: {event}")
        # Actually send SMS...

class PushNotifier(OrderObserver):
    def notify(self, event: str, order: Order):
        print(f"[PUSH] Order {order.order_id}: {event}")
        # Actually send push...
```

**Integration**:
```python
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())
system.add_observer(PushNotifier())

# When order placed:
system.notify_all("ORDER_PLACED", order)  # Fires all 3 notifiers
```

---

### Pattern 4: Singleton (System Controller)

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
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.products = {}
            self.users = {}
            self.carts = {}
            self.orders = {}
            self.observers = []
            self.pricing_strategy = RegularPricing()
            self.initialized = True
```

**Why**: Single instance ensures all users share same product inventory and order tracking.

---

## System Integration (55-70 min)

### ShoppingSystem Core Methods

```python
class ShoppingSystem:
    # Search
    def search_products(self, filters: List[SearchFilter]) -> List[Product]:
        results = list(self.products.values())
        for filter_obj in filters:
            results = filter_obj.filter(results)
        return results
    
    # Cart Management
    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> bool:
        cart = self.get_or_create_cart(user_id)
        product = self.products[product_id]
        return cart.add_item(product, quantity)
    
    def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        cart = self.carts.get(user_id)
        return cart.remove_item(product_id) if cart else False
    
    # Checkout (Complex - Multiple Steps)
    def checkout(self, user_id: str) -> Optional[Order]:
        cart = self.carts.get(user_id)
        if not cart or not cart.items:
            return None
        
        # Step 1: Calculate total with current pricing strategy
        total_price = 0
        for item in cart.items.values():
            item_price = self.pricing_strategy.calculate_price(
                item.product.price,
                item.quantity
            )
            total_price += item_price
        
        # Step 2: Create order
        order_id = str(uuid.uuid4())[:8]
        order = Order(order_id, user_id, dict(cart.items), total_price)
        
        # Step 3: Reserve all items (atomic operation)
        for item in cart.items.values():
            if not item.reserve():
                # ROLLBACK: Release all previously reserved items
                for prev_item in cart.items.values():
                    if prev_item.status == CartItemStatus.RESERVED:
                        prev_item.release()
                return None
        
        # Step 4: Save order and notify
        self.orders[order_id] = order
        user = self.users.get(user_id)
        if user:
            user.orders.append(order)
        
        self.notify_all("ORDER_PLACED", order)
        return order
    
    # Order Lifecycle
    def confirm_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.confirm():
            self.notify_all("ORDER_CONFIRMED", order)
            return True
        return False
    
    def ship_order(self, order_id: str, tracking_number: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.ship(tracking_number):
            self.notify_all("ORDER_SHIPPED", order)
            return True
        return False
    
    def deliver_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.deliver():
            self.notify_all("ORDER_DELIVERED", order)
            return True
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.cancel():
            self.notify_all("ORDER_CANCELLED", order)
            return True
        return False
```

### Edge Cases & Thread Safety

**Issue 1: Item added to cart, then goes out of stock**
- *Solution*: `add_item()` checks `is_available()` → returns False → item not added

**Issue 2: Two users trying to checkout with last item**
- *Solution*: Reservation happens at checkout. First checkout reserves. Second checkout's `item.reserve()` fails → entire order fails → rollback

**Issue 3: 100K concurrent cart operations**
- *Solution*: Singleton with `threading.Lock()` in `__new__()`. Only one ShoppingSystem instance created.

---

## Demo & Q&A (70-75 min)

### 5 Demo Scenarios

**Demo 1**: System setup with products and users  
**Demo 2**: Search with multiple filters  
**Demo 3**: Add/remove items from cart  
**Demo 4**: Different pricing strategies (regular vs bulk)  
**Demo 5**: Complete order lifecycle (place → confirm → ship → deliver)

**Run**:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## 12 Interview Questions & Answers

### Basic Level

**Q1: How does the shopping cart prevent double-booking?**
- Cart only adds items, doesn't reserve inventory
- Reservation happens atomically during checkout
- If reservation fails, entire order fails and items are released back

**Q2: What's the difference between CartItem status and Order status?**
- CartItem: ADDED → RESERVED → REMOVED (lifecycle in cart)
- Order: PENDING → CONFIRMED → SHIPPED → DELIVERED (lifecycle after checkout)
- CartItem reflects cart state; Order reflects purchase state

**Q3: Why use Strategy pattern for pricing?**
- Allows different pricing models (regular, bulk, membership) to coexist
- Add new pricing strategy without modifying checkout logic
- Strategy switched at checkout time, not hardcoded

---

### Intermediate Level

**Q4: How does checkout handle concurrent inventory?**
- Reserve inventory atomically in checkout
- Entire operation inside threading lock (Singleton)
- First checkout reserves, second checkout sees no inventory → fails gracefully

**Q5: How do search filters work?**
- Each filter is a strategy (CategoryFilter, PriceFilter, RatingFilter)
- Filters chain together, each reducing results
- Category filter → Price filter → Rating filter = final results

**Q6: What happens if an order is cancelled after shipment?**
- Cancel method checks order status
- Only allows cancel if PENDING or CONFIRMED
- SHIPPED/DELIVERED cannot be cancelled
- Prevents refunding already-in-transit orders

---

### Advanced Level

**Q7: How would you handle product inventory sync across multiple data centers?**
- Each DC has local cache of product inventory
- Central DB is source of truth
- On checkout, lock product inventory in central DB
- Eventually consistent model for reads, strong consistent for writes

**Q8: How would you scale to 1M+ products?**
- Partition products by category
- Use search index (Elasticsearch) for fast filtering
- Cache popular products in memory
- Lazy-load product details on demand

**Q9: How would you handle abandoned carts?**
- Add `last_modified` timestamp to cart
- Background job clears carts older than 24 hours
- Release reserved items back to inventory
- Email user: "Your cart is expiring"

**Q10: What if a product is delisted while in user's cart?**
- Check product status on checkout
- If DISCONTINUED, remove from cart automatically
- Notify user "Item {X} is no longer available"
- Adjust checkout total accordingly

**Q11: How would you prevent users from gaming bulk pricing?**
- Enforce bulk pricing only for same product
- Don't allow splitting across multiple carts/users
- Track bulk pricing by user + session
- Backend validation, not frontend

**Q12: How does the system handle peak traffic (holiday sales)?**
- Singleton pattern ensures single source of truth
- Threading locks make operations thread-safe
- Horizontal scaling: multiple ShoppingSystem replicas behind load balancer
- Use database transactions for atomic checkout

---

## ASCII UML Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    SHOPPING SYSTEM                           │
│                    (Singleton)                               │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐
    │ Product │ │  User   │ │  Order   │
    │ (1M+)   │ │ (100K+) │ │(tracking)│
    └─────────┘ └─────────┘ └──────────┘
        │           │           │
        │ HAS-A     │ HAS-A     │ HAS-A
        │           │           │
        ▼           ▼           ▼
    ┌────────────────────────────────┐
    │      ShoppingCart              │
    │  • items[]                      │
    │  • add_item()                   │
    │  • remove_item()                │
    │  • get_total_price()            │
    └────────────────────────────────┘
           │
           │ CONTAINS
           │
           ▼
    ┌────────────────────────────────┐
    │      CartItem                  │
    │  • product                      │
    │  • quantity                     │
    │  • status (ADDED/RESERVED)      │
    │  • reserve()                    │
    │  • release()                    │
    └────────────────────────────────┘
           │
           │ REFERENCES
           │
           ▼
    ┌────────────────────────────────┐
    │    SearchFilter                │
    │  (Abstract)                     │
    │  • CategoryFilter               │
    │  • PriceFilter                  │
    │  • RatingFilter                 │
    └────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│         PRICING STRATEGY (Abstract)                    │
│  • calculate_price(base_price, qty)                    │
├────────────────────────────────────────────────────────┤
│  • RegularPricing                                      │
│  • BulkPricing (10% off for 5+)                       │
│  • MembershipPricing (15% off)                        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│        ORDER OBSERVER (Abstract)                       │
│  • notify(event, order)                                │
├────────────────────────────────────────────────────────┤
│  • EmailNotifier                                       │
│  • SMSNotifier                                         │
│  • PushNotifier                                        │
└────────────────────────────────────────────────────────┘
```

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|-----------------|
| **S** | Each class: Product manages inventory, Order manages lifecycle, ShoppingCart manages items |
| **O** | Open to new pricing strategies/filters/notifiers without modifying core |
| **L** | All strategies/filters/notifiers are interchangeable implementations |
| **I** | Minimal interfaces (PricingStrategy, SearchFilter, OrderObserver) |
| **D** | Depend on abstractions (Strategy, Filter, Observer) not concrete classes |

---

## Interview Success Checklist

✅ Can explain 5 design patterns (Singleton, Strategy x2, Observer, State)  
✅ Can draw entity relationships (Product, Cart, CartItem, Order)  
✅ Can explain thread-safety mechanisms (Singleton with locks)  
✅ Can handle edge cases (concurrent checkout, inventory sync, abandoned carts)  
✅ Can explain scaling strategy (horizontal scaling with shared DB)  
✅ Can discuss trade-offs (eventual consistency vs strong consistency)  
✅ Ran demo successfully and explained output  
✅ SOLID principles demonstrated in code

---

*For 5-minute quick reference, see START_HERE.md | For running code, see INTERVIEW_COMPACT.py | For overview, see README.md*
