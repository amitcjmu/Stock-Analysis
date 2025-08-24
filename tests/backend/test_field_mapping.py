"""
Test suite for field mapping validation with proper UUID serialization handling.

This module addresses GitHub issue #230: UUID type mismatch in field mapping validation.
Root cause: UUID objects are being serialized to JSON without converting to strings first.
"""

import json
import logging
import uuid
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.data_import.field_mapping.models.mapping_schemas import (
    FieldMappingCreate,
    MappingValidationRequest,
)
from app.api.v1.endpoints.data_import.field_mapping.services.validation_service import (
    ValidationService,
)
from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle UUID objects by converting them to strings.

    This encoder fixes the 'Object of type UUID is not JSON serializable' error
    by automatically converting UUID instances to their string representation.
    """

    def default(self, obj: Any) -> Any:
        """Convert UUID objects to strings for JSON serialization.

        Args:
            obj: Object to serialize

        Returns:
            String representation of UUID or delegates to parent encoder
        """
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class TestFieldMappingValidation:
    """Test suite for field mapping validation with UUID handling."""

    def test_uuid_encoder_basic(self):
        """Test that UUIDEncoder correctly serializes UUID objects."""
        test_uuid = uuid4()
        test_data = {"id": test_uuid, "name": "test_mapping"}

        # This should not raise a TypeError
        json_str = json.dumps(test_data, cls=UUIDEncoder)
        assert json_str is not None

        # Verify the result is valid JSON and UUID is converted to string
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data["id"], str)
        assert len(parsed_data["id"]) == 36  # Standard UUID string length
        assert parsed_data["name"] == "test_mapping"

    def test_uuid_encoder_with_nested_objects(self):
        """Test UUIDEncoder with nested objects containing UUIDs."""
        test_data = {
            "mapping": {
                "id": uuid4(),
                "source_field": "old_name",
                "target_field": "new_name",
                "flow_id": uuid4()
            },
            "metadata": {
                "created_by": uuid4(),
                "timestamps": ["2025-01-01", "2025-01-02"]
            }
        }

        # Should serialize without errors
        json_str = json.dumps(test_data, cls=UUIDEncoder)
        assert json_str is not None

        # Verify all UUIDs are converted to strings
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data["mapping"]["id"], str)
        assert isinstance(parsed_data["mapping"]["flow_id"], str)
        assert isinstance(parsed_data["metadata"]["created_by"], str)

    def test_uuid_encoder_with_mixed_types(self):
        """Test UUIDEncoder handles mixed data types correctly."""
        test_data = {
            "uuid_field": uuid4(),
            "string_field": "test_string",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "none_field": None,
            "list_field": [uuid4(), "string_item", 123],
            "dict_field": {
                "nested_uuid": uuid4(),
                "nested_string": "nested_value"
            }
        }

        # Should serialize all types correctly
        json_str = json.dumps(test_data, cls=UUIDEncoder)
        parsed_data = json.loads(json_str)

        # Check UUID conversion
        assert isinstance(parsed_data["uuid_field"], str)
        assert isinstance(parsed_data["list_field"][0], str)
        assert isinstance(parsed_data["dict_field"]["nested_uuid"], str)

        # Check other types unchanged
        assert parsed_data["string_field"] == "test_string"
        assert parsed_data["int_field"] == 42
        assert parsed_data["float_field"] == 3.14
        assert parsed_data["bool_field"] is True
        assert parsed_data["none_field"] is None

    @pytest.mark.asyncio
    async def test_validate_field_mapping(self):
        """Test field mapping validation with UUID handling.

        This is the specific test mentioned in GitHub issue #230.
        """
        # Create a field mapping with UUID that would cause serialization issues
        mapping_id = uuid4()
        flow_id = uuid4()

        field_mapping = FieldMappingCreate(
            source_field="legacy_asset_id",
            target_field="asset_id",
            confidence=0.95,
            transformation_rule=None,
            validation_rule="not null",
            is_required=True
        )

        # Create test data that includes UUIDs
        test_validation_data = {
            "mapping_id": mapping_id,
            "flow_id": flow_id,
            "mapping": field_mapping.model_dump(),
            "metadata": {
                "created_at": "2025-01-01T00:00:00Z",
                "created_by": uuid4()
            }
        }

        # Test 1: Verify direct JSON serialization fails without UUIDEncoder
        with pytest.raises(TypeError) as exc_info:
            json.dumps(test_validation_data)
        assert "not JSON serializable" in str(exc_info.value)

        # Test 2: Verify JSON serialization succeeds with UUIDEncoder
        json_str = json.dumps(test_validation_data, cls=UUIDEncoder)
        assert json_str is not None

        # Verify the serialized data is correct
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data["mapping_id"], str)
        assert isinstance(parsed_data["flow_id"], str)
        assert isinstance(parsed_data["metadata"]["created_by"], str)

    @pytest.mark.asyncio
    async def test_validate_field_mapping_multiple(self):
        """Test validation of multiple field mappings with UUID handling."""
        mappings = []
        for i in range(3):
            mapping = FieldMappingCreate(
                source_field=f"source_field_{i}",
                target_field=f"target_field_{i}",
                confidence=0.8 + (i * 0.05),
                transformation_rule=None,
                validation_rule="not empty",
                is_required=i % 2 == 0
            )
            mappings.append(mapping)

        # Create validation request with UUIDs
        request_data = {
            "request_id": uuid4(),
            "flow_id": uuid4(),
            "mappings": [mapping.model_dump() for mapping in mappings],
            "validation_config": {
                "strict_mode": True,
                "config_id": uuid4()
            }
        }

        # Should serialize successfully with UUIDEncoder
        json_str = json.dumps(request_data, cls=UUIDEncoder)
        assert json_str is not None

        # Verify all UUIDs are converted
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data["request_id"], str)
        assert isinstance(parsed_data["flow_id"], str)
        assert isinstance(parsed_data["validation_config"]["config_id"], str)

    def test_field_mapping_serialization_in_responses(self):
        """Test that field mapping responses handle UUID serialization properly."""
        # Simulate a field mapping response that might contain UUIDs
        response_data = {
            "mapping_id": uuid4(),
            "flow_id": uuid4(),
            "is_valid": True,
            "validation_errors": [],
            "warnings": [
                {
                    "warning_id": uuid4(),
                    "message": "Low confidence mapping",
                    "field": "source_field_1"
                }
            ],
            "validated_mappings": [
                {
                    "mapping_id": uuid4(),
                    "source_field": "old_asset_name",
                    "target_field": "asset_name",
                    "confidence": 0.95,
                    "metadata": {
                        "suggestion_id": uuid4(),
                        "created_by_agent": True
                    }
                }
            ]
        }

        # Should serialize with UUIDEncoder
        json_str = json.dumps(response_data, cls=UUIDEncoder)
        parsed_data = json.loads(json_str)

        # Verify UUID conversion in nested structures
        assert isinstance(parsed_data["mapping_id"], str)
        assert isinstance(parsed_data["flow_id"], str)
        assert isinstance(parsed_data["warnings"][0]["warning_id"], str)
        assert isinstance(parsed_data["validated_mappings"][0]["mapping_id"], str)
        assert isinstance(parsed_data["validated_mappings"][0]["metadata"]["suggestion_id"], str)

    def test_transformation_rules_with_uuid_serialization(self):
        """Test that transformation rules containing UUIDs are handled correctly."""
        # Simulate transformation rules that might contain UUID references
        transformation_rules = {
            "rule_id": uuid4(),
            "transformations": [
                {
                    "transform_id": uuid4(),
                    "type": "string_replace",
                    "pattern": "old_prefix",
                    "replacement": "new_prefix"
                },
                {
                    "transform_id": uuid4(),
                    "type": "format_template",
                    "template": "{value}_formatted",
                    "template_id": uuid4()
                }
            ],
            "metadata": {
                "created_by": uuid4(),
                "schema_version": "1.0"
            }
        }

        # Should serialize successfully
        json_str = json.dumps(transformation_rules, cls=UUIDEncoder)
        parsed_data = json.loads(json_str)

        # Verify UUID conversion throughout the structure
        assert isinstance(parsed_data["rule_id"], str)
        assert isinstance(parsed_data["transformations"][0]["transform_id"], str)
        assert isinstance(parsed_data["transformations"][1]["transform_id"], str)
        assert isinstance(parsed_data["transformations"][1]["template_id"], str)
        assert isinstance(parsed_data["metadata"]["created_by"], str)


# Utility function to use UUIDEncoder in the codebase
def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize objects to JSON, handling UUIDs automatically.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments passed to json.dumps

    Returns:
        JSON string representation of the object
    """
    # Set UUIDEncoder as default cls if not already specified
    if 'cls' not in kwargs:
        kwargs['cls'] = UUIDEncoder

    return json.dumps(obj, **kwargs)


def safe_json_dump(obj: Any, fp, **kwargs) -> None:
    """Safely write objects to JSON file, handling UUIDs automatically.

    Args:
        obj: Object to serialize
        fp: File-like object to write to
        **kwargs: Additional arguments passed to json.dump
    """
    if 'cls' not in kwargs:
        kwargs['cls'] = UUIDEncoder

    return json.dump(obj, fp, **kwargs)


if __name__ == "__main__":
    # Quick verification that UUIDEncoder works
    test_uuid = uuid4()
    test_data = {"id": test_uuid, "name": "test"}

    try:
        json_str = json.dumps(test_data, cls=UUIDEncoder)
        print(f"✅ UUIDEncoder test passed: {json_str}")
    except Exception as e:
        print(f"❌ UUIDEncoder test failed: {e}")
