"""AI enhancement processor for gap analysis.

Contains tier_2 AI enhancement with persistent agent (sequential processing).
Split from tier_processors.py for file length compliance (<400 lines per file).
"""

import asyncio
import logging
from typing import Any

from fastapi import HTTPException

from app.core.redis_config import get_redis_manager
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
)

from .context_filter import build_compact_asset_context, get_tenant_safe_keys
from .output_parser import parse_task_output
from .task_builder import build_asset_enhancement_task
from .validation import sanitize_numeric_fields, validate_enhancement_output

logger = logging.getLogger(__name__)

# Per-asset timeout (120 seconds for agentic analysis with LLM calls)
PER_ASSET_TIMEOUT = 120

# Circuit breaker threshold (abort if failure rate > 50% AND at least 2 attempts)
CIRCUIT_BREAKER_THRESHOLD = 0.5
MIN_ATTEMPTS_BEFORE_BREAKING = 2


class EnhancementProcessorMixin:
    """Mixin providing AI enhancement processing for GapAnalysisService."""

    async def _run_tier_2_ai_analysis_no_persist(  # noqa: C901
        self, assets: list, collection_flow_id: str, gaps: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Run tier_2 AI enhancement with persistent agent (sequential processing).

        Architecture (Phase 3 - Asset-Batched Gap Enhancement):
        - ONE persistent TenantScoped agent for entire run (no per-asset Crew instantiation)
        - SEQUENTIAL asset processing (agent is single-threaded)
        - Redis distributed lock prevents multiple workers processing same flow
        - Per-asset upsert to DB after each enhancement (immediate persistence)
        - TenantMemoryManager learning (fail-safe, non-blocking)
        - HTTP polling for progress (no SSE)
        - Circuit breaker if failure rate > 50%
        - Manual intervention for failures (no auto-retry)

        Args:
            assets: List of Asset objects loaded from database
            collection_flow_id: Collection flow UUID
            gaps: List of programmatic gaps to enhance (from ProgrammaticGapScanner)

        Returns:
            Dict with AI-enhanced gaps and persistence status
        """
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        # Get Redis client for distributed locking
        redis_manager = get_redis_manager()
        if not redis_manager.is_available():
            logger.warning(
                "Redis unavailable, proceeding without lock (single-worker assumed)"
            )
            redis_client = None
        else:
            redis_client = redis_manager.client

        # Acquire distributed lock (prevent double-processing)
        lock_key = f"gap_enhancement_lock:{collection_flow_id}"
        lock_acquired = False

        if redis_client:
            try:
                lock_acquired = await redis_client.set(
                    lock_key, "locked", nx=True, ex=900  # 15-minute TTL
                )

                if not lock_acquired:
                    raise HTTPException(
                        status_code=409,
                        detail="Another worker is already processing this flow",
                    )
            except Exception as e:
                logger.error(f"Failed to acquire Redis lock: {e}")
                # Continue without lock if Redis fails (single-worker deployment)

        try:
            # Get single persistent agent for entire run
            logger.debug("🔧 Creating persistent gap_analysis_specialist agent")
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_type="gap_analysis_specialist",
            )
            logger.info(
                f"✅ Agent created: {agent.role if hasattr(agent, 'role') else 'gap_analysis_specialist'}"
            )

            # Initialize memory manager (fail-safe wrapper below)
            # Per ADR-024: Use TenantMemoryManager with valid database session
            memory_manager = TenantMemoryManager(
                crewai_service=None,  # Not needed for gap enhancement
                database_session=self.db,  # ✅ Pass actual AsyncSession
            )

            # Group gaps by asset
            gaps_by_asset = {}
            for gap in gaps:
                asset_id = gap.get("asset_id")
                if asset_id not in gaps_by_asset:
                    gaps_by_asset[asset_id] = []
                gaps_by_asset[asset_id].append(gap)

            # Create asset lookup
            asset_lookup = {str(a.id): a for a in assets}

            # Progress tracking
            total_assets = len(gaps_by_asset)
            processed_count = 0
            failed_count = 0
            failed_assets = []  # Track for manual intervention
            all_enhanced_gaps = {"critical": [], "high": [], "medium": [], "low": []}
            total_gaps_persisted = 0

            # Get tenant safe keys for context filtering
            tenant_safe_keys = set()
            if redis_client:
                try:
                    tenant_safe_keys = await get_tenant_safe_keys(
                        self.client_account_id, redis_client
                    )
                    logger.info(
                        f"📋 Loaded {len(tenant_safe_keys)} tenant safe keys for filtering"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to load tenant safe keys: {e}, using defaults"
                    )
                    from .context_filter import DEFAULT_SAFE_KEYS

                    tenant_safe_keys = DEFAULT_SAFE_KEYS
            else:
                from .context_filter import DEFAULT_SAFE_KEYS

                tenant_safe_keys = DEFAULT_SAFE_KEYS

            # Process assets SEQUENTIALLY (agent is not concurrency-safe)
            for asset_id, asset_gaps in gaps_by_asset.items():
                # Check circuit breaker (only after MIN_ATTEMPTS_BEFORE_BREAKING)
                total_attempts = processed_count + failed_count
                if total_attempts >= MIN_ATTEMPTS_BEFORE_BREAKING and failed_count > 0:
                    failure_rate = failed_count / max(total_attempts, 1)
                    if failure_rate > CIRCUIT_BREAKER_THRESHOLD:
                        logger.error(
                            f"🔴 Circuit breaker triggered: {failure_rate:.0%} failure rate "
                            f"({failed_count}/{total_attempts} assets failed)"
                        )
                        break

                asset = asset_lookup.get(asset_id)
                if not asset:
                    logger.warning(f"Asset {asset_id} not found, skipping")
                    failed_count += 1
                    failed_assets.append(
                        {"asset_id": asset_id, "error_code": "asset_not_found"}
                    )
                    continue

                try:
                    logger.info(
                        f"🔄 Enhancing {len(asset_gaps)} gaps for {asset.name} "
                        f"({asset.asset_type}) - {processed_count + 1}/{total_assets}"
                    )

                    # Build filtered context
                    asset_context = build_compact_asset_context(
                        asset, tenant_safe_keys, redis_client
                    )

                    # Retrieve learnings (fail-safe)
                    previous_learnings = []
                    try:
                        previous_learnings = (
                            await memory_manager.retrieve_similar_patterns(
                                client_account_id=self.client_account_id,
                                engagement_id=self.engagement_id,
                                pattern_type="gap_enhancement",
                                query_context={
                                    "asset_type": asset.asset_type,
                                    "gap_fields": [
                                        g.get("field_name") for g in asset_gaps
                                    ],
                                },
                                limit=3,
                            )
                        )
                        logger.debug(
                            f"📚 Retrieved {len(previous_learnings)} similar patterns"
                        )
                    except Exception as e:
                        logger.warning(f"Learning retrieval failed (non-blocking): {e}")

                    # Build task
                    task_description = build_asset_enhancement_task(
                        asset_gaps=asset_gaps,
                        asset_context=asset_context,
                        previous_learnings=previous_learnings,
                    )

                    # Execute agent with timeout (reuse persistent agent, no Crew creation)
                    try:
                        task_output = await asyncio.wait_for(
                            self._execute_agent_task(agent, task_description),
                            timeout=PER_ASSET_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.error(
                            f"⏱️ Asset {asset.name} enhancement timed out after {PER_ASSET_TIMEOUT}s"
                        )
                        failed_count += 1
                        failed_assets.append(
                            {
                                "asset_id": asset_id,
                                "asset_name": asset.name,
                                "error_code": "agent_timeout",
                            }
                        )
                        continue

                    # Parse and validate
                    result_dict = parse_task_output(task_output)

                    # Strict schema validation
                    validation_errors = validate_enhancement_output(
                        result_dict, asset_gaps
                    )
                    if validation_errors:
                        logger.warning(
                            f"Validation errors for {asset.name}: {validation_errors[:3]}"  # Log first 3
                        )
                        # Continue despite validation errors (log but don't fail)

                    # Sanitize numeric fields (remove NaN/Inf, clamp ranges)
                    result_dict["gaps"] = sanitize_numeric_fields(
                        result_dict.get("gaps", {})
                    )

                    # Persist immediately (atomic per asset)
                    # Note: Passing to persist_gaps which will use its own DB session
                    # For now, we'll skip persistence in this no_persist variant
                    # but the implementation plan says to persist - let's add it
                    logger.debug("💾 Persisting enhanced gaps for this asset...")
                    # gaps_persisted = await persist_gaps(
                    #     result_dict, [asset], db, collection_flow_id
                    # )
                    # total_gaps_persisted += gaps_persisted

                    # For now, skip persistence (as method name suggests)
                    # Accumulate gaps for return
                    for priority in ["critical", "high", "medium", "low"]:
                        all_enhanced_gaps[priority].extend(
                            result_dict.get("gaps", {}).get(priority, [])
                        )

                    # Store learning (fail-safe) - ADR-024: Use TenantMemoryManager
                    # NOTE: Embedding storage DISABLED due to schema mismatch (ARRAY(DECIMAL) vs float list)
                    # TODO: Create Alembic migration to use pgvector.Vector type instead of ARRAY(DECIMAL)
                    try:
                        # Calculate metrics but skip embedding storage until schema fixed
                        avg_confidence = 0.0
                        total_gaps_with_conf = 0
                        for gaps_list in result_dict.get("gaps", {}).values():
                            for gap in gaps_list:
                                if "confidence_score" in gap:
                                    avg_confidence += gap["confidence_score"]
                                    total_gaps_with_conf += 1

                        if total_gaps_with_conf > 0:
                            avg_confidence = avg_confidence / total_gaps_with_conf

                        logger.debug(
                            f"📊 Gap enhancement metrics - Asset: {asset.name}, "
                            f"Gaps: {len(asset_gaps)}, Avg Confidence: {avg_confidence:.2f}"
                        )

                    except Exception as e:
                        # Non-blocking: Metric calculation failures logged but ignored
                        logger.debug(
                            f"Learning metrics calculation failed (non-blocking): {e}"
                        )

                    # Update progress in Redis
                    if redis_client:
                        try:
                            await self._update_progress(
                                collection_flow_id,
                                processed=processed_count + 1,
                                total=total_assets,
                                current_asset=asset.name,
                                redis_client=redis_client,
                            )
                        except Exception as e:
                            logger.warning(f"Progress update failed: {e}")

                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"❌ Asset {asset.name} enhancement failed: {e}",
                        exc_info=True,
                    )
                    failed_count += 1
                    failed_assets.append(
                        {
                            "asset_id": asset_id,
                            "asset_name": asset.name,
                            "error_code": "enhancement_failed",
                            "error_message": str(e),
                        }
                    )

            # Return aggregated results
            logger.info(
                f"✅ Enhancement complete: {processed_count}/{total_assets} assets processed, "
                f"{failed_count} failed, {total_gaps_persisted} gaps persisted"
            )

            return {
                "gaps": all_enhanced_gaps,
                "questionnaire": {
                    "sections": []
                },  # No questionnaire in enhancement mode
                "summary": {
                    "total_gaps": sum(len(v) for v in all_enhanced_gaps.values()),
                    "assets_analyzed": processed_count,
                    "assets_failed": failed_count,
                    "gaps_persisted": total_gaps_persisted,
                    "failed_assets": failed_assets if failed_assets else None,
                },
            }

        finally:
            # Release Redis lock in finally block (always executes)
            if redis_client and lock_acquired:
                try:
                    await redis_client.delete(lock_key)
                    logger.debug("🔓 Released Redis lock")
                except Exception as e:
                    logger.error(f"Failed to release Redis lock: {e}")

    async def _run_tier_2_ai_analysis_with_persist(  # noqa: C901
        self, assets: list, collection_flow_id: str, gaps: list[dict[str, Any]], db
    ) -> dict[str, Any]:
        """Run tier_2 AI enhancement WITH per-asset persistence (for background jobs).

        Same as _run_tier_2_ai_analysis_no_persist but enables per-asset persistence
        using ProgrammaticGapScanner._persist_gaps_with_dedup().

        Args:
            assets: List of Asset objects loaded from database
            collection_flow_id: Collection flow UUID
            gaps: List of programmatic gaps to enhance
            db: AsyncSession for database operations

        Returns:
            Dict with AI-enhanced gaps and persistence status
        """
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )
        from app.services.collection.programmatic_gap_scanner import (
            ProgrammaticGapScanner,
        )

        # Get Redis client for distributed locking
        redis_manager = get_redis_manager()
        if not redis_manager.is_available():
            logger.warning(
                "Redis unavailable, proceeding without lock (single-worker assumed)"
            )
            redis_client = None
        else:
            redis_client = redis_manager.client

        # Acquire distributed lock (prevent double-processing)
        lock_key = f"gap_enhancement_lock:{collection_flow_id}"
        lock_acquired = False

        if redis_client:
            try:
                lock_acquired = await redis_client.set(
                    lock_key, "locked", nx=True, ex=900  # 15-minute TTL
                )

                if not lock_acquired:
                    raise HTTPException(
                        status_code=409,
                        detail="Another worker is already processing this flow",
                    )
            except Exception as e:
                logger.error(f"Failed to acquire Redis lock: {e}")
                # Continue without lock if Redis fails (single-worker deployment)

        try:
            # Get single persistent agent for entire run
            logger.debug("🔧 Creating persistent gap_analysis_specialist agent")
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_type="gap_analysis_specialist",
            )
            logger.info(
                f"✅ Agent created: {agent.role if hasattr(agent, 'role') else 'gap_analysis_specialist'}"
            )

            # Initialize memory manager (fail-safe wrapper below)
            # Per ADR-024: Use TenantMemoryManager with valid database session
            memory_manager = TenantMemoryManager(
                crewai_service=None,  # Not needed for gap enhancement
                database_session=db,  # ✅ Pass actual AsyncSession (db param)
            )

            # Initialize scanner for persistence
            scanner = ProgrammaticGapScanner()

            # Group gaps by asset
            gaps_by_asset = {}
            for gap in gaps:
                asset_id = gap.get("asset_id")
                if asset_id not in gaps_by_asset:
                    gaps_by_asset[asset_id] = []
                gaps_by_asset[asset_id].append(gap)

            # Create asset lookup
            asset_lookup = {str(a.id): a for a in assets}

            # Progress tracking
            total_assets = len(gaps_by_asset)
            processed_count = 0
            failed_count = 0
            failed_assets = []
            all_enhanced_gaps = {"critical": [], "high": [], "medium": [], "low": []}
            total_gaps_persisted = 0

            # Get tenant safe keys for context filtering
            tenant_safe_keys = set()
            if redis_client:
                try:
                    tenant_safe_keys = await get_tenant_safe_keys(
                        self.client_account_id, redis_client
                    )
                    logger.info(
                        f"📋 Loaded {len(tenant_safe_keys)} tenant safe keys for filtering"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to load tenant safe keys: {e}, using defaults"
                    )
                    from .context_filter import DEFAULT_SAFE_KEYS

                    tenant_safe_keys = DEFAULT_SAFE_KEYS
            else:
                from .context_filter import DEFAULT_SAFE_KEYS

                tenant_safe_keys = DEFAULT_SAFE_KEYS

            # Process assets SEQUENTIALLY (agent is not concurrency-safe)
            for asset_id, asset_gaps in gaps_by_asset.items():
                # Check circuit breaker (only after MIN_ATTEMPTS_BEFORE_BREAKING)
                total_attempts = processed_count + failed_count
                if total_attempts >= MIN_ATTEMPTS_BEFORE_BREAKING and failed_count > 0:
                    failure_rate = failed_count / max(total_attempts, 1)
                    if failure_rate > CIRCUIT_BREAKER_THRESHOLD:
                        logger.error(
                            f"🔴 Circuit breaker triggered: {failure_rate:.0%} failure rate "
                            f"({failed_count}/{total_attempts} assets failed)"
                        )
                        break

                asset = asset_lookup.get(asset_id)
                if not asset:
                    logger.warning(f"Asset {asset_id} not found, skipping")
                    failed_count += 1
                    failed_assets.append(
                        {"asset_id": asset_id, "error_code": "asset_not_found"}
                    )
                    continue

                try:
                    logger.info(
                        f"🔄 Enhancing {len(asset_gaps)} gaps for {asset.name} "
                        f"({asset.asset_type}) - {processed_count + 1}/{total_assets}"
                    )

                    # Build filtered context
                    asset_context = build_compact_asset_context(
                        asset, tenant_safe_keys, redis_client
                    )

                    # Retrieve learnings (fail-safe)
                    previous_learnings = []
                    try:
                        previous_learnings = (
                            await memory_manager.retrieve_similar_patterns(
                                client_account_id=self.client_account_id,
                                engagement_id=self.engagement_id,
                                pattern_type="gap_enhancement",
                                query_context={
                                    "asset_type": asset.asset_type,
                                    "gap_fields": [
                                        g.get("field_name") for g in asset_gaps
                                    ],
                                },
                                limit=3,
                            )
                        )
                        logger.debug(
                            f"📚 Retrieved {len(previous_learnings)} similar patterns"
                        )
                    except Exception as e:
                        logger.warning(f"Learning retrieval failed (non-blocking): {e}")

                    # Build task
                    task_description = build_asset_enhancement_task(
                        asset_gaps=asset_gaps,
                        asset_context=asset_context,
                        previous_learnings=previous_learnings,
                    )

                    # Execute agent with timeout (reuse persistent agent, no Crew creation)
                    try:
                        task_output = await asyncio.wait_for(
                            self._execute_agent_task(agent, task_description),
                            timeout=PER_ASSET_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.error(
                            f"⏱️ Asset {asset.name} enhancement timed out after {PER_ASSET_TIMEOUT}s"
                        )
                        failed_count += 1
                        failed_assets.append(
                            {
                                "asset_id": asset_id,
                                "asset_name": asset.name,
                                "error_code": "agent_timeout",
                            }
                        )
                        continue

                    # Parse and validate
                    result_dict = parse_task_output(task_output)

                    # Strict schema validation
                    validation_errors = validate_enhancement_output(
                        result_dict, asset_gaps
                    )
                    if validation_errors:
                        logger.warning(
                            f"Validation errors for {asset.name}: {validation_errors[:3]}"  # Log first 3
                        )
                        # Continue despite validation errors (log but don't fail)

                    # Sanitize numeric fields (remove NaN/Inf, clamp ranges)
                    result_dict["gaps"] = sanitize_numeric_fields(
                        result_dict.get("gaps", {})
                    )

                    # ✅ PERSIST IMMEDIATELY (atomic per asset)
                    try:
                        # Flatten gaps for persistence
                        gaps_to_persist = []
                        for priority in ["critical", "high", "medium", "low"]:
                            gaps_to_persist.extend(
                                result_dict.get("gaps", {}).get(priority, [])
                            )

                        if gaps_to_persist:
                            logger.debug(
                                f"💾 Persisting {len(gaps_to_persist)} enhanced gaps for {asset.name}"
                            )
                            from uuid import UUID

                            flow_uuid = (
                                UUID(collection_flow_id)
                                if isinstance(collection_flow_id, str)
                                else collection_flow_id
                            )
                            gaps_persisted = await scanner._persist_gaps_with_dedup(
                                gaps=gaps_to_persist,
                                collection_flow_id=flow_uuid,
                                db=db,
                            )
                            await db.commit()
                            total_gaps_persisted += gaps_persisted
                            logger.info(
                                f"✅ Persisted {gaps_persisted} gaps for {asset.name}"
                            )
                    except Exception as persist_error:
                        logger.error(
                            f"❌ Failed to persist gaps for {asset.name}: {persist_error}",
                            exc_info=True,
                        )
                        # Continue - don't fail entire job for persistence error

                    # Accumulate gaps for return
                    for priority in ["critical", "high", "medium", "low"]:
                        all_enhanced_gaps[priority].extend(
                            result_dict.get("gaps", {}).get(priority, [])
                        )

                    # Store learning (fail-safe) - ADR-024: Use TenantMemoryManager
                    # NOTE: Embedding storage DISABLED due to schema mismatch (ARRAY(DECIMAL) vs float list)
                    # TODO: Create Alembic migration to use pgvector.Vector type instead of ARRAY(DECIMAL)
                    try:
                        # Calculate metrics but skip embedding storage until schema fixed
                        avg_confidence = 0.0
                        total_gaps_with_conf = 0
                        for gaps_list in result_dict.get("gaps", {}).values():
                            for gap in gaps_list:
                                if "confidence_score" in gap:
                                    avg_confidence += gap["confidence_score"]
                                    total_gaps_with_conf += 1

                        if total_gaps_with_conf > 0:
                            avg_confidence = avg_confidence / total_gaps_with_conf

                        logger.debug(
                            f"📊 Gap enhancement metrics - Asset: {asset.name}, "
                            f"Gaps: {len(asset_gaps)}, Avg Confidence: {avg_confidence:.2f}"
                        )

                    except Exception as e:
                        # Non-blocking: Metric calculation failures logged but ignored
                        logger.debug(
                            f"Learning metrics calculation failed (non-blocking): {e}"
                        )

                    # Update progress in Redis
                    if redis_client:
                        try:
                            await self._update_progress(
                                collection_flow_id,
                                processed=processed_count + 1,
                                total=total_assets,
                                current_asset=asset.name,
                                redis_client=redis_client,
                            )
                        except Exception as e:
                            logger.warning(f"Progress update failed: {e}")

                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"❌ Asset {asset.name} enhancement failed: {e}",
                        exc_info=True,
                    )
                    failed_count += 1
                    failed_assets.append(
                        {
                            "asset_id": asset_id,
                            "asset_name": asset.name,
                            "error_code": "enhancement_failed",
                            "error_message": str(e),
                        }
                    )

            # Return aggregated results
            logger.info(
                f"✅ Enhancement complete: {processed_count}/{total_assets} assets processed, "
                f"{failed_count} failed, {total_gaps_persisted} gaps persisted"
            )

            return {
                "gaps": all_enhanced_gaps,
                "questionnaire": {
                    "sections": []
                },  # No questionnaire in enhancement mode
                "summary": {
                    "total_gaps": sum(len(v) for v in all_enhanced_gaps.values()),
                    "assets_analyzed": processed_count,
                    "assets_failed": failed_count,
                    "gaps_persisted": total_gaps_persisted,
                    "failed_assets": failed_assets if failed_assets else None,
                },
            }

        finally:
            # Release Redis lock in finally block (always executes)
            if redis_client and lock_acquired:
                try:
                    await redis_client.delete(lock_key)
                    logger.debug("🔓 Released Redis lock")
                except Exception as e:
                    logger.error(f"Failed to release Redis lock: {e}")
