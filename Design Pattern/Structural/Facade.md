# Facade Pattern

> Provide a unified, simplified interface to a set of interfaces in a subsystem. Facade defines a higher-level interface that makes the subsystem easier to use.

---

## Problem

You have a complex subsystem with many classes that clients need to interact with. This complexity makes the subsystem hard to use and maintain.

## Solution

The Facade pattern provides a single unified interface to a set of classes/components.

---

## Implementation

```python
# ============ COMPLEX SUBSYSTEM: Movie Theater ============

class AudioSystem:
    def __init__(self):
        self.volume = 5
    
    def set_volume(self, level: int):
        self.volume = level
        print(f"🔊 Audio volume set to {level}")
    
    def turn_on(self):
        print("🔊 Audio system ON")
    
    def turn_off(self):
        print("🔊 Audio system OFF")

class Projector:
    def __init__(self):
        self.is_on = False
    
    def turn_on(self):
        self.is_on = True
        print("🎬 Projector ON")
    
    def turn_off(self):
        self.is_on = False
        print("🎬 Projector OFF")
    
    def set_resolution(self, width: int, height: int):
        if self.is_on:
            print(f"🎬 Projector resolution: {width}x{height}")

class Screen:
    def __init__(self):
        self.position = "up"
    
    def down(self):
        self.position = "down"
        print("🎥 Screen DOWN")
    
    def up(self):
        self.position = "up"
        print("🎥 Screen UP")

class DVDPlayer:
    def __init__(self):
        self.is_playing = False
    
    def turn_on(self):
        print("📀 DVD Player ON")
    
    def turn_off(self):
        print("📀 DVD Player OFF")
    
    def play(self, movie: str):
        self.is_playing = True
        print(f"📀 Playing: {movie}")
    
    def stop(self):
        self.is_playing = False
        print("📀 DVD stopped")

class Lights:
    def __init__(self):
        self.brightness = 100
    
    def dim(self, level: int):
        self.brightness = level
        print(f"💡 Lights dimmed to {level}%")
    
    def turn_on(self):
        self.brightness = 100
        print("💡 Lights ON")

# ============ FACADE: Simplifies subsystem ============

class HomeTheaterFacade:
    """Facade - provides simple interface to complex subsystem"""
    
    def __init__(self):
        self.audio = AudioSystem()
        self.projector = Projector()
        self.screen = Screen()
        self.dvd_player = DVDPlayer()
        self.lights = Lights()
    
    def watch_movie(self, movie: str):
        """Simple interface to watch a movie"""
        print(f"\n🎭 Starting movie night: {movie}")
        self.lights.dim(10)
        self.screen.down()
        self.projector.turn_on()
        self.projector.set_resolution(1920, 1080)
        self.audio.turn_on()
        self.audio.set_volume(8)
        self.dvd_player.turn_on()
        self.dvd_player.play(movie)
    
    def end_movie(self):
        """Simple interface to end movie"""
        print("\n🎭 Ending movie night")
        self.dvd_player.stop()
        self.dvd_player.turn_off()
        self.projector.turn_off()
        self.screen.up()
        self.audio.turn_off()
        self.lights.turn_on()

# ============ ANOTHER EXAMPLE: Restaurant Ordering System ============

class Menu:
    def get_items(self):
        return ["Pizza", "Pasta", "Salad", "Burger"]

class Kitchen:
    def prepare_pizza(self):
        print("🍕 Preparing pizza...")
        return "Pizza"
    
    def prepare_pasta(self):
        print("🍝 Preparing pasta...")
        return "Pasta"
    
    def prepare_salad(self):
        print("🥗 Preparing salad...")
        return "Salad"

class Waiter:
    def take_order(self, order: str):
        print(f"✍️ Waiter taking order: {order}")
    
    def serve_order(self, item: str):
        print(f"🚶 Waiter serving: {item}")

class Cashier:
    def calculate_bill(self, items: list) -> float:
        prices = {"Pizza": 10, "Pasta": 8, "Salad": 6, "Burger": 7}
        total = sum(prices.get(item, 0) for item in items)
        print(f"💰 Total bill: ${total}")
        return total
    
    def process_payment(self, amount: float):
        print(f"💳 Payment of ${amount} processed")

class RestaurantFacade:
    """Facade - simplifies restaurant operations"""
    
    def __init__(self):
        self.menu = Menu()
        self.kitchen = Kitchen()
        self.waiter = Waiter()
        self.cashier = Cashier()
    
    def order_meal(self, items: list):
        print(f"\n🍽️ Ordering meal: {items}")
        
        # Show menu
        available = self.menu.get_items()
        print(f"Available: {available}")
        
        # Take order
        for item in items:
            self.waiter.take_order(item)
        
        # Prepare food
        for item in items:
            if item == "Pizza":
                self.kitchen.prepare_pizza()
            elif item == "Pasta":
                self.kitchen.prepare_pasta()
            elif item == "Salad":
                self.kitchen.prepare_salad()
        
        # Serve food
        for item in items:
            self.waiter.serve_order(item)
        
        # Calculate and pay bill
        total = self.cashier.calculate_bill(items)
        self.cashier.process_payment(total)

# ============ LIBRARY SYSTEM FACADE ============

class BookDatabase:
    def search_by_title(self, title: str):
        print(f"📚 Searching for: {title}")
        return ["Book 1", "Book 2"]

class InventorySystem:
    def check_availability(self, book_id: str):
        print(f"✅ Checking inventory for {book_id}")
        return True

class CheckoutSystem:
    def checkout_book(self, book_id: str, member_id: str):
        print(f"📋 Checkout: {book_id} to member {member_id}")

class NotificationSystem:
    def send_confirmation(self, member_id: str, book: str):
        print(f"📧 Confirmation email sent to member {member_id}")

class LibraryFacade:
    """Facade - simplifies library operations"""
    
    def __init__(self):
        self.database = BookDatabase()
        self.inventory = InventorySystem()
        self.checkout = CheckoutSystem()
        self.notifications = NotificationSystem()
    
    def borrow_book(self, title: str, member_id: str):
        print(f"\n📖 Borrowing book: {title}")
        
        # Search
        results = self.database.search_by_title(title)
        if not results:
            print("Book not found")
            return
        
        # Check availability
        book_id = results[0]
        if not self.inventory.check_availability(book_id):
            print("Book not available")
            return
        
        # Checkout
        self.checkout.checkout_book(book_id, member_id)
        
        # Send confirmation
        self.notifications.send_confirmation(member_id, title)

# Demo
if __name__ == "__main__":
    print("=" * 50)
    print("=== HOME THEATER FACADE ===")
    print("=" * 50)
    theater = HomeTheaterFacade()
    
    # Without facade, clients would need to do all this manually
    theater.watch_movie("The Matrix")
    theater.end_movie()
    
    print("\n" + "=" * 50)
    print("=== RESTAURANT FACADE ===")
    print("=" * 50)
    restaurant = RestaurantFacade()
    restaurant.order_meal(["Pizza", "Pasta", "Salad"])
    
    print("\n" + "=" * 50)
    print("=== LIBRARY FACADE ===")
    print("=" * 50)
    library = LibraryFacade()
    library.borrow_book("Clean Code", "M001")
```

---

## Key Concepts

- **Facade**: Single unified interface to complex subsystem
- **Subsystem**: Complex set of classes/components
- **Simplification**: Clients don't see complexity
- **Decoupling**: Clients depend only on facade, not subsystem
- **Convenience**: Common operations wrapped in simple methods

---

## When to Use

✅ Complex subsystem needs simplified interface  
✅ Reduce coupling between clients and subsystem  
✅ Provide entry point to layered subsystem  
✅ Simplify client code and dependencies  

---

## Interview Q&A

**Q1: What's the difference between Facade and Adapter?**

A:
- **Facade**: Simplifies complex subsystem. Multiple classes.
- **Adapter**: Makes incompatible interfaces work. Usually wraps one class.

```python
# Facade: Simplifies many classes
class HomeTheaterFacade:
    def watch_movie(self):
        self.projector.turn_on()
        self.audio.turn_on()
        self.screen.down()  # Multiple components

# Adapter: Converts one interface
class PaymentAdapter:
    def pay(self, amount):
        return legacy_payment.process(amount)  # One component
```

---

**Q2: Can a facade itself be decorated or wrapped?**

A: Yes, facades can be composed:

```python
class AdvancedTheaterFacade(HomeTheaterFacade):
    def watch_4k_movie(self, movie):
        # Uses parent facade + adds new functionality
        self.watch_movie(movie)
        self.projector.set_resolution(4096, 2160)
```

---

**Q3: How would you handle exceptions in a facade?**

A:
```python
class RobustTheaterFacade:
    def watch_movie(self, movie: str):
        try:
            self.lights.dim(10)
            self.projector.turn_on()
            self.dvd_player.play(movie)
        except Exception as e:
            print(f"Error: {e}")
            self.cleanup()
    
    def cleanup(self):
        # Ensure system is in safe state
        self.lights.turn_on()
        self.projector.turn_off()
```

---

**Q4: How would you make a facade for multiple providers?**

A:
```python
class FlexibleRestaurantFacade:
    def __init__(self, provider: str):
        if provider == "italian":
            self.kitchen = ItalianKitchen()
        elif provider == "chinese":
            self.kitchen = ChineseKitchen()
        else:
            self.kitchen = StandardKitchen()
    
    def order_meal(self, items):
        for item in items:
            self.kitchen.prepare(item)
```

---

**Q5: How would you test code using a facade?**

A:
```python
from unittest.mock import Mock

class MockHomeTheaterFacade:
    def __init__(self):
        self.projector = Mock()
        self.audio = Mock()
        self.lights = Mock()
    
    def watch_movie(self, movie):
        self.lights.dim(10)
        self.projector.turn_on()

# Test
facade = MockHomeTheaterFacade()
facade.watch_movie("The Matrix")
facade.lights.dim.assert_called_with(10)
```

---

## Trade-offs

✅ **Pros**: Simplifies complex subsystems, loose coupling, easier to use  
❌ **Cons**: Facade becomes too large, hides subsystem details, may be overkill for simple systems

---

## Real-World Examples

- **Framework APIs** (Django, React provide facades)
- **Database ORMs** (hide SQL complexity)
- **Logging frameworks** (hide configuration complexity)
- **Cloud SDKs** (AWS SDK facades, Azure SDK)
- **Java I/O** (various stream classes with simplified facades)
