"""Per-Asset, Per-Section Questionnaire Generation with Intelligent Gap Detection.

Per ADR-037 (Issue #1115): Orchestrates intelligent 2-phase questionnaire generation.
Replaces ProgrammaticGapScanner with IntelligentGapScanner (6-source checking).

Architecture (per ADR-037):
1. IntelligentGapScanner: Scan ALL assets for TRUE gaps (6 sources, cached)
2. DataAwarenessAgent: Create comprehensive data map (ONE-TIME)
3. SectionQuestionGenerator: Generate questions (per-asset, per-section, NO TOOLS)
4. Cross-section deduplication (track questions across sections)
5. Persist questionnaires to database

Performance Target: <15s for 9 questions (vs 44s with old pattern)

Benefits:
- TRUE gaps only (no false questions for data-exists-elsewhere)
- Data awareness context (intelligent option generation)
- Tool-free agent (no tool calling overhead)
- Cross-section deduplication (no duplicate questions)
- Redis caching for performance

CC Generated for Issue #1115 - Orchestration Layer Integration
Parent Issue: #1109 - Intelligent Gap Detection and Questionnaire Generation
"""

import json
import logging
from typing import List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_data_gap import CollectionDataGap
from app.core.redis_config import RedisConnectionManager
from app.models.asset import Asset

# Intelligent gap detection components (ADR-037)
from app.services.collection.gap_analysis.intelligent_gap_scanner import (
    IntelligentGapScanner,
)
from app.services.collection.gap_analysis.models import IntelligentGap
from app.services.collection.gap_analysis.data_awareness_agent import (
    DataAwarenessAgent,
)
from app.services.collection.gap_analysis.section_question_generator import (
    SectionQuestionGenerator,
)

# Keep legacy helpers for Redis operations
from .section_helpers import (
    store_section_in_redis,
    aggregate_sections_from_redis,
    cleanup_redis_cache,
)
from .deduplication_service import deduplicate_common_questions

logger = logging.getLogger(__name__)


async def _get_resolved_fields_for_assets(
    asset_ids: List[UUID], db: AsyncSession
) -> dict[str, set[str]]:
    """
    Get resolved fields for each asset (from ANY previous flow).

    GAP INHERITANCE for questionnaire generation: Skip generating questions
    for fields that have already been resolved in previous collection flows.

    Args:
        asset_ids: List of asset UUIDs to check
        db: Database session

    Returns:
        Dict mapping asset_id (str) -> set of resolved field_names
    """
    if not asset_ids:
        return {}

    # Query for already-resolved gaps (from ANY flow)
    resolved_stmt = select(
        CollectionDataGap.asset_id, CollectionDataGap.field_name
    ).where(
        and_(
            CollectionDataGap.asset_id.in_(asset_ids),
            CollectionDataGap.resolution_status == "resolved",
        )
    )
    resolved_result = await db.execute(resolved_stmt)

    # Build dict: asset_id -> set of resolved field_names
    resolved_by_asset: dict[str, set[str]] = {}
    for row in resolved_result:
        asset_id_str = str(row.asset_id)
        if asset_id_str not in resolved_by_asset:
            resolved_by_asset[asset_id_str] = set()
        resolved_by_asset[asset_id_str].add(row.field_name)

    total_resolved = sum(len(fields) for fields in resolved_by_asset.values())
    if total_resolved > 0:
        logger.info(
            f"🔄 Gap Inheritance (questionnaire): Found {total_resolved} resolved fields "
            f"across {len(resolved_by_asset)} asset(s) - will skip generating questions for these"
        )

    return resolved_by_asset


def _filter_gaps_by_resolved(
    intelligent_gaps: dict[str, List["IntelligentGap"]],
    resolved_by_asset: dict[str, set[str]],
) -> tuple[dict[str, List["IntelligentGap"]], int]:
    """
    Filter out gaps for fields that have already been resolved.

    Args:
        intelligent_gaps: Dict mapping asset_id -> list of IntelligentGap
        resolved_by_asset: Dict mapping asset_id -> set of resolved field_names

    Returns:
        Tuple of (filtered_gaps dict, count of gaps skipped)
    """
    filtered_gaps = {}
    total_skipped = 0

    for asset_id, gaps in intelligent_gaps.items():
        resolved_fields = resolved_by_asset.get(asset_id, set())

        if not resolved_fields:
            # No resolved fields for this asset - keep all gaps
            filtered_gaps[asset_id] = gaps
            continue

        # Filter out gaps whose field_id is in resolved_fields
        original_count = len(gaps)
        filtered = [g for g in gaps if g.field_id not in resolved_fields]
        skipped = original_count - len(filtered)
        total_skipped += skipped

        filtered_gaps[asset_id] = filtered

        if skipped > 0:
            logger.info(
                f"🔄 Asset {asset_id[:8]}...: Filtered {skipped} already-resolved gaps "
                f"({original_count} → {len(filtered)} remaining)"
            )

    return filtered_gaps, total_skipped


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
    Generate questionnaires per asset, per section with intelligent gap detection.

    Per ADR-037 (Issue #1115): Uses IntelligentGapScanner, DataAwarenessAgent,
    and SectionQuestionGenerator for intelligent 2-phase generation.

    Architecture:
    1. IntelligentGapScanner: Scan ALL assets for TRUE gaps (6 sources, cached)
    2. DataAwarenessAgent: Create comprehensive data map (ONE-TIME)
    3. SectionQuestionGenerator: Generate questions (per-asset, per-section, NO TOOLS)
    4. Cross-section deduplication (track questions across sections)
    5. Persist questionnaires to database

    Args:
        flow_id: Child collection flow ID (for logging and cache keys)
        flow_db_id: Collection flow primary key (for multi-tenant scoping)
        existing_assets: List of Asset objects to generate questionnaires for
        context: RequestContext with client_account_id, engagement_id
        db: Database session for intelligent gap scanning

    Returns:
        List of section dicts with deduplicated questions

    Raises:
        Exception: If intelligent gap scanning fails or agent calls fail
    """
    try:
        # CC FIX: Ensure CrewAI environment is set up before any agent code runs
        # Per Serena memory: Background tasks may not inherit startup env vars
        from app.core.crewai_env_setup import ensure_crewai_environment

        ensure_crewai_environment()
        # Step 1: Intelligent gap scanning (6 sources, cached)
        logger.info(
            f"🔍 Starting intelligent questionnaire generation for "
            f"{len(existing_assets)} asset(s) in flow {flow_id} "
            f"(client={context.client_account_id}, engagement={context.engagement_id})"
        )

        # Initialize Redis for caching
        redis = RedisConnectionManager()
        await redis.initialize()

        try:
            cache_key = f"intelligent_gaps:{flow_id}"
            cached_gaps = None

            # Try to get cached gaps
            if redis.is_available():
                try:
                    cached_data = await redis.client.get(cache_key)
                    if cached_data:
                        cached_gaps = json.loads(cached_data)
                        logger.info(
                            f"✅ Using cached intelligent gaps for flow {flow_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Redis cache read failed, proceeding without cache: {e}"
                    )

            if cached_gaps:
                # Reconstruct IntelligentGap objects from cached dicts
                intelligent_gaps = {
                    asset_id: [IntelligentGap.from_dict(gap_dict) for gap_dict in gaps]
                    for asset_id, gaps in cached_gaps.items()
                }
            else:
                # Scan gaps using IntelligentGapScanner (6 sources)
                scanner = IntelligentGapScanner(
                    db,  # Positional argument (not db_session=)
                    context.client_account_id,
                    context.engagement_id,
                )

                intelligent_gaps = {}
                for asset in existing_assets:
                    gaps = await scanner.scan_gaps(asset)
                    # Keep as IntelligentGap objects (not dicts) for DataAwarenessAgent
                    intelligent_gaps[str(asset.id)] = gaps

                # Cache for 5 minutes (serialize to dicts for JSON)
                if redis.is_available():
                    try:
                        serialized_gaps = {
                            asset_id: [gap.to_dict() for gap in gaps]
                            for asset_id, gaps in intelligent_gaps.items()
                        }
                        await redis.client.set(
                            cache_key,
                            json.dumps(serialized_gaps),
                            ex=300,  # 5 min TTL
                        )
                        logger.info(f"✅ Cached intelligent gaps for flow {flow_id}")
                    except Exception as e:
                        logger.warning(f"Redis cache write failed, continuing: {e}")

            # GAP INHERITANCE: Filter out already-resolved gaps from questionnaire generation
            # This prevents asking questions for fields that were answered in previous flows
            asset_uuids = [asset.id for asset in existing_assets]
            resolved_by_asset = await _get_resolved_fields_for_assets(asset_uuids, db)

            if resolved_by_asset:
                intelligent_gaps, gaps_skipped = _filter_gaps_by_resolved(
                    intelligent_gaps, resolved_by_asset
                )
                if gaps_skipped > 0:
                    logger.info(
                        f"🔄 Gap Inheritance: Filtered {gaps_skipped} already-resolved gaps "
                        f"from questionnaire generation"
                    )

            # Count TRUE gaps (now accessing IntelligentGap objects, not dicts)
            total_true_gaps = sum(
                len([g for g in gaps if g.is_true_gap])
                for gaps in intelligent_gaps.values()
            )

            logger.info(
                f"📊 Intelligent gap scanning complete: "
                f"{total_true_gaps} TRUE gaps found "
                f"({len(existing_assets)} assets, 6 sources checked)"
            )

            if total_true_gaps == 0:
                logger.info(
                    f"✅ No TRUE gaps found for flow {flow_id} - assets are already ready for assessment"
                )
                # ✅ Fix Bug #22: Return special marker indicating "no gaps" (asset ready)
                # This is different from "generation failed" - it means the asset has complete data
                # The background task will recognize this and mark the questionnaire as "completed"
                return [
                    {"_no_gaps_marker": True, "reason": "All assets have complete data"}
                ]

            # Step 2: Data awareness map (ONE-TIME)
            logger.info(f"🧠 Creating data awareness map (ONE-TIME for flow {flow_id})")

            data_awareness_agent = DataAwarenessAgent()
            data_map = await data_awareness_agent.create_data_map(
                flow_id=flow_id,
                assets=existing_assets,
                intelligent_gaps=intelligent_gaps,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
            )

            logger.info(
                f"✅ Data awareness map created with "
                f"{len(data_map.get('assets', []))} assets analyzed"
            )

            # Step 3: Generate questions per-asset, per-section (NO TOOLS)
            logger.info(
                f"📝 Starting section question generation "
                f"({len(existing_assets)} assets × {len(ASSESSMENT_FLOW_SECTIONS)} sections)"
            )

            section_generator = SectionQuestionGenerator()
            all_sections = []
            previously_asked = []  # For cross-section deduplication

            for asset in existing_assets:
                asset_gaps = intelligent_gaps.get(str(asset.id), [])
                true_gaps = [g for g in asset_gaps if g.is_true_gap]

                if not true_gaps:
                    logger.info(
                        f"Asset {asset.name} ({asset.id}) has no TRUE gaps, skipping"
                    )
                    continue

                # Group gaps by section
                # ✅ Fix Bug #16: true_gaps contains IntelligentGap objects, use attribute access
                gaps_by_section = {}
                for gap in true_gaps:
                    section = gap.section  # ✅ Use attribute access, not subscript
                    if section not in gaps_by_section:
                        gaps_by_section[section] = []
                    gaps_by_section[section].append(gap)

                # Generate questions per section
                for section_id in ASSESSMENT_FLOW_SECTIONS:
                    section_gaps = gaps_by_section.get(section_id, [])

                    if not section_gaps:
                        logger.debug(
                            f"No TRUE gaps for section '{section_id}' on asset {asset.name}, skipping"
                        )
                        continue

                    # ✅ Fix Bug #16: section_gaps already contains IntelligentGap objects
                    # They were reconstructed via IntelligentGap.from_dict() in cache handling
                    # or created directly by IntelligentGapScanner - no conversion needed
                    gap_objects = section_gaps

                    # Generate questions for this section
                    # ✅ Fix Bug #17: Use correct parameter names matching generator signature
                    # ✅ Fix Bug #19: Pass string IDs - context IDs are UUIDs, not integers
                    questions = await section_generator.generate_questions_for_section(
                        asset_name=asset.name,
                        asset_id=str(asset.id),
                        section_name=section_id,
                        gaps=gap_objects,
                        asset_data=data_map,
                        previous_questions=previously_asked,
                        client_account_id=(
                            str(context.client_account_id)
                            if context.client_account_id
                            else ""
                        ),
                        engagement_id=(
                            str(context.engagement_id) if context.engagement_id else ""
                        ),
                    )

                    if questions:
                        # Store section in Redis for aggregation
                        section_data = {
                            "section_id": section_id,
                            "asset_id": str(asset.id),
                            "questions": questions,
                        }

                        await store_section_in_redis(
                            redis=redis.client,
                            flow_id=flow_id,
                            asset_id=asset.id,
                            section_id=section_id,
                            section_data=section_data,
                            ttl=3600,  # 1 hour TTL
                        )

                        all_sections.append(section_data)

                        # Track for cross-section deduplication
                        previously_asked.extend([q["question_text"] for q in questions])

                        logger.info(
                            f"✅ Generated {len(questions)} questions for "
                            f"asset {asset.name}, section '{section_id}'"
                        )

            if not all_sections:
                logger.warning(f"No sections generated for flow {flow_id}")
                return []

            # Step 4: Aggregate sections from Redis
            logger.info(f"📦 Aggregating sections from Redis for flow {flow_id}")
            aggregated_sections = await aggregate_sections_from_redis(
                redis=redis.client,
                flow_id=flow_id,
                asset_ids=[str(asset.id) for asset in existing_assets],
                sections=ASSESSMENT_FLOW_SECTIONS,
            )

            if not aggregated_sections:
                logger.warning(f"No sections aggregated from Redis for flow {flow_id}")
                return []

            # Step 5: Deduplicate common questions across assets
            logger.info(
                f"🔄 Deduplicating questions across {len(existing_assets)} asset(s)"
            )

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
                f"✅ Deduplication complete: {dedup_stats.get('original_count', 0)} questions → "
                f"{dedup_stats.get('deduplicated_count', 0)} questions "
                f"({dedup_stats.get('reduction_percentage', 0):.1f}% reduction)"
            )

            # Step 6: Cleanup Redis cache
            await cleanup_redis_cache(
                redis=redis.client,
                flow_id=flow_id,
                asset_ids=[asset.id for asset in existing_assets],
                sections=ASSESSMENT_FLOW_SECTIONS,
            )

            logger.info(
                f"🎉 Intelligent questionnaire generation complete for flow {flow_id}: "
                f"{len(deduplicated_sections)} sections with "
                f"{dedup_stats.get('deduplicated_count', 0)} questions"
            )

            return deduplicated_sections

        finally:
            await redis.close()

    except Exception as e:
        logger.error(
            f"❌ Intelligent questionnaire generation failed for flow {flow_id}: {e}",
            exc_info=True,
        )
        raise
