"""
Asset Management Endpoints.
Handles asset CRUD operations and queries.
"""

import logging
import math
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
import pandas as pd

from app.api.v1.discovery.persistence import (
    get_processed_assets,
    update_asset_by_id,
    backup_processed_assets
)
from app.api.v1.discovery.serialization import clean_for_json_serialization

logger = logging.getLogger(__name__)

router = APIRouter()

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
    """
    try:
        # Get all processed assets
        all_assets = get_processed_assets()
        
        if not all_assets:
            return {
                "assets": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
        # Helper function to safely get numeric values
        def get_numeric_value(asset, field_names):
            for field_name in field_names:
                value = asset.get(field_name)
                if value is not None:
                    try:
                        if isinstance(value, str):
                            # Try to extract number from string
                            import re
                            match = re.search(r'(\d+(?:\.\d+)?)', str(value))
                            if match:
                                return float(match.group(1))
                            # Check for common text representations
                            value_lower = value.lower()
                            if value_lower in ['low', 'l']:
                                return 1
                            elif value_lower in ['medium', 'med', 'm']:
                                return 2
                            elif value_lower in ['high', 'h']:
                                return 3
                            elif value_lower in ['critical', 'crit', 'c']:
                                return 4
                        return float(value) if value not in ['', 'N/A', 'Unknown'] else None
                    except (ValueError, TypeError):
                        continue
            return None
        
        # Apply filters
        filtered_assets = []
        for asset in all_assets:
            # Asset type filter
            if asset_type and asset.get('asset_type', '').lower() != asset_type.lower():
                continue
            
            # Environment filter
            if environment and asset.get('environment', '').lower() != environment.lower():
                continue
            
            # Department filter
            if department and asset.get('department', '').lower() != department.lower():
                continue
            
            # Criticality filter
            if criticality and asset.get('criticality', '').lower() != criticality.lower():
                continue
            
            # Search filter (search in multiple fields)
            if search:
                search_lower = search.lower()
                searchable_fields = [
                    asset.get('hostname', ''),
                    asset.get('application_name', ''),
                    asset.get('department', ''),
                    asset.get('technology_stack', ''),
                    asset.get('operating_system', '')
                ]
                
                if not any(search_lower in str(field).lower() for field in searchable_fields):
                    continue
            
            filtered_assets.append(asset)
        
        # Calculate pagination
        total_assets = len(filtered_assets)
        total_pages = math.ceil(total_assets / page_size) if total_assets > 0 else 0
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Get page assets
        page_assets = filtered_assets[start_index:end_index]
        
        # Clean data for JSON serialization
        cleaned_assets = [clean_for_json_serialization(asset) for asset in page_assets]
        
        # Calculate summary statistics for the filtered set
        asset_types = {}
        environments = {}
        departments = {}
        
        for asset in filtered_assets:
            # Count asset types
            asset_type_val = asset.get('asset_type', 'Unknown')
            asset_types[asset_type_val] = asset_types.get(asset_type_val, 0) + 1
            
            # Count environments
            env_val = asset.get('environment', 'Unknown')
            environments[env_val] = environments.get(env_val, 0) + 1
            
            # Count departments
            dept_val = asset.get('department', 'Unknown')
            departments[dept_val] = departments.get(dept_val, 0) + 1
        
        return {
            "assets": cleaned_assets,
            "total": total_assets,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "summary": {
                "asset_types": asset_types,
                "environments": environments,
                "departments": departments,
                "total_by_type": {
                    "applications": sum(1 for a in filtered_assets if 'application' in a.get('asset_type', '').lower()),
                    "servers": sum(1 for a in filtered_assets if 'server' in a.get('asset_type', '').lower()),
                    "databases": sum(1 for a in filtered_assets if 'database' in a.get('asset_type', '').lower()),
                    "other": sum(1 for a in filtered_assets if not any(t in a.get('asset_type', '').lower() for t in ['application', 'server', 'database']))
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

@router.put("/assets/{asset_id}")
async def update_asset(asset_id: str, asset_data: Dict[str, Any]):
    """
    Update an existing asset.
    """
    try:
        # Add update timestamp
        asset_data['updated_timestamp'] = pd.Timestamp.now().isoformat()
        
        # Clean the data
        cleaned_data = clean_for_json_serialization(asset_data)
        
        # Update the asset
        success = update_asset_by_id(asset_id, cleaned_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        logger.info(f"Asset {asset_id} updated successfully")
        
        return {
            "status": "success",
            "message": f"Asset {asset_id} updated successfully",
            "asset_id": asset_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.post("/reprocess-assets")
async def reprocess_stored_assets():
    """
    Reprocess stored assets with updated algorithms.
    """
    try:
        all_assets = get_processed_assets()
        
        if not all_assets:
            return {
                "status": "success",
                "message": "No assets to reprocess",
                "processed_count": 0
            }
        
        reprocessed_count = 0
        
        for asset in all_assets:
            try:
                # Add reprocessing timestamp
                asset['reprocessed_timestamp'] = pd.Timestamp.now().isoformat()
                
                # You could add more sophisticated reprocessing logic here
                # For now, just update the timestamp
                
                reprocessed_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to reprocess asset {asset.get('id', 'unknown')}: {e}")
                continue
        
        # Backup the updated assets
        backup_processed_assets()
        
        logger.info(f"Reprocessed {reprocessed_count} assets")
        
        return {
            "status": "success",
            "message": f"Successfully reprocessed {reprocessed_count} assets",
            "processed_count": reprocessed_count,
            "total_assets": len(all_assets)
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess assets: {str(e)}")

@router.get("/applications")
async def get_applications_for_analysis():
    """
    Get applications formatted for 6R analysis.
    """
    try:
        all_assets = get_processed_assets()
        
        # Filter for applications and create analysis-ready format
        applications = []
        
        for asset in all_assets:
            asset_type = asset.get('asset_type', '').lower()
            
            # Include applications and services
            if 'application' in asset_type or 'service' in asset_type or asset.get('application_name'):
                
                # Get complexity score
                complexity_score = _calculate_complexity_score(asset)
                
                # Get business value score
                business_value = _get_business_value_score(asset)
                
                # Create application entry
                app_data = {
                    "id": asset.get('id'),
                    "name": asset.get('application_name') or asset.get('hostname', 'Unknown Application'),
                    "description": f"{asset.get('asset_type', 'Application')} - {asset.get('department', 'Unknown Department')}",
                    "department": asset.get('department', 'Unknown'),
                    "business_unit": asset.get('department', 'Unknown'),
                    "environment": asset.get('environment', 'Unknown'),
                    "criticality": asset.get('criticality', 'Medium'),
                    "technology_stack": asset.get('technology_stack', 'Unknown'),
                    "operating_system": asset.get('operating_system'),
                    "dependencies": asset.get('dependencies', ''),
                    "data_sensitivity": _assess_data_sensitivity(asset),
                    "compliance_requirements": _assess_compliance_requirements(asset),
                    "complexity_score": complexity_score,
                    "business_value_score": business_value,
                    "migration_readiness": asset.get('six_r_readiness', 'Unknown'),
                    "estimated_migration_effort": asset.get('migration_complexity', 'Unknown'),
                    "technical_debt": _assess_technical_debt(asset),
                    "modernization_potential": _assess_modernization_potential(asset),
                    "cloud_readiness": _assess_cloud_readiness(asset),
                    "tags": _generate_application_tags(asset),
                    "created_date": asset.get('processed_timestamp'),
                    "last_updated": asset.get('updated_timestamp', asset.get('processed_timestamp')),
                    "source": asset.get('discovery_source', 'cmdb_import')
                }
                
                applications.append(clean_for_json_serialization(app_data))
        
        # Sort by business value and complexity for better UX
        applications.sort(key=lambda x: (x.get('business_value_score', 0), x.get('complexity_score', 0)), reverse=True)
        
        logger.info(f"Retrieved {len(applications)} applications for analysis")
        
        return {
            "applications": applications,
            "total_count": len(applications),
            "summary": {
                "by_department": _group_by_field(applications, 'department'),
                "by_environment": _group_by_field(applications, 'environment'),
                "by_criticality": _group_by_field(applications, 'criticality'),
                "by_technology": _extract_technology_distribution(applications),
                "complexity_distribution": _get_complexity_distribution(applications),
                "readiness_distribution": _group_by_field(applications, 'migration_readiness')
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving applications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve applications: {str(e)}")

# Helper functions
def _calculate_complexity_score(asset: Dict[str, Any]) -> int:
    """Calculate complexity score based on asset attributes."""
    score = 1  # Base score
    
    # Technology stack complexity
    tech_stack = asset.get('technology_stack', '').lower()
    if any(keyword in tech_stack for keyword in ['legacy', 'mainframe', 'cobol', 'fortran']):
        score += 3
    elif any(keyword in tech_stack for keyword in ['java', '.net', 'python', 'node']):
        score += 1
    
    # Dependencies
    dependencies = asset.get('dependencies', '')
    if dependencies and len(dependencies) > 50:  # Assuming complex dependencies
        score += 2
    elif dependencies:
        score += 1
    
    # Environment complexity
    env = asset.get('environment', '').lower()
    if env == 'production':
        score += 2
    
    return min(score, 5)  # Cap at 5

def _get_business_value_score(asset: Dict[str, Any]) -> int:
    """Get business value score based on criticality and department."""
    criticality = asset.get('criticality', '').lower()
    
    if criticality in ['critical', 'high']:
        return 5
    elif criticality in ['medium', 'moderate']:
        return 3
    elif criticality in ['low']:
        return 1
    else:
        return 2  # Default

def _assess_data_sensitivity(asset: Dict[str, Any]) -> str:
    """Assess data sensitivity level."""
    app_name = asset.get('application_name', '').lower()
    dept = asset.get('department', '').lower()
    
    if any(keyword in app_name + dept for keyword in ['payment', 'financial', 'pii', 'gdpr', 'hipaa']):
        return 'High'
    elif any(keyword in app_name + dept for keyword in ['customer', 'user', 'personal']):
        return 'Medium'
    else:
        return 'Low'

def _assess_compliance_requirements(asset: Dict[str, Any]) -> List[str]:
    """Assess compliance requirements."""
    requirements = []
    app_name = asset.get('application_name', '').lower()
    dept = asset.get('department', '').lower()
    
    combined_text = app_name + dept
    
    if any(keyword in combined_text for keyword in ['payment', 'financial', 'bank']):
        requirements.extend(['PCI-DSS', 'SOX'])
    if any(keyword in combined_text for keyword in ['health', 'medical', 'patient']):
        requirements.append('HIPAA')
    if any(keyword in combined_text for keyword in ['eu', 'europe', 'gdpr']):
        requirements.append('GDPR')
    
    return requirements or ['General']

def _assess_technical_debt(asset: Dict[str, Any]) -> str:
    """Assess technical debt level."""
    tech_stack = asset.get('technology_stack', '').lower()
    
    if any(keyword in tech_stack for keyword in ['legacy', 'mainframe', 'cobol', 'vb6']):
        return 'High'
    elif any(keyword in tech_stack for keyword in ['java 8', '.net framework', 'php 5']):
        return 'Medium'
    else:
        return 'Low'

def _assess_modernization_potential(asset: Dict[str, Any]) -> str:
    """Assess modernization potential."""
    tech_stack = asset.get('technology_stack', '').lower()
    complexity = _calculate_complexity_score(asset)
    
    if complexity <= 2 and any(keyword in tech_stack for keyword in ['java', 'python', '.net core', 'node']):
        return 'High'
    elif complexity <= 3:
        return 'Medium'
    else:
        return 'Low'

def _assess_cloud_readiness(asset: Dict[str, Any]) -> str:
    """Assess cloud readiness."""
    tech_stack = asset.get('technology_stack', '').lower()
    dependencies = asset.get('dependencies', '')
    
    if any(keyword in tech_stack for keyword in ['microservice', 'container', 'docker', 'kubernetes']):
        return 'High'
    elif not dependencies or len(dependencies) < 30:
        return 'Medium'
    else:
        return 'Low'

def _generate_application_tags(asset: Dict[str, Any]) -> List[str]:
    """Generate tags for the application."""
    tags = []
    
    # Environment tag
    env = asset.get('environment')
    if env:
        tags.append(f"env:{env.lower()}")
    
    # Department tag
    dept = asset.get('department')
    if dept:
        tags.append(f"dept:{dept.lower().replace(' ', '-')}")
    
    # Technology tags
    tech_stack = asset.get('technology_stack', '').lower()
    for tech in ['java', 'python', '.net', 'php', 'node', 'docker', 'kubernetes']:
        if tech in tech_stack:
            tags.append(f"tech:{tech}")
    
    # Criticality tag
    criticality = asset.get('criticality')
    if criticality:
        tags.append(f"criticality:{criticality.lower()}")
    
    return tags

def _group_by_field(items: List[Dict], field: str) -> Dict[str, int]:
    """Group items by a specific field."""
    groups = {}
    for item in items:
        value = item.get(field, 'Unknown')
        groups[value] = groups.get(value, 0) + 1
    return groups

def _extract_technology_distribution(applications: List[Dict]) -> Dict[str, int]:
    """Extract technology distribution from applications."""
    tech_count = {}
    
    for app in applications:
        tech_stack = app.get('technology_stack', '').lower()
        
        # Count common technologies
        technologies = ['java', 'python', '.net', 'php', 'javascript', 'node', 'react', 'angular', 'vue']
        for tech in technologies:
            if tech in tech_stack:
                tech_count[tech] = tech_count.get(tech, 0) + 1
    
    return tech_count

def _get_complexity_distribution(applications: List[Dict]) -> Dict[str, int]:
    """Get complexity distribution."""
    distribution = {'Low (1-2)': 0, 'Medium (3)': 0, 'High (4-5)': 0}
    
    for app in applications:
        score = app.get('complexity_score', 1)
        if score <= 2:
            distribution['Low (1-2)'] += 1
        elif score == 3:
            distribution['Medium (3)'] += 1
        else:
            distribution['High (4-5)'] += 1
    
    return distribution 