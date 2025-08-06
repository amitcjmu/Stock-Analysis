#!/usr/bin/env python3
"""
Fix admin role script
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path modification - noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.logging import get_logger  # noqa: E402
from app.models import User, UserProfile, UserRole  # noqa: E402

logger = get_logger(__name__)


async def fix_admin_role():
    """Fix admin role for chocka@gmail.com"""

    async with AsyncSessionLocal() as db:
        try:
            # Find the user
            user_result = await db.execute(
                select(User).where(User.email == "chocka@gmail.com")
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.error("Target user not found!")
                return False

            logger.info(f"Found user with ID: {user.id}")

            # Check current roles
            roles_result = await db.execute(
                select(UserRole).where(UserRole.user_id == user.id)
            )
            current_roles = roles_result.scalars().all()

            logger.info(f"Current roles: {[role.role_type for role in current_roles]}")

            # Check if platform_admin role exists
            has_platform_admin = any(
                role.role_type == "platform_admin" for role in current_roles
            )

            if has_platform_admin:
                logger.info("✅ User already has platform_admin role")
            else:
                # Remove any existing non-admin roles
                for role in current_roles:
                    if role.role_type != "platform_admin":
                        logger.info(f"Removing role: {role.role_type}")
                        await db.delete(role)

                # Add platform_admin role
                platform_admin_role = UserRole(
                    user_id=user.id,
                    role_type="platform_admin",
                    scope_type="global",
                    is_active=True,
                    description="Platform Administrator",
                )
                db.add(platform_admin_role)
                logger.info("✅ Added platform_admin role")

            # Check UserProfile status
            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()

            if profile:
                logger.info(f"UserProfile status: {profile.status}")
                if profile.status != "active":
                    profile.status = "active"
                    logger.info("✅ Updated UserProfile status to active")

            # Commit changes
            await db.commit()

            # Verify the changes
            roles_result = await db.execute(
                select(UserRole).where(UserRole.user_id == user.id)
            )
            final_roles = roles_result.scalars().all()

            logger.info(f"Final roles: {[role.role_type for role in final_roles]}")

            return True

        except Exception as e:
            logger.error(f"Error fixing admin role: {e}")
            await db.rollback()
            return False


async def main():
    """Main function"""
    logger.info("🔧 Fixing admin role for target user...")

    success = await fix_admin_role()

    if success:
        logger.info("✅ Admin role fixed successfully!")
        logger.info("Please log out and log back in for the changes to take effect.")
    else:
        logger.error("❌ Failed to fix admin role")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
