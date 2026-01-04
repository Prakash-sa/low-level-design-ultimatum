# Singleton Pattern

> Ensure a class has only one instance and provide a global point of access to it.

---

## Problem

Some classes should have only one instance (logger, database connection, configuration). You need to prevent multiple instances and provide global access.

## Solution

The Singleton pattern restricts instantiation to a single object and provides a global access point.

---

## Implementation

```python
import threading
from typing import Optional

# ============ BASIC SINGLETON ============

class Logger:
    __instance: Optional['Logger'] = None
    
    @staticmethod
    def get_instance() -> 'Logger':
        if Logger.__instance is None:
            Logger.__instance = Logger()
        return Logger.__instance
    
    def log(self, message: str):
        print(f"[LOG] {message}")

# Usage
logger1 = Logger.get_instance()
logger2 = Logger.get_instance()
print(logger1 is logger2)  # True

# ============ THREAD-SAFE SINGLETON (using __new__) ============

class DatabaseConnection:
    __instance: Optional['DatabaseConnection'] = None
    __lock = threading.Lock()
    
    def __new__(cls):
        """Enforce singleton - only one instance can exist"""
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
                    cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self):
        """Only initialize once"""
        if self._initialized:
            return
        self._initialized = True
        self.connection_string = "localhost:5432"
        print("Database connection initialized")
    
    def query(self, sql: str):
        print(f"Executing: {sql}")

# Usage
db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(db1 is db2)  # True

# ============ METACLASS SINGLETON ============

class SingletonMeta(type):
    """Metaclass that enforces singleton pattern"""
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

class ConfigManager(metaclass=SingletonMeta):
    def __init__(self):
        self.config = {
            "app_name": "MyApp",
            "version": "1.0",
            "debug": True
        }
    
    def get(self, key: str):
        return self.config.get(key)

# Usage
config1 = ConfigManager()
config2 = ConfigManager()
print(config1 is config2)  # True
print(config1.get("app_name"))  # "MyApp"

# ============ MODULE-LEVEL SINGLETON (Python idiom) ============

# singleton.py
class _Logger:
    def __init__(self):
        self.log_level = "INFO"
    
    def log(self, message: str):
        print(f"[{self.log_level}] {message}")

# Create singleton instance at module level
logger_instance = _Logger()

# In other files, import:
# from singleton import logger_instance

# ============ LAZY SINGLETON WITH DECORATOR ============

def singleton(cls):
    """Decorator to make a class singleton"""
    instances = {}
    lock = threading.Lock()
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

@singleton
class AppSettings:
    def __init__(self):
        self.theme = "dark"
        self.language = "en"

# Usage
settings1 = AppSettings()
settings2 = AppSettings()
print(settings1 is settings2)  # True

# Demo
if __name__ == "__main__":
    print("=== Basic Singleton ===")
    logger1 = Logger.get_instance()
    logger2 = Logger.get_instance()
    logger1.log("This is a log message")
    print(f"Same instance: {logger1 is logger2}\n")
    
    print("=== Thread-Safe Singleton ===")
    db1 = DatabaseConnection()
    db2 = DatabaseConnection()
    print(f"Same instance: {db1 is db2}\n")
    
    print("=== Metaclass Singleton ===")
    config1 = ConfigManager()
    config2 = ConfigManager()
    print(f"Same instance: {config1 is config2}\n")
    
    print("=== Decorator Singleton ===")
    settings1 = AppSettings()
    settings2 = AppSettings()
    print(f"Same instance: {settings1 is settings2}")
```

---

## Key Concepts

- **Single Instance**: Only one object exists
- **Global Access**: Static method or property to access instance
- **Lazy Initialization**: Instance created when first needed
- **Thread Safety**: Double-checked locking prevents race conditions
- **Eager Loading**: Instance created at class load time (faster access, slower startup)
- **Lazy Loading**: Instance created on first use (slower first access, faster startup)

---

## Eager Loading vs Lazy Loading

**Eager Loading** - Instance created immediately:
```python
class EagerSingleton:
    _instance = None
    
    def __init__(self):
        self.data = "initialized"
    
    @classmethod
    def _initialize(cls):
        if cls._instance is None:
            cls._instance = cls()  # Create immediately

EagerSingleton._initialize()  # Called at module load
```

**Lazy Loading** - Instance created on first access:
```python
class LazySingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()  # Create on first call
        return cls._instance
```

Trade-offs: Eager = predictable, no runtime overhead; Lazy = minimal startup, runtime penalty on first access.

---

## When to Use

✅ Logger or logging service  
✅ Database connection pools  
✅ Configuration managers  
✅ Cache managers  
✅ Thread pools  

---

## Interview Q&A

**Q1: Why is Singleton considered an anti-pattern?**

A:
1. **Global state**: Hard to test and debug
2. **Hidden dependencies**: Class relationships unclear
3. **Concurrency issues**: If not thread-safe, race conditions
4. **Violates SRP**: Class responsible for both functionality and instance control

**Better alternative**: Dependency Injection

```python
# Instead of:
logger = Logger.get_instance()

# Use:
class Service:
    def __init__(self, logger: Logger):
        self.logger = logger
```

---

**Q2: Is double-checked locking thread-safe?**

A: In Python, yes due to GIL (Global Interpreter Lock). In Java/C++, it's complex due to memory visibility.

```python
# Pythonic and thread-safe
class Singleton:
    __instance = None
    __lock = threading.Lock()
    
    def __new__(cls):
        if cls.__instance is None:  # First check (no lock)
            with cls.__lock:
                if cls.__instance is None:  # Second check (with lock)
                    cls.__instance = super().__new__(cls)
        return cls.__instance
```

---

**Q3: How do you test Singleton code?**

A: Use dependency injection + mock:

```python
# Make singletons testable
class Logger:
    __instance = None
    
    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance
    
    @classmethod
    def set_instance(cls, instance):  # For testing
        cls.__instance = instance

# In tests:
mock_logger = MagicMock()
Logger.set_instance(mock_logger)
```

---

**Q4: Can you have multiple singleton instances per thread?**

A: Yes, use thread-local storage:

```python
import threading

class ThreadLocalSingleton:
    _instances = threading.local()
    
    def __new__(cls):
        if not hasattr(cls._instances, 'instance'):
            cls._instances.instance = super().__new__(cls)
        return cls._instances.instance

# Each thread gets its own instance
```

---

**Q5: How do you handle Singleton serialization/deserialization?**

A:
```python
import pickle

class SerializableSingleton:
    __instance = None
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __reduce__(self):
        # Ensure deserialization returns the singleton
        return (self.__class__, ())

# Usage
original = SerializableSingleton()
serialized = pickle.dumps(original)
deserialized = pickle.loads(serialized)
print(original is deserialized)  # True
```

---

## Trade-offs

✅ **Pros**: Global access, memory efficient, lazy initialization possible  
❌ **Cons**: Hidden dependencies, hard to test, violates SRP, global state complexity

---

## Real-World Examples

- **Logger frameworks** (Log4j, Python logging)
- **Database connection pools** (HikariCP, psycopg2)
- **Cache managers** (Redis clients)
- **Configuration servers** (Spring Cloud Config)

## Notes
- Singleton class never accepts parameters, if it accepts then it becomes factory