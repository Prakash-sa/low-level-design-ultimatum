# 📚 Library Management System - 75 Minute Interview Guide

## Your 3 Main Resources
1. **README.md** - Complete reference guide covering all design patterns (Singleton, Strategy, Factory, Observer, State, Decorator) and SOLID principles with code examples
2. **75_MINUTE_GUIDE.md** - Step-by-step implementation timeline with exact code for each phase
3. **INTERVIEW_COMPACT.py** - Single runnable file with 5 complete demo scenarios

## 75-Minute Implementation Timeline

| Time | Phase | What to Implement | Lines |
|------|-------|-------------------|-------|
| 0-5 min | Requirements | Clarify: 3 member types, book limit rules, fine system | 0 |
| 5-15 min | Architecture | Sketch: Singleton, Observer, Strategy patterns | 0 |
| 15-25 min | Phase 1 | Create enums (BookStatus, CheckoutStatus, MemberType) | 50 |
| 25-40 min | Phase 2 | Build Book & Member classes with type hierarchies | 120 |
| 40-55 min | Phase 3 | Implement Checkout, Search strategies, Notifications | 200 |
| 55-70 min | Phase 4 | Complete LibrarySystem Singleton with observers | 350 |
| 70-75 min | Demo | Show 5 demo scenarios, explain patterns | 480 |

## Implementation Phases with Milestones

### Phase 1: Enumerations (5 minutes)
```python
- BookStatus: AVAILABLE, CHECKED_OUT, RESERVED, LOST
- CheckoutStatus: ACTIVE, RETURNED, OVERDUE
- MemberType: STUDENT (5 books, 14 days), FACULTY (10 books, 21 days), PREMIUM (15 books, 30 days)
```
**Milestone**: Type system established

### Phase 2: Book & Member Classes (15 minutes)
```python
- Book: ISBN, title, author, total copies, available copies
- Book methods: can_checkout(), checkout(), return_book()
- Member base class + 3 subclasses (StudentMember, FacultyMember, PremiumMember)
- Each member type has checkout_limit and checkout_period
```
**Milestone**: Core entities working

### Phase 3: Checkout, Search & Notifications (15 minutes)
```python
- Checkout: ID, member, book, due date, return date, fine calculation
- SearchStrategy: ISBN search, Title search, Author search
- Observer pattern: EmailNotifier, SMSNotifier
- Fine calculator: Based on member type ($0.50/day for student, $0.25/day for faculty, $0.10/day for premium)
```
**Milestone**: Complex business logic implemented

### Phase 4: LibrarySystem Singleton (15 minutes)
```python
- LibrarySystem Singleton: 10K books, 1K members
- add_book(), register_member(), checkout_book(), return_book()
- Search strategy pattern: Switch between ISBN/Title/Author search
- Observer notifications: Email and SMS on checkout/return/overdue
```
**Milestone**: Complete system operational

### Phase 5: Demo & Edge Cases (5 minutes)
```python
- Demo 1: Add books to inventory
- Demo 2: Register members (different types)
- Demo 3: Checkout books (respect limits)
- Demo 4: Search books (multiple strategies)
- Demo 5: Return books & calculate fines
```

## Demo Scenarios to Show

### Demo 1: Adding Books to Inventory
- Add "Python Basics" (ISBN: 978-0-13-110362-7) with 5 copies
- Add "Data Science" (ISBN: 978-1-491-91205-8) with 3 copies
- Add "Web Dev" (ISBN: 978-0-596-52068-7) with 4 copies
- Show inventory counts and available status

### Demo 2: Registering Different Member Types
- Register Alice as StudentMember (5 book limit, 14-day checkout)
- Register Prof. Bob as FacultyMember (10 book limit, 21-day checkout)
- Register Charlie as PremiumMember (15 book limit, 30-day checkout)
- Show welcome notifications via email and SMS

### Demo 3: Checkout Books & Respect Limits
- Alice checks out "Python Basics" (StudentMember: 1/5 books)
- Prof. Bob checks out "Data Science" (FacultyMember: 1/10 books)
- Show due dates differ (14 days vs 21 days vs 30 days)
- Try to exceed limits → show rejection message

### Demo 4: Searching Books
- ISBN search for "978-0-13-110362-7" → find Python Basics
- Title search for "Data Science" → find exact match
- Author search for "John Doe" → find all books by author
- Show search strategy being changed and reused

### Demo 5: Returning Books & Fine Calculation
- Alice returns "Python Basics" on time → $0 fine
- Prof. Bob returns "Data Science" 5 days late → $1.25 fine (5 × $0.25/day)
- Charlie returns book 10 days late → $1.00 fine (10 × $0.10/day for premium)
- Show fine notifications via email and SMS

## Talking Points (What Interviewers Want to Hear)

### Design Pattern Discussion
- **Singleton**: "Why LibrarySystem is Singleton" → ensures one library instance, consistent member/book data
- **Strategy**: "Search algorithms" → easily swap ISBN/Title/Author search without changing checkout code
- **Factory**: "Member and Book creation" → encapsulates creation logic, extensible for new types
- **Observer**: "How members get notified" → loose coupling, can add more notification channels (Slack, Discord)
- **State**: "Checkout states" → clear transition from ACTIVE → RETURNED or OVERDUE
- **Decorator**: "Premium member benefits" → reserved books, extended checkout periods, lower fines

### SOLID Principles
- **Single Responsibility**: Member handles member state, Checkout handles checkout logic
- **Open/Closed**: Add new member types (CorporateMember) without modifying Member base class
- **Liskov Substitution**: StudentMember, FacultyMember, PremiumMember all substitute for Member
- **Interface Segregation**: SearchStrategy depends only on search interface
- **Dependency Inversion**: LibrarySystem depends on Member/Book abstractions, not concrete types

### Architecture Highlights
- Member types encapsulate business rules (limits, periods, fines)
- Search strategies allow flexible querying without branching logic
- Observer pattern enables real-time notifications
- Fine calculation logic is isolated and testable
- Book inventory is properly managed with concurrent access considerations

## Answer to Follow-Up Questions

### "What if a member exceeds checkout limit?"
A: Check total_checked_out < member.checkout_limit before allowing checkout.

### "How do you calculate fines for overdue books?"
A: (days_late) × (fine_per_day based on member type). Shown in Demo 5.

### "Why different checkout periods for different member types?"
A: Business rule - students (14 days) vs faculty (21 days) vs premium (30 days).

### "How does search strategy pattern help?"
A: Switch between ISBN/Title/Author without changing checkout code. Shows flexibility.

### "What if two members want same book?"
A: Implement reservation system (RESERVED status). First-come-first-served.

### "How does notification system scale?"
A: Observer pattern - add more observers (SlackNotifier, PushNotifier) without changing core code.

### "What about concurrent checkouts?"
A: Mention locks/queues for thread safety. Show single-threaded for interview.

### "How do you handle lost books?"
A: Mark as LOST status, member pays replacement fee + fine.

## Debugging Tips

### "Member checkout rejected but has available books"
- Check: Is member's checkout_limit exceeded?
- Check: Are they in good standing (no overdue books)?
- Verify: Book has available copies (not all checked out)

### "Fine calculation wrong"
- Check: Is days_late calculated correctly? (return_date - due_date)
- Check: Is member type fine_per_day correct? (0.50/0.25/0.10)
- Verify: Calculation is: days_late × fine_per_day

### "Search not finding book"
- Check: Is search strategy correct? (ISBN/Title/Author)
- Check: Is book in library inventory (added via add_book)?
- Verify: Search terms match exactly (case-sensitive?)

### "Notifications not sending"
- Check: Are observers registered? (add_observer called)
- Check: Is notify_all() called after checkout/return?
- Verify: Observer list is not empty

### "Member limit not enforced"
- Check: Is checkout_limit being checked? (total_checked_out < limit)
- Check: Are you counting only ACTIVE checkouts?
- Verify: Limit is correct for member type

## Emergency Options (If Stuck)

### Stuck on Enums (5 min in)?
→ Skip enums, hardcode status strings, add enums later

### Stuck on Member Types (20 min in)?
→ Single Member class with all rules, subclass later

### Stuck on Checkout Logic (35 min in)?
→ Simple checkout without fine calculation, add fines later

### Stuck on Search (50 min in)?
→ Single search method, strategy pattern later

### Stuck on Notifications (60 min in)?
→ Print statements instead of observer pattern

### Running out of time (70 min in)?
→ Implement 1-2 demos fully, explain others verbally with pseudocode

## Pro Tips for Maximum Impact

1. **Start with Member type hierarchy** - Show StudentMember/FacultyMember/PremiumMember first
2. **Explain business rules clearly** - "Students get 5 books for 14 days"
3. **Use search strategy as pattern example** - Easy to switch, shows flexibility
4. **Show fine calculation** - Demonstrate math: 5 days late × $0.25 = $1.25
5. **Test each demo** - Run all 5 demos to show system works end-to-end
6. **Mention scalability** - "With 1K members and 10K books, efficient searching matters"
7. **Ask clarifying questions** - "Should we support book reservations?" (shows thinking)
8. **Handle edge cases** - Member at limit, book out of stock, overdue penalties

## Success Criteria

✅ All 3 member types work (StudentMember, FacultyMember, PremiumMember)
✅ Checkout limits enforced (5/10/15 based on type)
✅ Checkout periods correct (14/21/30 days)
✅ Fine calculation working (days_late × fine_per_day)
✅ Search strategies implemented (ISBN, Title, Author)
✅ Observer pattern working (notifications sent)
✅ At least 4 demos run without errors
✅ Can explain 2 design patterns and 2 SOLID principles
✅ Handles edge cases (exceed limit, book out of stock, fine calculation)
✅ Code is clean, readable, and follows naming conventions

---

**Quick Start**: Run `python3 INTERVIEW_COMPACT.py` to see all 5 demos in action!
