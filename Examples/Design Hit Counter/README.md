# 🔢 Hit Counter System Design

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
