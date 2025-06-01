"""
Agent Analysis Handler
Handles agent-driven data quality assessment and analysis.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AgentAnalysisHandler:
    """Handler for agent-driven data quality analysis."""
    
    def __init__(self, quality_thresholds: Dict[str, float]):
        self.quality_thresholds = quality_thresholds
        self.agent_intelligence_available = True
    
    def is_available(self) -> bool:
        """Check if the handler is available."""
        return True
    
    async def analyze_data_quality(self, asset_data: List[Dict[str, Any]], 
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
            logger.error(f"Error in analyze_data_quality: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "total_assets": len(asset_data) if asset_data else 0
            }
    
    async def _fallback_quality_analysis(self, asset_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback quality analysis using rule-based assessment.
        Used when agent intelligence is not available.
        """
        logger.info("Using fallback rule-based quality analysis")
        
        total_assets = len(asset_data)
        quality_issues = []
        quality_scores = []
        
        # Analyze each asset for quality issues
        for i, asset in enumerate(asset_data[:50]):  # Limit analysis for performance
            asset_quality_score = self._calculate_asset_quality(asset)
            quality_scores.append(asset_quality_score)
            
            # Identify specific quality issues
            issues = self._identify_asset_quality_issues(asset)
            for issue in issues:
                quality_issues.append({
                    "asset_id": asset.get("id", f"asset_{i}"),
                    "asset_name": asset.get("asset_name") or asset.get("hostname", f"Unknown Asset {i}"),
                    "issue": issue,
                    "severity": "medium",
                    "confidence": 0.7
                })
        
        # Calculate quality buckets
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        clean_data = len([q for q in quality_scores if q >= 80])
        needs_attention = len([q for q in quality_scores if 60 <= q < 80])
        critical_issues = len([q for q in quality_scores if q < 60])
        
        # Generate recommendations
        recommendations = self._generate_fallback_recommendations(quality_issues)
        
        return {
            "analysis_type": "fallback_rules",
            "total_assets": total_assets,
            "quality_assessment": {
                "average_quality": average_quality,
                "assets_analyzed": len(quality_scores)
            },
            "priority_issues": quality_issues[:10],  # Top 10 issues
            "cleansing_recommendations": recommendations,
            "quality_buckets": {
                "clean_data": clean_data,
                "needs_attention": needs_attention,
                "critical_issues": critical_issues
            },
            "agent_confidence": 0.6,  # Lower confidence for fallback
            "agent_insights": [
                "Fallback analysis used - agent intelligence not available",
                f"Analyzed {len(quality_scores)} assets for quality issues"
            ],
            "suggested_operations": [
                "standardize_asset_types",
                "normalize_environments",
                "fix_hostname_format"
            ]
        }
    
    def _calculate_asset_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate quality score for a single asset."""
        score = 0.0
        max_score = 100.0
        
        # Essential fields (40 points)
        essential_fields = ['asset_name', 'hostname', 'asset_type', 'environment']
        for field in essential_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0
        
        # Important fields (30 points)
        important_fields = ['operating_system', 'ip_address', 'business_criticality']
        for field in important_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0
        
        # Optional fields (30 points)
        optional_fields = ['department', 'owner', 'cost_center', 'location']
        for field in optional_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 7.5
        
        return min(score, max_score)
    
    def _identify_asset_quality_issues(self, asset: Dict[str, Any]) -> List[str]:
        """Identify specific quality issues in an asset."""
        issues = []
        
        # Missing essential fields
        essential_fields = ['asset_name', 'hostname', 'asset_type', 'environment']
        for field in essential_fields:
            if not asset.get(field) or not str(asset[field]).strip():
                issues.append(f"Missing {field}")
        
        # Invalid data formats
        if asset.get('ip_address'):
            ip = str(asset['ip_address'])
            if not self._is_valid_ip(ip):
                issues.append("Invalid IP address format")
        
        # Inconsistent naming
        if asset.get('hostname'):
            hostname = str(asset['hostname'])
            if not hostname.replace('-', '').replace('_', '').isalnum():
                issues.append("Non-standard hostname format")
        
        return issues
    
    def _is_valid_ip(self, ip_address: str) -> bool:
        """Check if IP address is valid."""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _generate_fallback_recommendations(self, quality_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate cleanup recommendations based on identified issues."""
        recommendations = []
        issue_types = {}
        
        # Count issue types
        for issue in quality_issues:
            issue_type = issue.get("issue", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Generate recommendations based on common issues
        if any("Missing asset_name" in issue for issue in issue_types):
            recommendations.append("Standardize asset naming conventions")
        
        if any("Missing hostname" in issue for issue in issue_types):
            recommendations.append("Complete missing hostname information")
        
        if any("Invalid IP" in issue for issue in issue_types):
            recommendations.append("Validate and correct IP address formats")
        
        if any("hostname format" in issue for issue in issue_types):
            recommendations.append("Standardize hostname formatting")
        
        if not recommendations:
            recommendations.append("Perform general data quality improvements")
        
        return recommendations 