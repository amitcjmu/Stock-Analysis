"""
Data population operations for demo data seeding.
Handles creation of assets and canonical applications.
"""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, CanonicalApplication
from .base import BaseDemoSeeder


class DataPopulator(BaseDemoSeeder):
    """Manages demo data population for assets and applications"""

    async def populate_assets_table(self, db: AsyncSession, flow_ids: List[str]) -> int:
        """Populate assets table with demo data and proper discovered_at timestamps"""
        print("💾 Populating assets table...")

        # Check if assets already exist for this tenant
        result = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.client_account_id == self.demo_client_id,
                Asset.engagement_id == self.demo_engagement_id,
            )
        )
        existing_count = result.scalar()

        if existing_count > 0:
            print(f"  ⚠️ Found {existing_count} existing assets, skipping population")
            return existing_count

        # Demo asset data with proper multi-tenant scoping
        demo_assets = self._get_demo_assets_data()

        # Add assets with proper multi-tenant scoping and discovered_at timestamps
        assets_created = 0
        base_time = datetime.now(timezone.utc)

        for i, asset_data in enumerate(demo_assets):
            # Use different flow IDs for variety, or None if not enough flows
            flow_id = flow_ids[i % len(flow_ids)] if flow_ids else None
            discovery_flow_id = flow_id if flow_id else None
            master_flow_id = flow_id if flow_id else None

            # Stagger discovered_at timestamps to simulate real discovery over time
            discovered_at = base_time.replace(hour=base_time.hour - (i * 2))

            asset = Asset(
                id=uuid.uuid4(),
                client_account_id=self.demo_client_id,
                engagement_id=self.demo_engagement_id,
                flow_id=flow_id,
                master_flow_id=master_flow_id,
                discovery_flow_id=discovery_flow_id,
                source_phase="asset_inventory",
                current_phase="completed",
                discovered_at=discovered_at,  # This is the new column we added
                discovery_timestamp=discovered_at,  # Legacy column for backward compatibility
                imported_at=discovered_at,
                **asset_data,
            )

            db.add(asset)
            assets_created += 1

        await db.commit()
        print(f"✅ Created {assets_created} demo assets")
        return assets_created

    async def populate_canonical_applications(self, db: AsyncSession) -> int:
        """Populate canonical_applications table for Collection flow"""
        print("📱 Populating canonical applications...")

        # Check if canonical applications already exist for this tenant
        result = await db.execute(
            select(func.count(CanonicalApplication.id)).where(
                CanonicalApplication.client_account_id == self.demo_client_id,
                CanonicalApplication.engagement_id == self.demo_engagement_id,
            )
        )
        existing_count = result.scalar()

        if existing_count > 0:
            print(
                f"  ⚠️ Found {existing_count} existing canonical applications, skipping population"
            )
            return existing_count

        # Demo canonical applications matching the assets
        demo_applications = self._get_demo_applications_data()

        # Create canonical applications with proper multi-tenant scoping
        apps_created = 0

        for app_data in demo_applications:
            canonical_app = CanonicalApplication(
                id=uuid.uuid4(),
                client_account_id=self.demo_client_id,
                engagement_id=self.demo_engagement_id,
                created_by=self.demo_user_id,
                **app_data,
            )

            db.add(canonical_app)
            apps_created += 1

        await db.commit()
        print(f"✅ Created {apps_created} canonical applications")
        return apps_created

    def _get_demo_assets_data(self) -> List[dict]:
        """Get demo asset data"""
        return [
            {
                "name": "Web Frontend Server - Production",
                "asset_name": "web-frontend-prod",
                "hostname": "web-prod-01.demo-corp.com",
                "asset_type": "server",
                "description": "Production web frontend server hosting customer portal",
                "ip_address": "10.0.1.10",
                "operating_system": "Ubuntu 20.04 LTS",
                "cpu_cores": 8,
                "memory_gb": 32.0,
                "storage_gb": 500.0,
                "environment": "production",
                "datacenter": "Primary DC",
                "business_owner": "IT Operations",
                "technical_owner": "John Smith",
                "department": "IT",
                "application_name": "Customer Portal",
                "technology_stack": "React, Node.js, PostgreSQL",
                "criticality": "high",
                "business_criticality": "high",
                "six_r_strategy": "rehost",
                "migration_priority": 1,
                "migration_complexity": "medium",
                "migration_wave": 1,
                "status": "active",
                "migration_status": "not_started",
            },
            {
                "name": "Database Server - Customer Data",
                "asset_name": "db-customer-prod",
                "hostname": "db-prod-01.demo-corp.com",
                "asset_type": "database",
                "description": "Primary customer database server",
                "ip_address": "10.0.1.20",
                "operating_system": "CentOS 7",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "storage_gb": 2000.0,
                "environment": "production",
                "datacenter": "Primary DC",
                "business_owner": "Data Team",
                "technical_owner": "Sarah Johnson",
                "department": "Engineering",
                "application_name": "Customer Database",
                "technology_stack": "PostgreSQL 13",
                "criticality": "critical",
                "business_criticality": "critical",
                "six_r_strategy": "replatform",
                "migration_priority": 2,
                "migration_complexity": "high",
                "migration_wave": 1,
                "status": "active",
                "migration_status": "not_started",
            },
            {
                "name": "Analytics Processing Server",
                "asset_name": "analytics-batch-01",
                "hostname": "analytics-01.demo-corp.com",
                "asset_type": "application",
                "description": "Batch analytics processing server for business intelligence",
                "ip_address": "10.0.2.10",
                "operating_system": "Red Hat Enterprise Linux 8",
                "cpu_cores": 12,
                "memory_gb": 48.0,
                "storage_gb": 1000.0,
                "environment": "production",
                "datacenter": "Secondary DC",
                "business_owner": "Business Intelligence",
                "technical_owner": "Mike Wilson",
                "department": "Analytics",
                "application_name": "Business Intelligence Suite",
                "technology_stack": "Apache Spark, Hadoop, Python",
                "criticality": "medium",
                "business_criticality": "medium",
                "six_r_strategy": "refactor",
                "migration_priority": 3,
                "migration_complexity": "high",
                "migration_wave": 2,
                "status": "active",
                "migration_status": "not_started",
            },
            {
                "name": "Legacy ERP System",
                "asset_name": "erp-legacy-01",
                "hostname": "erp-main.demo-corp.com",
                "asset_type": "application",
                "description": "Legacy ERP system for financial and operational data",
                "ip_address": "10.0.1.30",
                "operating_system": "Windows Server 2016",
                "cpu_cores": 8,
                "memory_gb": 24.0,
                "storage_gb": 800.0,
                "environment": "production",
                "datacenter": "Primary DC",
                "business_owner": "Finance",
                "technical_owner": "Lisa Chen",
                "department": "Finance",
                "application_name": "Enterprise Resource Planning",
                "technology_stack": ".NET Framework, SQL Server",
                "criticality": "high",
                "business_criticality": "high",
                "six_r_strategy": "replace",
                "migration_priority": 4,
                "migration_complexity": "very_high",
                "migration_wave": 3,
                "status": "active",
                "migration_status": "not_started",
            },
            {
                "name": "Development Environment Server",
                "asset_name": "dev-env-01",
                "hostname": "dev-01.demo-corp.com",
                "asset_type": "server",
                "description": "Development environment for application testing",
                "ip_address": "10.0.3.10",
                "operating_system": "Ubuntu 22.04 LTS",
                "cpu_cores": 4,
                "memory_gb": 16.0,
                "storage_gb": 200.0,
                "environment": "development",
                "datacenter": "Primary DC",
                "business_owner": "Engineering",
                "technical_owner": "Development Team",
                "department": "Engineering",
                "application_name": "Development Tools",
                "technology_stack": "Docker, Kubernetes, Various",
                "criticality": "low",
                "business_criticality": "low",
                "six_r_strategy": "retire",
                "migration_priority": 5,
                "migration_complexity": "low",
                "migration_wave": 3,
                "status": "active",
                "migration_status": "not_started",
            },
        ]

    def _get_demo_applications_data(self) -> List[dict]:
        """Get demo canonical applications data"""
        return [
            {
                "canonical_name": "Customer Portal",
                "description": "Web-based customer portal for account management and services",
                "application_type": "web_application",
                "business_criticality": "high",
                "technology_stack": {
                    "frontend": ["React", "TypeScript"],
                    "backend": ["Node.js", "Express"],
                    "database": ["PostgreSQL"],
                    "infrastructure": ["Docker", "Nginx"],
                },
                "confidence_score": 0.95,
                "is_verified": True,
                "verification_source": "asset_inventory",
            },
            {
                "canonical_name": "Customer Database",
                "description": "Primary database storing customer information and transactions",
                "application_type": "database",
                "business_criticality": "critical",
                "technology_stack": {
                    "database": ["PostgreSQL 13"],
                    "backup": ["pg_dump", "WAL-E"],
                    "monitoring": ["pgAdmin", "DataDog"],
                },
                "confidence_score": 1.0,
                "is_verified": True,
                "verification_source": "asset_inventory",
            },
            {
                "canonical_name": "Business Intelligence Suite",
                "description": "Analytics and reporting platform for business insights",
                "application_type": "analytics",
                "business_criticality": "medium",
                "technology_stack": {
                    "processing": ["Apache Spark", "Hadoop"],
                    "languages": ["Python", "Scala"],
                    "visualization": ["Tableau", "Power BI"],
                },
                "confidence_score": 0.90,
                "is_verified": True,
                "verification_source": "asset_inventory",
            },
            {
                "canonical_name": "Enterprise Resource Planning",
                "description": "Legacy ERP system managing financial and operational processes",
                "application_type": "erp",
                "business_criticality": "high",
                "technology_stack": {
                    "framework": [".NET Framework 4.8"],
                    "database": ["SQL Server 2016"],
                    "platform": ["Windows Server 2016"],
                },
                "confidence_score": 0.85,
                "is_verified": True,
                "verification_source": "asset_inventory",
            },
            {
                "canonical_name": "Development Tools",
                "description": "Development environment and tooling infrastructure",
                "application_type": "development",
                "business_criticality": "low",
                "technology_stack": {
                    "containers": ["Docker", "Kubernetes"],
                    "ci_cd": ["Jenkins", "GitLab CI"],
                    "monitoring": ["Prometheus", "Grafana"],
                },
                "confidence_score": 0.80,
                "is_verified": False,
                "verification_source": "automated_discovery",
            },
        ]
