"""Compact Interview Script: Strategy-Driven Cache System
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
        # Lowest frequency; tie-breaker oldest access
        return min(store.items(), key=lambda kv: (kv[1].frequency, kv[1].last_access))[0]

class FIFOStrategy(EvictionStrategy):
    name = "fifo"
    def on_insert(self, key: str, entry: CacheEntry) -> None:
        # created_at already set
        pass
    def on_access(self, key: str, entry: CacheEntry) -> None:
        entry.frequency += 1  # still track for metrics
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
        return 0  # no-op

class WriteBackPolicy(WritePolicy):
    name = "write_back"
    def on_set(self, key: str, entry: CacheEntry, backing_store: Dict[str, Any]) -> None:
        entry.dirty = True
    def on_delete(self, key: str, backing_store: Dict[str, Any]) -> None:
        # If deleting a dirty entry before flush, propagate delete to backing store
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
        # restore previous or delete
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
# Cache Manager (Singleton-like)
# =============================
class CacheManager:
    def __init__(self,
                 capacity_items: int,
                 capacity_bytes: int,
                 eviction_strategy: EvictionStrategy,
                 write_policy: WritePolicy):
        self.capacity_items = capacity_items
        self.capacity_bytes = capacity_bytes
        self.eviction_strategy = eviction_strategy
        self.write_policy = write_policy
        self._store: Dict[str, CacheEntry] = {}
        self._backing_store: Dict[str, Any] = {}
        self._listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
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

    # ---- Public API ----
    def add_listener(self, fn: Callable[[str, Dict[str, Any]], None]):
        self._listeners.append(fn)

    def set(self, key: str, value: Any, ttl: Optional[float] = None, via_command: bool = False):
        size = self._estimate_size(value)
        now = time.time()
        if key in self._store:
            entry = self._store[key]
            entry.value = value
            entry.size = size
            entry.ttl = ttl
            entry.last_access = now
            # frequency retained; treat update as access
        else:
            entry = CacheEntry(value=value, size=size, created_at=now, last_access=now, ttl=ttl)
            self._store[key] = entry
            self.eviction_strategy.on_insert(key, entry)
        # capacity enforcement
        self._enforce_capacity()
        # write policy
        self.write_policy.on_set(key, entry, self._backing_store)
        self._metrics['sets'] += 1
        self._refresh_metrics()
        self._emit_event('entry_set', {'key': key, 'size': size})
        if not via_command:
            self._record_command(SetCommand(self, key, value, ttl), executed=True)

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        entry = self._store.get(key)
        if entry is None:
            self._metrics['misses'] += 1
            self._refresh_metrics()
            self._emit_event('entry_get_miss', {'key': key})
            return None
        if entry.expired(now):
            # expire
            self._store.pop(key, None)
            self._metrics['expirations'] += 1
            self._emit_event('entry_expired', {'key': key})
            self._metrics['misses'] += 1
            self._refresh_metrics()
            return None
        # hit
        entry.last_access = now
        entry.frequency += 1
        self.eviction_strategy.on_access(key, entry)
        self._metrics['hits'] += 1
        self._refresh_metrics()
        self._emit_event('entry_get_hit', {'key': key})
        return entry.value

    def delete(self, key: str, via_command: bool = False):
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
        prev = self.eviction_strategy.name
        self.eviction_strategy = new_strategy
        # Re-init entries for new strategy insertion semantics
        for k, e in self._store.items():
            new_strategy.on_insert(k, e)
        self._emit_event('strategy_swapped', {'from': prev, 'to': new_strategy.name})

    def swap_write_policy(self, new_policy: WritePolicy):
        prev = self.write_policy.name
        # if leaving write-back ensure flush
        if isinstance(self.write_policy, WriteBackPolicy) and not isinstance(new_policy, WriteBackPolicy):
            flushed = self.write_policy.flush(self._backing_store, self._store)
            self._metrics['flushed_writes'] += flushed
            self._emit_event('flushed', {'flushed_count': flushed})
        self.write_policy = new_policy
        self._emit_event('write_policy_swapped', {'from': prev, 'to': new_policy.name})
        self._refresh_metrics()

    def flush(self):
        flushed = self.write_policy.flush(self._backing_store, self._store)
        if flushed:
            self._metrics['flushed_writes'] += flushed
            self._emit_event('flushed', {'flushed_count': flushed})
            self._refresh_metrics()

    def take_snapshot(self) -> Dict[str, Any]:
        snap = {
            'store': copy.deepcopy(self._store),
            'backing': copy.deepcopy(self._backing_store),
            'eviction_strategy': self.eviction_strategy.name,
            'write_policy': self.write_policy.name,
            'metrics': copy.deepcopy(self._metrics),
            'timestamp': time.time(),
        }
        self._emit_event('snapshot_taken', {'items': len(self._store)})
        return snap

    def restore_snapshot(self, snapshot: Dict[str, Any]):
        self._store = snapshot['store']
        self._backing_store = snapshot['backing']
        self._metrics = snapshot['metrics']
        # strategies rebind by name
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
        return copy.deepcopy(self._metrics)

    # ---- Internal Helpers ----
    def _emit_event(self, name: str, payload: Dict[str, Any]):
        for listener_fn in self._listeners:
            try:
                listener_fn(name, payload)
            except Exception:
                pass

    def _estimate_size(self, value: Any) -> int:
        # Simplified size heuristic; refine if needed
        if isinstance(value, (str, bytes)):
            return len(value)
        return 1

    def _current_total_bytes(self) -> int:
        return sum(e.size for e in self._store.values())

    def _enforce_capacity(self):
        # Evict while over capacity
        safety = 0
        while (len(self._store) > self.capacity_items or self._current_total_bytes() > self.capacity_bytes) and safety < 10_000:
            victim = self.eviction_strategy.choose_victim(self._store)
            if victim is None:
                self._emit_event('eviction_blocked', {})
                break
            removed = self._store.pop(victim)
            if removed.dirty:
                # propagate delete to backing if write-back not flushed yet
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
            # command already executed externally
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
        self._store[key] = entry
        self._refresh_metrics()
        self._emit_event('entry_set', {'key': key, 'size': entry.size, 'restore': True})

# =============================
# Demo / Showcase
# =============================

def listener(event: str, payload: Dict[str, Any]):
    if event in {"metrics_updated"}:  # reduce noise; comment out to view all
        return
    print(f"[EVENT] {event} -> {payload}")


def demo():
    cache = CacheManager(capacity_items=5,
                         capacity_bytes=50,
                         eviction_strategy=LRUStrategy(),
                         write_policy=WriteThroughPolicy())
    cache.add_listener(listener)

    print("=== Demo 1: Basic LRU & Eviction ===")
    for i in range(7):  # exceed capacity items
        cache.set(f"k{i}", f"value-{i}")
    # access some keys to update recency
    cache.get("k3")
    cache.get("k4")
    cache.set("k_new", "new-value")  # triggers eviction
    print("Summary after Demo 1:", cache.summary())

    print("\n=== Demo 2: TTL Expiration ===")
    cache.set("temp", "short", ttl=0.2)
    time.sleep(0.25)
    v = cache.get("temp")  # should expire
    print("Value after TTL expiration (expect None):", v)
    print("Summary after Demo 2:", cache.summary())

    print("\n=== Demo 3: Strategy Swap (LRU -> LFU) ===")
    cache.swap_eviction_strategy(LFUStrategy())
    # generate access skew
    for _ in range(5):
        cache.get("k3")
    for _ in range(2):
        cache.get("k4")
    cache.set("heavy", "payload")  # may evict least freq
    print("Summary after Demo 3:", cache.summary())

    print("\n=== Demo 4: Write Policy Swap (Through -> Back -> Flush) ===")
    cache.swap_write_policy(WriteBackPolicy())
    cache.set("wb1", "alpha")
    cache.set("wb2", "beta")
    print("Dirty pending before flush:", cache.summary()['dirty_writes_pending'])
    cache.flush()
    print("Dirty pending after flush:", cache.summary()['dirty_writes_pending'])
    cache.swap_write_policy(WriteThroughPolicy())  # triggers flush if dirty (none now)

    print("Backing store keys:", list(cache._backing_store.keys()))

    print("\n=== Demo 5: Snapshot & Restore ===")
    snap = cache.take_snapshot()
    cache.set("snap_extra", "zzz")
    print("Items after extra set:", cache.summary()['current_items'])
    cache.restore_snapshot(snap)
    print("Items after restore (should revert):", cache.summary()['current_items'])

    print("\n=== Demo 6: High Volume & Metrics ===")
    for i in range(200):
        cache.set(f"bulk{i}", i % 10)
        cache.get(f"bulk{i}")
    print("Final Summary:", cache.summary())

    print("\n=== Demo 7: Command Undo/Redo ===")
    set_cmd = SetCommand(cache, "cmd_key", "cmd_value")
    set_cmd.execute()
    delete_cmd = DeleteCommand(cache, "cmd_key")
    delete_cmd.execute()
    print("Exists after delete:", cache.get("cmd_key"))
    cache.undo()  # undo delete
    print("Value after undo delete:", cache.get("cmd_key"))
    cache.undo()  # undo set (removes key)
    print("Value after undo set (expect None):", cache.get("cmd_key"))
    cache.redo()  # redo set
    print("Value after redo set:", cache.get("cmd_key"))

if __name__ == "__main__":
    demo()
