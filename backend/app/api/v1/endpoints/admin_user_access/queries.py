"""
Query handlers for Admin User Access Management (GET endpoints)
"""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import ClientAccess, EngagementAccess
from app.models.rbac.audit_models import AccessAuditLog

from .models import (
    ClientAccessResponse,
    EngagementAccessResponse,
    RecentActivityResponse,
)
from .validators import verify_admin_access

logger = logging.getLogger(__name__)


async def get_user_client_access(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all client access records for a user"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

        # Get client access records
        query = (
            select(ClientAccess, ClientAccount)
            .join(ClientAccount, ClientAccess.client_account_id == ClientAccount.id)
            .where(ClientAccess.user_profile_id == user_id)
            .order_by(ClientAccess.granted_at.desc())
        )

        result = await db.execute(query)
        access_records = result.all()

        client_access_list = []
        for access, client in access_records:
            client_access_list.append(
                ClientAccessResponse(
                    id=str(access.id),
                    client_account_id=str(access.client_account_id),
                    client_name=client.name,
                    access_level=access.access_level or "read",
                    is_active=access.is_active,
                    granted_at=(
                        access.granted_at.isoformat() if access.granted_at else ""
                    ),
                ).dict()
            )

        return {
            "status": "success",
            "client_access": client_access_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user client access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch client access: {str(e)}",
        )


async def get_user_engagement_access(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all engagement access records for a user"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

        # Get engagement access records
        query = (
            select(EngagementAccess, Engagement, ClientAccount)
            .join(Engagement, EngagementAccess.engagement_id == Engagement.id)
            .join(ClientAccount, Engagement.client_account_id == ClientAccount.id)
            .where(EngagementAccess.user_profile_id == user_id)
            .order_by(EngagementAccess.granted_at.desc())
        )

        result = await db.execute(query)
        access_records = result.all()

        engagement_access_list = []
        for access, engagement, client in access_records:
            engagement_access_list.append(
                EngagementAccessResponse(
                    id=str(access.id),
                    engagement_id=str(access.engagement_id),
                    engagement_name=engagement.name,
                    client_account_id=str(engagement.client_account_id),
                    client_name=client.name,
                    access_level=access.access_level or "read",
                    is_active=access.is_active,
                    granted_at=(
                        access.granted_at.isoformat() if access.granted_at else ""
                    ),
                ).dict()
            )

        return {
            "status": "success",
            "engagement_access": engagement_access_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user engagement access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch engagement access: {str(e)}",
        )


async def get_recent_activities(
    limit: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get recent admin activities from audit log"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

        # Query recent activities with user information
        query = (
            select(AccessAuditLog, User)
            .join(User, AccessAuditLog.user_id == User.id)
            .order_by(AccessAuditLog.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        activities_with_users = result.all()

        activities_list = []
        for audit_log, user in activities_with_users:
            user_name = f"{user.first_name} {user.last_name}".strip() or user.email
            activities_list.append(
                RecentActivityResponse(
                    id=str(audit_log.id),
                    user_name=user_name,
                    action_type=audit_log.action_type,
                    resource_type=audit_log.resource_type or "",
                    resource_id=audit_log.resource_id or "",
                    result=audit_log.result,
                    reason=audit_log.reason or "",
                    created_at=audit_log.created_at.isoformat(),
                ).dict()
            )

        return {
            "status": "success",
            "activities": activities_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activities: {str(e)}",
        )
