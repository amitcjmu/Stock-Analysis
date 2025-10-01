"""
Platform Detection Handler - Stub Implementation

CC: This handler is part of the legacy ADCS system and is NOT needed for
the alternate entry point collection flows (Asset Selection → Gap Analysis).
This stub prevents import errors while the flow logic is being updated to
make platform detection truly optional/conditional.
"""

import logging

logger = logging.getLogger(__name__)


class PlatformDetectionHandler:
    """
    Stub handler for platform detection.

    In the modern collection flow with alternate entry points, platform detection
    is only needed when starting from the Discovery flow path. When users select
    assets directly via the UI, this handler should be bypassed.
    """

    def __init__(
        self,
        flow_context,
        state_manager,
        services,
        unified_flow_management,
        crewai_service=None,
    ):
        """Initialize platform detection handler"""
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management
        self.crewai_service = crewai_service
        logger.info("⚠️  PlatformDetectionHandler initialized (stub implementation)")

    async def detect_platforms(self, state, config, initialization_result):
        """
        Stub platform detection - returns empty result.

        In the modern flow, platform detection should be skipped when assets
        are pre-selected via the UI (alternate entry point).
        """
        logger.info("⚠️  Platform detection skipped - using pre-selected assets from UI")

        return {
            "status": "skipped",
            "reason": "assets_pre_selected",
            "message": "Platform detection not needed for UI-selected assets",
            "platforms_detected": [],
            "selected_assets": initialization_result.get("selected_assets", []),
        }
