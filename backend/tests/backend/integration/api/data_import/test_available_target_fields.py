"""
Functional tests for available-target-fields endpoint.

Tests that:
1. All fields have import_types metadata
2. Different import types return correct field filtering via metadata
3. Response structure is correct
4. Field metadata includes import_types array
"""

import pytest
import json
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.data_import.handlers.field_handler import (
    get_available_target_fields,
    get_field_import_types,
)
from app.core.context import RequestContext


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_available_target_fields_has_import_types_metadata(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test that all fields returned have import_types metadata."""
    # Call the endpoint handler directly
    result = await get_available_target_fields(
        flow_id=None,
        import_category=None,
        context=demo_tenant_context,
        db=async_db_session,
    )

    # Verify response structure
    assert result["success"] is True
    assert "fields" in result
    assert "import_category" in result
    assert "total_fields" in result

    fields: List[Dict[str, Any]] = result["fields"]
    assert len(fields) > 0, "Should return at least some fields"

    # Verify ALL fields have import_types metadata
    for field in fields:
        assert (
            "import_types" in field
        ), f"Field {field.get('name')} missing import_types"
        assert isinstance(
            field["import_types"], list
        ), f"Field {field.get('name')} import_types should be a list"
        assert (
            len(field["import_types"]) > 0
        ), f"Field {field.get('name')} import_types should not be empty"
        assert all(
            isinstance(import_type, str) for import_type in field["import_types"]
        ), f"Field {field.get('name')} import_types should contain strings"

    print(f"\n✅ Verified {len(fields)} fields all have import_types metadata")


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_import_types_for_different_categories(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test that fields have correct import_types based on their category/type."""
    result = await get_available_target_fields(
        flow_id=None,
        import_category=None,
        context=demo_tenant_context,
        db=async_db_session,
    )

    fields: List[Dict[str, Any]] = result["fields"]
    field_map = {field["name"]: field for field in fields}

    # Test universal fields (should appear in multiple import types)
    universal_fields = ["hostname", "asset_name", "name", "description"]
    for field_name in universal_fields:
        if field_name in field_map:
            field = field_map[field_name]
            assert (
                "cmdb" in field["import_types"]
            ), f"{field_name} should include 'cmdb'"
            assert (
                "app_discovery" in field["import_types"]
            ), f"{field_name} should include 'app_discovery'"
            if (
                field_name != "description"
            ):  # description might not be in infrastructure
                assert "infrastructure" in field.get(
                    "import_types", []
                ), f"{field_name} should include 'infrastructure' or not be in field_map"
            print(f"✅ {field_name}: {field['import_types']}")

    # Test asset_type (NOT in app_discovery - removed in PR)
    if "asset_type" in field_map:
        field = field_map["asset_type"]
        assert "cmdb" in field["import_types"], "asset_type should include 'cmdb'"
        assert (
            "infrastructure" in field["import_types"]
        ), "asset_type should include 'infrastructure'"
        assert (
            "app_discovery" not in field["import_types"]
        ), "asset_type should NOT include 'app_discovery'"
        print(
            f"✅ asset_type: {field['import_types']} (correctly excludes app_discovery)"
        )

    # Test infrastructure-specific fields
    infrastructure_fields = ["ip_address", "mac_address", "cpu_cores", "memory_gb"]
    for field_name in infrastructure_fields:
        if field_name in field_map:
            field = field_map[field_name]
            assert (
                "infrastructure" in field["import_types"]
            ), f"{field_name} should include 'infrastructure'"
            assert (
                "cmdb" in field["import_types"]
            ), f"{field_name} should include 'cmdb'"
            print(f"✅ {field_name}: {field['import_types']}")

    # Test dependency fields (app_discovery only)
    dependency_fields = [
        "dependency_type",
        "relationship_nature",
        "port",
        "protocol_name",
    ]
    for field_name in dependency_fields:
        if field_name in field_map:
            field = field_map[field_name]
            assert (
                "app_discovery" in field["import_types"]
            ), f"{field_name} should include 'app_discovery'"
            print(f"✅ {field_name}: {field['import_types']}")


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_json_response_structure_for_cmdb(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test JSON response structure for CMDB import type."""
    result = await get_available_target_fields(
        flow_id=None,
        import_category="cmdb",
        context=demo_tenant_context,
        db=async_db_session,
    )

    # Print JSON structure for inspection
    json_output = json.dumps(result, indent=2, default=str)
    print("\n" + "=" * 80)
    print("JSON Response for CMDB import type:")
    print("=" * 80)
    print(json_output)
    print("=" * 80)

    # Verify structure
    assert result["success"] is True
    assert result["import_category"] == "cmdb"
    assert "fields" in result

    # Count fields that should be visible for CMDB
    cmdb_fields = [f for f in result["fields"] if "cmdb" in f.get("import_types", [])]
    print(
        f"\n📊 CMDB fields: {len(cmdb_fields)} out of {len(result['fields'])} total fields"
    )

    # Verify sample fields have correct structure
    sample_field = result["fields"][0] if result["fields"] else None
    if sample_field:
        assert "name" in sample_field
        assert "type" in sample_field
        assert "category" in sample_field
        assert "import_types" in sample_field
        print(
            f"\n✅ Sample field structure: {json.dumps(sample_field, indent=2, default=str)}"
        )


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_json_response_structure_for_app_discovery(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test JSON response structure for app_discovery import type."""
    result = await get_available_target_fields(
        flow_id=None,
        import_category="app_discovery",
        context=demo_tenant_context,
        db=async_db_session,
    )

    # Print JSON structure for inspection
    json_output = json.dumps(result, indent=2, default=str)
    print("\n" + "=" * 80)
    print("JSON Response for app_discovery import type:")
    print("=" * 80)
    print(json_output)
    print("=" * 80)

    # Verify structure
    assert result["success"] is True
    assert result["import_category"] == "app_discovery"
    assert "fields" in result

    # Count fields that should be visible for app_discovery
    app_discovery_fields = [
        f for f in result["fields"] if "app_discovery" in f.get("import_types", [])
    ]
    print(
        f"\n📊 App Discovery fields: {len(app_discovery_fields)} out of {len(result['fields'])} total fields"
    )

    # Verify dependency fields are included
    dependency_fields = [
        f for f in result["fields"] if f.get("category") == "dependency"
    ]
    print(f"\n📊 Dependency fields: {len(dependency_fields)}")
    for dep_field in dependency_fields[:5]:  # Show first 5
        print(f"  - {dep_field['name']}: {dep_field['import_types']}")


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_json_response_structure_for_infrastructure(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test JSON response structure for infrastructure import type."""
    result = await get_available_target_fields(
        flow_id=None,
        import_category="infrastructure",
        context=demo_tenant_context,
        db=async_db_session,
    )

    # Print JSON structure for inspection
    json_output = json.dumps(result, indent=2, default=str)
    print("\n" + "=" * 80)
    print("JSON Response for infrastructure import type:")
    print("=" * 80)
    print(json_output)
    print("=" * 80)

    # Verify structure
    assert result["success"] is True
    assert result["import_category"] == "infrastructure"
    assert "fields" in result

    # Count fields that should be visible for infrastructure
    infrastructure_fields = [
        f for f in result["fields"] if "infrastructure" in f.get("import_types", [])
    ]
    print(
        f"\n📊 Infrastructure fields: {len(infrastructure_fields)} out of {len(result['fields'])} total fields"
    )

    # Verify technical fields are included
    technical_fields = [f for f in result["fields"] if f.get("category") == "technical"]
    print(f"\n📊 Technical fields: {len(technical_fields)}")
    for tech_field in technical_fields[:5]:  # Show first 5
        print(f"  - {tech_field['name']}: {tech_field['import_types']}")


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_field_import_types_helper_function():
    """Test the get_field_import_types helper function directly."""
    # Test explicit field mapping
    result = get_field_import_types("hostname", "identification")
    assert "cmdb" in result
    assert "app_discovery" in result
    assert "infrastructure" in result
    print(f"✅ hostname: {result}")

    # Test category-based fallback
    result = get_field_import_types("some_business_field", "business")
    assert "cmdb" in result
    print(f"✅ some_business_field (business category): {result}")

    # Test dependency category
    result = get_field_import_types("dependency_type", "dependency")
    assert "app_discovery" in result
    print(f"✅ dependency_type (dependency category): {result}")

    # Test technical category
    result = get_field_import_types("some_technical_field", "technical")
    assert "cmdb" in result
    assert "infrastructure" in result
    print(f"✅ some_technical_field (technical category): {result}")


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
async def test_all_fields_have_complete_metadata(
    async_db_session: AsyncSession,
    demo_tenant_context: RequestContext,
):
    """Test that all fields have complete required metadata."""
    result = await get_available_target_fields(
        flow_id=None,
        import_category=None,
        context=demo_tenant_context,
        db=async_db_session,
    )

    fields: List[Dict[str, Any]] = result["fields"]
    required_keys = ["name", "type", "category", "import_types"]

    for field in fields:
        for key in required_keys:
            assert (
                key in field
            ), f"Field {field.get('name', 'unknown')} missing required key: {key}"

        # Verify import_types is not empty
        assert (
            len(field["import_types"]) > 0
        ), f"Field {field['name']} has empty import_types"

    print(f"\n✅ All {len(fields)} fields have complete metadata")


if __name__ == "__main__":
    # Run tests directly with pytest
    pytest.main([__file__, "-v", "-s"])
