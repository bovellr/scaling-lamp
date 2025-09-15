# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# PERFORMANCE MONITORING SERVICE
# ============================================================================

"""
Performance monitoring service to track and optimize application performance.
Provides metrics collection, profiling, and performance recommendations.
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: float
    unit: str = "ms"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceStats:
    """Performance statistics for a specific operation"""
    operation_name: str
    total_calls: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    memory_usage: List[float] = field(default_factory=list)
    cpu_usage: List[float] = field(default_factory=list)

class PerformanceMonitor:
    """Centralized performance monitoring service"""
    
    def __init__(self, enable_memory_monitoring: bool = True):
        self.enable_memory_monitoring = enable_memory_monitoring
        self._metrics: Dict[str, PerformanceStats] = {}
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
        
        # System monitoring
        self._process = psutil.Process()
        self._monitoring_thread = None
        self._stop_monitoring = False
        
        if enable_memory_monitoring:
            self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while not self._stop_monitoring:
                try:
                    memory_percent = self._process.memory_percent()
                    cpu_percent = self._process.cpu_percent()
                    
                    # Update all active operations with current system metrics
                    with self._lock:
                        for op_name in self._active_operations:
                            if op_name in self._metrics:
                                self._metrics[op_name].memory_usage.append(memory_percent)
                                self._metrics[op_name].cpu_usage.append(cpu_percent)
                    
                    time.sleep(0.1)  # Monitor every 100ms
                except Exception as e:
                    logger.warning(f"System monitoring error: {e}")
                    break
        
        self._monitoring_thread = threading.Thread(target=monitor_system, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
    
    @contextmanager
    def measure_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to measure operation performance"""
        start_time = time.time()
        start_memory = self._process.memory_info().rss if self.enable_memory_monitoring else 0
        
        with self._lock:
            self._active_operations[operation_name] = {
                'start_time': start_time,
                'start_memory': start_memory,
                'metadata': metadata or {}
            }
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            with self._lock:
                if operation_name in self._active_operations:
                    del self._active_operations[operation_name]
                
                self._record_metric(operation_name, duration, metadata or {})
    
    def _record_metric(self, operation_name: str, duration: float, metadata: Dict[str, Any]):
        """Record a performance metric"""
        if operation_name not in self._metrics:
            self._metrics[operation_name] = PerformanceStats(
                operation_name=operation_name,
                total_calls=0,
                total_time=0.0,
                average_time=0.0,
                min_time=float('inf'),
                max_time=0.0
            )
        
        stats = self._metrics[operation_name]
        stats.total_calls += 1
        stats.total_time += duration
        stats.average_time = stats.total_time / stats.total_calls
        stats.min_time = min(stats.min_time, duration)
        stats.max_time = max(stats.max_time, duration)
        stats.recent_times.append(duration)
    
    def measure_function(self, operation_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Decorator to measure function performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                with self.measure_operation(op_name, metadata):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for an operation or all operations"""
        with self._lock:
            if operation_name:
                if operation_name in self._metrics:
                    stats = self._metrics[operation_name]
                    return {
                        'operation_name': stats.operation_name,
                        'total_calls': stats.total_calls,
                        'total_time': stats.total_time,
                        'average_time': stats.average_time,
                        'min_time': stats.min_time,
                        'max_time': stats.max_time,
                        'recent_average': sum(stats.recent_times) / len(stats.recent_times) if stats.recent_times else 0,
                        'memory_usage_avg': sum(stats.memory_usage) / len(stats.memory_usage) if stats.memory_usage else 0,
                        'cpu_usage_avg': sum(stats.cpu_usage) / len(stats.cpu_usage) if stats.cpu_usage else 0
                    }
                return {}
            else:
                return {name: self.get_metrics(name) for name in self._metrics.keys()}
    
    def get_slow_operations(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        """Get operations that are slower than the threshold"""
        slow_ops = []
        for name, stats in self._metrics.items():
            if stats.average_time > threshold_ms:
                slow_ops.append({
                    'operation_name': name,
                    'average_time': stats.average_time,
                    'total_calls': stats.total_calls,
                    'total_time': stats.total_time
                })
        
        return sorted(slow_ops, key=lambda x: x['average_time'], reverse=True)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        try:
            memory_info = self._process.memory_info()
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': self._process.memory_percent(),
                'available': psutil.virtual_memory().available / 1024 / 1024  # MB
            }
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return {}
    
    def get_cpu_usage(self) -> Dict[str, float]:
        """Get current CPU usage statistics"""
        try:
            return {
                'process_cpu': self._process.cpu_percent(),
                'system_cpu': psutil.cpu_percent(),
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        total_operations = sum(stats.total_calls for stats in self._metrics.values())
        total_time = sum(stats.total_time for stats in self._metrics.values())
        
        return {
            'uptime': time.time() - self._start_time,
            'total_operations': total_operations,
            'total_time': total_time,
            'average_operation_time': total_time / total_operations if total_operations > 0 else 0,
            'operations_per_second': total_operations / (time.time() - self._start_time) if time.time() > self._start_time else 0,
            'memory_usage': self.get_memory_usage(),
            'cpu_usage': self.get_cpu_usage(),
            'slow_operations': self.get_slow_operations(),
            'operation_count': len(self._metrics)
        }
    
    def clear_metrics(self, operation_name: Optional[str] = None):
        """Clear performance metrics"""
        with self._lock:
            if operation_name:
                if operation_name in self._metrics:
                    del self._metrics[operation_name]
            else:
                self._metrics.clear()
    
    def export_metrics(self, file_path: str):
        """Export metrics to a file"""
        import json
        try:
            with open(file_path, 'w') as f:
                json.dump(self.get_performance_summary(), f, indent=2)
            logger.info(f"Performance metrics exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        # Check for slow operations
        slow_ops = self.get_slow_operations(500.0)  # 500ms threshold
        if slow_ops:
            recommendations.append(f"Consider optimizing {len(slow_ops)} slow operations: {[op['operation_name'] for op in slow_ops[:3]]}")
        
        # Check memory usage
        memory_usage = self.get_memory_usage()
        if memory_usage.get('percent', 0) > 80:
            recommendations.append("High memory usage detected. Consider implementing data pagination or caching.")
        
        # Check for frequently called operations
        for name, stats in self._metrics.items():
            if stats.total_calls > 1000 and stats.average_time > 100:
                recommendations.append(f"Operation '{name}' is called frequently ({stats.total_calls} times) and could benefit from caching.")
        
        return recommendations

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience decorators
def measure_performance(operation_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """Convenience decorator for measuring function performance"""
    return performance_monitor.measure_function(operation_name, metadata)

def measure_operation(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Convenience context manager for measuring operations"""
    return performance_monitor.measure_operation(operation_name, metadata)
