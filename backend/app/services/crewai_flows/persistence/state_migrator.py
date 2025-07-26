"""
Utilities to migrate existing SQLite states to PostgreSQL
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

from .postgres_store import PostgresFlowStateStore

logger = logging.getLogger(__name__)


class StateMigrator:
    """One-time migration from SQLite to PostgreSQL"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()

    async def migrate_active_flows(self) -> Dict[str, Any]:
        """
        Migrate all active flow states from SQLite to PostgreSQL
        Returns migration report
        """
        try:
            logger.info(
                "🔄 Starting migration of active flows from SQLite to PostgreSQL"
            )

            migration_report = {
                "started_at": datetime.utcnow().isoformat(),
                "flows_found": 0,
                "flows_migrated": 0,
                "flows_skipped": 0,
                "flows_failed": 0,
                "validation_errors": 0,
                "migration_details": [],
                "sqlite_sources": [],
            }

            # Find potential SQLite sources
            sqlite_sources = await self._find_sqlite_sources()
            migration_report["sqlite_sources"] = sqlite_sources

            if not sqlite_sources:
                logger.info("ℹ️ No SQLite sources found for migration")
                return migration_report

            # Migrate from each SQLite source
            for sqlite_path in sqlite_sources:
                source_report = await self._migrate_from_sqlite_file(sqlite_path)
                migration_report["flows_found"] += source_report["flows_found"]
                migration_report["flows_migrated"] += source_report["flows_migrated"]
                migration_report["flows_skipped"] += source_report["flows_skipped"]
                migration_report["flows_failed"] += source_report["flows_failed"]
                migration_report["validation_errors"] += source_report[
                    "validation_errors"
                ]
                migration_report["migration_details"].extend(source_report["details"])

            # Verify migration results
            await self._verify_migration_integrity(migration_report)

            # Mark migration as complete
            migration_report["completed_at"] = datetime.utcnow().isoformat()
            migration_report["status"] = "completed"

            logger.info(
                f"✅ Migration completed: {migration_report['flows_migrated']} flows migrated"
            )
            return migration_report

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            migration_report["status"] = "failed"
            migration_report["error"] = str(e)
            migration_report["completed_at"] = datetime.utcnow().isoformat()
            return migration_report

    async def _find_sqlite_sources(self) -> List[str]:
        """Find potential SQLite database files"""
        sqlite_paths = []

        # Common CrewAI SQLite locations
        potential_locations = [
            # CrewAI default locations
            os.path.expanduser("~/.crewai"),
            os.path.expanduser("~/.crewai/flows"),
            "/tmp/crewai",
            "/var/tmp/crewai",
            # Application-specific locations
            "./crewai_flows",
            "./data/crewai",
            "../data/crewai",
            # Docker volume locations
            "/app/data/crewai",
            "/data/crewai",
        ]

        for location in potential_locations:
            try:
                path = Path(location)
                if path.exists() and path.is_dir():
                    # Find SQLite files
                    for sqlite_file in path.glob("**/*.db"):
                        if sqlite_file.is_file():
                            sqlite_paths.append(str(sqlite_file))
                    for sqlite_file in path.glob("**/*.sqlite"):
                        if sqlite_file.is_file():
                            sqlite_paths.append(str(sqlite_file))
                    for sqlite_file in path.glob("**/*.sqlite3"):
                        if sqlite_file.is_file():
                            sqlite_paths.append(str(sqlite_file))
            except (OSError, PermissionError) as e:
                logger.debug(f"Cannot access {location}: {e}")
                continue

        # Remove duplicates
        sqlite_paths = list(set(sqlite_paths))

        # Validate that these are actually SQLite files
        valid_paths = []
        for path in sqlite_paths:
            if await self._is_valid_sqlite_file(path):
                valid_paths.append(path)

        logger.info(f"Found {len(valid_paths)} valid SQLite files for migration")
        return valid_paths

    async def _is_valid_sqlite_file(self, file_path: str) -> bool:
        """Check if file is a valid SQLite database"""
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            # Try to get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            # Check if it looks like CrewAI flow data
            table_names = [table[0] for table in tables]
            crewai_indicators = ["flows", "flow_state", "tasks", "agents", "crews"]

            return any(
                indicator in " ".join(table_names).lower()
                for indicator in crewai_indicators
            )

        except Exception:
            return False

    async def _migrate_from_sqlite_file(self, sqlite_path: str) -> Dict[str, Any]:
        """Migrate flows from a specific SQLite file"""
        report = {
            "sqlite_path": sqlite_path,
            "flows_found": 0,
            "flows_migrated": 0,
            "flows_skipped": 0,
            "flows_failed": 0,
            "validation_errors": 0,
            "details": [],
        }

        try:
            logger.info(f"🔄 Migrating from SQLite file: {sqlite_path}")

            # Connect to SQLite
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            cursor = conn.cursor()

            # Get table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            # Try different table naming patterns CrewAI might use
            flow_tables = [table for table in tables if "flow" in table.lower()]

            for table_name in flow_tables:
                try:
                    # Get all records from the flow table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    for row in rows:
                        report["flows_found"] += 1

                        # Convert row to dict
                        row_dict = dict(row)

                        # Try to extract flow state
                        flow_state = await self._extract_flow_state_from_row(row_dict)

                        if flow_state:
                            # Validate extracted state
                            validation_result = self.validator.validate_complete_state(
                                flow_state
                            )

                            if validation_result["valid"]:
                                # Migrate to PostgreSQL
                                try:
                                    await self._migrate_single_flow(flow_state)
                                    report["flows_migrated"] += 1
                                    report["details"].append(
                                        {
                                            "flow_id": flow_state.get("flow_id"),
                                            "status": "migrated",
                                            "source_table": table_name,
                                        }
                                    )
                                except Exception as e:
                                    report["flows_failed"] += 1
                                    report["details"].append(
                                        {
                                            "flow_id": flow_state.get("flow_id"),
                                            "status": "failed",
                                            "error": str(e),
                                            "source_table": table_name,
                                        }
                                    )
                            else:
                                report["validation_errors"] += 1
                                report["flows_skipped"] += 1
                                report["details"].append(
                                    {
                                        "flow_id": flow_state.get("flow_id"),
                                        "status": "validation_failed",
                                        "errors": validation_result["errors"],
                                        "source_table": table_name,
                                    }
                                )
                        else:
                            report["flows_skipped"] += 1
                            report["details"].append(
                                {
                                    "flow_id": "unknown",
                                    "status": "extraction_failed",
                                    "source_table": table_name,
                                }
                            )

                except Exception as e:
                    logger.error(f"❌ Failed to process table {table_name}: {e}")
                    continue

            conn.close()

        except Exception as e:
            logger.error(f"❌ Failed to migrate from {sqlite_path}: {e}")
            report["error"] = str(e)

        return report

    async def _extract_flow_state_from_row(
        self, row_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract and normalize flow state from SQLite row"""
        try:
            # Common field mappings from SQLite to our state model
            field_mappings = {
                # ID fields
                "id": "flow_id",
                "flow_id": "flow_id",
                "execution_id": "flow_id",
                "session_id": "session_id",
                "workflow_id": "flow_id",
                # Status fields
                "status": "status",
                "state": "status",
                "current_phase": "current_phase",
                "phase": "current_phase",
                "progress": "progress_percentage",
                "progress_percentage": "progress_percentage",
                # Data fields
                "data": "raw_data",
                "input_data": "raw_data",
                "flow_data": "raw_data",
                "state_data": "flow_state_data",
                "metadata": "metadata",
                # Timestamps
                "created_at": "created_at",
                "updated_at": "updated_at",
                "started_at": "started_at",
                "completed_at": "completed_at",
            }

            # Extract basic flow state
            flow_state = {}

            for sqlite_field, state_field in field_mappings.items():
                if sqlite_field in row_dict and row_dict[sqlite_field] is not None:
                    value = row_dict[sqlite_field]

                    # Handle JSON fields
                    if sqlite_field in [
                        "data",
                        "state_data",
                        "metadata",
                    ] and isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            continue

                    flow_state[state_field] = value

            # Ensure required fields
            if not flow_state.get("flow_id"):
                # Generate flow_id from available data
                if "session_id" in flow_state:
                    flow_state["flow_id"] = flow_state["session_id"]
                else:
                    return None

            # Set defaults for missing required fields
            flow_state.setdefault("current_phase", "initialization")
            flow_state.setdefault("status", "running")
            flow_state.setdefault("progress_percentage", 0.0)
            flow_state.setdefault("client_account_id", self.context.client_account_id)
            flow_state.setdefault("engagement_id", self.context.engagement_id)
            flow_state.setdefault("user_id", self.context.user_id)

            # Initialize missing collections
            flow_state.setdefault("phase_completion", {})
            flow_state.setdefault("crew_status", {})
            flow_state.setdefault("errors", [])
            flow_state.setdefault("warnings", [])
            flow_state.setdefault("agent_insights", [])
            flow_state.setdefault("user_clarifications", [])
            flow_state.setdefault("workflow_log", [])
            flow_state.setdefault("agent_confidences", {})

            # Add migration metadata
            flow_state["migration_info"] = {
                "migrated_at": datetime.utcnow().isoformat(),
                "source": "sqlite_migration",
                "original_data": row_dict,
            }

            return flow_state

        except Exception as e:
            logger.error(f"❌ Failed to extract flow state from row: {e}")
            return None

    async def _migrate_single_flow(self, flow_state: Dict[str, Any]) -> None:
        """Migrate a single flow to PostgreSQL"""
        try:
            flow_id = flow_state["flow_id"]

            # Check if flow already exists in PostgreSQL
            existing_state = await self.store.load_state(flow_id)

            if existing_state:
                logger.info(f"⏩ Flow {flow_id} already exists in PostgreSQL, skipping")
                return

            # Save to PostgreSQL
            await self.store.save_state(
                flow_id=flow_id,
                state=flow_state,
                phase=flow_state.get("current_phase", "initialization"),
            )

            logger.info(f"✅ Migrated flow {flow_id} to PostgreSQL")

        except Exception as e:
            logger.error(f"❌ Failed to migrate flow {flow_state.get('flow_id')}: {e}")
            raise

    async def _verify_migration_integrity(
        self, migration_report: Dict[str, Any]
    ) -> None:
        """Verify the integrity of migrated data"""
        try:
            logger.info("🔍 Verifying migration integrity...")

            verification_results = {
                "flows_verified": 0,
                "flows_corrupted": 0,
                "verification_errors": [],
            }

            # Get all migrated flows for this tenant
            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.client_account_id
                == self.context.client_account_id
            )
            result = await self.db.execute(stmt)
            records = result.scalars().all()

            for record in records:
                try:
                    if record.flow_state_data:
                        validation_result = self.validator.validate_complete_state(
                            record.flow_state_data
                        )

                        if validation_result["valid"]:
                            verification_results["flows_verified"] += 1
                        else:
                            verification_results["flows_corrupted"] += 1
                            verification_results["verification_errors"].append(
                                {
                                    "flow_id": record.flow_id,
                                    "errors": validation_result["errors"],
                                }
                            )
                except Exception as e:
                    verification_results["verification_errors"].append(
                        {"flow_id": record.flow_id, "error": str(e)}
                    )

            migration_report["verification"] = verification_results

            if verification_results["flows_corrupted"] > 0:
                logger.warning(
                    f"⚠️ {verification_results['flows_corrupted']} corrupted flows found after migration"
                )
            else:
                logger.info(
                    f"✅ All {verification_results['flows_verified']} migrated flows verified successfully"
                )

        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            migration_report["verification_error"] = str(e)

    async def cleanup_sqlite_references(self) -> Dict[str, Any]:
        """Clean up any remaining SQLite references in the codebase"""
        cleanup_report = {
            "started_at": datetime.utcnow().isoformat(),
            "actions_taken": [],
            "warnings": [],
        }

        try:
            logger.info("🧹 Cleaning up SQLite references...")

            # This would typically involve:
            # 1. Removing SQLite connection configurations
            # 2. Updating environment variables
            # 3. Removing SQLite-specific code paths
            # 4. Updating documentation

            # For now, we'll just log what should be done
            cleanup_actions = [
                "Remove SQLite connection strings from configuration",
                "Update CrewAI configuration to use PostgreSQL-only persistence",
                "Remove SQLite database files from deployment",
                "Update documentation to reflect PostgreSQL-only architecture",
            ]

            for action in cleanup_actions:
                cleanup_report["actions_taken"].append(
                    {
                        "action": action,
                        "status": "documented",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            cleanup_report["completed_at"] = datetime.utcnow().isoformat()
            cleanup_report["status"] = "completed"

            logger.info("✅ SQLite cleanup documented")
            return cleanup_report

        except Exception as e:
            logger.error(f"❌ SQLite cleanup failed: {e}")
            cleanup_report["status"] = "failed"
            cleanup_report["error"] = str(e)
            return cleanup_report


# Utility functions for migration management


async def run_migration(context: RequestContext) -> Dict[str, Any]:
    """Run a complete migration from SQLite to PostgreSQL"""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        migrator = StateMigrator(db, context)
        return await migrator.migrate_active_flows()


async def verify_migration_status(context: RequestContext) -> Dict[str, Any]:
    """Check the status of migration for a tenant"""
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            # Count flows in PostgreSQL for this tenant
            stmt = select(func.count(CrewAIFlowStateExtensions.id)).where(
                CrewAIFlowStateExtensions.client_account_id == context.client_account_id
            )
            result = await db.execute(stmt)
            flow_count = result.scalar()

            # Get sample of flows for validation
            sample_stmt = (
                select(CrewAIFlowStateExtensions)
                .where(
                    CrewAIFlowStateExtensions.client_account_id
                    == context.client_account_id
                )
                .limit(10)
            )
            sample_result = await db.execute(sample_stmt)
            sample_flows = sample_result.scalars().all()

            validator = FlowStateValidator()
            valid_flows = 0
            invalid_flows = 0

            for flow in sample_flows:
                if flow.flow_state_data:
                    validation = validator.validate_complete_state(flow.flow_state_data)
                    if validation["valid"]:
                        valid_flows += 1
                    else:
                        invalid_flows += 1

            return {
                "status": "completed" if flow_count > 0 else "not_started",
                "total_flows": flow_count,
                "sample_validation": {
                    "valid_flows": valid_flows,
                    "invalid_flows": invalid_flows,
                    "sample_size": len(sample_flows),
                },
                "checked_at": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat(),
        }
