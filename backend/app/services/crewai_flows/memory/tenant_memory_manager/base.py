"""
Base TenantMemoryManager class with initialization and core setup
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict

from app.services.crewai_flows.memory.tenant_memory_manager.enums import (
    LearningScope,
    MemoryIsolationLevel,
)
from app.services.crewai_flows.memory.tenant_memory_manager.models import (
    LearningDataClassification,
)

logger = logging.getLogger(__name__)


class TenantMemoryManager:
    """
    Enterprise-grade memory management with multi-tenant isolation
    Supports engagement-scoped, client-scoped, and global learning with privacy controls
    """

    def __init__(self, crewai_service, database_session):
        self.crewai_service = crewai_service
        self.db = database_session
        self.logger = logger

        # Learning data classification schema
        self.data_classifications = {
            "field_mapping_patterns": LearningDataClassification(
                sensitivity_level="internal",
                data_categories=["field_patterns", "schema_analysis"],
                retention_period=365,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False,  # Default: no cross-tenant sharing
            ),
            "asset_classification_insights": LearningDataClassification(
                sensitivity_level="confidential",
                data_categories=["asset_classification", "inventory_patterns"],
                retention_period=180,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False,
            ),
            "dependency_relationship_patterns": LearningDataClassification(
                sensitivity_level="confidential",
                data_categories=["dependencies", "topology_patterns"],
                retention_period=180,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False,
            ),
            "technical_debt_insights": LearningDataClassification(
                sensitivity_level="restricted",
                data_categories=["modernization", "risk_assessment"],
                retention_period=90,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False,
            ),
        }

    # Core helper methods

    def _generate_memory_id(
        self, client_account_id: str, engagement_id: str, scope: LearningScope
    ) -> str:
        """Generate unique memory ID based on scope"""
        base_string = f"{client_account_id}:{engagement_id}:{scope.value}:{datetime.utcnow().date()}"
        return hashlib.sha256(base_string.encode()).hexdigest()[:16]

    def _create_access_controls(
        self,
        client_id: str,
        engagement_id: str,
        scope: LearningScope,
        isolation: MemoryIsolationLevel,
    ) -> Dict[str, Any]:
        """Create access control configuration"""
        if scope == LearningScope.ENGAGEMENT:
            return {
                "allowed_clients": [client_id],
                "allowed_engagements": [engagement_id],
            }
        elif scope == LearningScope.CLIENT:
            return {"allowed_clients": [client_id], "allowed_engagements": []}
        elif scope == LearningScope.GLOBAL:
            return {
                "allowed_clients": [],
                "allowed_engagements": [],
            }  # Open with consent
        else:
            return {"allowed_clients": [], "allowed_engagements": []}  # Disabled

    def _create_encryption_config(
        self, isolation: MemoryIsolationLevel
    ) -> Dict[str, Any]:
        """Create encryption configuration based on isolation level"""
        return {
            "encryption_enabled": isolation != MemoryIsolationLevel.OPEN,
            "key_rotation_days": 30 if isolation == MemoryIsolationLevel.STRICT else 90,
            "algorithm": "AES-256-GCM",
        }

    def _create_audit_config(
        self, client_id: str, engagement_id: str
    ) -> Dict[str, Any]:
        """Create audit configuration"""
        return {
            "audit_enabled": True,
            "audit_level": "detailed",
            "retention_days": 1095,  # 3 years
            "client_id": client_id,
            "engagement_id": engagement_id,
        }

    def _audit_memory_operation(
        self, operation: str, memory_config: Dict[str, Any], details: Dict[str, Any]
    ):
        """Record audit trail for memory operations"""
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "memory_id": memory_config["memory_id"],
            "client_account_id": memory_config["client_account_id"],
            "engagement_id": memory_config["engagement_id"],
            "learning_scope": memory_config["learning_scope"],
            "details": details,
        }

        # Store audit record (implementation depends on audit storage system)
        self._store_audit_record(audit_record)
        self.logger.info(f"Memory operation audited: {operation}", extra=audit_record)

    def _store_audit_record(self, audit_record: Dict[str, Any]):
        """Store audit record in audit system"""
        # Implementation depends on audit storage system
        # Could be database, file system, or external audit service
        pass

    def _get_privacy_controls(self, memory_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get privacy control summary for memory configuration"""
        return {
            "learning_scope": memory_config["learning_scope"],
            "isolation_level": memory_config["isolation_level"],
            "cross_client_learning": memory_config["cross_client_learning_enabled"],
            "encryption_enabled": memory_config["encryption_config"][
                "encryption_enabled"
            ],
            "audit_enabled": memory_config["audit_config"]["audit_enabled"],
            "data_retention_policies": {
                category: classification.retention_period
                for category, classification in self.data_classifications.items()
            },
        }
