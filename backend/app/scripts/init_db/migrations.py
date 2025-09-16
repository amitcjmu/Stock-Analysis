"""
Migration utilities for database initialization.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    # Try relative imports first (when used as module)
    # Create logger locally since we don't use it from base
    from app.core.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    # Fall back to absolute imports (when used as script)
    import logging

    logger = logging.getLogger(__name__)


async def check_mock_data_exists(session: AsyncSession) -> bool:
    """Checks if mock data has already been populated."""
    # Check for the demo client account by ID since is_mock column was removed
    result = await session.execute(
        text(
            "SELECT 1 FROM client_accounts WHERE id = '11111111-1111-1111-1111-111111111111' LIMIT 1"
        )
    )
    return result.scalar_one_or_none() is not None
