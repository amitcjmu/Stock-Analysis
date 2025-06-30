"""
Context-aware database session management
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.context import get_current_context
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_context_db():
    """
    Get database session with context automatically set.
    Sets PostgreSQL session variables for RLS.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get current context
            context = get_current_context()
            if context:
                # Set context in PostgreSQL session
                await session.execute(
                    text("SELECT set_tenant_context(:client_account_id, :engagement_id)"),
                    {
                        "client_account_id": context.client_account_id,
                        "engagement_id": context.engagement_id
                    }
                )
                await session.commit()
                
                logger.debug(
                    f"Set database context for client {context.client_account_id}"
                )
            
            yield session
            
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# FastAPI dependency
async def get_db():
    """FastAPI dependency for context-aware database session"""
    async with get_context_db() as session:
        yield session