#!/usr/bin/env python3
"""
Database initialization script for AI Force Migration Platform.
Populates the database with comprehensive mock data for demo purposes.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import AsyncSessionLocal, engine
    from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation
    from app.models.cmdb_asset import CMDBAsset, AssetType, AssetStatus, SixRStrategy, CMDBSixRAnalysis, MigrationWave
    from app.models.tags import Tag, AssetTag
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import dependencies: {e}")
    DEPENDENCIES_AVAILABLE = False


class DatabaseInitializer:
    """Initialize database with comprehensive mock data."""
    
    def __init__(self):
        self.session: AsyncSession = None
        self.demo_client_id = None
        self.demo_engagement_id = None
        self.demo_user_id = None
        
    async def initialize(self):
        """Initialize the database with mock data."""
        if not DEPENDENCIES_AVAILABLE:
            logger.error("Dependencies not available. Cannot initialize database.")
            return False
            
        try:
            async with AsyncSessionLocal() as session:
                self.session = session
                
                logger.info("Starting database initialization...")
                
                # Check if mock data already exists
                if await self._mock_data_exists():
                    logger.info("Mock data already exists. Skipping initialization.")
                    return True
                
                # Create mock data in order
                await self._create_demo_client_account()
                await self._create_demo_users()
                await self._create_demo_engagement()
                await self._create_demo_tags()
                await self._create_demo_cmdb_assets()
                await self._create_demo_sixr_analysis()
                await self._create_demo_migration_waves()
                await self._assign_asset_tags()
                
                await session.commit()
                logger.info("Database initialization completed successfully!")
                return True
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if self.session:
                await self.session.rollback()
            return False
    
    async def _mock_data_exists(self) -> bool:
        """Check if mock data already exists."""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(ClientAccount).where(ClientAccount.is_mock == True).limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    async def _create_demo_client_account(self):
        """Create demo client account."""
        logger.info("Creating demo client account...")
        
        client_account = ClientAccount(
            id=uuid.uuid4(),
            name="Acme Corporation",
            slug="acme-corp",
            description="A leading technology company undergoing cloud migration",
            industry="Technology",
            company_size="Enterprise (1000+ employees)",
            subscription_tier="Enterprise",
            billing_contact_email="billing@acme-corp.com",
            settings={
                "timezone": "UTC",
                "currency": "USD",
                "notification_preferences": {
                    "email": True,
                    "slack": False,
                    "teams": True
                }
            },
            branding={
                "primary_color": "#2563eb",
                "logo_url": "/assets/acme-logo.png",
                "company_website": "https://acme-corp.com"
            },
            is_mock=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.session.add(client_account)
        await self.session.flush()
        self.demo_client_id = client_account.id
        logger.info(f"Created demo client account: {client_account.name}")
    
    async def _create_demo_users(self):
        """Create demo users."""
        logger.info("Creating demo users...")
        
        users_data = [
            {
                "email": "john.doe@acme-corp.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin"
            },
            {
                "email": "jane.smith@acme-corp.com", 
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "migration_lead"
            }
        ]
        
        demo_user = None
        for user_data in users_data:
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
                is_verified=True,
                is_mock=True,
                created_at=datetime.utcnow()
            )
            
            self.session.add(user)
            await self.session.flush()
            
            # Create user-account association
            association = UserAccountAssociation(
                id=uuid.uuid4(),
                user_id=user.id,
                client_account_id=self.demo_client_id,
                role=user_data["role"],
                is_mock=True,
                created_at=datetime.utcnow()
            )
            
            self.session.add(association)
            
            if user_data["role"] == "admin":
                self.demo_user_id = user.id
                demo_user = user
                
        logger.info("Created demo users and associations")
    
    async def _create_demo_engagement(self):
        """Create demo engagement."""
        logger.info("Creating demo engagement...")
        
        engagement = Engagement(
            id=uuid.uuid4(),
            client_account_id=self.demo_client_id,
            name="Cloud Migration Initiative 2024",
            slug="cloud-migration-2024",
            description="Comprehensive migration of on-premises infrastructure to Azure cloud",
            engagement_type="cloud_migration",
            status="active",
            priority="high",
            start_date=datetime.utcnow() - timedelta(days=30),
            target_completion_date=datetime.utcnow() + timedelta(days=180),
            engagement_lead_id=self.demo_user_id,
            client_contact_name="John Doe",
            client_contact_email="john.doe@acme-corp.com",
            settings={
                "migration_target": "Azure",
                "compliance_requirements": ["SOC2", "GDPR", "HIPAA"],
                "budget_limit": 500000,
                "timeline_flexibility": "moderate"
            },
            is_mock=True,
            is_active=True,
            created_by=self.demo_user_id,
            created_at=datetime.utcnow()
        )
        
        self.session.add(engagement)
        await self.session.flush()
        self.demo_engagement_id = engagement.id
        logger.info(f"Created demo engagement: {engagement.name}")
    
    async def _create_demo_tags(self):
        """Create demo tags for auto-tagging."""
        logger.info("Creating demo tags...")
        
        tags_data = [
            # Technology Tags
            {"name": "Windows Server", "category": "Technology", "description": "Microsoft Windows Server operating system"},
            {"name": "Linux", "category": "Technology", "description": "Linux-based operating systems"},
            {"name": "SQL Server", "category": "Technology", "description": "Microsoft SQL Server database"},
            {"name": "Oracle Database", "category": "Technology", "description": "Oracle database systems"},
            {"name": "VMware", "category": "Technology", "description": "VMware virtualization platform"},
            {"name": "IIS", "category": "Technology", "description": "Internet Information Services web server"},
            {"name": "Apache", "category": "Technology", "description": "Apache web server"},
            {"name": ".NET Framework", "category": "Technology", "description": ".NET application framework"},
            {"name": "Java", "category": "Technology", "description": "Java runtime environment"},
            {"name": "Docker", "category": "Technology", "description": "Container platform"},
            
            # Business Tags
            {"name": "Production", "category": "Business", "description": "Production environment systems"},
            {"name": "Development", "category": "Business", "description": "Development environment systems"},
            {"name": "Testing", "category": "Business", "description": "Testing environment systems"},
            {"name": "Critical", "category": "Business", "description": "Business-critical systems"},
            {"name": "High Availability", "category": "Business", "description": "High availability requirements"},
            {"name": "24x7", "category": "Business", "description": "24x7 operational requirements"},
            
            # Infrastructure Tags
            {"name": "Physical Server", "category": "Infrastructure", "description": "Physical hardware servers"},
            {"name": "Virtual Machine", "category": "Infrastructure", "description": "Virtual machine instances"},
            {"name": "Network Device", "category": "Infrastructure", "description": "Network infrastructure components"},
            {"name": "Storage System", "category": "Infrastructure", "description": "Storage infrastructure"},
            {"name": "Load Balancer", "category": "Infrastructure", "description": "Load balancing systems"},
            
            # Migration Tags
            {"name": "Ready for Migration", "category": "Migration", "description": "Assets ready for cloud migration"},
            {"name": "Needs Assessment", "category": "Migration", "description": "Requires further assessment"},
            {"name": "Dependencies", "category": "Migration", "description": "Has migration dependencies"},
            {"name": "Legacy System", "category": "Migration", "description": "Legacy system requiring special handling"}
        ]
        
        for tag_data in tags_data:
            tag = Tag(
                id=uuid.uuid4(),
                name=tag_data["name"],
                category=tag_data["category"],
                description=tag_data["description"],
                confidence_threshold=0.7,
                is_active=True,
                usage_count=0,
                created_at=datetime.utcnow()
            )
            
            self.session.add(tag)
            
        logger.info(f"Created {len(tags_data)} demo tags")
    
    async def _create_demo_cmdb_assets(self):
        """Create demo CMDB assets."""
        logger.info("Creating demo CMDB assets...")
        
        assets_data = [
            {
                "name": "WEB-PROD-01",
                "hostname": "web-prod-01.acme.local",
                "asset_type": AssetType.SERVER,
                "description": "Primary production web server hosting customer portal",
                "ip_address": "10.0.1.10",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 8,
                "memory_gb": 32.0,
                "storage_gb": 500.0,
                "business_owner": "John Doe",
                "department": "IT Operations",
                "application_name": "Customer Portal",
                "technology_stack": "IIS, .NET Framework 4.8",
                "criticality": "Critical",
                "status": AssetStatus.ASSESSED,
                "six_r_strategy": SixRStrategy.REPLATFORM,
                "migration_priority": 5,
                "migration_complexity": "Medium",
                "migration_wave": 1,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 1200.0,
                "estimated_cloud_cost": 800.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "DB-PROD-01",
                "hostname": "db-prod-01.acme.local",
                "asset_type": AssetType.DATABASE,
                "description": "Primary production SQL Server database",
                "ip_address": "10.0.1.20",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "storage_gb": 2000.0,
                "business_owner": "Jane Smith",
                "department": "Database Administration",
                "application_name": "Customer Database",
                "technology_stack": "SQL Server 2019 Enterprise",
                "criticality": "Critical",
                "status": AssetStatus.PLANNED,
                "six_r_strategy": SixRStrategy.REHOST,
                "migration_priority": 5,
                "migration_complexity": "High",
                "migration_wave": 1,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 2500.0,
                "estimated_cloud_cost": 1800.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "APP-PROD-01",
                "hostname": "app-prod-01.acme.local",
                "asset_type": AssetType.APPLICATION,
                "description": "Core business application server",
                "ip_address": "10.0.1.30",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Linux RHEL 8",
                "cpu_cores": 12,
                "memory_gb": 48.0,
                "storage_gb": 1000.0,
                "business_owner": "Mike Johnson",
                "department": "Application Development",
                "application_name": "ERP System",
                "technology_stack": "Java 11, Apache Tomcat",
                "criticality": "High",
                "status": AssetStatus.ASSESSED,
                "six_r_strategy": SixRStrategy.REFACTOR,
                "migration_priority": 5,
                "migration_complexity": "High",
                "migration_wave": 2,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 1800.0,
                "estimated_cloud_cost": 1200.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "LB-PROD-01",
                "hostname": "lb-prod-01.acme.local",
                "asset_type": AssetType.LOAD_BALANCER,
                "description": "Production load balancer for web tier",
                "ip_address": "10.0.1.5",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "F5 BIG-IP",
                "cpu_cores": 4,
                "memory_gb": 16.0,
                "storage_gb": 200.0,
                "business_owner": "Network Team",
                "department": "Network Operations",
                "application_name": "Load Balancing",
                "technology_stack": "F5 BIG-IP LTM",
                "criticality": "Critical",
                "status": AssetStatus.PLANNED,
                "six_r_strategy": SixRStrategy.REPLACE,
                "migration_priority": 5,
                "migration_complexity": "Medium",
                "migration_wave": 1,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 800.0,
                "estimated_cloud_cost": 400.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "STORAGE-01",
                "hostname": "storage-01.acme.local",
                "asset_type": AssetType.STORAGE,
                "description": "Primary SAN storage system",
                "ip_address": "10.0.2.10",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "NetApp ONTAP",
                "storage_gb": 50000.0,
                "business_owner": "Storage Team",
                "department": "Infrastructure",
                "application_name": "Shared Storage",
                "technology_stack": "NetApp FAS8200",
                "criticality": "Critical",
                "status": AssetStatus.DISCOVERED,
                "six_r_strategy": SixRStrategy.REPLATFORM,
                "migration_priority": 5,
                "migration_complexity": "High",
                "migration_wave": 3,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 3000.0,
                "estimated_cloud_cost": 2000.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "DEV-WEB-01",
                "hostname": "dev-web-01.acme.local",
                "asset_type": AssetType.SERVER,
                "description": "Development web server",
                "ip_address": "10.0.3.10",
                "environment": "Development",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 4,
                "memory_gb": 16.0,
                "storage_gb": 250.0,
                "business_owner": "Dev Team",
                "department": "Development",
                "application_name": "Development Portal",
                "technology_stack": "IIS, .NET Core",
                "criticality": "Low",
                "status": AssetStatus.ASSESSED,
                "six_r_strategy": SixRStrategy.REHOST,
                "migration_priority": 5,
                "migration_complexity": "Low",
                "migration_wave": 4,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 400.0,
                "estimated_cloud_cost": 200.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "LEGACY-APP-01",
                "hostname": "legacy-app-01.acme.local",
                "asset_type": AssetType.APPLICATION,
                "description": "Legacy mainframe application",
                "ip_address": "10.0.4.10",
                "environment": "Production",
                "location": "Data Center West",
                "datacenter": "DC-WEST-01",
                "operating_system": "IBM z/OS",
                "business_owner": "Legacy Systems Team",
                "department": "Mainframe Operations",
                "application_name": "Legacy Billing System",
                "technology_stack": "COBOL, DB2",
                "criticality": "Medium",
                "status": AssetStatus.EXCLUDED,
                "six_r_strategy": SixRStrategy.RETAIN,
                "migration_priority": 5,
                "migration_complexity": "Very High",
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 5000.0,
                "estimated_cloud_cost": 5000.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "BACKUP-SRV-01",
                "hostname": "backup-srv-01.acme.local",
                "asset_type": AssetType.SERVER,
                "description": "Backup and recovery server",
                "ip_address": "10.0.2.20",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 8,
                "memory_gb": 32.0,
                "storage_gb": 10000.0,
                "business_owner": "Backup Team",
                "department": "Infrastructure",
                "application_name": "Veeam Backup",
                "technology_stack": "Veeam Backup & Replication",
                "criticality": "High",
                "status": AssetStatus.PLANNED,
                "six_r_strategy": SixRStrategy.REPLACE,
                "migration_priority": 5,
                "migration_complexity": "Medium",
                "migration_wave": 2,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 1000.0,
                "estimated_cloud_cost": 600.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "MONITOR-01",
                "hostname": "monitor-01.acme.local",
                "asset_type": AssetType.SERVER,
                "description": "Infrastructure monitoring server",
                "ip_address": "10.0.1.100",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Linux Ubuntu 20.04",
                "cpu_cores": 6,
                "memory_gb": 24.0,
                "storage_gb": 500.0,
                "business_owner": "Monitoring Team",
                "department": "Operations",
                "application_name": "Nagios Monitoring",
                "technology_stack": "Nagios, Grafana",
                "criticality": "Medium",
                "status": AssetStatus.MIGRATED,
                "six_r_strategy": SixRStrategy.REPLACE,
                "migration_priority": 5,
                "migration_complexity": "Low",
                "migration_wave": 3,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 600.0,
                "estimated_cloud_cost": 300.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
            {
                "name": "FILE-SRV-01",
                "hostname": "file-srv-01.acme.local",
                "asset_type": AssetType.SERVER,
                "description": "File server for shared documents",
                "ip_address": "10.0.1.50",
                "environment": "Production",
                "location": "Data Center East",
                "datacenter": "DC-EAST-01",
                "operating_system": "Windows Server 2016",
                "cpu_cores": 4,
                "memory_gb": 16.0,
                "storage_gb": 5000.0,
                "business_owner": "IT Support",
                "department": "IT Operations",
                "application_name": "File Sharing",
                "technology_stack": "Windows File Services, DFS",
                "criticality": "Medium",
                "status": AssetStatus.PLANNED,
                "six_r_strategy": SixRStrategy.REPLACE,
                "migration_priority": 5,
                "migration_complexity": "Low",
                "migration_wave": 4,
                "discovery_method": "network_scan",
                "discovery_source": "Azure Migrate",
                "discovery_timestamp": datetime.utcnow() - timedelta(days=7),
                "current_monthly_cost": 500.0,
                "estimated_cloud_cost": 250.0,
                "is_mock": True,
                "created_by": self.demo_user_id,
            },
        ]
        
        for asset_data in assets_data:
            asset = CMDBAsset(
                id=uuid.uuid4(),
                client_account_id=self.demo_client_id,
                engagement_id=self.demo_engagement_id,
                created_at=datetime.utcnow(),
                **asset_data
            )
            
            self.session.add(asset)
            
        logger.info(f"Created {len(assets_data)} demo CMDB assets")
    
    async def _create_demo_sixr_analysis(self):
        """Create demo 6R analysis."""
        logger.info("Creating demo 6R analysis...")
        
        analysis = CMDBSixRAnalysis(
            id=uuid.uuid4(),
            client_account_id=self.demo_client_id,
            engagement_id=self.demo_engagement_id,
            analysis_name="Cloud Migration Assessment 2024",
            description="Comprehensive 6R analysis for cloud migration initiative",
            status="completed",
            total_assets=10,
            rehost_count=3,
            replatform_count=4,
            refactor_count=1,
            rearchitect_count=0,
            retire_count=0,
            retain_count=1,
            total_current_cost=16800.0,
            total_estimated_cost=11550.0,
            potential_savings=5250.0,
            analysis_results={
                "summary": {
                    "total_assets_analyzed": 10,
                    "migration_readiness": "75%",
                    "estimated_timeline": "6 months",
                    "risk_level": "Medium"
                },
                "recommendations": [
                    "Prioritize rehost strategy for quick wins",
                    "Consider replatform for database systems",
                    "Evaluate refactoring for legacy applications",
                    "Implement proper backup and disaster recovery"
                ]
            },
            recommendations={
                "immediate_actions": [
                    "Begin with Wave 1 migration (critical systems)",
                    "Set up Azure landing zone",
                    "Establish connectivity and security"
                ],
                "medium_term": [
                    "Migrate development environments",
                    "Implement monitoring and governance",
                    "Train operations team"
                ],
                "long_term": [
                    "Optimize cloud costs",
                    "Implement cloud-native features",
                    "Retire legacy systems"
                ]
            },
            is_mock=True,
            created_by=self.demo_user_id,
            created_at=datetime.utcnow()
        )
        
        self.session.add(analysis)
        logger.info("Created demo 6R analysis")
    
    async def _create_demo_migration_waves(self):
        """Create demo migration waves."""
        logger.info("Creating demo migration waves...")
        
        waves_data = [
            {
                "wave_number": 1,
                "name": "Critical Infrastructure",
                "description": "Migration of critical production infrastructure including web servers, databases, and load balancers",
                "status": "planned",
                "planned_start_date": datetime.utcnow() + timedelta(days=30),
                "planned_end_date": datetime.utcnow() + timedelta(days=60),
                "total_assets": 3,
                "estimated_cost": 15000.0,
                "estimated_effort_hours": 240.0
            },
            {
                "wave_number": 2,
                "name": "Application Tier",
                "description": "Migration of application servers and supporting infrastructure",
                "status": "planned",
                "planned_start_date": datetime.utcnow() + timedelta(days=60),
                "planned_end_date": datetime.utcnow() + timedelta(days=90),
                "total_assets": 2,
                "estimated_cost": 8000.0,
                "estimated_effort_hours": 160.0
            },
            {
                "wave_number": 3,
                "name": "Storage and Monitoring",
                "description": "Migration of storage systems and monitoring infrastructure",
                "status": "planned",
                "planned_start_date": datetime.utcnow() + timedelta(days=90),
                "planned_end_date": datetime.utcnow() + timedelta(days=120),
                "total_assets": 2,
                "estimated_cost": 12000.0,
                "estimated_effort_hours": 200.0
            },
            {
                "wave_number": 4,
                "name": "Development and Support",
                "description": "Migration of development environments and support systems",
                "status": "planned",
                "planned_start_date": datetime.utcnow() + timedelta(days=120),
                "planned_end_date": datetime.utcnow() + timedelta(days=150),
                "total_assets": 2,
                "estimated_cost": 5000.0,
                "estimated_effort_hours": 80.0
            }
        ]
        
        for wave_data in waves_data:
            wave = MigrationWave(
                id=uuid.uuid4(),
                client_account_id=self.demo_client_id,
                engagement_id=self.demo_engagement_id,
                is_mock=True,
                created_by=self.demo_user_id,
                created_at=datetime.utcnow(),
                **wave_data
            )
            
            self.session.add(wave)
            
        logger.info(f"Created {len(waves_data)} demo migration waves")
    
    async def _assign_asset_tags(self):
        """Assign tags to assets for demo purposes."""
        logger.info("Assigning tags to assets...")
        
        # Get some assets and tags for assignment
        from sqlalchemy import select
        
        assets_result = await self.session.execute(
            select(CMDBAsset).where(CMDBAsset.is_mock == True).limit(5)
        )
        assets = assets_result.scalars().all()
        
        tags_result = await self.session.execute(
            select(Tag).limit(10)
        )
        tags = tags_result.scalars().all()
        
        # Check if we have enough assets and tags
        if len(assets) < 3 or len(tags) < 5:
            logger.warning(f"Not enough assets ({len(assets)}) or tags ({len(tags)}) for assignment")
            return
        
        # Assign some tags to assets - use safe indexing
        tag_assignments = []
        
        if len(assets) > 0 and len(tags) > 0:
            tag_assignments.append((assets[0].id, tags[0].id, 0.95, "auto"))  # First asset -> First tag
        
        if len(assets) > 0 and len(tags) > 9:
            tag_assignments.append((assets[0].id, tags[9].id, 0.88, "auto"))  # First asset -> 10th tag
        
        if len(assets) > 1 and len(tags) > 2:
            tag_assignments.append((assets[1].id, tags[2].id, 0.92, "auto"))  # Second asset -> Third tag
        
        if len(assets) > 1 and len(tags) > 4:
            tag_assignments.append((assets[1].id, tags[4].id, 0.90, "auto"))  # Second asset -> Fifth tag
        
        if len(assets) > 2 and len(tags) > 1:
            tag_assignments.append((assets[2].id, tags[1].id, 0.85, "auto"))  # Third asset -> Second tag
        
        if len(assets) > 2 and len(tags) > 3:
            tag_assignments.append((assets[2].id, tags[3].id, 0.87, "auto"))  # Third asset -> Fourth tag
        
        for asset_id, tag_id, confidence, method in tag_assignments:
            asset_tag = AssetTag(
                id=uuid.uuid4(),
                cmdb_asset_id=asset_id,
                tag_id=tag_id,
                confidence_score=confidence,
                assigned_method=method,
                assigned_by=self.demo_user_id,
                is_validated=False,
                is_mock=True,
                created_at=datetime.utcnow()
            )
            
            self.session.add(asset_tag)
            
        logger.info(f"Assigned {len(tag_assignments)} tags to assets")


async def main():
    """Main function to initialize the database."""
    initializer = DatabaseInitializer()
    success = await initializer.initialize()
    
    if success:
        logger.info("✅ Database initialization completed successfully!")
        return 0
    else:
        logger.error("❌ Database initialization failed!")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 