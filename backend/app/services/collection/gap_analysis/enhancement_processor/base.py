"""Base mixin for AI enhancement processing."""

import logging
from typing import Any, Dict, List

from app.core.redis_config import get_redis_manager

from .agent_setup import setup_agent_and_memory
from .asset_processor import (
    accumulate_enhanced_gaps,
    check_circuit_breaker,
    process_single_asset,
)
from .gap_helpers import (
    create_asset_lookup,
    group_gaps_by_asset,
    initialize_progress_tracking,
    load_tenant_safe_keys,
)
from .redis_lock import acquire_enhancement_lock, release_enhancement_lock

logger = logging.getLogger(__name__)


class EnhancementProcessorMixin:
    """Mixin providing AI enhancement processing for GapAnalysisService."""

    async def _run_tier_2_ai_analysis_no_persist(
        self, assets: list, collection_flow_id: str, gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run tier_2 AI enhancement without persistence (return gaps only).

        Architecture (Phase 3 - Asset-Batched Gap Enhancement):
        - ONE persistent TenantScoped agent for entire run
        - SEQUENTIAL asset processing (agent is single-threaded)
        - Redis distributed lock prevents multiple workers processing same flow
        - No DB persistence (return enhanced gaps for caller to handle)
        - TenantMemoryManager learning (fail-safe, non-blocking)
        - Circuit breaker if failure rate > 50%

        Args:
            assets: List of Asset objects loaded from database
            collection_flow_id: Collection flow UUID
            gaps: List of programmatic gaps to enhance

        Returns:
            Dict with AI-enhanced gaps and summary
        """
        return await self._run_tier_2_enhancement(
            assets=assets,
            collection_flow_id=collection_flow_id,
            gaps=gaps,
            db_session=self.db,  # For memory manager
            persist=False,
        )

    async def _run_tier_2_ai_analysis_with_persist(
        self, assets: list, collection_flow_id: str, gaps: List[Dict[str, Any]], db
    ) -> Dict[str, Any]:
        """Run tier_2 AI enhancement WITH per-asset persistence.

        Same as no_persist variant but writes enhanced gaps to DB immediately.

        Args:
            assets: List of Asset objects loaded from database
            collection_flow_id: Collection flow UUID
            gaps: List of programmatic gaps to enhance
            db: AsyncSession for database operations

        Returns:
            Dict with AI-enhanced gaps and persistence summary
        """
        return await self._run_tier_2_enhancement(
            assets=assets,
            collection_flow_id=collection_flow_id,
            gaps=gaps,
            db_session=db,
            persist=True,
        )

    async def _run_tier_2_enhancement(
        self,
        assets: list,
        collection_flow_id: str,
        gaps: List[Dict[str, Any]],
        db_session,
        persist: bool = False,
    ) -> Dict[str, Any]:
        """Core enhancement logic shared by both persist and no-persist variants.

        Args:
            assets: List of Asset objects
            collection_flow_id: Collection flow UUID
            gaps: List of gaps to enhance
            db_session: AsyncSession for DB operations
            persist: Whether to persist gaps immediately

        Returns:
            Dict with enhanced gaps and summary
        """
        # Get Redis client for distributed locking
        redis_manager = get_redis_manager()
        redis_client = redis_manager.client if redis_manager.is_available() else None

        if not redis_client:
            logger.warning(
                "Redis unavailable, proceeding without lock (single-worker assumed)"
            )

        # Acquire distributed lock
        lock_acquired, lock_key = await acquire_enhancement_lock(
            collection_flow_id, redis_client
        )

        try:
            # Setup agent and memory
            agent, memory_manager = await setup_agent_and_memory(
                self.client_account_id, self.engagement_id, db_session
            )

            # Prepare scanner for persistence (if needed)
            scanner = None
            if persist:
                from app.services.collection.programmatic_gap_scanner import (
                    ProgrammaticGapScanner,
                )

                scanner = ProgrammaticGapScanner()

            # Group gaps and create lookups
            gaps_by_asset = group_gaps_by_asset(gaps)
            asset_lookup = create_asset_lookup(assets)
            total_assets = len(gaps_by_asset)

            # Initialize progress tracking
            progress = initialize_progress_tracking()

            # Load tenant safe keys
            tenant_safe_keys = await load_tenant_safe_keys(
                self.client_account_id, redis_client
            )

            # Process assets SEQUENTIALLY
            for asset_id, asset_gaps in gaps_by_asset.items():
                # Check circuit breaker
                if check_circuit_breaker(
                    progress["processed_count"], progress["failed_count"]
                ):
                    break

                # Create persist callback if needed
                persist_callback = None
                if persist and scanner:
                    persist_callback = self._create_persist_callback(
                        scanner, collection_flow_id, db_session
                    )

                # Process single asset
                result = await process_single_asset(
                    asset_id=asset_id,
                    asset_gaps=asset_gaps,
                    asset_lookup=asset_lookup,
                    agent=agent,
                    memory_manager=memory_manager,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    tenant_safe_keys=tenant_safe_keys,
                    redis_client=redis_client,
                    execute_agent_task_method=self._execute_agent_task,
                    persist_callback=persist_callback,
                )

                # Update progress based on result
                if result["success"]:
                    accumulate_enhanced_gaps(
                        progress["all_enhanced_gaps"], result["result_dict"]
                    )
                    progress["total_gaps_persisted"] += result.get("gaps_persisted", 0)
                    progress["processed_count"] += 1

                    # Update progress in Redis
                    if redis_client:
                        try:
                            await self._update_progress(
                                collection_flow_id,
                                processed=progress["processed_count"],
                                total=total_assets,
                                current_asset=result.get("asset_name", "Unknown"),
                                redis_client=redis_client,
                            )
                        except Exception as e:
                            logger.warning(f"Progress update failed: {e}")
                else:
                    progress["failed_count"] += 1
                    progress["failed_assets"].append(
                        {
                            "asset_id": result.get("asset_id"),
                            "asset_name": result.get("asset_name"),
                            "error_code": result.get("error_code"),
                            "error_message": result.get("error_message"),
                        }
                    )

            # Return aggregated results
            logger.info(
                f"✅ Enhancement complete: {progress['processed_count']}/{total_assets} assets processed, "
                f"{progress['failed_count']} failed, {progress['total_gaps_persisted']} gaps persisted"
            )

            return {
                "gaps": progress["all_enhanced_gaps"],
                "questionnaire": {
                    "sections": []
                },  # No questionnaire in enhancement mode
                "summary": {
                    "total_gaps": sum(
                        len(v) for v in progress["all_enhanced_gaps"].values()
                    ),
                    "assets_analyzed": progress["processed_count"],
                    "assets_failed": progress["failed_count"],
                    "gaps_persisted": progress["total_gaps_persisted"],
                    "failed_assets": (
                        progress["failed_assets"] if progress["failed_assets"] else None
                    ),
                },
            }

        finally:
            # Release Redis lock
            await release_enhancement_lock(redis_client, lock_key, lock_acquired)

    def _create_persist_callback(self, scanner, collection_flow_id: str, db_session):
        """Create persistence callback for asset processing.

        Args:
            scanner: ProgrammaticGapScanner instance
            collection_flow_id: Collection flow UUID
            db_session: AsyncSession for DB operations

        Returns:
            Async callback function
        """

        async def persist_gaps(result_dict: Dict[str, Any]) -> int:
            """Persist enhanced gaps to database.

            Args:
                result_dict: Enhanced gaps result

            Returns:
                Number of gaps persisted
            """
            # Flatten gaps for persistence
            gaps_to_persist = []
            for priority in ["critical", "high", "medium", "low"]:
                gaps_to_persist.extend(result_dict.get("gaps", {}).get(priority, []))

            if not gaps_to_persist:
                return 0

            logger.debug(f"💾 Persisting {len(gaps_to_persist)} enhanced gaps")

            from uuid import UUID

            flow_uuid = (
                UUID(collection_flow_id)
                if isinstance(collection_flow_id, str)
                else collection_flow_id
            )

            gaps_persisted = await scanner._persist_gaps_with_dedup(
                gaps=gaps_to_persist,
                collection_flow_id=flow_uuid,
                db=db_session,
            )
            await db_session.commit()

            logger.info(f"✅ Persisted {gaps_persisted} gaps")
            return gaps_persisted

        return persist_gaps
