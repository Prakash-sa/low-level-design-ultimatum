# OOP Principles: Abstraction, Encapsulation, Inheritance, Polymorphism

A practical, code-focused guide to the four pillars of Object-Oriented Programming in Python. This consolidates all relevant content and examples from the Introduction folder (no duplication, nothing missed): concepts, why-it-matters, advantages, notes, and runnable snippets including abstraction (Circle, Payment ABC), encapsulation (Movie with getters/setters and Pythonic properties), inheritance types (single, hierarchical, multilevel, multiple), and polymorphism (method overloading emulation, method overriding, operator overloading, duck typing), plus getters/setters patterns.

---

## 1) Abstraction

Abstraction simplifies complex systems by exposing only what is necessary (the "what") and hiding implementation details (the "how"). In Python, you can use simple public methods or formal abstract base classes (ABCs).

Why it matters
- Reduces cognitive load for users of a class or module.
- Encourages modular design and separation of concerns.

Real-world examples
- TV remote volume button: you press it without knowing the circuit internals.
- Vehicle accelerator: you press the pedal without engine-level details.

### Example A: Simple abstraction via public API (Circle)
```python
from math import pi

class Circle:
    def __init__(self, radius: float):
        self._radius = radius  # internal detail

    # Public API hides internal constant/implementation
    def area(self) -> float:
        return pi * self._radius ** 2

    def perimeter(self) -> float:
        return 2 * pi * self._radius

c = Circle(3)
print(c.area())      # 28.27...
print(c.perimeter()) # 18.85...
```

### Example B: Formal abstraction with ABCs (Payment)
```python
from abc import ABC, abstractmethod

class Payment(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> str:
        """Process a payment and return a status message."""
        raise NotImplementedError

class CreditCardPayment(Payment):
    def process_payment(self, amount: float) -> str:
        return f"Processing credit card payment of ${amount:.2f}"

class PayPalPayment(Payment):
    def process_payment(self, amount: float) -> str:
        return f"Processing PayPal payment of ${amount:.2f}"

# Client depends on abstraction (interface), not concrete classes
def checkout(processor: Payment, total: float) -> None:
    print(processor.process_payment(total))

checkout(CreditCardPayment(), 49.99)
checkout(PayPalPayment(), 19.00)
```

Abstraction vs Encapsulation (short)
- Abstraction: Hides implementation details and exposes a simpler interface (design-level).
- Encapsulation: Bundles data and methods and restricts direct access to internal state (access-level).

---

## 2) Encapsulation

Encapsulation bundles data and related behavior, and restricts direct access to internal state. In Python, we typically use the property pattern rather than classical getters/setters.

Why it matters
- Prevents external code from putting the object into an invalid state.
- Makes it easier to change the internal representation without breaking callers.

How to implement
- Use access modifiers by convention (`_protected`) or name-mangling for private (`__private`).
- Provide public methods (getters/setters or behavior-specific APIs) to expose only what is necessary.

Advantages
- Improves maintainability and modularity.
- Lets you enforce invariants and validation within setters.
- Supports safe refactoring of internal implementation.

### Example A: Classic getters/setters (as in repo: `encapsulation.py`)
```python
class Movie:
    def __init__(self, t: str = "", y: int = -1, g: str = ""):
        self.__title = t
        self.__year = y
        self.__genre = g

    def get_title(self) -> str:
        return self.__title

    def set_title(self, value: str) -> None:
        self.__title = value

    def get_year(self) -> int:
        return self.__year

    def set_year(self, value: int) -> None:
        self.__year = value

    def get_genre(self) -> str:
        return self.__genre

    def set_genre(self, value: str) -> None:
        self.__genre = value

    def print_details(self) -> None:
        print("Title:", self.get_title())
        print("Year:", self.get_year())
        print("Genre:", self.get_genre())

movie = Movie("The Lion King", 1994, "Adventure")
movie.print_details()
```

### Example B: Pythonic properties with validation (recommended)
```python
class Movie:
    def __init__(self, title: str, year: int, genre: str):
        self._title = title         # protected-by-convention
        self._genre = genre         # protected-by-convention
        self.year = year            # validated via property below

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value:
            raise ValueError("title cannot be empty")
        self._title = value

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        if value < 1888:  # first film around 1888
            raise ValueError("year is not realistic for a movie")
        self._year = value

m = Movie("Inception", 2010, "Sci-Fi")
print(m.title, m.year)        # Inception 2010
m.year = 2012                 # OK
# m.year = 1500               # ValueError
```

### Classic getters/setters pattern (general form)
```python
class Account:
    def __init__(self, balance: float):
        self._balance = balance

    def get_balance(self) -> float:
        return self._balance

    def set_balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("balance cannot be negative")
        self._balance = value
```

---

## 3) Inheritance

Inheritance enables reuse and extension of behavior using an IS-A relationship. Prefer composition if the relationship is not truly IS-A.

When to use
- Use inheritance to model an IS-A relationship (e.g., Car IS-A Vehicle).
- Avoid using inheritance just to reuse code; prefer composition when appropriate.

Common types of inheritance
- Single, Multiple, Multilevel, Hierarchical, Hybrid.

How to implement
- In Python, call base initialization with `super()` (or direct base call if required for MRO reasons).

Advantages
- Reusability: share common code in base classes.
- Extensibility: extend functionality in derived classes without modifying the base.
- Localized changes: updates to base behavior propagate to subclasses.

Notes and caveats
- Overuse of inheritance can lead to fragile hierarchies; prefer composition for flexible designs.

### Example A: Vehicle -> Car (override + super)
```python
class Vehicle:
    def __init__(self, make: str):
        self.make = make

    def start(self) -> str:
        return f"{self.make} vehicle starting"

class Car(Vehicle):
    def __init__(self, make: str, model: str):
        super().__init__(make)
        self.model = model

    # Extend/override behavior
    def start(self) -> str:
        base = super().start()
        return base + f"; {self.model} ready to drive"

c = Car("Toyota", "Corolla")
print(c.start())
```

Key tips:
- Model only true IS-A hierarchies (e.g., Car IS-A Vehicle).
- Use `super()` to reuse and extend base behavior cleanly.
- For flexible composition of behavior, consider delegation/strategy.

### Example B: Inheritance types demo (as in repo: `inheritance.py`)
```python
# Base class (Parent)
class Vehicle():
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def get_name(self):
        print("The car is a", self.name, self.model, end="")

# Single inheritance
class FuelCar(Vehicle):
    def __init__(self, name, model, combust_type):
        self.combust_type = combust_type
        Vehicle.__init__(self, name, model)

    def get_fuel_car(self):
        super().get_name()
        print(", combust type is", self.combust_type, end="")

# Hierarchical inheritance
class ElectricCar(Vehicle):
    def __init__(self, name, model, battery_power):
        self.battery_power = battery_power
        Vehicle.__init__(self, name, model)

    def get_electric_car(self):
        super().get_name()
        print(", battery power is", self.battery_power, end="")

# Multi-level inheritance
class GasolineCar(FuelCar):
    def __init__(self, name, model, combust_type, gas_capacity):
        self.gas_capacity = gas_capacity
        FuelCar.__init__(self, name, model, combust_type)
    
    def get_gasoline_car(self):
        super().get_fuel_car()
        print(", gas capacity is", self.gas_capacity)

# Multiple inheritance
class HybridCar(GasolineCar, ElectricCar):
    def __init__(self, name, model, combust_type, battery_power):
        FuelCar.__init__(self, name, model, combust_type)
        ElectricCar.__init__(self, name, model, battery_power)
        self.battery_power = battery_power

    def get_hybrid(self):
        self.get_fuel_car()
        print(", battery power is", self.battery_power)

# Demo
Fuel = FuelCar("Honda", "Accord", "Petrol"); Fuel.get_fuel_car(); print()
Electric = ElectricCar("Tesla", "ModelX", "200MWH"); Electric.get_electric_car(); print()
Gasoline = GasolineCar("Toyota", "Corolla", "Gasoline", "30 liters"); Gasoline.get_gasoline_car()
Hybrid = HybridCar("Toyota", "Prius", "Hybrid", "100MWH"); Hybrid.get_hybrid()
```

---

## 4) Polymorphism

Polymorphism allows different types to be used through the same interface, each providing its own behavior.

Why it matters
- Enables generic code that operates on abstractions (interfaces/base classes) while allowing concrete classes to provide specialized behavior.
- Improves extensibility and decouples code that uses objects from the object's specific implementation.

Types
- Static (compile-time) polymorphism (method overloading, operator overloading where the language supports it).
- Dynamic (runtime) polymorphism (method overriding in a class hierarchy).

### Example A: Method overloading (Python emulation via defaults/kwargs)
```python
class Sum:
    def addition(self, a, b, c=0):
        return a + b + c

s = Sum()
print(s.addition(14, 35))       # 49
print(s.addition(31, 34, 43))   # 108

class Area:
    def calculateArea(self, length, breadth=-1):
        if breadth != -1:
            return length * breadth
        else:
            return length * length

area = Area()
print(area.calculateArea(3, 4))  # rectangle: 12
print(area.calculateArea(6))     # square: 36
```

### Example B: Overriding (runtime polymorphism)
```python
class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"

class Cat(Animal):
    def speak(self) -> str:
        return "Meow!"

# Works uniformly on base type

def make_it_speak(a: Animal) -> None:
    print(a.speak())

make_it_speak(Dog())
make_it_speak(Cat())
```

### Example C: Duck typing (no inheritance required)
```python
class Robot:
    def speak(self) -> str:
        return "Beep!"

# Any object with .speak() works
for obj in (Dog(), Cat(), Robot()):
    print(obj.speak())
```

### Example D: Operator overloading (`__add__`)
```python
class ComplexNumber:
    def __init__(self):
        self.real = 0
        self.imaginary = 0

    def set_value(self, real, imaginary):
        self.real = real
        self.imaginary = imaginary

    def __add__(self, c):
        result = ComplexNumber()
        result.real = self.real + c.real
        result.imaginary = self.imaginary + c.imaginary
        return result

    def display(self):
        print(f"({self.real} + {self.imaginary}i)")

c1 = ComplexNumber(); c1.set_value(11, 5)
c2 = ComplexNumber(); c2.set_value(2, 6)
c3 = c1 + c2
c3.display()  # (13 + 11i)
```

Optional note:
- Python does not support true method overloading by signature like Java/C++; you can emulate via default parameters, `*args/**kwargs`, or `functools.singledispatch` for function-based overloading.

---

## Getters and Setters in Python (Patterns)

Pythonic approach favors properties over explicit `get_*/set_*` methods.

### Property pattern (recommended)
```python
class User:
    def __init__(self, email: str):
        self.email = email  # validated via property

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError("invalid email")
        self._email = value

u = User("alice@example.com")
# u.email = "bad"   # ValueError
```

### Explicit getters/setters (when interoperating with non-Pythonic APIs)
```python
class Settings:
    def __init__(self):
        self._debug = False

    def get_debug(self) -> bool:
        return self._debug

    def set_debug(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("debug must be bool")
        self._debug = value
```

### Read-only property
```python
class Order:
    def __init__(self, order_id: str):
        self._order_id = order_id

    @property
    def order_id(self) -> str:
        return self._order_id  # no setter => read-only
```

---

## Quick Recap

- **Abstraction**: Expose intent through a minimal API; hide details (use ABCs when contracts matter).
- **Encapsulation**: Protect invariants; validate via `@property` setters; avoid leaking internal state.
- **Inheritance**: Model true IS-A; use `super()`; prefer composition for flexibility.
- **Polymorphism**: Program to interfaces; rely on overriding and duck typing in Python.
- **Getters/Setters**: Use `@property` for Pythonic access, with validation; fall back to explicit methods only when necessary.
