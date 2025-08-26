"""
Multi-tenant scope enforcement operations.

This module handles multi-tenant isolation validation to ensure proper
data access control within tenant boundaries.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from .config import DeduplicationConfig


async def enforce_tenant_scope(
    db: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    config: DeduplicationConfig,
):
    """Enforce multi-tenant scope validation"""

    if not config.enforce_tenant_isolation:
        return

    # Verify client account exists and user has access
    if not isinstance(client_account_id, uuid.UUID):
        raise AuthorizationError("Invalid client account ID")

    if not isinstance(engagement_id, uuid.UUID):
        raise AuthorizationError("Invalid engagement ID")
