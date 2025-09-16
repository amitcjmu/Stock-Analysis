"""
Demo data manager - orchestrates all demo data creation.

This module coordinates client, user, and RBAC setup for demo data.
"""

import logging
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientAccount, Engagement
from .client_setup import DemoClientSetup
from .user_setup import DemoUserSetup
from .rbac_setup import DemoRBACSetup
from ..base import PlatformRequirements

logger = logging.getLogger(__name__)


class DemoDataManager:
    """Manages demo data creation and maintenance"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

        # Initialize component managers
        self.client_setup = DemoClientSetup(db)
        self.user_setup = DemoUserSetup(db)
        self.rbac_setup = DemoRBACSetup(db)

    async def ensure_demo_data(self):
        """Create demo client, engagement, and users if they don't exist"""
        logger.info("Ensuring demo data exists...")

        # Check for demo client with fixed UUID
        client = await self.db.get(ClientAccount, self.requirements.DEMO_CLIENT_ID)

        if not client:
            client = await self.client_setup.create_demo_client()

        # Always use fixed client ID
        client_id = self.requirements.DEMO_CLIENT_ID

        # Check for demo engagement with fixed UUID
        engagement = await self.db.get(Engagement, self.requirements.DEMO_ENGAGEMENT_ID)

        if not engagement:
            engagement = await self.client_setup.create_demo_engagement(client_id)

        # Always use fixed engagement ID
        engagement_id = self.requirements.DEMO_ENGAGEMENT_ID

        await self.db.commit()

        # Create primary demo user with fixed UUID
        await self.user_setup.ensure_primary_demo_user(client_id, engagement_id)

        # Ensure RBAC access for primary user
        await self.rbac_setup.ensure_rbac_access(
            self.requirements.DEMO_USER_ID, client_id, engagement_id, "analyst"
        )

        # Create additional demo users with def0-def0-def0 pattern
        for user_data in self.requirements.DEMO_USERS:
            await self.user_setup.ensure_demo_user(user_data, client_id, engagement_id)

            # Get the user ID for RBAC setup
            from sqlalchemy import select
            from app.models import User

            result = await self.db.execute(
                select(User).where(User.email == user_data["email"])
            )
            user = result.scalar_one_or_none()

            if user:
                await self.rbac_setup.ensure_rbac_access(
                    user.id, client_id, engagement_id, user_data["role"].value.lower()
                )

        logger.info("Demo data setup completed successfully")

    async def auto_seed_demo_data(self):
        """Auto-seed demo data if environment requires it"""
        auto_seed = os.getenv("AUTO_SEED_DEMO_DATA", "false").lower() == "true"

        if auto_seed:
            logger.info("Auto-seeding demo data based on environment configuration")
            await self.ensure_demo_data()
        else:
            logger.debug("Auto-seed demo data is disabled")

    async def get_demo_data_summary(self) -> dict:
        """Get comprehensive summary of demo data status"""
        # Get client info
        client_info = await self.client_setup.get_demo_client_info()

        # Get user info
        users_info = await self.user_setup.get_demo_users_summary()

        # Get RBAC audit for primary user
        rbac_info = await self.rbac_setup.audit_rbac_permissions(
            self.requirements.DEMO_USER_ID
        )

        return {
            "client": client_info,
            "users": users_info,
            "rbac": rbac_info,
            "requirements": {
                "client_id": str(self.requirements.DEMO_CLIENT_ID),
                "engagement_id": str(self.requirements.DEMO_ENGAGEMENT_ID),
                "primary_user_id": str(self.requirements.DEMO_USER_ID),
                "configured_user_roles": len(self.requirements.DEMO_USERS),
            },
        }

    async def verify_demo_data_integrity(self) -> list:
        """Verify integrity of demo data and return list of issues"""
        issues = []

        # Check client exists
        if not await self.client_setup.verify_demo_client_exists():
            issues.append("Demo client missing or misconfigured")

        # Check engagement exists
        if not await self.client_setup.verify_demo_engagement_exists():
            issues.append("Demo engagement missing or misconfigured")

        # Check primary user
        from app.models import User

        primary_user = await self.db.get(User, self.requirements.DEMO_USER_ID)
        if not primary_user:
            issues.append("Primary demo user missing")
        elif not primary_user.is_active:
            issues.append("Primary demo user is inactive")

        # Check demo users
        users_summary = await self.user_setup.get_demo_users_summary()
        expected_users = len(self.requirements.DEMO_USERS) + 1  # +1 for primary user
        if users_summary["total_demo_users"] < expected_users:
            issues.append(
                f"Missing demo users: expected {expected_users}, found {users_summary['total_demo_users']}"
            )

        # Check RBAC for primary user
        rbac_audit = await self.rbac_setup.audit_rbac_permissions(
            self.requirements.DEMO_USER_ID
        )
        if rbac_audit["issues"]:
            issues.extend(
                [f"Primary user RBAC: {issue}" for issue in rbac_audit["issues"]]
            )

        if issues:
            logger.warning(f"Demo data integrity issues: {', '.join(issues)}")
        else:
            logger.info("Demo data integrity check passed")

        return issues

    async def repair_demo_data(self):
        """Attempt to repair demo data issues"""
        logger.info("Repairing demo data...")

        try:
            # Re-run full demo data setup
            await self.ensure_demo_data()

            # Clean up orphaned RBAC records
            await self.rbac_setup.cleanup_orphaned_rbac_records()

            logger.info("Demo data repair completed")

        except Exception as e:
            logger.error(f"Demo data repair failed: {e}")
            raise
