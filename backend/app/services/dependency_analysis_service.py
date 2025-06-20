"""
Service for analyzing and managing asset dependencies with CrewAI integration.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.dependency_repository import DependencyRepository
from app.models.asset import AssetDependency
from app.services.crewai_flows.discovery_flow import DiscoveryFlowService
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class DependencyAnalysisService:
    """Service for analyzing and managing asset dependencies."""
    
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
        session_id: Optional[str] = None
    ):
        """Initialize the service with context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.session_id = session_id
        self.repository = DependencyRepository(db, client_account_id, engagement_id)
        self.discovery_flow = DiscoveryFlowService(db, client_account_id, engagement_id)

    async def get_dependency_analysis(self) -> Dict[str, Any]:
        """Get comprehensive dependency analysis."""
        # Get raw dependencies
        app_server_deps = await self.repository.get_app_server_dependencies()
        app_app_deps = await self.repository.get_app_app_dependencies()
        
        # Get available assets for mapping
        available_apps = await self.repository.get_available_applications()
        available_servers = await self.repository.get_available_servers()
        
        # Format for UI
        return {
            'app_server_mapping': {
                'hosting_relationships': app_server_deps,
                'available_applications': available_apps,
                'available_servers': available_servers
            },
            'cross_application_mapping': {
                'cross_app_dependencies': app_app_deps,
                'available_applications': available_apps,
                'dependency_graph': self._build_dependency_graph(app_app_deps)
            }
        }

    def _build_dependency_graph(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build graph structure for visualization."""
        nodes = set()
        edges = []
        
        for dep in dependencies:
            source_id = dep['source_app_id']
            target_app = dep['target_app_info']
            target_id = target_app['id']
            
            # Add nodes
            nodes.add((source_id, dep['source_app_name']))
            nodes.add((target_id, target_app['name']))
            
            # Add edge
            edges.append({
                'source': source_id,
                'target': target_id,
                'type': dep['dependency_type'],
                'description': dep.get('description', '')
            })
        
        return {
            'nodes': [{'id': id, 'label': name} for id, name in nodes],
            'edges': edges
        }

    async def analyze_with_crew(self, analysis_type: str) -> Dict[str, Any]:
        """Trigger CrewAI analysis for dependencies."""
        try:
            # Get current dependencies for context
            current_analysis = await self.get_dependency_analysis()
            
            # Trigger appropriate CrewAI analysis
            if analysis_type == 'app_server_dependencies':
                result = await self.discovery_flow.analyze_app_server_dependencies(
                    current_analysis['app_server_mapping']
                )
            elif analysis_type == 'app_app_dependencies':
                result = await self.discovery_flow.analyze_cross_app_dependencies(
                    current_analysis['cross_application_mapping']
                )
            else:
                raise ValidationError(f"Invalid analysis type: {analysis_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in CrewAI analysis: {str(e)}")
            raise

    async def create_dependency(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str,
        is_app_to_app: bool,
        description: Optional[str] = None
    ) -> AssetDependency:
        """Create a new dependency relationship."""
        try:
            if is_app_to_app:
                return await self.repository.create_app_app_dependency(
                    source_id,
                    target_id,
                    dependency_type,
                    description
                )
            else:
                return await self.repository.create_app_server_dependency(
                    source_id,
                    target_id,
                    dependency_type,
                    description
                )
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error creating dependency: {str(e)}")
            raise 