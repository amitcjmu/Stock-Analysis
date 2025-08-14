#!/usr/bin/env python3
"""
Backfill Master State from Child Records

This script backfills master flow state enrichment data from existing child flow records.
It synthesizes phase transitions, execution times, and metadata from discovery_flows data.

Usage:
    python scripts/maintenance/backfill_master_state_from_child.py [--dry-run] [--limit N]
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import argparse
import uuid

# Add parent directory to path for imports
sys.path.insert(0, "/app")

from sqlalchemy import select, update  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.crewai_flow_state_extensions import (  # noqa: E402
    CrewAIFlowStateExtensions,
)
from app.models.discovery_flow import DiscoveryFlow  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MasterStateBackfiller:
    """Backfills master flow state from child flow records."""

    def __init__(self, db_url: str, dry_run: bool = False):
        self.engine = create_async_engine(db_url, echo=False)
        self.AsyncSessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.dry_run = dry_run
        self.stats = {
            "flows_processed": 0,
            "flows_updated": 0,
            "flows_skipped": 0,
            "errors": 0,
        }

    async def get_recent_flows(
        self, limit: int = 100
    ) -> List[CrewAIFlowStateExtensions]:
        """Get recent master flows that may need backfilling."""
        async with self.AsyncSessionLocal() as session:
            # Get flows with empty or minimal enrichment data
            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(CrewAIFlowStateExtensions.flow_type == "discovery")
                .order_by(CrewAIFlowStateExtensions.created_at.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_child_flow_data(
        self, session: AsyncSession, flow_id: uuid.UUID
    ) -> Optional[DiscoveryFlow]:
        """Get child flow data for a master flow."""
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def synthesize_phase_transitions(
        self, child_flow: DiscoveryFlow
    ) -> List[Dict[str, Any]]:
        """Synthesize phase transitions from child flow data."""
        transitions = []

        # Map progress percentages to phases
        phase_map = {
            0: "initialization",
            10: "data_import",
            20: "data_validation",
            30: "field_mapping_generation",
            40: "field_mapping_approval",
            50: "data_cleansing",
            60: "asset_inventory",
            70: "dependency_analysis",
            80: "tech_debt_assessment",
            90: "sixr_strategy",
            100: "finalization",
        }

        # Get the current phase based on progress
        progress = child_flow.progress_percentage or 0
        current_phase = None
        for threshold, phase in sorted(phase_map.items()):
            if progress >= threshold:
                current_phase = phase
            else:
                break

        # Add completed transitions up to current phase
        if current_phase:
            base_time = child_flow.created_at
            for threshold, phase in sorted(phase_map.items()):
                if threshold <= progress:
                    # Add processing transition
                    transitions.append(
                        {
                            "phase": phase,
                            "status": "processing",
                            "timestamp": (
                                base_time + timedelta(minutes=threshold)
                            ).isoformat(),
                            "metadata": {"synthesized": True},
                        }
                    )

                    # Add completed transition if not the current phase
                    if threshold < progress:
                        transitions.append(
                            {
                                "phase": phase,
                                "status": "completed",
                                "timestamp": (
                                    base_time + timedelta(minutes=threshold + 5)
                                ).isoformat(),
                                "metadata": {
                                    "synthesized": True,
                                    "progress_at_completion": threshold,
                                },
                            }
                        )
                else:
                    break

        # Cap at 50 transitions
        return transitions[:50]

    def synthesize_execution_times(
        self, child_flow: DiscoveryFlow, transitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize phase execution times from transitions."""
        execution_times = {}

        # Calculate times based on transition pairs
        phase_starts = {}
        for transition in transitions:
            phase = transition["phase"]
            status = transition["status"]
            timestamp = datetime.fromisoformat(transition["timestamp"])

            if status == "processing":
                phase_starts[phase] = timestamp
            elif status == "completed" and phase in phase_starts:
                duration_ms = (timestamp - phase_starts[phase]).total_seconds() * 1000
                execution_times[phase] = {
                    "execution_time_ms": round(duration_ms, 2),
                    "recorded_at": timestamp.isoformat(),
                }

        return execution_times

    def synthesize_metadata(self, child_flow: DiscoveryFlow) -> Dict[str, Any]:
        """Synthesize flow metadata from child flow."""
        metadata = {
            "backfilled": True,
            "backfill_timestamp": datetime.utcnow().isoformat(),
            "source": "child_flow_synthesis",
        }

        # Extract key information from crewai_state_data if available
        if child_flow.crewai_state_data:
            try:
                state_data = child_flow.crewai_state_data
                if isinstance(state_data, dict):
                    # Extract progress snapshot
                    if "current_phase" in state_data:
                        metadata["last_known_phase"] = state_data["current_phase"]
                    if "progress" in state_data:
                        metadata["progress_snapshot"] = state_data["progress"]
            except Exception as e:
                logger.warning(f"Failed to extract state data: {e}")

        return metadata

    async def backfill_flow(self, master_flow: CrewAIFlowStateExtensions) -> bool:
        """Backfill a single master flow from its child data."""
        async with self.AsyncSessionLocal() as session:
            try:
                # Get child flow data
                child_flow = await self.get_child_flow_data(
                    session, master_flow.flow_id
                )
                if not child_flow:
                    logger.info(f"No child flow found for {master_flow.flow_id}")
                    self.stats["flows_skipped"] += 1
                    return False

                # Check if already has enrichment data
                if (
                    master_flow.phase_transitions
                    and len(master_flow.phase_transitions) > 0
                ):
                    logger.info(
                        f"Flow {master_flow.flow_id} already has enrichment data"
                    )
                    self.stats["flows_skipped"] += 1
                    return False

                # Synthesize enrichment data
                transitions = self.synthesize_phase_transitions(child_flow)
                execution_times = self.synthesize_execution_times(
                    child_flow, transitions
                )
                metadata = self.synthesize_metadata(child_flow)

                # Merge with existing metadata
                flow_metadata = master_flow.flow_metadata or {}
                flow_metadata.update(metadata)

                # Prepare update
                update_values = {
                    "phase_transitions": transitions,
                    "phase_execution_times": execution_times,
                    "flow_metadata": flow_metadata,
                    "updated_at": datetime.utcnow(),
                }

                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] Would update flow {master_flow.flow_id}:\n"
                        f"  - {len(transitions)} phase transitions\n"
                        f"  - {len(execution_times)} execution times\n"
                        f"  - Metadata keys: {list(metadata.keys())}"
                    )
                else:
                    # Execute update
                    stmt = (
                        update(CrewAIFlowStateExtensions)
                        .where(CrewAIFlowStateExtensions.flow_id == master_flow.flow_id)
                        .values(**update_values)
                    )
                    await session.execute(stmt)
                    await session.commit()

                    logger.info(
                        f"✅ Updated flow {master_flow.flow_id} with "
                        f"{len(transitions)} transitions and "
                        f"{len(execution_times)} execution times"
                    )

                self.stats["flows_updated"] += 1
                return True

            except Exception as e:
                logger.error(f"Failed to backfill flow {master_flow.flow_id}: {e}")
                self.stats["errors"] += 1
                return False

    async def run(self, limit: int = 100):
        """Run the backfill process."""
        logger.info(
            f"Starting backfill process (dry_run={self.dry_run}, limit={limit})"
        )

        # Get flows to process
        flows = await self.get_recent_flows(limit)
        logger.info(f"Found {len(flows)} flows to process")

        # Process each flow
        for flow in flows:
            self.stats["flows_processed"] += 1
            await self.backfill_flow(flow)

        # Print summary
        logger.info("=" * 60)
        logger.info("Backfill Summary:")
        logger.info(f"  Flows processed: {self.stats['flows_processed']}")
        logger.info(f"  Flows updated: {self.stats['flows_updated']}")
        logger.info(f"  Flows skipped: {self.stats['flows_skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info("=" * 60)

    async def cleanup(self):
        """Clean up resources."""
        await self.engine.dispose()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill master flow state from child records"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no database changes)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of flows to process (default: 100)",
    )

    args = parser.parse_args()

    # Get database URL from environment or settings
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    # Run backfill
    backfiller = MasterStateBackfiller(db_url, dry_run=args.dry_run)
    try:
        await backfiller.run(limit=args.limit)
    finally:
        await backfiller.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
