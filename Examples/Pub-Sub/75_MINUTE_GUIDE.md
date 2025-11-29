# 📡 Pub-Sub Messaging System – 75 Minute Deep Dive

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
