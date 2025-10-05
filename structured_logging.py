"""
Structured Logging System with Correlation IDs and Enhanced Formatting
"""

import logging
import json
import time
import uuid
import threading
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from functools import wraps
import traceback
import os
from pathlib import Path

# Thread-local storage for correlation context
_context = threading.local()


class SimpleFileHandler(logging.Handler):
    """A simple file handler that opens the file on each emit and closes it.

    This avoids keeping file descriptors open which can prevent deletion on
    Windows during tests that remove temporary directories.
    """
    def __init__(self, filepath: Union[str, Path], formatter: Optional[logging.Formatter] = None):
        super().__init__()
        self.filepath = str(filepath)
        if formatter:
            self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            # Open, append, and close on each emit
            with open(self.filepath, 'a', encoding='utf-8') as fh:
                fh.write(msg + "\n")
        except Exception:
            self.handleError(record)

class CorrelationContext:
    """Manages correlation IDs and request context across threads"""
    
    @staticmethod
    def set_correlation_id(correlation_id: str):
        """Set correlation ID for current thread"""
        _context.correlation_id = correlation_id
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get correlation ID for current thread"""
        return getattr(_context, 'correlation_id', None)
    
    @staticmethod
    def set_user_id(user_id: str):
        """Set user ID for current thread"""
        _context.user_id = user_id
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get user ID for current thread"""
        return getattr(_context, 'user_id', None)
    
    @staticmethod
    def set_request_context(context: Dict[str, Any]):
        """Set additional request context"""
        _context.request_context = context
    
    @staticmethod
    def update_request_context(update: Dict[str, Any]):
        """Update existing request context with values from update dict"""
        existing = getattr(_context, 'request_context', {}) or {}
        existing.update(update or {})
        _context.request_context = existing
    
    @staticmethod
    def get_request_context() -> Dict[str, Any]:
        """Get request context"""
        return getattr(_context, 'request_context', {})
    
    @staticmethod
    def clear():
        """Clear all context for current thread"""
        for attr in ['correlation_id', 'user_id', 'request_context']:
            if hasattr(_context, attr):
                delattr(_context, attr)

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add correlation context
        correlation_id = CorrelationContext.get_correlation_id()
        if correlation_id:
            log_entry['correlation_id'] = correlation_id
        
        user_id = CorrelationContext.get_user_id()
        if user_id:
            log_entry['user_id'] = user_id
        
        request_context = CorrelationContext.get_request_context()
        if request_context:
            log_entry['request_context'] = request_context
        
        # Add exception information if present
        if record.exc_info:
            try:
                if isinstance(record.exc_info, tuple) and record.exc_info[0]:
                    tb = ''.join(traceback.format_exception(*record.exc_info))
                elif record.exc_info is True and sys.exc_info()[0]:
                    tb = ''.join(traceback.format_exception(*sys.exc_info()))
                else:
                    tb = '<no-active-exception>'
            except Exception:
                tb = '<exception-formatting-failed>'

            # Provide exception as a string for easier assertions
            log_entry['exception'] = tb
        
        # Add extra fields from the log record
        if self.include_extra_fields:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'getMessage', 'exc_info', 
                              'exc_text', 'stack_info']:
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            # Merge extra fields at top-level so tests can access them directly
            for k, v in extra_fields.items():
                # Map special internal keys used by decorators to avoid
                # colliding with LogRecord internals (e.g. 'args'). Tests
                # expect 'args' and 'kwargs' in the final JSON, so we map
                # our internal names back to those keys here.
                out_key = k
                if k == '_args':
                    out_key = 'args'
                if k == '_kwargs':
                    out_key = 'kwargs'
                # Allow extra 'function' field to override record.funcName
                if out_key == 'function':
                    log_entry['function'] = v
                    continue

                # avoid overwriting other core keys
                if out_key not in log_entry:
                    log_entry[out_key] = v
        
        return json.dumps(log_entry, ensure_ascii=False)

class PerformanceLogger:
    """Logger for performance metrics and timing"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    @contextmanager
    def time_operation(self, operation_name: str, details: Optional[Dict[str, Any]] = None):
        """Context manager to time operations"""
        start_time = time.time()
        correlation_id = CorrelationContext.get_correlation_id()
        # Start log is emitted at DEBUG so tests that capture INFO only will
        # receive a single JSON record (the completed/failed entry).
        self.logger.debug(
            f"Starting operation: {operation_name}",
            extra={
                'event': 'operation_start',
                'operation': operation_name,
                'operation_status': 'started',
                'correlation_id': correlation_id,
                'details': details or {}
            }
        )
        
        try:
            yield
            duration = time.time() - start_time
            self.logger.info(
                f"Completed operation: {operation_name}",
                extra={
                    'event': 'operation_timing',
                    'operation': operation_name,
                    'duration': duration,
                    'details': details or {},
                    'correlation_id': correlation_id
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Failed operation: {operation_name}",
                extra={
                    'event': 'operation_timing',
                    'operation': operation_name,
                    'duration': duration,
                    'error': str(e),
                    'success': False,
                    'details': details or {},
                    'correlation_id': correlation_id
                },
                exc_info=True
            )
            raise

    def log_operation_timing(self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None):
        """Log a single timing metric for an operation"""
        self.logger.info(
            f"Operation timing: {operation}",
            extra={
                'event': 'operation_timing',
                'operation': operation,
                'duration': duration,
                'details': details or {}
            }
        )

    def log_slow_operation(self, operation: str, duration: float, threshold: float, details: Optional[Dict[str, Any]] = None):
        """Log when an operation is slower than a threshold"""
        level = self.logger.warning if duration >= threshold else self.logger.info
        level(
            f"Slow operation: {operation}",
            extra={
                'event': 'slow_operation',
                'operation': operation,
                'duration': duration,
                'threshold': threshold,
                'details': details or {}
            }
        )

class SecurityLogger:
    """Logger for security-related events"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str, **kwargs):
        """Log authentication attempts"""
        level = self.logger.info if success else self.logger.warning
        level(
            f"Authentication {'successful' if success else 'failed'} for user {user_id}",
            extra={
                'event_type': 'authentication_attempt',
                'user_id': user_id,
                'success': success,
                'ip_address': ip_address,
                'correlation_id': CorrelationContext.get_correlation_id(),
                **kwargs
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, **kwargs):
        """Log authorization failures"""
        self.logger.warning(
            f"Authorization failed for user {user_id} accessing {resource} with action {action}",
            extra={
                'event_type': 'authorization_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'correlation_id': CorrelationContext.get_correlation_id(),
                **kwargs
            }
        )
    
    def log_suspicious_activity(self, activity_type: str, ip_address: str = None, details: Optional[Dict[str, Any]] = None, severity: str = 'medium', **kwargs):
        """Log suspicious activities"""
        level = self.logger.error if severity.lower() in ('high', 'critical') else (self.logger.warning if severity.lower() == 'medium' else self.logger.info)
        level(
            f"Suspicious activity detected: {activity_type}",
            extra={
                'event_type': 'suspicious_activity',
                'activity_type': activity_type,
                'severity': severity,
                'details': details or {},
                'ip_address': ip_address,
                'correlation_id': CorrelationContext.get_correlation_id(),
                **kwargs
            }
        )



    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, action: str, ip_address: Optional[str] = None, **kwargs):
        """Log data access events"""
        self.logger.info(
            f"Data access: {user_id} {action} {resource_type}/{resource_id}",
            extra={
                'event_type': 'data_access',
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'ip_address': ip_address,
                'correlation_id': CorrelationContext.get_correlation_id(),
                **kwargs
            }
        )

def setup_structured_logging(
    app_name: str = "rag_agent",
    log_level: Union[str, int] = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> Dict[str, logging.Logger]:
    """
    Setup structured logging configuration
    
    Returns:
        Dictionary of configured loggers
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    # Allow log_level to be passed as int or string
    if isinstance(log_level, int):
        root_logger.setLevel(log_level)
    else:
        root_logger.setLevel(getattr(logging, str(log_level).upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter()
    
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # File handlers
    if enable_file:
        # Create all handlers at once with consistent naming
        log_types = ['app', 'security', 'performance', 'api', 'database', 'cache']
        file_handlers = {}
        
        for log_type in log_types:
            log_file = log_path / f"{log_type}.log"
            # Ensure file exists for tests
            log_file.touch(exist_ok=True)
            # Create handler
            handler = SimpleFileHandler(log_file, formatter=formatter)
            file_handlers[log_type] = handler
            handlers.append(handler)
    
    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Create specialized loggers with simple names (tests expect these exact names)
    loggers = {
        'app': logging.getLogger('app'),
        'security': logging.getLogger('security'),
        'performance': logging.getLogger('performance'),
        'api': logging.getLogger('api'),
        'database': logging.getLogger('database'),
        'cache': logging.getLogger('cache'),
    }

    # Attach file handlers to corresponding loggers when file logging enabled
    if enable_file:
        # Use file_handlers dictionary created earlier
        mapping = file_handlers

        for name, logger in loggers.items():
            logger.setLevel(root_logger.level)
            logger.handlers = []
            logger.addHandler(mapping[name])
    
    return loggers

def with_correlation_id(func):
    """Decorator to automatically generate correlation ID for functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Generate correlation ID if not present
        if not CorrelationContext.get_correlation_id():
            CorrelationContext.set_correlation_id(str(uuid.uuid4()))

        try:
            return func(*args, **kwargs)
        finally:
            # Don't clear context here as it might be needed by other operations
            pass

    return wrapper

def log_function_call(_func=None, *, include_args: bool = True, include_result: bool = True):
    """Decorator to log function calls with timing.

    Can be used with or without parameters:
      @log_function_call
      @log_function_call(include_args=False)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('app')
            start_time = time.time()
            func_name = func.__name__

            # Log function start with correct name
            start_extra = {
                'event': 'function_start',
                'function': func_name,  # Use function key directly
                '_args': list(args) if include_args else [],
                '_kwargs': kwargs if include_args else {},
            }
            logger.info(f"Function start: {func_name}", extra=start_extra)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                end_extra = {
                    'event': 'function_end',
                    'function': func_name,
                    'result': result if include_result else None,
                    'duration': duration,
                    'success': True
                }
                logger.info(f"Function end: {func_name}", extra=end_extra)
                return result
            except Exception as e:
                duration = time.time() - start_time
                end_extra = {
                    'event': 'function_end',
                    'function': func_name,
                    'duration': duration,
                    'success': False,
                    'exception': str(e)
                }
                logger.error(f"Function failed: {func_name}", extra=end_extra, exc_info=True)
                raise

        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)

# Global logger instances
_loggers = None

def get_logger(name: str = 'app') -> logging.Logger:
    """Get a configured logger instance by simple name (e.g., 'app')."""
    global _loggers
    if _loggers is None:
        _loggers = setup_structured_logging()

    # Return the pre-created named logger if available
    return _loggers.get(name, logging.getLogger(name))

def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    return PerformanceLogger(get_logger('performance'))

def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return SecurityLogger(get_logger('security'))

# Convenience functions
def log_api_request(method: str, path: str, user_id: str = None, ip_address: str = None, **kwargs):
    """Log API request (test expects signature: method, path, ...)"""
    logger = get_logger('api')
    logger.info(
        f"API request: {method} {path}",
        extra={
            'event': 'api_request',
            'method': method,
            'path': path,
            'user_id': user_id,
            'ip_address': ip_address,
            'correlation_id': CorrelationContext.get_correlation_id(),
            **kwargs
        }
    )

def log_api_response(method: str, path: str, status_code: int, response_size: int = None, duration: float = 0.0, user_id: str = None, error: str = None, **kwargs):
    """Log API response (test expects signature and keys like 'event' and 'path')"""
    logger = get_logger('api')
    level = logger.info if status_code < 400 else logger.warning
    extra = {
        'event': 'api_response',
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration': duration,
        'response_size': response_size,
        'user_id': user_id,
        'correlation_id': CorrelationContext.get_correlation_id(),
        **({} if error is None else {'error': error}),
        **kwargs
    }

    level(f"API response: {method} {path} - {status_code}", extra=extra)