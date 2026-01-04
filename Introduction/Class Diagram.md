# UML Class Diagrams: Complete Guide

> **What is a Class Diagram?**
> A class diagram is a type of static structure diagram used in UML to describe the structure of a system by showing the system's classes, their attributes, methods, and the relationships among the classes.

---

## 📋 Table of Contents
1. [Access Modifiers](#access-modifiers)
2. [Associations](#associations)
3. [Relationships](#relationships)
4. [Dependency](#dependency)
5. [Real-World Examples](#real-world-examples)
6. [Interview Questions](#interview-questions)
7. [Summary](#summary)

---

## 🔐 Access Modifiers

Access modifiers control the visibility and accessibility of class members (attributes and methods). They define which parts of your code can access specific members.

### Visibility Levels

| Symbol | Name | Visibility | Use Case |
|--------|------|-----------|----------|
| `+` | **Public** | Everywhere | General APIs, methods callers need to use |
| `-` | **Private** | Within class only | Internal implementation details |
| `#` | **Protected** | Class + Subclasses | Shared implementation for inheritance |
| `~` | **Package** | Same package only | Internal package-level access |

### 📊 ASCII Diagram: Access Modifier Visibility

```
┌─────────────────────────────────────────┐
│           VISIBILITY SCOPE              │
├─────────────────────────────────────────┤
│                                         │
│  + Public                               │
│    ├── Can be accessed from anywhere    │
│    ├── No restrictions                  │
│    └── Use for public interfaces        │
│                                         │
│  # Protected                            │
│    ├── Accessible in class + subclasses │
│    ├── Hidden from outside clients      │
│    └── Supports inheritance patterns    │
│                                         │
│  - Private                              │
│    ├── Only accessible within class     │
│    ├── Completely hidden from outside   │
│    └── Best for encapsulation           │
│                                         │
│  ~ Package                              │
│    ├── Only within same package         │
│    ├── Cross-package access blocked     │
│    └── Used for internal implementation │
│                                         │
└─────────────────────────────────────────┘
```

### Example: BankAccount Class

```
┌────────────────────────────────┐
│      BankAccount               │
├────────────────────────────────┤
│ Attributes:                    │
│ + accountNumber: String ──┐    │
│ # balance: Double ────────┼──┐ │
│ - PIN: Integer ───────────┼──┼─┤
│                           │  │ │
├────────────────────────────┤  │ │
│ Methods:                   │  │ │
│ + deposit(amount) ────────────┘ │
│ # calculateInterest() ─────────┘ │
│ - validatePIN(pin) ─────────────┘ │
│ + getBalance()                    │
└────────────────────────────────┘

Legend:
+ = Public (accessible everywhere)
# = Protected (for subclasses)
- = Private (internal only)
```

### 💡 Key Principles

| Principle | Description | Benefit |
|-----------|-------------|---------|
| **Encapsulation** | Hide implementation, expose interface | Security & flexibility |
| **Least Privilege** | Make members as private as possible | Reduced coupling |
| **Information Hiding** | Don't expose internal details | Easier maintenance |

---

## 🔗 Associations

Association represents a relationship between two classes where one class uses or interacts with another. It indicates that objects of one class are connected to objects of another class.

### 📊 Types of Associations

```
┌─────────────────────────────────────────────────────┐
│          ASSOCIATION TYPES                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Inheritance (IS-A)      ⬆️  Strong             │
│     └─ Child inherits from parent                  │
│                                                     │
│  2. Composition (HAS-A)     🔗 Strong              │
│     └─ Whole-Part (tightly bound)                  │
│                                                     │
│  3. Aggregation (HAS-A)     🔲 Weak                │
│     └─ Whole-Part (loosely bound)                  │
│                                                     │
│  4. Simple Association      ➡️  Medium             │
│     └─ Objects communicate/reference               │
│                                                     │
│  5. Dependency              ⟶ Weak                 │
│     └─ Temporary usage relationship                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### 1️⃣ Inheritance (Class Association / IS-A Relationship)

**Definition**: A child class inherits properties and methods from a parent class. It's an IS-A relationship.

**Notation**: Solid line with hollow arrowhead pointing to parent class

**When to Use**:
- Creating specialized versions of a general class
- Sharing common behavior among related classes
- Building class hierarchies

#### 📊 Inheritance Diagram: Multi-Level Hierarchy

```
                    ┌──────────────────┐
                    │     Vehicle      │
                    ├──────────────────┤
                    │ - speed: double  │
                    │ - color: String  │
                    ├──────────────────┤
                    │ + start()        │
                    │ + stop()         │
                    │ + drive()        │
                    └────────┬─────────┘
                             △
                ┌────────────┼────────────┐
                │            │            │
                │            │            │
         ┌──────┴────┐  ┌───┴─────┐  ┌──┴──────┐
         │   Car     │  │  Bike   │  │ Truck   │
         ├───────────┤  ├─────────┤  ├─────────┤
         │ - doors   │  │ -gears  │  │ -cargo  │
         ├───────────┤  ├─────────┤  ├─────────┤
         │ +honk()   │  │+shift() │  │+load()  │
         └───────────┘  └─────────┘  └─────────┘

Inheritance: Child extends Parent
Benefits:
✓ Code reuse
✓ Polymorphism
✓ Consistent interface
```

#### Example Code

```python
class Vehicle:
    def __init__(self, speed, color):
        self.speed = speed
        self.color = color
    
    def start(self):
        print("Starting engine...")
    
    def drive(self):
        print(f"Driving at {self.speed} km/h")

class Car(Vehicle):                    # Inherits from Vehicle
    def __init__(self, speed, color, doors):
        super().__init__(speed, color)
        self.doors = doors
    
    def honk(self):
        print("Beep! Beep!")

# Usage
car = Car(100, "red", 4)               # Car IS-A Vehicle
car.drive()                            # Inherits from parent
car.honk()                             # Own method
```

#### ⚠️ Common Mistakes

- ❌ Using inheritance when composition is better
- ❌ Creating deep hierarchies (more than 3 levels)
- ❌ Violating Liskov Substitution Principle
- ✅ Use inheritance for true IS-A relationships
- ✅ Prefer composition for HAS-A relationships

---

### 2️⃣ Simple Association (Object Association / HAS-A Relationship)

**Definition**: One object uses or references another object. It's the weakest connection between objects.

**Notation**: Simple line with or without arrowhead

**When to Use**:
- Objects communicate through references
- One object provides services to another
- Temporary or optional relationships

#### 📊 Simple Association Diagram

```
┌──────────────┐         ┌──────────────┐
│   Student    │────────▶│   Course     │
├──────────────┤         ├──────────────┤
│ - name       │ enrolls │ - courseId   │
│ - studentId  │  in     │ - title      │
├──────────────┤         ├──────────────┤
│ + getName()  │         │ + getName()  │
│ + enroll()   │         └──────────────┘
└──────────────┘

Navigation: One-way
Student knows about Course
Course doesn't know about Student
```

#### Example Code

```python
class Course:
    def __init__(self, course_id, title):
        self.course_id = course_id
        self.title = title
    
    def get_title(self):
        return self.title

class Student:
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id
        self.courses = []  # Reference to Course objects
    
    def enroll(self, course):
        self.courses.append(course)
    
    def get_courses(self):
        return [c.get_title() for c in self.courses]

# Usage
math_course = Course(101, "Mathematics")
student = Student("John", 1)
student.enroll(math_course)              # Association created
```

#### Characteristics

| Aspect | Description |
|--------|-------------|
| Strength | Weak - no dependency on lifecycle |
| Navigation | One or Two-way |
| Multiplicity | Can be one-to-one, one-to-many, many-to-many |
| Flexibility | Highly flexible, can be changed at runtime |

---

### 3️⃣ Composition (Strong IS-PART-OF Relationship)

**Definition**: A whole-part relationship where parts cannot exist independently. The container owns the parts.

**Notation**: Solid line with filled diamond on the container side

**When to Use**:
- Whole controls lifecycle of parts
- Parts have no meaning outside the whole
- Clear ownership and exclusive relationship

#### 📊 Composition Diagram: Chair Example

```
                    ┌──────────────┐
                    │    Chair     │ (Whole)
                    ├──────────────┤
                    │ - color      │
                    │ - legs ◊──┐  │
                    │ - seat  ◊─┼──┤
                    │ - arms  ◊─┘  │
                    └──────────────┘
                           ◊
                          /|\
                         / | \
                        /  |  \
        ┌──────────┐ ┌─────┴──┐ ┌──────────┐
        │   Leg    │ │  Seat  │ │   Arm    │
        │(Part)    │ │(Part)  │ │ (Part)   │
        └──────────┘ └────────┘ └──────────┘

Composition: Whole owns Parts
Multiplicity:
  Chair has 4 Legs
  Chair has 1 Seat
  Chair has 2 Arms

Lifecycle: If Chair is deleted, all parts are deleted
```

#### Example Code

```python
class Leg:
    def __init__(self, material):
        self.material = material

class Seat:
    def __init__(self, material):
        self.material = material

class Arm:
    def __init__(self, material):
        self.material = material

class Chair:
    def __init__(self, color):
        self.color = color
        # Composition: Chair OWNS these parts
        self.legs = [Leg("wood") for _ in range(4)]
        self.seat = Seat("fabric")
        self.arms = [Arm("wood") for _ in range(2)]
    
    def __del__(self):
        print("Chair deleted - all parts deleted with it")

# Usage
chair = Chair("red")
# When chair is deleted, all parts are automatically deleted
# Parts cannot exist without the chair
```

#### Key Characteristics

| Property | Details |
|----------|---------|
| **Ownership** | Container owns parts exclusively |
| **Lifecycle** | Parts die with container |
| **Multiplicity** | Fixed (usually 1:many or 1:1) |
| **Independence** | Parts cannot exist alone |
| **Strength** | Strongest relationship |

---

### 4️⃣ Aggregation (Weak HAS-A Relationship)

**Definition**: A whole-part relationship where parts can exist independently. The container only references the parts.

**Notation**: Line with unfilled (hollow) diamond on the container side

**When to Use**:
- Parts can exist independently
- Whole doesn't control lifecycle of parts
- Looser coupling than composition

#### 📊 Aggregation Diagram: University-Department Example

```
                    ┌─────────────────┐
                    │   University    │
                    ├─────────────────┤
                    │ - name          │
                    │ - departments ◇─┼───┐
                    │ - students    ◇─┼──┐│
                    └─────────────────┘  ││
                            ◇            ││
                           / \           ││
                          /   \          ││
                  ┌──────────────────┐ ┌─┴─────────────┐
                  │   Department     │ │    Student    │
                  ├──────────────────┤ ├───────────────┤
                  │ - name           │ │ - name        │
                  │ - faculty        │ │ - student_id  │
                  ├──────────────────┤ ├───────────────┤
                  │ + getName()      │ │ + getName()   │
                  └──────────────────┘ └───────────────┘

Aggregation: Whole references Parts (not owns)
Multiplicity:
  University HAS MANY Departments
  University HAS MANY Students

Lifecycle: If University is deleted, Departments/Students continue to exist
```

#### Example Code

```python
class Department:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name

class Student:
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id

class University:
    def __init__(self, name):
        self.name = name
        self.departments = []    # Aggregation: references, not owns
        self.students = []
    
    def add_department(self, department):
        self.departments.append(department)
    
    def add_student(self, student):
        self.students.append(student)

# Usage
dept = Department("Computer Science")
student = Student("Alice", 101)
university = University("MIT")
university.add_department(dept)
university.add_student(student)

# Even if university is deleted, department and student still exist
del university
print(dept.get_name())      # ✓ Still works!
print(student.name)         # ✓ Still works!
```

#### Composition vs Aggregation

| Aspect | Composition | Aggregation |
|--------|-------------|-------------|
| **Notation** | Filled diamond ◆ | Hollow diamond ◇ |
| **Ownership** | Container owns parts | Container references parts |
| **Lifecycle** | Parts die with container | Parts can outlive container |
| **Independence** | Parts cannot exist alone | Parts can exist independently |
| **Strength** | Strong | Weak |
| **Example** | Heart IS-PART-OF Body | Car HAS-A Engine (replaceable) |

---

## 🔄 Relationships

### Navigation Types

#### 📊 One-Way Association

```
┌─────────────┐        ┌─────────────┐
│   Driver    │───────▶│   Vehicle   │
├─────────────┤        ├─────────────┤
│ - name      │        │ - licensePlate│
├─────────────┤        ├─────────────┤
│ + drive()   │        │ + start()   │
└─────────────┘        └─────────────┘

Navigation: Only Driver knows about Vehicle
Arrow direction shows navigation direction
```

#### 📊 Two-Way Association (Bidirectional)

```
┌──────────────┐                ┌──────────────┐
│   Person     │◄───────────────▶│   Company    │
├──────────────┤   works for     ├──────────────┤
│ - name       │   employs       │ - name       │
│ - company ───┼────────────────-│ - employees  │
├──────────────┤                 ├──────────────┤
│ + getName()  │                 │ + getName()  │
└──────────────┘                 └──────────────┘

Navigation: Both know about each other
Person knows Company
Company knows all its Employees
```

#### Code Example: Two-Way Association

```python
class Company:
    def __init__(self, name):
        self.name = name
        self.employees = []

class Person:
    def __init__(self, name, company):
        self.name = name
        self.company = company              # Reference to Company
        self.company.employees.append(self) # Company knows Person

# Usage
company = Company("Google")
person = Person("John", company)
person2 = Person("Jane", company)

print(person.company.name)          # Person→Company ✓
print(len(company.employees))       # Company→Persons ✓
```

### Multiplicity

| Notation | Meaning | Example |
|----------|---------|---------|
| `1` | Exactly one | Each order has exactly 1 customer |
| `0..1` | Zero or one | Optional relationship |
| `*` or `0..*` | Zero or many | Order can have many items |
| `1..*` | One or many | Author has at least 1 book |
| `n` | Specific number | Deck has 52 cards |

#### 📊 Multiplicity Examples

```
┌─────────────┐ 1        * ┌──────────────┐
│   Customer  │────────────│    Order     │
└─────────────┘            └──────────────┘
  One customer can have many orders
  Each order belongs to one customer


┌──────────┐ 0..1    1..* ┌─────────────┐
│  Teacher │────────────────│  Student    │
└──────────┘               └─────────────┘
  A teacher may teach 1 to many students
  A student must have 1 to many teachers
```

---

## 🔀 Dependency

**Definition**: One class depends on another class for its implementation. The dependency exists when a class uses another class temporarily.

**Notation**: Dashed line with arrow pointing to the dependent class

**When to Use**:
- Temporary relationships
- A method receives an object as parameter
- Weak coupling is desired
- Usage is limited to specific operations

### 📊 Dependency Diagram

```
┌──────────────────┐        ┌─────────────┐
│RegistrationMgr  │- - - - ▶│  Student    │
├──────────────────┤ uses   ├─────────────┤
│ - students[]     │        │ - name      │
├──────────────────┤        ├─────────────┤
│+ register(s)     │        │ + getName() │
│+ unregister(s)   │        └─────────────┘
└──────────────────┘

Dependency: Dashed line
RegistrationMgr depends on Student
(usually as method parameter or temporary usage)
```

### Example Code

```python
from typing import List

class Student:
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id

class Course:
    def __init__(self, course_id, title):
        self.course_id = course_id
        self.title = title
        self.students: List[Student] = []

class RegistrationManager:
    def register_student(self, student: Student, course: Course):
        """
        Dependency: Uses Student object as parameter
        Temporary usage - doesn't own the Student
        """
        course.students.append(student)
        print(f"{student.name} registered in {course.title}")
    
    def generate_report(self, course: Course) -> str:
        """
        Another dependency usage
        """
        return f"Total students: {len(course.students)}"

# Usage
student = Student("Bob", 1)
course = Course(101, "Python")
manager = RegistrationManager()

# RegistrationManager depends on Student object
manager.register_student(student, course)
report = manager.generate_report(course)
```

### Dependency vs Association

| Aspect | Dependency | Association |
|--------|-----------|-------------|
| **Lifetime** | Temporary | Persistent |
| **Notation** | Dashed line | Solid line |
| **Coupling** | Weak | Strong |
| **Usage** | Method parameter | Object attribute |
| **Example** | sendEmail(person) | Student enrolled in Course |

---

## 🌍 Real-World Examples

### Example 1: E-Commerce System

```
┌────────────────────────────────────────────────────────┐
│                   E-COMMERCE SYSTEM                    │
└────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Customer   │
                    ├──────────────┤
                    │ - name       │
                    │ - email      │
                    │ - address ◇──┼─┐
                    └──────────────┘ │
                           △         │
                           │         │
                    ┌──────┴─────┐   │
                    │  Premium   │   │
                    │ Customer   │   │
                    └────────────┘   │
                                     │
        ┌────────────────────────────┤
        │                            │
        │                    ┌───────┴────────┐
        │                    │    Address     │
        │                    ├────────────────┤
        │                    │ - street       │
        │                    │ - city         │
        │                    │ - country      │
        │                    └────────────────┘
        │
        │ 1        *
    ┌───┴─────────────────────┐
    │        Order            │
    ├─────────────────────────┤
    │ - orderId               │◆─┐
    │ - items: List[Item]     │  │ Composition
    │ - totalPrice            │  │ Order OWNS items
    ├─────────────────────────┤  │
    │ + calculateTotal()      │  │
    └─────────────────────────┘  │
             △                    │
             │                    │
    ┌────────┴──────────┐        │
    │   Item            │        │
    ├───────────────────┤        │
    │ - itemId          │        │
    │ - quantity        │        │
    │ - product ────────┼────────┘
    │ - price           │
    ├───────────────────┤
    │ + getTotal()      │
    └───────────────────┘
             △
             │
        ┌────┴────┐
        │ Product │
        ├─────────┤
        │ - name  │
        │ - price │
        └─────────┘

Relationships:
✓ Customer IS-A Entity (Inheritance to Premium Customer)
✓ Customer HAS-A Address (Aggregation)
✓ Customer HAS-MANY Orders (Aggregation)
✓ Order OWNS Items (Composition)
✓ Item references Product (Association)
```

---

### Example 2: Library Management System

```
┌─────────────────────────────────────────────┐
│      LIBRARY MANAGEMENT SYSTEM              │
└─────────────────────────────────────────────┘

            ┌──────────────┐
            │   Library    │
            ├──────────────┤
            │ - name       │
            │ - address    │
            │ - books ◇────┼──────┐
            │ - members ◇──┼───┐  │
            └──────────────┘   │  │
                    △          │  │
                    │          │  │
             ┌──────┴──┐   ┌───┴──┴───────┐
             │ Member  │   │    Book      │
             ├─────────┤   ├──────────────┤
             │ - id    │   │ - isbn       │
             │ - name  │   │ - title      │
             │ - books │   │ - author ────┼──┐
             │   ◆─────┼─┐ │ - status     │  │
             └─────────┤ │ └──────────────┘  │
                       │ │                   │
         ┌─────────────┘ │        ┌──────────┘
         │               │        │
    ┌────┴────────┐ ┌────┴──────────┐
    │ BorrowRecord│ │    Author     │
    ├─────────────┤ ├───────────────┤
    │ - dateOut   │ │ - name        │
    │ - dueDate   │ │ - country     │
    │ - dateReturn│ │ - biography   │
    └─────────────┘ └───────────────┘

Relationships:
✓ Library HAS-MANY Books (Aggregation)
✓ Library HAS-MANY Members (Aggregation)
✓ Member BORROWS Books (Association)
✓ Member HAS-MANY BorrowRecords (Composition)
✓ Book written by Author (Association)
```

---

## 🎯 Interview Questions

### Basic Level

**Q1: What is the difference between association and aggregation?**

**Answer**:

| Aspect | Association | Aggregation |
|--------|-------------|-------------|
| **Relationship** | General relationship | Whole-Part relationship |
| **Strength** | Weaker | Slightly stronger |
| **Notation** | Simple line | Hollow diamond |
| **Lifecycle** | No specific binding | Parts can exist independently |
| **Example** | Student enrolls in Course | Library HAS Books |

**Key Point**: Aggregation is a special type of association with "HAS-A" semantics.

---

**Q2: When would you use inheritance vs composition?**

**Answer**:

**Use Inheritance (IS-A) when**:
- There's a true "is-a" relationship (Dog IS-A Animal)
- You want to share common behavior
- You need polymorphism
- The relationship is stable and fundamental

**Use Composition (HAS-A) when**:
- You want flexible object creation
- Relationships might change at runtime
- You want to avoid deep hierarchies
- Avoiding "Gorilla-Banana problem"

**Example**:
```python
# ✓ Good: Inheritance
class Animal:
    def eat(self):
        pass

class Dog(Animal):          # Dog IS-A Animal
    pass

# ✓ Better: Composition for flexibility
class Dog:
    def __init__(self):
        self.behavior = Behavior()  # Can change at runtime
    
    def eat(self):
        self.behavior.eat()
```

---

**Q3: Explain the difference between composition and aggregation with an example.**

**Answer**:

**Composition** (Strong relationship):
```
Car OWNS Engine
├─ If Car is destroyed → Engine is destroyed
├─ Parts cannot exist independently
└─ Solid diamond (◆) notation
```

**Aggregation** (Weak relationship):
```
Library HAS Books
├─ If Library is destroyed → Books still exist
├─ Parts can exist independently
└─ Hollow diamond (◇) notation
```

**Real-world analogy**:
- **Composition**: Body composed of organs (organs die if body dies)
- **Aggregation**: Team has players (players exist even if team dissolves)

---

### Intermediate Level

**Q4: What is the difference between dependency and association?**

**Answer**:

| Aspect | Dependency | Association |
|--------|-----------|-------------|
| **Strength** | Very Weak | Stronger |
| **Notation** | Dashed line | Solid line |
| **Lifetime** | Temporary | Persistent |
| **Usage** | Method parameter | Object attribute |
| **Coupling** | Loose | Tight |
| **Example** | sendEmail(user) | user.address |

**Code Example**:
```python
# Dependency: Temporary usage
def send_notification(user: User, msg: Message):  # Parameter
    print(f"Sending to {user.name}")

# Association: Persistent relationship
class User:
    def __init__(self):
        self.email = Email()  # Persistent attribute
```

---

**Q5: How would you model a library management system with class diagrams?**

**Answer**:

```
                    ┌──────────────┐
                    │   Library    │
                    ├──────────────┤
                    │ - name       │
                    │ - books ◇────┼───┐
                    │ - members ◇──┤   │
                    └──────────────┘   │
                           △           │
                    ┌──────┴──────┐    │
                    │Member       │    │
                    ├─────────────┤    │
                    │ - name      │    │
                    │ - memberId  │    │
                    │ - borrowed◆─┼──┐ │
                    └─────────────┘  │ │
                                     │ │
        ┌────────────────────────────┼─┘
        │                            │
        │               ┌────────────┴──┐
        │               │     Book      │
        │               ├───────────────┤
        │               │ - isbn        │
        │               │ - title       │
        │               │ - author ───┐ │
        │               ├───────────────┤
        │               │ + getDetails()│
        │               └───────────────┘
        │                        △
        │                        │
        └──────────────┬─────────┘
                       │
         ┌─────────────┴──────────┐
         │      Author            │
         ├────────────────────────┤
         │ - name                 │
         │ - country              │
         └────────────────────────┘

Relationships:
✓ Library HAS-MANY Books (Aggregation) - Books exist independently
✓ Library HAS-MANY Members (Aggregation) - Members exist independently
✓ Member BORROWED Books (Association with multiplicity)
✓ Book written by Author (Association)
```

---

**Q6: Explain the Liskov Substitution Principle with inheritance example.**

**Answer**:

**LSP**: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application.

**✓ Good Example**:
```python
class Bird:
    def fly(self):
        return "Flying"

class Eagle(Bird):
    def fly(self):
        return "Soaring high"

class Sparrow(Bird):
    def fly(self):
        return "Flying fast"

# Can substitute any Bird with its subclass
birds: List[Bird] = [Eagle(), Sparrow()]
for bird in birds:
    print(bird.fly())  # Works correctly
```

**❌ Bad Example**:
```python
class Bird:
    def fly(self):
        return "Flying"

class Penguin(Bird):
    def fly(self):
        raise Exception("Penguins can't fly!")  # Violates LSP!

# This breaks the contract
penguin: Bird = Penguin()
penguin.fly()  # Unexpected error
```

**Solution**:
```python
class Bird:
    pass

class FlyingBird(Bird):
    def fly(self):
        pass

class SwimmingBird(Bird):
    def swim(self):
        pass

class Penguin(SwimmingBird):  # Correct inheritance
    def swim(self):
        return "Swimming"
```

---

### Advanced Level

**Q7: Design a class diagram for a ride-sharing application (like Uber).**

**Answer**:

```
┌─────────────────────────────────────────────────────────────────┐
│              RIDE-SHARING APPLICATION                           │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │      User        │
                    ├──────────────────┤
                    │ - userId         │
                    │ - name           │
                    │ - phone          │
                    │ - ratings        │
                    │ - location ◇─────┼──┐
                    └────────┬─────────┘  │
                             △            │
        ┌────────────────────┼────────────┤
        │                    │            │
        │            ┌───────┴───┐   ┌───┴──────┐
        │            │ Passenger │   │  Driver  │
        │            │           │   ├──────────┤
        │            └───────────┘   │ - vehicle│
        │                            │ -license │
        │                            └────┬─────┘
        │                                 │
        │                        ┌────────┴──────┐
        │                        │    Vehicle    │
        │                        ├───────────────┤
        │                        │ - licensePlate│
        │                        │ - model       │
        │                        │ - capacity    │
        │                        └───────────────┘
        │
        │ 1        *
    ┌───┴──────────────────────┐
    │        Ride              │
    ├──────────────────────────┤
    │ - rideId                 │
    │ - pickupLocation ◇───┐   │
    │ - dropoffLocation ◇──┼─┐ │
    │ - startTime          │ │ │
    │ - endTime            │ │ │
    │ - fare               │ │ │
    │ - status             │ │ │
    │ - driver ────────────┼─┘ │
    │ - passenger ─────────┘   │
    ├──────────────────────────┤
    │ + calculateFare()        │
    │ + updateStatus()         │
    └──────────────────────────┘

Relationships:
✓ Passenger/Driver IS-A User (Inheritance)
✓ Driver HAS-A Vehicle (Composition) - Driver must have vehicle
✓ Ride HAS-MANY Locations (Composition)
✓ Ride references Driver & Passenger (Association)
✓ Ride tracks pickupLocation & dropoffLocation (Dependency)
```

**Q8: What are the advantages and disadvantages of deep inheritance hierarchies?**

**Answer**:

**Disadvantages of Deep Hierarchies**:
- ❌ Hard to understand and maintain
- ❌ Fragile base class problem
- ❌ Difficult to add new variations
- ❌ Risk of misusing inherited methods
- ❌ Violates Single Responsibility Principle

**Advantages**:
- ✓ Code reuse at multiple levels
- ✓ Clear hierarchical organization (sometimes)
- ✓ Enforces consistency

**Best Practice**:
```
Keep hierarchies shallow (max 3 levels)
Level 0: Base class (Animal)
Level 1: Intermediate (Mammal)
Level 2: Concrete (Dog) ← Stop here!
```

**Better Approach - Composition**:
```python
# Instead of: Dog -> Animal -> LivingBeing -> ...
# Use composition:

class Dog:
    def __init__(self):
        self.behavior = AnimalBehavior()
        self.movement = FourLeggedMovement()
        self.diet = CarnivoreeDiet()
```

---

## 📝 Summary Table

| Concept | Symbol | Strength | When to Use |
|---------|--------|----------|-----------|
| **Inheritance** | △ | Strong | IS-A relationship |
| **Composition** | ◆ | Strong | Whole owns parts |
| **Aggregation** | ◇ | Weak | Whole references parts |
| **Association** | → | Medium | Objects interact |
| **Dependency** | - - -► | Weak | Temporary usage |

---

## 🚀 Quick Decision Tree

```
Do classes have an IS-A relationship?
├─ YES → Use Inheritance (△)
└─ NO → Continue to next question

Does one class own/create the other?
├─ YES → Use Composition (◆)
└─ NO → Continue to next question

Can parts exist without the whole?
├─ YES → Use Aggregation (◇)
└─ NO → Use Association (→)

Is the relationship temporary/parameter-based?
├─ YES → Use Dependency (- - -►)
└─ NO → Use Association (→)
```

---

## 📚 References & Further Reading

- UML Specification by OMG
- "Design Patterns" by Gang of Four
- "Head First Design Patterns"
- "Refactoring" by Martin Fowler
- "Clean Architecture" by Robert C. Martin
- "Object-Oriented Design in Java" by Stephen Cole
