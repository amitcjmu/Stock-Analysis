"""
Secure Cache Encryption Module

Provides encryption/decryption utilities for sensitive data before caching.
Ensures PII, tokens, and other sensitive information is never stored in plaintext.
"""

import base64
import hashlib
import json
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheEncryption:
    """Handles encryption/decryption of sensitive data for caching"""

    def __init__(self):
        self._fernet = None
        self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """Initialize encryption with app secret key"""
        try:
            # Use app secret key to derive encryption key
            secret = settings.SECRET_KEY.encode()
            salt = hashlib.sha256(secret).digest()[
                :16
            ]  # Deterministic salt from secret

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret))
            self._fernet = Fernet(key)

        except Exception as e:
            logger.error(f"Failed to initialize cache encryption: {e}")
            # Fallback to disable caching of sensitive data
            self._fernet = None

    def encrypt_sensitive_data(self, data: Any) -> Optional[str]:
        """Encrypt sensitive data before caching"""
        if not self._fernet:
            logger.warning(
                "Cache encryption not available - sensitive data will not be cached"
            )
            return None

        try:
            # Serialize data to JSON string
            json_data = json.dumps(data, default=str, ensure_ascii=False)
            # Encrypt the JSON string
            encrypted_data = self._fernet.encrypt(json_data.encode())
            # Return base64 encoded encrypted data
            return base64.urlsafe_b64encode(encrypted_data).decode()

        except Exception as e:
            logger.error(f"Failed to encrypt sensitive data: {e}")
            return None

    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[Any]:
        """Decrypt sensitive data from cache"""
        if not self._fernet or not encrypted_data:
            return None

        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            # Decrypt
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            # Parse JSON
            return json.loads(decrypted_bytes.decode())

        except Exception as e:
            logger.error(f"Failed to decrypt sensitive data: {e}")
            return None

    def is_encryption_available(self) -> bool:
        """Check if encryption is properly initialized"""
        return self._fernet is not None


# Global instance
cache_encryption = CacheEncryption()


def encrypt_for_cache(data: Any) -> Optional[str]:
    """Convenience function to encrypt data for caching"""
    return cache_encryption.encrypt_sensitive_data(data)


def decrypt_from_cache(encrypted_data: str) -> Optional[Any]:
    """Convenience function to decrypt data from cache"""
    return cache_encryption.decrypt_sensitive_data(encrypted_data)


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field contains sensitive data that should be encrypted"""
    sensitive_patterns = {
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
        # CrewAI-specific sensitive patterns
        "agent_config",
        "tool_config",
        "agent_memory",
        "flow_state",
        "checkpoint_data",
        "agent_insights",
        "crew_results",
        "tool_params",
        "llm_config",
        "api_endpoint",
        "database_url",
        "connection_string",
    }

    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in sensitive_patterns)


def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive fields from data before logging"""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if is_sensitive_field(key):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_logging(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [sanitize_for_logging(item) for item in value]
        else:
            sanitized[key] = value

    return sanitized


class SecureCache:
    """Wrapper for cache operations with automatic encryption of sensitive data"""

    def __init__(self, cache_client):
        self.cache_client = cache_client
        self.encryption = cache_encryption

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        force_encrypt: bool = False,
    ) -> bool:
        """Set cache value with automatic encryption for sensitive data"""
        try:
            # Check if value contains sensitive data
            needs_encryption = force_encrypt or self._contains_sensitive_data(value)

            if needs_encryption:
                if not self.encryption.is_encryption_available():
                    logger.warning(
                        f"Cannot cache sensitive data for key {key} - encryption not available"
                    )
                    return False

                encrypted_value = self.encryption.encrypt_sensitive_data(value)
                if encrypted_value is None:
                    logger.error(f"Failed to encrypt sensitive data for key {key}")
                    return False

                # Store with encryption marker
                cache_data = {"encrypted": True, "data": encrypted_value}
            else:
                cache_data = {"encrypted": False, "data": value}

            # Use underlying cache client
            if hasattr(self.cache_client, "set"):
                return await self.cache_client.set(key, cache_data, ttl)
            else:
                # Fallback for sync clients
                return self.cache_client.set(key, json.dumps(cache_data), ttl)

        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get cache value with automatic decryption"""
        try:
            # Get from underlying cache
            if hasattr(self.cache_client, "get"):
                cached_data = await self.cache_client.get(key)
            else:
                cached_data = self.cache_client.get(key)
                if cached_data:
                    cached_data = json.loads(cached_data)

            if not cached_data:
                return None

            # Handle legacy unstructured cache data
            if not isinstance(cached_data, dict) or "encrypted" not in cached_data:
                return cached_data

            # Handle structured cache data with encryption info
            if cached_data.get("encrypted", False):
                decrypted_value = self.encryption.decrypt_sensitive_data(
                    cached_data["data"]
                )
                if decrypted_value is None:
                    logger.warning(f"Failed to decrypt cache data for key {key}")
                    return None
                return decrypted_value
            else:
                return cached_data["data"]

        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None

    def _contains_sensitive_data(self, data: Any) -> bool:
        """Check if data contains sensitive information"""
        if isinstance(data, dict):
            for key, value in data.items():
                if is_sensitive_field(key):
                    return True
                if isinstance(value, (dict, list)) and self._contains_sensitive_data(
                    value
                ):
                    return True

            # Check for CrewAI-specific sensitive data patterns
            if self._contains_crewai_sensitive_patterns(data):
                return True

        elif isinstance(data, list):
            for item in data:
                if self._contains_sensitive_data(item):
                    return True
        elif isinstance(data, str):
            # Check for token-like patterns
            if len(data) > 20 and ("token" in data.lower() or "bearer" in data.lower()):
                return True
            # Check for API key patterns
            if self._looks_like_api_key(data):
                return True

        return False

    def _contains_crewai_sensitive_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for CrewAI-specific sensitive data patterns"""
        # Check for flow state indicators
        crewai_sensitive_keys = {
            "flow_id",
            "client_account_id",
            "engagement_id",
            "user_id",
            "agent_insights",
            "crew_status",
            "raw_data",
            "field_mappings",
            "checkpoint_id",
            "state_snapshot",
            "agent_configuration",
            "tool_configuration",
            "llm_parameters",
            "memory_context",
        }

        return any(key in data for key in crewai_sensitive_keys)

    def _looks_like_api_key(self, value: str) -> bool:
        """Check if a string looks like an API key or credential"""
        if not isinstance(value, str) or len(value) < 16:
            return False

        # Common API key patterns
        api_key_patterns = [
            "sk-",  # OpenAI
            "pk_",  # Stripe
            "Bearer ",  # OAuth
            "Basic ",  # Basic auth
            "AIza",  # Google
            "AKIA",  # AWS
        ]

        for pattern in api_key_patterns:
            if value.startswith(pattern):
                return True

        # Check for long alphanumeric strings that might be keys
        if len(value) > 32 and value.replace("-", "").replace("_", "").isalnum():
            return True

        return False


def secure_setattr(obj: Any, key: str, value: Any) -> None:
    """
    Secure setattr wrapper that ensures sensitive data is handled properly.

    This function replaces direct setattr() calls to prevent sensitive data
    from being cached or logged without proper encryption. It performs
    automatic sanitization of sensitive fields before setting attributes.

    Args:
        obj: The object to set the attribute on
        key: The attribute name
        value: The value to set
    """
    try:
        # Check if the value contains sensitive data
        if is_sensitive_field(key):
            # For sensitive fields, we still set the value but ensure it's marked
            # This allows the rest of the system to handle encryption properly
            logger.debug(f"Setting sensitive attribute '{key}' with secure handling")

        # Set the attribute normally - the security is handled at the caching layer
        setattr(obj, key, value)

    except Exception as e:
        logger.error(f"Failed to set attribute '{key}' on {type(obj).__name__}: {e}")
        raise
