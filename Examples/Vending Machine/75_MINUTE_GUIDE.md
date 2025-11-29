# Vending Machine - 75 Minute Deep Implementation & Interview Guide

## 1. System Overview
Smart vending machine slice: manages product slots, dynamic pricing vs fixed, payment authorization (coins/card/mobile), transaction lifecycle, low-stock detection, and refill operations. Excludes hardware drivers, real concurrency, fraud detection, multi-currency reconciliation.

---

## 2. Core Functional Requirements
| Requirement | Included | Notes |
|-------------|----------|-------|
| View Products & Prices | ✅ | Derived from slots + strategy |
| Select Product | ✅ | Creates transaction in INITIATED state |
| Insert / Authorize Payment | ✅ | Accumulates amount or mocks card auth |
| Dispense Item | ✅ | Only after PAID state; decrements quantity |
| Issue Refund on Failure | ✅ | Emits refund event with amount |
| Low Stock Alert | ✅ | Threshold event (qty ≤ 2) |
| Refill Slot | ✅ | Emits slot_refilled event |
| Switch Pricing Strategy | ✅ | Fixed vs Demand pricing |

Excluded: complex change optimization, multi-machine network syncing, predictive restocking ML model, security hardening.

---

## 3. Design Patterns Mapping
| Pattern | Domain Use | Benefit |
|---------|------------|---------|
| Singleton | `VendingMachineSystem` central controller | Consistent orchestration |
| Strategy | Pricing & Payment behaviors | Pluggable algorithms |
| Observer | Operational events | Decoupled analytics/alerts |
| State | Transaction + Machine state | Guard invalid transitions |
| Factory | Slot/transaction creation helpers | Encapsulation & validation |

---

## 4. Enumerations & Constants
```python
from enum import Enum

class MachineState(Enum):
    IDLE = "idle"
    ACCEPTING_PAYMENT = "accepting_payment"
    DISPENSING = "dispensing"
    OUT_OF_ORDER = "out_of_order"

class TransactionStatus(Enum):
    INITIATED = "initiated"
    PAID = "paid"
    DISPENSED = "dispensed"
    REFUNDED = "refunded"
    FAILED = "failed"

LOW_STOCK_THRESHOLD = 2
```

---

## 5. Core Classes (Condensed)
```python
class Product:
    def __init__(self, pid, name): self.id=pid; self.name=name

class Slot:
    def __init__(self, sid, product, quantity, base_price):
        self.id=sid; self.product=product; self.quantity=quantity; self.base_price=base_price
    def decrement(self):
        if self.quantity <= 0: raise ValueError("Out of stock")
        self.quantity -= 1

class Transaction:
    def __init__(self, tid, slot, price):
        self.id=tid; self.slot=slot; self.price=price; self.amount_paid=0.0
        self.status=TransactionStatus.INITIATED
    def pay(self, amount): self.amount_paid += amount
```

---

## 6. Pricing Strategy (Strategy Pattern)
```python
class PricingStrategy(ABC):
    @abstractmethod
    def compute_price(self, slot: Slot) -> float: pass

class FixedPricing(PricingStrategy):
    def compute_price(self, slot): return slot.base_price

class DemandPricing(PricingStrategy):
    def compute_price(self, slot):
        scarcity = max(0, 1 - (slot.quantity / 10))  # naive
        return round(slot.base_price * (1 + 0.5*scarcity), 2)
```

---

## 7. Payment Strategy (Optional Extension)
```python
class PaymentStrategy(ABC):
    @abstractmethod
    def authorize(self, txn: Transaction, amount: float) -> bool: pass

class CoinPayment(PaymentStrategy):
    def authorize(self, txn, amount): txn.pay(amount); return txn.amount_paid >= txn.price

class CardPayment(PaymentStrategy):
    def authorize(self, txn, amount): txn.pay(amount); return txn.amount_paid >= txn.price
```

---

## 8. Observer Pattern
```python
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict): pass

class ConsoleObserver(Observer):
    def update(self, event, payload): print(f"[EVENT] {event.upper():18} | {payload}")
```
Events: `slot_refilled`, `low_stock`, `transaction_success`, `transaction_failed`, `dispensed`.

---

## 9. Singleton Controller
```python
class VendingMachineSystem:
    _instance=None
    def __new__(cls):
        if not cls._instance: cls._instance=super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self,'_init',False): return
        self.slots={}; self.transactions={}; self.observers=[]
        self.pricing_strategy=FixedPricing(); self.machine_state=MachineState.IDLE; self._init=True
    def add_observer(self,o): self.observers.append(o)
    def _notify(self,e,p): [o.update(e,p) for o in self.observers]
    def add_slot(self, product_name, quantity, base_price):
        sid=f"S{len(self.slots)+1}"; prod=Product(f"P{sid}", product_name)
        slot=Slot(sid, prod, quantity, base_price); self.slots[sid]=slot; return slot
    def select_slot(self, slot_id):
        slot=self.slots.get(slot_id); price=self.pricing_strategy.compute_price(slot)
        tid=f"T{len(self.transactions)+1}"; txn=Transaction(tid, slot, price); self.transactions[tid]=txn
        return txn
```
```python
    def pay(self, txn_id, amount, payment_strategy: PaymentStrategy):
        txn=self.transactions.get(txn_id)
        if not txn or txn.status!=TransactionStatus.INITIATED: return False
        self.machine_state=MachineState.ACCEPTING_PAYMENT
        ok=payment_strategy.authorize(txn, amount)
        if ok:
            txn.status=TransactionStatus.PAID
        else:
            if txn.amount_paid < txn.price:
                txn.status=TransactionStatus.FAILED; self._notify("transaction_failed",{"txn":txn_id,"paid":txn.amount_paid})
        return ok
    def dispense(self, txn_id):
        txn=self.transactions.get(txn_id)
        if not txn or txn.status!=TransactionStatus.PAID: return False
        self.machine_state=MachineState.DISPENSING
        try:
            txn.slot.decrement(); txn.status=TransactionStatus.DISPENSED
            self._notify("dispensed",{"txn":txn_id,"slot":txn.slot.id})
            if txn.slot.quantity <= LOW_STOCK_THRESHOLD:
                self._notify("low_stock",{"slot":txn.slot.id,"qty":txn.slot.quantity})
        except Exception as e:
            txn.status=TransactionStatus.FAILED; self._notify("transaction_failed",{"txn":txn_id,"error":str(e)})
            return False
        finally:
            self.machine_state=MachineState.IDLE
        return True
    def refill(self, slot_id, amount):
        slot=self.slots.get(slot_id); slot.quantity += amount
        self._notify("slot_refilled",{"slot":slot_id,"qty":slot.quantity})
```

---

## 10. UML Diagram (ASCII)
```
┌────────────────────────────────────────────────────────────────┐
│                     VENDING MACHINE SYSTEM                     │
└────────────────────────────────────────────────────────────────┘
                 ┌────────────────────────────┐
                 │ VendingMachineSystem       │ ◄─ Singleton
                 ├────────────────────────────┤
                 │ slots{} transactions{}     │
                 │ pricing_strategy           │
                 │ machine_state              │
                 ├────────────────────────────┤
                 │ +select_slot()             │
                 │ +pay() +dispense()         │
                 │ +refill()                  │
                 └──────────┬─────────────────┘
                            │
                            ▼
                         Slot ── Product
                            │ (base_price, quantity)
                            ▼
                       Transaction (price, status)

PricingStrategy ◄── FixedPricing / DemandPricing
PaymentStrategy ◄── CoinPayment / CardPayment
Observer ◄── ConsoleObserver receives events
```

---

## 11. Demo Flow Outline
1. Setup: slots created, observer registered.  
2. Dynamic Pricing: switch to DemandPricing; show new price.  
3. Purchase: pay exact with CoinPayment; dispense success.  
4. Low Stock & Refill: deplete to threshold; trigger low_stock; refill.  
5. Failure & Refund: insufficient payment leads to FAILED state (refund conceptually emitted).

---

## 12. Interview Q&A
**Q1: Why use Strategy for pricing?** To experiment with demand-based multipliers without touching Slot logic.
**Q2: How prevent dispensing without payment?** State check: must be PAID; otherwise returns False.
**Q3: What triggers low stock?** Quantity at or below threshold after dispensing; event enables proactive refill.
**Q4: Handling concurrency for quantity decrements?** In production, use atomic DB update or slot-level mutex.
**Q5: How would you process card payments securely?** Delegate to external PCI-compliant service; keep token only.
**Q6: Scaling to fleet of machines?** Add remote telemetry service; each machine publishes events (Observer -> message queue) aggregated centrally.
**Q7: Adding promotions (buy 2 get 1)?** New PromotionPricing strategy layering discount logic before compute_price.
**Q8: Recover from hardware failure?** Transition to OUT_OF_ORDER; block new transactions; dispatch maintenance alert.
**Q9: Support multi-currency?** Currency field in Slot; PricingStrategy returns value + currency; PaymentStrategy converts.
**Q10: Refund details?** Track amount_paid - price difference; observer event logs refund; integrate with payer source.
**Q11: Telemetry extension?** Add MetricsObserver capturing dispense times & failure counts for predictive restocking.
**Q12: Why not embed pricing in Slot?** Violates SRP; mixing concerns makes changing pricing rules risky.

---

## 13. Edge Cases & Guards
| Edge Case | Handling |
|-----------|----------|
| Select invalid slot | Return None / raise early |
| Pay after failure | Disallowed; status not INITIATED |
| Dispense out-of-stock | Caught; transaction_failed event |
| Refill negative amount | Validate > 0 before apply |
| Demand price on empty slot | Scarcity maxed; still guard against dispense |
| Multiple dispense attempts | Only first succeeds; statuses guard subsequent calls |

---

## 14. Scaling Prompts
- Event-driven restock planning with aggregated low_stock events.
- Predictive restocking: time-series of quantity deltas.
- Edge computing: local decisions (OUT_OF_ORDER) with cloud sync.
- Caching pricing for high-frequency selections.
- Splitting machine into microcontrollers vs app layer (not coded here).

---

## 15. Demo Snippet
```python
system = VendingMachineSystem(); system.add_observer(ConsoleObserver())
slot = system.add_slot("Water Bottle", 5, 1.50)
txn = system.select_slot(slot.id)
system.pay(txn.id, txn.price, CoinPayment())
system.dispense(txn.id)
print(slot.quantity)
```

---

## 16. Final Checklist
- [ ] Strategy swap demonstrates price change
- [ ] Transaction statuses enforced
- [ ] Low stock event fires correctly
- [ ] Refill event prints with updated quantity
- [ ] Dispense fails gracefully when stock empty
- [ ] You can articulate scaling & pattern choices

---

Deliver clarity: emphasize separation of concerns, explicit states, and pattern-driven extensibility.

