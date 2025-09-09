"""
Data Extractor for Field Mapping Generator

Handles extraction of data from validation results with multiple fallback strategies.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

from .base import FieldMappingGeneratorBase

logger = logging.getLogger(__name__)


class FieldMappingDataExtractor(FieldMappingGeneratorBase):
    """Handles extraction of field mapping data from validation results"""

    def prepare_field_mapping_input_data(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare input data for field mapping generation with bug fixes"""
        try:
            # Extract relevant data from validation result
            data_source = data_validation_agent_result.get("data_source", {})
            validation_errors = data_validation_agent_result.get(
                "validation_errors", []
            )
            field_analysis = data_validation_agent_result.get("field_analysis", {})

            # BUG FIX: Fallback to validated_data when field_analysis is empty
            # Post-modularization, the actual data is in validated_data field
            if not field_analysis and "validated_data" in data_validation_agent_result:
                field_analysis = self._extract_field_analysis_from_validated_data(
                    data_validation_agent_result["validated_data"]
                )

            # Additional fallback: try to get detected columns from flow state metadata
            if not field_analysis and hasattr(self.flow, "state") and self.flow.state:
                detected_columns = getattr(self.flow.state, "metadata", {}).get(
                    "detected_columns", []
                )
                if detected_columns:
                    field_analysis = {
                        col: {"field_name": col, "source": "state_metadata"}
                        for col in detected_columns
                    }
                    self.logger.info(
                        f"🔄 Generated field analysis from state metadata: {detected_columns}"
                    )

            # BUG FIX: Try to extract data_source from nested result structure if empty
            if not data_source:
                data_source = self._extract_data_source_from_result(
                    data_validation_agent_result
                )

            # Build comprehensive input for field mapping
            input_data = {
                "data_source": data_source,
                "validation_errors": validation_errors,
                "field_analysis": field_analysis,
                "validated_data": data_validation_agent_result.get(
                    "validated_data", []
                ),
                "flow_context": {
                    "flow_id": getattr(self.flow, "_flow_id", None),
                    "client_account_id": getattr(
                        self.flow.state, "client_account_id", None
                    ),
                    "data_import_id": getattr(self.flow.state, "data_import_id", None),
                },
                "timestamp": self._get_current_timestamp(),
            }

            self.logger.debug(
                f"📊 Prepared field mapping input data with {len(field_analysis)} field analyses"
            )
            return input_data

        except Exception as e:
            self.logger.error(f"❌ Failed to prepare field mapping input data: {e}")
            return {}

    def _extract_field_analysis_from_validated_data(
        self, validated_data: Any
    ) -> Dict[str, Any]:
        """Extract field analysis from validated data"""
        field_analysis = {}

        try:
            self.logger.info("🔄 Using validated_data fallback for field mapping")

            if (
                validated_data
                and isinstance(validated_data, list)
                and len(validated_data) > 0
            ):
                # Generate field analysis from validated data
                sample_record = validated_data[0]
                if isinstance(sample_record, dict):
                    for field_name, field_value in sample_record.items():
                        field_analysis[field_name] = {
                            "field_name": field_name,
                            "sample_value": field_value,
                            "data_type": type(field_value).__name__,
                            "source": "validated_data_extraction",
                        }
                    self.logger.info(
                        f"✅ Generated field analysis for {len(field_analysis)} fields from validated_data"
                    )
        except Exception as e:
            self.logger.error(
                f"❌ Failed to extract field analysis from validated_data: {e}"
            )

        return field_analysis

    def _extract_data_source_from_result(
        self, data_validation_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract data source from nested result structures"""
        data_source = {}

        try:
            # Check if data source info is in nested result structure
            nested_result = data_validation_agent_result.get("result", {})
            if nested_result and isinstance(nested_result, dict):
                data_source = nested_result.get("data_source", {})
                if data_source:
                    self.logger.info(
                        "🔄 Extracted data_source from nested result structure"
                    )
                    return data_source

            # Also check for data source info in file_analysis or detailed_report
            file_analysis = data_validation_agent_result.get("file_analysis", {})
            if file_analysis:
                data_source = {
                    "detected_type": file_analysis.get("detected_type", "unknown"),
                    "confidence": file_analysis.get("confidence", 0.0),
                    "recommended_agent": file_analysis.get(
                        "recommended_agent", "CMDB_Data_Analyst_Agent"
                    ),
                    "source": "file_analysis_extraction",
                }
                self.logger.info("🔄 Generated data_source from file_analysis")
        except Exception as e:
            self.logger.error(f"❌ Failed to extract data_source from result: {e}")

        return data_source
