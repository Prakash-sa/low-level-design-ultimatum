# Decorator Pattern

> Attach additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality.

---

## Problem

You want to add new functionality to objects without modifying their classes. Inheritance isn't flexible enough because you'd need many subclasses for each combination.

## Solution

The Decorator pattern uses composition to wrap objects with decorators that add new functionality.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import Optional

# ============ COFFEE DECORATOR EXAMPLE ============

class Beverage(ABC):
    """Component - base interface"""
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    def get_cost(self) -> float:
        pass

class SimpleCoffee(Beverage):
    """Concrete Component - simple beverage"""
    
    def get_description(self) -> str:
        return "Simple Coffee"
    
    def get_cost(self) -> float:
        return 2.0

class BeverageDecorator(Beverage):
    """Abstract Decorator - wraps a beverage"""
    
    def __init__(self, beverage: Beverage):
        self.beverage = beverage

class MilkDecorator(BeverageDecorator):
    """Concrete Decorator - adds milk"""
    
    def get_description(self) -> str:
        return self.beverage.get_description() + ", Milk"
    
    def get_cost(self) -> float:
        return self.beverage.get_cost() + 0.5

class SugarDecorator(BeverageDecorator):
    """Concrete Decorator - adds sugar"""
    
    def get_description(self) -> str:
        return self.beverage.get_description() + ", Sugar"
    
    def get_cost(self) -> float:
        return self.beverage.get_cost() + 0.25

class ChocolateDecorator(BeverageDecorator):
    """Concrete Decorator - adds chocolate"""
    
    def get_description(self) -> str:
        return self.beverage.get_description() + ", Chocolate"
    
    def get_cost(self) -> float:
        return self.beverage.get_cost() + 1.0

# ============ I/O STREAMS DECORATOR EXAMPLE ============

class DataStream(ABC):
    @abstractmethod
    def read(self) -> str:
        pass
    
    @abstractmethod
    def write(self, data: str):
        pass

class FileStream(DataStream):
    """Concrete Component - raw file stream"""
    
    def __init__(self, filename: str):
        self.filename = filename
    
    def read(self) -> str:
        return f"Reading from {self.filename}"
    
    def write(self, data: str):
        print(f"Writing to {self.filename}: {data}")

class StreamDecorator(DataStream):
    """Abstract Decorator"""
    
    def __init__(self, stream: DataStream):
        self.stream = stream

class BufferedStream(StreamDecorator):
    """Decorator - adds buffering"""
    
    def __init__(self, stream: DataStream):
        super().__init__(stream)
        self.buffer = []
    
    def read(self) -> str:
        return f"[BUFFERED] {self.stream.read()}"
    
    def write(self, data: str):
        self.buffer.append(data)
        if len(self.buffer) >= 3:
            print(f"Flushing buffer: {self.buffer}")
            self.buffer = []

class EncryptedStream(StreamDecorator):
    """Decorator - adds encryption"""
    
    def read(self) -> str:
        return f"[DECRYPTED] {self.stream.read()}"
    
    def write(self, data: str):
        encrypted = data.encode("rot13")  # Simple encryption
        self.stream.write(encrypted)

class CompressedStream(StreamDecorator):
    """Decorator - adds compression"""
    
    def read(self) -> str:
        return f"[DECOMPRESSED] {self.stream.read()}"
    
    def write(self, data: str):
        compressed = f"[COMPRESSED: {len(data)} -> {len(data)//2} bytes]"
        self.stream.write(compressed)

# ============ PIZZA DECORATOR EXAMPLE ============

class Pizza(ABC):
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    def get_price(self) -> float:
        pass

class BasicPizza(Pizza):
    def get_description(self) -> str:
        return "Basic Pizza"
    
    def get_price(self) -> float:
        return 5.0

class PizzaDecorator(Pizza):
    def __init__(self, pizza: Pizza):
        self.pizza = pizza

class CheeseTopping(PizzaDecorator):
    def get_description(self) -> str:
        return self.pizza.get_description() + " + Cheese"
    
    def get_price(self) -> float:
        return self.pizza.get_price() + 1.0

class PepperoniTopping(PizzaDecorator):
    def get_description(self) -> str:
        return self.pizza.get_description() + " + Pepperoni"
    
    def get_price(self) -> float:
        return self.pizza.get_price() + 1.5

class MushroomTopping(PizzaDecorator):
    def get_description(self) -> str:
        return self.pizza.get_description() + " + Mushroom"
    
    def get_price(self) -> float:
        return self.pizza.get_price() + 0.75

# ============ WINDOW DECORATOR EXAMPLE ============

class Window(ABC):
    @abstractmethod
    def render(self):
        pass

class SimpleWindow(Window):
    def render(self):
        print("Rendering Simple Window")

class WindowDecorator(Window):
    def __init__(self, window: Window):
        self.window = window

class VerticalScrollBar(WindowDecorator):
    def render(self):
        self.window.render()
        print("  + Adding Vertical Scrollbar")

class HorizontalScrollBar(WindowDecorator):
    def render(self):
        self.window.render()
        print("  + Adding Horizontal Scrollbar")

class BorderDecorator(WindowDecorator):
    def render(self):
        self.window.render()
        print("  + Adding Border")

# Demo
if __name__ == "__main__":
    print("=== Coffee Decorator ===")
    
    # Plain coffee
    coffee = SimpleCoffee()
    print(f"{coffee.get_description()}: ${coffee.get_cost()}")
    
    # Coffee with milk
    coffee = MilkDecorator(SimpleCoffee())
    print(f"{coffee.get_description()}: ${coffee.get_cost()}")
    
    # Coffee with milk and sugar
    coffee = SugarDecorator(MilkDecorator(SimpleCoffee()))
    print(f"{coffee.get_description()}: ${coffee.get_cost()}")
    
    # Coffee with milk, sugar, and chocolate
    coffee = ChocolateDecorator(
        SugarDecorator(MilkDecorator(SimpleCoffee()))
    )
    print(f"{coffee.get_description()}: ${coffee.get_cost()}\n")
    
    print("=== Pizza Toppings ===")
    pizza = BasicPizza()
    print(f"{pizza.get_description()}: ${pizza.get_price()}")
    
    pizza = CheeseTopping(BasicPizza())
    print(f"{pizza.get_description()}: ${pizza.get_price()}")
    
    pizza = PepperoniTopping(CheeseTopping(BasicPizza()))
    print(f"{pizza.get_description()}: ${pizza.get_price()}")
    
    pizza = MushroomTopping(PepperoniTopping(CheeseTopping(BasicPizza())))
    print(f"{pizza.get_description()}: ${pizza.get_price()}\n")
    
    print("=== Stream Decorators ===")
    file = FileStream("data.txt")
    print(file.read())
    
    buffered = BufferedStream(file)
    print(buffered.read())
    
    encrypted = EncryptedStream(file)
    encrypted.write("Secret message")
    
    compressed = CompressedStream(file)
    compressed.write("Large data here")
    print()
    
    print("=== Window Decorators ===")
    window = SimpleWindow()
    window.render()
    print()
    
    window = VerticalScrollBar(SimpleWindow())
    window.render()
    print()
    
    window = BorderDecorator(
        HorizontalScrollBar(
            VerticalScrollBar(SimpleWindow())
        )
    )
    window.render()
```

---

## Key Concepts

- **Component**: Common interface for original and decorated objects
- **Concrete Component**: Base object that can be decorated
- **Decorator**: Abstract class wrapping component
- **Concrete Decorators**: Add specific functionality
- **Composition over Inheritance**: Flexible functionality addition
- **Runtime stacking**: Decorators can be stacked in any order

---

## When to Use

✅ Add responsibilities to objects dynamically  
✅ Avoid class explosion from inheritance  
✅ Add/remove features at runtime  
✅ Need flexible combinations of features  

---

## Interview Q&A

**Q1: What's the difference between Decorator and Proxy?**

A:
- **Decorator**: Adds NEW functionality. Enhances behavior.
- **Proxy**: Controls access. Manages behavior.

```python
# Decorator: Adds functionality
class LoggingDecorator:
    def operation(self):
        print("Logging...")
        self.obj.operation()  # Then do original

# Proxy: Controls access
class ProxyUser:
    def operation(self):
        if self.has_permission():  # Check first
            self.obj.operation()
```

---

**Q2: What's the difference between Decorator and Composite?**

A:
- **Composite**: Tree structure, represents hierarchies
- **Decorator**: Linear wrapping, adds functionality

```python
# Composite: Tree
folder.add(subfolder)
folder.add(file)

# Decorator: Linear chain
decorated = Decorator1(Decorator2(Decorator3(object)))
```

---

**Q3: How would you handle decorator removal?**

A:
```python
class RemovableDecorator(Beverage):
    def __init__(self, beverage: Beverage):
        self.beverage = beverage
    
    def remove_decorator(self) -> Beverage:
        return self.beverage

# Usage
coffee = MilkDecorator(SimpleCoffee())
plain_coffee = coffee.remove_decorator()
```

---

**Q4: How would you prevent infinite decorator chains?**

A:
```python
class RestrictedDecorator(Beverage):
    def __init__(self, beverage: Beverage):
        if isinstance(beverage, RestrictedDecorator):
            raise TypeError("Cannot nest RestrictedDecorator")
        self.beverage = beverage
```

---

**Q5: How would you test decorated objects?**

A:
```python
from unittest.mock import Mock

# Create mock component
mock_beverage = Mock(spec=Beverage)
mock_beverage.get_description.return_value = "Mock"
mock_beverage.get_cost.return_value = 1.0

# Test decorator with mock
decorated = MilkDecorator(mock_beverage)
assert "Milk" in decorated.get_description()
assert decorated.get_cost() == 1.5
```

---

## Trade-offs

✅ **Pros**: Flexible, avoids inheritance explosion, add/remove at runtime  
❌ **Cons**: Complex object creation, many small classes, hard to debug

---

## Real-World Examples

- **Java I/O Streams** (BufferedInputStream, DataInputStream, etc.)
- **Text editors** (spell check, grammar check, formatting decorators)
- **UI frameworks** (scrollbars, borders, shadows on windows)
- **HTTP clients** (logging, compression, encryption decorators)
