"""
Database initialization script for AI Modernize Migration Platform.
Populates the database with mock data for demo purposes.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import bcrypt
    import numpy as np
    from app.core.database import AsyncSessionLocal, engine, init_db
    from app.models.asset import (
        Asset,
        AssetStatus,
        AssetType,
        MigrationWave,
        SixRStrategy,
    )
    from app.models.client_account import (
        ClientAccount,
        Engagement,
        User,
        UserAccountAssociation,
    )
    from app.models.rbac import (
        AccessLevel,
        ClientAccess,
        EngagementAccess,
        RoleType,
        UserProfile,
        UserRole,
        UserStatus,
    )
    from app.models.sixr_analysis import AnalysisStatus, SixRAnalysis
    from app.models.tags import AssetEmbedding, AssetTag, Tag

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages and set up the database connection.")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Static UUIDs for Demo Mode ---
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
DEMO_USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
ADMIN_USER_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")

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
            "billing_contact_email": "billing@democorp.com",
        }
    ],
    "users": [
        {
            "email": "demo@democorp.com",
            "password": "password123",  # Will be hashed
            "first_name": "Demo",
            "last_name": "User",
            "is_verified": True,
        }
        # SECURITY: ALL ADMIN DEMO ACCOUNTS REMOVED - no demo accounts with admin privileges
        # Platform admin (chocka@gmail.com) will be set up manually, not via scripts
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
            "client_contact_email": "john.smith@democorp.com",
        }
    ],
    # Tags based on Azure Migrate metadata categories
    "tags": [
        # Technology Tags
        {
            "name": "Windows Server",
            "category": "technology",
            "description": "Windows Server operating system",
        },
        {
            "name": "Linux",
            "category": "technology",
            "description": "Linux operating system",
        },
        {
            "name": "Database Server",
            "category": "technology",
            "description": "Database server workload",
        },
        {
            "name": "Web Server",
            "category": "technology",
            "description": "Web server workload",
        },
        {
            "name": "Application Server",
            "category": "technology",
            "description": "Application server workload",
        },
        {
            "name": "Domain Controller",
            "category": "technology",
            "description": "Active Directory domain controller",
        },
        {
            "name": "File Server",
            "category": "technology",
            "description": "File server workload",
        },
        {
            "name": "Mail Server",
            "category": "technology",
            "description": "Email server workload",
        },
        # Business Function Tags
        {
            "name": "Customer Facing",
            "category": "business",
            "description": "Customer-facing applications",
        },
        {
            "name": "Internal Tools",
            "category": "business",
            "description": "Internal business tools",
        },
        {
            "name": "Backup System",
            "category": "business",
            "description": "Backup and recovery systems",
        },
        {
            "name": "Monitoring",
            "category": "business",
            "description": "Monitoring and observability",
        },
        {
            "name": "Security",
            "category": "business",
            "description": "Security-related systems",
        },
        # Infrastructure Tags
        {
            "name": "Virtual Machine",
            "category": "infrastructure",
            "description": "Virtual machine workload",
        },
        {
            "name": "Physical Server",
            "category": "infrastructure",
            "description": "Physical server hardware",
        },
        {
            "name": "Network Device",
            "category": "infrastructure",
            "description": "Network infrastructure",
        },
        {
            "name": "Storage System",
            "category": "infrastructure",
            "description": "Storage infrastructure",
        },
        # Migration Readiness Tags
        {
            "name": "Cloud Ready",
            "category": "migration",
            "description": "Ready for cloud migration",
        },
        {
            "name": "Legacy System",
            "category": "migration",
            "description": "Legacy system requiring modernization",
        },
        {
            "name": "High Availability",
            "category": "migration",
            "description": "High availability requirements",
        },
        {
            "name": "Compliance Required",
            "category": "migration",
            "description": "Regulatory compliance requirements",
        },
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
            "six_r_strategy": SixRStrategy.REHOST.value,
            "migration_complexity": "Medium",
            "migration_wave": 1,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 65.5,
            "memory_utilization_percent": 78.2,
            "current_monthly_cost": 1200.0,
            "estimated_cloud_cost": 950.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Azure Migrate",
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
            "six_r_strategy": SixRStrategy.REPLATFORM.value,
            "migration_complexity": "High",
            "migration_wave": 2,
            "sixr_ready": "Needs Analysis",
            "dependencies": ["DC-WEB-01"],
            "cpu_utilization_percent": 45.3,
            "memory_utilization_percent": 82.1,
            "current_monthly_cost": 2500.0,
            "estimated_cloud_cost": 1800.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Azure Migrate",
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
            "six_r_strategy": SixRStrategy.REFACTOR.value,
            "migration_complexity": "Medium",
            "migration_wave": 3,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 35.8,
            "memory_utilization_percent": 68.4,
            "current_monthly_cost": 800.0,
            "estimated_cloud_cost": 650.0,
            "discovery_method": "network_scan",
            "discovery_source": "Custom Discovery Tool",
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
            "six_r_strategy": SixRStrategy.RETAIN.value,
            "migration_complexity": "Low",
            "sixr_ready": "Not Applicable",
            "discovery_method": "snmp_scan",
            "discovery_source": "Network Discovery",
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
            "six_r_strategy": SixRStrategy.REPLATFORM.value,
            "migration_complexity": "Medium",
            "migration_wave": 1,
            "sixr_ready": "Needs Analysis",
            "discovery_method": "manual_entry",
            "discovery_source": "Manual Entry",
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
            "six_r_strategy": SixRStrategy.REPLATFORM.value,
            "migration_complexity": "High",
            "migration_wave": 2,
            "sixr_ready": "Needs Analysis",
            "discovery_method": "api_integration",
            "discovery_source": "Dell EMC CloudIQ",
        },
    ],
}


def generate_mock_embedding(text: str) -> List[float]:
    """Generates a consistent, fake vector embedding for mock data."""
    # Use a simple hashing method to create a deterministic "random" vector
    np.random.seed(abs(hash(text)) % (2**32 - 1))
    return np.random.rand(1536).tolist()


async def create_mock_client_account(session: AsyncSession) -> uuid.UUID:
    """Creates mock client account if it doesn't exist."""
    client_data = MOCK_DATA["client_accounts"][0]
    client = ClientAccount(id=DEMO_CLIENT_ID, **client_data, is_mock=True)
    await session.merge(client)  # Use merge to handle potential pre-existence
    await session.flush()
    logger.info(f"Created mock client account: {client.name}")
    return client.id


async def create_mock_users(
    session: AsyncSession, client_account_id: uuid.UUID
) -> Dict[str, uuid.UUID]:
    """Creates mock users, profiles, roles, and access records."""
    logger.info("Creating mock users, profiles, and roles...")
    user_ids = {}

    for user_data in MOCK_DATA["users"]:
        # Check if user already exists
        existing_user_result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = existing_user_result.scalars().first()

        if existing_user:
            logger.info(
                f"User {user_data['email']} already exists, skipping creation but fetching ID."
            )
            user_ids[user_data["email"]] = existing_user.id
            # Even if user exists, ensure profile and roles are there for idempotency
            # This is a simplified approach for a seeding script.
            # A more robust implementation would check and update if necessary.
        else:
            # Hash password
            hashed_password = bcrypt.hashpw(
                user_data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Create user (only demo user, no admin accounts)
            user = User(
                id=DEMO_USER_ID,  # Only demo user, no admin constant needed
                email=user_data["email"],
                password_hash=hashed_password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
                is_verified=user_data.get("is_verified", True),
                is_mock=True,
            )
            session.add(user)
            await session.flush()
            user_id = user.id
            user_ids[user_data["email"]] = user_id
            logger.info(f"Created user: {user.email} with ID: {user_id}")

            # Associate user with client account (demo user only - no admin)
            user_account_association = UserAccountAssociation(
                user_id=user.id,
                client_account_id=client_account_id,
                role="User",  # Demo user gets standard user role, not admin
            )
            session.add(user_account_association)
            logger.info(
                f"Associated {user.email} with client account {client_account_id}"
            )

    # Commit users first to ensure they have IDs before creating dependent objects
    try:
        await session.commit()
    except Exception as e:
        logger.error(f"Error committing initial users: {e}")
        await session.rollback()
        raise

    # Now create profiles and roles for all users
    for email, user_id in user_ids.items():
        # Check for existing profile
        existing_profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        if existing_profile_result.scalars().first():
            logger.info(f"User profile for {email} already exists.")
        else:
            # Only demo user profile creation (no admin profiles)
            user_profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                organization="Demo Corporation",
                role_description="Demo User",  # Demo user only, no admin
                requested_access_level=AccessLevel.READ_WRITE,  # Standard access, no admin
                approved_at=datetime.utcnow(),
                approved_by=user_ids.get(
                    "demo@democorp.com", DEMO_USER_ID
                ),  # Self-approved by demo user
            )
            session.add(user_profile)
            logger.info(f"Created user profile for {email}")

        # Check for existing role
        existing_role_result = await session.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        if existing_role_result.scalars().first():
            logger.info(f"User role for {email} already exists.")
        else:
            # Only demo user role creation (analyst level, no admin)
            role_type = RoleType.ANALYST  # Demo user gets analyst role only
            user_role = UserRole(
                user_id=user_id,
                role_type=role_type.value,
                role_name=role_type.name.replace("_", " ").title(),
                description=f"{role_type.name.replace('_', ' ').title()} for Demo Corporation",
                scope_type="client",
                scope_client_id=client_account_id,
                assigned_by=user_ids.get("demo@democorp.com", DEMO_USER_ID),
                is_active=True,
            )
            session.add(user_role)
            logger.info(f"Assigned role '{role_type.name}' to {email}")

        # Check for existing client access
        existing_access_result = await session.execute(
            select(ClientAccess).where(
                ClientAccess.user_profile_id == user_id,
                ClientAccess.client_account_id == client_account_id,
            )
        )
        if existing_access_result.scalars().first():
            logger.info(f"Client access for {email} already exists.")
        else:
            # Only demo user client access (standard level, no admin)
            client_access = ClientAccess(
                user_profile_id=user_id,
                client_account_id=client_account_id,
                access_level=AccessLevel.READ_WRITE,  # Standard access only, no admin
                granted_by=user_ids.get("demo@democorp.com", DEMO_USER_ID),
            )
            session.add(client_access)
            logger.info(f"Granted client access to {email}")

    try:
        await session.commit()
        logger.info("Successfully created/verified mock users, profiles, and roles.")
    except Exception as e:
        logger.error(f"Error committing users and profiles: {e}")
        await session.rollback()
        raise

    return user_ids


async def create_mock_engagement(
    session: AsyncSession, client_account_id: uuid.UUID, user_ids: Dict[str, uuid.UUID]
) -> uuid.UUID:
    """Creates a mock engagement and grants access to users."""
    logger.info("Creating mock engagement...")
    engagement_data = MOCK_DATA["engagements"][0]

    # Check if engagement already exists
    existing_engagement_result = await session.execute(
        select(Engagement).where(
            Engagement.slug == engagement_data["slug"],
            Engagement.client_account_id == client_account_id,
        )
    )
    existing_engagement = existing_engagement_result.scalars().first()

    if existing_engagement:
        logger.info(f"Engagement '{engagement_data['name']}' already exists.")
        engagement_id = existing_engagement.id
    else:
        engagement = Engagement(
            id=DEMO_ENGAGEMENT_ID,
            client_account_id=client_account_id,
            name=engagement_data["name"],
            slug=engagement_data["slug"],
            description=engagement_data["description"],
            engagement_type=engagement_data["engagement_type"],
            status=engagement_data["status"],
            priority=engagement_data["priority"],
            start_date=datetime.utcnow() - timedelta(days=30),
            target_completion_date=datetime.utcnow() + timedelta(days=120),
            client_contact_name=engagement_data["client_contact_name"],
            client_contact_email=engagement_data["client_contact_email"],
            is_mock=True,
            created_by=user_ids["demo@democorp.com"],
        )
        session.add(engagement)
        await session.flush()
        engagement_id = engagement.id
        logger.info(f"Created engagement: {engagement.name}")
        await session.commit()

    # Grant engagement access to all created users
    for email, user_id in user_ids.items():
        existing_access_result = await session.execute(
            select(EngagementAccess).where(
                EngagementAccess.user_profile_id == user_id,
                EngagementAccess.engagement_id == engagement_id,
            )
        )
        if existing_access_result.scalars().first():
            logger.info(f"Engagement access for {email} already exists.")
            continue

        # Only demo user engagement access (analyst level, no admin)
        engagement_access = EngagementAccess(
            user_profile_id=user_id,
            engagement_id=engagement_id,
            access_level=AccessLevel.READ_WRITE,  # Standard access only, no admin
            engagement_role="Analyst",  # Demo user gets analyst role only
            granted_by=user_ids["demo@democorp.com"],
        )
        session.add(engagement_access)
        logger.info(f"Granted engagement access to {email}")

    try:
        await session.commit()
    except Exception as e:
        logger.error(f"Error granting engagement access: {e}")
        await session.rollback()
        raise

    return engagement_id


async def create_mock_tags(
    session: AsyncSession, client_account_id: uuid.UUID
) -> Dict[str, uuid.UUID]:
    """Creates mock tags based on predefined list."""
    tag_ids = {}
    for tag_data in MOCK_DATA["tags"]:
        # Check if tag exists for this client to ensure idempotency
        stmt = select(Tag.id).where(
            Tag.name == tag_data["name"], Tag.client_account_id == client_account_id
        )
        existing_tag_id = await session.execute(stmt)
        tag_id = existing_tag_id.scalar_one_or_none()

        if tag_id:
            tag_ids[tag_data["name"]] = tag_id
            continue

        tag = Tag(
            client_account_id=client_account_id,
            name=tag_data["name"],
            category=tag_data["category"],
            description=tag_data["description"],
            is_mock=True,
            reference_embedding=generate_mock_embedding(tag_data["name"]),
        )
        session.add(tag)
        await session.flush()
        tag_ids[tag_data["name"]] = tag.id
    logger.info(f"Created {len(MOCK_DATA['tags'])} mock tags.")
    return tag_ids


async def create_mock_assets(
    session: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: uuid.UUID,
    tag_ids: Dict[str, uuid.UUID],
) -> List[uuid.UUID]:
    """Creates mock assets, embeddings, and associates them with tags."""
    logger.info("Creating mock assets...")
    asset_ids = []

    # This path seems unused in the loop below, but we'll leave the loading logic for now.
    mock_data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "mock_cmdb_data.json"
    )
    try:
        with open(mock_data_path, "r") as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load mock asset data from mock_cmdb_data.json: {e}")

    for data in MOCK_DATA["assets"]:
        strategy = data.get("six_r_strategy")
        if isinstance(strategy, Enum):
            strategy = strategy.value

        asset = Asset(
            name=data["name"],
            hostname=data["hostname"],
            asset_type=data["asset_type"],
            description=data["description"],
            ip_address=data.get("ip_address"),
            operating_system=data.get("operating_system"),
            os_version=data.get("os_version"),
            environment=data.get("environment", "production"),
            status="active",
            migration_status=data.get("status", AssetStatus.DISCOVERED),
            business_owner=data.get("business_owner"),
            technical_owner=data.get("technical_owner"),
            application_name=data.get("application_name"),
            cpu_cores=data.get("cpu_cores"),
            memory_gb=data.get("ram_gb"),
            storage_gb=data.get("storage_gb"),
            business_criticality=data.get("business_criticality"),
            six_r_strategy=strategy,
            migration_complexity=data.get("migration_complexity"),
            migration_wave=data.get("migration_wave"),
            sixr_ready=data.get("sixr_ready"),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            created_by=user_id,
            is_mock=True,
        )
        session.add(asset)
        await session.flush()

        asset_ids.append(asset.id)

        # Create embedding
        embedding_text = (
            f"{data['name']} {data['description']} {data.get('operating_system', '')}"
        )
        embedding_vector = generate_mock_embedding(embedding_text)
        embedding = AssetEmbedding(
            asset_id=asset.id,
            embedding=embedding_vector,
            embedding_model="text-embedding-ada-002",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            is_mock=True,
        )
        session.add(embedding)

        # Associate tags
        if "tags" in data:
            for tag_name in data["tags"]:
                tag_id = tag_ids.get(tag_name)
                if tag_id:
                    asset_tag = AssetTag(asset_id=asset.id, tag_id=tag_id, is_mock=True)
                    session.add(asset_tag)

    logger.info(f"Successfully created {len(asset_ids)} assets.")
    return asset_ids


async def create_mock_sixr_analysis(
    session: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: uuid.UUID,
    asset_ids: List[uuid.UUID],
):
    """Creates a mock 6R analysis record for the engagement."""
    logger.info("Creating mock 6R analysis record...")

    # Check if an analysis for this engagement already exists
    existing_analysis_result = await session.execute(
        select(SixRAnalysis).where(SixRAnalysis.engagement_id == engagement_id)
    )
    existing_analysis = existing_analysis_result.scalar_one_or_none()

    # Convert asset UUIDs to strings for JSON serialization
    asset_id_strs = [str(aid) for aid in asset_ids]

    if existing_analysis:
        logger.info(
            f"6R analysis for engagement {engagement_id} already exists. Updating application_ids."
        )
        existing_ids = set(existing_analysis.application_ids or [])
        new_ids = set(asset_id_strs)
        all_ids = list(existing_ids.union(new_ids))

        existing_analysis.application_ids = all_ids
        existing_analysis.updated_at = datetime.utcnow()
        session.add(existing_analysis)
    else:
        logger.info("Creating new 6R analysis record.")
        analysis_record = SixRAnalysis(
            name="6R Analysis for Cloud Migration 2024",
            description="Automated 6R analysis for the initial set of discovered assets.",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            status=AnalysisStatus.COMPLETED,
            application_ids=asset_id_strs,
            final_recommendation=SixRStrategy.REHOST,
            confidence_score=0.85,
            created_by=str(user_id),
        )
        session.add(analysis_record)

    try:
        await session.commit()
        logger.info("Successfully created/updated mock 6R analysis record.")
    except Exception as e:
        logger.error(f"Failed to commit 6R analysis record: {e}")
        await session.rollback()


async def create_mock_migration_waves(
    session: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: uuid.UUID,
):
    """Creates mock migration waves and assigns assets to them."""

    wave_data = {
        1: {
            "name": "Wave 1 - Pilot",
            "description": "Pilot migration of non-critical web servers.",
            "status": "planning",
            "start_date_offset": 7,
            "end_date_offset": 37,
        },
        2: {
            "name": "Wave 2 - Core Databases",
            "description": "Replatform core customer databases.",
            "status": "planning",
            "start_date_offset": 45,
            "end_date_offset": 105,
        },
        3: {
            "name": "Wave 3 - Application Refactor",
            "description": "Refactor monolithic CRM application.",
            "status": "planning",
            "start_date_offset": 110,
            "end_date_offset": 200,
        },
    }

    for wave_num, data in wave_data.items():
        # Idempotency check
        stmt = select(MigrationWave).where(
            MigrationWave.wave_number == wave_num,
            MigrationWave.client_account_id == client_account_id,
            MigrationWave.engagement_id == engagement_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            continue

        start_date = datetime.now() + timedelta(days=data["start_date_offset"])
        end_date = datetime.now() + timedelta(days=data["end_date_offset"])

        wave = MigrationWave(
            wave_number=wave_num,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            planned_start_date=start_date,
            planned_end_date=end_date,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            is_mock=True,
            created_by=user_id,
        )
        session.add(wave)

    logger.info("Successfully created mock migration waves.")


async def initialize_mock_data(force: bool = False):
    """
    Initializes the database with mock data for the demo.
    Creates a client account, users, engagement, assets, tags, and analysis.
    """
    async with AsyncSessionLocal() as session:
        if not force and await check_mock_data_exists(session):
            logger.info("Mock data already exists. Skipping initialization.")
            return

        logger.info("--- Starting Mock Data Initialization ---")

        client_account_id = await create_mock_client_account(session)
        user_ids = await create_mock_users(session, client_account_id)
        engagement_id = await create_mock_engagement(
            session, client_account_id, user_ids
        )
        tag_ids = await create_mock_tags(session, client_account_id)

        demo_user_id = user_ids.get("demo@democorp.com")
        if not demo_user_id:
            logger.error("Could not find demo user ID after user creation.")
            # Fallback to a static ID if needed, though this indicates an issue
            demo_user_id_result = await session.execute(
                select(User.id).where(User.email == "demo@democorp.com")
            )
            demo_user_id = demo_user_id_result.scalar_one_or_none() or DEMO_USER_ID

        asset_ids = await create_mock_assets(
            session, client_account_id, engagement_id, demo_user_id, tag_ids
        )

        if asset_ids:
            # Pass correct UUID types
            await create_mock_sixr_analysis(
                session, client_account_id, engagement_id, demo_user_id, asset_ids
            )

        await create_mock_migration_waves(
            session, client_account_id, engagement_id, demo_user_id
        )

        logger.info("--- Mock Data Initialization Complete ---")


async def check_mock_data_exists(session: AsyncSession) -> bool:
    """Checks if mock data has already been populated."""
    result = await session.execute(
        text("SELECT 1 FROM client_accounts WHERE is_mock = TRUE LIMIT 1")
    )
    return result.scalar_one_or_none() is not None


async def main():
    """Main function to run the initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize the database with mock data."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-creation of mock data if it already exists.",
    )
    args = parser.parse_args()

    try:
        await init_db()
        await initialize_mock_data(force=args.force)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if DEPENDENCIES_AVAILABLE:
        asyncio.run(main())
