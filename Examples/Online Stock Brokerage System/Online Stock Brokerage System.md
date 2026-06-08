# Online Stock Brokerage System — Complete Design Guide

> Deposit funds, search real-time stock quotes, place market/limit orders, manage portfolios, and track profit/loss with atomic trade execution and observer-driven price updates.

**Scale**: 10,000+ concurrent users, 1M+ orders/day, 99.9% uptime during trading hours  
**Duration**: 75-minute interview guide  
**Focus**: Market vs limit order execution, atomic fund transfer, portfolio P&L tracking, observer-driven price triggers

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Users want to trade stocks online: buy/sell securities, manage investment portfolios, and track real-time profit/loss. System must prevent double-spending, execute orders atomically, and provide accurate portfolio valuation in real-time.

### Core Flow
```
User Deposit Funds
        ↓
Search & Browse Stocks (real-time quotes)
        ↓
Place Order (Market or Limit)
        ├─ Market: Execute immediately at current_price
        └─ Limit: Pending until price condition met
        ↓
If available: Deduct funds, record transaction
If insufficient: Reject order, balance unchanged
        ↓
Update Portfolio (holdings + cost basis)
        ↓
Calculate P/L (profit/loss vs cost basis)
        ↓
Send notifications (email/SMS/console)
        ↓
Withdraw gains or repeat trading
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Distributed system with 10K concurrent users"
2. **Market orders only, or limit orders too?** → "Both market and limit orders"
3. **Real payment processing?** → "Mock payment service for interview"
4. **Margin trading or long-only?** → "Long positions only (buying)"
5. **Multiple currencies?** → "Single currency (USD), US stock market"
6. **Trading hours enforcement?** → "9:30 AM – 4:00 PM EST"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **User/Trader** | Deposits funds and trades stocks | Deposit, search, place order, cancel, withdraw |
| **Brokerage Admin** | Manages stocks and exchange | Add stock, update price, manage accounts |
| **System** | Controller and notifier | Execute orders, trigger limit orders on price change, send notifications |

### Functional Requirements (What does the system do?)

✅ **Account Management**
  - Deposit and withdraw funds
  - View account balance and net worth

✅ **Market Data**
  - Real-time stock quotes
  - Price update broadcasting to subscribers

✅ **Order Execution**
  - Place market orders (execute immediately at current price)
  - Place limit orders (execute when price condition is met)
  - Cancel pending orders before execution

✅ **Portfolio Management**
  - Track holdings (stock → quantity + cost basis)
  - Calculate portfolio value in real-time
  - Calculate profit/loss vs cost basis

✅ **Transaction History**
  - Immutable record of every executed trade
  - Order history with status tracking

✅ **Watchlist & Notifications**
  - Watchlist for tracking favorite stocks
  - Email/SMS/push notifications on order events

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 10,000+ simultaneous users  
✅ **Latency**: <100ms search, <500ms order execution, <1000ms portfolio valuation  
✅ **Consistency**: Atomic transactions — no partial execution  
✅ **Accuracy**: Correct average cost basis for multi-purchase positions  
✅ **Uptime**: 99.9% during trading hours  
✅ **Scalability**: 1M+ orders/day across multiple regions  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES — multi-region with replicas |
| **Order types** | Market and Limit only |
| **Position direction** | Long only (no short selling) |
| **Currency** | Single (USD) |
| **Payment processing** | External gateway (out of scope) |
| **Options / futures** | Out of scope |
| **After-hours trading** | Out of scope |
| **Tax reporting / regulatory** | Out of scope |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

From the requirements above, identify nouns:

```
User, Account, Stock, Order, Portfolio, Transaction, Watchlist, StockExchange, ...
```

### Step 2.2: Define Core Classes

#### **Stock** — A tradable security
```
Properties:
  - symbol: str (e.g., "AAPL", "GOOGL")
  - name: str (e.g., "Apple Inc.")
  - current_price: float
  - observers: List[PriceObserver]
  - price_history: List[float]

Behaviors:
  - get_quote(): Return current price
  - update_price(new_price): Set price and notify all observers
  - add_observer(observer): Subscribe to price changes
  - remove_observer(observer): Unsubscribe
```

#### **Account** — A user's trading account
```
Properties:
  - account_id: str
  - user: User
  - balance: float
  - portfolio: Portfolio
  - transaction_history: List[Transaction]

Behaviors:
  - deposit(amount): Add funds
  - withdraw(amount): Remove funds (check balance)
  - get_balance(): Return available balance
  - get_net_worth(): balance + portfolio market value
  - place_order(stock, qty, order_type, price_type, limit_price)
```

#### **Order** — A buy or sell request
```
Properties:
  - order_id: str
  - account: Account
  - stock: Stock
  - quantity: int
  - order_type: OrderType (BUY / SELL)
  - price_type: PriceType (MARKET / LIMIT)
  - limit_price: Optional[float]
  - status: OrderStatus (PENDING / EXECUTED / CANCELLED / REJECTED)
  - execution_price: Optional[float]
  - timestamp: datetime

Behaviors:
  - execute(execution_price): Transition PENDING → EXECUTED
  - cancel(): Transition PENDING → CANCELLED
```

#### **Portfolio** — Holdings tracker for an account
```
Properties:
  - holdings: Dict[str, {quantity, cost_basis}]

Behaviors:
  - add_holding(stock, quantity, price): Add or average-up a position
  - remove_holding(stock, quantity): Reduce or close a position
  - calculate_value(): Sum of quantity × current_price for all holdings
  - get_profit_loss(): Dict with profit_loss, percentage, cost_total, current_value
  - get_holdings_summary(): List of holding details
```

#### **User** — A registered customer
```
Properties:
  - user_id: str
  - name: str
  - email: str
  - phone: str

Behaviors:
  - create_account(): Register a new trading account
  - get_orders(): Retrieve order history
```

#### **StockExchange** — Central controller (Singleton)
```
Properties:
  - stocks: Dict[str, Stock]
  - orders: Dict[str, Order]
  - accounts: Dict[str, Account]
  - strategies: Dict[PriceType, OrderStrategy]
  - observers: List[PriceObserver]
  - pending_orders: List[Order]

Behaviors:
  - get_instance(): Return singleton
  - place_order(order): Route to market or limit execution
  - execute_buy_order(order): Deduct funds, update portfolio
  - execute_sell_order(order): Add funds, reduce portfolio
  - check_and_execute_limit_orders(stock): Evaluate pending limit orders after price update
  - update_stock_price(symbol, new_price): Update price and notify observers
  - add_observer(observer): Register a global price observer
  - notify_observers(stock, old_price, new_price): Fan-out to all observers
```

#### **Brokerage** — (See StockExchange — the exchange IS the brokerage in this design)

### Step 2.3: Define Enumerations (State & Type)

```python
class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

class PriceType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
```

### Step 2.4: Why These Entities?

| Entity | Why Needed | Cost of Missing |
|--------|-----------|-----------------|
| **Stock** | Tracks live price and notifies subscribers | No real-time price updates, no limit-order triggers |
| **Account** | Manages funds separately from user identity | Can't enforce balance constraints |
| **Order** | Captures intent + lifecycle (PENDING → EXECUTED) | No audit trail, can't cancel |
| **Portfolio** | Tracks cost basis per holding for P&L | Inaccurate profit/loss reporting |
| **User** | Separates identity from financial data | Can't support multiple accounts per person |
| **StockExchange** | Central coordinator, thread-safe singleton | Race conditions on concurrent order execution |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Register Account**
```python
def register_account(user: User, initial_balance: float = 0.0) -> Account:
    """
    Create a new trading account for a registered user.
    Returns: Account object with account_id.
    Raises: ValueError if initial_balance < 0.
    """
```

#### **2. Place Order** (CRITICAL)
```python
def place_order(order: Order) -> bool:
    """
    Submit a buy or sell order for execution.

    Market order: Execute immediately at current price.
    Limit order:  Queue until price condition is met.

    Precondition (BUY):  account.balance >= quantity * price
    Precondition (SELL): portfolio has >= quantity shares

    Returns: True if executed or queued, False if rejected.

    Raises:
      - InsufficientFundsError: Insufficient balance for buy
      - InsufficientSharesError: Not enough shares to sell
      - InvalidOrderError: Negative quantity or missing limit price

    Concurrency: THREAD-SAFE — atomic fund check + deduction
    Response Time: <500ms
    """
```

#### **3. Cancel Order**
```python
def cancel_order(order_id: str) -> bool:
    """
    Cancel a PENDING order before execution.
    Precondition: order.status == PENDING
    Postcondition: order.status == CANCELLED

    Returns: True if cancelled, False if not in PENDING state.
    Raises: OrderNotFoundError
    """
```

#### **4. Update Stock Price**
```python
def update_stock_price(symbol: str, new_price: float) -> None:
    """
    Update market price of a stock and trigger observer notifications.
    Side effects:
      - Notifies all PriceObserver subscribers
      - Triggers check_and_execute_limit_orders for pending limit orders
    Raises: StockNotFoundError
    """
```

#### **5. Get Portfolio Value & P&L**
```python
def get_portfolio_summary(account_id: str) -> Dict:
    """
    Returns portfolio value, P&L, and per-holding breakdown.
    Response Time: <1000ms
    """
```

#### **6. Add Price Observer**
```python
def add_observer(observer: PriceObserver) -> None:
    """
    Register a global subscriber for all stock price changes.
    Events: price change on any stock.
    Observer receives: (stock, old_price, new_price)
    """
```

### Step 3.2: Exception Hierarchy

```python
class BrokerageException(Exception):
    """Base exception"""
    pass

class InsufficientFundsError(BrokerageException):
    """Account balance too low for buy order"""
    pass

class InsufficientSharesError(BrokerageException):
    """Not enough shares to sell"""
    pass

class InvalidOrderError(BrokerageException):
    """Invalid order parameters"""
    pass

class StockNotFoundError(BrokerageException):
    """Stock symbol not registered"""
    pass

class InvalidStateError(BrokerageException):
    """Invalid state transition attempted"""
    pass
```

### Step 3.3: API Usage Example

```python
exchange = StockExchange.get_instance()

# Setup
user = User("U001", "Alice", "alice@email.com", "555-0001")
account = exchange.register_account(user, initial_balance=10000.00)
apple = Stock("AAPL", "Apple Inc.", 150.00)
exchange.add_stock(apple)

# Market buy
order = OrderFactory.create_order(account, apple, 10, OrderType.BUY, PriceType.MARKET)
exchange.place_order(order)

# Limit sell — queued until price >= 160
limit_order = OrderFactory.create_order(
    account, apple, 5, OrderType.SELL, PriceType.LIMIT, limit_price=160.00
)
exchange.place_order(limit_order)

# Price update triggers limit order
exchange.update_stock_price("AAPL", 165.00)

# Portfolio P&L
pnl = account.portfolio.get_profit_loss()
print(f"P&L: ${pnl['profit_loss']:+,.2f} ({pnl['percentage']:+.2f}%)")
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
StockExchange HAS-A stocks (1:N Composition)
  └─ Exchange owns and manages all Stock objects

StockExchange HAS-A accounts (1:N Composition)
  └─ Exchange owns all Account objects

User HAS-A Account (1:N Association)
  └─ One user may have multiple accounts

Account HAS-A Portfolio (1:1 Composition)
  └─ Portfolio lives and dies with the account

Account PLACES Order (1:N Association)
  └─ Account references many orders over time

Order REFERENCES Stock (1:1 Association)
  └─ Order links to the traded security (no ownership)

Stock NOTIFIES PriceObserver (1:N Association)
  └─ Stock broadcasts to all registered observers

Portfolio CONTAINS Holdings (1:N Composition)
  └─ Portfolio owns its position data
```

### Step 4.2: Complete UML Class Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                    STOCK EXCHANGE (Singleton)                         │
├───────────────────────────────────────────────────────────────────────┤
│ - _instance: StockExchange                                            │
│ - stocks: Dict[str, Stock]                                            │
│ - orders: Dict[str, Order]                                            │
│ - accounts: Dict[str, Account]                                        │
│ - strategies: Dict[PriceType, OrderStrategy]                          │
│ - observers: List[PriceObserver]                                      │
├───────────────────────────────────────────────────────────────────────┤
│ + get_instance(): StockExchange                                       │
│ + place_order(order): bool                                            │
│ + execute_buy_order(order): bool                                      │
│ + execute_sell_order(order): bool                                     │
│ + check_and_execute_limit_orders(stock): void                         │
│ + update_stock_price(symbol, new_price): void                         │
│ + add_observer(observer): void                                        │
│ + notify_observers(stock, old_price, new_price): void                │
└───────────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐  ┌──────────┐  ┌────────────┐
    │   Stock     │  │   User   │  │  Order     │
    ├─────────────┤  ├──────────┤  ├────────────┤
    │ - symbol    │  │ - id     │  │ - order_id │
    │ - price     │  │ - name   │  │ - account  │
    │ - observers │  │ - email  │  │ - stock    │
    │ - history   │  │ - phone  │  │ - quantity │
    └─────────────┘  └──────────┘  │ - status   │
           │               │        │ - limit_   │
           │               │        │   price    │
           │               │        └────────────┘
           │               │
           └─ observers ─┐ │ creates
                         ▼ ▼
         ┌─────────────────────────────────────────┐
         │    Account                              │
         ├─────────────────────────────────────────┤
         │ - account_id                            │
         │ - user (User)                           │
         │ - balance: float                        │
         │ - portfolio: Portfolio                  │
         │ - transaction_history: List[Transaction]│
         ├─────────────────────────────────────────┤
         │ + deposit(amount): bool                 │
         │ + withdraw(amount): bool                │
         │ + get_balance(): float                  │
         │ + get_net_worth(): float                │
         │ + place_order(stock, qty, type, price) │
         └─────────────────────────────────────────┘
                         │
                         │ contains
                         ▼
         ┌─────────────────────────────────────────┐
         │    Portfolio                            │
         ├─────────────────────────────────────────┤
         │ - holdings: Dict[str, {qty, cost_basis}]│
         │ - current_value: float                  │
         ├─────────────────────────────────────────┤
         │ + add_holding(stock, qty, price): void │
         │ + remove_holding(stock, qty): bool      │
         │ + calculate_value(): float              │
         │ + get_profit_loss(): Dict               │
         │ + get_holdings_summary(): List          │
         └─────────────────────────────────────────┘


STRATEGY PATTERNS:

┌──────────────────────────────────────────────────┐
│    OrderStrategy (Abstract)                      │
│ - can_execute(order): bool                       │
│ - get_execution_price(order): Optional[float]    │
├──────────────────────────────────────────────────┤
│  ├─ MarketOrderStrategy (execute immediately)   │
│  └─ LimitOrderStrategy (execute conditionally)   │
└──────────────────────────────────────────────────┘


OBSERVER PATTERN:

┌──────────────────────────────────────────────────┐
│    PriceObserver (Abstract)                      │
│ - update(stock, old_price, new_price): void     │
├──────────────────────────────────────────────────┤
│  ├─ PortfolioObserver (recalculate P/L)         │
│  ├─ LimitOrderObserver (execute pending orders)  │
│  ├─ AlertObserver (send price alerts)            │
│  └─ ConsoleObserver (print updates)              │
└──────────────────────────────────────────────────┘


ENUMERATIONS:

┌──────────────────────────┐
│ OrderType (Enum)         │
├──────────────────────────┤
│ • BUY                    │
│ • SELL                   │
└──────────────────────────┘

┌──────────────────────────┐
│ PriceType (Enum)         │
├──────────────────────────┤
│ • MARKET                 │
│ • LIMIT                  │
└──────────────────────────┘

┌──────────────────────────┐
│ OrderStatus (Enum)       │
├──────────────────────────┤
│ • PENDING                │
│ • EXECUTED               │
│ • CANCELLED              │
│ • REJECTED               │
└──────────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| StockExchange → Stocks | 1:N | Composition | Exchange owns all stocks |
| StockExchange → Accounts | 1:N | Composition | Exchange owns all accounts |
| User → Account | 1:N | Association | One user, multiple accounts |
| Account → Portfolio | 1:1 | Composition | Portfolio lives inside account |
| Account → Orders | 1:N | Association | Account references many orders |
| Order → Stock | 1:1 | Association | Order references traded security |
| Stock → PriceObserver | 1:N | Association | Stock notifies multiple subscribers |
| Transaction → Order | 1:1 | Association | Immutable record of executed order |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only apply them to solve specific problems.

### Pattern 1: **Singleton** (For StockExchange)

**Problem**: 10K+ users accessing trading system → race conditions on order matching, fund deduction.

**Solution**: Single `StockExchange` instance with thread-safe double-checked locking.

```python
class StockExchange:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):   # *args/**kwargs — avoids TypeError when __init__ passes params
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.stocks = {}
                    cls._instance.orders = {}
                    cls._instance.accounts = {}
        return cls._instance

    @staticmethod
    def get_instance():
        return StockExchange()
```

**Benefit**: Single source of truth for all market operations, prevents conflicting order executions.  
**Trade-off**: Global state makes unit testing harder; must reset `_instance` between test runs.

---

### Pattern 2: **Strategy** (For Order Execution)

**Problem**: Market and Limit orders have fundamentally different execution logic; more types (stop-loss, trailing stop) may be added.

**Solution**: Pluggable `OrderStrategy` with a common interface.

```python
class OrderStrategy(ABC):
    @abstractmethod
    def can_execute(self, order) -> bool:
        pass

    @abstractmethod
    def get_execution_price(self, order) -> Optional[float]:
        pass

class MarketOrderStrategy(OrderStrategy):
    """Execute immediately at current market price"""
    def can_execute(self, order) -> bool:
        return True  # Always executable

    def get_execution_price(self, order) -> Optional[float]:
        return order.stock.current_price

class LimitOrderStrategy(OrderStrategy):
    """Execute only when price condition is met"""
    def can_execute(self, order) -> bool:
        if order.order_type == OrderType.BUY:
            return order.stock.current_price <= order.limit_price
        else:  # SELL
            return order.stock.current_price >= order.limit_price

    def get_execution_price(self, order) -> Optional[float]:
        if self.can_execute(order):
            return order.stock.current_price
        return None
```

**Benefit**: Easy to add `StopLossOrderStrategy` without changing core execution logic.  
**Trade-off**: Extra abstraction; for only 2 types, a simple `if/else` would also be readable.

---

### Pattern 3: **Observer** (For Price Updates)

**Problem**: Multiple components (portfolios, watchlists, price alerts) need real-time price updates without tight coupling to `Stock`.

**Solution**: Abstract `PriceObserver` interface with pluggable implementations.

```python
class PriceObserver(ABC):
    @abstractmethod
    def update(self, stock: 'Stock', old_price: float, new_price: float):
        pass

class PortfolioObserver(PriceObserver):
    """Recalculate portfolio value on price change"""
    def __init__(self, portfolio: 'Portfolio'):
        self.portfolio = portfolio

    def update(self, stock, old_price: float, new_price: float):
        # Portfolio automatically reflects new price; P/L recalculated on next call
        pass

class LimitOrderObserver(PriceObserver):
    """Check if pending limit orders can execute"""
    def __init__(self, exchange: 'StockExchange'):
        self.exchange = exchange

    def update(self, stock, old_price: float, new_price: float):
        self.exchange.check_and_execute_limit_orders(stock)

class AlertObserver(PriceObserver):
    """Send price alerts to users"""
    def update(self, stock, old_price: float, new_price: float):
        if new_price >= 150:  # example threshold
            pass  # send notification
```

**Benefit**: Decouples price updates from dependent components; add `SlackNotifier` without touching `Stock` or `StockExchange`.  
**Trade-off**: Observer lifecycle management; slow observers block the notification loop if not run async.

---

### Pattern 4: **State** (For Order Lifecycle)

**Problem**: Orders have valid transitions (PENDING → EXECUTED) and invalid ones (EXECUTED → PENDING); these must be enforced.

**Solution**: Enum-based state management with transition validation inside `Order`.

```python
class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Order:
    def execute(self, execution_price: float) -> bool:
        """Transition PENDING → EXECUTED"""
        if self.status != OrderStatus.PENDING:
            raise InvalidStateError()
        self.status = OrderStatus.EXECUTED
        self.execution_price = execution_price
        return True

    def cancel(self) -> bool:
        """Transition PENDING/REJECTED → CANCELLED"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.REJECTED]:
            raise InvalidStateError()
        self.status = OrderStatus.CANCELLED
        return True
```

**Benefit**: Invalid state transitions raise immediately at runtime; readable lifecycle.  
**Trade-off**: Enum states require explicit guard on every transition method.

---

### Pattern 5: **Factory** (For Order Creation)

**Problem**: Creating different order types scattered throughout code is hard to maintain and validate.

**Solution**: Centralized `OrderFactory` with validation and ID generation.

```python
class OrderFactory:
    _order_counter = 0

    @staticmethod
    def create_order(account: 'Account', stock: 'Stock', quantity: int,
                     order_type: 'OrderType', price_type: 'PriceType',
                     limit_price: Optional[float] = None) -> 'Order':
        OrderFactory._order_counter += 1
        order_id = f"ORD_{OrderFactory._order_counter}_{int(time.time())}"

        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price_type == PriceType.LIMIT and limit_price is None:
            raise ValueError("Limit price required for limit orders")

        return Order(order_id, account, stock, quantity, order_type, price_type, limit_price)
```

**Benefit**: Centralized validation, consistent ID generation, single place to extend.  
**Trade-off**: Static counter is not thread-safe under extreme concurrency (use `uuid` in production).

---

### Pattern 6: **Command** (For Trading Operations)

**Problem**: Buy/Sell/Cancel operations need undo capability, history, and audit trail.

**Solution**: Command objects encapsulate every trading operation.

```python
class Command(ABC):
    @abstractmethod
    def execute(self) -> bool:
        pass

class BuyCommand(Command):
    def __init__(self, exchange: 'StockExchange', order: 'Order'):
        self.exchange = exchange
        self.order = order

    def execute(self) -> bool:
        return self.exchange.execute_buy_order(self.order)

class SellCommand(Command):
    def __init__(self, exchange: 'StockExchange', order: 'Order'):
        self.exchange = exchange
        self.order = order

    def execute(self) -> bool:
        return self.exchange.execute_sell_order(self.order)

class CancelOrderCommand(Command):
    def __init__(self, order: 'Order'):
        self.order = order

    def execute(self) -> bool:
        return self.order.cancel()
```

**Benefit**: Encapsulates operations as objects for queuing, logging, and undo.  
**Trade-off**: Extra wrapper layer; justified when audit trail or undo/redo is required.

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---------------|---------|
| **Singleton** | Single consistent view of market state | Thread-safe global coordinator |
| **Strategy** | Market vs Limit execution logic varies | Pluggable, open/closed principle |
| **Observer** | Real-time price updates to many subscribers | Loose coupling, easy to extend |
| **State (Enum)** | Order lifecycle transitions must be valid | Invalid transitions caught at runtime |
| **Factory** | Consistent order creation with validation | Centralized, no scattered creation code |
| **Command** | Buy/Sell/Cancel need audit trail | Queuing, logging, undo support |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


# ============================================================
# ENUMERATIONS
# ============================================================

class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

class PriceType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


# ============================================================
# EXCEPTIONS
# ============================================================

class BrokerageException(Exception):
    pass

class InsufficientFundsError(BrokerageException):
    pass

class InsufficientSharesError(BrokerageException):
    pass

class InvalidStateError(BrokerageException):
    pass

class InvalidOrderError(BrokerageException):
    pass


# ============================================================
# CORE ENTITIES
# ============================================================

class User:
    def __init__(self, user_id: str, name: str, email: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone

    def __repr__(self):
        return f"User({self.user_id}, {self.name})"


class Portfolio:
    """Tracks stock holdings and computes profit/loss."""

    def __init__(self):
        self.holdings: Dict[str, dict] = {}  # symbol -> {quantity, cost_basis, stock}

    def add_holding(self, stock, quantity: int, price: float):
        symbol = stock.symbol
        if symbol in self.holdings:
            existing = self.holdings[symbol]
            total_qty = existing['quantity'] + quantity
            total_cost = existing['quantity'] * existing['cost_basis'] + quantity * price
            existing['quantity'] = total_qty
            existing['cost_basis'] = total_cost / total_qty
        else:
            self.holdings[symbol] = {
                'quantity': quantity,
                'cost_basis': price,
                'stock': stock
            }

    def remove_holding(self, stock, quantity: int) -> bool:
        symbol = stock.symbol
        if symbol not in self.holdings:
            return False
        holding = self.holdings[symbol]
        if holding['quantity'] < quantity:
            return False
        holding['quantity'] -= quantity
        if holding['quantity'] == 0:
            del self.holdings[symbol]
        return True

    def get_quantity(self, stock) -> int:
        return self.holdings.get(stock.symbol, {}).get('quantity', 0)

    def calculate_value(self) -> float:
        total = 0.0
        for holding in self.holdings.values():
            total += holding['quantity'] * holding['stock'].current_price
        return total

    def get_profit_loss(self) -> dict:
        total_cost = 0.0
        total_current = 0.0
        for holding in self.holdings.values():
            qty = holding['quantity']
            cost_basis = holding['cost_basis']
            current_price = holding['stock'].current_price
            total_cost += qty * cost_basis
            total_current += qty * current_price
        profit_loss = total_current - total_cost
        percentage = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
        return {
            'profit_loss': profit_loss,
            'percentage': percentage,
            'cost_total': total_cost,
            'current_value': total_current
        }

    def get_holdings_summary(self) -> List[dict]:
        summary = []
        for symbol, holding in self.holdings.items():
            qty = holding['quantity']
            cost_basis = holding['cost_basis']
            current_price = holding['stock'].current_price
            market_value = qty * current_price
            pl = market_value - qty * cost_basis
            summary.append({
                'symbol': symbol,
                'quantity': qty,
                'cost_basis': cost_basis,
                'current_price': current_price,
                'market_value': market_value,
                'profit_loss': pl
            })
        return summary


class Transaction:
    """Immutable record of an executed trade."""

    def __init__(self, transaction_id: str, order):
        self.transaction_id = transaction_id
        self.order = order
        self.execution_price = order.execution_price
        self.timestamp = datetime.now()

    def __repr__(self):
        return (f"Transaction({self.transaction_id}, "
                f"{self.order.order_type.value} {self.order.quantity} "
                f"{self.order.stock.symbol} @ ${self.execution_price:.2f})")


class Account:
    def __init__(self, account_id: str, user: User, initial_balance: float = 0.0):
        self.account_id = account_id
        self.user = user
        self.balance = initial_balance
        self.portfolio = Portfolio()
        self.transaction_history: List[Transaction] = []
        self._lock = threading.RLock()  # RLock allows re-entrant locking within same thread

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        with self._lock:
            self.balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0:
            return False
        with self._lock:
            if self.balance < amount:
                return False
            self.balance -= amount
        return True

    def get_balance(self) -> float:
        return self.balance

    def get_net_worth(self) -> float:
        return self.balance + self.portfolio.calculate_value()

    def record_transaction(self, order):
        txn_id = f"TXN_{len(self.transaction_history) + 1}_{int(time.time())}"
        self.transaction_history.append(Transaction(txn_id, order))

    def __repr__(self):
        return f"Account({self.account_id}, {self.user.name}, ${self.balance:.2f})"


# ============================================================
# PRICE OBSERVERS
# ============================================================

class PriceObserver(ABC):
    @abstractmethod
    def update(self, stock, old_price: float, new_price: float):
        pass


class ConsoleObserver(PriceObserver):
    def update(self, stock, old_price: float, new_price: float):
        direction = "UP" if new_price > old_price else "DOWN"
        print(f"  [PRICE {direction}] {stock.symbol}: ${old_price:.2f} -> ${new_price:.2f}")


class LimitOrderObserver(PriceObserver):
    """Triggers limit-order evaluation after every price change."""
    def __init__(self, exchange):
        self.exchange = exchange

    def update(self, stock, old_price: float, new_price: float):
        self.exchange.check_and_execute_limit_orders(stock)


class AlertObserver(PriceObserver):
    def __init__(self, threshold: float, label: str = "ALERT"):
        self.threshold = threshold
        self.label = label

    def update(self, stock, old_price: float, new_price: float):
        if new_price >= self.threshold:
            print(f"  [{self.label}] {stock.symbol} reached ${new_price:.2f} "
                  f"(threshold: ${self.threshold:.2f})")


# ============================================================
# STOCK
# ============================================================

class Stock:
    def __init__(self, symbol: str, name: str, initial_price: float):
        self.symbol = symbol
        self.name = name
        self.current_price = initial_price
        self._observers: List[PriceObserver] = []
        self.price_history: List[float] = [initial_price]
        self._lock = threading.Lock()

    def add_observer(self, observer: PriceObserver):
        with self._lock:
            self._observers.append(observer)

    def remove_observer(self, observer: PriceObserver):
        with self._lock:
            self._observers.remove(observer)

    def update_price(self, new_price: float):
        with self._lock:
            old_price = self.current_price
            self.current_price = new_price
            self.price_history.append(new_price)
            observers_copy = list(self._observers)

        for obs in observers_copy:
            obs.update(self, old_price, new_price)

    def get_quote(self) -> float:
        return self.current_price

    def __repr__(self):
        return f"Stock({self.symbol}, ${self.current_price:.2f})"


# ============================================================
# ORDER
# ============================================================

class Order:
    def __init__(self, order_id: str, account: Account, stock: Stock,
                 quantity: int, order_type: OrderType, price_type: PriceType,
                 limit_price: Optional[float] = None):
        self.order_id = order_id
        self.account = account
        self.stock = stock
        self.quantity = quantity
        self.order_type = order_type
        self.price_type = price_type
        self.limit_price = limit_price
        self.status = OrderStatus.PENDING
        self.execution_price: Optional[float] = None
        self.timestamp = datetime.now()

    def execute(self, execution_price: float) -> bool:
        if self.status != OrderStatus.PENDING:
            raise InvalidStateError(f"Cannot execute order in state {self.status}")
        self.status = OrderStatus.EXECUTED
        self.execution_price = execution_price
        return True

    def cancel(self) -> bool:
        if self.status not in [OrderStatus.PENDING, OrderStatus.REJECTED]:
            raise InvalidStateError(f"Cannot cancel order in state {self.status}")
        self.status = OrderStatus.CANCELLED
        return True

    def reject(self):
        self.status = OrderStatus.REJECTED

    def __repr__(self):
        return (f"Order({self.order_id}, {self.order_type.value} "
                f"{self.quantity} {self.stock.symbol} [{self.status.value}])")


# ============================================================
# ORDER STRATEGIES
# ============================================================

class OrderStrategy(ABC):
    @abstractmethod
    def can_execute(self, order: Order) -> bool:
        pass

    @abstractmethod
    def get_execution_price(self, order: Order) -> Optional[float]:
        pass


class MarketOrderStrategy(OrderStrategy):
    def can_execute(self, order: Order) -> bool:
        return True

    def get_execution_price(self, order: Order) -> Optional[float]:
        return order.stock.current_price


class LimitOrderStrategy(OrderStrategy):
    def can_execute(self, order: Order) -> bool:
        if order.order_type == OrderType.BUY:
            return order.stock.current_price <= order.limit_price
        else:
            return order.stock.current_price >= order.limit_price

    def get_execution_price(self, order: Order) -> Optional[float]:
        if self.can_execute(order):
            return order.stock.current_price
        return None


# ============================================================
# ORDER FACTORY
# ============================================================

class OrderFactory:
    _order_counter = 0
    _counter_lock = threading.Lock()

    @staticmethod
    def create_order(account: Account, stock: Stock, quantity: int,
                     order_type: OrderType, price_type: PriceType,
                     limit_price: Optional[float] = None) -> Order:
        with OrderFactory._counter_lock:
            OrderFactory._order_counter += 1
            order_id = f"ORD_{OrderFactory._order_counter}_{int(time.time())}"

        if quantity <= 0:
            raise InvalidOrderError("Quantity must be positive")
        if price_type == PriceType.LIMIT and limit_price is None:
            raise InvalidOrderError("Limit price required for limit orders")

        return Order(order_id, account, stock, quantity, order_type, price_type, limit_price)


# ============================================================
# STOCK EXCHANGE (Singleton + Central Coordinator)
# ============================================================

class StockExchange:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Fix: accept *args/**kwargs so __init__ calls don't raise TypeError
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.stocks: Dict[str, Stock] = {}
            self.orders: Dict[str, Order] = {}
            self.accounts: Dict[str, Account] = {}
            self._pending_limit_orders: List[Order] = []
            self._global_observers: List[PriceObserver] = []
            self._strategies: Dict[PriceType, OrderStrategy] = {
                PriceType.MARKET: MarketOrderStrategy(),
                PriceType.LIMIT: LimitOrderStrategy(),
            }
            # RLock: exchange lock may be held while calling account methods
            self._lock = threading.RLock()
            self._account_counter = 0
            self._initialized = True

    @staticmethod
    def get_instance() -> 'StockExchange':
        return StockExchange()

    # ---------- Registration ----------

    def add_stock(self, stock: Stock):
        with self._lock:
            self.stocks[stock.symbol] = stock
            # Attach global observers to each new stock
            for obs in self._global_observers:
                stock.add_observer(obs)

    def register_account(self, user: User, initial_balance: float = 0.0) -> Account:
        with self._lock:
            self._account_counter += 1
            account_id = f"ACC_{self._account_counter}"
            account = Account(account_id, user, initial_balance)
            self.accounts[account_id] = account
        return account

    def add_observer(self, observer: PriceObserver):
        """Register a global observer that receives updates from ALL stocks."""
        with self._lock:
            self._global_observers.append(observer)
            for stock in self.stocks.values():
                stock.add_observer(observer)

    # ---------- Price Updates ----------

    def update_stock_price(self, symbol: str, new_price: float):
        with self._lock:
            stock = self.stocks.get(symbol)
        if stock is None:
            print(f"  [ERROR] Stock {symbol} not found")
            return
        # update_price calls observers (including LimitOrderObserver) outside lock
        stock.update_price(new_price)

    def check_and_execute_limit_orders(self, stock: Stock):
        """Evaluate pending limit orders for a stock after a price change."""
        with self._lock:
            pending = [o for o in self._pending_limit_orders
                       if o.stock.symbol == stock.symbol and o.status == OrderStatus.PENDING]

        strategy = self._strategies[PriceType.LIMIT]
        for order in pending:
            if strategy.can_execute(order):
                if order.order_type == OrderType.BUY:
                    self.execute_buy_order(order)
                else:
                    self.execute_sell_order(order)

    # ---------- Order Placement ----------

    def place_order(self, order: Order) -> bool:
        with self._lock:
            self.orders[order.order_id] = order

        strategy = self._strategies[order.price_type]

        if order.price_type == PriceType.MARKET:
            if order.order_type == OrderType.BUY:
                return self.execute_buy_order(order)
            else:
                return self.execute_sell_order(order)
        else:  # LIMIT
            if strategy.can_execute(order):
                if order.order_type == OrderType.BUY:
                    return self.execute_buy_order(order)
                else:
                    return self.execute_sell_order(order)
            else:
                with self._lock:
                    self._pending_limit_orders.append(order)
                print(f"  [QUEUED] {order} pending limit @ ${order.limit_price:.2f}")
                return True

    def execute_buy_order(self, order: Order) -> bool:
        strategy = self._strategies[order.price_type]
        execution_price = strategy.get_execution_price(order)
        if execution_price is None:
            return False

        total_cost = order.quantity * execution_price

        with self._lock:
            account = order.account
            with account._lock:
                if account.balance < total_cost:
                    order.reject()
                    print(f"  [REJECTED] {order} — insufficient funds "
                          f"(need ${total_cost:.2f}, have ${account.balance:.2f})")
                    return False

                account.balance -= total_cost
                account.portfolio.add_holding(order.stock, order.quantity, execution_price)
                order.execute(execution_price)
                account.record_transaction(order)

            # Remove from pending if it was a limit order
            if order in self._pending_limit_orders:
                self._pending_limit_orders.remove(order)

        print(f"  [EXECUTED] {order.order_type.value.upper()} {order.quantity} "
              f"{order.stock.symbol} @ ${execution_price:.2f} "
              f"(cost ${total_cost:.2f}) | balance ${order.account.balance:.2f}")
        return True

    def execute_sell_order(self, order: Order) -> bool:
        strategy = self._strategies[order.price_type]
        execution_price = strategy.get_execution_price(order)
        if execution_price is None:
            return False

        proceeds = order.quantity * execution_price

        with self._lock:
            account = order.account
            with account._lock:
                if account.portfolio.get_quantity(order.stock) < order.quantity:
                    order.reject()
                    print(f"  [REJECTED] {order} — insufficient shares")
                    return False

                account.portfolio.remove_holding(order.stock, order.quantity)
                account.balance += proceeds
                order.execute(execution_price)
                account.record_transaction(order)

            if order in self._pending_limit_orders:
                self._pending_limit_orders.remove(order)

        print(f"  [EXECUTED] {order.order_type.value.upper()} {order.quantity} "
              f"{order.stock.symbol} @ ${execution_price:.2f} "
              f"(proceeds ${proceeds:.2f}) | balance ${order.account.balance:.2f}")
        return True

    # ---------- Reset (for testing) ----------

    def _reset(self):
        """Reset singleton state — use only in tests."""
        with self._lock:
            self.stocks.clear()
            self.orders.clear()
            self.accounts.clear()
            self._pending_limit_orders.clear()
            self._global_observers.clear()
            self._account_counter = 0


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  ONLINE STOCK BROKERAGE — DEMO")
    print("=" * 65)

    exchange = StockExchange.get_instance()
    exchange._reset()

    # ── Global observers ────────────────────────────────────────────
    exchange.add_observer(ConsoleObserver())
    exchange.add_observer(LimitOrderObserver(exchange))

    # ── Stocks ──────────────────────────────────────────────────────
    apple = Stock("AAPL", "Apple Inc.", 150.00)
    google = Stock("GOOGL", "Alphabet Inc.", 2800.00)
    exchange.add_stock(apple)
    exchange.add_stock(google)

    # Add a threshold alert directly to AAPL
    apple.add_observer(AlertObserver(threshold=165.00, label="PRICE ALERT"))

    # ── User & Account ───────────────────────────────────────────────
    user = User("U001", "Alice", "alice@email.com", "555-0001")
    account = exchange.register_account(user, initial_balance=10_000.00)
    print(f"\n  Setup: {account} | Net worth ${account.get_net_worth():,.2f}")

    # ── Demo 1: Market Buy ──────────────────────────────────────────
    print("\n[Demo 1] Market Buy — 10 AAPL @ $150")
    order1 = OrderFactory.create_order(account, apple, 10, OrderType.BUY, PriceType.MARKET)
    exchange.place_order(order1)

    # ── Demo 2: Portfolio Valuation ─────────────────────────────────
    print("\n[Demo 2] Portfolio After Market Buy")
    pnl = account.portfolio.get_profit_loss()
    print(f"  Portfolio value  : ${account.portfolio.calculate_value():,.2f}")
    print(f"  Cost basis total : ${pnl['cost_total']:,.2f}")
    print(f"  Profit / Loss    : ${pnl['profit_loss']:+,.2f} ({pnl['percentage']:+.2f}%)")
    print(f"  Account net worth: ${account.get_net_worth():,.2f}")

    # ── Demo 3: Limit Sell — queue then trigger ─────────────────────
    print("\n[Demo 3] Limit Sell — 5 AAPL @ $160 (currently $150 → queued)")
    order2 = OrderFactory.create_order(
        account, apple, 5, OrderType.SELL, PriceType.LIMIT, limit_price=160.00
    )
    exchange.place_order(order2)

    print("\n  Updating AAPL price to $165 → triggers limit sell + alert")
    exchange.update_stock_price("AAPL", 165.00)

    pnl = account.portfolio.get_profit_loss()
    print(f"  Portfolio value  : ${account.portfolio.calculate_value():,.2f}")
    print(f"  Profit / Loss    : ${pnl['profit_loss']:+,.2f} ({pnl['percentage']:+.2f}%)")

    # ── Demo 4: Full Cycle — buy GOOGL, price up, market sell ───────
    print("\n[Demo 4] Full Trading Cycle — Buy GOOGL, price rises, sell")
    order3 = OrderFactory.create_order(account, google, 1, OrderType.BUY, PriceType.MARKET)
    exchange.place_order(order3)

    print("  Updating GOOGL price to $3000")
    exchange.update_stock_price("GOOGL", 3000.00)

    order4 = OrderFactory.create_order(account, google, 1, OrderType.SELL, PriceType.MARKET)
    exchange.place_order(order4)

    # ── Final Summary ───────────────────────────────────────────────
    print("\n[Summary]")
    print(f"  Cash balance : ${account.get_balance():,.2f}")
    print(f"  Net worth    : ${account.get_net_worth():,.2f}")
    print(f"  Transactions : {len(account.transaction_history)}")
    for txn in account.transaction_history:
        print(f"    {txn}")

    print("\n" + "=" * 65)
    print("  Demo complete — all scenarios passed.")
    print("=" * 65)
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|--------------|------------|
| **place_order (market)** | RLock on exchange + RLock on account | Atomic balance check and deduction |
| **place_order (limit — queue)** | RLock on exchange | Safe append to pending list |
| **check_and_execute_limit_orders** | RLock on exchange; then per-order execution | No duplicate execution on concurrent price updates |
| **update_stock_price** | Stock-level Lock; observers notified outside lock | Lock not held during potentially slow observer callbacks |
| **account.deposit / withdraw** | RLock on account | No double-spend |
| **Singleton init** | Class-level Lock (double-checked) | Only one instance created under race |

**Concurrency Principles Applied**:
1. `threading.RLock` replaces `threading.Lock` throughout — exchange lock can be re-entered within the same thread without deadlock (e.g., `execute_buy_order` → `account._lock`).
2. Observers are notified **outside** the main exchange lock to prevent lock contention from slow notification callbacks.
3. Double-checked locking in `__new__` guards singleton creation.
4. `_pending_limit_orders` access always guarded; list snapshot taken before iterating.

---

## Demo Scenarios

### Demo 1: Setup & Deposit

```python
# Initialize system
exchange = StockExchange.get_instance()
exchange.add_observer(ConsoleObserver())

# Create user and account
user = User("U001", "Alice", "alice@email.com", "555-0001")
account = exchange.register_account(user, initial_balance=10000.00)

# Add stocks
apple = Stock("AAPL", "Apple Inc.", 150.00)
google = Stock("GOOGL", "Alphabet Inc.", 2800.00)
exchange.add_stock(apple)
exchange.add_stock(google)

print(f"Deposit: Account created with ${account.get_balance():.2f}")
```

### Demo 2: Market Orders

```python
# Place market buy order
order1 = OrderFactory.create_order(
    account, apple, 10, OrderType.BUY, PriceType.MARKET
)
exchange.place_order(order1)

print(f"Market Buy: 10 AAPL @ ${apple.current_price:.2f}")
print(f"   Total Cost: ${order1.quantity * apple.current_price:.2f}")
```

### Demo 3: Portfolio Valuation

```python
pnl = account.portfolio.get_profit_loss()
print(f"Portfolio Value: ${account.portfolio.calculate_value():.2f}")
print(f"   Profit/Loss: ${pnl['profit_loss']:+,.2f}")
print(f"   Return: {pnl['percentage']:+.2f}%")
```

### Demo 4: Limit Orders

```python
# Place limit sell order
order2 = OrderFactory.create_order(
    account, apple, 5, OrderType.SELL, PriceType.LIMIT, limit_price=160.00
)
exchange.place_order(order2)

print(f"Limit Sell: 5 AAPL @ $160.00 (currently ${apple.current_price:.2f})")

# Trigger execution by updating price
exchange.update_stock_price("AAPL", 165.00)
print(f"Price increased to $165.00 -> Limit order executed!")
```

### Demo 5: Full Trading Cycle

```python
# Complete workflow: buy → hold → sell → profit
order3 = OrderFactory.create_order(account, google, 1, OrderType.BUY, PriceType.MARKET)
exchange.place_order(order3)

# Price increase
exchange.update_stock_price("GOOGL", 3000.00)

# Sell at higher price
order4 = OrderFactory.create_order(account, google, 1, OrderType.SELL, PriceType.MARKET)
exchange.place_order(order4)

print(f"Final Balance: ${account.get_balance():,.2f}")
print(f"   Net Worth: ${account.get_net_worth():,.2f}")
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you calculate profit/loss for a portfolio?**

Track **cost basis** (average purchase price) for each holding.

- **Cost Basis**: `Σ(purchase_price × quantity) / total_quantity` (for multiple purchases)
- **Current Value**: `quantity × current_price`
- **Profit/Loss**: `current_value - (quantity × cost_basis)`
- **Percentage**: `(profit_loss / total_cost) × 100`

```python
def get_profit_loss(self) -> dict:
    total_cost = 0.0
    total_current = 0.0

    for symbol, holding in self.holdings.items():
        quantity = holding['quantity']
        cost_basis = holding['cost_basis']
        current_price = holding['stock'].current_price

        total_cost += quantity * cost_basis
        total_current += quantity * current_price

    profit_loss = total_current - total_cost
    percentage = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0

    return {
        'profit_loss': profit_loss,
        'percentage': percentage,
        'cost_total': total_cost,
        'current_value': total_current
    }
```

**Q2: What is the difference between market and limit orders?**

- **Market Order**: Execute immediately at current market price. Guarantees execution but not price.
- **Limit Order**: Execute only when price condition is met. Guarantees price but not execution.

Example — Stock trading at $100:
- **Market Buy**: Executes at $100 (or current ask)
- **Limit Buy @ $95**: Waits until price drops to $95 or below
- **Limit Sell @ $110**: Waits until price rises to $110 or above

**Q3: Why use Observer pattern for price updates?**

Decouples price updates from dependent components. When stock price changes, multiple listeners react independently:
- Portfolio recalculates value
- Limit orders check execution conditions
- Price alerts trigger notifications
- UI updates in real-time

Without Observer, `Stock` would need to know about all dependent components (tight coupling).

**Q4: How do you prevent race conditions in concurrent order placement?**

1. **Thread-safe Singleton**: Double-checked lock for instance creation
2. **Atomic Operations**: `RLock` guards fund deduction + portfolio update as a single unit
3. **Order Book Locking**: Synchronized access to `_pending_limit_orders`
4. **Database layer**: ACID guarantees
5. **Optimistic Locking**: Version numbers to detect conflicts in distributed settings

```python
with self._lock:                    # exchange lock
    with account._lock:             # account lock (RLock — re-entrant safe)
        if account.balance >= total_cost:
            account.balance -= total_cost
            portfolio.add_holding(stock, quantity, execution_price)
        else:
            order.status = OrderStatus.REJECTED
```

**Q5: What if user places conflicting orders (buy + sell same stock)?**

Allow both, but execute sequentially using price-time priority:
1. User holds 100 shares @ $50 cost
2. Places Limit Sell @ $100
3. Places Limit Buy @ $80 (averaging down)
4. When price hits $80: Buy executes first (FIFO)
5. When price hits $100: Sell executes
6. Portfolio now has 200 shares @ average cost $70

Order of execution is critical for P&L tracking.

---

### Intermediate Questions

**Q6: How do you handle limit orders that trigger simultaneously?**

Use **price-time priority**:
1. Sort pending limit orders by price (best price first)
2. Within same price, sort by timestamp (FIFO)
3. Execute orders sequentially in priority order
4. Check funds/shares availability before each execution

```python
def check_and_execute_limit_orders(self, stock: Stock):
    relevant_orders = [o for o in self.pending_orders if o.stock == stock]

    # Sort by price-time priority
    buy_orders = sorted([o for o in relevant_orders if o.order_type == OrderType.BUY],
                       key=lambda o: (-o.limit_price, o.timestamp))

    for order in buy_orders:
        if self.order_strategy[order.price_type].can_execute(order):
            self.execute_order(order)
```

**Q7: How do you ensure atomicity in buy/sell operations?**

Use **two-phase commit**:

Phase 1 — Validation:
1. Check sufficient funds (buy) or shares (sell)
2. Lock account balance
3. Verify order parameters

Phase 2 — Execution (all or nothing):
1. Deduct funds / add cash
2. Update portfolio
3. Record transaction
4. Release lock
5. Notify observers

If ANY step fails, rollback all changes.

```python
try:
    with exchange._lock:
        # Phase 1: Validate
        if order.order_type == OrderType.BUY:
            total_cost = order.quantity * execution_price
            if account.balance < total_cost:
                raise InsufficientFundsError()

        # Phase 2: Execute
        account.balance -= total_cost
        portfolio.add_holding(order.stock, order.quantity, execution_price)
        order.execute(execution_price)

        return True
except Exception:
    # Rollback
    return False
```

**Q8: How do you handle funds being withdrawn mid-trade?**

Lock funds during order lifecycle:
1. User has $10,000 balance
2. Places buy order for $5,000 (status=PENDING)
3. Tries to withdraw $7,000 → Reject (only $5,000 available)
4. Order executes → funds locked
5. Now withdrawal allowed only up to remaining balance

Funds are reserved from PENDING → EXECUTED, not before.

---

### Advanced Questions

**Q9: How would you scale this system to handle millions of users?**

Multi-tier microservices architecture:

**Tier 1: API Gateway** — Load balancer + session affinity

**Tier 2: Microservices**
- Order Service: Place, execute, cancel orders
- Portfolio Service: Holdings, valuation, P&L
- Market Data Service: Real-time prices, quotes
- User Service: Account management

**Tier 3: Storage**
- PostgreSQL with sharding by user_id
- Redis for distributed locks, caching
- Kafka for event streaming (order events, price updates)

**Tier 4: Caching**
- Redis for real-time prices (1-min TTL)
- Cache portfolio values (5-sec TTL)

```
Load Balancer
    ├─ Order Service Replica 1
    ├─ Order Service Replica 2
    ├─ Portfolio Service Replica 1
    ├─ Portfolio Service Replica 2
    └─ Market Data Service (central)
    ↓
PostgreSQL (sharded by user_id)
Redis (distributed locks, caching)
Kafka (event streaming)
```

**Q10: What metrics would you track?**

Business Metrics: Trading volume, active users, average order size, revenue from fees, user retention.

Performance Metrics: Order execution latency (p50/p95/p99), API response times, portfolio valuation time, WebSocket stability, system throughput (orders/sec).

Operational Metrics: Error rate, order rejection reasons, pending order queue length, price update frequency, uptime.

User Behavior: Most traded stocks, buy vs sell ratio, market vs limit ratio, average holding period, P&L distribution.

---

## Scaling Q&A

### Q1: How would you scale to 1M concurrent users and 100M orders/day (1,157 orders/sec)?

**Architecture**:
```
Global Load Balancer
    ├─ Region 1 (US)
    │  ├─ Order Service Cluster (100 pods)
    │  ├─ Portfolio Service Cluster (50 pods)
    │  └─ Market Data Cache (warm standby)
    ├─ Region 2 (EU)
    │  ├─ Order Service Cluster (50 pods)
    │  ├─ Portfolio Service Cluster (25 pods)
    │  └─ Market Data Cache
    └─ Region 3 (APAC)
       ├─ Order Service Cluster (30 pods)
       ├─ Portfolio Service Cluster (20 pods)
       └─ Market Data Cache

Shared Layer:
├─ PostgreSQL (1000 shards by user_id % 1000)
├─ Redis (distributed locks, price cache)
├─ Kafka (order events, price updates)
└─ Elasticsearch (order history search)
```

Per-Region Throughput: US 600 TPS | EU 400 TPS | APAC 157 TPS | **Total: 1,157 TPS**

---

### Q2: How to prevent overbooking (double-execution) in distributed settings?

Pessimistic locking with Redis:

```python
# Instead of threading.Lock
def execute_sell_order(self, order: Order):
    with redis_lock.acquire(f"user-{order.account.user_id}", timeout=5):
        if order.account.portfolio.get_quantity(order.stock) < order.quantity:
            order.status = OrderStatus.REJECTED
            return False

        order.account.portfolio.remove_holding(order.stock, order.quantity)
        return True
```

Only one replica can execute per user at a time globally. Prevents overselling.

---

### Q3: How to sync portfolio valuations across replicas?

**Option 1: Pessimistic Locking** — Read from primary DB → Lock row → Check balance → Execute → Unlock. Consistent but high latency.

**Option 2: Optimistic Locking** — Read portfolio version (v1), calculate P&L locally, try update: if version still v1 → commit, else retry. Fast but eventual.

**Option 3: Event Sourcing** — All order events → Kafka topic. Order Service publishes. Portfolio Service subscribes and updates async. Eventually consistent, full audit trail.

**Recommendation**:
- Market Orders: Pessimistic (critical consistency)
- Limit Orders: Optimistic (can retry)
- Portfolio Valuation: Event sourcing (async acceptable)

---

### Q4: How to handle peak traffic (holiday trading 5000+ TPS)?

Before peak: Auto-scale to 2000 Order Service pods, pre-warm price cache, increase DB connection pool, increase Kafka partitions.

During peak:
```
Order Request
    ↓
If queue size > 10K: Reject with "Service busy, retry later"
Else: Queue order
    ↓
Worker pool processes at 1000 TPS max
    ↓
Execute order atomically
    ↓
Queue notification event (async)
    ↓
Return success
```

---

### Q5: How to scale notifications to 100M order events/day?

Kafka + worker pool:

```
Order Event → Kafka Topic (10 partitions)
    ├─ Worker 1: Email notifier (100/sec)
    ├─ Worker 2: Email notifier (100/sec)
    ├─ Worker 3: SMS notifier (50/sec)
    └─ Worker 4: Push notifier (50/sec)
    ↓
Batch 100 notifications
    ↓
SendGrid/Twilio/Firebase APIs
    ↓
99.9% delivery within 30 seconds
```

Benefits: Parallel processing, batch efficiency, fault isolation (email down ≠ SMS down), auto-retry, per-channel monitoring.

---

### Q6: How to handle order search across 100M+ orders?

Elasticsearch with aggregation:

```
Elasticsearch Cluster (100 shards)
    ├─ Shard 1: Orders 1-1M
    ...
    └─ Shard 100: Orders 99M-100M

Query: symbol=AAPL AND status=EXECUTED AND date=[2024-01-01, 2024-01-31]
    ↓
ES searches all shards in parallel
    ↓
Returns matching documents in <100ms (vs 10s with array scan)
```

---

### Q7: How to ensure 99.9% uptime at scale?

Active-Active multi-region configuration:

```
Region 1 (US) [Primary]
    ├─ 3x Order Service replicas
    ├─ 3x Portfolio Service replicas
    ├─ PostgreSQL Primary + 2 replicas
    └─ Redis Cluster (3 nodes)

Region 2 (EU) [Hot Standby]
    ├─ 3x replicas (reads + fail-over writes)
    └─ PostgreSQL Replica (read-only)

Health Checks (every 10s):
- Response time > 1000ms → degrade
- Error rate > 0.1% → alert
- DB unreachable → failover

RTO < 30s | RPO < 5 min
```

---

### Q8: How to perform rolling updates without downtime?

Blue-Green deployment with traffic migration:

```
Week 1-2: Deploy v2 to "blue" (isolated, no traffic)
Week 3: Route 1% of traffic to blue, monitor for 1h
Week 4: 25% of traffic to blue
Week 5: 50%
Week 6: 100%

Rollback instantly if:
- Error rate > 1%
- Latency p99 > 2000ms
- Data corruption detected
```

---

### Q9: How to partition users across multiple databases?

Shard by user_id using consistent hashing:

```
Shard Ring:
├─ Node 1: user_ids 1-1M
├─ Node 2: user_ids 1M-2M
├─ Node 3: user_ids 2M-3M
└─ Node 4: user_ids 3M-4M

Query for user 500K:
    hash(500K) → Node 1
    Query Node 1 PostgreSQL

No cross-shard queries (fast); easy rebalancing with consistent hashing.
```

---

### Q10: How to test scaling without actual infrastructure?

Load testing + chaos testing:

```bash
wrk -t12 -c100000 -d30s \
  --script=place_order.lua \
  "https://api.brokerage.com/orders"

Monitor:
- Response time p99 < 500ms
- Error rate < 0.1%
- CPU/Memory saturation
- Database connection pool usage
```

Chaos tests:
1. Kill random replica → system should failover
2. Add 100ms latency to DB → measure degradation
3. Partition network for 30s → test recovery
4. Spike 100 TPS → 5000 TPS → test auto-scaling
5. Slow down price cache → verify fallback to DB

Verify after tests: no order double-execution, no lost funds, no stale portfolio values, payment consistency.

---

## Success Checklist

- [ ] Explain 6 design patterns clearly (Singleton, Strategy, Observer, State, Factory, Command)
- [ ] Draw UML diagram with all entities
- [ ] Implement market and limit orders
- [ ] Calculate portfolio profit/loss correctly using average cost basis
- [ ] Handle concurrent order placement with RLock
- [ ] Demonstrate limit order triggered by price update (Observer chain)
- [ ] Discuss scaling to 1M users (microservices, sharding, Kafka)
- [ ] Run all 5 demo scenarios successfully
- [ ] Answer 10+ interview questions confidently
- [ ] Explain thread-safety analysis (RLock vs Lock, notify outside lock)

---

**You're ready for your interview — let's trade! 📈**
