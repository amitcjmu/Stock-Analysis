"""
Data Cleansing Executor - Agentic Intelligence Integration
Handles data cleansing phase execution for the Unified Discovery Flow.
Now integrates agentic intelligence for comprehensive asset enrichment.
"""

import asyncio
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
        """Execute data cleansing with agentic intelligence instead of basic crew processing"""

        logger.info(
            "🧠 Starting agentic asset enrichment instead of basic data cleansing"
        )

        try:
            # Import agentic intelligence
            from app.services.agentic_intelligence.agentic_asset_enrichment import (
                enrich_assets_with_agentic_intelligence,
            )

            # Get raw import records from database with their IDs for proper linkage
            raw_import_records = await self._get_raw_import_records_with_ids()
            logger.info(
                f"🔄 Converting {len(raw_import_records)} raw import records to asset profiles for agentic analysis"
            )

            # Transform raw import records into structured assets with ID preservation
            assets_for_analysis = self._prepare_assets_for_agentic_analysis(
                raw_import_records
            )

            if not assets_for_analysis:
                logger.error(
                    "❌ No assets prepared for agentic analysis - this is a critical error"
                )
                raise RuntimeError(
                    "No assets prepared for agentic analysis - check raw data preparation"
                )

            # Extract multi-tenant context from state
            client_account_id = (
                uuid.UUID(self.state.client_account_id)
                if self.state.client_account_id
                else None
            )
            engagement_id = (
                uuid.UUID(self.state.engagement_id)
                if self.state.engagement_id
                else None
            )
            flow_id = uuid.UUID(self.state.flow_id) if self.state.flow_id else None

            if not client_account_id or not engagement_id:
                logger.error("Missing multi-tenant context for agentic analysis")
                # NO FALLBACK - Multi-tenant context is required
                raise RuntimeError(
                    "Missing multi-tenant context for agentic analysis. This is required."
                )

            # Perform agentic asset enrichment
            enriched_assets = await enrich_assets_with_agentic_intelligence(
                assets=assets_for_analysis,
                crewai_service=self.crew_manager.crewai_service,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                flow_id=flow_id,
                batch_size=3,  # Process 3 assets at a time
                enable_parallel_agents=True,  # Enable parallel agent execution
            )

            logger.info(
                f"✅ Agentic enrichment completed for {len(enriched_assets)} assets"
            )

            # Return results in expected format
            return {
                "cleaned_data": enriched_assets,  # Now enriched with agentic intelligence
                "enrichment_summary": self._generate_enrichment_summary(
                    enriched_assets
                ),
                "quality_metrics": self._calculate_agentic_quality_metrics(
                    enriched_assets
                ),
                "agentic_analysis": True,
            }

        except Exception as e:
            logger.error(f"❌ Agentic enrichment failed: {e}")
            logger.error(
                "❌ This indicates a real issue with agent execution that must be fixed"
            )
            raise

    async def execute_fallback(self) -> Dict[str, Any]:
        """NO FALLBACK ALLOWED - FAIL FAST TO EXPOSE REAL ISSUES"""
        logger.error(
            "❌ execute_fallback called for data_cleansing - FALLBACK DISABLED"
        )
        logger.error(
            "❌ If you see this error, fix the actual agentic intelligence execution issues"
        )
        raise RuntimeError(
            "Data cleansing fallback disabled - agentic intelligence must work properly"
        )

    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, "field_mappings", {}),
            "cleansing_type": "comprehensive_data_cleansing",
        }

    def _store_results(self, results: Dict[str, Any]):
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
        self._update_raw_records_with_cleansed_data(cleaned_data)

    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process data cleansing crew result and extract cleaned data - NO FALLBACKS"""
        logger.info(f"🔍 Processing data cleansing crew result: {type(crew_result)}")

        if hasattr(crew_result, "raw") and crew_result.raw:
            logger.info(f"📄 Crew raw output: {crew_result.raw}")

            # Try to parse JSON from crew output if it contains structured data
            import json

            try:
                if "{" in crew_result.raw and "}" in crew_result.raw:
                    # Try to extract JSON from the output
                    start = crew_result.raw.find("{")
                    end = crew_result.raw.rfind("}") + 1
                    json_str = crew_result.raw[start:end]
                    parsed_result = json.loads(json_str)

                    if (
                        "cleaned_data" in parsed_result
                        or "standardized_data" in parsed_result
                    ):
                        logger.info("✅ Found structured data in crew output")
                        return {
                            "cleaned_data": parsed_result.get(
                                "cleaned_data",
                                parsed_result.get("standardized_data", []),
                            ),
                            "quality_metrics": parsed_result.get("quality_metrics", {}),
                            "raw_result": crew_result.raw,
                        }
                    else:
                        logger.error(
                            f"❌ Crew JSON missing required keys. Got: {list(parsed_result.keys())}"
                        )
                        raise ValueError(
                            "Data cleansing crew returned JSON without cleaned_data or standardized_data"
                        )
                else:
                    logger.error(
                        f"❌ Crew output does not contain valid JSON: {crew_result.raw}"
                    )
                    raise ValueError("Data cleansing crew did not return JSON output")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Failed to parse JSON from crew output: {e}")
                logger.error(f"❌ Raw crew output: {crew_result.raw}")
                raise RuntimeError(f"Data cleansing crew output parsing failed: {e}")

        # If crew_result is already a dict, validate it
        elif isinstance(crew_result, dict):
            if "cleaned_data" in crew_result or "standardized_data" in crew_result:
                logger.info("✅ Crew returned valid dict with cleaned data")
                return crew_result
            else:
                logger.error(
                    f"❌ Crew dict missing required keys. Got: {list(crew_result.keys())}"
                )
                raise ValueError(
                    "Data cleansing crew returned dict without cleaned_data"
                )

        # No fallback allowed
        else:
            logger.error(f"❌ Unexpected crew result format: {type(crew_result)}")
            logger.error(f"❌ Crew result: {crew_result}")
            raise RuntimeError(
                f"Data cleansing crew returned unexpected result type: {type(crew_result)}"
            )

    async def _get_raw_import_records_with_ids(self) -> List[Dict[str, Any]]:
        """Get raw import records from database with their IDs preserved"""
        from app.core.database import AsyncSessionLocal
        from app.models.data_import.core import RawImportRecord
        from sqlalchemy import select

        records = []
        try:
            async with AsyncSessionLocal() as session:
                # Get data_import_id from state
                data_import_id = getattr(self.state, "data_import_id", None)
                if not data_import_id:
                    logger.error("❌ No data_import_id found in state")
                    return []

                # Query raw import records
                query = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == data_import_id)
                    .where(RawImportRecord.is_valid is True)
                )

                result = await session.execute(query)
                raw_records = result.scalars().all()

                for record in raw_records:
                    # Preserve the raw import record ID for linkage
                    record_data = {
                        "raw_import_record_id": str(record.id),
                        "row_number": record.row_number,
                        "raw_data": record.raw_data,
                        "cleansed_data": record.cleansed_data,
                        **record.raw_data,  # Flatten raw data for easy access
                    }
                    records.append(record_data)

                logger.info(f"✅ Retrieved {len(records)} raw import records with IDs")
                return records

        except Exception as e:
            logger.error(f"❌ Failed to get raw import records: {e}")
            return []

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

    def _safe_float_convert(self, value) -> float:
        """Safely convert value to float with fallback"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

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

    def _update_raw_records_with_cleansed_data(
        self, cleaned_data: List[Dict[str, Any]]
    ):
        """Update raw_import_records in the database with cleansed data"""
        try:
            # Get data_import_id from state
            data_import_id = getattr(self.state, "data_import_id", None)
            if not data_import_id:
                logger.warning("No data_import_id in state - cannot update raw records")
                return

            # Get validation results from state if available
            validation_results = getattr(self.state, "data_validation_results", None)

            # Create async task to update database
            async def update_records():
                try:
                    from app.core.database import AsyncSessionLocal
                    from app.services.data_import.storage_manager import (
                        ImportStorageManager,
                    )

                    async with AsyncSessionLocal() as db:
                        storage_manager = ImportStorageManager(
                            db, str(self.state.client_account_id)
                        )

                        # Convert data_import_id to UUID if it's a string
                        import uuid as uuid_pkg

                        if isinstance(data_import_id, str):
                            import_uuid = uuid_pkg.UUID(data_import_id)
                        else:
                            import_uuid = data_import_id

                        updated_count = (
                            await storage_manager.update_raw_records_with_cleansed_data(
                                data_import_id=import_uuid,
                                cleansed_data=cleaned_data,
                                validation_results=validation_results,
                            )
                        )

                        await db.commit()
                        logger.info(
                            f"✅ Updated {updated_count} raw records with cleansed data"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to update raw records with cleansed data: {e}"
                    )

            # Run the async update in the background
            asyncio.create_task(update_records())

        except Exception as e:
            logger.error(f"Error setting up raw records update: {e}")
