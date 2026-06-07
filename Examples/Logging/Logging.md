# Logging System — Complete Design Guide

> Centralized, thread-safe log capture, formatting, routing, and async dispatch across multiple output destinations with configurable severity filtering.

**Scale**: Millions of log events/day, 10+ concurrent services, 99.9% uptime  
**Duration**: 75-minute interview guide  
**Focus**: Async non-blocking writes, configurable appenders, log-level filtering, thread safety, log rotation

---

## Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Step 01: The Setup — Clarify Requirements](#step-01-the-setup--clarify-requirements)
3. [Step 02: Structure — Define Entities](#step-02-structure--define-entities)
4. [Step 03: Interface — APIs & Entry Points](#step-03-interface--apis--entry-points)
5. [Step 04: Architecture — Relationships & Diagram](#step-04-architecture--relationships--diagram)
6. [Step 05: Optimization — Design Patterns](#step-05-optimization--design-patterns)
7. [Step 06: Implementation — Code & Concurrency](#step-06-implementation--code--concurrency)
8. [Demo Scenarios](#demo-scenarios)
9. [Interview Q&A](#interview-qa)
10. [Scaling Q&A](#scaling-qa)
11. [Success Checklist](#success-checklist)

---

## Quick Start

**5-Minute Overview for Last-Minute Prep**

### What Problem Are We Solving?
Applications produce log events continuously. Synchronous writes block the calling thread, single-destination logging is inflexible, and unchecked log files overflow disks. A good logging system queues events asynchronously, routes them to multiple sinks (console, file, cloud) through a pipeline of handlers, formats output with pluggable formatters, rotates files on size or time thresholds, and filters noise via log levels — all without measurable overhead on application threads.

### Core Flow
```
App thread        Logger          Async Queue        Worker thread        Appenders
    │                │                 │                   │                  │
    │── log(INFO) ──>│                 │                   │                  │
    │                │── enqueue() ───>│                   │                  │
    │<── returns ────│                 │── dequeue ────────>│                  │
    │  (non-blocking)│                 │                   │── format ────────>│
    │                │                 │                   │                  │── write to console
    │                │                 │                   │                  │── write to file
    │                │                 │                   │                  │── send to cloud
```

---

## Step 01: The Setup — Clarify Requirements

> **Interview Tip**: Never code immediately. Ask clarifying questions first. Define scope, actors, and constraints.

### Questions to Ask (30 seconds each)

1. **Single process or distributed?** → "Distributed — multiple services send logs to shared infrastructure"
2. **How many log destinations?** → "Console, file, and cloud (Elasticsearch/CloudWatch)"
3. **Synchronous or async writes?** → "Async — must not block calling thread"
4. **Log rotation needed?** → "Yes — size-based and time-based (daily)"
5. **Structured logging?** → "Yes — key-value pairs for searchability"

### Actors (Who uses the system?)

| Actor | Role | Example Actions |
|-------|------|-----------------|
| **Application / Service** | Emits log events | Call `logger.info(...)`, `logger.error(...)` |
| **Ops / DevOps** | Configures & monitors logs | Set log levels, add appenders, query logs |
| **System** | Background coordinator | Dequeue events, dispatch to appenders, rotate files |

### Functional Requirements (What does the system do?)

✅ **Log Levels**
  - Support DEBUG, INFO, WARN, ERROR, FATAL severity levels
  - Filter messages below configured minimum level

✅ **Multiple Appenders**
  - Write logs to console, file, and cloud destinations simultaneously
  - Each appender independently configurable (level, formatter)

✅ **Async Writes**
  - Application thread only enqueues; background worker dispatches
  - Non-blocking: app performance unaffected by slow I/O

✅ **Structured Logging**
  - Accept key-value context pairs: `logger.info("Order placed", order_id="123")`
  - Format as JSON or plain text depending on appender formatter

✅ **Log Rotation**
  - Rotate file when it exceeds a maximum size (e.g., 10 MB)
  - Keep configurable number of backup files

✅ **Configurable Formatters**
  - Plain text formatter: `[timestamp] LEVEL message key=value`
  - JSON formatter: `{"timestamp": "...", "level": "...", "message": "..."}`

✅ **Centralized Logger**
  - Single named-logger registry; same logger name → same instance
  - Root logger as fallback for unconfigured names

### Non-Functional Requirements (How does it perform?)

✅ **Concurrency**: Thread-safe logging from 100s of threads simultaneously  
✅ **Throughput**: 100K+ log events/second without dropping messages  
✅ **Latency**: <1 ms overhead per `log()` call on calling thread  
✅ **Reliability**: No log events lost on graceful shutdown  
✅ **Disk Safety**: Log rotation prevents unbounded disk usage  
✅ **Extensibility**: Add new appenders/formatters without modifying core  

### Constraints & Clarifications

| Constraint | Decision |
|-----------|----------|
| **Distributed?** | YES — discuss LogAggregator and Kafka as scaling concern |
| **Real cloud integration?** | NO — mock CloudAppender for interview |
| **Queue overflow?** | Configurable: block caller or drop oldest (default: block) |
| **Log rotation backups** | Keep last 5 rotated files |
| **Max file size** | 10 MB (configurable) |
| **Worker threads** | 1 background worker (can scale to pool) |

---

## Step 02: Structure — Define Entities

> **Interview Tip**: Extract core objects from requirements. Look for **nouns**. Write them on whiteboard immediately.

### Step 2.1: List Core Entities (Extract Nouns)

```
Logger, LogMessage, Appender, Formatter, LogLevel, LogRecord, LogManager, ...
```

### Step 2.2: Define Core Classes

#### **LogMessage** — A single log event
```
Properties:
  - level: LogLevel (DEBUG, INFO, WARN, ERROR, FATAL)
  - message: str (human-readable description)
  - logger_name: str (which logger produced this)
  - timestamp: datetime (when the event occurred)
  - thread_id: int (which thread emitted it)
  - context: Dict[str, Any] (key-value structured pairs)

Behaviors:
  - (data object — no behaviors beyond construction)
```

#### **Formatter** — Converts a LogMessage to a string
```
Properties:
  - (abstract — subclasses hold format-specific config)

Behaviors:
  - format(log_message: LogMessage) -> str
    (PlainTextFormatter, JsonFormatter both implement this)
```

#### **Appender** — A single log output destination
```
Properties:
  - name: str (e.g., "console", "app.log")
  - formatter: Formatter (how to render the message)
  - min_level: LogLevel (this appender's own level filter)

Behaviors:
  - append(log_message: LogMessage): write the formatted string
  - set_formatter(formatter): swap formatter at runtime
```

#### **Logger** — Captures log events from application code
```
Properties:
  - name: str (e.g., "root", "myapp.db")
  - level: LogLevel (minimum level this logger processes)
  - appenders: List[Appender]
  - async_queue: Queue (buffer for worker thread)
  - _worker: Thread (background dispatcher)

Behaviors:
  - debug/info/warn/error/fatal(message, **context): enqueue LogMessage
  - log(level, message, **context): generic entry point
  - add_appender(appender): register a new destination
  - remove_appender(name): deregister a destination
  - set_level(level): change minimum level at runtime
  - shutdown(): drain queue and stop worker cleanly
```

#### **LogManager** — Singleton registry of named loggers
```
Properties:
  - _loggers: Dict[str, Logger]
  - _lock: threading.RLock

Behaviors:
  - get_logger(name): retrieve or create named Logger
  - configure(name, level, appenders): batch-configure a logger
```

#### **RotatingFileAppender** — File appender with rotation
```
Properties:
  - file_path: str
  - max_bytes: int (default 10 MB)
  - backup_count: int (default 5)
  - current_size: int

Behaviors:
  - append(log_message): check size, rotate if needed, write
  - _rotate(): rename log → log.1, log.1 → log.2, ... create fresh log
```

### Step 2.3: Define Enumerations (State & Type)

```python
from enum import IntEnum

class LogLevel(IntEnum):
    DEBUG = 10    # Verbose developer detail
    INFO  = 20    # Normal operational events
    WARN  = 30    # Unexpected but recoverable situations
    ERROR = 40    # Failures requiring attention
    FATAL = 50    # Unrecoverable — system cannot continue
```

### Step 2.4: Why These Entities?

| Entity | Why | Cost of Missing |
|--------|-----|-----------------|
| **LogMessage** | Structured event carrying all metadata | Can't filter, format, or route intelligently |
| **Logger** | Single entry point per named component | Every caller re-implements routing and filtering |
| **Appender** | Pluggable output destination | Hard-coded destinations, can't add new sinks |
| **Formatter** | Decouples rendering from routing | Each appender must know every output format |
| **LogManager** | Singleton registry of loggers | Duplicate loggers, divergent configurations |
| **RotatingFileAppender** | Prevents disk overflow | Log files grow unboundedly until disk full |

---

## Step 03: Interface — APIs & Entry Points

> **Interview Tip**: Define the contract (inputs, outputs, exceptions) BEFORE implementation. Focus on "what" not "how".

### Step 3.1: Public API Contracts

#### **1. Get or Create a Logger** ⭐ CRITICAL
```python
def get_logger(name: str = "root") -> Logger:
    """
    Retrieve the named Logger from the global registry (LogManager).
    Creates a new Logger with default configuration if it doesn't exist.

    Returns: Logger instance (same instance for same name — always).
    Raises: nothing (always returns a usable Logger).

    Thread Safety: THREAD-SAFE (guarded by LogManager RLock)
    """
    pass
```

#### **2. Log an Event** ⭐ CRITICAL
```python
def log(self, level: LogLevel, message: str, **context) -> None:
    """
    Enqueue a log event for async dispatch.

    Precondition: level >= self.level (otherwise silently dropped)
    Postcondition: LogMessage placed on async queue; returns immediately.

    Args:
      level   — severity of the event
      message — human-readable description
      **context — arbitrary key-value structured fields

    Raises: nothing (logging must never crash the caller)

    Concurrency: THREAD-SAFE — queue.Queue is thread-safe
    Response Time: <1 ms (just enqueues, does NOT block on I/O)
    """
    pass

# Convenience shorthands (all delegate to log()):
def debug(self, message: str, **context) -> None: ...
def info(self, message: str, **context) -> None: ...
def warn(self, message: str, **context) -> None: ...
def error(self, message: str, **context) -> None: ...
def fatal(self, message: str, **context) -> None: ...
```

#### **3. Add / Remove Appender**
```python
def add_appender(self, appender: Appender) -> None:
    """
    Register an output destination for this logger.
    Appender will receive all messages at or above its own min_level.

    Thread Safety: THREAD-SAFE (guarded by logger RLock)
    """
    pass

def remove_appender(self, name: str) -> bool:
    """
    Deregister the appender with the given name.
    Returns True if found and removed, False if not found.
    """
    pass
```

#### **4. Set Log Level**
```python
def set_level(self, level: LogLevel) -> None:
    """
    Change the minimum severity level at runtime.
    Messages below the new level are silently dropped BEFORE enqueuing.

    Example: set_level(LogLevel.WARN) suppresses all DEBUG/INFO traffic.
    """
    pass
```

#### **5. Graceful Shutdown**
```python
def shutdown(self) -> None:
    """
    Signal background worker to stop after draining the queue.

    Postcondition: all enqueued messages written before method returns.
    Timeout: up to 30 seconds; forcibly stops after timeout.

    Important: call this at application exit to prevent message loss.
    """
    pass
```

### Step 3.2: Exception / Failure Model

The logging system is designed to never propagate exceptions to callers:

```python
class LoggingException(Exception):
    """Base — only used internally; never reaches application code."""
    pass

class AppenderWriteError(LoggingException):
    """Raised inside worker thread; caught, logged to stderr, worker continues."""
    pass

class FormatterError(LoggingException):
    """Raised if formatter fails; fallback to str(log_message)."""
    pass
```

**Design principle**: if an appender fails (disk full, network down), the worker logs the error to stderr and continues processing — application code is never interrupted.

### Step 3.3: API Usage Example

```python
# 1. Get logger
logger = LogManager.get_instance().get_logger("myapp.orders")

# 2. Configure — add console + file output
logger.add_appender(ConsoleAppender(PlainTextFormatter()))
logger.add_appender(RotatingFileAppender("app.log", JsonFormatter(), max_bytes=10*1024*1024))
logger.set_level(LogLevel.INFO)

# 3. Log events (non-blocking — returns immediately)
logger.info("Application started", version="2.1.0", env="production")
logger.warn("High memory usage", usage_pct=85)
logger.error("Database connection failed", host="db.internal", retry=3)

# 4. Structured log → JSON formatter output:
# {"timestamp": "2025-01-15T12:30:45", "level": "ERROR",
#  "logger": "myapp.orders", "message": "Database connection failed",
#  "host": "db.internal", "retry": 3}

# 5. Graceful shutdown at application exit
logger.shutdown()
```

---

## Step 04: Architecture — Relationships & Diagram

> **Interview Tip**: Use composition, aggregation, and inheritance. Prefer composition over inheritance. Check cardinality (1:1, 1:N).

### Step 4.1: Relationship Types

```
LogManager HAS-A loggers (1:N Composition)
  └─ LogManager owns lifecycle of all Logger instances

Logger HAS-A appenders (1:N Composition)
  └─ Logger owns and manages its appender list

Logger HAS-A async_queue (1:1 Composition)
  └─ Each Logger has its own queue + worker thread

Appender HAS-A formatter (1:1 Composition)
  └─ Appender owns its formatter (Strategy pattern)

LogMessage IS-A value object (no ownership)
  └─ Created by Logger, consumed by Appenders

RotatingFileAppender IS-A Appender (Inheritance)
  └─ Extends FileAppender with rotation behavior

ConsoleAppender IS-A Appender (Inheritance)
  └─ Writes formatted output to sys.stdout

CloudAppender IS-A Appender (Inheritance)
  └─ Sends formatted output to remote endpoint
```

### Step 4.2: Complete UML Class Diagram

```
┌──────────────────────────────────┐
│     LogManager (Singleton)       │
├──────────────────────────────────┤
│ - _instance: LogManager          │
│ - _loggers: Dict[str, Logger]    │
│ - _lock: threading.RLock         │
├──────────────────────────────────┤
│ + get_instance(): LogManager     │
│ + get_logger(name): Logger       │
│ + configure(name, level, appnds) │
└──────────────┬───────────────────┘
       manages 1:N
               ▼
┌─────────────────────────────────────┐
│           Logger                    │
├─────────────────────────────────────┤
│ - name: str                         │
│ - level: LogLevel                   │
│ - appenders: List[Appender]         │
│ - _queue: queue.Queue               │
│ - _worker: Thread (daemon)          │
│ - _lock: threading.RLock            │
│ - _running: bool                    │
├─────────────────────────────────────┤
│ + log(level, message, **ctx): void  │
│ + debug/info/warn/error/fatal(...)  │
│ + add_appender(appender): void      │
│ + remove_appender(name): bool       │
│ + set_level(level): void            │
│ + shutdown(): void                  │
│ - _worker_loop(): void              │
└──────────────┬──────────────────────┘
       notifies 1:N
               ▼
┌─────────────────────────────────────┐
│        Appender (Abstract)          │
├─────────────────────────────────────┤
│ - name: str                         │
│ - formatter: Formatter              │
│ - min_level: LogLevel               │
├─────────────────────────────────────┤
│ + append(log_message): void  [ABC]  │
│ + set_formatter(fmt): void          │
└──┬──────────────────────────────────┘
   │ implemented by
   ├─→ ConsoleAppender   (writes to stdout)
   ├─→ FileAppender      (writes to file)
   ├─→ RotatingFileAppender (file + rotation)
   └─→ CloudAppender     (mock remote send)

Each Appender HAS-A:
┌──────────────────────────────────┐
│      Formatter (Abstract)        │
├──────────────────────────────────┤
│ + format(log_message): str [ABC] │
└──┬───────────────────────────────┘
   │ implemented by
   ├─→ PlainTextFormatter  → "[timestamp] LEVEL name — message key=val"
   └─→ JsonFormatter       → '{"timestamp":..., "level":..., ...}'

LogMessage (Value Object — passed through the pipeline):
┌──────────────────────────────────┐
│         LogMessage               │
├──────────────────────────────────┤
│ - level: LogLevel                │
│ - message: str                   │
│ - logger_name: str               │
│ - timestamp: datetime            │
│ - thread_id: int                 │
│ - context: Dict[str, Any]        │
└──────────────────────────────────┘

LogLevel (IntEnum — enables numeric comparison):
DEBUG(10) < INFO(20) < WARN(30) < ERROR(40) < FATAL(50)
```

### Step 4.3: Cardinality Summary

| Relationship | Cardinality | Type | Reason |
|-------------|------------|------|--------|
| LogManager → Loggers | 1:N | Composition | Registry owns all named loggers |
| Logger → Appenders | 1:N | Composition | Logger routes to multiple destinations |
| Logger → Queue | 1:1 | Composition | Each logger has isolated async buffer |
| Appender → Formatter | 1:1 | Composition | Each appender has one active formatter |
| Appender → LogMessage | N:1 | Association | Many appenders consume same message |
| RotatingFileAppender → FileAppender | 1:1 | Inheritance | Extends with rotation capability |

---

## Step 05: Optimization — Design Patterns

> **Interview Tip**: Don't force patterns. Only solve specific problems.

### Pattern 1: **Singleton** (For LogManager)

**Problem**: Different modules asking for the same named logger must receive the same configured instance — not separate unconfigured copies.

**Solution**: LogManager is a Singleton that owns the logger registry.

```python
class LogManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._loggers = {}
            self._initialized = True

    @classmethod
    def get_instance(cls) -> 'LogManager':
        return cls()
```

**Benefit**: ✅ One registry, consistent logger state, no duplicate workers  
**Trade-off**: ⚠️ Global state; reset between unit tests required

---

### Pattern 2: **Strategy** (For Formatters)

**Problem**: Console output wants human-readable text; file/cloud output wants machine-parseable JSON. The formatting algorithm must be swappable without touching Appender logic.

**Solution**: `Formatter` abstract base class with pluggable implementations.

```python
class Formatter(ABC):
    @abstractmethod
    def format(self, msg: LogMessage) -> str:
        pass

class PlainTextFormatter(Formatter):
    def format(self, msg: LogMessage) -> str:
        ts = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ctx = " ".join(f"{k}={v}" for k, v in msg.context.items())
        return f"[{ts}] {msg.level.name:<5} {msg.logger_name} — {msg.message} {ctx}".strip()

class JsonFormatter(Formatter):
    def format(self, msg: LogMessage) -> str:
        import json
        record = {
            "timestamp": msg.timestamp.isoformat(),
            "level": msg.level.name,
            "logger": msg.logger_name,
            "message": msg.message,
            **msg.context
        }
        return json.dumps(record)

# Usage: swap formatter at runtime
file_appender.set_formatter(JsonFormatter())
```

**Benefit**: ✅ Open/Closed — add new formats without touching appenders  
**Trade-off**: ⚠️ Extra abstraction layer for simple cases

---

### Pattern 3: **Observer / Async Appender** (For Dispatching)

**Problem**: If appenders write synchronously in the calling thread, a slow network or full disk blocks the application.

**Solution**: Logger queues `LogMessage` objects; a background worker thread drains the queue and notifies each appender — the Observer role.

```python
class Logger:
    def log(self, level: LogLevel, message: str, **context):
        if level >= self.level:
            msg = LogMessage(level, message, self.name, **context)
            self._queue.put(msg)          # Non-blocking enqueue

    def _worker_loop(self):
        while self._running or not self._queue.empty():
            try:
                msg = self._queue.get(timeout=0.1)
                with self._lock:
                    appenders_snapshot = list(self._appenders)
                for appender in appenders_snapshot:
                    if msg.level >= appender.min_level:
                        appender.append(msg)  # Each appender is an "Observer"
            except queue.Empty:
                continue
```

**Benefit**: ✅ Calling thread never blocks on I/O; slow appenders don't cascade  
**Trade-off**: ⚠️ Messages are delivered slightly delayed; must flush on shutdown

---

### Pattern 4: **Chain of Responsibility** (For Level Filtering)

**Problem**: Each layer (logger, appender) needs to independently filter messages by severity without coupling decisions together.

**Solution**: Each node in the chain independently checks the level and either processes or drops the message.

```python
# Logger-level filter (outermost gate)
def log(self, level: LogLevel, message: str, **context):
    if level < self.level:      # Logger gate: drop below logger's minimum
        return
    self._queue.put(LogMessage(level, message, self.name, **context))

# Appender-level filter (inner gate — each appender decides independently)
def append(self, msg: LogMessage):
    if msg.level < self.min_level:   # Appender gate
        return
    formatted = self.formatter.format(msg)
    self._write(formatted)

# Example: Logger at DEBUG, FileAppender at WARN
# → DEBUG/INFO events hit Logger, enqueue, then FileAppender silently drops them
# → WARN/ERROR/FATAL events pass both gates and are written
```

**Benefit**: ✅ Flexible multi-level filtering; file only captures errors, console shows all  
**Trade-off**: ⚠️ Events still enqueued if logger level passes but appender drops; minor waste

---

### Design Patterns Summary Table

| Pattern | Problem Solved | Where Applied | Benefit |
|---------|---|---|---|
| **Singleton** | Single consistent logger registry | LogManager | No duplicate loggers or workers |
| **Strategy** | Pluggable output format | Formatter (Plain/JSON) | Add formats without touching appenders |
| **Observer / Async** | Non-blocking I/O dispatch | Logger → Appenders via queue | Application thread never waits on disk/network |
| **Chain of Responsibility** | Independent level filtering at each layer | Logger + each Appender | Fine-grained per-destination filtering |

---

## Step 06: Implementation — Code & Concurrency

> **Interview Tip**: Write thread-safe, defensive code. Mention "Thread Safety" even if not asked.

### Complete Thread-Safe Implementation

```python
"""
Logging System — Interview Implementation
Demonstrates:
1. Singleton LogManager + named Logger registry
2. Async background worker (non-blocking log calls)
3. Strategy pattern — PlainTextFormatter vs JsonFormatter
4. Chain of Responsibility — per-logger and per-appender level filters
5. RotatingFileAppender — automatic size-based rotation
6. Graceful shutdown (queue drain)
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMERATIONS
# ============================================================================

class LogLevel(IntEnum):
    DEBUG = 10
    INFO  = 20
    WARN  = 30
    ERROR = 40
    FATAL = 50


# ============================================================================
# VALUE OBJECT
# ============================================================================

class LogMessage:
    """Immutable snapshot of a single log event."""

    def __init__(self, level: LogLevel, message: str, logger_name: str,
                 **context: Any):
        self.level = level
        self.message = message
        self.logger_name = logger_name
        self.timestamp = datetime.now()
        self.thread_id = threading.get_ident()
        self.context: Dict[str, Any] = context

    def __repr__(self) -> str:
        return (f"LogMessage({self.level.name}, {self.logger_name!r},"
                f" {self.message!r})")


# ============================================================================
# FORMATTERS  (Strategy pattern)
# ============================================================================

class Formatter(ABC):
    @abstractmethod
    def format(self, msg: LogMessage) -> str:
        pass


class PlainTextFormatter(Formatter):
    """Human-readable single-line format."""

    def format(self, msg: LogMessage) -> str:
        ts = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ctx_str = ""
        if msg.context:
            ctx_str = "  " + " ".join(f"{k}={v}" for k, v in msg.context.items())
        return f"[{ts}] {msg.level.name:<5} [{msg.logger_name}] {msg.message}{ctx_str}"


class JsonFormatter(Formatter):
    """Machine-parseable JSON format for structured log indexing."""

    def format(self, msg: LogMessage) -> str:
        record: Dict[str, Any] = {
            "timestamp": msg.timestamp.isoformat(),
            "level": msg.level.name,
            "logger": msg.logger_name,
            "thread": msg.thread_id,
            "message": msg.message,
        }
        record.update(msg.context)
        return json.dumps(record)


# ============================================================================
# APPENDERS
# ============================================================================

class Appender(ABC):
    """Abstract base: a single log output destination."""

    def __init__(self, name: str, formatter: Formatter,
                 min_level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self.formatter = formatter
        self.min_level = min_level

    def set_formatter(self, formatter: Formatter) -> None:
        self.formatter = formatter

    def append(self, msg: LogMessage) -> None:
        """Filter by min_level then delegate to _write."""
        if msg.level < self.min_level:
            return
        try:
            formatted = self.formatter.format(msg)
            self._write(formatted)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"[Appender:{self.name}] write error: {exc}\n")

    @abstractmethod
    def _write(self, text: str) -> None:
        pass


class ConsoleAppender(Appender):
    """Writes to stdout."""

    def __init__(self, formatter: Optional[Formatter] = None,
                 min_level: LogLevel = LogLevel.DEBUG):
        super().__init__("console", formatter or PlainTextFormatter(), min_level)

    def _write(self, text: str) -> None:
        print(text)


class FileAppender(Appender):
    """Writes to a plain file (no rotation)."""

    def __init__(self, file_path: str, formatter: Optional[Formatter] = None,
                 min_level: LogLevel = LogLevel.DEBUG):
        super().__init__(file_path, formatter or PlainTextFormatter(), min_level)
        self.file_path = file_path

    def _write(self, text: str) -> None:
        with open(self.file_path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


class RotatingFileAppender(Appender):
    """File appender that rotates when the file exceeds max_bytes."""

    def __init__(self, file_path: str, formatter: Optional[Formatter] = None,
                 min_level: LogLevel = LogLevel.DEBUG,
                 max_bytes: int = 10 * 1024 * 1024,
                 backup_count: int = 5):
        super().__init__(file_path, formatter or PlainTextFormatter(), min_level)
        self.file_path = file_path
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._file_lock = threading.Lock()

    def _rotate(self) -> None:
        """Rename log.N → log.N+1 and create a fresh log file."""
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.file_path}.{i}"
            dst = f"{self.file_path}.{i + 1}"
            if os.path.exists(src):
                os.rename(src, dst)
        if os.path.exists(self.file_path):
            os.rename(self.file_path, f"{self.file_path}.1")

    def _write(self, text: str) -> None:
        with self._file_lock:
            if os.path.exists(self.file_path):
                current_size = os.path.getsize(self.file_path)
                if current_size >= self.max_bytes:
                    self._rotate()
            with open(self.file_path, "a", encoding="utf-8") as fh:
                fh.write(text + "\n")


class CloudAppender(Appender):
    """Mock cloud appender (Elasticsearch / CloudWatch)."""

    def __init__(self, endpoint: str = "https://mock-cloud.example.com",
                 formatter: Optional[Formatter] = None,
                 min_level: LogLevel = LogLevel.ERROR):
        super().__init__("cloud", formatter or JsonFormatter(), min_level)
        self.endpoint = endpoint
        self._sent: List[str] = []

    def _write(self, text: str) -> None:
        # In production: HTTP POST to endpoint
        self._sent.append(text)
        print(f"  [CLOUD -> {self.endpoint}] {text[:80]}...")


# ============================================================================
# LOGGER
# ============================================================================

_SENTINEL = object()   # Signals worker to stop


class Logger:
    """
    Named logger — enqueues LogMessage objects for async dispatch.
    One background worker thread drains the queue and calls each Appender.
    """

    def __init__(self, name: str, level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self._level = level
        self._appenders: List[Appender] = []
        self._lock = threading.RLock()         # RLock: worker holds it while notifying
        self._queue: queue.Queue = queue.Queue()
        self._running = True
        self._worker = threading.Thread(
            target=self._worker_loop, name=f"log-worker-{name}", daemon=True
        )
        self._worker.start()

    # ---- public API ----

    @property
    def level(self) -> LogLevel:
        return self._level

    def set_level(self, level: LogLevel) -> None:
        with self._lock:
            self._level = level

    def add_appender(self, appender: Appender) -> None:
        with self._lock:
            self._appenders.append(appender)

    def remove_appender(self, name: str) -> bool:
        with self._lock:
            before = len(self._appenders)
            self._appenders = [a for a in self._appenders if a.name != name]
            return len(self._appenders) < before

    def log(self, level: LogLevel, message: str, **context: Any) -> None:
        """Enqueue a message for async dispatch (non-blocking)."""
        if level < self._level:
            return
        msg = LogMessage(level, message, self.name, **context)
        self._queue.put(msg)

    def debug(self, message: str, **ctx: Any) -> None:
        self.log(LogLevel.DEBUG, message, **ctx)

    def info(self, message: str, **ctx: Any) -> None:
        self.log(LogLevel.INFO, message, **ctx)

    def warn(self, message: str, **ctx: Any) -> None:
        self.log(LogLevel.WARN, message, **ctx)

    def error(self, message: str, **ctx: Any) -> None:
        self.log(LogLevel.ERROR, message, **ctx)

    def fatal(self, message: str, **ctx: Any) -> None:
        self.log(LogLevel.FATAL, message, **ctx)

    def shutdown(self, timeout: float = 5.0) -> None:
        """Drain the queue then stop the worker thread."""
        self._running = False
        self._queue.put(_SENTINEL)   # Unblock worker if waiting
        self._worker.join(timeout=timeout)

    # ---- background worker ----

    def _worker_loop(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=0.05)
            except queue.Empty:
                if not self._running and self._queue.empty():
                    break
                continue

            if item is _SENTINEL:
                # Drain remaining real messages before exiting
                while not self._queue.empty():
                    try:
                        remaining = self._queue.get_nowait()
                        if remaining is not _SENTINEL:
                            self._dispatch(remaining)
                    except queue.Empty:
                        break
                break

            self._dispatch(item)

    def _dispatch(self, msg: LogMessage) -> None:
        with self._lock:
            appenders = list(self._appenders)
        for appender in appenders:
            appender.append(msg)


# ============================================================================
# LOG MANAGER  (Singleton)
# ============================================================================

class LogManager:
    """
    Singleton registry for named Logger instances.
    Same name → same Logger object, always.
    """

    _instance: Optional[LogManager] = None
    _class_lock = threading.RLock()

    def __new__(cls, *args: Any, **kwargs: Any) -> LogManager:
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._loggers: Dict[str, Logger] = {}
            self._lock = threading.RLock()
            self._initialized = True

    @classmethod
    def get_instance(cls) -> LogManager:
        return cls()

    def get_logger(self, name: str = "root",
                   level: LogLevel = LogLevel.DEBUG) -> Logger:
        """Return existing logger or create a new one."""
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = Logger(name, level)
            return self._loggers[name]

    def shutdown_all(self, timeout: float = 5.0) -> None:
        """Gracefully shut down every registered logger."""
        with self._lock:
            loggers = list(self._loggers.values())
        for logger in loggers:
            logger.shutdown(timeout)


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_1_basic_logging() -> None:
    print("\n" + "=" * 70)
    print("DEMO 1: BASIC LOGGING — CONSOLE + PLAIN TEXT")
    print("=" * 70)

    manager = LogManager.get_instance()
    logger = manager.get_logger("demo1", LogLevel.DEBUG)
    logger.add_appender(ConsoleAppender(PlainTextFormatter(), LogLevel.DEBUG))

    logger.debug("Application booting", component="init")
    logger.info("Server listening", port=8080, host="0.0.0.0")
    logger.warn("High memory usage", pct=87)
    logger.error("Unhandled exception", exc="ValueError", line=42)
    logger.fatal("Out of disk space", path="/var/log")

    logger.shutdown()


def demo_2_level_filtering() -> None:
    print("\n" + "=" * 70)
    print("DEMO 2: LEVEL FILTERING — LOGGER AT WARN, CONSOLE SEES WARN+")
    print("=" * 70)

    manager = LogManager.get_instance()
    logger = manager.get_logger("demo2", LogLevel.WARN)
    logger.add_appender(ConsoleAppender(PlainTextFormatter(), LogLevel.DEBUG))

    logger.debug("This DEBUG message is silently dropped by the logger gate")
    logger.info("This INFO message is silently dropped by the logger gate")
    logger.warn("WARN passes the logger gate → printed")
    logger.error("ERROR passes the logger gate → printed")

    logger.shutdown()


def demo_3_json_formatter_and_cloud() -> None:
    print("\n" + "=" * 70)
    print("DEMO 3: JSON FORMATTER + CLOUD APPENDER (ERROR+)")
    print("=" * 70)

    manager = LogManager.get_instance()
    logger = manager.get_logger("demo3", LogLevel.DEBUG)

    console = ConsoleAppender(PlainTextFormatter(), LogLevel.DEBUG)
    cloud = CloudAppender(min_level=LogLevel.ERROR, formatter=JsonFormatter())

    logger.add_appender(console)
    logger.add_appender(cloud)

    logger.info("Request received", method="GET", path="/api/orders")
    logger.warn("Slow query detected", duration_ms=1450, table="orders")
    logger.error("Payment gateway timeout", gateway="Stripe", retry=2)

    logger.shutdown()


def demo_4_rotating_file() -> None:
    print("\n" + "=" * 70)
    print("DEMO 4: ROTATING FILE APPENDER (tiny 200-byte limit)")
    print("=" * 70)

    import tempfile, glob

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "app.log")
        manager = LogManager.get_instance()
        logger = manager.get_logger("demo4", LogLevel.DEBUG)
        # Tiny limit so rotation triggers in the demo
        rotating = RotatingFileAppender(
            log_path,
            PlainTextFormatter(),
            LogLevel.DEBUG,
            max_bytes=200,
            backup_count=3,
        )
        logger.add_appender(rotating)

        for i in range(10):
            logger.info(f"Log line {i:02d}", iteration=i, value=i * 100)

        logger.shutdown()

        files = sorted(glob.glob(log_path + "*"))
        print(f"  Files created after rotation: {[os.path.basename(f) for f in files]}")
        print(f"  Rotation working: {len(files) > 1}")


def demo_5_multithreaded() -> None:
    print("\n" + "=" * 70)
    print("DEMO 5: MULTI-THREADED — 5 THREADS LOGGING CONCURRENTLY")
    print("=" * 70)

    manager = LogManager.get_instance()
    logger = manager.get_logger("demo5", LogLevel.INFO)
    logger.add_appender(ConsoleAppender(PlainTextFormatter(), LogLevel.INFO))

    results = []
    lock = threading.Lock()

    def worker(thread_id: int) -> None:
        for i in range(3):
            logger.info(f"Thread message {i}", thread=thread_id, iteration=i)
        with lock:
            results.append(thread_id)

    threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(1, 6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logger.shutdown()
    print(f"\n  All {len(results)} threads completed successfully.")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LOGGING SYSTEM — INTERVIEW IMPLEMENTATION")
    print("=" * 70)

    demo_1_basic_logging()
    demo_2_level_filtering()
    demo_3_json_formatter_and_cloud()
    demo_4_rotating_file()
    demo_5_multithreaded()

    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")
```

### Thread-Safety Analysis

| Operation | Lock Strategy | Guarantees |
|-----------|---|---|
| **log() enqueue** | `queue.Queue` (thread-safe built-in) | Multiple callers never corrupt the queue |
| **add/remove appender** | Logger `RLock` | No mid-list modification during dispatch |
| **_dispatch (worker)** | Snapshot appenders under `RLock` | Concurrent add/remove safe while iterating |
| **RotatingFileAppender._write** | Per-appender `Lock` | No interleaved writes; rotation is atomic |
| **LogManager.get_logger** | LogManager `RLock` | Same name always returns same instance |
| **LogManager Singleton init** | Class-level `RLock` | Double-checked locking; single instance |

**Concurrency Principles**:
1. ✅ `RLock` (reentrant) — worker can re-enter the same lock within `_dispatch`; prevents deadlock
2. ✅ Minimize lock duration — appenders are snapshotted inside the lock, then called outside it
3. ✅ Worker is a daemon thread — does not prevent application exit
4. ✅ `_SENTINEL` object drains queue cleanly before worker stops

---

## Demo Scenarios

### Scenario 1: Basic Log Levels (Console Output)

```
[2025-01-15 12:30:45] DEBUG [demo1] Application booting  component=init
[2025-01-15 12:30:45] INFO  [demo1] Server listening  port=8080 host=0.0.0.0
[2025-01-15 12:30:45] WARN  [demo1] High memory usage  pct=87
[2025-01-15 12:30:45] ERROR [demo1] Unhandled exception  exc=ValueError line=42
[2025-01-15 12:30:45] FATAL [demo1] Out of disk space  path=/var/log
```

### Scenario 2: Level Filtering (Logger at WARN)

```
[Silently dropped] DEBUG — "This DEBUG message is silently dropped"
[Silently dropped] INFO  — "This INFO message is silently dropped"
[2025-01-15 12:30:46] WARN  [demo2] WARN passes the logger gate → printed
[2025-01-15 12:30:46] ERROR [demo2] ERROR passes the logger gate → printed
```

### Scenario 3: JSON Formatter + Cloud Appender (ERROR+)

```
Console (plain text):
  [2025-01-15 12:30:47] INFO  [demo3] Request received  method=GET path=/api/orders
  [2025-01-15 12:30:47] WARN  [demo3] Slow query detected  duration_ms=1450 table=orders
  [2025-01-15 12:30:47] ERROR [demo3] Payment gateway timeout  gateway=Stripe retry=2

Cloud receives (JSON, ERROR level only):
  {"timestamp":"2025-01-15T12:30:47","level":"ERROR","logger":"demo3",
   "message":"Payment gateway timeout","gateway":"Stripe","retry":2}
```

### Scenario 4: Log Rotation

```
After 10 log lines with 200-byte size limit:
  Files created: ['app.log', 'app.log.1', 'app.log.2', 'app.log.3']
  Rotation working: True
```

### Scenario 5: Multi-threaded Logging

```
5 threads each emitting 3 INFO messages concurrently → 15 lines total
No interleaved/corrupt output; all 5 threads complete successfully.
```

---

## Interview Q&A

### Basic Questions

**Q1: Why is async logging important?**

A: Synchronous logging blocks the application thread until the I/O completes. A file write can take 1-10 ms; a network call to Elasticsearch can take 50+ ms. With async logging, the calling thread enqueues in ~microseconds and continues — the background worker handles I/O independently. This is critical for high-throughput services.

**Q2: How does log level filtering work?**

A: Two-gate chain of responsibility:
1. **Logger gate** — if `event.level < logger.level`, drop immediately (no enqueue, no allocation).
2. **Appender gate** — if `event.level < appender.min_level`, the appender skips writing.

This allows a console appender to show DEBUG while a file appender only records ERROR.

**Q3: What is structured logging and why is it valuable?**

A: Instead of `logger.info("Order placed for user 123 amount $99")`, you write `logger.info("Order placed", user_id=123, amount=99)`. The key-value pairs are stored in `LogMessage.context` and rendered as JSON by `JsonFormatter`. This makes logs machine-searchable: `WHERE amount > 50 AND user_id = 123` in Elasticsearch vs full-text regex on strings.

**Q4: How does log rotation work?**

A: Before each write, `RotatingFileAppender` checks `os.path.getsize(file_path)`. If it exceeds `max_bytes`, it renames `app.log → app.log.1`, `app.log.1 → app.log.2`, etc. (up to `backup_count`), then creates a fresh `app.log`. The oldest backup is deleted if `backup_count` is exceeded.

**Q5: How do you ensure logs are not lost on application shutdown?**

A: `Logger.shutdown()` sets `_running = False` and puts a `_SENTINEL` on the queue. The worker drains all remaining real messages before the sentinel causes it to exit. `LogManager.shutdown_all()` calls this on every registered logger.

---

### Intermediate Questions

**Q6: How is thread safety maintained when multiple threads log concurrently?**

A: `queue.Queue` is inherently thread-safe (uses an internal lock). Multiple callers can call `log()` simultaneously without corruption. The single worker thread sequentially dequeues and dispatches — serializing all appender writes without needing additional locking in the hot path.

**Q7: Why use `threading.RLock` instead of `threading.Lock` in Logger?**

A: `_dispatch` is called from `_worker_loop` while holding `_lock` (to snapshot appenders). If an appender internally calls back into the same Logger (e.g., a meta-logging scenario), a plain `Lock` would deadlock. An `RLock` (reentrant lock) allows the same thread to re-acquire it.

**Q8: How would you add a new Syslog or Kafka appender?**

A: Create a class that extends `Appender` and implements `_write(text: str)`. The formatter is already injected; the appender just sends the text to the new destination. Zero changes to Logger, LogManager, or other appenders.

**Q9: What is the difference between `FileAppender` and `RotatingFileAppender`?**

A: `FileAppender` opens and appends without checking file size — it will grow unboundedly. `RotatingFileAppender` adds a per-write size check and a rotation mechanism, maintaining at most `1 + backup_count` files. Use `FileAppender` only for short-lived processes; prefer `RotatingFileAppender` for long-running services.

**Q10: How would you redact sensitive data (passwords, tokens)?**

A: Add a `RedactingFormatter` that wraps another formatter. Before returning the string, it applies regex patterns to replace sensitive fields: `re.sub(r'"password":"[^"]*"', '"password":"[REDACTED]"', text)`. Plug it in as the formatter for any appender that writes to external storage.

---

### Advanced Questions

**Q11: How would you implement log sampling for high-traffic services?**

A: Add a `SamplingAppender` wrapper that forwards only 1 in N messages: `if random.random() < self.sample_rate: self._inner.append(msg)`. Apply it only to DEBUG/INFO at the appender level; always forward WARN+ unsampled.

**Q12: How would you centralize logs from 10 microservices?**

A: Each service uses a `CloudAppender` that POSTs JSON log batches to a Kafka topic. A consumer group reads from Kafka and indexes into Elasticsearch. Kibana/Grafana queries Elasticsearch. Correlation IDs (`trace_id`, `request_id`) in `LogMessage.context` link events across services.

---

## Scaling Q&A

### Q1: Handle 100K log events per second from 10 services?

**Solution**: Replace the single queue with a ring buffer (circular array, lock-free). Batch writes: accumulate 100 messages or 50 ms, then write in one `fwrite()` call. Compress before cloud upload (gzip reduces 10x). Each service's CloudAppender batches and sends to Kafka, decoupling write spikes from Elasticsearch indexing speed.

### Q2: Multi-appender performance — one slow appender blocking others?

**Solution**: Give each appender its own queue and background thread (or thread-pool worker). The Logger dispatches to per-appender queues in O(N) time with no I/O — a slow CloudAppender's queue backs up in memory without blocking the FileAppender or ConsoleAppender.

### Q3: Log search at scale (years of data)?

**Solution**: Elasticsearch: ingest pipeline tags each document with `@timestamp`, `level`, `service`. Index per-day (`logs-2025-01-15`). ILM (Index Lifecycle Management) moves indexes from hot SSD → warm HDD → cold archive → delete after retention period. Search in <1 s across years via inverted index on structured fields.

### Q4: Cost optimization for log storage?

**Solution**: Tiered strategy: keep ERROR+ in hot storage (7 days), WARN in warm (30 days), INFO in cold (90 days), delete DEBUG after 24 hours. Compress all files with gzip. Apply log sampling (1 in 100) for INFO in high-traffic paths. Estimated 80% storage reduction vs naive "keep everything forever."

### Q5: Distributed tracing across services?

**Solution**: Inject `trace_id` and `span_id` into `LogMessage.context` via a thread-local context propagator (similar to OpenTelemetry). All log events for a single user request share the same `trace_id`. Elasticsearch query on `trace_id` reconstructs the full execution path across all 10 services.

### Q6: Real-time alerting on error patterns?

**Solution**: Stream log events to Kafka. A stream processor (Flink/Kafka Streams) applies a sliding window: if ERROR count > 50 in 60 seconds, trigger a PagerDuty alert. This decouples alerting from the logging write path — no synchronous notification in the hot path.

---

## Success Checklist

- [ ] Explain all 6 steps: Setup → Structure → Interface → Architecture → Optimization → Implementation
- [ ] Draw UML class diagram: LogManager → Logger → Appender hierarchy → Formatter
- [ ] Explain async logging: queue + worker thread, why non-blocking matters
- [ ] Explain two-gate level filtering: Logger gate then Appender gate
- [ ] Demonstrate Strategy pattern: swap PlainTextFormatter vs JsonFormatter
- [ ] Explain log rotation: size-based rename chain, backup_count
- [ ] Run complete implementation (5 demos) without errors
- [ ] Explain thread safety: RLock vs Lock, snapshot-then-iterate pattern
- [ ] Explain graceful shutdown: sentinel drains queue before worker exits
- [ ] Answer 5+ scaling Q&A questions (ring buffer, per-appender threads, Elasticsearch)
- [ ] Discuss trade-offs: sync vs async, in-process vs out-of-process aggregation

---

**Ready for interview? Start logging! 📝**
