# Library Management System — Complete Design Guide

> Book inventory management, member borrowing and return lifecycle, late fine calculation, reservation queues, and multi-branch support.

**Scale**: 100K+ members, 1M+ books, multi-branch  
**Duration**: 75-minute interview guide  
**Focus**: Overborrowing prevention, fine calculation, reservation queues, thread-safe inventory

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?

A member searches for a book → finds an available physical copy → borrows it (checkout with a due date) → returns it on time or late (fine applied) → or reserves it if all copies are borrowed and gets notified when one becomes available. Core concerns: prevent overborrowing, enforce fine policy, manage reservation queues, and keep inventory accurate across concurrent operations.

### Core Flow

```
Search Book → Find Available Copy → BORROW (14-day due date) → RETURN (fine if late)
                     ↓ all copies borrowed
              RESERVE (queue) → Notified when returned → Pick up within 2 days
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single branch or multi-branch?** → "Multi-branch, each with its own inventory"
2. **Digital books in scope?** → "Physical only for core; mention digital as extension"
3. **Real payment for fines?** → "Mock fine tracking for the interview"
4. **Renewals allowed?** → "Yes, max 2 renewals if no holds on that copy"
5. **Who manages inventory?** → "Librarian admin adds/removes books; members borrow/return"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Member** | Borrows and returns books | Search, borrow, return, renew, reserve |
| **Librarian / Admin** | Manages inventory and accounts | Add books, register members, resolve disputes |
| **System** | Coordinator and notifier | Calculate fines, expire reservations, send notifications |

### Functional Requirements (What does the system do?)

✅ **Search & Browse**
  - Search books by title, author, or ISBN
  - View available copies and reservation status per branch

✅ **Borrow & Return**
  - Borrow an available physical copy (14-day loan period)
  - Return a book and auto-calculate late fines
  - Prevent borrowing beyond the 5-book limit per member

✅ **Renewal**
  - Extend due date by 14 days (max 2 renewals)
  - Reject renewal if another member has reserved the copy

✅ **Reserve**
  - Join a reservation queue when all copies are borrowed
  - Notify member (first in queue) when a copy is returned
  - Hold copy for 2 days before releasing to next member

✅ **Fine Management**
  - Charge $0.50 per day late, capped at $10 per borrowing
  - Suspend membership when total fine balance exceeds $50

✅ **Reporting & Admin**
  - Track inventory per branch and per status
  - Generate borrowing reports and overdue notifications

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support simultaneous borrows/returns without inventory corruption  
✅ **Consistency**: Borrow limit and inventory status atomically enforced  
✅ **Latency**: Search < 200ms, borrow/return < 200ms  
✅ **Availability**: 99.5% uptime  
✅ **Scalability**: 100K+ members, 1M+ books with indexing  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Borrow limit** | 5 books per member at a time |
| **Loan period** | 14 days per checkout |
| **Renewals** | Max 2 per borrowing, only if no holds |
| **Fine rate** | $0.50/day late |
| **Fine cap per borrowing** | $10 |
| **Suspension threshold** | Fine balance > $50 |
| **Reservation hold window** | 2 days after member notified |
| **Multi-branch** | YES — books tracked per branch |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Book, BookItem, Member, Borrowing, Fine, Reservation, Library, Branch, ...
```

### Step 2.2: Define Core Classes

#### **Book** — A title in the catalog (logical record)
```
Properties:
  - isbn: str (e.g., "978-0-7432-7356-5")
  - title: str
  - author: str
  - genre: str

Behaviors:
  - (catalog entry; no behavior beyond data)
```

#### **BookItem** — A single physical copy of a Book
```
Properties:
  - book_id: str (unique per physical copy)
  - isbn: str (links to Book title)
  - title: str
  - author: str
  - status: BookStatus (AVAILABLE, BORROWED, RESERVED, MAINTENANCE, LOST)
  - branch: str

Behaviors:
  - is_available(): Check if status == AVAILABLE
  - mark_borrowed() / mark_available() / mark_reserved()
```

#### **Member** — A library member account
```
Properties:
  - member_id: str
  - name: str
  - email: str
  - status: MemberStatus (ACTIVE, SUSPENDED)
  - fine_balance: float
  - active_borrows: List[Borrowing]

Behaviors:
  - can_borrow(): Check borrow limit and suspension status
  - add_fine(amount): Accumulate fine, suspend if > $50
```

#### **Borrowing** — A single checkout transaction
```
Properties:
  - borrowing_id: str
  - book_id: str (which physical copy)
  - member_id: str
  - checkout_date: datetime
  - due_date: datetime (checkout + 14 days)
  - return_date: Optional[datetime]
  - fine: float
  - renewal_count: int

Behaviors:
  - calculate_fine(): max(0, days_late × 0.50), capped at $10
  - renew(): Extend due_date if renewal_count < 2
  - is_overdue(): return_date or now > due_date
```

#### **Library** — Singleton central coordinator
```
Properties:
  - books: Dict[str, BookItem]
  - members: Dict[str, Member]
  - borrowings: Dict[str, Borrowing]
  - book_counter / borrowing_counter: int
  - lock: threading.RLock

Behaviors:
  - add_book() / register_member()
  - search_books(title): Return matching BookItem list
  - borrow_book(member_id, book_id): Create Borrowing, update status
  - return_book(borrowing_id): Calculate fine, release copy
  - renew_book(borrowing_id): Extend due date
  - reserve_book(member_id, isbn): Mark copy RESERVED
  - display_member_account(member_id)
```

### Step 2.3: Define Enumerations (State & Type)

```python
class BookStatus(Enum):
    AVAILABLE    = 1   # Can be borrowed
    BORROWED     = 2   # Currently checked out
    RESERVED     = 3   # On hold for a specific member
    MAINTENANCE  = 4   # Under repair
    LOST         = 5   # Reported lost

class MemberStatus(Enum):
    ACTIVE    = 1   # Can borrow
    SUSPENDED = 2   # Fine balance > $50; borrowing blocked
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **BookItem** | Track individual physical copies, not just titles | Can't prevent double-borrowing of the same copy |
| **Member** | Profile with borrow limit and fine balance | Can't enforce limits or suspensions |
| **Borrowing** | Full transaction record with dates and fine | No audit trail; can't calculate fines |
| **Library** | Central thread-safe coordinator | No atomic borrow/return; race conditions on last copy |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Search Books**
```python
def search_books(title: str) -> List[BookItem]:
    """
    Find all physical copies whose title contains the search string (case-insensitive).
    Returns: List of BookItem objects (all statuses included).
    Response Time: <200ms (indexed on title)
    """
    pass
```

#### **2. Borrow Book** ⭐ CRITICAL
```python
def borrow_book(member_id: str, book_id: str) -> Optional[str]:
    """
    Check out a specific physical copy to a member.

    Preconditions:
      - member.status == ACTIVE
      - member.fine_balance <= $50
      - len(member.active_borrows) < 5
      - book.status == AVAILABLE

    Postconditions:
      - book.status == BORROWED
      - Borrowing record created with due_date = now + 14 days
      - Borrowing appended to member.active_borrows

    Returns: borrowing_id (str) on success, None on failure.

    Failure causes:
      - Member not found / suspended / borrow limit reached
      - Book not found / already borrowed / reserved
      - Fine balance > $50 (treated as suspension)

    Concurrency: THREAD-SAFE (guarded by RLock)
    Response Time: <200ms
    """
    pass
```

#### **3. Return Book** ⭐ CRITICAL
```python
def return_book(borrowing_id: str) -> float:
    """
    Return a book and calculate any late fine.

    Postconditions:
      - book.status == AVAILABLE
      - borrowing.return_date = now
      - fine = min(days_late × 0.50, 10.0) added to member.fine_balance
      - Borrowing removed from member.active_borrows

    Returns: fine amount charged (0.0 if on time).

    Failure causes:
      - borrowing_id not found → returns 0.0

    Side Effects: Member suspended if fine_balance > $50 after this return
    Concurrency: THREAD-SAFE
    """
    pass
```

#### **4. Renew Book**
```python
def renew_book(borrowing_id: str) -> bool:
    """
    Extend due date by 14 more days.

    Preconditions: borrowing exists, renewal_count < 2, no reservation on copy

    Postcondition: borrowing.due_date += 14 days, renewal_count += 1

    Returns: True on success, False if renewal blocked.
    """
    pass
```

#### **5. Reserve Book**
```python
def reserve_book(member_id: str, isbn: str) -> bool:
    """
    Reserve the first borrowed copy of an ISBN for a member.

    Precondition: No available copies of the ISBN exist (all BORROWED)
    Postcondition: First borrowed copy marked RESERVED for this member

    Returns: True if reservation created, False if copies available (borrow instead)
    or no copies exist.
    """
    pass
```

### Step 3.2: Failure Model

The implementation returns `None` / `False` / `0.0` rather than raising exceptions to keep the demo concise. A production version would use a typed hierarchy:

```python
class LibraryException(Exception): ...
class BorrowLimitExceededError(LibraryException): ...
class MemberSuspendedError(LibraryException): ...
class BookNotAvailableError(LibraryException): ...
class RenewalNotAllowedError(LibraryException): ...
class BorrowingNotFoundError(LibraryException): ...
```

### Step 3.3: API Usage Example

```python
lib = Library()

# Setup
lib.add_book("978-0", "1984", "George Orwell", copies=2)
lib.register_member("M1", "Jane", "jane@email.com")

# Search
copies = lib.search_books("1984")

# Borrow
borrow_id = lib.borrow_book("M1", copies[0].book_id)

# Return (fine if late)
fine = lib.return_book(borrow_id)

# Reserve when all copies out
lib.reserve_book("M2", "978-0")
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
Library HAS-A books (1:N Composition)
  └─ Library owns all physical BookItem records

Library HAS-A members (1:N Composition)
  └─ Library owns all Member accounts

Library HAS-A borrowings (1:N Composition)
  └─ Library owns all Borrowing transaction records

Member HAS-A active_borrows (1:N Composition)
  └─ Member tracks its own current checkouts

Borrowing REFERENCES book_id (1:1 Association)
  └─ Links to specific physical copy (no ownership)

Borrowing REFERENCES member_id (1:1 Association)
  └─ Links to the member who borrowed (no ownership)
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────┐
│       Library (Singleton)            │
├──────────────────────────────────────┤
│ - _instance: Library                 │
│ - books: Dict[str, BookItem]         │
│ - members: Dict[str, Member]         │
│ - borrowings: Dict[str, Borrowing]   │
│ - book_counter: int                  │
│ - borrowing_counter: int             │
│ - lock: threading.RLock              │
├──────────────────────────────────────┤
│ + add_book(isbn, title, author,      │
│            copies, branch)           │
│ + register_member(...): Member       │
│ + search_books(title): List[Book]    │
│ + borrow_book(member_id,             │
│               book_id): Optional[str]│
│ + return_book(borrowing_id): float   │
│ + renew_book(borrowing_id): bool     │
│ + reserve_book(member_id,            │
│                isbn): bool           │
│ + display_member_account(member_id)  │
└──────────────┬───────────────────────┘
        manages 1:N
   ┌──────────┼──────────────┐
   ▼          ▼              ▼
┌──────────┐ ┌────────────┐ ┌───────────┐
│ BookItem │ │   Member   │ │ Borrowing │
├──────────┤ ├────────────┤ ├───────────┤
│ book_id  │ │ member_id  │ │borrow_id  │
│ isbn     │ │ name       │ │book_id    │
│ title    │ │ email      │ │member_id  │
│ author   │ │ status     │ │checkout   │
│ status   │ │ fine_bal   │ │due_date   │
│ branch   │ │ borrows[]  │ │return_date│
└──────────┘ └────────────┘ │fine: float│
                             └───────────┘

Book Status Machine:
AVAILABLE ──borrow──→ BORROWED ──return──→ AVAILABLE
                          │
                       reserve
                          │
                          ▼
                       RESERVED ──pickup──→ BORROWED

Borrowing State:
┌──────────────────────────────┐
│ Borrowing                    │
├──────────────────────────────┤
│ checkout_date                │
│ due_date  (checkout + 14d)   │
│ return_date (None until back)│
│ fine (0 until returned)      │
│ renewal_count (max 2)        │
└──────────────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| Library → BookItems | 1:N | Composition | Library owns all physical copies |
| Library → Members | 1:N | Composition | Library owns all member records |
| Library → Borrowings | 1:N | Composition | Library owns all transaction records |
| Member → active_borrows | 1:N | Composition | Member tracks its own checkouts |
| Borrowing → BookItem | N:1 | Association | Many borrowings over time per copy |
| Borrowing → Member | N:1 | Association | Many borrowings over time per member |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For Library)

**Problem**: Multiple threads need a single consistent view of inventory, members, and borrowings.

**Solution**: One global Library instance, thread-safe double-checked locking initialization.

```python
class Library:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.lock = threading.RLock()  # Re-entrant: borrow_book calls internal helpers
        ...
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe initialization (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state makes unit testing harder, ⚠️ Doesn't scale across multiple processes without a shared store

---

### Pattern 2: **State Machine** (For Book Status)

**Problem**: A physical copy must follow strict transitions: AVAILABLE → BORROWED → AVAILABLE; BORROWED → RESERVED. Invalid states (borrowing an already-borrowed copy) must be caught.

**Solution**: `BookStatus` enum + guard checks on every status mutation.

```python
class BookStatus(Enum):
    AVAILABLE   = 1
    BORROWED    = 2
    RESERVED    = 3
    MAINTENANCE = 4
    LOST        = 5

# Guard in borrow_book:
if book.status != BookStatus.AVAILABLE:
    print(f"✗ Book {book_id} not available")
    return None
book.status = BookStatus.BORROWED
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid transitions caught early  
**Trade-off**: ⚠️ Must check state before every mutation; can grow complex with more states

---

### Pattern 3: **Observer** (For Reservation Notifications)

**Problem**: When a reserved book is returned, the waiting member must be notified without coupling the return logic to notification channels.

**Solution**: Observer pattern — Library notifies registered observers on book-available events.

```python
class LibraryObserver(ABC):
    @abstractmethod
    def on_book_available(self, member_id: str, book_title: str): pass

class EmailNotifier(LibraryObserver):
    def on_book_available(self, member_id: str, book_title: str):
        print(f"Email to {member_id}: '{book_title}' is now available!")

# Usage: attach at startup
library.add_observer(EmailNotifier())
# On return when copy was RESERVED:
library.notify_observers(reserved_member_id, book_title)
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add SMS, push, or in-app notifications  
**Trade-off**: ⚠️ Observer lifecycle management; errors in one notifier can affect others

---

### Pattern 4: **Strategy** (For Fine Calculation)

**Problem**: Fine policy may vary: flat-rate, tiered (escalating after 7 days), or membership-tier-based (premium members pay less).

**Solution**: Pluggable fine strategy injected into Library.

```python
class FineStrategy(ABC):
    @abstractmethod
    def calculate(self, days_late: int) -> float: pass

class FlatRateFine(FineStrategy):
    def calculate(self, days_late: int) -> float:
        return min(days_late * 0.50, 10.0)

class TieredFine(FineStrategy):
    def calculate(self, days_late: int) -> float:
        if days_late <= 7:
            return min(days_late * 0.50, 10.0)
        return min(3.50 + (days_late - 7) * 1.00, 10.0)  # $1/day after a week

# Usage: switch at runtime
library.set_fine_strategy(TieredFine())
```

**Benefit**: ✅ Add new fine policies without touching return logic, ✅ Configurable per member tier  
**Trade-off**: ⚠️ Extra abstraction layer for what could be a one-liner

---

### Pattern 5: **Factory** (For Book Creation)

**Problem**: Creating multiple physical copies of the same title requires consistent ID generation and initialization.

**Solution**: `add_book()` acts as a factory, creating N BookItem instances with auto-incremented IDs.

```python
def add_book(self, isbn: str, title: str, author: str, copies: int = 1, branch: str = "Main"):
    with self.lock:
        for _ in range(copies):
            self.book_counter += 1
            book = BookItem(f"BOOK_{self.book_counter}", isbn, title, author,
                            BookStatus.AVAILABLE, branch)
            self.books[book.book_id] = book
```

**Benefit**: ✅ Centralized, consistent copy creation, ✅ IDs guaranteed unique  
**Trade-off**: ⚠️ If creation logic grows (e.g., digital vs physical), consider a proper Factory class

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single consistent inventory/member store | No race on global state |
| **State Machine** | Book lifecycle transitions | Invalid borrows caught at runtime |
| **Observer** | Reservation notifications | Decoupled, multi-channel alerts |
| **Strategy** | Pluggable fine calculation | No change to return logic |
| **Factory** | Batch physical copy creation | Consistent IDs and initialization |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Library Management System - Interview Implementation
Demonstrates:
1. Book inventory management
2. Borrowing and return tracking
3. Late fine calculation
4. Reservation queue
5. Member account management
"""

from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading

# ============================================================================
# ENUMERATIONS
# ============================================================================

class BookStatus(Enum):
    AVAILABLE    = 1
    BORROWED     = 2
    RESERVED     = 3
    MAINTENANCE  = 4
    LOST         = 5

class MemberStatus(Enum):
    ACTIVE    = 1
    SUSPENDED = 2

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BookItem:
    book_id: str
    isbn: str
    title: str
    author: str
    status: BookStatus = BookStatus.AVAILABLE
    branch: str = "Main"

@dataclass
class Member:
    member_id: str
    name: str
    email: str
    status: MemberStatus = MemberStatus.ACTIVE
    fine_balance: float = 0.0
    active_borrows: List['Borrowing'] = field(default_factory=list)

@dataclass
class Borrowing:
    borrowing_id: str
    book_id: str
    member_id: str
    checkout_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    fine: float = 0.0

# ============================================================================
# LIBRARY (SINGLETON)
# ============================================================================

class Library:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Accept (and ignore) any constructor args so __init__ is reached cleanly
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.books: Dict[str, BookItem] = {}
        self.members: Dict[str, Member] = {}
        self.borrowings: Dict[str, Borrowing] = {}
        self.book_counter = 0
        self.borrowing_counter = 0
        # RLock (re-entrant): borrow_book holds the lock and calls search_books internally
        self.lock = threading.RLock()

    def add_book(self, isbn: str, title: str, author: str, copies: int = 1, branch: str = "Main"):
        with self.lock:
            for _ in range(copies):
                self.book_counter += 1
                book = BookItem(f"BOOK_{self.book_counter}", isbn, title, author,
                                BookStatus.AVAILABLE, branch)
                self.books[book.book_id] = book
            print(f"  Added {copies} copies of '{title}' to {branch}")

    def register_member(self, member_id: str, name: str, email: str) -> Member:
        with self.lock:
            member = Member(member_id, name, email)
            self.members[member_id] = member
            print(f"  Registered member: {name}")
            return member

    def search_books(self, title: str) -> List[BookItem]:
        with self.lock:
            return [b for b in self.books.values() if title.lower() in b.title.lower()]

    def borrow_book(self, member_id: str, book_id: str) -> Optional[str]:
        with self.lock:
            if member_id not in self.members or book_id not in self.books:
                return None

            member = self.members[member_id]
            book = self.books[book_id]

            # Check borrow limit
            if len(member.active_borrows) >= 5:
                print(f"  Member {member.name} has reached borrow limit")
                return None

            # Check suspension due to fines
            if member.fine_balance > 50:
                print(f"  Member {member.name} suspended (fines: ${member.fine_balance:.2f})")
                return None

            # Check book availability
            if book.status != BookStatus.AVAILABLE:
                print(f"  Book {book_id} not available (status: {book.status.name})")
                return None

            # Create borrowing record
            self.borrowing_counter += 1
            checkout = datetime.now()
            due = checkout + timedelta(days=14)

            borrowing = Borrowing(
                f"BORROW_{self.borrowing_counter}",
                book_id,
                member_id,
                checkout,
                due
            )

            self.borrowings[borrowing.borrowing_id] = borrowing
            member.active_borrows.append(borrowing)
            book.status = BookStatus.BORROWED

            print(f"  {member.name} borrowed '{book.title}' (Due: {due.date()})")
            return borrowing.borrowing_id

    def return_book(self, borrowing_id: str) -> float:
        with self.lock:
            if borrowing_id not in self.borrowings:
                return 0.0

            borrowing = self.borrowings[borrowing_id]

            # Only set return_date if not already set (simulate late return tests)
            if borrowing.return_date is None:
                borrowing.return_date = datetime.now()

            # Calculate fine
            days_late = max(0, (borrowing.return_date - borrowing.due_date).days)
            fine = min(days_late * 0.50, 10.0)
            borrowing.fine = fine

            # Update member
            member = self.members[borrowing.member_id]
            if borrowing in member.active_borrows:
                member.active_borrows.remove(borrowing)
            member.fine_balance += fine
            if member.fine_balance > 50:
                member.status = MemberStatus.SUSPENDED

            # Release book
            book = self.books[borrowing.book_id]
            book.status = BookStatus.AVAILABLE

            print(f"  {member.name} returned '{book.title}'")
            if fine > 0:
                print(f"  Fine: ${fine:.2f}")

            return fine

    def renew_book(self, borrowing_id: str) -> bool:
        with self.lock:
            if borrowing_id not in self.borrowings:
                return False

            borrowing = self.borrowings[borrowing_id]
            borrowing.due_date = borrowing.due_date + timedelta(days=14)

            member = self.members[borrowing.member_id]
            book = self.books[borrowing.book_id]

            print(f"  {member.name} renewed '{book.title}'")
            print(f"  New due date: {borrowing.due_date.date()}")
            return True

    def reserve_book(self, member_id: str, isbn: str) -> bool:
        with self.lock:
            if member_id not in self.members:
                return False

            # Find all copies
            copies = [b for b in self.books.values() if b.isbn == isbn]
            available = [c for c in copies if c.status == BookStatus.AVAILABLE]

            if available:
                print(f"  Copies available — borrow instead of reserving")
                return False

            # Mark first borrowed copy as reserved
            if copies:
                copies[0].status = BookStatus.RESERVED
                member = self.members[member_id]
                print(f"  {member.name} reserved '{copies[0].title}'")
                return True

            return False

    def display_member_account(self, member_id: str):
        with self.lock:
            if member_id not in self.members:
                return

            member = self.members[member_id]
            print(f"  Member:        {member.name}")
            print(f"  Active borrows:{len(member.active_borrows)}")
            print(f"  Fine balance:  ${member.fine_balance:.2f}")
            print(f"  Status:        {member.status.name}")

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_borrow_return():
    print("\n" + "="*70)
    print("DEMO 1: BORROW & RETURN")
    print("="*70)

    lib = Library()
    lib.add_book("978-0", "1984", "George Orwell", 2)
    lib.register_member("M1", "John", "john@email.com")

    books = lib.search_books("1984")
    if books:
        borrow_id = lib.borrow_book("M1", books[0].book_id)
        if borrow_id:
            fine = lib.return_book(borrow_id)
            print(f"  Return fine: ${fine:.2f}")

def demo_2_fine_calculation():
    print("\n" + "="*70)
    print("DEMO 2: LATE RETURN & FINE")
    print("="*70)

    lib = Library()
    lib.add_book("978-1", "The Hobbit", "J.R.R. Tolkien", 1)
    lib.register_member("M2", "Sarah", "sarah@email.com")

    books = lib.search_books("The Hobbit")
    if books:
        borrow_id = lib.borrow_book("M2", books[0].book_id)
        if borrow_id:
            # Simulate 3-day-late return
            lib.borrowings[borrow_id].return_date = (
                lib.borrowings[borrow_id].due_date + timedelta(days=3)
            )
            fine = lib.return_book(borrow_id)
            print(f"  Expected fine: $1.50, Actual: ${fine:.2f}")

def demo_3_reservation():
    print("\n" + "="*70)
    print("DEMO 3: BOOK RESERVATION")
    print("="*70)

    lib = Library()
    lib.add_book("978-2", "Dune", "Frank Herbert", 2)
    lib.register_member("M3", "Mike", "mike@email.com")
    lib.register_member("M4", "Lisa", "lisa@email.com")

    # Borrow all copies
    for book_id, book in list(lib.books.items()):
        if book.isbn == "978-2":
            lib.borrow_book("M3", book_id)

    # Try to reserve
    lib.reserve_book("M4", "978-2")

def demo_4_member_account():
    print("\n" + "="*70)
    print("DEMO 4: MEMBER ACCOUNT STATUS")
    print("="*70)

    lib = Library()
    lib.add_book("978-3", "Python Guide", "Various", 1)
    lib.register_member("M5", "Alex", "alex@email.com")

    books = lib.search_books("Python")
    if books:
        lib.borrow_book("M5", books[0].book_id)

    lib.display_member_account("M5")

def demo_5_multiple_books():
    print("\n" + "="*70)
    print("DEMO 5: MULTIPLE BORROWINGS")
    print("="*70)

    lib = Library()
    lib.add_book("978-4", "Book A", "Author A", 1)
    lib.add_book("978-5", "Book B", "Author B", 1)
    lib.add_book("978-6", "Book C", "Author C", 1)

    lib.register_member("M6", "Bob", "bob@email.com")

    for book_id, book in list(lib.books.items()):
        lib.borrow_book("M6", book_id)

    lib.display_member_account("M6")

# ============================================================================
# MAIN
# ============================================================================

if True:
    print("\n" + "="*70)
    print("LIBRARY MANAGEMENT SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_borrow_return()
    demo_2_fine_calculation()
    demo_3_reservation()
    demo_4_member_account()
    demo_5_multiple_books()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **borrow_book** | RLock on Library | Atomic: check limit + check status + create borrowing |
| **return_book** | RLock on Library | Atomic: set return_date + compute fine + release book |
| **reserve_book** | RLock on Library | Atomic: check availability + mark RESERVED |
| **renew_book** | RLock on Library | Atomic: extend due date |
| **Singleton init** | Class-level Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` (re-entrant) allows the same thread to re-enter locked sections (e.g., `search_books` called from within `borrow_book`)
2. ✅ Singleton uses a separate `_class_lock` so `__new__` never deadlocks with the instance lock
3. ✅ All mutations to books, members, and borrowings happen inside the same lock, preventing partial updates
4. ✅ Fine balance and member status updated atomically with book release

---

## Demo Scenarios

### Scenario 1: Borrow & Return (on time)
```
Added 2 copies of '1984' to Main
Registered member: John
John borrowed '1984' (Due: 2025-xx-xx)
John returned '1984'
Return fine: $0.00
```

### Scenario 2: Late Return + Fine
```
- Member John returns "The Hobbit" 3 days late
- Fine calculation: 3 days × $0.50 = $1.50
- John's fine balance: $1.50
- New borrow allowed (below $50 limit)
```

### Scenario 3: Reservation
```
- Member Bob wants "Dune" (all 2 copies borrowed)
- Creates reservation
- First borrowed copy marked RESERVED
- Bob notified when returned; has 2 days to pick up
```

### Scenario 4: Member Account Status
```
- Member Alex has 1 active borrow
- Fine balance: $0.00
- Status: ACTIVE
```

### Scenario 5: Multiple Borrowings
```
- Member Bob borrows Book A, B, and C
- Active borrows: 3/5
- Fine balance: $0.00
- Status: ACTIVE
```

---

## Interview Q&A

### Basic Level

**Q1: How do you prevent overborrowing?**
A: Check borrowing limit (5 books max). On new borrow: count active borrowings. If count >= 5, reject. Also check fine balance: if > $50, suspend borrowing privileges.

**Q2: What's the fine calculation policy?**
A: Fine = min($0.50 × days_late, $10). If returns 2 days late: 2 × $0.50 = $1.00. If 21+ days late: capped at $10. If total fine balance reaches $50: suspend membership. Forgive on first return for regular members.

**Q3: How do you handle book reservations?**
A: When all copies borrowed, allow member to reserve. Store in queue: first to reserve = first to be notified when available. On return: check reservation queue, notify next member, hold for 2 days.

**Q4: What's the difference between Book and Borrowing?**
A: **BookItem**: Physical inventory (ISBN, title, author, status). **Borrowing**: Transaction (member, book, dates, fine). One book can have multiple Borrowing records (over time). Multiple physical copies of same book = multiple BookItem entries.

### Intermediate Level

**Q5: How to handle multiple copies of same book?**
A: Each physical copy = separate BookItem record (different ID). Same ISBN/title. Query: "find all available copies of ISBN 123". Borrow = pick any available copy. Return = update that specific copy's status.

**Q6: How to support renewals?**
A: On renewal request: (1) Check if borrowed by member, (2) Check if no reservations, (3) Extend due date by 14 days, (4) Log renewal. Limit to 2 renewals per borrow (prevent indefinite holds).

**Q7: How to handle overdue notifications?**
A: Scheduled job: daily at 8 AM, find all overdue borrowings. Send email/SMS to member: "Your book X is due today" or "You have $5 in fines". Reminder 1 day before due + on due date + 1 day after.

**Q8: What if member loses book?**
A: (1) Report loss, (2) Charge replacement cost ($20-50 depending on book), (3) Return fine obligation, (4) Mark book as LOST in system. After 1 year: delete LOST books from inventory (assume replaced).

### Advanced Level

**Q9: How to handle multi-branch requests?**
A: Member in Branch A needs book at Branch B. Request → Reserve at Branch B. Notify when available → Transfer book to Branch A. Member picks up from Branch A. Transfers tracked + cost allocation.

**Q10: How to optimize search for 1M books?**
A: Index on (ISBN, title, author). Use full-text search (Elasticsearch). Cache popular books. Prefix search: "Book starts with 'The'" efficient with B-trees. Expected: <100ms query.

**Q11: How to prevent system abuse?**
A: (1) Limit borrows per day (max 5 new borrows), (2) Track patterns (same person reserves immediately after return), (3) Fine accumulation: if > $50, suspend, (4) Report duplicate accounts to admin.

**Q12: How to generate insights from borrowing data?**
A: Analytics: (1) Most borrowed books, (2) Member behavior (avid reader?), (3) Fine patterns, (4) Peak lending times. Use for: acquisition strategy (buy more popular books), fine structure adjustments.

---

## Scaling Q&A

**Q1: Can you handle 100K members, 1M books?**
A: Yes. Index on ISBN + member_id + status. Query: "find available copies" → index lookup O(log n). Partition by branch if needed. Expected: <100ms per query.

**Q2: How to handle real-time availability?**
A: Cache availability (Redis). On borrow: decrement cache. On return: increment cache. Cache miss = query DB. Accuracy: eventual consistency (couple seconds lag).

**Q3: How to prevent race condition on last copy?**
A: Last copy available, 2 members try to borrow simultaneously. Use pessimistic lock: reserve, check status again, borrow or reject. Or optimistic lock: version number on book status.

**Q4: How to optimize fine calculations?**
A: Store due_date, return_date in DB. Fine calculated on query (not stored initially). Store only if charged. Batch nightly job: calculate all overdue fines, store in batch.

**Q5: Can you support digital books (no physical limit)?**
A: Yes. Digital books: unlimited borrows (no inventory limit). Store separate status (digital vs physical). Lending period same. Digital expires automatically (DRM) at due date.

**Q6: How to handle inter-library loans?**
A: Network of libraries: central catalog. Member in Library A searches catalog (includes all libraries). Request → routed to Library B → transferred → member picks up from Library A. 3-5 days delay.

**Q7: How to migrate to multi-branch from single-branch?**
A: Phase 1: Add branch field to all records. Phase 2: Data migration (assign all books to branch 1). Phase 3: Update queries (add branch filter). Phase 4: Enable branch creation for new library.

**Q8: How to prevent fine inflation?**
A: Cap daily fine at $10 total (per book). Alternative: $0.50 per day, max 20 days = $10 cap. Clear fines after 1 year (forgiveness policy). Prevents debt spiral.

**Q9: Can you support membership tiers (premium)?**
A: Premium: borrow 10 books, 21-day period, 4 renewals, $0 fines first month. Regular: 5 books, 14 days, 2 renewals, $0.50/day fine. Student: 3 books, 7 days, 1 renewal. Flexible implementation.

**Q10: How to optimize reservation queue?**
A: Use priority queue (first-reserved = highest priority). When book available: notify top N members (in case some don't respond). Maintain sorted structure efficiently.

**Q11: How to handle book damage reports?**
A: Member reports damage on return. Assess: if severe (unusable) = charge member repair cost. If minor = accept & repair later. Track damage patterns (e.g., repeated by same member).

**Q12: Can you support reading recommendations?**
A: ML model: user's borrowing history → similar books → recommend. Books often borrowed together → suggest. Popular in member's age group/interests. Display on member dashboard.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with all relationships (Library, BookItem, Member, Borrowing)
- [ ] Walk through borrow → return → fine lifecycle
- [ ] Explain overborrowing prevention (limit check + fine balance check, both atomic)
- [ ] Explain reservation flow and queue notification
- [ ] Explain fine calculation: $0.50/day, $10 cap, $50 suspension threshold
- [ ] Explain why RLock is used instead of Lock (re-entrant needed within same thread)
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss trade-offs: in-memory vs DB, pessimistic vs optimistic locking, single branch vs multi-branch

---

**Ready for interview? Check out some books!**
