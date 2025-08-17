"""
Validation Handler
Handles field validation and missing field detection functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationHandler:
    """Handles field validation operations with graceful fallbacks."""

    def __init__(self):
        self.service_available = True

        # Required fields by asset type
        self.required_fields_by_type = {
            "server": [
                "Asset Name",
                "IP Address",
                "Operating System",
                "Environment",
                "CPU Cores",
                "Memory (GB)",
                "Business Owner",
            ],
            "application": [
                "Asset Name",
                "Business Owner",
                "Environment",
                "Version",
                "Criticality",
                "Application Service",
            ],
            "database": [
                "Asset Name",
                "Business Owner",
                "Environment",
                "Version",
                "Storage (GB)",
                "Criticality",
            ],
            "network": ["Asset Name", "IP Address", "Location", "Vendor", "Model"],
            "storage": ["Asset Name", "Storage (GB)", "Location", "Vendor", "Model"],
            "generic": ["Asset Name", "Asset Type", "Environment", "Business Owner"],
        }

        logger.info("Validation handler initialized successfully")

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    def identify_missing_fields(
        self,
        available_columns: List[str],
        asset_type: str = "server",
        mapped_fields: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Identify missing required fields for asset type."""
        try:
            required_fields = self.required_fields_by_type.get(
                asset_type, self.required_fields_by_type["generic"]
            )

            # If we have mapped fields, use those to check coverage
            if mapped_fields:
                covered_canonical_fields = set(mapped_fields.values())
            else:
                # Fallback to simple string matching
                covered_canonical_fields = set()
                available_lower = [
                    col.lower().replace(" ", "_") for col in available_columns
                ]

                for required_field in required_fields:
                    required_lower = required_field.lower().replace(" ", "_")
                    for available_field in available_lower:
                        if (
                            required_lower in available_field
                            or available_field in required_lower
                        ):
                            covered_canonical_fields.add(required_field)
                            break

            # Find missing fields
            missing_fields = []
            for required_field in required_fields:
                if required_field not in covered_canonical_fields:
                    missing_fields.append(required_field)

            return missing_fields

        except Exception as e:
            logger.error(f"Error identifying missing fields: {e}")
            return []

    def validate_field_format(
        self, field_name: str, value: Any, canonical_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate field format and suggest corrections."""
        try:
            validation_result = {
                "is_valid": True,
                "original_value": value,
                "suggested_value": None,
                "validation_message": "Field format is valid",
                "confidence": 1.0,
            }

            # Use canonical field for validation if available
            target_field = canonical_field or field_name
            target_field_lower = target_field.lower()

            # IP Address validation
            if "ip" in target_field_lower and "address" in target_field_lower:
                if not self._is_valid_ip(str(value)):
                    validation_result.update(
                        {
                            "is_valid": False,
                            "suggested_value": self._suggest_ip_format(str(value)),
                            "validation_message": "Invalid IP address format",
                            "confidence": 0.8,
                        }
                    )

            # Memory validation (should be numeric)
            elif "memory" in target_field_lower or "ram" in target_field_lower:
                if not self._is_numeric(value):
                    validation_result.update(
                        {
                            "is_valid": False,
                            "suggested_value": self._extract_numeric(str(value)),
                            "validation_message": "Memory should be numeric (GB)",
                            "confidence": 0.9,
                        }
                    )

            # CPU validation (should be numeric)
            elif "cpu" in target_field_lower or "core" in target_field_lower:
                if not self._is_numeric(value):
                    validation_result.update(
                        {
                            "is_valid": False,
                            "suggested_value": self._extract_numeric(str(value)),
                            "validation_message": "CPU cores should be numeric",
                            "confidence": 0.9,
                        }
                    )

            # Environment validation
            elif "environment" in target_field_lower:
                valid_envs = [
                    "production",
                    "prod",
                    "staging",
                    "stage",
                    "development",
                    "dev",
                    "test",
                    "qa",
                ]
                if str(value).lower() not in valid_envs:
                    suggested = self._suggest_environment(str(value))
                    if suggested:
                        validation_result.update(
                            {
                                "is_valid": False,
                                "suggested_value": suggested,
                                "validation_message": f"Environment should be one of: {', '.join(valid_envs)}",
                                "confidence": 0.7,
                            }
                        )

            # Criticality validation
            elif "critical" in target_field_lower or "priority" in target_field_lower:
                valid_criticality = ["low", "medium", "high", "critical"]
                if str(value).lower() not in valid_criticality:
                    suggested = self._suggest_criticality(str(value))
                    if suggested:
                        validation_result.update(
                            {
                                "is_valid": False,
                                "suggested_value": suggested,
                                "validation_message": f"Criticality should be one of: {', '.join(valid_criticality)}",
                                "confidence": 0.8,
                            }
                        )

            return validation_result

        except Exception as e:
            logger.error(f"Error validating field format: {e}")
            return {
                "is_valid": False,
                "original_value": value,
                "suggested_value": None,
                "validation_message": f"Validation error: {str(e)}",
                "confidence": 0.0,
            }

    def validate_data_completeness(
        self, data: List[Dict[str, Any]], asset_type: str = "server"
    ) -> Dict[str, Any]:
        """Validate data completeness across records."""
        try:
            if not data:
                return {
                    "completeness_score": 0.0,
                    "total_records": 0,
                    "field_completeness": {},
                    "recommendations": ["No data provided for validation"],
                }

            # Calculate field completeness
            field_stats = {}
            total_records = len(data)

            # Get all fields from the data
            all_fields = set()
            for record in data:
                all_fields.update(record.keys())

            # Calculate completeness for each field
            for field in all_fields:
                filled_count = sum(
                    1
                    for record in data
                    if record.get(field) and str(record[field]).strip()
                )
                field_stats[field] = {
                    "filled_count": filled_count,
                    "empty_count": total_records - filled_count,
                    "completeness_ratio": (
                        filled_count / total_records if total_records > 0 else 0
                    ),
                }

            # Calculate overall completeness
            total_possible_values = len(all_fields) * total_records
            total_filled_values = sum(
                stats["filled_count"] for stats in field_stats.values()
            )
            overall_completeness = (
                total_filled_values / total_possible_values
                if total_possible_values > 0
                else 0
            )

            # Generate recommendations
            recommendations = []
            low_completeness_fields = [
                field
                for field, stats in field_stats.items()
                if stats["completeness_ratio"] < 0.5
            ]

            if low_completeness_fields:
                recommendations.append(
                    f"Improve data collection for fields with low completeness: "
                    f"{', '.join(low_completeness_fields[:5])}"
                )

            if overall_completeness < 0.7:
                recommendations.append(
                    "Overall data completeness is below 70% - consider data cleanup efforts"
                )

            if overall_completeness >= 0.9:
                recommendations.append(
                    "Excellent data completeness - ready for migration planning"
                )

            return {
                "completeness_score": overall_completeness,
                "total_records": total_records,
                "total_fields": len(all_fields),
                "field_completeness": field_stats,
                "recommendations": recommendations,
                "validation_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error validating data completeness: {e}")
            return {
                "completeness_score": 0.0,
                "total_records": 0,
                "field_completeness": {},
                "recommendations": [f"Validation error: {str(e)}"],
                "error": str(e),
            }

    # Helper methods
    def _is_valid_ip(self, value: str) -> bool:
        """Check if value is a valid IP address."""
        try:
            parts = value.strip().split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False

    def _suggest_ip_format(self, value: str) -> Optional[str]:
        """Suggest IP address format."""
        try:
            # Extract numbers from the value
            import re

            numbers = re.findall(r"\d+", str(value))
            if len(numbers) >= 4:
                # Take first 4 numbers and validate range
                octets = []
                for i in range(4):
                    octet = int(numbers[i])
                    octets.append(str(min(255, max(0, octet))))
                return ".".join(octets)
            return None
        except (ValueError, IndexError):
            return None

    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric."""
        try:
            float(str(value).replace(",", ""))
            return True
        except (ValueError, TypeError):
            return False

    def _extract_numeric(self, value: str) -> Optional[str]:
        """Extract numeric value from string."""
        try:
            import re

            # Extract first number from string
            numbers = re.findall(r"\d+(?:\.\d+)?", str(value))
            return numbers[0] if numbers else None
        except (ValueError, IndexError):
            return None

    def _suggest_environment(self, value: str) -> Optional[str]:
        """Suggest environment value."""
        value_lower = str(value).lower()

        if "prod" in value_lower:
            return "production"
        elif "dev" in value_lower:
            return "development"
        elif "test" in value_lower or "qa" in value_lower:
            return "test"
        elif "stage" in value_lower or "stag" in value_lower:
            return "staging"

        return None

    def _suggest_criticality(self, value: str) -> Optional[str]:
        """Suggest criticality value."""
        value_lower = str(value).lower()

        if any(word in value_lower for word in ["critical", "crit", "high"]):
            return "critical"
        elif any(word in value_lower for word in ["medium", "med", "moderate"]):
            return "medium"
        elif any(word in value_lower for word in ["low", "minor"]):
            return "low"

        return None
