# 🏧 ATM - 75 Minute Interview Implementation Guide

## System Overview
A multi-user ATM system supporting card-based authentication, balance inquiries, cash withdrawal/deposit, transaction history, session management, and concurrent user access. The system must handle card validation, insufficient funds, daily limits, and automatic session timeouts.

---

## Core Requirements

### Functional Requirements
- **Authentication**: User login via ATM card and PIN verification
- **Balance Inquiry**: Check account balance in real-time
- **Withdrawal**: Withdraw cash with daily/transaction limits
- **Deposit**: Deposit cash to account
- **Transaction History**: View last N transactions
- **Session Management**: Auto-logout after inactivity timeout
- **Multiple Cards**: Support multiple cards per user
- **Error Handling**: Handle insufficient funds, invalid PIN, card lock

### Non-Functional Requirements
- Support 1000+ concurrent users
- Session timeout after 5 minutes inactivity
- Daily withdrawal limit (e.g., $2,000)
- Per-transaction limit (e.g., $500)
- Thread-safe operations
- Real-time notifications for transactions

### Scale & Constraints
- ATM machines: 10-100 nationwide
- Users per machine: 1-10 per minute
- Daily transactions per machine: 5,000+
- Cash limits: Track per machine
- PIN retries: 3 attempts max

---

## 75-Minute Implementation Timeline

### Phase 0: Requirements Clarification (0-5 minutes)
**Goal**: Define scope and constraints

**Clarifications**:
- Who manages accounts? (Central bank system)
- How often is PIN validated? (Per session)
- What triggers session timeout? (Inactivity, explicit logout)
- How are daily limits enforced? (Per user, per machine, per card?)
- Concurrent user handling? (Threading/locks)

**Expected Output**: Clear requirements and entity relationships

---

### Phase 1: Architecture & Design (5-15 minutes)
**Goal**: Define system architecture and patterns

**High-Level Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    ATM System (Singleton)                   │
├─────────────────────────────────────────────────────────────┤
│  • Manages all machines, users, sessions                    │
│  • Delegates to ATMachine for local operations              │
│  • Coordinates with Bank backend (simulated)                │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│                    ATM Machine (Location)                   │
├─────────────────────────────────────────────────────────────┤
│  • Cash management                                          │
│  • Session handling                                         │
│  • Transaction processing                                  │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│              Card Reader & Authentication                   │
├─────────────────────────────────────────────────────────────┤
│  • Card validation                                          │
│  • PIN verification                                         │
│  • Session creation                                        │
└─────────────────────────────────────────────────────────────┘
```

**Design Patterns**:
1. **Singleton**: ATMSystem instance - single coordinator
2. **Strategy**: Different transaction types (Withdrawal, Deposit, BalanceInquiry)
3. **Observer**: Notify systems of account changes
4. **State**: Session state management (LoggedOut, LoggedIn, Locked)
5. **Factory**: Create transactions based on type

**Key Decisions**:
- Use enum-based state machine for Session
- Strategy pattern for transaction types
- Observer pattern for notifications
- Thread locks for concurrent operations
- Time-based session expiry

**Expected Output**: Architecture diagram + pseudocode structure

---

### Phase 2: Core Entities (15-35 minutes)
**Goal**: Implement all core entities with full business logic

#### 1. Enumerations & Constants
```python
from enum import Enum
from datetime import datetime, timedelta
import threading
from abc import ABC, abstractmethod

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
```

#### 2. User & Card Management
```python
class Card:
    """Represents physical ATM card"""
    def __init__(self, card_number: str, pin: str, user_id: str):
        self.card_number = card_number
        self.pin = pin
        self.user_id = user_id
        self.status = CardStatus.ACTIVE
        self.failed_attempts = 0
        self.blocked_until = None
    
    def is_valid(self) -> bool:
        """Card is valid if not blocked/expired"""
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
        """Block card for 30 minutes"""
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
    
    def get_primary_account(self) -> 'Account':
        return self.accounts[0] if self.accounts else None
```

#### 3. Account Management
```python
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
    
    def can_withdraw(self, amount: float) -> tuple[bool, str]:
        """Check withdrawal eligibility"""
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
```

#### 4. Transaction Entities
```python
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
```

#### 5. Session Management
```python
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
```

#### 6. ATM Machine & System
```python
class ATMMachine:
    """Represents physical ATM"""
    def __init__(self, machine_id: str, location: str, cash_balance: float = 10000.0):
        self.machine_id = machine_id
        self.location = location
        self.cash_balance = cash_balance
        self.sessions = {}
        self.transactions = []
        self.lock = threading.Lock()
    
    def has_cash(self, amount: float) -> bool:
        """Check ATM cash"""
        with self.lock:
            return amount <= self.cash_balance
    
    def dispense_cash(self, amount: float) -> bool:
        """Dispense cash"""
        with self.lock:
            if self.has_cash(amount):
                self.cash_balance -= amount
                return True
            return False
    
    def accept_deposit(self, amount: float):
        """Accept deposit"""
        with self.lock:
            self.cash_balance += amount

class ATMSystem:
    """Singleton: Central coordinator"""
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
    
    def login(self, card_number: str, pin: str, machine_id: str):
        """Authenticate user"""
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
                           amount: float = 0.0):
        """Process transaction"""
        if session.is_expired():
            return False, "Session expired"
        
        session.update_activity()
        
        account = session.user.get_primary_account()
        if not account:
            return False, "No account linked"
        
        trans_id = f"TRX_{datetime.now().timestamp()}"
        transaction = Transaction(trans_id, account.account_id, trans_type, amount)
        
        if trans_type == TransactionType.WITHDRAWAL:
            if not session.atm_machine.has_cash(amount):
                return False, "ATM has insufficient cash"
        
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
    
    def get_transaction_history(self, session: Session, limit: int = 5):
        """Get recent transactions"""
        if session.is_expired():
            return []
        
        account = session.user.get_primary_account()
        if not account:
            return []
        
        return account.transactions[-limit:]
    
    def logout(self, session: Session):
        """End session"""
        session.logout()
        if session.card.card_number in session.atm_machine.sessions:
            del session.atm_machine.sessions[session.card.card_number]
        
        self._notify_observers(f"User {session.user.user_id} logged out", {
            "user_id": session.user.user_id
        })
    
    def add_observer(self, observer: 'TransactionObserver'):
        """Add observer"""
        self.observers.append(observer)
    
    def _notify_observers(self, event: str, data: dict):
        """Notify observers"""
        for observer in self.observers:
            observer.update(event, data)
```

---

### Phase 3: Design Patterns (35-55 minutes)

#### Pattern 1: Singleton (System Coordinator)
Thread-safe global ATMSystem ensures single instance managing all state, preventing conflicts.

#### Pattern 2: Strategy (Transaction Types)
TransactionType enum allows handling different logic (WITHDRAWAL/DEPOSIT/BALANCE_INQUIRY) without modifying core code.

#### Pattern 3: Observer (Notifications)
Observer interface enables multiple systems (Email/SMS/Push) reacting independently to transactions.

#### Pattern 4: State (Session Lifecycle)
SessionState enum manages clear transitions (LOGGED_OUT → LOGGED_IN → EXPIRED) preventing invalid operations.

#### Pattern 5: Factory (Transaction Creation)
Centralized Transaction creation with validation and ID generation.

---

### Phase 4: System Integration & Edge Cases (55-70 minutes)

**Login Flow**: Card validation → PIN check (3 attempts) → Session creation with timeout

**Transaction Flow**: Session validation → Limit checks (daily/transaction) → Balance check → Account update → ATM cash update → Observer notifications

**Edge Cases**:
- Card blocked after 3 failed attempts (30-min timeout)
- Daily limit resets at midnight
- ATM cash insufficient
- Session timeout during operation
- Concurrent access (thread locks)
- Account balance insufficient

**SOLID Principles**:
- **S**: Each class has single purpose (Card/Account/Session)
- **O**: New patterns via abstraction (Observer interface)
- **L**: Observers interchangeable
- **I**: Focused interfaces (TransactionObserver)
- **D**: Depend on abstractions (Observer, not concrete classes)

---

### Phase 5: Demo Scenarios (70-75 minutes)

1. **Successful Login & Balance Inquiry**: Login → Check balance → Display $1500
2. **Successful Withdrawal**: Verify limits → Deduct account → Dispense cash → Notify
3. **Failed Withdrawal (Insufficient Funds)**: Check balance $500 < $1000 requested → Fail
4. **Daily Limit Exceeded**: $1800 used + $300 request > $2000 limit → Fail
5. **Failed Login & Card Block**: 3 wrong PINs → Card blocked 30 min

---

## Class Diagram (ASCII UML)

```
                          ┌──────────────┐
                          │  ATMSystem   │◄────── Singleton
                          │  (Singleton) │
                          └──────┬───────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
           ┌────▼────┐      ┌────▼────┐      ┌────▼─────┐
           │  Users   │      │Accounts │      │ Machines │
           └──────────┘      └─────────┘      └──────────┘
                │                │                │
         ┌──────▼──────┐    ┌─────▼────┐    ┌────▼─────┐
         │   User      │    │ Account  │    │ATMMachine│
         ├─────────────┤    ├──────────┤    ├──────────┤
         │+user_id     │    │+balance  │    │+cash_bal │
         │+name        │    │+limits   │    │+sessions │
         │+cards[]     │    │+trans[]  │    │+trans[]  │
         │+accounts[]  │    │+lock     │    │+lock     │
         └─────────────┘    └─────────┘    └──────────┘
              │
         ┌────▼──────┐
         │   Card    │
         ├───────────┤
         │+card_no   │
         │+pin       │
         │+status    │
         │+attempts  │
         └───────────┘

         Session: user_id, state (LOGGED_IN/OUT/LOCKED), timeout
         Transaction: type, amount, status (PENDING/SUCCESS/FAIL)
         Observer: EmailNotifier, SMSNotifier, PushNotifier
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: What is ATMSystem's main responsibility?**
A: Singleton pattern ensures single global instance coordinating all ATM operations (users, accounts, machines, sessions, transactions).

**Q2: Why block a card after 3 failed PIN attempts?**
A: Prevents brute-force attacks while protecting legitimate users from accidental lockouts with 30-minute timeout.

**Q3: What is a session and why is it important?**
A: Session represents user's active state after login, managing timeout (auto-logout after 5 min inactivity) and preventing session hijacking.

### Intermediate Level

**Q4: How are withdrawal limits (daily and per-transaction) enforced?**
A: Per-transaction limit ($500 max) and daily limit ($2000 max) both checked before withdrawal. System resets daily limit at midnight and tracks usage.

**Q5: How is thread-safety ensured for concurrent users?**
A: Account, ATMMachine, ATMSystem each have threading.Lock(). Critical operations acquire locks: `with self.lock: [atomic operation]`.

**Q6: What happens if ATM runs out of cash?**
A: System checks `has_cash()` before dispensing. If insufficient, transaction fails with "ATM has insufficient cash". User tries different ATM or waits for replenishment.

**Q7: How does Observer pattern help notifications?**
A: Decouples notifications from core logic. Multiple observers (Email/SMS/Push) independently notified without coupling to ATMSystem.

### Advanced Level

**Q8: How would you handle session timeout in production?**
A: Background thread periodically checks all sessions. Expired sessions cleaned up, resources freed, user notified. Trade-off: automatic cleanup vs resource efficiency.

**Q9: What if ATM doesn't have change for deposit?**
A: Current system accepts all. Production checks capacity, offers partial deposit, or uses smart bill-counting. Trade-off: complexity vs user experience.

**Q10: How would you scale to 100 ATMs and 10,000 users?**
A: Use database instead of in-memory storage. Distributed ATMSystem with shared DB. Add Redis for sessions, message queue for notifications, load balancer. Trade-off: consistency vs availability (CAP).

**Q11: What security vulnerabilities exist?**
A: PIN stored as plaintext (hash instead). No encryption for card data. No audit logging. Session tokens not random (use UUID). No rate limiting on login.

**Q12: How would you test this system?**
A: Unit tests for card validation, limits, updates. Integration tests for full flows. Load tests for 1000 concurrent users. Security tests for brute force, double-spend.

---

## Summary

✅ **Singleton** for global coordination
✅ **Strategy** for transaction types
✅ **Observer** for notifications
✅ **State** for session lifecycle
✅ **Factory** for transaction creation
✅ **Thread-safe** with locks
✅ **Edge cases** handled (limits, blocking, timeout)
✅ **SOLID** principles throughout
✅ **Security** considerations
✅ **Scalability** discussion

**Key Takeaway**: ATM system demonstrates multiple patterns working together for secure, maintainable, scalable financial system with concurrent access, state management, and real-time notifications.
