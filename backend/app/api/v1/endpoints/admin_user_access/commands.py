"""
Command handlers for Admin User Access Management (POST/DELETE endpoints)
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import ClientAccess, EngagementAccess

from .models import GrantClientAccessRequest, GrantEngagementAccessRequest
from .validators import verify_admin_access, verify_client_access

logger = logging.getLogger(__name__)


async def grant_client_access(
    request: GrantClientAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Grant a user access to a client"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

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

        # Verify admin has access to this client (tenant scope verification)
        await verify_client_access(current_user, request.client_account_id, db)

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


async def grant_engagement_access(
    request: GrantEngagementAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Grant a user access to an engagement"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

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

        # Verify admin has access to the client that owns this engagement
        await verify_client_access(current_user, str(engagement.client_account_id), db)

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


async def revoke_client_access(
    access_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Revoke a user's access to a client"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

        # Validate and convert access_id to UUID
        try:
            access_uuid = UUID(access_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid access ID format",
            )

        # Get the access record
        access_query = select(ClientAccess).where(ClientAccess.id == access_uuid)
        access_result = await db.execute(access_query)
        access = access_result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client access record not found",
            )

        # Verify admin has access to this client (tenant scope verification)
        await verify_client_access(current_user, str(access.client_account_id), db)

        # Soft delete: Mark as inactive instead of hard delete (preserves audit trail)
        access.is_active = False
        await db.commit()

        logger.info(f"Revoked client access (soft delete): access_id={access_id}")

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


async def revoke_engagement_access(
    access_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Revoke a user's access to an engagement"""
    try:
        # Verify admin access
        await verify_admin_access(current_user, db)

        # Validate and convert access_id to UUID
        try:
            access_uuid = UUID(access_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid access ID format",
            )

        # Get the access record with engagement details for tenant verification
        access_query = (
            select(EngagementAccess, Engagement)
            .join(Engagement, EngagementAccess.engagement_id == Engagement.id)
            .where(EngagementAccess.id == access_uuid)
        )
        access_result = await db.execute(access_query)
        result = access_result.first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement access record not found",
            )

        access, engagement = result

        # Verify admin has access to the client that owns this engagement
        await verify_client_access(current_user, str(engagement.client_account_id), db)

        # Soft delete: Mark as inactive instead of hard delete (preserves audit trail)
        access.is_active = False
        await db.commit()

        logger.info(f"Revoked engagement access (soft delete): access_id={access_id}")

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
