# Concurrency in Python

Concurrency allows multiple tasks to execute seemingly simultaneously, improving performance and responsiveness. This guide covers synchronization primitives, patterns, and best practices.

---

## 📋 Overview

**Concurrency Models**:
- **Threading**: Multiple threads in same process, shared memory, OS-scheduled
- **Async/Await**: Single-threaded, cooperative multitasking via event loop
- **Multiprocessing**: Separate processes, isolated memory, true parallelism

**Python's GIL** (Global Interpreter Lock):
- Only one thread executes Python bytecode at a time
- Affects CPU-bound work; I/O operations release the GIL
- Async/await and multiprocessing bypass this

---

## 🔒 Synchronization Primitives

### Mutex / Lock

**Purpose**: Mutually exclusive lock. Only one thread holds it at a time. Protects critical sections from race conditions.

**Key Concepts**:
- Acquire: Thread locks; others wait
- Release: Thread unlocks; one waiter gets lock
- Reentrant Lock: Same thread can acquire multiple times (must release same number)

**Code Example**:
```python
import threading

balance = 0
lock = threading.Lock()

def increment():
    global balance
    with lock:  # Acquire lock (blocking if unavailable)
        temp = balance
        temp += 1
        balance = temp
        # Implicit release on exit

# Without lock, race condition possible:
# Thread 1: read (0) -> increment (1)
# Thread 2: read (0) -> increment (1)  <- Lost update!
# Result: balance = 1 (should be 2)

threads = [threading.Thread(target=increment) for _ in range(100)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(balance)  # With lock: 100, Without: Random (usually < 100)
```

**Performance**:
- Contention: High lock contention = threads waiting = worse performance
- Granularity: Fine-grained locks (more locks) = more overhead; coarse-grained (fewer locks) = less parallelism

---

### Semaphore

**Purpose**: Controls access to resource with counter. Allows up to N threads simultaneously.

**Key Concepts**:
- Binary semaphore: Counter = 1 (similar to Mutex, but different semantics)
- Counting semaphore: Counter = N (N threads can proceed)
- acquire() (or `with sem`): Decrements counter; blocks if 0
- release(): Increments counter; wakes one waiting thread

**Code Example**:
```python
import threading
import time

# Limit to 3 concurrent database connections
db_connections = threading.Semaphore(3)

def access_db(thread_id):
    print(f"Thread {thread_id} waiting for connection...")
    with db_connections:  # Acquire semaphore
        print(f"Thread {thread_id} connected")
        time.sleep(1)  # Simulate DB work
    print(f"Thread {thread_id} released connection")

threads = [threading.Thread(target=access_db, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Output shows max 3 threads accessing simultaneously
```

**Use Cases**:
- Resource pooling (database connections, thread pools)
- Rate limiting
- Producer-consumer buffer coordination

---

### Condition Variable

**Purpose**: Thread waits for a condition to be true; another thread signals when condition is met.

**Key Concepts**:
- wait(): Release lock, wait for notification, reacquire lock
- notify(): Wake one waiting thread
- notify_all(): Wake all waiting threads

**Code Example**:
```python
import threading

queue = []
cond = threading.Condition()

def producer():
    for i in range(5):
        with cond:
            queue.append(i)
            print(f"Produced {i}")
            cond.notify()  # Wake consumer

def consumer():
    while True:
        with cond:
            cond.wait()  # Wait for notification
            if queue:
                item = queue.pop(0)
                print(f"Consumed {item}")

p = threading.Thread(target=producer, daemon=True)
c = threading.Thread(target=consumer, daemon=True)
p.start()
c.start()
p.join()
```

---

## 🎯 Concurrency Patterns

### Producer-Consumer

**Purpose**: Decouple producer (creates data) from consumer (processes data) using shared buffer.

**Benefits**:
- Producers don't wait for consumers
- Consumers don't wait for producers (if buffer has data)
- Buffer smooths out speed differences

**Code Example**:
```python
import queue
import threading
import time

q = queue.Queue(maxsize=10)  # Bounded buffer

def producer():
    for i in range(20):
        print(f"Producing {i}")
        q.put(i)  # Blocks if queue is full
        time.sleep(0.1)

def consumer():
    while True:
        item = q.get()  # Blocks if queue is empty
        if item is None:  # Sentinel value to stop
            break
        print(f"Consuming {item}")
        time.sleep(0.2)
        q.task_done()  # Signal item processing complete

p = threading.Thread(target=producer)
c = threading.Thread(target=consumer)

p.start()
c.start()

p.join()
q.put(None)  # Signal consumer to stop
c.join()
```

**Thread-Safe Queue Operations**:
- `put()`: Add item (blocks if full)
- `get()`: Remove and return item (blocks if empty)
- `put_nowait()`: Add without blocking; raises `Full` if full
- `get_nowait()`: Get without blocking; raises `Empty` if empty
- `task_done()`: Signal consumer finished processing
- `join()`: Block until all items processed

---

### Read-Write Lock

**Purpose**: Allows multiple readers OR one writer (but not both). Optimized for read-heavy workloads.

**Key Concepts**:
- Multiple readers can hold lock simultaneously
- Writer acquires exclusive lock (no readers, no other writers)
- Readers have priority OR writers have priority (fairness trade-off)

**Code Example**:
```python
import threading

class ReadWriteLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._read_count = 0
        self._read_ready = threading.Condition(self._lock)
    
    def acquire_read(self):
        self._lock.acquire()
        self._read_count += 1
        self._lock.release()
    
    def release_read(self):
        self._lock.acquire()
        self._read_count -= 1
        if self._read_count == 0:
            self._read_ready.notify_all()
        self._lock.release()
    
    def acquire_write(self):
        self._lock.acquire()
        while self._read_count > 0:
            self._read_ready.wait()
    
    def release_write(self):
        self._lock.release()

# Usage
rwlock = ReadWriteLock()

def reader(thread_id):
    for _ in range(5):
        rwlock.acquire_read()
        print(f"Reader {thread_id} reading")
        # Read shared resource
        rwlock.release_read()

def writer(thread_id):
    for _ in range(3):
        rwlock.acquire_write()
        print(f"Writer {thread_id} writing")
        # Write shared resource
        rwlock.release_write()
```

---

### Thread Pool

**Purpose**: Reuses worker threads to execute tasks, avoiding overhead of creating threads for every task.

**Benefits**:
- Avoids thread creation/destruction overhead
- Limits concurrent thread count
- Queues excess tasks automatically
- Better resource utilization

**Code Example**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def slow_task(n):
    time.sleep(1)
    return n * n

# Use context manager for auto cleanup
with ThreadPoolExecutor(max_workers=4) as executor:
    # Submit tasks
    futures = [executor.submit(slow_task, i) for i in range(10)]
    
    # Retrieve results
    for future in as_completed(futures):
        result = future.result()
        print(f"Result: {result}")

# Alternative: map (maintains order)
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(slow_task, range(10)))
    print(results)
```

**Common Patterns**:
```python
# Submit once, get results later
executor = ThreadPoolExecutor(max_workers=4)
future = executor.submit(func, arg)
result = future.result(timeout=10)  # Blocks; raises TimeoutError

# Map with timeout
futures = executor.map(func, iterable, timeout=5)

# as_completed: process as results arrive
for future in as_completed(futures, timeout=30):
    try:
        result = future.result()
    except Exception as e:
        print(f"Task failed: {e}")
```

---

## ⚠️ Anti-Patterns & Pitfalls

### Deadlock

**Definition**: Two or more threads blocked forever, each waiting for resource held by the other.

**Example**:
```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1_work():
    with lock_a:
        print("Thread 1 acquired A")
        # Simulate some work
        import time
        time.sleep(0.1)
        with lock_b:  # Deadlock if Thread 2 holds B
            print("Thread 1 acquired B")

def thread_2_work():
    with lock_b:
        print("Thread 2 acquired B")
        import time
        time.sleep(0.1)
        with lock_a:  # Deadlock if Thread 1 holds A
            print("Thread 2 acquired A")

# Can deadlock:
# T1: acquire(A) -> wait(B)
# T2: acquire(B) -> wait(A)
# FREEZE!

t1 = threading.Thread(target=thread_1_work)
t2 = threading.Thread(target=thread_2_work)
t1.start()
t2.start()
# t1.join() # May hang forever
```

**Prevention Strategies**:
1. **Resource Ordering**: Always acquire locks in same order
2. **Timeouts**: Acquire with timeout; retry or fail gracefully
3. **Avoid Nested Locks**: Minimize number of locks held simultaneously
4. **Lock Hierarchy**: Define priority; lower priority waits for higher

**Fixed Example**:
```python
# Always acquire A before B
def thread_1_work():
    with lock_a:
        with lock_b:
            print("Thread 1 has both locks")

def thread_2_work():
    with lock_a:  # Same order!
        with lock_b:
            print("Thread 2 has both locks")
```

---

### Race Condition

**Definition**: Outcome depends on timing of thread execution; unpredictable result.

**Example**:
```python
# NOT thread-safe
counter = 0

def increment():
    global counter
    # Three steps: read, increment, write
    temp = counter      # Read
    temp = temp + 1     # Increment
    counter = temp      # Write
    # Race: Two threads can both read 0, both write 1

def decrement():
    global counter
    temp = counter
    temp = temp - 1
    counter = temp

# Interleaving:
# T1: read(0) -> T2: read(0) -> T1: write(1) -> T2: write(-1)
# Result: -1 (should be 0)
```

**Fix**:
```python
import threading
counter = 0
lock = threading.Lock()

def increment():
    global counter
    with lock:
        counter += 1  # Atomic within lock

def decrement():
    global counter
    with lock:
        counter -= 1
```

---

### Busy Waiting

**Anti-Pattern**: Thread repeatedly polls in a loop instead of waiting for notification.

```python
# BAD: Busy waiting
def consumer():
    while not queue:  # Wastes CPU spinning
        time.sleep(0.001)
    item = queue.pop()

# GOOD: Use condition variable or queue
def consumer():
    with queue_lock:
        cond.wait()  # Sleep until notified
        item = queue.pop()
```

---

### Lock Contention

**Issue**: Too many threads competing for same lock = poor performance.

**Symptoms**:
- Threads spend more time waiting than working
- Adding threads makes things slower (Amdahl's Law)
- High CPU usage but low throughput

**Solutions**:
1. **Fine-grained locks**: Separate locks for different data structures
2. **Lock-free data structures**: Use atomics, compare-and-swap
3. **Partitioning**: Divide data; each partition has own lock
4. **Reduce lock duration**: Minimize critical section

---

## 🔧 Advanced Concepts

### Atomic Variables

**Purpose**: Thread-safe single variable operations without explicit locking.

**Note**: Python integers are atomic for single operations due to GIL, but multi-step logic requires locks.

```python
import threading

# Python: Single operations on built-in types are atomic due to GIL
counter = 0
lock = threading.Lock()

# Atomic (GIL protects)
counter = 1

# NOT atomic (multiple steps)
counter += 1  # Actually: read, add, write

# Better: Use Lock
with lock:
    counter += 1

# Alternative: queue.Queue is thread-safe
from queue import Queue
q = Queue()
q.put(1)  # Atomic
item = q.get()  # Atomic
```

**Languages with true atomic variables** (Java, C++):
```java
// Java
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();  // Atomic, lock-free
```

---

### Future / Promise

**Purpose**: Placeholder for result that will be available in future.

**States**:
- Pending: Operation in progress
- Resolved: Operation succeeded, result available
- Rejected: Operation failed, exception set

**Code Example**:
```python
from concurrent.futures import ThreadPoolExecutor, Future
import time

executor = ThreadPoolExecutor(max_workers=2)

def slow_computation(n):
    time.sleep(2)
    if n < 0:
        raise ValueError("Negative number")
    return n * n

# Submit task, get Future immediately
future = executor.submit(slow_computation, 5)

# Do other work while computation runs
print("Computation started...")
print("Doing other work...")

# Later: get result (blocks if not ready)
try:
    result = future.result(timeout=3)
    print(f"Result: {result}")
except TimeoutError:
    print("Computation took too long")
except Exception as e:
    print(f"Computation failed: {e}")

executor.shutdown()
```

**Future Methods**:
- `result(timeout=None)`: Block and get result; raise exception if failed
- `done()`: Check if computation finished
- `cancel()`: Try to cancel (fails if already running)
- `add_done_callback(fn)`: Execute callback when done

---

## 🤔 Interview Q&A

### Q1: What's the difference between Lock and RLock?

**A**: 
- **Lock**: Once acquired, cannot be acquired again by same thread (deadlock if attempted)
- **RLock** (Reentrant): Same thread can acquire multiple times; must release same number
- Use RLock for recursive functions or nested lock scenarios

```python
import threading

lock = threading.Lock()
rlock = threading.RLock()

def recursive_lock_func(n):
    with lock:  # Will deadlock on recursion!
        if n > 0:
            recursive_lock_func(n - 1)

def recursive_rlock_func(n):
    with rlock:  # OK: same thread acquires multiple times
        if n > 0:
            recursive_rlock_func(n - 1)
```

---

### Q2: How do you prevent deadlock?

**A**: Four main strategies:

1. **Resource Ordering**: Always acquire locks in same order
```python
def safe_transfer():
    if account_a.id < account_b.id:
        with account_a.lock:
            with account_b.lock:
                pass
    else:
        with account_b.lock:
            with account_a.lock:
                pass
```

2. **Timeout**: Acquire with timeout, retry or fail
```python
acquired = lock.acquire(timeout=1.0)
if not acquired:
    print("Could not acquire lock, retrying...")
    # Retry or fail gracefully
```

3. **Avoid Circular Wait**: Prevent cycles in lock acquisition
4. **Hold Minimal Locks**: Release locks ASAP; don't nest if possible

---

### Q3: Explain the difference between Mutex and Semaphore.

**A**:
| Feature | Mutex | Semaphore |
|---------|-------|-----------|
| Counter | 1 (binary) | N (counting) |
| Holder | Only acquirer can release | Any thread can release |
| Use Case | Mutual exclusion | Resource pooling, signaling |
| Threads | 1 at a time | Up to N simultaneously |

```python
# Mutex: Only one thread accesses resource
with mutex:
    # Critical section

# Semaphore: Up to 3 threads access resource
sem = threading.Semaphore(3)
with sem:
    # Up to 3 threads here simultaneously
```

---

### Q4: What is a race condition? How do you fix it?

**A**: Race condition occurs when outcome depends on thread timing; result unpredictable.

**Example**:
```python
# Race condition:
balance = 100

def withdraw(amount):
    global balance
    if balance >= amount:  # Check
        time.sleep(0.01)   # Race: other thread can read here
        balance -= amount  # Update
        return True
    return False

# T1: check(100 >= 50) -> T2: check(100 >= 60) -> T1: balance=50 -> T2: balance=40
# Both withdraw succeed! Balance went negative.
```

**Fixes**:
1. **Lock critical section**:
```python
with lock:
    if balance >= amount:
        balance -= amount
        return True
```

2. **Atomic operations**: Use thread-safe data structures (Queue, etc.)
3. **Compare-and-swap**: Atomic read-modify-write

---

### Q5: What's the difference between blocking and non-blocking operations?

**A**:
- **Blocking**: Operation waits until result available (sleeps thread)
- **Non-blocking**: Operation returns immediately; may return "not ready" or success/failure

```python
# Blocking
queue = queue.Queue()
item = queue.get()  # Blocks if empty

# Non-blocking
try:
    item = queue.get_nowait()  # Raises Empty if no item
except queue.Empty:
    print("Queue is empty")
```

**Trade-offs**:
- Blocking: Simpler, wastes no CPU if waiting
- Non-blocking: Must poll, requires more complex logic, but responsive

---

### Q6: Explain deadlock, livelock, and starvation.

**A**:
| Issue | Definition | Example |
|-------|-----------|---------|
| **Deadlock** | Threads blocked forever waiting for each other | T1 waits for T2's lock; T2 waits for T1's lock |
| **Livelock** | Threads active but making no progress; responding to each other | T1 & T2 keep releasing/reacquiring; never proceed |
| **Starvation** | Some thread never gets resource | Low-priority thread never runs; high-priority starves it |

**Livelock Example**:
```python
# Both threads try, fail, retry endlessly
def thread_1():
    while True:
        if try_acquire(lock_a):
            if not try_acquire(lock_b):
                release(lock_a)  # Back off and retry
                time.sleep(random)

def thread_2():
    # Same logic; can keep backing off together
```

**Prevention**:
- Deadlock: Resource ordering, timeouts
- Livelock: Add randomized backoff, prioritize threads
- Starvation: Fair scheduling, priority queues

---

### Q7: What's the purpose of a thread pool? When would you use one?

**A**: Thread pool reuses worker threads to execute tasks, avoiding creation/destruction overhead.

**Benefits**:
- Reduced latency (threads already created)
- Resource limits (bounded thread count)
- Automatic task queueing
- Better CPU cache locality

**When to use**:
- Server handling many short-lived tasks
- I/O-bound work (network, files)
- Desktop app with many small jobs

```python
# Bad: Create thread per task
for task in tasks:
    t = threading.Thread(target=do_task, args=(task,))
    t.start()

# Good: Reuse thread pool
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(do_task, tasks)
```

---

### Q8: How does a Condition Variable work?

**A**: Condition Variable allows thread to wait for specific condition to be true.

**States**:
- Wait: Thread releases lock, sleeps until notified
- Notify: Wake sleeping thread; it reacquires lock
- Spurious wakeup: Thread wakes without notification (loop to recheck)

**Pattern**:
```python
cond = threading.Condition()

# Consumer
with cond:
    while not condition:  # Loop in case of spurious wakeup
        cond.wait()  # Release lock, sleep
    # Condition is true, have lock
    process_data()

# Producer
with cond:
    create_data()
    condition = True
    cond.notify_all()  # Wake consumers
```

---

### Q9: What is a Future/Promise? When do you use it?

**A**: Future is placeholder for result available in future; lets you do work while computation proceeds.

**Use cases**:
- Async operations (DB queries, HTTP requests)
- Batch processing with thread pool
- Concurrent task execution

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

# Fire and forget with future
future = executor.submit(slow_func, args)

# Do other work
do_other_work()

# Get result when ready
result = future.result()  # Blocks if not done

# Callbacks
future.add_done_callback(lambda f: print(f"Done: {f.result()}"))
```

---

### Q10: How do you handle thread exceptions?

**A**: Exceptions in threads don't crash main thread; must handle explicitly.

```python
import threading

def buggy_task():
    raise ValueError("Something went wrong")

# Exception disappears silently
t = threading.Thread(target=buggy_task)
t.start()
t.join()  # No exception raised!

# Fix: Catch and handle
def safe_task():
    try:
        buggy_task()
    except Exception as e:
        print(f"Task failed: {e}")
        # Log, retry, or signal error

# Or use ThreadPoolExecutor (captures exceptions in Future)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as executor:
    future = executor.submit(buggy_task)
    try:
        result = future.result()
    except Exception as e:
        print(f"Task failed: {e}")
```

---

### Q11: What's the difference between threading and async?

**A**:
| Aspect | Threading | Async (Coroutines) |
|--------|-----------|-------------------|
| Concurrency | OS-scheduled threads | Cooperative, single-threaded |
| GIL Impact | Affected (CPU-bound blocked) | Bypasses GIL |
| Context Switch | OS manages (implicit) | Application decides (explicit `await`) |
| Memory | ~1MB per thread | ~50KB per coroutine |
| Debugging | Hard (interleaving) | Easier (controlled execution) |
| Learning Curve | Easier | Steeper |

```python
# Threading
import threading
def fetch():
    data = requests.get(url)  # Blocks thread
    return data

t = threading.Thread(target=fetch)
t.start()

# Async
import asyncio
async def fetch():
    data = await httpx.get(url)  # Yields to event loop
    return data

asyncio.run(fetch())
```

---

### Q12: How would you implement a thread-safe counter?

**A**: Multiple approaches with trade-offs:

```python
import threading
from queue import Queue

# 1. Simple Lock
class CounterV1:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.count += 1
    
    def get(self):
        with self.lock:
            return self.count

# 2. Fine-grained: One lock per bucket (reduces contention)
class CounterV2:
    def __init__(self, buckets=16):
        self.buckets = [{'count': 0, 'lock': threading.Lock()} for _ in range(buckets)]
    
    def increment(self, thread_id):
        bucket = self.buckets[thread_id % len(self.buckets)]
        with bucket['lock']:
            bucket['count'] += 1
    
    def get(self):
        total = 0
        for bucket in self.buckets:
            with bucket['lock']:
                total += bucket['count']
        return total

# 3. Atomic (using Queue—thread-safe by design)
class CounterV3:
    def __init__(self):
        self.q = Queue(maxsize=1)
        self.q.put(0)
    
    def increment(self):
        val = self.q.get()
        self.q.put(val + 1)
    
    def get(self):
        val = self.q.get()
        self.q.put(val)
        return val
```

**Performance Comparison**:
- V1: Simple, fair contention
- V2: Low contention (better for many threads)
- V3: Simpler API, good for simple use cases

---

### Q13: What causes starvation in thread scheduling?

**A**: Starvation occurs when low-priority thread never gets CPU time due to high-priority threads.

**Causes**:
- High-priority threads always ready (spin in loop)
- Unfair lock implementation (writer preference)
- Interrupt-heavy system

**Example**:
```python
# If high-priority thread never waits, low-priority starves
def high_priority_work():
    while True:
        do_critical_work()  # Always runs, never yields

def low_priority_work():
    while True:
        do_background_work()  # May never run
```

**Prevention**:
- Fair scheduling policies
- Priority inversion prevention (boost priority of threads waiting on low-priority holders)
- Timeouts to ensure forward progress

---

## ✅ Best Practices

1. **Minimize Lock Duration**: Hold locks as short as possible
2. **Avoid Nested Locks**: Or use consistent ordering
3. **Prefer Higher-Level Abstractions**: Use Queue, ThreadPoolExecutor over raw locks
4. **Test Concurrency**: Use tools like ThreadSanitizer, Helgrind
5. **Document Thread Safety**: Clearly state which methods are thread-safe
6. **Use Immutability**: Immutable objects need no locks
7. **Avoid Busy Waiting**: Use events, conditions, queues instead
8. **Profile Lock Contention**: Identify hotspots; consider lock-free structures

---

## 📚 Summary Table

| Concept | Purpose | When to Use |
|---------|---------|------------|
| **Lock** | Mutual exclusion | Protecting shared data |
| **RLock** | Reentrant lock | Recursive functions, nested locking |
| **Semaphore** | N-way access | Resource pooling, rate limiting |
| **Condition** | Wait for condition | Producer-consumer, thread coordination |
| **Event** | One-time signal | Startup barriers, shutdown signals |
| **Queue** | Thread-safe buffer | Producer-consumer, task distribution |
| **Thread Pool** | Reuse workers | High throughput task execution |
| **Future** | Async result | Fire-and-forget operations |
| **Read-Write Lock** | Many readers, one writer | Read-heavy workloads |

---

## 💡 Key Takeaways

- **GIL limits threading** for CPU-bound work; use multiprocessing or async
- **Deadlock**: Resource ordering + timeouts prevent it
- **Race conditions**: Locks or atomic operations protect against it
- **Choose appropriate primitives**: Lock for exclusion, Semaphore for pooling, Queue for async
- **Profile before optimizing**: Measure lock contention, not just CPU
- **Async for I/O**: Lower overhead than threads for I/O-bound tasks
