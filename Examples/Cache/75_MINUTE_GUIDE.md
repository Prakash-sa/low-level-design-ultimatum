# 75-Minute Guide: Designing a Strategy-Driven Cache

## 0-5m: Problem Framing
Interview Prompt Version: "Design an in-memory cache with configurable eviction and TTL support. Support persistence and observability."
We target adaptability (swap eviction algorithms), reliability (correct expiration & flush semantics), and transparency (metrics & events).

## 5-15m: Requirements Decomposition
Functional:
- put(key, value, ttl?)
- get(key)
- delete(key)
- capacity limits (items, bytes)
- eviction strategies (LRU, LFU, FIFO baseline)
- TTL expiration (lazy check)
- Write policies (write-through vs write-back)
- Snapshot & restore
- Undo/redo for modifications (value layer)
Non-Functional:
- O(1) avg key access
- Stable event emission for monitoring
- Strategy interchange without downtime
- Bounded metadata overhead

## 15-25m: Choosing Patterns
- Singleton: A single authoritative cache manager simplifies coherence.
- Strategy: Encapsulate eviction algorithms; isolate persistence semantics.
- Observer: Publish lifecycle transitions for instrumentation.
- Command: Fine-grained reversible mutations (set/delete) vs coarse snapshot.
- Memento: Whole-system state checkpoint & rollback.
- State-rich Entries: Per-key telemetry enabling multi-dimensional eviction.

## 25-35m: Data Structures
Core map: `dict[str, CacheEntry]`. For LRU: maintain last_access timestamps only (avoid full ordered dict if timestamps suffice). For LFU: rely on frequency counters inside entries; victim selection scans (optimization later to buckets). For FIFO: keep insertion ordering via stored created_at or a monotonic counter.
TTL expiration is lazy: on access or during periodic operations, purge stale entries.
Capacity enforcement triggers repeated victim selection until constraints satisfied.

## 35-45m: Strategy Interfaces
EvictionStrategy:
- `on_insert(key, entry)`: allow capturing metadata or ordering adjustments.
- `on_access(key, entry)`: update recency/frequency.
- `choose_victim(store) -> key | None`: define removal policy.
WritePolicy:
- `on_set(key, entry, backing_store)`
- `on_delete(key, backing_store)`
- `flush(backing_store, entries) -> count`

## 45-55m: Lifecycle & Algorithms
Set Flow:
1. Normalize value; compute size.
2. Evict while over capacity (items or bytes).
3. Insert/update entry; bump frequency (if new set frequency=1 else unchanged?).
4. Strategy hooks, write policy action.
5. Emit metrics & events.
Get Flow:
1. Miss? record & emit.
2. Expired? remove & treat as miss.
3. Hit: update access metadata & strategy; emit.
Eviction Loop: Repeated `choose_victim` until constraints satisfied or no victim (defensive fallback).

## 55-60m: Undo/Redo vs Snapshot
Command targeted at key-level operations: `SetCommand` holds previous value/entry; `DeleteCommand` holds removed entry. Strategy swaps affect global invariants—too broad for simple reversal; snapshot covers that.
Snapshot tradeoff: memory overhead vs recovery speed. Suitable for interview demonstration.

## 60-65m: Metrics & Observability
Increment counters at mutation edges. Recompute `current_items`, `total_bytes` cheaply. Dirty backlog reflects persistence risk (write-back). Hit ratio derived externally: hits / (hits + misses).
Events unify instrumentation pipeline; consumer could log, aggregate, or drive dashboards.

## 65-70m: Strategy Swapping & Consistency
Eviction strategy swap leaves entries untouched; only victim selection logic changes. Frequency counters remain valid across strategies. Write policy swap from write-back to write-through triggers flush first, protecting durability.

## 70-75m: Extensions & Tradeoffs
Scaling:
- LFU optimization: frequency buckets mapping to ordered sets for O(1) victim retrieval.
- Segmented LRU (S-LRU) or ARC for dynamic adaptation between recency & frequency dimensions.
- Size-based multi-constraint eviction (value size + frequency weighting).
Durability:
- Periodic background flush thread for write-back.
- Journaling changes for crash recovery.
Distribution:
- Shard by key hash (consistent hashing) for parallelism; each shard retains same architecture.
- Promote hot keys into fast tier (e.g., local memory layer + remote store).

## Interview Narration Tips
1. Start with baseline map + TTL.
2. Introduce Strategy for eviction—show how adding new algorithm avoids touching core logic.
3. Add WritePolicy to cleanly separate persistence semantics.
4. Observer events demonstrate production-readiness & monitoring.
5. Command vs Snapshot: differentiate granularity of rollback.
6. Discuss complexity tradeoffs (LFU scanning vs bucketed LFU) and evolve design iteratively.
7. Close with extension suggestions (segmented, shard, async flush).

## Complexity Summary
- put/get baseline O(1) dictionary operations
- Eviction victim selection naive scan: O(n) worst-case (acceptable in interview; optimize later)
- LFU improvement path: O(1) updates via bucket linked structures

## Failure Scenarios & Handling
- Over-capacity with no victim: stop & emit warning event (prevent infinite loop)
- Write-back flush failure: capture exception and emit `flush_error` (placeholder for production)
- Expiration race: lazy model tolerates stale window; proactive scheduler optional.

## Security & Validation Notes
- Size accounting prevents memory blow-ups
- TTL avoids eternal residency of stale keys
- Snapshot restore integrity: full replacement reduces partial injection risk

Proceed to `INTERVIEW_COMPACT.py` for hands-on exploration.
