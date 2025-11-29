# Cache System (Airline-Style Architecture)

## Purpose
An in-memory, observable, strategy-driven cache supporting multiple eviction algorithms (LRU, LFU, FIFO, TTL), pluggable write policies (write-through / write-back), undoable mutations via Command pattern, snapshot & restore (Memento), and rich metrics emission.

## Core Goals
- Predictable eviction & expiration behavior
- Easy runtime strategy swapping without losing integrity
- Observability of cache lifecycle: hits, misses, evictions, expirations, flushes
- Extensibility: add new eviction or write policies with minimal friction
- Reversibility: undo/redo for set/delete operations when desired
- Consistency: snapshot state & restore safely

## Patterns Employed
| Pattern | Usage |
|---------|-------|
| Singleton | `CacheManager` orchestrates store & strategies |
| Strategy | Eviction (`LRUStrategy`, `LFUStrategy`, `FIFOStrategy`), Write Policy (`WriteThroughPolicy`, `WriteBackPolicy`) |
| Observer | Event listeners receive cache lifecycle events |
| Command | `SetCommand`, `DeleteCommand` encapsulate reversible actions |
| Memento | `take_snapshot` / `restore_snapshot` capture & roll back state |
| State | Entry metadata (access count, dirty flag, timestamps) forming micro-state machine |

## Key Components
- `CacheEntry`: dataclass capturing value, size, frequency, timestamps, TTL, dirty flag
- `EvictionStrategy`: interface for deciding victim & updating metadata
- `WritePolicy`: interface controlling persistence interactions with a backing store
- `CacheManager`: high-level API for set/get/delete, strategy swapping, metrics, snapshot, flush
- `Command` subclasses: reversible mutations integrated with undo/redo stacks

## Metrics Tracked
- `hits`, `misses`, `evictions`, `expirations`
- `sets`, `deletes`, `dirty_writes_pending`, `flushed_writes`
- `current_items`, `total_bytes`

## Events Emitted (Sample)
- `entry_set`, `entry_get_hit`, `entry_get_miss`, `entry_evicted`, `entry_expired`
- `strategy_swapped`, `write_policy_swapped`
- `snapshot_taken`, `snapshot_restored`
- `flushed`, `command_executed`, `command_undone`, `command_redone`
- `metrics_updated`

## Strategy Swapping Rules
- Eviction strategy swap recalculates internal ordering metadata but preserves entries.
- Write policy swap flushes if moving from write-back to write-through to avoid dirty loss.

## Undo/Redo Behavior
- Executing a new command clears redo stack.
- Undo reverses last command; redo reapplies it.
- Non-command mutations (e.g., strategy swap) are not undoable, use snapshot for coarse rollback.

## Snapshot Semantics
- Deep copy of entries & backing store plus active strategies' identifiers.
- Restore replaces entire current store; metrics recomputed.

## Extensibility Points
- Add eviction strategies by implementing: `on_insert`, `on_access`, `choose_victim`.
- Add write policies by implementing: `on_set`, `on_delete`, `flush`.
- Add custom metrics or event types in `CacheManager._emit_event`.

## Demo Scenarios (in `INTERVIEW_COMPACT.py`)
1. Basic LRU put/get & eviction
2. TTL expiration lifecycle
3. Eviction strategy swap (LRU -> LFU)
4. Write policy swap (write-through -> write-back -> flush)
5. Snapshot & restore integrity
6. High volume load with periodic pruning & metrics summary

## Interview Talking Points
- Tradeoffs between eviction strategies (recency vs frequency vs insertion order)
- Memory vs CPU overhead of maintaining auxiliary metadata (frequency counters)
- Write-back optimization vs risk of data loss; flush & dirty tracking
- TTL expiration asynchronous vs synchronous (current: lazy-on-access purge)
- Multi-tier future extension (e.g., promoting hot keys to faster layer)

## Possible Extensions
- Segmented LRU / ARC for adaptive recency vs frequency balance
- Size-based eviction combining bytes threshold with strategy priority
- Async flush queue for write-back policy
- Sharding for concurrency & lock minimization
- Prometheus metrics exporter / structured JSON event sink

---
Use the compact script for a guided execution showcasing all interactions.
