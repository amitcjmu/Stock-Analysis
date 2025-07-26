#!/usr/bin/env python3
"""
Grant admin access to a user by email
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import os

os.environ[
    "DATABASE_URL"
] = "postgresql://postgres:password@localhost:5432/migration_db"


async def grant_admin_access(email: str):
    """Grant admin access to a user"""
    try:
        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models.user import User
        from app.models.platform_admin import PlatformAdmin
        from datetime import datetime
        import uuid

        async with AsyncSessionLocal() as db:
            # Find user by email
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                print(f"❌ User with email '{email}' not found")
                return

            print(f"✅ Found user: {user.email} (ID: {user.id})")

            # Update user role to admin
            user.role = "admin"
            user.is_active = True
            user.is_approved = True

            # Check if already a platform admin
            result = await db.execute(
                select(PlatformAdmin).where(PlatformAdmin.user_id == user.id)
            )
            platform_admin = result.scalar_one_or_none()

            if platform_admin:
                print(f"✅ User is already a platform admin")
                platform_admin.is_super_admin = True
            else:
                # Create platform admin entry
                platform_admin = PlatformAdmin(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    is_super_admin=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(platform_admin)
                print(f"✅ Created platform admin entry")

            await db.commit()
            print(f"✅ Successfully granted admin access to {email}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_admin_access.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    asyncio.run(grant_admin_access(email))
