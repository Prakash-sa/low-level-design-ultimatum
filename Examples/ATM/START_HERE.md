# 🏧 ATM - 5 Minute Quick Start

## ⏱️ 75-Minute Interview Breakdown

| Time | What to Do | Duration |
|------|-----------|----------|
| 0-5 min | Requirements clarification + architecture | 5 min |
| 5-15 min | Design patterns + core entities overview | 10 min |
| 15-35 min | Card, User, Account, Transaction, Session classes | 20 min |
| 35-55 min | ATMMachine, ATMSystem, authentication, transactions | 20 min |
| 55-70 min | Observer pattern, edge cases, thread-safety | 15 min |
| 70-75 min | Run demos, explain design decisions | 5 min |

---

## 🎯 Core Entities (Memorize These)

```
User ──has──> Card ──links──> Account
                                 │
                            Transaction
                                 │
                              Session
                                 │
                            ATMMachine
                                 │
                            ATMSystem (Singleton)
```

**Card**: Validates PIN, blocks after 3 failures
**Account**: Manages balance, enforces limits (daily $2000, per-transaction $500)
**Session**: Tracks login state, auto-logout after 5 minutes inactivity
**ATM Machine**: Dispenses cash, manages local sessions
**ATMSystem**: Singleton coordinator for all operations

---

## 🔑 5 Design Patterns

### 1. **Singleton** (ATMSystem)
"One global instance coordinates all operations"
```python
# Thread-safe: _instance, _lock, __new__()
system = ATMSystem()  # Always same instance
```

### 2. **Strategy** (TransactionType)
"Different logic per transaction type"
```python
if trans_type == TransactionType.WITHDRAWAL:
    # Withdraw logic
elif trans_type == TransactionType.DEPOSIT:
    # Deposit logic
```

### 3. **Observer** (Notifications)
"Decouple notifications from core system"
```python
system.add_observer(EmailNotifier())
system.add_observer(SMSNotifier())
# Automatically notified on transactions
```

### 4. **State** (SessionState)
"Clear state transitions prevent invalid ops"
```python
session.state = SessionState.LOGGED_IN
if session.is_expired():  # Check before operations
    return False, "Session expired"
```

### 5. **Factory** (Transaction Creation)
"Centralized creation logic"
```python
transaction = Transaction(trans_id, account_id, type, amount)
```

---

## 💬 Key Talking Points

**Authentication**: "Card is validated, PIN verified (3 attempts max), card blocked 30 min if failed, session created with 5-min timeout"

**Withdrawal**: "Check session valid → Check daily limit ($2000) → Check per-transaction limit ($500) → Check balance → Check ATM cash → Deduct & dispense → Notify observers"

**Thread-Safety**: "Each critical section protected by lock: `with self.lock: [atomic operation]`. Prevents double-debit or over-dispensing"

**Limits**: "Daily resets at midnight. Tracked per account. Cannot exceed $2000/day or $500/transaction"

**Card Blocking**: "After 3 failed PIN attempts, card blocked for 30 minutes. Prevents brute-force attacks"

**Session Timeout**: "Check elapsed time since last activity. If > 5 minutes, mark as EXPIRED. Prevents unauthorized access after user leaves"

---

## ✅ Success Criteria (Checklist During Interview)

- [ ] Explain all 5 design patterns
- [ ] Show thread-safe account updates with locks
- [ ] Handle card blocking (3 failed attempts)
- [ ] Implement daily limit tracking (reset at midnight)
- [ ] Manage session timeout (5 minutes)
- [ ] Observer pattern for notifications (Email, SMS, Push)
- [ ] Run all 5 demos successfully
- [ ] Explain SOLID principles in context
- [ ] Discuss scaling to 1000 concurrent users
- [ ] Identify security vulnerabilities (PIN plaintext, no audit logging, etc.)

---

## 🚀 Quick Commands

```bash
# Run 5 working demos (2 minutes)
python3 INTERVIEW_COMPACT.py

# Read 75-minute guide (15 minutes deep dive)
cat 75_MINUTE_GUIDE.md

# Reference patterns (quick lookup)
grep -A 5 "class.*Observer" INTERVIEW_COMPACT.py
```

---

## 🎬 5 Demo Scenarios

### Demo 1: Setup & Login ✅
- Register user, create account, issue card
- Login successfully
- Check balance
- Logout

### Demo 2: Successful Withdrawal ✅
- Login
- Withdraw $300
- Show new balance and ATM cash updates
- Logout

### Demo 3: Failed Withdrawal (Insufficient Funds) ✅
- Login
- Attempt $500 withdrawal (balance only $200)
- Show error message
- Balance unchanged

### Demo 4: Daily Limit Exceeded ✅
- Already withdrew $1800 (of $2000 limit)
- Attempt $300 more withdrawal (total $2100)
- Show error: "Daily limit exceeded. Remaining: $200"

### Demo 5: Card Blocking (3 Failed PIN Attempts) ✅
- Wrong PIN attempt 1 (failed_attempts = 1)
- Wrong PIN attempt 2 (failed_attempts = 2)
- Wrong PIN attempt 3 (card blocked, blocked_until = now + 30 min)
- Correct PIN but card blocked → login fails

---

## 🔐 Security Considerations

**Vulnerabilities** (to discuss):
- PIN stored as plaintext (should be hashed)
- No card encryption
- No audit logging
- No rate limiting on login
- Session tokens not random (use UUID)
- No TLS for communication

**Mitigations**:
- Hash PIN with salt
- Encrypt card data
- Log all transactions
- Rate limit login attempts
- Use random session IDs
- Enable HTTPS/TLS

---

## 📈 Scaling Discussion

**Current**: In-memory, single machine
**Problems**: 
- Lost on restart
- 1000 concurrent users = memory limits
- No persistence

**Solutions**:
- Database for accounts/transactions (SQL/NoSQL)
- Redis for distributed sessions
- Message queue for async notifications
- API service layer
- Load balancer across ATMs
- Replicated ATMSystem instances

---

## 🆘 If You Get Stuck

**Early phase (< 15 min)**:
- Focus on entities first: Card, User, Account, Transaction, Session
- Singleton pattern can come later

**Mid phase (15-40 min)**:
- Implement basic business logic (withdrawal, deposit)
- Don't worry about thread-safety initially

**Late phase (> 40 min)**:
- Show 1-2 working demos
- Explain remaining patterns verbally
- Discuss scaling/security

---

## 🎓 Learning Path

1. **Understand requirements** (What needs to work?)
   - Authentication with PIN
   - Balance checks
   - Withdrawal/deposit with limits
   - Session timeout

2. **Design entities** (What data needs to be tracked?)
   - User, Card, Account, Transaction, Session
   - Each has specific responsibilities

3. **Implement patterns** (How to keep code clean?)
   - Singleton for global system
   - Observer for notifications
   - State for session lifecycle

4. **Handle concurrency** (How to prevent race conditions?)
   - Thread locks on shared state
   - Atomic operations

5. **Run demos** (Does it actually work?)
   - 5 scenarios showing all patterns in action

---

## 💡 Talking Through Demo

When running demo, explain:

1. **Why Singleton**: "One ATMSystem instance manages all operations. No conflicts with multiple instances."

2. **Why Observer**: "We notify multiple systems (Email, SMS) without coupling them to core logic. Easy to add new notifiers."

3. **Why State Machine**: "SessionState enum ensures valid transitions. Can't process transactions on expired/locked sessions."

4. **Why Thread Locks**: "Account balance is shared resource. Lock prevents double-debit when two users withdraw simultaneously."

5. **Why Strategy**: "Different transaction types (withdrawal/deposit) have different logic, but same processing flow."

---

## 📝 Interview Flow Example

**Interviewer**: "Design an ATM system"

**You**: "I'll start with requirements: authentication, balance checks, withdrawal/deposit with daily limits, session timeout, concurrent access. (2 min)

I'll use 5 design patterns: Singleton for global coordination, Strategy for transaction types, Observer for notifications, State for session lifecycle, Factory for transaction creation. (2 min)

Here are 5 core entities [draw diagram]: User, Card, Account, Transaction, Session. (1 min)

Let me implement Card validation with PIN and blocking... [write code] (10 min)

Now Account with daily limits and thread-safe balance... (10 min)

Session with timeout checking... (5 min)

ATMSystem as Singleton coordinator... (10 min)

Observer pattern for notifications... (10 min)

Let me run demo scenarios... [execute] (5 min)

Any questions about design decisions?" (Rest of time)
```

---

## 🎯 Final Checklist

Before interview:
- [ ] Read 75_MINUTE_GUIDE.md (understand timeline)
- [ ] Run INTERVIEW_COMPACT.py (see it working)
- [ ] Memorize 5 patterns (Singleton, Strategy, Observer, State, Factory)
- [ ] Know the edge cases (card blocking, daily limits, ATM cash, session timeout)
- [ ] Practice explaining each pattern
- [ ] Understand thread-safety with locks
- [ ] Can draw entity diagram from memory
- [ ] Can discuss scaling to 1000 users

---

## 🏁 Ready to Go!

You have everything needed:
- ✅ Complete implementation (INTERVIEW_COMPACT.py)
- ✅ 75-minute timeline (75_MINUTE_GUIDE.md)
- ✅ Working demos (5 scenarios)
- ✅ Pattern explanations
- ✅ Edge case handling
- ✅ Thread-safety discussion
- ✅ Scaling analysis

**Start with**: Run demo → Read guide → Understand patterns → Practice explaining

**Good luck! 🚀**
