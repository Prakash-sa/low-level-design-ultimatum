# Circuit Breaker Pattern

> Provide a way to prevent cascading failures in distributed systems by monitoring for failures and temporarily blocking requests to failing services.

---

## Problem

In distributed systems, services depend on each other. When one service fails, it can cause cascading failures across the entire system. Repeated calls to failing services waste resources.

## Solution

The Circuit Breaker pattern monitors for failures and automatically stops sending requests to a failing service, returning an error immediately instead of waiting for timeout.

---

## Implementation

```python
import time
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

# ============ CIRCUIT BREAKER STATES ============

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

# ============ BASIC CIRCUIT BREAKER ============

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, 
                 timeout_seconds: int = 60, 
                 success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                print(f"✅ Circuit breaker CLOSED (recovered)")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"🔴 Circuit breaker OPEN (too many failures)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout has elapsed"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_seconds
    
    def get_state(self) -> str:
        return self.state.value

# ============ ADVANCED CIRCUIT BREAKER WITH METRICS ============

class CircuitBreakerMetrics:
    """Track circuit breaker metrics"""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.blocked_calls = 0
    
    def record_call(self, success: bool, blocked: bool = False):
        self.total_calls += 1
        if blocked:
            self.blocked_calls += 1
        elif success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
    
    def get_success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    def __str__(self) -> str:
        return (f"Metrics(total={self.total_calls}, "
                f"success={self.successful_calls}, "
                f"failed={self.failed_calls}, "
                f"blocked={self.blocked_calls}, "
                f"rate={self.get_success_rate():.2%})")

class AdvancedCircuitBreaker:
    """Circuit breaker with metrics and detailed tracking"""
    
    def __init__(self, failure_threshold: int = 5, 
                 timeout_seconds: int = 60,
                 success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with metrics"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                print(f"🟡 Circuit breaker HALF_OPEN (testing recovery)")
            else:
                self.metrics.record_call(False, blocked=True)
                raise Exception(f"Circuit breaker OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self.metrics.record_call(success=True)
            self._on_success()
            return result
        except Exception as e:
            self.metrics.record_call(success=False)
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                print(f"✅ Circuit breaker CLOSED")
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"🔴 Circuit breaker OPEN")
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_seconds
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        return self.metrics

# ============ REAL-WORLD EXAMPLE: Payment Service ============

class PaymentService:
    """External payment service that can fail"""
    
    def __init__(self, fail_rate: float = 0.0):
        self.fail_rate = fail_rate
        self.call_count = 0
    
    def process_payment(self, amount: float) -> dict:
        """Simulate payment processing with potential failures"""
        self.call_count += 1
        
        import random
        if random.random() < self.fail_rate:
            raise Exception("Payment service temporarily unavailable")
        
        return {"status": "success", "amount": amount, "txn_id": f"TXN{self.call_count}"}

class OrderService:
    """Service that depends on payment service"""
    
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service
        self.circuit_breaker = AdvancedCircuitBreaker(
            failure_threshold=3,
            timeout_seconds=10,
            success_threshold=2
        )
    
    def place_order(self, order_id: str, amount: float) -> dict:
        """Place order with circuit breaker protection"""
        try:
            result = self.circuit_breaker.call(
                self.payment_service.process_payment,
                amount
            )
            return {
                "order_id": order_id,
                "status": "success",
                "payment": result
            }
        except Exception as e:
            return {
                "order_id": order_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_metrics(self):
        return self.circuit_breaker.get_metrics()

# ============ DECORATOR-BASED CIRCUIT BREAKER ============

def circuit_breaker_decorator(failure_threshold: int = 5, 
                               timeout_seconds: int = 60):
    """Decorator to add circuit breaker to any function"""
    
    def decorator(func: Callable) -> Callable:
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds
        )
        
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator

@circuit_breaker_decorator(failure_threshold=2, timeout_seconds=5)
def external_api_call(endpoint: str) -> str:
    """Simulated external API call"""
    import random
    if random.random() < 0.6:
        raise Exception(f"Failed to reach {endpoint}")
    return f"Response from {endpoint}"

# ============ FALLBACK STRATEGY ============

class CircuitBreakerWithFallback:
    """Circuit breaker with fallback behavior"""
    
    def __init__(self, primary_func: Callable, 
                 fallback_func: Callable,
                 failure_threshold: int = 5,
                 timeout_seconds: int = 60):
        self.primary_func = primary_func
        self.fallback_func = fallback_func
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds
        )
    
    def call(self, *args, **kwargs) -> Any:
        """Try primary, fall back on circuit open"""
        try:
            return self.circuit_breaker.call(self.primary_func, *args, **kwargs)
        except Exception as e:
            print(f"⚠️ Falling back due to: {e}")
            return self.fallback_func(*args, **kwargs)

# Demo
if __name__ == "__main__":
    print("=" * 60)
    print("=== BASIC CIRCUIT BREAKER ===")
    print("=" * 60)
    
    def unreliable_service(should_fail: bool = False):
        if should_fail:
            raise Exception("Service failed")
        return "Success"
    
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=5)
    
    # Simulate failures
    for i in range(5):
        try:
            result = cb.call(unreliable_service, should_fail=(i < 3))
            print(f"Call {i+1}: {result} - State: {cb.get_state()}")
        except Exception as e:
            print(f"Call {i+1}: {e} - State: {cb.get_state()}")
    
    print("\n" + "=" * 60)
    print("=== ADVANCED CIRCUIT BREAKER WITH METRICS ===")
    print("=" * 60)
    
    payment_service = PaymentService(fail_rate=0.0)
    order_service = OrderService(payment_service)
    
    # Successful orders
    for i in range(3):
        result = order_service.place_order(f"ORD{i+1}", 100.0)
        print(f"Order {i+1}: {result['status']}")
    
    print(f"Metrics: {order_service.get_metrics()}\n")
    
    # Simulate service failure
    payment_service.fail_rate = 0.9
    print("Service failure rate increased to 90%...\n")
    
    for i in range(5):
        result = order_service.place_order(f"ORD{i+4}", 100.0)
        print(f"Order {i+4}: {result['status']}")
    
    print(f"Metrics: {order_service.get_metrics()}\n")
    
    print("=" * 60)
    print("=== CIRCUIT BREAKER WITH FALLBACK ===")
    print("=" * 60)
    
    def primary_service():
        import random
        if random.random() < 0.8:
            raise Exception("Primary failed")
        return "Primary response"
    
    def fallback_service():
        return "Fallback response"
    
    cb_fallback = CircuitBreakerWithFallback(
        primary_service, fallback_service,
        failure_threshold=2, timeout_seconds=5
    )
    
    for i in range(5):
        result = cb_fallback.call()
        print(f"Call {i+1}: {result}")
```

---

## Key Concepts

- **CLOSED State**: Normal operation, requests pass through
- **OPEN State**: Service failing, requests blocked immediately
- **HALF_OPEN State**: Testing if service recovered, limited requests allowed
- **Failure Threshold**: Number of failures before opening circuit
- **Timeout**: Duration before attempting recovery
- **Success Threshold**: Successful calls needed in HALF_OPEN to close circuit

---

## When to Use

✅ Microservices communication  
✅ External API calls  
✅ Database connections  
✅ Prevent cascading failures  
✅ Resource protection  

---

## Interview Q&A

**Q1: What are the three states of a circuit breaker and transitions?**

A:
- **CLOSED → OPEN**: Failure count exceeds threshold
- **OPEN → HALF_OPEN**: Timeout period expires
- **HALF_OPEN → CLOSED**: Enough successful calls
- **HALF_OPEN → OPEN**: Failure occurs

---

**Q2: How do you handle timeouts in circuit breaker?**

A:
```python
def _should_attempt_reset(self):
    if not self.last_failure_time:
        return False
    elapsed = (datetime.now() - self.last_failure_time).total_seconds()
    return elapsed >= self.timeout_seconds
```

---

**Q3: What metrics should you track?**

A: Success rate, failure rate, blocked calls, state changes, call latency

```python
class CircuitBreakerMetrics:
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.blocked_calls = 0
```

---

**Q4: How do you combine circuit breaker with fallback?**

A:
```python
try:
    return circuit_breaker.call(primary_service)
except Exception:
    return fallback_service()
```

---

**Q5: How do you test circuit breaker code?**

A:
```python
def test_circuit_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=2)
    
    for _ in range(2):
        try:
            cb.call(failing_function)
        except:
            pass
    
    assert cb.get_state() == "open"
```

---

## Trade-offs

✅ **Pros**: Prevents cascading failures, fast failure, resource protection  
❌ **Cons**: Complexity, requires fallback strategy, state management

---

## Real-World Examples

- **Netflix Hystrix** (now Resilience4j)
- **Spring Cloud Circuit Breaker**
- **AWS AppConfig**
- **Kubernetes liveness probes**
