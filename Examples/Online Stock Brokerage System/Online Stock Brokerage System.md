# Online Stock Brokerage System — 75-Minute Interview Guide

## Quick Start Overview

## 5-Minute Overview

### What is this system?
A stock trading platform where users can buy/sell stocks, manage portfolios, track real-time prices, execute market/limit orders, and monitor investment performance.

### Core Flow
```
User deposits funds → Searches stocks → Places order (Market/Limit) → 
Order executed → Portfolio updated → Track profit/loss → Withdraw gains
```

## Essential Entities (Remember these!)

| Entity | Purpose | Key Method |
|--------|---------|------------|
| **Stock** | Represents a tradable security | `get_quote()`, `update_price()` |
| **Account** | User's trading account | `deposit()`, `get_balance()`, `get_net_worth()` |
| **Order** | Buy/sell request | `execute()`, `cancel()` |
| **Portfolio** | Holdings tracker | `calculate_value()`, `get_profit_loss()` |
| **Transaction** | Trade record | `record()`, `get_details()` |
| **MarketData** | Real-time prices | `update()`, `get_current_quote()` |

## Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````

Design Patterns (Memorize these!)

### 1. **Singleton** - StockExchange
```python
class StockExchange:
    _instance = None
    
    @staticmethod
    def get_instance():
        if StockExchange._instance is None:
            StockExchange._instance = StockExchange()
        return StockExchange._instance
```
**Why**: Single source of truth for all market operations

### 2. **Strategy** - Order Execution
```python
class MarketOrderStrategy(OrderStrategy):
    def execute(self, order):
        # Execute at current market price immediately
        return order.stock.current_price

class LimitOrderStrategy(OrderStrategy):
    def execute(self, order):
        # Execute only if price condition met
        if order.order_type == OrderType.BUY:
            return order.limit_price if current_price <= order.limit_price else None
```
**Why**: Different order types have different execution rules

### 3. **Observer** - Price Updates
```python
class PortfolioObserver(PriceObserver):
    def update(self, stock, new_price):
        # Recalculate portfolio value when price changes
        self.portfolio.recalculate_value()
```
**Why**: Multiple components (portfolios, watchlists, alerts) need price updates

### 4. **State** - Order Lifecycle
```python
class OrderState(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
```
**Why**: Clear order status transitions

### 5. **Factory** - Order Creation
```python
class OrderFactory:
    @staticmethod
    def create_order(order_type, **kwargs):
        if order_type == "MARKET":
            return MarketOrder(**kwargs)
        elif order_type == "LIMIT":
            return LimitOrder(**kwargs)
```
**Why**: Centralized order creation with type-specific logic

### 6. **Command** - Trading Operations
```python
class BuyCommand(Command):
    def execute(self):
        self.exchange.execute_buy(self.order)
    
    def undo(self):
        self.exchange.cancel_order(self.order)
```
**Why**: Encapsulate operations for undo/audit trail

## 75-Minute Interview Timeline

| Time | Task | What to Say |
|------|------|-------------|
| **0-10 min** | Requirements | "Let me clarify: we need buy/sell, portfolios, market/limit orders, real-time prices" |
| **10-30 min** | Core Entities | "I'll implement Stock, Account, Order, Portfolio, Transaction" |
| **30-50 min** | Patterns | "Using Singleton for exchange, Strategy for orders, Observer for prices" |
| **50-70 min** | Integration | "Let me wire up the StockExchange controller and order matching" |
| **70-75 min** | Demo | "Here's a working demo: deposit → buy stock → check portfolio → sell" |

## Quick Code Template

```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import threading

# 1. Enums
class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

class PriceType(Enum):
    MARKET = "market"
    LIMIT = "limit"

# 2. Core Entities
class Stock:
    def __init__(self, symbol, name, current_price):
        self.symbol = symbol
        self.name = name
        self.current_price = current_price

class Account:
    def __init__(self, account_id, user, initial_balance):
        self.account_id = account_id
        self.balance = initial_balance
        self.portfolio = Portfolio()

# 3. Strategy Pattern
class OrderStrategy(ABC):
    @abstractmethod
    def execute(self, order): pass

# 4. Observer Pattern
class PriceObserver(ABC):
    @abstractmethod
    def update(self, stock, new_price): pass

# 5. Singleton Controller
class StockExchange:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.stocks = {}
        self.orders = []
        self.observers = []
```

## Key Talking Points

### When asked about order matching:
> "Market orders execute immediately at current price. Limit orders wait in order book until price condition is met. I use Strategy pattern to handle different execution logic."

### When asked about portfolio tracking:
> "Portfolio maintains holdings (stock → quantity mapping) and cost basis. When price updates, Observer pattern notifies portfolio to recalculate value. Profit/loss = current_value - cost_basis."

### When asked about scalability:
> "Microservices architecture: Order service, Portfolio service, Market data service. Redis for real-time price caching. Kafka for event streaming. Database sharding by user_id."

### When asked about data consistency:
> "Use database transactions for atomic operations. Two-phase commit for fund transfer + order execution. Idempotent operations prevent duplicate orders. Transaction logs for audit trail."

## Demo Scenarios (Run these!)

```bash
python3 INTERVIEW_COMPACT.py
```

**Demo 1**: Setup - Create account, deposit funds
**Demo 2**: Market Order - Buy stock at current price
**Demo 3**: Portfolio Valuation - Calculate profit/loss
**Demo 4**: Limit Order - Conditional sell order
**Demo 5**: Full Flow - Complete trading cycle with price updates

## Common Interview Questions

**Q1: How do you handle concurrent orders?**
A: Thread-safe order book with locks, queue-based processing, database transactions

**Q2: How to calculate profit/loss?**
A: Track cost basis (average purchase price). Profit = (current_price - cost_basis) × quantity

**Q3: How to prevent race conditions?**
A: Locks for critical sections, optimistic locking, event sourcing for audit

**Q4: How to scale to millions of users?**
A: Microservices, Redis caching, Kafka streaming, database sharding

**Q5: How to ensure order execution fairness?**
A: FIFO order book, price-time priority, atomic matching algorithm

## Success Checklist

- [ ] Explain 8 core entities clearly
- [ ] Implement 3+ design patterns
- [ ] Show working buy/sell demo
- [ ] Calculate portfolio profit/loss correctly
- [ ] Handle market and limit orders
- [ ] Explain order matching logic
- [ ] Discuss scalability approach
- [ ] Run 3+ demo scenarios successfully

## If You Get Stuck

- **< 20 min**: Skip complex patterns, focus on Stock/Account/Order entities
- **20-50 min**: Implement basic buy/sell, defer limit orders and observers
- **> 50 min**: Show 1-2 working demos, explain rest verbally

## Key Formulas

**Portfolio Value**: `Σ(quantity × current_price)` for all holdings

**Profit/Loss**: `(current_price - cost_basis) × quantity`

**Cost Basis** (after multiple purchases): `Σ(purchase_price × quantity) / total_quantity`

**Net Worth**: `balance + portfolio_value`

**Transaction Amount**: `quantity × execution_price + fees`

---

**Remember**: Trading systems are about **order flow** and **state management**. Focus on clear order lifecycle and accurate portfolio tracking. Show working code, not just theory!


## 75-Minute Guide

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


## Detailed Design Reference

## Overview
A comprehensive stock trading platform that enables users to buy and sell stocks, manage portfolios, track real-time market data, execute orders, and monitor investment performance. The system handles order matching, portfolio valuation, transaction history, and fund management.

## Core Entities

### 1. **Stock**
- Attributes: `symbol`, `name`, `current_price`, `market_cap`, `sector`
- Methods: `update_price()`, `get_quote()`, `get_historical_data()`

### 2. **Account**
- Attributes: `account_id`, `user`, `balance`, `portfolio`, `transaction_history`
- Methods: `deposit()`, `withdraw()`, `get_balance()`, `get_net_worth()`

### 3. **Order**
- Attributes: `order_id`, `account`, `stock`, `quantity`, `order_type` (BUY/SELL), `price_type` (MARKET/LIMIT), `limit_price`, `status`, `timestamp`
- Methods: `execute()`, `cancel()`, `update_status()`

### 4. **Portfolio**
- Attributes: `holdings` (stock → quantity mapping), `total_value`, `cost_basis`
- Methods: `add_holding()`, `remove_holding()`, `calculate_value()`, `get_profit_loss()`

### 5. **Transaction**
- Attributes: `transaction_id`, `order`, `execution_price`, `quantity`, `total_amount`, `fees`, `timestamp`
- Methods: `record()`, `get_details()`

### 6. **MarketData**
- Attributes: `stock`, `timestamp`, `price`, `volume`, `bid`, `ask`
- Methods: `update()`, `get_current_quote()`, `get_spread()`

### 7. **User**
- Attributes: `user_id`, `name`, `email`, `accounts`
- Methods: `create_account()`, `get_accounts()`, `verify_identity()`

### 8. **Watchlist**
- Attributes: `watchlist_id`, `user`, `stocks`
- Methods: `add_stock()`, `remove_stock()`, `get_quotes()`

## Design Patterns

### 1. **Singleton Pattern**
- **Where**: `StockExchange` class
- **Why**: Ensure single instance of the exchange system that manages all orders and market data
- **Implementation**: Thread-safe singleton with `_instance` and `_lock`

### 2. **Strategy Pattern** (Order Execution)
- **Where**: Order execution strategies
- **Why**: Different order types (Market, Limit, Stop-Loss) have different execution logic
- **Strategies**:
  - `MarketOrderStrategy`: Execute immediately at current market price
  - `LimitOrderStrategy`: Execute only if price reaches limit
  - `StopLossOrderStrategy`: Trigger sell when price falls below threshold

### 3. **Observer Pattern** (Price Updates)
- **Where**: Market data notifications
- **Why**: Multiple components (portfolios, watchlists, price alerts) need real-time price updates
- **Implementation**:
  - `PriceObserver` interface
  - Concrete observers: `PortfolioObserver`, `WatchlistObserver`, `AlertObserver`

### 4. **State Pattern**
- **Where**: Order lifecycle
- **Why**: Orders transition through states: PENDING → EXECUTED/CANCELLED/REJECTED
- **States**: `PendingState`, `ExecutedState`, `CancelledState`, `RejectedState`

### 5. **Factory Pattern**
- **Where**: Order creation
- **Why**: Create different order types (Market, Limit, Stop-Loss) based on user input
- **Implementation**: `OrderFactory.create_order(type, params)`

### 6. **Command Pattern**
- **Where**: Trading operations (Buy, Sell, Cancel)
- **Why**: Encapsulate trading actions as objects for undo/history tracking
- **Commands**: `BuyCommand`, `SellCommand`, `CancelOrderCommand`

## Key Requirements Checklist

### Functional Requirements
- [x] User can create account and deposit funds
- [x] User can search stocks and view real-time quotes
- [x] User can place market and limit orders
- [x] System executes orders based on price conditions
- [x] Portfolio tracks holdings and calculates profit/loss
- [x] Transaction history maintained for all trades
- [x] Watchlist for tracking favorite stocks
- [x] Real-time price updates

### Non-Functional Requirements
- [x] **Scalability**: Handle 10,000+ concurrent users
- [x] **Performance**: Order execution < 100ms
- [x] **Reliability**: 99.9% uptime for trading hours
- [x] **Security**: Secure fund transfers and data encryption
- [x] **Consistency**: Atomic transactions, no partial executions

## Architecture Highlights

### Order Matching
```
User places order → OrderFactory creates order → 
Strategy determines execution logic → 
Exchange matches with counter orders → 
Transaction recorded → Portfolio updated → 
Observers notified
```

### Price Update Flow
```
MarketData updates stock price → 
Notify all observers (portfolios, watchlists, alerts) → 
Recalculate portfolio values → 
Check limit orders for execution
```

### Portfolio Valuation
```
Portfolio.calculate_value():
  For each holding (stock, quantity):
    current_value += quantity * stock.current_price
  return current_value
```

## SOLID Principles Applied

- **Single Responsibility**: `Order` handles order logic, `Portfolio` handles holdings, `Transaction` records trades
- **Open/Closed**: New order strategies can be added without modifying existing code
- **Liskov Substitution**: All order strategies implement `OrderStrategy` interface
- **Interface Segregation**: Separate interfaces for `PriceObserver`, `OrderStrategy`, `OrderState`
- **Dependency Inversion**: `StockExchange` depends on `OrderStrategy` abstraction, not concrete implementations

## Example Usage Flow

```python
# 1. Setup
exchange = StockExchange.get_instance()
user = User("U001", "Alice", "alice@example.com")
account = user.create_account(10000)  # $10,000 initial deposit

# 2. Search stock
apple = exchange.get_stock("AAPL")
quote = apple.get_quote()  # $150.00

# 3. Place market buy order
order = OrderFactory.create_order(
    order_type="MARKET",
    price_type="BUY",
    account=account,
    stock=apple,
    quantity=10
)
exchange.place_order(order)  # Executes immediately

# 4. Check portfolio
portfolio_value = account.portfolio.calculate_value()
profit_loss = account.portfolio.get_profit_loss()

# 5. Place limit sell order
sell_order = OrderFactory.create_order(
    order_type="LIMIT",
    price_type="SELL",
    account=account,
    stock=apple,
    quantity=5,
    limit_price=160.00  # Sell when price reaches $160
)
exchange.place_order(sell_order)  # Pending until price condition met
```

## Interview Discussion Points

1. **How do you handle concurrent order placement?**
   - Use locks/semaphores for order book access
   - Queue-based architecture for order processing
   - Database transactions with ACID guarantees

2. **How do you calculate profit/loss?**
   - Track cost basis (average purchase price per stock)
   - Current value = quantity × current_price
   - Profit/Loss = current_value - cost_basis

3. **How do you prevent race conditions in order matching?**
   - Thread-safe order book with locks
   - Optimistic locking with version numbers
   - Event sourcing for audit trail

4. **How to scale for millions of users?**
   - Microservices: Order service, Portfolio service, Market data service
   - Redis for real-time price caching
   - Kafka for event streaming (price updates, order events)
   - Database sharding by user_id

5. **How to ensure data consistency?**
   - Two-phase commit for fund transfer + order execution
   - Idempotent operations (duplicate order prevention)
   - Transaction logs for recovery

## Files in This Directory

- **README.md**: This overview document with entities, patterns, and architecture
- **START_HERE.md**: Quick reference guide for 75-minute interview preparation
- **INTERVIEW_COMPACT.py**: Complete working implementation (~700 lines) with 5 demo scenarios
- **75_MINUTE_GUIDE.md**: Detailed implementation guide with timeline, code examples, and Q&A

---

**Next Steps**: 
1. Read `START_HERE.md` for a 5-minute quick reference
2. Study `75_MINUTE_GUIDE.md` for step-by-step implementation
3. Run `python3 INTERVIEW_COMPACT.py` to see working demos


## Compact Code

```python
"""
Online Stock Brokerage System - Complete Interview Implementation
=====================================================================
Design Patterns: Singleton | Strategy | Observer | State | Factory | Command
Time Complexity: O(1) order execution, O(n) portfolio valuation
Space Complexity: O(u + s + o) where u=users, s=stocks, o=orders
=====================================================================
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import threading
import random


# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

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


# ============================================================================
# SECTION 2: CORE ENTITIES
# ============================================================================

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
    
    def __str__(self):
        return f"{self.symbol} ({self.name}) - ${self.current_price:.2f}"


class Portfolio:
    """Manages user's stock holdings"""
    def __init__(self):
        # holdings: {stock_symbol: {'quantity': int, 'cost_basis': float}}
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
    
    def get_holdings_summary(self) -> List[Dict]:
        """Get summary of all holdings"""
        summary = []
        for symbol, holding in self.holdings.items():
            stock = holding['stock']
            quantity = holding['quantity']
            cost_basis = holding['cost_basis']
            current_price = stock.current_price
            
            summary.append({
                'symbol': symbol,
                'quantity': quantity,
                'cost_basis': cost_basis,
                'current_price': current_price,
                'total_cost': quantity * cost_basis,
                'current_value': quantity * current_price,
                'profit_loss': quantity * (current_price - cost_basis)
            })
        
        return summary


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
    
    def get_transaction_history(self, limit: int = 10) -> List['Transaction']:
        """Get recent transactions"""
        return self.transaction_history[-limit:]


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
    
    def __str__(self):
        return (f"Order {self.order_id}: {self.order_type.value.upper()} {self.quantity} "
                f"{self.stock.symbol} @ {self.price_type.value.upper()} "
                f"({self.status.value})")


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
    
    def __str__(self):
        return (f"Transaction {self.transaction_id}: {self.transaction_type.value.upper()} "
                f"{self.quantity} {self.order.stock.symbol} @ ${self.execution_price:.2f}")


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
    
    def get_accounts(self) -> List[Account]:
        """Get all user accounts"""
        return self.accounts


class MarketData:
    """Real-time market data for a stock"""
    def __init__(self, stock: Stock):
        self.stock = stock
        self.timestamp = datetime.now()
        self.bid = stock.current_price - 0.01  # Simulate bid-ask spread
        self.ask = stock.current_price + 0.01
        self.volume = 0
    
    def update(self, new_price: float, volume: int = 0):
        """Update market data"""
        self.stock.update_price(new_price)
        self.timestamp = datetime.now()
        self.bid = new_price - 0.01
        self.ask = new_price + 0.01
        self.volume += volume
    
    def get_current_quote(self) -> Dict:
        """Get current quote with bid/ask"""
        return {
            'symbol': self.stock.symbol,
            'price': self.stock.current_price,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.ask - self.bid,
            'timestamp': self.timestamp
        }


# ============================================================================
# SECTION 3: STRATEGY PATTERN (Order Execution Strategies)
# ============================================================================

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


# ============================================================================
# SECTION 4: OBSERVER PATTERN (Price Update Notifications)
# ============================================================================

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


# ============================================================================
# SECTION 5: FACTORY PATTERN (Order Creation)
# ============================================================================

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


# ============================================================================
# SECTION 6: COMMAND PATTERN (Trading Operations)
# ============================================================================

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


# ============================================================================
# SECTION 7: SINGLETON PATTERN (Stock Exchange System)
# ============================================================================

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
    
    def get_stock(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol"""
        return self.stocks.get(symbol)
    
    def add_observer(self, observer: PriceObserver):
        """Add observer for all stocks"""
        self.observers.append(observer)
        
        # Subscribe to all existing stocks
        for stock in self.stocks.values():
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
        
        # Remove from pending if it was there
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        
        return True
    
    def execute_sell_order(self, order: Order) -> bool:
        """Execute a sell order"""
        strategy = self.strategies[order.price_type]
        execution_price = strategy.get_execution_price(order)
        
        if execution_price is None:
            order.reject()
            return False
        
        # Check sufficient shares
        symbol = order.stock.symbol
        if symbol not in order.account.portfolio.holdings:
            order.reject()
            return False
        
        holding = order.account.portfolio.holdings[symbol]
        if holding['quantity'] < order.quantity:
            order.reject()
            return False
        
        # Remove from portfolio
        order.account.portfolio.remove_holding(symbol, order.quantity)
        
        # Add funds
        total_proceeds = order.quantity * execution_price
        order.account.balance += total_proceeds
        
        # Mark order as executed
        order.execute(execution_price)
        
        # Create transaction record
        self.transaction_counter += 1
        transaction = Transaction(
            transaction_id=f"TXN{self.transaction_counter:05d}",
            order=order,
            execution_price=execution_price,
            quantity=order.quantity,
            transaction_type=TransactionType.SELL
        )
        order.account.add_transaction(transaction)
        
        # Remove from pending if it was there
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        
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
    
    def update_stock_price(self, symbol: str, new_price: float):
        """Update stock price (triggers observers and limit order checks)"""
        stock = self.stocks.get(symbol)
        if stock:
            market_data = self.market_data[symbol]
            market_data.update(new_price)


# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def demo_1_setup_and_deposit():
    """Demo 1: Setup users, accounts, and deposit funds"""
    print("\n" + "=" * 70)
    print("DEMO 1: Setup & Account Creation")
    print("=" * 70)
    
    exchange = StockExchange.get_instance()
    
    # Add stocks to exchange
    aapl = Stock("AAPL", "Apple Inc.", 150.00, "Technology")
    googl = Stock("GOOGL", "Alphabet Inc.", 2800.00, "Technology")
    tsla = Stock("TSLA", "Tesla Inc.", 700.00, "Automotive")
    
    exchange.add_stock(aapl)
    exchange.add_stock(googl)
    exchange.add_stock(tsla)
    
    print(f"✅ Added {len(exchange.stocks)} stocks to exchange")
    
    # Create users and accounts
    alice = User("U001", "Alice Johnson", "alice@example.com")
    alice_account = alice.create_account(50000.00)  # $50,000 initial deposit
    
    bob = User("U002", "Bob Smith", "bob@example.com")
    bob_account = bob.create_account(30000.00)  # $30,000 initial deposit
    
    print(f"✅ Created 2 users with accounts")
    print(f"   Alice: {alice_account.account_id} - ${alice_account.balance:,.2f}")
    print(f"   Bob: {bob_account.account_id} - ${bob_account.balance:,.2f}")
    
    return alice_account, bob_account, aapl, googl, tsla


def demo_2_market_orders():
    """Demo 2: Place and execute market orders"""
    print("\n" + "=" * 70)
    print("DEMO 2: Market Orders (Buy/Sell)")
    print("=" * 70)
    
    exchange = StockExchange.get_instance()
    alice_account, bob_account, aapl, googl, tsla = demo_1_setup_and_deposit()
    
    # Alice buys 100 shares of AAPL at market price
    print("\n→ Alice buying 100 AAPL shares at market price...")
    buy_order = OrderFactory.create_order(
        account=alice_account,
        stock=aapl,
        quantity=100,
        order_type=OrderType.BUY,
        price_type=PriceType.MARKET
    )
    
    success = exchange.place_order(buy_order)
    if success:
        print(f"✅ {buy_order}")
        print(f"   Execution Price: ${buy_order.execution_price:.2f}")
        print(f"   Total Cost: ${buy_order.quantity * buy_order.execution_price:,.2f}")
        print(f"   Remaining Balance: ${alice_account.balance:,.2f}")
    
    # Bob buys 10 shares of GOOGL
    print("\n→ Bob buying 10 GOOGL shares at market price...")
    buy_order2 = OrderFactory.create_order(
        account=bob_account,
        stock=googl,
        quantity=10,
        order_type=OrderType.BUY,
        price_type=PriceType.MARKET
    )
    
    success = exchange.place_order(buy_order2)
    if success:
        print(f"✅ {buy_order2}")
        print(f"   Execution Price: ${buy_order2.execution_price:.2f}")
        print(f"   Total Cost: ${buy_order2.quantity * buy_order2.execution_price:,.2f}")
        print(f"   Remaining Balance: ${bob_account.balance:,.2f}")


def demo_3_portfolio_valuation():
    """Demo 3: Portfolio tracking and profit/loss calculation"""
    print("\n" + "=" * 70)
    print("DEMO 3: Portfolio Valuation & Profit/Loss")
    print("=" * 70)
    
    exchange = StockExchange.get_instance()
    alice_account, bob_account, aapl, googl, tsla = demo_1_setup_and_deposit()
    
    # Alice builds portfolio
    exchange.place_order(OrderFactory.create_order(
        alice_account, aapl, 100, OrderType.BUY, PriceType.MARKET
    ))
    exchange.place_order(OrderFactory.create_order(
        alice_account, tsla, 20, OrderType.BUY, PriceType.MARKET
    ))
    
    print("\n→ Alice's Portfolio:")
    print("-" * 70)
    holdings = alice_account.portfolio.get_holdings_summary()
    for holding in holdings:
        print(f"   {holding['symbol']}: {holding['quantity']} shares @ "
              f"${holding['cost_basis']:.2f} (Current: ${holding['current_price']:.2f})")
        print(f"      P/L: ${holding['profit_loss']:+,.2f}")
    
    pnl = alice_account.portfolio.get_profit_loss()
    print(f"\n   Total Investment: ${pnl['total_cost']:,.2f}")
    print(f"   Current Value: ${pnl['current_value']:,.2f}")
    print(f"   Profit/Loss: ${pnl['profit_loss']:+,.2f} ({pnl['percentage']:+.2f}%)")
    print(f"   Net Worth: ${alice_account.get_net_worth():,.2f}")
    
    # Simulate price increase
    print("\n→ Simulating price changes...")
    exchange.update_stock_price("AAPL", 165.00)  # +10%
    exchange.update_stock_price("TSLA", 770.00)  # +10%
    
    pnl_after = alice_account.portfolio.get_profit_loss()
    print(f"\n   Updated Portfolio Value: ${pnl_after['current_value']:,.2f}")
    print(f"   New Profit/Loss: ${pnl_after['profit_loss']:+,.2f} ({pnl_after['percentage']:+.2f}%)")
    print(f"   Updated Net Worth: ${alice_account.get_net_worth():,.2f}")


def demo_4_limit_orders():
    """Demo 4: Limit orders with conditional execution"""
    print("\n" + "=" * 70)
    print("DEMO 4: Limit Orders (Conditional Execution)")
    print("=" * 70)
    
    exchange = StockExchange.get_instance()
    # Add console observer
    exchange.add_observer(ConsoleObserver())
    
    alice_account, bob_account, aapl, googl, tsla = demo_1_setup_and_deposit()
    
    # Alice buys TSLA at market
    exchange.place_order(OrderFactory.create_order(
        alice_account, tsla, 50, OrderType.BUY, PriceType.MARKET
    ))
    
    print(f"\n→ Alice owns 50 TSLA shares @ ${tsla.current_price:.2f}")
    print(f"   Current Balance: ${alice_account.balance:,.2f}")
    
    # Alice places limit sell order (sell when price reaches $750)
    print(f"\n→ Alice placing LIMIT SELL order: 50 TSLA @ $750.00...")
    limit_sell = OrderFactory.create_order(
        account=alice_account,
        stock=tsla,
        quantity=50,
        order_type=OrderType.SELL,
        price_type=PriceType.LIMIT,
        limit_price=750.00
    )
    
    exchange.place_order(limit_sell)
    print(f"✅ {limit_sell}")
    print(f"   Order is PENDING until TSLA reaches $750.00")
    
    # Simulate price movement
    print(f"\n→ Simulating price movements...")
    exchange.update_stock_price("TSLA", 720.00)  # Still below limit
    print(f"   Order status: {limit_sell.status.value} (price not reached)")
    
    exchange.update_stock_price("TSLA", 755.00)  # Above limit - triggers execution
    print(f"   Order status: {limit_sell.status.value}")
    
    if limit_sell.status == OrderStatus.EXECUTED:
        print(f"✅ Limit order EXECUTED at ${limit_sell.execution_price:.2f}")
        print(f"   Alice's new balance: ${alice_account.balance:,.2f}")


def demo_5_full_trading_cycle():
    """Demo 5: Complete trading cycle with price updates and transactions"""
    print("\n" + "=" * 70)
    print("DEMO 5: Full Trading Cycle with Price Updates")
    print("=" * 70)
    
    exchange = StockExchange.get_instance()
    alice_account, bob_account, aapl, googl, tsla = demo_1_setup_and_deposit()
    
    print(f"\n→ Starting Balance: ${alice_account.balance:,.2f}")
    
    # Step 1: Buy stocks
    print("\n[Step 1] Alice buying stocks...")
    exchange.place_order(OrderFactory.create_order(
        alice_account, aapl, 50, OrderType.BUY, PriceType.MARKET
    ))
    exchange.place_order(OrderFactory.create_order(
        alice_account, googl, 5, OrderType.BUY, PriceType.MARKET
    ))
    
    portfolio_value = alice_account.portfolio.calculate_value()
    print(f"✅ Portfolio Value: ${portfolio_value:,.2f}")
    print(f"   Remaining Cash: ${alice_account.balance:,.2f}")
    print(f"   Net Worth: ${alice_account.get_net_worth():,.2f}")
    
    # Step 2: Price changes
    print("\n[Step 2] Market price changes...")
    exchange.update_stock_price("AAPL", 160.00)  # +6.67%
    exchange.update_stock_price("GOOGL", 2900.00)  # +3.57%
    
    pnl = alice_account.portfolio.get_profit_loss()
    print(f"✅ Updated Portfolio Value: ${pnl['current_value']:,.2f}")
    print(f"   Profit/Loss: ${pnl['profit_loss']:+,.2f} ({pnl['percentage']:+.2f}%)")
    
    # Step 3: Sell some holdings
    print("\n[Step 3] Alice selling 25 AAPL shares...")
    exchange.place_order(OrderFactory.create_order(
        alice_account, aapl, 25, OrderType.SELL, PriceType.MARKET
    ))
    
    print(f"✅ Sale completed at ${aapl.current_price:.2f}/share")
    print(f"   Updated Cash Balance: ${alice_account.balance:,.2f}")
    print(f"   Updated Net Worth: ${alice_account.get_net_worth():,.2f}")
    
    # Step 4: Transaction history
    print("\n[Step 4] Transaction History:")
    print("-" * 70)
    for txn in alice_account.get_transaction_history():
        details = txn.get_details()
        print(f"   {details['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | "
              f"{details['type'].upper():6s} | {details['quantity']:3d} {details['stock']:5s} | "
              f"${details['price']:8.2f} | Total: ${details['total']:10,.2f}")
    
    print(f"\n[SUMMARY]")
    print("-" * 70)
    final_pnl = alice_account.portfolio.get_profit_loss()
    print(f"Final Portfolio Value: ${final_pnl['current_value']:,.2f}")
    print(f"Cash Balance: ${alice_account.balance:,.2f}")
    print(f"Net Worth: ${alice_account.get_net_worth():,.2f}")
    print(f"Total Profit/Loss: ${final_pnl['profit_loss']:+,.2f} ({final_pnl['percentage']:+.2f}%)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ONLINE STOCK BROKERAGE SYSTEM - 75 MINUTE INTERVIEW GUIDE")
    print("Design Patterns: Singleton | Strategy | Observer | State | Factory | Command")
    print("=" * 70)
    
    demo_1_setup_and_deposit()
    demo_2_market_orders()
    demo_3_portfolio_valuation()
    demo_4_limit_orders()
    demo_5_full_trading_cycle()
    
    print("\n" + "=" * 70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Singleton: Single StockExchange instance for consistency")
    print("  • Strategy: Market vs Limit order execution strategies")
    print("  • Observer: Real-time price update notifications")
    print("  • State: Clear order lifecycle (PENDING → EXECUTED/CANCELLED)")
    print("  • Factory: Centralized order creation with auto-generated IDs")
    print("  • Command: Encapsulated buy/sell operations")
    print("\nFor detailed implementation, see 75_MINUTE_GUIDE.md")

```

## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
