"""
Specific Question Generators
Specialized functions for generating different types of questions.
"""

from typing import Any, Dict


def generate_database_technical_question(
    asset_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate technical questions specific to database assets."""
    asset_name = asset_context.get("asset_name", "the database")

    return {
        "field_id": f"db_technical_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"Please provide technical details for {asset_name}",
        "field_type": "form_group",
        "required": True,
        "category": "technical_details",
        "sub_questions": [
            {
                "field_id": "database_engine",
                "question_text": "What database engine is used?",
                "field_type": "select",
                "options": [
                    {"value": "mysql", "label": "MySQL"},
                    {"value": "postgresql", "label": "PostgreSQL"},
                    {"value": "oracle", "label": "Oracle"},
                    {"value": "sqlserver", "label": "SQL Server"},
                    {"value": "mongodb", "label": "MongoDB"},
                    {"value": "other", "label": "Other"},
                ],
                "required": True,
            },
            {
                "field_id": "database_version",
                "question_text": "What version is currently running?",
                "field_type": "text",
                "required": False,
            },
            {
                "field_id": "database_size_gb",
                "question_text": "What is the approximate database size (GB)?",
                "field_type": "number",
                "validation": {"min": 0, "max": 100000},
                "required": False,
            },
            {
                "field_id": "backup_strategy",
                "question_text": "What is the current backup strategy?",
                "field_type": "select",
                "options": [
                    {
                        "value": "full_daily",
                        "label": "Full Daily - Complete database backup every day",
                    },
                    {
                        "value": "incremental",
                        "label": "Incremental - Daily incremental with weekly full",
                    },
                    {
                        "value": "differential",
                        "label": "Differential - Regular differential backups",
                    },
                    {
                        "value": "continuous",
                        "label": "Continuous - Real-time backup/replication",
                    },
                    {
                        "value": "snapshot",
                        "label": "Snapshot - Point-in-time snapshots",
                    },
                    {"value": "none", "label": "None - No backup strategy in place"},
                    {
                        "value": "unknown",
                        "label": "Unknown - Backup strategy not documented",
                    },
                ],
                "required": False,
            },
            {
                "field_id": "replication_setup",
                "question_text": "Is there any replication or clustering configured?",
                "field_type": "select",
                "options": [
                    {"value": "none", "label": "No replication"},
                    {"value": "master_slave", "label": "Master-Slave replication"},
                    {"value": "master_master", "label": "Master-Master replication"},
                    {"value": "cluster", "label": "Database cluster"},
                    {"value": "unknown", "label": "Unknown"},
                ],
                "required": False,
            },
            {
                "field_id": "performance_requirements",
                "question_text": "What are the performance requirements?",
                "field_type": "select",
                "options": [
                    {
                        "value": "low",
                        "label": "Low - < 100 transactions/sec, response time < 1s",
                    },
                    {
                        "value": "medium",
                        "label": "Medium - 100-1000 TPS, response time < 500ms",
                    },
                    {
                        "value": "high",
                        "label": "High - 1000-10000 TPS, response time < 100ms",
                    },
                    {
                        "value": "very_high",
                        "label": "Very High - 10000+ TPS, response time < 50ms",
                    },
                    {
                        "value": "mission_critical",
                        "label": "Mission Critical - Sub-10ms latency required",
                    },
                    {
                        "value": "unknown",
                        "label": "Unknown - Performance requirements not defined",
                    },
                ],
                "help_text": "Assess transaction volume, response time requirements, and throughput needs",
                "required": False,
            },
        ],
        "help_text": "Please provide technical information about this database to help with migration planning",
        "priority": "high",
        "gap_type": "technical_detail",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
    }


def generate_application_technical_question(
    asset_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate technical questions specific to application assets."""
    asset_name = asset_context.get("asset_name", "the application")

    return {
        "field_id": f"app_technical_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"Please provide technical details for {asset_name}",
        "field_type": "form_group",
        "required": True,
        "category": "technical_details",
        "sub_questions": [
            {
                "field_id": "programming_language",
                "question_text": "What programming language(s) is the application built with?",
                "field_type": "multi_select",
                "options": [
                    {"value": "java", "label": "Java"},
                    {"value": "python", "label": "Python"},
                    {"value": "javascript", "label": "JavaScript/Node.js"},
                    {"value": "csharp", "label": "C#/.NET"},
                    {"value": "php", "label": "PHP"},
                    {"value": "ruby", "label": "Ruby"},
                    {"value": "go", "label": "Go"},
                    {"value": "other", "label": "Other"},
                ],
                "required": True,
            },
            {
                "field_id": "framework",
                "question_text": "What framework(s) are used?",
                "field_type": "text",
                "help_text": "e.g., Spring Boot, Django, Express.js, ASP.NET",
                "required": False,
            },
            {
                "field_id": "architecture_pattern",
                "question_text": "What architectural pattern does the application follow?",
                "field_type": "select",
                "options": [
                    {"value": "monolith", "label": "Monolithic"},
                    {"value": "microservices", "label": "Microservices"},
                    {"value": "soa", "label": "Service-Oriented Architecture"},
                    {"value": "layered", "label": "Layered Architecture"},
                    {"value": "unknown", "label": "Unknown"},
                ],
                "required": False,
            },
            {
                "field_id": "containerized",
                "question_text": "Is the application containerized?",
                "field_type": "select",
                "options": [
                    {"value": "yes", "label": "Yes, using containers"},
                    {"value": "no", "label": "No, traditional deployment"},
                    {"value": "partial", "label": "Partially containerized"},
                    {"value": "unknown", "label": "Unknown"},
                ],
                "required": False,
            },
            {
                "field_id": "external_integrations",
                "question_text": "How many external systems does this application integrate with?",
                "field_type": "select",
                "options": [
                    {"value": "none", "label": "None - Standalone application"},
                    {
                        "value": "1-3",
                        "label": "1-3 integrations (APIs, databases, or services)",
                    },
                    {"value": "4-7", "label": "4-7 integrations (moderate complexity)"},
                    {"value": "8-15", "label": "8-15 integrations (high complexity)"},
                    {
                        "value": "16+",
                        "label": "16+ integrations (very high complexity)",
                    },
                    {
                        "value": "unknown",
                        "label": "Unknown - Integration count not assessed",
                    },
                ],
                "help_text": "Count APIs, databases, message queues, third-party services, etc.",
                "required": False,
            },
            {
                "field_id": "scalability_requirements",
                "question_text": "What are the scalability requirements?",
                "field_type": "select",
                "options": [
                    {
                        "value": "low",
                        "label": "Low - < 100 concurrent users, predictable load",
                    },
                    {
                        "value": "medium",
                        "label": "Medium - 100-1000 users, moderate variation",
                    },
                    {
                        "value": "high",
                        "label": "High - 1000-10000 users, significant peaks",
                    },
                    {
                        "value": "very_high",
                        "label": "Very High - 10000+ users, elastic scaling needed",
                    },
                    {
                        "value": "unknown",
                        "label": "Unknown - Scalability not yet assessed",
                    },
                ],
                "help_text": "Assess expected load, peak usage, and scaling patterns",
                "required": False,
            },
        ],
        "help_text": "Please provide technical information about this application to help with migration planning",
        "priority": "high",
        "gap_type": "technical_detail",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
    }


def generate_server_technical_question(asset_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate technical questions specific to server assets."""
    asset_name = asset_context.get("asset_name", "the server")

    return {
        "field_id": f"server_technical_{asset_context.get('asset_id', 'unknown')}",
        "question_text": f"Please provide technical details for {asset_name}",
        "field_type": "form_group",
        "required": True,
        "category": "technical_details",
        "sub_questions": [
            {
                "field_id": "cpu_cores",
                "question_text": "How many CPU cores does the server have?",
                "field_type": "number",
                "validation": {"min": 1, "max": 256},
                "required": False,
            },
            {
                "field_id": "memory_gb",
                "question_text": "How much RAM (GB) does the server have?",
                "field_type": "number",
                "validation": {"min": 1, "max": 2048},
                "required": False,
            },
            {
                "field_id": "storage_gb",
                "question_text": "What is the total storage capacity (GB)?",
                "field_type": "number",
                "validation": {"min": 1, "max": 100000},
                "required": False,
            },
            {
                "field_id": "virtualization",
                "question_text": "What virtualization platform is used?",
                "field_type": "select",
                "options": [
                    {"value": "vmware", "label": "VMware"},
                    {"value": "hyper_v", "label": "Microsoft Hyper-V"},
                    {"value": "kvm", "label": "KVM"},
                    {"value": "xen", "label": "Citrix Xen"},
                    {"value": "physical", "label": "Physical server"},
                    {"value": "other", "label": "Other"},
                ],
                "required": False,
            },
            {
                "field_id": "network_config",
                "question_text": "What is the network configuration complexity?",
                "field_type": "select",
                "options": [
                    {
                        "value": "simple",
                        "label": "Simple - Single subnet, basic firewall rules",
                    },
                    {
                        "value": "moderate",
                        "label": "Moderate - Multiple subnets, standard firewall",
                    },
                    {
                        "value": "complex",
                        "label": "Complex - VLANs, DMZ, advanced firewall rules",
                    },
                    {
                        "value": "very_complex",
                        "label": "Very Complex - Multi-tier security, complex routing",
                    },
                    {
                        "value": "unknown",
                        "label": "Unknown - Network configuration not documented",
                    },
                ],
                "help_text": "Assess VLAN configuration, subnet complexity, and firewall rules",
                "required": False,
            },
            {
                "field_id": "monitoring_tools",
                "question_text": "What monitoring tools are currently in place?",
                "field_type": "text",
                "help_text": "e.g., Nagios, Zabbix, SCOM, custom scripts",
                "required": False,
            },
        ],
        "help_text": "Please provide technical information about this server to help with migration planning",
        "priority": "medium",
        "gap_type": "technical_detail",
        "asset_specific": True,
        "asset_id": asset_context.get("asset_id"),
    }
