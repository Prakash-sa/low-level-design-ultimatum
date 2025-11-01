# Inheritance

Inheritance lets you create a new class (derived) from an existing class (base). The derived class reuses and extends behavior and state from the base class.

## When to use

- Use inheritance to model an IS-A relationship (e.g., Car IS-A Vehicle).
- Avoid using inheritance just to reuse code; prefer composition when appropriate.

## Common types of inheritance

- Single inheritance — a class extends one base class.
- Multiple inheritance — a class extends more than one base class (language-dependent).
- Multilevel inheritance — a class derives from a class which itself derives from another.
- Hierarchical inheritance — multiple classes extend the same base class.
- Hybrid inheritance — a combination of the above.

## How to implement

-  you have to explicitly call it using super()

## Advantages

- Reusability: share common code in base classes.
- Extensibility: extend functionality in derived classes without modifying the base.
- Localized changes: updates to base behavior propagate to subclasses.

## Notes and caveats

- Some languages restrict multiple inheritance (e.g., Java) to avoid complexity; they offer interfaces/traits instead.
- Overuse of inheritance can lead to fragile hierarchies; prefer composition for flexible designs.
