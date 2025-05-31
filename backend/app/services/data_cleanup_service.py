"""
Enhanced Data Cleanup Service - Agentic Intelligence with Quality Intelligence
Handles data quality improvements using AI agents for intelligent assessment and recommendations.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCleanupService:
    """
    Enhanced service for data quality improvements with agentic intelligence.
    Uses AI agents for quality assessment and intelligent cleanup recommendations.
    """
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 90.0,
            "good": 75.0, 
            "acceptable": 60.0,
            "needs_work": 0.0
        }
        self.workflow_advancement_threshold = 70.0  # Quality score needed to advance workflow
        
        # Agent intelligence availability
        self.agent_intelligence_available = True
        
        logger.info("Enhanced agentic data cleanup service initialized")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of data cleanup service."""
        return {
            "status": "healthy",
            "service": "data-cleanup-agentic",
            "version": "2.0.0",
            "agent_intelligence": self.agent_intelligence_available,
            "quality_thresholds": self.quality_thresholds,
            "workflow_threshold": self.workflow_advancement_threshold
        }
    
    async def agent_analyze_data_quality(self, asset_data: List[Dict[str, Any]], 
                                       page_context: str = "data-cleansing",
                                       client_account_id: Optional[str] = None,
                                       engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Agent-driven data quality assessment with intelligent prioritization.
        
        Args:
            asset_data: List of asset data to analyze
            page_context: UI context for agent learning
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping
            
        Returns:
            Agent assessment with quality issues, priorities, and recommendations
        """
        try:
            # Try agent-driven analysis first
            if self.agent_intelligence_available:
                try:
                    # Import agent communication service
                    from app.services.agent_ui_bridge import AgentUIBridge
                    
                    agent_bridge = AgentUIBridge()
                    
                    # Prepare data for agent analysis
                    analysis_request = {
                        "data_source": {
                            "assets": asset_data[:100],  # Sample for analysis
                            "total_count": len(asset_data),
                            "context": "data_quality_assessment"
                        },
                        "analysis_type": "data_quality_intelligence",
                        "page_context": page_context,
                        "client_context": {
                            "client_account_id": client_account_id,
                            "engagement_id": engagement_id
                        }
                    }
                    
                    # Get agent analysis
                    agent_response = await agent_bridge.analyze_with_agents(analysis_request)
                    
                    if agent_response.get("status") == "success":
                        # Agent provided intelligent analysis
                        return {
                            "analysis_type": "agent_driven",
                            "total_assets": len(asset_data),
                            "quality_assessment": agent_response.get("quality_assessment", {}),
                            "priority_issues": agent_response.get("priority_issues", []),
                            "cleansing_recommendations": agent_response.get("cleansing_recommendations", []),
                            "quality_buckets": agent_response.get("quality_buckets", {
                                "clean_data": 0,
                                "needs_attention": 0,
                                "critical_issues": 0
                            }),
                            "agent_confidence": agent_response.get("confidence", 0.85),
                            "agent_insights": agent_response.get("insights", []),
                            "suggested_operations": agent_response.get("suggested_operations", [])
                        }
                    
                except Exception as e:
                    logger.warning(f"Agent analysis failed, using fallback: {e}")
                    self.agent_intelligence_available = False
            
            # Fallback to rule-based analysis
            return await self._fallback_quality_analysis(asset_data)
            
        except Exception as e:
            logger.error(f"Error in agent_analyze_data_quality: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "total_assets": len(asset_data) if asset_data else 0
            }

    async def _fallback_quality_analysis(self, asset_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback rule-based quality analysis when agents are unavailable."""
        try:
            quality_issues = []
            clean_count = 0
            needs_attention_count = 0
            critical_count = 0
            
            for i, asset in enumerate(asset_data):
                asset_quality = self._calculate_data_quality(asset)
                issues = self._identify_asset_quality_issues(asset)
                
                if asset_quality >= 85:
                    clean_count += 1
                elif asset_quality >= 60:
                    needs_attention_count += 1
                else:
                    critical_count += 1
                
                if issues:
                    quality_issues.extend([{
                        "asset_id": asset.get("id", f"asset_{i}"),
                        "asset_name": asset.get("asset_name", f"Asset {i}"),
                        "issue": issue,
                        "severity": "critical" if asset_quality < 60 else "medium",
                        "impact": "migration_blocking" if asset_quality < 40 else "quality_improvement"
                    } for issue in issues])
            
            # Generate recommendations based on common issues
            recommendations = self._generate_fallback_recommendations(quality_issues)
            
            return {
                "analysis_type": "fallback_rules",
                "total_assets": len(asset_data),
                "quality_assessment": {
                    "average_quality": sum(self._calculate_data_quality(asset) for asset in asset_data) / len(asset_data) if asset_data else 0,
                    "quality_distribution": {
                        "excellent": sum(1 for asset in asset_data if self._calculate_data_quality(asset) >= 90),
                        "good": sum(1 for asset in asset_data if 75 <= self._calculate_data_quality(asset) < 90),
                        "acceptable": sum(1 for asset in asset_data if 60 <= self._calculate_data_quality(asset) < 75),
                        "needs_work": sum(1 for asset in asset_data if self._calculate_data_quality(asset) < 60)
                    }
                },
                "priority_issues": sorted(quality_issues, key=lambda x: x["severity"] == "critical", reverse=True)[:10],
                "cleansing_recommendations": recommendations,
                "quality_buckets": {
                    "clean_data": clean_count,
                    "needs_attention": needs_attention_count,
                    "critical_issues": critical_count
                },
                "agent_confidence": 0.60,  # Lower confidence for rule-based
                "agent_insights": [
                    "Using rule-based quality analysis (agent intelligence unavailable)",
                    f"Identified {len(quality_issues)} quality issues across {len(asset_data)} assets",
                    "Consider reviewing agent system status for enhanced intelligence"
                ],
                "suggested_operations": ["standardize_asset_types", "normalize_environments", "fix_hostnames", "complete_missing_fields"]
            }
            
        except Exception as e:
            logger.error(f"Error in fallback quality analysis: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "total_assets": len(asset_data) if asset_data else 0
            }

    def _identify_asset_quality_issues(self, asset: Dict[str, Any]) -> List[str]:
        """Identify specific quality issues in an asset."""
        issues = []
        
        # Missing critical fields
        critical_fields = ["asset_name", "asset_type", "environment"]
        for field in critical_fields:
            if not asset.get(field) or str(asset.get(field)).strip() == "":
                issues.append(f"Missing critical field: {field}")
        
        # Invalid data patterns
        if asset.get("ip_address") and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', str(asset.get("ip_address"))):
            issues.append("Invalid IP address format")
        
        # Inconsistent naming
        if asset.get("asset_name") and len(str(asset.get("asset_name")).strip()) < 3:
            issues.append("Asset name too short or unclear")
        
        # Environment standardization
        env = str(asset.get("environment", "")).lower()
        if env and env not in ["production", "test", "development", "staging", "prod", "dev"]:
            issues.append("Non-standard environment value")
        
        return issues

    def _generate_fallback_recommendations(self, quality_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate cleanup recommendations based on identified issues."""
        recommendations = []
        issue_counts = {}
        
        for issue in quality_issues:
            issue_type = issue["issue"].split(":")[0] if ":" in issue["issue"] else issue["issue"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        if issue_counts.get("Missing critical field", 0) > 0:
            recommendations.append("Complete missing critical fields for migration readiness")
        
        if issue_counts.get("Invalid IP address format", 0) > 0:
            recommendations.append("Standardize IP address formats for network mapping")
        
        if issue_counts.get("Non-standard environment value", 0) > 0:
            recommendations.append("Normalize environment values for wave planning")
        
        if issue_counts.get("Asset name too short", 0) > 0:
            recommendations.append("Improve asset naming for clear identification")
        
        if not recommendations:
            recommendations.append("Review data quality patterns for optimization opportunities")
        
        return recommendations

    async def process_agent_driven_cleanup(self, asset_data: List[Dict[str, Any]], 
                                         agent_operations: List[Dict[str, Any]],
                                         user_preferences: Dict[str, Any] = None,
                                         client_account_id: Optional[str] = None,
                                         engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process data cleanup using agent-recommended operations with user preferences.
        
        Args:
            asset_data: List of assets to clean
            agent_operations: Agent-recommended cleanup operations with confidence scores
            user_preferences: User preferences for cleanup approaches
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping
            
        Returns:
            Agent-driven cleanup results with learning feedback
        """
        try:
            cleanup_results = {
                "total_assets": len(asset_data),
                "successfully_cleaned": 0,
                "cleanup_errors": [],
                "agent_learning_data": [],
                "quality_improvements": {},
                "cleanup_summary": {},
                "workflow_updates": []
            }
            
            # Process each asset with agent-recommended operations
            for i, asset in enumerate(asset_data):
                try:
                    # Calculate original quality
                    original_quality = self._calculate_data_quality(asset)
                    
                    # Apply agent-recommended operations
                    cleaned_asset = await self._apply_agent_operations(
                        asset, agent_operations, user_preferences
                    )
                    
                    # Calculate improved quality
                    improved_quality = self._calculate_data_quality(cleaned_asset)
                    
                    # Track improvement for agent learning
                    asset_id = asset.get('id', f'asset_{i}')
                    improvement_data = {
                        "asset_id": asset_id,
                        "original_quality": original_quality,
                        "improved_quality": improved_quality,
                        "improvement": improved_quality - original_quality,
                        "operations_applied": [op["operation"] for op in agent_operations],
                        "user_preferences_applied": user_preferences or {}
                    }
                    
                    cleanup_results["quality_improvements"][asset_id] = improvement_data
                    cleanup_results["agent_learning_data"].append(improvement_data)
                    
                    # Update workflow if quality improved sufficiently
                    if improved_quality >= self.workflow_advancement_threshold:
                        await self._update_workflow_with_quality_improvement(
                            asset_id, improved_quality, client_account_id, engagement_id
                        )
                        cleanup_results["workflow_updates"].append({
                            "asset_id": asset_id,
                            "quality_score": improved_quality,
                            "workflow_advanced": True
                        })
                    
                    cleanup_results["successfully_cleaned"] += 1
                    
                except Exception as e:
                    logger.error(f"Error in agent-driven cleanup for asset {asset.get('id', i)}: {e}")
                    cleanup_results["cleanup_errors"].append({
                        "asset_id": asset.get('id', f'asset_{i}'),
                        "error": str(e)
                    })
            
            # Generate summary with agent learning insights
            cleanup_results["cleanup_summary"] = self._generate_agent_cleanup_summary(
                cleanup_results["quality_improvements"]
            )
            
            # Send learning data back to agents
            if cleanup_results["agent_learning_data"]:
                await self._send_cleanup_learning_to_agents(
                    cleanup_results["agent_learning_data"], client_account_id, engagement_id
                )
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error in process_agent_driven_cleanup: {e}")
            return {
                "error": f"Agent-driven cleanup failed: {str(e)}",
                "total_assets": len(asset_data) if asset_data else 0,
                "successfully_cleaned": 0
            }

    async def _apply_agent_operations(self, asset: Dict[str, Any], 
                                    agent_operations: List[Dict[str, Any]],
                                    user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply agent-recommended operations with user preferences."""
        cleaned_asset = asset.copy()
        user_prefs = user_preferences or {}
        
        for operation in agent_operations:
            op_type = operation.get("operation")
            confidence = operation.get("confidence", 0.5)
            parameters = operation.get("parameters", {})
            
            # Apply operation based on confidence and user preferences
            min_confidence = user_prefs.get("min_operation_confidence", 0.7)
            if confidence >= min_confidence:
                if op_type == "standardize_asset_types":
                    cleaned_asset = self._agent_standardize_asset_type(cleaned_asset, parameters)
                elif op_type == "normalize_environments":
                    cleaned_asset = self._agent_normalize_environment(cleaned_asset, parameters)
                elif op_type == "fix_hostnames":
                    cleaned_asset = self._agent_fix_hostname_format(cleaned_asset, parameters)
                elif op_type == "complete_missing_fields":
                    cleaned_asset = self._agent_complete_missing_fields(cleaned_asset, parameters)
                elif op_type == "standardize_departments":
                    cleaned_asset = self._agent_standardize_department(cleaned_asset, parameters)
                elif op_type == "fix_ip_addresses":
                    cleaned_asset = self._agent_fix_ip_address_format(cleaned_asset, parameters)
                elif op_type == "normalize_operating_systems":
                    cleaned_asset = self._agent_normalize_operating_system(cleaned_asset, parameters)
                elif op_type == "standardize_criticality":
                    cleaned_asset = self._agent_standardize_business_criticality(cleaned_asset, parameters)
                else:
                    # Fallback to original operation if agent version not available
                    cleaned_asset = self._apply_fallback_operation(cleaned_asset, op_type)
            
            # Track which operations were applied
            if not cleaned_asset.get('_agent_operations_applied'):
                cleaned_asset['_agent_operations_applied'] = []
            cleaned_asset['_agent_operations_applied'].append({
                "operation": op_type,
                "confidence": confidence,
                "applied": confidence >= min_confidence
            })
        
        return cleaned_asset

    def _agent_standardize_asset_type(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced asset type standardization with learned patterns."""
        asset_type = asset.get('asset_type', '').lower().strip()
        
        # Use agent-learned mappings if available, otherwise fallback
        agent_mappings = parameters.get("learned_mappings", {})
        standard_mappings = {
            'srv': 'server', 'server': 'server',
            'app': 'application', 'application': 'application',
            'db': 'database', 'database': 'database',
            'net': 'network', 'network': 'network',
            'vm': 'virtual_machine', 'virtual_machine': 'virtual_machine'
        }
        
        # Combine agent and standard mappings (agent takes precedence)
        all_mappings = {**standard_mappings, **agent_mappings}
        
        standardized_type = all_mappings.get(asset_type, asset_type)
        if standardized_type != asset_type:
            asset['asset_type'] = standardized_type
            asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['asset_type_standardized']
        
        return asset

    def _agent_normalize_environment(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced environment normalization with learned patterns."""
        environment = asset.get('environment', '').lower().strip()
        
        # Use agent-learned patterns
        agent_mappings = parameters.get("learned_mappings", {})
        standard_mappings = {
            'prod': 'production', 'production': 'production',
            'dev': 'development', 'development': 'development',
            'test': 'test', 'testing': 'test',
            'stage': 'staging', 'staging': 'staging'
        }
        
        all_mappings = {**standard_mappings, **agent_mappings}
        normalized_env = all_mappings.get(environment, environment)
        
        if normalized_env != environment:
            asset['environment'] = normalized_env
            asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['environment_normalized']
        
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

    def _generate_agent_cleanup_summary(self, quality_improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent-enhanced summary of cleanup operations."""
        if not quality_improvements:
            return {
                "total_operations": 0,
                "average_improvement": 0,
                "success_rate": 0,
                "agent_effectiveness": "no_data"
            }
        
        improvements = list(quality_improvements.values())
        total_improvement = sum(item["improvement"] for item in improvements)
        successful_operations = sum(1 for item in improvements if item["improvement"] > 0)
        
        return {
            "total_operations": len(improvements),
            "average_improvement": total_improvement / len(improvements),
            "success_rate": successful_operations / len(improvements),
            "agent_effectiveness": "high" if total_improvement / len(improvements) > 10 else "medium" if total_improvement / len(improvements) > 5 else "low",
            "quality_distribution": {
                "significant_improvement": sum(1 for item in improvements if item["improvement"] > 15),
                "moderate_improvement": sum(1 for item in improvements if 5 < item["improvement"] <= 15),
                "minimal_improvement": sum(1 for item in improvements if 0 < item["improvement"] <= 5),
                "no_improvement": sum(1 for item in improvements if item["improvement"] <= 0)
            }
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

    def _agent_fix_hostname_format(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced hostname formatting with learned patterns."""
        hostname = asset.get('hostname', '').strip()
        
        if hostname:
            # Use agent-learned patterns for hostname cleanup
            agent_patterns = parameters.get("hostname_patterns", {})
            
            # Apply agent patterns first, then fallback
            for pattern, replacement in agent_patterns.items():
                hostname = re.sub(pattern, replacement, hostname, flags=re.IGNORECASE)
            
            # Standard cleanup
            hostname = re.sub(r'^(host|server|srv)-?', '', hostname, flags=re.IGNORECASE)
            hostname = re.sub(r'\.(local|domain|com)$', '', hostname, flags=re.IGNORECASE)
            hostname = hostname.lower()
            hostname = re.sub(r'[^a-z0-9-]', '', hostname)
            
            if hostname != asset.get('hostname', ''):
                asset['hostname'] = hostname
                asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['hostname_formatted']
        
        return asset

    def _agent_complete_missing_fields(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced field completion with intelligent inference."""
        changes_made = []
        agent_inferences = parameters.get("field_inferences", {})
        
        # Use agent-learned inference patterns
        for field, inference_rules in agent_inferences.items():
            if not asset.get(field):
                for rule in inference_rules:
                    source_field = rule.get("source_field")
                    pattern = rule.get("pattern")
                    value = rule.get("value")
                    confidence = rule.get("confidence", 0.5)
                    
                    if confidence >= 0.7 and asset.get(source_field):
                        source_value = str(asset[source_field]).lower()
                        if re.search(pattern, source_value):
                            asset[field] = value
                            changes_made.append(f'{field}_inferred_by_agent')
                            break
        
        # Fallback inference if no agent rules applied
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
        
        if changes_made:
            asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + changes_made
        
        return asset

    def _agent_standardize_department(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced department standardization with learned patterns."""
        department = asset.get('department', '').strip()
        
        if department:
            # Use agent-learned mappings
            agent_mappings = parameters.get("learned_mappings", {})
            standard_mappings = {
                'it': 'IT', 'information technology': 'IT',
                'hr': 'HR', 'human resources': 'HR',
                'fin': 'Finance', 'finance': 'Finance',
                'ops': 'Operations', 'operations': 'Operations'
            }
            
            all_mappings = {**standard_mappings, **agent_mappings}
            standardized_dept = all_mappings.get(department.lower(), department.title())
            
            if standardized_dept != department:
                asset['department'] = standardized_dept
                asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['department_standardized']
        
        return asset

    def _agent_fix_ip_address_format(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced IP address formatting with validation."""
        ip_address = asset.get('ip_address', '').strip()
        
        if ip_address:
            # Agent-learned IP validation patterns
            agent_validation = parameters.get("ip_validation", {})
            is_valid = agent_validation.get("validate_strict", True)
            
            if is_valid:
                ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                if re.match(ip_pattern, ip_address):
                    parts = ip_address.split('.')
                    cleaned_ip = '.'.join([str(int(part)) for part in parts if part.isdigit()])
                    if cleaned_ip != ip_address:
                        asset['ip_address'] = cleaned_ip
                        asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['ip_formatted']
                else:
                    if not any(char.isdigit() for char in ip_address):
                        asset['ip_address'] = ''
                        asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['invalid_ip_removed']
        
        return asset

    def _agent_normalize_operating_system(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced OS normalization with learned patterns."""
        os_name = asset.get('operating_system', '').strip()
        
        if os_name:
            # Use agent-learned OS mappings
            agent_mappings = parameters.get("learned_mappings", {})
            standard_mappings = {
                'win': 'Windows', 'windows': 'Windows',
                'linux': 'Linux', 'ubuntu': 'Ubuntu Linux',
                'centos': 'CentOS Linux', 'rhel': 'Red Hat Enterprise Linux'
            }
            
            all_mappings = {**standard_mappings, **agent_mappings}
            os_lower = os_name.lower()
            
            for key, value in all_mappings.items():
                if key in os_lower:
                    if value != os_name:
                        asset['operating_system'] = value
                        asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['os_normalized']
                    break
        
        return asset

    def _agent_standardize_business_criticality(self, asset: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Agent-enhanced criticality standardization with learned patterns."""
        criticality = asset.get('business_criticality', '').strip()
        
        if criticality:
            # Use agent-learned criticality mappings
            agent_mappings = parameters.get("learned_mappings", {})
            standard_mappings = {
                'high': 'High', 'critical': 'High', 'mission critical': 'High',
                'medium': 'Medium', 'med': 'Medium', 'moderate': 'Medium',
                'low': 'Low', 'minimal': 'Low', 'non-critical': 'Low'
            }
            
            all_mappings = {**standard_mappings, **agent_mappings}
            standardized = all_mappings.get(criticality.lower(), criticality.title())
            
            if standardized != criticality:
                asset['business_criticality'] = standardized
                asset['_agent_cleanup_applied'] = asset.get('_agent_cleanup_applied', []) + ['criticality_standardized']
        
        return asset

    def _apply_fallback_operation(self, asset: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Apply fallback operation when agent version is not available."""
        if operation == "standardize_asset_types":
            return self._standardize_asset_type(asset)
        elif operation == "normalize_environments":
            return self._normalize_environment(asset)
        elif operation == "fix_hostnames":
            return self._fix_hostname_format(asset)
        elif operation == "complete_missing_fields":
            return self._complete_missing_fields(asset)
        elif operation == "standardize_departments":
            return self._standardize_department(asset)
        elif operation == "fix_ip_addresses":
            return self._fix_ip_address_format(asset)
        elif operation == "normalize_operating_systems":
            return self._normalize_operating_system(asset)
        elif operation == "standardize_criticality":
            return self._standardize_business_criticality(asset)
        else:
            logger.warning(f"Unknown fallback operation: {operation}")
            return asset

    async def _update_workflow_with_quality_improvement(self, asset_id: str, quality_score: float,
                                                       client_account_id: Optional[str],
                                                       engagement_id: Optional[str]) -> None:
        """Update workflow status based on quality improvement."""
        try:
            from app.services.workflow_service import WorkflowService
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                workflow_service = WorkflowService(db, client_account_id, engagement_id)
                await workflow_service.update_asset_workflow_status(asset_id, {
                    "cleanup_status": "completed",
                    "quality_score": quality_score
                })
        except Exception as e:
            logger.error(f"Error updating workflow for asset {asset_id}: {e}")

    async def _send_cleanup_learning_to_agents(self, learning_data: List[Dict[str, Any]],
                                             client_account_id: Optional[str],
                                             engagement_id: Optional[str]) -> None:
        """Send cleanup learning data back to agents for improvement."""
        try:
            from app.services.agent_ui_bridge import AgentUIBridge
            
            agent_bridge = AgentUIBridge()
            
            learning_request = {
                "learning_type": "data_cleanup_effectiveness",
                "learning_data": learning_data,
                "context": {
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                    "total_operations": len(learning_data),
                    "average_improvement": sum(item["improvement"] for item in learning_data) / len(learning_data) if learning_data else 0
                },
                "page_context": "data-cleansing"
            }
            
            await agent_bridge.process_agent_learning(learning_request)
            
        except Exception as e:
            logger.warning(f"Could not send learning data to agents: {e}")

    def _generate_agent_cleanup_summary(self, quality_improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent-enhanced summary of cleanup operations."""
        if not quality_improvements:
            return {
                "total_operations": 0,
                "average_improvement": 0,
                "success_rate": 0,
                "agent_effectiveness": "no_data"
            }
        
        improvements = list(quality_improvements.values())
        total_improvement = sum(item["improvement"] for item in improvements)
        successful_operations = sum(1 for item in improvements if item["improvement"] > 0)
        
        return {
            "total_operations": len(improvements),
            "average_improvement": total_improvement / len(improvements),
            "success_rate": successful_operations / len(improvements),
            "agent_effectiveness": "high" if total_improvement / len(improvements) > 10 else "medium" if total_improvement / len(improvements) > 5 else "low",
            "quality_distribution": {
                "significant_improvement": sum(1 for item in improvements if item["improvement"] > 15),
                "moderate_improvement": sum(1 for item in improvements if 5 < item["improvement"] <= 15),
                "minimal_improvement": sum(1 for item in improvements if 0 < item["improvement"] <= 5),
                "no_improvement": sum(1 for item in improvements if item["improvement"] <= 0)
            }
        }

    async def process_data_cleanup_batch(self, asset_data: List[Dict[str, Any]], 
                                       cleanup_operations: List[str],
                                       client_account_id: Optional[str] = None,
                                       engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Legacy method maintained for backward compatibility.
        Process a batch of assets for data cleanup and advance workflow status.
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
        Assess how ready the asset data is for cleanup operations.
        """
        if not assets:
            return {
                "total_assets": 0,
                "average_quality": 0,
                "ready_for_cleanup": 0,
                "cleanup_opportunities": {},
                "recommendations": []
            }
        
        # Calculate quality scores for all assets
        quality_scores = [self._calculate_data_quality(asset) for asset in assets]
        average_quality = sum(quality_scores) / len(quality_scores)
        
        # Count assets ready for cleanup (below good threshold)
        ready_assets = sum(1 for score in quality_scores if score < self.quality_thresholds["good"])
        
        # Identify cleanup opportunities
        opportunities = self._identify_cleanup_opportunities(assets)
        
        # Generate recommendations
        recommendations = self._generate_cleanup_recommendations(
            average_quality, opportunities, ready_assets, len(assets)
        )
        
        return {
            "total_assets": len(assets),
            "average_quality": round(average_quality, 2),
            "ready_for_cleanup": ready_assets,
            "cleanup_opportunities": opportunities,
            "recommendations": recommendations,
            "quality_thresholds": self.quality_thresholds
        }

    def _identify_cleanup_opportunities(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify the most common data quality issues."""
        opportunities = {
            "standardize_asset_types": 0,
            "normalize_environments": 0,
            "fix_hostnames": 0,
            "complete_missing_fields": 0,
            "standardize_departments": 0,
            "fix_ip_addresses": 0,
            "normalize_operating_systems": 0,
            "standardize_criticality": 0
        }
        
        for asset in assets:
            # Check for non-standard asset types
            asset_type = str(asset.get('asset_type', '')).lower().strip()
            if asset_type and asset_type not in ['server', 'application', 'database', 'network', 'virtual_machine']:
                opportunities["standardize_asset_types"] += 1
            
            # Check for non-standard environments
            env = str(asset.get('environment', '')).lower().strip()
            if env and env not in ['production', 'development', 'testing', 'staging', 'uat', 'qa']:
                opportunities["normalize_environments"] += 1
            
            # Check for problematic hostnames
            hostname = str(asset.get('hostname', '')).strip()
            if hostname and (len(hostname) < 3 or ' ' in hostname or hostname != hostname.lower()):
                opportunities["fix_hostnames"] += 1
            
            # Check for missing critical fields
            critical_fields = ['asset_name', 'asset_type', 'environment']
            missing_fields = sum(1 for field in critical_fields if not asset.get(field))
            if missing_fields > 0:
                opportunities["complete_missing_fields"] += 1
            
            # Check for non-standard departments
            dept = str(asset.get('department', '')).strip()
            if dept and dept.lower() not in ['it', 'hr', 'finance', 'operations', 'sales', 'marketing', 'engineering']:
                opportunities["standardize_departments"] += 1
            
            # Check for invalid IP addresses
            ip = str(asset.get('ip_address', '')).strip()
            if ip and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                opportunities["fix_ip_addresses"] += 1
            
            # Check for non-standard OS names
            os_name = str(asset.get('operating_system', '')).strip()
            if os_name and os_name.lower() not in ['windows', 'linux', 'ubuntu linux', 'centos linux', 'red hat enterprise linux']:
                opportunities["normalize_operating_systems"] += 1
            
            # Check for non-standard criticality
            criticality = str(asset.get('business_criticality', '')).strip()
            if criticality and criticality.lower() not in ['high', 'medium', 'low']:
                opportunities["standardize_criticality"] += 1
        
        return opportunities

    def _generate_cleanup_recommendations(self, average_quality: float, 
                                        opportunities: Dict[str, int],
                                        ready_assets: int, total_assets: int) -> List[str]:
        """Generate specific cleanup recommendations based on analysis."""
        recommendations = []
        
        if average_quality < self.quality_thresholds["acceptable"]:
            recommendations.append(
                f"Data quality is below acceptable threshold ({average_quality:.1f}% < {self.quality_thresholds['acceptable']}%). "
                "Immediate cleanup recommended before proceeding with migration analysis."
            )
        
        # Prioritize recommendations by impact
        sorted_opportunities = sorted(opportunities.items(), key=lambda x: x[1], reverse=True)
        
        for operation, count in sorted_opportunities[:3]:  # Top 3 opportunities
            if count > 0:
                percentage = (count / total_assets) * 100
                if operation == "complete_missing_fields":
                    recommendations.append(
                        f"Complete missing critical fields for {count} assets ({percentage:.1f}%) "
                        "to enable proper migration analysis."
                    )
                elif operation == "standardize_asset_types":
                    recommendations.append(
                        f"Standardize asset types for {count} assets ({percentage:.1f}%) "
                        "to improve 6R strategy recommendations."
                    )
                elif operation == "normalize_environments":
                    recommendations.append(
                        f"Normalize environment values for {count} assets ({percentage:.1f}%) "
                        "to enable accurate wave planning."
                    )
        
        if ready_assets == 0:
            recommendations.append("All assets meet minimum quality standards. Consider optimizing for better analysis accuracy.")
        
        return recommendations

# Create global instance
data_cleanup_service = DataCleanupService()

# Export main classes and functions
__all__ = [
    "DataCleanupService",
    "data_cleanup_service"
] 