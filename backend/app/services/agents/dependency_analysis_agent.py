"""
Dependency Analysis Agent - Specialized agent for network analysis and dependency mapping
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult, AgentClarificationRequest, AgentInsight

logger = logging.getLogger(__name__)

class DependencyAnalysisAgent(BaseDiscoveryAgent):
    """Dependency Analysis Agent for network analysis and critical path identification"""
    
    def __init__(self):
        super().__init__(
            agent_id="dependency_analysis_001",
            name="Dependency Analysis Specialist",
            role="Network Architecture and Dependency Expert",
            goal="Identify and map critical dependencies and network relationships between assets",
            backstory="Expert in network topology analysis and application integration mapping"
        )
        
        # Dependency indicators
        self.dependency_patterns = {
            'database_connection': ['jdbc', 'odbc', 'connection_string', 'datasource'],
            'api_integration': ['api', 'rest', 'soap', 'endpoint', 'service'],
            'network_dependency': ['port', 'tcp', 'udp', 'protocol', 'firewall'],
            'file_share': ['nfs', 'smb', 'cifs', 'share', 'mount'],
            'messaging': ['queue', 'topic', 'jms', 'mq', 'kafka']
        }
        
        # Critical path indicators
        self.critical_indicators = [
            'primary', 'master', 'main', 'core', 'critical', 'production'
        ]
        
        self.logger.info(f"🔗 Dependency Analysis Agent initialized")
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute dependency analysis"""
        start_time = time.time()
        
        try:
            assets = data.get('raw_data', [])
            if not assets:
                return self._create_error_result("No asset data provided")
            
            # Analyze dependencies
            dependency_results = await self._analyze_dependencies(assets)
            
            # Identify critical paths
            critical_paths = await self._identify_critical_paths(dependency_results)
            
            # Generate insights
            insights = await self._generate_dependency_insights(dependency_results, critical_paths)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_id=self.agent_id,
                status='completed',
                confidence_score=78.0,
                data={
                    'dependencies': dependency_results,
                    'critical_paths': critical_paths,
                    'dependency_summary': await self._create_dependency_summary(dependency_results)
                },
                insights=insights,
                clarifications=[],
                execution_time=execution_time,
                metadata={'assets_analyzed': len(assets)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return self._create_error_result(f"Dependency analysis failed: {str(e)}", execution_time)
    
    async def _analyze_dependencies(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dependencies between assets"""
        dependencies = []
        
        for asset in assets:
            asset_deps = await self._find_asset_dependencies(asset)
            if asset_deps:
                dependencies.extend(asset_deps)
        
        return {
            'total_dependencies': len(dependencies),
            'dependency_list': dependencies,
            'dependency_types': await self._categorize_dependencies(dependencies)
        }
    
    async def _find_asset_dependencies(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find dependencies for a single asset"""
        dependencies = []
        asset_id = self._get_asset_id(asset)
        
        # Check for different dependency types
        for dep_type, patterns in self.dependency_patterns.items():
            for key, value in asset.items():
                if isinstance(value, str) and any(pattern in value.lower() for pattern in patterns):
                    dependencies.append({
                        'source_asset': asset_id,
                        'dependency_type': dep_type,
                        'dependency_indicator': f"{key}: {value}",
                        'confidence': 75.0
                    })
        
        return dependencies
    
    async def _identify_critical_paths(self, dependency_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical dependency paths"""
        critical_paths = []
        
        # Simple critical path identification based on dependency count and criticality indicators
        for dep in dependency_results.get('dependency_list', []):
            if any(indicator in dep['dependency_indicator'].lower() for indicator in self.critical_indicators):
                critical_paths.append({
                    'path': dep,
                    'criticality': 'high',
                    'impact': 'Migration of this dependency requires careful planning'
                })
        
        return critical_paths
    
    async def _generate_dependency_insights(self, dependency_results: Dict[str, Any], 
                                          critical_paths: List[Dict[str, Any]]) -> List[AgentInsight]:
        """Generate insights about dependencies"""
        insights = []
        
        total_deps = dependency_results.get('total_dependencies', 0)
        if total_deps > 50:
            insights.append(AgentInsight(
                title="High Dependency Complexity",
                description=f"Identified {total_deps} dependencies. This indicates a complex environment requiring careful migration sequencing.",
                confidence_score=85.0,
                category="complexity",
                actionable=True,
                action_items=[
                    "Create detailed dependency mapping",
                    "Plan phased migration approach",
                    "Identify dependency breaking points"
                ]
            ))
        
        if len(critical_paths) > 0:
            insights.append(AgentInsight(
                title="Critical Dependencies Identified",
                description=f"Found {len(critical_paths)} critical dependency paths that require special attention during migration.",
                confidence_score=90.0,
                category="risk_assessment",
                actionable=True,
                action_items=[
                    "Review critical dependencies with stakeholders",
                    "Plan redundancy for critical paths",
                    "Test dependency chains before migration"
                ]
            ))
        
        return insights
    
    async def _categorize_dependencies(self, dependencies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize dependencies by type"""
        categories = {}
        for dep in dependencies:
            dep_type = dep.get('dependency_type', 'unknown')
            categories[dep_type] = categories.get(dep_type, 0) + 1
        return categories
    
    async def _create_dependency_summary(self, dependency_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create dependency summary"""
        return {
            'total_dependencies': dependency_results.get('total_dependencies', 0),
            'dependency_types': dependency_results.get('dependency_types', {}),
            'most_common_dependency': max(
                dependency_results.get('dependency_types', {}).items(),
                key=lambda x: x[1],
                default=('none', 0)
            )[0]
        }
    
    def _get_asset_id(self, asset: Dict[str, Any]) -> str:
        """Get asset identifier"""
        for key in ['id', 'asset_id', 'hostname', 'name']:
            if key in asset and asset[key]:
                return str(asset[key])
        return f"asset_{hash(str(asset)) % 10000}" 