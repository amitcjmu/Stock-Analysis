"""
Analysis queues management endpoints.
Handles batch analysis operations for applications.
"""

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.context import get_current_context
from app.models.analysis_queue import (
    AnalysisQueue,
    AnalysisQueueItem,
    QueueStatus,
    ItemStatus,
)
from app.schemas.analysis_queue import (
    AnalysisQueueCreate,
    AddItemRequest,
    QueueExportFormat,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_analysis_queues(
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get all analysis queues for the current engagement."""
    try:
        # Get queues for current engagement
        query = (
            select(AnalysisQueue)
            .where(
                and_(
                    AnalysisQueue.client_id == context.client_account_id,
                    AnalysisQueue.engagement_id == context.engagement_id,
                )
            )
            .options(selectinload(AnalysisQueue.items))
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        queues = result.scalars().all()

        # Transform to match frontend expectations
        result = []
        for queue in queues:
            completed_items = len(
                [item for item in queue.items if item.status == ItemStatus.COMPLETED]
            )
            total_items = len(queue.items)
            progress = (completed_items / total_items * 100) if total_items > 0 else 0

            # Get current processing item
            current_app = None
            for item in queue.items:
                if item.status == ItemStatus.PROCESSING:
                    current_app = item.application_id
                    break

            # Map backend status to frontend expected status
            status_map = {
                QueueStatus.PENDING: "pending",
                QueueStatus.PROCESSING: "in_progress",
                QueueStatus.PAUSED: "paused",
                QueueStatus.COMPLETED: "completed",
                QueueStatus.CANCELLED: "failed",
                QueueStatus.FAILED: "failed",
            }

            result.append(
                {
                    "id": str(queue.id),
                    "name": queue.name,
                    "applicationIds": [item.application_id for item in queue.items],
                    "status": status_map.get(queue.status, queue.status),
                    "progress": progress,
                    "createdAt": queue.created_at.isoformat(),
                    "startedAt": (
                        queue.started_at.isoformat() if queue.started_at else None
                    ),
                    "completedAt": (
                        queue.completed_at.isoformat() if queue.completed_at else None
                    ),
                    "currentApp": current_app,
                }
            )

        return result
    except Exception as e:
        logger.error(f"Error fetching analysis queues: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis queues")


@router.post("")
async def create_analysis_queue(
    request: AnalysisQueueCreate,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Create a new analysis queue."""
    try:
        # Create queue
        queue = AnalysisQueue(
            id=uuid4(),
            name=request.name,
            client_id=context.client_account_id,
            engagement_id=context.engagement_id,
            created_by=context.user,
            status=QueueStatus.PENDING,
        )

        # Add items if provided
        for app_id in request.applicationIds:
            item = AnalysisQueueItem(
                id=uuid4(),
                queue_id=queue.id,
                application_id=app_id,
                status=ItemStatus.PENDING,
            )
            queue.items.append(item)

        db.add(queue)
        await db.commit()
        await db.refresh(queue)

        return {
            "id": str(queue.id),
            "name": queue.name,
            "applicationIds": [item.application_id for item in queue.items],
            "status": "pending",
            "progress": 0,
            "createdAt": queue.created_at.isoformat(),
            "startedAt": None,
            "completedAt": None,
            "currentApp": None,
        }
    except Exception as e:
        logger.error(f"Error creating analysis queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create analysis queue")


@router.post("/{queue_id}/items")
async def add_to_queue(
    queue_id: str,
    request: AddItemRequest,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Add an application to an analysis queue."""
    try:
        # Get queue
        query = select(AnalysisQueue).where(
            and_(
                AnalysisQueue.id == queue_id,
                AnalysisQueue.client_id == context.client_account_id,
                AnalysisQueue.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if queue.status not in [QueueStatus.PENDING, QueueStatus.PAUSED]:
            raise HTTPException(
                status_code=400, detail="Cannot add items to active or completed queue"
            )

        # Add item
        item = AnalysisQueueItem(
            id=uuid4(),
            queue_id=queue.id,
            application_id=request.applicationId,
            status=ItemStatus.PENDING,
        )

        db.add(item)
        await db.commit()

        return {"message": "Application added to queue"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add to queue")


@router.post("/{queue_id}/start")
async def start_queue(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Start processing an analysis queue."""
    try:
        # Get queue
        query = select(AnalysisQueue).where(
            and_(
                AnalysisQueue.id == queue_id,
                AnalysisQueue.client_id == context.client_account_id,
                AnalysisQueue.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if queue.status not in [QueueStatus.PENDING, QueueStatus.PAUSED]:
            raise HTTPException(status_code=400, detail="Queue cannot be started")

        # Update status
        queue.status = QueueStatus.PROCESSING
        queue.started_at = datetime.utcnow()

        await db.commit()

        # TODO: Trigger actual processing

        return {"message": "Queue processing started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start queue")


@router.post("/{queue_id}/pause")
async def pause_queue(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Pause processing of an analysis queue."""
    try:
        # Get queue
        query = select(AnalysisQueue).where(
            and_(
                AnalysisQueue.id == queue_id,
                AnalysisQueue.client_id == context.client_account_id,
                AnalysisQueue.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if queue.status != QueueStatus.PROCESSING:
            raise HTTPException(
                status_code=400, detail="Only processing queues can be paused"
            )

        # Update status
        queue.status = QueueStatus.PAUSED

        await db.commit()

        return {"message": "Queue processing paused"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to pause queue")


@router.post("/{queue_id}/cancel")
async def cancel_queue(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Cancel processing of an analysis queue."""
    try:
        # Get queue
        query = select(AnalysisQueue).where(
            and_(
                AnalysisQueue.id == queue_id,
                AnalysisQueue.client_id == context.client_account_id,
                AnalysisQueue.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if queue.status in [QueueStatus.COMPLETED, QueueStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, detail="Queue already completed or cancelled"
            )

        # Update status
        queue.status = QueueStatus.CANCELLED
        queue.completed_at = datetime.utcnow()

        # Cancel pending items
        for item in queue.items:
            if item.status == ItemStatus.PENDING:
                item.status = ItemStatus.CANCELLED

        await db.commit()

        return {"message": "Queue processing cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel queue")


@router.post("/{queue_id}/retry")
async def retry_queue(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Retry failed items in an analysis queue."""
    try:
        # Get queue with items
        query = (
            select(AnalysisQueue)
            .where(
                and_(
                    AnalysisQueue.id == queue_id,
                    AnalysisQueue.client_id == context.client_account_id,
                    AnalysisQueue.engagement_id == context.engagement_id,
                )
            )
            .options(selectinload(AnalysisQueue.items))
        )

        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        # Reset failed items
        retry_count = 0
        for item in queue.items:
            if item.status == ItemStatus.FAILED:
                item.status = ItemStatus.PENDING
                item.error_message = None
                retry_count += 1

        if retry_count > 0:
            queue.status = QueueStatus.PROCESSING
            queue.completed_at = None

        await db.commit()

        return {"message": f"Retrying {retry_count} failed items"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to retry queue")


@router.delete("/{queue_id}")
async def delete_queue(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Delete an analysis queue."""
    try:
        # Get queue
        query = select(AnalysisQueue).where(
            and_(
                AnalysisQueue.id == queue_id,
                AnalysisQueue.client_id == context.client_account_id,
                AnalysisQueue.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        if queue.status == QueueStatus.PROCESSING:
            raise HTTPException(status_code=400, detail="Cannot delete active queue")

        await db.delete(queue)
        await db.commit()

        return {"message": "Queue deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting queue: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete queue")


@router.get("/{queue_id}/export")
async def export_queue(
    queue_id: str,
    format: QueueExportFormat = Query(QueueExportFormat.CSV),
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
):
    """Export queue results in specified format."""
    try:
        # Get queue with items
        query = (
            select(AnalysisQueue)
            .where(
                and_(
                    AnalysisQueue.id == queue_id,
                    AnalysisQueue.client_id == context.client_account_id,
                    AnalysisQueue.engagement_id == context.engagement_id,
                )
            )
            .options(selectinload(AnalysisQueue.items))
        )

        result = await db.execute(query)
        queue = result.scalar_one_or_none()

        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")

        # TODO: Implement actual export logic
        # For now, return a simple response
        if format == QueueExportFormat.CSV:
            return {"message": "CSV export not yet implemented", "queue_id": queue_id}
        else:
            return {
                "queue_id": str(queue.id),
                "name": queue.name,
                "status": queue.status,
                "items": [
                    {
                        "id": str(item.id),
                        "application_id": item.application_id,
                        "status": item.status,
                        "error_message": item.error_message,
                    }
                    for item in queue.items
                ],
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting queue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export queue")
