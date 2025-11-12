"""
Asset Repository Command Operations

Handles all write operations for assets, including:
- Workflow status updates
- Assessment readiness calculation
- Phase progression tracking
- 6R strategy updates from assessment flows
"""

import logging
from typing import List, Optional

from sqlalchemy import and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.asset import Asset, AssetDependency, WorkflowProgress

logger = logging.getLogger(__name__)


class AssetCommands:
    """Command (write) operations for assets."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def update_workflow_status(
        self, asset_id: int, phase: str, status: str
    ) -> bool:
        """Update workflow status for a specific phase."""
        field_name = f"{phase}_status"
        if not hasattr(Asset, field_name):
            return False

        stmt = (
            update(Asset)
            .where(Asset.id == asset_id)
            .values(**{field_name: status})
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def bulk_update_workflow_status(
        self, asset_ids: List[int], phase: str, status: str
    ) -> int:
        """Bulk update workflow status for multiple assets."""
        field_name = f"{phase}_status"
        if not hasattr(Asset, field_name):
            return 0

        stmt = (
            update(Asset)
            .where(Asset.id.in_(asset_ids))
            .values(**{field_name: status})
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def calculate_assessment_readiness(self, asset_id: int) -> str:
        """Calculate and update assessment readiness for an asset."""
        # Fetch the asset
        query = select(Asset).where(Asset.id == asset_id)
        result = await self.db.execute(query)
        asset = result.scalars().first()

        if not asset:
            return "not_ready"

        # Assessment readiness criteria
        mapping_complete = asset.mapping_status == "completed"
        cleanup_complete = asset.cleanup_status == "completed"
        quality_threshold = (asset.quality_score or 0) >= 70
        completeness_threshold = (asset.completeness_score or 0) >= 80

        if (
            mapping_complete
            and cleanup_complete
            and quality_threshold
            and completeness_threshold
        ):
            readiness = "ready"
        elif mapping_complete or cleanup_complete:
            readiness = "partial"
        else:
            readiness = "not_ready"

        # Update the asset
        stmt = (
            update(Asset)
            .where(Asset.id == asset_id)
            .values(assessment_readiness=readiness)
        )
        await self.db.execute(stmt)

        return readiness

    async def update_phase_progression(
        self, asset_id: int, new_phase: str, notes: str = None
    ) -> bool:
        """Update asset phase progression with tracking."""
        # Fetch the asset
        query = select(Asset).where(Asset.id == asset_id)
        result = await self.db.execute(query)
        asset = result.scalars().first()

        if not asset:
            return False

        # Update current phase and add to phase history
        updates = {"current_phase": new_phase}

        # Track phase progression in phase_context
        if asset.phase_context:
            phase_context = asset.phase_context.copy()
        else:
            phase_context = {}

        if "phase_history" not in phase_context:
            phase_context["phase_history"] = []

        phase_context["phase_history"].append(
            {
                "from_phase": asset.current_phase,
                "to_phase": new_phase,
                "timestamp": func.now(),
                "notes": notes,
            }
        )

        updates["phase_context"] = phase_context

        stmt = update(Asset).where(Asset.id == asset_id).values(**updates)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

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
        # Validate 6R strategy enum value
        valid_strategies = {
            "rehost",
            "replatform",
            "refactor",
            "rearchitect",
            "replace",
            "retire",
        }
        if six_r_strategy.lower() not in valid_strategies:
            raise ValueError(
                f"[ISSUE-999] Invalid 6R strategy '{six_r_strategy}'. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )

        # Clamp confidence score to 0.0-1.0 range
        clamped_confidence = max(0.0, min(1.0, confidence_score))
        if clamped_confidence != confidence_score:
            logger.warning(
                f"[ISSUE-999] Confidence score {confidence_score} clamped to "
                f"{clamped_confidence} (valid range: 0.0-1.0)"
            )

        try:
            # Build update query with tenant scoping
            update_stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.application_name == application_name,
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                    )
                )
                .values(
                    six_r_strategy=six_r_strategy.lower(),
                    confidence_score=clamped_confidence,
                    assessment_flow_id=(
                        assessment_flow_id
                        if assessment_flow_id
                        else Asset.assessment_flow_id
                    ),
                )
            )

            result = await self.db.execute(update_stmt)
            updated_count = result.rowcount

            if updated_count > 0:
                logger.info(
                    f"[ISSUE-999] ✅ Updated {updated_count} asset(s) for application "
                    f"'{application_name}' with 6R strategy: {six_r_strategy} "
                    f"(confidence: {clamped_confidence:.2%})"
                )
            else:
                logger.warning(
                    f"[ISSUE-999] ⚠️ No assets found for application '{application_name}' "
                    f"in tenant {self.client_account_id}/{self.engagement_id}"
                )

            return updated_count

        except Exception as e:
            logger.error(
                f"[ISSUE-999] ❌ Failed to update 6R strategy for application "
                f"'{application_name}': {e}"
            )
            raise


class AssetDependencyCommands:
    """Command (write) operations for asset dependencies."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id


class WorkflowProgressCommands:
    """Command (write) operations for workflow progress."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def update_progress(
        self,
        asset_id: int,
        phase: str,
        progress_percentage: float,
        notes: str = None,
    ) -> Optional[WorkflowProgress]:
        """Update progress for a specific asset and phase."""
        # Find existing progress record
        query = select(WorkflowProgress).where(
            and_(
                WorkflowProgress.asset_id == asset_id,
                WorkflowProgress.phase == phase,
            )
        )
        result = await self.db.execute(query)
        existing = result.scalars().first()

        if existing:
            # Update existing record
            stmt = (
                update(WorkflowProgress)
                .where(WorkflowProgress.id == existing.id)
                .values(
                    progress_percentage=progress_percentage,
                    notes=notes,
                    status="in_progress" if progress_percentage < 100 else "completed",
                )
            )
            await self.db.execute(stmt)
            return existing
        else:
            # Create new progress record
            new_progress = WorkflowProgress(
                asset_id=asset_id,
                phase=phase,
                progress_percentage=progress_percentage,
                notes=notes,
                status="in_progress" if progress_percentage < 100 else "completed",
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )
            self.db.add(new_progress)
            await self.db.flush()
            return new_progress
