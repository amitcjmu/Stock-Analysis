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
        """Entry point for background processor execution."""

        category_normalized = (import_category or "cmdb_export").lower()

        if category_normalized == "cmdb_export":
            logger.info(
                "CMDB import detected; delegating to legacy discovery background executor."
            )
            await self.background_service.start_background_flow_execution(
                flow_id=master_flow_id, file_data=raw_records, context=context
            )
            return

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
                await update_flow_status(
                    flow_id=master_flow_id,
                    status="failed",
                    phase_data={
                        "error": "Validation failed",
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
            logger.error(
                "Background import processor error for %s (category=%s): %s",
                master_flow_id,
                import_category,
                exc,
                exc_info=True,
            )
            await update_flow_status(
                flow_id=master_flow_id,
                status="failed",
                phase_data={
                    "error": str(exc),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context=context,
            )
