"""
Application Classification Tools for Inventory Building Crew
Provides specialized tools for application and service discovery and classification
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AppClassificationTool(BaseTool):
    name: str = "app_classification_tool"
    description: str = "Classifies applications and services based on their characteristics and business function"
    
    def _run(self, application_data: str) -> str:
        """
        Classify applications based on their characteristics
        
        Args:
            application_data: JSON string containing application information
            
        Returns:
            JSON string with application classification results
        """
        try:
            data = json.loads(application_data)
            
            classification_results = {}
            app_categories = {
                "web_application": ["web", "website", "portal", "frontend"],
                "database": ["database", "db", "sql", "nosql", "mysql", "postgresql", "oracle"],
                "middleware": ["middleware", "message", "queue", "broker", "activemq"],
                "enterprise_application": ["erp", "crm", "hr", "finance", "sap", "oracle"],
                "development_tool": ["jenkins", "git", "maven", "build", "ci/cd"],
                "monitoring_tool": ["monitor", "nagios", "splunk", "prometheus"],
                "security_tool": ["security", "firewall", "antivirus", "auth"],
                "backup_tool": ["backup", "restore", "archive"],
                "business_intelligence": ["bi", "reporting", "analytics", "tableau"],
                "communication": ["email", "chat", "collaboration", "sharepoint"]
            }
            
            for app in data.get("applications", []):
                app_name = app.get("name", "unknown")
                app_info = str(app).lower()
                
                # Classify based on keywords and patterns
                classified_category = "generic_application"
                confidence = 0.5
                business_function = "unknown"
                
                for category, keywords in app_categories.items():
                    if any(keyword in app_info for keyword in keywords):
                        classified_category = category
                        confidence = 0.8
                        business_function = self._determine_business_function(category)
                        break
                
                # Determine business criticality
                criticality = self._assess_business_criticality(app, classified_category)
                
                classification_results[app_name] = {
                    "category": classified_category,
                    "business_function": business_function,
                    "confidence": confidence,
                    "business_criticality": criticality,
                    "technical_attributes": self._extract_technical_attributes(app),
                    "dependencies": self._identify_dependencies(app)
                }
            
            return json.dumps({
                "application_classifications": classification_results,
                "summary": {
                    "total_applications": len(classification_results),
                    "category_distribution": self._get_category_distribution(classification_results),
                    "criticality_distribution": self._get_criticality_distribution(classification_results)
                }
            })
            
        except Exception as e:
            logger.error(f"Error in application classification: {e}")
            return json.dumps({"error": str(e)})
    
    def _determine_business_function(self, category: str) -> str:
        """Map application category to business function"""
        function_mapping = {
            "web_application": "customer_facing",
            "database": "data_management",
            "middleware": "integration",
            "enterprise_application": "business_operations",
            "development_tool": "development_support",
            "monitoring_tool": "operations_support",
            "security_tool": "security_compliance",
            "backup_tool": "data_protection",
            "business_intelligence": "decision_support",
            "communication": "collaboration"
        }
        return function_mapping.get(category, "support")
    
    def _assess_business_criticality(self, app: Dict[str, Any], category: str) -> str:
        """Assess business criticality of the application"""
        # High criticality categories
        high_crit_categories = ["database", "enterprise_application", "security_tool"]
        if category in high_crit_categories:
            return "high"
        
        # Check for explicit criticality indicators
        app_info = str(app).lower()
        if any(indicator in app_info for indicator in ["critical", "production", "core"]):
            return "high"
        elif any(indicator in app_info for indicator in ["test", "dev", "staging"]):
            return "low"
        
        return "medium"
    
    def _extract_technical_attributes(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical attributes from application data"""
        attributes = {}
        
        # Common technical fields
        tech_fields = ["version", "platform", "technology", "framework", "language"]
        for field in tech_fields:
            for key, value in app.items():
                if field in key.lower() and value:
                    attributes[field] = value
        
        # Determine if it's cloud-native
        app_info = str(app).lower()
        if any(indicator in app_info for indicator in ["kubernetes", "docker", "microservice"]):
            attributes["architecture"] = "cloud_native"
        elif any(indicator in app_info for indicator in ["monolith", "legacy"]):
            attributes["architecture"] = "traditional"
        
        return attributes
    
    def _identify_dependencies(self, app: Dict[str, Any]) -> List[str]:
        """Identify potential dependencies from application data"""
        dependencies = []
        app_info = str(app).lower()
        
        # Database dependencies
        if any(db in app_info for db in ["mysql", "postgresql", "oracle", "sql"]):
            dependencies.append("database")
        
        # Web server dependencies
        if any(web in app_info for web in ["apache", "nginx", "iis"]):
            dependencies.append("web_server")
        
        # Middleware dependencies
        if any(mw in app_info for mw in ["jboss", "websphere", "tomcat"]):
            dependencies.append("application_server")
        
        return dependencies
    
    def _get_category_distribution(self, classifications: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution of application categories"""
        distribution = {}
        for app_info in classifications.values():
            category = app_info["category"]
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def _get_criticality_distribution(self, classifications: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution of business criticality levels"""
        distribution = {}
        for app_info in classifications.values():
            criticality = app_info["business_criticality"]
            distribution[criticality] = distribution.get(criticality, 0) + 1
        return distribution

class ServiceDiscoveryTool(BaseTool):
    name: str = "service_discovery_tool"
    description: str = "Discovers and analyzes application services and their relationships"
    
    def _run(self, service_data: str) -> str:
        """
        Discover and analyze application services
        
        Args:
            service_data: JSON string containing service information
            
        Returns:
            JSON string with service discovery results
        """
        try:
            data = json.loads(service_data)
            
            discovery_results = {
                "discovered_services": self._discover_services(data.get("applications", [])),
                "service_patterns": self._analyze_service_patterns(data.get("applications", [])),
                "api_endpoints": self._identify_api_endpoints(data.get("applications", [])),
                "service_mesh_candidates": self._identify_service_mesh_candidates(data.get("applications", []))
            }
            
            return json.dumps(discovery_results)
            
        except Exception as e:
            logger.error(f"Error in service discovery: {e}")
            return json.dumps({"error": str(e)})
    
    def _discover_services(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Discover individual services within applications"""
        services = {}
        
        for app in applications:
            app_name = app.get("name", "unknown")
            app_info = str(app).lower()
            
            # Identify service types
            service_indicators = {
                "api_service": ["api", "rest", "service", "endpoint"],
                "web_service": ["web", "frontend", "ui"],
                "data_service": ["data", "database", "storage"],
                "auth_service": ["auth", "authentication", "ldap"],
                "messaging_service": ["message", "queue", "kafka", "rabbitmq"]
            }
            
            identified_services = []
            for service_type, keywords in service_indicators.items():
                if any(keyword in app_info for keyword in keywords):
                    identified_services.append(service_type)
            
            if not identified_services:
                identified_services = ["generic_service"]
            
            services[app_name] = {
                "service_types": identified_services,
                "protocol_hints": self._identify_protocols(app),
                "port_analysis": self._analyze_ports(app),
                "scalability_indicators": self._assess_scalability(app)
            }
        
        return services
    
    def _analyze_service_patterns(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze service architecture patterns"""
        patterns = {
            "microservices_indicators": 0,
            "monolith_indicators": 0,
            "distributed_system_complexity": "low"
        }
        
        for app in applications:
            app_info = str(app).lower()
            
            # Microservices indicators
            if any(indicator in app_info for indicator in ["microservice", "docker", "kubernetes", "api"]):
                patterns["microservices_indicators"] += 1
            
            # Monolith indicators
            if any(indicator in app_info for indicator in ["monolith", "legacy", "single"]):
                patterns["monolith_indicators"] += 1
        
        # Assess complexity
        total_apps = len(applications)
        if patterns["microservices_indicators"] > total_apps * 0.5:
            patterns["distributed_system_complexity"] = "high"
        elif patterns["microservices_indicators"] > total_apps * 0.2:
            patterns["distributed_system_complexity"] = "medium"
        
        return patterns
    
    def _identify_api_endpoints(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential API endpoints"""
        endpoints = []
        
        for app in applications:
            app_info = str(app).lower()
            if any(api_indicator in app_info for api_indicator in ["api", "rest", "soap", "endpoint"]):
                endpoints.append({
                    "application": app.get("name"),
                    "type": "potential_api",
                    "protocol": self._guess_api_protocol(app_info),
                    "confidence": 0.7
                })
        
        return endpoints
    
    def _identify_service_mesh_candidates(self, applications: List[Dict[str, Any]]) -> List[str]:
        """Identify applications that could benefit from service mesh"""
        candidates = []
        
        for app in applications:
            app_info = str(app).lower()
            if any(indicator in app_info for indicator in ["microservice", "distributed", "api"]):
                candidates.append(app.get("name", "unknown"))
        
        return candidates
    
    def _identify_protocols(self, app: Dict[str, Any]) -> List[str]:
        """Identify communication protocols"""
        protocols = []
        app_info = str(app).lower()
        
        protocol_indicators = {
            "http": ["http", "web", "rest"],
            "https": ["https", "ssl", "tls"],
            "tcp": ["tcp", "socket"],
            "udp": ["udp"],
            "grpc": ["grpc"],
            "websocket": ["websocket", "ws"]
        }
        
        for protocol, keywords in protocol_indicators.items():
            if any(keyword in app_info for keyword in keywords):
                protocols.append(protocol)
        
        return protocols if protocols else ["unknown"]
    
    def _analyze_ports(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze port usage patterns"""
        # Placeholder for port analysis
        return {"analysis": "port_data_not_available"}
    
    def _assess_scalability(self, app: Dict[str, Any]) -> str:
        """Assess application scalability characteristics"""
        app_info = str(app).lower()
        
        if any(indicator in app_info for indicator in ["cloud", "container", "kubernetes"]):
            return "cloud_scalable"
        elif any(indicator in app_info for indicator in ["cluster", "load_balancer"]):
            return "horizontally_scalable"
        elif "legacy" in app_info:
            return "limited_scalability"
        
        return "traditional_scalability"
    
    def _guess_api_protocol(self, app_info: str) -> str:
        """Guess API protocol based on application information"""
        if "rest" in app_info:
            return "REST"
        elif "soap" in app_info:
            return "SOAP"
        elif "graphql" in app_info:
            return "GraphQL"
        elif "grpc" in app_info:
            return "gRPC"
        
        return "HTTP" 