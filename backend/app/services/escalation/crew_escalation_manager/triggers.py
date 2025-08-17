"""
Escalation triggers and conditions for crew selection and escalation evaluation.
"""

from typing import Dict, Any

from .base import logger


class EscalationTriggerManager:
    """
    Manages escalation triggers, crew selection logic, and escalation conditions.
    """

    def __init__(self, crew_mappings: Dict[str, Dict[str, str]]):
        """Initialize with crew mappings configuration."""
        self.crew_mappings = crew_mappings

    def determine_crew_for_page_agent(self, page: str, agent_id: str) -> str:
        """
        Determine appropriate crew based on page and agent context.

        Args:
            page: The page context (field_mapping, asset_inventory, dependencies, tech_debt)
            agent_id: The agent identifier requesting escalation

        Returns:
            str: The crew type to use for escalation
        """
        page_mappings = self.crew_mappings.get(page, {})
        crew_type = page_mappings.get(agent_id)

        if not crew_type:
            # Default crew selection based on page
            default_crews = {
                "field_mapping": "field_mapping_crew",
                "asset_inventory": "asset_intelligence_crew",
                "dependencies": "dependency_analysis_crew",
                "tech_debt": "tech_debt_analysis_crew",
            }
            crew_type = default_crews.get(page, "general_analysis_crew")

        logger.info(
            f"🎯 Selected crew '{crew_type}' for page '{page}' and agent '{agent_id}'"
        )
        return crew_type

    def should_escalate_to_crew(
        self, page: str, agent_id: str, context: Dict[str, Any]
    ) -> bool:
        """
        Determine if an escalation should be triggered based on context.

        Args:
            page: The page context
            agent_id: The agent identifier
            context: Additional context for escalation decision

        Returns:
            bool: Whether escalation should be triggered
        """
        # Always allow escalation for Think/Ponder More buttons
        if context.get("escalation_trigger") in ["think", "ponder_more"]:
            return True

        # Check if there's enough data for meaningful escalation
        page_data = context.get("page_data", {})
        if not page_data or not page_data.get("assets"):
            logger.warning(f"Insufficient data for escalation on page '{page}'")
            return False

        # Page-specific escalation conditions
        if page == "field_mapping":
            return self._should_escalate_field_mapping(page_data, context)
        elif page == "asset_inventory":
            return self._should_escalate_asset_inventory(page_data, context)
        elif page == "dependencies":
            return self._should_escalate_dependencies(page_data, context)
        elif page == "tech_debt":
            return self._should_escalate_tech_debt(page_data, context)

        # Default to allowing escalation
        return True

    def _should_escalate_field_mapping(
        self, page_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Determine if field mapping escalation should be triggered."""
        # Check for complex mapping scenarios
        unmapped_fields = page_data.get("unmapped_fields", [])
        confidence_issues = page_data.get("low_confidence_mappings", [])

        # Escalate if there are many unmapped fields or confidence issues
        if len(unmapped_fields) > 5 or len(confidence_issues) > 3:
            logger.info("Field mapping escalation triggered due to complexity")
            return True

        return True  # Allow escalation for field mapping by default

    def _should_escalate_asset_inventory(
        self, page_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Determine if asset inventory escalation should be triggered."""
        assets = page_data.get("assets", [])

        # Check for assets needing classification
        unclassified_assets = [
            asset
            for asset in assets
            if not asset.get("classification")
            or asset.get("classification") == "unknown"
        ]

        # Escalate if there are unclassified assets or complex scenarios
        if len(unclassified_assets) > 0 or len(assets) > 10:
            logger.info(
                "Asset inventory escalation triggered for classification assistance"
            )
            return True

        return True

    def _should_escalate_dependencies(
        self, page_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Determine if dependency analysis escalation should be triggered."""
        assets = page_data.get("assets", [])

        # Check for complex dependency scenarios
        assets_with_dependencies = [
            asset
            for asset in assets
            if asset.get("dependencies") and len(asset["dependencies"]) > 0
        ]

        # Escalate if there are complex dependency patterns
        if len(assets_with_dependencies) > 0:
            logger.info(
                "Dependency analysis escalation triggered for complex dependencies"
            )
            return True

        return True

    def _should_escalate_tech_debt(
        self, page_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Determine if tech debt analysis escalation should be triggered."""
        assets = page_data.get("assets", [])

        # Check for legacy systems or modernization candidates
        legacy_assets = [
            asset
            for asset in assets
            if asset.get("legacy_indicators") or asset.get("modernization_candidate")
        ]

        # Escalate if there are legacy systems to analyze
        if len(legacy_assets) > 0 or len(assets) > 5:
            logger.info(
                "Tech debt analysis escalation triggered for legacy system analysis"
            )
            return True

        return True

    def get_escalation_priority(
        self, page: str, agent_id: str, context: Dict[str, Any]
    ) -> str:
        """
        Determine the priority level for an escalation.

        Args:
            page: The page context
            agent_id: The agent identifier
            context: Additional context

        Returns:
            str: Priority level ('low', 'medium', 'high', 'critical')
        """
        # Check for critical indicators
        if context.get("escalation_trigger") == "ponder_more":
            return "high"  # Ponder More requests are high priority

        if context.get("escalation_trigger") == "think":
            return "medium"  # Think requests are medium priority

        # Analyze page data for priority indicators
        page_data = context.get("page_data", {})
        assets = page_data.get("assets", [])

        # Critical priority conditions
        if len(assets) > 50:
            return "critical"  # Large datasets need immediate attention

        # High priority conditions
        error_conditions = [
            page_data.get("errors", []),
            page_data.get("validation_failures", []),
            page_data.get("critical_issues", []),
        ]
        if any(len(errors) > 0 for errors in error_conditions):
            return "high"

        # Medium priority for normal escalations
        return "medium"

    def validate_escalation_context(
        self, page: str, agent_id: str, context: Dict[str, Any]
    ) -> bool:
        """
        Validate that the escalation context is sufficient for processing.

        Args:
            page: The page context
            agent_id: The agent identifier
            context: Escalation context to validate

        Returns:
            bool: Whether the context is valid
        """
        # Required fields
        required_fields = ["escalation_trigger"]
        for field in required_fields:
            if field not in context:
                logger.error(f"Missing required field '{field}' in escalation context")
                return False

        # Validate escalation trigger
        valid_triggers = ["think", "ponder_more", "automatic", "manual"]
        if context["escalation_trigger"] not in valid_triggers:
            logger.error(f"Invalid escalation trigger: {context['escalation_trigger']}")
            return False

        # Validate page
        valid_pages = ["field_mapping", "asset_inventory", "dependencies", "tech_debt"]
        if page not in valid_pages:
            logger.error(f"Invalid page for escalation: {page}")
            return False

        logger.debug(
            f"Escalation context validated for page '{page}' and agent '{agent_id}'"
        )
        return True


# Export for use in other modules
__all__ = ["EscalationTriggerManager"]
