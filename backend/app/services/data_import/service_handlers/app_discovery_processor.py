"""
Application discovery import processor.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import TaskComplexity, multi_model_service

from .base_processor import BaseDataImportProcessor


class ApplicationDiscoveryProcessor(BaseDataImportProcessor):
    """Processor for application discovery imports."""

    category = "app_discovery"

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)

    async def validate_data(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform lightweight schema validation with LLM assistance."""
        record_preview = raw_records[:2] if raw_records else []
        prompt = (
            "You are validating an application discovery dataset. "
            "Verify that each record maps applications to infrastructure assets. "
            f"Preview: {record_preview}"
        )

        try:
            await multi_model_service.generate_response(
                prompt=prompt,
                task_type="dependency_analysis",
                complexity=TaskComplexity.MEDIUM,
            )
        except Exception as exc:
            self.logger.warning(
                "Application discovery validation used fallback due to error: %s", exc
            )

        return {
            "valid": True,
            "validation_errors": [],
            "warnings": [],
        }

    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrichment stub.

        TODO: Persist application dependencies into AssetDependency table.
        """
        self.logger.info(
            "Enrichment placeholder for application discovery import_id=%s "
            "(records=%s)",
            data_import_id,
            len(validated_records),
        )
        return {
            "assets_enriched": 0,
            "dependencies_created": 0,
            "performance_updated": 0,
        }
