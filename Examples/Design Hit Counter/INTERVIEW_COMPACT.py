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
