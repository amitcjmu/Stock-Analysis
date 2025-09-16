"""
Database Initialization Module

Ensures consistent setup of platform admin, user profiles, and demo data across database changes.

This module is designed to be idempotent and can be run multiple times safely.
It enforces the following requirements:
1. All users MUST have UserProfile records with status='active' to login
2. Platform admin account: chocka@gmail.com / Password123!
3. Demo UUIDs use pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX (DEFault/DEmo pattern)
4. NO demo client admin accounts (only platform admin can create client admins)
5. Demo users are tied to proper client/engagement context

Run this module manually when:
- Setting up a new database
- After major database schema changes
- When demo data needs to be reset
- If users report login issues ("Account not approved")

Usage:
    from app.core.database_initialization import initialize_database
    await initialize_database(db_session)
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Import all public components for backward compatibility
from .base import (
    PlatformRequirements,
    ASSESSMENT_MODELS_AVAILABLE,
    EngagementArchitectureStandard,
)
from .core import DatabaseInitializer
from .platform_admin import PlatformAdminManager
from .demo_data import DemoDataManager
from .user_management import UserManagementService
from .assessment_setup import AssessmentSetupService
from .utils import (
    auto_seed_demo_data,
    verify_database_schema,
    cleanup_test_data,
    get_initialization_summary,
    log_initialization_plan,
)

logger = logging.getLogger(__name__)

# Export all public components
__all__ = [
    "initialize_database",
    "DatabaseInitializer",
    "PlatformRequirements",
    "PlatformAdminManager",
    "DemoDataManager",
    "UserManagementService",
    "AssessmentSetupService",
    "auto_seed_demo_data",
    "verify_database_schema",
    "cleanup_test_data",
    "get_initialization_summary",
    "log_initialization_plan",
    "ASSESSMENT_MODELS_AVAILABLE",
    "EngagementArchitectureStandard",
]


async def initialize_database(db: AsyncSession):
    """Main entry point for database initialization"""
    initializer = DatabaseInitializer(db)
    await initializer.initialize()


# Make this available as a CLI command
if __name__ == "__main__":
    from app.core.database import AsyncSessionLocal

    async def main():
        """CLI entry point for database initialization"""
        log_initialization_plan()

        async with AsyncSessionLocal() as db:
            await initialize_database(db)
            logger.info("Database initialization completed via CLI")

    asyncio.run(main())
