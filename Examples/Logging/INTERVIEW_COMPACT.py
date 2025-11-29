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
