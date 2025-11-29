# 🪵 Logging System – Quick Start (5‑Minute Reference)

## ⏱️ Timeline
| Time | Focus | Output |
|------|-------|--------|
| 0–5  | Requirements | Levels, formatter, sink, filter |
| 5–15 | Architecture | Logger + strategies + events |
| 15–35 | Core Classes | LogRecord, strategies, Logger |
| 35–55 | Buffering & Metrics | Buffered sink + counters |
| 55–70 | Demos | 5 scenarios exercising lifecycle |
| 70–75 | Q&A | Trade-offs & scaling story |

## 🧱 Entities Cheat Sheet
LogRecord(id, level, msg, context, ts)
Logger: formatter_strategy, sink_strategy, filter_strategy, metrics
FormatterStrategy.format(record)
SinkStrategy.emit(formatted, record)
BufferedSink(buffer[], flush())
FilterStrategy.accept(record)

Levels: DEBUG < INFO < WARN < ERROR < CRITICAL

## 🛠 Patterns
Singleton (Logger)
Strategy (Formatter, Sink, Filter)
Observer (Events)
State (Buffered sink flush status)
Factory (Record creation wrapper)

## 🎯 Demo Order
1. Basic console logging
2. Threshold filter blocks DEBUG
3. Swap to JSON + memory sink
4. Buffered console accumulate & flush
5. Correlated context + metrics summary

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

## ✅ Checklist
- [ ] Filter prevents low-level logs after threshold raise
- [ ] Buffer flush clears buffer and emits batch event
- [ ] Strategy swaps emit events
- [ ] Metrics reflect counts accurately
- [ ] Context keys appear in JSON formatter

## 💬 Quick Answers
Why strategies? → Swap behavior without touching core.
Why filter first? → Avoid unnecessary formatting cost.
Why buffer? → Batch I/O reducing overhead at cost of latency.
How extend? → New sink class + swap at runtime.
Scaling path? → Async queue, structured output → ingestion pipeline.

## 🆘 If Behind
<20m: Implement Logger + simple formatter + console sink.
20–40m: Add filter + metrics.
40–55m: Buffered sink + flush.
>55m: JSON formatter + demos + events.

Focus on lifecycle clarity & extension narrative.
