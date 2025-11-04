"""
Service for resolving asset conflicts during data import.

Per Issue #910: Supports four resolution actions:
- keep_existing: Keep existing asset, discard new
- replace_with_new: Replace existing with new data
- merge: Field-by-field selection
- create_both_with_dependency: Create both assets and link to parent (NEW)
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.repositories.asset_repository import AssetRepository
from app.repositories.dependency_repository import DependencyRepository
from app.schemas.asset_conflict import (
    AssetConflictResolutionRequest,
    BulkConflictResolutionRequest,
    ConflictResolutionResponse,
)

logger = logging.getLogger(__name__)


class AssetConflictService:
    """Service for handling asset conflict resolution."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
    ):
        """Initialize service with database session and multi-tenant context."""
        self.db = db
        self.client_account_id = str(client_account_id)
        self.engagement_id = str(engagement_id)
        self.asset_repository = AssetRepository(
            db, self.client_account_id, self.engagement_id
        )
        self.dependency_repository = DependencyRepository(
            db, self.client_account_id, self.engagement_id
        )

    async def resolve_conflicts(
        self, request: BulkConflictResolutionRequest
    ) -> ConflictResolutionResponse:
        """
        Resolve multiple asset conflicts in a single atomic transaction.

        Args:
            request: Bulk resolution request with list of resolutions

        Returns:
            ConflictResolutionResponse with counts and created entity IDs
        """
        created_assets: List[UUID] = []
        created_dependencies: List[UUID] = []
        errors: List[str] = []

        # Process each resolution
        for resolution in request.resolutions:
            try:
                result = await self._resolve_single_conflict(resolution)
                if result.get("created_asset_id"):
                    created_assets.append(result["created_asset_id"])
                if result.get("created_dependency_ids"):
                    created_dependencies.extend(result["created_dependency_ids"])
            except Exception as e:
                error_msg = f"Conflict {resolution.conflict_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        # Commit transaction if no errors, otherwise rollback
        if errors:
            await self.db.rollback()
            # CC FIX (Qodo Security): Clear lists after rollback to reflect actual DB state
            created_assets.clear()
            created_dependencies.clear()
            resolved_count = 0
        else:
            await self.db.commit()
            resolved_count = len(request.resolutions)

        return ConflictResolutionResponse(
            resolved_count=resolved_count,
            total_requested=len(request.resolutions),
            created_assets=created_assets,
            created_dependencies=created_dependencies,
            errors=errors,
        )

    async def _resolve_single_conflict(
        self, resolution: AssetConflictResolutionRequest
    ) -> Dict[str, Any]:
        """
        Resolve a single asset conflict based on the chosen action.

        Args:
            resolution: Single conflict resolution request

        Returns:
            Dictionary with created_asset_id and created_dependency_ids

        Raises:
            ValidationError: If resolution action validation fails
        """
        result: Dict[str, Any] = {
            "created_asset_id": None,
            "created_dependency_ids": [],
        }

        if resolution.resolution_action == "keep_existing":
            # No changes needed - existing asset remains unchanged
            logger.info(f"Keeping existing asset for conflict {resolution.conflict_id}")
            return result

        elif resolution.resolution_action == "replace_with_new":
            # Update existing asset with all new data
            if not resolution.existing_asset_id or not resolution.new_asset_data:
                raise ValidationError(
                    "Missing existing_asset_id or new_asset_data for replace action"
                )

            _ = await self.asset_repository.update(
                resolution.existing_asset_id, **resolution.new_asset_data
            )
            logger.info(
                f"Replaced existing asset {resolution.existing_asset_id} with new data"
            )
            return result

        elif resolution.resolution_action == "merge":
            # Update specific fields based on merge selections
            if (
                not resolution.existing_asset_id
                or not resolution.merge_field_selections
            ):
                raise ValidationError(
                    "Missing existing_asset_id or merge_field_selections for merge action"
                )

            merged_data = self._build_merged_data(
                resolution.existing_asset_data or {},
                resolution.new_asset_data or {},
                resolution.merge_field_selections,
            )
            await self.asset_repository.update(
                resolution.existing_asset_id, **merged_data
            )
            logger.info(
                f"Merged asset {resolution.existing_asset_id} with selected fields"
            )
            return result

        elif resolution.resolution_action == "create_both_with_dependency":
            # Create new asset and link both to parent
            if not resolution.dependency_selection:
                raise ValidationError(
                    "dependency_selection required for create_both_with_dependency action"
                )

            if not resolution.new_asset_data:
                raise ValidationError(
                    "new_asset_data required for create_both_with_dependency action"
                )

            # Create new asset from import data
            new_asset = await self.asset_repository.create(**resolution.new_asset_data)
            result["created_asset_id"] = new_asset.id
            logger.info(f"Created new asset {new_asset.id} from conflict resolution")

            # Create dependency: Parent → Existing Asset
            if resolution.existing_asset_id:
                dep1 = await self.dependency_repository.create_dependency(
                    source_asset_id=str(
                        resolution.dependency_selection.parent_asset_id
                    ),
                    target_asset_id=str(resolution.existing_asset_id),
                    dependency_type=resolution.dependency_selection.dependency_type,
                    confidence_score=resolution.dependency_selection.confidence_score,
                    description=(
                        f"Manual dependency created via conflict resolution: "
                        f"{resolution.dependency_selection.parent_asset_name} → Existing Asset"
                    ),
                )
                result["created_dependency_ids"].append(dep1.id)
                logger.info(
                    f"Created dependency {dep1.id}: Parent "
                    f"{resolution.dependency_selection.parent_asset_id} → "
                    f"Existing {resolution.existing_asset_id}"
                )

            # Create dependency: Parent → New Asset
            dep2 = await self.dependency_repository.create_dependency(
                source_asset_id=str(resolution.dependency_selection.parent_asset_id),
                target_asset_id=str(new_asset.id),
                dependency_type=resolution.dependency_selection.dependency_type,
                confidence_score=resolution.dependency_selection.confidence_score,
                description=(
                    f"Manual dependency created via conflict resolution: "
                    f"{resolution.dependency_selection.parent_asset_name} → New Asset"
                ),
            )
            result["created_dependency_ids"].append(dep2.id)
            logger.info(
                f"Created dependency {dep2.id}: Parent "
                f"{resolution.dependency_selection.parent_asset_id} → "
                f"New {new_asset.id}"
            )

            return result

        else:
            raise ValidationError(
                f"Unknown resolution action: {resolution.resolution_action}"
            )

    def _build_merged_data(
        self,
        existing_data: Dict[str, Any],
        new_data: Dict[str, Any],
        field_selections: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Build merged asset data based on field-level selections.

        Args:
            existing_data: Data from existing asset
            new_data: Data from new asset
            field_selections: Map of field_name -> 'existing' | 'new'

        Returns:
            Dictionary with merged field values
        """
        merged = {}

        for field_name, source in field_selections.items():
            if source == "existing" and field_name in existing_data:
                merged[field_name] = existing_data[field_name]
            elif source == "new" and field_name in new_data:
                merged[field_name] = new_data[field_name]
            else:
                logger.warning(
                    f"Field {field_name} not found in {source} data, skipping"
                )

        return merged
