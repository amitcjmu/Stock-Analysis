"""
Main initialization logic for database seeding.
"""

import argparse
import asyncio
import os
import sys

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

try:
    from app.core.database import AsyncSessionLocal, init_db
    from sqlalchemy import select

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages and set up the database connection.")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

# Handle relative imports when running as script vs module
if __name__ == "__main__":
    # When running as script, import using absolute imports
    from base import DEMO_USER_ID, logger
    from migrations import check_mock_data_exists
    from schema import (
        create_mock_assets,
        create_mock_client_account,
        create_mock_engagement,
        create_mock_migration_waves,
        create_mock_sixr_analysis,
        create_mock_tags,
        create_mock_users,
    )
else:
    # When imported as module, use relative imports
    from .base import DEMO_USER_ID, logger
    from .migrations import check_mock_data_exists
    from .schema import (
        create_mock_assets,
        create_mock_client_account,
        create_mock_engagement,
        create_mock_migration_waves,
        create_mock_sixr_analysis,
        create_mock_tags,
        create_mock_users,
    )

# Import User model for fallback lookup
from app.models.client_account import User


async def initialize_mock_data(force: bool = False):
    """
    Initializes the database with mock data for the demo.
    Creates a client account, users, engagement, assets, tags, and analysis.
    """
    async with AsyncSessionLocal() as session:
        if not force and await check_mock_data_exists(session):
            logger.info("Mock data already exists. Skipping initialization.")
            return

        logger.info("--- Starting Mock Data Initialization ---")

        client_account_id = await create_mock_client_account(session)
        user_ids = await create_mock_users(session, client_account_id)
        engagement_id = await create_mock_engagement(
            session, client_account_id, user_ids
        )
        tag_ids = await create_mock_tags(session, client_account_id)

        demo_user_id = user_ids.get("demo@democorp.com")
        if not demo_user_id:
            logger.error("Could not find demo user ID after user creation.")
            # Fallback to a static ID if needed, though this indicates an issue
            demo_user_id_result = await session.execute(
                select(User.id).where(User.email == "demo@democorp.com")
            )
            demo_user_id = demo_user_id_result.scalar_one_or_none() or DEMO_USER_ID

        asset_ids = await create_mock_assets(
            session, client_account_id, engagement_id, demo_user_id, tag_ids
        )

        if asset_ids:
            # Pass correct UUID types
            await create_mock_sixr_analysis(
                session, client_account_id, engagement_id, demo_user_id, asset_ids
            )

        await create_mock_migration_waves(
            session, client_account_id, engagement_id, demo_user_id
        )

        logger.info("--- Mock Data Initialization Complete ---")


async def main():
    """Main function to run the initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize the database with mock data."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-creation of mock data if it already exists.",
    )
    args = parser.parse_args()

    try:
        await init_db()
        await initialize_mock_data(force=args.force)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if DEPENDENCIES_AVAILABLE:
        asyncio.run(main())
