"""
Data Cleansing Executor - Main Implementation

Main executor class that orchestrates data cleansing operations using
modular components for better code organization and maintainability.
"""

import logging
from typing import Any, Dict

from ..base_phase_executor import BasePhaseExecutor
from .agent_processor import AgentProcessor
from .base import DataCleansingBase
from .database_operations import DatabaseOperations

logger = logging.getLogger(__name__)


class DataCleansingExecutor(BasePhaseExecutor, DataCleansingBase):
    """
    Executes data cleansing phase for the Unified Discovery Flow.
    Cleans and validates data using CrewAI crew or fallback logic.
    """

    def get_phase_name(self) -> str:
        return "data_cleansing"

    def get_progress_percentage(self) -> float:
        return 33.3  # 2/6 phases

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data cleansing with persistent multi-tenant agents"""
        logger.info("🧠 Starting data cleansing with persistent multi-tenant agent")

        # Initialize database operations
        db_ops = DatabaseOperations(self.state, getattr(self, "db_session", None))

        # Get raw records WITH tenant scoping
        raw_import_records = await db_ops.get_raw_import_records_with_ids()
        logger.info(f"📋 Prepared {len(raw_import_records)} assets for cleansing")

        if not raw_import_records:
            raise RuntimeError("No raw import records found for data cleansing")

        # Initialize agent processor
        service_registry = getattr(self, "service_registry", None)
        agent_processor = AgentProcessor(self.state, service_registry)

        # Process with persistent agent
        agent_result = await agent_processor.process_with_agent(raw_import_records)

        # Handle agent processing result
        if agent_result.get("status") == "success":
            cleaned_data = agent_result["cleaned_data"]
        else:
            # Agent failed - use basic cleansing as fallback
            logger.warning(
                f"⚠️ Agent processing failed: {agent_result.get('error', 'Unknown error')}"
            )
            cleaned_data = self._basic_data_cleansing(raw_import_records)

        # VALIDATION 1: Check if we have any cleaned data
        if not cleaned_data:
            logger.error("❌ Data cleansing produced no results")
            return {
                "status": "error",
                "error_code": "CLEANSING_FAILED",
                "message": "Data cleansing produced no results - no cleaned data available",
                "raw_records_count": len(raw_import_records),
                "cleaned_records_count": 0,
            }

        logger.info(f"✅ Generated {len(cleaned_data)} cleaned records")

        # Log sample of cleaned data to debug ID mapping
        if cleaned_data:
            sample_record = cleaned_data[0]
            logger.info(f"📋 Sample cleaned record keys: {list(sample_record.keys())}")
            has_id = sum(1 for r in cleaned_data if "id" in r)
            has_raw_id = sum(1 for r in cleaned_data if "raw_import_record_id" in r)
            has_row_num = sum(1 for r in cleaned_data if "row_number" in r)
            logger.info(
                f"📊 ID mapping stats - id: {has_id}, raw_import_record_id: {has_raw_id}, row_number: {has_row_num}"
            )

        # CRITICAL: Fix ID mapping before storage
        for record in cleaned_data:
            if "raw_import_record_id" in record and "id" not in record:
                record["id"] = record["raw_import_record_id"]
                logger.debug("Mapped raw_import_record_id to id for record")

        # CRITICAL: Await the update (no fire-and-forget)
        updated_count = await db_ops.update_cleansed_data_sync(cleaned_data)

        # VALIDATION 2: Check if data was actually persisted
        if updated_count == 0:
            logger.error(
                f"❌ Failed to persist cleansed data (0/{len(cleaned_data)} records updated)"
            )
            return {
                "status": "error",
                "error_code": "CLEANSING_FAILED",
                "message": f"Failed to persist cleansed data to database (0/{len(cleaned_data)} records updated)",
                "raw_records_count": len(raw_import_records),
                "cleaned_records_count": len(cleaned_data),
                "persisted_count": 0,
            }

        logger.info(
            f"✅ Successfully persisted {updated_count}/{len(cleaned_data)} cleansed records"
        )

        # VALIDATION 3: Verify cleansed data exists in database before marking complete
        cleansed_count = await db_ops.verify_cleansed_data_in_database()
        if cleansed_count == 0:
            logger.error(
                "❌ Post-persistence verification failed - no cleansed data found in database"
            )
            return {
                "status": "error",
                "error_code": "CLEANSING_FAILED",
                "message": "Data cleansing verification failed - no cleansed data found in database after update",
                "raw_records_count": len(raw_import_records),
                "cleaned_records_count": len(cleaned_data),
                "updated_count": updated_count,
                "verified_count": 0,
            }

        # Only mark phase complete if we successfully cleansed and persisted data
        await self._mark_phase_complete("data_cleansing")

        return self._generate_cleansing_results(
            cleaned_data, len(raw_import_records), updated_count, cleansed_count
        )

    async def execute_fallback(self) -> Dict[str, Any]:
        """NO FALLBACK ALLOWED - Data cleansing is required per ADR-025"""
        logger.error(
            "❌ execute_fallback called for data_cleansing - FALLBACK DISABLED"
        )
        logger.error(
            "❌ Data cleansing is mandatory - cannot use raw data for asset creation"
        )
        raise RuntimeError(
            "Data cleansing fallback disabled - cleansed data is required for asset creation (ADR-025)"
        )

    async def _store_results(self, results: Dict[str, Any]):
        """Store results from crew execution"""
        # NO FALLBACK LOGIC - Crew results must be valid
        cleaned_data = results.get("cleaned_data", [])

        if not cleaned_data:
            logger.error(
                "❌ No cleaned_data in results - this indicates crew execution failure"
            )
            logger.error(f"❌ Results received: {list(results.keys())}")
            raise RuntimeError(
                "Data cleansing crew did not return cleaned_data - crew execution failed"
            )

        logger.info(
            f"🔍 Storing data cleansing results: {len(cleaned_data)} cleaned records"
        )

        self.state.cleaned_data = cleaned_data
        self.state.data_quality_metrics = results.get("quality_metrics", {})

        logger.info(
            f"✅ Data cleansing state updated: cleaned_data has {len(self.state.cleaned_data)} records"
        )

        # Update raw_import_records with cleansed data
        # Now handled synchronously in execute_with_crew via _update_cleansed_data_sync

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for CrewAI crew execution"""
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, "field_mappings", {}),
            "cleansing_type": "comprehensive_data_cleansing",
        }

    async def _mark_phase_complete(self, phase_name: str):
        """Mark phase as complete for progression tracking and persist to database"""
        logger.info(f"✅ Phase {phase_name} completed for flow {self.state.flow_id}")

        # Update state to indicate phase completion
        if phase_name == "data_cleansing":
            # Use the phase_completion dict instead of non-existent field
            if hasattr(self.state, "phase_completion"):
                self.state.phase_completion["data_cleansing"] = True
                logger.info("✅ Set phase_completion['data_cleansing'] = True in state")
            else:
                logger.warning("⚠️ State does not have phase_completion dict")

            # Persist data_cleansing_completed flag to database
            db_ops = DatabaseOperations(self.state, getattr(self, "db_session", None))
            await db_ops.persist_phase_completion_to_database(phase_name)
