#!/usr/bin/env python3
"""
Check the actual User table structure
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set database URL - use Docker network hostname
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"


async def check_user_structure():
    """Check the User table structure"""
    try:
        from sqlalchemy import select, text
        from app.core.database import AsyncSessionLocal
        from app.models import User
        from app.models.rbac import UserRole

        async with AsyncSessionLocal() as db:
            # Check User table structure
            result = await db.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'"
                )
            )
            columns = result.fetchall()

            print("=== USER TABLE COLUMNS ===")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")

            # Check if chocka@gmail.com exists
            result = await db.execute(
                select(User).where(User.email == "chocka@gmail.com")
            )
            user = result.scalar_one_or_none()

            if user:
                print(f"\n=== USER DETAILS ===")
                print(f"  ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Is Active: {user.is_active}")
                print(f"  Is Verified: {user.is_verified}")

            # Check UserRole entries
            print(f"\n=== USER ROLES ===")
            result = await db.execute(
                select(UserRole).where(UserRole.user_id == user.id)
            )
            roles = result.scalars().all()

            for role in roles:
                print(f"  Role: {role.role_type}, Active: {role.is_active}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_user_structure())
