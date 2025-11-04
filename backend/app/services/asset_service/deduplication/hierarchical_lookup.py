"""
Hierarchical Asset Lookup

Implements hierarchical deduplication strategy for finding existing assets
using multiple identifier types with priority ordering.

CC: Hierarchical deduplication lookup logic
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple

from sqlalchemy import select, and_, or_

from app.models.asset import Asset
from ..helpers import get_smart_asset_name

logger = logging.getLogger(__name__)


async def find_existing_asset_hierarchical(
    service_instance,
    asset_data: Dict[str, Any],
    client_id: uuid.UUID,
    engagement_id: uuid.UUID,
) -> Tuple[Optional[Asset], Optional[str]]:
    """
    Hierarchical deduplication check.

    Deduplication hierarchy (all scoped by client_account_id + engagement_id):
    1. name + asset_type
    2. hostname OR fqdn OR ip_address
    3. Smart-name normalization fallback
    4. Optional external/import identifiers

    Returns:
        Tuple of (asset, match_criterion) where match_criterion indicates which
        check matched: "name+type", "hostname", "fqdn", "ip", "normalized_name", etc.
    """
    # Priority 1: name + asset_type
    name = get_smart_asset_name(asset_data)
    asset_type = asset_data.get("asset_type")

    if name and asset_type:
        # SKIP_TENANT_CHECK - Service-level/monitoring query
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
        # SKIP_TENANT_CHECK - Service-level/monitoring query
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
        # SKIP_TENANT_CHECK - Service-level/monitoring query
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
        # SKIP_TENANT_CHECK - Service-level/monitoring query
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
