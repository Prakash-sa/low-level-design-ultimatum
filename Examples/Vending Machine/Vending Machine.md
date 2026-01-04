# Vending Machine — 75-Minute Interview Guide

## Quick Start

**What is it?** Automated vending machine dispensing snacks/drinks, accepting payments, managing inventory, and processing transactions.

**Key Classes:**
- `VendingMachine` (Singleton): Central system
- `Item`: Snack/drink with price, quantity
- `Slot`: Physical location for items
- `Transaction`: Payment record
- `PaymentProcessor`: Handles coins/notes/cards
- `Dispenser`: Physically releases item

**Core Flows:**
1. **Select**: Customer picks item → Check availability
2. **Payment**: Insert coins/notes/card → Validate amount
3. **Dispense**: Release item → Update inventory
4. **Change**: Return excess money
5. **Maintenance**: Restock items, collect revenue, service

**5 Design Patterns:**
- **Singleton**: One VendingMachine
- **State Machine**: Item status (available/sold-out/low-stock)
- **Strategy**: Different payment methods (cash, card, digital)
- **Observer**: Alert when low stock
- **Command**: Maintain transaction history

---

## System Overview

Autonomous vending machine managing product inventory, processing multi-payment methods, dispensing items, and tracking transactions.

### Requirements

**Functional:**
- Display available items with prices
- Accept coins, notes, cards
- Validate payment sufficiency
- Dispense items
- Return change
- Track inventory
- Log transactions
- Alert on low stock

**Non-Functional:**
- Transaction processing < 5 seconds
- Support 1000+ daily transactions
- 99.9% uptime
- Accurate change calculation

**Constraints:**
- Max items: 10 slots
- Max stock per slot: 20
- Price range: $0.50 - $10.00
- Coin denominations: $0.01, $0.05, $0.10, $0.25

---

## Architecture Diagram (ASCII UML)

```
┌──────────────────┐
│ VendingMachine   │
│ (Singleton)      │
└────────┬─────────┘
         │
    ┌────┼────┬───────┐
    │    │    │       │
    ▼    ▼    ▼       ▼
┌────┐ ┌────┐ ┌──────┐ ┌──────┐
│Slot│ │Item│ │Payment│ │Dispense
└────┘ └────┘ └──────┘ └──────┘

Item Status:
AVAILABLE → SOLD_OUT
   ↓
LOW_STOCK

Payment States:
INSERTING → SUFFICIENT → DISPENSING → COMPLETED
   ↓
INSUFFICIENT
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you represent items in the machine?**
A: Each slot stores: item_id, name, price, quantity. Slot has position (1-10). Query item: check slot.quantity > 0 for availability.

**Q2: What states can an item have?**
A: (1) AVAILABLE: quantity > 5, (2) LOW_STOCK: 0 < quantity <= 5, (3) SOLD_OUT: quantity = 0. Display accordingly to customer.

**Q3: How do you calculate change?**
A: Change = inserted_amount - item_price. Use greedy algorithm: use largest denominations first. Example: $5.25 change = 2×$2 + 1×$1 + 0×$0.25 = 3 coins.

**Q4: What payment methods do you support?**
A: Coins ($0.01-$0.25), notes ($1, $5, $10), card (credit/debit). Process via PaymentProcessor with different handlers: CoinHandler, CardHandler, etc.

**Q5: How do you prevent dispensing before payment validated?**
A: State machine: Insert payment → Validate amount >= price → Unlock dispenser → Release item. Dispenser locked initially, unlocked only after validation.

### Intermediate Level

**Q6: How to handle invalid coin insertion?**
A: Validate coin denomination (0.01, 0.05, 0.10, 0.25). If invalid: reject immediately, return to user. Only accept valid coins.

**Q7: How to prevent double-dispensing (customer hits button twice)?**
A: After dispense: set item.status = SOLD_OUT temporarily. Disable button for 5 seconds (state = DISPENSING). After dispense completes: re-enable. Idempotent.

**Q8: How to handle card payment decline?**
A: Card processor returns decline. Alert customer: "Payment declined, please retry or use cash". Transaction status = FAILED. Return inserted amount (if any) and reset.

**Q9: How to track low-stock alerts?**
A: Scheduled job: every 5 minutes, check all slots. If quantity < 5: send alert to maintenance service with slot number. Log in system.

**Q10: What's stored in transaction record?**
A: Item ID, quantity, price, payment method, amount inserted, change returned, timestamp, status (SUCCESS/FAILED). Used for reconciliation + analytics.

### Advanced Level

**Q11: How to handle machine malfunction (dispenser jams)?**
A: Dispense timeout (10 seconds): if not released, mark as JAMMED. Alert maintenance. Refund customer payment. Prevent overstocking single item (max 20 per slot).

**Q12: How to implement dynamic pricing (surge pricing)?**
A: ML model: time-of-day, location, demand → adjust price. Peak hours (lunch): +20% markup. Off-peak: -10% discount. Update prices overnight batch job.

---

## Scaling Q&A (12 Questions)

**Q1: Can single machine handle 1000 transactions/day?**
A: Yes. 1000 transactions / 16 hours = 62.5 transactions/hour = 1 transaction/minute. Processing: 5 seconds per transaction. No bottleneck.

**Q2: How to handle concurrent transactions?**
A: Lock on payment processing. One customer at a time. Queue system: next customer waits. Simple serialization acceptable for vending machine use case.

**Q3: How to prevent coin jam?**
A: Coin validator: accept/reject based on weight + magnetism. Jam detection: timeout on coin insertion. If jammed: alert maintenance, refund inserted coins.

**Q4: How to reconcile cash collected?**
A: Daily report: sum of (item_price × quantity_sold). Compare to (coin_inserted + card_payments). Discrepancies = theft or malfunction. Alert manager.

**Q5: Can you support multiple vending machines?**
A: Yes. Each machine = Singleton instance (or use ID). Global VendingMachineManager tracks all machines. Dashboard: occupancy, inventory, revenue per machine.

**Q6: How to handle network failure (card payment offline)?**
A: Fallback: accept cash only. Queue card transactions in memory. When network recovers: batch process queued cards. Allow limited card transactions offline (up to $50).

**Q7: How to prevent inventory inconsistency?**
A: Pessimistic locking: on dispense, lock slot. Decrement count. Unlock. Guarantees consistency. Alternative: optimistic locking with version numbers.

**Q8: How to detect fraud (coins)?**
A: Coin validator tests weight (counterfeit = different weight). Magnetic test (fake coins non-magnetic). Reject invalid coins. Log attempts.

**Q9: Can you support subscription (weekly snacks)?**
A: Membership model: customer pays $10/week → gets daily item. Smart dispenser: verify membership on RFID card. Decrement weekly quota.

**Q10: How to optimize restocking routes?**
A: Track all machines' inventory. Route optimization: visit machines with lowest stock first. Minimize travel time. Estimate restocking need: 3 days out.

**Q11: How to implement touchless payment (COVID)?**
A: NFC payment: customer waves phone/card. No buttons touched. Reduces contamination. Integrate Apple Pay, Google Pay, contactless card readers.

**Q12: How to predict demand (supply chain)?**
A: Historical sales data: which items sell most at which times. ML model: predict demand. Pre-restock popular items before peak hours. Reduce waste.

---

## Demo Scenarios (5 Examples)

### Demo 1: Successful Purchase
```
- Customer selects Coke (Slot 3, $2.00)
- Inserts: 1×$1 + 3×$0.25 + 5×$0.01 = $1.80
- Insufficient → waits
- Inserts: 1×$0.25 = $2.05 total
- Sufficient ✓
- Dispenses Coke
- Returns: $0.05 (1×$0.05)
```

### Demo 2: Payment Decline
```
- Customer selects Chips ($1.50)
- Taps credit card
- Card processor: DECLINED
- Alert: "Payment declined"
- Customer tries again with coins
- 1×$1 + 2×$0.25 + 1×$0.01 = $1.51
- Dispenses Chips
- No change needed
```

### Demo 3: Sold Out Item
```
- Customer wants Sprite (Slot 5, quantity=0)
- Status: SOLD_OUT
- Item grayed out on display
- Customer cannot select
- Alert shown: "Out of stock"
```

### Demo 4: Change Calculation (Complex)
```
- Customer selects Water ($0.99)
- Inserts: 5×$1 = $5.00
- Change: $5.00 - $0.99 = $4.01
- Dispense: 2×$2 + 1×$0.01 = 3 coins
- Customer receives: 2 dollar bills, 1 penny
```

### Demo 5: Low Stock Alert
```
- Item: Juice, quantity = 3
- Status changes: AVAILABLE → LOW_STOCK
- Alert sent: "Slot 7 (Juice) low stock"
- Maintenance receives notification
- Next restock: prioritize Juice
```

---

## Complete Implementation

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
    
    def __new__(cls):
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

---

## Summary

✅ **Multi-payment** processing (cash, card, digital)
✅ **Accurate change** calculation with greedy algorithm
✅ **Item status** tracking (available, low-stock, sold-out)
✅ **Inventory management** with automatic restock alerts
✅ **Transaction logging** for reconciliation
✅ **State machine** for payment states
✅ **Concurrent transaction** handling
✅ **Daily reporting** (revenue, items sold)
✅ **Dynamic pricing** support
✅ **Malfunction detection** (jams, timeouts)

**Key Takeaway**: Vending machine demonstrates payment processing, inventory management, and atomic transaction handling. Core focus: validate payments, calculate change accurately, track inventory, prevent double-dispensing.
