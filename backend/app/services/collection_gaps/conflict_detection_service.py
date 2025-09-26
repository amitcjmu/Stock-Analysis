"""
ConflictDetectionService for Asset-Agnostic Collection.

This service aggregates data from multiple sources and detects field-level conflicts
to enable asset-agnostic collection without application-specific configuration.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.models.data_import.core import RawImportRecord
from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class ConflictDetectionService:
    """
    Detects and manages field-level conflicts across multiple data sources.

    This service aggregates data from:
    - Asset.custom_attributes (JSON field)
    - Asset.technical_details (JSON field)
    - RawImportRecord.raw_data (JSON field from imports)

    When the same field has different values across sources, it creates
    an AssetFieldConflict record for manual resolution.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the conflict detection service."""
        self.db = db
        self.context = context
        # Use LoggerAdapter to attach contextual information
        self.logger = logging.LoggerAdapter(
            logger,
            {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
            },
        )

        # Convert context IDs to UUID for database queries
        self._client_account_uuid = (
            UUID(context.client_account_id) if context.client_account_id else None
        )
        self._engagement_uuid = (
            UUID(context.engagement_id) if context.engagement_id else None
        )

    async def detect_conflicts(self, asset_id: UUID) -> List[AssetFieldConflict]:
        """
        Aggregate data from multiple sources and detect conflicts for a specific asset.

        Args:
            asset_id: UUID of the asset to analyze

        Returns:
            List of newly created or updated AssetFieldConflict objects
        """
        self.logger.info(f"Starting conflict detection for asset {asset_id}")

        # Get asset with tenant scoping
        asset_result = await self.db.execute(
            select(Asset)
            .where(Asset.id == asset_id)
            .where(Asset.client_account_id == self._client_account_uuid)
            .where(Asset.engagement_id == self._engagement_uuid)
        )
        asset = asset_result.scalar_one_or_none()

        if not asset:
            self.logger.warning(f"Asset {asset_id} not found or not accessible")
            return []

        # Aggregate field data from all sources
        field_sources = await self._aggregate_field_data(asset)

        # Detect conflicts (fields with multiple different values)
        conflicts = []
        for field_name, sources in field_sources.items():
            if self._has_conflict(sources):
                conflict = await self._create_or_update_conflict(
                    asset_id, field_name, sources
                )
                if conflict:
                    conflicts.append(conflict)

        self.logger.info(f"Detected {len(conflicts)} conflicts for asset {asset_id}")
        return conflicts

    async def detect_conflicts_for_scope(
        self, scope: str, scope_id: str, asset_type: Optional[str] = None
    ) -> Dict[str, List[AssetFieldConflict]]:
        """
        Detect conflicts for all assets within a given scope.

        Args:
            scope: 'tenant', 'engagement', or 'asset'
            scope_id: ID of the scope entity
            asset_type: Optional filter by asset type

        Returns:
            Dictionary mapping asset_id to list of conflicts
        """
        self.logger.info(f"Starting conflict detection for scope {scope}:{scope_id}")

        # Build query based on scope
        query = select(Asset).where(
            Asset.client_account_id == self._client_account_uuid,
            Asset.engagement_id == self._engagement_uuid,
        )

        if scope == "asset":
            query = query.where(Asset.id == UUID(scope_id))
        elif scope == "engagement":
            # Already filtered by engagement_id above
            pass
        elif scope == "tenant":
            # Already filtered by client_account_id above
            pass
        else:
            raise ValueError(f"Invalid scope: {scope}")

        if asset_type:
            query = query.where(Asset.asset_type == asset_type)

        # Get all assets in scope
        assets_result = await self.db.execute(query)
        assets = assets_result.scalars().all()

        # Detect conflicts for each asset
        all_conflicts = {}
        for asset in assets:
            asset_conflicts = await self.detect_conflicts(asset.id)
            if asset_conflicts:
                all_conflicts[str(asset.id)] = asset_conflicts

        self.logger.info(
            f"Detected conflicts for {len(all_conflicts)} assets in scope {scope}:{scope_id}"
        )
        return all_conflicts

    async def _aggregate_field_data(
        self, asset: Asset
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate field data from all sources for an asset.

        Returns:
            Dictionary mapping field_name to list of source data
        """
        field_sources = {}

        # Source 1: custom_attributes JSON field
        if asset.custom_attributes:
            for field, value in asset.custom_attributes.items():
                # Skip empty values, None, and whitespace-only strings
                if value is not None and str(value).strip():
                    field_sources.setdefault(field, []).append(
                        {
                            "value": str(value),
                            "source": "custom_attributes",
                            "timestamp": asset.updated_at or asset.created_at,
                            "confidence": 0.7,  # Medium confidence for custom attributes
                        }
                    )

        # Source 2: technical_details JSON field
        if asset.technical_details:
            for field, value in asset.technical_details.items():
                # Skip empty values, None, and whitespace-only strings
                if value is not None and str(value).strip():
                    field_sources.setdefault(field, []).append(
                        {
                            "value": str(value),
                            "source": "technical_details",
                            "timestamp": asset.updated_at or asset.created_at,
                            "confidence": 0.8,  # Higher confidence for technical details
                        }
                    )

        # Source 3: raw_import_records
        import_records_result = await self.db.execute(
            select(RawImportRecord)
            .where(RawImportRecord.asset_id == asset.id)
            .where(RawImportRecord.client_account_id == self._client_account_uuid)
            .where(RawImportRecord.engagement_id == self._engagement_uuid)
        )
        import_records = import_records_result.scalars().all()

        for record in import_records:
            if record.raw_data:
                # Extract source file from raw_data if available
                source_file = record.raw_data.get("_source_file", "unknown")

                for field, value in record.raw_data.items():
                    # Skip internal metadata fields and empty/whitespace values
                    if field.startswith("_") or value is None or not str(value).strip():
                        continue

                    field_sources.setdefault(field, []).append(
                        {
                            "value": str(value),
                            "source": f"import:{source_file}",
                            "timestamp": record.created_at,
                            "confidence": 0.9,  # High confidence for imported data
                        }
                    )

        return field_sources

    def _has_conflict(self, sources: List[Dict[str, Any]]) -> bool:
        """
        Check if the sources contain conflicting values.

        Args:
            sources: List of source data dictionaries

        Returns:
            True if there are conflicting values, False otherwise
        """
        if len(sources) <= 1:
            return False

        # Get unique values (case-insensitive comparison)
        unique_values = set()
        for source in sources:
            value = str(source.get("value", "")).strip().lower()
            if value:  # Only consider non-empty values
                unique_values.add(value)

        # Conflict exists if there are multiple unique values
        return len(unique_values) > 1

    async def _create_or_update_conflict(
        self, asset_id: UUID, field_name: str, sources: List[Dict[str, Any]]
    ) -> Optional[AssetFieldConflict]:
        """
        Create a new conflict or update an existing one.

        Args:
            asset_id: Asset UUID
            field_name: Name of the conflicting field
            sources: List of conflicting source data

        Returns:
            AssetFieldConflict object or None if no conflict needed
        """
        # Check if conflict already exists
        existing_result = await self.db.execute(
            select(AssetFieldConflict)
            .where(AssetFieldConflict.asset_id == asset_id)
            .where(AssetFieldConflict.field_name == field_name)
            .where(AssetFieldConflict.client_account_id == self._client_account_uuid)
            .where(AssetFieldConflict.engagement_id == self._engagement_uuid)
        )
        existing_conflict = existing_result.scalar_one_or_none()

        # Prepare conflicting values with proper timestamps
        conflicting_values = []
        for source in sources:
            timestamp = source.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp_iso = timestamp.isoformat()
            else:
                timestamp_iso = (
                    str(timestamp) if timestamp else datetime.utcnow().isoformat()
                )

            conflicting_values.append(
                {
                    "value": source.get("value"),
                    "source": source.get("source"),
                    "timestamp": timestamp_iso,
                    "confidence": source.get("confidence", 0.5),
                }
            )

        if existing_conflict:
            # Update existing conflict if not already resolved
            if not existing_conflict.is_resolved:
                existing_conflict.conflicting_values = conflicting_values
                existing_conflict.updated_at = datetime.utcnow()
                await self.db.commit()
                self.logger.info(f"Updated existing conflict for {field_name}")
                return existing_conflict
            else:
                self.logger.info(
                    f"Conflict for {field_name} already resolved, skipping"
                )
                return None
        else:
            # Create new conflict
            new_conflict = AssetFieldConflict(
                asset_id=asset_id,
                client_account_id=self._client_account_uuid,
                engagement_id=self._engagement_uuid,
                field_name=field_name,
                conflicting_values=conflicting_values,
                resolution_status="pending",
            )

            self.db.add(new_conflict)
            await self.db.commit()
            await self.db.refresh(new_conflict)

            self.logger.info(f"Created new conflict for {field_name}")
            return new_conflict

    async def get_conflicts_for_asset(self, asset_id: UUID) -> List[AssetFieldConflict]:
        """
        Get all conflicts for a specific asset.

        Args:
            asset_id: Asset UUID

        Returns:
            List of AssetFieldConflict objects
        """
        result = await self.db.execute(
            select(AssetFieldConflict)
            .where(AssetFieldConflict.asset_id == asset_id)
            .where(AssetFieldConflict.client_account_id == self._client_account_uuid)
            .where(AssetFieldConflict.engagement_id == self._engagement_uuid)
            .order_by(AssetFieldConflict.created_at.desc())
        )
        return result.scalars().all()

    async def resolve_conflict(
        self,
        conflict_id: UUID,
        resolved_value: str,
        rationale: Optional[str] = None,
        auto_resolved: bool = False,
    ) -> AssetFieldConflict:
        """
        Resolve a specific conflict.

        Args:
            conflict_id: UUID of the conflict to resolve
            resolved_value: The chosen value for resolution
            rationale: Optional explanation of the resolution
            auto_resolved: Whether this was resolved automatically

        Returns:
            Updated AssetFieldConflict object

        Raises:
            ValueError: If conflict not found or already resolved
        """
        # Get conflict with tenant scoping
        result = await self.db.execute(
            select(AssetFieldConflict)
            .where(AssetFieldConflict.id == conflict_id)
            .where(AssetFieldConflict.client_account_id == self._client_account_uuid)
            .where(AssetFieldConflict.engagement_id == self._engagement_uuid)
        )
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found or not accessible")

        if conflict.is_resolved:
            raise ValueError(f"Conflict {conflict_id} is already resolved")

        # Resolve the conflict
        conflict.resolve_conflict(
            resolved_value=resolved_value,
            resolved_by=UUID(self.context.user_id),
            rationale=rationale,
            auto_resolved=auto_resolved,
        )

        await self.db.commit()
        await self.db.refresh(conflict)

        self.logger.info(
            f"Resolved conflict {conflict_id} with value '{resolved_value}'"
        )
        return conflict
