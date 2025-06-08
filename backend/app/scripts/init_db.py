"""
Database initialization script for AI Force Migration Platform.
Populates the database with mock data for demo purposes.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.database import engine, AsyncSessionLocal, init_db
    from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation
    from app.models.asset import Asset, AssetType, AssetStatus, SixRStrategy, MigrationWave
    # from app.models.sixr_analysis import SixRAnalysis
    from app.models.tags import Tag, AssetEmbedding, AssetTag
    import bcrypt
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages and set up the database connection.")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data based on Azure Migrate metadata and common migration scenarios
MOCK_DATA = {
    "client_accounts": [
        {
            "name": "Demo Corporation",
            "slug": "demo-corp",
            "description": "Sample enterprise client for platform demonstration",
            "industry": "Technology",
            "company_size": "Large (1000-5000 employees)",
            "subscription_tier": "enterprise",
            "billing_contact_email": "billing@democorp.com"
        }
    ],
    
    "users": [
        {
            "email": "demo@democorp.com",
            "password": "password123",  # Will be hashed
            "first_name": "Demo",
            "last_name": "User",
            "is_verified": True
        },
        {
            "email": "admin@democorp.com", 
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "is_verified": True
        }
    ],
    
    "engagements": [
        {
            "name": "Cloud Migration 2024",
            "slug": "cloud-migration-2024",
            "description": "Migration of on-premises infrastructure to AWS cloud",
            "engagement_type": "migration",
            "status": "active",
            "priority": "high",
            "client_contact_name": "John Smith",
            "client_contact_email": "john.smith@democorp.com"
        }
    ],
    
    # Tags based on Azure Migrate metadata categories
    "tags": [
        # Technology Tags
        {"name": "Windows Server", "category": "technology", "description": "Windows Server operating system"},
        {"name": "Linux", "category": "technology", "description": "Linux operating system"}, 
        {"name": "Database Server", "category": "technology", "description": "Database server workload"},
        {"name": "Web Server", "category": "technology", "description": "Web server workload"},
        {"name": "Application Server", "category": "technology", "description": "Application server workload"},
        {"name": "Domain Controller", "category": "technology", "description": "Active Directory domain controller"},
        {"name": "File Server", "category": "technology", "description": "File server workload"},
        {"name": "Mail Server", "category": "technology", "description": "Email server workload"},
        
        # Business Function Tags
        {"name": "Customer Facing", "category": "business", "description": "Customer-facing applications"},
        {"name": "Internal Tools", "category": "business", "description": "Internal business tools"},
        {"name": "Backup System", "category": "business", "description": "Backup and recovery systems"},
        {"name": "Monitoring", "category": "business", "description": "Monitoring and observability"},
        {"name": "Security", "category": "business", "description": "Security-related systems"},
        
        # Infrastructure Tags  
        {"name": "Virtual Machine", "category": "infrastructure", "description": "Virtual machine workload"},
        {"name": "Physical Server", "category": "infrastructure", "description": "Physical server hardware"},
        {"name": "Network Device", "category": "infrastructure", "description": "Network infrastructure"},
        {"name": "Storage System", "category": "infrastructure", "description": "Storage infrastructure"},
        
        # Migration Readiness Tags
        {"name": "Cloud Ready", "category": "migration", "description": "Ready for cloud migration"},
        {"name": "Legacy System", "category": "migration", "description": "Legacy system requiring modernization"},
        {"name": "High Availability", "category": "migration", "description": "High availability requirements"},
        {"name": "Compliance Required", "category": "migration", "description": "Regulatory compliance requirements"}
    ],
    
    # Assets based on typical enterprise infrastructure
    "assets": [
        # Servers
        {
            "name": "DC-WEB-01",
            "hostname": "dc-web-01.democorp.local",
            "asset_type": AssetType.SERVER,
            "description": "Primary web server hosting customer portal",
            "ip_address": "192.168.1.10",
            "fqdn": "dc-web-01.democorp.local",
            "environment": "Production",
            "location": "Data Center 1",
            "datacenter": "DC1-EAST",
            "operating_system": "Windows Server 2019",
            "os_version": "Standard",
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 500,
            "business_owner": "IT Operations",
            "department": "Infrastructure",
            "application_name": "Customer Portal",
            "technology_stack": "IIS, ASP.NET, SQL Server",
            "criticality": "High",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REHOST,
            "migration_complexity": "Medium",
            "migration_wave": 1,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 65.5,
            "memory_utilization_percent": 78.2,
            "current_monthly_cost": 1200.0,
            "estimated_cloud_cost": 950.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Azure Migrate"
        },
        {
            "name": "DC-DB-01", 
            "hostname": "dc-db-01.democorp.local",
            "asset_type": AssetType.DATABASE,
            "description": "Primary SQL Server database for customer data",
            "ip_address": "192.168.1.20",
            "fqdn": "dc-db-01.democorp.local", 
            "environment": "Production",
            "location": "Data Center 1",
            "datacenter": "DC1-EAST",
            "operating_system": "Windows Server 2016",
            "os_version": "Standard",
            "cpu_cores": 16,
            "memory_gb": 64,
            "storage_gb": 2000,
            "business_owner": "Database Team",
            "department": "IT",
            "application_name": "Customer Database",
            "technology_stack": "SQL Server 2016, Always On",
            "criticality": "Critical",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REPLATFORM,
            "migration_complexity": "High",
            "migration_wave": 2,
            "sixr_ready": "Needs Analysis",
            "dependencies": ["DC-WEB-01"],
            "cpu_utilization_percent": 45.3,
            "memory_utilization_percent": 82.1,
            "current_monthly_cost": 2500.0,
            "estimated_cloud_cost": 1800.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Azure Migrate"
        },
        {
            "name": "DC-APP-01",
            "hostname": "dc-app-01.democorp.local",
            "asset_type": AssetType.APPLICATION,
            "description": "Internal CRM application server",
            "ip_address": "192.168.1.30",
            "environment": "Production", 
            "location": "Data Center 1",
            "operating_system": "Linux Red Hat 8",
            "cpu_cores": 4,
            "memory_gb": 16,
            "storage_gb": 200,
            "business_owner": "Sales Team",
            "department": "Sales",
            "application_name": "CRM System",
            "technology_stack": "Java Spring Boot, PostgreSQL",
            "criticality": "Medium",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REFACTOR,
            "migration_complexity": "Medium",
            "migration_wave": 3,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 35.8,
            "memory_utilization_percent": 68.4,
            "current_monthly_cost": 800.0,
            "estimated_cloud_cost": 650.0,
            "discovery_method": "network_scan",
            "discovery_source": "Custom Discovery Tool"
        },
        # Network Devices
        {
            "name": "CORE-SW-01",
            "hostname": "core-sw-01",
            "asset_type": AssetType.NETWORK,
            "description": "Core network switch for data center connectivity",
            "ip_address": "192.168.1.1",
            "environment": "Production",
            "location": "Data Center 1",
            "operating_system": "Cisco IOS",
            "business_owner": "Network Team",
            "department": "Infrastructure",
            "technology_stack": "Cisco Catalyst 9500",
            "criticality": "Critical",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.RETAIN,
            "migration_complexity": "Low",
            "sixr_ready": "Not Applicable",
            "discovery_method": "snmp_scan",
            "discovery_source": "Network Discovery"
        },
        {
            "name": "FIREWALL-01",
            "hostname": "fw-01",
            "asset_type": AssetType.NETWORK,
            "description": "Perimeter firewall for network security",
            "ip_address": "192.168.1.2",
            "environment": "Production",
            "location": "Data Center 1", 
            "operating_system": "Palo Alto PAN-OS",
            "business_owner": "Security Team",
            "department": "Security",
            "technology_stack": "Palo Alto PA-5220",
            "criticality": "Critical",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REPLATFORM,
            "migration_complexity": "Medium",
            "migration_wave": 1,
            "sixr_ready": "Needs Analysis",
            "discovery_method": "manual_entry",
            "discovery_source": "Manual Entry"
        },
        # Storage
        {
            "name": "SAN-STORAGE-01",
            "hostname": "san-01",
            "asset_type": AssetType.STORAGE,
            "description": "Primary storage area network for VMs",
            "ip_address": "192.168.1.5",
            "environment": "Production",
            "location": "Data Center 1",
            "operating_system": "Dell EMC PowerStoreOS",
            "business_owner": "Storage Team",
            "department": "Infrastructure",
            "technology_stack": "Dell EMC PowerStore 9200T",
            "criticality": "High",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REPLATFORM,
            "migration_complexity": "High",
            "migration_wave": 2,
            "sixr_ready": "Needs Analysis",
            "discovery_method": "api_integration",
            "discovery_source": "Dell EMC CloudIQ"
        }
    ]
}


def generate_mock_embedding(text: str) -> List[float]:
    """Generates a consistent, fake vector embedding for mock data."""
    # Use a simple hashing method to create a deterministic "random" vector
    np.random.seed(abs(hash(text)) % (2**32 - 1))
    return np.random.rand(1536).tolist()


async def create_mock_client_account(session: AsyncSession) -> str:
    """Creates mock client account if it doesn't exist."""
    
    client_data = MOCK_DATA["client_accounts"][0]
    
    existing_client_result = await session.execute(
        text(f"SELECT id FROM client_accounts WHERE slug = '{client_data['slug']}'")
    )
    existing_client_row = existing_client_result.first()
    if existing_client_row:
        logger.info(f"Client account '{client_data['name']}' already exists.")
        return str(existing_client_row[0])
    
    new_client = ClientAccount(**client_data, is_mock=True)
    session.add(new_client)
    await session.flush()
    await session.refresh(new_client)
    
    logger.info(f"Created mock client account: {new_client.name}")
    return str(new_client.id)


async def create_mock_users(session: AsyncSession, client_account_id: str) -> List[str]:
    """Creates mock users and associates them with the client account."""
    user_ids = {}
    
    for user_data in MOCK_DATA["users"]:
        
        existing_user_result = await session.execute(
            text(f"SELECT id FROM users WHERE email = '{user_data['email']}'")
        )
        existing_user_row = existing_user_result.first()
        if existing_user_row:
            user_id = str(existing_user_row[0])
            user_ids[user_data['email']] = user_id
            logger.info(f"User with email '{user_data['email']}' already exists.")
            
            # Check for association
            assoc_stmt = text(f"SELECT 1 FROM user_account_associations WHERE user_id = '{user_id}' AND client_account_id = '{client_account_id}'")
            existing_assoc = await session.execute(assoc_stmt)
            if not existing_assoc.first():
                 association = UserAccountAssociation(
                    user_id=user_id,
                    client_account_id=client_account_id,
                    role="admin" if "admin" in user_data["email"] else "member"
                )
                 session.add(association)
            continue

        hashed_password = bcrypt.hashpw(
            user_data["password"].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        user = User(
            email=user_data["email"],
            password_hash=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_verified=user_data.get("is_verified", False),
            is_active=True,
            is_mock=True
        )
        
        session.add(user)
        await session.flush() # Flush to get the user.id
        await session.refresh(user)
        
        # Associate user with the client account
        association = UserAccountAssociation(
            user_id=user.id,
            client_account_id=client_account_id,
            role="admin" if "admin" in user.email else "member"
        )
        session.add(association)
        
        user_ids[user_data['email']] = str(user.id)
        logger.info(f"Created mock user: {user.email}")
    
    return user_ids


async def create_mock_engagement(session: AsyncSession, client_account_id: str, user_id: str) -> str:
    """Creates a mock engagement for the demo client."""
    engagement_data = MOCK_DATA["engagements"][0]
    
    # Check if engagement already exists
    existing_engagement_id = await session.execute(
        select(Engagement.id).where(
            Engagement.slug == engagement_data["slug"],
            Engagement.client_account_id == uuid.UUID(client_account_id)
        )
    )
    if existing_engagement_id.scalar_one_or_none():
        logger.info(f"Mock engagement '{engagement_data['name']}' already exists.")
        return str(existing_engagement_id.scalar_one())

    engagement = Engagement(
        id=uuid.uuid4(),
        client_account_id=uuid.UUID(client_account_id),
        name=engagement_data["name"],
        slug=engagement_data["slug"],
        description=engagement_data["description"],
        engagement_type=engagement_data["engagement_type"],
        status=engagement_data["status"],
        priority=engagement_data["priority"],
        client_contact_name=engagement_data["client_contact_name"],
        client_contact_email=engagement_data["client_contact_email"],
        created_by=uuid.UUID(user_id) if user_id else None,
        is_mock=True
    )
    session.add(engagement)
    await session.flush()
    logger.info(f"Created mock engagement: {engagement.name}")
    return str(engagement.id)


async def create_mock_tags(session: AsyncSession, client_account_id: str) -> Dict[str, str]:
    """Creates mock tags based on predefined list."""
    tag_ids = {}
    for tag_data in MOCK_DATA["tags"]:
        # Check if tag exists
        existing_tag_id = await session.execute(
            select(Tag.id).where(Tag.name == tag_data["name"])
        )
        if existing_tag_id.scalar_one_or_none():
            logger.info(f"Mock tag '{tag_data['name']}' already exists.")
            tag_ids[tag_data["name"]] = str(existing_tag_id.scalar_one())
            continue
            
        tag = Tag(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID(client_account_id),
            name=tag_data["name"],
            category=tag_data["category"],
            description=tag_data["description"],
            is_mock=True,
            # Placeholder for embedding - ensure it is not a string
            reference_embedding=generate_mock_embedding(tag_data["name"]),
        )
        session.add(tag)
        await session.flush()
        tag_ids[tag_data["name"]] = str(tag.id)
    logger.info(f"Created {len(tag_ids)} mock tags.")
    return tag_ids


async def create_mock_assets(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str, tag_ids: Dict[str, str]) -> List[str]:
    asset_ids = []
    
    mock_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'mock_cmdb_data.json')
    try:
        with open(mock_data_path, 'r') as f:
            mock_assets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load mock asset data: {e}")
        return []

    for asset_data in mock_assets:
        try:
            asset_id = uuid.uuid4()
            
            asset_info = asset_data.copy()
            asset_info.pop("dependencies", None)
            asset_info["id"] = asset_id
            asset_info["client_account_id"] = client_account_id
            asset_info["engagement_id"] = engagement_id
            asset_info["created_by"] = user_id
            asset_info["is_mock"] = True

            asset = Asset(**asset_info)
            session.add(asset)
            await session.flush()
            asset_ids.append(str(asset_id))

            # Create embedding
            embedding_text = f"{asset_data.get('name', '')} {asset_data.get('description', '')} {asset_data.get('technology_stack', '')}"
            embedding_vector = generate_mock_embedding(embedding_text)
            
            embedding = AssetEmbedding(
                asset_id=asset_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                embedding=embedding_vector,
                source_text=embedding_text,
                is_mock=True
            )
            session.add(embedding)
            
            # Link tags
            if asset_data.get('asset_type') == 'server': # Use .get() for safety
                os_info = asset_data.get('operating_system', '')
                tag_name = "Windows Server" if "windows" in os_info.lower() else "Linux"
                if tag_name in tag_ids:
                    asset_tag = AssetTag(
                        asset_id=asset_id, 
                        tag_id=tag_ids[tag_name], 
                        confidence_score=0.95,
                        assigned_method='auto',
                        is_mock=True
                    )
                    session.add(asset_tag)

        except Exception as e:
            logger.error(f"Error creating asset {asset_data.get('name')}: {e}")
            await session.rollback()

    # Link dependencies after all assets have been created
    # This logic is complex and depends on having asset objects, not just IDs.
    # We will simplify by not creating dependency links for now.

    await session.commit()
    logger.info("Successfully created mock assets and embeddings.")
    return asset_ids


async def create_mock_sixr_analysis(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str, asset_ids: List[str]):
    """Creates mock 6R analysis data for assets."""
    
    for asset_id_str in asset_ids:
        asset_id = uuid.UUID(asset_id_str)
        asset = await session.get(Asset, asset_id)
        
        if not asset:
            continue
            
        analysis = SixRAnalysis(
            asset_id=asset.id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            recommended_strategy=asset.six_r_strategy or SixRStrategy.RETAIN,
            justification="Mock data - based on initial asset discovery.",
            confidence_score=np.random.uniform(0.7, 0.95),
            status="completed",
            is_mock=True,
            created_by=user_id,
            analysis_version="1.0"
        )
        session.add(analysis)
        
    await session.commit()
    logger.info("Successfully created mock 6R analysis.")
    

async def create_mock_migration_waves(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str):
    """Creates mock migration waves."""
    
    wave_data = {
        1: {"name": "Wave 1 - Pilot", "description": "Pilot migration of non-critical web servers.", "status": "planning", "start_date_offset": 7, "end_date_offset": 37},
        2: {"name": "Wave 2 - Core Databases", "description": "Replatform core customer databases.", "status": "planning", "start_date_offset": 45, "end_date_offset": 105},
        3: {"name": "Wave 3 - Application Refactor", "description": "Refactor monolithic CRM application.", "status": "planning", "start_date_offset": 110, "end_date_offset": 200}
    }
    
    for wave_num, data in wave_data.items():
        stmt = select(MigrationWave).where(
            MigrationWave.wave_number == wave_num,
            MigrationWave.client_account_id == uuid.UUID(client_account_id),
            MigrationWave.engagement_id == uuid.UUID(engagement_id)
        )
        result = await session.execute(stmt)
        existing_wave = result.scalars().first()
        
        if not existing_wave:
            start_date = datetime.utcnow() + timedelta(days=data["start_date_offset"])
            end_date = datetime.utcnow() + timedelta(days=data["end_date_offset"])
            wave = MigrationWave(
                id=uuid.uuid4(),
                wave_number=wave_num,
                name=data["name"],
                description=data["description"],
                status=data["status"],
                planned_start_date=start_date,
                planned_end_date=end_date,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                is_mock=True,
                created_by=user_id
            )
            session.add(wave)
            
    await session.commit()
    logger.info("Successfully created mock migration waves.")


async def initialize_mock_data():
    """Initializes the database with mock data."""
    
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot initialize mock data due to missing dependencies.")
        return

    logger.info("Starting database initialization...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Create Client Account
            client_account_id = await create_mock_client_account(session)
            
            # 2. Create Users
            user_ids = await create_mock_users(session, client_account_id)
            admin_user_id = user_ids["admin@democorp.com"] # Assuming admin is the second user
            
            # 3. Create Engagement
            engagement_id = await create_mock_engagement(session, client_account_id, admin_user_id)
            
            # 4. Create Tags
            tag_ids = await create_mock_tags(session, client_account_id)
            
            # 5. Create Migration Waves
            await create_mock_migration_waves(
                session, 
                client_account_id, 
                engagement_id, 
                admin_user_id
            )
            
            # 6. Create Assets, Embeddings, and associate Tags
            asset_ids = await create_mock_assets(
                session, 
                client_account_id, 
                engagement_id, 
                admin_user_id, 
                tag_ids
            )
            
            # 7. Create 6R Analysis
            # await create_mock_sixr_analysis(
            #     session, 
            #     client_account_id, 
            #     engagement_id, 
            #     admin_user_id,
            #     asset_ids
            # )

            await session.commit()
            logger.info("Database initialization completed successfully.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error during database initialization: {e}")
            raise
        
        finally:
            await session.close()


async def check_mock_data_exists():
    """Checks if mock data has already been populated."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1 FROM client_accounts WHERE is_mock = TRUE LIMIT 1"))
        return result.scalar_one_or_none() is not None


async def main():
    """Main function to run the initialization script."""
    
    # Check if a command-line argument is provided
    force_run = '--force' in sys.argv
    
    if not force_run and await check_mock_data_exists():
        logger.info("Mock data already exists. Use '--force' to re-run.")
        return
        
    logger.info("Populating database with mock data...")
    await init_db()  # Ensure tables are created
    await initialize_mock_data()


if __name__ == "__main__":
    if not DEPENDENCIES_AVAILABLE:
        sys.exit(1)
    
    # Run the async main function
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1) 