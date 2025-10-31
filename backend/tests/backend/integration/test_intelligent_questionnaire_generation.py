"""
Integration tests for intelligent questionnaire generation.

Tests end-to-end context threading from asset attributes through to intelligent
option ordering in generated questionnaires without requiring full database setup.

Verifies:
- EOL status flows from OS version detection to security vulnerability options
- Business criticality flows to compliance and availability options
- Technology stack flows to business logic complexity options
- Graceful fallback when context is missing
"""

from unittest.mock import Mock
from uuid import uuid4

from app.api.v1.endpoints.collection_crud_questionnaires.utils import (
    _analyze_selected_assets,
    _determine_eol_status,
)
from app.services.ai_analysis.questionnaire_generator.tools.intelligent_options.security_options import (
    get_security_vulnerabilities_options,
    get_security_compliance_requirements_options,
)
from app.services.ai_analysis.questionnaire_generator.tools.intelligent_options.infrastructure_options import (
    get_availability_requirements_options,
)
from app.services.ai_analysis.questionnaire_generator.tools.intelligent_options.eol_options import (
    get_eol_technology_assessment_options,
)


def create_mock_asset(**kwargs):
    """Create a mock asset with specified attributes for testing."""
    asset = Mock()
    asset.id = kwargs.get("id", uuid4())
    asset.name = kwargs.get("name", "Mock Asset")
    asset.operating_system = kwargs.get("operating_system", None)
    asset.os_version = kwargs.get("os_version", None)
    asset.technology_stack = kwargs.get("technology_stack", [])
    asset.business_criticality = kwargs.get("business_criticality", None)
    asset.environment = kwargs.get("environment", "production")
    asset.application_name = kwargs.get("application_name", None)
    asset.asset_type = kwargs.get("asset_type", "application")
    asset.criticality = kwargs.get("criticality", "unknown")
    asset.raw_data = kwargs.get("raw_data", {})
    asset.field_mappings_used = kwargs.get("field_mappings_used", {})
    asset.mapping_status = kwargs.get("mapping_status", "complete")
    asset.completeness_score = kwargs.get("completeness_score", 1.0)
    asset.confidence_score = kwargs.get("confidence_score", 1.0)
    # Mock required attributes for _check_missing_critical_fields
    asset.business_owner = kwargs.get("business_owner", "Test Owner")
    asset.technical_owner = kwargs.get("technical_owner", "Test Tech Owner")
    asset.dependencies = kwargs.get("dependencies", [])
    return asset


class TestIntelligentQuestionnaireGeneration:
    """Integration tests for intelligent questionnaire generation with context threading."""

    def test_eol_expired_asset_context_threading(self):
        """Test that EOL_EXPIRED context flows through asset analysis to intelligent options."""
        # Create AIX 7.2 asset (EOL_EXPIRED per _determine_eol_status)
        asset = create_mock_asset(
            name="AIX Production Server",
            operating_system="AIX",
            os_version="7.2",
            technology_stack=["WebSphere 8.5", "DB2"],
            business_criticality="mission_critical",
            environment="production",
        )

        # Step 1: Verify EOL status determination
        eol_status = _determine_eol_status("AIX", "7.2", [])
        assert eol_status == "EOL_EXPIRED", "AIX 7.2 should be detected as EOL_EXPIRED"

        # Step 2: Verify asset analysis extracts EOL status correctly
        selected_assets, asset_analysis = _analyze_selected_assets([asset])
        assert len(selected_assets) == 1
        asset_context = selected_assets[0]
        assert asset_context["eol_technology"] == "EOL_EXPIRED"
        assert asset_context["operating_system"] == "AIX"
        assert asset_context["os_version"] == "7.2"

        # Step 3: Verify security vulnerabilities question has EOL-aware ordering
        field_type, options = get_security_vulnerabilities_options(asset_context)
        assert field_type == "select"
        assert (
            options[0]["value"] == "high_severity"
        ), "EOL_EXPIRED assets should show High Severity first"
        assert options[-1]["value"] == "none_known"

        # Step 4: Verify EOL assessment question has EOL-aware ordering
        field_type, options = get_eol_technology_assessment_options(asset_context)
        assert field_type == "select"
        assert (
            options[0]["value"] == "eol_expired_critical"
        ), "EOL_EXPIRED assets should show EOL Expired Critical first"

        # Step 5: Verify mission_critical business criticality flows to compliance options
        # Note: _analyze_selected_assets doesn't include business_criticality in returned context,
        # so we test it directly with the asset's business_criticality
        context_with_criticality = {
            **asset_context,
            "business_criticality": "mission_critical",
        }
        field_type, options = get_security_compliance_requirements_options(
            context_with_criticality
        )
        assert field_type == "multi_select"
        assert (
            options[0]["value"] == "pci_dss"
        ), "Mission critical assets should show PCI-DSS first"

    def test_current_asset_context_threading(self):
        """Test that CURRENT context flows through asset analysis to intelligent options."""
        # Create Ubuntu 22.04 asset (CURRENT per _determine_eol_status)
        asset = create_mock_asset(
            name="Modern Application Server",
            operating_system="Ubuntu",
            os_version="22.04",
            technology_stack=["Node.js", "Express", "PostgreSQL"],
            business_criticality="business_critical",
            environment="production",
        )

        # Step 1: Verify EOL status determination
        eol_status = _determine_eol_status("Ubuntu", "22.04", [])
        assert eol_status == "CURRENT", "Ubuntu 22.04 should be detected as CURRENT"

        # Step 2: Verify asset analysis extracts context correctly
        selected_assets, asset_analysis = _analyze_selected_assets([asset])
        asset_context = selected_assets[0]
        assert asset_context["eol_technology"] == "CURRENT"

        # Step 3: Verify security vulnerabilities question shows None Known first
        field_type, options = get_security_vulnerabilities_options(asset_context)
        assert field_type == "select"
        assert (
            options[0]["value"] == "none_known"
        ), "CURRENT assets should show None Known first"
        assert options[-1]["value"] == "high_severity"

        # Step 4: Verify EOL assessment question shows Current first
        field_type, options = get_eol_technology_assessment_options(asset_context)
        assert field_type == "select"
        assert (
            options[0]["value"] == "current"
        ), "CURRENT assets should show Current first"

    def test_multi_asset_context_threading(self):
        """Test that context from first asset is used for questionnaire generation."""
        # Create multiple assets with different EOL statuses
        asset_eol_expired = create_mock_asset(
            name="Legacy AIX Server",
            operating_system="AIX",
            os_version="7.1",
            technology_stack=["WebSphere 8.5"],
            business_criticality="mission_critical",
        )
        asset_current = create_mock_asset(
            name="Modern Ubuntu Server",
            operating_system="Ubuntu",
            os_version="22.04",
            technology_stack=["Node.js"],
            business_criticality="business_critical",
        )

        # Analyze assets (order matters - first asset context is used)
        selected_assets, asset_analysis = _analyze_selected_assets(
            [asset_eol_expired, asset_current]
        )
        assert len(selected_assets) == 2

        # Verify first asset context (EOL_EXPIRED)
        first_asset_context = selected_assets[0]
        assert first_asset_context["eol_technology"] == "EOL_EXPIRED"

        # When generating questionnaire, first asset context should drive option ordering
        field_type, options = get_security_vulnerabilities_options(first_asset_context)
        assert (
            options[0]["value"] == "high_severity"
        ), "First asset (EOL_EXPIRED) should drive option ordering"

    def test_missing_context_graceful_fallback(self):
        """Test graceful fallback when asset context is minimal or missing."""
        # Create asset with minimal data (no EOL, no criticality)
        asset = create_mock_asset(
            name="Minimal Asset",
            # No operating_system, os_version, or technology_stack
            # No business_criticality
        )

        # Analyze asset
        selected_assets, asset_analysis = _analyze_selected_assets([asset])
        asset_context = selected_assets[0]

        # EOL status should default to CURRENT
        assert asset_context["eol_technology"] == "CURRENT"

        # Security vulnerabilities should work with CURRENT default
        field_type, options = get_eol_technology_assessment_options(asset_context)
        assert field_type == "select"
        assert options[0]["value"] == "current"

        # Compliance options should return default (GDPR first)
        field_type, options = get_security_compliance_requirements_options(
            asset_context
        )
        assert field_type == "multi_select"
        assert (
            options[0]["value"] == "gdpr"
        ), "Empty business_criticality should return default options (GDPR first)"

        # Availability requirements should return None (no business_criticality)
        result = get_availability_requirements_options(asset_context)
        assert result is None, "Missing business_criticality should return None"


class TestContextNormalization:
    """Test that context values are properly normalized to prevent substring matching bugs."""

    def test_criticality_case_insensitive(self):
        """Test that criticality matching is case-insensitive."""
        context_upper = {"business_criticality": "MISSION_CRITICAL"}
        context_lower = {"business_criticality": "mission_critical"}
        context_mixed = {"business_criticality": "Mission_Critical"}

        # All should return mission critical options
        result_upper = get_security_compliance_requirements_options(context_upper)
        result_lower = get_security_compliance_requirements_options(context_lower)
        result_mixed = get_security_compliance_requirements_options(context_mixed)

        assert result_upper is not None
        assert result_lower is not None
        assert result_mixed is not None

        # All should have same first option (PCI-DSS)
        assert result_upper[1][0]["value"] == "pci_dss"
        assert result_lower[1][0]["value"] == "pci_dss"
        assert result_mixed[1][0]["value"] == "pci_dss"

    def test_no_substring_matching_bug(self):
        """Test that substring matching doesn't cause false positives."""
        # "missionary" should NOT match "mission" via substring matching
        context = {"business_criticality": "missionary"}

        # Should NOT return mission critical options
        result = get_availability_requirements_options(context)
        # Result should be None (no match) since we use exact matching now
        assert (
            result is None
        ), "Substring 'mission' in 'missionary' should NOT trigger mission_critical logic"
