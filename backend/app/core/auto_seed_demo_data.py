"""
Auto-seed demo data with proper multi-tenancy relationships.
This script runs automatically on startup if no demo data exists.
"""
import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Assessment, Asset, AssetDependency, DataImport, DiscoveryFlow, ImportFieldMapping
from app.models.asset import AssetStatus, AssetType, MigrationWave
from app.models.data_import import RawImportRecord

logger = logging.getLogger(__name__)

# Fixed demo IDs
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DEMO_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


class DemoDataSeeder:
    """Handles automatic seeding of demo data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.created_assets = []
        self.created_flows = []
        
    async def should_seed(self) -> bool:
        """Check if we should seed demo data"""
        # Check if there are any assets
        result = await self.db.execute(
            select(func.count()).select_from(Asset).where(
                Asset.client_account_id == DEMO_CLIENT_ID
            )
        )
        asset_count = result.scalar_one()
        
        if asset_count > 0:
            logger.info(f"Demo data already exists ({asset_count} assets). Skipping seeding.")
            return False
            
        return True
        
    async def confirm_seeding(self) -> bool:
        """In non-interactive mode, always seed if needed"""
        # In production/Docker, we can't interact, so we auto-seed
        # For interactive environments, you could add a prompt here
        return True
        
    async def seed_demo_data(self):
        """Main seeding orchestration"""
        try:
            logger.info("Starting demo data seeding...")
            
            # Create discovery flows first
            await self._create_discovery_flows()
            
            # Create data imports
            await self._create_data_imports()
            
            # Create assets
            await self._create_assets()
            
            # Create dependencies
            await self._create_asset_dependencies()
            
            # Create assessments and analyses
            # Skip assessments for now due to enum issue
            # await self._create_assessments()
            
            # Create migration waves
            await self._create_migration_waves()
            
            await self.db.commit()
            logger.info("Demo data seeding completed successfully!")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to seed demo data: {e}")
            raise
            
    async def _create_discovery_flows(self):
        """Create sample discovery flows"""
        flows_data = [
            {
                "flow_name": "Production Environment Discovery",
                "status": "complete",
                "progress_percentage": 1.0,
                "data_import_completed": True,
                "field_mapping_completed": True,
                "data_cleansing_completed": True,
                "asset_inventory_completed": True,
                "dependency_analysis_completed": True,
                "tech_debt_assessment_completed": True,
                "assessment_ready": True,
                "current_phase": "completed"
            },
            {
                "flow_name": "Development Environment Discovery",
                "status": "in_progress",
                "progress_percentage": 0.65,
                "data_import_completed": True,
                "field_mapping_completed": True,
                "data_cleansing_completed": True,
                "asset_inventory_completed": True,
                "dependency_analysis_completed": False,
                "tech_debt_assessment_completed": False,
                "assessment_ready": False,
                "current_phase": "dependency_analysis"
            }
        ]
        
        for flow_data in flows_data:
            flow = DiscoveryFlow(
                id=uuid.uuid4(),
                flow_id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                user_id=str(DEMO_USER_ID),
                **flow_data
            )
            self.db.add(flow)
            self.created_flows.append(flow)
            
        logger.info(f"Created {len(flows_data)} discovery flows")
        
    async def _create_data_imports(self):
        """Create sample data imports"""
        if not self.created_flows:
            return
            
        imports_data = [
            {
                "import_name": "server_inventory.csv",
                "import_type": "ASSET_INVENTORY",
                "filename": "server_inventory.csv",
                "file_size": 153600,
                "mime_type": "text/csv",
                "status": "completed",
                "total_records": 150,
                "processed_records": 150,
                "failed_records": 0
            },
            {
                "import_name": "application_catalog.xlsx",
                "import_type": "BUSINESS_APPS",
                "filename": "application_catalog.xlsx",
                "file_size": 204800,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "status": "completed",
                "total_records": 75,
                "processed_records": 75,
                "failed_records": 0
            }
        ]
        
        for i, import_data in enumerate(imports_data):
            data_import = DataImport(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                imported_by=DEMO_USER_ID,
                description=f"Demo import of {import_data['filename']}",
                progress_percentage=1.0 if import_data['status'] == 'completed' else 0.5,
                **import_data
            )
            self.db.add(data_import)
            
        logger.info(f"Created {len(imports_data)} data imports")
        
    async def _create_assets(self):
        """Create sample assets with proper multi-tenancy"""
        # Server assets
        servers = []
        for i in range(1, 21):  # 20 servers
            server = Asset(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                flow_id=self.created_flows[0].flow_id if self.created_flows else None,
                name=f"prod-server-{i:02d}",
                hostname=f"prod-server-{i:02d}.democorp.local",
                asset_type=AssetType.SERVER,
                description=f"Production server {i}",
                ip_address=f"10.0.1.{100 + i}",
                environment="production",
                datacenter="us-east-1",
                operating_system="Windows Server 2019" if i % 2 == 0 else "Red Hat Enterprise Linux 8",
                cpu_cores=8 if i <= 10 else 16,
                memory_gb=32 if i <= 10 else 64,
                storage_gb=500 + (i * 100),
                criticality="high" if i <= 5 else "medium",
                six_r_strategy="rehost" if i <= 10 else "replatform",
                migration_status=AssetStatus.DISCOVERED,
                discovery_method="automated",
                discovery_source="server_inventory.csv",
                imported_by=DEMO_USER_ID,
                created_by=DEMO_USER_ID
            )
            self.db.add(server)
            servers.append(server)
            
        # Application assets
        applications = []
        app_names = ["CRM System", "HR Portal", "Finance App", "Inventory Management", "Customer Portal"]
        for i, app_name in enumerate(app_names):
            app = Asset(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                flow_id=self.created_flows[0].flow_id if self.created_flows else None,
                name=app_name.lower().replace(" ", "-"),
                asset_name=app_name,
                asset_type=AssetType.APPLICATION,
                description=f"Business application: {app_name}",
                environment="production",
                application_name=app_name,
                technology_stack="Java Spring" if i % 2 == 0 else ".NET Core",
                criticality="high",
                business_owner=f"business.owner{i+1}@democorp.com",
                technical_owner=f"tech.owner{i+1}@democorp.com",
                six_r_strategy="refactor" if i < 2 else "replatform",
                migration_status=AssetStatus.DISCOVERED,
                discovery_method="automated",
                discovery_source="application_catalog.xlsx",
                imported_by=DEMO_USER_ID,
                created_by=DEMO_USER_ID
            )
            self.db.add(app)
            applications.append(app)
            
        # Database assets
        databases = []
        db_names = ["CustomerDB", "ProductDB", "OrderDB", "AnalyticsDB"]
        for i, db_name in enumerate(db_names):
            database = Asset(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                flow_id=self.created_flows[0].flow_id if self.created_flows else None,
                name=db_name.lower(),
                asset_name=db_name,
                asset_type=AssetType.DATABASE,
                description=f"Database: {db_name}",
                environment="production",
                technology_stack="PostgreSQL" if i % 2 == 0 else "MySQL",
                criticality="high",
                six_r_strategy="replatform",
                migration_status=AssetStatus.DISCOVERED,
                discovery_method="automated",
                imported_by=DEMO_USER_ID,
                created_by=DEMO_USER_ID
            )
            self.db.add(database)
            databases.append(database)
            
        self.created_assets = servers + applications + databases
        logger.info(f"Created {len(self.created_assets)} assets")
        
    async def _create_asset_dependencies(self):
        """Create dependencies between assets"""
        if len(self.created_assets) < 5:
            return
            
        # Get different asset types
        servers = [a for a in self.created_assets if a.asset_type == AssetType.SERVER]
        apps = [a for a in self.created_assets if a.asset_type == AssetType.APPLICATION]
        dbs = [a for a in self.created_assets if a.asset_type == AssetType.DATABASE]
        
        dependencies_created = 0
        
        # Apps depend on servers
        for i, app in enumerate(apps[:5]):
            if i < len(servers):
                dep = AssetDependency(
                    id=uuid.uuid4(),
                    asset_id=app.id,
                    depends_on_asset_id=servers[i].id,
                    dependency_type="hosting",
                    description=f"{app.asset_name} hosted on {servers[i].name}"
                )
                self.db.add(dep)
                dependencies_created += 1
                
        # Apps depend on databases
        for i, app in enumerate(apps[:4]):
            if i < len(dbs):
                dep = AssetDependency(
                    id=uuid.uuid4(),
                    asset_id=app.id,
                    depends_on_asset_id=dbs[i].id,
                    dependency_type="database",
                    description=f"{app.asset_name} uses {dbs[i].asset_name}"
                )
                self.db.add(dep)
                dependencies_created += 1
                
        logger.info(f"Created {dependencies_created} asset dependencies")
        
    async def _create_assessments(self):
        """Create sample assessments"""
        if not self.created_assets:
            return
            
        # Create assessments for first 5 assets
        for asset in self.created_assets[:5]:
            assessment = Assessment(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                migration_id=None,  # Can be added later
                asset_id=asset.id,
                assessment_type="TECHNICAL",
                status="COMPLETED",
                title=f"Technical Assessment - {asset.name}",
                description=f"Automated technical assessment for {asset.name}",
                overall_score=random.uniform(0.7, 0.95),
                risk_level=random.choice(["low", "medium", "high"]),
                confidence_level=random.uniform(0.8, 0.95),
                recommended_strategy=asset.six_r_strategy,
                technical_complexity=random.choice(["low", "medium", "high"]),
                compatibility_score=random.uniform(0.7, 1.0),
                business_criticality=asset.criticality,
                assessor="AI Assessment Engine",
                assessment_date=datetime.now(timezone.utc)
            )
            self.db.add(assessment)
            
        logger.info("Created sample assessments")
        
    async def _create_migration_waves(self):
        """Create sample migration waves"""
        waves_data = [
            {
                "wave_number": 1,
                "name": "Non-Critical Development Systems",
                "description": "First wave focusing on development and test environments",
                "status": "planned",
                "total_assets": 5,
                "planned_start_date": datetime.now(timezone.utc) + timedelta(days=30),
                "planned_end_date": datetime.now(timezone.utc) + timedelta(days=60)
            },
            {
                "wave_number": 2,
                "name": "Production Support Systems",
                "description": "Second wave for non-customer facing production systems",
                "status": "planned",
                "total_assets": 8,
                "planned_start_date": datetime.now(timezone.utc) + timedelta(days=90),
                "planned_end_date": datetime.now(timezone.utc) + timedelta(days=120)
            }
        ]
        
        for wave_data in waves_data:
            wave = MigrationWave(
                id=uuid.uuid4(),
                client_account_id=DEMO_CLIENT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                created_by=DEMO_USER_ID,
                **wave_data
            )
            self.db.add(wave)
            
        logger.info(f"Created {len(waves_data)} migration waves")


async def auto_seed_demo_data(db: AsyncSession) -> bool:
    """
    Automatically seed demo data if needed.
    Returns True if seeding was performed, False otherwise.
    """
    seeder = DemoDataSeeder(db)
    
    # Check if we should seed
    if not await seeder.should_seed():
        return False
        
    # Confirm seeding (auto-confirm in non-interactive mode)
    if not await seeder.confirm_seeding():
        logger.info("Demo data seeding cancelled by user")
        return False
        
    # Perform seeding
    await seeder.seed_demo_data()
    return True


# For testing
if __name__ == "__main__":
    import asyncio

    from app.core.database import AsyncSessionLocal
    
    async def main():
        async with AsyncSessionLocal() as db:
            seeded = await auto_seed_demo_data(db)
            if seeded:
                print("✅ Demo data seeded successfully!")
            else:
                print("ℹ️ Demo data already exists or seeding was skipped")
    
    asyncio.run(main())