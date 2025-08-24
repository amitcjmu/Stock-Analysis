"""
Field Mapping Validation
Validation logic for field mappings and data quality checks.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any

# from .exceptions import MappingValidationError  # Commented out - currently unused

logger = logging.getLogger(__name__)


class BaseValidator:
    """Base class for validators"""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data and return result with any error messages

        Returns:
            Tuple of (is_valid, error_messages)
        """
        raise NotImplementedError


class MappingValidator(BaseValidator):
    """Validates field mappings for correctness and completeness"""

    def __init__(self):
        self.malformed_values = {"{", "}", "[", "]", "", "null", "undefined", "None"}
        self.required_fields = {"name", "hostname"}
        self.recommended_fields = {"asset_type", "environment", "ip_address"}

    def validate_mappings(
        self, mappings: Dict[str, str], confidence_scores: Dict[str, float]
    ) -> Tuple[Dict[str, str], Dict[str, float], List[str]]:
        """
        Validate and clean field mappings

        Returns:
            Tuple of (cleaned_mappings, cleaned_confidence, validation_errors)
        """
        cleaned_mappings = {}
        cleaned_confidence = {}
        validation_errors = []

        for source, target in mappings.items():
            # Check for malformed mappings
            if self._is_malformed_mapping(source, target):
                validation_errors.append(
                    f"Skipping malformed mapping: {source} -> '{target}'"
                )
                continue

            # Check for valid target
            if not self._is_valid_target(target):
                validation_errors.append(f"Invalid target field: {source} -> {target}")
                continue

            # Check for valid source
            if not self._is_valid_source(source):
                validation_errors.append(f"Invalid source field: '{source}'")
                continue

            cleaned_mappings[source] = target
            cleaned_confidence[source] = confidence_scores.get(source, 0.7)

        # Check for required fields
        mapped_targets = set(cleaned_mappings.values())
        missing_required = self.required_fields - mapped_targets
        if missing_required:
            validation_errors.append(
                f"Missing required field mappings: {', '.join(missing_required)}"
            )

        # Warn about missing recommended fields
        missing_recommended = self.recommended_fields - mapped_targets
        if missing_recommended:
            validation_errors.append(
                f"Missing recommended field mappings: {', '.join(missing_recommended)}"
            )

        return cleaned_mappings, cleaned_confidence, validation_errors

    def _is_malformed_mapping(self, source: str, target: str) -> bool:
        """Check if mapping is malformed"""
        if not isinstance(target, str):
            return True

        target_clean = target.strip()
        if target_clean in self.malformed_values:
            return True

        if len(target_clean) < 2:
            return True

        return False

    def _is_valid_target(self, target: str) -> bool:
        """Check if target field is valid"""
        if not target or not isinstance(target, str):
            return False

        # Basic validation - can be extended
        target_clean = target.strip()
        return len(target_clean) >= 2 and target_clean.isalnum() or "_" in target_clean

    def _is_valid_source(self, source: str) -> bool:
        """Check if source field is valid"""
        if not source or not isinstance(source, str):
            return False

        # Basic validation - can be extended
        source_clean = source.strip()
        return len(source_clean) >= 1 and not source_clean.startswith("_")


class ConfidenceValidator:
    """Validates confidence scores and calculates quality metrics"""

    def __init__(self):
        self.low_confidence_threshold = 0.6
        self.high_confidence_threshold = 0.8

    def validate_confidence_scores(
        self, confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate confidence scores and calculate metrics

        Returns:
            Dict with validation results and metrics
        """
        if not confidence_scores:
            return {
                "valid": False,
                "error": "No confidence scores provided",
                "metrics": {},
            }

        # Validate individual scores
        invalid_scores = []
        for field, score in confidence_scores.items():
            if not isinstance(score, (int, float)):
                invalid_scores.append(f"{field}: not numeric")
            elif not (0.0 <= score <= 1.0):
                invalid_scores.append(f"{field}: {score} not in range [0,1]")

        if invalid_scores:
            return {
                "valid": False,
                "error": f"Invalid confidence scores: {'; '.join(invalid_scores)}",
                "metrics": {},
            }

        # Calculate metrics
        scores = list(confidence_scores.values())
        metrics = {
            "average_confidence": sum(scores) / len(scores),
            "min_confidence": min(scores),
            "max_confidence": max(scores),
            "low_confidence_count": sum(
                1 for s in scores if s < self.low_confidence_threshold
            ),
            "high_confidence_count": sum(
                1 for s in scores if s >= self.high_confidence_threshold
            ),
            "total_fields": len(scores),
        }

        metrics["low_confidence_percentage"] = (
            metrics["low_confidence_count"] / metrics["total_fields"] * 100
        )
        metrics["high_confidence_percentage"] = (
            metrics["high_confidence_count"] / metrics["total_fields"] * 100
        )

        return {
            "valid": True,
            "metrics": metrics,
            "warnings": self._generate_confidence_warnings(metrics),
        }

    def _generate_confidence_warnings(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate warnings based on confidence metrics"""
        warnings = []

        if metrics["average_confidence"] < self.low_confidence_threshold:
            warnings.append(
                f"Low average confidence: {metrics['average_confidence']:.2f}"
            )

        if metrics["low_confidence_percentage"] > 50:
            warnings.append(
                f"High percentage of low-confidence mappings: "
                f"{metrics['low_confidence_percentage']:.1f}%"
            )

        if metrics["min_confidence"] < 0.3:
            warnings.append(
                f"Very low minimum confidence: {metrics['min_confidence']:.2f}"
            )

        return warnings


class DataQualityValidator:
    """Validates data quality and completeness"""

    def __init__(self):
        self.min_records_threshold = 1
        self.min_fields_threshold = 3
        self.completeness_threshold = 0.5  # 50% of records should have the field

    def validate_raw_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate raw data quality

        Returns:
            Dict with validation results and quality metrics
        """
        if not raw_data:
            return {
                "valid": False,
                "error": "No raw data provided",
                "quality_score": 0.0,
            }

        if len(raw_data) < self.min_records_threshold:
            return {
                "valid": False,
                "error": f"Insufficient records: {len(raw_data)} < {self.min_records_threshold}",
                "quality_score": 0.0,
            }

        # Analyze field coverage
        field_stats = self._analyze_field_coverage(raw_data)
        quality_metrics = self._calculate_quality_metrics(raw_data, field_stats)

        # Determine if data is valid
        is_valid = (
            len(field_stats) >= self.min_fields_threshold
            and quality_metrics["overall_completeness"] >= self.completeness_threshold
        )

        return {
            "valid": is_valid,
            "field_stats": field_stats,
            "quality_metrics": quality_metrics,
            "quality_score": quality_metrics["overall_quality_score"],
            "warnings": self._generate_quality_warnings(quality_metrics),
        }

    def _analyze_field_coverage(
        self, raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze field coverage across records"""
        field_stats = {}
        total_records = len(raw_data)

        # Get all unique fields
        all_fields = set()
        for record in raw_data:
            all_fields.update(record.keys())

        # Analyze each field
        for field in all_fields:
            non_empty_count = 0
            data_types = set()

            for record in raw_data:
                value = record.get(field)
                if value is not None and str(value).strip():
                    non_empty_count += 1
                    data_types.add(type(value).__name__)

            field_stats[field] = {
                "total_count": total_records,
                "non_empty_count": non_empty_count,
                "completeness": non_empty_count / total_records,
                "data_types": list(data_types),
            }

        return field_stats

    def _calculate_quality_metrics(
        self, raw_data: List[Dict[str, Any]], field_stats: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall data quality metrics"""
        total_fields = len(field_stats)
        if total_fields == 0:
            return {"overall_quality_score": 0.0, "overall_completeness": 0.0}

        # Calculate average completeness
        completeness_scores = [stats["completeness"] for stats in field_stats.values()]
        overall_completeness = sum(completeness_scores) / len(completeness_scores)

        # Calculate fields with good completeness (>= threshold)
        complete_fields = sum(
            1
            for stats in field_stats.values()
            if stats["completeness"] >= self.completeness_threshold
        )
        completeness_ratio = complete_fields / total_fields

        # Calculate consistency (fields with single data type)
        consistent_fields = sum(
            1 for stats in field_stats.values() if len(stats["data_types"]) <= 1
        )
        consistency_ratio = consistent_fields / total_fields

        # Overall quality score (weighted combination)
        overall_quality_score = (
            overall_completeness * 0.5  # 50% weight on completeness
            + completeness_ratio * 0.3  # 30% weight on field coverage
            + consistency_ratio * 0.2  # 20% weight on consistency
        )

        return {
            "overall_completeness": overall_completeness,
            "completeness_ratio": completeness_ratio,
            "consistency_ratio": consistency_ratio,
            "overall_quality_score": overall_quality_score,
            "total_fields": total_fields,
            "complete_fields": complete_fields,
            "consistent_fields": consistent_fields,
            "total_records": len(raw_data),
        }

    def _generate_quality_warnings(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate warnings based on data quality metrics"""
        warnings = []

        if metrics["overall_completeness"] < self.completeness_threshold:
            warnings.append(
                f"Low data completeness: {metrics['overall_completeness']:.1%}"
            )

        if metrics["completeness_ratio"] < 0.7:
            warnings.append(
                f"Many fields have poor coverage: "
                f"{metrics['complete_fields']}/{metrics['total_fields']} fields adequate"
            )

        if metrics["consistency_ratio"] < 0.8:
            warnings.append("Data type inconsistencies detected in multiple fields")

        if metrics["overall_quality_score"] < 0.7:
            warnings.append(
                f"Overall data quality is low: {metrics['overall_quality_score']:.1%}"
            )

        return warnings


class CompositeValidator:
    """Composite validator that combines all validation strategies"""

    def __init__(self):
        self.mapping_validator = MappingValidator()
        self.confidence_validator = ConfidenceValidator()
        self.data_quality_validator = DataQualityValidator()

    def validate_mapping_results(
        self,
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
        raw_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of mapping results

        Returns:
            Dict with all validation results
        """
        results = {"overall_valid": True, "errors": [], "warnings": []}

        # Validate mappings
        try:
            cleaned_mappings, cleaned_confidence, mapping_errors = (
                self.mapping_validator.validate_mappings(mappings, confidence_scores)
            )

            results["cleaned_mappings"] = cleaned_mappings
            results["cleaned_confidence"] = cleaned_confidence
            results["mapping_validation"] = {
                "valid": len(mapping_errors) == 0,
                "errors": mapping_errors,
            }

            if mapping_errors:
                results["errors"].extend(mapping_errors)
                if not cleaned_mappings:
                    results["overall_valid"] = False

        except Exception as e:
            results["overall_valid"] = False
            results["errors"].append(f"Mapping validation failed: {e}")
            results["cleaned_mappings"] = mappings
            results["cleaned_confidence"] = confidence_scores

        # Validate confidence scores
        try:
            confidence_validation = (
                self.confidence_validator.validate_confidence_scores(
                    results["cleaned_confidence"]
                )
            )
            results["confidence_validation"] = confidence_validation

            if not confidence_validation["valid"]:
                results["overall_valid"] = False
                results["errors"].append(confidence_validation["error"])
            else:
                results["warnings"].extend(confidence_validation.get("warnings", []))

        except Exception as e:
            results["errors"].append(f"Confidence validation failed: {e}")

        # Validate raw data quality if provided
        if raw_data:
            try:
                data_quality = self.data_quality_validator.validate_raw_data(raw_data)
                results["data_quality_validation"] = data_quality

                if not data_quality["valid"]:
                    results["warnings"].append(
                        f"Data quality issue: {data_quality.get('error', 'Unknown')}"
                    )
                else:
                    results["warnings"].extend(data_quality.get("warnings", []))

            except Exception as e:
                results["warnings"].append(f"Data quality validation failed: {e}")

        return results

    async def validate_mappings(
        self, parsed_mappings: Dict[str, Any], validation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate parsed mappings with context information.
        This method provides compatibility with the base executor interface.
        """
        try:
            # Extract mappings from parsed structure
            if isinstance(parsed_mappings.get("mappings"), list):
                # Convert list format to dict format
                mappings = {}
                confidence_scores = {}
                for mapping in parsed_mappings["mappings"]:
                    if isinstance(mapping, dict):
                        source = mapping.get("source_field", "")
                        target = mapping.get("target_field", "")
                        confidence = mapping.get("confidence", 0.7)
                        if source and target:
                            mappings[source] = target
                            confidence_scores[source] = confidence
            else:
                mappings = parsed_mappings.get("mappings", {})
                confidence_scores = parsed_mappings.get("confidence_scores", {})

            # Use the existing validation method
            validation_results = self.validate_mapping_results(
                mappings, confidence_scores, validation_context.get("sample_data")
            )

            # Enhance with context information
            validation_results["validation_context"] = validation_context
            validation_results["error_count"] = len(
                validation_results.get("errors", [])
            )
            validation_results["warning_count"] = len(
                validation_results.get("warnings", [])
            )

            return validation_results

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "overall_valid": False,
                "error_count": 1,
                "errors": [f"Validation error: {e}"],
                "warnings": [],
                "cleaned_mappings": {},
                "cleaned_confidence": {},
                "validation_context": validation_context,
            }


# Factory function
def create_validator() -> CompositeValidator:
    """Create a composite validator with all validation strategies"""
    return CompositeValidator()
