# health_checks.py
"""
Health check system for monitoring application status and dependencies.
"""

import time
import logging
import asyncio
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import requests
from pathlib import Path
from standardized_error_handler import (
    handle_errors, handle_async_errors, ErrorCategory, ErrorSeverity,
    handle_network_error, handle_database_error
)

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class BaseHealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
    
    @handle_async_errors(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.LOW,
        context={'component': 'health_checks', 'operation': 'check'},
        return_error_response=False
    )
    async def check(self) -> HealthCheckResult:
        """Perform the health check."""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            status, message, details = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=timestamp,
                details=details
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                duration_ms=duration_ms,
                timestamp=timestamp
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=timestamp
            )
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Optional[Dict[str, Any]]]:
        """Override this method to implement the actual health check."""
        raise NotImplementedError

class SystemResourcesHealthCheck(BaseHealthCheck):
    """Check system resources (CPU, memory, disk)."""
    
    def __init__(self, 
                 cpu_threshold: float = 90.0,
                 memory_threshold: float = 90.0,
                 disk_threshold: float = 90.0):
        super().__init__("system_resources")
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Optional[Dict[str, Any]]]:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        details = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3)
        }
        
        issues = []
        
        if cpu_percent > self.cpu_threshold:
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory.percent > self.memory_threshold:
            issues.append(f"High memory usage: {memory.percent:.1f}%")
        
        if disk.percent > self.disk_threshold:
            issues.append(f"High disk usage: {disk.percent:.1f}%")
        
        if issues:
            status = HealthStatus.DEGRADED if len(issues) == 1 else HealthStatus.UNHEALTHY
            message = "; ".join(issues)
        else:
            status = HealthStatus.HEALTHY
            message = "System resources are healthy"
        
        return status, message, details

class DatabaseHealthCheck(BaseHealthCheck):
    """Check database connectivity and performance."""
    
    def __init__(self, connection_string: str = None):
        super().__init__("database")
        self.connection_string = connection_string
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Optional[Dict[str, Any]]]:
        # For this implementation, we'll check if FAISS index files exist
        faiss_files = [
            "outlook_index.faiss",
            "metadata.json"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_name in faiss_files:
            file_path = Path(file_name)
            if file_path.exists():
                existing_files.append({
                    'name': file_name,
                    'size_mb': file_path.stat().st_size / (1024**2),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            else:
                missing_files.append(file_name)
        
        details = {
            'existing_files': existing_files,
            'missing_files': missing_files
        }
        
        if missing_files:
            status = HealthStatus.DEGRADED
            message = f"Missing database files: {', '.join(missing_files)}"
        else:
            status = HealthStatus.HEALTHY
            message = "Database files are accessible"
        
        return status, message, details

class ExternalServiceHealthCheck(BaseHealthCheck):
    """Check external service connectivity."""
    
    def __init__(self, service_name: str, url: str, expected_status: int = 200):
        super().__init__(f"external_service_{service_name}")
        self.service_name = service_name
        self.url = url
        self.expected_status = expected_status
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Optional[Dict[str, Any]]]:
        try:
            response = requests.get(self.url, timeout=self.timeout)
            
            details = {
                'url': self.url,
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'headers': dict(response.headers)
            }
            
            if response.status_code == self.expected_status:
                status = HealthStatus.HEALTHY
                message = f"{self.service_name} is accessible"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{self.service_name} returned status {response.status_code}"
            
            return status, message, details
            
        except requests.exceptions.Timeout:
            handle_network_error(
                Exception(f"{self.service_name} request timed out"),
                {'component': 'health_checks', 'service': self.service_name, 'url': self.url}
            )
            return HealthStatus.UNHEALTHY, f"{self.service_name} request timed out", None
        except requests.exceptions.ConnectionError:
            handle_network_error(
                Exception(f"Cannot connect to {self.service_name}"),
                {'component': 'health_checks', 'service': self.service_name, 'url': self.url}
            )
            return HealthStatus.UNHEALTHY, f"Cannot connect to {self.service_name}", None
        except Exception as e:
            handle_network_error(
                e,
                {'component': 'health_checks', 'service': self.service_name, 'url': self.url}
            )
            return HealthStatus.UNHEALTHY, f"{self.service_name} check failed: {str(e)}", None

class ApplicationHealthCheck(BaseHealthCheck):
    """Check application-specific health metrics."""
    
    def __init__(self, app_context=None):
        super().__init__("application")
        self.app_context = app_context
    
    async def _perform_check(self) -> tuple[HealthStatus, str, Optional[Dict[str, Any]]]:
        details = {}
        issues = []
        
        # Check if critical components are initialized
        if self.app_context:
            if not hasattr(self.app_context, 'reasoner'):
                issues.append("Reasoner not initialized")
            
            if not hasattr(self.app_context, 'retriever'):
                issues.append("Retriever not initialized")
        
        # Check log file accessibility
        log_file = Path("agent_bridge.log")
        if log_file.exists():
            details['log_file_size_mb'] = log_file.stat().st_size / (1024**2)
        else:
            issues.append("Log file not accessible")
        
        # Check cache directory
        cache_dir = Path("cache")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.cache"))
            details['cache_files_count'] = len(cache_files)
        
        # Check for error patterns in recent logs
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    recent_lines = f.readlines()[-100:]  # Last 100 lines
                
                error_count = sum(1 for line in recent_lines if 'ERROR' in line)
                warning_count = sum(1 for line in recent_lines if 'WARNING' in line)
                
                details['recent_errors'] = error_count
                details['recent_warnings'] = warning_count
                
                if error_count > 10:
                    issues.append(f"High error rate: {error_count} errors in recent logs")
                elif error_count > 5:
                    issues.append(f"Moderate error rate: {error_count} errors in recent logs")
        
        except Exception as e:
            issues.append(f"Cannot read log file: {str(e)}")
        
        if issues:
            status = HealthStatus.DEGRADED if len(issues) <= 2 else HealthStatus.UNHEALTHY
            message = "; ".join(issues)
        else:
            status = HealthStatus.HEALTHY
            message = "Application is healthy"
        
        return status, message, details

class HealthCheckManager:
    """Manage and execute health checks."""
    
    def __init__(self):
        self.checks: List[BaseHealthCheck] = []
        self.last_results: Dict[str, HealthCheckResult] = {}
    
    def add_check(self, health_check: BaseHealthCheck):
        """Add a health check."""
        self.checks.append(health_check)
    
    def remove_check(self, name: str):
        """Remove a health check by name."""
        self.checks = [check for check in self.checks if check.name != name]
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        results = []
        
        # Run all checks concurrently
        tasks = [check.check() for check in self.checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        overall_status = HealthStatus.HEALTHY
        
        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                # Handle exceptions from health checks
                result = HealthCheckResult(
                    name=self.checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check exception: {str(result)}",
                    duration_ms=0,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            results.append(result)
            self.last_results[result.name] = result
            
            # Determine overall status
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Calculate summary statistics
        total_duration = sum(r.duration_ms for r in results)
        healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_checks': len(results),
                'healthy': healthy_count,
                'degraded': degraded_count,
                'unhealthy': unhealthy_count,
                'total_duration_ms': total_duration
            },
            'checks': [
                {
                    'name': r.name,
                    'status': r.status.value,
                    'message': r.message,
                    'duration_ms': r.duration_ms,
                    'timestamp': r.timestamp,
                    'details': r.details
                }
                for r in results
            ]
        }

    # New sync wrapper to run health checks with optional timeout and return AggregatedHealthResult
    def run_health_checks(self, timeout: float = 5.0) -> "AggregatedHealthResult":
        start = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Wrap coroutines into tasks explicitly to satisfy asyncio.wait requirements
            tasks = [loop.create_task(check.check()) for check in self.checks]
            done, pending = loop.run_until_complete(asyncio.wait(tasks, timeout=timeout))

            results: List["HealthCheckExecution"] = []
            overall_status = HealthStatus.HEALTHY

            # Collect completed results
            for task in done:
                try:
                    r: HealthCheckResult = task.result()
                except Exception as e:
                    r = HealthCheckResult(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check exception: {str(e)}",
                        duration_ms=0.0,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        details=None
                    )
                # Map to execution format
                results.append(HealthCheckExecution(
                    name=r.name,
                    status=r.status,
                    message=r.message,
                    execution_time=r.duration_ms,
                    metadata=r.details
                ))
                # Track overall status
                if r.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif r.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

            # Handle timed-out checks
            for p in pending:
                try:
                    p.cancel()
                except Exception:
                    pass
                results.append(HealthCheckExecution(
                    name="timeout",
                    status=HealthStatus.UNHEALTHY,
                    message="Health check timed out",
                    execution_time=float(timeout * 1000.0),
                    metadata=None
                ))
                overall_status = HealthStatus.UNHEALTHY

            total_checks = len(self.checks)
            checks_failed = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
            checks_passed = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
            exec_time = time.time() - start

            return AggregatedHealthResult(
                overall_status=overall_status,
                timestamp=datetime.now(timezone.utc),
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                total_checks=total_checks,
                execution_time=exec_time,
                results=results
            )
        finally:
            try:
                loop.close()
            except Exception:
                pass
    
    async def run_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check by name."""
        for check in self.checks:
            if check.name == name:
                result = await check.check()
                self.last_results[name] = result
                return result
        return None
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get the last health check results."""
        if not self.last_results:
            return {
                'status': 'unknown',
                'message': 'No health checks have been run yet',
                'checks': []
            }
        
        # Determine overall status from last results
        statuses = [result.status for result in self.last_results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            'status': overall_status.value,
            'timestamp': max(r.timestamp for r in self.last_results.values()),
            'checks': [
                {
                    'name': r.name,
                    'status': r.status.value,
                    'message': r.message,
                    'duration_ms': r.duration_ms,
                    'timestamp': r.timestamp,
                    'details': r.details
                }
                for r in self.last_results.values()
            ]
        }

# Global health check manager
health_manager = HealthCheckManager()

# Update signature to optionally accept a manager instance and app_context
def setup_default_health_checks(manager: HealthCheckManager = None, app_context=None):
    """Setup default health checks for the application."""
    target_manager = manager if manager is not None else health_manager
    # System resources check
    target_manager.add_check(SystemResourcesHealthCheck())
    # Database/FAISS check
    target_manager.add_check(DatabaseHealthCheck())
    # Application-specific check
    target_manager.add_check(ApplicationHealthCheck(app_context))
    # External service checks (if needed)
    # target_manager.add_check(ExternalServiceHealthCheck("ollama", "http://localhost:11434/api/version"))
    logger.info("Default health checks configured")

# Utility function for quick health status
async def get_health_status() -> str:
    """Get quick health status string."""
    results = await health_manager.run_all_checks()
    return results['status']

# New dataclasses to provide aggregate result in the shape expected by agent_bridge
@dataclass
class HealthCheckExecution:
    name: str
    status: HealthStatus
    message: str
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AggregatedHealthResult:
    overall_status: HealthStatus
    timestamp: datetime
    checks_passed: int
    checks_failed: int
    total_checks: int
    execution_time: float
    results: List[HealthCheckExecution]