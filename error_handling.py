# error_handling.py
"""
Error handling utilities with circuit breaker pattern and retry mechanisms.
"""

import time
import logging
import asyncio
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass, field
from threading import Lock
import traceback

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: float = 30.0  # Request timeout in seconds

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = Lock()
        # Cache log messages to avoid string formatting on every call
        self._log_msgs = {
            'open': f"Circuit breaker {name} is open",
            'half_open': f"Circuit breaker {name} attempting recovery (half-open)",
            'closed': f"Circuit breaker {name} closed after recovery",
            'open_again': f"Circuit breaker {name} opened again after failed recovery attempt",
            'failure': f"Circuit breaker {name} recorded failure: "
        }
        
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from OPEN to HALF_OPEN."""
        if not self.last_failure_time:
            return False
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _record_success(self):
        """Record a successful operation."""
        with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info(self._log_msgs['closed'])
    
    def _record_failure(self):
        """Record a failed operation."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.success_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(self._log_msgs['open_again'])
            elif (self.state == CircuitState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        # Fast path for closed state
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if execution_time > self.config.timeout:
                    raise TimeoutError(f"Operation timed out after {execution_time:.2f}s")
                
                self._record_success()
                return result
            except Exception as e:
                self._record_failure()
                logger.error(self._log_msgs['failure'] + str(e))
                raise
        
        # Slow path for open/half-open states
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(self._log_msgs['half_open'])
                else:
                    raise CircuitBreakerOpenError(self._log_msgs['open'])
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > self.config.timeout:
                raise TimeoutError(f"Operation timed out after {execution_time:.2f}s")
            
            self._record_success()
            return result
            
        except Exception as e:
            self._record_failure()
            logger.error(self._log_msgs['failure'] + str(e))
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(self._log_msgs['half_open'])
            else:
                raise CircuitBreakerOpenError(self._log_msgs['open'])

        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            logger.error(self._log_msgs['failure'] + str(e))
            raise
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator interface supporting sync and async functions."""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return wrapper

class RetryConfig:
    """Configuration for retry mechanism."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

class RetryHandler:
    """Retry mechanism with exponential backoff and jitter."""
    
    # Pre-define retryable error types for better performance
    RETRYABLE_ERROR_TYPES = (ConnectionError, TimeoutError, OSError)
    NON_RETRYABLE_PATTERNS = frozenset([
        'authentication', 'authorization', 'forbidden', 
        'validation', 'bad request'
    ])
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        # Import random once during initialization instead of in each call
        import random
        self.random = random
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add jitter to prevent thundering herd
            delay *= (0.5 + self.random.random() * 0.5)
        
        return delay
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if error is retryable."""
        # First check instance type (faster check)
        if isinstance(error, self.RETRYABLE_ERROR_TYPES):
            # Then check error message patterns
            error_msg = str(error).lower()
            return not any(pattern in error_msg for pattern in self.NON_RETRYABLE_PATTERNS)
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        max_attempts = self.config.max_attempts
        
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    logger.debug(f"Retry attempt {attempt}/{max_attempts} for {func.__name__}")
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts:
                    logger.error(f"All retry attempts failed for {func.__name__}: {str(e)}")
                    break
                
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error for {func.__name__}: {str(e)}")
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed for {func.__name__}: {str(e)}. Retrying in {delay:.2f}s")
                time.sleep(delay)
        
        raise last_exception
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with retry logic."""
        last_exception = None
        max_attempts = self.config.max_attempts
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    logger.debug(f"Retry attempt {attempt}/{max_attempts} for {func.__name__}")
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_attempts:
                    logger.error(f"All retry attempts failed for {func.__name__}: {str(e)}")
                    raise e
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error for {func.__name__}: {str(e)}")
                    raise e
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed for {func.__name__}: {str(e)}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        raise last_exception
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator interface supporting sync and async functions."""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.execute_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute(func, *args, **kwargs)
            return wrapper

def resilient(
    circuit_breaker_name: str,
    cb_config: CircuitBreakerConfig = None,
    retry_config: RetryConfig = None
):
    """Combined decorator for circuit breaker + retry with async support."""
    def decorator(func: Callable) -> Callable:
        retry_handler = RetryHandler(retry_config)
        cb = get_circuit_breaker(circuit_breaker_name, cb_config)
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await cb.call_async(retry_handler.execute_async, func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return cb.call(retry_handler.execute, func, *args, **kwargs)
            return wrapper
    return decorator

class ErrorTracker:
    """Track and analyze error patterns."""
    
    def __init__(self, max_errors=1000):
        self.errors: List[Dict[str, Any]] = []
        self.lock = Lock()
        self.max_errors = max_errors
        # Pre-calculate seconds in an hour for faster calculations
        self.seconds_per_hour = 3600
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Record an error with context."""
        with self.lock:
            # Create error record with minimal data
            error_record = {
                'timestamp': time.time(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                # Store only the last 1000 characters of traceback to save memory
                'traceback': traceback.format_exc()[-1000:] if traceback.format_exc() else "",
                'context': context or {}
            }
            
            # Use deque-like behavior for better performance
            self.errors.append(error_record)
            if len(self.errors) > self.max_errors:
                self.errors.pop(0)  # Remove oldest error (more efficient than slicing)
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        cutoff_time = time.time() - (hours * self.seconds_per_hour)
        
        # Use a more efficient approach with Counter
        from collections import Counter
        
        with self.lock:
            # Filter errors in a single pass
            recent_errors = []
            error_types = []
            
            for error in reversed(self.errors):  # Start from most recent
                if error['timestamp'] > cutoff_time:
                    recent_errors.append(error)
                    error_types.append(error['error_type'])
                    # Only collect the 10 most recent errors
                    if len(recent_errors) >= 10:
                        break
            
            # Count all error types in one pass
            error_counts = Counter(error['error_type'] for error in self.errors
                                   if error['timestamp'] > cutoff_time)

            return {
                'total_errors': sum(error_counts.values()),
                'error_types': dict(error_counts),
                'recent_errors': recent_errors  # Already limited to 10 most recent
            }

# Global error tracker
error_tracker = ErrorTracker()

def handle_errors(context: Dict[str, Any] = None):
    """Decorator to automatically track errors."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()) if kwargs else []
                }
                if context:
                    error_context.update(context)
                
                error_tracker.record_error(e, error_context)
                raise
        return wrapper
    return decorator

# Custom exceptions
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass

# Global circuit breakers for different services
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection (supports sync/async)."""
    def decorator(func: Callable) -> Callable:
        cb = get_circuit_breaker(name, config)
        return cb(func)
    return decorator

def retry(config: RetryConfig = None):
    """Decorator for retry logic (supports sync/async via RetryHandler.__call__)."""
    return RetryHandler(config)