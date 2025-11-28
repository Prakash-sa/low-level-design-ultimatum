# Stack Overflow - 75 Minute Interview Implementation Guide

## System Overview
Q&A platform with questions, answers, voting, reputation, and tagging system

## Core Requirements
- Ask questions
- Provide answers
- Voting system
- Reputation system
- Tags
- Search functionality
- User profiles
- Accept answer

## Core Entities
- Question
- Answer
- User
- Tag
- Vote

---

## 75-Minute Implementation Timeline

### Phase 0: Requirements Clarification (0-5 minutes)
**Goal**: Understand the problem and define scope

**Discuss**:
- Functional requirements
- Non-functional requirements
- Core entities and relationships
- Scale and constraints

**Expected Output**: Clear understanding of what to build

---

### Phase 1: Architecture & Design (5-15 minutes)
**Goal**: Design system architecture

**What to cover**:
- Singleton pattern for system instance
- Entity relationships
- Key design patterns to implement
- Basic class hierarchy

**Code Skeleton**:
```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

# Enumerations
class Status(Enum):
    ACTIVE = 1
    INACTIVE = 2
    COMPLETED = 3

# Base Classes
class Entity:
    def __init__(self):
        self.id = None
        self.created_at = datetime.now()
```

**Expected Output**: Architecture diagram on whiteboard + pseudocode

---

### Phase 2: Core Entities (15-35 minutes)
**Goal**: Implement core entity classes

**What to implement**:
- All entity classes from requirements
- Basic attributes and methods
- Inheritance hierarchy
- Enumerations

**Code Structure** (~100-150 lines):
```python
class Entity1:
    def __init__(self, id):
        self.id = id
        # attributes...
    
    def method1(self):
        # implementation
        pass

class Entity2:
    def __init__(self, id):
        self.id = id
        # attributes...
```

**Line Count**: 0 → ~150 lines

---

### Phase 3: Business Logic & Patterns (35-55 minutes)
**Goal**: Implement core business logic

**What to implement**:
- Strategy pattern for flexible behaviors
- Factory pattern for object creation
- Observer pattern for notifications
- State management
- Calculation logic

**Code Structure** (~100-150 lines):
```python
class StrategyInterface:
    @abstractmethod
    def execute(self):
        pass

class ConcreteStrategy1(StrategyInterface):
    def execute(self):
        # implementation
        pass

class SystemController:
    def __init__(self):
        self.strategy = ConcreteStrategy1()
    
    def process(self):
        self.strategy.execute()
```

**Line Count**: ~150 → ~300 lines

---

### Phase 4: System Integration (55-70 minutes)
**Goal**: Integrate all components into main system

**What to implement**:
- Main system/controller class
- Singleton pattern implementation
- Integration of all components
- Error handling

**Code Structure** (~100-150 lines):
```python
class System:
    _instance = None
    
    def __init__(self):
        self.entities = []
        self.observers = []
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = System()
        return cls._instance
    
    def add_entity(self, entity):
        self.entities.append(entity)
        self.notify_observers()
    
    def notify_observers(self):
        for observer in self.observers:
            observer.update()
```

**Line Count**: ~300 → ~450 lines

---

### Phase 5: Demo & Testing (70-75 minutes)
**Goal**: Show working implementation with demo scenarios

**Demo Scenarios** (~50-100 lines):
1. Basic operation flow
2. Pattern in action
3. Error handling
4. Edge case handling
5. Statistics/summary

**Example**:
```python
def demo_1_basic():
    system = System.get_instance()
    # Demo scenario 1
    print("Demo 1: Basic operation")

def demo_2_pattern():
    system = System.get_instance()
    # Demo scenario 2
    print("Demo 2: Pattern demonstration")

if __name__ == "__main__":
    demo_1_basic()
    demo_2_pattern()
```

---

## Key Points to Remember

### Design Patterns
- **Singleton**: Ensure only one instance of system
- **Strategy**: Different algorithms for same operation
- **Observer**: Notify multiple listeners of changes
- **Factory**: Encapsulate object creation
- **State**: Represent state transitions

### SOLID Principles
- **Single Responsibility**: Each class one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable
- **Interface Segregation**: Depend on specific interfaces
- **Dependency Inversion**: Depend on abstractions

### Common Pitfalls
- ❌ Not using Singleton - leads to multiple instances
- ❌ Tight coupling - hard to extend
- ❌ Not using abstractions - not flexible
- ❌ No error handling - crashes on edge cases
- ✅ Always use design patterns
- ✅ Keep classes focused
- ✅ Use abstractions and interfaces

## Interview Tips

1. **Talk through your design** - Explain patterns as you implement
2. **Ask clarifying questions** - "Should we support...?"
3. **Handle edge cases** - Show you think about errors
4. **Optimize incrementally** - Start simple, then optimize
5. **Use design patterns** - Shows you know when to apply them
6. **Write clean code** - Good naming and structure
7. **Test as you go** - Run demos after each phase
8. **Discuss trade-offs** - Why you chose this approach

## Success Criteria

✅ All core entities implemented
✅ Design patterns clearly used
✅ At least 3 demo scenarios work
✅ Code is clean and readable
✅ Error handling present
✅ Can explain design decisions
✅ SOLID principles applied
✅ 75 minutes used efficiently
