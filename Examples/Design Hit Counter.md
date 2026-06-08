# Hit Counter — Complete Design Guide

> Time-windowed request counting with pluggable strategies (fixed-window, sliding-window, probabilistic), per-endpoint memory management, event-driven observability, and snapshot-based rollback.

**Scale**: 1K–1M+ requests/second per endpoint, multiple strategies for accuracy/memory trade-offs  
**Duration**: 75-minute interview guide  
**Focus**: Windowing strategies, Strategy pattern for counting algorithms, pruning discipline, memory-bounded data structures

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

A service needs to track how many times each endpoint was called within the last X seconds — for rate limiting, analytics, and observability. The accuracy/memory trade-off matters: exact timestamp storage is precise but memory-intensive; bucket aggregation is fast but coarse; probabilistic counters are tiny but approximate. The system must support swapping strategies at runtime without changing calling code.

### Core Flow

```
Record Hit → Update Strategy State → Prune (sliding only) → Update Metrics → Emit Event
                                                                                    |
Query Count ← Aggregate Hits in Window ←────────────────────────────────────────────
                     |
             Snapshot / Restore (testing & rollback)
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single machine or distributed?** → "Single-process in-memory for the interview"
2. **Exact counts or approximate?** → "Pluggable — support both exact and approximate"
3. **Multiple endpoints?** → "Yes, arbitrary string endpoint keys"
4. **Memory bounding required?** → "Yes — sliding window must prune old data"
5. **Observability / monitoring needed?** → "Yes — emit events for external listeners"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Service / API Layer** | Records hits and queries counts | `record_hit("/api")`, `query_hits("/api", 10)` |
| **Monitoring System** | Listens to lifecycle events | Subscribe to `hit_recorded`, `pruned`, `strategy_swapped` |
| **Admin / Config** | Adjusts counting strategy at runtime | `swap_strategy(MorrisApproxStrategy())` |
| **Test Harness** | Captures and restores state | `take_snapshot()`, `restore_snapshot(snap)` |

### Functional Requirements (What does the system do?)

✅ **Record Hits**
  - Record a hit for a named endpoint with an optional timestamp
  - Support arbitrary string endpoint identifiers

✅ **Query Counts**
  - Return hit count for an endpoint within the last N seconds
  - Query must be non-destructive

✅ **Multiple Counting Strategies**
  - Fixed Window: divide time into equal buckets, aggregate overlapping buckets
  - Sliding Window: store per-hit timestamps, count those within the query window
  - Morris Approximation: probabilistic counter — O(1) memory per endpoint

✅ **Strategy Swap**
  - Swap counting algorithm at runtime without changing call sites
  - Incompatible strategies trigger a state reset (documented limitation)

✅ **Pruning (Memory Management)**
  - Sliding window must prune timestamps older than `max_window_s`
  - Metrics must track pruned event count

✅ **Event Emission (Observability)**
  - Fire events on `hit_recorded`, `pruned`, `strategy_swapped`, `snapshot_taken`, `metrics_updated`
  - Support multiple registered listeners

✅ **Snapshot / Restore**
  - Capture full state + metrics as a Memento
  - Restore for testing or rollback

### Non-Functional Requirements (How does it perform?)

✅ **Latency**: Record operation < 1 ms; Query operation < 10 ms  
✅ **Memory**: Bounded via pruning — sliding window never grows unboundedly  
✅ **Concurrency**: Thread-safe record/query/swap via locking  
✅ **Extensibility**: New strategies added without modifying `HitCounter`  
✅ **Observability**: Events emitted for all lifecycle transitions  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distribution** | Single-process in-memory only |
| **Accuracy** | Fixed / Sliding = exact; Morris = statistical (~±50% for large counts) |
| **Strategy swap** | Cannot losslessly convert old state — state is reset on type change |
| **Persistence** | No disk persistence; snapshots are in-memory only |
| **Clock** | Caller-supplied timestamps accepted; defaults to `time.time()` |
| **Singleton** | One `HitCounter` instance per process |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on the whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
HitCounter, CountingStrategy, FixedWindowStrategy, SlidingWindowStrategy,
MorrisApproxStrategy, Snapshot, Listener/Event, Metrics, State (per-endpoint)
```

### Step 2.2: Define Core Classes

#### **CountingStrategy** — Abstract base for all counting implementations

```
Properties:
  - (none — pure behavior)

Behaviors:
  - name(): Returns class name for logging
  - record(state, endpoint, ts): Record a hit in the strategy's internal representation
  - query(state, endpoint, now, last_seconds): Return hit count within window
  - prune(state, endpoint, now): Remove stale entries; returns pruned count
  - memory_entries(state): Return total tracked entries across all endpoints
```

#### **FixedWindowStrategy** — Bucket-based aggregation

```
Properties:
  - window_size_s: int (bucket granularity in seconds, e.g. 10)

Behaviors:
  - record(): bucket_key = floor(ts / window_size_s); increment bucket counter
  - query(): sum buckets where start_bucket <= key <= end_bucket
  - memory_entries(): total number of non-empty buckets across all endpoints
```

#### **SlidingWindowStrategy** — Per-hit timestamp list

```
Properties:
  - max_window_s: int (maximum retention window for pruning, e.g. 60)

Behaviors:
  - record(): append ts to endpoint's timestamp list
  - prune(): remove timestamps older than (now - max_window_s)
  - query(): count timestamps >= (now - last_seconds)
  - memory_entries(): total timestamps stored across all endpoints
```

#### **MorrisApproxStrategy** — Probabilistic counter

```
Properties:
  - (none — counter per endpoint is a single int in state)

Behaviors:
  - record(): increment counter c with probability 1 / 2^c (Morris algorithm)
  - query(): return estimate = 2^c - 1
  - memory_entries(): number of endpoints tracked (one int per endpoint)
```

#### **Snapshot** — Memento for state rollback

```
Properties:
  - state: Dict[str, Any]   (deep copy of per-endpoint strategy state)
  - metrics: Dict[str, int] (deep copy of metrics at capture time)

Behaviors:
  - (pure data holder — restored by HitCounter.restore_snapshot())
```

#### **HitCounter** — Central coordinator (Singleton)

```
Properties:
  - _instance: Optional[HitCounter]   (class-level singleton reference)
  - _lock: threading.RLock            (class-level creation lock)
  - strategy: CountingStrategy        (current counting implementation)
  - state: Dict[str, Any]             (per-endpoint strategy state)
  - metrics: Dict[str, int]           (total_hits, endpoints_count, pruned_events, memory_entries)
  - listeners: List[Callable]         (event subscribers)
  - lock: threading.RLock             (instance-level re-entrant operation lock)

Behaviors:
  - record_hit(endpoint, ts): Record a hit; prune if strategy supports it; emit events
  - query_hits(endpoint, last_seconds): Query strategy for hit count in window
  - swap_strategy(strategy): Replace counting algorithm; reset state if incompatible
  - take_snapshot(): Deep-copy state + metrics into a Snapshot (Memento)
  - restore_snapshot(snap): Replace state + metrics from snapshot
  - register_listener(fn): Subscribe to lifecycle events
  - get_metrics(): Return copy of current metrics dict
```

### Step 2.3: Define Enumerations / Data Classes

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Snapshot:
    """Memento: captures entire HitCounter state for rollback"""
    state: Dict[str, Any]
    metrics: Dict[str, int]
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **CountingStrategy (ABC)** | Defines pluggable counting contract | Can't swap algorithms at runtime |
| **FixedWindowStrategy** | O(1) record/query, low memory | No fast approximate counting |
| **SlidingWindowStrategy** | Exact per-hit granularity | No precise sliding-window counts |
| **MorrisApproxStrategy** | Single int per endpoint | No memory-efficient option at scale |
| **HitCounter** | Central thread-safe coordinator | No consistent shared state |
| **Snapshot** | Memento for testing/rollback | Can't undo state changes in tests |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Record Hit** ⭐ CRITICAL

```python
def record_hit(endpoint: str, ts: Optional[float] = None) -> None:
    """
    Record a hit for the named endpoint at the given timestamp.

    If ts is None, defaults to time.time().

    Side Effects:
      - Updates strategy-internal state for endpoint
      - Triggers prune if strategy supports it (sliding window)
      - Increments metrics: total_hits, endpoints_count, memory_entries
      - Emits: 'hit_recorded', 'metrics_updated', optionally 'pruned'

    Concurrency: THREAD-SAFE (re-entrant lock)
    Latency: < 1 ms
    """
    pass
```

#### **2. Query Hits** ⭐ CRITICAL

```python
def query_hits(endpoint: str, last_seconds: int) -> int:
    """
    Return the number of hits for endpoint within the last last_seconds seconds.

    Uses current time as the query anchor (now = time.time()).

    Returns: int (exact for Fixed/Sliding; approximate for Morris)

    Note: Morris approximation has statistical error ~±50% for large counts.

    Concurrency: THREAD-SAFE
    Latency: < 10 ms
    """
    pass
```

#### **3. Swap Strategy**

```python
def swap_strategy(strategy: CountingStrategy) -> None:
    """
    Replace the current counting algorithm with a new one.

    If the new strategy type differs from the current:
      - State is reset to {} (incompatible internal representations)
      - Emits: 'strategy_reset', then 'strategy_swapped'

    If same type: state is preserved, no reset.

    Concurrency: THREAD-SAFE
    """
    pass
```

#### **4. Snapshot & Restore**

```python
def take_snapshot() -> Snapshot:
    """
    Capture a deep copy of current state + metrics.
    Emits: 'snapshot_taken'
    Returns: Snapshot (Memento object)
    """
    pass

def restore_snapshot(snap: Snapshot) -> None:
    """
    Restore state and metrics from a previously captured Snapshot.
    Replaces current state entirely.
    Emits: 'snapshot_restored'
    """
    pass
```

#### **5. Register Listener**

```python
def register_listener(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    """
    Subscribe to lifecycle events.
    fn(event_name, payload_dict) is called on each event.
    Events: hit_recorded, pruned, strategy_swapped, strategy_reset,
            snapshot_taken, snapshot_restored, metrics_updated
    """
    pass
```

### Step 3.2: Failure Model

`HitCounter` uses a defensive / non-raising contract for interview clarity. Known failure modes:

```python
# No exception hierarchy required for in-memory counter.
# Failure modes are silent / logged:
#   - Unknown endpoint on query → returns 0 (empty state)
#   - Listener exceptions → caught, logged as [WARN], not re-raised
#   - Strategy swap on same type → no-op reset (state preserved)
```

### Step 3.3: API Usage Example

```python
hc = HitCounter()

# Subscribe to events
hc.register_listener(lambda e, p: print(f"[EVENT] {e}: {p}"))

# Record hits with explicit timestamps
for t in [0.0, 5.0, 8.0, 15.0, 18.0]:
    hc.record_hit("/api/search", ts=t)

# Query: how many hits in last 10 seconds (from now)?
count = hc.query_hits("/api/search", last_seconds=10)

# Swap to probabilistic strategy (resets state)
hc.swap_strategy(MorrisApproxStrategy())
for _ in range(1000):
    hc.record_hit("/api/search")
estimate = hc.query_hits("/api/search", last_seconds=60)

# Snapshot & restore for testing
snap = hc.take_snapshot()
# ... run test mutations ...
hc.restore_snapshot(snap)
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and association. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
HitCounter HAS-A CountingStrategy (1:1 Composition)
  └─ HitCounter owns and manages lifecycle of the current strategy

HitCounter HAS-A state (1:1 Composition)
  └─ State dict maps endpoint → strategy-specific representation
     (buckets dict for Fixed, timestamp list for Sliding, int for Morris)

HitCounter HAS-A metrics (1:1 Composition)
  └─ Metrics dict owns total_hits, pruned_events, memory_entries, endpoints_count

HitCounter HAS-A listeners (1:N Association)
  └─ Multiple callables subscribed to events

CountingStrategy IMPLEMENTED-BY FixedWindowStrategy (Inheritance)
CountingStrategy IMPLEMENTED-BY SlidingWindowStrategy (Inheritance)
CountingStrategy IMPLEMENTED-BY MorrisApproxStrategy (Inheritance)

HitCounter CREATES Snapshot (Factory)
  └─ take_snapshot() produces a Memento; restore_snapshot() consumes it
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────────────┐
│         HitCounter (Singleton)           │
├──────────────────────────────────────────┤
│ - _instance: Optional[HitCounter]        │
│ - _lock: threading.RLock  (class-level)  │
│ - strategy: CountingStrategy             │
│ - state: Dict[str, Any]                  │
│ - metrics: Dict[str, int]                │
│ - listeners: List[Callable]              │
│ - lock: threading.RLock  (inst-level)    │
├──────────────────────────────────────────┤
│ + record_hit(endpoint, ts): void         │
│ + query_hits(endpoint, last_s): int      │
│ + swap_strategy(strategy): void          │
│ + take_snapshot(): Snapshot              │
│ + restore_snapshot(snap): void           │
│ + register_listener(fn): void            │
│ + get_metrics(): Dict                    │
└────────────────┬─────────────────────────┘
                 │ owns 1:1
                 ▼
┌──────────────────────────────────────────┐
│       CountingStrategy (ABC)             │
├──────────────────────────────────────────┤
│ + name(): str                            │
│ + record(state, endpoint, ts): void      │
│ + query(state, endpoint, now, last): int │
│ + prune(state, endpoint, now): int       │
│ + memory_entries(state): int             │
└────┬──────────────┬────────────────┬─────┘
     │              │                │
     ▼              ▼                ▼
┌──────────────┐ ┌───────────────┐ ┌────────────────┐
│FixedWindow   │ │SlidingWindow  │ │MorrisApprox    │
│Strategy      │ │Strategy       │ │Strategy        │
├──────────────┤ ├───────────────┤ ├────────────────┤
│-window_size_s│ │-max_window_s  │ │(no fields)     │
├──────────────┤ ├───────────────┤ ├────────────────┤
│state repr:   │ │state repr:    │ │state repr:     │
│Dict[int,int] │ │List[float]    │ │int             │
│(buckets)     │ │(timestamps)   │ │(counter c)     │
├──────────────┤ ├───────────────┤ ├────────────────┤
│record: O(1)  │ │record: O(1)   │ │record: O(1)    │
│query: O(B)   │ │prune: O(n)    │ │query: O(1)     │
│memory: O(B)  │ │query: O(n)    │ │memory: O(E)    │
└──────────────┘ └───────────────┘ └────────────────┘

MEMENTO PATTERN (Snapshot):
┌─────────────────────────────┐
│  Snapshot (dataclass)       │
├─────────────────────────────┤
│ + state: Dict[str, Any]     │
│ + metrics: Dict[str, int]   │
└─────────────────────────────┘

Lifecycle:
RECORD_HIT → STRATEGY.record() → STRATEGY.prune() → METRICS_UPDATE
     └───────────────────────────────────────────→ EMIT_EVENT
                                                        │
                                              SNAPSHOT / RESTORE

B = number of non-empty buckets per endpoint
n = timestamps per endpoint within max_window_s
E = number of distinct endpoints
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| HitCounter → CountingStrategy | 1:1 | Composition | Counter owns one active strategy |
| HitCounter → state dict | 1:1 | Composition | State owned exclusively by counter |
| HitCounter → metrics dict | 1:1 | Composition | Metrics owned exclusively by counter |
| HitCounter → listeners | 1:N | Association | Multiple observers subscribe |
| CountingStrategy → FixedWindowStrategy | 1:1 | Inheritance | Concrete counting implementation |
| CountingStrategy → SlidingWindowStrategy | 1:1 | Inheritance | Concrete counting implementation |
| CountingStrategy → MorrisApproxStrategy | 1:1 | Inheritance | Concrete counting implementation |
| state → per-endpoint data | 1:N | Composition | Each endpoint has independent state |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For HitCounter)

**Problem**: Multiple callers across threads need one consistent view of hit counts and metrics.

**Solution**: One global `HitCounter` instance with double-checked thread-safe initialization.

```python
class HitCounter:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefit**: ✅ Single source of truth, ✅ Thread-safe (double-checked lock), ✅ Global access  
**Trade-off**: ⚠️ Global state (harder to unit-test in isolation), ⚠️ Does not scale across processes

---

### Pattern 2: **Strategy** (For Counting Algorithms) — Central Pattern

**Problem**: Different callers need different accuracy/memory trade-offs. Fixed window is fast but coarse; sliding window is exact but memory-intensive; Morris is tiny but probabilistic. These must be swappable without changing the calling code.

**Solution**: `CountingStrategy` ABC defines `record / query / prune / memory_entries`. `HitCounter` holds a reference to the current strategy and delegates all counting to it.

```python
class CountingStrategy:
    def record(self, state, endpoint, ts): raise NotImplementedError
    def query(self, state, endpoint, now, last_seconds): raise NotImplementedError
    def prune(self, state, endpoint, now): return 0
    def memory_entries(self, state): raise NotImplementedError

class FixedWindowStrategy(CountingStrategy):
    def __init__(self, window_size_s: int = 10):
        self.window_size_s = window_size_s

    def record(self, state, endpoint, ts):
        buckets = state.setdefault(endpoint, {})
        key = int(ts // self.window_size_s)
        buckets[key] = buckets.get(key, 0) + 1

    def query(self, state, endpoint, now, last_seconds):
        buckets = state.get(endpoint, {})
        start = int((now - last_seconds) // self.window_size_s)
        end = int(now // self.window_size_s)
        return sum(c for k, c in buckets.items() if start <= k <= end)

# Swap at runtime — HitCounter code unchanged:
hc.swap_strategy(SlidingWindowStrategy(max_window_s=60))
hc.swap_strategy(MorrisApproxStrategy())
```

**Benefit**: ✅ New strategies added without touching `HitCounter`, ✅ Runtime swap, ✅ Clear separation of accuracy/memory trade-off  
**Trade-off**: ⚠️ State reset required when switching between incompatible strategy types

---

### Pattern 3: **Observer** (For Lifecycle Events)

**Problem**: Monitoring, logging, and testing code needs to react to hit counter events (record, prune, strategy swap, snapshot) without coupling to core logic.

**Solution**: `HitCounter` maintains a list of listener callables. `_emit(event, payload)` calls each on lifecycle transitions.

```python
def register_listener(self, fn: Callable[[str, Dict], None]) -> None:
    self.listeners.append(fn)

def _emit(self, event: str, payload: Dict) -> None:
    for fn in self.listeners:
        try:
            fn(event, payload)
        except Exception as e:
            print(f"  [WARN] Listener error: {e}")

# Usage: track pruning frequency for tuning
pruned_total = [0]
hc.register_listener(
    lambda e, p: pruned_total.__setitem__(0, pruned_total[0] + p.get('removed', 0))
    if e == 'pruned' else None
)
```

**Benefit**: ✅ Loose coupling, ✅ Multiple independent consumers, ✅ Easy to add new monitoring  
**Trade-off**: ⚠️ Listener exceptions must be caught to prevent disrupting the caller

---

### Pattern 4: **Memento** (For Snapshot / Restore)

**Problem**: Tests need to apply hits, compare different queries, then roll back state. Strategy swaps may also need to be undone.

**Solution**: `take_snapshot()` captures a deep copy of state + metrics into a `Snapshot` dataclass. `restore_snapshot()` replaces live state from the snapshot.

```python
def take_snapshot(self) -> Snapshot:
    with self.lock:
        state_copy = {
            ep: (data.copy() if isinstance(data, (dict, list)) else data)
            for ep, data in self.state.items()
        }
        snap = Snapshot(state=state_copy, metrics=self.metrics.copy())
        self._emit('snapshot_taken', {'endpoints_count': len(self.state)})
        return snap

def restore_snapshot(self, snap: Snapshot) -> None:
    with self.lock:
        self.state = {
            ep: (data.copy() if isinstance(data, (dict, list)) else data)
            for ep, data in snap.state.items()
        }
        self.metrics = snap.metrics.copy()
        self._emit('snapshot_restored', {})
```

**Benefit**: ✅ Fast in-memory rollback, ✅ No impact on production state during testing  
**Trade-off**: ⚠️ Snapshot is a point-in-time copy — does not capture strategy type itself

---

### Pattern 5: **State Machine** (Per-Endpoint Bucket / Timestamp / Counter)

**Problem**: Each endpoint has independent counting state whose representation differs by strategy. Mixing representations would corrupt counts.

**Solution**: Each strategy defines and owns its per-endpoint state representation inside the shared `state` dict. The state machine is implicit in the strategy's `record`, `prune`, and `query` methods.

```python
# Fixed window: state["/api"] = {0: 3, 1: 2}       (bucket_key → count)
# Sliding:      state["/api"] = [0.0, 5.0, 8.0]    (timestamps list)
# Morris:       state["/api"] = 4                    (counter c, single int)

# Lifecycle:
# EMPTY → record() → NON_EMPTY → prune() → PARTIAL → query() → (no mutation)
```

**Benefit**: ✅ Clear separation of per-endpoint concerns, ✅ O(1) per-endpoint record for Fixed/Morris  
**Trade-off**: ⚠️ State dict is weakly typed — requires trust that only the owning strategy modifies it

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Benefit |
|---------|----------------|---------|
| **Singleton** | Single global HitCounter | Consistent state across all callers |
| **Strategy** | Swappable accuracy/memory trade-offs | Add new algorithms without changing HitCounter |
| **Observer** | Lifecycle events for monitoring | Loose coupling, event-driven observability |
| **Memento** | State rollback for testing | Fast in-memory undo with no production impact |
| **State Machine** | Per-endpoint state isolation | Clear strategy-owned representations |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Hit Counter - Interview Implementation
Demonstrates:
1. Pluggable counting strategies (fixed, sliding, approximate)
2. Per-endpoint state management
3. Pruning for memory efficiency
4. Event-driven lifecycle
5. Snapshot/restore for testing
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time
import threading
import random

# ============================================================================
# ENUMERATIONS & DATA CLASSES
# ============================================================================

@dataclass
class Snapshot:
    """Memento: captures entire state for rollback"""
    state: Dict[str, Any]
    metrics: Dict[str, int]

# ============================================================================
# COUNTING STRATEGIES (ABC)
# ============================================================================

class CountingStrategy:
    """Abstract base for counting implementations"""

    def name(self) -> str:
        return self.__class__.__name__

    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        raise NotImplementedError

    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        raise NotImplementedError

    def prune(self, state: Dict[str, Any], endpoint: str, now: float) -> int:
        """Returns number of entries pruned"""
        return 0

    def memory_entries(self, state: Dict[str, Any]) -> int:
        """Returns total memory entries across all endpoints"""
        raise NotImplementedError

# ============================================================================
# FIXED WINDOW STRATEGY
# ============================================================================

class FixedWindowStrategy(CountingStrategy):
    """Bucket aggregation: divide time into fixed windows"""

    def __init__(self, window_size_s: int = 10):
        self.window_size_s = window_size_s

    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        """Record hit in appropriate bucket"""
        buckets = state.setdefault(endpoint, {})
        bucket_key = int(ts // self.window_size_s)
        buckets[bucket_key] = buckets.get(bucket_key, 0) + 1

    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        """Query hits in time window (sum buckets)"""
        buckets = state.get(endpoint, {})
        if not buckets:
            return 0

        start_bucket = int((now - last_seconds) // self.window_size_s)
        end_bucket = int(now // self.window_size_s)

        return sum(count for b, count in buckets.items() if start_bucket <= b <= end_bucket)

    def memory_entries(self, state: Dict[str, Any]) -> int:
        return sum(len(buckets) for buckets in state.values())

# ============================================================================
# SLIDING WINDOW STRATEGY
# ============================================================================

class SlidingWindowStrategy(CountingStrategy):
    """Per-hit timestamps with pruning"""

    def __init__(self, max_window_s: int = 60):
        self.max_window_s = max_window_s

    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        """Append hit timestamp"""
        lst: List[float] = state.setdefault(endpoint, [])
        lst.append(ts)

    def prune(self, state: Dict[str, Any], endpoint: str, now: float) -> int:
        """Remove timestamps older than max_window_s"""
        lst: List[float] = state.get(endpoint, [])
        if not lst:
            return 0

        cutoff = now - self.max_window_s
        original_len = len(lst)

        # Find first index >= cutoff
        keep_index = 0
        for i, t in enumerate(lst):
            if t >= cutoff:
                keep_index = i
                break
        else:
            keep_index = original_len  # All old

        removed = original_len - keep_index
        lst[:] = lst[keep_index:]

        return removed

    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        """Count timestamps in window"""
        lst: List[float] = state.get(endpoint, [])
        if not lst:
            return 0

        cutoff = now - last_seconds
        return sum(1 for t in lst if t >= cutoff)

    def memory_entries(self, state: Dict[str, Any]) -> int:
        return sum(len(lst) for lst in state.values())

# ============================================================================
# MORRIS APPROXIMATION STRATEGY
# ============================================================================

class MorrisApproxStrategy(CountingStrategy):
    """Probabilistic counter: increment with probability 1/2^c"""

    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        """Increment counter probabilistically"""
        c = state.get(endpoint, 0)

        # Increment with probability 1 / 2^c
        prob = 1.0 / (2 ** c if c > 0 else 1)
        if random.random() < prob:
            c += 1

        state[endpoint] = c

    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        """Estimate count: 2^c - 1"""
        c = state.get(endpoint, 0)
        return int(2 ** c - 1) if c > 0 else 0

    def memory_entries(self, state: Dict[str, Any]) -> int:
        return len(state)

# ============================================================================
# HIT COUNTER (SINGLETON)
# ============================================================================

class HitCounter:
    """Central hit counter with pluggable strategies"""

    _instance: Optional['HitCounter'] = None
    _lock = threading.RLock()  # RLock: re-entrant so listeners can call back in safely

    def __new__(cls, *args, **kwargs):
        # Accept *args/**kwargs so subclass or explicit args don't raise TypeError
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.strategy: CountingStrategy = FixedWindowStrategy(window_size_s=10)
        self.state: Dict[str, Any] = {}
        self.metrics: Dict[str, int] = {
            'total_hits': 0,
            'endpoints_count': 0,
            'pruned_events': 0,
            'memory_entries': 0,
        }
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.lock = threading.RLock()  # RLock: record_hit → _emit → listener → get_metrics (re-entrant)
        print("HitCounter initialized")

    def register_listener(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to events"""
        self.listeners.append(fn)

    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        """Emit event to all listeners"""
        for listener_fn in self.listeners:
            try:
                listener_fn(event, payload)
            except Exception as e:
                print(f"  [WARN] Listener error: {e}")

    def record_hit(self, endpoint: str, ts: Optional[float] = None) -> None:
        """Record a hit for endpoint"""
        ts = ts or time.time()

        with self.lock:
            self.strategy.record(self.state, endpoint, ts)

            # Prune if supported
            removed = self.strategy.prune(self.state, endpoint, ts)
            if removed > 0:
                self.metrics['pruned_events'] += removed
                self._emit('pruned', {'endpoint': endpoint, 'removed': removed})

            # Update metrics
            self.metrics['total_hits'] += 1
            self.metrics['endpoints_count'] = len(self.state)
            self.metrics['memory_entries'] = self.strategy.memory_entries(self.state)

            self._emit('hit_recorded', {'endpoint': endpoint, 'ts': ts})
            self._emit('metrics_updated', {
                'total_hits': self.metrics['total_hits'],
                'memory_entries': self.metrics['memory_entries']
            })

    def query_hits(self, endpoint: str, last_seconds: int) -> int:
        """Query hit count for endpoint in last_seconds"""
        now = time.time()

        with self.lock:
            return self.strategy.query(self.state, endpoint, now, last_seconds)

    def swap_strategy(self, strategy: CountingStrategy) -> None:
        """Switch to different counting strategy"""
        with self.lock:
            old_name = self.strategy.name()
            new_name = strategy.name()

            # If incompatible, reset state
            if type(strategy) is not type(self.strategy):
                self.state = {}
                self.metrics['endpoints_count'] = 0
                self.metrics['pruned_events'] = 0
                self._emit('strategy_reset', {
                    'from': old_name,
                    'to': new_name,
                    'reason': 'incompatible_state_reset'
                })

            self.strategy = strategy
            self.metrics['memory_entries'] = self.strategy.memory_entries(self.state)

            self._emit('strategy_swapped', {'old': old_name, 'new': new_name})

    def take_snapshot(self) -> Snapshot:
        """Capture current state (Memento pattern)"""
        with self.lock:
            state_copy = {}
            for endpoint, data in self.state.items():
                if isinstance(data, dict):
                    state_copy[endpoint] = data.copy()
                elif isinstance(data, list):
                    state_copy[endpoint] = data.copy()
                else:
                    state_copy[endpoint] = data

            snap = Snapshot(state=state_copy, metrics=self.metrics.copy())
            self._emit('snapshot_taken', {'endpoints_count': len(self.state)})
            return snap

    def restore_snapshot(self, snap: Snapshot) -> None:
        """Restore state from snapshot"""
        with self.lock:
            self.state = {}
            for endpoint, data in snap.state.items():
                if isinstance(data, dict):
                    self.state[endpoint] = data.copy()
                elif isinstance(data, list):
                    self.state[endpoint] = data.copy()
                else:
                    self.state[endpoint] = data

            self.metrics = snap.metrics.copy()
            self._emit('snapshot_restored', {})

    def get_metrics(self) -> Dict[str, int]:
        """Return current metrics"""
        with self.lock:
            return self.metrics.copy()

# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def simple_listener(event: str, payload: Dict[str, Any]):
    if event in ['pruned', 'strategy_swapped', 'strategy_reset']:
        print(f"  [EVENT] {event}: {payload}")

def demo_1_fixed_window():
    print_section("DEMO 1: FIXED WINDOW BASELINE")

    hc = HitCounter()
    hc.register_listener(simple_listener)

    # Record hits at t=0, 5, 8, 15, 18
    for i, t in enumerate([0, 5, 8, 15, 18]):
        hc.record_hit("/api", ts=t)

    # Query at different times
    print("\n  Query at t=20s, last 10s:")
    count = hc.query_hits("/api", last_seconds=10)
    print(f"  /api count: {count} hits")
    print(f"  Metrics: {hc.get_metrics()}")

def demo_2_sliding_vs_fixed():
    print_section("DEMO 2: SLIDING WINDOW VS FIXED")

    hc = HitCounter()
    hc.register_listener(simple_listener)

    # Record same hits with sliding window
    hc.swap_strategy(SlidingWindowStrategy(max_window_s=5))

    for i, t in enumerate([0, 5, 8, 15, 18]):
        hc.record_hit("/stream", ts=t)

    print("\n  Sliding window queries:")
    print(f"  Last 1s:  {hc.query_hits('/stream', 1)} hits")
    print(f"  Last 5s:  {hc.query_hits('/stream', 5)} hits")
    print(f"  Last 20s: {hc.query_hits('/stream', 20)} hits")

def demo_3_morris_approx():
    print_section("DEMO 3: MORRIS APPROXIMATION")

    hc = HitCounter()
    hc.register_listener(simple_listener)
    hc.swap_strategy(MorrisApproxStrategy())

    # Record 1000 hits
    print("  Recording 1000 hits...")
    for i in range(1000):
        hc.record_hit("/counter")

    estimate = hc.query_hits("/counter", last_seconds=10)
    print(f"\n  Morris estimate: {estimate} (approx 1000, statistical error acceptable)")
    print(f"  Memory entries: {hc.get_metrics()['memory_entries']}")

def demo_4_high_volume_prune():
    print_section("DEMO 4: HIGH-VOLUME PRUNING")

    hc = HitCounter()
    hc.swap_strategy(SlidingWindowStrategy(max_window_s=1))

    print("  Recording burst of hits over 2 seconds...")
    start = time.time()
    i = 0
    while time.time() - start < 2.0:
        hc.record_hit("/burst", ts=time.time())
        i += 1

    metrics = hc.get_metrics()
    print(f"\n  Total hits: {metrics['total_hits']}")
    print(f"  Memory entries: {metrics['memory_entries']}")
    print(f"  Pruned events: {metrics['pruned_events']}")
    print(f"  Last 1s count: {hc.query_hits('/burst', 1)}")

def demo_5_snapshot_restore():
    print_section("DEMO 5: SNAPSHOT & RESTORE")

    hc = HitCounter()
    hc.swap_strategy(FixedWindowStrategy(window_size_s=10))

    # Record 50 hits
    for i in range(50):
        hc.record_hit("/home", ts=i * 0.1)

    snap = hc.take_snapshot()
    before_count = hc.query_hits("/home", last_seconds=10)
    before_metrics = hc.get_metrics()

    print(f"\n  After first batch: {before_count} hits")

    # Record 50 more
    for i in range(50):
        hc.record_hit("/home", ts=5 + i * 0.1)

    after_count = hc.query_hits("/home", last_seconds=10)
    after_metrics = hc.get_metrics()

    print(f"  After second batch: {after_count} hits")
    print(f"  Total hits: {after_metrics['total_hits']}")

    # Restore
    hc.restore_snapshot(snap)
    restored_count = hc.query_hits("/home", last_seconds=10)
    restored_metrics = hc.get_metrics()

    print(f"\n  After restore: {restored_count} hits")
    print(f"  Total hits: {restored_metrics['total_hits']}")

# ============================================================================
# MAIN
# ============================================================================

if True:
    print("\n" + "="*70)
    print("DESIGN HIT COUNTER - 5 DEMO SCENARIOS")
    print("="*70)

    demo_1_fixed_window()
    demo_2_sliding_vs_fixed()
    demo_3_morris_approx()
    demo_4_high_volume_prune()
    demo_5_snapshot_restore()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---------------|------------|
| **record_hit** | Instance RLock | Atomic: strategy.record + prune + metrics update |
| **query_hits** | Instance RLock | Consistent read of strategy state |
| **swap_strategy** | Instance RLock | Atomic: reset state + swap + metrics update |
| **take_snapshot** | Instance RLock | Deep copy under lock — snapshot is consistent |
| **restore_snapshot** | Instance RLock | Atomic full state replacement |
| **Singleton init** | Class RLock | Double-checked locking, single instance |

**Concurrency Principles**:
1. ✅ `threading.RLock` (re-entrant) on both class-level and instance-level locks — listeners that call `get_metrics()` inside `record_hit` won't deadlock
2. ✅ `__new__` accepts `*args, **kwargs` to avoid `TypeError` if subclassed or called with arguments
3. ✅ Notifications (`_emit`) fire inside the lock so listeners see consistent state
4. ✅ Minimal lock scope for `query_hits` — read-only, no mutation

---

## Demo Scenarios

### Demo 1: Fixed Window Baseline

```
- Record hits for /api endpoint: t=0, 5, 8, 15, 18s
- Window size: 10 seconds
- Query last 10s at t=20s
- Buckets: [0-10]: 3 hits, [10-20]: 2 hits
- Result: 5 hits (all buckets overlap)
```

### Demo 2: Sliding vs Fixed

```
- Same hits: t=0, 5, 8, 15, 18s
- Fixed window (10s): reports 5 hits
- Sliding window: exact count = 5 hits
- Fixed boundary effect: hit at t=9.99s vs t=10.00s differs
- Sliding always accurate
```

### Demo 3: Strategy Swap to Morris

```
- Start with fixed window
- 1000 hits recorded
- Swap to Morris approximation
- State reset (incompatible repr)
- Continue recording
- Estimate ≈ actual (statistical error ±50%)
```

### Demo 4: High-Volume Pruning

```
- Sliding window, max_window=5s
- Record 1000 hits over 10 seconds
- Pruning fires every record
- Memory entry count stays ≤ 5000 (5s × 1K QPS max)
- Without prune: would be 10K entries
```

### Demo 5: Snapshot & Restore

```
- Record 50 hits
- Take snapshot
- Record 50 more hits
- Query shows 100 hits
- Restore snapshot
- Query shows 50 hits again
- Metrics rolled back
```

---

## Interview Q&A

### Basic Level

**Q1: How do you record and query hits?**

A: Record: call `strategy.record(endpoint, timestamp)` → updates internal state. Query: call `strategy.query(endpoint, now, last_seconds)` → aggregates hits in time window. Different strategies use different representations (buckets vs timestamps vs probabilistic counters).

**Q2: What's the difference between fixed and sliding window strategies?**

A: Fixed: divides time into buckets (e.g., 10-sec buckets). Record: increment bucket. Query: sum buckets overlapping window. Fast but coarse. Sliding: stores individual timestamps. Query: count timestamps >= (now - last_seconds). Exact but memory-intensive.

**Q3: What's Morris approximation?**

A: Probabilistic counter. On record: increment counter c with probability 1/(2^c). Estimate = 2^c - 1. Extremely memory-efficient (single int per endpoint) but has statistical error (~±50% for large counts). Used when memory is critical.

**Q4: Why do you need pruning?**

A: Sliding window stores all timestamps. Without pruning, memory grows unbounded. Pruning: remove timestamps older than max_window_s. Called each record/query. Metrics track pruned_events.

**Q5: How do you handle strategy swaps?**

A: Different strategies use incompatible internal representations (buckets vs lists vs ints). Strategy swap: if incompatible, reset state (document limitation). Cannot losslessly convert approximate state to exact. Emit strategy_swapped event.

### Intermediate Level

**Q6: How do you calculate fixed window bucket key?**

A: `bucket_key = floor(timestamp / window_size_s)`. Example: ts=25.7s, window=10s → bucket=2. Multiple hits in same second go to same bucket. Query iterates buckets [floor((now-last_s)/window), floor(now/window)].

**Q7: How do you prevent memory explosion in sliding window?**

A: Pruning policy: remove timestamps older than max_window_s. Example: max_window=60s. On query(endpoint, last_5s), also prune timestamps < (now - 60). Cost: O(n) per prune. Trade-off: frequency of pruning vs memory growth.

**Q8: What does snapshot capture?**

A: Deep copy of entire state dict + metrics dict. Snapshot.restore() replaces current state. Used for testing (apply hits, snapshot, try different queries, restore). Or rollback if strategy swap fails.

**Q9: How are events useful?**

A: Listeners subscribe to events (hit_recorded, pruned, strategy_swapped, snapshot_taken, metrics_updated). Enables logging, monitoring, testing. Example: count pruned_events to tune pruning frequency.

**Q10: How do you handle multiple endpoints?**

A: Each endpoint has separate state (bucket dict for fixed, timestamp list for sliding, counter int for morris). HitCounter.state: dict[endpoint] → strategy-specific representation. Query per endpoint.

### Advanced Level

**Q11: How to optimize query for millions of endpoints?**

A: Partitioning: shard endpoints by hash(endpoint) % num_shards. Each shard is separate HitCounter instance. Query aggregates across shards. Fixed window: O(1) query (count hit buckets); sliding: O(n) where n = hits in window.

**Q12: How to detect and handle clock skew (time going backwards)?**

A: Fixed window: bucket_key always increases or stays same. Issue: negative drift → lower bucket. Mitigate: require monotonic timestamps (use max(ts, last_ts)). Sliding: filter out future timestamps (ts > now + delta). Log anomalies.

---

## Scaling Q&A

**Q1: Can you handle 1M requests/second?**

A: Fixed window: O(1) record (hash lookup). Yes, easily. Sliding: O(1) append but memory grows 1M items/sec = 8 MB/sec. Need aggressive pruning (every 100ms). Morris: O(1) record, ~100 endpoints × 8 bytes = negligible. Choose strategy by SLA.

**Q2: How much memory does each strategy use?**

A: Fixed window (10-sec bucket, 1M endpoints): 1M × 100 buckets × 8 bytes = 800 MB. Sliding (60-sec window, 1K QPS): 1K × 60 = 60K entries × 8 bytes = 480 KB. Morris: 1M × 8 bytes = 8 MB. Morris wins for scale.

**Q3: How to distribute across multiple machines?**

A: Shard endpoints. Machine 1 handles endpoints A-M, Machine 2 handles N-Z, etc. Each machine runs independent HitCounter. Aggregation: query all shards, sum results. Scaling: add shard for each 10M hits/sec.

**Q4: What if query arrives during pruning?**

A: Lock state during prune. Readers wait. Alternative: copy-on-write snapshot during prune, readers use old version. Trade-off: latency vs memory copy. For hit counter, lock acceptable (<1ms prune).

**Q5: How to persist state for recovery?**

A: Write-ahead log (WAL): append-only log of (record/query/strategy_swap) events. On restart: replay log → recover state. Or: checkpoint snapshots every N minutes + replay logs since last checkpoint.

**Q6: Can you support sliding window for 100M requests/day?**

A: 100M requests/day = 1.2K QPS. Sliding (60-sec): 1.2K × 60 = 72K timestamps × 8 bytes = 576 KB. Manageable. Prune every 10 seconds removes stale data. Yes, feasible.

**Q7: How to adapt strategy based on load?**

A: Monitor metrics (total_hits, memory_entries). If memory_entries > threshold, swap to Morris (probabilistic). If high accuracy needed, swap to sliding (higher memory). Metrics inform strategy choice.

**Q8: How to handle burst traffic?**

A: Burst: 10M hits in 1 second. Fixed window: increment bucket by 10M (single int, safe). Sliding: append 10M timestamps (memory spike). Prune immediately after to recover. Or use fixed window as buffer.

**Q9: Can you support real-time leaderboards (top endpoints)?**

A: Track query counts per endpoint. Rank by (count DESC). Recompute every 5 minutes (batch sort). Cache top-100 in memory. Update on-demand if endpoint promoted/demoted. O(n log n) batch, O(log n) updates.

**Q10: How to prevent double-counting (same request counted twice)?**

A: Request ID deduplication: maintain set of seen IDs (bloom filter for space efficiency). On record: check if ID seen. If yes, skip. Tradeoff: false negatives acceptable for hit counts.

**Q11: How to handle clock skew across distributed systems?**

A: Use global clock (NTP-synchronized). Max clock delta: ±1 second. Sliding window: discard timestamps > (now + 1s) or < (now - max_window - 1s). Log anomalies. Alert on skew > threshold.

**Q12: How to support multi-level aggregation (per-second, per-minute, per-hour)?**

A: Maintain separate HitCounter instances: 1-sec window, 60-sec window, 3600-sec window. Each runs independently. Query aggregates level needed. Or: single 3600-sec counter with sub-buckets (3600 / 1-sec).

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram with CountingStrategy hierarchy and HitCounter
- [ ] Explain the three strategy trade-offs: Fixed (fast, coarse) vs Sliding (exact, memory) vs Morris (tiny, approximate)
- [ ] Explain why Strategy pattern is the central pattern here and how swap works
- [ ] Discuss pruning: why it's needed for sliding window, what happens without it
- [ ] Explain how RLock prevents deadlock when listeners call back into HitCounter
- [ ] Run complete implementation (5 demos) without errors
- [ ] Answer 5+ scaling Q&A questions
- [ ] Discuss Memento pattern: take_snapshot / restore_snapshot and its use in testing
- [ ] Discuss trade-offs: choosing strategy based on SLA (accuracy vs memory vs speed)

---

**Ready for interview? Start counting those hits!**
