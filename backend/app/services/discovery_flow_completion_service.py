"""
Discovery Flow Completion Service
Handles flow completion logic, assessment package generation, and handoff to assessment phase.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow
from app.models.asset import Asset as DiscoveryAsset
from app.models.asset import Asset
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)


class DiscoveryFlowCompletionService:
    """Service for handling discovery flow completion and assessment handoff"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.discovery_repo = DiscoveryFlowRepository(db, str(context.client_account_id), str(context.engagement_id))
        self.asset_repo = AssetRepository(db, str(context.client_account_id))
    
    async def validate_flow_completion_readiness(
        self, 
        discovery_flow_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Validate if a discovery flow is ready for completion and assessment handoff.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            
        Returns:
            Dict containing validation results and readiness status
        """
        try:
            logger.info(f"🔍 Validating completion readiness for flow: {discovery_flow_id}")
            
            # Get discovery flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")
            
            # Get discovery assets
            discovery_assets = await self.db.execute(
                select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id == self.context.client_account_id
                    )
                )
            )
            assets = discovery_assets.scalars().all()
            
            # Validation checks
            validation_results = {
                "flow_id": str(discovery_flow_id),
                "is_ready": True,
                "validation_checks": {},
                "warnings": [],
                "errors": [],
                "asset_summary": {},
                "readiness_score": 0.0
            }
            
            # Check 1: All required phases completed
            required_phases = [
                "data_import_completed",
                "attribute_mapping_completed", 
                "data_cleansing_completed",
                "inventory_completed"
            ]
            
            completed_phases = []
            for phase in required_phases:
                if getattr(flow, phase, False):
                    completed_phases.append(phase)
            
            validation_results["validation_checks"]["phases_completed"] = {
                "required": len(required_phases),
                "completed": len(completed_phases),
                "missing": [p for p in required_phases if not getattr(flow, phase, False)],
                "passed": len(completed_phases) == len(required_phases)
            }
            
            if len(completed_phases) < len(required_phases):
                validation_results["errors"].append(
                    f"Missing required phases: {validation_results['validation_checks']['phases_completed']['missing']}"
                )
                validation_results["is_ready"] = False
            
            # Check 2: Minimum asset count
            min_assets = 1
            asset_count = len(assets)
            validation_results["validation_checks"]["asset_count"] = {
                "minimum_required": min_assets,
                "actual_count": asset_count,
                "passed": asset_count >= min_assets
            }
            
            if asset_count < min_assets:
                validation_results["errors"].append(
                    f"Insufficient assets: {asset_count} found, minimum {min_assets} required"
                )
                validation_results["is_ready"] = False
            
            # Check 3: Asset quality thresholds
            migration_ready_count = sum(1 for a in assets if a.migration_ready)
            high_confidence_count = sum(1 for a in assets if (a.confidence_score or 0) >= 0.8)
            validated_count = sum(1 for a in assets if a.validation_status == "approved")
            
            validation_results["validation_checks"]["asset_quality"] = {
                "migration_ready": {
                    "count": migration_ready_count,
                    "percentage": (migration_ready_count / asset_count * 100) if asset_count > 0 else 0,
                    "minimum_percentage": 50,
                    "passed": (migration_ready_count / asset_count * 100) >= 50 if asset_count > 0 else False
                },
                "high_confidence": {
                    "count": high_confidence_count,
                    "percentage": (high_confidence_count / asset_count * 100) if asset_count > 0 else 0,
                    "minimum_percentage": 70,
                    "passed": (high_confidence_count / asset_count * 100) >= 70 if asset_count > 0 else False
                },
                "validated": {
                    "count": validated_count,
                    "percentage": (validated_count / asset_count * 100) if asset_count > 0 else 0,
                    "minimum_percentage": 80,
                    "passed": (validated_count / asset_count * 100) >= 80 if asset_count > 0 else False
                }
            }
            
            # Add warnings for quality thresholds
            if not validation_results["validation_checks"]["asset_quality"]["migration_ready"]["passed"]:
                validation_results["warnings"].append(
                    f"Low migration readiness: {migration_ready_count}/{asset_count} assets ready"
                )
            
            if not validation_results["validation_checks"]["asset_quality"]["high_confidence"]["passed"]:
                validation_results["warnings"].append(
                    f"Low confidence scores: {high_confidence_count}/{asset_count} assets with >80% confidence"
                )
            
            if not validation_results["validation_checks"]["asset_quality"]["validated"]["passed"]:
                validation_results["warnings"].append(
                    f"Low validation rate: {validated_count}/{asset_count} assets validated"
                )
            
            # Check 4: Critical data completeness
            assets_with_names = sum(1 for a in assets if a.asset_name and a.asset_name.strip())
            assets_with_types = sum(1 for a in assets if a.asset_type and a.asset_type.strip())
            
            validation_results["validation_checks"]["data_completeness"] = {
                "assets_with_names": {
                    "count": assets_with_names,
                    "percentage": (assets_with_names / asset_count * 100) if asset_count > 0 else 0,
                    "passed": assets_with_names == asset_count
                },
                "assets_with_types": {
                    "count": assets_with_types,
                    "percentage": (assets_with_types / asset_count * 100) if asset_count > 0 else 0,
                    "passed": assets_with_types == asset_count
                }
            }
            
            if assets_with_names < asset_count:
                validation_results["errors"].append(
                    f"Missing asset names: {asset_count - assets_with_names} assets without names"
                )
                validation_results["is_ready"] = False
            
            if assets_with_types < asset_count:
                validation_results["warnings"].append(
                    f"Missing asset types: {asset_count - assets_with_types} assets without types"
                )
            
            # Generate asset summary
            asset_types = {}
            migration_complexities = {}
            for asset in assets:
                # Count by type
                asset_type = asset.asset_type or "unknown"
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                
                # Count by complexity
                complexity = asset.migration_complexity or "unknown"
                migration_complexities[complexity] = migration_complexities.get(complexity, 0) + 1
            
            validation_results["asset_summary"] = {
                "total_assets": asset_count,
                "migration_ready": migration_ready_count,
                "by_type": asset_types,
                "by_complexity": migration_complexities,
                "average_confidence": sum(a.confidence_score or 0 for a in assets) / asset_count if asset_count > 0 else 0
            }
            
            # Calculate overall readiness score
            phase_score = (len(completed_phases) / len(required_phases)) * 30
            asset_count_score = min(asset_count / min_assets, 1.0) * 20
            migration_ready_score = (migration_ready_count / asset_count) * 25 if asset_count > 0 else 0
            confidence_score = (high_confidence_count / asset_count) * 15 if asset_count > 0 else 0
            validation_score = (validated_count / asset_count) * 10 if asset_count > 0 else 0
            
            validation_results["readiness_score"] = phase_score + asset_count_score + migration_ready_score + confidence_score + validation_score
            
            logger.info(f"✅ Flow validation completed: {discovery_flow_id} - Ready: {validation_results['is_ready']}")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Error validating flow completion: {e}")
            raise
    
    async def get_assessment_ready_assets(
        self, 
        discovery_flow_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get assets that are ready for assessment with optional filtering.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            filters: Optional filters (migration_ready, asset_type, min_confidence, etc.)
            
        Returns:
            Dict containing filtered assets and metadata
        """
        try:
            logger.info(f"🔍 Getting assessment-ready assets for flow: {discovery_flow_id}")
            
            # Get discovery flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")
            
            # Base query for assets
            query = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow.id,
                    DiscoveryAsset.client_account_id == self.context.client_account_id
                )
            )
            
            # Apply filters
            if filters:
                if filters.get("migration_ready") is True:
                    query = query.where(DiscoveryAsset.migration_ready == True)
                
                if filters.get("asset_type"):
                    query = query.where(DiscoveryAsset.asset_type == filters["asset_type"])
                
                if filters.get("min_confidence"):
                    query = query.where(DiscoveryAsset.confidence_score >= filters["min_confidence"])
                
                if filters.get("validation_status"):
                    query = query.where(DiscoveryAsset.validation_status == filters["validation_status"])
                
                if filters.get("migration_complexity"):
                    query = query.where(DiscoveryAsset.migration_complexity == filters["migration_complexity"])
            
            # Execute query
            result = await self.db.execute(query)
            assets = result.scalars().all()
            
            # Convert to response format
            asset_list = []
            for asset in assets:
                asset_dict = {
                    "id": str(asset.id),
                    "discovery_flow_id": str(asset.discovery_flow_id),
                    "asset_name": asset.asset_name,
                    "asset_type": asset.asset_type,
                    "asset_subtype": asset.asset_subtype,
                    "migration_ready": asset.migration_ready,
                    "migration_complexity": asset.migration_complexity,
                    "migration_priority": asset.migration_priority,
                    "confidence_score": asset.confidence_score,
                    "validation_status": asset.validation_status,
                    "discovered_in_phase": asset.discovered_in_phase,
                    "discovery_method": asset.discovery_method,
                    "normalized_data": asset.normalized_data,
                    "created_at": asset.created_at.isoformat() if asset.created_at else None,
                    "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
                }
                asset_list.append(asset_dict)
            
            # Generate summary statistics
            total_count = len(asset_list)
            migration_ready_count = sum(1 for a in asset_list if a["migration_ready"])
            
            asset_types = {}
            complexities = {}
            for asset in asset_list:
                asset_type = asset["asset_type"] or "unknown"
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                
                complexity = asset["migration_complexity"] or "unknown"
                complexities[complexity] = complexities.get(complexity, 0) + 1
            
            response = {
                "flow_id": str(discovery_flow_id),
                "filters_applied": filters or {},
                "assets": asset_list,
                "summary": {
                    "total_assets": total_count,
                    "migration_ready": migration_ready_count,
                    "migration_ready_percentage": (migration_ready_count / total_count * 100) if total_count > 0 else 0,
                    "by_type": asset_types,
                    "by_complexity": complexities,
                    "average_confidence": sum(a["confidence_score"] or 0 for a in asset_list) / total_count if total_count > 0 else 0
                }
            }
            
            logger.info(f"✅ Retrieved {total_count} assessment-ready assets for flow: {discovery_flow_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error getting assessment-ready assets: {e}")
            raise
    
    async def generate_assessment_package(
        self, 
        discovery_flow_id: uuid.UUID,
        selected_asset_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive assessment package for handoff to assessment phase.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            selected_asset_ids: Optional list of specific asset IDs to include
            
        Returns:
            Dict containing complete assessment package
        """
        try:
            logger.info(f"🎯 Generating assessment package for flow: {discovery_flow_id}")
            
            # Validate flow readiness
            validation_results = await self.validate_flow_completion_readiness(discovery_flow_id)
            if not validation_results["is_ready"]:
                raise ValueError(f"Flow not ready for assessment: {validation_results['errors']}")
            
            # Get flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            
            # Get assets (filtered by selection if provided)
            if selected_asset_ids:
                # Get specific selected assets
                asset_query = select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.id.in_([uuid.UUID(aid) for aid in selected_asset_ids]),
                        DiscoveryAsset.client_account_id == self.context.client_account_id
                    )
                )
            else:
                # Get all migration-ready assets
                asset_query = select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.migration_ready == True,
                        DiscoveryAsset.client_account_id == self.context.client_account_id
                    )
                )
            
            result = await self.db.execute(asset_query)
            discovery_assets = result.scalars().all()
            
            # Generate assessment package
            assessment_package = {
                "package_id": str(uuid.uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "discovery_flow": {
                    "id": str(flow.id),
                    "flow_id": str(flow.flow_id),
                    "flow_name": flow.flow_name,
                    "completed_at": datetime.utcnow().isoformat(),
                    "progress_percentage": flow.progress_percentage,
                    "migration_readiness_score": flow.migration_readiness_score
                },
                "assets": [],
                "summary": {
                    "total_assets": len(discovery_assets),
                    "migration_ready_assets": sum(1 for a in discovery_assets if a.migration_ready),
                    "by_type": {},
                    "by_complexity": {},
                    "by_priority": {},
                    "average_confidence": 0.0,
                    "total_estimated_effort": 0
                },
                "migration_waves": [],
                "risk_assessment": {
                    "overall_risk": "medium",
                    "risk_factors": [],
                    "mitigation_recommendations": []
                },
                "recommendations": {
                    "six_r_distribution": {},
                    "modernization_opportunities": [],
                    "quick_wins": [],
                    "complex_migrations": []
                }
            }
            
            # Process each asset
            complexity_weights = {"low": 1, "medium": 3, "high": 8, "unknown": 5}
            total_confidence = 0
            
            for asset in discovery_assets:
                asset_data = {
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "type": asset.asset_type,
                    "subtype": asset.asset_subtype,
                    "migration_ready": asset.migration_ready,
                    "migration_complexity": asset.migration_complexity,
                    "migration_priority": asset.migration_priority or 3,
                    "confidence_score": asset.confidence_score or 0.0,
                    "validation_status": asset.validation_status,
                    "discovered_in_phase": asset.discovered_in_phase,
                    "normalized_data": asset.normalized_data or {},
                    "raw_data": asset.raw_data or {},
                    "estimated_effort_weeks": complexity_weights.get(asset.migration_complexity or "unknown", 5),
                    "six_r_recommendation": self._determine_six_r_strategy(asset),
                    "risk_level": self._assess_asset_risk(asset),
                    "modernization_potential": self._assess_modernization_potential(asset)
                }
                
                assessment_package["assets"].append(asset_data)
                
                # Update summary statistics
                asset_type = asset.asset_type or "unknown"
                assessment_package["summary"]["by_type"][asset_type] = \
                    assessment_package["summary"]["by_type"].get(asset_type, 0) + 1
                
                complexity = asset.migration_complexity or "unknown"
                assessment_package["summary"]["by_complexity"][complexity] = \
                    assessment_package["summary"]["by_complexity"].get(complexity, 0) + 1
                
                priority = asset.migration_priority or 3
                assessment_package["summary"]["by_priority"][str(priority)] = \
                    assessment_package["summary"]["by_priority"].get(str(priority), 0) + 1
                
                total_confidence += asset.confidence_score or 0.0
                assessment_package["summary"]["total_estimated_effort"] += asset_data["estimated_effort_weeks"]
            
            # Calculate averages
            if len(discovery_assets) > 0:
                assessment_package["summary"]["average_confidence"] = total_confidence / len(discovery_assets)
            
            # Generate migration waves based on dependencies and complexity
            assessment_package["migration_waves"] = self._generate_migration_waves(discovery_assets)
            
            # Generate risk assessment
            assessment_package["risk_assessment"] = self._generate_risk_assessment(discovery_assets)
            
            # Generate recommendations
            assessment_package["recommendations"] = self._generate_recommendations(discovery_assets)
            
            logger.info(f"✅ Assessment package generated for {len(discovery_assets)} assets")
            return assessment_package
            
        except Exception as e:
            logger.error(f"❌ Error generating assessment package: {e}")
            raise
    
    async def complete_discovery_flow(
        self, 
        discovery_flow_id: uuid.UUID,
        assessment_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark discovery flow as complete and prepare for assessment handoff.
        
        Args:
            discovery_flow_id: UUID of the discovery flow
            assessment_package: Generated assessment package
            
        Returns:
            Dict containing completion results
        """
        try:
            logger.info(f"🎯 Completing discovery flow: {discovery_flow_id}")
            
            # Update flow status
            await self.db.execute(
                update(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.flow_id == discovery_flow_id,
                        DiscoveryFlow.client_account_id == self.context.client_account_id
                    )
                ).values(
                    status="completed",
                    progress_percentage=100.0,
                    assessment_ready=True,
                    completed_at=datetime.utcnow(),
                    assessment_package=assessment_package,
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.db.commit()
            
            completion_result = {
                "flow_id": str(discovery_flow_id),
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "assessment_ready": True,
                "assessment_package": assessment_package,
                "next_steps": {
                    "assessment_initialization": f"/assess/initialize/{discovery_flow_id}",
                    "asset_selection": f"/assess/assets/{discovery_flow_id}",
                    "migration_planning": f"/plan/waves/{discovery_flow_id}"
                }
            }
            
            logger.info(f"✅ Discovery flow completed successfully: {discovery_flow_id}")
            return completion_result
            
        except Exception as e:
            logger.error(f"❌ Error completing discovery flow: {e}")
            raise
    
    def _determine_six_r_strategy(self, asset: DiscoveryAsset) -> str:
        """Determine 6R migration strategy for an asset"""
        # Simple heuristic based on asset type and complexity
        asset_type = asset.asset_type or "unknown"
        complexity = asset.migration_complexity or "medium"
        
        if asset_type in ["database", "legacy_system"]:
            return "replatform" if complexity == "high" else "rehost"
        elif asset_type == "application":
            return "refactor" if complexity == "high" else "replatform"
        elif asset_type in ["server", "infrastructure"]:
            return "rehost"
        else:
            return "replatform"
    
    def _assess_asset_risk(self, asset: DiscoveryAsset) -> str:
        """Assess migration risk level for an asset"""
        complexity = asset.migration_complexity or "medium"
        confidence = asset.confidence_score or 0.5
        
        if complexity == "high" or confidence < 0.6:
            return "high"
        elif complexity == "medium" and confidence >= 0.8:
            return "medium"
        else:
            return "low"
    
    def _assess_modernization_potential(self, asset: DiscoveryAsset) -> str:
        """Assess modernization potential for an asset"""
        asset_type = asset.asset_type or "unknown"
        
        if asset_type == "application":
            return "high"
        elif asset_type in ["server", "infrastructure"]:
            return "medium"
        else:
            return "low"
    
    def _generate_migration_waves(self, assets: List[DiscoveryAsset]) -> List[Dict[str, Any]]:
        """Generate migration waves based on dependencies and complexity"""
        # Simple wave generation - can be enhanced with dependency analysis
        waves = []
        
        # Wave 1: Low complexity, infrastructure
        wave1_assets = [a for a in assets if a.migration_complexity == "low" and a.asset_type in ["server", "infrastructure"]]
        if wave1_assets:
            waves.append({
                "wave": 1,
                "name": "Infrastructure Foundation",
                "assets": [{"id": str(a.id), "name": a.asset_name} for a in wave1_assets],
                "estimated_duration_weeks": max(2, len(wave1_assets)),
                "dependencies": []
            })
        
        # Wave 2: Medium complexity applications
        wave2_assets = [a for a in assets if a.migration_complexity == "medium" and a.asset_type == "application"]
        if wave2_assets:
            waves.append({
                "wave": 2,
                "name": "Core Applications",
                "assets": [{"id": str(a.id), "name": a.asset_name} for a in wave2_assets],
                "estimated_duration_weeks": max(4, len(wave2_assets) * 2),
                "dependencies": ["wave_1"] if waves else []
            })
        
        # Wave 3: High complexity and databases
        wave3_assets = [a for a in assets if a.migration_complexity == "high" or a.asset_type == "database"]
        if wave3_assets:
            waves.append({
                "wave": 3,
                "name": "Complex Systems",
                "assets": [{"id": str(a.id), "name": a.asset_name} for a in wave3_assets],
                "estimated_duration_weeks": max(6, len(wave3_assets) * 3),
                "dependencies": ["wave_1", "wave_2"] if len(waves) >= 2 else (["wave_1"] if waves else [])
            })
        
        return waves
    
    def _generate_risk_assessment(self, assets: List[DiscoveryAsset]) -> Dict[str, Any]:
        """Generate overall risk assessment"""
        high_risk_count = sum(1 for a in assets if self._assess_asset_risk(a) == "high")
        total_assets = len(assets)
        
        if high_risk_count / total_assets > 0.3:
            overall_risk = "high"
        elif high_risk_count / total_assets > 0.1:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        risk_factors = []
        if high_risk_count > 0:
            risk_factors.append(f"{high_risk_count} high-risk assets identified")
        
        complex_assets = sum(1 for a in assets if a.migration_complexity == "high")
        if complex_assets > 0:
            risk_factors.append(f"{complex_assets} highly complex assets")
        
        low_confidence = sum(1 for a in assets if (a.confidence_score or 0) < 0.7)
        if low_confidence > 0:
            risk_factors.append(f"{low_confidence} assets with low confidence scores")
        
        return {
            "overall_risk": overall_risk,
            "risk_factors": risk_factors,
            "mitigation_recommendations": [
                "Conduct detailed technical assessment for high-risk assets",
                "Plan additional discovery for low-confidence assets",
                "Consider proof-of-concept migrations for complex systems"
            ]
        }
    
    def _generate_recommendations(self, assets: List[DiscoveryAsset]) -> Dict[str, Any]:
        """Generate migration recommendations"""
        six_r_dist = {}
        quick_wins = []
        complex_migrations = []
        modernization_opportunities = []
        
        for asset in assets:
            strategy = self._determine_six_r_strategy(asset)
            six_r_dist[strategy] = six_r_dist.get(strategy, 0) + 1
            
            if asset.migration_complexity == "low" and asset.migration_ready:
                quick_wins.append({
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "reason": "Low complexity, migration ready"
                })
            
            if asset.migration_complexity == "high":
                complex_migrations.append({
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "complexity_factors": ["High migration complexity"]
                })
            
            if self._assess_modernization_potential(asset) == "high":
                modernization_opportunities.append({
                    "id": str(asset.id),
                    "name": asset.asset_name,
                    "opportunity": "Application modernization candidate"
                })
        
        return {
            "six_r_distribution": six_r_dist,
            "quick_wins": quick_wins,
            "complex_migrations": complex_migrations,
            "modernization_opportunities": modernization_opportunities
        } 