"""
Modernization Agent - Parsers Module
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

    def _parse_modernization_output(
        self, agent_output: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse the agent's modernization assessment output into structured data"""
        try:
            result = {
                "agent_analysis_type": "modernization_assessment",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Modernization Agent",
            }

            output_lower = str(agent_output).lower()

            # Extract cloud readiness score with validation and clamping
            readiness_score_match = re.search(
                r"cloud readiness score:?\s*(\d+)", output_lower
            )
            if readiness_score_match:
                try:
                    score = int(readiness_score_match.group(1))
                    # Clamp to 0-100 range
                    result["cloud_readiness_score"] = max(0, min(100, score))
                except (ValueError, AttributeError):
                    result["cloud_readiness_score"] = 50
            else:
                result["cloud_readiness_score"] = 50

            # Extract modernization potential
            if "modernization potential: high" in output_lower:
                result["modernization_potential"] = "high"
            elif "modernization potential: medium" in output_lower:
                result["modernization_potential"] = "medium"
            else:
                result["modernization_potential"] = "low"

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
            logger.warning(f"Failed to parse modernization output: {e}")
            return self._create_default_modernization_assessment(asset_data)

    def _convert_reasoning_to_dict(self, reasoning: AgentReasoning) -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format for modernization assessment"""

        modernization_potential = "low"
        if reasoning.score >= 80:
            modernization_potential = "high"
        elif reasoning.score >= 60:
            modernization_potential = "medium"

        return {
            "agent_analysis_type": "modernization_assessment",
            "cloud_readiness_score": reasoning.score,
            "modernization_potential": modernization_potential,
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

    def _create_default_modernization_assessment(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a default modernization assessment when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "modernization_assessment",
            "cloud_readiness_score": 50,
            "modernization_potential": "medium",
            "recommended_strategy": "lift-and-shift",
            "migration_effort": "medium",
            "technical_confidence": "low",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback",
        }
