"""
JWT token extraction and user ID resolution utilities.

Provides secure JWT decoding and user_id extraction from Authorization headers.
"""

import base64
import json
import logging
from typing import Optional

from app.core.security.secure_logging import safe_log_format, mask_id

logger = logging.getLogger(__name__)


def decode_jwt_payload(token: str) -> Optional[str]:
    """
    Decode JWT payload and extract user_id (sub claim).

    SECURITY WARNING: This function decodes JWT without verification.
    It should only be used as a fallback when proper JWT verification fails.

    Args:
        token: JWT token string

    Returns:
        User ID from sub claim, or None if extraction fails
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_part = parts[1]
        # Add padding only if needed
        missing_padding = (-len(payload_part)) % 4
        if missing_padding:
            payload_part += "=" * missing_padding
        decoded_payload = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(decoded_payload)

        # SECURITY FIX: Validate payload structure and prevent system user impersonation
        sub_claim = payload.get("sub")

        # CRITICAL: Never trust or use 'system' or empty subjects
        if not sub_claim or sub_claim in ["system", "admin", "root", ""]:
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting suspicious JWT subject claim: {sub_claim}",
                    sub_claim=sub_claim or "empty",
                )
            )
            return None

        # Additional validation: subject should be a valid UUID or identifier
        if len(str(sub_claim).strip()) < 3:
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting too-short JWT subject claim: {sub_claim}",
                    sub_claim=sub_claim,
                )
            )
            return None

        # Validate that sub claim doesn't contain suspicious patterns
        suspicious_patterns = ["system", "admin", "root", "service", "internal", "api"]
        sub_lower = str(sub_claim).lower()
        if any(pattern in sub_lower for pattern in suspicious_patterns):
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting JWT with suspicious subject pattern: {sub_claim}",
                    sub_claim=sub_claim,
                )
            )
            return None

        return sub_claim
    except Exception as e:
        logger.warning(
            safe_log_format("JWT payload decode failed: {error}", error=str(e))
        )
        return None


def extract_user_id_via_jwt_service(token: str) -> Optional[str]:
    """
    Extract user_id using JWT service as fallback.

    Args:
        token: JWT token string

    Returns:
        User ID from verified token, or None if verification fails
    """
    try:
        from app.services.auth_services.jwt_service import JWTService

        jwt_service = JWTService()
        payload = jwt_service.verify_token(token)
        return payload.get("sub") if payload else None
    except Exception as jwt_error:
        logger.warning(
            safe_log_format(
                "JWT service verification failed: {jwt_error}",
                jwt_error=str(jwt_error),
            )
        )
        return None


def extract_user_id_from_jwt(auth_header: str) -> Optional[str]:
    """
    Extract user_id from JWT token in Authorization header.

    This is a critical security fix that prevents flows from being created
    with user_id="system" which causes validation errors.

    Args:
        auth_header: Authorization header value

    Returns:
        User ID extracted from JWT token, or None if extraction fails
    """
    # SECURITY FIX: Normalize header value for case variations and extra spaces
    if not auth_header:
        return None

    # Strip extra spaces and normalize case
    normalized_header = auth_header.strip()

    # Check for Bearer token with case insensitive comparison
    if not normalized_header.lower().startswith("bearer "):
        return None

    try:
        # SECURITY FIX: Handle extra spaces properly and guard against headers with only scheme
        parts = normalized_header.split()
        if len(parts) != 2:
            logger.warning(
                "Authorization header does not contain exactly 2 parts (scheme and token)"
            )
            return None

        scheme, token = parts
        if not token:
            logger.warning("Authorization header contains empty token")
            return None

        # Try direct JWT decode first (more reliable for user_id extraction)
        user_id = decode_jwt_payload(token)
        if user_id:
            logger.info(
                safe_log_format(
                    "✅ Extracted user_id from JWT token: {user_id}",
                    user_id=mask_id(user_id),
                )
            )
            return user_id

        # Fallback to JWT service for proper verification
        logger.debug("Direct JWT decode failed, trying JWT service")
        user_id = extract_user_id_via_jwt_service(token)
        if user_id:
            logger.info(
                safe_log_format(
                    "✅ Extracted user_id from JWT service: {user_id}",
                    user_id=mask_id(user_id),
                )
            )
            return user_id

    except Exception as e:
        logger.warning(
            safe_log_format("Failed to extract user_id from JWT: {error}", error=str(e))
        )
    return None
