"""
Seed core entities: Client Account, Engagement, Users, and RBAC setup.
Simplified version that works with the actual database schema.
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from seeding.constants import (  # noqa: E402
    BASE_TIMESTAMP,
    DEFAULT_PASSWORD,
    DEMO_CLIENT_ID,
    DEMO_COMPANY_NAME,
    DEMO_ENGAGEMENT_ID,
    USER_IDS,
    USERS,
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_client_account(db: AsyncSession) -> dict:
    """Create the demo client account using raw SQL."""
    print("Creating client account...")

    await db.execute(
        text(
            """
        INSERT INTO client_accounts (
            id, name, code, description, industry, company_size,
            contact_email, subscription_tier, is_active, created_at,
            metadata, agent_configuration, features_enabled
        ) VALUES (
            :id, :name, :code, :description, :industry, :company_size,
            :contact_email, :subscription_tier, :is_active, :created_at,
            :metadata, :agent_configuration, :features_enabled
        )
        ON CONFLICT (id) DO NOTHING
    """
        ),
        {
            "id": DEMO_CLIENT_ID,
            "name": DEMO_COMPANY_NAME,
            "code": "DEMO",
            "description": "Demo client account for testing and demonstration purposes",
            "industry": "Technology",
            "company_size": "1000-5000",
            "contact_email": "contact@democorp.com",
            "subscription_tier": "enterprise",
            "is_active": True,
            "created_at": BASE_TIMESTAMP,
            "metadata": json.dumps({"source": "demo_seeding", "created_by": "Agent 2"}),
            "agent_configuration": json.dumps(
                {"learning_enabled": True, "confidence_threshold": 0.8}
            ),
            "features_enabled": json.dumps(
                {
                    "auto_discovery": True,
                    "ai_insights": True,
                    "advanced_analytics": True,
                }
            ),
        },
    )

    await db.commit()
    print(f"✓ Created client account: {DEMO_COMPANY_NAME}")
    return {"id": DEMO_CLIENT_ID, "name": DEMO_COMPANY_NAME}


async def create_engagement(db: AsyncSession, client_id: uuid.UUID) -> dict:
    """Create the demo engagement using raw SQL."""
    print("Creating engagement...")

    await db.execute(
        text(
            """
        INSERT INTO engagements (
            id, client_account_id, name, description,
            engagement_type, status, created_at, metadata
        ) VALUES (
            :id, :client_account_id, :name, :description,
            :engagement_type, :status, :created_at, :metadata
        )
        ON CONFLICT (id) DO NOTHING
    """
        ),
        {
            "id": DEMO_ENGAGEMENT_ID,
            "client_account_id": client_id,
            "name": "Cloud Migration Assessment 2024",
            "description": "Comprehensive cloud migration assessment and planning for DemoCorp's infrastructure",
            "engagement_type": "cloud_migration",
            "status": "active",
            "created_at": BASE_TIMESTAMP,
            "metadata": json.dumps(
                {
                    "target_clouds": ["AWS", "Azure"],
                    "migration_strategies": ["Rehost", "Replatform", "Refactor"],
                    "timeline": "18 months",
                }
            ),
        },
    )

    await db.commit()
    print("✓ Created engagement: Cloud Migration Assessment 2024")
    return {"id": DEMO_ENGAGEMENT_ID, "name": "Cloud Migration Assessment 2024"}


async def create_users(db: AsyncSession) -> list[dict]:
    """Create demo users with different roles using raw SQL."""
    print("Creating users...")

    created_users = []
    password_hash = pwd_context.hash(DEFAULT_PASSWORD)

    for user_data in USERS:
        # Create User
        await db.execute(
            text(
                """
            INSERT INTO users (
                id, email, hashed_password, full_name, is_active,
                email_verified, created_at, default_client_account_id,
                default_engagement_id
            ) VALUES (
                :id, :email, :hashed_password, :full_name, :is_active,
                :email_verified, :created_at, :default_client_account_id,
                :default_engagement_id
            )
            ON CONFLICT (id) DO NOTHING
        """
            ),
            {
                "id": user_data["id"],
                "email": user_data["email"],
                "hashed_password": password_hash,
                "full_name": user_data["full_name"],
                "is_active": user_data["is_active"],
                "email_verified": user_data["is_verified"],
                "created_at": BASE_TIMESTAMP,
                "default_client_account_id": DEMO_CLIENT_ID,
                "default_engagement_id": DEMO_ENGAGEMENT_ID,
            },
        )

        # Create UserRole
        await db.execute(
            text(
                """
            INSERT INTO user_roles (
                id, user_id, client_account_id, engagement_id,
                role, permissions, is_active, created_at
            ) VALUES (
                :id, :user_id, :client_account_id, :engagement_id,
                :role, :permissions, :is_active, :created_at
            )
            ON CONFLICT (id) DO NOTHING
        """
            ),
            {
                "id": uuid.uuid4(),
                "user_id": user_data["id"],
                "client_account_id": DEMO_CLIENT_ID,
                "engagement_id": DEMO_ENGAGEMENT_ID,
                "role": user_data["role"],
                "permissions": json.dumps(get_role_permissions(user_data["role"])),
                "is_active": True,
                "created_at": BASE_TIMESTAMP,
            },
        )

        # Create ClientAccess (if the table exists)
        try:
            await db.execute(
                text(
                    """
                INSERT INTO client_access (
                    id, user_id, client_account_id, access_level,
                    permissions, granted_at, granted_by, is_active
                ) VALUES (
                    :id, :user_id, :client_account_id, :access_level,
                    :permissions, :granted_at, :granted_by, :is_active
                )
                ON CONFLICT (id) DO NOTHING
            """
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_data["id"],
                    "client_account_id": DEMO_CLIENT_ID,
                    "access_level": (
                        "ADMIN"
                        if user_data["role"] in ["ENGAGEMENT_MANAGER", "CLIENT_ADMIN"]
                        else "READ_WRITE"
                    ),
                    "permissions": json.dumps(
                        get_client_permissions(user_data["role"])
                    ),
                    "granted_at": BASE_TIMESTAMP,
                    "granted_by": USER_IDS["engagement_manager"],
                    "is_active": True,
                },
            )
        except Exception:
            # Table might not exist, continue
            pass

        created_users.append(user_data)
        print(f"✓ Created user: {user_data['email']} ({user_data['role']})")

    await db.commit()
    return created_users


def get_role_permissions(role_type: str) -> dict:
    """Get permissions based on role type."""
    base_permissions = {
        "can_create_clients": False,
        "can_manage_engagements": False,
        "can_import_data": False,
        "can_export_data": False,
        "can_view_analytics": True,
        "can_manage_users": False,
        "can_configure_agents": False,
        "can_access_admin_console": False,
    }

    if role_type == "ENGAGEMENT_MANAGER":
        base_permissions.update(
            {
                "can_manage_engagements": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_users": True,
                "can_configure_agents": True,
            }
        )
    elif role_type == "CLIENT_ADMIN":
        base_permissions.update(
            {
                "can_create_clients": True,
                "can_manage_engagements": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_users": True,
                "can_access_admin_console": True,
            }
        )
    elif role_type == "ANALYST":
        base_permissions.update(
            {
                "can_import_data": True,
                "can_export_data": True,
                "can_configure_agents": True,
            }
        )

    return base_permissions


def get_client_permissions(role_type: str) -> dict:
    """Get client-level permissions based on role type."""
    base_permissions = {
        "can_view_data": True,
        "can_import_data": False,
        "can_export_data": False,
        "can_manage_engagements": False,
        "can_configure_client_settings": False,
        "can_manage_client_users": False,
    }

    if role_type in ["ENGAGEMENT_MANAGER", "CLIENT_ADMIN"]:
        base_permissions.update(
            {
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_engagements": True,
                "can_configure_client_settings": True,
                "can_manage_client_users": True,
            }
        )
    elif role_type == "ANALYST":
        base_permissions.update({"can_import_data": True, "can_export_data": True})

    return base_permissions


async def main():
    """Main seeding function."""
    print("\n=== Seeding Core Entities (Simplified) ===\n")

    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            result = await db.execute(
                text("SELECT id FROM client_accounts WHERE id = :id"),
                {"id": DEMO_CLIENT_ID},
            )
            if result.first():
                print("⚠️  Core entities already seeded. Skipping...")
                return

            # Create entities
            client = await create_client_account(db)
            engagement = await create_engagement(db, client["id"])
            users = await create_users(db)

            print("\n✅ Successfully seeded core entities:")
            print(f"   - 1 Client Account: {client['name']}")
            print(f"   - 1 Engagement: {engagement['name']}")
            print(f"   - {len(users)} Users with RBAC setup")

        except Exception as e:
            print(f"\n❌ Error seeding core entities: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
