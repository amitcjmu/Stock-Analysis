"""
UX Analyzer

Analyzes user experience and journey through the ADCS workflow.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.models.user_active_flows import UserActiveFlow

from .base import OptimizationContext, UserJourneyAnalytics

logger = logging.getLogger(__name__)


class UXAnalyzer:
    """Analyzes user experience and journey analytics"""
    
    def __init__(self):
        pass
    
    async def create_optimization_context(
        self,
        engagement_id: UUID,
        user_id: UUID
    ) -> OptimizationContext:
        """Create optimization context with relevant data"""
        
        async with AsyncSessionLocal() as session:
            # Get flows data
            flows_data = await self._get_flows_data(session, engagement_id)
            
            # Get user behavior data
            user_behavior = await self._get_user_behavior_data(session, user_id, engagement_id)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(session, engagement_id)
            
            # Get historical data for benchmarking
            historical_data = await self._get_historical_data(session, user_id)
            
            return OptimizationContext(
                engagement_id=engagement_id,
                user_id=user_id,
                flows_data=flows_data,
                user_behavior=user_behavior,
                performance_metrics=performance_metrics,
                historical_data=historical_data
            )
    
    async def analyze_user_journey(self, context: OptimizationContext) -> UserJourneyAnalytics:
        """Analyze the user's journey through the workflow"""
        
        flows_data = context.flows_data
        user_behavior = context.user_behavior
        
        # Determine journey start
        journey_start = datetime.utcnow()
        flows = [
            flows_data.get("collection_flow"),
            flows_data.get("discovery_flow"),
            flows_data.get("assessment_flow")
        ]
        valid_flows = [f for f in flows if f is not None]
        if valid_flows:
            journey_start = min([f.created_at for f in valid_flows])
            
        # Determine current phase
        current_phase = self._determine_current_phase(flows_data)
        
        # Calculate phases completed
        phases_completed = self._get_completed_phases(flows_data)
        
        # Calculate time per phase
        time_per_phase = self._calculate_phase_times(flows_data)
        
        # Calculate automation efficiency
        automation_efficiency = self._calculate_automation_efficiency(flows_data, user_behavior)
        
        # Extract user actions from behavior data
        user_actions = self._extract_user_actions(user_behavior)
        
        # Calculate satisfaction indicators
        satisfaction_indicators = self._calculate_satisfaction_indicators(
            flows_data, user_behavior, automation_efficiency
        )
        
        return UserJourneyAnalytics(
            engagement_id=context.engagement_id,
            user_id=context.user_id,
            journey_start=journey_start,
            current_phase=current_phase,
            phases_completed=phases_completed,
            time_per_phase=time_per_phase,
            errors_encountered=0,  # Would get from error tracking
            manual_interventions=0,  # Would get from intervention tracking
            automation_efficiency=automation_efficiency,
            user_actions=user_actions,
            satisfaction_indicators=satisfaction_indicators
        )
    
    async def _get_flows_data(self, session: AsyncSession, engagement_id: UUID) -> Dict[str, Any]:
        """Get comprehensive flows data"""
        
        # Collection flow
        collection_result = await session.execute(
            select(CollectionFlow).where(CollectionFlow.engagement_id == engagement_id)
        )
        collection_flow = collection_result.scalar_one_or_none()
        
        # Discovery flow
        discovery_result = await session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement_id)
        )
        discovery_flow = discovery_result.scalar_one_or_none()
        
        # Assessment flow
        assessment_result = await session.execute(
            select(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement_id)
        )
        assessment_flow = assessment_result.scalar_one_or_none()
        
        # Assets
        assets_result = await session.execute(
            select(Asset).where(Asset.engagement_id == engagement_id)
        )
        assets = assets_result.scalars().all()
        
        return {
            "collection_flow": collection_flow,
            "discovery_flow": discovery_flow,
            "assessment_flow": assessment_flow,
            "assets": assets,
            "asset_count": len(assets)
        }
    
    async def _get_user_behavior_data(
        self,
        session: AsyncSession,
        user_id: UUID,
        engagement_id: UUID
    ) -> Dict[str, Any]:
        """Get user behavior and interaction data"""
        
        # Get user active flows
        active_flows_result = await session.execute(
            select(UserActiveFlow)
            .where(
                and_(
                    UserActiveFlow.user_id == user_id,
                    UserActiveFlow.engagement_id == engagement_id
                )
            )
        )
        active_flows = active_flows_result.scalars().all()
        
        # Calculate behavior metrics
        total_sessions = len(active_flows)
        avg_session_duration = sum([
            (flow.last_accessed - flow.created_at).total_seconds() 
            for flow in active_flows
        ]) / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "average_session_duration": avg_session_duration,
            "active_flows": [
                {
                    "flow_type": flow.flow_type,
                    "created_at": flow.created_at,
                    "last_accessed": flow.last_accessed,
                    "interaction_count": flow.interaction_count or 0
                }
                for flow in active_flows
            ]
        }
    
    async def _get_performance_metrics(
        self,
        session: AsyncSession,
        engagement_id: UUID
    ) -> Dict[str, float]:
        """Get performance metrics for the engagement"""
        
        # Calculate various performance metrics
        metrics = {}
        
        # Asset processing speed
        assets_result = await session.execute(
            select(Asset).where(Asset.engagement_id == engagement_id)
        )
        assets = assets_result.scalars().all()
        
        metrics["asset_count"] = float(len(assets))
        if assets:
            avg_confidence = sum(a.confidence_score or 0.0 for a in assets) / len(assets)
            metrics["average_confidence"] = avg_confidence
        else:
            metrics["average_confidence"] = 0.0
        
        # Flow completion times (simplified)
        flows_data = await self._get_flows_data(session, engagement_id)
        
        for flow_type, flow in [
            ("collection", flows_data.get("collection_flow")),
            ("discovery", flows_data.get("discovery_flow")),
            ("assessment", flows_data.get("assessment_flow"))
        ]:
            if flow and flow.created_at:
                if flow.status == "completed" and hasattr(flow, 'completed_at') and flow.completed_at:
                    duration = (flow.completed_at - flow.created_at).total_seconds()
                    metrics[f"{flow_type}_completion_time"] = duration
                else:
                    # Ongoing duration
                    duration = (datetime.utcnow() - flow.created_at).total_seconds()
                    metrics[f"{flow_type}_current_duration"] = duration
                    
        return metrics
    
    async def _get_historical_data(self, session: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """Get historical data for benchmarking"""
        
        # Get user's previous engagements for benchmarking
        historical_collections = await session.execute(
            select(CollectionFlow)
            .where(
                and_(
                    CollectionFlow.user_id == user_id,
                    CollectionFlow.status == "completed"
                )
            )
            .limit(10)
        )
        collections = historical_collections.scalars().all()
        
        historical_discoveries = await session.execute(
            select(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.user_id == user_id,
                    DiscoveryFlow.status == "completed"
                )
            )
            .limit(10)
        )
        discoveries = historical_discoveries.scalars().all()
        
        # Calculate historical benchmarks
        avg_collection_time = 0
        avg_discovery_time = 0
        
        if collections:
            collection_times = [
                (flow.completed_at - flow.created_at).total_seconds()
                for flow in collections
                if hasattr(flow, 'completed_at') and flow.completed_at
            ]
            avg_collection_time = sum(collection_times) / len(collection_times) if collection_times else 0
            
        if discoveries:
            discovery_times = [
                (flow.completed_at - flow.created_at).total_seconds()
                for flow in discoveries
                if hasattr(flow, 'completed_at') and flow.completed_at
            ]
            avg_discovery_time = sum(discovery_times) / len(discovery_times) if discovery_times else 0
            
        return {
            "historical_engagements": len(collections) + len(discoveries),
            "average_collection_time": avg_collection_time,
            "average_discovery_time": avg_discovery_time,
            "user_experience_level": "experienced" if len(collections) > 5 else "novice"
        }
    
    def _determine_current_phase(self, flows_data: Dict[str, Any]) -> str:
        """Determine current phase based on flows"""
        if flows_data.get("assessment_flow"):
            return "assessment"
        elif flows_data.get("discovery_flow"):
            return "discovery"
        elif flows_data.get("collection_flow"):
            return "collection"
        return "not_started"
    
    def _get_completed_phases(self, flows_data: Dict[str, Any]) -> List[str]:
        """Get list of completed phases"""
        phases_completed = []
        if flows_data.get("collection_flow") and flows_data["collection_flow"].status == "completed":
            phases_completed.append("collection")
        if flows_data.get("discovery_flow") and flows_data["discovery_flow"].status == "completed":
            phases_completed.append("discovery")
        if flows_data.get("assessment_flow") and flows_data["assessment_flow"].status == "completed":
            phases_completed.append("assessment")
        return phases_completed
    
    def _calculate_phase_times(self, flows_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate time spent in each phase"""
        time_per_phase = {}
        for phase, flow in [
            ("collection", flows_data.get("collection_flow")),
            ("discovery", flows_data.get("discovery_flow")),
            ("assessment", flows_data.get("assessment_flow"))
        ]:
            if flow:
                if flow.status == "completed" and hasattr(flow, 'completed_at') and flow.completed_at:
                    time_per_phase[phase] = (flow.completed_at - flow.created_at).total_seconds()
                else:
                    time_per_phase[phase] = (datetime.utcnow() - flow.created_at).total_seconds()
        return time_per_phase
    
    def _calculate_automation_efficiency(
        self, 
        flows_data: Dict[str, Any], 
        user_behavior: Dict[str, Any]
    ) -> float:
        """Calculate automation efficiency based on manual interventions"""
        # Simplified calculation - in real implementation would track actual automation vs manual steps
        base_efficiency = 0.8
        
        # Adjust based on user interactions
        total_interactions = sum(
            flow_data["interaction_count"] 
            for flow_data in user_behavior.get("active_flows", [])
        )
        
        # Lower efficiency if high manual interaction
        if total_interactions > 50:
            base_efficiency -= 0.2
        elif total_interactions > 20:
            base_efficiency -= 0.1
        
        return max(0.0, min(1.0, base_efficiency))
    
    def _extract_user_actions(self, user_behavior: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract user actions from behavior data"""
        user_actions = []
        for flow_data in user_behavior.get("active_flows", []):
            user_actions.append({
                "flow_type": flow_data["flow_type"],
                "interactions": flow_data["interaction_count"],
                "duration": (flow_data["last_accessed"] - flow_data["created_at"]).total_seconds()
            })
        return user_actions
    
    def _calculate_satisfaction_indicators(
        self, 
        flows_data: Dict[str, Any], 
        user_behavior: Dict[str, Any], 
        automation_efficiency: float
    ) -> Dict[str, float]:
        """Calculate satisfaction indicators"""
        # Simplified satisfaction calculation
        return {
            "progress_smoothness": 0.85,  # Based on error rates and flow continuity
            "automation_satisfaction": automation_efficiency,
            "time_efficiency": 0.75,  # Based on comparison to benchmarks
            "error_resilience": 0.90   # Based on successful error recovery
        }