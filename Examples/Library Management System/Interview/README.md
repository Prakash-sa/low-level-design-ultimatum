# Library Management System - Interview Guide

## Overview

A comprehensive library management system demonstrating **SOLID principles**, **design patterns**, and scalable architecture for handling books, members, and circulation.

### Key Metrics
- **Lines of Code**: ~1,300 (production) / ~450 (interview compact)
- **Design Patterns**: 6
- **SOLID Principles**: 5/5
- **Complexity**: O(1) book search, O(log N) for sorting
- **Interview Time**: 75 minutes

---

## Functional Requirements (FR)

| # | Requirement | Details | Priority |
|---|---|---|---|
| FR1 | Add Books | Add new books with ISBN, title, author, copies | MUST |
| FR2 | Issue Book | Member borrows book, create checkout record | MUST |
| FR3 | Return Book | Member returns book, update inventory | MUST |
| FR4 | Search Books | Search by ISBN, title, author | MUST |
| FR5 | Member Mgmt | Register members, track status | MUST |
| FR6 | Reservations | Reserve unavailable books for members | SHOULD |
| FR7 | Fine System | Calculate fines for overdue books | SHOULD |
| FR8 | Notifications | Notify members about due dates, availability | SHOULD |
| FR9 | Reports | Generate reports on book circulation, popular books | SHOULD |
| FR10 | Multi-Library | Support multiple library branches | SHOULD |

---

## Non-Functional Requirements (NFR)

| # | Requirement | Details | Target |
|---|---|---|---|
| NFR1 | Availability | System up 24/7, fault-tolerant | 99.5% uptime |
| NFR2 | Performance | Book search < 50ms, issue/return < 100ms | Real-time |
| NFR3 | Concurrency | Handle 100+ simultaneous checkouts | Thread-safe |
| NFR4 | Scalability | Support 1M+ books, 100K+ members | Horizontal |
| NFR5 | Security | Role-based access (admin, member, staff) | Encrypted |
| NFR6 | Auditability | All transactions logged with timestamps | Full history |
| NFR7 | Usability | Simple API, clear error messages | User-friendly |
| NFR8 | Maintainability | Modular design, extensible | SOLID adherence |

---

## Design Patterns Used

### 1. **Singleton Pattern** ✓
**Class**: `LibrarySystem`
```python
@classmethod
def get_instance(cls):
    if cls._instance is None:
        cls._instance = LibrarySystem()
    return cls._instance
```
**Why**: Ensure single library system instance  
**Benefit**: Centralized library management, prevents duplicate systems

---

### 2. **Strategy Pattern** ✓
**Classes**: `SearchStrategy`, `FineCalculationStrategy`
```python
class SearchStrategy(ABC):
    @abstractmethod
    def search(self, books, query):
        pass

class ISBNSearchStrategy(SearchStrategy):
    def search(self, books, isbn):
        return [b for b in books if b.isbn == isbn]

class TitleSearchStrategy(SearchStrategy):
    def search(self, books, title):
        return [b for b in books if title.lower() in b.title.lower()]
```
**Why**: Different search/fine calculation algorithms  
**Benefit**: Easily swap algorithms without changing core logic

---

### 3. **Factory Pattern** ✓
**Classes**: `MemberFactory`, `BookFactory`
```python
class MemberFactory:
    @staticmethod
    def create_member(member_type, name, email):
        if member_type == "student":
            return StudentMember(name, email)
        elif member_type == "faculty":
            return FacultyMember(name, email)
        elif member_type == "guest":
            return GuestMember(name, email)
```
**Why**: Encapsulate member/book creation  
**Benefit**: Easy to add new types without changing existing code

---

### 4. **Observer Pattern** ✓
**Classes**: `MemberNotifier`, `LibraryNotification`
```python
class Observer(ABC):
    @abstractmethod
    def update(self, notification):
        pass

class EmailNotifier(Observer):
    def update(self, notification):
        self.send_email(notification)

class SMSNotifier(Observer):
    def update(self, notification):
        self.send_sms(notification)
```
**Why**: Notify members about due dates, availability  
**Benefit**: Loose coupling, multiple notification channels

---

### 5. **State Pattern** ✓
**Classes**: `BookStatus`, `CheckoutStatus`
- BookStatus: AVAILABLE → CHECKED_OUT → RESERVED → AVAILABLE
- CheckoutStatus: ACTIVE → OVERDUE → RETURNED → CLOSED
**Why**: Encapsulate state transitions  
**Benefit**: Type-safe, prevents invalid transitions

---

### 6. **Decorator Pattern** ✓
**Classes**: `PremiumMember`, `VIPMember`
```python
class Member:
    def get_checkout_limit(self):
        return 5

class PremiumMember(Member):
    def __init__(self, member):
        self.member = member
    
    def get_checkout_limit(self):
        return self.member.get_checkout_limit() + 5
```
**Why**: Add features (longer checkout periods, more books) dynamically  
**Benefit**: Composable functionality

---

## SOLID Principles

### S - Single Responsibility Principle ✓
```
Book              → Manages book data only
Member            → Manages member data only
Checkout          → Tracks book checkouts only
Library           → Orchestrates operations only
SearchEngine      → Handles search only
FineCalculator    → Calculates fines only
```
**Each class has ONE reason to change**

### O - Open/Closed Principle ✓
```
Member (open for extension)
├── StudentMember
├── FacultyMember
├── PremiumMember
└── GuestMember

SearchStrategy (open for extension)
├── ISBNSearchStrategy
├── TitleSearchStrategy
├── AuthorSearchStrategy
└── KeywordSearchStrategy
```
**Open for extension via subclasses, closed for modification**

### L - Liskov Substitution Principle ✓
```python
def checkout_book(self, member: Member, book: Book):
    # Works with any Member subclass
    # StudentMember, FacultyMember, PremiumMember all behave consistently
    pass
```
**All subclasses can replace parent without breaking code**

### I - Interface Segregation Principle ✓
```
Observer (just update)
├── EmailNotifier
├── SMSNotifier
└── PushNotifier

SearchStrategy (just search)
├── ISBNSearchStrategy
└── TitleSearchStrategy
```
**Classes only depend on interfaces they use**

### D - Dependency Inversion Principle ✓
```python
class LibrarySystem:
    def __init__(self, search_strategy: SearchStrategy):
        self.search_strategy = search_strategy
    
    def search(self, query):
        # Depends on abstraction, not concrete class
        return self.search_strategy.search(self.books, query)
```
**Depend on abstractions, not concrete classes**

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│            LIBRARY MANAGEMENT SYSTEM                │
└─────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐        ┌────▼────┐       ┌───▼────┐
    │ MEMBER │        │ LIBRARY  │       │ BOOK   │
    │MANAGER │        │SYSTEM    │       │MANAGER │
    └────┬───┘        └────┬─────┘       └───┬────┘
         │                  │                  │
    Register        Checkout/Return      Add/Remove
    Track Status    Search               Manage Stock
         │                  │                  │
    ┌────▼───────────────────────────────────▼─┐
    │     LIBRARY SYSTEM (Singleton)            │
    ├───────────────────────────────────────────┤
    │ - books: Dict[isbn, Book]                │
    │ - members: Dict[id, Member]              │
    │ - checkouts: Dict[id, Checkout]          │
    │ - search_strategy: SearchStrategy        │
    │ - fine_calculator: FineCalculator        │
    │ - notifiers: List[Observer]              │
    └───────────────────────────────────────────┘
         │                  │                  │
    ┌────▼─┐        ┌──────▼──────┐      ┌───▼────┐
    │BOOKS │        │  CHECKOUTS  │      │MEMBERS │
    ├──────┤        ├─────────────┤      ├────────┤
    │ISBN  │        │ Member ID   │      │Type:   │
    │Title │        │ Book ISBN   │      │Student │
    │Author│        │ Checkout    │      │Faculty │
    │Stock │        │ Due Date    │      │Premium │
    │      │        │ Fine        │      │Guest   │
    └──────┘        └─────────────┘      └────────┘
```

---

## State Machines

### Book State Machine
```
    ┌─────────┐
    │AVAILABLE│
    └────┬────┘
         │ checkout_book()
         │
    ┌────▼──────┐    reserve_book()    ┌──────────┐
    │CHECKED_OUT├──────────────────────►│RESERVED  │
    └────┬──────┘                       └────┬─────┘
         │                                   │
         │ return_book()                     │ checkout_reserved()
         │                                   │
         └───────────────┬───────────────────┘
                         │
                    ┌────▼────┐
                    │AVAILABLE│
                    └─────────┘
```

### Checkout State Machine
```
    ┌──────┐
    │ACTIVE│
    └──┬───┘
       │
   7 days  Overdue?
       │     no
       ├──────────┐
       │          │
   ┌───▼───┐   ┌──▼──────┐
   │OVERDUE│   │RETURNED │
   └───────┘   └─────────┘
       │
    Pay fine
       │
    ┌──▼──────┐
    │CLOSED   │
    └─────────┘
```

### Member Checkout Flow
```
    Member arrives
         │
         ▼
    ┌──────────────────┐
    │ Search for books │
    │ (by ISBN/Title)  │
    └─┬────────┬───────┘
      │        │
    Found   Not Found
      │        │
      ▼        ▼
    Check   Return null
    Stock
      │
      ├─ Stock > 0
      │    │
      │    ▼
      │ Issue book
      │    │
      │    ▼
      │ Create checkout
      │    │
      │    ▼
      │ Update inventory
      │    │
      │    ▼
      │ Send notification
      │
      └─ Stock = 0
           │
           ▼
         Add to
       Reservation
```

---

## Class Hierarchy

```
Book (Base)
├── TextBook (with subject)
├── ReferenceBook (non-checkable)
└── AudioBook (with duration)

Member (Abstract)
├── StudentMember (5 books, 21 days)
├── FacultyMember (10 books, 30 days)
├── PremiumMember (15 books, 60 days)
└── GuestMember (2 books, 7 days)

SearchStrategy (Abstract)
├── ISBNSearchStrategy
├── TitleSearchStrategy
├── AuthorSearchStrategy
└── KeywordSearchStrategy

FineCalculationStrategy (Abstract)
├── StandardFineCalculator ($0.50/day)
├── PremiumFineCalculator ($0.25/day)
└── GuestFineCalculator ($1.00/day)

Observer (Abstract)
├── EmailNotifier
├── SMSNotifier
└── PushNotifier
```

---

## Key Algorithms

### 1. Book Search Algorithm
```
Time: O(N) linear search, O(log N) with indexing
Space: O(K) where K = results

Algorithm:
1. Choose search strategy (ISBN, Title, Author, Keyword)
2. Apply filter to all books
3. Return matching results
4. Rank by relevance (optional)

Optimization:
- Index books by ISBN (O(1) lookup)
- Cache popular searches
- Use full-text search for keywords
```

### 2. Fine Calculation
```
Time: O(1)
Space: O(1)

Algorithm:
1. Get checkout date
2. Get return date
3. Calculate days overdue
4. Apply fine rate strategy
5. Add penalties if applicable

Example:
- Checkout: 2024-11-20, Due: 2024-12-04 (14 days)
- Returned: 2024-12-08
- Overdue: 4 days
- Fine: 4 × $0.50 = $2.00
```

### 3. Availability Check
```
Time: O(1) with indexing
Space: O(1)

Algorithm:
1. Look up book by ISBN
2. Get total copies
3. Count checked out copies
4. Get reservation count
5. Calculate available = total - checked_out - reserved
6. Return availability status
```

---

## Time Complexity Analysis

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| add_book() | O(1) | O(1) | Direct insertion |
| search_book() | O(N) | O(K) | N = books, K = results |
| checkout_book() | O(1) | O(1) | Direct lookup with index |
| return_book() | O(1) | O(1) | Direct update |
| calculate_fine() | O(1) | O(1) | Simple arithmetic |
| get_member_books() | O(M) | O(M) | M = member checkouts |
| reserve_book() | O(1) | O(1) | Direct insertion |
| get_available_books() | O(1) | O(1) | With caching |

---

## Interview Talking Points

### "Tell me about the patterns you used"
**Answer**:
"I used 6 design patterns:
1. **Singleton** for LibrarySystem (one instance)
2. **Strategy** for search and fine calculation (swap algorithms)
3. **Factory** for member/book creation (encapsulate creation)
4. **Observer** for notifications (real-time updates)
5. **State** for book and checkout states (type-safe transitions)
6. **Decorator** for premium members (add features dynamically)

Each pattern solves a specific problem in library management."

### "How would you handle concurrent checkouts?"
**Answer**:
"Use thread-safe operations:
```python
with self.checkout_lock:
    if book.available_copies > 0:
        book.available_copies -= 1
        checkout = Checkout(member, book)
```

This prevents race conditions where two members get the same book copy."

### "How to calculate late fees?"
**Answer**:
"Use Strategy pattern for different rates:
```python
class FineCalculator:
    def calculate(self, checkout):
        days_overdue = (today - checkout.due_date).days
        if days_overdue <= 0:
            return 0
        return days_overdue * self.rate_per_day
```

Different member types get different rates:
- Student: $0.50/day
- Faculty: $0.25/day
- Guest: $1.00/day"

### "How to handle book reservations?"
**Answer**:
"Implement a reservation queue:
```python
class Book:
    def reserve(self, member):
        if self.available_copies > 0:
            self.checkout(member)
        else:
            self.reservations.append(member)
            notify_member(member)  # Notify when available
```

Benefits:
- Queue ensures fairness
- Auto-notify when book becomes available
- Prevent lost requests"

### "How would you extend for multiple branches?"
**Answer**:
"Create branch-aware system:
```python
class LibraryBranch:
    def __init__(self, branch_id, name, location):
        self.books = {}  # Branch-specific inventory
        self.members = {}
        self.checkouts = {}

class LibrarySystem:
    def __init__(self):
        self.branches = {}  # Dict[branch_id, LibraryBranch]
    
    def search_all_branches(self, query):
        # Search across branches
        pass
```

This allows:
- Inter-branch transfers
- Cross-branch holds
- Unified member account"

### "How do you test this system?"
**Answer**:
"Unit tests for each component:
```python
def test_checkout():
    lib = LibrarySystem()
    book = Book('1234', 'Python', 'Guido', 5)
    member = StudentMember('John', 'john@uni.edu')
    lib.add_book(book)
    checkout = lib.checkout_book(member, book)
    assert checkout is not None
    assert book.available_copies == 4

def test_fine_calculation():
    checkout = Checkout(member, book)
    checkout.due_date = today - timedelta(days=5)
    fine = calculator.calculate_fine(checkout)
    assert fine == 2.50  # 5 days × $0.50
```

Integration tests:
- Checkout → Return → Verify fine
- Reserve → Notify → Auto-checkout
- Multi-member concurrent checkouts"

---

## Edge Cases

| Case | Handling | Code |
|------|----------|------|
| No stock | Add to reservation | `if stock == 0: reserve()` |
| Overdue book | Calculate fine, restrict checkouts | `check_debt_before_checkout()` |
| Invalid member | Reject checkout | `if not member.is_active: return None` |
| Return after deadline | Add late fee | `calculate_fine()` |
| Concurrent checkout | Use locks | `with lock: checkout()` |
| Lost book | Mark as lost, charge replacement fee | `mark_lost()` |
| Reserve expired | Auto-cancel if not picked up | `check_reservation_expiry()` |
| Member limit reached | Reject checkout | `if checkouts >= limit: return False` |

---

## Performance Characteristics

### Search Performance
- **Average**: O(N/2) - scan average half of books
- **Best**: O(1) - ISBN indexed search
- **Worst**: O(N) - full text search on all books

### Memory Usage
- Per book: ~500 bytes
- Per member: ~300 bytes
- Per checkout: ~200 bytes
- 100K books, 10K members: ~70 MB data

### Throughput
- Checkouts/minute: 1000+ (1M+ per day)
- Returns/minute: 500+ (depends on fine calculation)
- Searches/minute: 10000+ (parallel searches)

---

## Common Interview Extensions

**Q1**: "How to recommend books to members?"
**A1**: Implement recommendation engine based on checkout history

**Q2**: "How to handle book donations?"
**A2**: Add donation queue with approval workflow

**Q3**: "Can members exchange books between branches?"
**A3**: Create transfer request system with tracking

**Q4**: "How to implement membership tiers?"
**A4**: Use Decorator pattern for benefits (limits, discounts)

**Q5**: "How to track most popular books?"
**A5**: Maintain circulation statistics with rankings

**Q6**: "Can members renew books before due date?"
**A6**: Add renewal logic with limit checks (typically 2 renewals)

**Q7**: "How to implement holds for recalled books?"
**A7**: Create hold system with automatic processing

**Q8**: "How about inter-library loans?"
**A8**: Extend to support external library requests

---

## Summary

**Library Management System demonstrates:**
- ✅ 6 Design Patterns (Singleton, Strategy, Factory, Observer, State, Decorator)
- ✅ 5 SOLID Principles (SRP, OCP, LSP, ISP, DIP)
- ✅ Real-world problem solving
- ✅ Clean, modular architecture
- ✅ Scalable design
- ✅ Thread-safe operations
- ✅ Edge case handling
- ✅ Performance optimization

**Perfect for interviews because:**
- Shows understanding of library operations
- Demonstrates design patterns in practice
- Handles multiple requirements
- Extensible and maintainable
- Real-world applicable
- Room for follow-up questions
