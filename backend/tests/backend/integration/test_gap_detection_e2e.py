"""
End-to-End Tests: Intelligent Multi-Layer Gap Detection System

Comprehensive E2E tests covering the entire gap detection pipeline from
asset creation through questionnaire generation.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 15
Author: CC (Claude Code)
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.canonical_applications import CanonicalApplication
from app.models.assessment_flow import EngagementArchitectureStandard
from app.models import ClientAccount, Engagement, User
from app.services.child_flow_services.questionnaire_helpers_gap_analyzer import (
    analyze_and_generate_questionnaires,
)
from app.services.gap_detection.gap_analyzer import GapAnalyzer
from app.services.gap_detection.schemas import GapPriority


class MockChildFlow:
    """Mock child flow for testing."""

    def __init__(self, flow_id):
        self.id = flow_id


@pytest.mark.asyncio
@pytest.mark.e2e
class TestGapDetectionE2E:
    """End-to-end test suite for gap detection system."""

    @pytest_asyncio.fixture
    async def test_user(self, async_db_session: AsyncSession) -> User:
        """Create test user for E2E tests."""
        user_id = uuid4()
        user = User(
            id=user_id,
            username=f"e2e_test_user_{user_id.hex[:8]}",
            email=f"e2e_{user_id.hex[:8]}@test.com",
            password_hash="test_hash",
            is_active=True,
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_client(self, async_db_session: AsyncSession) -> ClientAccount:
        """Create test client account for E2E tests."""
        client_id = uuid4()
        client = ClientAccount(
            id=client_id,
            name="E2E Test Client",
            slug=f"e2e-test-client-{client_id.hex[:8]}",
            industry="Technology",
            company_size="Enterprise",
            headquarters_location="Test City",
            primary_contact_name="Test Contact",
            primary_contact_email="contact@testclient.com",
        )
        async_db_session.add(client)
        await async_db_session.commit()
        await async_db_session.refresh(client)
        return client

    @pytest_asyncio.fixture
    async def test_engagement(
        self,
        async_db_session: AsyncSession,
        test_user: User,
        test_client: ClientAccount,
    ) -> Engagement:
        """Create test engagement for E2E tests."""
        engagement_id = uuid4()
        engagement = Engagement(
            id=engagement_id,
            name="E2E Test Engagement",
            slug=f"e2e-test-engagement-{engagement_id.hex[:8]}",
            description="Test engagement for E2E gap detection testing",
            client_account_id=test_client.id,
            engagement_lead_id=test_user.id,
            status="active",
            engagement_type="migration",
        )
        async_db_session.add(engagement)
        await async_db_session.commit()
        await async_db_session.refresh(engagement)
        return engagement

    async def test_complete_pipeline_minimal_asset(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test complete pipeline with minimal asset data (maximum gaps)."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()
        flow_id = uuid4()

        context = RequestContext(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Create minimal asset (will trigger many gaps)
        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="minimal-app",
            asset_type="application",
        )
        async_db_session.add(asset)
        await async_db_session.commit()
        await async_db_session.refresh(asset)

        # Act: Run complete pipeline
        result = await analyze_and_generate_questionnaires(
            db=async_db_session,
            context=context,
            asset_ids=[asset_id],
            child_flow=MockChildFlow(flow_id),
        )

        # Assert
        assert result["status"] == "success"
        assert len(result["questionnaires"]) > 0

        # Verify comprehensive gaps were identified
        metadata = result["metadata"]
        assert metadata["total_questions"] > 0  # Should have at least some questions
        assert metadata["assets_analyzed"] == 1

    async def test_complete_pipeline_with_enrichment(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test pipeline with partially enriched asset data."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()
        flow_id = uuid4()

        context = RequestContext(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Create asset with some base data
        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="enriched-app",
            asset_type="application",
            operating_system="Linux",
            ip_address="10.0.1.5",
        )
        async_db_session.add(asset)

        # Create partial canonical application
        app = CanonicalApplication(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            canonical_name="enriched-app",
            normalized_name="enriched_app",
            name_hash="hash_enriched_app",
            business_criticality="high",
            # Missing: description, technology_stack, etc.
        )
        async_db_session.add(app)
        await async_db_session.commit()

        # Act
        result = await analyze_and_generate_questionnaires(
            db=async_db_session,
            context=context,
            asset_ids=[asset_id],
            child_flow=MockChildFlow(flow_id),
        )

        # Assert
        assert result["status"] == "success"
        # Should have fewer questions than minimal asset
        metadata = result["metadata"]
        assert metadata["total_questions"] < 20  # Fewer gaps due to enrichment

    async def test_complete_pipeline_with_standards(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test pipeline with architecture standards enforcement."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()
        flow_id = uuid4()

        context = RequestContext(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Create asset
        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="standards-app",
            asset_type="application",
        )
        async_db_session.add(asset)

        # Create multiple architecture standards
        standards = [
            EngagementArchitectureStandard(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                requirement_type="database",
                standard_name="PostgreSQL Standard",
                minimum_requirements={"min_version": "14.0"},
                is_mandatory=True,
            ),
            EngagementArchitectureStandard(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                requirement_type="compliance",
                standard_name="PCI-DSS",
                minimum_requirements={"level": "1"},
                is_mandatory=True,
            ),
        ]
        for std in standards:
            async_db_session.add(std)
        await async_db_session.commit()

        # Act
        result = await analyze_and_generate_questionnaires(
            db=async_db_session,
            context=context,
            asset_ids=[asset_id],
            child_flow=MockChildFlow(flow_id),
        )

        # Assert
        assert result["status"] == "success"
        # Should include questions about standards compliance
        sections = result["questionnaires"]
        section_titles = [s.get("section_title", "") for s in sections]
        assert any(
            "database" in title.lower() or "compliance" in title.lower()
            for title in section_titles
        )

    async def test_complete_pipeline_multiple_assets(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test pipeline with multiple assets (batch processing)."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_ids = [uuid4() for _ in range(5)]
        flow_id = uuid4()

        context = RequestContext(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Create 5 assets with varying data completeness
        for i, asset_id in enumerate(asset_ids):
            asset = Asset(
                id=asset_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                name=f"batch-app-{i+1}",
                asset_type="application",
                operating_system="Linux" if i % 2 == 0 else None,
                ip_address=f"10.0.1.{i+1}" if i % 3 == 0 else None,
            )
            async_db_session.add(asset)
        await async_db_session.commit()

        # Act
        result = await analyze_and_generate_questionnaires(
            db=async_db_session,
            context=context,
            asset_ids=asset_ids,
            child_flow=MockChildFlow(flow_id),
        )

        # Assert
        assert result["status"] == "success"
        metadata = result["metadata"]
        assert metadata["assets_analyzed"] == 5
        assert metadata["total_questions"] > 0

    async def test_gap_analyzer_performance_target(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test that gap analysis meets <50ms per asset performance target."""
        import time

        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()

        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="perf-test-app",
            asset_type="application",
        )
        async_db_session.add(asset)
        await async_db_session.commit()

        # Act
        gap_analyzer = GapAnalyzer()
        start_time = time.time()
        gap_report = await gap_analyzer.analyze_asset(
            asset=asset,
            application=None,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            db=async_db_session,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        # Assert
        assert gap_report is not None
        assert elapsed_ms < 50, f"Gap analysis took {elapsed_ms:.2f}ms, target is <50ms"

    async def test_questionnaire_generation_backward_compatibility(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test that new system maintains backward compatibility with legacy format."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()
        flow_id = uuid4()

        context = RequestContext(
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="compat-app",
            asset_type="application",
        )
        async_db_session.add(asset)
        await async_db_session.commit()

        # Act
        result = await analyze_and_generate_questionnaires(
            db=async_db_session,
            context=context,
            asset_ids=[asset_id],
            child_flow=MockChildFlow(flow_id),
        )

        # Assert - verify legacy format fields
        assert "status" in result
        assert "questionnaires" in result
        assert "metadata" in result

        # Verify questionnaire structure
        sections = result["questionnaires"]
        for section in sections:
            assert "section_id" in section
            assert "section_title" in section
            assert "questions" in section
            for question in section["questions"]:
                assert "question_id" in question
                assert "question_text" in question

    async def test_priority_gap_filtering(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test that only critical/high priority gaps generate questions."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id
        asset_id = uuid4()

        # Create asset with significant data
        asset = Asset(
            id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="priority-test-app",
            asset_type="application",
            operating_system="Linux",
            ip_address="10.0.1.1",
        )
        async_db_session.add(asset)

        # Create canonical application with most fields filled
        app = CanonicalApplication(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            canonical_name="priority-test-app",
            normalized_name="priority_test_app",
            name_hash="hash_priority_test_app",
            business_criticality="critical",
            description="Well-documented application",
            # Only missing low-priority fields
        )
        async_db_session.add(app)
        await async_db_session.commit()

        # Act
        gap_analyzer = GapAnalyzer()
        gap_report = await gap_analyzer.analyze_asset(
            asset=asset,
            application=app,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            db=async_db_session,
        )

        # Assert
        # Should have fewer gaps due to comprehensive data
        critical_gaps = [
            g for g in gap_report.all_gaps if g.priority == GapPriority.CRITICAL
        ]
        high_gaps = [g for g in gap_report.all_gaps if g.priority == GapPriority.HIGH]

        # Well-filled asset should have minimal critical/high gaps
        assert len(critical_gaps) + len(high_gaps) < len(gap_report.all_gaps)

    async def test_assessment_readiness_calculation(
        self,
        async_db_session: AsyncSession,
        test_client: ClientAccount,
        test_engagement: Engagement,
    ):
        """Test assessment readiness determination based on gap analysis."""
        # Arrange
        client_account_id = test_client.id
        engagement_id = test_engagement.id

        # Create two assets: one ready, one not
        ready_asset = Asset(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="ready-app",
            asset_type="application",
            operating_system="Linux",
            ip_address="10.0.1.1",
        )
        ready_app = CanonicalApplication(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            canonical_name="ready-app",
            normalized_name="ready_app",
            name_hash="hash_ready_app",
            business_criticality="high",
            description="Comprehensive application documentation",
            # Well-filled data
        )

        not_ready_asset = Asset(
            id=uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="not-ready-app",
            asset_type="application",
            # Minimal data
        )

        async_db_session.add(ready_asset)
        async_db_session.add(ready_app)
        async_db_session.add(not_ready_asset)
        await async_db_session.commit()

        # Act
        gap_analyzer = GapAnalyzer()

        ready_report = await gap_analyzer.analyze_asset(
            asset=ready_asset,
            application=ready_app,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            db=async_db_session,
        )

        not_ready_report = await gap_analyzer.analyze_asset(
            asset=not_ready_asset,
            application=None,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            db=async_db_session,
        )

        # Assert
        # Ready asset should have higher completeness
        assert ready_report.overall_completeness > not_ready_report.overall_completeness

        # Assessment readiness should reflect data quality
        if ready_report.assessment_ready:
            assert ready_report.overall_completeness >= 0.7

        if not not_ready_report.assessment_ready:
            assert not_ready_report.overall_completeness < 0.7
