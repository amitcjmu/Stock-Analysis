"""
Service Initializer for Collection Flow

This module handles the initialization of all required services for the collection flow.
"""

import logging

from app.core.context import RequestContext
from app.services.ai_analysis import (
    AdaptiveQuestionnaireGenerator,
    AIValidationService,
    BusinessAnalyzers,
    ConfidenceScorer,
    GapAnalysisAgent,
)
from app.services.collection_flow import (
    AuditLoggingService,
    CollectionFlowStateService,
    DataTransformationService,
    QualityAssessmentService,
    TierDetectionService,
)
from app.services.manual_collection import (
    AdaptiveFormService,
    BulkDataService,
    DataIntegrationService,
    ProgressTrackingService,
    TemplateService,
)
from app.services.manual_collection import (
    QuestionnaireValidationService as ValidationService,
)

logger = logging.getLogger(__name__)


class ServiceInitializer:
    """Initializes all required services for collection flow"""

    def __init__(self, db_session, context: RequestContext):
        self.db_session = db_session
        self.context = context
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all required services"""
        # Initialize Phase 1 & 2 services
        self.state_service = CollectionFlowStateService(self.db_session, self.context)
        self.tier_detection = TierDetectionService(self.db_session, self.context)
        self.data_transformation = DataTransformationService(
            self.db_session, self.context
        )
        self.quality_assessment = QualityAssessmentService(
            self.db_session, self.context
        )
        self.audit_logging = AuditLoggingService(self.db_session, self.context)

        # Initialize AI analysis services
        self.ai_validation = AIValidationService()
        self.business_analyzer = BusinessAnalyzers()
        self.confidence_scoring = ConfidenceScorer()
        # Pass required context parameters to GapAnalysisAgent
        self.gap_analysis_agent = GapAnalysisAgent(
            client_account_id=self.context.client_account_id or "",
            engagement_id=self.context.engagement_id or "",
        )
        self.questionnaire_generator = AdaptiveQuestionnaireGenerator()

        # Initialize manual collection services
        self.adaptive_form_service = AdaptiveFormService()
        self.bulk_data_service = BulkDataService(self.db_session, self.context)
        self.validation_service = ValidationService()
        self.template_service = TemplateService()
        self.progress_tracking = ProgressTrackingService()
        self.data_integration = DataIntegrationService(self.db_session, self.context)
