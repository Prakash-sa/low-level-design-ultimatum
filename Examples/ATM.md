# ATM System — Complete Design Guide

> Card-based authentication, PIN verification, cash withdrawal/deposit with daily limits, session management with auto-logout, and concurrent multi-user access.

**Scale**: 1,000+ concurrent users, 100+ ATM machines, 99.9% uptime
**Duration**: 75-minute interview guide
**Focus**: Secure authentication, limit enforcement, session lifecycle, thread-safe balance updates

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
A user inserts a card → enters PIN (3 attempts max before block) → system creates a timed session → user does balance inquiry / withdrawal / deposit under daily and per-transaction limits → session auto-expires after inactivity. Core concerns: security, correctness (no double-spend), and state management.

### Core Flow
```
Insert Card → Verify PIN (3 tries) → SESSION (5 min) → Withdraw / Deposit / Balance
                    ↓ 3 failures              ↓ inactivity
              CARD BLOCKED (30 min)      SESSION EXPIRED (auto-logout)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or networked?** → "Networked, 100+ ATMs sharing one backing system"
2. **Multiple cards/accounts per user?** → "Yes, a user can hold several cards and accounts"
3. **Real bank integration?** → "Mock backing service for the interview"
4. **Security depth (encryption/hashing)?** → "Discuss it; implement plaintext PIN for brevity"
5. **Offline mode?** → "Out of scope for the core; mention as a scaling concern"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Cardholder** | Authenticates & transacts | Insert card, enter PIN, withdraw, deposit, check balance |
| **Bank Admin** | Manages users & machines | Register users, issue cards, create accounts, register ATMs |
| **System** | Coordinator & notifier | Verify PIN, enforce limits, expire sessions, send notifications |

### Functional Requirements (What does the system do?)

✅ **Authentication**
  - Validate card + PIN with a 3-attempt limit
  - Block card for 30 minutes after 3 failed attempts

✅ **Balance & Transactions**
  - Real-time balance inquiry
  - Cash withdrawal with per-transaction and daily limits
  - Cash deposit
  - Record full transaction history

✅ **Session Management**
  - Create a session on successful login
  - Auto-logout after 5 minutes of inactivity
  - Reject operations on expired sessions

✅ **Notifications**
  - Notify on login, transaction success, logout
  - Support multiple channels (email, SMS, push)

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 1000+ simultaneous users
✅ **Consistency**: No double-spend; atomic balance updates
✅ **Latency**: O(1) authentication and balance lookups
✅ **Availability**: 99.9% uptime with redundant machines
✅ **Security**: Card blocking, session timeout, limit enforcement
✅ **Cleanup**: Expired sessions reclaimed automatically

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max PIN attempts** | 3 (then block card 30 min) |
| **Daily withdrawal limit** | $2,000 per account |
| **Per-transaction limit** | $500 |
| **Session timeout** | 5 minutes inactivity |
| **Multiple cards per user** | YES |
| **Real payment network** | NO — mock backing service |
| **PIN storage** | Plaintext for demo (hash in production) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
User, Card, Account, Session, ATMMachine, Transaction, Notification, ...
```

### Step 2.2: Define Core Classes

#### **Card** — A physical ATM card
```
Properties:
  - card_number: str
  - pin: str
  - user_id: str
  - status: CardStatus (ACTIVE, BLOCKED, EXPIRED)
  - failed_attempts: int
  - blocked_until: Optional[datetime]

Behaviors:
  - is_valid(): Check active & not blocked/expired
  - verify_pin(pin): Compare PIN, increment attempts, block on 3rd failure
  - block_card(): Set BLOCKED for 30 minutes
```

#### **User** — An ATM user profile
```
Properties:
  - user_id: str
  - name: str
  - cards: List[Card]
  - accounts: List[Account]

Behaviors:
  - add_card(card) / add_account(account)
  - get_primary_account(): Default account for transactions
```

#### **Account** — A bank account with limits
```
Properties:
  - account_id: str
  - user_id: str
  - balance: float
  - daily_withdrawal_limit: float ($2000)
  - daily_withdrawal_used: float
  - transaction_limit: float ($500)
  - transactions: List[Transaction]
  - lock: threading.Lock

Behaviors:
  - can_withdraw(amount): Validate limits + balance
  - withdraw(amount) / deposit(amount): Atomic balance change
  - reset_daily_limits(): Zero daily usage at midnight
  - get_balance(): Thread-safe read
```

#### **Session** — A user's active session at an ATM
```
Properties:
  - session_id: str
  - user: User
  - card: Card
  - atm_machine: ATMMachine
  - state: SessionState (LOGGED_IN, LOGGED_OUT, EXPIRED)
  - last_activity: datetime
  - timeout_duration: timedelta (5 min)

Behaviors:
  - is_expired(): Check inactivity timeout
  - update_activity(): Refresh last_activity
  - logout(): End session
```

#### **ATMMachine** — A physical ATM
```
Properties:
  - machine_id: str
  - location: str
  - cash_balance: float
  - sessions: Dict[str, Session]
  - transactions: List[Transaction]

Behaviors:
  - has_cash(amount): Check available cash
  - dispense_cash(amount) / accept_deposit(amount)
```

#### **Transaction** — A single operation record
```
Properties:
  - transaction_id: str
  - account_id: str
  - type: TransactionType (BALANCE_INQUIRY, WITHDRAWAL, DEPOSIT)
  - amount: float
  - status: TransactionStatus (PENDING, SUCCESS, FAILED)
  - created_at: datetime

Behaviors:
  - execute(account): Apply to account, set status
```

#### **ATMSystem** — Main controller (Singleton)
```
Properties:
  - users / accounts / machines: Dict
  - observers: List[TransactionObserver]
  - lock: threading.Lock

Behaviors:
  - register_user / create_account / issue_card / register_machine
  - login(card_number, pin, machine_id): Authenticate + create session
  - process_transaction(session, type, amount): Validate + execute
  - logout(session): End session
  - add_observer / notify_observers
```

### Step 2.3: Define Enumerations (State & Type)

```python
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

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Card** | Authentication + blocking | No brute-force protection |
| **User** | Owns cards/accounts | Can't link cards to balances |
| **Account** | Balance + limit tracking | Can't enforce limits or prevent overdraft |
| **Session** | Timed access control | Abandoned ATM stays logged in |
| **ATMMachine** | Physical cash management | Can't prevent cash overdraft |
| **Transaction** | Audit + history | No traceability |
| **ATMSystem** | Central coordination | No thread-safe single source of truth |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Login** ⭐ CRITICAL
```python
def login(card_number: str, pin: str, machine_id: str) -> Tuple[bool, Optional[Session]]:
    """
    Authenticate cardholder and open a session.

    Precondition: card is ACTIVE and not blocked
    Postcondition: session.state == LOGGED_IN on success

    Returns: (True, Session) on success, (False, None) on failure.

    Failure causes:
      - Card not found / invalid / blocked
      - Wrong PIN (increments failed_attempts; blocks card on 3rd)
      - Machine not found

    Concurrency: THREAD-SAFE (guarded by system lock)
    """
    pass
```

#### **2. Process Transaction** ⭐ CRITICAL
```python
def process_transaction(session: Session, trans_type: TransactionType,
                        amount: float = 0.0) -> Tuple[bool, str]:
    """
    Execute a balance inquiry, withdrawal, or deposit.

    Precondition: session not expired
    Postcondition: account balance updated atomically on success

    Returns: (True, message) or (False, reason).

    Failure causes:
      - Session expired
      - No linked account
      - ATM has insufficient cash (withdrawal)
      - Per-transaction / daily limit exceeded
      - Insufficient funds

    Side Effects: dispenses cash, records transaction, notifies observers
    Concurrency: THREAD-SAFE (account lock)
    """
    pass
```

#### **3. Logout**
```python
def logout(session: Session) -> None:
    """
    End a session and remove it from the machine.
    Postcondition: session.state == LOGGED_OUT
    Side Effects: notifies observers
    """
    pass
```

#### **4. Setup APIs**
```python
def register_user(user_id: str, name: str) -> User: ...
def create_account(account_id: str, user_id: str, balance: float = 1000.0) -> Account: ...
def issue_card(card_number: str, pin: str, user_id: str) -> Card: ...
def register_machine(machine_id: str, location: str) -> ATMMachine: ...
```

#### **5. Register Observer** (For Notifications)
```python
def add_observer(observer: TransactionObserver) -> None:
    """
    Register a callback for ATM events (login, transaction, logout).
    Observer is called: observer.update(event, data)
    Example: Add EmailNotifier + SMSNotifier for multi-channel alerts.
    """
    pass
```

### Step 3.2: Exception / Failure Model

This design returns `(bool, message)` tuples rather than raising, keeping the demo interview-friendly. A production version would raise a typed hierarchy:

```python
class ATMException(Exception): ...
class CardBlockedError(ATMException): ...
class InvalidPinError(ATMException): ...
class InsufficientFundsError(ATMException): ...
class DailyLimitExceededError(ATMException): ...
class SessionExpiredError(ATMException): ...
class ATMOutOfCashError(ATMException): ...
```

### Step 3.3: API Usage Example

```python
system = ATMSystem()

# 1. Setup
system.register_user("U001", "John Doe")
account = system.create_account("ACC001", "U001", balance=1500.0)
system.issue_card("4532123456789012", "1234", "U001")
system.register_machine("ATM001", "Main Street")
system.add_observer(EmailNotifier())

# 2. Login
ok, session = system.login("4532123456789012", "1234", "ATM001")

# 3. Withdraw
ok, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 300.0)

# 4. Logout
system.logout(session)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
ATMSystem HAS-A users / accounts / machines (1:N Composition)
  └─ System owns and manages lifecycle of all entities

User HAS-A cards (1:N Composition)
  └─ User owns multiple cards

User HAS-A accounts (1:N Composition)
  └─ User owns multiple accounts

Session REFERENCES user, card, machine (1:1 Association)
  └─ Session links to existing entities (no ownership)

ATMMachine HAS-A sessions (1:N Composition)
  └─ Machine tracks active sessions

Account HAS-A transactions (1:N Composition)
  └─ Account owns its transaction history

ATMSystem NOTIFIES TransactionObserver (1:N Association)
  └─ Multiple observers listen to events
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────┐
│     ATMSystem (Singleton)          │
├────────────────────────────────────┤
│ - users: Dict[str, User]           │
│ - accounts: Dict[str, Account]     │
│ - machines: Dict[str, ATMMachine]  │
│ - observers: List[Observer]        │
│ - lock: threading.Lock             │
├────────────────────────────────────┤
│ + login(...): (bool, Session)      │
│ + process_transaction(...): (bool) │
│ + logout(session): void            │
│ + add_observer(observer): void     │
└──────────────┬─────────────────────┘
       manages 1:N
   ┌──────────┼───────────┐
   ▼          ▼           ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│  User  │ │ Account │ │ATMMachine│
├────────┤ ├─────────┤ ├──────────┤
│user_id │ │balance  │ │cash      │
│cards[] │ │daily$   │ │sessions[]│
│accts[] │ │limit    │ │txns[]    │
└───┬────┘ └────┬────┘ └────┬─────┘
    │           │           │
    ▼           ▼           ▼
┌────────┐ ┌────────────┐ ┌──────────┐
│  Card  │ │Transaction │ │ Session  │
├────────┤ ├────────────┤ ├──────────┤
│number  │ │type: Enum  │ │state:Enum│
│pin     │ │amount      │ │last_act  │
│status  │ │status      │ │timeout   │
│blocked │ │created_at  │ │is_expired│
└────────┘ └────────────┘ └──────────┘

OBSERVER PATTERN (Notifications):
┌────────────────────────────────────┐
│ TransactionObserver (Abstract)     │
├────────────────────────────────────┤
│ + update(event, data)              │
└──┬─────────────────────────────────┘
   │ implemented by
   ├─→ EmailNotifier
   ├─→ SMSNotifier
   └─→ PushNotifier

STATE MACHINE (Session):
LOGGED_OUT ──login──→ LOGGED_IN ──timeout/logout──→ EXPIRED
      ▲                                                │
      └────────────────────────────────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| ATMSystem → Users | 1:N | Composition | System owns all users |
| ATMSystem → Accounts | 1:N | Composition | System owns all accounts |
| ATMSystem → Machines | 1:N | Composition | System owns all ATMs |
| User → Cards | 1:N | Composition | A user holds many cards |
| User → Accounts | 1:N | Composition | A user holds many accounts |
| Account → Transactions | 1:N | Composition | Account owns its history |
| ATMMachine → Sessions | 1:N | Composition | Machine tracks active sessions |
| Session → User/Card/Machine | 1:1 | Association | Session references entities |
| ATMSystem → Observers | 1:N | Association | System notifies many listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For ATMSystem)

**Problem**: Many threads/machines need one consistent view of users, accounts, and machines.

**Solution**: One global ATMSystem instance with thread-safe initialization.

```python
class ATMSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access
**Trade-off**: ⚠️ Global state (harder to test), ⚠️ Harder to scale across machines

---

### Pattern 2: **State** (For Session Lifecycle)

**Problem**: A session must move LOGGED_IN → EXPIRED / LOGGED_OUT and reject operations once invalid.

**Solution**: Explicit `SessionState` enum with timeout-driven transitions.

```python
def is_expired(self) -> bool:
    if self.state == SessionState.EXPIRED:
        return True
    if datetime.now() - self.last_activity > self.timeout_duration:
        self.state = SessionState.EXPIRED
        return True
    return False
```

**Benefit**: ✅ Explicit lifecycle, ✅ Invalid operations blocked
**Trade-off**: ⚠️ Must check state before each operation

---

### Pattern 3: **Observer** (For Notifications)

**Problem**: Login/withdrawal/logout events must trigger email/SMS/push without coupling.

**Solution**: Observer pattern decouples event producer from consumers.

```python
class TransactionObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict): pass

class EmailNotifier(TransactionObserver):
    def update(self, event: str, data: dict):
        print(f"📧 Email: {event} - {data}")

# Usage
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())
```

**Benefit**: ✅ Loose coupling, ✅ Easy to add new channels
**Trade-off**: ⚠️ Observer lifecycle management

---

### Pattern 4: **Strategy** (For Transaction Types)

**Problem**: Withdrawal, deposit, and inquiry behave differently and the set may grow.

**Solution**: `TransactionType` selects behavior in `execute()`; can graduate to a class-per-type strategy.

```python
def execute(self, account: Account) -> bool:
    if self.type == TransactionType.WITHDRAWAL:
        success = account.withdraw(self.amount)
    elif self.type == TransactionType.DEPOSIT:
        success = account.deposit(self.amount)
    else:
        success = True
    self.status = TransactionStatus.SUCCESS if success else TransactionStatus.FAILED
    return success
```

**Benefit**: ✅ Add new transaction types without touching core flow
**Trade-off**: ⚠️ Enum branch grows; promote to classes if it gets large

---

### Pattern 5: **Factory** (For Creating Transactions)

**Problem**: Creating a transaction requires consistent ID generation and initialization.

**Solution**: Centralize creation inside `process_transaction()`.

```python
trans_id = f"TRX_{datetime.now().timestamp()}"
transaction = Transaction(trans_id, account.account_id, trans_type, amount)
```

**Benefit**: ✅ Centralized, consistent initialization
**Trade-off**: ⚠️ If it grows, consider a dedicated factory/builder

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---|---|
| **Singleton** | Need single global ATMSystem | Consistent state across all clients |
| **State** | Session lifecycle correctness | Invalid operations blocked |
| **Observer** | Events trigger notifications | Loose coupling, event-driven |
| **Strategy** | Varying transaction behavior | Pluggable, easy to extend |
| **Factory** | Consistent transaction creation | Centralized, consistent IDs |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
🏧 ATM System - Interview Implementation
Demonstrates:
1. Setup & login
2. Successful withdrawal
3. Failed withdrawal (insufficient funds)
4. Daily limit exceeded
5. Card blocking after 3 failed PIN attempts
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime, timedelta
import threading
import uuid

# ============================================================================
# ENUMERATIONS
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
# CORE ENTITIES - USER & CARD
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
# CORE ENTITIES - ACCOUNT
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
        self.lock = threading.RLock()

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
                return False, "Amount must be positive"
            if amount > self.transaction_limit:
                return False, f"Amount exceeds per-transaction limit ${self.transaction_limit}"
            if self.daily_withdrawal_used + amount > self.daily_withdrawal_limit:
                remaining = self.daily_withdrawal_limit - self.daily_withdrawal_used
                return False, f"Daily limit exceeded. Remaining: ${remaining}"
            if amount > self.balance:
                return False, "Insufficient funds"
            return True, "OK"

    def withdraw(self, amount: float) -> bool:
        """Execute withdrawal (atomic check + debit)"""
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
# TRANSACTIONS & SESSIONS
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
# ATM MACHINE
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
        """Dispense cash from ATM (atomic check + debit)"""
        with self.lock:
            if amount <= self.cash_balance:
                self.cash_balance -= amount
                return True
            return False

    def accept_deposit(self, amount: float):
        """Accept deposit into ATM"""
        with self.lock:
            self.cash_balance += amount

# ============================================================================
# OBSERVER PATTERN
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
# ATM SYSTEM (SINGLETON)
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
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
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
                if card_found:
                    break

            if not card_found or not user_found:
                return False, None

            if not card_found.is_valid():
                return False, None

            if not card_found.verify_pin(pin):
                return False, None

            machine = self.machines.get(machine_id)
            if not machine:
                return False, None

            session_id = str(uuid.uuid4())
            session = Session(session_id, user_found, card_found, machine)
            machine.sessions[card_found.card_number] = session

            self._notify_observers(f"User {user_found.name} logged in", {
                "user_id": user_found.user_id
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

        if trans_type == TransactionType.WITHDRAWAL:
            if not session.atm_machine.has_cash(amount):
                return False, "ATM has insufficient cash"

        success = transaction.execute(account)

        if success:
            session.atm_machine.transactions.append(transaction)
            if trans_type == TransactionType.WITHDRAWAL:
                session.atm_machine.dispense_cash(amount)

            self._notify_observers(f"{trans_type.name} successful: ${amount}", {
                "user_id": session.user.user_id,
                "type": trans_type.name,
                "amount": amount
            })
            return True, f"{trans_type.name} successful"

        return False, f"{trans_type.name} failed"

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
# DEMO SCENARIOS
# ============================================================================

def demo_1_setup_and_login():
    """Demo 1: System setup and successful login"""
    print("\n" + "="*70)
    print("DEMO 1: SETUP AND SUCCESSFUL LOGIN")
    print("="*70)

    system = ATMSystem()

    user = system.register_user("U001", "John Doe")
    print(f"✓ User registered: {user.name}")

    account = system.create_account("ACC001", "U001", balance=1500.0)
    print(f"✓ Account created: ${account.get_balance()}")

    card = system.issue_card("4532123456789012", "1234", "U001")
    print(f"✓ Card issued: {card.card_number}")

    machine = system.register_machine("ATM001", "Main Street")
    print(f"✓ ATM registered: {machine.location}")

    system.add_observer(EmailNotifier())
    system.add_observer(SMSNotifier())

    success, session = system.login("4532123456789012", "1234", "ATM001")
    print(f"\n✓ Login successful: {success}")
    print(f"  Session state: {session.state.name}")
    print(f"  User: {session.user.name}")

    balance = account.get_balance()
    print(f"\n✓ Balance inquiry: ${balance}")

    system.logout(session)
    print(f"\n✓ Logout successful")

def demo_2_successful_withdrawal():
    """Demo 2: Successful withdrawal"""
    print("\n" + "="*70)
    print("DEMO 2: SUCCESSFUL WITHDRAWAL")
    print("="*70)

    system = ATMSystem()

    user = system.register_user("U002", "Jane Smith")
    account = system.create_account("ACC002", "U002", balance=2000.0)
    card = system.issue_card("4532111111111111", "5678", "U002")
    machine = system.register_machine("ATM002", "Downtown")
    system.add_observer(EmailNotifier())

    print(f"Initial balance: ${account.get_balance()}")

    success, session = system.login("4532111111111111", "5678", "ATM002")
    print(f"✓ Login successful")

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

    user = system.register_user("U003", "Bob Johnson")
    account = system.create_account("ACC003", "U003", balance=200.0)
    card = system.issue_card("4532222222222222", "9999", "U003")
    machine = system.register_machine("ATM003", "Uptown")
    system.add_observer(EmailNotifier())

    print(f"Current balance: ${account.get_balance()}")

    success, session = system.login("4532222222222222", "9999", "ATM003")
    print(f"✓ Login successful")

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

    user = system.register_user("U004", "Alice Brown")
    account = system.create_account("ACC004", "U004", balance=3000.0)
    card = system.issue_card("4532333333333333", "1111", "U004")
    machine = system.register_machine("ATM004", "Airport")

    print(f"Daily limit: ${account.daily_withdrawal_limit}")
    print(f"Current balance: ${account.get_balance()}")

    success, session = system.login("4532333333333333", "1111", "ATM004")
    print(f"✓ Login successful")

    print(f"\nFirst withdrawal: $1800")
    success, msg = system.process_transaction(session, TransactionType.WITHDRAWAL, 1800.0)
    print(f"✓ {msg}")
    print(f"  Balance: ${account.get_balance()}, Used today: ${account.daily_withdrawal_used}")

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

    user = system.register_user("U005", "Charlie Davis")
    account = system.create_account("ACC005", "U005", balance=1000.0)
    card = system.issue_card("4532444444444444", "2222", "U005")
    machine = system.register_machine("ATM005", "Mall")

    print("Attempt 1: Wrong PIN entered")
    success, session = system.login("4532444444444444", "9999", "ATM005")
    print(f"✗ Login failed")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")

    print("\nAttempt 2: Wrong PIN entered")
    success, session = system.login("4532444444444444", "3333", "ATM005")
    print(f"✗ Login failed")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")

    print("\nAttempt 3: Wrong PIN entered")
    success, session = system.login("4532444444444444", "4444", "ATM005")
    print(f"✗ Login failed")
    print(f"  Card status: {card.status.name}, Attempts: {card.failed_attempts}")

    print("\nAttempt 4: Correct PIN but card now blocked")
    success, session = system.login("4532444444444444", "2222", "ATM005")
    print(f"✗ Login failed")
    print(f"  Card status: {card.status.name}")

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
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **login** | System lock | Atomic card lookup + PIN verify + session creation |
| **withdraw** | Account RLock | Atomic check-limit + debit (no double-spend) |
| **dispense_cash** | Machine lock | No cash overdraft across concurrent withdrawals |
| **deposit** | Account RLock | Atomic balance increment |
| **Singleton init** | Class lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ Locks guard critical sections (check + modify together)
2. ✅ Account uses a re-entrant lock so `withdraw` can call `can_withdraw` safely
3. ✅ Double-checked locking for the Singleton
4. ✅ Notifications fire after state changes to keep critical sections short

---

## Demo Scenarios

### Scenario 1: Setup & Successful Login
```
✓ User registered: John Doe
✓ Account created: $1500
✓ Card issued: 4532123456789012
✓ Login successful → Session: LOGGED_IN
✓ Balance inquiry: $1500
```

### Scenario 2: Successful Withdrawal
```
Withdraw $300 → Balance: $1500 → $1200, ATM cash: $10000 → $9700
📧 Email: WITHDRAWAL successful: $300
```

### Scenario 3: Failed Withdrawal (Insufficient Funds)
```
Balance $200, attempt $500 → "Insufficient funds", balance unchanged
```

### Scenario 4: Daily Limit Exceeded
```
Daily limit $2000, already used $1800, attempt $300 (total $2100)
→ "Daily limit exceeded. Remaining: $200", transaction rejected
```

### Scenario 5: Card Blocking (3 Failed PIN Attempts)
```
Wrong PIN ×3 → card BLOCKED (30 min)
Correct PIN afterward → still blocked, login rejected
```

---

## Interview Q&A

### Basic Questions

**Q1: What is the main purpose of the ATMSystem?**

A: Singleton ensures one global instance managing all ATM operations across machines, users, accounts, sessions, and transactions — preventing conflicts and keeping state coherent.

**Q2: Why block a card after 3 failed PIN attempts?**

A: Security against brute-force attacks. A 30-minute block deters attackers while limiting inconvenience to legitimate users. Trade-off: convenience vs security.

**Q3: What is a session and why a 5-minute timeout?**

A: A session tracks the user's authenticated state. Inactivity timeout prevents unauthorized access if the user walks away; auto-logout blocks operations on an abandoned ATM.

**Q4: How are daily withdrawal limits enforced?**

A: Each account tracks `daily_withdrawal_used`. Before withdrawal it checks `used + amount ≤ $2000` and resets at midnight.

### Intermediate Questions

**Q5: How does the system prevent double-spending?**

A: A per-account re-entrant lock guards the check-and-debit so two concurrent withdrawals can't both read a stale balance: `with account.lock: validate; balance -= amount`.

**Q6: What happens if the ATM runs out of cash?**

A: `has_cash()` is checked before dispensing; if insufficient the transaction fails with "ATM has insufficient cash" and the balance is untouched.

**Q7: How does the Observer pattern handle notifications?**

A: Email/SMS/Push observers are notified independently on events, decoupling notifications from core logic so new channels need no core changes.

**Q8: How is session timeout checked?**

A: `is_expired()` compares now − last_activity to the timeout; if exceeded it marks the session EXPIRED. It's checked before each operation.

### Advanced Questions

**Q9: What thread-safety issues exist and how are they solved?**

A: Balance update races, session contention, and card-block state races. Solution: locks on shared resources (Account RLock, Machine lock, System lock).

**Q10: What security vulnerabilities exist in this demo?**

A: Plaintext PIN, no card encryption, no audit log, non-random session tokens, no login rate limiting. Fixes: hash PIN, encrypt card, audit all transactions, UUID/randomized tokens, rate limit.

---

## Scaling Q&A

### Q1: How to enforce daily limits across 100K users?

Each account tracks `daily_used` independently; shard users by ID across databases, each shard accounting independently. Watch for the midnight-reset synchronization spike.

### Q2: How to prevent double-withdrawal across distributed ATMs?

Pessimistic locking (lock account before withdrawal) or optimistic concurrency (version check + retry). Pessimistic = slower but simpler; optimistic = more retries under contention.

### Q3: How to scale to 10K concurrent sessions?

Move sessions to Redis for O(1) lookup by session_id; shard Redis for 100K+; periodically clean expired sessions.

### Q4: How to handle peak traffic (10K withdrawals/min)?

Replace the global lock with sharded per-account locks, process transactions in parallel, and make notifications asynchronous via a queue.

### Q5: How would you handle offline ATM mode (network down)?

Cache user/account data locally, debit and dispense locally, queue transactions, and replay on reconnect with conflict detection. Trade-off: consistency window vs availability.

### Q6: What if a card is reported stolen mid-session?

Subscribe to a card-block event stream; mark the card blocked globally (e.g., Redis) so the next ATM check rejects it.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through the login → session → transaction → logout lifecycle
- [ ] Explain card blocking after 3 failed PIN attempts
- [ ] Explain daily + per-transaction limit enforcement and midnight reset
- [ ] Explain how locks prevent double-spending and cash overdraft
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Mention thread safety in Singleton, withdraw, and dispense_cash
- [ ] Discuss security gaps (PIN hashing, encryption, audit logging)

---

**Ready for interview? Authenticate and withdraw! 🏧**
