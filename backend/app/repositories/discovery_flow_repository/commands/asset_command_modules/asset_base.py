"""
Asset Commands Base Class

Base class providing common functionality for all asset command modules.
"""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from ...queries.asset_queries import AssetQueries

logger = logging.getLogger(__name__)


class AssetCommandsBase:
    """Base class for asset commands providing common functionality"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.asset_queries = AssetQueries(db, client_account_id, engagement_id)

    def _base_custom_attributes(
        self, asset_data: dict, discovered_in_phase: str
    ) -> dict:
        """Build base custom attributes for asset creation"""
        return {
            "discovered_at": asset_data.get("discovered_at"),
            "discovered_in_phase": discovered_in_phase,
            "discovery_method": "flow_based",
            "raw_data": asset_data.get("raw_data", {}),
            "normalized_data": asset_data.get("normalized_data", {}),
            "confidence_score": asset_data.get("confidence_score", 0.0),
            "validation_status": "pending",
            "migration_ready": False,
            "migration_complexity": asset_data.get("migration_complexity", "Unknown"),
            "migration_priority": asset_data.get("migration_priority", 5),
        }
