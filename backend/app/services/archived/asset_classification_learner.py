"""
Asset Classification Learner Service

Implements intelligent asset classification learning from user feedback and patterns.
Stores successful classifications and provides AI-powered asset type predictions.
"""

import logging
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.learning_pattern_service import LearningPatternService
from app.services.embedding_service import EmbeddingService
from app.utils.vector_utils import VectorUtils

logger = logging.getLogger(__name__)


@dataclass
class AssetClassification:
    """Represents an asset classification result with confidence."""
    asset_type: str
    application_type: Optional[str] = None
    technology_stack: List[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    pattern_ids: List[str] = None


@dataclass
class ClassificationResult:
    """Result of asset classification learning operation."""
    pattern_id: str
    confidence: float
    success: bool
    message: str


class AssetClassificationLearner:
    """Service for learning and predicting asset classifications."""
    
    def __init__(self):
        self.learning_service = LearningPatternService()
        self.embedding_service = EmbeddingService()
        self.vector_utils = VectorUtils()
        
        # Common asset type patterns
        self.asset_type_patterns = {
            'server': [
                r'.*server.*', r'.*srv.*', r'.*host.*', r'.*node.*',
                r'.*vm.*', r'.*virtual.*', r'.*compute.*'
            ],
            'database': [
                r'.*db.*', r'.*database.*', r'.*sql.*', r'.*oracle.*',
                r'.*mysql.*', r'.*postgres.*', r'.*mongo.*', r'.*redis.*'
            ],
            'application': [
                r'.*app.*', r'.*application.*', r'.*service.*', r'.*api.*',
                r'.*web.*', r'.*portal.*', r'.*frontend.*', r'.*backend.*'
            ],
            'network': [
                r'.*router.*', r'.*switch.*', r'.*firewall.*', r'.*lb.*',
                r'.*loadbalancer.*', r'.*proxy.*', r'.*gateway.*'
            ],
            'storage': [
                r'.*storage.*', r'.*disk.*', r'.*volume.*', r'.*backup.*',
                r'.*archive.*', r'.*nas.*', r'.*san.*'
            ]
        }
        
        # Technology stack patterns
        self.technology_patterns = {
            'java': [r'.*java.*', r'.*jvm.*', r'.*tomcat.*', r'.*spring.*'],
            'python': [r'.*python.*', r'.*django.*', r'.*flask.*', r'.*fastapi.*'],
            'nodejs': [r'.*node.*', r'.*npm.*', r'.*express.*', r'.*react.*'],
            'dotnet': [r'.*\.net.*', r'.*dotnet.*', r'.*csharp.*', r'.*iis.*'],
            'php': [r'.*php.*', r'.*laravel.*', r'.*symfony.*', r'.*wordpress.*'],
            'database': [r'.*mysql.*', r'.*postgres.*', r'.*oracle.*', r'.*mongodb.*']
        }
    
    async def learn_from_classification(
        self,
        asset_name: str,
        asset_metadata: Dict[str, Any],
        classification_result: Dict[str, Any],
        user_confirmed: bool,
        client_account_id: str,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ClassificationResult:
        """
        Learn from an asset classification operation.
        
        Args:
            asset_name: Name of the asset
            asset_metadata: Additional asset metadata (technology, environment, etc.)
            classification_result: The classification that was applied
            user_confirmed: Whether the user confirmed this classification
            client_account_id: Client account ID
            engagement_id: Optional engagement ID
            user_id: Optional user ID who made the classification
            
        Returns:
            ClassificationResult with operation details
        """
        try:
            # Extract patterns from asset name and metadata
            name_patterns = self._extract_name_patterns(asset_name)
            metadata_patterns = self._extract_metadata_patterns(asset_metadata)
            
            # Prepare pattern data
            pattern_data = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "pattern_name": f"{asset_name}_classification",
                "pattern_type": "asset_classification",
                "asset_name_pattern": asset_name.lower(),
                "metadata_patterns": {
                    "name_patterns": name_patterns,
                    "metadata_patterns": metadata_patterns,
                    "original_metadata": asset_metadata
                },
                "predicted_asset_type": classification_result.get("asset_type", "unknown"),
                "predicted_application_type": classification_result.get("application_type"),
                "predicted_technology_stack": classification_result.get("technology_stack", []),
                "confidence_score": 0.9 if user_confirmed else 0.3,  # High confidence for user-confirmed
                "success_count": 1 if user_confirmed else 0,
                "failure_count": 0 if user_confirmed else 1,
                "accuracy_rate": 1.0 if user_confirmed else 0.0,
                "learning_source": "user_feedback" if user_confirmed else "ai_inference",
                "created_by": user_id,
                "pattern_context": {
                    "classification_timestamp": datetime.utcnow().isoformat(),
                    "user_confirmed": user_confirmed,
                    "asset_name": asset_name,
                    "classification_method": "pattern_learning"
                }
            }
            
            # Store the pattern
            pattern_id = await self.learning_service.store_pattern(
                pattern_data, 
                pattern_type="classification"
            )
            
            # Update existing similar patterns if this was confirmed
            if user_confirmed:
                await self._update_similar_classification_patterns(
                    asset_name, 
                    classification_result, 
                    client_account_id
                )
            
            logger.info(f"Learned classification: {asset_name} -> {classification_result.get('asset_type')} (confirmed: {user_confirmed})")
            
            return ClassificationResult(
                pattern_id=pattern_id,
                confidence=pattern_data["confidence_score"],
                success=True,
                message=f"Successfully learned classification pattern for {asset_name}"
            )
            
        except Exception as e:
            logger.error(f"Error learning from classification: {e}")
            return ClassificationResult(
                pattern_id="",
                confidence=0.0,
                success=False,
                message=f"Failed to learn classification: {str(e)}"
            )
    
    async def classify_asset_automatically(
        self,
        asset_data: Dict[str, Any],
        client_account_id: str,
        engagement_id: Optional[str] = None
    ) -> AssetClassification:
        """
        Automatically classify an asset based on learned patterns.
        
        Args:
            asset_data: Asset data including name and metadata
            client_account_id: Client account ID
            engagement_id: Optional engagement ID
            
        Returns:
            AssetClassification with predicted types and confidence
        """
        try:
            asset_name = asset_data.get("name", "")
            asset_metadata = asset_data.get("metadata", {})
            
            # Find similar classification patterns
            similar_patterns = await self._find_similar_asset_patterns(
                asset_name,
                asset_metadata,
                client_account_id
            )
            
            if similar_patterns:
                # Use the best matching pattern
                best_pattern, similarity = similar_patterns[0]
                
                # Calculate confidence based on similarity and pattern accuracy
                pattern_confidence = best_pattern.confidence_score or 0.5
                combined_confidence = (similarity + pattern_confidence) / 2
                
                # Extract classification from pattern
                classification = AssetClassification(
                    asset_type=best_pattern.predicted_asset_type,
                    application_type=best_pattern.predicted_application_type,
                    technology_stack=best_pattern.predicted_technology_stack or [],
                    confidence=combined_confidence,
                    reasoning=self._generate_classification_reasoning(
                        asset_name, best_pattern, similarity
                    ),
                    pattern_ids=[str(best_pattern.id)]
                )
                
                logger.debug(f"Classified {asset_name} as {classification.asset_type} (confidence: {combined_confidence:.3f})")
                return classification
            
            # Fallback to heuristic classification
            return await self._classify_with_heuristics(asset_name, asset_metadata)
            
        except Exception as e:
            logger.error(f"Error classifying asset automatically: {e}")
            return AssetClassification(
                asset_type="unknown",
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def _extract_name_patterns(self, asset_name: str) -> List[str]:
        """Extract patterns from asset name."""
        patterns = []
        name_lower = asset_name.lower()
        
        # Extract common patterns
        patterns.append(f"name_contains_{name_lower}")
        
        # Extract prefix patterns (first 3-5 characters)
        if len(name_lower) >= 3:
            patterns.append(f"prefix_{name_lower[:3]}")
        if len(name_lower) >= 5:
            patterns.append(f"prefix_{name_lower[:5]}")
        
        # Extract suffix patterns (last 3-5 characters)
        if len(name_lower) >= 3:
            patterns.append(f"suffix_{name_lower[-3:]}")
        if len(name_lower) >= 5:
            patterns.append(f"suffix_{name_lower[-5:]}")
        
        # Extract word patterns
        words = re.findall(r'\w+', name_lower)
        for word in words:
            if len(word) >= 3:
                patterns.append(f"word_{word}")
        
        # Extract number patterns
        if re.search(r'\d+', name_lower):
            patterns.append("contains_numbers")
        
        # Extract separator patterns
        if '-' in name_lower:
            patterns.append("dash_separated")
        if '_' in name_lower:
            patterns.append("underscore_separated")
        if '.' in name_lower:
            patterns.append("dot_separated")
        
        return patterns
    
    def _extract_metadata_patterns(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract patterns from asset metadata."""
        patterns = []
        
        # Extract technology patterns
        tech_fields = ['technology', 'tech_stack', 'platform', 'os', 'operating_system']
        for field in tech_fields:
            if field in metadata and metadata[field]:
                tech_value = str(metadata[field]).lower()
                patterns.append(f"tech_{tech_value}")
        
        # Extract environment patterns
        env_fields = ['environment', 'env', 'stage']
        for field in env_fields:
            if field in metadata and metadata[field]:
                env_value = str(metadata[field]).lower()
                patterns.append(f"env_{env_value}")
        
        # Extract location patterns
        location_fields = ['location', 'datacenter', 'region', 'zone']
        for field in location_fields:
            if field in metadata and metadata[field]:
                location_value = str(metadata[field]).lower()
                patterns.append(f"location_{location_value}")
        
        return patterns
    
    async def _find_similar_asset_patterns(
        self,
        asset_name: str,
        asset_metadata: Dict[str, Any],
        client_account_id: str,
        limit: int = 5
    ) -> List[Tuple[Any, float]]:
        """Find similar asset classification patterns."""
        try:
            # Use vector utils to find similar patterns
            similar_patterns = await self.vector_utils.find_similar_asset_patterns(
                asset_name,
                client_account_id,
                limit=limit,
                similarity_threshold=0.6
            )
            
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Error finding similar asset patterns: {e}")
            return []
    
    async def _classify_with_heuristics(
        self,
        asset_name: str,
        asset_metadata: Dict[str, Any]
    ) -> AssetClassification:
        """Classify asset using heuristic patterns when no learned patterns exist."""
        name_lower = asset_name.lower()
        
        # Check asset type patterns
        for asset_type, patterns in self.asset_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    # Check for technology stack
                    tech_stack = []
                    for tech, tech_patterns in self.technology_patterns.items():
                        for tech_pattern in tech_patterns:
                            if re.search(tech_pattern, name_lower):
                                tech_stack.append(tech)
                    
                    return AssetClassification(
                        asset_type=asset_type,
                        technology_stack=tech_stack,
                        confidence=0.6,  # Medium confidence for heuristics
                        reasoning=f"Heuristic classification based on name pattern '{pattern}'"
                    )
        
        # Default classification
        return AssetClassification(
            asset_type="server",  # Default to server
            confidence=0.3,  # Low confidence
            reasoning="Default classification - no patterns matched"
        )
    
    def _generate_classification_reasoning(
        self,
        asset_name: str,
        pattern: Any,
        similarity: float
    ) -> str:
        """Generate human-readable reasoning for classification."""
        reasoning_parts = [
            f"Based on similarity to learned pattern '{pattern.pattern_name}' (similarity: {similarity:.3f})"
        ]
        
        if pattern.accuracy_rate and pattern.accuracy_rate > 0.8:
            reasoning_parts.append(f"Pattern has high accuracy rate: {pattern.accuracy_rate:.1%}")
        
        if pattern.success_count and pattern.success_count > 5:
            reasoning_parts.append(f"Pattern confirmed {pattern.success_count} times")
        
        return ". ".join(reasoning_parts)
    
    async def _update_similar_classification_patterns(
        self,
        asset_name: str,
        classification_result: Dict[str, Any],
        client_account_id: str
    ) -> None:
        """Update confidence of similar patterns when user confirms classification."""
        try:
            similar_patterns = await self._find_similar_asset_patterns(
                asset_name, {}, client_account_id, limit=10
            )
            
            for pattern, similarity in similar_patterns:
                if similarity > 0.8:  # High similarity threshold
                    # Boost confidence for very similar patterns
                    await self.vector_utils.update_pattern_performance(
                        str(pattern.id),
                        was_successful=True,
                        pattern_type="classification"
                    )
            
        except Exception as e:
            logger.error(f"Error updating similar classification patterns: {e}")
    
    async def get_classification_statistics(
        self,
        client_account_id: str
    ) -> Dict[str, Any]:
        """Get classification learning statistics for a client."""
        try:
            # This would query the learning patterns to get statistics
            # For now, return basic structure
            return {
                "total_patterns": 0,
                "asset_types": {},
                "accuracy_by_type": {},
                "recent_classifications": []
            }
            
        except Exception as e:
            logger.error(f"Error getting classification statistics: {e}")
            return {} 