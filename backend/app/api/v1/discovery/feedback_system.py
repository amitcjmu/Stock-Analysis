"""
Feedback System Endpoints.
Handles user feedback collection and management using database storage.
Updated for Vercel serverless compatibility (no file system writes).
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select

from app.api.v1.discovery.models import PageFeedbackRequest
from app.core.database import get_db
from app.models.feedback import Feedback, FeedbackSummary

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock data for development/testing when no real feedback exists
MOCK_CLIENT_ACCOUNT_ID = "550e8400-e29b-41d4-a716-446655440000"
MOCK_ENGAGEMENT_ID = "550e8400-e29b-41d4-a716-446655440001"

# Fallback storage for when database is unavailable
FALLBACK_FEEDBACK_STORE = []

@router.post("/feedback")
async def submit_page_feedback(request: PageFeedbackRequest):
    """
    Submit general page feedback with automatic fallback.
    """
    # Try database storage first
    try:
        from app.core.database import get_db, AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            # Create feedback entry in database
            feedback_entry = Feedback(
                id=uuid.uuid4(),
                feedback_type="page_feedback",
                page=request.page,
                rating=request.rating,
                comment=request.comment,
                category=request.category,
                breadcrumb=request.breadcrumb,
                user_timestamp=request.timestamp,
                status="new"
            )
            
            db.add(feedback_entry)
            await db.commit()
            await db.refresh(feedback_entry)
            
            logger.info(f"Page feedback stored in database for {request.page}: {request.rating}/5")
            
            return {
                "status": "success",
                "message": "Feedback submitted successfully",
                "feedback_id": str(feedback_entry.id),
                "storage_method": "database"
            }
    
    except Exception as db_error:
        logger.warning(f"Database storage failed: {db_error}. Trying fallback...")
        
        # Fall back to in-memory storage
        try:
            from datetime import datetime
            
            feedback_entry = {
                "id": str(uuid.uuid4()),
                "feedback_type": "page_feedback",
                "page": request.page,
                "rating": request.rating,
                "comment": request.comment,
                "category": request.category,
                "breadcrumb": request.breadcrumb,
                "user_timestamp": request.timestamp,
                "created_at": datetime.utcnow().isoformat(),
                "status": "new",
                "storage_method": "fallback_memory"
            }
            
            # Store in global fallback store
            global FALLBACK_FEEDBACK_STORE
            if 'FALLBACK_FEEDBACK_STORE' not in globals():
                FALLBACK_FEEDBACK_STORE = []
            
            FALLBACK_FEEDBACK_STORE.append(feedback_entry)
            
            logger.info(f"Page feedback stored in fallback for {request.page}: {request.rating}/5")
            
            return {
                "status": "success",
                "message": "Feedback submitted successfully (fallback mode)",
                "feedback_id": feedback_entry["id"],
                "storage_method": "fallback_memory",
                "warning": "Database unavailable - using temporary storage"
            }
            
        except Exception as fallback_error:
            logger.error(f"Both database and fallback failed: {fallback_error}")
            raise HTTPException(status_code=500, detail="Failed to submit feedback - all storage methods failed")

@router.get("/feedback")
async def get_feedback(
    feedback_type: Optional[str] = None,
    page: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get feedback from database with optional filtering.
    """
    try:
        # Build query using select for async compatibility
        query = select(Feedback)
        
        # Apply filters
        if feedback_type:
            query = query.where(Feedback.feedback_type == feedback_type)
        if page:
            query = query.where(Feedback.page == page)
        if status:
            query = query.where(Feedback.status == status)
        
        # Order by most recent first
        query = query.order_by(desc(Feedback.created_at))
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        result = await db.execute(query)
        feedback_items = result.scalars().all()
        
        # Convert to dict format for API response
        feedback_list = []
        for item in feedback_items:
            feedback_dict = {
                "id": str(item.id),
                "feedback_type": item.feedback_type,
                "timestamp": item.created_at.isoformat() if item.created_at else None,
                "status": item.status or "new"
            }
            
            # Add fields based on feedback type
            if item.is_page_feedback:
                feedback_dict.update({
                    "page": item.page,
                    "rating": item.rating,
                    "comment": item.comment,
                    "category": item.category,
                    "breadcrumb": item.breadcrumb,
                    "user_timestamp": item.user_timestamp
                })
            elif item.is_cmdb_feedback:
                feedback_dict.update({
                    "filename": item.filename,
                    "original_analysis": item.original_analysis,
                    "user_corrections": item.user_corrections,
                    "asset_type_override": item.asset_type_override
                })
            
            feedback_list.append(feedback_dict)
        
        # Calculate summary statistics using async queries
        total_count_result = await db.execute(select(func.count(Feedback.id)))
        total_count = total_count_result.scalar()
        
        # Get summary by type
        summary_by_type = {}
        type_counts_result = await db.execute(
            select(Feedback.feedback_type, func.count(Feedback.id))
            .group_by(Feedback.feedback_type)
        )
        type_counts = type_counts_result.all()
        
        for feedback_type, count in type_counts:
            summary_by_type[feedback_type] = count
        
        # Get summary by page (for page feedback only)
        summary_by_page = {}
        page_counts_result = await db.execute(
            select(Feedback.page, func.count(Feedback.id))
            .where(Feedback.feedback_type == "page_feedback")
            .where(Feedback.page.isnot(None))
            .group_by(Feedback.page)
        )
        page_counts = page_counts_result.all()
        
        for page, count in page_counts:
            summary_by_page[page] = count
        
        # Get summary by rating
        summary_by_rating = {}
        rating_counts_result = await db.execute(
            select(Feedback.rating, func.count(Feedback.id))
            .where(Feedback.rating.isnot(None))
            .group_by(Feedback.rating)
        )
        rating_counts = rating_counts_result.all()
        
        for rating, count in rating_counts:
            summary_by_rating[f"{rating} stars"] = count
        
        # Get recent feedback (last 10)
        recent_feedback_result = await db.execute(
            select(Feedback)
            .order_by(desc(Feedback.created_at))
            .limit(10)
        )
        recent_feedback = recent_feedback_result.scalars().all()
        
        recent_list = []
        for item in recent_feedback:
            recent_dict = {
                "id": str(item.id),
                "page": item.page,
                "rating": item.rating,
                "comment": item.comment,
                "timestamp": item.created_at.isoformat() if item.created_at else None
            }
            recent_list.append(recent_dict)
        
        return {
            "feedback": feedback_list,
            "total_count": total_count,
            "summary": {
                "by_type": summary_by_type,
                "by_page": summary_by_page,
                "by_rating": summary_by_rating,
                "recent_feedback": recent_list
            },
            "storage_method": "database",
            "filters_applied": {
                "feedback_type": feedback_type,
                "page": page,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

@router.post("/feedback/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update feedback status (new -> reviewed -> resolved).
    """
    try:
        result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        # Validate status
        valid_statuses = ["new", "reviewed", "resolved"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        feedback.status = status
        await db.commit()
        
        logger.info(f"Updated feedback {feedback_id} status to {status}")
        
        return {
            "status": "success",
            "message": f"Feedback status updated to {status}",
            "feedback_id": feedback_id,
            "new_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update feedback status: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update feedback status")

@router.delete("/feedback/{feedback_id}")
async def delete_feedback(feedback_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete feedback entry.
    """
    try:
        result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        await db.delete(feedback)
        await db.commit()
        
        logger.info(f"Deleted feedback {feedback_id}")
        
        return {
            "status": "success",
            "message": "Feedback deleted successfully",
            "feedback_id": feedback_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete feedback: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete feedback")

@router.get("/feedback/stats")
async def get_feedback_stats(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive feedback statistics.
    """
    try:
        total_feedback_result = await db.execute(select(func.count(Feedback.id)))
        total_feedback = total_feedback_result.scalar()
        
        # Average rating for page feedback
        avg_rating_result = await db.execute(
            select(func.avg(Feedback.rating))
            .where(Feedback.feedback_type == "page_feedback")
            .where(Feedback.rating.isnot(None))
        )
        avg_rating = avg_rating_result.scalar()
        
        # Status breakdown
        status_stats_result = await db.execute(
            select(Feedback.status, func.count(Feedback.id))
            .group_by(Feedback.status)
        )
        status_stats = status_stats_result.all()
        
        status_breakdown = {}
        for status, count in status_stats:
            status_breakdown[status or "unknown"] = count
        
        # Page feedback breakdown
        page_stats_result = await db.execute(
            select(Feedback.page, func.count(Feedback.id), func.avg(Feedback.rating))
            .where(Feedback.feedback_type == "page_feedback")
            .where(Feedback.page.isnot(None))
            .group_by(Feedback.page)
        )
        page_stats = page_stats_result.all()
        
        page_breakdown = {}
        for page, count, avg_rating_for_page in page_stats:
            page_breakdown[page] = {
                "count": count,
                "average_rating": float(avg_rating_for_page or 0)
            }
        
        return {
            "total_feedback": total_feedback,
            "average_rating": float(avg_rating or 0),
            "status_breakdown": status_breakdown,
            "page_breakdown": page_breakdown,
            "storage_method": "database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback statistics") 