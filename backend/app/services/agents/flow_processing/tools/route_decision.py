"""
Route Decision Tool

This tool makes intelligent routing decisions based on flow analysis
and phase validation results.

Per ADR-027: Uses FlowTypeConfig as single source of truth for phase routes.
"""

import logging
import re
from typing import List, Optional

from ..crewai_imports import BaseTool
from app.services.flow_type_registry_helpers import get_flow_config

logger = logging.getLogger(__name__)


class RouteDecisionTool(BaseTool):
    """Tool for making intelligent routing decisions"""

    name: str = "route_decision_maker"
    description: str = (
        "Makes intelligent routing decisions based on flow analysis and phase validation results"
    )

    def _run(self, flow_analysis: str, validation_result: str) -> str:
        """Make intelligent routing decision based on actionable guidance"""
        try:
            # Parse inputs to extract actionable guidance
            flow_type = self._extract_flow_type(flow_analysis)
            current_phase = self._extract_current_phase(flow_analysis)
            flow_id = self._extract_flow_id(flow_analysis)

            # Log for debugging route generation issues
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"🔍 ROUTE DECISION DEBUG - flow_type={flow_type}, phase={current_phase}, flow_id={flow_id}"
            )

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
                    flow_type, current_phase, user_actions, flow_id
                )
                reasoning = f"User action required: {'; '.join(user_actions)}"
                confidence = 0.9
            elif system_actions:
                # System action required - trigger internal processing
                target_page = self._determine_system_action_route(
                    flow_type, current_phase, system_actions, flow_id
                )
                reasoning = f"System action required: {'; '.join(system_actions)}"
                confidence = 0.8
            else:
                # Default routing based on phase completion
                is_complete = "COMPLETE" in validation_result

                if is_complete:
                    next_phase = self._get_next_phase(flow_type, current_phase)
                    if next_phase:
                        target_page = self._get_phase_route(
                            flow_type, next_phase, flow_id
                        )
                        reasoning = f"Phase {current_phase} complete - advancing to {next_phase}"
                    else:
                        # Last phase - flow complete
                        target_page = f"/{flow_type}/overview"
                        reasoning = f"Flow complete - {current_phase} was final phase"
                else:
                    target_page = self._get_phase_route(
                        flow_type, current_phase, flow_id
                    )
                    reasoning = (
                        f"Phase {current_phase} incomplete - staying in current phase"
                    )

                confidence = 0.7

            # Include specific issues in reasoning
            if issues:
                reasoning += f" | Issues: {'; '.join(issues)}"

            # Final validation: ensure no unsubstituted templates in target_page
            if (
                "{" in target_page
                or "}" in target_page
                or "[" in target_page
                or "]" in target_page
            ):
                logger.warning(
                    f"⚠️ ROUTE WARNING - Unsubstituted template detected: {target_page}"
                )
                # Fallback to a safe route
                target_page = "/discovery/overview"
                reasoning = "Route template error - defaulting to overview"

            logger.info(f"✅ ROUTE DECISION - Final route: {target_page}")
            return f"ROUTE: {target_page} | REASONING: {reasoning} | CONFIDENCE: {confidence}"

        except Exception as e:
            logger.error(f"❌ ROUTE ERROR - Exception in route decision: {str(e)}")
            return f"Error making routing decision: {str(e)}"

    def _extract_actionable_guidance(self, validation_result: str) -> List[str]:
        """Extract actionable guidance from validation result"""
        if "ACTIONABLE_GUIDANCE:" in validation_result:
            guidance_part = validation_result.split("ACTIONABLE_GUIDANCE:")[1]
            return [g.strip() for g in guidance_part.split(";") if g.strip()]
        return []

    def _determine_user_action_route(
        self, flow_type: str, current_phase: str, user_actions: List[str], flow_id: str
    ) -> str:
        """
        Determine route based on required user actions.

        Per ADR-027: Uses FlowTypeConfig for route determination.
        """
        # Check if user needs to upload data
        if any("upload" in action.lower() for action in user_actions):
            return self._get_phase_route(flow_type, "data_import", flow_id)

        # Check if user needs to configure mappings
        if any("mapping" in action.lower() for action in user_actions):
            return self._get_phase_route(flow_type, "field_mapping", flow_id)

        # Check if user needs to review something or default to current phase
        return self._get_phase_route(flow_type, current_phase, flow_id)

    def _determine_system_action_route(
        self,
        flow_type: str,
        current_phase: str,
        system_actions: List[str],
        flow_id: str,
    ) -> str:
        """
        Determine route for system actions (usually stay on current page while processing).

        Per ADR-027: Uses FlowTypeConfig for route determination.
        """
        # For system actions, usually stay on enhanced dashboard to show processing
        if any(
            "trigger" in action.lower() or "process" in action.lower()
            for action in system_actions
        ):
            return f"/{flow_type}/enhanced-dashboard"

        # For navigation actions, go to the specified page
        if any("navigate" in action.lower() for action in system_actions):
            return self._get_phase_route(flow_type, current_phase, flow_id)

        # Default to enhanced dashboard
        return f"/{flow_type}/enhanced-dashboard"

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

    def _get_phase_route(
        self, flow_type: str, phase_name: str, flow_id: str = ""
    ) -> str:
        """
        Get phase route from FlowTypeConfig metadata.

        Per ADR-027: Uses authoritative ui_route from phase metadata.

        Args:
            flow_type: Type of flow (discovery, assessment, etc.)
            phase_name: Name of the phase
            flow_id: Optional flow ID for template substitution

        Returns:
            UI route with flow_id substituted if applicable
        """
        try:
            config = get_flow_config(flow_type)
            phase_obj = next((p for p in config.phases if p.name == phase_name), None)

            if phase_obj and phase_obj.metadata and "ui_route" in phase_obj.metadata:
                route = phase_obj.metadata["ui_route"]

                # Substitute flow_id if template exists
                if "{flow_id}" in route:
                    if flow_id and flow_id != "unknown":
                        return route.format(flow_id=flow_id)
                    else:
                        # If no flow_id, return to overview instead of broken template
                        return f"/{flow_type}/overview"

                return route

            # Fallback to overview if phase not found
            return f"/{flow_type}/overview"
        except ValueError:
            logger.warning(f"FlowTypeConfig not found for: {flow_type}")
            return f"/{flow_type}/overview"

    def _get_next_phase(self, flow_type: str, current_phase: str) -> Optional[str]:
        """
        Get next phase from FlowTypeConfig.

        Per ADR-027: Uses authoritative phase sequence from config registry.

        Args:
            flow_type: Type of flow (discovery, assessment, etc.)
            current_phase: Current phase name

        Returns:
            Next phase name, or None if last phase/phase not found
        """
        try:
            config = get_flow_config(flow_type)
            phases = [p.name for p in config.phases]

            if current_phase in phases:
                current_index = phases.index(current_phase)
                if current_index < len(phases) - 1:
                    return phases[current_index + 1]

            return None  # Last phase or phase not found
        except ValueError:
            logger.warning(f"FlowTypeConfig not found for: {flow_type}")
            return None
