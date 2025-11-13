"""
Unit tests for asset-type-aware critical attributes filtering.

Tests the fix for issue #678: Gap analysis should be asset-type-aware.
"""

from app.services.collection.critical_attributes import CriticalAttributesDefinition


class TestAssetTypeAwareAttributes:
    """Test asset-type-specific attribute filtering."""

    def test_server_gets_infrastructure_attributes(self):
        """Servers should get infrastructure attributes, not application attributes."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("server")

        # Should have infrastructure attributes
        assert "operating_system" in attrs
        assert "cpu_cores" in attrs
        assert "memory_gb" in attrs
        assert "storage_gb" in attrs
        assert "environment" in attrs

        # Should NOT have application-specific attributes
        assert "technology_stack" not in attrs
        assert "application_architecture" not in attrs
        assert "integration_points" not in attrs
        assert "code_quality_score" not in attrs

    def test_application_gets_tech_stack_attributes(self):
        """Applications should get tech stack and business attributes, not infrastructure details."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("application")

        # Should have application attributes
        assert "technology_stack" in attrs
        assert "application_architecture" in attrs
        assert "integration_points" in attrs

        # Should have business attributes
        assert "business_criticality" in attrs
        assert "compliance_requirements" in attrs

        # Should have technical debt attributes
        assert "code_quality_score" in attrs
        assert "security_vulnerabilities" in attrs

        # Should NOT have low-level infrastructure
        assert "cpu_cores" not in attrs
        assert "memory_gb" not in attrs
        assert "storage_gb" not in attrs
        assert "virtualization_type" not in attrs

    def test_database_gets_storage_and_dependencies(self):
        """Databases should get storage, dependencies, and business attributes."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("database")

        # Should have database-specific attributes
        assert "database_type" in attrs
        assert "data_volume" in attrs
        assert "storage_gb" in attrs
        assert "storage_capacity" in attrs

        # Should have dependency attributes
        assert "upstream_dependencies" in attrs
        assert "downstream_dependents" in attrs

        # Should have business attributes
        assert "business_criticality" in attrs
        assert "compliance_requirements" in attrs

        # Should NOT have application code attributes
        assert "technology_stack" not in attrs
        assert "application_architecture" not in attrs
        assert "code_quality_score" not in attrs

    def test_network_device_attributes(self):
        """Network devices should get infrastructure and dependency attributes."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("network")

        # Should have infrastructure
        assert "operating_system" in attrs
        assert "environment" in attrs

        # Should have dependencies
        assert "upstream_dependencies" in attrs
        assert "downstream_dependents" in attrs

        # Should NOT have application attributes
        assert "technology_stack" not in attrs
        assert "code_quality_score" not in attrs

    def test_container_gets_mixed_attributes(self):
        """Containers should get application + infrastructure + dependency attributes."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("container")

        # Should have application attributes
        assert "technology_stack" in attrs
        assert "application_architecture" in attrs

        # Should have infrastructure (but not virtualization)
        assert "operating_system" in attrs
        assert "virtualization_type" not in attrs

        # Should have dependencies
        assert "database_type" in attrs

    def test_unknown_asset_type_gets_all_attributes(self):
        """Unknown asset types should get all attributes as fallback."""
        attrs = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "unknown_type"
        )

        # Should have attributes from all categories
        assert "operating_system" in attrs
        assert "technology_stack" in attrs
        assert "database_type" in attrs
        assert len(attrs) > 15  # Should have most/all attributes

    def test_case_insensitive_asset_type(self):
        """Asset type matching should be case-insensitive."""
        attrs_lower = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "server"
        )
        attrs_upper = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "SERVER"
        )
        attrs_mixed = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "Server"
        )

        assert attrs_lower == attrs_upper == attrs_mixed

    def test_all_asset_types_have_required_attributes(self):
        """All asset types should get required attributes (environment, business_criticality)."""
        asset_types = [
            "server",
            "application",
            "database",
            "network",
            "virtual_machine",
            "container",
            "storage",
        ]

        for asset_type in asset_types:
            attrs = CriticalAttributesDefinition.get_attributes_by_asset_type(
                asset_type
            )

            # Environment and business_criticality are marked as required
            if asset_type in [
                "server",
                "virtual_machine",
                "storage",
                "network",
                "container",
            ]:
                assert "environment" in attrs, f"{asset_type} should have 'environment'"

            if asset_type in ["application", "database", "container"]:
                assert (
                    "business_criticality" in attrs
                ), f"{asset_type} should have 'business_criticality'"

    def test_attribute_count_varies_by_type(self):
        """Different asset types should have different numbers of attributes."""
        server_attrs = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "server"
        )
        app_attrs = CriticalAttributesDefinition.get_attributes_by_asset_type(
            "application"
        )
        db_attrs = CriticalAttributesDefinition.get_attributes_by_asset_type("database")

        # Servers should have fewer attributes than applications
        assert len(server_attrs) < len(app_attrs)

        # All should be non-empty
        assert len(server_attrs) > 0
        assert len(app_attrs) > 0
        assert len(db_attrs) > 0

        # All should be less than total attributes
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()
        assert len(server_attrs) < len(all_attrs)
        assert len(app_attrs) < len(all_attrs)
        assert len(db_attrs) < len(all_attrs)

    def test_backward_compatibility_get_attribute_mapping(self):
        """Original get_attribute_mapping() should still return all attributes."""
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()

        # Should have all 22+ attributes
        assert len(all_attrs) >= 22

        # Should have attributes from all categories
        assert "operating_system" in all_attrs
        assert "technology_stack" in all_attrs
        assert "business_criticality" in all_attrs
        assert "code_quality_score" in all_attrs
        assert "database_type" in all_attrs
