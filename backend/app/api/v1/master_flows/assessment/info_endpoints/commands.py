"""
Assessment information command endpoints.

PUT endpoints for updating assessment data (complexity metrics, etc.).
"""

import logging
from typing import Any, Dict
from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.collection_flow.asset_custom_attributes import AssetCustomAttributes
from ..uuid_utils import ensure_uuid

from . import router
from .schemas import ComplexityMetricsUpdate

logger = logging.getLogger(__name__)


@router.put("/{flow_id}/applications/{app_id}/complexity-metrics")
async def update_complexity_metrics(
    flow_id: str,
    app_id: str,
    metrics: ComplexityMetricsUpdate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Update complexity metrics for an application in assessment flow.

    Stores:
    - complexity_score (1-10) in assets.complexity_score
    - architecture_type in assets.application_type
    - customization_level in asset_custom_attributes.attributes

    CRITICAL: Per CLAUDE.md - PUT requests use request body, NOT query parameters.
    """
    try:
        if metrics.architecture_type not in [
            "Monolithic",
            "Microservices",
            "SOA",
            "Serverless",
            "Event-Driven",
            "Layered",
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid architecture_type: {metrics.architecture_type}",
            )
        if metrics.customization_level not in ["Low", "Medium", "High"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid customization_level: {metrics.customization_level}",
            )

        app_uuid, client_uuid, engagement_uuid = (
            ensure_uuid(app_id),
            ensure_uuid(context.client_account_id),
            ensure_uuid(context.engagement_id),
        )

        # Update assets table using raw SQL (complexity_score column exists in DB but not in Asset ORM model)
        await db.execute(
            text(
                """
                UPDATE migration.assets
                SET complexity_score = :complexity_score,
                    application_type = :application_type,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :asset_id
                  AND client_account_id = :client_account_id
                  AND engagement_id = :engagement_id
            """
            ),
            # fmt: off
            {"complexity_score": float(metrics.complexity_score), "application_type": metrics.architecture_type,
             "asset_id": app_uuid, "client_account_id": client_uuid, "engagement_id": engagement_uuid},
            # fmt: on
        )

        # Update or create asset_custom_attributes for customization_level
        result = await db.execute(
            select(AssetCustomAttributes).where(
                AssetCustomAttributes.asset_id == app_uuid,
                AssetCustomAttributes.client_account_id == client_uuid,
                AssetCustomAttributes.engagement_id == engagement_uuid,
            )
        )
        custom_attr = result.scalar_one_or_none()

        if custom_attr:
            (attrs := custom_attr.attributes or {}).update(
                {"customization_level": metrics.customization_level}
            )
            await db.execute(
                update(AssetCustomAttributes)
                .where(AssetCustomAttributes.id == custom_attr.id)
                .values(attributes=attrs)
            )
        else:
            new_attr = AssetCustomAttributes(
                id=uuid4(),
                client_account_id=client_uuid,
                engagement_id=engagement_uuid,
                asset_id=app_uuid,
                asset_type="application",
                attributes={"customization_level": metrics.customization_level},
                source="assessment_flow_complexity",
            )
            db.add(new_attr)

        await db.commit()
        logger.info(
            f"Updated complexity metrics for app {app_id}: score={metrics.complexity_score}, "
            f"arch={metrics.architecture_type}, custom={metrics.customization_level}"
        )

        return {
            "app_id": app_id,
            "complexity_score": metrics.complexity_score,
            "architecture_type": metrics.architecture_type,
            "customization_level": metrics.customization_level,
        }
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Failed to update complexity metrics for {app_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update complexity metrics: {str(e)}"
        )
