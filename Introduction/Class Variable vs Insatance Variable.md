# Class Variable vs Instance Variable in Python

## Overview
Understanding the difference between class and instance variables is fundamental to object-oriented programming in Python. They control data sharing, memory usage, and object state management.

---

## 1. Class Variable

### Definition
A variable **shared across all instances** of a class. It's defined at the class level (outside methods) and stored in the class's namespace, not in individual objects.

### Characteristics
- Shared by all instances of the class
- Defined inside the class body, outside any method
- Accessed via `ClassName.variable` or `instance.variable`
- Modification via class affects all instances (unless shadowed)
- Stored in class's `__dict__`, not instance's `__dict__`

### Basic Example
```python
class Car:
    wheels = 4              # Class variable (shared)
    manufacturer = "Generic"  # Class variable

    def __init__(self, brand):
        self.brand = brand  # Instance variable (unique per object)

# Create instances
c1 = Car("BMW")
c2 = Car("Audi")

# Both share the same class variable
print(c1.wheels, c2.wheels)      # Output: 4 4

# Modify via class
Car.wheels = 6
print(c1.wheels, c2.wheels)      # Output: 6 6 (both changed)

# Access class variable properly
print(Car.wheels)                # Output: 6
```

### Real-World Example: Counter Pattern
```python
class Employee:
    total_employees = 0      # Class variable - tracks total count
    company_name = "TechCorp"  # Class variable - shared info

    def __init__(self, name, department):
        self.name = name          # Instance variable
        self.department = department  # Instance variable
        Employee.total_employees += 1  # Increment class variable

    @classmethod
    def get_total_employees(cls):
        return cls.total_employees

# Create employees
emp1 = Employee("Alice", "Engineering")
emp2 = Employee("Bob", "Marketing")
emp3 = Employee("Charlie", "Sales")

print(Employee.total_employees)     # Output: 3
print(Employee.get_total_employees())  # Output: 3
print(emp1.company_name)            # Output: TechCorp (shared)
```

### Important: Shadowing Behavior
```python
class Demo:
    x = 10  # Class variable

d1 = Demo()
d2 = Demo()

print(d1.x, d2.x)  # 10 10 (reading from class)

# Modifying via instance creates instance variable (shadowing)
d1.x = 20
print(d1.x, d2.x)  # 20 10 (d1 now has its own x)
print(Demo.x)      # 10 (class variable unchanged)

# Modifying via class affects unshadowed instances
Demo.x = 30
print(d1.x, d2.x)  # 20 30 (d1 still shadowed, d2 uses class)
```

---

## 2. Instance Variable

### Definition
A variable **unique to each object instance**. It's defined inside methods (typically `__init__`) using `self` and stored in each object's individual namespace.

### Characteristics
- Unique for each object
- Defined inside `__init__()` or instance methods using `self.variable`
- Accessed only via `instance.variable`
- Modification affects only that specific object
- Stored in each instance's `__dict__`

### Basic Example
```python
class Car:
    def __init__(self, brand, color, year):
        self.brand = brand    # Instance variable
        self.color = color    # Instance variable
        self.year = year      # Instance variable

c1 = Car("BMW", "Black", 2024)
c2 = Car("Audi", "Blue", 2023)

print(c1.brand)  # Output: BMW
print(c2.brand)  # Output: Audi

# Modify instance variable
c1.color = "Red"
print(c1.color)  # Output: Red
print(c2.color)  # Output: Blue (unchanged)
```

### Real-World Example: Bank Account
```python
class BankAccount:
    bank_name = "Global Bank"  # Class variable
    interest_rate = 0.03       # Class variable

    def __init__(self, account_holder, balance=0):
        self.account_holder = account_holder  # Instance variable
        self.balance = balance                # Instance variable
        self.transactions = []                # Instance variable (mutable)

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(f"Deposit: +${amount}")

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            self.transactions.append(f"Withdraw: -${amount}")
        else:
            print("Insufficient funds")

    def get_summary(self):
        return {
            'holder': self.account_holder,
            'balance': self.balance,
            'bank': self.bank_name,
            'rate': self.interest_rate
        }

# Create accounts
acc1 = BankAccount("Alice", 1000)
acc2 = BankAccount("Bob", 500)

acc1.deposit(200)
acc2.withdraw(100)

print(acc1.balance)  # Output: 1200
print(acc2.balance)  # Output: 400
print(acc1.transactions)  # Output: ['Deposit: +$200']
print(acc2.transactions)  # Output: ['Withdraw: -$100']

# Shared class variable
print(acc1.bank_name)  # Output: Global Bank
print(acc2.bank_name)  # Output: Global Bank
```

---

## 3. Comparison Table

| Feature | Class Variable | Instance Variable |
|---------|---------------|-------------------|
| **Belongs to** | Class (shared by all instances) | Each individual object |
| **Memory** | Single shared location | Separate copy per instance |
| **Definition** | Inside class body, outside methods | Inside `__init__` or instance methods with `self` |
| **Access** | `ClassName.var` or `instance.var` | `instance.var` only |
| **Modification via class** | Affects all instances (if not shadowed) | Not applicable |
| **Modification via instance** | Creates instance variable (shadowing) | Affects only that instance |
| **Storage** | Class's `__dict__` | Instance's `__dict__` |
| **Use case** | Shared configuration, counters, constants | Object-specific state |

---

## 4. Common Pitfalls and Best Practices

### ⚠️ Pitfall 1: Mutable Class Variables
```python
# WRONG - Mutable class variable
class Student:
    grades = []  # Shared across all instances!

    def __init__(self, name):
        self.name = name

s1 = Student("Alice")
s2 = Student("Bob")

s1.grades.append(90)
s2.grades.append(85)

print(s1.grades)  # [90, 85] - Unexpected!
print(s2.grades)  # [90, 85] - Shared list
```

```python
# CORRECT - Mutable instance variable
class Student:
    def __init__(self, name):
        self.name = name
        self.grades = []  # Each instance gets own list

s1 = Student("Alice")
s2 = Student("Bob")

s1.grades.append(90)
s2.grades.append(85)

print(s1.grades)  # [90]
print(s2.grades)  # [85]
```

### ⚠️ Pitfall 2: Modifying Class Variables Through Instance
```python
class Config:
    debug_mode = False  # Class variable

c1 = Config()
c2 = Config()

# WRONG - Creates instance variable, doesn't modify class
c1.debug_mode = True

print(c1.debug_mode)     # True (instance variable)
print(c2.debug_mode)     # False (still using class variable)
print(Config.debug_mode) # False (class variable unchanged)

# CORRECT - Modify class variable
Config.debug_mode = True
print(c1.debug_mode)  # True (if not shadowed)
print(c2.debug_mode)  # True
```

### ✔️ Best Practice: Use Class Methods for Class Variables
```python
class AppConfig:
    _environment = "development"  # Private class variable

    @classmethod
    def set_environment(cls, env):
        """Properly modify class variable"""
        cls._environment = env

    @classmethod
    def get_environment(cls):
        return cls._environment

# Good practice
AppConfig.set_environment("production")
print(AppConfig.get_environment())  # production
```

---

## 5. Inspection and Debugging

### Using `__dict__`
```python
class Example:
    class_var = "shared"

    def __init__(self, value):
        self.instance_var = value

e1 = Example("unique1")
e2 = Example("unique2")

# Instance dictionaries (only instance variables)
print(e1.__dict__)  # {'instance_var': 'unique1'}
print(e2.__dict__)  # {'instance_var': 'unique2'}

# Class dictionary (includes class variables)
print(Example.__dict__)  # {..., 'class_var': 'shared', ...}
```

### Checking Variable Location
```python
class Demo:
    x = 10

    def __init__(self):
        self.y = 20

d = Demo()

# Check if variable is in instance
print('x' in d.__dict__)  # False (it's in class)
print('y' in d.__dict__)  # True (it's in instance)

# Check if variable is in class
print('x' in Demo.__dict__)  # True
print('y' in Demo.__dict__)  # False
```

---

## 6. When to Use What?

### Use Class Variables for:
- Constants shared across all instances
- Default configuration values
- Counters tracking total instances
- Shared resources or connection pools
- Type-level metadata

### Use Instance Variables for:
- Object-specific state
- Attributes that vary per object
- Mutable collections (lists, dicts)
- User input or dynamic data
- Object identity or unique properties

---

## 7. Complete Example

```python
class Product:
    # Class variables
    store_name = "TechMart"
    tax_rate = 0.08
    total_products = 0

    def __init__(self, name, price, quantity):
        # Instance variables
        self.name = name
        self.price = price
        self.quantity = quantity
        self.product_id = Product.total_products
        Product.total_products += 1

    def get_total_price(self):
        """Calculate price with tax"""
        subtotal = self.price * self.quantity
        return subtotal * (1 + Product.tax_rate)

    @classmethod
    def update_tax_rate(cls, new_rate):
        """Update tax rate for all products"""
        cls.tax_rate = new_rate

    def __repr__(self):
        return f"Product({self.name}, ${self.price}, qty={self.quantity})"

# Create products
p1 = Product("Laptop", 1000, 2)
p2 = Product("Mouse", 25, 5)

print(p1)  # Product(Laptop, $1000, qty=2)
print(p2)  # Product(Mouse, $25, qty=5)

# Instance-specific calculations
print(f"Laptop total: ${p1.get_total_price():.2f}")  # $2160.00
print(f"Mouse total: ${p2.get_total_price():.2f}")   # $135.00

# Shared class variables
print(f"Store: {Product.store_name}")     # TechMart
print(f"Total products: {Product.total_products}")  # 2

# Update class variable affects all
Product.update_tax_rate(0.10)
print(f"Laptop total: ${p1.get_total_price():.2f}")  # $2200.00
print(f"Mouse total: ${p2.get_total_price():.2f}")   # $137.50
```

---

## Summary

- **Class variables** are shared across all instances—use for constants, defaults, and shared state
- **Instance variables** are unique per object—use for object-specific data
- Avoid mutable class variables (lists, dicts) unless intentionally sharing
- Modify class variables through the class, not instances, to avoid shadowing
- Use `@classmethod` for operations on class variables
- Check `__dict__` to inspect where variables are stored
