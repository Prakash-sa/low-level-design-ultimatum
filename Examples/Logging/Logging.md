# Logging — 75-Minute Interview Guide

## Quick Start Overview

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


## 75-Minute Guide

## 1. Problem Framing (0–5)
Design an extensible in-memory logging framework with severity levels, pluggable formatter, sink, filter, buffering, metrics & events. Focus: interview-scale clarity + real-world evolution path.

Must:
- Log with levels (DEBUG..CRITICAL)
- Filter based on level threshold
- Pluggable formatter & sink
- Buffered sink flush
- Metrics & lifecycle events

Stretch:
- Context enrichment
- Strategy swapping at runtime
- Dead-letter (not typical here; omitted)

## 2. Requirements & Constraints (5–10)
Functional:
- Accept log requests quickly (O(1) enqueue/emit)
- Reject/skip logs below threshold
- Flush buffered output on demand

Non-Functional:
- Low coupling for extension
- Observability of internal events
- Deterministic filtering order

Assumptions:
- Single-threaded; no concurrency safety implemented
- Memory capacity sufficient for buffer demo

## 3. Domain Model (10–18)
Entities:
- LogRecord(id, level, message, context, timestamp)
- Logger(singleton; holds strategies + metrics)
- FormatterStrategy(format(LogRecord)->str)
- SinkStrategy(emit(str, LogRecord))
- FilterStrategy(accept(LogRecord)->bool)
- BufferedConsoleSink(buffer, flush)

Relationships:
Logger -> (FormatterStrategy, SinkStrategy, FilterStrategy)
Logger -> Metrics aggregator
Records created via Logger helper; passed through filter → formatter → sink.

## 4. Patterns (18–26)
Singleton: One Logger instance for simplicity.
Strategy: Formatter, Sink, Filter easily replaceable.
Observer: Emit events for each lifecycle stage.
State: Buffered sink internal buffer vs flushed state.
Factory: Implicit record creation wrapper inside Logger.

## 5. Log Lifecycle (26–32)
CREATE → FILTER_CHECK → (FILTERED_OUT | FORMAT → EMIT | BUFFER) → (FLUSH → EMIT) → COMPLETE.

Invariants:
1. Filter executes before formatting.
2. Filtered records increment filtered metric, not emitted.
3. Flush moves all buffered records through formatting/emission.
4. Strategy swap does not retroactively reformat emitted records.

## 6. Strategies (32–40)
Formatter:
- SimpleFormatter: level + message
- JsonFormatter: structured line (id, level, ts, msg, context)
Sink:
- ConsoleSink: immediate print
- MemorySink: store formatted lines
- BufferedConsoleSink: accumulate, flush prints batch
Filter:
- AllowAllFilter
- LevelThresholdFilter(min_level)

## 7. Severity Hierarchy (40–44)
DEBUG(10) < INFO(20) < WARN(30) < ERROR(40) < CRITICAL(50)
Threshold filter: accept if record.level.value >= min_level.value.

## 8. Buffering (44–50)
Benefits: batch output reduces overhead.
Trade-offs: increased latency, risk of lost logs on crash.
Flush conditions: manual or size threshold (manual for simplicity).
Event `flushed` emitted with count.

## 9. Metrics (50–55)
Per level increment on accepted log.
`filtered_out` counts rejected logs.
`emitted` counts successful sink emissions.
`buffered_pending` current buffer length (for buffered sink only).
`flushed_batches` number of flush operations.

## 10. Events (55–60)
Names:
- record_created
- record_filtered
- record_formatted
- record_emitted
- record_buffered
- flushed
- strategy_swapped (formatter/filter/sink)
Payload includes id, level, message snippet, counts or buffer size.

## 11. Demo Scenarios (60–68)
1. Basic logging (simple formatter)
2. Raise threshold (DEBUG rejected, INFO accepted)
3. Swap to JSON formatter + memory sink
4. Switch to buffered sink; log several; flush
5. Log with context; print metrics summary

## 12. Trade-offs (68–72)
Early filtering reduces cost vs filtering after formatting.
Buffering increases throughput but adds latency risk.
JSON vs plain: richer semantics vs performance overhead.
Singleton vs DI: simplicity vs test isolation.

## 13. Extensions (72–75)
- Async queue with worker thread (non-blocking)
- Structured correlation IDs (trace/span)
- Rotating file sink with size/time triggers
- Sampling strategy (drop repetitive DEBUG bursts)
- External exporter sink (HTTP/gRPC) with retry

## Summary
A modular logging core: lifecycle clarity + strategy-based extensibility + observable events + actionable metrics. Easily evolves toward production-ready features (async, batching, structured ingestion).


## Detailed Design Reference

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


## Compact Code

```python
"""Compact Logging System demonstration
Run: python3 INTERVIEW_COMPACT.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Callable, Optional
import time
import itertools
import json

# ---------------- Levels ----------------
class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50

# ---------------- Record ----------------
_record_id_counter = itertools.count(1)

def next_record_id() -> int:
    return next(_record_id_counter)

@dataclass(frozen=True)
class LogRecord:
    level: LogLevel
    message: str
    context: Dict[str, Any]
    id: int = field(default_factory=next_record_id)
    timestamp: float = field(default_factory=time.time)

# ---------------- Strategies ----------------
class FormatterStrategy:
    def format(self, record: LogRecord) -> str:
        raise NotImplementedError
    def name(self) -> str:
        return self.__class__.__name__

class SimpleFormatter(FormatterStrategy):
    def format(self, record: LogRecord) -> str:
        ts = time.strftime('%H:%M:%S', time.localtime(record.timestamp))
        return f"[{ts}] {record.level.name}: {record.message}"

class JsonFormatter(FormatterStrategy):
    def format(self, record: LogRecord) -> str:
        return json.dumps({
            "id": record.id,
            "ts": record.timestamp,
            "level": record.level.name,
            "message": record.message,
            "context": record.context
        })

class SinkStrategy:
    def emit(self, formatted: str, record: LogRecord) -> None:
        raise NotImplementedError
    def name(self) -> str:
        return self.__class__.__name__
    def buffered_length(self) -> int:
        return 0
    def flush(self) -> int:
        return 0

class ConsoleSink(SinkStrategy):
    def emit(self, formatted: str, record: LogRecord) -> None:
        print(formatted)

class MemorySink(SinkStrategy):
    def __init__(self) -> None:
        self.lines: List[str] = []
    def emit(self, formatted: str, record: LogRecord) -> None:
        self.lines.append(formatted)

class BufferedConsoleSink(SinkStrategy):
    def __init__(self, max_buffer: int = 5) -> None:
        self.buffer: List[str] = []
        self.max_buffer = max_buffer
    def emit(self, formatted: str, record: LogRecord) -> None:
        self.buffer.append(formatted)
        if len(self.buffer) >= self.max_buffer:
            self.flush()
    def buffered_length(self) -> int:
        return len(self.buffer)
    def flush(self) -> int:
        count = len(self.buffer)
        for line in self.buffer:
            print(line)
        self.buffer.clear()
        return count

class FilterStrategy:
    def accept(self, record: LogRecord) -> bool:
        raise NotImplementedError
    def name(self) -> str:
        return self.__class__.__name__

class AllowAllFilter(FilterStrategy):
    def accept(self, record: LogRecord) -> bool:
        return True

class LevelThresholdFilter(FilterStrategy):
    def __init__(self, min_level: LogLevel) -> None:
        self.min_level = min_level
    def accept(self, record: LogRecord) -> bool:
        return record.level.value >= self.min_level.value
    def name(self) -> str:
        return f"LevelThreshold({self.min_level.name})"

# ---------------- Logger (Singleton) ----------------
class Logger:
    _instance: Optional[Logger] = None
    def __init__(self) -> None:
        self.formatter: FormatterStrategy = SimpleFormatter()
        self.sink: SinkStrategy = ConsoleSink()
        self.filter: FilterStrategy = AllowAllFilter()
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.metrics: Dict[str, int] = {lvl.name: 0 for lvl in LogLevel}
        self.metrics.update({"filtered_out": 0, "emitted": 0, "flushed_batches": 0, "buffered_pending": 0})
    @classmethod
    def instance(cls) -> Logger:
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    def register_listener(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(fn)
    def _emit_event(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    def set_formatter(self, formatter: FormatterStrategy) -> None:
        old = self.formatter.name()
        self.formatter = formatter
        self._emit_event("strategy_swapped", {"type": "formatter", "old": old, "new": formatter.name()})
    def set_sink(self, sink: SinkStrategy) -> None:
        old = self.sink.name()
        self.sink = sink
        self._emit_event("strategy_swapped", {"type": "sink", "old": old, "new": sink.name()})
    def set_filter(self, flt: FilterStrategy) -> None:
        old = self.filter.name()
        self.filter = flt
        self._emit_event("strategy_swapped", {"type": "filter", "old": old, "new": flt.name()})
    def log(self, level: LogLevel, message: str, **context: Any) -> None:
        record = LogRecord(level=level, message=message, context=context)
        self._emit_event("record_created", {"id": record.id, "level": level.name, "msg": message[:40]})
        if not self.filter.accept(record):
            self.metrics["filtered_out"] += 1
            self._emit_event("record_filtered", {"id": record.id, "reason": self.filter.name()})
            return
        self.metrics[level.name] += 1
        formatted = self.formatter.format(record)
        self._emit_event("record_formatted", {"id": record.id, "formatter": self.formatter.name()})
        if isinstance(self.sink, BufferedConsoleSink):
            before = self.sink.buffered_length()
            self.sink.emit(formatted, record)
            after = self.sink.buffered_length()
            self.metrics["buffered_pending"] = after
            self._emit_event("record_buffered", {"id": record.id, "buffer_size": after})
            if after == 0 and before >= self.sink.max_buffer:  # flush happened
                self.metrics["flushed_batches"] += 1
                self._emit_event("flushed", {"count": before})
        else:
            self.sink.emit(formatted, record)
            self.metrics["emitted"] += 1
            self._emit_event("record_emitted", {"id": record.id, "sink": self.sink.name()})
    def flush(self) -> None:
        if hasattr(self.sink, "flush"):
            flushed = self.sink.flush()
            if flushed:
                self.metrics["flushed_batches"] += 1
                self.metrics["emitted"] += flushed
                self.metrics["buffered_pending"] = 0
                self._emit_event("flushed", {"count": flushed})
    def summary(self) -> Dict[str, int]:
        # If buffered sink still has pending items, show buffered_pending
        if isinstance(self.sink, BufferedConsoleSink):
            self.metrics["buffered_pending"] = self.sink.buffered_length()
        return dict(self.metrics)

# ---------------- Helper API ----------------
log = Logger.instance().log

# ---------------- Listener ----------------

def event_listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------- Demo Scenarios ----------------

def print_header(title: str) -> None:
    print(f"\n=== {title} ===")

def demo_1_basic_console() -> None:
    print_header("Demo 1: Basic Console Logging")
    logger = Logger.instance()
    logger.register_listener(event_listener)
    log(LogLevel.INFO, "System start", component="init")
    log(LogLevel.DEBUG, "Debug detail", component="init")


def demo_2_threshold_filter() -> None:
    print_header("Demo 2: Threshold Filter")
    logger = Logger.instance()
    logger.set_filter(LevelThresholdFilter(LogLevel.INFO))
    log(LogLevel.DEBUG, "This should be filtered", component="filter_test")
    log(LogLevel.INFO, "This is accepted", component="filter_test")


def demo_3_json_memory_sink() -> None:
    print_header("Demo 3: JSON Formatter + Memory Sink")
    logger = Logger.instance()
    logger.set_formatter(JsonFormatter())
    memory_sink = MemorySink()
    logger.set_sink(memory_sink)
    log(LogLevel.WARN, "Cache nearing capacity", usage=82)
    log(LogLevel.ERROR, "Cache overflow", usage=101)
    print("Memory sink stored lines:")
    for line in memory_sink.lines:
        print("  ", line)


def demo_4_buffered_sink_flush() -> None:
    print_header("Demo 4: Buffered Sink & Flush")
    logger = Logger.instance()
    logger.set_sink(BufferedConsoleSink(max_buffer=3))
    logger.set_formatter(SimpleFormatter())
    for i in range(5):
        log(LogLevel.INFO, f"Buffered message {i}")
    # Remaining buffered messages flush manually
    Logger.instance().flush()


def demo_5_context_and_summary() -> None:
    print_header("Demo 5: Context + Metrics Summary")
    logger = Logger.instance()
    logger.set_sink(ConsoleSink())
    logger.set_filter(AllowAllFilter())
    logger.set_formatter(SimpleFormatter())
    log(LogLevel.CRITICAL, "Service crash", trace_id="abc123", user_id=42)
    summary = logger.summary()
    print("Metrics Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

# ---------------- Main ----------------
if __name__ == "__main__":
    demo_1_basic_console()
    demo_2_threshold_filter()
    demo_3_json_memory_sink()
    demo_4_buffered_sink_flush()
    demo_5_context_and_summary()

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
