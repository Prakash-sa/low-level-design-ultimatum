# 📈 Online Stock Brokerage System - Quick Start Guide

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

## Design Patterns (Memorize these!)

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
