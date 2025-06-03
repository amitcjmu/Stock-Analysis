"""
Asset Management - Modular & Robust
Combines robust error handling with clean modular architecture.
Enhanced with multi-tenant context awareness and session management.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context
from app.repositories.session_aware_repository import create_session_aware_repository
from app.models.cmdb_asset import CMDBAsset

from .asset_handlers import (
    AssetCRUDHandler,
    AssetProcessingHandler,
    AssetValidationHandler,
    AssetAnalysisHandler,
    AssetUtilsHandler
)

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Initialize handlers
crud_handler = AssetCRUDHandler()
processing_handler = AssetProcessingHandler()
validation_handler = AssetValidationHandler()
analysis_handler = AssetAnalysisHandler()
utils_handler = AssetUtilsHandler()

# Request models
class BulkUpdateRequest(BaseModel):
    asset_ids: List[str]
    updates: Dict[str, Any]

class BulkDeleteRequest(BaseModel):
    asset_ids: List[str]

@router.get("/health")
async def asset_management_health_check():
    """Health check endpoint for asset management module."""
    return {
        "status": "healthy",
        "module": "asset-management",
        "version": "2.0.0",
        "components": {
            "crud": crud_handler.is_available(),
            "processing": processing_handler.is_available(),
            "validation": validation_handler.is_available(),
            "analysis": analysis_handler.is_available(),
            "utils": utils_handler.is_available()
        },
        "multi_tenant_features": {
            "context_aware_repositories": True,
            "session_management": True,
            "engagement_deduplication": True
        }
    }

@router.get("/assets")
async def get_processed_assets_paginated(
    page: int = 1,
    page_size: int = 50,
    asset_type: str = None,
    environment: str = None,
    department: str = None,
    criticality: str = None,
    search: str = None,
    view_mode: str = "engagement_view",  # "session_view" or "engagement_view"
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated processed assets with filtering capabilities.
    Enhanced with agentic intelligence and multi-tenant context awareness.
    """
    try:
        context = get_current_context()
        
        # Use session-aware repository for context-aware data access
        asset_repo = create_session_aware_repository(db, CMDBAsset, view_mode=view_mode)
        
        # Build filters for repository query
        filters = {}
        if asset_type:
            filters['asset_type'] = asset_type
        if environment:
            filters['environment'] = environment
        if department:
            filters['department'] = department
        if criticality:
            filters['criticality'] = criticality
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get assets from context-aware repository
        assets = await asset_repo.get_by_filters(**filters)
        
        # If no assets found, provide demo data for development
        if not assets and not filters:
            logger.info("No assets found in repository, providing demo data for development")
            demo_assets = await _get_demo_assets()
            assets = demo_assets
        
        # Apply search filter if provided (simple text search)
        if search:
            search_lower = search.lower()
            assets = [
                asset for asset in assets 
                if (asset.hostname and search_lower in asset.hostname.lower()) or
                   (asset.description and search_lower in asset.description.lower()) or
                   (asset.asset_type and search_lower in asset.asset_type.lower())
            ]
        
        # Apply pagination
        total_assets = len(assets)
        paginated_assets = assets[offset:offset + page_size]
        
        # Convert to dict format expected by existing handlers
        asset_dicts = []
        for asset in paginated_assets:
            asset_dict = {
                "id": str(asset.id),
                "hostname": asset.hostname,
                "ip_address": asset.ip_address,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "department": asset.department,
                "criticality": asset.criticality,
                "operating_system": asset.operating_system,
                "cpu_cores": asset.cpu_cores,
                "memory_gb": asset.memory_gb,
                "storage_gb": asset.storage_gb,
                "location": asset.location,
                "owner": asset.owner,
                "business_service": asset.business_service,
                "technical_service": asset.technical_service,
                "support_group": asset.support_group,
                "cost_center": asset.cost_center,
                "lifecycle_status": asset.lifecycle_status,
                "compliance_zone": asset.compliance_zone,
                "backup_required": asset.backup_required,
                "dr_tier": asset.dr_tier,
                "session_id": asset.session_id,
                "created_at": asset.created_at.isoformat() if asset.created_at else None,
                "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
            }
            asset_dicts.append(asset_dict)
        
        # Build result with context-aware pagination
        result = {
            "assets": asset_dicts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_assets": total_assets,
                "total_pages": (total_assets + page_size - 1) // page_size,
                "has_next": offset + page_size < total_assets,
                "has_previous": page > 1
            },
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "session_id": context.session_id,
                "view_mode": view_mode
            },
            "filters_applied": {
                "asset_type": asset_type,
                "environment": environment,
                "department": department,
                "criticality": criticality,
                "search": search
            }
        }
        
        # Enhance with agentic intelligence if available
        try:
            from app.services.crewai_service_modular import crewai_service
            if crewai_service.is_available() and result.get("assets"):
                # Add agentic enhancement metadata
                result["enhanced_capabilities"] = {
                    "intelligent_analysis": "Available via agentic asset intelligence",
                    "auto_classification": "AI-powered asset classification available",
                    "bulk_operations": "Intelligent bulk operation planning available",
                    "continuous_learning": "System learns from user interactions",
                    "agentic_framework_active": True,
                    "context_aware_deduplication": f"Using {view_mode} with engagement-level intelligence"
                }
                
                # Add intelligence status for UI
                result["intelligence_status"] = {
                    "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                    "field_mapping_intelligence": hasattr(crewai_service, 'field_mapping_tool'),
                    "learning_system": hasattr(crewai_service, 'memory'),
                    "session_management": True,
                    "multi_tenant_isolation": True
                }
                
                logger.info(f"Enhanced asset response with agentic intelligence for {len(result.get('assets', []))} assets (context: {context.client_account_id})")
        
        except ImportError:
            logger.info("CrewAI service not available, using standard asset response")
        except Exception as e:
            logger.warning(f"Failed to enhance with agentic intelligence: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_processed_assets_paginated: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

@router.put("/assets/bulk")
async def bulk_update_assets_endpoint(request: Request):
    """
    Bulk update multiple assets.
    """
    try:
        request_body = await request.json()
        result = await crud_handler.bulk_update_assets(request_body)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk update failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_update_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk update assets: {str(e)}")

@router.delete("/assets/bulk")
async def bulk_delete_assets_endpoint(request: BulkDeleteRequest):
    """
    Bulk delete multiple assets.
    """
    try:
        result = await crud_handler.bulk_delete_assets(request.asset_ids)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Bulk delete failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk_delete_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete assets: {str(e)}")

@router.put("/assets/{asset_id}")
async def update_asset(asset_id: str, asset_data: Dict[str, Any]):
    """
    Update an existing asset.
    """
    try:
        result = await crud_handler.update_asset(asset_id, asset_data)
        
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                raise HTTPException(status_code=404, detail=result.get("message"))
            else:
                raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_asset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.post("/reprocess-assets")
async def reprocess_stored_assets():
    """
    Reprocess stored assets with updated algorithms.
    """
    try:
        result = await processing_handler.reprocess_stored_assets()
        return result
        
    except Exception as e:
        logger.error(f"Error in reprocess_stored_assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess assets: {str(e)}")

@router.get("/applications")
async def get_applications_for_analysis():
    """
    Get applications data specially formatted for 6R analysis.
    """
    try:
        result = await processing_handler.get_applications_for_analysis()
        return result
        
    except Exception as e:
        logger.error(f"Error in get_applications_for_analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get applications: {str(e)}")

@router.get("/assets/duplicates")
async def find_duplicate_assets_endpoint():
    """Find potential duplicate assets in the inventory."""
    try:
        result = await crud_handler.find_duplicates()
        return result
        
    except Exception as e:
        logger.error(f"Error in find_duplicate_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find duplicates: {str(e)}")

@router.post("/assets/cleanup-duplicates")
async def cleanup_duplicate_assets_endpoint():
    """Remove duplicate assets from the inventory."""
    try:
        result = await crud_handler.cleanup_duplicates()
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_duplicate_assets_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup duplicates: {str(e)}")

@router.get("/data-issues")
async def get_data_issues():
    """
    Get comprehensive data quality analysis optimized for 3-section UI.
    """
    try:
        result = await analysis_handler.get_data_issues()
        return result
        
    except Exception as e:
        logger.error(f"Error in get_data_issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze data issues: {str(e)}")

@router.post("/validate-data")
async def validate_data():
    """
    Validate asset data and return validation results.
    """
    try:
        result = await validation_handler.validate_data()
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data: {str(e)}")

@router.post("/data-issues/{issue_id}/approve")
async def approve_data_issue(issue_id: str):
    """
    Approve a data issue resolution.
    """
    try:
        result = await validation_handler.approve_data_issue(issue_id)
        return result
        
    except Exception as e:
        logger.error(f"Error in approve_data_issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve data issue: {str(e)}")

@router.post("/data-issues/{issue_id}/reject")
async def reject_data_issue(issue_id: str, request: Request):
    """
    Reject a data issue resolution.
    """
    try:
        request_body = await request.json()
        rejection_reason = request_body.get("reason", "No reason provided")
        
        result = await validation_handler.reject_data_issue(issue_id, rejection_reason)
        return result
        
    except Exception as e:
        logger.error(f"Error in reject_data_issue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject data issue: {str(e)}")

# Legacy endpoints for backward compatibility
@router.get("/legacy/summary")
async def get_legacy_summary():
    """
    Legacy summary endpoint for backward compatibility.
    """
    try:
        # Use CRUD handler to get basic asset count
        params = {'page': 1, 'page_size': 1}
        result = await crud_handler.get_assets_paginated(params)
        
        return {
            "status": "success", 
            "total_assets": result.get("total", 0),
            "summary": result.get("summary", {}),
            "note": "This is a legacy endpoint. Please use /assets for full functionality."
        }
        
    except Exception as e:
        logger.error(f"Error in get_legacy_summary: {e}")
        return {
            "status": "error",
            "total_assets": 0,
            "summary": {},
            "error": str(e)
        }

# Enhanced Agentic Asset Intelligence Endpoints 🆕
@router.post("/assets/analyze")
async def analyze_assets_with_intelligence(request: Request):
    """
    Use Asset Intelligence Agent to analyze asset patterns and provide recommendations.
    Integrates with the existing discovery workflow.
    """
    try:
        from app.services.crewai_service_modular import crewai_service
        
        if not crewai_service.is_available():
            # Fallback to traditional analysis
            return await analysis_handler.get_data_issues()
        
        request_body = await request.json()
        asset_ids = request_body.get('asset_ids', [])
        operation = request_body.get('operation', 'pattern_analysis')
        
        # Get assets from CRUD handler first
        if asset_ids:
            assets_data = []
            for asset_id in asset_ids:
                try:
                    asset = await crud_handler.get_asset_by_id(asset_id)
                    if asset:
                        assets_data.append(asset)
                except:
                    pass  # Skip missing assets
        else:
            # Get sample of assets for analysis
            params = {'page': 1, 'page_size': 50}
            result = await crud_handler.get_assets_paginated(params)
            assets_data = result.get('assets', [])
        
        # Use Asset Intelligence Agent for analysis
        inventory_data = {
            "assets": assets_data,
            "operation": operation,
            "include_patterns": request_body.get('include_patterns', True),
            "include_quality_assessment": request_body.get('include_quality_assessment', True),
            "total_asset_count": len(assets_data)
        }
        
        analysis_result = await crewai_service.analyze_asset_inventory(inventory_data)
        
        # Enhance result with discovery context
        analysis_result.update({
            "discovery_integration": True,
            "assets_analyzed": len(assets_data),
            "endpoint": "/api/v1/discovery/assets/analyze"
        })
        
        return analysis_result
        
    except ImportError:
        logger.info("CrewAI service not available, falling back to traditional analysis")
        return await analysis_handler.get_data_issues()
    except Exception as e:
        logger.error(f"Asset intelligence analysis failed: {e}")
        # Fallback to traditional analysis
        return await analysis_handler.get_data_issues()

@router.post("/assets/auto-classify")
async def auto_classify_assets_with_intelligence(request: Request):
    """
    Use Asset Intelligence Agent for automatic asset classification.
    """
    try:
        from app.services.crewai_service_modular import crewai_service
        
        if not crewai_service.is_available():
            return {"status": "ai_not_available", "message": "AI classification not available"}
        
        request_body = await request.json()
        asset_ids = request_body.get('asset_ids', [])
        
        # Get assets from CRUD handler
        assets_data = []
        for asset_id in asset_ids:
            try:
                asset = await crud_handler.get_asset_by_id(asset_id)
                if asset:
                    assets_data.append(asset)
            except:
                pass  # Skip missing assets
        
        if not assets_data:
            return {"status": "no_assets", "message": "No assets found for classification"}
        
        # Use Asset Intelligence Agent for classification
        classification_data = {
            "asset_ids": asset_ids,
            "assets": assets_data,
            "use_learned_patterns": request_body.get('use_learned_patterns', True),
            "confidence_threshold": request_body.get('confidence_threshold', 0.8)
        }
        
        classification_result = await crewai_service.classify_assets(classification_data)
        
        # Enhance result with discovery context
        classification_result.update({
            "discovery_integration": True,
            "endpoint": "/api/v1/discovery/assets/auto-classify"
        })
        
        return classification_result
        
    except ImportError:
        return {"status": "ai_not_available", "message": "AI classification not available"}
    except Exception as e:
        logger.error(f"Asset auto-classification failed: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/assets/intelligence-status")
async def get_asset_intelligence_status():
    """Get the status of asset intelligence capabilities."""
    try:
        # Check if CrewAI service is available
        intelligence_status = {
            "crewai_available": False,
            "asset_intelligence_agent": False,
            "field_mapping_intelligence": False,
            "learning_system": False,
            "total_experiences": 0
        }
        
        try:
            from app.services.crewai_service_modular import crewai_service
            if crewai_service.is_available():
                intelligence_status["crewai_available"] = True
                intelligence_status["asset_intelligence_agent"] = "asset_intelligence" in (crewai_service.agents or {})
                intelligence_status["field_mapping_intelligence"] = hasattr(crewai_service, 'field_mapping_tool')
                intelligence_status["learning_system"] = hasattr(crewai_service, 'memory')
                
                if hasattr(crewai_service, 'memory') and crewai_service.memory:
                    intelligence_status["total_experiences"] = len(crewai_service.memory.experiences)
        except ImportError:
            pass
        
        return {
            "status": "success",
            "intelligence": intelligence_status,
            "capabilities": {
                "asset_classification": "Basic pattern matching available",
                "ai_enhancement": "CrewAI service available" if intelligence_status["crewai_available"] else "Limited to rule-based processing",
                "learning": "Active learning from user feedback" if intelligence_status["learning_system"] else "Static rules only"
            }
        }
    
    except Exception as e:
        logger.error(f"Error in get_asset_intelligence_status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get intelligence status: {str(e)}")

@router.get("/assets/discovery-metrics")
async def get_discovery_metrics():
    """Get discovery metrics for the dashboard overview."""
    try:
        # Get basic asset counts
        assets_result = await crud_handler.get_assets_paginated({'page': 1, 'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        # Calculate metrics
        total_assets = len(assets)
        applications = [a for a in assets if a.get('asset_type') == 'application']
        servers = [a for a in assets if a.get('asset_type') == 'server']
        
        # App-to-server mapping calculation
        app_mapping_percentage = 0
        if applications:
            mapped_apps = [a for a in applications if a.get('hostname') or a.get('ip_address')]
            app_mapping_percentage = int((len(mapped_apps) / len(applications)) * 100)
        
        # Data quality assessment
        complete_assets = [a for a in assets if all([
            a.get('name'),
            a.get('asset_type'),
            a.get('environment', '').strip(),
            a.get('department', '').strip()
        ])]
        data_quality = int((len(complete_assets) / total_assets * 100)) if total_assets > 0 else 0
        
        # Tech debt items (assets with missing or outdated info)
        tech_debt_items = total_assets - len(complete_assets)
        
        # Critical issues (high risk or end-of-life items)
        critical_issues = len([a for a in assets if 
            a.get('criticality') == 'High' or 
            a.get('support_status') == 'End of Life' or
            a.get('operating_system', '').lower() in ['windows server 2008', 'windows server 2012', 'centos 6', 'rhel 6']
        ])
        
        return {
            "status": "success",
            "metrics": {
                "totalAssets": total_assets,
                "totalApplications": len(applications),
                "applicationToServerMapping": app_mapping_percentage,
                "dependencyMappingComplete": min(75, app_mapping_percentage + 10),  # Estimate based on app mapping
                "techDebtItems": tech_debt_items,
                "criticalIssues": critical_issues,
                "discoveryCompleteness": data_quality,
                "dataQuality": data_quality
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_discovery_metrics: {e}")
        # Return demo data if there's an error
        return {
            "status": "success",
            "metrics": {
                "totalAssets": 0,
                "totalApplications": 0,
                "applicationToServerMapping": 0,
                "dependencyMappingComplete": 0,
                "techDebtItems": 0,
                "criticalIssues": 0,
                "discoveryCompleteness": 0,
                "dataQuality": 0
            }
        }

@router.get("/assets/application-landscape")
async def get_application_landscape():
    """Get application landscape data for dashboard analysis."""
    try:
        # Get applications
        assets_result = await crud_handler.get_assets_paginated({'asset_type': 'application', 'page_size': 1000})
        applications = assets_result.get('assets', [])
        
        # Transform applications for landscape view
        landscape_apps = []
        for app in applications:
            # Calculate cloud readiness score
            cloud_readiness = 50  # Base score
            
            # Boost for modern OS
            if app.get('operating_system'):
                os = app.get('operating_system', '').lower()
                if any(modern in os for modern in ['2019', '2022', 'ubuntu 20', 'ubuntu 22', 'rhel 8', 'rhel 9']):
                    cloud_readiness += 30
                elif any(legacy in os for legacy in ['2008', '2012', 'centos 6', 'rhel 6']):
                    cloud_readiness -= 20
            
            # Boost for containerized or cloud-native tech stack
            tech_stack = []
            if app.get('technology_stack'):
                tech_stack = app.get('technology_stack', '').split(',')
                cloud_readiness += min(20, len(tech_stack) * 5)
            
            landscape_apps.append({
                "id": app.get('id', ''),
                "name": app.get('name', 'Unknown'),
                "environment": app.get('environment', 'Unknown'),
                "criticality": app.get('criticality', 'Medium'),
                "techStack": tech_stack,
                "serverCount": 1 if app.get('hostname') else 0,
                "databaseCount": 1 if 'database' in app.get('name', '').lower() else 0,
                "dependencyCount": app.get('dependency_count', 0),
                "techDebtScore": max(0, 100 - cloud_readiness),
                "cloudReadiness": min(100, cloud_readiness)
            })
        
        # Calculate summaries
        summary = {
            "byEnvironment": {},
            "byCriticality": {},
            "byTechStack": {}
        }
        
        for app in landscape_apps:
            # By environment
            env = app["environment"]
            summary["byEnvironment"][env] = summary["byEnvironment"].get(env, 0) + 1
            
            # By criticality
            crit = app["criticality"]
            summary["byCriticality"][crit] = summary["byCriticality"].get(crit, 0) + 1
            
            # By tech stack
            for tech in app["techStack"]:
                tech = tech.strip()
                if tech:
                    summary["byTechStack"][tech] = summary["byTechStack"].get(tech, 0) + 1
        
        return {
            "status": "success",
            "landscape": {
                "applications": landscape_apps,
                "summary": summary
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_application_landscape: {e}")
        # Return empty landscape if there's an error
        return {
            "status": "success",
            "landscape": {
                "applications": [],
                "summary": {
                    "byEnvironment": {},
                    "byCriticality": {},
                    "byTechStack": {}
                }
            }
        }

@router.get("/assets/infrastructure-landscape")
async def get_infrastructure_landscape():
    """Get infrastructure landscape data for dashboard analysis."""
    try:
        # Get all assets
        assets_result = await crud_handler.get_assets_paginated({'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        # Analyze servers
        servers = [a for a in assets if a.get('asset_type') in ['server', 'virtual_machine', 'physical_server']]
        physical_servers = [s for s in servers if s.get('deployment_type') == 'Physical']
        virtual_servers = [s for s in servers if s.get('deployment_type') in ['Virtual', 'VM']]
        cloud_servers = [s for s in servers if s.get('deployment_type') == 'Cloud']
        
        # OS Support analysis
        supported_os = []
        deprecated_os = []
        
        for server in servers:
            os = server.get('operating_system', '').lower()
            if any(modern in os for modern in ['2019', '2022', 'ubuntu 20', 'ubuntu 22', 'rhel 8', 'rhel 9']):
                supported_os.append(server)
            elif any(legacy in os for legacy in ['2008', '2012', 'centos 6', 'rhel 6']):
                deprecated_os.append(server)
        
        # Analyze databases
        databases = [a for a in assets if 'database' in a.get('asset_type', '').lower() or 'database' in a.get('name', '').lower()]
        
        # Database version analysis
        supported_db_versions = []
        deprecated_db_versions = []
        eol_db_versions = []
        
        for db in databases:
            version = db.get('version', '').lower()
            name = db.get('name', '').lower()
            
            # Simple version detection (would be enhanced with real version parsing)
            if any(modern in version for modern in ['2019', '2022', '8.0', '9.0', '13', '14', '15']):
                supported_db_versions.append(db)
            elif any(old in version for old in ['2012', '2014', '5.7', '10', '11']):
                deprecated_db_versions.append(db)
            elif any(eol in version for eol in ['2008', '5.6', '9.6']):
                eol_db_versions.append(db)
        
        # Network devices
        network_devices = [a for a in assets if a.get('asset_type') in ['network_device', 'router', 'switch', 'firewall']]
        security_devices = [a for a in assets if 'firewall' in a.get('asset_type', '').lower() or 'security' in a.get('name', '').lower()]
        storage_devices = [a for a in assets if 'storage' in a.get('asset_type', '').lower() or 'san' in a.get('name', '').lower()]
        
        return {
            "status": "success",
            "landscape": {
                "servers": {
                    "total": len(servers),
                    "physical": len(physical_servers),
                    "virtual": len(virtual_servers),
                    "cloud": len(cloud_servers),
                    "supportedOS": len(supported_os),
                    "deprecatedOS": len(deprecated_os)
                },
                "databases": {
                    "total": len(databases),
                    "supportedVersions": len(supported_db_versions),
                    "deprecatedVersions": len(deprecated_db_versions),
                    "endOfLife": len(eol_db_versions)
                },
                "networks": {
                    "devices": len(network_devices),
                    "securityDevices": len(security_devices),
                    "storageDevices": len(storage_devices)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_infrastructure_landscape: {e}")
        # Return empty landscape if there's an error
        return {
            "status": "success",
            "landscape": {
                "servers": {
                    "total": 0,
                    "physical": 0,
                    "virtual": 0,
                    "cloud": 0,
                    "supportedOS": 0,
                    "deprecatedOS": 0
                },
                "databases": {
                    "total": 0,
                    "supportedVersions": 0,
                    "deprecatedVersions": 0,
                    "endOfLife": 0
                },
                "networks": {
                    "devices": 0,
                    "securityDevices": 0,
                    "storageDevices": 0
                }
            }
        } 

@router.get("/assets/tech-debt-analysis")
async def get_tech_debt_analysis():
    """Get tech debt analysis using the Tech Debt Analysis Agent."""
    try:
        # Import the tech debt analysis agent
        from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent
        
        # Get all assets for analysis
        assets_result = await crud_handler.get_assets_paginated({'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "items": [],
                "summary": {
                    "totalItems": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "endOfLife": 0,
                    "deprecated": 0
                }
            }
        
        # Perform tech debt analysis
        tech_debt_intelligence = await tech_debt_analysis_agent.analyze_tech_debt(
            assets, 
            stakeholder_context={}, 
            migration_timeline="6-12 months"
        )
        
        # Extract and transform the tech debt items for frontend
        prioritized_debt = tech_debt_intelligence.get("prioritized_tech_debt", [])
        tech_debt_items = []
        summary = {
            "totalItems": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "endOfLife": 0,
            "deprecated": 0
        }
        
        for debt_item in prioritized_debt:
            # Extract risk item from prioritized debt structure
            risk_item = debt_item.get("risk_item", debt_item)  # Fallback to debt_item if no risk_item
            
            # Transform agent analysis to frontend format
            tech_debt_item = {
                "id": risk_item.get("id", f"debt_{len(tech_debt_items)}"),
                "assetId": risk_item.get("asset_id", ""),
                "assetName": risk_item.get("asset_name", "Unknown Asset"),
                "component": _map_component_type(risk_item.get("category", "os")),
                "technology": risk_item.get("technology", "Unknown"),
                "currentVersion": risk_item.get("current_version", "Unknown"),
                "latestVersion": risk_item.get("latest_version", "Unknown"),
                "supportStatus": _map_support_status(risk_item.get("support_status", "unknown")),
                "endOfLifeDate": risk_item.get("end_of_life_date"),
                "securityRisk": risk_item.get("risk_level", "medium"),
                "migrationEffort": risk_item.get("migration_effort", "medium"),
                "businessImpact": risk_item.get("business_impact", "medium"),
                "recommendedAction": risk_item.get("recommended_action", "Review and plan upgrade"),
                "dependencies": risk_item.get("dependencies", [])
            }
            
            tech_debt_items.append(tech_debt_item)
            
            # Update summary counts
            summary["totalItems"] += 1
            risk_level = tech_debt_item["securityRisk"]
            if risk_level in summary:
                summary[risk_level] += 1
            
            if tech_debt_item["supportStatus"] == "end_of_life":
                summary["endOfLife"] += 1
            elif tech_debt_item["supportStatus"] == "deprecated":
                summary["deprecated"] += 1
        
        return {
            "status": "success",
            "items": tech_debt_items,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error in tech debt analysis: {e}")
        return {
            "status": "error",
            "items": [],
            "summary": {
                "totalItems": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "endOfLife": 0,
                "deprecated": 0
            },
            "error": str(e)
        }

@router.get("/assets/support-timelines")
async def get_support_timelines():
    """Get technology support timelines."""
    try:
        # Import the tech debt analysis agent
        from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent
        
        # Get all assets for analysis
        assets_result = await crud_handler.get_assets_paginated({'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "timelines": []
            }
        
        # Perform tech debt analysis to get support timelines
        tech_debt_intelligence = await tech_debt_analysis_agent.analyze_tech_debt(
            assets, 
            stakeholder_context={}, 
            migration_timeline="6-12 months"
        )
        
        # Extract support timeline information
        os_analysis = tech_debt_intelligence.get("tech_debt_analysis", {}).get("os_analysis", {})
        app_analysis = tech_debt_intelligence.get("tech_debt_analysis", {}).get("application_analysis", {})
        
        support_timelines = []
        
        # Process OS timelines
        for os_info in os_analysis.get("os_inventory", {}).values():
            timeline = {
                "technology": f"{os_info.get('name', 'Unknown OS')}",
                "currentVersion": os_info.get("version", "Unknown"),
                "supportEnd": _calculate_support_end_date(os_info),
                "extendedSupportEnd": _calculate_extended_support_date(os_info),
                "replacementOptions": _get_os_replacement_options(os_info)
            }
            support_timelines.append(timeline)
        
        # Process Application timelines
        for app_info in app_analysis.get("application_inventory", {}).values():
            timeline = {
                "technology": f"{app_info.get('name', 'Unknown App')}",
                "currentVersion": app_info.get("version", "Unknown"),
                "supportEnd": _calculate_app_support_end_date(app_info),
                "replacementOptions": _get_app_replacement_options(app_info)
            }
            support_timelines.append(timeline)
        
        return {
            "status": "success",
            "timelines": support_timelines[:10]  # Limit to top 10 most critical
        }
        
    except Exception as e:
        logger.error(f"Error getting support timelines: {e}")
        return {
            "status": "error",
            "timelines": [],
            "error": str(e)
        }

def _map_component_type(category: str) -> str:
    """Map agent category to frontend component type."""
    mapping = {
        "operating_system": "os",
        "application_versions": "app",
        "infrastructure": "framework",
        "security": "framework",
        "database": "database",
        "web": "web"
    }
    return mapping.get(category, "os")

def _map_support_status(status: str) -> str:
    """Map agent support status to frontend format."""
    mapping = {
        "mainstream_support": "supported",
        "extended_support": "extended",
        "end_of_support": "deprecated",
        "end_of_life": "end_of_life"
    }
    return mapping.get(status, "deprecated")

def _calculate_support_end_date(os_info: dict) -> str:
    """Calculate OS support end date."""
    # This would typically use real OS lifecycle data
    # For now, provide reasonable estimates based on OS name and version
    os_name = os_info.get("name", "").lower()
    version = os_info.get("version", "")
    
    if "windows server 2012" in os_name or "2012" in version:
        return "2023-10-10"  # Already EOL
    elif "windows server 2016" in os_name or "2016" in version:
        return "2027-01-12"
    elif "windows server 2019" in os_name or "2019" in version:
        return "2029-01-09"
    elif "centos 7" in os_name:
        return "2024-06-30"
    elif "rhel 7" in os_name:
        return "2024-06-30"
    elif "rhel 8" in os_name:
        return "2029-05-31"
    else:
        return "2025-12-31"  # Default estimate

def _calculate_extended_support_date(os_info: dict) -> str:
    """Calculate extended support end date."""
    # Extended support typically 3-5 years after mainstream
    from datetime import datetime, timedelta
    try:
        support_end = datetime.strptime(_calculate_support_end_date(os_info), "%Y-%m-%d")
        extended_end = support_end + timedelta(days=1095)  # 3 years
        return extended_end.strftime("%Y-%m-%d")
    except:
        return "2028-12-31"

def _calculate_app_support_end_date(app_info: dict) -> str:
    """Calculate application support end date."""
    # This would use real application lifecycle data
    app_name = app_info.get("name", "").lower()
    version = app_info.get("version", "")
    
    if "java" in app_name and "8" in version:
        return "2025-03-31"  # Oracle Java 8 commercial support
    elif "java" in app_name and "11" in version:
        return "2026-09-30"
    elif ".net" in app_name and any(v in version for v in ["4.6", "4.7", "4.8"]):
        return "2025-04-26"
    else:
        return "2026-12-31"

def _get_os_replacement_options(os_info: dict) -> list:
    """Get OS replacement options."""
    os_name = os_info.get("name", "").lower()
    
    if "windows" in os_name:
        return ["Windows Server 2022", "Windows Server 2019", "Azure Windows VM"]
    elif "centos" in os_name or "rhel" in os_name:
        return ["RHEL 9", "Ubuntu 22.04 LTS", "Azure Linux"]
    elif "ubuntu" in os_name:
        return ["Ubuntu 22.04 LTS", "Ubuntu 20.04 LTS"]
    else:
        return ["Modern Linux Distribution", "Cloud-native OS"]

def _get_app_replacement_options(app_info: dict) -> list:
    """Get application replacement options."""
    app_name = app_info.get("name", "").lower()
    
    if "java" in app_name:
        return ["OpenJDK 17", "OpenJDK 21", "Azure Spring Apps"]
    elif ".net" in app_name:
        return [".NET 6", ".NET 8", "Azure App Service"]
    elif "database" in app_name:
        return ["PostgreSQL 15", "Azure SQL Database", "AWS RDS"]
    else:
        return ["Modern Alternative", "Cloud Service"]


async def _get_demo_assets():
    """Generate demo assets for development when no real data is available."""
    from datetime import datetime
    
    demo_data = [
        {
            "hostname": "web-server-01",
            "ip_address": "192.168.1.10",
            "asset_type": "Server",
            "environment": "Production",
            "department": "IT Operations",
            "criticality": "High",
            "operating_system": "Windows Server 2019",
            "cpu_cores": 4,
            "memory_gb": 16,
            "storage_gb": 500,
            "location": "DC1",
            "owner": "IT Operations Team"
        },
        {
            "hostname": "db-server-01", 
            "ip_address": "192.168.1.20",
            "asset_type": "Database",
            "environment": "Production",
            "department": "Database Team",
            "criticality": "Critical",
            "operating_system": "Linux",
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 2000,
            "location": "DC1",
            "owner": "Database Team"
        },
        {
            "hostname": "app-server-01",
            "ip_address": "192.168.1.30", 
            "asset_type": "Server",
            "environment": "Production",
            "department": "Engineering",
            "criticality": "Medium",
            "operating_system": "Ubuntu 20.04",
            "cpu_cores": 4,
            "memory_gb": 8,
            "storage_gb": 250,
            "location": "DC1",
            "owner": "Development Team"
        },
        {
            "hostname": "test-server-01",
            "ip_address": "192.168.2.10",
            "asset_type": "Server", 
            "environment": "Test",
            "department": "QA",
            "criticality": "Low",
            "operating_system": "Windows Server 2016",
            "cpu_cores": 2,
            "memory_gb": 8,
            "storage_gb": 100,
            "location": "DC2",
            "owner": "QA Team"
        },
        {
            "hostname": "backup-server-01",
            "ip_address": "192.168.1.40",
            "asset_type": "Storage Device",
            "environment": "Production", 
            "department": "IT Operations",
            "criticality": "High",
            "operating_system": "Linux",
            "cpu_cores": 2,
            "memory_gb": 4,
            "storage_gb": 5000,
            "location": "DC1",
            "owner": "Backup Team"
        }
    ]
    
    # Create mock asset objects
    demo_assets = []
    for i, data in enumerate(demo_data):
        # Create a mock asset object with required attributes
        class MockAsset:
            def __init__(self, **kwargs):
                self.id = i + 1
                self.hostname = kwargs.get('hostname')
                self.ip_address = kwargs.get('ip_address')
                self.asset_type = kwargs.get('asset_type')
                self.environment = kwargs.get('environment')
                self.department = kwargs.get('department')
                self.criticality = kwargs.get('criticality')
                self.operating_system = kwargs.get('operating_system')
                self.cpu_cores = kwargs.get('cpu_cores')
                self.memory_gb = kwargs.get('memory_gb')
                self.storage_gb = kwargs.get('storage_gb')
                self.location = kwargs.get('location')
                self.owner = kwargs.get('owner')
                self.business_service = None
                self.technical_service = None
                self.support_group = None
                self.cost_center = None
                self.lifecycle_status = "Active"
                self.compliance_zone = "Internal"
                self.backup_required = True
                self.dr_tier = "Tier 1" if kwargs.get('criticality') == 'Critical' else "Tier 2"
                self.session_id = "demo_session"
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                self.description = f"Demo {kwargs.get('asset_type', 'Asset')}"
        
        demo_assets.append(MockAsset(**data))
    
    return demo_assets