"""
Manual Collection Framework Services

This package provides services for manual data collection including adaptive form generation,
bulk data processing, questionnaire validation, template management, progress tracking,
and data integration services.

Agent Team B3 Implementation.
"""

from .adaptive_form_service import AdaptiveFormService
from .bulk_data_service import BulkDataService
from .validation_service import QuestionnaireValidationService
from .template_service import TemplateService
from .progress_tracking_service import ProgressTrackingService
from .data_integration_service import DataIntegrationService

__all__ = [
    'AdaptiveFormService',
    'BulkDataService', 
    'QuestionnaireValidationService',
    'TemplateService',
    'ProgressTrackingService',
    'DataIntegrationService',
]