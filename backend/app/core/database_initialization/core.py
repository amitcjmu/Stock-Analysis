"""
Core database initialization orchestrator.

This module contains the main DatabaseInitializer class that coordinates
all database initialization activities.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .base import PlatformRequirements
from .platform_admin import PlatformAdminManager
from .demo_data import DemoDataManager
from .user_management import UserManagementService
from .assessment_setup import AssessmentSetupService

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles database initialization with platform requirements"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

        # Initialize component managers
        self.platform_admin = PlatformAdminManager(db)
        self.demo_data = DemoDataManager(db)
        self.user_management = UserManagementService(db)
        self.assessment_setup = AssessmentSetupService(db)

    async def initialize(self):
        """Run complete initialization process"""
        logger.info("Starting database initialization...")

        try:
            # Step 1: Verify assessment flow tables exist
            await self.assessment_setup.verify_assessment_tables()

            # Step 2: Ensure platform admin exists
            await self.platform_admin.ensure_platform_admin()

            # Step 3: Create demo data if needed
            await self.demo_data.ensure_demo_data()

            # Step 4: Initialize assessment standards for existing engagements
            try:
                await self.assessment_setup.ensure_engagement_assessment_standards()
            except Exception as e:
                logger.error(f"Failed to ensure engagement assessment standards: {e}")
                logger.warning(
                    "Continuing with database initialization without assessment standards"
                )

            # Step 5: Verify all users have profiles
            await self.user_management.ensure_user_profiles()

            # Step 6: Clean up invalid data
            await self.user_management.cleanup_invalid_data()

            # Step 7: Auto-seed demo data if needed
            await self.demo_data.auto_seed_demo_data()

            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def run_health_check(self):
        """Run comprehensive health check on database initialization"""
        logger.info("Running database initialization health check...")

        issues = []

        try:
            # Check platform admin exists
            from sqlalchemy import select
            from app.models import User

            result = await self.db.execute(
                select(User).where(User.email == self.requirements.PLATFORM_ADMIN_EMAIL)
            )
            admin = result.scalar_one_or_none()

            if not admin:
                issues.append("Platform admin does not exist")
            elif not admin.is_admin or not admin.is_active:
                issues.append("Platform admin is not properly configured")

            # Check demo data integrity
            from app.models import ClientAccount, Engagement

            demo_client = await self.db.get(
                ClientAccount, self.requirements.DEMO_CLIENT_ID
            )
            if not demo_client:
                issues.append("Demo client does not exist")

            demo_engagement = await self.db.get(
                Engagement, self.requirements.DEMO_ENGAGEMENT_ID
            )
            if not demo_engagement:
                issues.append("Demo engagement does not exist")

            # Check user profiles
            user_issues = await self.user_management.audit_user_integrity()
            issues.extend(user_issues)

            # Check assessment data if available
            assessment_issues = (
                await self.assessment_setup.audit_assessment_data_integrity()
            )
            issues.extend(assessment_issues)

            if issues:
                logger.warning(
                    f"Database initialization health check found issues: {', '.join(issues)}"
                )
            else:
                logger.info("Database initialization health check passed")

            return issues

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return [f"Health check error: {str(e)}"]

    async def repair_issues(self):
        """Attempt to repair common database initialization issues"""
        logger.info("Attempting to repair database initialization issues...")

        try:
            # Re-run initialization to fix most issues
            await self.initialize()

            # Fix orphaned data
            await self.user_management.fix_orphaned_profiles()
            await self.assessment_setup.cleanup_orphaned_assessment_data()

            logger.info("Database repair completed")

        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            raise
