"""
User profile management and cleanup functionality.

This module handles ensuring all users have proper profiles and cleaning up
invalid user data across the system.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.rbac import RoleType, UserProfile, UserRole, UserStatus
from .base import PlatformRequirements

logger = logging.getLogger(__name__)


class UserManagementService:
    """Manages user profiles and cleanup operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

    async def ensure_user_profiles(self):
        """Ensure all users have active profiles (required for login)"""
        logger.info("Ensuring all users have profiles...")

        # Find users without profiles
        query = text(
            """
        SELECT u.id, u.email, u.first_name, u.last_name
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE up.user_id IS NULL
        """
        )

        result = await self.db.execute(query)
        users_without_profiles = result.fetchall()

        for user_id, email, first_name, last_name in users_without_profiles:
            profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                approved_at=datetime.now(timezone.utc),
                registration_reason="Auto-created profile",
                organization="Unknown",
                role_description="User",
                requested_access_level="read_only",
            )
            self.db.add(profile)
            logger.warning(f"Created missing profile for user: {email}")

        if users_without_profiles:
            await self.db.commit()
            logger.info(f"Created profiles for {len(users_without_profiles)} users")

    async def cleanup_invalid_data(self):
        """Clean up any invalid demo data"""
        logger.info("Cleaning up invalid data...")

        # Remove any demo client admins (they should not exist)
        result = await self.db.execute(
            select(UserRole).where(
                UserRole.role_type == RoleType.CLIENT_ADMIN.value,
                UserRole.user_id.in_(select(User.id).where(User.email.like("%demo%"))),
            )
        )
        invalid_roles = result.scalars().all()

        for role in invalid_roles:
            await self.db.delete(role)
            logger.warning(f"Removed invalid demo client admin role: {role.id}")

        if invalid_roles:
            await self.db.commit()
            logger.info(f"Cleaned up {len(invalid_roles)} invalid demo roles")

    async def audit_user_integrity(self):
        """Audit user data integrity and report issues"""
        issues = []

        # Check for users without profiles
        query = text(
            """
        SELECT COUNT(*)
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE up.user_id IS NULL
        """
        )
        result = await self.db.execute(query)
        users_without_profiles = result.scalar()

        if users_without_profiles > 0:
            issues.append(f"{users_without_profiles} users without profiles")

        # Check for inactive users with active sessions
        query = text(
            """
        SELECT COUNT(*)
        FROM users u
        WHERE u.is_active = false
        AND EXISTS (SELECT 1 FROM user_sessions s WHERE s.user_id = u.id AND s.is_active = true)
        """
        )
        try:
            result = await self.db.execute(query)
            inactive_users_with_sessions = result.scalar()
            if inactive_users_with_sessions > 0:
                issues.append(
                    f"{inactive_users_with_sessions} inactive users with active sessions"
                )
        except Exception:
            # Sessions table might not exist
            pass

        # Log findings
        if issues:
            logger.warning(f"User integrity issues found: {', '.join(issues)}")
        else:
            logger.info("User data integrity check passed")

        return issues

    async def fix_orphaned_profiles(self):
        """Fix profiles that reference non-existent users"""
        logger.info("Checking for orphaned user profiles...")

        query = text(
            """
        SELECT up.user_id, up.id
        FROM user_profiles up
        LEFT JOIN users u ON up.user_id = u.id
        WHERE u.id IS NULL
        """
        )

        result = await self.db.execute(query)
        orphaned_profiles = result.fetchall()

        if orphaned_profiles:
            logger.warning(f"Found {len(orphaned_profiles)} orphaned user profiles")

            for user_id, profile_id in orphaned_profiles:
                await self.db.execute(
                    text("DELETE FROM user_profiles WHERE id = :profile_id"),
                    {"profile_id": profile_id},
                )
                logger.info(
                    f"Removed orphaned profile {profile_id} for non-existent user {user_id}"
                )

            await self.db.commit()
        else:
            logger.info("No orphaned user profiles found")
