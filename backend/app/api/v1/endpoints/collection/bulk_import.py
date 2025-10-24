"""
Collection Bulk Import Endpoints

Provides endpoints for CSV/JSON bulk import with intelligent field mapping.
Part of Collection Flow Adaptive Questionnaire Enhancements.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context_dependency
from app.repositories.context_aware_repository import ContextAwareRepository
from app.models.collection_flow import CollectionBackgroundTasks
from app.schemas.collection import (
    FieldMappingSuggestion,
    ImportAnalysisResponse,
    ImportExecutionRequest,
    ImportTaskDetailResponse,
    ImportTaskResponse,
)
from app.services.collection.unified_import_orchestrator import (
    UnifiedImportOrchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bulk-import/analyze", response_model=ImportAnalysisResponse)
async def analyze_import_file(
    file: UploadFile = File(...),
    import_type: str = Form(...),  # "application", "server", "database"
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze CSV/JSON file and suggest field mappings.

    Returns intelligent field mapping suggestions based on column names
    and data content using fuzzy matching and LLM analysis.
    """
    try:
        service = UnifiedImportOrchestrator(db=db, context=context)

        analysis = await service.analyze_import_file(file=file, import_type=import_type)

        # Convert to Pydantic response
        return ImportAnalysisResponse(
            file_name=analysis.file_name,
            total_rows=analysis.total_rows,
            detected_columns=analysis.detected_columns,
            suggested_mappings=[
                FieldMappingSuggestion(
                    csv_column=m.csv_column,
                    suggested_field=m.suggested_field,
                    confidence=m.confidence,
                    suggestions=m.suggestions,
                )
                for m in analysis.suggested_mappings
            ],
            unmapped_columns=analysis.unmapped_columns,
            validation_warnings=analysis.validation_warnings,
            import_batch_id=analysis.import_batch_id,
        )

    except ValueError as e:
        logger.error(f"❌ Import file validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Import file analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-import/execute", response_model=ImportTaskResponse)
async def execute_import(
    request: ImportExecutionRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute bulk import with confirmed field mappings.

    Creates a background task for processing the import asynchronously.
    Use the returned task ID to poll for status updates.

    NOTE: In production, this would dispatch to a background worker queue.
    For now, it creates the task record for future processing.
    """
    try:
        service = UnifiedImportOrchestrator(db=db, context=context)

        # For now, we create the task but don't actually process the data
        # In production, file_data would be loaded from the import_batch_id
        file_data = []  # Placeholder - would load from stored batch

        task = await service.execute_import(
            child_flow_id=request.child_flow_id,
            import_batch_id=request.import_batch_id,
            file_data=file_data,
            confirmed_mappings=request.confirmed_mappings,
            import_type=request.import_type,
            overwrite_existing=request.overwrite_existing,
            gap_recalculation_mode=request.gap_recalculation_mode,
        )

        return ImportTaskResponse(
            id=task.id,
            status=task.status,
            progress_percent=task.progress_percent,
            current_stage=task.current_stage,
        )

    except Exception as e:
        logger.error(f"❌ Import execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bulk-import/status/{task_id}", response_model=ImportTaskDetailResponse)
async def get_import_status(
    task_id: UUID,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get import task status for polling.

    Returns detailed task information including progress, errors, and results.
    """
    try:
        task_repo = ContextAwareRepository(db, CollectionBackgroundTasks, context)

        task = await task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Import task not found")

        return ImportTaskDetailResponse(
            id=task.id,
            status=task.status,
            progress_percent=task.progress_percent,
            current_stage=task.current_stage,
            rows_processed=task.rows_processed,
            total_rows=task.total_rows,
            error_message=task.error_message,
            result_data=task.result_data,
            created_at=task.created_at.isoformat() if task.created_at else None,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get import status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
