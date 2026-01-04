# Leaderboard — 75-Minute Interview Guide

## Quick Start Overview

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Players, score events, ranking |
| 5–15 | Architecture | Leaderboard + strategies + events |
| 15–35 | Core Code | Aggregation + strategies + recompute |
| 35–55 | Tie & decay | Weighted strategy + pruning |
| 55–70 | Demos | 5 scenarios verifying lifecycles |
| 70–75 | Q&A | Trade-offs & scaling story |

## 🧱 Entities Cheat Sheet
Player(id, name)
ScoreEvent(id, player_id, value, ts)
Leaderboard: aggregates[player_id] -> {total, count, recent_scores, last_update}
RankingStrategy.rank(aggregates) -> sorted list
StalePolicy.should_remove(aggregate) -> bool

Strategies: HighestScore, AverageScore, RecentWeighted

## 🛠 Patterns
Singleton (Leaderboard)
Strategy (Ranking, StalePolicy)
Observer (Events)
State (Last recompute timestamp)
Factory (ScoreEvent creation)

## 🎯 Demo Order
1. Setup + highest score
2. Tie handling after updates
3. Switch to average ranking
4. Switch to recent-weighted ranking (simulate decay)
5. Apply stale pruning + metrics summary

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Checklist
- [ ] Recompute after each score event
- [ ] Strategy swap triggers recompute
- [ ] Tie ordering deterministic
- [ ] Decay changes ranking order over time
- [ ] Stale removal emits events & updates metrics

## 💬 Quick Answers
Why separate ranking? → Swap scoring formulas without touching ingestion.
Why decay? → Emphasizes active performance vs historical accumulation.
How tie-break? → Secondary keys (last_update, player_id) for stability.
Scaling path? → Shard by player ranges + distributed sorted sets (Redis / DB indexes).
Pruning value? → Memory control + relevance.

## 🆘 If Behind
<20m: Implement Player, ScoreEvent, Leaderboard, HighestScore.
20–40m: Add average + ranking recompute + metrics.
40–55m: Add recent-weighted + tie logic.
>55m: Add stale policy + events + demos.

Focus on strategy swap narrative & ranking stability.


## 75-Minute Guide

## 1. Problem Framing (0–5)
Design an in-memory leaderboard tracking player rankings based on score submissions. Support multiple ranking formulas, deterministic ties, time-decay weighting, stale pruning, metrics & events.

Must:
- Ingest score events
- Compute ranks with pluggable strategy
- Emit events on changes
- Maintain aggregates per player

Stretch:
- Time-decay weighted scores
- Stale removal policy
- Metrics summary

## 2. Requirements & Constraints (5–10)
Functional:
- Rank retrieval (top N)
- Strategy hot-swap without data loss
- Deterministic ordering for ties

Non-Functional:
- O(1) ingest update (aggregate update only)
- Recompute complexity O(P log P) (sorting)
- Extensible: new strategy adds one class

Assumptions:
- Single process; no persistence
- Score event values positive integers/floats

## 3. Domain Model (10–18)
Entities:
- Player(id, name)
- ScoreEvent(id, player_id, value, timestamp)
- Aggregate: total, count, last_update, recent_scores list
- Leaderboard: aggregates dict, strategy, stale_policy, metrics
- RankingStrategy: rank(aggregates) -> ordered list
- StalePolicy: should_remove(agg, now) -> bool

Relationships:
Leaderboard → aggregates[player_id]
RankingStrategy consumes aggregates; returns sorted [(player_id, score, metadata)].

## 4. Patterns (18–26)
Singleton Leaderboard: centralized state.
Strategy: ranking + stale policy replaceable.
Observer: event emission for ingestion, recompute, stale removal, strategy swap.
State: last_recompute timestamp.
Factory: ScoreEvent creation with monotonic ID.

## 5. Lifecycle (26–32)
SCORE_EVENT_CREATED → INGESTED(aggregate mutated) → RECOMPUTE → RANKINGS_READY → QUERY_TOP.
Stale removal: PERIODIC_CHECK → REMOVED → RECOMPUTE.

Invariants:
1. Aggregates always reflect sum & count of processed events for player.
2. Strategy swap triggers immediate recompute.
3. Tie ordering stable across recomputes given same aggregate state.
4. Stale removal reduces players_count metric and triggers recompute.

## 6. Ranking Strategies (32–40)
HighestScoreStrategy:
score = aggregate.total
AverageScoreStrategy:
score = aggregate.total / aggregate.count
RecentWeightedStrategy:
score = Σ(each recent_score.value * weight(age))
weight(age_hours) = 1 / (1 + age_hours)
Maintain recent_scores bounded (e.g., last 20 submissions).

## 7. Tie Handling (40–45)
Primary key: computed score (desc)
Secondary: last_update (more recent first)
Tertiary: player_id (lexicographic) ensures deterministic total ordering.

## 8. Stale Policy (45–50)
TimeSinceUpdatePolicy(max_idle_seconds)
If (now - aggregate.last_update) > max_idle: candidate for removal.
Trigger event and recompute after batch removal.

## 9. Metrics (50–55)
- total_score_events
- players_count
- ranking_recomputes
- stale_removed
- last_recompute_age_sec (derived)

## 10. Events (55–58)
Names:
- score_ingested
- rankings_recomputed
- strategy_swapped
- stale_removed
- stale_check
Payload: player_id, counts, strategy name, removed list, top sample.

## 11. Demo Scenarios (58–66)
1. Setup + initial scores (highest score)
2. More scores causing ties
3. Swap to average strategy alters order
4. Swap to recent-weighted (simulate artificial aging)
5. Apply stale policy + summary metrics

## 12. Trade-offs (66–72)
Per-event recompute vs batched: latency vs throughput.
Decay weighting: favors recency but adds CPU overhead.
Average vs total: fairness for varying activity levels.
Removal policy: memory vs historical continuity.
Singleton simplicity vs scalability (distributed sorted sets).

## 13. Extensions (72–75)
- Persistent append-only event log
- Redis sorted set backend for large scale
- Seasonal leaderboards with reset & archive
- Movement events (rank_change) detection
- Elo/MMR strategy with opponent strength weighting

## Summary
Flexible leaderboard: ingestion + aggregate updates O(1), ranking formula decoupled by strategy, deterministic ordering, optional staleness pruning, comprehensive events & metrics enabling scaling discussion.


## Detailed Design Reference

Pattern-aligned with the Airline Management System style: clear lifecycle, strategies, observer events, metrics, extensibility.

---
## 🎯 Goal
Maintain ranked list of players based on score inputs with pluggable ranking strategies (highest-total, average, recent-weighted), tie handling, stale entry pruning, and observable events.

---
## 🧱 Core Components
| Component | Responsibility | Patterns |
|-----------|----------------|----------|
| `Player` | Identity, metadata | Value Object |
| `ScoreEvent` | Immutable scoring input | Value Object |
| `Leaderboard` | Stores aggregates, computes rankings | Singleton, Strategy, Observer |
| `RankingStrategy` | Defines ranking computation | Strategy |
| `StalePolicy` | Determines pruning logic | Strategy (optional) |
| `Metrics` | Track counts & latencies | Aggregator |
| `Events` | Lifecycle notifications | Observer |

---
## 🔄 Score Lifecycle
SCORE_EVENT_CREATED → INGESTED → AGGREGATED → RECOMPUTED_RANKINGS → (EMITTED_TOP | IDLE). Pruning: STALE_CHECK → REMOVED.

---
## 🧠 Key Patterns
- Singleton Leaderboard: central coordination of state.
- Strategy Ranking: swap formula without touching aggregation store.
- Strategy StalePolicy: optional pluggable removal rule.
- Observer: events for score_ingested, rankings_recomputed, strategy_swapped, stale_removed.
- State: leaderboard holds last recompute timestamp.
- Factory: helper creates ScoreEvent with monotonic id.

---
## ⚙ Ranking Strategies
1. `HighestScoreStrategy`: rank by total accumulated points.
2. `AverageScoreStrategy`: rank by average of scores (min samples threshold optional).
3. `RecentWeightedStrategy`: apply time-decay weight (e.g., weight = 1/(1+age_hours)).

Tie-breakers: deterministic secondary key (higher last_update timestamp, then player id).

---
## 🛡 Stale Policy (Optional)
`TimeSinceUpdatePolicy(max_idle_seconds)` – remove players not updated recently.

---
## 📊 Metrics
- total_score_events
- players_count
- ranking_recomputes
- stale_removed
- last_recompute_age_sec

---
## 🧪 Demo Scenarios
1. Basic setup + highest score ranking
2. Multiple updates + tie resolution
3. Strategy swap to average ranking
4. Strategy swap to recent-weighted (time decay simulation)
5. Stale pruning + metrics summary

---
## 🗂 Files
- `START_HERE.md` – quick cheat sheet
- `75_MINUTE_GUIDE.md` – deep dive
- `INTERVIEW_COMPACT.py` – runnable compact implementation

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

---
## 💬 Talking Points
- Why separate aggregate vs ranking strategy: enables adding percentile/elo without rewriting ingestion.
- Handling ties: deterministic ordering ensures stability across recomputes.
- Time-decay approach: simple inverse age weighting; production systems may use exponential decay.
- Stale pruning: keeps leaderboard responsive & memory bound.
- Scaling: sharding by player ID range / distributed caches.

---
## 🚀 Future Enhancements
- Persistent event log for recompute/replay.
- Distributed caching & eventual consistency (CRDT or sorted set in Redis).
- Partitioned leaderboards (regional / seasonal).
- Rollback capability via snapshots.
- Ranking delta notifications for movement events.

---
## ✅ Interview Closure
Show ingestion pipeline, ranking strategy swap, events + metrics, deterministic ties, and scaling path (distributed, persistent, more complex scoring).


## Compact Code

```python
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
