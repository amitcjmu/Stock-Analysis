"""
Manual Collection Framework Services

This package provides services for manual data collection including adaptive form generation,
bulk data processing, questionnaire validation, template management, progress tracking,
and data integration services.

Agent Team B3 Implementation.
"""

from .adaptive_form_service import AdaptiveFormService
from .bulk_data_service import BulkDataService
from .data_integration_service import DataIntegrationService
from .progress_tracking_service import ProgressTrackingService
from .template_service import TemplateService
from .validation_service import QuestionnaireValidationService

__all__ = [
    "AdaptiveFormService",
    "BulkDataService",
    "QuestionnaireValidationService",
    "TemplateService",
    "ProgressTrackingService",
    "DataIntegrationService",
]
