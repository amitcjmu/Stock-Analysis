"""
Utility functions and helper methods for discovery flow management.

Extracted from flow_manager.py to reduce file size while maintaining clean separation of concerns.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.
    CC FIX: Prevents 'Object of type UUID is not JSON serializable' errors
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuids_to_str(item) for item in obj]
    return obj


def calculate_readiness_scores(flow: DiscoveryFlow) -> dict:
    """
    Calculate readiness scores based on flow state and completion data.

    This is business logic that belongs in the service layer, not repository.

    Args:
        flow: The discovery flow to calculate readiness for

    Returns:
        Dictionary with readiness scores
    """
    state_data = flow.crewai_state_data or {}

    # Calculate readiness based on completed phases and data quality
    completed_phases = [
        phase
        for phase, data in state_data.get("phases", {}).items()
        if data.get("completed", False)
    ]

    # Base readiness calculation
    total_phases = 6  # data_import, attribute_mapping, data_cleansing, inventory, dependencies, tech_debt
    phase_completion_score = (
        len(completed_phases) / total_phases * 100 if total_phases > 0 else 0
    )

    # Calculate individual dimension scores
    data_quality_score = state_data.get("data_quality_score", 80.0)
    mapping_completeness = state_data.get("mapping_completeness", 90.0)
    asset_coverage = min(100.0, len(flow.assets) * 10)  # 10% per asset, max 100%
    dependency_analysis = 95.0 if "dependencies" in completed_phases else 70.0

    # Overall readiness is weighted average
    overall_readiness = (
        phase_completion_score * 0.3
        + data_quality_score * 0.25
        + mapping_completeness * 0.25
        + asset_coverage * 0.1
        + dependency_analysis * 0.1
    )

    # Assessment ready if overall > 70% and critical phases complete
    assessment_ready = overall_readiness >= 70.0 and all(
        phase in completed_phases
        for phase in ["data_import", "attribute_mapping", "inventory"]
    )

    return {
        "overall": round(overall_readiness, 2),
        "data_quality": data_quality_score,
        "mapping_completeness": mapping_completeness,
        "asset_coverage": round(asset_coverage, 2),
        "dependency_analysis": dependency_analysis,
        "assessment_ready": assessment_ready,
    }


async def update_master_flow_completion(
    flow_id: str,
    master_flow_repo: CrewAIFlowStateExtensionsRepository,
) -> bool:
    """
    Update the master flow state to completed status.

    This cross-repository coordination belongs in the service layer.

    Args:
        flow_id: The flow ID
        master_flow_repo: Repository for master flow operations

    Returns:
        True if successful, False otherwise
    """
    try:
        # Update master flow status using the master flow repository
        await master_flow_repo.update_flow_status(
            flow_id=flow_id,
            status="completed",
            phase_data={
                "completed_by": "discovery_flow_service",
                "completion_timestamp": datetime.utcnow().isoformat(),
            },
            collaboration_entry={
                "timestamp": datetime.utcnow().isoformat(),
                "action": "flow_completed",
                "source": "discovery_flow_service",
                "message": "Discovery flow completed successfully - all phases finished",
            },
        )

        logger.info(f"✅ Master flow state updated to completed for: {flow_id}")
        return True

    except Exception as e:
        logger.warning(f"⚠️ Failed to update master flow completion for {flow_id}: {e}")
        # Don't fail the whole operation if master flow update fails
        return False


async def create_extensions_record(
    flow_id: str,
    data_import_id: str,
    user_id: str,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    master_flow_repo: CrewAIFlowStateExtensionsRepository,
    context: RequestContext,
    auto_commit: bool = True,
) -> None:
    """
    Create corresponding crewai_flow_state_extensions record.

    Args:
        flow_id: The flow ID
        data_import_id: Data import identifier
        user_id: User who initiated the flow
        raw_data: Raw data for the flow
        metadata: Additional metadata
        master_flow_repo: Repository for master flow operations
        context: Request context with tenant information
        auto_commit: Whether to commit automatically
    """
    logger.info(f"🔧 Creating crewai_flow_state_extensions record: {flow_id}")

    try:
        # CC FIX: Convert UUIDs to strings to prevent JSON serialization errors
        flow_configuration = convert_uuids_to_str(
            {
                "data_import_id": data_import_id,
                "raw_data_count": len(raw_data),
                "metadata": metadata or {},
            }
        )

        initial_state = convert_uuids_to_str(
            {
                "created_from": "discovery_flow_service",
                "raw_data_sample": raw_data[:2] if raw_data else [],
                "creation_timestamp": datetime.utcnow().isoformat(),
            }
        )

        # CC FIX: Pass auto_commit parameter to master flow creation
        extensions_record = await master_flow_repo.create_master_flow(
            flow_id=flow_id,  # Same flow_id as discovery flow
            flow_type="discovery",
            user_id=user_id or (str(context.user_id) if context.user_id else "system"),
            flow_name=f"Discovery Flow {flow_id[:8]}",
            flow_configuration=flow_configuration,
            initial_state=initial_state,
            auto_commit=auto_commit,
        )
        logger.info(f"✅ Extensions record created: {extensions_record.flow_id}")
    except Exception as ext_error:
        logger.error(f"❌ Failed to create extensions record: {ext_error}")
        # CC FIX: Raise the error instead of just warning (critical for transaction integrity)
        raise


async def create_assets_from_inventory(
    flow: DiscoveryFlow,
    asset_data_list: List[Dict[str, Any]],
    flow_repo: DiscoveryFlowRepository,
) -> List[Asset]:
    """
    Create discovery assets from inventory phase results.

    Args:
        flow: The discovery flow
        asset_data_list: List of asset data to create
        flow_repo: Repository for flow operations

    Returns:
        List of created Asset objects
    """
    try:
        logger.info(
            f"📦 Creating {len(asset_data_list)} assets from inventory for flow: {flow.flow_id}"
        )

        assets = await flow_repo.asset_commands.create_assets_from_discovery(
            discovery_flow_id=flow.id,
            asset_data_list=asset_data_list,
            discovered_in_phase="inventory",
        )

        logger.info(f"✅ Created {len(assets)} assets from inventory")
        return assets

    except Exception as e:
        logger.error(f"❌ Failed to create assets from inventory: {e}")
        raise
