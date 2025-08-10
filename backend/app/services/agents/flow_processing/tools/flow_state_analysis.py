"""
Flow State Analysis Tool

This tool analyzes the current state of any flow type (Discovery, Assess, Plan, Execute, etc.)
to determine progress and completion status using API validation endpoints.
"""

import logging

from app.core.context import RequestContext

from ..crewai_imports import BaseTool

logger = logging.getLogger(__name__)


class FlowStateAnalysisTool(BaseTool):
    """Tool for analyzing current flow state across all flow types using API calls"""

    name: str = "flow_state_analyzer"
    description: str = (
        "Analyzes the current state of any flow type (Discovery, Assess, Plan, "
        "Execute, etc.) using API validation endpoints to determine progress and "
        "completion status"
    )

    # API-based tool - no database access needed
    base_url: str = (
        "http://127.0.0.1:8000"  # Use 127.0.0.1 for internal container calls
    )
    timeout: float = 30.0  # Increased timeout for complex validations

    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0

    def _run(self, flow_id: str) -> str:
        """Analyze flow state using API calls and return structured analysis"""
        try:
            # Use API calls to get flow status instead of direct database access
            result = self._get_flow_status_via_api(flow_id)
            return (
                f"Flow {flow_id} analysis: Type={result['flow_type']}, "
                f"Phase={result['current_phase']}, Progress={result['progress_percentage']}%, "
                f"Status={result['status']}"
            )
        except Exception as e:
            logger.error(f"Flow state analysis failed for {flow_id}: {e}")
            return f"Error analyzing flow {flow_id}: {str(e)}"

    def _get_flow_status_via_api(self, flow_id: str) -> dict:
        """Get flow status using real service calls to provide actionable insights"""
        try:
            # Call the actual flow management service to get real status
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
                    asyncio.run, self._get_real_flow_status(flow_id, context)
                )
                result = future.result(timeout=30)
                return result

        except Exception as e:
            logger.error(f"Failed to get real flow status for {flow_id}: {e}")
            # Return error status with actionable guidance
            return {
                "flow_type": "discovery",
                "current_phase": "data_import",
                "status": "error",
                "progress_percentage": 0,
                "phases_data": {},
                "agent_insights": [],
                "validation_results": {},
                "error_message": f"Failed to get flow status: {str(e)}",
                "actionable_guidance": "Please check system logs and retry the flow processing",
            }

    async def _get_real_flow_status(
        self, flow_id: str, context: "RequestContext"
    ) -> dict:
        """Get real flow status with detailed analysis"""
        try:
            from app.api.v1.discovery_handlers.flow_management import (
                FlowManagementHandler,
            )
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                handler = FlowManagementHandler(session, context)
                flow_response = await handler.get_flow_status(flow_id)

                # Analyze the real status to provide actionable insights
                current_phase = flow_response.get("current_phase", "data_import")
                progress = flow_response.get("progress_percentage", 0)
                phases = flow_response.get("phases", {})

                # Determine what specifically failed or needs attention
                actionable_insights = []
                specific_issues = []

                if current_phase == "data_import" and progress == 0:
                    # Check if there's actual data
                    raw_data = flow_response.get("raw_data", [])
                    flow_response.get("field_mapping", {})

                    if not raw_data:
                        specific_issues.append("No data has been imported yet")
                        actionable_insights.append(
                            "User needs to upload a data file first"
                        )
                    elif len(raw_data) < 5:
                        specific_issues.append(
                            f"Only {len(raw_data)} records imported - insufficient for analysis"
                        )
                        actionable_insights.append(
                            "User should upload a file with more data records"
                        )
                    else:
                        specific_issues.append(
                            "Data imported but not processed through validation"
                        )
                        actionable_insights.append(
                            "System should trigger data validation and processing"
                        )

                # Convert to format expected by agent
                return {
                    "flow_type": "discovery",
                    "current_phase": current_phase,
                    "status": flow_response.get("status", "active"),
                    "progress_percentage": progress,
                    "phases_data": phases,
                    "agent_insights": flow_response.get("agent_insights", []),
                    "validation_results": flow_response.get("validation_results", {}),
                    "raw_data_count": len(flow_response.get("raw_data", [])),
                    "field_mapping_status": (
                        "configured"
                        if flow_response.get("field_mapping")
                        else "pending"
                    ),
                    "specific_issues": specific_issues,
                    "actionable_insights": actionable_insights,
                    "data_import_id": flow_response.get("data_import_id"),
                    "created_at": flow_response.get("created_at"),
                    "updated_at": flow_response.get("updated_at"),
                }
        except Exception as e:
            logger.error(f"Real flow status failed for {flow_id}: {e}")
            raise

    def _determine_flow_type_via_api(self, flow_id: str) -> str:
        """Determine flow type using API calls instead of database queries"""
        try:
            import requests

            # Use default client context for agent requests
            headers = {
                "Content-Type": "application/json",
                "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
                "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
            }

            # Try unified flows endpoint first (preferred)
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/flows",
                    headers=headers,
                    params={"flowId": flow_id},
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception:
                        data = None
                    if isinstance(data, dict) and data:
                        if str(data.get("id") or data.get("flow_id")) == str(flow_id):
                            return data.get("flow_type", "discovery")
                    elif isinstance(data, list) and data:
                        for item in data:
                            if isinstance(item, dict) and str(
                                item.get("id") or item.get("flow_id")
                            ) == str(flow_id):
                                return item.get("flow_type", "discovery")
            except Exception:
                pass

            # For now, default to discovery since that's the primary flow type
            # In the future, this could check other flow type APIs
            return "discovery"

        except Exception as e:
            logger.error(f"Failed to determine flow type via API for {flow_id}: {e}")
            return "discovery"

    def _get_default_phase_for_flow_type(self, flow_type: str) -> str:
        """Get default starting phase for each flow type"""
        default_phases = {
            "discovery": "data_import",
            "assess": "migration_readiness",
            "plan": "wave_planning",
            "execute": "pre_migration",
            "modernize": "modernization_assessment",
            "finops": "cost_analysis",
            "observability": "monitoring_setup",
            "decommission": "decommission_planning",
        }
        return default_phases.get(flow_type, "data_import")
