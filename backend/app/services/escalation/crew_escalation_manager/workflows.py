"""
Escalation workflow management for high-level coordination and escalation startup.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import BackgroundTasks

from .base import logger
from .exceptions import EscalationError
from .triggers import EscalationTriggerManager
from .policies import EscalationPolicyManager


class EscalationWorkflowManager:
    """
    Manages high-level escalation workflows, coordination, and startup processes.
    """

    def __init__(
        self,
        active_escalations: Dict[str, Dict[str, Any]],
        trigger_manager: EscalationTriggerManager,
        policy_manager: EscalationPolicyManager,
        execution_handler: Any,
        notification_manager: Any,
    ):
        """Initialize with managers and handlers."""
        self.active_escalations = active_escalations
        self.trigger_manager = trigger_manager
        self.policy_manager = policy_manager
        self.execution_handler = execution_handler
        self.notification_manager = notification_manager

    async def start_crew_escalation(
        self,
        crew_type: str,
        escalation_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start a crew escalation for Think button functionality."""
        try:
            # Validate escalation context
            page = escalation_context.get("page", "unknown")
            agent_id = escalation_context.get("agent_id", "unknown")

            if not self.trigger_manager.validate_escalation_context(
                page, agent_id, escalation_context
            ):
                raise EscalationError("Invalid escalation context provided")

            # Check if escalation should be triggered
            if not self.trigger_manager.should_escalate_to_crew(
                page, agent_id, escalation_context
            ):
                raise EscalationError("Escalation conditions not met")

            escalation_id = str(uuid.uuid4())

            # Initialize escalation tracking
            escalation_record = {
                "escalation_id": escalation_id,
                "crew_type": crew_type,
                "escalation_type": "think",
                "status": "initializing",
                "progress": 0,
                "current_phase": "crew_initialization",
                "context": escalation_context,
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "crew_activity": [],
                "preliminary_insights": [],
                "estimated_completion": (
                    datetime.utcnow() + timedelta(minutes=5)
                ).isoformat(),
                "priority": self.trigger_manager.get_escalation_priority(
                    page, agent_id, escalation_context
                ),
            }

            self.active_escalations[escalation_id] = escalation_record

            # Start crew execution in background
            background_tasks.add_task(
                self.execution_handler.execute_crew_thinking,
                escalation_id,
                crew_type,
                escalation_context,
            )

            logger.info(f"🚀 Started crew escalation {escalation_id} with {crew_type}")
            return escalation_id

        except Exception as e:
            logger.error(f"❌ Failed to start crew escalation: {e}")
            raise EscalationError(f"Failed to start crew escalation: {e}")

    async def start_extended_collaboration(
        self,
        collaboration_strategy: Dict[str, Any],
        collaboration_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start extended crew collaboration for Ponder More functionality."""
        try:
            # Validate collaboration strategy
            if not self.policy_manager.validate_collaboration_strategy(
                collaboration_strategy
            ):
                raise EscalationError("Invalid collaboration strategy provided")

            # Validate escalation context
            page = collaboration_context.get("page", "unknown")
            agent_id = collaboration_context.get("agent_id", "unknown")

            if not self.trigger_manager.validate_escalation_context(
                page, agent_id, collaboration_context
            ):
                raise EscalationError("Invalid collaboration context provided")

            escalation_id = str(uuid.uuid4())

            # Calculate estimated completion time based on strategy
            duration_estimate = collaboration_strategy.get("estimated_duration", {})
            estimated_minutes = duration_estimate.get("estimated_minutes", 10)

            # Initialize collaboration tracking
            collaboration_record = {
                "escalation_id": escalation_id,
                "collaboration_strategy": collaboration_strategy,
                "escalation_type": "ponder_more",
                "status": "initializing",
                "progress": 0,
                "current_phase": "collaboration_setup",
                "context": collaboration_context,
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "crew_activity": [],
                "preliminary_insights": [],
                "collaboration_details": {
                    "active_crews": [collaboration_strategy["primary_crew"]]
                    + collaboration_strategy.get("additional_crews", []),
                    "collaboration_pattern": collaboration_strategy["pattern"],
                    "phase_progress": {},
                },
                "estimated_completion": (
                    datetime.utcnow() + timedelta(minutes=estimated_minutes)
                ).isoformat(),
                "priority": self.trigger_manager.get_escalation_priority(
                    page, agent_id, collaboration_context
                ),
                "resource_requirements": collaboration_strategy.get(
                    "resource_requirements", {}
                ),
            }

            self.active_escalations[escalation_id] = collaboration_record

            # Start collaboration in background
            background_tasks.add_task(
                self.execution_handler.execute_crew_collaboration,
                escalation_id,
                collaboration_strategy,
                collaboration_context,
            )

            logger.info(
                f"🤝 Started crew collaboration {escalation_id} with strategy {collaboration_strategy['pattern']}"
            )
            return escalation_id

        except Exception as e:
            logger.error(f"❌ Failed to start crew collaboration: {e}")
            raise EscalationError(f"Failed to start crew collaboration: {e}")

    def get_escalation_status_summary(self, escalation_id: str) -> Dict[str, Any]:
        """Get comprehensive escalation status including workflow state."""
        base_status = self.notification_manager.get_escalation_status_summary(
            escalation_id
        )

        if not base_status:
            return {"error": "Escalation not found"}

        escalation = self.active_escalations.get(escalation_id, {})

        # Add workflow-specific information
        workflow_info = {
            "priority": escalation.get("priority", "medium"),
            "escalation_type": escalation.get("escalation_type", "unknown"),
            "estimated_completion": escalation.get("estimated_completion"),
            "crew_type": escalation.get("crew_type"),
            "workflow_stage": self._determine_workflow_stage(escalation),
            "resource_usage": self._calculate_current_resource_usage(escalation),
        }

        # Add collaboration-specific details if applicable
        if escalation.get("escalation_type") == "ponder_more":
            collaboration_details = escalation.get("collaboration_details", {})
            workflow_info.update(
                {
                    "collaboration_pattern": collaboration_details.get(
                        "collaboration_pattern"
                    ),
                    "active_crews_count": len(
                        collaboration_details.get("active_crews", [])
                    ),
                    "collaboration_strategy": escalation.get(
                        "collaboration_strategy", {}
                    ).get("collaboration_type"),
                }
            )

        base_status.update(workflow_info)
        return base_status

    def _determine_workflow_stage(self, escalation: Dict[str, Any]) -> str:
        """Determine the current workflow stage."""
        status = escalation.get("status", "unknown")
        progress = escalation.get("progress", 0)

        if status == "completed":
            return "completed"
        elif status == "failed":
            return "failed"
        elif status == "cancelled":
            return "cancelled"
        elif progress < 20:
            return "initialization"
        elif progress < 40:
            return "analysis"
        elif progress < 70:
            return "processing"
        elif progress < 90:
            return "synthesis"
        else:
            return "finalization"

    def _calculate_current_resource_usage(
        self, escalation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate current resource usage for the escalation."""
        escalation_type = escalation.get("escalation_type", "think")
        collaboration_details = escalation.get("collaboration_details", {})

        if escalation_type == "ponder_more":
            active_crews = collaboration_details.get("active_crews", [])
            return {
                "crew_count": len(active_crews),
                "estimated_cpu": len(active_crews) * 0.5,
                "estimated_memory_mb": len(active_crews) * 512,
                "resource_tier": "high" if len(active_crews) > 3 else "medium",
            }
        else:
            return {
                "crew_count": 1,
                "estimated_cpu": 0.5,
                "estimated_memory_mb": 512,
                "resource_tier": "low",
            }

    def get_active_escalations_summary(self) -> Dict[str, Any]:
        """Get summary of all active escalations."""
        active_count = len(
            [
                e
                for e in self.active_escalations.values()
                if e.get("status") not in ["completed", "failed", "cancelled"]
            ]
        )

        completed_count = len(
            [
                e
                for e in self.active_escalations.values()
                if e.get("status") == "completed"
            ]
        )

        failed_count = len(
            [e for e in self.active_escalations.values() if e.get("status") == "failed"]
        )

        # Group by type
        by_type = {}
        for escalation in self.active_escalations.values():
            escalation_type = escalation.get("escalation_type", "unknown")
            if escalation_type not in by_type:
                by_type[escalation_type] = 0
            by_type[escalation_type] += 1

        # Calculate resource usage
        total_crews = sum(
            len(e.get("collaboration_details", {}).get("active_crews", [1]))
            for e in self.active_escalations.values()
            if e.get("status") not in ["completed", "failed", "cancelled"]
        )

        return {
            "total_escalations": len(self.active_escalations),
            "active_escalations": active_count,
            "completed_escalations": completed_count,
            "failed_escalations": failed_count,
            "escalations_by_type": by_type,
            "total_active_crews": total_crews,
            "system_load": (
                "high" if total_crews > 10 else "medium" if total_crews > 5 else "low"
            ),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def recommend_workflow_optimization(self, context: Dict[str, Any]) -> List[str]:
        """Recommend workflow optimizations based on current state."""
        recommendations = []

        summary = self.get_active_escalations_summary()

        # Check system load
        if summary["system_load"] == "high":
            recommendations.append(
                "Consider queuing new escalations to reduce system load"
            )
            recommendations.append("Prioritize completion of existing escalations")

        # Check failure rate
        total_completed = (
            summary["completed_escalations"] + summary["failed_escalations"]
        )
        if total_completed > 0:
            failure_rate = summary["failed_escalations"] / total_completed
            if failure_rate > 0.2:  # More than 20% failure rate
                recommendations.append(
                    "High failure rate detected - review escalation conditions"
                )
                recommendations.append("Consider adjusting crew selection criteria")

        # Check escalation patterns
        if summary["escalations_by_type"].get("ponder_more", 0) > summary[
            "escalations_by_type"
        ].get("think", 0):
            recommendations.append(
                "High collaboration demand - consider scaling strategic crews"
            )

        # Page-specific recommendations
        page = context.get("page")
        if page:
            page_recommendations = self.policy_manager.get_policy_recommendations(
                page, context
            )
            recommendations.extend(page_recommendations)

        return recommendations


# Export for use in other modules
__all__ = ["EscalationWorkflowManager"]
