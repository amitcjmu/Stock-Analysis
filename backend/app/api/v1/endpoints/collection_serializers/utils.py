"""
Collection Flow Serializer Utilities
Utility functions for collection flow serialization operations.
"""

from typing import Any, Dict, List
from uuid import UUID

from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow


def build_cleanup_flow_details(flow: CollectionFlow) -> Dict[str, Any]:
    """Build details for a flow being cleaned up.

    Args:
        flow: Collection flow to build details for

    Returns:
        Flow details dictionary
    """
    from app.api.v1.endpoints.collection_utils import calculate_time_since_creation

    time_since_update = calculate_time_since_creation(flow.updated_at)
    estimated_size = (
        len(str(flow.collection_config or {}))
        + len(str(flow.phase_state or {}))
        + len(str(flow.collection_results or {}))
    )

    return {
        "flow_id": str(flow.flow_id),
        "status": flow.status,
        "age_hours": time_since_update.total_seconds() / 3600,
        "estimated_size": estimated_size,
    }


def normalize_tenant_ids(
    client_account_id: Any, engagement_id: Any
) -> tuple[UUID, UUID]:
    """Normalize tenant IDs to UUIDs.

    Args:
        client_account_id: Client account ID (any format)
        engagement_id: Engagement ID (any format)

    Returns:
        Tuple of (client_uuid, engagement_uuid)

    Raises:
        ValueError: If IDs cannot be converted to UUIDs
    """
    try:
        client_uuid = UUID(str(client_account_id))
        engagement_uuid = UUID(str(engagement_id))
        return client_uuid, engagement_uuid
    except Exception as e:
        raise ValueError(f"Invalid tenant identifiers: {e}")


def build_application_snapshot(application: Asset) -> Dict[str, Any]:
    """Build an application snapshot for metadata storage.

    Args:
        application: Application asset to snapshot

    Returns:
        Application snapshot dictionary
    """
    return {
        "id": str(application.id),
        "name": application.name,
        "business_criticality": application.business_criticality,
        "technology_stack": application.technology_stack,
        "architecture_pattern": application.architecture_pattern,
    }


def extract_application_ids_from_assets(applications: List[Asset]) -> List[str]:
    """Extract string IDs from application assets.

    Args:
        applications: List of application assets

    Returns:
        List of application ID strings
    """
    return [str(app.id) for app in applications]
