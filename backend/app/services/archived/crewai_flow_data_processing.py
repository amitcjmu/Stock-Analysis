#!/usr/bin/env python3
"""
CrewAI Flow Data Processing Service
Implements proper CrewAI Flow state management for processing raw import data into applications and servers
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

# CrewAI Flow imports
try:
    from crewai.flow.flow import Flow, listen, start
    from pydantic import BaseModel, Field
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False
    # Create dummy classes for when CrewAI Flow is not available
    class Flow:
        pass
    class BaseModel:
        pass
    def start():
        return lambda x: x
    def listen(func):
        return lambda x: x
    def Field(**kwargs):
        return None

from app.models.asset import Asset
from app.models.data_import import RawImportRecord
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# CrewAI Flow State Model
class DataProcessingState(BaseModel):
    """Structured state for CrewAI Flow data processing."""
    # Input data
    import_session_id: str = ""
    total_raw_records: int = 0
    
    # Processing progress tracking
    current_step: int = 0
    total_steps: int = 4  # Analysis → Field Mapping → Asset Classification → CMDB Creation
    progress_percentage: float = 0.0
    
    # Data analysis results
    raw_records: List[Dict[str, Any]] = []
    analyzed_data: Dict[str, Any] = {}
    field_mappings: Dict[str, str] = {}
    
    # Asset classification results
    applications: List[Dict[str, Any]] = []
    servers: List[Dict[str, Any]] = []
    databases: List[Dict[str, Any]] = []
    other_assets: List[Dict[str, Any]] = []
    
    # Dependency relationships
    dependencies: List[Dict[str, Any]] = []
    
    # Processing results
    processed_assets: List[str] = []  # List of created asset IDs
    processing_errors: List[str] = []
    
    # Context information
    client_account_id: str = ""
    engagement_id: str = ""
    user_id: str = ""
    
    # Status tracking
    processing_status: str = "initialized"  # initialized → analyzing → mapping → classifying → creating → completed
    completed_at: Optional[datetime] = None


class CrewAIFlowDataProcessor(Flow[DataProcessingState]):
    """CrewAI Flow for processing raw import data with proper state management."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    @start()
    def initialize_processing(self, 
                            import_session_id: str,
                            client_account_id: str,
                            engagement_id: str,
                            user_id: str) -> str:
        """Initialize the data processing flow with proper state setup."""
        self.logger.info(f"🚀 Initializing CrewAI Flow data processing for session: {import_session_id}")
        
        # Initialize state
        self.state.import_session_id = import_session_id
        self.state.client_account_id = client_account_id
        self.state.engagement_id = engagement_id
        self.state.user_id = user_id
        self.state.current_step = 0
        self.state.processing_status = "initialized"
        
        self.update_progress()
        
        self.logger.info(f"Flow ID: {self.state.id}")
        return "Flow initialized successfully"
    
    def update_progress(self):
        """Helper method to calculate and update progress."""
        if self.state.total_steps > 0:
            self.state.progress_percentage = (self.state.current_step / self.state.total_steps) * 100
            self.logger.info(f"📊 Progress: {self.state.progress_percentage:.1f}% (Step {self.state.current_step}/{self.state.total_steps})")
    
    @listen(initialize_processing)
    async def analyze_raw_data(self, previous_result: str) -> str:
        """Step 1: Analyze raw import records and understand data structure."""
        self.logger.info("🔍 Step 1: Analyzing raw import data structure")
        self.state.processing_status = "analyzing"
        self.state.current_step = 1
        self.update_progress()
        
        try:
            # Load raw records from database
            async with AsyncSessionLocal() as session:
                raw_records_query = await session.execute(
                    select(RawImportRecord).where(
                        RawImportRecord.data_import_id == self.state.import_session_id
                    )
                )
                raw_records = raw_records_query.scalars().all()
                
                if not raw_records:
                    self.state.processing_errors.append("No raw records found for session")
                    return "No data to process"
                
                # Convert to state data
                self.state.total_raw_records = len(raw_records)
                self.state.raw_records = [record.raw_data for record in raw_records]
                
                # Analyze data structure
                self.state.analyzed_data = self._analyze_data_structure(self.state.raw_records)
                
                self.logger.info(f"✅ Analyzed {len(self.state.raw_records)} raw records")
                self.logger.info(f"📊 Data structure: {self.state.analyzed_data}")
                
                return f"Analyzed {len(self.state.raw_records)} records successfully"
                
        except Exception as e:
            error_msg = f"Error analyzing raw data: {e}"
            self.state.processing_errors.append(error_msg)
            self.logger.error(error_msg)
            return error_msg
    
    @listen(analyze_raw_data)
    async def perform_intelligent_field_mapping(self, previous_result: str) -> str:
        """Step 2: Use CrewAI agents for intelligent field mapping."""
        self.logger.info("🧠 Step 2: Performing intelligent field mapping with CrewAI agents")
        self.state.processing_status = "mapping"
        self.state.current_step = 2
        self.update_progress()
        
        try:
            # Use CrewAI agents for field mapping if available
            try:
                from app.services.crewai_flow_service import crewai_flow_service
                
                # Prepare data for CrewAI analysis
                cmdb_data = {
                    "headers": list(self.state.raw_records[0].keys()) if self.state.raw_records else [],
                    "sample_data": self.state.raw_records[:5],
                    "total_records": self.state.total_raw_records,
                    "data_structure": self.state.analyzed_data
                }
                
                # Run CrewAI field mapping
                flow_result = await crewai_flow_service.run_discovery_flow(cmdb_data)
                
                if flow_result.get("status") == "success":
                    self.state.field_mappings = flow_result.get("suggested_field_mappings", {})
                    self.logger.info(f"✨ CrewAI provided {len(self.state.field_mappings)} field mappings")
                else:
                    self.logger.warning("CrewAI flow failed, using fallback field mapping")
                    self.state.field_mappings = self._fallback_field_mapping()
                    
            except (ImportError, Exception) as e:
                self.logger.warning(f"CrewAI Flow not available ({e}), using fallback field mapping")
                self.state.field_mappings = self._fallback_field_mapping()
            
            return f"Field mapping completed with {len(self.state.field_mappings)} mappings"
            
        except Exception as e:
            error_msg = f"Error in field mapping: {e}"
            self.state.processing_errors.append(error_msg)
            self.logger.error(error_msg)
            return error_msg
    
    @listen(perform_intelligent_field_mapping)
    async def classify_assets_intelligently(self, previous_result: str) -> str:
        """Step 3: Classify assets into applications, servers, databases using intelligent analysis."""
        self.logger.info("🎯 Step 3: Classifying assets intelligently")
        self.state.processing_status = "classifying"
        self.state.current_step = 3
        self.update_progress()
        
        try:
            # Process each raw record and classify
            for i, raw_data in enumerate(self.state.raw_records):
                try:
                    asset_classification = self._classify_single_asset(raw_data, self.state.field_mappings)
                    asset_type = asset_classification["asset_type"]
                    
                    if asset_type == "application":
                        self.state.applications.append(asset_classification)
                    elif asset_type == "server":
                        self.state.servers.append(asset_classification)
                    elif asset_type == "database":
                        self.state.databases.append(asset_classification)
                    else:
                        self.state.other_assets.append(asset_classification)
                    
                    # Extract dependency relationships
                    dependencies = self._extract_dependencies(raw_data, asset_classification)
                    if dependencies:
                        self.state.dependencies.extend(dependencies)
                        
                except Exception as e:
                    self.state.processing_errors.append(f"Error classifying record {i}: {e}")
                    continue
            
            # Log classification results
            total_classified = len(self.state.applications) + len(self.state.servers) + len(self.state.databases) + len(self.state.other_assets)
            
            self.logger.info(f"✅ Asset Classification Results:")
            self.logger.info(f"   📱 Applications: {len(self.state.applications)}")
            self.logger.info(f"   🖥️  Servers: {len(self.state.servers)}")
            self.logger.info(f"   🗄️  Databases: {len(self.state.databases)}")
            self.logger.info(f"   📦 Other Assets: {len(self.state.other_assets)}")
            self.logger.info(f"   🔗 Dependencies: {len(self.state.dependencies)}")
            self.logger.info(f"   📊 Total Classified: {total_classified}/{self.state.total_raw_records}")
            
            return f"Classified {total_classified} assets successfully"
            
        except Exception as e:
            error_msg = f"Error in asset classification: {e}"
            self.state.processing_errors.append(error_msg)
            self.logger.error(error_msg)
            return error_msg
    
    @listen(classify_assets_intelligently)
    async def create_assets(self, previous_result: str) -> str:
        """Step 4: Create assets in database with proper relationships."""
        self.logger.info("💾 Step 4: Creating assets in database")
        self.state.processing_status = "creating"
        self.state.current_step = 4
        self.update_progress()
        
        try:
            async with AsyncSessionLocal() as session:
                # Create assets from all categories
                all_assets = (self.state.applications + self.state.servers + 
                            self.state.databases + self.state.other_assets)
                
                created_count = 0
                
                for asset_data in all_assets:
                    try:
                        # Create enhanced Asset with enriched data
                        asset = Asset(
                            client_account_id=self.state.client_account_id,
                            engagement_id=self.state.engagement_id,
                            
                            # Core identification
                            name=asset_data["name"],
                            hostname=asset_data.get("hostname"),
                            asset_type=asset_data["asset_type"],
                            asset_name=asset_data.get("name"),
                            
                            # Technical details
                            ip_address=asset_data.get("ip_address"),
                            operating_system=asset_data.get("operating_system"),
                            environment=asset_data.get("environment", "Unknown"),
                            
                            # Business information
                            business_owner=asset_data.get("business_owner"),
                            department=asset_data.get("department"),
                            technical_owner=asset_data.get("technical_owner"),
                            
                            # Migration and classification information
                            sixr_ready=asset_data.get("sixr_ready", "Pending Analysis"),
                            migration_complexity=asset_data.get("migration_complexity", "Unknown"),
                            intelligent_asset_type=asset_data.get("intelligent_asset_type"),
                            
                            # Enhanced metadata with AI insights
                            ai_recommendations={"classification_confidence": asset_data.get("confidence_score", 0.5)},
                            confidence_score=asset_data.get("confidence_score", 0.5),
                            ai_confidence_score=asset_data.get("confidence_score", 0.5),
                            
                            # Discovery and processing metadata
                            discovery_source="crewai_flow_processing",
                            discovery_method="agentic_classification",
                            discovered_at=datetime.utcnow(),
                            last_ai_analysis=datetime.utcnow(),
                            source_file=f"flow_session_{self.state.import_session_id}",
                            source_system="crewai_flow",
                            
                            # Status and workflow
                            status="discovered",
                            discovery_status="completed",
                            mapping_status="completed", 
                            cleanup_status="completed",
                            assessment_readiness="ready" if asset_data.get("confidence_score", 0) > 0.7 else "partial",
                            
                            # Audit fields
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            created_by=self.state.user_id
                        )
                        
                        session.add(asset)
                        await session.flush()
                        
                        self.state.processed_assets.append(str(asset.id))
                        created_count += 1
                        
                        self.logger.info(f"✅ Created enriched asset: {asset.name} (ID: {asset.id}) - Type: {asset.asset_type}")
                        
                        # Update corresponding raw record with detailed processing notes
                        raw_record_query = await session.execute(
                            select(RawImportRecord).where(
                                and_(
                                    RawImportRecord.data_import_id == self.state.import_session_id,
                                    RawImportRecord.raw_data == asset_data["raw_data"]
                                )
                            )
                        )
                        raw_record = raw_record_query.scalar_one_or_none()
                        
                        if raw_record:
                            raw_record.asset_id = asset.id
                            raw_record.is_processed = True
                            raw_record.processed_at = datetime.utcnow()
                            raw_record.processing_notes = f"Processed by CrewAI Flow - Classified as {asset_data['asset_type']} with {asset_data.get('confidence_score', 0):.2f} confidence. Enriched with AI insights and field mapping."
                        
                    except Exception as e:
                        error_msg = f"Error creating enriched asset {asset_data.get('name', 'unknown')}: {e}"
                        self.state.processing_errors.append(error_msg)
                        self.logger.error(error_msg)
                        continue
                
                # Commit all changes
                await session.commit()
                
                # Complete the flow
                self.state.processing_status = "completed"
                self.state.completed_at = datetime.utcnow()
                self.update_progress()
                
                self.logger.info(f"✅ CrewAI Flow completed successfully!")
                self.logger.info(f"   📊 Created {created_count} assets")
                self.logger.info(f"   📱 Applications: {len(self.state.applications)}")
                self.logger.info(f"   🖥️  Servers: {len(self.state.servers)}")
                self.logger.info(f"   🗄️  Databases: {len(self.state.databases)}")
                self.logger.info(f"   ⚠️  Errors: {len(self.state.processing_errors)}")
                
                return f"Successfully created {created_count} assets with proper classification"
                
        except Exception as e:
            error_msg = f"Error creating assets: {e}"
            self.state.processing_errors.append(error_msg)
            self.logger.error(error_msg)
            return error_msg
    
    def _analyze_data_structure(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure and patterns in raw data."""
        if not raw_records:
            return {"error": "No data to analyze"}
        
        # Get all field names
        all_fields = set()
        for record in raw_records:
            all_fields.update(record.keys())
        
        # Analyze field patterns
        analysis = {
            "total_records": len(raw_records),
            "total_fields": len(all_fields),
            "field_names": list(all_fields),
            "has_citype": any("citype" in field.lower() for field in all_fields),
            "has_related_ci": any("related" in field.lower() and "ci" in field.lower() for field in all_fields),
            "has_applications": False,
            "has_servers": False,
            "sample_values": {}
        }
        
        # Sample first few records for value analysis
        sample_record = raw_records[0] if raw_records else {}
        for field, value in sample_record.items():
            analysis["sample_values"][field] = str(value)[:50]  # Truncate long values
        
        # Check for application and server indicators
        for record in raw_records[:10]:  # Check first 10 records
            citype = str(record.get("CITYPE", record.get("citype", record.get("CI_TYPE", "")))).lower()
            if "application" in citype:
                analysis["has_applications"] = True
            if "server" in citype:
                analysis["has_servers"] = True
        
        return analysis
    
    def _fallback_field_mapping(self) -> Dict[str, str]:
        """Provide fallback field mapping when CrewAI is not available."""
        if not self.state.raw_records:
            return {}
        
        sample_record = self.state.raw_records[0]
        mappings = {}
        
        for field in sample_record.keys():
            field_lower = field.lower()
            
            # Map common CMDB fields
            if field_lower in ["ciid", "ci_id"]:
                mappings[field] = "asset_id"
            elif field_lower in ["citype", "ci_type", "type"]:
                mappings[field] = "asset_type"
            elif field_lower in ["name", "asset_name", "hostname"]:
                mappings[field] = "name"
            elif field_lower in ["environment", "env"]:
                mappings[field] = "environment"
            elif field_lower in ["ip_address", "ip"]:
                mappings[field] = "ip_address"
            elif field_lower in ["os", "operating_system"]:
                mappings[field] = "operating_system"
            elif field_lower in ["owner", "business_owner"]:
                mappings[field] = "business_owner"
            elif field_lower in ["location", "datacenter"]:
                mappings[field] = "location"
            elif field_lower in ["related_ci", "related_cis", "dependencies"]:
                mappings[field] = "dependencies"
            else:
                mappings[field] = field  # Keep original field name
        
        return mappings
    
    def _classify_single_asset(self, raw_data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Enhanced asset classification with AI intelligence and confidence scoring."""
        
        # Extract key identifiers
        citype = self._get_mapped_value(raw_data, "citype", field_mappings, "").lower()
        ciid = self._get_mapped_value(raw_data, "ciid", field_mappings, "")
        name = self._get_mapped_value(raw_data, "name", field_mappings, "")
        
        # Enhanced asset type determination with AI logic
        asset_type = "server"  # Default
        confidence_score = 0.5  # Default confidence
        classification_method = "pattern_analysis"
        intelligent_type = None
        
        # Primary classification based on CITYPE (most reliable)
        if citype:
            classification_method = "citype_analysis"
            if "application" in citype:
                asset_type = "application"
                confidence_score = 0.95
                intelligent_type = "business_application"
            elif "server" in citype:
                asset_type = "server"
                confidence_score = 0.95
                intelligent_type = "compute_server"
            elif "database" in citype:
                asset_type = "database"
                confidence_score = 0.95
                intelligent_type = "database_server"
            elif any(term in citype for term in ["network", "switch", "router", "firewall"]):
                asset_type = "network"
                confidence_score = 0.90
                intelligent_type = "network_infrastructure"
            elif any(term in citype for term in ["storage", "san", "nas"]):
                asset_type = "storage"
                confidence_score = 0.90
                intelligent_type = "storage_infrastructure"
        
        # Secondary classification using AI pattern analysis
        if not citype or confidence_score < 0.8:
            classification_method = "ai_pattern_analysis"
            # Analyze naming patterns
            combined_text = f"{name} {ciid}".lower()
            
            if any(pattern in combined_text for pattern in ["app", "application", "portal", "web", "api"]):
                asset_type = "application"
                confidence_score = 0.75
                intelligent_type = "application_service"
            elif any(pattern in combined_text for pattern in ["srv", "server", "host", "vm", "node"]):
                asset_type = "server"
                confidence_score = 0.80
                intelligent_type = "virtual_server" if "vm" in combined_text else "physical_server"
            elif any(pattern in combined_text for pattern in ["db", "database", "sql", "oracle", "mysql"]):
                asset_type = "database"
                confidence_score = 0.85
                intelligent_type = "database_engine"
        
        # Enhanced business and technical metadata extraction
        business_metadata = {
            "business_owner": self._get_mapped_value(raw_data, "business_owner", field_mappings),
            "technical_owner": self._get_mapped_value(raw_data, "technical_owner", field_mappings),
            "department": self._get_mapped_value(raw_data, "department", field_mappings),
            "environment": self._get_mapped_value(raw_data, "environment", field_mappings, "Unknown"),
            "criticality": self._determine_criticality(raw_data, field_mappings)
        }
        
        # AI-powered migration assessment
        migration_assessment = self._assess_migration_readiness(raw_data, asset_type, confidence_score)
        
        # Build comprehensive asset classification
        classification = {
            "asset_type": asset_type,
            "intelligent_asset_type": intelligent_type,
            "name": name or ciid or f"Asset_{ciid}",
            "asset_id": ciid,
            "hostname": self._get_mapped_value(raw_data, "hostname", field_mappings),
            "ip_address": self._get_mapped_value(raw_data, "ip_address", field_mappings),
            "environment": business_metadata["environment"],
            "operating_system": self._get_mapped_value(raw_data, "operating_system", field_mappings),
            
            # Business information
            "business_owner": business_metadata["business_owner"],
            "technical_owner": business_metadata["technical_owner"],
            "department": business_metadata["department"],
            "business_criticality": business_metadata["criticality"],
            
            # Migration and AI insights
            "sixr_ready": migration_assessment["sixr_ready"],
            "migration_complexity": migration_assessment["complexity"],
            "recommended_6r_strategy": migration_assessment["strategy"],
            "strategy_confidence": migration_assessment["strategy_confidence"],
            
            # Technical metadata
            "location": self._get_mapped_value(raw_data, "location", field_mappings),
            "raw_data": raw_data,
            
            # AI classification metadata
            "confidence_score": confidence_score,
            "classification_method": classification_method,
            "ai_insights": {
                "pattern_matches": self._get_pattern_matches(combined_text if 'combined_text' in locals() else ""),
                "enrichment_applied": True,
                "field_mappings_used": len(field_mappings),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return classification
    
    def _determine_criticality(self, raw_data: Dict[str, Any], field_mappings: Dict[str, str]) -> str:
        """Determine business criticality based on available data."""
        
        # Check for explicit criticality fields
        criticality_fields = ["criticality", "business_criticality", "importance", "priority"]
        for field in raw_data.keys():
            if any(crit in field.lower() for crit in criticality_fields):
                value = str(raw_data[field]).lower()
                if any(term in value for term in ["high", "critical", "production"]):
                    return "high"
                elif any(term in value for term in ["medium", "important"]):
                    return "medium"
                elif any(term in value for term in ["low", "test", "dev"]):
                    return "low"
        
        # Infer from environment
        environment = self._get_mapped_value(raw_data, "environment", field_mappings, "").lower()
        if environment in ["production", "prod"]:
            return "high"
        elif environment in ["staging", "uat", "pre-prod"]:
            return "medium"
        elif environment in ["development", "dev", "test"]:
            return "low"
        
        return "medium"  # Default
    
    def _assess_migration_readiness(self, raw_data: Dict[str, Any], asset_type: str, confidence: float) -> Dict[str, str]:
        """AI-powered migration readiness assessment."""
        
        # Base assessment on asset type and data completeness
        if confidence > 0.8:
            sixr_ready = "Ready for Assessment"
            complexity = "Medium"
        elif confidence > 0.6:
            sixr_ready = "Partially Ready"
            complexity = "Medium"
        else:
            sixr_ready = "Requires Analysis"
            complexity = "High"
        
        # Determine recommended strategy
        if asset_type == "application":
            strategy = "refactor"
            strategy_confidence = 0.7
        elif asset_type == "database":
            strategy = "replatform"
            strategy_confidence = 0.8
        else:  # server
            strategy = "rehost"
            strategy_confidence = 0.75
        
        return {
            "sixr_ready": sixr_ready,
            "complexity": complexity,
            "strategy": strategy,
            "strategy_confidence": strategy_confidence
        }
    
    def _get_pattern_matches(self, text: str) -> List[str]:
        """Get pattern matches for AI insights."""
        patterns = []
        if "app" in text:
            patterns.append("application_pattern")
        if "srv" in text or "server" in text:
            patterns.append("server_pattern")
        if "db" in text:
            patterns.append("database_pattern")
        return patterns
    
    def _extract_dependencies(self, raw_data: Dict[str, Any], asset_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dependency relationships from raw data."""
        dependencies = []
        
        # Check for RELATED CI field
        related_ci_fields = ["related_ci", "related_cis", "dependencies", "depends_on"]
        
        for field in raw_data.keys():
            if any(pattern in field.lower() for pattern in related_ci_fields):
                related_value = raw_data[field]
                if related_value and str(related_value).strip():
                    dependencies.append({
                        "source_asset": asset_classification["asset_id"],
                        "target_asset": str(related_value).strip(),
                        "relationship_type": "depends_on",
                        "source_field": field
                    })
        
        return dependencies
    
    def _get_mapped_value(self, raw_data: Dict[str, Any], field_type: str, field_mappings: Dict[str, str], default: Any = None) -> Any:
        """Get a value from raw data using field mappings."""
        
        # First check direct field mapping
        for source_field, mapped_field in field_mappings.items():
            if field_type.lower() in mapped_field.lower() and source_field in raw_data:
                return raw_data[source_field]
        
        # Then check common field name variations
        field_variations = {
            "citype": ["CITYPE", "citype", "CI_TYPE", "type", "asset_type"],
            "ciid": ["CIID", "ciid", "CI_ID", "asset_id", "id"],
            "name": ["NAME", "name", "asset_name", "hostname", "server_name"],
            "hostname": ["hostname", "server_name", "host_name", "computer_name"],
            "ip_address": ["ip_address", "IP_ADDRESS", "ip", "IP"],
            "environment": ["environment", "ENVIRONMENT", "env", "ENV"],
            "operating_system": ["operating_system", "OS", "os", "Operating System"],
            "business_owner": ["business_owner", "owner", "Owner", "Business Owner"],
            "department": ["department", "DEPARTMENT", "dept", "team"],
            "location": ["location", "LOCATION", "datacenter", "site"]
        }
        
        if field_type in field_variations:
            for variation in field_variations[field_type]:
                if variation in raw_data:
                    return raw_data[variation]
        
        return default


# Service wrapper for easy integration
class CrewAIFlowDataProcessingService:
    """Service wrapper for CrewAI Flow data processing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_import_session(self,
                                   import_session_id: str,
                                   client_account_id: str,
                                   engagement_id: str,
                                   user_id: str) -> Dict[str, Any]:
        """Process a data import session using CrewAI Flow."""
        
        if not CREWAI_FLOW_AVAILABLE:
            return await self._fallback_processing(import_session_id, client_account_id, engagement_id, user_id)
        
        try:
            # Create and run CrewAI Flow
            flow = CrewAIFlowDataProcessor()
            
            # Initialize flow with proper parameters - let the Flow handle state management
            result = flow.initialize_processing(
                import_session_id=import_session_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id
            )
            
            # Run through the flow steps manually with proper error handling
            try:
                # Step 1: Analyze raw data
                analyze_result = await flow.analyze_raw_data(result)
                self.logger.info(f"✅ Flow Step 1 Complete: {analyze_result}")
                
                # Step 2: Perform field mapping
                mapping_result = await flow.perform_intelligent_field_mapping(analyze_result)
                self.logger.info(f"✅ Flow Step 2 Complete: {mapping_result}")
                
                # Step 3: Classify assets
                classification_result = await flow.classify_assets_intelligently(mapping_result)
                self.logger.info(f"✅ Flow Step 3 Complete: {classification_result}")
                
                # Step 4: Create assets
                creation_result = await flow.create_assets(classification_result)
                self.logger.info(f"✅ Flow Step 4 Complete: {creation_result}")
                
                # Extract results from flow state
                return {
                    "status": "success",
                    "flow_id": getattr(flow.state, 'id', 'unknown'),
                    "processing_status": getattr(flow.state, 'processing_status', 'completed'),
                    "progress_percentage": getattr(flow.state, 'progress_percentage', 100.0),
                    "total_processed": len(getattr(flow.state, 'processed_assets', [])),
                    "classification_results": {
                        "applications": len(getattr(flow.state, 'applications', [])),
                        "servers": len(getattr(flow.state, 'servers', [])),
                        "databases": len(getattr(flow.state, 'databases', [])),
                        "other_assets": len(getattr(flow.state, 'other_assets', [])),
                        "dependencies": len(getattr(flow.state, 'dependencies', []))
                    },
                    "processed_asset_ids": getattr(flow.state, 'processed_assets', []),
                    "processing_errors": getattr(flow.state, 'processing_errors', []),
                    "field_mappings": getattr(flow.state, 'field_mappings', {}),
                    "crewai_flow_used": True,
                    "completed_at": getattr(flow.state, 'completed_at', None),
                    "detailed_message": f"CrewAI Flow processed {len(getattr(flow.state, 'processed_assets', []))} assets with intelligent classification and enrichment"
                }
                
            except Exception as flow_e:
                self.logger.error(f"CrewAI Flow steps failed: {flow_e}")
                self.logger.info("Falling back to non-CrewAI processing due to flow execution error")
                return await self._fallback_processing(import_session_id, client_account_id, engagement_id, user_id)
            
        except Exception as e:
            self.logger.error(f"CrewAI Flow processing failed: {e}")
            self.logger.info("Falling back to non-CrewAI processing due to initialization error")
            return await self._fallback_processing(import_session_id, client_account_id, engagement_id, user_id)
    
    async def _fallback_processing(self, import_session_id: str, client_account_id: str, engagement_id: str, user_id: str) -> Dict[str, Any]:
        """Fallback processing when CrewAI Flow is not available."""
        self.logger.warning("Using fallback processing - CrewAI Flow not available")
        
        # Basic processing without CrewAI Flow state management
        try:
            async with AsyncSessionLocal() as session:
                # Get raw records
                raw_records_query = await session.execute(
                    select(RawImportRecord).where(
                        RawImportRecord.data_import_id == import_session_id
                    )
                )
                raw_records = raw_records_query.scalars().all()
                
                processed_count = 0
                for record in raw_records:
                    if record.asset_id is not None:
                        continue  # Already processed
                    
                    # Simple asset creation
                    raw_data = record.raw_data
                    
                    asset = Asset(
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        name=raw_data.get("NAME", raw_data.get("name", f"Asset_{record.row_number}")),
                        hostname=raw_data.get("hostname"),
                        asset_type=raw_data.get("CITYPE", "server").lower(),
                        ip_address=raw_data.get("IP_ADDRESS"),
                        operating_system=raw_data.get("OS"),
                        environment=raw_data.get("ENVIRONMENT", "Unknown"),
                        discovery_source="fallback_cmdb_import",
                        discovery_method="basic_mapping",
                        discovered_at=datetime.utcnow(),
                        created_at=datetime.utcnow()
                    )
                    
                    session.add(asset)
                    await session.flush()
                    
                    record.asset_id = asset.id
                    record.is_processed = True
                    record.processed_at = datetime.utcnow()
                    record.processing_notes = f"Processed by fallback method (non-agentic) - CrewAI Flow was not available. Created basic asset with CITYPE: {raw_data.get('CITYPE', 'server')}"
                    
                    processed_count += 1
                
                await session.commit()
                
                return {
                    "status": "success",
                    "processing_status": "completed",
                    "total_processed": processed_count,
                    "crewai_flow_used": False,
                    "fallback_used": True
                }
                
        except Exception as e:
            self.logger.error(f"Fallback processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "crewai_flow_used": False,
                "fallback_used": True
            } 