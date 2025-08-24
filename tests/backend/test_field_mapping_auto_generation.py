#!/usr/bin/env python3
"""
Test field mapping auto-generation functionality.
Run with: docker exec migration_backend pytest /app/tests/backend/test_field_mapping_auto_generation.py -v
"""

import pytest
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8081")
# Use environment variable for JWT token to avoid hardcoding credentials
# Default value is a mock token for demo purposes only - never use in production
AUTH_TOKEN = os.getenv(
    "TEST_AUTH_TOKEN",
    "mock.jwt.token.for.testing.only.replace.with.env.var.in.production"
)
CLIENT_ID = "11111111-1111-1111-1111-111111111111"
ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "X-Client-Account-ID": CLIENT_ID,
    "X-Engagement-ID": ENGAGEMENT_ID,
    "Content-Type": "application/json"
}

def check_field_mappings(flow_id):
    """Check field mappings for a specific flow"""
    url = f"{BASE_URL}/api/v1/unified-discovery/flows/{flow_id}/field-mappings"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("field_mappings", [])
    return []

@pytest.mark.integration
def test_field_mapping_auto_generation():
    """Test that field mappings are auto-generated correctly"""
    flow_id = "7c606b3c-3c58-4dac-ba0f-74a1bb2bf79a"
    mappings = check_field_mappings(flow_id)

    assert len(mappings) == 6, f"Expected 6 mappings, got {len(mappings)}"

    mapping_dict = {m["source_field"]: m for m in mappings}
    assert mapping_dict["os"]["target_field"] == "operating_system"
    assert mapping_dict["application"]["target_field"] == "application_name"

    auto_mapped = sum(1 for m in mappings if m.get("confidence_score", 0) >= 0.8)
    assert auto_mapped == len(mappings), f"Not all fields auto-mapped: {auto_mapped}/{len(mappings)}"
