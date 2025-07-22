#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.scripts.seed_sixr_analysis_demo import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with demo data."""
    try:
        async with AsyncSessionLocal() as db:
            await seed_demo_data(db)
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())