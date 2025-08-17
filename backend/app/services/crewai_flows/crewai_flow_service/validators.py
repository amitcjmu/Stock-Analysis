"""
Validation module for CrewAI Flow Service.

This module contains validation logic for input/output data,
flow states, and data quality assessments.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FlowValidationMixin:
    """
    Mixin class providing validation methods for the CrewAI Flow Service.
    """

    def _get_standard_field_mappings(self) -> Dict[str, List[str]]:
        """
        Get standard CMDB field mappings.

        Returns:
            Dictionary mapping standard fields to possible source field patterns
        """
        return {
            "hostname": ["hostname", "host_name", "server_name", "name", "system_name"],
            "ip_address": ["ip_address", "ip", "ipaddress", "primary_ip", "mgmt_ip"],
            "operating_system": ["os", "operating_system", "platform", "os_name"],
            "environment": ["environment", "env", "tier", "stage"],
            "application": ["application", "app", "application_name", "service"],
            "owner": ["owner", "responsible", "contact", "primary_contact"],
            "status": ["status", "state", "operational_status", "running_status"],
            "cpu_count": ["cpu", "cpu_count", "processors", "vcpu", "cores"],
            "memory_gb": ["memory", "ram", "memory_gb", "ram_gb", "mem"],
            "disk_gb": ["disk", "storage", "disk_gb", "hdd_size", "storage_gb"],
        }

    async def execute_data_import_validation(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute data import validation phase.
        This method validates imported data and prepares it for field mapping.

        Args:
            flow_id: Discovery Flow ID
            raw_data: Raw data records to validate
            client_account_id: Client account identifier
            engagement_id: Engagement identifier
            user_id: User identifier
            **kwargs: Additional parameters

        Returns:
            Dict containing validation results
        """
        try:
            logger.info(f"🔍 Executing data import validation for flow: {flow_id}")
            logger.info(f"📊 Validating {len(raw_data)} raw data records")

            # Create context for the validation
            context = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "user_id": user_id,
                "flow_id": flow_id,
            }

            # Get discovery flow service
            discovery_service = await self._get_discovery_flow_service(context)

            # Basic validation logic
            validation_results = {
                "total_records": len(raw_data),
                "valid_records": 0,
                "invalid_records": 0,
                "validation_errors": [],
                "field_analysis": {},
                "data_quality_score": 0.0,
            }

            valid_records = []
            for idx, record in enumerate(raw_data):
                if isinstance(record, dict) and record:
                    # Basic validation: record must be a non-empty dict
                    validation_results["valid_records"] += 1
                    valid_records.append(record)

                    # Analyze fields
                    for field_name, field_value in record.items():
                        if field_name not in validation_results["field_analysis"]:
                            validation_results["field_analysis"][field_name] = {
                                "count": 0,
                                "non_empty_count": 0,
                                "data_types": set(),
                            }

                        field_info = validation_results["field_analysis"][field_name]
                        field_info["count"] += 1

                        if field_value is not None and str(field_value).strip():
                            field_info["non_empty_count"] += 1

                        field_info["data_types"].add(type(field_value).__name__)
                else:
                    validation_results["invalid_records"] += 1
                    validation_results["validation_errors"].append(
                        {
                            "record_index": idx,
                            "error": "Record is not a valid dictionary or is empty",
                            "record": record,
                        }
                    )

            # Calculate data quality score
            if validation_results["total_records"] > 0:
                validation_results["data_quality_score"] = (
                    validation_results["valid_records"]
                    / validation_results["total_records"]
                )

            # Convert sets to lists for JSON serialization
            for field_name, field_info in validation_results["field_analysis"].items():
                field_info["data_types"] = list(field_info["data_types"])

            # Update flow state with validation results
            try:
                flow = await discovery_service.get_flow_by_id(flow_id)
                if flow:
                    await discovery_service.update_flow_data(
                        flow_id,
                        {
                            "validation_results": validation_results,
                            "valid_records_count": validation_results["valid_records"],
                            "data_quality_score": validation_results[
                                "data_quality_score"
                            ],
                        },
                    )
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to update flow state with validation results: {e}"
                )

            valid_count = validation_results["valid_records"]
            total_count = validation_results["total_records"]
            logger.info(
                f"✅ Data import validation completed: {valid_count}/{total_count} records valid"
            )

            return {
                "status": "completed",
                "phase": "data_import_validation",
                "results": validation_results,
                "valid_records": valid_records,
                "flow_id": flow_id,
                "method": "execute_data_import_validation",
            }

        except Exception as e:
            logger.error(f"❌ Data import validation failed for flow {flow_id}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                "status": "failed",
                "phase": "data_import_validation",
                "error": str(e),
                "flow_id": flow_id,
                "method": "execute_data_import_validation",
            }

    async def generate_field_mapping_suggestions(
        self,
        flow_id: str,
        validation_result: Dict[str, Any],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate field mapping suggestions based on validation results.
        This method analyzes field patterns and suggests mappings to standard schema.

        Args:
            flow_id: Discovery Flow ID
            validation_result: Results from data validation
            client_account_id: Client account identifier
            engagement_id: Engagement identifier
            user_id: User identifier
            **kwargs: Additional parameters

        Returns:
            Dict containing field mapping suggestions
        """
        try:
            logger.info(f"🗺️ Generating field mapping suggestions for flow: {flow_id}")

            # Get standard field mappings
            standard_fields = self._get_standard_field_mappings()

            # Get field analysis from validation results
            field_analysis = validation_result.get("field_analysis", {})

            # Generate mapping suggestions
            suggested_mappings = {}
            confidence_scores = {}
            unmapped_fields = []

            for field_name in field_analysis.keys():
                field_lower = field_name.lower().strip()
                best_match = None
                best_score = 0.0

                # Find best matching standard field
                for standard_field, patterns in standard_fields.items():
                    for pattern in patterns:
                        # Simple string matching scoring
                        if field_lower == pattern:
                            best_match = standard_field
                            best_score = 1.0
                            break
                        elif pattern in field_lower or field_lower in pattern:
                            score = 0.8 if pattern in field_lower else 0.6
                            if score > best_score:
                                best_match = standard_field
                                best_score = score

                if best_match and best_score > 0.5:
                    suggested_mappings[field_name] = best_match
                    confidence_scores[field_name] = best_score
                else:
                    unmapped_fields.append(field_name)

            # Calculate overall confidence
            overall_confidence = 0.0
            if suggested_mappings:
                overall_confidence = sum(confidence_scores.values()) / len(
                    confidence_scores
                )

            field_mapping_results = {
                "mappings": suggested_mappings,
                "confidence_scores": confidence_scores,
                "unmapped_fields": unmapped_fields,
                "overall_confidence": overall_confidence,
                "total_fields": len(field_analysis),
                "mapped_fields": len(suggested_mappings),
                "mapping_coverage": (
                    len(suggested_mappings) / len(field_analysis)
                    if field_analysis
                    else 0
                ),
            }

            logger.info(
                f"✅ Field mapping suggestions generated: {len(suggested_mappings)}/{len(field_analysis)} fields mapped"
            )

            return {
                "status": "completed",
                "phase": "field_mapping_suggestions",
                "results": field_mapping_results,
                "flow_id": flow_id,
                "method": "generate_field_mapping_suggestions",
            }

        except Exception as e:
            logger.error(
                f"❌ Field mapping suggestion generation failed for flow {flow_id}: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                "status": "failed",
                "phase": "field_mapping_suggestions",
                "error": str(e),
                "flow_id": flow_id,
                "method": "generate_field_mapping_suggestions",
            }

    async def execute_flow_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Dict[str, Any],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generic method to execute any flow phase.
        This method routes to the appropriate phase-specific method.

        Args:
            flow_id: Discovery Flow ID
            phase_name: Name of the phase to execute
            phase_input: Input data for the phase
            client_account_id: Client account identifier
            engagement_id: Engagement identifier
            user_id: User identifier
            **kwargs: Additional parameters

        Returns:
            Dict containing phase execution results
        """
        try:
            logger.info(f"🚀 Executing flow phase: {phase_name} for flow: {flow_id}")

            # Route to appropriate phase method
            if phase_name == "data_import_validation":
                return await self.execute_data_import_validation(
                    flow_id=flow_id,
                    raw_data=phase_input.get("raw_data", []),
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    **kwargs,
                )
            elif phase_name == "field_mapping":
                if phase_input.get("approved_mappings"):
                    return await self.apply_field_mappings(
                        flow_id=flow_id,
                        approved_mappings=phase_input["approved_mappings"],
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        user_id=user_id,
                        **kwargs,
                    )
                else:
                    return await self.generate_field_mapping_suggestions(
                        flow_id=flow_id,
                        validation_result=phase_input.get("validation_result", {}),
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        user_id=user_id,
                        **kwargs,
                    )
            elif phase_name == "data_cleansing":
                return await self.execute_data_cleansing(
                    flow_id=flow_id,
                    field_mappings=phase_input.get("field_mappings", {}),
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    **kwargs,
                )
            elif phase_name == "asset_creation":
                return await self.create_discovery_assets(
                    flow_id=flow_id,
                    cleaned_data=phase_input.get("cleaned_data", []),
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    **kwargs,
                )
            elif phase_name == "analysis":
                return await self.execute_analysis_phases(
                    flow_id=flow_id,
                    assets=phase_input.get("assets", []),
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    **kwargs,
                )
            else:
                # Unknown phase
                logger.warning(f"⚠️ Unknown flow phase: {phase_name}")
                return {
                    "status": "failed",
                    "phase": phase_name,
                    "error": f"Unknown phase: {phase_name}",
                    "flow_id": flow_id,
                    "method": "execute_flow_phase",
                }

        except Exception as e:
            logger.error(
                f"❌ Flow phase execution failed: {phase_name} for flow {flow_id}: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                "status": "failed",
                "phase": phase_name,
                "error": str(e),
                "flow_id": flow_id,
                "method": "execute_flow_phase",
            }
