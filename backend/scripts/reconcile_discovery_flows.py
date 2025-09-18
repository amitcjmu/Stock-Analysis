#!/usr/bin/env python3
"""
Discovery Flow Data Reconciliation Script

This script reconciles discovery flow completion flags and progress data
by inferring flags from existing artifacts and fixing inconsistent state.

Usage:
    python reconcile_discovery_flows.py --dry-run
    python reconcile_discovery_flows.py --apply
    python reconcile_discovery_flows.py --apply --client-id CLIENT_UUID
    python reconcile_discovery_flows.py --dry-run --output-csv report.csv

CC: This script implements the reconciliation functionality specified in
the discovery flow data population implementation plan.
"""

import argparse
import asyncio
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.discovery_flow import DiscoveryFlow  # noqa: E402

logger = logging.getLogger(__name__)


class DiscoveryFlowReconciler:
    """Reconciles discovery flow completion flags and state."""

    def __init__(self, db: AsyncSession, dry_run: bool = True):
        self.db = db
        self.dry_run = dry_run
        self.changes_report: List[Dict[str, Any]] = []

    async def reconcile_all_flows(
        self, client_account_id: Optional[str] = None
    ) -> Tuple[int, int, int]:
        """
        Reconcile all discovery flows or flows for a specific client.

        Returns:
            Tuple of (total_flows, flows_with_changes, total_changes)
        """
        logger.info(f"Starting reconciliation (dry_run={self.dry_run})")

        # Build query
        query = select(DiscoveryFlow)
        if client_account_id:
            query = query.where(
                DiscoveryFlow.client_account_id == UUID(client_account_id)
            )

        result = await self.db.execute(query)
        flows = result.scalars().all()

        total_flows = len(flows)
        flows_with_changes = 0
        total_changes = 0

        logger.info(f"Found {total_flows} flows to reconcile")

        for flow in flows:
            changes = await self._reconcile_single_flow(flow)
            if changes:
                flows_with_changes += 1
                total_changes += len(changes)

                # Record changes for reporting
                self.changes_report.extend(changes)

                # Apply changes if not dry run
                if not self.dry_run:
                    await self._apply_changes(flow, changes)

        if not self.dry_run:
            await self.db.commit()
            logger.info("Changes committed to database")

        return total_flows, flows_with_changes, total_changes

    async def _reconcile_single_flow(self, flow: DiscoveryFlow) -> List[Dict[str, Any]]:
        """
        Reconcile a single discovery flow.

        Returns:
            List of changes to be made
        """
        changes = []

        # Check data import completion
        data_import_completed = await self._check_data_import_completion(flow)
        if data_import_completed != flow.data_import_completed:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "data_import_completed",
                    "old_value": flow.data_import_completed,
                    "new_value": data_import_completed,
                    "reason": "Has data_import_id and raw import records",
                }
            )

        # Check field mapping completion
        field_mapping_completed = await self._check_field_mapping_completion(flow)
        if field_mapping_completed != flow.field_mapping_completed:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "field_mapping_completed",
                    "old_value": flow.field_mapping_completed,
                    "new_value": field_mapping_completed,
                    "reason": "Has field_mappings JSON data",
                }
            )

        # Check asset inventory completion
        asset_inventory_completed = await self._check_asset_inventory_completion(flow)
        if asset_inventory_completed != flow.asset_inventory_completed:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "asset_inventory_completed",
                    "old_value": flow.asset_inventory_completed,
                    "new_value": asset_inventory_completed,
                    "reason": "Has discovered_assets JSON data or linked assets",
                }
            )

        # Check dependency analysis completion
        dependency_analysis_completed = (
            await self._check_dependency_analysis_completion(flow)
        )
        if dependency_analysis_completed != flow.dependency_analysis_completed:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "dependency_analysis_completed",
                    "old_value": flow.dependency_analysis_completed,
                    "new_value": dependency_analysis_completed,
                    "reason": "Has dependencies JSON data",
                }
            )

        # Check tech debt assessment completion
        tech_debt_completed = await self._check_tech_debt_completion(flow)
        if tech_debt_completed != flow.tech_debt_assessment_completed:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "tech_debt_assessment_completed",
                    "old_value": flow.tech_debt_assessment_completed,
                    "new_value": tech_debt_completed,
                    "reason": "Has tech_debt_analysis JSON data",
                }
            )

        # Check current phase consistency
        expected_phase = self._calculate_current_phase(
            data_import_completed,
            field_mapping_completed,
            flow.data_cleansing_completed,  # Keep current value
            asset_inventory_completed,
            dependency_analysis_completed,
            tech_debt_completed,
        )
        if expected_phase != flow.current_phase:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "current_phase",
                    "old_value": flow.current_phase,
                    "new_value": expected_phase,
                    "reason": "Phase inconsistent with completion flags",
                }
            )

        # Check completion status
        all_phases_complete = all(
            [
                data_import_completed,
                field_mapping_completed,
                flow.data_cleansing_completed,  # Keep current
                asset_inventory_completed,
                dependency_analysis_completed,
                tech_debt_completed,
            ]
        )

        if all_phases_complete and flow.status != "completed":
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "status",
                    "old_value": flow.status,
                    "new_value": "completed",
                    "reason": "All phases complete",
                }
            )

        if all_phases_complete and flow.completed_at is None:
            changes.append(
                {
                    "flow_id": str(flow.flow_id),
                    "client_account_id": str(flow.client_account_id),
                    "field": "completed_at",
                    "old_value": None,
                    "new_value": datetime.utcnow().isoformat(),
                    "reason": "All phases complete but no completion timestamp",
                }
            )

        return changes

    async def _check_data_import_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if data import is complete based on artifacts."""
        if not flow.data_import_id:
            return False

        # Check for raw import records
        try:
            from app.models import RawImportRecord

            raw_count_result = await self.db.execute(
                select(RawImportRecord.id)
                .where(RawImportRecord.data_import_id == flow.data_import_id)
                .limit(1)
            )
            has_raw_data = raw_count_result.scalar() is not None
            return has_raw_data
        except Exception as e:
            logger.warning(f"Could not check raw import records: {e}")
            return bool(flow.data_import_id)

    async def _check_field_mapping_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if field mapping is complete based on artifacts."""
        return bool(
            flow.field_mappings
            and (isinstance(flow.field_mappings, (dict, list)) and flow.field_mappings)
        )

    async def _check_asset_inventory_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if asset inventory is complete based on artifacts."""
        # Check discovered_assets JSON
        has_discovered_assets = bool(
            flow.discovered_assets
            and isinstance(flow.discovered_assets, (dict, list))
            and flow.discovered_assets
        )

        if has_discovered_assets:
            return True

        # Check for linked assets in assets table
        try:
            from app.models.asset import Asset

            asset_count_result = await self.db.execute(
                select(Asset.id)
                .where(
                    and_(
                        Asset.discovery_flow_id == flow.flow_id,
                        Asset.client_account_id == flow.client_account_id,
                    )
                )
                .limit(1)
            )
            has_linked_assets = asset_count_result.scalar() is not None
            return has_linked_assets
        except Exception as e:
            logger.warning(f"Could not check linked assets: {e}")
            return has_discovered_assets

    async def _check_dependency_analysis_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if dependency analysis is complete based on artifacts."""
        return bool(
            flow.dependencies
            and isinstance(flow.dependencies, (dict, list))
            and flow.dependencies
        )

    async def _check_tech_debt_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if tech debt assessment is complete based on artifacts."""
        return bool(
            flow.tech_debt_analysis
            and isinstance(flow.tech_debt_analysis, (dict, list))
            and flow.tech_debt_analysis
        )

    def _calculate_current_phase(
        self,
        data_import_completed: bool,
        field_mapping_completed: bool,
        data_cleansing_completed: bool,
        asset_inventory_completed: bool,
        dependency_analysis_completed: bool,
        tech_debt_completed: bool,
    ) -> str:
        """Calculate what the current phase should be based on completion flags."""
        phases = [
            ("data_import", data_import_completed),
            ("field_mapping", field_mapping_completed),
            ("data_cleansing", data_cleansing_completed),
            ("asset_inventory", asset_inventory_completed),
            ("dependency_analysis", dependency_analysis_completed),
            ("tech_debt_assessment", tech_debt_completed),
        ]

        # Find the first incomplete phase
        for phase_name, completed in phases:
            if not completed:
                return phase_name

        # All phases complete
        return "tech_debt_assessment"

    async def _apply_changes(
        self, flow: DiscoveryFlow, changes: List[Dict[str, Any]]
    ) -> None:
        """Apply reconciliation changes to a flow."""
        for change in changes:
            field = change["field"]
            new_value = change["new_value"]

            if field == "completed_at" and new_value:
                new_value = datetime.fromisoformat(new_value.replace("Z", "+00:00"))

            setattr(flow, field, new_value)

        # Recalculate progress
        flow.update_progress()

        logger.info(f"Applied {len(changes)} changes to flow {flow.flow_id}")

    def write_csv_report(self, filepath: str) -> None:
        """Write changes report to CSV file."""
        if not self.changes_report:
            logger.info("No changes to report")
            return

        with open(filepath, "w", newline="") as csvfile:
            fieldnames = [
                "flow_id",
                "client_account_id",
                "field",
                "old_value",
                "new_value",
                "reason",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.changes_report)

        logger.info(f"Wrote {len(self.changes_report)} changes to {filepath}")


async def main():
    """Main reconciliation function."""
    parser = argparse.ArgumentParser(description="Reconcile discovery flow data")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without applying them (default)",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes to database"
    )
    parser.add_argument(
        "--client-id", type=str, help="Reconcile flows for specific client only"
    )
    parser.add_argument(
        "--output-csv", type=str, help="Write changes report to CSV file"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Determine mode
    dry_run = not args.apply

    if dry_run:
        logger.info("Running in DRY RUN mode - no changes will be applied")
    else:
        logger.info("Running in APPLY mode - changes will be persisted")

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=args.verbose, future=True)

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        reconciler = DiscoveryFlowReconciler(db, dry_run=dry_run)

        try:
            (
                total_flows,
                flows_with_changes,
                total_changes,
            ) = await reconciler.reconcile_all_flows(client_account_id=args.client_id)

            logger.info("Reconciliation complete:")
            logger.info(f"  Total flows: {total_flows}")
            logger.info(f"  Flows with changes: {flows_with_changes}")
            logger.info(f"  Total changes: {total_changes}")

            if args.output_csv:
                reconciler.write_csv_report(args.output_csv)

            if dry_run and total_changes > 0:
                logger.info("Re-run with --apply to persist these changes")

        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            await db.rollback()
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
