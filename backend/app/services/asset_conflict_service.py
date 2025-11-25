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
        # Get import_category from conflict record (if available) to determine if dependency fields should be extracted
        import_category = None
        try:
            from app.models.asset_conflict_resolution import AssetConflictResolution
            from app.models.data_import.core import DataImport

            # Fetch conflict record to get data_import_id
            conflict_record = await self.db.get(
                AssetConflictResolution, UUID(resolution.conflict_id)
            )
            if conflict_record and conflict_record.data_import_id:
                # Query DataImport to get import_category
                data_import = await self.db.get(
                    DataImport, conflict_record.data_import_id
                )
                if data_import:
                    import_category = data_import.import_category
        except Exception as e:
            logger.debug(
                f"Could not determine import_category for conflict {resolution.conflict_id}: {e}"
            )
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

            # Extract dependency fields ONLY for app-discovery imports (Issue #833)
            # Check import_category from data_import_id to determine if dependency fields should be extracted
            port = None
            protocol_name = None
            conn_count = None
            bytes_total = None
            first_seen = None
            last_seen = None

            # Only extract dependency fields for app-discovery imports
            if import_category:
                # Normalize import_category for comparison
                normalized_category = import_category.lower().replace("-", "_")
                if normalized_category in [
                    "app_discovery",
                    "app-discovery",
                    "app_dependency",
                ]:
                    # Extract dependency fields from raw record data
                    # These fields should be in new_asset_data's custom_attributes or raw_data
                    raw_data = (
                        resolution.new_asset_data.get("raw_data")
                        or resolution.new_asset_data.get("custom_attributes")
                        or {}
                    )

                    # Extract dependency fields with type conversion
                    port = raw_data.get("port")
                    if port is not None:
                        try:
                            port = int(port)
                        except (ValueError, TypeError):
                            port = None

                    protocol_name = raw_data.get("protocol_name")

                    conn_count = raw_data.get("conn_count")
                    if conn_count is not None:
                        try:
                            conn_count = int(conn_count)
                        except (ValueError, TypeError):
                            conn_count = None

                    bytes_total = raw_data.get("bytes_total")
                    if bytes_total is not None:
                        try:
                            bytes_total = int(bytes_total)
                        except (ValueError, TypeError):
                            bytes_total = None

                    first_seen = raw_data.get("first_seen")
                    last_seen = raw_data.get("last_seen")

                    logger.debug(
                        f"Extracted dependency fields for app-discovery conflict resolution: "
                        f"conn_count={conn_count}, port={port}, protocol={protocol_name}"
                    )

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
                    port=port,
                    protocol_name=protocol_name,
                    conn_count=conn_count,
                    bytes_total=bytes_total,
                    first_seen=first_seen,
                    last_seen=last_seen,
                )
                result["created_dependency_ids"].append(dep1.id)
                logger.info(
                    f"Created dependency {dep1.id}: Parent "
                    f"{resolution.dependency_selection.parent_asset_id} → "
                    f"Existing {resolution.existing_asset_id} "
                    f"(conn_count={conn_count}, port={port}, protocol={protocol_name})"
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
                port=port,
                protocol_name=protocol_name,
                conn_count=conn_count,
                bytes_total=bytes_total,
                first_seen=first_seen,
                last_seen=last_seen,
            )
            result["created_dependency_ids"].append(dep2.id)
            logger.info(
                f"Created dependency {dep2.id}: Parent "
                f"{resolution.dependency_selection.parent_asset_id} → "
                f"New {new_asset.id} "
                f"(conn_count={conn_count}, port={port}, protocol={protocol_name})"
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
