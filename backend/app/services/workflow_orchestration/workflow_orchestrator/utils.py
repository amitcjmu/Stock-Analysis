"""
Workflow Utility Functions - Helper functions and configurations
Team C1 - Task C1.2

Contains utility functions for workflow configuration, scheduling,
quality thresholds, retry policies, and common helper methods.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.logging import get_logger

from .base import WorkflowConfiguration, WorkflowPriority
from ..collection_phase_engine import AutomationTier

logger = get_logger(__name__)


class WorkflowUtils:
    """Utility functions for workflow orchestration"""

    def __init__(self, orchestrator):
        """Initialize with reference to main orchestrator"""
        self.orchestrator = orchestrator

    def _create_workflow_configuration(
        self,
        automation_tier: str,
        priority: str,
        scheduling_config: Optional[Dict[str, Any]],
        client_requirements: Optional[Dict[str, Any]],
    ) -> WorkflowConfiguration:
        """Create workflow configuration from parameters"""
        return WorkflowConfiguration(
            automation_tier=AutomationTier(automation_tier),
            priority=WorkflowPriority(priority),
            timeout_minutes=(
                scheduling_config.get(
                    "timeout_minutes", self.orchestrator.default_timeout_minutes
                )
                if scheduling_config
                else self.orchestrator.default_timeout_minutes
            ),
            quality_thresholds=self._get_quality_thresholds(automation_tier),
            retry_config=self._get_retry_config(automation_tier),
            scheduling_config=scheduling_config or {},
            notification_config=(
                client_requirements.get("notifications", {})
                if client_requirements
                else {}
            ),
            metadata={
                "created_by": self.orchestrator.context.user_id,
                "tenant": self.orchestrator.context.client_account_id,
                "engagement": self.orchestrator.context.engagement_id,
            },
        )

    def _can_execute_immediately(self) -> bool:
        """Check if workflow can be executed immediately"""
        return (
            len(self.orchestrator.active_workflows)
            < self.orchestrator.max_concurrent_workflows
        )

    def _calculate_scheduled_time(
        self, scheduling_config: Optional[Dict[str, Any]]
    ) -> Optional[datetime]:
        """Calculate when workflow should be scheduled"""
        if not scheduling_config:
            return None

        if scheduling_config.get("execute_immediately", True):
            return None

        # Handle scheduled execution
        delay_minutes = scheduling_config.get("delay_minutes", 0)
        return datetime.utcnow() + timedelta(minutes=delay_minutes)

    def _get_quality_thresholds(self, automation_tier: str) -> Dict[str, float]:
        """Get quality thresholds based on automation tier"""
        thresholds = {
            "tier_1": {
                "overall": 0.95,
                "platform_detection": 0.95,
                "collection": 0.95,
                "synthesis": 0.95,
            },
            "tier_2": {
                "overall": 0.85,
                "platform_detection": 0.85,
                "collection": 0.85,
                "synthesis": 0.85,
            },
            "tier_3": {
                "overall": 0.75,
                "platform_detection": 0.75,
                "collection": 0.75,
                "synthesis": 0.75,
            },
            "tier_4": {
                "overall": 0.60,
                "platform_detection": 0.60,
                "collection": 0.60,
                "synthesis": 0.60,
            },
        }
        return thresholds.get(automation_tier, thresholds["tier_2"])

    def _get_retry_config(self, automation_tier: str) -> Dict[str, Any]:
        """Get retry configuration based on automation tier"""
        return {
            "max_retries": 3,
            "base_delay_minutes": 5,
            "backoff_multiplier": 2,
            "max_delay_minutes": 30,
        }
