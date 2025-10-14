"""
Discovery Child Flow Service
Service for managing discovery flow child operations

Per ADR-027: Uses FlowTypeConfig for phase information
"""

import logging
from typing import Any, Dict, List, Optional

from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService
from app.services.flow_type_registry import PhaseConfig

logger = logging.getLogger(__name__)


class DiscoveryChildFlowService(BaseChildFlowService):
    """
    Service for discovery flow child operations

    Per ADR-027: Integrates with FlowTypeConfig for authoritative phase information
    """

    def __init__(self, db, context):
        super().__init__(db, context)
        # Initialize repository with proper tenant context
        self.repository = DiscoveryFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
        )
        # Cache flow config for performance
        self._flow_config = None

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get discovery flow child status

        Args:
            flow_id: Flow identifier

        Returns:
            Child flow status dictionary or None
        """
        try:
            child_flow = await self.repository.get_by_flow_id(flow_id)
            if not child_flow:
                return None

            # CRITICAL FIX: Include import_metadata with correct data_import_id
            # This ensures field mappings are properly isolated by import
            import_metadata = {}
            if hasattr(child_flow, "data_import_id") and child_flow.data_import_id:
                import_metadata = {
                    "import_id": str(child_flow.data_import_id),
                    "data_import_id": str(
                        child_flow.data_import_id
                    ),  # Both formats for compatibility
                }
                logger.info(
                    f"🔍 Discovery flow {flow_id} linked to import {child_flow.data_import_id}"
                )
            else:
                logger.warning(
                    f"⚠️ Discovery flow {flow_id} has no data_import_id - field mappings may not work correctly"
                )

            return {
                "status": getattr(child_flow, "status", None),
                "current_phase": getattr(child_flow, "current_phase", None),
                "progress_percentage": getattr(child_flow, "progress_percentage", 0.0),
                "metadata": getattr(child_flow, "metadata", {}),
                "import_metadata": import_metadata,  # CRITICAL: Include import metadata with correct data_import_id
                "raw_data": [],  # Placeholder - could be populated from data import if needed
                "field_mappings": [],  # Placeholder - field mappings are retrieved via separate API
            }
        except Exception as e:
            logger.warning(f"Failed to get discovery child flow status: {e}")
            return None

    async def get_by_master_flow_id(self, flow_id: str) -> Optional[Any]:
        """
        Get discovery flow by master flow ID

        Args:
            flow_id: Master flow identifier

        Returns:
            Discovery flow entity or None
        """
        try:
            return await self.repository.get_by_master_flow_id(flow_id)
        except Exception as e:
            logger.warning(f"Failed to get discovery flow by master ID: {e}")
            return None

    def _get_flow_config(self):
        """Get FlowTypeConfig for discovery flow (cached)"""
        if self._flow_config is None:
            from app.services.flow_type_registry_helpers import get_flow_config

            self._flow_config = get_flow_config("discovery")
        return self._flow_config

    def get_phase_config(self, phase_name: str) -> Optional[PhaseConfig]:
        """
        Get phase configuration from FlowTypeConfig

        Per ADR-027: Single source of truth for phase information

        Args:
            phase_name: Canonical phase name

        Returns:
            PhaseConfig or None if phase not found
        """
        try:
            config = self._get_flow_config()
            for phase_config in config.phases:
                if phase_config.name == phase_name:
                    return phase_config
            return None
        except Exception as e:
            logger.warning(f"Failed to get phase config for '{phase_name}': {e}")
            return None

    def get_all_phases(self) -> List[str]:
        """
        Get list of all valid phase names for discovery flow

        Per ADR-027: Replaces hardcoded PHASE_SEQUENCES

        Returns:
            List of phase names in order
        """
        try:
            config = self._get_flow_config()
            return [p.name for p in config.phases]
        except Exception as e:
            logger.warning(f"Failed to get phases from FlowTypeConfig: {e}")
            # Fallback to empty list
            return []

    def validate_phase(self, phase_name: str) -> bool:
        """
        Validate that a phase name is valid for discovery flow

        Per ADR-027: Uses FlowTypeConfig instead of PHASE_SEQUENCES

        Args:
            phase_name: Phase name to validate

        Returns:
            True if phase is valid, False otherwise
        """
        valid_phases = self.get_all_phases()
        return phase_name in valid_phases

    def get_phase_metadata(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """
        Get phase metadata (UI route, duration, etc.)

        Per ADR-027: Metadata from FlowTypeConfig

        Args:
            phase_name: Canonical phase name

        Returns:
            Phase metadata dictionary or None
        """
        phase_config = self.get_phase_config(phase_name)
        if not phase_config:
            return None

        return {
            "name": phase_config.name,
            "display_name": phase_config.display_name,
            "description": phase_config.description,
            "can_pause": phase_config.can_pause,
            "can_skip": phase_config.can_skip,
            "ui_route": phase_config.metadata.get("ui_route"),
            "estimated_duration_minutes": phase_config.metadata.get(
                "estimated_duration_minutes"
            ),
            "icon": phase_config.metadata.get("icon"),
            "help_text": phase_config.metadata.get("help_text"),
        }

    def get_next_phase(self, current_phase: str) -> Optional[str]:
        """
        Get the next phase after the current phase

        Per ADR-027: Uses FlowTypeConfig phase order

        Args:
            current_phase: Current phase name

        Returns:
            Next phase name or None if no next phase
        """
        try:
            phases = self.get_all_phases()
            if current_phase not in phases:
                return None

            current_index = phases.index(current_phase)
            if current_index < len(phases) - 1:
                return phases[current_index + 1]

            return None
        except Exception as e:
            logger.warning(f"Failed to get next phase after '{current_phase}': {e}")
            return None
