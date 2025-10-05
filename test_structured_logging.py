"""
Comprehensive tests for structured logging
"""

import pytest
import json
import time
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import logging
from structured_logging import (
    CorrelationContext, StructuredFormatter, PerformanceLogger,
    SecurityLogger, setup_structured_logging, get_logger,
    get_performance_logger, get_security_logger, with_correlation_id,
    log_function_call, log_api_request, log_api_response
)

class TestCorrelationContext:
    """Test cases for CorrelationContext"""
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        test_id = "test-correlation-id"
        CorrelationContext.set_correlation_id(test_id)
        
        assert CorrelationContext.get_correlation_id() == test_id
    
    def test_clear_correlation_id(self):
        """Test clearing correlation ID"""
        CorrelationContext.set_correlation_id("test-id")
        CorrelationContext.clear()
        
        assert CorrelationContext.get_correlation_id() is None
    
    def test_set_and_get_request_context(self):
        """Test setting and getting request context"""
        context = {
            "user_id": "user123",
            "session_id": "session456",
            "ip_address": "192.168.1.1"
        }
        
        CorrelationContext.set_request_context(context)
        retrieved_context = CorrelationContext.get_request_context()
        
        assert retrieved_context == context
    
    def test_update_request_context(self):
        """Test updating request context"""
        initial_context = {"user_id": "user123"}
        CorrelationContext.set_request_context(initial_context)
        
        update = {"session_id": "session456"}
        CorrelationContext.update_request_context(update)
        
        final_context = CorrelationContext.get_request_context()
        assert final_context["user_id"] == "user123"
        assert final_context["session_id"] == "session456"
    
    def test_clear_request_context(self):
        """Test clearing request context"""
        CorrelationContext.set_request_context({"user_id": "user123"})
        CorrelationContext.clear()
        
        assert CorrelationContext.get_request_context() == {}

class TestStructuredFormatter:
    """Test cases for StructuredFormatter"""
    
    def setup_method(self):
        """Setup test environment"""
        self.formatter = StructuredFormatter()
    
    def test_format_basic_log_record(self):
        """Test formatting basic log record"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test_logger"
        assert log_data["module"] == "test"
        assert log_data["line"] == 10
        assert "timestamp" in log_data
    
    def test_format_with_correlation_id(self):
        """Test formatting with correlation ID"""
        CorrelationContext.set_correlation_id("test-correlation-id")
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["correlation_id"] == "test-correlation-id"
        
        CorrelationContext.clear()
    
    def test_format_with_request_context(self):
        """Test formatting with request context"""
        context = {"user_id": "user123", "session_id": "session456"}
        CorrelationContext.set_request_context(context)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["request_context"] == context
        
        CorrelationContext.clear()
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.user_id = "user123"
        record.action = "login"
        record.duration = 0.5
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["user_id"] == "user123"
        assert log_data["action"] == "login"
        assert log_data["duration"] == 0.5
    
    def test_format_with_exception(self):
        """Test formatting with exception"""
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()  # Pass the actual exception tuple
            )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error occurred"
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]
        assert "Test exception" in log_data["exception"]

class TestPerformanceLogger:
    """Test cases for PerformanceLogger"""
    
    def setup_method(self):
        """Setup test environment"""
        self.logger = logging.getLogger("test_performance")
        self.logger.handlers = []  # Clear handlers
        
        # Add string handler for testing
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.perf_logger = PerformanceLogger(self.logger)
    
    def test_log_operation_timing(self):
        """Test logging operation timing"""
        self.perf_logger.log_operation_timing(
            operation="test_operation",
            duration=0.5,
            details={"param": "value"}
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["operation"] == "test_operation"
        assert log_data["duration"] == 0.5
        assert log_data["details"] == {"param": "value"}
        assert log_data["level"] == "INFO"
    
    def test_log_slow_operation(self):
        """Test logging slow operation"""
        self.perf_logger.log_slow_operation(
            operation="slow_operation",
            duration=2.5,
            threshold=1.0,
            details={"query": "SELECT * FROM table"}
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["operation"] == "slow_operation"
        assert log_data["duration"] == 2.5
        assert log_data["threshold"] == 1.0
        assert log_data["level"] == "WARNING"
        assert "slow" in log_data["message"].lower()
    
    def test_time_operation_context_manager(self):
        """Test timing operation with context manager"""
        with self.perf_logger.time_operation("context_operation", {"param": "value"}):
            time.sleep(0.1)  # Simulate work
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["operation"] == "context_operation"
        assert log_data["duration"] >= 0.1
        assert log_data["details"] == {"param": "value"}
    
    def test_time_operation_context_manager_with_exception(self):
        """Test timing operation context manager with exception"""
        try:
            with self.perf_logger.time_operation("failing_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["operation"] == "failing_operation"
        assert log_data["success"] is False
        assert "exception" in log_data

class TestSecurityLogger:
    """Test cases for SecurityLogger"""
    
    def setup_method(self):
        """Setup test environment"""
        self.logger = logging.getLogger("test_security")
        self.logger.handlers = []  # Clear handlers
        
        # Add string handler for testing
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.security_logger = SecurityLogger(self.logger)
    
    def test_log_authentication_attempt(self):
        """Test logging authentication attempt"""
        self.security_logger.log_authentication_attempt(
            user_id="user123",
            success=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event_type"] == "authentication_attempt"
        assert log_data["user_id"] == "user123"
        assert log_data["success"] is True
        assert log_data["ip_address"] == "192.168.1.1"
        assert log_data["user_agent"] == "Mozilla/5.0"
        assert log_data["level"] == "INFO"
    
    def test_log_failed_authentication(self):
        """Test logging failed authentication"""
        self.security_logger.log_authentication_attempt(
            user_id="user123",
            success=False,
            ip_address="192.168.1.1",
            failure_reason="Invalid password"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["success"] is False
        assert log_data["failure_reason"] == "Invalid password"
        assert log_data["level"] == "WARNING"
    
    def test_log_authorization_failure(self):
        """Test logging authorization failure"""
        self.security_logger.log_authorization_failure(
            user_id="user123",
            resource="/admin/users",
            action="DELETE",
            ip_address="192.168.1.1"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event_type"] == "authorization_failure"
        assert log_data["user_id"] == "user123"
        assert log_data["resource"] == "/admin/users"
        assert log_data["action"] == "DELETE"
        assert log_data["level"] == "WARNING"
    
    def test_log_suspicious_activity(self):
        """Test logging suspicious activity"""
        self.security_logger.log_suspicious_activity(
            activity_type="rate_limit_exceeded",
            ip_address="192.168.1.1",
            details={"requests_per_minute": 1000},
            severity="high"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event_type"] == "suspicious_activity"
        assert log_data["activity_type"] == "rate_limit_exceeded"
        assert log_data["severity"] == "high"
        assert log_data["details"]["requests_per_minute"] == 1000
        assert log_data["level"] == "ERROR"
    
    def test_log_data_access(self):
        """Test logging data access"""
        self.security_logger.log_data_access(
            user_id="user123",
            resource_type="user_profile",
            resource_id="profile456",
            action="READ",
            ip_address="192.168.1.1"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event_type"] == "data_access"
        assert log_data["user_id"] == "user123"
        assert log_data["resource_type"] == "user_profile"
        assert log_data["resource_id"] == "profile456"
        assert log_data["action"] == "READ"

class TestSetupStructuredLogging:
    """Test cases for setup_structured_logging function"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
        
        # Clear all loggers
        for logger_name in ['app', 'security', 'performance', 'api', 'database', 'cache']:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.setLevel(logging.NOTSET)
    
    def test_setup_structured_logging_basic(self):
        """Test basic structured logging setup"""
        setup_structured_logging(log_dir=self.temp_dir)
        
        # Check that loggers are created
        app_logger = logging.getLogger('app')
        security_logger = logging.getLogger('security')
        performance_logger = logging.getLogger('performance')
        
        assert app_logger.level == logging.INFO
        assert security_logger.level == logging.INFO
        assert performance_logger.level == logging.INFO
        
        # Check that handlers are added
        assert len(app_logger.handlers) > 0
        assert len(security_logger.handlers) > 0
        assert len(performance_logger.handlers) > 0
    
    def test_setup_with_debug_level(self):
        """Test setup with debug log level"""
        setup_structured_logging(log_dir=self.temp_dir, log_level=logging.DEBUG)
        
        app_logger = logging.getLogger('app')
        assert app_logger.level == logging.DEBUG
    
    def test_log_files_created(self):
        """Test that log files are created"""
        setup_structured_logging(log_dir=self.temp_dir)
        
        # Check that log files exist
        log_files = [
            "app.log", "security.log", "performance.log",
            "api.log", "database.log", "cache.log"
        ]
        
        for log_file in log_files:
            log_path = Path(self.temp_dir) / log_file
            assert log_path.exists()

class TestLoggerGetters:
    """Test cases for logger getter functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        setup_structured_logging(log_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_logger(self):
        """Test get_logger function"""
        logger = get_logger("app")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "app"
    
    def test_get_performance_logger(self):
        """Test get_performance_logger function"""
        perf_logger = get_performance_logger()
        assert isinstance(perf_logger, PerformanceLogger)
    
    def test_get_security_logger(self):
        """Test get_security_logger function"""
        sec_logger = get_security_logger()
        assert isinstance(sec_logger, SecurityLogger)

class TestDecorators:
    """Test cases for logging decorators"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        setup_structured_logging(log_dir=self.temp_dir)
        
        # Capture logs
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(StructuredFormatter())
        
        app_logger = logging.getLogger('app')
        app_logger.addHandler(handler)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
        CorrelationContext.clear()
    
    def test_with_correlation_id_decorator(self):
        """Test with_correlation_id decorator"""
        @with_correlation_id
        def test_function():
            logger = get_logger("app")
            logger.info("Test message")
            return "result"
        
        result = test_function()
        assert result == "result"
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert "correlation_id" in log_data
        assert log_data["correlation_id"] is not None
    
    def test_log_function_call_decorator(self):
        """Test log_function_call decorator"""
        @log_function_call
        def test_function(x, y, z="default"):
            time.sleep(0.01)  # Simulate work
            return x + y
        
        result = test_function(1, 2, z="custom")
        assert result == 3
        
        log_output = self.log_stream.getvalue()
        lines = log_output.strip().split('\n')
        
        # Should have start and end log entries
        assert len(lines) >= 2
        
        start_log = json.loads(lines[0])
        end_log = json.loads(lines[-1])
        
        assert start_log["event"] == "function_start"
        assert start_log["function"] == "test_function"
        assert start_log["args"] == [1, 2]
        assert start_log["kwargs"] == {"z": "custom"}
        
        assert end_log["event"] == "function_end"
        assert end_log["function"] == "test_function"
        assert end_log["result"] == 3
        assert end_log["duration"] > 0
    
    def test_log_function_call_with_exception(self):
        """Test log_function_call decorator with exception"""
        @log_function_call
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        log_output = self.log_stream.getvalue()
        lines = log_output.strip().split('\n')
        
        end_log = json.loads(lines[-1])
        assert end_log["event"] == "function_end"
        assert end_log["success"] is False
        assert "exception" in end_log

class TestAPILogging:
    """Test cases for API logging functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        setup_structured_logging(log_dir=self.temp_dir)
        
        # Capture logs
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(StructuredFormatter())
        
        api_logger = logging.getLogger('api')
        api_logger.addHandler(handler)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_log_api_request(self):
        """Test log_api_request function"""
        log_api_request(
            method="POST",
            path="/api/users",
            user_id="user123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_size=1024
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event"] == "api_request"
        assert log_data["method"] == "POST"
        assert log_data["path"] == "/api/users"
        assert log_data["user_id"] == "user123"
        assert log_data["ip_address"] == "192.168.1.1"
        assert log_data["request_size"] == 1024
    
    def test_log_api_response(self):
        """Test log_api_response function"""
        log_api_response(
            method="GET",
            path="/api/users/123",
            status_code=200,
            response_size=2048,
            duration=0.5,
            user_id="user123"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["event"] == "api_response"
        assert log_data["method"] == "GET"
        assert log_data["path"] == "/api/users/123"
        assert log_data["status_code"] == 200
        assert log_data["response_size"] == 2048
        assert log_data["duration"] == 0.5
        assert log_data["user_id"] == "user123"
    
    def test_log_api_error_response(self):
        """Test logging API error response"""
        log_api_response(
            method="POST",
            path="/api/users",
            status_code=400,
            response_size=256,
            duration=0.1,
            error="Validation failed"
        )
        
        log_output = self.log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["status_code"] == 400
        assert log_data["error"] == "Validation failed"
        assert log_data["level"] == "WARNING"

class TestIntegration:
    """Integration tests for structured logging"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        setup_structured_logging(log_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
        CorrelationContext.clear()
    
    def test_full_logging_pipeline(self):
        """Test complete logging pipeline"""
        # Set correlation context
        CorrelationContext.set_correlation_id("test-correlation-123")
        CorrelationContext.set_request_context({
            "user_id": "user123",
            "session_id": "session456"
        })
        
        # Log API request
        log_api_request(
            method="POST",
            path="/api/chat",
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # Log performance data
        perf_logger = get_performance_logger()
        with perf_logger.time_operation("chat_processing"):
            time.sleep(0.01)  # Simulate work
        
        # Log security event
        sec_logger = get_security_logger()
        sec_logger.log_data_access(
            user_id="user123",
            resource_type="chat_history",
            resource_id="chat789",
            action="READ"
        )
        
        # Log API response
        log_api_response(
            method="POST",
            path="/api/chat",
            status_code=200,
            response_size=1024,
            duration=0.5
        )
        
        # Verify log files contain data
        log_files = ["api.log", "performance.log", "security.log"]
        for log_file in log_files:
            log_path = Path(self.temp_dir) / log_file
            assert log_path.exists()
            assert log_path.stat().st_size > 0
    
    def test_correlation_id_propagation(self):
        """Test correlation ID propagation across different loggers"""
        correlation_id = "test-correlation-456"
        CorrelationContext.set_correlation_id(correlation_id)
        
        # Log to different loggers
        app_logger = get_logger("app")
        app_logger.info("App message")
        
        sec_logger = get_security_logger()
        sec_logger.log_authentication_attempt(
            user_id="user123",
            success=True,
            ip_address="192.168.1.1"
        )
        
        perf_logger = get_performance_logger()
        perf_logger.log_operation_timing("test_operation", 0.1)
        
        # Read log files and verify correlation ID
        log_files = ["app.log", "security.log", "performance.log"]
        for log_file in log_files:
            log_path = Path(self.temp_dir) / log_file
            with open(log_path, 'r') as f:
                log_content = f.read().strip()
                if log_content:  # Only check if file has content
                    log_data = json.loads(log_content.split('\n')[-1])
                    assert log_data.get("correlation_id") == correlation_id

if __name__ == '__main__':
    pytest.main([__file__])