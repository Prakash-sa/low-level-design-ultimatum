# 📈 Online Stock Brokerage System - Low Level Design

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
