"""
Concrete implementations of the TelemetryService interface.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Deque
from datetime import datetime, timedelta
from collections import defaultdict, deque
from uuid import uuid4

from .interface import TelemetryService, MetricType, LogLevel

logger = logging.getLogger(__name__)


class CloudTelemetryService(TelemetryService):
    """
    Cloud telemetry service implementation for SaaS deployments.
    Integrates with services like DataDog, New Relic, or CloudWatch.
    """
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize cloud telemetry service.
        
        Args:
            endpoint: Telemetry service endpoint
            api_key: API key for authentication
        """
        self.endpoint = endpoint or os.getenv("TELEMETRY_ENDPOINT")
        self.api_key = api_key or os.getenv("TELEMETRY_API_KEY")
        self._buffer: List[Dict[str, Any]] = []
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._metrics_cache: Dict[str, Deque[Dict[str, Any]]] = defaultdict(lambda: deque(maxlen=1000))
        logger.info(f"Initialized CloudTelemetryService with endpoint: {self.endpoint}")
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric to cloud service."""
        metric_data = {
            "name": name,
            "value": value,
            "type": metric_type.value,
            "tags": tags or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in cache for summaries
        self._metrics_cache[name].append(metric_data)
        
        # Buffer for batch sending
        self._buffer.append({
            "type": "metric",
            "data": metric_data
        })
        
        # Auto-flush if buffer is large
        if len(self._buffer) >= 100:
            await self.flush()
        
        logger.debug(f"Recorded metric: {name}={value}")
    
    async def record_event(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record custom event to cloud service."""
        event_data = {
            "name": event_name,
            "properties": properties or {},
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        
        self._buffer.append({
            "type": "event",
            "data": event_data
        })
        
        logger.debug(f"Recorded event: {event_name}")
    
    async def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send log to cloud service."""
        log_data = {
            "message": message,
            "level": level.value,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._buffer.append({
            "type": "log",
            "data": log_data
        })
        
        # Also log locally
        log_func = getattr(logger, level.value, logger.info)
        log_func(f"{message} | context: {context}")
    
    async def start_trace(
        self,
        operation_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start distributed trace."""
        trace_id = str(uuid4())
        
        self._traces[trace_id] = {
            "operation": operation_name,
            "tags": tags or {},
            "start_time": datetime.utcnow(),
            "spans": []
        }
        
        logger.debug(f"Started trace: {trace_id} for {operation_name}")
        return trace_id
    
    async def end_trace(
        self,
        trace_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """End distributed trace."""
        if trace_id not in self._traces:
            logger.warning(f"Trace {trace_id} not found")
            return
        
        trace = self._traces.pop(trace_id)
        duration = (datetime.utcnow() - trace["start_time"]).total_seconds()
        
        trace_data = {
            "trace_id": trace_id,
            "operation": trace["operation"],
            "duration_seconds": duration,
            "success": success,
            "error": error,
            "tags": trace["tags"],
            "timestamp": trace["start_time"].isoformat()
        }
        
        self._buffer.append({
            "type": "trace",
            "data": trace_data
        })
        
        logger.debug(f"Ended trace: {trace_id} (duration: {duration}s)")
    
    async def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record error with context."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._buffer.append({
            "type": "error",
            "data": error_data
        })
        
        logger.error(f"Recorded error: {error}", exc_info=error)
    
    async def flush(self) -> None:
        """Flush buffered telemetry data."""
        if not self._buffer:
            return
        
        # In production, this would send to the telemetry endpoint
        # For now, just log and clear
        logger.info(f"Flushing {len(self._buffer)} telemetry items to cloud service")
        self._buffer.clear()
    
    async def health_check(self) -> bool:
        """Check cloud telemetry connectivity."""
        try:
            # In production, this would ping the telemetry endpoint
            return bool(self.endpoint or os.getenv("TELEMETRY_ENDPOINT"))
        except Exception as e:
            logger.error(f"Telemetry health check failed: {e}")
            return False
    
    async def get_metrics_summary(
        self,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {}
        
        for name, metrics in self._metrics_cache.items():
            if metric_names and name not in metric_names:
                continue
            
            filtered_metrics = [
                m for m in metrics
                if (not start_time or datetime.fromisoformat(m["timestamp"]) >= start_time) and
                   (not end_time or datetime.fromisoformat(m["timestamp"]) <= end_time)
            ]
            
            if filtered_metrics:
                values = [m["value"] for m in filtered_metrics]
                summary[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": filtered_metrics[-1]["value"]
                }
        
        return summary


class NoOpTelemetryService(TelemetryService):
    """
    No-operation telemetry service for local development and on-premises deployments.
    Provides a graceful fallback that doesn't send data anywhere but maintains the interface.
    """
    
    def __init__(self):
        """Initialize no-op telemetry service."""
        self._metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._events: List[Dict[str, Any]] = []
        self._logs: List[Dict[str, Any]] = []
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._errors: List[Dict[str, Any]] = []
        logger.info("Initialized NoOpTelemetryService (telemetry disabled)")
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record metric locally only."""
        # Store locally for potential debugging
        self._metrics[name].append({
            "value": value,
            "type": metric_type.value,
            "tags": tags or {},
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 100 values per metric
        if len(self._metrics[name]) > 100:
            self._metrics[name] = self._metrics[name][-100:]
        
        logger.debug(f"[NoOp] Metric: {name}={value}")
    
    async def record_event(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record event locally only."""
        self._events.append({
            "name": event_name,
            "properties": properties or {},
            "timestamp": timestamp or datetime.utcnow()
        })
        
        # Keep only last 1000 events
        if len(self._events) > 1000:
            self._events = self._events[-1000:]
        
        logger.debug(f"[NoOp] Event: {event_name}")
    
    async def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log locally only."""
        self._logs.append({
            "message": message,
            "level": level.value,
            "context": context or {},
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 1000 logs
        if len(self._logs) > 1000:
            self._logs = self._logs[-1000:]
        
        # Use Python logger
        log_func = getattr(logger, level.value, logger.info)
        log_func(f"[NoOp] {message}")
    
    async def start_trace(
        self,
        operation_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start local trace."""
        trace_id = str(uuid4())
        
        self._traces[trace_id] = {
            "operation": operation_name,
            "tags": tags or {},
            "start_time": datetime.utcnow()
        }
        
        logger.debug(f"[NoOp] Trace started: {trace_id}")
        return trace_id
    
    async def end_trace(
        self,
        trace_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """End local trace."""
        if trace_id in self._traces:
            trace = self._traces.pop(trace_id)
            duration = (datetime.utcnow() - trace["start_time"]).total_seconds()
            logger.debug(f"[NoOp] Trace ended: {trace_id} (duration: {duration}s)")
    
    async def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record error locally."""
        self._errors.append({
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 100 errors
        if len(self._errors) > 100:
            self._errors = self._errors[-100:]
        
        logger.error(f"[NoOp] Error: {error}")
    
    async def flush(self) -> None:
        """No-op flush."""
        logger.debug("[NoOp] Flush called (no action taken)")
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True
    
    async def get_metrics_summary(
        self,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get local metrics summary."""
        summary = {}
        
        for name, metrics in self._metrics.items():
            if metric_names and name not in metric_names:
                continue
            
            filtered_metrics = [
                m for m in metrics
                if (not start_time or m["timestamp"] >= start_time) and
                   (not end_time or m["timestamp"] <= end_time)
            ]
            
            if filtered_metrics:
                values = [m["value"] for m in filtered_metrics]
                summary[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1]
                }
        
        return summary