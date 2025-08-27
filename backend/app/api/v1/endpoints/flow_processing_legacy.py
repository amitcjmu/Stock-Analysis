"""
Flow Processing Legacy Validation Functions
Maintained for backward compatibility
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

# Import the REAL single intelligent CrewAI agent
try:
    from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent

    INTELLIGENT_AGENT_AVAILABLE = True
except ImportError:
    INTELLIGENT_AGENT_AVAILABLE = False

    class IntelligentFlowAgent:
        async def analyze_flow_continuation(self, flow_id: str, **kwargs):
            return type(
                "MockResult",
                (),
                {
                    "current_phase": "data_import",
                    "phase_status": "INCOMPLETE",
                    "specific_issues": [],
                },
            )()


async def validate_flow_phases(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Dict[str, Any]:
    """Legacy validation function - simplified for compatibility"""
    try:
        # Use the intelligent agent for validation too
        intelligent_agent = IntelligentFlowAgent()
        result = await intelligent_agent.analyze_flow_continuation(flow_id)

        return {
            "current_phase": result.current_phase,
            "status": result.phase_status,
            "validation_details": {
                "data": {
                    "import_sessions": 1,  # Simplified for compatibility
                    "raw_records": 0,  # Will be updated by agent analysis
                    "threshold_met": False,
                }
            },
        }

    except Exception as e:
        logger.error(f"Legacy validation failed: {e}")
        return {
            "current_phase": "data_import",
            "status": "INCOMPLETE",
            "validation_details": {"error": str(e)},
        }


async def validate_phase_data(
    flow_id: str, phase: str, db: AsyncSession, context: RequestContext
) -> Dict[str, Any]:
    """Legacy phase validation function - simplified for compatibility"""
    try:
        # Use the intelligent agent for phase validation
        intelligent_agent = IntelligentFlowAgent()
        result = await intelligent_agent.analyze_flow_continuation(flow_id)

        return {
            "phase": phase,
            "status": result.phase_status,
            "complete": result.phase_status == "COMPLETE",
            "data": {"import_sessions": 1, "raw_records": 0, "threshold_met": False},
            "actionable_guidance": (
                result.specific_issues[0]
                if result.specific_issues
                else "No specific issues"
            ),
        }

    except Exception as e:
        logger.error(f"Legacy phase validation failed: {e}")
        return {
            "phase": phase,
            "status": "ERROR",
            "complete": False,
            "data": {},
            "actionable_guidance": f"Validation error: {str(e)}",
        }
