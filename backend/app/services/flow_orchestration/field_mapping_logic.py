"""
Field Mapping Logic Module

This module contains field mapping methods extracted from execution_engine_crew_discovery.py
to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldMappingLogic:
    """Handles field mapping logic for discovery flows"""

    def __init__(self):
        """Initialize the field mapping logic handler"""
        pass

    async def execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase with actual field mapping logic"""
        logger.info("🗺️ Executing discovery field mapping")

        try:
            # Get raw data from phase input
            raw_data = phase_input.get("raw_data", [])
            if not raw_data:
                logger.warning("⚠️ No raw data available for field mapping")
                return {
                    "phase": "field_mapping",
                    "status": "completed",
                    "mappings": {},
                    "agent": "field_mapping_agent",
                }

            # Extract field names from first record
            sample_record = (
                raw_data[0] if isinstance(raw_data, list) and raw_data else raw_data
            )
            if isinstance(sample_record, dict):
                source_fields = list(sample_record.keys())
            else:
                logger.warning("⚠️ Raw data is not in expected dictionary format")
                return {
                    "phase": "field_mapping",
                    "status": "completed",
                    "mappings": {},
                    "agent": "field_mapping_agent",
                }

            logger.info(
                f"📊 Creating field mappings for {len(source_fields)} source fields"
            )

            # Create intelligent field mappings based on field names
            field_mappings = await self.generate_field_mappings(source_fields, raw_data)

            # TODO: Persist field mappings to database (placeholder for field_mappings table)
            logger.info(f"✅ Generated {len(field_mappings)} field mappings")

            return {
                "phase": "field_mapping",
                "status": "completed",
                "mappings": field_mappings,
                "field_count": len(source_fields),
                "mapped_count": len(field_mappings),
                "agent": "field_mapping_agent",
            }

        except Exception as e:
            logger.error(f"❌ Field mapping execution failed: {e}")
            return {
                "phase": "field_mapping",
                "status": "error",
                "error": str(e),
                "mappings": {},
                "agent": "field_mapping_agent",
            }

    async def generate_field_mappings(
        self, source_fields: List[str], raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate intelligent field mappings based on source field analysis"""
        mappings = {}

        # Standard migration attribute mapping patterns
        field_patterns = {
            # Server/Asset identification
            "server_name": {
                "standard_attribute": "asset_name",
                "confidence": 0.95,
                "critical": True,
            },
            "hostname": {
                "standard_attribute": "asset_name",
                "confidence": 0.95,
                "critical": True,
            },
            "name": {
                "standard_attribute": "asset_name",
                "confidence": 0.85,
                "critical": True,
            },
            "asset_name": {
                "standard_attribute": "asset_name",
                "confidence": 1.0,
                "critical": True,
            },
            # Environment
            "environment": {
                "standard_attribute": "environment",
                "confidence": 1.0,
                "critical": True,
            },
            "env": {
                "standard_attribute": "environment",
                "confidence": 0.9,
                "critical": True,
            },
            # Operating System
            "os_type": {
                "standard_attribute": "operating_system",
                "confidence": 0.95,
                "critical": True,
            },
            "os": {
                "standard_attribute": "operating_system",
                "confidence": 0.9,
                "critical": True,
            },
            "operating_system": {
                "standard_attribute": "operating_system",
                "confidence": 1.0,
                "critical": True,
            },
            # Hardware specifications
            "cpu_cores": {
                "standard_attribute": "cpu_cores",
                "confidence": 1.0,
                "critical": False,
            },
            "cores": {
                "standard_attribute": "cpu_cores",
                "confidence": 0.9,
                "critical": False,
            },
            "vcpus": {
                "standard_attribute": "cpu_cores",
                "confidence": 0.9,
                "critical": False,
            },
            "memory_gb": {
                "standard_attribute": "memory_gb",
                "confidence": 1.0,
                "critical": False,
            },
            "memory": {
                "standard_attribute": "memory_gb",
                "confidence": 0.85,
                "critical": False,
            },
            "ram": {
                "standard_attribute": "memory_gb",
                "confidence": 0.9,
                "critical": False,
            },
            "ram_gb": {
                "standard_attribute": "memory_gb",
                "confidence": 0.95,
                "critical": False,
            },
            "disk_gb": {
                "standard_attribute": "storage_gb",
                "confidence": 0.95,
                "critical": False,
            },
            "storage": {
                "standard_attribute": "storage_gb",
                "confidence": 0.85,
                "critical": False,
            },
            "storage_gb": {
                "standard_attribute": "storage_gb",
                "confidence": 1.0,
                "critical": False,
            },
            # Status and ownership
            "status": {
                "standard_attribute": "status",
                "confidence": 1.0,
                "critical": False,
            },
            "state": {
                "standard_attribute": "status",
                "confidence": 0.85,
                "critical": False,
            },
            "owner": {
                "standard_attribute": "owner",
                "confidence": 1.0,
                "critical": False,
            },
            "responsible_party": {
                "standard_attribute": "owner",
                "confidence": 0.9,
                "critical": False,
            },
            # Application context
            "application": {
                "standard_attribute": "application",
                "confidence": 1.0,
                "critical": True,
            },
            "app": {
                "standard_attribute": "application",
                "confidence": 0.9,
                "critical": True,
            },
            "service": {
                "standard_attribute": "application",
                "confidence": 0.8,
                "critical": True,
            },
        }

        for source_field in source_fields:
            source_field_lower = source_field.lower()

            # Direct pattern match
            if source_field_lower in field_patterns:
                pattern = field_patterns[source_field_lower]
                mappings[source_field] = {
                    "source_field": source_field,
                    "target_attribute": pattern["standard_attribute"],
                    "confidence_score": pattern["confidence"],
                    "is_critical": pattern["critical"],
                    "mapping_type": "direct_match",
                    "data_type": await self.infer_data_type(source_field, raw_data),
                }
            else:
                # Fuzzy matching for partial matches
                best_match = None
                best_confidence = 0.0

                for pattern_key, pattern_info in field_patterns.items():
                    if (
                        pattern_key in source_field_lower
                        or source_field_lower in pattern_key
                    ):
                        # Calculate confidence based on similarity
                        similarity = min(
                            len(pattern_key), len(source_field_lower)
                        ) / max(len(pattern_key), len(source_field_lower))
                        confidence = (
                            pattern_info["confidence"] * similarity * 0.7
                        )  # Reduce confidence for fuzzy matches

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = pattern_info

                if (
                    best_match and best_confidence > 0.5
                ):  # Only include if confidence > 50%
                    mappings[source_field] = {
                        "source_field": source_field,
                        "target_attribute": best_match["standard_attribute"],
                        "confidence_score": best_confidence,
                        "is_critical": best_match["critical"],
                        "mapping_type": "fuzzy_match",
                        "data_type": await self.infer_data_type(source_field, raw_data),
                    }
                else:
                    # Unmapped field
                    mappings[source_field] = {
                        "source_field": source_field,
                        "target_attribute": "unmapped",
                        "confidence_score": 0.0,
                        "is_critical": False,
                        "mapping_type": "unmapped",
                        "data_type": await self.infer_data_type(source_field, raw_data),
                    }

        return mappings

    async def infer_data_type(
        self, field_name: str, raw_data: List[Dict[str, Any]]
    ) -> str:
        """Infer data type from field name and sample data"""
        # Get sample values for this field
        sample_values = []
        for record in raw_data[:5]:  # Check first 5 records
            if isinstance(record, dict) and field_name in record:
                value = record[field_name]
                if value is not None:
                    sample_values.append(value)

        if not sample_values:
            return "unknown"

        # Analyze sample values
        sample_value = sample_values[0]

        # Check if it's numeric
        try:
            float(sample_value)
            if "." in str(sample_value):
                return "decimal"
            else:
                return "integer"
        except (ValueError, TypeError):
            pass

        # Check field name patterns for data type hints
        field_lower = field_name.lower()
        if any(
            keyword in field_lower for keyword in ["date", "time", "created", "updated"]
        ):
            return "datetime"
        elif any(keyword in field_lower for keyword in ["email", "mail"]):
            return "email"
        elif any(keyword in field_lower for keyword in ["url", "link"]):
            return "url"
        elif any(keyword in field_lower for keyword in ["ip", "address"]):
            return "ip_address"
        else:
            return "string"
