#!/usr/bin/env python3
"""
Fix demo user profiles to enable login.
Creates UserProfile records with 'active' status for all demo users.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User
from app.models.rbac import UserProfile, UserStatus


async def create_active_profiles_for_demo_users():
    """Create active UserProfile records for all demo users"""
    print("🔧 Creating active profiles for demo users...")
    
    async with AsyncSessionLocal() as session:
        # Find all demo users (by email pattern)
        result = await session.execute(
            select(User).where(
                User.email.like('%demo%')
            )
        )
        demo_users = result.scalars().all()
        
        if not demo_users:
            print("❌ No demo users found!")
            return False
        
        print(f"\n📋 Found {len(demo_users)} demo users")
        
        created_count = 0
        updated_count = 0
        
        for user in demo_users:
            # Check if profile exists
            existing_profile = await session.get(UserProfile, user.id)
            
            if existing_profile:
                if existing_profile.status != UserStatus.ACTIVE:
                    # Update existing profile to active
                    existing_profile.status = UserStatus.ACTIVE
                    existing_profile.approved_at = datetime.now(timezone.utc)
                    print(f"   ✅ Updated profile for {user.email} to ACTIVE")
                    updated_count += 1
                else:
                    print(f"   ⚠️ Profile for {user.email} already active")
            else:
                # Create new active profile
                profile = UserProfile(
                    user_id=user.id,
                    status=UserStatus.ACTIVE,
                    approved_at=datetime.now(timezone.utc),
                    registration_reason="Demo account for testing",
                    organization="Demo Organization",
                    role_description="Demo user for platform testing",
                    requested_access_level="admin",
                    notification_preferences={"email": True, "slack": False}
                )
                session.add(profile)
                print(f"   ✅ Created active profile for {user.email}")
                created_count += 1
        
        await session.commit()
        
        print(f"\n📊 Summary:")
        print(f"   - Created: {created_count} new profiles")
        print(f"   - Updated: {updated_count} existing profiles")
        print(f"   - Total demo users: {len(demo_users)}")
        
        return True


async def verify_demo_logins():
    """Verify demo users can now login"""
    print("\n🔍 Verifying demo user profiles...")
    
    async with AsyncSessionLocal() as session:
        # Check specific demo users
        demo_emails = [
            "demo@democorp.com",
            "demo@demo.democorp.com",
            "admin@demo.techcorp.com",
            "analyst@demo.democorp.com"
        ]
        
        for email in demo_emails:
            # Get user
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar()
            
            if not user:
                continue
            
            # Get profile
            profile = await session.get(UserProfile, user.id)
            
            if profile and profile.status == UserStatus.ACTIVE:
                print(f"   ✅ {email} - Profile ACTIVE")
            elif profile:
                print(f"   ❌ {email} - Profile status: {profile.status}")
            else:
                print(f"   ❌ {email} - No profile found")


async def main():
    """Main entry point"""
    print("="*60)
    print("🔧 FIX DEMO USER PROFILES")
    print("="*60)
    
    try:
        # Create/update profiles
        success = await create_active_profiles_for_demo_users()
        
        if success:
            # Verify the fix
            await verify_demo_logins()
            
            print("\n✅ Demo user profiles fixed!")
            print("\n🔐 You can now login with:")
            print("   - demo@democorp.com (Demo123!)")
            print("   - demo@demo.democorp.com (Demo123!)")
            print("   - Any user with 'demo' in email (Demo123!)")
        else:
            print("\n❌ Failed to fix demo user profiles")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())