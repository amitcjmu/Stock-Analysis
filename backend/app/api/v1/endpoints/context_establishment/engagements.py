"""
Engagement retrieval endpoint for context establishment.

Handles GET /engagements endpoint - provides list of engagements for a client.
CRITICAL: Preserves RBAC fix at line 368 (ClientAccess.is_active.is_(True)).
"""

import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models import User

from .models import EngagementResponse, EngagementsListResponse
from .utils import (
    CLIENT_ACCOUNT_AVAILABLE,
    ClientAccount,
    ClientAccess,
    DEMO_CLIENT_ID,
    Engagement,
    get_logger,
    UserRole,
)

router = APIRouter()
logger = get_logger(__name__)


@router.get("/engagements", response_model=EngagementsListResponse)
async def get_context_engagements(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of engagements for a specific client for context establishment.

    This endpoint is exempt from engagement context requirements and is specifically
    designed for initial context setup. It only requires authentication and client_id.

    Args:
        client_id: The client ID to get engagements for (query parameter)
    """
    try:
        logger.info(
            f"🔍 Context Establishment: Getting engagements for client {client_id}, user {current_user.id}"
        )

        if not CLIENT_ACCOUNT_AVAILABLE:
            # Return demo data if models not available (only for demo client)
            if client_id == DEMO_CLIENT_ID:
                demo_engagements = [
                    EngagementResponse(
                        id="22222222-2222-2222-2222-222222222222",
                        name="Cloud Migration 2024",
                        client_id=client_id,
                        status="active",
                        type="migration",
                    )
                ]
                return EngagementsListResponse(engagements=demo_engagements)
            else:
                return EngagementsListResponse(engagements=[])

        # Check if user is platform admin
        role_query = select(UserRole).where(
            and_(
                UserRole.user_id == current_user.id,
                UserRole.role_type == "platform_admin",
                UserRole.is_active,
            )
        )
        role_result = await db.execute(role_query)
        is_platform_admin = role_result.scalar_one_or_none() is not None

        # Verify client exists and is active
        logger.info(
            safe_log_format(
                "🔍 Looking for client: {client_id} (type: {type_client_id})",
                client_id=client_id,
                type_client_id=type(client_id),
            )
        )

        # First check if client exists at all
        client_exists_query = select(ClientAccount).where(ClientAccount.id == client_id)
        exists_result = await db.execute(client_exists_query)
        client_exists = exists_result.scalar_one_or_none()

        if not client_exists:
            logger.error(
                safe_log_format(
                    "❌ Client not found in database: {client_id}", client_id=client_id
                )
            )
            raise HTTPException(status_code=404, detail="Client not found")

        # Now check if it's active (handle NULL as active for backward compatibility)
        client_query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_id,
                or_(ClientAccount.is_active, ClientAccount.is_active.is_(None)),
            )
        )
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()

        if not client:
            logger.error(
                f"❌ Client {client_id} exists but is marked as inactive (is_active=False)"
            )
            raise HTTPException(status_code=404, detail="Client not found or inactive")

        logger.info(
            safe_log_format(
                "✅ Found active client: {client_name} ({client_id})",
                client_name=client.name,
                client_id=client.id,
            )
        )

        if not is_platform_admin:
            # Regular users: Verify they have access to this client
            logger.info(
                f"🔍 Checking ClientAccess for user_profile_id={str(current_user.id)}, client_id={client_id}"
            )
            access_check_query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == str(current_user.id),
                    ClientAccess.client_account_id == client_id,
                    # CRITICAL: SQLAlchemy boolean comparison - .is_(True) for flake8 E712
                    # This is the RBAC fix that MUST be preserved (original line 368)
                    ClientAccess.is_active.is_(True),
                )
            )
            access_result = await db.execute(access_check_query)
            client_access = access_result.scalar_one_or_none()

            access_id = client_access.id if client_access else "None"
            logger.info(
                f"🔍 ClientAccess query result: {client_access is not None} "
                f"(found={access_id})"
            )

            # Special case for demo user accessing demo client
            is_demo_access = (
                current_user.email
                and current_user.email.endswith("@demo-corp.com")
                and client_id == DEMO_CLIENT_ID
            )

            logger.info(
                f"🔍 is_demo_access={is_demo_access}, user_email={current_user.email}"
            )

            if not client_access and not is_demo_access:
                logger.error(
                    f"❌ Access denied for user {current_user.id} to client {client_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: No permission for this client",
                )

        # Get ONLY ACTIVE engagements for this client that the user is authorized to see
        # Handle NULL is_active as active for backward compatibility
        query = (
            select(Engagement)
            .where(
                and_(
                    Engagement.client_account_id == client_id,
                    or_(Engagement.is_active, Engagement.is_active.is_(None)),
                )
            )
            .order_by(Engagement.name)
        )

        result = await db.execute(query)
        engagements = result.scalars().all()

        engagement_responses = []
        for engagement in engagements:
            engagement_responses.append(
                EngagementResponse(
                    id=str(engagement.id),
                    name=engagement.name,
                    client_id=str(engagement.client_account_id),
                    status=engagement.status or "active",
                    type=engagement.engagement_type,
                    start_date=(
                        engagement.start_date.isoformat()
                        if engagement.start_date
                        else None
                    ),
                    end_date=(
                        engagement.target_completion_date.isoformat()
                        if engagement.target_completion_date
                        else None
                    ),
                )
            )

        logger.info(
            f"✅ Context Establishment: Found {len(engagement_responses)} engagements for client {client_id}"
        )
        return EngagementsListResponse(engagements=engagement_responses)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error in context establishment - get engagements: {e}", e=e
            )
        )
        logger.error(
            safe_log_format(
                "Traceback: {traceback_format_exc}",
                traceback_format_exc=traceback.format_exc(),
            )
        )
        # Return demo data as fallback only for demo client
        if client_id == DEMO_CLIENT_ID:
            demo_engagements = [
                EngagementResponse(
                    id="22222222-2222-2222-2222-222222222222",
                    name="Demo Cloud Migration Project",
                    client_id=client_id,
                    status="active",
                    type="migration",
                )
            ]
            return EngagementsListResponse(engagements=demo_engagements)
        else:
            return EngagementsListResponse(engagements=[])
