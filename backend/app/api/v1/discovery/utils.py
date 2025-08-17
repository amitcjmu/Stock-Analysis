"""
CMDB Discovery Utilities
Helper functions for asset processing and analysis.
"""

import logging
from typing import Any, Dict, List

try:
    from app.services.crewai_flow_service import CrewAIFlowService

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAIFlowService = None


logger = logging.getLogger(__name__)


def _check_patterns(combined_text: str, patterns: list) -> bool:
    """Check if any pattern in the list matches the combined text with word boundaries."""
    import re

    for pattern in patterns:
        # Use word boundaries for more accurate matching
        # This prevents false positives like "sql" matching in "mysql"
        if re.search(r"\b" + re.escape(pattern) + r"\b", combined_text, re.IGNORECASE):
            return True
    return False


def _get_db_server_patterns():
    """Get database server specific patterns."""
    return [
        "db server",
        "database server",
        "sql server",
        "oracle server",
        "mysql server",
        "postgres server",
        "mongodb server",
        "redis server",
        "cassandra server",
    ]


def _get_app_server_patterns():
    """Get application server specific patterns."""
    return [
        "app server",
        "application server",
        "web server",
        "api server",
        "webserver",
        "tomcat",
        "apache server",
        "nginx server",
        "iis server",
    ]


def _get_database_patterns():
    """Get standalone database patterns."""
    return [
        "database",
        "db-",
        "-db",
        "sql",
        "oracle",
        "mysql",
        "postgres",
        "postgresql",
        "mongodb",
        "redis",
        "cassandra",
        "elasticsearch",
        "influxdb",
        "mariadb",
        "mssql",
        "sqlite",
        "dynamodb",
        "couchdb",
        "neo4j",
    ]


def _get_security_patterns():
    """Get security device patterns."""
    return [
        "firewall",
        "fw-",
        "-fw",
        "ids",
        "ips",
        "waf",
        "proxy",
        "checkpoint",
        "symantec",
        "mcafee",
        "splunk",
        "qualys",
        "nessus",
        "security",
    ]


def _get_network_patterns():
    """Get network device patterns."""
    return [
        "switch",
        "router",
        "gateway",
        "loadbalancer",
        "lb-",
        "cisco",
        "juniper",
        "palo",
        "fortinet",
        "f5",
        "netscaler",
        "core",
        "edge",
        "wan",
        "lan",
        "wifi",
        "access-point",
        "ap-",
    ]


def _get_storage_patterns():
    """Get storage device patterns."""
    return [
        "san",
        "nas",
        "storage",
        "array",
        "netapp",
        "emc",
        "dell",
        "hp-3par",
        "pure",
        "nimble",
        "solidfire",
        "vnx",
        "unity",
        "powermax",
    ]


def _get_virtualization_patterns():
    """Get virtualization platform patterns."""
    return [
        "vmware",
        "vcenter",
        "esxi",
        "hyper-v",
        "citrix",
        "xen",
        "kvm",
        "docker",
        "kubernetes",
        "openshift",
        "vsphere",
    ]


def _get_server_patterns():
    """Get generic server patterns."""
    return [
        "server",
        "srv-",
        "-srv",
        "host",
        "machine",
        "vm",
        "computer",
        "node",
        "mail",
        "dns",
        "dhcp",
        "domain",
        "controller",
    ]


def _get_application_patterns():
    """Get standalone application patterns."""
    return [
        "application",
        "app-",
        "-app",
        "service",
        "software",
        "portal",
        "system",
        "platform",
        "api",
        "microservice",
        "webapp",
    ]


def _get_infrastructure_patterns():
    """Get infrastructure device patterns."""
    return [
        "ups",
        "power",
        "rack",
        "kvm",
        "console",
        "monitor",
        "printer",
        "scanner",
        "phone",
        "voip",
        "camera",
        "sensor",
    ]


def _classify_by_pattern_groups(combined_text: str) -> str:
    """Classify asset type by checking pattern groups in priority order."""
    # Check in priority order - highest priority first
    pattern_checks = [
        (_get_db_server_patterns(), "Database"),
        (_get_app_server_patterns(), "Application"),
        (_get_database_patterns(), "Database"),
        (_get_security_patterns(), "Security Device"),
        (_get_network_patterns(), "Network Device"),
        (_get_storage_patterns(), "Storage Device"),
        (_get_virtualization_patterns(), "Virtualization Platform"),
        (_get_server_patterns(), "Server"),
        (_get_application_patterns(), "Application"),
        (_get_infrastructure_patterns(), "Infrastructure Device"),
    ]

    for patterns, asset_type in pattern_checks:
        if _check_patterns(combined_text, patterns):
            return asset_type

    return "Unknown"


def standardize_asset_type(
    asset_type: str, asset_name: str = "", asset_data: Dict[str, Any] = None
) -> str:
    """Standardize asset type names using comprehensive pattern matching."""
    if not asset_type and not asset_name:
        return "Unknown"

    # Combine type and name for better detection
    combined_text = f"{asset_type or ''} {asset_name or ''}".lower()

    # Classify using pattern groups
    return _classify_by_pattern_groups(combined_text)


def get_field_value(asset: Dict[str, Any], field_names: List[str]) -> str:
    """Get field value using flexible field name matching."""
    for field_name in field_names:
        value = asset.get(field_name)
        if (
            value
            and str(value).strip()
            and str(value).strip().lower() not in ["unknown", "null", "none", ""]
        ):
            return str(value).strip()
    return "Unknown"


def get_tech_stack(asset: Dict[str, Any]) -> str:
    """Extract technology stack information from asset data with flexible field mapping."""
    # Try to build tech stack from available fields
    tech_components = []

    # Operating System (combine OS type and version for display)
    os_type = get_field_value(
        asset, ["operating_system", "os", "platform", "os_name", "os_type"]
    )
    os_version = get_field_value(
        asset, ["os_version", "version", "os_ver", "operating_system_version"]
    )

    if os_type != "Unknown" and os_version != "Unknown":
        tech_components.append(f"{os_type} {os_version}")
    elif os_type != "Unknown":
        tech_components.append(os_type)
    elif os_version != "Unknown":
        tech_components.append(os_version)

    # Application version information
    app_version = get_field_value(
        asset, ["app_version", "software_version", "application_version"]
    )
    if app_version != "Unknown" and app_version not in [
        comp for comp in tech_components
    ]:
        tech_components.append(f"v{app_version}")

    # Workload/Asset Type information
    workload_type = get_field_value(
        asset, ["workload_type", "workload type", "asset_type"]
    )
    if workload_type != "Unknown" and workload_type not in [
        comp for comp in tech_components
    ]:
        tech_components.append(workload_type)

    # Database specific
    db_version = get_field_value(
        asset, ["database_version", "db_version", "db_release"]
    )
    if db_version != "Unknown":
        tech_components.append(db_version)

    # Platform information
    platform = get_field_value(asset, ["platform", "technology", "framework"])
    if platform != "Unknown" and platform not in tech_components:
        tech_components.append(platform)

    # If no tech stack info found, try to use asset type or fallback
    if not tech_components:
        asset_type = get_field_value(
            asset, ["asset_type", "ci_type", "type", "sys_class_name"]
        )
        if asset_type != "Unknown":
            tech_components.append(asset_type)

    return " | ".join(tech_components) if tech_components else "Unknown"


def generate_suggested_headers(assets: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate suggested table headers based on actual asset data."""
    if not assets:
        return []

    # Analyze the data to determine which fields are most relevant
    assets[0]
    headers = []

    # Always include basic identification fields
    headers.extend(
        [
            {
                "key": "id",
                "label": "Asset ID",
                "description": "Unique identifier for the asset",
            },
            {
                "key": "type",
                "label": "Type",
                "description": "Asset classification (Application, Server, Database)",
            },
            {"key": "name", "label": "Name", "description": "Asset name or hostname"},
        ]
    )

    # Check if we have tech stack information
    if any(
        asset.get("techStack") and asset["techStack"] != "Unknown" for asset in assets
    ):
        headers.append(
            {
                "key": "techStack",
                "label": "Tech Stack",
                "description": "Technology platform and versions",
            }
        )

    # Check if we have department information
    if any(
        asset.get("department") and asset["department"] != "Unknown" for asset in assets
    ):
        headers.append(
            {
                "key": "department",
                "label": "Department",
                "description": "Business owner or responsible department",
            }
        )

    # Check if we have environment information
    if any(
        asset.get("environment") and asset["environment"] != "Unknown"
        for asset in assets
    ):
        headers.append(
            {
                "key": "environment",
                "label": "Environment",
                "description": "Deployment environment (Production, Test, Dev)",
            }
        )

    # Check if we have criticality information
    if any(
        asset.get("criticality") and asset["criticality"] != "Medium"
        for asset in assets
    ):
        headers.append(
            {
                "key": "criticality",
                "label": "Criticality",
                "description": "Business criticality level",
            }
        )

    # Check if we have server-specific fields (for servers and databases)
    has_servers = any(asset.get("type") in ["Server", "Database"] for asset in assets)
    if has_servers:
        if any(asset.get("ipAddress") for asset in assets):
            headers.append(
                {
                    "key": "ipAddress",
                    "label": "IP Address",
                    "description": "Network IP address",
                }
            )
        if any(asset.get("operatingSystem") for asset in assets):
            headers.append(
                {
                    "key": "operatingSystem",
                    "label": "Operating System",
                    "description": "Server operating system type",
                }
            )
        if any(asset.get("osVersion") for asset in assets):
            headers.append(
                {
                    "key": "osVersion",
                    "label": "OS Version",
                    "description": "Operating system version",
                }
            )
        if any(asset.get("cpuCores") for asset in assets):
            headers.append(
                {
                    "key": "cpuCores",
                    "label": "CPU Cores",
                    "description": "Number of CPU cores",
                }
            )
        if any(asset.get("memoryGb") for asset in assets):
            headers.append(
                {
                    "key": "memoryGb",
                    "label": "Memory (GB)",
                    "description": "RAM memory in gigabytes",
                }
            )
        if any(asset.get("storageGb") for asset in assets):
            headers.append(
                {
                    "key": "storageGb",
                    "label": "Storage (GB)",
                    "description": "Storage capacity in gigabytes",
                }
            )

    # Always include status
    headers.append(
        {
            "key": "status",
            "label": "Status",
            "description": "Discovery and processing status",
        }
    )

    return headers


def assess_6r_readiness(asset_type: str, asset_data: Dict[str, Any]) -> str:
    """Assess if an asset is ready for 6R treatment analysis."""

    # Devices typically don't need 6R analysis
    device_types = [
        "Network Device",
        "Storage Device",
        "Security Device",
        "Infrastructure Device",
    ]
    if asset_type in device_types:
        return "Not Applicable"

    # Check for minimum required data
    has_name = bool(asset_data.get("Name") or asset_data.get("asset_name"))
    has_environment = bool(
        asset_data.get("Environment") or asset_data.get("environment")
    )
    has_owner = bool(
        asset_data.get("Business_Owner") or asset_data.get("business_owner")
    )

    if asset_type == "Application":
        # Applications need name, environment, owner
        if has_name and has_environment and has_owner:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Owner Info"
        else:
            return "Insufficient Data"

    elif asset_type == "Server":
        # Servers need infrastructure specs
        try:
            cpu_cores = int(
                float(asset_data.get("CPU_Cores", asset_data.get("cpu_cores", 0)) or 0)
            )
        except (ValueError, TypeError):
            cpu_cores = 0

        try:
            memory_gb = int(
                float(asset_data.get("Memory_GB", asset_data.get("memory_gb", 0)) or 0)
            )
        except (ValueError, TypeError):
            memory_gb = 0

        has_os = bool(asset_data.get("OS") or asset_data.get("operating_system"))

        if has_name and has_environment and cpu_cores > 0 and memory_gb > 0 and has_os:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Infrastructure Data"
        else:
            return "Insufficient Data"

    elif asset_type == "Database":
        # Databases need version and host info
        has_version = bool(
            asset_data.get("Version") or asset_data.get("database_version")
        )
        bool(asset_data.get("Host") or asset_data.get("hostname"))

        if has_name and has_environment and has_version:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Version Info"
        else:
            return "Insufficient Data"

    elif asset_type == "Virtualization Platform":
        return "Complex Analysis Required"

    else:  # Unknown type
        return "Type Classification Needed"


def assess_migration_complexity(asset_type: str, asset_data: Dict[str, Any]) -> str:
    """Assess the migration complexity of an asset."""

    # Devices typically have low complexity
    device_types = [
        "Network Device",
        "Storage Device",
        "Security Device",
        "Infrastructure Device",
    ]
    if asset_type in device_types:
        return "Low"

    if asset_type == "Application":
        # Check for complexity indicators
        has_dependencies = bool(
            asset_data.get("Related_CI") or asset_data.get("dependencies")
        )
        is_critical = str(asset_data.get("Criticality", "")).lower() in [
            "high",
            "critical",
        ]
        is_production = str(asset_data.get("Environment", "")).lower() == "production"

        complexity_score = 0
        if has_dependencies:
            complexity_score += 2
        if is_critical:
            complexity_score += 2
        if is_production:
            complexity_score += 1

        if complexity_score >= 4:
            return "High"
        elif complexity_score >= 2:
            return "Medium"
        else:
            return "Low"

    elif asset_type == "Server":
        # Server complexity based on specs and usage
        try:
            cpu_cores = int(
                float(asset_data.get("CPU_Cores", asset_data.get("cpu_cores", 0)) or 0)
            )
        except (ValueError, TypeError):
            cpu_cores = 0

        try:
            memory_gb = int(
                float(asset_data.get("Memory_GB", asset_data.get("memory_gb", 0)) or 0)
            )
        except (ValueError, TypeError):
            memory_gb = 0

        is_production = str(asset_data.get("Environment", "")).lower() == "production"

        complexity_score = 0
        if cpu_cores > 16:
            complexity_score += 2
        elif cpu_cores > 8:
            complexity_score += 1

        if memory_gb > 64:
            complexity_score += 2
        elif memory_gb > 32:
            complexity_score += 1

        if is_production:
            complexity_score += 1

        if complexity_score >= 4:
            return "High"
        elif complexity_score >= 2:
            return "Medium"
        else:
            return "Low"

    elif asset_type == "Database":
        # Databases are typically medium to high complexity
        is_critical = str(asset_data.get("Criticality", "")).lower() in [
            "high",
            "critical",
        ]
        is_production = str(asset_data.get("Environment", "")).lower() == "production"

        if is_critical and is_production:
            return "High"
        elif is_production:
            return "Medium"
        else:
            return "Low"

    elif asset_type == "Virtualization Platform":
        return "High"

    else:
        return "Medium"


def crewai_available() -> bool:
    """Check if the CrewAI service is available."""
    return CREWAI_AVAILABLE


def analyze_data_source(
    data_source_id: str, crewai_flow_service: CrewAIFlowService = None
) -> dict:
    """Analyze a data source and return its type and quality."""
    if not crewai_available():
        return {"error": "CrewAI service is not available"}, 503

    if crewai_flow_service is None:
        # Initialize service if not provided
        try:
            crewai_flow_service = CrewAIFlowService()
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI service: {e}")
            return {"error": "Failed to initialize CrewAI service"}, 503

    crewai_flow_service.create_task(
        agent_name="data_source_intelligence_001",
        task_description=f"Analyze data source: {data_source_id}",
        context=f"Analyze the data source with ID {data_source_id} and determine its type and quality.",
    )

    # This is a placeholder implementation. In a real application, you would wait for the task to
    # complete and return the result.
    return {"status": "Analysis in progress"}
