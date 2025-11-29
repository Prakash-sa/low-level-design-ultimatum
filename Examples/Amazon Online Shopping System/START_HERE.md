# Amazon Online Shopping System - START HERE (5-Minute Quick Reference)

> **Time-Constrained Interview? Read this in 5 minutes before your interview.**

---

## 1. The Problem (30 seconds)

**Amazon Online Shopping System**: Users browse products → add to cart → checkout → place order → receive notifications → track shipment.

**Your Role**: Design backend to handle 100K concurrent users, 1M+ products, inventory management, and real-time order tracking.

**Scale**: 100K+ concurrent, 1M+ products, 24/7 uptime

---

## 2. System Overview (1 minute)

```
User browsing
    ↓
SEARCH: Filter by category/price/rating (Strategy filters)
    ↓
ADD TO CART: Temporary collection (no inventory deduction)
    ↓
CHECKOUT: 
  1. Calculate price with strategy (regular/bulk/membership)
  2. Reserve inventory atomically
  3. Create order
  4. If reservation fails → rollback
    ↓
CONFIRM & SHIP: Order transitions (PENDING → CONFIRMED → SHIPPED)
    ↓
NOTIFY: Send email/SMS/push to customer (Observer pattern)
    ↓
DELIVER: Final state, customer receives package
```

---

## 3. Five Design Patterns (3 minutes)

### Pattern 1: **SINGLETON** (Consistent State)
**Problem**: Multiple threads accessing shopping system → race conditions  
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

# All users share same instance
system = ShoppingSystem.get_instance()
```

**Interview Talking Point**: "Singleton ensures all 100K users share same product inventory and order tracking. Threading lock makes it thread-safe."

---

### Pattern 2: **STRATEGY (Pricing)** (Pluggable Algorithms)
**Problem**: Different pricing models (regular, bulk, membership) shouldn't require code changes  
**Solution**: Pluggable pricing strategies

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float, quantity: int) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price, qty):
        return base_price * qty  # No discount

class BulkPricing(PricingStrategy):
    def calculate_price(self, base_price, qty):
        return base_price * qty * 0.9 if qty >= 5 else base_price * qty

# Switch at checkout
system.set_pricing_strategy(BulkPricing())
total = strategy.calculate_price(100, 5)  # $450
```

**Interview Talking Point**: "Strategy pattern lets us add new pricing models (seasonal, regional) without touching checkout logic."

---

### Pattern 3: **STRATEGY (Search Filters)** (Composable Filters)
**Problem**: Search by category + price + rating simultaneously  
**Solution**: Chainable filter strategies

```python
class SearchFilter(ABC):
    @abstractmethod
    def filter(self, products: List[Product]) -> List[Product]:
        pass

class CategoryFilter(SearchFilter):
    def filter(self, products):
        return [p for p in products if p.category == self.category]

class PriceFilter(SearchFilter):
    def filter(self, products):
        return [p for p in products if self.min_price <= p.price <= self.max_price]

# Combine filters
filters = [
    CategoryFilter(ProductCategory.ELECTRONICS),
    PriceFilter(500, 1500)
]
results = system.search_products(filters)
```

**Interview Talking Point**: "Each filter is independent strategy. Filters chain together to progressively narrow results."

---

### Pattern 4: **OBSERVER** (Decouple Notifications)
**Problem**: ShoppingSystem shouldn't know about email/SMS/push details  
**Solution**: Observer pattern with pluggable notifiers

```python
class OrderObserver(ABC):
    @abstractmethod
    def notify(self, event: str, order: Order):
        pass

class EmailNotifier(OrderObserver):
    def notify(self, event, order):
        send_email(order.user.email, f"Order {order.id}: {event}")

class SMSNotifier(OrderObserver):
    def notify(self, event, order):
        send_sms(order.user.phone, f"Order {order.id}: {event}")

# Add notifiers
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())

# All notifiers fire on events
system.notify_all("ORDER_PLACED", order)  # Fires email + SMS
```

**Interview Talking Point**: "Observer pattern decouples. ShoppingSystem doesn't care *how* users are notified. Add Slack? Just create SlackNotifier."

---

### Pattern 5: **STATE** (Order Lifecycle)
**Problem**: Orders have valid transitions (PENDING → CONFIRMED) and invalid ones (SHIPPED → PENDING)  
**Solution**: Enum-based state with validation

```python
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order:
    def confirm(self) -> bool:
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
            return True
        return False
    
    def ship(self, tracking) -> bool:
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.SHIPPED
            self.tracking_number = tracking
            return True
        return False
    
    def cancel(self) -> bool:
        if self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            # Release inventory
            for item in self.items.values():
                item.product.release(item.quantity)
            self.status = OrderStatus.CANCELLED
            return True
        return False  # Can't cancel SHIPPED/DELIVERED
```

**Interview Talking Point**: "State pattern prevents invalid transitions. Can't ship a cancelled order because state validation blocks it."

---

## 4. Core Classes Structure (memorize this)

```
ShoppingSystem (Singleton)
├── Product[] (1M+)
│   ├── quantity_available
│   ├── reserve(qty) → decrease inventory
│   └── release(qty) → increase inventory (on cancel)
│
├── User[] (100K+)
│   └── orders[]
│
├── ShoppingCart[user_id]
│   ├── items[]
│   ├── add_item(product, qty)
│   ├── remove_item(product_id)
│   └── checkout()
│
├── CartItem
│   ├── product
│   ├── quantity
│   ├── reserve() → lock inventory
│   └── release() → unlock inventory
│
├── Order[]
│   ├── status (PENDING → CONFIRMED → SHIPPED → DELIVERED)
│   ├── items[]
│   ├── total_price
│   ├── confirm()
│   ├── ship()
│   ├── deliver()
│   └── cancel()
│
├── PricingStrategy (pluggable)
│   ├── RegularPricing
│   ├── BulkPricing (10% off for 5+)
│   └── MembershipPricing (15% off)
│
├── SearchFilter (pluggable)
│   ├── CategoryFilter
│   ├── PriceFilter
│   └── RatingFilter
│
└── OrderObserver (pluggable)
    ├── EmailNotifier
    ├── SMSNotifier
    └── PushNotifier
```

---

## 5. Key Interview Talking Points (1 minute)

### Point 1: **How do you prevent double-booking?**
"Cart adds items without reserving. Reservation happens atomically during checkout. If first checkout reserves last item, second checkout sees no inventory → entire order fails gracefully. Items released back if rollback."

### Point 2: **How do pricing strategies work?**
"Strategy pattern. Each strategy (Regular, Bulk, Membership) implements `calculate_price()`. At checkout, we call current strategy: `strategy.calculate_price(base_price, qty)`. Switch strategies by setting `set_pricing_strategy(new_strategy)`."

### Point 3: **How do search filters work?**
"Each filter is a strategy. CategoryFilter → PriceFilter → RatingFilter. Each takes previous results and narrows them. Chainable = no nested loops."

### Point 4: **How do notifications work?**
"Observer pattern. ShoppingSystem maintains list of observers (EmailNotifier, SMSNotifier). When order event fires, it calls `notify_all('ORDER_PLACED', order)`. Each observer handles it independently. Can add new notifiers without touching core."

### Point 5: **How do you handle concurrent checkouts?**
"Singleton with threading.Lock. Only one ShoppingSystem instance. When 100K users try checkout simultaneously, operations are thread-safe. First user's checkout reserves inventory atomically. Next user sees no inventory."

---

## 6. Quick Demo Commands

```bash
# Change to directory
cd Examples/Amazon\ Online\ Shopping\ System

# Run all 5 demos (2 minutes)
python3 INTERVIEW_COMPACT.py

# Output shows:
# ✅ Demo 1: Catalog created, users registered
# ✅ Demo 2: Search with filters (category/price)
# ✅ Demo 3: Add items, remove items, view cart
# ✅ Demo 4: Regular pricing vs bulk pricing (10% off for 5+)
# ✅ Demo 5: Order lifecycle (place → confirm → ship → deliver)
```

---

## 7. Success Checklist (Before Interview)

- [ ] Can explain Singleton (why + how + threading locks)
- [ ] Can explain Strategy pattern (pricing + filters)
- [ ] Can explain Observer pattern (decouple notifications)
- [ ] Can explain State pattern (valid transitions)
- [ ] Can draw Product → Cart → CartItem → Order relationships
- [ ] Can explain how checkout prevents double-booking
- [ ] Can explain how pricing strategies are applied
- [ ] Can run demo without errors
- [ ] Can answer "Why these patterns?" for each

---

## 8. Emergency Troubleshooting

| Issue | Fix |
|-------|-----|
| "I forgot Singleton" | Single instance, thread-safe, shared state |
| "I don't understand Strategy" | It's interface for multiple implementations. Pricing: regular vs bulk. Filters: category vs price. |
| "How's Observer different from callbacks?" | Observer is cleaner. Subscribers register, get notified automatically. Decouples sender/receiver. |
| "Demo won't run" | `cd` to correct directory, ensure Python 3.8+, run `python3 INTERVIEW_COMPACT.py` |
| "I keep confusing State and Strategy" | **State** = object's condition (PENDING/CONFIRMED), **Strategy** = algorithm choice (pricing/filtering) |

---

## 9. Deep Dive Reference

| Section | File | Time |
|---------|------|------|
| **Complete Code** | 75_MINUTE_GUIDE.md | 20 min read |
| **Working Demo** | INTERVIEW_COMPACT.py | 5 min run |
| **Full Overview** | README.md | 10 min read |
| **12 Q&A** | 75_MINUTE_GUIDE.md (end) | 15 min prep |

---

## 10. Final Reminders

✅ **You have 5 design patterns memorized**  
✅ **You can run the demo**  
✅ **You can explain thread-safety**  
✅ **You can handle edge cases (concurrent checkout, pricing, filters)**  

### During Interview:
1. Start with **high-level architecture** (ShoppingSystem → Product/Cart/Order)
2. Explain **why each pattern** (Singleton for consistency, Strategy for flexibility)
3. **Deep dive on 2-3 patterns** (interviewer will ask specifics)
4. Discuss **edge cases** (double-booking, inventory sync, abandoned carts)
5. Talk **scaling** (100K concurrent, 1M products, caching, search indices)

---

**NOW: Go back to 75_MINUTE_GUIDE.md for Q&A prep!**

*Ready? Let's ace this interview.* 🚀
