"""
Asset Conflict Detection

Implements single and bulk conflict detection with O(1) performance.
Provides conflict serialization for UI comparison.

CC: Conflict detection and serialization for asset deduplication
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy import select, and_

from app.models.asset import Asset
from ..helpers import get_smart_asset_name

logger = logging.getLogger(__name__)

# Chunking for very large batches (avoid parameter limits in IN clauses)
CHUNK_SIZE = 500


def _check_single_asset_conflict(
    asset_data: Dict[str, Any],
    existing_by_name: Dict[str, Asset],
    existing_by_name_type: Dict[Tuple[str, str], Asset],
    existing_by_hostname: Dict[str, Asset],
    existing_by_ip: Dict[str, Asset],
) -> Optional[Dict[str, Any]]:
    """
    Check if single asset conflicts with existing assets.

    Returns conflict dict if conflict found, None otherwise.
    Extracted helper to reduce bulk_prepare_conflicts complexity.

    Args:
        asset_data: Asset data to check
        existing_by_name: Name-only index (matches DB constraint)
        existing_by_name_type: Name+type composite index (for conflict details)
        existing_by_hostname: Hostname index
        existing_by_ip: IP address index

    Returns:
        Conflict dictionary or None

    Note: Environment-only matching removed (Issue #1236) - was causing
    false positives when assets had different names but same environment.
    """
    hostname = asset_data.get("hostname")
    ip = asset_data.get("ip_address")
    name = get_smart_asset_name(asset_data)
    asset_type = asset_data.get("asset_type", "Unknown")

    # CRITICAL: Check NAME ALONE first (matches DB constraint)
    # Database has UNIQUE constraint on (client_account_id, engagement_id, name)
    if name and name in existing_by_name:
        existing = existing_by_name[name]
        name_type_key = (name, asset_type)
        if name_type_key in existing_by_name_type:
            conflict_key = f"{name} ({asset_type})"
        else:
            conflict_key = (
                f"{name} (name conflict: "
                f"existing={existing.asset_type}, new={asset_type})"
            )

        return {
            "conflict_type": "name",
            "conflict_key": conflict_key,
            "existing_asset_id": existing.id,
            "existing_asset_data": serialize_asset_for_comparison(existing),
            "new_asset_data": asset_data,
        }

    # Check hostname (secondary check)
    if hostname and hostname in existing_by_hostname:
        existing = existing_by_hostname[hostname]
        return {
            "conflict_type": "hostname",
            "conflict_key": hostname,
            "existing_asset_id": existing.id,
            "existing_asset_data": serialize_asset_for_comparison(existing),
            "new_asset_data": asset_data,
        }

    # Check IP address (tertiary check)
    if ip and ip in existing_by_ip:
        existing = existing_by_ip[ip]
        return {
            "conflict_type": "ip_address",
            "conflict_key": ip,
            "existing_asset_id": existing.id,
            "existing_asset_data": serialize_asset_for_comparison(existing),
            "new_asset_data": asset_data,
        }

    # NOTE: Environment-only matching REMOVED (Issue #1236)
    # Environment is too broad and causes false positives when two unrelated
    # assets happen to be in the same environment but have different names.
    # Assets should only conflict on unique identifiers: name, hostname, or IP.

    # No conflict
    return None


async def bulk_prepare_conflicts(  # noqa: C901
    service_instance,
    assets_data: List[Dict[str, Any]],
    client_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Bulk prefetch for O(1) conflict detection.

    Performance optimization: Single query per field type (hostname/ip/name),
    then in-memory O(1) lookups. Eliminates N+1 query problem.

    Args:
        service_instance: AssetService instance
        assets_data: List of asset data dictionaries to check
        client_id: Client account UUID
        engagement_id: Engagement UUID

    Returns:
        Tuple of (conflict_free_assets, conflicting_assets_with_details)

        conflicting_assets_with_details format:
        [
            {
                "conflict_type": "duplicate_hostname",
                "conflict_key": "server-prod-01",
                "existing_asset_id": UUID,
                "existing_asset_data": {...},
                "new_asset_data": {...}
            },
            ...
        ]
    """
    if not assets_data:
        return [], []

    logger.info(f"🔍 Bulk conflict detection for {len(assets_data)} assets")

    # Step 1: Extract all unique identifiers from batch
    hostnames = {a.get("hostname") for a in assets_data if a.get("hostname")}
    ip_addresses = {a.get("ip_address") for a in assets_data if a.get("ip_address")}
    # NOTE: Environment extraction removed (Issue #1236) - environment-only matching disabled
    # name+asset_type composite for reduced false positives
    name_type_pairs = {
        (get_smart_asset_name(a), a.get("asset_type", "Unknown"))
        for a in assets_data
        if get_smart_asset_name(a)
    }

    # Step 2: Bulk fetch existing assets (ONE query per field type)
    existing_by_hostname = {}
    existing_by_ip = {}
    existing_by_name = {}  # CRITICAL FIX: name-only index (matches DB constraint)
    existing_by_name_type = {}  # name+type composite (for conflict details)

    if hostnames:
        # Process in chunks to avoid parameter limits
        hostname_list = list(hostnames)
        for i in range(0, len(hostname_list), CHUNK_SIZE):
            chunk = hostname_list[i : i + CHUNK_SIZE]
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                    Asset.hostname.in_(chunk),
                    Asset.hostname.is_not(None),
                    Asset.hostname != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            for asset in result.scalars().all():
                existing_by_hostname[asset.hostname] = asset
        logger.debug(f"  Found {len(existing_by_hostname)} existing assets by hostname")

    if ip_addresses:
        # Process in chunks to avoid parameter limits
        ip_list = list(ip_addresses)
        for i in range(0, len(ip_list), CHUNK_SIZE):
            chunk = ip_list[i : i + CHUNK_SIZE]
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                    Asset.ip_address.in_(chunk),
                    Asset.ip_address.is_not(None),
                    Asset.ip_address != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            for asset in result.scalars().all():
                existing_by_ip[asset.ip_address] = asset
        logger.debug(f"  Found {len(existing_by_ip)} existing assets by IP")

    # NOTE: Environment query REMOVED (Issue #1236)
    # Environment-only matching caused false positives - assets with same
    # environment but different names were incorrectly flagged as conflicts

    # CRITICAL FIX: Query by NAME alone (matches database constraint)
    # Database constraint: ix_assets_unique_name_per_context on (client_account_id, engagement_id, name)
    # We MUST check name alone, not name+asset_type, to match the actual constraint
    if name_type_pairs:
        # Process in chunks to avoid parameter limits
        names_only = list({name for name, _ in name_type_pairs})
        for i in range(0, len(names_only), CHUNK_SIZE):
            chunk = names_only[i : i + CHUNK_SIZE]
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                    Asset.name.in_(chunk),
                    Asset.name.is_not(None),
                    Asset.name != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            # Build BOTH indexes: name-only (for constraint matching) AND name+type (for details)
            for asset in result.scalars().all():
                # Name-only index (critical for constraint matching)
                existing_by_name[asset.name] = asset
                # Name+type composite (for better conflict messaging)
                key = (asset.name, asset.asset_type or "Unknown")
                existing_by_name_type[key] = asset
        logger.debug(
            f"  Found {len(existing_by_name)} existing assets by name (DB constraint match), "
            f"{len(existing_by_name_type)} by name+type (conflict details)"
        )

    # Step 3: O(1) lookup for each asset using helper function
    conflict_free = []
    conflicts = []

    for asset_data in assets_data:
        conflict = _check_single_asset_conflict(
            asset_data,
            existing_by_name,
            existing_by_name_type,
            existing_by_hostname,
            existing_by_ip,
        )

        if conflict:
            conflicts.append(conflict)
        else:
            conflict_free.append(asset_data)

    logger.info(
        f"✅ Bulk conflict detection complete: "
        f"{len(conflict_free)} conflict-free, {len(conflicts)} conflicts"
    )

    return conflict_free, conflicts


def serialize_asset_for_comparison(asset: Asset) -> Dict:
    """
    Extract safe fields for UI comparison with PII hygiene.

    Limits snapshot fields to defined allowlist (prevents sensitive data leakage).
    Redacts custom_attributes by default (may contain PII).
    Only includes fields necessary for conflict resolution.

    Note: UI should still apply display restrictions for additional safety.

    Args:
        asset: Asset to serialize

    Returns:
        Dictionary of safe fields for comparison
    """
    # Only include fields from DEFAULT_ALLOWED_MERGE_FIELDS (PII hygiene)
    # Excludes raw_data, custom_attributes, and other potentially sensitive fields
    return {
        "id": str(asset.id),
        "name": asset.name,
        "hostname": asset.hostname,
        "ip_address": asset.ip_address,
        "asset_type": asset.asset_type,
        "operating_system": asset.operating_system,
        "os_version": asset.os_version,
        "cpu_cores": asset.cpu_cores,
        "memory_gb": asset.memory_gb,
        "storage_gb": asset.storage_gb,
        "environment": asset.environment,
        "business_owner": asset.business_owner,
        "department": asset.department,
        "criticality": asset.criticality,
        "location": asset.location,
        "datacenter": asset.datacenter,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        # NOTE: custom_attributes explicitly excluded for PII protection
        # NOTE: raw_data explicitly excluded for PII protection
    }
