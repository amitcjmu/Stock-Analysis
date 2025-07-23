"""
Context helper functions for multi-tenant access verification.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def verify_client_access(
    x_client_account_id: Optional[str] = Header(None, alias="X-Client-Account-ID")
) -> str:
    """
    Verify client account access from header.
    Returns client_account_id if valid, raises exception otherwise.
    """
    if not x_client_account_id:
        raise HTTPException(
            status_code=400,
            detail="Client account context is required. Please provide X-Client-Account-ID header.",
        )

    # TODO: Add actual permission verification here
    # For now, just return the client account ID
    return x_client_account_id


async def verify_engagement_access(
    db: AsyncSession, engagement_id: str, client_account_id: str
) -> bool:
    """
    Verify user has access to the specified engagement.
    """
    # TODO: Implement actual engagement access verification
    # For now, just return True
    logger.info(
        f"Verifying engagement access: engagement_id={engagement_id}, client_account_id={client_account_id}"
    )
    return True


async def verify_standards_modification_permission(
    current_user, client_account_id: str
) -> bool:
    """
    Verify user has permission to modify architecture standards.
    """
    # TODO: Implement RBAC permission check
    # For now, allow all authenticated users
    return True
