"""
Template Models

Models and enums for template service.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class TemplateType(str, Enum):
    """Types of application templates"""

    WEB_APPLICATION = "web_application"
    DATABASE = "database"
    API_SERVICE = "api_service"
    BATCH_JOB = "batch_job"
    MICROSERVICE = "microservice"
    LEGACY_SYSTEM = "legacy_system"
    CLOUD_NATIVE = "cloud_native"


class TemplateStatus(str, Enum):
    """Template lifecycle status"""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class SimilarityMethod(str, Enum):
    """Methods for calculating application similarity"""

    TECHNOLOGY_STACK = "technology_stack"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    BUSINESS_DOMAIN = "business_domain"
    DEPLOYMENT_MODEL = "deployment_model"


@dataclass
class ApplicationProfile:
    """Profile of an application for template matching"""

    application_id: UUID
    name: str
    technology_stack: List[str]
    architecture_patterns: List[str]
    business_domain: str
    deployment_model: str
    complexity_score: float
    data_sensitivity: str
    compliance_requirements: List[str]
    performance_requirements: Dict[str, Any]
    integration_patterns: List[str]


@dataclass
class TemplateField:
    """Individual field in a template"""

    field_id: str
    field_type: str
    label: str
    description: str
    required: bool
    validation_rules: Dict[str, Any]
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    default_value: Optional[Any] = None


@dataclass
class ApplicationTemplate:
    """Template for application data collection"""

    template_id: str
    name: str
    description: str
    template_type: TemplateType
    target_applications: List[str]
    fields: List[TemplateField]
    form_sections: List[Dict[str, Any]]
    validation_rules: Dict[str, Any]
    default_values: Dict[str, Any]
    effectiveness_score: float
    usage_count: int
    created_at: datetime
    updated_at: datetime
    status: TemplateStatus
    metadata: Dict[str, Any]


@dataclass
class SimilarityResult:
    """Result of application similarity analysis"""

    application_id: UUID
    similarity_score: float
    matching_factors: List[str]
    confidence_level: float


@dataclass
class TemplateApplication:
    """Result of applying a template to an application"""

    application_id: UUID
    template_id: str
    applied_at: datetime
    completion_rate: float
    effectiveness_score: float
    user_feedback: Optional[Dict[str, Any]] = None
