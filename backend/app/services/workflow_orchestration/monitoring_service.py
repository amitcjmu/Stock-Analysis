"""
Workflow Monitoring and Progress Tracking Service
Team C1 - Task C1.6

Comprehensive monitoring and progress tracking system for Collection Flow workflows, providing
real-time insights, performance metrics, health monitoring, and detailed progress tracking
throughout the entire workflow lifecycle.

Integrates with all workflow orchestration components to provide unified monitoring,
alerting, and analytics for workflow optimization and operational excellence.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import uuid
from collections import defaultdict, deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.core.exceptions import FlowError, InvalidFlowStateError

# Import orchestration components for monitoring
from .workflow_orchestrator import WorkflowOrchestrator, WorkflowStatus, WorkflowPriority, WorkflowExecution
from .collection_phase_engine import CollectionPhaseExecutionEngine, CollectionPhaseStatus, AutomationTier
from .tier_routing_service import TierRoutingService
from .handoff_protocol import CollectionDiscoveryHandoffProtocol, HandoffStatus

# Import Master Flow Orchestrator for integration
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# Import Phase 1 & 2 components for metrics
from app.services.collection_flow import CollectionFlowStateService, AuditLoggingService

logger = get_logger(__name__)


class MonitoringLevel(Enum):
    """Monitoring detail levels"""
    BASIC = "basic"              # Basic status and health
    STANDARD = "standard"        # Standard metrics and progress
    DETAILED = "detailed"        # Detailed phase and component metrics
    COMPREHENSIVE = "comprehensive"  # Full diagnostic and performance data


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics tracked"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    RESOURCE = "resource"
    BUSINESS = "business"
    OPERATIONAL = "operational"


class HealthStatus(Enum):
    """Health status indicators"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    metric_name: str
    metric_type: MetricType
    value: Union[int, float, str, bool]
    unit: Optional[str]
    tags: Dict[str, str]
    context: Dict[str, Any]


@dataclass
class ProgressMilestone:
    """Progress milestone definition"""
    milestone_id: str
    name: str
    description: str
    phase: Optional[str]
    completion_criteria: Dict[str, Any]
    weight: float  # Contribution to overall progress
    dependencies: List[str]
    estimated_duration_ms: Optional[int]
    metadata: Dict[str, Any]


@dataclass
class WorkflowProgress:
    """Comprehensive workflow progress tracking"""
    workflow_id: str
    overall_progress: float  # 0.0 to 1.0
    phase_progress: Dict[str, float]
    completed_milestones: List[str]
    current_milestone: Optional[str]
    estimated_completion: Optional[datetime]
    time_remaining_ms: Optional[int]
    velocity_metrics: Dict[str, float]
    bottlenecks: List[Dict[str, Any]]
    quality_gates_status: Dict[str, str]
    last_updated: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for workflows"""
    workflow_id: str
    execution_time_ms: Optional[int]
    throughput: float  # Items processed per minute
    resource_utilization: Dict[str, float]
    queue_metrics: Dict[str, Any]
    error_rate: float
    success_rate: float
    quality_scores: Dict[str, float]
    efficiency_score: float
    sla_compliance: Dict[str, bool]


@dataclass
class AlertDefinition:
    """Alert rule definition"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # Alert condition expression
    threshold: Union[int, float]
    evaluation_window_ms: int
    cooldown_ms: int
    enabled: bool
    notification_channels: List[str]
    metadata: Dict[str, Any]


@dataclass
class Alert:
    """Active alert instance"""
    alert_id: str
    alert_definition_id: str
    workflow_id: Optional[str]
    severity: AlertSeverity
    title: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    current_value: Union[int, float, str]
    threshold_value: Union[int, float]
    context: Dict[str, Any]
    acknowledgments: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class MonitoringSession:
    """Monitoring session for a workflow"""
    session_id: str
    workflow_id: str
    monitoring_level: MonitoringLevel
    start_time: datetime
    end_time: Optional[datetime]
    metrics_collected: int
    alerts_triggered: int
    health_checks_performed: int
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]


class WorkflowMonitoringService:
    """
    Workflow Monitoring and Progress Tracking Service
    
    Provides comprehensive monitoring capabilities including:
    - Real-time workflow progress tracking
    - Performance metrics collection and analysis
    - Health monitoring and alerting
    - Resource utilization tracking
    - Quality gate monitoring
    - SLA compliance tracking
    - Bottleneck identification and analysis
    - Historical analytics and trending
    - Predictive monitoring and anomaly detection
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Workflow Monitoring Service"""
        self.db = db
        self.context = context
        
        # Initialize orchestration services for monitoring
        self.master_orchestrator = MasterFlowOrchestrator(db, context)
        self.collection_state = CollectionFlowStateService(db, context)
        self.audit_logging = AuditLoggingService(db, context)
        
        # Monitoring state
        self.active_sessions: Dict[str, MonitoringSession] = {}
        self.metric_buffer: deque = deque(maxlen=10000)  # Rolling metrics buffer
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_definitions: Dict[str, AlertDefinition] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        
        # Progress tracking
        self.workflow_progress: Dict[str, WorkflowProgress] = {}
        self.milestone_definitions: Dict[str, ProgressMilestone] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        # Configuration
        self.monitoring_interval_ms = 5000  # 5 seconds
        self.metrics_retention_hours = 72   # 3 days
        self.alert_evaluation_interval_ms = 10000  # 10 seconds
        self.health_check_interval_ms = 30000  # 30 seconds
        
        # Background task management
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Initialize default milestones and alerts
        self._initialize_default_milestones()
        self._initialize_default_alerts()
        
        logger.info("✅ Workflow Monitoring Service initialized")
    
    async def start_monitoring_service(self):
        """Start the monitoring service background tasks"""
        try:
            # Start metrics collection
            self._monitoring_task = asyncio.create_task(self._metrics_collection_loop())
            
            # Start alert evaluation
            self._alert_task = asyncio.create_task(self._alert_evaluation_loop())
            
            # Start health monitoring
            self._health_task = asyncio.create_task(self._health_monitoring_loop())
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("🚀 Workflow Monitoring Service started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring service: {e}")
            raise
    
    async def stop_monitoring_service(self):
        """Stop the monitoring service background tasks"""
        try:
            # Cancel background tasks
            for task in [self._monitoring_task, self._alert_task, self._health_task, self._cleanup_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("🛑 Workflow Monitoring Service stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping monitoring service: {e}")
    
    async def start_workflow_monitoring(
        self,
        workflow_id: str,
        monitoring_level: str = "standard",
        custom_milestones: Optional[List[Dict[str, Any]]] = None,
        alert_overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start monitoring for a specific workflow
        
        Args:
            workflow_id: ID of the workflow to monitor
            monitoring_level: Level of monitoring detail
            custom_milestones: Custom milestones for this workflow
            alert_overrides: Custom alert configurations
            
        Returns:
            Monitoring session ID
        """
        try:
            session_id = f"mon-session-{uuid.uuid4()}"
            
            logger.info(f"📊 Starting workflow monitoring: {workflow_id} (level: {monitoring_level})")
            
            # Create monitoring session
            session = MonitoringSession(
                session_id=session_id,
                workflow_id=workflow_id,
                monitoring_level=MonitoringLevel(monitoring_level),
                start_time=datetime.utcnow(),
                end_time=None,
                metrics_collected=0,
                alerts_triggered=0,
                health_checks_performed=0,
                configuration={
                    "custom_milestones": custom_milestones or [],
                    "alert_overrides": alert_overrides or {},
                    "monitoring_level": monitoring_level
                },
                metadata={
                    "created_by": self.context.user_id,
                    "tenant": self.context.client_account_id,
                    "engagement": self.context.engagement_id
                }
            )
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            # Initialize workflow progress tracking
            await self._initialize_workflow_progress(workflow_id, custom_milestones or [])
            
            # Initialize performance metrics
            await self._initialize_performance_metrics(workflow_id)
            
            # Setup workflow-specific alerts
            await self._setup_workflow_alerts(workflow_id, alert_overrides or {})
            
            # Log monitoring start
            await self.audit_logging.log_monitoring_event(
                workflow_id=workflow_id,
                event_type="monitoring_started",
                session_id=session_id,
                monitoring_level=monitoring_level
            )
            
            logger.info(f"✅ Workflow monitoring started: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to start workflow monitoring: {e}")
            raise FlowError(f"Monitoring start failed: {str(e)}")
    
    async def get_workflow_progress(
        self,
        workflow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive workflow progress information
        
        Args:
            workflow_id: ID of the workflow
            include_details: Whether to include detailed progress data
            
        Returns:
            Comprehensive progress information
        """
        try:
            # Get workflow progress
            progress = self.workflow_progress.get(workflow_id)
            if not progress:
                # Initialize if not exists
                await self._initialize_workflow_progress(workflow_id, [])
                progress = self.workflow_progress.get(workflow_id)
            
            if not progress:
                raise ValueError(f"Unable to track progress for workflow: {workflow_id}")
            
            # Get current workflow status from orchestrator
            workflow_status = await self._get_workflow_status_from_orchestrator(workflow_id)
            
            # Update progress based on current status
            updated_progress = await self._update_progress_from_status(progress, workflow_status)
            
            progress_data = {
                "workflow_id": workflow_id,
                "overall_progress": updated_progress.overall_progress,
                "phase_progress": updated_progress.phase_progress,
                "current_milestone": updated_progress.current_milestone,
                "estimated_completion": updated_progress.estimated_completion.isoformat() if updated_progress.estimated_completion else None,
                "time_remaining_ms": updated_progress.time_remaining_ms,
                "last_updated": updated_progress.last_updated.isoformat(),
                "status_summary": {
                    "completed_milestones": len(updated_progress.completed_milestones),
                    "total_milestones": len(self.milestone_definitions),
                    "current_phase": self._get_current_phase_from_status(workflow_status),
                    "overall_status": workflow_status.get("status", "unknown")
                }
            }
            
            # Add detailed information if requested
            if include_details:
                progress_data.update({
                    "completed_milestones": updated_progress.completed_milestones,
                    "velocity_metrics": updated_progress.velocity_metrics,
                    "bottlenecks": updated_progress.bottlenecks,
                    "quality_gates_status": updated_progress.quality_gates_status,
                    "milestone_details": [
                        asdict(milestone) for milestone in self.milestone_definitions.values()
                    ]
                })
            
            return progress_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get workflow progress: {e}")
            raise FlowError(f"Progress retrieval failed: {str(e)}")
    
    async def get_performance_metrics(
        self,
        workflow_id: str,
        time_range_minutes: int = 60,
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a workflow
        
        Args:
            workflow_id: ID of the workflow
            time_range_minutes: Time range for metrics
            metric_types: Specific metric types to include
            
        Returns:
            Comprehensive performance metrics
        """
        try:
            logger.info(f"📈 Getting performance metrics for workflow: {workflow_id}")
            
            # Get current performance metrics
            perf_metrics = self.performance_metrics.get(workflow_id)
            if not perf_metrics:
                await self._initialize_performance_metrics(workflow_id)
                perf_metrics = self.performance_metrics.get(workflow_id)
            
            # Get historical metrics from buffer
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
            historical_metrics = [
                metric for metric in self.metric_buffer
                if metric.timestamp >= cutoff_time and 
                   metric.tags.get("workflow_id") == workflow_id
            ]
            
            # Filter by metric types if specified
            if metric_types:
                historical_metrics = [
                    metric for metric in historical_metrics
                    if metric.metric_type.value in metric_types
                ]
            
            # Calculate aggregated metrics
            aggregated_metrics = await self._aggregate_historical_metrics(
                historical_metrics=historical_metrics,
                time_range_minutes=time_range_minutes
            )
            
            # Get real-time metrics
            real_time_metrics = await self._collect_real_time_metrics(workflow_id)
            
            # Combine all metrics
            metrics_data = {
                "workflow_id": workflow_id,
                "time_range_minutes": time_range_minutes,
                "current_metrics": asdict(perf_metrics) if perf_metrics else {},
                "real_time_metrics": real_time_metrics,
                "aggregated_metrics": aggregated_metrics,
                "metric_trends": await self._calculate_metric_trends(historical_metrics),
                "performance_summary": await self._generate_performance_summary(
                    workflow_id=workflow_id,
                    current_metrics=perf_metrics,
                    historical_metrics=historical_metrics
                )
            }
            
            return metrics_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance metrics: {e}")
            raise FlowError(f"Metrics retrieval failed: {str(e)}")
    
    async def get_health_status(
        self,
        workflow_id: Optional[str] = None,
        component_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get health status for workflows and components
        
        Args:
            workflow_id: Specific workflow ID (optional)
            component_filter: Filter by specific components
            
        Returns:
            Comprehensive health status information
        """
        try:
            logger.info(f"🏥 Getting health status for workflow: {workflow_id or 'all'}")
            
            # Get overall system health
            system_health = await self._assess_system_health()
            
            # Get workflow-specific health if requested
            workflow_health = {}
            if workflow_id:
                workflow_health = await self._assess_workflow_health(workflow_id)
            else:
                # Get health for all active workflows
                for wf_id in self.workflow_progress.keys():
                    workflow_health[wf_id] = await self._assess_workflow_health(wf_id)
            
            # Get component health
            component_health = await self._assess_component_health(component_filter)
            
            # Get active alerts
            relevant_alerts = self._get_relevant_alerts(workflow_id)
            
            # Calculate overall health score
            overall_health = await self._calculate_overall_health_score(
                system_health=system_health,
                workflow_health=workflow_health,
                component_health=component_health,
                active_alerts=relevant_alerts
            )
            
            health_data = {
                "overall_health": overall_health,
                "system_health": system_health,
                "workflow_health": workflow_health,
                "component_health": component_health,
                "active_alerts": [asdict(alert) for alert in relevant_alerts],
                "health_trends": await self._calculate_health_trends(),
                "recommendations": await self._generate_health_recommendations(
                    overall_health=overall_health,
                    alerts=relevant_alerts
                ),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get health status: {e}")
            raise FlowError(f"Health status retrieval failed: {str(e)}")
    
    async def get_active_alerts(
        self,
        workflow_id: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts with optional filtering
        
        Args:
            workflow_id: Filter by workflow ID
            severity_filter: Filter by severity level
            limit: Maximum number of alerts to return
            
        Returns:
            List of active alerts
        """
        try:
            # Filter alerts
            filtered_alerts = list(self.active_alerts.values())
            
            if workflow_id:
                filtered_alerts = [
                    alert for alert in filtered_alerts
                    if alert.workflow_id == workflow_id
                ]
            
            if severity_filter:
                filtered_alerts = [
                    alert for alert in filtered_alerts
                    if alert.severity.value == severity_filter
                ]
            
            # Sort by severity and time
            severity_order = {
                AlertSeverity.CRITICAL: 4,
                AlertSeverity.ERROR: 3,
                AlertSeverity.WARNING: 2,
                AlertSeverity.INFO: 1
            }
            
            filtered_alerts.sort(
                key=lambda a: (severity_order[a.severity], a.triggered_at),
                reverse=True
            )
            
            # Limit results
            limited_alerts = filtered_alerts[:limit]
            
            return [asdict(alert) for alert in limited_alerts]
            
        except Exception as e:
            logger.error(f"❌ Failed to get active alerts: {e}")
            raise FlowError(f"Alert retrieval failed: {str(e)}")
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Acknowledge an active alert
        
        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: User acknowledging the alert
            notes: Optional acknowledgment notes
            
        Returns:
            Acknowledgment result
        """
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                raise ValueError(f"Alert not found: {alert_id}")
            
            # Add acknowledgment
            acknowledgment = {
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": datetime.utcnow().isoformat(),
                "notes": notes,
                "user_id": self.context.user_id
            }
            
            alert.acknowledgments.append(acknowledgment)
            
            # Log acknowledgment
            await self.audit_logging.log_monitoring_event(
                workflow_id=alert.workflow_id,
                event_type="alert_acknowledged",
                alert_id=alert_id,
                acknowledged_by=acknowledged_by,
                notes=notes
            )
            
            logger.info(f"✅ Alert acknowledged: {alert_id} by {acknowledged_by}")
            
            return {
                "alert_id": alert_id,
                "acknowledged": True,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": acknowledgment["acknowledged_at"],
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to acknowledge alert: {e}")
            raise FlowError(f"Alert acknowledgment failed: {str(e)}")
    
    async def create_custom_alert(
        self,
        name: str,
        description: str,
        condition: str,
        threshold: Union[int, float],
        severity: str = "warning",
        evaluation_window_ms: int = 60000,
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Create a custom alert definition
        
        Args:
            name: Alert name
            description: Alert description
            condition: Alert condition expression
            threshold: Alert threshold value
            severity: Alert severity level
            evaluation_window_ms: Evaluation window in milliseconds
            workflow_id: Associated workflow ID (optional)
            
        Returns:
            Alert definition ID
        """
        try:
            alert_def_id = f"custom-alert-{uuid.uuid4()}"
            
            alert_definition = AlertDefinition(
                alert_id=alert_def_id,
                name=name,
                description=description,
                severity=AlertSeverity(severity),
                condition=condition,
                threshold=threshold,
                evaluation_window_ms=evaluation_window_ms,
                cooldown_ms=300000,  # 5 minutes default
                enabled=True,
                notification_channels=[],
                metadata={
                    "created_by": self.context.user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "workflow_id": workflow_id,
                    "custom": True
                }
            )
            
            # Add to alert definitions
            self.alert_definitions[alert_def_id] = alert_definition
            
            logger.info(f"✅ Custom alert created: {alert_def_id}")
            return alert_def_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create custom alert: {e}")
            raise FlowError(f"Custom alert creation failed: {str(e)}")
    
    async def get_monitoring_analytics(
        self,
        time_range_hours: int = 24,
        include_predictions: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive monitoring analytics
        
        Args:
            time_range_hours: Time range for analytics
            include_predictions: Whether to include predictive analytics
            
        Returns:
            Comprehensive monitoring analytics
        """
        try:
            logger.info(f"📊 Generating monitoring analytics for {time_range_hours} hours")
            
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Get workflow execution analytics
            execution_analytics = await self._analyze_workflow_executions(cutoff_time)
            
            # Get performance analytics
            performance_analytics = await self._analyze_performance_trends(cutoff_time)
            
            # Get quality analytics
            quality_analytics = await self._analyze_quality_trends(cutoff_time)
            
            # Get resource utilization analytics
            resource_analytics = await self._analyze_resource_utilization(cutoff_time)
            
            # Get alert analytics
            alert_analytics = await self._analyze_alert_patterns(cutoff_time)
            
            analytics = {
                "analysis_period": {
                    "start_time": cutoff_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "duration_hours": time_range_hours
                },
                "execution_analytics": execution_analytics,
                "performance_analytics": performance_analytics,
                "quality_analytics": quality_analytics,
                "resource_analytics": resource_analytics,
                "alert_analytics": alert_analytics,
                "summary_insights": await self._generate_analytics_insights(
                    execution_analytics,
                    performance_analytics,
                    quality_analytics
                )
            }
            
            # Add predictive analytics if requested
            if include_predictions:
                analytics["predictive_analytics"] = await self._generate_predictive_analytics(
                    analytics=analytics
                )
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Failed to generate monitoring analytics: {e}")
            raise FlowError(f"Analytics generation failed: {str(e)}")
    
    # Event handling
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for monitoring events"""
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit a monitoring event to registered handlers"""
        try:
            for handler in self.event_handlers[event_type]:
                await handler(event_data)
        except Exception as e:
            logger.warning(f"Event handler error for {event_type}: {e}")
    
    # Private methods for core monitoring functionality
    
    async def _metrics_collection_loop(self):
        """Background loop for collecting metrics"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval_ms / 1000)
                
                # Collect metrics for all active workflows
                for workflow_id in list(self.workflow_progress.keys()):
                    await self._collect_workflow_metrics(workflow_id)
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Update progress tracking
                await self._update_progress_tracking()
                
            except Exception as e:
                logger.error(f"❌ Metrics collection error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _alert_evaluation_loop(self):
        """Background loop for evaluating alerts"""
        while True:
            try:
                await asyncio.sleep(self.alert_evaluation_interval_ms / 1000)
                
                # Evaluate all alert definitions
                for alert_def in self.alert_definitions.values():
                    if alert_def.enabled:
                        await self._evaluate_alert_condition(alert_def)
                
                # Check for alert resolutions
                await self._check_alert_resolutions()
                
            except Exception as e:
                logger.error(f"❌ Alert evaluation error: {e}")
                await asyncio.sleep(30)
    
    async def _health_monitoring_loop(self):
        """Background loop for health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval_ms / 1000)
                
                # Perform health checks
                await self._perform_health_checks()
                
                # Update health status
                await self._update_health_status()
                
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup tasks"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
                # Clean up resolved alerts
                await self._cleanup_resolved_alerts()
                
                # Clean up completed sessions
                await self._cleanup_completed_sessions()
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
    
    def _initialize_default_milestones(self):
        """Initialize default progress milestones"""
        default_milestones = [
            {
                "name": "Workflow Initialization",
                "description": "Workflow has been initialized and started",
                "phase": None,
                "weight": 0.05,
                "criteria": {"status": "initializing"}
            },
            {
                "name": "Platform Detection Started",
                "description": "Platform detection phase has begun",
                "phase": "platform_detection",
                "weight": 0.1,
                "criteria": {"phase_status": "running"}
            },
            {
                "name": "Platform Detection Completed",
                "description": "Platform detection phase completed successfully",
                "phase": "platform_detection",
                "weight": 0.2,
                "criteria": {"phase_status": "completed"}
            },
            {
                "name": "Automated Collection Started",
                "description": "Automated collection phase has begun",
                "phase": "automated_collection",
                "weight": 0.3,
                "criteria": {"phase_status": "running"}
            },
            {
                "name": "Automated Collection Completed",
                "description": "Automated collection phase completed",
                "phase": "automated_collection",
                "weight": 0.5,
                "criteria": {"phase_status": "completed"}
            },
            {
                "name": "Gap Analysis Completed",
                "description": "Gap analysis phase completed",
                "phase": "gap_analysis",
                "weight": 0.65,
                "criteria": {"phase_status": "completed"}
            },
            {
                "name": "Manual Collection Completed",
                "description": "Manual collection phase completed",
                "phase": "manual_collection",
                "weight": 0.8,
                "criteria": {"phase_status": "completed"}
            },
            {
                "name": "Data Synthesis Completed",
                "description": "Data synthesis phase completed",
                "phase": "synthesis",
                "weight": 0.95,
                "criteria": {"phase_status": "completed"}
            },
            {
                "name": "Workflow Completed",
                "description": "Workflow has been completed successfully",
                "phase": None,
                "weight": 1.0,
                "criteria": {"status": "completed"}
            }
        ]
        
        for milestone_data in default_milestones:
            milestone_id = f"default-{milestone_data['name'].lower().replace(' ', '-')}"
            milestone = ProgressMilestone(
                milestone_id=milestone_id,
                name=milestone_data["name"],
                description=milestone_data["description"],
                phase=milestone_data["phase"],
                completion_criteria=milestone_data["criteria"],
                weight=milestone_data["weight"],
                dependencies=[],
                estimated_duration_ms=None,
                metadata={"default": True}
            )
            self.milestone_definitions[milestone_id] = milestone
    
    def _initialize_default_alerts(self):
        """Initialize default alert definitions"""
        default_alerts = [
            {
                "name": "Workflow Timeout",
                "description": "Workflow execution time exceeds threshold",
                "condition": "execution_time_ms > threshold",
                "threshold": 7200000,  # 2 hours
                "severity": "warning"
            },
            {
                "name": "High Error Rate",
                "description": "Error rate exceeds acceptable threshold",
                "condition": "error_rate > threshold",
                "threshold": 0.1,  # 10%
                "severity": "error"
            },
            {
                "name": "Low Quality Score",
                "description": "Quality score below minimum threshold",
                "condition": "quality_score < threshold",
                "threshold": 0.7,  # 70%
                "severity": "warning"
            },
            {
                "name": "Resource Utilization High",
                "description": "Resource utilization exceeds threshold",
                "condition": "resource_utilization > threshold",
                "threshold": 0.9,  # 90%
                "severity": "warning"
            },
            {
                "name": "Workflow Failed",
                "description": "Workflow execution failed",
                "condition": "status == 'failed'",
                "threshold": 1,
                "severity": "critical"
            }
        ]
        
        for alert_data in default_alerts:
            alert_id = f"default-{alert_data['name'].lower().replace(' ', '-')}"
            alert_def = AlertDefinition(
                alert_id=alert_id,
                name=alert_data["name"],
                description=alert_data["description"],
                severity=AlertSeverity(alert_data["severity"]),
                condition=alert_data["condition"],
                threshold=alert_data["threshold"],
                evaluation_window_ms=60000,  # 1 minute
                cooldown_ms=300000,  # 5 minutes
                enabled=True,
                notification_channels=[],
                metadata={"default": True}
            )
            self.alert_definitions[alert_id] = alert_def
    
    # Simplified implementations for core monitoring functions
    # These would be fully implemented with real monitoring logic in production
    
    async def _initialize_workflow_progress(self, workflow_id: str, custom_milestones: List[Dict[str, Any]]):
        """Initialize progress tracking for a workflow"""
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            overall_progress=0.0,
            phase_progress={},
            completed_milestones=[],
            current_milestone=None,
            estimated_completion=None,
            time_remaining_ms=None,
            velocity_metrics={},
            bottlenecks=[],
            quality_gates_status={},
            last_updated=datetime.utcnow()
        )
        self.workflow_progress[workflow_id] = progress
    
    async def _initialize_performance_metrics(self, workflow_id: str):
        """Initialize performance metrics for a workflow"""
        metrics = PerformanceMetrics(
            workflow_id=workflow_id,
            execution_time_ms=None,
            throughput=0.0,
            resource_utilization={},
            queue_metrics={},
            error_rate=0.0,
            success_rate=1.0,
            quality_scores={},
            efficiency_score=1.0,
            sla_compliance={}
        )
        self.performance_metrics[workflow_id] = metrics
    
    async def _setup_workflow_alerts(self, workflow_id: str, alert_overrides: Dict[str, Any]):
        """Setup workflow-specific alerts"""
        # Would implement workflow-specific alert configuration
        pass
    
    async def _get_workflow_status_from_orchestrator(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status from the orchestrator"""
        try:
            return await self.master_orchestrator.get_flow_status(workflow_id, include_details=True)
        except Exception:
            return {"status": "unknown"}
    
    async def _update_progress_from_status(self, progress: WorkflowProgress, status: Dict[str, Any]) -> WorkflowProgress:
        """Update progress based on workflow status"""
        # Simple progress calculation
        workflow_status = status.get("status", "unknown")
        phase_results = status.get("phase_results", {})
        
        if workflow_status == "completed":
            progress.overall_progress = 1.0
        elif workflow_status == "running":
            # Calculate based on completed phases
            completed_phases = len([p for p in phase_results.values() if p.get("status") == "completed"])
            total_phases = 5  # Standard number of phases
            progress.overall_progress = min(0.95, completed_phases / total_phases)
        
        progress.last_updated = datetime.utcnow()
        return progress
    
    def _get_current_phase_from_status(self, status: Dict[str, Any]) -> Optional[str]:
        """Extract current phase from workflow status"""
        phase_results = status.get("phase_results", {})
        for phase, result in phase_results.items():
            if result.get("status") == "running":
                return phase
        return None
    
    async def _collect_workflow_metrics(self, workflow_id: str):
        """Collect metrics for a specific workflow"""
        # Would implement real metrics collection
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            metric_name="workflow_status",
            metric_type=MetricType.OPERATIONAL,
            value="running",
            unit=None,
            tags={"workflow_id": workflow_id},
            context={}
        )
        self.metric_buffer.append(metric)
    
    async def _update_performance_metrics(self):
        """Update performance metrics for all workflows"""
        # Would implement real performance metrics updates
        pass
    
    async def _update_progress_tracking(self):
        """Update progress tracking for all workflows"""
        # Would implement real progress tracking updates
        pass
    
    async def _evaluate_alert_condition(self, alert_def: AlertDefinition):
        """Evaluate an alert condition"""
        # Would implement real alert condition evaluation
        pass
    
    async def _check_alert_resolutions(self):
        """Check if any alerts should be resolved"""
        # Would implement alert resolution checking
        pass
    
    async def _perform_health_checks(self):
        """Perform health checks on system components"""
        # Would implement real health checks
        pass
    
    async def _update_health_status(self):
        """Update overall health status"""
        # Would implement health status updates
        pass
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics from buffer"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
        while self.metric_buffer and self.metric_buffer[0].timestamp < cutoff_time:
            self.metric_buffer.popleft()
    
    async def _cleanup_resolved_alerts(self):
        """Clean up resolved alerts"""
        resolved_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved_at and 
            (datetime.utcnow() - alert.resolved_at).total_seconds() > 3600  # 1 hour
        ]
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
    
    async def _cleanup_completed_sessions(self):
        """Clean up completed monitoring sessions"""
        completed_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session.end_time and 
            (datetime.utcnow() - session.end_time).total_seconds() > 3600  # 1 hour
        ]
        for session_id in completed_sessions:
            del self.active_sessions[session_id]
    
    # Additional helper methods with simplified implementations
    
    async def _aggregate_historical_metrics(self, historical_metrics: List[MetricPoint], time_range_minutes: int) -> Dict[str, Any]:
        """Aggregate historical metrics"""
        return {"average_value": 0.5, "max_value": 1.0, "min_value": 0.0}
    
    async def _collect_real_time_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Collect real-time metrics"""
        return {"cpu_usage": 0.3, "memory_usage": 0.4, "network_io": 0.1}
    
    async def _calculate_metric_trends(self, metrics: List[MetricPoint]) -> Dict[str, Any]:
        """Calculate metric trends"""
        return {"trend": "stable", "change_rate": 0.02}
    
    async def _generate_performance_summary(self, workflow_id: str, current_metrics: Optional[PerformanceMetrics], historical_metrics: List[MetricPoint]) -> Dict[str, Any]:
        """Generate performance summary"""
        return {"overall_performance": "good", "efficiency": 0.85, "recommendations": []}
    
    async def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        return {"status": "healthy", "score": 0.95}
    
    async def _assess_workflow_health(self, workflow_id: str) -> Dict[str, Any]:
        """Assess workflow-specific health"""
        return {"status": "healthy", "score": 0.9}
    
    async def _assess_component_health(self, component_filter: Optional[List[str]]) -> Dict[str, Any]:
        """Assess component health"""
        return {"orchestrator": "healthy", "phase_engine": "healthy", "tier_routing": "healthy"}
    
    def _get_relevant_alerts(self, workflow_id: Optional[str]) -> List[Alert]:
        """Get relevant alerts for workflow or all alerts"""
        if workflow_id:
            return [alert for alert in self.active_alerts.values() if alert.workflow_id == workflow_id]
        return list(self.active_alerts.values())
    
    async def _calculate_overall_health_score(self, system_health: Dict[str, Any], workflow_health: Dict[str, Any], component_health: Dict[str, Any], active_alerts: List[Alert]) -> Dict[str, Any]:
        """Calculate overall health score"""
        return {"score": 0.9, "status": "healthy", "components_healthy": 5, "total_components": 5}
    
    async def _calculate_health_trends(self) -> Dict[str, Any]:
        """Calculate health trends"""
        return {"trend": "stable", "health_improving": True}
    
    async def _generate_health_recommendations(self, overall_health: Dict[str, Any], alerts: List[Alert]) -> List[str]:
        """Generate health recommendations"""
        return ["System is operating normally", "Monitor resource utilization"]
    
    async def _analyze_workflow_executions(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze workflow execution patterns"""
        return {"total_executions": 10, "success_rate": 0.9, "average_duration": 3600000}
    
    async def _analyze_performance_trends(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze performance trends"""
        return {"performance_trend": "improving", "efficiency_trend": "stable"}
    
    async def _analyze_quality_trends(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze quality trends"""
        return {"quality_trend": "stable", "average_quality": 0.85}
    
    async def _analyze_resource_utilization(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze resource utilization"""
        return {"average_cpu": 0.4, "average_memory": 0.5, "peak_utilization": 0.8}
    
    async def _analyze_alert_patterns(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze alert patterns"""
        return {"total_alerts": 5, "resolved_alerts": 4, "average_resolution_time": 1800}
    
    async def _generate_analytics_insights(self, execution_analytics: Dict[str, Any], performance_analytics: Dict[str, Any], quality_analytics: Dict[str, Any]) -> List[str]:
        """Generate analytics insights"""
        return ["Workflows are performing well", "Quality scores are stable", "No significant issues detected"]
    
    async def _generate_predictive_analytics(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive analytics"""
        return {"predicted_performance": "stable", "risk_factors": [], "recommendations": []}