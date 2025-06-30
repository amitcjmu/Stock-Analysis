"""
Unified Discovery Flow with proper CrewAI patterns
Phase 2: Event-driven flow using @start/@listen decorators
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from app.services.flows.base_flow import BaseDiscoveryFlow, BaseFlowState
from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai.flow.flow import Flow, start, listen
    CREWAI_FLOW_AVAILABLE = True
    logger.info("✅ CrewAI Flow imports successful")
except ImportError as e:
    logger.warning(f"CrewAI Flow not available: {e}")
    
    # Fallback implementations
    class Flow:
        def __init__(self): 
            self.state = None
        def __class_getitem__(cls, item):
            return cls
        def kickoff(self):
            return {}
    
    def listen(condition):
        def decorator(func):
            return func
        return decorator
    
    def start():
        def decorator(func):
            return func
        return decorator

# Import crew factory for agent orchestration
try:
    from app.services.crews.factory import CrewFactory
    CREW_FACTORY_AVAILABLE = True
    logger.info("✅ CrewFactory available")
except ImportError:
    logger.warning("CrewFactory not available - using fallback")
    CREW_FACTORY_AVAILABLE = False
    
    class CrewFactory:
        @staticmethod
        async def execute_crew(crew_type: str, inputs: Dict[str, Any]):
            return {"status": "fallback", "data": {}}


class DiscoveryFlowState(BaseFlowState):
    """Complete state for discovery flow"""
    # Data import info
    data_import_id: str = ""
    import_filename: str = ""
    total_records: int = 0
    
    # Phase-specific results
    field_mappings: Dict[str, Any] = {}
    cleansed_data: Dict[str, Any] = {}
    discovered_assets: List[Dict[str, Any]] = []
    dependencies: Dict[str, Any] = {}
    tech_debt_analysis: Dict[str, Any] = {}
    
    # Progress tracking
    progress_percentage: float = 0.0
    phase_timings: Dict[str, float] = {}
    
    # Raw data (for compatibility)
    raw_data: List[Dict[str, Any]] = []
    session_id: str = ""
    
    # Phase completion tracking
    phase_completion: Dict[str, bool] = {}
    
    # Agent results
    agent_confidences: Dict[str, float] = {}
    agent_insights: List[Dict[str, Any]] = []
    user_clarifications: List[Dict[str, Any]] = []
    
    # Status tracking
    status: str = "running"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    
    def add_error(self, phase: str, message: str):
        """Add error to tracking"""
        self.errors.append({
            "phase": phase, 
            "message": message, 
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_entry(self, message: str):
        """Add log entry"""
        logger.info(f"Flow {self.flow_id}: {message}")


class UnifiedDiscoveryFlow(BaseDiscoveryFlow):
    """
    Discovery flow with proper CrewAI patterns.
    Uses @start and @listen decorators for flow control.
    """
    
    @property
    def state_class(self):
        return DiscoveryFlowState
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize discovery flow"""
        super().__init__(db, context)
        
        # Initialize crew factory
        if CREW_FACTORY_AVAILABLE:
            self.crew_factory = CrewFactory()
        else:
            self.crew_factory = CrewFactory()  # Fallback
    
    @start()
    async def initialize_discovery(self, import_data: Dict[str, Any]) -> DiscoveryFlowState:
        """
        Start the discovery flow with data import.
        This is the entry point triggered by external call.
        """
        logger.info("Starting discovery flow initialization")
        
        # Create initial state
        self.state = DiscoveryFlowState(
            flow_id=import_data["flow_id"],
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            user_id=self.context.user_id,
            data_import_id=import_data["import_id"],
            import_filename=import_data["filename"],
            total_records=import_data["record_count"],
            current_phase="initialization",
            raw_data=import_data.get("raw_data", []),
            session_id=import_data.get("session_id", "")
        )
        
        # Save initial state
        await self.save_state(self.state)
        
        # Emit start event
        self.emit_event("flow_started", {
            "import_id": self.state.data_import_id,
            "filename": self.state.import_filename,
            "records": self.state.total_records
        })
        
        return self.state
    
    @listen(initialize_discovery)
    async def validate_and_analyze_data(self, initial_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Validate imported data and perform initial analysis.
        Triggered automatically after initialization.
        """
        logger.info(f"Starting data validation for flow {initial_state.flow_id}")
        
        self.state = initial_state
        self.state.current_phase = "data_validation"
        
        try:
            # Execute validation crew
            validation_result = await self.crew_factory.execute_crew(
                crew_type="data_validation",
                inputs={
                    "import_id": self.state.data_import_id,
                    "flow_id": self.state.flow_id,
                    "raw_data": self.state.raw_data
                }
            )
            
            # Update state with results
            self.state.metadata["validation_results"] = validation_result
            self.state.phases_completed.append("data_validation")
            self.state.phase_completion["data_validation"] = True
            self.state.progress_percentage = 10.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "data_validation",
                "status": validation_result.get("status", "unknown")
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "data_validation")
            raise
    
    @listen(validate_and_analyze_data)
    async def perform_field_mapping(self, validated_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Perform intelligent field mapping.
        Triggered after successful validation.
        """
        logger.info(f"Starting field mapping for flow {validated_state.flow_id}")
        
        self.state = validated_state
        self.state.current_phase = "field_mapping"
        
        try:
            # Get source schema from validation results
            validation_results = self.state.metadata.get("validation_results", {})
            source_schema = validation_results.get("schema", {})
            
            # Execute field mapping crew
            mapping_result = await self.crew_factory.execute_crew(
                crew_type="field_mapping",
                inputs={
                    "import_id": self.state.data_import_id,
                    "source_schema": source_schema,
                    "target_fields": await self._get_target_fields(),
                    "raw_data": self.state.raw_data
                }
            )
            
            # Update state with mappings
            self.state.field_mappings = mapping_result.get("mappings", {})
            self.state.phases_completed.append("field_mapping")
            self.state.phase_completion["field_mapping"] = True
            self.state.progress_percentage = 30.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "field_mapping",
                "mappings_created": len(self.state.field_mappings)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "field_mapping")
            raise
    
    @listen(perform_field_mapping)
    async def cleanse_data(self, mapped_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Cleanse data based on field mappings.
        Triggered after field mapping completion.
        """
        logger.info(f"Starting data cleansing for flow {mapped_state.flow_id}")
        
        self.state = mapped_state
        self.state.current_phase = "data_cleansing"
        
        try:
            # Execute data cleansing crew
            cleansing_result = await self.crew_factory.execute_crew(
                crew_type="data_cleansing",
                inputs={
                    "import_id": self.state.data_import_id,
                    "field_mappings": self.state.field_mappings,
                    "raw_data": self.state.raw_data
                }
            )
            
            # Update state
            self.state.cleansed_data = cleansing_result.get("cleansed_data", {})
            self.state.phases_completed.append("data_cleansing")
            self.state.phase_completion["data_cleansing"] = True
            self.state.progress_percentage = 50.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "data_cleansing",
                "records_cleansed": cleansing_result.get("records_processed", 0)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "data_cleansing")
            raise
    
    @listen(cleanse_data)
    async def build_asset_inventory(self, cleansed_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Build asset inventory from cleansed data.
        Triggered after data cleansing.
        """
        logger.info(f"Starting asset inventory for flow {cleansed_state.flow_id}")
        
        self.state = cleansed_state
        self.state.current_phase = "asset_inventory"
        
        try:
            # Execute asset inventory crew
            inventory_result = await self.crew_factory.execute_crew(
                crew_type="asset_inventory",
                inputs={
                    "import_id": self.state.data_import_id,
                    "cleansed_data": self.state.cleansed_data
                }
            )
            
            # Update state
            self.state.discovered_assets = inventory_result.get("assets", [])
            self.state.phases_completed.append("asset_inventory")
            self.state.phase_completion["asset_inventory"] = True
            self.state.progress_percentage = 70.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "asset_inventory",
                "assets_discovered": len(self.state.discovered_assets)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "asset_inventory")
            raise
    
    @listen(build_asset_inventory)
    async def analyze_dependencies(self, inventory_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Analyze dependencies between discovered assets.
        Triggered after asset inventory.
        """
        logger.info(f"Starting dependency analysis for flow {inventory_state.flow_id}")
        
        self.state = inventory_state
        self.state.current_phase = "dependency_analysis"
        
        try:
            # Execute dependency analysis crew
            dependency_result = await self.crew_factory.execute_crew(
                crew_type="dependency_analysis",
                inputs={
                    "assets": self.state.discovered_assets
                }
            )
            
            # Update state
            self.state.dependencies = dependency_result.get("dependencies", {})
            self.state.phases_completed.append("dependency_analysis")
            self.state.phase_completion["dependency_analysis"] = True
            self.state.progress_percentage = 90.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "dependency_analysis",
                "dependencies_found": dependency_result.get("total_dependencies", 0)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "dependency_analysis")
            raise
    
    @listen(analyze_dependencies)
    async def assess_technical_debt(self, analyzed_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Final phase: Assess technical debt and provide recommendations.
        Triggered after dependency analysis.
        """
        logger.info(f"Starting technical debt assessment for flow {analyzed_state.flow_id}")
        
        self.state = analyzed_state
        self.state.current_phase = "technical_debt"
        
        try:
            # Execute tech debt analysis crew
            tech_debt_result = await self.crew_factory.execute_crew(
                crew_type="tech_debt_analysis",
                inputs={
                    "assets": self.state.discovered_assets,
                    "dependencies": self.state.dependencies
                }
            )
            
            # Update state
            self.state.tech_debt_analysis = tech_debt_result
            self.state.phases_completed.append("technical_debt")
            self.state.phase_completion["technical_debt"] = True
            self.state.progress_percentage = 100.0
            self.state.current_phase = "completed"
            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow().isoformat()
            
            # Save final state
            await self.save_state(self.state)
            
            # Emit completion events
            self.emit_event("phase_completed", {
                "phase": "technical_debt",
                "recommendations": len(tech_debt_result.get("recommendations", []))
            })
            
            self.emit_event("flow_completed", {
                "flow_id": self.state.flow_id,
                "total_phases": len(self.state.phases_completed),
                "assets_discovered": len(self.state.discovered_assets)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "technical_debt")
            raise
    
    async def _get_target_fields(self) -> List[Dict[str, Any]]:
        """Get available target fields for mapping"""
        # TODO: Implement fetching from database
        return [
            {"name": "hostname", "type": "string", "required": True},
            {"name": "ip_address", "type": "string", "required": False},
            {"name": "operating_system", "type": "string", "required": False},
            {"name": "asset_type", "type": "string", "required": True},
            {"name": "environment", "type": "string", "required": False},
            {"name": "business_owner", "type": "string", "required": False}
        ]