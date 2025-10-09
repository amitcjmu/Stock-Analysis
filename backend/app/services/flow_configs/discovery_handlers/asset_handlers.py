"""
Discovery Asset Handlers

Handlers for asset creation, validation, and inventory management.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .helpers import (
    _count_asset_types,
    _create_asset_indexes,
    _map_asset_relationships,
    _prepare_cmdb_format,
    _validate_created_assets,
)

logger = logging.getLogger(__name__)


async def asset_creation_completion(
    flow_id: str, phase_name: str, phase_output: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Handle asset creation phase completion

    Performs:
    - Asset validation
    - Index creation
    - Relationship mapping
    - Integration with CMDB
    """
    try:
        logger.info(f"Handling asset creation completion for flow {flow_id}")

        assets = phase_output.get("assets", [])
        phase_output.get("creation_report", {})

        # Validate created assets
        validation_results = await _validate_created_assets(assets)

        # Create asset indexes for fast lookup
        asset_indexes = _create_asset_indexes(assets)

        # Map relationships between assets
        relationships = _map_asset_relationships(assets)

        # Prepare for CMDB integration
        cmdb_ready_assets = _prepare_cmdb_format(assets)

        # Update statistics
        statistics_update = {
            "assets_created": len(assets),
            "asset_types": _count_asset_types(assets),
            "validation_passed": validation_results["passed"],
            "validation_failed": validation_results["failed"],
            "relationships_mapped": len(relationships),
        }

        completion_result = {
            "phase_completed": True,
            "flow_id": flow_id,
            "phase": phase_name,
            "completion_time": datetime.utcnow().isoformat(),
            "assets_created": len(assets),
            "validation_results": validation_results,
            "asset_indexes": asset_indexes,
            "relationships": relationships,
            "cmdb_integration": {
                "ready": len(cmdb_ready_assets) > 0,
                "asset_count": len(cmdb_ready_assets),
            },
            "statistics_update": statistics_update,
        }

        logger.info(
            f"Asset creation completed for flow {flow_id}: {len(assets)} assets created"
        )
        return completion_result

    except Exception as e:
        logger.error(f"Asset creation completion handler error for flow {flow_id}: {e}")
        return {
            "phase_completed": False,
            "flow_id": flow_id,
            "phase": phase_name,
            "error": str(e),
            "completion_time": datetime.utcnow().isoformat(),
        }


async def asset_inventory(
    flow_id: str, phase_input: Dict[str, Any], context: Any, **kwargs
) -> Dict[str, Any]:
    """Execute asset inventory phase - creates assets from raw data using AssetInventoryExecutor"""
    logger.info(f"Executing asset inventory handler for flow {flow_id}")

    try:
        # Import the executor here to avoid circular imports
        from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor import (
            AssetInventoryExecutor,
        )

        # Create flow context for the executor
        flow_context = {
            "flow_id": flow_id,
            "master_flow_id": phase_input.get("master_flow_id", flow_id),
            "client_account_id": phase_input.get("client_account_id")
            or getattr(context, "client_account_id", None),
            "engagement_id": phase_input.get("engagement_id")
            or getattr(context, "engagement_id", None),
            "user_id": getattr(context, "user_id", None),
            "db_session": kwargs.get("db_session")
            or getattr(context, "db_session", None),
        }

        # Validate required context
        if not all([flow_context["client_account_id"], flow_context["engagement_id"]]):
            logger.error(
                f"Missing required context for asset inventory: {flow_context}"
            )
            return {
                "phase": "asset_inventory",
                "status": "failed",
                "flow_id": flow_id,
                "error": "Missing required tenant context (client_account_id, engagement_id)",
                "assets_created": 0,
            }

        # Create executor instance (no base class dependencies needed)
        executor = AssetInventoryExecutor(state=None, crew_manager=None)

        # Execute asset creation
        result = await executor.execute_asset_creation(flow_context)

        # Ensure proper return format
        # Asset inventory is the FINAL phase of discovery - flow should complete here
        result.update(
            {
                "phase": "asset_inventory",
                "flow_id": flow_id,
                "next_phase": None,  # No next phase - discovery flow complete
                "flow_complete": True,  # Mark flow as complete
            }
        )

        return result

    except Exception as e:
        logger.error(f"Asset inventory handler failed: {e}")
        return {
            "phase": "asset_inventory",
            "status": "failed",
            "flow_id": flow_id,
            "error": str(e),
            "assets_created": 0,
        }
