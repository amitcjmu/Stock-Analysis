"""
Telemetry Service interface for abstracting monitoring and metrics collection.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Log levels for telemetry."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TelemetryService(ABC):
    """
    Abstract interface for telemetry collection.
    Supports metrics, logging, and tracing for both cloud and local deployments.
    """
    
    @abstractmethod
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags for the metric
        """
        pass
    
    @abstractmethod
    async def record_event(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record a custom event.
        
        Args:
            event_name: Name of the event
            properties: Event properties
            timestamp: Event timestamp (defaults to now)
        """
        pass
    
    @abstractmethod
    async def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a log message.
        
        Args:
            message: Log message
            level: Log level
            context: Additional context
        """
        pass
    
    @abstractmethod
    async def start_trace(
        self,
        operation_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Start a distributed trace.
        
        Args:
            operation_name: Name of the operation
            tags: Optional tags for the trace
            
        Returns:
            Trace ID
        """
        pass
    
    @abstractmethod
    async def end_trace(
        self,
        trace_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        End a distributed trace.
        
        Args:
            trace_id: ID of the trace to end
            success: Whether the operation succeeded
            error: Error message if failed
        """
        pass
    
    @abstractmethod
    async def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error with full context.
        
        Args:
            error: The exception that occurred
            context: Additional context
        """
        pass
    
    @abstractmethod
    async def flush(self) -> None:
        """
        Flush any buffered telemetry data.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the telemetry service is operational.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_metrics_summary(
        self,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Args:
            metric_names: Filter by metric names
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary of metric summaries
        """
        pass