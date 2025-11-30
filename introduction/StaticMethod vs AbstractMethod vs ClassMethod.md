# Static Method vs Abstract Method vs Class Method in Python

## Overview
Python provides three powerful method decorators for different use cases:
- `@staticmethod` — Utility functions that don't need instance or class data
- `@classmethod` — Methods that operate on class-level data or serve as alternative constructors
- `@abstractmethod` — Contract enforcement requiring subclasses to implement behavior

---

## 1. Static Method (`@staticmethod`)

### Definition
A method that belongs to a class namespace but doesn't access instance (`self`) or class (`cls`) data. It behaves like a regular function but is grouped inside a class for logical organization.

### Characteristics
- Defined with `@staticmethod` decorator
- No access to `self` (instance variables)
- No access to `cls` (class variables)
- Used for utility/helper functions
- Can be called via class name or instance

### Example
```python
class MathUtils:
    @staticmethod
    def add(a, b):
        """Simple addition utility"""
        return a + b
    
    @staticmethod
    def is_even(n):
        """Check if number is even"""
        return n % 2 == 0

# Call via class
print(MathUtils.add(3, 4))        # Output: 7
print(MathUtils.is_even(10))      # Output: True

# Can also call via instance (though uncommon)
util = MathUtils()
print(util.add(5, 6))             # Output: 11
```

### Real-World Example
```python
class DateValidator:
    @staticmethod
    def is_valid_format(date_str):
        """Validate date string format YYYY-MM-DD"""
        import re
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, date_str))
    
    @staticmethod
    def is_leap_year(year):
        """Check if year is a leap year"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

print(DateValidator.is_valid_format("2025-11-29"))  # True
print(DateValidator.is_leap_year(2024))             # True
```

---

## 2. Class Method (`@classmethod`)

### Definition
A method that receives the class itself (`cls`) as the first parameter instead of an instance. It can access and modify class-level state shared by all instances.

### Characteristics
- Defined with `@classmethod` decorator
- First parameter is `cls` (the class itself)
- Can access/modify class variables
- Commonly used as alternative constructors
- Enables factory patterns

### Example
```python
class User:
    user_count = 0
    
    def __init__(self, name, email):
        self.name = name
        self.email = email
        User.user_count += 1
    
    @classmethod
    def get_user_count(cls):
        """Get total number of users"""
        return cls.user_count
    
    @classmethod
    def from_email(cls, email):
        """Alternative constructor from email"""
        name = email.split("@")[0]
        return cls(name, email)
    
    @classmethod
    def reset_count(cls):
        """Reset user count"""
        cls.user_count = 0

# Regular constructor
user1 = User("Alice", "alice@example.com")

# Alternative constructor
user2 = User.from_email("bob@example.com")

print(User.get_user_count())      # Output: 2
print(user2.name)                 # Output: bob
```

### Real-World Example: Configuration Manager
```python
from datetime import datetime

class AppConfig:
    environment = "development"
    debug_mode = True
    
    @classmethod
    def set_production(cls):
        """Switch to production settings"""
        cls.environment = "production"
        cls.debug_mode = False
    
    @classmethod
    def set_development(cls):
        """Switch to development settings"""
        cls.environment = "development"
        cls.debug_mode = True
    
    @classmethod
    def get_config(cls):
        """Get current configuration"""
        return {
            'env': cls.environment,
            'debug': cls.debug_mode,
            'timestamp': datetime.now()
        }

AppConfig.set_production()
print(AppConfig.get_config())
# Output: {'env': 'production', 'debug': False, 'timestamp': ...}
```

---

## 3. Abstract Method (`@abstractmethod`)

### Definition
A method declared in a base class that **must** be implemented by all concrete subclasses. Enforces a contract ensuring consistent interfaces across implementations.

### Characteristics
- Defined using `@abstractmethod` from `abc` module
- Base class must inherit from `ABC`
- Cannot instantiate abstract class directly
- Forces subclasses to implement the method
- Enables polymorphism and interface-driven design
- Can have a default implementation (subclass still must override)

### Example
```python
from abc import ABC, abstractmethod

class Animal(ABC):
    """Abstract base class for animals"""
    
    @abstractmethod
    def speak(self):
        """All animals must implement speak"""
        pass
    
    @abstractmethod
    def move(self):
        """All animals must implement move"""
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"
    
    def move(self):
        return "Running on four legs"

class Bird(Animal):
    def speak(self):
        return "Chirp!"
    
    def move(self):
        return "Flying in the sky"

# This works
dog = Dog()
print(dog.speak())    # Output: Woof!
print(dog.move())     # Output: Running on four legs

# This raises TypeError: Can't instantiate abstract class
# animal = Animal()
```

### Real-World Example: Payment Processing
```python
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """Abstract payment processor interface"""
    
    @abstractmethod
    def validate_credentials(self):
        """Validate payment credentials"""
        pass
    
    @abstractmethod
    def process_payment(self, amount):
        """Process the payment"""
        pass
    
    @abstractmethod
    def refund(self, transaction_id):
        """Refund a transaction"""
        pass

class StripeProcessor(PaymentProcessor):
    def __init__(self, api_key):
        self.api_key = api_key
    
    def validate_credentials(self):
        return len(self.api_key) > 0
    
    def process_payment(self, amount):
        return f"Stripe: Processing ${amount}"
    
    def refund(self, transaction_id):
        return f"Stripe: Refunding transaction {transaction_id}"

class PayPalProcessor(PaymentProcessor):
    def __init__(self, client_id, secret):
        self.client_id = client_id
        self.secret = secret
    
    def validate_credentials(self):
        return bool(self.client_id and self.secret)
    
    def process_payment(self, amount):
        return f"PayPal: Processing ${amount}"
    
    def refund(self, transaction_id):
        return f"PayPal: Refunding transaction {transaction_id}"

# Polymorphic usage
processors = [
    StripeProcessor("sk_test_123"),
    PayPalProcessor("client_123", "secret_456")
]

for processor in processors:
    print(processor.process_payment(100))
# Output:
# Stripe: Processing $100
# PayPal: Processing $100
```

---

## 4. Comparison Table

| Feature | `@staticmethod` | `@classmethod` | `@abstractmethod` |
|---------|----------------|----------------|-------------------|
| **Has `self`?** | ❌ No | ❌ No | ✔ Yes (in subclass) |
| **Has `cls`?** | ❌ No | ✔ Yes | ❌ No (unless combined with `@classmethod`) |
| **Can modify class state?** | ❌ No | ✔ Yes | ✔ Yes (in subclass) |
| **Must be overridden?** | ❌ No | ❌ No | ✔ Yes |
| **Can be called on class?** | ✔ Yes | ✔ Yes | ❌ No (must implement first) |
| **Supports polymorphism?** | ❌ No | ❌ Limited | ✔ Yes |
| **Requires ABC inheritance?** | ❌ No | ❌ No | ✔ Yes |
| **Primary use case** | Utilities/helpers | Alt constructors, class ops | Interface enforcement |

---

## 5. When to Use What?

### Use `@staticmethod` when:
- ✔ You need a helper/utility function logically related to the class
- ✔ The function doesn't need access to instance or class data
- ✔ Examples: validation, formatting, calculations, parsing

### Use `@classmethod` when:
- ✔ You need to create alternative constructors
- ✔ You need to access/modify class-level state
- ✔ You want factory methods that return class instances
- ✔ Examples: `from_json()`, `from_dict()`, configuration management

### Use `@abstractmethod` when:
- ✔ You want to enforce a contract across subclasses
- ✔ You need polymorphic behavior
- ✔ You're implementing design patterns (Strategy, Template Method, etc.)
- ✔ You want to define interfaces in Python

---

## 6. Strategy Pattern Example (Combining All Three)

Here's how all three decorators can work together in a real design pattern:

```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Abstract strategy interface"""
    
    @abstractmethod
    def execute(self, a, b):
        """Must be implemented by concrete strategies"""
        pass
    
    @staticmethod
    def validate_inputs(a, b):
        """Static helper for input validation"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Inputs must be numbers")
        return True

class AddStrategy(Strategy):
    def execute(self, a, b):
        self.validate_inputs(a, b)
        return a + b

class MultiplyStrategy(Strategy):
    def execute(self, a, b):
        self.validate_inputs(a, b)
        return a * b

class Context:
    """Context that uses a strategy"""
    
    _default_strategy = None
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
    
    @classmethod
    def set_default_strategy(cls, strategy: Strategy):
        """Set default strategy for all instances"""
        cls._default_strategy = strategy
    
    @classmethod
    def create_with_default(cls):
        """Alternative constructor using default strategy"""
        if cls._default_strategy is None:
            raise ValueError("No default strategy set")
        return cls(cls._default_strategy)
    
    def execute(self, a, b):
        return self.strategy.execute(a, b)

# Usage
Context.set_default_strategy(AddStrategy())
ctx1 = Context.create_with_default()
print(ctx1.execute(3, 4))         # Output: 7

ctx2 = Context(MultiplyStrategy())
print(ctx2.execute(3, 4))         # Output: 12
```

### Why This Design?

1. **`@abstractmethod`** in `Strategy.execute()` — Enforces all strategies implement `execute()`
2. **`@staticmethod`** in `Strategy.validate_inputs()` — Shared utility logic, no state needed
3. **`@classmethod`** in `Context.set_default_strategy()` — Manages class-level default configuration
4. **`@classmethod`** in `Context.create_with_default()` — Alternative constructor pattern

---

## 7. Common Mistakes to Avoid

### ❌ Wrong: Using `@staticmethod` when you need class data
```python
class Config:
    environment = "dev"
    
    @staticmethod
    def get_env():
        return Config.environment  # Hardcoded class name
```

### ✔ Right: Use `@classmethod` instead
```python
class Config:
    environment = "dev"
    
    @classmethod
    def get_env(cls):
        return cls.environment  # Dynamic class reference
```

### ❌ Wrong: Forgetting to inherit from ABC
```python
class Strategy:
    @abstractmethod
    def execute(self):
        pass
# This won't prevent instantiation!
```

### ✔ Right: Inherit from ABC
```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self):
        pass
# Now Strategy() raises TypeError
```

---

## 8. Quick Reference

```python
from abc import ABC, abstractmethod

class Demo(ABC):
    class_var = 0
    
    def __init__(self, value):
        self.value = value
    
    # Regular instance method
    def instance_method(self):
        return self.value
    
    # Static method - no self, no cls
    @staticmethod
    def static_helper(x, y):
        return x + y
    
    # Class method - receives cls
    @classmethod
    def from_string(cls, s):
        return cls(int(s))
    
    # Abstract method - must override
    @abstractmethod
    def abstract_operation(self):
        pass

class ConcreteDemo(Demo):
    def abstract_operation(self):
        return "Implemented!"

# Usage
obj = ConcreteDemo(42)
print(obj.instance_method())              # 42
print(Demo.static_helper(10, 20))         # 30
print(Demo.from_string("99").value)       # 99
print(obj.abstract_operation())           # Implemented!
```

---

## Summary

| Decorator | Purpose | Use When |
|-----------|---------|----------|
| `@staticmethod` | Utility function in class namespace | No instance/class data needed |
| `@classmethod` | Operate on class-level data | Alternative constructors, factory methods |
| `@abstractmethod` | Enforce implementation contract | Building interfaces, polymorphic systems |

**Pro Tip**: You can combine decorators! Example: `@classmethod` + `@abstractmethod` for abstract factory methods.