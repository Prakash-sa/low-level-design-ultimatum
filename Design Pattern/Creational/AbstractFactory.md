# Abstract Factory Pattern

> Provide an interface for creating families of related or dependent objects without specifying their concrete classes.

---

## Problem

You need to create groups of related objects (e.g., UI components for Windows vs Mac) that must be used together consistently.

## Solution

The Abstract Factory pattern provides an interface for creating families of related objects.

---

## Implementation

```python
from abc import ABC, abstractmethod

# ============ ABSTRACT PRODUCTS ============

class Button(ABC):
    @abstractmethod
    def render(self):
        pass

class Checkbox(ABC):
    @abstractmethod
    def render(self):
        pass

# ============ CONCRETE PRODUCTS: Windows ============

class WindowsButton(Button):
    def render(self):
        return "Rendering Windows button"

class WindowsCheckbox(Checkbox):
    def render(self):
        return "Rendering Windows checkbox"

# ============ CONCRETE PRODUCTS: Mac ============

class MacButton(Button):
    def render(self):
        return "Rendering Mac button"

class MacCheckbox(Checkbox):
    def render(self):
        return "Rendering Mac checkbox"

# ============ CONCRETE PRODUCTS: Linux ============

class LinuxButton(Button):
    def render(self):
        return "Rendering Linux button"

class LinuxCheckbox(Checkbox):
    def render(self):
        return "Rendering Linux checkbox"

# ============ ABSTRACT FACTORY ============

class GUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button:
        pass
    
    @abstractmethod
    def create_checkbox(self) -> Checkbox:
        pass

# ============ CONCRETE FACTORIES ============

class WindowsFactory(GUIFactory):
    def create_button(self) -> Button:
        return WindowsButton()
    
    def create_checkbox(self) -> Checkbox:
        return WindowsCheckbox()

class MacFactory(GUIFactory):
    def create_button(self) -> Button:
        return MacButton()
    
    def create_checkbox(self) -> Checkbox:
        return MacCheckbox()

class LinuxFactory(GUIFactory):
    def create_button(self) -> Button:
        return LinuxButton()
    
    def create_checkbox(self) -> Checkbox:
        return LinuxCheckbox()

# ============ CLIENT ============

class Application:
    def __init__(self, factory: GUIFactory):
        self.factory = factory
    
    def render(self) -> str:
        button = self.factory.create_button()
        checkbox = self.factory.create_checkbox()
        return f"{button.render()}\n{checkbox.render()}"

# ============ REAL-WORLD EXAMPLE: Database Connection ============

class Connection(ABC):
    @abstractmethod
    def connect(self):
        pass

class Query(ABC):
    @abstractmethod
    def execute(self):
        pass

# MySQL
class MySQLConnection(Connection):
    def connect(self):
        return "Connected to MySQL"

class MySQLQuery(Query):
    def execute(self):
        return "Executing MySQL query"

# PostgreSQL
class PostgreSQLConnection(Connection):
    def connect(self):
        return "Connected to PostgreSQL"

class PostgreSQLQuery(Query):
    def execute(self):
        return "Executing PostgreSQL query"

# MongoDB
class MongoConnection(Connection):
    def connect(self):
        return "Connected to MongoDB"

class MongoQuery(Query):
    def execute(self):
        return "Executing MongoDB query"

# Database Factories
class DatabaseFactory(ABC):
    @abstractmethod
    def create_connection(self) -> Connection:
        pass
    
    @abstractmethod
    def create_query(self) -> Query:
        pass

class MySQLFactory(DatabaseFactory):
    def create_connection(self) -> Connection:
        return MySQLConnection()
    
    def create_query(self) -> Query:
        return MySQLQuery()

class PostgreSQLFactory(DatabaseFactory):
    def create_connection(self) -> Connection:
        return PostgreSQLConnection()
    
    def create_query(self) -> Query:
        return PostgreSQLQuery()

class MongoFactory(DatabaseFactory):
    def create_connection(self) -> Connection:
        return MongoConnection()
    
    def create_query(self) -> Query:
        return MongoQuery()

class Database:
    def __init__(self, factory: DatabaseFactory):
        self.factory = factory
    
    def setup(self):
        connection = self.factory.create_connection()
        query = self.factory.create_query()
        return f"{connection.connect()}\n{query.execute()}"

# Demo
if __name__ == "__main__":
    print("=== GUI Abstract Factory ===")
    
    # Windows GUI
    windows_factory = WindowsFactory()
    windows_app = Application(windows_factory)
    print("Windows Application:")
    print(windows_app.render())
    print()
    
    # Mac GUI
    mac_factory = MacFactory()
    mac_app = Application(mac_factory)
    print("Mac Application:")
    print(mac_app.render())
    print()
    
    # Linux GUI
    linux_factory = LinuxFactory()
    linux_app = Application(linux_factory)
    print("Linux Application:")
    print(linux_app.render())
    print()
    
    print("=== Database Abstract Factory ===")
    
    # MySQL
    mysql_db = Database(MySQLFactory())
    print("MySQL Setup:")
    print(mysql_db.setup())
    print()
    
    # PostgreSQL
    postgres_db = Database(PostgreSQLFactory())
    print("PostgreSQL Setup:")
    print(postgres_db.setup())
    print()
    
    # MongoDB
    mongo_db = Database(MongoFactory())
    print("MongoDB Setup:")
    print(mongo_db.setup())
```

---

## Key Concepts

- **Abstract Factory**: Interface for creating families of products
- **Concrete Factory**: Creates specific family of related objects
- **Family Consistency**: Ensures related objects work together
- **Product Families**: Groups of related objects (Button+Checkbox, Connection+Query)

---

## When to Use

✅ System needs to work with multiple families of related objects  
✅ Need consistency among related objects  
✅ Want to hide specific classes from clients  
✅ Platform-specific implementations (Windows/Mac/Linux)  

---

## Interview Q&A

**Q1: What's the difference between Factory Method and Abstract Factory?**

A:
- **Factory Method**: Creates ONE type of object. Allows subclasses to choose which class.
- **Abstract Factory**: Creates FAMILIES of related objects. Ensures consistency.

```python
# Factory Method (one product)
class Restaurant:
    def create_burger(self) -> Burger:
        pass

# Abstract Factory (family of products)
class GUIFactory:
    def create_button(self) -> Button:
        pass
    def create_checkbox(self) -> Checkbox:
        pass
```

---

**Q2: How would you handle adding a new product family (e.g., Material Design)?**

A: Create new factories without modifying existing code:

```python
class MaterialButton(Button):
    def render(self):
        return "Rendering Material Design button"

class MaterialCheckbox(Checkbox):
    def render(self):
        return "Rendering Material Design checkbox"

class MaterialFactory(GUIFactory):
    def create_button(self) -> Button:
        return MaterialButton()
    
    def create_checkbox(self) -> Checkbox:
        return MaterialCheckbox()

# Client code needs NO changes!
factory = MaterialFactory()
app = Application(factory)
```

---

**Q3: Can you combine Abstract Factory with Singleton?**

A: Yes, create single factory instances:

```python
class FactoryProvider:
    _factories = {
        "windows": WindowsFactory(),
        "mac": MacFactory(),
        "linux": LinuxFactory()
    }
    
    @staticmethod
    def get_factory(os_type: str) -> GUIFactory:
        return FactoryProvider._factories.get(os_type)
```

---

**Q4: How would you make factories injectable?**

A:
```python
class Application:
    def __init__(self, factory: GUIFactory):
        self.factory = factory

# Dependency Injection
def create_app(os_type: str) -> Application:
    factory = FactoryProvider.get_factory(os_type)
    return Application(factory)

# Or in config:
app = Application(config.gui_factory)
```

---

**Q5: How would you handle factory initialization with parameters?**

A:
```python
class ParameterizedFactory(GUIFactory):
    def __init__(self, theme: str, size: str):
        self.theme = theme
        self.size = size
    
    def create_button(self) -> Button:
        return Button(theme=self.theme, size=self.size)

# Usage
factory = ParameterizedFactory(theme="dark", size="large")
app = Application(factory)
```

---

## Trade-offs

✅ **Pros**: Ensures product family consistency, easy to swap families, isolates concrete classes  
❌ **Cons**: More complex, overkill for simple scenarios, hard to extend

---

## Real-World Examples

- **UI frameworks** (different platforms need different widgets)
- **Database drivers** (MySQL vs PostgreSQL vs MongoDB)
- **Payment gateways** (Stripe, PayPal, Square)
- **Cloud providers** (AWS, Azure, GCP)

## Notes

- Factory Method Pattern employs a single factory class per type, while the Abstract Factory Pattern involves multiple factory methods to manage the creation of interrelated components.