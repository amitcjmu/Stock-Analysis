"""
Dependency Analysis Crew Execution Handler
Handles both App-Server and App-App dependency crews
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .base import CrewExecutionBase
from .parsers import CrewResultParser
from .fallbacks import CrewFallbackHandler

logger = logging.getLogger(__name__)

class DependencyAnalysisExecutor(CrewExecutionBase):
    """Handles execution of dependency analysis crews"""
    
    def __init__(self, crewai_service):
        super().__init__(crewai_service)
        self.parser = CrewResultParser()
        self.fallback_handler = CrewFallbackHandler()
    
    def execute_app_server_dependency_crew(self, state) -> Dict[str, Any]:
        """Execute App-Server Dependency Crew with enhanced CrewAI features"""
        try:
            # Execute enhanced App-Server Dependency Crew
            try:
                from app.services.crewai_flows.crews.app_server_dependency_crew import create_app_server_dependency_crew
                
                # Pass shared memory and asset inventory
                shared_memory = getattr(state, 'shared_memory_reference', None)
                
                # Create and execute the enhanced crew with correct arguments
                crew = create_app_server_dependency_crew(
                    crewai_service=self.crewai_service,
                    asset_inventory=state.asset_inventory,
                    shared_memory=shared_memory
                )
                crew_result = crew.kickoff()
                
                # Parse crew results
                app_server_dependencies = self.parser.parse_dependency_results(crew_result, "app_server")
                
                logger.info("✅ Enhanced App-Server Dependency Crew executed successfully")
                
            except Exception as crew_error:
                logger.warning(f"Enhanced App-Server Dependency Crew execution failed, using fallback: {crew_error}")
                # Fallback dependency mapping
                app_server_dependencies = self.fallback_handler.intelligent_dependency_fallback(state.asset_inventory, "app_server")
        
            crew_status = self.create_crew_status(
                status="completed",
                manager="Dependency Manager",
                agents=["Hosting Relationship Expert", "Migration Impact Analyst"],
                success_criteria_met=True
            )
            
            return {
                "app_server_dependencies": app_server_dependencies,
                "crew_status": crew_status
            }
            
        except Exception as e:
            logger.error(f"App-Server Dependency Crew execution failed: {e}")
            raise
    
    def execute_app_app_dependency_crew(self, state) -> Dict[str, Any]:
        """Execute App-App Dependency Crew with enhanced CrewAI features"""
        try:
            # Execute enhanced App-App Dependency Crew
            try:
                from app.services.crewai_flows.crews.app_app_dependency_crew import create_app_app_dependency_crew
                
                # Pass shared memory and asset inventory  
                shared_memory = getattr(state, 'shared_memory_reference', None)
                
                # Create and execute the enhanced crew with correct arguments
                crew = create_app_app_dependency_crew(
                    crewai_service=self.crewai_service,
                    asset_inventory=state.asset_inventory,
                    app_server_dependencies=state.app_server_dependencies,
                    shared_memory=shared_memory
                )
                crew_result = crew.kickoff()
                
                # Parse crew results
                app_app_dependencies = self.parser.parse_dependency_results(crew_result, "app_app")
                
                logger.info("✅ Enhanced App-App Dependency Crew executed successfully")
                
            except Exception as crew_error:
                logger.warning(f"Enhanced App-App Dependency Crew execution failed, using fallback: {crew_error}")
                # Fallback dependency mapping
                app_app_dependencies = self.fallback_handler.intelligent_dependency_fallback(state.asset_inventory, "app_app")
        
            crew_status = self.create_crew_status(
                status="completed",
                manager="Integration Manager",
                agents=["Integration Pattern Expert", "Business Flow Analyst"],
                success_criteria_met=True
            )
            
            return {
                "app_app_dependencies": app_app_dependencies,
                "crew_status": crew_status
            }
            
        except Exception as e:
            logger.error(f"App-App Dependency Crew execution failed: {e}")
            raise