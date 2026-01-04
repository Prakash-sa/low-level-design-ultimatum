# Low-Level Design Ultimatum

A comprehensive repository of object-oriented design concepts, patterns, and system design examples for interview preparation and learning.

## 📚 What's Included

### Introduction to OOP
- [Abstraction](Introduction/Abstraction.md) — Exposing simple interfaces while hiding complexity
- [Encapsulation](Introduction/Encapsulation.md) — Controlling access to data and implementation details
- [Inheritance](Introduction/Inheritance.md) — Modeling IS-A relationships between classes
- [Polymorphism](Introduction/Polymorphism.md) — Compile-time and runtime polymorphism
- [Class vs Instance Variables](Introduction/Class%20Variable%20vs%20Instance%20Variable.md) — Understanding shared vs. unique attributes
- [OOP Principles (All-in-One)](Introduction/OOP%20Principles.md) — Comprehensive overview

### Design Patterns
- **Behavioral**: Command, Iterator, Observer, Strategy
- **Creational**: Abstract Factory, Builder, Factory, Singleton
- **Structural**: Adapter, Composite, Decorator, Facade

### System Design Examples
Real-world examples including:
- Airline Management System
- Train Platform Management System
- Amazon Locker System
- ATM System
- Library Management System
- Parking Lot System
- Hotel Management System
- And 10+ more...

### Company Tagged Examples
- Amazon
- Uber

---

## 🏗️ Core Engineering Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **DRY** | Avoid duplication; extract common logic | Create shared utility instead of copying code |
| **KISS** | Prefer simple solutions | Direct algorithms over complex abstractions |
| **YAGNI** | Build only what's needed now | Skip speculative features |
| **Separation of Concerns** | Split responsibilities by layer | Use repository pattern for data access |
| **Law of Demeter** | Minimize knowledge of internal details | Use facade to hide subsystem complexity |
| **Fail Fast** | Validate early and raise errors immediately | Check input validity at entry |
| **Idempotency** | Operations safely retryable | Use request IDs to prevent duplicates |

---

## 🎯 SOLID Principles

| Principle | Focus | Example |
|-----------|-------|---------|
| **Single Responsibility** | One reason to change | Separate file saving from data processing |
| **Open/Closed** | Extend, don't modify | Strategy pattern for payment methods |
| **Liskov Substitution** | Subtypes usable as base type | ✗ Square ⊂ Rectangle (breaks LSP) |
| **Interface Segregation** | Small interfaces | Separate "Printable" and "Savable" |
| **Dependency Inversion** | Depend on abstractions | Inject `PaymentGateway` interface |

---

## 📖 OOP Fundamentals

**Class vs Instance Variables**:
- **Instance attributes**: unique per object, live in `obj.__dict__`
- **Class attributes**: shared across instances, live in `Class.__dict__`
- Modifying via instance creates shadowing instance attribute

**Attribute Lookup Order**:
1. Check instance `__dict__`
2. Check class `__dict__` and MRO
3. Call `__getattr__` or raise `AttributeError`

---

## 🤔 Common Interview Q&A

**Q: What's the difference between class and instance variables?**  
A: Class variables are shared across all instances (`Class.__dict__`). Instance variables are unique per object (`obj.__dict__`). Accessing via instance first checks `obj.__dict__`, then `Class.__dict__`. Modifying creates a shadowing instance attribute.

**Q: When do you choose inheritance vs composition?**  
A: Use inheritance for strict IS-A relationships with shared behavior contracts. Prefer composition to assemble behaviors dynamically and avoid tight coupling—composition is more flexible and testable.

**Q: Explain LSP with an example.**  
A: Subtypes must be usable anywhere the base type is expected. Classic violation: `Square` inheriting `Rectangle` and setting width/height independently breaks LSP. Fix: use different abstraction (`Shape` with `area()`) or avoid misleading inheritance.

**Q: What are signs of SRP violation?**  
A: Class changes for multiple reasons (business rules, logging, persistence). Split into: business service, repository, logger.

**Q: What is YAGNI and how do you apply it?**  
A: Build only what's needed now. Avoid premature generalization, speculative configuration, or complex extension points.

**Q: How to apply KISS in API design?**  
A: Use clear, minimal endpoints with predictable inputs/outputs. Reduce optional parameters; provide sensible defaults and versioning.

**Q: DRY vs deduplication trade-off?**  
A: DRY removes duplication, but over-abstracting harms readability. Extract only cohesive, stable logic; code that evolves differently may be safer than a leaky abstraction.

**Q: Explain Dependency Inversion with an example.**  
A: Depend on interfaces (e.g., `PaymentGateway`) instead of concrete classes (`Stripe`). Inject the implementation; high-level modules stay stable while low-level details vary.

**Q: How to design idempotent operations?**  
A: Use natural keys or request IDs; ensure repeated calls have the same effect (e.g., PUT replaces state, POST with idempotency key prevents duplicates).

**Q: What's the difference between overloading and overriding?**  
A: Overloading (compile-time polymorphism) is multiple methods with same name, different signatures. Overriding (runtime polymorphism) replaces parent method in subclass.

**Q: Inheritance vs Composition—which is better?**  
A: Composition is generally preferred ("composition over inheritance"). Inheritance creates tight coupling and fragile base class problem; composition provides flexibility and easier testing.

---

## 📚 Resources

- [CodeTekTeach - Design Patterns](https://youtube.com/watch?v=c6sMYunKIB8)
- [Medium - 23 OOP Design Patterns in Python](https://medium.com/@cautaerts/all-23-oop-software-design-patterns-with-examples-in-python-cac1d3f4f4d5)
- [Python Patterns Guide](https://python-patterns.guide/)
- [CodeSignal - Mastering Design Patterns](https://codesignal.com/learn/paths/mastering-design-patterns-with-python)
- [Refactoring Guru - Design Patterns](https://refactoring.guru/design-patterns)
- [AlgoMaster - LLD Guide](https://algomaster.io/learn/lld/what-is-lld)

---

## 🚀 How to Use This Repository

1. **Start with Introduction/** for OOP fundamentals
2. **Explore Design Pattern/** examples for patterns in action
3. **Study Examples/** for real-world system design scenarios
4. **Reference Company Tagged/** for company-specific insights
5. Use code examples as starting points for practice programs and interview prep

**Tips for Interview Success**:
- Understand the "why" behind each principle
- Practice explaining trade-offs concisely
- Walk through examples step-by-step
- Discuss scaling and edge cases
- Be ready to extend designs based on new requirements
