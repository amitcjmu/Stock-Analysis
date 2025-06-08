"""
Confidence Manager Service

Implements dynamic confidence threshold management for AI-powered operations.
Adjusts thresholds based on user feedback and correction patterns.
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.core.database import AsyncSessionLocal
# from app.models.learning_patterns import ConfidenceThreshold, UserFeedbackEvent

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for different operations."""
    auto_apply: float = 0.9      # Automatically apply suggestions above this threshold
    suggest: float = 0.6         # Show suggestions above this threshold
    reject: float = 0.3          # Reject suggestions below this threshold
    operation_type: str = ""
    client_account_id: str = ""
    last_updated: Optional[datetime] = None


@dataclass
class ThresholdAdjustment:
    """Result of threshold adjustment operation."""
    operation_type: str
    old_thresholds: ConfidenceThresholds
    new_thresholds: ConfidenceThresholds
    adjustment_reason: str
    success: bool


class ConfidenceManager:
    """Service for managing dynamic confidence thresholds."""
    
    def __init__(self):
        # Default thresholds for different operation types
        self.default_thresholds = {
            "field_mapping": ConfidenceThresholds(
                auto_apply=0.9,
                suggest=0.6,
                reject=0.3,
                operation_type="field_mapping"
            ),
            "asset_classification": ConfidenceThresholds(
                auto_apply=0.85,
                suggest=0.65,
                reject=0.35,
                operation_type="asset_classification"
            ),
            "migration_strategy": ConfidenceThresholds(
                auto_apply=0.95,  # Higher threshold for critical decisions
                suggest=0.7,
                reject=0.4,
                operation_type="migration_strategy"
            ),
            "risk_assessment": ConfidenceThresholds(
                auto_apply=0.9,
                suggest=0.65,
                reject=0.3,
                operation_type="risk_assessment"
            )
        }
    
    async def get_thresholds(
        self,
        client_account_id: str,
        operation_type: str
    ) -> ConfidenceThresholds:
        """
        Get confidence thresholds for a client and operation type.
        
        Args:
            client_account_id: Client account ID
            operation_type: Type of operation (field_mapping, asset_classification, etc.)
            
        Returns:
            ConfidenceThresholds for the client and operation
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get all threshold records for this client and operation
                result = await session.execute(
                    select(ConfidenceThreshold).where(
                        and_(
                            ConfidenceThreshold.client_account_id == client_account_id,
                            ConfidenceThreshold.operation_type == operation_type
                        )
                    )
                )
                
                threshold_records = result.scalars().all()
                
                if threshold_records:
                    # Build thresholds from individual records
                    thresholds = ConfidenceThresholds(
                        operation_type=operation_type,
                        client_account_id=client_account_id
                    )
                    
                    for record in threshold_records:
                        if record.threshold_name == 'auto_apply':
                            thresholds.auto_apply = record.threshold_value
                        elif record.threshold_name == 'suggest':
                            thresholds.suggest = record.threshold_value
                        elif record.threshold_name == 'reject':
                            thresholds.reject = record.threshold_value
                        
                        if record.updated_at:
                            thresholds.last_updated = record.updated_at
                    
                    return thresholds
                else:
                    # Create and store default thresholds
                    default = self.default_thresholds.get(
                        operation_type, 
                        self.default_thresholds["field_mapping"]
                    )
                    
                    await self._store_thresholds(
                        session,
                        client_account_id,
                        operation_type,
                        default
                    )
                    await session.commit()
                    
                    default.client_account_id = client_account_id
                    return default
                    
        except Exception as e:
            logger.error(f"Error getting thresholds: {e}")
            # Return default thresholds as fallback
            default = self.default_thresholds.get(
                operation_type, 
                self.default_thresholds["field_mapping"]
            )
            default.client_account_id = client_account_id
            return default
    
    async def adjust_thresholds(
        self,
        client_account_id: str,
        operation_type: str,
        correction_event: Dict[str, Any]
    ) -> ThresholdAdjustment:
        """
        Adjust confidence thresholds based on user correction patterns.
        
        Args:
            client_account_id: Client account ID
            operation_type: Type of operation
            correction_event: Details about the user correction
            
        Returns:
            ThresholdAdjustment with old and new thresholds
        """
        try:
            # Get current thresholds
            current_thresholds = await self.get_thresholds(client_account_id, operation_type)
            
            # Analyze correction patterns
            correction_analysis = await self._analyze_correction_patterns(
                client_account_id,
                operation_type
            )
            
            # Calculate threshold adjustments
            new_thresholds = self._calculate_threshold_adjustments(
                current_thresholds,
                correction_event,
                correction_analysis
            )
            
            # Store updated thresholds
            async with AsyncSessionLocal() as session:
                await self._update_thresholds(
                    session,
                    client_account_id,
                    operation_type,
                    new_thresholds
                )
                await session.commit()
            
            adjustment_reason = self._generate_adjustment_reason(
                correction_event,
                correction_analysis
            )
            
            logger.info(f"Adjusted thresholds for {client_account_id}/{operation_type}: {adjustment_reason}")
            
            return ThresholdAdjustment(
                operation_type=operation_type,
                old_thresholds=current_thresholds,
                new_thresholds=new_thresholds,
                adjustment_reason=adjustment_reason,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error adjusting thresholds: {e}")
            return ThresholdAdjustment(
                operation_type=operation_type,
                old_thresholds=current_thresholds,
                new_thresholds=current_thresholds,
                adjustment_reason=f"Adjustment failed: {str(e)}",
                success=False
            )
    
    async def record_user_feedback(
        self,
        client_account_id: str,
        operation_type: str,
        original_confidence: float,
        user_action: str,  # 'accepted', 'rejected', 'corrected'
        was_correct: bool,
        feedback_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record user feedback for threshold adjustment analysis.
        
        Args:
            client_account_id: Client account ID
            operation_type: Type of operation
            original_confidence: Original confidence score
            user_action: What the user did
            was_correct: Whether the original suggestion was correct
            feedback_details: Additional feedback details
            
        Returns:
            True if feedback was recorded successfully
        """
        try:
            async with AsyncSessionLocal() as session:
                feedback_event = UserFeedbackEvent(
                    client_account_id=client_account_id,
                    feedback_type=operation_type,  # Use feedback_type instead of operation_type
                    original_confidence=original_confidence,
                    original_suggestion={"action": user_action, "was_correct": was_correct},
                    user_correction=feedback_details or {},
                    correction_type=user_action,
                    created_at=datetime.utcnow()
                )
                
                session.add(feedback_event)
                await session.commit()
                
                logger.debug(f"Recorded feedback: {user_action} for {operation_type} (confidence: {original_confidence})")
                return True
                
        except Exception as e:
            logger.error(f"Error recording user feedback: {e}")
            return False
    
    async def get_threshold_statistics(
        self,
        client_account_id: str,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about threshold performance and adjustments.
        
        Args:
            client_account_id: Client account ID
            operation_type: Optional operation type filter
            
        Returns:
            Dictionary with threshold statistics
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get feedback events for analysis
                query = select(UserFeedbackEvent).where(
                    UserFeedbackEvent.client_account_id == client_account_id
                )
                
                if operation_type:
                    query = query.where(UserFeedbackEvent.feedback_type == operation_type)
                
                # Get recent feedback (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                query = query.where(UserFeedbackEvent.created_at >= thirty_days_ago)
                
                result = await session.execute(query)
                feedback_events = result.scalars().all()
                
                # Calculate statistics
                stats = self._calculate_threshold_statistics(feedback_events)
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting threshold statistics: {e}")
            return {}
    
    async def _store_thresholds(
        self,
        session: AsyncSession,
        client_account_id: str,
        operation_type: str,
        thresholds: ConfidenceThresholds
    ) -> None:
        """Store new thresholds in database."""
        # Store each threshold as a separate record
        threshold_configs = [
            ('auto_apply', thresholds.auto_apply),
            ('suggest', thresholds.suggest),
            ('reject', thresholds.reject)
        ]
        
        for threshold_name, threshold_value in threshold_configs:
            threshold_record = ConfidenceThreshold(
                client_account_id=client_account_id,
                operation_type=operation_type,
                threshold_name=threshold_name,
                threshold_value=threshold_value,
                initial_value=threshold_value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(threshold_record)
        
        await session.flush()
    
    async def _update_thresholds(
        self,
        session: AsyncSession,
        client_account_id: str,
        operation_type: str,
        thresholds: ConfidenceThresholds
    ) -> None:
        """Update existing thresholds in database."""
        # Update each threshold separately
        threshold_updates = [
            ('auto_apply', thresholds.auto_apply),
            ('suggest', thresholds.suggest),
            ('reject', thresholds.reject)
        ]
        
        for threshold_name, threshold_value in threshold_updates:
            await session.execute(
                update(ConfidenceThreshold)
                .where(
                    and_(
                        ConfidenceThreshold.client_account_id == client_account_id,
                        ConfidenceThreshold.operation_type == operation_type,
                        ConfidenceThreshold.threshold_name == threshold_name
                    )
                )
                .values(
                    threshold_value=threshold_value,
                    adjustment_count=ConfidenceThreshold.adjustment_count + 1,
                    last_adjustment=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
    
    async def _analyze_correction_patterns(
        self,
        client_account_id: str,
        operation_type: str
    ) -> Dict[str, Any]:
        """Analyze user correction patterns to inform threshold adjustments."""
        try:
            async with AsyncSessionLocal() as session:
                # Get recent feedback events (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                result = await session.execute(
                    select(UserFeedbackEvent).where(
                        and_(
                            UserFeedbackEvent.client_account_id == client_account_id,
                            UserFeedbackEvent.feedback_type == operation_type,
                            UserFeedbackEvent.created_at >= thirty_days_ago
                        )
                    )
                )
                
                feedback_events = result.scalars().all()
                
                if not feedback_events:
                    return {"total_events": 0}
                
                # Analyze patterns
                total_events = len(feedback_events)
                accepted_count = sum(1 for e in feedback_events if e.correction_type == 'accepted')
                rejected_count = sum(1 for e in feedback_events if e.correction_type == 'rejected')
                corrected_count = sum(1 for e in feedback_events if e.correction_type == 'corrected')
                
                # Calculate accuracy by confidence ranges
                high_confidence_events = [e for e in feedback_events if e.original_confidence >= 0.8]
                medium_confidence_events = [e for e in feedback_events if 0.5 <= e.original_confidence < 0.8]
                low_confidence_events = [e for e in feedback_events if e.original_confidence < 0.5]
                
                return {
                    "total_events": total_events,
                    "accepted_rate": accepted_count / total_events,
                    "rejected_rate": rejected_count / total_events,
                    "corrected_rate": corrected_count / total_events,
                    "high_confidence_accuracy": self._calculate_accuracy(high_confidence_events),
                    "medium_confidence_accuracy": self._calculate_accuracy(medium_confidence_events),
                    "low_confidence_accuracy": self._calculate_accuracy(low_confidence_events),
                    "avg_confidence": sum(e.original_confidence for e in feedback_events) / total_events
                }
                
        except Exception as e:
            logger.error(f"Error analyzing correction patterns: {e}")
            return {"total_events": 0}
    
    def _calculate_accuracy(self, events: List[UserFeedbackEvent]) -> float:
        """Calculate accuracy rate for a list of feedback events."""
        if not events:
            return 0.0
        
        # Consider 'accepted' as correct, others as incorrect for simplicity
        correct_count = sum(1 for e in events if e.correction_type == 'accepted')
        return correct_count / len(events)
    
    def _calculate_threshold_adjustments(
        self,
        current_thresholds: ConfidenceThresholds,
        correction_event: Dict[str, Any],
        correction_analysis: Dict[str, Any]
    ) -> ConfidenceThresholds:
        """Calculate new thresholds based on correction patterns."""
        new_thresholds = ConfidenceThresholds(
            auto_apply=current_thresholds.auto_apply,
            suggest=current_thresholds.suggest,
            reject=current_thresholds.reject,
            operation_type=current_thresholds.operation_type,
            client_account_id=current_thresholds.client_account_id
        )
        
        if correction_analysis.get("total_events", 0) < 5:
            # Not enough data for adjustments
            return new_thresholds
        
        # Adjust based on accuracy rates
        high_confidence_accuracy = correction_analysis.get("high_confidence_accuracy", 0.9)
        medium_confidence_accuracy = correction_analysis.get("medium_confidence_accuracy", 0.7)
        
        # If high confidence suggestions are often wrong, raise auto_apply threshold
        if high_confidence_accuracy < 0.8:
            new_thresholds.auto_apply = min(0.95, current_thresholds.auto_apply + 0.05)
        elif high_confidence_accuracy > 0.95:
            new_thresholds.auto_apply = max(0.8, current_thresholds.auto_apply - 0.02)
        
        # If medium confidence suggestions are often wrong, raise suggest threshold
        if medium_confidence_accuracy < 0.6:
            new_thresholds.suggest = min(0.8, current_thresholds.suggest + 0.05)
        elif medium_confidence_accuracy > 0.85:
            new_thresholds.suggest = max(0.5, current_thresholds.suggest - 0.02)
        
        # Ensure thresholds maintain proper order
        new_thresholds.suggest = min(new_thresholds.suggest, new_thresholds.auto_apply - 0.1)
        new_thresholds.reject = min(new_thresholds.reject, new_thresholds.suggest - 0.1)
        
        return new_thresholds
    
    def _generate_adjustment_reason(
        self,
        correction_event: Dict[str, Any],
        correction_analysis: Dict[str, Any]
    ) -> str:
        """Generate human-readable reason for threshold adjustment."""
        total_events = correction_analysis.get("total_events", 0)
        
        if total_events < 5:
            return "Insufficient feedback data for threshold adjustment"
        
        high_accuracy = correction_analysis.get("high_confidence_accuracy", 0.9)
        medium_accuracy = correction_analysis.get("medium_confidence_accuracy", 0.7)
        
        reasons = []
        
        if high_accuracy < 0.8:
            reasons.append(f"High confidence accuracy low ({high_accuracy:.1%})")
        elif high_accuracy > 0.95:
            reasons.append(f"High confidence accuracy excellent ({high_accuracy:.1%})")
        
        if medium_accuracy < 0.6:
            reasons.append(f"Medium confidence accuracy low ({medium_accuracy:.1%})")
        elif medium_accuracy > 0.85:
            reasons.append(f"Medium confidence accuracy good ({medium_accuracy:.1%})")
        
        if not reasons:
            return "Thresholds maintained based on stable performance"
        
        return "Adjusted based on: " + ", ".join(reasons)
    
    def _calculate_threshold_statistics(
        self,
        feedback_events: List[UserFeedbackEvent]
    ) -> Dict[str, Any]:
        """Calculate statistics from feedback events."""
        if not feedback_events:
            return {
                "total_feedback": 0,
                "accuracy_by_confidence": {},
                "user_action_distribution": {}
            }
        
        total_feedback = len(feedback_events)
        
        # Group by confidence ranges
        confidence_ranges = {
            "high (0.8+)": [e for e in feedback_events if e.original_confidence >= 0.8],
            "medium (0.5-0.8)": [e for e in feedback_events if 0.5 <= e.original_confidence < 0.8],
            "low (<0.5)": [e for e in feedback_events if e.original_confidence < 0.5]
        }
        
        accuracy_by_confidence = {}
        for range_name, events in confidence_ranges.items():
            if events:
                accuracy = sum(1 for e in events if e.was_correct) / len(events)
                accuracy_by_confidence[range_name] = {
                    "accuracy": accuracy,
                    "count": len(events)
                }
        
        # User action distribution
        action_counts = {}
        for event in feedback_events:
            action_counts[event.correction_type] = action_counts.get(event.correction_type, 0) + 1
        
        user_action_distribution = {
            action: count / total_feedback 
            for action, count in action_counts.items()
        }
        
        return {
            "total_feedback": total_feedback,
            "accuracy_by_confidence": accuracy_by_confidence,
            "user_action_distribution": user_action_distribution,
            "overall_accuracy": sum(1 for e in feedback_events if e.correction_type == 'accepted') / total_feedback
        } 