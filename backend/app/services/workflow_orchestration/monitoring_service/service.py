"""
Main Monitoring Service
Team C1 - Task C1.6

Main orchestration service that coordinates all monitoring components.
"""

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger

# Import Phase 1 & 2 components for metrics
from app.services.collection_flow import AuditLoggingService, CollectionFlowStateService

# Import Master Flow Orchestrator for integration
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession

# Import orchestration components for monitoring
from .alerts import AlertManager
from .analytics import AnalyticsEngine
from .health import HealthMonitor
from .metrics import MetricsCollector
from .models import MonitoringSession
from .progress import ProgressTracker

# Import modular components
from .types import MonitoringLevel

logger = get_logger(__name__)


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

        # Initialize modular components
        self.alert_manager = AlertManager()
        self.metrics_collector = MetricsCollector()
        self.progress_tracker = ProgressTracker()
        self.health_monitor = HealthMonitor()
        self.analytics_engine = AnalyticsEngine()

        # Monitoring state
        self.active_sessions: Dict[str, MonitoringSession] = {}

        # Configuration
        self.monitoring_interval_ms = 5000  # 5 seconds
        self.alert_evaluation_interval_ms = 10000  # 10 seconds
        self.health_check_interval_ms = 30000  # 30 seconds

        # Background task management
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

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
            for task in [
                self._monitoring_task,
                self._alert_task,
                self._health_task,
                self._cleanup_task,
            ]:
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
        alert_overrides: Optional[Dict[str, Any]] = None,
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

            logger.info(
                f"📊 Starting workflow monitoring: {workflow_id} (level: {monitoring_level})"
            )

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
                    "monitoring_level": monitoring_level,
                },
                metadata={
                    "created_by": self.context.user_id,
                    "tenant": self.context.client_account_id,
                    "engagement": self.context.engagement_id,
                },
            )

            # Add to active sessions
            self.active_sessions[session_id] = session

            # Initialize workflow progress tracking
            await self.progress_tracker.initialize_workflow_progress(
                workflow_id, custom_milestones or []
            )

            # Initialize performance metrics
            await self.metrics_collector.initialize_performance_metrics(workflow_id)

            # Setup workflow-specific alerts
            await self._setup_workflow_alerts(workflow_id, alert_overrides or {})

            # Log monitoring start
            await self.audit_logging.log_monitoring_event(
                workflow_id=workflow_id,
                event_type="monitoring_started",
                session_id=session_id,
                monitoring_level=monitoring_level,
            )

            logger.info(f"✅ Workflow monitoring started: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"❌ Failed to start workflow monitoring: {e}")
            raise FlowError(f"Monitoring start failed: {str(e)}")

    # Delegate methods to modular components

    async def get_workflow_progress(
        self, workflow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive workflow progress information"""
        return await self.progress_tracker.get_workflow_progress(
            workflow_id, include_details
        )

    async def get_performance_metrics(
        self,
        workflow_id: str,
        time_range_minutes: int = 60,
        metric_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for a workflow"""
        return await self.metrics_collector.get_performance_metrics(
            workflow_id, time_range_minutes, metric_types
        )

    async def get_health_status(
        self,
        workflow_id: Optional[str] = None,
        component_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get health status for workflows and components"""
        return await self.health_monitor.get_health_status(
            workflow_id, component_filter
        )

    async def get_active_alerts(
        self,
        workflow_id: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get active alerts with optional filtering"""
        return await self.alert_manager.get_active_alerts(
            workflow_id, severity_filter, limit
        )

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Acknowledge an active alert"""
        result = await self.alert_manager.acknowledge_alert(
            alert_id, acknowledged_by, notes, self.context.user_id
        )

        # Log acknowledgment
        await self.audit_logging.log_monitoring_event(
            workflow_id=None,  # Would be extracted from alert
            event_type="alert_acknowledged",
            alert_id=alert_id,
            acknowledged_by=acknowledged_by,
            notes=notes,
        )

        return result

    async def create_custom_alert(
        self,
        name: str,
        description: str,
        condition: str,
        threshold: Union[int, float],
        severity: str = "warning",
        evaluation_window_ms: int = 60000,
        workflow_id: Optional[str] = None,
    ) -> str:
        """Create a custom alert definition"""
        return await self.alert_manager.create_custom_alert(
            name,
            description,
            condition,
            threshold,
            severity,
            evaluation_window_ms,
            workflow_id,
            self.context.user_id,
        )

    async def get_monitoring_analytics(
        self, time_range_hours: int = 24, include_predictions: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive monitoring analytics"""
        return await self.analytics_engine.get_monitoring_analytics(
            time_range_hours, include_predictions
        )

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

    # Background monitoring loops

    async def _metrics_collection_loop(self):
        """Background loop for collecting metrics"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval_ms / 1000)

                # Collect metrics for all active workflows
                for workflow_id in list(self.progress_tracker.workflow_progress.keys()):
                    await self.metrics_collector.collect_workflow_metrics(workflow_id)

                # Update performance metrics
                await self.metrics_collector.update_performance_metrics()

                # Update progress tracking
                await self.progress_tracker.update_progress_tracking()

            except Exception as e:
                logger.error(f"❌ Metrics collection error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _alert_evaluation_loop(self):
        """Background loop for evaluating alerts"""
        while True:
            try:
                await asyncio.sleep(self.alert_evaluation_interval_ms / 1000)

                # Evaluate all alert definitions
                for alert_def in self.alert_manager.alert_definitions.values():
                    if alert_def.enabled:
                        await self.alert_manager.evaluate_alert_condition(alert_def)

                # Check for alert resolutions
                await self.alert_manager.check_alert_resolutions()

            except Exception as e:
                logger.error(f"❌ Alert evaluation error: {e}")
                await asyncio.sleep(30)

    async def _health_monitoring_loop(self):
        """Background loop for health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval_ms / 1000)

                # Perform health checks
                await self.health_monitor.perform_health_checks()

                # Update health status
                await self.health_monitor.update_health_status()

            except Exception as e:
                logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Background loop for cleanup tasks"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Clean up old metrics
                await self.metrics_collector.cleanup_old_metrics()

                # Clean up resolved alerts
                await self.alert_manager.cleanup_resolved_alerts()

                # Clean up completed sessions
                await self._cleanup_completed_sessions()

            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")

    # Helper methods

    async def _setup_workflow_alerts(
        self, workflow_id: str, alert_overrides: Dict[str, Any]
    ):
        """Setup workflow-specific alerts"""
        # Would implement workflow-specific alert configuration
        pass

    async def _cleanup_completed_sessions(self):
        """Clean up completed monitoring sessions"""
        completed_sessions = [
            session_id
            for session_id, session in self.active_sessions.items()
            if session.end_time
            and (datetime.utcnow() - session.end_time).total_seconds() > 3600  # 1 hour
        ]
        for session_id in completed_sessions:
            del self.active_sessions[session_id]
