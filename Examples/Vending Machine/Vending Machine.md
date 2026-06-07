# Vending Machine — Complete Design Guide

> Item selection, multi-method payment, accurate change calculation, inventory tracking, and transaction logging with low-stock alerts.

**Scale**: 1,000+ transactions/day per machine, <5s per transaction, 99.9% uptime
**Duration**: 75-minute interview guide
**Focus**: Payment validation, greedy change calculation, item state machine, atomic dispensing

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
A customer selects a slot → inserts payment (cash/card) → the machine validates the amount covers the price → dispenses the item → returns exact change using the fewest coins → logs the transaction and alerts maintenance when stock runs low. Core concerns: payment correctness, accurate change, and atomic dispensing.

### Core Flow
```
Select Slot → Insert Payment → VALIDATE (>= price) → DISPENSE → Return Change
                                    ↓ insufficient
                              REJECT (return money)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Cash, card, or both?** → "Both — cash and card"
2. **Does it return change?** → "Yes, with the fewest coins"
3. **How many slots / capacity?** → "10 slots, up to 20 units each"
4. **Single customer at a time?** → "Yes — serialize transactions"
5. **Low-stock alerts?** → "Yes, notify maintenance below threshold"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Customer** | Buys items | Select slot, insert payment, collect item + change |
| **Maintenance** | Services machine | Restock slots, collect revenue, respond to alerts |
| **System** | Coordinator | Validate payment, dispense, compute change, log transactions |

### Functional Requirements (What does the system do?)

✅ **Display & Select**
  - Show items with price, quantity, and status
  - Select an item by slot number

✅ **Payment**
  - Accept cash and card
  - Validate inserted amount ≥ price
  - Reject and return money on insufficient payment

✅ **Dispense & Change**
  - Dispense item, decrement inventory
  - Return change using a greedy fewest-coins algorithm

✅ **Inventory & Alerts**
  - Track quantity per slot
  - Restock slots
  - Alert maintenance on low stock

✅ **Reporting**
  - Log every transaction
  - Produce a daily revenue / units-sold report

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Transaction processing < 5 seconds
✅ **Throughput**: 1,000+ transactions/day per machine
✅ **Uptime**: 99.9%
✅ **Correctness**: Exact change; no double-dispensing
✅ **Concurrency**: One transaction at a time (serialized)

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max slots** | 10 |
| **Max stock per slot** | 20 |
| **Price range** | $0.50 – $10.00 |
| **Coin denominations** | $0.01, $0.05, $0.10, $0.25 (notes $1, $2) |
| **Low-stock threshold** | ≤ 5 units |
| **Concurrency** | Serialized — one customer at a time |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
VendingMachine, Slot, Item, Transaction, PaymentProcessor, CoinDispenser, ...
```

### Step 2.2: Define Core Classes

#### **Item** — A product in a slot
```
Properties:
  - item_id: str
  - name: str
  - price: float
  - quantity: int

Behaviors:
  - status (derived): AVAILABLE / LOW_STOCK / SOLD_OUT based on quantity
```

#### **Slot** — A physical location holding one item type
```
Properties:
  - slot_number: int (1-10)
  - item: Item
```

#### **Transaction** — A purchase record
```
Properties:
  - transaction_id: str
  - item_id: str
  - amount_inserted: float
  - price: float
  - change: float
  - payment_method: PaymentMethod
  - timestamp: datetime
  - status: TransactionStatus
```

#### **CoinDispenser** — Change calculator
```
Behaviors:
  - calculate_change(amount): Greedy breakdown into fewest coins
```

#### **PaymentProcessor** — Payment validation
```
Behaviors:
  - validate_payment(inserted, price): inserted >= price
```

#### **VendingMachine** — Main controller (Singleton)
```
Properties:
  - slots: Dict[int, Slot]
  - transactions: List[Transaction]
  - total_revenue: float
  - lock: threading.Lock

Behaviors:
  - add_item / restock / display_items
  - purchase(slot, inserted, method): validate → dispense → change
  - get_daily_report()
```

### Step 2.3: Define Enumerations (State & Type)

```python
class ItemStatus(Enum):
    AVAILABLE = 1     # quantity > 5
    LOW_STOCK = 2     # 0 < quantity <= 5
    SOLD_OUT = 3      # quantity == 0

class TransactionStatus(Enum):
    PENDING = 1
    COMPLETED = 2
    FAILED = 3

class PaymentMethod(Enum):
    CASH = 1
    CARD = 2
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Item** | Price + quantity + status | Can't track availability |
| **Slot** | Maps position → item | Can't address products |
| **Transaction** | Audit + reconciliation | No revenue tracking |
| **CoinDispenser** | Correct change | Wrong/over change given |
| **PaymentProcessor** | Validate before dispense | Dispense without payment |
| **VendingMachine** | Central coordination | No atomic dispensing |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Purchase** ⭐ CRITICAL
```python
def purchase(slot_number: int, inserted_amount: float,
             payment_method: PaymentMethod = PaymentMethod.CASH) -> Tuple[bool, float, str]:
    """
    Validate payment, dispense item, and return change.

    Precondition: slot exists and item.quantity > 0
    Postcondition: quantity decremented, transaction logged, change returned

    Returns: (success, change_or_returned_amount, message)

    Failure causes:
      - Invalid slot
      - Item sold out
      - Insufficient payment (returns inserted amount)

    Concurrency: THREAD-SAFE (machine lock — serialized)
    """
    pass
```

#### **2. Add Item / Restock**
```python
def add_item(slot_number: int, name: str, price: float, quantity: int) -> bool: ...
def restock(slot_number: int, quantity: int) -> bool: ...
```

#### **3. Display & Report**
```python
def display_items() -> None: ...      # Show all slots with status
def get_daily_report() -> None: ...   # Revenue + units sold
```

#### **4. Change Calculation**
```python
@staticmethod
def calculate_change(change_amount: float) -> Tuple[Dict[float, int], float]:
    """
    Greedy fewest-coin breakdown.
    Returns: (coin -> count map, remaining unpayable amount).
    Example: $4.01 -> {2.00: 2, 0.01: 1}, remainder 0.0
    """
    pass
```

### Step 3.2: Failure Model

This design returns `(bool, amount, message)` tuples for an interview-friendly flow. A production version raises:

```python
class VendingException(Exception): ...
class InvalidSlotError(VendingException): ...
class SoldOutError(VendingException): ...
class InsufficientPaymentError(VendingException): ...
class DispenserJamError(VendingException): ...
```

### Step 3.3: API Usage Example

```python
machine = VendingMachine(10)
machine.add_item(1, "Coke", 2.00, 10)

machine.display_items()
success, change, msg = machine.purchase(1, 2.50, PaymentMethod.CASH)
# -> success=True, change=0.50, msg="Success"

machine.get_daily_report()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
VendingMachine HAS-A slots (1:N Composition)
  └─ Machine owns and manages all slots

Slot HAS-A item (1:1 Composition)
  └─ Each slot holds one item type

VendingMachine HAS-A transactions (1:N Composition)
  └─ Machine owns transaction history

VendingMachine USES-A PaymentProcessor + CoinDispenser (1:1 Composition)
  └─ Validation and change services
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────┐
│   VendingMachine (Singleton)       │
├────────────────────────────────────┤
│ - slots: Dict[int, Slot]           │
│ - transactions: List[Transaction]  │
│ - total_revenue: float             │
│ - payment_processor                │
│ - lock: threading.Lock             │
├────────────────────────────────────┤
│ + add_item(...) / restock(...)     │
│ + display_items()                  │
│ + purchase(...): (bool,float,str)  │
│ + get_daily_report()               │
└──────────────┬─────────────────────┘
       owns 1:N │
               ▼
        ┌──────────────┐
        │    Slot      │
        ├──────────────┤
        │ slot_number  │
        │ item: Item   │
        └──────┬───────┘
        holds 1:1
               ▼
        ┌──────────────┐
        │    Item      │
        ├──────────────┤
        │ item_id      │
        │ name / price │
        │ quantity     │
        │ status (der.)│
        └──────────────┘

SERVICES (Composition):
┌──────────────────────┐   ┌──────────────────────┐
│ PaymentProcessor     │   │ CoinDispenser        │
│ + validate_payment() │   │ + calculate_change() │
└──────────────────────┘   └──────────────────────┘

ITEM STATE MACHINE:
AVAILABLE ──sales──→ LOW_STOCK ──sales──→ SOLD_OUT
    ▲                                         │
    └──────────────── restock ────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| VendingMachine → Slots | 1:N | Composition | Machine owns all slots |
| Slot → Item | 1:1 | Composition | One item type per slot |
| VendingMachine → Transactions | 1:N | Composition | Machine owns history |
| VendingMachine → PaymentProcessor | 1:1 | Composition | Validation service |
| VendingMachine → CoinDispenser | 1:1 | Composition | Change service |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For VendingMachine)

**Problem**: One machine must own a single consistent view of inventory and revenue.

**Solution**: One global instance with thread-safe initialization.

```python
class VendingMachine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe init
**Trade-off**: ⚠️ Global state; use an ID-keyed manager for fleets

---

### Pattern 2: **State** (For Item Status)

**Problem**: An item is AVAILABLE, LOW_STOCK, or SOLD_OUT and the display/logic must react.

**Solution**: Derive status from quantity so it can never drift out of sync.

```python
@property
def status(self) -> ItemStatus:
    if self.quantity == 0:
        return ItemStatus.SOLD_OUT
    elif self.quantity <= 5:
        return ItemStatus.LOW_STOCK
    return ItemStatus.AVAILABLE
```

**Benefit**: ✅ Single source of truth (quantity), ✅ No inconsistent state
**Trade-off**: ⚠️ Computed each access (negligible here)

---

### Pattern 3: **Strategy** (For Payment Methods)

**Problem**: Cash and card validate/settle differently and more methods may appear (NFC, mobile).

**Solution**: A `PaymentProcessor` abstraction selected by `PaymentMethod`.

```python
class PaymentProcessor:
    def validate_payment(self, inserted: float, price: float) -> bool:
        return inserted >= price
# Extend with CardProcessor, NFCProcessor without touching purchase()
```

**Benefit**: ✅ Add payment methods without changing core flow
**Trade-off**: ⚠️ Extra abstraction layer

---

### Pattern 4: **Observer** (For Low-Stock Alerts)

**Problem**: Maintenance must be notified when stock dips, without coupling to the purchase flow.

**Solution**: Emit a low-stock event after dispensing (here a print; in production an observer list).

```python
if item.quantity <= 5 and item.quantity > 0:
    print(f"⚠️ LOW STOCK ALERT: Slot {slot_number} ({item.name}) needs restocking")
```

**Benefit**: ✅ Decoupled alerting, easy to add channels
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 5: **Command / Greedy Algorithm** (For Change)

**Problem**: Return change with the fewest coins, accurately.

**Solution**: Greedy descent through denominations.

```python
DENOMINATIONS = [2.00, 1.00, 0.25, 0.10, 0.05, 0.01]
for denom in DENOMINATIONS:
    count = int(change_amount / denom)
    if count > 0:
        coins[denom] = count
        change_amount = round(change_amount - count * denom, 2)
```

**Benefit**: ✅ Fewest coins for canonical denominations
**Trade-off**: ⚠️ Greedy isn't optimal for arbitrary denominations (use DP then)

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Single machine state | Consistent inventory/revenue |
| **State** | Item availability | No inconsistent status |
| **Strategy** | Varying payment methods | Pluggable, extensible |
| **Observer** | Low-stock alerts | Decoupled notifications |
| **Greedy** | Change calculation | Fewest coins returned |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
🍿 Vending Machine - Interview Implementation
Demonstrates:
1. Item inventory management
2. Multi-payment processing
3. Change calculation
4. State machine
5. Transaction logging
"""

from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class ItemStatus(Enum):
    AVAILABLE = 1
    LOW_STOCK = 2
    SOLD_OUT = 3

class TransactionStatus(Enum):
    PENDING = 1
    COMPLETED = 2
    FAILED = 3

class PaymentMethod(Enum):
    CASH = 1
    CARD = 2

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Item:
    item_id: str
    name: str
    price: float
    quantity: int

    @property
    def status(self) -> ItemStatus:
        if self.quantity == 0:
            return ItemStatus.SOLD_OUT
        elif self.quantity <= 5:
            return ItemStatus.LOW_STOCK
        return ItemStatus.AVAILABLE

@dataclass
class Slot:
    slot_number: int
    item: Item

@dataclass
class Transaction:
    transaction_id: str
    item_id: str
    amount_inserted: float
    price: float
    change: float
    payment_method: PaymentMethod
    timestamp: datetime
    status: TransactionStatus = TransactionStatus.PENDING

# ============================================================================
# PAYMENT PROCESSOR
# ============================================================================

class CoinDispenser:
    """Calculate change using greedy algorithm"""

    DENOMINATIONS = [2.00, 1.00, 0.25, 0.10, 0.05, 0.01]

    @staticmethod
    def calculate_change(change_amount: float) -> Tuple[Dict[float, int], float]:
        """Returns coin breakdown and remaining amount"""
        change_amount = round(change_amount, 2)
        coins = {}

        for denom in CoinDispenser.DENOMINATIONS:
            count = int(change_amount / denom)
            if count > 0:
                coins[denom] = count
                change_amount -= count * denom
                change_amount = round(change_amount, 2)

        return coins, change_amount

class PaymentProcessor:
    def validate_payment(self, inserted: float, price: float) -> bool:
        return inserted >= price

# ============================================================================
# VENDING MACHINE (SINGLETON)
# ============================================================================

class VendingMachine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, num_slots: int = 10):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.slots: Dict[int, Slot] = {}
        self.num_slots = num_slots
        self.transactions: List[Transaction] = []
        self.transaction_counter = 0
        self.total_revenue = 0.0
        self.lock = threading.Lock()
        self.payment_processor = PaymentProcessor()

        print(f"🍿 Vending machine initialized with {num_slots} slots")

    def add_item(self, slot_number: int, name: str, price: float, quantity: int):
        with self.lock:
            if slot_number < 1 or slot_number > self.num_slots:
                return False

            item = Item(f"ITEM_{slot_number}", name, price, quantity)
            slot = Slot(slot_number, item)
            self.slots[slot_number] = slot

            print(f"✓ Added {quantity}x '{name}' (${price}) to slot {slot_number}")
            return True

    def display_items(self):
        with self.lock:
            print("\n  Available Items:")
            for slot_num in sorted(self.slots.keys()):
                slot = self.slots[slot_num]
                item = slot.item
                status_symbol = "✓" if item.status == ItemStatus.AVAILABLE else "⚠" if item.status == ItemStatus.LOW_STOCK else "✗"
                print(f"  {status_symbol} Slot {slot_num}: {item.name:15} ${item.price:5.2f} (qty: {item.quantity})")

    def purchase(self, slot_number: int, inserted_amount: float, payment_method: PaymentMethod = PaymentMethod.CASH) -> Tuple[bool, float, str]:
        with self.lock:
            if slot_number not in self.slots:
                return False, 0.0, "Invalid slot"

            slot = self.slots[slot_number]
            item = slot.item

            # Check availability
            if item.quantity == 0:
                return False, 0.0, "Item sold out"

            # Validate payment
            if not self.payment_processor.validate_payment(inserted_amount, item.price):
                return False, inserted_amount, f"Insufficient payment (need ${item.price}, inserted ${inserted_amount:.2f})"

            # Process transaction
            self.transaction_counter += 1
            change = inserted_amount - item.price

            transaction = Transaction(
                f"TXN_{self.transaction_counter:06d}",
                item.item_id,
                inserted_amount,
                item.price,
                change,
                payment_method,
                datetime.now(),
                TransactionStatus.COMPLETED
            )

            self.transactions.append(transaction)
            self.total_revenue += item.price

            # Dispense item
            item.quantity -= 1

            print(f"✓ Dispensing: {item.name}")
            print(f"  Price: ${item.price:.2f}")
            print(f"  Inserted: ${inserted_amount:.2f}")

            if change > 0:
                coins, remainder = CoinDispenser.calculate_change(change)
                print(f"  Change: ${change:.2f}")
                if coins:
                    print(f"  Coins returned: {coins}")

            # Check low stock
            if item.quantity <= 5 and item.quantity > 0:
                print(f"  ⚠️ LOW STOCK ALERT: Slot {slot_number} ({item.name}) needs restocking")

            return True, change, "Success"

    def restock(self, slot_number: int, quantity: int):
        with self.lock:
            if slot_number not in self.slots:
                return False

            self.slots[slot_number].item.quantity += quantity
            print(f"✓ Restocked slot {slot_number}: +{quantity} units")
            return True

    def get_daily_report(self):
        with self.lock:
            print(f"\n  Daily Report:")
            print(f"  Total transactions: {len(self.transactions)}")
            print(f"  Total revenue: ${self.total_revenue:.2f}")
            print(f"  Items sold:")

            item_sales = {}
            for txn in self.transactions:
                item_id = txn.item_id
                item_sales[item_id] = item_sales.get(item_id, 0) + 1

            for item_id, count in item_sales.items():
                print(f"    {item_id}: {count} units")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_successful_purchase():
    print("\n" + "="*70)
    print("DEMO 1: SUCCESSFUL PURCHASE")
    print("="*70)

    machine = VendingMachine(10)
    machine.add_item(1, "Coke", 2.00, 10)
    machine.add_item(2, "Chips", 1.50, 8)

    machine.display_items()

    success, change, msg = machine.purchase(1, 2.00, PaymentMethod.CASH)
    print(f"  Result: {msg}")

def demo_2_insufficient_payment():
    print("\n" + "="*70)
    print("DEMO 2: INSUFFICIENT PAYMENT")
    print("="*70)

    machine = VendingMachine(10)
    machine.add_item(1, "Water", 1.50, 5)

    success, returned, msg = machine.purchase(1, 1.00, PaymentMethod.CASH)
    print(f"  Result: {msg}")
    print(f"  Returned: ${returned:.2f}")

def demo_3_change_calculation():
    print("\n" + "="*70)
    print("DEMO 3: COMPLEX CHANGE CALCULATION")
    print("="*70)

    machine = VendingMachine(10)
    machine.add_item(1, "Coffee", 0.99, 10)

    success, change, msg = machine.purchase(1, 5.00, PaymentMethod.CASH)
    print(f"  Result: {msg}")

def demo_4_sold_out():
    print("\n" + "="*70)
    print("DEMO 4: SOLD OUT ITEM")
    print("="*70)

    machine = VendingMachine(10)
    machine.add_item(1, "Juice", 1.75, 1)

    machine.display_items()

    # Sell the only unit
    machine.purchase(1, 2.00, PaymentMethod.CASH)

    print("\n  After first sale:")
    machine.display_items()

    # Try to purchase again
    success, _, msg = machine.purchase(1, 2.00, PaymentMethod.CASH)
    print(f"  Second purchase result: {msg}")

def demo_5_multiple_transactions():
    print("\n" + "="*70)
    print("DEMO 5: MULTIPLE TRANSACTIONS & REPORT")
    print("="*70)

    machine = VendingMachine(10)
    machine.add_item(1, "Coke", 2.00, 20)
    machine.add_item(2, "Chips", 1.50, 20)
    machine.add_item(3, "Candy", 0.75, 20)

    # Multiple purchases
    machine.purchase(1, 2.00, PaymentMethod.CASH)
    machine.purchase(2, 2.00, PaymentMethod.CASH)
    machine.purchase(3, 1.00, PaymentMethod.CASH)
    machine.purchase(1, 2.50, PaymentMethod.CASH)

    machine.get_daily_report()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🍿 VENDING MACHINE - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_successful_purchase()
    demo_2_insufficient_payment()
    demo_3_change_calculation()
    demo_4_sold_out()
    demo_5_multiple_transactions()

    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **purchase** | Machine lock | Atomic check-stock + validate + dispense (no double-dispense) |
| **add_item / restock** | Machine lock | Consistent inventory updates |
| **display_items / report** | Machine lock | Consistent snapshot reads |
| **Singleton init** | Class lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ A single machine lock serializes transactions (acceptable for one customer at a time)
2. ✅ Validate-then-dispense happens inside one critical section
3. ✅ Double-checked locking for the Singleton
4. ✅ For a fleet, key machines by ID instead of a global singleton

---

## Demo Scenarios

### Scenario 1: Successful Purchase
```
Select Coke ($2.00), insert $2.00 → Dispense Coke, change $0.00
```

### Scenario 2: Insufficient Payment
```
Select Water ($1.50), insert $1.00 → "Insufficient payment", $1.00 returned
```

### Scenario 3: Complex Change Calculation
```
Select Coffee ($0.99), insert $5.00 → change $4.01 = {2.00:2, 0.01:1}
```

### Scenario 4: Sold Out Item
```
Juice qty=1 → first purchase dispenses; status → SOLD_OUT
Second purchase → "Item sold out"
```

### Scenario 5: Multiple Transactions & Report
```
4 purchases → Daily Report: total transactions, total revenue, units sold per item
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you represent items in the machine?**

A: Each slot stores item_id, name, price, quantity, and a derived status. Availability is `quantity > 0`.

**Q2: What states can an item have?**

A: AVAILABLE (qty > 5), LOW_STOCK (0 < qty ≤ 5), SOLD_OUT (qty = 0). Status is derived from quantity so it can't drift.

**Q3: How do you calculate change?**

A: Greedy descent through denominations, largest first: `change = inserted − price`, then take as many of each denomination as fit.

**Q4: What payment methods do you support?**

A: Cash and card via a `PaymentProcessor` abstraction; new methods (NFC, mobile) plug in without changing `purchase()`.

**Q5: How do you prevent dispensing before payment is validated?**

A: `purchase()` validates `inserted ≥ price` inside the lock before decrementing inventory and dispensing.

### Intermediate Questions

**Q6: How to prevent double-dispensing (button pressed twice)?**

A: The machine lock serializes purchases; once dispensed, quantity drops and a repeat hits SOLD_OUT or a fresh transaction.

**Q7: How to handle a card payment decline?**

A: The card processor returns a decline → transaction FAILED, return any inserted cash, prompt retry.

**Q8: How to track low-stock alerts?**

A: After each dispense, if `quantity ≤ 5` emit a low-stock alert (observer/notification) to maintenance.

**Q9: What's stored in a transaction record?**

A: Item, amount inserted, price, change, payment method, timestamp, and status — used for reconciliation and analytics.

### Advanced Questions

**Q10: How to handle a dispenser jam?**

A: Dispense timeout → mark JAMMED, alert maintenance, refund the customer; cap stock per slot to limit exposure.

**Q11: How to implement dynamic pricing?**

A: Overnight batch adjusts prices by time-of-day/demand (e.g. +20% at lunch). `purchase()` reads the current price.

**Q12: How to reconcile cash collected?**

A: Daily report sums `price × units_sold`; compare to cash + card receipts; discrepancies flag theft or malfunction.

---

## Scaling Q&A

### Q1: Can a single machine handle 1,000 transactions/day?

Yes — ~1/minute over 16 hours at ~5s each. No bottleneck; a single serialized lock suffices.

### Q2: How to support a fleet of machines?

Key each machine by ID (drop the strict singleton) and add a `VendingMachineManager` with a dashboard for inventory and revenue per machine.

### Q3: How to handle card-network failure (offline)?

Fall back to cash; queue card transactions in memory and batch-process on reconnect, with a small offline card cap.

### Q4: How to prevent inventory inconsistency?

Pessimistic lock per slot on dispense (decrement under lock), or optimistic concurrency with version numbers.

### Q5: How to optimize restocking routes?

Track fleet inventory and visit lowest-stock machines first; forecast 3 days out to minimize trips.

### Q6: How to predict demand?

ML on historical sales by item/time to pre-stock popular items before peaks and reduce waste.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through the select → pay → validate → dispense → change flow
- [ ] Explain the item state machine (AVAILABLE/LOW_STOCK/SOLD_OUT)
- [ ] Explain the greedy change algorithm and its limits
- [ ] Explain how the lock prevents double-dispensing
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss fleet management and offline payment fallback
- [ ] Discuss reconciliation and jam handling

---

**Ready for interview? Insert coin and dispense! 🍿**
