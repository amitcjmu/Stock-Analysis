"""
Feature flag system for controlling access to experimental or beta features.

This module provides decorators and utilities for feature-gated endpoints
following enterprise patterns for gradual rollouts and A/B testing.
"""

import logging
import os
from functools import wraps
from typing import Dict, Set
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Feature flags configuration
# In production, this would typically come from environment variables,
# a configuration service, or a feature flag management system
FEATURE_FLAGS: Dict[str, bool] = {
    # Collection Gaps Phase 2 features
    "collection.gaps.v1": True,  # Enable asset-agnostic collection endpoints
    "collection.gaps.v2": True,  # Enable asset selection and enhanced questionnaires
    "collection.gaps.v2_agent_questionnaires": True,  # Use agent-driven questionnaire generation
    "collection.gaps.bootstrap_fallback": True,  # Allow bootstrap fallback if agent times out
    "collection.gaps.skip_tier3_no_gaps": False,  # Allow TIER_3 to skip when no gaps
    "collection.gaps.conflict_detection": True,  # Enable conflict detection features
    "collection.gaps.advanced_analytics": False,  # Future analytics features
    # Other feature flags can be added here
    "experimental.ai_recommendations": False,
    "beta.enhanced_reporting": False,
}

# Features that are permanently enabled (cannot be disabled)
PERMANENT_FEATURES: Set[str] = {
    "collection.gaps.v1",  # Core Collection Gaps Phase 2 functionality
    "collection.gaps.v2",  # Asset selection and enhanced questionnaires
}


def is_feature_enabled(feature_name: str, default: bool = False) -> bool:
    """
    Check if a feature flag is enabled with environment variable override support.

    Environment variables override configured flags using the pattern:
    FEATURE_FLAG_<FEATURE_NAME> where dots are replaced with underscores and uppercased.
    Example: collection.gaps.v2 -> FEATURE_FLAG_COLLECTION_GAPS_V2

    Args:
        feature_name: The name of the feature to check
        default: Default value if feature flag not found

    Returns:
        True if the feature is enabled, False otherwise
    """
    # Permanent features are always enabled
    if feature_name in PERMANENT_FEATURES:
        return True

    # Check for environment variable override
    env_var_name = f"FEATURE_FLAG_{feature_name.replace('.', '_').upper()}"
    env_override = os.getenv(env_var_name)

    if env_override is not None:
        # Parse environment override (support various formats)
        env_enabled = env_override.lower() in ["true", "1", "yes", "on", "enabled"]
        logger.debug(
            f"Feature flag '{feature_name}' overridden by {env_var_name}={env_override} -> {env_enabled}"
        )
        return env_enabled

    # Check configured feature flags
    enabled = FEATURE_FLAGS.get(feature_name, default)

    logger.debug(f"Feature flag check: '{feature_name}' = {enabled}")
    return enabled


def require_feature(feature_name: str):
    """
    Decorator to require a feature flag to be enabled for an endpoint.

    If the feature is disabled, returns a 404 Not Found response to hide
    the existence of the endpoint from unauthorized users.

    Args:
        feature_name: The name of the feature flag to check

    Returns:
        Decorator function that checks the feature flag

    Raises:
        HTTPException: 404 Not Found if feature is disabled
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_feature_enabled(feature_name):
                logger.warning(
                    f"Access denied to disabled feature '{feature_name}' "
                    f"for endpoint {func.__name__}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_enabled_features() -> Dict[str, bool]:
    """
    Get all currently enabled features.

    Returns:
        Dictionary of feature names and their enabled status
    """
    return {name: is_feature_enabled(name) for name in FEATURE_FLAGS}


def enable_feature(feature_name: str) -> bool:
    """
    Enable a feature flag at runtime.

    Args:
        feature_name: The name of the feature to enable

    Returns:
        True if feature was enabled, False if it was already enabled
    """
    if feature_name in FEATURE_FLAGS:
        was_enabled = FEATURE_FLAGS[feature_name]
        FEATURE_FLAGS[feature_name] = True

        if not was_enabled:
            logger.info(f"Feature '{feature_name}' enabled at runtime")
            return True
    else:
        # Add new feature flag
        FEATURE_FLAGS[feature_name] = True
        logger.info(f"New feature '{feature_name}' added and enabled")
        return True

    return False


def disable_feature(feature_name: str) -> bool:
    """
    Disable a feature flag at runtime.

    Args:
        feature_name: The name of the feature to disable

    Returns:
        True if feature was disabled, False if it was already disabled

    Raises:
        ValueError: If trying to disable a permanent feature
    """
    if feature_name in PERMANENT_FEATURES:
        raise ValueError(f"Cannot disable permanent feature '{feature_name}'")

    if feature_name in FEATURE_FLAGS:
        was_enabled = FEATURE_FLAGS[feature_name]
        FEATURE_FLAGS[feature_name] = False

        if was_enabled:
            logger.info(f"Feature '{feature_name}' disabled at runtime")
            return True

    return False


def log_feature_flags() -> None:
    """
    Log current feature flag configuration for startup audit trail.

    Logs both configured flags and any environment overrides for observability.
    """
    logger.info("🚩 Feature Flags Configuration:")

    # Log configured feature flags
    for feature_name, default_value in FEATURE_FLAGS.items():
        # Check if environment override exists
        env_var_name = f"FEATURE_FLAG_{feature_name.replace('.', '_').upper()}"
        env_override = os.getenv(env_var_name)

        if env_override is not None:
            env_enabled = env_override.lower() in ["true", "1", "yes", "on", "enabled"]
            logger.info(
                f"  {feature_name}: {env_enabled} "
                f"(ENV override: {env_var_name}={env_override}, default: {default_value})"
            )
        else:
            logger.info(f"  {feature_name}: {default_value}")

    # Log permanent features
    if PERMANENT_FEATURES:
        logger.info("🔒 Permanent Features (always enabled):")
        for feature_name in sorted(PERMANENT_FEATURES):
            logger.info(f"  {feature_name}: True (permanent)")

    # Check for unknown environment overrides
    unknown_overrides = []
    for env_var in os.environ:
        if env_var.startswith("FEATURE_FLAG_"):
            # Convert back to feature name
            feature_name = (
                env_var.replace("FEATURE_FLAG_", "").replace("_", ".").lower()
            )
            if (
                feature_name not in FEATURE_FLAGS
                and feature_name not in PERMANENT_FEATURES
            ):
                unknown_overrides.append((env_var, os.getenv(env_var)))

    if unknown_overrides:
        logger.warning("⚠️ Unknown feature flag environment overrides detected:")
        for env_var, value in unknown_overrides:
            logger.warning(f"  {env_var}={value}")

    logger.info("✅ Feature flag configuration loaded successfully")
