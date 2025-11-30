# Python Built-in Exceptions

## Overview
Python has a rich hierarchy of built-in exceptions that help handle errors and exceptional conditions. Understanding these exceptions is crucial for writing robust, error-handling code.

---

## Exception Hierarchy

```
BaseException
├── SystemExit
├── KeyboardInterrupt
├── GeneratorExit
└── Exception
    ├── StopIteration
    ├── StopAsyncIteration
    ├── ArithmeticError
    │   ├── FloatingPointError
    │   ├── OverflowError
    │   └── ZeroDivisionError
    ├── AssertionError
    ├── AttributeError
    ├── BufferError
    ├── EOFError
    ├── ImportError
    │   └── ModuleNotFoundError
    ├── LookupError
    │   ├── IndexError
    │   └── KeyError
    ├── MemoryError
    ├── NameError
    │   └── UnboundLocalError
    ├── OSError
    │   ├── BlockingIOError
    │   ├── ChildProcessError
    │   ├── ConnectionError
    │   │   ├── BrokenPipeError
    │   │   ├── ConnectionAbortedError
    │   │   ├── ConnectionRefusedError
    │   │   └── ConnectionResetError
    │   ├── FileExistsError
    │   ├── FileNotFoundError
    │   ├── InterruptedError
    │   ├── IsADirectoryError
    │   ├── NotADirectoryError
    │   ├── PermissionError
    │   ├── ProcessLookupError
    │   └── TimeoutError
    ├── ReferenceError
    ├── RuntimeError
    │   ├── NotImplementedError
    │   └── RecursionError
    ├── SyntaxError
    │   └── IndentationError
    │       └── TabError
    ├── SystemError
    ├── TypeError
    ├── ValueError
    │   └── UnicodeError
    │       ├── UnicodeDecodeError
    │       ├── UnicodeEncodeError
    │       └── UnicodeTranslateError
    └── Warning
        ├── DeprecationWarning
        ├── PendingDeprecationWarning
        ├── RuntimeWarning
        ├── SyntaxWarning
        ├── UserWarning
        ├── FutureWarning
        ├── ImportWarning
        ├── UnicodeWarning
        ├── BytesWarning
        └── ResourceWarning
```

---

## 1. Common Exceptions

### ZeroDivisionError
Raised when dividing by zero.

```python
# Example
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")  # Output: Error: division by zero

# Real-world usage
def calculate_average(total, count):
    try:
        return total / count
    except ZeroDivisionError:
        return 0  # Return default when count is zero

print(calculate_average(100, 0))  # Output: 0
```

### TypeError
Raised when an operation is applied to an object of inappropriate type.

```python
# Example
try:
    result = "5" + 5
except TypeError as e:
    print(f"Error: {e}")  # Output: Error: can only concatenate str (not "int") to str

# Real-world usage
def add_numbers(a, b):
    try:
        return a + b
    except TypeError:
        # Try converting to numbers
        try:
            return float(a) + float(b)
        except (TypeError, ValueError):
            raise TypeError("Arguments must be numeric")

print(add_numbers("10", "20"))  # Output: 30.0
```

### ValueError
Raised when a function receives an argument of correct type but inappropriate value.

```python
# Example
try:
    number = int("abc")
except ValueError as e:
    print(f"Error: {e}")  # Output: Error: invalid literal for int() with base 10: 'abc'

# Real-world usage
def parse_age(age_str):
    try:
        age = int(age_str)
        if age < 0 or age > 150:
            raise ValueError("Age must be between 0 and 150")
        return age
    except ValueError as e:
        print(f"Invalid age: {e}")
        return None

print(parse_age("25"))   # Output: 25
print(parse_age("200"))  # Output: Invalid age: Age must be between 0 and 150
```

### IndexError
Raised when trying to access an index that doesn't exist.

```python
# Example
try:
    my_list = [1, 2, 3]
    print(my_list[10])
except IndexError as e:
    print(f"Error: {e}")  # Output: Error: list index out of range

# Real-world usage
def safe_get(lst, index, default=None):
    try:
        return lst[index]
    except IndexError:
        return default

my_list = [1, 2, 3]
print(safe_get(my_list, 1))   # Output: 2
print(safe_get(my_list, 10))  # Output: None
```

### KeyError
Raised when a dictionary key is not found.

```python
# Example
try:
    my_dict = {"name": "Alice", "age": 30}
    print(my_dict["email"])
except KeyError as e:
    print(f"Error: Key {e} not found")  # Output: Error: Key 'email' not found

# Real-world usage
def get_user_info(user_data, key, default="N/A"):
    try:
        return user_data[key]
    except KeyError:
        return default

user = {"name": "Bob", "age": 25}
print(get_user_info(user, "name"))   # Output: Bob
print(get_user_info(user, "email"))  # Output: N/A
```

### AttributeError
Raised when an attribute reference or assignment fails.

```python
# Example
try:
    my_list = [1, 2, 3]
    my_list.append_item(4)  # No such method
except AttributeError as e:
    print(f"Error: {e}")  # Output: Error: 'list' object has no attribute 'append_item'

# Real-world usage
class Person:
    def __init__(self, name):
        self.name = name

def get_attribute_safe(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except AttributeError:
        return default

p = Person("Alice")
print(get_attribute_safe(p, "name"))   # Output: Alice
print(get_attribute_safe(p, "age"))    # Output: None
```

### NameError
Raised when a local or global name is not found.

```python
# Example
try:
    print(undefined_variable)
except NameError as e:
    print(f"Error: {e}")  # Output: Error: name 'undefined_variable' is not defined

# Real-world usage
def safe_eval_variable(var_name, context):
    try:
        return eval(var_name, context)
    except NameError:
        return f"Variable '{var_name}' not defined"

context = {"x": 10, "y": 20}
print(safe_eval_variable("x", context))  # Output: 10
print(safe_eval_variable("z", context))  # Output: Variable 'z' not defined
```

---

## 2. File and I/O Exceptions

### FileNotFoundError
Raised when a file or directory is requested but doesn't exist.

```python
# Example
try:
    with open("nonexistent.txt", "r") as f:
        content = f.read()
except FileNotFoundError as e:
    print(f"Error: {e}")  # Output: Error: [Errno 2] No such file or directory: 'nonexistent.txt'

# Real-world usage
def read_config(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Config file '{filename}' not found, using defaults")
        return "{}"

config = read_config("config.json")
```

### PermissionError
Raised when trying to perform an operation without adequate permissions.

```python
# Example
try:
    with open("/root/protected.txt", "w") as f:
        f.write("test")
except PermissionError as e:
    print(f"Error: {e}")  # Output: Error: [Errno 13] Permission denied: '/root/protected.txt'

# Real-world usage
def safe_write(filename, content):
    try:
        with open(filename, "w") as f:
            f.write(content)
        return True
    except PermissionError:
        print(f"No permission to write to {filename}")
        return False
```

### IsADirectoryError
Raised when a file operation is requested on a directory.

```python
# Example
try:
    with open("/tmp", "r") as f:
        content = f.read()
except IsADirectoryError as e:
    print(f"Error: {e}")  # Output: Error: [Errno 21] Is a directory: '/tmp'
```

### EOFError
Raised when `input()` hits end-of-file condition.

```python
# Example
try:
    user_input = input("Enter something: ")
except EOFError:
    print("End of input reached")
```

---

## 3. Import Exceptions

### ImportError
Raised when an import statement fails.

```python
# Example
try:
    import nonexistent_module
except ImportError as e:
    print(f"Error: {e}")  # Output: Error: No module named 'nonexistent_module'

# Real-world usage
def optional_import(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        print(f"Optional module '{module_name}' not available")
        return None

requests = optional_import("requests")
if requests:
    print("Requests library available")
```

### ModuleNotFoundError
Subclass of ImportError, raised when a module cannot be located.

```python
# Example
try:
    from some_package import some_module
except ModuleNotFoundError as e:
    print(f"Error: {e}")  # Output: Error: No module named 'some_package'
```

---

## 4. Arithmetic Exceptions

### OverflowError
Raised when an arithmetic operation is too large to be represented.

```python
# Example (rare in Python 3 due to arbitrary precision integers)
import math

try:
    result = math.exp(1000)  # e^1000
except OverflowError as e:
    print(f"Error: {e}")  # Output: Error: math range error
```

### FloatingPointError
Raised when a floating point operation fails.

```python
# Example (requires special configuration)
import numpy as np

np.seterr(all='raise')
try:
    result = np.float64(1.0) / np.float64(0.0)
except FloatingPointError as e:
    print(f"Error: {e}")
```

---

## 5. Runtime Exceptions

### RecursionError
Raised when maximum recursion depth is exceeded.

```python
# Example
def infinite_recursion():
    return infinite_recursion()

try:
    infinite_recursion()
except RecursionError as e:
    print(f"Error: Maximum recursion depth exceeded")

# Real-world usage with proper recursion
def factorial(n, depth=0, max_depth=1000):
    if depth > max_depth:
        raise RecursionError("Maximum recursion depth for factorial")
    if n <= 1:
        return 1
    return n * factorial(n - 1, depth + 1, max_depth)

try:
    print(factorial(5))      # Output: 120
    print(factorial(2000))   # Raises RecursionError
except RecursionError as e:
    print(f"Error: {e}")
```

### NotImplementedError
Raised when an abstract method requires implementation.

```python
# Example
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        raise NotImplementedError("Subclass must implement speak()")

class Dog(Animal):
    def speak(self):
        return "Woof!"

# Real-world usage
class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount):
        raise NotImplementedError("Must implement process_payment()")

class StripeProcessor(PaymentProcessor):
    def process_payment(self, amount):
        return f"Processing ${amount} via Stripe"

class PayPalProcessor(PaymentProcessor):
    def process_payment(self, amount):
        return f"Processing ${amount} via PayPal"

processor = StripeProcessor()
print(processor.process_payment(100))  # Output: Processing $100 via Stripe
```

### MemoryError
Raised when an operation runs out of memory.

```python
# Example
try:
    huge_list = [0] * (10 ** 10)  # Try to allocate huge list
except MemoryError:
    print("Not enough memory to allocate list")
```

---

## 6. Assertion and System Exceptions

### AssertionError
Raised when an `assert` statement fails.

```python
# Example
try:
    x = 5
    assert x > 10, "x must be greater than 10"
except AssertionError as e:
    print(f"Error: {e}")  # Output: Error: x must be greater than 10

# Real-world usage
def withdraw(balance, amount):
    assert amount > 0, "Withdrawal amount must be positive"
    assert amount <= balance, "Insufficient funds"
    return balance - amount

try:
    new_balance = withdraw(100, 150)
except AssertionError as e:
    print(f"Withdrawal failed: {e}")  # Output: Withdrawal failed: Insufficient funds
```

### SystemExit
Raised by `sys.exit()`.

```python
# Example
import sys

try:
    sys.exit(0)
except SystemExit as e:
    print(f"Exiting with code: {e.code}")  # Output: Exiting with code: 0
```

### KeyboardInterrupt
Raised when user interrupts execution (Ctrl+C).

```python
# Example
try:
    while True:
        pass  # Infinite loop
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
```

---

## 7. Syntax Exceptions

### SyntaxError
Raised when Python encounters invalid syntax.

```python
# This will raise SyntaxError at parse time, can't be caught normally
# if True
#     print("Missing colon")

# Real-world usage with eval/exec
try:
    eval("if True print('test')")
except SyntaxError as e:
    print(f"Syntax error in expression: {e}")
```

### IndentationError
Raised when indentation is incorrect.

```python
# Real-world usage with exec
try:
    code = """
def test():
print("Bad indentation")
"""
    exec(code)
except IndentationError as e:
    print(f"Indentation error: {e}")
```

### TabError
Raised when mixing tabs and spaces inconsistently.

```python
# Example with exec
try:
    code = "def test():\n\tpass\n    pass"  # Mixed tabs and spaces
    exec(code)
except TabError as e:
    print(f"Tab error: {e}")
```

---

## 8. Unicode Exceptions

### UnicodeDecodeError
Raised when Unicode decoding fails.

```python
# Example
try:
    byte_string = b'\xff\xfe'
    text = byte_string.decode('utf-8')
except UnicodeDecodeError as e:
    print(f"Error: Cannot decode bytes")

# Real-world usage
def safe_decode(byte_data, encoding='utf-8'):
    try:
        return byte_data.decode(encoding)
    except UnicodeDecodeError:
        return byte_data.decode(encoding, errors='replace')

data = b'\xff\xfe'
print(safe_decode(data))  # Uses replacement character
```

### UnicodeEncodeError
Raised when Unicode encoding fails.

```python
# Example
try:
    text = "Hello 世界"
    encoded = text.encode('ascii')
except UnicodeEncodeError as e:
    print(f"Error: Cannot encode to ASCII")

# Real-world usage
def safe_encode(text, encoding='utf-8'):
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, errors='replace')
```

---

## 9. Connection and Network Exceptions

### ConnectionError
Base class for connection-related errors.

```python
# Example
import socket

try:
    sock = socket.socket()
    sock.connect(("nonexistent.example.com", 80))
except ConnectionError as e:
    print(f"Connection error: {e}")
```

### TimeoutError
Raised when an operation times out.

```python
# Example
import socket

try:
    sock = socket.socket()
    sock.settimeout(1)
    sock.connect(("192.0.2.1", 80))  # Non-routable address
except TimeoutError:
    print("Connection timed out")
```

### BrokenPipeError
Raised when writing to a pipe/socket that's been closed.

```python
# Example
import socket

try:
    sock = socket.socket()
    sock.close()
    sock.send(b"data")
except BrokenPipeError:
    print("Broken pipe - connection closed")
```

---

## 10. Custom Exception Handling Pattern

### Best Practices Example

```python
class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

class UserService:
    def create_user(self, username, email):
        # Validation
        if not username:
            raise ValidationError("Username cannot be empty")
        if "@" not in email:
            raise ValidationError("Invalid email format")
        
        # Simulate database operation
        try:
            # Database logic here
            if username == "admin":
                raise DatabaseError("Username 'admin' is reserved")
            return {"username": username, "email": email}
        except DatabaseError as e:
            print(f"Database error: {e}")
            raise

# Usage
service = UserService()

try:
    user = service.create_user("john", "john@example.com")
    print(f"User created: {user}")
except ValidationError as e:
    print(f"Validation failed: {e}")
except DatabaseError as e:
    print(f"Database operation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 11. Exception Handling Patterns

### Multiple Exceptions

```python
def process_data(data):
    try:
        # Multiple operations that can fail
        value = int(data['value'])
        result = 100 / value
        items = data['items']
        first_item = items[0]
        return first_item
    except (KeyError, IndexError) as e:
        print(f"Data access error: {e}")
        return None
    except (ValueError, TypeError) as e:
        print(f"Type conversion error: {e}")
        return None
    except ZeroDivisionError:
        print("Cannot divide by zero")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Try-Except-Else-Finally

```python
def read_and_process_file(filename):
    file_handle = None
    try:
        file_handle = open(filename, 'r')
        content = file_handle.read()
        data = int(content)
    except FileNotFoundError:
        print(f"File {filename} not found")
        return None
    except ValueError:
        print("File content is not a valid number")
        return None
    else:
        # Executes only if no exception occurred
        print("File processed successfully")
        return data * 2
    finally:
        # Always executes, cleanup code
        if file_handle:
            file_handle.close()
            print("File closed")
```

### Context Managers (Automatic Cleanup)

```python
# Better approach using context manager
def read_and_process_file(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            data = int(content)
            return data * 2
    except FileNotFoundError:
        print(f"File {filename} not found")
        return None
    except ValueError:
        print("File content is not a valid number")
        return None
    # File automatically closed, no finally needed
```

---

## 12. Warning Categories

Warnings are not exceptions but alert users to potential issues.

```python
import warnings

# DeprecationWarning
warnings.warn("This function is deprecated", DeprecationWarning)

# UserWarning
warnings.warn("This is a user warning", UserWarning)

# FutureWarning
warnings.warn("This behavior will change in future", FutureWarning)

# Custom warning handling
def risky_operation():
    warnings.warn("This operation is risky", RuntimeWarning)
    return "result"

# Filter warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
result = risky_operation()  # Warning suppressed
```

---

## Summary

### Exception Handling Best Practices

1. **Be Specific**: Catch specific exceptions rather than using bare `except:`
2. **Use Finally**: For cleanup operations that must always execute
3. **Context Managers**: Use `with` statements for resource management
4. **Custom Exceptions**: Create custom exceptions for application-specific errors
5. **Don't Silence**: Avoid catching exceptions without handling them
6. **Log Errors**: Always log unexpected exceptions for debugging
7. **Fail Fast**: Raise exceptions early when invalid state is detected
8. **Document**: Document what exceptions your functions can raise

### Common Exception Categories

| Category | Exceptions | Use Case |
|----------|-----------|----------|
| **Value Errors** | ValueError, TypeError | Invalid arguments or data types |
| **Lookup Errors** | KeyError, IndexError, AttributeError | Missing keys, indices, or attributes |
| **I/O Errors** | FileNotFoundError, PermissionError, EOFError | File and I/O operations |
| **Arithmetic** | ZeroDivisionError, OverflowError | Mathematical operations |
| **Runtime** | RecursionError, MemoryError | Runtime resource issues |
| **Import** | ImportError, ModuleNotFoundError | Module loading issues |
| **Network** | ConnectionError, TimeoutError | Network operations |
| **System** | SystemExit, KeyboardInterrupt | System-level events |

### Quick Reference

```python
# Basic exception handling
try:
    risky_operation()
except SpecificError as e:
    handle_error(e)
except AnotherError:
    handle_another_error()
else:
    success_action()
finally:
    cleanup()

# Raising exceptions
raise ValueError("Invalid value")
raise CustomError("Something went wrong") from original_exception

# Re-raising
try:
    operation()
except SomeError:
    log_error()
    raise  # Re-raise same exception

# Custom exceptions
class MyCustomError(Exception):
    pass
```
