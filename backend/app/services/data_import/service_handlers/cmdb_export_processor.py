"""
CMDB export processor that delegates to the legacy discovery flow pipeline.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .base_processor import BaseDataImportProcessor


class CMDBExportProcessor(BaseDataImportProcessor):
    """
    Processor that keeps CMDB imports on the legacy discovery execution path.
    """

    category = "cmdb_export"

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)

    async def process(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Short-circuit the processor pipeline so the caller can reuse the legacy flow.
        """
        self.logger.info(
            "Delegating CMDB import %s to legacy discovery flow executor",
            data_import_id,
        )
        return {
            "status": "delegated",
            "delegate_to_legacy": True,
        }

    async def validate_data(
        self,
        data_import_id: uuid.UUID,
        raw_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError("CMDBExportProcessor delegates to legacy executor.")

    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError("CMDBExportProcessor delegates to legacy executor.")
