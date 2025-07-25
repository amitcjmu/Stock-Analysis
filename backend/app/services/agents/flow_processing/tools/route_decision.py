"""
Route Decision Tool

This tool makes intelligent routing decisions based on flow analysis
and phase validation results.
"""

import logging
import re
from typing import ClassVar, Dict, List

from ..crewai_imports import BaseTool

logger = logging.getLogger(__name__)


class RouteDecisionTool(BaseTool):
    """Tool for making intelligent routing decisions"""

    name: str = "route_decision_maker"
    description: str = "Makes intelligent routing decisions based on flow analysis and phase validation results"

    # Route mapping for all flow types - ClassVar to avoid Pydantic field annotation requirement
    ROUTE_MAPPING: ClassVar[Dict[str, Dict[str, str]]] = {
        "discovery": {
            "data_import": "/discovery/import",
            "attribute_mapping": "/discovery/attribute-mapping",
            "data_cleansing": "/discovery/data-cleansing",
            "inventory": "/discovery/inventory",
            "dependencies": "/discovery/dependencies",
            "tech_debt": "/discovery/tech-debt",
            "completed": "/discovery/tech-debt",
        },
        "assessment": {
            "migration_readiness": "/assess/migration-readiness",
            "business_impact": "/assess/business-impact",
            "technical_assessment": "/assess/technical-assessment",
            "completed": "/assess/summary",
        },
        "plan": {
            "wave_planning": "/plan/wave-planning",
            "runbook_creation": "/plan/runbook-creation",
            "resource_allocation": "/plan/resource-allocation",
            "completed": "/plan/summary",
        },
        "execute": {
            "pre_migration": "/execute/pre-migration",
            "migration_execution": "/execute/migration-execution",
            "post_migration": "/execute/post-migration",
            "completed": "/execute/summary",
        },
        "modernize": {
            "modernization_assessment": "/modernize/assessment",
            "architecture_design": "/modernize/architecture-design",
            "implementation_planning": "/modernize/implementation-planning",
            "completed": "/modernize/summary",
        },
        "finops": {
            "cost_analysis": "/finops/cost-analysis",
            "budget_planning": "/finops/budget-planning",
            "completed": "/finops/summary",
        },
        "observability": {
            "monitoring_setup": "/observability/monitoring-setup",
            "performance_optimization": "/observability/performance-optimization",
            "completed": "/observability/summary",
        },
        "decommission": {
            "decommission_planning": "/decommission/planning",
            "data_migration": "/decommission/data-migration",
            "system_shutdown": "/decommission/system-shutdown",
            "completed": "/decommission/summary",
        },
    }

    def _run(self, flow_analysis: str, validation_result: str) -> str:
        """Make intelligent routing decision based on actionable guidance"""
        try:
            # Parse inputs to extract actionable guidance
            flow_type = self._extract_flow_type(flow_analysis)
            current_phase = self._extract_current_phase(flow_analysis)
            flow_id = self._extract_flow_id(flow_analysis)

            # Extract actionable guidance from validation results
            actionable_guidance = self._extract_actionable_guidance(validation_result)

            # Determine if this requires user action or system action
            user_actions = [g for g in actionable_guidance if "USER_ACTION:" in g]
            system_actions = [g for g in actionable_guidance if "SYSTEM_ACTION:" in g]
            issues = [g for g in actionable_guidance if "ISSUE:" in g]

            # Make intelligent routing decision
            if user_actions:
                # User action required - route to appropriate page
                target_page = self._determine_user_action_route(
                    current_phase, user_actions, flow_id
                )
                reasoning = f"User action required: {'; '.join(user_actions)}"
                confidence = 0.9
            elif system_actions:
                # System action required - trigger internal processing
                target_page = self._determine_system_action_route(
                    current_phase, system_actions, flow_id
                )
                reasoning = f"System action required: {'; '.join(system_actions)}"
                confidence = 0.8
            else:
                # Default routing based on phase completion
                is_complete = "COMPLETE" in validation_result
                routes = self.ROUTE_MAPPING.get(flow_type, {})

                if is_complete:
                    next_phase = self._get_next_phase(flow_type, current_phase)
                    target_page = routes.get(next_phase, routes.get("completed", "/"))
                    reasoning = (
                        f"Phase {current_phase} complete - advancing to {next_phase}"
                    )
                else:
                    target_page = routes.get(current_phase, "/")
                    reasoning = (
                        f"Phase {current_phase} incomplete - staying in current phase"
                    )

                confidence = 0.7

            # Include specific issues in reasoning
            if issues:
                reasoning += f" | Issues: {'; '.join(issues)}"

            return f"ROUTE: {target_page} | REASONING: {reasoning} | CONFIDENCE: {confidence}"

        except Exception as e:
            return f"Error making routing decision: {str(e)}"

    def _extract_actionable_guidance(self, validation_result: str) -> List[str]:
        """Extract actionable guidance from validation result"""
        if "ACTIONABLE_GUIDANCE:" in validation_result:
            guidance_part = validation_result.split("ACTIONABLE_GUIDANCE:")[1]
            return [g.strip() for g in guidance_part.split(";") if g.strip()]
        return []

    def _determine_user_action_route(
        self, current_phase: str, user_actions: List[str], flow_id: str
    ) -> str:
        """Determine route based on required user actions"""
        # Check if user needs to upload data
        if any("upload" in action.lower() for action in user_actions):
            return "/discovery/data-import"

        # Check if user needs to configure mappings
        if any("mapping" in action.lower() for action in user_actions):
            return f"/discovery/attribute-mapping?flow_id={flow_id}"

        # Check if user needs to review something
        if any("review" in action.lower() for action in user_actions):
            return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"

        # Default to current phase page
        return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"

    def _determine_system_action_route(
        self, current_phase: str, system_actions: List[str], flow_id: str
    ) -> str:
        """Determine route for system actions (usually stay on current page while processing)"""
        # For system actions, usually stay on enhanced dashboard to show processing
        if any(
            "trigger" in action.lower() or "process" in action.lower()
            for action in system_actions
        ):
            return f"/discovery/enhanced-dashboard?flow_id={flow_id}&action=processing"

        # For navigation actions, go to the specified page
        if any("navigate" in action.lower() for action in system_actions):
            return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"

        # Default to enhanced dashboard
        return f"/discovery/enhanced-dashboard?flow_id={flow_id}"

    def _extract_flow_type(self, analysis: str) -> str:
        """Extract flow type from analysis"""
        for flow_type in [
            "discovery",
            "assess",
            "plan",
            "execute",
            "modernize",
            "finops",
            "observability",
            "decommission",
        ]:
            if f"Type={flow_type}" in analysis:
                return flow_type
        return "discovery"

    def _extract_current_phase(self, analysis: str) -> str:
        """Extract current phase from analysis"""
        match = re.search(r"Phase=([^,]+)", analysis)
        return match.group(1) if match else "data_import"

    def _extract_flow_id(self, analysis: str) -> str:
        """Extract flow ID from analysis"""
        match = re.search(r"Flow ([a-f0-9-]+)", analysis)
        return match.group(1) if match else ""

    def _get_next_phase(self, flow_type: str, current_phase: str) -> str:
        """Get the next phase for a flow type"""
        phase_sequences = {
            "discovery": [
                "data_import",
                "attribute_mapping",
                "data_cleansing",
                "inventory",
                "dependencies",
                "tech_debt",
            ],
            "assess": [
                "migration_readiness",
                "business_impact",
                "technical_assessment",
            ],
            "plan": ["wave_planning", "runbook_creation", "resource_allocation"],
            "execute": ["pre_migration", "migration_execution", "post_migration"],
            "modernize": [
                "modernization_assessment",
                "architecture_design",
                "implementation_planning",
            ],
            "finops": ["cost_analysis", "budget_planning"],
            "observability": ["monitoring_setup", "performance_optimization"],
            "decommission": [
                "decommission_planning",
                "data_migration",
                "system_shutdown",
            ],
        }

        sequence = phase_sequences.get(flow_type, [])
        try:
            current_index = sequence.index(current_phase)
            if current_index + 1 < len(sequence):
                return sequence[current_index + 1]
        except ValueError:
            pass

        return "completed"
