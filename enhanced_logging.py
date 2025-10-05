# enhanced_logging.py
"""
Enhanced logging and monitoring system for the RAG Agent application.
Provides comprehensive logging, monitoring, and observability capabilities.
"""

import logging
import logging.handlers
import json
import time
import threading
import traceback
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from enum import Enum
import uuid
import psutil
import os
from contextlib import contextmanager
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity
)

class LogLevel(Enum):
    """Enhanced log levels."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"

class LogCategory(Enum):
    """Log categories for better organization."""
    APPLICATION = "APPLICATION"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    AUDIT = "AUDIT"
    ERROR = "ERROR"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    USER_ACTION = "USER_ACTION"
    SYSTEM = "SYSTEM"

@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    component: str
    operation: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[Dict[str, Any]] = None
    system_info: Optional[Dict[str, Any]] = None

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created, timezone.utc),
            level=LogLevel(record.levelname),
            category=LogCategory(getattr(record, 'category', LogCategory.APPLICATION).value),
            message=record.getMessage(),
            component=getattr(record, 'component', 'unknown'),
            operation=getattr(record, 'operation', 'unknown'),
            request_id=getattr(record, 'request_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            correlation_id=getattr(record, 'correlation_id', None),
            duration_ms=getattr(record, 'duration_ms', None),
            metadata=getattr(record, 'metadata', {}),
            exception_info=self._format_exception(record) if record.exc_info else None,
            system_info=self._get_system_info() if getattr(record, 'include_system_info', False) else None
        )
        
        return json.dumps(asdict(log_entry), default=str, ensure_ascii=False)
    
    def _format_exception(self, record):
        """Format exception information."""
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            return {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            }
        return None
    
    def _get_system_info(self):
        """Get current system information."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
                "thread_count": threading.active_count()
            }
        except Exception:
            return {"error": "Failed to get system info"}

class LogAggregator:
    """Aggregates and manages log entries."""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.entries: List[LogEntry] = []
        self._lock = threading.RLock()
        self.metrics = {
            "total_logs": 0,
            "logs_by_level": {level.value: 0 for level in LogLevel},
            "logs_by_category": {category.value: 0 for category in LogCategory},
            "errors_per_hour": [],
            "performance_issues": []
        }
        
        logger = logging.getLogger(__name__)
        logger.info("LogAggregator initialized")
    
    def add_entry(self, entry: LogEntry):
        """Add a log entry to the aggregator."""
        with self._lock:
            self.entries.append(entry)
            
            # Maintain max entries limit
            if len(self.entries) > self.max_entries:
                self.entries.pop(0)
            
            # Update metrics
            self.metrics["total_logs"] += 1
            self.metrics["logs_by_level"][entry.level.value] += 1
            self.metrics["logs_by_category"][entry.category.value] += 1
            
            # Track errors
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self._track_error(entry)
            
            # Track performance issues
            if entry.category == LogCategory.PERFORMANCE and entry.duration_ms and entry.duration_ms > 1000:
                self._track_performance_issue(entry)
    
    def _track_error(self, entry: LogEntry):
        """Track error patterns."""
        current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
        # Find or create hour entry
        hour_entry = None
        for error_hour in self.metrics["errors_per_hour"]:
            if error_hour["hour"] == current_hour.isoformat():
                hour_entry = error_hour
                break
        
        if not hour_entry:
            hour_entry = {
                "hour": current_hour.isoformat(),
                "count": 0,
                "components": {}
            }
            self.metrics["errors_per_hour"].append(hour_entry)
        
        hour_entry["count"] += 1
        if entry.component not in hour_entry["components"]:
            hour_entry["components"][entry.component] = 0
        hour_entry["components"][entry.component] += 1
    
    def _track_performance_issue(self, entry: LogEntry):
        """Track performance issues."""
        self.metrics["performance_issues"].append({
            "timestamp": entry.timestamp.isoformat(),
            "component": entry.component,
            "operation": entry.operation,
            "duration_ms": entry.duration_ms,
            "message": entry.message
        })
        
        # Keep only last 100 performance issues
        if len(self.metrics["performance_issues"]) > 100:
            self.metrics["performance_issues"].pop(0)
    
    def get_recent_entries(self, minutes: int = 60, level: Optional[LogLevel] = None, category: Optional[LogCategory] = None) -> List[LogEntry]:
        """Get recent log entries with optional filtering."""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=minutes)
            
            filtered_entries = []
            for entry in reversed(self.entries):  # Most recent first
                if entry.timestamp < cutoff_time:
                    break
                
                if level and entry.level != level:
                    continue
                
                if category and entry.category != category:
                    continue
                
                filtered_entries.append(entry)
            
            return filtered_entries
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics."""
        with self._lock:
            return self.metrics.copy()

class EnhancedLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str, aggregator: Optional[LogAggregator] = None):
        self.name = name
        self.aggregator = aggregator
        self.logger = logging.getLogger(name)
        self._context = threading.local()
        
        # Set default context
        self._context.request_id = None
        self._context.user_id = None
        self._context.session_id = None
        self._context.correlation_id = None
    
    def set_context(self, request_id: Optional[str] = None, user_id: Optional[str] = None, 
                   session_id: Optional[str] = None, correlation_id: Optional[str] = None):
        """Set logging context for current thread."""
        if request_id is not None:
            self._context.request_id = request_id
        if user_id is not None:
            self._context.user_id = user_id
        if session_id is not None:
            self._context.session_id = session_id
        if correlation_id is not None:
            self._context.correlation_id = correlation_id
    
    def clear_context(self):
        """Clear logging context."""
        self._context.request_id = None
        self._context.user_id = None
        self._context.session_id = None
        self._context.correlation_id = None
    
    def _log(self, level: LogLevel, category: LogCategory, message: str, 
             component: str, operation: str, duration_ms: Optional[float] = None,
             metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Internal logging method."""
        # Create structured log entry
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            category=category,
            message=message,
            component=component,
            operation=operation,
            request_id=getattr(self._context, 'request_id', None),
            user_id=getattr(self._context, 'user_id', None),
            session_id=getattr(self._context, 'session_id', None),
            correlation_id=getattr(self._context, 'correlation_id', None),
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        # Add to aggregator if available
        if self.aggregator:
            self.aggregator.add_entry(entry)
        
        # Log to standard logger
        extra = {
            'category': category,
            'component': component,
            'operation': operation,
            'request_id': entry.request_id,
            'user_id': entry.user_id,
            'session_id': entry.session_id,
            'correlation_id': entry.correlation_id,
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        }
        
        self.logger.log(getattr(logging, level.value), message, extra=extra, exc_info=exc_info)
    
    def trace(self, message: str, component: str = None, operation: str = "trace", **kwargs):
        """Log trace message."""
        self._log(LogLevel.TRACE, LogCategory.APPLICATION, message, 
                 component or self.name, operation, **kwargs)
    
    def debug(self, message: str, component: str = None, operation: str = "debug", **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, LogCategory.APPLICATION, message, 
                 component or self.name, operation, **kwargs)
    
    def info(self, message: str, component: str = None, operation: str = "info", **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, LogCategory.APPLICATION, message, 
                 component or self.name, operation, **kwargs)
    
    def warning(self, message: str, component: str = None, operation: str = "warning", **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, LogCategory.APPLICATION, message, 
                 component or self.name, operation, **kwargs)
    
    def error(self, message: str, component: str = None, operation: str = "error", **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, LogCategory.ERROR, message, 
                 component or self.name, operation, exc_info=True, **kwargs)
    
    def critical(self, message: str, component: str = None, operation: str = "critical", **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, LogCategory.ERROR, message, 
                 component or self.name, operation, exc_info=True, **kwargs)
    
    def audit(self, message: str, component: str = None, operation: str = "audit", **kwargs):
        """Log audit message."""
        self._log(LogLevel.AUDIT, LogCategory.AUDIT, message, 
                 component or self.name, operation, **kwargs)
    
    def security(self, message: str, component: str = None, operation: str = "security", **kwargs):
        """Log security message."""
        self._log(LogLevel.SECURITY, LogCategory.SECURITY, message, 
                 component or self.name, operation, **kwargs)
    
    def performance(self, message: str, duration_ms: float, component: str = None, operation: str = "performance", **kwargs):
        """Log performance message."""
        self._log(LogLevel.PERFORMANCE, LogCategory.PERFORMANCE, message, 
                 component or self.name, operation, duration_ms=duration_ms, **kwargs)
    
    def user_action(self, action: str, component: str = None, operation: str = "user_action", **kwargs):
        """Log user action."""
        self._log(LogLevel.INFO, LogCategory.USER_ACTION, f"User action: {action}", 
                 component or self.name, operation, **kwargs)
    
    def database_operation(self, operation: str, duration_ms: Optional[float] = None, 
                          component: str = None, **kwargs):
        """Log database operation."""
        self._log(LogLevel.INFO, LogCategory.DATABASE, f"Database operation: {operation}", 
                 component or self.name, operation, duration_ms=duration_ms, **kwargs)
    
    def network_request(self, method: str, url: str, status_code: int, duration_ms: Optional[float] = None,
                       component: str = None, **kwargs):
        """Log network request."""
        message = f"Network request: {method} {url} -> {status_code}"
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'method': method,
            'url': url,
            'status_code': status_code
        })
        kwargs['metadata'] = metadata
        
        self._log(LogLevel.INFO, LogCategory.NETWORK, message, 
                 component or self.name, "network_request", duration_ms=duration_ms, **kwargs)

class LoggingManager:
    """Centralized logging manager."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.aggregator = LogAggregator()
        self.loggers: Dict[str, EnhancedLogger] = {}
        self._setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("LoggingManager initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default logging configuration."""
        return {
            "log_level": "INFO",
            "log_directory": "logs",
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
            "enable_console": True,
            "enable_file": True,
            "enable_json": True,
            "enable_rotation": True,
            "log_categories": {
                "application": "INFO",
                "security": "WARNING",
                "performance": "INFO",
                "audit": "INFO",
                "error": "ERROR",
                "database": "INFO",
                "network": "INFO",
                "user_action": "INFO",
                "system": "INFO"
            }
        }
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create log directory
        log_dir = Path(self.config["log_directory"])
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config["log_level"]))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.config["enable_console"]:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handlers
        if self.config["enable_file"]:
            # Main application log
            app_handler = logging.handlers.RotatingFileHandler(
                log_dir / "rag_agent.log",
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"]
            )
            app_handler.setLevel(logging.INFO)
            
            if self.config["enable_json"]:
                app_handler.setFormatter(StructuredFormatter())
            else:
                app_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                app_handler.setFormatter(app_formatter)
            
            root_logger.addHandler(app_handler)
            
            # Error log
            error_handler = logging.handlers.RotatingFileHandler(
                log_dir / "rag_agent_errors.log",
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"]
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(error_handler)
            
            # Security log
            security_handler = logging.handlers.RotatingFileHandler(
                log_dir / "rag_agent_security.log",
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"]
            )
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(security_handler)
            
            # Performance log
            perf_handler = logging.handlers.RotatingFileHandler(
                log_dir / "rag_agent_performance.log",
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"]
            )
            perf_handler.setLevel(logging.INFO)
            perf_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(perf_handler)
    
    def get_logger(self, name: str) -> EnhancedLogger:
        """Get or create an enhanced logger."""
        if name not in self.loggers:
            self.loggers[name] = EnhancedLogger(name, self.aggregator)
        return self.loggers[name]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics."""
        return self.aggregator.get_metrics()
    
    def get_recent_logs(self, minutes: int = 60, level: Optional[LogLevel] = None, 
                       category: Optional[LogCategory] = None) -> List[LogEntry]:
        """Get recent log entries."""
        return self.aggregator.get_recent_entries(minutes, level, category)

# Global logging manager
_logging_manager = None

def get_logging_manager() -> LoggingManager:
    """Get or create global logging manager."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager

def get_enhanced_logger(name: str) -> EnhancedLogger:
    """Get or create an enhanced logger."""
    return get_logging_manager().get_logger(name)

# Context managers for logging
@contextmanager
def log_context(request_id: Optional[str] = None, user_id: Optional[str] = None,
               session_id: Optional[str] = None, correlation_id: Optional[str] = None):
    """Context manager for setting logging context."""
    logger = get_enhanced_logger(__name__)
    logger.set_context(request_id, user_id, session_id, correlation_id)
    try:
        yield logger
    finally:
        logger.clear_context()

@contextmanager
def performance_logging(operation: str, component: str, logger: Optional[EnhancedLogger] = None):
    """Context manager for performance logging."""
    if logger is None:
        logger = get_enhanced_logger(component)
    
    start_time = time.time()
    logger.info(f"Starting {operation}", component=component, operation=operation)
    
    try:
        yield logger
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Failed {operation}: {str(e)}", component=component, 
                    operation=operation, duration_ms=duration_ms)
        raise
    else:
        duration_ms = (time.time() - start_time) * 1000
        logger.performance(f"Completed {operation}", duration_ms, 
                          component=component, operation=operation)

# Decorators for automatic logging
def log_function_call(level: LogLevel = LogLevel.DEBUG, component: Optional[str] = None):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_enhanced_logger(component or func.__module__)
            logger._log(level, LogCategory.APPLICATION, f"Calling {func.__name__}", 
                       component or func.__module__, func.__name__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.performance(f"Completed {func.__name__}", duration_ms, 
                                 component or func.__module__, func.__name__)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Failed {func.__name__}: {str(e)}", 
                           component or func.__module__, func.__name__, 
                           duration_ms=duration_ms)
                raise
        
        return wrapper
    return decorator

def log_user_action(action: str, component: Optional[str] = None):
    """Decorator to log user actions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_enhanced_logger(component or func.__module__)
            logger.user_action(f"{action} via {func.__name__}", 
                             component or func.__module__, func.__name__)
            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the enhanced logging system
    print("📝 Enhanced Logging Test")
    print("=" * 50)
    
    # Initialize logging manager
    logging_manager = get_logging_manager()
    
    # Get logger
    logger = get_enhanced_logger("test_module")
    
    # Test different log levels and categories
    print("Testing log levels and categories...")
    
    logger.info("Application started", component="main", operation="startup")
    logger.warning("Configuration warning", component="config", operation="load")
    logger.error("Sample error", component="test", operation="error_test")
    logger.security("Security event detected", component="auth", operation="login_attempt")
    logger.audit("User action logged", component="audit", operation="user_action")
    logger.performance("Operation completed", 150.5, component="performance", operation="test_op")
    logger.user_action("Button clicked", component="ui", operation="button_click")
    logger.database_operation("SELECT query", 25.3, component="db", operation="query")
    logger.network_request("GET", "https://api.example.com", 200, 100.2, component="api")
    
    # Test context manager
    print("\nTesting context manager...")
    with log_context(request_id="req-123", user_id="user-456") as ctx_logger:
        ctx_logger.info("Contextual log message", component="context_test")
    
    # Test performance logging
    print("\nTesting performance logging...")
    with performance_logging("test_operation", "test_component") as perf_logger:
        time.sleep(0.1)  # Simulate work
        perf_logger.info("Working...", component="test_component")
    
    # Test decorator
    print("\nTesting decorators...")
    
    @log_function_call(LogLevel.INFO, "decorator_test")
    def sample_function():
        time.sleep(0.05)
        return "success"
    
    @log_user_action("test_action", "decorator_test")
    def user_action_function():
        return "action_completed"
    
    result1 = sample_function()
    result2 = user_action_function()
    
    # Get metrics
    print("\nLogging metrics:")
    metrics = logging_manager.get_metrics()
    print(f"Total logs: {metrics['total_logs']}")
    print(f"Logs by level: {metrics['logs_by_level']}")
    print(f"Logs by category: {metrics['logs_by_category']}")
    
    # Get recent logs
    print("\nRecent logs:")
    recent_logs = logging_manager.get_recent_logs(minutes=1)
    for log in recent_logs[-5:]:  # Show last 5 logs
        print(f"  {log.timestamp.strftime('%H:%M:%S')} - {log.level.value} - {log.message}")
    
    print("\n✅ Enhanced logging test completed")
