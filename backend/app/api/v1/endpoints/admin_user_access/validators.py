"""
Validation and access control helpers for Admin User Access Management
"""

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.rbac import ClientAccess, UserRole


async def verify_admin_access(current_user: User, db: AsyncSession) -> bool:
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


async def verify_client_access(
    current_user: User, client_account_id: str, db: AsyncSession
) -> bool:
    """Verify the admin has access to the specified client account"""
    # Check if user is platform_admin (has access to all clients)
    platform_admin_query = select(UserRole).where(
        and_(
            UserRole.user_id == current_user.id,
            UserRole.role_type == "platform_admin",
            UserRole.is_active == True,  # noqa: E712
        )
    )
    result = await db.execute(platform_admin_query)
    if result.scalar_one_or_none():
        return True

    # Check if user has ClientAccess for this specific client
    client_access_query = select(ClientAccess).where(
        and_(
            ClientAccess.user_profile_id == current_user.id,
            ClientAccess.client_account_id == client_account_id,
            ClientAccess.is_active == True,  # noqa: E712
        )
    )
    result = await db.execute(client_access_query)
    if result.scalar_one_or_none():
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to manage this client",
    )
