"""
Data Cleanup Service - Workflow Integrated
Handles data quality improvements and automatic workflow advancement.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCleanupService:
    """
    Service for data quality improvements with workflow integration.
    Automatically advances assets through cleanup phase when quality thresholds are met.
    """
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 90.0,
            "good": 75.0, 
            "acceptable": 60.0,
            "needs_work": 0.0
        }
        self.workflow_advancement_threshold = 70.0  # Quality score needed to advance workflow
        logger.info("Data cleanup service initialized")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of data cleanup service."""
        return {
            "status": "healthy",
            "service": "data-cleanup",
            "version": "1.0.0",
            "quality_thresholds": self.quality_thresholds,
            "workflow_threshold": self.workflow_advancement_threshold
        }
    
    async def process_data_cleanup_batch(self, asset_data: List[Dict[str, Any]], 
                                       cleanup_operations: List[str],
                                       client_account_id: Optional[str] = None,
                                       engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a batch of assets for data cleanup and advance workflow status.
        
        Args:
            asset_data: List of asset dictionaries to clean
            cleanup_operations: List of cleanup operations to perform
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping
            
        Returns:
            Cleanup results with workflow advancement status
        """
        try:
            cleanup_results = {
                "total_assets": len(asset_data),
                "successfully_cleaned": 0,
                "cleanup_errors": [],
                "workflow_updates": [],
                "quality_improvements": {},
                "cleanup_summary": {}
            }
            
            # Import workflow service for updates
            try:
                from app.services.workflow_service import WorkflowService
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as db:
                    workflow_service = WorkflowService(db, client_account_id, engagement_id)
                    
                    for asset in asset_data:
                        try:
                            # Calculate original quality score
                            original_quality = self._calculate_data_quality(asset)
                            
                            # Apply cleanup operations
                            cleaned_asset = self._apply_cleanup_operations(asset, cleanup_operations)
                            
                            # Calculate improved quality score
                            improved_quality = self._calculate_data_quality(cleaned_asset)
                            
                            # Track quality improvement
                            asset_id = asset.get('id', 'unknown')
                            cleanup_results["quality_improvements"][asset_id] = {
                                "original_quality": original_quality,
                                "improved_quality": improved_quality,
                                "improvement": improved_quality - original_quality,
                                "operations_applied": cleanup_operations
                            }
                            
                            # Update asset in database with improved data
                            if asset.get('id'):
                                await self._update_asset_with_cleaned_data(
                                    asset['id'], cleaned_asset, improved_quality, db, 
                                    client_account_id, engagement_id
                                )
                            
                            # Update workflow status if quality is good enough
                            if improved_quality >= self.workflow_advancement_threshold:
                                if asset.get('id'):
                                    workflow_update = await workflow_service.update_asset_workflow_status(
                                        asset['id'], {
                                            "cleanup_status": "completed",
                                            "quality_score": improved_quality
                                        }
                                    )
                                    cleanup_results["workflow_updates"].append({
                                        "asset_id": asset['id'],
                                        "workflow_update": workflow_update,
                                        "quality_score": improved_quality
                                    })
                            
                            cleanup_results["successfully_cleaned"] += 1
                            
                        except Exception as e:
                            logger.error(f"Error cleaning asset {asset.get('id', 'unknown')}: {e}")
                            cleanup_results["cleanup_errors"].append({
                                "asset_id": asset.get('id', 'unknown'),
                                "error": str(e)
                            })
                
                # Generate cleanup summary
                cleanup_results["cleanup_summary"] = self._generate_cleanup_summary(
                    cleanup_results["quality_improvements"]
                )
                
            except ImportError:
                logger.warning("Workflow service not available, proceeding without workflow updates")
                cleanup_results["workflow_updates"] = "not_available"
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error in process_data_cleanup_batch: {e}")
            return {
                "error": f"Batch cleanup failed: {str(e)}",
                "total_assets": len(asset_data) if asset_data else 0,
                "successfully_cleaned": 0
            }
    
    def _apply_cleanup_operations(self, asset: Dict[str, Any], 
                                operations: List[str]) -> Dict[str, Any]:
        """Apply specified cleanup operations to an asset."""
        cleaned_asset = asset.copy()
        
        for operation in operations:
            if operation == "standardize_asset_types":
                cleaned_asset = self._standardize_asset_type(cleaned_asset)
            elif operation == "normalize_environments":
                cleaned_asset = self._normalize_environment(cleaned_asset)
            elif operation == "fix_hostnames":
                cleaned_asset = self._fix_hostname_format(cleaned_asset)
            elif operation == "complete_missing_fields":
                cleaned_asset = self._complete_missing_fields(cleaned_asset)
            elif operation == "standardize_departments":
                cleaned_asset = self._standardize_department(cleaned_asset)
            elif operation == "fix_ip_addresses":
                cleaned_asset = self._fix_ip_address_format(cleaned_asset)
            elif operation == "normalize_operating_systems":
                cleaned_asset = self._normalize_operating_system(cleaned_asset)
            elif operation == "standardize_criticality":
                cleaned_asset = self._standardize_business_criticality(cleaned_asset)
            else:
                logger.warning(f"Unknown cleanup operation: {operation}")
        
        return cleaned_asset
    
    def _standardize_asset_type(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize asset type values."""
        asset_type = asset.get('asset_type', '').lower().strip()
        
        # Mapping of common variations to standard types
        type_mappings = {
            'srv': 'server',
            'server': 'server',
            'app': 'application',
            'application': 'application',
            'db': 'database',
            'database': 'database',
            'net': 'network',
            'network': 'network',
            'vm': 'virtual_machine',
            'virtual_machine': 'virtual_machine',
            'container': 'container',
            'storage': 'storage',
            'load_balancer': 'load_balancer',
            'lb': 'load_balancer'
        }
        
        standardized_type = type_mappings.get(asset_type, asset_type)
        if standardized_type != asset_type:
            asset['asset_type'] = standardized_type
            asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['asset_type_standardized']
        
        return asset
    
    def _normalize_environment(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment values."""
        environment = asset.get('environment', '').lower().strip()
        
        # Mapping of common variations to standard environments
        env_mappings = {
            'prod': 'production',
            'production': 'production',
            'prd': 'production',
            'dev': 'development',
            'development': 'development',
            'test': 'testing',
            'testing': 'testing',
            'tst': 'testing',
            'stage': 'staging',
            'staging': 'staging',
            'stg': 'staging',
            'uat': 'uat',
            'user_acceptance_testing': 'uat',
            'qa': 'qa',
            'quality_assurance': 'qa'
        }
        
        standardized_env = env_mappings.get(environment, environment)
        if standardized_env != environment:
            asset['environment'] = standardized_env
            asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['environment_normalized']
        
        return asset
    
    def _fix_hostname_format(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix hostname formatting issues."""
        hostname = asset.get('hostname', '').strip()
        
        if hostname:
            # Remove common prefixes/suffixes
            hostname = re.sub(r'^(host|server|srv)-?', '', hostname, flags=re.IGNORECASE)
            hostname = re.sub(r'\.(local|domain|com)$', '', hostname, flags=re.IGNORECASE)
            
            # Ensure lowercase
            hostname = hostname.lower()
            
            # Remove invalid characters
            hostname = re.sub(r'[^a-z0-9-]', '', hostname)
            
            if hostname != asset.get('hostname', ''):
                asset['hostname'] = hostname
                asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['hostname_formatted']
        
        return asset
    
    def _complete_missing_fields(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Complete missing fields with intelligent defaults."""
        changes_made = []
        
        # Infer environment from hostname if missing
        if not asset.get('environment') and asset.get('hostname'):
            hostname = asset['hostname'].lower()
            if 'prod' in hostname or 'prd' in hostname:
                asset['environment'] = 'production'
                changes_made.append('environment_inferred')
            elif 'dev' in hostname:
                asset['environment'] = 'development'
                changes_made.append('environment_inferred')
            elif 'test' in hostname or 'tst' in hostname:
                asset['environment'] = 'testing'
                changes_made.append('environment_inferred')
        
        # Infer asset type from hostname if missing
        if not asset.get('asset_type') and asset.get('hostname'):
            hostname = asset['hostname'].lower()
            if 'db' in hostname or 'sql' in hostname:
                asset['asset_type'] = 'database'
                changes_made.append('asset_type_inferred')
            elif 'app' in hostname or 'web' in hostname:
                asset['asset_type'] = 'application'
                changes_made.append('asset_type_inferred')
            elif 'srv' in hostname or 'server' in hostname:
                asset['asset_type'] = 'server'
                changes_made.append('asset_type_inferred')
        
        # Set default criticality if missing
        if not asset.get('business_criticality'):
            asset['business_criticality'] = 'Medium'
            changes_made.append('criticality_defaulted')
        
        if changes_made:
            asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + changes_made
        
        return asset
    
    def _standardize_department(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize department names."""
        department = asset.get('department', '').strip()
        
        if department:
            # Common department standardizations
            dept_mappings = {
                'it': 'IT',
                'information technology': 'IT',
                'hr': 'HR',
                'human resources': 'HR',
                'fin': 'Finance',
                'finance': 'Finance',
                'ops': 'Operations',
                'operations': 'Operations',
                'sales': 'Sales',
                'marketing': 'Marketing',
                'eng': 'Engineering',
                'engineering': 'Engineering'
            }
            
            standardized_dept = dept_mappings.get(department.lower(), department.title())
            if standardized_dept != department:
                asset['department'] = standardized_dept
                asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['department_standardized']
        
        return asset
    
    def _fix_ip_address_format(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix IP address formatting."""
        ip_address = asset.get('ip_address', '').strip()
        
        if ip_address:
            # Validate and clean IP address format
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, ip_address):
                # IP is valid, ensure proper formatting
                parts = ip_address.split('.')
                cleaned_ip = '.'.join([str(int(part)) for part in parts if part.isdigit()])
                if cleaned_ip != ip_address:
                    asset['ip_address'] = cleaned_ip
                    asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['ip_formatted']
            else:
                # Invalid IP format, remove if clearly wrong
                if not any(char.isdigit() for char in ip_address):
                    asset['ip_address'] = ''
                    asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['invalid_ip_removed']
        
        return asset
    
    def _normalize_operating_system(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize operating system names."""
        os_name = asset.get('operating_system', '').strip()
        
        if os_name:
            # Common OS normalizations
            os_mappings = {
                'win': 'Windows',
                'windows': 'Windows',
                'linux': 'Linux',
                'ubuntu': 'Ubuntu Linux',
                'centos': 'CentOS Linux',
                'rhel': 'Red Hat Enterprise Linux',
                'red hat': 'Red Hat Enterprise Linux',
                'suse': 'SUSE Linux',
                'aix': 'IBM AIX',
                'solaris': 'Oracle Solaris',
                'freebsd': 'FreeBSD',
                'macos': 'macOS',
                'mac os': 'macOS'
            }
            
            # Check for partial matches
            os_lower = os_name.lower()
            for key, value in os_mappings.items():
                if key in os_lower:
                    if value != os_name:
                        asset['operating_system'] = value
                        asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['os_normalized']
                    break
        
        return asset
    
    def _standardize_business_criticality(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize business criticality values."""
        criticality = asset.get('business_criticality', '').strip()
        
        if criticality:
            # Map variations to standard criticality levels
            criticality_mappings = {
                'high': 'High',
                'critical': 'High',
                'mission critical': 'High',
                'medium': 'Medium',
                'med': 'Medium',
                'moderate': 'Medium',
                'low': 'Low',
                'minimal': 'Low',
                'non-critical': 'Low'
            }
            
            standardized = criticality_mappings.get(criticality.lower(), criticality.title())
            if standardized != criticality:
                asset['business_criticality'] = standardized
                asset['_cleanup_applied'] = asset.get('_cleanup_applied', []) + ['criticality_standardized']
        
        return asset
    
    def _calculate_data_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate data quality score for an asset."""
        try:
            # Critical fields for quality assessment
            critical_fields = [
                'hostname', 'asset_name', 'asset_type', 'environment',
                'business_owner', 'department', 'operating_system', 'business_criticality'
            ]
            
            # Field weights (more important fields have higher weights)
            field_weights = {
                'asset_type': 15,
                'hostname': 15,
                'environment': 15,
                'asset_name': 10,
                'operating_system': 10,
                'business_criticality': 10,
                'business_owner': 10,
                'department': 10
            }
            
            total_possible_score = sum(field_weights.values())
            actual_score = 0
            
            for field in critical_fields:
                value = asset.get(field)
                if value and str(value).strip() and str(value).lower() not in ['unknown', 'null', 'none', '', 'tbd']:
                    # Additional quality checks
                    if field == 'ip_address' and value:
                        # Validate IP format
                        if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', value):
                            actual_score += field_weights.get(field, 5)
                    elif field == 'hostname' and value:
                        # Check hostname format
                        if re.match(r'^[a-zA-Z0-9-]+$', value):
                            actual_score += field_weights.get(field, 5)
                    else:
                        actual_score += field_weights.get(field, 5)
            
            # Bonus points for additional populated fields
            total_fields = len(asset)
            populated_fields = sum(1 for v in asset.values() if v and str(v).strip())
            bonus_score = min(15, (populated_fields / total_fields) * 15)  # Max 15% bonus
            
            final_score = ((actual_score / total_possible_score) * 85) + bonus_score
            return min(100.0, final_score)
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0
    
    async def _update_asset_with_cleaned_data(self, asset_id: str, cleaned_asset: Dict[str, Any], 
                                            quality_score: float, db, client_account_id: Optional[str],
                                            engagement_id: Optional[str]) -> None:
        """Update asset in database with cleaned data."""
        try:
            from app.repositories.asset_repository import AssetRepository
            
            asset_repo = AssetRepository(db, client_account_id, engagement_id)
            
            # Extract fields to update (exclude internal cleanup tracking)
            update_data = {k: v for k, v in cleaned_asset.items() if not k.startswith('_')}
            update_data['quality_score'] = quality_score
            update_data['last_cleanup'] = datetime.now()
            
            await asset_repo.update(asset_id, **update_data)
            
        except Exception as e:
            logger.error(f"Error updating asset {asset_id} with cleaned data: {e}")
    
    def _generate_cleanup_summary(self, quality_improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of cleanup operations."""
        if not quality_improvements:
            return {}
        
        total_assets = len(quality_improvements)
        total_improvement = sum(
            data["improvement"] for data in quality_improvements.values()
        )
        average_improvement = total_improvement / total_assets if total_assets > 0 else 0
        
        # Count quality levels achieved
        quality_levels = {"excellent": 0, "good": 0, "acceptable": 0, "needs_work": 0}
        for data in quality_improvements.values():
            final_quality = data["improved_quality"]
            if final_quality >= 90:
                quality_levels["excellent"] += 1
            elif final_quality >= 75:
                quality_levels["good"] += 1
            elif final_quality >= 60:
                quality_levels["acceptable"] += 1
            else:
                quality_levels["needs_work"] += 1
        
        # Count assets that advanced workflow
        workflow_advanced = sum(
            1 for data in quality_improvements.values()
            if data["improved_quality"] >= self.workflow_advancement_threshold
        )
        
        return {
            "total_assets_processed": total_assets,
            "average_quality_improvement": round(average_improvement, 2),
            "quality_distribution": quality_levels,
            "assets_advanced_workflow": workflow_advanced,
            "workflow_advancement_rate": round((workflow_advanced / total_assets) * 100, 1) if total_assets > 0 else 0
        }
    
    def assess_cleanup_readiness(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall cleanup readiness across a set of assets.
        
        Args:
            assets: List of asset dictionaries to assess
            
        Returns:
            Cleanup readiness assessment
        """
        try:
            if not assets:
                return {"readiness": "no_data", "message": "No assets to assess"}
            
            quality_scores = [self._calculate_data_quality(asset) for asset in assets]
            total_assets = len(assets)
            
            # Calculate statistics
            average_quality = sum(quality_scores) / total_assets
            ready_assets = len([score for score in quality_scores if score >= self.workflow_advancement_threshold])
            
            # Identify common cleanup opportunities
            cleanup_opportunities = self._identify_cleanup_opportunities(assets)
            
            # Determine readiness level
            if average_quality >= 85.0:
                readiness_level = "ready"
            elif average_quality >= 70.0:
                readiness_level = "mostly_ready"
            elif average_quality >= 50.0:
                readiness_level = "needs_improvement"
            else:
                readiness_level = "significant_work_needed"
            
            return {
                "readiness": readiness_level,
                "average_quality": round(average_quality, 1),
                "ready_assets": ready_assets,
                "total_assets": total_assets,
                "ready_percentage": round((ready_assets / total_assets) * 100, 1),
                "quality_distribution": {
                    "excellent": len([s for s in quality_scores if s >= 90]),
                    "good": len([s for s in quality_scores if 75 <= s < 90]),
                    "acceptable": len([s for s in quality_scores if 60 <= s < 75]),
                    "needs_work": len([s for s in quality_scores if s < 60])
                },
                "cleanup_opportunities": cleanup_opportunities,
                "recommendations": self._generate_cleanup_recommendations(
                    average_quality, cleanup_opportunities, ready_assets, total_assets
                )
            }
            
        except Exception as e:
            logger.error(f"Error assessing cleanup readiness: {e}")
            return {
                "readiness": "error",
                "error": str(e)
            }
    
    def _identify_cleanup_opportunities(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify common cleanup opportunities across assets."""
        opportunities = {
            "missing_asset_types": 0,
            "unstandardized_environments": 0,
            "malformed_hostnames": 0,
            "missing_departments": 0,
            "invalid_ip_addresses": 0,
            "unstandardized_os": 0,
            "missing_criticality": 0
        }
        
        standard_envs = {'production', 'development', 'testing', 'staging', 'uat', 'qa'}
        
        for asset in assets:
            # Missing asset types
            if not asset.get('asset_type') or asset.get('asset_type', '').strip().lower() in ['unknown', '']:
                opportunities["missing_asset_types"] += 1
            
            # Unstandardized environments
            env = asset.get('environment', '').lower().strip()
            if env and env not in standard_envs:
                opportunities["unstandardized_environments"] += 1
            
            # Malformed hostnames
            hostname = asset.get('hostname', '').strip()
            if hostname and not re.match(r'^[a-zA-Z0-9-]+$', hostname):
                opportunities["malformed_hostnames"] += 1
            
            # Missing departments
            if not asset.get('department') or asset.get('department', '').strip().lower() in ['unknown', '']:
                opportunities["missing_departments"] += 1
            
            # Invalid IP addresses
            ip = asset.get('ip_address', '').strip()
            if ip and not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                opportunities["invalid_ip_addresses"] += 1
            
            # Unstandardized OS
            os_name = asset.get('operating_system', '').strip()
            if os_name and len(os_name) < 3:  # Too short to be meaningful
                opportunities["unstandardized_os"] += 1
            
            # Missing criticality
            if not asset.get('business_criticality') or asset.get('business_criticality', '').strip().lower() in ['unknown', '']:
                opportunities["missing_criticality"] += 1
        
        return opportunities
    
    def _generate_cleanup_recommendations(self, average_quality: float, 
                                        opportunities: Dict[str, int],
                                        ready_assets: int, total_assets: int) -> List[str]:
        """Generate specific recommendations for data cleanup."""
        recommendations = []
        
        if average_quality < 70.0:
            recommendations.append(f"Improve overall data quality from {average_quality:.1f}% to 70%")
        
        # Priority recommendations based on opportunities
        if opportunities.get("missing_asset_types", 0) > 0:
            recommendations.append(
                f"Complete asset type classification for {opportunities['missing_asset_types']} assets"
            )
        
        if opportunities.get("unstandardized_environments", 0) > 0:
            recommendations.append(
                f"Standardize environment values for {opportunities['unstandardized_environments']} assets"
            )
        
        if opportunities.get("missing_departments", 0) > 0:
            recommendations.append(
                f"Complete department information for {opportunities['missing_departments']} assets"
            )
        
        if opportunities.get("malformed_hostnames", 0) > 0:
            recommendations.append(
                f"Fix hostname formatting for {opportunities['malformed_hostnames']} assets"
            )
        
        if opportunities.get("invalid_ip_addresses", 0) > 0:
            recommendations.append(
                f"Correct IP address format for {opportunities['invalid_ip_addresses']} assets"
            )
        
        # Progress recommendations
        ready_percentage = (ready_assets / total_assets) * 100 if total_assets > 0 else 0
        if ready_percentage < 80:
            recommendations.append(
                f"Focus on high-impact cleanup to advance {total_assets - ready_assets} assets to assessment phase"
            )
        
        if not recommendations:
            recommendations.append("Data cleanup is complete! Ready to proceed to assessment phase.")
        
        return recommendations

# Create global instance
data_cleanup_service = DataCleanupService()

# Export main classes and functions
__all__ = [
    "DataCleanupService",
    "data_cleanup_service"
] 