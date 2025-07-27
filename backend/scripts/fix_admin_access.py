#!/usr/bin/env python3
"""
Fix admin access for the platform admin user
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set database URL - use Docker network hostname
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"
)


async def fix_admin_access():
    """Fix admin access for chocka@gmail.com"""
    try:
        import uuid
        from datetime import datetime

        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models import User
        from app.models.rbac import UserRole

        async with AsyncSessionLocal() as db:
            # Find user by email
            result = await db.execute(
                select(User).where(User.email == "chocka@gmail.com")
            )
            user = result.scalar_one_or_none()

            if not user:
                print("❌ User chocka@gmail.com not found")
                return

            print(f"✅ Found user: {user.email} (ID: {user.id})")
            print(f"  User is_active: {user.is_active}")

            # Check for platform_admin role
            result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user.id, UserRole.role_type == "platform_admin"
                )
            )
            platform_role = result.scalar_one_or_none()

            if not platform_role:
                # Create platform_admin role
                platform_role = UserRole(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    role_type="platform_admin",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(platform_role)
                print("✅ Created platform_admin role")
            else:
                # Ensure it's active
                platform_role.is_active = True
                print("✅ Platform admin role already exists and is active")

            await db.commit()
            print("✅ Successfully fixed admin access for chocka@gmail.com")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_admin_access())
