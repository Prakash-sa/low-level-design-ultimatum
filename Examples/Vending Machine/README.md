# 🤖 Vending Machine System – 75 Minute Interview Overview

Smart vending machine with product slots, dynamic pricing, multi‑payment, transaction lifecycle, low‑stock alerts, and refill operations. Mirrors Airline example structure: clear entities, patterns, timeline, demo scenarios, and extensibility talking points.

**Scale (Assumed)**: 1–5 machines, 20–50 slots each, 100–300 daily transactions.  
**Focus**: Inventory lifecycle (stock → selection → payment → dispense → decrement/refill) + design patterns for extensibility.

---

## Core Domain Entities
| Entity | Purpose | Relationships |
|--------|---------|--------------|
| **Product** | Consumable item descriptor | Referenced by Slot |
| **Slot** | Holds product, quantity, base price | Owned by VendingMachineSystem |
| **Transaction** | Purchase attempt with lifecycle | Links Slot + payment amount |
| **PricingStrategy** | Dynamic price computation | Injected into system |
| **PaymentStrategy** | Authorize & capture payment | Chosen per transaction |
| **Observer** | Receives machine events | Subscribed to system |

---

## Design Patterns Implemented
| Pattern | Purpose | Example |
|---------|---------|---------|
| **Singleton** | Single machine controller instance | `VendingMachineSystem.get_instance()` |
| **Strategy** | Pluggable pricing or payment rules | `FixedPricing` vs `DemandPricing`, `CoinPayment` |
| **Observer** | Event notifications | `ConsoleObserver` for low stock, dispense events |
| **State** | Transaction & machine states | `TransactionStatus` (INITIATED→PAID→DISPENSED) |
| **Factory** | Object creation helpers | `add_slot()` assigns IDs, creates Slot |

Optional future patterns: Command for refund workflow, Decorator for caching price lookups.

---

## 75-Minute Timeline
| Time | Phase | What to Code |
|------|-------|--------------|
| 0–5  | Requirements | Clarify scope (refunds? multi-currency?) |
| 5–15 | Architecture | Sketch entities + pattern mapping |
| 15–35 | Core Entities | Product, Slot, Transaction, enums |
| 35–55 | Business Logic | select, price, pay, dispense, refill, events |
| 55–70 | Integration | Strategies, Observers, machine summary |
| 70–75 | Demo & Q&A | Run INTERVIEW_COMPACT.py demos |

---

## Demo Scenarios (5)
1. Setup: Products & slots creation
2. Dynamic Pricing: Switch strategy; view price difference
3. Successful Purchase: Select → pay → dispense
4. Low Stock & Refill: Consume to threshold then refill
5. Failure & Refund: Insufficient payment triggers failure & refund

Run all demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---

## Interview Checklist
- [ ] Can articulate each pattern & domain mapping
- [ ] Know transaction lifecycle statuses
- [ ] Can explain dynamic pricing factors (remaining quantity, demand multiplier)
- [ ] Understand low‑stock threshold & event emission
- [ ] Can discuss payment strategy swap (coins vs card vs wallet)
- [ ] Provide scaling ideas (telemetry, remote monitoring, predictive restock)

---

## Key Concepts to Explain
**Dynamic Pricing Strategy**: Adjusts effective price based on remaining inventory (scarcity) or time windows; pluggable so machine logic stays stable.

**Observer Events**: `slot_refilled`, `low_stock`, `transaction_success`, `transaction_failed`, `dispensed` enable analytics & remote alerting.

**Transaction State Management**: Guards invalid operations (cannot dispense before PAID); explicit enum transitions make reasoning clear.

**Refund Handling**: On failure we generate refund amount and emit event; later could integrate with external payment processor.

---

## File Purpose
| File | Purpose |
|------|---------|
| `README.md` | High-level overview & checklist |
| `START_HERE.md` | Rapid timeline & talking points |
| `75_MINUTE_GUIDE.md` | Deep dive design, UML, Q&A |
| `INTERVIEW_COMPACT.py` | Working implementation + demos |

---

## Tips for Success
✅ Keep pricing & payment logic out of core entities (Strategy)  
✅ Emit events early; show extensibility  
✅ Narrate trade-offs (precision of change calculation, concurrency)  
✅ Clarify exclusions (nutrition info, remote firmware updates) to stay focused  
✅ Mention reliability (sensor errors → OUT_OF_ORDER state) without overbuilding

---

See `75_MINUTE_GUIDE.md` for full breakdown; run `INTERVIEW_COMPACT.py` for demonstration; use `START_HERE.md` for quick verbal prompts.

