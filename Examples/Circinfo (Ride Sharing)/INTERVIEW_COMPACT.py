#!/usr/bin/env python3
"""
Ride-Sharing System - Complete Working Implementation
Run this file to see all 5 demo scenarios in action
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import List, Optional
import threading
import math
import time


# ===== ENUMS =====

class VehicleType(Enum):
    ECONOMY = "economy"
    PREMIUM = "premium"
    SHARED = "shared"


class RideStatus(Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ===== LOCATION =====

class Location:
    """Geographic location with distance calculation"""
    def __init__(self, latitude: float, longitude: float, address: str):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance using Haversine formula (in km)"""
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Earth radius in km
    
    def __str__(self):
        return "%s (%.4f, %.4f)" % (self.address, self.latitude, self.longitude)


# ===== VEHICLE & DRIVER =====

class Vehicle:
    """Vehicle with type and capacity"""
    def __init__(self, vehicle_id: str, model: str, vehicle_type: VehicleType, 
                 registration: str, capacity: int):
        self.vehicle_id = vehicle_id
        self.model = model
        self.vehicle_type = vehicle_type
        self.registration = registration
        self.capacity = capacity
        self.current_location = None


class Driver:
    """Driver with availability and ratings"""
    def __init__(self, driver_id: str, name: str, phone: str, vehicle: Vehicle):
        self.driver_id = driver_id
        self.name = name
        self.phone = phone
        self.vehicle = vehicle
        self.current_location = None
        self.is_available = True
        self.total_rides = 0
        self.total_rating = 0.0
        self.rides_rated = 0
        self.earnings = 0.0
    
    def get_average_rating(self) -> float:
        """Calculate average driver rating"""
        if self.rides_rated == 0:
            return 5.0  # Default for new drivers
        return self.total_rating / self.rides_rated
    
    def update_location(self, location: Location):
        """Update driver's current location"""
        self.current_location = location
        self.vehicle.current_location = location
    
    def accept_ride(self, ride: 'Ride'):
        """Accept a ride request"""
        ride.accept_ride(self)
        self.is_available = False
    
    def __str__(self):
        return "%s (%s) - Rating: %.1f/5.0" % (
            self.name, self.vehicle.model, self.get_average_rating())


# ===== RIDER =====

class Rider:
    """Rider with wallet and ratings"""
    def __init__(self, rider_id: str, name: str, phone: str):
        self.rider_id = rider_id
        self.name = name
        self.phone = phone
        self.wallet_balance = 500.0  # Initial balance
        self.total_rides = 0
        self.total_spent = 0.0
        self.total_rating = 0.0
        self.rides_rated = 0
    
    def get_average_rating(self) -> float:
        """Calculate average rider rating"""
        if self.rides_rated == 0:
            return 5.0
        return self.total_rating / self.rides_rated
    
    def can_afford_ride(self, amount: float) -> bool:
        """Check if rider can afford the fare"""
        return self.wallet_balance >= amount
    
    def deduct_payment(self, amount: float) -> bool:
        """Deduct fare from wallet"""
        if self.can_afford_ride(amount):
            self.wallet_balance -= amount
            self.total_spent += amount
            self.total_rides += 1
            return True
        return False
    
    def add_funds(self, amount: float):
        """Add funds to wallet"""
        self.wallet_balance += amount
    
    def __str__(self):
        return "%s - Balance: $%.2f, Rating: %.1f/5.0" % (
            self.name, self.wallet_balance, self.get_average_rating())


# ===== RIDE (STATE PATTERN) =====

class Ride:
    """Ride with lifecycle state management"""
    def __init__(self, ride_id: str, rider: Rider, pickup: Location, 
                 dropoff: Location, vehicle_type: VehicleType):
        self.ride_id = ride_id
        self.rider = rider
        self.driver = None
        self.pickup_location = pickup
        self.dropoff_location = dropoff
        self.vehicle_type = vehicle_type
        self.status = RideStatus.REQUESTED
        self.requested_time = datetime.now()
        self.accepted_time = None
        self.started_time = None
        self.completed_time = None
        self.estimated_distance = pickup.distance_to(dropoff)
        self.actual_distance = 0.0
        self.estimated_fare = 0.0
        self.actual_fare = 0.0
        self.driver_rating = None
        self.rider_rating = None
    
    def accept_ride(self, driver: Driver):
        """Transition: REQUESTED -> ACCEPTED"""
        if self.status != RideStatus.REQUESTED:
            raise ValueError("Cannot accept ride with status %s" % self.status.value)
        self.driver = driver
        self.status = RideStatus.ACCEPTED
        self.accepted_time = datetime.now()
    
    def start_ride(self):
        """Transition: ACCEPTED -> IN_PROGRESS"""
        if self.status != RideStatus.ACCEPTED:
            raise ValueError("Cannot start ride with status %s" % self.status.value)
        self.status = RideStatus.IN_PROGRESS
        self.started_time = datetime.now()
    
    def complete_ride(self, final_location: Location):
        """Transition: IN_PROGRESS -> COMPLETED"""
        if self.status != RideStatus.IN_PROGRESS:
            raise ValueError("Cannot complete ride with status %s" % self.status.value)
        self.status = RideStatus.COMPLETED
        self.completed_time = datetime.now()
        self.actual_distance = self.pickup_location.distance_to(final_location)
    
    def cancel_ride(self):
        """Cancel ride at any state"""
        self.status = RideStatus.CANCELLED


# ===== PRICING STRATEGY =====

class PricingStrategy(ABC):
    """Abstract pricing strategy"""
    @abstractmethod
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        pass


class FixedPricing(PricingStrategy):
    """Fixed pricing: base + per-km rate"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * demand_multiplier


class SurgePricing(PricingStrategy):
    """Surge pricing during high demand"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        # demand_multiplier ranges from 1.0 to 3.0+
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * max(1.0, demand_multiplier)


class PeakHourPricing(PricingStrategy):
    """Peak hour pricing (rush hours)"""
    BASE_FARE = 2.0
    PER_KM_RATE = 1.5
    PEAK_MULTIPLIER = 1.5  # 50% increase
    
    def calculate_fare(self, distance: float, demand_multiplier: float = 1.0) -> float:
        current_hour = datetime.now().hour
        is_peak = current_hour in [7, 8, 9, 17, 18, 19]  # Morning/evening rush
        
        multiplier = self.PEAK_MULTIPLIER if is_peak else 1.0
        multiplier *= demand_multiplier
        
        fare = self.BASE_FARE + (distance * self.PER_KM_RATE)
        return fare * multiplier


# ===== MATCHING STRATEGY =====

class MatchingStrategy(ABC):
    """Abstract matching strategy"""
    @abstractmethod
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        pass


class NearestDriverMatcher(MatchingStrategy):
    """Match with nearest available driver"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type]
        
        if not matching_drivers:
            return None
        
        # Return nearest driver
        return min(matching_drivers, 
                  key=lambda d: d.current_location.distance_to(ride.pickup_location))


class RatingBasedMatcher(MatchingStrategy):
    """Match with highest-rated driver (within acceptable distance)"""
    def find_driver(self, ride: Ride, available_drivers: List[Driver]) -> Optional[Driver]:
        if not available_drivers:
            return None
        
        # Filter by vehicle type and max distance (5km)
        matching_drivers = [d for d in available_drivers 
                           if d.vehicle.vehicle_type == ride.vehicle_type
                           and d.current_location.distance_to(ride.pickup_location) <= 5.0]
        
        if not matching_drivers:
            return None
        
        # Return highest-rated driver
        return max(matching_drivers, key=lambda d: d.get_average_rating())


# ===== OBSERVER PATTERN =====

class RideObserver(ABC):
    """Observer interface for ride events"""
    @abstractmethod
    def update(self, event: str, ride: Ride, message: str):
        pass


class RiderNotifier(RideObserver):
    """Notify rider of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        print("  [RIDER] %s: %s" % (ride.rider.name, message))


class DriverNotifier(RideObserver):
    """Notify driver of ride events"""
    def update(self, event: str, ride: Ride, message: str):
        if ride.driver:
            print("  [DRIVER] %s: %s" % (ride.driver.name, message))


class AdminNotifier(RideObserver):
    """Notify admin of critical events"""
    def update(self, event: str, ride: Ride, message: str):
        if event in ["payment_failed", "no_driver", "ride_cancelled", "insufficient_funds"]:
            print("  [ADMIN] Ride %s: %s" % (ride.ride_id, message))


# ===== SINGLETON - RIDE SHARING SYSTEM =====

class RideSharingSystem:
    """Singleton controller for ride-sharing platform"""
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
            self.drivers = {}
            self.riders = {}
            self.rides = {}
            self.active_rides = []
            self.completed_rides = []
            self.observers = []
            self.pricing_strategy = SurgePricing()
            self.matching_strategy = NearestDriverMatcher()
            self.demand_multiplier = 1.0
            self.ride_counter = 0
            self.lock = threading.Lock()
            self.initialized = True
    
    def register_driver(self, driver: Driver):
        """Register a new driver"""
        self.drivers[driver.driver_id] = driver
    
    def register_rider(self, rider: Rider):
        """Register a new rider"""
        self.riders[rider.rider_id] = rider
    
    def add_observer(self, observer: RideObserver):
        """Add observer for notifications"""
        self.observers.append(observer)
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Change pricing strategy at runtime"""
        self.pricing_strategy = strategy
    
    def set_matching_strategy(self, strategy: MatchingStrategy):
        """Change matching strategy at runtime"""
        self.matching_strategy = strategy
    
    def update_demand_multiplier(self):
        """Update demand multiplier based on active rides vs available drivers"""
        available_count = len([d for d in self.drivers.values() if d.is_available])
        if available_count == 0:
            self.demand_multiplier = 3.0
            return
        
        active_count = len(self.active_rides)
        ratio = active_count / max(available_count, 1)
        
        if ratio < 0.5:
            self.demand_multiplier = 1.0
        elif ratio < 1.0:
            self.demand_multiplier = 1.5
        else:
            self.demand_multiplier = 2.0
    
    def request_ride(self, rider: Rider, pickup: Location, 
                    dropoff: Location, vehicle_type: VehicleType) -> Optional[Ride]:
        """Rider requests a ride"""
        with self.lock:
            # Update demand multiplier
            self.update_demand_multiplier()
            
            # Create ride
            self.ride_counter += 1
            ride_id = "RIDE_%05d" % self.ride_counter
            ride = Ride(ride_id, rider, pickup, dropoff, vehicle_type)
            
            # Calculate estimated fare
            ride.estimated_fare = self.pricing_strategy.calculate_fare(
                ride.estimated_distance, self.demand_multiplier)
            
            # Check affordability
            if not rider.can_afford_ride(ride.estimated_fare):
                self._notify_observers("insufficient_funds", ride, 
                    "Insufficient balance. Required: $%.2f, Available: $%.2f" % 
                    (ride.estimated_fare, rider.wallet_balance))
                return None
            
            # Find and assign driver
            available_drivers = [d for d in self.drivers.values() 
                               if d.is_available and d.current_location]
            matched_driver = self.matching_strategy.find_driver(ride, available_drivers)
            
            if not matched_driver:
                self._notify_observers("no_driver", ride, "No driver available")
                return None
            
            # Auto-accept (for demo)
            matched_driver.accept_ride(ride)
            self.rides[ride_id] = ride
            self.active_rides.append(ride)
            
            self._notify_observers("ride_accepted", ride, 
                "Driver %s accepted. Distance: %.1fkm, Fare: $%.2f (%.1fx surge)" % 
                (matched_driver.name, matched_driver.current_location.distance_to(pickup),
                 ride.estimated_fare, self.demand_multiplier))
            
            return ride
    
    def start_ride(self, ride: Ride):
        """Start a ride"""
        ride.start_ride()
        self._notify_observers("ride_started", ride, "Ride started from %s" % ride.pickup_location.address)
    
    def complete_ride(self, ride: Ride, final_location: Location, 
                     driver_rating: int, rider_rating: int) -> bool:
        """Complete ride with payment and ratings"""
        with self.lock:
            ride.complete_ride(final_location)
            ride.actual_fare = self.pricing_strategy.calculate_fare(
                ride.actual_distance, self.demand_multiplier)
            
            # Process payment
            if ride.rider.deduct_payment(ride.actual_fare):
                ride.driver.earnings += ride.actual_fare * 0.75  # Driver gets 75%
                ride.driver.total_rides += 1
                
                # Add ratings
                if 1 <= driver_rating <= 5:
                    ride.driver_rating = driver_rating
                    ride.driver.total_rating += driver_rating
                    ride.driver.rides_rated += 1
                
                if 1 <= rider_rating <= 5:
                    ride.rider_rating = rider_rating
                    ride.rider.total_rating += rider_rating
                    ride.rider.rides_rated += 1
                
                ride.driver.is_available = True
                self.active_rides.remove(ride)
                self.completed_rides.append(ride)
                
                self._notify_observers("ride_completed", ride,
                    "Completed. Distance: %.1fkm, Fare: $%.2f, Ratings: D=%d/5, R=%d/5" % 
                    (ride.actual_distance, ride.actual_fare, driver_rating, rider_rating))
                
                return True
            else:
                self._notify_observers("payment_failed", ride, "Payment failed: Insufficient balance")
                return False
    
    def _notify_observers(self, event: str, ride: Ride, message: str):
        """Notify all observers"""
        for observer in self.observers:
            observer.update(event, ride, message)
    
    def get_system_stats(self):
        """Get system statistics"""
        return {
            'total_drivers': len(self.drivers),
            'available_drivers': len([d for d in self.drivers.values() if d.is_available]),
            'total_riders': len(self.riders),
            'active_rides': len(self.active_rides),
            'completed_rides': len(self.completed_rides),
            'demand_multiplier': self.demand_multiplier
        }


# ===== DEMO SCENARIOS =====

def print_section(title):
    """Print section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def demo1_setup():
    """Demo 1: Setup & Registration"""
    print_section("DEMO 1: Setup & Registration")
    
    system = RideSharingSystem()
    
    # Add observers
    system.add_observer(RiderNotifier())
    system.add_observer(DriverNotifier())
    system.add_observer(AdminNotifier())
    
    # Register drivers
    v1 = Vehicle("V001", "Toyota Corolla", VehicleType.ECONOMY, "ABC123", 4)
    d1 = Driver("D001", "Alice", "111-1111", v1)
    d1.update_location(Location(37.7749, -122.4194, "San Francisco Downtown"))
    system.register_driver(d1)
    
    v2 = Vehicle("V002", "Tesla Model S", VehicleType.PREMIUM, "XYZ789", 4)
    d2 = Driver("D002", "Bob", "222-2222", v2)
    d2.update_location(Location(37.7849, -122.4094, "Financial District"))
    system.register_driver(d2)
    
    v3 = Vehicle("V003", "Honda Civic", VehicleType.ECONOMY, "DEF456", 4)
    d3 = Driver("D003", "Charlie", "333-3333", v3)
    d3.update_location(Location(37.7649, -122.4294, "Mission District"))
    system.register_driver(d3)
    
    # Register riders
    r1 = Rider("R001", "Emma", "444-4444")
    system.register_rider(r1)
    
    r2 = Rider("R002", "Frank", "555-5555")
    system.register_rider(r2)
    
    print("\nRegistered Drivers:")
    for driver in system.drivers.values():
        print("  - %s at %s" % (driver, driver.current_location))
    
    print("\nRegistered Riders:")
    for rider in system.riders.values():
        print("  - %s" % rider)
    
    stats = system.get_system_stats()
    print("\nSystem Stats:")
    for key, value in stats.items():
        print("  %s: %s" % (key, value))


def demo2_successful_ride():
    """Demo 2: Successful Ride with Payment and Ratings"""
    print_section("DEMO 2: Successful Ride with Payment and Ratings")
    
    system = RideSharingSystem()
    rider = system.riders["R001"]
    
    pickup = Location(37.7849, -122.4194, "Union Square")
    dropoff = Location(37.8049, -122.4294, "North Beach")
    
    print("\n1. Requesting ride...")
    print("   Pickup: %s" % pickup)
    print("   Dropoff: %s" % dropoff)
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if ride:
        print("\n2. Starting ride...")
        system.start_ride(ride)
        
        print("\n3. Completing ride...")
        system.complete_ride(ride, dropoff, driver_rating=5, rider_rating=4)
        
        print("\n4. Updated balances:")
        print("   Rider balance: $%.2f (spent $%.2f)" % (rider.wallet_balance, ride.actual_fare))
        print("   Driver earnings: $%.2f" % ride.driver.earnings)
        print("   Driver rating: %.1f/5.0" % ride.driver.get_average_rating())


def demo3_surge_pricing():
    """Demo 3: Surge Pricing During High Demand"""
    print_section("DEMO 3: Surge Pricing During High Demand")
    
    system = RideSharingSystem()
    
    # Create multiple active rides to trigger surge
    print("\n1. Creating 15 active rides to simulate high demand...")
    
    # Create temporary drivers and riders
    for i in range(15):
        v = Vehicle("V%03d" % (100+i), "Car %d" % i, VehicleType.ECONOMY, "TMP%03d" % i, 4)
        d = Driver("D%03d" % (100+i), "Driver %d" % i, "999-999%d" % i, v)
        d.update_location(Location(37.7 + i*0.01, -122.4 + i*0.01, "Location %d" % i))
        system.register_driver(d)
        
        r = Rider("R%03d" % (100+i), "Rider %d" % i, "888-888%d" % i)
        system.register_rider(r)
        
        # Request ride (auto-accepted)
        pickup = Location(37.7 + i*0.01, -122.4 + i*0.01, "Pickup %d" % i)
        dropoff = Location(37.7 + i*0.01 + 0.1, -122.4 + i*0.01, "Dropoff %d" % i)
        ride = system.request_ride(r, pickup, dropoff, VehicleType.ECONOMY)
        if ride:
            system.start_ride(ride)  # Start to keep active
    
    print("   Active rides: %d" % len(system.active_rides))
    print("   Available drivers: %d" % len([d for d in system.drivers.values() if d.is_available]))
    
    # Update surge
    system.update_demand_multiplier()
    print("   Surge multiplier: %.1fx" % system.demand_multiplier)
    
    # New rider requests ride
    print("\n2. New rider requesting ride during surge...")
    rider = system.riders["R002"]
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.7949, -122.4394, "Marina")
    
    base_fare = FixedPricing().calculate_fare(pickup.distance_to(dropoff), 1.0)
    print("   Base fare (no surge): $%.2f" % base_fare)
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    if ride:
        print("   Surge fare (%.1fx): $%.2f" % (system.demand_multiplier, ride.estimated_fare))
        print("   Difference: $%.2f (%.0f%% increase)" % 
              (ride.estimated_fare - base_fare, (system.demand_multiplier - 1) * 100))


def demo4_rating_based_matching():
    """Demo 4: Rating-Based Driver Matching"""
    print_section("DEMO 4: Rating-Based Driver Matching")
    
    system = RideSharingSystem()
    
    # Give drivers different ratings
    print("\n1. Setting up drivers with different ratings...")
    
    # Complete some rides to build ratings
    drivers = list(system.drivers.values())[:3]
    
    # Alice: 5 stars (2 rides)
    drivers[0].total_rating = 10.0
    drivers[0].rides_rated = 2
    drivers[0].is_available = True
    
    # Bob: 3 stars (2 rides)
    drivers[1].total_rating = 6.0
    drivers[1].rides_rated = 2
    drivers[1].is_available = True
    
    # Charlie: 4 stars (2 rides)
    drivers[2].total_rating = 8.0
    drivers[2].rides_rated = 2
    drivers[2].is_available = True
    
    for d in drivers:
        print("   %s - Rating: %.1f/5.0" % (d.name, d.get_average_rating()))
    
    # Switch to rating-based matching
    print("\n2. Switching to Rating-Based Matcher...")
    system.set_matching_strategy(RatingBasedMatcher())
    
    print("\n3. Requesting ride (should match highest-rated driver)...")
    rider = system.riders["R001"]
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.7949, -122.4394, "Uptown")
    
    ride = system.request_ride(rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if ride:
        print("\n   Matched Driver: %s (Rating: %.1f/5.0)" % 
              (ride.driver.name, ride.driver.get_average_rating()))
        
        # Complete with 5-star rating
        system.start_ride(ride)
        system.complete_ride(ride, dropoff, driver_rating=5, rider_rating=5)
        
        print("   Updated Rating: %.1f/5.0" % ride.driver.get_average_rating())


def demo5_insufficient_balance():
    """Demo 5: Insufficient Balance Scenario"""
    print_section("DEMO 5: Insufficient Balance Scenario")
    
    system = RideSharingSystem()
    
    # Create rider with low balance
    low_balance_rider = Rider("R999", "Poor Pete", "999-9999")
    low_balance_rider.wallet_balance = 3.0  # Very low balance
    system.register_rider(low_balance_rider)
    
    print("\n1. Rider with low balance: $%.2f" % low_balance_rider.wallet_balance)
    
    # Request long ride (expensive)
    pickup = Location(37.7749, -122.4194, "Downtown")
    dropoff = Location(37.8749, -122.5194, "Far Suburb")  # 15km+ away
    
    distance = pickup.distance_to(dropoff)
    estimated_fare = system.pricing_strategy.calculate_fare(distance, system.demand_multiplier)
    
    print("2. Requesting ride...")
    print("   Distance: %.1f km" % distance)
    print("   Estimated fare: $%.2f" % estimated_fare)
    print("   Available balance: $%.2f" % low_balance_rider.wallet_balance)
    
    print("\n3. Attempting to book...")
    ride = system.request_ride(low_balance_rider, pickup, dropoff, VehicleType.ECONOMY)
    
    if not ride:
        print("\n4. Ride request failed (insufficient funds)")
        print("   Need to add: $%.2f to wallet" % (estimated_fare - low_balance_rider.wallet_balance))


# ===== MAIN =====

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RIDE-SHARING SYSTEM - COMPLETE DEMONSTRATION")
    print("="*60)
    
    demo1_setup()
    time.sleep(1)
    
    demo2_successful_ride()
    time.sleep(1)
    
    demo3_surge_pricing()
    time.sleep(1)
    
    demo4_rating_based_matching()
    time.sleep(1)
    
    demo5_insufficient_balance()
    
    print("\n" + "="*60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nKey Patterns Demonstrated:")
    print("1. Singleton: RideSharingSystem (one instance)")
    print("2. Strategy: 3 Pricing algorithms (Fixed/Surge/PeakHour)")
    print("3. Strategy: 2 Matching algorithms (Nearest/RatingBased)")
    print("4. Observer: 3 Notifiers (Rider/Driver/Admin)")
    print("5. State: Ride lifecycle (REQUESTED->ACCEPTED->IN_PROGRESS->COMPLETED)")
    print("\nRun 'python3 INTERVIEW_COMPACT.py' to see all demos")
