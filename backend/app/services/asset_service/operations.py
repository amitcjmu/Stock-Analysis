"""
Asset Service Operations Module

CRUD operations for asset management including legacy methods.
Provides create_asset, bulk_create_assets, and backward compatibility.

CC: Asset CRUD operations with repository pattern
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select, and_

from app.models.asset import Asset, AssetStatus
from .helpers import get_smart_asset_name, convert_numeric_fields
from .deduplication import create_or_update_asset

logger = logging.getLogger(__name__)


async def create_asset(
    service_instance, asset_data: Dict[str, Any], flow_id: str = None
) -> Optional[Asset]:
    """
    DEPRECATED: Use create_or_update_asset() instead.

    Legacy method kept for backward compatibility.
    Delegates to create_or_update_asset() with default behavior.

    Args:
        service_instance: AssetService instance (self)
        asset_data: Asset information to create
        flow_id: Optional flow ID for backward compatibility

    Returns:
        Created asset or existing asset if duplicate
    """
    # Delegate to unified method with default behavior
    asset, status = await create_or_update_asset(
        service_instance, asset_data, flow_id, upsert=False
    )
    return asset


async def bulk_create_assets(
    service_instance, assets_data: List[Dict[str, Any]]
) -> List[Asset]:
    """
    Create multiple assets without committing

    CRITICAL FIX: Services never commit/rollback - orchestrator owns transaction

    Args:
        service_instance: AssetService instance (self)
        assets_data: List of asset data dictionaries

    Returns:
        List of created assets
    """
    created_assets = []

    try:
        for asset_data in assets_data:
            asset = await create_asset(service_instance, asset_data)
            if asset:
                created_assets.append(asset)

        # NOTE: Repository.create() commits, which is a problem
        # TODO: Add create_no_commit variant to repository pattern
        # For now, this violates the service pattern but maintains compatibility

        logger.info(f"✅ Bulk created {len(created_assets)} assets")
        return created_assets

    except Exception as e:
        # CRITICAL FIX: Services should NOT rollback - orchestrator handles this
        logger.error(f"❌ Bulk asset creation failed: {e}")
        raise  # Let orchestrator handle rollback


async def legacy_create_asset(
    service_instance, asset_data: Dict[str, Any], flow_id: str = None
) -> Optional[Asset]:
    """Original create_asset implementation - kept for reference only."""
    try:
        # Extract context IDs - handle both string and UUID types
        client_id, engagement_id = await service_instance._extract_context_ids(
            asset_data
        )

        # Generate smart asset name
        smart_name = get_smart_asset_name(asset_data)

        logger.info(
            f"🏷️ Generating asset name: '{smart_name}' from data keys: {list(asset_data.keys())}"
        )

        # Check for existing asset (idempotency) using smart name
        existing = await find_existing_asset(
            service_instance,
            name=smart_name,
            client_id=client_id,
            engagement_id=engagement_id,
        )

        if existing:
            logger.info(f"Asset already exists: {existing.name} (ID: {existing.id})")
            return existing

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
        # CRITICAL FIX: Always use create_no_commit to avoid individual commits
        # The orchestrator will handle the final commit
        create_method = service_instance.repository.create_no_commit

        created_asset = await create_method(
            # Multi-tenant context will be applied by repository
            client_account_id=client_id,
            engagement_id=engagement_id,
            # Flow association fields for proper asset tracking
            flow_id=effective_flow_id,  # Legacy field for backward compatibility
            master_flow_id=master_flow_id if master_flow_id else effective_flow_id,
            discovery_flow_id=(
                discovery_flow_id if discovery_flow_id else effective_flow_id
            ),
            raw_import_records_id=raw_import_records_id,  # Link to source data
            # Basic information - use smart name for both fields
            name=smart_name,
            asset_name=smart_name,
            asset_type=asset_data.get("asset_type", "Unknown"),
            description=asset_data.get("description", "Discovered by agent"),
            # Network information
            hostname=asset_data.get("hostname"),
            ip_address=asset_data.get("ip_address"),
            fqdn=asset_data.get("fqdn"),
            mac_address=asset_data.get("mac_address"),
            # Environment
            environment=asset_data.get("environment", "Unknown"),
            # Location and infrastructure
            location=asset_data.get("location"),
            datacenter=asset_data.get("datacenter"),
            rack_location=asset_data.get("rack_location"),
            availability_zone=asset_data.get("availability_zone"),
            # Technical specifications - ALL CONVERTED NUMERIC VALUES
            operating_system=asset_data.get("operating_system"),
            os_version=asset_data.get("os_version"),
            **numeric_fields,
            # Business information - map fields to correct Asset model fields
            business_owner=asset_data.get("business_unit")
            or asset_data.get("owner")
            or asset_data.get("business_owner"),
            technical_owner=asset_data.get("technical_owner")
            or asset_data.get("owner"),
            department=asset_data.get("department"),
            # Application details
            application_name=asset_data.get("application_name"),
            technology_stack=asset_data.get("technology_stack"),
            # Criticality
            criticality=asset_data.get("criticality", "Medium"),
            business_criticality=asset_data.get("business_criticality", "Medium"),
            # Migration planning
            migration_complexity=asset_data.get("migration_complexity"),
            # Status
            status=AssetStatus.DISCOVERED,
            migration_status=AssetStatus.DISCOVERED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # Store full attributes as JSON
            custom_attributes=asset_data.get("attributes", {})
            or asset_data.get("custom_attributes", {}),
            # Discovery metadata
            discovery_method="service_api",
            discovery_source=asset_data.get("discovery_source", "Service API"),
            discovery_timestamp=datetime.utcnow(),
            # Import metadata
            imported_by=asset_data.get("imported_by"),
            imported_at=asset_data.get("imported_at"),
            source_filename=asset_data.get("source_filename"),
            raw_data=asset_data,
        )

        logger.info(
            f"✅ Asset created via service: {created_asset.name} (ID: {created_asset.id})"
        )
        return created_asset

    except Exception as e:
        logger.error(f"❌ Asset service failed to create asset: {e}")
        raise


async def find_existing_asset(
    service_instance, name: str, client_id: uuid.UUID, engagement_id: uuid.UUID
) -> Optional[Asset]:
    """Check for existing asset with same name in same context"""
    try:
        stmt = select(Asset).where(
            and_(
                Asset.name == name,
                Asset.client_account_id == client_id,
                Asset.engagement_id == engagement_id,
            )
        )
        result = await service_instance.db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Failed to check for existing asset: {e}")
        return None
