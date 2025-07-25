#!/usr/bin/env python3
"""
Test User Access Flow
Demonstrates how new users get client access in the platform
"""

import asyncio
import os

# Add the backend directory to Python path
import sys

from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import AsyncSessionLocal


async def test_user_access_flow():
    """Test the complete user access flow"""

    print("🔍 Testing User Access Flow")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        # 1. Show current client access records
        print("\n1. Current Client Access Records:")
        result = await db.execute(text("""
            SELECT ca.user_profile_id, ca.client_account_id, ca.access_level, ca.is_active,
                   cl.name as client_name, up.email
            FROM client_access ca
            JOIN client_accounts cl ON ca.client_account_id = cl.id
            LEFT JOIN user_profiles up ON ca.user_profile_id = up.user_id
            ORDER BY ca.created_at DESC
        """))

        for row in result:
            print(f"   User: {row.email or 'N/A'} ({row.user_profile_id})")
            print(f"   Client: {row.client_name} ({row.client_account_id})")
            print(f"   Access: {row.access_level}, Active: {row.is_active}")
            print()

        # 2. Show available clients
        print("\n2. Available Clients for Access:")
        result = await db.execute(text("""
            SELECT id, name, industry, is_active
            FROM client_accounts
            WHERE is_active = true
            ORDER BY name
            LIMIT 5
        """))

        for row in result:
            print(f"   {row.name} ({row.industry}) - ID: {row.id}")

        # 3. Show user profiles without client access
        print("\n3. Users Without Client Access:")
        result = await db.execute(text("""
            SELECT up.user_id, up.email, up.status
            FROM user_profiles up
            LEFT JOIN client_access ca ON up.user_id = ca.user_profile_id
            WHERE ca.user_profile_id IS NULL
        """))

        users_without_access = list(result)
        if users_without_access:
            for row in users_without_access:
                print(f"   {row.email} ({row.user_id}) - Status: {row.status}")
        else:
            print("   No users found without client access")

        # 4. Show the user access flow process
        print("\n4. User Access Flow Process:")
        print("""
   📝 New User Registration:
      1. User registers via /auth/register endpoint
      2. UserProfile created with status 'pending_approval'
      3. Admin receives notification in User Approvals dashboard

   👤 Admin Approval Process:
      1. Admin reviews user in /admin/users/access dashboard
      2. Admin approves user with specific access level
      3. ClientAccess record created linking user to client(s)
      4. User status changed to 'active'

   🔐 Access Control:
      1. User login triggers context resolution via /me endpoint
      2. System finds user's ClientAccess records
      3. Context includes accessible client/engagement IDs
      4. All API calls include context headers for multi-tenant security
        """)

        # 5. Show how to grant access to existing user
        print("\n5. How to Grant Client Access to Existing User:")
        print("""
   Method 1 - Via Admin Dashboard:
      1. Go to /admin/users/access
      2. Find user in Active Users tab
      3. Click "Edit Access"
      4. Grant access to specific clients

   Method 2 - Via Database (Emergency):
      INSERT INTO client_access (
          id, user_profile_id, client_account_id,
          access_level, granted_by, is_active
      ) VALUES (
          gen_random_uuid(),
          'USER_ID_HERE',
          'CLIENT_ID_HERE',
          'read_write',
          'ADMIN_USER_ID',
          true
      );
        """)

        # 6. Show RBAC dashboard locations
        print("\n6. RBAC Dashboard Locations:")
        print("""
   📊 Admin Dashboard: /admin/dashboard
      - Overview of users, clients, engagements
      - System health and statistics

   👥 User Management: /admin/users/access
      - Pending user approvals
      - Active user management
      - Client access management

   🏢 Client Management: /admin/clients
      - Create/edit/delete clients
      - Manage client business context
      - View client engagements

   📋 Engagement Management: /admin/engagements
      - Create/edit engagements
      - Link engagements to clients
      - Manage project contexts
        """)

if __name__ == "__main__":
    asyncio.run(test_user_access_flow())
