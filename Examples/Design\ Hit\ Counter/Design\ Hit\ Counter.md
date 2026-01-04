# Design Hit Counter — 75-Minute Interview Guide

## Quick Start

**What is it?** Time-windowed request counter supporting multiple strategies (fixed-window buckets, sliding-window precise, probabilistic approximate) for tracking per-endpoint hit rates with real-time queries, pruning, and observability.

**Key Classes:**
- `HitCounter` (Singleton): Central coordinator
- `CountingStrategy` (ABC): Pluggable counting implementations
- `FixedWindowStrategy`: Bucket-based by window size
- `SlidingWindowStrategy`: Per-hit timestamp list with pruning
- `MorrisApproxStrategy`: Probabilistic counter (memory-efficient)
- `Snapshot`: Memento for state rollback

**Core Flows:**
1. **Record Hit**: Update counter → Optionally prune → Update metrics
2. **Query Count**: Aggregate hits in time window → Return total
3. **Swap Strategy**: Change counting approach → Reset incompatible state
4. **Snapshot/Restore**: Capture state for rollback/testing
5. **Emit Events**: Fire lifecycle notifications (recorded, pruned, swapped)

**5 Design Patterns:**
- **Singleton**: One HitCounter instance
- **Strategy**: Interchangeable counting semantics
- **Observer**: Events for lifecycle tracking
- **Memento**: Snapshot for state recovery
- **State Machine**: Per-endpoint bucket/timestamp/counter management

---

## System Overview

In-memory hit counter for rate limiting, analytics, and request tracking with pluggable accuracy/performance trade-offs.

### Requirements

**Functional:**
- Record hits per endpoint with timestamp
- Query hit count for last X seconds
- Support multiple counting strategies (fixed, sliding, approximate)
- Swap strategies transparently
- Prune old data to bound memory
- Emit events for lifecycle observability
- Snapshot state for testing/rollback

**Non-Functional:**
- Record operation < 1ms
- Query operation < 10ms
- Memory bounded (pruning prevents unbounded growth)
- Extensible for new strategies

**Constraints:**
- Single-process in-memory (no distribution)
- Fixed/sliding window strategies are exact; Morris is approximate
- Strategy swap cannot convert old state (reset required)
- No persistence (snapshots are in-memory only)

---

## Architecture Diagram (ASCII UML)

```
┌─────────────────────┐
│ HitCounter          │
│ (Singleton)         │
└──────────┬──────────┘
           │
    ┌──────┼────────────────────┐
    │      │                    │
    ▼      ▼                    ▼
┌──────────────────┐  ┌──────────────┐  ┌─────────────┐
│CountingStrategy  │  │State         │  │Events       │
│ (ABC)            │  │FixedWindow   │  │Listeners    │
└────┬─────┬───────┘  │SlidingWindow │  └─────────────┘
     │     │          │MorrisApprox  │
     ▼     ▼          └──────────────┘
┌──────────────┐   ┌──────────────┐
│FixedWindow   │   │Sliding       │
│Strategy      │   │Window        │
├──────────────┤   │Strategy      │
│- buckets     │   ├──────────────┤
│- record()    │   │- timestamps  │
│- query()     │   │- prune()     │
│- memory()    │   │- query()     │
└──────────────┘   └──────────────┘
     │                    │
     └────────┬───────────┘
              ▼
        ┌──────────────┐
        │Morris Approx │
        ├──────────────┤
        │- c (counter) │
        │- record()    │
        │- query()     │
        └──────────────┘

Lifecycle:
RECORD_HIT → STRATEGY_UPDATE → (PRUNE) → METRICS_UPDATE → QUERY
                ↓
            EMIT_EVENT (hit_recorded, pruned, strategy_swapped)
                ↓
            SNAPSHOT / RESTORE
```

---

## Interview Q&A (12 Questions)

### Basic Level

**Q1: How do you record and query hits?**
A: Record: call strategy.record(endpoint, timestamp) → updates internal state. Query: call strategy.query(endpoint, now, last_seconds) → aggregates hits in time window. Different strategies use different representations (buckets vs timestamps vs probabilistic counters).

**Q2: What's the difference between fixed and sliding window strategies?**
A: Fixed: divides time into buckets (e.g., 10-sec buckets). Record: increment bucket. Query: sum buckets overlapping window. Fast but coarse. Sliding: stores individual timestamps. Query: count timestamps >= (now - last_seconds). Exact but memory-intensive.

**Q3: What's Morris approximation?**
A: Probabilistic counter. On record: increment counter c with probability 1/(2^c). Estimate = 2^c - 1. Extremely memory-efficient (single int per endpoint) but has statistical error (~±50% for large counts). Used when memory is critical.

**Q4: Why do you need pruning?**
A: Sliding window stores all timestamps. Without pruning, memory grows unbounded. Pruning: remove timestamps older than max_window_s. Called each record/query. Metrics track pruned_events.

**Q5: How do you handle strategy swaps?**
A: Different strategies use incompatible internal representations (buckets vs lists vs ints). Strategy.swap(): if incompatible, reset state (document limitation). Cannot losslessly convert approximate state to exact. Emit strategy_swapped event.

### Intermediate Level

**Q6: How do you calculate fixed window bucket key?**
A: bucket_key = floor(timestamp / window_size_s). Example: ts=25.7s, window=10s → bucket=2. Multiple hits in same second go to same bucket. Query iterates buckets [floor((now-last_s)/window), floor(now/window)].

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

## Scaling Q&A (12 Questions)

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

## Demo Scenarios (5 Examples)

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

## Complete Implementation

```python
"""
⏱️ Design Hit Counter - Interview Implementation
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
    _lock = threading.Lock()
    
    def __new__(cls):
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
        self.lock = threading.Lock()
        print("⏱️ HitCounter initialized")
    
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
    print(f"\n  Morris estimate: {estimate} ≈ 1000 (statistical error acceptable)")
    print(f"  Memory entries: {hc.get_metrics()['memory_entries']}")

def demo_4_high_volume_prune():
    print_section("DEMO 4: HIGH-VOLUME PRUNING")
    
    hc = HitCounter()
    hc.swap_strategy(SlidingWindowStrategy(max_window_s=1))
    
    print("  Recording burst of 500 hits over 2 seconds...")
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

if __name__ == "__main__":
    print("\n" + "="*70)
    print("⏱️ DESIGN HIT COUNTER - 5 DEMO SCENARIOS")
    print("="*70)
    
    demo_1_fixed_window()
    demo_2_sliding_vs_fixed()
    demo_3_morris_approx()
    demo_4_high_volume_prune()
    demo_5_snapshot_restore()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED")
    print("="*70 + "\n")
```

---

## Design Patterns

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Singleton** | One HitCounter instance | Centralized state, no duplication |
| **Strategy** | CountingStrategy subclasses | Swap accuracy/performance trade-offs transparently |
| **Observer** | Event listeners on lifecycle | Observability, decoupled monitoring |
| **Memento** | Snapshot/Restore | Fast state rollback for testing |
| **State Machine** | Per-endpoint buckets/lists/counters | Clear separation of strategy concerns |

---

## Summary

✅ **Multiple strategies** (fixed window, sliding window, probabilistic)
✅ **Pluggable counting logic** with Strategy pattern
✅ **Pruning** prevents unbounded memory growth in sliding window
✅ **Metrics tracking** (total_hits, pruned_events, memory_entries)
✅ **Events** (hit_recorded, pruned, strategy_swapped, snapshot_taken)
✅ **Snapshot/restore** for testing and rollback
✅ **Per-endpoint state** management
✅ **Scales** from 1K to 1M+ requests/second
✅ **Memory-efficient** options (Morris approximation)
✅ **Extensible** for custom strategies

**Key Takeaway**: Hit counter demonstrates strategy pattern (swappable accuracy/performance), observability via events, and memory-bounded data structures. Core focus: understand windowing strategies, pruning discipline, and selecting strategy based on SLA (accuracy vs memory).
