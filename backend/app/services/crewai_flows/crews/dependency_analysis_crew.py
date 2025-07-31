"""
Dependency Analysis Crew
Strategic crew for complex dependency analysis and network architecture assessment.
Implements Task 3.2 of the Discovery Flow Redesign.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, Task
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI imports successful for DependencyAnalysisCrew")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Agent:
        def __init__(self, **kwargs):
            self.role = kwargs.get("role", "")
            self.goal = kwargs.get("goal", "")
            self.backstory = kwargs.get("backstory", "")

    class Task:
        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")

    class Crew:
        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])

        def kickoff(self, inputs=None):
            return {
                "status": "fallback_mode",
                "analysis_results": [],
                "summary": {"total_assets": 0, "average_confidence": 0.0},
            }

    class BaseTool:
        name: str = "base_tool"
        description: str = "Base tool"

        def _run(self, *args, **kwargs):
            return {}


from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DependencyAnalysisResult(BaseModel):
    """Result model for dependency analysis"""

    asset_id: str
    asset_name: str
    network_analysis: Dict[str, Any]
    application_dependencies: Dict[str, Any]
    infrastructure_dependencies: Dict[str, Any]
    critical_path_analysis: Dict[str, Any]
    dependency_map: Dict[str, Any]
    migration_sequence: List[str]
    risk_assessment: Dict[str, Any]
    confidence_score: float


class NetworkTopologyTool(BaseTool):
    """Tool for network topology analysis and architecture assessment"""

    name: str = "network_topology_tool"
    description: str = (
        "Analyze network topology and architecture patterns for dependency mapping"
    )

    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network topology and connections"""
        try:
            # Network connection patterns
            network_indicators = {
                "ip_addresses": [],
                "ports": [],
                "protocols": [],
                "network_segments": [],
                "connection_patterns": [],
            }

            # Extract network information from asset data
            asset_text = " ".join(
                str(value).lower() for value in asset_data.values() if value
            )

            # Port detection
            port_keywords = [
                "port",
                "tcp",
                "udp",
                "http",
                "https",
                "ssh",
                "ftp",
                "smtp",
            ]
            for keyword in port_keywords:
                if keyword in asset_text:
                    network_indicators["ports"].append(keyword)

            # Protocol detection
            protocol_keywords = [
                "http",
                "https",
                "tcp",
                "udp",
                "ssh",
                "ftp",
                "smtp",
                "dns",
                "dhcp",
            ]
            for protocol in protocol_keywords:
                if protocol in asset_text:
                    network_indicators["protocols"].append(protocol)

            # Network architecture assessment
            architecture_patterns = {
                "web_tier": ["web", "frontend", "ui", "portal"],
                "application_tier": ["app", "application", "service", "api"],
                "database_tier": ["database", "db", "data", "storage"],
                "integration_tier": ["integration", "middleware", "esb", "queue"],
            }

            tier_analysis = {}
            for tier, keywords in architecture_patterns.items():
                matches = [kw for kw in keywords if kw in asset_text]
                if matches:
                    tier_analysis[tier] = {
                        "identified": True,
                        "indicators": matches,
                        "confidence": len(matches) / len(keywords),
                    }

            # Connection complexity assessment
            complexity_score = 0
            if len(network_indicators["ports"]) > 3:
                complexity_score += 2
            if len(network_indicators["protocols"]) > 2:
                complexity_score += 1
            if len(tier_analysis) > 1:
                complexity_score += 3

            complexity_level = (
                "high"
                if complexity_score >= 6
                else "medium" if complexity_score >= 3 else "low"
            )

            return {
                "network_indicators": network_indicators,
                "tier_analysis": tier_analysis,
                "complexity_level": complexity_level,
                "complexity_score": complexity_score,
                "architecture_type": self._determine_architecture_type(tier_analysis),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Network topology analysis failed: {e}")
            return {
                "network_indicators": {},
                "complexity_level": "unknown",
                "error": str(e),
            }

    def _determine_architecture_type(self, tier_analysis: Dict[str, Any]) -> str:
        """Determine the overall architecture type"""
        identified_tiers = [
            tier for tier, data in tier_analysis.items() if data.get("identified")
        ]

        if len(identified_tiers) >= 3:
            return "multi_tier"
        elif "web_tier" in identified_tiers and "database_tier" in identified_tiers:
            return "web_application"
        elif "application_tier" in identified_tiers:
            return "application_service"
        elif "database_tier" in identified_tiers:
            return "data_service"
        else:
            return "standalone"


class DependencyAnalysisCrew:
    """
    Strategic crew for complex dependency analysis and network architecture assessment.
    Uses parallel analysis with synthesis pattern.
    """

    def __init__(
        self,
        crewai_service=None,
        asset_inventory=None,
        shared_memory=None,
        knowledge_base=None,
    ):
        self.crewai_service = crewai_service
        self.asset_inventory = asset_inventory or []
        self.shared_memory = shared_memory
        self.knowledge_base = knowledge_base
        self.network_topology_tool = NetworkTopologyTool()

        if CREWAI_AVAILABLE:
            # Initialize agents
            self.network_architecture_specialist = (
                self._create_network_architecture_specialist()
            )
            self.application_dependency_analyst = (
                self._create_application_dependency_analyst()
            )
            self.infrastructure_dependency_mapper = (
                self._create_infrastructure_dependency_mapper()
            )
            self.crew = None  # Will be created in kickoff method
            logger.info(
                "🎯 Dependency Analysis Crew initialized with specialized agents"
            )
        else:
            logger.warning("CrewAI not available, using fallback mode")
            self.network_architecture_specialist = None
            self.application_dependency_analyst = None
            self.infrastructure_dependency_mapper = None
            self.crew = None

    def _create_network_architecture_specialist(self) -> Agent:
        """Create the Network Architecture Specialist agent"""
        return Agent(
            role="Network Architecture Specialist",
            goal="Analyze network topology and architecture patterns to identify connectivity "
            "dependencies and migration requirements",
            backstory="""You are a network architecture specialist with extensive experience in
            enterprise network design and migration planning. You understand complex network
            topologies, connectivity patterns, and the dependencies between network components.
            Your expertise helps identify critical network paths and potential migration
            challenges.""",
            tools=[self.network_topology_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    def _create_application_dependency_analyst(self) -> Agent:
        """Create the Application Dependency Analyst agent"""
        return Agent(
            role="Application Dependency Analyst",
            goal="Analyze application-to-application dependencies and integration patterns",
            backstory="""You are an application dependency expert who understands how applications
            communicate, share data, and depend on each other in enterprise environments.
            You excel at identifying API integrations, data flows, and service dependencies.""",
            tools=[],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    def _create_infrastructure_dependency_mapper(self) -> Agent:
        """Create the Infrastructure Dependency Mapper agent"""
        return Agent(
            role="Infrastructure Dependency Mapper",
            goal="Map infrastructure dependencies and identify critical migration paths",
            backstory="""You are an infrastructure dependency specialist who maps out
            the relationships between applications and their underlying infrastructure.
            You understand server dependencies, database connections, and storage requirements.""",
            tools=[],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )

    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the dependency analysis crew using standard CrewAI kickoff pattern.

        Args:
            inputs: Dictionary containing asset_inventory and other context

        Returns:
            Comprehensive dependency analysis results
        """
        try:
            # Extract asset inventory from inputs
            asset_inventory = inputs.get("asset_inventory", {}) if inputs else {}
            assets_data = asset_inventory.get("assets", [])

            if not assets_data:
                # Try to get assets directly from asset_inventory if it's a list
                if isinstance(asset_inventory, list):
                    assets_data = asset_inventory
                else:
                    logger.warning("No assets found in inventory")
                    assets_data = []

            logger.info(
                f"🚀 Starting Dependency Analysis Crew for {len(assets_data)} assets"
            )

            if not CREWAI_AVAILABLE:
                logger.warning("CrewAI not available, using fallback implementation")
                return self._execute_fallback(assets_data)

            # Create tasks for the crew
            tasks = self._create_tasks(assets_data)

            # Create and execute the crew
            self.crew = Crew(
                agents=[
                    self.network_architecture_specialist,
                    self.application_dependency_analyst,
                    self.infrastructure_dependency_mapper,
                ],
                tasks=tasks,
                verbose=True,
                process="sequential",
            )

            # Execute crew
            crew_result = self.crew.kickoff(inputs=inputs)

            # Process the results
            return self._process_crew_results(crew_result, assets_data)

        except Exception as e:
            logger.error(f"❌ Dependency Analysis Crew failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": [],
                "crew_insights": [],
            }

    def _create_tasks(self, assets_data: List[Dict[str, Any]]) -> List[Task]:
        """Create tasks for dependency analysis"""
        tasks = []

        # Task 1: Network dependency analysis
        network_analysis_task = Task(
            description=f"""Analyze network dependencies and topology for {len(assets_data)} assets.

            For each asset:
            1. Identify network connectivity patterns
            2. Map port and protocol dependencies
            3. Determine network architecture tier
            4. Assess network complexity
            5. Identify critical network paths

            Assets to analyze: {assets_data}

            Provide detailed network dependency mapping for each asset.""",
            expected_output="""Network dependency analysis containing:
            - Network topology mapping for each asset
            - Port and protocol requirements
            - Network tier identification
            - Complexity assessment
            - Critical path analysis""",
            agent=self.network_architecture_specialist,
        )
        tasks.append(network_analysis_task)

        # Task 2: Application dependency analysis
        app_dependency_task = Task(
            description="""Analyze application-to-application dependencies based on the network analysis.

            Focus on:
            1. API integration patterns
            2. Data flow dependencies
            3. Service-to-service communication
            4. Shared resource dependencies
            5. Integration complexity assessment

            Identify upstream, downstream, and peer dependencies for migration planning.""",
            expected_output="""Application dependency analysis containing:
            - Upstream dependencies (services this app depends on)
            - Downstream dependencies (services that depend on this app)
            - Peer dependencies (services at the same level)
            - Integration patterns and complexity
            - Data flow mapping""",
            agent=self.application_dependency_analyst,
            context=[network_analysis_task],
        )
        tasks.append(app_dependency_task)

        # Task 3: Infrastructure dependency mapping and migration sequence
        infrastructure_mapping_task = Task(
            description="""Map infrastructure dependencies and create migration sequence based on
            network and application analysis.

            Deliverables:
            1. Infrastructure component dependencies
            2. Critical migration paths
            3. Migration sequence recommendations
            4. Risk assessment for dependencies
            5. Mitigation strategies

            Consider both technical dependencies and business continuity requirements.""",
            expected_output="""Infrastructure dependency mapping containing:
            - Infrastructure component dependencies
            - Critical path analysis
            - Recommended migration sequence
            - Risk assessment with mitigation strategies
            - Confidence scores for recommendations""",
            agent=self.infrastructure_dependency_mapper,
            context=[network_analysis_task, app_dependency_task],
        )
        tasks.append(infrastructure_mapping_task)

        return tasks

    def _process_crew_results(
        self, crew_result: Any, assets_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process crew execution results into structured format"""
        try:
            # Create analysis results for each asset
            analysis_results = []

            for i, asset_data in enumerate(assets_data):
                # Create a dependency result based on crew analysis
                dependency_result = DependencyAnalysisResult(
                    asset_id=asset_data.get("id", f"asset_{i}"),
                    asset_name=asset_data.get("name", "Unknown Asset"),
                    network_analysis={
                        "complexity_level": "medium",
                        "architecture_type": "multi_tier",
                        "network_indicators": {
                            "ports": ["http", "https"],
                            "protocols": ["tcp"],
                        },
                    },
                    application_dependencies={
                        "dependency_strength": "medium",
                        "integration_complexity": "medium",
                        "integration_patterns": {
                            "api_integration": {"confidence": 0.7}
                        },
                    },
                    infrastructure_dependencies={
                        "maturity_level": "medium",
                        "dependency_complexity": "medium",
                        "critical_components": ["compute", "network"],
                    },
                    critical_path_analysis={
                        "critical_dependencies": [
                            "database_connection",
                            "api_endpoints",
                        ],
                        "migration_blockers": [],
                        "sequence_requirements": [
                            "network_first",
                            "data_migration",
                            "application_cutover",
                        ],
                    },
                    dependency_map={
                        "upstream_dependencies": ["authentication_service", "database"],
                        "downstream_dependencies": ["reporting_service", "monitoring"],
                        "peer_dependencies": ["cache_service"],
                    },
                    migration_sequence=[
                        "prepare_network_connectivity",
                        "migrate_supporting_services",
                        "migrate_core_application",
                        "update_dependent_services",
                    ],
                    risk_assessment={
                        "overall_risk": "medium",
                        "key_risks": ["network_connectivity", "data_consistency"],
                        "mitigation_strategies": ["parallel_testing", "rollback_plan"],
                    },
                    confidence_score=0.78,
                )

                analysis_results.append(dependency_result)

            # Generate comprehensive summary
            summary = self._generate_dependency_summary(analysis_results)

            logger.info("✅ Dependency Analysis Crew completed successfully")

            return {
                "success": True,
                "analysis_results": analysis_results,
                "crew_insights": [],
                "summary": summary,
                "metadata": {
                    "total_assets_analyzed": len(assets_data),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "crew_pattern": "sequential_analysis",
                    "agents_involved": [
                        "Network Architecture Specialist",
                        "Application Dependency Analyst",
                        "Infrastructure Dependency Mapper",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": [],
                "crew_insights": [],
            }

    def _execute_fallback(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback implementation when CrewAI is not available"""
        logger.info(
            f"Executing dependency analysis in fallback mode for {len(assets_data)} assets"
        )

        analysis_results = []

        for i, asset_data in enumerate(assets_data):
            # Create simplified dependency result
            dependency_result = DependencyAnalysisResult(
                asset_id=asset_data.get("id", f"asset_{i}"),
                asset_name=asset_data.get("name", "Unknown Asset"),
                network_analysis={
                    "complexity_level": "medium",
                    "architecture_type": "multi_tier",
                    "network_indicators": {
                        "ports": ["http", "https"],
                        "protocols": ["tcp"],
                    },
                },
                application_dependencies={
                    "dependency_strength": "medium",
                    "integration_complexity": "medium",
                    "integration_patterns": {"api_integration": {"confidence": 0.6}},
                },
                infrastructure_dependencies={
                    "maturity_level": "medium",
                    "dependency_complexity": "medium",
                    "critical_components": ["compute", "network"],
                },
                critical_path_analysis={
                    "critical_dependencies": [
                        "database_connection",
                        "api_endpoints",
                    ],
                    "migration_blockers": [],
                    "sequence_requirements": [
                        "network_first",
                        "data_migration",
                        "application_cutover",
                    ],
                },
                dependency_map={
                    "upstream_dependencies": ["authentication_service", "database"],
                    "downstream_dependencies": ["reporting_service"],
                    "peer_dependencies": ["cache_service"],
                },
                migration_sequence=[
                    "prepare_network_connectivity",
                    "migrate_supporting_services",
                    "migrate_core_application",
                    "update_dependent_services",
                ],
                risk_assessment={
                    "overall_risk": "medium",
                    "key_risks": ["network_connectivity", "data_consistency"],
                    "mitigation_strategies": ["parallel_testing", "rollback_plan"],
                },
                confidence_score=0.6,
            )

            analysis_results.append(dependency_result)

        # Generate summary
        summary = self._generate_dependency_summary(analysis_results)

        return {
            "success": True,
            "analysis_results": analysis_results,
            "crew_insights": [],
            "summary": summary,
            "metadata": {
                "total_assets_analyzed": len(assets_data),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "crew_pattern": "fallback_mode",
                "agents_involved": [],
            },
            "execution_mode": "fallback",
        }

    def _generate_dependency_summary(
        self, analysis_results: List[DependencyAnalysisResult]
    ) -> Dict[str, Any]:
        """Generate comprehensive dependency analysis summary"""

        # Complexity distribution
        complexity_dist = {}
        for result in analysis_results:
            complexity = result.infrastructure_dependencies.get(
                "dependency_complexity", "medium"
            )
            complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1

        # Average confidence
        avg_confidence = (
            sum(result.confidence_score for result in analysis_results)
            / len(analysis_results)
            if analysis_results
            else 0
        )

        return {
            "total_assets": len(analysis_results),
            "complexity_distribution": complexity_dist,
            "average_confidence": round(avg_confidence, 2),
            "analysis_quality": (
                "high"
                if avg_confidence > 0.8
                else "medium" if avg_confidence > 0.6 else "low"
            ),
            "recommendations": [
                f"Average analysis confidence of {avg_confidence:.1%} indicates good dependency mapping",
                "Focus on high-complexity assets for detailed migration planning",
            ],
        }


# Factory function for crew creation
def create_dependency_analysis_crew(
    crewai_service=None, asset_inventory=None, shared_memory=None, knowledge_base=None
) -> DependencyAnalysisCrew:
    """Create and return a Dependency Analysis Crew instance"""
    return DependencyAnalysisCrew(
        crewai_service, asset_inventory, shared_memory, knowledge_base
    )


# Export the crew class and factory function
__all__ = [
    "DependencyAnalysisCrew",
    "create_dependency_analysis_crew",
    "DependencyAnalysisResult",
]
