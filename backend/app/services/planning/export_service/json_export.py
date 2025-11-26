"""
JSON Export Module - JSON format export generation

Generates JSON exports of planning flow data for programmatic access.

Architecture:
- Layer 2 (Service Layer): Format-specific export generation
- Returns structured JSON with metadata
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from .base import BaseExportService

logger = logging.getLogger(__name__)


class JSONExportService(BaseExportService):
    """
    Service for exporting planning data as JSON.

    Generates structured JSON with export metadata.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize JSON export service.

        Args:
            db: Async SQLAlchemy database session
            context: Request context with tenant scoping
        """
        super().__init__(db, context)

    def export_json(
        self, planning_data: Dict[str, Any], planning_flow_id: UUID
    ) -> Tuple[bytes, str, str]:
        """
        Export planning data as JSON.

        Args:
            planning_data: Complete planning data dictionary
            planning_flow_id: Planning flow UUID for filename

        Returns:
            Tuple of (json_bytes, content_type, filename)
        """
        try:
            # Add export metadata
            export_data = {
                "export_metadata": {
                    "format": "json",
                    "version": "1.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "exported_by": str(self.context.client_account_id),
                },
                "planning_data": planning_data,
            }

            # Serialize to JSON with proper formatting
            json_content = json.dumps(export_data, indent=2, default=str)
            content_bytes = json_content.encode("utf-8")

            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"planning_export_{planning_flow_id}_{timestamp}.json"

            logger.info(f"✅ JSON export generated: {len(content_bytes)} bytes")

            return (content_bytes, "application/json", filename)

        except Exception as e:
            logger.error(f"❌ JSON export failed: {e}", exc_info=True)
            raise
