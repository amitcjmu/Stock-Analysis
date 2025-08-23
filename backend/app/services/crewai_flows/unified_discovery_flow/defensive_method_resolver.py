"""
Defensive Method Resolver

This module provides robust method resolution for field mapping operations
to handle edge cases and dynamic method calls that might cause AttributeError
issues like those described in issue #175.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DefensiveMethodResolver:
    """
    Resolves method calls defensively to handle variations in method names,
    typos, and edge cases that might occur in dynamic environments.
    """

    # Known method name variations for field mapping
    FIELD_MAPPING_METHOD_VARIANTS = {
        "generate_field_mapping_suggestions": [
            "generate_field_mapping_suggestions",  # Correct plural form
            "generate_field_mapping_suggestion",  # Potential typo - singular
            "generate_field_mappings",
            "generate_mapping_suggestions",
            "field_mapping_suggestions",
            "create_field_mapping_suggestions",
            "build_field_mapping_suggestions",
        ],
        "execute_field_mapping": [
            "execute_field_mapping",
            "execute_field_mappings",
            "run_field_mapping",
            "process_field_mapping",
        ],
        "apply_field_mappings": [
            "apply_field_mappings",
            "apply_approved_field_mappings",
            "execute_approved_field_mappings",
            "process_approved_mappings",
        ],
    }

    def __init__(self, target_object: Any):
        """
        Initialize resolver for a specific object.

        Args:
            target_object: The object to resolve methods on
        """
        self.target_object = target_object
        self.method_cache: Dict[str, Optional[Callable]] = {}
        self.available_methods: Set[str] = set()

        # Cache available methods
        self._cache_available_methods()

    def _cache_available_methods(self):
        """Cache all available methods on the target object for fast lookup."""
        try:
            for attr_name in dir(self.target_object):
                if callable(getattr(self.target_object, attr_name, None)):
                    self.available_methods.add(attr_name)

            logger.debug(f"Cached {len(self.available_methods)} available methods")
        except Exception as e:
            logger.warning(f"Failed to cache available methods: {e}")

    def resolve_method(
        self, method_name: str, fallback_variants: Optional[List[str]] = None
    ) -> Optional[Callable]:
        """
        Resolve a method by name, trying variants if the exact name doesn't exist.

        Args:
            method_name: The primary method name to look for
            fallback_variants: Additional variants to try if primary fails

        Returns:
            The resolved method or None if not found
        """
        # Check cache first
        if method_name in self.method_cache:
            cached_method = self.method_cache[method_name]
            if cached_method is not None:
                logger.debug(f"✅ Method '{method_name}' resolved from cache")
                return cached_method

        # Try exact match first
        method = self._try_get_method(method_name)
        if method:
            self.method_cache[method_name] = method
            logger.info(f"✅ Method '{method_name}' resolved exactly")
            return method

        # Get predefined variants
        variants = self._get_method_variants(method_name)

        # Add custom fallback variants
        if fallback_variants:
            variants.extend(fallback_variants)

        # Try variants
        for variant in variants:
            if variant != method_name:  # Skip the already-tried exact match
                method = self._try_get_method(variant)
                if method:
                    self.method_cache[method_name] = method
                    logger.warning(
                        f"⚠️ Method '{method_name}' not found, resolved to variant '{variant}'"
                    )
                    return method

        # Cache negative result to avoid repeated lookups
        self.method_cache[method_name] = None
        logger.error(
            f"❌ Method '{method_name}' could not be resolved with any variant"
        )

        # Log available methods for debugging
        similar_methods = self._find_similar_methods(method_name)
        if similar_methods:
            logger.info(f"💡 Similar methods available: {similar_methods}")

        return None

    def _try_get_method(self, method_name: str) -> Optional[Callable]:
        """
        Try to get a specific method from the target object.

        Args:
            method_name: Name of the method to get

        Returns:
            The method if it exists and is callable, None otherwise
        """
        try:
            # Fast check using cached methods
            if method_name not in self.available_methods:
                return None

            method = getattr(self.target_object, method_name, None)
            if callable(method):
                return method
        except Exception as e:
            logger.debug(f"Exception getting method '{method_name}': {e}")

        return None

    def _get_method_variants(self, method_name: str) -> List[str]:
        """
        Get known variants for a method name.

        Args:
            method_name: The primary method name

        Returns:
            List of known variants
        """
        # Check if this method has predefined variants
        for primary, variants in self.FIELD_MAPPING_METHOD_VARIANTS.items():
            if method_name == primary or method_name in variants:
                return variants.copy()

        # Generate automatic variants
        variants = [method_name]

        # Try common patterns
        if method_name.endswith("s"):
            variants.append(method_name[:-1])  # Remove plural 's'
        else:
            variants.append(method_name + "s")  # Add plural 's'

        if "suggestion" in method_name and not method_name.endswith("s"):
            variants.append(method_name + "s")  # Make suggestions plural
        elif "suggestions" in method_name:
            variants.append(
                method_name.replace("suggestions", "suggestion")
            )  # Make singular

        return variants

    def _find_similar_methods(self, method_name: str) -> List[str]:
        """
        Find methods with similar names for debugging.

        Args:
            method_name: The method name to find similar matches for

        Returns:
            List of similar method names
        """
        similar = []
        keywords = method_name.lower().replace("_", " ").split()

        for available_method in self.available_methods:
            available_lower = available_method.lower()
            # Check if any keywords match
            if any(keyword in available_lower for keyword in keywords):
                similar.append(available_method)

        return sorted(similar)[:5]  # Return top 5 matches

    def resolve_and_call(self, method_name: str, *args, **kwargs) -> Any:
        """
        Resolve a method and call it with the provided arguments.

        Args:
            method_name: The method name to resolve and call
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            The result of the method call

        Raises:
            AttributeError: If the method cannot be resolved
            Exception: Any exception raised by the resolved method
        """
        method = self.resolve_method(method_name)
        if method is None:
            available_methods = self._find_similar_methods(method_name)
            error_msg = f"Method '{method_name}' could not be resolved on {type(self.target_object).__name__}"
            if available_methods:
                error_msg += f". Similar methods available: {available_methods}"
            raise AttributeError(error_msg)

        logger.info(
            f"🎯 Calling resolved method '{method_name}' with {len(args)} args, {len(kwargs)} kwargs"
        )

        try:
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Method '{method_name}' call failed: {e}")
            raise

    def has_method(self, method_name: str) -> bool:
        """
        Check if a method exists (using variants if necessary).

        Args:
            method_name: The method name to check

        Returns:
            True if the method can be resolved, False otherwise
        """
        return self.resolve_method(method_name) is not None

    def get_method_info(self, method_name: str) -> Dict[str, Any]:
        """
        Get diagnostic information about a method resolution.

        Args:
            method_name: The method name to get info for

        Returns:
            Dictionary with method resolution information
        """
        method = self.resolve_method(method_name)
        variants = self._get_method_variants(method_name)
        similar_methods = self._find_similar_methods(method_name)

        return {
            "method_name": method_name,
            "resolved": method is not None,
            "actual_method_name": method.__name__ if method else None,
            "variants_tried": variants,
            "similar_methods": similar_methods,
            "cached": method_name in self.method_cache,
            "target_object_type": type(self.target_object).__name__,
        }


def create_method_resolver(target_object: Any) -> DefensiveMethodResolver:
    """
    Factory function to create a DefensiveMethodResolver.

    Args:
        target_object: The object to create a resolver for

    Returns:
        A new DefensiveMethodResolver instance
    """
    return DefensiveMethodResolver(target_object)


# Convenient utility functions
def safe_method_call(target_object: Any, method_name: str, *args, **kwargs) -> Any:
    """
    Safely call a method with defensive resolution.

    Args:
        target_object: The object to call the method on
        method_name: The method name to call
        *args: Arguments to pass to the method
        **kwargs: Keyword arguments to pass to the method

    Returns:
        The result of the method call

    Raises:
        AttributeError: If the method cannot be resolved
    """
    resolver = create_method_resolver(target_object)
    return resolver.resolve_and_call(method_name, *args, **kwargs)


def has_method(target_object: Any, method_name: str) -> bool:
    """
    Check if an object has a method (using variants if necessary).

    Args:
        target_object: The object to check
        method_name: The method name to check for

    Returns:
        True if the method exists, False otherwise
    """
    resolver = create_method_resolver(target_object)
    return resolver.has_method(method_name)
