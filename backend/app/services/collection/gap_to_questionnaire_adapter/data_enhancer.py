"""
Data Enhancer for Questionnaire Pre-fill

Enriches questionnaire data with existing field values.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class DataEnhancer:
    """Enhances questionnaire data with existing values for pre-fill."""

    async def enhance(
        self,
        data_gaps: Dict[str, Any],
        asset_id: UUID,
        db: AsyncSession,
        context: RequestContext,
    ) -> Dict[str, Any]:
        """
        Enhance data_gaps with existing field values for pre-fill.

        This allows the questionnaire to show existing values for verification
        rather than asking for completely new input.

        Args:
            data_gaps: Base data_gaps dict
            asset_id: Asset UUID
            db: Database session
            context: Request context

        Returns:
            Enhanced data_gaps dict with existing_field_values
        """
        # Query asset and application enrichment data
        from sqlalchemy import select

        from app.models.asset import Asset

        result = await db.execute(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            logger.warning(f"Asset {asset_id} not found for data enhancement")
            return data_gaps

        # Build existing field values map
        existing_values = {}
        if asset.operating_system:
            existing_values["operating_system"] = asset.operating_system
        if asset.ip_address:
            existing_values["ip_address"] = asset.ip_address

        # ✅ FIX Bug #11 (DataEnhancer enrichment_data AttributeError):
        # Asset model has technical_details JSONB (NOT enrichment_data)
        # technical_details is a dict, NOT an object with attributes
        if hasattr(asset, "technical_details") and asset.technical_details:
            enrichment = asset.technical_details
            # Access as dict keys, not object attributes
            if isinstance(enrichment, dict):
                if enrichment.get("database_version"):
                    existing_values["database_version"] = enrichment["database_version"]
                if enrichment.get("backup_frequency"):
                    existing_values["backup_frequency"] = enrichment["backup_frequency"]

        # Add to data_gaps
        if existing_values:
            data_gaps["existing_field_values"] = {str(asset_id): existing_values}
            logger.debug(
                f"Enhanced data_gaps with {len(existing_values)} existing field values"
            )

        return data_gaps


__all__ = ["DataEnhancer"]
