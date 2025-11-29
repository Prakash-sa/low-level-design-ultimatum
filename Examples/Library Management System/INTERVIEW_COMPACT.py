"""
Library Management System - 75 Minute Interview Implementation
Single-file, ready-to-run, copy-paste friendly
~480 lines of production-ready code
"""

from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from abc import ABC, abstractmethod


# ============================================================================
# SECTION 1: ENUMERATIONS & BASIC TYPES
# ============================================================================

class BookStatus(Enum):
    AVAILABLE = auto()
    CHECKED_OUT = auto()
    RESERVED = auto()

class CheckoutStatus(Enum):
    ACTIVE = auto()
    OVERDUE = auto()
    RETURNED = auto()

class MemberType(Enum):
    STUDENT = 1
    FACULTY = 2
    PREMIUM = 3


# ============================================================================
# SECTION 2: BOOK CLASS
# ============================================================================

class Book:
    """Book with inventory and reservation management"""
    def __init__(self, isbn: str, title: str, author: str, total_copies: int):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.checked_out = 0
        self.reservations: List[str] = []
    
    def is_available(self) -> bool:
        return self.available_copies > 0
    
    def checkout(self) -> bool:
        if self.available_copies > 0:
            self.available_copies -= 1
            self.checked_out += 1
            return True
        return False
    
    def return_book(self) -> bool:
        if self.checked_out > 0:
            self.available_copies += 1
            self.checked_out -= 1
            return True
        return False
    
    def reserve(self, member_id: str):
        if member_id not in self.reservations:
            self.reservations.append(member_id)
            return True
        return False
    
    def __repr__(self):
        return f"{self.title} ({self.author}) - Available: {self.available_copies}/{self.total_copies}"


# ============================================================================
# SECTION 3: MEMBER CLASSES
# ============================================================================

class Member(ABC):
    """Base member class with checkout policies"""
    def __init__(self, member_id: str, name: str, email: str):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.member_type = None
        self.checkouts: List['Checkout'] = []
        self.fine_rate = 0.50
    
    @abstractmethod
    def get_checkout_limit(self) -> int:
        pass
    
    @abstractmethod
    def get_checkout_days(self) -> int:
        pass

class StudentMember(Member):
    def __init__(self, member_id: str, name: str, email: str):
        super().__init__(member_id, name, email)
        self.member_type = MemberType.STUDENT
        self.fine_rate = 0.50
    
    def get_checkout_limit(self) -> int:
        return 5
    
    def get_checkout_days(self) -> int:
        return 14

class FacultyMember(Member):
    def __init__(self, member_id: str, name: str, email: str):
        super().__init__(member_id, name, email)
        self.member_type = MemberType.FACULTY
        self.fine_rate = 0.50
    
    def get_checkout_limit(self) -> int:
        return 10
    
    def get_checkout_days(self) -> int:
        return 21

class PremiumMember(Member):
    def __init__(self, member_id: str, name: str, email: str):
        super().__init__(member_id, name, email)
        self.member_type = MemberType.PREMIUM
        self.fine_rate = 0.25
    
    def get_checkout_limit(self) -> int:
        return 15
    
    def get_checkout_days(self) -> int:
        return 30


# ============================================================================
# SECTION 4: CHECKOUT CLASS
# ============================================================================

class Checkout:
    """Tracks book checkouts with due dates and fines"""
    _id_counter = 1000
    
    def __init__(self, member: Member, book: Book):
        Checkout._id_counter += 1
        self.checkout_id = f"CHK-{Checkout._id_counter}"
        self.member = member
        self.book = book
        self.checkout_date = datetime.now()
        self.due_date = self.checkout_date + timedelta(days=member.get_checkout_days())
        self.return_date: Optional[datetime] = None
        self.fine_amount = 0.0
        self.status = CheckoutStatus.ACTIVE
    
    def return_checkout(self) -> float:
        self.return_date = datetime.now()
        days_overdue = (self.return_date - self.due_date).days
        
        if days_overdue > 0:
            self.fine_amount = days_overdue * self.member.fine_rate
            self.status = CheckoutStatus.OVERDUE
        else:
            self.status = CheckoutStatus.RETURNED
        
        return self.fine_amount
    
    def __repr__(self):
        return f"{self.checkout_id}: {self.book.title} (Due: {self.due_date.strftime('%Y-%m-%d')})"


# ============================================================================
# SECTION 5: SEARCH & NOTIFICATION STRATEGIES
# ============================================================================

class SearchStrategy(ABC):
    """Strategy pattern for book search"""
    @abstractmethod
    def search(self, books: Dict[str, Book], query: str) -> List[Book]:
        pass

class ISBNSearchStrategy(SearchStrategy):
    def search(self, books: Dict[str, Book], isbn: str) -> List[Book]:
        if isbn in books:
            return [books[isbn]]
        return []

class TitleSearchStrategy(SearchStrategy):
    def search(self, books: Dict[str, Book], title: str) -> List[Book]:
        query = title.lower()
        return [b for b in books.values() if query in b.title.lower()]

class AuthorSearchStrategy(SearchStrategy):
    def search(self, books: Dict[str, Book], author: str) -> List[Book]:
        query = author.lower()
        return [b for b in books.values() if query in b.author.lower()]

# Observer Pattern for Notifications
class Observer(ABC):
    """Observer interface for notifications"""
    @abstractmethod
    def notify(self, message: str):
        pass

class EmailNotifier(Observer):
    def notify(self, message: str):
        print(f"  📧 Email: {message}")

class SMSNotifier(Observer):
    def notify(self, message: str):
        print(f"  📱 SMS: {message}")


# ============================================================================
# SECTION 6: LIBRARY SYSTEM (SINGLETON)
# ============================================================================

class LibrarySystem:
    """Main library system controller - Singleton pattern"""
    _instance = None
    
    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}
        self.checkouts: Dict[str, Checkout] = {}
        self.search_strategy: SearchStrategy = ISBNSearchStrategy()
        self.observers: List[Observer] = []
        self._member_id_counter = 1000
    
    @classmethod
    def get_instance(cls):
        """Singleton getter"""
        if cls._instance is None:
            cls._instance = LibrarySystem()
        return cls._instance
    
    def add_book(self, book: Book) -> bool:
        """Add a new book to library"""
        if book.isbn not in self.books:
            self.books[book.isbn] = book
            print(f"  ✅ Added: {book}")
            return True
        return False
    
    def register_member(self, name: str, email: str, member_type: str) -> Optional[Member]:
        """Register a new member"""
        self._member_id_counter += 1
        member_id = f"MEM-{self._member_id_counter}"
        
        if member_type == "student":
            member = StudentMember(member_id, name, email)
        elif member_type == "faculty":
            member = FacultyMember(member_id, name, email)
        elif member_type == "premium":
            member = PremiumMember(member_id, name, email)
        else:
            return None
        
        self.members[member_id] = member
        print(f"  ✅ Registered {member_type}: {name} ({member_id})")
        self.notify_all(f"Welcome {name}!")
        return member
    
    def search_books(self, query: str) -> List[Book]:
        """Search books using current strategy"""
        return self.search_strategy.search(self.books, query)
    
    def set_search_strategy(self, strategy: SearchStrategy):
        """Change search strategy"""
        self.search_strategy = strategy
    
    def checkout_book(self, member_id: str, isbn: str) -> Optional[Checkout]:
        """Issue a book to member"""
        if member_id not in self.members or isbn not in self.books:
            return None
        
        member = self.members[member_id]
        book = self.books[isbn]
        
        # Check limits
        if len(member.checkouts) >= member.get_checkout_limit():
            print(f"  ❌ {member.name} reached checkout limit")
            return None
        
        if not book.checkout():
            print(f"  ❌ Book not available")
            return None
        
        checkout = Checkout(member, book)
        member.checkouts.append(checkout)
        self.checkouts[checkout.checkout_id] = checkout
        
        print(f"  ✅ {member.name} checked out: {book.title}")
        self.notify_all(f"Book checked out. Due: {checkout.due_date.strftime('%Y-%m-%d')}")
        return checkout
    
    def return_book(self, member_id: str, isbn: str) -> float:
        """Process book return and calculate fine"""
        if member_id not in self.members:
            return -1
        
        member = self.members[member_id]
        book = self.books.get(isbn)
        
        # Find active checkout
        checkout = None
        for c in member.checkouts:
            if c.book.isbn == isbn and c.status == CheckoutStatus.ACTIVE:
                checkout = c
                break
        
        if not checkout:
            print(f"  ❌ No active checkout found")
            return -1
        
        fine = checkout.return_checkout()
        book.return_book()
        
        print(f"  ✅ {member.name} returned: {book.title}")
        if fine > 0:
            print(f"     Fine: ${fine:.2f}")
        self.notify_all(f"Book returned. Fine: ${fine:.2f}")
        return fine
    
    def reserve_book(self, member_id: str, isbn: str) -> bool:
        """Reserve a book for member"""
        if member_id not in self.members or isbn not in self.books:
            return False
        
        member = self.members[member_id]
        book = self.books[isbn]
        
        if book.reserve(member_id):
            print(f"  ✅ {member.name} reserved: {book.title}")
            return True
        return False
    
    def add_observer(self, observer: Observer):
        """Add notification observer"""
        self.observers.append(observer)
    
    def notify_all(self, message: str):
        """Notify all observers"""
        for observer in self.observers:
            observer.notify(message)
    
    def get_statistics(self) -> Dict:
        """Get library statistics"""
        total_books = sum(b.total_copies for b in self.books.values())
        total_checkouts = len([c for c in self.checkouts.values() if c.status == CheckoutStatus.ACTIVE])
        
        return {
            "total_unique_titles": len(self.books),
            "total_copies": total_books,
            "active_checkouts": total_checkouts,
            "total_members": len(self.members),
        }
    
    def print_status(self):
        """Print library status"""
        stats = self.get_statistics()
        print("\n  📚 Library Status:")
        print(f"     Titles: {stats['total_unique_titles']} | "
              f"Copies: {stats['total_copies']} | "
              f"Checkouts: {stats['active_checkouts']} | "
              f"Members: {stats['total_members']}")


# ============================================================================
# SECTION 7: DEMO & TESTING
# ============================================================================

def demo_1_add_books():
    """Demo 1: Add books to library"""
    print("\n" + "="*70)
    print("DEMO 1: Adding Books")
    print("="*70)
    
    lib = LibrarySystem.get_instance()
    books_data = [
        ("1001", "Python Basics", "John Doe", 5),
        ("1002", "Data Science", "Jane Smith", 3),
        ("1003", "Web Dev", "Bob Johnson", 4),
    ]
    for isbn, title, author, copies in books_data:
        book = Book(isbn, title, author, copies)
        lib.add_book(book)

def demo_2_register_members():
    """Demo 2: Register members"""
    print("\n" + "="*70)
    print("DEMO 2: Registering Members")
    print("="*70)
    
    lib = LibrarySystem.get_instance()
    lib.register_member("Alice", "alice@uni.edu", "student")
    lib.register_member("Prof. Bob", "bob@uni.edu", "faculty")
    lib.register_member("Charlie", "charlie@user.com", "premium")

def demo_3_checkout_books():
    """Demo 3: Checkout books"""
    print("\n" + "="*70)
    print("DEMO 3: Checking Out Books")
    print("="*70)
    
    lib = LibrarySystem.get_instance()
    members = list(lib.members.values())
    
    if len(members) >= 2:
        lib.checkout_book(members[0].member_id, "1001")
        lib.checkout_book(members[1].member_id, "1002")
    
    lib.print_status()

def demo_4_search_books():
    """Demo 4: Search books with different strategies"""
    print("\n" + "="*70)
    print("DEMO 4: Searching Books")
    print("="*70)
    
    lib = LibrarySystem.get_instance()
    
    # Search by ISBN
    lib.set_search_strategy(ISBNSearchStrategy())
    results = lib.search_books("1001")
    print(f"  ISBN search found: {len(results)} book(s)")
    
    # Search by title
    lib.set_search_strategy(TitleSearchStrategy())
    results = lib.search_books("Python")
    print(f"  Title search found: {len(results)} book(s)")
    for book in results:
        print(f"    - {book}")

def demo_5_return_and_fine():
    """Demo 5: Return books and calculate fines"""
    print("\n" + "="*70)
    print("DEMO 5: Returning Books & Fine Calculation")
    print("="*70)
    
    lib = LibrarySystem.get_instance()
    members = list(lib.members.values())
    
    if len(members) >= 1:
        member = members[0]
        if member.checkouts:
            book_isbn = member.checkouts[0].book.isbn
            fine = lib.return_book(member.member_id, book_isbn)
            print(f"  Total fine: ${fine:.2f}")

def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("LIBRARY MANAGEMENT SYSTEM - 75 MINUTE INTERVIEW")
    print("="*70)
    
    # Initialize
    lib = LibrarySystem.get_instance()
    lib.add_observer(EmailNotifier())
    lib.add_observer(SMSNotifier())
    
    # Run demos
    demo_1_add_books()
    demo_2_register_members()
    demo_3_checkout_books()
    demo_4_search_books()
    demo_5_return_and_fine()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
