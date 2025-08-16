"""
Base mixin for CrewAI Flow State Extensions repository.
Provides initialization, feature flags, and JSON serialization utilities.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class BaseRepo(ContextAwareRepository):
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str | None = None,
        user_id: Optional[str] = None,
    ) -> None:
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        try:
            parsed_client = (
                (
                    client_account_id
                    if isinstance(client_account_id, uuid.UUID)
                    else uuid.UUID(str(client_account_id))
                )
                if client_account_id and client_account_id != "None"
                else demo_client_id
            )
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid client_account_id '{client_account_id}', using demo fallback"
            )
            parsed_client = demo_client_id

        try:
            parsed_engagement = (
                (
                    engagement_id
                    if isinstance(engagement_id, uuid.UUID)
                    else uuid.UUID(str(engagement_id))
                )
                if engagement_id and engagement_id != "None"
                else demo_engagement_id
            )
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid engagement_id '{engagement_id}', using demo fallback"
            )
            parsed_engagement = demo_engagement_id

        super().__init__(
            db=db,
            model_class=CrewAIFlowStateExtensions,
            client_account_id=str(parsed_client),
            engagement_id=str(parsed_engagement),
        )

        self.client_account_id = str(parsed_client)
        self.engagement_id = str(parsed_engagement)
        self.user_id = user_id

        flag = os.getenv("MASTER_STATE_ENRICHMENT_ENABLED", "false")
        self._enrichment_enabled = flag.strip().lower() in ("1", "true", "yes")

    def _ensure_json_serializable(
        self, obj: Any, _visited: Optional[set] = None, _depth: int = 0
    ) -> Any:
        if _visited is None:
            _visited = set()
        MAX_DEPTH = 50
        if _depth > MAX_DEPTH:
            logger.warning(
                f"Maximum serialization depth {MAX_DEPTH} reached, converting to string"
            )
            return str(obj)
        try:
            if isinstance(obj, dict):
                obj_id = id(obj)
                if obj_id in _visited:
                    return "<circular reference: dict>"
                _visited.add(obj_id)
                result: Dict[str, Any] = {}
                for k, v in obj.items():
                    result[k] = self._ensure_json_serializable(v, _visited, _depth + 1)
                _visited.discard(obj_id)
                return result
            if isinstance(obj, list):
                obj_id = id(obj)
                if obj_id in _visited:
                    return "<circular reference: list>"
                _visited.add(obj_id)
                result = [
                    self._ensure_json_serializable(item, _visited, _depth + 1)
                    for item in obj
                ]
                _visited.discard(obj_id)
                return result
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            if hasattr(obj, "__dict__"):
                obj_id = id(obj)
                if obj_id in _visited:
                    return f"<circular reference: {type(obj).__name__}>"
                _visited.add(obj_id)
                data = self._ensure_json_serializable(
                    obj.__dict__, _visited, _depth + 1
                )
                _visited.discard(obj_id)
                return data
            logger.warning(
                f"Converting unknown type {type(obj).__name__} to string: {obj}"
            )
            return str(obj)
        except Exception as e:
            logger.error(
                f"Error in _ensure_json_serializable for object {type(obj).__name__}: {e}"
            )
            return str(obj)
