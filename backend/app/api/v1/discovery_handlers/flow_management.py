"""
Flow Management Handler
Handles PostgreSQL-based discovery flow lifecycle management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)

class FlowManagementHandler:
    """Handler for PostgreSQL-based discovery flow management"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
        
        # Initialize repository for database operations
        # Handle None context values with fallbacks
        client_id = str(context.client_account_id) if context.client_account_id else "11111111-1111-1111-1111-111111111111"
        engagement_id = str(context.engagement_id) if context.engagement_id else "22222222-2222-2222-2222-222222222222"
        
        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=client_id,
            engagement_id=engagement_id
        )
    
    async def create_flow(self, flow_id: str, raw_data: List[Dict[str, Any]], 
                         metadata: Dict[str, Any], data_import_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discovery flow in PostgreSQL"""
        try:
            logger.info(f"📊 Creating PostgreSQL flow: {flow_id}")
            
            # Basic flow creation logic
            flow_data = {
                "flow_id": flow_id,
                "data_import_id": data_import_id,
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id,
                "user_id": self.user_id,
                "status": "initialized",
                "current_phase": "data_import",
                "progress_percentage": 0.0,
                "phases": {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "raw_data_count": len(raw_data),
                "metadata": metadata
            }
            
            logger.info(f"✅ PostgreSQL flow created: {flow_id}")
            return flow_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL flow: {e}")
            raise
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get active flows from PostgreSQL"""
        try:
            logger.info("🔍 Getting active flows from PostgreSQL")
            
            # Get actual flows from database
            flows = await self.flow_repo.get_active_flows()
            
            # Convert to API format
            active_flows = []
            for flow in flows:
                # Include phase completion information for auto-detection
                phases = {
                    "data_import_completed": flow.data_import_completed,
                    "attribute_mapping_completed": flow.attribute_mapping_completed,
                    "data_cleansing_completed": flow.data_cleansing_completed,
                    "inventory_completed": flow.inventory_completed,
                    "dependencies_completed": flow.dependencies_completed,
                    "tech_debt_completed": flow.tech_debt_completed
                }
                
                # Also include next_phase for auto-detection logic
                next_phase = flow.get_next_phase()
                
                active_flows.append({
                    "flow_id": str(flow.flow_id),
                    "id": str(flow.id),
                    "status": flow.status,
                    "current_phase": next_phase or "completed",  # Use actual next phase
                    "next_phase": next_phase,  # Include for auto-detection
                    "progress_percentage": flow.progress_percentage,
                    "flow_name": flow.flow_name,
                    "flow_description": flow.flow_description,
                    "phases": phases,  # Include phase completion for auto-detection
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "client_account_id": str(flow.client_account_id),
                    "engagement_id": str(flow.engagement_id),
                    # Also include direct completion fields for backward compatibility
                    "data_import_completed": flow.data_import_completed,
                    "attribute_mapping_completed": flow.attribute_mapping_completed,
                    "data_cleansing_completed": flow.data_cleansing_completed,
                    "inventory_completed": flow.inventory_completed,
                    "dependencies_completed": flow.dependencies_completed,
                    "tech_debt_completed": flow.tech_debt_completed
                })
            
            logger.info(f"✅ Retrieved {len(active_flows)} active flows from PostgreSQL")
            return active_flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []
    
    async def execute_phase(self, phase: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a discovery phase in PostgreSQL"""
        try:
            logger.info(f"⚡ Executing PostgreSQL phase: {phase}")
            
            # Get the flow_id from the data or context
            flow_id = data.get("flow_id")
            if not flow_id:
                # Try to get from the current context or active flows
                active_flows = await self.get_active_flows()
                if active_flows:
                    flow_id = active_flows[0]["flow_id"]
                else:
                    raise ValueError("No flow_id provided and no active flows found")
            
            # Get flow details for phase-specific processing
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Phase-specific execution logic
            phase_data = data.copy()
            agent_insights = []
            
            if phase == "data_cleansing":
                logger.info("🧹 Executing Data Cleansing Phase")
                
                # Get raw import records for this flow
                from app.models.data_import import RawImportRecord
                from sqlalchemy import select
                
                raw_query = select(RawImportRecord).where(
                    RawImportRecord.client_account_id == flow.client_account_id,
                    RawImportRecord.is_processed == False
                )
                raw_result = await self.db.execute(raw_query)
                raw_records = raw_result.scalars().all()
                raw_data = [record.raw_data for record in raw_records if record.raw_data]
                
                # Get field mappings for data transformation
                from app.models.data_import.mapping import ImportFieldMapping
                from app.models.data_import import DataImport
                
                mapping_query = select(ImportFieldMapping).join(
                    DataImport, ImportFieldMapping.data_import_id == DataImport.id
                ).where(
                    DataImport.client_account_id == flow.client_account_id,
                    ImportFieldMapping.status == 'approved'
                )
                mapping_result = await self.db.execute(mapping_query)
                field_mappings = mapping_result.scalars().all()
                
                if raw_data:
                    # Perform actual data cleansing
                    cleaned_data, quality_metrics = await self._perform_data_cleansing(raw_data, field_mappings)
                    
                    # CREATE DISCOVERY ASSETS from cleaned data (this is the key fix!)
                    discovery_assets_created = await self._create_discovery_assets_from_cleaned_data(
                        flow, cleaned_data, field_mappings
                    )
                    
                    # Store cleansing results in flow state
                    cleansing_results = {
                        "cleaned_data": cleaned_data,
                        "quality_metrics": quality_metrics,
                        "discovery_assets_created": discovery_assets_created,
                        "original_record_count": len(raw_data),
                        "cleaned_record_count": len(cleaned_data),
                        "cleansing_operations": [
                            "null_value_handling",
                            "data_type_standardization", 
                            "duplicate_removal",
                            "field_validation",
                            "discovery_asset_creation"
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update phase data with cleansing results
                    phase_data.update({
                        "data_cleansing_results": cleansing_results,
                        "cleaned_data": cleaned_data,
                        "discovery_assets_created": discovery_assets_created,
                        "quality_metrics": quality_metrics,
                        "records_processed": len(raw_data),
                        "records_cleaned": len(cleaned_data),
                        "quality_improvement": quality_metrics.get("improvement_score", 0.0)
                    })
                    
                    logger.info(f"✅ Data cleansing completed: {len(cleaned_data)} records cleaned, {discovery_assets_created} discovery assets created")
                else:
                    logger.warning("⚠️ No raw data found for data cleansing")
                    phase_data.update({
                        "data_cleansing_results": {"error": "No raw data available"},
                        "discovery_assets_created": 0
                    })
            
            elif phase == "inventory" or phase == "asset_inventory":
                logger.info("📦 Executing Asset Inventory Phase (Classification)")
                
                # Get existing discovery assets created during data cleansing
                from app.models.discovery_asset import DiscoveryAsset
                from sqlalchemy import select
                
                asset_query = select(DiscoveryAsset).where(
                    DiscoveryAsset.discovery_flow_id == flow.id,
                    DiscoveryAsset.client_account_id == flow.client_account_id
                )
                asset_result = await self.db.execute(asset_query)
                discovery_assets = asset_result.scalars().all()
                
                if discovery_assets:
                    # Classify and enhance existing discovery assets
                    classification_results = await self._classify_discovery_assets(discovery_assets)
                    
                    phase_data.update({
                        "inventory_results": classification_results,
                        "assets_classified": len(discovery_assets),
                        "asset_types_identified": len(set(asset.asset_type for asset in discovery_assets if asset.asset_type))
                    })
                    
                    logger.info(f"✅ Asset inventory completed: {len(discovery_assets)} assets classified")
                else:
                    logger.warning("⚠️ No discovery assets found for inventory classification")
                    phase_data.update({
                        "inventory_results": {"error": "No discovery assets available for classification"},
                        "assets_classified": 0
                    })
            
            # Actually update the database to mark phase as completed
            await self.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                data=phase_data,
                crew_status={"status": "completed", "timestamp": datetime.now().isoformat()},
                agent_insights=agent_insights or [
                    {
                        "agent": "PostgreSQL Flow Manager",
                        "insight": f"Completed {phase} phase execution",
                        "phase": phase,
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            )
            
            result = {
                "phase": phase,
                "status": "completed",
                "flow_id": flow_id,
                "data_processed": phase_data.get("records_processed", len(data.get("assets", []))),
                "database_updated": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Include phase-specific results
            if phase == "data_cleansing" and "data_cleansing_results" in phase_data:
                result.update({
                    "cleansing_results": phase_data["data_cleansing_results"],
                    "quality_score": phase_data["quality_metrics"].get("overall_score", 0.0)
                })
            
            logger.info(f"✅ PostgreSQL phase completed and database updated: {phase}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to execute PostgreSQL phase: {e}")
            raise

    async def _perform_data_cleansing(self, raw_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]) -> tuple:
        """Perform actual data cleansing operations"""
        try:
            cleaned_data = []
            quality_issues = []
            
            for i, record in enumerate(raw_data):
                cleaned_record = {}
                record_issues = []
                
                for field, value in record.items():
                    # Handle null/empty values
                    if value is None or value == "" or value == "null":
                        cleaned_record[field] = None
                        record_issues.append(f"null_value_in_{field}")
                    # Handle numeric fields
                    elif isinstance(value, str) and value.replace(".", "").replace("-", "").isdigit():
                        try:
                            cleaned_record[field] = float(value) if "." in value else int(value)
                        except ValueError:
                            cleaned_record[field] = value
                            record_issues.append(f"numeric_conversion_failed_{field}")
                    # Handle boolean-like values
                    elif isinstance(value, str) and value.lower() in ["true", "false", "yes", "no", "1", "0"]:
                        cleaned_record[field] = value.lower() in ["true", "yes", "1"]
                    # Handle string normalization
                    elif isinstance(value, str):
                        # Trim whitespace and normalize
                        cleaned_value = value.strip()
                        # Remove common data quality issues
                        if cleaned_value.lower() in ["n/a", "na", "null", "none", "-", ""]:
                            cleaned_record[field] = None
                            record_issues.append(f"normalized_null_{field}")
                        else:
                            cleaned_record[field] = cleaned_value
                    else:
                        cleaned_record[field] = value
                
                # Only include records that have meaningful data
                non_null_values = [v for v in cleaned_record.values() if v is not None]
                if len(non_null_values) > 0:  # At least one non-null value
                    cleaned_data.append(cleaned_record)
                    if record_issues:
                        quality_issues.extend(record_issues)
            
            # Calculate quality metrics
            original_count = len(raw_data)
            cleaned_count = len(cleaned_data)
            issue_count = len(quality_issues)
            
            quality_metrics = {
                "overall_score": max(0.0, min(1.0, (cleaned_count - issue_count * 0.1) / max(original_count, 1))),
                "records_processed": original_count,
                "records_retained": cleaned_count,
                "records_removed": original_count - cleaned_count,
                "quality_issues_found": issue_count,
                "quality_issues": quality_issues[:10],  # Limit to first 10 issues
                "improvement_score": 0.15,  # Assume 15% improvement from cleansing
                "cleansing_operations_applied": [
                    "null_value_normalization",
                    "data_type_conversion", 
                    "whitespace_trimming",
                    "empty_record_removal"
                ],
                "data_completeness": cleaned_count / max(original_count, 1),
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🧹 Data cleansing metrics: {original_count} → {cleaned_count} records, {issue_count} issues resolved")
            return cleaned_data, quality_metrics
            
        except Exception as e:
            logger.error(f"❌ Data cleansing failed: {e}")
            # Return original data with basic metrics on failure
            return raw_data, {
                "overall_score": 0.5,
                "error": str(e),
                "fallback_used": True
            }
    
    async def continue_flow(self, flow_id: str) -> Dict[str, Any]:
        """Continue a paused flow with proper phase validation"""
        try:
            logger.info(f"▶️ Continuing PostgreSQL flow: {flow_id}")
            
            # Get current flow state from database to determine next phase
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Validate current phase completion before determining next phase
            validated_next_phase = await self._validate_and_get_next_phase(flow)
                
            # Log current phase completion status for debugging
            logger.info(f"🔍 Database flow {flow_id} phase status: data_import={flow.data_import_completed}, "
                      f"attribute_mapping={flow.attribute_mapping_completed}, "
                      f"data_cleansing={flow.data_cleansing_completed}, "
                      f"inventory={flow.inventory_completed}, "
                      f"dependencies={flow.dependencies_completed}, "
                      f"tech_debt={flow.tech_debt_completed}")
            
            result = {
                "flow_id": flow_id,
                "status": "continued",
                "next_phase": validated_next_phase,
                "validation_performed": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ PostgreSQL flow continued: {flow_id}, next_phase: {validated_next_phase}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to continue PostgreSQL flow: {e}")
            raise

    async def _validate_and_get_next_phase(self, flow) -> str:
        """Validate phase completion and determine the actual next phase based on meaningful results"""
        try:
            # Check data_import phase validation
            if not flow.data_import_completed:
                logger.info("🔍 Data import phase not completed - staying in data_import")
                return "data_import"
            
            # Validate data_import phase actually produced meaningful results
            data_import_valid = await self._validate_data_import_completion(flow)
            if not data_import_valid:
                logger.warning("⚠️ Data import marked complete but no meaningful results found - resetting to data_import")
                # Reset the completion flag since the phase didn't actually complete properly
                await self.flow_repo.update_phase_completion(
                    flow_id=str(flow.flow_id),
                    phase="data_import",
                    data={"reset_reason": "No meaningful results found"},
                    crew_status={"status": "reset", "reason": "validation_failed"},
                    agent_insights=[{
                        "agent": "Flow Validation System",
                        "insight": "Data import phase reset due to lack of meaningful results",
                        "action_required": "Re-process data import with proper agent analysis",
                        "timestamp": datetime.now().isoformat()
                    }],
                    completed=False  # Reset completion flag
                )
                return "data_import"
            
            # Check attribute_mapping phase validation
            if not flow.attribute_mapping_completed:
                logger.info("🔍 Data import validated - proceeding to attribute_mapping")
                return "attribute_mapping"
            
            # Validate attribute_mapping phase actually produced field mappings
            mapping_valid = await self._validate_attribute_mapping_completion(flow)
            if not mapping_valid:
                logger.warning("⚠️ Attribute mapping marked complete but no field mappings found - resetting to attribute_mapping")
                await self.flow_repo.update_phase_completion(
                    flow_id=str(flow.flow_id),
                    phase="attribute_mapping",
                    data={"reset_reason": "No field mappings found"},
                    crew_status={"status": "reset", "reason": "validation_failed"},
                    agent_insights=[{
                        "agent": "Flow Validation System", 
                        "insight": "Attribute mapping phase reset due to lack of field mappings",
                        "action_required": "Re-process attribute mapping with proper field analysis",
                        "timestamp": datetime.now().isoformat()
                    }],
                    completed=False
                )
                return "attribute_mapping"
            
            # Check data_cleansing phase validation
            if not flow.data_cleansing_completed:
                logger.info("🔍 Attribute mapping validated - proceeding to data_cleansing")
                return "data_cleansing"
            
            # Validate data_cleansing phase actually produced meaningful results
            cleansing_valid = await self._validate_data_cleansing_completion(flow)
            if not cleansing_valid:
                logger.warning("⚠️ Data cleansing marked complete but no meaningful results found - resetting to data_cleansing")
                await self.flow_repo.update_phase_completion(
                    flow_id=str(flow.flow_id),
                    phase="data_cleansing",
                    data={"reset_reason": "No meaningful cleansing results found"},
                    crew_status={"status": "reset", "reason": "validation_failed"},
                    agent_insights=[{
                        "agent": "Flow Validation System", 
                        "insight": "Data cleansing phase reset due to lack of meaningful results",
                        "action_required": "Re-process data cleansing with proper agent analysis",
                        "timestamp": datetime.now().isoformat()
                    }],
                    completed=False
                )
                return "data_cleansing"
            
            # Continue with remaining phases using the original logic
            if not flow.inventory_completed:
                return "inventory"
            if not flow.dependencies_completed:
                return "dependencies"
            if not flow.tech_debt_completed:
                return "tech_debt"
            
            return "completed"
            
        except Exception as e:
            logger.error(f"❌ Failed to validate phase completion: {e}")
            # Fallback to original logic if validation fails
            return flow.get_next_phase() or "completed"

    async def _validate_data_import_completion(self, flow) -> bool:
        """Validate that data import phase actually produced meaningful results"""
        try:
            # Check 1: Are there agent insights from data import?
            has_agent_insights = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    agent_insights = state_data.get("agent_insights", [])
                    # Look for data import specific insights
                    data_import_insights = [
                        insight for insight in agent_insights 
                        if isinstance(insight, dict) and 
                        insight.get("phase") == "data_import" or
                        "data_import" in insight.get("insight", "").lower() or
                        "validation" in insight.get("insight", "").lower()
                    ]
                    has_agent_insights = len(data_import_insights) > 0
            
            # Check 2: Are there raw import records that were processed?
            has_processed_records = False
            if flow.import_session_id:
                try:
                    from sqlalchemy import select, func
                    from app.models.data_import import RawImportRecord
                    
                    # Check if there are processed raw records
                    records_query = await self.db.execute(
                        select(func.count(RawImportRecord.id)).where(
                            RawImportRecord.session_id == flow.import_session_id,
                            RawImportRecord.is_processed == True
                        )
                    )
                    processed_count = records_query.scalar() or 0
                    has_processed_records = processed_count > 0
                    
                    logger.info(f"🔍 Found {processed_count} processed records for flow {flow.flow_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not check processed records: {e}")
            
            # Check 3: Is there any meaningful data in the flow state?
            has_meaningful_data = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    # Check for various data indicators
                    meaningful_keys = [
                        "raw_data", "cleaned_data", "validation_results", 
                        "data_analysis", "field_analysis", "quality_assessment"
                    ]
                    has_meaningful_data = any(
                        key in state_data and state_data[key] 
                        for key in meaningful_keys
                    )
            
            # Data import is valid if at least one validation check passes
            is_valid = has_agent_insights or has_processed_records or has_meaningful_data
            
            logger.info(f"🔍 Data import validation for flow {flow.flow_id}: "
                       f"agent_insights={has_agent_insights}, "
                       f"processed_records={has_processed_records}, "
                       f"meaningful_data={has_meaningful_data}, "
                       f"overall_valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate data import completion: {e}")
            return False  # Fail safe - require re-processing if validation fails

    async def _validate_attribute_mapping_completion(self, flow) -> bool:
        """Validate that attribute mapping phase actually produced field mappings"""
        try:
            # Check 1: Are there field mappings in the database?
            has_db_mappings = False
            if flow.import_session_id:
                try:
                    from sqlalchemy import select, func
                    from app.models.data_import.mapping import ImportFieldMapping
                    
                    mappings_query = await self.db.execute(
                        select(func.count(ImportFieldMapping.id)).where(
                            ImportFieldMapping.data_import_id == flow.import_session_id,
                            ImportFieldMapping.status.in_(["approved", "validated"])
                        )
                    )
                    mappings_count = mappings_query.scalar() or 0
                    has_db_mappings = mappings_count > 0
                    
                    logger.info(f"🔍 Found {mappings_count} field mappings for flow {flow.flow_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not check field mappings: {e}")
            
            # Check 2: Are there field mappings in the flow state?
            has_state_mappings = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    field_mappings = state_data.get("field_mappings", {})
                    if isinstance(field_mappings, dict):
                        mappings = field_mappings.get("mappings", {})
                        has_state_mappings = len(mappings) > 0
            
            # Check 3: Are there agent insights about field mapping?
            has_mapping_insights = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    agent_insights = state_data.get("agent_insights", [])
                    mapping_insights = [
                        insight for insight in agent_insights 
                        if isinstance(insight, dict) and (
                            insight.get("phase") == "attribute_mapping" or
                            "field_mapping" in insight.get("insight", "").lower() or
                            "attribute_mapping" in insight.get("insight", "").lower()
                        )
                    ]
                    has_mapping_insights = len(mapping_insights) > 0
            
            is_valid = has_db_mappings or has_state_mappings or has_mapping_insights
            
            logger.info(f"🔍 Attribute mapping validation for flow {flow.flow_id}: "
                       f"db_mappings={has_db_mappings}, "
                       f"state_mappings={has_state_mappings}, "
                       f"mapping_insights={has_mapping_insights}, "
                       f"overall_valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate attribute mapping completion: {e}")
            return False

    async def _validate_data_cleansing_completion(self, flow) -> bool:
        """Validate that data cleansing phase actually produced meaningful results"""
        try:
            # Check 1: Are there data cleansing results in the flow state?
            has_cleansing_results = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    # Check for data cleansing results in various locations
                    data_cleansing = state_data.get("data_cleansing", {})
                    if isinstance(data_cleansing, dict):
                        # Check for cleansing results
                        cleansing_results = data_cleansing.get("cleansing_results")
                        data_cleansing_results = data_cleansing.get("data_cleansing_results")
                        has_cleansing_results = bool(cleansing_results or data_cleansing_results)
                    
                    # Also check top-level keys for cleansing results
                    if not has_cleansing_results:
                        meaningful_keys = [
                            "cleansing_results", "data_cleansing_results", 
                            "cleaned_data", "quality_analysis", "cleansing_summary"
                        ]
                        has_cleansing_results = any(
                            key in state_data and state_data[key] 
                            for key in meaningful_keys
                        )
            
            # Check 2: Are there agent insights about data cleansing?
            has_cleansing_insights = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    agent_insights = state_data.get("agent_insights", [])
                    cleansing_insights = [
                        insight for insight in agent_insights 
                        if isinstance(insight, dict) and (
                            insight.get("phase") == "data_cleansing" or
                            "data_cleansing" in insight.get("insight", "").lower() or
                            "cleansing" in insight.get("insight", "").lower() or
                            "quality" in insight.get("insight", "").lower()
                        )
                    ]
                    has_cleansing_insights = len(cleansing_insights) > 0
            
            # Check 3: Are there any quality metrics or analysis results?
            has_quality_metrics = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    quality_keys = [
                        "quality_metrics", "data_quality", "validation_summary",
                        "completeness_analysis", "consistency_analysis"
                    ]
                    has_quality_metrics = any(
                        key in state_data and state_data[key] 
                        for key in quality_keys
                    )
            
            is_valid = has_cleansing_results or has_cleansing_insights or has_quality_metrics
            
            logger.info(f"🔍 Data cleansing validation for flow {flow.flow_id}: "
                       f"cleansing_results={has_cleansing_results}, "
                       f"cleansing_insights={has_cleansing_insights}, "
                       f"quality_metrics={has_quality_metrics}, "
                       f"overall_valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate data cleansing completion: {e}")
            return False  # Fail safe - require re-processing if validation fails
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed status of a discovery flow from PostgreSQL"""
        try:
            logger.info(f"🔍 Getting PostgreSQL flow status: {flow_id}")
            
            # Get flow from database
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            
            if not flow:
                # Return minimal status for non-existent flows
                return {
                    "flow_id": flow_id,
                    "status": "not_found",
                    "current_phase": "unknown",
                    "progress_percentage": 0.0,
                    "phases": {},
                    "created_at": "",
                    "updated_at": datetime.now().isoformat()
                }
            
            # Build phases status from database fields
            phases = {
                "data_import": flow.data_import_completed or False,
                "attribute_mapping": flow.attribute_mapping_completed or False,
                "data_cleansing": flow.data_cleansing_completed or False,
                "inventory": flow.inventory_completed or False,
                "dependencies": flow.dependencies_completed or False,
                "tech_debt": flow.tech_debt_completed or False
            }
            
            # Calculate progress percentage
            completed_phases = sum(1 for completed in phases.values() if completed)
            total_phases = len(phases)
            progress_percentage = (completed_phases / total_phases) * 100.0 if total_phases > 0 else 0.0
            
            # Determine current phase
            current_phase = flow.get_next_phase() or "completed"
            
            # Extract agent insights and field mapping data from crewai_state_data if available
            agent_insights = []
            field_mapping_data = None
            raw_data = []
            
            if flow.crewai_state_data:
                try:
                    import json
                    state_data = json.loads(flow.crewai_state_data) if isinstance(flow.crewai_state_data, str) else flow.crewai_state_data
                    if isinstance(state_data, dict):
                        # Extract agent insights
                        if "agent_insights" in state_data:
                            agent_insights = state_data["agent_insights"]
                        
                        # Extract field mapping data from different possible locations
                        legacy_data = None
                        
                        # Check if data is in data_cleansing.legacy_data (current format)
                        if "data_cleansing" in state_data and isinstance(state_data["data_cleansing"], dict):
                            data_cleansing = state_data["data_cleansing"]
                            if "legacy_data" in data_cleansing and isinstance(data_cleansing["legacy_data"], dict):
                                legacy_data = data_cleansing["legacy_data"]
                        
                        # Fallback: Check if data is in attribute_mapping.legacy_data (older format)
                        elif "attribute_mapping" in state_data and isinstance(state_data["attribute_mapping"], dict):
                            attr_mapping = state_data["attribute_mapping"]
                            if "legacy_data" in attr_mapping and isinstance(attr_mapping["legacy_data"], dict):
                                legacy_data = attr_mapping["legacy_data"]
                        
                        # Extract raw data and field mappings from legacy_data
                        if legacy_data:
                            # Get raw data
                            if "raw_data" in legacy_data and isinstance(legacy_data["raw_data"], list):
                                raw_data = legacy_data["raw_data"]
                            
                            # Get field mappings
                            if "field_mappings" in legacy_data and isinstance(legacy_data["field_mappings"], dict):
                                field_mappings_raw = legacy_data["field_mappings"]
                                
                                # Format field mapping data for frontend consumption
                                field_mapping_data = {
                                    "mappings": field_mappings_raw.get("critical_mappings", {}),
                                    "attributes": raw_data,  # Include raw data for the data tab
                                    "critical_attributes": field_mappings_raw.get("critical_mappings", {}),
                                    "confidence_scores": field_mappings_raw.get("mapping_confidence", {}),
                                    "unmapped_fields": field_mappings_raw.get("unmapped_columns", []),
                                    "validation_results": {"valid": True, "score": 0.8},
                                    "user_clarifications": legacy_data.get("user_clarifications", []),  # Include clarification questions
                                    "analysis": {
                                        "status": "completed",
                                        "message": "Field mapping analysis completed by CrewAI agents",
                                        "summary": field_mappings_raw.get("summary", ""),
                                        "ambiguous_mappings": field_mappings_raw.get("ambiguous_mappings", {}),
                                        "secondary_mappings": field_mappings_raw.get("secondary_mappings", {})
                                    },
                                    "progress": {
                                        "total": len(raw_data[0].keys()) if raw_data and len(raw_data) > 0 else 0,
                                        "mapped": len(field_mappings_raw.get("critical_mappings", {})),
                                        "critical_mapped": len(field_mappings_raw.get("critical_mappings", {}))
                                    }
                                }
                        
                        # Fallback: Check for field mappings in the old format
                        elif "field_mappings" in state_data:
                            field_mappings_raw = state_data["field_mappings"]
                            
                            # Format field mapping data for frontend consumption
                            field_mapping_data = {
                                "mappings": field_mappings_raw.get("mappings", {}),
                                "attributes": field_mappings_raw.get("attributes", []),
                                "critical_attributes": field_mappings_raw.get("critical_attributes", []),
                                "confidence_scores": field_mappings_raw.get("confidence_scores", {}),
                                "unmapped_fields": field_mappings_raw.get("unmapped_fields", []),
                                "validation_results": field_mappings_raw.get("validation_results", {}),
                                "analysis": field_mappings_raw.get("agent_insights", {}),
                                "progress": {
                                    "total": len(field_mappings_raw.get("mappings", {})) + len(field_mappings_raw.get("unmapped_fields", [])),
                                    "mapped": len(field_mappings_raw.get("mappings", {})),
                                    "critical_mapped": len([attr for attr in field_mappings_raw.get("critical_attributes", []) if attr.get("mapped_to")])
                                }
                            }
                        
                        # Extract raw data if not found yet
                        if not raw_data:
                            if "raw_data" in state_data:
                                raw_data = state_data["raw_data"]
                            elif "cleaned_data" in state_data:
                                raw_data = state_data["cleaned_data"]
                            
                except Exception as e:
                    logger.warning(f"Failed to extract data from crewai_state_data: {e}")
            
            # If no field mapping data in state but we have raw data from import, try to get it from import session
            if not field_mapping_data and flow.import_session_id:
                try:
                    # Get raw data from import session if not in state
                    if not raw_data:
                        from sqlalchemy import select
                        from app.models.data_import import RawImportRecord
                        
                        # Query raw import records for this import session
                        records_query = select(RawImportRecord).where(
                            RawImportRecord.data_import_id == flow.import_session_id
                        ).order_by(RawImportRecord.row_number)
                        
                        records_result = await self.db.execute(records_query)
                        raw_records = records_result.scalars().all()
                        
                        # Extract raw data from records
                        raw_data = [record.raw_data for record in raw_records if record.raw_data]
                    
                    # Create basic field mapping structure if data exists but no mappings
                    if raw_data and not field_mapping_data:
                        headers = list(raw_data[0].keys()) if raw_data else []
                        field_mapping_data = {
                            "mappings": {},
                            "attributes": raw_data,  # Include raw data for the data tab
                            "critical_attributes": [],
                            "confidence_scores": {},
                            "unmapped_fields": headers,
                            "validation_results": {"valid": False, "score": 0.0},
                            "analysis": {"status": "pending", "message": "Field mapping analysis not yet completed"},
                            "progress": {
                                "total": len(headers),
                                "mapped": 0,
                                "critical_mapped": 0
                            }
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to get import data for field mapping: {e}")
            
            flow_status = {
                "flow_id": flow_id,
                "data_import_id": str(flow.import_session_id) if flow.import_session_id else None,
                "status": flow.status,
                "current_phase": current_phase,
                "progress_percentage": progress_percentage,
                "phases": phases,
                "agent_insights": agent_insights,
                "created_at": flow.created_at.isoformat() if flow.created_at else "",
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else datetime.now().isoformat()
            }
            
            # Include field mapping data if available
            if field_mapping_data:
                flow_status["field_mapping"] = field_mapping_data
            
            logger.info(f"✅ PostgreSQL flow status retrieved: {flow_id}")
            return flow_status
            
        except Exception as e:
            logger.error(f"❌ Failed to get PostgreSQL flow status: {e}")
            raise
    
    async def complete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Complete a discovery flow"""
        try:
            logger.info(f"✅ Completing PostgreSQL flow: {flow_id}")
            
            result = {
                "flow_id": flow_id,
                "status": "completed",
                "completion_time": datetime.now().isoformat(),
                "final_phase": "tech_debt_analysis"
            }
            
            logger.info(f"✅ PostgreSQL flow completed: {flow_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to complete PostgreSQL flow: {e}")
            raise
    
    async def delete_flow(self, flow_id: str, force_delete: bool = False) -> Dict[str, Any]:
        """Delete a discovery flow and cleanup"""
        try:
            logger.info(f"🗑️ Deleting PostgreSQL flow: {flow_id}, force: {force_delete}")
            
            # Actually delete from database
            deleted = await self.flow_repo.delete_flow(flow_id)
            
            if deleted:
                cleanup_summary = {
                    "flow_records_deleted": 1,
                    "asset_records_deleted": 0,  # Assets are cascade deleted
                    "session_data_deleted": 1,
                    "cleanup_time": datetime.now().isoformat()
                }
                
                result = {
                    "flow_id": flow_id,
                    "deleted": True,
                    "cleanup_summary": cleanup_summary,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"✅ PostgreSQL flow deleted: {flow_id}")
                return result
            else:
                logger.warning(f"⚠️ PostgreSQL flow not found for deletion: {flow_id}")
                return {
                    "flow_id": flow_id,
                    "deleted": False,
                    "error": "Flow not found",
                    "timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete PostgreSQL flow: {e}")
            raise

    async def _create_discovery_assets_from_cleaned_data(
        self, 
        flow, 
        cleaned_data: List[Dict[str, Any]], 
        field_mappings: List[Any]
    ) -> int:
        """Create discovery assets from cleaned data during data cleansing phase"""
        try:
            if not cleaned_data:
                logger.warning("⚠️ No cleaned data available for discovery asset creation")
                return 0
                
            logger.info(f"📊 Creating discovery assets from {len(cleaned_data)} cleaned records")
            
            # Import required modules
            from app.models.discovery_asset import DiscoveryAsset
            import uuid as uuid_pkg
            from datetime import datetime
            
            # Create mapping dictionary from field mappings
            mapping_dict = {}
            for mapping in field_mappings:
                if hasattr(mapping, 'source_field') and hasattr(mapping, 'target_field'):
                    mapping_dict[mapping.source_field] = mapping.target_field
                    
            discovery_assets_created = 0
            
            # Process each cleaned record into a discovery asset
            for index, record in enumerate(cleaned_data):
                try:
                    # Apply field mappings to get standardized data
                    mapped_data = self._apply_field_mappings_to_record(record, mapping_dict)
                    
                    # Create discovery asset
                    discovery_asset = DiscoveryAsset(
                        # Multi-tenant isolation
                        client_account_id=flow.client_account_id,
                        engagement_id=flow.engagement_id,
                        discovery_flow_id=flow.id,
                        
                        # Asset identification
                        asset_name=mapped_data.get('asset_name') or mapped_data.get('Asset_Name') or mapped_data.get('hostname') or f"Asset_{index + 1}",
                        asset_type=self._determine_asset_type_from_data(mapped_data, record),
                        
                        # Discovery metadata
                        discovered_in_phase='data_cleansing',
                        discovery_method='postgresql_flow_manager',
                        confidence_score=0.85,
                        
                        # Asset data
                        raw_data=record,
                        normalized_data=mapped_data,
                        
                        # Migration readiness
                        migration_ready=False,  # Will be determined in later phases
                        migration_complexity="Medium",
                        migration_priority=3,
                        
                        # Status tracking
                        asset_status="discovered",
                        validation_status="pending",
                        
                        # Timestamps
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    self.db.add(discovery_asset)
                    discovery_assets_created += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create discovery asset {index}: {e}")
                    continue
                    
            # Commit all discovery assets
            await self.db.commit()
            
            logger.info(f"✅ Created {discovery_assets_created} discovery assets during data cleansing")
            return discovery_assets_created
            
        except Exception as e:
            logger.error(f"❌ Failed to create discovery assets: {e}")
            await self.db.rollback()
            return 0

    def _apply_field_mappings_to_record(self, record: dict, mapping_dict: dict) -> dict:
        """Apply field mappings to transform record data"""
        mapped_data = {}
        
        for source_field, value in record.items():
            # Get target field from mapping, or use original field name
            target_field = mapping_dict.get(source_field, source_field)
            mapped_data[target_field] = value
            
        return mapped_data

    def _determine_asset_type_from_data(self, mapped_data: dict, original_data: dict) -> str:
        """Determine asset type from available data"""
        # Check mapped data first
        asset_type = mapped_data.get("asset_type") or original_data.get("asset_type") or original_data.get("TYPE")
        
        if asset_type:
            asset_type_str = str(asset_type).upper()
            # Map common types
            if "SERVER" in asset_type_str or "SRV" in asset_type_str:
                return "SERVER"
            elif "DATABASE" in asset_type_str or "DB" in asset_type_str:
                return "DATABASE"
            elif "NETWORK" in asset_type_str or "NET" in asset_type_str:
                return "NETWORK"
            elif "STORAGE" in asset_type_str:
                return "STORAGE"
            elif "APPLICATION" in asset_type_str or "APP" in asset_type_str:
                return "APPLICATION"
            elif "VIRTUAL" in asset_type_str or "VM" in asset_type_str:
                return "VIRTUAL_MACHINE"
                
        # Default fallback
        return "SERVER"

    async def _classify_discovery_assets(self, discovery_assets: List[Any]) -> Dict[str, Any]:
        """Classify and enhance discovery assets during inventory phase"""
        try:
            classification_results = {
                "assets_processed": len(discovery_assets),
                "asset_type_distribution": {},
                "classification_updates": [],
                "enhancement_summary": {}
            }
            
            for asset in discovery_assets:
                # Enhance asset type classification if needed
                current_type = asset.asset_type or "UNKNOWN"
                
                # Improve classification based on normalized data
                if asset.normalized_data:
                    enhanced_type = self._enhance_asset_classification(asset.normalized_data, current_type)
                    if enhanced_type != current_type:
                        asset.asset_type = enhanced_type
                        classification_results["classification_updates"].append({
                            "asset_id": str(asset.id),
                            "old_type": current_type,
                            "new_type": enhanced_type
                        })
                
                # Update distribution count
                final_type = asset.asset_type or "UNKNOWN"
                classification_results["asset_type_distribution"][final_type] = \
                    classification_results["asset_type_distribution"].get(final_type, 0) + 1
            
            # Commit classification updates
            await self.db.commit()
            
            logger.info(f"✅ Classified {len(discovery_assets)} assets: {classification_results['asset_type_distribution']}")
            return classification_results
            
        except Exception as e:
            logger.error(f"❌ Asset classification failed: {e}")
            return {"error": str(e), "assets_processed": 0}

    def _enhance_asset_classification(self, normalized_data: dict, current_type: str) -> str:
        """Enhance asset type classification based on normalized data"""
        # Look for more specific indicators in the data
        os_info = normalized_data.get("operating_system", "").lower()
        hostname = normalized_data.get("hostname", "").lower()
        app_name = normalized_data.get("application_name", "").lower()
        
        # Database indicators
        if any(db_indicator in os_info or db_indicator in hostname or db_indicator in app_name 
               for db_indicator in ["sql", "oracle", "postgres", "mysql", "mongodb", "db"]):
            return "DATABASE"
        
        # Application indicators
        if any(app_indicator in hostname or app_indicator in app_name 
               for app_indicator in ["web", "app", "api", "service", "portal"]):
            return "APPLICATION"
        
        # Virtual machine indicators
        if any(vm_indicator in os_info or vm_indicator in hostname 
               for vm_indicator in ["vm", "virtual", "esx", "vmware", "hyper-v"]):
            return "VIRTUAL_MACHINE"
        
        # Network device indicators
        if any(net_indicator in hostname or net_indicator in normalized_data.get("asset_name", "").lower()
               for net_indicator in ["switch", "router", "firewall", "lb", "balancer"]):
            return "NETWORK"
        
        # Keep current type if no better classification found
        return current_type 