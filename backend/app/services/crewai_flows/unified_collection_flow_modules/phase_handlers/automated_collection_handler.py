"""
Automated Collection Handler - Stub Implementation

CC: This handler is part of the legacy ADCS system and is NOT needed for
the alternate entry point collection flows (Asset Selection → Gap Analysis).
This stub prevents import errors while the flow logic is being updated to
make automated platform collection truly optional/conditional.
"""

import logging

logger = logging.getLogger(__name__)


class AutomatedCollectionHandler:
    """
    Stub handler for automated data collection via platform adapters.

    In the modern collection flow with alternate entry points, automated collection
    is only needed when starting from the Discovery flow path with platform adapters.
    When users select assets directly via the UI and provide data manually, this
    handler should be bypassed.
    """

    def __init__(self, flow_context, state_manager, services, crewai_service=None):
        """Initialize automated collection handler"""
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service
        logger.info("⚠️  AutomatedCollectionHandler initialized (stub implementation)")

    async def automated_collection(self, state, config, platform_result):
        """
        Stub automated collection - returns empty result.

        In the modern flow, automated collection should be skipped when assets
        are pre-selected via the UI (alternate entry point) and data will be
        collected manually through questionnaires.
        """
        logger.info("⚠️  Automated collection skipped - using manual collection path")

        return {
            "status": "skipped",
            "reason": "manual_collection_path",
            "message": "Automated collection not needed - using questionnaire-based manual collection",
            "assets_collected": platform_result.get("selected_assets", []),
            "collection_method": "manual_questionnaire",
        }
