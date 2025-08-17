#!/usr/bin/env python3
"""
Script to check admin access and debug authentication issues
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# flake8: noqa: E402
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.models.user_role import UserRole
from app.services.rbac_service import create_rbac_service


async def check_admin_access():
    """Check admin access for all users"""
    async with AsyncSessionLocal() as db:
        # Get all users
        users = await db.execute(select(User))
        users = users.scalars().all()

        print("=== USERS IN DATABASE ===")
        for user in users:
            print(f"\nUser: {user.email}")
            print(f"  ID: {user.id}")
            print(f"  Role: {user.role}")
            print(f"  Active: {user.is_active}")
            print(f"  Approved: {user.is_approved}")

            # Check if platform admin
            platform_admin = await db.execute(
                select(PlatformAdmin).where(PlatformAdmin.user_id == user.id)
            )
            platform_admin = platform_admin.scalar_one_or_none()
            print(f"  Platform Admin: {platform_admin is not None}")
            if platform_admin:
                print(f"    Super Admin: {platform_admin.is_super_admin}")

            # Check user roles
            roles = await db.execute(
                select(UserRole).where(UserRole.user_id == user.id)
            )
            roles = roles.scalars().all()
            if roles:
                print("  User Roles:")
                for role in roles:
                    print(f"    - {role.role} (Client: {role.client_account_id})")

            # Check RBAC access
            rbac_service = create_rbac_service(db)
            admin_access = await rbac_service.validate_user_access(
                user_id=str(user.id), resource_type="admin_console", action="read"
            )
            print(f"  RBAC Admin Access: {admin_access['has_access']}")
            if not admin_access["has_access"]:
                print(f"    Reason: {admin_access.get('reason', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(check_admin_access())
