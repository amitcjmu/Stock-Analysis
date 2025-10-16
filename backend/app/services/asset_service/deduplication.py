"""
Asset Service Deduplication Module

Hierarchical deduplication logic and merge strategies for asset creation.
Implements create_or_update_asset with intelligent duplicate detection.

CC: Deduplication and merge strategies for asset management
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, Literal, Set, List
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.asset import Asset, AssetStatus
from .helpers import (
    get_smart_asset_name,
    convert_numeric_fields,
    convert_single_field_value,
)

logger = logging.getLogger(__name__)


# ============================================================================
# FIELD MERGE ALLOWLIST - CRITICAL FOR SECURITY
# ============================================================================

# Fields that CAN be merged (safe to update)
DEFAULT_ALLOWED_MERGE_FIELDS = {
    # Technical specs
    "operating_system",
    "os_version",
    "cpu_cores",
    "memory_gb",
    "storage_gb",
    # Network info
    "ip_address",
    "fqdn",
    "mac_address",
    # Infrastructure
    "environment",
    "location",
    "datacenter",
    "rack_location",
    "availability_zone",
    # Business info
    "business_owner",
    "technical_owner",
    "department",
    "application_name",
    "technology_stack",
    "criticality",
    "business_criticality",
    # Migration planning
    "six_r_strategy",
    "migration_priority",
    "migration_complexity",
    "migration_wave",
    # Metadata
    "description",
    "custom_attributes",
    # Performance metrics
    "cpu_utilization_percent",
    "memory_utilization_percent",
    "disk_iops",
    "network_throughput_mbps",
    "current_monthly_cost",
    "estimated_cloud_cost",
}

# Fields that MUST NEVER be merged (immutable identifiers and tenant context)
NEVER_MERGE_FIELDS = {
    "id",
    "client_account_id",
    "engagement_id",
    "flow_id",
    "master_flow_id",
    "discovery_flow_id",
    "assessment_flow_id",
    "planning_flow_id",
    "execution_flow_id",
    "raw_import_records_id",
    "created_at",
    "created_by",
    "name",
    "asset_name",  # Part of identity
    "hostname",  # Part of unique constraint - never merge
}


async def create_or_update_asset(
    service_instance,
    asset_data: Dict[str, Any],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
    conflict_detection_mode: bool = False,  # NEW: enable preflight conflict check
    allowed_merge_fields: Optional[Set[str]] = None,  # NEW: field allowlist for merge
) -> Tuple[Asset, Literal["created", "existed", "updated", "conflict"]]:
    """
    SINGLE SOURCE OF TRUTH for asset creation/update with optional conflict detection.

    This is the single source of truth for asset creation/update logic.
    All executors, tools, and services should use this method.

    Deduplication hierarchy (all scoped by client_account_id + engagement_id):
    1. name + asset_type
    2. hostname OR fqdn OR ip_address
    3. Smart-name normalization fallback
    4. Optional external/import identifiers

    Args:
        service_instance: AssetService instance (self)
        asset_data: Asset information
        flow_id: Optional flow ID for context
        upsert: If True, allow updates to existing assets
        merge_strategy: "enrich" (non-destructive) or "overwrite" (replace)
        conflict_detection_mode: If True, return conflicts instead of creating
        allowed_merge_fields: Set of fields allowed for merge (defaults to DEFAULT_ALLOWED_MERGE_FIELDS)

    Returns:
        Tuple of (asset, status) where status is:
        - "created": New asset was created
        - "existed": Identical asset already exists (returned unchanged)
        - "updated": Existing asset was updated
        - "conflict": Duplicate detected (only when conflict_detection_mode=True)

    NEW BEHAVIOR (conflict_detection_mode=True):
    - If duplicate exists, return (existing_asset, "conflict") immediately
    - Does NOT create or update asset
    - Caller responsible for storing conflict in asset_conflict_resolutions table

    FIELD MERGE SAFETY:
    - Only fields in allowed_merge_fields can be merged
    - Fields in NEVER_MERGE_FIELDS are always excluded
    - Default allowlist excludes tenant context and immutable identifiers

    Raises:
        ValueError: If missing required tenant context
        IntegrityError: If database constraint violation persists after retry
    """
    try:
        # Extract context IDs
        client_id, engagement_id = await service_instance._extract_context_ids(
            asset_data
        )

        # Hierarchical deduplication check
        existing_asset, match_criterion = await find_existing_asset_hierarchical(
            service_instance, asset_data, client_id, engagement_id
        )

        if existing_asset:
            logger.info(
                f"🔍 Found existing asset '{existing_asset.name}' "
                f"(ID: {existing_asset.id}) via {match_criterion}"
            )

            if conflict_detection_mode:
                # NEW PATH: Return conflict for caller to handle
                logger.info(
                    f"⚠️ Conflict detected via {match_criterion}: {existing_asset.name}"
                )
                return (existing_asset, "conflict")

            if not upsert:
                # Default: return existing unchanged
                return (existing_asset, "existed")

            # Upsert requested - merge data with field allowlist validation
            if merge_strategy == "enrich":
                # Non-destructive enrichment
                updated_asset = await enrich_asset(
                    service_instance, existing_asset, asset_data, allowed_merge_fields
                )
                logger.info(f"✨ Enriched asset '{existing_asset.name}' with new data")
            else:
                # Explicit overwrite
                updated_asset = await overwrite_asset(
                    service_instance, existing_asset, asset_data, allowed_merge_fields
                )
                logger.warning(
                    f"⚠️ Overwrote asset '{existing_asset.name}' with new data"
                )

            return (updated_asset, "updated")

        # No duplicate - create new asset
        try:
            new_asset = await create_new_asset(service_instance, asset_data, flow_id)
            logger.info(f"✅ Created new asset '{new_asset.name}' (ID: {new_asset.id})")
            return (new_asset, "created")
        except IntegrityError as ie:
            await service_instance.db.rollback()  # Prevent session invalidation
            logger.warning(
                f"⚠️ IntegrityError during asset creation (likely race condition): {ie}"
            )

            # Retry hierarchical lookup after rollback - another process may have created it
            existing_asset, match_criterion = await find_existing_asset_hierarchical(
                service_instance, asset_data, client_id, engagement_id
            )

            if existing_asset:
                logger.info(
                    f"🔄 Found asset after rollback via {match_criterion}, returning existing"
                )
                if conflict_detection_mode:
                    return (existing_asset, "conflict")
                return (existing_asset, "existed")
            else:
                # True duplicate key conflict - log and re-raise
                logger.error(f"❌ IntegrityError persists after retry: {ie}")
                raise

    except IntegrityError:
        # Already handled above, but catch here to prevent outer exception handler
        raise
    except Exception as e:
        logger.error(f"❌ create_or_update_asset failed: {e}")
        raise


async def find_existing_asset_hierarchical(
    service_instance,
    asset_data: Dict[str, Any],
    client_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Tuple[Optional[Asset], Optional[str]]:
    """
    Hierarchical deduplication check.

    Returns:
        Tuple of (asset, match_criterion) where match_criterion indicates which
        check matched: "name+type", "hostname", "fqdn", "ip", "normalized_name", etc.
    """
    # Priority 1: name + asset_type
    name = get_smart_asset_name(asset_data)
    asset_type = asset_data.get("asset_type")

    if name and asset_type:
        stmt = select(Asset).where(
            and_(
                Asset.name == name,
                Asset.asset_type == asset_type,
                Asset.client_account_id == client_id,
                Asset.engagement_id == engagement_id,
            )
        )
        result = await service_instance.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if asset:
            return (asset, "name+type")

    # Priority 2: hostname OR fqdn OR ip_address
    identifiers = []
    if asset_data.get("hostname"):
        identifiers.append(Asset.hostname == asset_data["hostname"])
    if asset_data.get("fqdn"):
        identifiers.append(Asset.fqdn == asset_data["fqdn"])
    if asset_data.get("ip_address"):
        identifiers.append(Asset.ip_address == asset_data["ip_address"])

    if identifiers:
        stmt = select(Asset).where(
            and_(
                or_(*identifiers),
                Asset.client_account_id == client_id,
                Asset.engagement_id == engagement_id,
            )
        )
        result = await service_instance.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if asset:
            match_field = (
                "hostname"
                if asset_data.get("hostname")
                else ("fqdn" if asset_data.get("fqdn") else "ip")
            )
            return (asset, match_field)

    # Priority 3: Smart-name normalization fallback
    if name:
        normalized_name = name.lower().strip().replace(" ", "-")
        stmt = select(Asset).where(
            and_(
                Asset.name.ilike(f"%{normalized_name}%"),
                Asset.client_account_id == client_id,
                Asset.engagement_id == engagement_id,
            )
        )
        result = await service_instance.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if asset:
            return (asset, "normalized_name")

    # Priority 4: Optional external/import identifiers
    external_id = asset_data.get("external_id") or asset_data.get("import_id")
    if external_id:
        stmt = select(Asset).where(
            and_(
                or_(
                    Asset.external_id == external_id,
                    Asset.raw_data["import_id"].astext == str(external_id),
                ),
                Asset.client_account_id == client_id,
                Asset.engagement_id == engagement_id,
            )
        )
        result = await service_instance.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if asset:
            return (asset, "external_id")

    return (None, None)


async def create_new_asset(
    service_instance, asset_data: Dict[str, Any], flow_id: Optional[str]
) -> Asset:
    """Create a new asset (extracted from original create_asset)."""
    # Generate smart asset name
    smart_name = get_smart_asset_name(asset_data)
    client_id, engagement_id = await service_instance._extract_context_ids(asset_data)

    # Resolve flow IDs
    (
        master_flow_id,
        discovery_flow_id,
        raw_import_records_id,
        effective_flow_id,
    ) = await service_instance._resolve_flow_ids(asset_data, flow_id)

    # Convert numeric fields
    numeric_fields = convert_numeric_fields(asset_data)

    # Use repository's keyword-based create method
    create_method = (
        service_instance.repository.create_no_commit
        if service_instance._request_context
        else service_instance.repository.create
    )

    try:
        created_asset = await create_method(
            client_account_id=client_id,
            engagement_id=engagement_id,
            flow_id=effective_flow_id,
            master_flow_id=master_flow_id if master_flow_id else effective_flow_id,
            discovery_flow_id=(
                discovery_flow_id if discovery_flow_id else effective_flow_id
            ),
            raw_import_records_id=raw_import_records_id,
            name=smart_name,
            asset_name=smart_name,
            asset_type=asset_data.get("asset_type", "Unknown"),
            description=asset_data.get("description", "Discovered by agent"),
            hostname=asset_data.get("hostname"),
            ip_address=asset_data.get("ip_address"),
            environment=asset_data.get("environment", "Unknown"),
            operating_system=asset_data.get("operating_system"),
            **numeric_fields,
            business_owner=asset_data.get("business_unit")
            or asset_data.get("owner")
            or asset_data.get("business_owner"),
            technical_owner=asset_data.get("technical_owner")
            or asset_data.get("owner"),
            department=asset_data.get("department"),
            criticality=asset_data.get("criticality", "Medium"),
            business_criticality=asset_data.get("business_criticality", "Medium"),
            status=AssetStatus.DISCOVERED,
            migration_status=AssetStatus.DISCOVERED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            custom_attributes=asset_data.get("attributes", {})
            or asset_data.get("custom_attributes", {}),
            discovery_method="service_api",
            discovery_source=asset_data.get("discovery_source", "Service API"),
            discovery_timestamp=datetime.utcnow(),
            raw_data=asset_data,
        )

        return created_asset

    except IntegrityError as ie:
        await service_instance.db.rollback()  # Prevent session invalidation

        # Differentiate unique constraint violations (race conditions) from other errors
        # The exact message depends on database backend (PostgreSQL, MySQL, etc.)
        error_msg = str(ie.orig).lower() if hasattr(ie, "orig") else str(ie).lower()

        # Check if this is a unique constraint violation (can be retried)
        is_unique_violation = any(
            keyword in error_msg
            for keyword in ["unique constraint", "duplicate key", "duplicate entry"]
        )

        if is_unique_violation:
            # This is likely a race condition - another process created the asset
            # The caller's retry logic will handle this by finding the existing asset
            logger.warning(
                f"⚠️ Unique constraint violation (likely race condition) for '{smart_name}': {ie}"
            )
            raise  # Re-raise for caller's race-condition handling
        else:
            # This is a different integrity issue (NOT NULL, foreign key, CHECK constraint)
            # These are unrecoverable and should not trigger retry logic
            logger.error(
                f"❌ Unrecoverable IntegrityError in create_new_asset for '{smart_name}': {ie}"
            )
            raise  # Re-raise, but caller should not retry


async def enrich_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Non-destructive enrichment: add new fields, keep existing values.

    NEW: Field allowlist validation.
    - Only merge fields in allowlist that don't exist in existing asset
    - Skip fields in NEVER_MERGE_FIELDS
    - Log warnings for attempted protected field merges
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist
        if field not in allowlist:
            continue

        # Skip if field in never-merge list
        if field in NEVER_MERGE_FIELDS:
            logger.warning(f"⚠️ Attempted to merge protected field '{field}' - skipping")
            continue

        # Only update if existing value is None/empty
        # CC FIX: Use 'is not None' instead of truthiness to allow zero values (0, 0.0, etc.)
        if value is not None and not getattr(existing, field, None):
            # CC FIX: Convert value to proper type (fixes cpu_cores='8' string->int error)
            typed_value = convert_single_field_value(field, value)
            setattr(existing, field, typed_value)

    # Special handling for custom_attributes (merge dicts)
    if "custom_attributes" in new_data and "custom_attributes" in allowlist:
        existing_attrs = existing.custom_attributes or {}
        new_attrs = new_data["custom_attributes"]
        existing.custom_attributes = {**existing_attrs, **new_attrs}

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


async def overwrite_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Explicit overwrite: replace allowed fields with new values.

    NEW: Implement "replace_with_new" as UPDATE (not delete+create).
    - Preserves FK relationships and audit history
    - Only updates fields in allowlist
    - Respects NEVER_MERGE_FIELDS protection
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist or in never-merge list
        if field not in allowlist or field in NEVER_MERGE_FIELDS:
            continue

        # Overwrite existing value with new value
        if value is not None:
            # CC FIX: Convert value to proper type (fixes cpu_cores='8' string->int error)
            typed_value = convert_single_field_value(field, value)
            setattr(existing, field, typed_value)

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


# ============================================================================
# BULK CONFLICT DETECTION - O(1) PER ASSET
# ============================================================================


async def bulk_prepare_conflicts(
    service_instance,
    assets_data: List[Dict[str, Any]],
    client_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Tuple[List[Dict], List[Dict]]:
    """
    NEW METHOD: Bulk prefetch for O(1) conflict detection.

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
    # NEW: name+asset_type composite for reduced false positives
    name_type_pairs = {
        (get_smart_asset_name(a), a.get("asset_type", "Unknown"))
        for a in assets_data
        if get_smart_asset_name(a)
    }

    # Step 2: Bulk fetch existing assets (ONE query per field type)
    # NEW: Chunking for very large batches (per GPT-5 feedback)
    CHUNK_SIZE = 500  # Avoid parameter limits in IN clauses

    existing_by_hostname = {}
    existing_by_ip = {}
    existing_by_name_type = {}  # NEW: name+type composite key

    if hostnames:
        # Process in chunks to avoid parameter limits
        hostname_list = list(hostnames)
        for i in range(0, len(hostname_list), CHUNK_SIZE):
            chunk = hostname_list[i : i + CHUNK_SIZE]
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
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
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.ip_address.in_(chunk),
                    Asset.ip_address.is_not(None),
                    Asset.ip_address != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            for asset in result.scalars().all():
                existing_by_ip[asset.ip_address] = asset
        logger.debug(f"  Found {len(existing_by_ip)} existing assets by IP")

    # NEW: Query by name+asset_type composite (reduces false positives)
    if name_type_pairs:
        # Process in chunks to avoid parameter limits
        names_only = list({name for name, _ in name_type_pairs})
        for i in range(0, len(names_only), CHUNK_SIZE):
            chunk = names_only[i : i + CHUNK_SIZE]
            stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                    Asset.name.in_(chunk),
                    Asset.name.is_not(None),
                    Asset.name != "",
                )
            )
            result = await service_instance.db.execute(stmt)
            # Build dict with (name, asset_type) composite key
            for asset in result.scalars().all():
                key = (asset.name, asset.asset_type or "Unknown")
                existing_by_name_type[key] = asset
        logger.debug(
            f"  Found {len(existing_by_name_type)} existing assets by name+type"
        )

    # Step 3: O(1) lookup for each asset
    conflict_free = []
    conflicts = []

    for asset_data in assets_data:
        hostname = asset_data.get("hostname")
        ip = asset_data.get("ip_address")
        name = get_smart_asset_name(asset_data)
        asset_type = asset_data.get("asset_type", "Unknown")  # NEW: for composite key

        # Check hostname first (highest priority unique constraint)
        if hostname and hostname in existing_by_hostname:
            existing = existing_by_hostname[hostname]
            conflicts.append(
                {
                    "conflict_type": "hostname",  # Aligned with CHECK constraint
                    "conflict_key": hostname,
                    "existing_asset_id": existing.id,
                    "existing_asset_data": serialize_asset_for_comparison(existing),
                    "new_asset_data": asset_data,
                }
            )
            continue

        # Check IP address
        if ip and ip in existing_by_ip:
            existing = existing_by_ip[ip]
            conflicts.append(
                {
                    "conflict_type": "ip_address",  # Aligned with CHECK constraint
                    "conflict_key": ip,
                    "existing_asset_id": existing.id,
                    "existing_asset_data": serialize_asset_for_comparison(existing),
                    "new_asset_data": asset_data,
                }
            )
            continue

        # Check name+asset_type composite (NEW: reduces false positives)
        name_type_key = (name, asset_type)
        if name and name_type_key in existing_by_name_type:
            existing = existing_by_name_type[name_type_key]
            conflicts.append(
                {
                    "conflict_type": "name",  # Aligned with CHECK constraint
                    "conflict_key": f"{name} ({asset_type})",  # Include type in display
                    "existing_asset_id": existing.id,
                    "existing_asset_data": serialize_asset_for_comparison(existing),
                    "new_asset_data": asset_data,
                }
            )
            continue

        # No conflict found
        conflict_free.append(asset_data)

    logger.info(
        f"✅ Bulk conflict detection complete: "
        f"{len(conflict_free)} conflict-free, {len(conflicts)} conflicts"
    )

    return conflict_free, conflicts


def serialize_asset_for_comparison(asset: Asset) -> Dict:
    """
    Extract safe fields for UI comparison with PII hygiene.

    NEW (per GPT-5 feedback):
    - Limits snapshot fields to defined allowlist (prevents sensitive data leakage)
    - Redacts custom_attributes by default (may contain PII)
    - Only includes fields necessary for conflict resolution

    Note: UI should still apply display restrictions for additional safety.
    """
    # NEW: Only include fields from DEFAULT_ALLOWED_MERGE_FIELDS (PII hygiene)
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


# ============================================================================
# EXISTING METHODS - BATCH PREFETCH UTILITIES
# ============================================================================


def _build_prefetch_criteria(assets_data: list[Dict[str, Any]]) -> tuple:
    """Extract unique identifiers from assets for batch prefetch."""
    names = set()
    hostnames = set()
    fqdns = set()
    ip_addresses = set()

    for asset_data in assets_data:
        name = get_smart_asset_name(asset_data)
        if name:
            names.add(name)
        if asset_data.get("hostname"):
            hostnames.add(asset_data["hostname"])
        if asset_data.get("fqdn"):
            fqdns.add(asset_data["fqdn"])
        if asset_data.get("ip_address"):
            ip_addresses.add(asset_data["ip_address"])

    return names, hostnames, fqdns, ip_addresses


def _build_lookup_indexes(existing_assets: list[Asset]) -> tuple:
    """Build in-memory indexes from prefetched assets."""
    name_index = {a.name: a for a in existing_assets if a.name}
    hostname_index = {a.hostname: a for a in existing_assets if a.hostname}
    fqdn_index = {a.fqdn: a for a in existing_assets if a.fqdn}
    ip_index = {a.ip_address: a for a in existing_assets if a.ip_address}
    return name_index, hostname_index, fqdn_index, ip_index


def _find_existing_in_indexes(
    asset_data: Dict[str, Any],
    name_index: dict,
    hostname_index: dict,
    fqdn_index: dict,
    ip_index: dict,
) -> Optional[Asset]:
    """Find existing asset using hierarchical dedup logic against indexes."""
    name = get_smart_asset_name(asset_data)
    asset_type = asset_data.get("asset_type")

    # Priority 1: name + type (check both match)
    if name and asset_type and name in name_index:
        potential = name_index[name]
        if potential.asset_type == asset_type:
            return potential

    # Priority 2: hostname/fqdn/ip (any match)
    if asset_data.get("hostname") and asset_data["hostname"] in hostname_index:
        return hostname_index[asset_data["hostname"]]
    elif asset_data.get("fqdn") and asset_data["fqdn"] in fqdn_index:
        return fqdn_index[asset_data["fqdn"]]
    elif asset_data.get("ip_address") and asset_data["ip_address"] in ip_index:
        return ip_index[asset_data["ip_address"]]

    return None


async def bulk_create_or_update_assets(
    service_instance,
    assets_data: list[Dict[str, Any]],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
) -> list[Tuple[Asset, Literal["created", "existed", "updated"]]]:
    """
    Batch-optimized asset creation with single prefetch query.

    Eliminates N+1 query problem by prefetching all potential duplicates
    in one query, then processing assets in memory.

    Args:
        service_instance: AssetService instance (self)
        assets_data: List of asset data dictionaries
        flow_id: Optional flow ID for context
        upsert: If True, allow updates to existing assets
        merge_strategy: "enrich" (non-destructive) or "overwrite" (replace)

    Returns:
        List of (asset, status) tuples
    """
    if not assets_data:
        return []

    # Extract context IDs once
    client_id, engagement_id = await service_instance._extract_context_ids(
        assets_data[0]
    )

    # Build prefetch criteria from all assets
    names, hostnames, fqdns, ip_addresses = _build_prefetch_criteria(assets_data)

    # Single prefetch query with OR conditions
    conditions = [
        Asset.client_account_id == client_id,
        Asset.engagement_id == engagement_id,
    ]

    or_conditions = []
    if names:
        or_conditions.append(Asset.name.in_(names))
    if hostnames:
        or_conditions.append(Asset.hostname.in_(hostnames))
    if fqdns:
        or_conditions.append(Asset.fqdn.in_(fqdns))
    if ip_addresses:
        or_conditions.append(Asset.ip_address.in_(ip_addresses))

    if or_conditions:
        conditions.append(or_(*or_conditions))
        stmt = select(Asset).where(and_(*conditions))
        result = await service_instance.db.execute(stmt)
        existing_assets = result.scalars().all()
        name_index, hostname_index, fqdn_index, ip_index = _build_lookup_indexes(
            existing_assets
        )
    else:
        # No lookup criteria - all will be new
        name_index = hostname_index = fqdn_index = ip_index = {}

    # Process each asset using prefetched data
    results = []
    new_assets = []

    for asset_data in assets_data:
        existing = _find_existing_in_indexes(
            asset_data, name_index, hostname_index, fqdn_index, ip_index
        )

        if existing:
            if not upsert:
                results.append((existing, "existed"))
            else:
                if merge_strategy == "enrich":
                    updated = await enrich_asset(service_instance, existing, asset_data)
                else:
                    updated = await overwrite_asset(
                        service_instance, existing, asset_data
                    )
                results.append((updated, "updated"))
        else:
            # Create new asset (will be bulk inserted)
            new_asset = await create_new_asset(service_instance, asset_data, flow_id)
            new_assets.append(new_asset)
            results.append((new_asset, "created"))

    # Bulk flush all new assets at once
    if new_assets:
        try:
            await service_instance.db.flush()
        except IntegrityError as ie:
            await service_instance.db.rollback()  # Prevent session invalidation
            logger.error(
                f"❌ IntegrityError during bulk flush of {len(new_assets)} assets: {ie}"
            )
            raise  # Re-raise to let caller handle the failure

    logger.info(
        f"✅ Batch processed {len(assets_data)} assets: "
        f"{len(new_assets)} created, "
        f"{len([r for r in results if r[1] == 'existed'])} existed, "
        f"{len([r for r in results if r[1] == 'updated'])} updated"
    )

    return results
