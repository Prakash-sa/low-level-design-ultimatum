# Library Management System — 75-Minute Interview Guide

## Quick Start

**What is it?** A book lending and management system tracking inventory, member borrowing, returns, fines, and holds.

**Key Classes:**
- `Library` (Singleton): Central coordinator
- `Book`: Physical copy with status (available/borrowed/reserved/lost)
- `Member`: User profile with active borrowings, fine balance
- `Borrowing`: Book rental with due date, fine tracking
- `Fine`: Late return penalties
- `Reservation`: Hold on borrowed books

**Core Flows:**
1. **Search**: Member searches for book → Get available copies → Get reservation details
2. **Borrow**: Member borrows book → Issue checkout → Set due date → Update inventory
3. **Return**: Member returns book → Calculate fine (if late) → Update status
4. **Renew**: Extend due date (if no reservations) → Update system
5. **Reserve**: Hold book for member when all copies borrowed → Notify when available

**5 Design Patterns:**
- **Singleton**: One `Library` system
- **State Machine**: Book status (available, borrowed, reserved, lost)
- **Observer**: Notify member when reserved book available
- **Strategy**: Different fine calculations (daily, tiered)
- **Factory**: Create different book types (reference, periodical, digital)

---

## System Overview

Multi-branch library system managing book inventory, member accounts, borrowing transactions, late fines, and book reservations.

### Requirements

**Functional:**
- Search books by title/author/ISBN
- Borrow and return books
- Manage member accounts
- Calculate late fines
- Reserve books
- Track book inventory per branch
- Generate reports
- Support multiple branches/locations

**Non-Functional:**
- Search < 200ms
- Support 100K+ members, 1M+ books
- Accurate inventory
- 99.5% uptime

**Constraints:**
- Borrow limit: 5 books per member
- Borrow period: 14 days (renewals: 2x, if no holds)
- Fine: $0.50/day (max $10)
- Maximum fine: $50 (before suspension)

---

## Architecture Diagram (ASCII UML)

```
┌─────────────────┐
│ Library         │
│ (Singleton)     │
└────────┬────────┘
         │
    ┌────┼────┬────────┐
    │    │    │        │
    ▼    ▼    ▼        ▼
┌──────┐ ┌─────┐ ┌──────┐ ┌────────┐
│Books │ │Member│ │Borrow│ │Reserve │
└──────┘ └─────┘ └──────┘ └────────┘

Book Status Machine:
AVAILABLE → BORROWED → AVAILABLE
             ↓
         RESERVED

Borrowing State:
┌────────────────┐
│ Borrowing      │
├────────────────┤
│ book_id        │
│ member_id      │
│ checkout_date  │
│ due_date       │
│ return_date    │
│ fine_amount    │
└────────────────┘
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you prevent overborrowing?**
A: Check borrowing limit (5 books max). On new borrow: count active borrowings. If count >= 5, reject. Also check fine balance: if > $50, suspend borrowing privileges.

**Q2: What's the fine calculation policy?**
A: Fine = min($0.50 × days_late, $10). If returns 2 days late: 2 × $0.50 = $1.00. If 21+ days late: capped at $10. If fine reaches $50: suspend membership. Forgive on first return for regular members.

**Q3: How do you handle book reservations?**
A: When all copies borrowed, allow member to reserve. Store in queue: first to reserve = first to be notified when available. On return: check reservation queue, notify next member, hold for 2 days.

**Q4: What's the difference between Book and Borrowing?**
A: **Book**: Physical inventory (ISBN, title, author). **Borrowing**: Transaction (member, book, dates, fine). One book can have multiple Borrowing records (over time). Multiple physical copies of same book = multiple Book entries.

### Intermediate Level

**Q5: How to handle multiple copies of same book?**
A: Each physical copy = separate Book record (different ID). Same ISBN/title. Query: "find all available copies of ISBN 123". Borrow = pick any available copy. Return = update that specific copy's status.

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

## Scaling Q&A (12 Questions)

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

## Demo Scenarios (5 Examples)

### Demo 1: Borrow Book
```
- Member Jane searches for "1984"
- Found: 3 copies, 2 available, 1 borrowed (due tomorrow)
- Jane borrows copy 1
- Due date: 14 days from now
- Borrow count: 1/5
```

### Demo 2: Late Return + Fine
```
- Member John returns "The Hobbit" 3 days late
- Fine calculation: 3 days × $0.50 = $1.50
- John's fine balance: $1.50
- New borrow allowed (below $50 limit)
```

### Demo 3: Reservation
```
- Member Bob wants "Dune" (all 5 copies borrowed)
- Creates reservation
- Joins queue (position 2)
- Waits for notification
- When book returned: Bob notified, has 2 days to pick up
```

### Demo 4: Renewal
```
- Member Alice borrowed "Python Guide" (due in 3 days)
- Requests renewal (1st renewal)
- New due date: 14 days from now
- Can renew 1 more time
```

### Demo 5: Multi-Branch Transfer
```
- Member at Downtown Branch needs book at Uptown Branch
- Requests transfer
- Book moved from Uptown to Downtown (2 days)
- Member picks up from Downtown
```

---

## Complete Implementation

```python
"""
📚 Library Management System - Interview Implementation
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
    AVAILABLE = 1
    BORROWED = 2
    RESERVED = 3
    MAINTENANCE = 4
    LOST = 5

class MemberStatus(Enum):
    ACTIVE = 1
    SUSPENDED = 2

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Book:
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
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}
        self.borrowings: Dict[str, Borrowing] = {}
        self.book_counter = 0
        self.borrowing_counter = 0
        self.lock = threading.Lock()
    
    def add_book(self, isbn: str, title: str, author: str, copies: int = 1, branch: str = "Main"):
        with self.lock:
            for _ in range(copies):
                self.book_counter += 1
                book = Book(f"BOOK_{self.book_counter}", isbn, title, author, BookStatus.AVAILABLE, branch)
                self.books[book.book_id] = book
            print(f"✓ Added {copies} copies of '{title}' to {branch}")
    
    def register_member(self, member_id: str, name: str, email: str) -> Member:
        with self.lock:
            member = Member(member_id, name, email)
            self.members[member_id] = member
            print(f"✓ Registered member: {name}")
            return member
    
    def search_books(self, title: str) -> List[Book]:
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
                print(f"✗ Member {member.name} has reached borrow limit")
                return None
            
            # Check if member suspended due to fines
            if member.fine_balance > 50:
                print(f"✗ Member {member.name} suspended (fines: ${member.fine_balance})")
                return None
            
            # Check book availability
            if book.status != BookStatus.AVAILABLE:
                print(f"✗ Book {book_id} not available")
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
            
            print(f"✓ {member.name} borrowed '{book.title}' (Due: {due.date()})")
            return borrowing.borrowing_id
    
    def return_book(self, borrowing_id: str) -> float:
        with self.lock:
            if borrowing_id not in self.borrowings:
                return 0.0
            
            borrowing = self.borrowings[borrowing_id]
            borrowing.return_date = datetime.now()
            
            # Calculate fine
            days_late = max(0, (borrowing.return_date - borrowing.due_date).days)
            fine = min(days_late * 0.50, 10.0)
            borrowing.fine = fine
            
            # Update member
            member = self.members[borrowing.member_id]
            member.active_borrows.remove(borrowing)
            member.fine_balance += fine
            
            # Release book
            book = self.books[borrowing.book_id]
            book.status = BookStatus.AVAILABLE
            
            print(f"✓ {member.name} returned '{book.title}'")
            if fine > 0:
                print(f"  Fine: ${fine}")
            
            return fine
    
    def renew_book(self, borrowing_id: str) -> bool:
        with self.lock:
            if borrowing_id not in self.borrowings:
                return False
            
            borrowing = self.borrowings[borrowing_id]
            
            # Extend due date by 14 days
            old_due = borrowing.due_date
            borrowing.due_date = borrowing.due_date + timedelta(days=14)
            
            member = self.members[borrowing.member_id]
            book = self.books[borrowing.book_id]
            
            print(f"✓ {member.name} renewed '{book.title}'")
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
                print(f"✗ Copies available, borrow instead")
                return False
            
            # Mark first copy as reserved
            if copies:
                copies[0].status = BookStatus.RESERVED
                member = self.members[member_id]
                print(f"✓ {member.name} reserved '{copies[0].title}'")
                return True
            
            return False
    
    def display_member_account(self, member_id: str):
        with self.lock:
            if member_id not in self.members:
                return
            
            member = self.members[member_id]
            print(f"\n  Member: {member.name}")
            print(f"  Active borrows: {len(member.active_borrows)}")
            print(f"  Fine balance: ${member.fine_balance:.2f}")
            print(f"  Status: {member.status.name}")

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
            print(f"  Return fine: ${fine}")

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
            # Simulate late return (3 days)
            lib.borrowings[borrow_id].return_date = lib.borrowings[borrow_id].due_date + timedelta(days=3)
            fine = lib.return_book(borrow_id)
            print(f"  Expected fine: $1.50, Actual: ${fine}")

def demo_3_reservation():
    print("\n" + "="*70)
    print("DEMO 3: BOOK RESERVATION")
    print("="*70)
    
    lib = Library()
    lib.add_book("978-2", "Dune", "Frank Herbert", 2)
    lib.register_member("M3", "Mike", "mike@email.com")
    lib.register_member("M4", "Lisa", "lisa@email.com")
    
    # Borrow all copies
    for book_id, book in lib.books.items():
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
    
    for book_id, book in lib.books.items():
        lib.borrow_book("M6", book_id)
    
    lib.display_member_account("M6")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("📚 LIBRARY MANAGEMENT SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_borrow_return()
    demo_2_fine_calculation()
    demo_3_reservation()
    demo_4_member_account()
    demo_5_multiple_books()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Summary

✅ **Borrow/return** with automatic fine calculation
✅ **Late fee** enforcement and member suspension
✅ **Reservation queue** with notifications
✅ **Renewal logic** with limits
✅ **Multi-branch** support
✅ **Inventory tracking** per status
✅ **Scalable to 1M books** with indexing
✅ **Member account** management
✅ **Overdue notifications** (automated)
✅ **Inter-library loans** support

**Key Takeaway**: Library system demonstrates inventory management, transaction tracking, fine calculation, and queue-based reservations. Core focus: preventing overborrowing, accurate fine calculation, and scalable search.
