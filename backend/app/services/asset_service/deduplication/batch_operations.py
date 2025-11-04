"""
Batch Asset Operations

Implements batch-optimized asset creation with single prefetch query.
Eliminates N+1 query problem for bulk operations.

CC: Batch operations and utilities for asset deduplication
"""

import logging
from typing import Dict, Any, Optional, Tuple, Literal, List

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.asset import Asset
from ..helpers import get_smart_asset_name
from .merge_strategies import enrich_asset, overwrite_asset

logger = logging.getLogger(__name__)


def _build_prefetch_criteria(assets_data: List[Dict[str, Any]]) -> Tuple:
    """
    Extract unique identifiers from assets for batch prefetch.

    Args:
        assets_data: List of asset data dictionaries

    Returns:
        Tuple of (names, hostnames, fqdns, ip_addresses) sets
    """
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


def _build_lookup_indexes(existing_assets: List[Asset]) -> Tuple:
    """
    Build in-memory indexes from prefetched assets.

    Args:
        existing_assets: List of existing assets to index

    Returns:
        Tuple of (name_index, hostname_index, fqdn_index, ip_index) dictionaries
    """
    name_index = {a.name: a for a in existing_assets if a.name}
    hostname_index = {a.hostname: a for a in existing_assets if a.hostname}
    fqdn_index = {a.fqdn: a for a in existing_assets if a.fqdn}
    ip_index = {a.ip_address: a for a in existing_assets if a.ip_address}
    return name_index, hostname_index, fqdn_index, ip_index


def _find_existing_in_indexes(
    asset_data: Dict[str, Any],
    name_index: Dict,
    hostname_index: Dict,
    fqdn_index: Dict,
    ip_index: Dict,
) -> Optional[Asset]:
    """
    Find existing asset using hierarchical dedup logic against indexes.

    Args:
        asset_data: Asset data to search for
        name_index: Name lookup index
        hostname_index: Hostname lookup index
        fqdn_index: FQDN lookup index
        ip_index: IP address lookup index

    Returns:
        Existing asset if found, None otherwise
    """
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
    assets_data: List[Dict[str, Any]],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
) -> List[Tuple[Asset, Literal["created", "existed", "updated"]]]:
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
    # Import here to avoid circular dependency
    from .orchestration import create_new_asset

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
        stmt = select(Asset).where(and_(*conditions))  # SKIP_TENANT_CHECK
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
