"""
Unified Asset Processing Service
Consolidates asset intelligence, classification, and workflow management.
"""

import logging
from typing import Any, Dict

from .asset_processing_handlers import AssetValidationHandler, AssetWorkflowHandler

logger = logging.getLogger(__name__)


class AssetProcessingService:
    def __init__(self, config=None):
        self.config = config
        self.workflow_handler = AssetWorkflowHandler()
        self.validation_handler = AssetValidationHandler()
        self._intelligence_handler = None

    def _get_intelligence_handler(self):
        if self._intelligence_handler is None:
            from .asset_processing_handlers.asset_intelligence_handler import (
                AssetIntelligenceHandler,
            )

            self._intelligence_handler = AssetIntelligenceHandler()
        return self._intelligence_handler

    async def process_new_asset(
        self, asset_data: Dict[str, Any], client_account_id: str, engagement_id: str
    ) -> Dict[str, Any]:
        """
        Processes a new asset, from validation to workflow initiation.
        """
        intelligence_handler = self._get_intelligence_handler()

        # 1. Validate asset data
        is_valid, validation_errors = self.validation_handler.validate_asset(asset_data)
        if not is_valid:
            return {"success": False, "errors": validation_errors}

        # 2. Enrich asset with intelligence
        enriched_data = await intelligence_handler.enrich_asset(
            asset_data, client_account_id
        )

        # 3. Initiate workflow
        workflow_status = await self.workflow_handler.initiate_workflow(
            enriched_data, engagement_id
        )

        return {
            "success": True,
            "asset_id": enriched_data.get("id"),
            "workflow_status": workflow_status,
        }

    def get_service_status(self):
        intelligence_handler = self._get_intelligence_handler()
        return {
            "service_name": "AssetProcessingService",
            "handlers_initialized": {
                "intelligence": intelligence_handler is not None,
                "workflow": self.workflow_handler is not None,
                "validation": self.validation_handler is not None,
            },
        }


asset_processing_service = AssetProcessingService()
