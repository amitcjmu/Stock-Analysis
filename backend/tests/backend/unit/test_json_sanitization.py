"""Unit tests for JSON sanitization utility.

Tests the shared json_sanitization module used across all LLM-powered endpoints
to prevent JSON serialization errors from NaN and Infinity values.

See ADR-029 for architectural decision and usage guidelines.
"""

from datetime import date, datetime, timezone

from app.utils.json_sanitization import sanitize_for_json


class TestSanitizeForJson:
    """Test suite for sanitize_for_json utility function."""

    def test_sanitize_nan_value(self):
        """Test that NaN values are converted to None."""
        data = {"score": float("nan"), "count": 42}
        result = sanitize_for_json(data)
        assert result == {"score": None, "count": 42}

    def test_sanitize_infinity_value(self):
        """Test that Infinity values are converted to None."""
        data = {"pos_inf": float("inf"), "neg_inf": float("-inf"), "normal": 3.14}
        result = sanitize_for_json(data)
        assert result == {"pos_inf": None, "neg_inf": None, "normal": 3.14}

    def test_sanitize_nested_dict(self):
        """Test that nested dictionaries are recursively sanitized."""
        data = {
            "level1": {
                "score": float("nan"),
                "level2": {"confidence": float("inf"), "valid": 0.95},
            }
        }
        result = sanitize_for_json(data)
        assert result == {
            "level1": {"score": None, "level2": {"confidence": None, "valid": 0.95}}
        }

    def test_sanitize_list_of_dicts(self):
        """Test that lists containing dictionaries are sanitized."""
        data = [
            {"question": "Q1", "score": float("nan")},
            {"question": "Q2", "score": 0.85},
            {"question": "Q3", "confidence": float("inf")},
        ]
        result = sanitize_for_json(data)
        assert result == [
            {"question": "Q1", "score": None},
            {"question": "Q2", "score": 0.85},
            {"question": "Q3", "confidence": None},
        ]

    def test_sanitize_datetime_objects(self):
        """Test that datetime objects are converted to ISO format strings."""
        dt = datetime(2025, 10, 22, 15, 30, 0, tzinfo=timezone.utc)
        data = {"created_at": dt, "name": "Test"}
        result = sanitize_for_json(data)
        assert result["name"] == "Test"
        assert isinstance(result["created_at"], str)
        assert "2025-10-22" in result["created_at"]

    def test_sanitize_date_objects(self):
        """Test that date objects are converted to ISO format strings."""
        d = date(2025, 10, 22)
        data = {"date": d, "name": "Test"}
        result = sanitize_for_json(data)
        assert result["name"] == "Test"
        assert isinstance(result["date"], str)
        assert result["date"] == "2025-10-22"

    def test_sanitize_preserves_valid_primitives(self):
        """Test that valid primitive types are preserved."""
        data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean_true": True,
            "boolean_false": False,
            "null": None,
        }
        result = sanitize_for_json(data)
        assert result == data

    def test_sanitize_non_serializable_object(self):
        """Test that non-serializable objects are converted to strings."""

        class CustomObject:
            def __str__(self):
                return "CustomObject()"

        data = {"obj": CustomObject(), "name": "Test"}
        result = sanitize_for_json(data)
        assert result["name"] == "Test"
        assert result["obj"] == "CustomObject()"

    def test_sanitize_empty_structures(self):
        """Test that empty structures are handled correctly."""
        assert sanitize_for_json({}) == {}
        assert sanitize_for_json([]) == []
        assert sanitize_for_json(None) is None

    def test_sanitize_questionnaire_like_structure(self):
        """Test sanitization of a structure similar to questionnaire questions.

        This is a key use case from Issue #682 where LLM-generated questionnaires
        contained NaN and Infinity values that caused JSON serialization failures.
        """
        questions = [
            {
                "id": "q1",
                "text": "What is your application name?",
                "type": "text",
                "confidence": 0.95,
                "target_gaps": ["application_name"],
            },
            {
                "id": "q2",
                "text": "What is the business criticality?",
                "type": "select",
                "confidence": float("nan"),  # AI model returned NaN
                "options": ["high", "medium", "low"],
                "target_gaps": ["business_criticality"],
            },
            {
                "id": "q3",
                "text": "What is the data volume?",
                "type": "number",
                "confidence": float("inf"),  # AI model returned Infinity
                "target_gaps": ["data_volume"],
            },
        ]
        result = sanitize_for_json(questions)

        # Verify structure is preserved
        assert len(result) == 3
        assert result[0]["id"] == "q1"
        assert result[0]["confidence"] == 0.95

        # Verify NaN and Infinity are sanitized
        assert result[1]["confidence"] is None
        assert result[2]["confidence"] is None

        # Verify other fields are preserved
        assert result[1]["options"] == ["high", "medium", "low"]
        assert result[2]["type"] == "number"


class TestSanitizeForJsonEdgeCases:
    """Test edge cases and error conditions."""

    def test_deeply_nested_structure(self):
        """Test sanitization of deeply nested structures."""
        data = {
            "l1": {"l2": {"l3": {"l4": {"l5": {"score": float("nan"), "valid": True}}}}}
        }
        result = sanitize_for_json(data)
        assert result["l1"]["l2"]["l3"]["l4"]["l5"]["score"] is None
        assert result["l1"]["l2"]["l3"]["l4"]["l5"]["valid"] is True

    def test_mixed_list_types(self):
        """Test lists containing mixed types."""
        data = [
            "string",
            42,
            3.14,
            float("nan"),
            True,
            None,
            {"key": float("inf")},
        ]
        result = sanitize_for_json(data)
        assert result == ["string", 42, 3.14, None, True, None, {"key": None}]

    def test_unicode_strings(self):
        """Test that Unicode strings are preserved."""
        data = {"text": "Hello 世界 🌍", "emoji": "✅ 🚀"}
        result = sanitize_for_json(data)
        assert result == data

    def test_zero_and_negative_numbers(self):
        """Test that zero and negative numbers are preserved."""
        data = {
            "zero": 0,
            "negative": -42,
            "negative_float": -3.14,
            "zero_float": 0.0,
        }
        result = sanitize_for_json(data)
        assert result == data

    def test_large_arrays(self):
        """Test performance with large arrays."""
        # Create a large array with some problematic values
        data = [
            {"id": i, "score": float("nan") if i % 100 == 0 else i * 0.1}
            for i in range(1000)
        ]
        result = sanitize_for_json(data)

        # Verify array length is preserved
        assert len(result) == 1000

        # Verify NaN values are sanitized
        assert result[0]["score"] is None  # i=0, should be NaN
        assert result[100]["score"] is None  # i=100, should be NaN

        # Verify normal values are preserved
        assert result[1]["score"] == 0.1
        assert result[99]["score"] == 9.9


class TestSanitizeForJsonLLMUseCases:
    """Test real-world LLM use cases from the codebase."""

    def test_gap_analysis_confidence_scores(self):
        """Test sanitization of gap analysis with confidence scores.

        Gap analysis endpoints return AI-generated confidence scores that
        may contain NaN values when the AI model is uncertain.
        """
        gap_analysis = {
            "gaps": [
                {
                    "attribute": "business_criticality",
                    "confidence": 0.95,
                    "impact": "high",
                },
                {
                    "attribute": "data_volume",
                    "confidence": float("nan"),  # AI uncertain
                    "impact": "medium",
                },
                {
                    "attribute": "compliance_requirements",
                    "confidence": float("inf"),  # AI error
                    "impact": "high",
                },
            ],
            "overall_confidence": 0.85,
        }
        result = sanitize_for_json(gap_analysis)

        # Verify valid confidence scores preserved
        assert result["gaps"][0]["confidence"] == 0.95
        assert result["overall_confidence"] == 0.85

        # Verify problematic scores sanitized
        assert result["gaps"][1]["confidence"] is None
        assert result["gaps"][2]["confidence"] is None

        # Verify other fields preserved
        assert result["gaps"][0]["impact"] == "high"
        assert result["gaps"][1]["attribute"] == "data_volume"

    def test_assessment_recommendations_risk_scores(self):
        """Test sanitization of assessment recommendations with risk scores.

        Assessment endpoints return AI-generated risk and complexity scores.
        """
        recommendations = {
            "strategy": "rehost",
            "risk_score": 0.35,
            "complexity_score": float("nan"),  # AI couldn't determine
            "business_impact_score": 0.75,
            "estimated_effort": float("inf"),  # AI overflow
        }
        result = sanitize_for_json(recommendations)

        assert result["risk_score"] == 0.35
        assert result["complexity_score"] is None
        assert result["business_impact_score"] == 0.75
        assert result["estimated_effort"] is None

    def test_agent_insights_analysis(self):
        """Test sanitization of agent-generated insights and analysis."""
        insights = {
            "timestamp": datetime(2025, 10, 22, 15, 30, tzinfo=timezone.utc),
            "agent": "discovery_agent",
            "analysis": {
                "patterns_identified": 5,
                "confidence_level": float("nan"),
                "recommendations": [
                    {"priority": 1, "confidence": 0.9},
                    {"priority": 2, "confidence": float("inf")},
                ],
            },
        }
        result = sanitize_for_json(insights)

        # Verify datetime converted
        assert isinstance(result["timestamp"], str)
        assert "2025-10-22" in result["timestamp"]

        # Verify nested confidence scores sanitized
        assert result["analysis"]["confidence_level"] is None
        assert result["analysis"]["recommendations"][0]["confidence"] == 0.9
        assert result["analysis"]["recommendations"][1]["confidence"] is None

        # Verify structure preserved
        assert result["analysis"]["patterns_identified"] == 5
        assert result["agent"] == "discovery_agent"


class TestSanitizeForJsonPerformance:
    """Test performance characteristics of sanitization."""

    def test_performance_with_large_nested_structure(self):
        """Test that sanitization performs reasonably with large structures."""
        # Create a moderately large nested structure similar to real API responses
        data = {
            "flow_id": "test-123",
            "metadata": {"created": datetime.now(timezone.utc)},
            "results": [
                {
                    "id": i,
                    "score": float("nan") if i % 50 == 0 else i * 0.1,
                    "details": {
                        "confidence": float("inf") if i % 75 == 0 else 0.8,
                        "tags": [f"tag{j}" for j in range(5)],
                    },
                }
                for i in range(500)
            ],
        }

        # This should complete quickly (< 1 second)
        result = sanitize_for_json(data)

        # Verify sanitization worked
        assert result["flow_id"] == "test-123"
        assert isinstance(result["metadata"]["created"], str)
        assert len(result["results"]) == 500

        # Spot check some sanitized values
        assert result["results"][0]["score"] is None  # i=0, NaN
        assert result["results"][50]["score"] is None  # i=50, NaN
        assert result["results"][1]["score"] == 0.1

        assert (
            result["results"][0]["details"]["confidence"] is None
        )  # i=0, Infinity (0 % 75 == 0)
        assert result["results"][75]["details"]["confidence"] is None  # Infinity
        assert result["results"][1]["details"]["confidence"] == 0.8  # Normal value

    def test_no_modification_of_clean_data(self):
        """Test that clean data passes through unchanged."""
        clean_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "nested": {"list": [1, 2, 3]},
        }
        result = sanitize_for_json(clean_data)
        assert result == clean_data
