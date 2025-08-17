"""
Schema Analysis Tool for Field Mapping Crew
Analyzes data structure and field semantics using AI intelligence
"""

import logging
from typing import Any, Dict, List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SchemaAnalysisInput(BaseModel):
    """Input for schema analysis"""

    data_sample: List[Dict[str, Any]] = Field(
        description="Sample data records for analysis"
    )
    metadata: Dict[str, Any] = Field(
        default={}, description="Additional metadata about the data source"
    )


class SchemaAnalysisTool(BaseTool):
    name: str = "schema_analysis_tool"
    description: str = (
        "Analyzes data structure and field semantics to understand field meanings and relationships"
    )
    args_schema: type[BaseModel] = SchemaAnalysisInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(
        self, data_sample: List[Dict[str, Any]], metadata: Dict[str, Any] = None
    ) -> str:
        """
        Analyze data schema and field semantics

        Returns detailed analysis of field meanings, data types, patterns, and relationships
        """
        try:
            if not data_sample:
                return "No data provided for schema analysis"

            # Analyze field structure
            fields_analysis = self._analyze_fields(data_sample)

            # Detect data patterns
            patterns = self._detect_patterns(data_sample)

            # Semantic understanding
            semantic_analysis = self._analyze_semantics(
                fields_analysis, patterns, metadata or {}
            )

            # Generate analysis report
            {
                "field_analysis": fields_analysis,
                "data_patterns": patterns,
                "semantic_insights": semantic_analysis,
                "recommendations": self._generate_recommendations(
                    fields_analysis, patterns
                ),
            }

            return (
                f"Schema Analysis Complete: Found {len(fields_analysis)} fields "
                f"with semantic insights: {semantic_analysis}"
            )

        except Exception as e:
            logger.error(f"Schema analysis failed: {e}")
            return f"Schema analysis failed: {str(e)}"

    def _analyze_fields(self, data_sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze individual fields for types, nullability, patterns"""
        field_analysis = {}

        if not data_sample:
            return field_analysis

        # Get all possible fields from sample
        all_fields = set()
        for record in data_sample[:10]:  # Analyze first 10 records
            all_fields.update(record.keys())

        for field in all_fields:
            values = [
                record.get(field) for record in data_sample[:10] if field in record
            ]
            non_null_values = [v for v in values if v is not None and v != ""]

            field_analysis[field] = {
                "data_type": self._infer_data_type(non_null_values),
                "null_count": len(values) - len(non_null_values),
                "sample_values": non_null_values[:3],
                "pattern_hints": self._detect_field_patterns(non_null_values),
            }

        return field_analysis

    def _infer_data_type(self, values: List[Any]) -> str:
        """Infer the primary data type of field values"""
        if not values:
            return "unknown"

        # Simple type inference
        first_value = values[0]
        if isinstance(first_value, bool):
            return "boolean"
        elif isinstance(first_value, int):
            return "integer"
        elif isinstance(first_value, float):
            return "float"
        elif isinstance(first_value, str):
            # Check for common patterns in strings
            if any(char.isdigit() for char in first_value):
                if "." in first_value:
                    return "ip_address_candidate"
                elif len(first_value) > 10:
                    return "text"
                else:
                    return "identifier_candidate"
            return "string"
        else:
            return "mixed"

    def _detect_field_patterns(self, values: List[Any]) -> List[str]:
        """Detect patterns in field values that indicate semantic meaning"""
        patterns = []

        if not values:
            return patterns

        # Convert all values to strings for pattern detection
        str_values = [str(v) for v in values if v is not None]

        for value in str_values[:3]:
            if self._looks_like_ip(value):
                patterns.append("ip_address")
            elif self._looks_like_hostname(value):
                patterns.append("hostname")
            elif self._looks_like_id(value):
                patterns.append("identifier")
            elif self._looks_like_version(value):
                patterns.append("version")

        return list(set(patterns))

    def _looks_like_ip(self, value: str) -> bool:
        """Check if value looks like an IP address"""
        parts = value.split(".")
        return len(parts) == 4 and all(
            part.isdigit() and 0 <= int(part) <= 255 for part in parts if part.isdigit()
        )

    def _looks_like_hostname(self, value: str) -> bool:
        """Check if value looks like a hostname"""
        return "." in value and not self._looks_like_ip(value)

    def _looks_like_id(self, value: str) -> bool:
        """Check if value looks like an identifier"""
        return (
            len(value) > 8
            and any(char.isdigit() for char in value)
            and any(char.isalpha() for char in value)
        )

    def _looks_like_version(self, value: str) -> bool:
        """Check if value looks like a version number"""
        return "." in value and any(char.isdigit() for char in value)

    def _detect_patterns(self, data_sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect overall data patterns and relationships"""
        return {
            "record_count": len(data_sample),
            "consistent_fields": self._find_consistent_fields(data_sample),
            "potential_keys": self._identify_potential_keys(data_sample),
        }

    def _find_consistent_fields(self, data_sample: List[Dict[str, Any]]) -> List[str]:
        """Find fields that appear consistently across records"""
        if not data_sample:
            return []

        field_counts = {}
        total_records = len(data_sample)

        for record in data_sample:
            for field in record.keys():
                field_counts[field] = field_counts.get(field, 0) + 1

        # Fields present in at least 80% of records
        consistent_fields = [
            field
            for field, count in field_counts.items()
            if count / total_records >= 0.8
        ]

        return consistent_fields

    def _identify_potential_keys(self, data_sample: List[Dict[str, Any]]) -> List[str]:
        """Identify fields that could be primary keys"""
        potential_keys = []

        for field in self._find_consistent_fields(data_sample):
            values = [record.get(field) for record in data_sample if field in record]
            unique_values = set(v for v in values if v is not None)

            # If all values are unique, it could be a key
            if len(unique_values) == len(values) and len(values) > 1:
                potential_keys.append(field)

        return potential_keys

    def _analyze_semantics(
        self,
        fields_analysis: Dict[str, Any],
        patterns: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate semantic understanding of the data structure"""
        return {
            "data_source_type": metadata.get("source_type", "unknown"),
            "likely_asset_fields": self._identify_asset_fields(fields_analysis),
            "business_context_fields": self._identify_business_fields(fields_analysis),
            "technical_fields": self._identify_technical_fields(fields_analysis),
            "relationship_hints": self._identify_relationships(fields_analysis),
        }

    def _identify_asset_fields(self, fields_analysis: Dict[str, Any]) -> List[str]:
        """Identify fields likely to contain asset information"""
        asset_keywords = [
            "name",
            "hostname",
            "server",
            "asset",
            "device",
            "computer",
            "id",
            "type",
        ]
        asset_fields = []

        for field, analysis in fields_analysis.items():
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in asset_keywords):
                asset_fields.append(field)
            elif "identifier" in analysis.get("pattern_hints", []):
                asset_fields.append(field)

        return asset_fields

    def _identify_business_fields(self, fields_analysis: Dict[str, Any]) -> List[str]:
        """Identify fields containing business context"""
        business_keywords = [
            "owner",
            "department",
            "cost",
            "business",
            "criticality",
            "environment",
            "tier",
        ]
        business_fields = []

        for field, analysis in fields_analysis.items():
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in business_keywords):
                business_fields.append(field)

        return business_fields

    def _identify_technical_fields(self, fields_analysis: Dict[str, Any]) -> List[str]:
        """Identify fields containing technical information"""
        technical_keywords = [
            "ip",
            "os",
            "cpu",
            "memory",
            "disk",
            "version",
            "platform",
        ]
        technical_fields = []

        for field, analysis in fields_analysis.items():
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in technical_keywords):
                technical_fields.append(field)
            elif "ip_address" in analysis.get("pattern_hints", []):
                technical_fields.append(field)

        return technical_fields

    def _identify_relationships(
        self, fields_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify potential relationships between fields"""
        relationships = {}

        # Look for foreign key patterns
        id_fields = [
            field
            for field, analysis in fields_analysis.items()
            if "id" in field.lower()
            or "identifier" in analysis.get("pattern_hints", [])
        ]

        if id_fields:
            relationships["potential_foreign_keys"] = id_fields

        return relationships

    def _generate_recommendations(
        self, fields_analysis: Dict[str, Any], patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for field mapping"""
        recommendations = []

        if patterns.get("potential_keys"):
            recommendations.append(
                f"Consider using {patterns['potential_keys'][0]} as primary identifier"
            )

        if len(fields_analysis) > 20:
            recommendations.append(
                "Large number of fields detected - consider grouping by domain"
            )

        if patterns.get("record_count", 0) < 5:
            recommendations.append(
                "Limited sample size - consider analyzing more records for better accuracy"
            )

        return recommendations
