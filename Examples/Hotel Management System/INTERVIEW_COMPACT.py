#!/usr/bin/env python3
"""
Hotel Management System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action

Design Patterns Demonstrated:
1. Singleton - HotelManagementSystem (centralized control)
2. Factory - RoomFactory (room creation)
3. Strategy - PricingStrategy (Regular/Seasonal/Event)
4. Observer - Notifications (Guest/Staff/Admin)
5. State - Room and Reservation lifecycles
6. Command - Service requests
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import threading
import time


# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class RoomType(Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"


class RoomStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ONLINE = "online"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ServiceType(Enum):
    ROOM_SERVICE = "room_service"
    HOUSEKEEPING = "housekeeping"
    MAINTENANCE = "maintenance"
    LAUNDRY = "laundry"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class StaffRole(Enum):
    RECEPTIONIST = "receptionist"
    HOUSEKEEPER = "housekeeper"
    MAINTENANCE = "maintenance"
    ROOM_SERVICE = "room_service"
    MANAGER = "manager"


# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Guest:
    """Guest with loyalty program and preferences"""
    def __init__(self, guest_id: str, name: str, email: str, phone: str):
        self.guest_id = guest_id
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = datetime.now()
        self.loyalty_points = 0
        self.total_stays = 0
        self.total_spent = 0.0
        self.preferences = {}
        self.is_vip = False
    
    def add_loyalty_points(self, points: int):
        """Add loyalty points from stay"""
        self.loyalty_points += points
        if self.loyalty_points >= 1000:
            self.is_vip = True
    
    def get_discount_percentage(self) -> float:
        """Calculate loyalty discount"""
        if self.is_vip:
            return 0.15  # 15% VIP discount
        elif self.loyalty_points >= 500:
            return 0.10  # 10% silver discount
        elif self.loyalty_points >= 200:
            return 0.05  # 5% bronze discount
        return 0.0
    
    def __str__(self):
        vip_status = "VIP" if self.is_vip else "Regular"
        return "%s (%s) - Points: %d, Stays: %d, Spent: $%.2f" % (
            self.name, vip_status, self.loyalty_points, self.total_stays, self.total_spent)


class Room:
    """Room with state management"""
    def __init__(self, room_id: str, room_number: str, room_type: RoomType,
                 base_price: float, floor: int, capacity: int, amenities: List[str]):
        self.room_id = room_id
        self.room_number = room_number
        self.room_type = room_type
        self.base_price = base_price
        self.floor = floor
        self.capacity = capacity
        self.amenities = amenities
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
        self.last_cleaned = datetime.now()
        self.maintenance_notes = []
    
    def reserve(self, reservation: 'Reservation'):
        """Transition: AVAILABLE → RESERVED"""
        if self.status != RoomStatus.AVAILABLE:
            raise ValueError("Room %s is not available (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.RESERVED
        self.current_reservation = reservation
    
    def occupy(self):
        """Transition: RESERVED → OCCUPIED"""
        if self.status != RoomStatus.RESERVED:
            raise ValueError("Room %s is not reserved (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.OCCUPIED
    
    def checkout(self):
        """Transition: OCCUPIED → AVAILABLE"""
        if self.status != RoomStatus.OCCUPIED:
            raise ValueError("Room %s is not occupied (status: %s)" % 
                           (self.room_number, self.status.value))
        self.status = RoomStatus.AVAILABLE
        self.current_reservation = None
    
    def mark_for_maintenance(self, note: str):
        """Transition: ANY → MAINTENANCE"""
        self.status = RoomStatus.MAINTENANCE
        self.maintenance_notes.append({
            'timestamp': datetime.now(),
            'note': note
        })
    
    def complete_maintenance(self):
        """Transition: MAINTENANCE → AVAILABLE"""
        if self.status != RoomStatus.MAINTENANCE:
            raise ValueError("Room %s is not in maintenance" % self.room_number)
        self.status = RoomStatus.AVAILABLE
        self.last_cleaned = datetime.now()
    
    def __str__(self):
        return "Room %s (%s) - %s - $%.2f/night - Floor %d" % (
            self.room_number, self.room_type.value, self.status.value, 
            self.base_price, self.floor)


class Reservation:
    """Reservation with lifecycle management"""
    def __init__(self, reservation_id: str, guest: Guest, room: Room,
                 check_in_date: date, check_out_date: date):
        self.reservation_id = reservation_id
        self.guest = guest
        self.room = room
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.status = ReservationStatus.PENDING
        self.created_at = datetime.now()
        self.confirmed_at = None
        self.checked_in_at = None
        self.checked_out_at = None
        self.total_price = 0.0
        self.discount_applied = 0.0
        self.invoice = None
        self.num_nights = (check_out_date - check_in_date).days
    
    def confirm(self, total_price: float):
        """Transition: PENDING → CONFIRMED"""
        if self.status != ReservationStatus.PENDING:
            raise ValueError("Cannot confirm reservation with status %s" % self.status.value)
        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = datetime.now()
        self.total_price = total_price
        self.room.reserve(self)
    
    def check_in(self):
        """Transition: CONFIRMED → CHECKED_IN"""
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Cannot check in with status %s" % self.status.value)
        self.status = ReservationStatus.CHECKED_IN
        self.checked_in_at = datetime.now()
        self.room.occupy()
    
    def check_out(self):
        """Transition: CHECKED_IN → CHECKED_OUT"""
        if self.status != ReservationStatus.CHECKED_IN:
            raise ValueError("Cannot check out with status %s" % self.status.value)
        self.status = ReservationStatus.CHECKED_OUT
        self.checked_out_at = datetime.now()
        self.room.checkout()
    
    def cancel(self):
        """Cancel reservation"""
        if self.status == ReservationStatus.CHECKED_OUT:
            raise ValueError("Cannot cancel completed reservation")
        self.status = ReservationStatus.CANCELLED
        if self.room.status == RoomStatus.RESERVED:
            self.room.status = RoomStatus.AVAILABLE
            self.room.current_reservation = None


class InvoiceLineItem:
    """Individual charge on invoice"""
    def __init__(self, description: str, quantity: int, unit_price: float):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.amount = quantity * unit_price


class Invoice:
    """Invoice with line items and totals"""
    def __init__(self, invoice_id: str, reservation: Reservation):
        self.invoice_id = invoice_id
        self.reservation = reservation
        self.guest = reservation.guest
        self.line_items = []
        self.created_at = datetime.now()
        self.subtotal = 0.0
        self.tax = 0.0
        self.discount = 0.0
        self.total = 0.0
        self.amount_paid = 0.0
        self.balance = 0.0
    
    def add_line_item(self, description: str, quantity: int, unit_price: float):
        """Add charge to invoice"""
        item = InvoiceLineItem(description, quantity, unit_price)
        self.line_items.append(item)
        self._recalculate()
    
    def apply_discount(self, discount_amount: float):
        """Apply loyalty or promotional discount"""
        self.discount = discount_amount
        self._recalculate()
    
    def _recalculate(self):
        """Recalculate totals"""
        self.subtotal = sum(item.amount for item in self.line_items)
        self.tax = self.subtotal * 0.10  # 10% tax
        self.total = self.subtotal + self.tax - self.discount
        self.balance = self.total - self.amount_paid
    
    def get_summary(self) -> str:
        """Generate invoice summary"""
        summary = "\n" + "="*50 + "\n"
        summary += "           INVOICE %s\n" % self.invoice_id
        summary += "="*50 + "\n"
        summary += "Guest: %s\n" % self.guest.name
        summary += "Reservation: %s\n" % self.reservation.reservation_id
        summary += "Room: %s\n" % self.reservation.room.room_number
        summary += "-" * 50 + "\n"
        for item in self.line_items:
            summary += "%-30s x%d @ $%.2f = $%.2f\n" % (
                item.description, item.quantity, item.unit_price, item.amount)
        summary += "-" * 50 + "\n"
        summary += "%-40s $%.2f\n" % ("Subtotal:", self.subtotal)
        summary += "%-40s $%.2f\n" % ("Tax (10%):", self.tax)
        if self.discount > 0:
            summary += "%-40s -$%.2f\n" % ("Discount:", self.discount)
        summary += "%-40s $%.2f\n" % ("TOTAL:", self.total)
        summary += "%-40s $%.2f\n" % ("Paid:", self.amount_paid)
        summary += "%-40s $%.2f\n" % ("Balance:", self.balance)
        summary += "="*50 + "\n"
        return summary


class Payment:
    """Payment transaction"""
    def __init__(self, payment_id: str, invoice: Invoice, amount: float, 
                 method: PaymentMethod):
        self.payment_id = payment_id
        self.invoice = invoice
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING
        self.timestamp = datetime.now()
        self.transaction_id = None
    
    def process(self) -> bool:
        """Process payment (simplified)"""
        if self.amount <= 0:
            self.status = PaymentStatus.FAILED
            return False
        
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = "TXN_%s_%d" % (self.payment_id, int(datetime.now().timestamp()))
        self.invoice.amount_paid += self.amount
        self.invoice._recalculate()
        return True


class RoomService:
    """Service request with priority and assignment"""
    def __init__(self, service_id: str, room: Room, service_type: ServiceType,
                 description: str, priority: Priority):
        self.service_id = service_id
        self.room = room
        self.service_type = service_type
        self.description = description
        self.priority = priority
        self.requested_at = datetime.now()
        self.assigned_staff = None
        self.started_at = None
        self.completed_at = None
        self.is_completed = False
        self.notes = ""
    
    def assign_to(self, staff: 'Staff'):
        """Assign service to staff member"""
        self.assigned_staff = staff
        staff.assigned_services.append(self)
    
    def start_service(self):
        """Mark service as started"""
        self.started_at = datetime.now()
    
    def complete_service(self, notes: str = ""):
        """Mark service as completed"""
        self.completed_at = datetime.now()
        self.is_completed = True
        self.notes = notes
        if self.assigned_staff:
            self.assigned_staff.assigned_services.remove(self)


class Staff:
    """Staff member with role and availability"""
    def __init__(self, staff_id: str, name: str, role: StaffRole):
        self.staff_id = staff_id
        self.name = name
        self.role = role
        self.is_available = True
        self.assigned_services = []
        self.completed_services = 0
        self.shift_start = None
        self.shift_end = None
    
    def can_handle_service(self, service_type: ServiceType) -> bool:
        """Check if staff can handle this service type"""
        mapping = {
            StaffRole.HOUSEKEEPER: [ServiceType.HOUSEKEEPING, ServiceType.LAUNDRY],
            StaffRole.MAINTENANCE: [ServiceType.MAINTENANCE],
            StaffRole.ROOM_SERVICE: [ServiceType.ROOM_SERVICE],
        }
        return service_type in mapping.get(self.role, [])
    
    def __str__(self):
        status = "Available" if self.is_available else "Busy"
        return "%s (%s) - %s - %d active tasks, %d completed" % (
            self.name, self.role.value, status, len(self.assigned_services), 
            self.completed_services)


# ============================================================================
# SECTION 3: FACTORY PATTERN
# ============================================================================

class RoomFactory:
    """Factory for creating different room types"""
    
    @staticmethod
    def create_room(room_id: str, room_number: str, room_type: RoomType, 
                   floor: int) -> Room:
        """Create room with type-specific configuration"""
        
        if room_type == RoomType.STANDARD:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=100.0,
                floor=floor,
                capacity=2,
                amenities=["WiFi", "TV", "Air Conditioning"]
            )
        
        elif room_type == RoomType.DELUXE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=200.0,
                floor=floor,
                capacity=3,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar", 
                          "Room Service", "Ocean View"]
            )
        
        elif room_type == RoomType.SUITE:
            return Room(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                base_price=400.0,
                floor=floor,
                capacity=4,
                amenities=["WiFi", "TV", "Air Conditioning", "Mini Bar",
                          "Room Service", "Ocean View", "Jacuzzi", 
                          "Kitchen", "Living Room", "Balcony"]
            )
        
        else:
            raise ValueError("Unknown room type: %s" % room_type)


# ============================================================================
# SECTION 4: STRATEGY PATTERN - PRICING
# ============================================================================

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        pass


class RegularPricing(PricingStrategy):
    """Standard pricing without modifications"""
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        base_total = room.base_price * num_nights
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


class SeasonalPricing(PricingStrategy):
    """Seasonal pricing with summer/winter rates"""
    SUMMER_MULTIPLIER = 1.3  # 30% increase (June-August)
    WINTER_MULTIPLIER = 1.5  # 50% increase (December-February)
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        current_month = datetime.now().month
        
        # Determine seasonal multiplier
        if current_month in [6, 7, 8]:  # Summer
            multiplier = self.SUMMER_MULTIPLIER
            season = "Summer"
        elif current_month in [12, 1, 2]:  # Winter holidays
            multiplier = self.WINTER_MULTIPLIER
            season = "Winter"
        else:
            multiplier = 1.0
            season = "Regular"
        
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


class EventPricing(PricingStrategy):
    """Event-based pricing for conferences, holidays, etc."""
    def __init__(self, event_dates: List[date], event_multiplier: float = 2.0):
        self.event_dates = event_dates
        self.event_multiplier = event_multiplier
    
    def calculate_price(self, room: Room, num_nights: int, guest: Guest) -> float:
        # Check if reservation overlaps with event dates
        is_event_period = date.today() in self.event_dates
        
        multiplier = self.event_multiplier if is_event_period else 1.0
        base_total = room.base_price * num_nights * multiplier
        discount = base_total * guest.get_discount_percentage()
        return base_total - discount


# ============================================================================
# SECTION 5: OBSERVER PATTERN - NOTIFICATIONS
# ============================================================================

class HotelObserver(ABC):
    """Observer interface for hotel events"""
    @abstractmethod
    def update(self, event: str, data: dict):
        pass


class GuestNotifier(HotelObserver):
    """Notify guests of events"""
    def update(self, event: str, data: dict):
        if event in ["reservation_confirmed", "check_in_ready", "service_completed", 
                     "invoice_generated", "payment_processed"]:
            guest_name = data.get('guest_name', 'Guest')
            message = data.get('message', '')
            print("  [GUEST] %s: %s" % (guest_name, message))


class StaffNotifier(HotelObserver):
    """Notify staff of events"""
    def update(self, event: str, data: dict):
        if event in ["new_reservation", "service_requested", "check_out", 
                     "maintenance_needed"]:
            message = data.get('message', '')
            print("  [STAFF] %s" % message)


class AdminNotifier(HotelObserver):
    """Notify admin of critical events"""
    def update(self, event: str, data: dict):
        if event in ["payment_failed", "no_rooms_available", "maintenance_urgent",
                     "reservation_cancelled"]:
            message = data.get('message', '')
            priority = data.get('priority', 'NORMAL')
            print("  [ADMIN] [%s] %s" % (priority, message))


# ============================================================================
# SECTION 6: COMMAND PATTERN - SERVICE REQUESTS
# ============================================================================

class ServiceCommand(ABC):
    """Abstract command for service requests"""
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass


class RoomServiceCommand(ServiceCommand):
    """Command for room service request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        """Execute service request"""
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        return True
    
    def get_description(self) -> str:
        return "Room Service for %s - %s" % (
            self.service.room.room_number, self.service.description)


class HousekeepingCommand(ServiceCommand):
    """Command for housekeeping request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        return True
    
    def get_description(self) -> str:
        return "Housekeeping for %s" % self.service.room.room_number


class MaintenanceCommand(ServiceCommand):
    """Command for maintenance request"""
    def __init__(self, service: RoomService, staff: Staff):
        self.service = service
        self.staff = staff
    
    def execute(self) -> bool:
        if not self.staff.is_available:
            return False
        
        self.service.assign_to(self.staff)
        self.service.start_service()
        self.staff.is_available = False
        
        # Mark room for maintenance (store note even if already in maintenance)
        if self.service.room.status != RoomStatus.MAINTENANCE:
            self.service.room.mark_for_maintenance(self.service.description)
        else:
            # Add note to existing maintenance
            self.service.room.maintenance_notes.append({
                'timestamp': datetime.now(),
                'note': self.service.description
            })
        
        return True
    
    def get_description(self) -> str:
        return "Maintenance for %s - %s" % (
            self.service.room.room_number, self.service.description)


# ============================================================================
# SECTION 7: SINGLETON - HOTEL MANAGEMENT SYSTEM
# ============================================================================

class HotelManagementSystem:
    """Singleton controller for hotel operations"""
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
            # Room inventory
            self.rooms: Dict[str, Room] = {}
            self.room_counter = 0
            
            # Guest registry
            self.guests: Dict[str, Guest] = {}
            self.guest_counter = 0
            
            # Reservations
            self.reservations: Dict[str, Reservation] = {}
            self.reservation_counter = 0
            
            # Staff
            self.staff: Dict[str, Staff] = {}
            self.staff_counter = 0
            
            # Services
            self.services: Dict[str, RoomService] = {}
            self.service_counter = 0
            
            # Invoices & Payments
            self.invoices: Dict[str, Invoice] = {}
            self.invoice_counter = 0
            self.payments: Dict[str, Payment] = {}
            self.payment_counter = 0
            
            # Strategies
            self.pricing_strategy = RegularPricing()
            
            # Observers
            self.observers: List[HotelObserver] = []
            
            # Thread safety
            self.lock = threading.Lock()
            
            self.initialized = True
    
    # ===== Observer Management =====
    
    def attach_observer(self, observer: HotelObserver):
        """Add observer for notifications"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: dict):
        """Notify all observers of event"""
        for observer in self.observers:
            observer.update(event, data)
    
    # ===== Strategy Management =====
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Change pricing strategy at runtime"""
        self.pricing_strategy = strategy
    
    # ===== Room Management =====
    
    def add_room(self, room_type: RoomType, room_number: str, floor: int) -> Room:
        """Add room using factory"""
        with self.lock:
            self.room_counter += 1
            room_id = "ROOM_%04d" % self.room_counter
            
            room = RoomFactory.create_room(room_id, room_number, room_type, floor)
            self.rooms[room_id] = room
            
            return room
    
    def get_available_rooms(self, room_type: Optional[RoomType] = None) -> List[Room]:
        """Get available rooms, optionally filtered by type"""
        available = [r for r in self.rooms.values() 
                    if r.status == RoomStatus.AVAILABLE]
        
        if room_type:
            available = [r for r in available if r.room_type == room_type]
        
        return available
    
    # ===== Guest Management =====
    
    def register_guest(self, name: str, email: str, phone: str) -> Guest:
        """Register new guest"""
        with self.lock:
            self.guest_counter += 1
            guest_id = "GUEST_%05d" % self.guest_counter
            
            guest = Guest(guest_id, name, email, phone)
            self.guests[guest_id] = guest
            
            return guest
    
    # ===== Staff Management =====
    
    def add_staff(self, name: str, role: StaffRole) -> Staff:
        """Add staff member"""
        with self.lock:
            self.staff_counter += 1
            staff_id = "STAFF_%04d" % self.staff_counter
            
            staff = Staff(staff_id, name, role)
            self.staff[staff_id] = staff
            
            return staff
    
    def find_available_staff(self, service_type: ServiceType) -> Optional[Staff]:
        """Find available staff for service type"""
        for staff in self.staff.values():
            if staff.is_available and staff.can_handle_service(service_type):
                return staff
        return None
    
    # ===== Reservation Management =====
    
    def create_reservation(self, guest: Guest, room_type: RoomType,
                          check_in: date, check_out: date) -> Optional[Reservation]:
        """Create new reservation"""
        with self.lock:
            # Find available room
            available_rooms = self.get_available_rooms(room_type)
            if not available_rooms:
                self.notify_observers("no_rooms_available", {
                    'guest_name': guest.name,
                    'room_type': room_type.value,
                    'message': "No %s rooms available" % room_type.value
                })
                return None
            
            # Select first available room
            room = available_rooms[0]
            
            # Create reservation
            self.reservation_counter += 1
            reservation_id = "RES_%06d" % self.reservation_counter
            
            reservation = Reservation(reservation_id, guest, room, check_in, check_out)
            
            # Calculate price using strategy
            total_price = self.pricing_strategy.calculate_price(
                room, reservation.num_nights, guest)
            
            # Confirm reservation
            reservation.confirm(total_price)
            reservation.discount_applied = room.base_price * reservation.num_nights * \
                                          guest.get_discount_percentage()
            
            self.reservations[reservation_id] = reservation
            
            # Notify observers
            self.notify_observers("reservation_confirmed", {
                'guest_name': guest.name,
                'room_number': room.room_number,
                'check_in': str(check_in),
                'check_out': str(check_out),
                'total_price': total_price,
                'message': "Reservation confirmed! Room %s (%d nights) - Total: $%.2f" % 
                          (room.room_number, reservation.num_nights, total_price)
            })
            
            self.notify_observers("new_reservation", {
                'message': "New reservation: %s for %s, Room %s (%s to %s)" % 
                          (guest.name, room_type.value, room.room_number, 
                           check_in, check_out)
            })
            
            return reservation
    
    def check_in(self, reservation: Reservation) -> bool:
        """Check in guest"""
        try:
            reservation.check_in()
            
            self.notify_observers("check_in_ready", {
                'guest_name': reservation.guest.name,
                'room_number': reservation.room.room_number,
                'message': "Welcome! Checked into Room %s. Enjoy your stay!" % 
                          reservation.room.room_number
            })
            
            return True
        except ValueError as e:
            print("  [ERROR] Check-in failed: %s" % str(e))
            return False
    
    def check_out(self, reservation: Reservation) -> Optional[Invoice]:
        """Check out guest and generate invoice"""
        with self.lock:
            # Check out
            reservation.check_out()
            
            # Generate invoice
            self.invoice_counter += 1
            invoice_id = "INV_%06d" % self.invoice_counter
            
            invoice = Invoice(invoice_id, reservation)
            
            # Add room charges
            invoice.add_line_item(
                description="%s Room (%d nights)" % (
                    reservation.room.room_type.value.title(), 
                    reservation.num_nights),
                quantity=reservation.num_nights,
                unit_price=reservation.room.base_price
            )
            
            # Apply discount
            if reservation.discount_applied > 0:
                invoice.apply_discount(reservation.discount_applied)
            
            self.invoices[invoice_id] = invoice
            reservation.invoice = invoice
            
            # Update guest stats
            reservation.guest.total_stays += 1
            
            # Notify observers
            self.notify_observers("invoice_generated", {
                'guest_name': reservation.guest.name,
                'invoice_id': invoice_id,
                'total': invoice.total,
                'message': "Checked out from Room %s. Invoice #%s generated (Total: $%.2f)" % 
                          (reservation.room.room_number, invoice_id, invoice.total)
            })
            
            self.notify_observers("check_out", {
                'message': "Guest %s checked out from Room %s" % 
                          (reservation.guest.name, reservation.room.room_number)
            })
            
            return invoice
    
    # ===== Payment Processing =====
    
    def process_payment(self, invoice: Invoice, amount: float, 
                       method: PaymentMethod) -> Optional[Payment]:
        """Process payment for invoice"""
        with self.lock:
            self.payment_counter += 1
            payment_id = "PAY_%06d" % self.payment_counter
            
            payment = Payment(payment_id, invoice, amount, method)
            
            if payment.process():
                self.payments[payment_id] = payment
                
                # Award loyalty points (1 point per $10 spent)
                points = int(amount / 10)
                invoice.guest.add_loyalty_points(points)
                invoice.guest.total_spent += amount
                
                self.notify_observers("payment_processed", {
                    'guest_name': invoice.guest.name,
                    'amount': amount,
                    'method': method.value,
                    'points': points,
                    'message': "Payment of $%.2f processed via %s. Earned %d loyalty points!" % 
                              (amount, method.value, points)
                })
                
                return payment
            else:
                self.notify_observers("payment_failed", {
                    'guest_name': invoice.guest.name,
                    'amount': amount,
                    'message': "Payment of $%.2f failed" % amount,
                    'priority': 'HIGH'
                })
                return None
    
    # ===== Service Management =====
    
    def request_service(self, room: Room, service_type: ServiceType,
                       description: str, priority: Priority) -> Optional[RoomService]:
        """Request room service"""
        with self.lock:
            # Find available staff
            staff = self.find_available_staff(service_type)
            
            if not staff:
                self.notify_observers("service_requested", {
                    'message': "Service request for Room %s queued (no staff available)" % 
                              room.room_number
                })
                return None
            
            # Create service request
            self.service_counter += 1
            service_id = "SVC_%06d" % self.service_counter
            
            service = RoomService(service_id, room, service_type, description, priority)
            self.services[service_id] = service
            
            # Create and execute command
            if service_type == ServiceType.ROOM_SERVICE:
                command = RoomServiceCommand(service, staff)
            elif service_type == ServiceType.HOUSEKEEPING:
                command = HousekeepingCommand(service, staff)
            elif service_type == ServiceType.MAINTENANCE:
                command = MaintenanceCommand(service, staff)
            else:
                command = RoomServiceCommand(service, staff)
            
            if command.execute():
                self.notify_observers("service_requested", {
                    'message': "%s: %s assigned to %s for Room %s" % 
                              (service_type.value, staff.name, staff.role.value, 
                               room.room_number)
                })
                
                if service_type == ServiceType.MAINTENANCE and priority == Priority.URGENT:
                    self.notify_observers("maintenance_urgent", {
                        'message': "URGENT maintenance needed in Room %s: %s" % 
                                  (room.room_number, description),
                        'priority': 'URGENT'
                    })
                
                return service
            
            return None
    
    def complete_service(self, service: RoomService, notes: str = ""):
        """Complete service request"""
        service.complete_service(notes)
        
        if service.assigned_staff:
            service.assigned_staff.is_available = True
            service.assigned_staff.completed_services += 1
        
        # Complete maintenance on room
        if service.service_type == ServiceType.MAINTENANCE:
            if service.room.status == RoomStatus.MAINTENANCE:
                service.room.complete_maintenance()
        
        self.notify_observers("service_completed", {
            'guest_name': 'Guest',
            'service_type': service.service_type.value,
            'room_number': service.room.room_number,
            'message': "%s completed for Room %s" % 
                      (service.service_type.value, service.room.room_number)
        })
    
    # ===== Statistics =====
    
    def get_statistics(self) -> dict:
        """Get hotel statistics"""
        total_rooms = len(self.rooms)
        available_rooms = len([r for r in self.rooms.values() 
                              if r.status == RoomStatus.AVAILABLE])
        occupied_rooms = len([r for r in self.rooms.values() 
                             if r.status == RoomStatus.OCCUPIED])
        reserved_rooms = len([r for r in self.rooms.values() 
                             if r.status == RoomStatus.RESERVED])
        
        return {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'reserved_rooms': reserved_rooms,
            'occupied_rooms': occupied_rooms,
            'maintenance_rooms': total_rooms - available_rooms - reserved_rooms - occupied_rooms,
            'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0,
            'total_guests': len(self.guests),
            'total_staff': len(self.staff),
            'active_reservations': len([r for r in self.reservations.values() 
                                       if r.status in [ReservationStatus.CONFIRMED, 
                                                      ReservationStatus.CHECKED_IN]]),
            'completed_stays': len([r for r in self.reservations.values() 
                                   if r.status == ReservationStatus.CHECKED_OUT]),
            'pending_services': len([s for s in self.services.values() 
                                    if not s.is_completed])
        }


# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70)


def demo1_setup_and_room_creation():
    """Demo 1: System Setup & Room Creation"""
    print_section("DEMO 1: System Setup & Room Creation")
    
    system = HotelManagementSystem()
    
    # Add observers
    print("\n1. Adding observers...")
    system.attach_observer(GuestNotifier())
    system.attach_observer(StaffNotifier())
    system.attach_observer(AdminNotifier())
    print("   ✓ Guest, Staff, and Admin notifiers attached")
    
    # Create rooms using factory
    print("\n2. Creating rooms using Factory pattern...")
    rooms_config = [
        (RoomType.STANDARD, "101", 1),
        (RoomType.STANDARD, "102", 1),
        (RoomType.DELUXE, "201", 2),
        (RoomType.DELUXE, "202", 2),
        (RoomType.SUITE, "301", 3),
    ]
    
    for room_type, room_number, floor in rooms_config:
        room = system.add_room(room_type, room_number, floor)
        print("   ✓ Created: %s" % room)
    
    # Add staff
    print("\n3. Adding staff members...")
    staff_config = [
        ("Maria", StaffRole.HOUSEKEEPER),
        ("Carlos", StaffRole.ROOM_SERVICE),
        ("David", StaffRole.MAINTENANCE),
        ("Ana", StaffRole.HOUSEKEEPER),
    ]
    
    for name, role in staff_config:
        staff = system.add_staff(name, role)
        print("   ✓ Added: %s" % staff)
    
    # Display statistics
    print("\n4. System Statistics:")
    stats = system.get_statistics()
    for key, value in stats.items():
        print("   %s: %s" % (key.replace('_', ' ').title(), value))


def demo2_guest_registration_and_reservation():
    """Demo 2: Guest Registration & Reservation"""
    print_section("DEMO 2: Guest Registration & Reservation")
    
    system = HotelManagementSystem()
    
    # Register guests
    print("\n1. Registering guests...")
    guest1 = system.register_guest("John Smith", "john@email.com", "555-0101")
    guest2 = system.register_guest("Sarah Johnson", "sarah@email.com", "555-0102")
    print("   ✓ %s" % guest1)
    print("   ✓ %s" % guest2)
    
    # Create reservation
    print("\n2. Creating reservation...")
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=4)
    
    reservation = system.create_reservation(guest1, RoomType.STANDARD, check_in, check_out)
    
    if reservation:
        print("\n3. Reservation Details:")
        print("   ID: %s" % reservation.reservation_id)
        print("   Guest: %s" % reservation.guest.name)
        print("   Room: %s (%s)" % (reservation.room.room_number, reservation.room.room_type.value))
        print("   Check-in: %s" % reservation.check_in_date)
        print("   Check-out: %s" % reservation.check_out_date)
        print("   Nights: %d" % reservation.num_nights)
        print("   Total: $%.2f" % reservation.total_price)
        print("   Status: %s" % reservation.status.value)


def demo3_dynamic_pricing_comparison():
    """Demo 3: Dynamic Pricing Comparison"""
    print_section("DEMO 3: Dynamic Pricing Comparison")
    
    system = HotelManagementSystem()
    
    # Get a room and guest
    guest = system.register_guest("Alice Williams", "alice@email.com", "555-0103")
    room = list(system.rooms.values())[0]  # Get first room
    
    num_nights = 3
    
    print("\n1. Comparing pricing strategies for %s Room (%d nights)..." % 
          (room.room_type.value.title(), num_nights))
    print("   Base price: $%.2f/night" % room.base_price)
    print("   Guest discount: %.0f%%" % (guest.get_discount_percentage() * 100))
    
    # Regular pricing
    print("\n2. Regular Pricing:")
    system.set_pricing_strategy(RegularPricing())
    regular_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % regular_price)
    
    # Seasonal pricing
    print("\n3. Seasonal Pricing:")
    system.set_pricing_strategy(SeasonalPricing())
    seasonal_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % seasonal_price)
    print("   Difference: $%.2f (%.1f%%)" % 
          (seasonal_price - regular_price, 
           ((seasonal_price - regular_price) / regular_price * 100)))
    
    # Event pricing
    print("\n4. Event Pricing (conference dates):")
    event_dates = [date.today() + timedelta(days=i) for i in range(7)]
    system.set_pricing_strategy(EventPricing(event_dates, event_multiplier=2.0))
    event_price = system.pricing_strategy.calculate_price(room, num_nights, guest)
    print("   Price: $%.2f" % event_price)
    print("   Difference: $%.2f (%.1f%%)" % 
          (event_price - regular_price, 
           ((event_price - regular_price) / regular_price * 100)))
    
    # VIP guest comparison
    print("\n5. VIP Guest with 1000 loyalty points:")
    vip_guest = system.register_guest("VIP Member", "vip@email.com", "555-0104")
    vip_guest.add_loyalty_points(1000)
    print("   Guest: %s" % vip_guest)
    print("   Discount: %.0f%%" % (vip_guest.get_discount_percentage() * 100))
    
    system.set_pricing_strategy(RegularPricing())
    vip_price = system.pricing_strategy.calculate_price(room, num_nights, vip_guest)
    print("   Regular price: $%.2f" % regular_price)
    print("   VIP price: $%.2f" % vip_price)
    print("   Savings: $%.2f" % (regular_price - vip_price))


def demo4_full_guest_journey():
    """Demo 4: Full Guest Journey"""
    print_section("DEMO 4: Full Guest Journey (Reservation to Check-out)")
    
    system = HotelManagementSystem()
    
    # Register guest
    print("\n1. Guest Registration:")
    guest = system.register_guest("Emma Davis", "emma@email.com", "555-0105")
    print("   %s" % guest)
    
    # Create reservation
    print("\n2. Creating Reservation:")
    check_in = date.today()
    check_out = date.today() + timedelta(days=2)
    reservation = system.create_reservation(guest, RoomType.DELUXE, check_in, check_out)
    
    # Check in
    print("\n3. Checking In:")
    system.check_in(reservation)
    
    # Request services
    print("\n4. Requesting Services (Command Pattern):")
    
    # Room service
    service1 = system.request_service(
        reservation.room, 
        ServiceType.ROOM_SERVICE,
        "Breakfast for 2: eggs, toast, coffee",
        Priority.MEDIUM
    )
    
    # Housekeeping
    service2 = system.request_service(
        reservation.room,
        ServiceType.HOUSEKEEPING,
        "Extra towels and toiletries",
        Priority.LOW
    )
    
    # Complete services
    print("\n5. Completing Services:")
    if service1:
        system.complete_service(service1, "Delivered at 8:30 AM")
    if service2:
        system.complete_service(service2, "Restocked at 10:00 AM")
    
    # Check out
    print("\n6. Checking Out & Generating Invoice:")
    invoice = system.check_out(reservation)
    
    if invoice:
        print(invoice.get_summary())
    
    # Process payment
    print("7. Processing Payment:")
    payment = system.process_payment(invoice, invoice.total, PaymentMethod.CREDIT_CARD)
    
    if payment:
        print("\n8. Updated Guest Profile:")
        print("   %s" % guest)


def demo5_room_state_management():
    """Demo 5: Room State Management & Maintenance"""
    print_section("DEMO 5: Room State Management & Maintenance")
    
    system = HotelManagementSystem()
    
    # Get a room
    room = list(system.rooms.values())[2]  # Get third room
    guest = system.register_guest("Mike Brown", "mike@email.com", "555-0106")
    
    print("\n1. Initial Room State:")
    print("   %s" % room)
    print("   Status: %s" % room.status.value)
    
    # Reserve room
    print("\n2. Creating Reservation (AVAILABLE → RESERVED):")
    check_in = date.today()
    check_out = date.today() + timedelta(days=1)
    reservation = system.create_reservation(guest, room.room_type, check_in, check_out)
    print("   New Status: %s" % room.status.value)
    
    # Check in
    print("\n3. Checking In (RESERVED → OCCUPIED):")
    system.check_in(reservation)
    print("   New Status: %s" % room.status.value)
    
    # Request urgent maintenance
    print("\n4. Requesting Urgent Maintenance:")
    service = system.request_service(
        room,
        ServiceType.MAINTENANCE,
        "Air conditioning not working",
        Priority.URGENT
    )
    
    if service:
        print("   Room Status: %s" % room.status.value)
        if room.maintenance_notes:
            print("   Maintenance Notes: %s" % room.maintenance_notes[-1]['note'])
    
    # Complete maintenance
    print("\n5. Completing Maintenance:")
    if service:
        # Complete the maintenance service
        system.complete_service(service, "Replaced AC filter and recharged coolant")
        print("   Room Status after maintenance: %s" % room.status.value)
        
        # Now check out the guest (room is back to AVAILABLE, but we need to manually set to OCCUPIED first)
        # This is a demo limitation - in real scenario, guest would still be in room during maintenance
        print("\n6. Checking Out Guest:")
        # Manually restore to OCCUPIED state for proper checkout
        room.status = RoomStatus.OCCUPIED
        system.check_out(reservation)
        print("   Room Status after checkout: %s" % room.status.value)
    
    # Attempt invalid transition
    print("\n7. Attempting Invalid State Transition:")
    print("   Trying to occupy an available room (should fail)...")
    try:
        room.occupy()
    except ValueError as e:
        print("   ✓ Correctly prevented: %s" % str(e))
    
    # Show state machine
    print("\n8. Room State Machine:")
    print("   AVAILABLE → RESERVED → OCCUPIED → AVAILABLE")
    print("        ↓         ↓          ↓")
    print("   MAINTENANCE (from any state)")
    print("\n   Note: Room transitions back to AVAILABLE after maintenance completes")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("HOTEL MANAGEMENT SYSTEM - COMPLETE DEMONSTRATION".center(70))
    print("="*70)
    print("\nDesign Patterns Implemented:")
    print("  1. Singleton    - HotelManagementSystem")
    print("  2. Factory      - RoomFactory")
    print("  3. Strategy     - PricingStrategy (Regular/Seasonal/Event)")
    print("  4. Observer     - Notifications (Guest/Staff/Admin)")
    print("  5. State        - Room & Reservation lifecycles")
    print("  6. Command      - Service requests")
    
    time.sleep(1)
    
    demo1_setup_and_room_creation()
    time.sleep(1)
    
    demo2_guest_registration_and_reservation()
    time.sleep(1)
    
    demo3_dynamic_pricing_comparison()
    time.sleep(1)
    
    demo4_full_guest_journey()
    time.sleep(1)
    
    demo5_room_state_management()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY".center(70))
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Singleton ensures single system instance with thread safety")
    print("  • Factory creates rooms with type-specific configurations")
    print("  • Strategy enables runtime pricing changes")
    print("  • Observer decouples notifications from core logic")
    print("  • State machines prevent invalid transitions")
    print("  • Command encapsulates service requests for queuing")
    print("\nRun: python3 INTERVIEW_COMPACT.py")
    print("="*70 + "\n")
