"""
Asset Service Deduplication Module

Hierarchical deduplication logic and merge strategies for asset creation.
Implements create_or_update_asset with intelligent duplicate detection.

CC: Deduplication and merge strategies for asset management
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, Literal
from datetime import datetime

from sqlalchemy import select, and_, or_

from app.models.asset import Asset, AssetStatus
from .helpers import get_smart_asset_name, convert_numeric_fields

logger = logging.getLogger(__name__)


async def create_or_update_asset(
    service_instance,
    asset_data: Dict[str, Any],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
) -> Tuple[Asset, Literal["created", "existed", "updated"]]:
    """
    Unified asset creation with hierarchical deduplication and merge strategies.

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

    Returns:
        Tuple of (asset, status) where status is:
        - "created": New asset was created
        - "existed": Identical asset already exists (returned unchanged)
        - "updated": Existing asset was updated

    Raises:
        ValueError: If missing required tenant context
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

            if not upsert:
                # Default: return existing unchanged
                return (existing_asset, "existed")

            # Upsert requested - merge data
            if merge_strategy == "enrich":
                # Non-destructive enrichment
                updated_asset = await enrich_asset(
                    service_instance, existing_asset, asset_data
                )
                logger.info(f"✨ Enriched asset '{existing_asset.name}' with new data")
            else:
                # Explicit overwrite
                updated_asset = await overwrite_asset(
                    service_instance, existing_asset, asset_data
                )
                logger.warning(
                    f"⚠️ Overwrote asset '{existing_asset.name}' with new data"
                )

            return (updated_asset, "updated")

        # No duplicate - create new asset
        new_asset = await create_new_asset(service_instance, asset_data, flow_id)
        logger.info(f"✅ Created new asset '{new_asset.name}' (ID: {new_asset.id})")

        return (new_asset, "created")

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
        technical_owner=asset_data.get("technical_owner") or asset_data.get("owner"),
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


async def enrich_asset(
    service_instance, existing: Asset, new_data: Dict[str, Any]
) -> Asset:
    """Non-destructive enrichment: add new fields, keep existing values."""
    # Update only if new value provided and old value is None/empty
    if new_data.get("description") and not existing.description:
        existing.description = new_data["description"]

    if new_data.get("operating_system") and not existing.operating_system:
        existing.operating_system = new_data["operating_system"]

    # Merge custom_attributes
    if new_data.get("custom_attributes"):
        existing_attrs = existing.custom_attributes or {}
        new_attrs = new_data["custom_attributes"]
        existing.custom_attributes = {**existing_attrs, **new_attrs}

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


async def overwrite_asset(
    service_instance, existing: Asset, new_data: Dict[str, Any]
) -> Asset:
    """Explicit overwrite: replace all fields with new values."""
    existing.description = new_data.get("description", existing.description)
    existing.operating_system = new_data.get(
        "operating_system", existing.operating_system
    )
    existing.custom_attributes = new_data.get(
        "custom_attributes", existing.custom_attributes
    )
    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing
