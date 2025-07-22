"""
Assessment Flow State Models - Pydantic v2 Models
Complete Pydantic models for assessment flow state management with proper typing and validation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# === CORE ENUMS ===

class SixRStrategy(str, Enum):
    """The six strategies for cloud migration (6R framework)"""
    REWRITE = "rewrite"
    REARCHITECT = "rearchitect" 
    REFACTOR = "refactor"
    REPLATFORM = "replatform"
    REHOST = "rehost"
    REPURCHASE = "repurchase"
    RETIRE = "retire"
    RETAIN = "retain"

class AssessmentPhase(str, Enum):
    """Assessment flow phases in order of execution"""
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    COMPONENT_DISCOVERY = "component_discovery"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies" 
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
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

# === ARCHITECTURE STANDARDS MODELS ===

class ArchitectureRequirement(BaseModel):
    """Engagement-level architecture requirement definition"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    requirement_type: str = Field(..., description="Type of requirement (e.g., 'java_versions', 'security_standards')")
    description: str = Field(..., description="Human-readable description of the requirement")
    mandatory: bool = Field(default=True, description="Whether this requirement is mandatory or optional")
    supported_versions: Optional[Dict[str, str]] = Field(default=None, description="Supported technology versions")
    requirement_details: Optional[Dict[str, Any]] = Field(default=None, description="Additional requirement specifications")
    created_by: Optional[str] = Field(default=None, description="Who created this requirement")
    created_at: Optional[datetime] = Field(default=None, description="When this requirement was created")
    updated_at: Optional[datetime] = Field(default=None, description="When this requirement was last updated")

class ApplicationArchitectureOverride(BaseModel):
    """Application-specific architecture override with rationale"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    application_id: UUID = Field(..., description="UUID of the application")
    standard_id: Optional[UUID] = Field(default=None, description="UUID of the standard being overridden")
    override_type: OverrideType = Field(..., description="Type of override")
    override_details: Optional[Dict[str, Any]] = Field(default=None, description="Details of the override")
    rationale: str = Field(..., description="Business rationale for the override")
    approved_by: Optional[str] = Field(default=None, description="Who approved this override")
    created_at: Optional[datetime] = Field(default=None, description="When this override was created")

# === COMPONENT AND TECH DEBT MODELS ===

class ApplicationComponent(BaseModel):
    """Flexible component identification beyond 3-tier architecture"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    component_name: str = Field(..., min_length=1, max_length=255, description="Name of the component")
    component_type: ComponentType = Field(..., description="Type of component")
    technology_stack: Optional[Dict[str, Any]] = Field(default=None, description="Technology details and versions")
    dependencies: Optional[List[str]] = Field(default=None, description="Other components this depends on")
    
    @field_validator('component_name')
    @classmethod
    def validate_component_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Component name cannot be empty')
        return v.strip()

class TechDebtItem(BaseModel):
    """Tech debt analysis item with severity and remediation tracking"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    category: str = Field(..., description="Category of tech debt (e.g., 'security', 'performance')")
    severity: TechDebtSeverity = Field(..., description="Severity level of the tech debt")
    description: str = Field(..., min_length=1, description="Description of the tech debt issue")
    remediation_effort_hours: Optional[int] = Field(default=None, ge=0, description="Estimated hours to remediate")
    impact_on_migration: Optional[str] = Field(default=None, description="How this impacts migration")
    tech_debt_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Quantified score for prioritization")
    detected_by_agent: Optional[str] = Field(default=None, description="Which agent detected this debt")
    agent_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Agent confidence in detection")
    component_id: Optional[UUID] = Field(default=None, description="Associated component UUID")

class ComponentTreatment(BaseModel):
    """Component-level 6R treatment with compatibility validation"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    component_name: str = Field(..., description="Name of the component")
    component_type: ComponentType = Field(..., description="Type of component")
    recommended_strategy: SixRStrategy = Field(..., description="Recommended 6R strategy")
    rationale: str = Field(..., description="Rationale for the strategy choice")
    compatibility_validated: bool = Field(default=False, description="Whether compatibility has been validated")
    compatibility_issues: Optional[List[str]] = Field(default=None, description="List of compatibility concerns")

# === 6R DECISION MODELS ===

class SixRDecision(BaseModel):
    """Application-level 6R decision with component rollup"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    application_id: UUID = Field(..., description="UUID of the application")
    application_name: str = Field(..., min_length=1, description="Name of the application")
    component_treatments: List[ComponentTreatment] = Field(default_factory=list, description="Component-level treatments")
    overall_strategy: SixRStrategy = Field(..., description="Overall application strategy")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the decision")
    rationale: str = Field(..., description="Rationale for the overall strategy")
    architecture_exceptions: List[str] = Field(default_factory=list, description="Architecture standard exceptions")
    tech_debt_score: Optional[float] = Field(default=None, ge=0.0, description="Overall tech debt score")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors identified")
    estimated_effort_hours: Optional[int] = Field(default=None, ge=0, description="Estimated migration effort")
    estimated_cost: Optional[Decimal] = Field(default=None, ge=0, description="Estimated migration cost")
    move_group_hints: List[str] = Field(default_factory=list, description="Migration grouping hints")
    user_modifications: Optional[Dict[str, Any]] = Field(default=None, description="User-made modifications")
    modified_by: Optional[str] = Field(default=None, description="Who made modifications")
    modified_at: Optional[datetime] = Field(default=None, description="When modifications were made")
    app_on_page_data: Optional[Dict[str, Any]] = Field(default=None, description="Complete app-on-page view")
    decision_factors: Optional[Dict[str, Any]] = Field(default=None, description="Factors that influenced decision")
    ready_for_planning: bool = Field(default=False, description="Ready for planning flow")
    
    @computed_field
    @property
    def has_high_risk_factors(self) -> bool:
        """Check if application has high-risk factors"""
        high_risk_keywords = ['legacy', 'deprecated', 'unsupported', 'critical', 'security']
        return any(keyword in ' '.join(self.risk_factors).lower() for keyword in high_risk_keywords)
    
    @computed_field
    @property
    def component_strategy_summary(self) -> Dict[str, int]:
        """Summary of component strategies"""
        summary = {}
        for treatment in self.component_treatments:
            strategy = treatment.recommended_strategy.value
            summary[strategy] = summary.get(strategy, 0) + 1
        return summary
    
    def calculate_overall_strategy(self) -> SixRStrategy:
        """Calculate app-level strategy from component treatments"""
        if not self.component_treatments:
            return SixRStrategy.RETAIN  # Default fallback
        
        strategies = [ct.recommended_strategy for ct in self.component_treatments]
        
        # Return highest modernization strategy
        strategy_order = [
            SixRStrategy.REWRITE,
            SixRStrategy.REARCHITECT, 
            SixRStrategy.REFACTOR,
            SixRStrategy.REPLATFORM,
            SixRStrategy.REHOST,
            SixRStrategy.REPURCHASE,
            SixRStrategy.RETIRE,
            SixRStrategy.RETAIN
        ]
        
        for strategy in strategy_order:
            if strategy in strategies:
                return strategy
                
        return SixRStrategy.RETAIN  # Default fallback
    
    def get_compatibility_issues(self) -> List[str]:
        """Get all compatibility issues across components"""
        issues = []
        for treatment in self.component_treatments:
            if treatment.compatibility_issues:
                issues.extend(treatment.compatibility_issues)
        return list(set(issues))  # Remove duplicates
    
    def validate_component_compatibility(self) -> List[str]:
        """Validate compatibility between component treatments"""
        issues = []
        treatments = {ct.component_name: ct.recommended_strategy 
                     for ct in self.component_treatments}
        
        # Check for incompatible combinations
        if (treatments.get("frontend") == SixRStrategy.REWRITE and 
            treatments.get("backend") == SixRStrategy.RETAIN):
            issues.append("Frontend rewrite with backend retain may cause integration issues")
        
        if (treatments.get("database") == SixRStrategy.RETIRE and 
            any(s in [SixRStrategy.RETAIN, SixRStrategy.REHOST] for s in treatments.values())):
            issues.append("Database retirement conflicts with retained components")
            
        return issues

class AssessmentLearningFeedback(BaseModel):
    """Learning feedback for agent improvement"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    original_strategy: SixRStrategy = Field(..., description="Agent's original recommendation")
    override_strategy: SixRStrategy = Field(..., description="User's override decision")
    feedback_reason: str = Field(..., description="User's rationale for change")
    agent_id: str = Field(..., description="Which agent made the original decision")
    learned_pattern: Optional[Dict[str, Any]] = Field(default=None, description="Pattern extracted for learning")

# === MAIN FLOW STATE MODEL ===

class AssessmentFlowState(BaseModel):
    """Complete assessment flow state with all components"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    # Flow identification
    flow_id: UUID = Field(..., description="Unique flow identifier")
    client_account_id: UUID = Field(..., description="Client account UUID")
    engagement_id: UUID = Field(..., description="Engagement UUID")
    selected_application_ids: List[UUID] = Field(..., description="Selected application UUIDs")
    
    # Architecture requirements
    engagement_architecture_standards: List[ArchitectureRequirement] = Field(
        default_factory=list, description="Engagement-level architecture standards"
    )
    application_architecture_overrides: Dict[str, List[ApplicationArchitectureOverride]] = Field(
        default_factory=dict, description="App-specific architecture overrides"
    )
    architecture_captured: bool = Field(default=False, description="Whether architecture has been captured")
    
    # Component identification  
    application_components: Dict[str, List[ApplicationComponent]] = Field(
        default_factory=dict, description="Components by application ID"
    )
    
    # Tech debt analysis
    tech_debt_analysis: Dict[str, List[TechDebtItem]] = Field(
        default_factory=dict, description="Tech debt items by application ID"
    )
    component_tech_debt: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Tech debt scores by app->component"
    )
    
    # 6R decisions
    sixr_decisions: Dict[str, SixRDecision] = Field(
        default_factory=dict, description="6R decisions by application ID"
    )
    
    # User interaction tracking
    pause_points: List[str] = Field(default_factory=list, description="Pause point identifiers")
    user_inputs: Dict[str, Any] = Field(default_factory=dict, description="Phase-specific user inputs")
    
    # Flow metadata
    status: AssessmentFlowStatus = Field(default=AssessmentFlowStatus.INITIALIZED, description="Flow status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    current_phase: AssessmentPhase = Field(default=AssessmentPhase.INITIALIZATION, description="Current phase")
    next_phase: Optional[AssessmentPhase] = Field(default=None, description="Next phase to execute")
    phase_results: Dict[str, Any] = Field(default_factory=dict, description="Phase completion results")
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Agent-generated insights")
    
    # Readiness tracking
    apps_ready_for_planning: List[UUID] = Field(default_factory=list, description="Apps ready for planning")
    
    # Timestamps
    created_at: datetime = Field(..., description="When flow was created")
    updated_at: datetime = Field(..., description="When flow was last updated")
    last_user_interaction: Optional[datetime] = Field(default=None, description="Last user interaction time")
    completed_at: Optional[datetime] = Field(default=None, description="When flow was completed")
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Progress must be between 0 and 100')
        return v
    
    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if flow is complete"""
        return self.status == AssessmentFlowStatus.COMPLETED
    
    @computed_field
    @property
    def apps_needing_review(self) -> List[UUID]:
        """Get applications that need user review"""
        return [
            UUID(app_id) for app_id, decision in self.sixr_decisions.items()
            if decision.confidence_score < 0.8
        ]
    
    @computed_field
    @property
    def high_risk_applications(self) -> List[UUID]:
        """Get applications with high risk factors"""
        return [
            UUID(app_id) for app_id, decision in self.sixr_decisions.items()
            if decision.has_high_risk_factors
        ]
    
    @computed_field
    @property
    def critical_tech_debt_count(self) -> int:
        """Count critical tech debt items across all applications"""
        count = 0
        for app_debt in self.tech_debt_analysis.values():
            count += sum(1 for item in app_debt if item.severity == TechDebtSeverity.CRITICAL)
        return count
    
    def get_applications_by_strategy(self, strategy: SixRStrategy) -> List[UUID]:
        """Get applications using a specific strategy"""
        return [
            UUID(app_id) for app_id, decision in self.sixr_decisions.items()
            if decision.overall_strategy == strategy
        ]
    
    def get_phase_progress(self) -> Dict[str, bool]:
        """Get completion status of all phases"""
        phases = list(AssessmentPhase)
        current_index = phases.index(self.current_phase) if self.current_phase in phases else 0
        
        return {
            phase.value: i <= current_index 
            for i, phase in enumerate(phases)
        }
    
    def calculate_overall_readiness_score(self) -> float:
        """Calculate overall migration readiness score"""
        if not self.sixr_decisions:
            return 0.0
        
        total_score = 0.0
        app_count = len(self.sixr_decisions)
        
        for decision in self.sixr_decisions.values():
            # Base score from confidence
            score = decision.confidence_score * 100
            
            # Reduce score for high tech debt
            if decision.tech_debt_score and decision.tech_debt_score > 70:
                score -= 20
            
            # Reduce score for high risk factors
            if decision.has_high_risk_factors:
                score -= 15
            
            # Reduce score for compatibility issues
            if decision.get_compatibility_issues():
                score -= 10
            
            total_score += max(0, score)  # Ensure non-negative
        
        return round(total_score / app_count, 1)
    
    def get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of strategies across applications"""
        distribution = {}
        for decision in self.sixr_decisions.values():
            strategy = decision.overall_strategy.value
            distribution[strategy] = distribution.get(strategy, 0) + 1
        return distribution
    
    def get_migration_complexity_summary(self) -> Dict[str, Any]:
        """Get summary of migration complexity factors"""
        return {
            "total_applications": len(self.selected_application_ids),
            "decisions_completed": len(self.sixr_decisions),
            "apps_ready_for_planning": len(self.apps_ready_for_planning),
            "high_risk_apps": len(self.high_risk_applications),
            "critical_tech_debt": self.critical_tech_debt_count,
            "overall_readiness": self.calculate_overall_readiness_score(),
            "strategy_distribution": self.get_strategy_distribution()
        }

# === RESPONSE MODELS FOR APIS ===

class AssessmentFlowSummary(BaseModel):
    """Simplified assessment flow summary for list views"""
    model_config = ConfigDict(use_enum_values=True)
    
    flow_id: UUID
    client_account_id: UUID
    engagement_id: UUID
    status: AssessmentFlowStatus
    progress: int
    current_phase: AssessmentPhase
    total_applications: int
    decisions_completed: int
    overall_readiness: float
    created_at: datetime
    updated_at: datetime

class AssessmentPhaseResult(BaseModel):
    """Result of completing an assessment phase"""
    model_config = ConfigDict(use_enum_values=True)
    
    phase: AssessmentPhase
    completed: bool
    result_data: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]
    next_phase: Optional[AssessmentPhase] = None
    pause_required: bool = False
    user_input_needed: bool = False

class AssessmentValidationResult(BaseModel):
    """Result of validating assessment data"""
    model_config = ConfigDict(use_enum_values=True)
    
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)