# Pub-Sub — 75-Minute Interview Guide

## Quick Start Overview

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


## 75-Minute Guide

## 1. Problem Framing (0–5)
Build an in-memory topic-based publish–subscribe broker supporting multiple subscribers per topic, delivery strategies, retry, basic backpressure, and observability.

Must:
- Publish messages to topics
- Register/deregister subscribers
- Deliver messages (immediate or batched)
- Retry failed deliveries up to cap
- Dead-letter storage after exhaustion
- Metrics + events emission

Stretch:
- Backpressure handling (reject or drop)
- Strategy hot-swap
- Delivery latency simulation

## 2. Requirements & Constraints (5–10)
Functional:
- At-least-once delivery (maybe duplicates on retry)
- Non-blocking publish (quick enqueue)
- Broadcast semantics (each subscriber receives a copy)

Non-Functional:
- Extensible strategies
- Observable events (diagnostics)
- Deterministic retry behavior

Assumptions:
- Single-threaded process (no real concurrency)
- Limited memory; queue size bounded

## 3. Domain Model (10–18)
Entities:
- Message(id, topic, payload, status, attempts, timestamp)
- Broker(topics, subscribers, queues, strategy, retry_policy, metrics)
- Subscriber(id, handle())
- DeliveryStrategy Interface
- RetryPolicy Interface
- DeadLetterStore(list)

Relationships:
Broker → (topic -> queue[Message])
Broker → subscribers[topic] -> Subscriber
Strategy invoked per topic or globally.

## 4. Patterns (18–26)
Singleton Broker: simplified global access.
Strategy: swap delivery mechanism (immediate vs batch).
Observer: events for instrumentation.
State: message status transitions enforced centrally.
Factory: message creation helper ensures IDs.

## 5. Message Lifecycle (26–32)
CREATED → QUEUED → (DELIVERING → DELIVERED) | FAILED → (RETRY_SCHEDULED → QUEUED) | DEAD_LETTER

Invariants:
1. Attempts increments only on delivery tries.
2. Failed and max attempts ⇒ dead-letter.
3. Retry scheduled before requeue.
4. Redelivery clears previous transient status.

## 6. Delivery Strategies (32–40)
ImmediateDeliveryStrategy:
- On publish: deliver to each subscriber instantly.
- If subscriber errors → apply retry.

BatchedDeliveryStrategy(batch_size= N):
- Accumulate messages per topic until size reached.
- Flush triggers delivery of batch (still one-by-one to subscribers).
- Strategy swap keeps existing queue intact.

## 7. Retry Policy (40–46)
SimpleRetryPolicy(max_attempts, backoff_factor):
- should_retry(message) & compute_delay(attempt)
Delay simulation minimal (we note value; not sleeping heavily).
Duplicate risk: subscriber must be idempotent.

## 8. Backpressure (46–52)
Max queue length per topic.
If exceeded:
- emit `backpressure` event
- Policy: reject new message OR drop oldest (choose reject for clarity).

## 9. Metrics (52–56)
Per topic:
- published_count
- delivered_count
- failed_count
- dead_letter_count
- subscriber_count
- queue_length

## 10. Events (56–60)
Names:
- subscriber_added, message_enqueued, delivering, delivered, failed, retry_scheduled, dead_letter, strategy_swapped, backpressure, batch_flush
Payload includes ids, topic, attempts, status snapshot.

## 11. Demo Scenarios (60–68)
1. Setup + immediate publish
2. Simulated failure + retry success
3. Multiple subscribers broadcast
4. Switch to batched strategy and flush
5. Backpressure + dead-letter summary

## 12. Trade-Offs (68–72)
At-least-once vs exactly-once: complexity of deduplication.
Immediate vs batched: latency vs throughput.
Reject vs drop on backpressure: reliability vs freshness.
Retry timing: exponential backoff avoids hot loops.
Singleton broker vs DI: testability trade-off.

## 13. Extensions (72–75)
- Persistence log (append-only + replay)
- Consumer groups (scaling parallelism)
- Partitioning + ordering guarantees
- Pull-based flow control (subscriber-driven)
- Distributed cluster with consistent hashing

## Summary
Design emphasizes clear lifecycles, strategic flexibility, robust retry, and observability. Scales conceptually toward production patterns (partitioning, durability, consumer groups) while remaining interview-friendly.


## Detailed Design Reference

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


## Compact Code

```python
"""Compact Pub-Sub implementation demonstrating patterns
Run: python3 INTERVIEW_COMPACT.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
import time
import itertools

# ---------------- Message & Status -----------------
class MessageStatus(Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    DEAD_LETTER = "DEAD_LETTER"

_message_id_counter = itertools.count(1)

def next_message_id() -> int:
    return next(_message_id_counter)

@dataclass
class Message:
    topic: str
    payload: Any
    id: int = field(default_factory=next_message_id)
    status: MessageStatus = MessageStatus.CREATED
    attempts: int = 0
    created_ts: float = field(default_factory=time.time)
    last_ts: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_ts = time.time()

# ---------------- Subscriber -----------------
class Subscriber:
    def __init__(self, name: str, handler: Callable[[Message], None]) -> None:
        self.name = name
        self.handler = handler
    def handle(self, msg: Message) -> None:
        self.handler(msg)

# ---------------- Retry Policy (Strategy) -----------------
class RetryPolicy:
    def should_retry(self, msg: Message) -> bool:
        raise NotImplementedError
    def compute_delay(self, msg: Message) -> float:
        raise NotImplementedError

class SimpleRetryPolicy(RetryPolicy):
    def __init__(self, max_attempts: int = 3, backoff_factor: float = 0.25) -> None:
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
    def should_retry(self, msg: Message) -> bool:
        return msg.attempts < self.max_attempts
    def compute_delay(self, msg: Message) -> float:
        return (msg.attempts or 1) * self.backoff_factor

# ---------------- Delivery Strategy (Strategy) -----------------
class DeliveryStrategy:
    def name(self) -> str:
        return self.__class__.__name__
    def publish(self, broker: Broker, topic: str, msg: Message) -> None:  # type: ignore[name-defined]
        raise NotImplementedError
    def flush(self, broker: Broker, topic: str) -> None:  # type: ignore[name-defined]
        pass

class ImmediateDeliveryStrategy(DeliveryStrategy):
    def publish(self, broker: Broker, topic: str, msg: Message) -> None:  # type: ignore[name-defined]
        broker._enqueue(topic, msg)
        broker._deliver_topic_messages(topic)

class BatchedDeliveryStrategy(DeliveryStrategy):
    def __init__(self, batch_size: int = 3) -> None:
        self.batch_size = batch_size
    def publish(self, broker: Broker, topic: str, msg: Message) -> None:  # type: ignore[name-defined]
        broker._enqueue(topic, msg)
        if len(broker.queues[topic]) >= self.batch_size:
            self.flush(broker, topic)
    def flush(self, broker: Broker, topic: str) -> None:  # type: ignore[name-defined]
        broker._emit("batch_flush", {"topic": topic, "size": len(broker.queues[topic])})
        broker._deliver_topic_messages(topic)

# ---------------- Dead Letter Store -----------------
class DeadLetterStore:
    def __init__(self) -> None:
        self.messages: List[Message] = []
    def add(self, msg: Message) -> None:
        self.messages.append(msg)

# ---------------- Broker (Singleton) -----------------
class Broker:
    _instance: Optional[Broker] = None
    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Subscriber]] = {}
        self.queues: Dict[str, List[Message]] = {}
        self.retry_policy: RetryPolicy = SimpleRetryPolicy()
        self.delivery_strategy: DeliveryStrategy = ImmediateDeliveryStrategy()
        self.dead_letter = DeadLetterStore()
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.metrics: Dict[str, Dict[str, int]] = {}
        self.max_queue_size = 10
    @classmethod
    def instance(cls) -> Broker:
        if cls._instance is None:
            cls._instance = Broker()
        return cls._instance
    def register_listener(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(fn)
    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    def add_subscriber(self, topic: str, subscriber: Subscriber) -> None:
        self.subscribers.setdefault(topic, []).append(subscriber)
        self.metrics.setdefault(topic, self._new_metrics())
        self._emit("subscriber_added", {"topic": topic, "subscriber": subscriber.name})
    def publish(self, topic: str, payload: Any) -> Message:
        self.metrics.setdefault(topic, self._new_metrics())
        msg = Message(topic=topic, payload=payload)
        self.metrics[topic]["published"] += 1
        self.delivery_strategy.publish(self, topic, msg)
        return msg
    def _enqueue(self, topic: str, msg: Message) -> None:
        q = self.queues.setdefault(topic, [])
        if len(q) >= self.max_queue_size:
            self._emit("backpressure", {"topic": topic, "queue_length": len(q)})
            return  # reject publish for simplicity
        msg.status = MessageStatus.QUEUED
        msg.touch()
        q.append(msg)
        self._emit("message_enqueued", {"topic": topic, "id": msg.id, "queue_length": len(q)})
    def _deliver_topic_messages(self, topic: str) -> None:
        q = self.queues.get(topic, [])
        if not q:
            return
        subs = self.subscribers.get(topic, [])
        while q:
            msg = q.pop(0)
            self._deliver_to_subscribers(topic, msg, subs)
    def _deliver_to_subscribers(self, topic: str, msg: Message, subs: List[Subscriber]) -> None:
        if not subs:
            # No subscribers, leave in delivered state for metrics
            msg.status = MessageStatus.DELIVERED
            self.metrics[topic]["delivered"] += 1
            self._emit("delivered", {"topic": topic, "id": msg.id, "subs": 0})
            return
        for sub in subs:
            self._deliver_single(topic, msg, sub)
    def _deliver_single(self, topic: str, msg: Message, sub: Subscriber) -> None:
        msg.status = MessageStatus.DELIVERING
        msg.attempts += 1
        msg.touch()
        self._emit("delivering", {"topic": topic, "id": msg.id, "attempt": msg.attempts, "subscriber": sub.name})
        try:
            sub.handle(msg)
            msg.status = MessageStatus.DELIVERED
            self.metrics[topic]["delivered"] += 1
            self._emit("delivered", {"topic": topic, "id": msg.id, "subscriber": sub.name})
        except Exception as exc:  # noqa: BLE001
            msg.status = MessageStatus.FAILED
            self.metrics[topic]["failed"] += 1
            self._emit("failed", {"topic": topic, "id": msg.id, "subscriber": sub.name, "error": str(exc)})
            self._handle_failure(topic, msg)
    def _handle_failure(self, topic: str, msg: Message) -> None:
        if self.retry_policy.should_retry(msg):
            msg.status = MessageStatus.RETRY_SCHEDULED
            delay = self.retry_policy.compute_delay(msg)
            self._emit("retry_scheduled", {"topic": topic, "id": msg.id, "delay": delay})
            # Simulate delay logically (no sleep) then requeue
            msg.status = MessageStatus.QUEUED
            self.queues.setdefault(topic, []).append(msg)
        else:
            msg.status = MessageStatus.DEAD_LETTER
            self.dead_letter.add(msg)
            self.metrics[topic]["dead_letter"] += 1
            self._emit("dead_letter", {"topic": topic, "id": msg.id})
    def swap_strategy(self, strategy: DeliveryStrategy) -> None:
        old = self.delivery_strategy.name()
        self.delivery_strategy = strategy
        self._emit("strategy_swapped", {"old": old, "new": strategy.name()})
    def flush(self, topic: str) -> None:
        self.delivery_strategy.flush(self, topic)
    def summarize(self) -> Dict[str, Dict[str, int]]:
        for topic, m in self.metrics.items():
            m["queue_length"] = len(self.queues.get(topic, []))
            m["subscriber_count"] = len(self.subscribers.get(topic, []))
        return self.metrics
    def _new_metrics(self) -> Dict[str, int]:
        return {"published": 0, "delivered": 0, "failed": 0, "dead_letter": 0, "queue_length": 0, "subscriber_count": 0}

# ---------------- Publisher (Facade) -----------------
class Publisher:
    def __init__(self, broker: Broker) -> None:
        self.broker = broker
    def publish(self, topic: str, payload: Any) -> Message:
        return self.broker.publish(topic, payload)

# ---------------- Event Listener -----------------
def event_listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------- Demo Scenarios -----------------

def print_header(title: str) -> None:
    print("\n=== " + title + " ===")

def demo_1_basic_publish() -> None:
    print_header("Demo 1: Basic Publish")
    broker = Broker.instance()
    broker.register_listener(event_listener)
    broker.add_subscriber("news", Subscriber("sub_A", lambda m: print(f"sub_A received {m.id}: {m.payload}")))
    pub = Publisher(broker)
    pub.publish("news", {"headline": "Hello World"})


def demo_2_failure_retry() -> None:
    print_header("Demo 2: Failure + Retry")
    broker = Broker.instance()
    def flaky_handler(msg: Message) -> None:
        if msg.attempts < 2:
            raise RuntimeError("Transient failure")
        print(f"flaky received after {msg.attempts} attempts: {msg.payload}")
    broker.add_subscriber("tasks", Subscriber("flaky", flaky_handler))
    pub = Publisher(broker)
    pub.publish("tasks", {"job": "process"})
    # Process queued retries (immediate strategy already requeues; call deliver explicitly if leftover)
    broker._deliver_topic_messages("tasks")


def demo_3_multiple_subscribers() -> None:
    print_header("Demo 3: Broadcast to Multiple Subscribers")
    broker = Broker.instance()
    broker.add_subscriber("news", Subscriber("sub_B", lambda m: print(f"sub_B got {m.payload}")))
    pub = Publisher(broker)
    pub.publish("news", {"headline": "Multi-subscriber"})


def demo_4_strategy_swap_and_batch() -> None:
    print_header("Demo 4: Strategy Swap -> Batched Delivery")
    broker = Broker.instance()
    broker.swap_strategy(BatchedDeliveryStrategy(batch_size=2))
    pub = Publisher(broker)
    pub.publish("metrics", {"value": 1})
    pub.publish("metrics", {"value": 2})  # triggers flush
    pub.publish("metrics", {"value": 3})
    broker.flush("metrics")  # manual flush for remaining


def demo_5_backpressure_dead_letter_summary() -> None:
    print_header("Demo 5: Backpressure + Summary")
    broker = Broker.instance()
    broker.swap_strategy(ImmediateDeliveryStrategy())
    # Subscriber that always fails to push messages into dead-letter after retries
    def always_fail(msg: Message) -> None:
        raise RuntimeError("Permanent failure")
    broker.add_subscriber("errors", Subscriber("sink", always_fail))
    pub = Publisher(broker)
    for i in range(5):
        pub.publish("errors", {"event": i})
        broker._deliver_topic_messages("errors")
    print("Dead-letter count:", len(broker.dead_letter.messages))
    print("Metrics summary:")
    for topic, data in broker.summarize().items():
        print(topic, data)

# ---------------- Main -----------------
if __name__ == "__main__":
    demo_1_basic_publish()
    demo_2_failure_retry()
    demo_3_multiple_subscribers()
    demo_4_strategy_swap_and_batch()
    demo_5_backpressure_dead_letter_summary()

```

## Architecture Sketch
````
(Describe components, controller, strategies, observers, flows)
````


## UML Class Diagram (text)
````
(Classes, relationships, strategies/observers, enums)
````


## Scaling & Trade-offs (Q&A)
- How to scale? (sharding/queues/caching/locks)
- Prevent double booking/conflicts? (locks/optimistic concurrency)
- Persistence? (snapshots + event log)
- Performance? (bucketed lookups/O(1) operations)
- Memory/history growth? (caps, snapshots)
