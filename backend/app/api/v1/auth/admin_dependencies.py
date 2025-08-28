"""
Admin authorization dependencies for protecting admin endpoints
"""

from fastapi import Depends, HTTPException, status
from app.api.v1.auth.auth_utils import get_current_user
from app.models.client_account import User
import logging

logger = logging.getLogger(__name__)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the current user has admin privileges.
    Raises 403 Forbidden if the user is not an admin.
    """
    # User is admin if they have is_admin=True OR role="admin"
    is_admin_by_flag = getattr(current_user, "is_admin", False)
    user_role = (
        getattr(current_user, "role", None) if hasattr(current_user, "role") else None
    )
    is_admin_by_role = user_role == "admin"

    # Allow access only if either condition is true
    if not (is_admin_by_flag or is_admin_by_role):
        # Deny access - user is neither is_admin=True nor has role="admin"
        logger.warning(
            f"Non-admin user {current_user.id} attempted to access admin endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )

    return current_user


async def require_admin_or_owner(
    resource_owner_id: str, current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is either admin or owns the resource.
    """
    # Admins can access anything
    if getattr(current_user, "is_admin", False):
        return current_user

    # Check if user owns the resource
    if str(current_user.id) == resource_owner_id:
        return current_user

    logger.warning(
        f"User {current_user.id} denied access to resource owned by {resource_owner_id}"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this resource",
    )
