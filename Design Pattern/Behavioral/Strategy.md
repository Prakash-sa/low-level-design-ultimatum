# Strategy Pattern

> Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.

---

## Problem

You have a class that needs to perform an algorithm, but the algorithm can vary based on context. You want to avoid hardcoding different algorithms in many conditional branches.

## Solution

The Strategy pattern extracts algorithms into separate Strategy classes that implement a common interface. The context uses the appropriate strategy at runtime.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import List

# Strategy interface
class FilterStrategy(ABC):
    @abstractmethod
    def should_remove(self, value: int) -> bool:
        pass

# Concrete Strategies
class RemoveNegativeStrategy(FilterStrategy):
    def should_remove(self, value: int) -> bool:
        return value < 0

class RemoveOddStrategy(FilterStrategy):
    def should_remove(self, value: int) -> bool:
        return abs(value) % 2 == 1

class RemoveEvenStrategy(FilterStrategy):
    def should_remove(self, value: int) -> bool:
        return value % 2 == 0

class RemoveMultiplesStrategy(FilterStrategy):
    def __init__(self, divisor: int):
        self.divisor = divisor
    
    def should_remove(self, value: int) -> bool:
        return value % self.divisor == 0

# Context
class ValueFilter:
    def __init__(self, strategy: FilterStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: FilterStrategy):
        self.strategy = strategy
    
    def filter(self, values: List[int]) -> List[int]:
        return [v for v in values if not self.strategy.should_remove(v)]

# Payment Strategy example
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

class CreditCardPayment(PaymentStrategy):
    def __init__(self, card_number: str):
        self.card_number = card_number
    
    def pay(self, amount: float) -> bool:
        print(f"Processing credit card payment of ${amount} with card {self.card_number[-4:]}")
        return True

class PayPalPayment(PaymentStrategy):
    def __init__(self, email: str):
        self.email = email
    
    def pay(self, amount: float) -> bool:
        print(f"Processing PayPal payment of ${amount} to {self.email}")
        return True

class CryptocurrencyPayment(PaymentStrategy):
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
    
    def pay(self, amount: float) -> bool:
        print(f"Processing crypto payment of ${amount} to {self.wallet_address}")
        return True

class ShoppingCart:
    def __init__(self, payment_strategy: PaymentStrategy):
        self.items = []
        self.payment_strategy = payment_strategy
    
    def set_payment_strategy(self, strategy: PaymentStrategy):
        self.payment_strategy = strategy
    
    def add_item(self, price: float):
        self.items.append(price)
    
    def checkout(self) -> bool:
        total = sum(self.items)
        return self.payment_strategy.pay(total)

# Demo
if __name__ == "__main__":
    # Filter example
    print("=== Filter Strategy ===")
    values = [-7, -4, 0, 2, 5, 6, 9]
    
    filter_obj = ValueFilter(RemoveNegativeStrategy())
    print(f"Original: {values}")
    print(f"Remove negatives: {filter_obj.filter(values)}")
    
    filter_obj.set_strategy(RemoveOddStrategy())
    print(f"Remove odd: {filter_obj.filter(values)}")
    
    filter_obj.set_strategy(RemoveMultiplesStrategy(3))
    print(f"Remove multiples of 3: {filter_obj.filter(values)}\n")
    
    # Payment example
    print("=== Payment Strategy ===")
    cart = ShoppingCart(CreditCardPayment("1234-5678-9012-3456"))
    cart.add_item(29.99)
    cart.add_item(15.50)
    
    print("Using Credit Card:")
    cart.checkout()
    
    cart.set_payment_strategy(PayPalPayment("user@example.com"))
    print("\nUsing PayPal:")
    cart.checkout()
    
    cart.set_payment_strategy(CryptocurrencyPayment("0x1234..."))
    print("\nUsing Cryptocurrency:")
    cart.checkout()
```

---

## Key Concepts

- **Strategy**: Abstract algorithm interface
- **Concrete Strategy**: Implementation of specific algorithm
- **Context**: Uses a strategy to perform work
- **Runtime Selection**: Strategy chosen at runtime, not compile time

---

## When to Use

✅ Multiple algorithms for a task (sorting, filtering, payment)  
✅ Want to avoid massive if-else chains  
✅ Need to switch algorithms at runtime  
✅ Different implementations for different contexts  

---

## Interview Q&A

**Q1: What's the difference between Strategy and State patterns?**

A:
- **Strategy**: Client chooses which algorithm to use. All strategies are valid anytime.
- **State**: Object's internal state determines which behavior to use. State transitions follow rules.

```python
# Strategy: Client decides
calculator.set_strategy(AddStrategy())  # Client picks

# State: State machine decides
traffic_light.change()  # Transitions: RED → GREEN → YELLOW → RED
```

---

**Q2: How would you implement a sorting strategy?**

A:
```python
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: List[int]) -> List[int]:
        pass

class BubbleSortStrategy(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        # Bubble sort implementation
        arr = data.copy()
        for i in range(len(arr)):
            for j in range(len(arr) - 1 - i):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

class QuickSortStrategy(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        if len(data) <= 1:
            return data
        pivot = data[len(data) // 2]
        left = [x for x in data if x < pivot]
        middle = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + middle + self.sort(right)

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self.strategy = strategy
    
    def sort(self, data: List[int]) -> List[int]:
        return self.strategy.sort(data)

# Usage
sorter = Sorter(QuickSortStrategy())
print(sorter.sort([3, 1, 4, 1, 5]))  # [1, 1, 3, 4, 5]
```

---

**Q3: How would you combine Strategy with Factory patterns?**

A:
```python
class StrategyFactory:
    @staticmethod
    def create_filter_strategy(strategy_name: str) -> FilterStrategy:
        strategies = {
            "negative": RemoveNegativeStrategy,
            "odd": RemoveOddStrategy,
            "even": RemoveEvenStrategy,
        }
        strategy_class = strategies.get(strategy_name)
        if strategy_class:
            return strategy_class()
        raise ValueError(f"Unknown strategy: {strategy_name}")

# Usage
strategy = StrategyFactory.create_filter_strategy("odd")
filter_obj = ValueFilter(strategy)
```

---

**Q4: What happens if you need context-specific data in a strategy?**

A: Pass context data to the strategy method:

```python
class Strategy(ABC):
    @abstractmethod
    def execute(self, context_data: Dict[str, Any]) -> Any:
        pass

class ConcreteStrategy(Strategy):
    def execute(self, context_data: Dict[str, Any]) -> Any:
        user_level = context_data.get("user_level")
        price = context_data.get("price")
        
        if user_level == "premium":
            return price * 0.8  # 20% discount
        return price
```

---

**Q5: How would you handle strategy-specific configuration?**

A:
```python
class Strategy(ABC):
    @abstractmethod
    def execute(self, data: Any) -> Any:
        pass

class ConfigurableStrategy(Strategy):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def execute(self, data: Any) -> Any:
        threshold = self.config.get("threshold", 0)
        return [x for x in data if x > threshold]

# Usage
strategy = ConfigurableStrategy({"threshold": 5})
```

---

## Trade-offs

✅ **Pros**: Easy to add new algorithms, avoids large conditionals, runtime selection  
❌ **Cons**: Extra classes, memory overhead for simple algorithms, overkill if only 1-2 strategies

---

## Real-World Examples

- **Compression algorithms** (ZIP, RAR, 7Z)
- **Payment methods** (Credit card, PayPal, Crypto)
- **Sorting algorithms** (Quick sort, Merge sort, Bubble sort)
- **Caching strategies** (LRU, LFU, FIFO)
