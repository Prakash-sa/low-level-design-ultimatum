# 🤖 Vending Machine - Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Scope: selection, payment, dispense, refill |
| 5–15 | Architecture | Entities + state & event mapping |
| 15–35 | Core Entities | Product, Slot, Transaction, enums |
| 35–55 | Logic | select, compute price, pay, dispense, low‑stock, refill |
| 55–70 | Integration | Strategies + Observer events + summary |
| 70–75 | Demo & Q&A | Run scenarios & explain patterns |

## 🧱 Core Entities Cheat Sheet
Product(id, name)
Slot(id, product, quantity, base_price)
Transaction(id, slot, price, amount_paid, status)
Enums: MachineState(IDLE, ACCEPTING_PAYMENT, DISPENSING, OUT_OF_ORDER), TransactionStatus(INITIATED, PAID, DISPENSED, REFUNDED, FAILED)

## 🛠 Patterns Talking Points
Singleton: One controller managing all slots & transactions.
Strategy: PricingStrategy (fixed vs demand) & PaymentStrategy (coins/card/mobile).
Observer: Emits events for low_stock, slot_refilled, transaction_success, transaction_failed.
State: TransactionStatus guards dispensing only after PAID.
Factory: Helper methods create slots/transactions with generated IDs.

## 🎯 Demo Order
1. Setup: Create products, slots, observer.
2. Dynamic Pricing: Switch strategy; compare prices.
3. Purchase: Select → pay exact → dispense.
4. Low Stock & Refill: Deplete, trigger event, refill.
5. Failure & Refund: Underpay triggers fail & refund event.

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Success Checklist
- [ ] Price changes under demand strategy
- [ ] Low stock event fires at threshold
- [ ] Dispense only after PAID state
- [ ] Refund emitted on failure
- [ ] Refill resets quantity & emits slot_refilled
- [ ] Can explain each pattern mapping

## 💬 Quick Answers
Why Strategy? → Swap pricing/payment models without touching core transaction flow.
Why Observer? → Future integrations (telemetry, remote alerts) decoupled from logic.
Prevent invalid dispense? → Check TransactionStatus == PAID before dispensing.
Low stock detection? → Threshold (e.g., qty <= 2) triggers event for proactive restock.

## 🆘 If Behind
<20m: Implement Slot + Product + select/dispense flow only.
20–50m: Add Transaction + basic payment + events.
>50m: Show working purchase, narrate dynamic pricing & future payment types.

Stay concise; emphasize extensibility, safety, and clear state transitions.

