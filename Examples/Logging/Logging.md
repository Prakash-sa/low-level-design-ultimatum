# Logging System — 75-Minute Interview Guide

## Quick Start

### 5-Minute Overview
A centralized logging system that captures, processes, stores, and retrieves application logs. Core flow: **Log event → Format → Route → Store → Query**.

### Key Entities
| Entity | Purpose |
|--------|---------|
| **Logger** | Captures log events |
| **Log Level** | Severity (DEBUG, INFO, WARN, ERROR, FATAL) |
| **Appender** | Routes logs (console, file, cloud) |
| **Formatter** | Formats log output |
| **LogAggregator** | Centralizes logs from multiple sources |

### 4 Design Patterns
1. **Singleton**: Central logger instance
2. **Observer**: Appenders notified of logs
3. **Strategy**: Different formatting strategies
4. **Factory**: Logger creation

### Critical Points
✅ Thread-safe logging  
✅ Async writes (non-blocking)  
✅ Log rotation (prevent disk overflow)  
✅ Log levels (filter by severity)  
✅ Performance (minimal overhead)  

---

## System Overview

### Problem
Applications need to log events efficiently without blocking. Logs must be searchable and not overwhelm disk.

### Solution
Async logging with buffering, multiple appenders, rotation, and centralized aggregation.

---

## Requirements

✅ Log with different levels (DEBUG, INFO, WARN, ERROR, FATAL)  
✅ Multiple appenders (console, file, cloud)  
✅ Async writes (non-blocking)  
✅ Log rotation (daily, size-based)  
✅ Structured logging (key-value pairs)  
✅ Searchable logs  
✅ Configurable format  

---

## Architecture & Patterns

### 1. Logger Singleton
```python
class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.appenders = []
            cls._instance.level = LogLevel.INFO
            cls._instance.queue = queue.Queue()
        return cls._instance
    
    def log(self, level, message, **kwargs):
        if level >= self.level:
            log_entry = LogEntry(level, message, kwargs)
            self.queue.put(log_entry)  # Async
```

### 2. Appender Pattern (Observer)
```python
class Appender(ABC):
    @abstractmethod
    def append(self, log_entry):
        pass

class FileAppender(Appender):
    def append(self, log_entry):
        with open(self.file, 'a') as f:
            f.write(self.formatter.format(log_entry))

class ConsoleAppender(Appender):
    def append(self, log_entry):
        print(self.formatter.format(log_entry))

class CloudAppender(Appender):
    def append(self, log_entry):
        # Send to Elasticsearch/CloudWatch
        pass
```

### 3. Async Processing
```python
class AsyncLogger:
    def __init__(self, logger):
        self.logger = logger
        self.worker_thread = Thread(target=self._process_logs, daemon=True)
        self.worker_thread.start()
    
    def _process_logs(self):
        while True:
            log_entry = self.logger.queue.get()
            for appender in self.logger.appenders:
                appender.append(log_entry)
```

### 4. Log Rotation
```python
class RotatingFileAppender(FileAppender):
    def append(self, log_entry):
        size = os.path.getsize(self.file)
        if size > self.max_size:
            self._rotate()  # Rename to log.1, create new log
        super().append(log_entry)
```

---

## Interview Q&A

### Q1: Why async logging?
**A**: Sync logging blocks application. Async queues logs, writes in background. Non-blocking.

### Q2: Log level filtering?
**A**: Set logger.level = LogLevel.WARN. Only log WARN, ERROR, FATAL. Skip DEBUG, INFO.

### Q3: Log rotation strategy?
**A**: By size (rotate when >100MB) or time (daily at midnight). Keep last 7 days.

### Q4: Structured logging?
**A**: `logger.info("Order placed", order_id="123", amount=99.99)` → JSON `{"msg":"Order placed","order_id":"123","amount":99.99}` → Easy to search.

### Q5: Multi-thread safety?
**A**: Queue is thread-safe. Use queue.Queue() for appender serialization.

### Q6: Performance impact?
**A**: Async + queue = minimal overhead. App thread just puts message in queue, continues.

### Q7: Centralized logging (many services)?
**A**: All services send logs to central aggregator (Elasticsearch, Splunk). Query all logs together.

### Q8: Log sampling?
**A**: High traffic → sample 1% of logs. Skip repetitive debug logs to reduce storage.

### Q9: Real-time monitoring?
**A**: Stream logs to Kafka → process in real-time → alert on error patterns.

### Q10: Privacy concerns?
**A**: Redact sensitive data (passwords, tokens, PII) before logging. Use formatter to strip.

---

## Scaling Q&A

### Q1: 100K logs/sec (10 services × 10K each)?
**A**: Ring buffer (circular array), batch writes, compression before cloud storage.

### Q2: Multi-appender performance?
**A**: Thread pool for appenders. Each appender in parallel thread. One slow appender doesn't block others.

### Q3: Log search at scale?
**A**: Elasticsearch indexing. Ingest 100K logs/sec, search in <1s across years of data.

### Q4: Cost optimization?
**A**: Compress logs (gzip), tiered storage (hot SSD → cold archive), delete old logs after retention.

---

## Demo
```python
logger = Logger()
logger.add_appender(ConsoleAppender())
logger.add_appender(FileAppender("app.log"))

logger.info("Application started")
logger.warn("High memory usage", usage="85%")
logger.error("Database connection failed")

# Query logs
logs = logger.search(level="ERROR", time_range="last_1h")
```

---

**Ready to log! 📝**
