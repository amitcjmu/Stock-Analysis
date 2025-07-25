"""
Phase Validation Tool

Tool for validating specific phase completion using success criteria.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

try:
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class BaseTool:
        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def _run(self, *args, **kwargs):
            return "CrewAI not available - using fallback"


from app.core.context import RequestContext
from app.knowledge_bases.flow_intelligence_knowledge import (
    FlowType,
    get_phase_definition,
    get_success_criteria,
)

logger = logging.getLogger(__name__)


class PhaseValidationTool(BaseTool):
    """Tool for validating specific phase completion using success criteria"""

    name: str = "phase_validator"
    description: str = "Validates if a specific phase meets its success criteria by checking actual data and validation services"

    def _run(
        self, flow_id: str, phase_id: str, flow_type: str, context_data: str
    ) -> str:
        """Validate phase completion against success criteria"""
        try:
            context = (
                json.loads(context_data)
                if isinstance(context_data, str)
                else context_data
            )

            # Get phase definition and success criteria
            flow_type_enum = FlowType(flow_type)
            phase_def = get_phase_definition(flow_type_enum, phase_id)
            success_criteria = get_success_criteria(flow_type_enum, phase_id)

            if not phase_def:
                return json.dumps(
                    {
                        "phase_valid": False,
                        "error": f"Unknown phase {phase_id} for flow type {flow_type}",
                        "completion_percentage": 0,
                    }
                )

            # Validate phase using real services
            validation_result = self._validate_phase_criteria(
                flow_id, phase_id, success_criteria, context
            )

            return json.dumps(validation_result)

        except Exception as e:
            logger.error(f"Phase validation failed for {flow_id}/{phase_id}: {e}")
            return json.dumps(
                {
                    "phase_valid": False,
                    "error": str(e),
                    "completion_percentage": 0,
                    "issues": [f"Validation service error: {str(e)}"],
                }
            )

    def _validate_phase_criteria(
        self,
        flow_id: str,
        phase_id: str,
        success_criteria: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate phase against its success criteria"""
        try:
            if phase_id == "data_import":
                return self._validate_data_import_phase(
                    flow_id, success_criteria, context
                )
            elif phase_id == "attribute_mapping":
                return self._validate_attribute_mapping_phase(
                    flow_id, success_criteria, context
                )
            elif phase_id == "data_cleansing":
                return self._validate_data_cleansing_phase(
                    flow_id, success_criteria, context
                )
            else:
                # Generic validation for other phases
                return {
                    "phase_valid": False,
                    "completion_percentage": 0,
                    "issues": [f"Phase {phase_id} validation not yet implemented"],
                    "criteria_met": [],
                    "criteria_failed": success_criteria,
                }
        except Exception as e:
            logger.error(f"Criteria validation failed: {e}")
            return {
                "phase_valid": False,
                "completion_percentage": 0,
                "issues": [f"Validation error: {str(e)}"],
                "criteria_met": [],
                "criteria_failed": success_criteria,
            }

    def _validate_data_import_phase(
        self, flow_id: str, success_criteria: List[str], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data import phase specifically"""
        try:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self._async_validate_data_import(flow_id, context)
                )
                result = future.result(timeout=10)
                return result
        except Exception as e:
            logger.error(f"Data import validation failed: {e}")
            return {
                "phase_valid": False,
                "completion_percentage": 0,
                "issues": [f"Data import validation error: {str(e)}"],
                "specific_issue": "Unable to check data import status",
                "user_action_needed": "Check data import page and upload data if needed",
            }

    async def _async_validate_data_import(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Async validation of data import phase"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.services.data_import_v2_service import DataImportV2Service

            # Create request context
            request_context = RequestContext(
                client_account_id=context.get("client_account_id"),
                engagement_id=context.get("engagement_id"),
                user_id=context.get("user_id"),
                flow_id=flow_id,
            )

            async with AsyncSessionLocal() as session:
                import_service = DataImportV2Service(session, request_context)
                latest_import = await import_service.get_latest_import()

                if not latest_import:
                    return {
                        "phase_valid": False,
                        "completion_percentage": 0,
                        "issues": ["No data import found"],
                        "specific_issue": "No data has been uploaded yet",
                        "user_action_needed": "Go to Data Import page and upload a CSV/Excel file with asset data",
                        "criteria_met": [],
                        "criteria_failed": [
                            "At least 1 data file uploaded successfully",
                            "Raw data records > 0 in database",
                        ],
                    }

                # Check record count
                record_count = latest_import.get("record_count", 0)
                status = latest_import.get("status", "unknown")

                if record_count == 0:
                    return {
                        "phase_valid": False,
                        "completion_percentage": 0,
                        "issues": [
                            f"Data import found but contains 0 records (Status: {status})"
                        ],
                        "specific_issue": "Data file was uploaded but contains no valid records",
                        "user_action_needed": "Upload a data file containing asset information with at least 1 record",
                        "criteria_met": [],
                        "criteria_failed": ["Raw data records > 0 in database"],
                    }

                # Import exists with data
                criteria_met = [
                    "At least 1 data file uploaded successfully",
                    "Raw data records > 0 in database",
                ]

                if status == "completed":
                    criteria_met.append("Import status = 'completed'")
                    criteria_met.append("No critical import errors")

                    return {
                        "phase_valid": True,
                        "completion_percentage": 100,
                        "issues": [],
                        "record_count": record_count,
                        "import_status": status,
                        "criteria_met": criteria_met,
                        "criteria_failed": [],
                    }
                else:
                    return {
                        "phase_valid": False,
                        "completion_percentage": 50,
                        "issues": [f"Import status is '{status}', not 'completed'"],
                        "specific_issue": f"Data import is in '{status}' status",
                        "user_action_needed": "Wait for import processing to complete or check for import errors",
                        "criteria_met": criteria_met[:2],  # First two criteria met
                        "criteria_failed": [
                            "Import status = 'completed'",
                            "No critical import errors",
                        ],
                    }

        except Exception as e:
            logger.error(f"Async data import validation failed: {e}")
            raise

    def _validate_attribute_mapping_phase(
        self, flow_id: str, success_criteria: List[str], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate attribute mapping phase"""
        # Simplified validation - in real implementation would check field mapping service
        return {
            "phase_valid": False,
            "completion_percentage": 0,
            "issues": ["Attribute mapping validation not yet implemented"],
            "user_action_needed": "Complete field mapping configuration",
            "criteria_met": [],
            "criteria_failed": success_criteria,
        }

    def _validate_data_cleansing_phase(
        self, flow_id: str, success_criteria: List[str], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data cleansing phase"""
        # Simplified validation - in real implementation would check data quality service
        return {
            "phase_valid": False,
            "completion_percentage": 0,
            "issues": ["Data cleansing validation not yet implemented"],
            "user_action_needed": "Complete data quality analysis and cleansing",
            "criteria_met": [],
            "criteria_failed": success_criteria,
        }
