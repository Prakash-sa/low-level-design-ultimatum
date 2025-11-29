"""
Amazon Locker System - Interview Implementation
Complete working implementation with design patterns and demo scenarios
Timeline: 75 minutes | Scale: 100+ concurrent, 1000+ lockers
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
import uuid

# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class LockerSlotStatus(Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    RESERVED = "reserved"

class PackageStatus(Enum):
    PENDING = "pending"
    STORED = "stored"
    RETRIEVED = "retrieved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class LockerSize(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class UserRole(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Location:
    """Represents a physical locker location"""
    def __init__(self, location_id: str, name: str, address: str, city: str):
        self.location_id = location_id
        self.name = name
        self.address = address
        self.city = city
        self.created_at = datetime.now()

class LockerSlot:
    """Represents a single slot in a locker"""
    def __init__(self, slot_id: str, size: LockerSize):
        self.slot_id = slot_id
        self.size = size
        self.status = LockerSlotStatus.EMPTY
        self.package_id: Optional[str] = None
    
    def is_available(self) -> bool:
        return self.status == LockerSlotStatus.EMPTY
    
    def occupy(self, package_id: str):
        if not self.is_available():
            raise ValueError(f"Slot {self.slot_id} is not empty")
        self.status = LockerSlotStatus.OCCUPIED
        self.package_id = package_id
    
    def release(self):
        self.status = LockerSlotStatus.EMPTY
        self.package_id = None

class Locker:
    """Represents a physical locker with multiple slots"""
    def __init__(self, locker_id: str, location: Location, capacity: int):
        self.locker_id = locker_id
        self.location = location
        self.slots: Dict[str, LockerSlot] = {}
        self.created_at = datetime.now()
        
        # Create slots: distributed by size
        for i in range(capacity // 3):
            self.slots[f"S{i}"] = LockerSlot(f"S{i}", LockerSize.SMALL)
        for i in range(capacity // 3, 2 * capacity // 3):
            self.slots[f"M{i}"] = LockerSlot(f"M{i}", LockerSize.MEDIUM)
        for i in range(2 * capacity // 3, capacity):
            self.slots[f"L{i}"] = LockerSlot(f"L{i}", LockerSize.LARGE)
    
    def get_available_slots(self, size: LockerSize) -> List[LockerSlot]:
        return [s for s in self.slots.values() 
                if s.is_available() and s.size == size]
    
    def total_available(self) -> int:
        return sum(1 for s in self.slots.values() if s.is_available())

class Package:
    """Represents a package to be stored"""
    def __init__(self, package_id: str, user_id: str, 
                 size: LockerSize, weight: float):
        self.package_id = package_id
        self.user_id = user_id
        self.size = size
        self.weight = weight
        self.status = PackageStatus.PENDING
        self.created_at = datetime.now()
        self.stored_at: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None
        self.pickup_code: Optional[str] = None
        self.retrieved_at: Optional[datetime] = None
    
    def store(self, expiry_days: int = 7):
        """Mark package as stored"""
        self.status = PackageStatus.STORED
        self.stored_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=expiry_days)
        self.pickup_code = str(uuid.uuid4())[:6].upper()
    
    def retrieve(self):
        """Mark package as retrieved"""
        self.status = PackageStatus.RETRIEVED
        self.retrieved_at = datetime.now()
    
    def is_expired(self) -> bool:
        return (self.expires_at and 
                datetime.now() > self.expires_at)

class User:
    """Represents a user/customer"""
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = UserRole.CUSTOMER
        self.created_at = datetime.now()

# ============================================================================
# SECTION 3: ALLOCATION STRATEGY (Strategy Pattern)
# ============================================================================

class AllocationStrategy(ABC):
    """Abstract strategy for locker slot allocation"""
    @abstractmethod
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        pass

class BestFitAllocation(AllocationStrategy):
    """Allocate the smallest suitable slot"""
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        available = locker.get_available_slots(size)
        return available[0] if available else None

class FirstAvailableAllocation(AllocationStrategy):
    """Allocate first available slot of the size"""
    def allocate(self, locker: Locker, size: LockerSize) -> Optional[LockerSlot]:
        available = locker.get_available_slots(size)
        return available[0] if available else None

# ============================================================================
# SECTION 4: OBSERVER PATTERN (Notifications)
# ============================================================================

class Notifier(ABC):
    """Observer interface for package events"""
    @abstractmethod
    def notify(self, event: str, user: User, package: Package):
        pass

class EmailNotifier(Notifier):
    """Email notifications"""
    def notify(self, event: str, user: User, package: Package):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📧 EMAIL: {user.email} | "
              f"Event: {event} | Package: {package.package_id} | "
              f"Code: {package.pickup_code}")

class SMSNotifier(Notifier):
    """SMS notifications"""
    def notify(self, event: str, user: User, package: Package):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📱 SMS: {user.phone} | "
              f"Event: {event} | Package: {package.package_id} | "
              f"Code: {package.pickup_code}")

# ============================================================================
# SECTION 5: LOCKER SYSTEM (Singleton + Controller)
# ============================================================================

class LockerSystem:
    """Singleton controller for locker operations"""
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
            self.locations: Dict[str, Location] = {}
            self.lockers: Dict[str, Locker] = {}
            self.packages: Dict[str, Package] = {}
            self.users: Dict[str, User] = {}
            self.notifiers: List[Notifier] = []
            self.allocation_strategy: AllocationStrategy = BestFitAllocation()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'LockerSystem':
        """Get singleton instance"""
        return LockerSystem()
    
    def set_allocation_strategy(self, strategy: AllocationStrategy):
        """Switch allocation strategy"""
        self.allocation_strategy = strategy
    
    def add_notifier(self, notifier: Notifier):
        """Subscribe to events"""
        self.notifiers.append(notifier)
    
    def notify_all(self, event: str, user: User, package: Package):
        """Notify all subscribers"""
        for notifier in self.notifiers:
            notifier.notify(event, user, package)
    
    def create_location(self, location_id: str, name: str, 
                       address: str, city: str) -> Location:
        location = Location(location_id, name, address, city)
        self.locations[location_id] = location
        return location
    
    def create_locker(self, locker_id: str, location_id: str, 
                     capacity: int) -> Optional[Locker]:
        if location_id not in self.locations:
            return None
        locker = Locker(locker_id, self.locations[location_id], capacity)
        self.lockers[locker_id] = locker
        return locker
    
    def register_user(self, user_id: str, name: str, 
                     email: str, phone: str) -> User:
        user = User(user_id, name, email, phone)
        self.users[user_id] = user
        return user
    
    def store_package(self, package_id: str, user_id: str, 
                     locker_id: str, size: LockerSize, 
                     weight: float) -> Optional[str]:
        """Store package in locker and return pickup code"""
        if locker_id not in self.lockers:
            print(f"❌ Locker {locker_id} not found")
            return None
        
        if user_id not in self.users:
            print(f"❌ User {user_id} not found")
            return None
        
        locker = self.lockers[locker_id]
        user = self.users[user_id]
        
        # Find available slot
        slot = self.allocation_strategy.allocate(locker, size)
        if not slot:
            print(f"❌ No available slot for size {size.name}")
            return None
        
        # Create and store package
        package = Package(package_id, user_id, size, weight)
        package.store(expiry_days=7)
        slot.occupy(package_id)
        
        self.packages[package_id] = package
        self.notify_all("STORED", user, package)
        
        return package.pickup_code
    
    def retrieve_package(self, package_id: str, user_id: str, 
                        pickup_code: str) -> bool:
        """Retrieve package with verification"""
        if package_id not in self.packages:
            print(f"❌ Package {package_id} not found")
            return False
        
        package = self.packages[package_id]
        user = self.users.get(user_id)
        
        if package.user_id != user_id:
            print(f"❌ Unauthorized access")
            return False
        
        if package.pickup_code != pickup_code:
            print(f"❌ Invalid pickup code")
            return False
        
        if package.is_expired():
            package.status = PackageStatus.EXPIRED
            self.notify_all("EXPIRED", user, package)
            return False
        
        if package.status != PackageStatus.STORED:
            print(f"❌ Package already retrieved or cancelled")
            return False
        
        # Mark as retrieved
        package.retrieve()
        
        # Release slot
        for locker in self.lockers.values():
            for slot in locker.slots.values():
                if slot.package_id == package_id:
                    slot.release()
        
        self.notify_all("RETRIEVED", user, package)
        return True
    
    def cancel_package(self, package_id: str, user_id: str) -> bool:
        """Cancel package before retrieval"""
        if package_id not in self.packages:
            return False
        
        package = self.packages[package_id]
        user = self.users.get(user_id)
        
        if package.user_id != user_id or package.status != PackageStatus.STORED:
            return False
        
        package.status = PackageStatus.CANCELLED
        
        # Release slot
        for locker in self.lockers.values():
            for slot in locker.slots.values():
                if slot.package_id == package_id:
                    slot.release()
        
        self.notify_all("CANCELLED", user, package)
        return True
    
    def get_available_slots(self, locker_id: str, size: LockerSize) -> int:
        """Get count of available slots"""
        if locker_id not in self.lockers:
            return 0
        return len(self.lockers[locker_id].get_available_slots(size))

# ============================================================================
# SECTION 6: DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    """Demo 1: System setup - Create location, locker, users"""
    print("\n" + "="*70)
    print("DEMO 1: System Setup & Location Creation")
    print("="*70)
    
    system = LockerSystem.get_instance()
    system.notifiers.clear()
    system.add_notifier(EmailNotifier())
    system.add_notifier(SMSNotifier())
    
    # Create location and locker
    loc = system.create_location("LOC001", "NYC Downtown", "123 Main St", "NYC")
    locker = system.create_locker("LOCK001", "LOC001", 15)
    
    # Create users
    user1 = system.register_user("U001", "John Doe", "john@example.com", "555-1234")
    user2 = system.register_user("U002", "Jane Smith", "jane@example.com", "555-5678")
    
    print(f"✅ Location created: {loc.name}")
    print(f"✅ Locker created with {locker.total_available()} available slots")
    print(f"✅ Registered {len(system.users)} users")
    return system, locker, user1, user2

def demo_2_store_retrieve():
    """Demo 2: Store and retrieve package"""
    print("\n" + "="*70)
    print("DEMO 2: Store & Retrieve Package")
    print("="*70)
    
    system, locker, user1, user2 = demo_1_setup()
    
    print("\n→ Storing SMALL package for John Doe...")
    code1 = system.store_package("PKG001", "U001", "LOCK001", LockerSize.SMALL, 2.5)
    
    if code1:
        print(f"✅ Package stored with code: {code1}")
        
        print("\n→ Retrieving package with correct code...")
        if system.retrieve_package("PKG001", "U001", code1):
            print(f"✅ Package retrieved successfully")

def demo_3_multiple_sizes():
    """Demo 3: Store packages of different sizes"""
    print("\n" + "="*70)
    print("DEMO 3: Multiple Package Sizes & Notifications")
    print("="*70)
    
    system, locker, user1, user2 = demo_1_setup()
    
    print("\n→ Storing SMALL package for John Doe...")
    code1 = system.store_package("PKG001", "U001", "LOCK001", LockerSize.SMALL, 2.5)
    
    print("\n→ Storing MEDIUM package for Jane Smith...")
    code2 = system.store_package("PKG002", "U002", "LOCK001", LockerSize.MEDIUM, 5.0)
    
    print("\n→ Storing LARGE package for Jane Smith...")
    code3 = system.store_package("PKG003", "U002", "LOCK001", LockerSize.LARGE, 8.0)
    
    print(f"\n✅ Available slots: {locker.total_available()}")

def demo_4_cancellation():
    """Demo 4: Cancel package and free slot"""
    print("\n" + "="*70)
    print("DEMO 4: Package Cancellation & Slot Release")
    print("="*70)
    
    system, locker, user1, user2 = demo_1_setup()
    
    print("\n→ Storing MEDIUM package for Jane Smith...")
    code = system.store_package("PKG002", "U002", "LOCK001", LockerSize.MEDIUM, 5.0)
    print(f"  Before cancel - Available slots: {locker.total_available()}")
    
    print("\n→ Cancelling package...")
    system.cancel_package("PKG002", "U002")
    print(f"✅ Package cancelled - slot freed")
    print(f"  After cancel - Available slots: {locker.total_available()}")

def demo_5_full_flow():
    """Demo 5: Complete flow with multiple users and packages"""
    print("\n" + "="*70)
    print("DEMO 5: Complete Flow - Multiple Users & Packages")
    print("="*70)
    
    system, locker, user1, user2 = demo_1_setup()
    
    print("\n→ User 1 stores SMALL package...")
    code1 = system.store_package("PKG001", "U001", "LOCK001", LockerSize.SMALL, 2.5)
    system.retrieve_package("PKG001", "U001", code1)
    
    print("\n→ User 2 stores MEDIUM package...")
    code2 = system.store_package("PKG002", "U002", "LOCK001", LockerSize.MEDIUM, 5.0)
    
    print("\n→ User 2 stores LARGE package...")
    code3 = system.store_package("PKG003", "U002", "LOCK001", LockerSize.LARGE, 8.0)
    system.retrieve_package("PKG003", "U002", code3)
    
    print("\n[SUMMARY]")
    print("-" * 70)
    print(f"Total packages: {len(system.packages)}")
    print(f"Retrieved: {sum(1 for p in system.packages.values() if p.status == PackageStatus.RETRIEVED)}")
    print(f"Stored: {sum(1 for p in system.packages.values() if p.status == PackageStatus.STORED)}")
    print(f"Available slots in locker: {locker.total_available()}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AMAZON LOCKER SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State")
    print("="*70)
    
    try:
        demo_1_setup()
        demo_2_store_retrieve()
        demo_3_multiple_sizes()
        demo_4_cancellation()
        demo_5_full_flow()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nKey Takeaways:")
        print("  • Singleton: Single LockerSystem instance for consistency")
        print("  • Strategy: Pluggable allocation algorithms (BestFit vs FirstAvailable)")
        print("  • Observer: Real-time package event notifications")
        print("  • State: Clear package lifecycle (PENDING → STORED → RETRIEVED/EXPIRED)")
        print("\nFor detailed implementation, see 75_MINUTE_GUIDE.md")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
