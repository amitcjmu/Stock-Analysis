"""
Topology Mapping Tools for Dependency Analysis Crews
Provides specialized tools for mapping application and infrastructure topology
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TopologyMappingTool(BaseTool):
    name: str = "topology_mapping_tool"
    description: str = "Maps application topology and hosting relationships between applications and infrastructure"
    
    def _run(self, topology_data: str) -> str:
        """
        Map application topology and hosting relationships
        
        Args:
            topology_data: JSON string containing applications and infrastructure data
            
        Returns:
            JSON string with topology mapping results
        """
        try:
            data = json.loads(topology_data)
            applications = data.get("applications", [])
            servers = data.get("servers", [])
            
            topology_results = {
                "hosting_relationships": self._map_hosting_relationships(applications, servers),
                "application_tiers": self._identify_application_tiers(applications),
                "network_topology": self._analyze_network_topology(applications, servers),
                "dependency_chains": self._build_dependency_chains(applications, servers),
                "topology_insights": self._generate_topology_insights(applications, servers)
            }
            
            return json.dumps(topology_results)
            
        except Exception as e:
            logger.error(f"Error in topology mapping: {e}")
            return json.dumps({"error": str(e)})
    
    def _map_hosting_relationships(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map which applications are hosted on which servers"""
        relationships = []
        
        for app in applications:
            app_name = app.get("name", "")
            
            # Try to find hosting server through various methods
            hosting_server = self._find_hosting_server(app, servers)
            
            if hosting_server:
                relationships.append({
                    "application": app_name,
                    "hosted_on": hosting_server["name"],
                    "hosting_type": self._determine_hosting_type(app, hosting_server),
                    "confidence": self._calculate_hosting_confidence(app, hosting_server)
                })
            else:
                relationships.append({
                    "application": app_name,
                    "hosted_on": "unknown",
                    "hosting_type": "unidentified",
                    "confidence": 0.0
                })
        
        return relationships
    
    def _find_hosting_server(self, app: Dict[str, Any], servers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the server hosting a specific application"""
        app_name = app.get("name", "").lower()
        app_ip = app.get("ip_address", "")
        
        # Method 1: Direct IP match
        for server in servers:
            server_ip = server.get("ip_address", "")
            if app_ip and server_ip and app_ip == server_ip:
                return server
        
        # Method 2: Hostname/name similarity
        for server in servers:
            server_name = server.get("name", "").lower()
            if app_name and server_name:
                if app_name in server_name or server_name in app_name:
                    return server
        
        # Method 3: Environment and location matching
        app_env = app.get("environment", "")
        app_location = app.get("location", "")
        
        for server in servers:
            server_env = server.get("environment", "")
            server_location = server.get("location", "")
            
            env_match = app_env and server_env and app_env == server_env
            location_match = app_location and server_location and app_location == server_location
            
            if env_match and location_match:
                return server
        
        return None
    
    def _determine_hosting_type(self, app: Dict[str, Any], server: Dict[str, Any]) -> str:
        """Determine the type of hosting relationship"""
        app_info = str(app).lower()
        server_info = str(server).lower()
        
        if any(indicator in app_info or indicator in server_info for indicator in ["docker", "container"]):
            return "containerized"
        elif any(indicator in app_info or indicator in server_info for indicator in ["vm", "virtual"]):
            return "virtualized"
        elif any(indicator in app_info or indicator in server_info for indicator in ["cloud", "aws", "azure"]):
            return "cloud_hosted"
        else:
            return "direct_hosted"
    
    def _calculate_hosting_confidence(self, app: Dict[str, Any], server: Dict[str, Any]) -> float:
        """Calculate confidence score for hosting relationship"""
        confidence = 0.5
        
        # IP address match gives highest confidence
        if app.get("ip_address") == server.get("ip_address"):
            confidence = 0.95
        # Name similarity gives medium confidence
        elif app.get("name", "").lower() in server.get("name", "").lower():
            confidence = 0.8
        # Environment and location match gives lower confidence
        elif (app.get("environment") == server.get("environment") and 
              app.get("location") == server.get("location")):
            confidence = 0.6
        
        return confidence
    
    def _identify_application_tiers(self, applications: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify application architecture tiers"""
        tiers = {
            "presentation_tier": [],
            "application_tier": [],
            "data_tier": [],
            "integration_tier": [],
            "unknown_tier": []
        }
        
        for app in applications:
            app_name = app.get("name", "")
            app_info = str(app).lower()
            
            # Classify into tiers based on application characteristics
            if any(indicator in app_info for indicator in ["web", "frontend", "ui", "portal"]):
                tiers["presentation_tier"].append(app_name)
            elif any(indicator in app_info for indicator in ["api", "service", "business", "logic"]):
                tiers["application_tier"].append(app_name)
            elif any(indicator in app_info for indicator in ["database", "db", "data", "storage"]):
                tiers["data_tier"].append(app_name)
            elif any(indicator in app_info for indicator in ["middleware", "integration", "message", "queue"]):
                tiers["integration_tier"].append(app_name)
            else:
                tiers["unknown_tier"].append(app_name)
        
        return tiers
    
    def _analyze_network_topology(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network topology patterns"""
        network_analysis = {
            "subnets": self._identify_subnets(applications + servers),
            "network_zones": self._identify_network_zones(applications + servers),
            "connectivity_patterns": self._analyze_connectivity_patterns(applications, servers)
        }
        
        return network_analysis
    
    def _identify_subnets(self, assets: List[Dict[str, Any]]) -> List[str]:
        """Identify network subnets from asset IP addresses"""
        subnets = set()
        
        for asset in assets:
            ip = asset.get("ip_address", "")
            if ip and "." in ip:
                # Simple subnet identification (first 3 octets)
                subnet = ".".join(ip.split(".")[:3]) + ".0/24"
                subnets.add(subnet)
        
        return list(subnets)
    
    def _identify_network_zones(self, assets: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify network security zones"""
        zones = {
            "dmz": [],
            "internal": [],
            "database": [],
            "management": []
        }
        
        for asset in assets:
            asset_name = asset.get("name", "")
            asset_info = str(asset).lower()
            
            if any(indicator in asset_info for indicator in ["dmz", "external", "public"]):
                zones["dmz"].append(asset_name)
            elif any(indicator in asset_info for indicator in ["database", "db", "data"]):
                zones["database"].append(asset_name)
            elif any(indicator in asset_info for indicator in ["mgmt", "management", "admin"]):
                zones["management"].append(asset_name)
            else:
                zones["internal"].append(asset_name)
        
        return zones
    
    def _analyze_connectivity_patterns(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze connectivity patterns between assets"""
        patterns = {
            "north_south_traffic": self._identify_north_south_traffic(applications),
            "east_west_traffic": self._identify_east_west_traffic(applications),
            "communication_protocols": self._identify_protocols(applications + servers)
        }
        
        return patterns
    
    def _build_dependency_chains(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build dependency chains showing how applications depend on each other"""
        chains = []
        
        # Simple dependency chain building based on tier analysis
        tiers = self._identify_application_tiers(applications)
        
        # Build chains from presentation -> application -> data
        for web_app in tiers["presentation_tier"]:
            chain = {
                "chain_id": f"chain_{len(chains) + 1}",
                "components": [web_app],
                "flow_type": "user_request"
            }
            
            # Add application tier dependencies
            if tiers["application_tier"]:
                chain["components"].append(tiers["application_tier"][0])  # Simplified
            
            # Add data tier dependencies
            if tiers["data_tier"]:
                chain["components"].append(tiers["data_tier"][0])  # Simplified
            
            chains.append(chain)
        
        return chains
    
    def _generate_topology_insights(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about the topology"""
        insights = {
            "complexity_assessment": self._assess_topology_complexity(applications, servers),
            "migration_considerations": self._identify_migration_considerations(applications, servers),
            "optimization_opportunities": self._identify_optimization_opportunities(applications, servers)
        }
        
        return insights
    
    def _assess_topology_complexity(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> str:
        """Assess overall topology complexity"""
        total_assets = len(applications) + len(servers)
        tiers = self._identify_application_tiers(applications)
        tier_count = sum(1 for tier_apps in tiers.values() if tier_apps)
        
        if total_assets > 50 and tier_count > 2:
            return "high"
        elif total_assets > 20 or tier_count > 1:
            return "medium"
        else:
            return "low"
    
    def _identify_migration_considerations(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> List[str]:
        """Identify key migration considerations based on topology"""
        considerations = []
        
        tiers = self._identify_application_tiers(applications)
        
        if len(tiers["data_tier"]) > 1:
            considerations.append("Multiple databases require data migration coordination")
        
        if len(tiers["integration_tier"]) > 0:
            considerations.append("Integration middleware requires careful migration sequencing")
        
        if len(applications) > len(servers) * 2:
            considerations.append("High application density may indicate shared hosting concerns")
        
        return considerations
    
    def _identify_optimization_opportunities(self, applications: List[Dict[str, Any]], servers: List[Dict[str, Any]]) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Check for containerization opportunities
        containerizable_apps = sum(1 for app in applications 
                                 if "legacy" not in str(app).lower())
        
        if containerizable_apps > len(applications) * 0.5:
            opportunities.append("High potential for containerization")
        
        # Check for microservices opportunities
        service_oriented_apps = sum(1 for app in applications 
                                  if any(indicator in str(app).lower() 
                                        for indicator in ["api", "service"]))
        
        if service_oriented_apps > 3:
            opportunities.append("Microservices architecture potential")
        
        return opportunities
    
    def _identify_north_south_traffic(self, applications: List[Dict[str, Any]]) -> List[str]:
        """Identify applications with north-south traffic patterns"""
        return [app.get("name", "") for app in applications 
                if any(indicator in str(app).lower() 
                      for indicator in ["web", "api", "portal", "frontend"])]
    
    def _identify_east_west_traffic(self, applications: List[Dict[str, Any]]) -> List[str]:
        """Identify applications with east-west traffic patterns"""
        return [app.get("name", "") for app in applications 
                if any(indicator in str(app).lower() 
                      for indicator in ["service", "middleware", "integration"])]
    
    def _identify_protocols(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify communication protocols in use"""
        protocols = {}
        
        for asset in assets:
            asset_info = str(asset).lower()
            
            if any(indicator in asset_info for indicator in ["http", "web"]):
                protocols["HTTP"] = protocols.get("HTTP", 0) + 1
            if any(indicator in asset_info for indicator in ["https", "ssl"]):
                protocols["HTTPS"] = protocols.get("HTTPS", 0) + 1
            if any(indicator in asset_info for indicator in ["database", "sql"]):
                protocols["Database"] = protocols.get("Database", 0) + 1
        
        return protocols

class HostingAnalysisTool(BaseTool):
    name: str = "hosting_analysis_tool"
    description: str = "Analyzes hosting patterns and resource utilization relationships"
    
    def _run(self, hosting_data: str) -> str:
        """
        Analyze hosting patterns and resource relationships
        
        Args:
            hosting_data: JSON string containing hosting relationship data
            
        Returns:
            JSON string with hosting analysis results
        """
        try:
            data = json.loads(hosting_data)
            
            analysis_results = {
                "hosting_patterns": self._analyze_hosting_patterns(data),
                "resource_utilization": self._analyze_resource_utilization(data),
                "consolidation_opportunities": self._identify_consolidation_opportunities(data),
                "hosting_risks": self._assess_hosting_risks(data)
            }
            
            return json.dumps(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in hosting analysis: {e}")
            return json.dumps({"error": str(e)})
    
    def _analyze_hosting_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze hosting deployment patterns"""
        relationships = data.get("hosting_relationships", [])
        
        patterns = {
            "hosting_types": {},
            "apps_per_server": {},
            "shared_hosting_count": 0,
            "dedicated_hosting_count": 0
        }
        
        # Count hosting types
        for rel in relationships:
            hosting_type = rel.get("hosting_type", "unknown")
            patterns["hosting_types"][hosting_type] = patterns["hosting_types"].get(hosting_type, 0) + 1
        
        # Analyze apps per server
        server_app_count = {}
        for rel in relationships:
            server = rel.get("hosted_on", "unknown")
            server_app_count[server] = server_app_count.get(server, 0) + 1
        
        for server, count in server_app_count.items():
            patterns["apps_per_server"][server] = count
            if count > 1:
                patterns["shared_hosting_count"] += 1
            else:
                patterns["dedicated_hosting_count"] += 1
        
        return patterns
    
    def _analyze_resource_utilization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        return {
            "analysis_type": "resource_utilization",
            "note": "Detailed resource analysis requires performance monitoring data",
            "placeholder_metrics": {
                "average_cpu_utilization": "unknown",
                "memory_utilization": "unknown",
                "storage_utilization": "unknown"
            }
        }
    
    def _identify_consolidation_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify opportunities for server consolidation"""
        opportunities = []
        relationships = data.get("hosting_relationships", [])
        
        # Group by server
        server_apps = {}
        for rel in relationships:
            server = rel.get("hosted_on", "unknown")
            if server not in server_apps:
                server_apps[server] = []
            server_apps[server].append(rel.get("application"))
        
        # Identify underutilized servers
        for server, apps in server_apps.items():
            if len(apps) == 1 and server != "unknown":
                opportunities.append({
                    "type": "consolidation_candidate",
                    "server": server,
                    "applications": apps,
                    "reasoning": "Single application server could be consolidated"
                })
        
        return opportunities
    
    def _assess_hosting_risks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess risks in current hosting configuration"""
        risks = []
        relationships = data.get("hosting_relationships", [])
        
        # Check for unknown hosting
        unknown_hosting = [rel for rel in relationships if rel.get("hosted_on") == "unknown"]
        if unknown_hosting:
            risks.append({
                "risk_type": "unknown_hosting",
                "severity": "medium",
                "description": f"{len(unknown_hosting)} applications have unknown hosting",
                "affected_applications": [rel.get("application") for rel in unknown_hosting]
            })
        
        # Check for low confidence relationships
        low_confidence = [rel for rel in relationships if rel.get("confidence", 0) < 0.5]
        if low_confidence:
            risks.append({
                "risk_type": "low_confidence_mapping",
                "severity": "low",
                "description": f"{len(low_confidence)} hosting relationships have low confidence",
                "affected_relationships": len(low_confidence)
            })
        
        return risks 