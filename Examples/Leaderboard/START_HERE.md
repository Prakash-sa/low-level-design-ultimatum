# 🏆 Leaderboard System – Quick Start (5‑Minute Reference)

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
