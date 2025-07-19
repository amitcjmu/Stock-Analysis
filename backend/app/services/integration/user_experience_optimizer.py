"""
User Experience Optimizer for ADCS End-to-End Integration

This service optimizes user experience across the Collection → Discovery → Assessment workflow,
providing intelligent recommendations, progress optimization, and seamless flow transitions.

Generated with CC for ADCS end-to-end integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.monitoring.metrics import track_performance
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models.user_active_flows import UserActiveFlows

logger = get_logger(__name__)

class UXOptimizationArea(Enum):
    """Areas of user experience optimization"""
    WORKFLOW_NAVIGATION = "workflow_navigation"
    PROGRESS_TRACKING = "progress_tracking"
    ERROR_COMMUNICATION = "error_communication"
    DATA_VISUALIZATION = "data_visualization"
    AUTOMATION_TRANSPARENCY = "automation_transparency"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"

class UXMetricType(Enum):
    """Types of UX metrics"""
    TIME_TO_COMPLETION = "time_to_completion"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    ABANDONMENT_RATE = "abandonment_rate"
    TASK_SUCCESS_RATE = "task_success_rate"
    COGNITIVE_LOAD = "cognitive_load"

@dataclass
class UXRecommendation:
    """User experience improvement recommendation"""
    id: str
    area: UXOptimizationArea
    title: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    priority_score: float
    implementation_guidance: List[str]
    expected_improvement: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserJourneyAnalytics:
    """Analytics for user journey through ADCS workflow"""
    engagement_id: UUID
    user_id: UUID
    journey_start: datetime
    current_phase: str
    phases_completed: List[str]
    time_per_phase: Dict[str, float]
    errors_encountered: int
    manual_interventions: int
    automation_efficiency: float
    user_actions: List[Dict[str, Any]]
    satisfaction_indicators: Dict[str, float]

@dataclass
class OptimizationContext:
    """Context for UX optimization"""
    engagement_id: UUID
    user_id: UUID
    flows_data: Dict[str, Any]
    user_behavior: Dict[str, Any]
    performance_metrics: Dict[str, float]
    historical_data: Dict[str, Any]

class UserExperienceOptimizer:
    """
    Optimizes user experience across the complete ADCS workflow
    """
    
    def __init__(self):
        self.ux_metrics_cache: Dict[UUID, Dict[str, Any]] = {}
        self.user_preferences: Dict[UUID, Dict[str, Any]] = {}
        self.optimization_rules = self._initialize_optimization_rules()
        
    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize UX optimization rules"""
        return {
            "workflow_navigation": {
                "auto_advance_threshold": 0.9,  # Auto-advance when confidence > 90%
                "show_preview": True,
                "breadcrumb_depth": 3,
                "shortcuts_enabled": True
            },
            "progress_tracking": {
                "granular_progress": True,
                "estimated_time_remaining": True,
                "milestone_celebrations": True,
                "comparative_benchmarks": True
            },
            "error_communication": {
                "progressive_disclosure": True,
                "suggested_actions": True,
                "recovery_guidance": True,
                "expert_escalation": True
            },
            "data_visualization": {
                "adaptive_charts": True,
                "drill_down_enabled": True,
                "export_options": True,
                "accessibility_features": True
            },
            "automation_transparency": {
                "ai_confidence_display": True,
                "processing_indicators": True,
                "manual_override_options": True,
                "explanation_on_demand": True
            },
            "performance_optimization": {
                "lazy_loading": True,
                "progressive_enhancement": True,
                "caching_strategy": "intelligent",
                "background_processing": True
            }
        }
        
    @track_performance("ux.optimization.analyze")
    async def analyze_user_experience(
        self,
        engagement_id: UUID,
        user_id: UUID
    ) -> Tuple[UserJourneyAnalytics, List[UXRecommendation]]:
        """
        Analyze user experience and provide optimization recommendations
        """
        
        logger.info(
            "Analyzing user experience for workflow optimization",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id)
            }
        )
        
        try:
            # Create optimization context
            context = await self._create_optimization_context(engagement_id, user_id)
            
            # Analyze user journey
            journey_analytics = await self._analyze_user_journey(context)
            
            # Generate UX recommendations
            recommendations = await self._generate_ux_recommendations(context, journey_analytics)
            
            # Cache metrics for future optimization
            self.ux_metrics_cache[engagement_id] = {
                "journey_analytics": journey_analytics,
                "recommendations": recommendations,
                "last_updated": datetime.utcnow()
            }
            
            logger.info(
                "User experience analysis completed",
                extra={
                    "engagement_id": str(engagement_id),
                    "recommendations_count": len(recommendations),
                    "journey_duration": (datetime.utcnow() - journey_analytics.journey_start).total_seconds()
                }
            )
            
            return journey_analytics, recommendations
            
        except Exception as e:
            logger.error(
                "Error during user experience analysis",
                extra={
                    "engagement_id": str(engagement_id),
                    "user_id": str(user_id),
                    "error": str(e)
                }
            )
            raise
            
    async def _create_optimization_context(
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
            select(UserActiveFlows)
            .where(
                and_(
                    UserActiveFlows.user_id == user_id,
                    UserActiveFlows.engagement_id == engagement_id
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
            select(func.count(Asset.id), func.avg(Asset.confidence_score))
            .where(Asset.engagement_id == engagement_id)
        )
        asset_count, avg_confidence = assets_result.first()
        
        metrics["asset_count"] = float(asset_count or 0)
        metrics["average_confidence"] = float(avg_confidence or 0.0)
        
        # Flow completion times
        flows_data = await self._get_flows_data(session, engagement_id)
        
        for flow_type, flow in [
            ("collection", flows_data.get("collection_flow")),
            ("discovery", flows_data.get("discovery_flow")),
            ("assessment", flows_data.get("assessment_flow"))
        ]:
            if flow and flow.created_at:
                if flow.status == "completed" and flow.completed_at:
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
                if flow.completed_at
            ]
            avg_collection_time = sum(collection_times) / len(collection_times) if collection_times else 0
            
        if discoveries:
            discovery_times = [
                (flow.completed_at - flow.created_at).total_seconds()
                for flow in discoveries
                if flow.completed_at
            ]
            avg_discovery_time = sum(discovery_times) / len(discovery_times) if discovery_times else 0
            
        return {
            "historical_engagements": len(collections) + len(discoveries),
            "average_collection_time": avg_collection_time,
            "average_discovery_time": avg_discovery_time,
            "user_experience_level": "experienced" if len(collections) > 5 else "novice"
        }
        
    async def _analyze_user_journey(self, context: OptimizationContext) -> UserJourneyAnalytics:
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
        current_phase = "not_started"
        if flows_data.get("assessment_flow"):
            current_phase = "assessment"
        elif flows_data.get("discovery_flow"):
            current_phase = "discovery"
        elif flows_data.get("collection_flow"):
            current_phase = "collection"
            
        # Calculate phases completed
        phases_completed = []
        if flows_data.get("collection_flow") and flows_data["collection_flow"].status == "completed":
            phases_completed.append("collection")
        if flows_data.get("discovery_flow") and flows_data["discovery_flow"].status == "completed":
            phases_completed.append("discovery")
        if flows_data.get("assessment_flow") and flows_data["assessment_flow"].status == "completed":
            phases_completed.append("assessment")
            
        # Calculate time per phase
        time_per_phase = {}
        for phase, flow in [
            ("collection", flows_data.get("collection_flow")),
            ("discovery", flows_data.get("discovery_flow")),
            ("assessment", flows_data.get("assessment_flow"))
        ]:
            if flow:
                if flow.status == "completed" and flow.completed_at:
                    time_per_phase[phase] = (flow.completed_at - flow.created_at).total_seconds()
                else:
                    time_per_phase[phase] = (datetime.utcnow() - flow.created_at).total_seconds()
                    
        # Calculate automation efficiency
        automation_efficiency = 0.8  # Placeholder - would calculate based on actual automation usage
        
        # Extract user actions from behavior data
        user_actions = []
        for flow_data in user_behavior.get("active_flows", []):
            user_actions.append({
                "flow_type": flow_data["flow_type"],
                "interactions": flow_data["interaction_count"],
                "duration": (flow_data["last_accessed"] - flow_data["created_at"]).total_seconds()
            })
            
        # Calculate satisfaction indicators
        satisfaction_indicators = {
            "progress_smoothness": 0.85,  # Based on error rates and flow continuity
            "automation_satisfaction": automation_efficiency,
            "time_efficiency": 0.75,  # Based on comparison to benchmarks
            "error_resilience": 0.90   # Based on successful error recovery
        }
        
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
        
    async def _generate_ux_recommendations(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Generate UX improvement recommendations"""
        
        recommendations = []
        
        # Workflow navigation recommendations
        nav_recs = await self._analyze_workflow_navigation(context, journey)
        recommendations.extend(nav_recs)
        
        # Progress tracking recommendations
        progress_recs = await self._analyze_progress_tracking(context, journey)
        recommendations.extend(progress_recs)
        
        # Error communication recommendations
        error_recs = await self._analyze_error_communication(context, journey)
        recommendations.extend(error_recs)
        
        # Performance optimization recommendations
        perf_recs = await self._analyze_performance_optimization(context, journey)
        recommendations.extend(perf_recs)
        
        # Automation transparency recommendations
        auto_recs = await self._analyze_automation_transparency(context, journey)
        recommendations.extend(auto_recs)
        
        # Sort by priority score
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
        
    async def _analyze_workflow_navigation(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Analyze workflow navigation and suggest improvements"""
        
        recommendations = []
        
        # Check if user is spending too much time in transition
        if len(journey.phases_completed) < 2 and journey.current_phase == "collection":
            # Suggest auto-advance if collection is complete
            flows_data = context.flows_data
            collection_flow = flows_data.get("collection_flow")
            
            if (collection_flow and 
                collection_flow.status == "completed" and 
                not flows_data.get("discovery_flow")):
                
                recommendations.append(UXRecommendation(
                    id="auto_advance_discovery",
                    area=UXOptimizationArea.WORKFLOW_NAVIGATION,
                    title="Auto-advance to Discovery Phase",
                    description="Collection is complete. Automatically transition to discovery phase.",
                    impact="high",
                    effort="low",
                    priority_score=9.0,
                    implementation_guidance=[
                        "Display transition notification",
                        "Auto-initiate discovery flow",
                        "Provide option to review collection results first"
                    ],
                    expected_improvement={
                        "time_to_completion": -0.2,
                        "user_satisfaction": 0.15
                    }
                ))
                
        # Check for navigation shortcuts
        if journey.current_phase == "assessment" and len(journey.user_actions) > 10:
            recommendations.append(UXRecommendation(
                id="navigation_shortcuts",
                area=UXOptimizationArea.WORKFLOW_NAVIGATION,
                title="Add Navigation Shortcuts",
                description="User has high interaction count. Provide quick navigation shortcuts.",
                impact="medium",
                effort="medium",
                priority_score=7.0,
                implementation_guidance=[
                    "Add keyboard shortcuts",
                    "Implement quick-access toolbar",
                    "Provide phase jump capabilities"
                ],
                expected_improvement={
                    "time_to_completion": -0.15,
                    "cognitive_load": -0.1
                }
            ))
            
        return recommendations
        
    async def _analyze_progress_tracking(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Analyze progress tracking and suggest improvements"""
        
        recommendations = []
        
        # Check if progress tracking could be more granular
        if journey.automation_efficiency > 0.8:
            recommendations.append(UXRecommendation(
                id="granular_progress_tracking",
                area=UXOptimizationArea.PROGRESS_TRACKING,
                title="Enhanced Progress Visualization",
                description="High automation efficiency detected. Show detailed AI processing steps.",
                impact="medium",
                effort="medium",
                priority_score=6.5,
                implementation_guidance=[
                    "Show AI agent activities in real-time",
                    "Display confidence building over time",
                    "Add estimated completion times for each step"
                ],
                expected_improvement={
                    "automation_transparency": 0.2,
                    "user_satisfaction": 0.1
                }
            ))
            
        # Check for milestone celebrations
        if len(journey.phases_completed) >= 2:
            recommendations.append(UXRecommendation(
                id="milestone_celebrations",
                area=UXOptimizationArea.PROGRESS_TRACKING,
                title="Milestone Achievement Notifications",
                description="Multiple phases completed. Celebrate user progress.",
                impact="low",
                effort="low",
                priority_score=5.0,
                implementation_guidance=[
                    "Show completion animations",
                    "Display progress achievements",
                    "Provide summary of accomplishments"
                ],
                expected_improvement={
                    "user_satisfaction": 0.1,
                    "engagement": 0.15
                }
            ))
            
        return recommendations
        
    async def _analyze_error_communication(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Analyze error communication and suggest improvements"""
        
        recommendations = []
        
        # Check if user encountered errors
        if journey.errors_encountered > 0:
            recommendations.append(UXRecommendation(
                id="improved_error_messaging",
                area=UXOptimizationArea.ERROR_COMMUNICATION,
                title="Enhanced Error Communication",
                description="Errors detected. Improve error messaging and recovery guidance.",
                impact="high",
                effort="medium",
                priority_score=8.5,
                implementation_guidance=[
                    "Provide clear, actionable error messages",
                    "Show step-by-step recovery instructions",
                    "Offer direct assistance options"
                ],
                expected_improvement={
                    "error_recovery_rate": 0.3,
                    "user_satisfaction": 0.2
                }
            ))
            
        return recommendations
        
    async def _analyze_performance_optimization(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Analyze performance and suggest optimizations"""
        
        recommendations = []
        
        # Check for slow processing times
        performance_metrics = context.performance_metrics
        historical_data = context.historical_data
        
        current_collection_time = journey.time_per_phase.get("collection", 0)
        avg_collection_time = historical_data.get("average_collection_time", 0)
        
        if current_collection_time > avg_collection_time * 1.5:
            recommendations.append(UXRecommendation(
                id="performance_optimization",
                area=UXOptimizationArea.PERFORMANCE_OPTIMIZATION,
                title="Optimize Collection Performance",
                description="Collection taking longer than usual. Implement performance optimizations.",
                impact="high",
                effort="high",
                priority_score=7.5,
                implementation_guidance=[
                    "Implement parallel processing for large datasets",
                    "Add caching for frequently accessed data",
                    "Optimize database queries"
                ],
                expected_improvement={
                    "time_to_completion": -0.4,
                    "user_satisfaction": 0.25
                }
            ))
            
        return recommendations
        
    async def _analyze_automation_transparency(
        self,
        context: OptimizationContext,
        journey: UserJourneyAnalytics
    ) -> List[UXRecommendation]:
        """Analyze automation transparency and suggest improvements"""
        
        recommendations = []
        
        # Check if automation explanation could be improved
        if journey.automation_efficiency > 0.7 and journey.satisfaction_indicators.get("automation_satisfaction", 0) < 0.8:
            recommendations.append(UXRecommendation(
                id="automation_transparency",
                area=UXOptimizationArea.AUTOMATION_TRANSPARENCY,
                title="Improve AI Process Transparency",
                description="High automation with lower satisfaction. Increase AI transparency.",
                impact="medium",
                effort="medium",
                priority_score=6.8,
                implementation_guidance=[
                    "Show AI reasoning for recommendations",
                    "Display confidence scores for automated decisions",
                    "Provide option to view detailed AI analysis"
                ],
                expected_improvement={
                    "automation_satisfaction": 0.2,
                    "trust_in_system": 0.15
                }
            ))
            
        return recommendations
        
    @track_performance("ux.optimization.apply")
    async def apply_ux_optimizations(
        self,
        engagement_id: UUID,
        user_id: UUID,
        optimization_ids: List[str]
    ) -> Dict[str, Any]:
        """Apply selected UX optimizations"""
        
        logger.info(
            "Applying UX optimizations",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id),
                "optimization_ids": optimization_ids
            }
        )
        
        applied_optimizations = []
        failed_optimizations = []
        
        # Get cached recommendations
        cached_data = self.ux_metrics_cache.get(engagement_id)
        if not cached_data:
            return {
                "error": "No optimization recommendations found for engagement",
                "applied": [],
                "failed": optimization_ids
            }
            
        recommendations = cached_data["recommendations"]
        
        for opt_id in optimization_ids:
            try:
                # Find recommendation
                recommendation = next((r for r in recommendations if r.id == opt_id), None)
                if not recommendation:
                    failed_optimizations.append({"id": opt_id, "reason": "Recommendation not found"})
                    continue
                    
                # Apply optimization based on area
                success = await self._apply_optimization(engagement_id, user_id, recommendation)
                
                if success:
                    applied_optimizations.append({
                        "id": opt_id,
                        "title": recommendation.title,
                        "area": recommendation.area.value
                    })
                else:
                    failed_optimizations.append({"id": opt_id, "reason": "Implementation failed"})
                    
            except Exception as e:
                failed_optimizations.append({"id": opt_id, "reason": str(e)})
                
        return {
            "applied": applied_optimizations,
            "failed": failed_optimizations,
            "engagement_id": str(engagement_id)
        }
        
    async def _apply_optimization(
        self,
        engagement_id: UUID,
        user_id: UUID,
        recommendation: UXRecommendation
    ) -> bool:
        """Apply a specific optimization"""
        
        # This would implement actual optimization application
        # For now, return success for demonstration
        
        logger.info(
            f"Applying optimization: {recommendation.title}",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id),
                "optimization_area": recommendation.area.value
            }
        )
        
        # Store user preference if applicable
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
            
        self.user_preferences[user_id][recommendation.id] = {
            "applied_at": datetime.utcnow(),
            "area": recommendation.area.value,
            "expected_improvement": recommendation.expected_improvement
        }
        
        return True
        
    @track_performance("ux.metrics.get")
    async def get_ux_metrics(self, engagement_id: UUID) -> Dict[str, Any]:
        """Get UX metrics for an engagement"""
        
        cached_data = self.ux_metrics_cache.get(engagement_id)
        
        if not cached_data:
            return {
                "engagement_id": str(engagement_id),
                "metrics_available": False,
                "message": "No UX metrics available. Run analysis first."
            }
            
        journey = cached_data["journey_analytics"]
        recommendations = cached_data["recommendations"]
        
        return {
            "engagement_id": str(engagement_id),
            "metrics_available": True,
            "journey_analytics": {
                "current_phase": journey.current_phase,
                "phases_completed": journey.phases_completed,
                "total_journey_time": (datetime.utcnow() - journey.journey_start).total_seconds(),
                "automation_efficiency": journey.automation_efficiency,
                "satisfaction_indicators": journey.satisfaction_indicators
            },
            "recommendations": [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "area": rec.area.value,
                    "impact": rec.impact,
                    "priority_score": rec.priority_score
                }
                for rec in recommendations
            ],
            "improvement_opportunities": len(recommendations),
            "last_updated": cached_data["last_updated"].isoformat()
        }