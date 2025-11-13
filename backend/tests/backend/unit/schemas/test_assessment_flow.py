"""
Unit tests for Assessment Flow Pydantic schemas.

Tests the new schemas introduced in October 2025 data model refactor:
- ApplicationAssetGroup
- EnrichmentStatus
- ReadinessSummary
- AssessmentFlowCreateRequest (with new fields)
"""

import pytest
from uuid import UUID
from pydantic import ValidationError

from app.schemas.assessment_flow import (
    ApplicationAssetGroup,
    EnrichmentStatus,
    ReadinessSummary,
    AssessmentFlowCreateRequest,
)


class TestApplicationAssetGroup:
    """Test ApplicationAssetGroup schema validation."""

    def test_valid_application_asset_group_with_canonical_id(self):
        """Test ApplicationAssetGroup with canonical application ID."""
        group = ApplicationAssetGroup(
            canonical_application_id=UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a"),
            canonical_application_name="CRM System",
            asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            asset_count=1,
            asset_types=["server"],
            readiness_summary={"ready": 1, "not_ready": 0},
        )

        assert group.canonical_application_id == UUID(
            "05459507-86cb-41f9-9c2d-2a9f4a50445a"
        )
        assert group.canonical_application_name == "CRM System"
        assert len(group.asset_ids) == 1
        assert group.asset_count == 1
        assert "server" in group.asset_types
        assert group.readiness_summary["ready"] == 1

    def test_application_asset_group_unmapped_asset(self):
        """Test ApplicationAssetGroup for unmapped assets (canonical_application_id = None)."""
        unmapped = ApplicationAssetGroup(
            canonical_application_id=None,
            canonical_application_name="Unmapped Asset - Server01",
            asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            asset_count=1,
            asset_types=["server"],
            readiness_summary={"ready": 0, "not_ready": 1},
        )

        assert unmapped.canonical_application_id is None
        assert "Unmapped" in unmapped.canonical_application_name
        assert unmapped.readiness_summary["not_ready"] == 1

    def test_application_asset_group_with_multiple_assets(self):
        """Test ApplicationAssetGroup with multiple assets and types."""
        group = ApplicationAssetGroup(
            canonical_application_id=UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a"),
            canonical_application_name="E-Commerce Platform",
            asset_ids=[
                UUID("c4ed088f-6658-405b-b011-8ce50c065ddf"),
                UUID("d5fe199f-7769-516c-c122-9df61d176eef"),
                UUID("e6ff200a-8870-627d-d233-0ea72e287ff0"),
            ],
            asset_count=3,
            asset_types=["server", "database", "network_device"],
            readiness_summary={"ready": 2, "not_ready": 1, "in_progress": 0},
        )

        assert group.asset_count == 3
        assert len(group.asset_ids) == 3
        assert len(group.asset_types) == 3
        assert sum(group.readiness_summary.values()) == 3

    def test_application_asset_group_defaults(self):
        """Test ApplicationAssetGroup with minimal required fields."""
        group = ApplicationAssetGroup(canonical_application_name="Minimal Application")

        assert group.canonical_application_id is None
        assert group.asset_ids == []
        assert group.asset_count == 0
        assert group.asset_types == []
        assert group.readiness_summary == {}

    def test_application_asset_group_invalid_asset_count(self):
        """Test ApplicationAssetGroup rejects negative asset count."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationAssetGroup(
                canonical_application_name="Test App",
                asset_count=-1,  # Invalid: negative count
            )

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_application_asset_group_json_serialization(self):
        """Test ApplicationAssetGroup can be serialized to JSON."""
        group = ApplicationAssetGroup(
            canonical_application_id=UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a"),
            canonical_application_name="CRM System",
            asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            asset_count=1,
            asset_types=["server"],
            readiness_summary={"ready": 1, "not_ready": 0},
        )

        json_data = group.model_dump_json()
        assert "05459507-86cb-41f9-9c2d-2a9f4a50445a" in json_data
        assert "CRM System" in json_data


class TestEnrichmentStatus:
    """Test EnrichmentStatus schema validation."""

    def test_enrichment_status_defaults(self):
        """Test EnrichmentStatus default values are all zero."""
        status = EnrichmentStatus()

        assert status.compliance_flags == 0
        assert status.licenses == 0
        assert status.vulnerabilities == 0
        assert status.resilience == 0
        assert status.dependencies == 0
        assert status.product_links == 0
        assert status.field_conflicts == 0

    def test_enrichment_status_with_values(self):
        """Test EnrichmentStatus with actual enrichment data."""
        status = EnrichmentStatus(
            compliance_flags=2,
            licenses=0,
            vulnerabilities=3,
            resilience=1,
            dependencies=4,
            product_links=0,
            field_conflicts=0,
        )

        assert status.compliance_flags == 2
        assert status.vulnerabilities == 3
        assert status.dependencies == 4

    def test_enrichment_status_rejects_negative_values(self):
        """Test EnrichmentStatus rejects negative counts."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichmentStatus(compliance_flags=-1)  # Invalid: negative count

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_enrichment_status_all_fields_populated(self):
        """Test EnrichmentStatus with all enrichment types populated."""
        status = EnrichmentStatus(
            compliance_flags=5,
            licenses=3,
            vulnerabilities=8,
            resilience=2,
            dependencies=10,
            product_links=4,
            field_conflicts=1,
        )

        # Total enrichments should be meaningful
        total_enrichments = (
            status.compliance_flags
            + status.licenses
            + status.vulnerabilities
            + status.resilience
            + status.dependencies
            + status.product_links
            + status.field_conflicts
        )
        assert total_enrichments == 33


class TestReadinessSummary:
    """Test ReadinessSummary schema validation."""

    def test_readiness_summary_defaults(self):
        """Test ReadinessSummary default values."""
        summary = ReadinessSummary()

        assert summary.total_assets == 0
        assert summary.ready == 0
        assert summary.not_ready == 0
        assert summary.in_progress == 0
        assert summary.avg_completeness_score == 0.0

    def test_readiness_summary_valid(self):
        """Test ReadinessSummary with valid data."""
        summary = ReadinessSummary(
            total_assets=5,
            ready=2,
            not_ready=3,
            in_progress=0,
            avg_completeness_score=0.64,
        )

        assert summary.total_assets == 5
        assert summary.ready == 2
        assert summary.not_ready == 3
        assert summary.avg_completeness_score == 0.64

    def test_readiness_summary_completeness_score_bounds(self):
        """Test ReadinessSummary validates completeness score bounds (0.0-1.0)."""
        # Valid: score = 0.0
        summary_min = ReadinessSummary(
            total_assets=1, not_ready=1, avg_completeness_score=0.0
        )
        assert summary_min.avg_completeness_score == 0.0

        # Valid: score = 1.0
        summary_max = ReadinessSummary(
            total_assets=1, ready=1, avg_completeness_score=1.0
        )
        assert summary_max.avg_completeness_score == 1.0

        # Invalid: score > 1.0
        with pytest.raises(ValidationError) as exc_info:
            ReadinessSummary(
                total_assets=1, ready=1, avg_completeness_score=1.5  # Invalid: > 1.0
            )
        assert "less than or equal to 1" in str(exc_info.value)

        # Invalid: score < 0.0
        with pytest.raises(ValidationError) as exc_info:
            ReadinessSummary(
                total_assets=1,
                not_ready=1,
                avg_completeness_score=-0.1,  # Invalid: < 0.0
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_readiness_summary_negative_counts(self):
        """Test ReadinessSummary rejects negative asset counts."""
        with pytest.raises(ValidationError) as exc_info:
            ReadinessSummary(total_assets=-1)  # Invalid: negative count

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_readiness_summary_consistency(self):
        """Test ReadinessSummary with consistent ready/not_ready counts."""
        summary = ReadinessSummary(
            total_assets=10,
            ready=6,
            not_ready=3,
            in_progress=1,
            avg_completeness_score=0.75,
        )

        # ready + not_ready + in_progress should equal total_assets
        assert (
            summary.ready + summary.not_ready + summary.in_progress
            == summary.total_assets
        )


class TestAssessmentFlowCreateRequest:
    """Test AssessmentFlowCreateRequest schema with new fields."""

    def test_assessment_flow_create_old_format_backward_compatibility(self):
        """Test backward compatibility with deprecated selected_application_ids."""
        # Old format (deprecated field)
        old_format = AssessmentFlowCreateRequest(
            selected_application_ids=["c4ed088f-6658-405b-b011-8ce50c065ddf"]
        )

        assert len(old_format.selected_application_ids) == 1
        assert old_format.selected_asset_ids == []  # New field defaults to empty

    def test_assessment_flow_create_new_format(self):
        """Test new format with proper semantic fields."""
        new_format = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            selected_canonical_application_ids=[
                UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a")
            ],
        )

        assert len(new_format.selected_asset_ids) == 1
        assert len(new_format.selected_canonical_application_ids) == 1
        assert (
            new_format.selected_application_ids is None
        )  # Deprecated field not provided

    def test_assessment_flow_create_with_application_asset_groups(self):
        """Test AssessmentFlowCreateRequest with application-asset groupings."""
        request = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            selected_canonical_application_ids=[
                UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a")
            ],
            application_asset_groups=[
                ApplicationAssetGroup(
                    canonical_application_id=UUID(
                        "05459507-86cb-41f9-9c2d-2a9f4a50445a"
                    ),
                    canonical_application_name="CRM System",
                    asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
                    asset_count=1,
                    asset_types=["server"],
                    readiness_summary={"ready": 1, "not_ready": 0},
                )
            ],
        )

        assert len(request.application_asset_groups) == 1
        assert (
            request.application_asset_groups[0].canonical_application_name
            == "CRM System"
        )

    def test_assessment_flow_create_with_enrichment_status(self):
        """Test AssessmentFlowCreateRequest with enrichment status."""
        request = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            enrichment_status=EnrichmentStatus(
                compliance_flags=1, vulnerabilities=2, dependencies=3
            ),
        )

        assert request.enrichment_status.compliance_flags == 1
        assert request.enrichment_status.vulnerabilities == 2
        assert request.enrichment_status.dependencies == 3

    def test_assessment_flow_create_with_readiness_summary(self):
        """Test AssessmentFlowCreateRequest with readiness summary."""
        request = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            readiness_summary=ReadinessSummary(
                total_assets=1, ready=1, not_ready=0, avg_completeness_score=0.85
            ),
        )

        assert request.readiness_summary.total_assets == 1
        assert request.readiness_summary.ready == 1
        assert request.readiness_summary.avg_completeness_score == 0.85

    def test_assessment_flow_create_complete_example(self):
        """Test AssessmentFlowCreateRequest with all new fields populated."""
        request = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            selected_canonical_application_ids=[
                UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a")
            ],
            application_asset_groups=[
                ApplicationAssetGroup(
                    canonical_application_id=UUID(
                        "05459507-86cb-41f9-9c2d-2a9f4a50445a"
                    ),
                    canonical_application_name="CRM System",
                    asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
                    asset_count=1,
                    asset_types=["server"],
                    readiness_summary={"ready": 1, "not_ready": 0},
                )
            ],
            enrichment_status=EnrichmentStatus(
                compliance_flags=0,
                licenses=0,
                vulnerabilities=0,
                resilience=0,
                dependencies=0,
                product_links=0,
                field_conflicts=0,
            ),
            readiness_summary=ReadinessSummary(
                total_assets=1,
                ready=1,
                not_ready=0,
                in_progress=0,
                avg_completeness_score=0.85,
            ),
        )

        # Validate all fields are properly set
        assert len(request.selected_asset_ids) == 1
        assert len(request.selected_canonical_application_ids) == 1
        assert len(request.application_asset_groups) == 1
        assert request.enrichment_status is not None
        assert request.readiness_summary is not None
        assert request.readiness_summary.avg_completeness_score == 0.85

    def test_assessment_flow_create_max_assets_validation(self):
        """Test AssessmentFlowCreateRequest rejects more than 100 assets."""
        # Create 101 fake asset UUIDs
        too_many_assets = [
            UUID(f"00000000-0000-0000-0000-{str(i).zfill(12)}") for i in range(101)
        ]

        with pytest.raises(ValidationError) as exc_info:
            AssessmentFlowCreateRequest(selected_asset_ids=too_many_assets)

        assert "Maximum 100 assets" in str(exc_info.value)

    def test_assessment_flow_create_invalid_application_ids_format(self):
        """Test AssessmentFlowCreateRequest validates deprecated field format."""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentFlowCreateRequest(
                selected_application_ids=["", "valid-id"]  # Empty string invalid
            )

        assert "non-empty strings" in str(exc_info.value)

    def test_assessment_flow_create_minimal_valid_request(self):
        """Test AssessmentFlowCreateRequest with minimal required fields."""
        # With new format: selected_asset_ids has default empty list
        request = AssessmentFlowCreateRequest()

        assert request.selected_asset_ids == []
        assert request.selected_canonical_application_ids == []
        assert request.application_asset_groups == []
        assert request.enrichment_status is None
        assert request.readiness_summary is None


class TestSchemaInteroperability:
    """Test interoperability between schemas."""

    def test_nested_schemas_in_request(self):
        """Test nested schemas work correctly in AssessmentFlowCreateRequest."""
        # Create nested schemas
        app_group = ApplicationAssetGroup(
            canonical_application_id=UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a"),
            canonical_application_name="Test App",
            asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            asset_count=1,
            asset_types=["server"],
            readiness_summary={"ready": 1},
        )

        enrichment = EnrichmentStatus(compliance_flags=1)
        readiness = ReadinessSummary(
            total_assets=1, ready=1, avg_completeness_score=1.0
        )

        # Create request with all nested schemas
        request = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            application_asset_groups=[app_group],
            enrichment_status=enrichment,
            readiness_summary=readiness,
        )

        # Verify nested schemas are accessible
        assert (
            request.application_asset_groups[0].canonical_application_name == "Test App"
        )
        assert request.enrichment_status.compliance_flags == 1
        assert request.readiness_summary.avg_completeness_score == 1.0

    def test_json_serialization_round_trip(self):
        """Test schemas can be serialized to JSON and deserialized back."""
        original = AssessmentFlowCreateRequest(
            selected_asset_ids=[UUID("c4ed088f-6658-405b-b011-8ce50c065ddf")],
            selected_canonical_application_ids=[
                UUID("05459507-86cb-41f9-9c2d-2a9f4a50445a")
            ],
            enrichment_status=EnrichmentStatus(compliance_flags=2),
            readiness_summary=ReadinessSummary(
                total_assets=1, ready=1, avg_completeness_score=0.9
            ),
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize back
        import json

        data = json.loads(json_str)
        reconstructed = AssessmentFlowCreateRequest(**data)

        # Verify fields match
        assert reconstructed.selected_asset_ids == original.selected_asset_ids
        assert reconstructed.enrichment_status.compliance_flags == 2
        assert reconstructed.readiness_summary.avg_completeness_score == 0.9
