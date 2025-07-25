"""
Phase Validation Tool

This tool validates whether phases are complete by calling validation APIs
that check actual data presence and quality.
"""

import logging

from app.core.context import RequestContext

from ..crewai_imports import BaseTool

logger = logging.getLogger(__name__)


class PhaseValidationTool(BaseTool):
    """Tool for validating phase completion using actual data validation APIs"""

    name: str = "phase_validator"
    description: str = "Validates whether phases are complete by calling validation APIs that check actual data presence and quality"

    # Define fields for Pydantic compatibility
    base_url: str = "http://127.0.0.1:8000"
    timeout: float = 30.0

    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0

    def _run(self, flow_id: str, phase: str) -> str:
        """Validate phase completion using validation API"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_phase(flow_id, phase)
        except Exception as e:
            logger.error(f"Phase validation error for {phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)}"

    def _sync_validate_phase(self, flow_id: str, phase: str) -> str:
        """Validate phase using real validation services to provide actionable guidance"""
        try:
            # Call the actual phase validation endpoint
            import asyncio

            from app.core.context import RequestContext

            # Create context for service calls
            context = RequestContext(
                client_account_id="11111111-1111-1111-1111-111111111111",
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id=None,
                session_id=None,
            )

            # Use a thread to run async call safely
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self._validate_phase_real(flow_id, phase, context)
                )
                result = future.result(timeout=30)
                return result

        except Exception as e:
            logger.error(f"Phase validation failed for {flow_id}/{phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)} - Please check system status and retry"

    async def _validate_phase_real(
        self, flow_id: str, phase: str, context: "RequestContext"
    ) -> str:
        """Use real validation service to check phase completion"""
        try:
            from app.api.v1.endpoints.flow_processing import validate_phase_data
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                # Call the actual validation function
                validation_result = await validate_phase_data(
                    flow_id, phase, session, context
                )

                status = validation_result.get("status", "UNKNOWN")
                message = validation_result.get("message", "No details available")
                complete = validation_result.get("complete", False)
                data = validation_result.get("data", {})

                # Provide specific actionable guidance based on phase and validation results
                actionable_guidance = []

                if phase == "data_import" and not complete:
                    import_sessions = data.get("import_sessions", 0)
                    raw_records = data.get("raw_records", 0)
                    data.get("threshold_met", False)

                    if import_sessions == 0:
                        actionable_guidance.append(
                            "No data files have been uploaded yet"
                        )
                        actionable_guidance.append(
                            "ACTION: User needs to upload a data file using the Data Import page"
                        )
                        actionable_guidance.append("ROUTE: /discovery/data-import")
                    elif raw_records < 5:
                        actionable_guidance.append(
                            f"Only {raw_records} records imported - insufficient for analysis"
                        )
                        actionable_guidance.append(
                            "ACTION: User needs to upload a larger data file with more records"
                        )
                        actionable_guidance.append("ROUTE: /discovery/data-import")
                    else:
                        actionable_guidance.append(
                            f"Data imported ({raw_records} records) but processing incomplete"
                        )
                        actionable_guidance.append(
                            "ACTION: System should trigger background processing of imported data"
                        )
                        actionable_guidance.append(
                            "INTERNAL: Re-trigger data import processing workflow"
                        )

                elif phase == "attribute_mapping" and not complete:
                    approved_mappings = data.get("approved_mappings", 0)
                    data.get("high_confidence_mappings", 0)

                    if approved_mappings == 0:
                        actionable_guidance.append(
                            "No field mappings have been configured"
                        )
                        actionable_guidance.append(
                            "ACTION: User needs to configure field mappings"
                        )
                        actionable_guidance.append(
                            "ROUTE: /discovery/attribute-mapping"
                        )
                    else:
                        actionable_guidance.append(
                            f"Only {approved_mappings} mappings approved - need more for completion"
                        )
                        actionable_guidance.append(
                            "ACTION: User needs to review and approve more field mappings"
                        )
                        actionable_guidance.append(
                            "ROUTE: /discovery/attribute-mapping"
                        )

                # Format comprehensive result with actionable guidance
                result = f"Phase {phase} is {status}: {message} (Complete: {complete})"
                result += f" | Data: {data}"
                if actionable_guidance:
                    result += (
                        f" | ACTIONABLE_GUIDANCE: {'; '.join(actionable_guidance)}"
                    )

                return result

        except Exception as e:
            logger.error(f"Real phase validation failed for {flow_id}/{phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)} - System unable to validate phase completion"
