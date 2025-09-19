"""
Data Validation Tool Implementations

Core implementation classes for data validation, analysis, and quality assessment.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataValidationToolImpl:
    """Implementation of data validation logic"""

    @staticmethod
    async def validate_data(
        raw_data: List[Dict[str, Any]], context_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate imported data for structure and quality"""
        try:
            logger.info(f"🔍 Validating {len(raw_data)} records")

            validation_results = {
                "total_records": len(raw_data),
                "valid_records": 0,
                "invalid_records": 0,
                "errors": [],
                "warnings": [],
                "field_statistics": {},
            }

            if not raw_data:
                validation_results["errors"].append("No data to validate")
                return validation_results

            # Analyze field presence and consistency
            all_fields: set[str] = set()
            field_counts: Dict[str, int] = {}

            for idx, record in enumerate(raw_data):
                if not isinstance(record, dict):
                    validation_results["errors"].append(
                        f"Record {idx} is not a dictionary"
                    )
                    validation_results["invalid_records"] += 1
                    continue

                # Track fields
                for field in record.keys():
                    all_fields.add(field)
                    field_counts[field] = field_counts.get(field, 0) + 1

                validation_results["valid_records"] += 1

            # Calculate field statistics
            for field in all_fields:
                completeness = (field_counts.get(field, 0) / len(raw_data)) * 100
                validation_results["field_statistics"][field] = {
                    "count": field_counts.get(field, 0),
                    "completeness_percentage": round(completeness, 2),
                    "is_required": (
                        completeness > 90
                    ),  # Fields present in >90% of records
                }

            # Check for required fields
            required_fields = [
                field
                for field, stats in validation_results["field_statistics"].items()
                if stats["is_required"]
            ]

            if not required_fields:
                validation_results["warnings"].append(
                    "No consistently present fields found - " "data may be inconsistent"
                )

            validation_results["required_fields"] = required_fields
            validation_results["all_fields"] = list(all_fields)

            logger.info(
                f"✅ Validation complete: "
                f"{validation_results['valid_records']} valid, "
                f"{validation_results['invalid_records']} invalid"
            )

            return validation_results

        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            return {
                "total_records": len(raw_data) if raw_data else 0,
                "valid_records": 0,
                "invalid_records": len(raw_data) if raw_data else 0,
                "errors": [str(e)],
                "warnings": [],
            }


class DataStructureAnalyzerImpl:
    """Implementation of data structure analysis"""

    @staticmethod
    async def analyze_structure(
        raw_data: List[Dict[str, Any]], context_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the structure and patterns in imported data"""
        try:
            logger.info(f"🔬 Analyzing data structure for {len(raw_data)} records")

            analysis = {
                "record_count": len(raw_data),
                "field_types": {},
                "patterns_detected": [],
                "asset_type_indicators": {},
                "data_quality_score": 0,
            }

            if not raw_data:
                return analysis

            # Analyze field types and patterns
            for record in raw_data[:100]:  # Sample first 100 records
                for field, value in record.items():
                    if field not in analysis["field_types"]:
                        analysis["field_types"][field] = {
                            "types_found": set(),
                            "sample_values": [],
                        }

                    # Detect type
                    value_type = type(value).__name__
                    analysis["field_types"][field]["types_found"].add(value_type)

                    # Store sample values
                    if len(analysis["field_types"][field]["sample_values"]) < 5:
                        analysis["field_types"][field]["sample_values"].append(
                            str(value)[:100]
                        )

            # Detect asset type indicators
            asset_indicators = {
                "server": [
                    "hostname",
                    "ip_address",
                    "operating_system",
                    "cpu",
                    "memory",
                ],
                "application": ["app_name", "version", "vendor", "service", "url"],
                "database": ["db_name", "db_type", "schema", "instance", "port"],
                "network": ["device_type", "switch", "router", "firewall", "vlan"],
            }

            for asset_type, indicators in asset_indicators.items():
                matches = sum(
                    1
                    for indicator in indicators
                    if any(
                        indicator.lower() in field.lower()
                        for field in analysis["field_types"].keys()
                    )
                )
                if matches > 0:
                    analysis["asset_type_indicators"][asset_type] = {
                        "confidence": matches / len(indicators),
                        "matched_fields": matches,
                    }

            # Calculate data quality score
            total_fields = len(analysis["field_types"])
            consistent_fields = sum(
                1
                for field_info in analysis["field_types"].values()
                if len(field_info["types_found"]) == 1
            )
            analysis["data_quality_score"] = (
                (consistent_fields / total_fields * 100) if total_fields > 0 else 0
            )

            # Convert sets to lists for JSON serialization
            for field_info in analysis["field_types"].values():
                field_info["types_found"] = list(field_info["types_found"])

            logger.info("✅ Structure analysis complete")
            return analysis

        except Exception as e:
            logger.error(f"❌ Structure analysis failed: {e}")
            return {
                "record_count": len(raw_data) if raw_data else 0,
                "field_types": {},
                "patterns_detected": [],
                "error": str(e),
            }


class FieldSuggestionImpl:
    """Implementation of field suggestion logic"""

    @staticmethod
    def generate_suggestions(mapping_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate field mapping suggestions"""
        try:
            source_fields = mapping_request.get("source_fields", [])

            suggestions = {}
            for field in source_fields:
                field_lower = field.lower()

                # Common mapping patterns
                if "hostname" in field_lower or "host" in field_lower:
                    suggestions[field] = {
                        "target": "hostname",
                        "confidence": 0.9,
                        "type": "direct",
                    }
                elif "ip" in field_lower or "address" in field_lower:
                    suggestions[field] = {
                        "target": "ip_address",
                        "confidence": 0.85,
                        "type": "direct",
                    }
                elif "os" in field_lower or "operating" in field_lower:
                    suggestions[field] = {
                        "target": "operating_system",
                        "confidence": 0.8,
                        "type": "direct",
                    }
                elif "env" in field_lower:
                    suggestions[field] = {
                        "target": "environment",
                        "confidence": 0.75,
                        "type": "direct",
                    }
                else:
                    # Default suggestion
                    suggestions[field] = {
                        "target": field.replace(" ", "_").lower(),
                        "confidence": 0.5,
                        "type": "inferred",
                    }

            return {
                "suggestions": suggestions,
                "total_fields": len(source_fields),
                "mapped_fields": len(suggestions),
            }

        except Exception as e:
            logger.error(f"❌ Field suggestion failed: {e}")
            return {"error": str(e), "suggestions": {}}


class DataQualityImpl:
    """Implementation of data quality assessment"""

    @staticmethod
    def assess_quality(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data quality"""
        try:
            assessment = {
                "total_records": len(raw_data),
                "quality_score": 0,
                "issues": [],
                "recommendations": [],
            }

            if not raw_data:
                assessment["issues"].append("No data to assess")
                return assessment

            # Check for empty records
            empty_records = sum(1 for r in raw_data if not r or len(r) == 0)
            if empty_records > 0:
                assessment["issues"].append(f"{empty_records} empty records found")

            # Check for consistency
            field_sets = [set(r.keys()) for r in raw_data if isinstance(r, dict)]
            if field_sets:
                common_fields = set.intersection(*field_sets)
                consistency_score = len(common_fields) / len(field_sets[0]) * 100
            else:
                consistency_score = 0

            # Check for null values
            null_count = 0
            for record in raw_data:
                if isinstance(record, dict):
                    null_count += sum(
                        1 for v in record.values() if v is None or v == ""
                    )

            # Calculate overall quality score
            assessment["quality_score"] = max(
                0,
                min(
                    100,
                    consistency_score
                    - (empty_records / len(raw_data) * 20)
                    - (null_count / (len(raw_data) * 10) * 10),
                ),
            )

            # Generate recommendations
            if assessment["quality_score"] < 50:
                assessment["recommendations"].append(
                    "Data quality is low - extensive cleansing required"
                )
            elif assessment["quality_score"] < 75:
                assessment["recommendations"].append(
                    "Data quality is moderate - some cleansing recommended"
                )
            else:
                assessment["recommendations"].append(
                    "Data quality is good - ready for processing"
                )

            return assessment

        except Exception as e:
            logger.error(f"❌ Quality assessment failed: {e}")
            return {"error": str(e), "quality_score": 0, "recommendations": []}
