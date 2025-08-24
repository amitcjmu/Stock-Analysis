"""
User Feedback API Integration Tests.

Tests user feedback processing with agentic learning.
"""

import pytest


class TestUserFeedbackAPI:
    """Test user feedback processing with agentic learning."""

    @pytest.mark.asyncio
    async def test_submit_cmdb_feedback(self, api_client, auth_headers):
        """Test submitting user feedback for agentic learning."""
        feedback_data = {
            "filename": "test_feedback.csv",
            "originalAnalysis": {
                "asset_type_detected": "server",
                "confidence_level": 0.7,
                "issues": ["Missing business owner"],
                "missing_fields_relevant": ["Business_Owner", "Environment"],
            },
            "userCorrections": {
                "asset_type_override": "Application",
                "field_mappings": {
                    "RAM_GB": "Memory (GB)",
                    "APP_OWNER": "Business Owner",
                },
                "comments": "This is actually an application, not a server",
            },
            "assetTypeOverride": "Application",
        }

        response = await api_client.post(
            "/api/v1/flows/cmdb-feedback", json=feedback_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify feedback processing response
        assert "status" in data
        assert "learningApplied" in data
        assert "message" in data

        # Agentic learning should be applied
        if data.get("learningApplied"):
            assert "patternsLearned" in data
            assert "accuracyImprovement" in data
