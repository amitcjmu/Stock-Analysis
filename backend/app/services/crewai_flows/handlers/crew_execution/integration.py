"""
Discovery Integration and Database Persistence Handler
"""

import asyncio
import hashlib
import logging
import uuid as uuid_pkg
from datetime import datetime
from typing import Any, Dict

from .base import CrewExecutionBase

logger = logging.getLogger(__name__)


class DiscoveryIntegrationExecutor(CrewExecutionBase):
    """Handles final discovery integration and database persistence"""

    def execute_discovery_integration(self, state) -> Dict[str, Any]:
        """Execute Discovery Integration - final consolidation"""
        # Create comprehensive discovery summary
        discovery_summary = {
            "total_assets": len(state.cleaned_data),
            "asset_breakdown": {
                "servers": len(state.asset_inventory.get("servers", [])),
                "applications": len(state.asset_inventory.get("applications", [])),
                "devices": len(state.asset_inventory.get("devices", [])),
            },
            "dependency_analysis": {
                "app_server_relationships": len(
                    state.app_server_dependencies.get("hosting_relationships", [])
                ),
                "app_app_integrations": len(
                    state.app_app_dependencies.get("communication_patterns", [])
                ),
            },
            "technical_debt_score": state.technical_debt_assessment.get(
                "debt_scores", {}
            ).get("overall", 0),
            "six_r_readiness": True,
        }

        # Prepare Assessment Flow package
        assessment_flow_package = {
            "discovery_flow_id": state.flow_id,
            "asset_inventory": state.asset_inventory,
            "dependencies": {
                "app_server": state.app_server_dependencies,
                "app_app": state.app_app_dependencies,
            },
            "technical_debt": state.technical_debt_assessment,
            "field_mappings": state.field_mappings,
            "data_quality": state.data_quality_metrics,
            "discovery_timestamp": datetime.utcnow().isoformat(),
            "crew_execution_summary": state.crew_status,
        }

        # **CRITICAL FIX**: Add database persistence
        database_integration_results = self._persist_discovery_data_to_database(state)

        return {
            "discovery_summary": discovery_summary,
            "assessment_flow_package": assessment_flow_package,
            "database_integration": database_integration_results,
        }

    def _persist_discovery_data_to_database(self, state) -> Dict[str, Any]:
        """Persist discovery data to database tables - Synchronous wrapper"""
        try:
            # Run async code in a separate thread to avoid event loop conflicts
            def run_in_thread():
                return asyncio.run(self._async_persist_discovery_data(state))

            # Execute in a separate thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                persistence_results = future.result(timeout=60)  # 60 second timeout

            logger.info(
                f"✅ Discovery data persisted to database: {persistence_results}"
            )
            return persistence_results
        except Exception as e:
            logger.error(f"❌ Database persistence failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "assets_created": 0,
                "imports_created": 0,
                "records_created": 0,
            }

    async def _async_persist_discovery_data(self, state) -> Dict[str, Any]:
        """Async method to persist discovery data to database"""
        from sqlalchemy.exc import SQLAlchemyError

        from app.core.database import AsyncSessionLocal
        from app.models.data_import import DataImport, ImportStatus, RawImportRecord
        from app.models.data_import.mapping import ImportFieldMapping

        assets_created = 0
        imports_created = 0
        records_created = 0
        field_mappings_created = 0

        async with AsyncSessionLocal() as db_session:
            try:
                # 1. Create DataImport session record
                import_session = DataImport(
                    id=uuid_pkg.uuid4(),
                    client_account_id=(
                        uuid_pkg.UUID(state.client_account_id)
                        if state.client_account_id
                        else None
                    ),
                    engagement_id=(
                        uuid_pkg.UUID(state.engagement_id)
                        if state.engagement_id
                        else None
                    ),
                    session_id=uuid_pkg.UUID(state.flow_id) if state.flow_id else None,
                    import_name=f"CrewAI Discovery Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    import_type="discovery_flow",
                    description="Data processed by CrewAI Discovery Flow with specialized crews",
                    source_filename=state.metadata.get(
                        "filename", "discovery_flow_data.csv"
                    ),
                    file_size_bytes=len(str(state.cleaned_data).encode()),
                    file_type="application/json",
                    file_hash=hashlib.sha256(
                        str(state.cleaned_data).encode()
                    ).hexdigest()[:32],
                    status=ImportStatus.PROCESSED,
                    total_records=len(state.cleaned_data),
                    processed_records=len(state.cleaned_data),
                    failed_records=0,
                    import_config={
                        "discovery_flow_state": {
                            "crew_status": state.crew_status,
                            "field_mappings": state.field_mappings.get("mappings", {}),
                            "asset_inventory": state.asset_inventory,
                            "technical_debt": state.technical_debt_assessment,
                        }
                    },
                    imported_by=(
                        uuid_pkg.UUID(state.user_id)
                        if state.user_id and state.user_id != "anonymous"
                        else uuid_pkg.UUID("44444444-4444-4444-4444-444444444444")
                    ),
                    completed_at=datetime.utcnow(),
                )

                db_session.add(import_session)
                await db_session.flush()
                imports_created = 1

                # 2. Create RawImportRecord entries for each cleaned record
                for index, record in enumerate(state.cleaned_data):
                    raw_record = RawImportRecord(
                        id=uuid_pkg.uuid4(),
                        data_import_id=import_session.id,
                        client_account_id=import_session.client_account_id,
                        engagement_id=import_session.engagement_id,
                        session_id=import_session.session_id,
                        row_number=index + 1,
                        record_id=record.get("asset_name")
                        or record.get("hostname")
                        or f"record_{index + 1}",
                        raw_data=record,
                        is_processed=True,
                        is_valid=True,
                        created_at=datetime.utcnow(),
                    )
                    db_session.add(raw_record)
                    records_created += 1

                # 3. Create ImportFieldMapping entries
                field_mappings = state.field_mappings.get("mappings", {})
                confidence_scores = state.field_mappings.get("confidence_scores", {})
                agent_reasoning = state.field_mappings.get("agent_reasoning", {})
                transformations = state.field_mappings.get("transformations", [])

                # CRITICAL: Get master_flow_id from state for field mapping linkage
                master_flow_id = getattr(state, "master_flow_id", None) or getattr(
                    state, "_master_flow_id", None
                )
                logger.info(
                    f"🔗 Using master_flow_id for field mappings: {master_flow_id}"
                )

                # If no master_flow_id, skip creating field mappings to avoid foreign key errors
                if not master_flow_id:
                    logger.warning(
                        "⚠️ No master_flow_id available - skipping field mapping creation to avoid "
                        "foreign key constraint errors"
                    )
                    logger.warning(
                        "⚠️ This indicates a flow creation order issue that needs to be fixed"
                    )

                    # Commit what we have so far before returning
                    try:
                        await db_session.commit()
                        logger.info(
                            "✅ Committed partial data (import session and records)"
                        )
                    except Exception as e:
                        await db_session.rollback()
                        logger.error(f"❌ Failed to commit partial data: {e}")

                    return {
                        "status": "error",
                        "error": "missing_master_flow_id",
                        "message": "Cannot create field mappings without a master_flow_id",
                        "assets_created": assets_created,
                        "imports_created": imports_created,
                        "records_created": records_created,
                        "field_mappings_created": 0,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                logger.info(
                    f"🔍 Creating {len(field_mappings)} field mappings for data_import_id: {import_session.id}"
                )

                for source_field, target_field in field_mappings.items():
                    # Get reasoning and transformation info for this field
                    field_reasoning = agent_reasoning.get(source_field, {})

                    # Find any transformations for this field
                    field_transformations = [
                        t
                        for t in transformations
                        if source_field in t.get("source_fields", [])
                    ]

                    # Build transformation rules JSON
                    transformation_rules = {
                        "agent_reasoning": field_reasoning.get("reasoning", ""),
                        "data_patterns": field_reasoning.get("data_patterns", {}),
                        "requires_transformation": field_reasoning.get(
                            "requires_transformation", False
                        ),
                        "transformations": field_transformations,
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "crew_version": "2.0",
                    }

                    field_mapping = ImportFieldMapping(
                        data_import_id=import_session.id,
                        client_account_id=state.client_account_id,  # Add missing field
                        master_flow_id=master_flow_id,  # CRITICAL FIX: Add master_flow_id
                        source_field=source_field,
                        target_field=target_field,
                        confidence_score=confidence_scores.get(source_field, 0.8),
                        match_type="agent_analysis",  # Updated from mapping_type
                        status="approved",
                        suggested_by="crewai_agent_v2",
                        transformation_rules=transformation_rules,  # Store agent reasoning and transformations
                        created_at=datetime.utcnow(),
                    )
                    db_session.add(field_mapping)
                    field_mappings_created += 1

                # 4. Commit all changes
                await db_session.commit()

                logger.info("✅ Database persistence completed:")
                logger.info(f"   - Imports created: {imports_created}")
                logger.info(f"   - Records created: {records_created}")
                logger.info(f"   - Field mappings created: {field_mappings_created}")

                return {
                    "status": "success",
                    "import_session_id": str(import_session.id),
                    "assets_created": assets_created,
                    "imports_created": imports_created,
                    "records_created": records_created,
                    "field_mappings_created": field_mappings_created,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            except SQLAlchemyError as e:
                await db_session.rollback()
                logger.error(f"Database persistence error: {e}")
                raise
            except Exception as e:
                await db_session.rollback()
                logger.error(f"Unexpected error during persistence: {e}")
                raise
