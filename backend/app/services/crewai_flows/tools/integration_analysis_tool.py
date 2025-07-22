"""
Integration Analysis Tools for App-App Dependency Crew
Provides specialized tools for analyzing application integration patterns and dependencies
"""

import json
import logging
from typing import Any, Dict, List, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class IntegrationAnalysisTool(BaseTool):
    name: str = "integration_analysis_tool"
    description: str = "Analyzes integration patterns and communication between applications"
    
    def _run(self, integration_data: str) -> str:
        """
        Analyze integration patterns between applications
        
        Args:
            integration_data: JSON string containing application integration information
            
        Returns:
            JSON string with integration analysis results
        """
        try:
            data = json.loads(integration_data)
            applications = data.get("applications", [])
            
            analysis_results = {
                "integration_patterns": self._analyze_integration_patterns(applications),
                "communication_flows": self._map_communication_flows(applications),
                "integration_complexity": self._assess_integration_complexity(applications),
                "modernization_opportunities": self._identify_modernization_opportunities(applications)
            }
            
            return json.dumps(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in integration analysis: {e}")
            return json.dumps({"error": str(e)})
    
    def _analyze_integration_patterns(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze integration architecture patterns"""
        patterns = {
            "point_to_point": 0,
            "hub_and_spoke": 0,
            "enterprise_service_bus": 0,
            "microservices_mesh": 0,
            "api_gateway": 0,
            "message_queue": 0
        }
        
        integration_keywords = {
            "point_to_point": ["direct", "point-to-point", "p2p"],
            "hub_and_spoke": ["hub", "spoke", "central"],
            "enterprise_service_bus": ["esb", "service_bus", "middleware"],
            "microservices_mesh": ["mesh", "microservice", "service_mesh"],
            "api_gateway": ["gateway", "api_gateway", "proxy"],
            "message_queue": ["queue", "kafka", "rabbitmq", "activemq", "message"]
        }
        
        for app in applications:
            app_info = str(app).lower()
            
            for pattern, keywords in integration_keywords.items():
                if any(keyword in app_info for keyword in keywords):
                    patterns[pattern] += 1
        
        # Determine dominant pattern
        dominant_pattern = max(patterns, key=patterns.get) if any(patterns.values()) else "unknown"
        
        return {
            "pattern_counts": patterns,
            "dominant_pattern": dominant_pattern,
            "pattern_distribution": self._calculate_pattern_distribution(patterns)
        }
    
    def _map_communication_flows(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map communication flows between applications"""
        flows = []
        
        # Identify potential communication based on application types and tiers
        api_providers = []
        api_consumers = []
        databases = []
        
        for app in applications:
            app_name = app.get("name", "")
            app_info = str(app).lower()
            
            if any(indicator in app_info for indicator in ["api", "service", "rest"]):
                api_providers.append(app_name)
            
            if any(indicator in app_info for indicator in ["web", "frontend", "client"]):
                api_consumers.append(app_name)
            
            if any(indicator in app_info for indicator in ["database", "db", "data"]):
                databases.append(app_name)
        
        # Map potential flows
        for consumer in api_consumers:
            for provider in api_providers:
                if consumer != provider:
                    flows.append({
                        "source": consumer,
                        "target": provider,
                        "flow_type": "api_call",
                        "confidence": 0.6,
                        "protocol": "HTTP/REST"
                    })
        
        for app in api_providers + api_consumers:
            for db in databases:
                flows.append({
                    "source": app,
                    "target": db,
                    "flow_type": "data_access",
                    "confidence": 0.7,
                    "protocol": "Database"
                })
        
        return flows
    
    def _assess_integration_complexity(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall integration complexity"""
        app_count = len(applications)
        
        # Count potential integration points
        api_apps = sum(1 for app in applications 
                      if any(indicator in str(app).lower() 
                            for indicator in ["api", "service", "integration"]))
        
        databases = sum(1 for app in applications 
                       if any(indicator in str(app).lower() 
                             for indicator in ["database", "db"]))
        
        # Calculate complexity score
        complexity_score = (api_apps * 2 + databases * 1.5 + app_count * 0.5) / 10
        
        if complexity_score > 5:
            complexity_level = "high"
        elif complexity_score > 2:
            complexity_level = "medium"
        else:
            complexity_level = "low"
        
        return {
            "complexity_level": complexity_level,
            "complexity_score": complexity_score,
            "api_integration_count": api_apps,
            "database_integration_count": databases,
            "total_applications": app_count
        }
    
    def _identify_modernization_opportunities(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify opportunities for integration modernization"""
        opportunities = []
        
        # Check for legacy integration patterns
        legacy_count = sum(1 for app in applications 
                          if any(indicator in str(app).lower() 
                                for indicator in ["legacy", "mainframe", "cobol"]))
        
        if legacy_count > 0:
            opportunities.append({
                "opportunity": "legacy_modernization",
                "description": f"{legacy_count} legacy applications could benefit from API modernization",
                "priority": "high"
            })
        
        # Check for API gateway opportunities
        api_count = sum(1 for app in applications 
                       if any(indicator in str(app).lower() 
                             for indicator in ["api", "rest", "service"]))
        
        if api_count > 3:
            opportunities.append({
                "opportunity": "api_gateway_implementation",
                "description": f"{api_count} APIs could benefit from centralized gateway",
                "priority": "medium"
            })
        
        # Check for microservices opportunities
        monolith_indicators = sum(1 for app in applications 
                                 if "monolith" in str(app).lower())
        
        if monolith_indicators > 0:
            opportunities.append({
                "opportunity": "microservices_decomposition",
                "description": f"{monolith_indicators} monolithic applications could be decomposed",
                "priority": "medium"
            })
        
        return opportunities
    
    def _calculate_pattern_distribution(self, patterns: Dict[str, int]) -> Dict[str, float]:
        """Calculate percentage distribution of integration patterns"""
        total = sum(patterns.values())
        if total == 0:
            return {pattern: 0.0 for pattern in patterns}
        
        return {pattern: (count / total) * 100 for pattern, count in patterns.items()}

class APIAnalysisTool(BaseTool):
    name: str = "api_analysis_tool"
    description: str = "Analyzes API characteristics and service dependencies"
    
    def _run(self, api_data: str) -> str:
        """
        Analyze API characteristics and dependencies
        
        Args:
            api_data: JSON string containing API and service information
            
        Returns:
            JSON string with API analysis results
        """
        try:
            data = json.loads(api_data)
            applications = data.get("applications", [])
            
            analysis_results = {
                "api_inventory": self._build_api_inventory(applications),
                "api_dependencies": self._map_api_dependencies(applications),
                "api_characteristics": self._analyze_api_characteristics(applications),
                "service_mesh_readiness": self._assess_service_mesh_readiness(applications)
            }
            
            return json.dumps(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in API analysis: {e}")
            return json.dumps({"error": str(e)})
    
    def _build_api_inventory(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build inventory of APIs and services"""
        api_inventory = []
        
        for app in applications:
            app_name = app.get("name", "")
            app_info = str(app).lower()
            
            if any(indicator in app_info for indicator in ["api", "service", "rest", "soap"]):
                api_type = "REST" if "rest" in app_info else "SOAP" if "soap" in app_info else "Unknown"
                
                api_inventory.append({
                    "service_name": app_name,
                    "api_type": api_type,
                    "protocol": self._determine_protocol(app_info),
                    "authentication": self._determine_auth_method(app_info),
                    "data_format": self._determine_data_format(app_info),
                    "versioning": self._has_versioning(app_info),
                    "documentation": self._has_documentation(app_info)
                })
        
        return api_inventory
    
    def _map_api_dependencies(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map dependencies between APIs and services"""
        dependencies = []
        
        # Build lists of different application types
        api_services = [app for app in applications 
                       if any(indicator in str(app).lower() 
                             for indicator in ["api", "service"])]
        
        web_apps = [app for app in applications 
                   if any(indicator in str(app).lower() 
                         for indicator in ["web", "frontend", "ui"])]
        
        databases = [app for app in applications 
                    if any(indicator in str(app).lower() 
                          for indicator in ["database", "db"])]
        
        # Map web app -> API dependencies
        for web_app in web_apps:
            for api_service in api_services:
                dependencies.append({
                    "consumer": web_app.get("name", ""),
                    "provider": api_service.get("name", ""),
                    "dependency_type": "api_consumption",
                    "criticality": self._assess_dependency_criticality(web_app, api_service),
                    "protocol": "HTTP"
                })
        
        # Map API -> Database dependencies
        for api_service in api_services:
            for database in databases:
                dependencies.append({
                    "consumer": api_service.get("name", ""),
                    "provider": database.get("name", ""),
                    "dependency_type": "data_access",
                    "criticality": "high",
                    "protocol": "Database"
                })
        
        return dependencies
    
    def _analyze_api_characteristics(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze characteristics of APIs in the environment"""
        api_apps = [app for app in applications 
                   if any(indicator in str(app).lower() 
                         for indicator in ["api", "service"])]
        
        characteristics = {
            "total_apis": len(api_apps),
            "rest_apis": sum(1 for app in api_apps if "rest" in str(app).lower()),
            "soap_apis": sum(1 for app in api_apps if "soap" in str(app).lower()),
            "secured_apis": sum(1 for app in api_apps if any(indicator in str(app).lower() 
                                                           for indicator in ["auth", "oauth", "jwt"])),
            "documented_apis": sum(1 for app in api_apps if any(indicator in str(app).lower() 
                                                              for indicator in ["swagger", "openapi", "doc"])),
            "versioned_apis": sum(1 for app in api_apps if any(indicator in str(app).lower() 
                                                             for indicator in ["v1", "v2", "version"]))
        }
        
        # Calculate API maturity score
        if characteristics["total_apis"] > 0:
            maturity_score = (
                (characteristics["rest_apis"] / characteristics["total_apis"]) * 0.3 +
                (characteristics["secured_apis"] / characteristics["total_apis"]) * 0.3 +
                (characteristics["documented_apis"] / characteristics["total_apis"]) * 0.2 +
                (characteristics["versioned_apis"] / characteristics["total_apis"]) * 0.2
            )
        else:
            maturity_score = 0.0
        
        characteristics["api_maturity_score"] = maturity_score
        characteristics["maturity_level"] = self._get_maturity_level(maturity_score)
        
        return characteristics
    
    def _assess_service_mesh_readiness(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess readiness for service mesh implementation"""
        api_services = [app for app in applications 
                       if any(indicator in str(app).lower() 
                             for indicator in ["api", "service", "microservice"])]
        
        readiness_factors = {
            "microservices_count": len(api_services),
            "containerized_services": sum(1 for app in api_services 
                                        if any(indicator in str(app).lower() 
                                              for indicator in ["docker", "container", "k8s"])),
            "cloud_native_services": sum(1 for app in api_services 
                                       if any(indicator in str(app).lower() 
                                             for indicator in ["cloud", "kubernetes", "aws", "azure"])),
            "service_discovery_present": sum(1 for app in api_services 
                                           if any(indicator in str(app).lower() 
                                                 for indicator in ["consul", "etcd", "discovery"]))
        }
        
        # Calculate readiness score
        total_services = readiness_factors["microservices_count"]
        if total_services > 0:
            readiness_score = (
                (readiness_factors["containerized_services"] / total_services) * 0.4 +
                (readiness_factors["cloud_native_services"] / total_services) * 0.3 +
                (readiness_factors["service_discovery_present"] / total_services) * 0.3
            )
        else:
            readiness_score = 0.0
        
        readiness_factors["readiness_score"] = readiness_score
        readiness_factors["recommendation"] = self._get_service_mesh_recommendation(readiness_score, total_services)
        
        return readiness_factors
    
    def _determine_protocol(self, app_info: str) -> str:
        """Determine API protocol from application information"""
        if "grpc" in app_info:
            return "gRPC"
        elif "graphql" in app_info:
            return "GraphQL"
        elif "soap" in app_info:
            return "SOAP"
        elif any(indicator in app_info for indicator in ["rest", "http", "api"]):
            return "REST/HTTP"
        else:
            return "Unknown"
    
    def _determine_auth_method(self, app_info: str) -> str:
        """Determine authentication method"""
        if "oauth" in app_info:
            return "OAuth"
        elif "jwt" in app_info:
            return "JWT"
        elif "basic" in app_info:
            return "Basic Auth"
        elif "api_key" in app_info or "apikey" in app_info:
            return "API Key"
        elif any(indicator in app_info for indicator in ["auth", "authentication"]):
            return "Authentication Present"
        else:
            return "Unknown"
    
    def _determine_data_format(self, app_info: str) -> str:
        """Determine data format"""
        if "json" in app_info:
            return "JSON"
        elif "xml" in app_info:
            return "XML"
        elif "protobuf" in app_info:
            return "Protocol Buffers"
        else:
            return "Unknown"
    
    def _has_versioning(self, app_info: str) -> bool:
        """Check if API has versioning"""
        return any(indicator in app_info for indicator in ["v1", "v2", "version", "versioning"])
    
    def _has_documentation(self, app_info: str) -> bool:
        """Check if API has documentation"""
        return any(indicator in app_info for indicator in ["swagger", "openapi", "doc", "documentation"])
    
    def _assess_dependency_criticality(self, consumer: Dict[str, Any], provider: Dict[str, Any]) -> str:
        """Assess criticality of dependency relationship"""
        consumer_info = str(consumer).lower()
        provider_info = str(provider).lower()
        
        if any(indicator in consumer_info for indicator in ["critical", "production", "core"]):
            return "high"
        elif any(indicator in provider_info for indicator in ["core", "central", "main"]):
            return "high"
        else:
            return "medium"
    
    def _get_maturity_level(self, score: float) -> str:
        """Get API maturity level based on score"""
        if score >= 0.8:
            return "advanced"
        elif score >= 0.6:
            return "intermediate"
        elif score >= 0.4:
            return "developing"
        else:
            return "basic"
    
    def _get_service_mesh_recommendation(self, score: float, service_count: int) -> str:
        """Get service mesh implementation recommendation"""
        if service_count < 5:
            return "Service mesh not recommended - insufficient microservices"
        elif score >= 0.7:
            return "High readiness - proceed with service mesh implementation"
        elif score >= 0.5:
            return "Medium readiness - consider containerization first"
        else:
            return "Low readiness - focus on cloud-native transformation" 