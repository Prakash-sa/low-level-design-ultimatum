# 🏧 ATM - Interview Reference Guide

## System Overview
Multi-user ATM system supporting card-based authentication, balance inquiries, cash withdrawal/deposit with limits, session management, and concurrent access. Core focus: Design patterns, thread-safety, state management, and financial constraints.

---

## Core Entities & Attributes

| Entity | Key Attributes | Responsibilities |
|--------|--------------|------------------|
| **User** | user_id, name, cards[], accounts[] | Manages user profile, linked cards, and accounts |
| **Card** | card_number, pin, status, failed_attempts, blocked_until | Card validation, PIN verification, brute-force protection |
| **Account** | balance, daily_limit, transaction_limit, transactions[] | Balance management, transaction history, limit enforcement |
| **Transaction** | transaction_id, type, amount, status, created_at | Records financial operations with status tracking |
| **Session** | session_id, user, state, last_activity, timeout_duration | User state management, auto-logout after inactivity |
| **ATMMachine** | machine_id, location, cash_balance, sessions[] | Cash management, session handling per location |
| **ATMSystem** | users, accounts, machines, observers | Central coordinator (Singleton pattern) |

---

## Design Patterns & Implementation

### Pattern 1: Singleton (System Coordinator)
**Class**: `ATMSystem`
**Purpose**: Ensure single global instance managing all ATM operations
```python
class ATMSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
```
**Benefits**: Prevents multiple instances with conflicting state

### Pattern 2: Strategy (Transaction Types)
**Classes**: `TransactionType` enum with WITHDRAWAL/DEPOSIT/BALANCE_INQUIRY
**Purpose**: Different logic per transaction type
**Implementation**: In `process_transaction()`, conditionally execute based on type
**Benefits**: Easy to add new transaction types without modifying core code

### Pattern 3: Observer (Notifications)
**Classes**: `TransactionObserver` (abstract) → `EmailNotifier`, `SMSNotifier`, `PushNotifier`
**Purpose**: Decouple notifications from core logic
**Implementation**: Register observers, notify all on transaction completion
**Benefits**: Multiple systems independently notified without tight coupling

### Pattern 4: State (Session Lifecycle)
**Classes**: `SessionState` enum (LOGGED_OUT, LOGGED_IN, SESSION_LOCKED, EXPIRED)
**Purpose**: Manage clear state transitions
**Implementation**: Check `session.is_expired()` before each operation
**Benefits**: Prevent invalid operations during wrong states

### Pattern 5: Factory (Transaction Creation)
**Method**: `process_transaction()` creates Transaction based on type
**Purpose**: Centralized creation with validation
**Benefits**: Consistent transaction initialization

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S - Single Responsibility** | Card handles PIN, Account handles balance, Session manages timeout |
| **O - Open/Closed** | Add new transaction types via enum; new observers without modifying system |
| **L - Liskov Substitution** | All observers implement same interface; Email/SMS/Push interchangeable |
| **I - Interface Segregation** | TransactionObserver has single `update()` method; focused APIs |
| **D - Dependency Inversion** | System depends on Observer abstraction, not concrete notifiers |

---

## Key Business Logic

### Authentication Flow
```
1. Card validation (card exists, not expired/blocked)
2. PIN verification (up to 3 attempts)
3. Block card for 30 min after 3 failures
4. Create session with 5-minute timeout
5. Notify observers of login
```

### Withdrawal Flow
```
1. Session validity check (not expired)
2. Limit validation (per-transaction ≤ $500, daily ≤ $2000)
3. Balance check (sufficient funds)
4. ATM cash check (machine has cash)
5. Deduct from account
6. Dispense cash
7. Notify observers
```

### Session Timeout
```
1. Check elapsed time since last activity
2. If > 5 minutes: mark session as EXPIRED
3. Prevent further operations
4. Clean up session resources
```

---

## Thread-Safety Implementation

**Protected Sections**:
- `Account` balance updates (with `threading.Lock()`)
- `ATMMachine` cash balance updates (with `threading.Lock()`)
- `ATMSystem` user/machine registration (with `threading.Lock()`)

**Pattern**:
```python
with self.lock:
    # Atomic operation
    self.balance -= amount
    self.daily_withdrawal_used += amount
```

---

## Edge Cases Handled

| Case | Solution |
|------|----------|
| Card blocked after 3 PIN fails | Block for 30 minutes, prevent login |
| Daily limit exceeded | Check remaining daily allocation before withdrawal |
| ATM cash insufficient | Check machine cash, fail withdrawal if insufficient |
| Session timeout mid-operation | Check `is_expired()` at operation start |
| Concurrent withdrawals | Thread locks prevent race conditions |
| Negative amounts | Validation rejects amount ≤ 0 |

---

## Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────┐
│         ATM System (Singleton)          │
│  Coordinates all operations globally    │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│ Users  │ │Accounts  │ │ Machines │
└────────┘ └──────────┘ └──────────┘
    │        │              │
    ▼        ▼              ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│ Card   │ │Transaction│ │Session   │
└────────┘ └──────────┘ └──────────┘
    
Observer Pattern:
┌─────────────────────────────────┐
│  TransactionObserver (Abstract) │
└────────┬────────────────────────┘
         │
    ┌────┼────┬─────────┐
    ▼    ▼    ▼         ▼
┌─────┐ ┌──┐ ┌────┐ ┌────────┐
│Email│ │SMS│ │Push│ │Custom  │
└─────┘ └──┘ └────┘ └────────┘
```

---

## Demo Scenarios Included

1. **Setup & Login**: User registration, account creation, card issuance, successful login
2. **Successful Withdrawal**: $300 withdrawal with balance and ATM cash updates
3. **Failed Withdrawal**: Insufficient funds error handling
4. **Daily Limit**: Daily limit tracking and enforcement
5. **Card Blocking**: 3 failed PIN attempts trigger 30-minute block

---

## Interview Tips

**What to Emphasize**:
- Singleton ensures single system instance without conflicts
- Thread locks protect concurrent access to shared resources
- Observer pattern allows flexible notification systems
- State machine prevents invalid operations
- Daily limit reset at midnight (critical for banking)
- Card blocking prevents brute-force attacks

**Questions to Prepare For**:
- "How do you handle concurrent users accessing same account?"
- "What prevents double-spending?"
- "How would you scale to 1000 ATMs?"
- "How does session timeout work?"
- "Why use Observer pattern for notifications?"

**Potential Improvements**:
- Audit logging of all transactions
- Transaction rollback on failure
- Distributed ATM system with shared database
- PIN stored as salted hash (not plaintext)
- Rate limiting on login attempts
- Multi-factor authentication

---

## Files in This System

- **75_MINUTE_GUIDE.md**: Complete 75-minute implementation timeline with full code
- **INTERVIEW_COMPACT.py**: Working executable implementation with 5 demo scenarios
- **README.md**: This reference guide (patterns, SOLID, edge cases)
- **START_HERE.md**: 5-minute quick reference for rapid preparation

---

## Quick Reference

**Key Limits**:
- PIN attempts: 3 max
- Card block duration: 30 minutes
- Session timeout: 5 minutes
- Transaction limit: $500 max
- Daily limit: $2000 max
- Concurrent users: 1000+

**Key Classes**: Card, User, Account, Transaction, Session, ATMMachine, ATMSystem

**Key Patterns**: Singleton, Strategy, Observer, State, Factory

**Key Entities**: Users, Cards, Accounts, Transactions, Sessions, Machines

---

## Success Checklist

✅ Understand entity relationships and responsibilities
✅ Explain each design pattern and why it's used
✅ Discuss thread-safety mechanisms
✅ Handle edge cases (limits, blocking, timeout)
✅ Explain SOLID principles in context
✅ Discuss scaling to 1000 concurrent users
✅ Talk through security concerns
✅ Run demo scenarios successfully
