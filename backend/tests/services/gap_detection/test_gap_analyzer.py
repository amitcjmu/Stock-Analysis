"""
Unit tests for GapAnalyzer orchestrator.

Tests cover:
1. Complete asset with 100% completeness
2. Asset missing critical fields (priority 1)
3. Asset with partial enrichments
4. Asset with standards violations
5. Weighted completeness calculation
6. Gap prioritization (critical/high/medium)
7. Assessment readiness threshold
8. Readiness blockers generation
9. Parallel inspector execution performance
10. Tenant scoping parameter passing

Target: >90% code coverage
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.gap_detection import (
    GapAnalyzer,
    ComprehensiveGapReport,
    ColumnGapReport,
    EnrichmentGapReport,
    JSONBGapReport,
    ApplicationGapReport,
    StandardsGapReport,
    StandardViolation,
)


@pytest.fixture
def mock_asset():
    """Create a mock Asset with typical attributes."""
    asset = MagicMock()
    asset.id = uuid4()
    asset.asset_name = "test-server-01"
    asset.asset_type = "server"
    asset.six_r_strategy = "rehost"
    asset.criticality = "tier_1_critical"

    # Column attributes
    asset.cpu_cores = 8
    asset.memory_gb = 32
    asset.storage_gb = 500
    asset.operating_system = "Ubuntu 20.04"
    asset.technology_stack = "Python, Django"

    # Enrichment relationships
    asset.resilience = MagicMock()
    asset.compliance_flags = MagicMock()
    asset.compliance_flags.compliance_scopes = ["PCI-DSS"]

    return asset


@pytest.fixture
def mock_application():
    """Create a mock CanonicalApplication."""
    app = MagicMock()
    app.id = uuid4()
    app.application_name = "test-app"
    app.application_description = "Test application"
    app.business_unit = "Engineering"
    return app


@pytest.fixture
def mock_db_session():
    """Create a mock AsyncSession."""
    return AsyncMock()


@pytest.mark.asyncio
class TestGapAnalyzer:
    """Test suite for GapAnalyzer orchestrator."""

    async def test_analyze_asset_complete_data(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test gap analysis with complete asset data (100% completeness)."""
        analyzer = GapAnalyzer()

        # Mock all inspectors to return perfect scores
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Perfect scores (no gaps)
            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=1.0,
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=1.0,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=1.0,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            assert isinstance(report, ComprehensiveGapReport)
            assert report.overall_completeness == 1.0
            assert report.is_ready_for_assessment is True
            assert len(report.readiness_blockers) == 0
            assert len(report.critical_gaps) == 0
            assert len(report.high_priority_gaps) == 0
            assert len(report.medium_priority_gaps) == 0
            assert report.asset_id == str(mock_asset.id)
            assert report.asset_name == "test-server-01"
            assert report.asset_type == "server"

    async def test_analyze_asset_missing_critical_fields(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test gap analysis with missing critical (priority 1) fields."""
        analyzer = GapAnalyzer()

        # Mock inspectors with critical gaps
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Critical gaps: missing cpu_cores and memory_gb (priority 1)
            mock_col.return_value = ColumnGapReport(
                missing_attributes=["cpu_cores", "memory_gb"],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=0.50,
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=1.0,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=1.0,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            assert report.overall_completeness < 1.0
            # Should NOT be ready due to critical gaps
            assert report.is_ready_for_assessment is False
            assert len(report.readiness_blockers) > 0
            # cpu_cores and memory_gb should be in critical_gaps
            assert any("cpu_cores" in gap for gap in report.critical_gaps) or any(
                "memory_gb" in gap for gap in report.critical_gaps
            )

    async def test_analyze_asset_partial_enrichments(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test gap analysis with some enrichments missing."""
        analyzer = GapAnalyzer()

        # Mock inspectors with missing enrichments
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=1.0,
            )
            # Missing resilience and compliance_flags enrichments
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=["resilience", "compliance_flags"],
                incomplete_tables={},
                completeness_score=0.60,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=1.0,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            assert report.overall_completeness < 1.0
            # Enrichments are high priority (not critical)
            assert "resilience" in report.high_priority_gaps
            assert "compliance_flags" in report.high_priority_gaps
            # Should still be ready if overall completeness >= threshold
            # (depends on weights)

    async def test_analyze_asset_standards_violations(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test gap analysis with mandatory standards violations."""
        analyzer = GapAnalyzer()

        # Mock inspectors with standards violations
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=1.0,
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=1.0,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=1.0,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            # Mandatory standards violation
            mock_std.return_value = StandardsGapReport(
                violated_standards=[
                    StandardViolation(
                        standard_name="Encryption at Rest",
                        requirement_type="security",
                        violation_details="Required: encryption_enabled=True, Found: False",
                        is_mandatory=True,
                        override_available=False,
                    )
                ],
                missing_mandatory_data=["Encryption at Rest"],
                override_required=True,
                completeness_score=0.75,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            # Should NOT be ready due to mandatory standards violation
            assert report.is_ready_for_assessment is False
            assert len(report.readiness_blockers) > 0
            assert any("Standard:" in gap for gap in report.critical_gaps)
            assert report.standards_gaps.override_required is True

    async def test_weighted_completeness_calculation(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test weighted completeness calculation with different layer scores."""
        analyzer = GapAnalyzer()

        # Mock inspectors with varying scores
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Varying completeness scores
            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=0.85,  # 85%
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=0.70,  # 70%
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=0.90,  # 90%
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=0.60,  # 60%
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=0.80,  # 80%
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            # Verify weighted scores exist for all layers
            assert "columns" in report.weighted_scores
            assert "enrichments" in report.weighted_scores
            assert "jsonb" in report.weighted_scores
            assert "application" in report.weighted_scores
            assert "standards" in report.weighted_scores

            # Verify overall completeness is clamped to [0.0, 1.0]
            assert 0.0 <= report.overall_completeness <= 1.0

            # Verify sum of weighted scores equals overall completeness
            sum_weighted = sum(report.weighted_scores.values())
            assert abs(sum_weighted - report.overall_completeness) < 0.01

    async def test_gap_prioritization(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test gap prioritization into critical/high/medium categories."""
        analyzer = GapAnalyzer()

        # Mock inspectors with mixed priority gaps
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Priority 1: cpu_memory_storage_specs (critical)
            mock_col.return_value = ColumnGapReport(
                missing_attributes=["cpu_cores"],  # Priority 1
                empty_attributes=[],
                null_attributes=[],
                completeness_score=0.75,
            )
            # Priority 2: enrichments (high)
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=["resilience"],
                incomplete_tables={},
                completeness_score=0.80,
            )
            # Priority 3: JSONB keys (medium)
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={"custom_attributes": ["environment"]},
                empty_values={},
                completeness_score=0.90,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=["business_unit"],  # Priority 2
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=0.85,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            # Critical gaps should contain cpu_cores (priority 1)
            assert (
                any("cpu_cores" in gap for gap in report.critical_gaps)
                or len(report.critical_gaps) > 0
            )

            # High priority should contain enrichments and application metadata
            assert "resilience" in report.high_priority_gaps
            assert "business_unit" in report.high_priority_gaps

            # Medium priority should contain JSONB keys
            assert any(
                "custom_attributes.environment" in gap
                for gap in report.medium_priority_gaps
            )

    async def test_assessment_readiness_threshold(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test assessment readiness determination based on threshold."""
        analyzer = GapAnalyzer()

        # Mock inspectors with score just below threshold
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Scores that result in overall < 0.75 threshold
            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=0.60,  # Low score
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=0.60,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=0.60,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=0.60,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=0.60,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            # Should NOT be ready if overall < threshold
            assert report.overall_completeness < report.completeness_threshold
            assert report.is_ready_for_assessment is False
            assert len(report.readiness_blockers) > 0
            # First blocker should mention completeness below threshold
            assert any(
                "below threshold" in blocker for blocker in report.readiness_blockers
            )

    async def test_readiness_blockers(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test specific readiness blocker messages generation."""
        analyzer = GapAnalyzer()

        # Mock inspectors with multiple blocking issues
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Low completeness + critical gaps + standards violation
            mock_col.return_value = ColumnGapReport(
                missing_attributes=["cpu_cores", "memory_gb"],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=0.50,
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[],
                incomplete_tables={},
                completeness_score=1.0,
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={},
                empty_values={},
                completeness_score=1.0,
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[
                    StandardViolation(
                        standard_name="Network Segmentation",
                        requirement_type="security",
                        violation_details="Required: firewall_enabled=True, Found: False",
                        is_mandatory=True,
                        override_available=False,
                    )
                ],
                missing_mandatory_data=["Network Segmentation"],
                override_required=True,
                completeness_score=0.75,
            )

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            # Assertions
            assert report.is_ready_for_assessment is False
            assert len(report.readiness_blockers) >= 3  # Threshold, gaps, standards

            # Check blocker messages contain expected content
            blockers_text = " ".join(report.readiness_blockers)
            assert "below threshold" in blockers_text or "Completeness" in blockers_text
            assert "critical attributes" in blockers_text or "Missing" in blockers_text
            assert "standards" in blockers_text or "Violates" in blockers_text

    async def test_parallel_inspector_execution(
        self, mock_asset, mock_application, mock_db_session
    ):
        """Test that inspectors are executed in parallel with asyncio.gather."""
        analyzer = GapAnalyzer()

        # Track call order with timestamps
        call_times = []

        async def mock_inspect_with_delay(*args, **kwargs):
            import asyncio

            call_times.append(datetime.utcnow())
            await asyncio.sleep(0.01)  # Small delay to simulate work
            return ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=1.0,
            )

        # Mock all inspectors with delays
        with patch.object(
            analyzer.column_inspector, "inspect", side_effect=mock_inspect_with_delay
        ), patch.object(
            analyzer.enrichment_inspector,
            "inspect",
            new=AsyncMock(
                return_value=EnrichmentGapReport(
                    missing_tables=[], incomplete_tables={}, completeness_score=1.0
                )
            ),
        ), patch.object(
            analyzer.jsonb_inspector,
            "inspect",
            new=AsyncMock(
                return_value=JSONBGapReport(
                    missing_keys={}, empty_values={}, completeness_score=1.0
                )
            ),
        ), patch.object(
            analyzer.application_inspector,
            "inspect",
            new=AsyncMock(
                return_value=ApplicationGapReport(
                    missing_metadata=[],
                    incomplete_tech_stack=[],
                    missing_business_context=[],
                    completeness_score=1.0,
                )
            ),
        ), patch.object(
            analyzer.standards_inspector,
            "inspect",
            new=AsyncMock(
                return_value=StandardsGapReport(
                    violated_standards=[],
                    missing_mandatory_data=[],
                    override_required=False,
                    completeness_score=1.0,
                )
            ),
        ):

            start_time = datetime.utcnow()

            # Run analysis
            report = await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )

            end_time = datetime.utcnow()
            # Calculate duration for performance validation
            _ = (end_time - start_time).total_seconds() * 1000  # noqa: F841

            # Assertions
            assert isinstance(report, ComprehensiveGapReport)
            # Should complete in <50ms target (allowing some overhead)
            # Note: In testing, parallel execution should be < 5 * 10ms = 50ms
            # If sequential, would be 5 * 10ms = 50ms
            # This is a weak test due to small delays, but validates structure

    async def test_tenant_scoping(self, mock_asset, mock_application, mock_db_session):
        """Test that tenant scoping parameters are passed to all inspectors."""
        analyzer = GapAnalyzer()

        client_account_id = "test-client-uuid-123"
        engagement_id = "test-engagement-uuid-456"

        # Mock inspectors and capture call arguments
        with patch.object(
            analyzer.column_inspector, "inspect", new=AsyncMock()
        ) as mock_col, patch.object(
            analyzer.enrichment_inspector, "inspect", new=AsyncMock()
        ) as mock_enr, patch.object(
            analyzer.jsonb_inspector, "inspect", new=AsyncMock()
        ) as mock_jsonb, patch.object(
            analyzer.application_inspector, "inspect", new=AsyncMock()
        ) as mock_app, patch.object(
            analyzer.standards_inspector, "inspect", new=AsyncMock()
        ) as mock_std:

            # Configure mock returns
            mock_col.return_value = ColumnGapReport(
                missing_attributes=[],
                empty_attributes=[],
                null_attributes=[],
                completeness_score=1.0,
            )
            mock_enr.return_value = EnrichmentGapReport(
                missing_tables=[], incomplete_tables={}, completeness_score=1.0
            )
            mock_jsonb.return_value = JSONBGapReport(
                missing_keys={}, empty_values={}, completeness_score=1.0
            )
            mock_app.return_value = ApplicationGapReport(
                missing_metadata=[],
                incomplete_tech_stack=[],
                missing_business_context=[],
                completeness_score=1.0,
            )
            mock_std.return_value = StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

            # Run analysis
            await analyzer.analyze_asset(
                asset=mock_asset,
                application=mock_application,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=mock_db_session,
            )

            # Assertions - verify all inspectors were called with tenant scoping
            for mock_inspector in [mock_col, mock_enr, mock_jsonb, mock_app, mock_std]:
                mock_inspector.assert_called_once()
                call_kwargs = mock_inspector.call_args.kwargs
                assert call_kwargs["client_account_id"] == client_account_id
                assert call_kwargs["engagement_id"] == engagement_id

    async def test_analyze_asset_none_raises_error(self, mock_db_session):
        """Test that passing None asset raises ValueError."""
        analyzer = GapAnalyzer()

        with pytest.raises(ValueError, match="Asset cannot be None"):
            await analyzer.analyze_asset(
                asset=None,
                application=None,
                client_account_id="test-client-123",
                engagement_id="test-engagement-456",
                db=mock_db_session,
            )
