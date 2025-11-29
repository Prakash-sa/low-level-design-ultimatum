# 🍽️ Restaurant Management System - Low Level Design

## Overview
A comprehensive system for managing restaurant operations: table reservations, seating, menu catalog, order lifecycle from placement to kitchen preparation and serving, billing with dynamic pricing strategies (happy hour, service charge), payments, and real-time notifications for status changes. Designed for interview demonstration with clear patterns and extensibility.

## Core Domain Entities

### 1. **MenuItem**
- Attributes: `item_id`, `name`, `category` (STARTER / MAIN / DRINK / DESSERT), `base_price`, `is_available`
- Methods: `get_price(strategy)`, `mark_unavailable()`

### 2. **Table**
- Attributes: `table_id`, `capacity`, `status` (AVAILABLE / RESERVED / OCCUPIED)
- Methods: `reserve()`, `occupy()`, `release()`

### 3. **Customer**
- Attributes: `customer_id`, `name`, `contact`
- Methods: `create_reservation()`, `place_order()`

### 4. **Reservation**
- Attributes: `reservation_id`, `customer`, `table`, `time`, `status` (PENDING / CONFIRMED / CANCELLED)
- Methods: `confirm()`, `cancel()`

### 5. **OrderItem**
- Attributes: `menu_item`, `quantity`, `final_price`
- Methods: `calculate(strategy)`

### 6. **Order**
- Attributes: `order_id`, `table`, `items[]`, `status` (RECEIVED / PREPARING / READY / SERVED / CANCELLED), `subtotal`, `bill_total`
- Methods: `add_item()`, `update_status()`, `calculate_totals(strategy)`

### 7. **Payment**
- Attributes: `payment_id`, `order`, `amount`, `method` (CARD / CASH / WALLET), `timestamp`
- Methods: `process()`

### 8. **KitchenTicket**
- Attributes: `ticket_id`, `order`, `queued_at`, `started_at`, `completed_at`
- Methods: `start()`, `complete()`

### 9. **InventoryItem** (Optional Extension)
- Attributes: `sku`, `name`, `quantity`
- Methods: `consume(amount)`, `replenish(amount)`

## Design Patterns Applied

| Pattern | Why | Implementation |
|---------|-----|----------------|
| Singleton | Single system orchestrator | `RestaurantSystem.get_instance()` |
| Strategy | Flexible pricing/service rules | `PricingStrategy` subclasses (Base, HappyHour, ServiceCharge) |
| Observer | Decoupled notifications | `RestaurantObserver` + `ConsoleObserver` events (`reservation_created`, `order_status_changed`, `payment_processed`) |
| State | Order & Reservation lifecycle | `OrderStatus`, `ReservationStatus`, transitions enforced in methods |
| Factory | Clean creation of entities | `OrderFactory`, `ReservationFactory` generate IDs & validate inputs |
| Command | Encapsulated operations | `PlaceOrderCommand`, `UpdateOrderStatusCommand`, `ProcessPaymentCommand`, `CreateReservationCommand`, `CancelReservationCommand` |

## Core Flows

### Reservation Flow
```
Customer requests reservation → RestaurantSystem finds AVAILABLE table → Reservation created (PENDING) → confirm() → Table status RESERVED → Customer arrives → occupy() → status OCCUPIED
```

### Order Lifecycle
```
Order placed (RECEIVED) → KitchenTicket created → status PREPARING → cooking done → READY → waiter serves → SERVED → payment processed → table released
```

### Billing Flow with Strategy
```
order.subtotal = Σ(item.base_price × qty)
strategy adjustments: discount% or service fee → bill_total = strategy.apply(subtotal)
```

## Pricing Strategies (Strategy Pattern)

| Strategy | Rule | Example |
|----------|------|---------|
| BasePricingStrategy | No modification | Lunch standard pricing |
| HappyHourPricingStrategy | Percentage discount on certain categories | 20% off DRINK 4–6 PM |
| ServiceChargePricingStrategy | Add service charge percentage | 10% service fee on dine-in |
| Composite (Interview extension) | Combine discount + charge | Happy hour + service fee |

## Order States (State Pattern)
```
RECEIVED → PREPARING → READY → SERVED
              ↘ CANCELLED (allowed only before READY)
```

## Reservation States
```
PENDING → CONFIRMED → CANCELLED
```

## Success Criteria Checklist
- [x] Reservation & table status transitions
- [x] Order lifecycle with state validation
- [x] Strategy based billing (discount + service charge)
- [x] Observer notifications for key events
- [x] Command pattern for encapsulated actions
- [x] Factory based ID generation & validation
- [x] Demo scenarios runnable (`python3 INTERVIEW_COMPACT.py`)

## Sample Usage
```python
system = RestaurantSystem.get_instance()
customer = Customer("C001", "Alice", "alice@example.com")
table = system.get_available_table(capacity=4)
reservation = system.create_reservation(customer, table, datetime.now())
reservation.confirm()
order = system.place_order(table, [("ITEM001", 2), ("ITEM005", 1)])
order.calculate_totals(HappyHourPricingStrategy())
payment = system.process_payment(order, method="CARD")
```

## Scalability & Extensions
- Multiple branches: Branch identifier inside `RestaurantSystem`
- Distributed kitchen: Separate KitchenService microservice
- Realtime waiter tablets: WebSocket observer implementation
- Inventory deductions on order placement
- Analytics: event streaming (Kafka) for orders & payments

## Files
- `README.md` (this overview)
- `START_HERE.md` (rapid interview guide)
- `INTERVIEW_COMPACT.py` (full runnable implementation with demos)
- `75_MINUTE_GUIDE.md` (step-by-step deep dive + UML + Q&A)

---
**Next**: Open `START_HERE.md` for 5‑minute prep or run demos: `python3 INTERVIEW_COMPACT.py`.
