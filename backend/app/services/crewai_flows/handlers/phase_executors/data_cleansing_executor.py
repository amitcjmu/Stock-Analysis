"""
Data Cleansing Executor - Agentic Intelligence Integration
Handles data cleansing phase execution for the Unified Discovery Flow.
Now integrates agentic intelligence for comprehensive asset enrichment.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from .base_phase_executor import BasePhaseExecutor
from .data_cleansing_utils import DataCleansingUtils

logger = logging.getLogger(__name__)


class DataCleansingExecutor(BasePhaseExecutor):
    """
    Executes data cleansing phase for the Unified Discovery Flow.
    Cleans and validates data using CrewAI crew or fallback logic.
    """

    def get_phase_name(self) -> str:
        return "data_cleansing"

    def get_progress_percentage(self) -> float:
        return 33.3  # 2/6 phases

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data cleansing with persistent multi-tenant agents instead of crew-based processing"""
        logger.info("🧠 Starting data cleansing with persistent multi-tenant agent")

        # Get raw records WITH tenant scoping
        raw_import_records = await self._get_raw_import_records_with_ids()
        logger.info(f"📋 Prepared {len(raw_import_records)} assets for cleansing")

        if not raw_import_records:
            raise RuntimeError("No raw import records found for data cleansing")

        # BUILD RequestContext from state (DataCleansingExecutor doesn't have self.context)
        from app.core.context import RequestContext

        request_context = RequestContext(
            client_account_id=self.state.client_account_id,
            engagement_id=self.state.engagement_id,
            user_id=getattr(self.state, "user_id", None),
            flow_id=self.state.flow_id,
        )

        # Get service registry if available
        service_registry = getattr(self, "service_registry", None)

        # Use TenantScopedAgentPool CLASSMETHOD (not instance)
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        cleansing_agent = await TenantScopedAgentPool.get_agent(
            context=request_context,
            agent_type="data_cleansing",
            service_registry=service_registry,  # Pass if available
        )

        logger.info("🔧 Retrieved agent: data_cleansing")

        # Process with persistent agent - handle both sync and async cases
        # The agent may not have a process method, so we need to handle this gracefully
        cleaned_data = []
        try:
            # Check if agent has a process method
            if hasattr(cleansing_agent, "process"):
                # Check if it's async
                import inspect

                if inspect.iscoroutinefunction(cleansing_agent.process):
                    cleaned_data = await cleansing_agent.process(raw_import_records)
                else:
                    # Sync method - need to handle carefully to avoid greenlet issues
                    cleaned_data = cleansing_agent.process(raw_import_records)
            else:
                # Agent doesn't have process method - use basic cleansing logic
                logger.warning(
                    "⚠️ Agent doesn't have process method, using fallback cleansing"
                )
                cleaned_data = self._basic_data_cleansing(raw_import_records)
        except Exception as agent_err:
            logger.error(f"❌ Agent processing failed: {agent_err}")
            # Use basic cleansing as fallback
            cleaned_data = self._basic_data_cleansing(raw_import_records)

        # VALIDATION 1: Check if agent returned any data
        if not cleaned_data:
            logger.error("❌ Data cleansing agent returned no results")
            return {
                "status": "error",
                "error_code": "CLEANSING_FAILED",
                "message": "Data cleansing produced no results - agent returned empty data",
                "raw_records_count": len(raw_import_records),
                "cleaned_records_count": 0,
            }

        logger.info(f"✅ Agent returned {len(cleaned_data)} cleaned records")

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
        updated_count = await self._update_cleansed_data_sync(cleaned_data)

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
        cleansed_count = await self._verify_cleansed_data_in_database()
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

        return {
            "status": "success",
            "cleaned_data": cleaned_data,
            "cleansing_summary": DataCleansingUtils.generate_cleansing_summary(
                cleaned_data
            ),
            "quality_metrics": DataCleansingUtils.calculate_cleansing_quality_metrics(
                cleaned_data
            ),
            "persistent_agent_used": True,
            "crew_based": False,
            "raw_records_count": len(raw_import_records),
            "cleaned_records_count": len(cleaned_data),
            "persisted_count": updated_count,
            "verified_count": cleansed_count,
        }

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

    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, "field_mappings", {}),
            "cleansing_type": "comprehensive_data_cleansing",
        }

    async def _store_results(self, results: Dict[str, Any]):
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

    def _prepare_assets_for_agentic_analysis(
        self, raw_import_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform raw import records into structured assets suitable for agentic intelligence analysis"""

        assets = []

        for i, record in enumerate(raw_import_records):
            try:
                # Create structured asset from raw import record, preserving linkage
                asset = {
                    "id": str(uuid.uuid4()),  # Generate unique ID for asset processing
                    "raw_import_record_id": record.get(
                        "raw_import_record_id"
                    ),  # Preserve linkage
                    "name": record.get("name", record.get("hostname", f"asset_{i+1}")),
                    "asset_type": record.get(
                        "asset_type", record.get("type", "unknown")
                    ),
                    "technology_stack": record.get(
                        "technology_stack",
                        record.get("technology", record.get("software", "")),
                    ),
                    "environment": record.get(
                        "environment", record.get("env", "unknown")
                    ),
                    "business_criticality": record.get(
                        "business_criticality", record.get("criticality", "medium")
                    ),
                    # Performance metrics
                    "cpu_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get("cpu_utilization_percent", record.get("cpu_usage"))
                    ),
                    "memory_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get(
                            "memory_utilization_percent", record.get("memory_usage")
                        )
                    ),
                    "disk_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get("disk_utilization_percent", record.get("disk_usage"))
                    ),
                    # Network and security
                    "network_exposure": record.get(
                        "network_exposure", record.get("exposure", "internal")
                    ),
                    "data_sensitivity": record.get(
                        "data_sensitivity", record.get("sensitivity", "standard")
                    ),
                    # Architecture context
                    "architecture_style": record.get(
                        "architecture_style", record.get("architecture", "unknown")
                    ),
                    "integration_complexity": record.get(
                        "integration_complexity", "medium"
                    ),
                    "data_volume": record.get(
                        "data_volume", record.get("storage_gb", "unknown")
                    ),
                    # Original raw import record for reference and linkage
                    "raw_import_record": record,
                    "enrichment_status": "basic",
                    "source": "discovery_flow",
                }

                assets.append(asset)

            except Exception as e:
                logger.warning(f"Failed to convert raw record {i} to asset: {e}")
                continue

        logger.info(
            f"✅ Prepared {len(assets)} assets for agentic analysis with preserved raw record linkage"
        )
        return assets

    async def _update_cleansed_data_sync(
        self, cleaned_data: List[Dict[str, Any]]
    ) -> int:
        """Update raw records with cleansed data - SYNCHRONOUS, no fire-and-forget
        Returns: Number of records successfully updated
        """
        # Use existing session if available, otherwise create new one
        if hasattr(self, "db_session") and self.db_session:
            db = self.db_session
            should_commit = False  # Don't commit if using provided session
        else:
            from app.core.database import AsyncSessionLocal

            db = AsyncSessionLocal()
            should_commit = True  # Commit if we created the session

        try:
            from app.services.data_import.storage_manager import ImportStorageManager

            storage_manager = ImportStorageManager(
                db, str(self.state.client_account_id)
            )

            data_import_id = uuid.UUID(self.state.data_import_id)

            # Get the master_flow_id from state (it should be the same as flow_id)
            master_flow_id = getattr(self.state, "master_flow_id", self.state.flow_id)

            updated_count = await storage_manager.update_raw_records_with_cleansed_data(
                data_import_id=data_import_id,
                cleansed_data=cleaned_data,
                validation_results=getattr(self.state, "data_validation_results", None),
                master_flow_id=master_flow_id,  # Pass master_flow_id for proper asset association
            )

            if should_commit:
                await db.commit()

            logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
            return updated_count

        finally:
            if should_commit and db:
                await db.close()

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
            await self._persist_phase_completion_to_database(phase_name)

    async def _persist_phase_completion_to_database(self, phase_name: str):
        """Persist phase completion flag to the discovery_flows table"""
        try:
            from sqlalchemy import select
            from app.models.discovery_flow import DiscoveryFlow

            # Use existing session if available, otherwise create new one
            if hasattr(self, "db_session") and self.db_session:
                db = self.db_session
                should_commit = False  # Don't commit if using provided session
            else:
                from app.core.database import AsyncSessionLocal

                db = AsyncSessionLocal()
                should_commit = True  # Commit if we created the session

            try:
                # Find the discovery flow by flow_id (not master_flow_id)
                flow_id = (
                    uuid.UUID(self.state.flow_id)
                    if isinstance(self.state.flow_id, str)
                    else self.state.flow_id
                )

                result = await db.execute(
                    select(DiscoveryFlow).where(
                        DiscoveryFlow.flow_id
                        == flow_id,  # Use flow_id, not master_flow_id
                        (
                            DiscoveryFlow.client_account_id
                            == uuid.UUID(self.state.client_account_id)
                            if isinstance(self.state.client_account_id, str)
                            else self.state.client_account_id
                        ),
                        (
                            DiscoveryFlow.engagement_id
                            == uuid.UUID(self.state.engagement_id)
                            if isinstance(self.state.engagement_id, str)
                            else self.state.engagement_id
                        ),
                    )
                )

                discovery_flow = result.scalar_one_or_none()

                if discovery_flow:
                    if phase_name == "data_cleansing":
                        discovery_flow.data_cleansing_completed = True
                        logger.info(
                            f"✅ Updated discovery_flow.data_cleansing_completed = True for flow {self.state.flow_id}"
                        )

                    if should_commit:
                        await db.commit()
                    else:
                        await db.flush()  # Flush changes if not committing

                    logger.info(
                        f"✅ Successfully persisted {phase_name} completion to database"
                    )
                else:
                    logger.warning(
                        f"⚠️ Could not find discovery flow for master_flow_id {self.state.flow_id}"
                    )

            finally:
                if should_commit and db:
                    await db.close()

        except Exception as e:
            logger.error(
                f"❌ Failed to persist {phase_name} completion to database: {e}"
            )
            # Don't raise the exception - phase completion should not fail the whole process

    async def _verify_cleansed_data_in_database(self) -> int:
        """Verify that cleansed data exists in the database for this import
        Returns: Count of records with cleansed_data
        """
        from sqlalchemy import select, func
        from app.models.data_import.core import RawImportRecord

        # Use existing session if available
        if hasattr(self, "db_session") and self.db_session:
            session = self.db_session
            should_close = False
        else:
            from app.core.database import AsyncSessionLocal

            session = AsyncSessionLocal()
            should_close = True

        try:
            data_import_id = getattr(self.state, "data_import_id", None)
            if not data_import_id:
                logger.error("❌ No data_import_id found in state for verification")
                return 0

            # Count records with cleansed_data (non-null)
            query = select(func.count()).where(
                (
                    RawImportRecord.data_import_id == uuid.UUID(data_import_id)
                    if isinstance(data_import_id, str)
                    else data_import_id
                ),
                (
                    RawImportRecord.client_account_id
                    == uuid.UUID(self.state.client_account_id)
                    if isinstance(self.state.client_account_id, str)
                    else self.state.client_account_id
                ),
                (
                    RawImportRecord.engagement_id == uuid.UUID(self.state.engagement_id)
                    if isinstance(self.state.engagement_id, str)
                    else self.state.engagement_id
                ),
                RawImportRecord.cleansed_data.isnot(
                    None
                ),  # Only count non-null cleansed_data
            )

            result = await session.execute(query)
            count = result.scalar() or 0

            logger.info(
                f"📊 Verification: {count} records have cleansed_data in database"
            )
            return count

        except Exception as e:
            logger.error(f"❌ Failed to verify cleansed data in database: {e}")
            return 0

        finally:
            if should_close and session:
                await session.close()

    def _basic_data_cleansing(
        self, raw_import_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Basic data cleansing fallback when agent is not available or fails"""
        logger.info(
            f"🔧 Performing basic data cleansing on {len(raw_import_records)} records"
        )

        cleaned_data = []
        for record in raw_import_records:
            # Create a cleaned version of the record
            cleaned_record = {}

            # CRITICAL: Preserve ALL ID fields for mapping
            if "raw_import_record_id" in record:
                cleaned_record["raw_import_record_id"] = record["raw_import_record_id"]
                cleaned_record["id"] = record["raw_import_record_id"]

            # CRITICAL: Preserve row_number for fallback updating
            if "row_number" in record:
                cleaned_record["row_number"] = record["row_number"]
                logger.debug(f"Preserved row_number: {record['row_number']} for record")

            # Copy over the raw data fields
            raw_data = record.get("raw_data", {})
            if isinstance(raw_data, dict):
                cleaned_record.update(raw_data)

            # Basic cleansing operations
            for key, value in record.items():
                if key not in ["raw_import_record_id", "id", "raw_data", "row_number"]:
                    # Clean string values
                    if isinstance(value, str):
                        value = value.strip()
                        # Convert empty strings to None
                        if value == "":
                            value = None
                    cleaned_record[key] = value

            # Add cleansing metadata
            cleaned_record["cleansing_method"] = "basic_fallback"
            cleaned_record["cleansed_at"] = datetime.utcnow().isoformat()

            cleaned_data.append(cleaned_record)

        logger.info(f"✅ Basic cleansing completed for {len(cleaned_data)} records")
        return cleaned_data

    async def _get_raw_import_records_with_ids(self) -> List[Dict[str, Any]]:
        """Get raw import records with IDs and tenant scoping"""
        from sqlalchemy import select
        from app.models.data_import.core import RawImportRecord  # CORRECT IMPORT

        # Use existing session if available
        if hasattr(self, "db_session") and self.db_session:
            session = self.db_session
        else:
            from app.core.database import AsyncSessionLocal

            session = AsyncSessionLocal()

        try:
            data_import_id = getattr(self.state, "data_import_id", None)
            if not data_import_id:
                logger.error("❌ No data_import_id found in state")
                return []

            # WITH TENANT SCOPING - Ensure proper UUID conversion
            query = select(RawImportRecord).where(
                (
                    RawImportRecord.data_import_id == uuid.UUID(data_import_id)
                    if isinstance(data_import_id, str)
                    else data_import_id
                ),
                (
                    RawImportRecord.client_account_id
                    == uuid.UUID(self.state.client_account_id)
                    if isinstance(self.state.client_account_id, str)
                    else self.state.client_account_id
                ),
                (
                    RawImportRecord.engagement_id == uuid.UUID(self.state.engagement_id)
                    if isinstance(self.state.engagement_id, str)
                    else self.state.engagement_id
                ),
            )

            result = await session.execute(query)
            raw_records = result.scalars().all()

            logger.info(f"📊 Found {len(raw_records)} raw import records")

            # Convert to dict format with ID preservation
            records = []
            for record in raw_records:
                record_data = {
                    "raw_import_record_id": str(record.id),  # Preserve for ID mapping
                    "row_number": record.row_number,
                    "raw_data": record.raw_data,
                    "cleansed_data": record.cleansed_data,
                    **record.raw_data,  # Flatten for easy access
                }
                records.append(record_data)

            return records

        finally:
            if not hasattr(self, "db_session"):
                await session.close()
