"""
Engagement CRUD Handler - Core engagement operations
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.client_account import Engagement
from app.schemas.admin_schemas import EngagementResponse
from datetime import datetime, timedelta
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class EngagementCRUDHandler:
    """Handler for engagement CRUD operations"""

    @staticmethod
    async def list_engagements(
        db: AsyncSession,
        client_account_id: str,
        pagination: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List all engagements for a client with pagination."""
        page = pagination.get('page', 1)
        page_size = pagination.get('page_size', 20)

        query = select(Engagement)
        if client_account_id:
             query = query.where(Engagement.client_account_id == client_account_id)
        
        total_items_query = select(func.count()).select_from(query.alias())
        total_items_result = await db.execute(total_items_query)
        total_items = total_items_result.scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        engagements = result.scalars().all()

        engagement_responses = [EngagementResponse.model_validate(eng) for eng in engagements]
            
        total_pages = (total_items + page_size - 1) // page_size
        
        return {
            "items": engagement_responses,
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for engagements."""
        try:
            # Total engagements
            total_query = select(func.count()).select_from(Engagement)
            total_result = await db.execute(total_query)
            total_engagements = total_result.scalar_one()

            # Active engagements
            active_query = select(func.count()).select_from(Engagement).where(Engagement.status == 'In Progress')
            active_result = await db.execute(active_query)
            active_engagements = active_result.scalar_one()

            # Engagements by type
            type_query = select(Engagement.engagement_type, func.count()).group_by(Engagement.engagement_type)
            type_result = await db.execute(type_query)
            engagements_by_type = {row[0]: row[1] for row in type_result.all() if row[0]}

            # Engagements by status
            status_query = select(Engagement.status, func.count()).group_by(Engagement.status)
            status_result = await db.execute(status_query)
            engagements_by_status = {row[0]: row[1] for row in status_result.all() if row[0]}
            
            # Recent engagements (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_query = select(Engagement).where(Engagement.created_at >= seven_days_ago).order_by(Engagement.created_at.desc()).limit(5)
            recent_result = await db.execute(recent_query)
            recent_engagements = recent_result.scalars().all()

            return {
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "engagements_by_type": engagements_by_type,
                "engagements_by_status": engagements_by_status,
                "avg_engagement_duration_days": 0, # Placeholder
                "recent_engagements": recent_engagements
            }
        except Exception as e:
            logger.error(f"Error getting engagement dashboard stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve dashboard stats") 