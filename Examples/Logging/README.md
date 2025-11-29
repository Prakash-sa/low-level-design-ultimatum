# 🪵 Logging System Design

Structured redesign aligned with the Airline Management System pattern approach: emphasize modularity (strategies), observability (events), lifecycle/state, and extensibility.

---
## 🎯 Goal
Provide a flexible in‑process logging framework supporting pluggable formatters, sinks, filters, buffering & metrics with minimal coupling.

---
## 🧱 Core Components
| Component | Responsibility | Patterns |
|-----------|----------------|----------|
| `LogRecord` | Immutable snapshot of an event | Value Object |
| `LogLevel` | Severity taxonomy | Enum |
| `Logger` | Orchestrates formatting, filtering, sink dispatch | Singleton, Strategy, Observer |
| `FormatterStrategy` | Convert record → output string | Strategy |
| `SinkStrategy` | Deliver formatted output somewhere | Strategy |
| `FilterStrategy` | Decide acceptance of record | Strategy |
| `BufferedSink` | Accumulate then flush batch | State/Strategy |
| `Metrics` | Counts per level + dropped | Aggregator |
| `Events` | Lifecycle notifications | Observer |

---
## 🔄 Log Record Lifecycle
CREATED → FILTER_CHECK → (FILTERED_OUT | FORMATTED → EMITTING → EMITTED) | BUFFERED (→ FLUSHING → EMITTED) | ERROR (sink/format failure).

---
## 🧠 Key Patterns
- Singleton Logger ensures coherent global config.
- Strategy for formatter, sink, filter enables runtime swaps.
- Observer events support instrumentation & analytics.
- State for buffered sink pending vs flushed.
- Factory helper for record creation with monotonic id.

---
## ⚙ Strategies
Formatters: `SimpleFormatter`, `JsonFormatter`
Sinks: `ConsoleSink`, `MemorySink`, `BufferedConsoleSink`
Filters: `AllowAllFilter`, `LevelThresholdFilter`

---
## 📊 Metrics Tracked
- per level counts (`INFO`, `ERROR`, etc.)
- filtered_out
- emitted
- buffered_pending
- flushed_batches

---
## 🧪 Demo Scenarios
1. Basic console logging (simple formatter)
2. Level threshold filter demonstration
3. Swap to JSON + memory sink
4. Buffered sink then flush
5. Context-rich correlation & metrics summary

---
## 🗂 Files
- `START_HERE.md` – 5‑minute interviewer cheat sheet
- `75_MINUTE_GUIDE.md` – stepwise deep dive
- `INTERVIEW_COMPACT.py` – runnable compact code

Run:
```bash
python3 INTERVIEW_COMPACT.py
```

---
## 💬 Talking Points
- Why strategy separation: isolates concerns & future extensibility (e.g., async sink).
- Buffered vs immediate sinks: throughput vs latency trade-off.
- Filtering early reduces formatting cost.
- Structured (JSON) formatting improves ingestion & search.
- Metrics for dynamic reconfiguration (raise threshold under load).

---
## 🚀 Future Enhancements
- Async dispatch with queue + worker thread
- Log rotation / size-based file sink
- Sampling filter for high-volume DEBUG
- Trace/span correlation (distributed tracing IDs)
- External exporter (HTTP / gRPC)

---
## ✅ Interview Closure
Show pattern layering, lifecycle clarity, clean extension points, and scaling pathways (async, persistence, structured log ingestion).
