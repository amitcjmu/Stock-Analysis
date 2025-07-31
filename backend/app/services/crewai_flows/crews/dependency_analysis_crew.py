"""
Dependency Analysis Crew
Strategic crew for complex dependency analysis and network architecture assessment.
Implements Task 3.2 of the Discovery Flow Redesign.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.info("✅ CrewAI imports successful for DependencyAnalysisCrew")


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

        # Initialize agents - CrewAI is required
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
        logger.info("🎯 Dependency Analysis Crew initialized with specialized agents")

    def _create_network_architecture_specialist(self) -> Agent:
        """Create the Network Architecture Specialist agent"""
        # Get LLM configuration
        from app.services.llm_config import get_crewai_llm

        llm = get_crewai_llm()

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
            llm=llm,
        )

    def _create_application_dependency_analyst(self) -> Agent:
        """Create the Application Dependency Analyst agent"""
        # Get LLM configuration
        from app.services.llm_config import get_crewai_llm

        llm = get_crewai_llm()

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
            llm=llm,
        )

    def _create_infrastructure_dependency_mapper(self) -> Agent:
        """Create the Infrastructure Dependency Mapper agent"""
        # Get LLM configuration
        from app.services.llm_config import get_crewai_llm

        llm = get_crewai_llm()

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
            llm=llm,
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

            # Validate that assets_data contains valid asset dictionaries
            if assets_data:
                valid_assets = []
                for asset in assets_data:
                    if isinstance(asset, dict) and asset.get("id"):
                        valid_assets.append(asset)
                    else:
                        logger.warning(f"Skipping invalid asset: {asset}")
                assets_data = valid_assets

            # CRITICAL: Ensure we have actual asset data
            if not assets_data:
                logger.error("❌ No assets data available for dependency analysis")
                return {
                    "success": False,
                    "error": "No assets data available",
                    "analysis_results": [],
                    "dependencies": [],
                    "crew_insights": [],
                }

            # Log asset details for debugging
            logger.info(f"📊 Asset inventory contains {len(assets_data)} assets:")
            asset_types = {}
            asset_names = []
            for asset in assets_data:
                if isinstance(asset, dict):
                    asset_type = asset.get("type", "unknown")
                    asset_name = asset.get("name", asset.get("asset_name", "Unknown"))
                    asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                    asset_names.append(f"{asset_name} ({asset_type})")

            for asset_type, count in asset_types.items():
                logger.info(f"  - {asset_type}: {count} assets")

            # Log sample asset names for verification
            if asset_names:
                logger.info(f"Sample assets: {', '.join(asset_names[:5])}...")

            logger.info(
                f"🚀 Starting Dependency Analysis Crew for {len(assets_data)} REAL assets"
            )

            # CrewAI is required - no fallback

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

        # Format asset list for agents - include ID and name only to prevent overwhelming context
        asset_summary = []
        for asset in assets_data[:50]:  # Limit to first 50 assets for context window
            if isinstance(asset, dict):
                asset_summary.append(
                    {
                        "id": asset.get("id", "unknown"),
                        "name": asset.get("name", asset.get("asset_name", "Unknown")),
                        "type": asset.get("type", "unknown"),
                    }
                )

        # Task 1: Network dependency analysis
        network_analysis_task = Task(
            description=f"""Analyze network dependencies and topology for {len(assets_data)} REAL assets.

            CRITICAL INSTRUCTIONS:
            - ONLY analyze the actual assets provided below
            - DO NOT invent or create any fictional services
            - If an asset doesn't have clear dependencies, mark it as standalone
            - Use the asset IDs and names exactly as provided

            For each asset:
            1. Check if asset name/description indicates network connectivity
            2. Look for keywords indicating dependencies (API, database, service)
            3. Identify potential port/protocol usage based on asset type
            4. Determine if asset is client, server, or both
            5. Map connectivity patterns between REAL assets only

            REAL Assets to analyze (showing first {len(asset_summary)} of {len(assets_data)}):
            {asset_summary}

            Return analysis as structured data for each asset.""",
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
            description=f"""Analyze application-to-application dependencies based on the network analysis.

            CRITICAL INSTRUCTIONS:
            - ONLY identify dependencies between the {len(assets_data)} REAL assets provided
            - DO NOT create fictional services or applications
            - Base dependencies on asset names and types
            - If unsure about a dependency, don't include it

            Focus on:
            1. Identifying applications from the asset list (type='application')
            2. Finding servers that host these applications
            3. Discovering databases used by applications
            4. Mapping API relationships based on asset names
            5. Identifying shared infrastructure

            For each dependency found, provide:
            - source_id: The ID of the source asset
            - target_id: The ID of the target asset
            - dependency_type: Type of dependency (hosting, database, api, etc)
            - confidence_score: How confident you are (0.0-1.0)
            - is_app_to_app: Boolean indicating if both are applications

            Return results as a JSON array of dependency objects.""",
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
            description=f"""Map infrastructure dependencies and create migration sequence based on
            network and application analysis of {len(assets_data)} REAL assets.

            CRITICAL INSTRUCTIONS:
            - Create a structured JSON output with discovered dependencies
            - Each dependency must reference REAL asset IDs from the provided list
            - DO NOT invent any services or components

            Required JSON output format:
            {{"dependencies": [
                {{
                    "source_id": "actual_asset_id",
                    "source_name": "actual_asset_name",
                    "target_id": "actual_asset_id",
                    "target_name": "actual_asset_name",
                    "dependency_type": "hosting|database|api|network|storage",
                    "confidence_score": 0.0-1.0,
                    "is_app_to_app": true/false,
                    "description": "Brief description of the dependency"
                }}
            ],
            "migration_groups": [
                {{
                    "group_name": "Group 1",
                    "asset_ids": ["id1", "id2"],
                    "sequence": 1,
                    "reason": "Why these should migrate together"
                }}
            ]}}

            Base dependencies on:
            1. Asset types (servers host applications, applications use databases)
            2. Asset names (similar names may indicate relationships)
            3. Common patterns (web servers, app servers, databases)

            Remember: ONLY use assets from the provided list!""",
            expected_output="""A valid JSON object containing:
            1. 'dependencies' array with discovered dependency relationships
            2. 'migration_groups' array with recommended migration sequences
            Each dependency must reference real asset IDs from the provided inventory.""",
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
            # Initialize empty results
            dependencies = []
            analysis_results = []

            # Try to extract structured JSON from crew result
            if isinstance(crew_result, str):
                # Try to parse JSON from string result
                import json
                import re

                # Look for JSON in the result
                json_match = re.search(r"\{[\s\S]*\}", crew_result)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group())
                        if "dependencies" in parsed_result:
                            dependencies = parsed_result["dependencies"]
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse JSON from crew result")
            elif isinstance(crew_result, dict):
                # Direct dict result
                dependencies = crew_result.get("dependencies", [])

            # Create asset lookup for validation
            asset_lookup = {}
            for asset in assets_data:
                if isinstance(asset, dict):
                    asset_id = asset.get("id")
                    if asset_id:
                        asset_lookup[asset_id] = asset

            # Process and validate dependencies
            validated_dependencies = []
            for dep in dependencies:
                if isinstance(dep, dict):
                    source_id = dep.get("source_id")
                    target_id = dep.get("target_id")

                    # Validate that both assets exist
                    if source_id in asset_lookup and target_id in asset_lookup:
                        validated_dep = {
                            "source_id": source_id,
                            "source_name": dep.get(
                                "source_name",
                                asset_lookup[source_id].get("name", "Unknown"),
                            ),
                            "target_id": target_id,
                            "target_name": dep.get(
                                "target_name",
                                asset_lookup[target_id].get("name", "Unknown"),
                            ),
                            "dependency_type": dep.get("dependency_type", "unknown"),
                            "confidence_score": float(dep.get("confidence_score", 0.5)),
                            "is_app_to_app": bool(dep.get("is_app_to_app", False)),
                            "description": dep.get("description", ""),
                        }
                        validated_dependencies.append(validated_dep)
                    else:
                        logger.warning(
                            f"Skipping invalid dependency: {source_id} -> {target_id}"
                        )

            # If no valid dependencies found, this is a crew failure
            if not validated_dependencies:
                logger.error(
                    "No dependencies extracted from crew - dependency analysis failed"
                )
                # Return empty dependencies rather than generating fake ones
                validated_dependencies = []

            # Create analysis results for compatibility
            for asset_data in assets_data:
                asset_id = asset_data.get("id", "unknown")
                asset_name = asset_data.get(
                    "name", asset_data.get("asset_name", "Unknown")
                )

                # Find dependencies for this asset
                upstream = [
                    d for d in validated_dependencies if d["target_id"] == asset_id
                ]
                downstream = [
                    d for d in validated_dependencies if d["source_id"] == asset_id
                ]

                dependency_result = DependencyAnalysisResult(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    network_analysis={
                        "complexity_level": (
                            "low"
                            if len(upstream) + len(downstream) == 0
                            else (
                                "medium"
                                if len(upstream) + len(downstream) < 3
                                else "high"
                            )
                        ),
                        "architecture_type": self._determine_architecture_type_from_asset(
                            asset_data
                        ),
                        "network_indicators": {
                            "ports": [],
                            "protocols": [],
                        },
                    },
                    application_dependencies={
                        "dependency_strength": (
                            "low"
                            if not downstream
                            else "medium" if len(downstream) < 2 else "high"
                        ),
                        "integration_complexity": "low",
                        "integration_patterns": {},
                    },
                    infrastructure_dependencies={
                        "maturity_level": "medium",
                        "dependency_complexity": "low" if not upstream else "medium",
                        "critical_components": [],
                    },
                    critical_path_analysis={
                        "critical_dependencies": [d["source_name"] for d in upstream],
                        "migration_blockers": [],
                        "sequence_requirements": [],
                    },
                    dependency_map={
                        "upstream_dependencies": [d["source_id"] for d in upstream],
                        "downstream_dependencies": [d["target_id"] for d in downstream],
                        "peer_dependencies": [],
                    },
                    migration_sequence=[],
                    risk_assessment={
                        "overall_risk": "low" if not upstream else "medium",
                        "key_risks": [],
                        "mitigation_strategies": [],
                    },
                    confidence_score=0.8 if validated_dependencies else 0.5,
                )

                analysis_results.append(dependency_result)

            # Generate comprehensive summary
            summary = self._generate_dependency_summary(analysis_results)

            logger.info("✅ Dependency Analysis Crew completed successfully")

            return {
                "success": True,
                "analysis_results": analysis_results,
                "dependencies": validated_dependencies,
                "crew_insights": [],
                "summary": summary,
                "metadata": {
                    "total_assets_analyzed": len(assets_data),
                    "total_dependencies_found": len(validated_dependencies),
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

    def _determine_architecture_type_from_asset(
        self, asset_data: Dict[str, Any]
    ) -> str:
        """Determine architecture type from asset information"""
        asset_type = asset_data.get("type", "").lower()
        asset_name = asset_data.get("name", "").lower()

        if "web" in asset_name or "frontend" in asset_name:
            return "web_tier"
        elif "api" in asset_name or "service" in asset_name:
            return "application_tier"
        elif "database" in asset_type or "db" in asset_type:
            return "data_tier"
        elif "server" in asset_type:
            return "infrastructure"
        else:
            return "standalone"

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
