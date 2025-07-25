#!/usr/bin/env python3
"""
Test data seeding script for consolidated schema
Creates realistic test data without any mock flags
"""

import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Initialize Faker
fake = Faker()

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/migration_db"
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Test tenant IDs
TEST_TENANT_1 = uuid.uuid4()
TEST_TENANT_2 = uuid.uuid4()

# Sample data
ASSET_TYPES = ["server", "application", "database", "network_device", "storage"]
SIXR_STRATEGIES = ["rehost", "replatform", "refactor", "repurchase", "retire", "retain"]
OS_TYPES = [
    "Windows Server 2019",
    "RHEL 8",
    "Ubuntu 20.04",
    "CentOS 7",
    "Amazon Linux 2",
]
DEPARTMENTS = ["Finance", "HR", "Engineering", "Sales", "Marketing", "Operations"]
DATACENTERS = ["DC-East-1", "DC-West-1", "DC-Central", "Cloud-AWS", "Cloud-Azure"]


class TestDataSeeder:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def seed_all(self):
        """Seed all test data"""
        async with self.async_session() as session:
            print("Starting test data seeding...\n")

            # Create test tenants
            await self._create_client_accounts(session)

            # Create users
            await self._create_users(session)

            # Create engagements
            await self._create_engagements(session)

            # Create master flows
            master_flows = await self._create_master_flows(session)

            # Create discovery data
            await self._create_discovery_data(session, master_flows)

            # Create assets
            await self._create_assets(session, master_flows)

            await session.commit()
            print("\n✅ Test data seeding completed!")

    async def _create_client_accounts(self, session: AsyncSession):
        """Create test client accounts"""
        print("Creating client accounts...")

        clients = [
            {
                "id": TEST_TENANT_1,
                "name": "Acme Corporation",
                "industry": "Technology",
                "contact_email": "admin@acme.com",
                "is_active": True,
            },
            {
                "id": TEST_TENANT_2,
                "name": "Global Enterprises",
                "industry": "Manufacturing",
                "contact_email": "admin@global.com",
                "is_active": True,
            },
        ]

        for client in clients:
            await session.execute(
                text(
                    """
                    INSERT INTO client_accounts (id, name, industry, contact_email, is_active)
                    VALUES (:id, :name, :industry, :email, :active)
                    ON CONFLICT (id) DO NOTHING
                """
                ),
                {
                    "id": client["id"],
                    "name": client["name"],
                    "industry": client["industry"],
                    "email": client["contact_email"],
                    "active": client["is_active"],
                },
            )

        print(f"✓ Created {len(clients)} client accounts")

    async def _create_users(self, session: AsyncSession):
        """Create test users"""
        print("Creating users...")

        users = []
        for i in range(5):
            user_id = uuid.uuid4()
            users.append(
                {
                    "id": user_id,
                    "email": f"user{i+1}@example.com",
                    "full_name": fake.name(),
                    "is_active": True,
                    "is_superuser": i == 0,  # First user is admin
                    "default_client_account_id": (
                        TEST_TENANT_1 if i < 3 else TEST_TENANT_2
                    ),
                    "default_engagement_id": None,  # Will be set after engagements created
                }
            )

            await session.execute(
                text(
                    """
                    INSERT INTO users (id, email, full_name, is_active, is_superuser,
                                     default_client_account_id, hashed_password)
                    VALUES (:id, :email, :name, :active, :super, :client_id, :password)
                    ON CONFLICT (email) DO NOTHING
                """
                ),
                {
                    "id": user_id,
                    "email": users[i]["email"],
                    "name": users[i]["full_name"],
                    "active": users[i]["is_active"],
                    "super": users[i]["is_superuser"],
                    "client_id": users[i]["default_client_account_id"],
                    "password": "hashed_password_here",  # In real scenario, properly hash
                },
            )

        print(f"✓ Created {len(users)} users")

    async def _create_engagements(self, session: AsyncSession):
        """Create test engagements"""
        print("Creating engagements...")

        engagements = []

        # 3 engagements for tenant 1
        for i in range(3):
            eng_id = uuid.uuid4()
            engagements.append(
                {
                    "id": eng_id,
                    "client_account_id": TEST_TENANT_1,
                    "name": f"Cloud Migration Phase {i+1}",
                    "description": f"Migration project phase {i+1} for Acme Corp",
                    "start_date": datetime.now() - timedelta(days=90 - i * 30),
                    "target_end_date": datetime.now() + timedelta(days=30 + i * 30),
                    "is_active": True,
                }
            )

        # 3 engagements for tenant 2
        for i in range(3):
            eng_id = uuid.uuid4()
            engagements.append(
                {
                    "id": eng_id,
                    "client_account_id": TEST_TENANT_2,
                    "name": f"Digital Transformation Wave {i+1}",
                    "description": f"Transformation wave {i+1} for Global Enterprises",
                    "start_date": datetime.now() - timedelta(days=60 - i * 20),
                    "target_end_date": datetime.now() + timedelta(days=60 + i * 30),
                    "is_active": True,
                }
            )

        for eng in engagements:
            await session.execute(
                text(
                    """
                    INSERT INTO engagements (id, client_account_id, name, description,
                                           start_date, target_end_date, is_active)
                    VALUES (:id, :client_id, :name, :desc, :start, :end, :active)
                    ON CONFLICT (id) DO NOTHING
                """
                ),
                {
                    "id": eng["id"],
                    "client_id": eng["client_account_id"],
                    "name": eng["name"],
                    "desc": eng["description"],
                    "start": eng["start_date"],
                    "end": eng["target_end_date"],
                    "active": eng["is_active"],
                },
            )

        print(f"✓ Created {len(engagements)} engagements")
        return engagements

    async def _create_master_flows(self, session: AsyncSession):
        """Create master flow orchestrators"""
        print("Creating master flows...")

        master_flows = []

        # Create 5 master flows
        for i in range(5):
            flow_id = uuid.uuid4()
            master_flows.append(
                {
                    "flow_id": flow_id,
                    "flow_type": "unified_discovery",
                    "master_state": {
                        "current_phase": "discovery",
                        "phases": ["discovery", "assessment", "planning", "execution"],
                        "created_at": datetime.now().isoformat(),
                    },
                    "metadata": {"version": "1.0", "created_by": "system"},
                }
            )

            await session.execute(
                text(
                    """
                    INSERT INTO crewai_flow_state_extensions (flow_id, flow_type, master_state, metadata)
                    VALUES (:id, :type, :state, :meta)
                    ON CONFLICT (flow_id) DO NOTHING
                """
                ),
                {
                    "id": flow_id,
                    "type": "unified_discovery",
                    "state": json.dumps(master_flows[i]["master_state"]),
                    "meta": json.dumps(master_flows[i]["metadata"]),
                },
            )

        print(f"✓ Created {len(master_flows)} master flows")
        return master_flows

    async def _create_discovery_data(self, session: AsyncSession, master_flows):
        """Create discovery phase data"""
        print("Creating discovery data...")

        # Get engagement IDs
        result = await session.execute(text("SELECT id FROM engagements LIMIT 6"))
        engagement_ids = [row[0] for row in result]

        # Create data imports
        imports_created = 0
        for i in range(10):
            import_id = uuid.uuid4()
            client_id = TEST_TENANT_1 if i < 5 else TEST_TENANT_2
            engagement_id = random.choice(
                engagement_ids[:3] if i < 5 else engagement_ids[3:]
            )
            master_flow_id = master_flows[i % len(master_flows)]["flow_id"]

            status = random.choice(
                ["completed", "processing", "completed", "completed"]
            )

            await session.execute(
                text(
                    """
                    INSERT INTO data_imports (
                        id, client_account_id, engagement_id, master_flow_id,
                        filename, file_size, mime_type, source_system,
                        status, total_records, processed_records, failed_records,
                        created_at
                    ) VALUES (
                        :id, :client_id, :eng_id, :master_id,
                        :filename, :size, :mime, :source,
                        :status, :total, :processed, :failed,
                        :created
                    )
                """
                ),
                {
                    "id": import_id,
                    "client_id": client_id,
                    "eng_id": engagement_id,
                    "master_id": master_flow_id,
                    "filename": f"{fake.word()}_servers_{i+1}.csv",
                    "size": random.randint(1024, 1024 * 1024 * 10),
                    "mime": "text/csv",
                    "source": random.choice(
                        ["servicenow", "cmdb_export", "manual_upload"]
                    ),
                    "status": status,
                    "total": random.randint(100, 1000),
                    "processed": random.randint(90, 1000),
                    "failed": random.randint(0, 10),
                    "created": datetime.now() - timedelta(days=random.randint(1, 30)),
                },
            )

            # Create discovery flow
            flow_id = uuid.uuid4()
            phases_completed = []
            if status == "completed":
                phases_completed = [
                    "data_validation",
                    "field_mapping",
                    "data_cleansing",
                    "asset_inventory",
                    "dependency_analysis",
                ]

            await session.execute(
                text(
                    """
                    INSERT INTO discovery_flows (
                        id, data_import_id, master_flow_id,
                        flow_name, status, current_phase, phases_completed,
                        data_validation_completed, field_mapping_completed,
                        data_cleansing_completed, asset_inventory_completed,
                        dependency_analysis_completed, tech_debt_assessment_completed,
                        progress_percentage, created_at
                    ) VALUES (
                        :id, :import_id, :master_id,
                        :name, :status, :phase, :phases,
                        :val_done, :map_done, :clean_done, :inv_done,
                        :dep_done, :tech_done, :progress, :created
                    )
                """
                ),
                {
                    "id": flow_id,
                    "import_id": import_id,
                    "master_id": master_flow_id,
                    "name": f"Discovery: {fake.word()}_servers_{i+1}.csv",
                    "status": status,
                    "phase": "completed" if status == "completed" else "field_mapping",
                    "phases": json.dumps(phases_completed),
                    "val_done": status == "completed",
                    "map_done": status == "completed",
                    "clean_done": status == "completed",
                    "inv_done": status == "completed",
                    "dep_done": status == "completed",
                    "tech_done": status == "completed",
                    "progress": (
                        100 if status == "completed" else random.randint(20, 80)
                    ),
                    "created": datetime.now() - timedelta(days=random.randint(1, 30)),
                },
            )

            # Create field mappings
            if status in ["completed", "processing"]:
                for j in range(random.randint(5, 15)):
                    mapping_id = uuid.uuid4()
                    await session.execute(
                        text(
                            """
                            INSERT INTO import_field_mappings (
                                id, data_import_id, client_account_id, master_flow_id,
                                source_field, target_field, match_type, confidence_score,
                                status, suggested_by, created_at
                            ) VALUES (
                                :id, :import_id, :client_id, :master_id,
                                :source, :target, :match, :confidence,
                                :status, :suggested, :created
                            )
                        """
                        ),
                        {
                            "id": mapping_id,
                            "import_id": import_id,
                            "client_id": client_id,
                            "master_id": master_flow_id,
                            "source": fake.word()
                            + "_"
                            + random.choice(["name", "id", "type", "status"]),
                            "target": random.choice(
                                ["hostname", "ip_address", "os_type", "department"]
                            ),
                            "match": random.choice(
                                ["exact", "fuzzy", "pattern", "custom"]
                            ),
                            "confidence": round(random.uniform(0.7, 1.0), 2),
                            "status": (
                                "approved" if status == "completed" else "suggested"
                            ),
                            "suggested": "ai_mapper",
                            "created": datetime.now()
                            - timedelta(days=random.randint(1, 30)),
                        },
                    )

            imports_created += 1

        print(f"✓ Created {imports_created} data imports with flows and mappings")

    async def _create_assets(self, session: AsyncSession, master_flows):
        """Create discovered assets"""
        print("Creating assets...")

        assets_created = 0

        # Get discovery flow IDs
        result = await session.execute(
            text(
                "SELECT id, master_flow_id FROM discovery_flows WHERE status = 'completed'"
            )
        )
        discovery_flows = [(row[0], row[1]) for row in result]

        for flow_id, master_id in discovery_flows:
            # Create 3-8 assets per completed flow
            for i in range(random.randint(3, 8)):
                asset_id = uuid.uuid4()
                asset_type = random.choice(ASSET_TYPES)

                # Build asset data based on type
                asset_data = {
                    "id": asset_id,
                    "discovery_flow_id": flow_id,
                    "master_flow_id": master_id,
                    "asset_type": asset_type,
                    "status": "discovered",
                    "discovery_source": "automated_discovery",
                    "hostname": fake.slug()
                    + "-"
                    + random.choice(["app", "db", "web", "api"]),
                    "ip_address": fake.ipv4_private(),
                    "environment": random.choice(
                        ["production", "staging", "development", "qa"]
                    ),
                    "business_criticality": random.choice(
                        ["critical", "high", "medium", "low"]
                    ),
                    "created_at": datetime.now()
                    - timedelta(days=random.randint(1, 20)),
                }

                # Add type-specific fields
                if asset_type == "server":
                    asset_data.update(
                        {
                            "operating_system": random.choice(OS_TYPES),
                            "os_version": f"{random.randint(1, 10)}.{random.randint(0, 9)}",
                            "cpu_cores": random.choice([2, 4, 8, 16, 32]),
                            "memory_gb": random.choice([4, 8, 16, 32, 64, 128]),
                            "storage_gb": random.choice([100, 250, 500, 1000, 2000]),
                            "cpu_utilization_percent": random.randint(10, 90),
                            "memory_utilization_percent": random.randint(20, 95),
                            "storage_utilization_percent": random.randint(30, 85),
                        }
                    )
                elif asset_type == "application":
                    asset_data.update(
                        {
                            "application_name": fake.catch_phrase(),
                            "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                            "vendor": fake.company(),
                            "runtime": random.choice(
                                ["Java", ".NET", "Python", "Node.js", "Go"]
                            ),
                            "user_count": random.randint(10, 1000),
                        }
                    )
                elif asset_type == "database":
                    asset_data.update(
                        {
                            "database_engine": random.choice(
                                [
                                    "PostgreSQL",
                                    "MySQL",
                                    "Oracle",
                                    "SQL Server",
                                    "MongoDB",
                                ]
                            ),
                            "database_version": f"{random.randint(9, 15)}.{random.randint(0, 5)}",
                            "storage_gb": random.randint(50, 5000),
                            "max_iops": random.randint(1000, 50000),
                        }
                    )

                # Add business fields
                asset_data.update(
                    {
                        "business_owner": fake.name(),
                        "technical_owner": fake.name(),
                        "department": random.choice(DEPARTMENTS),
                        "cost_center": f"CC{random.randint(1000, 9999)}",
                        "location": random.choice(DATACENTERS),
                        "current_monthly_cost": round(random.uniform(100, 5000), 2),
                        "six_r_strategy": random.choice(SIXR_STRATEGIES),
                        "migration_complexity": random.choice(
                            ["low", "medium", "high", "very_high"]
                        ),
                        "estimated_migration_cost": round(
                            random.uniform(1000, 50000), 2
                        ),
                    }
                )

                # Build SQL dynamically based on available fields
                fields = list(asset_data.keys())
                placeholders = [f":{field}" for field in fields]

                await session.execute(
                    text(
                        f"""
                        INSERT INTO assets ({', '.join(fields)})
                        VALUES ({', '.join(placeholders)})
                    """
                    ),
                    asset_data,
                )

                assets_created += 1

                # Create some dependencies
                if random.random() > 0.7 and assets_created > 1:
                    # Create dependency with a previous asset
                    dep_id = uuid.uuid4()
                    await session.execute(
                        text(
                            """
                            INSERT INTO asset_dependencies (
                                id, source_asset_id, target_asset_id,
                                dependency_type, description, created_at
                            ) VALUES (
                                :id, :source, :target, :type, :desc, :created
                            )
                        """
                        ),
                        {
                            "id": dep_id,
                            "source": asset_id,
                            "target": asset_id,  # Simplified for demo
                            "type": random.choice(
                                ["network", "database", "api", "shared_storage"]
                            ),
                            "desc": f'{asset_data["hostname"]} depends on shared resource',
                            "created": datetime.now(),
                        },
                    )

        print(f"✓ Created {assets_created} assets with dependencies")


async def main():
    """Main entry point"""
    print(
        f"Seeding test data to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}\n"
    )

    seeder = TestDataSeeder(DATABASE_URL)

    try:
        await seeder.seed_all()
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        await seeder.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
