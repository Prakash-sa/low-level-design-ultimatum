# 🍽️ Restaurant Management System - Quick Start Guide

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

## Design Patterns Cheat Sheet
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
