#!/usr/bin/env python3
"""
Fix User Roles and Security Issues
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import and_, select, update

from app.core.database import AsyncSessionLocal
from app.models.client_account import User
from app.models.rbac import RoleType, UserProfile, UserRole


async def fix_user_roles_and_security():
    """Fix user roles and remove security vulnerabilities."""
    print("🔧 Starting User Roles and Security Fix...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all users and their profiles
            users_query = select(User, UserProfile).join(
                UserProfile, User.id == UserProfile.user_id
            ).order_by(User.email)
            
            result = await db.execute(users_query)
            users_with_profiles = result.all()
            
            print(f"📊 Found {len(users_with_profiles)} users with profiles")
            
            # Fix each user's roles and security
            for user, profile in users_with_profiles:
                print(f"\n👤 Processing user: {user.email}")
                
                # Determine correct role based on email and intended purpose
                if user.email == "chocka@gmail.com":
                    role_type = RoleType.PLATFORM_ADMIN
                    role_name = "Platform Administrator"
                    access_level = "super_admin"
                    print("   🔑 Setting as Platform Administrator")
                    
                # SECURITY: admin@democorp.com account removed - no longer created
                    
                elif user.email == "demo@democorp.com":
                    # SECURITY FIX: Demo user should be Analyst, not Admin
                    role_type = RoleType.ANALYST
                    role_name = "Demo Analyst"
                    access_level = "read_write"
                    print("   🔒 SECURITY FIX: Downgrading from admin to analyst")
                    
                elif user.email == "demo@aiforce.com":
                    role_type = RoleType.VIEWER
                    role_name = "Demo Viewer"
                    access_level = "read_only"
                    print("   👀 Setting as Demo Viewer")
                    
                else:
                    role_type = RoleType.ANALYST
                    role_name = "Analyst"
                    access_level = "read_write"
                    print("   📊 Setting as Analyst")
                
                # Update user profile with correct access level
                profile_update = update(UserProfile).where(
                    UserProfile.user_id == user.id
                ).values(
                    requested_access_level=access_level,
                    role_description=role_name,
                    status='active'
                )
                await db.execute(profile_update)
                print(f"   ✓ Updated profile: {access_level} / {role_name}")
                
                # Check if user role already exists
                existing_role_query = select(UserRole).where(
                    and_(
                        UserRole.user_id == user.id,
                        UserRole.is_active == True
                    )
                )
                existing_role_result = await db.execute(existing_role_query)
                existing_role = existing_role_result.scalar_one_or_none()
                
                if existing_role:
                    # Update existing role
                    role_update = update(UserRole).where(
                        UserRole.id == existing_role.id
                    ).values(
                        role_type=role_type,
                        role_name=role_name,
                        description=f"Updated role for {user.email}",
                        permissions=get_role_permissions(role_type),
                        updated_at=datetime.utcnow()
                    )
                    await db.execute(role_update)
                    print(f"   ✓ Updated existing user role: {role_type}")
                else:
                    # Create new user role
                    user_role = UserRole(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        role_type=role_type,
                        role_name=role_name,
                        description=f"Role for {user.email}",
                        permissions=get_role_permissions(role_type),
                        scope_type="global",
                        is_active=True,
                        assigned_by=user.id,
                        created_at=datetime.utcnow()
                    )
                    db.add(user_role)
                    print(f"   ✓ Created new user role: {role_type}")
            
            # Commit all changes
            await db.commit()
            print("\n✅ User roles and security fix completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error fixing user roles: {e}")
            await db.rollback()
            raise

def get_role_permissions(role_type: str) -> dict:
    """Get permissions for a specific role type."""
    permissions = {
        RoleType.PLATFORM_ADMIN: {
            "can_read_all_data": True,
            "can_write_all_data": True,
            "can_delete_data": True,
            "can_manage_users": True,
            "can_approve_users": True,
            "can_access_admin_console": True,
            "can_view_audit_logs": True,
            "can_manage_clients": True,
            "can_manage_engagements": True,
            "can_access_llm_usage": True
        },
        RoleType.ANALYST: {
            "can_read_data": True,
            "can_write_data": True,
            "can_delete_data": False,
            "can_run_analysis": True,
            "can_view_reports": True,
            "can_export_data": True
        },
        RoleType.VIEWER: {
            "can_read_data": True,
            "can_write_data": False,
            "can_delete_data": False,
            "can_view_reports": True,
            "can_export_data": True
        }
    }
    
    return permissions.get(role_type, permissions[RoleType.VIEWER])

if __name__ == "__main__":
    asyncio.run(fix_user_roles_and_security())
