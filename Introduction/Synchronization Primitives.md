# Synchronization Primitives

Essential building blocks for thread-safe programming. Synchronization primitives enable safe access to shared resources in multi-threaded environments.

---

## 📋 Overview

Synchronization primitives control how threads interact with shared data:
- **Locking**: Mutual exclusion (only one thread at a time)
- **Signaling**: Thread-to-thread communication (condition variables, events)
- **Coordination**: Barriers, latches (thread coordination points)

**Trade-offs**:
- **Correctness**: Prevent race conditions, deadlocks
- **Performance**: Lock contention reduces throughput
- **Simplicity**: More primitives = more complexity

---

## 🔒 Locking Primitives

### Mutex (Mutual Exclusion Lock)

**Purpose**: Only one thread holds lock at a time. Others wait until released.

**Key Semantics**:
- Only the thread that acquired can release (normally)
- Non-reentrant: Same thread acquiring twice → deadlock
- Fair: Usually FIFO order (depends on OS scheduler)

**Code Example**:
```python
import threading

resource = "shared data"
lock = threading.Lock()

def access_resource(thread_id):
    print(f"Thread {thread_id} waiting for lock...")
    with lock:  # Acquire (blocking)
        print(f"Thread {thread_id} has lock")
        # Critical section: Access shared resource
        temp = resource
        # Simulate work
        import time
        time.sleep(0.1)
        print(f"Thread {thread_id} done")
    # Release (automatic on exit)

threads = [threading.Thread(target=access_resource, args=(i,)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Operations**:
```python
# Explicit acquire/release
lock.acquire()
try:
    # Critical section
    pass
finally:
    lock.release()

# Context manager (preferred)
with lock:
    # Critical section (auto-release on exit)
    pass

# Non-blocking acquire
acquired = lock.acquire(blocking=False)
if acquired:
    try:
        # Critical section
        pass
    finally:
        lock.release()
else:
    print("Could not acquire lock")
```

**Performance Considerations**:
- **Contention**: High contention → threads wait longer
- **Granularity**: Fine-grained (many locks) vs coarse-grained (few locks)
- **Lock Duration**: Keep critical section short

---

### Reentrant Lock (RLock)

**Purpose**: Same thread can acquire multiple times without deadlock. Must release same number of times.

**When to Use**:
- Recursive functions holding lock
- Nested method calls with locks
- Callback-style code where lock acquired, then callback called

**Code Example**:
```python
import threading

rlock = threading.RLock()

def recursive_func(n):
    with rlock:
        print(f"Depth {n}")
        if n > 0:
            recursive_func(n - 1)  # Recursion: same thread reacquires
        # Lock automatically released on scope exit

recursive_func(3)

# Output:
# Depth 3
# Depth 2
# Depth 1
# Depth 0
# (No deadlock!)
```

**With regular Lock (DEADLOCK)**:
```python
lock = threading.Lock()

def recursive_func(n):
    with lock:
        if n > 0:
            recursive_func(n - 1)  # DEADLOCK: cannot reacquire

# recursive_func(3)  # Hangs forever!
```

---

## 🎛️ Counting Primitives

### Semaphore

**Purpose**: Counter-based primitive. Allows N threads to access resource simultaneously.

**Mechanics**:
- Counter initialized to N
- `acquire()`: Decrements counter; blocks if counter = 0
- `release()`: Increments counter; wakes one waiting thread
- Binary Semaphore: N = 1 (similar to Mutex, but semantics differ)

**Code Example**:
```python
import threading
import time

# Limit concurrent database connections to 3
db_pool_limit = threading.Semaphore(3)

def use_database(thread_id):
    print(f"Thread {thread_id} waiting for DB connection...")
    with db_pool_limit:  # Acquire
        print(f"Thread {thread_id} using database (max 3 concurrent)")
        time.sleep(1)  # Simulate DB work
    print(f"Thread {thread_id} released connection")

threads = [threading.Thread(target=use_database, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Output shows max 3 threads in DB section simultaneously
```

**Mutex vs Semaphore**:
```python
# Mutex: Only one thread
with mutex:
    # Only one thread here at a time
    pass

# Binary Semaphore: Semantic difference (any thread can release)
sem = threading.Semaphore(1)
# Thread A acquires
# Thread B can release (unlike Mutex)
```

**Use Cases**:
- Resource pooling (connections, file handles)
- Rate limiting (N concurrent requests)
- Producer-consumer synchronization
- Barrier-like coordination

---

### Bounded Semaphore

**Variant**: Like Semaphore but `release()` raises error if counter > initial value (prevents buggy code).

```python
bounded_sem = threading.BoundedSemaphore(3)
bounded_sem.release()
bounded_sem.release()
bounded_sem.release()
bounded_sem.release()  # Raises ValueError (counter would exceed 3)
```

---

## 🔄 Signaling Primitives

### Condition Variable

**Purpose**: Thread waits for specific condition; another thread signals when condition is met.

**Operations**:
- `wait()`: Release lock, sleep until notified, reacquire lock
- `notify()`: Wake one waiting thread
- `notify_all()`: Wake all waiting threads

**Semantics**:
- Always used with lock (prevents race between check and wait)
- Spurious wakeup: Thread may wake without notification (must recheck condition)

**Code Example**:
```python
import threading
import time

data_available = False
cond = threading.Condition()

def producer():
    global data_available
    for i in range(5):
        time.sleep(1)
        with cond:
            data_available = True
            print("Producer: Data ready")
            cond.notify_all()  # Wake consumers

def consumer(thread_id):
    global data_available
    for _ in range(5):
        with cond:
            # Loop: spurious wakeup check
            while not data_available:
                print(f"Consumer {thread_id} waiting...")
                cond.wait()  # Release lock, sleep
            # Wake up: have lock, condition true
            print(f"Consumer {thread_id} got data")
            data_available = False

p = threading.Thread(target=producer, daemon=True)
c1 = threading.Thread(target=consumer, args=(1,), daemon=True)
c2 = threading.Thread(target=consumer, args=(2,), daemon=True)

p.start()
c1.start()
c2.start()

time.sleep(10)
```

**Pattern (Producer-Consumer)**:
```python
# Producer
with cond:
    prepare_data()
    cond.notify_all()

# Consumer
with cond:
    while not condition_met():
        cond.wait()
    consume_data()
```

---

### Event

**Purpose**: Simple flag-based signaling. One-time or repeated synchronization point.

**Operations**:
- `set()`: Signal event (wake all waiters)
- `clear()`: Clear signal
- `wait()`: Block until event set
- `is_set()`: Check if set

**Code Example**:
```python
import threading
import time

event = threading.Event()

def worker(thread_id):
    print(f"Worker {thread_id} waiting for start signal...")
    event.wait()  # Block until set
    print(f"Worker {thread_id} started!")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
for t in threads:
    t.start()

time.sleep(2)
print("Main: Starting workers...")
event.set()  # Wake all waiters

for t in threads:
    t.join()
```

**Use Cases**:
- Startup synchronization
- Shutdown signals
- One-time coordination
- Simple thread barriers

---

## 🎯 Optimization Primitives

### Read-Write Lock

**Purpose**: Allows multiple readers OR one writer (but not both). Optimized for read-heavy workloads.

**Behavior**:
- Multiple threads can read simultaneously
- Only one thread writes (exclusive)
- Writers may have priority (to prevent starvation)

**Implementation** (Python—not built-in):
```python
import threading

class ReadWriteLock:
    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._writers_waiting = 0
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._write_ready = threading.Condition(self._lock)
    
    def acquire_read(self):
        self._lock.acquire()
        try:
            # Wait if writers are active or waiting
            while self._writers > 0 or self._writers_waiting > 0:
                self._read_ready.wait()
            self._readers += 1
        finally:
            self._lock.release()
    
    def release_read(self):
        self._lock.acquire()
        try:
            self._readers -= 1
            if self._readers == 0:
                self._write_ready.notify_all()  # Wake writers
        finally:
            self._lock.release()
    
    def acquire_write(self):
        self._lock.acquire()
        try:
            self._writers_waiting += 1
            while self._readers > 0 or self._writers > 0:
                self._write_ready.wait()
            self._writers_waiting -= 1
            self._writers += 1
        finally:
            self._lock.release()
    
    def release_write(self):
        self._lock.acquire()
        try:
            self._writers -= 1
            self._read_ready.notify_all()  # Wake readers
            self._write_ready.notify_all()  # Wake next writer
        finally:
            self._lock.release()

# Usage
rwlock = ReadWriteLock()

def reader(thread_id):
    for _ in range(3):
        rwlock.acquire_read()
        print(f"Reader {thread_id} reading")
        # Read data
        rwlock.release_read()

def writer(thread_id):
    for _ in range(2):
        rwlock.acquire_write()
        print(f"Writer {thread_id} writing")
        # Write data
        rwlock.release_write()

threads = []
for i in range(5):
    threads.append(threading.Thread(target=reader, args=(i,)))
for i in range(2):
    threads.append(threading.Thread(target=writer, args=(i,)))

for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Performance**:
- Read-heavy: RWLock faster than regular Lock
- Write-heavy: RWLock slower (overhead of reader tracking)
- Balanced: Regular Lock often sufficient

---

### Spinlock

**Purpose**: Thread repeatedly checks if lock available (busy waiting). Efficient for very short waits.

**Mechanics**:
- No context switch (stays in user space)
- Efficient if held for microseconds
- Wasteful if held longer (burns CPU)

**Python Example** (educational; GIL limits usefulness):
```python
import time

class Spinlock:
    def __init__(self):
        self._locked = False
    
    def acquire(self):
        while self._locked:
            pass  # Spin: waste CPU until available
        self._locked = True
    
    def release(self):
        self._locked = False

# Not recommended for Python (GIL anyway)
# Better suited for kernel/systems code
```

**When to Use**:
- Lock held for < 1 microsecond
- Kernel/embedded code (no system calls)
- Single-core systems (context switch overhead high)

**In Python**: Rarely useful due to GIL; threading.Lock uses OS locks (better).

---

### Barrier

**Purpose**: Synchronization point. N threads wait until all N arrive.

**Code Example**:
```python
import threading

barrier = threading.Barrier(3)

def worker(thread_id):
    print(f"Worker {thread_id} doing work...")
    import time
    time.sleep(1)  # Simulate work
    
    print(f"Worker {thread_id} reaching barrier")
    barrier.wait()  # Block until 3 threads arrive
    
    print(f"Worker {thread_id} past barrier (all done)")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Use Cases**:
- Phase synchronization (all threads complete phase before next)
- Load balancing (wait for slowest)
- Bulk processing (process in batches)

---

## 🤔 Interview Q&A

### Q1: Mutex vs Semaphore—what's the difference?

**A**:

| Aspect | Mutex | Semaphore |
|--------|-------|-----------|
| Counter | 1 (binary) | N (counting) |
| Holder | Acquirer only | Any thread can release |
| Semantics | Ownership | Signaling |
| Threads | 1 at a time | Up to N simultaneously |
| Use Case | Critical sections | Resource pooling |

```python
# Mutex: Only one thread
with mutex:
    access_resource()

# Semaphore(3): Up to 3 threads
with semaphore:
    access_resource()

# Key: Mutex owner releases; Semaphore any thread can release
with mutex:
    pass
# Only acquirer can release

sem = Semaphore(1)
sem.acquire()
# Different thread can release (Mutex would be incorrect)
```

---

### Q2: What's the difference between Lock and RLock?

**A**:

| Feature | Lock | RLock |
|---------|------|-------|
| Reentrancy | Non-reentrant | Reentrant |
| Same Thread Reacquire | Deadlock | OK (counter) |
| Release | Once | Same count as acquire |
| Typical Use | Simple exclusion | Recursive functions |

```python
# Lock: deadlock on recursion
lock = threading.Lock()
def recursive(n):
    with lock:
        if n > 0:
            recursive(n - 1)  # DEADLOCK

# RLock: OK
rlock = threading.RLock()
def recursive(n):
    with rlock:
        if n > 0:
            recursive(n - 1)  # OK: counter tracks acquisitions
```

---

### Q3: Why use Condition Variables instead of just polling?

**A**: Condition variables are efficient; polling wastes CPU and is slow.

```python
# Bad: Polling (busy waiting)
while not condition:
    time.sleep(0.001)  # Wastes CPU, slow response

# Good: Condition variable
with cond:
    while not condition:
        cond.wait()  # Sleep until notified, no CPU waste
```

**Benefits of Condition Variables**:
- No CPU waste (thread sleeps)
- Faster wake-up (signaled, not polled)
- Scalable (efficient for many threads)

---

### Q4: What is spurious wakeup? How do you handle it?

**A**: Thread wakes from `wait()` without explicit notification. Possible on some systems.

**Solution**: Always check condition in loop, not if statement.

```python
# Wrong: if statement (vulnerable to spurious wakeup)
with cond:
    if not condition:
        cond.wait()
    process()  # May fail if spurious wakeup!

# Correct: while loop
with cond:
    while not condition:  # Recheck after wakeup
        cond.wait()
    process()  # Safe
```

---

### Q5: When would you use a Read-Write Lock?

**A**: Read-Write Lock optimizes read-heavy workloads where many threads read and few write.

```python
# Scenario: 1000 threads reading, 10 threads writing

# With regular Lock: All serialized (slow)
with lock:
    if writing:
        write_data()
    else:
        read_data()

# With RWLock: Many readers concurrent (fast)
if writing:
    rwlock.acquire_write()  # Exclusive
    write_data()
else:
    rwlock.acquire_read()   # Concurrent
    read_data()
```

**Performance**:
- 99% reads: RWLock ~10x faster
- 50% reads: RWLock overhead outweighs benefit
- 99% writes: Regular lock simpler and faster

---

### Q6: Explain the difference between notify() and notify_all().

**A**:
- `notify()`: Wake ONE waiting thread
- `notify_all()`: Wake ALL waiting threads

**Use notify()** when only one thread needs to proceed (saves wake-ups):
```python
queue = []
cond = threading.Condition()

def producer():
    with cond:
        queue.append(data)
        cond.notify()  # Only one consumer needs to wake

def consumer():
    with cond:
        while not queue:
            cond.wait()
        item = queue.pop(0)
```

**Use notify_all()** when condition affects multiple threads:
```python
# Multiple threads waiting on same condition
def producer():
    with cond:
        data_ready = True
        cond.notify_all()  # Multiple consumers may proceed

def consumer():
    with cond:
        while not data_ready:
            cond.wait()
        process_data()
```

---

### Q7: What's the purpose of a Barrier? When do you use it?

**A**: Barrier is synchronization point where N threads wait until all N arrive.

**Use Cases**:
- Phase synchronization: Complete phase before next
- Parallel algorithms: Wait for slowest thread
- Bulk operations: Process in batches

```python
barrier = threading.Barrier(4)

def stage1():
    do_work()
    barrier.wait()  # Wait for all

def stage2():
    do_more_work()

# All threads complete stage1 before any starts stage2
```

**vs Condition Variable**:
```python
# Condition: Flexible, requires manual coordination
with cond:
    done_count += 1
    if done_count == N:
        cond.notify_all()

# Barrier: Automatic, cleaner for phase sync
barrier.wait()  # Blocks until N threads arrive
```

---

### Q8: How do you prevent deadlock with multiple locks?

**A**: Resource ordering + timeouts prevent deadlock.

**Strategy 1: Resource Ordering** (prevent circular wait):
```python
lock_a = threading.Lock()
lock_b = threading.Lock()

# Always acquire in same order (e.g., A before B)
def safe_function():
    with lock_a:
        with lock_b:
            access_shared_resource()

# Never:
# with lock_b:
#     with lock_a:  <- Different order! Deadlock possible
```

**Strategy 2: Timeouts**:
```python
if lock_a.acquire(timeout=1.0):
    try:
        if lock_b.acquire(timeout=1.0):
            try:
                access_resource()
            finally:
                lock_b.release()
        else:
            print("Could not acquire B, backing off")
            # Retry or handle
    finally:
        lock_a.release()
else:
    print("Could not acquire A")
```

---

### Q9: Compare blocking vs non-blocking lock acquisition.

**A**:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Blocking** | Wait until lock available | Most common; simplicity |
| **Non-blocking** | Return immediately | Avoid deadlock, responsive UI |

```python
# Blocking (default)
with lock:  # Waits if necessary
    access_resource()

# Non-blocking
acquired = lock.acquire(blocking=False)
if acquired:
    try:
        access_resource()
    finally:
        lock.release()
else:
    print("Could not acquire lock")

# Timeout (hybrid)
acquired = lock.acquire(timeout=1.0)
if acquired:
    try:
        access_resource()
    finally:
        lock.release()
else:
    print("Timeout: Could not acquire lock")
```

---

### Q10: What's lock contention? How do you measure and reduce it?

**A**: Lock contention = threads competing for same lock = performance degradation.

**Symptoms**:
- Threads wait long for locks
- Adding threads makes throughput worse (Amdahl's Law)
- High CPU but low throughput (context switching)

**Measurement**:
```python
import threading
import time

lock = threading.Lock()
contention_count = 0

def measure_contention():
    global contention_count
    start = time.time()
    with lock:
        acquired = time.time()
    end = acquired
    
    wait_time = acquired - start
    if wait_time > 0.01:
        contention_count += 1

# Reduction Strategies

# 1. Fine-grained locks (partition data)
class PartitionedCounter:
    def __init__(self, partitions=16):
        self.buckets = [{'count': 0, 'lock': threading.Lock()} for _ in range(partitions)]
    
    def increment(self, thread_id):
        bucket = self.buckets[thread_id % len(self.buckets)]
        with bucket['lock']:
            bucket['count'] += 1

# 2. Short critical section
def process_item():
    # Prepare outside lock
    prepared = expensive_computation()
    
    with lock:
        # Only critical section in lock
        shared_data.update(prepared)

# 3. Lock-free data structures
from queue import Queue
q = Queue()  # Thread-safe, no explicit locks
q.put(item)

# 4. Read-Write Lock for read-heavy
if write:
    rwlock.acquire_write()
else:
    rwlock.acquire_read()  # Concurrent
```

---

### Q11: Design a thread-safe cache with Read-Write Lock.

**A**:
```python
import threading

class CacheRWLock:
    def __init__(self):
        self.cache = {}
        self.rwlock = ReadWriteLock()
    
    def get(self, key):
        self.rwlock.acquire_read()
        try:
            return self.cache.get(key)
        finally:
            self.rwlock.release_read()
    
    def put(self, key, value):
        self.rwlock.acquire_write()
        try:
            self.cache[key] = value
        finally:
            self.rwlock.release_write()
    
    def invalidate(self, key):
        self.rwlock.acquire_write()
        try:
            if key in self.cache:
                del self.cache[key]
        finally:
            self.rwlock.release_write()

# Many readers (fast), few writers (exclusive)
cache = CacheRWLock()

def reader(thread_id):
    for _ in range(100):
        value = cache.get(f"key_{thread_id}")

def writer():
    for i in range(10):
        cache.put(f"key_{i}", f"value_{i}")
```

---

### Q12: How do you handle exceptions in critical sections?

**A**: Always ensure lock released on exception (use context manager or finally).

```python
# Good: Context manager (auto-release)
with lock:
    risky_operation()  # If raises, lock auto-released

# Also good: try-finally
lock.acquire()
try:
    risky_operation()
finally:
    lock.release()  # Guaranteed release

# Bad: Lock never released on exception
lock.acquire()
risky_operation()  # If exception, lock held forever!
lock.release()
```

---

## 📚 Summary Table

| Primitive | Purpose | Holders | Wait Type |
|-----------|---------|---------|-----------|
| **Mutex** | Mutual exclusion | 1 | Blocking |
| **RLock** | Reentrant mutex | 1 (same thread) | Blocking |
| **Semaphore** | N-way access | Up to N | Blocking |
| **Condition** | Wait for condition | 1 + waiters | Blocking, signaled |
| **Event** | Simple signal | All | Blocking, signaled |
| **RWLock** | Multiple readers | Many readers OR 1 writer | Blocking |
| **Barrier** | Phase sync | All N | Blocking |
| **Spinlock** | Busy wait | 1 | CPU spin |

---

## ✅ Best Practices

1. **Use Context Managers**: Always `with lock:` for auto-release
2. **Minimize Critical Section**: Short lock duration
3. **Consistent Ordering**: Always acquire locks in same order (prevent deadlock)
4. **Avoid Nested Locks**: If necessary, use ordered/timed
5. **Check Condition in Loop**: Handle spurious wakeups
6. **Prefer Higher-Level Abstractions**: Queue, ThreadPoolExecutor over raw locks
7. **Document Lock Semantics**: What does each lock protect?
8. **Profile Contention**: Measure before optimizing

---

## 💡 Key Takeaways

- **Mutex**: Simplest; use for basic mutual exclusion
- **Semaphore**: For resource pooling and coordination
- **Condition Variable**: For complex coordination (producer-consumer)
- **RWLock**: When workload is read-heavy
- **Barrier**: For phase-based parallel algorithms
- **Deadlock Prevention**: Resource ordering + timeouts
- **Performance**: Profile contention; fine-grained locks or lock-free structures
