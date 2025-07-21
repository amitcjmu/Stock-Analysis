"""
Crew Execution Handler for Discovery Flow
This file now serves as a compatibility layer, re-exporting all functionality
from the modularized crew_execution modules.
"""

import logging
from typing import Dict, Any

# Import all modularized components
from .crew_execution import (
    FieldMappingExecutor,
    DataCleansingExecutor,
    InventoryBuildingExecutor,
    DependencyAnalysisExecutor,
    TechnicalDebtExecutor,
    DiscoveryIntegrationExecutor
)

logger = logging.getLogger(__name__)

class CrewExecutionHandler:
    """
    Handles execution of all Discovery Flow crews.
    
    This class now delegates to specialized executors for better modularity
    while maintaining backward compatibility.
    """
    
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service
        
        # Initialize all executors
        self.field_mapping_executor = FieldMappingExecutor(crewai_service)
        self.data_cleansing_executor = DataCleansingExecutor(crewai_service)
        self.inventory_building_executor = InventoryBuildingExecutor(crewai_service)
        self.dependency_analysis_executor = DependencyAnalysisExecutor(crewai_service)
        self.technical_debt_executor = TechnicalDebtExecutor(crewai_service)
        self.discovery_integration_executor = DiscoveryIntegrationExecutor(crewai_service)
    
    def execute_field_mapping_crew(self, state, crewai_service) -> Dict[str, Any]:
        """Execute Field Mapping Crew with enhanced CrewAI features"""
        return self.field_mapping_executor.execute_field_mapping_crew(state, crewai_service)
    
    def execute_data_cleansing_crew(self, state) -> Dict[str, Any]:
        """Execute Data Cleansing Crew with enhanced CrewAI features"""
        return self.data_cleansing_executor.execute_data_cleansing_crew(state)
    
    def execute_inventory_building_crew(self, state) -> Dict[str, Any]:
        """Execute Inventory Building Crew with enhanced CrewAI features"""
        return self.inventory_building_executor.execute_inventory_building_crew(state)
    
    def execute_app_server_dependency_crew(self, state) -> Dict[str, Any]:
        """Execute App-Server Dependency Crew with enhanced CrewAI features"""
        return self.dependency_analysis_executor.execute_app_server_dependency_crew(state)
    
    def execute_app_app_dependency_crew(self, state) -> Dict[str, Any]:
        """Execute App-App Dependency Crew with enhanced CrewAI features"""
        return self.dependency_analysis_executor.execute_app_app_dependency_crew(state)
    
    def execute_technical_debt_crew(self, state) -> Dict[str, Any]:
        """Execute Technical Debt Crew with enhanced CrewAI features"""
        return self.technical_debt_executor.execute_technical_debt_crew(state)
    
    def execute_discovery_integration(self, state) -> Dict[str, Any]:
        """Execute Discovery Integration - final consolidation"""
        return self.discovery_integration_executor.execute_discovery_integration(state)
    
    # Legacy private methods maintained for compatibility
    def _persist_discovery_data_to_database(self, state) -> Dict[str, Any]:
        """Persist discovery data to database tables - Synchronous wrapper"""
        return self.discovery_integration_executor._persist_discovery_data_to_database(state)
    
    async def _async_persist_discovery_data(self, state) -> Dict[str, Any]:
        """Async method to persist discovery data to database"""
        return await self.discovery_integration_executor._async_persist_discovery_data(state)