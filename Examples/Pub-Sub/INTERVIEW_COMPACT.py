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
