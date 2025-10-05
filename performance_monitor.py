# performance_monitor.py
"""
Performance monitoring and metrics collection system for the RAG Agent application.
Provides comprehensive performance tracking, metrics collection, and alerting capabilities.
"""

import time
import psutil
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
from pathlib import Path
from standardized_error_handler import (
    handle_errors, ErrorCategory, ErrorSeverity,
    handle_database_error
)

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class Alert:
    """Performance alert."""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    threshold: float
    current_value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: List[float] = field(default_factory=list)

class MetricsCollector:
    """Collects and stores performance metrics."""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.alerts: List[Alert] = []
        self._lock = threading.RLock()
        
        # System monitoring
        self.last_network_stats = None
        self.last_disk_io = None
        
        logger.info("MetricsCollector initialized")
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, metric_type: MetricType = MetricType.GAUGE):
        """Record a metric value."""
        with self._lock:
            metric_point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                metric_type=metric_type
            )
            
            self.metrics[name].append(metric_point)
            
            logger.debug(f"Recorded metric {name}: {value}")
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        self.record_metric(name, value, tags, MetricType.COUNTER)
    
    def record_timer(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric."""
        self.record_metric(name, duration_seconds * 1000, tags, MetricType.TIMER)  # Convert to milliseconds
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        self.record_metric(name, value, tags, MetricType.HISTOGRAM)
    
    def get_metric_history(self, name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """Get metric history for a specific duration."""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
            return [point for point in self.metrics[name] if point.timestamp >= cutoff_time]
    
    def get_metric_summary(self, name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get statistical summary of a metric."""
        history = self.get_metric_history(name, duration_minutes)
        
        if not history:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}
        
        values = [point.value for point in history]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
            "last": values[-1] if values else 0
        }
    
    def add_alert(self, alert: Alert):
        """Add a performance alert."""
        with self._lock:
            self.alerts.append(alert)
            logger.warning(f"Performance alert: {alert.name} - {alert.message}")
    
    def get_recent_alerts(self, duration_minutes: int = 60) -> List[Alert]:
        """Get recent alerts."""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
            return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
    
    def clear_old_alerts(self, duration_hours: int = 24):
        """Clear old alerts."""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=duration_hours)
            self.alerts = [alert for alert in self.alerts if alert.timestamp >= cutoff_time]

class SystemMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
        self.interval = 30  # seconds
        
        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'load_average': 4.0
        }
        
        logger.info("SystemMonitor initialized")
    
    def start_monitoring(self, interval: int = 30):
        """Start system monitoring."""
        if self.monitoring:
            logger.warning("System monitoring already running")
            return
        
        self.interval = interval
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"System monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                snapshot = self._collect_system_snapshot()
                self._record_system_metrics(snapshot)
                self._check_thresholds(snapshot)
                
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)
    
    @handle_errors(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.LOW,
        context={'component': 'system_monitor', 'operation': 'collect_snapshot'},
        return_error_response=False
    )
    def _collect_system_snapshot(self) -> PerformanceSnapshot:
        """Collect system performance snapshot."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            load_avg = []
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                load_avg = [0.0, 0.0, 0.0]
            
            return PerformanceSnapshot(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024**3),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.error(f"Error collecting system snapshot: {e}")
            handle_database_error(e, {'component': 'system_monitor', 'operation': 'collect_snapshot'})
            raise
    
    def _record_system_metrics(self, snapshot: PerformanceSnapshot):
        """Record system metrics from snapshot."""
        tags = {"source": "system_monitor"}
        
        # CPU metrics
        self.metrics_collector.record_metric("system.cpu_percent", snapshot.cpu_percent, tags)
        
        # Memory metrics
        self.metrics_collector.record_metric("system.memory_percent", snapshot.memory_percent, tags)
        self.metrics_collector.record_metric("system.memory_used_gb", snapshot.memory_used_gb, tags)
        self.metrics_collector.record_metric("system.memory_available_gb", snapshot.memory_available_gb, tags)
        
        # Disk metrics
        self.metrics_collector.record_metric("system.disk_usage_percent", snapshot.disk_usage_percent, tags)
        self.metrics_collector.record_metric("system.disk_free_gb", snapshot.disk_free_gb, tags)
        
        # Network metrics
        self.metrics_collector.record_metric("system.network_bytes_sent", snapshot.network_bytes_sent, tags)
        self.metrics_collector.record_metric("system.network_bytes_recv", snapshot.network_bytes_recv, tags)
        
        # Process metrics
        self.metrics_collector.record_metric("system.process_count", snapshot.process_count, tags)
        
        # Load average metrics
        for i, load in enumerate(snapshot.load_average):
            self.metrics_collector.record_metric(f"system.load_avg_{i+1}", load, tags)
    
    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check performance thresholds and generate alerts."""
        current_time = datetime.now(timezone.utc)
        
        # CPU threshold
        if snapshot.cpu_percent > self.thresholds['cpu_percent']:
            alert = Alert(
                name="high_cpu_usage",
                severity=AlertSeverity.WARNING,
                message=f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                timestamp=current_time,
                threshold=self.thresholds['cpu_percent'],
                current_value=snapshot.cpu_percent
            )
            self.metrics_collector.add_alert(alert)
        
        # Memory threshold
        if snapshot.memory_percent > self.thresholds['memory_percent']:
            alert = Alert(
                name="high_memory_usage",
                severity=AlertSeverity.WARNING,
                message=f"High memory usage: {snapshot.memory_percent:.1f}%",
                timestamp=current_time,
                threshold=self.thresholds['memory_percent'],
                current_value=snapshot.memory_percent
            )
            self.metrics_collector.add_alert(alert)
        
        # Disk threshold
        if snapshot.disk_usage_percent > self.thresholds['disk_usage_percent']:
            alert = Alert(
                name="high_disk_usage",
                severity=AlertSeverity.CRITICAL,
                message=f"High disk usage: {snapshot.disk_usage_percent:.1f}%",
                timestamp=current_time,
                threshold=self.thresholds['disk_usage_percent'],
                current_value=snapshot.disk_usage_percent
            )
            self.metrics_collector.add_alert(alert)
        
        # Load average threshold
        if snapshot.load_average and snapshot.load_average[0] > self.thresholds['load_average']:
            alert = Alert(
                name="high_load_average",
                severity=AlertSeverity.WARNING,
                message=f"High load average: {snapshot.load_average[0]:.2f}",
                timestamp=current_time,
                threshold=self.thresholds['load_average'],
                current_value=snapshot.load_average[0]
            )
            self.metrics_collector.add_alert(alert)

class ApplicationMonitor:
    """Monitors application-specific performance metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        
        logger.info("ApplicationMonitor initialized")
    
    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API request metrics."""
        tags = {
            "endpoint": endpoint,
            "status_code": str(status_code)
        }
        
        # Record response time
        self.metrics_collector.record_timer("app.request_duration", duration_ms / 1000, tags)
        
        # Record request count
        self.metrics_collector.increment_counter("app.request_count", tags=tags)
        
        # Track request times for percentile calculations
        self.request_times[endpoint].append(duration_ms)
        if len(self.request_times[endpoint]) > 100:  # Keep only last 100 requests
            self.request_times[endpoint].pop(0)
        
        # Record error counts
        if status_code >= 400:
            self.error_counts[endpoint] += 1
            self.metrics_collector.increment_counter("app.error_count", tags=tags)
    
    def record_rag_operation(self, operation: str, duration_ms: float, success: bool):
        """Record RAG operation metrics."""
        tags = {
            "operation": operation,
            "success": str(success)
        }
        
        self.metrics_collector.record_timer("rag.operation_duration", duration_ms / 1000, tags)
        self.metrics_collector.increment_counter("rag.operation_count", tags=tags)
        
        if not success:
            self.metrics_collector.increment_counter("rag.error_count", tags=tags)
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics."""
        tags = {
            "operation": operation,
            "hit": str(hit)
        }
        
        self.metrics_collector.increment_counter("cache.operation_count", tags=tags)
        if hit:
            self.metrics_collector.increment_counter("cache.hit_count", tags=tags)
        else:
            self.metrics_collector.increment_counter("cache.miss_count", tags=tags)
    
    def get_endpoint_performance(self, endpoint: str) -> Dict[str, Any]:
        """Get performance metrics for a specific endpoint."""
        if endpoint not in self.request_times:
            return {"request_count": 0, "avg_response_time": 0, "error_count": 0}
        
        times = self.request_times[endpoint]
        return {
            "request_count": len(times),
            "avg_response_time": sum(times) / len(times) if times else 0,
            "min_response_time": min(times) if times else 0,
            "max_response_time": max(times) if times else 0,
            "error_count": self.error_counts[endpoint]
        }

class PerformanceReporter:
    """Generates performance reports and exports metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector, system_monitor: SystemMonitor, app_monitor: ApplicationMonitor):
        self.metrics_collector = metrics_collector
        self.system_monitor = system_monitor
        self.app_monitor = app_monitor
        
        logger.info("PerformanceReporter initialized")
    
    def generate_report(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "system_metrics": {},
            "application_metrics": {},
            "alerts": [],
            "summary": {}
        }
        
        # System metrics
        system_metrics = [
            "system.cpu_percent",
            "system.memory_percent",
            "system.disk_usage_percent",
            "system.process_count"
        ]
        
        for metric in system_metrics:
            summary = self.metrics_collector.get_metric_summary(metric, duration_minutes)
            report["system_metrics"][metric] = summary
        
        # Application metrics
        app_metrics = [
            "app.request_count",
            "app.request_duration",
            "app.error_count",
            "rag.operation_count",
            "rag.operation_duration",
            "cache.hit_count",
            "cache.miss_count"
        ]
        
        for metric in app_metrics:
            summary = self.metrics_collector.get_metric_summary(metric, duration_minutes)
            report["application_metrics"][metric] = summary
        
        # Alerts
        recent_alerts = self.metrics_collector.get_recent_alerts(duration_minutes)
        report["alerts"] = [
            {
                "name": alert.name,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "threshold": alert.threshold,
                "current_value": alert.current_value
            }
            for alert in recent_alerts
        ]
        
        # Summary
        total_requests = sum(
            summary.get("sum", 0) 
            for metric, summary in report["application_metrics"].items() 
            if "request_count" in metric
        )
        
        avg_response_time = 0
        if "app.request_duration" in report["application_metrics"]:
            avg_response_time = report["application_metrics"]["app.request_duration"].get("avg", 0)
        
        error_rate = 0
        if total_requests > 0 and "app.error_count" in report["application_metrics"]:
            error_count = report["application_metrics"]["app.error_count"].get("sum", 0)
            error_rate = (error_count / total_requests) * 100
        
        report["summary"] = {
            "total_requests": total_requests,
            "avg_response_time_ms": avg_response_time,
            "error_rate_percent": error_rate,
            "alerts_count": len(recent_alerts),
            "system_health": self._assess_system_health(report["system_metrics"])
        }
        
        return report
    
    def _assess_system_health(self, system_metrics: Dict[str, Any]) -> str:
        """Assess overall system health."""
        cpu_avg = system_metrics.get("system.cpu_percent", {}).get("avg", 0)
        memory_avg = system_metrics.get("system.memory_percent", {}).get("avg", 0)
        disk_avg = system_metrics.get("system.disk_usage_percent", {}).get("avg", 0)
        
        if cpu_avg > 80 or memory_avg > 85 or disk_avg > 90:
            return "critical"
        elif cpu_avg > 60 or memory_avg > 70 or disk_avg > 80:
            return "warning"
        else:
            return "healthy"
    
    def export_metrics(self, file_path: str, duration_minutes: int = 60):
        """Export metrics to JSON file."""
        try:
            report = self.generate_report(duration_minutes)
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Performance report exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            handle_database_error(e, {'component': 'performance_reporter', 'operation': 'export_metrics'})

# Global performance monitoring components
_metrics_collector = None
_system_monitor = None
_app_monitor = None
_performance_reporter = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def get_system_monitor() -> SystemMonitor:
    """Get or create global system monitor."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(get_metrics_collector())
    return _system_monitor

def get_app_monitor() -> ApplicationMonitor:
    """Get or create global application monitor."""
    global _app_monitor
    if _app_monitor is None:
        _app_monitor = ApplicationMonitor(get_metrics_collector())
    return _app_monitor

def get_performance_reporter() -> PerformanceReporter:
    """Get or create global performance reporter."""
    global _performance_reporter
    if _performance_reporter is None:
        _performance_reporter = PerformanceReporter(
            get_metrics_collector(),
            get_system_monitor(),
            get_app_monitor()
        )
    return _performance_reporter

# Decorator for automatic performance monitoring
def monitor_performance(operation_name: str):
    """Decorator to automatically monitor function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            app_monitor = get_app_monitor()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                app_monitor.record_rag_operation(operation_name, duration_ms, True)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                app_monitor.record_rag_operation(operation_name, duration_ms, False)
                raise
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the performance monitoring system
    print("📊 Performance Monitor Test")
    print("=" * 50)
    
    # Initialize components
    metrics_collector = get_metrics_collector()
    system_monitor = get_system_monitor()
    app_monitor = get_app_monitor()
    reporter = get_performance_reporter()
    
    # Start system monitoring
    system_monitor.start_monitoring(interval=5)
    
    # Simulate some application activity
    print("Simulating application activity...")
    for i in range(10):
        app_monitor.record_request("/chat", 150 + i * 10, 200)
        app_monitor.record_rag_operation("retrieve", 50 + i * 5, True)
        app_monitor.record_cache_operation("get", i % 2 == 0)
        time.sleep(0.1)
    
    # Wait for some metrics to accumulate
    time.sleep(10)
    
    # Generate and display report
    print("\nGenerating performance report...")
    report = reporter.generate_report(duration_minutes=1)
    
    print(f"System Health: {report['summary']['system_health']}")
    print(f"Total Requests: {report['summary']['total_requests']}")
    print(f"Avg Response Time: {report['summary']['avg_response_time_ms']:.2f}ms")
    print(f"Error Rate: {report['summary']['error_rate_percent']:.2f}%")
    print(f"Alerts: {report['summary']['alerts_count']}")
    
    # Stop monitoring
    system_monitor.stop_monitoring()
    
    print("\n✅ Performance monitoring test completed")
