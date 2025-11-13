"""
Enrichment executors - Individual enrichment functions for the AutoEnrichmentPipeline.

Extracted from auto_enrichment_pipeline.py for modularization (400-line limit compliance).

**ADR Compliance**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for agent learning (CrewAI memory=False)

Each function receives the necessary context (db, agent_pool, memory_manager, tenant IDs)
and returns the count of successfully enriched assets.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager

logger = logging.getLogger(__name__)


async def enrich_compliance(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with compliance flags using ComplianceEnrichmentAgent.

    **ADR Compliance**:
    - Uses TenantScopedAgentPool to retrieve persistent agent
    - Uses multi_model_service for LLM calls
    - Stores learned patterns via TenantMemoryManager

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting compliance enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import ComplianceEnrichmentAgent

        # Initialize ComplianceEnrichmentAgent (ADR-015, ADR-024)
        agent = ComplianceEnrichmentAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        # Enrich all assets
        enriched_count = await agent.enrich_assets(assets)

        logger.info(f"Compliance enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"Compliance enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_licenses(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with software licensing information using LicensingEnrichmentAgent.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting license enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import LicensingEnrichmentAgent

        agent = LicensingEnrichmentAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        enriched_count = await agent.enrich_assets(assets)
        logger.info(f"License enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"License enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_vulnerabilities(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with security vulnerabilities using VulnerabilityEnrichmentAgent.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting vulnerability enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import VulnerabilityEnrichmentAgent

        agent = VulnerabilityEnrichmentAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        enriched_count = await agent.enrich_assets(assets)
        logger.info(f"Vulnerability enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"Vulnerability enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_resilience(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with HA/DR configuration using ResilienceEnrichmentAgent.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting resilience enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import ResilienceEnrichmentAgent

        agent = ResilienceEnrichmentAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        enriched_count = await agent.enrich_assets(assets)
        logger.info(f"Resilience enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"Resilience enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_dependencies(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with dependency relationships using DependencyEnrichmentAgent.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting dependency enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import DependencyEnrichmentAgent

        agent = DependencyEnrichmentAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        enriched_count = await agent.enrich_assets(assets)
        logger.info(f"Dependency enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"Dependency enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_product_links(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with vendor product catalog matching using ProductMatchingAgent.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting product link enrichment for {len(assets)} assets")

    try:
        from app.services.enrichment.agents import ProductMatchingAgent

        agent = ProductMatchingAgent(
            db=db,
            agent_pool=agent_pool,
            memory_manager=memory_manager,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        enriched_count = await agent.enrich_assets(assets)
        logger.info(f"Product link enrichment completed: {enriched_count} assets")
        return enriched_count

    except Exception as e:
        logger.error(f"Product link enrichment failed: {e}", exc_info=True)
        return 0


async def enrich_field_conflicts(
    assets: List[Asset],
    db: AsyncSession,
    agent_pool: type,
    memory_manager: TenantMemoryManager,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Enrich assets with multi-source conflict resolution.

    Args:
        assets: List of Asset instances to enrich
        db: Async SQLAlchemy session
        agent_pool: TenantScopedAgentPool class
        memory_manager: TenantMemoryManager instance
        client_account_id: Multi-tenant client account UUID
        engagement_id: Multi-tenant engagement UUID

    Returns:
        Number of assets successfully enriched
    """
    logger.info(f"Starting field conflict enrichment for {len(assets)} assets")
    # TODO: Implement conflict resolution logic
    return 0
