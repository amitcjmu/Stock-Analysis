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
