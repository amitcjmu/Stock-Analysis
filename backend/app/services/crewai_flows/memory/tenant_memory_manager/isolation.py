"""
Memory isolation and privacy control methods
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List

from app.services.crewai_flows.memory.tenant_memory_manager.enums import (
    LearningScope,
    MemoryIsolationLevel,
)
from app.services.crewai_flows.memory.tenant_memory_manager.models import (
    LearningDataClassification,
)


class MemoryIsolationMixin:
    """Mixin for memory isolation and privacy control methods"""

    def create_isolated_memory(
        self,
        client_account_id: str,
        engagement_id: str,
        learning_scope: LearningScope,
        isolation_level: MemoryIsolationLevel = MemoryIsolationLevel.STRICT,
        cross_client_learning_enabled: bool = False,
    ) -> Dict[str, Any]:
        """
        Create memory instance with appropriate isolation controls

        Args:
            client_account_id: Client account identifier
            engagement_id: Engagement identifier
            learning_scope: Scope of learning persistence
            isolation_level: Level of memory isolation
            cross_client_learning_enabled: Whether to enable cross-client learning

        Returns:
            Memory configuration with isolation controls
        """

        memory_id = self._generate_memory_id(
            client_account_id, engagement_id, learning_scope
        )

        # Determine memory scope and access controls
        memory_config = {
            "memory_id": memory_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "learning_scope": learning_scope.value,
            "isolation_level": isolation_level.value,
            "cross_client_learning_enabled": cross_client_learning_enabled,
            "created_at": datetime.utcnow().isoformat(),
            "access_controls": self._create_access_controls(
                client_account_id, engagement_id, learning_scope, isolation_level
            ),
            "encryption_config": self._create_encryption_config(isolation_level),
            "audit_config": self._create_audit_config(client_account_id, engagement_id),
        }

        # Create actual memory instance based on scope
        if learning_scope == LearningScope.DISABLED:
            memory_instance = self._create_disabled_memory()
        elif learning_scope == LearningScope.ENGAGEMENT:
            memory_instance = self._create_engagement_scoped_memory(memory_config)
        elif learning_scope == LearningScope.CLIENT:
            memory_instance = self._create_client_scoped_memory(memory_config)
        elif learning_scope == LearningScope.GLOBAL:
            memory_instance = self._create_global_memory(memory_config)
        else:
            raise ValueError(f"Unsupported learning scope: {learning_scope}")

        # Log memory creation for audit
        self._audit_memory_operation(
            "memory_created",
            memory_config,
            {"memory_type": learning_scope.value, "isolation": isolation_level.value},
        )

        return {
            "memory_instance": memory_instance,
            "memory_config": memory_config,
            "privacy_controls": self._get_privacy_controls(memory_config),
        }

    def _create_engagement_scoped_memory(self, config: Dict[str, Any]):
        """Create memory instance scoped to single engagement"""
        try:
            from crewai.memory import LongTermMemory

            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
                storage_config={
                    "namespace": f"engagement_{config['engagement_id']}",
                    "isolation": "strict",
                    "encryption": True,
                },
            )
        except ImportError:
            self.logger.warning("CrewAI advanced memory not available, using fallback")
            return self._create_fallback_memory(config)

    def _create_client_scoped_memory(self, config: Dict[str, Any]):
        """Create memory instance scoped to client account"""
        try:
            from crewai.memory import LongTermMemory

            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
                storage_config={
                    "namespace": f"client_{config['client_account_id']}",
                    "isolation": "moderate",
                    "encryption": True,
                },
            )
        except ImportError:
            return self._create_fallback_memory(config)

    def _create_global_memory(self, config: Dict[str, Any]):
        """Create global memory instance with consent controls"""
        try:
            from crewai.memory import LongTermMemory

            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
                storage_config={
                    "namespace": "global_shared",
                    "isolation": "open",
                    "consent_required": True,
                },
            )
        except ImportError:
            return self._create_fallback_memory(config)

    def _create_disabled_memory(self):
        """Create disabled memory that doesn't persist learning"""
        return None  # No memory instance for disabled learning

    def _create_fallback_memory(self, config: Dict[str, Any]):
        """Create fallback memory when CrewAI advanced features unavailable"""
        return {
            "type": "fallback",
            "config": config,
            "storage": {},
            "isolation_enforced": True,
        }

    def _is_cross_tenant_sharing_allowed(
        self, memory_config: Dict[str, Any], classification: LearningDataClassification
    ) -> bool:
        """Check if cross-tenant sharing is allowed for this data"""
        return (
            classification.cross_tenant_sharing_allowed
            and memory_config.get("cross_client_learning_enabled", False)
            and memory_config["learning_scope"] == "global"
        )

    def _sanitize_for_tenant_isolation(
        self, learning_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Remove tenant-specific information from learning data"""
        # Remove or hash client-specific identifiers
        sanitized = learning_data.copy()

        # Remove direct client identifiers
        sanitized.pop("client_account_id", None)
        sanitized.pop("engagement_id", None)
        sanitized.pop("client_name", None)

        # Hash or generalize asset names
        if "asset_names" in sanitized:
            sanitized["asset_names"] = [
                hashlib.sha256(name.encode()).hexdigest()[:8]
                for name in sanitized["asset_names"]
            ]

        return sanitized

    def _validate_access_permissions(
        self,
        memory_config: Dict[str, Any],
        requesting_client: str,
        requesting_engagement: str,
    ) -> bool:
        """Validate if requesting client/engagement has access to memory"""
        access_controls = memory_config["access_controls"]

        # Check client-level access
        allowed_clients = access_controls.get("allowed_clients", [])
        if allowed_clients and requesting_client not in allowed_clients:
            return False

        # Check engagement-level access if specified
        allowed_engagements = access_controls.get("allowed_engagements", [])
        if allowed_engagements and requesting_engagement not in allowed_engagements:
            return False

        return True

    def _apply_privacy_filters(
        self,
        data: List[Dict[str, Any]],
        memory_config: Dict[str, Any],
        requesting_client: str,
    ) -> List[Dict[str, Any]]:
        """Apply privacy filters to retrieved data"""
        if not data:
            return []

        # Filter based on isolation level and client access
        if memory_config["isolation_level"] == "strict":
            # Only return data from same client
            return [
                item
                for item in data
                if item.get("client_account_id") == requesting_client
            ]

        return data

    def _encrypt_learning_data(
        self, data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Encrypt learning data"""
        # Placeholder for encryption implementation
        return {"encrypted": True, "data": data}

    def _decrypt_learning_data(
        self, data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Decrypt learning data"""
        # Placeholder for decryption implementation
        if data.get("encrypted"):
            return data.get("data", {})
        return data
