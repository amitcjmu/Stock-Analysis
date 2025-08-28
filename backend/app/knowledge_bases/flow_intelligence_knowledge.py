"""
Flow Intelligence Knowledge Base
Comprehensive knowledge for the Flow Processing Agent

This knowledge base provides the agent with:
- Complete flow definitions and phases
- Success criteria for each phase
- Navigation paths and user actions
- Service mappings for validation
- Context requirements for multi-tenant operations
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class FlowType(Enum):
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    EXECUTION = "execution"
    DECOMMISSION = "decommission"
    FINOPS = "finops"
    MODERNIZE = "modernize"


class PhaseStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ActionType(Enum):
    USER_ACTION = "user_action"  # User needs to do something
    SYSTEM_ACTION = "system_action"  # System needs to process something
    NAVIGATION = "navigation"  # Simple navigation to view results


# Complete Flow Definitions
FLOW_DEFINITIONS = {
    FlowType.DISCOVERY: {
        "name": "Discovery Flow",
        "description": "Asset discovery and inventory management",
        "phases": [
            {
                "id": "data_import",
                "name": "Data Import",
                "description": "Import asset data from various sources",
                "success_criteria": [
                    "At least 1 data file uploaded successfully",
                    "Raw data records > 0 in database",
                    "Import status = 'completed'",
                    "No critical import errors",
                ],
                "user_actions": [
                    "Upload CSV/Excel files with asset data",
                    "Configure data source connections",
                    "Review and fix import errors",
                ],
                "system_actions": [
                    "Process uploaded files",
                    "Validate data formats",
                    "Store raw data in database",
                ],
                "validation_services": [
                    "data_import_service.get_latest_import",
                    "data_import_service.get_import_stats",
                    "raw_data_repository.count_records",
                ],
                "navigation_path": "/discovery/cmdb-import",
            },
            {
                "id": "attribute_mapping",
                "name": "Attribute Mapping",
                "description": "Map imported fields to critical attributes",
                "success_criteria": [
                    "At least 80% of critical attributes mapped",
                    "Required identity attributes mapped (name, id)",
                    "Mapping confidence > 0.7",
                    "Field mapping saved successfully",
                ],
                "user_actions": [
                    "Review suggested field mappings",
                    "Manually map unmapped fields",
                    "Validate mapping accuracy",
                    "Save final mapping configuration",
                ],
                "system_actions": [
                    "Generate AI-powered mapping suggestions",
                    "Calculate mapping confidence scores",
                    "Apply mapping transformations",
                ],
                "validation_services": [
                    "field_mapper_service.get_mapping_status",
                    "field_mapper_service.calculate_coverage",
                    "critical_attributes_service.validate_mappings",
                ],
                "navigation_path": "/discovery/attribute-mapping/{flow_id}",
            },
            {
                "id": "data_cleansing",
                "name": "Data Cleansing",
                "description": "Clean and standardize asset data",
                "success_criteria": [
                    "Data quality score > 80%",
                    "Critical validation errors = 0",
                    "Duplicate records resolved",
                    "Standardization rules applied",
                ],
                "user_actions": [
                    "Review data quality issues",
                    "Resolve duplicate records",
                    "Fix validation errors",
                    "Apply cleansing rules",
                ],
                "system_actions": [
                    "Run data quality analysis",
                    "Detect duplicate records",
                    "Apply standardization rules",
                    "Generate quality reports",
                ],
                "validation_services": [
                    "data_cleansing_service.get_quality_score",
                    "data_cleansing_service.get_validation_results",
                    "duplicate_detection_service.get_duplicates",
                ],
                "navigation_path": "/discovery/data-cleansing/{flow_id}",
            },
            {
                "id": "inventory",
                "name": "Asset Inventory",
                "description": "Generate comprehensive asset inventory",
                "success_criteria": [
                    "All assets categorized and classified",
                    "Asset relationships identified",
                    "Inventory completeness > 95%",
                    "Asset profiles generated",
                ],
                "user_actions": [
                    "Review asset classifications",
                    "Validate asset categories",
                    "Update asset profiles",
                    "Confirm inventory accuracy",
                ],
                "system_actions": [
                    "Classify assets using AI",
                    "Generate asset profiles",
                    "Calculate inventory metrics",
                    "Create asset hierarchy",
                ],
                "validation_services": [
                    "asset_service.get_classification_status",
                    "asset_service.get_inventory_completeness",
                    "asset_service.get_categorization_results",
                ],
                "navigation_path": "/discovery/inventory/{flow_id}",
            },
            {
                "id": "dependencies",
                "name": "Dependency Analysis",
                "description": "Analyze asset dependencies and relationships",
                "success_criteria": [
                    "Dependency mapping completed",
                    "Critical dependencies identified",
                    "Dependency confidence > 0.8",
                    "Dependency graph generated",
                ],
                "user_actions": [
                    "Review dependency mappings",
                    "Validate critical dependencies",
                    "Update dependency relationships",
                    "Approve dependency analysis",
                ],
                "system_actions": [
                    "Analyze asset dependencies",
                    "Generate dependency graphs",
                    "Calculate dependency scores",
                    "Identify critical paths",
                ],
                "validation_services": [
                    "dependency_service.get_analysis_status",
                    "dependency_service.get_dependency_count",
                    "dependency_service.get_critical_dependencies",
                ],
                "navigation_path": "/discovery/dependencies/{flow_id}",
            },
            {
                "id": "tech_debt",
                "name": "Technical Debt Analysis",
                "description": "Analyze technical debt and modernization opportunities",
                "success_criteria": [
                    "Tech debt assessment completed",
                    "Modernization opportunities identified",
                    "Risk levels calculated",
                    "Recommendations generated",
                ],
                "user_actions": [
                    "Review tech debt analysis",
                    "Validate risk assessments",
                    "Prioritize modernization opportunities",
                    "Approve recommendations",
                ],
                "system_actions": [
                    "Analyze technical debt",
                    "Calculate risk scores",
                    "Generate modernization recommendations",
                    "Create priority matrices",
                ],
                "validation_services": [
                    "tech_debt_service.get_analysis_status",
                    "tech_debt_service.get_debt_score",
                    "tech_debt_service.get_recommendations",
                ],
                "navigation_path": "/discovery/tech-debt/{flow_id}",
            },
        ],
    },
    FlowType.ASSESSMENT: {
        "name": "Assessment Flow",
        "description": "Migration readiness and impact assessment",
        "phases": [
            {
                "id": "readiness_assessment",
                "name": "Readiness Assessment",
                "description": "Assess migration readiness across all dimensions",
                "success_criteria": [
                    "All assessment categories completed",
                    "Readiness score calculated",
                    "Risk factors identified",
                    "Recommendations generated",
                ],
                "user_actions": [
                    "Complete assessment questionnaires",
                    "Review readiness scores",
                    "Address identified gaps",
                    "Validate assessment results",
                ],
                "system_actions": [
                    "Calculate readiness scores",
                    "Analyze risk factors",
                    "Generate recommendations",
                    "Create readiness reports",
                ],
                "validation_services": [
                    "assessment_service.get_readiness_status",
                    "assessment_service.get_readiness_score",
                    "assessment_service.get_risk_factors",
                ],
                "navigation_path": "/assess/readiness/{flow_id}",
            },
            {
                "id": "impact_analysis",
                "name": "Impact Analysis",
                "description": "Analyze migration impact on business and operations",
                "success_criteria": [
                    "Impact analysis completed",
                    "Business impact assessed",
                    "Operational impact evaluated",
                    "Mitigation strategies defined",
                ],
                "user_actions": [
                    "Review impact assessments",
                    "Validate business impacts",
                    "Define mitigation strategies",
                    "Approve impact analysis",
                ],
                "system_actions": [
                    "Calculate business impact",
                    "Assess operational changes",
                    "Generate impact reports",
                    "Suggest mitigation strategies",
                ],
                "validation_services": [
                    "impact_service.get_analysis_status",
                    "impact_service.get_business_impact",
                    "impact_service.get_operational_impact",
                ],
                "navigation_path": "/assess/impact/{flow_id}",
            },
        ],
    },
}

# Context Services for Multi-Tenant Operations
CONTEXT_SERVICES = {
    "client_context": {
        "service": "context_service.get_client_context",
        "description": "Get client account context for multi-tenant operations",
        "required_params": ["client_account_id"],
        "returns": "Client account details and configuration",
    },
    "engagement_context": {
        "service": "context_service.get_engagement_context",
        "description": "Get engagement context for scoped operations",
        "required_params": ["client_account_id", "engagement_id"],
        "returns": "Engagement details and scope",
    },
    "user_context": {
        "service": "context_service.get_user_context",
        "description": "Get user context and permissions",
        "required_params": ["user_id"],
        "returns": "User details and access permissions",
    },
}

# Navigation Rules
NAVIGATION_RULES = {
    "user_action_required": {
        "description": "User needs to perform an action to continue",
        "routing_pattern": "/flow_type/phase_id/{flow_id}",
        "examples": [
            "/discovery/cmdb-import",  # No flow_id for data import
            "/discovery/attribute-mapping/123",
        ],
    },
    "system_processing": {
        "description": "System is processing, user should wait or check status",
        "routing_pattern": "/flow_type/overview/{flow_id}",
        "examples": ["/discovery/overview/123", "/assess/overview/123"],
    },
    "phase_complete": {
        "description": "Phase is complete, user can proceed to next phase",
        "routing_pattern": "/flow_type/next_phase/{flow_id}",
        "examples": [
            "/discovery/attribute-mapping/123",
            "/discovery/data-cleansing/123",
        ],
    },
    "flow_complete": {
        "description": "Entire flow is complete, user can view results or start next flow",
        "routing_pattern": "/discovery/overview or /collection/progress/{flow_id}",
        "examples": ["/discovery/overview", "/collection/progress/123"],
    },
}

# Agent Intelligence Guidelines
AGENT_INTELLIGENCE = {
    "decision_framework": [
        "1. Determine flow type and current phase using flow_id",
        "2. Get proper context (client, engagement, user) for multi-tenant operations",
        "3. Validate current phase completion using appropriate services",
        "4. Identify specific issues or blockers preventing progress",
        "5. Distinguish between user actions and system actions needed",
        "6. Provide specific, actionable guidance (not vague instructions)",
        "7. Route user to appropriate page where they can take action",
    ],
    "actionable_guidance": {
        "principles": [
            "Be specific about what the user needs to do",
            "Distinguish between user actions and system actions",
            "Provide context about why the action is needed",
            "Include expected outcomes of the action",
            "Avoid vague instructions like 'ensure completion'",
        ],
        "good_examples": [
            "Go to the Data Import page and upload a CSV file containing at least 100 asset records",
            "Review the field mapping suggestions and manually map the 'Server Name' field to the 'hostname' attribute",
            "Resolve the 15 duplicate server records found in the data cleansing analysis",
        ],
        "bad_examples": [
            "Complete the data import phase",
            "Ensure data import is finished",
            "Fix the issues and try again",
        ],
    },
    "context_usage": {
        "always_get_context": [
            "Use client_account_id for all database queries",
            "Use engagement_id to scope flow operations",
            "Use user_id for permission checks",
            "Use session_id for tracking user actions",
        ],
        "context_flow": [
            "1. Extract context from request headers or parameters",
            "2. Validate context using context services",
            "3. Pass context to all service calls",
            "4. Ensure all operations are properly scoped",
        ],
    },
    "service_usage": {
        "validation_pattern": [
            "1. Call appropriate validation service for the phase",
            "2. Check specific success criteria (not just generic status)",
            "3. Identify exact issues preventing completion",
            "4. Determine if issue requires user action or system action",
            "5. Provide specific remediation steps",
        ],
        "error_handling": [
            "Handle service failures gracefully",
            "Provide fallback analysis when services are unavailable",
            "Log specific errors for debugging",
            "Never leave user without guidance",
        ],
    },
}


def get_flow_definition(flow_type: FlowType) -> Dict[str, Any]:
    """Get complete flow definition including all phases and criteria"""
    return FLOW_DEFINITIONS.get(flow_type, {})


def get_phase_definition(flow_type: FlowType, phase_id: str) -> Dict[str, Any]:
    """Get specific phase definition with success criteria and actions"""
    flow_def = get_flow_definition(flow_type)
    phases = flow_def.get("phases", [])

    for phase in phases:
        if phase["id"] == phase_id:
            return phase

    return {}


def get_next_phase(flow_type: FlowType, current_phase: str) -> Optional[str]:
    """Get the next phase in the flow sequence"""
    flow_def = get_flow_definition(flow_type)
    phases = flow_def.get("phases", [])

    for i, phase in enumerate(phases):
        if phase["id"] == current_phase and i + 1 < len(phases):
            return phases[i + 1]["id"]

    return None


def get_navigation_path(
    flow_type: FlowType,
    phase_id: str,
    flow_id: str,
    action_type: ActionType = ActionType.USER_ACTION,
) -> str:
    """Get the navigation path for a specific phase and action type"""
    phase_def = get_phase_definition(flow_type, phase_id)

    if not phase_def:
        # FIXED: Always include flow_id in overview paths to maintain routing context
        return f"/{flow_type.value}/overview/{flow_id}"

    base_path = phase_def.get("navigation_path", f"/{flow_type.value}/{phase_id}")

    # Substitute flow_id in path template or add as parameter for non-parametric paths
    if "{flow_id}" in base_path:
        return base_path.format(flow_id=flow_id)
    else:
        # For paths that don't expect flow_id in path (like data import)
        # Only data_import phase should not have flow_id in path
        if phase_id == "data_import":
            if "?" in base_path:
                return f"{base_path}&flow_id={flow_id}"
            else:
                return base_path
        else:
            # All other phases must carry flow_id in the path
            return f"{base_path}/{flow_id}"


def get_validation_services(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get list of validation services for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("validation_services", [])


def get_success_criteria(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get success criteria for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("success_criteria", [])


def get_user_actions(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get user actions required for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("user_actions", [])


def get_system_actions(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get system actions required for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("system_actions", [])
