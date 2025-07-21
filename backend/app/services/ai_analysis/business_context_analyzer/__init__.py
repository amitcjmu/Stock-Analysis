"""
Business Context Analysis Module - B2.4
ADCS AI Analysis & Intelligence Service

Modularized business context analysis for questionnaire targeting.

This module provides comprehensive business intelligence to optimize questionnaire design
and targeting, ensuring the right questions are asked to the right stakeholders at the
right time.

Modular Components:
- enums: Business domain, organization size, stakeholder roles, and migration driver enums
- models: Data models for BusinessContext and QuestionnaireTarget
- domain_configurations: Domain-specific configurations and stakeholder expertise
- analyzers: Core business analysis methods
- optimization: Questionnaire targeting and optimization logic
- utilities: Helper functions and default creation methods

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

# Export all enums
from .enums import (
    BusinessDomain,
    OrganizationSize,
    StakeholderRole,
    MigrationDriverType
)

# Export all models
from .models import (
    BusinessContext,
    QuestionnaireTarget
)

# Export configuration manager
from .domain_configurations import DomainConfigurationManager

# Export analyzers
from .analyzers import BusinessAnalyzers

# Export optimization components
from .optimization import QuestionnaireOptimizer

# Export utilities
from .utilities import BusinessContextUtilities

__all__ = [
    # Enums
    'BusinessDomain',
    'OrganizationSize', 
    'StakeholderRole',
    'MigrationDriverType',
    
    # Models
    'BusinessContext',
    'QuestionnaireTarget',
    
    # Components
    'DomainConfigurationManager',
    'BusinessAnalyzers',
    'QuestionnaireOptimizer',
    'BusinessContextUtilities'
]