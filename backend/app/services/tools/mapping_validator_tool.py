"""
Mapping Validator Tool for validating field mappings
"""

import json
import logging
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

logger = logging.getLogger(__name__)


class MappingValidatorTool(AsyncBaseDiscoveryTool):
    """Validates field mappings for data type compatibility and quality"""

    name: str = "mapping_validator"
    description: str = "Validate field mappings for compatibility and data integrity"

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="mapping_validator",
            description="Comprehensive mapping validation and quality assessment",
            tool_class=cls,
            categories=["validation", "mapping", "data_quality"],
            required_params=["mappings"],
            optional_params=["source_schema", "target_schema", "sample_data"],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self,
        mappings: List[Dict[str, Any]],
        source_schema: Dict[str, str] = None,
        target_schema: Dict[str, str] = None,
        sample_data: List[Dict[str, Any]] = None,
    ) -> str:
        """
        Validate field mappings for quality and compatibility.

        Args:
            mappings: List of field mappings to validate
            source_schema: Schema information for source fields
            target_schema: Schema information for target fields
            sample_data: Sample data for validation testing

        Returns:
            JSON string with validation results
        """
        try:
            validation_results = {
                "status": "success",
                "total_mappings": len(mappings),
                "valid_mappings": 0,
                "issues": [],
                "warnings": [],
                "recommendations": [],
                "mapping_quality_score": 0.0,
                "details": [],
            }

            # Validate each mapping
            for i, mapping in enumerate(mappings):
                mapping_validation = await self._validate_single_mapping(
                    mapping, source_schema, target_schema, sample_data
                )

                validation_results["details"].append(mapping_validation)

                if mapping_validation["valid"]:
                    validation_results["valid_mappings"] += 1

                # Collect issues and warnings
                validation_results["issues"].extend(
                    mapping_validation.get("issues", [])
                )
                validation_results["warnings"].extend(
                    mapping_validation.get("warnings", [])
                )

            # Check for duplicate target mappings
            self._check_duplicate_targets(mappings, validation_results)

            # Check for missing critical fields
            self._check_missing_critical_fields(mappings, validation_results)

            # Calculate overall quality score
            validation_results["mapping_quality_score"] = self._calculate_quality_score(
                validation_results
            )

            # Generate recommendations
            validation_results["recommendations"] = self._generate_recommendations(
                validation_results
            )

            return json.dumps(validation_results, indent=2)

        except Exception as e:
            logger.error(f"Mapping validation failed: {e}")
            return json.dumps({"status": "error", "error": str(e), "valid_mappings": 0})

    async def _validate_single_mapping(
        self,
        mapping: Dict[str, Any],
        source_schema: Dict[str, str] = None,
        target_schema: Dict[str, str] = None,
        sample_data: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate a single field mapping"""
        result = {
            "source_field": mapping.get("source_field"),
            "target_field": mapping.get("target_field"),
            "valid": True,
            "issues": [],
            "warnings": [],
            "confidence": mapping.get("confidence", 0.0),
            "data_type_compatible": True,
            "data_loss_risk": "low",
        }

        source_field = mapping.get("source_field")
        target_field = mapping.get("target_field")

        # Basic validation
        if not source_field or not target_field:
            result["valid"] = False
            result["issues"].append("Missing source or target field")
            return result

        # Confidence validation
        confidence = mapping.get("confidence", 0.0)
        if confidence < 0.3:
            result["warnings"].append(f"Low confidence mapping: {confidence:.2f}")
        elif confidence < 0.5:
            result["warnings"].append(
                f"Medium confidence mapping: {confidence:.2f} - review recommended"
            )

        # Data type compatibility
        if source_schema and target_schema:
            source_type = source_schema.get(source_field, "unknown")
            target_type = target_schema.get(target_field, "unknown")

            compatible, risk = self._check_type_compatibility(source_type, target_type)
            result["data_type_compatible"] = compatible
            result["data_loss_risk"] = risk

            if not compatible:
                result["issues"].append(
                    f"Data type incompatibility: {source_type} -> {target_type}"
                )
            elif risk == "high":
                result["warnings"].append(
                    f"High data loss risk: {source_type} -> {target_type}"
                )

        # Sample data validation
        if sample_data:
            data_issues = self._validate_with_sample_data(
                source_field, target_field, sample_data
            )
            result["warnings"].extend(data_issues)

        # Field name pattern validation
        name_warnings = self._validate_field_names(source_field, target_field)
        result["warnings"].extend(name_warnings)

        return result

    def _check_type_compatibility(
        self, source_type: str, target_type: str
    ) -> tuple[bool, str]:
        """Check if source and target data types are compatible"""
        # Type compatibility matrix
        compatible_types = {
            "string": ["string", "text", "varchar", "char"],
            "integer": ["integer", "int", "number", "float", "decimal"],
            "float": ["float", "number", "decimal", "integer", "int"],
            "boolean": ["boolean", "bool", "int"],
            "date": ["date", "datetime", "timestamp", "string"],
            "datetime": ["datetime", "timestamp", "date", "string"],
            "json": ["json", "text", "string"],
            "array": ["array", "json", "string"],
        }

        source_lower = source_type.lower()
        target_lower = target_type.lower()

        # Direct match
        if source_lower == target_lower:
            return True, "low"

        # Check compatibility matrix
        for base_type, compatible in compatible_types.items():
            if source_lower in compatible and target_lower in compatible:
                # Assess data loss risk
                if source_lower in ["float", "decimal"] and target_lower in [
                    "int",
                    "integer",
                ]:
                    return True, "high"
                elif source_lower == "datetime" and target_lower == "date":
                    return True, "medium"
                elif source_lower in ["json", "array"] and target_lower == "string":
                    return True, "medium"
                else:
                    return True, "low"

        return False, "high"

    def _validate_with_sample_data(
        self, source_field: str, target_field: str, sample_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Validate mapping using sample data"""
        warnings = []

        # Check if source field exists in sample data
        has_source_data = any(source_field in record for record in sample_data)
        if not has_source_data:
            warnings.append(f"Source field '{source_field}' not found in sample data")
            return warnings

        # Analyze data patterns
        values = []
        null_count = 0

        for record in sample_data:
            value = record.get(source_field)
            if value is None:
                null_count += 1
            else:
                values.append(value)

        # Check null percentage
        null_percentage = (null_count / len(sample_data)) * 100
        if null_percentage > 50:
            warnings.append(
                f"High null percentage in source field: {null_percentage:.1f}%"
            )
        elif null_percentage > 20:
            warnings.append(
                f"Moderate null percentage in source field: {null_percentage:.1f}%"
            )

        # Check data uniformity
        if values:
            unique_values = len(set(str(v) for v in values))
            if unique_values == 1:
                warnings.append("Source field has only one unique value")
            elif unique_values / len(values) < 0.1:
                warnings.append("Source field has very low data diversity")

        return warnings

    def _validate_field_names(self, source_field: str, target_field: str) -> List[str]:
        """Validate field name patterns"""
        warnings = []

        # Check for potentially problematic mappings
        source_lower = source_field.lower()
        target_lower = target_field.lower()

        # ID field mappings
        if "id" in source_lower and "name" in target_lower:
            warnings.append("Mapping ID field to name field - verify this is correct")

        # Date/time field mappings
        if any(term in source_lower for term in ["date", "time", "created", "updated"]):
            if not any(
                term in target_lower for term in ["date", "time", "created", "updated"]
            ):
                warnings.append("Mapping temporal field to non-temporal field")

        # Critical field mappings
        critical_sources = ["hostname", "server", "ip", "asset"]
        critical_targets = ["asset_name", "asset_id", "ip_address"]

        if any(term in source_lower for term in critical_sources):
            if not any(term in target_lower for term in critical_targets):
                warnings.append(
                    "Critical asset field may not be mapped to appropriate target"
                )

        return warnings

    def _check_duplicate_targets(
        self, mappings: List[Dict[str, Any]], results: Dict[str, Any]
    ):
        """Check for duplicate target field mappings"""
        target_fields = {}

        for mapping in mappings:
            target = mapping.get("target_field")
            if target:
                if target in target_fields:
                    target_fields[target].append(mapping.get("source_field"))
                else:
                    target_fields[target] = [mapping.get("source_field")]

        for target, sources in target_fields.items():
            if len(sources) > 1:
                results["issues"].append(
                    f"Duplicate target mapping: '{target}' mapped from {sources}"
                )

    def _check_missing_critical_fields(
        self, mappings: List[Dict[str, Any]], results: Dict[str, Any]
    ):
        """Check for missing critical field mappings"""
        critical_fields = ["asset_name", "asset_type", "asset_id"]
        mapped_targets = {m.get("target_field") for m in mappings}

        missing_critical = [
            field for field in critical_fields if field not in mapped_targets
        ]

        if missing_critical:
            results["warnings"].append(
                f"Missing mappings for critical fields: {missing_critical}"
            )

    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall mapping quality score"""
        total_mappings = results["total_mappings"]
        if total_mappings == 0:
            return 0.0

        valid_mappings = results["valid_mappings"]
        issues_count = len(results["issues"])
        warnings_count = len(results["warnings"])

        # Base score from valid mappings
        base_score = (valid_mappings / total_mappings) * 100

        # Deduct for issues and warnings
        issue_penalty = min(issues_count * 10, 50)  # Max 50% penalty for issues
        warning_penalty = min(warnings_count * 5, 25)  # Max 25% penalty for warnings

        quality_score = max(0, base_score - issue_penalty - warning_penalty)

        return round(quality_score, 1)

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Quality-based recommendations
        quality_score = results["mapping_quality_score"]
        if quality_score < 60:
            recommendations.append(
                "Consider reviewing all mappings - quality score is low"
            )
        elif quality_score < 80:
            recommendations.append(
                "Review mappings with warnings - moderate quality score"
            )

        # Issue-based recommendations
        if results["issues"]:
            recommendations.append("Resolve all mapping issues before proceeding")

        # Warning-based recommendations
        if len(results["warnings"]) > results["total_mappings"] * 0.5:
            recommendations.append(
                "High number of warnings - consider additional field analysis"
            )

        # Validation rate recommendations
        valid_rate = (
            results["valid_mappings"] / results["total_mappings"]
            if results["total_mappings"] > 0
            else 0
        )
        if valid_rate < 0.8:
            recommendations.append("Low validation rate - verify source data quality")

        return recommendations
