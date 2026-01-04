# Pub-Sub Message Broker — 75-Minute Interview Guide

## Quick Start

### 5-Minute Overview
A publish-subscribe message broker for decoupled communication between producers and consumers. Publishers emit messages to topics, subscribers receive messages. Patterns: At-most-once, At-least-once, Exactly-once delivery.

### Key Entities
| Entity | Purpose |
|--------|---------|
| **Topic** | Named message channel (ORDERS, PAYMENTS, NOTIFICATIONS) |
| **Publisher** | Sends messages to topic |
| **Subscriber** | Receives messages from topic |
| **Message** | Data unit with metadata (key, value, timestamp) |
| **Broker** | Central coordinator |

### 5 Design Patterns
1. **Singleton**: Central broker
2. **Observer**: Subscribers notified
3. **Factory**: Message creation
4. **Strategy**: Delivery guarantees
5. **Thread Pool**: Concurrent subscribers

### Critical Points
✅ Decouple publishers & subscribers  
✅ Topic partitioning for scalability  
✅ Consumer groups for load balancing  
✅ Offset management for fault tolerance  
✅ At-least-once delivery (retry logic)  

---

## System Overview

### Problem
Multiple services need to communicate asynchronously without tight coupling.

### Solution
Topic-based pub-sub with message persistence and consumer groups.

---

## Requirements

✅ Publish messages to topic  
✅ Subscribe to topic  
✅ Consume messages in order  
✅ Consumer groups (multiple subscribers)  
✅ Offset management (position in topic)  
✅ Message retention (configurable)  
✅ Fault tolerance (message replication)  

---

## Architecture

### 1. Topic & Partitions
```
Topic "ORDERS"
├─ Partition 0: [Msg1, Msg2, Msg3, ...]
├─ Partition 1: [Msg4, Msg5, Msg6, ...]
└─ Partition 2: [Msg7, Msg8, Msg9, ...]

Each partition: ordered, immutable log
```

### 2. Consumer Groups
```
Topic "ORDERS"
├─ Consumer Group A
│  ├─ Consumer A1: consumes Partition 0
│  ├─ Consumer A2: consumes Partition 1
│  └─ Consumer A3: consumes Partition 2
│
└─ Consumer Group B (independent)
   ├─ Consumer B1: consumes Partition 0
   └─ Consumer B2: consumes Partitions 1,2
```

### 3. Broker Architecture
```python
class Broker:
    def __init__(self):
        self.topics = {}  # topic -> Topic
        self.consumer_groups = {}  # group -> ConsumerGroup
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    def publish(self, topic_name, key, message):
        topic = self.topics.get(topic_name)
        partition = hash(key) % topic.num_partitions
        topic.partitions[partition].append((key, message))
    
    def subscribe(self, group_id, topic_name, consumer_id):
        group = self.consumer_groups.get(group_id)
        # Assign partition to consumer
        group.assign_partition(consumer_id, partition)
    
    def consume(self, group_id, consumer_id):
        offset = self.get_offset(group_id, consumer_id)
        message = self.partitions[assigned_partition][offset]
        self.update_offset(group_id, consumer_id, offset + 1)
        return message
```

---

## Interview Q&A

### Q1: Pub-Sub vs Queue difference?
**A**: Pub-Sub: broadcast to all subscribers. Queue: work distribution among consumers. Pub-Sub = one-to-many. Queue = one-to-one.

### Q2: Consumer group coordination?
**A**: All consumers in group share responsibility for topic partitions. Rebalancing when consumer joins/leaves.

### Q3: Offset management?
**A**: Each consumer stores offset (position in partition). On restart: resume from offset, don't reprocess.

### Q4: Exactly-once delivery?
**A**: Idempotent consumer (deduplication ID), transactional writes, offset commits atomically with processing.

### Q5: Message ordering?
**A**: Within partition: messages ordered. Across partitions: no guarantee. Use single partition if strict order needed (performance tradeoff).

### Q6: Dead letter queue?
**A**: Messages failing N retries → sent to DLQ topic. Manual inspection & reprocessing.

### Q7: Backpressure handling?
**A**: If subscriber slow → buffer in broker grows. Stop accepting publishes until buffer clears.

### Q8: Replication?
**A**: Each partition replicated across 3 brokers. Leader handles reads/writes, followers sync. On failure: follower becomes leader.

### Q9: Message retention?
**A**: Delete old messages after TTL or size limit. Tradeoff: memory vs replay ability.

### Q10: Scaling to 1M messages/sec?
**A**: Partition topics (sharding), multiple brokers, consumer groups for load balancing, disk persistence.

---

## Scaling Q&A

### Q1: 1M messages/sec, 100+ topics?
**A**: 1000+ brokers, 100 partitions per topic, consumer groups = load distribution.

### Q2: Exactly-once semantics?
**A**: Idempotent produces (dedup key), atomic offset commits, transactional processing.

### Q3: Multi-datacenter replication?
**A**: Geo-replication (async to other DC). RPO = seconds, RTO = seconds.

---

## Demo
```python
broker = Broker()
broker.create_topic("ORDERS", 3)

# Publish
broker.publish("ORDERS", "order_id_1", {"amount": 100})
broker.publish("ORDERS", "order_id_2", {"amount": 200})

# Subscribe
broker.subscribe("payment_group", "ORDERS", "consumer_1")

# Consume
msg = broker.consume("payment_group", "consumer_1")  # Gets message
offset = broker.get_offset("payment_group", "consumer_1")  # Track position
```

---

**Ready to publish & subscribe! 📨**
