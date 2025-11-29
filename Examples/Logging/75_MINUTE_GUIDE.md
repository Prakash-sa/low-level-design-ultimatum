# 🪵 Logging System – 75 Minute Deep Dive

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
