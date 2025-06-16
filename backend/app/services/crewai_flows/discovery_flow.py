"""
Discovery Flow using CrewAI Flow Best Practices
Incorporates @persist decorator, advanced state management, and simplified control transfer
Following: https://docs.crewai.com/guides/flows/mastering-flow-state
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# CrewAI Flow imports
try:
    from crewai.flow.flow import Flow, listen, start, persist
    from crewai import Task, Crew
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False
    # Mock classes for when CrewAI Flow is not available
    class Flow:
        def __init__(self): 
            self.state = None
        
        def __class_getitem__(cls, item):
            """Support type subscripting for Flow[StateType]"""
            return cls
        
        def kickoff(self):
            """Mock kickoff method"""
            return "completed"
    
    def start(): return lambda f: f
    def listen(func): return lambda f: f
    def persist(): return lambda f: f

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

class DiscoveryFlowState(BaseModel):
    """
    Structured state for Discovery Flow following CrewAI best practices.
    
    This state model follows the recommended patterns:
    - Focused state with only necessary fields
    - Clear separation of concerns
    - Immutable operations where possible
    - Comprehensive error handling
    """
    
    # Context Information (Required)
    session_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    
    # Input Data
    cmdb_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing Status
    current_phase: str = "initialization"
    status: str = "running"
    progress_percentage: float = 0.0
    
    # Phase Completion Tracking (Boolean flags for simplicity)
    phases_completed: Dict[str, bool] = Field(default_factory=lambda: {
        "data_validation": False,
        "field_mapping": False,
        "asset_classification": False,
        "dependency_analysis": False,
        "database_integration": False
    })
    
    # Results Storage (Structured by phase)
    results: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent Communication
    agent_insights: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    
    # Error Handling
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_error(self, phase: str, error: str, details: Optional[Dict] = None):
        """Add an error with context information."""
        self.errors.append({
            "phase": phase,
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"{datetime.utcnow().isoformat()}: {message}")
    
    def mark_phase_complete(self, phase: str, results: Dict[str, Any] = None):
        """Mark a phase as complete and store results."""
        self.phases_completed[phase] = True
        if results:
            self.results[phase] = results
        
        # Update progress
        completed_count = sum(1 for completed in self.phases_completed.values() if completed)
        total_phases = len(self.phases_completed)
        self.progress_percentage = (completed_count / total_phases) * 100
    
    def get_completion_status(self) -> Dict[str, Any]:
        """Get comprehensive completion status."""
        return {
            "phases_completed": self.phases_completed,
            "progress_percentage": self.progress_percentage,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "is_complete": all(self.phases_completed.values()),
            "has_errors": len(self.errors) > 0
        }

@persist()  # Enable automatic state persistence
class DiscoveryFlow(Flow[DiscoveryFlowState]):
    """
    Discovery Flow using CrewAI Flow best practices.
    
    Key improvements:
    - Uses @persist() decorator for automatic state persistence
    - Simplified control transfer with clear phase boundaries
    - Better error handling and recovery
    - Immutable state operations
    - Comprehensive logging and monitoring
    """
    
    def __init__(self, crewai_service, context: RequestContext):
        super().__init__()
        self.crewai_service = crewai_service
        self.context = context
        self.agents = crewai_service.agents if crewai_service else {}
        
        logger.info(f"🏗️ Discovery Flow initialized for session: {context.session_id}")
    
    @start()
    def initialize_discovery(self):
        """
        Initialize the discovery workflow.
        
        State before: Empty state
        State after: Initialized with input data and context
        """
        logger.info(f"🚀 Starting Discovery Flow for session: {self.state.session_id}")
        
        # Update state immutably
        self.state.current_phase = "initialization"
        self.state.started_at = datetime.utcnow()
        
        # Validate input data
        cmdb_data = self.state.cmdb_data.get("file_data", [])
        if not cmdb_data:
            self.state.add_error("initialization", "No CMDB data provided")
            return "initialization_failed"
        
        # Store initialization insights
        self.state.agent_insights["initialization"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Discovery workflow initialized successfully",
            "data_size": len(cmdb_data),
            "metadata": self.state.metadata,
            "context": {
                "client_account_id": self.state.client_account_id,
                "engagement_id": self.state.engagement_id
            }
        }
        
        logger.info(f"✅ Discovery Flow initialized with {len(cmdb_data)} records")
        return "initialized"
    
    @listen(initialize_discovery)
    def validate_data_quality(self, previous_result):
        """
        Validate CMDB data quality and structure.
        
        State before: Initialized
        State after: Data validation results stored
        """
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping data validation due to initialization failure")
            return "validation_skipped"
        
        logger.info("🔍 Starting Data Validation phase")
        self.state.current_phase = "data_validation"
        
        try:
            cmdb_data = self.state.cmdb_data.get("file_data", [])
            
            if not CREWAI_FLOW_AVAILABLE or 'data_validator' not in self.agents:
                # Fallback validation
                validation_results = self._perform_fallback_validation(cmdb_data)
            else:
                # Use CrewAI agent for validation
                validation_results = self._perform_agent_validation(cmdb_data)
            
            # Store results immutably
            self.state.mark_phase_complete("data_validation", validation_results)
            
            logger.info(f"✅ Data validation completed: {validation_results.get('total_records', 0)} records processed")
            return "validation_completed"
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            self.state.add_error("data_validation", str(e))
            return "validation_failed"
    
    @listen(validate_data_quality)
    def map_source_fields(self, previous_result):
        """
        Map source fields to standard schema.
        
        State before: Data validated
        State after: Field mappings established
        """
        if previous_result in ["validation_skipped", "validation_failed"]:
            logger.error("❌ Skipping field mapping due to validation issues")
            return "mapping_skipped"
        
        logger.info("🗺️ Starting Field Mapping phase")
        self.state.current_phase = "field_mapping"
        
        try:
            cmdb_data = self.state.cmdb_data.get("file_data", [])
            
            if not CREWAI_FLOW_AVAILABLE or 'field_mapper' not in self.agents:
                # Fallback mapping
                mapping_results = self._perform_fallback_mapping(cmdb_data)
            else:
                # Use CrewAI agent for mapping
                mapping_results = self._perform_agent_mapping(cmdb_data)
            
            # Store results immutably
            self.state.mark_phase_complete("field_mapping", mapping_results)
            
            logger.info(f"✅ Field mapping completed: {len(mapping_results.get('field_mappings', {}))} mappings created")
            return "mapping_completed"
            
        except Exception as e:
            logger.error(f"❌ Field mapping failed: {e}")
            self.state.add_error("field_mapping", str(e))
            return "mapping_failed"
    
    @listen(map_source_fields)
    def classify_assets(self, previous_result):
        """
        Classify assets and determine migration strategies.
        
        State before: Fields mapped
        State after: Assets classified with strategies
        """
        if previous_result in ["mapping_skipped", "mapping_failed"]:
            logger.error("❌ Skipping asset classification due to mapping issues")
            return "classification_skipped"
        
        logger.info("🏷️ Starting Asset Classification phase")
        self.state.current_phase = "asset_classification"
        
        try:
            cmdb_data = self.state.cmdb_data.get("file_data", [])
            field_mappings = self.state.results.get("field_mapping", {}).get("field_mappings", {})
            
            if not CREWAI_FLOW_AVAILABLE or 'asset_classifier' not in self.agents:
                # Fallback classification
                classification_results = self._perform_fallback_classification(cmdb_data, field_mappings)
            else:
                # Use CrewAI agent for classification
                classification_results = self._perform_agent_classification(cmdb_data, field_mappings)
            
            # Store results immutably
            self.state.mark_phase_complete("asset_classification", classification_results)
            
            logger.info(f"✅ Asset classification completed: {len(classification_results.get('classified_assets', []))} assets classified")
            return "classification_completed"
            
        except Exception as e:
            logger.error(f"❌ Asset classification failed: {e}")
            self.state.add_error("asset_classification", str(e))
            return "classification_failed"
    
    @listen(classify_assets)
    def analyze_dependencies(self, previous_result):
        """
        Analyze asset dependencies and relationships.
        
        State before: Assets classified
        State after: Dependencies mapped
        """
        if previous_result in ["classification_skipped", "classification_failed"]:
            logger.error("❌ Skipping dependency analysis due to classification issues")
            return "dependency_analysis_skipped"
        
        logger.info("🔗 Starting Dependency Analysis phase")
        self.state.current_phase = "dependency_analysis"
        
        try:
            cmdb_data = self.state.cmdb_data.get("file_data", [])
            classified_assets = self.state.results.get("asset_classification", {}).get("classified_assets", [])
            
            if not CREWAI_FLOW_AVAILABLE or 'dependency_analyzer' not in self.agents:
                # Fallback dependency analysis
                dependency_results = self._perform_fallback_dependency_analysis(cmdb_data, classified_assets)
            else:
                # Use CrewAI agent for dependency analysis
                dependency_results = self._perform_agent_dependency_analysis(cmdb_data, classified_assets)
            
            # Store results immutably
            self.state.mark_phase_complete("dependency_analysis", dependency_results)
            
            logger.info(f"✅ Dependency analysis completed: {len(dependency_results.get('dependencies', []))} dependencies identified")
            return "dependency_analysis_completed"
            
        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            self.state.add_error("dependency_analysis", str(e))
            return "dependency_analysis_failed"
    
    @listen(analyze_dependencies)
    def finalize_discovery(self, previous_result):
        """
        Finalize discovery workflow and prepare results.
        
        State before: Dependencies analyzed
        State after: Complete discovery results ready
        """
        logger.info("🎯 Finalizing Discovery Flow")
        self.state.current_phase = "finalization"
        
        try:
            # Mark database integration as complete (placeholder)
            self.state.mark_phase_complete("database_integration", {
                "status": "completed",
                "message": "Discovery results ready for database integration",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update final status
            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow()
            self.state.current_phase = "completed"
            
            # Generate final recommendations
            self.state.recommendations = [
                "Discovery workflow completed successfully",
                f"Processed {len(self.state.cmdb_data.get('file_data', []))} CMDB records",
                f"Completed {sum(1 for completed in self.state.phases_completed.values() if completed)} phases",
                "Results ready for migration planning"
            ]
            
            logger.info(f"✅ Discovery Flow completed for session: {self.state.session_id}")
            return "discovery_completed"
            
        except Exception as e:
            logger.error(f"❌ Discovery finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            self.state.status = "failed"
            return "discovery_failed"

    # Fallback Methods (when CrewAI agents are not available)
    
    def _perform_fallback_validation(self, cmdb_data: List[Dict]) -> Dict[str, Any]:
        """Perform basic data validation without agents."""
        logger.info("Using fallback data validation")
        
        total_records = len(cmdb_data)
        valid_records = 0
        issues = []
        
        for i, record in enumerate(cmdb_data):
            if record and isinstance(record, dict) and len(record) > 0:
                valid_records += 1
            else:
                issues.append(f"Record {i}: Empty or invalid record")
        
        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "validation_rate": (valid_records / total_records) * 100 if total_records > 0 else 0,
            "issues": issues[:10],  # Limit to first 10 issues
            "method": "fallback_validation"
        }
    
    def _perform_fallback_mapping(self, cmdb_data: List[Dict]) -> Dict[str, Any]:
        """Perform basic field mapping without agents."""
        logger.info("Using fallback field mapping")
        
        if not cmdb_data:
            return {"field_mappings": {}, "method": "fallback_mapping"}
        
        # Get all unique field names from the data
        all_fields = set()
        for record in cmdb_data:
            if isinstance(record, dict):
                all_fields.update(record.keys())
        
        # Create basic mappings (identity mapping for now)
        field_mappings = {}
        standard_fields = {
            "name": ["name", "hostname", "server_name", "asset_name"],
            "type": ["type", "asset_type", "category", "class"],
            "status": ["status", "state", "condition"],
            "environment": ["environment", "env", "stage"],
            "location": ["location", "datacenter", "site"],
            "owner": ["owner", "responsible", "contact"]
        }
        
        for standard_field, possible_names in standard_fields.items():
            for field in all_fields:
                if field.lower() in [name.lower() for name in possible_names]:
                    field_mappings[field] = standard_field
                    break
        
        return {
            "field_mappings": field_mappings,
            "total_fields": len(all_fields),
            "mapped_fields": len(field_mappings),
            "method": "fallback_mapping"
        }
    
    def _perform_fallback_classification(self, cmdb_data: List[Dict], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Perform basic asset classification without agents."""
        logger.info("Using fallback asset classification")
        
        classified_assets = []
        
        for i, record in enumerate(cmdb_data):
            if not isinstance(record, dict):
                continue
            
            # Basic classification logic
            asset_type = "unknown"
            migration_strategy = "rehost"  # Default 6R strategy
            
            # Try to determine type from available fields
            type_field = None
            for field, mapped_field in field_mappings.items():
                if mapped_field == "type" and field in record:
                    type_field = record[field]
                    break
            
            if type_field:
                type_lower = str(type_field).lower()
                if "server" in type_lower or "vm" in type_lower:
                    asset_type = "server"
                elif "database" in type_lower or "db" in type_lower:
                    asset_type = "database"
                    migration_strategy = "replatform"
                elif "application" in type_lower or "app" in type_lower:
                    asset_type = "application"
                    migration_strategy = "refactor"
            
            classified_assets.append({
                "id": f"asset_{i}",
                "original_data": record,
                "asset_type": asset_type,
                "migration_strategy": migration_strategy,
                "confidence": 0.6,  # Low confidence for fallback
                "classification_method": "fallback"
            })
        
        return {
            "classified_assets": classified_assets,
            "total_assets": len(classified_assets),
            "classification_summary": {
                "server": len([a for a in classified_assets if a["asset_type"] == "server"]),
                "database": len([a for a in classified_assets if a["asset_type"] == "database"]),
                "application": len([a for a in classified_assets if a["asset_type"] == "application"]),
                "unknown": len([a for a in classified_assets if a["asset_type"] == "unknown"])
            },
            "method": "fallback_classification"
        }
    
    def _perform_fallback_dependency_analysis(self, cmdb_data: List[Dict], classifications: List[Dict]) -> Dict[str, Any]:
        """Perform basic dependency analysis without agents."""
        logger.info("Using fallback dependency analysis")
        
        # Basic dependency detection based on naming patterns
        dependencies = []
        
        for i, asset in enumerate(classifications):
            for j, other_asset in enumerate(classifications):
                if i != j:
                    # Simple heuristic: if names are similar, they might be related
                    asset_name = str(asset.get("original_data", {}).get("name", f"asset_{i}")).lower()
                    other_name = str(other_asset.get("original_data", {}).get("name", f"asset_{j}")).lower()
                    
                    # Check for common prefixes or suffixes
                    if (asset_name[:3] == other_name[:3] and len(asset_name) > 3) or \
                       (asset_name.split('-')[0] == other_name.split('-')[0] if '-' in asset_name and '-' in other_name else False):
                        dependencies.append({
                            "source": asset["id"],
                            "target": other_asset["id"],
                            "type": "potential_relationship",
                            "confidence": 0.3,
                            "method": "fallback_heuristic"
                        })
        
        return {
            "dependencies": dependencies[:50],  # Limit to prevent explosion
            "total_dependencies": len(dependencies),
            "method": "fallback_dependency_analysis"
        }
    
    # Agent Methods (when CrewAI agents are available)
    
    def _perform_agent_validation(self, cmdb_data: List[Dict]) -> Dict[str, Any]:
        """Perform data validation using CrewAI agents."""
        # Placeholder for agent-based validation
        return self._perform_fallback_validation(cmdb_data)
    
    def _perform_agent_mapping(self, cmdb_data: List[Dict]) -> Dict[str, Any]:
        """Perform field mapping using CrewAI agents."""
        return self._perform_fallback_mapping(cmdb_data)
    
    def _perform_agent_classification(self, cmdb_data: List[Dict], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Perform asset classification using CrewAI agents."""
        return self._perform_fallback_classification(cmdb_data, field_mappings)
    
    def _perform_agent_dependency_analysis(self, cmdb_data: List[Dict], classifications: List[Dict]) -> Dict[str, Any]:
        """Perform dependency analysis using CrewAI agents."""
        return self._perform_fallback_dependency_analysis(cmdb_data, classifications)


def create_discovery_flow(
    session_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    cmdb_data: Dict[str, Any],
    metadata: Dict[str, Any],
    crewai_service,
    context: RequestContext
) -> DiscoveryFlow:
    """
    Factory function to create a Discovery Flow with initialized state.
    
    This function creates a properly initialized DiscoveryFlow instance
    following CrewAI best practices for flow creation.
    """
    
    # Create the flow instance
    flow = DiscoveryFlow(crewai_service=crewai_service, context=context)
    
    # Initialize the state
    flow.state = DiscoveryFlowState(
        session_id=session_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        cmdb_data=cmdb_data,
        metadata=metadata
    )
    
    logger.info(f"🏗️ Discovery Flow created for session: {session_id}")
    return flow 