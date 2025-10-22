"""
Bulk analysis background task.
Handles parallel processing of multiple analyses with batching.
"""

import asyncio
import logging
from typing import List

from .initial_analysis_task import run_initial_analysis

logger = logging.getLogger(__name__)


async def run_bulk_analysis(
    decision_engine, analysis_ids: List[int], batch_size: int, user: str
):
    """
    Run bulk analysis for multiple applications.

    Args:
        decision_engine: SixRDecisionEngine instance for analysis
        analysis_ids: List of analysis IDs to process
        batch_size: Number of analyses to process in parallel per batch
        user: User who initiated the bulk analysis
    """
    try:
        for i in range(0, len(analysis_ids), batch_size):
            batch = analysis_ids[i : i + batch_size]

            # Process batch in parallel
            tasks = []
            for analysis_id in batch:
                task = run_initial_analysis(decision_engine, analysis_id, {}, user)
                tasks.append(task)

            # Wait for batch completion
            await asyncio.gather(*tasks, return_exceptions=True)

            # Small delay between batches to avoid overwhelming the system
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Failed to run bulk analysis: {e}")
