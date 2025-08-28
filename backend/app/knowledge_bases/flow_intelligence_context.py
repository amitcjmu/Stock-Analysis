"""
Flow Intelligence Knowledge Base - Context and Rules
Context services and navigation rules for flow processing
"""

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
