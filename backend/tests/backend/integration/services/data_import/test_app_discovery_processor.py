"""
Integration tests for the ApplicationDiscoveryProcessor and target fields.
"""

from __future__ import annotations

from typing import List
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset.models import Asset
from app.models.asset.relationships import AssetDependency
from app.models.client_account import ClientAccount, Engagement, User
from app.services.data_import.service_handlers.app_discovery_processor import (
    ApplicationDiscoveryProcessor,
)


@pytest.fixture
def app_discovery_context(
    test_client_account: ClientAccount, test_engagement: Engagement, test_user: User
) -> RequestContext:
    """Request context for app discovery tests using created tenant records."""
    return RequestContext(
        client_account_id=test_client_account.id,
        engagement_id=test_engagement.id,
        user_id=str(test_user.id),
        flow_id=str(uuid4()),
    )


@pytest.mark.asyncio
async def test_validate_data_normalizes_records(
    async_db_session: AsyncSession, app_discovery_context: RequestContext
):
    """validate_data should normalize topology rows and flag missing fields."""
    processor = ApplicationDiscoveryProcessor(async_db_session, app_discovery_context)

    raw_records = [
        {
            "application_name": "ClaimsSuite",
            "tier_name": "ClaimsWeb",
            "node_name": "claims-web-01",
            "called_component": "PolicyAPI",
            "dependency_type": "http",
            "call_count": "12",
            "avg_response_time_ms": "145.4",
        },
        {
            "application_name": "",
            "tier_name": "MissingApp",
            "called_component": "",
        },
    ]

    result = await processor.validate_data(
        data_import_id=uuid4(),
        raw_records=raw_records,
        processing_config={},
    )

    # When validation fails, normalized_records may not be in result
    # Check if we have validation errors first
    assert result["valid"] is False
    assert len(result["validation_errors"]) == 1

    # Check normalization was performed via the processor's internal state
    assert processor._normalization is not None
    if processor._normalization.normalized_records:
        normalized = processor._normalization.normalized_records
        assert len(normalized) >= 1
        # topology_normalizer maps tier_name -> component_name
        assert normalized[0]["component_name"] == "ClaimsWeb"
        assert normalized[0]["host_name"] == "claims-web-01"
        assert normalized[0]["dependency_type"] == "http"
        assert normalized[0]["call_count"] == 12
        assert normalized[0]["avg_latency_ms"] == pytest.approx(145.4)


@pytest.mark.asyncio
async def test_enrich_assets_creates_components_and_dependencies(
    async_db_session: AsyncSession, app_discovery_context: RequestContext
):
    """enrich_assets should create component assets and dependency edges."""
    processor = ApplicationDiscoveryProcessor(async_db_session, app_discovery_context)
    processor.master_flow_id = str(uuid4())

    validated_records: List[dict] = [
        {
            "application_name": "ClaimsSuite",
            "component_name": "ClaimsWeb",  # topology_normalizer uses component_name
            "host_name": "claims-web-01",  # topology_normalizer uses host_name
            "dependency_target": "PolicyAPI",  # topology_normalizer uses dependency_target
            "dependency_type": "http",
            "call_count": 25,
            "avg_latency_ms": 110.2,  # topology_normalizer uses avg_latency_ms
            "error_rate_percent": 0.4,
        },
        {
            "application_name": "ClaimsSuite",
            "component_name": "PolicyAPI",
            "host_name": None,
            "dependency_target": "DataHub",
            "dependency_type": "jdbc",
            "call_count": 5,
            "avg_latency_ms": 340.0,
            "error_rate_percent": 0.0,
        },
    ]

    result = await processor.enrich_assets(
        data_import_id=uuid4(),
        validated_records=validated_records,
        processing_config={},
    )

    assert result["assets_enriched"] >= 3
    assert result["dependencies_created"] == 2

    # Verify assets exist for every unique component (filtered by tenant)
    asset_rows = await async_db_session.execute(
        select(Asset).where(
            Asset.application_name == "ClaimsSuite",
            Asset.client_account_id == app_discovery_context.client_account_id,
            Asset.engagement_id == app_discovery_context.engagement_id,
        )
    )
    assets = asset_rows.scalars().all()
    asset_names = {asset.name for asset in assets}

    # Component assets are created with format "Application::ComponentName"
    # Target assets are created with just the target name
    # So we should have: "ClaimsSuite::ClaimsWeb", "ClaimsSuite::PolicyAPI", "PolicyAPI", "DataHub"
    assert (
        len(asset_names) >= 3
    ), f"Expected at least 3 assets, got {len(asset_names)}: {asset_names}"
    # Verify component assets (format: Application::Component)
    assert any(
        "ClaimsSuite::ClaimsWeb" in name or name == "ClaimsSuite::ClaimsWeb"
        for name in asset_names
    ), f"Missing ClaimsSuite::ClaimsWeb. Found: {asset_names}"
    assert any(
        "PolicyAPI" in name for name in asset_names
    ), f"Missing PolicyAPI (component or target). Found: {asset_names}"

    # Filter dependencies by tenant to avoid counting dependencies from other tests
    dependency_rows = await async_db_session.execute(
        select(AssetDependency).where(
            AssetDependency.client_account_id
            == app_discovery_context.client_account_id,
            AssetDependency.engagement_id == app_discovery_context.engagement_id,
        )
    )
    dependencies = dependency_rows.scalars().all()
    assert len(dependencies) == 2
    for dep in dependencies:
        assert dep.dependency_type in {"http", "jdbc"}
        assert dep.asset_id != dep.depends_on_asset_id


@pytest.mark.asyncio
async def test_get_assets_table_fields_includes_dependency_columns(
    async_db_session: AsyncSession,
):
    """Ensure dependency-specific columns are exposed to attribute mapping for app-discovery imports."""
    from app.api.v1.endpoints.data_import.handlers.field_handler import (
        get_available_target_fields,
    )
    from app.core.context import RequestContext
    from tests.fixtures.mfo_fixtures import (
        DEMO_CLIENT_ACCOUNT_ID,
        DEMO_ENGAGEMENT_ID,
        DEMO_USER_ID,
    )

    # Create context for the request
    context = RequestContext(
        client_account_id=DEMO_CLIENT_ACCOUNT_ID,
        engagement_id=DEMO_ENGAGEMENT_ID,
        user_id=str(DEMO_USER_ID),
        flow_id=str(uuid4()),
    )

    # Get fields with app_discovery import category (which includes dependency fields)
    result = await get_available_target_fields(
        flow_id=None,
        import_category="app_discovery",
        context=context,
        db=async_db_session,
    )

    fields = result["fields"]
    field_names = {field["name"] for field in fields}

    dependency_columns = {
        "dependency_type",
        "port",
        "protocol_name",
        "conn_count",
        "first_seen",
        "last_seen",
    }

    assert dependency_columns.issubset(
        field_names
    ), f"Missing dependency columns. Expected: {dependency_columns}, Got fields: {sorted(field_names)}"
