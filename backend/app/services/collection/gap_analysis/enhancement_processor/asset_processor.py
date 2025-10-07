"""Core asset processing logic for gap enhancement."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager

from ..context_filter import build_compact_asset_context
from ..output_parser import parse_task_output
from ..task_builder import build_asset_enhancement_task
from ..validation import sanitize_numeric_fields, validate_enhancement_output
from .constants import (
    MIN_ATTEMPTS_BEFORE_BREAKING,
    CIRCUIT_BREAKER_THRESHOLD,
    PER_ASSET_TIMEOUT,
)

logger = logging.getLogger(__name__)


def check_circuit_breaker(processed_count: int, failed_count: int) -> bool:
    """Check if circuit breaker should trigger.

    Args:
        processed_count: Number of successfully processed assets
        failed_count: Number of failed assets

    Returns:
        True if circuit breaker should trigger, False otherwise
    """
    total_attempts = processed_count + failed_count
    if total_attempts >= MIN_ATTEMPTS_BEFORE_BREAKING and failed_count > 0:
        failure_rate = failed_count / max(total_attempts, 1)
        if failure_rate > CIRCUIT_BREAKER_THRESHOLD:
            logger.error(
                f"🔴 Circuit breaker triggered: {failure_rate:.0%} failure rate "
                f"({failed_count}/{total_attempts} assets failed)"
            )
            return True
    return False


async def retrieve_pattern_learnings(
    memory_manager: TenantMemoryManager,
    client_account_id: str,
    engagement_id: str,
    asset,
    asset_gaps: List[Dict[str, Any]],
) -> List[Any]:
    """Retrieve similar patterns from memory (fail-safe).

    Args:
        memory_manager: TenantMemoryManager instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        asset: Asset object
        asset_gaps: List of gaps for this asset

    Returns:
        List of previous learnings
    """
    try:
        previous_learnings = await memory_manager.retrieve_similar_patterns(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            pattern_type="gap_enhancement",
            query_context={
                "asset_type": asset.asset_type,
                "gap_fields": [g.get("field_name") for g in asset_gaps],
            },
            limit=3,
        )
        logger.debug(f"📚 Retrieved {len(previous_learnings)} similar patterns")
        return previous_learnings
    except Exception as e:
        logger.warning(f"Learning retrieval failed (non-blocking): {e}")
        return []


async def execute_agent_with_timeout(
    execute_agent_task_method,
    agent,
    task_description: str,
) -> Optional[Any]:
    """Execute agent task with timeout.

    Args:
        execute_agent_task_method: Bound method for executing agent task
        agent: Agent instance
        task_description: Task description string

    Returns:
        Task output or None if timeout

    Raises:
        asyncio.TimeoutError: If task times out
    """
    return await asyncio.wait_for(
        execute_agent_task_method(agent, task_description),
        timeout=PER_ASSET_TIMEOUT,
    )


def parse_and_validate_output(
    task_output: Any, asset, asset_gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Parse and validate agent output.

    Args:
        task_output: Raw task output from agent
        asset: Asset object
        asset_gaps: List of gaps for validation

    Returns:
        Parsed and sanitized result dictionary
    """
    # Parse and validate
    result_dict = parse_task_output(task_output)

    # Strict schema validation
    validation_errors = validate_enhancement_output(result_dict, asset_gaps)
    if validation_errors:
        logger.warning(
            f"Validation errors for {asset.name}: {validation_errors[:3]}"  # Log first 3
        )
        # Continue despite validation errors (log but don't fail)

    # Sanitize numeric fields (remove NaN/Inf, clamp ranges)
    result_dict["gaps"] = sanitize_numeric_fields(result_dict.get("gaps", {}))

    return result_dict


def accumulate_enhanced_gaps(
    all_enhanced_gaps: Dict[str, List[Dict[str, Any]]], result_dict: Dict[str, Any]
):
    """Accumulate enhanced gaps from result.

    Args:
        all_enhanced_gaps: Dict to accumulate gaps into
        result_dict: Result dictionary from agent
    """
    for priority in ["critical", "high", "medium", "low"]:
        all_enhanced_gaps[priority].extend(
            result_dict.get("gaps", {}).get(priority, [])
        )


def calculate_gap_metrics(result_dict: Dict[str, Any]) -> float:
    """Calculate average confidence score (fail-safe).

    Args:
        result_dict: Result dictionary from agent

    Returns:
        Average confidence score or 0.0
    """
    try:
        avg_confidence = 0.0
        total_gaps_with_conf = 0

        for gaps_list in result_dict.get("gaps", {}).values():
            for gap in gaps_list:
                if "confidence_score" in gap:
                    avg_confidence += gap["confidence_score"]
                    total_gaps_with_conf += 1

        if total_gaps_with_conf > 0:
            avg_confidence = avg_confidence / total_gaps_with_conf

        return avg_confidence
    except Exception as e:
        logger.debug(f"Learning metrics calculation failed (non-blocking): {e}")
        return 0.0


async def process_single_asset(
    asset_id: str,
    asset_gaps: List[Dict[str, Any]],
    asset_lookup: Dict[str, Any],
    agent,
    memory_manager: TenantMemoryManager,
    client_account_id: str,
    engagement_id: str,
    tenant_safe_keys: set,
    redis_client,
    execute_agent_task_method,
    persist_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """Process a single asset's gaps.

    Args:
        asset_id: Asset ID to process
        asset_gaps: List of gaps for this asset
        asset_lookup: Dict mapping asset_id to Asset object
        agent: Agent instance
        memory_manager: TenantMemoryManager instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        tenant_safe_keys: Set of safe keys for filtering
        redis_client: Redis client (or None)
        execute_agent_task_method: Bound method for executing agent task
        persist_callback: Optional callback for persisting gaps (db, result_dict) -> int

    Returns:
        Dict with processing results
    """
    asset = asset_lookup.get(asset_id)
    if not asset:
        logger.warning(f"Asset {asset_id} not found, skipping")
        return {
            "success": False,
            "error_code": "asset_not_found",
            "asset_id": asset_id,
        }

    try:
        logger.info(
            f"🔄 Enhancing {len(asset_gaps)} gaps for {asset.name} ({asset.asset_type})"
        )

        # Build filtered context
        asset_context = build_compact_asset_context(
            asset, tenant_safe_keys, redis_client
        )

        # Retrieve learnings
        previous_learnings = await retrieve_pattern_learnings(
            memory_manager, client_account_id, engagement_id, asset, asset_gaps
        )

        # Build task
        task_description = build_asset_enhancement_task(
            asset_gaps=asset_gaps,
            asset_context=asset_context,
            previous_learnings=previous_learnings,
        )

        # Execute agent with timeout
        try:
            task_output = await execute_agent_with_timeout(
                execute_agent_task_method, agent, task_description
            )
        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ Asset {asset.name} enhancement timed out after {PER_ASSET_TIMEOUT}s"
            )
            return {
                "success": False,
                "error_code": "agent_timeout",
                "asset_id": asset_id,
                "asset_name": asset.name,
            }

        # Parse and validate
        result_dict = parse_and_validate_output(task_output, asset, asset_gaps)

        # Persist if callback provided
        gaps_persisted = 0
        if persist_callback:
            try:
                gaps_persisted = await persist_callback(result_dict)
            except Exception as persist_error:
                logger.error(
                    f"❌ Failed to persist gaps for {asset.name}: {persist_error}",
                    exc_info=True,
                )
                # Continue - don't fail for persistence error

        # Calculate metrics
        avg_confidence = calculate_gap_metrics(result_dict)
        logger.debug(
            f"📊 Gap enhancement metrics - Asset: {asset.name}, "
            f"Gaps: {len(asset_gaps)}, Avg Confidence: {avg_confidence:.2f}"
        )

        return {
            "success": True,
            "result_dict": result_dict,
            "gaps_persisted": gaps_persisted,
            "asset_name": asset.name,
        }

    except Exception as e:
        logger.error(f"❌ Asset {asset.name} enhancement failed: {e}", exc_info=True)
        return {
            "success": False,
            "error_code": "enhancement_failed",
            "error_message": str(e),
            "asset_id": asset_id,
            "asset_name": asset.name,
        }
