"""
Asset Service

Provides controlled asset creation and management through proper repository pattern.
This service ensures multi-tenant isolation, transactional integrity, and idempotency.

CC: Service layer for asset operations following repository pattern
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.asset import Asset, AssetStatus
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

    def _get_smart_asset_name(self, data: Dict[str, Any]) -> str:
        """Generate unique asset name from available data with intelligent fallbacks"""
        # Try explicit name field first
        if data.get("name"):
            return str(data["name"]).strip()

        # Try asset_name field
        if data.get("asset_name"):
            return str(data["asset_name"]).strip()

        # Try hostname (most common for servers/infrastructure)
        if data.get("hostname"):
            return str(data["hostname"]).strip()

        # Try application_name (for applications)
        if data.get("application_name"):
            return str(data["application_name"]).strip()

        # Try primary_application
        if data.get("primary_application"):
            return str(data["primary_application"]).strip()

        # Try IP address as identifier
        if data.get("ip_address"):
            return f"Asset-{data['ip_address']}"

        # Last resort: generate unique name based on asset type and UUID
        asset_type = data.get("asset_type", "Asset").replace(" ", "-")
        unique_id = str(uuid.uuid4())[:8]  # Short UUID for readability
        return f"{asset_type}-{unique_id}"

    def _safe_int_convert(self, value, default=None):
        """Convert value to integer with safe error handling"""
        if value is None or value == "":
            return default
        try:
            return int(float(str(value)))  # Handle both int and float strings
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert '{value}' to integer, using default {default}"
            )
            return default

    def _safe_float_convert(self, value, default=None):
        """Convert value to float with safe error handling"""
        if value is None or value == "":
            return default
        try:
            return float(str(value))
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert '{value}' to float, using default {default}"
            )
            return default

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

    def _convert_numeric_fields(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert all numeric fields with proper error handling."""
        return {
            # INTEGER fields
            "cpu_cores": self._safe_int_convert(asset_data.get("cpu_cores"), None),
            "migration_priority": self._safe_int_convert(
                asset_data.get("migration_priority"), 5
            ),
            "migration_wave": self._safe_int_convert(
                asset_data.get("migration_wave"), None
            ),
            # FLOAT fields
            "memory_gb": self._safe_float_convert(asset_data.get("memory_gb"), None),
            "storage_gb": self._safe_float_convert(asset_data.get("storage_gb"), None),
            "cpu_utilization_percent": self._safe_float_convert(
                asset_data.get("cpu_utilization_percent"), None
            ),
            "memory_utilization_percent": self._safe_float_convert(
                asset_data.get("memory_utilization_percent"), None
            ),
            "disk_iops": self._safe_float_convert(asset_data.get("disk_iops"), None),
            "network_throughput_mbps": self._safe_float_convert(
                asset_data.get("network_throughput_mbps"), None
            ),
            "completeness_score": self._safe_float_convert(
                asset_data.get("completeness_score"), None
            ),
            "quality_score": self._safe_float_convert(
                asset_data.get("quality_score"), None
            ),
            "confidence_score": self._safe_float_convert(
                asset_data.get("confidence_score"), None
            ),
            "current_monthly_cost": self._safe_float_convert(
                asset_data.get("current_monthly_cost"), None
            ),
            "estimated_cloud_cost": self._safe_float_convert(
                asset_data.get("estimated_cloud_cost"), None
            ),
            "assessment_readiness_score": self._safe_float_convert(
                asset_data.get("assessment_readiness_score"), None
            ),
        }

    async def create_asset(
        self, asset_data: Dict[str, Any], flow_id: str = None
    ) -> Optional[Asset]:
        """
        Create an asset with proper validation and idempotency

        Args:
            asset_data: Asset information to create
            flow_id: Optional flow ID for backward compatibility

        Returns:
            Created asset or existing asset if duplicate
        """
        try:
            # Extract context IDs - handle both string and UUID types
            client_id, engagement_id = await self._extract_context_ids(asset_data)

            # Generate smart asset name
            smart_name = self._get_smart_asset_name(asset_data)

            logger.info(
                f"🏷️ Generating asset name: '{smart_name}' from data keys: {list(asset_data.keys())}"
            )

            # Check for existing asset (idempotency) using smart name
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
            ) = await self._resolve_flow_ids(asset_data, flow_id)

            # Convert numeric fields
            numeric_fields = self._convert_numeric_fields(asset_data)

            # Use repository's keyword-based create method
            # CRITICAL FIX: Always use create_no_commit to avoid individual commits
            # The orchestrator will handle the final commit
            create_method = self.repository.create_no_commit

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

    async def _find_existing_asset(
        self, name: str, client_id: uuid.UUID, engagement_id: uuid.UUID
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
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to check for existing asset: {e}")
            return None

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

    async def bulk_create_assets(
        self, assets_data: List[Dict[str, Any]]
    ) -> List[Asset]:
        """
        Create multiple assets without committing

        CRITICAL FIX: Services never commit/rollback - orchestrator owns transaction

        Args:
            assets_data: List of asset data dictionaries

        Returns:
            List of created assets
        """
        created_assets = []

        try:
            for asset_data in assets_data:
                asset = await self.create_asset(asset_data)
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
