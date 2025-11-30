"""
Model Fixtures for Integration Tests

Provides User, Client, Engagement, and populated engagement fixtures.
"""

from typing import Any, Dict
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientAccount, Engagement, User


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=uuid4(),
        username="integration_test_user",
        email="integration@test.com",
        hashed_password="test_hash",
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_client(test_session: AsyncSession) -> ClientAccount:
    """Create test client account."""
    client = ClientAccount(
        id=uuid4(),
        account_name="Integration Test Client",
        industry="Technology",
        company_size="Enterprise",
        headquarters_location="Test City",
        primary_contact_name="Test Contact",
        primary_contact_email="contact@testclient.com",
        business_objectives=["Cost Reduction", "Modernization"],
        target_cloud_providers=["aws", "azure"],
        business_priorities=["cost_reduction", "agility_speed"],
        compliance_requirements=["SOC2", "GDPR"],
    )
    test_session.add(client)
    await test_session.commit()
    await test_session.refresh(client)
    return client


@pytest.fixture
async def test_engagement(
    test_session: AsyncSession, test_user: User, test_client: ClientAccount
) -> Engagement:
    """Create test engagement."""
    engagement = Engagement(
        id=uuid4(),
        name="Integration Test Engagement",
        description="Test engagement for integration testing",
        client_id=test_client.id,
        created_by=test_user.id,
        status="active",
        scope="full_migration_assessment",
        timeline_months=6,
        budget_range="100k-500k",
    )
    test_session.add(engagement)
    await test_session.commit()
    await test_session.refresh(engagement)
    return engagement


@pytest.fixture
async def populated_engagement(
    test_session: AsyncSession,
    test_engagement: Engagement,
    integration_test_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Create engagement with populated test data."""
    from app.models.asset import Asset
    from app.models.collection_flow import CollectionFlow

    # Create collection flow
    collection_flow = CollectionFlow(
        id=uuid4(),
        engagement_id=test_engagement.id,
        user_id=test_engagement.created_by,
        client_id=test_engagement.client_id,
        status="completed",
        current_phase="completed",
        progress_percentage=100.0,
        automation_tier="tier_1",
        confidence_score=0.85,
        metadata={"asset_count": integration_test_config["test_data_sizes"]["small"]},
    )
    test_session.add(collection_flow)

    # Create test assets
    assets = []
    asset_count = integration_test_config["test_data_sizes"]["small"]

    for i in range(asset_count):
        asset = Asset(
            id=uuid4(),
            engagement_id=test_engagement.id,
            name=f"Test Asset {i+1}",
            type="application" if i % 2 == 0 else "database",
            environment="production" if i % 3 == 0 else "staging",
            business_criticality=3 + (i % 3),
            confidence_score=0.7 + (i % 3) * 0.1,
            technical_fit_score=0.8,
            status="active",
            metadata={"test_asset": True},
        )
        test_session.add(asset)
        assets.append(asset)

    await test_session.commit()

    # Refresh objects
    await test_session.refresh(collection_flow)
    for asset in assets:
        await test_session.refresh(asset)

    return {
        "engagement": test_engagement,
        "collection_flow": collection_flow,
        "assets": assets,
        "asset_count": asset_count,
    }
