"""
Asset query operations for retrieving asset data.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class AssetQueries:
    """Handles asset query operations."""

    def __init__(self, context: RequestContext):
        self.context = context

    async def get_discovered_assets(
        self, flow_id: str, asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get discovered assets for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return []

                # Build query for assets
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id,
                    )
                )

                # Apply asset type filter if specified
                if asset_type:
                    asset_query = asset_query.where(Asset.asset_type == asset_type)

                # Execute query
                result = await db.execute(asset_query)
                assets = result.scalars().all()

                # Convert to response format
                asset_list = []
                for asset in assets:
                    asset_data = {
                        "id": str(asset.id),
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "asset_subtype": getattr(asset, "asset_subtype", None),
                        "status": asset.status,
                        "criticality": getattr(asset, "criticality", "medium"),
                        "quality_score": getattr(asset, "quality_score", 0.0),
                        "confidence_score": getattr(asset, "confidence_score", 0.0),
                        "validation_status": getattr(
                            asset, "validation_status", "pending"
                        ),
                        "discovery_method": getattr(
                            asset, "discovery_method", "unknown"
                        ),
                        "discovered_at": (
                            asset.created_at.isoformat() if asset.created_at else None
                        ),
                        "last_updated": (
                            asset.updated_at.isoformat() if asset.updated_at else None
                        ),
                    }
                    asset_list.append(asset_data)

                return asset_list

            except Exception as e:
                logger.error(f"Database error in get_discovered_assets: {e}")
                raise

    async def get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get relationships for a specific asset"""
        async with AsyncSessionLocal() as db:
            try:
                # Get the target asset
                asset_query = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == self.context.client_account_id,
                    )
                )
                result = await db.execute(asset_query)
                asset = result.scalar_one_or_none()

                if not asset:
                    return {
                        "status": "error",
                        "error": "Asset not found",
                        "relationships": {},
                    }

                # Initialize relationship categories
                relationships = {"depends_on": [], "dependents": [], "related": []}

                # Get other assets in the same flow for relationship analysis
                flow_assets_stmt = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == asset.discovery_flow_id,
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.id != asset.id,  # Exclude the target asset
                    )
                )

                flow_result = await db.execute(flow_assets_stmt)
                flow_assets = flow_result.scalars().all()

                # Basic relationship detection based on asset types and names
                for related_asset in flow_assets:
                    relationship_data = {
                        "id": str(related_asset.id),
                        "name": related_asset.name,
                        "type": related_asset.asset_type,
                        "relationship_type": "unknown",
                    }

                    # Simple heuristics for relationship detection
                    if asset.asset_type == related_asset.asset_type:
                        relationship_data["relationship_type"] = "same_type"
                        relationships["related"].append(relationship_data)
                    elif (
                        "database" in asset.asset_type.lower()
                        and "application" in related_asset.asset_type.lower()
                    ):
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["dependents"].append(relationship_data)
                    elif (
                        "application" in asset.asset_type.lower()
                        and "database" in related_asset.asset_type.lower()
                    ):
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["depends_on"].append(relationship_data)

                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                    "relationships": relationships,
                    "total_relationships": (
                        len(relationships["depends_on"])
                        + len(relationships["dependents"])
                        + len(relationships["related"])
                    ),
                    "relationship_summary": {
                        "dependencies": len(relationships["depends_on"]),
                        "dependents": len(relationships["dependents"]),
                        "related": len(relationships["related"]),
                    },
                }

            except Exception as e:
                logger.error(f"Database error in get_asset_relationships: {e}")
                raise
