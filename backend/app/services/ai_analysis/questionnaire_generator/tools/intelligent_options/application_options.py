"""
Application architecture-related intelligent options for questionnaire generation.
Handles dependency assessment and architecture-specific patterns.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# All possible dependency options
ALL_OPTIONS = {
    "minimal": {
        "value": "minimal",
        "label": "Minimal - Standalone with no or few external dependencies",
    },
    "low": {"value": "low", "label": "Low - Depends on 1-3 systems"},
    "moderate": {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
    "high": {"value": "high", "label": "High - Depends on 8-15 systems"},
    "very_high": {
        "value": "very_high",
        "label": "Very High - Highly coupled with 16+ systems",
    },
    "unknown": {
        "value": "unknown",
        "label": "Unknown - Dependency analysis not yet performed",
    },
}

# Architecture pattern configurations
ARCHITECTURE_CONFIG = {
    "monolithic": {
        "aliases": {"monolith", "monolithic_application"},
        "order": ["minimal", "low", "moderate", "high", "very_high", "unknown"],
        "log_message": "monolithic dependency options (minimal first)",
    },
    "microservices": {
        "aliases": {"microservices_architecture"},
        "order": ["high", "very_high", "moderate", "low", "minimal", "unknown"],
        "log_message": "microservices dependency options (high first)",
    },
    "soa_event_driven": {
        "aliases": {
            "soa",
            "service_oriented_architecture",
            "service-oriented",
            "event_driven",
            "event-driven_architecture",
            "event-driven",
        },
        "order": ["moderate", "high", "very_high", "low", "minimal", "unknown"],
        "log_message": "SOA/Event-Driven dependency options (moderate first)",
    },
    "layered": {
        "aliases": {"n_tier", "n-tier", "ntier", "layered_architecture", "tiered"},
        "order": ["low", "moderate", "minimal", "high", "very_high", "unknown"],
        "log_message": "layered/N-tier dependency options (low first)",
    },
    "serverless": {
        "aliases": {"serverless_function", "function_based", "lambda", "faas"},
        "order": ["minimal", "low", "moderate", "high", "very_high", "unknown"],
        "log_message": "serverless dependency options (minimal first)",
    },
    "hybrid": {
        "aliases": {"hybrid_architecture", "mixed"},
        "order": ["moderate", "low", "high", "minimal", "very_high", "unknown"],
        "log_message": "hybrid architecture dependency options (moderate first)",
    },
}

# Build a flat map from alias to config key for quick lookup
PATTERN_MAP = {
    alias: key
    for key, config in ARCHITECTURE_CONFIG.items()
    for alias in config["aliases"] | {key}
}


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

    # Look up configuration based on pattern
    config_key = PATTERN_MAP.get(architecture_pattern)

    if config_key:
        config = ARCHITECTURE_CONFIG[config_key]
        options = [ALL_OPTIONS[value] for value in config["order"]]
        logger.info(
            f"Providing {config['log_message']} for architecture_pattern: {architecture_pattern}"
        )
        return "select", options

    # If architecture_pattern is present but doesn't match patterns, return None
    return None
