# Vending Machine — 75-Minute Interview Guide

## Quick Start Overview

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Scope: selection, payment, dispense, refill |
| 5–15 | Architecture | Entities + state & event mapping |
| 15–35 | Core Entities | Product, Slot, Transaction, enums |
| 35–55 | Logic | select, compute price, pay, dispense, low‑stock, refill |
| 55–70 | Integration | Strategies + Observer events + summary |
| 70–75 | Demo & Q&A | Run scenarios & explain patterns |

## 🧱 Core Entities Cheat Sheet
Product(id, name)
Slot(id, product, quantity, base_price)
Transaction(id, slot, price, amount_paid, status)
Enums: MachineState(IDLE, ACCEPTING_PAYMENT, DISPENSING, OUT_OF_ORDER), TransactionStatus(INITIATED, PAID, DISPENSED, REFUNDED, FAILED)

## 🛠 Patterns Talking Points
Singleton: One controller managing all slots & transactions.
Strategy: PricingStrategy (fixed vs demand) & PaymentStrategy (coins/card/mobile).
Observer: Emits events for low_stock, slot_refilled, transaction_success, transaction_failed.
State: TransactionStatus guards dispensing only after PAID.
Factory: Helper methods create slots/transactions with generated IDs.

## 🎯 Demo Order
1. Setup: Create products, slots, observer.
2. Dynamic Pricing: Switch strategy; compare prices.
3. Purchase: Select → pay exact → dispense.
4. Low Stock & Refill: Deplete, trigger event, refill.
5. Failure & Refund: Underpay triggers fail & refund event.

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Success Checklist
- [ ] Price changes under demand strategy
- [ ] Low stock event fires at threshold
- [ ] Dispense only after PAID state
- [ ] Refund emitted on failure
- [ ] Refill resets quantity & emits slot_refilled
- [ ] Can explain each pattern mapping

## 💬 Quick Answers
Why Strategy? → Swap pricing/payment models without touching core transaction flow.
Why Observer? → Future integrations (telemetry, remote alerts) decoupled from logic.
Prevent invalid dispense? → Check TransactionStatus == PAID before dispensing.
Low stock detection? → Threshold (e.g., qty <= 2) triggers event for proactive restock.

## 🆘 If Behind
<20m: Implement Slot + Product + select/dispense flow only.
20–50m: Add Transaction + basic payment + events.
>50m: Show working purchase, narrate dynamic pricing & future payment types.

Stay concise; emphasize extensibility, safety, and clear state transitions.


## 75-Minute Guide

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

## 3. Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns Mapping
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


## Detailed Design Reference

Smart vending machine with product slots, dynamic pricing, multi‑payment, transaction lifecycle, low‑stock alerts, and refill operations. Mirrors Airline example structure: clear entities, patterns, timeline, demo scenarios, and extensibility talking points.

**Scale (Assumed)**: 1–5 machines, 20–50 slots each, 100–300 daily transactions.  
**Focus**: Inventory lifecycle (stock → selection → payment → dispense → decrement/refill) + design patterns for extensibility.

---

## Core Domain Entities
| Entity | Purpose | Relationships |
|--------|---------|--------------|
| **Product** | Consumable item descriptor | Referenced by Slot |
| **Slot** | Holds product, quantity, base price | Owned by VendingMachineSystem |
| **Transaction** | Purchase attempt with lifecycle | Links Slot + payment amount |
| **PricingStrategy** | Dynamic price computation | Injected into system |
| **PaymentStrategy** | Authorize & capture payment | Chosen per transaction |
| **Observer** | Receives machine events | Subscribed to system |

---

## Design Patterns Implemented
| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single machine controller instance | `VendingMachineSystem.get_instance()` |
| **Strategy** | Pluggable pricing or payment rules | `FixedPricing` vs `DemandPricing`, `CoinPayment` |
| **Observer** | Event notifications | `ConsoleObserver` for low stock, dispense events |
| **State** | Transaction & machine states | `TransactionStatus` (INITIATED→PAID→DISPENSED) |
| **Factory** | Object creation helpers | `add_slot()` assigns IDs, creates Slot |

Optional future patterns: Command for refund workflow, Decorator for caching price lookups.

---

## 75-Minute Timeline
| Time | Phase | What to Code |
|------|-------|--------------|
| 0–5  | Requirements | Clarify scope (refunds? multi-currency?) |
| 5–15 | Architecture | Sketch entities + pattern mapping |
| 15–35 | Core Entities | Product, Slot, Transaction, enums |
| 35–55 | Business Logic | select, price, pay, dispense, refill, events |
| 55–70 | Integration | Strategies, Observers, machine summary |
| 70–75 | Demo & Q&A | Run INTERVIEW_COMPACT.py demos |

---

## Demo Scenarios (5)
1. Setup: Products & slots creation
2. Dynamic Pricing: Switch strategy; view price difference
3. Successful Purchase: Select → pay → dispense
4. Low Stock & Refill: Consume to threshold then refill
5. Failure & Refund: Insufficient payment triggers failure & refund

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Checklist
- [ ] Can articulate each pattern & domain mapping
- [ ] Know transaction lifecycle statuses
- [ ] Can explain dynamic pricing factors (remaining quantity, demand multiplier)
- [ ] Understand low‑stock threshold & event emission
- [ ] Can discuss payment strategy swap (coins vs card vs wallet)
- [ ] Provide scaling ideas (telemetry, remote monitoring, predictive restock)

---

## Key Concepts to Explain
**Dynamic Pricing Strategy**: Adjusts effective price based on remaining inventory (scarcity) or time windows; pluggable so machine logic stays stable.

**Observer Events**: `slot_refilled`, `low_stock`, `transaction_success`, `transaction_failed`, `dispensed` enable analytics & remote alerting.

**Transaction State Management**: Guards invalid operations (cannot dispense before PAID); explicit enum transitions make reasoning clear.

**Refund Handling**: On failure we generate refund amount and emit event; later could integrate with external payment processor.

---

## File Purpose
| File | Purpose |
|------|---------|
| `README.md` | High-level overview & checklist |
| `START_HERE.md` | Rapid timeline & talking points |
| `75_MINUTE_GUIDE.md` | Deep dive design, UML, Q&A |
| `INTERVIEW_COMPACT.py` | Working implementation + demos |

---

## Tips for Success
✅ Keep pricing & payment logic out of core entities (Strategy)  
✅ Emit events early; show extensibility  
✅ Narrate trade-offs (precision of change calculation, concurrency)  
✅ Clarify exclusions (nutrition info, remote firmware updates) to stay focused  
✅ Mention reliability (sensor errors → OUT_OF_ORDER state) without overbuilding

---

See `75_MINUTE_GUIDE.md` for full breakdown; run `INTERVIEW_COMPACT.py` for demonstration; use `START_HERE.md` for quick verbal prompts.


## Compact Code

```python
"""Vending Machine - Interview Compact Implementation
Patterns: Singleton | Strategy (Pricing/Payment) | Observer | State | Factory
Five demo scenarios aligned with Airline example structure.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

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

# ============================================================================
# CORE ENTITIES
# ============================================================================

class Product:
    def __init__(self, pid: str, name: str):
        self.id = pid
        self.name = name
    def __repr__(self): return f"Product({self.name})"

class Slot:
    def __init__(self, sid: str, product: Product, quantity: int, base_price: float):
        self.id = sid
        self.product = product
        self.quantity = quantity
        self.base_price = base_price
    def decrement(self):
        if self.quantity <= 0:
            raise ValueError("Out of stock")
        self.quantity -= 1
    def __repr__(self): return f"Slot({self.id}, {self.product.name}, qty={self.quantity})"

class Transaction:
    def __init__(self, tid: str, slot: Slot, price: float):
        self.id = tid
        self.slot = slot
        self.price = price
        self.amount_paid = 0.0
        self.status = TransactionStatus.INITIATED
        self.created_at = datetime.now()
    def pay(self, amount: float):
        self.amount_paid += amount
    def __repr__(self): return f"Txn({self.id}, {self.slot.product.name}, status={self.status.name})"

# ============================================================================
# STRATEGIES (Pricing & Payment)
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def compute_price(self, slot: Slot) -> float:
        pass

class FixedPricing(PricingStrategy):
    def compute_price(self, slot: Slot) -> float:
        return round(slot.base_price, 2)

class DemandPricing(PricingStrategy):
    def compute_price(self, slot: Slot) -> float:
        # Scarcity multiplier: fewer items => higher price (up to +50%)
        max_capacity = 10  # assumed for demo
        scarcity = max(0.0, 1 - (slot.quantity / max_capacity))
        multiplier = 1 + 0.5 * scarcity
        return round(slot.base_price * multiplier, 2)

class PaymentStrategy(ABC):
    @abstractmethod
    def authorize(self, txn: Transaction, amount: float) -> bool:
        pass

class CoinPayment(PaymentStrategy):
    def authorize(self, txn: Transaction, amount: float) -> bool:
        txn.pay(amount)
        return txn.amount_paid >= txn.price

class CardPayment(PaymentStrategy):
    def authorize(self, txn: Transaction, amount: float) -> bool:
        txn.pay(amount)  # mock card charge
        return txn.amount_paid >= txn.price

# ============================================================================
# OBSERVER
# ============================================================================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, payload: Dict):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {event.upper():18} | {payload}")

# ============================================================================
# SINGLETON SYSTEM
# ============================================================================

class VendingMachineSystem:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if getattr(self, '_initialized', False): return
        self.slots: Dict[str, Slot] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.observers: List[Observer] = []
        self.pricing_strategy: PricingStrategy = FixedPricing()
        self.machine_state = MachineState.IDLE
        self._initialized = True
    def add_observer(self, obs: Observer):
        self.observers.append(obs)
    def _notify(self, event: str, payload: Dict):
        for o in self.observers: o.update(event, payload)
    def set_pricing_strategy(self, strategy: PricingStrategy):
        self.pricing_strategy = strategy
        self._notify("pricing_strategy_changed", {"strategy": strategy.__class__.__name__})
    def add_slot(self, product_name: str, quantity: int, base_price: float) -> Slot:
        sid = f"S{len(self.slots)+1}"; prod = Product(f"P{sid}", product_name)
        slot = Slot(sid, prod, quantity, base_price); self.slots[sid] = slot
        self._notify("slot_added", {"slot": sid, "product": product_name, "qty": quantity})
        return slot
    def select_slot(self, slot_id: str) -> Optional[Transaction]:
        slot = self.slots.get(slot_id)
        if not slot or slot.quantity <= 0: return None
        price = self.pricing_strategy.compute_price(slot)
        tid = f"T{len(self.transactions)+1}"; txn = Transaction(tid, slot, price)
        self.transactions[tid] = txn
        self._notify("transaction_initiated", {"txn": tid, "slot": slot_id, "price": price})
        return txn
    def pay(self, txn_id: str, amount: float, payment_strategy: PaymentStrategy) -> bool:
        txn = self.transactions.get(txn_id)
        if not txn or txn.status != TransactionStatus.INITIATED: return False
        self.machine_state = MachineState.ACCEPTING_PAYMENT
        ok = payment_strategy.authorize(txn, amount)
        if ok:
            txn.status = TransactionStatus.PAID
            self._notify("payment_authorized", {"txn": txn_id, "paid": txn.amount_paid})
        else:
            if txn.amount_paid < txn.price:
                txn.status = TransactionStatus.FAILED
                self._notify("transaction_failed", {"txn": txn_id, "paid": txn.amount_paid, "price": txn.price})
        return ok
    def dispense(self, txn_id: str) -> bool:
        txn = self.transactions.get(txn_id)
        if not txn or txn.status != TransactionStatus.PAID: return False
        self.machine_state = MachineState.DISPENSING
        try:
            txn.slot.decrement()
            txn.status = TransactionStatus.DISPENSED
            self._notify("dispensed", {"txn": txn_id, "slot": txn.slot.id, "product": txn.slot.product.name})
            if txn.slot.quantity <= LOW_STOCK_THRESHOLD:
                self._notify("low_stock", {"slot": txn.slot.id, "qty": txn.slot.quantity})
        except Exception as e:
            txn.status = TransactionStatus.FAILED
            self._notify("transaction_failed", {"txn": txn_id, "error": str(e)})
            return False
        finally:
            self.machine_state = MachineState.IDLE
        return True
    def refill(self, slot_id: str, amount: int):
        slot = self.slots.get(slot_id)
        if not slot or amount <= 0: return False
        slot.quantity += amount
        self._notify("slot_refilled", {"slot": slot_id, "qty": slot.quantity})
        return True
    def summary(self) -> Dict[str, int]:
        return {"slots": len(self.slots), "transactions": len(self.transactions)}

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup(system: VendingMachineSystem):
    print("\n" + "="*70); print("DEMO 1: Setup & Slot Creation"); print("="*70)
    system.observers.clear(); system.add_observer(ConsoleObserver())
    s1 = system.add_slot("Water Bottle", 5, 1.50)
    s2 = system.add_slot("Chocolate Bar", 4, 2.00)
    s3 = system.add_slot("Chips", 6, 2.50)
    return s1, s2, s3

def demo_2_dynamic_pricing(system: VendingMachineSystem, slot: Slot):
    print("\n" + "="*70); print("DEMO 2: Dynamic Pricing Strategy"); print("="*70)
    txn_fixed = system.select_slot(slot.id)
    print(f"Fixed price: {txn_fixed.price}")
    system.set_pricing_strategy(DemandPricing())
    txn_dynamic = system.select_slot(slot.id)
    print(f"Demand price: {txn_dynamic.price}")

def demo_3_purchase(system: VendingMachineSystem, slot: Slot):
    print("\n" + "="*70); print("DEMO 3: Purchase Flow"); print("="*70)
    txn = system.select_slot(slot.id)
    system.pay(txn.id, txn.price, CoinPayment())
    system.dispense(txn.id)
    print(f"Remaining qty: {slot.quantity}")

def demo_4_low_stock_refill(system: VendingMachineSystem, slot: Slot):
    print("\n" + "="*70); print("DEMO 4: Low Stock & Refill"); print("="*70)
    # Deplete slot to trigger low stock
    while slot.quantity > LOW_STOCK_THRESHOLD:
        txn = system.select_slot(slot.id)
        system.pay(txn.id, txn.price, CoinPayment())
        system.dispense(txn.id)
    # Refill
    system.refill(slot.id, 5)
    print(f"Post-refill qty: {slot.quantity}")

def demo_5_failure_refund(system: VendingMachineSystem, slot: Slot):
    print("\n" + "="*70); print("DEMO 5: Failure & Refund Scenario"); print("="*70)
    txn = system.select_slot(slot.id)
    # Underpay intentionally
    system.pay(txn.id, txn.price / 2, CardPayment())
    # Attempt dispense should fail (not paid)
    success = system.dispense(txn.id)
    print(f"Dispense success? {success} | Status: {txn.status.name}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VENDING MACHINE - 75 MINUTE INTERVIEW DEMOS")
    print("Patterns: Singleton | Strategy | Observer | State | Factory")
    print("="*70)
    system = VendingMachineSystem()
    try:
        s1, s2, s3 = demo_1_setup(system)
        demo_2_dynamic_pricing(system, s2)
        demo_3_purchase(system, s1)
        demo_4_low_stock_refill(system, s3)
        demo_5_failure_refund(system, s2)
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("Summary:")
        print(system.summary())
        print("Key Takeaways:")
        print(" • Pricing strategy swap shows extensibility")
        print(" • State guards dispensing before payment")
        print(" • Observer events provide hooks for telemetry")
        print(" • Low stock & refill demonstrate alert workflow")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback; traceback.print_exc()

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
