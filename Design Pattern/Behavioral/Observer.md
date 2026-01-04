# Observer Pattern

> Define a one-to-many dependency between objects so that when one object changes state, all its dependents are notified automatically.

---

## Problem

You need to notify multiple objects about state changes without coupling them tightly. For example, when a YouTube channel uploads a video, all subscribers should be notified.

## Solution

The Observer pattern defines a Subject that maintains a list of Observers. When state changes, the Subject notifies all Observers automatically.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable

# Observer interface
class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: Any):
        pass

# Subject interface
class Subject:
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event: str, data: Any):
        for observer in self._observers:
            observer.update(event, data)

# Concrete Subject: YouTube Channel
class YouTubeChannel(Subject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.videos: List[str] = []
    
    def upload_video(self, title: str):
        self.videos.append(title)
        self.notify("video_uploaded", {"channel": self.name, "title": title})
    
    def get_subscriber_count(self) -> int:
        return len(self._observers)

# Concrete Observer: User
class YouTubeUser(Observer):
    def __init__(self, name: str):
        self.name = name
    
    def update(self, event: str, data: Any):
        if event == "video_uploaded":
            print(f"🔔 {self.name}: New video from {data['channel']}: {data['title']}")
        elif event == "live_stream":
            print(f"🔴 {self.name}: Live stream started: {data['title']}")

# Concrete Observer: Email Notifier
class EmailNotifier(Observer):
    def __init__(self, email: str):
        self.email = email
    
    def update(self, event: str, data: Any):
        print(f"📧 Email sent to {self.email}: {event} - {data}")

# Concrete Observer: Analytics Logger
class AnalyticsLogger(Observer):
    def update(self, event: str, data: Any):
        print(f"📊 Logged event: {event} with data: {data}")

# Functional approach (using callbacks)
class EventEmitter:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def off(self, event: str, callback: Callable):
        if event in self._listeners:
            self._listeners[event].remove(callback)
    
    def emit(self, event: str, *args, **kwargs):
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(*args, **kwargs)

# Demo
if __name__ == "__main__":
    # Observer pattern (class-based)
    channel = YouTubeChannel("TechTalk")
    
    user1 = YouTubeUser("Alice")
    user2 = YouTubeUser("Bob")
    email_notifier = EmailNotifier("admin@example.com")
    analytics = AnalyticsLogger()
    
    channel.attach(user1)
    channel.attach(user2)
    channel.attach(email_notifier)
    channel.attach(analytics)
    
    print("=== Class-based Observer ===")
    channel.upload_video("Design Patterns Explained")
    print(f"Subscribers: {channel.get_subscriber_count()}\n")
    
    # Event Emitter (functional approach)
    emitter = EventEmitter()
    
    def on_login(username):
        print(f"✅ {username} logged in")
    
    def log_event(username):
        print(f"📝 Event logged for {username}")
    
    emitter.on("login", on_login)
    emitter.on("login", log_event)
    
    print("=== Functional Observer ===")
    emitter.emit("login", "charlie")
```

---

## Key Concepts

- **Subject**: Maintains list of observers, notifies on state change
- **Observer**: Interface for receiving notifications
- **Loose Coupling**: Subject and Observer don't know details about each other
- **Push vs Pull**: Subject can push data or Observer can pull data

---

## When to Use

✅ One-to-many dependencies between objects  
✅ Need to notify multiple objects without knowing who they are  
✅ Building event-driven systems  
✅ Publish-subscribe messaging  

---

## Interview Q&A

**Q1: What's the difference between Observer and Pub/Sub?**

A:
- **Observer**: Tightly coupled - Observer knows about Subject directly
- **Pub/Sub**: Loosely coupled - Publisher and Subscriber use a Message Broker as intermediary

```python
# Observer (tight coupling)
subject.attach(observer)  # Observer registers with Subject

# Pub/Sub (loose coupling)
message_broker.publish("event_name", data)  # Publisher sends to broker
message_broker.subscribe("event_name", handler)  # Subscriber receives from broker
```

---

**Q2: How do you handle exceptions in Observer notifications?**

A: Wrap in try-catch to prevent one failing observer from breaking others:

```python
def notify(self, event: str, data: Any):
    for observer in self._observers:
        try:
            observer.update(event, data)
        except Exception as e:
            print(f"Error notifying observer: {e}")
```

---

**Q3: How would you implement weak references to prevent memory leaks?**

A:
```python
import weakref

class Subject:
    def __init__(self):
        self._observers = []  # Will store weak references
    
    def attach(self, observer: Observer):
        weak_observer = weakref.ref(observer, self._on_observer_deleted)
        self._observers.append(weak_observer)
    
    def _on_observer_deleted(self, weak_ref):
        self._observers.remove(weak_ref)
    
    def notify(self, event: str, data: Any):
        for weak_observer in self._observers:
            observer = weak_observer()
            if observer is not None:
                observer.update(event, data)
```

---

**Q4: How do you prevent infinite notification loops?**

A: Use a flag to track if we're in a notification cycle:

```python
class Subject:
    def __init__(self):
        self._observers = []
        self._notifying = False
    
    def notify(self, event: str, data: Any):
        if self._notifying:
            return  # Prevent recursive notifications
        
        self._notifying = True
        try:
            for observer in self._observers:
                observer.update(event, data)
        finally:
            self._notifying = False
```

---

**Q5: How would you implement observer priorities (some observers get notified first)?**

A:
```python
class PriorityObserver(Observer, ABC):
    def __init__(self, priority: int = 0):
        self.priority = priority

class PrioritySubject(Subject):
    def attach(self, observer: PriorityObserver):
        self._observers.append(observer)
        self._observers.sort(key=lambda o: o.priority, reverse=True)
    
    def notify(self, event: str, data: Any):
        for observer in self._observers:
            observer.update(event, data)
```

---

## Trade-offs

✅ **Pros**: Loose coupling, dynamic relationships, supports many observers  
❌ **Cons**: Memory leaks if not cleaned up, observer notifications non-deterministic, performance overhead

---

## Real-World Examples

- **Event listeners** (React component updates)
- **Message queues** (Kafka, RabbitMQ)
- **Database triggers** (notify on INSERT/UPDATE)
- **Notification systems** (email, SMS, push notifications)
