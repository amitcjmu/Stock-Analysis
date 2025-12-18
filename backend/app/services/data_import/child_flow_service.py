"""
Data Import Child Flow Service

Encapsulates master/child flow creation for data import executions while
maintaining transaction safety and real-data audit trails.
"""

from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.crewai_env_setup import ensure_crewai_environment
from app.core.logging import get_logger
from app.models.data_import import DataImport, RawImportRecord
from app.services.data_import.storage_manager.operations import ImportStorageOperations
from app.services.discovery_flow_service import DiscoveryFlowService
# MasterFlowOrchestrator removed - master flow code removed from project


logger = get_logger(__name__)


class DataImportChildFlowService:
    """Coordinates creation of master + discovery child flows for data imports."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def create_import_flow(
        self,
        data_import: DataImport,
        storage_ops: ImportStorageOperations,
        raw_records: List[Dict[str, Any]],
        import_category: Optional[str] = None,
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create the master + child flow for a data import within an ongoing transaction.

        Args:
            data_import: Persisted DataImport record.
            storage_ops: Storage operations facade for linkage updates.
            raw_records: Raw records stored for this import (used by discovery flow).
            import_category: High-level processor routing category.
            processing_config: Optional processor configuration overrides.

        Returns:
            Dict[str, Any]: Metadata including master_flow_id and raw_data_sample.
        """
        ensure_crewai_environment()
        logger.info(
            "✅ CrewAI environment configured for DataImportChildFlowService initialization"
        )

        # MasterFlowOrchestrator removed - master flow code removed from project
        # Generate a flow ID directly without master flow orchestrator
        master_flow_id_str = str(uuid.uuid4())
        logger.info(f"✅ Flow ID generated: {master_flow_id_str}")

        raw_data_sample = await self._get_raw_data_sample(data_import.id)

        discovery_service = DiscoveryFlowService(self.db, self.context)
        metadata: Dict[str, Any] = {
            "source": "data_import",
            "import_id": str(data_import.id),
            "master_flow_id": master_flow_id_str,
            "import_category": import_category,
            "processing_config": processing_config or {},
            "import_timestamp": datetime.utcnow().isoformat(),
        }
        if isinstance(raw_records, list) and raw_records:
            first_row = raw_records[0]
            if isinstance(first_row, dict):
                metadata["detected_columns"] = sorted(first_row.keys())

        # Store actual raw records for downstream phases
        await discovery_service.create_discovery_flow(
            flow_id=master_flow_id_str,
            raw_data=raw_records,
            metadata=self._convert_uuids_to_str(metadata),
            data_import_id=str(data_import.id),
            user_id=str(self.context.user_id),
            master_flow_id=master_flow_id_str,
        )
        logger.info(
            f"✅ Discovery flow child record created and linked: {master_flow_id_str}"
        )

        await storage_ops.update_import_with_flow_id(
            data_import_id=data_import.id, flow_id=master_flow_id_str
        )
        data_import.master_flow_id = uuid.UUID(master_flow_id_str)
        data_import.flow_execution_data = {
            "flow_id": master_flow_id_str,
            "file_data": raw_records,
            "import_category": import_category,
            "processing_config": processing_config or {},
        }

        return {
            "master_flow_id": master_flow_id_str,
            "raw_data_sample": raw_data_sample,
        }

    async def _get_raw_data_sample(
        self, data_import_id: uuid.UUID, limit: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Fetch a deterministic sample of raw records for audit trails and previews.
        """
        logger.info(
            f"🔍 Fetching raw data sample for data_import_id={data_import_id}, limit={limit}"
        )
        try:
            query = (
                select(RawImportRecord.raw_data)
                .where(RawImportRecord.data_import_id == data_import_id)
                .order_by(RawImportRecord.row_number.asc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            rows = result.scalars().all()

            sample: List[Dict[str, Any]] = []
            for row in rows:
                if isinstance(row, dict):
                    sample.append(row)

            logger.info(f"✅ Retrieved {len(sample)} sample records")
            return sample
        except Exception as exc:
            logger.error(
                f"❌ Failed to fetch raw data sample for data import {data_import_id}: {exc}",
                exc_info=True,
            )
            return []

    def _convert_uuids_to_str(self, obj: Any) -> Any:
        """Recursively convert UUID objects to strings for JSON serialization."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, dict):
            return {
                key: self._convert_uuids_to_str(value) for key, value in obj.items()
            }
        if isinstance(obj, list):
            return [self._convert_uuids_to_str(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(self._convert_uuids_to_str(item) for item in obj)
        if isinstance(obj, set):
            return {self._convert_uuids_to_str(item) for item in obj}
        return obj
