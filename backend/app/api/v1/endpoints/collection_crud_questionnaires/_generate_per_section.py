"""Per-Asset, Per-Section Questionnaire Generation with Redis Caching.

Per ADR-035: Orchestrates batched agent calls to avoid 16KB+ JSON truncation.
Generates ~2KB responses per (asset, section) combination.

Architecture:
1. For each asset, generate questions per assessment flow section
2. Store intermediate results in Redis cache
3. Aggregate sections from Redis
4. Deduplicate common questions across assets
5. Return final questionnaire structure

Benefits:
- No JSON truncation (16KB+ → 2KB per call)
- Agent maintains intelligence (AIX options for AIX systems)
- Common questions deduplicated (asked once, applied to multiple assets)
- Aligned with Issue #980 assessment flow sections
"""

import asyncio
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.services.collection.gap_scanner.scanner import ProgrammaticGapScanner
from app.services.collection.gap_analysis.task_builder import (
    build_section_specific_task,
)

# Import Redis and helper functions
from .section_helpers import (
    filter_gaps_by_section,
    store_section_in_redis,
    aggregate_sections_from_redis,
    cleanup_redis_cache,
)
from .deduplication_service import deduplicate_common_questions

logger = logging.getLogger(__name__)

# Per ADR-035: Assessment flow sections aligned with Issue #980
ASSESSMENT_FLOW_SECTIONS = [
    "infrastructure",  # Column gaps: OS, hardware, network
    "resilience",  # Enrichment gaps: HA, DR, backup
    "compliance",  # Standards gaps: GDPR, HIPAA, encryption
    "dependencies",  # Enrichment gaps: APIs, integrations
    "tech_debt",  # JSONB gaps: code quality, vulnerabilities
]


async def _generate_questionnaires_per_section(  # noqa: C901
    flow_id: str,
    flow_db_id: UUID,
    existing_assets: List[Asset],
    context: RequestContext,
    db: AsyncSession,
) -> List[dict]:
    """
    Generate questionnaires per asset, per section with Redis caching.

    Per ADR-035: Batched generation to avoid 16KB+ JSON truncation.
    Each agent call generates ~2KB for a single (asset, section) combination.

    Args:
        flow_id: Child collection flow ID (for logging)
        flow_db_id: Collection flow primary key (for gap analysis per ADR-025)
        existing_assets: List of Asset objects to generate questionnaires for
        context: RequestContext with client_account_id, engagement_id
        db: Database session for gap analysis

    Returns:
        List of section dicts with deduplicated questions

    Raises:
        Exception: If gap analysis fails or agent calls fail
    """
    from app.core.redis_config import RedisConnectionManager

    try:
        # Step 1: Run gap analysis for all assets
        logger.info(
            f"Starting per-section questionnaire generation for "
            f"{len(existing_assets)} asset(s) in flow {flow_id} "
            f"(flow_db_id: {flow_db_id})"
        )

        gap_scanner = ProgrammaticGapScanner()
        # CC FIX Issue #2: Pass flow_db_id (collection_flows.id PK) instead of master_flow_id
        # Per ADR-025: Use collection_flows.id for foreign keys and background jobs
        gap_results = await gap_scanner.scan_assets_for_gaps(
            selected_asset_ids=[str(asset.id) for asset in existing_assets],
            collection_flow_id=str(flow_db_id),  # Use primary key, not master flow UUID
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            db=db,
        )

        if not gap_results or not gap_results.get("gaps"):
            logger.warning(f"No gaps found for assets in flow {flow_id}")
            return []

        # Group gaps by asset_id for efficient lookup
        gaps_by_asset = {}
        for gap in gap_results["gaps"]:
            asset_id = gap.get("asset_id")
            if asset_id:
                if asset_id not in gaps_by_asset:
                    gaps_by_asset[asset_id] = []
                gaps_by_asset[asset_id].append(gap.get("field_name"))

        logger.info(
            f"Gap analysis complete: {len(gaps_by_asset)} asset(s) with gaps, "
            f"{gap_results.get('summary', {}).get('total_gaps', 0)} total gaps"
        )

        # Step 2: Generate questions per asset, per section with Redis caching
        redis = RedisConnectionManager()
        await redis.initialize()

        try:
            # Generate sections in parallel for all (asset, section) combinations
            tasks = []
            for asset in existing_assets:
                # CRITICAL FIX: gap scanner returns asset_id as string, but asset.id is UUID
                # Must convert to string for dictionary lookup to work
                asset_gaps = gaps_by_asset.get(str(asset.id), [])
                if not asset_gaps:
                    logger.info(
                        f"Asset {asset.name} ({asset.id}) has no gaps, skipping questionnaire generation"
                    )
                    continue

                # Generate questions for each assessment flow section
                for section_id in ASSESSMENT_FLOW_SECTIONS:
                    tasks.append(
                        _generate_asset_section(
                            redis=redis,
                            flow_id=flow_id,
                            asset=asset,
                            section_id=section_id,
                            all_gaps=asset_gaps,
                            context=context,
                        )
                    )

            if not tasks:
                logger.warning(f"No generation tasks created for flow {flow_id}")
                return []

            logger.info(
                f"Executing {len(tasks)} parallel agent calls "
                f"({len(existing_assets)} assets × "
                f"{len(ASSESSMENT_FLOW_SECTIONS)} sections)"
            )

            # Execute all (asset, section) generations in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any errors but continue with successful results
            failed_count = sum(1 for r in results if isinstance(r, Exception))
            if failed_count > 0:
                logger.warning(
                    f"{failed_count}/{len(results)} section generations failed, continuing with successful results"
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Section generation failed: {result}", exc_info=result
                        )

            # Step 3: Aggregate sections from Redis
            logger.info(f"Aggregating sections from Redis for flow {flow_id}")
            aggregated_sections = await aggregate_sections_from_redis(
                redis=redis,
                flow_id=flow_id,
                asset_ids=[asset.id for asset in existing_assets],
                sections=ASSESSMENT_FLOW_SECTIONS,
            )

            if not aggregated_sections:
                logger.warning(f"No sections aggregated from Redis for flow {flow_id}")
                return []

            # Step 4: Deduplicate common questions across assets
            logger.info(
                f"Deduplicating questions across {len(existing_assets)} asset(s)"
            )

            # Build assets_data for deduplication context
            assets_data = [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type,
                }
                for asset in existing_assets
            ]

            dedup_result = deduplicate_common_questions(
                sections=aggregated_sections,
                assets=assets_data,
            )

            deduplicated_sections = dedup_result["sections"]
            dedup_stats = dedup_result.get("deduplication_stats", {})

            logger.info(
                f"Deduplication complete: {dedup_stats.get('original_count', 0)} questions → "
                f"{dedup_stats.get('deduplicated_count', 0)} questions "
                f"({dedup_stats.get('reduction_percentage', 0):.1f}% reduction)"
            )

            # Step 5: Cleanup Redis cache
            await cleanup_redis_cache(
                redis=redis,
                flow_id=flow_id,
                asset_ids=[asset.id for asset in existing_assets],
                sections=ASSESSMENT_FLOW_SECTIONS,
            )

            return deduplicated_sections

        finally:
            await redis.close()

    except Exception as e:
        logger.error(
            f"Per-section questionnaire generation failed for flow {flow_id}: {e}",
            exc_info=True,
        )
        raise


async def _generate_asset_section(
    redis,
    flow_id: str,
    asset: Asset,
    section_id: str,
    all_gaps: List[str],
    context: RequestContext,
) -> Optional[dict]:
    """
    Generate questions for ONE asset, ONE section using persistent TenantScopedAgent.

    Per ADR-015: Uses TenantScopedAgentPool for persistent agent execution.
    Per ADR-035: Each call generates ~2KB JSON (vs 16KB+ for full questionnaire).

    Args:
        redis: RedisConnectionManager instance
        flow_id: Collection flow ID
        asset: Asset object to generate questions for
        section_id: Assessment flow section (infrastructure, resilience, etc.)
        all_gaps: All gaps for this asset (will be filtered by section)
        context: RequestContext with client_account_id, engagement_id

    Returns:
        Section dict if generation succeeds, None otherwise
    """
    import asyncio
    from crewai import Task
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    try:
        # Filter gaps relevant to this section
        section_gaps = filter_gaps_by_section(all_gaps, section_id)

        if not section_gaps:
            logger.debug(
                f"No gaps for asset {asset.name} ({asset.id}) in section {section_id}, skipping"
            )
            return None

        # Build asset context for intelligent option generation
        asset_data = {
            "asset_id": str(asset.id),
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "operating_system": asset.operating_system,
            "os_version": getattr(asset, "os_version", None),
            "eol_technology": getattr(asset, "eol_technology", False),
        }

        # Build business context for multi-tenant scoping
        business_context = {
            "engagement_id": str(context.engagement_id),
            "client_account_id": str(context.client_account_id),
        }

        # Generate agent task prompt
        task_description = build_section_specific_task(
            asset_data=asset_data,
            gaps=section_gaps,
            section_id=section_id,
            business_context=business_context,
        )

        logger.info(
            f"Generating {section_id} questions for asset {asset.name} ({len(section_gaps)} gaps)"
        )

        # CC FIX (Issue #1067 - ADR-015 Compliance): Use TenantScopedAgentPool
        # Replace legacy crew-based execution with persistent agent pattern
        logger.debug(
            f"🔧 Getting persistent questionnaire_generator agent for "
            f"client={context.client_account_id}, engagement={context.engagement_id}"
        )

        agent = await TenantScopedAgentPool.get_or_create_agent(
            client_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            agent_type="questionnaire_generator",  # Existing agent type from agent pool
        )

        logger.debug(
            f"✅ Agent retrieved: {agent.role if hasattr(agent, 'role') else 'questionnaire_generator'}"
        )

        # Extract underlying CrewAI agent from AgentWrapper (per gap_analysis pattern)
        underlying_agent = agent._agent if hasattr(agent, "_agent") else agent

        # Create Task (no Crew needed - agent executes directly per ADR-015)
        task = Task(
            description=task_description,
            expected_output="JSON object with section questions (no markdown, valid JSON only)",
            agent=underlying_agent,
        )

        logger.debug(
            "🤖 Executing questionnaire generation task via persistent agent (no Crew creation)"
        )

        # Execute task directly on persistent agent (per gap_analysis/agent_helpers.py pattern)
        result = await asyncio.to_thread(agent.execute_task, task)

        logger.debug(
            f"📤 Agent task completed for {section_id}: {str(result)[:200]}..."
        )

        if not result:
            logger.warning(
                f"Agent returned empty result for asset {asset.name}, section {section_id}"
            )
            return None

        # Parse agent output (should be valid JSON)
        import json

        # Agent returns raw string output from task execution
        agent_output = str(result)

        # Strip markdown code blocks if present (agent sometimes adds despite instructions)
        if "```json" in agent_output:
            agent_output = agent_output.split("```json")[1].split("```")[0].strip()
        elif "```" in agent_output:
            agent_output = agent_output.split("```")[1].split("```")[0].strip()

        section_data = json.loads(agent_output)

        # Validate section structure
        if not isinstance(section_data, dict) or "questions" not in section_data:
            logger.error(
                f"Invalid section structure from agent for asset {asset.name}, section {section_id}: {section_data}"
            )
            return None

        # Store in Redis for aggregation
        await store_section_in_redis(
            redis=redis,
            flow_id=flow_id,
            asset_id=asset.id,
            section_id=section_id,
            section_data=section_data,
            ttl=3600,  # 1 hour TTL
        )

        logger.info(
            f"Generated {len(section_data.get('questions', []))} questions for asset {asset.name}, section {section_id}"
        )

        return section_data

    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parse error for asset {asset.name}, section {section_id}: {e}",
            exc_info=True,
        )
        logger.error(f"Agent output that failed to parse: {agent_output[:500]}...")
        return None

    except Exception as e:
        logger.error(
            f"Section generation failed for asset {asset.name}, section {section_id}: {e}",
            exc_info=True,
        )
        return None
