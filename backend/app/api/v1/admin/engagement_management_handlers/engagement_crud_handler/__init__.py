"""
Engagement CRUD Handler - Core engagement operations
Backward compatibility module preserving public API
"""

from .commands import EngagementCommands
from .queries import EngagementQueries


class EngagementCRUDHandler:
    """Handler for engagement CRUD operations - preserves backward compatibility"""

    # Query operations (read)
    list_engagements = EngagementQueries.list_engagements
    get_engagement = EngagementQueries.get_engagement
    get_dashboard_stats = EngagementQueries.get_dashboard_stats
    _convert_engagement_to_response = EngagementQueries._convert_engagement_to_response

    # Command operations (write)
    create_engagement = EngagementCommands.create_engagement
    update_engagement = EngagementCommands.update_engagement
    delete_engagement = EngagementCommands.delete_engagement


# Export for backward compatibility
__all__ = [
    "EngagementCRUDHandler",
    "EngagementQueries",
    "EngagementCommands",
]
