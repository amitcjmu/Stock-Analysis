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
        try:
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

            engagement_responses = []
            for eng in engagements:
                eng_dict = {
                    "id": str(eng.id),
                    "client_account_id": str(eng.client_account_id),
                    "engagement_name": eng.name,
                    "engagement_description": eng.description,
                    "migration_scope": eng.migration_scope,
                    "target_cloud_provider": eng.engagement_type,
                    "planned_start_date": eng.start_date,
                    "planned_end_date": eng.target_completion_date,
                    "created_at": eng.created_at,
                    "updated_at": eng.updated_at,
                    "is_active": eng.is_active,
                    "current_phase": eng.status
                }
                engagement_responses.append(EngagementResponse(**eng_dict))
            
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
        except Exception as e:
            logger.error(f"Error listing engagements for client {client_account_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while listing engagements.")

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for engagements."""
        try:
            # Total engagements
            total_query = select(func.count()).select_from(Engagement)
            total_engagements = (await db.execute(total_query)).scalar_one()

            # Active engagements
            active_query = select(func.count()).where(Engagement.is_active == True)
            active_engagements = (await db.execute(active_query)).scalar_one()

            # Engagements by type
            type_query = select(Engagement.engagement_type, func.count()).group_by(Engagement.engagement_type)
            engagements_by_type = {
                row[0]: row[1] for row in (await db.execute(type_query)).all() if row[0]
            }

            # Engagements by status
            status_query = select(Engagement.status, func.count()).group_by(Engagement.status)
            engagements_by_status = {
                row[0]: row[1] for row in (await db.execute(status_query)).all() if row[0]
            }
            
            # Average engagement duration
            duration_query = select(
                func.avg(
                    func.extract('epoch', Engagement.actual_completion_date - Engagement.start_date) / (60*60*24)
                )
            ).where(
                Engagement.actual_completion_date.isnot(None),
                Engagement.start_date.isnot(None)
            )
            avg_duration_result = (await db.execute(duration_query)).scalar_one_or_none()
            avg_engagement_duration_days = round(avg_duration_result, 2) if avg_duration_result else 0.0

            # Recent engagements (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = select(Engagement).where(Engagement.created_at >= thirty_days_ago).order_by(Engagement.created_at.desc()).limit(5)
            recent_engagements = (await db.execute(recent_query)).scalars().all()
            recent_engagement_responses = [EngagementResponse.model_validate(e, from_attributes=True) for e in recent_engagements]

            return {
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "engagements_by_type": engagements_by_type,
                "engagements_by_status": engagements_by_status,
                "avg_engagement_duration_days": avg_engagement_duration_days,
                "recent_engagements": recent_engagement_responses,
            }
        except Exception as e:
            logger.error(f"Error getting engagement dashboard stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}") 