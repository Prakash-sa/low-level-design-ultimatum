Abstract Class:
An abstract class, defined using the abc module (Abstract Base Classes), acts as a blueprint for other classes. It can contain both abstract methods (methods declared but not implemented) and concrete methods (methods with full implementations). Abstract classes cannot be instantiated directly; subclasses must implement all abstract methods to be instantiable.
Example of an Abstract Class:
Python

# Interface vs Abstract Class

This note explains the practical differences between abstract classes and interfaces in Python, provides runnable examples, introduces `Protocol` as a lightweight interface alternative, and gives interview-style questions with answers.

---

## Quick summary

- **Abstract class**: a class (usually inheriting from `abc.ABC`) that can define abstract methods and concrete methods. It acts as a blueprint and can provide shared implementation.
- **Interface**: not a distinct language construct in Python, but commonly implemented as an all-abstract class using `abc.ABC` or via `typing.Protocol` (PEP 544) to express structural typing. Interfaces define a contract (a set of methods) that implementing classes must provide.

When to use which:
- Use an **abstract class** when you want a shared base implementation and to enforce a common API.
- Use an **interface / Protocol** when you want to specify behavior (a "can-do" relationship) without prescribing implementation or inheritance.

---

## Abstract class (with examples)

Use the `abc` module. Abstract classes can contain some implemented (concrete) methods and some abstract methods.

Example (Vehicle):

```python
from abc import ABC, abstractmethod

class Vehicle(ABC):
    @abstractmethod
    def start_engine(self):
        """Start engine — must be implemented by subclasses."""
        pass

    def stop_engine(self):
        """A concrete method shared by all vehicles."""
        print("Engine stopped.")


class Car(Vehicle):
    def start_engine(self):
        print("Car engine started with a key.")


class Motorcycle(Vehicle):
    def start_engine(self):
        print("Motorcycle engine started with a kickstarter.")


if __name__ == '__main__':
    car = Car()
    car.start_engine()
    car.stop_engine()

    motorcycle = Motorcycle()
    motorcycle.start_engine()
    motorcycle.stop_engine()

    # vehicle = Vehicle()  # TypeError: Can't instantiate abstract class Vehicle
```

Notes and advanced tips:
- You can provide default behavior in concrete methods on an abstract class to reduce code duplication.
- You can define `@abstractmethod` on `@classmethod` and `@staticmethod` too.
- Use `ABC.register(SomeClass)` to register a class as a virtual subclass of an ABC without inheritance.

---

## Interface via ABC (all-abstract base class)

An interface is commonly represented by an ABC where every method is abstract. It expresses a strict contract.

Example (Flyable):

```python
from abc import ABC, abstractmethod

class Flyable(ABC):
    @abstractmethod
    def take_off(self):
        pass

    @abstractmethod
    def land(self):
        pass


class Airplane(Flyable):
    def take_off(self):
        print("Airplane taking off from runway.")

    def land(self):
        print("Airplane landing on runway.")


class Drone(Flyable):
    def take_off(self):
        print("Drone taking off vertically.")

    def land(self):
        print("Drone landing vertically.")


if __name__ == '__main__':
    airplane = Airplane()
    airplane.take_off()
    airplane.land()

    drone = Drone()
    drone.take_off()
    drone.land()
```

Because Python supports multiple inheritance you can implement multiple ABC-based interfaces by inheriting from several ABCs.

---

## Structural interfaces: `typing.Protocol`

`Protocol` (from `typing`) provides structural typing — duck-typing enforced by static checkers like `mypy` rather than runtime ABC checks. It is often a more flexible, lighter-weight way to express "interfaces".

Example using `Protocol`:

```python
from typing import Protocol

class FlyableProto(Protocol):
    def take_off(self) -> None: ...
    def land(self) -> None: ...


class Bird:
    def take_off(self):
        print("Bird flaps wings and takes off")

    def land(self):
        print("Bird lands")


def launch(flyable: FlyableProto):
    flyable.take_off()


if __name__ == '__main__':
    b = Bird()
    launch(b)  # Works fine — Bird matches the Protocol shape
```

Use `Protocol` when you want interface-like behavior without forcing inheritance.

---

## Key differences (concise)

- **Default implementation**: Abstract classes may provide concrete methods; interfaces (pure ABC or Protocol) typically don't.
- **Inheritance vs structural typing**: ABCs are nominal (require explicit inheritance or registration). `Protocol` is structural (duck-typed).
- **Multiple contracts**: With ABCs you can implement multiple interfaces via multiple inheritance. Protocols let any object match if it has the required methods.
- **Runtime checks**: `isinstance(obj, ABC)` works for ABCs (including registered virtual subclasses). `Protocol` is primarily for static checking; runtime isinstance checks are not typical.

---

## Common pitfalls and best practices

- Don't use abstract classes just to hold constants; use modules or dataclasses for that.
- Prefer `Protocol` for light-weight interfaces when you don't need runtime registration or enforcement.
- If many classes share implementation, put shared behavior into an abstract base class to avoid duplication.
- Avoid deep inheritance trees; prefer composition when it leads to clearer designs.

---

## Interview questions (with answers)

### Basic

1) Q: What is the main difference between an abstract class and an interface in Python?

   A: An abstract class (using `abc.ABC`) can contain both abstract and concrete methods and is nominal (requires inheritance). An interface (when represented by an all-abstract ABC) defines only abstract methods; `Protocol` provides a structural-interface alternative (duck-typing) preferred for flexibility.

2) Q: Can you instantiate an abstract class? Why or why not?

   A: No — abstract classes that contain unimplemented `@abstractmethod`s cannot be instantiated. Python raises `TypeError` to prevent creating incomplete objects that don't fulfill required behavior.

3) Q: When would you prefer a `Protocol` over an `ABC`?

   A: Use `Protocol` when you want structural typing (duck-typing), no forced inheritance, and want static checks from tools like `mypy`. Use `ABC` when you need runtime enforcement or to provide shared implementation.

### Intermediate

4) Q: Show a small code example where an abstract class provides a default implementation and a subclass overrides it.

   A:

```python
from abc import ABC, abstractmethod

class Writer(ABC):
    @abstractmethod
    def write(self, data: str):
        pass

    def write_line(self, data: str):
        self.write(data + "\n")


class ConsoleWriter(Writer):
    def write(self, data: str):
        print(data, end='')


cw = ConsoleWriter()
cw.write_line('Hello')
```

5) Q: How can you register a class as a virtual subclass of an abstract base class?

   A: Use `MyABC.register(SomeClass)`. This marks `SomeClass` as a virtual subclass for `isinstance`/`issubclass` checks without changing its inheritance chain.

### Advanced

6) Q: Explain trade-offs between using multiple inheritance of ABCs vs composition with interfaces.

   A: Multiple inheritance lets a class implement multiple contracts and reuse code from multiple bases, but it can cause method resolution complexity (MRO) and tight coupling. Composition favors single-responsibility and clear dependencies but requires explicit delegation; it's often easier to reason about, test, and maintain.

7) Q: How would you design a plugin system where plugins can optionally implement a `configure()` hook? Which approach would you choose and why?

   A: Use an ABC where `configure` is optional (provide a concrete no-op default in the base class) or define a `Plugin` Protocol with an optional `configure` method (using `typing_extensions` `@runtime_checkable` and `Protocol` for runtime checks if needed). If runtime discovery and registration are required, ABCs with `register` and `entry_points` work well. If maximum flexibility and light coupling are important, `Protocol` is better.

8) Q: Show how to declare and check an abstract class method (`@classmethod`) as abstract.

   A:

```python
from abc import ABC, abstractmethod

class Base(ABC):
    @classmethod
    @abstractmethod
    def create(cls, *args, **kwargs):
        pass


class Impl(Base):
    @classmethod
    def create(cls, name):
        return cls()

# Impl.create('x') -> works
```

---

## File location

`/Users/prakashsaini/Desktop/low-level-design-ultimatum/Introduction/INterface vs Abstract Class.md`

---

If you want, I can also:
- add a short diagram (ASCII) comparing nominal vs structural typing,
- add unit tests demonstrating the runtime errors for instantiating ABCs,
- or convert this into a slide-friendly README for interview prep.

Which of these would you like next?

