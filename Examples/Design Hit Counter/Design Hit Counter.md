# Design Hit Counter — 75-Minute Interview Guide

## Quick Start Overview

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | record/query windows |
| 5–15 | Architecture | HitCounter + strategies + events |
| 15–35 | Implement strategies | Fixed, Sliding, Morris approx |
| 35–55 | Pruning + metrics | Memory control & instrumentation |
| 55–70 | Demos + snapshot | 5 scenarios |
| 70–75 | Q&A | Trade-offs & scaling |

## 🧱 Entities Cheat Sheet
HitCounter(strategy, endpoints_state, metrics)
CountingStrategy.record(endpoint, ts)
CountingStrategy.query(endpoint, now, last_seconds)
Strategies: FixedWindowStrategy, SlidingWindowStrategy, MorrisApproxStrategy
Snapshot(state_clone)

## 🛠 Patterns
Singleton (HitCounter)
Strategy (Counting semantics)
Observer (Events)
Memento (Snapshot)
State (Per-endpoint buckets/timestamps/counter value)

## 🎯 Demo Order
1. Fixed window baseline
2. Sliding window vs fixed comparative counts
3. Swap to Morris approximation
4. High-volume hits + pruning
5. Snapshot, mutate, restore

Run:
```bash
python3 "INTERVIEW_COMPACT.py"
```

## ✅ Checklist
- [ ] Strategy swap emits event
- [ ] Sliding pruning reduces memory entries
- [ ] Approximate count near actual for large N
- [ ] Snapshot restore returns previous totals
- [ ] Metrics updated after each record

## 💬 Quick Answers
Why strategies? → Swap accuracy/performance trade-offs transparently.
Why prune? → Prevent unbounded growth in sliding window.
Why approximate? → Reduce memory for massive traffic at cost of error.
Why snapshot? → Fast rollback & testing strategy effects.
Scaling path? → Shard counters + persist bucket deltas.

## 🆘 If Behind
<20m: Implement FixedWindowStrategy + basic record/query.
20–35m: Add SlidingWindowStrategy + pruning.
35–50m: Add Morris approx strategy.
>50m: Events, metrics, snapshot, demos.

Focus on accuracy vs memory trade-off narrative.


## 75-Minute Guide

## 1. Problem Framing (0–5)
Design an in-memory hit counter supporting per-endpoint counts over time windows with swappable strategies (fixed buckets, sliding timestamps, approximate probabilistic), pruning, metrics, events, snapshot restore.

Must:
- record_hit(endpoint)
- query_hits(endpoint, last_seconds)
- strategy swap
- pruning for sliding strategy
- metrics & events
- snapshot/restore

Stretch:
- Approximate counting for large scale
- Multi-endpoint aggregation

## 2. Requirements & Constraints (5–10)
Functional:
- Query count for last X seconds
- Handle high rate inserts (O(1) or amortized small)
- Support differing accuracy/performance strategies

Non-Functional:
- Memory efficiency (prune old data)
- Extensibility for new strategies
- Observability for tuning

Assumptions:
- Single process, moderate data size
- No persistence or distribution (discuss extension)

## 3. Domain Model (10–18)
Entities:
- HitCounter(strategy, endpoints_state, metrics)
- EndpointState depends on strategy:
  - FixedWindow: dict bucket_key -> count
  - SlidingWindow: list of timestamps
  - MorrisApprox: integer counter c
- CountingStrategy(record/query/prune)
- Snapshot(deep copy of endpoints_state + metrics)

Relationships:
HitCounter delegates record/query/prune operations to strategy using common interface.

## 4. Patterns (18–26)
Singleton: single counter instance.
Strategy: interchangeable counting logic.
Observer: events for record, prune, strategy swap.
Memento: snapshot for rollback.
State: distinct internal representation per strategy.

## 5. Lifecycle (26–32)
RECORD → STATE_UPDATE → (OPTIONAL_PRUNE) → METRICS_UPDATE → QUERY (AGGREGATE) → SNAPSHOT / RESTORE.

Invariants:
1. Strategy encapsulates all state mutation specifics.
2. Metrics update after each record.
3. Snapshot restore fully replaces internal state.
4. Strategy swap does not retroactively convert existing representation (document limitation).

## 6. Strategies (32–42)
FixedWindowStrategy(window_size_s):
- Bucket key = floor(timestamp / window_size_s)
- Record: increment bucket
- Query(last_seconds): iterate buckets overlapping [now - last_seconds, now]
Pros: small memory for high traffic. Cons: boundary effects & coarse accuracy.

SlidingWindowStrategy(max_window_s):
- Store individual hit timestamps (append list)
- Prune hits older than max_window_s on record/query
- Query: count hits with ts >= now - last_seconds
Pros: exact accuracy. Cons: memory grows with traffic.

MorrisApproxStrategy:
- Probabilistic counter c per endpoint
- On record: increment c with probability 1 / (2^c)
- Estimate = 2^c - 1
Pros: extremely memory efficient. Cons: statistical error.

## 7. Pruning (42–48)
SlidingWindowStrategy performs pruning each record to drop stale timestamps.
Metrics: `pruned_events` increments by number removed.
Trade-off: Frequent pruning cost vs memory growth.

## 8. Metrics (48–53)
- total_hits (logical hits recorded)
- endpoints_count
- pruned_events
- memory_entries (sum of buckets or timestamps or endpoints for Morris)
- strategy (current)

## 9. Events (53–57)
Names:
- hit_recorded {endpoint, ts}
- pruned {endpoint, removed}
- strategy_swapped {old, new}
- snapshot_taken {endpoints_count}
- snapshot_restored {}
- metrics_updated {total_hits, memory_entries}

## 10. Demo Scenarios (57–65)
1. Fixed window record & query
2. Sliding window vs fixed comparison
3. Strategy swap to Morris approx
4. High-frequency hits + pruning visualization
5. Snapshot, mutate, restore

## 11. Trade-offs (65–72)
Fixed window: efficient but boundary inaccuracies.
Sliding: precise but memory heavy & prune cost.
Approximate: super lightweight but estimation error (discuss typical error magnitude ~ acceptable for trending).
Snapshot vs log replay: memory copy vs iterative reconstruction.
Strategy swap limitations: cannot convert old representation; must restart or snapshot earlier.

## 12. Extensions (72–75)
- Distributed counters (shard + merge)
- Persistent time-series store (append-only log)
- Advanced approximate (LogLog Beta, HyperLogLog for distinct users)
- Adaptive strategy selection based on traffic
- Rate limiting hooks (alerts when threshold exceeded)

## Summary
Flexible hit counter: strategy-based accuracy/performance dial, observable lifecycle, pruning memory discipline, and snapshot rollback path—mirrors production considerations while remaining interview-friendly.


## Detailed Design Reference

Aligned with Airline Management System style: structured patterns, lifecycle clarity, strategy extensibility, events, metrics, snapshot.

---
## 🎯 Goal
Track request hit counts per endpoint over time with pluggable windowing/counting strategies (fixed window, sliding window, approximate probabilistic), real‑time queries, pruning, and observability.

---
## 🧱 Core Components
| Component | Responsibility | Patterns |
|-----------|----------------|----------|
| `HitCounter` | Records hits + queries counts | Singleton, Observer |
| `CountingStrategy` | Implements record/query logic | Strategy |
| `FixedWindowStrategy` | Bucket aggregation by window size | Strategy |
| `SlidingWindowStrategy` | Precise per-hit timestamps pruned | Strategy |
| `MorrisApproxStrategy` | Probabilistic approximate counting | Strategy |
| `Snapshot` | Captures entire state for rollback | Memento |
| `Events` | Emitted lifecycle notifications | Observer |

---
## 🔄 Lifecycle
RECORD_REQUEST → BUCKET_UPDATE / LIST_APPEND / PROB_UPDATE → (PRUNE_EXPIRED) → QUERY_COUNT (aggregates) → SNAPSHOT / RESTORE.

---
## 🧠 Key Patterns
- Singleton: One in‑process counter for simplicity.
- Strategy: Swappable counting semantics without internal restructuring.
- Observer: Events for `hit_recorded`, `pruned`, `strategy_swapped`, `snapshot_taken`, `snapshot_restored`.
- Memento: Snapshot deep copy of endpoint state.
- State: Strategy influences bucket representation.

---
## ⚙ Strategies
1. Fixed Window (window_size_s): integer bucket key = floor(ts / window_size).
2. Sliding Window: keep ordered timestamps; prune older than query horizon.
3. Morris Approximation: probabilistic counter per endpoint (estimate = 2^c - 1).

---
## 📊 Metrics
- `total_hits`
- `endpoints_count`
- `pruned_events`
- `strategy` (current)
- `memory_entries` (raw structures)

---
## 🧪 Demo Scenarios
1. Basic fixed window counting
2. Sliding window precision vs fixed
3. Strategy swap to Morris approximate
4. Mixed endpoint hits + pruning
5. Snapshot, mutate, restore

Run:
```bash
python3 "INTERVIEW_COMPACT.py"
```

---
## 💬 Talking Points
- Trade-off: sliding precision vs fixed window memory efficiency.
- Approximate counting reduces memory footprint for high traffic.
- Strategy swap preserves logical totals (cannot convert approximate state to exact retroactively; note limitation).
- Pruning essential for sliding windows to bound memory.
- Snapshot gives instant rollback; alternative is write-ahead log.

---
## 🚀 Future Enhancements
- HyperLogLog for distinct user counting.
- Multi-level aggregation (minute/hour/day).
- Persistence & distributed sharding.
- Rate limiting integration (threshold checks).
- Adaptive window compression.

---
## ✅ Interview Closure
Show clear separations: strategy for counting, singleton orchestrator, events enabling observability, metrics, and extensible snapshot path for resilience & experimentation.


## Compact Code

```python
"""Compact Hit Counter with Strategy, Events, Snapshot
Run: python3 INTERVIEW_COMPACT.py
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional
import time
import random

# ---------------- Strategies -----------------
class CountingStrategy:
    def name(self) -> str:
        return self.__class__.__name__
    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        raise NotImplementedError
    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        raise NotImplementedError
    def prune(self, state: Dict[str, Any], endpoint: str, now: float) -> int:
        return 0
    def memory_entries(self, state: Dict[str, Any]) -> int:
        raise NotImplementedError

class FixedWindowStrategy(CountingStrategy):
    def __init__(self, window_size_s: int = 10) -> None:
        self.window_size_s = window_size_s
    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        buckets = state.setdefault(endpoint, {})  # bucket_key -> count
        bucket_key = int(ts // self.window_size_s)
        buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        buckets = state.get(endpoint, {})
        if not buckets:
            return 0
        start_bucket = int((now - last_seconds) // self.window_size_s)
        end_bucket = int(now // self.window_size_s)
        return sum(count for b, count in buckets.items() if start_bucket <= b <= end_bucket)
    def memory_entries(self, state: Dict[str, Any]) -> int:
        return sum(len(buckets) for buckets in state.values())

class SlidingWindowStrategy(CountingStrategy):
    def __init__(self, max_window_s: int = 60) -> None:
        self.max_window_s = max_window_s
    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        lst: List[float] = state.setdefault(endpoint, [])
        lst.append(ts)
    def prune(self, state: Dict[str, Any], endpoint: str, now: float) -> int:
        lst: List[float] = state.get(endpoint, [])
        if not lst:
            return 0
        cutoff = now - self.max_window_s
        # Remove outdated timestamps (keep order)
        original_len = len(lst)
        # Find first index >= cutoff
        keep_index = 0
        for i, t in enumerate(lst):
            if t >= cutoff:
                keep_index = i
                break
        else:
            keep_index = original_len  # all old
        removed = lst[:keep_index]
        lst[:] = lst[keep_index:]
        return len(removed)
    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        lst: List[float] = state.get(endpoint, [])
        if not lst:
            return 0
        cutoff = now - last_seconds
        # Binary search could optimize; linear for simplicity
        return sum(1 for t in lst if t >= cutoff)
    def memory_entries(self, state: Dict[str, Any]) -> int:
        return sum(len(lst) for lst in state.values())

class MorrisApproxStrategy(CountingStrategy):
    def record(self, state: Dict[str, Any], endpoint: str, ts: float) -> None:
        c = state.get(endpoint, 0)
        # Increment with probability 1 / 2^c
        if random.random() < 1 / (2 ** c if c > 0 else 1):
            c += 1
        state[endpoint] = c
    def query(self, state: Dict[str, Any], endpoint: str, now: float, last_seconds: int) -> int:
        # No temporal resolution; treat all hits as in window
        c = state.get(endpoint, 0)
        return int(2 ** c - 1)
    def memory_entries(self, state: Dict[str, Any]) -> int:
        return len(state)

# ---------------- Snapshot -----------------
@dataclass
class Snapshot:
    state: Dict[str, Any]
    metrics: Dict[str, int]

# ---------------- HitCounter Singleton -----------------
class HitCounter:
    _instance: Optional['HitCounter'] = None
    def __init__(self) -> None:
        self.strategy: CountingStrategy = FixedWindowStrategy(window_size_s=10)
        self.state: Dict[str, Any] = {}
        self.metrics: Dict[str, int] = {
            'total_hits': 0,
            'endpoints_count': 0,
            'pruned_events': 0,
            'memory_entries': 0,
        }
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
    @classmethod
    def instance(cls) -> 'HitCounter':
        if cls._instance is None:
            cls._instance = HitCounter()
        return cls._instance
    def register(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(fn)
    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    def record_hit(self, endpoint: str, ts: Optional[float] = None) -> None:
        ts = ts or time.time()
        self.strategy.record(self.state, endpoint, ts)
        # Prune if supported
        removed = self.strategy.prune(self.state, endpoint, ts)
        if removed:
            self.metrics['pruned_events'] += removed
            self._emit('pruned', {'endpoint': endpoint, 'removed': removed})
        self.metrics['total_hits'] += 1
        self.metrics['endpoints_count'] = len(self.state)
        self.metrics['memory_entries'] = self.strategy.memory_entries(self.state)
        self._emit('hit_recorded', {'endpoint': endpoint, 'ts': ts})
        self._emit('metrics_updated', {k: self.metrics[k] for k in ['total_hits','memory_entries']})
    def query_hits(self, endpoint: str, last_seconds: int) -> int:
        now = time.time()
        return self.strategy.query(self.state, endpoint, now, last_seconds)
    def swap_strategy(self, strategy: CountingStrategy) -> None:
        old = self.strategy.name()
        # If incompatible representation, reset state (cannot losslessly convert)
        if type(strategy) is not type(self.strategy):
            self.state = {}
            self.metrics['endpoints_count'] = 0
            self.metrics['memory_entries'] = 0
            self._emit('strategy_reset', {'from': old, 'to': strategy.name(), 'reason': 'incompatible_state_reset'})
        self.strategy = strategy
        self.metrics['memory_entries'] = self.strategy.memory_entries(self.state)
        self._emit('strategy_swapped', {'old': old, 'new': strategy.name()})
    def take_snapshot(self) -> Snapshot:
        snap = Snapshot(state={k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in self.state.items()}, metrics=self.metrics.copy())
        self._emit('snapshot_taken', {'endpoints_count': len(self.state)})
        return snap
    def restore_snapshot(self, snap: Snapshot) -> None:
        self.state = {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in snap.state.items()}
        self.metrics = snap.metrics.copy()
        self._emit('snapshot_restored', {})

# ---------------- Demo Helpers -----------------

def print_header(title: str) -> None:
    print(f"\n=== {title} ===")

def listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------- Demo Scenarios -----------------

def demo_1_fixed_window() -> None:
    print_header("Demo 1: Fixed Window Counting")
    hc = HitCounter.instance()
    hc.register(listener)
    for i in range(5):
        hc.record_hit("/home")
        time.sleep(0.05)
    count = hc.query_hits("/home", last_seconds=2)
    print("/home count last 2s:", count)


def demo_2_sliding_vs_fixed() -> None:
    print_header("Demo 2: Sliding vs Fixed Comparison")
    hc = HitCounter.instance()
    hc.swap_strategy(SlidingWindowStrategy(max_window_s=5))
    for i in range(10):
        hc.record_hit("/api")
        time.sleep(0.02)
    time.sleep(0.1)
    hc.record_hit("/api")
    print("/api sliding last 1s:", hc.query_hits("/api", 1))
    print("/api sliding last 5s:", hc.query_hits("/api", 5))


def demo_3_morris_approx() -> None:
    print_header("Demo 3: Morris Approximation Strategy")
    hc = HitCounter.instance()
    hc.swap_strategy(MorrisApproxStrategy())
    for i in range(100):
        hc.record_hit("/stream")
    est = hc.query_hits("/stream", 60)
    print("/stream approx count ~", est)


def demo_4_high_volume_prune() -> None:
    print_header("Demo 4: High Volume + Pruning")
    hc = HitCounter.instance()
    hc.swap_strategy(SlidingWindowStrategy(max_window_s=1))
    start = time.time()
    while time.time() - start < 1.2:
        hc.record_hit("/burst")
    print("/burst last 1s:", hc.query_hits("/burst", 1))
    print("Pruned events total:", hc.metrics['pruned_events'])


def demo_5_snapshot_restore() -> None:
    print_header("Demo 5: Snapshot & Restore")
    hc = HitCounter.instance()
    snap = hc.take_snapshot()
    for i in range(20):
        hc.record_hit("/home")
    after = hc.query_hits("/home", 10)
    hc.restore_snapshot(snap)
    restored = hc.query_hits("/home", 10)
    print("Count after extra hits:", after, "-> after restore:", restored)

# ---------------- Main -----------------
if __name__ == "__main__":
    demo_1_fixed_window()
    demo_2_sliding_vs_fixed()
    demo_3_morris_approx()
    demo_4_high_volume_prune()
    demo_5_snapshot_restore()

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
