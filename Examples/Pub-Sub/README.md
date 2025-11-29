# 📡 Pub-Sub Messaging System

Designing a lightweight publish–subscribe messaging system (single-process simulation) showcasing core distributed messaging concepts using the same structured format as the Airline Management System example.

---
## 🎯 Goal
Deliver topic-based messages from publishers to subscribers with pluggable delivery strategies (immediate vs batched), retry handling, backpressure simulation, and observable events.

---
## 🧱 Core Building Blocks
| Component | Responsibility | Patterns |
|-----------|----------------|----------|
| `Message` | Payload + metadata (id, timestamp, attempts) | Value Object |
| `Subscriber` | Receives messages (callback) | Strategy (user logic) |
| `Publisher` | Facade to broker to publish | Facade |
| `Broker` | Routes, queues, retries, metrics | Singleton, Observer, Strategy, State |
| `DeliveryStrategy` | Defines dispatch mechanics | Strategy |
| `RetryPolicy` | Determines retry timing/limits | Strategy |
| `Event` | Emitted lifecycle notifications | Observer |

---
## 🕸 Relationships
Broker holds: topics -> queues, subscribers, delivery strategy, metrics.
Publisher delegates to broker.publish(topic, message).
Broker dispatches periodically or instantly based on strategy.
Subscribers implement `handle(message)` and may raise errors to trigger retries.

---
## 🔄 Message Lifecycle
CREATED → QUEUED → DELIVERING → DELIVERED | FAILED (→ RETRY_SCHEDULED → QUEUED) | DEAD_LETTER.

---
## 🧠 Key Patterns
- Singleton Broker: Single coordination point.
- Strategy: Delivery (`ImmediateDeliveryStrategy`, `BatchedDeliveryStrategy`), Retry policy.
- Observer: Event emission (`message_enqueued`, `delivered`, `failed`, `dead_letter`, `subscriber_added`, `strategy_swapped`).
- State: Message status transitions controlled centrally.
- Factory (implicit): Message creation via helper.

---
## ⚙ Delivery Strategies
1. Immediate: Dispatch as soon as enqueued.
2. Batched (size or time threshold): Accumulate then flush.
Switching strategy should not lose queued messages.

---
## 🛡 Reliability & Backpressure
- Retry with capped attempts and exponential-ish backoff simulation.
- Dead-letter queue for permanent failures.
- Backpressure: max queue length triggers `backpressure` event and refusal or drop policy.

---
## 📊 Metrics Tracked
- Published count per topic
- Delivered / Failed / Dead-letter counts
- Average latency (simulated timestamp delta)
- Subscriber lag (queue length)

---
## 🧪 Demo Scenarios
1. Setup + basic publish + subscribe
2. Failure & retry leading to success
3. Multiple subscribers + broadcast behavior
4. Strategy swap from batched to immediate
5. Backpressure & dead-letter handling summary

---
## 🗂 Files
- `START_HERE.md` – 5‑minute reference
- `75_MINUTE_GUIDE.md` – deep dive interview flow
- `INTERVIEW_COMPACT.py` – runnable compact implementation

Run demos:
```bash
python3 INTERVIEW_COMPACT.py
```

---
## 📝 Talking Points
- Why Pub-Sub vs direct calls? Decoupling producers/consumers, scalability.
- Strategy vs hard-coded delivery loops: enables tuning latency/throughput trade-offs.
- Retry vs idempotency: highlight need for idempotent subscriber handlers.
- Backpressure design: drop, block, or overflow queue – trade-offs.
- Extensions: persistence, partitioning, ordering guarantees, distributed broker, exactly-once semantics.

---
## 🚀 Future Enhancements
- Persistent log (append-only) with replay
- Partition + consumer groups (Kafka-style)
- At-least vs exactly-once semantics (dedup keys)
- Observability integration (tracing/spans)
- Circuit breaker around slow subscribers

---
## ✅ Interview Closure
Summarize: clear lifecycle, extensible strategies, robust retry path, events for instrumentation, ready path to scaling horizontally.
