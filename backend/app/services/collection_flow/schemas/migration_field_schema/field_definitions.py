"""Field definitions for migration assessment."""

from typing import Dict, Any
from .base_schemas import FieldCategory, FieldPriority


CORE_FIELDS: Dict[str, Dict[str, Any]] = {
    "asset_name": {
        "category": FieldCategory.IDENTITY,
        "priority": FieldPriority.CRITICAL,
        "field_type": "text",
        "question_text": "What is the asset name?",
        "help_text": "Primary identifier for this asset",
    },
    "asset_type": {
        "category": FieldCategory.IDENTITY,
        "priority": FieldPriority.CRITICAL,
        "field_type": "select",
        "question_text": "What type of asset is this?",
        "options": [
            "application",
            "database",
            "server",
            "network_device",
            "storage",
            "middleware",
            "container",
            "vm",
        ],
    },
    "business_owner": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.CRITICAL,
        "field_type": "text",
        "question_text": "Who is the business owner?",
        "help_text": "Primary business contact responsible for this asset",
    },
    "technical_owner": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.CRITICAL,
        "field_type": "text",
        "question_text": "Who is the technical owner?",
        "help_text": "Primary technical contact responsible for this asset",
    },
    "business_purpose": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.HIGH,
        "field_type": "textarea",
        "question_text": "What is the primary business purpose?",
    },
    "business_criticality": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What is the business criticality?",
        "options": [
            "Mission Critical",
            "Business Critical",
            "Important",
            "Standard",
            "Low",
        ],
    },
    "operating_system": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.CRITICAL,
        "field_type": "text",
        "question_text": "What is the operating system?",
    },
    "technology_stack": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "multi_select",
        "question_text": "What technologies does this asset use?",
        "options": [
            "Java",
            "Python",
            ".NET",
            "Node.js",
            "Ruby",
            "PHP",
            "Go",
            "Other",
        ],
    },
    "version": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "text",
        "question_text": "What is the current version?",
    },
    "environment": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What environment is this deployed in?",
        "options": ["Production", "Staging", "Development", "DR", "Test"],
    },
    "datacenter": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "text",
        "question_text": "Which datacenter hosts this asset?",
    },
    "location": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.MEDIUM,
        "field_type": "text",
        "question_text": "What is the physical location?",
    },
    "dependencies": {
        "category": FieldCategory.DEPENDENCIES,
        "priority": FieldPriority.CRITICAL,
        "field_type": "textarea",
        "question_text": "What are the critical dependencies?",
        "help_text": "List systems, databases, or services this asset depends on",
    },
    "integration_points": {
        "category": FieldCategory.DEPENDENCIES,
        "priority": FieldPriority.HIGH,
        "field_type": "textarea",
        "question_text": "What are the integration points?",
    },
    "data_classification": {
        "category": FieldCategory.COMPLIANCE,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What is the data classification level?",
        "options": ["Public", "Internal", "Confidential", "Restricted"],
    },
    "compliance_requirements": {
        "category": FieldCategory.COMPLIANCE,
        "priority": FieldPriority.HIGH,
        "field_type": "multi_select",
        "question_text": "What compliance requirements apply?",
        "options": ["PCI-DSS", "HIPAA", "SOC2", "GDPR", "CCPA", "None"],
    },
    "maintenance_window": {
        "category": FieldCategory.OPERATIONS,
        "priority": FieldPriority.MEDIUM,
        "field_type": "text",
        "question_text": "What is the maintenance window?",
    },
    "sla_requirements": {
        "category": FieldCategory.OPERATIONS,
        "priority": FieldPriority.MEDIUM,
        "field_type": "text",
        "question_text": "What are the SLA requirements?",
    },
    "backup_strategy": {
        "category": FieldCategory.OPERATIONS,
        "priority": FieldPriority.MEDIUM,
        "field_type": "textarea",
        "question_text": "What is the backup strategy?",
    },
    "current_usage_patterns": {
        "category": FieldCategory.OPERATIONS,
        "priority": FieldPriority.HIGH,
        "field_type": "textarea",
        "question_text": "What are the current usage patterns?",
        "help_text": "Peak hours, transaction volumes, user patterns - helps determine Retire vs Rehost",
        "six_r_relevance": ["retire", "rehost", "replatform"],
    },
    "business_value": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What business value does this asset provide?",
        "options": [
            "High - Revenue Generating",
            "Medium - Operational",
            "Low - Support",
            "Minimal - Legacy",
        ],
        "help_text": "Determines if asset should be Retired or migrated",
        "six_r_relevance": [
            "retire",
            "rehost",
        ],  # Map retain → rehost per 6R standardization
    },
    "vendor_support_status": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What is the vendor support status?",
        "options": [
            "Active Support",
            "Extended Support",
            "End of Life",
            "No Support",
        ],
        "help_text": "End of Life systems often need Refactor or Replace",
        "six_r_relevance": [
            "refactor",
            "replace",
            "replatform",
        ],  # Map repurchase → replace
    },
    "licensing_model": {
        "category": FieldCategory.COMPLIANCE,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What is the licensing model?",
        "options": [
            "Perpetual",
            "Subscription",
            "Open Source",
            "Custom/Enterprise",
        ],
        "help_text": "Affects Rehost vs Replace decision",
        "six_r_relevance": ["rehost", "replace"],  # Map repurchase → replace
    },
    "cloud_readiness": {
        "category": FieldCategory.MIGRATION,
        "priority": FieldPriority.CRITICAL,
        "field_type": "select",
        "question_text": "What is the cloud readiness level?",
        "options": [
            "Cloud Native",
            "Cloud Ready",
            "Requires Changes",
            "Not Compatible",
        ],
        "help_text": "Determines if Rehost is viable or Refactor needed",
        "six_r_relevance": ["rehost", "replatform", "refactor"],
    },
    "architecture_pattern": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What architecture pattern is used?",
        "options": [
            "Monolithic",
            "N-Tier",
            "Microservices",
            "Serverless",
            "Hybrid",
        ],
        "help_text": "Monolithic may need Refactor for cloud optimization",
        "six_r_relevance": ["rehost", "refactor"],
    },
    "state_management": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.MEDIUM,
        "field_type": "select",
        "question_text": "How is state managed?",
        "options": ["Stateless", "Session State", "Persistent State", "Mixed"],
        "help_text": "Stateful apps need careful Rehost planning",
        "six_r_relevance": ["rehost", "replatform"],
    },
    "data_residency_requirements": {
        "category": FieldCategory.COMPLIANCE,
        "priority": FieldPriority.HIGH,
        "field_type": "textarea",
        "question_text": "Are there data residency requirements?",
        "help_text": "May force specific cloud region for Rehost",
        "six_r_relevance": ["rehost"],  # Removed retain per 6R standardization
    },
    "custom_code_percentage": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.MEDIUM,
        "field_type": "select",
        "question_text": "What percentage is custom code vs COTS?",
        "options": ["<25%", "25-50%", "50-75%", ">75%", "100% Custom"],
        "help_text": "High custom code suggests Refactor, low suggests Replace",
        "six_r_relevance": ["refactor", "replace"],  # Map repurchase → replace
    },
    "saas_alternatives": {
        "category": FieldCategory.MIGRATION,
        "priority": FieldPriority.MEDIUM,
        "field_type": "textarea",
        "question_text": "Are there SaaS alternatives available?",
        "help_text": "List potential SaaS replacements - drives Replace consideration",
        "six_r_relevance": ["replace"],  # Map repurchase → replace
    },
    "migration_priority": {
        "category": FieldCategory.MIGRATION,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What is the migration priority?",
        "options": ["Wave 1 (High)", "Wave 2 (Medium)", "Wave 3 (Low)", "TBD"],
    },
    "target_platform": {
        "category": FieldCategory.MIGRATION,
        "priority": FieldPriority.HIGH,
        "field_type": "text",
        "question_text": "What is the target platform for migration?",
    },
}

APPLICATION_FIELDS: Dict[str, Dict[str, Any]] = {
    "application_tier": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "select",
        "question_text": "What tier is this application?",
        "options": [
            "Presentation",
            "Application",
            "Data",
            "Integration",
            "Full Stack",
        ],
    },
    "programming_language": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.HIGH,
        "field_type": "text",
        "question_text": "What programming language is used?",
    },
    "framework": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.MEDIUM,
        "field_type": "text",
        "question_text": "What framework is used?",
    },
    "user_count": {
        "category": FieldCategory.BUSINESS,
        "priority": FieldPriority.MEDIUM,
        "field_type": "number",
        "question_text": "How many active users?",
    },
}

DATABASE_FIELDS: Dict[str, Dict[str, Any]] = {
    "database_type": {
        "category": FieldCategory.TECHNICAL,
        "priority": FieldPriority.CRITICAL,
        "field_type": "select",
        "question_text": "What type of database?",
        "options": [
            "MySQL",
            "PostgreSQL",
            "Oracle",
            "SQL Server",
            "MongoDB",
            "Cassandra",
            "Redis",
            "Other",
        ],
    },
    "database_size": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "text",
        "question_text": "What is the database size?",
    },
    "transaction_volume": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.MEDIUM,
        "field_type": "text",
        "question_text": "What is the average transaction volume?",
    },
}

SERVER_FIELDS: Dict[str, Dict[str, Any]] = {
    "cpu_cores": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "number",
        "question_text": "How many CPU cores?",
    },
    "memory_gb": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "number",
        "question_text": "How much memory (GB)?",
    },
    "storage_gb": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.HIGH,
        "field_type": "number",
        "question_text": "How much storage (GB)?",
    },
    "virtualization_platform": {
        "category": FieldCategory.INFRASTRUCTURE,
        "priority": FieldPriority.MEDIUM,
        "field_type": "select",
        "question_text": "What virtualization platform?",
        "options": ["VMware", "Hyper-V", "KVM", "Xen", "Physical", "Cloud Native"],
    },
}


def get_fields_for_asset_type(asset_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all applicable fields for a given asset type.

    Args:
        asset_type: Type of asset (application, database, server, etc.)

    Returns:
        Dictionary of field definitions applicable to this asset type
    """
    # Start with core fields that apply to all assets
    fields = CORE_FIELDS.copy()

    # Add type-specific fields
    if asset_type == "application":
        fields.update(APPLICATION_FIELDS)
    elif asset_type == "database":
        fields.update(DATABASE_FIELDS)
    elif asset_type in ["server", "vm", "virtual_machine"]:
        fields.update(SERVER_FIELDS)

    return fields
