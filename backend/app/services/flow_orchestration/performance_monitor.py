"""
Flow Performance Monitor

Handles performance tracking, metrics collection, timing measurements, and resource usage monitoring.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import psutil
import sys

from app.core.logging import get_logger
from app.services.performance_tracker import PerformanceTracker as BasePerformanceTracker

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_id: str
    flow_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = None
    resource_usage: Dict[str, Any] = None


@dataclass
class ResourceSnapshot:
    """Resource usage snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage: Dict[str, Any]
    network_io: Dict[str, Any] = None


class FlowPerformanceMonitor:
    """
    Enhanced performance monitoring for flow operations with detailed metrics and resource tracking.
    """
    
    def __init__(self):
        """Initialize the Flow Performance Monitor"""
        self.base_tracker = BasePerformanceTracker()
        self.active_metrics: Dict[str, PerformanceMetric] = {}
        self.completed_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.resource_snapshots: Dict[str, List[ResourceSnapshot]] = defaultdict(list)
        self.performance_thresholds = {
            "flow_creation_ms": 5000,
            "phase_execution_ms": 30000,
            "status_check_ms": 1000,
            "cpu_threshold_percent": 80,
            "memory_threshold_percent": 85
        }
        
        logger.info("✅ Flow Performance Monitor initialized")
    
    def start_operation(
        self,
        flow_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a flow operation
        
        Args:
            flow_id: Flow identifier
            operation_type: Type of operation being tracked
            metadata: Additional metadata for the operation
            
        Returns:
            Tracking ID for the operation
        """
        # Use base tracker to get tracking ID
        tracking_id = self.base_tracker.start_operation(operation_type, metadata or {})
        
        # Create enhanced metric
        metric = PerformanceMetric(
            metric_id=tracking_id,
            flow_id=flow_id,
            operation_type=operation_type,
            start_time=datetime.utcnow(),
            metadata=metadata or {},
            resource_usage=self._capture_resource_snapshot()
        )
        
        self.active_metrics[tracking_id] = metric
        
        # Take initial resource snapshot
        self._take_resource_snapshot(flow_id)
        
        logger.debug(f"📊 Started tracking {operation_type} for flow {flow_id}")
        return tracking_id
    
    def end_operation(
        self,
        tracking_id: str,
        success: bool = True,
        result_metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetric:
        """
        End tracking of a flow operation
        
        Args:
            tracking_id: Tracking ID returned by start_operation
            success: Whether the operation succeeded
            result_metadata: Additional metadata about the result
            
        Returns:
            Completed performance metric
        """
        # End base tracker operation
        self.base_tracker.end_operation(tracking_id, success, result_metadata or {})
        
        # Get and complete our metric
        metric = self.active_metrics.get(tracking_id)
        if not metric:
            logger.warning(f"⚠️ No active metric found for tracking ID: {tracking_id}")
            return None
        
        # Complete the metric
        metric.end_time = datetime.utcnow()
        metric.duration_ms = (metric.end_time - metric.start_time).total_seconds() * 1000
        metric.success = success
        
        # Add result metadata
        if result_metadata:
            metric.metadata.update(result_metadata)
        
        # Capture final resource usage
        final_resources = self._capture_resource_snapshot()
        metric.resource_usage["final"] = final_resources
        
        # Calculate resource deltas
        if "initial" in metric.resource_usage:
            metric.resource_usage["delta"] = self._calculate_resource_delta(
                metric.resource_usage["initial"],
                final_resources
            )
        
        # Move to completed metrics
        self.completed_metrics[metric.flow_id].append(metric)
        del self.active_metrics[tracking_id]
        
        # Take final resource snapshot
        self._take_resource_snapshot(metric.flow_id)
        
        # Check performance thresholds
        self._check_performance_thresholds(metric)
        
        logger.debug(f"📊 Completed tracking {metric.operation_type} for flow {metric.flow_id}: {metric.duration_ms:.2f}ms")
        return metric
    
    def _capture_resource_snapshot(self) -> Dict[str, Any]:
        """Capture current system resource usage"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / 1024 / 1024
            
            # Get disk usage for current directory
            disk_usage = psutil.disk_usage('/')
            disk_info = {
                "total_gb": disk_usage.total / 1024 / 1024 / 1024,
                "used_gb": disk_usage.used / 1024 / 1024 / 1024,
                "free_gb": disk_usage.free / 1024 / 1024 / 1024,
                "percent": (disk_usage.used / disk_usage.total) * 100
            }
            
            # Get network I/O if available
            network_io = {}
            try:
                net_io = psutil.net_io_counters()
                network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            except:
                pass
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_mb": memory_mb,
                "disk_usage": disk_info,
                "network_io": network_io
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to capture resource snapshot: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _take_resource_snapshot(self, flow_id: str):
        """Take a resource snapshot for a specific flow"""
        try:
            snapshot_data = self._capture_resource_snapshot()
            
            snapshot = ResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=snapshot_data.get("cpu_percent", 0),
                memory_percent=snapshot_data.get("memory_percent", 0),
                memory_mb=snapshot_data.get("memory_mb", 0),
                disk_usage=snapshot_data.get("disk_usage", {}),
                network_io=snapshot_data.get("network_io", {})
            )
            
            self.resource_snapshots[flow_id].append(snapshot)
            
            # Keep only last 20 snapshots per flow
            if len(self.resource_snapshots[flow_id]) > 20:
                self.resource_snapshots[flow_id] = self.resource_snapshots[flow_id][-20:]
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to take resource snapshot for flow {flow_id}: {e}")
    
    def _calculate_resource_delta(
        self,
        initial_resources: Dict[str, Any],
        final_resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate the delta between initial and final resource usage"""
        try:
            delta = {}
            
            # Calculate CPU delta
            if "cpu_percent" in initial_resources and "cpu_percent" in final_resources:
                delta["cpu_percent_delta"] = final_resources["cpu_percent"] - initial_resources["cpu_percent"]
            
            # Calculate memory delta
            if "memory_mb" in initial_resources and "memory_mb" in final_resources:
                delta["memory_mb_delta"] = final_resources["memory_mb"] - initial_resources["memory_mb"]
            
            # Calculate network I/O delta
            if ("network_io" in initial_resources and "network_io" in final_resources and 
                initial_resources["network_io"] and final_resources["network_io"]):
                initial_net = initial_resources["network_io"]
                final_net = final_resources["network_io"]
                
                delta["network_io_delta"] = {
                    "bytes_sent_delta": final_net.get("bytes_sent", 0) - initial_net.get("bytes_sent", 0),
                    "bytes_recv_delta": final_net.get("bytes_recv", 0) - initial_net.get("bytes_recv", 0),
                    "packets_sent_delta": final_net.get("packets_sent", 0) - initial_net.get("packets_sent", 0),
                    "packets_recv_delta": final_net.get("packets_recv", 0) - initial_net.get("packets_recv", 0)
                }
            
            return delta
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate resource delta: {e}")
            return {}
    
    def _check_performance_thresholds(self, metric: PerformanceMetric):
        """Check if performance metric exceeds thresholds"""
        warnings = []
        
        # Check duration thresholds
        threshold_key = f"{metric.operation_type}_ms"
        if threshold_key in self.performance_thresholds:
            threshold = self.performance_thresholds[threshold_key]
            if metric.duration_ms > threshold:
                warnings.append(f"Operation {metric.operation_type} took {metric.duration_ms:.2f}ms (threshold: {threshold}ms)")
        
        # Check resource thresholds
        if metric.resource_usage and "final" in metric.resource_usage:
            final_resources = metric.resource_usage["final"]
            
            # Check CPU threshold
            cpu_percent = final_resources.get("cpu_percent", 0)
            if cpu_percent > self.performance_thresholds["cpu_threshold_percent"]:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}% (threshold: {self.performance_thresholds['cpu_threshold_percent']}%)")
            
            # Check memory threshold
            memory_percent = final_resources.get("memory_percent", 0)
            if memory_percent > self.performance_thresholds["memory_threshold_percent"]:
                warnings.append(f"High memory usage: {memory_percent:.1f}% (threshold: {self.performance_thresholds['memory_threshold_percent']}%)")
        
        # Log warnings
        if warnings:
            logger.warning(f"⚠️ Performance thresholds exceeded for {metric.operation_type} in flow {metric.flow_id}: {'; '.join(warnings)}")
    
    def get_flow_performance_summary(self, flow_id: str) -> Dict[str, Any]:
        """
        Get performance summary for a specific flow
        
        Args:
            flow_id: Flow identifier
            
        Returns:
            Performance summary for the flow
        """
        completed_metrics = self.completed_metrics.get(flow_id, [])
        active_metrics = [m for m in self.active_metrics.values() if m.flow_id == flow_id]
        resource_snapshots = self.resource_snapshots.get(flow_id, [])
        
        if not completed_metrics and not active_metrics:
            return {
                "flow_id": flow_id,
                "total_operations": 0,
                "message": "No performance data available"
            }
        
        # Calculate summary statistics
        total_operations = len(completed_metrics) + len(active_metrics)
        successful_operations = len([m for m in completed_metrics if m.success])
        failed_operations = len([m for m in completed_metrics if not m.success])
        
        # Duration statistics
        durations = [m.duration_ms for m in completed_metrics if m.duration_ms is not None]
        duration_stats = {}
        if durations:
            duration_stats = {
                "total_duration_ms": sum(durations),
                "average_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations)
            }
        
        # Operation type breakdown
        operation_breakdown = {}
        for metric in completed_metrics:
            op_type = metric.operation_type
            if op_type not in operation_breakdown:
                operation_breakdown[op_type] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "success_count": 0,
                    "failure_count": 0
                }
            
            operation_breakdown[op_type]["count"] += 1
            if metric.duration_ms:
                operation_breakdown[op_type]["total_duration_ms"] += metric.duration_ms
            
            if metric.success:
                operation_breakdown[op_type]["success_count"] += 1
            else:
                operation_breakdown[op_type]["failure_count"] += 1
        
        # Calculate average durations
        for op_type, stats in operation_breakdown.items():
            if stats["count"] > 0:
                stats["average_duration_ms"] = stats["total_duration_ms"] / stats["count"]
        
        # Resource usage summary
        resource_summary = {}
        if resource_snapshots:
            cpu_values = [s.cpu_percent for s in resource_snapshots]
            memory_values = [s.memory_mb for s in resource_snapshots]
            
            resource_summary = {
                "cpu_usage": {
                    "average_percent": sum(cpu_values) / len(cpu_values),
                    "max_percent": max(cpu_values),
                    "min_percent": min(cpu_values)
                },
                "memory_usage": {
                    "average_mb": sum(memory_values) / len(memory_values),
                    "max_mb": max(memory_values),
                    "min_mb": min(memory_values)
                },
                "snapshot_count": len(resource_snapshots)
            }
        
        return {
            "flow_id": flow_id,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_statistics": duration_stats,
            "operation_breakdown": operation_breakdown,
            "resource_summary": resource_summary,
            "active_operations": len(active_metrics)
        }
    
    def get_system_performance_overview(self) -> Dict[str, Any]:
        """
        Get overall system performance overview
        
        Returns:
            System performance overview
        """
        # Get current system resources
        current_resources = self._capture_resource_snapshot()
        
        # Aggregate metrics across all flows
        all_completed_metrics = []
        for flow_metrics in self.completed_metrics.values():
            all_completed_metrics.extend(flow_metrics)
        
        total_flows = len(self.completed_metrics)
        total_operations = len(all_completed_metrics)
        active_operations = len(self.active_metrics)
        
        # Calculate overall statistics
        successful_operations = len([m for m in all_completed_metrics if m.success])
        failed_operations = len([m for m in all_completed_metrics if not m.success])
        
        # Duration statistics
        durations = [m.duration_ms for m in all_completed_metrics if m.duration_ms is not None]
        duration_stats = {}
        if durations:
            duration_stats = {
                "total_duration_ms": sum(durations),
                "average_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations)
            }
        
        # Operation type statistics
        operation_stats = {}
        for metric in all_completed_metrics:
            op_type = metric.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = 0
            operation_stats[op_type] += 1
        
        return {
            "system_resources": current_resources,
            "flow_statistics": {
                "total_flows": total_flows,
                "total_operations": total_operations,
                "active_operations": active_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "success_rate": successful_operations / total_operations if total_operations > 0 else 0
            },
            "duration_statistics": duration_stats,
            "operation_type_statistics": operation_stats,
            "performance_thresholds": self.performance_thresholds
        }
    
    def set_performance_threshold(self, threshold_name: str, threshold_value: float):
        """
        Set a performance threshold
        
        Args:
            threshold_name: Name of the threshold
            threshold_value: Threshold value
        """
        self.performance_thresholds[threshold_name] = threshold_value
        logger.info(f"📊 Set performance threshold {threshold_name} to {threshold_value}")
    
    def clear_flow_metrics(self, flow_id: str):
        """
        Clear metrics for a specific flow
        
        Args:
            flow_id: Flow identifier
        """
        # Remove completed metrics
        self.completed_metrics.pop(flow_id, None)
        
        # Remove active metrics
        active_to_remove = [tid for tid, metric in self.active_metrics.items() if metric.flow_id == flow_id]
        for tid in active_to_remove:
            del self.active_metrics[tid]
        
        # Remove resource snapshots
        self.resource_snapshots.pop(flow_id, None)
        
        logger.info(f"🧹 Cleared performance metrics for flow {flow_id}")
    
    def get_slow_operations(self, threshold_ms: float = 5000) -> List[PerformanceMetric]:
        """
        Get operations that exceeded the specified duration threshold
        
        Args:
            threshold_ms: Duration threshold in milliseconds
            
        Returns:
            List of slow operations
        """
        slow_operations = []
        
        for flow_metrics in self.completed_metrics.values():
            for metric in flow_metrics:
                if metric.duration_ms and metric.duration_ms > threshold_ms:
                    slow_operations.append(metric)
        
        # Sort by duration (slowest first)
        slow_operations.sort(key=lambda m: m.duration_ms or 0, reverse=True)
        
        return slow_operations
    
    def record_audit_event(self, audit_entry: Dict[str, Any]):
        """
        Record an audit event for performance tracking
        
        Args:
            audit_entry: Audit entry data
        """
        # Delegate to base tracker
        self.base_tracker.record_audit_event(audit_entry)
        
        # Log performance-related audit events
        if audit_entry.get("operation") in ["create", "execute", "delete"]:
            logger.debug(f"📊 Audit event recorded: {audit_entry.get('operation')} for flow {audit_entry.get('flow_id')}")