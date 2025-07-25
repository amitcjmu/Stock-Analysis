#!/usr/bin/env python3
"""
Check all roles for chocka@gmail.com
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import User, UserRole
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_user_roles():
    """Check all roles for chocka@gmail.com"""

    async with AsyncSessionLocal() as db:
        try:
            # Find the user
            user_result = await db.execute(
                select(User).where(User.email == "chocka@gmail.com")
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.error("User chocka@gmail.com not found!")
                return

            logger.info(f"Found user: {user.email} (ID: {user.id})")

            # Get ALL roles for this user
            roles_result = await db.execute(
                select(UserRole)
                .where(UserRole.user_id == user.id)
                .order_by(UserRole.created_at)
            )
            all_roles = roles_result.scalars().all()

            logger.info(f"\nTotal roles found: {len(all_roles)}")
            logger.info("=" * 60)

            for i, role in enumerate(all_roles, 1):
                logger.info(f"\nRole {i}:")
                logger.info(f"  ID: {role.id}")
                logger.info(f"  Type: {role.role_type}")
                logger.info(f"  Name: {role.role_name}")
                logger.info(f"  Active: {role.is_active}")
                logger.info(f"  Scope: {role.scope_type}")
                logger.info(f"  Created: {role.created_at}")
                logger.info(f"  Updated: {role.updated_at}")
                logger.info(f"  Description: {role.description}")

            # Show which role would be selected by the current query logic
            logger.info("\n" + "=" * 60)
            logger.info("Current query logic (.limit(1)) would select:")

            # Simulate the exact query from user_service.py
            logger.info(f"\nChecking with user_id as string: {str(user.id)}")
            logger.info(f"Checking with UserRole.is_active is True")

            limited_result = await db.execute(
                select(UserRole)
                .where(
                    and_(UserRole.user_id == str(user.id), UserRole.is_active is True)
                )
                .limit(1)
            )
            limited_role = limited_result.scalar_one_or_none()

            # Also try without string conversion
            logger.info(f"\nAlso checking without string conversion...")
            direct_result = await db.execute(
                select(UserRole)
                .where(and_(UserRole.user_id == user.id, UserRole.is_active == True))
                .limit(1)
            )
            direct_role = direct_result.scalar_one_or_none()

            if direct_role and not limited_role:
                logger.warning(
                    "⚠️  TYPE MISMATCH ISSUE: Role found without string conversion but not with string conversion!"
                )

            if limited_role:
                logger.info(f"  Role Type: {limited_role.role_type}")
                logger.info(
                    f"  This explains why the user is seen as: {'admin' if limited_role.role_type == 'platform_admin' else limited_role.role_type}"
                )
            else:
                logger.info("  No active role found!")

        except Exception as e:
            logger.error(f"Error checking roles: {e}")


async def main():
    """Main function"""
    logger.info("🔍 Checking roles for chocka@gmail.com...")
    await check_user_roles()


if __name__ == "__main__":
    asyncio.run(main())
