"""
Flow Intelligence Knowledge Base
Comprehensive knowledge for the Flow Processing Agent to understand:
- Flow types and their purposes
- Phases within each flow and their sequence
- Success criteria for each phase
- Navigation paths and user actions
- Available services and tools for validation
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class PhaseDefinition:
    """Definition of a phase within a flow"""
    name: str
    display_name: str
    description: str
    success_criteria: List[str]
    validation_service: str
    validation_endpoint: str
    user_actions: List[str]
    system_actions: List[str]
    navigation_route: str
    dependencies: List[str]
    estimated_time_minutes: int

@dataclass
class FlowDefinition:
    """Definition of a complete flow"""
    name: str
    display_name: str
    description: str
    phases: List[PhaseDefinition]
    entry_point: str
    completion_route: str
    purpose: str

# DISCOVERY FLOW DEFINITION
DISCOVERY_FLOW = FlowDefinition(
    name="discovery",
    display_name="Discovery Flow",
    description="Comprehensive asset discovery and analysis flow for migration planning",
    purpose="Analyze existing infrastructure to understand what needs to be migrated",
    entry_point="/discovery/data-import",
    completion_route="/assess",
    phases=[
        PhaseDefinition(
            name="data_import",
            display_name="Data Import",
            description="Import and validate source data files (CMDB, infrastructure, applications)",
            success_criteria=[
                "At least 5 raw records imported",
                "Data successfully parsed and stored",
                "No critical validation errors",
                "Import session created with valid flow_id"
            ],
            validation_service="data_import_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/data_import",
            user_actions=[
                "Upload CSV/Excel files with asset data",
                "Select appropriate data category (CMDB, App Discovery, Infrastructure)",
                "Review and confirm file format",
                "Retry upload if validation fails"
            ],
            system_actions=[
                "Parse uploaded files",
                "Validate data format and structure",
                "Create import session and flow_id",
                "Store raw records in database",
                "Trigger initial data analysis"
            ],
            navigation_route="/discovery/data-import",
            dependencies=[],
            estimated_time_minutes=10
        ),
        PhaseDefinition(
            name="attribute_mapping",
            display_name="Attribute Mapping",
            description="Map imported fields to standardized migration attributes",
            success_criteria=[
                "At least 3 field mappings approved",
                "All critical attributes mapped (asset_name, asset_type, environment)",
                "Mapping confidence scores above 70%",
                "No unmapped critical fields"
            ],
            validation_service="field_mapping_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/attribute_mapping",
            user_actions=[
                "Review suggested field mappings",
                "Approve or modify mapping suggestions",
                "Map unmapped critical fields manually",
                "Validate mapping accuracy"
            ],
            system_actions=[
                "Analyze field patterns using AI",
                "Generate mapping suggestions",
                "Calculate confidence scores",
                "Update field mapping database"
            ],
            navigation_route="/discovery/attribute-mapping",
            dependencies=["data_import"],
            estimated_time_minutes=15
        ),
        PhaseDefinition(
            name="data_cleansing",
            display_name="Data Cleansing",
            description="Clean and standardize imported data for analysis",
            success_criteria=[
                "Data quality score above 80%",
                "Duplicate records resolved",
                "Missing critical data filled or flagged",
                "Data format standardized"
            ],
            validation_service="data_quality_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/data_cleansing",
            user_actions=[
                "Review data quality issues",
                "Resolve duplicate entries",
                "Provide missing information",
                "Approve cleansing recommendations"
            ],
            system_actions=[
                "Identify data quality issues",
                "Suggest cleansing actions",
                "Apply approved cleansing rules",
                "Generate data quality report"
            ],
            navigation_route="/discovery/data-cleansing",
            dependencies=["attribute_mapping"],
            estimated_time_minutes=20
        ),
        PhaseDefinition(
            name="inventory",
            display_name="Asset Inventory",
            description="Build comprehensive asset inventory with classifications",
            success_criteria=[
                "All assets classified by type",
                "Business criticality assigned",
                "Technical complexity scored",
                "Migration wave assignments suggested"
            ],
            validation_service="inventory_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/inventory",
            user_actions=[
                "Review asset classifications",
                "Adjust business criticality ratings",
                "Validate technical assessments",
                "Approve inventory completeness"
            ],
            system_actions=[
                "Classify assets using AI analysis",
                "Calculate business impact scores",
                "Assess technical complexity",
                "Generate migration recommendations"
            ],
            navigation_route="/discovery/inventory",
            dependencies=["data_cleansing"],
            estimated_time_minutes=25
        ),
        PhaseDefinition(
            name="dependencies",
            display_name="Dependency Analysis",
            description="Identify and map asset dependencies and relationships",
            success_criteria=[
                "Application dependencies mapped",
                "Infrastructure dependencies identified",
                "Network dependencies documented",
                "Dependency risks assessed"
            ],
            validation_service="dependency_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/dependencies",
            user_actions=[
                "Review dependency mappings",
                "Add missing dependencies",
                "Validate relationship accuracy",
                "Assess dependency risks"
            ],
            system_actions=[
                "Analyze network connections",
                "Identify application relationships",
                "Map infrastructure dependencies",
                "Calculate dependency complexity"
            ],
            navigation_route="/discovery/dependencies",
            dependencies=["inventory"],
            estimated_time_minutes=30
        ),
        PhaseDefinition(
            name="tech_debt",
            display_name="Technical Debt Analysis",
            description="Assess technical debt and modernization opportunities",
            success_criteria=[
                "Technical debt scored for all assets",
                "Modernization opportunities identified",
                "Legacy system risks documented",
                "Modernization roadmap suggested"
            ],
            validation_service="tech_debt_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/tech_debt",
            user_actions=[
                "Review technical assessments",
                "Validate modernization suggestions",
                "Prioritize technical debt items",
                "Approve analysis completeness"
            ],
            system_actions=[
                "Analyze technology stacks",
                "Identify legacy components",
                "Calculate modernization ROI",
                "Generate tech debt report"
            ],
            navigation_route="/discovery/tech-debt",
            dependencies=["dependencies"],
            estimated_time_minutes=20
        )
    ]
)

# ASSESS FLOW DEFINITION
ASSESS_FLOW = FlowDefinition(
    name="assess",
    display_name="Assessment Flow",
    description="Comprehensive migration readiness and impact assessment",
    purpose="Evaluate migration readiness and plan migration approach",
    entry_point="/assess/migration-readiness",
    completion_route="/plan",
    phases=[
        PhaseDefinition(
            name="migration_readiness",
            display_name="Migration Readiness",
            description="Assess overall readiness for migration",
            success_criteria=[
                "Readiness score calculated for all assets",
                "Blockers identified and documented",
                "Dependencies validated",
                "Risk assessment completed"
            ],
            validation_service="readiness_validation",
            validation_endpoint="/api/v1/flow-processing/validate-phase/{flow_id}/migration_readiness",
            user_actions=[
                "Review readiness assessments",
                "Address identified blockers",
                "Validate dependency mappings",
                "Approve readiness scores"
            ],
            system_actions=[
                "Calculate readiness scores",
                "Identify migration blockers",
                "Assess dependency impacts",
                "Generate readiness report"
            ],
            navigation_route="/assess/migration-readiness",
            dependencies=[],
            estimated_time_minutes=25
        )
    ]
)

# ALL FLOWS REGISTRY
FLOW_REGISTRY = {
    "discovery": DISCOVERY_FLOW,
    "assess": ASSESS_FLOW,
    # Additional flows can be added here
}

# CONTEXT SERVICES MAPPING
CONTEXT_SERVICES = {
    "flow_status": {
        "service": "FlowManagementHandler",
        "endpoint": "/api/v1/discovery/flow/status/{flow_id}",
        "description": "Get comprehensive flow status including phases, progress, and data"
    },
    "import_status": {
        "service": "ImportStorageHandler", 
        "endpoint": "/api/v1/data-import/processing-status/{import_session_id}",
        "description": "Get import session status with record counts and processing progress"
    },
    "validation": {
        "service": "PhaseValidationService",
        "endpoint": "/api/v1/flow-processing/validate-phase/{flow_id}/{phase}",
        "description": "Validate specific phase completion with detailed criteria checking"
    },
    "context_extraction": {
        "service": "RequestContext",
        "endpoint": "/api/v1/context/extract/{flow_id}",
        "description": "Extract client_account_id and engagement_id from flow_id for proper context scoping"
    }
}

# NAVIGATION RULES
NAVIGATION_RULES = {
    "user_needs_to_upload_data": "/discovery/data-import",
    "user_needs_to_configure_mappings": "/discovery/attribute-mapping?flow_id={flow_id}",
    "user_needs_to_review_cleansing": "/discovery/data-cleansing?flow_id={flow_id}",
    "user_needs_to_validate_inventory": "/discovery/inventory?flow_id={flow_id}",
    "user_needs_to_review_dependencies": "/discovery/dependencies?flow_id={flow_id}",
    "user_needs_to_assess_tech_debt": "/discovery/tech-debt?flow_id={flow_id}",
    "system_processing_required": "/discovery/enhanced-dashboard?flow_id={flow_id}&action=processing",
    "phase_complete_advance": "next_phase_route",
    "flow_complete": "/assess?flow_id={flow_id}",
    "error_occurred": "/discovery/enhanced-dashboard?flow_id={flow_id}&error=true"
}

# AGENT INTELLIGENCE GUIDELINES
AGENT_GUIDELINES = {
    "primary_goal": "Provide specific, actionable guidance that distinguishes between user actions and system actions",
    "analysis_approach": "Use real validation services to get accurate status, don't rely on hardcoded assumptions",
    "user_guidance_principles": [
        "Never tell users to 'ensure completion' of something they can't control",
        "Always provide specific, actionable steps",
        "Route users to pages where they can actually take required actions",
        "For system issues, explain that background processing is needed"
    ],
    "context_awareness": [
        "Always extract proper context (client_account_id, engagement_id) for flow operations",
        "Scope all data queries to the correct tenant context",
        "Understand that flows are tied to specific engagements and clients"
    ],
    "validation_strategy": [
        "Use fail-fast approach - stop at first incomplete phase",
        "Check actual data counts and thresholds, not just flags",
        "Validate success criteria against real data, not assumptions",
        "Provide specific details about what failed and why"
    ]
}

def get_flow_definition(flow_type: str) -> FlowDefinition:
    """Get flow definition by type"""
    return FLOW_REGISTRY.get(flow_type, DISCOVERY_FLOW)

def get_phase_definition(flow_type: str, phase_name: str) -> PhaseDefinition:
    """Get phase definition by flow type and phase name"""
    flow = get_flow_definition(flow_type)
    for phase in flow.phases:
        if phase.name == phase_name:
            return phase
    return None

def get_next_phase(flow_type: str, current_phase: str) -> str:
    """Get the next phase in the flow sequence"""
    flow = get_flow_definition(flow_type)
    phase_names = [phase.name for phase in flow.phases]
    
    try:
        current_index = phase_names.index(current_phase)
        if current_index + 1 < len(phase_names):
            return phase_names[current_index + 1]
        else:
            return "completed"
    except ValueError:
        return phase_names[0] if phase_names else "unknown"

def get_navigation_route(situation: str, **kwargs) -> str:
    """Get navigation route for a specific situation"""
    route_template = NAVIGATION_RULES.get(situation, "/discovery/enhanced-dashboard")
    return route_template.format(**kwargs)

def get_context_service(service_name: str) -> Dict[str, str]:
    """Get context service information"""
    return CONTEXT_SERVICES.get(service_name, {}) 