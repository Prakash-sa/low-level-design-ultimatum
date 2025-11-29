# 🏆 Leaderboard System Design

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