"""
Asset Service Base Module

Core AssetService class initialization and utility methods.
Provides foundation for controlled asset creation and management.

CC: Service layer for asset operations following repository pattern
"""

import logging
import uuid
from typing import Dict, Any, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.asset_repository import AssetRepository
from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class AssetService:
    """Service for controlled asset operations"""

    def __init__(
        self, db: AsyncSession, context: Union[RequestContext, Dict[str, Any]]
    ):
        """
        Initialize asset service with database session and context

        Args:
            db: Database session from orchestrator
            context: RequestContext (ServiceRegistry pattern) or Dict (legacy pattern)
        """
        self.db = db

        # Handle both ServiceRegistry pattern (RequestContext) and legacy pattern (Dict)
        if isinstance(context, RequestContext):
            # ServiceRegistry pattern - convert RequestContext to context_info
            self.context_info = {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": context.user_id,
                "flow_id": context.flow_id,
            }
            self._request_context = context
        else:
            # Legacy pattern - use context dict directly
            self.context_info = context
            self._request_context = None

        # CRITICAL FIX: Pass tenant context to AssetRepository
        # Repository requires these for multi-tenant scoping
        client_account_id = (
            str(self.context_info.get("client_account_id"))
            if self.context_info.get("client_account_id")
            else None
        )
        engagement_id = (
            str(self.context_info.get("engagement_id"))
            if self.context_info.get("engagement_id")
            else None
        )

        self.repository = AssetRepository(
            db, client_account_id=client_account_id, engagement_id=engagement_id
        )

    def _get_uuid(self, value: Any) -> Optional[uuid.UUID]:
        """
        Safely convert value to UUID

        Args:
            value: String UUID, UUID object, or None

        Returns:
            UUID object or None
        """
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value

        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID value: {value}")
            return None

    async def _extract_context_ids(
        self, asset_data: Dict[str, Any]
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Extract and validate context IDs from asset data."""
        client_id = self._get_uuid(
            asset_data.get("client_account_id")
            or self.context_info.get("client_account_id")
        )
        engagement_id = self._get_uuid(
            asset_data.get("engagement_id") or self.context_info.get("engagement_id")
        )

        if not client_id or not engagement_id:
            raise ValueError(
                "Missing required tenant context (client_id, engagement_id)"
            )

        return client_id, engagement_id

    async def _resolve_flow_ids(
        self, asset_data: Dict[str, Any], flow_id: str
    ) -> tuple[str, str, uuid.UUID, uuid.UUID]:
        """Resolve various flow IDs from asset data and parameters."""
        # Honor explicit flow IDs if provided, fallback to flow_id parameter
        master_flow_id = asset_data.pop("master_flow_id", None) or flow_id
        discovery_flow_id = asset_data.pop("discovery_flow_id", None)

        # Extract raw_import_records_id for linking
        raw_import_records_id = self._get_uuid(
            asset_data.pop("raw_import_records_id", None)
        )

        # If no discovery_flow_id, lookup from master_flow_id
        # CC: Fix - discovery_flows have flow_id == master_flow_id, not a separate master_flow_id column
        if not discovery_flow_id and master_flow_id:
            try:
                from app.models.discovery_flow import DiscoveryFlow
                from sqlalchemy import select

                # Try looking up by flow_id first (which should equal master_flow_id)
                result = await self.db.execute(
                    select(DiscoveryFlow.flow_id).where(
                        DiscoveryFlow.flow_id == master_flow_id
                    )
                )
                discovery_flow = result.scalar_one_or_none()
                if discovery_flow:
                    discovery_flow_id = str(discovery_flow)
                    logger.info(
                        f"✅ Found discovery_flow_id {discovery_flow_id} for master_flow_id {master_flow_id}"
                    )
                else:
                    # If master_flow_id is the discovery flow ID itself, use it
                    discovery_flow_id = master_flow_id
                    logger.info(
                        f"📌 Using master_flow_id as discovery_flow_id: {discovery_flow_id}"
                    )
            except Exception as e:
                logger.warning(f"Could not lookup discovery_flow_id: {e}")
                # Fallback to using master_flow_id as discovery_flow_id
                discovery_flow_id = master_flow_id

        # Use provided flow IDs or fallback to context
        effective_flow_id = self._get_uuid(
            master_flow_id
            or flow_id
            or asset_data.get("flow_id")
            or self.context_info.get("flow_id")
        )

        logger.info(
            f"🔗 Associating asset with master_flow_id: {master_flow_id}, discovery_flow_id: {discovery_flow_id}"
        )

        return (
            master_flow_id,
            discovery_flow_id,
            raw_import_records_id,
            effective_flow_id,
        )

    async def _find_existing_asset(
        self, name: str, client_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Check for existing asset with same name in same context."""
        from app.models.asset import Asset
        from sqlalchemy import select, and_

        try:
            stmt = select(Asset).where(
                and_(
                    Asset.name == name,
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to check for existing asset: {e}")
            return None

    async def create_asset(self, asset_data: Dict[str, Any], flow_id: str = None):
        """
        Create an asset with proper validation and idempotency.

        Args:
            asset_data: Asset information to create
            flow_id: Optional flow ID for backward compatibility

        Returns:
            Created asset or existing asset if duplicate
        """
        # Import here to avoid circular imports
        from app.models.asset import AssetStatus
        from app.services.asset_service.helpers import (
            extract_context_ids,
            get_smart_asset_name,
            resolve_flow_ids,
            convert_numeric_fields,
        )
        from app.services.asset_service.child_table_helpers import (
            create_child_records_if_needed,
        )
        from datetime import datetime

        try:
            # Extract context IDs
            client_id, engagement_id = await extract_context_ids(
                asset_data, self.context_info
            )

            # Generate smart asset name
            smart_name = get_smart_asset_name(asset_data)

            # Check for existing asset (idempotency)
            existing = await self._find_existing_asset(
                name=smart_name,
                client_id=client_id,
                engagement_id=engagement_id,
            )

            if existing:
                logger.info(
                    f"Asset already exists: {existing.name} (ID: {existing.id})"
                )
                return existing

            # Resolve flow IDs
            (
                master_flow_id,
                discovery_flow_id,
                raw_import_records_id,
                effective_flow_id,
            ) = await resolve_flow_ids(asset_data, flow_id)

            # Convert numeric fields
            numeric_fields = convert_numeric_fields(asset_data)

            # Create asset using repository
            created_asset = await self.repository.create_no_commit(
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
                fqdn=asset_data.get("fqdn"),
                mac_address=asset_data.get("mac_address"),
                environment=asset_data.get("environment", "Unknown"),
                location=asset_data.get("location"),
                datacenter=asset_data.get("datacenter"),
                rack_location=asset_data.get("rack_location"),
                availability_zone=asset_data.get("availability_zone"),
                operating_system=asset_data.get("operating_system"),
                os_version=asset_data.get("os_version"),
                **numeric_fields,
                business_owner=asset_data.get("business_owner"),
                technical_owner=asset_data.get("technical_owner"),
                department=asset_data.get("department"),
                application_name=asset_data.get("application_name"),
                technology_stack=asset_data.get("technology_stack"),
                criticality=asset_data.get("criticality", "Medium"),
                business_criticality=asset_data.get("business_criticality", "Medium"),
                migration_complexity=asset_data.get("migration_complexity"),
                # CMDB Fields
                business_unit=asset_data.get("business_unit"),
                vendor=asset_data.get("vendor"),
                application_type=asset_data.get("application_type"),
                lifecycle=asset_data.get("lifecycle"),
                hosting_model=asset_data.get("hosting_model"),
                server_role=asset_data.get("server_role"),
                security_zone=asset_data.get("security_zone"),
                database_type=asset_data.get("database_type"),
                database_version=asset_data.get("database_version"),
                database_size_gb=asset_data.get("database_size_gb"),
                pii_flag=asset_data.get("pii_flag"),
                application_data_classification=asset_data.get(
                    "application_data_classification"
                ),
                cpu_utilization_percent_max=asset_data.get(
                    "cpu_utilization_percent_max"
                ),
                memory_utilization_percent_max=asset_data.get(
                    "memory_utilization_percent_max"
                ),
                storage_free_gb=asset_data.get("storage_free_gb"),
                has_saas_replacement=asset_data.get("has_saas_replacement"),
                risk_level=asset_data.get("risk_level"),
                tshirt_size=asset_data.get("tshirt_size"),
                proposed_treatmentplan_rationale=asset_data.get(
                    "proposed_treatmentplan_rationale"
                ),
                annual_cost_estimate=asset_data.get("annual_cost_estimate"),
                status=AssetStatus.DISCOVERED,
                migration_status=AssetStatus.DISCOVERED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                custom_attributes=asset_data.get("attributes", {})
                or asset_data.get("custom_attributes", {}),
                discovery_method="service_api",
                discovery_source=asset_data.get("discovery_source", "Service API"),
                discovery_timestamp=datetime.utcnow(),
                imported_by=asset_data.get("imported_by"),
                imported_at=asset_data.get("imported_at"),
                source_filename=asset_data.get("source_filename"),
                raw_data=asset_data,
            )

            # Create child table records if data exists
            await create_child_records_if_needed(
                self.db, created_asset, asset_data, client_id, engagement_id
            )

            logger.info(
                f"✅ Asset created via service: {created_asset.name} (ID: {created_asset.id})"
            )
            return created_asset

        except Exception as e:
            logger.error(f"❌ Asset service failed to create asset: {e}")
            raise
