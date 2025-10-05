"""
Comprehensive tests for error handling module
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from error_handling import (
    CircuitBreakerConfig, CircuitBreaker, CircuitBreakerState,
    RetryConfig, RetryHandler, ErrorTracker,
    circuit_breaker, retry, resilient, handle_errors,
    CircuitBreakerError, RetryExhaustedError, ServiceUnavailableError
)

class TestCircuitBreakerConfig:
    """Test cases for CircuitBreakerConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.success_threshold == 3
        assert config.timeout == 30
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            success_threshold=5,
            timeout=60
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120
        assert config.success_threshold == 5
        assert config.timeout == 60

class TestCircuitBreaker:
    """Test cases for CircuitBreaker"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,  # Short timeout for testing
            success_threshold=2,
            timeout=5
        )
        self.circuit_breaker = CircuitBreaker("test_service", self.config)
    
    def test_initial_state(self):
        """Test initial circuit breaker state"""
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0
    
    def test_record_success(self):
        """Test recording successful operations"""
        self.circuit_breaker.record_success()
        assert self.circuit_breaker.success_count == 1
        assert self.circuit_breaker.failure_count == 0
    
    def test_record_failure(self):
        """Test recording failed operations"""
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.failure_count == 1
        assert self.circuit_breaker.success_count == 0
    
    def test_state_transition_to_open(self):
        """Test state transition from CLOSED to OPEN"""
        # Record failures to reach threshold
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
    
    def test_state_transition_to_half_open(self):
        """Test state transition from OPEN to HALF_OPEN"""
        # Move to OPEN state
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Check if can attempt
        assert self.circuit_breaker.can_attempt() == True
        assert self.circuit_breaker.state == CircuitBreakerState.HALF_OPEN
    
    def test_state_transition_to_closed_from_half_open(self):
        """Test state transition from HALF_OPEN to CLOSED"""
        # Move to HALF_OPEN state
        for _ in range(3):
            self.circuit_breaker.record_failure()
        time.sleep(1.1)
        self.circuit_breaker.can_attempt()  # Transition to HALF_OPEN
        
        # Record enough successes to close
        for _ in range(2):
            self.circuit_breaker.record_success()
        
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.failure_count == 0
    
    def test_can_attempt_when_closed(self):
        """Test can_attempt when circuit is CLOSED"""
        assert self.circuit_breaker.can_attempt() == True
    
    def test_can_attempt_when_open(self):
        """Test can_attempt when circuit is OPEN"""
        # Move to OPEN state
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        assert self.circuit_breaker.can_attempt() == False
    
    def test_reset(self):
        """Test circuit breaker reset"""
        # Record some failures
        for _ in range(2):
            self.circuit_breaker.record_failure()
        
        self.circuit_breaker.reset()
        
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0

class TestRetryConfig:
    """Test cases for RetryConfig"""
    
    def test_default_config(self):
        """Test default retry configuration"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter == True
    
    def test_custom_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False
        )
        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter == False

class TestRetryHandler:
    """Test cases for RetryHandler"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            jitter=False  # Disable jitter for predictable testing
        )
        self.retry_handler = RetryHandler(self.config)
    
    def test_calculate_delay(self):
        """Test delay calculation"""
        delay1 = self.retry_handler.calculate_delay(1)
        delay2 = self.retry_handler.calculate_delay(2)
        delay3 = self.retry_handler.calculate_delay(3)
        
        assert delay1 == 0.1
        assert delay2 == 0.2
        assert delay3 == 0.4
    
    def test_calculate_delay_with_max(self):
        """Test delay calculation with maximum limit"""
        config = RetryConfig(base_delay=10.0, max_delay=5.0, jitter=False)
        handler = RetryHandler(config)
        
        delay = handler.calculate_delay(5)
        assert delay == 5.0  # Should be capped at max_delay
    
    def test_should_retry_retryable_exception(self):
        """Test should_retry with retryable exceptions"""
        assert self.retry_handler.should_retry(ConnectionError()) == True
        assert self.retry_handler.should_retry(TimeoutError()) == True
        assert self.retry_handler.should_retry(Exception("Temporary error")) == True
    
    def test_should_retry_non_retryable_exception(self):
        """Test should_retry with non-retryable exceptions"""
        assert self.retry_handler.should_retry(ValueError()) == False
        assert self.retry_handler.should_retry(TypeError()) == False
    
    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        """Test successful async execution"""
        async def success_func():
            return "success"
        
        result = await self.retry_handler.execute_async(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_async_retry_then_success(self):
        """Test async execution with retry then success"""
        call_count = 0
        
        async def retry_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await self.retry_handler.execute_async(retry_then_success)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_async_max_retries_exceeded(self):
        """Test async execution with max retries exceeded"""
        async def always_fail():
            raise ConnectionError("Always fails")
        
        with pytest.raises(RetryExhaustedError):
            await self.retry_handler.execute_async(always_fail)
    
    def test_execute_sync_success(self):
        """Test successful sync execution"""
        def success_func():
            return "success"
        
        result = self.retry_handler.execute(success_func)
        assert result == "success"
    
    def test_execute_sync_retry_then_success(self):
        """Test sync execution with retry then success"""
        call_count = 0
        
        def retry_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = self.retry_handler.execute(retry_then_success)
        assert result == "success"
        assert call_count == 3

class TestErrorTracker:
    """Test cases for ErrorTracker"""
    
    def setup_method(self):
        """Setup test environment"""
        self.error_tracker = ErrorTracker()
    
    def test_record_error(self):
        """Test error recording"""
        error = ValueError("Test error")
        self.error_tracker.record_error("test_service", error, {"key": "value"})
        
        summary = self.error_tracker.get_error_summary("test_service")
        assert summary['total_errors'] == 1
        assert summary['error_types']['ValueError'] == 1
    
    def test_get_error_summary_empty(self):
        """Test error summary for service with no errors"""
        summary = self.error_tracker.get_error_summary("nonexistent_service")
        assert summary['total_errors'] == 0
        assert summary['error_types'] == {}
    
    def test_get_recent_errors(self):
        """Test getting recent errors"""
        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")
        
        self.error_tracker.record_error("test_service", error1)
        self.error_tracker.record_error("test_service", error2)
        
        recent_errors = self.error_tracker.get_recent_errors("test_service", limit=1)
        assert len(recent_errors) == 1
        assert recent_errors[0]['error_type'] == 'TypeError'
    
    def test_clear_errors(self):
        """Test clearing errors"""
        error = ValueError("Test error")
        self.error_tracker.record_error("test_service", error)
        
        self.error_tracker.clear_errors("test_service")
        
        summary = self.error_tracker.get_error_summary("test_service")
        assert summary['total_errors'] == 0

class TestDecorators:
    """Test cases for decorator functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.call_count = 0
    
    def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker decorator with successful function"""
        @circuit_breaker("test_service", CircuitBreakerConfig(failure_threshold=2))
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker decorator with failing function"""
        @circuit_breaker("test_service_2", CircuitBreakerConfig(failure_threshold=2))
        def failing_func():
            raise ValueError("Always fails")
        
        # First two calls should raise ValueError
        with pytest.raises(ValueError):
            failing_func()
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Third call should raise CircuitBreakerError (circuit is open)
        with pytest.raises(CircuitBreakerError):
            failing_func()
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful function"""
        @retry(RetryConfig(max_attempts=3))
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_retry_decorator_eventual_success(self):
        """Test retry decorator with eventual success"""
        @retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def eventual_success():
            self.call_count += 1
            if self.call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = eventual_success()
        assert result == "success"
        assert self.call_count == 3
    
    def test_resilient_decorator(self):
        """Test resilient decorator combining circuit breaker and retry"""
        @resilient(
            "resilient_service",
            cb_config=CircuitBreakerConfig(failure_threshold=5),
            retry_config=RetryConfig(max_attempts=2, base_delay=0.01)
        )
        def resilient_func():
            self.call_count += 1
            if self.call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = resilient_func()
        assert result == "success"
        assert self.call_count == 2
    
    def test_handle_errors_decorator(self):
        """Test handle_errors decorator"""
        @handle_errors(context={"service": "test"})
        def error_func():
            raise ValueError("Test error")
        
        # Should not raise exception, but log it
        result = error_func()
        assert result is None

class TestAsyncDecorators:
    """Test cases for async decorator functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.call_count = 0
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker_decorator(self):
        """Test async circuit breaker decorator"""
        @circuit_breaker("async_service", CircuitBreakerConfig(failure_threshold=2))
        async def async_success_func():
            return "async_success"
        
        result = await async_success_func()
        assert result == "async_success"
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """Test async retry decorator"""
        @retry(RetryConfig(max_attempts=3, base_delay=0.01))
        async def async_eventual_success():
            self.call_count += 1
            if self.call_count < 3:
                raise ConnectionError("Temporary failure")
            return "async_success"
        
        result = await async_eventual_success()
        assert result == "async_success"
        assert self.call_count == 3

class TestExceptions:
    """Test cases for custom exceptions"""
    
    def test_circuit_breaker_error(self):
        """Test CircuitBreakerError"""
        error = CircuitBreakerError("test_service", "Circuit breaker is open")
        assert error.service_name == "test_service"
        assert "Circuit breaker is open" in str(error)
    
    def test_retry_exhausted_error(self):
        """Test RetryExhaustedError"""
        original_error = ValueError("Original error")
        error = RetryExhaustedError(3, original_error)
        assert error.max_attempts == 3
        assert error.last_exception == original_error
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError"""
        error = ServiceUnavailableError("test_service", "Service is down")
        assert error.service_name == "test_service"
        assert "Service is down" in str(error)

if __name__ == '__main__':
    pytest.main([__file__])