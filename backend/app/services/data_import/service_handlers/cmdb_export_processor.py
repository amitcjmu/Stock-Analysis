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
        Delegate to legacy CMDB discovery executor.

        This processor short-circuits the standard validation/enrichment pipeline
        to route CMDB imports through the existing discovery flow executor.
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
        """
        Not used - CMDBExportProcessor delegates via process().

        This method is required by the abstract base class but should never
        be called directly since process() handles delegation.
        """
        self.logger.warning(
            "validate_data() called directly on CMDBExportProcessor - "
            "this should not happen. Use process() instead."
        )
        return {
            "valid": False,
            "validation_errors": ["Use process() method for delegation"],
        }

    async def enrich_assets(
        self,
        data_import_id: uuid.UUID,
        validated_records: List[Dict[str, Any]],
        processing_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Not used - CMDBExportProcessor delegates via process().

        This method is required by the abstract base class but should never
        be called directly since process() handles delegation.
        """
        self.logger.warning(
            "enrich_assets() called directly on CMDBExportProcessor - "
            "this should not happen. Use process() method for delegation."
        )
        return {
            "assets_enriched": 0,
            "dependencies_created": 0,
            "performance_updated": 0,
        }
