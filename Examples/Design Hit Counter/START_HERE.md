# 🔢 Hit Counter – Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | record/query windows |
| 5–15 | Architecture | HitCounter + strategies + events |
| 15–35 | Implement strategies | Fixed, Sliding, Morris approx |
| 35–55 | Pruning + metrics | Memory control & instrumentation |
| 55–70 | Demos + snapshot | 5 scenarios |
| 70–75 | Q&A | Trade-offs & scaling |

## 🧱 Entities Cheat Sheet
HitCounter(strategy, endpoints_state, metrics)
CountingStrategy.record(endpoint, ts)
CountingStrategy.query(endpoint, now, last_seconds)
Strategies: FixedWindowStrategy, SlidingWindowStrategy, MorrisApproxStrategy
Snapshot(state_clone)

## 🛠 Patterns
Singleton (HitCounter)
Strategy (Counting semantics)
Observer (Events)
Memento (Snapshot)
State (Per-endpoint buckets/timestamps/counter value)

## 🎯 Demo Order
1. Fixed window baseline
2. Sliding window vs fixed comparative counts
3. Swap to Morris approximation
4. High-volume hits + pruning
5. Snapshot, mutate, restore

Run:
```bash
python3 "INTERVIEW_COMPACT.py"
```

## ✅ Checklist
- [ ] Strategy swap emits event
- [ ] Sliding pruning reduces memory entries
- [ ] Approximate count near actual for large N
- [ ] Snapshot restore returns previous totals
- [ ] Metrics updated after each record

## 💬 Quick Answers
Why strategies? → Swap accuracy/performance trade-offs transparently.
Why prune? → Prevent unbounded growth in sliding window.
Why approximate? → Reduce memory for massive traffic at cost of error.
Why snapshot? → Fast rollback & testing strategy effects.
Scaling path? → Shard counters + persist bucket deltas.

## 🆘 If Behind
<20m: Implement FixedWindowStrategy + basic record/query.
20–35m: Add SlidingWindowStrategy + pruning.
35–50m: Add Morris approx strategy.
>50m: Events, metrics, snapshot, demos.

Focus on accuracy vs memory trade-off narrative.
