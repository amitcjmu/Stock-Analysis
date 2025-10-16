"""
Test fixtures for enrichment integration tests.

Provides sample assets, test database setup, and mock data for enrichment testing.
"""

import pytest
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset


@pytest.fixture
def client_account_id() -> UUID:
    """Test client account ID for tenant scoping"""
    return uuid4()


@pytest.fixture
def engagement_id() -> UUID:
    """Test engagement ID for tenant scoping"""
    return uuid4()


@pytest.fixture
async def sample_assets(
    async_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
) -> List[Asset]:
    """
    Create diverse sample assets for enrichment testing.

    Includes:
    - Web servers (Apache, Nginx)
    - Databases (PostgreSQL, MySQL)
    - Applications (Java, Node.js, Python)
    - Network devices (Cisco routers, firewalls)

    Each asset has varying levels of metadata to test enrichment
    in different data quality scenarios.
    """
    assets = [
        # Asset 1: Well-populated web server
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Web Server - Production",
            asset_type="server",
            technology_stack="Apache Tomcat 9.0",
            operating_system="Linux Ubuntu 22.04 LTS",
            environment="production",
            data_sensitivity="high",
            location="us-east-1",
            cpu_cores=8,
            memory_gb=32,
            storage_gb=500,
            business_criticality="critical",
            assessment_readiness="not_ready",
            assessment_readiness_score=0.3,
        ),
        # Asset 2: Database with minimal metadata
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Customer Database",
            asset_type="database",
            technology_stack="PostgreSQL 14",
            data_sensitivity="high",
            # Missing: operating_system, environment, location, resources
            assessment_readiness="not_ready",
            assessment_readiness_score=0.2,
        ),
        # Asset 3: Application with partial metadata
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="CRM Application",
            asset_type="application",
            technology_stack="Java Spring Boot",
            operating_system="Linux",
            environment="production",
            business_criticality="high",
            application_type="web_application",
            # Missing: data_sensitivity, location, resources
            assessment_readiness="not_ready",
            assessment_readiness_score=0.4,
        ),
        # Asset 4: Network device
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Edge Router 01",
            asset_type="network_device",
            technology_stack="Cisco IOS",
            environment="production",
            location="datacenter-1",
            business_criticality="critical",
            assessment_readiness="not_ready",
            assessment_readiness_score=0.35,
        ),
        # Asset 5: Node.js application
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="API Gateway",
            asset_type="application",
            technology_stack="Node.js Express",
            operating_system="Linux Alpine",
            environment="production",
            data_sensitivity="medium",
            cpu_cores=4,
            memory_gb=16,
            assessment_readiness="not_ready",
            assessment_readiness_score=0.45,
        ),
        # Asset 6: MySQL database
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Analytics Database",
            asset_type="database",
            technology_stack="MySQL 8.0",
            operating_system="Linux",
            environment="staging",
            data_sensitivity="low",
            storage_gb=1000,
            assessment_readiness="not_ready",
            assessment_readiness_score=0.3,
        ),
        # Asset 7: Python application
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="ML Processing Pipeline",
            asset_type="application",
            technology_stack="Python 3.11 FastAPI",
            operating_system="Linux Ubuntu",
            environment="production",
            data_sensitivity="high",
            business_criticality="high",
            cpu_cores=16,
            memory_gb=64,
            assessment_readiness="not_ready",
            assessment_readiness_score=0.5,
        ),
        # Asset 8: Firewall device
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Perimeter Firewall",
            asset_type="network_device",
            technology_stack="Palo Alto Networks",
            environment="production",
            location="datacenter-1",
            business_criticality="critical",
            assessment_readiness="not_ready",
            assessment_readiness_score=0.4,
        ),
        # Asset 9: Legacy application (minimal data)
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Legacy Billing System",
            asset_type="application",
            technology_stack="Java EE 7",
            # Missing: most metadata
            assessment_readiness="not_ready",
            assessment_readiness_score=0.15,
        ),
        # Asset 10: Redis cache server
        Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Cache Server",
            asset_type="database",
            technology_stack="Redis 7.0",
            operating_system="Linux",
            environment="production",
            data_sensitivity="low",
            cpu_cores=4,
            memory_gb=32,
            assessment_readiness="not_ready",
            assessment_readiness_score=0.4,
        ),
    ]

    # Add all assets to session
    for asset in assets:
        async_db_session.add(asset)

    await async_db_session.commit()

    # Refresh all assets to get generated IDs
    for asset in assets:
        await async_db_session.refresh(asset)

    return assets


@pytest.fixture
async def minimal_asset(
    async_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
) -> Asset:
    """
    Create a minimal asset with very little metadata.

    Used to test enrichment graceful handling of missing data.
    """
    asset = Asset(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="Minimal Test Asset",
        asset_type="server",
        # Only required fields populated
        assessment_readiness="not_ready",
        assessment_readiness_score=0.1,
    )

    async_db_session.add(asset)
    await async_db_session.commit()
    await async_db_session.refresh(asset)

    return asset


@pytest.fixture
async def performance_test_assets(
    async_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
) -> List[Asset]:
    """
    Create 50 assets for performance testing.

    Diverse mix of asset types to simulate real-world enrichment load.
    """
    assets = []
    asset_types = ["server", "database", "application", "network_device"]
    tech_stacks = [
        "Apache Tomcat",
        "PostgreSQL",
        "Java Spring Boot",
        "Cisco IOS",
        "Node.js",
        "MySQL",
        "Python FastAPI",
        "Nginx",
        "MongoDB",
        "React",
    ]

    for i in range(50):
        asset = Asset(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name=f"Performance Test Asset {i:03d}",
            asset_type=asset_types[i % len(asset_types)],
            technology_stack=tech_stacks[i % len(tech_stacks)],
            operating_system="Linux" if i % 3 != 0 else "Windows",
            environment=["production", "staging", "development"][i % 3],
            data_sensitivity=["high", "medium", "low"][i % 3],
            business_criticality=["critical", "high", "medium", "low"][i % 4],
            cpu_cores=(i % 8) + 2,
            memory_gb=(i % 16) * 4 + 8,
            storage_gb=(i % 10) * 100 + 100,
            assessment_readiness="not_ready",
            assessment_readiness_score=0.3 + (i % 5) * 0.1,
        )
        assets.append(asset)
        async_db_session.add(asset)

    await async_db_session.commit()

    # Refresh all assets
    for asset in assets:
        await async_db_session.refresh(asset)

    return assets
