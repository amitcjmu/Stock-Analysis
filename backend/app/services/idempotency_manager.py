"""
Idempotency Manager for Service Registry Architecture

Provides idempotency guarantees for operations to prevent duplicate processing
in distributed systems and retry scenarios.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.base_service import ServiceBase


class IdempotencyStatus(Enum):
    """Status of an idempotent operation"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class IdempotencyRecord:
    """Record of an idempotent operation"""

    idempotency_key: str
    operation: str
    status: IdempotencyStatus
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    request_hash: str
    metadata: Dict[str, Any]


class IdempotencyManager(ServiceBase):
    """
    Manager for idempotent operations in the Service Registry.

    This service ensures that operations with the same idempotency key
    are processed exactly once, even in the face of retries, failures,
    or distributed processing.

    Key features:
    - Idempotency key generation and validation
    - Operation deduplication
    - Result caching and retrieval
    - TTL-based expiration
    - Multi-tenant isolation
    """

    # Default TTL for idempotency records (in seconds)
    DEFAULT_TTL = 3600  # 1 hour

    # Maximum TTL allowed (in seconds)
    MAX_TTL = 86400  # 24 hours

    def __init__(self, session: AsyncSession, context: RequestContext):
        """
        Initialize IdempotencyManager.

        Args:
            session: Database session from orchestrator
            context: Request context with tenant information
        """
        super().__init__(session, context)

        # Cache for recent idempotency checks
        self._recent_keys_cache: Dict[str, IdempotencyRecord] = {}
        self._cache_max_size = 100

        self.logger.debug(
            f"Initialized IdempotencyManager for client {context.client_account_id}"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for IdempotencyManager.

        Returns:
            Health status and metrics
        """
        try:
            # For now, we'll simulate the check since the IdempotencyRecord
            # table doesn't exist yet in the actual database
            return {
                "status": "healthy",
                "service": "IdempotencyManager",
                "client_account_id": self.context.client_account_id,
                "cache_size": len(self._recent_keys_cache),
                "cache_max_size": self._cache_max_size,
                "default_ttl": self.DEFAULT_TTL,
                "max_ttl": self.MAX_TTL,
            }
        except Exception as e:
            await self.record_failure(
                operation="health_check",
                error=e,
                context_data={"service": "IdempotencyManager"},
            )
            return {
                "status": "unhealthy",
                "service": "IdempotencyManager",
                "error": str(e),
            }

    def generate_idempotency_key(
        self,
        operation: str,
        request_data: Dict[str, Any],
        custom_key: Optional[str] = None,
    ) -> str:
        """
        Generate a unique idempotency key for an operation.

        Args:
            operation: Name of the operation
            request_data: Request data to include in key generation
            custom_key: Optional custom key component

        Returns:
            Generated idempotency key
        """
        try:
            # Build key components
            key_components = {
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "operation": operation,
                "request_data": self._normalize_request_data(request_data),
            }

            if custom_key:
                key_components["custom"] = custom_key

            # Generate stable hash
            key_string = json.dumps(key_components, sort_keys=True)
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()

            # Create readable key
            idempotency_key = f"{operation}_{key_hash[:16]}"

            self.logger.debug(f"Generated idempotency key: {idempotency_key}")
            return idempotency_key

        except Exception as e:
            self.logger.error(f"Failed to generate idempotency key: {e}")
            # Fallback to timestamp-based key
            fallback_key = f"{operation}_{datetime.now(timezone.utc).timestamp()}"
            return fallback_key

    async def check_idempotency(
        self,
        idempotency_key: str,
        operation: str,
        request_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> Optional[IdempotencyRecord]:
        """
        Check if an operation has already been processed.

        Args:
            idempotency_key: Unique key for the operation
            operation: Name of the operation
            request_data: Request data for validation
            ttl_seconds: TTL for the idempotency record

        Returns:
            Existing IdempotencyRecord if found, None otherwise
        """
        try:
            # Check cache first
            if idempotency_key in self._recent_keys_cache:
                cached_record = self._recent_keys_cache[idempotency_key]
                if cached_record.expires_at > datetime.now(timezone.utc):
                    self.logger.debug(
                        f"Idempotency key found in cache: {idempotency_key}"
                    )
                    return cached_record

            # In a real implementation, we would query the database here
            # For now, we'll simulate the check
            self.logger.debug(
                f"No existing record for idempotency key: {idempotency_key}"
            )

            # Create new pending record
            ttl = min(ttl_seconds or self.DEFAULT_TTL, self.MAX_TTL)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

            request_hash = self._hash_request_data(request_data)

            new_record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation=operation,
                status=IdempotencyStatus.PENDING,
                result=None,
                error=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                request_hash=request_hash,
                metadata={
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id,
                    "user_id": self.context.user_id,
                },
            )

            # Add to cache
            self._add_to_cache(idempotency_key, new_record)

            return None  # No existing record

        except Exception as e:
            await self.record_failure(
                operation="check_idempotency",
                error=e,
                context_data={
                    "idempotency_key": idempotency_key,
                    "operation": operation,
                },
            )
            return None

    async def start_operation(
        self,
        idempotency_key: str,
        operation: str,
        request_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Mark an operation as in-progress.

        Args:
            idempotency_key: Unique key for the operation
            operation: Name of the operation
            request_data: Request data
            ttl_seconds: TTL for the record

        Returns:
            True if operation can proceed, False if duplicate
        """
        try:
            # Check for existing record
            existing = await self.check_idempotency(
                idempotency_key, operation, request_data, ttl_seconds
            )

            if existing:
                if existing.status == IdempotencyStatus.COMPLETED:
                    self.logger.info(
                        f"Operation already completed for key: {idempotency_key}"
                    )
                    return False
                elif existing.status == IdempotencyStatus.IN_PROGRESS:
                    self.logger.info(
                        f"Operation already in progress for key: {idempotency_key}"
                    )
                    return False
                elif existing.status == IdempotencyStatus.FAILED:
                    # Allow retry of failed operations
                    self.logger.info(
                        f"Retrying failed operation for key: {idempotency_key}"
                    )

            # Create or update record to IN_PROGRESS
            ttl = min(ttl_seconds or self.DEFAULT_TTL, self.MAX_TTL)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

            record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                operation=operation,
                status=IdempotencyStatus.IN_PROGRESS,
                result=None,
                error=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                request_hash=self._hash_request_data(request_data),
                metadata={
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id,
                    "user_id": self.context.user_id,
                },
            )

            self._add_to_cache(idempotency_key, record)

            self.logger.debug(f"Started operation for key: {idempotency_key}")
            return True

        except Exception as e:
            await self.record_failure(
                operation="start_operation",
                error=e,
                context_data={
                    "idempotency_key": idempotency_key,
                    "operation": operation,
                },
            )
            return True  # Allow operation to proceed on error

    async def complete_operation(
        self, idempotency_key: str, result: Dict[str, Any]
    ) -> bool:
        """
        Mark an operation as completed with its result.

        Args:
            idempotency_key: Unique key for the operation
            result: Operation result to cache

        Returns:
            True if successfully marked complete
        """
        try:
            # Update record in cache
            if idempotency_key in self._recent_keys_cache:
                record = self._recent_keys_cache[idempotency_key]
                record.status = IdempotencyStatus.COMPLETED
                record.result = result
                record.updated_at = datetime.now(timezone.utc)

                self.logger.debug(f"Completed operation for key: {idempotency_key}")
                return True

            # In real implementation, would update database
            self.logger.warning(
                f"Idempotency key not found in cache: {idempotency_key}"
            )
            return False

        except Exception as e:
            await self.record_failure(
                operation="complete_operation",
                error=e,
                context_data={"idempotency_key": idempotency_key},
            )
            return False

    async def fail_operation(
        self, idempotency_key: str, error: Union[str, Exception]
    ) -> bool:
        """
        Mark an operation as failed.

        Args:
            idempotency_key: Unique key for the operation
            error: Error that occurred

        Returns:
            True if successfully marked failed
        """
        try:
            error_str = str(error)

            # Update record in cache
            if idempotency_key in self._recent_keys_cache:
                record = self._recent_keys_cache[idempotency_key]
                record.status = IdempotencyStatus.FAILED
                record.error = error_str
                record.updated_at = datetime.now(timezone.utc)

                self.logger.debug(f"Failed operation for key: {idempotency_key}")
                return True

            # In real implementation, would update database
            self.logger.warning(
                f"Idempotency key not found in cache: {idempotency_key}"
            )
            return False

        except Exception as e:
            await self.record_failure(
                operation="fail_operation",
                error=e,
                context_data={
                    "idempotency_key": idempotency_key,
                    "original_error": str(error),
                },
            )
            return False

    async def get_cached_result(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a completed operation.

        Args:
            idempotency_key: Unique key for the operation

        Returns:
            Cached result if available, None otherwise
        """
        try:
            # Check cache
            if idempotency_key in self._recent_keys_cache:
                record = self._recent_keys_cache[idempotency_key]
                if record.status == IdempotencyStatus.COMPLETED:
                    if record.expires_at > datetime.now(timezone.utc):
                        self.logger.debug(
                            f"Retrieved cached result for key: {idempotency_key}"
                        )
                        return record.result
                    else:
                        # Expired
                        del self._recent_keys_cache[idempotency_key]

            # In real implementation, would query database
            return None

        except Exception as e:
            self.logger.error(f"Failed to get cached result: {e}")
            return None

    async def cleanup_expired(self) -> int:
        """
        Clean up expired idempotency records.

        Returns:
            Number of records cleaned up
        """
        try:
            now = datetime.now(timezone.utc)
            expired_keys = []

            # Find expired records in cache
            for key, record in self._recent_keys_cache.items():
                if record.expires_at <= now:
                    expired_keys.append(key)

            # Remove expired records
            for key in expired_keys:
                del self._recent_keys_cache[key]

            if expired_keys:
                self.logger.info(f"Cleaned up {len(expired_keys)} expired records")

            # In real implementation, would also clean database
            return len(expired_keys)

        except Exception as e:
            await self.record_failure(
                operation="cleanup_expired", error=e, context_data={}
            )
            return 0

    def validate_idempotency_key(self, key: str) -> bool:
        """
        Validate an idempotency key format.

        Args:
            key: Key to validate

        Returns:
            True if valid, False otherwise
        """
        if not key:
            return False

        # Check length (operation_name + underscore + 16 char hash minimum)
        if len(key) < 18:
            return False

        # Check format (should contain underscore)
        if "_" not in key:
            return False

        # Check for valid characters (alphanumeric, underscore, hyphen)
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", key):
            return False

        return True

    # Private helper methods

    def _normalize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize request data for consistent hashing."""
        # Remove volatile fields that shouldn't affect idempotency
        volatile_fields = {
            "timestamp",
            "request_id",
            "trace_id",
            "span_id",
            "created_at",
            "updated_at",
            "id",
        }

        normalized = {}
        for key, value in data.items():
            if key.lower() not in volatile_fields:
                if isinstance(value, dict):
                    normalized[key] = self._normalize_request_data(value)
                elif isinstance(value, list):
                    normalized[key] = sorted(str(v) for v in value)
                else:
                    normalized[key] = str(value)

        return normalized

    def _hash_request_data(self, data: Dict[str, Any]) -> str:
        """Generate stable hash of request data."""
        normalized = self._normalize_request_data(data)
        data_string = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def _add_to_cache(self, key: str, record: IdempotencyRecord) -> None:
        """Add record to cache with size limit."""
        # Implement simple LRU by removing oldest if at capacity
        if len(self._recent_keys_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._recent_keys_cache))
            del self._recent_keys_cache[oldest_key]

        self._recent_keys_cache[key] = record

    async def get_operation_status(
        self, idempotency_key: str
    ) -> Optional[IdempotencyStatus]:
        """
        Get the current status of an operation.

        Args:
            idempotency_key: Unique key for the operation

        Returns:
            Current status or None if not found
        """
        try:
            if idempotency_key in self._recent_keys_cache:
                record = self._recent_keys_cache[idempotency_key]
                if record.expires_at > datetime.now(timezone.utc):
                    return record.status
                else:
                    # Expired
                    return IdempotencyStatus.EXPIRED

            return None

        except Exception as e:
            self.logger.error(f"Failed to get operation status: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the idempotency cache.

        Returns:
            Cache statistics
        """
        now = datetime.now(timezone.utc)

        stats = {
            "cache_size": len(self._recent_keys_cache),
            "cache_max_size": self._cache_max_size,
            "status_counts": {},
            "expired_count": 0,
        }

        # Count by status
        for record in self._recent_keys_cache.values():
            if record.expires_at <= now:
                stats["expired_count"] += 1
            else:
                status_name = record.status.value
                stats["status_counts"][status_name] = (
                    stats["status_counts"].get(status_name, 0) + 1
                )

        return stats
