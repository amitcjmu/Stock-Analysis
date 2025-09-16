#!/usr/bin/env python3
"""
Test script to verify field mapping validation against Asset model
"""

import asyncio
import sys

sys.path.insert(0, "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend")

from app.services.crewai_flows.unified_discovery_flow.handlers.field_mapping_generator.base import (
    FieldMappingGeneratorBase,
)


async def test_field_mapping():
    """Test field mapping validation"""

    # Create a mock flow instance
    class MockFlow:
        pass

    mapper = FieldMappingGeneratorBase(MockFlow())

    # Test cases: source field -> expected target field
    test_cases = [
        # Valid direct mappings
        ("name", "name"),
        ("hostname", "hostname"),
        ("ip_address", "ip_address"),
        # Common mappings that should be normalized
        ("Server_Name", "name"),
        ("Host", "hostname"),
        ("IP", "ip_address"),
        ("CPU", "cpu_cores"),
        ("Memory", "memory_gb"),
        ("OS", "operating_system"),
        # Fields that should be UNMAPPED
        ("cpu_utilization", "UNMAPPED"),
        ("memory_utilization", "UNMAPPED"),
        ("aws_readiness", "UNMAPPED"),
        ("migration_readiness", "UNMAPPED"),
        ("random_field_123", "UNMAPPED"),
        # Business fields
        ("Owner", "business_owner"),
        ("Department", "department"),
        ("Environment", "environment"),
        # Complex mappings
        ("Device_Name", "name"),
        ("Device_Type", "asset_type"),
        ("Datacenter", "datacenter"),
    ]

    print("Testing field mapping validation...")
    print("-" * 60)

    all_passed = True
    for source_field, expected_target in test_cases:
        target = mapper._map_common_field_names(source_field)
        status = "✅" if target == expected_target else "❌"

        if target != expected_target:
            all_passed = False

        print(
            f"{status} {source_field:25} -> {target:25} (expected: {expected_target})"
        )

    print("-" * 60)

    # Test that all valid Asset fields are recognized
    valid_fields = mapper._get_valid_asset_fields()
    print(f"\n✅ Total valid Asset fields: {len(valid_fields)}")

    # Test a few important fields are in the valid set
    important_fields = [
        "name",
        "hostname",
        "ip_address",
        "cpu_cores",
        "memory_gb",
        "asset_type",
    ]
    for field in important_fields:
        if field in valid_fields:
            print(f"  ✅ {field} is a valid Asset field")
        else:
            print(f"  ❌ {field} should be a valid Asset field!")
            all_passed = False

    if all_passed:
        print("\n🎉 All field mapping tests passed!")
    else:
        print("\n❌ Some field mapping tests failed!")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_field_mapping())
    sys.exit(0 if result else 1)
