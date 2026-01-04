# Builder Pattern

> Separate the construction of a complex object from its representation so that the same construction process can create different representations.

---

## Problem

An object has many optional parameters, and constructors become unwieldy. You want to construct complex objects step by step with a clean API.

## Solution

The Builder pattern separates construction logic into a builder class, allowing step-by-step object creation and method chaining.

---

## Implementation

```python
from typing import Optional, List

# ============ BASIC BUILDER ============

class Burger:
    def __init__(self):
        self.buns: Optional[str] = None
        self.patty: Optional[str] = None
        self.cheese: Optional[str] = None
        self.lettuce: bool = False
        self.tomato: bool = False
        self.onion: bool = False
    
    def __str__(self) -> str:
        parts = [self.buns, self.patty, self.cheese]
        if self.lettuce:
            parts.append("lettuce")
        if self.tomato:
            parts.append("tomato")
        if self.onion:
            parts.append("onion")
        return f"Burger({', '.join(p for p in parts if p)})"

class BurgerBuilder:
    def __init__(self):
        self.burger = Burger()
    
    def add_buns(self, bun_style: str) -> 'BurgerBuilder':
        self.burger.buns = bun_style
        return self  # Enable chaining
    
    def add_patty(self, patty_style: str) -> 'BurgerBuilder':
        self.burger.patty = patty_style
        return self
    
    def add_cheese(self, cheese_style: str) -> 'BurgerBuilder':
        self.burger.cheese = cheese_style
        return self
    
    def add_lettuce(self) -> 'BurgerBuilder':
        self.burger.lettuce = True
        return self
    
    def add_tomato(self) -> 'BurgerBuilder':
        self.burger.tomato = True
        return self
    
    def add_onion(self) -> 'BurgerBuilder':
        self.burger.onion = True
        return self
    
    def build(self) -> Burger:
        return self.burger

# ============ BUILDER WITH VALIDATION ============

class House:
    def __init__(self, foundation: str, walls: str, roof: str, 
                 rooms: int, garage: bool):
        self.foundation = foundation
        self.walls = walls
        self.roof = roof
        self.rooms = rooms
        self.garage = garage
    
    def __str__(self) -> str:
        return (f"House(foundation={self.foundation}, walls={self.walls}, "
                f"roof={self.roof}, rooms={self.rooms}, garage={self.garage})")

class HouseBuilder:
    def __init__(self):
        self.foundation = "concrete"
        self.walls = "brick"
        self.roof = "tiles"
        self.rooms = 4
        self.garage = False
    
    def set_foundation(self, foundation: str) -> 'HouseBuilder':
        if foundation not in ["concrete", "stone", "wood"]:
            raise ValueError(f"Invalid foundation: {foundation}")
        self.foundation = foundation
        return self
    
    def set_walls(self, walls: str) -> 'HouseBuilder':
        if walls not in ["brick", "wood", "stone"]:
            raise ValueError(f"Invalid walls: {walls}")
        self.walls = walls
        return self
    
    def set_roof(self, roof: str) -> 'HouseBuilder':
        if roof not in ["tiles", "metal", "shingles"]:
            raise ValueError(f"Invalid roof: {roof}")
        self.roof = roof
        return self
    
    def set_rooms(self, rooms: int) -> 'HouseBuilder':
        if rooms < 1 or rooms > 10:
            raise ValueError(f"Invalid rooms: {rooms}")
        self.rooms = rooms
        return self
    
    def set_garage(self, has_garage: bool) -> 'HouseBuilder':
        self.garage = has_garage
        return self
    
    def build(self) -> House:
        return House(self.foundation, self.walls, self.roof, 
                    self.rooms, self.garage)

# ============ BUILDER WITH DIRECTOR ============

class Car:
    def __init__(self):
        self.engine: Optional[str] = None
        self.wheels: Optional[int] = None
        self.transmission: Optional[str] = None
        self.interior: Optional[str] = None
    
    def __str__(self) -> str:
        return (f"Car(engine={self.engine}, wheels={self.wheels}, "
                f"transmission={self.transmission}, interior={self.interior})")

class CarBuilder:
    def __init__(self):
        self.car = Car()
    
    def set_engine(self, engine: str) -> 'CarBuilder':
        self.car.engine = engine
        return self
    
    def set_wheels(self, wheels: int) -> 'CarBuilder':
        self.car.wheels = wheels
        return self
    
    def set_transmission(self, transmission: str) -> 'CarBuilder':
        self.car.transmission = transmission
        return self
    
    def set_interior(self, interior: str) -> 'CarBuilder':
        self.car.interior = interior
        return self
    
    def build(self) -> Car:
        return self.car

class CarDirector:
    """Encapsulates construction steps for different car types"""
    
    @staticmethod
    def build_sports_car(builder: CarBuilder) -> Car:
        return (builder
                .set_engine("V8 Turbo")
                .set_wheels(20)
                .set_transmission("Manual")
                .set_interior("Leather")
                .build())
    
    @staticmethod
    def build_family_car(builder: CarBuilder) -> Car:
        return (builder
                .set_engine("V4")
                .set_wheels(17)
                .set_transmission("Automatic")
                .set_interior("Cloth")
                .build())
    
    @staticmethod
    def build_electric_car(builder: CarBuilder) -> Car:
        return (builder
                .set_engine("Electric")
                .set_wheels(18)
                .set_transmission("Automatic")
                .set_interior("Premium")
                .build())

# Demo
if __name__ == "__main__":
    print("=== Basic Builder ===")
    burger = (BurgerBuilder()
              .add_buns("sesame")
              .add_patty("beef")
              .add_cheese("cheddar")
              .add_lettuce()
              .add_tomato()
              .build())
    print(burger)
    print()
    
    print("=== Builder with Validation ===")
    house = (HouseBuilder()
             .set_foundation("stone")
             .set_walls("brick")
             .set_roof("metal")
             .set_rooms(5)
             .set_garage(True)
             .build())
    print(house)
    print()
    
    print("=== Builder with Director ===")
    builder = CarBuilder()
    
    sports_car = CarDirector.build_sports_car(builder)
    print("Sports Car:", sports_car)
    
    builder = CarBuilder()  # Reset for next car
    family_car = CarDirector.build_family_car(builder)
    print("Family Car:", family_car)
    
    builder = CarBuilder()
    electric_car = CarDirector.build_electric_car(builder)
    print("Electric Car:", electric_car)
```

---

## Key Concepts

- **Builder**: Constructs complex objects step by step
- **Method Chaining**: Returns `self` to enable fluent API
- **Director**: Encapsulates construction sequences for different variations
- **Separation**: Decouples construction from representation

---

## When to Use

✅ Objects with many optional parameters  
✅ Want to construct complex objects step by step  
✅ Need multiple representations of the same type  
✅ Want immutable objects with fluent API  

---

## Interview Q&A

**Q1: What's the difference between Builder and Factory patterns?**

A:
- **Builder**: Step-by-step construction. Good for complex objects with many variations.
- **Factory**: One-shot object creation. Good for simple objects or type selection.

```python
# Factory: One shot
burger = BurgerFactory.create("special")

# Builder: Step by step
burger = BurgerBuilder().add_patty("beef").add_cheese("cheddar").build()
```

---

**Q2: When would you use a Director with Builder?**

A: Use Director when you have complex, reusable construction sequences:

```python
# Without Director: Repetitive
car1 = CarBuilder().set_engine("V8").set_wheels(20)...build()
car2 = CarBuilder().set_engine("V8").set_wheels(20)...build()

# With Director: Reusable
car1 = CarDirector.build_sports_car(CarBuilder())
car2 = CarDirector.build_sports_car(CarBuilder())
```

---

**Q3: How do you make builder objects thread-safe?**

A:
```python
import threading

class ThreadSafeBuilder:
    def __init__(self):
        self.obj = ComplexObject()
        self.lock = threading.Lock()
    
    def set_property(self, name: str, value: Any) -> 'ThreadSafeBuilder':
        with self.lock:
            setattr(self.obj, name, value)
        return self
    
    def build(self) -> ComplexObject:
        with self.lock:
            return copy.deepcopy(self.obj)
```

---

**Q4: How would you handle immutable objects with Builder?**

A:
```python
class ImmutableBurger:
    def __init__(self, buns, patty, cheese):
        self._buns = buns
        self._patty = patty
        self._cheese = cheese
    
    @property
    def buns(self):
        return self._buns
    
    # No setters - immutable

class BurgerBuilder:
    def __init__(self):
        self.buns = None
        self.patty = None
        self.cheese = None
    
    def build(self) -> ImmutableBurger:
        # Create immutable object at the end
        return ImmutableBurger(self.buns, self.patty, self.cheese)
```

---

**Q5: How do you handle default values in Builder?**

A: Set defaults in builder constructor or provide separate methods:

```python
class ConfigBuilder:
    def __init__(self):
        # Set defaults
        self.timeout = 30
        self.retry = 3
        self.debug = False
    
    def set_timeout(self, timeout: int) -> 'ConfigBuilder':
        self.timeout = timeout
        return self
    
    # Only override what's needed
    config = ConfigBuilder().set_timeout(60).build()
    # retry=3, debug=False (defaults)
```

---

## Trade-offs

✅ **Pros**: Clean API, method chaining, handles complexity, immutability support  
❌ **Cons**: Extra builder class, overkill for simple objects

---

## Real-World Examples

- **StringBuilder** in Java/C#
- **ConfigBuilder** in applications
- **SQL QueryBuilder** (SELECT, WHERE, ORDER BY)
- **HTML builders** in templating
