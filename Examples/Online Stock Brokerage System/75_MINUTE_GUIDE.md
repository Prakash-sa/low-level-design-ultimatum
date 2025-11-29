# Online Stock Brokerage System - 75 Minute Interview Implementation Guide

## System Overview
A comprehensive stock trading platform enabling users to buy/sell stocks, manage portfolios, track real-time market data, execute market/limit orders, and monitor investment performance with profit/loss tracking.

---

## Requirements Clarification (First 10 minutes)

### Functional Requirements

**Core Trading Operations**:
- ✅ Users can create accounts and deposit/withdraw funds
- ✅ Real-time stock quotes and market data
- ✅ Place market orders (execute immediately at current price)
- ✅ Place limit orders (execute when price condition met)
- ✅ Portfolio management with holdings tracking
- ✅ Transaction history and audit trail
- ✅ Profit/loss calculation with cost basis tracking

**Account Management**:
- ✅ Multiple accounts per user
- ✅ Cash balance tracking
- ✅ Net worth calculation (cash + portfolio value)
- ✅ Fund deposits and withdrawals

**Order Types**:
- ✅ Market orders (immediate execution)
- ✅ Limit orders (conditional execution)
- ✅ Buy and sell operations
- ✅ Order cancellation

**Portfolio Features**:
- ✅ Holdings summary (stock, quantity, cost basis)
- ✅ Real-time valuation
- ✅ Profit/loss calculation per holding and total
- ✅ Average cost basis for multiple purchases

### Non-Functional Requirements

- **Performance**: Order execution < 100ms
- **Scalability**: Support 10,000+ concurrent users
- **Reliability**: 99.9% uptime during trading hours
- **Security**: Secure fund transfers, data encryption
- **Consistency**: Atomic transactions (no partial executions)

### Out of Scope (Can Discuss)

- ❌ Options, futures, derivatives trading
- ❌ Margin trading and short selling
- ❌ After-hours trading
- ❌ Real-time market data feeds (simulated)
- ❌ Regulatory compliance (SEC, FINRA)
- ❌ Tax reporting (1099 forms)
- ❌ Advanced order types (stop-loss, trailing stop, bracket orders)

**Scope Agreement**:
- ✅ Market and limit orders
- ✅ Portfolio tracking with profit/loss
- ✅ Real-time price updates
- ✅ Multiple users and accounts
- ✅ Transaction history
- ❌ Complex derivatives, margin, short selling (can discuss)

---

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Singleton** | Single exchange instance | `StockExchange.get_instance()` |
| **Strategy** | Order execution algorithms | `MarketOrderStrategy`, `LimitOrderStrategy` |
| **Observer** | Price update notifications | `PriceObserver` → `PortfolioObserver`, `LimitOrderObserver` |
| **State** | Order lifecycle | `OrderStatus` enum (PENDING → EXECUTED/CANCELLED) |
| **Factory** | Order creation | `OrderFactory.create_order()` |
| **Command** | Trading operations | `BuyCommand`, `SellCommand`, `CancelOrderCommand` |

---

## Core Classes & Implementation

### Enumerations

```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import threading

class OrderType(Enum):
    """Type of order: buy or sell"""
    BUY = "buy"
    SELL = "sell"

class PriceType(Enum):
    """Pricing strategy for order"""
    MARKET = "market"  # Execute at current market price
    LIMIT = "limit"    # Execute only at specified price or better

class OrderStatus(Enum):
    """Order lifecycle states"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class TransactionType(Enum):
    """Type of fund transaction"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BUY = "buy"
    SELL = "sell"
```

### 1. Stock Class

```python
class Stock:
    """Represents a tradable stock"""
    def __init__(self, symbol: str, name: str, current_price: float, sector: str = "Technology"):
        self.symbol = symbol
        self.name = name
        self.current_price = current_price
        self.sector = sector
        self.price_history: List[Tuple[datetime, float]] = []
        self.observers: List['PriceObserver'] = []
    
    def update_price(self, new_price: float):
        """Update stock price and notify observers"""
        old_price = self.current_price
        self.current_price = new_price
        self.price_history.append((datetime.now(), new_price))
        
        # Notify all observers of price change
        for observer in self.observers:
            observer.update(self, old_price, new_price)
    
    def add_observer(self, observer: 'PriceObserver'):
        """Subscribe to price updates"""
        self.observers.append(observer)
    
    def get_quote(self) -> Dict:
        """Get current quote information"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.current_price,
            'sector': self.sector,
            'timestamp': datetime.now()
        }
```

**Key Features**:
- Observer pattern for price updates
- Price history tracking
- Real-time quote retrieval

### 2. Portfolio Class

```python
class Portfolio:
    """Manages user's stock holdings"""
    def __init__(self):
        # holdings: {stock_symbol: {'quantity': int, 'cost_basis': float, 'stock': Stock}}
        self.holdings: Dict[str, Dict] = {}
    
    def add_holding(self, stock: Stock, quantity: int, purchase_price: float):
        """Add or update a holding with cost basis calculation"""
        symbol = stock.symbol
        
        if symbol in self.holdings:
            # Update average cost basis
            old_qty = self.holdings[symbol]['quantity']
            old_basis = self.holdings[symbol]['cost_basis']
            new_qty = old_qty + quantity
            new_basis = ((old_qty * old_basis) + (quantity * purchase_price)) / new_qty
            
            self.holdings[symbol] = {
                'stock': stock,
                'quantity': new_qty,
                'cost_basis': new_basis
            }
        else:
            self.holdings[symbol] = {
                'stock': stock,
                'quantity': quantity,
                'cost_basis': purchase_price
            }
    
    def remove_holding(self, stock_symbol: str, quantity: int) -> bool:
        """Remove shares from holding"""
        if stock_symbol not in self.holdings:
            return False
        
        holding = self.holdings[stock_symbol]
        if holding['quantity'] < quantity:
            return False
        
        holding['quantity'] -= quantity
        
        # Remove holding if quantity becomes zero
        if holding['quantity'] == 0:
            del self.holdings[stock_symbol]
        
        return True
    
    def calculate_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = 0.0
        for holding in self.holdings.values():
            stock = holding['stock']
            quantity = holding['quantity']
            total_value += quantity * stock.current_price
        return total_value
    
    def get_profit_loss(self) -> Dict:
        """Calculate profit/loss for entire portfolio"""
        total_cost = 0.0
        total_current = 0.0
        
        for holding in self.holdings.values():
            stock = holding['stock']
            quantity = holding['quantity']
            cost_basis = holding['cost_basis']
            
            cost = quantity * cost_basis
            current = quantity * stock.current_price
            
            total_cost += cost
            total_current += current
        
        profit_loss = total_current - total_cost
        percentage = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
        
        return {
            'total_cost': total_cost,
            'current_value': total_current,
            'profit_loss': profit_loss,
            'percentage': percentage
        }
```

**Key Features**:
- Average cost basis calculation for multiple purchases
- Real-time portfolio valuation
- Profit/loss tracking (absolute and percentage)

### 3. Account Class

```python
class Account:
    """User's trading account"""
    def __init__(self, account_id: str, user: 'User', initial_balance: float = 0.0):
        self.account_id = account_id
        self.user = user
        self.balance = initial_balance
        self.portfolio = Portfolio()
        self.transaction_history: List['Transaction'] = []
        self.created_at = datetime.now()
    
    def deposit(self, amount: float) -> bool:
        """Deposit funds into account"""
        if amount <= 0:
            return False
        self.balance += amount
        return True
    
    def withdraw(self, amount: float) -> bool:
        """Withdraw funds from account"""
        if amount <= 0 or amount > self.balance:
            return False
        self.balance -= amount
        return True
    
    def get_balance(self) -> float:
        """Get available cash balance"""
        return self.balance
    
    def get_net_worth(self) -> float:
        """Calculate total net worth (cash + portfolio value)"""
        return self.balance + self.portfolio.calculate_value()
    
    def add_transaction(self, transaction: 'Transaction'):
        """Record a transaction"""
        self.transaction_history.append(transaction)
```

**Key Features**:
- Cash balance management
- Portfolio integration
- Net worth calculation
- Transaction history

### 4. Order Class

```python
class Order:
    """Represents a buy/sell order"""
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
        self.executed_at: Optional[datetime] = None
    
    def execute(self, execution_price: float) -> bool:
        """Mark order as executed"""
        if self.status != OrderStatus.PENDING:
            return False
        
        self.execution_price = execution_price
        self.status = OrderStatus.EXECUTED
        self.executed_at = datetime.now()
        return True
    
    def cancel(self) -> bool:
        """Cancel pending order"""
        if self.status != OrderStatus.PENDING:
            return False
        
        self.status = OrderStatus.CANCELLED
        return True
    
    def reject(self) -> bool:
        """Reject order (insufficient funds, invalid params, etc.)"""
        if self.status != OrderStatus.PENDING:
            return False
        
        self.status = OrderStatus.REJECTED
        return True
```

**Key Features**:
- State machine (PENDING → EXECUTED/CANCELLED/REJECTED)
- Market and limit order support
- Execution tracking

### 5. Transaction Class

```python
class Transaction:
    """Records a completed trade"""
    def __init__(self, transaction_id: str, order: Order, execution_price: float,
                 quantity: int, transaction_type: TransactionType, fees: float = 0.0):
        self.transaction_id = transaction_id
        self.order = order
        self.execution_price = execution_price
        self.quantity = quantity
        self.transaction_type = transaction_type
        self.fees = fees
        self.total_amount = (quantity * execution_price) + fees
        self.timestamp = datetime.now()
    
    def get_details(self) -> Dict:
        """Get transaction details"""
        return {
            'transaction_id': self.transaction_id,
            'order_id': self.order.order_id,
            'stock': self.order.stock.symbol,
            'type': self.transaction_type.value,
            'quantity': self.quantity,
            'price': self.execution_price,
            'fees': self.fees,
            'total': self.total_amount,
            'timestamp': self.timestamp
        }
```

**Key Features**:
- Immutable transaction record
- Fee tracking
- Audit trail

### 6. User Class

```python
class User:
    """Represents a system user"""
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.accounts: List[Account] = []
        self.created_at = datetime.now()
    
    def create_account(self, initial_balance: float = 0.0) -> Account:
        """Create a new trading account"""
        account_id = f"ACC{len(self.accounts) + 1:03d}"
        account = Account(account_id, self, initial_balance)
        self.accounts.append(account)
        return account
```

**Key Features**:
- Multiple accounts per user
- Auto-generated account IDs

---

## Strategy Pattern (Order Execution)

```python
class OrderStrategy(ABC):
    """Abstract base class for order execution strategies"""
    @abstractmethod
    def can_execute(self, order: Order) -> bool:
        """Check if order can be executed"""
        pass
    
    @abstractmethod
    def get_execution_price(self, order: Order) -> Optional[float]:
        """Get execution price for order"""
        pass

class MarketOrderStrategy(OrderStrategy):
    """Execute immediately at current market price"""
    def can_execute(self, order: Order) -> bool:
        return True  # Market orders always execute
    
    def get_execution_price(self, order: Order) -> Optional[float]:
        return order.stock.current_price

class LimitOrderStrategy(OrderStrategy):
    """Execute only when price condition is met"""
    def can_execute(self, order: Order) -> bool:
        if order.limit_price is None:
            return False
        
        current_price = order.stock.current_price
        
        if order.order_type == OrderType.BUY:
            # Buy limit: execute if current price <= limit price
            return current_price <= order.limit_price
        else:
            # Sell limit: execute if current price >= limit price
            return current_price >= order.limit_price
    
    def get_execution_price(self, order: Order) -> Optional[float]:
        if self.can_execute(order):
            return order.stock.current_price
        return None
```

**Why Strategy Pattern?**
- Different order types have different execution logic
- Easy to add new order types (stop-loss, trailing stop)
- Encapsulates execution algorithms
- Testable in isolation

---

## Observer Pattern (Price Updates)

```python
class PriceObserver(ABC):
    """Observer interface for price updates"""
    @abstractmethod
    def update(self, stock: Stock, old_price: float, new_price: float):
        pass

class PortfolioObserver(PriceObserver):
    """Observes price changes to recalculate portfolio value"""
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
    
    def update(self, stock: Stock, old_price: float, new_price: float):
        # Portfolio value automatically updates since it references stock objects
        change_pct = ((new_price - old_price) / old_price) * 100
        # Could trigger alerts, logging, etc.

class LimitOrderObserver(PriceObserver):
    """Observes price changes to execute pending limit orders"""
    def __init__(self, exchange: 'StockExchange'):
        self.exchange = exchange
    
    def update(self, stock: Stock, old_price: float, new_price: float):
        # Check if any pending limit orders can now be executed
        self.exchange.check_limit_orders(stock)

class ConsoleObserver(PriceObserver):
    """Console-based observer for demo purposes"""
    def update(self, stock: Stock, old_price: float, new_price: float):
        timestamp = datetime.now().strftime("%H:%M:%S")
        change = new_price - old_price
        change_pct = (change / old_price) * 100
        arrow = "📈" if change >= 0 else "📉"
        print(f"[{timestamp}] {arrow} PRICE UPDATE: {stock.symbol} "
              f"${old_price:.2f} → ${new_price:.2f} ({change_pct:+.2f}%)")
```

**Why Observer Pattern?**
- Decouples price updates from dependent components
- Multiple listeners (portfolio, limit orders, alerts)
- Easy to add new observers without modifying Stock class
- Real-time reactivity

---

## Factory Pattern (Order Creation)

```python
class OrderFactory:
    """Factory for creating different types of orders"""
    _order_counter = 0
    
    @staticmethod
    def create_order(account: Account, stock: Stock, quantity: int,
                    order_type: OrderType, price_type: PriceType,
                    limit_price: Optional[float] = None) -> Order:
        """Create an order with auto-generated ID"""
        OrderFactory._order_counter += 1
        order_id = f"ORD{OrderFactory._order_counter:05d}"
        
        order = Order(
            order_id=order_id,
            account=account,
            stock=stock,
            quantity=quantity,
            order_type=order_type,
            price_type=price_type,
            limit_price=limit_price
        )
        
        return order
```

**Why Factory Pattern?**
- Centralized order creation
- Auto-generated unique IDs
- Validation before creation
- Easy to extend for new order types

---

## Command Pattern (Trading Operations)

```python
class Command(ABC):
    """Abstract command for trading operations"""
    @abstractmethod
    def execute(self) -> bool:
        pass

class BuyCommand(Command):
    """Command to execute a buy order"""
    def __init__(self, exchange: 'StockExchange', order: Order):
        self.exchange = exchange
        self.order = order
    
    def execute(self) -> bool:
        return self.exchange.execute_buy_order(self.order)

class SellCommand(Command):
    """Command to execute a sell order"""
    def __init__(self, exchange: 'StockExchange', order: Order):
        self.exchange = exchange
        self.order = order
    
    def execute(self) -> bool:
        return self.exchange.execute_sell_order(self.order)

class CancelOrderCommand(Command):
    """Command to cancel an order"""
    def __init__(self, order: Order):
        self.order = order
    
    def execute(self) -> bool:
        return self.order.cancel()
```

**Why Command Pattern?**
- Encapsulates operations as objects
- Enables undo/redo functionality
- Audit trail for trading operations
- Request queuing and logging

---

## StockExchange (Singleton + Controller)

```python
class StockExchange:
    """Singleton controller for the stock exchange"""
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
            self.stocks: Dict[str, Stock] = {}
            self.orders: List[Order] = []
            self.pending_orders: List[Order] = []
            self.market_data: Dict[str, MarketData] = {}
            self.transaction_counter = 0
            self.observers: List[PriceObserver] = []
            
            # Strategy mapping
            self.strategies: Dict[PriceType, OrderStrategy] = {
                PriceType.MARKET: MarketOrderStrategy(),
                PriceType.LIMIT: LimitOrderStrategy()
            }
            
            self.initialized = True
    
    @staticmethod
    def get_instance() -> 'StockExchange':
        """Get singleton instance"""
        return StockExchange()
    
    def add_stock(self, stock: Stock):
        """Add a stock to the exchange"""
        self.stocks[stock.symbol] = stock
        self.market_data[stock.symbol] = MarketData(stock)
        
        # Add exchange observers to stock
        for observer in self.observers:
            stock.add_observer(observer)
    
    def place_order(self, order: Order) -> bool:
        """Place an order on the exchange"""
        self.orders.append(order)
        
        # Get appropriate strategy
        strategy = self.strategies[order.price_type]
        
        # Try to execute immediately
        if strategy.can_execute(order):
            # Create and execute command
            if order.order_type == OrderType.BUY:
                command = BuyCommand(self, order)
            else:
                command = SellCommand(self, order)
            
            return command.execute()
        else:
            # Add to pending orders for later execution
            self.pending_orders.append(order)
            return True
    
    def execute_buy_order(self, order: Order) -> bool:
        """Execute a buy order"""
        strategy = self.strategies[order.price_type]
        execution_price = strategy.get_execution_price(order)
        
        if execution_price is None:
            order.reject()
            return False
        
        total_cost = (order.quantity * execution_price)
        
        # Check sufficient funds
        if order.account.balance < total_cost:
            order.reject()
            return False
        
        # Deduct funds
        order.account.balance -= total_cost
        
        # Add to portfolio
        order.account.portfolio.add_holding(order.stock, order.quantity, execution_price)
        
        # Mark order as executed
        order.execute(execution_price)
        
        # Create transaction record
        self.transaction_counter += 1
        transaction = Transaction(
            transaction_id=f"TXN{self.transaction_counter:05d}",
            order=order,
            execution_price=execution_price,
            quantity=order.quantity,
            transaction_type=TransactionType.BUY
        )
        order.account.add_transaction(transaction)
        
        return True
    
    def check_limit_orders(self, stock: Stock):
        """Check if any pending limit orders can be executed"""
        executed_orders = []
        
        for order in self.pending_orders:
            if order.stock.symbol != stock.symbol:
                continue
            
            strategy = self.strategies[order.price_type]
            if strategy.can_execute(order):
                # Execute order
                if order.order_type == OrderType.BUY:
                    self.execute_buy_order(order)
                else:
                    self.execute_sell_order(order)
                
                executed_orders.append(order)
        
        # Remove executed orders from pending
        for order in executed_orders:
            if order in self.pending_orders:
                self.pending_orders.remove(order)
```

**Key Responsibilities**:
- Manages all stocks and orders
- Executes trades atomically
- Maintains pending orders
- Coordinates strategies and commands
- Thread-safe singleton implementation

---

## UML Class Diagram

```
┌────────────────────────────────────────────┐
│      StockExchange (Singleton)             │
├────────────────────────────────────────────┤
│ - _instance: StockExchange                 │
│ - stocks: Dict[str, Stock]                 │
│ - orders: List[Order]                      │
│ - pending_orders: List[Order]              │
│ - strategies: Dict[PriceType, Strategy]    │
├────────────────────────────────────────────┤
│ + get_instance(): StockExchange            │
│ + add_stock(stock)                         │
│ + place_order(order)                       │
│ + execute_buy_order(order)                 │
│ + execute_sell_order(order)                │
│ + check_limit_orders(stock)                │
└────────────────────────────────────────────┘
           │
           │ manages
           ▼
    ┌─────────────┐
    │    Stock    │
    ├─────────────┤
    │ - symbol    │
    │ - price     │
    │ - observers │
    ├─────────────┤
    │+update_price()│
    │+add_observer()│
    └─────────────┘
           │
           │ notifies
           ▼
    ┌──────────────────────────┐
    │   PriceObserver (ABC)    │
    ├──────────────────────────┤
    │+update(stock, old, new)  │
    └────────┬─────────────────┘
             │
      ┌──────┴─────────┬──────────────┐
      ▼                ▼              ▼
┌───────────┐  ┌────────────┐  ┌──────────┐
│Portfolio  │  │LimitOrder  │  │Console   │
│Observer   │  │Observer    │  │Observer  │
└───────────┘  └────────────┘  └──────────┘

┌────────────────────────────────────────────┐
│           User                             │
├────────────────────────────────────────────┤
│ - user_id, name, email                     │
│ - accounts: List[Account]                  │
├────────────────────────────────────────────┤
│ + create_account()                         │
└────────────────────────────────────────────┘
           │
           │ HAS-MANY
           ▼
    ┌──────────────┐
    │   Account    │
    ├──────────────┤
    │ - balance    │
    │ - portfolio  │
    ├──────────────┤
    │+deposit()    │
    │+withdraw()   │
    │+get_net_worth()│
    └──────────────┘
           │
           │ HAS-ONE
           ▼
    ┌────────────────┐
    │   Portfolio    │
    ├────────────────┤
    │ - holdings     │
    ├────────────────┤
    │+add_holding()  │
    │+calculate_value()│
    │+get_profit_loss()│
    └────────────────┘

┌──────────────────────────────────────────┐
│      OrderStrategy (ABC)                 │
├──────────────────────────────────────────┤
│+can_execute(order): bool                 │
│+get_execution_price(order): float        │
└────────┬─────────────────────────────────┘
         │
    ┌────┴─────────┐
    ▼              ▼
┌─────────┐  ┌──────────┐
│Market   │  │Limit     │
│Order    │  │Order     │
│Strategy │  │Strategy  │
└─────────┘  └──────────┘

┌──────────────────────────────────────────┐
│          Command (ABC)                   │
├──────────────────────────────────────────┤
│+execute(): bool                          │
└────────┬─────────────────────────────────┘
         │
    ┌────┴───────────┬──────────────┐
    ▼                ▼              ▼
┌────────┐     ┌──────────┐  ┌──────────┐
│Buy     │     │Sell      │  │Cancel    │
│Command │     │Command   │  │Command   │
└────────┘     └──────────┘  └──────────┘
```

---

## Interview Q&A

### Basic Questions

**Q1: How do you calculate profit/loss for a portfolio?**

A: Track cost basis (average purchase price) for each holding. Calculate:
- **Cost Basis**: `Σ(purchase_price × quantity) / total_quantity` (for multiple purchases)
- **Current Value**: `quantity × current_price`
- **Profit/Loss**: `current_value - (quantity × cost_basis)`
- **Percentage**: `(profit_loss / total_cost) × 100`

```python
def get_profit_loss(self) -> Dict:
    total_cost = 0.0
    total_current = 0.0
    
    for holding in self.holdings.values():
        quantity = holding['quantity']
        cost_basis = holding['cost_basis']
        current_price = holding['stock'].current_price
        
        total_cost += quantity * cost_basis
        total_current += quantity * current_price
    
    profit_loss = total_current - total_cost
    percentage = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
    
    return {'profit_loss': profit_loss, 'percentage': percentage}
```

**Q2: What's the difference between market and limit orders?**

A:
- **Market Order**: Executes immediately at current market price. Guarantees execution but not price.
- **Limit Order**: Executes only when price condition is met. Guarantees price but not execution.

Example:
- Stock trading at $100
- Market Buy: Executes at $100 (or current ask)
- Limit Buy @ $95: Waits until price drops to $95 or below
- Limit Sell @ $110: Waits until price rises to $110 or above

**Q3: Why use Observer pattern for price updates?**

A: Decouples price updates from dependent components. When stock price changes, multiple listeners react independently:
- Portfolio recalculates value
- Limit orders check execution conditions
- Price alerts trigger notifications
- UI updates in real-time

Without Observer, Stock class would need to know about all dependent components (tight coupling).

### Intermediate Questions

**Q4: How do you prevent race conditions in concurrent order placement?**

A:
1. **Thread-safe Singleton**: Use lock for instance creation
2. **Atomic Operations**: Wrap fund deduction + portfolio update in transaction
3. **Order Book Locking**: Synchronize access to pending orders
4. **Database Transactions**: ACID guarantees for persistent storage
5. **Optimistic Locking**: Version numbers to detect conflicts

```python
class StockExchange:
    _lock = threading.Lock()
    
    def execute_buy_order(self, order: Order) -> bool:
        with self._lock:
            # Check funds
            if order.account.balance < total_cost:
                return False
            
            # Atomic: deduct funds + add holding
            order.account.balance -= total_cost
            order.account.portfolio.add_holding(...)
```

**Q5: How would you scale this system to handle millions of users?**

A:
**Architecture**:
- **Microservices**: Order service, Portfolio service, Market data service, User service
- **Message Queue**: Kafka for order events, price updates
- **Caching**: Redis for real-time prices, user sessions
- **Database**: PostgreSQL with sharding by user_id
- **Load Balancer**: Distribute requests across multiple instances

**Data Partitioning**:
- User accounts: Shard by user_id
- Order book: Partition by stock_symbol
- Price data: Time-series database (InfluxDB)

**Performance**:
- WebSocket for real-time price updates
- CDN for static assets
- Read replicas for portfolio queries
- Write-through cache for frequently traded stocks

**Q6: How do you handle limit orders that trigger simultaneously?**

A: Use **price-time priority**:
1. Sort pending limit orders by price (best price first)
2. Within same price, sort by timestamp (FIFO)
3. Execute orders sequentially in priority order
4. Check funds/shares availability before each execution

```python
def check_limit_orders(self, stock: Stock):
    # Filter relevant orders
    relevant_orders = [o for o in self.pending_orders if o.stock == stock]
    
    # Sort by price-time priority
    buy_orders = sorted([o for o in relevant_orders if o.order_type == OrderType.BUY],
                       key=lambda o: (-o.limit_price, o.timestamp))
    sell_orders = sorted([o for o in relevant_orders if o.order_type == OrderType.SELL],
                        key=lambda o: (o.limit_price, o.timestamp))
    
    # Execute in order
    for order in buy_orders + sell_orders:
        if self.can_execute(order):
            self.execute_order(order)
```

### Advanced Questions

**Q7: How would you implement stop-loss orders?**

A: Extend with `StopLossOrderStrategy`:

```python
class StopLossOrderStrategy(OrderStrategy):
    """Trigger sell when price falls below stop price"""
    def can_execute(self, order: Order) -> bool:
        if order.stop_price is None:
            return False
        
        # Sell when current price <= stop price
        return order.stock.current_price <= order.stop_price
    
    def get_execution_price(self, order: Order) -> Optional[float]:
        if self.can_execute(order):
            return order.stock.current_price  # Execute at market
        return None
```

**Order Flow**:
1. User places stop-loss sell @ $90 (stock currently at $100)
2. Order added to pending with `StopLossOrderStrategy`
3. Price drops to $89 → Observer triggers → Order executes at market price

**Q8: How do you ensure atomicity in buy/sell operations?**

A: Use **two-phase commit**:

**Phase 1 - Validation**:
1. Check sufficient funds (buy) or shares (sell)
2. Lock account balance
3. Verify order parameters

**Phase 2 - Execution** (all or nothing):
```python
def execute_buy_order(self, order: Order) -> bool:
    try:
        # Begin transaction
        total_cost = order.quantity * execution_price
        
        # Step 1: Deduct funds
        if order.account.balance < total_cost:
            raise InsufficientFundsError()
        order.account.balance -= total_cost
        
        # Step 2: Add holding
        order.account.portfolio.add_holding(
            order.stock, order.quantity, execution_price
        )
        
        # Step 3: Record transaction
        transaction = Transaction(...)
        order.account.add_transaction(transaction)
        
        # Step 4: Update order status
        order.execute(execution_price)
        
        # Commit transaction
        return True
    except Exception as e:
        # Rollback all changes
        self._rollback(order)
        return False
```

**In Production**: Use database transactions with BEGIN/COMMIT/ROLLBACK.

**Q9: How would you implement a trading fee structure?**

A: Add fees to `Transaction`:

```python
class FeeCalculator(ABC):
    @abstractmethod
    def calculate_fee(self, order: Order, execution_price: float) -> float:
        pass

class PercentageFeeCalculator(FeeCalculator):
    """Charge percentage of transaction value"""
    def __init__(self, fee_percentage: float = 0.001):  # 0.1%
        self.fee_percentage = fee_percentage
    
    def calculate_fee(self, order: Order, execution_price: float) -> float:
        transaction_value = order.quantity * execution_price
        return transaction_value * self.fee_percentage

class TieredFeeCalculator(FeeCalculator):
    """Lower fees for higher transaction volumes"""
    def calculate_fee(self, order: Order, execution_price: float) -> float:
        transaction_value = order.quantity * execution_price
        
        if transaction_value < 1000:
            return transaction_value * 0.002  # 0.2%
        elif transaction_value < 10000:
            return transaction_value * 0.001  # 0.1%
        else:
            return transaction_value * 0.0005  # 0.05%
```

**Usage**:
```python
fee_calculator = PercentageFeeCalculator(0.001)
fee = fee_calculator.calculate_fee(order, execution_price)
transaction = Transaction(..., fees=fee)
```

**Q10: What metrics would you track for this system?**

A:
**Business Metrics**:
- Trading volume (daily, monthly)
- Number of active users
- Average transaction size
- Revenue from fees
- User retention rate

**Performance Metrics**:
- Order execution latency (p50, p95, p99)
- API response times
- Database query performance
- WebSocket connection stability
- System throughput (orders/second)

**Operational Metrics**:
- Error rate (failed orders, rejections)
- Order rejection reasons (insufficient funds, invalid params)
- Pending order queue length
- Price update frequency
- System uptime

**User Behavior**:
- Most traded stocks
- Buy vs sell ratio
- Market vs limit order ratio
- Average holding period
- Profit/loss distribution

---

## Demo Script

```python
from datetime import datetime

def run_all_demos():
    print("=" * 70)
    print("ONLINE STOCK BROKERAGE SYSTEM - DEMO")
    print("=" * 70)
    
    # Demo 1: Setup
    exchange = StockExchange.get_instance()
    alice = User("U001", "Alice", "alice@example.com")
    alice_account = alice.create_account(50000.00)
    
    # Add stocks
    aapl = Stock("AAPL", "Apple Inc.", 150.00)
    googl = Stock("GOOGL", "Alphabet Inc.", 2800.00)
    exchange.add_stock(aapl)
    exchange.add_stock(googl)
    
    # Demo 2: Market buy order
    print("\n[DEMO 2] Market Buy Order")
    order = OrderFactory.create_order(
        alice_account, aapl, 100, OrderType.BUY, PriceType.MARKET
    )
    exchange.place_order(order)
    print(f"✅ Bought 100 AAPL @ ${order.execution_price:.2f}")
    
    # Demo 3: Portfolio valuation
    print("\n[DEMO 3] Portfolio Valuation")
    pnl = alice_account.portfolio.get_profit_loss()
    print(f"Portfolio Value: ${pnl['current_value']:,.2f}")
    print(f"Profit/Loss: ${pnl['profit_loss']:+,.2f}")
    
    # Demo 4: Limit order
    print("\n[DEMO 4] Limit Sell Order")
    limit_order = OrderFactory.create_order(
        alice_account, aapl, 50, OrderType.SELL, 
        PriceType.LIMIT, limit_price=160.00
    )
    exchange.place_order(limit_order)
    print(f"✅ Placed limit sell @ $160.00 (currently ${aapl.current_price:.2f})")
    
    # Trigger limit order
    exchange.update_stock_price("AAPL", 165.00)
    print(f"✅ Price increased to $165.00 → Limit order executed!")
    
    # Demo 5: Summary
    print("\n[DEMO 5] Summary")
    print(f"Final Balance: ${alice_account.balance:,.2f}")
    print(f"Portfolio Value: ${alice_account.portfolio.calculate_value():,.2f}")
    print(f"Net Worth: ${alice_account.get_net_worth():,.2f}")

if __name__ == "__main__":
    run_all_demos()
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Order Execution** | Strategy pattern for Market vs Limit orders |
| **Price Updates** | Observer pattern for real-time notifications |
| **Portfolio Tracking** | Average cost basis for accurate profit/loss |
| **State Management** | Clear order lifecycle (PENDING → EXECUTED/CANCELLED) |
| **Scalability** | Microservices, Redis caching, Kafka streaming |
| **Atomicity** | Two-phase commit for fund transfer + portfolio update |

---

## Interview Tips

1. **Clarify order types early** — Market vs Limit, stop-loss optional
2. **Explain cost basis calculation** — Show average purchase price logic
3. **Demonstrate patterns** — Strategy for orders, Observer for prices
4. **Handle edge cases** — Insufficient funds, invalid quantities, concurrent orders
5. **Discuss trade-offs** — Immediate consistency vs eventual consistency
6. **Demo incrementally** — Show deposit → buy → price change → sell → P/L
7. **Mention scalability** — Microservices, sharding, caching strategies
8. **Ask follow-up questions** — "Want to add stop-loss orders?" (shows depth)
