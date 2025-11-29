"""
Airline Management System - Interview Implementation
Complete working implementation with design patterns and demo scenarios
Timeline: 75 minutes | Scale: 500 concurrent users, 1-10k flights/day
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class SeatStatus(Enum):
    AVAILABLE = "available"
    HOLD = "hold"
    BOOKED = "booked"

class BookingStatus(Enum):
    HOLD = "hold"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SeatClass(Enum):
    ECONOMY = 1
    BUSINESS = 2

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Seat:
    """Represents a single seat on a flight"""
    def __init__(self, seat_id: str, seat_class: SeatClass):
        self.seat_id = seat_id
        self.seat_class = seat_class
        self.status = SeatStatus.AVAILABLE
        self.booked_by = None
    
    def is_available(self) -> bool:
        return self.status == SeatStatus.AVAILABLE
    
    def hold(self):
        if not self.is_available():
            raise ValueError(f"Seat {self.seat_id} not available")
        self.status = SeatStatus.HOLD
    
    def book(self):
        self.status = SeatStatus.BOOKED
    
    def release(self):
        self.status = SeatStatus.AVAILABLE
        self.booked_by = None

class Passenger:
    """Represents a passenger"""
    def __init__(self, passenger_id: str, name: str, email: str):
        self.passenger_id = passenger_id
        self.name = name
        self.email = email

class Flight:
    """Represents a flight with seat inventory"""
    def __init__(self, flight_id: str, origin: str, destination: str, 
                 departure: datetime, aircraft_type: str):
        self.flight_id = flight_id
        self.origin = origin
        self.destination = destination
        self.departure = departure
        self.aircraft_type = aircraft_type
        self.seats: Dict[str, Seat] = {}
    
    def add_seat(self, seat: Seat):
        self.seats[seat.seat_id] = seat
    
    def get_seat(self, seat_id: str) -> Optional[Seat]:
        return self.seats.get(seat_id)
    
    def available_seats_count(self) -> int:
        return sum(1 for s in self.seats.values() if s.is_available())

class Booking:
    """Represents a booking with lifecycle (HOLD → CONFIRMED or EXPIRED)"""
    def __init__(self, booking_id: str, passenger: Passenger, 
                 flight: Flight, seat: Seat, price: float):
        self.booking_id = booking_id
        self.passenger = passenger
        self.flight = flight
        self.seat = seat
        self.price = price
        self.status = BookingStatus.HOLD
        self.created_at = datetime.now()
        self.hold_until: Optional[datetime] = None
    
    def confirm(self):
        """Transition to CONFIRMED status"""
        self.status = BookingStatus.CONFIRMED
        self.seat.book()
    
    def cancel(self):
        """Transition to CANCELLED status"""
        self.status = BookingStatus.CANCELLED
        self.seat.release()
    
    def expire(self):
        """Transition to EXPIRED status if hold time exceeded"""
        if self.status == BookingStatus.HOLD:
            self.status = BookingStatus.EXPIRED
            self.seat.release()

# ============================================================================
# SECTION 3: PRICING STRATEGY (Strategy Pattern)
# ============================================================================

class PricingStrategy(ABC):
    """Abstract strategy for calculating seat price"""
    @abstractmethod
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        pass

class FixedPricing(PricingStrategy):
    """Base pricing: Economy $100, Business $200"""
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        return 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0

class DemandBasedPricing(PricingStrategy):
    """Dynamic pricing based on seat occupancy"""
    def calculate_price(self, flight: Flight, seat: Seat) -> float:
        base = 200.0 if seat.seat_class == SeatClass.BUSINESS else 100.0
        available = flight.available_seats_count()
        total = len(flight.seats)
        
        # Price increases as occupancy increases (up to 1.5x)
        occupancy_rate = 1.0 - (available / total)
        multiplier = 1.0 + (occupancy_rate * 0.5)
        
        return base * multiplier

# ============================================================================
# SECTION 4: OBSERVER PATTERN (Notifications)
# ============================================================================

class Observer(ABC):
    """Observer interface for booking events"""
    @abstractmethod
    def update(self, event: str, booking: 'Booking'):
        pass

class ConsoleObserver(Observer):
    """Console-based observer for demo purposes"""
    def update(self, event: str, booking: 'Booking'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event.upper():12} | "
              f"Passenger: {booking.passenger.name:15} | "
              f"Flight: {booking.flight.flight_id:8} | "
              f"Seat: {booking.seat.seat_id:4} | "
              f"Price: ${booking.price:.2f}")

# ============================================================================
# SECTION 5: AIRLINE SYSTEM (Singleton + Controller)
# ============================================================================

class AirlineSystem:
    """Singleton controller for airline operations"""
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
            self.flights: Dict[str, Flight] = {}
            self.passengers: Dict[str, Passenger] = {}
            self.bookings: Dict[str, Booking] = {}
            self.observers: List[Observer] = []
            self.pricing_strategy: PricingStrategy = FixedPricing()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'AirlineSystem':
        """Get singleton instance"""
        return AirlineSystem()
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Switch pricing algorithm dynamically"""
        self.pricing_strategy = strategy
    
    def add_observer(self, observer: Observer):
        """Subscribe to booking events"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, booking: 'Booking'):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(event, booking)
    
    def add_flight(self, flight: Flight):
        self.flights[flight.flight_id] = flight
    
    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.passenger_id] = passenger
    
    def hold_seat(self, passenger_id: str, flight_id: str, 
                  seat_id: str, hold_seconds: int = 300) -> Optional[Booking]:
        """Attempt to hold a seat for a passenger"""
        if flight_id not in self.flights:
            print(f"❌ Flight {flight_id} not found")
            return None
        
        flight = self.flights[flight_id]
        seat = flight.get_seat(seat_id)
        
        if not seat or not seat.is_available():
            print(f"❌ Seat {seat_id} not available")
            return None
        
        passenger = self.passengers.get(passenger_id)
        if not passenger:
            print(f"❌ Passenger {passenger_id} not found")
            return None
        
        # Hold the seat and create booking
        seat.hold()
        price = self.pricing_strategy.calculate_price(flight, seat)
        
        booking = Booking(f"BK{len(self.bookings)+1}", passenger, flight, seat, price)
        booking.hold_until = datetime.now() + timedelta(seconds=hold_seconds)
        
        self.bookings[booking.booking_id] = booking
        self.notify_observers("held", booking)
        return booking
    
    def confirm_booking(self, booking_id: str) -> bool:
        """Confirm a held booking"""
        booking = self.bookings.get(booking_id)
        if not booking:
            print(f"❌ Booking {booking_id} not found")
            return False
        
        if booking.status != BookingStatus.HOLD:
            print(f"❌ Booking not in HOLD status")
            return False
        
        if datetime.now() > booking.hold_until:
            booking.expire()
            self.notify_observers("expired", booking)
            print(f"❌ Hold expired for booking {booking_id}")
            return False
        
        booking.confirm()
        self.notify_observers("confirmed", booking)
        return True
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking and release the seat"""
        booking = self.bookings.get(booking_id)
        if not booking:
            return False
        
        booking.cancel()
        self.notify_observers("cancelled", booking)
        return True
    
    def check_and_expire_holds(self):
        """Expire all timed-out holds (background task)"""
        now = datetime.now()
        for booking in self.bookings.values():
            if (booking.status == BookingStatus.HOLD and 
                booking.hold_until and now > booking.hold_until):
                booking.expire()
                self.notify_observers("expired", booking)

# ============================================================================
# SECTION 6: DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    """Demo 1: System setup - Create flight, passengers, and register observer"""
    print("\n" + "="*70)
    print("DEMO 1: System Setup & Flight Creation")
    print("="*70)
    
    system = AirlineSystem.get_instance()
    system.observers.clear()
    system.add_observer(ConsoleObserver())
    
    # Create flight
    flight = Flight("AA101", "NYC", "LAX", 
                   datetime.now() + timedelta(hours=2), "Boeing 737")
    flight.add_seat(Seat("1A", SeatClass.BUSINESS))
    flight.add_seat(Seat("1B", SeatClass.ECONOMY))
    flight.add_seat(Seat("2A", SeatClass.ECONOMY))
    system.add_flight(flight)
    
    # Create passengers
    p1 = Passenger("P001", "John Doe", "john@example.com")
    p2 = Passenger("P002", "Jane Smith", "jane@example.com")
    system.register_passenger(p1)
    system.register_passenger(p2)
    
    print(f"✅ Flight {flight.flight_id} created with {len(flight.seats)} seats")
    print(f"✅ Registered {len(system.passengers)} passengers")
    return system, flight, p1, p2

def demo_2_hold_confirm():
    """Demo 2: Hold and confirm booking"""
    print("\n" + "="*70)
    print("DEMO 2: Hold & Confirm Booking")
    print("="*70)
    
    system, flight, p1, p2 = demo_1_setup()
    
    # Hold a seat
    print("\n→ Attempting to hold seat 1A for John Doe...")
    booking1 = system.hold_seat("P001", "AA101", "1A", hold_seconds=10)
    
    if booking1:
        print(f"✅ Booking created: {booking1.booking_id}")
        print("\n→ Confirming booking...")
        if system.confirm_booking(booking1.booking_id):
            print(f"✅ Booking {booking1.booking_id} confirmed")

def demo_3_dynamic_pricing():
    """Demo 3: Dynamic pricing strategy"""
    print("\n" + "="*70)
    print("DEMO 3: Dynamic Pricing - Demand-Based Strategy")
    print("="*70)
    
    system, flight, p1, p2 = demo_1_setup()
    
    print(f"\n→ Using Fixed Pricing (base)...")
    booking1 = system.hold_seat("P001", "AA101", "1A", hold_seconds=10)
    if booking1:
        print(f"  Seat 1A (Business) price: ${booking1.price:.2f}")
    
    print(f"\n→ Switching to Demand-Based Pricing...")
    system.set_pricing_strategy(DemandBasedPricing())
    booking2 = system.hold_seat("P002", "AA101", "1B", hold_seconds=10)
    if booking2:
        print(f"  Seat 1B (Economy) price: ${booking2.price:.2f}")
    print(f"✅ Pricing strategy switched successfully")

def demo_4_cancellation():
    """Demo 4: Cancellation and seat release"""
    print("\n" + "="*70)
    print("DEMO 4: Cancellation & Seat Release")
    print("="*70)
    
    system, flight, p1, p2 = demo_1_setup()
    
    print("\n→ Holding seat 1B for Jane Smith...")
    booking = system.hold_seat("P002", "AA101", "1B", hold_seconds=10)
    
    if booking:
        print(f"✅ Booking {booking.booking_id} held")
        print(f"  Seat 1B status: {flight.get_seat('1B').status.value}")
        
        print("\n→ Cancelling booking...")
        system.cancel_booking(booking.booking_id)
        print(f"✅ Booking {booking.booking_id} cancelled")
        print(f"  Seat 1B status: {flight.get_seat('1B').status.value}")

def demo_5_full_flow():
    """Demo 5: Complete booking flow with multiple bookings"""
    print("\n" + "="*70)
    print("DEMO 5: Complete Booking Flow - Multiple Bookings")
    print("="*70)
    
    system, flight, p1, p2 = demo_1_setup()
    
    print("\n→ Passenger 1: Hold Business seat 1A...")
    b1 = system.hold_seat("P001", "AA101", "1A", hold_seconds=10)
    if b1:
        system.confirm_booking(b1.booking_id)
    
    print("\n→ Passenger 2: Hold Economy seat 1B...")
    system.set_pricing_strategy(DemandBasedPricing())
    b2 = system.hold_seat("P002", "AA101", "1B", hold_seconds=10)
    if b2:
        system.confirm_booking(b2.booking_id)
    
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total bookings: {len(system.bookings)}")
    print(f"Confirmed bookings: {sum(1 for b in system.bookings.values() if b.status == BookingStatus.CONFIRMED)}")
    print(f"Available seats: {flight.available_seats_count()}")
    print(f"Booked seats: {sum(1 for s in flight.seats.values() if s.status == SeatStatus.BOOKED)}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AIRLINE MANAGEMENT SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State")
    print("="*70)
    
    try:
        demo_1_setup()
        demo_2_hold_confirm()
        demo_3_dynamic_pricing()
        demo_4_cancellation()
        demo_5_full_flow()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nKey Takeaways:")
        print("  • Singleton: Single AirlineSystem instance for consistency")
        print("  • Strategy: Pluggable pricing algorithms (Fixed vs DemandBased)")
        print("  • Observer: Real-time booking event notifications")
        print("  • State: Clear booking lifecycle (HOLD → CONFIRMED or EXPIRED)")
        print("\nFor detailed implementation, see 75_MINUTE_GUIDE.md")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
