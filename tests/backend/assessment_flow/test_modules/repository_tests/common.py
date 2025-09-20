"""
Common imports and setup for assessment repository tests.

Shared imports, mock classes, and configuration for repository test modules.
"""

from datetime import datetime, timezone

import pytest

# Import MFO fixtures and markers
from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    MockRequestContext,
)

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
    from app.repositories.assessment_flow_repository import AssessmentFlowRepository

    REPOSITORY_AVAILABLE = True
except ImportError:
    # Mock classes for when components don't exist yet
    REPOSITORY_AVAILABLE = False

    class AssessmentFlowRepository:
        def __init__(self, db_session, client_account_id):
            self.db_session = db_session
            self.client_account_id = client_account_id

    class AssessmentFlowState:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class AssessmentPhase:
        ARCHITECTURE_MINIMUMS = "architecture_minimums"
        TECH_DEBT_ANALYSIS = "tech_debt_analysis"

    AsyncSession = object
