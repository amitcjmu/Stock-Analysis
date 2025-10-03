"""
Business Value Agent - Parsers Module
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

    def _parse_agent_output(
        self, agent_output: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse the agent's natural language output into structured data"""
        try:
            result = {
                "agent_analysis_type": "business_value",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Business Value Agent",
            }

            output_lower = str(agent_output).lower()

            # Extract business value score
            score_match = re.search(r"business value score:?\s*(\d+)", output_lower)
            if score_match:
                result["business_value_score"] = int(score_match.group(1))
            else:
                # Try to extract score from other patterns
                score_match = re.search(r"score:?\s*(\d+)", output_lower)
                result["business_value_score"] = (
                    int(score_match.group(1)) if score_match else 5
                )

            # Extract confidence level
            if "high" in output_lower and "confidence" in output_lower:
                result["confidence_level"] = "high"
            elif "medium" in output_lower and "confidence" in output_lower:
                result["confidence_level"] = "medium"
            else:
                result["confidence_level"] = "medium"

            # Extract reasoning
            reasoning_match = re.search(
                r"(?:primary reasoning|reasoning):(.+?)(?:evidence found|$)",
                output_lower,
                re.DOTALL,
            )
            if reasoning_match:
                result["reasoning"] = reasoning_match.group(1).strip()
            else:
                result["reasoning"] = (
                    "Business value determined through agentic analysis"
                )

            # Extract recommendations
            recommendations_match = re.search(
                r"recommendations:(.+?)$", output_lower, re.DOTALL
            )
            if recommendations_match:
                result["recommendations"] = [
                    rec.strip()
                    for rec in recommendations_match.group(1).split("-")
                    if rec.strip()
                ]
            else:
                result["recommendations"] = ["Standard migration approach recommended"]

            # Set enrichment status
            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"

            return result

        except Exception as e:
            logger.warning(f"Failed to parse agent output: {e}")
            return self._create_default_analysis(asset_data)

    def _convert_reasoning_to_dict(self, reasoning: AgentReasoning) -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format"""
        return {
            "agent_analysis_type": "business_value",
            "business_value_score": reasoning.score,
            "confidence_level": (
                "high"
                if reasoning.confidence >= 0.7
                else "medium" if reasoning.confidence >= 0.4 else "low"
            ),
            "reasoning": reasoning.reasoning_summary,
            "evidence_count": len(reasoning.evidence_pieces),
            "patterns_applied": len(reasoning.applied_patterns),
            "patterns_discovered": len(reasoning.discovered_patterns),
            "recommendations": reasoning.recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine",
        }

    def _create_default_analysis(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default analysis when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "business_value",
            "business_value_score": 5,  # Default medium value
            "confidence_level": "low",
            "reasoning": "Default analysis - agent reasoning unavailable",
            "recommendations": ["Standard migration approach"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback",
        }
