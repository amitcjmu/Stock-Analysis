"""
Comprehensive Migration Field Schema - 6R Assessment Aligned

Defines ALL fields required for accurate 6R strategy recommendation:
- Rehost: Lift-and-shift to cloud (needs infrastructure specs)
- Replatform: Minor optimizations (needs tech stack compatibility)
- Refactor: Re-architect for cloud (needs architecture patterns, code base)
- Repurchase: Replace with SaaS (needs business process, vendor alternatives)
- Retire: Decommission (needs usage data, business justification)
- Retain: Keep as-is (needs compliance requirements, constraints)

This schema ensures gap analysis identifies EVERY missing field needed for
proper 6R assessment, not just basic inventory data.
"""

from typing import Dict, List, Any
from enum import Enum


class FieldCategory(str, Enum):
    """Field categories for organizing questionnaire sections."""

    IDENTITY = "identity"
    BUSINESS = "business"
    TECHNICAL = "technical"
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCIES = "dependencies"
    COMPLIANCE = "compliance"
    MIGRATION = "migration"
    OPERATIONS = "operations"


class FieldPriority(str, Enum):
    """Field priority levels for gap analysis."""

    CRITICAL = "critical"  # Must have for migration planning
    HIGH = "high"  # Important for accurate assessment
    MEDIUM = "medium"  # Useful for optimization
    LOW = "low"  # Nice to have


class MigrationFieldSchema:
    """Comprehensive schema of all fields needed for migration assessment."""

    # Core fields that apply to ALL asset types
    CORE_FIELDS = {
        # Identity Fields
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
        # Business Fields
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
        # Technical Fields
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
        # Infrastructure Fields
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
        # Dependencies
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
        # Compliance Fields
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
        # Operations Fields
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
        # Migration-Specific Fields (6R Assessment Drivers)
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
            "six_r_relevance": ["retire", "retain"],
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
            "help_text": "End of Life systems often need Refactor or Repurchase",
            "six_r_relevance": ["refactor", "repurchase", "replatform"],
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
            "help_text": "Affects Rehost vs Repurchase decision",
            "six_r_relevance": ["rehost", "repurchase"],
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
            "help_text": "May force Retain or specific cloud region for Rehost",
            "six_r_relevance": ["retain", "rehost"],
        },
        "custom_code_percentage": {
            "category": FieldCategory.TECHNICAL,
            "priority": FieldPriority.MEDIUM,
            "field_type": "select",
            "question_text": "What percentage is custom code vs COTS?",
            "options": ["<25%", "25-50%", "50-75%", ">75%", "100% Custom"],
            "help_text": "High custom code suggests Refactor, low suggests Repurchase",
            "six_r_relevance": ["refactor", "repurchase"],
        },
        "saas_alternatives": {
            "category": FieldCategory.MIGRATION,
            "priority": FieldPriority.MEDIUM,
            "field_type": "textarea",
            "question_text": "Are there SaaS alternatives available?",
            "help_text": "List potential SaaS replacements - drives Repurchase consideration",
            "six_r_relevance": ["repurchase"],
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

    # Additional fields specific to application assets
    APPLICATION_FIELDS = {
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

    # Additional fields specific to database assets
    DATABASE_FIELDS = {
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

    # Additional fields specific to server assets
    SERVER_FIELDS = {
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

    @classmethod
    def get_fields_for_asset_type(cls, asset_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all applicable fields for a given asset type.

        Args:
            asset_type: Type of asset (application, database, server, etc.)

        Returns:
            Dictionary of field definitions applicable to this asset type
        """
        # Start with core fields that apply to all assets
        fields = cls.CORE_FIELDS.copy()

        # Add type-specific fields
        if asset_type == "application":
            fields.update(cls.APPLICATION_FIELDS)
        elif asset_type == "database":
            fields.update(cls.DATABASE_FIELDS)
        elif asset_type in ["server", "vm", "virtual_machine"]:
            fields.update(cls.SERVER_FIELDS)

        return fields

    @classmethod
    def get_fields_by_category(
        cls, asset_type: str = None
    ) -> Dict[FieldCategory, List[str]]:
        """
        Get fields organized by category.

        Args:
            asset_type: Optional asset type to filter fields

        Returns:
            Dictionary mapping categories to field names
        """
        fields = cls.get_fields_for_asset_type(asset_type or "application")

        categorized = {}
        for field_name, field_def in fields.items():
            category = field_def["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(field_name)

        return categorized

    @classmethod
    def get_critical_fields(cls, asset_type: str = None) -> List[str]:
        """
        Get all CRITICAL priority fields for an asset type.

        Args:
            asset_type: Optional asset type to filter fields

        Returns:
            List of critical field names
        """
        fields = cls.get_fields_for_asset_type(asset_type or "application")
        return [
            field_name
            for field_name, field_def in fields.items()
            if field_def.get("priority") == FieldPriority.CRITICAL
        ]

    @classmethod
    def get_high_priority_fields(cls, asset_type: str = None) -> List[str]:
        """
        Get all HIGH priority fields for an asset type.

        Args:
            asset_type: Optional asset type to filter fields

        Returns:
            List of high priority field names
        """
        fields = cls.get_fields_for_asset_type(asset_type or "application")
        return [
            field_name
            for field_name, field_def in fields.items()
            if field_def.get("priority") == FieldPriority.HIGH
        ]

    @classmethod
    def get_six_r_decision_fields(cls, asset_type: str = None) -> Dict[str, List[str]]:
        """
        Get fields organized by which 6R strategy they inform.

        This helps understand what data is needed for each migration strategy:
        - Rehost: Infrastructure specs, dependencies
        - Replatform: Tech stack, cloud readiness
        - Refactor: Architecture, code base
        - Repurchase: Business process, alternatives
        - Retire: Usage, business value
        - Retain: Compliance, constraints

        Args:
            asset_type: Optional asset type to filter fields

        Returns:
            Dictionary mapping 6R strategies to field names that inform that decision
        """
        fields = cls.get_fields_for_asset_type(asset_type or "application")

        six_r_mapping = {
            "rehost": [],
            "replatform": [],
            "refactor": [],
            "repurchase": [],
            "retire": [],
            "retain": [],
        }

        for field_name, field_def in fields.items():
            if "six_r_relevance" in field_def:
                for strategy in field_def["six_r_relevance"]:
                    if strategy in six_r_mapping:
                        six_r_mapping[strategy].append(field_name)

        return six_r_mapping

    @classmethod
    def validate_assessment_readiness(
        cls, asset, asset_type: str = None
    ) -> Dict[str, Any]:
        """
        Validate if asset has sufficient data for 6R assessment.

        Returns assessment readiness report indicating which 6R strategies
        can be accurately evaluated based on available data.

        Args:
            asset: Asset object to validate
            asset_type: Optional asset type

        Returns:
            Dictionary with readiness status per 6R strategy
        """
        asset_type = asset_type or getattr(asset, "asset_type", "application")
        six_r_fields = cls.get_six_r_decision_fields(asset_type)

        readiness = {}
        for strategy, required_fields in six_r_fields.items():
            if not required_fields:
                continue

            # Check how many required fields are populated
            populated = 0
            for field in required_fields:
                value = getattr(asset, field, None)
                if value and (not isinstance(value, (list, dict)) or len(value) > 0):
                    populated += 1

            total = len(required_fields)
            percentage = (populated / total * 100) if total > 0 else 0

            readiness[strategy] = {
                "percentage": percentage,
                "populated_fields": populated,
                "total_fields": total,
                "assessment_viable": percentage
                >= 70,  # Need 70%+ for reliable assessment
                "missing_fields": [
                    f for f in required_fields if not getattr(asset, f, None)
                ],
            }

        # Overall assessment readiness
        viable_strategies = sum(1 for r in readiness.values() if r["assessment_viable"])
        readiness["overall"] = {
            "viable_strategies": viable_strategies,
            "total_strategies": len(readiness),
            "can_assess": viable_strategies >= 3,  # Need at least 3 viable options
        }

        return readiness
