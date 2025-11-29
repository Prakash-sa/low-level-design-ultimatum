"""Car Rental System - Interview Implementation"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Tuple
from datetime import datetime, timedelta
import threading

class VehicleType(Enum):
    ECONOMY = 1
    SEDAN = 2
    SUV = 3
    LUXURY = 4

class VehicleStatus(Enum):
    AVAILABLE = 1
    RENTED = 2
    MAINTENANCE = 3
    RETIRED = 4

class BookingStatus(Enum):
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELLED = 4
    RETURNED = 5

class PaymentStatus(Enum):
    PENDING = 1
    PAID = 2
    FAILED = 3
    REFUNDED = 4

class Vehicle:
    BASE_RATES = {
        VehicleType.ECONOMY: 40.0,
        VehicleType.SEDAN: 60.0,
        VehicleType.SUV: 80.0,
        VehicleType.LUXURY: 150.0
    }
    
    def __init__(self, vehicle_id, vehicle_type, license_plate, location_id):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate
        self.location_id = location_id
        self.status = VehicleStatus.AVAILABLE
        self.mileage = 0.0
        self.fuel_level = 100.0
        self.damage_reported = False
        self.created_at = datetime.now()
    
    def is_available(self):
        return self.status == VehicleStatus.AVAILABLE and not self.damage_reported
    
    def reserve(self):
        if self.status == VehicleStatus.AVAILABLE:
            self.status = VehicleStatus.RENTED
            return True
        return False
    
    def release(self):
        self.status = VehicleStatus.AVAILABLE
    
    def update_fuel(self, fuel_level):
        self.fuel_level = max(0.0, min(100.0, fuel_level))
    
    def report_damage(self):
        self.damage_reported = True
        self.status = VehicleStatus.MAINTENANCE
    
    def clear_damage(self):
        self.damage_reported = False
        self.status = VehicleStatus.AVAILABLE
    
    def update_mileage(self, additional_miles):
        self.mileage += additional_miles
    
    def __repr__(self):
        return "%s (%s)" % (self.vehicle_id, self.vehicle_type.name)

class Customer:
    def __init__(self, customer_id, name, email):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.bookings = []
        self.created_at = datetime.now()
        self.total_rentals = 0
        self.loyalty_points = 0
    
    def add_booking(self, booking):
        self.bookings.append(booking)
        self.total_rentals += 1
        self.loyalty_points += 10
    
    def get_loyalty_discount(self):
        if self.total_rentals > 100:
            return 0.20
        elif self.total_rentals > 50:
            return 0.15
        elif self.total_rentals > 10:
            return 0.10
        return 0.0

class Location:
    def __init__(self, location_id, name, city):
        self.location_id = location_id
        self.name = name
        self.city = city
        self.vehicles = []
        self.bookings = []
        self.lock = threading.Lock()
    
    def add_vehicle(self, vehicle):
        with self.lock:
            self.vehicles.append(vehicle)
    
    def get_available_vehicles(self, vehicle_type=None):
        with self.lock:
            available = [v for v in self.vehicles if v.is_available()]
            if vehicle_type:
                available = [v for v in available if v.vehicle_type == vehicle_type]
            return available
    
    def get_available_count(self, vehicle_type):
        with self.lock:
            return len([v for v in self.vehicles 
                       if v.vehicle_type == vehicle_type and v.is_available()])
    
    def add_booking(self, booking):
        with self.lock:
            self.bookings.append(booking)

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, vehicle, rental_days, base_rate, location):
        pass

class DailyRatePricing(PricingStrategy):
    def calculate_price(self, vehicle, rental_days, base_rate, location):
        return base_rate * rental_days

class WeeklyDiscountPricing(PricingStrategy):
    def calculate_price(self, vehicle, rental_days, base_rate, location):
        if rental_days >= 7:
            return base_rate * rental_days * 0.85
        return base_rate * rental_days

class DemandBasedPricing(PricingStrategy):
    def calculate_price(self, vehicle, rental_days, base_rate, location):
        available_count = location.get_available_count(vehicle.vehicle_type)
        if available_count > 5:
            multiplier = 1.0
        elif available_count < 2:
            multiplier = 1.3
        else:
            multiplier = 1.1
        return base_rate * rental_days * multiplier

class Booking:
    def __init__(self, booking_id, customer, vehicle, location, pickup_date, dropoff_date):
        self.booking_id = booking_id
        self.customer = customer
        self.vehicle = vehicle
        self.location = location
        self.pickup_date = pickup_date
        self.dropoff_date = dropoff_date
        self.status = BookingStatus.PENDING
        self.created_at = datetime.now()
        self.rental_cost = 0.0
        self.fuel_charge = 0.0
        self.damage_charge = 0.0
        self.total_cost = 0.0
        self.payment_status = PaymentStatus.PENDING
    
    def get_rental_days(self):
        delta = self.dropoff_date - self.pickup_date
        return max(1, delta.days)
    
    def calculate_cost(self, pricing_strategy, base_rate):
        rental_days = self.get_rental_days()
        cost = pricing_strategy.calculate_price(self.vehicle, rental_days, base_rate, self.location)
        discount = self.customer.get_loyalty_discount()
        cost = cost * (1 - discount)
        self.rental_cost = cost
        return cost
    
    def add_fuel_charge(self, charge):
        self.fuel_charge += charge
    
    def add_damage_charge(self, charge):
        self.damage_charge += charge
    
    def finalize_cost(self):
        self.total_cost = self.rental_cost + self.fuel_charge + self.damage_charge
        return self.total_cost
    
    def activate(self):
        if self.status == BookingStatus.PENDING:
            self.status = BookingStatus.ACTIVE
            return True
        return False
    
    def complete(self):
        self.status = BookingStatus.COMPLETED
    
    def return_vehicle(self):
        self.status = BookingStatus.RETURNED
        return self.total_cost
    
    def __repr__(self):
        return "Booking(%s) %s %s" % (self.booking_id, self.vehicle, self.status.name)

class BookingObserver(ABC):
    @abstractmethod
    def update(self, event, data):
        pass

class EmailNotifier(BookingObserver):
    def update(self, event, data):
        print("    [EMAIL] %s - %s - %s" % (event, data.get('customer'), data.get('vehicle')))

class SMSNotifier(BookingObserver):
    def update(self, event, data):
        print("    [SMS] %s - %s" % (event, data.get('customer')))

class SystemLogNotifier(BookingObserver):
    def update(self, event, data):
        print("    [LOG] [%s] %s" % (datetime.now().strftime('%H:%M:%S'), event))

class CarRentalSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.locations = {}
        self.customers = {}
        self.vehicles = {}
        self.bookings = {}
        self.observers = []
        self.lock = threading.Lock()
        self.pricing_strategy = DailyRatePricing()
    
    def register_location(self, location_id, name, city):
        with self.lock:
            location = Location(location_id, name, city)
            self.locations[location_id] = location
            return location
    
    def register_customer(self, customer_id, name, email):
        with self.lock:
            customer = Customer(customer_id, name, email)
            self.customers[customer_id] = customer
            return customer
    
    def add_vehicle(self, vehicle_id, vehicle_type, license_plate, location_id):
        with self.lock:
            vehicle = Vehicle(vehicle_id, vehicle_type, license_plate, location_id)
            self.vehicles[vehicle_id] = vehicle
            if location_id in self.locations:
                self.locations[location_id].add_vehicle(vehicle)
            return vehicle
    
    def search_vehicles(self, location_id, vehicle_type):
        if location_id not in self.locations:
            return []
        return self.locations[location_id].get_available_vehicles(vehicle_type)
    
    def create_booking(self, customer_id, vehicle_id, location_id, pickup_date, dropoff_date):
        with self.lock:
            if customer_id not in self.customers or vehicle_id not in self.vehicles:
                return False, None
            
            customer = self.customers[customer_id]
            vehicle = self.vehicles[vehicle_id]
            location = self.locations.get(location_id)
            
            if not vehicle.is_available() or vehicle.location_id != location_id:
                return False, None
            
            if not vehicle.reserve():
                return False, None
            
            booking_id = "BK_%s" % int(datetime.now().timestamp())
            booking = Booking(booking_id, customer, vehicle, location, pickup_date, dropoff_date)
            
            base_rate = vehicle.BASE_RATES[vehicle.vehicle_type]
            booking.calculate_cost(self.pricing_strategy, base_rate)
            
            self.bookings[booking_id] = booking
            location.add_booking(booking)
            customer.add_booking(booking)
            
            self._notify_observers("Booking Created", {
                "customer": customer.name,
                "vehicle": str(vehicle),
                "booking_id": booking_id,
                "cost": "$%.2f" % booking.rental_cost
            })
            
            return True, booking
    
    def pickup_vehicle(self, booking_id):
        with self.lock:
            if booking_id not in self.bookings:
                return False, "Booking not found"
            
            booking = self.bookings[booking_id]
            if not booking.activate():
                return False, "Booking already activated"
            
            booking.payment_status = PaymentStatus.PAID
            
            self._notify_observers("Vehicle Picked Up", {
                "customer": booking.customer.name,
                "vehicle": str(booking.vehicle),
                "booking_id": booking_id
            })
            
            return True, "Pickup successful. Vehicle: %s" % booking.vehicle.vehicle_id
    
    def return_vehicle(self, booking_id, fuel_level=100.0, damage=False, damage_amount=0.0):
        with self.lock:
            if booking_id not in self.bookings:
                return False, {}
            
            booking = self.bookings[booking_id]
            
            if fuel_level < 100.0:
                fuel_charge = (100.0 - fuel_level) * 0.5
                booking.add_fuel_charge(fuel_charge)
            
            if damage:
                booking.add_damage_charge(damage_amount)
                booking.vehicle.report_damage()
            
            booking.vehicle.update_fuel(fuel_level)
            booking.complete()
            booking.return_vehicle()
            
            self._notify_observers("Vehicle Returned", {
                "customer": booking.customer.name,
                "vehicle": str(booking.vehicle),
                "total_cost": "$%.2f" % booking.total_cost
            })
            
            return True, {
                "rental_cost": booking.rental_cost,
                "fuel_charge": booking.fuel_charge,
                "damage_charge": booking.damage_charge,
                "total_cost": booking.total_cost
            }
    
    def set_pricing_strategy(self, strategy):
        self.pricing_strategy = strategy
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def _notify_observers(self, event, data):
        for observer in self.observers:
            observer.update(event, data)

def demo_1_setup_and_search():
    print("\n" + "="*70)
    print("DEMO 1: SETUP AND VEHICLE SEARCH")
    print("="*70)
    
    system = CarRentalSystem()
    
    loc_sf = system.register_location("LOC_SF", "San Francisco Downtown", "SF")
    loc_la = system.register_location("LOC_LA", "Los Angeles Beach", "LA")
    print("- Locations registered: %s, %s" % (loc_sf.name, loc_la.name))
    
    v1 = system.add_vehicle("VH_001", VehicleType.ECONOMY, "SF-1001", "LOC_SF")
    v2 = system.add_vehicle("VH_002", VehicleType.SEDAN, "SF-2001", "LOC_SF")
    v3 = system.add_vehicle("VH_003", VehicleType.SUV, "SF-3001", "LOC_SF")
    print("- Vehicles added to SF: %s, %s, %s" % (v1, v2, v3))
    
    v4 = system.add_vehicle("VH_004", VehicleType.LUXURY, "LA-4001", "LOC_LA")
    print("- Vehicle added to LA: %s" % v4)
    
    c1 = system.register_customer("CUST_001", "Alice Johnson", "alice@example.com")
    c2 = system.register_customer("CUST_002", "Bob Smith", "bob@example.com")
    print("- Customers registered: %s, %s" % (c1.name, c2.name))
    
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    print("\nSearching for ECONOMY vehicles in SF:")
    results = system.search_vehicles("LOC_SF", VehicleType.ECONOMY)
    for v in results:
        print("  Available: %s - $%.0f/day" % (v.vehicle_id, v.BASE_RATES[v.vehicle_type]))

def demo_2_successful_booking():
    print("\n" + "="*70)
    print("DEMO 2: SUCCESSFUL BOOKING (DAILY RATE PRICING)")
    print("="*70)
    
    system = CarRentalSystem()
    
    loc = system.register_location("LOC_SF", "Downtown", "SF")
    vehicle = system.add_vehicle("VH_001", VehicleType.SEDAN, "SF-2001", "LOC_SF")
    system.register_customer("CUST_001", "Alice", "alice@example.com")
    system.add_observer(EmailNotifier())
    
    print("Vehicle: %s (%s)" % (vehicle.vehicle_id, vehicle.vehicle_type.name))
    print("Base rate: $%.0f/day" % vehicle.BASE_RATES[vehicle.vehicle_type])
    
    pickup = datetime.now()
    dropoff = pickup + timedelta(days=3)
    
    print("\nCreating booking for 3 days...")
    success, booking = system.create_booking("CUST_001", "VH_001", "LOC_SF", pickup, dropoff)
    
    if success:
        print("- Booking created: %s" % booking.booking_id)
        print("  Rental cost: $%.2f" % booking.rental_cost)
        print("  Vehicle status: %s" % vehicle.status.name)
    else:
        print("- Booking failed")

def demo_3_loyalty_discount():
    print("\n" + "="*70)
    print("DEMO 3: BOOKING WITH LOYALTY DISCOUNT")
    print("="*70)
    
    system = CarRentalSystem()
    system.set_pricing_strategy(DailyRatePricing())
    
    loc = system.register_location("LOC_SF", "Downtown", "SF")
    vehicle = system.add_vehicle("VH_001", VehicleType.SEDAN, "SF-2001", "LOC_SF")
    customer = system.register_customer("CUST_VIP", "VIP Member", "vip@example.com")
    
    customer.total_rentals = 15
    
    print("Customer: %s - %d total rentals" % (customer.name, customer.total_rentals))
    print("Loyalty discount: %.0f%%" % (customer.get_loyalty_discount() * 100))
    
    pickup = datetime.now()
    dropoff = pickup + timedelta(days=5)
    
    print("\nCreating 5-day booking...")
    success, booking = system.create_booking("CUST_VIP", "VH_001", "LOC_SF", pickup, dropoff)
    
    if success:
        base_cost = 60.0 * 5
        print("- Base cost (5 days @ $60): $%.2f" % base_cost)
        print("- After 10%% loyalty discount: $%.2f" % booking.rental_cost)
        print("- Savings: $%.2f" % (base_cost - booking.rental_cost))

def demo_4_demand_based_pricing():
    print("\n" + "="*70)
    print("DEMO 4: DEMAND-BASED PRICING")
    print("="*70)
    
    system = CarRentalSystem()
    system.set_pricing_strategy(DemandBasedPricing())
    
    loc = system.register_location("LOC_SF", "Downtown", "SF")
    
    vehicle = system.add_vehicle("VH_001", VehicleType.SUV, "SF-3001", "LOC_SF")
    system.register_customer("CUST_001", "Bob", "bob@example.com")
    
    print("Vehicle: %s (%s)" % (vehicle.vehicle_id, vehicle.vehicle_type.name))
    print("Available SUVs at location: %d" % loc.get_available_count(VehicleType.SUV))
    print("Low availability - Surge pricing active (30%% premium)")
    
    pickup = datetime.now()
    dropoff = pickup + timedelta(days=2)
    
    print("\nCreating 2-day booking...")
    success, booking = system.create_booking("CUST_001", "VH_001", "LOC_SF", pickup, dropoff)
    
    if success:
        base_cost = 80.0 * 2
        print("- Base cost (2 days @ $80): $%.2f" % base_cost)
        print("- With surge pricing (30%%): $%.2f" % booking.rental_cost)
        print("- Markup: $%.2f" % (booking.rental_cost - base_cost))

def demo_5_return_with_charges():
    print("\n" + "="*70)
    print("DEMO 5: VEHICLE RETURN WITH CHARGES")
    print("="*70)
    
    system = CarRentalSystem()
    
    loc = system.register_location("LOC_SF", "Downtown", "SF")
    vehicle = system.add_vehicle("VH_001", VehicleType.ECONOMY, "SF-1001", "LOC_SF")
    system.register_customer("CUST_001", "Charlie", "charlie@example.com")
    system.add_observer(SystemLogNotifier())
    
    pickup = datetime.now()
    dropoff = pickup + timedelta(days=3)
    
    success, booking = system.create_booking("CUST_001", "VH_001", "LOC_SF", pickup, dropoff)
    print("- Booking created: %s" % booking.booking_id)
    print("  Rental cost: $%.2f" % booking.rental_cost)
    
    system.pickup_vehicle(booking.booking_id)
    print("- Vehicle picked up")
    
    print("\nReturning vehicle...")
    print("  Fuel level: 40%% (needs $30 fuel charge)")
    print("  Damage reported: Yes ($200 damage charge)")
    
    success, charges = system.return_vehicle(booking.booking_id, fuel_level=40.0, 
                                            damage=True, damage_amount=200.0)
    
    if success:
        print("\n- Vehicle returned")
        print("  Rental cost:   $%.2f" % charges['rental_cost'])
        print("  Fuel charge:   $%.2f" % charges['fuel_charge'])
        print("  Damage charge: $%.2f" % charges['damage_charge'])
        print("  ---------------------")
        print("  Total cost:    $%.2f" % charges['total_cost'])
        print("\n  Vehicle status: %s" % vehicle.status.name)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CAR RENTAL SYSTEM - INTERVIEW IMPLEMENTATION - 5 DEMOS")
    print("="*70)
    
    demo_1_setup_and_search()
    demo_2_successful_booking()
    demo_3_loyalty_discount()
    demo_4_demand_based_pricing()
    demo_5_return_with_charges()
    
    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
