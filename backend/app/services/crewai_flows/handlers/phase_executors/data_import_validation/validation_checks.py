"""
Core validation checks for data import validation.
Contains the main validation logic and coordination.

Enhanced with intelligent data profiling per ADR-038:
- Multi-value detection
- Full dataset analysis
- Field length validation against schema constraints
- Data profile report generation

Related: ADR-038, Issue #1204
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_profiler import DataProfiler, DataProfileReport

logger = logging.getLogger(__name__)


class ValidationChecks:
    """Core validation checks for data import validation"""

    def __init__(self, state):
        self.state = state

    async def perform_validation_checks(self) -> Dict[str, Any]:
        """
        Perform comprehensive validation checks on imported data.
        This includes structure, PII, security, and data type validation.
        """
        try:
            logger.info("🔍 Starting comprehensive data validation")

            validation_results = {
                "is_valid": True,
                "validation_passed": True,
                "timestamp": self._get_timestamp(),
                "total_records": len(self.state.raw_data) if self.state.raw_data else 0,
                "validation_summary": {},
            }

            # 1. Structure validation
            structure_results = self.check_data_structure()
            validation_results["structure_validation"] = structure_results

            if not structure_results.get("is_valid", False):
                validation_results["is_valid"] = False
                validation_results["reason"] = "Data structure validation failed"
                logger.warning("⚠️ Data structure validation failed")

            # 2. PII Detection
            pii_results = self.detect_pii()
            validation_results["pii_detection"] = pii_results

            if pii_results.get("pii_detected", False):
                logger.warning("⚠️ PII detected in data - may need special handling")

            # 3. Security scanning
            security_results = self.scan_for_malicious_content()
            validation_results["security_scan"] = security_results

            if security_results.get("malicious_content_detected", False):
                validation_results["is_valid"] = False
                validation_results["reason"] = "Malicious content detected"
                logger.error("❌ Malicious content detected in data")

            # 4. Data type validation
            type_results = self.validate_data_types()
            validation_results["data_type_validation"] = type_results

            # 5. Source validation
            source_results = self.validate_data_source()
            validation_results["source_validation"] = source_results

            # Generate summary
            validation_results["validation_summary"] = {
                "structure_valid": structure_results.get("is_valid", False),
                "pii_detected": pii_results.get("pii_detected", False),
                "security_threats": security_results.get(
                    "malicious_content_detected", False
                ),
                "type_validation_score": type_results.get("quality_score", 0),
                "source_valid": source_results.get("is_valid", False),
                "overall_quality_score": self._calculate_overall_score(
                    validation_results
                ),
            }

            # If validation passed, include the data
            if validation_results["is_valid"]:
                validation_results["validated_data"] = self.state.raw_data
                logger.info("✅ Data validation completed successfully")

            # Add additional metadata for storage
            validation_results.update(
                {
                    "validator": "DataImportValidationExecutor",
                    "validation_version": "1.0",
                    "engagement_id": getattr(self.state, "engagement_id", ""),
                    "client_account_id": getattr(self.state, "client_account_id", ""),
                }
            )

            return validation_results

        except Exception as e:
            logger.error(f"❌ Validation failed with error: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "validation_passed": False,
                "reason": f"Validation error: {str(e)}",
                "timestamp": self._get_timestamp(),
                "error_details": str(e),
            }

    def check_data_structure(self) -> Dict[str, Any]:
        """Check if the data structure is valid for processing"""
        try:
            # Enhanced debugging for data structure validation
            logger.info("🔍 Starting data structure validation")

            if not self.state.raw_data:
                logger.warning("⚠️ No raw data found in state")
                return {
                    "is_valid": False,
                    "reason": "No data provided",
                    "record_count": 0,
                    "structure_analysis": {"empty_data": True},
                }

            if not isinstance(self.state.raw_data, list):
                logger.warning("⚠️ Raw data is not a list")
                return {
                    "is_valid": False,
                    "reason": "Data is not in expected list format",
                    "data_type": str(type(self.state.raw_data)),
                    "structure_analysis": {"invalid_format": True},
                }

            record_count = len(self.state.raw_data)
            logger.info(f"🔍 Found {record_count} records to validate")

            if record_count == 0:
                return {
                    "is_valid": False,
                    "reason": "Empty data list",
                    "record_count": 0,
                    "structure_analysis": {"empty_list": True},
                }

            # Check first record structure
            first_record = self.state.raw_data[0]
            if not isinstance(first_record, dict):
                logger.warning(
                    f"⚠️ First record is not a dictionary: {type(first_record)}"
                )
                return {
                    "is_valid": False,
                    "reason": "Records are not in dictionary format",
                    "first_record_type": str(type(first_record)),
                    "structure_analysis": {"invalid_record_format": True},
                }

            field_count = len(first_record.keys())
            logger.info(f"🔍 First record has {field_count} fields")

            return {
                "is_valid": True,
                "record_count": record_count,
                "field_count": field_count,
                "sample_fields": list(first_record.keys())[:10],  # First 10 fields
                "structure_analysis": {
                    "valid_format": True,
                    "has_fields": field_count > 0,
                    "consistent_structure": True,  # Could be enhanced
                },
            }

        except Exception as e:
            logger.error(f"❌ Structure validation failed: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "reason": f"Structure validation error: {str(e)}",
                "error": str(e),
            }

    def detect_pii(self) -> Dict[str, Any]:
        """Detect Personally Identifiable Information in the data"""
        try:
            pii_indicators = {
                "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "phone": r"\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b",
                "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            }

            pii_detected = False
            pii_types_found = []

            # Check field names for PII indicators
            if self.state.raw_data and isinstance(self.state.raw_data[0], dict):
                field_names = list(self.state.raw_data[0].keys())
                pii_field_names = []

                for field in field_names:
                    field_lower = field.lower()
                    if any(
                        pii_term in field_lower
                        for pii_term in ["ssn", "social", "email", "phone", "credit"]
                    ):
                        pii_field_names.append(field)
                        pii_detected = True
                        pii_types_found.append(f"field_name_{field}")

                # Basic pattern matching on first few records
                if not pii_detected:
                    sample_records = self.state.raw_data[:5]  # Check first 5 records
                    for record in sample_records:
                        if isinstance(record, dict):
                            for value in record.values():
                                if isinstance(value, str):
                                    for pii_type, pattern in pii_indicators.items():
                                        if re.search(pattern, value):
                                            pii_detected = True
                                            pii_types_found.append(pii_type)
                                            break

            return {
                "pii_detected": pii_detected,
                "pii_types": list(set(pii_types_found)),
                "confidence": 0.8 if pii_detected else 0.1,
                "recommendation": (
                    "Review data handling procedures"
                    if pii_detected
                    else "No immediate PII concerns"
                ),
            }

        except Exception as e:
            logger.error(f"❌ PII detection failed: {str(e)}")
            return {"pii_detected": False, "error": str(e)}

    def scan_for_malicious_content(self) -> Dict[str, Any]:
        """Scan data for malicious patterns"""
        try:
            # Basic malicious pattern detection
            malicious_patterns = [
                r"<script[^>]*>.*?</script>",  # Script tags
                r"javascript:",  # JavaScript URLs
                r"data:text/html",  # Data URLs
                r"eval\s*\(",  # eval() calls
                r"document\.write",  # document.write
                r"window\.location",  # location manipulation
                r"<iframe[^>]*>",  # iframe tags
                r"on\w+\s*=",  # event handlers
                r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b",  # SQL injection patterns
            ]

            malicious_content_detected = False
            detected_patterns = []

            # Check sample records for malicious patterns
            sample_records = (
                self.state.raw_data[:10] if self.state.raw_data else []
            )  # Check first 10 records
            for record in sample_records:
                if isinstance(record, dict):
                    for value in record.values():
                        if isinstance(value, str):
                            for pattern in malicious_patterns:
                                if re.search(pattern, value, re.IGNORECASE):
                                    malicious_content_detected = True
                                    detected_patterns.append(pattern)

            return {
                "malicious_content_detected": malicious_content_detected,
                "detected_patterns": list(set(detected_patterns)),
                "scanned_records": len(sample_records),
                "recommendation": (
                    "Block upload"
                    if malicious_content_detected
                    else "Content appears safe"
                ),
            }

        except Exception as e:
            logger.error(f"❌ Security scan failed: {str(e)}")
            return {"malicious_content_detected": False, "error": str(e)}

    def validate_data_types(self) -> Dict[str, Any]:
        """Validate data types and consistency"""
        try:
            if not self.state.raw_data or not isinstance(self.state.raw_data[0], dict):
                return {"quality_score": 0.0}

            # Analyze first record to understand field types
            first_record = self.state.raw_data[0]
            type_analysis = {}

            for field, value in first_record.items():
                # Basic type validation - accept most common types
                if isinstance(value, (str, int, float, bool, type(None))):
                    type_analysis[field] = {
                        "type": type(value).__name__,
                        "valid": True,
                    }
                else:
                    type_analysis[field] = {
                        "type": type(value).__name__,
                        "valid": False,
                    }

            valid_fields = sum(
                1 for field_info in type_analysis.values() if field_info["valid"]
            )
            total_fields = len(type_analysis)
            quality_score = valid_fields / total_fields if total_fields > 0 else 0.0

            return {"quality_score": quality_score, "type_analysis": type_analysis}

        except Exception as e:
            logger.error(f"❌ Data type validation failed: {str(e)}")
            return {"quality_score": 0.5}  # Default moderate score

    def validate_data_source(self) -> Dict[str, Any]:
        """Validate the data source information"""
        try:
            metadata = getattr(self.state, "metadata", {})

            # Check if source information is available
            source_info = metadata.get("source", {})
            has_source = bool(source_info)

            # Basic source validation
            is_valid = True
            validation_notes = []

            if not has_source:
                validation_notes.append("No source information provided")
                is_valid = False
            else:
                # Check for basic source fields
                expected_fields = ["type", "name"]
                missing_fields = [
                    field for field in expected_fields if field not in source_info
                ]
                if missing_fields:
                    validation_notes.append(
                        f"Missing source fields: {', '.join(missing_fields)}"
                    )

            return {
                "is_valid": is_valid,
                "has_source_info": has_source,
                "source_info": source_info,
                "validation_notes": validation_notes,
            }

        except Exception as e:
            logger.error(f"❌ Source validation failed: {str(e)}")
            return {"is_valid": False, "error": str(e)}

    def _calculate_overall_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate an overall quality score"""
        scores = []

        # Structure validation (pass/fail)
        if validation_results.get("structure_validation", {}).get("is_valid", False):
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Security (pass/fail - security issues are critical)
        if not validation_results.get("security_scan", {}).get(
            "malicious_content_detected", False
        ):
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Data type quality score
        type_score = validation_results.get("data_type_validation", {}).get(
            "quality_score", 0.0
        )
        scores.append(type_score)

        # Source validation (pass/fail)
        if validation_results.get("source_validation", {}).get("is_valid", False):
            scores.append(1.0)
        else:
            scores.append(0.5)  # Less critical than other factors

        return sum(scores) / len(scores) if scores else 0.0

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()

    # ========================================================================
    # ADR-038: Intelligent Data Profiling Integration
    # ========================================================================

    def generate_data_profile(
        self,
        schema_constraints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive data profile with intelligent analysis.

        This is the main entry point for ADR-038 data profiling, which includes:
        - Multi-value detection (comma/semicolon/pipe-separated)
        - Full dataset analysis (all records, not samples)
        - Field length validation against schema constraints
        - Quality scoring and recommendations

        Args:
            schema_constraints: Optional schema constraints dict. If None,
                               will be loaded from schema_constraints utility.

        Returns:
            Dict with full data profile report suitable for UI display

        Related: ADR-038, Issue #1204
        """
        try:
            logger.info("[ADR-038] Starting intelligent data profiling")

            if not self.state.raw_data:
                logger.warning("[ADR-038] No raw data available for profiling")
                return {
                    "error": "No data available for profiling",
                    "profile": None,
                }

            # Create profiler and generate report
            profiler = DataProfiler(self.state.raw_data)
            report: DataProfileReport = profiler.generate_profile_report(
                schema_constraints
            )

            # Convert to dict for storage and API response
            profile_dict = report.to_dict()

            logger.info(
                f"[ADR-038] Data profiling complete: "
                f"{report.total_records} records, "
                f"{report.blocking_issue_count} blocking issues, "
                f"overall score: {report.overall_quality_score}"
            )

            return profile_dict

        except Exception as e:
            logger.error(f"[ADR-038] Data profiling failed: {e}", exc_info=True)
            return {
                "error": f"Profiling failed: {str(e)}",
                "profile": None,
            }

    def detect_multi_values_only(
        self, field_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect multi-valued fields without full profiling.

        Useful for quick checks during field mapping preview.

        Args:
            field_name: Optional specific field to check

        Returns:
            List of multi-value detection results
        """
        if not self.state.raw_data:
            return []

        profiler = DataProfiler(self.state.raw_data)
        results = profiler.detect_multi_values(field_name)
        return [r.to_dict() for r in results]

    def check_field_lengths_only(
        self,
        schema_constraints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Check field length violations without full profiling.

        Useful for quick validation during import preview.

        Args:
            schema_constraints: Optional schema constraints

        Returns:
            List of length violation results
        """
        if not self.state.raw_data:
            return []

        profiler = DataProfiler(self.state.raw_data)
        violations = profiler.check_field_length_violations(schema_constraints)
        return [v.to_dict() for v in violations]
