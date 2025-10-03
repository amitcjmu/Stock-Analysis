"""
RiskAssessment Agent - Parsers Module
Contains methods for parsing agent output and converting data formats.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict

from app.services.agentic_intelligence.agent_reasoning_patterns import AgentReasoning

logger = logging.getLogger(__name__)


class ParsersMixin:
    """Mixin for output parsing and data conversion"""

    def _parse_risk_assessment_output(
        self, agent_output: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse the agent's risk_assessment assessment output into structured data"""
        try:
            result = {
                "agent_analysis_type": "risk_assessment_assessment",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "RiskAssessment Agent",
            }

            output_lower = str(agent_output).lower()

            # Extract security risk score (NOT cloud readiness) with validation and clamping
            risk_score_match = (
                re.search(r"security risk score:?\s*(\d+)", output_lower)
                or re.search(r"risk score:?\s*(\d+)", output_lower)
                or re.search(r"score:?\s*(\d+)", output_lower)
            )
            if risk_score_match:
                try:
                    score = int(risk_score_match.group(1))
                    # Clamp to 0-100 range
                    result["security_risk_score"] = max(0, min(100, score))
                except (ValueError, AttributeError):
                    result["security_risk_score"] = 50
            else:
                result["security_risk_score"] = 50

            # Extract risk level with better patterns
            if "risk: high" in output_lower or "high risk" in output_lower:
                result["risk_assessment"] = "high"
            elif "risk: medium" in output_lower or "medium risk" in output_lower:
                result["risk_assessment"] = "medium"
            else:
                result["risk_assessment"] = "low"

            # Extract recommended strategy
            if "recommended strategy: rebuild" in output_lower:
                result["recommended_strategy"] = "rebuild"
            elif "recommended strategy: refactor" in output_lower:
                result["recommended_strategy"] = "refactor"
            elif "recommended strategy: re-platform" in output_lower:
                result["recommended_strategy"] = "re-platform"
            else:
                result["recommended_strategy"] = "lift-and-shift"

            # Extract migration effort
            if "migration effort: high" in output_lower:
                result["migration_effort"] = "high"
            elif "migration effort: medium" in output_lower:
                result["migration_effort"] = "medium"
            else:
                result["migration_effort"] = "low"

            # Extract technical confidence
            if "high" in output_lower and "confidence" in output_lower:
                result["technical_confidence"] = "high"
            elif "medium" in output_lower and "confidence" in output_lower:
                result["technical_confidence"] = "medium"
            else:
                result["technical_confidence"] = "medium"

            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"

            return result

        except Exception as e:
            logger.warning(f"Failed to parse risk_assessment output: {e}")
            return self._create_default_risk_assessment_assessment(asset_data)

    def _convert_reasoning_to_dict(self, reasoning: AgentReasoning) -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format for risk_assessment assessment"""

        risk_assessment = "low"
        if reasoning.score >= 80:
            risk_assessment = "high"
        elif reasoning.score >= 60:
            risk_assessment = "medium"

        return {
            "agent_analysis_type": "risk_assessment_assessment",
            "security_risk_score": reasoning.score,
            "risk_assessment": risk_assessment,
            "recommended_strategy": (
                "re-platform" if reasoning.score >= 70 else "lift-and-shift"
            ),
            "migration_effort": "medium",
            "technical_confidence": (
                "high"
                if reasoning.confidence >= 0.7
                else "medium" if reasoning.confidence >= 0.4 else "low"
            ),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine",
        }

    def _create_default_risk_assessment_assessment(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a default risk_assessment assessment when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "risk_assessment_assessment",
            "security_risk_score": 50,
            "risk_assessment": "medium",
            "recommended_strategy": "lift-and-shift",
            "migration_effort": "medium",
            "technical_confidence": "low",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback",
        }
