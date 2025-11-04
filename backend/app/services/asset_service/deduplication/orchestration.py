"""
Asset Orchestration

Main orchestration logic for create_or_update_asset with conflict detection
and deduplication. Single source of truth for asset creation/update.

CC: Main orchestration for asset creation and updates
"""

import logging
from typing import Dict, Any, Optional, Tuple, Literal, Set
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.models.asset import Asset, AssetStatus
from ..helpers import get_smart_asset_name, convert_numeric_fields
from .hierarchical_lookup import find_existing_asset_hierarchical
from .merge_strategies import enrich_asset, overwrite_asset

logger = logging.getLogger(__name__)


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


async def create_new_asset(
    service_instance, asset_data: Dict[str, Any], flow_id: Optional[str]
) -> Asset:
    """
    Create a new asset (extracted from original create_asset).

    Args:
        service_instance: AssetService instance
        asset_data: Asset data dictionary
        flow_id: Optional flow ID for context

    Returns:
        Created asset instance

    Raises:
        IntegrityError: If database constraint violation occurs
    """
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
