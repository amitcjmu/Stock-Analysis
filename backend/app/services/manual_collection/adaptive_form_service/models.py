"""
Adaptive Form Service Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from .enums import FieldType, ValidationRule


@dataclass
class ConditionalDisplayRule:
    """Rules for conditional field display based on other field values"""

    dependent_field: str
    condition: str  # 'equals', 'contains', 'not_equals', 'in', 'not_in'
    values: List[str]
    required_when_visible: bool = False


@dataclass
class FieldValidation:
    """Validation configuration for a form field"""

    rules: List[ValidationRule]
    parameters: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class FormField:
    """Configuration for a dynamic form field"""

    id: str
    label: str
    field_type: FieldType
    critical_attribute: str  # Maps to one of the 22 critical attributes
    description: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None  # For select/radio fields
    validation: Optional[FieldValidation] = None
    conditional_display: Optional[ConditionalDisplayRule] = None
    section: str = "general"
    order: int = 0
    help_text: Optional[str] = None
    business_impact_score: float = 0.0  # Impact on 6R decision confidence


@dataclass
class FormSection:
    """Logical grouping of related form fields"""

    id: str
    title: str
    description: Optional[str] = None
    fields: List[FormField] = None
    order: int = 0
    required_fields_count: int = 0
    completion_weight: float = 0.0  # Weight in overall form completion

    def __post_init__(self):
        if self.fields is None:
            self.fields = []


@dataclass
class AdaptiveForm:
    """Complete adaptive form configuration"""

    id: str
    title: str
    application_id: UUID
    gap_analysis_id: UUID
    sections: List[FormSection]
    total_fields: int
    required_fields: int
    estimated_completion_time: int  # minutes
    confidence_impact_score: float  # Expected confidence improvement
    created_at: datetime
    updated_at: datetime


@dataclass
class GapAnalysisResult:
    """Gap analysis result structure"""

    critical_gaps: List[Dict[str, Any]]
    completeness_score: float
    missing_attributes: List[str]
    business_context: Dict[str, Any]
    application_metadata: Dict[str, Any]


@dataclass
class ApplicationContext:
    """Application context for form adaptation"""

    application_id: UUID
    technology_stack: List[str]
    architecture_pattern: str
    detected_patterns: List[str]
    business_criticality: str
    compliance_requirements: List[str]
    related_applications: List[UUID]
