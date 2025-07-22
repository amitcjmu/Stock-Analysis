"""
Summary manager for discovery flow reporting and analytics.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow

from .asset_manager import AssetManager

logger = logging.getLogger(__name__)


class SummaryManager:
    """Manager for discovery flow summary generation and analytics."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.asset_manager = AssetManager(db, context)
    
    async def get_flow_summary(self, flow: DiscoveryFlow) -> Dict[str, Any]:
        """Get a comprehensive summary of the discovery flow"""
        try:
            logger.info(f"📊 Generating flow summary for: {flow.flow_id}")
            
            await self.asset_manager.get_flow_assets(flow.flow_id, flow.id)
            
            # Generate asset statistics
            asset_statistics = await self.asset_manager.get_asset_summary_statistics(flow.flow_id, flow.id)
            
            # Phase completion status
            phase_completion = self._get_phase_completion_status(flow)
            completed_phases = sum(1 for completed in phase_completion.values() if completed)
            
            # Flow progress analysis
            progress_analysis = self._analyze_flow_progress(flow, asset_statistics)
            
            # Quality assessment
            quality_assessment = self._assess_flow_quality(flow, asset_statistics)
            
            summary = {
                "flow_info": {
                    "flow_id": flow.flow_id,
                    "status": flow.status,
                    "current_phase": flow.get_next_phase(),
                    "progress_percentage": flow.progress_percentage,
                    "assessment_ready": flow.assessment_ready
                },
                "phase_completion": {
                    "status": phase_completion,
                    "completed_phases": completed_phases,
                    "total_phases": 6,
                    "completion_percentage": round((completed_phases / 6) * 100, 1)
                },
                "assets": asset_statistics,
                "progress_analysis": progress_analysis,
                "quality_assessment": quality_assessment,
                "timestamps": {
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "completed_at": flow.completed_at.isoformat() if flow.completed_at else None
                },
                "crewai_integration": {
                    "state_data_available": bool(flow.crewai_state_data),
                    "last_sync": flow.updated_at.isoformat() if flow.updated_at else None
                }
            }
            
            logger.info(f"✅ Flow summary generated: {flow.flow_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate flow summary for {flow.flow_id}: {e}")
            raise
    
    async def get_multi_flow_summary(self, flows: List[DiscoveryFlow]) -> Dict[str, Any]:
        """Get summary statistics across multiple discovery flows"""
        try:
            logger.info(f"📊 Generating multi-flow summary for {len(flows)} flows")
            
            if not flows:
                return self._create_empty_multi_flow_summary()
            
            # Aggregate statistics
            total_assets = 0
            total_flows = len(flows)
            status_distribution = {}
            phase_completion_stats = {}
            quality_aggregates = {"total_quality": 0.0, "total_confidence": 0.0, "asset_count": 0}
            
            for flow in flows:
                # Flow status distribution
                status_distribution[flow.status] = status_distribution.get(flow.status, 0) + 1
                
                # Phase completion aggregation
                phase_completion = self._get_phase_completion_status(flow)
                for phase, completed in phase_completion.items():
                    if phase not in phase_completion_stats:
                        phase_completion_stats[phase] = {"completed": 0, "total": 0}
                    phase_completion_stats[phase]["total"] += 1
                    if completed:
                        phase_completion_stats[phase]["completed"] += 1
                
                # Asset and quality aggregation
                try:
                    assets = await self.asset_manager.get_flow_assets(flow.flow_id, flow.id)
                    total_assets += len(assets)
                    
                    for asset in assets:
                        quality_aggregates["asset_count"] += 1
                        quality_aggregates["total_quality"] += asset.quality_score or 0.0
                        quality_aggregates["total_confidence"] += asset.confidence_score or 0.0
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get assets for flow {flow.flow_id}: {e}")
                    continue
            
            # Calculate averages
            avg_quality = (quality_aggregates["total_quality"] / quality_aggregates["asset_count"] 
                          if quality_aggregates["asset_count"] > 0 else 0.0)
            avg_confidence = (quality_aggregates["total_confidence"] / quality_aggregates["asset_count"] 
                             if quality_aggregates["asset_count"] > 0 else 0.0)
            
            # Phase completion percentages
            phase_completion_percentages = {}
            for phase, stats in phase_completion_stats.items():
                phase_completion_percentages[phase] = round(
                    (stats["completed"] / stats["total"]) * 100, 1
                ) if stats["total"] > 0 else 0.0
            
            summary = {
                "overview": {
                    "total_flows": total_flows,
                    "total_assets": total_assets,
                    "avg_assets_per_flow": round(total_assets / total_flows, 1) if total_flows > 0 else 0
                },
                "flow_status_distribution": status_distribution,
                "phase_completion": {
                    "statistics": phase_completion_stats,
                    "completion_percentages": phase_completion_percentages
                },
                "quality_metrics": {
                    "average_quality_score": round(avg_quality, 3),
                    "average_confidence_score": round(avg_confidence, 3),
                    "total_assessed_assets": quality_aggregates["asset_count"]
                },
                "performance_indicators": self._calculate_performance_indicators(flows, phase_completion_percentages)
            }
            
            logger.info(f"✅ Multi-flow summary generated for {total_flows} flows")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate multi-flow summary: {e}")
            raise
    
    async def get_flow_health_report(self, flow: DiscoveryFlow) -> Dict[str, Any]:
        """Generate a health report for a discovery flow"""
        try:
            logger.info(f"🏥 Generating health report for flow: {flow.flow_id}")
            
            assets = await self.asset_manager.get_flow_assets(flow.flow_id, flow.id)
            asset_stats = await self.asset_manager.get_asset_summary_statistics(flow.flow_id, flow.id)
            
            # Health indicators
            health_indicators = []
            overall_health = "healthy"
            
            # Phase completion health
            phase_completion = self._get_phase_completion_status(flow)
            completed_phases = sum(1 for completed in phase_completion.values() if completed)
            
            if completed_phases < 3:
                health_indicators.append({
                    "indicator": "Low Phase Completion",
                    "severity": "medium",
                    "message": f"Only {completed_phases}/6 phases completed",
                    "recommendation": "Focus on completing remaining discovery phases"
                })
                overall_health = "warning"
            
            # Asset quality health
            if asset_stats["avg_quality_score"] < 0.6:
                health_indicators.append({
                    "indicator": "Low Asset Quality",
                    "severity": "high",
                    "message": f"Average quality score: {asset_stats['avg_quality_score']:.2f}",
                    "recommendation": "Review and improve asset data quality"
                })
                overall_health = "critical"
            
            # Asset confidence health
            if asset_stats["avg_confidence_score"] < 0.7:
                health_indicators.append({
                    "indicator": "Low Asset Confidence",
                    "severity": "medium",
                    "message": f"Average confidence score: {asset_stats['avg_confidence_score']:.2f}",
                    "recommendation": "Validate and improve asset discovery accuracy"
                })
                if overall_health == "healthy":
                    overall_health = "warning"
            
            # Validation status health
            unvalidated_count = asset_stats["quality_metrics"]["unvalidated_assets"]
            if unvalidated_count > len(assets) * 0.3:  # More than 30% unvalidated
                health_indicators.append({
                    "indicator": "High Unvalidated Assets",
                    "severity": "medium",
                    "message": f"{unvalidated_count} assets pending validation",
                    "recommendation": "Complete asset validation process"
                })
                if overall_health == "healthy":
                    overall_health = "warning"
            
            # Progress stagnation health
            if flow.progress_percentage and flow.progress_percentage < 50:
                health_indicators.append({
                    "indicator": "Low Progress",
                    "severity": "low",
                    "message": f"Flow progress: {flow.progress_percentage}%",
                    "recommendation": "Continue with discovery phases to increase progress"
                })
            
            health_report = {
                "flow_id": flow.flow_id,
                "overall_health": overall_health,
                "health_score": self._calculate_health_score(flow, asset_stats),
                "health_indicators": health_indicators,
                "recommendations": [indicator["recommendation"] for indicator in health_indicators],
                "metrics": {
                    "phase_completion_rate": round((completed_phases / 6) * 100, 1),
                    "asset_quality_rate": round(asset_stats["avg_quality_score"] * 100, 1),
                    "asset_confidence_rate": round(asset_stats["avg_confidence_score"] * 100, 1),
                    "validation_completion_rate": round(
                        ((len(assets) - unvalidated_count) / len(assets)) * 100, 1
                    ) if len(assets) > 0 else 0
                },
                "generated_at": logger.info.__self__.time() if hasattr(logger.info.__self__, 'time') else "unknown"
            }
            
            logger.info(f"✅ Health report generated for flow: {flow.flow_id} - Status: {overall_health}")
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate health report for {flow.flow_id}: {e}")
            raise
    
    def _get_phase_completion_status(self, flow: DiscoveryFlow) -> Dict[str, bool]:
        """Get phase completion status for a flow"""
        return {
            "data_import": flow.data_import_completed,
            "attribute_mapping": flow.attribute_mapping_completed,
            "data_cleansing": flow.data_cleansing_completed,
            "inventory": flow.inventory_completed,
            "dependencies": flow.dependencies_completed,
            "tech_debt": flow.tech_debt_completed
        }
    
    def _analyze_flow_progress(self, flow: DiscoveryFlow, asset_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze flow progress and identify bottlenecks"""
        
        phase_completion = self._get_phase_completion_status(flow)
        completed_phases = sum(1 for completed in phase_completion.values() if completed)
        
        # Identify next steps
        next_steps = []
        if not phase_completion["data_import"]:
            next_steps.append("Complete data import phase")
        elif not phase_completion["attribute_mapping"]:
            next_steps.append("Complete attribute mapping phase")
        elif not phase_completion["data_cleansing"]:
            next_steps.append("Complete data cleansing phase")
        elif not phase_completion["inventory"]:
            next_steps.append("Complete inventory phase")
        elif not phase_completion["dependencies"]:
            next_steps.append("Complete dependency analysis phase")
        elif not phase_completion["tech_debt"]:
            next_steps.append("Complete technical debt assessment phase")
        else:
            next_steps.append("Ready for assessment handoff")
        
        # Identify potential blockers
        blockers = []
        if asset_stats["total_count"] == 0 and completed_phases > 2:
            blockers.append("No assets discovered despite phase progress")
        
        if asset_stats["quality_metrics"]["unvalidated_assets"] > asset_stats["total_count"] * 0.5:
            blockers.append("High number of unvalidated assets")
        
        return {
            "completion_rate": round((completed_phases / 6) * 100, 1),
            "current_phase": flow.get_next_phase(),
            "next_steps": next_steps,
            "potential_blockers": blockers,
            "estimated_completion": self._estimate_completion_time(flow, completed_phases)
        }
    
    def _assess_flow_quality(self, flow: DiscoveryFlow, asset_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall flow quality"""
        
        quality_factors = {
            "data_completeness": min(1.0, asset_stats["total_count"] / 10),  # Assuming 10+ assets is good
            "asset_quality": asset_stats["avg_quality_score"],
            "asset_confidence": asset_stats["avg_confidence_score"],
            "validation_rate": 1.0 - (asset_stats["quality_metrics"]["unvalidated_assets"] / max(1, asset_stats["total_count"]))
        }
        
        # Calculate weighted quality score
        weights = {"data_completeness": 0.2, "asset_quality": 0.3, "asset_confidence": 0.3, "validation_rate": 0.2}
        overall_quality = sum(score * weights[factor] for factor, score in quality_factors.items())
        
        quality_level = "excellent" if overall_quality >= 0.9 else (
            "good" if overall_quality >= 0.7 else (
                "fair" if overall_quality >= 0.5 else "poor"
            )
        )
        
        return {
            "overall_quality_score": round(overall_quality, 3),
            "quality_level": quality_level,
            "quality_factors": quality_factors,
            "improvement_areas": self._identify_improvement_areas(quality_factors)
        }
    
    def _calculate_health_score(self, flow: DiscoveryFlow, asset_stats: Dict[str, Any]) -> float:
        """Calculate a numerical health score for the flow"""
        
        phase_completion = self._get_phase_completion_status(flow)
        completed_phases = sum(1 for completed in phase_completion.values() if completed)
        
        # Health factors (0-1 scale)
        factors = {
            "phase_completion": completed_phases / 6,
            "asset_quality": asset_stats["avg_quality_score"],
            "asset_confidence": asset_stats["avg_confidence_score"],
            "progress": (flow.progress_percentage or 0) / 100
        }
        
        # Weighted health score
        weights = {"phase_completion": 0.3, "asset_quality": 0.25, "asset_confidence": 0.25, "progress": 0.2}
        health_score = sum(score * weights[factor] for factor, score in factors.items())
        
        return round(health_score, 3)
    
    def _calculate_performance_indicators(self, flows: List[DiscoveryFlow], phase_percentages: Dict[str, float]) -> Dict[str, Any]:
        """Calculate performance indicators across flows"""
        
        active_flows = [f for f in flows if f.status == "active"]
        completed_flows = [f for f in flows if f.status == "completed"]
        
        return {
            "completion_rate": round((len(completed_flows) / len(flows)) * 100, 1) if flows else 0,
            "average_phase_completion": round(sum(phase_percentages.values()) / len(phase_percentages), 1) if phase_percentages else 0,
            "active_flows_ratio": round((len(active_flows) / len(flows)) * 100, 1) if flows else 0,
            "flow_efficiency": "high" if len(completed_flows) > len(active_flows) else "medium"
        }
    
    def _identify_improvement_areas(self, quality_factors: Dict[str, float]) -> List[str]:
        """Identify areas for quality improvement"""
        
        improvement_areas = []
        
        for factor, score in quality_factors.items():
            if score < 0.7:
                if factor == "data_completeness":
                    improvement_areas.append("Increase asset discovery coverage")
                elif factor == "asset_quality":
                    improvement_areas.append("Improve asset data quality")
                elif factor == "asset_confidence":
                    improvement_areas.append("Enhance discovery accuracy")
                elif factor == "validation_rate":
                    improvement_areas.append("Complete asset validation process")
        
        return improvement_areas
    
    def _estimate_completion_time(self, flow: DiscoveryFlow, completed_phases: int) -> str:
        """Estimate time to completion based on current progress"""
        
        remaining_phases = 6 - completed_phases
        
        if remaining_phases == 0:
            return "Flow ready for completion"
        elif remaining_phases <= 2:
            return "1-2 days"
        elif remaining_phases <= 4:
            return "3-5 days"
        else:
            return "1-2 weeks"
    
    def _create_empty_multi_flow_summary(self) -> Dict[str, Any]:
        """Create empty multi-flow summary when no flows exist"""
        return {
            "overview": {
                "total_flows": 0,
                "total_assets": 0,
                "avg_assets_per_flow": 0
            },
            "flow_status_distribution": {},
            "phase_completion": {
                "statistics": {},
                "completion_percentages": {}
            },
            "quality_metrics": {
                "average_quality_score": 0.0,
                "average_confidence_score": 0.0,
                "total_assessed_assets": 0
            },
            "performance_indicators": {
                "completion_rate": 0.0,
                "average_phase_completion": 0.0,
                "active_flows_ratio": 0.0,
                "flow_efficiency": "unknown"
            }
        }