"""
Application architecture-related intelligent options for questionnaire generation.
Handles dependency assessment and architecture-specific patterns.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_dependencies_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Suggest dependency complexity based on architecture pattern.

    Args:
        asset_context: Dict with asset data including 'architecture_pattern', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    architecture_pattern_raw = asset_context.get("architecture_pattern", "")
    # Handle custom_attributes.architecture_pattern format
    if not architecture_pattern_raw:
        architecture_pattern_raw = asset_context.get(
            "custom_attributes.architecture_pattern", ""
        )

    # Normalize: strip whitespace, convert to lowercase
    architecture_pattern = (architecture_pattern_raw or "").strip().lower()

    # Monolithic → Typically low dependencies (self-contained)
    if architecture_pattern in ["monolith", "monolithic", "monolithic_application"]:
        options = [
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing monolithic dependency options (minimal first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # Microservices → Typically high dependencies (distributed, many services)
    elif architecture_pattern in ["microservices", "microservices_architecture"]:
        options = [
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing microservices dependency options (high first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # SOA / Event-Driven → Moderate to high dependencies
    elif architecture_pattern in [
        "soa",
        "service_oriented_architecture",
        "service-oriented",
        "event_driven",
        "event-driven_architecture",
        "event-driven",
    ]:
        options = [
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing SOA/Event-Driven dependency options (moderate first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # Layered / N-Tier → Low to moderate dependencies (internal layers)
    elif architecture_pattern in [
        "layered",
        "n_tier",
        "n-tier",
        "ntier",
        "layered_architecture",
        "tiered",
    ]:
        options = [
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing layered/N-tier dependency options (low first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # Serverless → Minimal standalone functions
    elif architecture_pattern in [
        "serverless",
        "serverless_function",
        "function_based",
        "lambda",
        "faas",
    ]:
        options = [
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing serverless dependency options (minimal first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # Hybrid → Balanced options
    elif architecture_pattern in ["hybrid", "hybrid_architecture", "mixed"]:
        options = [
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {
                "value": "minimal",
                "label": "Minimal - Standalone with no or few external dependencies",
            },
            {
                "value": "very_high",
                "label": "Very High - Highly coupled with 16+ systems",
            },
            {
                "value": "unknown",
                "label": "Unknown - Dependency analysis not yet performed",
            },
        ]
        logger.info(
            f"Providing hybrid architecture dependency options (moderate first) "
            f"for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # If architecture_pattern is present but doesn't match patterns, return None
    return None
