#!/usr/bin/env python3
"""
Phase 3 Migration Summary Report
================================

Generates a comprehensive summary of Phase 3 data integrity fix results.
This script consolidates all migration activities and provides final metrics.

Usage:
    python scripts/phase3_migration_summary_report.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


class Phase3SummaryReporter:
    """Generates comprehensive Phase 3 migration summary."""

    def __init__(self):
        self.summary = {
            "report_timestamp": datetime.now().isoformat(),
            "phase": "Phase 3 - Data Integrity Fixes",
            "objectives": [
                "Fix orphaned DataImport records (master_flow_id = NULL)",
                "Fix orphaned RawImportRecord records (master_flow_id = NULL)",
                "Fix orphaned DiscoveryFlow records (master_flow_id = NULL)",
                "Validate all foreign key relationships",
                "Improve overall system health score",
            ],
            "before_state": {},
            "after_state": {},
            "achievements": {},
            "remaining_issues": [],
            "next_steps": [],
        }

    async def get_current_metrics(self, session):
        """Get current state metrics."""
        metrics = {}

        # Data imports
        data_imports_total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.data_imports")
        )
        data_imports_total = data_imports_total_result.scalar()

        data_imports_with_master_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.data_imports WHERE master_flow_id IS NOT NULL"
            )
        )
        data_imports_with_master = data_imports_with_master_result.scalar()

        metrics["data_imports"] = {
            "total": data_imports_total,
            "with_master_flow_id": data_imports_with_master,
            "orphaned": data_imports_total - data_imports_with_master,
            "health_percentage": (
                (data_imports_with_master / data_imports_total * 100)
                if data_imports_total > 0
                else 0
            ),
        }

        # Raw import records
        raw_records_total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.raw_import_records")
        )
        raw_records_total = raw_records_total_result.scalar()

        raw_records_with_master_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.raw_import_records WHERE master_flow_id IS NOT NULL"
            )
        )
        raw_records_with_master = raw_records_with_master_result.scalar()

        metrics["raw_import_records"] = {
            "total": raw_records_total,
            "with_master_flow_id": raw_records_with_master,
            "orphaned": raw_records_total - raw_records_with_master,
            "health_percentage": (
                (raw_records_with_master / raw_records_total * 100)
                if raw_records_total > 0
                else 0
            ),
        }

        # Discovery flows
        discovery_flows_total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.discovery_flows")
        )
        discovery_flows_total = discovery_flows_total_result.scalar()

        discovery_flows_with_master_result = await session.execute(
            text(
                "SELECT COUNT(*) FROM migration.discovery_flows WHERE master_flow_id IS NOT NULL"
            )
        )
        discovery_flows_with_master = discovery_flows_with_master_result.scalar()

        metrics["discovery_flows"] = {
            "total": discovery_flows_total,
            "with_master_flow_id": discovery_flows_with_master,
            "orphaned": discovery_flows_total - discovery_flows_with_master,
            "health_percentage": (
                (discovery_flows_with_master / discovery_flows_total * 100)
                if discovery_flows_total > 0
                else 0
            ),
        }

        # Master flows
        master_flows_total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.crewai_flow_state_extensions")
        )
        master_flows_total = master_flows_total_result.scalar()

        master_flows_with_children_result = await session.execute(
            text(
                """
            SELECT COUNT(DISTINCT cfse.id) FROM migration.crewai_flow_state_extensions cfse
            WHERE EXISTS (
                SELECT 1 FROM migration.data_imports di WHERE di.master_flow_id = cfse.id
            ) OR EXISTS (
                SELECT 1 FROM migration.discovery_flows df WHERE df.master_flow_id = cfse.id
            )
        """
            )
        )
        master_flows_with_children = master_flows_with_children_result.scalar()

        metrics["master_flows"] = {
            "total": master_flows_total,
            "with_children": master_flows_with_children,
            "orphaned": master_flows_total - master_flows_with_children,
            "utilization_percentage": (
                (master_flows_with_children / master_flows_total * 100)
                if master_flows_total > 0
                else 0
            ),
        }

        return metrics

    async def generate_summary(self):
        """Generate comprehensive summary report."""
        async with AsyncSessionLocal() as session:
            current_metrics = await self.get_current_metrics(session)

            # Set after state (current)
            self.summary["after_state"] = current_metrics

            # Set before state (documented issues from initial validation)
            self.summary["before_state"] = {
                "data_imports": {
                    "total": 16,
                    "with_master_flow_id": 0,
                    "orphaned": 16,
                    "health_percentage": 0,
                },
                "raw_import_records": {
                    "total": 265,
                    "with_master_flow_id": 0,
                    "orphaned": 265,
                    "health_percentage": 0,
                },
                "discovery_flows": {
                    "total": 20,
                    "with_master_flow_id": 7,
                    "orphaned": 13,
                    "health_percentage": 35,
                },
                "master_flows": {
                    "total": 32,
                    "with_children": 0,
                    "orphaned": 32,
                    "utilization_percentage": 0,
                },
            }

            # Calculate achievements
            self.summary["achievements"] = {
                "data_imports_fixed": self.summary["before_state"]["data_imports"][
                    "orphaned"
                ]
                - self.summary["after_state"]["data_imports"]["orphaned"],
                "raw_records_fixed": self.summary["before_state"]["raw_import_records"][
                    "orphaned"
                ]
                - self.summary["after_state"]["raw_import_records"]["orphaned"],
                "discovery_flows_fixed": self.summary["before_state"][
                    "discovery_flows"
                ]["orphaned"]
                - self.summary["after_state"]["discovery_flows"]["orphaned"],
                "health_improvement": {
                    "data_imports": self.summary["after_state"]["data_imports"][
                        "health_percentage"
                    ]
                    - self.summary["before_state"]["data_imports"]["health_percentage"],
                    "raw_records": self.summary["after_state"]["raw_import_records"][
                        "health_percentage"
                    ]
                    - self.summary["before_state"]["raw_import_records"][
                        "health_percentage"
                    ],
                    "discovery_flows": self.summary["after_state"]["discovery_flows"][
                        "health_percentage"
                    ]
                    - self.summary["before_state"]["discovery_flows"][
                        "health_percentage"
                    ],
                },
                "total_records_fixed": (
                    (
                        self.summary["before_state"]["data_imports"]["orphaned"]
                        - self.summary["after_state"]["data_imports"]["orphaned"]
                    )
                    + (
                        self.summary["before_state"]["raw_import_records"]["orphaned"]
                        - self.summary["after_state"]["raw_import_records"]["orphaned"]
                    )
                    + (
                        self.summary["before_state"]["discovery_flows"]["orphaned"]
                        - self.summary["after_state"]["discovery_flows"]["orphaned"]
                    )
                ),
            }

            # Identify remaining issues
            if self.summary["after_state"]["data_imports"]["orphaned"] > 0:
                self.summary["remaining_issues"].append(
                    f"{self.summary['after_state']['data_imports']['orphaned']} orphaned data imports"
                )

            if self.summary["after_state"]["raw_import_records"]["orphaned"] > 0:
                self.summary["remaining_issues"].append(
                    f"{self.summary['after_state']['raw_import_records']['orphaned']} orphaned raw import records"
                )

            if self.summary["after_state"]["discovery_flows"]["orphaned"] > 0:
                self.summary["remaining_issues"].append(
                    f"{self.summary['after_state']['discovery_flows']['orphaned']} orphaned discovery flows"
                )

            if self.summary["after_state"]["master_flows"]["orphaned"] > 0:
                self.summary["remaining_issues"].append(
                    f"{self.summary['after_state']['master_flows']['orphaned']} unused master flows"
                )

            # Define next steps
            if self.summary["remaining_issues"]:
                self.summary["next_steps"] = [
                    "Investigate remaining orphaned records",
                    "Consider creating master flows for orphaned discovery flows",
                    "Review master flows without children for potential cleanup",
                    "Implement monitoring to prevent future orphaned records",
                ]
            else:
                self.summary["next_steps"] = [
                    "Phase 3 complete - proceed to Phase 4",
                    "Implement monitoring to prevent future orphaned records",
                    "Regular health checks using validation scripts",
                ]

            # Calculate overall success rate
            total_before = (
                self.summary["before_state"]["data_imports"]["orphaned"]
                + self.summary["before_state"]["raw_import_records"]["orphaned"]
                + self.summary["before_state"]["discovery_flows"]["orphaned"]
            )

            total_after = (
                self.summary["after_state"]["data_imports"]["orphaned"]
                + self.summary["after_state"]["raw_import_records"]["orphaned"]
                + self.summary["after_state"]["discovery_flows"]["orphaned"]
            )

            self.summary["overall_success_rate"] = (
                ((total_before - total_after) / total_before * 100)
                if total_before > 0
                else 100
            )

    def print_summary(self):
        """Print formatted summary report."""
        print("\n" + "=" * 80)
        print("PHASE 3 DATA INTEGRITY MIGRATION - FINAL SUMMARY REPORT")
        print("=" * 80)
        print(f"Report Generated: {self.summary['report_timestamp']}")
        print()

        print("OBJECTIVES COMPLETED:")
        for obj in self.summary["objectives"]:
            print(f"  • {obj}")
        print()

        print("MIGRATION RESULTS:")
        print("-" * 80)

        # Data Imports
        before_di = self.summary["before_state"]["data_imports"]
        after_di = self.summary["after_state"]["data_imports"]
        print("DATA IMPORTS:")
        print(
            f"  Before: {before_di['orphaned']}/{before_di['total']} orphaned ({before_di['health_percentage']:.1f}% healthy)"
        )
        print(
            f"  After:  {after_di['orphaned']}/{after_di['total']} orphaned ({after_di['health_percentage']:.1f}% healthy)"
        )
        print(f"  Fixed:  {self.summary['achievements']['data_imports_fixed']} records")
        print(
            f"  Improvement: +{self.summary['achievements']['health_improvement']['data_imports']:.1f}%"
        )
        print()

        # Raw Import Records
        before_rir = self.summary["before_state"]["raw_import_records"]
        after_rir = self.summary["after_state"]["raw_import_records"]
        print("RAW IMPORT RECORDS:")
        print(
            f"  Before: {before_rir['orphaned']}/{before_rir['total']} orphaned ({before_rir['health_percentage']:.1f}% healthy)"
        )
        print(
            f"  After:  {after_rir['orphaned']}/{after_rir['total']} orphaned ({after_rir['health_percentage']:.1f}% healthy)"
        )
        print(f"  Fixed:  {self.summary['achievements']['raw_records_fixed']} records")
        print(
            f"  Improvement: +{self.summary['achievements']['health_improvement']['raw_records']:.1f}%"
        )
        print()

        # Discovery Flows
        before_df = self.summary["before_state"]["discovery_flows"]
        after_df = self.summary["after_state"]["discovery_flows"]
        print("DISCOVERY FLOWS:")
        print(
            f"  Before: {before_df['orphaned']}/{before_df['total']} orphaned ({before_df['health_percentage']:.1f}% healthy)"
        )
        print(
            f"  After:  {after_df['orphaned']}/{after_df['total']} orphaned ({after_df['health_percentage']:.1f}% healthy)"
        )
        print(
            f"  Fixed:  {self.summary['achievements']['discovery_flows_fixed']} records"
        )
        print(
            f"  Improvement: +{self.summary['achievements']['health_improvement']['discovery_flows']:.1f}%"
        )
        print()

        # Overall Results
        print("OVERALL RESULTS:")
        print("-" * 80)
        print(
            f"Total Records Fixed: {self.summary['achievements']['total_records_fixed']}"
        )
        print(f"Overall Success Rate: {self.summary['overall_success_rate']:.1f}%")
        print()

        # Remaining Issues
        if self.summary["remaining_issues"]:
            print("REMAINING ISSUES:")
            for issue in self.summary["remaining_issues"]:
                print(f"  ⚠️  {issue}")
        else:
            print("✅ NO REMAINING ISSUES - PHASE 3 COMPLETE")
        print()

        # Next Steps
        print("NEXT STEPS:")
        for step in self.summary["next_steps"]:
            print(f"  • {step}")
        print()

        # Files Created
        print("SCRIPTS CREATED:")
        print(
            "  • fix_orphaned_data_imports.py - Links orphaned data imports to master flows"
        )
        print(
            "  • validate_flow_relationships.py - Comprehensive relationship validation"
        )
        print("  • data_integrity_cleanup_utilities.py - General cleanup utilities")
        print("  • fix_orphaned_discovery_flows.py - Links orphaned discovery flows")
        print("  • phase3_migration_summary_report.py - This summary report")
        print()

        print("=" * 80)

        # Export JSON summary
        json_file = (
            Path(__file__).parent
            / f"phase3_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_file, "w") as f:
            json.dump(self.summary, f, indent=2)
        print(f"Detailed JSON report saved to: {json_file}")
        print("=" * 80)


async def main():
    """Main entry point."""
    reporter = Phase3SummaryReporter()
    await reporter.generate_summary()
    reporter.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
