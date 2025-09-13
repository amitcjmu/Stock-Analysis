"""
Data Cleansing Executor - Agentic Intelligence Integration
Handles data cleansing phase execution for the Unified Discovery Flow.
Now integrates agentic intelligence for comprehensive asset enrichment.
"""

import logging
import uuid
from typing import Any, Dict, List

from .base_phase_executor import BasePhaseExecutor

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

        # Process with persistent agent (structured results, no JSON parsing)
        cleaned_data = await cleansing_agent.process(raw_import_records)

        # CRITICAL: Fix ID mapping before storage
        for record in cleaned_data:
            if "raw_import_record_id" in record and "id" not in record:
                record["id"] = record["raw_import_record_id"]

        # CRITICAL: Await the update (no fire-and-forget)
        await self._update_cleansed_data_sync(cleaned_data)

        # Set phase completion flag
        await self._mark_phase_complete("data_cleansing")

        return {
            "cleaned_data": cleaned_data,
            "cleansing_summary": self._generate_cleansing_summary(cleaned_data),
            "quality_metrics": self._calculate_cleansing_quality_metrics(cleaned_data),
            "persistent_agent_used": True,
            "crew_based": False,
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
                    "cpu_utilization_percent": self._safe_float_convert(
                        record.get("cpu_utilization_percent", record.get("cpu_usage"))
                    ),
                    "memory_utilization_percent": self._safe_float_convert(
                        record.get(
                            "memory_utilization_percent", record.get("memory_usage")
                        )
                    ),
                    "disk_utilization_percent": self._safe_float_convert(
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

    def _generate_enrichment_summary(
        self, enriched_assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of agentic enrichment results"""

        total_assets = len(enriched_assets)
        successful_enrichments = sum(
            1
            for asset in enriched_assets
            if asset.get("enrichment_status") == "agentic_complete"
        )

        # Business Value Distribution
        business_value_distribution = {"high": 0, "medium": 0, "low": 0}
        for asset in enriched_assets:
            score = asset.get("business_value_score", 5)
            if score >= 8:
                business_value_distribution["high"] += 1
            elif score >= 6:
                business_value_distribution["medium"] += 1
            else:
                business_value_distribution["low"] += 1

        # Risk Assessment Distribution
        risk_distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for asset in enriched_assets:
            risk_level = asset.get("risk_assessment", "medium")
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # Cloud Readiness Distribution
        cloud_ready_count = sum(
            1
            for asset in enriched_assets
            if asset.get("cloud_readiness_score", 50) >= 70
        )
        modernization_ready_count = sum(
            1
            for asset in enriched_assets
            if asset.get("modernization_potential") == "high"
        )

        summary = {
            "total_assets_analyzed": total_assets,
            "successful_enrichments": successful_enrichments,
            "enrichment_success_rate": (
                round((successful_enrichments / total_assets * 100), 1)
                if total_assets > 0
                else 0
            ),
            "business_value_distribution": business_value_distribution,
            "risk_assessment_distribution": risk_distribution,
            "cloud_readiness_metrics": {
                "cloud_ready_assets": cloud_ready_count,
                "modernization_ready_assets": modernization_ready_count,
                "cloud_readiness_percentage": (
                    round((cloud_ready_count / total_assets * 100), 1)
                    if total_assets > 0
                    else 0
                ),
            },
            "agentic_intelligence_metrics": {
                "patterns_discovered": sum(
                    asset.get("memory_patterns_discovered", 0)
                    for asset in enriched_assets
                ),
                "average_confidence": (
                    round(
                        sum(
                            asset.get("agentic_confidence_score", 0.5)
                            for asset in enriched_assets
                        )
                        / total_assets,
                        2,
                    )
                    if total_assets > 0
                    else 0.0
                ),
            },
        }

        return summary

    def _calculate_agentic_quality_metrics(
        self, enriched_assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate quality metrics based on agentic enrichment completeness"""

        total_assets = len(enriched_assets)
        if total_assets == 0:
            return {"quality_score": 0, "completeness": 0}

        # Calculate completeness based on enrichment fields
        enrichment_fields = [
            "business_value_score",
            "risk_assessment",
            "cloud_readiness_score",
            "business_value_reasoning",
            "risk_analysis_reasoning",
            "architecture_assessment",
        ]

        completeness_scores = []
        for asset in enriched_assets:
            field_count = sum(
                1 for field in enrichment_fields if asset.get(field) is not None
            )
            completeness = field_count / len(enrichment_fields)
            completeness_scores.append(completeness)

        average_completeness = sum(completeness_scores) / len(completeness_scores)

        # Calculate overall quality score
        successful_enrichments = sum(
            1
            for asset in enriched_assets
            if asset.get("enrichment_status") == "agentic_complete"
        )
        success_rate = successful_enrichments / total_assets

        # Quality score combines completeness and success rate
        quality_score = (average_completeness * 0.6) + (success_rate * 0.4)

        return {
            "quality_score": round(quality_score * 100, 1),
            "completeness_percentage": round(average_completeness * 100, 1),
            "success_rate_percentage": round(success_rate * 100, 1),
            "agentic_analysis_used": True,
            "total_assets_processed": total_assets,
            "successfully_enriched": successful_enrichments,
        }

    def _safe_float_convert(self, value: Any) -> float:
        """Safely convert a value to float, returning 0.0 if conversion fails"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    async def _update_cleansed_data_sync(self, cleaned_data: List[Dict[str, Any]]):
        """Update raw records with cleansed data - SYNCHRONOUS, no fire-and-forget"""
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

            updated_count = await storage_manager.update_raw_records_with_cleansed_data(
                data_import_id=data_import_id,
                cleansed_data=cleaned_data,
                validation_results=getattr(self.state, "data_validation_results", None),
            )

            if should_commit:
                await db.commit()

            logger.info(f"✅ Updated {updated_count} raw records with cleansed data")

        finally:
            if should_commit and db:
                await db.close()

    async def _mark_phase_complete(self, phase_name: str):
        """Mark phase as complete for progression tracking"""
        # For now, just log the phase completion
        # The actual phase tracking is handled by the master flow orchestrator
        logger.info(f"✅ Phase {phase_name} completed for flow {self.state.flow_id}")

        # Update state to indicate phase completion
        if phase_name == "data_cleansing":
            self.state.data_cleansing_completed = True
            logger.info("✅ Set data_cleansing_completed flag in state")

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

            # WITH TENANT SCOPING
            query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.client_account_id == self.state.client_account_id,
                RawImportRecord.engagement_id == self.state.engagement_id,
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
