"""
Base Collection Tool

Common functionality for all collection orchestration tools.
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseCollectionTool:
    """Base class for collection orchestration tools"""

    def __init__(self):
        self.tool_id = None
        self.name = None
        self.description = None

    def _create_base_result(self, action: str) -> Dict[str, Any]:
        """Create base result structure"""
        return {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "tool": self.name or self.__class__.__name__,
            "success": False,
            "errors": [],
        }

    def _add_error(self, result: Dict[str, Any], error_msg: str):
        """Add error to result"""
        result["errors"].append(error_msg)
        result["success"] = False
        logger.error(f"{self.name}: {error_msg}")

    def _mark_success(self, result: Dict[str, Any]):
        """Mark result as successful"""
        result["success"] = len(result["errors"]) == 0
