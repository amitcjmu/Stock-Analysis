"""
Feature flag system for controlling access to experimental or beta features.

This module provides decorators and utilities for feature-gated endpoints
following enterprise patterns for gradual rollouts and A/B testing.
"""

import logging
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
    "collection.gaps.conflict_detection": True,  # Enable conflict detection features
    "collection.gaps.advanced_analytics": False,  # Future analytics features
    # Other feature flags can be added here
    "experimental.ai_recommendations": False,
    "beta.enhanced_reporting": False,
}

# Features that are permanently enabled (cannot be disabled)
PERMANENT_FEATURES: Set[str] = {
    "collection.gaps.v1",  # Core Collection Gaps Phase 2 functionality
}


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        feature_name: The name of the feature to check

    Returns:
        True if the feature is enabled, False otherwise
    """
    # Permanent features are always enabled
    if feature_name in PERMANENT_FEATURES:
        return True

    # Check configured feature flags
    enabled = FEATURE_FLAGS.get(feature_name, False)

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
