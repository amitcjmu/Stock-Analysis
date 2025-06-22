"""
Unified Flow Crew Manager
Handles CrewAI crew creation and management for the Unified Discovery Flow.
Extracted from unified_discovery_flow.py for better modularity.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist
    CREWAI_FLOW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrewAI Flow not available: {e}")


class UnifiedFlowCrewManager:
    """
    Manages CrewAI crew creation and execution for the Unified Discovery Flow.
    Handles on-demand crew creation with proper error handling and fallbacks.
    """
    
    def __init__(self, crewai_service, state):
        """Initialize crew manager with service and state references"""
        self.crewai_service = crewai_service
        self.state = state
        self.crew_factories = {}
        
        # Initialize crew factories for on-demand creation
        self._initialize_crew_factories()
    
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
    
    def create_crew_on_demand(self, crew_type: str, **kwargs) -> Optional[Any]:
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
    
    def is_crew_available(self, crew_type: str) -> bool:
        """Check if a crew type is available"""
        return crew_type in self.crew_factories and CREWAI_FLOW_AVAILABLE
    
    def get_available_crews(self) -> list:
        """Get list of available crew types"""
        return list(self.crew_factories.keys()) if CREWAI_FLOW_AVAILABLE else [] 