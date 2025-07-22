"""
Multi-Tenant Memory Management Service
Handles learning persistence with enterprise privacy controls and data isolation
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class LearningScope(Enum):
    """Learning scope levels for multi-tenant isolation"""
    DISABLED = "disabled"          # No learning persistence
    ENGAGEMENT = "engagement"      # Learning isolated to single engagement
    CLIENT = "client"             # Learning shared across client's engagements
    GLOBAL = "global"             # Learning shared across all clients (with consent)

class MemoryIsolationLevel(Enum):
    """Memory isolation levels for enterprise security"""
    STRICT = "strict"             # Complete isolation, no cross-tenant access
    MODERATE = "moderate"         # Limited sharing with explicit consent
    OPEN = "open"                # Open sharing with audit trail

@dataclass
class LearningDataClassification:
    """Classification of learning data for privacy compliance"""
    sensitivity_level: str  # "public", "internal", "confidential", "restricted"
    data_categories: List[str]  # ["field_patterns", "asset_classification", "dependencies"]
    retention_period: int  # Days
    encryption_required: bool
    audit_required: bool
    cross_tenant_sharing_allowed: bool

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
                cross_tenant_sharing_allowed=False  # Default: no cross-tenant sharing
            ),
            "asset_classification_insights": LearningDataClassification(
                sensitivity_level="confidential",
                data_categories=["asset_classification", "inventory_patterns"],
                retention_period=180,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False
            ),
            "dependency_relationship_patterns": LearningDataClassification(
                sensitivity_level="confidential",
                data_categories=["dependencies", "topology_patterns"],
                retention_period=180,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False
            ),
            "technical_debt_insights": LearningDataClassification(
                sensitivity_level="restricted",
                data_categories=["modernization", "risk_assessment"],
                retention_period=90,
                encryption_required=True,
                audit_required=True,
                cross_tenant_sharing_allowed=False
            )
        }
    
    def create_isolated_memory(self, 
                             client_account_id: str,
                             engagement_id: str,
                             learning_scope: LearningScope,
                             isolation_level: MemoryIsolationLevel = MemoryIsolationLevel.STRICT,
                             cross_client_learning_enabled: bool = False) -> Dict[str, Any]:
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
        
        memory_id = self._generate_memory_id(client_account_id, engagement_id, learning_scope)
        
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
            "audit_config": self._create_audit_config(client_account_id, engagement_id)
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
            {"memory_type": learning_scope.value, "isolation": isolation_level.value}
        )
        
        return {
            "memory_instance": memory_instance,
            "memory_config": memory_config,
            "privacy_controls": self._get_privacy_controls(memory_config)
        }
    
    def store_learning_data(self,
                          memory_config: Dict[str, Any],
                          data_category: str,
                          learning_data: Dict[str, Any],
                          confidence_score: float = 0.0) -> Dict[str, Any]:
        """
        Store learning data with privacy compliance and audit trail
        
        Args:
            memory_config: Memory configuration with isolation controls
            data_category: Category of learning data (field_patterns, asset_classification, etc.)
            learning_data: Actual learning data to store
            confidence_score: Confidence score for the learning data
        
        Returns:
            Storage result with privacy compliance status
        """
        
        # Validate privacy compliance
        classification = self.data_classifications.get(data_category)
        if not classification:
            raise ValueError(f"Unknown data category: {data_category}")
        
        # Check if cross-tenant sharing is allowed
        if not self._is_cross_tenant_sharing_allowed(memory_config, classification):
            learning_data = self._sanitize_for_tenant_isolation(learning_data)
        
        # Encrypt if required
        if classification.encryption_required:
            learning_data = self._encrypt_learning_data(learning_data, memory_config)
        
        # Create storage record
        storage_record = {
            "memory_id": memory_config["memory_id"],
            "client_account_id": memory_config["client_account_id"],
            "engagement_id": memory_config["engagement_id"],
            "data_category": data_category,
            "learning_data": learning_data,
            "confidence_score": confidence_score,
            "stored_at": datetime.utcnow().isoformat(),
            "classification": {
                "sensitivity_level": classification.sensitivity_level,
                "retention_period": classification.retention_period,
                "cross_tenant_sharing": classification.cross_tenant_sharing_allowed
            },
            "privacy_controls": {
                "encrypted": classification.encryption_required,
                "audited": classification.audit_required,
                "isolated": memory_config["isolation_level"] == "strict"
            }
        }
        
        # Store based on learning scope
        storage_result = self._store_by_scope(memory_config, storage_record)
        
        # Audit the storage operation
        if classification.audit_required:
            self._audit_memory_operation(
                "learning_data_stored",
                memory_config,
                {
                    "data_category": data_category,
                    "confidence_score": confidence_score,
                    "data_size": len(str(learning_data)),
                    "encrypted": classification.encryption_required
                }
            )
        
        return storage_result
    
    def retrieve_learning_data(self,
                             memory_config: Dict[str, Any],
                             data_category: str,
                             requesting_client_id: str,
                             requesting_engagement_id: str) -> Dict[str, Any]:
        """
        Retrieve learning data with access control validation
        
        Args:
            memory_config: Memory configuration 
            data_category: Category of data to retrieve
            requesting_client_id: Client requesting the data
            requesting_engagement_id: Engagement requesting the data
        
        Returns:
            Learning data if access is authorized, empty if not
        """
        
        # Validate access permissions
        access_authorized = self._validate_access_permissions(
            memory_config, requesting_client_id, requesting_engagement_id
        )
        
        if not access_authorized:
            self._audit_memory_operation(
                "access_denied",
                memory_config,
                {
                    "requesting_client": requesting_client_id,
                    "requesting_engagement": requesting_engagement_id,
                    "data_category": data_category
                }
            )
            return {"data": None, "access_granted": False, "reason": "insufficient_permissions"}
        
        # Retrieve data based on scope
        learning_data = self._retrieve_by_scope(memory_config, data_category)
        
        # Decrypt if necessary
        classification = self.data_classifications.get(data_category)
        if classification and classification.encryption_required:
            learning_data = self._decrypt_learning_data(learning_data, memory_config)
        
        # Filter data based on privacy controls
        filtered_data = self._apply_privacy_filters(
            learning_data, memory_config, requesting_client_id
        )
        
        # Audit the retrieval
        self._audit_memory_operation(
            "learning_data_retrieved",
            memory_config,
            {
                "requesting_client": requesting_client_id,
                "data_category": data_category,
                "records_returned": len(filtered_data) if filtered_data else 0
            }
        )
        
        return {
            "data": filtered_data,
            "access_granted": True,
            "privacy_filtered": len(filtered_data) != len(learning_data) if learning_data else False
        }
    
    def cleanup_expired_data(self, memory_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up expired learning data based on retention policies
        
        Args:
            memory_config: Memory configuration
        
        Returns:
            Cleanup summary
        """
        
        cleanup_summary = {
            "cleaned_categories": [],
            "records_removed": 0,
            "data_size_freed": 0,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
        
        for category, classification in self.data_classifications.items():
            expired_data = self._find_expired_data(memory_config, category, classification)
            
            if expired_data:
                removal_result = self._remove_expired_data(memory_config, expired_data)
                cleanup_summary["cleaned_categories"].append(category)
                cleanup_summary["records_removed"] += removal_result["records_removed"]
                cleanup_summary["data_size_freed"] += removal_result["data_size_freed"]
        
        # Audit cleanup operation
        self._audit_memory_operation(
            "data_cleanup_completed",
            memory_config,
            cleanup_summary
        )
        
        return cleanup_summary
    
    def get_learning_analytics(self, 
                             client_account_id: str,
                             engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get learning analytics with privacy compliance
        
        Args:
            client_account_id: Client account ID
            engagement_id: Optional engagement ID for engagement-scoped analytics
        
        Returns:
            Learning analytics with privacy controls applied
        """
        
        analytics = {
            "learning_effectiveness": {},
            "data_usage_stats": {},
            "privacy_compliance": {},
            "memory_performance": {}
        }
        
        # Get analytics based on client's memory configurations
        memory_configs = self._get_client_memory_configs(client_account_id, engagement_id)
        
        for config in memory_configs:
            config_analytics = self._calculate_memory_analytics(config)
            analytics = self._merge_analytics(analytics, config_analytics)
        
        # Apply privacy filtering to analytics
        analytics = self._apply_privacy_filters_to_analytics(analytics, client_account_id)
        
        return analytics
    
    # Private helper methods
    
    def _generate_memory_id(self, client_account_id: str, engagement_id: str, scope: LearningScope) -> str:
        """Generate unique memory ID based on scope"""
        base_string = f"{client_account_id}:{engagement_id}:{scope.value}:{datetime.utcnow().date()}"
        return hashlib.sha256(base_string.encode()).hexdigest()[:16]
    
    def _create_access_controls(self, client_id: str, engagement_id: str, 
                              scope: LearningScope, isolation: MemoryIsolationLevel) -> Dict[str, Any]:
        """Create access control configuration"""
        if scope == LearningScope.ENGAGEMENT:
            return {"allowed_clients": [client_id], "allowed_engagements": [engagement_id]}
        elif scope == LearningScope.CLIENT:
            return {"allowed_clients": [client_id], "allowed_engagements": []}
        elif scope == LearningScope.GLOBAL:
            return {"allowed_clients": [], "allowed_engagements": []}  # Open with consent
        else:
            return {"allowed_clients": [], "allowed_engagements": []}  # Disabled
    
    def _create_encryption_config(self, isolation: MemoryIsolationLevel) -> Dict[str, Any]:
        """Create encryption configuration based on isolation level"""
        return {
            "encryption_enabled": isolation != MemoryIsolationLevel.OPEN,
            "key_rotation_days": 30 if isolation == MemoryIsolationLevel.STRICT else 90,
            "algorithm": "AES-256-GCM"
        }
    
    def _create_audit_config(self, client_id: str, engagement_id: str) -> Dict[str, Any]:
        """Create audit configuration"""
        return {
            "audit_enabled": True,
            "audit_level": "detailed",
            "retention_days": 1095,  # 3 years
            "client_id": client_id,
            "engagement_id": engagement_id
        }
    
    def _create_engagement_scoped_memory(self, config: Dict[str, Any]):
        """Create memory instance scoped to single engagement"""
        try:
            from crewai.memory import LongTermMemory
            return LongTermMemory(
                storage_type="vector",
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"},
                storage_config={
                    "namespace": f"engagement_{config['engagement_id']}",
                    "isolation": "strict",
                    "encryption": True
                }
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
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"},
                storage_config={
                    "namespace": f"client_{config['client_account_id']}",
                    "isolation": "moderate",
                    "encryption": True
                }
            )
        except ImportError:
            return self._create_fallback_memory(config)
    
    def _create_global_memory(self, config: Dict[str, Any]):
        """Create global memory instance with consent controls"""
        try:
            from crewai.memory import LongTermMemory
            return LongTermMemory(
                storage_type="vector",
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"},
                storage_config={
                    "namespace": "global_shared",
                    "isolation": "open",
                    "consent_required": True
                }
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
            "isolation_enforced": True
        }
    
    def _audit_memory_operation(self, operation: str, memory_config: Dict[str, Any], details: Dict[str, Any]):
        """Record audit trail for memory operations"""
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "memory_id": memory_config["memory_id"],
            "client_account_id": memory_config["client_account_id"],
            "engagement_id": memory_config["engagement_id"],
            "learning_scope": memory_config["learning_scope"],
            "details": details
        }
        
        # Store audit record (implementation depends on audit storage system)
        self._store_audit_record(audit_record)
        self.logger.info(f"Memory operation audited: {operation}", extra=audit_record)
    
    def _is_cross_tenant_sharing_allowed(self, memory_config: Dict[str, Any], 
                                       classification: LearningDataClassification) -> bool:
        """Check if cross-tenant sharing is allowed for this data"""
        return (
            classification.cross_tenant_sharing_allowed and
            memory_config.get("cross_client_learning_enabled", False) and
            memory_config["learning_scope"] == "global"
        )
    
    def _sanitize_for_tenant_isolation(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tenant-specific information from learning data"""
        # Remove or hash client-specific identifiers
        sanitized = learning_data.copy()
        
        # Remove direct client identifiers
        sanitized.pop("client_account_id", None)
        sanitized.pop("engagement_id", None)
        sanitized.pop("client_name", None)
        
        # Hash or generalize asset names
        if "asset_names" in sanitized:
            sanitized["asset_names"] = [hashlib.sha256(name.encode()).hexdigest()[:8] 
                                      for name in sanitized["asset_names"]]
        
        return sanitized
    
    def _validate_access_permissions(self, memory_config: Dict[str, Any], 
                                   requesting_client: str, requesting_engagement: str) -> bool:
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
    
    def _store_audit_record(self, audit_record: Dict[str, Any]):
        """Store audit record in audit system"""
        # Implementation depends on audit storage system
        # Could be database, file system, or external audit service
        pass
    
    def _encrypt_learning_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt learning data"""
        # Placeholder for encryption implementation
        return {"encrypted": True, "data": data}
    
    def _decrypt_learning_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt learning data"""
        # Placeholder for decryption implementation
        if data.get("encrypted"):
            return data.get("data", {})
        return data
    
    def _store_by_scope(self, memory_config: Dict[str, Any], storage_record: Dict[str, Any]) -> Dict[str, Any]:
        """Store data according to memory scope"""
        # Implementation depends on storage backend
        return {"stored": True, "record_id": storage_record["memory_id"]}
    
    def _retrieve_by_scope(self, memory_config: Dict[str, Any], data_category: str) -> List[Dict[str, Any]]:
        """Retrieve data according to memory scope"""
        # Implementation depends on storage backend
        return []
    
    def _apply_privacy_filters(self, data: List[Dict[str, Any]], 
                             memory_config: Dict[str, Any], requesting_client: str) -> List[Dict[str, Any]]:
        """Apply privacy filters to retrieved data"""
        if not data:
            return []
        
        # Filter based on isolation level and client access
        if memory_config["isolation_level"] == "strict":
            # Only return data from same client
            return [item for item in data 
                   if item.get("client_account_id") == requesting_client]
        
        return data
    
    def _get_privacy_controls(self, memory_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get privacy control summary for memory configuration"""
        return {
            "learning_scope": memory_config["learning_scope"],
            "isolation_level": memory_config["isolation_level"], 
            "cross_client_learning": memory_config["cross_client_learning_enabled"],
            "encryption_enabled": memory_config["encryption_config"]["encryption_enabled"],
            "audit_enabled": memory_config["audit_config"]["audit_enabled"],
            "data_retention_policies": {
                category: classification.retention_period 
                for category, classification in self.data_classifications.items()
            }
        }
    
    # Additional helper methods for analytics, cleanup, etc.
    def _find_expired_data(self, memory_config: Dict[str, Any], category: str, 
                          classification: LearningDataClassification) -> List[Dict[str, Any]]:
        """Find expired data for cleanup"""
        return []
    
    def _remove_expired_data(self, memory_config: Dict[str, Any], 
                           expired_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Remove expired data"""
        return {"records_removed": 0, "data_size_freed": 0}
    
    def _get_client_memory_configs(self, client_id: str, engagement_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memory configurations for client"""
        return []
    
    def _calculate_memory_analytics(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate analytics for memory configuration"""
        return {}
    
    def _merge_analytics(self, base: Dict[str, Any], additional: Dict[str, Any]) -> Dict[str, Any]:
        """Merge analytics from multiple memory configurations"""
        return base
    
    def _apply_privacy_filters_to_analytics(self, analytics: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Apply privacy filters to analytics data"""
        return analytics 