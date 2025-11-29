# START HERE: Cache System Overview

## Quick Mental Model
A single `CacheManager` holds key→entry mappings. Each entry tracks metadata (timestamps, frequency, TTL, dirty flag). An eviction strategy updates metadata and selects victims when capacity constraints hit. A write policy defines persistence semantics with a backing store. Commands wrap reversible mutations; snapshots give coarse rollback.

## Core Classes
- `CacheManager(capacity_items: int, capacity_bytes: int, eviction_strategy, write_policy)`
- `CacheEntry(value, size, created_at, last_access, frequency, ttl, dirty)`
- `EvictionStrategy` implementations: LRU, LFU, FIFO
- `WritePolicy` implementations: WriteThrough, WriteBack
- Commands: `SetCommand`, `DeleteCommand`

## Typical Flows
Set:
1. Validate TTL and size constraints
2. Possibly evict victim(s) until under capacities
3. Insert/update entry; update strategy metadata
4. Write policy handles persistence (mark dirty or immediate write)
5. Emit events & update metrics

Get:
1. Check existence; expire if TTL passed
2. On hit: update access metadata & frequency
3. On miss: record metrics

Eviction:
- Triggered on `set` when crossing item or byte capacity
- Strategy `choose_victim` returns key; entry removed, metrics & event updated

Strategy Swap:
- Replace eviction strategy; rebuild metadata (frequency already in entries)
- Emit `strategy_swapped`

Write Policy Swap:
- If leaving write-back, perform flush first
- Emit `write_policy_swapped`

Undo / Redo:
- Command executes → push onto undo stack, clear redo
- Undo pops & reverses; redo reapplies

Snapshot:
- Deep copy entries & backing store, plus strategy/write policy identifiers & metrics baseline
- Restore wipes current state and reinstates snapshot, refreshing metrics

## Events (subscribe via `add_listener(fn)`) Example Payloads
- `entry_set`: { key, size }
- `entry_get_hit`: { key }
- `entry_get_miss`: { key }
- `entry_evicted`: { key, reason }
- `entry_expired`: { key }
- `strategy_swapped`: { from, to }
- `write_policy_swapped`: { from, to }
- `flushed`: { flushed_count }
- `snapshot_taken`: { items }
- `snapshot_restored`: {}
- `metrics_updated`: { hits, misses, ... }

## Metrics Insight
Use metrics to articulate operational efficiency: hit ratio, eviction pressure, expiration volume, dirty backlog (write-back).

## Interview Angles
- Why separate eviction & write strategies? Clear separation of residency vs persistence policy
- TTL handling: lazy vs proactive scheduling tradeoffs
- Command pattern boundaries (only state mutations, not strategy swaps)
- Snapshot atomicity & full replacement to avoid partial corruption

## Run the Demo
Execute: `python3 INTERVIEW_COMPACT.py` from `Examples/Cache/` to see all scenarios.

Proceed to `75_MINUTE_GUIDE.md` for a deep architectural narrative.
