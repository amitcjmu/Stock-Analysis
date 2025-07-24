"""
Flow Repair Service

Handles orphaned data repair and flow reconciliation for the Master Flow Orchestrator.
Extracted from MasterFlowOrchestrator to follow single responsibility principle.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class FlowRepairService:
    """Service for repairing orphaned data and reconciling flow states"""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo

    async def generate_repair_options(
        self, flow_id: str, discovered_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate repair options for orphaned data"""
        try:
            repair_options = {
                "flow_id": flow_id,
                "available_repairs": [],
                "recommended_action": "none",
                "confidence": 0.0,
            }

            # Analyze discovered data to generate repair options
            if "orphaned_discovery_flows" in discovered_data:
                orphaned_flows = discovered_data["orphaned_discovery_flows"]
                if orphaned_flows:
                    repair_options["available_repairs"].append(
                        {
                            "type": "link_discovery_flow",
                            "description": f"Link to {len(orphaned_flows)} orphaned discovery flow(s)",
                            "affected_items": len(orphaned_flows),
                            "confidence": 0.8,
                            "details": orphaned_flows,
                        }
                    )

            if "orphaned_data_imports" in discovered_data:
                orphaned_imports = discovered_data["orphaned_data_imports"]
                if orphaned_imports:
                    repair_options["available_repairs"].append(
                        {
                            "type": "link_data_import",
                            "description": f"Link to {len(orphaned_imports)} orphaned data import(s)",
                            "affected_items": len(orphaned_imports),
                            "confidence": 0.7,
                            "details": orphaned_imports,
                        }
                    )

            if "orphaned_assets" in discovered_data:
                orphaned_assets = discovered_data["orphaned_assets"]
                if orphaned_assets:
                    repair_options["available_repairs"].append(
                        {
                            "type": "link_assets",
                            "description": f"Link to {len(orphaned_assets)} orphaned asset(s)",
                            "affected_items": len(orphaned_assets),
                            "confidence": 0.6,
                            "details": orphaned_assets,
                        }
                    )

            # Determine recommended action
            if repair_options["available_repairs"]:
                # Recommend the repair with highest confidence and most items
                best_repair = max(
                    repair_options["available_repairs"],
                    key=lambda x: (x["confidence"], x["affected_items"]),
                )
                repair_options["recommended_action"] = best_repair["type"]
                repair_options["confidence"] = best_repair["confidence"]

            return repair_options

        except Exception as e:
            logger.error(f"Error generating repair options: {e}")
            return {"flow_id": flow_id, "error": str(e), "available_repairs": []}

    async def repair_orphaned_data(
        self,
        flow_id: str,
        repair_type: str,
        target_items: List[str],
        create_master_flow: bool = True,
    ) -> Dict[str, Any]:
        """Repair orphaned data by linking it to the specified flow"""
        try:
            logger.info(f"🔧 Starting repair of orphaned data for flow {flow_id}")
            logger.info(
                f"Repair type: {repair_type}, Target items: {len(target_items)}"
            )

            repair_result = {
                "flow_id": flow_id,
                "repair_type": repair_type,
                "items_processed": 0,
                "items_repaired": 0,
                "errors": [],
                "master_flow_created": False,
            }

            # Create master flow if requested and doesn't exist
            if create_master_flow:
                master_flow_created = await self._ensure_master_flow_exists(flow_id)
                repair_result["master_flow_created"] = master_flow_created

            # Perform specific repair based on type
            if repair_type == "link_discovery_flow":
                result = await self._repair_orphaned_discovery_flows(
                    flow_id, target_items
                )
            elif repair_type == "link_data_import":
                result = await self._repair_orphaned_data_imports(flow_id, target_items)
            elif repair_type == "link_assets":
                result = await self._repair_orphaned_assets(flow_id, target_items)
            else:
                raise ValueError(f"Unknown repair type: {repair_type}")

            repair_result.update(result)

            logger.info(
                f"✅ Repair completed: {repair_result['items_repaired']}/{repair_result['items_processed']} items repaired"
            )
            return repair_result

        except Exception as e:
            logger.error(f"Error repairing orphaned data: {e}")
            return {
                "flow_id": flow_id,
                "error": str(e),
                "items_processed": 0,
                "items_repaired": 0,
            }

    async def _ensure_master_flow_exists(self, flow_id: str) -> bool:
        """Ensure master flow exists, create if it doesn't"""
        try:
            # Check if master flow already exists
            existing_flow = await self.master_repo.get_by_flow_id(flow_id)
            if existing_flow:
                logger.info(f"Master flow {flow_id} already exists")
                return False

            # Create master flow
            flow_data = {
                "flow_id": uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id,
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "user_id": self.context.user_id,
                "flow_type": "unified_discovery",  # Default type
                "flow_name": f"Repaired Flow {flow_id[:8]}",
                "flow_status": "repairing",
                "flow_configuration": {
                    "created_via": "repair_service",
                    "repair_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "flow_persistence_data": {},
            }

            await self.master_repo.create(flow_data)
            logger.info(f"✅ Created master flow {flow_id} for repair")
            return True

        except Exception as e:
            logger.error(f"Error ensuring master flow exists: {e}")
            return False

    async def _repair_orphaned_discovery_flows(
        self, flow_id: str, target_items: List[str]
    ) -> Dict[str, Any]:
        """Repair orphaned discovery flows by linking them to master flow"""
        try:
            items_processed = 0
            items_repaired = 0
            errors = []

            for item_id in target_items:
                try:
                    items_processed += 1

                    # Update discovery flow to reference the master flow
                    query = text(
                        """
                        UPDATE discovery_flows 
                        SET master_flow_id = :flow_id,
                            updated_at = NOW()
                        WHERE id = :item_id
                        AND client_account_id = :client_id
                        AND engagement_id = :engagement_id
                    """
                    )

                    result = await self.db.execute(
                        query,
                        {
                            "flow_id": flow_id,
                            "item_id": item_id,
                            "client_id": self.context.client_account_id,
                            "engagement_id": self.context.engagement_id,
                        },
                    )

                    if result.rowcount > 0:
                        items_repaired += 1
                        logger.info(
                            f"✅ Linked discovery flow {item_id} to master flow {flow_id}"
                        )
                    else:
                        errors.append(
                            f"Discovery flow {item_id} not found or already linked"
                        )

                except Exception as e:
                    errors.append(f"Error linking discovery flow {item_id}: {str(e)}")
                    logger.error(f"Error linking discovery flow {item_id}: {e}")

            await self.db.commit()

            return {
                "items_processed": items_processed,
                "items_repaired": items_repaired,
                "errors": errors,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error repairing orphaned discovery flows: {e}")
            return {
                "items_processed": len(target_items),
                "items_repaired": 0,
                "errors": [str(e)],
            }

    async def _repair_orphaned_data_imports(
        self, flow_id: str, target_items: List[str]
    ) -> Dict[str, Any]:
        """Repair orphaned data imports by linking them to master flow"""
        try:
            items_processed = 0
            items_repaired = 0
            errors = []

            for item_id in target_items:
                try:
                    items_processed += 1

                    # Update data import to reference the master flow
                    query = text(
                        """
                        UPDATE data_imports 
                        SET master_flow_id = :flow_id,
                            updated_at = NOW()
                        WHERE id = :item_id
                        AND client_account_id = :client_id
                        AND engagement_id = :engagement_id
                    """
                    )

                    result = await self.db.execute(
                        query,
                        {
                            "flow_id": flow_id,
                            "item_id": item_id,
                            "client_id": self.context.client_account_id,
                            "engagement_id": self.context.engagement_id,
                        },
                    )

                    if result.rowcount > 0:
                        items_repaired += 1
                        logger.info(
                            f"✅ Linked data import {item_id} to master flow {flow_id}"
                        )
                    else:
                        errors.append(
                            f"Data import {item_id} not found or already linked"
                        )

                except Exception as e:
                    errors.append(f"Error linking data import {item_id}: {str(e)}")
                    logger.error(f"Error linking data import {item_id}: {e}")

            await self.db.commit()

            return {
                "items_processed": items_processed,
                "items_repaired": items_repaired,
                "errors": errors,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error repairing orphaned data imports: {e}")
            return {
                "items_processed": len(target_items),
                "items_repaired": 0,
                "errors": [str(e)],
            }

    async def _repair_orphaned_assets(
        self, flow_id: str, target_items: List[str]
    ) -> Dict[str, Any]:
        """Repair orphaned assets by linking them to master flow"""
        try:
            items_processed = 0
            items_repaired = 0
            errors = []

            for item_id in target_items:
                try:
                    items_processed += 1

                    # Update asset to reference the master flow
                    query = text(
                        """
                        UPDATE assets 
                        SET master_flow_id = :flow_id,
                            updated_at = NOW()
                        WHERE id = :item_id
                        AND client_account_id = :client_id
                        AND engagement_id = :engagement_id
                    """
                    )

                    result = await self.db.execute(
                        query,
                        {
                            "flow_id": flow_id,
                            "item_id": item_id,
                            "client_id": self.context.client_account_id,
                            "engagement_id": self.context.engagement_id,
                        },
                    )

                    if result.rowcount > 0:
                        items_repaired += 1
                        logger.info(
                            f"✅ Linked asset {item_id} to master flow {flow_id}"
                        )
                    else:
                        errors.append(f"Asset {item_id} not found or already linked")

                except Exception as e:
                    errors.append(f"Error linking asset {item_id}: {str(e)}")
                    logger.error(f"Error linking asset {item_id}: {e}")

            await self.db.commit()

            return {
                "items_processed": items_processed,
                "items_repaired": items_repaired,
                "errors": errors,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error repairing orphaned assets: {e}")
            return {
                "items_processed": len(target_items),
                "items_repaired": 0,
                "errors": [str(e)],
            }

    async def summarize_orphaned_data(
        self, discovered_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize orphaned data for reporting"""
        try:
            summary = {
                "total_orphaned_items": 0,
                "categories": {},
                "recommendations": [],
                "repair_complexity": "low",
            }

            # Summarize orphaned discovery flows
            orphaned_flows = discovered_data.get("orphaned_discovery_flows", [])
            if orphaned_flows:
                summary["categories"]["discovery_flows"] = {
                    "count": len(orphaned_flows),
                    "items": [
                        {
                            "id": flow.get("id"),
                            "flow_id": flow.get("flow_id"),
                            "status": flow.get("status"),
                            "created_at": flow.get("created_at"),
                        }
                        for flow in orphaned_flows
                    ],
                }
                summary["total_orphaned_items"] += len(orphaned_flows)
                summary["recommendations"].append(
                    {
                        "type": "link_discovery_flows",
                        "priority": "high",
                        "description": f"Link {len(orphaned_flows)} orphaned discovery flows",
                    }
                )

            # Summarize orphaned data imports
            orphaned_imports = discovered_data.get("orphaned_data_imports", [])
            if orphaned_imports:
                summary["categories"]["data_imports"] = {
                    "count": len(orphaned_imports),
                    "items": [
                        {
                            "id": imp.get("id"),
                            "filename": imp.get("filename"),
                            "status": imp.get("status"),
                            "created_at": imp.get("created_at"),
                        }
                        for imp in orphaned_imports
                    ],
                }
                summary["total_orphaned_items"] += len(orphaned_imports)
                summary["recommendations"].append(
                    {
                        "type": "link_data_imports",
                        "priority": "medium",
                        "description": f"Link {len(orphaned_imports)} orphaned data imports",
                    }
                )

            # Summarize orphaned assets
            orphaned_assets = discovered_data.get("orphaned_assets", [])
            if orphaned_assets:
                summary["categories"]["assets"] = {
                    "count": len(orphaned_assets),
                    "items": [
                        {
                            "id": asset.get("id"),
                            "name": asset.get("name"),
                            "asset_type": asset.get("asset_type"),
                            "created_at": asset.get("created_at"),
                        }
                        for asset in orphaned_assets
                    ],
                }
                summary["total_orphaned_items"] += len(orphaned_assets)
                summary["recommendations"].append(
                    {
                        "type": "link_assets",
                        "priority": "low",
                        "description": f"Link {len(orphaned_assets)} orphaned assets",
                    }
                )

            # Determine repair complexity
            if summary["total_orphaned_items"] > 10:
                summary["repair_complexity"] = "high"
            elif summary["total_orphaned_items"] > 5:
                summary["repair_complexity"] = "medium"

            return summary

        except Exception as e:
            logger.error(f"Error summarizing orphaned data: {e}")
            return {"error": str(e), "total_orphaned_items": 0, "categories": {}}
