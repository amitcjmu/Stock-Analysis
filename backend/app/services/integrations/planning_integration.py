"""
Planning Flow Integration Service for Assessment Flow.
Handles integration points with Planning Flow for 6R decision handoff and re-assessment support.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlowState
from app.models.asset import Asset

logger = logging.getLogger(__name__)


class PlanningFlowIntegration:
    """Integration service for Planning Flow handoff and coordination."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def export_assessment_results(
        self,
        db: AsyncSession,
        flow_id: str,
        client_account_id: int
    ) -> Dict[str, Any]:
        """
        Export assessment results for Planning Flow consumption.
        
        Args:
            db: Database session
            flow_id: Assessment flow ID
            client_account_id: Client account ID for multi-tenant filtering
            
        Returns:
            Complete assessment export package for Planning Flow
        """
        try:
            # Get assessment flow state
            from app.repositories.assessment_flow_repository import AssessmentFlowRepository
            repository = AssessmentFlowRepository(db, client_account_id)
            flow_state = await repository.get_assessment_flow_state(flow_id)
            
            if not flow_state:
                raise ValueError(f"Assessment flow {flow_id} not found")
            
            if not flow_state.is_completed:
                raise ValueError(f"Assessment flow {flow_id} is not completed")
            
            # Build export package
            export_package = {
                "export_metadata": {
                    "flow_id": flow_id,
                    "engagement_id": flow_state.engagement_id,
                    "exported_at": datetime.utcnow().isoformat(),
                    "export_version": "1.0",
                    "applications_count": len(flow_state.selected_application_ids),
                    "readiness_score": self._calculate_export_readiness_score(flow_state)
                },
                "assessment_summary": {
                    "status": flow_state.status.value,
                    "progress": flow_state.progress,
                    "phases_completed": list(flow_state.phase_results.keys()) if flow_state.phase_results else [],
                    "architecture_captured": flow_state.architecture_captured,
                    "finalized_at": flow_state.finalized_at.isoformat() if flow_state.finalized_at else None
                },
                "architecture_standards": {
                    "engagement_standards": flow_state.engagement_standards or {},
                    "application_overrides": flow_state.application_overrides or {},
                    "compliance_requirements": await self._extract_compliance_requirements(db, flow_state)
                },
                "applications": await self._export_application_assessments(db, flow_state),
                "move_groups": await self._generate_move_group_hints(db, flow_state),
                "planning_recommendations": await self._generate_planning_recommendations(db, flow_state),
                "risk_assessments": await self._export_risk_assessments(db, flow_state),
                "cost_estimates": await self._export_cost_estimates(db, flow_state)
            }
            
            self.logger.info(f"Exported assessment results for flow {flow_id} to Planning Flow")
            return export_package
            
        except Exception as e:
            self.logger.error(f"Failed to export assessment results: {str(e)}")
            raise
    
    async def handle_reassessment_request(
        self,
        db: AsyncSession,
        application_ids: List[str],
        planning_context: Dict[str, Any],
        client_account_id: int,
        requested_by: str
    ) -> Dict[str, Any]:
        """
        Handle re-assessment request from Planning Flow.
        
        Args:
            db: Database session
            application_ids: List of application IDs requiring re-assessment
            planning_context: Context from Planning Flow about why re-assessment is needed
            client_account_id: Client account ID for multi-tenant filtering
            requested_by: User who requested re-assessment
            
        Returns:
            Re-assessment initiation response
        """
        try:
            # Validate applications exist and are accessible
            stmt = select(Asset).where(
                and_(
                    Asset.id.in_(application_ids),
                    Asset.client_account_id == client_account_id
                )
            )
            result = await db.execute(stmt)
            assets = result.scalars().all()
            
            if len(assets) != len(application_ids):
                found_ids = {str(asset.id) for asset in assets}
                missing_ids = set(application_ids) - found_ids
                raise ValueError(f"Applications not found: {', '.join(missing_ids)}")
            
            # Create re-assessment request record
            reassessment_request = {
                "request_id": f"reassess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "application_ids": application_ids,
                "planning_context": planning_context,
                "requested_by": requested_by,
                "requested_at": datetime.utcnow().isoformat(),
                "status": "pending",
                "reassessment_scope": self._determine_reassessment_scope(planning_context),
                "priority": planning_context.get("priority", "medium")
            }
            
            # Update assets to mark them for re-assessment
            for asset in assets:
                await self._mark_asset_for_reassessment(db, asset, reassessment_request)
            
            # Generate recommendations for re-assessment approach
            recommendations = await self._generate_reassessment_recommendations(
                db, assets, planning_context
            )
            
            response = {
                "reassessment_request": reassessment_request,
                "affected_applications": [
                    {
                        "id": str(asset.id),
                        "name": asset.name,
                        "current_assessment_status": asset.assessment_status,
                        "current_sixr_decision": self._get_current_sixr_decision(asset),
                        "reassessment_required": True
                    }
                    for asset in assets
                ],
                "recommendations": recommendations,
                "estimated_effort": self._estimate_reassessment_effort(assets, planning_context),
                "next_steps": [
                    "Review reassessment scope and recommendations",
                    "Initialize new assessment flow for affected applications",
                    "Coordinate with Planning Flow on timeline requirements"
                ]
            }
            
            self.logger.info(f"Created re-assessment request for {len(application_ids)} applications")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to handle reassessment request: {str(e)}")
            raise
    
    async def create_planning_flow_handoff(
        self,
        db: AsyncSession,
        assessment_flow_id: str,
        client_account_id: int,
        handoff_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create handoff package for Planning Flow initialization.
        
        Args:
            db: Database session
            assessment_flow_id: Assessment flow ID to hand off
            client_account_id: Client account ID for multi-tenant filtering
            handoff_options: Optional handoff configuration
            
        Returns:
            Planning Flow initialization package
        """
        try:
            # Export assessment results
            export_package = await self.export_assessment_results(
                db, assessment_flow_id, client_account_id
            )
            
            # Create Planning Flow handoff package
            handoff_package = {
                "handoff_metadata": {
                    "source_flow_type": "assessment",
                    "source_flow_id": assessment_flow_id,
                    "handoff_created_at": datetime.utcnow().isoformat(),
                    "handoff_version": "1.0",
                    "planning_flow_required": True
                },
                "initialization_data": {
                    "engagement_id": export_package["export_metadata"]["engagement_id"],
                    "applications": export_package["applications"],
                    "architecture_standards": export_package["architecture_standards"],
                    "move_group_hints": export_package["move_groups"],
                    "risk_constraints": export_package["risk_assessments"],
                    "cost_targets": export_package["cost_estimates"]
                },
                "planning_preferences": handoff_options or {},
                "validation_requirements": {
                    "applications_validated": True,
                    "sixr_decisions_complete": True,
                    "architecture_standards_applied": export_package["assessment_summary"]["architecture_captured"],
                    "risk_assessments_complete": True
                }
            }
            
            self.logger.info(f"Created Planning Flow handoff package for assessment {assessment_flow_id}")
            return handoff_package
            
        except Exception as e:
            self.logger.error(f"Failed to create Planning Flow handoff: {str(e)}")
            raise
    
    async def sync_planning_feedback(
        self,
        db: AsyncSession,
        assessment_flow_id: str,
        planning_feedback: Dict[str, Any],
        client_account_id: int
    ) -> bool:
        """
        Synchronize feedback from Planning Flow back to Assessment.
        
        Args:
            db: Database session
            assessment_flow_id: Assessment flow ID
            planning_feedback: Feedback from Planning Flow
            client_account_id: Client account ID for multi-tenant filtering
            
        Returns:
            True if sync successful
        """
        try:
            # Get assessment flow state
            from app.repositories.assessment_flow_repository import AssessmentFlowRepository
            repository = AssessmentFlowRepository(db, client_account_id)
            flow_state = await repository.get_assessment_flow_state(assessment_flow_id)
            
            if not flow_state:
                raise ValueError(f"Assessment flow {assessment_flow_id} not found")
            
            # Process planning feedback
            feedback_processed = {
                "planning_flow_id": planning_feedback.get("planning_flow_id"),
                "feedback_received_at": datetime.utcnow().isoformat(),
                "feedback_type": planning_feedback.get("feedback_type", "general"),
                "application_updates": {},
                "recommendations_accepted": planning_feedback.get("recommendations_accepted", []),
                "recommendations_rejected": planning_feedback.get("recommendations_rejected", []),
                "planning_constraints": planning_feedback.get("constraints", {})
            }
            
            # Update applications based on planning feedback
            if "application_updates" in planning_feedback:
                for app_id, updates in planning_feedback["application_updates"].items():
                    await self._apply_planning_feedback_to_application(
                        db, app_id, updates, client_account_id
                    )
                    feedback_processed["application_updates"][app_id] = updates
            
            # Store feedback in assessment flow
            if not flow_state.phase_results:
                flow_state.phase_results = {}
            
            flow_state.phase_results["planning_feedback"] = feedback_processed
            await db.commit()
            
            self.logger.info(f"Synchronized planning feedback for assessment flow {assessment_flow_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to sync planning feedback: {str(e)}")
            raise
    
    # Private helper methods
    
    def _calculate_export_readiness_score(self, flow_state: AssessmentFlowState) -> float:
        """Calculate overall readiness score for export."""
        score = 0.0
        
        # Base score from completion
        if flow_state.status.value == "completed":
            score += 40.0
        
        # Architecture standards captured
        if flow_state.architecture_captured:
            score += 20.0
        
        # Phase completion
        if flow_state.phase_results:
            completed_phases = len(flow_state.phase_results)
            score += (completed_phases / 5) * 30.0  # 5 phases expected
        
        # Applications ready for planning
        if flow_state.apps_ready_for_planning:
            ready_ratio = len(flow_state.apps_ready_for_planning) / len(flow_state.selected_application_ids)
            score += ready_ratio * 10.0
        
        return min(100.0, score)
    
    async def _extract_compliance_requirements(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> Dict[str, Any]:
        """Extract compliance requirements from assessment."""
        # Query assets for compliance data
        stmt = select(Asset).where(
            and_(
                Asset.id.in_(flow_state.selected_application_ids),
                Asset.client_account_id == flow_state.client_account_id
            )
        )
        result = await db.execute(stmt)
        assets = result.scalars().all()
        
        compliance_requirements = {}
        for asset in assets:
            if asset.compliance_requirements:
                compliance_requirements[str(asset.id)] = asset.compliance_requirements
        
        return compliance_requirements
    
    async def _export_application_assessments(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> List[Dict[str, Any]]:
        """Export detailed application assessment data."""
        applications = []
        
        for app_id in flow_state.selected_application_ids:
            app_assessment = {
                "application_id": app_id,
                "components": flow_state.get_application_components(app_id),
                "tech_debt_analysis": flow_state.get_tech_debt_analysis(app_id),
                "sixr_decision": flow_state.get_sixr_decision(app_id),
                "app_on_page_data": flow_state.app_on_page_data.get(app_id) if flow_state.app_on_page_data else None,
                "assessment_confidence": self._calculate_assessment_confidence(flow_state, app_id),
                "planning_ready": app_id in (flow_state.apps_ready_for_planning or [])
            }
            applications.append(app_assessment)
        
        return applications
    
    async def _generate_move_group_hints(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> List[Dict[str, Any]]:
        """Generate move group hints for Planning Flow."""
        move_groups = []
        
        # Group applications by 6R strategy
        strategy_groups = {}
        for app_id in flow_state.selected_application_ids:
            sixr_decision = flow_state.get_sixr_decision(app_id)
            if sixr_decision and "decisions" in sixr_decision:
                for decision in sixr_decision["decisions"]:
                    strategy = decision.get("recommended_strategy", "unknown")
                    if strategy not in strategy_groups:
                        strategy_groups[strategy] = []
                    strategy_groups[strategy].append(app_id)
        
        # Create move group hints
        for strategy, app_ids in strategy_groups.items():
            if len(app_ids) > 1:  # Only suggest groups with multiple apps
                move_group = {
                    "suggested_group_name": f"{strategy.title()} Migration Group",
                    "strategy": strategy,
                    "application_ids": app_ids,
                    "rationale": f"Applications using {strategy} strategy can be migrated together",
                    "estimated_duration": len(app_ids) * 2,  # weeks
                    "risk_level": "medium"
                }
                move_groups.append(move_group)
        
        return move_groups
    
    async def _generate_planning_recommendations(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> List[Dict[str, Any]]:
        """Generate planning recommendations based on assessment."""
        recommendations = []
        
        # Analyze tech debt patterns
        high_debt_apps = []
        for app_id in flow_state.selected_application_ids:
            tech_debt = flow_state.get_tech_debt_analysis(app_id)
            if tech_debt and tech_debt.get("analysis", {}).get("overall_debt_score", 0) > 70:
                high_debt_apps.append(app_id)
        
        if high_debt_apps:
            recommendations.append({
                "type": "tech_debt_remediation",
                "priority": "high",
                "description": "Address high technical debt before migration",
                "affected_applications": high_debt_apps,
                "estimated_effort": len(high_debt_apps) * 4  # weeks
            })
        
        # Add more recommendation logic as needed
        
        return recommendations
    
    async def _export_risk_assessments(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> Dict[str, Any]:
        """Export risk assessment data."""
        risk_assessments = {
            "overall_risk_level": "medium",
            "application_risks": {},
            "migration_risks": [],
            "mitigation_strategies": []
        }
        
        # Analyze risks per application
        for app_id in flow_state.selected_application_ids:
            sixr_decision = flow_state.get_sixr_decision(app_id)
            if sixr_decision and "decisions" in sixr_decision:
                app_risks = []
                for decision in sixr_decision["decisions"]:
                    risk_level = decision.get("risk_level", "medium")
                    app_risks.append({
                        "risk_level": risk_level,
                        "dependencies": decision.get("dependencies", []),
                        "estimated_effort": decision.get("estimated_effort")
                    })
                risk_assessments["application_risks"][app_id] = app_risks
        
        return risk_assessments
    
    async def _export_cost_estimates(
        self, 
        db: AsyncSession, 
        flow_state: AssessmentFlowState
    ) -> Dict[str, Any]:
        """Export cost estimate data."""
        cost_estimates = {
            "total_estimated_cost": 0.0,
            "application_costs": {},
            "cost_breakdown": {
                "migration_effort": 0.0,
                "infrastructure": 0.0,
                "training": 0.0,
                "contingency": 0.0
            }
        }
        
        # Calculate costs per application
        for app_id in flow_state.selected_application_ids:
            sixr_decision = flow_state.get_sixr_decision(app_id)
            if sixr_decision and "decisions" in sixr_decision:
                app_cost = 0.0
                for decision in sixr_decision["decisions"]:
                    estimated_cost = decision.get("estimated_cost", 0)
                    if estimated_cost:
                        app_cost += estimated_cost
                
                cost_estimates["application_costs"][app_id] = app_cost
                cost_estimates["total_estimated_cost"] += app_cost
        
        return cost_estimates
    
    def _calculate_assessment_confidence(self, flow_state: AssessmentFlowState, app_id: str) -> float:
        """Calculate confidence score for application assessment."""
        confidence_factors = []
        
        # Component analysis confidence
        components = flow_state.get_application_components(app_id)
        if components and components.get("user_verified"):
            confidence_factors.append(0.9)
        elif components:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.3)
        
        # Tech debt analysis confidence
        tech_debt = flow_state.get_tech_debt_analysis(app_id)
        if tech_debt and tech_debt.get("analysis", {}).get("analysis_confidence"):
            confidence_factors.append(tech_debt["analysis"]["analysis_confidence"])
        
        # 6R decision confidence
        sixr_decision = flow_state.get_sixr_decision(app_id)
        if sixr_decision and "decisions" in sixr_decision:
            decision_confidences = [
                decision.get("confidence_score", 0.5) 
                for decision in sixr_decision["decisions"]
            ]
            if decision_confidences:
                confidence_factors.append(sum(decision_confidences) / len(decision_confidences))
        
        # Calculate average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5  # Default moderate confidence
    
    def _determine_reassessment_scope(self, planning_context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine scope of re-assessment based on planning context."""
        scope = {
            "full_reassessment": False,
            "components_review": False,
            "sixr_reconsideration": False,
            "tech_debt_reanalysis": False,
            "architecture_standards_review": False
        }
        
        reason = planning_context.get("reason", "")
        
        if "component" in reason.lower():
            scope["components_review"] = True
        if "strategy" in reason.lower() or "6r" in reason.lower():
            scope["sixr_reconsideration"] = True
        if "debt" in reason.lower():
            scope["tech_debt_reanalysis"] = True
        if "architecture" in reason.lower() or "standard" in reason.lower():
            scope["architecture_standards_review"] = True
        
        # If no specific scope identified, do full re-assessment
        if not any(scope.values()):
            scope["full_reassessment"] = True
        
        return scope
    
    async def _mark_asset_for_reassessment(
        self, 
        db: AsyncSession, 
        asset: Asset, 
        reassessment_request: Dict[str, Any]
    ):
        """Mark an asset for re-assessment."""
        # Update asset assessment status
        asset.assessment_status = "reassessment_required"
        asset.reassessment_context = reassessment_request
        await db.commit()
    
    def _get_current_sixr_decision(self, asset: Asset) -> Dict[str, Any]:
        """Get current 6R decision for an asset."""
        if asset.assessment_results and "sixr_decision" in asset.assessment_results:
            return asset.assessment_results["sixr_decision"]
        return {}
    
    async def _generate_reassessment_recommendations(
        self, 
        db: AsyncSession, 
        assets: List[Asset], 
        planning_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for re-assessment approach."""
        recommendations = []
        
        # Analyze why re-assessment is needed
        reason = planning_context.get("reason", "")
        
        if "dependency" in reason.lower():
            recommendations.append({
                "type": "dependency_analysis",
                "description": "Focus on dependency analysis and impact assessment",
                "estimated_effort": "medium"
            })
        
        if "cost" in reason.lower():
            recommendations.append({
                "type": "cost_reanalysis",
                "description": "Re-evaluate cost estimates and 6R strategy economics",
                "estimated_effort": "low"
            })
        
        return recommendations
    
    def _estimate_reassessment_effort(
        self, 
        assets: List[Asset], 
        planning_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate effort required for re-assessment."""
        base_effort_per_app = 4  # hours
        total_hours = len(assets) * base_effort_per_app
        
        # Adjust based on reassessment scope
        scope_multipliers = {
            "full": 1.0,
            "partial": 0.6,
            "focused": 0.3
        }
        
        scope = planning_context.get("scope", "partial")
        multiplier = scope_multipliers.get(scope, 0.6)
        
        return {
            "estimated_hours": int(total_hours * multiplier),
            "estimated_days": int((total_hours * multiplier) / 8),
            "complexity": "medium" if len(assets) > 5 else "low",
            "recommended_approach": "incremental" if len(assets) > 10 else "batch"
        }
    
    async def _apply_planning_feedback_to_application(
        self, 
        db: AsyncSession, 
        app_id: str, 
        updates: Dict[str, Any], 
        client_account_id: int
    ):
        """Apply planning feedback updates to an application."""
        stmt = select(Asset).where(
            and_(
                Asset.id == app_id,
                Asset.client_account_id == client_account_id
            )
        )
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()
        
        if asset:
            # Update asset with planning feedback
            if "planning_notes" in updates:
                asset.planning_notes = updates["planning_notes"]
            
            if "planning_priority" in updates:
                asset.planning_priority = updates["planning_priority"]
            
            await db.commit()