"""
Database query methods for Discovery Flow Execution Engine.
Contains field mapping and flow ID retrieval methods.
"""

from typing import Any, Dict, Optional

from sqlalchemy import select

from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseQueryMixin:
    """Mixin class containing database query methods for discovery flows."""

    async def _get_approved_field_mappings(self, phase_input: Dict[str, Any]) -> Dict:
        """Get approved field mappings from database with correct model and filters"""
        try:
            # CORRECTED: Use correct import path
            from app.models.data_import.mapping import ImportFieldMapping

            data_import_id = phase_input.get("data_import_id")
            if not data_import_id:
                logger.warning("No data_import_id in phase_input")
                return {}

            # CORRECTED: Use provided session, not open new one
            session = (
                self.db_session
                if hasattr(self, "db_session") and self.db_session
                else None
            )
            if session is None:
                logger.error("No database session available for field mappings query")
                return {}

            # CORRECTED: Use status='approved' and add multi-tenant scoping with engagement_id
            filters = [
                ImportFieldMapping.data_import_id == data_import_id,
                ImportFieldMapping.status == "approved",
                ImportFieldMapping.client_account_id == self.context.client_account_id,
                ImportFieldMapping.engagement_id == self.context.engagement_id,
            ]
            result = await session.execute(select(ImportFieldMapping).where(*filters))
            mappings = result.scalars().all()

            if not mappings:
                logger.warning(
                    f"No approved field mappings found for data_import_id={data_import_id} "
                    f"client_account_id={self.context.client_account_id} "
                    f"engagement_id={self.context.engagement_id}"
                )

            # Convert to dict, exclude UNMAPPED targets
            # CRITICAL FIX: Reverse mapping - we need target -> source to look up CSV fields
            field_mappings = {
                m.target_field: m.source_field
                for m in mappings
                if m.target_field and m.target_field != "UNMAPPED"
            }

            logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")
            return field_mappings

        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve field mappings: {e}")
            return {}

    async def _get_discovery_flow_id(self, master_flow_id: str) -> Optional[str]:
        """Get internal discovery flow ID from master flow ID"""
        if not master_flow_id:
            return None

        try:
            from app.models.discovery_flow import DiscoveryFlow

            session = (
                self.db_session
                if hasattr(self, "db_session") and self.db_session
                else None
            )
            if session is None:
                logger.error(
                    "No database session available for discovery flow ID query"
                )
                return None
            result = await session.execute(
                select(DiscoveryFlow.id).where(
                    DiscoveryFlow.master_flow_id == master_flow_id
                )
            )
            discovery_flow = result.scalar_one_or_none()
            return str(discovery_flow) if discovery_flow else None
        except Exception as e:
            logger.warning(f"Could not get discovery_flow_id: {e}")
            return None
