# Amazon Online Shopping System - Interview Preparation Guide

> **75-Minute System Design Interview Guide** | Complete Implementation with Design Patterns & Real-world Demo

## Table of Contents
- [System Overview](#system-overview)
- [Core Entities](#core-entities)
- [Design Patterns](#design-patterns)
- [SOLID Principles](#solid-principles)
- [75-Minute Timeline](#75-minute-timeline)
- [Demo Scenarios](#demo-scenarios)
- [Interview Preparation](#interview-preparation)

---

## System Overview

**What**: E-commerce platform for browsing, cart management, checkout, order tracking, and notifications  
**Scale**: 100K+ concurrent users, 1M+ products worldwide  
**Key Challenge**: Inventory management, concurrent checkouts, state transitions  

**Core Operations**:
- Search products (category, price, rating filters)
- Add/remove items from shopping cart
- Apply pricing strategies (regular, bulk, membership)
- Checkout and create orders
- Track order lifecycle (PENDING → SHIPPED → DELIVERED)
- Receive notifications (email, SMS, push)

---

## Core Entities

| Entity | Responsibility | State |
|--------|----------------|-------|
| **Product** | Catalog item with inventory & reviews | AVAILABLE/OUT_OF_STOCK/DISCONTINUED |
| **ShoppingCart** | User's temporary collection of items | Per-user, items can be added/removed |
| **CartItem** | Product + quantity in cart | ADDED → RESERVED → REMOVED |
| **Order** | Confirmed purchase with tracking | PENDING → CONFIRMED → SHIPPED → DELIVERED |
| **User** | Customer profile & order history | Created during registration |
| **ShoppingSystem** | Central controller (Singleton) | Manages all operations thread-safely |

---

## Design Patterns

| Pattern | Usage | Benefits |
|---------|-------|----------|
| **Singleton** | Single ShoppingSystem instance (thread-safe) | Ensures consistent inventory, prevents race conditions |
| **Strategy (Pricing)** | Pluggable price calculations (Regular/Bulk/Membership) | Add new models without modifying checkout |
| **Strategy (Search)** | Pluggable filters (Category/Price/Rating) | Chainable filters, composable search |
| **Observer** | Notify users via Email/SMS/Push on events | Decouple notifications, extensible channels |
| **State** | Order lifecycle (PENDING → SHIPPED) | Clear transitions, prevents invalid states |

### Singleton Pattern Example
```python
# Thread-safe lazy initialization
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

### Strategy Pattern Example (Pricing)
```python
# Pluggable pricing strategies
pricing_strategy = RegularPricing()
price = pricing_strategy.calculate_price(100, 5)  # $500

# Switch at checkout
system.set_pricing_strategy(BulkPricing())
price = pricing_strategy.calculate_price(100, 5)  # $450 (10% off)
```

### Strategy Pattern Example (Search)
```python
# Chainable filters
filters = [
    CategoryFilter(ProductCategory.ELECTRONICS),
    PriceFilter(500, 1500),
    RatingFilter(4.0)
]
results = system.search_products(filters)
```

---

## SOLID Principles

| Principle | Implementation |
|-----------|-----------------|
| **S** (Single Responsibility) | Product manages inventory, Order manages lifecycle, ShoppingCart manages items |
| **O** (Open/Closed) | Open for extension (new strategies/filters), closed for modification |
| **L** (Liskov Substitution) | All strategies/filters/observers interchangeable |
| **I** (Interface Segregation) | Minimal interfaces (PricingStrategy, SearchFilter, OrderObserver) |
| **D** (Dependency Inversion) | Depend on abstractions, not concrete classes |

---

## 75-Minute Timeline

| Time | Section | Topics |
|------|---------|--------|
| **0-5 min** | Requirements Gathering | Scale (100K concurrent), Features (search, cart, checkout, tracking), Constraints |
| **5-15 min** | Architecture Design | Singleton, cart reservations, state transitions, notification system |
| **15-35 min** | Core Entities | Product, ShoppingCart, CartItem, Order, User (with full code) |
| **35-55 min** | Business Logic | Pricing strategies, search filters, observer notifications, checkout logic |
| **55-70 min** | Integration & Edge Cases | Thread safety, double-booking prevention, inventory sync, abandoned carts |
| **70-75 min** | Demo & Q&A | Run 5 scenarios, answer interview questions, discuss trade-offs |

---

## Demo Scenarios

| Demo | Purpose | Key Pattern |
|------|---------|------------|
| **Demo 1: Setup** | Create catalog and users | System initialization |
| **Demo 2: Search** | Filter products by category/price/rating | Strategy pattern (filters) |
| **Demo 3: Cart** | Add/remove items from shopping cart | Cart state management |
| **Demo 4: Pricing** | Apply different pricing strategies | Strategy pattern (pricing) |
| **Demo 5: Lifecycle** | Complete order flow (place → ship → deliver) | Observer pattern + state transitions |

**Run Demo**:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Preparation

### Files Reference
- **START_HERE.md** → 5-minute quick reference (patterns, code structure)
- **75_MINUTE_GUIDE.md** → Deep dive (complete code, UML, 12 Q&A)
- **INTERVIEW_COMPACT.py** → Executable demo (run to see patterns in action)
- **README.md** → This file (quick overview)

### Success Checklist
- ✅ Can explain all 5 design patterns (Singleton, Strategy x2, Observer, State)
- ✅ Can draw entity relationships (Product, Cart, CartItem, Order)
- ✅ Can discuss thread-safety (locks in Singleton)
- ✅ Can handle edge cases (concurrent checkout, inventory sync, abandoned carts)
- ✅ Can explain scaling strategy (horizontal scaling with shared DB)
- ✅ Can discuss trade-offs (eventual consistency vs strong consistency)
- ✅ Can run demo without errors and explain output
- ✅ SOLID principles demonstrated in code

### Common Interview Questions
1. *How do you prevent double-booking during checkout?* → Atomic inventory reservation
2. *How do different pricing strategies work?* → Pluggable Strategy pattern
3. *How do notifications work without coupling?* → Observer pattern
4. *What happens if item goes out of stock while in cart?* → Graceful removal on checkout
5. *How do you handle concurrent checkouts?* → Singleton + threading locks
6. *How do you scale to 1M+ products?* → Horizontal scaling, caching, search indices
7. *What about abandoned carts?* → Background job clears old carts, releases inventory
8. *How do order cancellations work?* → State validation prevents invalid cancels

---

## Quick Reference

**Core Classes**: 11
- Enumerations (5): ProductCategory, ProductStatus, OrderStatus, CartItemStatus, UserRole
- Entities (6): Product, CartItem, ShoppingCart, Order, User
- Strategies (3): PricingStrategy + RegularPricing, BulkPricing, MembershipPricing
- Filters (3): SearchFilter + CategoryFilter, PriceFilter, RatingFilter
- Observers (3): OrderObserver + EmailNotifier, SMSNotifier, PushNotifier
- Controller (1): ShoppingSystem

**Key Methods**: 20+
- `add_product()` → Add to catalog
- `register_user()` → Register customer
- `search_products()` → Search with filters
- `add_to_cart()` → Add item (no reservation)
- `remove_from_cart()` → Remove item
- `checkout()` → Create order + reserve inventory
- `confirm_order()` → Confirm payment
- `ship_order()` → Ship order
- `deliver_order()` → Mark delivered
- `cancel_order()` → Cancel + refund

**Design Metrics**:
- Thread-safety: ✅ (Singleton with locks)
- Extensibility: ✅ (Strategy + Observer patterns)
- Scalability: ✅ (Horizontal scaling, caching)
- Maintainability: ✅ (Clear separation of concerns)

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  SHOPPING SYSTEM                             │
│                  (Singleton)                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │    Product       │      │     User         │              │
│  │  • name          │      │  • email         │              │
│  │  • price         │      │  • phone         │              │
│  │  • quantity      │      │  • orders[]      │              │
│  │  • reserve()     │      └──────────────────┘              │
│  │  • release()     │              │                         │
│  └──────────────────┘              │ HAS-A                   │
│          │                         │                         │
│          │ HAS-A                   ▼                         │
│          │                   ┌──────────────────┐            │
│          │                   │  ShoppingCart    │            │
│          └──────────────────→│  • items[]       │            │
│                              │  • add_item()    │            │
│                              │  • remove_item() │            │
│                              │  • checkout()    │            │
│                              └──────────────────┘            │
│                                    │                         │
│                                    │ CONTAINS                │
│                                    ▼                         │
│                              ┌──────────────────┐            │
│                              │   CartItem       │            │
│                              │  • product       │            │
│                              │  • quantity      │            │
│                              │  • reserve()     │            │
│                              │  • release()     │            │
│                              └──────────────────┘            │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │          PRICING STRATEGY (Abstract)               │     │
│  │  • calculate_price(base_price, qty)                │     │
│  ├────────────────────────────────────────────────────┤     │
│  │  • RegularPricing                                  │     │
│  │  • BulkPricing (10% off for 5+)                   │     │
│  │  • MembershipPricing (15% off)                    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │        ORDER OBSERVER (Abstract)                   │     │
│  │  • notify(event, order)                            │     │
│  ├────────────────────────────────────────────────────┤     │
│  │  • EmailNotifier                                   │     │
│  │  • SMSNotifier                                     │     │
│  │  • PushNotifier                                    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Read START_HERE.md** for 5-minute pattern memorization
2. **Study 75_MINUTE_GUIDE.md** for complete code walkthrough
3. **Run INTERVIEW_COMPACT.py** to see patterns in action
4. **Practice explaining** each pattern and edge case
5. **Mock interview** focusing on concurrency and scaling

---

*Last updated: 2024 | For detailed Q&A and code, see 75_MINUTE_GUIDE.md*
