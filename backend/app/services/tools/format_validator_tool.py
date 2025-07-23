"""
Format Validator Tool for data format validation
"""

import json
import logging
import re
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

logger = logging.getLogger(__name__)


class FormatValidatorTool(AsyncBaseDiscoveryTool):
    """Validates data formats against expected patterns"""

    name: str = "format_validator"
    description: str = "Validate data formats and detect format inconsistencies"

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="format_validator",
            description="Comprehensive format validation for various data types",
            tool_class=cls,
            categories=["validation", "format", "data_quality"],
            required_params=["data"],
            optional_params=["format_rules", "strict_mode"],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self,
        data: List[Dict[str, Any]],
        format_rules: Dict[str, str] = None,
        strict_mode: bool = False,
    ) -> str:
        """
        Validate data formats across all fields.

        Args:
            data: Data to validate
            format_rules: Custom format rules per field
            strict_mode: Whether to apply strict validation

        Returns:
            JSON string with validation results
        """
        try:
            if not data:
                return json.dumps({"error": "No data provided for validation"})

            validation_results = {
                "overall_valid": True,
                "total_records": len(data),
                "total_fields": len(data[0]) if data else 0,
                "field_validation": {},
                "format_issues": [],
                "summary": {},
                "recommendations": [],
            }

            # Get all unique fields
            all_fields = set()
            for record in data:
                all_fields.update(record.keys())

            # Validate each field
            for field in all_fields:
                field_validation = await self._validate_field_format(
                    field, data, format_rules, strict_mode
                )
                validation_results["field_validation"][field] = field_validation

                if not field_validation["valid"]:
                    validation_results["overall_valid"] = False

                # Collect issues
                validation_results["format_issues"].extend(
                    field_validation.get("issues", [])
                )

            # Generate summary and recommendations
            validation_results["summary"] = self._create_validation_summary(
                validation_results
            )
            validation_results["recommendations"] = (
                self._generate_format_recommendations(validation_results)
            )

            return json.dumps(validation_results, indent=2)

        except Exception as e:
            logger.error(f"Format validation failed: {e}")
            return json.dumps({"error": str(e), "overall_valid": False})

    async def _validate_field_format(
        self,
        field: str,
        data: List[Dict[str, Any]],
        format_rules: Dict[str, str] = None,
        strict_mode: bool = False,
    ) -> Dict[str, Any]:
        """Validate format for a specific field"""

        # Extract values for this field
        values = []
        for record in data:
            if field in record and record[field] is not None:
                values.append(record[field])

        if not values:
            return {
                "field": field,
                "valid": True,
                "total_values": 0,
                "valid_values": 0,
                "issues": [],
                "detected_format": "empty",
            }

        validation_result = {
            "field": field,
            "total_values": len(values),
            "valid_values": 0,
            "invalid_values": 0,
            "issues": [],
            "detected_format": None,
            "format_consistency": 0.0,
            "sample_valid": [],
            "sample_invalid": [],
        }

        # Check if custom format rule exists
        if format_rules and field in format_rules:
            custom_pattern = format_rules[field]
            validation_result.update(
                self._validate_against_pattern(
                    values, custom_pattern, f"custom_{field}"
                )
            )
        else:
            # Auto-detect format and validate
            detected_format = self._detect_field_format(field, values)
            validation_result["detected_format"] = detected_format

            if detected_format != "unknown":
                format_validation = self._validate_detected_format(
                    values, detected_format, strict_mode
                )
                validation_result.update(format_validation)
            else:
                # Basic validation for unknown formats
                validation_result.update(self._basic_format_validation(values))

        # Determine if field is valid
        if validation_result["total_values"] > 0:
            validation_result["format_consistency"] = (
                validation_result["valid_values"] / validation_result["total_values"]
            )
            validation_result["valid"] = validation_result["format_consistency"] >= (
                0.95 if strict_mode else 0.8
            )
        else:
            validation_result["valid"] = True

        return validation_result

    def _detect_field_format(self, field_name: str, values: List[Any]) -> str:
        """Auto-detect the expected format for a field"""
        field_lower = field_name.lower()
        sample_values = [str(v) for v in values[:20]]  # Sample first 20 values

        # Pattern-based detection using field name
        name_patterns = {
            "email": ["email", "mail", "e_mail"],
            "phone": ["phone", "tel", "telephone", "mobile", "cell"],
            "ip": ["ip", "ip_address", "ipaddress"],
            "mac": ["mac", "mac_address", "macaddress"],
            "url": ["url", "website", "link", "uri"],
            "date": ["date", "created", "updated", "modified", "time"],
            "id": ["id", "identifier", "key", "uuid", "guid"],
            "currency": ["price", "cost", "amount", "salary", "fee"],
            "postal": ["zip", "postal", "postcode"],
            "ssn": ["ssn", "social", "security"],
        }

        for format_type, keywords in name_patterns.items():
            if any(keyword in field_lower for keyword in keywords):
                # Verify with sample values
                if self._verify_format_with_samples(sample_values, format_type):
                    return format_type

        # Content-based detection
        if sample_values:
            return self._detect_format_from_content(sample_values)

        return "unknown"

    def _verify_format_with_samples(
        self, sample_values: List[str], format_type: str
    ) -> bool:
        """Verify detected format with sample values"""
        patterns = self._get_format_patterns()

        if format_type not in patterns:
            return False

        pattern = patterns[format_type]
        matches = sum(1 for v in sample_values if re.match(pattern, v, re.IGNORECASE))

        # At least 60% should match for confirmation
        return matches / len(sample_values) >= 0.6

    def _detect_format_from_content(self, sample_values: List[str]) -> str:
        """Detect format based on content analysis"""
        patterns = self._get_format_patterns()

        format_scores = {}

        for format_type, pattern in patterns.items():
            matches = sum(
                1 for v in sample_values if re.match(pattern, v, re.IGNORECASE)
            )
            score = matches / len(sample_values)

            if score >= 0.6:  # At least 60% match
                format_scores[format_type] = score

        # Return format with highest score
        if format_scores:
            return max(format_scores.items(), key=lambda x: x[1])[0]

        # Check for numeric patterns
        numeric_count = sum(1 for v in sample_values if self._is_numeric(v))
        if numeric_count / len(sample_values) >= 0.8:
            return "numeric"

        # Check for boolean patterns
        boolean_count = sum(
            1
            for v in sample_values
            if v.lower() in ["true", "false", "1", "0", "yes", "no"]
        )
        if boolean_count / len(sample_values) >= 0.8:
            return "boolean"

        return "text"

    def _validate_detected_format(
        self, values: List[Any], format_type: str, strict_mode: bool
    ) -> Dict[str, Any]:
        """Validate values against detected format"""
        patterns = self._get_format_patterns()

        if format_type not in patterns:
            return self._basic_format_validation(values)

        pattern = patterns[format_type]
        return self._validate_against_pattern(values, pattern, format_type)

    def _validate_against_pattern(
        self, values: List[Any], pattern: str, format_name: str
    ) -> Dict[str, Any]:
        """Validate values against a specific pattern"""
        valid_values = []
        invalid_values = []
        issues = []

        for value in values:
            str_value = str(value)

            if re.match(pattern, str_value, re.IGNORECASE):
                valid_values.append(value)
            else:
                invalid_values.append(value)

        # Generate issues for invalid values
        if invalid_values:
            issues.append(
                f"Found {len(invalid_values)} values that don't match {format_name} format"
            )

            # Add sample invalid values
            sample_invalid = invalid_values[:3]
            issues.append(f"Sample invalid values: {sample_invalid}")

        return {
            "valid_values": len(valid_values),
            "invalid_values": len(invalid_values),
            "issues": issues,
            "sample_valid": valid_values[:3],
            "sample_invalid": invalid_values[:3],
        }

    def _basic_format_validation(self, values: List[Any]) -> Dict[str, Any]:
        """Basic validation for unknown formats"""
        valid_count = 0
        issues = []

        # Check for basic data quality issues
        empty_count = sum(1 for v in values if str(v).strip() == "")
        null_like_count = sum(
            1 for v in values if str(v).lower() in ["null", "none", "n/a", "undefined"]
        )

        valid_count = len(values) - empty_count - null_like_count

        if empty_count > 0:
            issues.append(f"Found {empty_count} empty values")

        if null_like_count > 0:
            issues.append(f"Found {null_like_count} null-like values")

        return {
            "valid_values": valid_count,
            "invalid_values": empty_count + null_like_count,
            "issues": issues,
            "sample_valid": [
                v
                for v in values
                if str(v).strip()
                and str(v).lower() not in ["null", "none", "n/a", "undefined"]
            ][:3],
            "sample_invalid": [
                v
                for v in values
                if not str(v).strip()
                or str(v).lower() in ["null", "none", "n/a", "undefined"]
            ][:3],
        }

    def _get_format_patterns(self) -> Dict[str, str]:
        """Get predefined format patterns"""
        return {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^[\+]?[\d\s\-\(\)\.]{7,15}$",
            "ip": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            "mac": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
            "url": r"^https?://[^\s/$.?#].[^\s]*$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "datetime": r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}",
            "time": r"^\d{2}:\d{2}(:\d{2})?$",
            "id": r"^[a-zA-Z0-9\-_]{3,}$",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "currency": r"^\$?[\d,]+\.?\d*$",
            "postal": r"^[A-Za-z0-9\s\-]{3,10}$",
            "ssn": r"^\d{3}-\d{2}-\d{4}$",
            "credit_card": r"^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$",
        }

    def _is_numeric(self, value: str) -> bool:
        """Check if a value is numeric"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _create_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create validation summary"""
        field_validations = results["field_validation"]

        total_fields = len(field_validations)
        valid_fields = sum(1 for v in field_validations.values() if v["valid"])

        # Calculate overall format consistency
        if field_validations:
            consistencies = [
                v["format_consistency"] for v in field_validations.values()
            ]
            avg_consistency = sum(consistencies) / len(consistencies)
        else:
            avg_consistency = 0.0

        # Count detected formats
        detected_formats = {}
        for validation in field_validations.values():
            format_type = validation.get("detected_format", "unknown")
            detected_formats[format_type] = detected_formats.get(format_type, 0) + 1

        return {
            "total_fields": total_fields,
            "valid_fields": valid_fields,
            "invalid_fields": total_fields - valid_fields,
            "validation_rate": (
                (valid_fields / total_fields * 100) if total_fields > 0 else 0
            ),
            "average_consistency": round(avg_consistency * 100, 1),
            "detected_formats": detected_formats,
            "total_issues": len(results["format_issues"]),
        }

    def _generate_format_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate format validation recommendations"""
        recommendations = []

        summary = results["summary"]
        field_validations = results["field_validation"]

        # Overall recommendations
        if summary["validation_rate"] < 80:
            recommendations.append(
                "Consider data cleansing - low format validation rate"
            )

        if summary["average_consistency"] < 90:
            recommendations.append("Standardize data formats across all fields")

        # Field-specific recommendations
        for field, validation in field_validations.items():
            if not validation["valid"]:
                if validation["format_consistency"] < 0.5:
                    recommendations.append(
                        f"Field '{field}': Major format inconsistencies detected"
                    )
                else:
                    recommendations.append(
                        f"Field '{field}': Minor format issues need attention"
                    )

        # Format-specific recommendations
        detected_formats = summary["detected_formats"]
        if "unknown" in detected_formats and detected_formats["unknown"] > 2:
            recommendations.append(
                "Multiple fields have unrecognized formats - review data standards"
            )

        return recommendations
