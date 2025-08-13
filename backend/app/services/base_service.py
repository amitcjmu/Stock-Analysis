"""
Base Service Class for Service Registry Architecture

This module provides the foundational ServiceBase class that all services in the
Service Registry pattern must inherit from. It ensures consistent patterns for:
- Database session management without direct commits
- Request context propagation
- Failure recording and Dead Letter Queue handling
- Proper error handling and logging

Key principles:
- Services receive AsyncSession and RequestContext from orchestrator
- Services may call flush() for ID generation but NEVER commit() or close()
- Severe failures are recorded and enqueued to DLQ non-blocking
- All database operations remain within orchestrator transaction scope
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    DataError,
    InvalidRequestError,
    TimeoutError as SQLTimeoutError,
)

from app.core.context import RequestContext
from app.core.logging import get_logger


@dataclass
class FailureRecord:
    """Represents a failure to be recorded in the failure journal"""

    timestamp: datetime
    service_name: str
    operation: str
    error_type: str
    error_message: str
    context_data: Dict[str, Any]
    severity: str
    is_recoverable: bool
    retry_count: int = 0
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert failure record to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "operation": self.operation,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "context_data": self.context_data,
            "severity": self.severity,
            "is_recoverable": self.is_recoverable,
            "retry_count": self.retry_count,
            "correlation_id": self.correlation_id,
        }


class ServiceBase(ABC):
    """
    Base class for all services in the Service Registry architecture.

    This class provides:
    - Database session management without commits/closes
    - Request context access and validation
    - Failure recording with Dead Letter Queue integration
    - Consistent error handling and logging patterns
    - Database flush capability for ID generation

    Key Rules:
    1. Services receive AsyncSession and RequestContext from orchestrator
    2. Services may call flush_for_id() but NEVER commit() or close()
    3. All database operations remain within orchestrator transaction scope
    4. Severe failures are automatically recorded and enqueued to DLQ
    """

    # Allowlist of exceptions that are considered "severe" and require DLQ handling
    SEVERE_FAILURE_TYPES: Set[type] = {
        DatabaseError,
        IntegrityError,
        OperationalError,
        DataError,
        InvalidRequestError,
        SQLTimeoutError,
    }

    def __init__(self, session: AsyncSession, context: RequestContext):
        """
        Initialize the service with database session and request context.

        Args:
            session: Active AsyncSession from orchestrator (DO NOT close/commit)
            context: Request context with client, engagement, user info

        Raises:
            ValueError: If session or context is None
        """
        if session is None:
            raise ValueError("Database session is required")
        if context is None:
            raise ValueError("Request context is required")

        self._session = session
        self._context = context
        self._logger = get_logger(self.__class__.__module__)

        # Track service instance for logging and monitoring
        self._service_name = self.__class__.__name__
        self._failure_records: List[FailureRecord] = []

        self._logger.debug(
            f"Initialized {self._service_name}",
            extra={
                "service_name": self._service_name,
                "context_client_id": self._context.client_account_id,
                "context_engagement_id": self._context.engagement_id,
            },
        )

    @property
    def session(self) -> AsyncSession:
        """
        Get the database session.

        WARNING: DO NOT call commit() or close() on this session.
        Use flush_for_id() if you need to generate IDs.
        """
        return self._session

    @property
    def context(self) -> RequestContext:
        """Get the request context"""
        return self._context

    @property
    def logger(self) -> logging.Logger:
        """Get the service logger"""
        return self._logger

    async def flush_for_id(self) -> None:
        """
        Flush the database session to generate IDs without committing.

        This is the ONLY acceptable way for services to flush the session.
        Use this when you need to get auto-generated IDs from the database
        but want to keep the transaction open for the orchestrator.

        Example:
            # Create new record that needs an ID
            new_record = MyModel(name="example")
            self.session.add(new_record)
            await self.flush_for_id()  # Now new_record.id is available
            # Continue with operations using new_record.id
        """
        try:
            await self._session.flush()
            self._logger.debug(
                f"{self._service_name}: Flushed session for ID generation",
                extra={"service_name": self._service_name, "operation": "flush_for_id"},
            )
        except Exception as e:
            await self.record_failure(
                operation="flush_for_id",
                error=e,
                context_data={"operation_type": "database_flush"},
            )
            raise

    async def record_failure(
        self,
        operation: str,
        error: Exception,
        context_data: Optional[Dict[str, Any]] = None,
        is_recoverable: bool = True,
        retry_count: int = 0,
    ) -> None:
        """
        Record a failure in the failure journal and handle severe failures.

        This method:
        1. Creates a failure record with context information
        2. Logs the failure appropriately based on severity
        3. For severe failures, enqueues to DLQ non-blocking
        4. Stores failure record for potential batch processing

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            context_data: Additional context information
            is_recoverable: Whether this failure might be recoverable
            retry_count: Number of retry attempts made
        """
        error_type = type(error).__name__
        error_message = str(error)
        is_severe = self._is_severe_failure(error)

        # Sanitize context data to prevent sensitive information leakage
        safe_context = self._sanitize_context_data(context_data or {})
        safe_context.update(
            {
                "client_account_id": self._context.client_account_id,
                "engagement_id": self._context.engagement_id,
                "flow_id": self._context.flow_id,
                "service_name": self._service_name,
            }
        )

        # Create failure record
        failure_record = FailureRecord(
            timestamp=datetime.now(timezone.utc),
            service_name=self._service_name,
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            context_data=safe_context,
            severity="severe" if is_severe else "moderate",
            is_recoverable=is_recoverable,
            retry_count=retry_count,
            correlation_id=self._context.request_id,
        )

        # Store failure record
        self._failure_records.append(failure_record)

        # Log the failure with appropriate level
        log_level = "error" if is_severe else "warning"
        self._logger.__getattribute__(log_level)(
            f"{self._service_name} operation '{operation}' failed: {error_message}",
            extra={
                "service_name": self._service_name,
                "operation": operation,
                "error_type": error_type,
                "severity": failure_record.severity,
                "is_recoverable": is_recoverable,
                "retry_count": retry_count,
                "correlation_id": failure_record.correlation_id,
                "context_data": safe_context,
            },
        )

        # For severe failures, enqueue to DLQ non-blocking
        if is_severe:
            try:
                await self._enqueue_to_dlq(failure_record)
            except Exception as dlq_error:
                # DLQ enqueueing failures should not break the main flow
                self._logger.error(
                    f"Failed to enqueue severe failure to DLQ: {dlq_error}",
                    extra={
                        "service_name": self._service_name,
                        "original_failure": failure_record.to_dict(),
                        "dlq_error": str(dlq_error),
                    },
                )

    def _is_severe_failure(self, error: Exception) -> bool:
        """
        Determine if a failure is severe using allowlist approach.

        Severe failures are those that indicate system-level issues
        that require immediate attention and DLQ processing.

        Args:
            error: The exception to evaluate

        Returns:
            True if the error is considered severe
        """
        return type(error) in self.SEVERE_FAILURE_TYPES

    async def _enqueue_to_dlq(self, failure_record: FailureRecord) -> None:
        """
        Enqueue severe failure to Dead Letter Queue non-blocking.

        This is implemented as a fire-and-forget operation using asyncio.create_task
        to ensure that DLQ failures don't impact the main service operation.

        Args:
            failure_record: The failure record to enqueue
        """
        # Create non-blocking task for DLQ enqueueing
        task = asyncio.create_task(
            self._perform_dlq_enqueue(failure_record),
            name=f"dlq_enqueue_{self._service_name}_{failure_record.correlation_id}",
        )

        # Log that DLQ enqueueing was initiated
        self._logger.info(
            f"Initiated DLQ enqueueing for severe failure in {self._service_name}",
            extra={
                "service_name": self._service_name,
                "failure_correlation_id": failure_record.correlation_id,
                "task_name": task.get_name(),
            },
        )

        # Note: We don't await the task - it runs in background
        # This ensures DLQ operations don't block service execution

    async def _perform_dlq_enqueue(self, failure_record: FailureRecord) -> None:
        """
        Perform the actual DLQ enqueueing operation.

        Integrates with:
        1. failure_journal for persistence
        2. ErrorRecoverySystem for DLQ processing

        Args:
            failure_record: The failure record to enqueue
        """
        try:
            # First, persist to failure journal
            from app.services.integration.failure_journal import log_failure
            
            await log_failure(
                self._session,
                client_account_id=str(self._context.client_account_id) if self._context.client_account_id else None,
                engagement_id=str(self._context.engagement_id) if self._context.engagement_id else None,
                source=self._service_name,
                operation=failure_record.operation,
                payload={
                    "service": self._service_name,
                    "context_data": failure_record.context_data,
                    "retry_count": failure_record.retry_count,
                },
                error_message=failure_record.error_message,
                trace=None,  # Could add stack trace if needed
            )
            
            # Then enqueue to ErrorRecoverySystem DLQ (if available)
            try:
                from app.services.recovery.error_recovery_system import (
                    ErrorRecoverySystem,
                    get_error_recovery_system,
                    RecoveryOperation,
                )
                
                recovery_system = get_error_recovery_system()
                if recovery_system and hasattr(recovery_system, 'enqueue_to_dlq'):
                    operation = RecoveryOperation(
                        id=failure_record.correlation_id or str(uuid.uuid4()),
                        operation_type=failure_record.operation,
                        payload=failure_record.context_data,
                        max_retries=3,
                        current_attempt=failure_record.retry_count,
                        last_error=failure_record.error_message,
                        created_at=failure_record.timestamp,
                    )
                    await recovery_system.enqueue_to_dlq(operation)
                    
                    self._logger.info(
                        f"DLQ: Enqueued severe failure from {self._service_name} to ErrorRecoverySystem",
                        extra={
                            "service_name": self._service_name,
                            "operation_id": operation.id,
                        },
                    )
            except ImportError:
                # ErrorRecoverySystem not available, failure journal is sufficient
                pass
                
        except Exception as e:
            # Log DLQ failures but don't propagate them
            self._logger.error(
                f"DLQ enqueueing failed for {self._service_name}: {e}",
                extra={
                    "service_name": self._service_name,
                    "dlq_error": str(e),
                    "original_failure": failure_record.to_dict(),
                },
            )

    def _sanitize_context_data(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context data to remove sensitive information.

        Args:
            context_data: Raw context data that may contain sensitive info

        Returns:
            Sanitized context data safe for logging and storage
        """
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "key",
            "auth",
            "credential",
            "private",
            "confidential",
            "sensitive",
            "api_key",
            "bearer",
        }

        sanitized = {}
        for key, value in context_data.items():
            key_lower = key.lower()

            # Check if key contains sensitive terms
            is_sensitive = any(
                sensitive_term in key_lower for sensitive_term in sensitive_keys
            )

            if is_sensitive:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self._sanitize_context_data(value)
            elif isinstance(value, (list, tuple)):
                # Handle lists/tuples that might contain dicts
                sanitized[key] = [
                    (
                        self._sanitize_context_data(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def get_failure_summary(self) -> Dict[str, Any]:
        """
        Get a summary of failures recorded by this service instance.

        Returns:
            Dictionary containing failure statistics and recent failures
        """
        if not self._failure_records:
            return {
                "total_failures": 0,
                "severe_failures": 0,
                "recent_failures": [],
            }

        severe_count = sum(1 for f in self._failure_records if f.severity == "severe")

        # Get last 5 failures for summary
        recent_failures = [
            {
                "timestamp": f.timestamp.isoformat(),
                "operation": f.operation,
                "error_type": f.error_type,
                "severity": f.severity,
                "correlation_id": f.correlation_id,
            }
            for f in self._failure_records[-5:]
        ]

        return {
            "service_name": self._service_name,
            "total_failures": len(self._failure_records),
            "severe_failures": severe_count,
            "recent_failures": recent_failures,
        }

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform service-specific health check.

        Each service must implement this method to provide health status
        including any service-specific metrics or validation checks.

        Returns:
            Dictionary containing health status and metrics
        """
        pass
