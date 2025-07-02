#!/usr/bin/env python3
"""
Test platform admin login.
"""
import asyncio
import os
import sys
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User
from app.models.rbac import UserProfile


async def test_login(email: str, password: str):
    """Test user login"""
    print(f"\n🔐 Testing login for: {email}")
    
    async with AsyncSessionLocal() as session:
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found!")
            return False
        
        print(f"✅ User found: {user.email}")
        
        # Check if user is active
        if not user.is_active or not user.is_verified:
            print("❌ Account not activated!")
            return False
        
        print("✅ Account is active and verified")
        
        # Get user profile
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile or profile.status != "active":
            print("❌ Account not approved!")
            return False
        
        print("✅ Account is approved")
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.password_hash:
            if user.password_hash == password_hash:
                print("✅ Password is correct!")
                print(f"\n🎉 Login successful for {email}!")
                print(f"   User ID: {user.id}")
                print(f"   Name: {user.first_name} {user.last_name}")
                return True
            else:
                print("❌ Invalid password!")
                print(f"   Expected: {user.password_hash[:20]}...")
                print(f"   Got: {password_hash[:20]}...")
                return False
        else:
            print("⚠️ User has no password hash set")
            return False


async def test_demo_login(email: str, password: str):
    """Test demo user login"""
    print(f"\n🔐 Testing demo login for: {email}")
    
    async with AsyncSessionLocal() as session:
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Demo user not found!")
            return False
        
        print(f"✅ Demo user found: {user.email}")
        print(f"   Default client: {user.default_client_id}")
        print(f"   Default engagement: {user.default_engagement_id}")
        
        return await test_login(email, password)


async def main():
    """Main test process"""
    print("="*60)
    print("🧪 LOGIN TESTING")
    print("="*60)
    
    try:
        # Test platform admin
        await test_login("chocka@gmail.com", "Password123!")
        
        # Test demo users
        demo_users = [
            ("manager@demo-corp.com", "Demo123!"),
            ("analyst@demo-corp.com", "Demo123!"),
            ("viewer@demo-corp.com", "Demo123!")
        ]
        
        print("\n" + "="*60)
        print("🧪 DEMO USER TESTING")
        print("="*60)
        
        for email, password in demo_users:
            await test_demo_login(email, password)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())