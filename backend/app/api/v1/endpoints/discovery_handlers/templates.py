"""
Templates Handler
Handles CMDB templates and field mappings.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TemplateHandler:
    """Handles CMDB templates and field mappings."""
    
    def __init__(self):
        self.field_mapper_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize optional dependencies with graceful fallbacks."""
        try:
            from app.services.field_mapper import field_mapper
            self.field_mapper = field_mapper
            self.field_mapper_available = True
            logger.info("Field mapper service initialized successfully")
        except ImportError as e:
            logger.warning(f"Field mapper service not available: {e}")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def get_templates(self) -> Dict[str, Any]:
        """
        Get CMDB template examples and field mappings.
        """
        base_templates = self._get_base_templates()
        
        if self.field_mapper_available:
            try:
                # Enhance with dynamic field mappings
                dynamic_mappings = self.field_mapper.get_all_mappings()
                base_templates["dynamic_field_mappings"] = dynamic_mappings
                base_templates["mapping_source"] = "enhanced_with_learned_mappings"
            except Exception as e:
                logger.warning(f"Failed to get dynamic mappings: {e}")
                base_templates["mapping_source"] = "static_fallback"
        else:
            base_templates["mapping_source"] = "static_only"
        
        return base_templates
    
    def _get_base_templates(self) -> Dict[str, Any]:
        """Get base template definitions."""
        return {
            "templates": [
                {
                    "name": "Enterprise CMDB",
                    "description": "Standard enterprise configuration management database format",
                    "required_fields": ["hostname", "asset_type", "environment", "department"],
                    "optional_fields": ["ip_address", "operating_system", "application_name", "criticality"],
                    "sample_data": {
                        "hostname": "web-server-01",
                        "asset_type": "Server", 
                        "environment": "Production",
                        "department": "IT",
                        "ip_address": "10.0.1.100",
                        "operating_system": "Ubuntu 20.04",
                        "application_name": "Web Portal",
                        "criticality": "High"
                    }
                },
                {
                    "name": "Application Inventory",
                    "description": "Application-focused inventory with technical details",
                    "required_fields": ["application_name", "technology_stack", "environment"],
                    "optional_fields": ["department", "criticality", "dependencies", "data_sensitivity"],
                    "sample_data": {
                        "application_name": "Customer Portal",
                        "technology_stack": "Java, Spring Boot, PostgreSQL",
                        "environment": "Production",
                        "department": "Customer Service",
                        "criticality": "High",
                        "dependencies": "User Management Service, Payment Gateway",
                        "data_sensitivity": "High"
                    }
                },
                {
                    "name": "Infrastructure Assets",
                    "description": "Infrastructure-focused asset inventory",
                    "required_fields": ["hostname", "asset_type", "environment", "location"],
                    "optional_fields": ["ip_address", "cpu_cores", "memory_gb", "storage_gb", "business_owner"],
                    "sample_data": {
                        "hostname": "db-server-01",
                        "asset_type": "Database Server",
                        "environment": "Production",
                        "location": "Data Center A",
                        "ip_address": "10.0.2.100",
                        "cpu_cores": 8,
                        "memory_gb": 32,
                        "storage_gb": 1000,
                        "business_owner": "Database Team"
                    }
                }
            ],
            "field_mappings": {
                "hostname": ["host", "server_name", "machine_name", "system_name", "computer_name"],
                "asset_type": ["type", "category", "classification", "asset_category", "ci_type"],
                "environment": ["env", "stage", "tier", "deployment_environment", "env_type"],
                "department": ["dept", "business_unit", "organization", "team", "division"],
                "application_name": ["app", "application", "service_name", "app_name", "service"],
                "technology_stack": ["tech_stack", "technologies", "platform", "stack", "tech"],
                "criticality": ["priority", "importance", "business_criticality", "critical", "business_impact"],
                "ip_address": ["ip", "ip_addr", "host_ip", "server_ip", "network_address"],
                "operating_system": ["os", "os_name", "operating_sys", "platform", "os_version"],
                "cpu_cores": ["cpu", "cores", "processors", "vcpu", "cpu_count"],
                "memory_gb": ["memory", "ram", "ram_gb", "memory_size", "mem"],
                "storage_gb": ["storage", "disk", "disk_gb", "storage_size", "hdd"]
            },
            "validation_rules": {
                "hostname": {
                    "required": True,
                    "pattern": "^[a-zA-Z0-9][a-zA-Z0-9\\-]*[a-zA-Z0-9]$",
                    "description": "Valid hostname format"
                },
                "environment": {
                    "required": True,
                    "allowed_values": ["Production", "Staging", "Development", "Test", "UAT"],
                    "description": "Standard environment classifications"
                },
                "asset_type": {
                    "required": True,
                    "allowed_values": ["Server", "Database", "Application", "Network Device", "Storage"],
                    "description": "Standard asset type classifications"
                },
                "ip_address": {
                    "pattern": "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$",
                    "description": "Valid IPv4 address format"
                }
            }
        } 