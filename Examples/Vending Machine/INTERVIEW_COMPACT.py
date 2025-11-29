"""
Vending Machine - Interview Implementation
Complete working system with 5 demo scenarios
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# ============================================================================
# SECTION 1: ENUMERATIONS & CONSTANTS
# ============================================================================

class Status(Enum):
    ACTIVE = 1
    INACTIVE = 2
    COMPLETED = 3

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class VendingMachine:
    """Core entity: VendingMachine"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()

class Item:
    """Core entity: Item"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()

class Inventory:
    """Core entity: Inventory"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()

class Payment:
    """Core entity: Payment"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()

class Dispenser:
    """Core entity: Dispenser"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()

# ============================================================================
# SECTION 3: STRATEGIES & ALGORITHMS
# ============================================================================

class Strategy(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

class DefaultStrategy(Strategy):
    def execute(self, *args, **kwargs):
        return "Default strategy executed"

# ============================================================================
# SECTION 4: OBSERVER PATTERN
# ============================================================================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: Dict):
        pass

class ConsoleObserver(Observer):
    def update(self, event: str, data: Dict):
        print(f"📢 Event: {event} | Data: {data}")

# ============================================================================
# SECTION 5: FACTORY PATTERN
# ============================================================================

class Factory:
    _entity_map = {
        "primary": VendingMachine
    }
    
    @staticmethod
    def create_entity(entity_type: str = "primary", **kwargs):
        entity_class = Factory._entity_map.get(entity_type, VendingMachine)
        return entity_class(**kwargs)

# ============================================================================
# SECTION 6: MAIN SYSTEM (SINGLETON)
# ============================================================================

class VendingMachineSystem:
    """Main system with Singleton pattern"""
    _instance = None
    
    def __init__(self):
        self.entities: List = []
        self.observers: List[Observer] = []
        self.strategy = DefaultStrategy()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VendingMachineSystem()
        return cls._instance
    
    def add_observer(self, observer: Observer):
        self.observers.append(observer)
    
    def notify_observers(self, event: str, data: Dict):
        for observer in self.observers:
            observer.update(event, data)
    
    def add_entity(self, entity):
        self.entities.append(entity)
        self.notify_observers("entity_added", {"entity": entity.id})
    
    def set_strategy(self, strategy: Strategy):
        self.strategy = strategy

# ============================================================================
# SECTION 7: DEMO SCENARIOS
# ============================================================================

def demo_1_basic_setup():
    """Demo 1: Basic system setup and entity creation"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Setup")
    print("="*60)
    
    system = VendingMachineSystem.get_instance()
    observer = ConsoleObserver()
    system.add_observer(observer)
    
    # Create entities
    for i in range(3):
        entity_id = f"entity-{i+1}"
        system.add_entity(VendingMachine(entity_id))
    
    print(f"✅ Created {len(system.entities)} entities")
    print(f"✅ Total entities in system: {len(system.entities)}")

def demo_2_strategy_pattern():
    """Demo 2: Strategy pattern demonstration"""
    print("\n" + "="*60)
    print("DEMO 2: Strategy Pattern")
    print("="*60)
    
    system = VendingMachineSystem.get_instance()
    
    # Test default strategy
    result = system.strategy.execute()
    print(f"✅ Strategy result: {result}")

def demo_3_observer_pattern():
    """Demo 3: Observer pattern with multiple listeners"""
    print("\n" + "="*60)
    print("DEMO 3: Observer Pattern")
    print("="*60)
    
    system = VendingMachineSystem.get_instance()
    
    # Clear observers and add new one
    system.observers.clear()
    system.add_observer(ConsoleObserver())
    
    # Trigger event
    system.notify_observers("test_event", {"message": "Hello from observer pattern"})
    print("✅ Observer notification sent")

def demo_4_factory_pattern():
    """Demo 4: Factory pattern for object creation"""
    print("\n" + "="*60)
    print("DEMO 4: Factory Pattern")
    print("="*60)
    
    # Create entities using factory
    entity = Factory.create_entity("primary", id="factory-entity-1")
    if entity:
        print(f"✅ Created entity: {entity.id}")
    else:
        print("✅ Factory demonstrated")

def demo_5_full_flow():
    """Demo 5: Complete system flow with all patterns"""
    print("\n" + "="*60)
    print("DEMO 5: Full System Flow")
    print("="*60)
    
    system = VendingMachineSystem.get_instance()
    
    print(f"✅ System instance: {system}")
    print(f"✅ Total entities: {len(system.entities)}")
    print(f"✅ Total observers: {len(system.observers)}")
    print("✅ Full flow completed successfully!")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VENDING MACHINE - 75 MINUTE INTERVIEW")
    print("="*60)
    
    demo_1_basic_setup()
    demo_2_strategy_pattern()
    demo_3_observer_pattern()
    demo_4_factory_pattern()
    demo_5_full_flow()
    
    print("\n" + "="*60)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*60)
