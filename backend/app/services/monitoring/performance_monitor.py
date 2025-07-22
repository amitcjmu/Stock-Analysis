"""
Performance Monitor
Implements Task 4.2 of the Discovery Flow Redesign.
Provides comprehensive performance monitoring for agents, crews, and user interactions.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Generic performance metric"""
    metric_type: str
    operation_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.lock = Lock()
        
        # Metric storage
        self.metrics: deque = deque(maxlen=max_metrics)
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        
        # Performance thresholds
        self.thresholds = {
            "agent_response_time": 30.0,
            "crew_escalation_time": 300.0,
            "user_interaction_time": 30.0,
        }
        
        logger.info("🔍 Performance Monitor initialized")
    
    def start_operation(self, operation_type: str, operation_id: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking an operation"""
        operation_data = {
            "operation_type": operation_type,
            "operation_id": operation_id,
            "start_time": time.time(),
            "metadata": metadata or {}
        }
        
        with self.lock:
            self.active_operations[operation_id] = operation_data
        
        logger.debug(f"📊 Started tracking {operation_type}: {operation_id}")
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     metadata: Optional[Dict[str, Any]] = None):
        """End tracking an operation"""
        with self.lock:
            if operation_id not in self.active_operations:
                logger.warning(f"⚠️ Operation {operation_id} not found")
                return
            
            operation_data = self.active_operations.pop(operation_id)
        
        end_time = time.time()
        duration = end_time - operation_data["start_time"]
        
        metric = PerformanceMetric(
            metric_type=operation_data["operation_type"],
            operation_id=operation_id,
            start_time=operation_data["start_time"],
            end_time=end_time,
            duration=duration,
            success=success,
            metadata={**operation_data["metadata"], **(metadata or {})}
        )
        
        with self.lock:
            self.metrics.append(metric)
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {operation_data['operation_type']} {operation_id} completed in {duration:.2f}s")
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard"""
        with self.lock:
            metrics_list = list(self.metrics)
            active_ops = len(self.active_operations)
        
        if not metrics_list:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "No performance data available",
                "active_operations": active_ops
            }
        
        # Analyze metrics by type
        metrics_by_type = defaultdict(list)
        for metric in metrics_list:
            metrics_by_type[metric.metric_type].append(metric)
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_operations": active_ops,
            "total_operations": len(metrics_list),
            "metrics_by_type": {}
        }
        
        for metric_type, type_metrics in metrics_by_type.items():
            dashboard["metrics_by_type"][metric_type] = self._analyze_metrics(type_metrics)
        
        # Overall performance grade
        dashboard["performance_grade"] = self._calculate_performance_grade(metrics_list)
        
        return dashboard
    
    def _analyze_metrics(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze metrics for a specific type"""
        if not metrics:
            return {"message": "No data available"}
        
        total_operations = len(metrics)
        successful_operations = sum(1 for m in metrics if m.success)
        
        durations = [m.duration for m in metrics if m.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_operations": total_operations,
            "success_rate": successful_operations / total_operations,
            "average_duration": avg_duration,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "recent_operations": len([m for m in metrics if m.start_time > time.time() - 3600])
        }
    
    def _calculate_performance_grade(self, metrics: List[PerformanceMetric]) -> str:
        """Calculate overall performance grade"""
        if not metrics:
            return "no_data"
        
        success_rate = sum(1 for m in metrics if m.success) / len(metrics)
        durations = [m.duration for m in metrics if m.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        score = success_rate * 60 + (30 - min(avg_duration, 30)) / 30 * 40
        
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        else:
            return "needs_improvement"

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_dashboard():
    """Get the current performance dashboard"""
    return performance_monitor.get_performance_dashboard()

def start_operation_tracking(operation_type: str, operation_id: str, metadata: Optional[Dict[str, Any]] = None):
    """Start tracking an operation"""
    return performance_monitor.start_operation(operation_type, operation_id, metadata)

def end_operation_tracking(operation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None):
    """End tracking an operation"""
    performance_monitor.end_operation(operation_id, success, metadata) 