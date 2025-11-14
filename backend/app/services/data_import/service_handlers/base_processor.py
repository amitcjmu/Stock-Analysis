"""
Base processor definition for multi-category data imports.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger


class BaseDataImportProcessor(ABC):
    """Abstract base class for import processors."""

    category: str = "base"

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    async def process(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute validation followed by enrichment."""
        validation_result = await self.validate_data(
            data_import_id=data_import_id,
            raw_records=raw_records,
            processing_config=processing_config or {},
        )

        if not validation_result.get("valid", False):
            self.logger.warning(
                "Validation failed for data_import_id=%s, errors=%s",
                data_import_id,
                validation_result.get("validation_errors"),
            )
            return {
                "status": "failed",
                "validation": validation_result,
                "enrichment": None,
            }

        enrichment_result = await self.enrich_assets(
            data_import_id=data_import_id,
            validated_records=raw_records,
            processing_config=processing_config or {},
        )

        return {
            "status": "completed",
            "validation": validation_result,
            "enrichment": enrichment_result,
        }

    @abstractmethod
    async def validate_data(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate incoming records."""

    @abstractmethod
    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist validated data to downstream models."""
