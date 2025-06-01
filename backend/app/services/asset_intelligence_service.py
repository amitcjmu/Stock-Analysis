"""
Agentic Asset Intelligence Service
Provides AI-powered analysis of asset readiness for migration assessment
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

class AssetIntelligenceService:
    """
    AI-powered asset intelligence for migration readiness assessment
    """
    
    def __init__(self):
        self.crewai_available = False
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize CrewAI and other AI services"""
        try:
            from app.services.crewai_service_modular import crewai_service
            self.crewai_service = crewai_service
            self.crewai_available = crewai_service.is_available()
            logger.info("Asset Intelligence Service initialized with CrewAI support")
        except ImportError:
            logger.warning("CrewAI service not available for Asset Intelligence")
    
    async def analyze_asset_inventory(self, db: AsyncSession, client_account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive analysis of entire asset inventory for migration readiness
        """
        try:
            # Get all assets with workflow progress
            query = select(AssetInventory).options(
                selectinload(AssetInventory.workflow_progress)
            )
            
            if client_account_id:
                query = query.where(AssetInventory.client_account_id == client_account_id)
            
            result = await db.execute(query)
            assets = result.scalars().all()
            
            if not assets:
                return {
                    "status": "no_assets",
                    "message": "No assets found for analysis",
                    "total_assets": 0
                }
            
            # Perform comprehensive analysis
            analysis_result = await self._perform_comprehensive_analysis(assets)
            
            # Store analysis results back to database
            await self._update_asset_analysis_results(db, assets, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in asset inventory analysis: {e}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "total_assets": 0
            }
    
    async def _perform_comprehensive_analysis(self, assets: List) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered analysis of asset inventory
        """
        total_assets = len(assets)
        
        # Basic metrics
        asset_metrics = self._calculate_asset_metrics(assets)
        
        # Workflow analysis
        workflow_analysis = self._analyze_workflow_progress(assets)
        
        # Data quality assessment
        quality_analysis = self._assess_data_quality(assets)
        
        # Migration readiness assessment
        readiness_analysis = self._assess_migration_readiness(assets)
        
        # Dependency analysis
        dependency_analysis = self._analyze_dependencies(assets)
        
        # AI-powered insights (if CrewAI available)
        ai_insights = await self._generate_ai_insights(assets)
        
        # Recommendations for next steps
        recommendations = self._generate_recommendations(assets, workflow_analysis, quality_analysis)
        
        return {
            "status": "success",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "total_assets": total_assets,
            "asset_metrics": asset_metrics,
            "workflow_analysis": workflow_analysis,
            "data_quality": quality_analysis,
            "migration_readiness": readiness_analysis,
            "dependency_analysis": dependency_analysis,
            "ai_insights": ai_insights,
            "recommendations": recommendations,
            "assessment_ready": self._determine_assessment_readiness(workflow_analysis, quality_analysis)
        }
    
    def _calculate_asset_metrics(self, assets: List) -> Dict[str, Any]:
        """Calculate basic asset inventory metrics"""
        metrics = {
            "total_count": len(assets),
            "by_type": {},
            "by_environment": {},
            "by_criticality": {},
            "by_status": {}
        }
        
        for asset in assets:
            # Count by type
            asset_type = getattr(asset, 'asset_type', 'Unknown')
            metrics["by_type"][asset_type] = metrics["by_type"].get(asset_type, 0) + 1
            
            # Count by environment
            environment = getattr(asset, 'environment', 'Unknown')
            metrics["by_environment"][environment] = metrics["by_environment"].get(environment, 0) + 1
            
            # Count by criticality
            criticality = getattr(asset, 'business_criticality', 'Unknown')
            metrics["by_criticality"][criticality] = metrics["by_criticality"].get(criticality, 0) + 1
            
            # Count by discovery status
            discovery_status = getattr(asset, 'discovery_status', 'Unknown')
            metrics["by_status"][discovery_status] = metrics["by_status"].get(discovery_status, 0) + 1
        
        return metrics
    
    def _analyze_workflow_progress(self, assets: List) -> Dict[str, Any]:
        """Analyze workflow progress across all assets"""
        workflow_stats = {
            "discovery": {"completed": 0, "pending": 0, "failed": 0},
            "mapping": {"completed": 0, "pending": 0, "in_progress": 0, "failed": 0},
            "cleanup": {"completed": 0, "pending": 0, "in_progress": 0, "failed": 0},
            "assessment_ready": {"ready": 0, "partial": 0, "not_ready": 0}
        }
        
        for asset in assets:
            # Discovery status
            discovery_status = getattr(asset, 'discovery_status', 'pending')
            if discovery_status in workflow_stats["discovery"]:
                workflow_stats["discovery"][discovery_status] += 1
            
            # Mapping status
            mapping_status = getattr(asset, 'mapping_status', 'pending')
            if mapping_status in workflow_stats["mapping"]:
                workflow_stats["mapping"][mapping_status] += 1
            
            # Cleanup status
            cleanup_status = getattr(asset, 'cleanup_status', 'pending')
            if cleanup_status in workflow_stats["cleanup"]:
                workflow_stats["cleanup"][cleanup_status] += 1
            
            # Assessment readiness
            assessment_readiness = getattr(asset, 'assessment_readiness', 'not_ready')
            if assessment_readiness in workflow_stats["assessment_ready"]:
                workflow_stats["assessment_ready"][assessment_readiness] += 1
        
        # Calculate completion percentages
        total_assets = len(assets)
        workflow_stats["completion_percentages"] = {
            "discovery": (workflow_stats["discovery"]["completed"] / total_assets * 100) if total_assets > 0 else 0,
            "mapping": (workflow_stats["mapping"]["completed"] / total_assets * 100) if total_assets > 0 else 0,
            "cleanup": (workflow_stats["cleanup"]["completed"] / total_assets * 100) if total_assets > 0 else 0,
            "assessment_ready": (workflow_stats["assessment_ready"]["ready"] / total_assets * 100) if total_assets > 0 else 0
        }
        
        return workflow_stats
    
    def _assess_data_quality(self, assets: List) -> Dict[str, Any]:
        """Assess data quality across all assets"""
        critical_fields = [
            'asset_name', 'asset_type', 'environment', 'business_owner',
            'business_criticality', 'application_id', 'hostname'
        ]
        
        quality_stats = {
            "overall_score": 0.0,
            "completeness_by_field": {},
            "missing_critical_data": [],
            "quality_issues": []
        }
        
        total_assets = len(assets)
        if total_assets == 0:
            return quality_stats
        
        # Analyze completeness for each critical field
        for field in critical_fields:
            filled_count = sum(1 for asset in assets if getattr(asset, field, None) not in [None, '', 'Unknown'])
            completeness = (filled_count / total_assets) * 100
            quality_stats["completeness_by_field"][field] = completeness
        
        # Calculate overall completeness score
        quality_stats["overall_score"] = sum(quality_stats["completeness_by_field"].values()) / len(critical_fields)
        
        # Identify assets with missing critical data
        for asset in assets:
            missing_fields = []
            for field in critical_fields:
                if getattr(asset, field, None) in [None, '', 'Unknown']:
                    missing_fields.append(field)
            
            if missing_fields:
                quality_stats["missing_critical_data"].append({
                    "asset_id": getattr(asset, 'asset_id', 'unknown'),
                    "asset_name": getattr(asset, 'asset_name', 'Unknown'),
                    "missing_fields": missing_fields,
                    "completeness": ((len(critical_fields) - len(missing_fields)) / len(critical_fields)) * 100
                })
        
        return quality_stats
    
    def _assess_migration_readiness(self, assets: List) -> Dict[str, Any]:
        """Assess migration readiness for all assets"""
        readiness_stats = {
            "ready_for_assessment": 0,
            "needs_more_data": 0,
            "has_dependencies": 0,
            "needs_modernization": 0,
            "readiness_by_type": {},
            "blockers": []
        }
        
        for asset in assets:
            asset_type = getattr(asset, 'asset_type', 'Unknown')
            
            # Initialize type stats if not exists
            if asset_type not in readiness_stats["readiness_by_type"]:
                readiness_stats["readiness_by_type"][asset_type] = {
                    "total": 0, "ready": 0, "needs_data": 0, "has_issues": 0
                }
            
            readiness_stats["readiness_by_type"][asset_type]["total"] += 1
            
            # Check readiness criteria
            assessment_readiness = getattr(asset, 'assessment_readiness', 'not_ready')
            
            if assessment_readiness == 'ready':
                readiness_stats["ready_for_assessment"] += 1
                readiness_stats["readiness_by_type"][asset_type]["ready"] += 1
            elif assessment_readiness == 'partial':
                readiness_stats["needs_more_data"] += 1
                readiness_stats["readiness_by_type"][asset_type]["needs_data"] += 1
            else:
                readiness_stats["readiness_by_type"][asset_type]["has_issues"] += 1
            
            # Check for dependencies
            if (getattr(asset, 'server_dependencies', None) or 
                getattr(asset, 'application_dependencies', None)):
                readiness_stats["has_dependencies"] += 1
            
            # Check modernization needs
            tech_debt_score = getattr(asset, 'tech_debt_score', 0)
            if tech_debt_score and tech_debt_score > 7.0:
                readiness_stats["needs_modernization"] += 1
        
        return readiness_stats
    
    def _analyze_dependencies(self, assets: List) -> Dict[str, Any]:
        """Analyze asset dependencies for migration planning"""
        dependency_stats = {
            "total_dependencies": 0,
            "application_dependencies": 0,
            "server_dependencies": 0,
            "database_dependencies": 0,
            "complex_dependency_chains": [],
            "orphaned_assets": []
        }
        
        for asset in assets:
            asset_name = getattr(asset, 'asset_name', 'Unknown')
            
            # Count application dependencies
            app_deps = getattr(asset, 'application_dependencies', []) or []
            if app_deps:
                dependency_stats["application_dependencies"] += len(app_deps)
                dependency_stats["total_dependencies"] += len(app_deps)
            
            # Count server dependencies
            server_deps = getattr(asset, 'server_dependencies', []) or []
            if server_deps:
                dependency_stats["server_dependencies"] += len(server_deps)
                dependency_stats["total_dependencies"] += len(server_deps)
            
            # Count database dependencies
            db_deps = getattr(asset, 'database_dependencies', []) or []
            if db_deps:
                dependency_stats["database_dependencies"] += len(db_deps)
                dependency_stats["total_dependencies"] += len(db_deps)
            
            # Identify complex dependency chains (assets with many dependencies)
            total_deps = len(app_deps) + len(server_deps) + len(db_deps)
            if total_deps > 5:
                dependency_stats["complex_dependency_chains"].append({
                    "asset_name": asset_name,
                    "total_dependencies": total_deps,
                    "types": {
                        "applications": len(app_deps),
                        "servers": len(server_deps),
                        "databases": len(db_deps)
                    }
                })
            
            # Identify orphaned assets (no dependencies)
            if total_deps == 0 and getattr(asset, 'asset_type', '') == 'Application':
                dependency_stats["orphaned_assets"].append(asset_name)
        
        return dependency_stats
    
    async def _generate_ai_insights(self, assets: List) -> Dict[str, Any]:
        """Generate AI-powered insights using CrewAI agents"""
        if not self.crewai_available:
            return {
                "available": False,
                "message": "AI insights not available - CrewAI service not initialized"
            }
        
        try:
            # Prepare asset data for AI analysis
            asset_data = []
            for asset in assets[:50]:  # Limit to 50 assets for AI analysis
                asset_data.append({
                    "asset_id": getattr(asset, 'asset_id', ''),
                    "asset_name": getattr(asset, 'asset_name', ''),
                    "asset_type": getattr(asset, 'asset_type', ''),
                    "environment": getattr(asset, 'environment', ''),
                    "business_criticality": getattr(asset, 'business_criticality', ''),
                    "assessment_readiness": getattr(asset, 'assessment_readiness', ''),
                    "completeness_score": getattr(asset, 'completeness_score', 0),
                    "quality_score": getattr(asset, 'quality_score', 0)
                })
            
            # Use Asset Intelligence Agent for analysis
            ai_result = await self.crewai_service.analyze_asset_inventory({
                "assets": asset_data,
                "operation": "readiness_assessment",
                "focus": "migration_assessment_preparation"
            })
            
            return {
                "available": True,
                "analysis_result": ai_result,
                "assets_analyzed": len(asset_data),
                "confidence_score": ai_result.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {
                "available": False,
                "error": str(e),
                "message": "AI insights generation failed"
            }
    
    def _generate_recommendations(self, assets: List, workflow_analysis: Dict, quality_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations for improving asset readiness"""
        recommendations = []
        
        # Workflow recommendations
        mapping_completion = workflow_analysis["completion_percentages"]["mapping"]
        if mapping_completion < 80:
            recommendations.append({
                "type": "workflow",
                "priority": "high",
                "title": "Complete Attribute Mapping",
                "description": f"Only {mapping_completion:.1f}% of assets have completed attribute mapping",
                "action": "Navigate to Attribute Mapping page and complete mapping for remaining assets",
                "affected_assets": workflow_analysis["mapping"]["pending"] + workflow_analysis["mapping"]["in_progress"]
            })
        
        # Data quality recommendations
        overall_quality = quality_analysis["overall_score"]
        if overall_quality < 70:
            recommendations.append({
                "type": "data_quality",
                "priority": "high",
                "title": "Improve Data Quality",
                "description": f"Overall data completeness is {overall_quality:.1f}%, below recommended 70%",
                "action": "Navigate to Data Cleansing page and address missing critical fields",
                "affected_assets": len(quality_analysis["missing_critical_data"])
            })
        
        # Critical field recommendations
        for field, completeness in quality_analysis["completeness_by_field"].items():
            if completeness < 50:
                recommendations.append({
                    "type": "critical_field",
                    "priority": "medium",
                    "title": f"Missing {field.replace('_', ' ').title()} Data",
                    "description": f"Only {completeness:.1f}% of assets have {field} populated",
                    "action": f"Focus on collecting {field} information during attribute mapping",
                    "field": field
                })
        
        return recommendations
    
    def _determine_assessment_readiness(self, workflow_analysis: Dict, quality_analysis: Dict) -> Dict[str, Any]:
        """Determine if the inventory is ready for assessment phase"""
        mapping_completion = workflow_analysis["completion_percentages"]["mapping"]
        cleanup_completion = workflow_analysis["completion_percentages"]["cleanup"]
        overall_quality = quality_analysis["overall_score"]
        
        # Criteria for assessment readiness
        mapping_threshold = 80  # 80% of assets should be mapped
        cleanup_threshold = 70  # 70% of assets should be cleaned
        quality_threshold = 70  # 70% overall data quality
        
        is_ready = (mapping_completion >= mapping_threshold and 
                   cleanup_completion >= cleanup_threshold and 
                   overall_quality >= quality_threshold)
        
        return {
            "ready": is_ready,
            "overall_score": (mapping_completion + cleanup_completion + overall_quality) / 3,
            "criteria": {
                "mapping_completion": {
                    "current": mapping_completion,
                    "required": mapping_threshold,
                    "met": mapping_completion >= mapping_threshold
                },
                "cleanup_completion": {
                    "current": cleanup_completion,
                    "required": cleanup_threshold,
                    "met": cleanup_completion >= cleanup_threshold
                },
                "data_quality": {
                    "current": overall_quality,
                    "required": quality_threshold,
                    "met": overall_quality >= quality_threshold
                }
            },
            "next_steps": self._get_next_steps(mapping_completion, cleanup_completion, overall_quality)
        }
    
    def _get_next_steps(self, mapping_completion: float, cleanup_completion: float, quality_score: float) -> List[str]:
        """Get specific next steps based on current state"""
        next_steps = []
        
        if mapping_completion < 80:
            next_steps.append("Complete attribute mapping for remaining assets")
        
        if cleanup_completion < 70:
            next_steps.append("Perform data cleansing to improve data quality")
        
        if quality_score < 70:
            next_steps.append("Fill in missing critical fields for key assets")
        
        if not next_steps:
            next_steps.append("Ready to proceed to Assessment phase!")
        
        return next_steps
    
    async def _update_asset_analysis_results(self, db: AsyncSession, assets: List, analysis_result: Dict[str, Any]):
        """Update asset analysis results in database"""
        try:
            for asset in assets:
                # Update AI analysis results
                asset.ai_analysis_result = analysis_result
                asset.last_ai_analysis = datetime.utcnow()
                
                # Update assessment readiness based on analysis
                if analysis_result.get("assessment_ready", {}).get("ready", False):
                    asset.assessment_readiness = "ready"
                elif analysis_result["data_quality"]["overall_score"] > 50:
                    asset.assessment_readiness = "partial"
                else:
                    asset.assessment_readiness = "not_ready"
            
            await db.commit()
            logger.info(f"Updated analysis results for {len(assets)} assets")
            
        except Exception as e:
            logger.error(f"Failed to update asset analysis results: {e}")
            await db.rollback()

# Global service instance
asset_intelligence_service = AssetIntelligenceService() 