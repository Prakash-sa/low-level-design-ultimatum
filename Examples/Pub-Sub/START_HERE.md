# 📡 Pub-Sub Messaging System – Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Topics, publish, subscribe, retry |
| 5–15 | Architecture | Broker + strategies + events |
| 15–35 | Core Code | Message, Broker, Strategies, Subscriber |
| 35–55 | Reliability | Retry + dead-letter + backpressure |
| 55–70 | Demos | 5 scenarios show lifecycle |
| 70–75 | Q&A | Trade-offs & scaling story |

## 🧱 Entities Cheat Sheet
Message(id, topic, payload, status, attempts, ts)
Subscriber(id, handle(msg))
Publisher(broker)
Broker: topics -> queue[], subscribers[], metrics, strategy, retry_policy
DeliveryStrategy.execute(broker, topic)
RetryPolicy.should_retry(message)

Statuses: CREATED, QUEUED, DELIVERING, DELIVERED, FAILED, RETRY_SCHEDULED, DEAD_LETTER

## 🛠 Patterns
Singleton (Broker)
Strategy (Delivery, Retry)
Observer (Events)
State (Message status)
Factory (Message creation helper)

## 🎯 Demo Order
1. Basic publish/subscribe immediate delivery
2. Simulated failure + retry success
3. Multiple subscribers broadcast
4. Swap to batched strategy + flush
5. Backpressure + dead-letter summary

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Checklist
- [ ] Redelivery increments attempts
- [ ] Retry stops at max attempts
- [ ] Dead-letter recorded
- [ ] Strategy swap retains queued messages
- [ ] Events printed

## 💬 Quick Answers
Why clear separation? → Broker centralizes routing, strategies keep flexibility.
Why strategy? → Swap latency vs throughput behavior dynamically.
How scaling? → Partition topics, distributed broker cluster, persistence log.
Why dead-letter? → Prevent infinite retry loops, allow manual handling.
Backpressure response? → Emit event; either reject publishes or drop oldest.

## 🆘 If Behind
<20m: Implement Broker + immediate delivery + subscribe.
20–50m: Add retry + metrics + batched strategy.
>50m: Backpressure + dead-letter + events + demos.

Focus on lifecycle clarity and extensibility narrative.
