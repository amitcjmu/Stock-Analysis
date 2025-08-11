"""
Field mapping suggestion route handlers.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

from ..models.mapping_schemas import FieldMappingAnalysis
from ..services.suggestion_service import SuggestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suggestions", tags=["field-mapping-suggestions"])


def get_suggestion_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> SuggestionService:
    """Dependency injection for suggestion service."""
    return SuggestionService(db, context)


@router.get("/imports/{import_id}/suggestions", response_model=FieldMappingAnalysis)
async def get_field_mapping_suggestions(
    import_id: str, service: SuggestionService = Depends(get_suggestion_service)
):
    """Get AI-powered field mapping suggestions for an import."""
    try:
        analysis = await service.get_field_mapping_suggestions(import_id)
        return analysis
    except ValueError as e:
        logger.warning(
            f"Validation error getting suggestions for import {import_id}: {e}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error getting field mapping suggestions for import {import_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate field mapping suggestions"
        )


@router.post("/imports/{import_id}/regenerate", response_model=FieldMappingAnalysis)
async def regenerate_suggestions(
    import_id: str,
    feedback: Optional[Dict[str, Any]] = None,
    service: SuggestionService = Depends(get_suggestion_service),
):
    """Regenerate suggestions with user feedback incorporated."""
    try:
        analysis = await service.regenerate_suggestions(import_id, feedback)
        return analysis
    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Error regenerating suggestions for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error regenerating suggestions for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to regenerate suggestions")


@router.get("/imports/{import_id}/confidence-metrics")
async def get_confidence_metrics(
    import_id: str, service: SuggestionService = Depends(get_suggestion_service)
):
    """Get confidence metrics for field mapping suggestions."""
    try:
        metrics = await service.get_suggestion_confidence_metrics(import_id)
        return metrics
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error getting confidence metrics for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get confidence metrics")


@router.get("/available-target-fields")
async def get_available_target_fields(
    service: SuggestionService = Depends(get_suggestion_service),
):
    """
    DEPRECATED: Get list of all available target fields for mapping.

    This endpoint is deprecated as of 2025-07-12. Frontend now uses a hardcoded
    list of asset fields to eliminate unnecessary API calls on every app start.
    The hardcoded list in FieldOptionsContext.tsx contains all asset model fields.

    This endpoint is kept for backward compatibility but should not be used.
    """
    try:
        fields = await service._get_available_target_fields()
        return {
            "fields": fields,
            "total_count": len(fields),
            "categories": list(
                set(field.get("category", "unknown") for field in fields)
            ),
            "deprecated": True,
            "message": "This endpoint is deprecated. Frontend uses hardcoded asset fields list.",
        }
    except Exception as e:
        logger.error(safe_log_format("Error getting available target fields: {e}", e=e))
        raise HTTPException(
            status_code=500, detail="Failed to get available target fields"
        )
