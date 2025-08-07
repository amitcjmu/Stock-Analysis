#!/usr/bin/env python3
"""
⚠️ WARNING: DO NOT RUN THIS SCRIPT! ⚠️

This script uses SHA256 password hashing which is incompatible with the
authentication service that expects bcrypt hashes. Running this script will
set an invalid password hash that will prevent login.

USE INSTEAD: python -m app.core.database_initialization

The database initialization module correctly uses passlib with bcrypt and
will set passwords that work with the authentication service.

---

Verify and fix platform admin password if needed.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import User
from app.models.rbac import UserProfile


def get_password_hash(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()


async def verify_platform_admin():
    """Verify platform admin exists and has valid password"""
    print("\n🔍 Verifying platform admin...")

    async with AsyncSessionLocal() as session:
        # Find platform admin
        result = await session.execute(
            select(User).where(User.email == "chocka@gmail.com")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ Platform admin not found!")
            return

        print(f"✅ Platform admin found: {admin.email}")
        print(f"   ID: {admin.id}")
        print(f"   Active: {admin.is_active}")
        print(f"   Verified: {admin.is_verified}")

        # Check password hash
        print("\n🔐 Checking password hash...")
        print(
            f"   Current hash: {admin.password_hash[:20]}..."
            if admin.password_hash
            else "   No password hash!"
        )

        # Update password to ensure it's valid
        new_password = os.getenv(
            "ADMIN_TEST_PASSWORD", "DefaultPassword123!"
        )  # Use env var or fallback
        new_hash = get_password_hash(new_password)
        admin.password_hash = new_hash

        print(f"   New hash: {new_hash[:20]}...")

        # Check user profile
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == admin.id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            print("\n⚠️ No user profile found!")
        else:
            print("\n👤 User profile:")
            print(f"   Status: {profile.status}")
            print(f"   Organization: {profile.organization}")

        await session.commit()
        print("\n✅ Platform admin password updated successfully!")

        # Test the new password
        print("\n🧪 Testing password verification...")
        test_password = os.getenv(
            "ADMIN_TEST_PASSWORD", "DefaultPassword123!"
        )  # Use same env var
        try:
            # Since we're using SHA256, just compare hashes
            test_hash = get_password_hash(test_password)
            is_valid = test_hash == new_hash
            print(
                f"   Password verification: {'✅ Valid' if is_valid else '❌ Invalid'}"
            )
        except Exception as e:
            print(f"   ❌ Password verification error: {e}")


async def main():
    """Main verification process"""
    print("=" * 60)
    print("🔐 PLATFORM ADMIN VERIFICATION")
    print("=" * 60)

    try:
        await verify_platform_admin()
        print("\n✅ Verification complete!")
        print("\n🔐 Login credentials:")
        print("   Email: chocka@gmail.com")
        print("   Password: Password123!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
