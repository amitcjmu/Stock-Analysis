"""
Main entry point for the discovery flow database seeding script.
"""

import asyncio
import logging
import os
import sys

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

try:
    # Test import to ensure dependencies are available
    from app.core.database import AsyncSessionLocal  # noqa: F401

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

from .database_operations import (
    drop_existing_tables,
    create_fresh_tables,
    verify_seeded_data,
)
from .data_seeder import seed_demo_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main function to execute the seeding process"""
    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ Required dependencies are not available")
        return False

    try:
        logger.info("🚀 Starting Discovery Flow Database Seeding Process...")

        # Step 1: Drop existing tables
        await drop_existing_tables()

        # Step 2: Create fresh tables
        await create_fresh_tables()

        # Step 3: Seed demo data
        await seed_demo_data()

        # Step 4: Verify seeded data
        verification_passed = await verify_seeded_data()

        if verification_passed:
            logger.info("🎉 Discovery Flow Database Seeding completed successfully!")
            return True
        else:
            logger.error("❌ Verification failed - seeding may be incomplete")
            return False

    except Exception as e:
        logger.error(f"❌ Seeding process failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
