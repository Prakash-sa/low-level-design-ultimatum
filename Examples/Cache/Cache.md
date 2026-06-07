# Cache System — Complete Design Guide

> Configurable in-memory cache with pluggable eviction strategies (LRU, LFU, FIFO), write policies, TTL expiration, undo/redo commands, snapshots, and event-based observability.

**Scale**: 1,000+ concurrent operations, up to 1M entries, bounded memory  
**Duration**: 75-minute interview guide  
**Focus**: Pluggable eviction/write policies, TTL expiration, thread safety, undo/redo, event observability

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
A caller stores key/value pairs in fast memory. When capacity is exceeded, the cache must intelligently evict entries using a pluggable algorithm (LRU, LFU, FIFO). Reads check TTL expiration lazily. All mutations are reversible via undo/redo, and the entire state can be snapshotted and restored. Core concerns: adaptability (swap strategies at runtime), reliability (correct eviction and expiry), and transparency (metric events).

### Core Flow
```
put(key, value) → Validate size → Evict if over capacity (strategy) → Write policy → Emit event
get(key)        → Check TTL expiry (lazy) → Update access metadata → Return value / None
delete(key)     → Remove from store → Write policy.on_delete → Emit event
                                ↓ capacity exceeded
                  choose_victim() (LRU / LFU / FIFO) → evict → emit entry_evicted
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single node or distributed?** → "Single node in-process cache; distributed is a scaling concern"
2. **Which eviction algorithms are required?** → "LRU for now, but LFU and FIFO must also be supported"
3. **Do we need TTL?** → "Yes, per-key expiration"
4. **Backing store integration?** → "Mock backing store; discuss write-through vs write-back"
5. **Concurrency requirements?** → "Mention lock strategy; single-threaded demo"
6. **Undo/redo required?** → "Yes, for set and delete operations"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Application** | Primary cache consumer | put/get/delete values, subscribe to events |
| **Admin / Operator** | Manages cache configuration | Swap eviction strategy, swap write policy, flush, snapshot/restore |
| **System** | Event emitter & metrics tracker | Emit hits/misses/evictions, expire TTL entries, enforce capacity |

### Functional Requirements (What does the system do?)

✅ **Core Operations**
  - `put(key, value, ttl?)` — insert or update an entry
  - `get(key)` — retrieve with hit/miss/expiration handling
  - `delete(key)` — remove an entry

✅ **Capacity Management**
  - Item-count limit (e.g., 1000 max entries)
  - Byte-size limit (e.g., 10 MB)
  - Automatic eviction when either limit is exceeded

✅ **Eviction Strategies**
  - LRU (Least Recently Used)
  - LFU (Least Frequently Used)
  - FIFO (First In, First Out)
  - Runtime swap without downtime (preserve entries)

✅ **TTL Expiration**
  - Per-key TTL in seconds
  - Lazy evaluation on access (no background thread in demo)

✅ **Write Policies**
  - Write-through: immediately sync to backing store
  - Write-back: mark dirty, defer sync; explicit `flush()`
  - Runtime swap (auto-flush when leaving write-back)

✅ **Undo / Redo**
  - `SetCommand` and `DeleteCommand` wrap mutations
  - `undo()` reverts last operation; `redo()` reapplies

✅ **Snapshot & Restore**
  - `take_snapshot()` — deep-copy full state
  - `restore_snapshot()` — atomic whole-system rollback

✅ **Observability**
  - Event listeners for: set, get-hit, get-miss, eviction, expiry, strategy-swap, policy-swap, snapshot, metrics

### Non-Functional Requirements (How does it perform?)

✅ **Access Performance**: O(1) average key lookup  
✅ **Eviction Performance**: O(n) victim selection (optimizable to O(1) with bucket-based LFU)  
✅ **Concurrency**: Thread-safe with locks in production; single-threaded demo  
✅ **Memory**: Bounded metadata overhead (~48 bytes per entry)  
✅ **Extensibility**: New eviction or write-policy class needs no core changes

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Max entries** | Configurable (e.g., 1000) |
| **Max bytes** | Configurable (e.g., 10 MB) |
| **TTL enforcement** | Lazy on access only (demo); background scan in production |
| **Strategy swap** | Preserve all entries; rebuild metadata |
| **Write-back flush** | Required before swapping away from write-back |
| **Undo stack depth** | Unbounded in demo; cap to 100 in production |
| **Snapshot copy** | Deep copy (full state clone) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
CacheEntry, CacheManager, EvictionStrategy, WritePolicy, Command, Snapshot, BackingStore, ...
```

### Step 2.2: Define Core Classes

#### **CacheEntry** — One stored item
```
Properties:
  - value: Any
  - size: int                  (bytes estimate)
  - created_at: float          (epoch timestamp)
  - last_access: float         (epoch timestamp)
  - frequency: int             (access counter)
  - ttl: Optional[float]       (seconds until expiry)
  - dirty: bool                (write-back pending flag)

Behaviors:
  - expired(now?): Return True if (now - created_at) >= ttl
```

#### **EvictionStrategy** — Pluggable victim-selection algorithm
```
Properties:
  - name: str

Behaviors:
  - on_insert(key, entry): Initialize metadata (e.g., set last_access)
  - on_access(key, entry): Update metadata on read
  - choose_victim(store): Return the key to evict, or None
```

#### **LRUStrategy / LFUStrategy / FIFOStrategy** — Concrete eviction algorithms
```
LRU  → choose_victim: min(last_access)
LFU  → choose_victim: min(frequency, then last_access)
FIFO → choose_victim: min(created_at)
```

#### **WritePolicy** — Pluggable persistence strategy
```
Properties:
  - name: str

Behaviors:
  - on_set(key, entry, backing_store): React to a put (sync or mark dirty)
  - on_delete(key, backing_store): Remove key from backing store
  - flush(backing_store, entries): Sync all dirty entries; return count
```

#### **Command** — Reversible mutation
```
Behaviors:
  - execute(): Apply the mutation; save previous state
  - undo(): Restore previous state
```

#### **SetCommand / DeleteCommand** — Concrete commands
```
SetCommand:
  - key, value, ttl, prev_entry (saved before execute)
  - execute → cache.set(via_command=True); save old entry
  - undo    → restore prev_entry (or delete if it was new)

DeleteCommand:
  - key, removed_entry (saved before execute)
  - execute → cache.delete(via_command=True)
  - undo    → restore removed_entry
```

#### **CacheManager** — Central orchestrator
```
Properties:
  - capacity_items: int
  - capacity_bytes: int
  - eviction_strategy: EvictionStrategy
  - write_policy: WritePolicy
  - _store: Dict[str, CacheEntry]
  - _backing_store: Dict[str, Any]
  - _listeners: List[Callable]
  - _undo_stack / _redo_stack: List[Command]
  - _metrics: Dict[str, int]

Behaviors:
  - set / get / delete
  - swap_eviction_strategy / swap_write_policy / flush
  - take_snapshot / restore_snapshot
  - undo / redo
  - add_listener / summary
```

### Step 2.3: Define Enumerations (State & Type)

```python
# No formal Enum classes in this design — eviction algorithm and write policy
# are identified by string names on strategy/policy objects:
#   strategy.name in {"lru", "lfu", "fifo"}
#   policy.name   in {"write_through", "write_back"}
#
# This keeps runtime swapping simple (restore_snapshot maps name → class).
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **CacheEntry** | Per-key metadata for eviction, TTL, dirty tracking | Can't implement any eviction or TTL |
| **EvictionStrategy** | Pluggable victim selection | Hard-coded algorithm, no runtime swap |
| **WritePolicy** | Pluggable persistence | Mixed concerns, can't switch through/back |
| **Command** | Encapsulates reversible mutations | No undo/redo |
| **CacheManager** | Central coordinator | No capacity enforcement or metric collection |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. put** ⭐ CRITICAL
```python
def set(key: str, value: Any, ttl: Optional[float] = None,
        via_command: bool = False) -> None:
    """
    Insert or update a key/value pair.

    Precondition:  key is a non-empty string; value is any serialisable object
    Postcondition: key exists in store; capacity enforced; write policy applied

    Parameters:
      key          -- lookup key
      value        -- value to cache
      ttl          -- optional time-to-live in seconds (None = no expiry)
      via_command  -- internal flag; callers must leave False

    Side Effects:
      - Evicts entries if over capacity (calls eviction_strategy.choose_victim)
      - Calls write_policy.on_set (immediately persists or marks dirty)
      - Emits 'entry_set' event
      - Appends SetCommand to undo stack (when via_command=False)
    """
```

#### **2. get** ⭐ CRITICAL
```python
def get(key: str) -> Optional[Any]:
    """
    Retrieve a value by key.

    Precondition:  key is a string
    Postcondition: access metadata updated; expired entry removed

    Returns: value if present and not expired, else None

    Failure causes:
      - Key not found    → None, emits 'entry_get_miss'
      - Key TTL expired  → entry removed, None, emits 'entry_expired' + miss

    Side Effects: updates last_access & frequency; emits 'entry_get_hit' or miss
    """
```

#### **3. delete**
```python
def delete(key: str, via_command: bool = False) -> None:
    """
    Remove a key from the cache.

    Postcondition: key absent from store; write_policy.on_delete called

    Side Effects: emits 'entry_evicted' (reason='delete');
                  appends DeleteCommand to undo stack when via_command=False
    """
```

#### **4. Strategy / Policy Controls**
```python
def swap_eviction_strategy(new_strategy: EvictionStrategy) -> None:
    """Replace eviction algorithm; rebuilds metadata on existing entries."""

def swap_write_policy(new_policy: WritePolicy) -> None:
    """Replace write policy; auto-flushes if leaving write-back."""

def flush() -> None:
    """Force-sync all dirty write-back entries to the backing store."""
```

#### **5. Snapshot / Undo**
```python
def take_snapshot() -> Dict[str, Any]:
    """Return a deep copy of the complete cache state."""

def restore_snapshot(snapshot: Dict[str, Any]) -> None:
    """Atomically replace current state with snapshot."""

def undo() -> None: ...
def redo() -> None: ...
```

### Step 3.2: Exception / Failure Model

The implementation uses silent returns and event emission rather than raising exceptions — keeping the demo interview-friendly. A production version would raise a typed hierarchy:

```python
class CacheException(Exception): ...
class CapacityError(CacheException): ...
class EvictionBlockedError(CacheException): ...
class InvalidKeyError(CacheException): ...
class SnapshotRestoreError(CacheException): ...
```

### Step 3.3: API Usage Example

```python
cache = CacheManager(
    capacity_items=5,
    capacity_bytes=100,
    eviction_strategy=LRUStrategy(),
    write_policy=WriteThroughPolicy()
)
cache.add_listener(lambda event, payload: print(f"[{event}] {payload}"))

# Basic put / get
cache.set("user:1", "Alice", ttl=60)
value = cache.get("user:1")   # "Alice"

# Strategy swap at runtime
cache.swap_eviction_strategy(LFUStrategy())

# Write-back + flush
cache.swap_write_policy(WriteBackPolicy())
cache.set("config", "dark-mode")   # marked dirty
cache.flush()                       # synced to backing store

# Snapshot & restore
snap = cache.take_snapshot()
cache.set("temp", "x")
cache.restore_snapshot(snap)        # reverts to state before "temp"

# Undo / redo
cache.set("a", 1)
cache.undo()    # removes "a"
cache.redo()    # re-inserts "a"
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
CacheManager HAS-A EvictionStrategy (1:1 Composition)
  └─ Manager owns and replaces the strategy

CacheManager HAS-A WritePolicy (1:1 Composition)
  └─ Manager owns and replaces the policy

CacheManager HAS-A store: Dict[str, CacheEntry] (1:N Composition)
  └─ Manager owns all entries

CacheManager HAS-A backing_store: Dict (1:1 Composition)
  └─ Manager simulates the durable store

CacheManager HAS-A undo_stack / redo_stack (1:N Composition)
  └─ Manager owns command history

Command REFERENCES CacheManager (Association)
  └─ Commands call back into the manager to apply/undo

CacheManager NOTIFIES Listeners via callbacks (1:N Association)
  └─ Many callables listen to cache events
```

### Step 4.2: Complete UML Class Diagram

```
┌────────────────────────────────────────────────────────┐
│            CacheManager (Singleton-style)              │
├────────────────────────────────────────────────────────┤
│ - capacity_items: int                                  │
│ - capacity_bytes: int                                  │
│ - eviction_strategy: EvictionStrategy                  │
│ - write_policy: WritePolicy                            │
│ - _store: Dict[str, CacheEntry]                        │
│ - _backing_store: Dict[str, Any]                       │
│ - _listeners: List[Callable]                           │
│ - _undo_stack / _redo_stack: List[Command]             │
│ - _metrics: Dict[str, int]                             │
├────────────────────────────────────────────────────────┤
│ + set(key, value, ttl?)                                │
│ + get(key) -> Optional[Any]                            │
│ + delete(key)                                          │
│ + swap_eviction_strategy(new_strategy)                 │
│ + swap_write_policy(new_policy)                        │
│ + flush()                                              │
│ + take_snapshot() -> Dict                              │
│ + restore_snapshot(snapshot)                           │
│ + undo() / redo()                                      │
│ + add_listener(fn) / summary() -> Dict                 │
└────────────┬──────────────────────────────────────────┘
             │ owns 1:N
    ┌────────┼────────────┬─────────────┐
    │        │            │             │
    ▼        ▼            ▼             ▼
┌─────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Store  │ │EvictionStrat.│ │ WritePolicy  │ │  Command     │
│(Dict)   │ │(LRU/LFU/FIFO)│ │(Through/Back)│ │ undo stack   │
└────┬────┘ └──────────────┘ └──────────────┘ └──────────────┘
     │
     ▼
┌──────────────────┐
│  CacheEntry      │
├──────────────────┤
│ + value: Any     │
│ + size: int      │
│ + frequency: int │
│ + last_access    │
│ + created_at     │
│ + ttl            │
│ + dirty: bool    │
├──────────────────┤
│ + expired(): bool│
└──────────────────┘

Command Pattern (Undo/Redo):
┌─────────────────────┐
│   Command (ABC)     │
│ + execute()         │
│ + undo()            │
└────┬────────────────┘
     │
  ┌──┴──────────┐
  ▼             ▼
┌──────────┐ ┌──────────┐
│SetCommand│ │DeleteCmd │
│(prev_    │ │(removed_ │
│ entry)   │ │ entry)   │
└──────────┘ └──────────┘

Observer Pattern (Events):
┌─────────────────────────────────────┐
│   Listeners (callbacks)             │
│ - entry_set, entry_get_hit/miss     │
│ - entry_evicted, entry_expired      │
│ - strategy_swapped, policy_swapped  │
│ - snapshot_taken/restored           │
│ - metrics_updated                   │
└─────────────────────────────────────┘

Memento Pattern (Snapshots):
┌──────────────────────────────────────┐
│   Snapshot (Deep Copy)               │
│ - store state                        │
│ - backing store                      │
│ - strategy/policy identifiers        │
│ - metrics baseline                   │
└──────────────────────────────────────┘
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| CacheManager → CacheEntry (store) | 1:N | Composition | Manager owns all entries |
| CacheManager → EvictionStrategy | 1:1 | Composition | One active algorithm at a time |
| CacheManager → WritePolicy | 1:1 | Composition | One active policy at a time |
| CacheManager → Command (stacks) | 1:N | Composition | Manager owns full command history |
| CacheManager → Listeners | 1:N | Association | Callbacks registered externally |
| Command → CacheManager | N:1 | Association | Commands call back into the manager |
| CacheEntry → CacheManager | N:1 | (none) | Entries are passive data objects |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For CacheManager)

**Problem**: Multiple subsystems must share one consistent view of cached data, metrics, and strategies.

**Solution**: One global CacheManager instance with thread-safe initialization (double-checked locking).

```python
class CacheManager:
    _instance = None
    _cls_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._cls_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ No conflicting capacity counts, ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test), ⚠️ Must reset `_instance` between tests

---

### Pattern 2: **Strategy** (For Eviction & Write Policy)

**Problem**: Different workloads need different eviction algorithms (LRU for recency, LFU for frequency, FIFO for fairness). Write semantics differ too (sync vs deferred).

**Solution**: `EvictionStrategy` and `WritePolicy` are abstract interfaces; concrete classes implement the variation.

```python
class EvictionStrategy:
    def on_insert(self, key, entry): pass
    def on_access(self, key, entry): pass
    def choose_victim(self, store) -> Optional[str]:
        raise NotImplementedError

class LRUStrategy(EvictionStrategy):
    def on_access(self, key, entry):
        entry.last_access = time.time()
    def choose_victim(self, store):
        return min(store.items(), key=lambda kv: kv[1].last_access)[0]
```

**Benefit**: ✅ Runtime swapping with zero downtime, ✅ Open/closed principle (add CLOCK strategy without touching CacheManager)  
**Trade-off**: ⚠️ O(n) victim scan; optimize with priority queue or bucket structure at scale

---

### Pattern 3: **Observer** (For Event-Driven Observability)

**Problem**: Cache consumers need to react to hits, misses, evictions, and metric updates without coupling cache core to specific monitoring systems.

**Solution**: A list of callable listeners receives every event with its payload.

```python
def add_listener(self, fn: Callable[[str, Dict], None]):
    self._listeners.append(fn)

def _emit_event(self, name: str, payload: Dict):
    for fn in self._listeners:
        try:
            fn(name, payload)
        except Exception:
            pass  # never let a listener crash the cache
```

**Benefit**: ✅ Pluggable monitoring (Prometheus, logging, alerting), ✅ Loose coupling  
**Trade-off**: ⚠️ Slow listeners block the cache; move to async queue in production

---

### Pattern 4: **Command** (For Undo / Redo)

**Problem**: Mutations (set/delete) need to be reversible for debugging, testing, and rollback workflows.

**Solution**: `SetCommand` and `DeleteCommand` encapsulate the mutation and its inverse, stored in undo/redo stacks.

```python
class SetCommand(Command):
    def execute(self):
        self.prev_entry = copy.deepcopy(self.cache._store.get(self.key))
        self.cache.set(self.key, self.value, self.ttl, via_command=True)

    def undo(self):
        if self.prev_entry is None:
            self.cache.delete(self.key, via_command=True)
        else:
            self.cache._direct_restore_entry(self.key, self.prev_entry)
```

**Benefit**: ✅ Fine-grained reversible history, ✅ Clean separation of command logic from cache core  
**Trade-off**: ⚠️ Deep copies add memory pressure; cap stack to ~100 in production

---

### Pattern 5: **Memento** (For Snapshot & Restore)

**Problem**: A coarse-grained rollback is needed — restoring the entire cache to a known-good state after a bad batch operation.

**Solution**: `take_snapshot()` creates a deep copy of the full store, backing store, and metadata; `restore_snapshot()` atomically swaps the whole state back.

```python
def take_snapshot(self) -> Dict[str, Any]:
    return {
        'store': copy.deepcopy(self._store),
        'backing': copy.deepcopy(self._backing_store),
        'eviction_strategy': self.eviction_strategy.name,
        'write_policy': self.write_policy.name,
        'metrics': copy.deepcopy(self._metrics),
        'timestamp': time.time(),
    }
```

**Benefit**: ✅ Atomic whole-system recovery, ✅ Strategy and policy names preserved for reconstruction  
**Trade-off**: ⚠️ O(n) deep copy cost; for large caches consider COW (copy-on-write) or incremental snapshots

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|---------------|---------|
| **Singleton** | One global cache coordinator | Coherent state, no conflicts |
| **Strategy** | Pluggable eviction & write behavior | Runtime swapping, open/closed |
| **Observer** | Lifecycle event monitoring | Decoupled observability |
| **Command** | Reversible mutations (undo/redo) | Fine-grained history, testability |
| **Memento** | Whole-system snapshot & restore | Atomic coarse-grained rollback |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Cache System - Interview Implementation
Demonstrates:
1. Basic LRU put/get & eviction
2. TTL expiration
3. Strategy swap (LRU -> LFU)
4. Write policy swap (write-through -> write-back -> flush)
5. Snapshot & restore
6. High volume insertion & metrics summary
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, List
import time
import copy
import threading

# =============================
# Data Structures & Strategies
# =============================
@dataclass
class CacheEntry:
    value: Any
    size: int
    created_at: float
    last_access: float
    frequency: int = 0
    ttl: Optional[float] = None  # seconds
    dirty: bool = False

    def expired(self, now: Optional[float] = None) -> bool:
        if self.ttl is None:
            return False
        ref = now or time.time()
        return (ref - self.created_at) >= self.ttl

# ---- Eviction Strategy Interface ----
class EvictionStrategy:
    name: str = "base"

    def on_insert(self, key: str, entry: CacheEntry) -> None:
        pass

    def on_access(self, key: str, entry: CacheEntry) -> None:
        pass

    def choose_victim(self, store: Dict[str, CacheEntry]) -> Optional[str]:
        raise NotImplementedError

class LRUStrategy(EvictionStrategy):
    name = "lru"
    def on_insert(self, key: str, entry: CacheEntry) -> None:
        entry.last_access = time.time()
    def on_access(self, key: str, entry: CacheEntry) -> None:
        entry.last_access = time.time()
    def choose_victim(self, store: Dict[str, CacheEntry]) -> Optional[str]:
        if not store:
            return None
        return min(store.items(), key=lambda kv: kv[1].last_access)[0]

class LFUStrategy(EvictionStrategy):
    name = "lfu"
    def on_insert(self, key: str, entry: CacheEntry) -> None:
        entry.frequency = 1
        entry.last_access = time.time()
    def on_access(self, key: str, entry: CacheEntry) -> None:
        entry.frequency += 1
        entry.last_access = time.time()
    def choose_victim(self, store: Dict[str, CacheEntry]) -> Optional[str]:
        if not store:
            return None
        return min(store.items(), key=lambda kv: (kv[1].frequency, kv[1].last_access))[0]

class FIFOStrategy(EvictionStrategy):
    name = "fifo"
    def on_insert(self, key: str, entry: CacheEntry) -> None:
        pass
    def on_access(self, key: str, entry: CacheEntry) -> None:
        entry.frequency += 1
    def choose_victim(self, store: Dict[str, CacheEntry]) -> Optional[str]:
        if not store:
            return None
        return min(store.items(), key=lambda kv: kv[1].created_at)[0]

# ---- Write Policy Interface ----
class WritePolicy:
    name: str = "base"
    def on_set(self, key: str, entry: CacheEntry, backing_store: Dict[str, Any]) -> None:
        raise NotImplementedError
    def on_delete(self, key: str, backing_store: Dict[str, Any]) -> None:
        raise NotImplementedError
    def flush(self, backing_store: Dict[str, Any], entries: Dict[str, CacheEntry]) -> int:
        return 0

class WriteThroughPolicy(WritePolicy):
    name = "write_through"
    def on_set(self, key: str, entry: CacheEntry, backing_store: Dict[str, Any]) -> None:
        backing_store[key] = entry.value
        entry.dirty = False
    def on_delete(self, key: str, backing_store: Dict[str, Any]) -> None:
        backing_store.pop(key, None)
    def flush(self, backing_store: Dict[str, Any], entries: Dict[str, CacheEntry]) -> int:
        return 0

class WriteBackPolicy(WritePolicy):
    name = "write_back"
    def on_set(self, key: str, entry: CacheEntry, backing_store: Dict[str, Any]) -> None:
        entry.dirty = True
    def on_delete(self, key: str, backing_store: Dict[str, Any]) -> None:
        backing_store.pop(key, None)
    def flush(self, backing_store: Dict[str, Any], entries: Dict[str, CacheEntry]) -> int:
        count = 0
        for k, e in entries.items():
            if e.dirty:
                backing_store[k] = e.value
                e.dirty = False
                count += 1
        return count

# =============================
# Command Pattern
# =============================
class Command:
    def execute(self):
        raise NotImplementedError
    def undo(self):
        raise NotImplementedError

class SetCommand(Command):
    def __init__(self, cache: 'CacheManager', key: str, value: Any, ttl: Optional[float] = None):
        self.cache = cache
        self.key = key
        self.value = value
        self.ttl = ttl
        self.prev_entry: Optional[CacheEntry] = None
    def execute(self):
        self.prev_entry = copy.deepcopy(self.cache._store.get(self.key))
        self.cache.set(self.key, self.value, self.ttl, via_command=True)
    def undo(self):
        if self.prev_entry is None:
            self.cache.delete(self.key, via_command=True)
        else:
            self.cache._direct_restore_entry(self.key, self.prev_entry)

class DeleteCommand(Command):
    def __init__(self, cache: 'CacheManager', key: str):
        self.cache = cache
        self.key = key
        self.removed_entry: Optional[CacheEntry] = None
    def execute(self):
        if self.key in self.cache._store:
            self.removed_entry = copy.deepcopy(self.cache._store[self.key])
        self.cache.delete(self.key, via_command=True)
    def undo(self):
        if self.removed_entry:
            self.cache._direct_restore_entry(self.key, self.removed_entry)

# =============================
# Cache Manager (Singleton)
# =============================
class CacheManager:
    _instance = None
    _cls_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Accept constructor args so Singleton can be re-initialised in tests
        if cls._instance is None:
            with cls._cls_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 capacity_items: int,
                 capacity_bytes: int,
                 eviction_strategy: EvictionStrategy,
                 write_policy: WritePolicy):
        # Guard against re-initialisation on repeated __init__ calls
        if getattr(self, '_initialised', False):
            return
        self._initialised = True
        self.capacity_items = capacity_items
        self.capacity_bytes = capacity_bytes
        self.eviction_strategy = eviction_strategy
        self.write_policy = write_policy
        self._store: Dict[str, CacheEntry] = {}
        self._backing_store: Dict[str, Any] = {}
        self._listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._lock = threading.RLock()  # RLock so set() can call _enforce_capacity safely
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'sets': 0,
            'deletes': 0,
            'flushed_writes': 0,
            'dirty_writes_pending': 0,
            'current_items': 0,
            'total_bytes': 0,
        }

    @classmethod
    def _reset(cls):
        """Test helper: clear singleton so a fresh instance can be created."""
        cls._instance = None

    def add_listener(self, fn: Callable[[str, Dict[str, Any]], None]):
        self._listeners.append(fn)

    def set(self, key: str, value: Any, ttl: Optional[float] = None, via_command: bool = False):
        with self._lock:
            size = self._estimate_size(value)
            now = time.time()
            if key in self._store:
                entry = self._store[key]
                entry.value = value
                entry.size = size
                entry.ttl = ttl
                entry.last_access = now
            else:
                entry = CacheEntry(value=value, size=size, created_at=now, last_access=now, ttl=ttl)
                self._store[key] = entry
                self.eviction_strategy.on_insert(key, entry)
            self._enforce_capacity()
            self.write_policy.on_set(key, entry, self._backing_store)
            self._metrics['sets'] += 1
            self._refresh_metrics()
        self._emit_event('entry_set', {'key': key, 'size': size})
        if not via_command:
            self._record_command(SetCommand(self, key, value, ttl), executed=True)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            now = time.time()
            entry = self._store.get(key)
            if entry is None:
                self._metrics['misses'] += 1
                self._refresh_metrics()
                self._emit_event('entry_get_miss', {'key': key})
                return None
            if entry.expired(now):
                self._store.pop(key, None)
                self._metrics['expirations'] += 1
                self._emit_event('entry_expired', {'key': key})
                self._metrics['misses'] += 1
                self._refresh_metrics()
                return None
            entry.last_access = now
            entry.frequency += 1
            self.eviction_strategy.on_access(key, entry)
            self._metrics['hits'] += 1
            self._refresh_metrics()
        self._emit_event('entry_get_hit', {'key': key})
        return entry.value

    def delete(self, key: str, via_command: bool = False):
        with self._lock:
            if key not in self._store:
                return
            self._store.pop(key)
            self.write_policy.on_delete(key, self._backing_store)
            self._metrics['deletes'] += 1
            self._refresh_metrics()
        self._emit_event('entry_evicted', {'key': key, 'reason': 'delete'})
        if not via_command:
            self._record_command(DeleteCommand(self, key), executed=True)

    def swap_eviction_strategy(self, new_strategy: EvictionStrategy):
        with self._lock:
            prev = self.eviction_strategy.name
            self.eviction_strategy = new_strategy
            for k, e in self._store.items():
                new_strategy.on_insert(k, e)
        self._emit_event('strategy_swapped', {'from': prev, 'to': new_strategy.name})

    def swap_write_policy(self, new_policy: WritePolicy):
        with self._lock:
            prev = self.write_policy.name
            if isinstance(self.write_policy, WriteBackPolicy) and not isinstance(new_policy, WriteBackPolicy):
                flushed = self.write_policy.flush(self._backing_store, self._store)
                self._metrics['flushed_writes'] += flushed
                self._emit_event('flushed', {'flushed_count': flushed})
            self.write_policy = new_policy
        self._emit_event('write_policy_swapped', {'from': prev, 'to': new_policy.name})
        self._refresh_metrics()

    def flush(self):
        with self._lock:
            flushed = self.write_policy.flush(self._backing_store, self._store)
            if flushed:
                self._metrics['flushed_writes'] += flushed
                self._emit_event('flushed', {'flushed_count': flushed})
                self._refresh_metrics()

    def take_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            snap = {
                'store': copy.deepcopy(self._store),
                'backing': copy.deepcopy(self._backing_store),
                'eviction_strategy': self.eviction_strategy.name,
                'write_policy': self.write_policy.name,
                'metrics': copy.deepcopy(self._metrics),
                'timestamp': time.time(),
            }
        self._emit_event('snapshot_taken', {'items': len(snap['store'])})
        return snap

    def restore_snapshot(self, snapshot: Dict[str, Any]):
        with self._lock:
            self._store = snapshot['store']
            self._backing_store = snapshot['backing']
            self._metrics = snapshot['metrics']
            es_name = snapshot['eviction_strategy']
            wp_name = snapshot['write_policy']
            self.eviction_strategy = {
                'lru': LRUStrategy(), 'lfu': LFUStrategy(), 'fifo': FIFOStrategy()
            }[es_name]
            self.write_policy = {
                'write_through': WriteThroughPolicy(), 'write_back': WriteBackPolicy()
            }[wp_name]
        self._emit_event('snapshot_restored', {})
        self._refresh_metrics()

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._metrics)

    # ---- Internal Helpers ----
    def _emit_event(self, name: str, payload: Dict[str, Any]):
        for listener_fn in self._listeners:
            try:
                listener_fn(name, payload)
            except Exception:
                pass

    def _estimate_size(self, value: Any) -> int:
        if isinstance(value, (str, bytes)):
            return len(value)
        return 1

    def _current_total_bytes(self) -> int:
        return sum(e.size for e in self._store.values())

    def _enforce_capacity(self):
        # Called inside self._lock (RLock allows re-entry)
        safety = 0
        while (len(self._store) > self.capacity_items or self._current_total_bytes() > self.capacity_bytes) and safety < 10_000:
            victim = self.eviction_strategy.choose_victim(self._store)
            if victim is None:
                self._emit_event('eviction_blocked', {})
                break
            removed = self._store.pop(victim)
            if removed.dirty:
                self.write_policy.on_delete(victim, self._backing_store)
            self._metrics['evictions'] += 1
            self._emit_event('entry_evicted', {'key': victim, 'reason': 'capacity'})
            safety += 1
        self._refresh_metrics()

    def _refresh_metrics(self):
        self._metrics['current_items'] = len(self._store)
        self._metrics['total_bytes'] = self._current_total_bytes()
        self._metrics['dirty_writes_pending'] = sum(1 for e in self._store.values() if e.dirty)
        self._emit_event('metrics_updated', copy.deepcopy(self._metrics))

    def _record_command(self, cmd: Command, executed: bool = False):
        if executed:
            self._undo_stack.append(cmd)
            self._redo_stack.clear()
            self._emit_event('command_executed', {'type': cmd.__class__.__name__})
        else:
            cmd.execute()
            self._undo_stack.append(cmd)
            self._redo_stack.clear()
            self._emit_event('command_executed', {'type': cmd.__class__.__name__})

    def undo(self):
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._refresh_metrics()
        self._emit_event('command_undone', {'type': cmd.__class__.__name__})

    def redo(self):
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        self._refresh_metrics()
        self._emit_event('command_redone', {'type': cmd.__class__.__name__})

    def _direct_restore_entry(self, key: str, entry: CacheEntry):
        with self._lock:
            self._store[key] = entry
            self._refresh_metrics()
        self._emit_event('entry_set', {'key': key, 'size': entry.size, 'restore': True})

# =============================
# Demo / Showcase
# =============================

def listener(event: str, payload: Dict[str, Any]):
    if event in {"metrics_updated"}:
        return
    print(f"  [EVENT] {event} -> {payload}")


def _make_cache(capacity_items, capacity_bytes, strategy=None, policy=None):
    """Helper: reset singleton and create a fresh CacheManager for each demo."""
    CacheManager._reset()
    return CacheManager(
        capacity_items=capacity_items,
        capacity_bytes=capacity_bytes,
        eviction_strategy=strategy or LRUStrategy(),
        write_policy=policy or WriteThroughPolicy()
    )


def demo_1_basic_lru():
    """Demo 1: Basic LRU & Eviction"""
    print("\n" + "="*70)
    print("DEMO 1: BASIC LRU & EVICTION")
    print("="*70)
    cache = _make_cache(capacity_items=5, capacity_bytes=50)
    cache.add_listener(listener)

    for i in range(7):
        cache.set(f"k{i}", f"value-{i}")
    cache.get("k3")
    cache.get("k4")
    cache.set("k_new", "new-value")
    print("Summary:", cache.summary())

def demo_2_ttl():
    """Demo 2: TTL Expiration"""
    print("\n" + "="*70)
    print("DEMO 2: TTL EXPIRATION")
    print("="*70)
    cache = _make_cache(capacity_items=100, capacity_bytes=1000)
    cache.add_listener(listener)

    cache.set("temp", "short", ttl=0.2)
    time.sleep(0.25)
    v = cache.get("temp")
    print(f"  Value after TTL expiration: {v}")
    print("Summary:", cache.summary())

def demo_3_strategy_swap():
    """Demo 3: Strategy Swap (LRU -> LFU)"""
    print("\n" + "="*70)
    print("DEMO 3: STRATEGY SWAP (LRU -> LFU)")
    print("="*70)
    cache = _make_cache(capacity_items=10, capacity_bytes=100)
    cache.add_listener(listener)

    for i in range(5):
        cache.set(f"k{i}", f"val{i}")
    for _ in range(5):
        cache.get("k0")
    for _ in range(2):
        cache.get("k1")

    cache.swap_eviction_strategy(LFUStrategy())
    cache.set("new", "item")
    print("Summary:", cache.summary())

def demo_4_write_policy():
    """Demo 4: Write Policy Swap (Through -> Back -> Flush)"""
    print("\n" + "="*70)
    print("DEMO 4: WRITE POLICY SWAP & FLUSH")
    print("="*70)
    cache = _make_cache(capacity_items=100, capacity_bytes=1000)
    cache.add_listener(listener)

    cache.set("k1", "v1")
    cache.swap_write_policy(WriteBackPolicy())
    cache.set("k2", "v2")
    cache.set("k3", "v3")
    print(f"  Dirty before flush: {cache.summary()['dirty_writes_pending']}")
    cache.flush()
    print(f"  Dirty after flush: {cache.summary()['dirty_writes_pending']}")

def demo_5_snapshot():
    """Demo 5: Snapshot & Restore"""
    print("\n" + "="*70)
    print("DEMO 5: SNAPSHOT & RESTORE")
    print("="*70)
    cache = _make_cache(capacity_items=100, capacity_bytes=1000)
    cache.add_listener(listener)

    cache.set("base1", "val1")
    cache.set("base2", "val2")
    snap = cache.take_snapshot()
    cache.set("after_snap", "val3")
    print(f"  Items after snap: {cache.summary()['current_items']}")
    cache.restore_snapshot(snap)
    print(f"  Items after restore: {cache.summary()['current_items']}")

if True:
    print("\n" + "="*70)
    print("CACHE SYSTEM - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_basic_lru()
    demo_2_ttl()
    demo_3_strategy_swap()
    demo_4_write_policy()
    demo_5_snapshot()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|--------------|------------|
| **set** | RLock (re-entrant) | Atomic insert + capacity enforce + write policy |
| **get** | RLock | Atomic TTL check + metadata update |
| **delete** | RLock | Atomic removal + write policy notification |
| **swap_eviction_strategy** | RLock | Atomic strategy replace + metadata rebuild |
| **swap_write_policy** | RLock | Auto-flush + atomic policy swap |
| **take_snapshot** | RLock | Consistent deep copy under lock |
| **Singleton init** | Class-level Lock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` used so `set()` can call `_enforce_capacity()` without deadlock
2. ✅ Events emitted *outside* the lock to keep critical sections short
3. ✅ Listeners wrapped in try/except — a slow or crashing observer never blocks the cache
4. ✅ Singleton double-checked locking prevents race during first instantiation

---

## Demo Scenarios

### Scenario 1: Basic LRU Put/Get & Eviction
```
- Set k0 → k6 (7 items, capacity 5)
- Access k3, k4 to make them recent
- Set k_new → triggers eviction of oldest (k0, k1, k2)
- Show remaining: k3, k4, k5, k6, k_new
```

### Scenario 2: TTL Expiration
```
- Set "temp" with ttl=0.2 seconds
- Wait 0.25 seconds
- Get "temp" → None (lazy expiration on access)
- Hit ratio affected (counts as miss)
```

### Scenario 3: Eviction Strategy Swap (LRU → LFU)
```
- Initially LRU
- Access k0 five times, k1 twice
- Swap to LFU
- Set new_item → LFU evicts k1 (lower frequency) not k0
```

### Scenario 4: Write Policy Swap (Through → Back → Flush)
```
- Set with write-through (immediate backing store write)
- Swap to write-back (mark dirty)
- Set multiple items (dirty_pending increases)
- Call flush() → writes all dirty, dirty_pending = 0
- Swap back to write-through
```

### Scenario 5: Snapshot & Restore
```
- Take snapshot of current state (base1, base2)
- Set after_snap item
- Restore snapshot → state reverts to 2 items
- Verifies full state recovery including metrics
```

---

## Interview Q&A

### Basic Level

**Q1: What is the main purpose of the CacheManager?**  
A: Singleton pattern ensures one global instance coordinating all cache operations (put/get/delete), strategies (LRU/LFU/FIFO), write policies (through/back), and metrics/events emission for observability.

**Q2: Why do you need multiple eviction strategies?**  
A: Different workloads benefit from different policies: LRU favors recent access patterns, LFU favors frequently accessed items, FIFO is simple for fair rotation. Pluggable Strategy pattern allows swapping at runtime without modifying core code.

**Q3: What is TTL and how is it handled?**  
A: TTL (time-to-live) is per-key expiration time. System uses lazy expiration: checks on access. If expired, entry removed, recorded as miss/eviction. Advantage: no background thread overhead. Trade-off: stale entries briefly visible.

**Q4: Why separate WritePolicy from eviction strategy?**  
A: Clear separation of concerns: eviction decides residency (which keys stay), write policy decides persistence (when to write backing store). Allows independent swapping and testing.

### Intermediate Level

**Q5: How does write-through differ from write-back?**  
A: Write-through: immediately persist to backing store on set (safe but slower). Write-back: mark entry dirty, defer writing (fast but risky if crash). System requires explicit flush() for write-back.

**Q6: How do you safely swap strategies at runtime?**  
A: Eviction strategy swap rebuilds metadata (LRU last_access, LFU frequency counters) on existing entries but preserves all data. Write policy swap flushes if leaving write-back to avoid data loss. Both emit events for monitoring.

**Q7: How does the Command pattern enable undo/redo?**  
A: SetCommand and DeleteCommand encapsulate reversible mutations, storing previous state (old entry for set, removed entry for delete). Undo stack reverses last command; redo reapplies. Each new command clears redo stack.

**Q8: How is memory managed under capacity pressure?**  
A: `_enforce_capacity()` runs after each set, repeatedly calling strategy's `choose_victim()` until item count ≤ capacity_items AND total bytes ≤ capacity_bytes. Victim removed, eviction metric incremented, event emitted.

### Advanced Level

**Q9: How would you handle concurrent access in production?**  
A: Add `threading.RLock()` around critical sections: store access, capacity enforcement, metric updates. Strategy's on_access() needs thread-safe frequency updates. Write policy flush needs atomic backing store write. Emit events outside the lock to avoid holding it during slow observers.

**Q10: How would you optimize LFU for 1M entries?**  
A: Naive LFU scans all entries to find min frequency: O(n) per eviction. Optimize: bucket-based LFU mapping frequency → ordered set of keys. Update on access is O(log n), victim selection O(1). Trade-off: higher memory for faster eviction.

**Q11: How would you scale this to a distributed cache?**  
A: Shard by key hash (consistent hashing) across multiple nodes. Each shard runs same architecture independently. Promotion strategy: hot keys replicated to fast tier (e.g., local RAM + remote store). Leader for invalidation coordination.

**Q12: What security/correctness concerns exist?**  
A: Size accounting prevents memory blowups. TTL prevents eternal residency. Snapshot restore replaces entire state (avoids partial injection). Missing: access control (who can get/set), audit logging, encryption at rest, rate limiting.

---

## Scaling Q&A

**Q1: How does eviction strategy affect performance at 100K keys?**  
A: LRU: maintains last_access timestamps, O(1) per access, victim selection O(n) scan (acceptable). At 100K, could optimize with time-bucketing or segment-based approach. LFU: similar O(n) scan, bucket optimization suggested.

**Q2: What happens if the cache fills up and strategy returns no victim?**  
A: Current implementation prevents infinite loop with safety counter (10K iterations). If no victim found, emit `eviction_blocked` event and stop accepting new keys. Production: reject new puts with error, alert ops.

**Q3: How do you prevent memory growth from undo/redo stacks?**  
A: Cap stack sizes (e.g., max 100 commands). When exceeded, pop oldest. Or implement per-session undo (discard when user disconnects). Trade-off: bounded memory vs full history.

**Q4: Can snapshot restore happen while writes are in progress?**  
A: In single-threaded demo, no. Production: acquire global write lock during restore to ensure consistency. Alternative: versioned snapshots + eventual consistency model.

**Q5: How does write-back handle crash scenarios?**  
A: Current implementation loses dirty writes. Production mitigation: WAL (write-ahead logging) per dirty write before acknowledging set(). On startup, replay log to restore dirty entries. Trade-off: write latency vs durability.

**Q6: What's the memory overhead of tracking frequency + timestamps + TTL per entry?**  
A: CacheEntry: value + size + created_at + last_access + frequency + ttl + dirty ≈ 48+ bytes per entry. For 100K entries: ~4.8 MB overhead. Acceptable. Optimization: use compact integer timestamps for memory-constrained systems.

**Q7: How do you handle TTL expiration at scale?**  
A: Current: lazy expiration on access only (stale entries accumulate). Production: background thread periodic scan + removal. Alternative: delta queue of pending expirations (O(1) add, pop nearest). Trade-off: background CPU vs stale data window.

**Q8: How would you monitor cache health metrics?**  
A: Emit `metrics_updated` event with hit rate, eviction pressure, dirty backlog. Exporter: Prometheus format. Alerts: hit ratio drops below threshold, eviction rate > threshold, dirty backlog growing unbounded.

**Q9: Can write policy swap happen mid-flush?**  
A: Current: swap triggers flush if leaving write-back. If flush in progress elsewhere, potential race. Solution: acquire lock during swap, ensure flush completes before releasing policy reference.

**Q10: How to partition cache across NUMA nodes for locality?**  
A: Shard by key hash. Each NUMA node owns subset of shards. Thread binds to NUMA node; access local shards (cache-friendly). Remote shard access incurs penalty but infrequent. Performance gain: 20–30% on NUMA systems.

**Q11: What if an eviction strategy always returns the same victim (bug)?**  
A: Safety counter prevents infinite loop. But cache keeps trying same victim, making no progress. Detect: track prev_victim across iterations. If repeated, trigger strategy fallback (e.g., FIFO) or emit alert.

**Q12: How do you handle cache stampede (1000 simultaneous misses after expiration)?**  
A: Lazy expiration causes sudden miss spike. Mitigation: probabilistic early expiration (remove entry slightly before TTL), or lock-free read during fetch (wait for one fetch result, all others use it). Trade-off: extra reads vs stampede risk.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw the UML class diagram with all relationships
- [ ] Walk through put → capacity check → eviction → write policy lifecycle
- [ ] Explain all three eviction strategies (LRU, LFU, FIFO) and when to choose each
- [ ] Explain TTL lazy expiration and its trade-off vs background scan
- [ ] Explain write-through vs write-back and the dirty flag / flush flow
- [ ] Explain how RLock prevents deadlock when set() calls _enforce_capacity()
- [ ] Walk through undo/redo: Command pattern, prev_entry, execute/undo
- [ ] Walk through snapshot/restore: deep copy, strategy name, atomic state swap
- [ ] Run the complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss optimizing LFU from O(n) scan to O(1) with bucket structure

---

**Ready for interview? Cache it, evict it, and restore it! 🔄**
