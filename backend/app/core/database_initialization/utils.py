"""
Database initialization utilities and helper functions.

This module contains utility functions used across the database initialization
process, including auto-seeding functionality.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def auto_seed_demo_data(db: AsyncSession) -> bool:
    """Auto-seed comprehensive demo data if needed"""
    logger.info("Checking if demo data seeding is needed...")

    try:
        # Import the auto seeder
        from app.core.auto_seed_demo_data import auto_seed_demo_data

        # Run auto-seeding
        seeded = await auto_seed_demo_data(db)

        if seeded:
            logger.info("✅ Demo data seeded successfully!")
        else:
            logger.info("Demo data already exists or seeding was skipped")

        return seeded

    except ImportError as e:
        logger.warning(f"Auto-seeder not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to auto-seed demo data: {e}")
        # Don't raise - this shouldn't block initialization
        return False


async def verify_database_schema(db: AsyncSession) -> list:
    """Verify that all required database schema elements exist"""
    from sqlalchemy import text

    logger.info("Verifying database schema...")

    missing_elements = []

    # Check for required tables
    required_tables = [
        "users",
        "user_profiles",
        "user_roles",
        "client_accounts",
        "engagements",
        "user_account_associations",
    ]

    for table in required_tables:
        try:
            result = await db.execute(
                text("SELECT to_regclass(:table_name)"), {"table_name": table}
            )
            if not result.scalar():
                missing_elements.append(f"table:{table}")
        except Exception as e:
            logger.warning(f"Could not verify table {table}: {e}")
            missing_elements.append(f"table:{table}")

    # Check for required indexes
    required_indexes = [
        ("users", "users_email_key"),
        ("user_profiles", "user_profiles_user_id_key"),
        ("engagements", "engagements_client_account_id_idx"),
    ]

    for table, index in required_indexes:
        try:
            result = await db.execute(
                text(
                    """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = :table_name AND indexname = :index_name
                """
                ),
                {"table_name": table, "index_name": index},
            )
            if not result.scalar():
                missing_elements.append(f"index:{index}")
        except Exception as e:
            logger.warning(f"Could not verify index {index}: {e}")
            missing_elements.append(f"index:{index}")

    if missing_elements:
        logger.warning(f"Missing schema elements: {', '.join(missing_elements)}")
    else:
        logger.info("Database schema verification passed")

    return missing_elements


async def cleanup_test_data(db: AsyncSession):
    """Clean up test data that might interfere with initialization"""
    from sqlalchemy import text

    logger.info("Cleaning up potential test data...")

    try:
        # Remove any users with test emails
        test_patterns = ["%test%", "%example%", "%localhost%"]

        for pattern in test_patterns:
            result = await db.execute(
                text(
                    "DELETE FROM users WHERE email LIKE :pattern AND is_admin = false"
                ),
                {"pattern": pattern},
            )
            if result.rowcount > 0:
                logger.info(
                    f"Removed {result.rowcount} test users with pattern {pattern}"
                )

        # Remove any demo clients with wrong IDs (keeping our fixed UUID)
        from .base import PlatformRequirements

        requirements = PlatformRequirements()

        result = await db.execute(
            text(
                """
            DELETE FROM client_accounts
            WHERE name LIKE '%demo%'
            AND id != :demo_client_id
            """
            ),
            {"demo_client_id": requirements.DEMO_CLIENT_ID},
        )

        if result.rowcount > 0:
            logger.info(f"Removed {result.rowcount} duplicate demo clients")

        await db.commit()

    except Exception as e:
        logger.warning(f"Error during test data cleanup: {e}")
        await db.rollback()


def get_initialization_summary() -> dict:
    """Get a summary of what database initialization will do"""
    return {
        "platform_admin": {
            "action": "Create or update platform administrator account",
            "email": "chocka@gmail.com (configurable via env)",
            "permissions": "Full platform access",
        },
        "demo_data": {
            "action": "Create demo client, engagement, and users",
            "client_id": "11111111-1111-1111-1111-111111111111",
            "engagement_id": "22222222-2222-2222-2222-222222222222",
            "users": "Primary demo user + 3 role-based users",
        },
        "user_profiles": {
            "action": "Ensure all users have active profiles for login",
            "scope": "All existing users without profiles",
        },
        "assessment_setup": {
            "action": "Verify assessment tables and initialize standards",
            "scope": "All active engagements",
        },
        "cleanup": {
            "action": "Remove invalid demo data and orphaned records",
            "scope": "Demo client admin roles, orphaned profiles",
        },
    }


def log_initialization_plan():
    """Log the initialization plan for transparency"""
    summary = get_initialization_summary()

    logger.info("Database Initialization Plan:")
    logger.info("=" * 50)

    for section, details in summary.items():
        logger.info(f"{section.upper()}: {details['action']}")
        for key, value in details.items():
            if key != "action":
                logger.info(f"  {key}: {value}")
        logger.info("")
