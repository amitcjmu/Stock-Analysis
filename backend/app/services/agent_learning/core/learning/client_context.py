"""
Client Context Management Module - Handles client and engagement context learning
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class ClientContextManager:
    """Handles client and engagement context management for learning."""

    async def create_client_learning_context(
        self, client_account_id: str, client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create client-specific learning context.
        Integrated from client_context_manager.py for consolidated context management.
        """
        context = LearningContext(client_account_id=client_account_id)
        memory = self._get_context_memory(context)

        # Store client context information
        memory.add_experience(
            "client_context",
            {
                "client_account_id": client_account_id,
                "client_name": client_data.get(
                    "client_name", f"Client {client_account_id}"
                ),
                "industry": client_data.get("industry"),
                "organization_size": client_data.get("organization_size"),
                "technology_stack": client_data.get("technology_stack", []),
                "business_priorities": client_data.get("business_priorities", []),
                "compliance_requirements": client_data.get(
                    "compliance_requirements", []
                ),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Created client learning context for {client_account_id}")
        return {"status": "created", "context_key": context.context_hash}

    async def create_engagement_learning_context(
        self,
        engagement_id: str,
        client_account_id: str,
        engagement_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create engagement-specific learning context.
        Integrated from client_context_manager.py for consolidated context management.
        """
        context = LearningContext(
            client_account_id=client_account_id, engagement_id=engagement_id
        )
        memory = self._get_context_memory(context)

        # Store engagement context information
        memory.add_experience(
            "engagement_context",
            {
                "engagement_id": engagement_id,
                "client_account_id": client_account_id,
                "engagement_name": engagement_data.get(
                    "engagement_name", f"Engagement {engagement_id}"
                ),
                "engagement_type": engagement_data.get("engagement_type"),
                "migration_goals": engagement_data.get("migration_goals", []),
                "timeline": engagement_data.get("timeline"),
                "stakeholders": engagement_data.get("stakeholders", []),
                "technical_constraints": engagement_data.get(
                    "technical_constraints", []
                ),
                "business_constraints": engagement_data.get("business_constraints", []),
                "success_criteria": engagement_data.get("success_criteria", []),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Created engagement learning context for {engagement_id}")
        return {"status": "created", "context_key": context.context_hash}

    async def learn_organizational_pattern(
        self, client_account_id: str, pattern_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn organizational patterns specific to the client.
        Integrated from client_context_manager.py for consolidated learning.
        """
        context = LearningContext(client_account_id=client_account_id)

        pattern = LearningPattern(
            pattern_id=f"org_pattern_{datetime.utcnow().timestamp()}",
            pattern_type="organizational_pattern",
            context=context,
            pattern_data=pattern_data.get("pattern_data", {}),
            confidence=pattern_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )

        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []

        self.learning_patterns[context_key].append(pattern)

        # Update stats
        self.global_stats["organizational_patterns"] = (
            self.global_stats.get("organizational_patterns", 0) + 1
        )
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1

        self._save_learning_patterns()

        logger.info(f"Learned organizational pattern for client {client_account_id}")
        return {"status": "learned", "pattern_id": pattern.pattern_id}

    async def get_client_learning_context(
        self, client_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get client learning context information."""
        context = LearningContext(client_account_id=client_account_id)
        memory = self._get_context_memory(context)

        client_contexts = memory.experiences.get("client_context", [])
        if client_contexts:
            return client_contexts[-1]  # Return most recent

        return None

    async def get_engagement_learning_context(
        self, engagement_id: str, client_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get engagement learning context information."""
        context = LearningContext(
            client_account_id=client_account_id, engagement_id=engagement_id
        )
        memory = self._get_context_memory(context)

        engagement_contexts = memory.experiences.get("engagement_context", [])
        if engagement_contexts:
            return engagement_contexts[-1]  # Return most recent

        return None

    async def get_organizational_patterns(
        self, client_account_id: str
    ) -> List[Dict[str, Any]]:
        """Get organizational patterns for a client."""
        context = LearningContext(client_account_id=client_account_id)
        context_key = context.context_hash

        patterns = self.learning_patterns.get(context_key, [])
        org_patterns = [
            p for p in patterns if p.pattern_type == "organizational_pattern"
        ]

        return [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "pattern_data": p.pattern_data,
                "confidence": p.confidence,
                "usage_count": p.usage_count,
                "created_at": p.created_at.isoformat(),
                "last_used": p.last_used.isoformat(),
            }
            for p in org_patterns
        ]

    async def get_combined_learning_context(
        self, engagement_id: str, client_account_id: str
    ) -> Dict[str, Any]:
        """Get combined client and engagement learning context."""
        client_context = await self.get_client_learning_context(client_account_id)
        engagement_context = await self.get_engagement_learning_context(
            engagement_id, client_account_id
        )
        org_patterns = await self.get_organizational_patterns(client_account_id)

        return {
            "client_context": client_context,
            "engagement_context": engagement_context,
            "organizational_patterns": org_patterns,
            "context_separation": "isolated_per_client_engagement",
        }
