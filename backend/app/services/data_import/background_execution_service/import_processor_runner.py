import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger
from app.services.data_import.service_handlers import get_processor_for_category

from .utils import update_flow_status

logger = get_logger(__name__)

_background_processor_tasks = set()


def _sanitize_error_message(exc: Exception, import_category: str) -> str:
    """
    Sanitize exception messages to provide user-friendly, actionable context
    without exposing internal system details.

    Args:
        exc: The exception that occurred
        import_category: The import category being processed

    Returns:
        User-friendly error message
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)

    # Map common exception types to user-friendly messages
    if exc_type == "ValidationError":
        return (
            f"Data validation failed for {import_category} import. "
            "Please check your data format and required fields."
        )
    elif exc_type == "ValueError":
        # Check if it's about missing required fields
        if "required" in exc_message.lower() or "missing" in exc_message.lower():
            return f"Missing required fields in {import_category} import. Please check your data and try again."
        return f"Invalid data format in {import_category} import. Please verify your data structure."
    elif exc_type == "KeyError":
        return f"Missing required field in {import_category} import data. Please check your data structure."
    elif exc_type == "IntegrityError" or exc_type == "UniqueViolationError":
        return (
            f"Duplicate or conflicting data detected in {import_category} import. "
            "Please review your data for duplicates."
        )
    elif exc_type == "ConnectionError" or exc_type == "TimeoutError":
        return f"Database connection issue during {import_category} import. Please try again later."
    elif exc_type == "PermissionError" or "access" in exc_message.lower():
        return f"Access denied for {import_category} import. Please check your permissions."
    elif exc_type == "FileNotFoundError":
        return f"Required file not found for {import_category} import. Please check your file paths."
    elif "normalization" in exc_message.lower() or "parse" in exc_message.lower():
        return f"Data format error in {import_category} import. Please verify your data matches the expected format."
    elif "database" in exc_message.lower() or "sql" in exc_message.lower():
        return f"Database error occurred during {import_category} import. Please try again or contact support."
    else:
        # Generic fallback - don't expose internal details
        return (
            f"An error occurred processing your {import_category} import. "
            "Please check your data and try again. If the issue persists, contact support."
        )


class ImportProcessorBackgroundRunner:
    """Executes category-specific data import processors in the background."""

    def __init__(self, background_service):
        """
        Args:
            background_service: Instance of ``BackgroundExecutionService`` used for
                legacy discovery execution and tenant scoping.
        """

        self.background_service = background_service
        self.db = background_service.db
        self.client_account_id = background_service.client_account_id

    async def start_background_import_execution(
        self,
        master_flow_id: str,
        data_import_id: str,
        raw_records: List[Dict[str, Any]],
        import_category: Optional[str],
        processing_config: Optional[Dict[str, Any]],
        context: RequestContext,
    ) -> None:
        """
        Entry point for background processor execution.

        Unified execution model: All import categories (including cmdb_export) go through
        the processor system. Processors can return delegate_to_legacy=True to use legacy
        execution paths internally, but from the runner's perspective, it's a single unified flow.
        """

        category_normalized = (import_category or "cmdb_export").lower()

        try:
            # Validate lookup before scheduling the task so we can gracefully fallback.
            get_processor_for_category(category_normalized, self.db, context)

            task = asyncio.create_task(
                self._run_import_processor_task(
                    master_flow_id=master_flow_id,
                    data_import_id=data_import_id,
                    raw_records=raw_records,
                    import_category=category_normalized,
                    processing_config=processing_config or {},
                    context=context,
                )
            )
            _background_processor_tasks.add(task)
            task.add_done_callback(_background_processor_tasks.discard)
            await asyncio.sleep(0.1)
        except KeyError:
            logger.warning(
                "No processor registered for category '%s'; falling back to discovery flow executor.",
                import_category,
            )
            await self.background_service.start_background_flow_execution(
                flow_id=master_flow_id, file_data=raw_records, context=context
            )
        except Exception as exc:
            logger.error(
                "Failed to start background import execution for %s: %s",
                master_flow_id,
                exc,
                exc_info=True,
            )
            raise FlowError(f"Failed to start background import execution: {exc}")

    async def _run_import_processor_task(
        self,
        master_flow_id: str,
        data_import_id: str,
        raw_records: List[Dict[str, Any]],
        import_category: str,
        processing_config: Dict[str, Any],
        context: RequestContext,
    ) -> None:
        """Execute the category-specific processor."""

        try:
            await update_flow_status(
                flow_id=master_flow_id,
                status="processing",
                phase_data={
                    "message": f"Starting {import_category} import processing",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context=context,
            )

            processor = get_processor_for_category(import_category, self.db, context)
            if hasattr(processor, "set_flow_context"):
                processor.set_flow_context(
                    master_flow_id=master_flow_id,
                    data_import_id=uuid.UUID(data_import_id),
                )
            data_import_uuid = uuid.UUID(str(data_import_id))
            if hasattr(processor, "set_flow_context"):
                processor.set_flow_context(
                    master_flow_id=master_flow_id,
                    data_import_id=data_import_uuid,
                )
            result = await processor.process(
                data_import_id=data_import_uuid,
                raw_records=raw_records,
                processing_config=processing_config,
            )

            if result.get("delegate_to_legacy"):
                logger.info(
                    "Processor delegated flow %s (category=%s) to legacy discovery executor",
                    master_flow_id,
                    import_category,
                )
                await self.background_service.start_background_flow_execution(
                    flow_id=master_flow_id, file_data=raw_records, context=context
                )
                return

            if result.get("status") != "completed":
                # Extract validation errors if available
                validation = result.get("validation", {})
                validation_errors = validation.get("validation_errors", [])
                error_context = "Validation failed"
                if validation_errors:
                    # Provide actionable context from validation errors
                    if len(validation_errors) == 1:
                        error_context = f"Validation failed: {validation_errors[0]}"
                    else:
                        error_context = (
                            f"Validation failed: {len(validation_errors)} errors found"
                        )

                await update_flow_status(
                    flow_id=master_flow_id,
                    status="failed",
                    phase_data={
                        "error": error_context,
                        "validation": result.get("validation"),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    context=context,
                )
                return

            await update_flow_status(
                flow_id=master_flow_id,
                status="completed",
                phase_data={
                    "message": f"{import_category} import enrichment completed",
                    "validation": result.get("validation"),
                    "enrichment": result.get("enrichment"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context=context,
            )

        except Exception as exc:
            # Log full error details internally for debugging
            logger.error(
                "Background import processor error for flow_id=%s, category=%s, error_type=%s",
                master_flow_id,
                import_category,
                type(exc).__name__,
                exc_info=True,  # Full stack trace in logs
            )

            # Sanitize error message before exposing to users
            sanitized_message = _sanitize_error_message(exc, import_category)

            await update_flow_status(
                flow_id=master_flow_id,
                status="failed",
                phase_data={
                    "error": sanitized_message,
                    "error_type": type(exc).__name__,  # Type only, not full message
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context=context,
            )
