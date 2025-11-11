"""
Unit tests for RequirementsEngine.

Tests context-aware requirements aggregation including:
- Asset type requirements
- 6R strategy requirements
- Compliance scope requirements
- Criticality tier requirements
- Requirement merging logic
- LRU cache performance

Coverage target: >90%
"""

import pytest
import time

from app.services.gap_detection.requirements.requirements_engine import (
    RequirementsEngine,
)
from app.services.gap_detection.schemas import DataRequirements


@pytest.fixture
def engine():
    """Create a fresh RequirementsEngine instance for each test."""
    engine = RequirementsEngine()
    engine.clear_cache()  # Start with clean cache
    return engine


class TestAssetTypeRequirements:
    """Test requirements for asset types alone."""

    @pytest.mark.asyncio
    async def test_server_requirements(self, engine):
        """Test server asset type requirements."""
        reqs = await engine.get_requirements(asset_type="server")

        assert isinstance(reqs, DataRequirements)
        assert "asset_name" in reqs.required_columns
        assert "operating_system" in reqs.required_columns
        assert "cpu_cores" in reqs.required_columns
        assert "memory_gb" in reqs.required_columns
        assert "resilience" in reqs.required_enrichments
        assert reqs.completeness_threshold == 0.75
        assert reqs.priority_weights["columns"] == 0.50

    @pytest.mark.asyncio
    async def test_database_requirements(self, engine):
        """Test database asset type requirements."""
        reqs = await engine.get_requirements(asset_type="database")

        assert "technology_stack" in reqs.required_columns
        assert "storage_gb" in reqs.required_columns
        assert "resilience" in reqs.required_enrichments
        assert "compliance_flags" in reqs.required_enrichments
        assert reqs.completeness_threshold == 0.80  # Higher for databases

    @pytest.mark.asyncio
    async def test_application_requirements(self, engine):
        """Test application asset type requirements."""
        reqs = await engine.get_requirements(asset_type="application")

        assert "technology_stack" in reqs.required_columns
        assert "architecture_pattern" in reqs.required_columns
        assert "tech_debt" in reqs.required_enrichments
        assert "technical_details" in reqs.required_jsonb_keys
        assert "api_endpoints" in reqs.required_jsonb_keys["technical_details"]
        assert reqs.completeness_threshold == 0.75

    @pytest.mark.asyncio
    async def test_network_requirements(self, engine):
        """Test network asset type requirements."""
        reqs = await engine.get_requirements(asset_type="network")

        assert "ip_address" in reqs.required_columns
        assert "fqdn" in reqs.required_columns
        assert "resilience" in reqs.required_enrichments
        assert reqs.completeness_threshold == 0.70

    @pytest.mark.asyncio
    async def test_container_requirements(self, engine):
        """Test container asset type requirements."""
        reqs = await engine.get_requirements(asset_type="container")

        assert "technology_stack" in reqs.required_columns
        assert "vulnerabilities" in reqs.required_enrichments
        assert "custom_attributes" in reqs.required_jsonb_keys
        assert "container_runtime" in reqs.required_jsonb_keys["custom_attributes"]

    @pytest.mark.asyncio
    async def test_unknown_asset_type_defaults(self, engine):
        """Test unknown asset type falls back to 'other' defaults."""
        reqs = await engine.get_requirements(asset_type="unknown_type")

        assert "asset_name" in reqs.required_columns
        assert "environment" in reqs.required_columns
        assert reqs.completeness_threshold == 0.60  # Default threshold
        assert len(reqs.required_enrichments) == 0  # Minimal requirements

    @pytest.mark.asyncio
    async def test_case_insensitive_asset_type(self, engine):
        """Test asset type is case-insensitive."""
        reqs_lower = await engine.get_requirements(asset_type="server")
        reqs_upper = await engine.get_requirements(asset_type="SERVER")
        reqs_mixed = await engine.get_requirements(asset_type="Server")

        assert reqs_lower.required_columns == reqs_upper.required_columns
        assert reqs_lower.required_columns == reqs_mixed.required_columns


class TestSixRStrategyRequirements:
    """Test requirements merging with 6R strategies."""

    @pytest.mark.asyncio
    async def test_rehost_strategy(self, engine):
        """Test rehost strategy adds infrastructure requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="rehost",
        )

        # Should have application base requirements
        assert "technology_stack" in reqs.required_columns
        # Plus rehost-specific requirements
        assert "cpu_cores" in reqs.required_columns
        assert "memory_gb" in reqs.required_columns
        assert "performance_metrics" in reqs.required_enrichments

    @pytest.mark.asyncio
    async def test_refactor_strategy(self, engine):
        """Test refactor strategy adds technical debt requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="refactor",
        )

        # Should have application base requirements
        assert "technology_stack" in reqs.required_columns
        # Plus refactor-specific requirements
        assert "code_quality" in reqs.required_columns
        assert "tech_debt" in reqs.required_enrichments
        assert "vulnerabilities" in reqs.required_enrichments
        # Refactor has higher threshold
        assert reqs.completeness_threshold == 0.85

    @pytest.mark.asyncio
    async def test_replatform_strategy(self, engine):
        """Test replatform strategy adds compatibility requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="replatform",
        )

        assert "dependencies" in reqs.required_columns
        assert "dependencies" in reqs.required_enrichments
        assert "technical_details" in reqs.required_jsonb_keys
        assert (
            "compatibility_assessment" in reqs.required_jsonb_keys["technical_details"]
        )

    @pytest.mark.asyncio
    async def test_retire_strategy(self, engine):
        """Test retire strategy has lower completeness threshold."""
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="retire",
        )

        # Retire threshold (0.60) is lower than application base (0.75)
        # But max() is used, so application threshold wins
        assert reqs.completeness_threshold == 0.75  # Application base threshold


class TestComplianceRequirements:
    """Test requirements merging with compliance scopes."""

    @pytest.mark.asyncio
    async def test_pci_dss_compliance(self, engine):
        """Test PCI-DSS compliance adds security requirements."""
        reqs = await engine.get_requirements(
            asset_type="database",
            compliance_scopes=["PCI-DSS"],
        )

        # Should have compliance-specific requirements
        assert "vulnerabilities" in reqs.required_enrichments
        assert "technical_details" in reqs.required_jsonb_keys
        assert "encryption_at_rest" in reqs.required_jsonb_keys["technical_details"]
        assert "Encryption at Rest" in reqs.required_standards
        assert reqs.completeness_threshold == 0.90  # Very high bar for PCI

    @pytest.mark.asyncio
    async def test_hipaa_compliance(self, engine):
        """Test HIPAA compliance adds PHI requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            compliance_scopes=["HIPAA"],
        )

        assert "phi_data_handling" in reqs.required_jsonb_keys["technical_details"]
        assert "audit_logging" in reqs.required_jsonb_keys["technical_details"]
        assert "PHI Data Encryption" in reqs.required_standards
        assert reqs.completeness_threshold == 0.90  # Very high bar for HIPAA

    @pytest.mark.asyncio
    async def test_multiple_compliance_scopes(self, engine):
        """Test multiple compliance scopes merge correctly."""
        reqs = await engine.get_requirements(
            asset_type="database",
            compliance_scopes=["PCI-DSS", "SOC2"],
        )

        # Should have requirements from both scopes
        assert "encryption_at_rest" in reqs.required_jsonb_keys["technical_details"]
        assert (
            "change_management_process" in reqs.required_jsonb_keys["technical_details"]
        )
        assert "Encryption at Rest" in reqs.required_standards
        assert "Change Management" in reqs.required_standards
        # Should use highest threshold
        assert reqs.completeness_threshold == 0.90  # PCI is higher than SOC2

    @pytest.mark.asyncio
    async def test_gdpr_compliance(self, engine):
        """Test GDPR compliance adds data privacy requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            compliance_scopes=["GDPR"],
        )

        assert "pii_data_handling" in reqs.required_jsonb_keys["technical_details"]
        assert "Data Privacy" in reqs.required_standards


class TestCriticalityRequirements:
    """Test requirements merging with criticality tiers."""

    @pytest.mark.asyncio
    async def test_tier_1_critical(self, engine):
        """Test tier 1 critical adds stringent requirements."""
        reqs = await engine.get_requirements(
            asset_type="application",
            criticality="tier_1_critical",
        )

        assert "resilience" in reqs.required_enrichments
        assert "performance_metrics" in reqs.required_enrichments
        assert "custom_attributes" in reqs.required_jsonb_keys
        assert "sla_requirements" in reqs.required_jsonb_keys["custom_attributes"]
        assert reqs.completeness_threshold == 0.90  # Very high bar

    @pytest.mark.asyncio
    async def test_tier_2_important(self, engine):
        """Test tier 2 important has moderate requirements."""
        reqs = await engine.get_requirements(
            asset_type="server",
            criticality="tier_2_important",
        )

        assert "resilience" in reqs.required_enrichments
        assert reqs.completeness_threshold == 0.75

    @pytest.mark.asyncio
    async def test_tier_3_standard(self, engine):
        """Test tier 3 standard has minimal additional requirements."""
        reqs = await engine.get_requirements(
            asset_type="server",
            criticality="tier_3_standard",
        )

        # Should not add many requirements, just lower threshold
        assert reqs.completeness_threshold >= 0.60


class TestRequirementMerging:
    """Test requirement merging logic."""

    @pytest.mark.asyncio
    async def test_list_merging_deduplicates(self, engine):
        """Test list merging deduplicates correctly."""
        reqs = await engine.get_requirements(
            asset_type="database",  # requires resilience, compliance_flags
            six_r_strategy="rehost",  # requires resilience, performance_metrics
        )

        # "resilience" appears in both - should only appear once
        assert reqs.required_enrichments.count("resilience") == 1
        # Should have union of all requirements
        assert "compliance_flags" in reqs.required_enrichments
        assert "performance_metrics" in reqs.required_enrichments

    @pytest.mark.asyncio
    async def test_dict_merging_is_recursive(self, engine):
        """Test dict merging is recursive."""
        reqs = await engine.get_requirements(
            asset_type="application",  # requires technical_details.api_endpoints
            six_r_strategy="refactor",  # requires technical_details.refactoring_scope
        )

        # Should merge both keys under technical_details
        assert "technical_details" in reqs.required_jsonb_keys
        assert "api_endpoints" in reqs.required_jsonb_keys["technical_details"]
        assert "refactoring_scope" in reqs.required_jsonb_keys["technical_details"]

    @pytest.mark.asyncio
    async def test_threshold_takes_maximum(self, engine):
        """Test completeness threshold takes maximum value."""
        reqs = await engine.get_requirements(
            asset_type="database",  # threshold=0.80
            six_r_strategy="refactor",  # threshold=0.85
            criticality="tier_1_critical",  # threshold=0.90
        )

        # Should use highest threshold
        assert reqs.completeness_threshold == 0.90

    @pytest.mark.asyncio
    async def test_priority_weights_merge(self, engine):
        """Test priority weights are averaged when merging."""
        reqs = await engine.get_requirements(
            asset_type="application",  # columns=0.30, enrichments=0.30
            six_r_strategy="refactor",  # columns=0.30, enrichments=0.45
        )

        # Weights should be averaged (not summed)
        assert reqs.priority_weights["columns"] == 0.30  # (0.30 + 0.30) / 2 = 0.30
        assert reqs.priority_weights["enrichments"] == pytest.approx(
            0.375
        )  # (0.30 + 0.45) / 2 = 0.375


class TestCachePerformance:
    """Test LRU cache performance."""

    @pytest.mark.asyncio
    async def test_cache_improves_performance(self, engine):
        """Test cache hit is faster than cache miss."""
        # First call (cache miss)
        start = time.time()
        reqs1 = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="refactor",
            compliance_scopes=["PCI-DSS"],
        )
        first_duration = time.time() - start

        # Second call (cache hit)
        start = time.time()
        reqs2 = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="refactor",
            compliance_scopes=["PCI-DSS"],
        )
        second_duration = time.time() - start

        # Cache hit should be faster
        assert second_duration < first_duration
        # Cache hit should be <1ms
        assert second_duration < 0.001

        # Results should be identical
        assert reqs1.required_columns == reqs2.required_columns
        assert reqs1.completeness_threshold == reqs2.completeness_threshold

    @pytest.mark.asyncio
    async def test_cache_info_tracking(self, engine):
        """Test cache info provides accurate statistics."""
        # Clear cache
        engine.clear_cache()
        initial_info = engine.get_cache_info()
        assert initial_info["hits"] == 0
        assert initial_info["misses"] == 0
        assert initial_info["hit_rate"] == 0.0

        # First call - cache miss
        await engine.get_requirements(asset_type="server")
        info_after_miss = engine.get_cache_info()
        assert info_after_miss["misses"] == 1
        assert info_after_miss["hits"] == 0

        # Second call - cache hit
        await engine.get_requirements(asset_type="server")
        info_after_hit = engine.get_cache_info()
        assert info_after_hit["hits"] == 1
        assert info_after_hit["misses"] == 1
        assert info_after_hit["hit_rate"] == 0.5  # 1 hit out of 2 calls

    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self, engine):
        """Test different contexts create different cache keys."""
        engine.clear_cache()

        # Call with different asset types
        await engine.get_requirements(asset_type="server")
        await engine.get_requirements(asset_type="database")
        await engine.get_requirements(asset_type="application")

        cache_info = engine.get_cache_info()
        assert cache_info["current_size"] == 3  # Three unique cache entries
        assert cache_info["misses"] == 3  # All were cache misses

    @pytest.mark.asyncio
    async def test_cache_clear(self, engine):
        """Test cache can be cleared."""
        # Populate cache
        await engine.get_requirements(asset_type="server")
        await engine.get_requirements(asset_type="database")

        cache_info_before = engine.get_cache_info()
        assert cache_info_before["current_size"] == 2

        # Clear cache
        engine.clear_cache()

        cache_info_after = engine.get_cache_info()
        assert cache_info_after["current_size"] == 0
        assert cache_info_after["hits"] == 0
        assert cache_info_after["misses"] == 0


class TestComplexScenarios:
    """Test complex multi-context scenarios."""

    @pytest.mark.asyncio
    async def test_full_context_merge(self, engine):
        """Test all contexts merge correctly."""
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="refactor",
            compliance_scopes=["PCI-DSS", "HIPAA"],
            criticality="tier_1_critical",
        )

        # Should have requirements from all contexts
        # Asset type
        assert "technology_stack" in reqs.required_columns
        # 6R strategy
        assert "code_quality" in reqs.required_columns
        # Compliance
        assert "encryption_at_rest" in reqs.required_jsonb_keys["technical_details"]
        # Criticality
        assert "sla_requirements" in reqs.required_jsonb_keys["custom_attributes"]
        # Should use highest threshold
        assert reqs.completeness_threshold == 0.90

    @pytest.mark.asyncio
    async def test_empty_contexts(self, engine):
        """Test with minimal context (only asset type)."""
        reqs = await engine.get_requirements(asset_type="server")

        # Should have asset type requirements
        assert len(reqs.required_columns) > 0
        assert len(reqs.required_enrichments) > 0
        # But no compliance/criticality specific requirements
        assert len(reqs.required_standards) == 0

    @pytest.mark.asyncio
    async def test_none_contexts_handled(self, engine):
        """Test None contexts are handled gracefully."""
        reqs = await engine.get_requirements(
            asset_type="server",
            six_r_strategy=None,
            compliance_scopes=None,
            criticality=None,
        )

        # Should still return valid requirements
        assert isinstance(reqs, DataRequirements)
        assert len(reqs.required_columns) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_compliance_list(self, engine):
        """Test empty compliance scopes list."""
        reqs = await engine.get_requirements(
            asset_type="server",
            compliance_scopes=[],
        )

        # Should not add compliance requirements
        assert len(reqs.required_standards) == 0

    @pytest.mark.asyncio
    async def test_unknown_six_r_strategy(self, engine):
        """Test unknown 6R strategy is ignored."""
        reqs = await engine.get_requirements(
            asset_type="server",
            six_r_strategy="unknown_strategy",
        )

        # Should only have asset type requirements
        assert "cpu_cores" in reqs.required_columns

    @pytest.mark.asyncio
    async def test_unknown_compliance_scope(self, engine):
        """Test unknown compliance scope is ignored."""
        reqs = await engine.get_requirements(
            asset_type="server",
            compliance_scopes=["UNKNOWN_COMPLIANCE"],
        )

        # Should not crash, just ignore unknown scope
        assert isinstance(reqs, DataRequirements)


# Performance benchmark test
@pytest.mark.asyncio
async def test_performance_benchmark():
    """Benchmark RequirementsEngine performance."""
    engine = RequirementsEngine()
    engine.clear_cache()

    # Warm up cache with common contexts
    contexts = [
        ("application", "refactor", ["PCI-DSS"], "tier_1_critical"),
        ("server", "rehost", None, "tier_2_important"),
        ("database", "replatform", ["HIPAA"], "tier_1_critical"),
    ]

    # First pass - populate cache
    for asset_type, strategy, compliance, criticality in contexts:
        await engine.get_requirements(
            asset_type=asset_type,
            six_r_strategy=strategy,
            compliance_scopes=compliance,
            criticality=criticality,
        )

    # Second pass - measure cache hit performance
    total_time = 0
    iterations = 100

    for _ in range(iterations):
        for asset_type, strategy, compliance, criticality in contexts:
            start = time.time()
            await engine.get_requirements(
                asset_type=asset_type,
                six_r_strategy=strategy,
                compliance_scopes=compliance,
                criticality=criticality,
            )
            total_time += time.time() - start

    avg_time = total_time / (iterations * len(contexts))

    # Average cache hit should be <1ms
    assert (
        avg_time < 0.001
    ), f"Average cache hit time {avg_time*1000:.2f}ms exceeds 1ms target"

    cache_info = engine.get_cache_info()
    assert cache_info["hit_rate"] > 0.99  # Almost all hits after first pass
