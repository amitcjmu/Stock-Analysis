"""
Asset repository with context-aware multi-tenant data access.
Provides asset-specific query methods with automatic client account scoping.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
import logging

from app.models.asset import Asset, AssetDependency, WorkflowProgress, AssetStatus, SixRStrategy
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class AssetRepository(ContextAwareRepository[Asset]):
    """
    Asset repository with context-aware operations and asset-specific methods.
    """
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        """Initialize asset repository with context."""
        super().__init__(db, Asset, client_account_id, engagement_id)
    
    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Get asset by hostname with context filtering."""
        return await self.get_by_filters(hostname=hostname)
    
    async def get_by_asset_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type with context filtering."""
        return await self.get_by_filters(asset_type=asset_type)
    
    async def get_by_environment(self, environment: str) -> List[Asset]:
        """Get assets by environment with context filtering."""
        return await self.get_by_filters(environment=environment)
    
    async def get_by_status(self, status: AssetStatus) -> List[Asset]:
        """Get assets by migration status with context filtering."""
        return await self.get_by_filters(status=status)
    
    async def get_by_6r_strategy(self, strategy: SixRStrategy) -> List[Asset]:
        """Get assets by 6R strategy with context filtering."""
        return await self.get_by_filters(six_r_strategy=strategy)
    
    async def get_by_workflow_status(self, phase: str, status: str) -> List[Asset]:
        """Get assets by workflow phase status."""
        field_name = f"{phase}_status"
        if hasattr(Asset, field_name):
            return await self.get_by_filters(**{field_name: status})
        return []
    
    async def get_assessment_ready_assets(self) -> List[Asset]:
        """Get assets that are ready for assessment phase."""
        return await self.get_by_filters(assessment_readiness='ready')
    
    async def get_assets_by_import_batch(self, batch_id: str) -> List[Asset]:
        """Get assets from a specific import batch."""
        return await self.get_by_filters(import_batch_id=batch_id)
    
    async def search_assets(self, search_term: str) -> List[Asset]:
        """Search assets by name, hostname, or description."""
        query = select(Asset).where(
            or_(
                Asset.name.ilike(f"%{search_term}%"),
                Asset.hostname.ilike(f"%{search_term}%"),
                Asset.description.ilike(f"%{search_term}%"),
                Asset.asset_name.ilike(f"%{search_term}%")
            )
        )
        return await self.query_with_context(query)
    
    async def get_assets_with_dependencies(self) -> List[Asset]:
        """Get assets that have dependencies."""
        query = select(Asset).where(
            or_(
                Asset.dependencies.isnot(None),
                Asset.dependents.isnot(None),
                Asset.server_dependencies.isnot(None),
                Asset.application_dependencies.isnot(None),
                Asset.database_dependencies.isnot(None)
            )
        )
        return await self.query_with_context(query)
    
    async def get_assets_by_criticality(self, criticality: str) -> List[Asset]:
        """Get assets by business criticality."""
        return await self.get_by_filters(business_criticality=criticality)
    
    async def get_assets_by_department(self, department: str) -> List[Asset]:
        """Get assets by department."""
        return await self.get_by_filters(department=department)
    
    async def get_assets_needing_analysis(self) -> List[Asset]:
        """Get assets that need AI analysis."""
        query = select(Asset).where(
            or_(
                Asset.last_ai_analysis.is_(None),
                Asset.ai_confidence_score < 0.7,
                Asset.recommended_6r_strategy.is_(None)
            )
        )
        return await self.query_with_context(query)
    
    async def get_workflow_summary(self) -> Dict[str, Dict[str, int]]:
        """Get workflow progress summary across all phases."""
        phases = ['discovery', 'mapping', 'cleanup', 'assessment']
        statuses = ['pending', 'in_progress', 'completed', 'failed']
        
        summary = {}
        for phase in phases:
            summary[phase] = {}
            for status in statuses:
                field_name = f"{phase}_status"
                if hasattr(Asset, field_name):
                    count = await self.count(**{field_name: status})
                    summary[phase][status] = count
                else:
                    summary[phase][status] = 0
        
        return summary
    
    async def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        query = select(
            func.avg(Asset.completeness_score).label('avg_completeness'),
            func.avg(Asset.quality_score).label('avg_quality'),
            func.count(Asset.id).label('total_assets'),
            func.count(Asset.missing_critical_fields).label('assets_with_missing_fields')
        )
        query = self._apply_context_filter(query)
        
        result = await self.db.execute(query)
        row = result.first()
        
        return {
            'average_completeness': float(row.avg_completeness or 0),
            'average_quality': float(row.avg_quality or 0),
            'total_assets': row.total_assets,
            'assets_with_missing_fields': row.assets_with_missing_fields
        }
    
    async def update_workflow_status(self, asset_id: int, phase: str, status: str) -> bool:
        """Update workflow status for a specific phase."""
        field_name = f"{phase}_status"
        if hasattr(Asset, field_name):
            updated = await self.update(asset_id, **{field_name: status})
            return updated is not None
        return False
    
    async def bulk_update_workflow_status(self, asset_ids: List[int], phase: str, status: str) -> int:
        """Bulk update workflow status for multiple assets."""
        field_name = f"{phase}_status"
        if hasattr(Asset, field_name):
            return await self.bulk_update(
                filters={'id': asset_ids},
                updates={field_name: status}
            )
        return 0
    
    async def calculate_assessment_readiness(self, asset_id: int) -> str:
        """Calculate and update assessment readiness for an asset."""
        asset = await self.get_by_id(asset_id)
        if not asset:
            return 'not_ready'
        
        # Assessment readiness criteria
        mapping_complete = asset.mapping_status == 'completed'
        cleanup_complete = asset.cleanup_status == 'completed'
        quality_threshold = (asset.quality_score or 0) >= 70
        completeness_threshold = (asset.completeness_score or 0) >= 80
        
        if mapping_complete and cleanup_complete and quality_threshold and completeness_threshold:
            readiness = 'ready'
        elif mapping_complete or cleanup_complete:
            readiness = 'partial'
        else:
            readiness = 'not_ready'
        
        # Update the asset
        await self.update(asset_id, assessment_readiness=readiness)
        
        return readiness


class AssetDependencyRepository(ContextAwareRepository[AssetDependency]):
    """Asset dependency repository with context-aware operations."""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        """Initialize asset dependency repository with context."""
        super().__init__(db, AssetDependency, client_account_id, engagement_id)
    
    async def get_dependencies_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the source."""
        return await self.get_by_filters(source_asset_id=asset_id)
    
    async def get_dependents_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the target."""
        return await self.get_by_filters(target_asset_id=asset_id)
    
    async def get_by_dependency_type(self, dependency_type: str) -> List[AssetDependency]:
        """Get dependencies by type."""
        return await self.get_by_filters(dependency_type=dependency_type)
    
    async def get_critical_dependencies(self) -> List[AssetDependency]:
        """Get dependencies marked as critical."""
        return await self.get_by_filters(criticality='critical')


class WorkflowProgressRepository(ContextAwareRepository[WorkflowProgress]):
    """Workflow progress repository with context-aware operations."""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        """Initialize workflow progress repository with context."""
        super().__init__(db, WorkflowProgress, client_account_id, engagement_id)
    
    async def get_progress_for_asset(self, asset_id: int) -> List[WorkflowProgress]:
        """Get all workflow progress records for an asset."""
        return await self.get_by_filters(asset_id=asset_id)
    
    async def get_progress_by_phase(self, phase: str) -> List[WorkflowProgress]:
        """Get workflow progress for a specific phase."""
        return await self.get_by_filters(phase=phase)
    
    async def get_active_workflows(self) -> List[WorkflowProgress]:
        """Get workflows that are currently in progress."""
        return await self.get_by_filters(status='in_progress')
    
    async def update_progress(self, asset_id: int, phase: str, progress_percentage: float, notes: str = None) -> Optional[WorkflowProgress]:
        """Update progress for a specific asset and phase."""
        # Find existing progress record
        existing = await self.get_by_filters(asset_id=asset_id, phase=phase)
        
        if existing:
            # Update existing record
            progress_record = existing[0]
            return await self.update(
                progress_record.id,
                progress_percentage=progress_percentage,
                notes=notes,
                status='in_progress' if progress_percentage < 100 else 'completed'
            )
        else:
            # Create new progress record
            return await self.create(
                asset_id=asset_id,
                phase=phase,
                progress_percentage=progress_percentage,
                notes=notes,
                status='in_progress' if progress_percentage < 100 else 'completed'
            ) 