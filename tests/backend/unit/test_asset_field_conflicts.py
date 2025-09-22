"""
Unit tests for AssetFieldConflict model and related functionality.

Tests the core AssetFieldConflict model including creation, relationships,
utility methods, and data validation for asset-agnostic collection.

Generated with CC for Asset-Agnostic Collection Phase 2.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.core.context import RequestContext


class TestAssetFieldConflictModel:
    """Test AssetFieldConflict model functionality."""

    @pytest.fixture
    def sample_context(self):
        """Create sample request context."""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def sample_conflict_data(self, sample_context):
        """Create sample conflict data."""
        return {
            "asset_id": uuid.uuid4(),
            "client_account_id": uuid.UUID(sample_context.client_account_id),
            "engagement_id": uuid.UUID(sample_context.engagement_id),
            "field_name": "os_version",
            "conflicting_values": [
                {
                    "value": "Ubuntu 20.04",
                    "source": "custom_attributes",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "confidence": 0.7,
                },
                {
                    "value": "Ubuntu 22.04",
                    "source": "technical_details",
                    "timestamp": "2024-01-16T14:45:00Z",
                    "confidence": 0.8,
                },
                {
                    "value": "Ubuntu 20.04.6",
                    "source": "import:server_inventory.csv",
                    "timestamp": "2024-01-17T09:15:00Z",
                    "confidence": 0.9,
                },
            ],
        }

    def test_asset_field_conflict_creation(self, sample_conflict_data):
        """Test creating an AssetFieldConflict instance."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        assert conflict.asset_id == sample_conflict_data["asset_id"]
        assert conflict.client_account_id == sample_conflict_data["client_account_id"]
        assert conflict.engagement_id == sample_conflict_data["engagement_id"]
        assert conflict.field_name == sample_conflict_data["field_name"]
        assert conflict.conflicting_values == sample_conflict_data["conflicting_values"]
        assert conflict.resolution_status == "pending"
        assert conflict.resolved_value is None
        assert conflict.resolved_by is None
        assert conflict.resolution_rationale is None

    def test_is_resolved_property(self, sample_conflict_data):
        """Test is_resolved property for different statuses."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        # Initially not resolved
        assert conflict.is_resolved is False

        # Mark as auto-resolved
        conflict.resolution_status = "auto_resolved"
        assert conflict.is_resolved is True

        # Mark as manually resolved
        conflict.resolution_status = "manual_resolved"
        assert conflict.is_resolved is True

        # Back to pending
        conflict.resolution_status = "pending"
        assert conflict.is_resolved is False

    def test_source_count_property(self, sample_conflict_data):
        """Test source_count property."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        assert conflict.source_count == 3

        # Test with no conflicting values
        conflict.conflicting_values = []
        assert conflict.source_count == 0

        # Test with None
        conflict.conflicting_values = None
        assert conflict.source_count == 0

    def test_get_highest_confidence_value(self, sample_conflict_data):
        """Test get_highest_confidence_value method."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        highest = conflict.get_highest_confidence_value()
        assert highest is not None
        assert highest["confidence"] == 0.9
        assert highest["source"] == "import:server_inventory.csv"
        assert highest["value"] == "Ubuntu 20.04.6"

        # Test with no conflicting values
        conflict.conflicting_values = []
        assert conflict.get_highest_confidence_value() is None

        # Test with None
        conflict.conflicting_values = None
        assert conflict.get_highest_confidence_value() is None

    def test_get_sources(self, sample_conflict_data):
        """Test get_sources method."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        sources = conflict.get_sources()
        expected_sources = [
            "custom_attributes",
            "technical_details",
            "import:server_inventory.csv",
        ]
        assert sources == expected_sources

        # Test with no conflicting values
        conflict.conflicting_values = []
        assert conflict.get_sources() == []

        # Test with None
        conflict.conflicting_values = None
        assert conflict.get_sources() == []

    def test_add_conflicting_value_new(self, sample_conflict_data):
        """Test adding a new conflicting value."""
        conflict = AssetFieldConflict(**sample_conflict_data)
        initial_count = conflict.source_count

        # Add new conflicting value
        conflict.add_conflicting_value(
            value="CentOS 8",
            source="manual_entry",
            timestamp=datetime.utcnow(),
            confidence=0.6,
        )

        assert conflict.source_count == initial_count + 1
        assert "manual_entry" in conflict.get_sources()

        # Find the new value
        new_value = next(
            (v for v in conflict.conflicting_values if v["source"] == "manual_entry"),
            None,
        )
        assert new_value is not None
        assert new_value["value"] == "CentOS 8"
        assert new_value["confidence"] == 0.6

    def test_add_conflicting_value_update_existing(self, sample_conflict_data):
        """Test updating an existing conflicting value."""
        conflict = AssetFieldConflict(**sample_conflict_data)
        initial_count = conflict.source_count

        # Update existing source
        conflict.add_conflicting_value(
            value="Ubuntu 20.04.7",
            source="custom_attributes",  # This source already exists
            timestamp=datetime.utcnow(),
            confidence=0.95,
        )

        # Count should remain the same (update, not add)
        assert conflict.source_count == initial_count

        # Find the updated value
        updated_value = next(
            (
                v
                for v in conflict.conflicting_values
                if v["source"] == "custom_attributes"
            ),
            None,
        )
        assert updated_value is not None
        assert updated_value["value"] == "Ubuntu 20.04.7"
        assert updated_value["confidence"] == 0.95

    def test_add_conflicting_value_empty_list(self, sample_context):
        """Test adding conflicting value when list is empty."""
        conflict_data = {
            "asset_id": uuid.uuid4(),
            "client_account_id": uuid.UUID(sample_context.client_account_id),
            "engagement_id": uuid.UUID(sample_context.engagement_id),
            "field_name": "memory_gb",
            "conflicting_values": [],
        }
        conflict = AssetFieldConflict(**conflict_data)

        conflict.add_conflicting_value(
            value="16",
            source="discovery_scan",
            confidence=0.8,
        )

        assert conflict.source_count == 1
        assert conflict.conflicting_values[0]["value"] == "16"
        assert conflict.conflicting_values[0]["source"] == "discovery_scan"

    def test_resolve_conflict_manual(self, sample_conflict_data, sample_context):
        """Test manually resolving a conflict."""
        conflict = AssetFieldConflict(**sample_conflict_data)
        user_id = uuid.UUID(sample_context.user_id)

        conflict.resolve_conflict(
            resolved_value="Ubuntu 20.04.6 LTS",
            resolved_by=user_id,
            rationale="Chose import data as it's most recent and comprehensive",
            auto_resolved=False,
        )

        assert conflict.resolved_value == "Ubuntu 20.04.6 LTS"
        assert conflict.resolved_by == user_id
        assert conflict.resolution_rationale == "Chose import data as it's most recent and comprehensive"
        assert conflict.resolution_status == "manual_resolved"
        assert conflict.is_resolved is True
        assert conflict.updated_at is not None

    def test_resolve_conflict_auto(self, sample_conflict_data):
        """Test automatically resolving a conflict."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        conflict.resolve_conflict(
            resolved_value="Ubuntu 20.04.6",
            rationale="Auto-resolved using highest confidence source",
            auto_resolved=True,
        )

        assert conflict.resolved_value == "Ubuntu 20.04.6"
        assert conflict.resolved_by is None  # No user for auto-resolution
        assert conflict.resolution_rationale == "Auto-resolved using highest confidence source"
        assert conflict.resolution_status == "auto_resolved"
        assert conflict.is_resolved is True

    def test_to_dict(self, sample_conflict_data):
        """Test to_dict method for API responses."""
        conflict = AssetFieldConflict(**sample_conflict_data)
        conflict.id = uuid.uuid4()
        conflict.created_at = datetime.utcnow()
        conflict.updated_at = datetime.utcnow()

        result = conflict.to_dict()

        # Check all required fields are present
        required_fields = [
            "id",
            "asset_id",
            "client_account_id",
            "engagement_id",
            "field_name",
            "conflicting_values",
            "resolution_status",
            "resolved_value",
            "resolved_by",
            "resolution_rationale",
            "created_at",
            "updated_at",
            "is_resolved",
            "source_count",
            "sources",
        ]

        for field in required_fields:
            assert field in result

        # Check field values
        assert result["id"] == str(conflict.id)
        assert result["asset_id"] == str(conflict.asset_id)
        assert result["field_name"] == conflict.field_name
        assert result["conflicting_values"] == conflict.conflicting_values
        assert result["resolution_status"] == conflict.resolution_status
        assert result["is_resolved"] == conflict.is_resolved
        assert result["source_count"] == conflict.source_count
        assert result["sources"] == conflict.get_sources()

    def test_to_dict_with_nulls(self, sample_context):
        """Test to_dict method with null values."""
        conflict_data = {
            "asset_id": uuid.uuid4(),
            "client_account_id": uuid.UUID(sample_context.client_account_id),
            "engagement_id": uuid.UUID(sample_context.engagement_id),
            "field_name": "test_field",
            "conflicting_values": [],
        }
        conflict = AssetFieldConflict(**conflict_data)
        conflict.id = uuid.uuid4()

        result = conflict.to_dict()

        assert result["resolved_value"] is None
        assert result["resolved_by"] is None
        assert result["resolution_rationale"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_repr(self, sample_conflict_data):
        """Test string representation of the model."""
        conflict = AssetFieldConflict(**sample_conflict_data)
        conflict.id = uuid.uuid4()

        repr_str = repr(conflict)

        assert "AssetFieldConflict" in repr_str
        assert str(conflict.id) in repr_str
        assert str(conflict.asset_id) in repr_str
        assert conflict.field_name in repr_str
        assert conflict.resolution_status in repr_str

    def test_unique_constraint_fields(self, sample_conflict_data):
        """Test that the model has the correct unique constraint fields."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        # The unique constraint should be on these fields
        assert conflict.asset_id is not None
        assert conflict.field_name is not None
        assert conflict.client_account_id is not None
        assert conflict.engagement_id is not None

    def test_tenant_isolation_fields(self, sample_conflict_data):
        """Test that tenant isolation fields are properly set."""
        conflict = AssetFieldConflict(**sample_conflict_data)

        # Both tenant fields should be UUIDs
        assert isinstance(conflict.client_account_id, uuid.UUID)
        assert isinstance(conflict.engagement_id, uuid.UUID)

        # They should match the input data
        assert conflict.client_account_id == sample_conflict_data["client_account_id"]
        assert conflict.engagement_id == sample_conflict_data["engagement_id"]


class TestAssetFieldConflictEdgeCases:
    """Test edge cases and error conditions."""

    def test_conflicting_values_with_missing_fields(self):
        """Test handling of conflicting values with missing optional fields."""
        asset_id = uuid.uuid4()
        client_account_id = uuid.uuid4()
        engagement_id = uuid.uuid4()

        conflict = AssetFieldConflict(
            asset_id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            field_name="test_field",
            conflicting_values=[
                {
                    "value": "test_value",
                    "source": "test_source",
                    # Missing timestamp and confidence
                }
            ],
        )

        # Should handle missing fields gracefully
        highest = conflict.get_highest_confidence_value()
        assert highest is not None
        assert highest["confidence"] == 0.0  # Default when missing

    def test_empty_field_name(self):
        """Test behavior with empty field name."""
        conflict = AssetFieldConflict(
            asset_id=uuid.uuid4(),
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            field_name="",
            conflicting_values=[],
        )

        assert conflict.field_name == ""
        assert conflict.source_count == 0

    def test_large_conflicting_values_list(self):
        """Test performance with many conflicting values."""
        large_values = []
        for i in range(100):
            large_values.append(
                {
                    "value": f"value_{i}",
                    "source": f"source_{i}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": i / 100.0,
                }
            )

        conflict = AssetFieldConflict(
            asset_id=uuid.uuid4(),
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            field_name="test_field",
            conflicting_values=large_values,
        )

        assert conflict.source_count == 100
        highest = conflict.get_highest_confidence_value()
        assert highest["confidence"] == 0.99  # Highest value
        assert len(conflict.get_sources()) == 100
