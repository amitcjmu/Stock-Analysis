"""
Flow coordinator for orchestrating assessment flow operations.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from .assessment_manager import AssessmentManager
from ..repositories.assessment_repository import AssessmentRepository

logger = logging.getLogger(__name__)


class FlowCoordinator:
    """Coordinates assessment flow operations and orchestrates between components."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.assessment_manager = AssessmentManager(db, context)
        self.repository = AssessmentRepository(db, context)
    
    async def orchestrate_flow_completion(
        self,
        discovery_flow_id: uuid.UUID,
        completion_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate the complete flow completion process.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            completion_options: Optional completion configuration
            
        Returns:
            Dict containing comprehensive completion results
        """
        try:
            logger.info(f"🎯 Orchestrating flow completion: {discovery_flow_id}")
            
            completion_options = completion_options or {}
            
            # Step 1: Validate flow completion readiness
            readiness_result = await self.assessment_manager.validate_flow_completion_readiness(discovery_flow_id)
            
            if not readiness_result["is_ready"]:
                return {
                    "status": "not_ready",
                    "flow_id": str(discovery_flow_id),
                    "readiness_result": readiness_result,
                    "message": "Flow is not ready for completion",
                    "required_actions": readiness_result.get("errors", [])
                }
            
            # Step 2: Get assessment-ready assets
            assets_result = await self.assessment_manager.get_assessment_ready_assets(discovery_flow_id)
            
            # Step 3: Generate comprehensive assessment package
            include_recommendations = completion_options.get("include_recommendations", True)
            assessment_package = await self.assessment_manager.generate_assessment_package(
                discovery_flow_id, include_recommendations
            )
            
            # Step 4: Complete the discovery flow
            completion_result = await self.assessment_manager.complete_discovery_flow(
                discovery_flow_id, completion_options.get("user_id")
            )
            
            # Step 5: Generate orchestration summary
            orchestration_result = {
                "status": "completed",
                "flow_id": str(discovery_flow_id),
                "completion_timestamp": completion_result["completed_at"],
                "readiness_validation": {
                    "status": "passed",
                    "score": readiness_result["readiness_score"],
                    "summary": f"Flow ready with {readiness_result['asset_summary']['migration_ready']} migration-ready assets"
                },
                "asset_processing": {
                    "total_assets": assets_result["total_assets"],
                    "assessment_ready": assets_result["assessment_ready"]["count"],
                    "needs_review": assets_result["needs_review"]["count"],
                    "insufficient_data": assets_result["insufficient_data"]["count"],
                    "readiness_percentage": assets_result["readiness_percentage"]
                },
                "assessment_package": assessment_package,
                "next_phase": {
                    "phase_name": "migration_assessment",
                    "entry_point": f"/api/v3/assessment/flows/{discovery_flow_id}/initialize",
                    "estimated_duration": completion_result["next_steps"]["estimated_duration"],
                    "ready_assets": completion_result["next_steps"]["ready_assets"]
                },
                "workflow_recommendations": completion_result["next_steps"]["recommended_actions"]
            }
            
            logger.info(f"✅ Flow completion orchestration successful: {discovery_flow_id}")
            return orchestration_result
            
        except Exception as e:
            logger.error(f"❌ Error orchestrating flow completion: {e}")
            raise
    
    async def coordinate_partial_assessment(
        self,
        discovery_flow_id: uuid.UUID,
        selected_asset_ids: List[str],
        assessment_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate partial assessment for selected assets.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            selected_asset_ids: List of specific asset IDs to assess
            assessment_options: Optional assessment configuration
            
        Returns:
            Dict containing partial assessment results
        """
        try:
            logger.info(f"🎯 Coordinating partial assessment for {len(selected_asset_ids)} assets")
            
            assessment_options = assessment_options or {}
            
            # Validate selected assets exist and belong to flow
            flow = await self.repository.get_flow_by_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Flow not found: {discovery_flow_id}")
            
            # Get selected assets
            selected_assets = []
            for asset_id in selected_asset_ids:
                asset = await self.repository.get_asset_by_id(asset_id)
                if asset and asset.discovery_flow_id == flow.id:
                    selected_assets.append(asset)
                else:
                    logger.warning(f"Asset {asset_id} not found or doesn't belong to flow")
            
            if not selected_assets:
                raise ValueError("No valid assets found for assessment")
            
            # Generate partial assessment package for selected assets
            partial_package = await self._generate_partial_assessment_package(
                discovery_flow_id, selected_assets, assessment_options
            )
            
            # Generate coordination summary
            coordination_result = {
                "status": "partial_assessment_completed",
                "flow_id": str(discovery_flow_id),
                "selected_assets": len(selected_assets),
                "requested_assets": len(selected_asset_ids),
                "assessment_package": partial_package,
                "scope": "partial",
                "assessment_options": assessment_options,
                "next_steps": [
                    "Review partial assessment results",
                    "Decide on remaining asset inclusion",
                    "Proceed with selected assets or expand scope"
                ]
            }
            
            logger.info(f"✅ Partial assessment coordination completed for {len(selected_assets)} assets")
            return coordination_result
            
        except Exception as e:
            logger.error(f"❌ Error coordinating partial assessment: {e}")
            raise
    
    async def coordinate_assessment_validation(
        self,
        discovery_flow_id: uuid.UUID,
        validation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate comprehensive assessment validation.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            validation_options: Optional validation configuration
            
        Returns:
            Dict containing validation results and recommendations
        """
        try:
            logger.info(f"🔍 Coordinating assessment validation: {discovery_flow_id}")
            
            validation_options = validation_options or {}
            
            # Get flow and assets
            flow = await self.repository.get_flow_by_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Flow not found: {discovery_flow_id}")
            
            assets = await self.repository.get_flow_assets(flow)
            
            # Perform comprehensive validation
            validation_results = {
                "flow_validation": await self.assessment_manager.validate_flow_completion_readiness(discovery_flow_id),
                "asset_statistics": await self.repository.get_flow_statistics(str(discovery_flow_id)),
                "readiness_assessment": await self.assessment_manager.readiness_assessor.assess_flow_readiness(flow, assets),
                "risk_assessment": await self.assessment_manager.risk_assessor.assess_flow_risk(str(discovery_flow_id), assets),
                "complexity_assessment": await self.assessment_manager.complexity_assessor.assess_flow_complexity(str(discovery_flow_id), assets)
            }
            
            # Generate validation summary
            overall_validation = self._generate_overall_validation_summary(validation_results)
            
            coordination_result = {
                "status": "validation_completed",
                "flow_id": str(discovery_flow_id),
                "validation_timestamp": str(uuid.uuid4()),  # Use as validation session ID
                "overall_validation": overall_validation,
                "detailed_results": validation_results,
                "recommendations": self._generate_validation_recommendations(overall_validation, validation_results),
                "next_steps": self._generate_validation_next_steps(overall_validation)
            }
            
            logger.info(f"✅ Assessment validation coordination completed: {discovery_flow_id}")
            return coordination_result
            
        except Exception as e:
            logger.error(f"❌ Error coordinating assessment validation: {e}")
            raise
    
    async def coordinate_flow_reset(
        self,
        discovery_flow_id: uuid.UUID,
        reset_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate flow reset for re-assessment.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            reset_options: Optional reset configuration
            
        Returns:
            Dict containing reset results
        """
        try:
            logger.info(f"🔄 Coordinating flow reset: {discovery_flow_id}")
            
            reset_options = reset_options or {}
            
            # Validate flow exists
            flow = await self.repository.get_flow_by_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Flow not found: {discovery_flow_id}")
            
            # Delete assessment data
            reset_successful = await self.repository.delete_assessment_data(str(discovery_flow_id))
            
            if not reset_successful:
                raise ValueError("Failed to reset flow assessment data")
            
            # Get updated flow statistics
            updated_statistics = await self.repository.get_flow_statistics(str(discovery_flow_id))
            
            coordination_result = {
                "status": "reset_completed",
                "flow_id": str(discovery_flow_id),
                "reset_timestamp": str(uuid.uuid4()),
                "reset_scope": reset_options.get("scope", "assessment_data"),
                "updated_statistics": updated_statistics,
                "next_steps": [
                    "Re-validate flow completion readiness",
                    "Re-generate assessment package if needed",
                    "Proceed with fresh assessment process"
                ]
            }
            
            logger.info(f"✅ Flow reset coordination completed: {discovery_flow_id}")
            return coordination_result
            
        except Exception as e:
            logger.error(f"❌ Error coordinating flow reset: {e}")
            raise
    
    async def _generate_partial_assessment_package(
        self,
        discovery_flow_id: uuid.UUID,
        selected_assets: List,
        assessment_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate assessment package for selected assets."""
        
        # Convert assets to the format expected by assessment manager
        asset_dicts = []
        for asset in selected_assets:
            asset_dict = {
                "id": str(asset.id),
                "asset_name": asset.asset_name,
                "asset_type": asset.asset_type,
                "asset_subtype": asset.asset_subtype,
                "migration_complexity": asset.migration_complexity,
                "confidence_score": asset.confidence_score or 0.0,
                "validation_status": asset.validation_status,
                "migration_ready": asset.migration_ready,
                "migration_priority": asset.migration_priority or 3,
                "normalized_data": asset.normalized_data or {}
            }
            asset_dicts.append(asset_dict)
        
        # Generate risk assessment for selected assets
        risk_assessment = await self.assessment_manager.risk_assessor.assess_migration_risks(asset_dicts)
        
        # Generate complexity assessment for selected assets
        complexity_assessment = await self.assessment_manager.complexity_assessor.assess_migration_complexity(asset_dicts)
        
        # Create partial assessment package
        partial_package = {
            "package_type": "partial",
            "flow_id": str(discovery_flow_id),
            "selected_asset_count": len(selected_assets),
            "assessment_scope": "selected_assets",
            "risk_assessment": risk_assessment,
            "complexity_assessment": complexity_assessment,
            "assets": asset_dicts,
            "assessment_options": assessment_options
        }
        
        return partial_package
    
    def _generate_overall_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall validation summary from detailed results."""
        
        flow_validation = validation_results["flow_validation"]
        readiness_assessment = validation_results["readiness_assessment"]
        risk_assessment = validation_results["risk_assessment"]
        complexity_assessment = validation_results["complexity_assessment"]
        
        # Calculate overall readiness score
        overall_score = (
            flow_validation["readiness_score"] * 0.3 +
            readiness_assessment["readiness_score"] * 0.4 +
            (1 - risk_assessment["overall_risk_score"]) * 0.2 +  # Lower risk = higher readiness
            (1 - complexity_assessment["overall_complexity_score"]) * 0.1  # Lower complexity = higher readiness
        )
        
        # Determine overall status
        is_ready = (
            flow_validation["is_ready"] and
            readiness_assessment["is_ready"] and
            risk_assessment["overall_risk_level"] in ["low", "medium"] and
            complexity_assessment["overall_complexity_level"] in ["low", "medium"]
        )
        
        return {
            "is_ready": is_ready,
            "overall_score": round(overall_score, 2),
            "validation_level": "high" if overall_score >= 0.8 else ("medium" if overall_score >= 0.6 else "low"),
            "critical_issues": self._identify_critical_validation_issues(validation_results),
            "summary": f"Overall readiness: {round(overall_score * 100, 1)}% - {'Ready' if is_ready else 'Not Ready'}"
        }
    
    def _identify_critical_validation_issues(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify critical issues preventing validation."""
        
        issues = []
        
        # Flow-level issues
        if not validation_results["flow_validation"]["is_ready"]:
            issues.extend(validation_results["flow_validation"].get("errors", []))
        
        # Readiness issues
        if not validation_results["readiness_assessment"]["is_ready"]:
            gaps = validation_results["readiness_assessment"].get("readiness_gaps", [])
            for gap in gaps:
                if gap.get("severity") == "high":
                    issues.append(gap["description"])
        
        # Risk issues
        if validation_results["risk_assessment"]["overall_risk_level"] == "high":
            issues.append("High migration risk identified")
        
        # Complexity issues
        if validation_results["complexity_assessment"]["overall_complexity_level"] == "high":
            issues.append("High migration complexity detected")
        
        return issues
    
    def _generate_validation_recommendations(
        self,
        overall_validation: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        
        recommendations = []
        
        if overall_validation["is_ready"]:
            recommendations.append("Flow is ready for migration assessment")
            recommendations.append("Proceed with assessment package generation")
        else:
            recommendations.append("Address critical validation issues before proceeding")
            
            # Add specific recommendations from each assessment
            recommendations.extend(validation_results["readiness_assessment"].get("recommendations", []))
            recommendations.extend(validation_results["risk_assessment"].get("recommendations", []))
            recommendations.extend(validation_results["complexity_assessment"].get("recommendations", []))
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_validation_next_steps(self, overall_validation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate next steps based on validation results."""
        
        next_steps = []
        
        if overall_validation["is_ready"]:
            next_steps.append({
                "action": "Generate Assessment Package",
                "description": "Create comprehensive assessment package for migration planning",
                "priority": "high",
                "estimated_effort": "1-2 hours"
            })
            next_steps.append({
                "action": "Initiate Migration Assessment",
                "description": "Begin migration assessment phase with generated package",
                "priority": "high",
                "estimated_effort": "1-2 weeks"
            })
        else:
            next_steps.append({
                "action": "Resolve Critical Issues",
                "description": "Address all critical validation issues",
                "priority": "high",
                "estimated_effort": "1-2 weeks"
            })
            next_steps.append({
                "action": "Re-validate Flow",
                "description": "Re-run validation after issue resolution",
                "priority": "medium",
                "estimated_effort": "1-2 hours"
            })
        
        return next_steps