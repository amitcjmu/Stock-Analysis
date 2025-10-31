"""
Client retrieval endpoint for context establishment.

Handles GET /clients endpoint - provides list of accessible clients for user.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models import User

from .models import ClientResponse, ClientsListResponse
from .utils import (
    CLIENT_ACCOUNT_AVAILABLE,
    ClientAccount,
    DEMO_CLIENT_ID,
    get_logger,
    UserRole,
)

router = APIRouter()
logger = get_logger(__name__)


def _get_demo_clients() -> ClientsListResponse:
    """Get demo client data for fallback scenarios."""
    demo_clients = [
        ClientResponse(
            id=DEMO_CLIENT_ID,
            name="Democorp",
            industry="Technology",
            company_size="Enterprise",
            status="active",
        )
    ]
    return ClientsListResponse(clients=demo_clients)


async def _get_platform_admin_clients(db: AsyncSession) -> ClientsListResponse:
    """Get all active clients for platform admin users."""
    clients_query = (
        select(ClientAccount)
        .where(ClientAccount.is_active)
        .order_by(ClientAccount.name)
    )

    result = await db.execute(clients_query)
    all_clients = result.scalars().all()

    client_responses = []
    for client in all_clients:
        client_responses.append(
            ClientResponse(
                id=str(client.id),
                name=client.name,
                industry=client.industry,
                company_size=client.company_size,
                status="active" if client.is_active else "inactive",
            )
        )

    return ClientsListResponse(clients=client_responses)


async def _get_regular_user_clients(
    db: AsyncSession, current_user: User
) -> ClientsListResponse:
    """Get clients accessible to regular (non-admin) users."""
    logger.info(f"🔍 Looking for client access for user_profile_id: {current_user.id}")

    # Import ClientAccess from utils (already imported conditionally)
    from .utils import ClientAccess

    access_query = (
        select(ClientAccess, ClientAccount)
        .join(ClientAccount, ClientAccess.client_account_id == ClientAccount.id)
        .where(
            and_(
                ClientAccess.user_profile_id == str(current_user.id),
                ClientAccess.is_active,
                ClientAccount.is_active,
            )
        )
    )

    # Debug: Print the actual SQL query (only in development)
    if logger.isEnabledFor(logging.DEBUG):
        try:
            compiled_query = str(access_query.compile())
            logger.debug(
                safe_log_format(
                    "🔍 SQL Query structure: {compiled_query}",
                    compiled_query=compiled_query,
                )
            )
        except Exception as e:
            logger.debug(safe_log_format("🔍 SQL Query compilation failed: {e}", e=e))

    result = await db.execute(access_query)
    accessible_clients = result.all()
    logger.info(
        f"🔍 Found {len(accessible_clients)} accessible clients for user {current_user.id}"
    )

    # Debug logging for empty results
    if len(accessible_clients) == 0:
        await _debug_log_client_access(db, current_user.id)

    client_responses = []
    for client_access, client in accessible_clients:
        client_responses.append(
            ClientResponse(
                id=str(client.id),
                name=client.name,
                industry=client.industry,
                company_size=client.company_size,
                status="active" if client.is_active else "inactive",
            )
        )

    # Fallback to demo client for demo users
    if not client_responses and _is_demo_user(current_user):
        return await _get_demo_client_from_db(db)

    return ClientsListResponse(clients=client_responses)


async def _debug_log_client_access(db: AsyncSession, user_id: str):
    """Debug logging for client access issues."""
    from .utils import ClientAccess

    # Check if ClientAccess records exist at all
    debug_query = select(ClientAccess).where(
        ClientAccess.user_profile_id == str(user_id)
    )
    debug_result = await db.execute(debug_query)
    debug_access = debug_result.all()
    logger.info(
        f"🔍 Debug: Found {len(debug_access)} ClientAccess records for user {user_id}"
    )

    for access in debug_access:
        logger.info(
            f"🔍 Debug: ClientAccess {access.id}, client_account_id: {access.client_account_id}, "
            f"is_active: {access.is_active}"
        )

    # Check if ClientAccount records exist
    debug_client_query = select(ClientAccount).where(ClientAccount.id == DEMO_CLIENT_ID)
    debug_client_result = await db.execute(debug_client_query)
    debug_clients = debug_client_result.all()
    logger.info(f"🔍 Debug: Found {len(debug_clients)} demo ClientAccount records")

    for client in debug_clients:
        logger.info(
            f"🔍 Debug: ClientAccount {client.id}, name: {client.name}, is_active: {client.is_active}"
        )


def _is_demo_user(user: User) -> bool:
    """Check if user is a demo user based on email."""
    return user.email and user.email.endswith("@demo-corp.com")


async def _get_demo_client_from_db(db: AsyncSession) -> ClientsListResponse:
    """Get demo client from database for demo users."""
    demo_client_query = select(ClientAccount).where(
        and_(
            ClientAccount.id == DEMO_CLIENT_ID,
            ClientAccount.is_active,
        )
    )
    demo_result = await db.execute(demo_client_query)
    demo_client = demo_result.scalar_one_or_none()

    client_responses = []
    if demo_client:
        client_responses.append(
            ClientResponse(
                id=str(demo_client.id),
                name=demo_client.name,
                industry=demo_client.industry,
                company_size=demo_client.company_size,
                status="active",
            )
        )

    return ClientsListResponse(clients=client_responses)


@router.get("/clients", response_model=ClientsListResponse)
async def get_context_clients(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get list of clients accessible to the current user for context establishment.

    This endpoint is exempt from engagement context requirements and is specifically
    designed for initial context setup. It only requires authentication.
    """
    try:
        logger.info(
            f"🔍 Context Establishment: Getting clients for user {current_user.id}"
        )

        if not CLIENT_ACCOUNT_AVAILABLE:
            return _get_demo_clients()

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

        if is_platform_admin:
            return await _get_platform_admin_clients(db)
        else:
            return await _get_regular_user_clients(db, current_user)

    except Exception as e:
        logger.error(
            safe_log_format("Error in context establishment - get clients: {e}", e=e)
        )
        # Return demo data as fallback for demo user only
        if _is_demo_user(current_user):
            return _get_demo_clients()
        else:
            # Non-demo users get empty list if there's an error
            return ClientsListResponse(clients=[])
