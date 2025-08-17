"""Master enrichment class composed from focused mixins."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.crewai_flow_state_extensions.base import BaseRepo
from app.repositories.crewai_flow_state_extensions.enrichment.metadata import (
    MetadataEnrichmentMixin,
)
from app.repositories.crewai_flow_state_extensions.enrichment.transitions import (
    TransitionsEnrichmentMixin,
)
from app.repositories.crewai_flow_state_extensions.enrichment.metrics import (
    MetricsEnrichmentMixin,
)
from app.repositories.crewai_flow_state_extensions.enrichment.errors import (
    ErrorsEnrichmentMixin,
)
from app.repositories.crewai_flow_state_extensions.enrichment.collaboration import (
    CollaborationEnrichmentMixin,
)


class MasterFlowEnrichment(
    BaseRepo,
    MetadataEnrichmentMixin,
    TransitionsEnrichmentMixin,
    MetricsEnrichmentMixin,
    ErrorsEnrichmentMixin,
    CollaborationEnrichmentMixin,
):
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
    ):
        super().__init__(db, client_account_id, engagement_id, user_id)
