"""
Query Helper Functions for Discovery Flow Status Operations

This module contains database query helper functions for retrieving discovery flows
and related data.
"""

import logging
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def get_discovery_flow(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Optional[DiscoveryFlow]:
    """Get discovery flow by ID and context"""
    # SKIP_TENANT_CHECK - Service-level/monitoring query
    stmt = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_master_flow(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Optional[CrewAIFlowStateExtensions]:
    """Get master flow state data"""
    # SKIP_TENANT_CHECK - Service-level/monitoring query
    stmt = select(CrewAIFlowStateExtensions).where(
        and_(
            CrewAIFlowStateExtensions.flow_id == flow_id,
            CrewAIFlowStateExtensions.client_account_id == context.client_account_id,
            CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def debug_flow_context(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> None:
    """Debug flow context when flow is not found"""
    # SKIP_TENANT_CHECK - Service-level/monitoring query
    debug_stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
    debug_result = await db.execute(debug_stmt)
    debug_flow = debug_result.scalar_one_or_none()

    if debug_flow:
        logger.error(
            safe_log_format(
                "❌ Flow {flow_id} exists but with different context: "
                "client={client_account_id}, engagement={engagement_id}",
                flow_id=flow_id,
                client_account_id=debug_flow.client_account_id,
                engagement_id=debug_flow.engagement_id,
            )
        )
        raise ValueError(f"Flow {flow_id} exists but not in current context")
    else:
        logger.error(
            safe_log_format(
                "❌ Flow {flow_id} not found in DiscoveryFlow table with context "
                "client={client_account_id}, engagement={engagement_id}",
                flow_id=flow_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
            )
        )
        raise ValueError(f"Flow {flow_id} not found")
