"""
Bulk operations utility for field mapping.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import ImportFieldMapping
from ..models.mapping_schemas import FieldMappingUpdate

logger = logging.getLogger(__name__)


class BulkOperations:
    """Utility for bulk field mapping operations."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize bulk operations utility."""
        self.db = db
        self.context = context

    async def bulk_update_field_mappings(
        self, mapping_ids: List[str], update_data: FieldMappingUpdate
    ) -> Dict[str, Any]:
        """Update multiple field mappings in a single database transaction."""

        # Convert string UUIDs to UUID objects
        try:
            mapping_uuids = [
                UUID(id_str) if isinstance(id_str, str) else id_str
                for id_str in mapping_ids
            ]

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format in bulk update: {e}")
            raise ValueError(f"Invalid UUID format in mapping_ids: {e}")

        # Get all mappings to update
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id.in_(mapping_uuids),
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()

        if not mappings:
            raise ValueError("No field mappings found for the provided IDs")

        # Update all mappings in a single transaction
        updated_mappings = []
        failed_updates = []

        try:
            for mapping in mappings:
                try:
                    # Update fields
                    if update_data.target_field is not None:
                        mapping.target_field = update_data.target_field
                    if update_data.transformation_rule is not None:
                        mapping.transformation_rules = update_data.transformation_rule
                    if update_data.validation_rule is not None:
                        mapping.transformation_rules = update_data.validation_rule
                    if update_data.is_approved is not None:
                        mapping.status = (
                            "approved" if update_data.is_approved else "suggested"
                        )

                    mapping.updated_at = datetime.utcnow()
                    updated_mappings.append(mapping.id)

                except Exception as e:
                    logger.error(f"Error updating mapping {mapping.id}: {e}")
                    failed_updates.append({"mapping_id": mapping.id, "error": str(e)})

            # Commit all changes at once
            await self.db.commit()

            logger.info(f"Bulk updated {len(updated_mappings)} field mappings")

            return {
                "status": "success",
                "total_mappings": len(mapping_ids),
                "updated_mappings": len(updated_mappings),
                "failed_updates": len(failed_updates),
                "updated_ids": updated_mappings,
                "failures": failed_updates,
            }

        except Exception as e:
            # Rollback on any error
            await self.db.rollback()
            logger.error(f"Bulk update failed: {e}")
            raise ValueError(f"Bulk update failed: {str(e)}")
