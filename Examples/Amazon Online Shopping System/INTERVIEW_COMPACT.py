"""
Amazon Online Shopping System - Interview Implementation
Complete working implementation with design patterns and demo scenarios
Timeline: 75 minutes | Scale: 100K+ concurrent, 1M+ products
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

class ProductCategory(Enum):
    ELECTRONICS = "electronics"
    BOOKS = "books"
    CLOTHING = "clothing"
    HOME = "home"
    SPORTS = "sports"

class ProductStatus(Enum):
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class CartItemStatus(Enum):
    ADDED = "added"
    RESERVED = "reserved"
    PURCHASED = "purchased"
    REMOVED = "removed"

class UserRole(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SELLER = "seller"

# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

class Product:
    """Represents a product in the catalog"""
    def __init__(self, product_id: str, name: str, category: ProductCategory, 
                 price: float, quantity_available: int):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.quantity_available = quantity_available
        self.status = ProductStatus.AVAILABLE
        self.rating = 0.0
        self.reviews = []
        self.created_at = datetime.now()
    
    def is_available(self, qty: int) -> bool:
        return self.status == ProductStatus.AVAILABLE and self.quantity_available >= qty
    
    def reserve(self, qty: int) -> bool:
        if self.is_available(qty):
            self.quantity_available -= qty
            return True
        return False
    
    def release(self, qty: int):
        self.quantity_available += qty
    
    def add_review(self, rating: float, comment: str):
        self.reviews.append({"rating": rating, "comment": comment, "date": datetime.now()})
        if self.reviews:
            self.rating = sum(r["rating"] for r in self.reviews) / len(self.reviews)

class CartItem:
    """Represents an item in shopping cart"""
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.status = CartItemStatus.ADDED
        self.added_at = datetime.now()
    
    def get_total_price(self) -> float:
        return self.product.price * self.quantity
    
    def reserve(self) -> bool:
        if self.product.reserve(self.quantity):
            self.status = CartItemStatus.RESERVED
            return True
        return False
    
    def release(self):
        self.product.release(self.quantity)
        self.status = CartItemStatus.REMOVED

class ShoppingCart:
    """Shopping cart for a user"""
    def __init__(self, user_id: str):
        self.cart_id = str(uuid.uuid4())[:8]
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
    
    def add_item(self, product: Product, quantity: int) -> bool:
        if not product.is_available(quantity):
            return False
        
        if product.product_id in self.items:
            self.items[product.product_id].quantity += quantity
        else:
            self.items[product.product_id] = CartItem(product, quantity)
        
        self.last_modified = datetime.now()
        return True
    
    def remove_item(self, product_id: str) -> bool:
        if product_id in self.items:
            self.items[product_id].release()
            del self.items[product_id]
            self.last_modified = datetime.now()
            return True
        return False
    
    def get_total_price(self) -> float:
        return sum(item.get_total_price() for item in self.items.values())
    
    def get_item_count(self) -> int:
        return sum(item.quantity for item in self.items.values())
    
    def clear(self):
        for item in self.items.values():
            item.release()
        self.items.clear()

class Order:
    """Represents a placed order"""
    def __init__(self, order_id: str, user_id: str, items: Dict[str, CartItem], 
                 total_price: float):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_price = total_price
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.shipped_at: Optional[datetime] = None
        self.delivered_at: Optional[datetime] = None
        self.tracking_number: Optional[str] = None
    
    def confirm(self) -> bool:
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
            return True
        return False
    
    def ship(self, tracking_number: str) -> bool:
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.SHIPPED
            self.tracking_number = tracking_number
            self.shipped_at = datetime.now()
            return True
        return False
    
    def deliver(self) -> bool:
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.DELIVERED
            self.delivered_at = datetime.now()
            return True
        return False
    
    def cancel(self) -> bool:
        if self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            self.status = OrderStatus.CANCELLED
            for item in self.items.values():
                item.release()
            return True
        return False

class User:
    """Represents a customer"""
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = UserRole.CUSTOMER
        self.address: Optional[str] = None
        self.orders: List[Order] = []
        self.created_at = datetime.now()

# ============================================================================
# SECTION 3: PRICING STRATEGY (Strategy Pattern)
# ============================================================================

class PricingStrategy(ABC):
    """Abstract strategy for price calculation"""
    @abstractmethod
    def calculate_price(self, base_price: float, quantity: int) -> float:
        pass

class RegularPricing(PricingStrategy):
    """Regular pricing - no discount"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

class BulkPricing(PricingStrategy):
    """Bulk discount - 10% off for 5+ items"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        if quantity >= 5:
            return base_price * quantity * 0.9
        return base_price * quantity

class MembershipPricing(PricingStrategy):
    """Member discount - 15% off"""
    def calculate_price(self, base_price: float, quantity: int) -> float:
        return base_price * quantity * 0.85

# ============================================================================
# SECTION 4: SEARCH FILTER (Strategy Pattern)
# ============================================================================

class SearchFilter(ABC):
    """Abstract strategy for product search"""
    @abstractmethod
    def filter(self, products: List[Product]) -> List[Product]:
        pass

class CategoryFilter(SearchFilter):
    """Filter by category"""
    def __init__(self, category: ProductCategory):
        self.category = category
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products if p.category == self.category]

class PriceFilter(SearchFilter):
    """Filter by price range"""
    def __init__(self, min_price: float, max_price: float):
        self.min_price = min_price
        self.max_price = max_price
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products if self.min_price <= p.price <= self.max_price]

class RatingFilter(SearchFilter):
    """Filter by minimum rating"""
    def __init__(self, min_rating: float):
        self.min_rating = min_rating
    
    def filter(self, products: List[Product]) -> List[Product]:
        return [p for p in products if p.rating >= self.min_rating]

# ============================================================================
# SECTION 5: OBSERVER PATTERN (Notifications)
# ============================================================================

class OrderObserver(ABC):
    """Observer interface for order events"""
    @abstractmethod
    def notify(self, event: str, order: Order):
        pass

class EmailNotifier(OrderObserver):
    """Email notifications"""
    def notify(self, event: str, order: Order):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📧 EMAIL: Order {order.order_id} | "
              f"Event: {event} | Status: {order.status.value}")

class SMSNotifier(OrderObserver):
    """SMS notifications"""
    def notify(self, event: str, order: Order):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📱 SMS: Order {order.order_id} | "
              f"Event: {event} | Amount: ${order.total_price:.2f}")

class PushNotifier(OrderObserver):
    """Push notifications"""
    def notify(self, event: str, order: Order):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔔 PUSH: Order {order.order_id} | "
              f"Event: {event}")

# ============================================================================
# SECTION 6: SHOPPING SYSTEM (Singleton + Controller)
# ============================================================================

class ShoppingSystem:
    """Singleton controller for shopping operations"""
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
            self.products: Dict[str, Product] = {}
            self.users: Dict[str, User] = {}
            self.carts: Dict[str, ShoppingCart] = {}
            self.orders: Dict[str, Order] = {}
            self.observers: List[OrderObserver] = []
            self.pricing_strategy: PricingStrategy = RegularPricing()
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'ShoppingSystem':
        return ShoppingSystem()
    
    def add_observer(self, observer: OrderObserver):
        """Subscribe to order events"""
        self.observers.append(observer)
    
    def notify_all(self, event: str, order: Order):
        """Notify all observers"""
        for observer in self.observers:
            observer.notify(event, order)
    
    def set_pricing_strategy(self, strategy: PricingStrategy):
        """Switch pricing strategy"""
        self.pricing_strategy = strategy
    
    def add_product(self, name: str, category: ProductCategory, 
                   price: float, quantity: int) -> Product:
        product_id = str(uuid.uuid4())[:8]
        product = Product(product_id, name, category, price, quantity)
        self.products[product_id] = product
        return product
    
    def register_user(self, name: str, email: str, phone: str) -> User:
        user_id = str(uuid.uuid4())[:8]
        user = User(user_id, name, email, phone)
        self.users[user_id] = user
        return user
    
    def search_products(self, filters: List[SearchFilter]) -> List[Product]:
        """Search products with multiple filters"""
        results = list(self.products.values())
        for filter_obj in filters:
            results = filter_obj.filter(results)
        return results
    
    def get_or_create_cart(self, user_id: str) -> ShoppingCart:
        if user_id not in self.carts:
            self.carts[user_id] = ShoppingCart(user_id)
        return self.carts[user_id]
    
    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> bool:
        if product_id not in self.products:
            return False
        
        cart = self.get_or_create_cart(user_id)
        product = self.products[product_id]
        return cart.add_item(product, quantity)
    
    def remove_from_cart(self, user_id: str, product_id: str) -> bool:
        cart = self.carts.get(user_id)
        if cart:
            return cart.remove_item(product_id)
        return False
    
    def checkout(self, user_id: str) -> Optional[Order]:
        """Checkout cart and create order"""
        cart = self.carts.get(user_id)
        if not cart or not cart.items:
            return None
        
        total_price = 0
        for item in cart.items.values():
            item_price = self.pricing_strategy.calculate_price(
                item.product.price, item.quantity)
            total_price += item_price
        
        order_id = str(uuid.uuid4())[:8]
        order = Order(order_id, user_id, dict(cart.items), total_price)
        
        for item in cart.items.values():
            if not item.reserve():
                for prev_item in cart.items.values():
                    if prev_item.status == CartItemStatus.RESERVED:
                        prev_item.release()
                return None
        
        self.orders[order_id] = order
        user = self.users.get(user_id)
        if user:
            user.orders.append(order)
        
        self.notify_all("ORDER_PLACED", order)
        return order
    
    def confirm_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.confirm():
            self.notify_all("ORDER_CONFIRMED", order)
            return True
        return False
    
    def ship_order(self, order_id: str, tracking_number: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.ship(tracking_number):
            self.notify_all("ORDER_SHIPPED", order)
            return True
        return False
    
    def deliver_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.deliver():
            self.notify_all("ORDER_DELIVERED", order)
            return True
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.cancel():
            self.notify_all("ORDER_CANCELLED", order)
            return True
        return False

# ============================================================================
# SECTION 7: DEMO SCENARIOS
# ============================================================================

def demo_1_setup():
    """Demo 1: System setup - Create products and users"""
    print("\n" + "="*70)
    print("DEMO 1: System Setup & Catalog Creation")
    print("="*70)
    
    system = ShoppingSystem.get_instance()
    system.observers.clear()
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    p1 = system.add_product("Laptop", ProductCategory.ELECTRONICS, 999.99, 10)
    p2 = system.add_product("Python Book", ProductCategory.BOOKS, 49.99, 50)
    p3 = system.add_product("T-Shirt", ProductCategory.CLOTHING, 19.99, 100)
    
    u1 = system.register_user("Alice Johnson", "alice@example.com", "555-1234")
    u2 = system.register_user("Bob Smith", "bob@example.com", "555-5678")
    
    print(f"✅ Catalog created with {len(system.products)} products")
    print(f"✅ Registered {len(system.users)} users")
    return system, [p1, p2, p3], [u1, u2]

def demo_2_search_and_filter():
    """Demo 2: Search products with filters"""
    print("\n" + "="*70)
    print("DEMO 2: Search & Filter Products")
    print("="*70)
    
    system, products, users = demo_1_setup()
    
    print("\n→ Search: Electronics under $1000")
    filters = [
        CategoryFilter(ProductCategory.ELECTRONICS),
        PriceFilter(0, 1000)
    ]
    results = system.search_products(filters)
    for p in results:
        print(f"  • {p.name} (${p.price})")
    
    print("\n→ Search: Books $40-$60")
    filters = [
        CategoryFilter(ProductCategory.BOOKS),
        PriceFilter(40, 60)
    ]
    results = system.search_products(filters)
    for p in results:
        print(f"  • {p.name} (${p.price})")

def demo_3_shopping_cart():
    """Demo 3: Add items to cart"""
    print("\n" + "="*70)
    print("DEMO 3: Shopping Cart Operations")
    print("="*70)
    
    system, products, users = demo_1_setup()
    user = users[0]
    
    print(f"\n→ Adding items to cart for {user.name}...")
    system.add_to_cart(user.user_id, products[0].product_id, 1)
    system.add_to_cart(user.user_id, products[1].product_id, 3)
    
    cart = system.carts[user.user_id]
    print(f"✅ Cart items: {cart.get_item_count()}")
    print(f"✅ Cart total: ${cart.get_total_price():.2f}")
    
    print(f"\n→ Removing book from cart...")
    system.remove_from_cart(user.user_id, products[1].product_id)
    print(f"✅ Cart items: {cart.get_item_count()}")
    print(f"✅ Cart total: ${cart.get_total_price():.2f}")

def demo_4_pricing_strategies():
    """Demo 4: Different pricing strategies"""
    print("\n" + "="*70)
    print("DEMO 4: Pricing Strategies (Regular vs Bulk)")
    print("="*70)
    
    system, products, users = demo_1_setup()
    user = users[0]
    
    print(f"\n→ Regular pricing (10 items):")
    for _ in range(10):
        system.add_to_cart(user.user_id, products[2].product_id, 1)
    
    order1 = system.checkout(user.user_id)
    if order1:
        print(f"  Regular: 10 T-Shirts @ ${products[2].price} = ${order1.total_price:.2f}")
    
    system.carts.clear()
    user2 = users[1]
    
    print(f"\n→ Bulk pricing (5+ items = 10% discount):")
    system.set_pricing_strategy(BulkPricing())
    for _ in range(5):
        system.add_to_cart(user2.user_id, products[2].product_id, 1)
    
    order2 = system.checkout(user2.user_id)
    if order2:
        print(f"  Bulk: 5 T-Shirts @ ${products[2].price} = ${order2.total_price:.2f}")

def demo_5_full_order_lifecycle():
    """Demo 5: Complete order lifecycle"""
    print("\n" + "="*70)
    print("DEMO 5: Complete Order Lifecycle")
    print("="*70)
    
    system, products, users = demo_1_setup()
    system.set_pricing_strategy(RegularPricing())
    
    user = users[0]
    
    print(f"\n→ Adding items to cart...")
    system.add_to_cart(user.user_id, products[0].product_id, 1)
    system.add_to_cart(user.user_id, products[1].product_id, 2)
    
    print(f"→ Checkout...")
    order = system.checkout(user.user_id)
    if order:
        print(f"✅ Order created: {order.order_id} | Total: ${order.total_price:.2f}")
    
    print(f"\n→ Confirm order...")
    system.confirm_order(order.order_id)
    
    print(f"→ Ship order...")
    system.ship_order(order.order_id, "AMZN-" + str(uuid.uuid4())[:8].upper())
    
    print(f"→ Deliver order...")
    system.deliver_order(order.order_id)
    
    print(f"\n[SUMMARY]")
    print(f"Order Status: {order.status.value}")
    print(f"Items: {len(order.items)}")
    print(f"Total: ${order.total_price:.2f}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AMAZON ONLINE SHOPPING SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer")
    print("="*70)
    
    try:
        demo_1_setup()
        demo_2_search_and_filter()
        demo_3_shopping_cart()
        demo_4_pricing_strategies()
        demo_5_full_order_lifecycle()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nKey Takeaways:")
        print("  • Singleton: Single ShoppingSystem instance")
        print("  • Strategy: Pluggable pricing & search filters")
        print("  • Observer: Real-time order notifications")
        print("  • State: Clear order lifecycle transitions")
        print("\nFor detailed implementation, see 75_MINUTE_GUIDE.md")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
