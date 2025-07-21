"""
Asset Classification Learning Module - Handles asset classification patterns
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.agent_learning.models import LearningContext

logger = logging.getLogger(__name__)


class AssetClassificationLearning:
    """Handles asset classification pattern learning."""
    
    async def learn_from_asset_classification(
        self,
        asset_name: str,
        asset_metadata: Dict[str, Any],
        classification_result: Dict[str, Any],
        user_confirmed: bool,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Learns from an asset classification operation."""
        if not context:
            context = LearningContext()
        
        try:
            pattern_data = {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "pattern_name": f"{asset_name}_classification",
                "pattern_type": "asset_classification",
                "asset_name_pattern": asset_name.lower(),
                "metadata_patterns": {
                    "original_metadata": asset_metadata
                },
                "predicted_asset_type": classification_result.get("asset_type", "unknown"),
                "confidence_score": 0.9 if user_confirmed else 0.3,
                "learning_source": "user_feedback" if user_confirmed else "ai_inference",
                "created_by": context.user_id,
            }
            
            pattern_id = await self._store_classification_pattern(pattern_data)
            
            return {
                "pattern_id": pattern_id,
                "confidence": pattern_data["confidence_score"],
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error learning from classification: {e}")
            return {"success": False, "error": str(e)}

    async def classify_asset_automatically(
        self,
        asset_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Automatically classify an asset based on learned patterns."""
        if not context:
            context = LearningContext()

        try:
            asset_name = asset_data.get("name", "")
            
            similar_patterns = await self.vector_utils.find_similar_asset_patterns(
                asset_name,
                context.client_account_id,
                limit=1,
                similarity_threshold=0.7
            )
            
            if similar_patterns:
                best_pattern, similarity = similar_patterns[0]
                return {
                    "asset_type": best_pattern.predicted_asset_type,
                    "confidence": (similarity + best_pattern.confidence_score) / 2,
                    "pattern_id": str(best_pattern.id)
                }
            
            return {"asset_type": "unknown", "confidence": 0.1}
            
        except Exception as e:
            logger.error(f"Error classifying asset automatically: {e}")
            return {"asset_type": "unknown", "confidence": 0.0, "error": str(e)}

    async def _store_classification_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store an asset classification pattern."""
        # TODO: Implement when AssetClassificationPattern model is available
        logger.warning("AssetClassificationPattern model not available - storing in memory only")
        # For now, just return a placeholder ID
        return f"pattern_{pattern_data.get('asset_name_pattern', 'unknown')}_{int(time.time())}"
        
        # Original implementation commented out until model is available:
        # name_embedding = await self.embedding_service.embed_text(pattern_data["asset_name_pattern"])
        # 
        # async with AsyncSessionLocal() as session:
        #     pattern = AssetClassificationPattern(
        #         client_account_id=pattern_data["client_account_id"],
        #         engagement_id=pattern_data.get("engagement_id"),
        #         asset_name_pattern=pattern_data["asset_name_pattern"],
        #         asset_name_embedding=name_embedding,
        #         metadata_patterns=pattern_data["metadata_patterns"],
        #         predicted_asset_type=pattern_data["predicted_asset_type"],
        #         confidence_score=pattern_data["confidence_score"],
        #         learning_source=pattern_data["learning_source"],
        #         created_by=pattern_data.get("created_by")
        #     )
        #     session.add(pattern)
        #     await session.commit()
        #     await session.refresh(pattern)
        #     return str(pattern.id)