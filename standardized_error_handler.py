# standardized_error_handler.py
"""
Standardized error handling module for the RAG Agent application.
Provides unified error handling, logging, and response formatting.
"""

import logging
import traceback
import functools
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
import json
from flask import jsonify

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for errors."""
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class StandardizedError:
    """Standardized error representation."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    context: Optional[ErrorContext] = None
    timestamp: str = None
    stack_trace: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

class ErrorHandler:
    """Main error handler class."""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history_size = 1000
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        include_stack_trace: bool = False
    ) -> StandardizedError:
        """Handle and standardize an error."""
        
        # Generate unique error ID
        error_id = self._generate_error_id()
        
        # Create standardized error
        standardized_error = StandardizedError(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            details=self._get_error_details(error),
            context=context,
            stack_trace=traceback.format_exc() if include_stack_trace else None
        )
        
        # Log the error
        self._log_error(standardized_error)
        
        # Track error metrics
        self._track_error_metrics(standardized_error)
        
        # Add to history
        self._add_to_history(standardized_error)
        
        return standardized_error
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_error_details(self, error: Exception) -> Optional[str]:
        """Extract additional error details."""
        if hasattr(error, 'details'):
            return error.details
        elif hasattr(error, 'response'):
            return f"Response status: {getattr(error.response, 'status_code', 'unknown')}"
        return None
    
    def _log_error(self, error: StandardizedError):
        """Log the standardized error."""
        log_data = {
            'error_id': error.error_id,
            'category': error.category.value,
            'severity': error.severity.value,
            'error_message': error.message,
            'timestamp': error.timestamp
        }
        
        if error.context:
            log_data.update({
                'endpoint': error.context.endpoint,
                'component': error.context.component,
                'request_id': error.context.request_id
            })
        
        # Choose log level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {error.message}", extra=log_data)
        
        # Log stack trace if available
        if error.stack_trace:
            logger.debug(f"Stack trace for {error.error_id}: {error.stack_trace}")
    
    def _track_error_metrics(self, error: StandardizedError):
        """Track error metrics for monitoring."""
        key = f"{error.category.value}:{error.severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _add_to_history(self, error: StandardizedError):
        """Add error to history (with size limit)."""
        self.error_history.append(error)
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics summary."""
        total_errors = sum(self.error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_counts_by_category_severity': self.error_counts,
            'recent_errors_count': len(self.error_history),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors."""
        return self.error_history[-limit:] if self.error_history else []

# Global error handler instance
error_handler = ErrorHandler()

# Decorators for standardized error handling
def handle_errors(
    category: ErrorCategory = ErrorCategory.INTERNAL,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    include_stack_trace: bool = False,
    return_error_response: bool = True
):
    """Decorator for standardized error handling."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create error context
                error_context = ErrorContext(
                    endpoint=context.get('endpoint') if context else None,
                    component=context.get('component') if context else func.__module__,
                    operation=func.__name__,
                    metadata=context
                )
                
                # Handle the error
                standardized_error = error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context=error_context,
                    include_stack_trace=include_stack_trace
                )
                
                if return_error_response:
                    return _create_error_response(standardized_error)
                else:
                    raise
        return wrapper
    return decorator

def handle_async_errors(
    category: ErrorCategory = ErrorCategory.INTERNAL,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    include_stack_trace: bool = False,
    return_error_response: bool = True
):
    """Decorator for standardized async error handling."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Create error context
                error_context = ErrorContext(
                    endpoint=context.get('endpoint') if context else None,
                    component=context.get('component') if context else func.__module__,
                    operation=func.__name__,
                    metadata=context
                )
                
                # Handle the error
                standardized_error = error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context=error_context,
                    include_stack_trace=include_stack_trace
                )
                
                if return_error_response:
                    response_data, status_code = _create_error_response(standardized_error)
                    return jsonify(response_data), status_code
                else:
                    raise
        return wrapper
    return decorator

def _create_error_response(error: StandardizedError) -> tuple[dict[str, Any], int]:
    """Create standardized error response."""
    response_data = {
        'error': {
            'id': error.error_id,
            'category': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'timestamp': error.timestamp
        }
    }
    
    # Add details if available
    if error.details:
        response_data['error']['details'] = error.details
    
    # Add context if available
    if error.context:
        response_data['error']['context'] = {
            'endpoint': error.context.endpoint,
            'component': error.context.component,
            'operation': error.context.operation
        }
    
    # Determine HTTP status code based on category
    status_code = _get_http_status_code(error.category)
    
    return response_data, status_code

def _get_http_status_code(category: ErrorCategory) -> int:
    """Map error category to HTTP status code."""
    mapping = {
        ErrorCategory.VALIDATION: 400,
        ErrorCategory.AUTHENTICATION: 401,
        ErrorCategory.AUTHORIZATION: 403,
        ErrorCategory.NOT_FOUND: 404,
        ErrorCategory.RATE_LIMIT: 429,
        ErrorCategory.TIMEOUT: 408,
        ErrorCategory.NETWORK: 502,
        ErrorCategory.EXTERNAL_SERVICE: 502,
        ErrorCategory.DATABASE: 503,
        ErrorCategory.CONFIGURATION: 500,
        ErrorCategory.INTERNAL: 500,
        ErrorCategory.UNKNOWN: 500
    }
    return mapping.get(category, 500)

# Utility functions for common error scenarios
def handle_validation_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> StandardizedError:
    """Handle validation errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        context=ErrorContext(**context) if context else None
    )

def handle_authentication_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> StandardizedError:
    """Handle authentication errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        context=ErrorContext(**context) if context else None
    )

def handle_network_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> StandardizedError:
    """Handle network errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        context=ErrorContext(**context) if context else None
    )

def handle_database_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> StandardizedError:
    """Handle database errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        context=ErrorContext(**context) if context else None,
        include_stack_trace=True
    )

def handle_external_service_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> StandardizedError:
    """Handle external service errors."""
    return error_handler.handle_error(
        error=error,
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        context=ErrorContext(**context) if context else None
    )

# Error monitoring and alerting
class ErrorMonitor:
    """Monitor error patterns and trigger alerts."""
    
    def __init__(self, error_threshold: int = 10, time_window_minutes: int = 5):
        self.error_threshold = error_threshold
        self.time_window_minutes = time_window_minutes
        self.alerts_sent = set()
    
    def check_error_thresholds(self) -> Dict[str, Any]:
        """Check if error thresholds are exceeded."""
        now = datetime.now(timezone.utc)
        time_threshold = now.timestamp() - (self.time_window_minutes * 60)
        
        # Count recent errors by category
        recent_errors = [
            error for error in error_handler.error_history
            if datetime.fromisoformat(error.timestamp).timestamp() > time_threshold
        ]
        
        category_counts = {}
        for error in recent_errors:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Check thresholds
        alerts = []
        for category, count in category_counts.items():
            if count >= self.error_threshold:
                alert_key = f"{category}:{now.minute // self.time_window_minutes}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        'category': category,
                        'count': count,
                        'threshold': self.error_threshold,
                        'time_window_minutes': self.time_window_minutes
                    })
                    self.alerts_sent.add(alert_key)
        
        return {
            'total_recent_errors': len(recent_errors),
            'category_counts': category_counts,
            'alerts': alerts,
            'timestamp': now.isoformat()
        }

# Global error monitor instance
error_monitor = ErrorMonitor()

# Export main components
__all__ = [
    'ErrorSeverity', 'ErrorCategory', 'ErrorContext', 'StandardizedError',
    'ErrorHandler', 'error_handler', 'handle_errors', 'handle_async_errors',
    'handle_validation_error', 'handle_authentication_error', 'handle_network_error',
    'handle_database_error', 'handle_external_service_error',
    'ErrorMonitor', 'error_monitor'
]
