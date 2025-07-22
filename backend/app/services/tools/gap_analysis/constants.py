"""
Constants and configuration for gap analysis tools
"""

from typing import ClassVar, Dict, List

# Critical attributes mapping patterns
ATTRIBUTE_PATTERNS: Dict[str, List[str]] = {
    # Infrastructure attributes
    "hostname": ["hostname", "server_name", "host", "machine_name", "computer_name"],
    "environment": ["environment", "env", "stage", "tier", "deployment_env"],
    "os_type": ["os_type", "operating_system", "os", "platform", "os_family"],
    "os_version": ["os_version", "os_ver", "version", "os_release", "kernel_version"],
    "cpu_cores": ["cpu_cores", "cores", "vcpu", "processors", "cpu_count"],
    "memory_gb": ["memory_gb", "ram", "memory", "total_memory", "mem_size"],
    "storage_gb": ["storage_gb", "disk_size", "storage", "disk_space", "total_storage"],
    "network_zone": ["network_zone", "subnet", "vlan", "network", "security_zone"],
    
    # Application attributes
    "application_name": ["application_name", "app_name", "application", "service_name"],
    "application_type": ["application_type", "app_type", "category", "app_category"],
    "technology_stack": ["technology_stack", "tech_stack", "framework", "platform", "runtime"],
    "criticality_level": ["criticality_level", "criticality", "priority", "importance"],
    "data_classification": ["data_classification", "data_class", "sensitivity", "classification"],
    "compliance_scope": ["compliance_scope", "compliance", "regulatory", "compliance_req"],
    
    # Operational attributes
    "owner": ["owner", "owner_group", "responsible_party", "team", "department"],
    "cost_center": ["cost_center", "cost_centre", "budget_code", "financial_code"],
    "backup_strategy": ["backup_strategy", "backup_policy", "backup_type", "recovery_strategy"],
    "monitoring_status": ["monitoring_status", "monitoring", "monitored", "monitoring_enabled"],
    "patch_level": ["patch_level", "patch_status", "update_level", "patch_version"],
    "last_scan_date": ["last_scan_date", "scan_date", "last_scanned", "discovery_date"],
    
    # Dependencies attributes
    "application_dependencies": ["application_dependencies", "app_dependencies", "depends_on", "dependencies"],
    "database_dependencies": ["database_dependencies", "db_dependencies", "databases", "data_sources"],
    "integration_points": ["integration_points", "integrations", "interfaces", "api_connections"],
    "data_flows": ["data_flows", "data_transfer", "data_movement", "flow_direction"]
}

# Attribute categories
ATTRIBUTE_CATEGORIES = {
    "infrastructure": ["hostname", "environment", "os_type", "os_version", 
                     "cpu_cores", "memory_gb", "storage_gb", "network_zone"],
    "application": ["application_name", "application_type", "technology_stack",
                  "criticality_level", "data_classification", "compliance_scope"],
    "operational": ["owner", "cost_center", "backup_strategy", "monitoring_status",
                  "patch_level", "last_scan_date"],
    "dependencies": ["application_dependencies", "database_dependencies",
                   "integration_points", "data_flows"]
}

# Priority mapping for attributes
PRIORITY_MAP = {
    # Critical attributes
    "hostname": "critical",
    "application_name": "critical",
    "owner": "critical",
    "environment": "critical",
    "technology_stack": "critical",
    
    # High priority
    "os_type": "high",
    "os_version": "high",
    "criticality_level": "high",
    "data_classification": "high",
    "application_dependencies": "high",
    
    # Medium priority
    "cpu_cores": "medium",
    "memory_gb": "medium",
    "storage_gb": "medium",
    "backup_strategy": "medium",
    "monitoring_status": "medium",
    
    # Low priority
    "patch_level": "low",
    "last_scan_date": "low",
    "cost_center": "low",
    "network_zone": "low"
}

# Collection difficulty mapping
DIFFICULTY_MAP = {
    # Easy to collect
    "hostname": "easy",
    "os_type": "easy",
    "os_version": "easy",
    "cpu_cores": "easy",
    "memory_gb": "easy",
    "storage_gb": "easy",
    
    # Medium difficulty
    "environment": "medium",
    "owner": "medium",
    "application_name": "medium",
    "backup_strategy": "medium",
    "monitoring_status": "medium",
    
    # Hard to collect
    "technology_stack": "hard",
    "application_dependencies": "hard",
    "database_dependencies": "hard",
    "integration_points": "hard",
    "data_flows": "hard",
    
    # Very hard
    "criticality_level": "hard",
    "data_classification": "hard",
    "compliance_scope": "very_hard"
}

# Data source recommendations
SOURCE_MAP = {
    # Automated sources
    "hostname": "discovery_tools",
    "os_type": "discovery_tools",
    "os_version": "discovery_tools",
    "cpu_cores": "discovery_tools",
    "memory_gb": "discovery_tools",
    "storage_gb": "discovery_tools",
    "network_zone": "network_scan",
    "monitoring_status": "monitoring_api",
    "last_scan_date": "discovery_logs",
    
    # Semi-automated sources
    "environment": "cmdb_import",
    "application_name": "cmdb_import",
    "backup_strategy": "backup_system",
    "patch_level": "patch_management",
    
    # Manual sources
    "owner": "stakeholder_input",
    "cost_center": "finance_team",
    "technology_stack": "technical_interview",
    "criticality_level": "business_assessment",
    "data_classification": "security_review",
    "compliance_scope": "compliance_team",
    "application_dependencies": "architecture_review",
    "database_dependencies": "dba_interview",
    "integration_points": "integration_mapping",
    "data_flows": "data_flow_analysis"
}

# Effort estimation matrices
EFFORT_MATRIX = {
    "easy": {"collection": 1, "validation": 0.5, "documentation": 0.5},
    "medium": {"collection": 4, "validation": 2, "documentation": 2},
    "hard": {"collection": 16, "validation": 4, "documentation": 4},
    "very_hard": {"collection": 32, "validation": 8, "documentation": 8}
}

# Base effort hours by difficulty (simplified)
BASE_EFFORT_HOURS = {
    "easy": 2,
    "medium": 8,
    "hard": 24,
    "very_hard": 40
}

# Strategy requirements mapping
STRATEGY_REQUIREMENTS = {
    "rehost": ["hostname", "os_type", "os_version", "cpu_cores", "memory_gb", 
              "storage_gb", "network_zone", "environment"],
    "replatform": ["technology_stack", "os_type", "application_dependencies",
                  "database_dependencies", "integration_points"],
    "refactor": ["technology_stack", "application_type", "application_dependencies",
                "database_dependencies", "data_flows", "criticality_level"],
    "repurchase": ["application_name", "application_type", "criticality_level",
                  "integration_points", "compliance_scope"],
    "retire": ["application_name", "criticality_level", "owner", 
              "application_dependencies", "cost_center"],
    "retain": ["owner", "cost_center", "backup_strategy", "monitoring_status",
              "patch_level", "criticality_level"]
}

# Validation rules for attributes
VALIDATION_RULES = {
    "cpu_cores": lambda v: isinstance(v, (int, float)) and 0 < v <= 1024,
    "memory_gb": lambda v: isinstance(v, (int, float)) and 0 < v <= 10240,
    "storage_gb": lambda v: isinstance(v, (int, float)) and 0 < v <= 1000000,
    "hostname": lambda v: isinstance(v, str) and len(v) > 2,
    "environment": lambda v: isinstance(v, str) and v.lower() in ["dev", "test", "qa", "staging", "prod", "production"],
    "os_type": lambda v: isinstance(v, str) and any(os in v.lower() for os in ["windows", "linux", "unix", "aix", "solaris"])
}