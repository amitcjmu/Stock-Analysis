import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, select, update

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)

# Bug #1087 Fix: OCC retry configuration
OCC_MAX_RETRIES = 3
OCC_BASE_DELAY = 0.1  # 100ms
OCC_MAX_DELAY = 2.0  # 2 seconds


class TransitionsEnrichmentMixin:
    async def add_phase_transition(
        self,
        flow_id: str,
        phase: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
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

        transitions = list(flow.phase_transitions or [])
        entry = self._ensure_json_serializable(
            {
                "phase": phase,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": self._ensure_json_serializable(metadata or {}),
            }
        )
        transitions.append(entry)
        if len(transitions) > 200:
            transitions = transitions[-200:]

        # Bug #1087 Fix: OCC retry with exponential backoff
        for attempt in range(OCC_MAX_RETRIES + 1):
            # Re-fetch flow on retry to get updated version
            if attempt > 0:
                result = await self.db.execute(stmt)
                flow = result.scalar_one_or_none()
                if not flow:
                    return
                transitions = list(flow.phase_transitions or [])
                transitions.append(entry)
                if len(transitions) > 200:
                    transitions = transitions[-200:]

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
                .values(phase_transitions=transitions, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                if attempt > 0:
                    logger.info(
                        "✅ OCC conflict resolved after %d retries for flow_id=%s (transitions)",
                        attempt,
                        flow_id,
                    )
                return  # Success

            # OCC conflict - retry with exponential backoff
            if attempt < OCC_MAX_RETRIES:
                delay = min(OCC_BASE_DELAY * (2**attempt), OCC_MAX_DELAY)
                delay += random.uniform(0, delay * 0.2)
                logger.warning(
                    "⚠️ OCC conflict updating phase_transitions for flow_id=%s (attempt %d/%d), "
                    "retrying in %.2fs...",
                    flow_id,
                    attempt + 1,
                    OCC_MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.warning(
                    "❌ OCC conflict updating phase_transitions for flow_id=%s after %d retries; "
                    "update skipped.",
                    flow_id,
                    OCC_MAX_RETRIES,
                )

    async def record_phase_execution_time(
        self, flow_id: str, phase: str, execution_time_ms: float
    ) -> None:
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
        times = dict(flow.phase_execution_times or {})
        times[phase] = {
            "execution_time_ms": float(execution_time_ms),
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Bug #1087 Fix: OCC retry with exponential backoff
        for attempt in range(OCC_MAX_RETRIES + 1):
            # Re-fetch flow on retry to get updated version
            if attempt > 0:
                result = await self.db.execute(stmt)
                flow = result.scalar_one_or_none()
                if not flow:
                    return
                times = dict(flow.phase_execution_times or {})
                times[phase] = {
                    "execution_time_ms": float(execution_time_ms),
                    "completed_at": datetime.utcnow().isoformat(),
                }

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
                .values(phase_execution_times=times, updated_at=datetime.utcnow())
            )
            result_upd = await self.db.execute(stmt_upd)
            if result_upd.rowcount:
                if attempt > 0:
                    logger.info(
                        "✅ OCC conflict resolved after %d retries for flow_id=%s (execution_times)",
                        attempt,
                        flow_id,
                    )
                return  # Success

            # OCC conflict - retry with exponential backoff
            if attempt < OCC_MAX_RETRIES:
                delay = min(OCC_BASE_DELAY * (2**attempt), OCC_MAX_DELAY)
                delay += random.uniform(0, delay * 0.2)
                logger.warning(
                    "⚠️ OCC conflict updating phase_execution_times for flow_id=%s (attempt %d/%d), "
                    "retrying in %.2fs...",
                    flow_id,
                    attempt + 1,
                    OCC_MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.warning(
                    "❌ OCC conflict updating phase_execution_times for flow_id=%s after %d retries; "
                    "update skipped.",
                    flow_id,
                    OCC_MAX_RETRIES,
                )
