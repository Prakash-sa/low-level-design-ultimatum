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
