# Low-Level Design and OOP Glossary

## Topic Tags

| Letter | Topics |
| --- | --- |
| A | [Abstraction](#abstraction), [Abstract Class](#abstract-class), [Actor](#actor), [Adapter Pattern](#adapter-pattern), [Aggregation](#aggregation), [Association](#association) |
| B | [Builder Pattern](#builder-pattern), [Business Invariant](#business-invariant) |
| C | [Class](#class), [Class Diagram](#class-diagram), [Command Pattern](#command-pattern), [Composition](#composition), [Concurrency](#concurrency), [Constructor](#constructor) |
| D | [Dependency](#dependency), [Dependency Injection](#dependency-injection), [Dependency Inversion Principle](#dependency-inversion-principle), [Design Pattern](#design-pattern), [Domain Model](#domain-model), [DTO](#dto) |
| E | [Encapsulation](#encapsulation), [Entity](#entity), [Enum](#enum) |
| F | [Facade Pattern](#facade-pattern), [Factory Pattern](#factory-pattern) |
| G | [God Class](#god-class) |
| H | [Has-A Relationship](#has-a-relationship) |
| I | [Inheritance](#inheritance), [Interface](#interface), [Interface Segregation Principle](#interface-segregation-principle), [Is-A Relationship](#is-a-relationship) |
| L | [Liskov Substitution Principle](#liskov-substitution-principle) |
| M | [Method](#method) |
| O | [Object](#object), [Observer Pattern](#observer-pattern), [Open Closed Principle](#open-closed-principle) |
| P | [Polymorphism](#polymorphism) |
| R | [Repository](#repository), [Responsibility](#responsibility) |
| S | [Service](#service), [Single Responsibility Principle](#single-responsibility-principle), [Singleton Pattern](#singleton-pattern), [State Pattern](#state-pattern), [Strategy Pattern](#strategy-pattern) |
| U | [Use Case](#use-case) |
| V | [Value Object](#value-object) |

---

## Abstraction

Definition: Abstraction is the OOP principle of exposing only essential behavior while hiding internal implementation details.

Read-aloud note: "I use abstraction to give clients a simple contract and keep complex implementation details hidden behind public methods or interfaces."

Example: `PaymentProcessor.process(amount)` hides whether the payment is handled by card, wallet, or UPI.

## Abstract Class

Definition: An abstract class is a partially implemented base class that defines shared behavior and requires subclasses to implement specific methods.

Read-aloud note: "I use an abstract class when subclasses share common code but must still provide their own implementation for some behavior."

Example: `Vehicle` can define `start()` behavior while requiring each subclass to implement `calculateFare()`.

## Actor

Definition: An actor is an external user, role, or system that interacts with the design to perform a use case.

Read-aloud note: "I identify actors first because they help discover the main workflows and public methods the design must support."

Example: In a parking lot system, actors can be `Driver`, `GateAttendant`, and `Admin`.

## Adapter Pattern

Definition: The Adapter pattern converts one interface into another interface expected by the client.

Read-aloud note: "I use Adapter when I need to integrate an existing or third-party class without changing the client code."

Example: `StripePaymentAdapter` implements `PaymentProcessor` while internally calling Stripe-specific APIs.

## Aggregation

Definition: Aggregation is a weak whole-part relationship where the child can exist independently of the parent.

Read-aloud note: "I use aggregation when one object references another, but does not control its lifecycle."

Example: A `Team` has `Players`, but a `Player` can still exist if the `Team` is deleted.

## Association

Definition: Association is a relationship where one class knows about or uses another class.

Read-aloud note: "Association shows that two classes collaborate, but it does not necessarily mean ownership."

Example: A `Doctor` is associated with many `Patients`.

## Builder Pattern

Definition: The Builder pattern constructs complex objects step by step.

Read-aloud note: "I use Builder when an object has many optional fields or construction parameters and a constructor would become unreadable."

Example: `ReportBuilder.setTitle().setDateRange().setFormat().build()` creates a complex report.

## Business Invariant

Definition: A business invariant is a rule that must always remain true for the system to be valid.

Read-aloud note: "I call out invariants because low-level design is not only about classes, it is also about preventing invalid state."

Example: A confirmed seat booking must not overlap with another confirmed booking for the same seat and show.

## Class

Definition: A class is a blueprint that defines state and behavior shared by objects of that type.

Read-aloud note: "I create a class when a concept has meaningful responsibility, behavior, or lifecycle in the domain."

Example: `ParkingTicket` can store ticket number, entry time, assigned spot, and payment status.

## Class Diagram

Definition: A class diagram is a UML-style representation of classes, attributes, methods, and relationships.

Read-aloud note: "I use a class diagram to communicate ownership, collaboration, and extension points clearly."

Example: A movie booking diagram can show `Theater`, `Screen`, `Show`, `Seat`, `Booking`, and `Payment`.

## Command Pattern

Definition: The Command pattern represents an action as an object.

Read-aloud note: "I use Command when actions need to be queued, logged, retried, undone, or executed later."

Example: A text editor can represent `InsertTextCommand` and `DeleteTextCommand` for undo and redo.

## Composition

Definition: Composition is a strong whole-part relationship where the parent owns the child lifecycle.

Read-aloud note: "I use composition when a child object is a real part of the parent and should not live independently."

Example: A `Board` is composed of `Cells`; if the board is removed, its cells are removed too.

## Concurrency

Definition: Concurrency means multiple operations may execute at overlapping times and access shared state.

Read-aloud note: "I mention concurrency when two users can modify the same resource, because checking and updating must be atomic."

Example: Two users trying to book the same movie seat must not both succeed.

## Constructor

Definition: A constructor initializes an object into a valid starting state.

Read-aloud note: "I keep constructors focused on creating a valid object, not doing heavy business workflows or external calls."

Example: `Account(accountId, owner, openingBalance)` should validate that opening balance is not negative.

## Dependency

Definition: A dependency is a relationship where one class needs another class to perform its responsibility.

Read-aloud note: "I track dependencies because too many direct dependencies make a class hard to test and change."

Example: `OrderService` depends on `PaymentProcessor` to complete checkout.

## Dependency Injection

Definition: Dependency injection provides a class its dependencies from the outside instead of creating them internally.

Read-aloud note: "I use dependency injection to decouple classes and make them easier to test with mocks or alternate implementations."

Example: `OrderService(PaymentProcessor processor)` receives the payment processor through its constructor.

## Dependency Inversion Principle

Definition: The Dependency Inversion Principle says high-level modules should depend on abstractions, not concrete implementations.

Read-aloud note: "I apply DIP when business logic should not be tightly coupled to a specific database, payment provider, or notification channel."

Example: `CheckoutService` depends on `PaymentGateway`, not directly on `StripeGateway`.

## Design Pattern

Definition: A design pattern is a reusable solution to a common software design problem.

Read-aloud note: "I use patterns only when they simplify the design or make extension cleaner."

Example: Strategy fits when discount calculation can vary by coupon, membership, or campaign.

## Domain Model

Definition: A domain model is the set of classes and relationships that represent the core business concepts and rules.

Read-aloud note: "I keep business behavior in the domain model instead of scattering rules across controllers or utility classes."

Example: In a library system, `BookItem`, `Member`, `Loan`, `Reservation`, and `Fine` form the domain model.

## DTO

Definition: A Data Transfer Object carries data between layers or across boundaries without business logic.

Read-aloud note: "I use DTOs to separate external request or response shape from internal domain objects."

Example: `CreateBookingRequest` can contain `showId`, `seatIds`, and `userId`.

## Encapsulation

Definition: Encapsulation bundles data with behavior and restricts direct access to internal state.

Read-aloud note: "I use encapsulation to protect invariants by forcing state changes through controlled methods."

Example: `Account.withdraw(amount)` validates balance instead of allowing direct modification of `balance`.

## Entity

Definition: An entity is a domain object with unique identity and lifecycle.

Read-aloud note: "I model something as an entity when identity matters even if its attributes change."

Example: A `User` remains the same user even if their email or phone number changes.

## Enum

Definition: An enum represents a fixed set of named constants.

Read-aloud note: "I use enums for limited states or types to avoid invalid string values."

Example: `BookingStatus` can be `PENDING`, `CONFIRMED`, `CANCELLED`, or `EXPIRED`.

## Facade Pattern

Definition: The Facade pattern provides a simplified interface over a complex subsystem.

Read-aloud note: "I use Facade when a client should not need to coordinate many low-level components directly."

Example: `BookingFacade.bookTicket()` can coordinate seat lock, payment, booking creation, and notification.

## Factory Pattern

Definition: The Factory pattern centralizes object creation logic and hides construction details.

Read-aloud note: "I use Factory when object creation varies by type or condition."

Example: `VehicleFactory.createVehicle(type)` can return `Car`, `Bike`, or `Truck`.

## God Class

Definition: A god class is an oversized class that owns too many responsibilities.

Read-aloud note: "I avoid god classes by splitting responsibilities into focused services, entities, strategies, and repositories."

Example: `ParkingLotManager` should not handle spot assignment, payment, ticket printing, notifications, and reporting all by itself.

## Has-A Relationship

Definition: A Has-A relationship means one object contains, owns, or uses another object.

Read-aloud note: "I model Has-A relationships with composition or aggregation instead of inheritance."

Example: A `Car` has an `Engine`.

## Inheritance

Definition: Inheritance lets a child class derive state or behavior from a parent class.

Read-aloud note: "I use inheritance only for a true Is-A relationship where the child can safely substitute the parent."

Example: `Car` and `Bike` can inherit from `Vehicle` if all vehicles share meaningful behavior.

## Interface

Definition: An interface defines a behavior contract that implementing classes must provide.

Read-aloud note: "I use interfaces at variation points so high-level code depends on capabilities, not concrete classes."

Example: `NotificationSender` can be implemented by `EmailSender`, `SmsSender`, and `PushSender`.

## Interface Segregation Principle

Definition: The Interface Segregation Principle says clients should not depend on methods they do not use.

Read-aloud note: "I split large interfaces into smaller focused interfaces so classes implement only relevant behavior."

Example: Use `Printable` and `Scannable` instead of forcing every machine to implement one large `Machine` interface.

## Is-A Relationship

Definition: An Is-A relationship means a subclass is a valid specialized form of its parent type.

Read-aloud note: "I verify Is-A relationships with substitutability, not just shared fields."

Example: A `SavingsAccount` is an `Account`, but a `User` is not a `DatabaseRecord` just because it can be saved.

## Liskov Substitution Principle

Definition: The Liskov Substitution Principle says subclasses must be usable wherever the base class is expected without breaking correctness.

Read-aloud note: "I check LSP before using inheritance because a subclass should not surprise callers of the parent type."

Example: A `ReadOnlyFile` subclass that throws on `write()` may violate expectations of a general `File` type with writable behavior.

## Method

Definition: A method is behavior defined inside a class.

Read-aloud note: "I design public methods around use cases and keep method names clear and action-oriented."

Example: `Booking.confirm()`, `Booking.cancel()`, and `Booking.expire()` are clearer than directly setting status.

## Object

Definition: An object is a runtime instance of a class with its own state and behavior.

Read-aloud note: "Objects collaborate by calling methods on each other, and each object should protect its own valid state."

Example: `ticket123` is an object of class `ParkingTicket`.

## Observer Pattern

Definition: The Observer pattern defines a one-to-many dependency where observers are notified when a subject changes state.

Read-aloud note: "I use Observer when multiple components need to react to an event without tightly coupling the subject to each component."

Example: When an order is placed, email, invoice, and analytics observers can react.

## Open Closed Principle

Definition: The Open Closed Principle says software entities should be open for extension but closed for modification.

Read-aloud note: "I apply OCP by adding new classes for new behavior instead of repeatedly editing stable code."

Example: Add `WalletPaymentStrategy` without modifying existing card payment logic.

## Polymorphism

Definition: Polymorphism allows different classes to be used through a common interface while providing different implementations.

Read-aloud note: "I use polymorphism to remove conditionals when behavior depends on object type."

Example: `pricingStrategy.calculatePrice(order)` works for `RegularPricing`, `SurgePricing`, or `DiscountPricing`.

## Repository

Definition: A repository abstracts data access for domain objects.

Read-aloud note: "I use repositories to keep persistence logic separate from business logic."

Example: `BookingRepository.findById(id)` and `BookingRepository.save(booking)` hide storage details.

## Responsibility

Definition: A responsibility is the specific job assigned to a class, method, or module.

Read-aloud note: "Every class I introduce should have one clear responsibility that I can explain in one sentence."

Example: `SeatLockManager` is responsible for temporarily locking seats during booking.

## Service

Definition: A service coordinates a use case or business operation that does not naturally belong to one entity.

Read-aloud note: "I use services to orchestrate workflows while keeping domain rules inside domain objects when possible."

Example: `BookingService` coordinates seat availability, locking, payment, and booking confirmation.

## Single Responsibility Principle

Definition: The Single Responsibility Principle says a class should have one clear reason to change.

Read-aloud note: "I apply SRP by separating unrelated responsibilities into different classes."

Example: Split payment processing, invoice generation, and notification sending into separate classes.

## Singleton Pattern

Definition: The Singleton pattern ensures a class has only one shared instance and provides global access to it.

Read-aloud note: "I mention Singleton carefully because global state can make testing and concurrency harder; dependency injection is often cleaner."

Example: A configuration provider may be singleton-like if the application needs one shared configuration source.

## State Pattern

Definition: The State pattern lets an object change behavior when its internal state changes.

Read-aloud note: "I use State when many conditionals depend on lifecycle state."

Example: A vending machine behaves differently in `IdleState`, `HasMoneyState`, `DispensingState`, and `SoldOutState`.

## Strategy Pattern

Definition: The Strategy pattern defines interchangeable algorithms behind a common interface.

Read-aloud note: "I use Strategy when a policy or algorithm can vary independently from the main object."

Example: `ParkingSpotAssignmentStrategy` can be nearest-first, random, or preferred-zone based.

## Use Case

Definition: A use case is a specific user goal or workflow the system must support.

Read-aloud note: "I use use cases to validate that the class diagram actually supports real behavior."

Example: In movie booking, a main use case is selecting seats, locking them, paying, and confirming the booking.

## Value Object

Definition: A value object is an immutable domain object defined by its values rather than unique identity.

Read-aloud note: "I use value objects for concepts where equality is based on fields, not identity."

Example: Two `Money(100, "USD")` objects are equal if amount and currency are the same.
