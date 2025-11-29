# 🔢 Hit Counter – 75 Minute Deep Dive

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
