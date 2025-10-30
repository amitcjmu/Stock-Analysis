"""
Unit tests for uuid_utils.ensure_uuid function.

Tests INTEGER to UUID conversion for Assessment Flow endpoints (Issue #867).
"""

import pytest
from uuid import UUID
from app.api.v1.master_flows.assessment.uuid_utils import ensure_uuid


class TestEnsureUuid:
    """Test ensure_uuid function with various input types."""

    def test_uuid_object_passthrough(self):
        """UUID objects should pass through unchanged."""
        input_uuid = UUID("11111111-1111-1111-1111-111111111111")
        result = ensure_uuid(input_uuid)
        assert result == input_uuid
        assert isinstance(result, UUID)

    def test_valid_uuid_string(self):
        """Valid UUID strings should convert to UUID objects."""
        result = ensure_uuid("11111111-1111-1111-1111-111111111111")
        assert result == UUID("11111111-1111-1111-1111-111111111111")
        assert isinstance(result, UUID)

    def test_demo_client_integer(self):
        """Integer 1 should map to demo client UUID."""
        result = ensure_uuid(1)
        assert result == UUID("11111111-1111-1111-1111-111111111111")
        assert isinstance(result, UUID)

    def test_demo_client_string(self):
        """String "1" should map to demo client UUID (main bug fix)."""
        result = ensure_uuid("1")
        assert result == UUID("11111111-1111-1111-1111-111111111111")
        assert isinstance(result, UUID)

    def test_demo_engagement_integer(self):
        """Integer 2 should map to demo engagement UUID."""
        result = ensure_uuid(2)
        assert result == UUID("22222222-2222-2222-2222-222222222222")
        assert isinstance(result, UUID)

    def test_demo_engagement_string(self):
        """String "2" should map to demo engagement UUID."""
        result = ensure_uuid("2")
        assert result == UUID("22222222-2222-2222-2222-222222222222")
        assert isinstance(result, UUID)

    def test_unknown_integer_zero_padding(self):
        """Unknown integers should convert to zero-padded UUIDs."""
        result = ensure_uuid(999)
        # 999 in hex = 0x3e7, zero-padded to 32 chars
        expected = UUID("00000000-0000-0000-0000-0000000003e7")
        assert result == expected
        assert isinstance(result, UUID)

    def test_unknown_integer_string_zero_padding(self):
        """Unknown integer strings should convert to zero-padded UUIDs."""
        result = ensure_uuid("999")
        expected = UUID("00000000-0000-0000-0000-0000000003e7")
        assert result == expected
        assert isinstance(result, UUID)

    def test_none_value(self):
        """None should return None."""
        result = ensure_uuid(None)
        assert result is None

    def test_invalid_string_raises_error(self):
        """Invalid strings should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot convert string"):
            ensure_uuid("not-a-uuid-or-number")

    def test_invalid_uuid_format_raises_error(self):
        """Invalid UUID format should raise ValueError."""
        with pytest.raises(ValueError):
            ensure_uuid("11111111-1111-1111-1111")  # Too short

    def test_zero_integer(self):
        """Zero should convert to all-zeros UUID."""
        result = ensure_uuid(0)
        expected = UUID("00000000-0000-0000-0000-000000000000")
        assert result == expected
        assert isinstance(result, UUID)

    def test_zero_string(self):
        """String "0" should convert to all-zeros UUID."""
        result = ensure_uuid("0")
        expected = UUID("00000000-0000-0000-0000-000000000000")
        assert result == expected
        assert isinstance(result, UUID)

    def test_large_integer(self):
        """Large integers should convert correctly."""
        result = ensure_uuid(123456789)
        # 123456789 in hex = 0x75bcd15, zero-padded to 32 chars
        expected = UUID("00000000-0000-0000-0000-0000075bcd15")
        assert result == expected
        assert isinstance(result, UUID)


class TestEnsureUuidRealWorldScenarios:
    """Test real-world scenarios from Assessment Flow."""

    def test_frontend_sends_string_one_as_client_account_id(self):
        """
        Reproduces Issue #867: Frontend sends client_account_id="1" (string).

        This is the main bug - ensure_uuid("1") was failing with:
        ValueError: badly formed hexadecimal UUID string
        """
        # Simulates: context.client_account_id = "1" from HTTP header
        client_account_id = "1"
        result = ensure_uuid(client_account_id)

        # Should convert to demo client UUID
        assert result == UUID("11111111-1111-1111-1111-111111111111")
        assert isinstance(result, UUID)

    def test_backend_expects_uuid_for_database_queries(self):
        """
        After conversion, UUID should work in SQLAlchemy queries.
        """
        client_account_id = "1"
        uuid_value = ensure_uuid(client_account_id)

        # Should be usable in WHERE clauses like:
        # Asset.client_account_id == ensure_uuid(context.client_account_id)
        assert isinstance(uuid_value, UUID)
        assert str(uuid_value) == "11111111-1111-1111-1111-111111111111"

    def test_handles_both_legacy_integer_and_new_uuid_clients(self):
        """
        System should handle both legacy (INTEGER) and new (UUID) client IDs.
        """
        # Legacy client (INTEGER sent as string from headers)
        legacy_result = ensure_uuid("1")
        assert legacy_result == UUID("11111111-1111-1111-1111-111111111111")

        # New client (UUID sent as string from headers)
        new_client_uuid_str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        new_result = ensure_uuid(new_client_uuid_str)
        assert new_result == UUID(new_client_uuid_str)

        # Both should be UUID objects
        assert isinstance(legacy_result, UUID)
        assert isinstance(new_result, UUID)
