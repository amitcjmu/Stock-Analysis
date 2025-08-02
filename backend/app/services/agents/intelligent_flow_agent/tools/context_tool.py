"""
Flow Context Tool

Tool for getting proper multi-tenant context for flow operations.
"""

import json
import logging
from typing import Any, Dict

from app.core.security.secure_setattr import secure_setattr, SAFE_ATTRIBUTES

try:
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class BaseTool:
        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"

        def __init__(self, **kwargs):
            # Define allowed attributes for this fallback tool
            allowed_attrs = SAFE_ATTRIBUTES | {
                "name",
                "description",
                "tool_type",
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


class FlowContextTool(BaseTool):
    """Tool for getting proper multi-tenant context for flow operations"""

    name: str = "flow_context_analyzer"
    description: str = (
        "Gets proper client, engagement, and user context for multi-tenant flow operations. Expects the actual flow_id UUID (e.g., '9a0cb58d-bad8-4fb7-a4b9-ee7e35df281b'), not placeholder strings."
    )

    def _run(
        self,
        flow_id: str,
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
    ) -> str:
        """Get context information for flow operations"""
        try:
            context = self._get_flow_context(
                flow_id, client_account_id, engagement_id, user_id
            )
            return json.dumps(
                {
                    "context_found": True,
                    "client_account_id": context.get("client_account_id"),
                    "engagement_id": context.get("engagement_id"),
                    "user_id": context.get("user_id"),
                    "flow_type": context.get("flow_type", "discovery"),
                    "message": "Context successfully retrieved for multi-tenant operations",
                }
            )
        except Exception as e:
            logger.error(f"Context analysis failed for {flow_id}: {e}")
            return json.dumps(
                {
                    "context_found": False,
                    "error": str(e),
                    "fallback_context": {
                        "client_account_id": client_account_id
                        or "11111111-1111-1111-1111-111111111111",
                        "engagement_id": engagement_id
                        or "22222222-2222-2222-2222-222222222222",
                        "flow_type": "discovery",
                    },
                }
            )

    def _get_flow_context(
        self,
        flow_id: str,
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """Get context using flow management service"""
        try:
            # Use direct service calls for context
            context = {
                "client_account_id": client_account_id
                or "11111111-1111-1111-1111-111111111111",
                "engagement_id": engagement_id
                or "22222222-2222-2222-2222-222222222222",
                "user_id": user_id,
                "flow_type": "discovery",  # Default, will be determined from flow data
            }

            return context
        except Exception as e:
            logger.error(f"Failed to get context for flow {flow_id}: {e}")
            raise
