"""Compact Leaderboard System
Run: python3 INTERVIEW_COMPACT.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Tuple
import time
import itertools

# ---------------- Player & ScoreEvent -----------------
@dataclass
class Player:
    player_id: str
    name: str

_score_event_counter = itertools.count(1)

def next_event_id() -> int:
    return next(_score_event_counter)

@dataclass(frozen=True)
class ScoreEvent:
    player_id: str
    value: float
    timestamp: float = field(default_factory=time.time)
    id: int = field(default_factory=next_event_id)

# ---------------- Aggregates -----------------
@dataclass
class PlayerAggregate:
    player_id: str
    total: float = 0.0
    count: int = 0
    last_update: float = field(default_factory=time.time)
    recent_scores: List[ScoreEvent] = field(default_factory=list)
    max_recent: int = 20

    def ingest(self, event: ScoreEvent) -> None:
        self.total += event.value
        self.count += 1
        self.last_update = event.timestamp
        self.recent_scores.append(event)
        if len(self.recent_scores) > self.max_recent:
            # keep only latest max_recent
            self.recent_scores = self.recent_scores[-self.max_recent :]

# ---------------- Ranking Strategies -----------------
class RankingStrategy:
    def name(self) -> str:
        return self.__class__.__name__
    def compute_score(self, agg: PlayerAggregate, now: float) -> float:
        raise NotImplementedError

class HighestScoreStrategy(RankingStrategy):
    def compute_score(self, agg: PlayerAggregate, now: float) -> float:
        return agg.total

class AverageScoreStrategy(RankingStrategy):
    def compute_score(self, agg: PlayerAggregate, now: float) -> float:
        if agg.count == 0:
            return 0.0
        return agg.total / agg.count

class RecentWeightedStrategy(RankingStrategy):
    def compute_score(self, agg: PlayerAggregate, now: float) -> float:
        score = 0.0
        for ev in agg.recent_scores:
            age_hours = (now - ev.timestamp) / 3600.0
            weight = 1.0 / (1.0 + age_hours)
            score += ev.value * weight
        return score

# ---------------- Stale Policy -----------------
class StalePolicy:
    def should_remove(self, agg: PlayerAggregate, now: float) -> bool:
        raise NotImplementedError
    def name(self) -> str:
        return self.__class__.__name__

class TimeSinceUpdatePolicy(StalePolicy):
    def __init__(self, max_idle_seconds: float) -> None:
        self.max_idle_seconds = max_idle_seconds
    def should_remove(self, agg: PlayerAggregate, now: float) -> bool:
        return (now - agg.last_update) > self.max_idle_seconds
    def name(self) -> str:
        return f"TimeSinceUpdate({self.max_idle_seconds}s)"

# ---------------- Leaderboard (Singleton) -----------------
class Leaderboard:
    _instance: Optional[Leaderboard] = None
    def __init__(self) -> None:
        self.players: Dict[str, Player] = {}
        self.aggregates: Dict[str, PlayerAggregate] = {}
        self.strategy: RankingStrategy = HighestScoreStrategy()
        self.stale_policy: Optional[StalePolicy] = None
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.metrics: Dict[str, int] = {
            "total_score_events": 0,
            "players_count": 0,
            "ranking_recomputes": 0,
            "stale_removed": 0,
        }
        self.last_recompute: float = time.time()
        self.cached_ranking: List[Tuple[str, float]] = []
    @classmethod
    def instance(cls) -> Leaderboard:
        if cls._instance is None:
            cls._instance = Leaderboard()
        return cls._instance
    def register_listener(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(fn)
    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    def add_player(self, player_id: str, name: str) -> None:
        if player_id not in self.players:
            self.players[player_id] = Player(player_id, name)
            self.aggregates[player_id] = PlayerAggregate(player_id)
            self.metrics["players_count"] = len(self.players)
            self._emit("player_added", {"player_id": player_id, "name": name})
    def ingest_score(self, player_id: str, value: float) -> None:
        now = time.time()
        if player_id not in self.players:
            self.add_player(player_id, player_id)
        agg = self.aggregates[player_id]
        ev = ScoreEvent(player_id=player_id, value=value, timestamp=now)
        agg.ingest(ev)
        self.metrics["total_score_events"] += 1
        self._emit("score_ingested", {"player_id": player_id, "value": value, "total": agg.total, "count": agg.count})
        self.recompute()
    def recompute(self) -> None:
        now = time.time()
        ranked: List[Tuple[str, float, PlayerAggregate]] = []
        for pid, agg in self.aggregates.items():
            score = self.strategy.compute_score(agg, now)
            ranked.append((pid, score, agg))
        # Sort by score desc, last_update desc, player_id asc
        ranked.sort(key=lambda x: (-x[1], -x[2].last_update, x[0]))
        self.cached_ranking = [(pid, score) for pid, score, _ in ranked]
        self.metrics["ranking_recomputes"] += 1
        self.last_recompute = now
        top_preview = self.cached_ranking[:5]
        self._emit("rankings_recomputed", {"strategy": self.strategy.name(), "top_preview": top_preview})
    def set_strategy(self, strategy: RankingStrategy) -> None:
        old = self.strategy.name()
        self.strategy = strategy
        self._emit("strategy_swapped", {"old": old, "new": strategy.name()})
        self.recompute()
    def set_stale_policy(self, policy: StalePolicy) -> None:
        self.stale_policy = policy
        self._emit("stale_policy_set", {"policy": policy.name()})
    def prune_stale(self) -> None:
        if not self.stale_policy:
            return
        now = time.time()
        self._emit("stale_check", {})
        removed: List[str] = []
        for pid in list(self.aggregates.keys()):
            agg = self.aggregates[pid]
            if self.stale_policy.should_remove(agg, now):
                removed.append(pid)
                del self.aggregates[pid]
                del self.players[pid]
        if removed:
            self.metrics["stale_removed"] += len(removed)
            self.metrics["players_count"] = len(self.players)
            self._emit("stale_removed", {"removed": removed})
            self.recompute()
    def top(self, n: int) -> List[Tuple[str, float]]:
        return self.cached_ranking[:n]
    def summary(self) -> Dict[str, Any]:
        age = time.time() - self.last_recompute
        data = dict(self.metrics)
        data["last_recompute_age_sec"] = round(age, 3)
        data["strategy"] = self.strategy.name()
        return data

# ---------------- Listener -----------------

def event_listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------- Demo Scenarios -----------------

def print_header(title: str) -> None:
    print("\n=== " + title + " ===")

def demo_1_setup_highest() -> None:
    print_header("Demo 1: Setup + Highest Score")
    lb = Leaderboard.instance()
    lb.register_listener(event_listener)
    lb.add_player("p1", "Alice")
    lb.add_player("p2", "Bob")
    lb.ingest_score("p1", 50)
    lb.ingest_score("p2", 40)
    lb.ingest_score("p1", 30)
    print("Top 2:", lb.top(2))


def demo_2_ties() -> None:
    print_header("Demo 2: Tie Handling")
    lb = Leaderboard.instance()
    lb.ingest_score("p2", 40)  # Bob total 80 ties Alice 80
    print("Top 2 after tie:", lb.top(2))


def demo_3_average_strategy() -> None:
    print_header("Demo 3: Average Strategy Swap")
    lb = Leaderboard.instance()
    lb.set_strategy(AverageScoreStrategy())
    print("Top 2 (average):", lb.top(2))


def demo_4_recent_weighted() -> None:
    print_header("Demo 4: Recent Weighted Strategy")
    lb = Leaderboard.instance()
    # Simulate older scores by manual timestamp adjustments
    # Manually age Alice's first score (simulate earlier timestamp)
    aged: List[ScoreEvent] = []
    for ev in lb.aggregates["p1"].recent_scores:
        aged.append(ScoreEvent(player_id=ev.player_id, value=ev.value, timestamp=ev.timestamp - 3600))
    lb.aggregates["p1"].recent_scores = aged
    lb.set_strategy(RecentWeightedStrategy())
    print("Top 2 (recent-weighted):", lb.top(2))


def demo_5_stale_prune_summary() -> None:
    print_header("Demo 5: Stale Prune + Summary")
    lb = Leaderboard.instance()
    lb.set_stale_policy(TimeSinceUpdatePolicy(max_idle_seconds=0.1))
    time.sleep(0.15)  # allow entries to become stale
    lb.prune_stale()
    print("Summary:", lb.summary())

# ---------------- Main -----------------
if __name__ == "__main__":
    demo_1_setup_highest()
    demo_2_ties()
    demo_3_average_strategy()
    demo_4_recent_weighted()
    demo_5_stale_prune_summary()
