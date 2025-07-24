#!/usr/bin/env python3
"""
Test automatic RBAC mapping during user creation.
This verifies that when users are created with default_client_id and default_engagement_id,
the appropriate ClientAccess and EngagementAccess records are automatically created.
"""

import asyncio
import json
from datetime import datetime

from app.core.seed_data_config import DemoDataConfig

# Import models and services
from app.models import ClientAccount, Engagement, User
from app.models.rbac import AccessLevel, ClientAccess, EngagementAccess
from app.services.rbac_service import RBACService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def test_rbac_auto_mapping():
    """Test the automatic RBAC mapping functionality"""

    # Database connection
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/migration_db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        print("🔍 Testing Automatic RBAC Mapping...")
        print("=" * 60)

        # Step 1: Find demo client and engagement
        print("\n1️⃣ Finding demo client and engagement...")

        # Find demo client
        from sqlalchemy import String, cast

        client_result = await db.execute(
            select(ClientAccount).where(
                cast(ClientAccount.id, String).like("%def0-def0-def0%")
            )
        )
        demo_client = client_result.scalar_one_or_none()

        if not demo_client:
            print("❌ No demo client found! Run database initialization first.")
            return

        print(f"✅ Found demo client: {demo_client.name} ({demo_client.id})")

        # Find demo engagement
        engagement_result = await db.execute(
            select(Engagement).where(
                Engagement.client_account_id == demo_client.id,
                cast(Engagement.id, String).like("%def0-def0-def0%"),
            )
        )
        demo_engagement = engagement_result.scalar_one_or_none()

        if not demo_engagement:
            print("❌ No demo engagement found! Run database initialization first.")
            return

        print(
            f"✅ Found demo engagement: {demo_engagement.name} ({demo_engagement.id})"
        )

        # Step 2: Create a test user through RBAC service
        print("\n2️⃣ Creating test user with default IDs...")

        rbac_service = RBACService(db)
        test_user_id = str(DemoDataConfig.create_demo_uuid())
        test_email = (
            f"test_rbac_{datetime.now().strftime('%Y%m%d_%H%M%S')}@demo-corp.com"
        )

        user_data = {
            "user_id": test_user_id,
            "email": test_email,
            "full_name": "Test RBAC User",
            "organization": "Demo Corporation",
            "role_description": "Test Analyst",
            "registration_reason": "Testing automatic RBAC mapping",
            "requested_access_level": AccessLevel.READ_WRITE,
            "default_client_id": str(demo_client.id),
            "default_engagement_id": str(demo_engagement.id),
        }

        print(f"📧 Creating user: {test_email}")
        print(f"🏢 Default Client ID: {demo_client.id}")
        print(f"📋 Default Engagement ID: {demo_engagement.id}")

        # Register user (creates pending RBAC mappings)
        result = await rbac_service.register_user_request(user_data)

        if result["status"] != "success":
            print(f"❌ User registration failed: {result['message']}")
            return

        print("✅ User registered successfully (pending approval)")

        # Step 3: Verify pending RBAC mappings were created
        print("\n3️⃣ Verifying pending RBAC mappings...")

        # Check for pending ClientAccess
        client_access_result = await db.execute(
            select(ClientAccess).where(
                ClientAccess.user_profile_id == test_user_id,
                ClientAccess.client_account_id == demo_client.id,
            )
        )
        pending_client_access = client_access_result.scalar_one_or_none()

        if pending_client_access:
            print("✅ Pending ClientAccess created:")
            print(f"   - Access Level: {pending_client_access.access_level}")
            print(f"   - Is Active: {pending_client_access.is_active}")
            print(f"   - Notes: {pending_client_access.notes}")
        else:
            print("❌ No pending ClientAccess found!")

        # Check for pending EngagementAccess
        engagement_access_result = await db.execute(
            select(EngagementAccess).where(
                EngagementAccess.user_profile_id == test_user_id,
                EngagementAccess.engagement_id == demo_engagement.id,
            )
        )
        pending_engagement_access = engagement_access_result.scalar_one_or_none()

        if pending_engagement_access:
            print("✅ Pending EngagementAccess created:")
            print(f"   - Access Level: {pending_engagement_access.access_level}")
            print(f"   - Engagement Role: {pending_engagement_access.engagement_role}")
            print(f"   - Is Active: {pending_engagement_access.is_active}")
        else:
            print("❌ No pending EngagementAccess found!")

        # Step 4: Approve the user (should activate RBAC mappings)
        print("\n4️⃣ Approving user (should activate RBAC mappings)...")

        # Get platform admin ID to use as approver
        admin_result = await db.execute(
            select(User).where(User.email == "chocka@gmail.com")
        )
        admin = admin_result.scalar_one_or_none()

        if not admin:
            print("❌ Platform admin not found!")
            return

        approval_result = await rbac_service.approve_user(
            user_id=test_user_id,
            approved_by=str(admin.id),
            approval_data={
                "access_level": AccessLevel.READ_WRITE,
                "client_access": [],  # No additional access, should use defaults
            },
        )

        if approval_result["status"] != "success":
            print(f"❌ User approval failed: {approval_result['message']}")
            return

        print("✅ User approved successfully")

        # Step 5: Verify RBAC mappings are now active
        print("\n5️⃣ Verifying RBAC mappings are now active...")

        # Re-check ClientAccess
        await db.refresh(pending_client_access)
        if pending_client_access.is_active:
            print("✅ ClientAccess is now active!")
            print(f"   - Granted by: {pending_client_access.granted_by}")
            print(
                f"   - Permissions: {json.dumps(pending_client_access.permissions, indent=2)}"
            )
        else:
            print("❌ ClientAccess is still not active!")

        # Re-check EngagementAccess
        await db.refresh(pending_engagement_access)
        if pending_engagement_access.is_active:
            print("✅ EngagementAccess is now active!")
            print(f"   - Granted by: {pending_engagement_access.granted_by}")
            print(
                f"   - Permissions: {json.dumps(pending_engagement_access.permissions, indent=2)}"
            )
        else:
            print("❌ EngagementAccess is still not active!")

        # Step 6: Test admin direct user creation
        print("\n6️⃣ Testing admin direct user creation with auto RBAC...")

        admin_test_user_id = str(DemoDataConfig.create_demo_uuid())
        admin_test_email = (
            f"admin_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@demo-corp.com"
        )

        admin_user_data = {
            "user_id": admin_test_user_id,
            "email": admin_test_email,
            "full_name": "Admin Created User",
            "password": "TestPassword123!",
            "organization": "Demo Corporation",
            "role_name": "Analyst",
            "role_description": "Admin created analyst",
            "access_level": "analyst",
            "default_client_id": str(demo_client.id),
            "default_engagement_id": str(demo_engagement.id),
            "is_active": True,
        }

        print(f"📧 Admin creating user: {admin_test_email}")

        admin_result = await rbac_service.admin_create_user(
            user_data=admin_user_data, created_by=str(admin.id)
        )

        if admin_result["status"] != "success":
            print(f"❌ Admin user creation failed: {admin_result['message']}")
        else:
            print("✅ Admin user created successfully")

            # Check RBAC mappings for admin-created user
            admin_client_access = await db.execute(
                select(ClientAccess).where(
                    ClientAccess.user_profile_id == admin_test_user_id,
                    ClientAccess.client_account_id == demo_client.id,
                )
            )
            admin_client_access = admin_client_access.scalar_one_or_none()

            admin_engagement_access = await db.execute(
                select(EngagementAccess).where(
                    EngagementAccess.user_profile_id == admin_test_user_id,
                    EngagementAccess.engagement_id == demo_engagement.id,
                )
            )
            admin_engagement_access = admin_engagement_access.scalar_one_or_none()

            if admin_client_access and admin_client_access.is_active:
                print("✅ ClientAccess auto-created and active for admin-created user")
            else:
                print("❌ ClientAccess not created for admin-created user")

            if admin_engagement_access and admin_engagement_access.is_active:
                print(
                    "✅ EngagementAccess auto-created and active for admin-created user"
                )
            else:
                print("❌ EngagementAccess not created for admin-created user")

        print("\n" + "=" * 60)
        print("✅ RBAC Auto-Mapping Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_rbac_auto_mapping())
