"""
Asset handler for agent service layer asset management operations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class AssetHandler:
    """Handles asset management operations for the agent service layer."""
    
    def __init__(self, context: RequestContext):
        self.context = context
    
    async def get_discovered_assets(self, flow_id: str, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get discovered assets for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return []
                
                # Build query for assets
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id
                    )
                )
                
                # Apply asset type filter if specified
                if asset_type:
                    asset_query = asset_query.where(Asset.asset_type == asset_type)
                
                # Execute query
                result = await db.execute(asset_query)
                assets = result.scalars().all()
                
                # Convert to response format
                asset_list = []
                for asset in assets:
                    asset_data = {
                        "id": str(asset.id),
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "asset_subtype": getattr(asset, 'asset_subtype', None),
                        "status": asset.status,
                        "criticality": getattr(asset, 'criticality', 'medium'),
                        "quality_score": getattr(asset, 'quality_score', 0.0),
                        "confidence_score": getattr(asset, 'confidence_score', 0.0),
                        "validation_status": getattr(asset, 'validation_status', 'pending'),
                        "discovery_method": getattr(asset, 'discovery_method', 'unknown'),
                        "discovered_at": asset.created_at.isoformat() if asset.created_at else None,
                        "last_updated": asset.updated_at.isoformat() if asset.updated_at else None
                    }
                    asset_list.append(asset_data)
                
                return asset_list
                
            except Exception as e:
                logger.error(f"Database error in get_discovered_assets: {e}")
                raise
    
    async def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get asset dependencies for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "dependencies": {}
                    }
                
                # Get dependencies data from flow
                dependencies_data = getattr(flow, 'dependencies_data', {}) or {}
                
                # Get assets for context
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id
                    )
                )
                result = await db.execute(asset_query)
                assets = result.scalars().all()
                
                # Build dependency map
                dependency_map = {}
                orphaned_assets = []
                highly_connected_assets = []
                
                for asset in assets:
                    asset_id = str(asset.id)
                    asset_dependencies = dependencies_data.get(asset_id, {})
                    
                    dependency_info = {
                        "asset_id": asset_id,
                        "asset_name": asset.name,
                        "asset_type": asset.asset_type,
                        "depends_on": asset_dependencies.get("depends_on", []),
                        "depended_by": asset_dependencies.get("depended_by", []),
                        "dependency_count": len(asset_dependencies.get("depends_on", [])),
                        "dependent_count": len(asset_dependencies.get("depended_by", []))
                    }
                    
                    total_connections = dependency_info["dependency_count"] + dependency_info["dependent_count"]
                    
                    if total_connections == 0:
                        orphaned_assets.append(dependency_info)
                    elif total_connections > 5:
                        highly_connected_assets.append(dependency_info)
                    
                    dependency_map[asset_id] = dependency_info
                
                # Generate dependency analysis
                total_assets = len(assets)
                total_dependencies = sum(
                    len(dep_info.get("depends_on", [])) 
                    for dep_info in dependency_map.values()
                )
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "dependencies": dependency_map,
                    "analysis": {
                        "total_assets": total_assets,
                        "total_dependencies": total_dependencies,
                        "orphaned_assets": len(orphaned_assets),
                        "highly_connected_assets": len(highly_connected_assets),
                        "dependency_density": (total_dependencies / total_assets) if total_assets > 0 else 0
                    },
                    "insights": {
                        "orphaned_assets": orphaned_assets[:5],  # Top 5
                        "highly_connected_assets": highly_connected_assets[:5]  # Top 5
                    },
                    "metadata": {
                        "dependencies_completed": flow.dependencies_completed,
                        "analysis_timestamp": flow.updated_at.isoformat() if flow.updated_at else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in get_asset_dependencies: {e}")
                raise
    
    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "analysis": {}
                    }
                
                # Get tech debt data from flow
                tech_debt_data = getattr(flow, 'tech_debt_data', {}) or {}
                
                # Get assets for analysis
                asset_query = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.id,
                        Asset.client_account_id == self.context.client_account_id
                    )
                )
                result = await db.execute(asset_query)
                assets = result.scalars().all()
                
                # Analyze tech debt by asset
                tech_debt_by_asset = tech_debt_data.get("by_asset", {})
                high_debt_assets = []
                medium_debt_assets = []
                low_debt_assets = []
                
                debt_categories = {
                    "security": 0,
                    "performance": 0,
                    "maintainability": 0,
                    "compatibility": 0,
                    "compliance": 0
                }
                
                for asset in assets:
                    asset_id = str(asset.id)
                    asset_debt = tech_debt_by_asset.get(asset_id, {})
                    
                    debt_score = asset_debt.get("debt_score", 0)
                    debt_items = asset_debt.get("debt_items", [])
                    
                    asset_debt_info = {
                        "asset_id": asset_id,
                        "asset_name": asset.name,
                        "asset_type": asset.asset_type,
                        "debt_score": debt_score,
                        "debt_level": self._categorize_debt_level(debt_score),
                        "debt_items": debt_items,
                        "debt_count": len(debt_items)
                    }
                    
                    # Categorize by debt level
                    if debt_score >= 7:
                        high_debt_assets.append(asset_debt_info)
                    elif debt_score >= 4:
                        medium_debt_assets.append(asset_debt_info)
                    else:
                        low_debt_assets.append(asset_debt_info)
                    
                    # Count debt by category
                    for item in debt_items:
                        category = item.get("category", "other")
                        if category in debt_categories:
                            debt_categories[category] += 1
                
                # Calculate overall statistics
                total_debt_items = sum(len(asset_debt_by_asset.get(str(a.id), {}).get("debt_items", [])) for a in assets)
                avg_debt_score = sum(asset_debt_by_asset.get(str(a.id), {}).get("debt_score", 0) for a in assets) / len(assets) if assets else 0
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "analysis": {
                        "summary": {
                            "total_assets": len(assets),
                            "total_debt_items": total_debt_items,
                            "average_debt_score": round(avg_debt_score, 2),
                            "high_debt_assets": len(high_debt_assets),
                            "medium_debt_assets": len(medium_debt_assets),
                            "low_debt_assets": len(low_debt_assets)
                        },
                        "debt_by_category": debt_categories,
                        "assets_by_debt_level": {
                            "high": high_debt_assets,
                            "medium": medium_debt_assets,
                            "low": low_debt_assets
                        },
                        "top_issues": self._get_top_debt_issues(tech_debt_data),
                        "recommendations": self._generate_debt_recommendations(debt_categories, avg_debt_score)
                    },
                    "metadata": {
                        "tech_debt_completed": flow.tech_debt_completed,
                        "analysis_timestamp": flow.updated_at.isoformat() if flow.updated_at else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in get_tech_debt_analysis: {e}")
                raise
    
    async def validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        async with AsyncSessionLocal() as db:
            try:
                # Get asset
                asset_query = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == self.context.client_account_id
                    )
                )
                result = await db.execute(asset_query)
                asset = result.scalar_one_or_none()
                
                if not asset:
                    return {
                        "status": "error",
                        "error": "Asset not found",
                        "is_valid": False
                    }
                
                # Validate asset data
                validation_results = {
                    "required_fields": self._validate_required_fields(asset),
                    "data_quality": self._validate_data_quality(asset),
                    "consistency": self._validate_data_consistency(asset)
                }
                
                # Calculate overall validity
                field_validity = validation_results["required_fields"]["is_valid"]
                quality_validity = validation_results["data_quality"]["score"] >= 0.7
                consistency_validity = validation_results["consistency"]["is_consistent"]
                
                overall_valid = field_validity and quality_validity and consistency_validity
                
                # Generate recommendations
                recommendations = []
                if not field_validity:
                    recommendations.extend(validation_results["required_fields"]["recommendations"])
                if not quality_validity:
                    recommendations.extend(validation_results["data_quality"]["recommendations"])
                if not consistency_validity:
                    recommendations.extend(validation_results["consistency"]["recommendations"])
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "is_valid": overall_valid,
                    "validation_results": validation_results,
                    "recommendations": recommendations,
                    "validation_score": self._calculate_validation_score(validation_results)
                }
                
            except Exception as e:
                logger.error(f"Database error in validate_asset_data: {e}")
                raise
    
    async def get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get relationships for a specific asset"""
        async with AsyncSessionLocal() as db:
            try:
                # Get the target asset
                asset_query = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == self.context.client_account_id
                    )
                )
                result = await db.execute(asset_query)
                asset = result.scalar_one_or_none()
                
                if not asset:
                    return {
                        "status": "error",
                        "error": "Asset not found",
                        "relationships": {}
                    }
                
                # Initialize relationship categories
                relationships = {
                    "depends_on": [],
                    "dependents": [],
                    "related": []
                }
                
                # Get other assets in the same flow for relationship analysis
                flow_assets_stmt = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == asset.discovery_flow_id,
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.id != asset.id  # Exclude the target asset
                    )
                )
                
                flow_result = await db.execute(flow_assets_stmt)
                flow_assets = flow_result.scalars().all()
                
                # Basic relationship detection based on asset types and names
                for related_asset in flow_assets:
                    relationship_data = {
                        "id": str(related_asset.id),
                        "name": related_asset.name,
                        "type": related_asset.asset_type,
                        "relationship_type": "unknown"
                    }
                    
                    # Simple heuristics for relationship detection
                    if asset.asset_type == related_asset.asset_type:
                        relationship_data["relationship_type"] = "same_type"
                        relationships["related"].append(relationship_data)
                    elif "database" in asset.asset_type.lower() and "application" in related_asset.asset_type.lower():
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["dependents"].append(relationship_data)
                    elif "application" in asset.asset_type.lower() and "database" in related_asset.asset_type.lower():
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["depends_on"].append(relationship_data)
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                    "relationships": relationships,
                    "total_relationships": (
                        len(relationships["depends_on"]) + 
                        len(relationships["dependents"]) + 
                        len(relationships["related"])
                    ),
                    "relationship_summary": {
                        "dependencies": len(relationships["depends_on"]),
                        "dependents": len(relationships["dependents"]),
                        "related": len(relationships["related"])
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in get_asset_relationships: {e}")
                raise
    
    def _categorize_debt_level(self, debt_score: float) -> str:
        """Categorize debt level based on score"""
        if debt_score >= 7:
            return "high"
        elif debt_score >= 4:
            return "medium"
        else:
            return "low"
    
    def _get_top_debt_issues(self, tech_debt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top technical debt issues"""
        all_issues = tech_debt_data.get("top_issues", [])
        return sorted(all_issues, key=lambda x: x.get("severity", 0), reverse=True)[:10]
    
    def _generate_debt_recommendations(self, debt_categories: Dict[str, int], avg_debt_score: float) -> List[str]:
        """Generate recommendations based on debt analysis"""
        recommendations = []
        
        if avg_debt_score >= 7:
            recommendations.append("High technical debt detected - prioritize debt reduction before migration")
        elif avg_debt_score >= 4:
            recommendations.append("Moderate technical debt - plan debt reduction during migration")
        
        # Category-specific recommendations
        if debt_categories.get("security", 0) > 0:
            recommendations.append("Address security vulnerabilities before migration")
        if debt_categories.get("performance", 0) > 0:
            recommendations.append("Consider performance optimizations during migration")
        if debt_categories.get("compliance", 0) > 0:
            recommendations.append("Ensure compliance requirements are met in target environment")
        
        return recommendations
    
    def _validate_required_fields(self, asset: Asset) -> Dict[str, Any]:
        """Validate required fields for an asset"""
        required_fields = ["name", "asset_type"]
        missing_fields = []
        
        for field in required_fields:
            if not getattr(asset, field, None):
                missing_fields.append(field)
        
        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "recommendations": [f"Provide value for {field}" for field in missing_fields]
        }
    
    def _validate_data_quality(self, asset: Asset) -> Dict[str, Any]:
        """Validate data quality for an asset"""
        quality_score = getattr(asset, 'quality_score', 0.0)
        confidence_score = getattr(asset, 'confidence_score', 0.0)
        
        recommendations = []
        if quality_score < 0.7:
            recommendations.append("Improve data quality through validation and cleansing")
        if confidence_score < 0.7:
            recommendations.append("Increase confidence through additional data verification")
        
        return {
            "score": max(quality_score, confidence_score),
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "recommendations": recommendations
        }
    
    def _validate_data_consistency(self, asset: Asset) -> Dict[str, Any]:
        """Validate data consistency for an asset"""
        # Simple consistency checks
        is_consistent = True
        issues = []
        
        # Check name consistency
        if asset.name and len(asset.name.strip()) == 0:
            is_consistent = False
            issues.append("Asset name is empty or whitespace only")
        
        # Check type consistency
        if not asset.asset_type:
            is_consistent = False
            issues.append("Asset type is not specified")
        
        return {
            "is_consistent": is_consistent,
            "consistency_issues": issues,
            "recommendations": ["Fix " + issue.lower() for issue in issues]
        }
    
    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        field_score = 1.0 if validation_results["required_fields"]["is_valid"] else 0.0
        quality_score = validation_results["data_quality"]["score"]
        consistency_score = 1.0 if validation_results["consistency"]["is_consistent"] else 0.0
        
        return round((field_score + quality_score + consistency_score) / 3, 2)