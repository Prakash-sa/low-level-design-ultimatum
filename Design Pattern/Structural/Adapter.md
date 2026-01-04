# Adapter Pattern

> Convert the interface of a class into another interface clients expect. Adapter lets classes work together that couldn't otherwise because of incompatible interfaces.

---

## Problem

You have existing code that uses one interface, but you need to integrate it with another component that expects a different interface. You don't want to modify the existing code.

## Solution

The Adapter pattern converts one interface to another by wrapping the incompatible component.

---

## Implementation

```python
from abc import ABC, abstractmethod

# ============ OLD INTERFACE (Existing code) ============

class LegacyPaymentProcessor:
    """Old payment system with different interface"""
    
    def process_payment(self, amount: float) -> dict:
        # Returns dict instead of boolean
        return {
            "status": "completed",
            "amount": amount,
            "transaction_id": "TXN-12345"
        }

# ============ NEW INTERFACE (What we want) ============

class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

# ============ CLASS ADAPTER (Inheritance) ============

class LegacyPaymentAdapter(PaymentProcessor, LegacyPaymentProcessor):
    """Inherits from both old implementation and new interface"""
    
    def pay(self, amount: float) -> bool:
        # Adapt old method to new interface
        result = self.process_payment(amount)
        return result["status"] == "completed"

# ============ OBJECT ADAPTER (Composition) ============

class PaymentAdapterComposition(PaymentProcessor):
    """Uses composition - more flexible"""
    
    def __init__(self, legacy_processor: LegacyPaymentProcessor):
        self.legacy_processor = legacy_processor
    
    def pay(self, amount: float) -> bool:
        result = self.legacy_processor.process_payment(amount)
        return result["status"] == "completed"

# ============ TWO-WAY ADAPTER ============

class StandardPaymentGateway(PaymentProcessor):
    def pay(self, amount: float) -> bool:
        print(f"Processing payment of ${amount}")
        return True

class TwoWayAdapter(PaymentProcessor):
    """Adapts between StandardPaymentGateway and LegacyPaymentProcessor"""
    
    def __init__(self, target=None):
        self.target = target
    
    def pay(self, amount: float) -> bool:
        if isinstance(self.target, LegacyPaymentProcessor):
            result = self.target.process_payment(amount)
            return result["status"] == "completed"
        elif isinstance(self.target, StandardPaymentGateway):
            return self.target.pay(amount)
        return False

# ============ REAL-WORLD EXAMPLE: USB Adapters ============

class ElectricDevice(ABC):
    @abstractmethod
    def use_electricity(self, voltage: int):
        pass

class EuropeanSocket:
    """European 220V socket"""
    def provide_electricity(self):
        return 220

class AmericanSocket:
    """American 110V socket"""
    def provide_electricity(self):
        return 110

class Laptop(ElectricDevice):
    def use_electricity(self, voltage: int):
        if voltage in [100, 240]:  # Accepts 100-240V
            print(f"Laptop charging at {voltage}V")
        else:
            print(f"Laptop cannot charge at {voltage}V")

class Adapter110to220(ElectricDevice):
    """Adapts 110V American to 220V European requirement"""
    
    def __init__(self, american_socket: AmericanSocket):
        self.american_socket = american_socket
    
    def use_electricity(self, voltage: int):
        original_voltage = self.american_socket.provide_electricity()
        # Step up voltage
        adapted_voltage = original_voltage * 2
        print(f"Adapter converting {original_voltage}V to {adapted_voltage}V")
        return adapted_voltage

# ============ MULTIPLE INHERITANCE ADAPTER ============

class OldLogSystem:
    def log(self, msg: str):
        print(f"[OLD LOG] {msg}")

class NewLogInterface(ABC):
    @abstractmethod
    def debug(self, msg: str):
        pass
    
    @abstractmethod
    def error(self, msg: str):
        pass

class LogAdapter(NewLogInterface):
    def __init__(self, old_logger: OldLogSystem):
        self.old_logger = old_logger
    
    def debug(self, msg: str):
        self.old_logger.log(f"DEBUG: {msg}")
    
    def error(self, msg: str):
        self.old_logger.log(f"ERROR: {msg}")

# ============ ADAPTER FOR COLLECTIONS ============

class OldDataStore:
    """Returns data as list"""
    def get_data(self):
        return [1, 2, 3, 4, 5]

class CollectionInterface(ABC):
    @abstractmethod
    def iterate(self):
        pass

class CollectionAdapter(CollectionInterface):
    def __init__(self, old_store: OldDataStore):
        self.old_store = old_store
    
    def iterate(self):
        # Adapt list to iterable interface
        for item in self.old_store.get_data():
            yield item

# Demo
if __name__ == "__main__":
    print("=== Class Adapter (Inheritance) ===")
    legacy = LegacyPaymentProcessor()
    adapter = LegacyPaymentAdapter()
    result = adapter.pay(100.0)
    print(f"Payment processed: {result}\n")
    
    print("=== Object Adapter (Composition) ===")
    legacy = LegacyPaymentProcessor()
    adapter = PaymentAdapterComposition(legacy)
    result = adapter.pay(100.0)
    print(f"Payment processed: {result}\n")
    
    print("=== Two-Way Adapter ===")
    legacy = LegacyPaymentProcessor()
    adapter = TwoWayAdapter(legacy)
    result = adapter.pay(100.0)
    print(f"Payment processed: {result}\n")
    
    print("=== Voltage Adapter ===")
    american_socket = AmericanSocket()
    adapter = Adapter110to220(american_socket)
    voltage = adapter.use_electricity(110)
    
    laptop = Laptop()
    laptop.use_electricity(voltage)
    print()
    
    print("=== Log Adapter ===")
    old_logger = OldLogSystem()
    log_adapter = LogAdapter(old_logger)
    log_adapter.debug("This is a debug message")
    log_adapter.error("This is an error message")
    print()
    
    print("=== Collection Adapter ===")
    store = OldDataStore()
    collection = CollectionAdapter(store)
    print("Iterating adapted collection:")
    for item in collection.iterate():
        print(f"  Item: {item}")
```

---

## Key Concepts

- **Class Adapter**: Uses inheritance to adapt incompatible interfaces
- **Object Adapter**: Uses composition (wrapper) for flexibility
- **Two-Way Adapter**: Adapts between two incompatible interfaces
- **Transparent**: Client doesn't know about adaptation

---

## When to Use

✅ Need to integrate legacy code with new code  
✅ Incompatible interfaces need to work together  
✅ Want to decouple client from incompatible components  
✅ Reuse existing classes with incompatible interfaces  

---

## Interview Q&A

**Q1: What's the difference between Adapter and Decorator?**

A:
- **Adapter**: Converts incompatible interfaces. Interface mismatch problem.
- **Decorator**: Adds new behavior without changing interface. Enhancement.

```python
# Adapter: Changes interface
class LegacyAdapter(PaymentProcessor):
    def pay(self, amount):
        return legacy.process_payment(amount)  # Different interface

# Decorator: Same interface, adds behavior
class LoggingDecorator(PaymentProcessor):
    def __init__(self, processor):
        self.processor = processor
    
    def pay(self, amount):
        print(f"Logging payment of {amount}")  # Added behavior
        return self.processor.pay(amount)  # Same interface
```

---

**Q2: When would you use Class Adapter vs Object Adapter?**

A:
- **Class Adapter**: Simpler, single inheritance. Not extensible.
- **Object Adapter**: More flexible, can adapt multiple types.

```python
# Class Adapter (single inheritance)
class PaymentAdapter(PaymentProcessor, LegacyPaymentProcessor):
    pass

# Object Adapter (composition)
class PaymentAdapter:
    def __init__(self, legacy):
        self.legacy = legacy
```

---

**Q3: How would you handle a many-to-one adapter?**

A:
```python
class UniversalAdapter:
    """Adapts multiple old interfaces to one new interface"""
    
    def __init__(self, adaptee):
        self.adaptee = adaptee
    
    def pay(self, amount: float) -> bool:
        if hasattr(self.adaptee, 'process_payment'):  # Type 1
            result = self.adaptee.process_payment(amount)
            return result.get("status") == "completed"
        elif hasattr(self.adaptee, 'charge'):  # Type 2
            return self.adaptee.charge(amount)
        elif hasattr(self.adaptee, 'transfer'):  # Type 3
            return self.adaptee.transfer(amount)
        return False
```

---

**Q4: How would you adapt a database driver?**

A:
```python
class OldDatabaseDriver:
    def executeQuery(self, query):
        return {"results": []}

class DatabaseInterface(ABC):
    @abstractmethod
    def execute(self, query: str):
        pass

class DatabaseAdapter(DatabaseInterface):
    def __init__(self, old_driver):
        self.old_driver = old_driver
    
    def execute(self, query: str):
        return self.old_driver.executeQuery(query).get("results")
```

---

**Q5: How would you test Adapter code?**

A:
```python
class MockLegacyProcessor:
    def process_payment(self, amount):
        return {"status": "completed", "amount": amount}

# Test adapter
adapter = PaymentAdapterComposition(MockLegacyProcessor())
assert adapter.pay(100.0) == True

# Test with new interface
new_payment = StandardPaymentGateway()
adapter2 = TwoWayAdapter(new_payment)
assert adapter2.pay(100.0) == True
```

---

## Trade-offs

✅ **Pros**: Integrates incompatible components, doesn't modify existing code, reusable  
❌ **Cons**: Extra complexity, inheritance issues (with class adapter)

---

## Real-World Examples

- **USB adapters** (USB-C to USB-A)
- **Database drivers** (adapting different DB APIs)
- **Payment gateways** (Stripe, PayPal, Square)
- **Legacy code integration** (mainframe to cloud)
