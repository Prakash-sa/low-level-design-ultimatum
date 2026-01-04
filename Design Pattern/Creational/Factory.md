# Factory Pattern

> Define an interface for creating an object, but let subclasses decide which class to instantiate.

---

## Problem

You need to create objects of different types based on some criteria, but you don't want to hardcode `new ClassName()` in multiple places.

## Solution

The Factory pattern abstracts object creation into a factory method or factory class.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import List

# ============ PRODUCT INTERFACE ============

class Burger(ABC):
    @abstractmethod
    def prepare(self) -> str:
        pass
    
    @abstractmethod
    def get_price(self) -> float:
        pass

# ============ CONCRETE PRODUCTS ============

class CheeseBurger(Burger):
    def __init__(self):
        self.ingredients = ["bun", "cheese", "beef-patty"]
    
    def prepare(self) -> str:
        return f"CheeseBurger with {', '.join(self.ingredients)}"
    
    def get_price(self) -> float:
        return 5.99

class VeganBurger(Burger):
    def __init__(self):
        self.ingredients = ["bun", "veggies", "special-sauce"]
    
    def prepare(self) -> str:
        return f"VeganBurger with {', '.join(self.ingredients)}"
    
    def get_price(self) -> float:
        return 6.99

class SpecialBurger(Burger):
    def __init__(self):
        self.ingredients = ["bun", "double-patty", "bacon", "cheese", "lettuce"]
    
    def prepare(self) -> str:
        return f"SpecialBurger with {', '.join(self.ingredients)}"
    
    def get_price(self) -> float:
        return 8.99

# ============ SIMPLE FACTORY ============

class BurgerFactory:
    """Simple Factory - not a design pattern, just a helper class"""
    
    @staticmethod
    def create_burger(burger_type: str) -> Burger:
        if burger_type == "cheese":
            return CheeseBurger()
        elif burger_type == "vegan":
            return VeganBurger()
        elif burger_type == "special":
            return SpecialBurger()
        else:
            raise ValueError(f"Unknown burger type: {burger_type}")

# ============ FACTORY METHOD PATTERN ============

class Restaurant(ABC):
    """Abstract creator"""
    
    @abstractmethod
    def create_burger(self) -> Burger:
        """Factory method - subclasses decide which burger to create"""
        pass
    
    def order_burger(self) -> str:
        burger = self.create_burger()
        return burger.prepare()

class FastFoodRestaurant(Restaurant):
    """Concrete creator - creates CheeseBurger"""
    
    def create_burger(self) -> Burger:
        return CheeseBurger()

class HealthyRestaurant(Restaurant):
    """Concrete creator - creates VeganBurger"""
    
    def create_burger(self) -> Burger:
        return VeganBurger()

class PremiumRestaurant(Restaurant):
    """Concrete creator - creates SpecialBurger"""
    
    def create_burger(self) -> Burger:
        return SpecialBurger()

# ============ ABSTRACT FACTORY PATTERN ============

class Pizza(ABC):
    @abstractmethod
    def prepare(self) -> str:
        pass

class MargheritaPizza(Pizza):
    def prepare(self) -> str:
        return "Margherita Pizza"

class PepperoniPizza(Pizza):
    def prepare(self) -> str:
        return "Pepperoni Pizza"

class Drink(ABC):
    @abstractmethod
    def prepare(self) -> str:
        pass

class Cola(Drink):
    def prepare(self) -> str:
        return "Cola"

class OrangeJuice(Drink):
    def prepare(self) -> str:
        return "Orange Juice"

class MealFactory(ABC):
    """Abstract factory - creates families of related objects"""
    
    @abstractmethod
    def create_pizza(self) -> Pizza:
        pass
    
    @abstractmethod
    def create_drink(self) -> Drink:
        pass

class ItalianMealFactory(MealFactory):
    """Concrete factory - creates Italian meals"""
    
    def create_pizza(self) -> Pizza:
        return MargheritaPizza()
    
    def create_drink(self) -> Drink:
        return OrangeJuice()

class AmericanMealFactory(MealFactory):
    """Concrete factory - creates American meals"""
    
    def create_pizza(self) -> Pizza:
        return PepperoniPizza()
    
    def create_drink(self) -> Drink:
        return Cola()

# ============ REGISTRY FACTORY ============

class RegistryFactory:
    """Factory using a registry - extensible without modifying factory"""
    _registry = {}
    
    @classmethod
    def register(cls, burger_type: str, burger_class):
        cls._registry[burger_type] = burger_class
    
    @classmethod
    def create(cls, burger_type: str) -> Burger:
        burger_class = cls._registry.get(burger_type)
        if burger_class is None:
            raise ValueError(f"Unknown type: {burger_type}")
        return burger_class()

# Register types
RegistryFactory.register("cheese", CheeseBurger)
RegistryFactory.register("vegan", VeganBurger)
RegistryFactory.register("special", SpecialBurger)

# Demo
if __name__ == "__main__":
    print("=== Simple Factory ===")
    factory = BurgerFactory()
    burger1 = factory.create_burger("cheese")
    burger2 = factory.create_burger("vegan")
    print(burger1.prepare())
    print(burger2.prepare())
    print()
    
    print("=== Factory Method Pattern ===")
    restaurants = [
        FastFoodRestaurant(),
        HealthyRestaurant(),
        PremiumRestaurant()
    ]
    
    for restaurant in restaurants:
        print(restaurant.order_burger())
    print()
    
    print("=== Abstract Factory Pattern ===")
    italian_factory = ItalianMealFactory()
    american_factory = AmericanMealFactory()
    
    print(f"Italian meal: {italian_factory.create_pizza().prepare()}, {italian_factory.create_drink().prepare()}")
    print(f"American meal: {american_factory.create_pizza().prepare()}, {american_factory.create_drink().prepare()}")
    print()
    
    print("=== Registry Factory ===")
    burger = RegistryFactory.create("vegan")
    print(burger.prepare())
```

---

## Key Concepts

- **Simple Factory**: Helper class with static method
- **Factory Method**: Subclasses override method to decide which object to create
- **Abstract Factory**: Creates families of related objects
- **Registry Factory**: Objects registered by type for lookup

---

## When to Use

✅ Complex object creation logic  
✅ Need to support multiple types/implementations  
✅ Want to decouple creation from usage  
✅ Extensibility: add new types without modifying existing code  

---

## Interview Q&A

**Q1: What's the difference between Simple Factory and Factory Method?**

A:
- **Simple Factory**: Static method returns object. Not extensible (modify factory to add type).
- **Factory Method**: Abstract method in subclasses. Extensible (add new subclass).

```python
# Simple Factory (NOT extensible)
class BurgerFactory:
    @staticmethod
    def create(type):
        if type == "new_type":  # Have to modify factory
            return NewBurger()

# Factory Method (extensible)
class NewRestaurant(Restaurant):  # Just add new subclass
    def create_burger(self):
        return NewBurger()
```

---

**Q2: When would you use Abstract Factory vs Factory Method?**

A:
- **Factory Method**: One family of objects (burgers)
- **Abstract Factory**: Multiple families of related objects (pizza + drink combos)

```python
# Factory Method: Single product
class Restaurant:
    def create_burger(self) -> Burger:
        pass

# Abstract Factory: Multiple products
class MealFactory:
    def create_pizza(self) -> Pizza:
        pass
    def create_drink(self) -> Drink:
        pass
```

---

**Q3: How do you handle factory creation with many parameters?**

A: Use Builder pattern inside factory:

```python
class ComplexProductFactory:
    @staticmethod
    def create_with_builder(config: Dict) -> ComplexProduct:
        return (ComplexProductBuilder()
                .set_property1(config.get("prop1"))
                .set_property2(config.get("prop2"))
                .build())
```

---

**Q4: How would you implement a registry factory that supports plugins?**

A:
```python
class PluginFactory:
    _plugins = {}
    
    @classmethod
    def register_plugin(cls, name: str, plugin_class):
        cls._plugins[name] = plugin_class
    
    @classmethod
    def create(cls, name: str, *args, **kwargs):
        if name not in cls._plugins:
            raise ValueError(f"Plugin not found: {name}")
        return cls._plugins[name](*args, **kwargs)

# Plugins can be loaded dynamically
import importlib
plugin_module = importlib.import_module("my_plugin")
PluginFactory.register_plugin("custom", plugin_module.CustomClass)
```

---

**Q5: How do you test factory pattern code?**

A: Use dependency injection and mock:

```python
# Make factory injectable
class Service:
    def __init__(self, factory: BurgerFactory):
        self.factory = factory
    
    def get_burger(self, type: str) -> Burger:
        return self.factory.create(type)

# In tests:
class MockFactory:
    def create(self, type: str):
        return MagicMock(spec=Burger)

service = Service(MockFactory())
```

---

## Trade-offs

✅ **Pros**: Decouples creation from usage, extensible, supports polymorphism  
❌ **Cons**: Extra classes, can be overkill for simple object creation

---

## Real-World Examples

- **Object databases** (create Document, Image, Video objects)
- **UI frameworks** (create Button, TextBox, Dialog widgets)
- **Data parsers** (JSON, XML, YAML parsers)
- **Plugin systems** (load different implementations dynamically)
