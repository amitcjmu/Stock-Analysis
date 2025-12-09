"""
Engagement query operations (read operations)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import Engagement
from app.schemas.admin_schemas import EngagementResponse

logger = logging.getLogger(__name__)


class EngagementQueries:
    """Handler for engagement read operations"""

    @staticmethod
    async def list_engagements(
        db: AsyncSession,
        client_account_id: Optional[str],
        pagination: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all engagements for a client with pagination."""
        try:
            page = pagination.get("page", 1)
            page_size = pagination.get("page_size", 20)

            # Check if user is platform admin
            is_platform_admin = False
            if user_id:
                try:
                    from app.models.rbac import RoleType, UserRole

                    admin_check = await db.execute(
                        select(UserRole).where(
                            and_(
                                UserRole.user_id == user_id,
                                UserRole.role_type == RoleType.PLATFORM_ADMIN,
                                UserRole.is_active == True,  # noqa: E712
                            )
                        )
                    )
                    admin_role = admin_check.scalar_one_or_none()
                    is_platform_admin = admin_role is not None

                    if is_platform_admin:
                        logger.info(
                            f"Platform admin {user_id} - showing all engagements"
                        )
                except Exception as e:
                    logger.warning(f"Could not check admin status: {e}")

            query = select(Engagement).where(
                Engagement.is_active.is_(True)
            )  # Filter out soft-deleted
            # Only filter by client_account_id if it's provided (not None) AND user is not platform admin
            if client_account_id is not None and not is_platform_admin:
                query = query.where(Engagement.client_account_id == client_account_id)

            # Build the count query with the same conditions
            count_query = (
                select(func.count())
                .select_from(Engagement)
                .where(Engagement.is_active.is_(True))
            )  # noqa: E712
            if client_account_id is not None and not is_platform_admin:
                count_query = count_query.where(
                    Engagement.client_account_id == client_account_id
                )

            total_items_result = await db.execute(count_query)
            total_items = total_items_result.scalar_one()

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(query)
            engagements = result.scalars().all()

            engagement_responses = []
            for eng in engagements:
                # Properly convert database model to response schema
                engagement_responses.append(
                    await EngagementQueries._convert_engagement_to_response(eng)
                )

            total_pages = (total_items + page_size - 1) // page_size

            return {
                "items": engagement_responses,
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        except Exception as e:
            logger.error(
                f"Error listing engagements for client {client_account_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred while listing engagements: {str(e)}",
            )

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for engagements."""
        try:
            # Total engagements (only active ones)
            total_query = select(func.count()).where(
                Engagement.is_active == True  # noqa: E712
            )  # noqa: E712
            total_engagements = (await db.execute(total_query)).scalar_one()

            # Active engagements (redundant now since we only count active ones)
            active_query = select(func.count()).where(
                Engagement.is_active == True  # noqa: E712
            )  # noqa: E712
            active_engagements = (await db.execute(active_query)).scalar_one()

            # Engagements by type (only active ones)
            type_query = (
                select(Engagement.engagement_type, func.count())
                .where(Engagement.is_active.is_(True))  # noqa: E712
                .group_by(Engagement.engagement_type)
            )
            engagements_by_type = {
                row[0]: row[1] for row in (await db.execute(type_query)).all() if row[0]
            }

            # Engagements by status (only active ones)
            status_query = (
                select(Engagement.status, func.count())
                .where(Engagement.is_active.is_(True))  # noqa: E712
                .group_by(Engagement.status)
            )
            engagements_by_status = {
                row[0]: row[1]
                for row in (await db.execute(status_query)).all()
                if row[0]
            }

            # Average engagement duration (only active ones)
            duration_query = select(
                func.avg(
                    func.extract(
                        "epoch",
                        Engagement.actual_completion_date - Engagement.start_date,
                    )
                    / (60 * 60 * 24)
                )
            ).where(
                Engagement.is_active == True,  # noqa: E712
                Engagement.actual_completion_date.isnot(None),
                Engagement.start_date.isnot(None),
            )
            avg_duration_result = (
                await db.execute(duration_query)
            ).scalar_one_or_none()
            avg_engagement_duration_days = (
                round(avg_duration_result, 2) if avg_duration_result else 0.0
            )

            # Recent engagements (last 30 days, only active ones)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = (
                select(Engagement)
                .where(
                    Engagement.is_active == True,  # noqa: E712
                    Engagement.created_at >= thirty_days_ago,
                )
                .order_by(Engagement.created_at.desc())
                .limit(5)
            )
            recent_engagements = (await db.execute(recent_query)).scalars().all()

            # Convert recent engagements to response format
            recent_engagement_responses = []
            for eng in recent_engagements:
                recent_engagement_responses.append(
                    await EngagementQueries._convert_engagement_to_response(eng)
                )

            return {
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "engagements_by_type": engagements_by_type,
                "engagements_by_status": engagements_by_status,
                "avg_engagement_duration_days": avg_engagement_duration_days,
                "recent_engagements": recent_engagement_responses,
            }
        except Exception as e:
            logger.error(
                f"Error getting engagement dashboard stats: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}"
            )

    @staticmethod
    async def get_engagement(
        engagement_id: str, db: AsyncSession
    ) -> EngagementResponse:
        """Get engagement by ID."""
        try:
            query = select(Engagement).where(
                Engagement.id == engagement_id,
                Engagement.is_active,  # noqa: E712  # Only return active engagements
            )
            result = await db.execute(query)
            engagement = result.scalar_one_or_none()

            if not engagement:
                raise HTTPException(status_code=404, detail="Engagement not found")

            return await EngagementQueries._convert_engagement_to_response(engagement)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving engagement {engagement_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve engagement: {str(e)}"
            )

    @staticmethod
    async def _convert_engagement_to_response(
        engagement: Engagement,
    ) -> EngagementResponse:
        """Convert Engagement model to EngagementResponse schema with proper field mapping."""
        try:
            # Handle migration_scope - convert to string if it's a dict
            migration_scope = engagement.migration_scope
            if isinstance(migration_scope, dict):
                # Convert dict to a readable string representation
                scope_parts = []
                if migration_scope.get("target_clouds"):
                    scope_parts.append(
                        f"Clouds: {', '.join(migration_scope['target_clouds'])}"
                    )
                if migration_scope.get("migration_strategies"):
                    scope_parts.append(
                        f"Strategies: {', '.join(migration_scope['migration_strategies'])}"
                    )
                if migration_scope.get("business_units"):
                    scope_parts.append(
                        f"Units: {', '.join(migration_scope['business_units'])}"
                    )
                if migration_scope.get("scope_type"):
                    scope_parts.append(f"Type: {migration_scope['scope_type']}")
                migration_scope = (
                    "; ".join(scope_parts) if scope_parts else "Full Migration"
                )
            elif not migration_scope:
                migration_scope = "Full Migration"

            # Extract budget information from settings
            settings = engagement.settings or {}
            estimated_budget = settings.get("estimated_budget", 0.0)
            settings.get("budget_currency", "USD")

            return EngagementResponse(
                id=str(engagement.id),
                engagement_name=engagement.name,  # Map 'name' to 'engagement_name'
                client_account_id=str(engagement.client_account_id),
                engagement_description=engagement.description,
                migration_scope=migration_scope,
                target_cloud_provider=engagement.engagement_type or "aws",
                planned_start_date=engagement.start_date,
                planned_end_date=engagement.target_completion_date,
                estimated_budget=estimated_budget,
                actual_start_date=engagement.start_date,  # Use start_date as actual_start_date
                actual_end_date=engagement.actual_completion_date,
                engagement_manager=engagement.client_contact_name or "Not Assigned",
                technical_lead=settings.get(
                    "technical_lead", engagement.client_contact_name or "Not Assigned"
                ),
                team_preferences=engagement.team_preferences or {},
                agent_configuration=settings.get("agent_configuration", {}),
                discovery_preferences=settings.get("discovery_preferences", {}),
                assessment_criteria=settings.get("assessment_criteria", {}),
                current_phase=engagement.status or "planning",
                completion_percentage=0.0,  # Default to 0.0
                current_flow_id=None,  # Default to None
                created_at=engagement.created_at,
                updated_at=engagement.updated_at,
                is_active=engagement.is_active,
                total_flows=0,  # Default to 0
                total_assets=0,  # Default to 0
            )
        except Exception as e:
            logger.error(f"Error converting engagement to response: {e}")
            # Return a minimal valid response to prevent complete failure
            return EngagementResponse(
                id=str(engagement.id),
                engagement_name=engagement.name or "Unknown Engagement",
                client_account_id=str(engagement.client_account_id),
                engagement_description=engagement.description or "",
                migration_scope="Full Migration",
                target_cloud_provider="aws",
                current_phase="planning",
                completion_percentage=0.0,
                created_at=engagement.created_at or datetime.utcnow(),
                is_active=engagement.is_active,
            )
