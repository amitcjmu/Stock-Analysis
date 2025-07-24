"""
Seeding script that works with the actual database schema.
This version uses only fields that actually exist in the database.
"""

import asyncio
import json
import sys
import uuid
from datetime import timedelta
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from seeding.constants import (
    BASE_TIMESTAMP,
    DEFAULT_PASSWORD,
    DEMO_CLIENT_ID,
    DEMO_COMPANY_NAME,
    DEMO_ENGAGEMENT_ID,
    FLOWS,
    IMPORTS,
    USERS,
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_users(db: AsyncSession) -> list[dict]:
    """Seed users with actual schema fields."""
    print("\n👥 Seeding users...")

    created_users = []
    password_hash = pwd_context.hash(DEFAULT_PASSWORD)

    for user_data in USERS:
        try:
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
                    "permissions": json.dumps(
                        {
                            "can_import_data": user_data["role"] != "VIEWER",
                            "can_export_data": user_data["role"] != "VIEWER",
                            "can_manage_users": user_data["role"]
                            in ["ENGAGEMENT_MANAGER", "CLIENT_ADMIN"],
                            "can_view_analytics": True,
                        }
                    ),
                    "is_active": True,
                    "created_at": BASE_TIMESTAMP,
                },
            )

            created_users.append(user_data)
            print(f"  ✓ Created user: {user_data['email']} ({user_data['role']})")

        except Exception as e:
            print(f"  ⚠️  Error creating user {user_data['email']}: {str(e)}")

    await db.commit()
    return created_users


async def seed_discovery_flows(db: AsyncSession) -> list[dict]:
    """Seed discovery flows with actual schema fields."""
    print("\n🔄 Seeding discovery flows...")

    created_flows = []

    for i, flow_data in enumerate(FLOWS):
        try:
            flow_id = flow_data["id"]
            created_at = BASE_TIMESTAMP + timedelta(days=i * 7)

            # Map our constants to actual schema fields
            status_map = {
                "complete": "completed",
                "in_progress": "active",
                "failed": "failed",
            }

            await db.execute(
                text(
                    """
                INSERT INTO discovery_flows (
                    id, flow_id, flow_name, status, progress_percentage,
                    client_account_id, engagement_id, user_id,
                    created_at, assessment_ready, error_message,
                    data_import_completed, field_mapping_completed,
                    asset_inventory_completed
                ) VALUES (
                    :id, :flow_id, :flow_name, :status, :progress_percentage,
                    :client_account_id, :engagement_id, :user_id,
                    :created_at, :assessment_ready, :error_message,
                    :data_import_completed, :field_mapping_completed,
                    :asset_inventory_completed
                )
                ON CONFLICT (id) DO NOTHING
            """
                ),
                {
                    "id": flow_id,
                    "flow_id": flow_id,  # Using same ID for both
                    "flow_name": flow_data["name"],
                    "status": status_map.get(flow_data["state"], "active"),
                    "progress_percentage": flow_data["progress"] / 100.0,
                    "client_account_id": DEMO_CLIENT_ID,
                    "engagement_id": DEMO_ENGAGEMENT_ID,
                    "user_id": str(flow_data["created_by"]),
                    "created_at": created_at,
                    "assessment_ready": flow_data.get("assessment_ready", False),
                    "error_message": flow_data.get("error_message"),
                    "data_import_completed": flow_data["progress"] >= 20,
                    "field_mapping_completed": flow_data["progress"] >= 45,
                    "asset_inventory_completed": flow_data["progress"] >= 65,
                },
            )

            created_flows.append(
                {
                    "id": str(flow_id),
                    "name": flow_data["name"],
                    "status": status_map.get(flow_data["state"], "active"),
                    "progress": flow_data["progress"],
                }
            )

            print(
                f"  ✓ Created flow: {flow_data['name']} ({flow_data['state']}, {flow_data['progress']}%)"
            )

        except Exception as e:
            print(f"  ⚠️  Error creating flow {flow_data['name']}: {str(e)}")

    await db.commit()
    return created_flows


async def seed_data_imports(db: AsyncSession) -> list[dict]:
    """Seed data imports with actual schema fields."""
    print("\n📊 Seeding data imports...")

    created_imports = []

    for import_data in IMPORTS:
        try:
            created_at = BASE_TIMESTAMP + timedelta(
                hours=import_data.get("hour_offset", 0)
            )

            # Map status values
            status_map = {
                "completed": "completed",
                "processing": "in_progress",
                "failed": "failed",
            }

            await db.execute(
                text(
                    """
                INSERT INTO data_imports (
                    id, flow_id, client_account_id, engagement_id,
                    filename, status, total_rows, processed_rows,
                    failed_rows, created_at, created_by
                ) VALUES (
                    :id, :flow_id, :client_account_id, :engagement_id,
                    :filename, :status, :total_rows, :processed_rows,
                    :failed_rows, :created_at, :created_by
                )
                ON CONFLICT (id) DO NOTHING
            """
                ),
                {
                    "id": import_data["id"],
                    "flow_id": import_data["flow_id"],
                    "client_account_id": DEMO_CLIENT_ID,
                    "engagement_id": DEMO_ENGAGEMENT_ID,
                    "filename": import_data["filename"],
                    "status": status_map.get(import_data["status"], "pending"),
                    "total_rows": import_data["total_rows"],
                    "processed_rows": import_data["processed_rows"],
                    "failed_rows": import_data["failed_rows"],
                    "created_at": created_at,
                    "created_by": str(import_data["created_by"]),
                },
            )

            created_imports.append(
                {
                    "id": str(import_data["id"]),
                    "flow_id": str(import_data["flow_id"]),
                    "filename": import_data["filename"],
                    "type": import_data["import_type"],
                    "status": import_data["status"],
                    "rows": {
                        "total": import_data["total_rows"],
                        "processed": import_data["processed_rows"],
                        "failed": import_data["failed_rows"],
                    },
                }
            )

            print(
                f"  ✓ Created import: {import_data['filename']} ({import_data['status']})"
            )

        except Exception as e:
            print(f"  ⚠️  Error creating import {import_data['filename']}: {str(e)}")

    # Add hour offsets
    for i, import_data in enumerate(IMPORTS):
        import_data["hour_offset"] = i * 2

    await db.commit()
    return created_imports


async def generate_seeded_ids_json(
    users: list[dict], flows: list[dict], imports: list[dict]
):
    """Generate SEEDED_IDS.json for Agent 3."""
    seeded_data = {
        "client_account": {"id": str(DEMO_CLIENT_ID), "name": DEMO_COMPANY_NAME},
        "engagement": {
            "id": str(DEMO_ENGAGEMENT_ID),
            "name": "Cloud Migration Assessment 2024",
        },
        "users": [
            {"id": str(user["id"]), "email": user["email"], "role": user["role"]}
            for user in users
        ],
        "flows": flows,
        "imports": imports,
    }

    output_path = Path(__file__).parent / "SEEDED_IDS.json"
    with open(output_path, "w") as f:
        json.dump(seeded_data, f, indent=2)

    print("\n✅ Generated SEEDED_IDS.json")
    return output_path


async def main():
    """Main seeding function that works with actual schema."""
    print("\n" + "=" * 60)
    print("🌱 DATABASE SEEDING (ACTUAL SCHEMA VERSION)")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # Check if client exists
            result = await db.execute(
                text("SELECT name FROM client_accounts WHERE id = :id"),
                {"id": DEMO_CLIENT_ID},
            )
            client = result.first()

            if not client:
                print(
                    "\n⚠️  Client account not found. Please run 01_core_entities_simple.py first."
                )
                return

            print(f"\n✓ Using existing client: {client[0]}")

            # Check if engagement exists
            result = await db.execute(
                text("SELECT name FROM engagements WHERE id = :id"),
                {"id": DEMO_ENGAGEMENT_ID},
            )
            engagement = result.first()

            if engagement:
                print(f"✓ Using existing engagement: {engagement[0]}")
            else:
                # Create engagement
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
                """
                    ),
                    {
                        "id": DEMO_ENGAGEMENT_ID,
                        "client_account_id": DEMO_CLIENT_ID,
                        "name": "Cloud Migration Assessment 2024",
                        "description": "Comprehensive cloud migration assessment",
                        "engagement_type": "cloud_migration",
                        "status": "active",
                        "created_at": BASE_TIMESTAMP,
                        "metadata": json.dumps({"source": "demo_seeding"}),
                    },
                )
                await db.commit()
                print("✓ Created engagement: Cloud Migration Assessment 2024")

            # Seed data
            users = await seed_users(db)
            flows = await seed_discovery_flows(db)
            imports = await seed_data_imports(db)

            # Generate SEEDED_IDS.json
            json_path = await generate_seeded_ids_json(users, flows, imports)

            print("\n" + "=" * 60)
            print("✅ SEEDING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("\nSummary:")
            print(f"  - Users: {len(users)}")
            print(f"  - Discovery Flows: {len(flows)}")
            print(f"  - Data Imports: {len(imports)}")
            print(f"\n📁 SEEDED_IDS.json created at: {json_path}")

        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
