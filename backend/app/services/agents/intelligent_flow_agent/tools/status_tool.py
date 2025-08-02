"""
Flow Status Tool

Tool for getting comprehensive flow status and phase information.
"""

import asyncio
import json
import logging
from typing import Any, Dict

try:
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class BaseTool:
        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"

        def __init__(self, **kwargs):
            from app.core.security.secure_setattr import secure_setattr, SAFE_ATTRIBUTES

            # Define allowed attributes for status tool updates
            allowed_attrs = SAFE_ATTRIBUTES | {
                "name",
                "description",
                "return_direct",
                "verbose",
                "args_schema",
                "response_format",
                "handle_tool_error",
                "handle_validation_error",
                "enabled",
            }

            for key, value in kwargs.items():
                # Use secure_setattr to prevent sensitive data exposure
                if not secure_setattr(
                    self, key, value, allowed_attrs, strict_mode=False
                ):
                    logging.warning(
                        f"Skipped setting potentially sensitive attribute: {key}"
                    )

        def _run(self, *args, **kwargs):
            return "CrewAI not available - using fallback"


logger = logging.getLogger(__name__)


class FlowStatusTool(BaseTool):
    """Tool for getting comprehensive flow status and phase information"""

    name: str = "flow_status_analyzer"
    description: str = (
        "Gets detailed flow status including current phase, progress, and data validation results. Pass the actual flow_id UUID and context_data as a JSON string."
    )

    def _run(self, flow_id: str, context_data: str) -> str:
        """Get comprehensive flow status with detailed analysis"""
        try:
            context = (
                json.loads(context_data)
                if isinstance(context_data, str)
                else context_data
            )

            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context, we need to handle this differently
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self._async_get_fixed_flow_status(flow_id, context)
                    )
                    status_result = future.result()
            except RuntimeError:
                # No running loop, use asyncio.run directly
                status_result = asyncio.run(
                    self._async_get_fixed_flow_status(flow_id, context)
                )

            # Special handling for not_found flows
            if (
                status_result.get("status") == "not_found"
                or status_result.get("current_phase") == "not_found"
            ):
                status_result["user_guidance"] = (
                    "Flow not found. User needs to start a new discovery flow by uploading data."
                )

            return json.dumps(status_result)

        except Exception as e:
            logger.error(f"Flow status analysis failed for {flow_id}: {e}")
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "flow_id": flow_id,
                    "current_phase": "data_import",
                    "progress": 0,
                    "status": "error",
                }
            )

    def _get_real_flow_status(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get real flow status using FIXED FlowHandler directly"""
        try:
            # Import our fixed FlowHandler directly
            import asyncio

            from app.core.context import RequestContext
            from app.services.agents.agent_service_layer.handlers.flow_handler import (
                FlowHandler,
            )

            # Create proper context for FlowHandler
            request_context = RequestContext(
                client_account_id=context.get(
                    "client_account_id", "11111111-1111-1111-1111-111111111111"
                ),
                engagement_id=context.get(
                    "engagement_id", "22222222-2222-2222-2222-222222222222"
                ),
                user_id=context.get("user_id"),
            )

            # Use our fixed FlowHandler directly
            handler = FlowHandler(request_context)

            # Since we're in a sync method but calling async, handle properly
            async def async_call():
                return await handler.get_flow_status(flow_id)

            # Try to run the async call properly
            try:
                asyncio.get_running_loop()
                # We're in an async context, use thread executor
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_call())
                    result = future.result()
            except RuntimeError:
                # No running loop, use asyncio.run directly
                result = asyncio.run(async_call())

            # Handle service layer responses
            if result.get("status") == "not_found":
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_type": "discovery",
                    "current_phase": "not_found",
                    "progress": 0.0,
                    "status": "not_found",
                    "phases": {},
                    "flow_exists": False,
                    "user_guidance": "Flow not found. User needs to start a new discovery flow by uploading data.",
                }

            elif result.get("status") == "error":
                return {
                    "success": False,
                    "flow_id": flow_id,
                    "flow_type": "discovery",
                    "current_phase": "error",
                    "progress": 0.0,
                    "status": "error",
                    "phases": {},
                    "error": result.get("error", "Service error"),
                    "user_guidance": result.get("guidance", "System error occurred"),
                }

            # Success case - extract flow data
            flow_data = result.get("flow", {})
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_type": "discovery",
                "current_phase": flow_data.get("current_phase", "data_import"),
                "next_phase": flow_data.get("next_phase"),
                "progress": flow_data.get("progress", 0.0),
                "status": flow_data.get("status", "active"),
                "phases": flow_data.get("phases_completed", {}),
                "flow_exists": True,
                "is_complete": flow_data.get("progress", 0) >= 100,
                "user_guidance": self._generate_user_guidance(flow_data),
            }

        except Exception as e:
            logger.error(f"Service layer flow status failed: {e}")
            # Return clear "not found" status for any errors
            return {
                "success": False,
                "flow_id": flow_id,
                "flow_type": "discovery",
                "current_phase": "not_found",
                "progress": 0.0,
                "status": "not_found",
                "phases": {},
                "raw_data_count": 0,
                "field_mapping": {},
                "validation_results": {},
                "error": str(e),
            }

    def _generate_user_guidance(self, flow_data: Dict[str, Any]) -> str:
        """Generate actionable user guidance based on flow state"""
        current_phase = flow_data.get("current_phase", "unknown")
        next_phase = flow_data.get("next_phase")
        progress = flow_data.get("progress", 0)

        if progress >= 100:
            return "All discovery phases completed. Flow is ready for assessment."

        if next_phase:
            phase_routes = {
                "data_import": "/discovery/data-import",
                "attribute_mapping": "/discovery/attribute-mapping",
                "data_cleansing": "/discovery/data-cleansing",
                "inventory": "/discovery/inventory-building",
                "dependencies": "/discovery/dependency-analysis",
                "tech_debt": "/discovery/tech-debt-analysis",
            }

            route = phase_routes.get(next_phase, f"/discovery/{next_phase}")
            phase_name = next_phase.replace("_", " ").title()
            return f"Navigate to {route} to continue with {phase_name} phase."

        # Handle flow not found
        if current_phase == "not_found":
            return "Flow not found. Navigate to /discovery/cmdb-import to start a new discovery flow."

        return f"Currently in {current_phase.replace('_', ' ').title()} phase."

    async def _async_get_fixed_flow_status(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Async flow status lookup using our FIXED FlowHandler"""
        try:
            # Import our fixed FlowHandler directly
            from app.core.context import RequestContext
            from app.services.agents.agent_service_layer.handlers.flow_handler import (
                FlowHandler,
            )

            # Create proper context for FlowHandler
            request_context = RequestContext(
                client_account_id=context.get(
                    "client_account_id", "11111111-1111-1111-1111-111111111111"
                ),
                engagement_id=context.get(
                    "engagement_id", "22222222-2222-2222-2222-222222222222"
                ),
                user_id=context.get("user_id"),
            )

            # Use our fixed FlowHandler directly
            handler = FlowHandler(request_context)

            # Call our fixed async method
            result = await handler.get_flow_status(flow_id)

            # Convert FlowHandler result to expected format
            if result.get("flow_exists"):
                flow_data = result.get("flow", {})

                # CRITICAL: Include data count from our improved detection
                raw_data_count = flow_data.get("raw_data_count", 0)

                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_type": "discovery",
                    "current_phase": flow_data.get("current_phase", "data_import"),
                    "next_phase": flow_data.get("next_phase"),
                    "progress": flow_data.get("progress", 0.0),
                    "status": flow_data.get("status", "active"),
                    "phases": flow_data.get("phases_completed", {}),
                    "flow_exists": True,
                    "is_complete": flow_data.get("progress", 0) >= 100,
                    "raw_data_count": raw_data_count,  # CRITICAL: Pass through our improved data detection
                    "data_import_id": flow_data.get("data_import_id"),
                    "user_guidance": self._generate_user_guidance(flow_data),
                }
            else:
                # Flow not found
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_type": "discovery",
                    "current_phase": "not_found",
                    "progress": 0.0,
                    "status": "not_found",
                    "phases": {},
                    "flow_exists": False,
                    "user_guidance": "Flow not found. User needs to start a new discovery flow by uploading data.",
                }

        except Exception as e:
            logger.error(f"Fixed flow status lookup failed: {e}")
            # Return clear "not found" status for any errors
            return {
                "success": False,
                "flow_id": flow_id,
                "flow_type": "discovery",
                "current_phase": "not_found",
                "progress": 0.0,
                "status": "not_found",
                "phases": {},
                "raw_data_count": 0,
                "field_mapping": {},
                "validation_results": {},
                "error": str(e),
            }

    async def _async_get_flow_status(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Async flow status lookup with proper error handling"""
        try:
            from app.api.v1.discovery_handlers.flow_management import (
                FlowManagementHandler,
            )
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal

            # Create request context
            request_context = RequestContext(
                client_account_id=context.get("client_account_id"),
                engagement_id=context.get("engagement_id"),
                user_id=context.get("user_id"),
                flow_id=flow_id,
            )

            async with AsyncSessionLocal() as session:
                handler = FlowManagementHandler(session, request_context)
                flow_response = await handler.get_flow_status(flow_id)

                # Handle non-existent flows clearly
                if flow_response.get("status") == "not_found":
                    return {
                        "success": True,
                        "flow_id": flow_id,
                        "flow_type": "discovery",
                        "current_phase": "not_found",
                        "progress": 0.0,
                        "status": "not_found",
                        "phases": {},
                        "raw_data_count": 0,
                        "field_mapping": {},
                        "validation_results": {},
                        "user_guidance": "FLOW_NOT_FOUND: This flow ID does not exist in the system. User needs to start a new discovery flow by uploading data.",
                    }

                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_type": flow_response.get("flow_type", "discovery"),
                    "current_phase": flow_response.get("current_phase", "data_import"),
                    "progress": flow_response.get("progress_percentage", 0),
                    "status": flow_response.get("status", "in_progress"),
                    "phases": flow_response.get("phases", {}),
                    "raw_data_count": len(flow_response.get("raw_data", [])),
                    "field_mapping": flow_response.get("field_mapping", {}),
                    "validation_results": flow_response.get("validation_results", {}),
                }

        except Exception as e:
            logger.error(f"Async flow status failed: {e}")
            # Return clear "not found" for any database/service errors
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_type": "discovery",
                "current_phase": "not_found",
                "progress": 0.0,
                "status": "not_found",
                "phases": {},
                "raw_data_count": 0,
                "field_mapping": {},
                "validation_results": {},
                "user_guidance": "FLOW_ERROR: Unable to access flow data. Flow may not exist or there may be a system issue.",
            }
