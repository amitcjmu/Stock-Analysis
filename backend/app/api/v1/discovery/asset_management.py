"""
Asset Management - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

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
    search: str = None
):
    """
    Get paginated processed assets with filtering capabilities.
    Enhanced with agentic intelligence and asset inventory management.
    """
    try:
        # First try to get assets using existing CRUD handler
        params = {
            'page': page,
            'page_size': page_size,
            'asset_type': asset_type,
            'environment': environment,
            'department': department,
            'criticality': criticality,
            'search': search
        }
        
        result = await crud_handler.get_assets_paginated(params)
        
        # Enhance with agentic intelligence if available
        try:
            from app.services.crewai_service import crewai_service
            if crewai_service.is_available() and result.get("assets"):
                # Add agentic enhancement metadata
                result["enhanced_capabilities"] = {
                    "intelligent_analysis": "Available via agentic asset intelligence",
                    "auto_classification": "AI-powered asset classification available",
                    "bulk_operations": "Intelligent bulk operation planning available",
                    "continuous_learning": "System learns from user interactions",
                    "agentic_framework_active": True
                }
                
                # Add intelligence status for UI
                result["intelligence_status"] = {
                    "asset_intelligence_agent": "asset_intelligence" in (crewai_service.agents or {}),
                    "field_mapping_intelligence": hasattr(crewai_service, 'field_mapping_tool'),
                    "learning_system": hasattr(crewai_service, 'memory')
                }
                
                logger.info(f"Enhanced asset response with agentic intelligence for {len(result.get('assets', []))} assets")
        
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
        from app.services.crewai_service import crewai_service
        
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
        from app.services.crewai_service import crewai_service
        
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
            from app.services.crewai_service import crewai_service
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