"""
Server Classification Tools for Inventory Building Crew
Provides specialized tools for server and infrastructure classification
"""

import json
import logging
from typing import Any, Dict, List, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ServerClassificationTool(BaseTool):
    name: str = "server_classification_tool"
    description: str = "Classifies servers and infrastructure assets based on technical characteristics"
    
    def _run(self, asset_data: str) -> str:
        """
        Classify server assets based on their characteristics
        
        Args:
            asset_data: JSON string containing asset information
            
        Returns:
            JSON string with server classification results
        """
        try:
            data = json.loads(asset_data)
            
            classification_results = {}
            server_types = {
                "physical_server": ["physical", "bare_metal", "hardware"],
                "virtual_server": ["virtual", "vm", "vmware", "hyper-v"],
                "cloud_instance": ["aws", "azure", "gcp", "cloud", "ec2"],
                "container": ["docker", "kubernetes", "k8s", "container"],
                "database_server": ["database", "db", "sql", "oracle", "mysql"],
                "web_server": ["web", "apache", "nginx", "iis", "tomcat"],
                "application_server": ["app", "application", "jboss", "websphere"]
            }
            
            for asset in data.get("assets", []):
                asset_name = asset.get("name", "unknown")
                asset_info = str(asset).lower()
                
                # Classify based on keywords and patterns
                classified_type = "generic_server"
                confidence = 0.5
                characteristics = []
                
                for server_type, keywords in server_types.items():
                    if any(keyword in asset_info for keyword in keywords):
                        classified_type = server_type
                        confidence = 0.8
                        characteristics.append(f"Matched {server_type} keywords")
                        break
                
                # Additional classification logic
                os_info = asset.get("operating_system", "").lower()
                if "windows" in os_info:
                    characteristics.append("Windows-based")
                elif "linux" in os_info or "unix" in os_info:
                    characteristics.append("Unix/Linux-based")
                
                classification_results[asset_name] = {
                    "type": classified_type,
                    "confidence": confidence,
                    "characteristics": characteristics,
                    "technical_specs": self._extract_technical_specs(asset)
                }
            
            return json.dumps({
                "server_classifications": classification_results,
                "summary": {
                    "total_servers": len(classification_results),
                    "classification_distribution": self._get_type_distribution(classification_results)
                }
            })
            
        except Exception as e:
            logger.error(f"Error in server classification: {e}")
            return json.dumps({"error": str(e)})
    
    def _extract_technical_specs(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical specifications from asset data"""
        specs = {}
        
        # Common technical fields
        tech_fields = ["cpu", "memory", "disk", "storage", "ram", "cores", "vcpu"]
        for field in tech_fields:
            for key, value in asset.items():
                if field in key.lower() and value:
                    specs[field] = value
        
        return specs
    
    def _get_type_distribution(self, classifications: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution of server types"""
        distribution = {}
        for asset_info in classifications.values():
            server_type = asset_info["type"]
            distribution[server_type] = distribution.get(server_type, 0) + 1
        return distribution

class InfrastructureAnalysisTool(BaseTool):
    name: str = "infrastructure_analysis_tool"
    description: str = "Analyzes infrastructure patterns and relationships"
    
    def _run(self, infrastructure_data: str) -> str:
        """
        Analyze infrastructure patterns and relationships
        
        Args:
            infrastructure_data: JSON string with infrastructure asset data
            
        Returns:
            JSON string with infrastructure analysis results
        """
        try:
            data = json.loads(infrastructure_data)
            assets = data.get("assets", [])
            
            analysis_results = {
                "infrastructure_patterns": self._analyze_patterns(assets),
                "capacity_analysis": self._analyze_capacity(assets),
                "technology_stack": self._analyze_technology_stack(assets),
                "risk_assessment": self._assess_infrastructure_risks(assets)
            }
            
            return json.dumps(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in infrastructure analysis: {e}")
            return json.dumps({"error": str(e)})
    
    def _analyze_patterns(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze infrastructure deployment patterns"""
        patterns = {
            "naming_conventions": self._detect_naming_patterns(assets),
            "environment_distribution": self._analyze_environments(assets),
            "location_distribution": self._analyze_locations(assets)
        }
        return patterns
    
    def _analyze_capacity(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze infrastructure capacity"""
        total_servers = len(assets)
        
        capacity_metrics = {
            "total_assets": total_servers,
            "average_age": self._calculate_average_age(assets),
            "capacity_utilization": "unknown"  # Placeholder
        }
        return capacity_metrics
    
    def _analyze_technology_stack(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technology stack distribution"""
        os_distribution = {}
        for asset in assets:
            os = asset.get("operating_system", "unknown")
            os_distribution[os] = os_distribution.get(os, 0) + 1
        
        return {
            "operating_systems": os_distribution,
            "technology_diversity": len(os_distribution)
        }
    
    def _assess_infrastructure_risks(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess infrastructure-related migration risks"""
        risks = []
        
        if len(assets) > 100:
            risks.append("Large infrastructure scope may increase migration complexity")
        
        legacy_count = sum(1 for asset in assets if self._is_legacy_system(asset))
        if legacy_count > len(assets) * 0.3:
            risks.append("High percentage of legacy systems detected")
        
        return {
            "risk_factors": risks,
            "legacy_system_count": legacy_count,
            "risk_level": "high" if len(risks) > 2 else "medium" if risks else "low"
        }
    
    def _detect_naming_patterns(self, assets: List[Dict[str, Any]]) -> List[str]:
        """Detect naming convention patterns"""
        patterns = []
        names = [asset.get("name", "") for asset in assets if asset.get("name")]
        
        if any("-" in name for name in names):
            patterns.append("hyphen-separated")
        if any("." in name for name in names):
            patterns.append("dot-separated")
        if any(name.startswith(("srv", "server")) for name in names):
            patterns.append("srv-prefix")
        
        return patterns
    
    def _analyze_environments(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze environment distribution"""
        env_distribution = {}
        for asset in assets:
            env = asset.get("environment", "unknown")
            env_distribution[env] = env_distribution.get(env, 0) + 1
        return env_distribution
    
    def _analyze_locations(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze location distribution"""
        location_distribution = {}
        for asset in assets:
            location = asset.get("location", "unknown")
            location_distribution[location] = location_distribution.get(location, 0) + 1
        return location_distribution
    
    def _calculate_average_age(self, assets: List[Dict[str, Any]]) -> float:
        """Calculate average age of infrastructure"""
        # Placeholder - would need actual age/install date data
        return 5.0
    
    def _is_legacy_system(self, asset: Dict[str, Any]) -> bool:
        """Determine if system is legacy based on characteristics"""
        os = asset.get("operating_system", "").lower()
        legacy_indicators = ["windows 2008", "windows 2003", "windows xp", "centos 6", "rhel 6"]
        return any(indicator in os for indicator in legacy_indicators) 