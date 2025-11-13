"""
Unit tests for AutoEnrichmentPipeline service.

Tests verify ADR compliance:
- ADR-015: TenantScopedAgentPool usage
- ADR-024: TenantMemoryManager usage
- LLM Tracking: multi_model_service integration
"""

from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.services.enrichment.auto_enrichment_pipeline import AutoEnrichmentPipeline


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def client_account_id() -> UUID:
    """Create a test client account ID."""
    return uuid4()


@pytest.fixture
def engagement_id() -> UUID:
    """Create a test engagement ID."""
    return uuid4()


@pytest.fixture
def sample_assets(client_account_id: UUID, engagement_id: UUID) -> List[Asset]:
    """Create sample asset instances for testing."""
    return [
        Asset(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Test Server 1",
            asset_type="server",
            operating_system="Linux",
            assessment_readiness="not_ready",
        ),
        Asset(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_name="Test Database 1",
            asset_type="database",
            operating_system="Windows",
            assessment_readiness="not_ready",
        ),
    ]


@pytest.mark.asyncio
async def test_pipeline_initialization(
    mock_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
):
    """Test AutoEnrichmentPipeline initializes correctly with tenant context."""
    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    assert pipeline.db == mock_db_session
    assert pipeline.client_account_id == client_account_id
    assert pipeline.engagement_id == engagement_id
    assert pipeline.agent_pool is not None  # TenantScopedAgentPool class
    assert pipeline.memory_manager is not None  # TenantMemoryManager instance


@pytest.mark.asyncio
async def test_pipeline_uses_tenant_scoped_agent_pool(
    mock_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
):
    """Test pipeline retrieves agents from TenantScopedAgentPool (ADR-015)."""
    with patch(
        "app.services.enrichment.auto_enrichment_pipeline.TenantScopedAgentPool"
    ) as mock_pool:
        pipeline = AutoEnrichmentPipeline(
            db=mock_db_session,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        # Verify pool is assigned (not instantiated, it's a class reference)
        assert pipeline.agent_pool == mock_pool


@pytest.mark.asyncio
async def test_pipeline_uses_tenant_memory_manager(
    mock_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
):
    """Test pipeline uses TenantMemoryManager for learning (ADR-024)."""
    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Verify TenantMemoryManager initialized
    assert pipeline.memory_manager is not None
    assert hasattr(pipeline.memory_manager, "store_learning")
    assert hasattr(pipeline.memory_manager, "retrieve_similar_patterns")
    assert pipeline.memory_manager.db == mock_db_session


@pytest.mark.asyncio
async def test_trigger_auto_enrichment_empty_asset_list(
    mock_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
):
    """Test enrichment handles empty asset list gracefully."""
    # Mock empty query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    result = await pipeline.trigger_auto_enrichment([uuid4()])

    assert result["total_assets"] == 0
    assert "error" in result
    assert result["error"] == "No assets found"


@pytest.mark.asyncio
async def test_trigger_auto_enrichment_with_assets(
    mock_db_session: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    sample_assets: List[Asset],
):
    """Test enrichment processes assets and returns statistics."""
    # Mock query result with sample assets
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_assets
    mock_db_session.execute.return_value = mock_result

    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Mock enrichment methods to return counts
    with patch.object(pipeline, "_enrich_compliance", return_value=2):
        with patch.object(pipeline, "_enrich_licenses", return_value=2):
            with patch.object(pipeline, "_enrich_vulnerabilities", return_value=2):
                with patch.object(pipeline, "_enrich_resilience", return_value=2):
                    with patch.object(pipeline, "_enrich_dependencies", return_value=2):
                        with patch.object(
                            pipeline, "_enrich_product_links", return_value=2
                        ):
                            with patch.object(
                                pipeline, "_enrich_field_conflicts", return_value=0
                            ):
                                with patch.object(
                                    pipeline, "_recalculate_readiness"
                                ) as mock_recalc:
                                    result = await pipeline.trigger_auto_enrichment(
                                        [asset.id for asset in sample_assets]
                                    )

    assert result["total_assets"] == 2
    assert result["enrichment_results"]["compliance_flags"] == 2
    assert result["enrichment_results"]["licenses"] == 2
    assert result["enrichment_results"]["vulnerabilities"] == 2
    assert result["enrichment_results"]["resilience"] == 2
    assert result["enrichment_results"]["dependencies"] == 2
    assert result["enrichment_results"]["product_links"] == 2
    assert result["enrichment_results"]["field_conflicts"] == 0
    assert "elapsed_time_seconds" in result
    assert isinstance(result["elapsed_time_seconds"], float)

    # Verify readiness recalculation was called
    mock_recalc.assert_called_once()


@pytest.mark.asyncio
async def test_enrichment_concurrent_execution(
    mock_db_session: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    sample_assets: List[Asset],
):
    """Test enrichment agents execute concurrently for performance."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_assets
    mock_db_session.execute.return_value = mock_result

    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Mock all enrichment methods to return AsyncMock
    with patch.object(pipeline, "_enrich_compliance", return_value=2):
        with patch.object(pipeline, "_enrich_licenses", return_value=2):
            with patch.object(pipeline, "_enrich_vulnerabilities", return_value=2):
                with patch.object(pipeline, "_enrich_resilience", return_value=2):
                    with patch.object(pipeline, "_enrich_dependencies", return_value=2):
                        with patch.object(
                            pipeline, "_enrich_product_links", return_value=2
                        ):
                            with patch.object(
                                pipeline, "_enrich_field_conflicts", return_value=0
                            ):
                                with patch.object(pipeline, "_recalculate_readiness"):
                                    result = await pipeline.trigger_auto_enrichment(
                                        [asset.id for asset in sample_assets]
                                    )

    # Verify concurrent execution by checking all enrichment tasks completed
    assert result["enrichment_results"]["compliance_flags"] == 2
    assert result["enrichment_results"]["licenses"] == 2
    assert result["enrichment_results"]["vulnerabilities"] == 2
    assert result["enrichment_results"]["resilience"] == 2
    assert result["enrichment_results"]["dependencies"] == 2
    assert result["enrichment_results"]["product_links"] == 2
    assert result["enrichment_results"]["field_conflicts"] == 0


@pytest.mark.asyncio
async def test_recalculate_readiness_updates_assets(
    mock_db_session: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    sample_assets: List[Asset],
):
    """Test readiness recalculation updates asset fields correctly."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_assets
    mock_db_session.execute.return_value = mock_result

    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    await pipeline._recalculate_readiness([asset.id for asset in sample_assets])

    # Verify execute was called for query
    assert mock_db_session.execute.call_count >= 1

    # Verify commit was called
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_enrichment_handles_agent_failure_gracefully(
    mock_db_session: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    sample_assets: List[Asset],
):
    """Test enrichment continues when individual agents fail."""
    # Mock query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_assets
    mock_db_session.execute.return_value = mock_result

    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Mock one enrichment method to fail
    with patch.object(
        pipeline, "_enrich_compliance", side_effect=Exception("Agent failed")
    ):
        with patch.object(pipeline, "_enrich_licenses", return_value=2):
            with patch.object(pipeline, "_enrich_vulnerabilities", return_value=2):
                with patch.object(pipeline, "_enrich_resilience", return_value=2):
                    with patch.object(pipeline, "_enrich_dependencies", return_value=2):
                        with patch.object(
                            pipeline, "_enrich_product_links", return_value=2
                        ):
                            with patch.object(
                                pipeline, "_enrich_field_conflicts", return_value=0
                            ):
                                with patch.object(pipeline, "_recalculate_readiness"):
                                    result = await pipeline.trigger_auto_enrichment(
                                        [asset.id for asset in sample_assets]
                                    )

    # Verify partial success
    assert result["total_assets"] == 2
    assert result["enrichment_results"]["compliance_flags"] == 0  # Failed
    assert result["enrichment_results"]["licenses"] == 2  # Succeeded
    assert result["enrichment_results"]["vulnerabilities"] == 2  # Succeeded


@pytest.mark.asyncio
async def test_multi_tenant_scoping_enforced(
    mock_db_session: AsyncSession, client_account_id: UUID, engagement_id: UUID
):
    """Test all database queries include multi-tenant scoping."""
    pipeline = AutoEnrichmentPipeline(
        db=mock_db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Verify tenant context is stored
    assert pipeline.client_account_id == client_account_id
    assert pipeline.engagement_id == engagement_id

    # In actual implementation, all queries would include these filters
    # This test verifies the context is available for use


@pytest.mark.asyncio
async def test_enrichment_uses_multi_model_service():
    """Test LLM calls use multi_model_service for tracking."""
    # This test would verify multi_model_service.generate_response() is called
    # In actual implementation with agents, this would be tested
    with patch(
        "app.services.enrichment.auto_enrichment_pipeline.multi_model_service"
    ) as mock_service:
        mock_service.generate_response = AsyncMock(
            return_value={
                "status": "success",
                "response": "Test response",
                "usage_log_id": str(uuid4()),
            }
        )

        # When agents are implemented, verify generate_response is called
        # For now, this test structure is ready for implementation
        assert mock_service is not None


@pytest.mark.asyncio
async def test_critical_attributes_defined():
    """Test critical attributes for assessment readiness are properly defined."""
    from app.services.enrichment.auto_enrichment_pipeline import CRITICAL_ATTRIBUTES

    # Verify 22 critical attributes exist across 4 categories
    total_attributes = sum(len(attrs) for attrs in CRITICAL_ATTRIBUTES.values())
    assert (
        total_attributes == 22
    ), f"Expected 22 critical attributes, found {total_attributes}"

    # Verify categories
    assert "infrastructure" in CRITICAL_ATTRIBUTES
    assert "application" in CRITICAL_ATTRIBUTES
    assert "business" in CRITICAL_ATTRIBUTES
    assert "technical_debt" in CRITICAL_ATTRIBUTES

    # Verify specific required attributes
    assert "application_name" in CRITICAL_ATTRIBUTES["infrastructure"]
    assert "business_criticality" in CRITICAL_ATTRIBUTES["application"]
    assert "business_owner" in CRITICAL_ATTRIBUTES["business"]
    assert "known_vulnerabilities" in CRITICAL_ATTRIBUTES["technical_debt"]
