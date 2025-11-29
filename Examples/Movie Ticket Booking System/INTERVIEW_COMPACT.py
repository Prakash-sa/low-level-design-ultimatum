"""
Movie Ticket Booking System - Interview Implementation
Complete working implementation with design patterns and demo scenarios
Timeline: 75 minutes | Scale: 1,000 concurrent users, 100+ theaters, 10k+ bookings/day
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class SeatType(Enum):
    REGULAR = 1
    PREMIUM = 2
    VIP = 3

class SeatStatus(Enum):
    AVAILABLE = "available"
    LOCKED = "locked"
    BOOKED = "booked"

class BookingStatus(Enum):
    PENDING = "pending"
    LOCKED = "locked"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    UPI = "upi"
    WALLET = "wallet"

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Movie:
    """Represents a movie"""
    def __init__(self, movie_id: str, title: str, duration: int, 
                 genre: List[str], language: str, rating: str):
        self.movie_id = movie_id
        self.title = title
        self.duration = duration  # minutes
        self.genre = genre
        self.language = language
        self.rating = rating
        self.created_at = datetime.now()
    
    def get_duration_formatted(self) -> str:
        hours = self.duration // 60
        minutes = self.duration % 60
        return f"{hours}h {minutes}m"

class Seat:
    """Represents a single seat in a hall"""
    def __init__(self, seat_id: str, row: str, number: int, seat_type: SeatType):
        self.seat_id = seat_id
        self.row = row
        self.number = number
        self.seat_type = seat_type
        self.status = SeatStatus.AVAILABLE
        self.locked_until: Optional[datetime] = None
        self.locked_by: Optional[str] = None  # user_id
        self.price_multiplier = self._get_multiplier()
    
    def _get_multiplier(self) -> float:
        if self.seat_type == SeatType.REGULAR:
            return 1.0
        elif self.seat_type == SeatType.PREMIUM:
            return 1.3
        else:  # VIP
            return 1.5
    
    def is_available(self) -> bool:
        if self.status == SeatStatus.AVAILABLE:
            return True
        if self.status == SeatStatus.LOCKED:
            if datetime.now() > self.locked_until:
                self.unlock()
                return True
        return False
    
    def lock(self, user_id: str, duration_minutes: int = 10):
        if not self.is_available():
            raise ValueError(f"Seat {self.seat_id} not available")
        self.status = SeatStatus.LOCKED
        self.locked_by = user_id
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
    
    def unlock(self):
        self.status = SeatStatus.AVAILABLE
        self.locked_by = None
        self.locked_until = None
    
    def book(self):
        self.status = SeatStatus.BOOKED

class Hall:
    """Represents a screening hall in a theater"""
    def __init__(self, hall_id: str, hall_number: str, capacity: int):
        self.hall_id = hall_id
        self.hall_number = hall_number
        self.capacity = capacity
        self.seat_layout: List[List[Seat]] = []
    
    def generate_seat_layout(self, rows: int, cols: int):
        """Generate seat layout with mixed types"""
        row_letters = [chr(65 + i) for i in range(rows)]  # A, B, C...
        
        for idx, row in enumerate(row_letters):
            row_seats = []
            for num in range(1, cols + 1):
                # First 2 rows are VIP, next 2 are Premium, rest Regular
                if idx < 2:
                    seat_type = SeatType.VIP
                elif idx < 4:
                    seat_type = SeatType.PREMIUM
                else:
                    seat_type = SeatType.REGULAR
                
                seat_id = f"{row}{num}"
                seat = Seat(seat_id, row, num, seat_type)
                row_seats.append(seat)
            self.seat_layout.append(row_seats)
    
    def get_seat(self, seat_id: str) -> Optional[Seat]:
        """Get seat by ID like 'A1', 'B5'"""
        for row in self.seat_layout:
            for seat in row:
                if seat.seat_id == seat_id:
                    return seat
        return None
    
    def get_available_seats(self) -> List[Seat]:
        """Get all available seats"""
        available = []
        for row in self.seat_layout:
            for seat in row:
                if seat.is_available():
                    available.append(seat)
        return available

class Theater:
    """Represents a cinema theater"""
    def __init__(self, theater_id: str, name: str, location: str, city: str):
        self.theater_id = theater_id
        self.name = name
        self.location = location
        self.city = city
        self.halls: Dict[str, Hall] = {}
    
    def add_hall(self, hall: Hall):
        self.halls[hall.hall_id] = hall

class Show:
    """Represents a movie screening"""
    def __init__(self, show_id: str, movie: Movie, hall: Hall, 
                 start_time: datetime, base_price: float):
        self.show_id = show_id
        self.movie = movie
        self.hall = hall
        self.start_time = start_time
        self.end_time = start_time + timedelta(minutes=movie.duration)
        self.base_price = base_price
    
    def get_available_seats(self) -> List[Seat]:
        return self.hall.get_available_seats()

class User:
    """Represents a customer"""
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.bookings: List['Booking'] = []

class Payment:
    """Represents a payment transaction"""
    def __init__(self, payment_id: str, amount: float, method: PaymentMethod):
        self.payment_id = payment_id
        self.amount = amount
        self.payment_method = method
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
    
    def process(self) -> bool:
        """Simulate payment processing"""
        # In real system, integrate with payment gateway
        self.status = PaymentStatus.SUCCESS
        return True

class Booking:
    """Represents a booking"""
    def __init__(self, booking_id: str, user: User, show: Show, seats: List[Seat]):
        self.booking_id = booking_id
        self.user = user
        self.show = show
        self.seats = seats
        self.status = BookingStatus.PENDING
        self.total_amount = 0.0
        self.payment: Optional[Payment] = None
        self.booking_time = datetime.now()
    
    def calculate_total(self, pricing_strategy: 'PricingStrategy') -> float:
        """Calculate total price using pricing strategy"""
        total = 0.0
        for seat in self.seats:
            price = pricing_strategy.calculate_price(self.show.base_price, seat)
            total += price
        return total
    
    def confirm(self):
        """Confirm booking after payment"""
        self.status = BookingStatus.CONFIRMED
        for seat in self.seats:
            seat.book()
    
    def cancel(self):
        """Cancel booking and release seats"""
        self.status = BookingStatus.CANCELLED
        for seat in self.seats:
            seat.unlock()

# ============================================================================
# SECTION 3: PRICING STRATEGY (Strategy Pattern)
# ============================================================================

class PricingStrategy(ABC):
    """Abstract strategy for calculating seat price"""
    @abstractmethod
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        pass

class RegularPricing(PricingStrategy):
    """Regular weekday pricing"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        return base_price * seat.price_multiplier

class WeekendPricing(PricingStrategy):
    """Weekend pricing with 50% markup"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        base = base_price * seat.price_multiplier
        return base * 1.5  # 50% weekend surcharge

class HolidayPricing(PricingStrategy):
    """Holiday pricing with 100% markup"""
    def calculate_price(self, base_price: float, seat: Seat) -> float:
        base = base_price * seat.price_multiplier
        return base * 2.0  # 100% holiday surcharge

# ============================================================================
# SECTION 4: OBSERVER PATTERN (Notifications)
# ============================================================================

class BookingObserver(ABC):
    """Observer interface for booking events"""
    @abstractmethod
    def update(self, event: str, booking: Booking):
        pass

class ConsoleObserver(BookingObserver):
    """Console-based observer for demo purposes"""
    def update(self, event: str, booking: Booking):
        timestamp = datetime.now().strftime("%H:%M:%S")
        seats_str = ", ".join([s.seat_id for s in booking.seats])
        print(f"[{timestamp}] {event.upper():20} | "
              f"User: {booking.user.name:15} | "
              f"Show: {booking.show.show_id:8} | "
              f"Seats: {seats_str:15} | "
              f"Total: ${booking.total_amount:.2f}")

class EmailNotifier(BookingObserver):
    """Email notification observer"""
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"📧 Email sent to {booking.user.email}: Booking confirmed!")
        elif event == "booking_cancelled":
            print(f"📧 Email sent to {booking.user.email}: Booking cancelled.")

class SMSNotifier(BookingObserver):
    """SMS notification observer"""
    def update(self, event: str, booking: Booking):
        if event == "booking_confirmed":
            print(f"📱 SMS sent to {booking.user.phone}: Your booking is confirmed!")

# ============================================================================
# SECTION 5: BOOKING SYSTEM (Singleton + Controller)
# ============================================================================

class BookingSystem:
    """Singleton controller for movie ticket booking"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.movies: Dict[str, Movie] = {}
            self.theaters: Dict[str, Theater] = {}
            self.shows: Dict[str, Show] = {}
            self.bookings: Dict[str, Booking] = {}
            self.users: Dict[str, User] = {}
            self.observers: List[BookingObserver] = []
            self.pricing_strategy: PricingStrategy = RegularPricing()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'BookingSystem':
        """Get singleton instance"""
        return BookingSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Switch pricing algorithm dynamically"""
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: BookingObserver):
        """Subscribe to booking events"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: Booking):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(event, booking)
    
    def add_movie(self, movie: Movie):
        self.movies[movie.movie_id] = movie
    
    def add_theater(self, theater: Theater):
        self.theaters[theater.theater_id] = theater
    
    def add_show(self, show: Show):
        self.shows[show.show_id] = show
    
    def register_user(self, user: User):
        self.users[user.user_id] = user
    
    def search_movies(self, query: str = "", genre: str = "") -> List[Movie]:
        """Search movies by title or genre"""
        results = []
        for movie in self.movies.values():
            if query and query.lower() not in movie.title.lower():
                continue
            if genre and genre not in movie.genre:
                continue
            results.append(movie)
        return results
    
    def get_shows_by_movie(self, movie_id: str) -> List[Show]:
        """Get all shows for a movie"""
        return [show for show in self.shows.values() 
                if show.movie.movie_id == movie_id]
    
    def lock_seats(self, user_id: str, show_id: str, 
                   seat_ids: List[str]) -> Optional[Booking]:
        """Lock seats for a user"""
        if show_id not in self.shows:
            print(f"❌ Show {show_id} not found")
            return None
        
        show = self.shows[show_id]
        user = self.users.get(user_id)
        
        if not user:
            print(f"❌ User {user_id} not found")
            return None
        
        # Get seats and check availability
        seats = []
        for seat_id in seat_ids:
            seat = show.hall.get_seat(seat_id)
            if not seat or not seat.is_available():
                print(f"❌ Seat {seat_id} not available")
                return None
            seats.append(seat)
        
        # Lock all seats
        for seat in seats:
            seat.lock(user_id)
        
        # Create booking
        booking_id = f"BK{len(self.bookings)+1:04d}"
        booking = Booking(booking_id, user, show, seats)
        booking.status = BookingStatus.LOCKED
        booking.total_amount = booking.calculate_total(self.pricing_strategy)
        
        self.bookings[booking_id] = booking
        self.notify_observers("seats_locked", booking)
        
        return booking
    
    def confirm_booking(self, booking_id: str, 
                       payment_method: PaymentMethod) -> bool:
        """Confirm booking with payment"""
        booking = self.bookings.get(booking_id)
        if not booking:
            print(f"❌ Booking {booking_id} not found")
            return False
        
        if booking.status != BookingStatus.LOCKED:
            print(f"❌ Booking not in LOCKED status")
            return False
        
        # Process payment
        payment = Payment(f"PAY{len(self.bookings)}", 
                         booking.total_amount, payment_method)
        if payment.process():
            booking.payment = payment
            booking.confirm()
            self.notify_observers("booking_confirmed", booking)
            return True
        
        return False
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return False
        
        booking.cancel()
        self.notify_observers("booking_cancelled", booking)
        return True

# ============================================================================
# SECTION 6: DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    """Demo 1: System setup - Create movies, theaters, shows"""
    print("\n" + "="*70)
    print("DEMO 1: Setup & Movie/Theater Creation")
    print("="*70)
    
    system = BookingSystem.get_instance()
    system.observers.clear()
    system.add_observer(ConsoleObserver())
    
    # Create movies
    movie1 = Movie("MOV001", "Inception", 148, 
                   ["Sci-Fi", "Thriller"], "English", "PG-13")
    movie2 = Movie("MOV002", "The Dark Knight", 152, 
                   ["Action", "Crime"], "English", "PG-13")
    system.add_movie(movie1)
    system.add_movie(movie2)
    
    # Create theater with hall
    theater = Theater("THR001", "PVR Cinemas", "Downtown", "New York")
    hall = Hall("HALL001", "Hall 1", 60)
    hall.generate_seat_layout(6, 10)  # 6 rows x 10 seats = 60 total
    theater.add_hall(hall)
    system.add_theater(theater)
    
    # Create shows
    show1 = Show("SHW001", movie1, hall, 
                datetime.now() + timedelta(hours=2), 15.0)
    show2 = Show("SHW002", movie2, hall, 
                datetime.now() + timedelta(hours=5), 15.0)
    system.add_show(show1)
    system.add_show(show2)
    
    # Register users
    user1 = User("USR001", "Alice Johnson", "alice@example.com", "+1234567890")
    user2 = User("USR002", "Bob Smith", "bob@example.com", "+1987654321")
    system.register_user(user1)
    system.register_user(user2)
    
    print(f"✅ Created {len(system.movies)} movies")
    print(f"✅ Created {len(system.theaters)} theaters with {len(hall.seat_layout)} rows")
    print(f"✅ Created {len(system.shows)} shows")
    print(f"✅ Registered {len(system.users)} users")
    
    return system, movie1, show1, hall, user1, user2

def demo_2_search_browse():
    """Demo 2: Search and browse movies"""
    print("\n" + "="*70)
    print("DEMO 2: Search & Browse Movies")
    print("="*70)
    
    system, movie1, show1, hall, user1, user2 = demo_1_setup()
    
    # Search movies
    print("\n→ Searching for 'Inception'...")
    results = system.search_movies(query="Inception")
    for movie in results:
        print(f"  Found: {movie.title} ({movie.get_duration_formatted()}) - {movie.genre}")
    
    # Get shows for movie
    print(f"\n→ Getting shows for '{movie1.title}'...")
    shows = system.get_shows_by_movie(movie1.movie_id)
    for show in shows:
        available = len(show.get_available_seats())
        print(f"  Show {show.show_id} at {show.start_time.strftime('%I:%M %p')} - "
              f"{available} seats available")
    
    print(f"✅ Search completed successfully")

def demo_3_seat_selection():
    """Demo 3: Seat selection and locking"""
    print("\n" + "="*70)
    print("DEMO 3: Seat Selection & Locking")
    print("="*70)
    
    system, movie1, show1, hall, user1, user2 = demo_1_setup()
    
    # User 1 locks seats
    print("\n→ User 1 (Alice) selecting seats A1, A2 (VIP)...")
    booking1 = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking1:
        print(f"✅ Seats locked - Total: ${booking1.total_amount:.2f}")
    
    # User 2 tries same seats
    print("\n→ User 2 (Bob) tries to select same seats...")
    booking2 = system.lock_seats("USR002", "SHW001", ["A1", "A2"])
    if not booking2:
        print("✅ Correctly blocked - seats already locked")
    
    # User 2 selects different seats
    print("\n→ User 2 (Bob) selecting different seats C5, C6 (Premium)...")
    booking2 = system.lock_seats("USR002", "SHW001", ["C5", "C6"])
    if booking2:
        print(f"✅ Seats locked - Total: ${booking2.total_amount:.2f}")

def demo_4_pricing_strategies():
    """Demo 4: Pricing strategies"""
    print("\n" + "="*70)
    print("DEMO 4: Pricing Strategies (Regular/Weekend/Holiday)")
    print("="*70)
    
    system, movie1, show1, hall, user1, user2 = demo_1_setup()
    
    # Regular pricing
    print("\n→ Using Regular Pricing (weekday)...")
    system.set_pricing_strategy(RegularPricing())
    booking = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking:
        print(f"  VIP seats (A1, A2): ${booking.total_amount:.2f}")
    
    # Weekend pricing
    print("\n→ Switching to Weekend Pricing (+50%)...")
    system.set_pricing_strategy(WeekendPricing())
    # Unlock previous seats
    hall.get_seat("A1").unlock()
    hall.get_seat("A2").unlock()
    booking = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking:
        print(f"  VIP seats (A1, A2): ${booking.total_amount:.2f}")
    
    # Holiday pricing
    print("\n→ Switching to Holiday Pricing (+100%)...")
    system.set_pricing_strategy(HolidayPricing())
    hall.get_seat("A1").unlock()
    hall.get_seat("A2").unlock()
    booking = system.lock_seats("USR001", "SHW001", ["A1", "A2"])
    if booking:
        print(f"  VIP seats (A1, A2): ${booking.total_amount:.2f}")
    
    print("✅ Pricing strategy demonstration completed")

def demo_5_full_flow():
    """Demo 5: Complete booking flow"""
    print("\n" + "="*70)
    print("DEMO 5: Complete Booking Flow - Browse → Select → Pay → Confirm")
    print("="*70)
    
    system, movie1, show1, hall, user1, user2 = demo_1_setup()
    
    # Add email and SMS observers
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    # Reset to regular pricing
    system.set_pricing_strategy(RegularPricing())
    
    # User 1: Full booking flow
    print("\n→ User 1 (Alice) booking flow...")
    print("  1. Searching movies...")
    movies = system.search_movies(query="Inception")
    
    print("  2. Selecting show...")
    shows = system.get_shows_by_movie(movies[0].movie_id)
    
    print("  3. Locking seats...")
    booking = system.lock_seats("USR001", shows[0].show_id, ["A1", "A2"])
    
    print("  4. Processing payment...")
    if booking:
        success = system.confirm_booking(booking.booking_id, PaymentMethod.CREDIT_CARD)
        if success:
            print(f"✅ Booking {booking.booking_id} confirmed!")
    
    # User 2: Another booking
    print("\n→ User 2 (Bob) booking flow...")
    booking2 = system.lock_seats("USR002", "SHW001", ["E5", "E6", "E7"])
    if booking2:
        system.confirm_booking(booking2.booking_id, PaymentMethod.UPI)
    
    # Summary
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total bookings: {len(system.bookings)}")
    confirmed = sum(1 for b in system.bookings.values() 
                   if b.status == BookingStatus.CONFIRMED)
    print(f"Confirmed bookings: {confirmed}")
    available = len(show1.get_available_seats())
    print(f"Available seats in Show 1: {available}")
    booked = sum(1 for row in hall.seat_layout for s in row 
                if s.status == SeatStatus.BOOKED)
    print(f"Booked seats: {booked}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MOVIE TICKET BOOKING SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory")
    print("="*70)
    
    try:
        demo_1_setup()
        demo_2_search_browse()
        demo_3_seat_selection()
        demo_4_pricing_strategies()
        demo_5_full_flow()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nKey Takeaways:")
        print("  • Singleton: Single BookingSystem instance for consistency")
        print("  • Strategy: Pluggable pricing (Regular/Weekend/Holiday)")
        print("  • Observer: Real-time notifications (Email/SMS/Console)")
        print("  • State: Clear booking lifecycle (PENDING → LOCKED → CONFIRMED)")
        print("  • Seat Locking: 10-minute timeout prevents double-booking")
        print("\nFor detailed implementation, see 75_MINUTE_GUIDE.md")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
