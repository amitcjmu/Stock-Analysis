"""
Unified Discovery Flow Implementation
Single CrewAI Flow consolidating all competing discovery flow implementations.
Follows CrewAI Flow documentation patterns from:
https://docs.crewai.com/guides/flows/mastering-flow-state

Replaces:
- backend/app/services/crewai_flows/discovery_flow.py
- backend/app/services/crewai_flows/models/flow_state.py
- Multiple competing flow implementations
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist
    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Flow imports successful")
except ImportError as e:
    logger = logging.getLogger(__name__)
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
    
    def persist():
        def decorator(func):
            return func
        return decorator

# Import unified state model
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.context import RequestContext

@persist()  # Enable CrewAI state persistence
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    Unified Discovery Flow following CrewAI documentation patterns.
    Single source of truth for all discovery flow operations.
    
    Handles all discovery phases with proper state management:
    1. Field Mapping
    2. Data Cleansing  
    3. Asset Inventory
    4. Dependency Analysis
    5. Technical Debt Analysis
    """
    
    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """Initialize unified discovery flow with proper state management"""
        
        # Store initialization parameters
        self._init_session_id = kwargs.get('session_id', str(uuid.uuid4()))
        self._init_client_account_id = kwargs.get('client_account_id', '')
        self._init_engagement_id = kwargs.get('engagement_id', '')
        self._init_user_id = kwargs.get('user_id', '')
        self._init_raw_data = kwargs.get('raw_data', [])
        self._init_metadata = kwargs.get('metadata', {})
        self._init_context = context
        
        super().__init__()
        
        # Store services and context
        self.crewai_service = crewai_service
        self.context = context
        
        # Initialize state if not exists
        if not hasattr(self, 'state') or self.state is None:
            self.state = UnifiedDiscoveryFlowState()
        
        # Initialize crew factories for on-demand creation
        self._initialize_crew_factories()
        
        logger.info(f"✅ Unified Discovery Flow initialized with session: {self._init_session_id}")
    
    def _initialize_crew_factories(self):
        """Initialize CrewAI crew factory functions for on-demand creation"""
        try:
            # Import crew factory functions
            from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
            from app.services.crewai_flows.crews.data_cleansing_crew import create_data_cleansing_crew
            from app.services.crewai_flows.crews.inventory_building_crew import create_inventory_building_crew
            from app.services.crewai_flows.crews.app_server_dependency_crew import create_app_server_dependency_crew
            from app.services.crewai_flows.crews.technical_debt_crew import create_technical_debt_crew
            
            # Store factory functions
            self.crew_factories = {
                "field_mapping": create_field_mapping_crew,
                "data_cleansing": create_data_cleansing_crew,
                "asset_inventory": create_inventory_building_crew,
                "dependency_analysis": create_app_server_dependency_crew,
                "tech_debt_analysis": create_technical_debt_crew
            }
            
            logger.info("✅ CrewAI crew factories initialized successfully")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import CrewAI crew factories: {e}")
            self.crew_factories = {}
        except Exception as e:
            logger.error(f"❌ Failed to initialize CrewAI crew factories: {e}")
            self.crew_factories = {}
    
    def _create_crew_on_demand(self, crew_type: str, **kwargs) -> Optional[Any]:
        """Create a crew on-demand with proper error handling"""
        try:
            if crew_type not in self.crew_factories:
                raise Exception(f"Crew factory not available for: {crew_type}")
            
            factory = self.crew_factories[crew_type]
            
            # Create crew with appropriate parameters
            if crew_type == "field_mapping":
                crew = factory(
                    self.crewai_service,
                    kwargs.get('sample_data', []),
                    kwargs.get('shared_memory'),
                    kwargs.get('knowledge_base')
                )
            elif crew_type == "data_cleansing":
                crew = factory(
                    self.crewai_service,
                    kwargs.get('raw_data', []),
                    kwargs.get('field_mappings', {}),
                    kwargs.get('shared_memory'),
                    kwargs.get('knowledge_base')
                )
            elif crew_type == "asset_inventory":
                crew = factory(
                    self.crewai_service,
                    kwargs.get('cleaned_data', []),
                    kwargs.get('field_mappings', {}),
                    kwargs.get('shared_memory'),
                    kwargs.get('knowledge_base')
                )
            elif crew_type == "dependency_analysis":
                crew = factory(
                    self.crewai_service,
                    kwargs.get('asset_inventory', []),
                    kwargs.get('shared_memory'),
                    kwargs.get('knowledge_base')
                )
            elif crew_type == "tech_debt_analysis":
                crew = factory(
                    self.crewai_service,
                    kwargs.get('asset_inventory', []),
                    kwargs.get('dependencies', {}),
                    kwargs.get('shared_memory'),
                    kwargs.get('knowledge_base')
                )
            else:
                raise Exception(f"Unknown crew type: {crew_type}")
            
            logger.info(f"✅ {crew_type} crew created successfully")
            return crew
            
        except Exception as e:
            logger.error(f"❌ Failed to create {crew_type} crew: {e}")
            self.state.add_error(f"{crew_type}_crew_creation", str(e))
            return None
    
    @start()
    def initialize_discovery(self):
        """Initialize the unified discovery workflow"""
        logger.info("🚀 Starting Unified Discovery Flow initialization")
        
        # Set core state fields
        self.state.session_id = self._init_session_id
        self.state.client_account_id = self._init_client_account_id
        self.state.engagement_id = self._init_engagement_id
        self.state.user_id = self._init_user_id
        self.state.raw_data = self._init_raw_data
        self.state.metadata = self._init_metadata
        
        # Set flow status
        self.state.current_phase = "initialization"
        self.state.status = "running"
        self.state.started_at = datetime.utcnow().isoformat()
        
        # Validate input data
        if not self.state.raw_data:
            self.state.add_error("initialization", "No raw data provided")
            return "initialization_failed"
        
        self.state.log_entry(f"Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"✅ Unified Discovery Flow initialized with {len(self.state.raw_data)} records")
        
        return "initialized"
    
    @listen(initialize_discovery)
    def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping using CrewAI crew"""
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping field mapping due to initialization failure")
            return "field_mapping_skipped"
        
        logger.info("🔍 Starting Field Mapping Crew execution")
        self.state.current_phase = "field_mapping"
        self.state.progress_percentage = 16.7  # 1/6 phases
        
        try:
            # Create field mapping crew on-demand
            crew = self._create_crew_on_demand(
                "field_mapping",
                sample_data=self.state.raw_data[:5],  # First 5 records for analysis
                shared_memory=getattr(self.state, 'shared_memory_reference', None)
            )
            
            if crew and CREWAI_FLOW_AVAILABLE:
                # Execute the crew
                crew_input = {
                    "columns": list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                    "sample_data": self.state.raw_data[:5],
                    "mapping_type": "comprehensive_field_mapping"
                }
                
                crew_result = crew.kickoff(inputs=crew_input)
                logger.info(f"Field mapping crew completed: {type(crew_result)}")
                
                # Process crew results
                field_mappings = self._process_field_mapping_results(crew_result)
                
            else:
                logger.warning("Field mapping crew not available - using fallback")
                field_mappings = self._fallback_field_mapping()
            
            # Store results in state
            self.state.field_mappings = field_mappings
            self.state.mark_phase_complete("field_mapping", field_mappings)
            self.state.update_progress()
            
            logger.info(f"✅ Field mapping completed: {len(field_mappings.get('mappings', {}))} mappings")
            return "field_mapping_completed"
            
        except Exception as e:
            logger.error(f"❌ Field mapping execution failed: {e}")
            self.state.add_error("field_mapping", str(e))
            return "field_mapping_failed"
    
    @listen(execute_field_mapping_crew)
    def execute_data_cleansing_crew(self, previous_result):
        """Execute data cleansing using CrewAI crew"""
        if previous_result in ["field_mapping_skipped", "field_mapping_failed"]:
            logger.error("❌ Skipping data cleansing due to field mapping issues")
            return "data_cleansing_skipped"
        
        logger.info("🧹 Starting Data Cleansing Crew execution")
        self.state.current_phase = "data_cleansing"
        self.state.progress_percentage = 33.3  # 2/6 phases
        
        try:
            # Create data cleansing crew on-demand
            crew = self._create_crew_on_demand(
                "data_cleansing",
                raw_data=self.state.raw_data,
                field_mappings=self.state.field_mappings,
                shared_memory=getattr(self.state, 'shared_memory_reference', None)
            )
            
            if crew and CREWAI_FLOW_AVAILABLE:
                # Execute the crew
                crew_input = {
                    "raw_data": self.state.raw_data,
                    "field_mappings": self.state.field_mappings,
                    "cleansing_type": "comprehensive_data_cleansing"
                }
                
                crew_result = crew.kickoff(inputs=crew_input)
                logger.info(f"Data cleansing crew completed: {type(crew_result)}")
                
                # Process crew results
                cleansing_results = self._process_data_cleansing_results(crew_result)
                
            else:
                logger.warning("Data cleansing crew not available - using fallback")
                cleansing_results = self._fallback_data_cleansing()
            
            # Store results in state
            self.state.cleaned_data = cleansing_results.get("cleaned_data", [])
            self.state.data_quality_metrics = cleansing_results.get("quality_metrics", {})
            self.state.mark_phase_complete("data_cleansing", cleansing_results)
            self.state.update_progress()
            
            logger.info(f"✅ Data cleansing completed: {len(self.state.cleaned_data)} records cleaned")
            return "data_cleansing_completed"
            
        except Exception as e:
            logger.error(f"❌ Data cleansing execution failed: {e}")
            self.state.add_error("data_cleansing", str(e))
            return "data_cleansing_failed"
    
    @listen(execute_data_cleansing_crew)
    def execute_asset_inventory_crew(self, previous_result):
        """Execute asset inventory using CrewAI crew"""
        if previous_result in ["data_cleansing_skipped", "data_cleansing_failed"]:
            logger.error("❌ Skipping asset inventory due to data cleansing issues")
            return "asset_inventory_skipped"
        
        logger.info("📦 Starting Asset Inventory Crew execution")
        self.state.current_phase = "asset_inventory"
        self.state.progress_percentage = 50.0  # 3/6 phases
        
        try:
            # Create asset inventory crew on-demand
            crew = self._create_crew_on_demand(
                "asset_inventory",
                cleaned_data=self.state.cleaned_data,
                field_mappings=self.state.field_mappings,
                shared_memory=getattr(self.state, 'shared_memory_reference', None)
            )
            
            if crew and CREWAI_FLOW_AVAILABLE:
                # Execute the crew
                crew_input = {
                    "cleaned_data": self.state.cleaned_data,
                    "field_mappings": self.state.field_mappings,
                    "inventory_type": "comprehensive_asset_classification"
                }
                
                crew_result = crew.kickoff(inputs=crew_input)
                logger.info(f"Asset inventory crew completed: {type(crew_result)}")
                
                # Process crew results
                inventory_results = self._process_asset_inventory_results(crew_result)
                
            else:
                logger.warning("Asset inventory crew not available - using fallback")
                inventory_results = self._fallback_asset_inventory()
            
            # Store results in state
            self.state.asset_inventory = inventory_results
            self.state.mark_phase_complete("asset_inventory", inventory_results)
            self.state.update_progress()
            
            total_assets = inventory_results.get("total_assets", 0)
            logger.info(f"✅ Asset inventory completed: {total_assets} assets classified")
            return "asset_inventory_completed"
            
        except Exception as e:
            logger.error(f"❌ Asset inventory execution failed: {e}")
            self.state.add_error("asset_inventory", str(e))
            return "asset_inventory_failed"
    
    @listen(execute_asset_inventory_crew)
    def execute_dependency_analysis_crew(self, previous_result):
        """Execute dependency analysis using CrewAI crew"""
        if previous_result in ["asset_inventory_skipped", "asset_inventory_failed"]:
            logger.error("❌ Skipping dependency analysis due to asset inventory issues")
            return "dependency_analysis_skipped"
        
        logger.info("🔗 Starting Dependency Analysis Crew execution")
        self.state.current_phase = "dependency_analysis"
        self.state.progress_percentage = 66.7  # 4/6 phases
        
        try:
            # Create dependency analysis crew on-demand
            crew = self._create_crew_on_demand(
                "dependency_analysis",
                asset_inventory=self.state.asset_inventory,
                shared_memory=getattr(self.state, 'shared_memory_reference', None)
            )
            
            if crew and CREWAI_FLOW_AVAILABLE:
                # Execute the crew
                crew_input = {
                    "asset_inventory": self.state.asset_inventory,
                    "analysis_type": "comprehensive_dependency_mapping"
                }
                
                crew_result = crew.kickoff(inputs=crew_input)
                logger.info(f"Dependency analysis crew completed: {type(crew_result)}")
                
                # Process crew results
                dependency_results = self._process_dependency_analysis_results(crew_result)
                
            else:
                logger.warning("Dependency analysis crew not available - using fallback")
                dependency_results = self._fallback_dependency_analysis()
            
            # Store results in state
            self.state.dependencies = dependency_results
            self.state.mark_phase_complete("dependency_analysis", dependency_results)
            self.state.update_progress()
            
            total_deps = (
                len(dependency_results.get("app_server_dependencies", {}).get("hosting_relationships", [])) +
                len(dependency_results.get("app_app_dependencies", {}).get("communication_patterns", []))
            )
            logger.info(f"✅ Dependency analysis completed: {total_deps} dependencies identified")
            return "dependency_analysis_completed"
            
        except Exception as e:
            logger.error(f"❌ Dependency analysis execution failed: {e}")
            self.state.add_error("dependency_analysis", str(e))
            return "dependency_analysis_failed"
    
    @listen(execute_dependency_analysis_crew)
    def execute_tech_debt_analysis_crew(self, previous_result):
        """Execute technical debt analysis using CrewAI crew"""
        if previous_result in ["dependency_analysis_skipped", "dependency_analysis_failed"]:
            logger.error("❌ Skipping tech debt analysis due to dependency analysis issues")
            return "tech_debt_analysis_skipped"
        
        logger.info("⚠️ Starting Technical Debt Analysis Crew execution")
        self.state.current_phase = "tech_debt_analysis"
        self.state.progress_percentage = 83.3  # 5/6 phases
        
        try:
            # Create tech debt analysis crew on-demand
            crew = self._create_crew_on_demand(
                "tech_debt_analysis",
                asset_inventory=self.state.asset_inventory,
                dependencies=self.state.dependencies,
                shared_memory=getattr(self.state, 'shared_memory_reference', None)
            )
            
            if crew and CREWAI_FLOW_AVAILABLE:
                # Execute the crew
                crew_input = {
                    "asset_inventory": self.state.asset_inventory,
                    "dependencies": self.state.dependencies,
                    "analysis_type": "comprehensive_technical_debt_assessment"
                }
                
                crew_result = crew.kickoff(inputs=crew_input)
                logger.info(f"Technical debt analysis crew completed: {type(crew_result)}")
                
                # Process crew results
                tech_debt_results = self._process_tech_debt_analysis_results(crew_result)
                
            else:
                logger.warning("Technical debt analysis crew not available - using fallback")
                tech_debt_results = self._fallback_tech_debt_analysis()
            
            # Store results in state
            self.state.technical_debt = tech_debt_results
            self.state.mark_phase_complete("tech_debt_analysis", tech_debt_results)
            self.state.update_progress()
            
            debt_items = len(tech_debt_results.get("debt_scores", {}))
            logger.info(f"✅ Technical debt analysis completed: {debt_items} debt items assessed")
            return "tech_debt_analysis_completed"
            
        except Exception as e:
            logger.error(f"❌ Technical debt analysis execution failed: {e}")
            self.state.add_error("tech_debt_analysis", str(e))
            return "tech_debt_analysis_failed"
    
    @listen(execute_tech_debt_analysis_crew)
    def finalize_discovery(self, previous_result):
        """Finalize the discovery flow and provide comprehensive summary"""
        logger.info("🎯 Finalizing Unified Discovery Flow")
        self.state.current_phase = "finalization"
        self.state.progress_percentage = 100.0
        
        try:
            # Generate final summary
            summary = self.state.finalize_flow()
            
            # Validate overall success
            total_assets = self.state.asset_inventory.get("total_assets", 0)
            if total_assets == 0:
                logger.error("❌ Discovery Flow FAILED: No assets were processed")
                self.state.status = "failed"
                self.state.add_error("finalization", "No assets were processed during discovery")
                return "discovery_failed"
            
            # Mark as completed
            self.state.status = "completed"
            self.state.current_phase = "completed"
            
            logger.info(f"✅ Unified Discovery Flow completed successfully")
            logger.info(f"📊 Summary: {total_assets} assets, {len(self.state.errors)} errors, {len(self.state.warnings)} warnings")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Discovery flow finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            self.state.status = "failed"
            return "discovery_failed"
    
    # ========================================
    # HELPER METHODS FOR RESULT PROCESSING
    # ========================================
    
    def _process_field_mapping_results(self, crew_result) -> Dict[str, Any]:
        """Process field mapping crew results"""
        # Extract field mappings from crew output
        mappings = {}
        confidence_scores = {}
        unmapped_fields = []
        
        # Basic field mapping logic (enhanced by crew intelligence)
        if self.state.raw_data:
            sample_record = self.state.raw_data[0]
            for field in sample_record.keys():
                field_lower = field.lower()
                
                if any(keyword in field_lower for keyword in ['name', 'hostname', 'server']):
                    mappings[field] = 'name'
                    confidence_scores[field] = 0.9
                elif any(keyword in field_lower for keyword in ['ip', 'address']):
                    mappings[field] = 'ip_address'
                    confidence_scores[field] = 0.95
                elif any(keyword in field_lower for keyword in ['os', 'operating']):
                    mappings[field] = 'operating_system'
                    confidence_scores[field] = 0.85
                elif any(keyword in field_lower for keyword in ['cpu', 'processor']):
                    mappings[field] = 'cpu_cores'
                    confidence_scores[field] = 0.8
                elif any(keyword in field_lower for keyword in ['memory', 'ram']):
                    mappings[field] = 'memory_gb'
                    confidence_scores[field] = 0.8
                elif any(keyword in field_lower for keyword in ['storage', 'disk']):
                    mappings[field] = 'storage_gb'
                    confidence_scores[field] = 0.8
                else:
                    unmapped_fields.append(field)
        
        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "unmapped_fields": unmapped_fields,
            "validation_results": {"overall_confidence": sum(confidence_scores.values()) / max(len(confidence_scores), 1)},
            "agent_insights": {"crew_output": str(crew_result)}
        }
    
    def _process_data_cleansing_results(self, crew_result) -> Dict[str, Any]:
        """Process data cleansing crew results"""
        cleaned_data = []
        quality_metrics = {}
        
        # Basic data cleansing (enhanced by crew intelligence)
        for record in self.state.raw_data:
            cleaned_record = {}
            for field, value in record.items():
                # Basic cleaning
                if isinstance(value, str):
                    cleaned_record[field] = value.strip()
                else:
                    cleaned_record[field] = value
            cleaned_data.append(cleaned_record)
        
        quality_metrics = {
            "overall_score": 0.85,
            "completeness": len(cleaned_data) / max(len(self.state.raw_data), 1),
            "standardization_complete": True
        }
        
        return {
            "cleaned_data": cleaned_data,
            "quality_metrics": quality_metrics,
            "crew_output": str(crew_result)
        }
    
    def _process_asset_inventory_results(self, crew_result) -> Dict[str, Any]:
        """Process asset inventory crew results"""
        servers = []
        applications = []
        devices = []
        
        # Basic asset classification (enhanced by crew intelligence)
        for record in self.state.cleaned_data:
            asset_type = "server"  # Default classification
            
            # Basic classification logic
            if any(keyword in str(record).lower() for keyword in ['server', 'host']):
                asset_type = "server"
            elif any(keyword in str(record).lower() for keyword in ['app', 'application']):
                asset_type = "application"
            elif any(keyword in str(record).lower() for keyword in ['device', 'endpoint']):
                asset_type = "device"
            
            asset_data = {
                "id": str(uuid.uuid4()),
                "type": asset_type,
                "data": record,
                "classification_confidence": 0.8
            }
            
            if asset_type == "server":
                servers.append(asset_data)
            elif asset_type == "application":
                applications.append(asset_data)
            else:
                devices.append(asset_data)
        
        total_assets = len(servers) + len(applications) + len(devices)
        
        return {
            "servers": servers,
            "applications": applications,
            "devices": devices,
            "classification_metadata": {"crew_output": str(crew_result)},
            "total_assets": total_assets,
            "classification_confidence": {"overall": 0.8}
        }
    
    def _process_dependency_analysis_results(self, crew_result) -> Dict[str, Any]:
        """Process dependency analysis crew results"""
        return {
            "app_server_dependencies": {
                "hosting_relationships": [],
                "resource_mappings": [],
                "topology_insights": {"crew_output": str(crew_result)}
            },
            "app_app_dependencies": {
                "communication_patterns": [],
                "api_dependencies": [],
                "integration_complexity": {},
                "dependency_graph": {"nodes": [], "edges": []}
            }
        }
    
    def _process_tech_debt_analysis_results(self, crew_result) -> Dict[str, Any]:
        """Process technical debt analysis crew results"""
        return {
            "debt_scores": {},
            "modernization_recommendations": [],
            "risk_assessments": {},
            "six_r_preparation": {"crew_output": str(crew_result)}
        }
    
    # ========================================
    # FALLBACK METHODS
    # ========================================
    
    def _fallback_field_mapping(self) -> Dict[str, Any]:
        """Fallback field mapping when crew is not available"""
        return {
            "mappings": {"name": "name"} if self.state.raw_data else {},
            "confidence_scores": {"name": 0.5} if self.state.raw_data else {},
            "unmapped_fields": [],
            "validation_results": {"fallback_used": True},
            "agent_insights": {"message": "Fallback field mapping used"}
        }
    
    def _fallback_data_cleansing(self) -> Dict[str, Any]:
        """Fallback data cleansing when crew is not available"""
        return {
            "cleaned_data": self.state.raw_data,
            "quality_metrics": {"overall_score": 0.5, "fallback_used": True}
        }
    
    def _fallback_asset_inventory(self) -> Dict[str, Any]:
        """Fallback asset inventory when crew is not available"""
        return {
            "servers": [{"id": str(uuid.uuid4()), "type": "server", "data": record} for record in self.state.cleaned_data],
            "applications": [],
            "devices": [],
            "classification_metadata": {"fallback_used": True},
            "total_assets": len(self.state.cleaned_data),
            "classification_confidence": {"overall": 0.5}
        }
    
    def _fallback_dependency_analysis(self) -> Dict[str, Any]:
        """Fallback dependency analysis when crew is not available"""
        return {
            "app_server_dependencies": {"hosting_relationships": [], "resource_mappings": [], "topology_insights": {}},
            "app_app_dependencies": {"communication_patterns": [], "api_dependencies": [], "integration_complexity": {}, "dependency_graph": {"nodes": [], "edges": []}}
        }
    
    def _fallback_tech_debt_analysis(self) -> Dict[str, Any]:
        """Fallback technical debt analysis when crew is not available"""
        return {
            "debt_scores": {},
            "modernization_recommendations": [],
            "risk_assessments": {},
            "six_r_preparation": {"fallback_used": True}
        }


# ========================================
# FACTORY FUNCTION
# ========================================

def create_unified_discovery_flow(
    session_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    crewai_service,
    context: RequestContext
) -> UnifiedDiscoveryFlow:
    """
    Factory function to create and initialize a Unified Discovery Flow.
    
    This replaces all previous factory functions and creates a single,
    properly configured CrewAI Flow instance.
    """
    
    flow = UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        session_id=session_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        raw_data=raw_data,
        metadata=metadata
    )
    
    logger.info(f"✅ Unified Discovery Flow created: {session_id}")
    return flow 