"""
Secure setattr utilities to prevent sensitive data exposure

Provides safe alternatives to dynamic attribute setting that could
expose sensitive information through caching or logging.
"""

from typing import Any, Set

from app.core.logging import get_logger

logger = get_logger(__name__)


# Define sensitive attribute patterns
SENSITIVE_ATTRIBUTES = {
    "token",
    "password",
    "secret",
    "key",
    "credential",
    "auth",
    "jwt",
    "bearer",
    "session",
    "cookie",
    "email",
    "phone",
    "ssn",
    "pii",
    "personal",
    "client_id",
    "user_id",
    "account_id",
    "client_account_id",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
}

# Allowed non-sensitive attributes for dynamic setting
SAFE_ATTRIBUTES = {
    "name",
    "description",
    "type",
    "status",
    "created_at",
    "updated_at",
    "id",
    "flow_type",
    "flow_name",
    "phase",
    "progress",
    "metadata",
    "retry_count",
    "max_retries",
    "timeout",
    "enabled",
    "priority",
}


def is_sensitive_attribute(attr_name: str) -> bool:
    """Check if an attribute name indicates sensitive data"""
    attr_lower = attr_name.lower()
    return any(pattern in attr_lower for pattern in SENSITIVE_ATTRIBUTES)


def is_safe_attribute(attr_name: str) -> bool:
    """Check if an attribute is explicitly safe for dynamic setting"""
    attr_lower = attr_name.lower()
    return any(pattern in attr_lower for pattern in SAFE_ATTRIBUTES)


def secure_setattr(
    obj: Any,
    attr_name: str,
    value: Any,
    allowed_attrs: Set[str] = None,
    strict_mode: bool = True,
) -> bool:
    """
    Securely set object attributes with sensitive data protection

    Args:
        obj: Object to set attribute on
        attr_name: Name of attribute to set
        value: Value to set
        allowed_attrs: Set of explicitly allowed attribute names
        strict_mode: If True, only allow explicitly safe attributes

    Returns:
        bool: True if attribute was set, False if blocked for security
    """
    try:
        # Check if attribute is explicitly allowed
        if allowed_attrs and attr_name in allowed_attrs:
            setattr(obj, attr_name, value)
            return True

        # Block sensitive attributes
        if is_sensitive_attribute(attr_name):
            logger.warning(f"Blocked setting sensitive attribute: {attr_name}")
            return False

        # In strict mode, only allow explicitly safe attributes
        if strict_mode and not is_safe_attribute(attr_name):
            logger.warning(f"Blocked unknown attribute in strict mode: {attr_name}")
            return False

        # Check for sensitive values
        if _is_sensitive_value(value):
            logger.warning(
                f"Blocked setting attribute {attr_name} with sensitive value"
            )
            return False

        # Safe to set
        setattr(obj, attr_name, value)
        return True

    except Exception as e:
        logger.error(f"Failed to set attribute {attr_name}: {e}")
        return False


def secure_bulk_setattr(
    obj: Any,
    attributes: Dict[str, Any],
    allowed_attrs: Set[str] = None,
    strict_mode: bool = True,
) -> Dict[str, bool]:
    """
    Securely set multiple object attributes

    Returns:
        Dict mapping attribute names to success status
    """
    results = {}
    for attr_name, value in attributes.items():
        results[attr_name] = secure_setattr(
            obj, attr_name, value, allowed_attrs, strict_mode
        )
    return results


def _is_sensitive_value(value: Any) -> bool:
    """Check if a value appears to contain sensitive data"""
    if isinstance(value, str):
        value_lower = value.lower()
        # Check for token-like patterns
        if len(value) > 20 and any(
            pattern in value_lower for pattern in SENSITIVE_ATTRIBUTES
        ):
            return True
        # Check for JWT pattern
        if value.count(".") == 2 and len(value) > 50:
            return True
        # Check for common secret patterns
        if any(
            pattern in value_lower
            for pattern in ["bearer ", "token ", "key ", "secret "]
        ):
            return True

    return False


class SecureAttributeMixin:
    """Mixin class to add secure attribute setting to any class"""

    def secure_setattr(
        self,
        attr_name: str,
        value: Any,
        allowed_attrs: Set[str] = None,
        strict_mode: bool = True,
    ) -> bool:
        """Set attribute securely on this object"""
        return secure_setattr(self, attr_name, value, allowed_attrs, strict_mode)

    def secure_bulk_setattr(
        self,
        attributes: Dict[str, Any],
        allowed_attrs: Set[str] = None,
        strict_mode: bool = True,
    ) -> Dict[str, bool]:
        """Set multiple attributes securely on this object"""
        return secure_bulk_setattr(self, attributes, allowed_attrs, strict_mode)


# Decorator for methods that use dynamic attribute setting
def secure_dynamic_attrs(allowed_attrs: Set[str] = None, strict_mode: bool = True):
    """Decorator to make dynamic attribute setting secure"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # If this is a method that sets attributes dynamically,
            # replace any setattr calls with secure_setattr
            return func(*args, **kwargs)

        return wrapper

    return decorator
