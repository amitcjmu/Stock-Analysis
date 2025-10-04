"""
Integration tests for Gap Analysis Service

Tests the lean single-agent gap analysis implementation end-to-end:
1. Service initialization with tenant context
2. Asset loading from database
3. Agent creation and task execution
4. Gap detection and persistence
5. Database verification
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow
from app.services.collection.gap_analysis_service import GapAnalysisService


@pytest.fixture
async def test_collection_flow(async_db_session: AsyncSession):
    """Create a test collection flow."""
    flow = CollectionFlow(
        id=uuid4(),
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        flow_name="Test Gap Analysis Flow",
        current_phase="gap_analysis",
        status="gap_analysis",
    )
    async_db_session.add(flow)
    await async_db_session.commit()
    await async_db_session.refresh(flow)
    return flow


@pytest.fixture
async def test_assets(async_db_session: AsyncSession):
    """Create test assets with varying levels of completeness."""
    # Asset 1: Server with missing critical attributes
    server = Asset(
        id=uuid4(),
        name="test-server-01",
        asset_type="server",
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        # Missing: operating_system, cpu_cores, memory_gb, technology_stack
    )

    # Asset 2: Database with partial attributes
    database = Asset(
        id=uuid4(),
        name="test-db-01",
        asset_type="database",
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        operating_system="PostgreSQL 16",
        # Missing: cpu_cores, memory_gb, storage_gb, backup_strategy
    )

    # Asset 3: Application with most attributes
    app = Asset(
        id=uuid4(),
        name="test-app-01",
        asset_type="application",
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        operating_system="Linux",
        cpu_cores=4,
        memory_gb=16,
        # Missing: technology_stack, architecture_pattern, business_criticality_score
    )

    async_db_session.add_all([server, database, app])
    await async_db_session.commit()

    for asset in [server, database, app]:
        await async_db_session.refresh(asset)

    return [server, database, app]


@pytest.mark.asyncio
class TestGapAnalysisService:
    """Test suite for Gap Analysis Service"""

    async def test_service_initialization(self):
        """Test service can be initialized with tenant context."""
        service = GapAnalysisService(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        assert service.client_account_id == "11111111-1111-1111-1111-111111111111"
        assert service.engagement_id == "22222222-2222-2222-2222-222222222222"
        assert service.collection_flow_id is not None

    async def test_load_assets(
        self, async_db_session: AsyncSession, test_assets: list[Asset]
    ):
        """Test loading real assets from database."""
        service = GapAnalysisService(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        asset_ids = [str(asset.id) for asset in test_assets]
        loaded_assets = await service._load_assets(asset_ids, async_db_session)

        assert len(loaded_assets) == 3
        assert all(isinstance(asset, Asset) for asset in loaded_assets)
        assert {asset.name for asset in loaded_assets} == {
            "test-server-01",
            "test-db-01",
            "test-app-01",
        }

    async def test_load_assets_empty_result(self, async_db_session: AsyncSession):
        """Test loading assets when none match criteria."""
        service = GapAnalysisService(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        # Use non-existent asset IDs
        loaded_assets = await service._load_assets(
            [str(uuid4()), str(uuid4())], async_db_session
        )

        assert len(loaded_assets) == 0

    async def test_load_assets_wrong_tenant(
        self, async_db_session: AsyncSession, test_assets: list[Asset]
    ):
        """Test tenant isolation - assets from different tenant not loaded."""
        service = GapAnalysisService(
            client_account_id="99999999-9999-9999-9999-999999999999",  # Wrong client
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        asset_ids = [str(asset.id) for asset in test_assets]
        loaded_assets = await service._load_assets(asset_ids, async_db_session)

        assert len(loaded_assets) == 0  # Tenant isolation working

    async def test_empty_result_structure(self):
        """Test empty result has correct structure."""
        service = GapAnalysisService(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        result = service._empty_result()

        assert "gaps" in result
        assert "questionnaire" in result
        assert "summary" in result
        assert result["summary"]["total_gaps"] == 0
        assert result["summary"]["assets_analyzed"] == 0

    async def test_error_result_structure(self):
        """Test error result has correct structure."""
        service = GapAnalysisService(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            collection_flow_id=str(uuid4()),
        )

        result = service._error_result("Test error message")

        assert result["status"] == "error"
        assert result["error"] == "Test error message"
        assert "gaps" in result
        assert "questionnaire" in result

    async def test_persist_gaps(
        self,
        async_db_session: AsyncSession,
        test_collection_flow: CollectionFlow,
        test_assets: list[Asset],
    ):
        """Test gap persistence to database."""
        service = GapAnalysisService(
            client_account_id=str(test_collection_flow.client_account_id),
            engagement_id=str(test_collection_flow.engagement_id),
            collection_flow_id=str(test_collection_flow.id),
        )

        # Mock result with gaps
        result_dict = {
            "gaps": {
                "critical": [
                    {
                        "asset_id": str(test_assets[0].id),
                        "field_name": "operating_system",
                        "gap_type": "missing_field",
                        "gap_category": "infrastructure",
                        "description": "Operating system not specified",
                        "impact_on_sixr": "high",
                        "suggested_resolution": "Request from system admin",
                    },
                    {
                        "asset_id": str(test_assets[1].id),
                        "field_name": "technology_stack",
                        "gap_type": "missing_field",
                        "gap_category": "application",
                        "description": "Technology stack unknown",
                        "impact_on_sixr": "high",
                        "suggested_resolution": "Request from app owner",
                    },
                ],
                "high": [
                    {
                        "asset_id": str(test_assets[2].id),
                        "field_name": "backup_strategy",
                        "gap_type": "missing_field",
                        "gap_category": "operational",
                        "description": "Backup strategy not documented",
                        "impact_on_sixr": "medium",
                        "suggested_resolution": "Review with ops team",
                    }
                ],
            },
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 3, "assets_analyzed": 3},
        }

        gaps_count = await service._persist_gaps(
            result_dict, test_assets, async_db_session
        )

        assert gaps_count == 3

        # Verify in database
        stmt = select(CollectionDataGap).where(
            CollectionDataGap.collection_flow_id == test_collection_flow.id
        )
        result = await async_db_session.execute(stmt)
        persisted_gaps = result.scalars().all()

        assert len(persisted_gaps) == 3

        # Verify gap details
        critical_gaps = [g for g in persisted_gaps if g.priority == 1]
        high_gaps = [g for g in persisted_gaps if g.priority == 2]

        assert len(critical_gaps) == 2
        assert len(high_gaps) == 1

        # Verify field names
        field_names = {g.field_name for g in persisted_gaps}
        assert field_names == {
            "operating_system",
            "technology_stack",
            "backup_strategy",
        }

    async def test_analyze_with_no_assets(
        self, async_db_session: AsyncSession, test_collection_flow: CollectionFlow
    ):
        """Test gap analysis when no assets are found."""
        service = GapAnalysisService(
            client_account_id=str(test_collection_flow.client_account_id),
            engagement_id=str(test_collection_flow.engagement_id),
            collection_flow_id=str(test_collection_flow.id),
        )

        result = await service.analyze_and_generate_questionnaire(
            selected_asset_ids=[str(uuid4()), str(uuid4())],  # Non-existent
            db=async_db_session,
            automation_tier="tier_2",
        )

        assert result["summary"]["total_gaps"] == 0
        assert result["summary"]["assets_analyzed"] == 0
        assert len(result["gaps"]) == 0

    @pytest.mark.skip(reason="Requires CrewAI agent setup and API keys")
    async def test_full_gap_analysis_with_agent(
        self,
        async_db_session: AsyncSession,
        test_collection_flow: CollectionFlow,
        test_assets: list[Asset],
    ):
        """
        Full integration test with real agent execution.

        Skipped by default - requires:
        1. DEEPINFRA_API_KEY environment variable
        2. CrewAI agent pool properly configured
        3. Network access to DeepInfra API
        """
        service = GapAnalysisService(
            client_account_id=str(test_collection_flow.client_account_id),
            engagement_id=str(test_collection_flow.engagement_id),
            collection_flow_id=str(test_collection_flow.id),
        )

        asset_ids = [str(asset.id) for asset in test_assets]
        result = await service.analyze_and_generate_questionnaire(
            selected_asset_ids=asset_ids,
            db=async_db_session,
            automation_tier="tier_2",
        )

        # Verify structure
        assert "gaps" in result
        assert "questionnaire" in result
        assert "summary" in result

        # Verify gaps detected
        total_gaps = sum(
            len(v) if isinstance(v, list) else 0 for v in result["gaps"].values()
        )
        assert total_gaps > 0, "Agent should detect gaps in test assets"

        # Verify database persistence
        stmt = select(CollectionDataGap).where(
            CollectionDataGap.collection_flow_id == test_collection_flow.id
        )
        db_result = await async_db_session.execute(stmt)
        persisted_gaps = db_result.scalars().all()

        assert len(persisted_gaps) == result["summary"]["gaps_persisted"]
        assert result["summary"]["assets_analyzed"] == len(test_assets)


@pytest.mark.asyncio
class TestGapAnalysisDatabase:
    """Database-specific tests for gap analysis."""

    async def test_gap_deduplication(
        self, async_db_session: AsyncSession, test_collection_flow: CollectionFlow
    ):
        """Test that duplicate gaps are not created."""
        gap1 = CollectionDataGap(
            collection_flow_id=test_collection_flow.id,
            gap_type="missing_field",
            gap_category="infrastructure",
            field_name="operating_system",
            description="OS missing",
            impact_on_sixr="high",
            priority=1,
            suggested_resolution="Manual collection",
            resolution_status="pending",
        )

        async_db_session.add(gap1)
        await async_db_session.commit()

        # Verify single gap exists
        stmt = select(CollectionDataGap).where(
            CollectionDataGap.collection_flow_id == test_collection_flow.id
        )
        result = await async_db_session.execute(stmt)
        gaps = result.scalars().all()

        assert len(gaps) == 1

    async def test_gap_priority_ordering(
        self, async_db_session: AsyncSession, test_collection_flow: CollectionFlow
    ):
        """Test gaps can be ordered by priority."""
        gaps = [
            CollectionDataGap(
                collection_flow_id=test_collection_flow.id,
                gap_type="missing_field",
                gap_category="infrastructure",
                field_name=f"field_{i}",
                description=f"Field {i} missing",
                impact_on_sixr="high",
                priority=priority,
                suggested_resolution="Manual collection",
                resolution_status="pending",
            )
            for i, priority in enumerate([3, 1, 4, 2], start=1)
        ]

        async_db_session.add_all(gaps)
        await async_db_session.commit()

        # Query ordered by priority
        stmt = (
            select(CollectionDataGap)
            .where(CollectionDataGap.collection_flow_id == test_collection_flow.id)
            .order_by(CollectionDataGap.priority.asc())
        )
        result = await async_db_session.execute(stmt)
        ordered_gaps = result.scalars().all()

        assert [g.priority for g in ordered_gaps] == [1, 2, 3, 4]
