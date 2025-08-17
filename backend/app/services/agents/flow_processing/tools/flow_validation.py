"""
Flow Validation Tool

This tool performs fast fail-first flow validation to identify the first
incomplete phase that needs attention.
"""

import logging

from app.core.context import RequestContext

from ..crewai_imports import BaseTool

logger = logging.getLogger(__name__)


class FlowValidationTool(BaseTool):
    """Tool for fast fail-first flow validation to find the current incomplete phase"""

    name: str = "flow_validator"
    description: str = (
        "Performs fast fail-first validation to identify the first incomplete phase that needs attention"
    )

    # Define fields for Pydantic compatibility
    base_url: str = "http://127.0.0.1:8000"
    timeout: float = 30.0

    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0

    def _run(self, flow_id: str) -> str:
        """Validate flow and return first incomplete phase"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_flow(flow_id)
        except Exception as e:
            logger.error(f"Flow validation error for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)}"

    def _sync_validate_flow(self, flow_id: str) -> str:
        """Flow validation using real validation services with actionable guidance"""
        try:
            # Call the actual flow validation endpoint
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
                    asyncio.run, self._validate_flow_real(flow_id, context)
                )
                result = future.result(timeout=30)
                return result

        except Exception as e:
            logger.error(f"Flow validation failed for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)} - Please check system status and retry"

    async def _validate_flow_real(self, flow_id: str, context: "RequestContext") -> str:
        """Use real validation service to check flow completion with actionable guidance"""
        try:
            from app.api.v1.endpoints.flow_processing import validate_flow_phases
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                # Call the actual validation function
                validation_result = await validate_flow_phases(
                    flow_id, session, context
                )

                current_phase = validation_result.get("current_phase", "unknown")
                status = validation_result.get("status", "UNKNOWN")
                next_action = validation_result.get(
                    "next_action", "Unknown action required"
                )
                route_to = validation_result.get(
                    "route_to", "/discovery/enhanced-dashboard"
                )
                validation_details = validation_result.get("validation_details", {})

                # Build actionable guidance based on validation details
                actionable_guidance = []

                if current_phase == "data_import" and status == "INCOMPLETE":
                    data = validation_details.get("data", {})
                    import_sessions = data.get("import_sessions", 0)
                    raw_records = data.get("raw_records", 0)

                    if import_sessions == 0:
                        actionable_guidance.append("ISSUE: No data has been uploaded")
                        actionable_guidance.append(
                            "USER_ACTION: Upload a data file via Data Import page"
                        )
                        actionable_guidance.append(
                            "SYSTEM_ACTION: Navigate user to data import"
                        )
                    elif raw_records < 5:
                        actionable_guidance.append(
                            f"ISSUE: Insufficient data ({raw_records} records)"
                        )
                        actionable_guidance.append(
                            "USER_ACTION: Upload a larger data file with more records"
                        )
                        actionable_guidance.append(
                            "SYSTEM_ACTION: Guide user to upload better data"
                        )
                    else:
                        actionable_guidance.append(
                            f"ISSUE: Data uploaded ({raw_records} records) but processing incomplete"
                        )
                        actionable_guidance.append(
                            "USER_ACTION: No user action required"
                        )
                        actionable_guidance.append(
                            "SYSTEM_ACTION: Trigger background data processing"
                        )

                # Format comprehensive result with fail-fast approach
                result = (
                    f"Flow {flow_id}: CurrentPhase={current_phase}, "
                    f"Status={status}, NextAction={next_action}, Route={route_to}"
                )
                result += " | FailFast=True (stopped at first incomplete phase)"

                if actionable_guidance:
                    result += (
                        f" | ACTIONABLE_GUIDANCE: {'; '.join(actionable_guidance)}"
                    )

                return result

        except Exception as e:
            logger.error(f"Real flow validation failed for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)} - System unable to validate flow completion"
