"""Unit tests for data profiler and validation checks.

Tests the intelligent data profiling system implemented per ADR-038:
- Multi-value detection (comma/semicolon/pipe-separated)
- Full dataset analysis
- Field length validation against schema constraints
- Data profile report generation

Related: ADR-038, Issue #1204, Issue #1213
"""

from app.services.crewai_flows.handlers.phase_executors.data_import_validation.data_profiler import (
    DataProfiler,
)
from app.services.crewai_flows.handlers.phase_executors.data_import_validation.data_profiler_models import (
    FieldStatistics,
    LengthViolation,
    MultiValueResult,
    MULTI_VALUE_PATTERNS,
)


class TestFieldStatistics:
    """Test suite for FieldStatistics class."""

    def test_add_value_tracks_length(self):
        """Test that adding values tracks their lengths."""
        stats = FieldStatistics()
        stats.add_value("hello")
        stats.add_value("world")
        stats.add_value("!")

        assert len(stats.lengths) == 3
        assert stats.lengths == [5, 5, 1]

    def test_add_null_value_increments_count(self):
        """Test that null and empty values increment null_count."""
        stats = FieldStatistics()
        stats.add_value(None)
        stats.add_value("")
        stats.add_value("valid")

        assert stats.null_count == 2
        assert stats.total_records == 3

    def test_unique_values_tracked(self):
        """Test that unique values are tracked."""
        stats = FieldStatistics()
        stats.add_value("a")
        stats.add_value("b")
        stats.add_value("a")  # Duplicate
        stats.add_value("c")

        assert len(stats.unique_values) == 3
        assert "a" in stats.unique_values
        assert "b" in stats.unique_values
        assert "c" in stats.unique_values

    def test_unique_values_capped(self):
        """Test that unique values are capped at MAX_UNIQUE_VALUES."""
        stats = FieldStatistics()
        for i in range(1500):  # More than MAX_UNIQUE_VALUES (1000)
            stats.add_value(f"value_{i}")

        assert len(stats.unique_values) == stats.MAX_UNIQUE_VALUES

    def test_summary_calculation(self):
        """Test summary statistics calculation."""
        stats = FieldStatistics()
        stats.add_value("short")  # 5
        stats.add_value("medium_length")  # 13
        stats.add_value("very_long_string")  # 16
        stats.add_value(None)  # null

        summary = stats.summary()

        assert summary["min_length"] == 5
        assert summary["max_length"] == 16
        assert summary["null_count"] == 1
        assert summary["null_percentage"] == 25.0  # 1/4
        assert summary["total_records"] == 4
        assert summary["non_null_records"] == 3


class TestMultiValuePatterns:
    """Test suite for multi-value detection patterns."""

    def test_comma_pattern_detects_three_or_more(self):
        """Test that comma pattern requires 3+ values."""
        pattern = MULTI_VALUE_PATTERNS["comma"]

        # Should match (3+ values)
        assert pattern.match("a, b, c") is not None
        assert pattern.match("value1,value2,value3") is not None
        assert pattern.match("one, two, three, four") is not None

        # Should NOT match (fewer than 3)
        assert pattern.match("a, b") is None
        assert pattern.match("single") is None

    def test_semicolon_pattern_detects_three_or_more(self):
        """Test that semicolon pattern requires 3+ values."""
        pattern = MULTI_VALUE_PATTERNS["semicolon"]

        # Should match
        assert pattern.match("a; b; c") is not None
        assert pattern.match("value1;value2;value3") is not None

        # Should NOT match
        assert pattern.match("a; b") is None

    def test_pipe_pattern_detects_three_or_more(self):
        """Test that pipe pattern requires 3+ values."""
        pattern = MULTI_VALUE_PATTERNS["pipe"]

        # Should match
        assert pattern.match("a | b | c") is not None
        assert pattern.match("value1|value2|value3") is not None

        # Should NOT match
        assert pattern.match("a | b") is None


class TestDataProfilerMultiValueDetection:
    """Test suite for DataProfiler multi-value detection."""

    def test_detect_comma_separated_values(self):
        """Test detection of comma-separated values."""
        data = [
            {"apps": "App1, App2, App3"},
            {"apps": "SingleApp"},
            {"apps": "App4, App5, App6, App7"},
        ]
        profiler = DataProfiler(data)
        results = profiler.detect_multi_values("apps")

        assert len(results) == 1
        result = results[0]
        assert result.is_multi_valued is True
        assert result.affected_count == 2
        assert result.delimiter == "comma"

    def test_detect_semicolon_separated_values(self):
        """Test detection of semicolon-separated values."""
        data = [
            {"servers": "srv1; srv2; srv3"},
            {"servers": "srv4; srv5; srv6"},
        ]
        profiler = DataProfiler(data)
        results = profiler.detect_multi_values("servers")

        assert len(results) == 1
        result = results[0]
        assert result.is_multi_valued is True
        assert result.delimiter == "semicolon"

    def test_detect_pipe_separated_values(self):
        """Test detection of pipe-separated values."""
        data = [
            {"deps": "lib1 | lib2 | lib3"},
        ]
        profiler = DataProfiler(data)
        results = profiler.detect_multi_values("deps")

        assert len(results) == 1
        result = results[0]
        assert result.is_multi_valued is True
        assert result.delimiter == "pipe"

    def test_no_multi_value_detection_for_clean_data(self):
        """Test that clean data doesn't trigger false positives."""
        data = [
            {"name": "Simple Application"},
            {"name": "Another App"},
            {"name": "Third App"},
        ]
        profiler = DataProfiler(data)
        results = profiler.detect_multi_values("name")

        assert len(results) == 0

    def test_multi_value_samples_are_limited(self):
        """Test that samples are limited to prevent response bloat."""
        # Create many records with multi-values
        data = [{"apps": f"App{i}, App{i+1}, App{i+2}"} for i in range(50)]
        profiler = DataProfiler(data)
        results = profiler.detect_multi_values("apps")

        assert len(results) == 1
        # Samples should be limited to 5
        assert len(results[0].samples) <= 5


class TestDataProfilerFullDatasetAnalysis:
    """Test suite for DataProfiler full dataset analysis."""

    def test_analyze_full_dataset_basic(self):
        """Test basic full dataset analysis."""
        data = [
            {"name": "App1", "status": "active"},
            {"name": "App2", "status": "inactive"},
            {"name": "Application Three", "status": "active"},
        ]
        profiler = DataProfiler(data)
        result = profiler.analyze_full_dataset()

        assert "name" in result
        assert "status" in result
        assert result["name"]["total_records"] == 3
        assert result["name"]["min_length"] == 4  # "App1"
        assert result["name"]["max_length"] == 17  # "Application Three"

    def test_analyze_handles_null_values(self):
        """Test that analysis correctly handles null values."""
        data = [
            {"field": "value1"},
            {"field": None},
            {"field": ""},
            {"field": "value2"},
        ]
        profiler = DataProfiler(data)
        result = profiler.analyze_full_dataset()

        assert result["field"]["null_count"] == 2  # None and ""
        assert result["field"]["null_percentage"] == 50.0

    def test_analyze_empty_dataset(self):
        """Test analysis of empty dataset."""
        profiler = DataProfiler([])
        result = profiler.analyze_full_dataset()

        assert result == {}


class TestDataProfilerLengthValidation:
    """Test suite for field length validation."""

    def test_detect_length_violation(self):
        """Test detection of field values exceeding schema limits."""
        data = [
            {"name": "Short"},  # 5 chars
            {"name": "A" * 300},  # 300 chars - exceeds 255 limit
            {"name": "Normal"},  # 6 chars
        ]
        schema = {"name": {"max_length": 255}}

        profiler = DataProfiler(data)
        violations = profiler.check_field_length_violations(schema)

        assert len(violations) == 1
        v = violations[0]
        assert v.field_name == "name"
        assert v.schema_limit == 255
        assert v.max_found == 300
        assert v.exceeds_by == 45
        assert v.affected_count >= 1

    def test_no_violation_when_within_limits(self):
        """Test that no violations are reported when data is within limits."""
        data = [
            {"name": "Short"},
            {"name": "Medium Length Name"},
            {"name": "Longer Application Name Here"},
        ]
        schema = {"name": {"max_length": 255}}

        profiler = DataProfiler(data)
        violations = profiler.check_field_length_violations(schema)

        assert len(violations) == 0

    def test_violation_samples_provided(self):
        """Test that violation samples are provided."""
        data = [
            {"app_name": "A" * 300},
            {"app_name": "B" * 400},
        ]
        schema = {"app_name": {"max_length": 255}}

        profiler = DataProfiler(data)
        violations = profiler.check_field_length_violations(schema)

        assert len(violations) == 1
        assert len(violations[0].samples) >= 1
        assert violations[0].samples[0]["value_length"] > 255


class TestDataProfileReport:
    """Test suite for DataProfileReport generation."""

    def test_generate_profile_report_basic(self):
        """Test basic profile report generation."""
        data = [
            {"name": "App1", "status": "active"},
            {"name": "App2", "status": "pending"},
            {"name": "Application Three", "status": "active"},
        ]
        profiler = DataProfiler(data)
        report = profiler.generate_profile_report()

        assert report.total_records == 3
        assert report.total_fields == 2
        assert "name" in report.field_profiles
        assert "status" in report.field_profiles
        assert report.overall_quality_score > 0

    def test_report_identifies_critical_issues(self):
        """Test that report identifies critical issues (length violations)."""
        data = [
            {"app_name": "A" * 300},  # Exceeds limit
        ]
        schema = {"app_name": {"max_length": 255}}

        profiler = DataProfiler(data)
        report = profiler.generate_profile_report(schema)

        assert len(report.critical_issues) > 0
        assert report.blocking_issue_count > 0
        assert report.requires_user_decision is True

    def test_report_identifies_warnings(self):
        """Test that report identifies warnings (multi-value fields)."""
        data = [
            {"apps": "App1, App2, App3"},
            {"apps": "App4, App5, App6"},
        ]

        profiler = DataProfiler(data)
        report = profiler.generate_profile_report()

        assert len(report.warnings) > 0

    def test_report_identifies_info(self):
        """Test that report identifies info items (high null percentage)."""
        data = [
            {"name": "App1", "optional": None},
            {"name": "App2", "optional": None},
            {"name": "App3", "optional": None},
            {"name": "App4", "optional": "value"},
        ]

        profiler = DataProfiler(data)
        report = profiler.generate_profile_report()

        # optional field has 75% null - should be reported as info
        info_fields = [i["field"] for i in report.info]
        assert "optional" in info_fields

    def test_report_to_dict_conversion(self):
        """Test that report converts to dict correctly."""
        data = [{"name": "App1"}, {"name": "App2"}]

        profiler = DataProfiler(data)
        report = profiler.generate_profile_report()
        report_dict = report.to_dict()

        assert "generated_at" in report_dict
        assert "summary" in report_dict
        assert "issues" in report_dict
        assert "field_profiles" in report_dict
        assert "user_action_required" in report_dict
        assert "blocking_issues" in report_dict


class TestDataProfilerQualityScores:
    """Test suite for quality score calculations."""

    def test_completeness_score_all_filled(self):
        """Test completeness score when all fields are filled."""
        data = [
            {"name": "App1", "status": "active"},
            {"name": "App2", "status": "inactive"},
        ]

        profiler = DataProfiler(data)
        profiler.analyze_full_dataset()
        score = profiler._calculate_completeness_score()

        assert score == 100.0

    def test_completeness_score_with_nulls(self):
        """Test completeness score with null values."""
        data = [
            {"name": "App1", "status": None},
            {"name": None, "status": "active"},
        ]

        profiler = DataProfiler(data)
        profiler.analyze_full_dataset()
        score = profiler._calculate_completeness_score()

        # 2 non-null out of 4 total = 50%
        assert score == 50.0

    def test_constraint_compliance_score_no_violations(self):
        """Test compliance score with no violations."""
        data = [
            {"name": "Short"},
            {"name": "Medium"},
        ]

        profiler = DataProfiler(data)
        profiler.analyze_full_dataset()
        profiler._length_violations = []
        score = profiler._calculate_constraint_compliance_score()

        assert score == 100.0


class TestDataProfilerEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_raw_data(self):
        """Test handling of empty raw data."""
        profiler = DataProfiler([])

        assert profiler.analyze_full_dataset() == {}
        assert profiler.detect_multi_values() == []
        assert profiler.check_field_length_violations({}) == []

    def test_non_dict_records_are_skipped(self):
        """Test that non-dict records are gracefully skipped."""
        data = [
            {"name": "Valid"},
            "invalid_string_record",
            ["invalid", "list", "record"],
            {"name": "Also Valid"},
        ]

        profiler = DataProfiler(data)
        result = profiler.analyze_full_dataset()

        # Should only process the 2 valid dict records
        assert result["name"]["total_records"] == 2

    def test_unicode_values(self):
        """Test handling of Unicode values."""
        data = [
            {"name": "应用程序"},  # Chinese
            {"name": "アプリケーション"},  # Japanese
            {"name": "приложение"},  # Russian
        ]

        profiler = DataProfiler(data)
        result = profiler.analyze_full_dataset()

        assert result["name"]["total_records"] == 3

    def test_mixed_type_values(self):
        """Test handling of mixed type values in same field."""
        data = [
            {"value": "string"},
            {"value": 123},
            {"value": 45.67},
            {"value": True},
        ]

        profiler = DataProfiler(data)
        result = profiler.analyze_full_dataset()

        # All values should be converted to strings and tracked
        assert result["value"]["total_records"] == 4


class TestMultiValueResult:
    """Test suite for MultiValueResult dataclass."""

    def test_to_dict_conversion(self):
        """Test MultiValueResult to dict conversion."""
        result = MultiValueResult(
            field_name="apps",
            is_multi_valued=True,
            affected_count=5,
            delimiter="comma",
            samples=[
                {
                    "record_index": 0,
                    "value": "a,b,c",
                    "delimiter": "comma",
                    "item_count": 3,
                }
            ],
            recommendation="Consider splitting",
        )
        d = result.to_dict()

        assert d["field"] == "apps"
        assert d["is_multi_valued"] is True
        assert d["affected_count"] == 5
        assert d["delimiter"] == "comma"


class TestLengthViolation:
    """Test suite for LengthViolation dataclass."""

    def test_to_dict_conversion(self):
        """Test LengthViolation to dict conversion."""
        violation = LengthViolation(
            field_name="app_name",
            schema_limit=255,
            max_found=300,
            exceeds_by=45,
            affected_count=2,
            samples=[
                {"record_index": 0, "value_length": 300, "preview": "A" * 50 + "..."}
            ],
            recommendations=["Truncate to 255 characters"],
        )
        d = violation.to_dict()

        assert d["severity"] == "critical"
        assert d["field"] == "app_name"
        assert d["schema_limit"] == 255
        assert d["max_found"] == 300
        assert d["exceeds_by"] == 45
