# Low-Level-Design-Ultimatum

This repo contains concise explanations and examples of core object-oriented design concepts used in low-level design (LLD). The goal is to provide quick reference notes and small code examples to help with interviews and study.

Contents

- Introduction files:
  - `Introduction/Abstraction.md` — Abstraction: exposing a simple interface and hiding implementation.
  - `Introduction/Encapsulation.md` — Encapsulation: controlling access to data and implementation details.
  - `Introduction/Inheritance.md` — Inheritance: modelling IS-A relationships between classes.
  - `Introduction/Polymorphism.md` — Polymorphism: compile-time (overloading) and runtime (overriding) polymorphism.

Key concepts covered

- Attributes, methods, classes, and objects
- Principles of OOP: Encapsulation, Abstraction, Inheritance, Polymorphism

Quick links

- [Abstraction](Introduction/Abstraction.md)
- [Encapsulation](Introduction/Encapsulation.md)
- [Inheritance](Introduction/Inheritance.md)
- [Polymorphism](Introduction/Polymorphism.md)
- [Class vs Instance Variables](Introduction/Class Variable vs Insatance Variable.md)
- [Python Built-in Exceptions](Introduction/Python Built-in Exceptions.md)
 - [OOP Principles (All-in-One)](Introduction/OOP Principles.md)

How to use

- Read the files under `Introduction/` for short explanations and examples.
- Use the examples as a starting point for small practice programs or interview prep.

## Basics

- Instance attributes maintain unique data for each object, while class attributes provide a shared value across all instances unless overridden.

### Core Engineering Principles

- **DRY (Don't Repeat Yourself):** Avoid duplication. Extract common logic into functions, classes, or modules. Improves maintainability and reduces bugs.
- **KISS (Keep It Simple, Stupid):** Prefer simple solutions over clever ones. Simplicity eases understanding, testing, and refactoring.
- **YAGNI (You Aren’t Gonna Need It):** Don’t build features until they’re actually needed. Reduces waste and complexity.
- **Separation of Concerns:** Split responsibilities across modules/layers (e.g., UI, domain, persistence). Each part focuses on a single concern.
- **Law of Demeter (Principle of Least Knowledge):** Minimize knowledge of internal details of other objects; interact through clear interfaces.
- **Fail Fast:** Validate early, raise errors immediately on invalid state to prevent cascading failures.
- **Idempotency:** Design operations that can be safely retried without unintended side effects (important for APIs and distributed systems).

### SOLID Principle

S – Single Responsibility Principle (SRP)
➜ One class = one reason to change
Example: separate file saving logic from data processing logic.

O – Open/Closed Principle (OCP)
➜ Classes open for extension, closed for modification
Example: strategy pattern for payment methods.

L – Liskov Substitution Principle (LSP)
➜ Subtypes must be usable as base type without breaking logic.
Example: Shape hierarchy with Rectangle and Square.
 A classic violation occurs with a Rectangle and Square hierarchy, where a Square cannot be substituted for a Rectangle because setting the width and height independently breaks the Square's required equal dimensions. 

I – Interface Segregation (ISP)
➜ Prefer many small interfaces to one big one.
Example: separate “Printable” and “Savable” interfaces.

D – Dependency Inversion (DIP)
➜ Depend on abstractions, not concrete classes.

Example: inject dependencies via constructor or DI container.
Without DIP: A Switch class directly instantiates and uses a Lamp class.
With DIP: An ISwitchClient interface is introduced, and both Switch and Lamp depend on it. Switch uses the ISwitchClient interface, and Lamp implements it. This means Switch doesn't know or care about the specific Lamp implementation and can be used with any other class that implements ISwitchClient. 

## Common Interview Q&A

- **Q: What’s the difference between class and instance variables?**
  - **A:** Class variables are shared across all instances and live in the class `__dict__`. Instance variables are unique per object and live in the instance `__dict__`. Modifying a class variable via an instance creates a shadowing instance attribute.

- **Q: When do you choose inheritance vs composition?**
  - **A:** Use inheritance for strict IS-A relationships and shared behavior contracts. Prefer composition to assemble behaviors dynamically and avoid tight coupling; composition is more flexible and testable.

- **Q: Explain LSP with an example.**
  - **A:** Subtypes must be usable anywhere the base type is expected. A classic violation: making `Square` inherit `Rectangle` and changing width sets height, breaking callers that rely on independent width/height. Fix via different abstraction (e.g., `Shape` with area) or avoid misleading inheritance.

- **Q: What are signs you’re violating SRP?**
  - **A:** Class changes for multiple reasons (e.g., business rules, logging, persistence). Split responsibilities: business service, repository, logger.

- **Q: What is YAGNI and how do you apply it?**
  - **A:** Build only what’s needed now. Avoid premature generalization, speculative configuration flags, or complex extension points until requirements demand them.

- **Q: How do you apply KISS in API design?**
  - **A:** Favor clear, minimal endpoints, predictable inputs/outputs, and consistent error models. Reduce optional params; provide sensible defaults and versioning.

- **Q: What’s DRY vs deduplication trade-off?**
  - **A:** DRY removes duplication, but over-abstracting can harm readability. Extract only cohesive, stable logic; duplicated code that evolves differently may be safer than a leaky abstraction.

- **Q: Explain Dependency Inversion with a quick example.**
  - **A:** Depend on interfaces (e.g., `PaymentGateway`) instead of concrete classes (`Stripe`). Inject the implementation; high-level modules stay stable while low-level details vary.

- **Q: How do you design idempotent operations?**
  - **A:** Use natural keys or request IDs; ensure repeated calls have the same effect (e.g., PUT replaces state, POST with idempotency key prevents duplicates).

## Sources

- [CodeTekTeach](http://youtube.com/watch?v=c6sMYunKIB8)
- [Medium](https://medium.com/@cautaerts/all-23-oop-software-design-patterns-with-examples-in-python-cac1d3f4f4d5)
- [Guide](https://python-patterns.guide/)
- [CodeSignal](https://codesignal.com/learn/paths/mastering-design-patterns-with-python)
- [Design Patterns](https://refactoring.guru/design-patterns)
- [AlgoMaster](https://algomaster.io/learn/lld/what-is-lld)
