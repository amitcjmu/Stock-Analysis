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

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import engine, AsyncSessionLocal, init_db
    from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation
    from app.models.cmdb_asset import CMDBAsset, AssetType, AssetStatus, SixRStrategy, MigrationWave
    from app.models.sixr_analysis import SixRAnalysis
    from app.models.tags import Tag, CMDBAssetEmbedding, AssetTag
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
    
    # CMDB Assets based on typical enterprise infrastructure
    "cmdb_assets": [
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
            "discovery_source": "Security Audit"
        },
        # Storage Systems
        {
            "name": "SAN-01",
            "hostname": "san-01.democorp.local",
            "asset_type": AssetType.STORAGE,
            "description": "Primary SAN storage for database systems",
            "ip_address": "192.168.1.50",
            "environment": "Production",
            "location": "Data Center 1",
            "operating_system": "NetApp ONTAP",
            "storage_gb": 10000,
            "business_owner": "Storage Team",
            "department": "Infrastructure", 
            "technology_stack": "NetApp FAS2750",
            "criticality": "Critical",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REPLATFORM,
            "migration_complexity": "High",
            "migration_wave": 2,
            "sixr_ready": "Needs Analysis",
            "discovery_method": "agent_scan",
            "discovery_source": "Storage Discovery Tool"
        },
        # Legacy Systems
        {
            "name": "LEGACY-ERP-01",
            "hostname": "legacy-erp-01",
            "asset_type": AssetType.APPLICATION,
            "description": "Legacy ERP system requiring modernization",
            "ip_address": "192.168.2.10",
            "environment": "Production",
            "location": "Data Center 2",
            "operating_system": "Windows Server 2012 R2",
            "cpu_cores": 12,
            "memory_gb": 48,
            "storage_gb": 1500,
            "business_owner": "Finance Team",
            "department": "Finance",
            "application_name": "Legacy ERP",
            "technology_stack": "Oracle Forms, Oracle Database",
            "criticality": "High",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REARCHITECT,
            "migration_complexity": "High",
            "migration_wave": 4,
            "sixr_ready": "Complex Analysis Required",
            "cpu_utilization_percent": 25.4,
            "memory_utilization_percent": 55.8,
            "current_monthly_cost": 3000.0,
            "estimated_cloud_cost": 2200.0,
            "discovery_method": "manual_entry",
            "discovery_source": "Application Portfolio Review"
        },
        # Virtual Infrastructure
        {
            "name": "VMWARE-VCENTER",
            "hostname": "vcenter.democorp.local",
            "asset_type": AssetType.OTHER,
            "description": "VMware vCenter managing virtual infrastructure",
            "ip_address": "192.168.1.60",
            "environment": "Production",
            "location": "Data Center 1",
            "operating_system": "VMware vSphere 7.0",
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 500,
            "business_owner": "Virtualization Team",
            "department": "Infrastructure",
            "technology_stack": "VMware vSphere 7.0, vCenter",
            "criticality": "Critical",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REPLATFORM,
            "migration_complexity": "High",
            "migration_wave": 1,
            "sixr_ready": "Complex Analysis Required",
            "discovery_method": "api_discovery",
            "discovery_source": "VMware API"
        },
        # Development/Test Systems
        {
            "name": "DEV-WEB-01",
            "hostname": "dev-web-01.democorp.local",
            "asset_type": AssetType.SERVER,
            "description": "Development web server for testing",
            "ip_address": "192.168.3.10",
            "environment": "Development",
            "location": "Data Center 1",
            "operating_system": "Ubuntu 20.04",
            "cpu_cores": 4,
            "memory_gb": 8,
            "storage_gb": 100,
            "business_owner": "Development Team",
            "department": "Engineering",
            "application_name": "Dev Portal",
            "technology_stack": "Node.js, React, MongoDB",
            "criticality": "Low",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REHOST,
            "migration_complexity": "Low",
            "migration_wave": 1,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 15.2,
            "memory_utilization_percent": 45.6,
            "current_monthly_cost": 300.0,
            "estimated_cloud_cost": 180.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Azure Migrate"
        },
        # Monitoring and Management
        {
            "name": "MONITORING-01",
            "hostname": "monitoring-01.democorp.local",
            "asset_type": AssetType.APPLICATION,
            "description": "Infrastructure monitoring and alerting system",
            "ip_address": "192.168.1.70",
            "environment": "Production",
            "location": "Data Center 1",
            "operating_system": "CentOS 8",
            "cpu_cores": 6,
            "memory_gb": 24,
            "storage_gb": 750,
            "business_owner": "Operations Team",
            "department": "IT Operations",
            "application_name": "Monitoring System",
            "technology_stack": "Prometheus, Grafana, AlertManager",
            "criticality": "High",
            "status": AssetStatus.DISCOVERED,
            "six_r_strategy": SixRStrategy.REHOST,
            "migration_complexity": "Medium",
            "migration_wave": 1,
            "sixr_ready": "Ready",
            "cpu_utilization_percent": 42.1,
            "memory_utilization_percent": 67.8,
            "current_monthly_cost": 600.0,
            "estimated_cloud_cost": 450.0,
            "discovery_method": "agent_scan",
            "discovery_source": "Custom Discovery"
        }
    ]
}

# Mock embeddings for demonstration (in production, these would be generated by DeepInfra)
def generate_mock_embedding(text: str) -> List[float]:
    """Generate a mock embedding vector for demo purposes."""
    # Use text hash to create consistent mock embeddings
    text_hash = hash(text) 
    np.random.seed(abs(text_hash) % 2**32)
    return np.random.normal(0, 1, 1536).tolist()

async def create_mock_client_account(session: AsyncSession) -> str:
    """Create mock client account and return its ID."""
    client_data = MOCK_DATA["client_accounts"][0]
    
    client_account = ClientAccount(
        name=client_data["name"],
        slug=client_data["slug"],
        description=client_data["description"],
        industry=client_data["industry"],
        company_size=client_data["company_size"],
        subscription_tier=client_data["subscription_tier"],
        billing_contact_email=client_data["billing_contact_email"],
        is_mock=True
    )
    
    session.add(client_account)
    await session.flush()  # Get the ID
    logger.info(f"Created mock client account: {client_account.name}")
    return str(client_account.id)

async def create_mock_users(session: AsyncSession, client_account_id: str) -> List[str]:
    """Create mock users and return their IDs."""
    user_ids = []
    
    for user_data in MOCK_DATA["users"]:
        # Hash password
        password_hash = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            email=user_data["email"],
            password_hash=password_hash,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_verified=user_data["is_verified"],
            is_mock=True
        )
        
        session.add(user)
        await session.flush()
        
        # Create user-account association
        association = UserAccountAssociation(
            user_id=user.id,
            client_account_id=client_account_id,
            role="admin" if "admin" in user_data["email"] else "member",
            is_mock=True
        )
        session.add(association)
        
        user_ids.append(str(user.id))
        logger.info(f"Created mock user: {user.email}")
    
    return user_ids

async def create_mock_engagement(session: AsyncSession, client_account_id: str, user_id: str) -> str:
    """Create mock engagement and return its ID."""
    engagement_data = MOCK_DATA["engagements"][0]
    
    engagement = Engagement(
        client_account_id=client_account_id,
        name=engagement_data["name"],
        slug=engagement_data["slug"],
        description=engagement_data["description"],
        engagement_type=engagement_data["engagement_type"],
        status=engagement_data["status"],
        priority=engagement_data["priority"],
        start_date=datetime.utcnow(),
        target_completion_date=datetime.utcnow() + timedelta(days=365),
        engagement_lead_id=user_id,
        client_contact_name=engagement_data["client_contact_name"],
        client_contact_email=engagement_data["client_contact_email"],
        is_mock=True,
        created_by=user_id
    )
    
    session.add(engagement)
    await session.flush()
    logger.info(f"Created mock engagement: {engagement.name}")
    return str(engagement.id)

async def create_mock_tags(session: AsyncSession) -> Dict[str, str]:
    """Create mock tags and return mapping of names to IDs."""
    tag_ids = {}
    
    for tag_data in MOCK_DATA["tags"]:
        # Generate mock embedding for the tag
        embedding_text = f"{tag_data['name']} {tag_data['description']}"
        mock_embedding = generate_mock_embedding(embedding_text)
        
        tag = Tag(
            name=tag_data["name"],
            category=tag_data["category"],
            description=tag_data["description"],
            reference_embedding=json.dumps(mock_embedding),  # Convert list to JSON string
            confidence_threshold=0.7,
            is_active=True,
            usage_count=0
        )
        
        session.add(tag)
        await session.flush()
        tag_ids[tag.name] = str(tag.id)
        logger.info(f"Created mock tag: {tag.name}")
    
    return tag_ids

async def create_mock_cmdb_assets(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str, tag_ids: Dict[str, str]) -> List[str]:
    """Create mock CMDB assets with embeddings and tags."""
    asset_ids = []
    
    for asset_data in MOCK_DATA["cmdb_assets"]:
        # Create the asset
        asset = CMDBAsset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name=asset_data["name"],
            hostname=asset_data.get("hostname"),
            asset_type=asset_data["asset_type"],
            description=asset_data["description"],
            ip_address=asset_data.get("ip_address"),
            fqdn=asset_data.get("fqdn"),
            environment=asset_data["environment"],
            location=asset_data.get("location"),
            datacenter=asset_data.get("datacenter"),
            operating_system=asset_data.get("operating_system"),
            os_version=asset_data.get("os_version"),
            cpu_cores=asset_data.get("cpu_cores"),
            memory_gb=asset_data.get("memory_gb"),
            storage_gb=asset_data.get("storage_gb"),
            business_owner=asset_data.get("business_owner"),
            department=asset_data.get("department"),
            application_name=asset_data.get("application_name"),
            technology_stack=asset_data.get("technology_stack"),
            criticality=asset_data.get("criticality"),
            status=asset_data.get("status", AssetStatus.DISCOVERED),
            six_r_strategy=asset_data.get("six_r_strategy"),
            migration_complexity=asset_data.get("migration_complexity"),
            migration_wave=asset_data.get("migration_wave"),
            sixr_ready=asset_data.get("sixr_ready"),
            dependencies=asset_data.get("dependencies"),
            cpu_utilization_percent=asset_data.get("cpu_utilization_percent"),
            memory_utilization_percent=asset_data.get("memory_utilization_percent"),
            current_monthly_cost=asset_data.get("current_monthly_cost"),
            estimated_cloud_cost=asset_data.get("estimated_cloud_cost"),
            discovery_method=asset_data.get("discovery_method"),
            discovery_source=asset_data.get("discovery_source"),
            discovery_timestamp=datetime.utcnow(),
            is_mock=True,
            created_by=user_id,
            imported_by=user_id,
            imported_at=datetime.utcnow(),
            source_filename="mock_data_initialization"
        )
        
        session.add(asset)
        await session.flush()
        
        # Create embedding for the asset
        embedding_text = f"{asset.name} {asset.description} {asset.technology_stack} {asset.operating_system}"
        mock_embedding = generate_mock_embedding(embedding_text)
        
        embedding = CMDBAssetEmbedding(
            cmdb_asset_id=asset.id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            embedding=json.dumps(mock_embedding),  # Convert list to JSON string
            source_text=embedding_text,
            embedding_model="text-embedding-ada-002",
            is_mock=True
        )
        session.add(embedding)
        
        # Auto-assign tags based on asset characteristics
        assigned_tags = []
        
        if asset.asset_type == AssetType.DATABASE:
            assigned_tags.append("Database Server")
        elif asset.asset_type == AssetType.SERVER and asset.application_name and "web" in asset.application_name.lower():
            assigned_tags.append("Web Server")
        elif asset.asset_type == AssetType.APPLICATION:
            assigned_tags.append("Application Server")
        elif asset.asset_type == AssetType.NETWORK:
            assigned_tags.append("Network Device")
        elif asset.asset_type == AssetType.STORAGE:
            assigned_tags.append("Storage System")
        elif asset.asset_type == AssetType.OTHER:
            assigned_tags.append("Virtual Machine")
        
        # Business function tags
        if asset.department and "security" in asset.department.lower():
            assigned_tags.append("Security")
        elif asset.application_name and any(keyword in asset.application_name.lower() for keyword in ["customer", "portal", "public"]):
            assigned_tags.append("Customer Facing")
        elif asset.application_name and any(keyword in asset.application_name.lower() for keyword in ["internal", "crm", "erp"]):
            assigned_tags.append("Internal Tools")
        elif asset.application_name and any(keyword in asset.application_name.lower() for keyword in ["backup", "monitor"]):
            if "backup" in asset.application_name.lower():
                assigned_tags.append("Backup System")
            if "monitor" in asset.application_name.lower():
                assigned_tags.append("Monitoring")
        
        # Migration readiness tags
        if asset.six_r_strategy in [SixRStrategy.REHOST, SixRStrategy.REPLATFORM] and asset.sixr_ready == "Ready":
            assigned_tags.append("Cloud Ready")
        elif asset.operating_system and "2012" in asset.operating_system:
            assigned_tags.append("Legacy System")
        elif asset.criticality == "Critical":
            assigned_tags.append("High Availability")
        
        # Create tag associations
        for tag_name in assigned_tags:
            if tag_name in tag_ids:
                # Calculate mock confidence score based on tag relevance
                confidence = 0.8 + (hash(f"{asset.name}{tag_name}") % 20) / 100  # 0.8-0.99
                
                asset_tag = AssetTag(
                    cmdb_asset_id=asset.id,
                    tag_id=tag_ids[tag_name],
                    confidence_score=min(confidence, 0.99),
                    assigned_method="auto",
                    is_validated=False,
                    is_mock=True
                )
                session.add(asset_tag)
        
        asset_ids.append(str(asset.id))
        logger.info(f"Created mock asset: {asset.name} with {len(assigned_tags)} tags")
    
    return asset_ids

async def create_mock_sixr_analysis(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str, asset_ids: List[str]):
    """Create mock 6R analysis."""
    # Calculate summary statistics
    total_assets = len(asset_ids)
    
    analysis = SixRAnalysis(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        analysis_name="Demo Migration Analysis",
        description="Comprehensive 6R analysis for cloud migration readiness",
        status="completed",
        total_assets=total_assets,
        rehost_count=4,  # Based on our mock data
        replatform_count=3,
        refactor_count=1,
        rearchitect_count=1,
        retire_count=0,
        retain_count=1,
        total_current_cost=11700.0,  # Sum of current costs
        total_estimated_cost=8670.0,  # Sum of estimated costs
        potential_savings=3030.0,
        analysis_results={
            "summary": {
                "total_assets": total_assets,
                "cloud_ready_percentage": 70,
                "estimated_migration_duration_months": 12,
                "risk_assessment": "Medium"
            },
            "recommendations": [
                "Prioritize web servers and development systems for Wave 1 migration",
                "Plan database migration carefully with proper backup strategies",
                "Consider modernizing legacy ERP system during migration",
                "Implement proper monitoring and logging in cloud environment"
            ]
        },
        recommendations={
            "immediate_actions": [
                "Complete network security assessment",
                "Update system documentation",
                "Plan staff training for cloud technologies"
            ],
            "migration_phases": {
                "wave_1": "Non-critical systems and development environments",
                "wave_2": "Database systems with proper replication",
                "wave_3": "Customer-facing applications",
                "wave_4": "Legacy systems requiring modernization"
            }
        },
        is_mock=True,
        created_by=user_id
    )
    
    session.add(analysis)
    logger.info("Created mock 6R analysis")

async def create_mock_migration_waves(session: AsyncSession, client_account_id: str, engagement_id: str, user_id: str):
    """Create mock migration waves."""
    base_date = datetime.utcnow()
    
    waves = [
        {
            "wave_number": 1,
            "name": "Development and Non-Critical Systems",
            "description": "Migration of development environments and non-critical applications",
            "planned_start_date": base_date + timedelta(days=30),
            "planned_end_date": base_date + timedelta(days=90),
            "total_assets": 3,
            "estimated_cost": 5000.0,
            "estimated_effort_hours": 200
        },
        {
            "wave_number": 2, 
            "name": "Database and Storage Systems",
            "description": "Migration of database servers and storage infrastructure",
            "planned_start_date": base_date + timedelta(days=91),
            "planned_end_date": base_date + timedelta(days=150),
            "total_assets": 2,
            "estimated_cost": 8000.0,
            "estimated_effort_hours": 400
        },
        {
            "wave_number": 3,
            "name": "Customer-Facing Applications",
            "description": "Migration of customer portal and web applications",
            "planned_start_date": base_date + timedelta(days=151),
            "planned_end_date": base_date + timedelta(days=210),
            "total_assets": 2,
            "estimated_cost": 6000.0,
            "estimated_effort_hours": 300
        },
        {
            "wave_number": 4,
            "name": "Legacy System Modernization", 
            "description": "Modernization and migration of legacy ERP system",
            "planned_start_date": base_date + timedelta(days=211),
            "planned_end_date": base_date + timedelta(days=300),
            "total_assets": 1,
            "estimated_cost": 15000.0,
            "estimated_effort_hours": 800
        }
    ]
    
    for wave_data in waves:
        wave = MigrationWave(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            wave_number=wave_data["wave_number"],
            name=wave_data["name"],
            description=wave_data["description"],
            status="planned",
            planned_start_date=wave_data["planned_start_date"],
            planned_end_date=wave_data["planned_end_date"],
            total_assets=wave_data["total_assets"],
            completed_assets=0,
            failed_assets=0,
            estimated_cost=wave_data["estimated_cost"],
            estimated_effort_hours=wave_data["estimated_effort_hours"],
            is_mock=True,
            created_by=user_id
        )
        
        session.add(wave)
        logger.info(f"Created mock migration wave: {wave.name}")

async def initialize_mock_data():
    """Initialize the database with mock data."""
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Required dependencies not available. Cannot initialize database.")
        return False
    
    try:
        logger.info("Starting database initialization with mock data...")
        
        # Initialize database tables
        await init_db()
        logger.info("Database tables initialized")
        
        async with AsyncSessionLocal() as session:
            try:
                # Create mock data in the correct order
                logger.info("Creating mock client account...")
                client_account_id = await create_mock_client_account(session)
                
                logger.info("Creating mock users...")
                user_ids = await create_mock_users(session, client_account_id)
                admin_user_id = user_ids[1]  # Use admin user for creation
                
                logger.info("Creating mock engagement...")
                engagement_id = await create_mock_engagement(session, client_account_id, admin_user_id)
                
                logger.info("Creating mock tags...")
                tag_ids = await create_mock_tags(session)
                
                logger.info("Creating mock CMDB assets...")
                asset_ids = await create_mock_cmdb_assets(session, client_account_id, engagement_id, admin_user_id, tag_ids)
                
                logger.info("Creating mock 6R analysis...")
                await create_mock_sixr_analysis(session, client_account_id, engagement_id, admin_user_id, asset_ids)
                
                logger.info("Creating mock migration waves...")
                await create_mock_migration_waves(session, client_account_id, engagement_id, admin_user_id)
                
                # Commit all changes
                await session.commit()
                logger.info("Mock data initialization completed successfully!")
                
                # Print summary
                logger.info(f"""
                Mock Data Summary:
                - Client Account: {MOCK_DATA['client_accounts'][0]['name']}
                - Users: {len(user_ids)}
                - Engagements: 1
                - Tags: {len(tag_ids)}
                - CMDB Assets: {len(asset_ids)}
                - 6R Analyses: 1
                - Migration Waves: 4
                """)
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error during mock data creation: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

async def check_mock_data_exists():
    """Check if mock data already exists in the database."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                "SELECT COUNT(*) FROM client_accounts WHERE is_mock = true"
            )
            count = result.scalar()
            return count > 0
    except Exception:
        return False

async def main():
    """Main function to run the database initialization."""
    try:
        # Check if mock data already exists
        if await check_mock_data_exists():
            logger.info("Mock data already exists in the database. Skipping initialization.")
            print("Mock data already exists. Use --force to recreate.")
            return
        
        # Initialize mock data
        success = await initialize_mock_data()
        
        if success:
            print("✅ Database initialization completed successfully!")
            print("Mock data has been created for demonstration purposes.")
            print("\nYou can now:")
            print("1. Start the backend server")
            print("2. Access the demo data through the API")
            print("3. Use the frontend to visualize the mock migration project")
        else:
            print("❌ Database initialization failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Initialization cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 