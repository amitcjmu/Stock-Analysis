"""
Canonical API tag definitions for OpenAPI documentation.

This module defines all allowed tags for API endpoints to ensure consistency
across the application. Tags should only be applied at the include_router level,
never in the endpoint files themselves.
"""


# Canonical tag names - Title Case, singular where appropriate
class APITags:
    """Centralized API tag constants to prevent drift."""

    # Authentication & User Management
    AUTHENTICATION = "Authentication"
    USER_MANAGEMENT = "User Management"
    ADMIN_USER_MANAGEMENT = "Admin User Management"
    DEMO_FUNCTIONS = "Demo Functions"

    # Data Import & Processing
    DATA_IMPORT_CORE = "Data Import Core"
    FIELD_MAPPING = "Field Mapping"
    FIELD_MAPPING_ANALYSIS = "Field Mapping Analysis"
    FIELD_MAPPING_CRUD = "Field Mapping CRUD"
    FIELD_MAPPING_SUGGESTIONS = "Field Mapping Suggestions"
    FIELD_MAPPING_UTILITIES = "Field Mapping Utilities"
    IMPORT_STORAGE = "Import Storage"
    IMPORT_RETRIEVAL = "Import Retrieval"
    ASSET_PROCESSING = "Asset Processing"
    CANONICAL_APPLICATIONS = "Canonical Applications"
    CRITICAL_ATTRIBUTES = "Critical Attributes"
    CLEAN_API = "Clean API"

    # Administration
    ADMIN = "Admin"
    CLIENT_MANAGEMENT = "Client Management"
    ENGAGEMENT_MANAGEMENT = "Admin - Engagement Management"
    PLATFORM_ADMIN = "Platform Admin"
    ADMIN_OPERATIONS = "Admin Operations"
    SECURITY_MONITORING = "Security Monitoring"
    FLOW_COMPARISON = "Flow Comparison"

    # Monitoring & Analytics
    AGENT_MONITORING = "Agent Monitoring"
    AGENT_PERFORMANCE = "Agent Performance"
    CREWAI_FLOW_MONITORING = "CrewAI Flow Monitoring"
    ERROR_MONITORING = "Error Monitoring"
    HEALTH_METRICS = "Health & Metrics"
    ANALYSIS_QUEUES = "Analysis Queues"

    # Business Operations
    FINOPS = "FinOps"
    ADMIN_LLM_USAGE = "Admin - LLM Usage"
    MASTER_FLOW_COORDINATION = "Master Flow Coordination"
    AI_LEARNING = "AI Learning"

    # Assessment & Workflow
    ASSESSMENT_FLOW_MANAGEMENT = "Assessment Flow Management"
    ARCHITECTURE_STANDARDS = "Architecture Standards"
    COMPONENT_ANALYSIS = "Component Analysis"
    TECH_DEBT_ANALYSIS = "Tech Debt Analysis"
    SIXR_DECISIONS = "6R Decisions"
    FLOW_FINALIZATION = "Flow Finalization"

    # Discovery & Collection
    UNIFIED_DISCOVERY = "Unified Discovery"
    COLLECTION_FLOW = "Collection Flow"
    COLLECTION_GAP_ANALYSIS = "Collection Gap Analysis"
    DEPENDENCY_ANALYSIS = "Dependency Analysis"
    AGENT_INSIGHTS = "Agent Insights"

    # System
    SYSTEM_HEALTH = "System Health"
    EMERGENCY_CONTROL = "Emergency Control"
    WEBSOCKET_CACHE = "WebSocket Cache"
    CACHED_CONTEXT = "Cached Context"

    # Legacy/Migration
    LEGACY_UPLOAD = "Legacy Upload"
    QUALITY_ANALYSIS = "Quality Analysis"

    @classmethod
    def get_all_tags(cls) -> list[str]:
        """Return all defined tags for validation."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("_") and isinstance(value, str)
        ]

    @classmethod
    def validate_tag(cls, tag: str) -> bool:
        """Check if a tag is in the canonical list."""
        return tag in cls.get_all_tags()


# Legacy tag mappings for backward compatibility
LEGACY_TAG_MAPPINGS = {
    "platform-admin": APITags.PLATFORM_ADMIN,
    "security-monitoring": APITags.SECURITY_MONITORING,
    "6R Decisions": APITags.SIXR_DECISIONS,
    "Admin Engagement Management": APITags.ENGAGEMENT_MANAGEMENT,
    "Field Mapping - CRUD": APITags.FIELD_MAPPING_CRUD,
    "Field Mapping - Analysis": APITags.FIELD_MAPPING_ANALYSIS,
    "Field Mapping - Utilities": APITags.FIELD_MAPPING_UTILITIES,
}


def normalize_tag(tag: str) -> str:
    """
    Normalize a tag to its canonical form.

    Args:
        tag: The tag to normalize

    Returns:
        The canonical tag name, or the original if not found
    """
    return LEGACY_TAG_MAPPINGS.get(tag, tag)
