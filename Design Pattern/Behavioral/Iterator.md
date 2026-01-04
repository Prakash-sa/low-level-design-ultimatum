# Iterator Pattern

> Provide a way to access elements of an aggregate object sequentially without exposing its underlying representation.

---

## Problem

You have a collection (array, linked list, tree) and need to iterate through it without exposing its internal structure or allowing multiple simultaneous iterations.

## Solution

The Iterator pattern abstracts iteration logic into a separate object that knows how to traverse the collection.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

T = TypeVar('T')

# Iterator interface
class Iterator(ABC, Generic[T]):
    @abstractmethod
    def has_next(self) -> bool:
        pass
    
    @abstractmethod
    def next(self) -> T:
        pass

# Iterable interface
class Iterable(ABC, Generic[T]):
    @abstractmethod
    def create_iterator(self) -> Iterator[T]:
        pass

# Linked List Node
class ListNode:
    def __init__(self, val: int):
        self.val = val
        self.next = None

# Linked List Collection
class LinkedList(Iterable[int]):
    def __init__(self, head: ListNode = None):
        self.head = head
    
    def create_iterator(self) -> Iterator[int]:
        return LinkedListIterator(self.head)
    
    def add(self, val: int):
        if not self.head:
            self.head = ListNode(val)
        else:
            node = self.head
            while node.next:
                node = node.next
            node.next = ListNode(val)

# Concrete Iterator
class LinkedListIterator(Iterator[int]):
    def __init__(self, head: ListNode):
        self.current = head
    
    def has_next(self) -> bool:
        return self.current is not None
    
    def next(self) -> int:
        if not self.has_next():
            raise StopIteration()
        val = self.current.val
        self.current = self.current.next
        return val

# Python magic methods for iteration
class LinkedListMagic(Iterable[int]):
    def __init__(self, head: ListNode = None):
        self.head = head
    
    def __iter__(self):
        self.current = self.head
        return self
    
    def __next__(self) -> int:
        if self.current is None:
            raise StopIteration()
        val = self.current.val
        self.current = self.current.next
        return val

# Demo
if __name__ == "__main__":
    # Using explicit iterator
    head = ListNode(1)
    head.next = ListNode(2)
    head.next.next = ListNode(3)
    
    linked_list = LinkedList(head)
    iterator = linked_list.create_iterator()
    
    print("Explicit iteration:")
    while iterator.has_next():
        print(iterator.next(), end=" ")
    print()
    
    # Using Python's for loop
    linked_list_magic = LinkedListMagic(head)
    print("Python for loop:")
    for val in linked_list_magic:
        print(val, end=" ")
    print()
    
    # Multiple simultaneous iterators
    iter1 = linked_list.create_iterator()
    iter2 = linked_list.create_iterator()
    
    print("Two iterators:")
    print(f"Iter1: {iter1.next()}, Iter2: {iter2.next()}")
    print(f"Iter1: {iter1.next()}, Iter2: {iter2.next()}")
```

---

## Key Concepts

- **Iterator**: Manages current position and provides `has_next()`, `next()`
- **Iterable**: Creates iterators for traversal
- **Aggregate**: The collection being iterated
- **Decoupling**: Client doesn't know about collection's internal structure

---

## When to Use

✅ Need to traverse collections without exposing structure  
✅ Support multiple simultaneous iterations  
✅ Provide uniform interface for different collection types  
✅ Hide complexity of traversal logic  

---

## Interview Q&A

**Q1: What's the difference between Iterator and Iterable?**

A:
- **Iterable**: An object that CAN be iterated over (has `__iter__()` in Python)
- **Iterator**: The object that PERFORMS iteration (has `__iter__()` and `__next__()`)

```python
# Iterable
class MyList:
    def __iter__(self):  # Returns an iterator
        return MyIterator(...)

# Iterator
class MyIterator:
    def __iter__(self):  # Returns self
        return self
    
    def __next__(self):  # Returns next value
        ...
```

---

**Q2: Can you have multiple iterators on the same collection simultaneously?**

A: Yes. Each iterator maintains its own position:

```python
collection = LinkedList(head)
iter1 = collection.create_iterator()
iter2 = collection.create_iterator()

# They can advance independently
print(iter1.next())  # 1
print(iter1.next())  # 2
print(iter2.next())  # 1 (iter2 is still at start)
```

---

**Q3: How would you implement a reverse iterator?**

A:
```python
class ReverseIterator(Iterator[int]):
    def __init__(self, head: ListNode):
        self.values = []
        node = head
        while node:
            self.values.append(node.val)
            node = node.next
        self.index = len(self.values) - 1
    
    def has_next(self) -> bool:
        return self.index >= 0
    
    def next(self) -> int:
        if not self.has_next():
            raise StopIteration()
        val = self.values[self.index]
        self.index -= 1
        return val
```

---

**Q4: How do you handle modification during iteration?**

A: Use a **fail-fast** approach with version numbers:

```python
class LinkedList:
    def __init__(self):
        self.head = None
        self.version = 0
    
    def add(self, val: int):
        # ... add logic ...
        self.version += 1
    
    def create_iterator(self) -> Iterator:
        return LinkedListIterator(self.head, self.version)

class LinkedListIterator:
    def __init__(self, head, version):
        self.current = head
        self.initial_version = version
        self.list_version = version  # Reference to list's version
    
    def next(self) -> int:
        if self.list_version != self.initial_version:
            raise RuntimeError("Collection modified during iteration")
        # ... return next value ...
```

---

**Q5: How would you implement a filtered iterator?**

A:
```python
class FilteredIterator(Iterator[int]):
    def __init__(self, base_iter: Iterator[int], predicate):
        self.base_iter = base_iter
        self.predicate = predicate
        self.next_val = None
        self.advance()
    
    def advance(self):
        while self.base_iter.has_next():
            val = self.base_iter.next()
            if self.predicate(val):
                self.next_val = val
                return
        self.next_val = None
    
    def has_next(self) -> bool:
        return self.next_val is not None
    
    def next(self) -> int:
        val = self.next_val
        self.advance()
        return val

# Usage
filtered = FilteredIterator(
    linked_list.create_iterator(),
    lambda x: x > 5  # Only values > 5
)
```

---

## Trade-offs

✅ **Pros**: Decouples iteration from collection, supports multiple iterators, clean interface  
❌ **Cons**: Extra objects, potential performance overhead for simple arrays

---

## Real-World Examples

- **Python's `iter()` and `next()`** built-ins
- **Java's `Iterator` interface**
- **Database cursors** (iterate through query results)
- **File readers** (iterate through lines)
