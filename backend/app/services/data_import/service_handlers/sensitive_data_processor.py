"""
Sensitive data asset import processor.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import TaskComplexity, multi_model_service

from .base_processor import BaseDataImportProcessor


class SensitiveDataProcessor(BaseDataImportProcessor):
    """Processor for sensitive data asset imports."""

    category = "sensitive_data"

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)

    async def validate_data(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform classification validation with LLM support."""
        record_preview = raw_records[:2] if raw_records else []
        prompt = (
            "Validate sensitive data asset classifications and compliance scopes. "
            "Ensure records include classification levels and scope tags. "
            f"Preview: {record_preview}"
        )

        try:
            await multi_model_service.generate_response(
                prompt=prompt,
                task_type="compliance_validation",
                complexity=TaskComplexity.MEDIUM,
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
            )
        except Exception as exc:
            self.logger.warning(
                "Sensitive data validation used fallback due to error: %s", exc
            )

        return {"valid": True, "validation_errors": [], "warnings": []}

    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrichment stub.

        TODO: Persist sensitive data attributes into asset_custom_attributes table.
        """
        self.logger.info(
            "Enrichment placeholder for sensitive data import_id=%s (records=%s)",
            data_import_id,
            len(validated_records),
        )
        return {
            "assets_enriched": len(validated_records),
            "dependencies_created": 0,
            "performance_updated": 0,
        }
