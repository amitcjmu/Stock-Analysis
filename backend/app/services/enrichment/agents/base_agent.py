"""
Base Enrichment Agent - Shared parsing and normalization logic for all enrichment agents.

**ADR COMPLIANCE**:
- ADR-029: Centralized safe_parse_llm_json usage with proper type checking

This base class provides a reusable `_parse_and_normalize` method that handles:
- JSON parsing with ADR-029 compliance (safe_parse_llm_json)
- Type validation (ensures response is a dict, not list/None)
- Error handling with fallback data
- Logging for debugging parse failures
"""

import logging
from typing import Any, Callable, Dict, TypeVar

from app.utils.json_sanitization import safe_parse_llm_json

logger = logging.getLogger(__name__)

# Type variable for fallback data type
T = TypeVar("T", bound=Dict[str, Any])


class BaseEnrichmentAgent:
    """
    Base class for all enrichment agents providing shared parsing utilities.

    All enrichment agents should inherit from this class to use the
    standardized `_parse_and_normalize` method for LLM response handling.
    """

    def _parse_and_normalize(
        self,
        response: str,
        normalizer: Callable[[Dict[str, Any]], Dict[str, Any]],
        fallback_data: Dict[str, Any],
        agent_name: str,
    ) -> Dict[str, Any]:
        """
        Parse LLM response and normalize data with error handling.

        This method provides a standardized way to:
        1. Parse JSON using safe_parse_llm_json (ADR-029)
        2. Validate the response is a dict (not list/None)
        3. Apply agent-specific normalization
        4. Handle errors with appropriate fallback data

        Args:
            response: Raw LLM response string
            normalizer: Function to normalize parsed dict into agent-specific format
            fallback_data: Data to return on parse/normalization failure
            agent_name: Name of the agent for logging purposes

        Returns:
            Normalized data dict or fallback_data on failure

        Example:
            ```python
            def _normalize_compliance_data(self, data: Dict) -> Dict:
                return {
                    "compliance_scopes": data.get("compliance_scopes", []),
                    "data_classification": data.get("data_classification", "internal"),
                    ...
                }

            result = self._parse_and_normalize(
                response=llm_response,
                normalizer=self._normalize_compliance_data,
                fallback_data={"compliance_scopes": [], ...},
                agent_name="compliance",
            )
            ```
        """
        # ADR-029: Use safe_parse_llm_json instead of json.loads
        data = safe_parse_llm_json(response)

        # Fix for Qodo suggestion: Check isinstance(data, dict) instead of just None
        # This handles cases where LLM returns a list or other non-dict JSON
        if not isinstance(data, dict):
            logger.warning(
                f"Failed to parse {agent_name} response as dict: {response[:100]}..."
            )
            return {
                **fallback_data,
                "reasoning": "Failed to parse LLM response as JSON object",
            }

        try:
            return normalizer(data)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize {agent_name} data: {e}")
            return {
                **fallback_data,
                "reasoning": f"Failed to normalize LLM response data: {e}",
            }
