"""
Modular Workflow Monitoring Service
Team C1 - Task C1.6

A modularized workflow monitoring and progress tracking system providing
comprehensive monitoring capabilities for Collection Flow workflows.

Components:
- Types and Enums: Common type definitions and enumerations
- Models: Data models and dataclasses for monitoring data
- Alerts: Alert management, evaluation, and acknowledgment
- Metrics: Metrics collection, aggregation, and analysis
- Progress: Workflow progress tracking and milestone management
- Health: Health monitoring and status assessment
- Analytics: Analytics generation and insights
- Service: Main orchestration service coordinating all components

Usage:
    from app.services.workflow_orchestration.monitoring_service import WorkflowMonitoringService
    
    # Initialize service
    monitoring_service = WorkflowMonitoringService(db, context)
    
    # Start monitoring
    session_id = await monitoring_service.start_workflow_monitoring(workflow_id)
"""

# Import all public interfaces for backward compatibility
from .types import MonitoringLevel, AlertSeverity, MetricType, HealthStatus
from .models import (
    MetricPoint, ProgressMilestone, WorkflowProgress, PerformanceMetrics,
    AlertDefinition, Alert, MonitoringSession
)
from .alerts import AlertManager
from .metrics import MetricsCollector
from .progress import ProgressTracker
from .health import HealthMonitor
from .analytics import AnalyticsEngine
from .service import WorkflowMonitoringService

# Export all public interfaces
__all__ = [
    # Main service
    'WorkflowMonitoringService',
    
    # Types and enums
    'MonitoringLevel',
    'AlertSeverity', 
    'MetricType',
    'HealthStatus',
    
    # Data models
    'MetricPoint',
    'ProgressMilestone',
    'WorkflowProgress',
    'PerformanceMetrics',
    'AlertDefinition',
    'Alert',
    'MonitoringSession',
    
    # Component managers
    'AlertManager',
    'MetricsCollector',
    'ProgressTracker',
    'HealthMonitor',
    'AnalyticsEngine'
]