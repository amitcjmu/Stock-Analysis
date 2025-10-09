"""
Admin User Access Management API Endpoints

Provides endpoints for admins to manage user access to clients and engagements.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import ClientAccess, EngagementAccess, UserRole
from app.models.rbac.audit_models import AccessAuditLog

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class ClientAccessResponse(BaseModel):
    id: str
    client_account_id: str
    client_name: str
    access_level: str
    is_active: bool
    granted_at: str


class EngagementAccessResponse(BaseModel):
    id: str
    engagement_id: str
    engagement_name: str
    client_account_id: str
    client_name: str
    access_level: str
    is_active: bool
    granted_at: str


class GrantClientAccessRequest(BaseModel):
    user_id: str
    client_account_id: str
    access_level: str


class GrantEngagementAccessRequest(BaseModel):
    user_id: str
    engagement_id: str
    access_level: str


class RecentActivityResponse(BaseModel):
    id: str
    user_name: str
    action_type: str
    resource_type: str
    resource_id: str
    result: str
    reason: str
    created_at: str


async def _verify_admin_access(current_user: User, db: AsyncSession) -> bool:
    """Verify the current user has admin privileges"""
    role_query = select(UserRole).where(
        and_(
            UserRole.user_id == current_user.id,
            UserRole.role_type.in_(["platform_admin", "client_admin"]),
            UserRole.is_active == True,  # noqa: E712
        )
    )
    result = await db.execute(role_query)
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return True


@router.get("/clients/{user_id}")
async def get_user_client_access(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all client access records for a user"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

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


@router.get("/engagements/{user_id}")
async def get_user_engagement_access(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all engagement access records for a user"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

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


@router.post("/clients")
async def grant_client_access(
    request: GrantClientAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Grant a user access to a client"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

        # Verify client exists
        client_query = select(ClientAccount).where(
            ClientAccount.id == request.client_account_id
        )
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        # Check if access already exists
        existing_query = select(ClientAccess).where(
            and_(
                ClientAccess.user_profile_id == request.user_id,
                ClientAccess.client_account_id == request.client_account_id,
            )
        )
        existing_result = await db.execute(existing_query)
        existing_access = existing_result.scalar_one_or_none()

        if existing_access:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has access to this client",
            )

        # Create new client access record
        new_access = ClientAccess(
            user_profile_id=UUID(request.user_id),
            client_account_id=UUID(request.client_account_id),
            access_level=request.access_level,
            is_active=True,
            granted_by=str(current_user.id),
        )

        db.add(new_access)
        await db.commit()
        await db.refresh(new_access)

        logger.info(
            f"Granted client access: user={request.user_id}, client={request.client_account_id}"
        )

        return {
            "status": "success",
            "message": "Client access granted successfully",
            "access_id": str(new_access.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting client access: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant client access: {str(e)}",
        )


@router.post("/engagements")
async def grant_engagement_access(
    request: GrantEngagementAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Grant a user access to an engagement"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

        # Verify engagement exists
        engagement_query = select(Engagement).where(
            Engagement.id == request.engagement_id
        )
        engagement_result = await db.execute(engagement_query)
        engagement = engagement_result.scalar_one_or_none()

        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found",
            )

        # Check if access already exists
        existing_query = select(EngagementAccess).where(
            and_(
                EngagementAccess.user_profile_id == request.user_id,
                EngagementAccess.engagement_id == request.engagement_id,
            )
        )
        existing_result = await db.execute(existing_query)
        existing_access = existing_result.scalar_one_or_none()

        if existing_access:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has access to this engagement",
            )

        # Create new engagement access record
        new_access = EngagementAccess(
            user_profile_id=UUID(request.user_id),
            engagement_id=UUID(request.engagement_id),
            access_level=request.access_level,
            is_active=True,
            granted_by=str(current_user.id),
        )

        db.add(new_access)
        await db.commit()
        await db.refresh(new_access)

        logger.info(
            f"Granted engagement access: user={request.user_id}, engagement={request.engagement_id}"
        )

        return {
            "status": "success",
            "message": "Engagement access granted successfully",
            "access_id": str(new_access.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting engagement access: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant engagement access: {str(e)}",
        )


@router.delete("/clients/{access_id}")
async def revoke_client_access(
    access_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Revoke a user's access to a client"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

        # Get the access record
        access_query = select(ClientAccess).where(ClientAccess.id == access_id)
        access_result = await db.execute(access_query)
        access = access_result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client access record not found",
            )

        # Delete the access record
        await db.delete(access)
        await db.commit()

        logger.info(f"Revoked client access: access_id={access_id}")

        return {
            "status": "success",
            "message": "Client access revoked successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking client access: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke client access: {str(e)}",
        )


@router.delete("/engagements/{access_id}")
async def revoke_engagement_access(
    access_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Revoke a user's access to an engagement"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

        # Get the access record
        access_query = select(EngagementAccess).where(EngagementAccess.id == access_id)
        access_result = await db.execute(access_query)
        access = access_result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement access record not found",
            )

        # Delete the access record
        await db.delete(access)
        await db.commit()

        logger.info(f"Revoked engagement access: access_id={access_id}")

        return {
            "status": "success",
            "message": "Engagement access revoked successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking engagement access: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke engagement access: {str(e)}",
        )


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get recent admin activities from audit log"""
    try:
        # Verify admin access
        await _verify_admin_access(current_user, db)

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
