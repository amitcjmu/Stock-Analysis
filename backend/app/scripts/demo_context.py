"""Utility for retrieving fixed demo tenant context (client, engagement, user).

All scripts can import `get_demo_context` to obtain the UUIDs needed for
multi-tenant inserts.  Assumes `init_db.py` has already seeded the demo data.
"""

import uuid
from typing import Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Constants for the seeded demo data
DEMO_CLIENT_SLUG = "demo-corp"
DEMO_ENGAGEMENT_SLUG = "cloud-migration-2024"
# SECURITY: Only use demo user - no admin@democorp account
DEMO_EMAIL = "demo@democorp.com"

try:
    from app.models.client_account import ClientAccount, Engagement, User
except ImportError:  # During docs builds / static analysis
    ClientAccount = Engagement = User = object  # type: ignore[misc,assignment]


async def get_demo_context(session: AsyncSession) -> Dict[str, uuid.UUID]:
    """Return ``client_account_id``, ``engagement_id`` and ``user_id`` for demo data.

    Raises:
        RuntimeError: If the expected demo rows are not present.  Call the
            main ``init_db.py`` bootstrap first to create them.
    """

    # --- Client -----------------------------------------------------------
    result = await session.execute(
        select(ClientAccount.id).where(ClientAccount.slug == DEMO_CLIENT_SLUG)
    )
    client_account_id: uuid.UUID | None = result.scalar_one_or_none()
    if client_account_id is None:
        raise RuntimeError("Demo client account not found – run init_db.py first.")

    # --- Engagement -------------------------------------------------------
    result = await session.execute(
        select(Engagement.id).where(
            Engagement.slug == DEMO_ENGAGEMENT_SLUG,
            Engagement.client_account_id == client_account_id,
        )
    )
    engagement_id: uuid.UUID | None = result.scalar_one_or_none()
    if engagement_id is None:
        raise RuntimeError("Demo engagement not found – run init_db.py first.")

    # --- User -------------------------------------------------------------
    # SECURITY: Only use demo user - no admin@democorp fallback
    result = await session.execute(select(User.id).where(User.email == DEMO_EMAIL))
    user_id: uuid.UUID | None = result.scalar_one_or_none()
    if user_id is None:
        raise RuntimeError("Demo user not found – run init_db.py first.")

    return {
        "client_account_id": client_account_id,
        "engagement_id": engagement_id,
        "user_id": user_id,
    }
