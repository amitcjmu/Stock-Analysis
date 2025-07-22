"""
Asset manager for discovery flow asset operations.
"""

import logging
import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class AssetManager:
    """Manager for discovery flow asset operations and lifecycle management."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        
        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id)
        )
    
    async def get_flow_assets(self, flow_id: str, flow_internal_id: uuid.UUID) -> List[Asset]:
        """Get all assets for a discovery flow"""
        try:
            assets = await self.flow_repo.asset_queries.get_assets_by_flow_id(flow_internal_id)
            logger.info(f"✅ Found {len(assets)} assets for flow: {flow_id}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets for flow {flow_id}: {e}")
            raise
    
    async def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type for the current client/engagement"""
        try:
            assets = await self.flow_repo.asset_queries.get_assets_by_type(asset_type)
            logger.info(f"✅ Found {len(assets)} assets of type: {asset_type}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets by type {asset_type}: {e}")
            raise
    
    async def validate_asset(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_results: Dict[str, Any] = None
    ) -> Asset:
        """Update asset validation status and results"""
        try:
            logger.info(f"🔍 Validating asset: {asset_id}, status: {validation_status}")
            
            valid_statuses = ["pending", "validated", "failed", "manual_review"]
            if validation_status not in valid_statuses:
                raise ValueError(f"Invalid validation status: {validation_status}")
            
            asset = await self.flow_repo.asset_commands.update_asset_validation(
                asset_id=asset_id,
                validation_status=validation_status,
                validation_results=validation_results
            )
            
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")
            
            logger.info(f"✅ Asset validation updated: {asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"❌ Failed to validate asset {asset_id}: {e}")
            raise
    
    async def create_assets_from_discovery(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory"
    ) -> List[Asset]:
        """Create discovery assets from phase results"""
        try:
            logger.info(f"📦 Creating {len(asset_data_list)} assets from {discovered_in_phase} phase")
            
            assets = await self.flow_repo.asset_commands.create_assets_from_discovery(
                discovery_flow_id=discovery_flow_id,
                asset_data_list=asset_data_list,
                discovered_in_phase=discovered_in_phase
            )
            
            logger.info(f"✅ Created {len(assets)} assets from {discovered_in_phase}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to create assets from {discovered_in_phase}: {e}")
            raise
    
    async def update_asset_quality_scores(
        self,
        asset_id: uuid.UUID,
        quality_score: float,
        confidence_score: float
    ) -> Asset:
        """Update asset quality and confidence scores"""
        try:
            logger.info(f"📊 Updating quality scores for asset: {asset_id}")
            
            # Validate score ranges
            if not (0.0 <= quality_score <= 1.0):
                raise ValueError(f"Quality score must be between 0.0 and 1.0: {quality_score}")
            
            if not (0.0 <= confidence_score <= 1.0):
                raise ValueError(f"Confidence score must be between 0.0 and 1.0: {confidence_score}")
            
            asset = await self.flow_repo.asset_commands.update_asset_quality_scores(
                asset_id=asset_id,
                quality_score=quality_score,
                confidence_score=confidence_score
            )
            
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")
            
            logger.info(f"✅ Asset quality scores updated: {asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"❌ Failed to update asset quality scores {asset_id}: {e}")
            raise
    
    async def get_assets_by_validation_status(self, validation_status: str) -> List[Asset]:
        """Get assets by validation status"""
        try:
            assets = await self.flow_repo.asset_queries.get_assets_by_validation_status(validation_status)
            logger.info(f"✅ Found {len(assets)} assets with validation status: {validation_status}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets by validation status {validation_status}: {e}")
            raise
    
    async def get_assets_requiring_review(self, min_confidence_threshold: float = 0.7) -> List[Asset]:
        """Get assets that require manual review based on confidence threshold"""
        try:
            assets = await self.flow_repo.asset_queries.get_assets_below_confidence_threshold(min_confidence_threshold)
            logger.info(f"✅ Found {len(assets)} assets requiring review (confidence < {min_confidence_threshold})")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets requiring review: {e}")
            raise
    
    async def bulk_validate_assets(
        self,
        asset_ids: List[uuid.UUID],
        validation_status: str,
        validation_results: Dict[str, Any] = None
    ) -> List[Asset]:
        """Bulk validate multiple assets"""
        try:
            logger.info(f"🔍 Bulk validating {len(asset_ids)} assets with status: {validation_status}")
            
            valid_statuses = ["pending", "validated", "failed", "manual_review"]
            if validation_status not in valid_statuses:
                raise ValueError(f"Invalid validation status: {validation_status}")
            
            updated_assets = []
            for asset_id in asset_ids:
                try:
                    asset = await self.validate_asset(asset_id, validation_status, validation_results)
                    updated_assets.append(asset)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to validate asset {asset_id}: {e}")
                    continue
            
            logger.info(f"✅ Bulk validation completed: {len(updated_assets)}/{len(asset_ids)} assets updated")
            return updated_assets
            
        except Exception as e:
            logger.error(f"❌ Failed to bulk validate assets: {e}")
            raise
    
    async def get_asset_summary_statistics(self, flow_id: str, flow_internal_id: uuid.UUID) -> Dict[str, Any]:
        """Get summary statistics for assets in a discovery flow"""
        try:
            assets = await self.get_flow_assets(flow_id, flow_internal_id)
            
            # Calculate summary statistics
            asset_type_counts = {}
            validation_status_counts = {}
            total_quality_score = 0.0
            total_confidence_score = 0.0
            
            for asset in assets:
                # Asset type distribution
                asset_type_counts[asset.asset_type] = asset_type_counts.get(asset.asset_type, 0) + 1
                
                # Validation status distribution
                validation_status_counts[asset.validation_status] = validation_status_counts.get(asset.validation_status, 0) + 1
                
                # Quality metrics
                total_quality_score += asset.quality_score or 0.0
                total_confidence_score += asset.confidence_score or 0.0
            
            avg_quality_score = total_quality_score / len(assets) if assets else 0.0
            avg_confidence_score = total_confidence_score / len(assets) if assets else 0.0
            
            statistics = {
                "total_count": len(assets),
                "type_distribution": asset_type_counts,
                "validation_status_distribution": validation_status_counts,
                "avg_quality_score": round(avg_quality_score, 3),
                "avg_confidence_score": round(avg_confidence_score, 3),
                "quality_metrics": {
                    "high_quality_assets": sum(1 for a in assets if (a.quality_score or 0) >= 0.8),
                    "low_confidence_assets": sum(1 for a in assets if (a.confidence_score or 0) < 0.7),
                    "unvalidated_assets": sum(1 for a in assets if a.validation_status == "pending")
                }
            }
            
            logger.info(f"✅ Asset summary statistics generated for flow: {flow_id}")
            return statistics
            
        except Exception as e:
            logger.error(f"❌ Failed to generate asset summary statistics for flow {flow_id}: {e}")
            raise
    
    async def filter_assets_by_criteria(
        self,
        flow_internal_id: uuid.UUID,
        criteria: Dict[str, Any]
    ) -> List[Asset]:
        """Filter assets by specific criteria"""
        try:
            logger.info(f"🔍 Filtering assets by criteria: {criteria}")
            
            # Get all assets for the flow
            assets = await self.flow_repo.asset_queries.get_assets_by_flow_id(flow_internal_id)
            
            # Apply filters
            filtered_assets = []
            for asset in assets:
                if self._matches_criteria(asset, criteria):
                    filtered_assets.append(asset)
            
            logger.info(f"✅ Found {len(filtered_assets)} assets matching criteria")
            return filtered_assets
            
        except Exception as e:
            logger.error(f"❌ Failed to filter assets by criteria: {e}")
            raise
    
    def _matches_criteria(self, asset: Asset, criteria: Dict[str, Any]) -> bool:
        """Check if asset matches the given criteria"""
        
        # Asset type filter
        if "asset_type" in criteria and asset.asset_type != criteria["asset_type"]:
            return False
        
        # Validation status filter
        if "validation_status" in criteria and asset.validation_status != criteria["validation_status"]:
            return False
        
        # Quality score filter
        if "min_quality_score" in criteria and (asset.quality_score or 0) < criteria["min_quality_score"]:
            return False
        
        if "max_quality_score" in criteria and (asset.quality_score or 0) > criteria["max_quality_score"]:
            return False
        
        # Confidence score filter
        if "min_confidence_score" in criteria and (asset.confidence_score or 0) < criteria["min_confidence_score"]:
            return False
        
        if "max_confidence_score" in criteria and (asset.confidence_score or 0) > criteria["max_confidence_score"]:
            return False
        
        # Created date filter
        if "created_after" in criteria and asset.created_at < criteria["created_after"]:
            return False
        
        if "created_before" in criteria and asset.created_at > criteria["created_before"]:
            return False
        
        return True