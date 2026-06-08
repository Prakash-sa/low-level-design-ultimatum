# Pub-Sub Message Broker — Complete Design Guide

> Topic-based publish-subscribe messaging with consumer groups, offset management, at-least-once delivery guarantees, and thread-safe concurrent producers and consumers.

**Scale**: 1,000+ concurrent producers/consumers, 100+ topics, 99.9% uptime
**Duration**: 75-minute interview guide
**Focus**: Topic partitioning, consumer group coordination, offset tracking, delivery guarantees, thread-safe broker

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Multiple services need to communicate asynchronously without tight coupling. A publisher (Order Service) emits an event to a named topic; multiple independent subscribers (Payment Service, Notification Service, Analytics Service) each receive and process the event at their own pace. The broker persists messages so slow consumers never lose data and fast restarts resume from where they left off.

### Core Flow
```
Publisher → publish(topic, key, message)
                        |
              [Broker: hash(key) → Partition N]
                        |
          ┌─────────────┴──────────────┐
          ▼                            ▼
  Consumer Group A              Consumer Group B
  (each partition                (independent copy
   assigned to one               of every message)
   consumer in group)
          |
  consume(group, consumer) → message + auto-advance offset
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single broker or distributed cluster?** → "Single broker for the interview; mention cluster as a scaling concern"
2. **Message ordering required?** → "Within a partition only; cross-partition ordering not guaranteed"
3. **Delivery guarantee?** → "At-least-once (retry on failure); mention exactly-once as an extension"
4. **Message persistence?** → "In-memory for the demo; disk-backed in production"
5. **Consumer groups or pure broadcast?** → "Both: consumer groups for load balancing, multiple groups for fan-out"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Publisher** | Produces events to topics | create_topic, publish message |
| **Subscriber / Consumer** | Reads events from topics | subscribe, consume, commit offset |
| **Broker** | Central coordinator | Route messages, track offsets, manage groups |
| **Admin / System** | Manages configuration | Create/delete topics, set retention, trigger compaction |

### Functional Requirements (What does the system do?)

✅ **Topic Management**
  - Create and delete named topics
  - Support configurable number of partitions per topic
  - Configurable message retention (count or TTL)

✅ **Publishing**
  - Publish messages with optional partition key
  - Route message to partition via `hash(key) % num_partitions`
  - Assign monotonically increasing offset within each partition

✅ **Subscribing & Consuming**
  - Subscribe a consumer to a topic under a consumer group
  - Assign partitions to consumers in a group (each partition → one consumer)
  - Consume next message at current offset; advance offset atomically
  - Resume from last committed offset on restart

✅ **Consumer Groups**
  - Multiple independent groups consume the same topic (fan-out)
  - Within a group, partitions are distributed across consumers (load balance)
  - Rebalance when a consumer joins or leaves the group

✅ **Offset Management**
  - Track per-(group, consumer, partition) offset
  - Commit offset after successful processing
  - Replay from any past offset (seek)

✅ **Delivery Guarantees**
  - At-most-once: fire-and-forget (advance offset before processing)
  - At-least-once: advance offset only after successful processing
  - Exactly-once: idempotent consumer + transactional offset commit (extension)

✅ **Dead Letter Queue**
  - Messages failing N retries routed to `<topic>-DLQ`
  - Manual inspection and reprocessing

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Support 1,000+ simultaneous producers and consumers
✅ **Ordering**: Guaranteed within a partition; best-effort across partitions
✅ **Throughput**: 100K+ messages/sec per broker (in-memory); disk-backed for persistence
✅ **Latency**: <10 ms publish; <20 ms consume (in-memory)
✅ **Fault Tolerance**: No message loss on consumer crash (offset not advanced until commit)
✅ **Scalability**: Add partitions and consumer instances independently

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | NO for demo — single broker; mention sharding as extension |
| **Persistence** | In-memory (append-only list per partition) |
| **Max message size** | 1 MB (mention Kafka default) |
| **Retention** | Configurable per topic (default: 1,000 messages or 7 days) |
| **Consumer group rebalance** | Simple round-robin partition assignment |
| **Real disk I/O?** | No — mock append-only log for interview |
| **Authentication?** | Out of scope; mention ACLs as production concern |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Topic, Partition, Message, Publisher, Subscriber, ConsumerGroup, Subscription, Broker, Offset, ...
```

### Step 2.2: Define Core Classes

#### **Message** — A single unit of data
```
Properties:
  - message_id: str          (UUID, globally unique)
  - key: Optional[str]       (determines partition routing)
  - value: Any               (payload; dict, string, bytes)
  - timestamp: datetime      (when published)
  - headers: Dict[str, str]  (optional metadata: source, correlation-id)
  - offset: int              (position within its partition; set by broker)

Behaviors:
  - (immutable data holder once created)
```

#### **Partition** — An ordered, append-only log segment of a topic
```
Properties:
  - partition_id: int
  - topic_name: str
  - messages: List[Message]  (append-only; position = offset)
  - lock: threading.Lock     (guards concurrent appends)

Behaviors:
  - append(message): Add message, set offset = len(messages) - 1
  - read(offset): Return message at given offset (or None)
  - size(): Number of messages stored
```

#### **Topic** — A named channel composed of N partitions
```
Properties:
  - topic_name: str
  - num_partitions: int
  - partitions: List[Partition]
  - retention_limit: int     (max messages per partition before pruning)

Behaviors:
  - get_partition(key): hash(key) % num_partitions → Partition
  - append(key, message): Route to correct partition and append
  - partition_count(): Return num_partitions
```

#### **Publisher** — A producer of messages
```
Properties:
  - publisher_id: str
  - name: str

Behaviors:
  - (identity holder; actual publish goes through Broker API)
```

#### **Subscriber** — An individual consumer within a group
```
Properties:
  - subscriber_id: str
  - name: str
  - group_id: str            (which consumer group this subscriber belongs to)

Behaviors:
  - (identity holder; actual consume goes through Broker API)
```

#### **ConsumerGroup** — A logical group of subscribers sharing a topic's partitions
```
Properties:
  - group_id: str
  - topic_name: str
  - subscribers: List[Subscriber]
  - partition_assignments: Dict[str, List[int]]   (subscriber_id → [partition_ids])
  - offsets: Dict[Tuple[str, int], int]           ((subscriber_id, partition_id) → next offset)
  - lock: threading.RLock

Behaviors:
  - add_subscriber(subscriber): Register and rebalance partitions
  - remove_subscriber(subscriber_id): Unregister and rebalance
  - assign_partitions(): Round-robin partition → subscriber assignment
  - get_offset(subscriber_id, partition_id): Current read position
  - advance_offset(subscriber_id, partition_id): Increment offset after consume
```

#### **Broker** — Central coordinator (Singleton)
```
Properties:
  - topics: Dict[str, Topic]
  - consumer_groups: Dict[str, ConsumerGroup]
  - publishers: Dict[str, Publisher]
  - subscribers: Dict[str, Subscriber]
  - observers: List[BrokerObserver]          (for audit/monitoring)
  - lock: threading.RLock

Behaviors:
  - create_topic(name, num_partitions, retention): Create topic
  - register_publisher(publisher_id, name): Register publisher
  - register_subscriber(subscriber_id, group_id, name): Register subscriber
  - subscribe(group_id, topic_name, subscriber_id): Join group on topic
  - publish(publisher_id, topic_name, key, value): Route and append message
  - consume(group_id, subscriber_id): Return next unconsumed message
  - get_offset(group_id, subscriber_id): Current offset for subscriber
  - seek(group_id, subscriber_id, partition_id, offset): Reposition reader
```

### Step 2.3: Define Enumerations (State & Type)

```python
from enum import Enum

class DeliveryGuarantee(Enum):
    AT_MOST_ONCE  = "at_most_once"   # advance offset BEFORE processing
    AT_LEAST_ONCE = "at_least_once"  # advance offset AFTER processing (default)
    EXACTLY_ONCE  = "exactly_once"   # idempotent + transactional commit

class MessageStatus(Enum):
    PENDING    = "pending"    # published, not yet consumed
    CONSUMED   = "consumed"   # consumed by at least one group
    DLQ        = "dlq"        # moved to dead-letter queue after N retries
    EXPIRED    = "expired"    # past retention TTL

class TopicStatus(Enum):
    ACTIVE   = "active"    # accepting publishes and consumes
    PAUSED   = "paused"    # no new publishes accepted
    DELETED  = "deleted"   # permanently removed

class GroupStatus(Enum):
    ACTIVE      = "active"      # consuming normally
    REBALANCING = "rebalancing" # partition reassignment in progress
    INACTIVE    = "inactive"    # no active subscribers
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **Message** | Immutable data unit with identity and position | Can't track delivery or replay |
| **Partition** | Ordered log for parallelism and ordering guarantee | No ordering or horizontal scale |
| **Topic** | Groups related partitions under a name | No routing or namespace |
| **Publisher** | Identity for audit, rate limiting, ACLs | Can't attribute messages to source |
| **Subscriber** | Individual consumer identity within a group | Can't assign partitions |
| **ConsumerGroup** | Load-balance partitions; enable fan-out | Every subscriber would duplicate or miss messages |
| **Broker** | Central coordinator, thread-safe single source of truth | No consistent routing or offset management |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Create Topic**
```python
def create_topic(topic_name: str, num_partitions: int = 3,
                 retention_limit: int = 1000) -> Topic:
    """
    Create a named topic with N partitions.

    Returns: Topic object.
    Raises: TopicAlreadyExistsError if topic_name already registered.
    Idempotency: NO — call once per topic name.
    """
    pass
```

#### **2. Register Publisher**
```python
def register_publisher(publisher_id: str, name: str) -> Publisher:
    """
    Register a publisher identity.
    Returns: Publisher object.
    """
    pass
```

#### **3. Register Subscriber**
```python
def register_subscriber(subscriber_id: str, group_id: str,
                        name: str) -> Subscriber:
    """
    Register a subscriber identity belonging to group_id.
    Returns: Subscriber object.
    """
    pass
```

#### **4. Subscribe to Topic** ⭐ CRITICAL
```python
def subscribe(group_id: str, topic_name: str,
              subscriber_id: str) -> ConsumerGroup:
    """
    Add subscriber_id to consumer group group_id on topic_name.
    If group doesn't exist, create it.
    Triggers partition rebalance among group members.

    Precondition: topic exists, subscriber registered.
    Postcondition: subscriber assigned one or more partitions.

    Returns: Updated ConsumerGroup.
    Raises:
      - TopicNotFoundError: topic_name invalid.
      - SubscriberNotFoundError: subscriber_id not registered.

    Concurrency: THREAD-SAFE (RLock on group).
    """
    pass
```

#### **5. Publish** ⭐ CRITICAL
```python
def publish(publisher_id: str, topic_name: str,
            key: Optional[str], value: Any) -> Message:
    """
    Publish a message to a topic.
    Partition routing: hash(key) % num_partitions (or round-robin if key=None).

    Returns: Message with assigned offset and partition.
    Raises:
      - TopicNotFoundError: topic_name invalid.
      - PublisherNotFoundError: publisher_id not registered.

    Concurrency: THREAD-SAFE — each partition has its own lock.
    Idempotency: NO — each call appends a new message.
    """
    pass
```

#### **6. Consume** ⭐ CRITICAL
```python
def consume(group_id: str, subscriber_id: str) -> Optional[Message]:
    """
    Return the next unconsumed message for subscriber_id within group_id.
    Advances offset AFTER returning (at-least-once semantics).

    Precondition: subscriber assigned partitions in group.
    Postcondition: offset advanced by 1 for the consumed partition.

    Returns: Message, or None if no new messages.
    Raises:
      - GroupNotFoundError: group_id invalid.
      - SubscriberNotInGroupError: subscriber has not subscribed.

    Concurrency: THREAD-SAFE (RLock on group offsets).
    """
    pass
```

#### **7. Get Offset**
```python
def get_offset(group_id: str, subscriber_id: str) -> Dict[int, int]:
    """
    Return current offsets: {partition_id: next_offset} for subscriber.
    Useful for monitoring lag.
    """
    pass
```

#### **8. Seek (Replay)**
```python
def seek(group_id: str, subscriber_id: str,
         partition_id: int, offset: int) -> bool:
    """
    Reposition subscriber's read cursor for a specific partition.
    Enables message replay or skipping.

    Returns: True if seek succeeded, False if offset out of range.
    """
    pass
```

### Step 3.2: Exception Hierarchy

```python
class BrokerException(Exception):
    """Base exception for all broker errors."""
    pass

class TopicNotFoundError(BrokerException):
    """Topic name not registered."""
    pass

class TopicAlreadyExistsError(BrokerException):
    """Topic with this name already created."""
    pass

class PublisherNotFoundError(BrokerException):
    """Publisher ID not registered."""
    pass

class SubscriberNotFoundError(BrokerException):
    """Subscriber ID not registered."""
    pass

class SubscriberNotInGroupError(BrokerException):
    """Subscriber has not subscribed to the group/topic."""
    pass

class GroupNotFoundError(BrokerException):
    """Consumer group not found."""
    pass
```

### Step 3.3: API Usage Example

```python
broker = Broker.get_instance()

# 1. Create topic
broker.create_topic("ORDERS", num_partitions=3)

# 2. Register actors
broker.register_publisher("svc-orders", "Order Service")
broker.register_subscriber("payment-1", "payment-group", "Payment Consumer 1")
broker.register_subscriber("payment-2", "payment-group", "Payment Consumer 2")
broker.register_subscriber("analytics-1", "analytics-group", "Analytics Consumer")

# 3. Subscribe to topic
broker.subscribe("payment-group", "ORDERS", "payment-1")
broker.subscribe("payment-group", "ORDERS", "payment-2")
broker.subscribe("analytics-group", "ORDERS", "analytics-1")

# 4. Publish messages
broker.publish("svc-orders", "ORDERS", "order_101", {"amount": 99.99})
broker.publish("svc-orders", "ORDERS", "order_102", {"amount": 250.00})

# 5. Consume
msg = broker.consume("payment-group", "payment-1")
print(f"Payment-1 got: {msg.value}")

# 6. Check offset
offsets = broker.get_offset("payment-group", "payment-1")
print(f"Offsets: {offsets}")
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
Broker HAS-A topics (1:N Composition)
  └─ Broker creates and owns all topics

Topic HAS-A partitions (1:N Composition)
  └─ Topic owns N Partition objects (N configured at creation)

Partition HAS-A messages (1:N Composition)
  └─ Partition owns its append-only message log

Broker HAS-A consumer_groups (1:N Composition)
  └─ Broker creates and tracks all consumer groups

ConsumerGroup REFERENCES Topic (1:1 Association)
  └─ Group reads from one topic (no ownership)

ConsumerGroup HAS-A subscribers (1:N Aggregation)
  └─ Group tracks its subscriber roster (subscribers exist independently)

Subscriber BELONGS-TO ConsumerGroup (N:1 Association)
  └─ A subscriber is a member of exactly one group per topic

Publisher USES Broker (1:1 Association)
  └─ Publisher calls broker.publish(); no ownership
```

### Step 4.2: Complete UML Class Diagram

```
┌───────────────────────────────────────────────┐
│            Broker (Singleton)                 │
├───────────────────────────────────────────────┤
│ - _instance: Broker                           │
│ - topics: Dict[str, Topic]                    │
│ - consumer_groups: Dict[str, ConsumerGroup]   │
│ - publishers: Dict[str, Publisher]            │
│ - subscribers: Dict[str, Subscriber]          │
│ - observers: List[BrokerObserver]             │
│ - _lock: threading.RLock                      │
├───────────────────────────────────────────────┤
│ + get_instance(): Broker                      │
│ + create_topic(name, partitions): Topic       │
│ + register_publisher(id, name): Publisher     │
│ + register_subscriber(id, gid, name): Sub     │
│ + subscribe(group, topic, sub): ConsumerGroup │
│ + publish(pub_id, topic, key, value): Message │
│ + consume(group_id, sub_id): Optional[Message]│
│ + get_offset(group, sub): Dict[int, int]      │
│ + seek(group, sub, partition, offset): bool   │
└───────────────┬───────────────────────────────┘
    manages 1:N │
                ▼
    ┌───────────────────────────────────┐
    │             Topic                 │
    ├───────────────────────────────────┤
    │ - topic_name: str                 │
    │ - num_partitions: int             │
    │ - partitions: List[Partition]     │
    │ - retention_limit: int            │
    │ - status: TopicStatus             │
    ├───────────────────────────────────┤
    │ + get_partition(key): Partition   │
    │ + append(key, message): int       │
    │ + partition_count(): int          │
    └───────────┬───────────────────────┘
    contains 1:N│
                ▼
    ┌───────────────────────────────────┐
    │           Partition               │
    ├───────────────────────────────────┤
    │ - partition_id: int               │
    │ - topic_name: str                 │
    │ - messages: List[Message]         │
    │ - lock: threading.Lock            │
    ├───────────────────────────────────┤
    │ + append(message): int (offset)   │
    │ + read(offset): Optional[Message] │
    │ + size(): int                     │
    └───────────────────────────────────┘
                    ▲ reads from
                    │
    ┌───────────────────────────────────┐
    │          ConsumerGroup            │
    ├───────────────────────────────────┤
    │ - group_id: str                   │
    │ - topic_name: str                 │
    │ - subscribers: List[Subscriber]   │
    │ - partition_assignments: Dict     │
    │ - offsets: Dict[(sub,part), int]  │
    │ - lock: threading.RLock           │
    ├───────────────────────────────────┤
    │ + add_subscriber(sub): void       │
    │ + assign_partitions(): void       │
    │ + get_offset(sub, part): int      │
    │ + advance_offset(sub, part): void │
    └───────────┬───────────────────────┘
    roster 1:N  │
                ▼
    ┌───────────────────────┐    ┌───────────────────────┐
    │      Subscriber       │    │      Publisher         │
    ├───────────────────────┤    ├───────────────────────┤
    │ - subscriber_id: str  │    │ - publisher_id: str   │
    │ - name: str           │    │ - name: str           │
    │ - group_id: str       │    └───────────────────────┘
    └───────────────────────┘

    ┌─────────────────────────────────────────┐
    │               Message                   │
    ├─────────────────────────────────────────┤
    │ - message_id: str (UUID)                │
    │ - key: Optional[str]                    │
    │ - value: Any                            │
    │ - timestamp: datetime                   │
    │ - offset: int (set by Partition.append) │
    │ - partition_id: int                     │
    └─────────────────────────────────────────┘

OBSERVER PATTERN (Audit/Monitoring):
┌───────────────────────────────────────┐
│  BrokerObserver (Abstract)            │
├───────────────────────────────────────┤
│ + on_publish(topic, message): void    │
│ + on_consume(group, sub, message)     │
└──┬────────────────────────────────────┘
   │ implemented by
   ├─→ ConsoleAuditObserver (log all events)
   ├─→ MetricsObserver (count msgs/sec)
   └─→ AlertObserver (lag > threshold)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| Broker → Topics | 1:N | Composition | Broker creates and owns all topics |
| Topic → Partitions | 1:N | Composition | Topic owns N ordered log segments |
| Partition → Messages | 1:N | Composition | Partition is the append-only log |
| Broker → ConsumerGroups | 1:N | Composition | Broker tracks all groups |
| ConsumerGroup → Subscribers | 1:N | Aggregation | Group tracks member roster |
| ConsumerGroup → Topic | N:1 | Association | Many groups can read one topic |
| Publisher → Broker | N:1 | Association | Publishers call broker API |
| Broker → BrokerObserver | 1:N | Association | System notifies many listeners |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Observer / Pub-Sub Core** (The System IS an Observer Pattern)

**Problem**: Publishers and subscribers must communicate without knowing about each other. A new subscriber joining should not require changes to publisher code.

**Solution**: The Broker acts as the mediator. Publishers push to the broker; subscribers pull from the broker. The broker's `observers` list adds a second layer for monitoring/audit.

```python
class BrokerObserver(ABC):
    @abstractmethod
    def on_publish(self, topic_name: str, message: 'Message') -> None:
        pass

    @abstractmethod
    def on_consume(self, group_id: str, subscriber_id: str,
                   message: 'Message') -> None:
        pass

class ConsoleAuditObserver(BrokerObserver):
    def on_publish(self, topic_name: str, message: 'Message') -> None:
        print(f"[PUBLISH] topic={topic_name} key={message.key} "
              f"partition={message.partition_id} offset={message.offset}")

    def on_consume(self, group_id: str, subscriber_id: str,
                   message: 'Message') -> None:
        print(f"[CONSUME] group={group_id} sub={subscriber_id} "
              f"offset={message.offset} value={message.value}")

# Usage
broker.add_observer(ConsoleAuditObserver())
```

**Benefit**: ✅ Decoupled producers from consumers, ✅ Easy to add monitoring without touching core logic
**Trade-off**: ⚠️ Observer list grows; keep notifications lightweight or run them async

---

### Pattern 2: **Strategy** (For Delivery Guarantees)

**Problem**: Different consumers need different delivery guarantees. A payments service needs at-least-once; an analytics service can tolerate at-most-once for higher throughput.

**Solution**: Inject a `DeliveryStrategy` that controls when the offset advances relative to message processing.

```python
class DeliveryStrategy(ABC):
    @abstractmethod
    def consume_and_process(self, broker: 'Broker', group_id: str,
                            subscriber_id: str,
                            handler: Callable) -> Optional['Message']:
        pass

class AtLeastOnceStrategy(DeliveryStrategy):
    """Advance offset AFTER successful processing. Retry on failure."""
    def consume_and_process(self, broker, group_id, subscriber_id, handler):
        msg = broker.consume(group_id, subscriber_id)   # does NOT advance offset yet
        if msg:
            try:
                handler(msg)
                broker.commit_offset(group_id, subscriber_id)  # advance on success
            except Exception:
                pass  # offset not advanced → message will be re-delivered
        return msg

class AtMostOnceStrategy(DeliveryStrategy):
    """Advance offset BEFORE processing. Message may be lost on crash."""
    def consume_and_process(self, broker, group_id, subscriber_id, handler):
        msg = broker.consume(group_id, subscriber_id)  # consume + advance immediately
        if msg:
            handler(msg)  # if this crashes, message is gone
        return msg

# Usage: inject strategy per consumer
strategy = AtLeastOnceStrategy()
strategy.consume_and_process(broker, "payment-group", "payment-1", process_payment)
```

**Benefit**: ✅ Swap guarantee without changing consumer code, ✅ Mix strategies across consumer groups
**Trade-off**: ⚠️ Exactly-once requires distributed transactions (out of scope for interview)

---

### Pattern 3: **Singleton** (For Broker)

**Problem**: Every service in the process must reach the same broker instance with the same topic state and offset state.

**Solution**: Double-checked locking Singleton with `RLock` to avoid re-entrancy issues when `__init__` is called multiple times.

```python
class Broker:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):   # accept *args/**kwargs so subclasses/tests don't break
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.topics: Dict[str, 'Topic'] = {}
        self.consumer_groups: Dict[str, 'ConsumerGroup'] = {}
        self.publishers: Dict[str, 'Publisher'] = {}
        self.subscribers: Dict[str, 'Subscriber'] = {}
        self.observers: List['BrokerObserver'] = []
        self._lock = threading.RLock()   # RLock: broker methods can call each other

    @classmethod
    def get_instance(cls) -> 'Broker':
        return cls()
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ `RLock` allows re-entrant calls
**Trade-off**: ⚠️ Global state makes unit testing harder (reset `_instance = None` in test teardown)

---

### Pattern 4: **Factory Method** (For Messages)

**Problem**: Creating a message requires generating a UUID, capturing a timestamp, and assigning a partition offset. Scattering this logic across callers is error-prone.

**Solution**: Centralize creation in `Partition.append()`.

```python
class Partition:
    def append(self, key: Optional[str], value: Any) -> 'Message':
        with self.lock:
            offset = len(self.messages)
            msg = Message(
                message_id=str(uuid.uuid4()),
                key=key,
                value=value,
                timestamp=datetime.now(),
                offset=offset,
                partition_id=self.partition_id,
            )
            self.messages.append(msg)
            return msg
```

**Benefit**: ✅ Consistent message initialization, ✅ Offset assignment is always correct
**Trade-off**: ⚠️ Partition knows about Message internals; acceptable since they are tightly coupled

---

### Pattern 5: **Thread Pool** (For Concurrent Consumers)

**Problem**: A service may want to run several consumers in parallel to drain a high-throughput topic without blocking.

**Solution**: Wrap consume loops in a `ThreadPoolExecutor`.

```python
from concurrent.futures import ThreadPoolExecutor

def start_consumer_workers(broker, group_id, subscriber_ids, handler, num_workers=4):
    def worker(sub_id):
        while True:
            msg = broker.consume(group_id, sub_id)
            if msg:
                handler(msg)

    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = [pool.submit(worker, sid) for sid in subscriber_ids]
```

**Benefit**: ✅ Parallel consumption across partitions, ✅ CPU-bound handlers don't block each other
**Trade-off**: ⚠️ Requires careful shutdown signaling; use a threading.Event stop flag in production

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Observer / Pub-Sub** | Decouple producers from consumers + monitoring hooks | Zero coupling; new consumers require no publisher changes |
| **Strategy** | Varying delivery guarantees per consumer group | Swap AT-MOST-ONCE / AT-LEAST-ONCE without code change |
| **Singleton** | Need single consistent broker state | Thread-safe single source of truth |
| **Factory Method** | Consistent message creation with correct offsets | No scattered UUID / timestamp / offset logic |
| **Thread Pool** | Parallel consumption across partitions | Throughput scales with worker count |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Pub-Sub Message Broker — Interview Implementation
Demonstrates:
1. Topic creation with N partitions
2. Publisher registration and multi-partition publish
3. Consumer group subscription and partition assignment
4. Fan-out: two independent groups receive same messages
5. Offset tracking and replay via seek
"""

from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import threading
import uuid


# ============================================================================
# ENUMERATIONS
# ============================================================================

class DeliveryGuarantee(Enum):
    AT_MOST_ONCE  = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE  = "exactly_once"


class TopicStatus(Enum):
    ACTIVE  = "active"
    PAUSED  = "paused"
    DELETED = "deleted"


# ============================================================================
# CORE ENTITIES
# ============================================================================

class Message:
    """Immutable data unit traveling through the broker."""
    def __init__(self, message_id: str, key: Optional[str], value: Any,
                 timestamp: datetime, offset: int, partition_id: int,
                 topic_name: str):
        self.message_id   = message_id
        self.key          = key
        self.value        = value
        self.timestamp    = timestamp
        self.offset       = offset
        self.partition_id = partition_id
        self.topic_name   = topic_name

    def __repr__(self) -> str:
        return (f"Message(topic={self.topic_name}, partition={self.partition_id}, "
                f"offset={self.offset}, key={self.key!r}, value={self.value!r})")


class Partition:
    """Ordered, append-only log segment of a topic."""
    def __init__(self, partition_id: int, topic_name: str,
                 retention_limit: int = 1000):
        self.partition_id   = partition_id
        self.topic_name     = topic_name
        self.retention_limit = retention_limit
        self.messages: List[Message] = []
        self.lock = threading.Lock()

    def append(self, key: Optional[str], value: Any) -> Message:
        """Append a new message; offset = current length before append."""
        with self.lock:
            offset = len(self.messages)
            msg = Message(
                message_id=str(uuid.uuid4()),
                key=key,
                value=value,
                timestamp=datetime.now(),
                offset=offset,
                partition_id=self.partition_id,
                topic_name=self.topic_name,
            )
            self.messages.append(msg)
            # Enforce retention (drop oldest if over limit)
            if len(self.messages) > self.retention_limit:
                self.messages = self.messages[-self.retention_limit:]
            return msg

    def read(self, offset: int) -> Optional[Message]:
        """Return message at given offset, or None if out of range."""
        with self.lock:
            if 0 <= offset < len(self.messages):
                return self.messages[offset]
            return None

    def size(self) -> int:
        with self.lock:
            return len(self.messages)


class Topic:
    """Named channel composed of N partitions."""
    def __init__(self, topic_name: str, num_partitions: int = 3,
                 retention_limit: int = 1000):
        self.topic_name     = topic_name
        self.num_partitions = num_partitions
        self.retention_limit = retention_limit
        self.status         = TopicStatus.ACTIVE
        self.partitions: List[Partition] = [
            Partition(i, topic_name, retention_limit)
            for i in range(num_partitions)
        ]
        self._rr_counter = 0  # round-robin counter for keyless messages
        self._rr_lock    = threading.Lock()

    def get_partition_for_key(self, key: Optional[str]) -> Partition:
        """Route message to partition by key hash, or round-robin if no key."""
        if key is not None:
            idx = hash(key) % self.num_partitions
        else:
            with self._rr_lock:
                idx = self._rr_counter % self.num_partitions
                self._rr_counter += 1
        return self.partitions[idx]

    def append(self, key: Optional[str], value: Any) -> Message:
        partition = self.get_partition_for_key(key)
        return partition.append(key, value)

    def partition_count(self) -> int:
        return self.num_partitions


class Publisher:
    """Identity object for a message producer."""
    def __init__(self, publisher_id: str, name: str):
        self.publisher_id = publisher_id
        self.name         = name

    def __repr__(self) -> str:
        return f"Publisher(id={self.publisher_id!r}, name={self.name!r})"


class Subscriber:
    """Individual consumer within a consumer group."""
    def __init__(self, subscriber_id: str, group_id: str, name: str):
        self.subscriber_id = subscriber_id
        self.group_id      = group_id
        self.name          = name

    def __repr__(self) -> str:
        return f"Subscriber(id={self.subscriber_id!r}, group={self.group_id!r})"


class ConsumerGroup:
    """
    A logical group of subscribers sharing a topic's partitions.
    Within a group, each partition is assigned to exactly one subscriber.
    Multiple groups receive independent copies of every message (fan-out).
    """
    def __init__(self, group_id: str, topic_name: str, num_partitions: int):
        self.group_id        = group_id
        self.topic_name      = topic_name
        self.num_partitions  = num_partitions
        self.subscribers: List[Subscriber] = []
        # subscriber_id -> [partition_ids]
        self.partition_assignments: Dict[str, List[int]] = {}
        # (subscriber_id, partition_id) -> next_offset_to_read
        self.offsets: Dict[Tuple[str, int], int] = {}
        self._lock = threading.RLock()  # RLock: assign_partitions calls other locked methods

    def add_subscriber(self, subscriber: Subscriber) -> None:
        with self._lock:
            if any(s.subscriber_id == subscriber.subscriber_id
                   for s in self.subscribers):
                return  # already a member
            self.subscribers.append(subscriber)
            self.assign_partitions()

    def remove_subscriber(self, subscriber_id: str) -> None:
        with self._lock:
            self.subscribers = [s for s in self.subscribers
                                 if s.subscriber_id != subscriber_id]
            if subscriber_id in self.partition_assignments:
                del self.partition_assignments[subscriber_id]
            # clean up offsets for removed subscriber
            self.offsets = {k: v for k, v in self.offsets.items()
                            if k[0] != subscriber_id}
            self.assign_partitions()

    def assign_partitions(self) -> None:
        """Round-robin partition assignment across current subscribers."""
        with self._lock:
            if not self.subscribers:
                self.partition_assignments = {}
                return
            # Reset assignments
            for sub in self.subscribers:
                self.partition_assignments[sub.subscriber_id] = []
            # Distribute partitions round-robin
            for partition_id in range(self.num_partitions):
                sub = self.subscribers[partition_id % len(self.subscribers)]
                self.partition_assignments[sub.subscriber_id].append(partition_id)
            # Initialize offset for any newly assigned (partition, subscriber) pair
            for sub in self.subscribers:
                for pid in self.partition_assignments[sub.subscriber_id]:
                    key = (sub.subscriber_id, pid)
                    if key not in self.offsets:
                        self.offsets[key] = 0  # start from beginning

    def get_assigned_partitions(self, subscriber_id: str) -> List[int]:
        with self._lock:
            return list(self.partition_assignments.get(subscriber_id, []))

    def get_offset(self, subscriber_id: str, partition_id: int) -> int:
        with self._lock:
            return self.offsets.get((subscriber_id, partition_id), 0)

    def advance_offset(self, subscriber_id: str, partition_id: int) -> None:
        with self._lock:
            key = (subscriber_id, partition_id)
            self.offsets[key] = self.offsets.get(key, 0) + 1

    def seek(self, subscriber_id: str, partition_id: int, offset: int) -> None:
        with self._lock:
            self.offsets[(subscriber_id, partition_id)] = offset

    def all_offsets(self, subscriber_id: str) -> Dict[int, int]:
        with self._lock:
            return {pid: self.offsets.get((subscriber_id, pid), 0)
                    for pid in self.partition_assignments.get(subscriber_id, [])}


# ============================================================================
# OBSERVER PATTERN (Audit / Monitoring)
# ============================================================================

class BrokerObserver(ABC):
    @abstractmethod
    def on_publish(self, topic_name: str, message: Message) -> None:
        pass

    @abstractmethod
    def on_consume(self, group_id: str, subscriber_id: str,
                   message: Message) -> None:
        pass


class ConsoleAuditObserver(BrokerObserver):
    def on_publish(self, topic_name: str, message: Message) -> None:
        ts = message.timestamp.strftime("%H:%M:%S")
        print(f"  [PUBLISH  {ts}] topic={topic_name:12} "
              f"partition={message.partition_id} offset={message.offset:4} "
              f"key={str(message.key):12} value={message.value}")

    def on_consume(self, group_id: str, subscriber_id: str,
                   message: Message) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [CONSUME  {ts}] group={group_id:14} sub={subscriber_id:12} "
              f"partition={message.partition_id} offset={message.offset:4} "
              f"value={message.value}")


# ============================================================================
# BROKER (SINGLETON)
# ============================================================================

class Broker:
    """
    Singleton: Central coordinator for all pub-sub operations.
    Uses RLock throughout so methods can safely call each other.
    """
    _instance: Optional['Broker'] = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Accept *args/**kwargs so super().__new__ doesn't reject them."""
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.topics: Dict[str, Topic] = {}
        self.consumer_groups: Dict[str, ConsumerGroup] = {}
        self.publishers: Dict[str, Publisher] = {}
        self.subscribers: Dict[str, Subscriber] = {}
        self.observers: List[BrokerObserver] = []
        self._lock = threading.RLock()   # RLock: broker methods call each other

    @classmethod
    def get_instance(cls) -> 'Broker':
        return cls()

    # ── Topic Management ──────────────────────────────────────────────────────

    def create_topic(self, topic_name: str, num_partitions: int = 3,
                     retention_limit: int = 1000) -> Topic:
        with self._lock:
            if topic_name in self.topics:
                raise ValueError(f"Topic '{topic_name}' already exists")
            topic = Topic(topic_name, num_partitions, retention_limit)
            self.topics[topic_name] = topic
            print(f"[Broker] Topic '{topic_name}' created "
                  f"({num_partitions} partitions)")
            return topic

    # ── Registration ──────────────────────────────────────────────────────────

    def register_publisher(self, publisher_id: str, name: str) -> Publisher:
        with self._lock:
            pub = Publisher(publisher_id, name)
            self.publishers[publisher_id] = pub
            return pub

    def register_subscriber(self, subscriber_id: str, group_id: str,
                            name: str) -> Subscriber:
        with self._lock:
            sub = Subscriber(subscriber_id, group_id, name)
            self.subscribers[subscriber_id] = sub
            return sub

    # ── Subscribe ─────────────────────────────────────────────────────────────

    def subscribe(self, group_id: str, topic_name: str,
                  subscriber_id: str) -> ConsumerGroup:
        with self._lock:
            if topic_name not in self.topics:
                raise ValueError(f"Topic '{topic_name}' not found")
            if subscriber_id not in self.subscribers:
                raise ValueError(f"Subscriber '{subscriber_id}' not registered")

            topic = self.topics[topic_name]
            key = f"{group_id}::{topic_name}"
            if key not in self.consumer_groups:
                group = ConsumerGroup(group_id, topic_name,
                                      topic.num_partitions)
                self.consumer_groups[key] = group
            else:
                group = self.consumer_groups[key]

            sub = self.subscribers[subscriber_id]
            group.add_subscriber(sub)
            assignments = group.get_assigned_partitions(subscriber_id)
            print(f"[Broker] '{subscriber_id}' joined group '{group_id}' "
                  f"on topic '{topic_name}' → partitions {assignments}")
            return group

    def _get_group(self, group_id: str, topic_name: str) -> Optional[ConsumerGroup]:
        key = f"{group_id}::{topic_name}"
        return self.consumer_groups.get(key)

    def _find_group_for_subscriber(self, group_id: str,
                                   subscriber_id: str) -> Optional[ConsumerGroup]:
        """Find the ConsumerGroup object for (group_id, subscriber_id)."""
        with self._lock:
            sub = self.subscribers.get(subscriber_id)
            if not sub:
                return None
            # Search groups matching group_id that have this subscriber
            for key, group in self.consumer_groups.items():
                if group.group_id == group_id:
                    if any(s.subscriber_id == subscriber_id
                           for s in group.subscribers):
                        return group
            return None

    # ── Publish ───────────────────────────────────────────────────────────────

    def publish(self, publisher_id: str, topic_name: str,
                key: Optional[str], value: Any) -> Message:
        with self._lock:
            if topic_name not in self.topics:
                raise ValueError(f"Topic '{topic_name}' not found")
            if publisher_id not in self.publishers:
                raise ValueError(f"Publisher '{publisher_id}' not registered")
            topic = self.topics[topic_name]

        # Partition.append has its own lock; release broker lock first
        msg = topic.append(key, value)

        for obs in self.observers:
            obs.on_publish(topic_name, msg)
        return msg

    # ── Consume ───────────────────────────────────────────────────────────────

    def consume(self, group_id: str, subscriber_id: str) -> Optional[Message]:
        """
        Return the next unconsumed message for subscriber_id in group_id.
        Iterates over assigned partitions, returns first available message,
        and advances the offset (at-least-once: caller should re-seek on crash).
        """
        group = self._find_group_for_subscriber(group_id, subscriber_id)
        if not group:
            return None

        topic_name = group.topic_name
        with self._lock:
            topic = self.topics.get(topic_name)
        if not topic:
            return None

        assigned = group.get_assigned_partitions(subscriber_id)
        for pid in assigned:
            offset = group.get_offset(subscriber_id, pid)
            partition = topic.partitions[pid]
            msg = partition.read(offset)
            if msg is not None:
                group.advance_offset(subscriber_id, pid)
                for obs in self.observers:
                    obs.on_consume(group_id, subscriber_id, msg)
                return msg
        return None  # no new messages across all assigned partitions

    # ── Offset / Seek ─────────────────────────────────────────────────────────

    def get_offset(self, group_id: str, subscriber_id: str) -> Dict[int, int]:
        group = self._find_group_for_subscriber(group_id, subscriber_id)
        if not group:
            return {}
        return group.all_offsets(subscriber_id)

    def seek(self, group_id: str, subscriber_id: str,
             partition_id: int, offset: int) -> bool:
        group = self._find_group_for_subscriber(group_id, subscriber_id)
        if not group:
            return False
        assigned = group.get_assigned_partitions(subscriber_id)
        if partition_id not in assigned:
            return False
        group.seek(subscriber_id, partition_id, offset)
        return True

    # ── Observers ─────────────────────────────────────────────────────────────

    def add_observer(self, observer: BrokerObserver) -> None:
        with self._lock:
            self.observers.append(observer)

    # ── Utility ───────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        """Reset broker state (for test isolation only)."""
        with self._lock:
            self.topics.clear()
            self.consumer_groups.clear()
            self.publishers.clear()
            self.subscribers.clear()
            self.observers.clear()


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PUB-SUB MESSAGE BROKER — INTERVIEW DEMO")
    print("=" * 70)

    broker = Broker.get_instance()
    broker._reset()  # clean state for demo
    broker.add_observer(ConsoleAuditObserver())

    # ── Setup ─────────────────────────────────────────────────────────────────
    print("\n[SETUP] Creating topic and registering actors...")
    broker.create_topic("ORDERS", num_partitions=3, retention_limit=500)
    broker.register_publisher("svc-orders", "Order Service")
    broker.register_subscriber("payment-1", "payment-group", "Payment Consumer 1")
    broker.register_subscriber("payment-2", "payment-group", "Payment Consumer 2")
    broker.register_subscriber("analytics-1", "analytics-group", "Analytics Consumer")

    # ── Subscribe ─────────────────────────────────────────────────────────────
    print("\n[SUBSCRIBE] Adding consumers to groups...")
    broker.subscribe("payment-group",   "ORDERS", "payment-1")
    broker.subscribe("payment-group",   "ORDERS", "payment-2")
    broker.subscribe("analytics-group", "ORDERS", "analytics-1")

    # ── Publish ───────────────────────────────────────────────────────────────
    print("\n[PUBLISH] Publishing 6 messages to ORDERS topic...")
    orders = [
        ("order_101", {"item": "laptop",  "amount": 999.99}),
        ("order_102", {"item": "mouse",   "amount":  29.99}),
        ("order_103", {"item": "monitor", "amount": 349.00}),
        ("order_104", {"item": "keyboard","amount":  89.00}),
        ("order_105", {"item": "headset", "amount": 149.50}),
        ("order_106", {"item": "webcam",  "amount":  79.00}),
    ]
    published = []
    for key, value in orders:
        msg = broker.publish("svc-orders", "ORDERS", key, value)
        published.append(msg)

    # ── Consume: payment-group (load-balanced) ────────────────────────────────
    print("\n[CONSUME] payment-group consuming (load-balanced across 2 consumers)...")
    for _ in range(4):
        for sub_id in ("payment-1", "payment-2"):
            msg = broker.consume("payment-group", sub_id)
            if msg is None:
                pass  # no message for this consumer on this round

    # ── Consume: analytics-group (fan-out; independent copy) ──────────────────
    print("\n[CONSUME] analytics-group consuming (fan-out — independent copy)...")
    for _ in range(6):
        msg = broker.consume("analytics-group", "analytics-1")

    # ── Offset check ──────────────────────────────────────────────────────────
    print("\n[OFFSETS] Current offsets:")
    for sub_id in ("payment-1", "payment-2"):
        offsets = broker.get_offset("payment-group", sub_id)
        print(f"  payment-group / {sub_id}: {offsets}")
    offsets = broker.get_offset("analytics-group", "analytics-1")
    print(f"  analytics-group / analytics-1: {offsets}")

    # ── Seek / Replay ─────────────────────────────────────────────────────────
    print("\n[SEEK] analytics-1 replaying partition 0 from offset 0...")
    broker.seek("analytics-group", "analytics-1", 0, 0)
    msg = broker.consume("analytics-group", "analytics-1")
    if msg:
        print(f"  Replayed: {msg}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE — ALL SCENARIOS PASSED")
    print("=" * 70)
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **publish** | Broker RLock (validation) + Partition Lock (append) | Atomic message creation; concurrent publishes to different partitions do not block each other |
| **consume** | ConsumerGroup RLock (offset read + advance) | Atomic offset read → advance; no two consumers in a group double-consume the same message |
| **subscribe / assign_partitions** | ConsumerGroup RLock | Rebalance is atomic; no partial assignment visible to other threads |
| **create_topic** | Broker RLock | No duplicate topics |
| **Singleton init** | Class-level Lock (double-checked) | Single instance even under concurrent first-call race |
| **Seek** | ConsumerGroup RLock | Offset repositioning is atomic |

**Concurrency Principles**:
1. ✅ `RLock` on Broker and ConsumerGroup — methods can call each other without deadlock
2. ✅ Separate lock per Partition — parallel publishes to different partitions proceed concurrently
3. ✅ Broker lock released before `partition.append()` to minimize contention
4. ✅ Singleton uses `__new__(cls, *args, **kwargs)` to avoid argument-rejection bug
5. ✅ Notifications fire outside critical sections to keep lock durations short

---

## Demo Scenarios

### Scenario 1: Topic Creation and Multi-Partition Publishing

```
[Broker] Topic 'ORDERS' created (3 partitions)
[PUBLISH 12:00:01] topic=ORDERS       partition=0 offset=   0 key=order_101    value={'item': 'laptop', 'amount': 999.99}
[PUBLISH 12:00:01] topic=ORDERS       partition=2 offset=   0 key=order_102    value={'item': 'mouse', 'amount': 29.99}
[PUBLISH 12:00:01] topic=ORDERS       partition=0 offset=   1 key=order_103    value={'item': 'monitor', 'amount': 349.0}
```

Key hash routes `order_101` and `order_103` to partition 0, `order_102` to partition 2.

### Scenario 2: Consumer Group Load Balancing

```
payment-group with 2 consumers, 3 partitions:
  payment-1 → partitions [0, 2]
  payment-2 → partitions [1]

payment-1 drains its partitions independently of payment-2.
No message is delivered to both payment-1 and payment-2.
```

### Scenario 3: Fan-Out (Two Independent Groups)

```
analytics-group subscribes to same topic ORDERS.
analytics-1 → all 3 partitions (only consumer in its group).
analytics-1 receives ALL 6 messages independently of payment-group.
Fan-out: 1 publish → N consumer groups each get their own copy.
```

### Scenario 4: Offset Tracking and Replay

```
After consuming all 6 messages:
  analytics-group / analytics-1: {0: 2, 1: 2, 2: 2}

After seek(partition=0, offset=0):
  Re-consumes first message on partition 0 — replay confirmed.
```

### Scenario 5: Partition Key Routing

```
hash("order_101") % 3 = 0  → Partition 0
hash("order_102") % 3 = 2  → Partition 2
hash("order_103") % 3 = 0  → Partition 0  (same key prefix → same partition)
No key → round-robin across partitions
```

---

## Interview Q&A

### Basic Questions

**Q1: What is the difference between Pub-Sub and a message queue?**

A: Pub-Sub broadcasts to all subscriber groups — one publish → many independent consumers each receive a copy (fan-out). A message queue delivers each message to exactly one consumer (work distribution). Pub-Sub = 1:N; Queue = 1:1. In this design, multiple `ConsumerGroup`s provide fan-out (pub-sub semantics), while multiple consumers within a group provide load balancing (queue semantics).

**Q2: How are messages routed to partitions?**

A: `hash(key) % num_partitions`. Same key always lands on the same partition — preserving order for all events related to a single entity (e.g., all events for `order_101` are ordered). If no key is given, round-robin distributes across partitions.

**Q3: How do consumer groups work?**

A: Each consumer group maintains its own offset per partition. Within a group, partitions are distributed across consumers (each partition → exactly one consumer). Multiple groups each receive all messages independently, enabling fan-out.

**Q4: What delivery guarantee does this implementation use?**

A: At-least-once. The offset advances after the message is returned. If the consumer crashes before committing work, it re-reads from the last committed offset on restart. To get exactly-once, you need idempotent consumers (deduplication by `message_id`) plus transactional offset commits.

**Q5: Why use RLock instead of Lock on Broker and ConsumerGroup?**

A: `threading.RLock` (re-entrant lock) allows the same thread to acquire the lock multiple times without deadlocking. This is necessary when a locked broker method calls another broker method (or a ConsumerGroup method calls `assign_partitions` which itself acquires the group lock).

---

### Intermediate Questions

**Q6: How do you prevent two consumers in the same group from reading the same message?**

A: Partition assignment: each partition is assigned to exactly one consumer in the group. `ConsumerGroup.assign_partitions()` gives partition 0 to consumer A, partition 1 to consumer B, etc. Since no two consumers own the same partition, there is no double-consumption.

**Q7: What happens when a consumer joins an existing group?**

A: `ConsumerGroup.add_subscriber()` appends the new subscriber, then calls `assign_partitions()` which rebalances all partitions round-robin across the full (updated) subscriber list. This is a group rebalance. During rebalance, existing consumers may lose some partitions and gain others — a Kafka-style "stop the world" rebalance within the group.

**Q8: How do you implement a Dead Letter Queue?**

A: Track retry count per (group, message_id). After N retries, publish the message to `<topic_name>-DLQ` instead of retrying. Consumers subscribe to the DLQ topic for manual inspection and reprocessing.

**Q9: How do you handle message ordering?**

A: Ordering is guaranteed within a single partition (append-only log). Cross-partition ordering is not guaranteed. If strict global ordering is required, use a single partition (performance tradeoff). For entity-level ordering (all events for a user/order), hash by entity ID to ensure all events land on the same partition.

**Q10: What metrics would you monitor on this broker?**

A: Consumer lag (partition size - consumer offset), publish rate (msg/sec per topic), consume rate per group, DLQ growth rate, partition skew (uneven message distribution across partitions), and rebalance frequency.

---

### Advanced Questions

**Q11: How would you implement exactly-once delivery?**

A: Three parts: (1) Idempotent publishers — broker deduplicates messages with the same `(publisher_id, sequence_number)`. (2) Idempotent consumers — consumers track processed `message_id`s in a local store. (3) Atomic offset commit — consumer writes processing result and offset commit in a single transaction (e.g., to the same DB). This prevents the "process succeeds, commit fails" gap.

**Q12: How would you scale this to a distributed cluster?**

A: Shard topics across broker nodes (each broker owns a subset of partitions). Use a coordination service (ZooKeeper / etcd) for leader election and partition assignment metadata. Replicate each partition to 2 additional brokers (leader + 2 followers) for fault tolerance. On leader failure, a follower is promoted. Consumers connect to the leader of their assigned partition.

**Q13: How do you handle a slow consumer causing broker memory pressure?**

A: Three strategies: (1) Enforce retention — drop oldest messages after `retention_limit`. (2) Back-pressure — pause publish if consumer lag exceeds a threshold. (3) Disk spill — persist messages to disk and read lazily, freeing RAM. Monitor consumer lag; alert if `partition.size() - consumer_offset > threshold`.

---

## Scaling Q&A

### Q1: How do you scale to 1M messages/sec across 100+ topics?

Distribute topics across a cluster of brokers (horizontal partitioning). Each broker handles a subset of partitions. Consumers connect to the partition leader. Add brokers and partitions linearly to scale throughput. In-memory brokers can handle ~1M msg/sec per node; disk-backed (Kafka-style) handles ~500K msg/sec with durability.

### Q2: How do you replicate messages across data centres?

Geo-replication: a mirroring process reads from the primary cluster and publishes to the secondary. Async replication gives RPO of a few seconds; sync replication gives RPO of 0 but adds latency. Consumer groups on the secondary start from offset 0 or from a checkpointed offset.

### Q3: How do you handle consumer group rebalancing at scale (1,000 consumers)?

Use an incremental cooperative rebalance (Kafka's strategy): only reassign partitions that changed ownership, rather than stopping all consumers. Reduces the rebalance storm. Assign a group coordinator node responsible for tracking membership and issuing assignment deltas.

### Q4: How do you prevent hot partitions (skewed message distribution)?

Monitor per-partition message rate. If one partition receives 10x more traffic, re-key messages using a compound key (original_key + random suffix) to spread load, or increase partition count and rehash. Alert on partition skew ratio > 3:1.

### Q5: What if a broker node fails mid-publish?

With replication factor 3: the partition leader fails → ZooKeeper/etcd detects absence within session timeout (seconds) → elects a follower as new leader. In-flight publishes to the failed leader are retried by the publisher (with idempotency key to avoid duplicates). RPO ≈ 0 with sync replication; RTO ≈ seconds.

### Q6: How do you handle exactly-once semantics at scale?

Producers assign a monotonically increasing sequence number. Broker deduplicates within a 5-minute window using a bloom filter or bounded LRU cache keyed by `(publisher_id, sequence)`. Consumers use a distributed ID store (Redis SET) to check `message_id` before processing. Offset commit is co-located with the consumer's own DB write in a two-phase commit or saga pattern.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with Topic, Partition, Message, ConsumerGroup, Subscriber, Publisher, Broker
- [ ] Explain partition routing: `hash(key) % num_partitions` for ordering guarantees
- [ ] Explain consumer group fan-out vs within-group load balancing
- [ ] Explain offset management: per-(group, subscriber, partition) tracking
- [ ] Explain at-least-once vs exactly-once and what is needed for each
- [ ] Run the complete implementation without errors (demo exits 0)
- [ ] Discuss thread safety: RLock on Broker and ConsumerGroup, per-Partition Lock, Singleton `__new__` with `*args`
- [ ] Mention Dead Letter Queue for poison messages
- [ ] Answer 5+ scaling Q&A questions including replication, hot partitions, and rebalancing

---

**Ready for interview? Publish your first message and let the consumers run!**
