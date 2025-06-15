#!/usr/bin/env python3
"""
Script to check user role and profile information.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.client_account import User
from app.models.rbac import UserProfile, UserRole

async def check_user_role():
    """Check user role and profile information."""
    async with AsyncSessionLocal() as db:
        try:
            # Get user
            user_query = select(User).where(User.email == 'chocka@gmail.com')
            result = await db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ User: {user.email}")
                print(f"   ID: {user.id}")
                
                # Get user profile
                profile_query = select(UserProfile).where(UserProfile.user_id == user.id)
                profile_result = await db.execute(profile_query)
                profile = profile_result.scalar_one_or_none()
                
                if profile:
                    print(f"📋 Profile:")
                    print(f"   Status: {profile.status}")
                    print(f"   Requested Access Level: {profile.requested_access_level}")
                    print(f"   Organization: {profile.organization}")
                else:
                    print("❌ No profile found")
                
                # Get user roles
                roles_query = select(UserRole).where(UserRole.user_id == user.id)
                roles_result = await db.execute(roles_query)
                roles = roles_result.scalars().all()
                
                if roles:
                    print(f"🔐 Roles:")
                    for role in roles:
                        print(f"   - {role.role_type} (active: {role.is_active})")
                else:
                    print("❌ No roles found")
                    
                    # If user has admin access level but no roles, create one
                    if profile and profile.requested_access_level == "admin":
                        print("🔧 Creating admin role for user...")
                        
                        admin_role = UserRole(
                            user_id=user.id,
                            role_type="platform_admin",
                            role_name="Platform Administrator",
                            description="Admin user with full platform access",
                            permissions={
                                "can_create_clients": True,
                                "can_manage_engagements": True,
                                "can_import_data": True,
                                "can_export_data": True,
                                "can_view_analytics": True,
                                "can_manage_users": True,
                                "can_configure_agents": True,
                                "can_access_admin_console": True
                            },
                            is_active=True,
                            assigned_by=user.id  # Self-assigned for now
                        )
                        
                        db.add(admin_role)
                        await db.commit()
                        print("✅ Admin role created successfully")
                    
            else:
                print("❌ User not found")
                
        except Exception as e:
            print(f"❌ Error checking user role: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_role()) 