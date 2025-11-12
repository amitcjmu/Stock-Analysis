"""
Asset Repository Base

Main repository class that delegates to specialized query and command modules.
Maintains backward compatibility with the original AssetRepository interface.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetDependency, WorkflowProgress
from app.repositories.context_aware_repository import ContextAwareRepository

from .commands import AssetCommands, AssetDependencyCommands, WorkflowProgressCommands
from .queries import (
    AssetDependencyQueries,
    AssetQueries,
    WorkflowProgressQueries,
)

logger = logging.getLogger(__name__)


class AssetRepository(ContextAwareRepository[Asset]):
    """
    Asset repository with context-aware operations and asset-specific methods.

    This repository delegates to specialized query and command modules:
    - AssetQueries: All read operations
    - AssetCommands: All write operations
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        include_deleted: bool = False,
    ):
        """
        Initialize asset repository with context.

        Args:
            db: Database session
            client_account_id: Client account ID for tenant scoping
            engagement_id: Engagement ID for tenant scoping
            include_deleted: Whether to include soft-deleted assets (Issue #912)
        """
        super().__init__(db, Asset, client_account_id, engagement_id)
        self.include_deleted = include_deleted

        # Initialize specialized query and command handlers
        self.queries = AssetQueries(
            db, client_account_id, engagement_id, include_deleted
        )
        self.commands = AssetCommands(db, client_account_id, engagement_id)

    def _apply_context_filter(self, query):
        """
        Override to add soft delete filtering (Issue #912).

        Applies tenant scoping from parent class, then adds
        deleted_at filter unless include_deleted is True.
        """
        # Apply parent tenant scoping first
        query = super()._apply_context_filter(query)

        # Add soft delete filter unless explicitly including deleted
        if not self.include_deleted:
            query = query.where(Asset.deleted_at.is_(None))

        return query

    # ========== Query Method Delegation ==========

    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Get asset by hostname with context filtering."""
        return await self.queries.get_by_hostname(hostname)

    async def get_by_asset_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type with context filtering."""
        return await self.queries.get_by_asset_type(asset_type)

    async def get_by_environment(self, environment: str) -> List[Asset]:
        """Get assets by environment with context filtering."""
        return await self.queries.get_by_environment(environment)

    async def get_by_status(self, status: str) -> List[Asset]:
        """Get assets by migration status with context filtering."""
        return await self.queries.get_by_status(status)

    async def get_by_6r_strategy(self, strategy: str) -> List[Asset]:
        """Get assets by 6R strategy with context filtering."""
        return await self.queries.get_by_6r_strategy(strategy)

    async def get_by_workflow_status(self, phase: str, status: str) -> List[Asset]:
        """Get assets by workflow phase status."""
        return await self.queries.get_by_workflow_status(phase, status)

    async def get_assessment_ready_assets(self) -> List[Asset]:
        """Get assets that are ready for assessment phase."""
        return await self.queries.get_assessment_ready_assets()

    async def get_assets_by_import_batch(self, batch_id: str) -> List[Asset]:
        """Get assets from a specific import batch."""
        return await self.queries.get_assets_by_import_batch(batch_id)

    async def search_assets(self, search_term: str) -> List[Asset]:
        """Search assets by name, hostname, or description."""
        return await self.queries.search_assets(search_term)

    async def get_assets_with_dependencies(self) -> List[Asset]:
        """Get assets that have dependencies."""
        return await self.queries.get_assets_with_dependencies()

    async def get_assets_by_criticality(self, criticality: str) -> List[Asset]:
        """Get assets by business criticality."""
        return await self.queries.get_assets_by_criticality(criticality)

    async def get_assets_by_department(self, department: str) -> List[Asset]:
        """Get assets by department."""
        return await self.queries.get_assets_by_department(department)

    async def get_assets_needing_analysis(self) -> List[Asset]:
        """Get assets that need AI analysis."""
        return await self.queries.get_assets_needing_analysis()

    async def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        return await self.queries.get_data_quality_summary()

    async def get_workflow_summary(self) -> Dict[str, Dict[str, int]]:
        """Get workflow progress summary across all phases."""
        return await self.queries.get_workflow_summary()

    async def get_by_master_flow(self, master_flow_id: str) -> List[Asset]:
        """Get assets by master flow ID with context filtering."""
        return await self.queries.get_by_master_flow(master_flow_id)

    async def get_by_discovery_flow(self, discovery_flow_id: str) -> List[Asset]:
        """Get assets by discovery flow ID with context filtering."""
        return await self.queries.get_by_discovery_flow(discovery_flow_id)

    async def get_by_source_phase(self, source_phase: str) -> List[Asset]:
        """Get assets by source phase with context filtering."""
        return await self.queries.get_by_source_phase(source_phase)

    async def get_by_current_phase(self, current_phase: str) -> List[Asset]:
        """Get assets by current phase with context filtering."""
        return await self.queries.get_by_current_phase(current_phase)

    async def get_multi_phase_assets(self) -> List[Asset]:
        """Get assets that have progressed through multiple phases."""
        return await self.queries.get_multi_phase_assets()

    async def get_master_flow_summary(self, master_flow_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a master flow."""
        return await self.queries.get_master_flow_summary(master_flow_id)

    async def get_cross_phase_analytics(self) -> Dict[str, Any]:
        """Get analytics across all phases and master flows."""
        return await self.queries.get_cross_phase_analytics()

    # ========== Command Method Delegation ==========

    async def update_workflow_status(
        self, asset_id: int, phase: str, status: str
    ) -> bool:
        """Update workflow status for a specific phase."""
        return await self.commands.update_workflow_status(asset_id, phase, status)

    async def bulk_update_workflow_status(
        self, asset_ids: List[int], phase: str, status: str
    ) -> int:
        """Bulk update workflow status for multiple assets."""
        return await self.commands.bulk_update_workflow_status(
            asset_ids, phase, status
        )

    async def calculate_assessment_readiness(self, asset_id: int) -> str:
        """Calculate and update assessment readiness for an asset."""
        return await self.commands.calculate_assessment_readiness(asset_id)

    async def update_phase_progression(
        self, asset_id: int, new_phase: str, notes: str = None
    ) -> bool:
        """Update asset phase progression with tracking."""
        return await self.commands.update_phase_progression(
            asset_id, new_phase, notes
        )

    async def update_six_r_strategy_from_assessment(
        self,
        application_name: str,
        six_r_strategy: str,
        confidence_score: float,
        assessment_flow_id: Optional[str] = None,
    ) -> int:
        """
        Update 6R strategy for all assets matching an application name.

        This method is called after the assessment flow recommendation phase
        to persist 6R strategies back to the assets table.

        Args:
            application_name: The canonical application name
            six_r_strategy: One of: rehost, replatform, refactor, rearchitect, replace, retire
            confidence_score: Float 0.0-1.0 indicating recommendation confidence
            assessment_flow_id: Optional UUID of assessment flow for tracking

        Returns:
            Number of assets updated

        Raises:
            ValueError: If six_r_strategy is not a valid enum value
        """
        return await self.commands.update_six_r_strategy_from_assessment(
            application_name, six_r_strategy, confidence_score, assessment_flow_id
        )


class AssetDependencyRepository(ContextAwareRepository[AssetDependency]):
    """Asset dependency repository with context-aware operations."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize asset dependency repository with context."""
        super().__init__(db, AssetDependency, client_account_id, engagement_id)

        # Initialize specialized handlers
        self.queries = AssetDependencyQueries(db, client_account_id, engagement_id)
        self.commands = AssetDependencyCommands(db, client_account_id, engagement_id)

    async def get_dependencies_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the source."""
        return await self.queries.get_dependencies_for_asset(asset_id)

    async def get_dependents_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the target."""
        return await self.queries.get_dependents_for_asset(asset_id)

    async def get_by_dependency_type(
        self, dependency_type: str
    ) -> List[AssetDependency]:
        """Get dependencies by type."""
        return await self.queries.get_by_dependency_type(dependency_type)

    async def get_critical_dependencies(self) -> List[AssetDependency]:
        """Get dependencies marked as critical."""
        return await self.queries.get_critical_dependencies()


class WorkflowProgressRepository(ContextAwareRepository[WorkflowProgress]):
    """Workflow progress repository with context-aware operations."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize workflow progress repository with context."""
        super().__init__(db, WorkflowProgress, client_account_id, engagement_id)

        # Initialize specialized handlers
        self.queries = WorkflowProgressQueries(db, client_account_id, engagement_id)
        self.commands = WorkflowProgressCommands(db, client_account_id, engagement_id)

    async def get_progress_for_asset(self, asset_id: int) -> List[WorkflowProgress]:
        """Get all workflow progress records for an asset."""
        return await self.queries.get_progress_for_asset(asset_id)

    async def get_progress_by_phase(self, phase: str) -> List[WorkflowProgress]:
        """Get workflow progress for a specific phase."""
        return await self.queries.get_progress_by_phase(phase)

    async def get_active_workflows(self) -> List[WorkflowProgress]:
        """Get workflows that are currently in progress."""
        return await self.queries.get_active_workflows()

    async def update_progress(
        self, asset_id: int, phase: str, progress_percentage: float, notes: str = None
    ) -> Optional[WorkflowProgress]:
        """Update progress for a specific asset and phase."""
        return await self.commands.update_progress(
            asset_id, phase, progress_percentage, notes
        )
