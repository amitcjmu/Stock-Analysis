"""
Base escalation classes and core data structures for CrewEscalationManager.
"""

import logging
from typing import Any, Dict, List, Optional

# Setup logger
logger = logging.getLogger(__name__)

# Strategic crews - Use PERSISTENT wrappers (Phase B1 - Nov 2025)
try:
    from ...crewai_flows.crews.asset_intelligence_crew import (
        create_asset_intelligence_crew,
    )

    # Use persistent wrappers for dependency analysis and tech debt
    from ...persistent_agents.dependency_analysis_persistent import (
        execute_dependency_analysis,
    )
    from ...persistent_agents.technical_debt_persistent import (
        execute_tech_debt_analysis,
    )

    STRATEGIC_CREWS_AVAILABLE = True
    logger.info("Strategic crews using PERSISTENT wrappers (Phase B1)")
except ImportError:
    logger.debug("Strategic crews not available - using fallback functionality")
    STRATEGIC_CREWS_AVAILABLE = False


class CrewEscalationManagerBase:
    """
    Base class for crew escalation management with core data structures and utilities.

    This class contains the shared state and configuration used by all escalation components.
    """

    def __init__(self):
        """Initialize the base escalation manager with core data structures."""
        self.active_escalations: Dict[str, Dict[str, Any]] = {}

        # Initialize crew mappings
        self.crew_mappings = self._initialize_crew_mappings()

        # Initialize strategic crews if available
        self.strategic_crews = {}
        if STRATEGIC_CREWS_AVAILABLE:
            self._initialize_strategic_crews()

        # Initialize delegation patterns
        self.delegation_patterns = self._initialize_delegation_patterns()

        # Initialize collaboration strategies
        self.collaboration_strategies = self._initialize_collaboration_strategies()

        logger.info(
            "🚀 Crew Escalation Manager Base initialized with strategic crew integration"
        )

    def _initialize_crew_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize crew mappings configuration."""
        return {
            # Page -> Agent -> Crew mappings (Enhanced with strategic crews)
            "field_mapping": {
                "attribute_mapping_agent": "field_mapping_crew",
                "data_validation_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
            },
            "asset_inventory": {
                "asset_inventory_agent": "asset_intelligence_crew",
                "data_cleansing_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
                "business_context_analyst": "asset_intelligence_crew",
                "environment_specialist": "asset_intelligence_crew",
            },
            "dependencies": {
                "dependency_analysis_agent": "dependency_analysis_crew",
                "asset_inventory_agent": "asset_intelligence_crew",
                "network_architecture_specialist": "dependency_analysis_crew",
                "application_integration_expert": "dependency_analysis_crew",
                "infrastructure_dependencies_analyst": "dependency_analysis_crew",
            },
            "tech_debt": {
                "tech_debt_analysis_agent": "tech_debt_analysis_crew",
                "dependency_analysis_agent": "dependency_analysis_crew",
                "legacy_modernization_expert": "tech_debt_analysis_crew",
                "cloud_migration_strategist": "tech_debt_analysis_crew",
                "risk_assessment_specialist": "tech_debt_analysis_crew",
            },
        }

    def _initialize_strategic_crews(self) -> None:
        """Initialize strategic crew instances if available."""
        try:
            # Use PERSISTENT wrappers for dependency and tech debt (Phase B1 - Nov 2025)
            self.strategic_crews = {
                "asset_intelligence_crew": create_asset_intelligence_crew(),
                "dependency_analysis_crew": execute_dependency_analysis,  # Persistent wrapper
                "tech_debt_analysis_crew": execute_tech_debt_analysis,  # Persistent wrapper
            }
            logger.info(
                "✅ Strategic crews initialized with PERSISTENT wrappers (Phase B1)"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize strategic crews: {e}")
            self.strategic_crews = {}

    def _initialize_delegation_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize delegation patterns for Ponder More functionality."""
        return {
            "sequential_delegation": {
                "description": "Sequential expert delegation with escalating complexity",
                "pattern": "expert_1 -> expert_2 -> expert_3 -> synthesis",
            },
            "parallel_delegation": {
                "description": "Parallel expert analysis with collaborative synthesis",
                "pattern": "expert_1 || expert_2 || expert_3 -> collaborative_synthesis",
            },
            "hierarchical_delegation": {
                "description": "Hierarchical delegation with specialist review",
                "pattern": "specialists -> senior_experts -> executive_review",
            },
        }

    def _initialize_collaboration_strategies(self) -> Dict[str, Dict[str, str]]:
        """Initialize collaboration strategies for Ponder More functionality."""
        return {
            "cross_agent": {
                "pattern": "parallel_synthesis",
                "description": "Multiple agents collaborate in parallel then synthesize results",
            },
            "expert_panel": {
                "pattern": "sequential_expert_review",
                "description": "Sequential expert review with escalating complexity",
            },
            "full_crew": {
                "pattern": "full_crew_collaboration",
                "description": "Complete crew collaboration with debate and consensus",
            },
        }

    def cleanup_completed_escalations(self, max_age_hours: int = 24) -> int:
        """Clean up old completed escalations."""
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        to_remove = []
        for escalation_id, escalation in self.active_escalations.items():
            if escalation["status"] in ["completed", "failed", "cancelled"]:
                completed_time = (
                    escalation.get("completed_at")
                    or escalation.get("failed_at")
                    or escalation.get("cancelled_at")
                )
                if (
                    completed_time
                    and datetime.fromisoformat(completed_time) < cutoff_time
                ):
                    to_remove.append(escalation_id)

        for escalation_id in to_remove:
            del self.active_escalations[escalation_id]

        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old escalations")

        return len(to_remove)

    async def get_escalation_status(
        self, escalation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get status of a specific escalation."""
        return self.active_escalations.get(escalation_id)

    async def get_flow_escalations(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get all escalations for a specific flow."""
        flow_escalations = []
        for escalation in self.active_escalations.values():
            if escalation.get("context", {}).get("flow_id") == flow_id:
                flow_escalations.append(escalation)

        # Sort by creation time
        flow_escalations.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return flow_escalations

    async def cancel_escalation(self, escalation_id: str) -> Dict[str, Any]:
        """Cancel an ongoing escalation."""
        from datetime import datetime
        from .exceptions import EscalationNotFoundError, InvalidEscalationStateError

        if escalation_id not in self.active_escalations:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")

        escalation = self.active_escalations[escalation_id]

        if escalation["status"] in ["completed", "failed", "cancelled"]:
            raise InvalidEscalationStateError(
                f"Cannot cancel escalation in {escalation['status']} state",
                escalation["status"],
                escalation_id,
            )

        escalation["status"] = "cancelled"
        escalation["cancelled_at"] = datetime.utcnow().isoformat()
        escalation["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"🚫 Cancelled escalation {escalation_id}")
        return {"success": True, "message": "Escalation cancelled successfully"}


# Export shared constants and utilities
__all__ = ["CrewEscalationManagerBase", "STRATEGIC_CREWS_AVAILABLE", "logger"]
