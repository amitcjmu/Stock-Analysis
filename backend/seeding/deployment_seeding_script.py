"""
Complete deployment seeding script for Railway/Vercel deployment.
This script sets up all demo data in the correct order for a fresh deployment.
Run this after migrations are applied to populate the database with demo data.
"""

import asyncio
import hashlib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

from sqlalchemy import func, select, text

from app.core.database import AsyncSessionLocal
from app.models import (
    Asset,
    ClientAccount,
    DataImport,
    DiscoveryFlow,
    Engagement,
    ImportFieldMapping,
    User,
    UserAccountAssociation,
    UserRole,
)
from seeding.constants import DEMO_USER_IDS

# Import the individual seeding modules
from seeding.demo_multi_tenant_setup import (
    clean_demo_data,
    create_demo_multi_tenant_data,
)


class DeploymentSeeder:
    """Orchestrates the complete deployment seeding process"""

    def __init__(self):
        self.demo_client_id = "11111111-1111-1111-1111-111111111111"
        self.demo_engagement_id = "22222222-2222-2222-2222-222222222222"

    def get_secure_demo_password_hash(self):
        """Get secure password hash from environment or generate one"""
        demo_password = os.getenv(
            "DEMO_SEED_PASSWORD", "DemoPassword123!"
        )  # nosec B105 - Demo password fallback for seeding
        # Use SHA256 for consistent demo password hashing
        return hashlib.sha256(demo_password.encode()).hexdigest()

    async def check_database_ready(self):
        """Verify database is ready and migrations are applied"""
        print("\n🔍 Checking database readiness...")
        async with AsyncSessionLocal() as session:
            try:
                # Check if core tables exist
                await session.execute(text("SELECT 1 FROM client_accounts LIMIT 1"))
                await session.execute(text("SELECT 1 FROM users LIMIT 1"))
                await session.execute(text("SELECT 1 FROM discovery_flows LIMIT 1"))
                await session.execute(text("SELECT 1 FROM assets LIMIT 1"))
                print("✅ Database tables verified")
                return True
            except Exception as e:
                print(f"❌ Database not ready: {e}")
                return False

    async def seed_base_demo_account(self):
        """Seed the base DemoCorp account and users"""
        print("\n📁 Creating base DemoCorp account...")
        async with AsyncSessionLocal() as session:
            # Check if already exists
            existing = await session.get(ClientAccount, self.demo_client_id)
            if existing:
                print("⚠️ Base DemoCorp account already exists")
                return

            # Create base client account
            client = ClientAccount(
                id=self.demo_client_id,
                name="DemoCorp International",
                slug="democorp",
                description="Primary demo company for platform demonstrations",
                industry="Technology",
                company_size="1000-5000",
                headquarters_location="San Francisco, CA",
                primary_contact_name="Demo Admin",
                primary_contact_email="admin@democorp.com",
                contact_phone="+1-555-0000",
            )
            session.add(client)

            # Create base engagement
            engagement = Engagement(
                id=self.demo_engagement_id,
                client_account_id=self.demo_client_id,
                name="Cloud Migration Assessment 2024",
                slug="cloud-migration-2024",
                description="Comprehensive cloud migration assessment and planning",
                status="active",
                engagement_type="migration",
                start_date=datetime.now(timezone.utc),
                target_completion_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            )
            session.add(engagement)

            # Create base demo users
            demo_users = [
                {
                    "id": DEMO_USER_IDS["demo"],
                    "email": "demo@democorp.com",
                    "first_name": "Demo",
                    "last_name": "User",
                    "role": "engagement_manager",
                },
                {
                    "id": DEMO_USER_IDS["analyst"],
                    "email": "analyst@democorp.com",
                    "first_name": "Demo",
                    "last_name": "Analyst",
                    "role": "analyst",
                },
                {
                    "id": DEMO_USER_IDS["viewer"],
                    "email": "viewer@democorp.com",
                    "first_name": "Demo",
                    "last_name": "Viewer",
                    "role": "viewer",
                },
                {
                    "id": DEMO_USER_IDS["client_admin"],
                    "email": "client.admin@democorp.com",
                    "first_name": "Client",
                    "last_name": "Admin",
                    "role": "client_admin",
                },
            ]

            for user_data in demo_users:
                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    password_hash=self.get_secure_demo_password_hash(),
                    is_active=True,
                    is_verified=True,
                    default_client_id=self.demo_client_id,
                    default_engagement_id=self.demo_engagement_id,
                )
                session.add(user)

                # Create RBAC role
                user_role = UserRole(
                    user_id=user_data["id"],
                    client_account_id=self.demo_client_id,
                    engagement_id=self.demo_engagement_id,
                    role=user_data["role"],
                )
                session.add(user_role)

                # Create user-client association
                association = UserAccountAssociation(
                    user_id=user_data["id"],
                    client_account_id=self.demo_client_id,
                    role=user_data["role"],
                )
                session.add(association)

            await session.commit()
            print("✅ Base DemoCorp account and users created")

    async def seed_discovery_flows(self):
        """Seed discovery flows in various states"""
        print("\n🔄 Creating discovery flows...")
        async with AsyncSessionLocal() as session:
            # Check if flows already exist
            result = await session.execute(select(func.count(DiscoveryFlow.id)))
            if result.scalar() > 0:
                print("⚠️ Discovery flows already exist")
                return

            flows = [
                {
                    "flow_name": "Complete Discovery Flow - Ready for Assessment",
                    "status": "complete",
                    "progress_percentage": 100.0,
                    "data_import_completed": True,
                    "field_mapping_completed": True,
                    "data_cleansing_completed": True,
                    "asset_inventory_completed": True,
                    "dependency_analysis_completed": True,
                    "tech_debt_assessment_completed": True,
                    "assessment_ready": True,
                    "learning_scope": "engagement",
                    "memory_isolation_level": "strict",
                },
                {
                    "flow_name": "In Progress - Field Mapping Stage",
                    "status": "active",
                    "progress_percentage": 33.3,
                    "data_import_completed": True,
                    "field_mapping_completed": False,
                    "learning_scope": "engagement",
                    "memory_isolation_level": "moderate",
                },
                {
                    "flow_name": "In Progress - Asset Inventory Stage",
                    "status": "active",
                    "progress_percentage": 50.0,
                    "data_import_completed": True,
                    "field_mapping_completed": True,
                    "data_cleansing_completed": True,
                    "learning_scope": "client",
                    "memory_isolation_level": "open",
                },
                {
                    "flow_name": "Failed Import - Error Handling Demo",
                    "status": "failed",
                    "progress_percentage": 16.7,
                    "data_import_completed": True,
                    "error_message": "Invalid data format in import file",
                    "error_phase": "field_mapping",
                    "learning_scope": "engagement",
                    "memory_isolation_level": "strict",
                },
                {
                    "flow_name": "Just Started - Initial State",
                    "status": "active",
                    "progress_percentage": 0.0,
                    "learning_scope": "engagement",
                    "memory_isolation_level": "strict",
                },
            ]

            # Import discovery flow module here to access CrewAI state
            from seeding.discovery_flow_seeder import generate_crewai_state_data

            for i, flow_data in enumerate(flows):
                flow = DiscoveryFlow(
                    flow_id=f"flow{i+1:08d}-def0-def0-def0-{i+1:012d}",
                    client_account_id=self.demo_client_id,
                    engagement_id=self.demo_engagement_id,
                    user_id=DEMO_USER_IDS["demo"],
                    crewai_state_data=generate_crewai_state_data(
                        flow_data["status"], flow_data["progress_percentage"]
                    ),
                    **flow_data,
                )
                session.add(flow)

            await session.commit()
            print("✅ Discovery flows created")

    async def seed_complete_demo_data(self):
        """Run the complete seeding process"""
        print("\n" + "=" * 60)
        print("🚀 DEPLOYMENT SEEDING PROCESS")
        print("=" * 60)

        # Step 1: Check database
        if not await self.check_database_ready():
            print("❌ Database not ready. Please run migrations first.")
            return False

        # Step 2: Clean and create multi-tenant demo data
        print("\n📋 Setting up multi-tenant demo data...")
        await clean_demo_data()
        await create_demo_multi_tenant_data()

        # Step 3: Create base DemoCorp account
        await self.seed_base_demo_account()

        # Step 4: Create discovery flows
        await self.seed_discovery_flows()

        # Step 5: Import the complete seeding scripts
        print("\n📦 Running complete data seeding...")

        # Import and run the seeding modules in order
        try:
            # These modules will use the existing demo accounts
            from seeding.asset_dependency_seeder import seed_dependencies
            from seeding.asset_seeder import seed_assets
            from seeding.data_import_seeder import seed_data_imports
            from seeding.field_mapping_seeder import seed_field_mappings
            from seeding.migration_planning_seeder import seed_migration_planning

            await seed_data_imports()
            await seed_field_mappings()
            await seed_assets()
            await seed_dependencies()
            await seed_migration_planning()

        except ImportError as e:
            print(f"⚠️ Some seeding modules not found: {e}")
            print("Basic demo data has been created successfully.")

        # Step 6: Verify deployment
        await self.verify_deployment()

        print("\n" + "=" * 60)
        print("✅ DEPLOYMENT SEEDING COMPLETE!")
        print("=" * 60)
        print("\n📝 Demo Login Credentials:")
        print("   - demo@democorp.com (Password: Demo123!)")
        print("   - admin@demo.techcorp.com (Password: Demo123!)")
        print("   - All demo users use password: Demo123!")

        return True

    async def verify_deployment(self):
        """Verify the deployment data"""
        print("\n🔍 Verifying deployment data...")
        async with AsyncSessionLocal() as session:
            # Count records
            counts = {
                "Client Accounts": await session.scalar(
                    select(func.count(ClientAccount.id))
                ),
                "Users": await session.scalar(select(func.count(User.id))),
                "Discovery Flows": await session.scalar(
                    select(func.count(DiscoveryFlow.id))
                ),
                "Data Imports": await session.scalar(select(func.count(DataImport.id))),
                "Assets": await session.scalar(select(func.count(Asset.id))),
                "Field Mappings": await session.scalar(
                    select(func.count(ImportFieldMapping.id))
                ),
            }

            print("\n📊 Record Counts:")
            for entity, count in counts.items():
                print(f"   - {entity}: {count}")


async def main():
    """Main entry point for deployment seeding"""
    seeder = DeploymentSeeder()
    success = await seeder.seed_complete_demo_data()

    if not success:
        print("\n❌ Deployment seeding failed")
        sys.exit(1)
    else:
        print("\n✅ Deployment seeding successful")
        sys.exit(0)


if __name__ == "__main__":
    # Check if running in production
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL_ENV"):
        print("🚨 Running in production environment")
        print("⚠️ This will create demo data in the production database")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(main())
