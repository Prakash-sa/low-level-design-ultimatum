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
