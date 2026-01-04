# Online Stock Brokerage System — 75-Minute Interview Guide

## Quick Start

### 5-Minute Overview
A stock trading platform where users can deposit funds, search stocks, place market/limit orders, manage portfolios, and track profit/loss in real-time. Core flow: **Deposit → Search → Order (Market/Limit) → Execute → Portfolio Updated → Track P/L**.

### Key Entities (Memorize!)
| Entity | Purpose | Critical Method |
|--------|---------|-----------------|
| **Stock** | Tradable security (AAPL, GOOGL, etc) | `get_quote()`, `update_price()` |
| **Account** | User's trading account | `deposit()`, `get_balance()`, `get_net_worth()` |
| **Order** | Buy/sell request | `execute()`, `cancel()` |
| **Portfolio** | Holdings tracker (stock → quantity) | `calculate_value()`, `get_profit_loss()` |
| **Transaction** | Executed trade record | `record()`, `get_details()` |
| **User** | Customer account | `create_account()`, `get_orders()` |

### 5 Design Patterns
1. **Singleton**: `StockExchange` ensures single instance, thread-safe
2. **Strategy**: `MarketOrderStrategy` vs `LimitOrderStrategy` for execution logic
3. **Observer**: Price updates notify portfolios, watchlists, alerts
4. **State**: `OrderStatus` enum (PENDING → EXECUTED/CANCELLED/REJECTED)
5. **Factory**: `OrderFactory.create_order()` for order creation
6. **Command**: `BuyCommand`, `SellCommand` for undo/audit trail

### Critical Interview Points
✅ How prevent double-booking? → Atomic fund transfer + order execution  
✅ Market vs Limit orders? → Market: immediate @ current price, Limit: conditional  
✅ Thread-safety? → Singleton + threading.Lock on critical sections  
✅ Concurrency? → 10K concurrent users, 1M orders/day, distributed locks (Redis)  
✅ Scaling? → Microservices (Order, Portfolio, Market Data), sharding by user_id  

---

## System Overview

### Problem Statement
Users want to trade stocks online: buy/sell securities, manage investment portfolios, and track real-time profit/loss. System must prevent double-spending, execute orders atomically, and provide accurate portfolio valuation in real-time.

### Core Workflow
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

### Key Constraints
- **Concurrency**: 10,000+ simultaneous users trading
- **Atomicity**: Fund transfer + order execution must be all-or-nothing
- **Accuracy**: Cost basis calculation for multi-purchase average
- **Scalability**: 1M+ orders/day across multiple regions
- **Real-time**: Price updates within 100ms, P/L recalculation within 500ms

---

## Requirements & Scope

### Functional Requirements
✅ User account management (deposit/withdraw funds)  
✅ Real-time stock quotes and market data  
✅ Place market orders (execute immediately at current price)  
✅ Place limit orders (execute when price condition met)  
✅ Portfolio management (holdings, cost basis, P/L tracking)  
✅ Order history and transaction records  
✅ Cancel pending orders (before execution)  
✅ Watchlist for tracking favorite stocks  
✅ Notifications (email/SMS/push)  

### Non-Functional Requirements
✅ Support 10,000+ concurrent users  
✅ <100ms search latency  
✅ <500ms order execution latency  
✅ <1000ms portfolio valuation  
✅ 99.9% uptime during trading hours  
✅ Atomic transactions (no partial execution)  
✅ Accurate profit/loss calculation  

### Out of Scope
❌ Payment processing (assume external gateway)  
❌ Options, futures, derivatives  
❌ Margin trading and short selling  
❌ After-hours trading  
❌ Tax reporting (1099 forms)  
❌ Regulatory compliance (SEC, FINRA)  
❌ Advanced order types (stop-loss, trailing stop, bracket orders)  

### Scope Agreement
✅ Basic market and limit orders  
✅ Long positions only (buying)  
✅ Single currency (USD)  
✅ US stock market  
✅ Trading hours: 9:30 AM - 4:00 PM EST  

---

## Architecture & Design Patterns

### 1. Singleton Pattern (Thread-Safe)

**Problem**: 10K+ users accessing trading system → race conditions on order matching, fund deduction

**Solution**: Single `StockExchange` instance with thread-safe locks

```python
class StockExchange:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
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

**Why**: Single source of truth for all market operations, prevents conflicting order executions

**Interview Tip**: "Double-check locking ensures thread-safety even with high concurrency"

---

### 2. Strategy Pattern (Order Execution)

**Problem**: Different order types (Market, Limit, Stop-Loss) have different execution logic

**Solution**: Pluggable order execution strategies

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

**Why**: Different order types extensible without modifying core execution logic

**Interview Tip**: "Easy to add StopLossOrderStrategy without changing existing code"

---

### 3. Observer Pattern (Price Updates)

**Problem**: Multiple components (portfolios, watchlists, price alerts) need real-time price updates

**Solution**: Abstract Observer interface with pluggable implementations

```python
class PriceObserver(ABC):
    @abstractmethod
    def update(self, stock: 'Stock', old_price: float, new_price: float):
        pass

class PortfolioObserver(PriceObserver):
    """Recalculate portfolio value on price change"""
    def __init__(self, portfolio: 'Portfolio'):
        self.portfolio = portfolio
    
    def update(self, stock: Stock, old_price: float, new_price: float):
        # Portfolio automatically reflects new price
        # Profit/loss recalculated

class LimitOrderObserver(PriceObserver):
    """Check if pending limit orders can execute"""
    def __init__(self, exchange: 'StockExchange'):
        self.exchange = exchange
    
    def update(self, stock: Stock, old_price: float, new_price: float):
        self.exchange.check_and_execute_limit_orders(stock)

class AlertObserver(PriceObserver):
    """Send price alerts to users"""
    def update(self, stock: Stock, old_price: float, new_price: float):
        if new_price >= 150:  # User alert threshold
            # Send notification
            pass
```

**Why**: Decouples price updates from dependent components, easy to add new observers

**Interview Tip**: "Add SlackNotifier without modifying Stock or StockExchange classes"

---

### 4. State Pattern (Order Lifecycle)

**Problem**: Orders have valid transitions (PENDING → EXECUTED) and invalid ones (EXECUTED → PENDING)

**Solution**: Enum-based state management with validation

```python
class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Order:
    def __init__(self, order_id, account, stock, quantity, order_type, price_type, limit_price=None):
        self.order_id = order_id
        self.account = account
        self.stock = stock
        self.quantity = quantity
        self.order_type = order_type  # BUY or SELL
        self.price_type = price_type  # MARKET or LIMIT
        self.limit_price = limit_price
        self.status = OrderStatus.PENDING
        self.execution_price = None
        self.timestamp = datetime.now()
    
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

**Why**: Prevents invalid state transitions at compile-time

---

### 5. Factory Pattern (Order Creation)

**Problem**: Creating different order types scattered throughout code → hard to maintain

**Solution**: Centralized factory for order creation

```python
class OrderFactory:
    _order_counter = 0
    
    @staticmethod
    def create_order(account: 'Account', stock: 'Stock', quantity: int,
                    order_type: OrderType, price_type: PriceType,
                    limit_price: Optional[float] = None) -> 'Order':
        OrderFactory._order_counter += 1
        order_id = f"ORD_{OrderFactory._order_counter}_{int(time.time())}"
        
        # Validation
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price_type == PriceType.LIMIT and limit_price is None:
            raise ValueError("Limit price required for limit orders")
        
        order = Order(order_id, account, stock, quantity, order_type, price_type, limit_price)
        return order
```

**Why**: Centralized validation and ID generation

---

### 6. Command Pattern (Trading Operations)

**Problem**: Buy/Sell/Cancel operations need undo/history/audit trail

**Solution**: Command objects for all trading operations

```python
class Command(ABC):
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

**Why**: Encapsulates operations as objects for queuing, logging, undo

---

## Core Entities & UML Diagram

### Class Diagram

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

### Entity Relationships

| Entity | Relationship | Count | Purpose |
|--------|-------------|-------|---------|
| User | HAS-A Account | 1..* | Multiple accounts per user |
| Account | HAS-A Portfolio | 1 | Holdings tracker |
| Account | PLACES Order | 0..* | Order history |
| Order | REFERENCES Stock | 1 | Which security traded |
| Stock | NOTIFIES Observer | 1..* | Price update subscribers |
| Portfolio | CONTAINS Holding | 1..* | Stock + quantity |
| Transaction | RECORDS Order | 1..1 | Immutable trade log |

---

## Interview Q&A

### Q1: How do you calculate profit/loss for a portfolio?

**Answer**: Track **cost basis** (average purchase price) for each holding.

- **Cost Basis**: `Σ(purchase_price × quantity) / total_quantity` (for multiple purchases)
- **Current Value**: `quantity × current_price`
- **Profit/Loss**: `current_value - (quantity × cost_basis)`
- **Percentage**: `(profit_loss / total_cost) × 100`

```python
def get_profit_loss(self) -> Dict:
    total_cost = 0.0
    total_current = 0.0
    
    for symbol, holding in self.holdings.items():
        quantity = holding['quantity']
        cost_basis = holding['cost_basis']
        current_price = self.stocks[symbol].current_price
        
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

---

### Q2: What's the difference between market and limit orders?

**Answer**:
- **Market Order**: Execute immediately at current market price. Guarantees execution but not price.
- **Limit Order**: Execute only when price condition is met. Guarantees price but not execution.

**Example**:
- Stock trading at $100
- **Market Buy**: Executes at $100 (or current ask)
- **Limit Buy @ $95**: Waits until price drops to $95 or below
- **Limit Sell @ $110**: Waits until price rises to $110 or above

---

### Q3: Why use Observer pattern for price updates?

**Answer**: Decouples price updates from dependent components. When stock price changes, multiple listeners react independently:

- Portfolio recalculates value
- Limit orders check execution conditions
- Price alerts trigger notifications
- UI updates in real-time

Without Observer, Stock class would need to know about all dependent components (tight coupling).

---

### Q4: How do you prevent race conditions in concurrent order placement?

**Answer**:
1. **Thread-safe Singleton**: Use lock for instance creation
2. **Atomic Operations**: Lock fund deduction + portfolio update
3. **Order Book Locking**: Synchronize access to pending orders
4. **Database Transactions**: ACID guarantees
5. **Optimistic Locking**: Version numbers to detect conflicts

```python
with self._lock:
    # Deduct funds
    if account.balance >= total_cost:
        account.balance -= total_cost
        # Update portfolio
        portfolio.add_holding(stock, quantity, execution_price)
    else:
        order.status = OrderStatus.REJECTED
```

---

### Q5: How would you scale this system to handle millions of users?

**Answer**: Multi-tier microservices architecture:

**Tier 1: API Gateway**
- Load balancer distributes requests
- Session affinity (user always hits same region)

**Tier 2: Microservices**
- Order Service: Place, execute, cancel orders
- Portfolio Service: Holdings, valuation, P/L
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

---

### Q6: How do you handle limit orders that trigger simultaneously?

**Answer**: Use **price-time priority**:
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

---

### Q7: How do you ensure atomicity in buy/sell operations?

**Answer**: Use **two-phase commit**:

**Phase 1 - Validation**:
1. Check sufficient funds (buy) or shares (sell)
2. Lock account balance
3. Verify order parameters

**Phase 2 - Execution** (all or nothing):
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
except Exception as e:
    # Rollback
    return False
```

---

### Q8: What if user places conflicting orders (buy + sell same stock)?

**Answer**: Allow both, but execute sequentially:

1. User holds 100 shares @ $50 cost
2. Places Limit Sell @ $100
3. Places Limit Buy @ $80 (averaging down)
4. When price hits $80: Buy executes first (FIFO)
5. When price hits $100: Sell executes
6. Portfolio now has 200 shares @ average cost $70

Order of execution critical for P/L tracking.

---

### Q9: How do you handle funds being withdrawn mid-trade?

**Answer**: Lock funds during order lifecycle:

1. User has $10,000 balance
2. Places buy order for $5,000 (status=PENDING)
3. Tries to withdraw $7,000 → Reject (only $5,000 available)
4. Order executes → funds locked
5. Now withdrawal allowed only up to remaining balance

Funds are reserved from PENDING → EXECUTED, not before.

---

### Q10: What metrics would you track?

**Answer**:

**Business Metrics**:
- Trading volume (daily, monthly)
- Number of active users
- Average order size
- Revenue from fees
- User retention

**Performance Metrics**:
- Order execution latency (p50, p95, p99)
- API response times
- Portfolio valuation time
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

## Scaling Q&A

### Q1: How would you scale to 1M concurrent users and 100M orders/day (1,157 orders/sec)?

**Answer**: Global LB, 1000+ shards, distributed locks

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

**Per-Region Throughput**:
- Region US: 600 TPS
- Region EU: 400 TPS
- Region APAC: 157 TPS
- **Total**: 1,157 TPS

---

### Q2: How to prevent overbooking in distributed settings?

**Answer**: Pessimistic locking with Redis

**Problem**: Each replica has own `threading.Lock`, but they don't know about each other.

**Solution**: Distributed lock (Redis)

```python
# Instead of threading.Lock
def execute_sell_order(self, order: Order):
    with redis_lock.acquire(f"user-{order.account.user_id}", timeout=5):
        # Check shares available
        if order.account.portfolio.get_quantity(order.stock) < order.quantity:
            order.status = OrderStatus.REJECTED
            return False
        
        # Execute atomically
        order.account.portfolio.remove_holding(order.stock, order.quantity)
        return True
```

Only 1 replica can execute per user at a time globally. Prevents overselling.

---

### Q3: How to sync portfolio valuations across replicas?

**Answer**: Multi-strategy approach

**Option 1: Pessimistic Locking** (Consistent but slower)
```
Read from primary DB → Lock row → Check balance → Execute → Unlock
Consistent but high latency (network round-trip)
```

**Option 2: Optimistic Locking** (Fast but eventual)
```
Read portfolio version (v1)
Calculate P/L locally
Try update: if version still v1 → commit, else retry
Consistent if version matches, fast
```

**Option 3: Event Sourcing** (Audit trail)
```
All order events → Kafka topic
Order Service processes and publishes
Portfolio Service subscribes and updates async
Eventually consistent, audit trail for debugging
```

**Recommendation**: 
- **Market Orders**: Pessimistic (critical consistency)
- **Limit Orders**: Optimistic (can retry)
- **Portfolio Valuation**: Event sourcing (async ok)

---

### Q4: How to handle peak traffic (holiday trading 5000+ TPS)?

**Answer**:

**Before Peak**:
1. Auto-scale to 2000 Order Service pods
2. Pre-warm price cache
3. Increase DB connection pool
4. Increase Kafka partitions

**During Peak**:
1. **Queue checkouts**: If latency > 1000ms, queue request
2. **Async notifications**: Email/SMS in background
3. **Cache aggressively**: 1-min TTL for price quotes
4. **Load shedding**: Reject new orders if queue > 10K requests

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

**Answer**: Kafka + worker pool

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

**Benefits**:
- Parallel processing
- Batch efficiency (reduce API calls)
- Fault isolation (email down ≠ SMS down)
- Auto-retry on failure
- Monitoring per channel

---

### Q6: How to handle order search across 100M+ orders?

**Answer**: Elasticsearch + aggregation

```
Elasticsearch Cluster (100 shards)
    ├─ Shard 1: Orders 1-1M
    ├─ Shard 2: Orders 1M-2M
    ...
    └─ Shard 100: Orders 99M-100M

Query: symbol=AAPL AND status=EXECUTED AND date=[2024-01-01, 2024-01-31]
    ↓
ES searches all shards in parallel
    ↓
Returns matching documents in <100ms (vs 10s with array scan)
```

**Aggregations**:
```
Filter: symbol=AAPL
Aggregate: SUM(quantity), AVG(price), COUNT(orders)
    ↓
1-year trading summary in <500ms
```

---

### Q7: How to ensure 99.9% uptime at scale?

**Answer**: Multi-region failover

```
Active-Active Configuration:
Region 1 (US) [Primary]
    ├─ 3x Order Service replicas
    ├─ 3x Portfolio Service replicas
    ├─ PostgreSQL Primary + 2 replicas
    └─ Redis Cluster (3 nodes)

Region 2 (EU) [Hot Standby]
    ├─ 3x Order Service replicas
    ├─ 3x Portfolio Service replicas
    ├─ PostgreSQL Replica (read-only)
    └─ Redis Cluster (replicated)

Region 3 (APAC) [Cold Standby]
    └─ PostgreSQL Replica (read-only)

Health Checks (every 10s):
- Response time > 1000ms → degrade
- Error rate > 0.1% → alert
- DB unreachable → failover

Failure Handling:
1. Region US fails → Traffic → Region EU
2. RTO (Recovery Time): < 30 seconds
3. RPO (Recovery Point): < 5 minutes
4. No data loss (replicated before failover)
```

---

### Q8: How to perform rolling updates without downtime?

**Answer**: Blue-Green deployment with traffic migration

```
Week 1-2: Deploy v2 to "blue" (isolated, no traffic)
Week 3: Route 1% of traffic to blue, monitor for 1h
Week 4: 25% of traffic to blue
Week 5: 50% of traffic
Week 6: 100% of traffic on blue

Rollback instant if:
- Error rate > 1%
- Latency p99 > 2000ms
- Data corruption detected
```

**Benefits**:
- Zero downtime
- Quick rollback
- Gradual validation
- Customer experience unaffected

---

### Q9: How to partition users across multiple databases?

**Answer**: Shard by user_id

```
Shard Ring (Consistent Hashing):
├─ Node 1: user_ids 1-1M
├─ Node 2: user_ids 1M-2M
├─ Node 3: user_ids 2M-3M
└─ Node 4: user_ids 3M-4M

Query for user 500K:
    hash(500K) → Node 1
    Query Node 1 PostgreSQL
    
No cross-shard queries (fast)
Easy rebalancing with consistent hashing
```

---

### Q10: How to test scaling without actual infrastructure?

**Answer**: Load testing + chaos testing

**Load Testing**:
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

**Chaos Testing**:
1. Kill random replica → system should failover
2. Add 100ms latency to DB → measure degradation
3. Partition network for 30s → test recovery
4. Spike: 100 TPS → 5000 TPS → test auto-scaling
5. Slow down price cache → verify fallback to DB

**Verify After Tests**:
- No order double-execution
- No lost funds
- No stale portfolio values
- Payment consistency

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

print(f"✅ Deposit: Account created with ${account.get_balance():.2f}")
```

### Demo 2: Market Orders

```python
# Place market buy order
order1 = OrderFactory.create_order(
    account, apple, 10, OrderType.BUY, PriceType.MARKET
)
exchange.place_order(order1)

print(f"✅ Market Buy: 10 AAPL @ ${apple.current_price:.2f}")
print(f"   Total Cost: ${order1.quantity * apple.current_price:.2f}")
```

### Demo 3: Portfolio Valuation

```python
pnl = account.portfolio.get_profit_loss()
print(f"✅ Portfolio Value: ${account.portfolio.calculate_value():.2f}")
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

print(f"✅ Limit Sell: 5 AAPL @ $160.00 (currently ${apple.current_price:.2f})")

# Trigger execution by updating price
exchange.update_stock_price("AAPL", 165.00)
print(f"✅ Price increased to $165.00 → Limit order executed!")
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

print(f"✅ Final Balance: ${account.get_balance():,.2f}")
print(f"   Net Worth: ${account.get_net_worth():,.2f}")
```

---

## Key Takeaways

| Aspect | Implementation |
|--------|-----------------|
| **Order Execution** | Strategy pattern for Market vs Limit |
| **Price Updates** | Observer pattern for real-time recalculation |
| **Portfolio Tracking** | Average cost basis for accurate P/L |
| **State Management** | Clear order lifecycle (PENDING → EXECUTED/CANCELLED) |
| **Concurrency** | Thread-safe Singleton + distributed locks (Redis) |
| **Scalability** | Microservices, sharding by user_id, event streaming |
| **Atomicity** | Two-phase commit for fund transfer + execution |

---

## Success Checklist

- [ ] Explain 6 design patterns clearly
- [ ] Draw UML diagram with all entities
- [ ] Implement market and limit orders
- [ ] Calculate portfolio profit/loss correctly
- [ ] Handle concurrent order placement
- [ ] Discuss scaling to 1M users
- [ ] Run all 5 demo scenarios successfully
- [ ] Answer 10+ interview questions confidently

---

**You're ready for your interview! Let's trade! 📈**
