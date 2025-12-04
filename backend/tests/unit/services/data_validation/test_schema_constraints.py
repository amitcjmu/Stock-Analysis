"""Unit tests for schema constraints utility.

Tests the schema constraint extraction from SQLAlchemy models.

Related: ADR-038, Issue #1204, Issue #1205
"""

import pytest
from unittest.mock import patch

from app.utils.schema_constraints import (
    get_asset_schema_constraints,
    get_column_max_length,
    get_all_varchar_columns,
    is_column_nullable,
    SMALL_STRING_LENGTH,
    MEDIUM_STRING_LENGTH,
    LARGE_STRING_LENGTH,
    KNOWN_VARCHAR_FIELDS,
)


class TestSchemaConstantsDefinitions:
    """Test suite for schema constraint constants."""

    def test_string_length_constants(self):
        """Test that string length constants are defined correctly."""
        assert SMALL_STRING_LENGTH == 50
        assert MEDIUM_STRING_LENGTH == 100
        assert LARGE_STRING_LENGTH == 255

    def test_known_varchar_fields_defined(self):
        """Test that KNOWN_VARCHAR_FIELDS contains expected fields."""
        assert "application_name" in KNOWN_VARCHAR_FIELDS
        assert "hostname" in KNOWN_VARCHAR_FIELDS
        assert "name" in KNOWN_VARCHAR_FIELDS
        assert "asset_name" in KNOWN_VARCHAR_FIELDS

        # Check expected lengths
        assert KNOWN_VARCHAR_FIELDS["application_name"] == LARGE_STRING_LENGTH
        assert KNOWN_VARCHAR_FIELDS["asset_type"] == SMALL_STRING_LENGTH


class TestGetAssetSchemaConstraints:
    """Test suite for get_asset_schema_constraints function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        # This test may require mocking if Asset model is not available
        # For now, just verify it doesn't crash
        try:
            result = get_asset_schema_constraints()
            assert isinstance(result, dict)
        except ImportError:
            # Asset model not available in test context
            pytest.skip("Asset model not available")

    def test_caching_behavior(self):
        """Test that results are cached via lru_cache."""
        # Clear the cache first
        get_asset_schema_constraints.cache_clear()

        try:
            result1 = get_asset_schema_constraints()
            result2 = get_asset_schema_constraints()

            # Should return the same cached object
            assert result1 is result2

            # Check cache info
            cache_info = get_asset_schema_constraints.cache_info()
            assert cache_info.hits >= 1
        except ImportError:
            pytest.skip("Asset model not available")


class TestGetColumnMaxLength:
    """Test suite for get_column_max_length function."""

    def test_returns_none_for_unknown_column(self):
        """Test that None is returned for unknown columns."""
        result = get_column_max_length("nonexistent_column_xyz")
        assert result is None

    def test_returns_int_for_varchar_column(self):
        """Test that an integer is returned for VARCHAR columns."""
        # Mock the get_asset_schema_constraints function
        mock_constraints = {"test_column": {"max_length": 255, "nullable": True}}
        with patch(
            "app.utils.schema_constraints.get_asset_schema_constraints",
            return_value=mock_constraints,
        ):
            result = get_column_max_length("test_column")
            assert result == 255


class TestGetAllVarcharColumns:
    """Test suite for get_all_varchar_columns function."""

    def test_returns_dict_with_max_lengths(self):
        """Test that function returns dict of column_name -> max_length."""
        mock_constraints = {
            "name": {"max_length": 255, "nullable": True},
            "status": {"max_length": 50, "nullable": False},
            "description": {"nullable": True},  # No max_length (TEXT column)
        }
        with patch(
            "app.utils.schema_constraints.get_asset_schema_constraints",
            return_value=mock_constraints,
        ):
            result = get_all_varchar_columns()

            assert "name" in result
            assert result["name"] == 255
            assert "status" in result
            assert result["status"] == 50
            # description should NOT be included (no max_length)
            assert "description" not in result


class TestIsColumnNullable:
    """Test suite for is_column_nullable function."""

    def test_returns_true_for_nullable_column(self):
        """Test that True is returned for nullable columns."""
        mock_constraints = {"test_column": {"nullable": True}}
        with patch(
            "app.utils.schema_constraints.get_asset_schema_constraints",
            return_value=mock_constraints,
        ):
            result = is_column_nullable("test_column")
            assert result is True

    def test_returns_false_for_not_null_column(self):
        """Test that False is returned for NOT NULL columns."""
        mock_constraints = {"test_column": {"nullable": False}}
        with patch(
            "app.utils.schema_constraints.get_asset_schema_constraints",
            return_value=mock_constraints,
        ):
            result = is_column_nullable("test_column")
            assert result is False

    def test_returns_true_for_unknown_column(self):
        """Test that True (default) is returned for unknown columns."""
        mock_constraints = {}
        with patch(
            "app.utils.schema_constraints.get_asset_schema_constraints",
            return_value=mock_constraints,
        ):
            result = is_column_nullable("unknown_column")
            assert result is True  # Default to nullable if unknown


class TestSchemaConstraintsIntegration:
    """Integration tests for schema constraints (requires database models)."""

    @pytest.mark.skipif(
        True,  # Skip by default, enable when running with full DB setup
        reason="Requires database models to be available",
    )
    def test_actual_asset_model_constraints(self):
        """Test extraction of actual Asset model constraints."""
        # Clear cache to ensure fresh extraction
        get_asset_schema_constraints.cache_clear()

        constraints = get_asset_schema_constraints()

        # Verify some expected fields exist
        assert len(constraints) > 0

        # application_name should have max_length
        if "application_name" in constraints:
            assert "max_length" in constraints["application_name"]

        # id field should not have max_length (UUID type)
        if "id" in constraints:
            assert (
                "max_length" not in constraints["id"]
                or constraints["id"]["max_length"] is None
            )
