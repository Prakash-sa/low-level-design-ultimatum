# 🏆 Leaderboard System – 75 Minute Deep Dive

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
