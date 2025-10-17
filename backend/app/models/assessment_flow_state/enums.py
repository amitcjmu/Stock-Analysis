"""
Assessment Flow State Enums
All enum definitions for assessment flow state management.

Note: SixRStrategy has been moved to app.models.asset.enums (canonical location).
Import from there instead: from app.models.asset.enums import SixRStrategy
"""

from enum import Enum


class AssessmentPhase(str, Enum):
    """Assessment flow phases in order of execution (ADR-027)

    Canonical Assessment Phases (October 2025):
    These phases align with ADR-027 Universal FlowTypeConfig Pattern.
    Phase configs are defined in backend/app/services/flow_configs/assessment_phases/

    Deprecated values (removed October 2025):
    - architecture_minimums → readiness_assessment
    - tech_debt_analysis → split into complexity_analysis + tech_debt_assessment
    - component_sixr_strategies → risk_assessment
    - app_on_page_generation → recommendation_generation
    - dependency_analysis moved from Discovery to Assessment per ADR-027
    """

    INITIALIZATION = "initialization"
    READINESS_ASSESSMENT = "readiness_assessment"
    COMPLEXITY_ANALYSIS = "complexity_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ASSESSMENT = "tech_debt_assessment"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATION_GENERATION = "recommendation_generation"
    FINALIZATION = "finalization"


class AssessmentFlowStatus(str, Enum):
    """Assessment flow status values"""

    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TechDebtSeverity(str, Enum):
    """Tech debt severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComponentType(str, Enum):
    """Application component types"""

    FRONTEND = "frontend"
    MIDDLEWARE = "middleware"
    BACKEND = "backend"
    DATABASE = "database"
    SERVICE = "service"
    API = "api"
    UI = "ui"
    CUSTOM = "custom"


class OverrideType(str, Enum):
    """Architecture override types"""

    EXCEPTION = "exception"
    MODIFICATION = "modification"
    ADDITION = "addition"
