"""
Workflow Service for Asset Migration Workflow Management.
Handles workflow status initialization and progression logic.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime
import logging

from app.models.asset import Asset, AssetStatus
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service for managing asset workflow progression."""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None):
        self.db = db
        self.client_account_id = client_account_id
        self.asset_repo = AssetRepository(db, client_account_id)
    
    async def initialize_workflow_status_for_existing_assets(self) -> Dict[str, int]:
        """
        Initialize workflow status for existing assets based on data completeness.
        Maps existing data completeness to appropriate workflow phase.
        """
        
        logger.info("Initializing workflow status for existing assets...")
        
        # Get all assets without workflow status
        query = select(Asset).where(
            or_(
                Asset.discovery_status.is_(None),
                Asset.mapping_status.is_(None),
                Asset.cleanup_status.is_(None),
                Asset.assessment_readiness.is_(None)
            )
        )
        
        if self.client_account_id:
            query = query.where(Asset.client_account_id == self.client_account_id)
        
        result = await self.db.execute(query)
        assets = result.scalars().all()
        
        stats = {
            "total_processed": 0,
            "discovery_completed": 0,
            "mapping_in_progress": 0,
            "cleanup_in_progress": 0,
            "assessment_ready": 0,
            "errors": 0
        }
        
        for asset in assets:
            try:
                # Determine workflow status based on existing data
                workflow_status = self._determine_initial_workflow_status(asset)
                
                # Update asset with workflow status
                asset.discovery_status = workflow_status["discovery_status"]
                asset.mapping_status = workflow_status["mapping_status"]
                asset.cleanup_status = workflow_status["cleanup_status"]
                asset.assessment_readiness = workflow_status["assessment_readiness"]
                
                # Update statistics
                stats["total_processed"] += 1
                if workflow_status["discovery_status"] == "completed":
                    stats["discovery_completed"] += 1
                if workflow_status["mapping_status"] == "in_progress":
                    stats["mapping_in_progress"] += 1
                if workflow_status["cleanup_status"] == "in_progress":
                    stats["cleanup_in_progress"] += 1
                if workflow_status["assessment_readiness"] == "ready":
                    stats["assessment_ready"] += 1
                
            except Exception as e:
                logger.error(f"Error initializing workflow for asset {asset.id}: {e}")
                stats["errors"] += 1
        
        # Commit all changes
        await self.db.commit()
        
        logger.info(f"Workflow initialization completed: {stats}")
        return stats
    
    async def advance_asset_workflow(
        self, 
        asset_id: int, 
        target_phase: str, 
        force: bool = False,
        notes: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Advance an asset's workflow to the target phase.
        
        Returns:
            Tuple of (success, blocking_issues)
        """
        
        asset = await self.db.get(Asset, asset_id)
        if not asset:
            return False, ["Asset not found"]
        
        # Validate advancement
        if not force:
            blocking_issues = self._validate_workflow_advancement(asset, target_phase)
            if blocking_issues:
                return False, blocking_issues
        
        # Update workflow status
        success = self._update_workflow_status(asset, target_phase)
        if success:
            await self.db.commit()
            logger.info(f"Advanced asset {asset_id} to {target_phase} phase")
        
        return success, []
    
    async def get_workflow_summary(self) -> Dict[str, Any]:
        """Get comprehensive workflow summary statistics."""
        
        base_query = select(Asset)
        if self.client_account_id:
            base_query = base_query.where(Asset.client_account_id == self.client_account_id)
        
        # Total assets
        total_result = await self.db.execute(select(func.count(Asset.id)))
        total_assets = total_result.scalar() or 0
        
        # Phase counts
        discovery_completed = await self._count_assets_by_status("discovery_status", "completed")
        mapping_completed = await self._count_assets_by_status("mapping_status", "completed")
        cleanup_completed = await self._count_assets_by_status("cleanup_status", "completed")
        assessment_ready = await self._count_assets_by_status("assessment_readiness", "ready")
        
        # Quality metrics
        quality_metrics = await self._calculate_quality_metrics()
        
        # Phase distribution
        phase_distribution = {
            "discovery": total_assets - discovery_completed,
            "mapping": discovery_completed - mapping_completed,
            "cleanup": mapping_completed - cleanup_completed,
            "assessment_ready": assessment_ready
        }
        
        # Readiness criteria
        readiness_criteria = await self._calculate_assessment_readiness_criteria()
        
        return {
            "total_assets": total_assets,
            "discovery_completed": discovery_completed,
            "mapping_completed": mapping_completed,
            "cleanup_completed": cleanup_completed,
            "assessment_ready": assessment_ready,
            "phase_distribution": phase_distribution,
            "quality_metrics": quality_metrics,
            "readiness_criteria": readiness_criteria,
            "assessment_readiness_percentage": (assessment_ready / total_assets * 100) if total_assets > 0 else 0
        }
    
    async def get_assets_by_workflow_phase(
        self, 
        phase: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Asset]:
        """Get assets currently in a specific workflow phase."""
        
        # Build query based on phase
        if phase == "discovery":
            query = select(Asset).where(
                or_(
                    Asset.discovery_status != "completed",
                    Asset.discovery_status.is_(None)
                )
            )
        elif phase == "mapping":
            query = select(Asset).where(
                and_(
                    Asset.discovery_status == "completed",
                    or_(
                        Asset.mapping_status != "completed",
                        Asset.mapping_status.is_(None)
                    )
                )
            )
        elif phase == "cleanup":
            query = select(Asset).where(
                and_(
                    Asset.mapping_status == "completed",
                    or_(
                        Asset.cleanup_status != "completed",
                        Asset.cleanup_status.is_(None)
                    )
                )
            )
        elif phase == "assessment_ready":
            query = select(Asset).where(Asset.assessment_readiness == "ready")
        else:
            raise ValueError(f"Invalid phase: {phase}")
        
        if self.client_account_id:
            query = query.where(Asset.client_account_id == self.client_account_id)
        
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def batch_update_workflow_status(
        self, 
        asset_ids: List[int], 
        status_updates: Dict[str, str]
    ) -> Dict[str, int]:
        """Batch update workflow status for multiple assets."""
        
        stats = {"updated": 0, "errors": 0}
        
        for asset_id in asset_ids:
            try:
                asset = await self.db.get(Asset, asset_id)
                if asset:
                    # Apply status updates
                    for field, value in status_updates.items():
                        if hasattr(asset, field):
                            setattr(asset, field, value)
                    stats["updated"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error updating asset {asset_id}: {e}")
                stats["errors"] += 1
        
        await self.db.commit()
        return stats
    
    # Private helper methods
    
    def _determine_initial_workflow_status(self, asset: Asset) -> Dict[str, str]:
        """Determine initial workflow status based on existing data completeness."""
        
        # Calculate data completeness score
        completeness_score = self._calculate_data_completeness(asset)
        
        # Determine workflow status based on completeness and existing 6R readiness
        if completeness_score >= 90 and getattr(asset, 'sixr_ready', None) == 'ready':
            # High completeness and 6R ready -> Assessment ready
            return {
                "discovery_status": "completed",
                "mapping_status": "completed", 
                "cleanup_status": "completed",
                "assessment_readiness": "ready"
            }
        elif completeness_score >= 70:
            # Good completeness -> Cleanup phase
            return {
                "discovery_status": "completed",
                "mapping_status": "completed",
                "cleanup_status": "in_progress",
                "assessment_readiness": "not_ready"
            }
        elif completeness_score >= 50:
            # Moderate completeness -> Mapping phase
            return {
                "discovery_status": "completed",
                "mapping_status": "in_progress",
                "cleanup_status": "pending",
                "assessment_readiness": "not_ready"
            }
        else:
            # Low completeness -> Discovery phase
            return {
                "discovery_status": "in_progress",
                "mapping_status": "pending",
                "cleanup_status": "pending",
                "assessment_readiness": "not_ready"
            }
    
    def _calculate_data_completeness(self, asset: Asset) -> float:
        """Calculate data completeness score for an asset."""
        
        # Critical fields for migration assessment
        critical_fields = [
            'name', 'asset_type', 'hostname', 'operating_system', 
            'environment', 'business_criticality'
        ]
        
        # Optional but important fields
        important_fields = [
            'description', 'ip_address', 'cpu_cores', 'memory_gb', 
            'storage_gb', 'migration_complexity'
        ]
        
        critical_score = 0
        important_score = 0
        
        # Check critical fields (70% weight)
        for field in critical_fields:
            if hasattr(asset, field) and getattr(asset, field) is not None:
                critical_score += 1
        
        # Check important fields (30% weight)
        for field in important_fields:
            if hasattr(asset, field) and getattr(asset, field) is not None:
                important_score += 1
        
        # Calculate weighted score
        critical_percentage = (critical_score / len(critical_fields)) * 70
        important_percentage = (important_score / len(important_fields)) * 30
        
        return critical_percentage + important_percentage
    
    def _validate_workflow_advancement(self, asset: Asset, target_phase: str) -> List[str]:
        """Validate if an asset can advance to the target phase."""
        
        blocking_issues = []
        
        if target_phase == "mapping":
            if asset.discovery_status != "completed":
                blocking_issues.append("Discovery phase not completed")
        
        elif target_phase == "cleanup":
            if asset.discovery_status != "completed":
                blocking_issues.append("Discovery phase not completed")
            if asset.mapping_status != "completed":
                blocking_issues.append("Mapping phase not completed")
        
        elif target_phase == "assessment":
            if asset.discovery_status != "completed":
                blocking_issues.append("Discovery phase not completed")
            if asset.mapping_status != "completed":
                blocking_issues.append("Mapping phase not completed")
            if asset.cleanup_status != "completed":
                blocking_issues.append("Cleanup phase not completed")
            
            # Check assessment readiness criteria
            if asset.completeness_score and asset.completeness_score < 80.0:
                blocking_issues.append("Data completeness below 80%")
            if asset.quality_score and asset.quality_score < 70.0:
                blocking_issues.append("Data quality below 70%")
        
        return blocking_issues
    
    def _update_workflow_status(self, asset: Asset, target_phase: str) -> bool:
        """Update asset workflow status to target phase."""
        
        try:
            if target_phase == "mapping":
                asset.discovery_status = "completed"
                asset.mapping_status = "in_progress"
            elif target_phase == "cleanup":
                asset.mapping_status = "completed"
                asset.cleanup_status = "in_progress"
            elif target_phase == "assessment":
                asset.cleanup_status = "completed"
                asset.assessment_readiness = "ready"
            else:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error updating workflow status: {e}")
            return False
    
    async def _count_assets_by_status(self, status_field: str, status_value: str) -> int:
        """Count assets by specific status field value."""
        
        query = select(func.count(Asset.id)).where(
            getattr(Asset, status_field) == status_value
        )
        
        if self.client_account_id:
            query = query.where(Asset.client_account_id == self.client_account_id)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def _calculate_quality_metrics(self) -> Dict[str, float]:
        """Calculate data quality metrics across assets."""
        
        # Average completeness score
        completeness_query = select(func.avg(Asset.completeness_score)).where(
            Asset.completeness_score.isnot(None)
        )
        if self.client_account_id:
            completeness_query = completeness_query.where(Asset.client_account_id == self.client_account_id)
        
        completeness_result = await self.db.execute(completeness_query)
        avg_completeness = completeness_result.scalar() or 0.0
        
        # Average quality score
        quality_query = select(func.avg(Asset.quality_score)).where(
            Asset.quality_score.isnot(None)
        )
        if self.client_account_id:
            quality_query = quality_query.where(Asset.client_account_id == self.client_account_id)
        
        quality_result = await self.db.execute(quality_query)
        avg_quality = quality_result.scalar() or 0.0
        
        return {
            "average_completeness": float(avg_completeness),
            "average_quality": float(avg_quality),
            "overall_readiness": (float(avg_completeness) + float(avg_quality)) / 2
        }
    
    async def _calculate_assessment_readiness_criteria(self) -> Dict[str, Any]:
        """Calculate assessment readiness criteria compliance."""
        
        # Count assets meeting each criterion
        mapping_ready = await self._count_assets_by_status("mapping_status", "completed")
        cleanup_ready = await self._count_assets_by_status("cleanup_status", "completed")
        
        # Count assets with sufficient data quality
        quality_query = select(func.count(Asset.id)).where(
            and_(
                Asset.completeness_score >= 80.0,
                Asset.quality_score >= 70.0
            )
        )
        if self.client_account_id:
            quality_query = quality_query.where(Asset.client_account_id == self.client_account_id)
        
        quality_result = await self.db.execute(quality_query)
        quality_ready = quality_result.scalar() or 0
        
        # Total assets
        total_result = await self.db.execute(select(func.count(Asset.id)))
        total_assets = total_result.scalar() or 0
        
        return {
            "mapping_completion_percentage": (mapping_ready / total_assets * 100) if total_assets > 0 else 0,
            "cleanup_completion_percentage": (cleanup_ready / total_assets * 100) if total_assets > 0 else 0,
            "data_quality_percentage": (quality_ready / total_assets * 100) if total_assets > 0 else 0,
            "overall_assessment_readiness": min(
                (mapping_ready / total_assets * 100) if total_assets > 0 else 0,
                (cleanup_ready / total_assets * 100) if total_assets > 0 else 0,
                (quality_ready / total_assets * 100) if total_assets > 0 else 0
            )
        } 