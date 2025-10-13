"""
Asset Resolution Service for Assessment Flow
Handles asset→application mapping during ASSET_APPLICATION_RESOLUTION phase

CC: Service follows enterprise 7-layer architecture with tenant scoping
Per docs/planning/dependency-to-assessment/README.md Step 1
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AssetResolutionService:
    """Service for resolving asset→application mappings in assessment flows

    Responsibilities:
    - Query unresolved assets (assets without mappings)
    - Retrieve existing mappings for an assessment flow
    - Create/update asset→application mappings with tenant scoping
    - Validate resolution completion for phase progression
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        """Initialize service with database session and tenant context

        Args:
            db: Async database session
            client_account_id: Client account UUID for multi-tenant isolation
            engagement_id: Engagement UUID for data scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger.bind(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

    async def get_unresolved_assets(
        self, assessment_flow_id: UUID, selected_asset_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """Get assets that do not have application mappings yet

        Args:
            assessment_flow_id: Assessment flow UUID
            selected_asset_ids: List of asset UUIDs from collection phase

        Returns:
            List of unresolved asset dictionaries with id, name, asset_type
        """
        try:
            if not selected_asset_ids:
                return []

            # CC: Performance optimization per Qodo #7 - single LEFT JOIN query
            # Eliminates N+1 query pattern by combining mapping check and asset fetch
            query = """
                SELECT a.id, a.name, a.asset_type
                FROM unnest(CAST(:selected_ids AS uuid[])) AS selected(id)
                LEFT JOIN migration.asset_application_mappings m
                    ON selected.id = m.asset_id
                    AND m.assessment_flow_id = :flow_id
                    AND m.client_account_id = :client_account_id
                    AND m.engagement_id = :engagement_id
                LEFT JOIN migration.assets a
                    ON selected.id = a.id
                    AND a.client_account_id = :client_account_id
                    AND a.engagement_id = :engagement_id
                WHERE m.id IS NULL
                ORDER BY a.name
            """

            result = await self.db.execute(
                sa.text(query).bindparams(
                    selected_ids=[str(aid) for aid in selected_asset_ids],
                    flow_id=assessment_flow_id,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                )
            )

            unresolved = [
                {
                    "asset_id": str(row.id),
                    "name": row.name,
                    "asset_type": row.asset_type,
                }
                for row in result.fetchall()
                if row.id is not None  # Filter out nulls from LEFT JOIN
            ]

            self.logger.info(
                f"Found {len(unresolved)} unresolved assets for flow {assessment_flow_id}"
            )
            return unresolved

        except Exception as e:
            self.logger.error(
                f"Error getting unresolved assets for flow {assessment_flow_id}: {e}"
            )
            raise

    async def get_existing_mappings(
        self, assessment_flow_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get existing asset→application mappings for an assessment flow

        Args:
            assessment_flow_id: Assessment flow UUID

        Returns:
            List of mapping dictionaries with asset_id, application_id, method, confidence
        """
        try:
            # Query mappings with tenant scoping
            query = """
                SELECT
                    asset_id,
                    application_id,
                    mapping_method,
                    mapping_confidence,
                    created_at
                FROM migration.asset_application_mappings
                WHERE assessment_flow_id = :flow_id
                  AND client_account_id = :client_account_id
                  AND engagement_id = :engagement_id
                ORDER BY created_at ASC
            """

            result = await self.db.execute(
                sa.text(query).bindparams(
                    flow_id=assessment_flow_id,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                )
            )

            mappings = [
                {
                    "asset_id": str(row.asset_id),
                    "application_id": str(row.application_id),
                    "mapping_method": row.mapping_method,
                    "mapping_confidence": float(row.mapping_confidence),
                    "created_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                }
                for row in result.fetchall()
            ]

            self.logger.info(
                f"Retrieved {len(mappings)} existing mappings for flow {assessment_flow_id}"
            )
            return mappings

        except Exception as e:
            self.logger.error(
                f"Error getting existing mappings for flow {assessment_flow_id}: {e}"
            )
            raise

    async def create_mapping(
        self,
        assessment_flow_id: UUID,
        asset_id: UUID,
        application_id: UUID,
        mapping_method: str = "user_manual",
        mapping_confidence: float = 1.0,
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Create or update an asset→application mapping

        Args:
            assessment_flow_id: Assessment flow UUID
            asset_id: Asset UUID to map
            application_id: Target application UUID
            mapping_method: Method used (user_manual, agent_suggested, deduplication_auto)
            mapping_confidence: Confidence score (0.0-1.0)
            created_by: UUID of user creating the mapping

        Returns:
            Success status dictionary
        """
        try:
            # Validate confidence range
            if not 0.0 <= mapping_confidence <= 1.0:
                raise ValueError("mapping_confidence must be between 0.0 and 1.0")

            # Validate mapping method
            valid_methods = ["user_manual", "agent_suggested", "deduplication_auto"]
            if mapping_method not in valid_methods:
                raise ValueError(f"mapping_method must be one of {valid_methods}")

            # Upsert mapping with tenant scoping
            # CC: Security fix per Qodo #3 - enforce tenant isolation in UPDATE clause
            # Prevents cross-tenant data updates via ON CONFLICT
            query = """
                INSERT INTO migration.asset_application_mappings (
                    assessment_flow_id,
                    asset_id,
                    application_id,
                    mapping_confidence,
                    mapping_method,
                    client_account_id,
                    engagement_id,
                    created_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    :flow_id,
                    :asset_id,
                    :application_id,
                    :confidence,
                    :method,
                    :client_account_id,
                    :engagement_id,
                    :created_by,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (assessment_flow_id, asset_id)
                DO UPDATE SET
                    application_id = EXCLUDED.application_id,
                    mapping_confidence = EXCLUDED.mapping_confidence,
                    mapping_method = EXCLUDED.mapping_method,
                    updated_at = NOW()
                WHERE
                    migration.asset_application_mappings.client_account_id = :client_account_id
                    AND migration.asset_application_mappings.engagement_id = :engagement_id
                RETURNING id
            """

            result = await self.db.execute(
                sa.text(query).bindparams(
                    flow_id=assessment_flow_id,
                    asset_id=asset_id,
                    application_id=application_id,
                    confidence=mapping_confidence,
                    method=mapping_method,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    created_by=created_by,
                )
            )

            await self.db.commit()

            mapping_id = result.scalar_one()

            self.logger.info(
                f"Created/updated mapping {mapping_id}: asset {asset_id} → application {application_id}"
            )

            return {
                "status": "success",
                "mapping_id": str(mapping_id),
                "asset_id": str(asset_id),
                "application_id": str(application_id),
            }

        except Exception as e:
            await self.db.rollback()
            self.logger.error(
                f"Error creating mapping for asset {asset_id} → application {application_id}: {e}"
            )
            raise

    async def validate_resolution_complete(
        self, assessment_flow_id: UUID, selected_asset_ids: List[UUID]
    ) -> tuple[bool, List[str]]:
        """Validate if all assets have been mapped to applications

        Args:
            assessment_flow_id: Assessment flow UUID
            selected_asset_ids: List of asset UUIDs from collection phase

        Returns:
            Tuple of (is_complete, list_of_unmapped_asset_ids)
        """
        try:
            # Get existing mappings
            existing_mappings = await self.get_existing_mappings(assessment_flow_id)
            mapped_asset_ids = {UUID(m["asset_id"]) for m in existing_mappings}

            # Find unmapped assets
            unmapped_ids = [
                str(aid) for aid in selected_asset_ids if aid not in mapped_asset_ids
            ]

            is_complete = len(unmapped_ids) == 0

            if is_complete:
                self.logger.info(
                    f"Asset resolution complete for flow {assessment_flow_id}: "
                    f"all {len(selected_asset_ids)} assets mapped"
                )
            else:
                self.logger.warning(
                    f"Asset resolution incomplete for flow {assessment_flow_id}: "
                    f"{len(unmapped_ids)} of {len(selected_asset_ids)} assets unmapped"
                )

            return is_complete, unmapped_ids

        except Exception as e:
            self.logger.error(
                f"Error validating resolution completion for flow {assessment_flow_id}: {e}"
            )
            raise
