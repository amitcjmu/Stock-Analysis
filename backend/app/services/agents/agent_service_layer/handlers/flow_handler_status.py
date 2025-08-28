"""
Flow Handler Status Operations
Handles flow status retrieval and processing
"""

import logging
from typing import Any, Dict

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from .flow_handler_helpers import FlowHandlerHelpers

logger = logging.getLogger(__name__)


class FlowHandlerStatus:
    """Handles flow status operations"""

    def __init__(self, context: RequestContext):
        self.context = context

    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get flow status prioritizing child flow operational data per ADR-012

        ADR-012: Use child flow status for operational decisions,
        master flow for lifecycle only
        """
        async with AsyncSessionLocal() as db:
            try:
                # ADR-012: First determine flow type from master flow
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                master_repo = CrewAIFlowStateExtensionsRepository(
                    db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
                master_flow = await master_repo.get_by_flow_id(flow_id)

                if not master_flow:
                    logger.info(f"Master flow not found: {flow_id}")
                    return {"status": "not_found", "flow_exists": False}

                # ADR-012: Get operational status from appropriate child flow
                if master_flow.flow_type == "discovery":
                    return await self._handle_discovery_flow_status(flow_id, db)
                elif master_flow.flow_type == "assessment":
                    return self._handle_assessment_flow_status(flow_id)
                elif master_flow.flow_type == "collection":
                    return self._handle_collection_flow_status(flow_id, master_flow)
                else:
                    return self._handle_unsupported_flow_status(flow_id, master_flow)

            except Exception as e:
                logger.error(f"[ADR-012] Error getting flow status: {e}")
                return {"status": "error", "error": str(e), "flow_exists": False}

    async def _handle_discovery_flow_status(self, flow_id: str, db) -> Dict[str, Any]:
        """Handle discovery flow status checking"""
        # Use discovery flow repository for operational status
        flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=str(self.context.engagement_id),
        )

        # Get real flow data from discovery flows table (child flow)
        flow = await flow_repo.get_by_flow_id(flow_id)

        if flow:
            logger.info(f"Found discovery flow in legacy table: {flow_id}")

            # CRITICAL FIX: Check for actual data via data_import_id
            actual_data_status = (
                await FlowHandlerHelpers.check_actual_data_via_import_id(flow)
            )

            # Merge the database completion flags with actual data detection
            actual_phases = {
                "data_import": actual_data_status.get(
                    "has_import_data", flow.data_import_completed
                ),
                "field_mapping": actual_data_status.get(
                    "has_field_mappings", flow.field_mapping_completed
                ),
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            # Determine current phase based on actual data
            current_phase = FlowHandlerHelpers.determine_actual_current_phase(
                actual_phases, flow
            )
            next_phase = FlowHandlerHelpers.determine_next_phase(actual_phases)

            return {
                "status": "success",
                "flow_exists": True,
                "flow": {
                    "flow_id": str(flow.flow_id),
                    "flow_type": "discovery",
                    "status": flow.status,
                    "current_phase": current_phase,
                    "next_phase": next_phase,
                    "progress": flow.progress_percentage,
                    "phases_completed": actual_phases,
                    "raw_data_count": actual_data_status.get("field_mapping_count", 0),
                    "field_mapping_count": actual_data_status.get(
                        "field_mapping_count", 0
                    ),
                    "data_import_id": (
                        str(flow.data_import_id) if flow.data_import_id else None
                    ),
                },
                "flow_type": "discovery",
            }
        else:
            logger.info(f"Discovery flow not found in child repository: {flow_id}")
            return {
                "status": "not_found",
                "flow_exists": False,
                "message": "Discovery flow not found in child repository",
            }

    def _handle_assessment_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Handle assessment flow status checking"""
        # TODO: Add assessment flow repository support
        logger.warning(
            f"[ADR-012] Assessment flow type not yet fully supported: {flow_id}"
        )
        return {
            "status": "not_implemented",
            "flow_exists": True,
            "message": "Assessment flows not yet supported in child flow status",
        }

    def _handle_collection_flow_status(
        self, flow_id: str, master_flow
    ) -> Dict[str, Any]:
        """Handle collection flow status checking"""
        # Collection flow support - using master flow data for now
        # TODO: Implement CollectionFlowRepository when collection-specific
        # data model is ready
        logger.info(f"[ADR-012] Collection flow using master flow data: {flow_id}")

        # Determine current phase - collection flows typically use questionnaires phase
        current_phase = "questionnaires"  # Default phase for collection flows
        if hasattr(master_flow, "get_current_phase"):
            # Try to get phase from method if available
            try:
                phase = master_flow.get_current_phase()
                if phase:
                    current_phase = phase
            except Exception:
                pass  # Use default

        return {
            "status": "success",
            "flow_exists": True,
            "flow": {
                "flow_id": flow_id,
                "flow_type": "collection",
                "status": master_flow.flow_status,
                "current_phase": current_phase,
                "progress": 0.0,  # Default progress for collection flows
                "phases_completed": {},  # Empty phases for now
                "message": "Collection flow status from master flow",
            },
            "flow_type": "collection",
        }

    def _handle_unsupported_flow_status(
        self, flow_id: str, master_flow
    ) -> Dict[str, Any]:
        """Handle unsupported flow type status checking"""
        # Other flow types - return master flow data for now
        logger.warning(
            f"[ADR-012] Unsupported flow type, using master flow: "
            f"{master_flow.flow_type}"
        )
        return {
            "status": "success",
            "flow_exists": True,
            "flow": {
                "flow_id": flow_id,
                "flow_type": master_flow.flow_type,
                "status": master_flow.flow_status,  # Using master status
                "current_phase": master_flow.current_phase,
                "message": (
                    f"Using master flow status for unsupported type: "
                    f"{master_flow.flow_type}"
                ),
            },
            "flow_type": master_flow.flow_type,
        }
