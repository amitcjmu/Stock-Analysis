"""
Import and structure verification tests for AssessmentApplicationResolver.

Since aiosqlite is not installed in the Docker environment, these tests verify
that the service can be imported and that its structure is correct.

Full database tests should be run in integration tests with PostgreSQL.
"""

import pytest
from inspect import signature

# Test imports
from app.services.assessment.application_resolver import AssessmentApplicationResolver
from app.schemas.assessment_flow import (
    ApplicationAssetGroup,
    EnrichmentStatus,
    ReadinessSummary,
)


def test_import_service():
    """Test that AssessmentApplicationResolver can be imported."""
    assert AssessmentApplicationResolver is not None


def test_service_has_required_methods():
    """Test that service has all required methods."""
    required_methods = [
        "resolve_assets_to_applications",
        "calculate_enrichment_status",
        "calculate_readiness_summary",
    ]

    for method_name in required_methods:
        assert hasattr(
            AssessmentApplicationResolver, method_name
        ), f"Missing method: {method_name}"


def test_init_signature():
    """Test __init__ has correct signature."""
    sig = signature(AssessmentApplicationResolver.__init__)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "db" in params
    assert "client_account_id" in params
    assert "engagement_id" in params


def test_resolve_assets_to_applications_signature():
    """Test resolve_assets_to_applications has correct signature."""
    sig = signature(AssessmentApplicationResolver.resolve_assets_to_applications)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "asset_ids" in params
    assert "collection_flow_id" in params


def test_calculate_enrichment_status_signature():
    """Test calculate_enrichment_status has correct signature."""
    sig = signature(AssessmentApplicationResolver.calculate_enrichment_status)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "asset_ids" in params


def test_calculate_readiness_summary_signature():
    """Test calculate_readiness_summary has correct signature."""
    sig = signature(AssessmentApplicationResolver.calculate_readiness_summary)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "asset_ids" in params


def test_schema_imports():
    """Test that all required Pydantic schemas can be imported."""
    assert ApplicationAssetGroup is not None
    assert EnrichmentStatus is not None
    assert ReadinessSummary is not None


def test_application_asset_group_fields():
    """Test ApplicationAssetGroup has required fields."""
    required_fields = [
        "canonical_application_id",
        "canonical_application_name",
        "asset_ids",
        "asset_count",
        "asset_types",
        "readiness_summary",
    ]

    schema = ApplicationAssetGroup.model_json_schema()
    properties = schema.get("properties", {})

    for field in required_fields:
        assert field in properties, f"Missing field in ApplicationAssetGroup: {field}"


def test_enrichment_status_fields():
    """Test EnrichmentStatus has all 7 enrichment table fields."""
    required_fields = [
        "compliance_flags",
        "licenses",
        "vulnerabilities",
        "resilience",
        "dependencies",
        "product_links",
        "field_conflicts",
    ]

    schema = EnrichmentStatus.model_json_schema()
    properties = schema.get("properties", {})

    for field in required_fields:
        assert field in properties, f"Missing field in EnrichmentStatus: {field}"


def test_readiness_summary_fields():
    """Test ReadinessSummary has required fields."""
    required_fields = [
        "total_assets",
        "ready",
        "not_ready",
        "in_progress",
        "avg_completeness_score",
    ]

    schema = ReadinessSummary.model_json_schema()
    properties = schema.get("properties", {})

    for field in required_fields:
        assert field in properties, f"Missing field in ReadinessSummary: {field}"


def test_enrichment_status_instantiation():
    """Test EnrichmentStatus can be instantiated with default values."""
    status = EnrichmentStatus()

    assert status.compliance_flags == 0
    assert status.licenses == 0
    assert status.vulnerabilities == 0
    assert status.resilience == 0
    assert status.dependencies == 0
    assert status.product_links == 0
    assert status.field_conflicts == 0


def test_readiness_summary_instantiation():
    """Test ReadinessSummary can be instantiated with default values."""
    summary = ReadinessSummary()

    assert summary.total_assets == 0
    assert summary.ready == 0
    assert summary.not_ready == 0
    assert summary.in_progress == 0
    assert summary.avg_completeness_score == 0.0


def test_enrichment_status_with_data():
    """Test EnrichmentStatus can be instantiated with data."""
    status = EnrichmentStatus(
        compliance_flags=2,
        licenses=1,
        vulnerabilities=3,
        resilience=1,
        dependencies=4,
        product_links=0,
        field_conflicts=2,
    )

    assert status.compliance_flags == 2
    assert status.licenses == 1
    assert status.vulnerabilities == 3
    assert status.resilience == 1
    assert status.dependencies == 4
    assert status.product_links == 0
    assert status.field_conflicts == 2


def test_readiness_summary_with_data():
    """Test ReadinessSummary can be instantiated with data."""
    summary = ReadinessSummary(
        total_assets=10,
        ready=5,
        not_ready=3,
        in_progress=2,
        avg_completeness_score=0.75,
    )

    assert summary.total_assets == 10
    assert summary.ready == 5
    assert summary.not_ready == 3
    assert summary.in_progress == 2
    assert summary.avg_completeness_score == 0.75


def test_service_has_docstrings():
    """Test that service class and methods have docstrings."""
    assert AssessmentApplicationResolver.__doc__ is not None

    assert (
        AssessmentApplicationResolver.resolve_assets_to_applications.__doc__ is not None
    )
    assert AssessmentApplicationResolver.calculate_enrichment_status.__doc__ is not None
    assert AssessmentApplicationResolver.calculate_readiness_summary.__doc__ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
