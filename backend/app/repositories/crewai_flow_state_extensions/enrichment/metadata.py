import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select, update

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)

# Bug #1087 Fix: OCC retry configuration
OCC_MAX_RETRIES = 3
OCC_BASE_DELAY = 0.1  # 100ms
OCC_MAX_DELAY = 2.0  # 2 seconds


class MetadataEnrichmentMixin:
    async def update_flow_metadata(
        self, flow_id: str, metadata_updates: Dict[str, Any]
    ) -> None:
        if not getattr(self, "_enrichment_enabled", False):
            return
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(
                "Invalid UUID in enrichment call for flow_id=%s: %s", flow_id, e
            )
            return

        stmt = (
            select(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        flow = result.scalar_one_or_none()
        if not flow:
            return

        metadata = flow.flow_metadata or {}
        if not isinstance(metadata, dict):
            logger.warning(
                "flow_metadata is not a dict; resetting to empty dict for flow_id=%s",
                flow_id,
            )
            metadata = {}

        serializable = self._ensure_json_serializable(metadata_updates)
        if not isinstance(serializable, dict):
            logger.warning(
                "metadata_updates did not serialize to a dict; skipping merge for flow_id=%s",
                flow_id,
            )
        else:
            metadata.update(serializable)

        # Bug #1087 Fix: OCC retry with exponential backoff
        for attempt in range(OCC_MAX_RETRIES + 1):
            # Re-fetch flow on retry to get updated version
            if attempt > 0:
                result = await self.db.execute(stmt)
                flow = result.scalar_one_or_none()
                if not flow:
                    return
                metadata = flow.flow_metadata or {}
                if not isinstance(metadata, dict):
                    metadata = {}
                serializable = self._ensure_json_serializable(metadata_updates)
                if isinstance(serializable, dict):
                    metadata.update(serializable)

            prev_updated_at = flow.updated_at
            stmt_upd = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.id == flow.id,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                        CrewAIFlowStateExtensions.updated_at == prev_updated_at,
                    )
                )
                .values(flow_metadata=metadata, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
                # await self.db.commit()  # REMOVED to prevent double commit
                if attempt > 0:
                    logger.info(
                        "✅ OCC conflict resolved after %d retries for flow_id=%s",
                        attempt,
                        flow_id,
                    )
                return  # Success

            # OCC conflict - retry with exponential backoff
            if attempt < OCC_MAX_RETRIES:
                delay = min(OCC_BASE_DELAY * (2**attempt), OCC_MAX_DELAY)
                # Add jitter to prevent thundering herd
                delay += random.uniform(0, delay * 0.2)
                logger.warning(
                    "⚠️ OCC conflict updating flow_metadata for flow_id=%s (attempt %d/%d), "
                    "retrying in %.2fs...",
                    flow_id,
                    attempt + 1,
                    OCC_MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                # Max retries exhausted
                logger.warning(
                    "❌ OCC conflict updating flow_metadata for flow_id=%s after %d retries; update skipped.",
                    flow_id,
                    OCC_MAX_RETRIES,
                )
