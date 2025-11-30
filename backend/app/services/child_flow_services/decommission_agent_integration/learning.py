"""
Decommission Agent Integration - Learning Storage Module

Handles storing decommission learnings via TenantMemoryManager.
ADR Compliance: ADR-024 (TenantMemoryManager)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)

logger = logging.getLogger(__name__)


async def _store_decommission_learnings(
    phase_name: str,
    result: Dict[str, Any],
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    db: AsyncSession,
) -> None:
    """Store decommission learnings via TenantMemoryManager (ADR-024)."""
    try:
        memory_manager = TenantMemoryManager(crewai_service=None, database_session=db)

        learning_data = {
            "phase": phase_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "key_insights": result.get("key_insights", []),
            "patterns_identified": result.get("patterns", []),
        }

        await memory_manager.store_learning(
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            scope=LearningScope.ENGAGEMENT,
            pattern_type="DECOMMISSION_OPTIMIZATION",
            pattern_data=learning_data,
        )

        logger.info(f"Stored {phase_name} learnings via TenantMemoryManager")

    except Exception as e:
        logger.warning(f"Failed to store decommission learnings: {e}")
