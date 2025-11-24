"""
Unit tests for upload_handler._normalize_records.
"""

import pytest

from app.api.v1.endpoints.data_import.handlers.upload_handler import (
    _normalize_records,
)


class TestNormalizeRecords:
    """Verify upload handler normalization logic."""

    def test_accepts_list_of_dicts(self):
        """List payloads of dict rows should pass through unchanged."""
        payload = [{"name": "a"}, {"name": "b"}]

        result = _normalize_records(payload)

        assert result == payload

    def test_accepts_wrapped_data_key(self):
        """Dict payloads with `data` list should unwrap correctly."""
        payload = {"data": [{"id": 1}, {"id": 2}]}

        result = _normalize_records(payload)

        assert result == payload["data"]

    def test_accepts_single_dict(self):
        """Single JSON object should be wrapped in a list."""
        payload = {"name": "solo"}

        result = _normalize_records(payload)

        assert result == [payload]

    def test_rejects_non_dict_entries(self):
        """Lists containing non-dict entries must raise ValueError."""
        payload = [{"name": "ok"}, "bad-row"]

        with pytest.raises(ValueError) as excinfo:
            _normalize_records(payload)

        assert "each entry must be a JSON object" in str(excinfo.value)

    def test_rejects_invalid_payload_types(self):
        """Payloads that are not dict/list must raise ValueError."""
        payload = "invalid"

        with pytest.raises(ValueError) as excinfo:
            _normalize_records(payload)

        assert "Payload must be a JSON object or a list" in str(excinfo.value)
