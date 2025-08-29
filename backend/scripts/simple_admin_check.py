#!/usr/bin/env python3
"""
Simple script to check and fix admin access for chocka@gmail.com
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, update  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.client_account import User  # noqa: E402


async def check_and_fix_admin_access():
    """Check and fix admin access for chocka@gmail.com"""
    async with AsyncSessionLocal() as db:
        # Find the user
        result = await db.execute(select(User).where(User.email == "chocka@gmail.com"))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ User chocka@gmail.com not found in database")
            return

        print(f"✅ Found user: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Is Admin: {user.is_admin}")

        if not user.is_admin:
            print("🔧 User is not admin, fixing...")
            # Update the user to be admin
            await db.execute(
                update(User).where(User.id == user.id).values(is_admin=True)
            )
            await db.commit()
            print("✅ User is now admin!")
        else:
            print("✅ User already has admin privileges")

        # Also check if user is active
        if not user.is_active:
            print("🔧 User is not active, fixing...")
            await db.execute(
                update(User).where(User.id == user.id).values(is_active=True)
            )
            await db.commit()
            print("✅ User is now active!")


if __name__ == "__main__":
    asyncio.run(check_and_fix_admin_access())
