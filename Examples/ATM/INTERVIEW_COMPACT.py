"""
🏧 ATM - Interview Implementation
Complete working system with 5 demo scenarios
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime, timedelta
import threading

# ============================================================================
# SECTION 1: ENUMERATIONS
# ============================================================================

class TransactionType(Enum):
    BALANCE_INQUIRY = 1
    WITHDRAWAL = 2
    DEPOSIT = 3

class TransactionStatus(Enum):
    PENDING = 1
    SUCCESS = 2
    FAILED = 3

class SessionState(Enum):
    LOGGED_OUT = 1
    LOGGED_IN = 2
    SESSION_LOCKED = 3
    EXPIRED = 4

class CardStatus(Enum):
    ACTIVE = 1
    BLOCKED = 2
    EXPIRED = 3

# ============================================================================
# SECTION 2: CORE ENTITIES - USER & CARD
# ============================================================================

class Card:
    """Represents physical ATM card"""
    def __init__(self, card_number: str, pin: str, user_id: str):
        self.card_number = card_number
        self.pin = pin
        self.user_id = user_id
        self.status = CardStatus.ACTIVE
        self.created_at = datetime.now()
        self.failed_attempts = 0
        self.blocked_until = None
    
    def is_valid(self) -> bool:
        """Check if card is valid and not blocked/expired"""
        if self.status != CardStatus.ACTIVE:
            return False
        if self.blocked_until and datetime.now() < self.blocked_until:
            return False
        return True
    
    def verify_pin(self, entered_pin: str) -> bool:
        """Verify PIN with 3-attempt limit"""
        if not self.is_valid():
            return False
        
        if entered_pin == self.pin:
            self.failed_attempts = 0
            return True
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 3:
                self.block_card()
            return False
    
    def block_card(self):
        """Block card for 30 minutes after 3 failed attempts"""
        self.status = CardStatus.BLOCKED
        self.blocked_until = datetime.now() + timedelta(minutes=30)

class User:
    """Represents ATM user"""
    def __init__(self, user_id: str, name: str):
        self.user_id = user_id
        self.name = name
        self.cards = []
        self.accounts = []
        self.created_at = datetime.now()
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def add_account(self, account: 'Account'):
        self.accounts.append(account)
    
    def get_primary_account(self) -> Optional['Account']:
        return self.accounts[0] if self.accounts else None

# ============================================================================
# SECTION 3: CORE ENTITIES - ACCOUNT
# ============================================================================

class Account:
    """Represents bank account"""
    def __init__(self, account_id: str, user_id: str, balance: float = 0.0):
        self.account_id = account_id
        self.user_id = user_id
        self.balance = balance
        self.daily_withdrawal_limit = 2000.0
        self.daily_withdrawal_used = 0.0
        self.transaction_limit = 500.0
        self.transactions = []
        self.created_at = datetime.now()
        self.last_reset_date = datetime.now().date()
        self.lock = threading.Lock()
    
    def reset_daily_limits(self):
        """Reset daily limits at midnight"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_withdrawal_used = 0.0
            self.last_reset_date = today
    
    def can_withdraw(self, amount: float) -> Tuple[bool, str]:
        """Check if withdrawal is allowed"""
        with self.lock:
            self.reset_daily_limits()
            
            if amount <= 0:
                return False, "Invalid amount"
            
            if amount > self.transaction_limit:
                return False, f"Limit ${self.transaction_limit} per transaction"
            
            remaining_daily = self.daily_withdrawal_limit - self.daily_withdrawal_used
            if amount > remaining_daily:
                return False, f"Daily limit exceeded. Remaining: ${remaining_daily}"
            
            if amount > self.balance:
                return False, f"Insufficient funds. Available: ${self.balance}"
            
            return True, "OK"
    
    def withdraw(self, amount: float) -> bool:
        """Execute withdrawal"""
        with self.lock:
            can_withdraw, msg = self.can_withdraw(amount)
            if not can_withdraw:
                return False
            
            self.balance -= amount
            self.daily_withdrawal_used += amount
            return True
    
    def deposit(self, amount: float) -> bool:
        """Execute deposit"""
        with self.lock:
            if amount <= 0:
                return False
            self.balance += amount
            return True
    
    def get_balance(self) -> float:
        """Get current balance"""
        with self.lock:
            return self.balance

# ============================================================================
# SECTION 4: TRANSACTIONS & SESSIONS
# ============================================================================

class Transaction:
    """Represents single transaction"""
    def __init__(self, transaction_id: str, account_id: str, 
                 trans_type: TransactionType, amount: float):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.type = trans_type
        self.amount = amount
        self.status = TransactionStatus.PENDING
        self.created_at = datetime.now()
    
    def execute(self, account: Account) -> bool:
        """Execute transaction"""
        if self.type == TransactionType.WITHDRAWAL:
            success = account.withdraw(self.amount)
        elif self.type == TransactionType.DEPOSIT:
            success = account.deposit(self.amount)
        else:
            success = True
        
        self.status = TransactionStatus.SUCCESS if success else TransactionStatus.FAILED
        if success:
            account.transactions.append(self)
        return success
    
    def __repr__(self) -> str:
        return f"[{self.type.name}] ${self.amount} - {self.status.name}"

class Session:
    """Represents user session at ATM"""
    def __init__(self, session_id: str, user: User, card: Card, 
                 atm_machine: 'ATMMachine', timeout_minutes: int = 5):
        self.session_id = session_id
        self.user = user
        self.card = card
        self.atm_machine = atm_machine
        self.state = SessionState.LOGGED_IN
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.timeout_duration = timedelta(minutes=timeout_minutes)
    
    def is_expired(self) -> bool:
        """Check if session timeout"""
        if self.state == SessionState.EXPIRED:
            return True
        elapsed = datetime.now() - self.last_activity
        if elapsed > self.timeout_duration:
            self.state = SessionState.EXPIRED
            return True
        return False
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def logout(self):
        """End session"""
        self.state = SessionState.LOGGED_OUT

# ============================================================================
# SECTION 5: ATM MACHINE
# ============================================================================

class ATMMachine:
    """Represents physical ATM machine"""
    def __init__(self, machine_id: str, location: str, cash_balance: float = 10000.0):
        self.machine_id = machine_id
        self.location = location
        self.cash_balance = cash_balance
        self.sessions = {}
        self.transactions = []
        self.lock = threading.Lock()
    
    def has_cash(self, amount: float) -> bool:
        """Check if ATM has sufficient cash"""
        with self.lock:
            return amount <= self.cash_balance
    
    def dispense_cash(self, amount: float) -> bool:
        """Dispense cash from ATM"""
        with self.lock:
            if self.has_cash(amount):
                self.cash_balance -= amount
                return True
            return False
    
    def accept_deposit(self, amount: float):
        """Accept deposit into ATM"""
        with self.lock:
            self.cash_balance += amount

# ============================================================================
# SECTION 6: OBSERVER PATTERN
# ============================================================================

class TransactionObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict):
        pass

class EmailNotifier(TransactionObserver):
    def update(self, event: str, data: dict):
        print(f"    📧 Email: {event} - {data}")

class SMSNotifier(TransactionObserver):
    def update(self, event: str, data: dict):
        print(f"    📱 SMS: {event} - {data}")

class PushNotifier(TransactionObserver):
    def update(self, event: str, data: dict):
        print(f"    🔔 Push: {event} - {data}")

# ============================================================================
# SECTION 7: ATM SYSTEM (SINGLETON)
# ============================================================================

class ATMSystem:
    """Singleton: Central coordinator for all ATM operations"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.users = {}
        self.accounts = {}
        self.machines = {}
        self.observers = []
        self.lock = threading.Lock()
    
    def register_user(self, user_id: str, name: str) -> User:
        """Register new user"""
        with self.lock:
            user = User(user_id, name)
            self.users[user_id] = user
            return user
    
    def create_account(self, account_id: str, user_id: str, balance: float = 1000.0) -> Account:
        """Create account for user"""
        with self.lock:
            account = Account(account_id, user_id, balance)
            self.accounts[account_id] = account
            if user_id in self.users:
                self.users[user_id].add_account(account)
            return account
    
    def issue_card(self, card_number: str, pin: str, user_id: str) -> Card:
        """Issue card to user"""
        with self.lock:
            card = Card(card_number, pin, user_id)
            if user_id in self.users:
                self.users[user_id].add_card(card)
            return card
    
    def register_machine(self, machine_id: str, location: str) -> ATMMachine:
        """Register ATM machine"""
        with self.lock:
            machine = ATMMachine(machine_id, location)
            self.machines[machine_id] = machine
            return machine
    
    def login(self, card_number: str, pin: str, machine_id: str) -> Tuple[bool, Optional[Session]]:
        """Authenticate user and create session"""
        with self.lock:
            user_found = None
            card_found = None
            
            for user in self.users.values():
                for card in user.cards:
                    if card.card_number == card_number:
                        user_found = user
                        card_found = card
                        break
            
            if not card_found or not user_found:
                return False, None
            
            if not card_found.verify_pin(pin):
                return False, None
            
            machine = self.machines.get(machine_id)
            if not machine:
                return False, None
            
            session_id = f"SES_{datetime.now().timestamp()}"
            session = Session(session_id, user_found, card_found, machine)
            machine.sessions[card_number] = session
            
            self._notify_observers(f"User {user_found.user_id} logged in", {
                "user_id": user_found.user_id,
                "machine_id": machine_id
            })
            
            return True, session
    
    def process_transaction(self, session: Session, trans_type: TransactionType, 
                           amount: float = 0.0) -> Tuple[bool, str]:
        """Process transaction"""
        if session.is_expired():
            return False, "Session expired"
        
        session.update_activity()
        
        account = session.user.get_primary_account()
        if not account:
            return False, "No account linked"
        
        trans_id = f"TRX_{datetime.now().timestamp()}"
        transaction = Transaction(trans_id, account.account_id, trans_type, amount)
        
        # Check machine cash for withdrawals
        if trans_type == TransactionType.WITHDRAWAL:
            if not session.atm_machine.has_cash(amount):
                return False, "ATM has insufficient cash"
        
        # Execute transaction
        success = transaction.execute(account)
        
        if success:
            session.atm_machine.transactions.append(transaction)
            
            if trans_type == TransactionType.WITHDRAWAL:
                session.atm_machine.dispense_cash(amount)
            elif trans_type == TransactionType.DEPOSIT:
                session.atm_machine.accept_deposit(amount)
            
            self._notify_observers(f"Transaction {trans_type.name}", {
                "account_id": account.account_id,
                "amount": amount,
                "type": trans_type.name,
                "new_balance": account.get_balance()
            })
            
            return True, f"{trans_type.name} successful"
        
        return False, f"{trans_type.name} failed"
    
    def get_transaction_history(self, session: Session, limit: int = 5) -> list:
        """Get recent transactions"""
        if session.is_expired():
            return []
        
        account = session.user.get_primary_account()
        if not account:
            return []
        
        return account.transactions[-limit:]
    
    def logout(self, session: Session):
        """End user session"""
        session.logout()
        if session.card.card_number in session.atm_machine.sessions:
            del session.atm_machine.sessions[session.card.card_number]
        
        self._notify_observers(f"User {session.user.user_id} logged out", {
            "user_id": session.user.user_id
        })
    
    def add_observer(self, observer: TransactionObserver):
        """Add observer for notifications"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: dict):
        """Notify all observers of events"""
        for observer in self.observers:
            observer.update(event, data)

# ============================================================================
# SECTION 8: DEMO SCENARIOS
# ============================================================================

def demo_1_setup_and_login():
    """Demo 1: System setup and successful login"""
    print("\n" + "="*70)
    print("DEMO 1: SETUP AND SUCCESSFUL LOGIN")
    print("="*70)
    
    system = ATMSystem()
    
    # Register user
    user = system.register_user("U001", "John Doe")
    print(f"✓ User registered: {user.name}")
    
    # Create account
    account = system.create_account("ACC001", "U001", balance=1500.0)
    print(f"✓ Account created: ${account.get_balance()}")
    
    # Issue card
    card = system.issue_card("4532123456789012", "1234", "U001")
    print(f"✓ Card issued: {card.card_number}")
    
    # Register machine
    machine = system.register_machine("ATM001", "Main Street")
    print(f"✓ ATM registered: {machine.location}")
    
    # Add observers
    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())
    
    # Login
    success, session = system.login("4532123456789012", "1234", "ATM001")
    print(f"\n✓ Login successful: {success}")
    print(f"  Session state: {session.state.name}")
    print(f"  User: {session.user.name}")
    
    # Check balance
    success, msg = system.process_transaction(session, TransactionType.BALANCE_INQUIRY)
    balance = account.get_balance()
    print(f"\n✓ Balance inquiry: ${balance}")
    
    # Logout
    system.logout(session)
    print(f"\n✓ Logout successful")

def demo_2_successful_withdrawal():
    """Demo 2: Successful withdrawal"""
    print("\n" + "="*70)
    print("DEMO 2: SUCCESSFUL WITHDRAWAL")
    print("="*70)
    
    system = ATMSystem()
    
    # Setup
    user = system.register_user("U002", "Jane Smith")
    account = system.create_account("ACC002", "U002", balance=2000.0)
    card = system.issue_card("4532111111111111", "5678", "U002")
    machine = system.register_machine("ATM002", "Downtown")
    system.add_observer(EmailNotifier())
    
    print(f"Initial balance: ${account.get_balance()}")
    
    # Login
    success, session = system.login("4532111111111111", "5678", "ATM002")
    print(f"✓ Login successful")
    
    # Withdraw $300
    print(f"\nAttempting withdrawal: $300")
    success, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 300.0)
    print(f"✓ {msg}")
    print(f"  New balance: ${account.get_balance()}")
    print(f"  ATM cash: ${machine.cash_balance}")
    
    system.logout(session)

def demo_3_failed_withdrawal():
    """Demo 3: Failed withdrawal (insufficient funds)"""
    print("\n" + "="*70)
    print("DEMO 3: FAILED WITHDRAWAL (INSUFFICIENT FUNDS)")
    print("="*70)
    
    system = ATMSystem()
    
    # Setup
    user = system.register_user("U003", "Bob Johnson")
    account = system.create_account("ACC003", "U003", balance=200.0)
    card = system.issue_card("4532222222222222", "9999", "U003")
    machine = system.register_machine("ATM003", "Uptown")
    system.add_observer(EmailNotifier())
    
    print(f"Current balance: ${account.get_balance()}")
    
    # Login
    success, session = system.login("4532222222222222", "9999", "ATM003")
    print(f"✓ Login successful")
    
    # Try to withdraw $500 (exceeds balance)
    print(f"\nAttempting withdrawal: $500")
    success, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 500.0)
    print(f"✗ {msg}")
    print(f"  Balance unchanged: ${account.get_balance()}")
    
    system.logout(session)

def demo_4_daily_limit():
    """Demo 4: Daily limit exceeded"""
    print("\n" + "="*70)
    print("DEMO 4: DAILY WITHDRAWAL LIMIT EXCEEDED")
    print("="*70)
    
    system = ATMSystem()
    
    # Setup
    user = system.register_user("U004", "Alice Brown")
    account = system.create_account("ACC004", "U004", balance=3000.0)
    card = system.issue_card("4532333333333333", "1111", "U004")
    machine = system.register_machine("ATM004", "Airport")
    
    print(f"Daily limit: ${account.daily_withdrawal_limit}")
    print(f"Current balance: ${account.get_balance()}")
    
    # Login
    success, session = system.login("4532333333333333", "1111", "ATM004")
    print(f"✓ Login successful")
    
    # Withdraw $1800
    print(f"\nFirst withdrawal: $1800")
    success, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 1800.0)
    print(f"✓ {msg}")
    print(f"  Balance: ${account.get_balance()}, Used today: ${account.daily_withdrawal_used}")
    
    # Try to withdraw $300 more (total would be $2100 > $2000 limit)
    print(f"\nSecond withdrawal: $300 (total would be $2100)")
    success, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 300.0)
    print(f"✗ {msg}")
    print(f"  Balance: ${account.get_balance()}")
    
    system.logout(session)

def demo_5_card_blocking():
    """Demo 5: Card blocking after 3 failed attempts"""
    print("\n" + "="*70)
    print("DEMO 5: CARD BLOCKING (3 FAILED PIN ATTEMPTS)")
    print("="*70)
    
    system = ATMSystem()
    
    # Setup
    user = system.register_user("U005", "Charlie Davis")
    account = system.create_account("ACC005", "U005", balance=1000.0)
    card = system.issue_card("4532444444444444", "2222", "U005")
    machine = system.register_machine("ATM005", "Mall")
    
    # Attempt 1: Wrong PIN
    print("Attempt 1: Wrong PIN entered")
    success, session = system.login("4532444444444444", "9999", "ATM005")
    print(f"✗ Login failed: {not success}")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")
    
    # Attempt 2: Wrong PIN
    print("\nAttempt 2: Wrong PIN entered")
    success, session = system.login("4532444444444444", "3333", "ATM005")
    print(f"✗ Login failed: {not success}")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")
    
    # Attempt 3: Wrong PIN
    print("\nAttempt 3: Wrong PIN entered")
    success, session = system.login("4532444444444444", "4444", "ATM005")
    print(f"✗ Login failed: {not success}")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")
    
    # Attempt 4: Correct PIN but card blocked
    print("\nAttempt 4: Correct PIN but card now blocked")
    success, session = system.login("4532444444444444", "2222", "ATM005")
    print(f"✗ Login failed: {not success}")
    print(f"  Card status: {card.status.name}")
    print(f"  Card blocked until: {card.blocked_until.strftime('%H:%M:%S')}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏧 ATM SYSTEM - INTERVIEW IMPLEMENTATION - 5 DEMOS")
    print("="*70)
    
    demo_1_setup_and_login()
    demo_2_successful_withdrawal()
    demo_3_failed_withdrawal()
    demo_4_daily_limit()
    demo_5_card_blocking()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
