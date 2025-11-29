"""
Restaurant Management System - Complete Interview Implementation
=====================================================================
Design Patterns: Singleton | Strategy | Observer | State | Factory | Command
Time Complexity: O(1) state transitions, O(n) billing where n = items
Space Complexity: O(t + m + r + o) tables + menu items + reservations + orders
=====================================================================
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import threading

# ============================================================================
# SECTION 1: ENUMERATIONS (STATE & TYPES)
# ============================================================================

class TableStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"

class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class OrderStatus(Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"

class Category(Enum):
    STARTER = "starter"
    MAIN = "main"
    DRINK = "drink"
    DESSERT = "dessert"

# ============================================================================
# SECTION 2: CORE DOMAIN CLASSES
# ============================================================================

class MenuItem:
    def __init__(self, item_id: str, name: str, category: Category, base_price: float, is_available: bool = True):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.base_price = base_price
        self.is_available = is_available
    
    def mark_unavailable(self):
        self.is_available = False
    
    def get_price(self) -> float:
        return self.base_price
    
    def __str__(self):
        return f"{self.name} (${self.base_price:.2f})"


class Table:
    def __init__(self, table_id: str, capacity: int):
        self.table_id = table_id
        self.capacity = capacity
        self.status = TableStatus.AVAILABLE
    
    def reserve(self) -> bool:
        if self.status != TableStatus.AVAILABLE:
            return False
        self.status = TableStatus.RESERVED
        return True
    
    def occupy(self) -> bool:
        if self.status not in [TableStatus.RESERVED, TableStatus.AVAILABLE]:
            return False
        self.status = TableStatus.OCCUPIED
        return True
    
    def release(self) -> bool:
        self.status = TableStatus.AVAILABLE
        return True
    
    def __str__(self):
        return f"Table {self.table_id} ({self.capacity} seats) - {self.status.value}"


class Customer:
    def __init__(self, customer_id: str, name: str, contact: str):
        self.customer_id = customer_id
        self.name = name
        self.contact = contact
    
    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class Reservation:
    def __init__(self, reservation_id: str, customer: Customer, table: Table, time: datetime):
        self.reservation_id = reservation_id
        self.customer = customer
        self.table = table
        self.time = time
        self.status = ReservationStatus.PENDING
        self.created_at = datetime.now()
    
    def confirm(self) -> bool:
        if self.status != ReservationStatus.PENDING:
            return False
        if not self.table.reserve():  # ensure table can be reserved
            return False
        self.status = ReservationStatus.CONFIRMED
        return True
    
    def cancel(self) -> bool:
        if self.status == ReservationStatus.CANCELLED:
            return False
        self.status = ReservationStatus.CANCELLED
        # release table if it was confirmed
        if self.table.status == TableStatus.RESERVED:
            self.table.release()
        return True
    
    def __str__(self):
        return f"Reservation {self.reservation_id} for Table {self.table.table_id} - {self.status.value}"


class OrderItem:
    def __init__(self, menu_item: MenuItem, quantity: int):
        self.menu_item = menu_item
        self.quantity = quantity
        self.final_price = 0.0  # filled during bill calculation
    
    def line_subtotal(self) -> float:
        return self.menu_item.base_price * self.quantity
    
    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity} (${self.line_subtotal():.2f})"


class Order:
    def __init__(self, order_id: str, table: Table):
        self.order_id = order_id
        self.table = table
        self.items: List[OrderItem] = []
        self.status = OrderStatus.RECEIVED
        self.subtotal = 0.0
        self.bill_total = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_item(self, order_item: OrderItem) -> bool:
        if self.status in [OrderStatus.READY, OrderStatus.SERVED, OrderStatus.CANCELLED]:
            return False
        if not order_item.menu_item.is_available:
            return False
        self.items.append(order_item)
        return True
    
    def update_status(self, new_status: OrderStatus) -> bool:
        valid_transitions = {
            OrderStatus.RECEIVED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.SERVED],
            OrderStatus.SERVED: [],
            OrderStatus.CANCELLED: []
        }
        if new_status in valid_transitions[self.status]:
            self.status = new_status
            self.updated_at = datetime.now()
            return True
        return False
    
    def calculate_totals(self, pricing_strategy: 'PricingStrategy'):
        self.subtotal = sum(item.line_subtotal() for item in self.items)
        context = {
            'items': self.items,
            'table_id': self.table.table_id,
            'hour': datetime.now().hour
        }
        self.bill_total = pricing_strategy.apply(self.subtotal, context)
        return self.bill_total
    
    def __str__(self):
        return f"Order {self.order_id} ({self.status.value}) - {len(self.items)} items"


class KitchenTicket:
    def __init__(self, ticket_id: str, order: Order):
        self.ticket_id = ticket_id
        self.order = order
        self.queued_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def start(self):
        if self.order.status == OrderStatus.RECEIVED:
            self.order.update_status(OrderStatus.PREPARING)
            self.started_at = datetime.now()
            return True
        return False
    
    def complete(self):
        if self.order.status == OrderStatus.PREPARING:
            self.order.update_status(OrderStatus.READY)
            self.completed_at = datetime.now()
            return True
        return False
    
    def __str__(self):
        return f"Ticket {self.ticket_id} for {self.order.order_id} - {self.order.status.value}"


class Payment:
    def __init__(self, payment_id: str, order: Order, amount: float, method: PaymentMethod):
        self.payment_id = payment_id
        self.order = order
        self.amount = amount
        self.method = method
        self.timestamp = datetime.now()
        self.success = False
    
    def process(self) -> bool:
        if self.order.status != OrderStatus.SERVED:
            return False
        # Simplified success
        self.success = True
        return True
    
    def __str__(self):
        return f"Payment {self.payment_id} ${self.amount:.2f} via {self.method.value} ({'OK' if self.success else 'PENDING'})"


# ============================================================================
# SECTION 3: STRATEGY PATTERN (Pricing)
# ============================================================================

class PricingStrategy(ABC):
    @abstractmethod
    def apply(self, subtotal: float, context: Dict) -> float:
        pass

class BasePricingStrategy(PricingStrategy):
    def apply(self, subtotal: float, context: Dict) -> float:
        return round(subtotal, 2)

class HappyHourPricingStrategy(PricingStrategy):
    def __init__(self, discount_percent: float = 0.20, start_hour: int = 16, end_hour: int = 18):
        self.discount_percent = discount_percent
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def apply(self, subtotal: float, context: Dict) -> float:
        hour = context.get('hour', 0)
        if self.start_hour <= hour < self.end_hour:
            # Discount only on drinks lines
            drink_sub = sum(i.line_subtotal() for i in context['items'] if i.menu_item.category == Category.DRINK)
            discount = drink_sub * self.discount_percent
            return round(subtotal - discount, 2)
        return round(subtotal, 2)

class ServiceChargePricingStrategy(PricingStrategy):
    def __init__(self, service_rate: float = 0.10):
        self.service_rate = service_rate
    
    def apply(self, subtotal: float, context: Dict) -> float:
        charge = subtotal * self.service_rate
        return round(subtotal + charge, 2)

class CompositePricingStrategy(PricingStrategy):
    def __init__(self, strategies: List[PricingStrategy]):
        self.strategies = strategies
    
    def apply(self, subtotal: float, context: Dict) -> float:
        total = subtotal
        for strat in self.strategies:
            total = strat.apply(total, context)
        return round(total, 2)

# ============================================================================
# SECTION 4: OBSERVER PATTERN
# ============================================================================

class RestaurantObserver(ABC):
    @abstractmethod
    def update(self, event: str, payload: Dict):
        pass

class ConsoleObserver(RestaurantObserver):
    def update(self, event: str, payload: Dict):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 🔔 {event.upper()}: {payload}")

# ============================================================================
# SECTION 5: FACTORY PATTERN
# ============================================================================

class ReservationFactory:
    _counter = 0
    @staticmethod
    def create(customer: Customer, table: Table, time: datetime) -> Reservation:
        ReservationFactory._counter += 1
        return Reservation(f"RSV{ReservationFactory._counter:04d}", customer, table, time)

class OrderFactory:
    _counter = 0
    @staticmethod
    def create(table: Table) -> Order:
        OrderFactory._counter += 1
        return Order(f"ORD{OrderFactory._counter:05d}", table)

class KitchenTicketFactory:
    _counter = 0
    @staticmethod
    def create(order: Order) -> KitchenTicket:
        KitchenTicketFactory._counter += 1
        return KitchenTicket(f"KT{KitchenTicketFactory._counter:04d}", order)

class PaymentFactory:
    _counter = 0
    @staticmethod
    def create(order: Order, amount: float, method: PaymentMethod) -> Payment:
        PaymentFactory._counter += 1
        return Payment(f"PAY{PaymentFactory._counter:05d}", order, amount, method)

# ============================================================================
# SECTION 6: COMMAND PATTERN
# ============================================================================

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class CreateReservationCommand(Command):
    def __init__(self, system: 'RestaurantSystem', customer: Customer, table: Table, time: datetime):
        self.system = system
        self.customer = customer
        self.table = table
        self.time = time
    def execute(self) -> Optional[Reservation]:
        return self.system.create_reservation(self.customer, self.table, self.time)

class CancelReservationCommand(Command):
    def __init__(self, reservation: Reservation):
        self.reservation = reservation
    def execute(self) -> bool:
        return self.reservation.cancel()

class PlaceOrderCommand(Command):
    def __init__(self, system: 'RestaurantSystem', table: Table, items: List[Tuple[str, int]]):
        self.system = system
        self.table = table
        self.items = items
    def execute(self) -> Optional[Order]:
        return self.system.place_order(self.table, self.items)

class UpdateOrderStatusCommand(Command):
    def __init__(self, order: Order, new_status: OrderStatus):
        self.order = order
        self.new_status = new_status
    def execute(self) -> bool:
        return self.order.update_status(self.new_status)

class ProcessPaymentCommand(Command):
    def __init__(self, system: 'RestaurantSystem', order: Order, method: PaymentMethod, strategy: PricingStrategy):
        self.system = system
        self.order = order
        self.method = method
        self.strategy = strategy
    def execute(self) -> Optional[Payment]:
        return self.system.process_payment(self.order, self.method, self.strategy)

# ============================================================================
# SECTION 7: SINGLETON SYSTEM
# ============================================================================

class RestaurantSystem:
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
            self.tables: Dict[str, Table] = {}
            self.menu: Dict[str, MenuItem] = {}
            self.reservations: Dict[str, Reservation] = {}
            self.orders: Dict[str, Order] = {}
            self.tickets: Dict[str, KitchenTicket] = {}
            self.payments: Dict[str, Payment] = {}
            self.observers: List[RestaurantObserver] = []
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'RestaurantSystem':
        return RestaurantSystem()
    
    def add_observer(self, observer: RestaurantObserver):
        self.observers.append(observer)
    
    def notify(self, event: str, payload: Dict):
        for obs in self.observers:
            obs.update(event, payload)
    
    # --- Menu & Tables ---
    def add_table(self, table_id: str, capacity: int):
        self.tables[table_id] = Table(table_id, capacity)
    
    def add_menu_item(self, item_id: str, name: str, category: Category, price: float):
        self.menu[item_id] = MenuItem(item_id, name, category, price)
    
    def get_available_table(self, capacity: int) -> Optional[Table]:
        for t in self.tables.values():
            if t.capacity >= capacity and t.status == TableStatus.AVAILABLE:
                return t
        return None
    
    # --- Reservation ---
    def create_reservation(self, customer: Customer, table: Table, time: datetime) -> Optional[Reservation]:
        if table.status != TableStatus.AVAILABLE:
            return None
        reservation = ReservationFactory.create(customer, table, time)
        self.reservations[reservation.reservation_id] = reservation
        self.notify('reservation_created', {'reservation_id': reservation.reservation_id, 'table': table.table_id, 'customer': customer.name})
        return reservation
    
    # --- Orders ---
    def place_order(self, table: Table, items: List[Tuple[str, int]]) -> Optional[Order]:
        if table.status not in [TableStatus.OCCUPIED, TableStatus.RESERVED]:
            return None
        order = OrderFactory.create(table)
        for item_id, qty in items:
            menu_item = self.menu.get(item_id)
            if not menu_item or not menu_item.is_available:
                continue
            order.add_item(OrderItem(menu_item, qty))
        if not order.items:
            return None
        self.orders[order.order_id] = order
        self.notify('order_placed', {'order_id': order.order_id, 'table': table.table_id, 'items': len(order.items)})
        return order
    
    def create_kitchen_ticket(self, order: Order) -> KitchenTicket:
        ticket = KitchenTicketFactory.create(order)
        self.tickets[ticket.ticket_id] = ticket
        self.notify('kitchen_ticket_created', {'ticket_id': ticket.ticket_id, 'order_id': order.order_id})
        return ticket
    
    # --- Payment ---
    def process_payment(self, order: Order, method: PaymentMethod, pricing_strategy: PricingStrategy) -> Optional[Payment]:
        if order.status != OrderStatus.SERVED:
            return None
        total = order.calculate_totals(pricing_strategy)
        payment = PaymentFactory.create(order, total, method)
        if payment.process():
            self.payments[payment.payment_id] = payment
            self.notify('payment_processed', {'payment_id': payment.payment_id, 'order_id': order.order_id, 'amount': total})
            # release table after payment
            order.table.release()
            return payment
        return None

# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def seed_system() -> RestaurantSystem:
    system = RestaurantSystem.get_instance()
    if not system.tables:  # avoid reseeding on reruns
        # Tables
        for i in range(1, 6):
            system.add_table(f"T{i}", capacity=2 + (i % 3) * 2)  # varied capacities
        # Menu Items
        system.add_menu_item("ITEM001", "Bruschetta", Category.STARTER, 6.50)
        system.add_menu_item("ITEM002", "Margherita Pizza", Category.MAIN, 12.00)
        system.add_menu_item("ITEM003", "Pasta Alfredo", Category.MAIN, 14.00)
        system.add_menu_item("ITEM004", "Tiramisu", Category.DESSERT, 7.00)
        system.add_menu_item("ITEM005", "Lemonade", Category.DRINK, 3.50)
        system.add_menu_item("ITEM006", "Espresso", Category.DRINK, 2.80)
    return system

def demo_1_setup():
    print("\n" + "=" * 70)
    print("DEMO 1: System Setup & Seeding")
    print("=" * 70)
    system = seed_system()
    system.add_observer(ConsoleObserver())
    print(f"✅ Tables: {len(system.tables)} | Menu Items: {len(system.menu)}")
    for t in system.tables.values():
        print(f"  - {t}")


def demo_2_reservation_flow():
    print("\n" + "=" * 70)
    print("DEMO 2: Reservation Lifecycle")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C001", "Alice", "alice@example.com")
    table = system.get_available_table(capacity=4)
    reservation = system.create_reservation(customer, table, datetime.now() + timedelta(hours=1))
    if reservation and reservation.confirm():
        print(f"✅ Confirmed {reservation}")
    # Occupy table
    if table.occupy():
        print(f"✅ Table {table.table_id} occupied")


def demo_3_order_lifecycle():
    print("\n" + "=" * 70)
    print("DEMO 3: Order Placement → Preparation → Ready → Served")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C002", "Bob", "bob@example.com")
    table = system.get_available_table(capacity=2)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM002", 2), ("ITEM005", 3), ("ITEM004", 1)])
    if order:
        print(f"✅ Placed {order}")
        ticket = system.create_kitchen_ticket(order)
        ticket.start()
        print(f"🍳 Started preparation for {order.order_id}")
        ticket.complete()
        print(f"✅ Order {order.order_id} READY")
        order.update_status(OrderStatus.SERVED)
        print(f"✅ Order {order.order_id} SERVED")


def demo_4_pricing_and_payment():
    print("\n" + "=" * 70)
    print("DEMO 4: Pricing Strategy & Payment")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C003", "Carol", "carol@example.com")
    table = system.get_available_table(capacity=2)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM005", 4), ("ITEM006", 2), ("ITEM002", 1)])  # drinks + main
    ticket = system.create_kitchen_ticket(order)
    ticket.start()
    ticket.complete()
    order.update_status(OrderStatus.SERVED)
    # Apply composite: happy hour + service charge
    composite = CompositePricingStrategy([HappyHourPricingStrategy(start_hour=0, end_hour=23), ServiceChargePricingStrategy(0.10)])
    total = order.calculate_totals(composite)
    print(f"Subtotal: ${order.subtotal:.2f} | Final (HH + Service): ${total:.2f}")
    payment = system.process_payment(order, PaymentMethod.CARD, composite)
    if payment:
        print(f"✅ {payment}")


def demo_5_full_flow():
    print("\n" + "=" * 70)
    print("DEMO 5: End-to-End Scenario")
    print("=" * 70)
    system = seed_system()
    customer = Customer("C004", "Dana", "dana@example.com")
    table = system.get_available_table(capacity=4)
    reservation = system.create_reservation(customer, table, datetime.now())
    reservation.confirm()
    table.occupy()
    order = system.place_order(table, [("ITEM001", 1), ("ITEM002", 1), ("ITEM005", 2)])
    ticket = system.create_kitchen_ticket(order)
    ticket.start()
    ticket.complete()
    order.update_status(OrderStatus.SERVED)
    # Simple pricing
    pricing = BasePricingStrategy()
    billing = order.calculate_totals(pricing)
    payment = system.process_payment(order, PaymentMethod.CASH, pricing)
    print(f"Final Bill: ${billing:.2f} | Payment Success: {payment.success if payment else False}")
    print(f"Table Released: {table.status.value}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RESTAURANT MANAGEMENT SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory | Command")
    print("=" * 70)
    demo_1_setup()
    demo_2_reservation_flow()
    demo_3_order_lifecycle()
    demo_4_pricing_and_payment()
    demo_5_full_flow()
    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • State: Order & reservation transitions enforced")
    print("  • Strategy: Flexible pricing (happy hour, service charge)")
    print("  • Observer: Decoupled notifications for events")
    print("  • Factory: Centralized creation & ID generation")
    print("  • Command: Encapsulated high-level operations")
    print("  • Singleton: Single orchestrator instance")
    print("\nSee 75_MINUTE_GUIDE.md for deep explanations & UML.")
