"""
Flow Handler Navigation Operations
Handles navigation guidance for flows
"""

import logging
from typing import Any, Dict

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class FlowHandlerNavigation:
    """Handles flow navigation operations"""

    def __init__(self, context: RequestContext):
        self.context = context

    async def get_navigation_guidance(
        self, flow_id: str, current_phase: str
    ) -> Dict[str, Any]:
        """Get navigation guidance using flow repository"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                # Direct repository call - no HTTP needed
                flow = await flow_repo.get_by_flow_id(flow_id)

                if not flow:
                    return {
                        "status": "flow_not_found",
                        "guidance": [],
                        "message": "Cannot provide guidance for non-existent flow",
                    }

                # Extract phases completed from flow model
                # Per ADR-027: Discovery v3.0.0 has only 5 phases
                phases_completed = {
                    "data_import": flow.data_import_completed,
                    "data_validation": flow.data_validation_completed,
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                }

                # Generate contextual guidance
                guidance = self._generate_guidance(phases_completed, flow_id)

                flow_data = {
                    "flow_id": str(flow.flow_id),
                    "status": flow.status,
                    "current_phase": getattr(flow, "current_phase", "data_import"),
                    "next_phase": (
                        "field_mapping"
                        if not flow.field_mapping_completed
                        else "data_cleansing"
                    ),
                    "progress": flow.progress_percentage,
                    "phases_completed": phases_completed,
                }

                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "current_phase": current_phase,
                    "guidance": guidance,
                    "flow_status": flow_data,
                }

            except Exception as e:
                logger.error(f"Error in get_navigation_guidance: {e}")
                return {"status": "error", "error": str(e), "guidance": []}

    def _generate_guidance(
        self, phases_completed: Dict[str, bool], flow_id: str
    ) -> list:
        """Generate contextual guidance based on completion status"""
        guidance = []

        # Check what's been completed and suggest next steps
        if not phases_completed.get("data_import"):
            guidance.append(
                {
                    "action": "complete_data_import",
                    "description": "Complete data import phase",
                    "priority": "high",
                    "next_url": f"/discovery/{flow_id}/data-import",
                }
            )
        elif not phases_completed.get("field_mapping"):
            guidance.append(
                {
                    "action": "complete_field_mapping",
                    "description": "Complete field mapping phase",
                    "priority": "high",
                    "next_url": f"/discovery/{flow_id}/field-mapping",
                }
            )
        elif not phases_completed.get("data_cleansing"):
            guidance.append(
                {
                    "action": "complete_data_cleansing",
                    "description": "Complete data cleansing phase",
                    "priority": "high",
                    "next_url": f"/discovery/{flow_id}/data-cleansing",
                }
            )
        elif not phases_completed.get("asset_inventory"):
            guidance.append(
                {
                    "action": "complete_asset_inventory",
                    "description": "Complete asset inventory phase",
                    "priority": "high",
                    "next_url": f"/discovery/{flow_id}/asset-inventory",
                }
            )
        elif not phases_completed.get("dependency_analysis"):
            guidance.append(
                {
                    "action": "complete_dependency_analysis",
                    "description": "Complete dependency analysis phase",
                    "priority": "medium",
                    "next_url": f"/discovery/{flow_id}/dependency-analysis",
                }
            )
        elif not phases_completed.get("tech_debt_assessment"):
            guidance.append(
                {
                    "action": "complete_tech_debt_assessment",
                    "description": "Complete technical debt assessment phase",
                    "priority": "medium",
                    "next_url": f"/discovery/{flow_id}/tech-debt-assessment",
                }
            )
        else:
            guidance.append(
                {
                    "action": "flow_complete",
                    "description": "All phases complete - ready for assessment",
                    "priority": "low",
                    "next_url": f"/assessment/{flow_id}/summary",
                }
            )

        return guidance
