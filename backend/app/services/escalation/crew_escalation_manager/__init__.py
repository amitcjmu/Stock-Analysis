"""
Crew Escalation Manager - Modularized Implementation

Manages crew escalations for Think/Ponder More button functionality.
Implements Tasks 2.3 and 3.4 of the Discovery Flow Redesign.
Enhanced with strategic crew integration and delegation capabilities.

This package contains the modularized version of the CrewEscalationManager,
split into logical components for better maintainability and testing.

Components:
- base.py: Base escalation classes and core data structures
- triggers.py: Escalation triggers and conditions
- policies.py: Escalation policies and rules
- handlers.py: Escalation handlers and actions
- notifications.py: Notification and alert systems
- workflows.py: Escalation workflow management
- metrics.py: Escalation metrics and tracking
- exceptions.py: Escalation-specific exceptions
"""

from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks

from .base import CrewEscalationManagerBase
from .triggers import EscalationTriggerManager
from .policies import EscalationPolicyManager
from .handlers import EscalationExecutionHandler
from .notifications import EscalationNotificationManager
from .workflows import EscalationWorkflowManager
from .metrics import EscalationMetricsManager


class CrewEscalationManager(CrewEscalationManagerBase):
    """
    Manages crew escalations for Think/Ponder More functionality.

    Handles:
    - Crew selection based on page/agent context
    - Background crew execution
    - Progress tracking and status updates
    - Results integration back to discovery flow

    This is the main class that composes all modular components while maintaining
    the original public interface for zero breaking changes.
    """

    def __init__(self):
        """Initialize the CrewEscalationManager with all modular components."""
        # Initialize base class with core data structures
        super().__init__()

        # Initialize all modular components
        self.trigger_manager = EscalationTriggerManager(self.crew_mappings)

        self.policy_manager = EscalationPolicyManager(
            self.collaboration_strategies, self.delegation_patterns
        )

        self.notification_manager = EscalationNotificationManager(
            self.active_escalations
        )

        self.metrics_manager = EscalationMetricsManager(self.strategic_crews)

        self.execution_handler = EscalationExecutionHandler(
            self.strategic_crews, self.notification_manager, self.metrics_manager
        )

        self.workflow_manager = EscalationWorkflowManager(
            self.active_escalations,
            self.trigger_manager,
            self.policy_manager,
            self.execution_handler,
            self.notification_manager,
        )

    def determine_crew_for_page_agent(self, page: str, agent_id: str) -> str:
        """Determine appropriate crew based on page and agent context."""
        return self.trigger_manager.determine_crew_for_page_agent(page, agent_id)

    def determine_collaboration_strategy(
        self, page: str, agent_id: str, collaboration_type: str
    ) -> Dict[str, Any]:
        """Determine collaboration strategy for Ponder More functionality."""
        return self.policy_manager.determine_collaboration_strategy(
            page, agent_id, collaboration_type
        )

    async def start_crew_escalation(
        self,
        crew_type: str,
        escalation_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start a crew escalation for Think button functionality."""
        return await self.workflow_manager.start_crew_escalation(
            crew_type, escalation_context, background_tasks
        )

    async def start_extended_collaboration(
        self,
        collaboration_strategy: Dict[str, Any],
        collaboration_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start extended crew collaboration for Ponder More functionality."""
        return await self.workflow_manager.start_extended_collaboration(
            collaboration_strategy, collaboration_context, background_tasks
        )

    # The following methods are preserved for backward compatibility
    # but delegate to the base class or appropriate managers

    async def _execute_crew_thinking(
        self, escalation_id: str, crew_type: str, context: Dict[str, Any]
    ) -> None:
        """Execute crew thinking process in background (compatibility method)."""
        await self.execution_handler.execute_crew_thinking(
            escalation_id, crew_type, context
        )

    async def _execute_crew_collaboration(
        self,
        escalation_id: str,
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """Execute crew collaboration process (compatibility method)."""
        await self.execution_handler.execute_crew_collaboration(
            escalation_id, collaboration_strategy, context
        )

    async def _execute_strategic_crew_analysis(
        self, crew_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute analysis with a specific strategic crew (compatibility method)."""
        return await self.execution_handler._execute_strategic_crew_analysis(
            crew_type, context
        )

    async def _execute_parallel_delegation(
        self, crews: List[str], context: Dict[str, Any], escalation_id: str
    ) -> Dict[str, Any]:
        """Execute parallel delegation to multiple crews (compatibility method)."""
        return await self.execution_handler._execute_parallel_delegation(
            crews, context, escalation_id
        )

    async def _execute_sequential_delegation(
        self, crews: List[str], context: Dict[str, Any], escalation_id: str
    ) -> Dict[str, Any]:
        """Execute sequential delegation to multiple crews (compatibility method)."""
        return await self.execution_handler._execute_sequential_delegation(
            crews, context, escalation_id
        )

    async def _execute_hierarchical_delegation(
        self,
        primary_crew: str,
        additional_crews: List[str],
        context: Dict[str, Any],
        escalation_id: str,
    ) -> Dict[str, Any]:
        """Execute hierarchical delegation with specialist review (compatibility method)."""
        return await self.execution_handler._execute_hierarchical_delegation(
            primary_crew, additional_crews, context, escalation_id
        )

    def _extract_strategic_insights(
        self, crew_type: str, crew_results: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from strategic crew results (compatibility method)."""
        return self.metrics_manager.extract_strategic_insights(
            crew_type, crew_results, context
        )

    def _extract_asset_intelligence_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from asset intelligence crew results (compatibility method)."""
        return self.metrics_manager._extract_asset_intelligence_insights(
            analysis_results, context
        )

    def _extract_dependency_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from dependency analysis crew results (compatibility method)."""
        return self.metrics_manager._extract_dependency_insights(
            analysis_results, context
        )

    def _extract_tech_debt_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from tech debt analysis crew results (compatibility method)."""
        return self.metrics_manager._extract_tech_debt_insights(
            analysis_results, context
        )

    def _synthesize_multi_crew_insights(
        self,
        crew_results: Dict[str, Any],
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Synthesize insights from multiple crew analyses (compatibility method)."""
        return self.metrics_manager.synthesize_multi_crew_insights(
            crew_results, collaboration_strategy, context
        )

    async def _generate_strategic_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        crew_results: Dict[str, Any],
        preliminary_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate results from strategic crew execution (compatibility method)."""
        return await self.metrics_manager.generate_strategic_crew_results(
            crew_type, context, crew_results, preliminary_insights
        )

    def _extract_strategic_recommendations(
        self, crew_type: str, crew_results: Dict[str, Any]
    ) -> List[str]:
        """Extract strategic recommendations from crew results (compatibility method)."""
        return self.metrics_manager.extract_strategic_recommendations(
            crew_type, crew_results
        )

    async def _update_escalation_progress(
        self, escalation_id: str, progress: int, phase: str, description: str
    ) -> None:
        """Update escalation progress and status (compatibility method)."""
        await self.notification_manager.update_escalation_progress(
            escalation_id, progress, phase, description
        )

    async def _handle_escalation_error(
        self, escalation_id: str, error_message: str
    ) -> None:
        """Handle escalation errors (compatibility method)."""
        await self.notification_manager.handle_escalation_error(
            escalation_id, error_message
        )

    def _get_expected_outcomes(self, page: str, collaboration_type: str) -> List[str]:
        """Get expected outcomes based on page and collaboration type (compatibility method)."""
        return self.policy_manager._get_expected_outcomes(page, collaboration_type)

    def _generate_preliminary_insights(
        self, crew_type: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate preliminary insights when crew results are not available (compatibility method)."""
        return self.metrics_manager.generate_preliminary_insights(crew_type, context)

    async def _generate_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        preliminary_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate crew results based on preliminary insights (compatibility method)."""
        return await self.metrics_manager.generate_crew_results(
            crew_type, context, preliminary_insights
        )

    async def _generate_collaborative_results(
        self,
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
        comprehensive_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate collaborative results from multiple crews (compatibility method)."""
        return await self.metrics_manager.generate_collaborative_results(
            collaboration_strategy, context, comprehensive_insights
        )


# Export all public classes and functions for backward compatibility
__all__ = [
    "CrewEscalationManager",
    # Export component classes for advanced usage
    "CrewEscalationManagerBase",
    "EscalationTriggerManager",
    "EscalationPolicyManager",
    "EscalationExecutionHandler",
    "EscalationNotificationManager",
    "EscalationWorkflowManager",
    "EscalationMetricsManager",
]
