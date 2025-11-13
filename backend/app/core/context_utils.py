"""
Context utility functions.
Extracted from context.py to reduce file size and complexity.
"""

import logging
from typing import Dict, Optional

from fastapi import HTTPException
from app.core.security.secure_logging import safe_log_format
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def resolve_demo_client_ids(
    db_session, demo_client_config: Dict[str, str]
) -> None:
    """
    Resolve and update demo client configuration from database.
    This ensures we're using actual UUIDs from the database.

    Args:
        db_session: Database session for queries
        demo_client_config: Demo client configuration dict to update
    """
    try:
        from app.models.client_account import ClientAccount, Engagement

        # Find the Complete Test Client
        client = await db_session.execute(
            select(ClientAccount).where(ClientAccount.name == "Complete Test Client")
        )
        client = client.scalar_one_or_none()

        if client:
            demo_client_config["client_account_id"] = str(client.id)

            # Find the Azure Transformation engagement
            engagement = await db_session.execute(
                select(Engagement).where(
                    Engagement.client_account_id == client.id,
                    Engagement.name == "Azure Transformation",
                )
            )
            engagement = engagement.scalar_one_or_none()

            if engagement:
                demo_client_config["engagement_id"] = str(engagement.id)

        logger.info(
            safe_log_format(
                "✅ Demo client configuration resolved: {demo_client_config}",
                demo_client_config=demo_client_config,
            )
        )

    except Exception as e:
        logger.warning(
            safe_log_format(
                "⚠️ Could not resolve demo client IDs from database: {e}", e=e
            )
        )
        # Keep using the hardcoded UUIDs as fallback


def create_context_headers(context) -> Dict[str, str]:
    """
    Create HTTP headers from request context.

    Args:
        context: RequestContext to convert to headers

    Returns:
        Dictionary of headers
    """
    headers = {}

    if context.client_account_id:
        headers["X-Client-Account-Id"] = context.client_account_id

    if context.engagement_id:
        headers["X-Engagement-Id"] = context.engagement_id

    if context.user_id:
        headers["X-User-Id"] = context.user_id

    if context.flow_id:
        headers["X-Flow-Id"] = context.flow_id

    return headers


def is_demo_client(
    client_account_id: Optional[str], demo_client_config: Dict[str, str]
) -> bool:
    """
    Check if the given client account ID matches our demo client.

    Args:
        client_account_id: Client account ID to check
        demo_client_config: Demo client configuration with IDs

    Returns:
        True if this is the demo client
    """
    return client_account_id == demo_client_config["client_account_id"]


def validate_context(
    context,
    require_client: bool = True,
    require_engagement: bool = False,
) -> None:
    """
    Validate that required context is present.

    Args:
        context: RequestContext to validate
        require_client: Whether client account ID is required
        require_engagement: Whether engagement ID is required

    Raises:
        HTTPException: If required context is missing
    """
    if require_client and not context.client_account_id:
        raise HTTPException(
            status_code=403,  # Changed from 400 to 403 for security
            detail=(
                "Client account context is required for multi-tenant security. "
                "Please provide one of: X-Client-Account-ID, X-Client-Account-Id, or x-client-account-id header. "
                "Note: HTTP headers are case-insensitive, any casing will work."
            ),
        )

    if require_engagement and not context.engagement_id:
        raise HTTPException(
            status_code=403,  # Changed from 400 to 403 for security
            detail=(
                "Engagement context is required for multi-tenant security. "
                "Please provide one of: X-Engagement-ID, X-Engagement-Id, or x-engagement-id header. "
                "Note: HTTP headers are case-insensitive, any casing will work."
            ),
        )
