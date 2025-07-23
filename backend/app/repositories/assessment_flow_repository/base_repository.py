"""
Assessment Flow Base Repository

Main repository class that delegates to specialized query and command modules.
Maintains backward compatibility with the original AssessmentFlowRepository interface.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import (
    ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
)
from app.models.assessment_flow_state import (
    ApplicationComponent as ApplicationComponentState,
)
from app.models.assessment_flow_state import (
    ArchitectureRequirement,
    AssessmentFlowState,
    TechDebtItem,
)
from app.models.assessment_flow_state import (
    AssessmentLearningFeedback as AssessmentLearningFeedbackState,
)
from app.models.assessment_flow_state import (
    ComponentTreatment as ComponentTreatmentState,
)
from app.models.assessment_flow_state import SixRDecision as SixRDecisionState
from app.repositories.base import ContextAwareRepository

# Import command handlers
from .commands import (
    ArchitectureCommands,
    ComponentCommands,
    DecisionCommands,
    FeedbackCommands,
    FlowCommands,
)

# Import query handlers
from .queries import AnalyticsQueries, FlowQueries, StateQueries

# Import specifications
from .specifications import FlowSpecifications

logger = logging.getLogger(__name__)


class AssessmentFlowRepository(ContextAwareRepository):
    """Repository for assessment flow data access with multi-tenant support"""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: int,
        engagement_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ):
        super().__init__(db, client_account_id, engagement_id, user_id)

        # Initialize command handlers
        self._flow_commands = FlowCommands(db, client_account_id)
        self._architecture_commands = ArchitectureCommands(db, client_account_id)
        self._component_commands = ComponentCommands(db, client_account_id)
        self._decision_commands = DecisionCommands(db, client_account_id)
        self._feedback_commands = FeedbackCommands(db, client_account_id)

        # Initialize query handlers
        self._flow_queries = FlowQueries(db, client_account_id)
        self._analytics_queries = AnalyticsQueries(db, client_account_id)
        self._state_queries = StateQueries(db, client_account_id)

        # Initialize specifications
        self._flow_specs = FlowSpecifications(db, client_account_id)

    # === FLOW MANAGEMENT ===

    async def create_assessment_flow(
        self,
        engagement_id: str,
        selected_application_ids: List[str],
        created_by: Optional[str] = None,
    ) -> str:
        """Create new assessment flow with initial state and register with master flow system"""
        return await self._flow_commands.create_assessment_flow(
            engagement_id, selected_application_ids, created_by
        )

    async def get_assessment_flow_state(
        self, flow_id: str
    ) -> Optional[AssessmentFlowState]:
        """Get complete assessment flow state with all related data"""
        return await self._flow_queries.get_assessment_flow_state(flow_id)

    async def update_flow_phase(
        self,
        flow_id: str,
        current_phase: str,
        next_phase: Optional[str] = None,
        progress: Optional[int] = None,
        status: Optional[str] = None,
    ):
        """Update flow phase and progress, sync with master flow"""
        await self._flow_commands.update_flow_phase(
            flow_id, current_phase, next_phase, progress, status
        )

        # Update master flow status
        await self._flow_specs.update_master_flow_status(
            flow_id, status or "running", current_phase
        )

    async def save_user_input(
        self, flow_id: str, phase: str, user_input: Dict[str, Any]
    ):
        """Save user input for specific phase"""
        await self._flow_commands.save_user_input(flow_id, phase, user_input)

    async def save_agent_insights(
        self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
    ):
        """Save agent insights for specific phase and log to master flow"""
        await self._flow_commands.save_agent_insights(flow_id, phase, insights)

        # Log agent collaboration to master flow
        await self._flow_specs.log_agent_collaboration(flow_id, phase, insights)

    # === ARCHITECTURE STANDARDS MANAGEMENT ===

    async def save_architecture_standards(
        self, engagement_id: str, standards: List[ArchitectureRequirement]
    ):
        """Save or update engagement architecture standards"""
        await self._architecture_commands.save_architecture_standards(
            engagement_id, standards
        )

    async def save_application_overrides(
        self,
        flow_id: str,
        app_id: str,
        overrides: List[ApplicationArchitectureOverrideState],
    ):
        """Save application architecture overrides"""
        await self._architecture_commands.save_application_overrides(
            flow_id, app_id, overrides
        )

    # === COMPONENT MANAGEMENT ===

    async def save_application_components(
        self, flow_id: str, app_id: str, components: List[ApplicationComponentState]
    ):
        """Save application components for specific app"""
        await self._component_commands.save_application_components(
            flow_id, app_id, components
        )

    async def save_tech_debt_analysis(
        self, flow_id: str, app_id: str, tech_debt_items: List[TechDebtItem]
    ):
        """Save tech debt analysis for application"""
        await self._component_commands.save_tech_debt_analysis(
            flow_id, app_id, tech_debt_items
        )

    async def save_component_treatments(
        self, flow_id: str, app_id: str, treatments: List[ComponentTreatmentState]
    ):
        """Save component treatments for application"""
        await self._component_commands.save_component_treatments(
            flow_id, app_id, treatments
        )

    # === 6R DECISION MANAGEMENT ===

    async def save_sixr_decision(self, flow_id: str, decision: SixRDecisionState):
        """Save or update 6R decision for application"""
        await self._decision_commands.save_sixr_decision(flow_id, decision)

        # Save component treatments
        await self.save_component_treatments(
            flow_id, str(decision.application_id), decision.component_treatments
        )

    async def mark_apps_ready_for_planning(self, flow_id: str, app_ids: List[str]):
        """Mark applications as ready for planning flow"""
        await self._decision_commands.mark_apps_ready_for_planning(flow_id, app_ids)

    # === LEARNING FEEDBACK ===

    async def save_learning_feedback(
        self, flow_id: str, decision_id: str, feedback: AssessmentLearningFeedbackState
    ):
        """Save learning feedback for agent improvement"""
        await self._feedback_commands.save_learning_feedback(
            flow_id, decision_id, feedback
        )

    # === QUERY METHODS ===

    async def get_flows_by_engagement(
        self, engagement_id: str, limit: int = 50
    ) -> List[AssessmentFlow]:
        """Get all assessment flows for an engagement"""
        return await self._flow_queries.get_flows_by_engagement(engagement_id, limit)

    async def get_flows_by_status(
        self, status: str, limit: int = 50
    ) -> List[AssessmentFlow]:
        """Get flows by status"""
        return await self._flow_queries.get_flows_by_status(status, limit)

    async def search_flows_by_application(self, app_id: str) -> List[AssessmentFlow]:
        """Find flows that include a specific application"""
        return await self._flow_queries.search_flows_by_application(app_id)

    async def get_flow_analytics(self, flow_id: str) -> Dict[str, Any]:
        """Get analytics data for a flow"""
        return await self._analytics_queries.get_flow_analytics(flow_id)

    # === PRIVATE HELPER METHODS ===

    async def _get_architecture_standards(
        self, engagement_id: str
    ) -> List[ArchitectureRequirement]:
        """Get architecture standards for engagement"""
        return await self._state_queries.get_architecture_standards(engagement_id)

    async def _get_application_overrides(
        self, flow_id: str
    ) -> Dict[str, List[ApplicationArchitectureOverrideState]]:
        """Get application architecture overrides grouped by app"""
        return await self._state_queries.get_application_overrides(flow_id)

    async def _get_application_components(
        self, flow_id: str
    ) -> Dict[str, List[ApplicationComponentState]]:
        """Get application components grouped by app"""
        return await self._state_queries.get_application_components(flow_id)

    async def _get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get tech debt analysis and scores grouped by app"""
        return await self._state_queries.get_tech_debt_analysis(flow_id)

    async def _get_sixr_decisions(self, flow_id: str) -> Dict[str, SixRDecisionState]:
        """Get 6R decisions for all applications"""
        return await self._state_queries.get_sixr_decisions(flow_id)

    async def _update_master_flow_status(
        self,
        flow_id: str,
        status: str,
        current_phase: str,
        phase_data: Optional[Dict[str, Any]] = None,
    ):
        """Update master flow status and phase data"""
        await self._flow_specs.update_master_flow_status(
            flow_id, status, current_phase, phase_data
        )

    async def _log_agent_collaboration(
        self, flow_id: str, phase: str, insights: List[Dict[str, Any]]
    ):
        """Log agent collaboration to master flow"""
        await self._flow_specs.log_agent_collaboration(flow_id, phase, insights)
