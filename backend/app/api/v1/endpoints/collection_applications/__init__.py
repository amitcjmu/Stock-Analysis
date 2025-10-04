"""Collection Application Selection endpoints.

This module handles application selection for collection flows,
enabling targeted questionnaire generation based on selected applications.
"""

from app.api.v1.endpoints.collection_applications.handlers import (
    update_flow_applications,
)

__all__ = ["update_flow_applications"]
