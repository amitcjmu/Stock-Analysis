"""
Core dependency analysis logic.

This module contains the DependencyAnalyzer class which provides
comprehensive dependency analysis capabilities for asset migration.
"""

from typing import Any, Dict, List
from datetime import datetime

from .base import (
    logger,
    ASSET_TYPE_DATABASE,
    ASSET_TYPE_APPLICATION,
    ASSET_TYPE_LOAD_BALANCER,
    ASSET_TYPE_SECURITY_GROUP,
    FLOW_TYPE_READ_WRITE,
)
from .graph_builders import DependencyGraphBuilder
from .wave_planners import CriticalPathAnalyzer, MigrationInsightsGenerator


class DependencyAnalyzer:
    """Core dependency analysis logic"""

    @staticmethod
    def analyze_dependencies(
        assets: List[Dict[str, Any]], context_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze dependencies between assets based on various indicators

        Args:
            assets: List of asset records with potential dependency information
            context_info: Optional context with client/engagement info

        Returns:
            Comprehensive dependency analysis results
        """
        try:
            logger.info(f"🔍 Analyzing dependencies for {len(assets)} assets")

            if not assets:
                return DependencyAnalyzer._create_empty_analysis("No assets provided")

            # Analyze different types of dependencies
            network_deps = DependencyAnalyzer._analyze_network_dependencies(assets)
            config_deps = DependencyAnalyzer._analyze_configuration_dependencies(assets)
            data_deps = DependencyAnalyzer._analyze_data_dependencies(assets)
            service_deps = DependencyAnalyzer._analyze_service_dependencies(assets)

            # Build dependency graph
            dependency_graph = DependencyGraphBuilder.build_dependency_graph(
                assets, network_deps, config_deps, data_deps, service_deps
            )

            # Analyze critical paths and bottlenecks
            critical_analysis = CriticalPathAnalyzer.analyze_critical_paths(
                dependency_graph
            )

            # Generate migration insights
            migration_insights = MigrationInsightsGenerator.generate_migration_insights(
                dependency_graph, critical_analysis
            )

            # Generate wave planning recommendations
            wave_recommendations = (
                MigrationInsightsGenerator.generate_wave_planning_recommendations(
                    dependency_graph, critical_analysis
                )
            )

            return {
                "success": True,
                "asset_count": len(assets),
                "dependency_summary": {
                    "network_dependencies": len(network_deps),
                    "configuration_dependencies": len(config_deps),
                    "data_dependencies": len(data_deps),
                    "service_dependencies": len(service_deps),
                },
                "dependency_graph": dependency_graph,
                "critical_analysis": critical_analysis,
                "migration_insights": migration_insights,
                "wave_planning": wave_recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "context": context_info or {},
            }

        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {str(e)}")
            return DependencyAnalyzer._create_empty_analysis(
                f"Analysis failed: {str(e)}"
            )

    @staticmethod
    def _create_empty_analysis(error: str = None) -> Dict[str, Any]:
        """Create empty analysis result for error cases"""
        return {
            "success": False,
            "error": error,
            "asset_count": 0,
            "dependency_summary": {
                "network_dependencies": 0,
                "configuration_dependencies": 0,
                "data_dependencies": 0,
                "service_dependencies": 0,
            },
            "dependency_graph": {
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0,
            },
            "critical_analysis": {
                "bottlenecks": [],
                "circular_dependencies": [],
                "critical_paths": [],
            },
            "migration_insights": [],
            "wave_planning": {"total_waves": 1, "wave_strategy": "single_wave"},
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _analyze_network_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze network-based dependencies between assets"""
        dependencies = []

        for asset in assets:
            asset_id = str(asset.get("id", ""))
            connections = []

            # Check for explicit IP/hostname references
            for field in ["ip_address", "hostname", "server_name", "host"]:
                if field in asset and asset[field]:
                    value = str(asset[field]).strip()
                    if value and "." in value:  # Basic IP/hostname check
                        connections.append(
                            {
                                "type": "explicit",
                                "field": field,
                                "value": value,
                                "confidence": 0.9,
                            }
                        )

            # Check configuration fields for network references
            for field in ["configuration", "network_config", "dns_config"]:
                if field in asset and isinstance(asset[field], (str, dict)):
                    config_text = str(asset[field])
                    # Simple pattern matching for IP addresses
                    import re

                    ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
                    ips = re.findall(ip_pattern, config_text)
                    for ip in ips:
                        connections.append(
                            {
                                "type": "inferred",
                                "field": field,
                                "value": ip,
                                "confidence": 0.6,
                            }
                        )

            if connections:
                dependencies.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset.get("name", "Unknown"),
                        "connections": connections,
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_configuration_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze configuration-based dependencies"""
        dependencies = []

        for asset in assets:
            asset_id = str(asset.get("id", ""))
            references = []

            # Check for database connections in applications
            if asset.get("asset_type") == ASSET_TYPE_APPLICATION:
                for field in ["database_url", "db_host", "data_source"]:
                    if field in asset and asset[field]:
                        references.append(
                            {
                                "type": "database_connection",
                                "field": field,
                                "value": str(asset[field]),
                                "confidence": 0.8,
                            }
                        )

            # Check for service URLs and endpoints
            for field in ["service_url", "api_endpoint", "external_service"]:
                if field in asset and asset[field]:
                    references.append(
                        {
                            "type": "service_reference",
                            "field": field,
                            "value": str(asset[field]),
                            "confidence": 0.7,
                        }
                    )

            if references:
                dependencies.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset.get("name", "Unknown"),
                        "references": references,
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_data_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze data flow dependencies"""
        dependencies = []

        # Find applications and databases
        applications = [
            a for a in assets if a.get("asset_type") == ASSET_TYPE_APPLICATION
        ]
        databases = [a for a in assets if a.get("asset_type") == ASSET_TYPE_DATABASE]

        for app in applications:
            asset_id = str(app.get("id", ""))
            data_flows = []

            # Check for likely database connections
            for db in databases:
                if DependencyAnalyzer._is_likely_connected(app, db):
                    data_flows.append(
                        {
                            "source": db.get("name", "Unknown"),
                            "target": app.get("name", "Unknown"),
                            "flow_type": FLOW_TYPE_READ_WRITE,
                            "confidence": 0.7,
                        }
                    )

            if data_flows:
                dependencies.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": app.get("name", "Unknown"),
                        "data_flows": data_flows,
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_service_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze service-level dependencies"""
        dependencies = []

        for asset in assets:
            asset_id = str(asset.get("id", ""))
            services = []

            # Check for load balancer relationships
            if asset.get("asset_type") == ASSET_TYPE_LOAD_BALANCER:
                # Load balancers typically serve applications
                for other_asset in assets:
                    if other_asset.get(
                        "asset_type"
                    ) == ASSET_TYPE_APPLICATION and other_asset.get(
                        "environment"
                    ) == asset.get(
                        "environment"
                    ):
                        services.append(
                            {
                                "service": other_asset.get("name", "Unknown"),
                                "type": "explicit",
                                "relationship": "serves",
                                "confidence": 0.8,
                            }
                        )

            # Check for security group relationships
            elif asset.get("asset_type") == ASSET_TYPE_SECURITY_GROUP:
                # Security groups typically protect other assets
                for other_asset in assets:
                    if other_asset.get("environment") == asset.get("environment"):
                        services.append(
                            {
                                "service": other_asset.get("name", "Unknown"),
                                "type": "inferred",
                                "relationship": "protects",
                                "confidence": 0.6,
                            }
                        )

            if services:
                dependencies.append(
                    {
                        "asset_id": asset_id,
                        "asset_name": asset.get("name", "Unknown"),
                        "services": services,
                    }
                )

        return dependencies

    @staticmethod
    def _is_likely_connected(app: Dict[str, Any], db: Dict[str, Any]) -> bool:
        """Determine if an application is likely connected to a database"""
        # Same environment indicates higher likelihood
        if app.get("environment") == db.get("environment"):
            return True

        # Check for name patterns
        app_name = app.get("name", "").lower()
        db_name = db.get("name", "").lower()

        # Simple heuristics for connection likelihood
        if any(word in app_name for word in db_name.split()) or any(
            word in db_name for word in app_name.split()
        ):
            return True

        return False
