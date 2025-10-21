"""
Storage and retrieval methods for learning data
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.services.crewai_flows.memory.tenant_memory_manager.enums import LearningScope

logger = logging.getLogger(__name__)


class StorageMixin:
    """Mixin for storage and retrieval operations"""

    def store_learning_data(
        self,
        memory_config: Dict[str, Any],
        data_category: str,
        learning_data: Dict[str, Any],
        confidence_score: float = 0.0,
    ) -> Dict[str, Any]:
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
                "cross_tenant_sharing": classification.cross_tenant_sharing_allowed,
            },
            "privacy_controls": {
                "encrypted": classification.encryption_required,
                "audited": classification.audit_required,
                "isolated": memory_config["isolation_level"] == "strict",
            },
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
                    "encrypted": classification.encryption_required,
                },
            )

        return storage_result

    def retrieve_learning_data(
        self,
        memory_config: Dict[str, Any],
        data_category: str,
        requesting_client_id: str,
        requesting_engagement_id: str,
    ) -> Dict[str, Any]:
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
                    "data_category": data_category,
                },
            )
            return {
                "data": None,
                "access_granted": False,
                "reason": "insufficient_permissions",
            }

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
                "records_returned": len(filtered_data) if filtered_data else 0,
            },
        )

        return {
            "data": filtered_data,
            "access_granted": True,
            "privacy_filtered": (
                len(filtered_data) != len(learning_data) if learning_data else False
            ),
        }

    async def store_learning(
        self,
        client_account_id: int,
        engagement_id: int,
        scope: LearningScope,
        pattern_type: str,
        pattern_data: Dict[str, Any],
    ) -> str:
        """
        Store agent learning pattern with multi-tenant isolation.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            scope: Learning scope (ENGAGEMENT, CLIENT, GLOBAL)
            pattern_type: Type of pattern (e.g., "field_mapping", "asset_classification")
            pattern_data: Pattern data to store

        Returns:
            Pattern ID (UUID as string)
        """
        from app.utils.vector_utils import VectorUtils

        vector_utils = VectorUtils()

        # Generate pattern text for embedding
        pattern_text = f"{pattern_type}: {str(pattern_data)}"
        pattern_name = pattern_data.get("name", pattern_type)

        # Store pattern with tenant scoping
        pattern_id = await vector_utils.store_pattern_embedding(
            pattern_text=pattern_text,
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            client_account_id=str(client_account_id),
            engagement_id=(
                str(engagement_id) if scope == LearningScope.ENGAGEMENT else None
            ),
            pattern_context=pattern_data,
            confidence_score=pattern_data.get("confidence", 0.5),
        )

        logger.info(
            f"Stored learning pattern: {pattern_type} for client {client_account_id}, "
            f"engagement {engagement_id}, scope {scope.value}"
        )

        return pattern_id

    async def retrieve_similar_patterns(
        self,
        client_account_id: int,
        engagement_id: int,
        pattern_type: str,
        query_context: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar patterns for agent context.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            pattern_type: Type of pattern to retrieve
            query_context: Context for similarity search
            limit: Maximum number of results

        Returns:
            List of similar patterns with similarity scores
        """
        from app.services.embedding_service import EmbeddingService
        from app.utils.vector_utils import VectorUtils

        vector_utils = VectorUtils()
        embedding_service = EmbeddingService()

        # Generate query embedding
        query_text = f"{pattern_type}: {str(query_context)}"
        query_embedding = await embedding_service.embed_text(query_text)

        # Find similar patterns with engagement-level isolation
        # Per Qodo Bot review: engagement_id ensures proper data isolation between engagements
        similar_patterns = await vector_utils.find_similar_patterns(
            query_embedding=query_embedding,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),  # Enforce engagement-level isolation
            pattern_type=pattern_type,
            limit=limit,
            similarity_threshold=0.7,
        )

        # Format results
        results = []
        for pattern, similarity in similar_patterns:
            results.append(
                {
                    "pattern_id": pattern["id"],  # Fixed: pattern is a dict, not object
                    "pattern_type": pattern["pattern_type"],
                    "pattern_name": pattern["pattern_name"],
                    "pattern_data": pattern[
                        "pattern_data"
                    ],  # Fixed: was pattern_metadata
                    "confidence": pattern["confidence_score"],
                    "similarity": similarity,
                }
            )

        logger.info(
            f"Retrieved {len(results)} similar patterns for {pattern_type} "
            f"(client {client_account_id}, engagement {engagement_id})"
        )

        return results

    def _store_by_scope(
        self, memory_config: Dict[str, Any], storage_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store data according to memory scope"""
        # Implementation depends on storage backend
        return {"stored": True, "record_id": storage_record["memory_id"]}

    def _retrieve_by_scope(
        self, memory_config: Dict[str, Any], data_category: str
    ) -> List[Dict[str, Any]]:
        """Retrieve data according to memory scope"""
        # Implementation depends on storage backend
        return []

    async def store_questionnaire_template(
        self,
        client_account_id: int,
        engagement_id: int,
        asset_type: str,
        gap_pattern: str,
        questions: List[Dict],
        metadata: Dict[str, Any],
        scope: LearningScope = LearningScope.CLIENT,
    ) -> str:
        """
        Store questionnaire template for reuse across similar assets.

        Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.2:
        Enables 90% cache hit rate for similar assets with same gap patterns.

        This is NOT for LLM cost reduction (questionnaires are deterministic/tool-based),
        but for TIME and UX improvements - avoiding redundant generation operations.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            asset_type: Type of asset (e.g., "database", "server", "application")
            gap_pattern: Sorted string of gap field names (e.g., "backup_strategy_replication_config")
            questions: List of question dictionaries to cache
            metadata: Additional metadata about template generation
            scope: Learning scope (defaults to CLIENT for cross-engagement sharing)

        Returns:
            Pattern ID (UUID as string)
        """
        # Create cache key for exact matching
        cache_key = f"{asset_type}_{gap_pattern}"

        # Build pattern data for storage
        pattern_data = {
            "cache_key": cache_key,
            "questions": questions,
            "asset_type": asset_type,
            "gap_pattern": gap_pattern,
            "metadata": metadata,
            "generated_at": datetime.utcnow().isoformat(),
            "usage_count": 0,  # Track reuse frequency
            "question_count": len(questions),
        }

        # Store using existing store_learning infrastructure
        pattern_id = await self.store_learning(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            scope=scope,  # CLIENT scope allows reuse across engagements
            pattern_type="questionnaire_template",
            pattern_data=pattern_data,
        )

        logger.info(
            f"✅ Stored questionnaire template: {cache_key} "
            f"({len(questions)} questions) for client {client_account_id}"
        )

        return pattern_id

    async def retrieve_questionnaire_template(
        self,
        client_account_id: int,
        engagement_id: int,
        asset_type: str,
        gap_pattern: str,
        scope: LearningScope = LearningScope.CLIENT,
    ) -> Dict[str, Any]:
        """
        Retrieve cached questionnaire template.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            asset_type: Type of asset
            gap_pattern: Sorted string of gap field names
            scope: Learning scope (defaults to CLIENT)

        Returns:
            Dict with 'questions' (list) and 'usage_count' (int), or empty dict if not found
        """
        cache_key = f"{asset_type}_{gap_pattern}"

        # Retrieve using existing retrieve_similar_patterns
        # Use cache_key as query context for exact matching
        patterns = await self.retrieve_similar_patterns(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            pattern_type="questionnaire_template",
            query_context={"cache_key": cache_key},
            limit=1,  # Only need best match
        )

        if patterns:
            pattern = patterns[0]
            pattern_data = pattern.get("pattern_data", {})

            # Increment usage count (for analytics)
            usage_count = pattern_data.get("usage_count", 0) + 1
            pattern_data["usage_count"] = usage_count

            logger.info(
                f"✅ Cache HIT for {cache_key} "
                f"(usage_count: {usage_count}, similarity: {pattern.get('similarity', 0):.2f})"
            )

            return {
                "questions": pattern_data.get("questions", []),
                "usage_count": usage_count,
                "cache_hit": True,
                "similarity": pattern.get("similarity", 0),
                "metadata": pattern_data.get("metadata", {}),
            }

        logger.info(f"❌ Cache MISS for {cache_key} - will generate fresh")
        return {
            "questions": [],
            "usage_count": 0,
            "cache_hit": False,
            "similarity": 0,
        }
