"""
Asset Inventory Agent - Specialized agent for asset classification and inventory management
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult, AgentClarificationRequest, AgentInsight

logger = logging.getLogger(__name__)

class AssetInventoryAgent(BaseDiscoveryAgent):
    """Asset Inventory Agent for classification and criticality assessment"""
    
    def __init__(self):
        super().__init__(
            agent_id="asset_inventory_001",
            name="Asset Inventory Specialist",
            role="Asset Inventory and Classification Expert",
            goal="Accurately classify and categorize all discovered assets with proper criticality assessment",
            backstory="Expert asset inventory specialist with deep knowledge of enterprise IT infrastructure"
        )
        
        # Asset classification models
        self.asset_types = {
            'server': ['server', 'host', 'machine', 'node', 'vm', 'virtual'],
            'database': ['db', 'database', 'sql', 'oracle', 'mysql', 'postgres', 'mongo'],
            'application': ['app', 'application', 'service', 'webapp', 'api'],
            'network': ['router', 'switch', 'firewall', 'load balancer', 'proxy'],
            'storage': ['storage', 'nas', 'san', 'disk', 'volume'],
            'middleware': ['middleware', 'message queue', 'broker', 'cache']
        }
        
        self.logger.info(f"🏭 Asset Inventory Agent initialized")
    
    def get_role(self) -> str:
        """Return the agent's role description"""
        return "Asset Inventory and Classification Expert"
    
    def get_goal(self) -> str:
        """Return the agent's goal description"""
        return "Accurately classify and categorize all discovered assets with proper criticality assessment"
    
    def get_backstory(self) -> str:
        """Return the agent's backstory"""
        return "Expert asset inventory specialist with deep knowledge of enterprise IT infrastructure"
    
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute the agent's main functionality"""
        return await self.execute_analysis(data, context)
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute asset inventory analysis"""
        start_time = time.time()
        
        try:
            assets = data.get('raw_data', [])
            if not assets:
                return self._create_error_result("No asset data provided")
            
            # Perform classification
            classification_results = await self._classify_assets(assets)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_id=self.agent_id,
                status='completed',
                confidence_score=85.0,
                data=classification_results,
                insights=[],
                clarifications=[],
                execution_time=execution_time,
                metadata={'assets_processed': len(assets)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return self._create_error_result(f"Asset inventory analysis failed: {str(e)}", execution_time)
    
    async def _classify_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify assets by type"""
        classified = []
        unclassified = []
        
        for asset in assets:
            asset_type = await self._determine_asset_type(asset)
            if asset_type != 'unknown':
                classified.append({'asset': asset, 'type': asset_type})
            else:
                unclassified.append(asset)
        
        return {
            'classified_assets': classified,
            'unclassified_assets': unclassified,
            'classification_rate': len(classified) / len(assets) * 100
        }
    
    async def _determine_asset_type(self, asset: Dict[str, Any]) -> str:
        """Determine asset type"""
        text = " ".join(str(v).lower() for v in asset.values() if isinstance(v, str))
        
        for asset_type, keywords in self.asset_types.items():
            if any(keyword in text for keyword in keywords):
                return asset_type
        
        return 'unknown'

    async def _assess_criticality(self, assets: List[Dict[str, Any]], 
                                classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business criticality of assets"""
        criticality_results = {
            'asset_criticality': [],
            'criticality_summary': {},
            'high_risk_assets': []
        }
        
        for asset in assets:
            asset_id = self._get_asset_identifier(asset)
            criticality, confidence = await self._determine_criticality(asset)
            
            criticality_assessment = {
                'asset_id': asset_id,
                'criticality_level': criticality,
                'criticality_confidence': confidence,
                'criticality_factors': await self._get_criticality_factors(asset, criticality)
            }
            
            criticality_results['asset_criticality'].append(criticality_assessment)
            
            # Flag high-risk assets
            if criticality in ['critical', 'high']:
                criticality_results['high_risk_assets'].append({
                    'asset_id': asset_id,
                    'criticality': criticality,
                    'risk_factors': await self._identify_risk_factors(asset)
                })
        
        # Create summary
        criticality_counts = {}
        for assessment in criticality_results['asset_criticality']:
            level = assessment['criticality_level']
            criticality_counts[level] = criticality_counts.get(level, 0) + 1
        
        criticality_results['criticality_summary'] = {
            'total_assets': len(assets),
            'criticality_distribution': criticality_counts,
            'high_risk_count': len(criticality_results['high_risk_assets']),
            'risk_percentage': len(criticality_results['high_risk_assets']) / len(assets) * 100
        }
        
        return criticality_results
    
    async def _determine_criticality(self, asset: Dict[str, Any]) -> Tuple[str, float]:
        """Determine asset criticality with confidence"""
        text_fields = []
        for key, value in asset.items():
            if isinstance(value, str):
                text_fields.append(f"{key}:{value}".lower())
        
        combined_text = " ".join(text_fields)
        
        # Score criticality levels
        criticality_scores = {}
        for level, keywords in self.criticality_indicators.items():
            score = 0
            matches = []
            
            for keyword in keywords:
                if keyword in combined_text:
                    score += 1
                    matches.append(keyword)
            
            if score > 0:
                # Boost based on field importance
                if any(keyword in asset.get('environment', '').lower() for keyword in keywords):
                    score += 2
                if any(keyword in asset.get('tier', '').lower() for keyword in keywords):
                    score += 2
                
                criticality_scores[level] = {
                    'score': score,
                    'matches': matches,
                    'confidence': min(score * 20, 90)
                }
        
        if not criticality_scores:
            return 'medium', 50.0  # Default to medium
        
        best_level = max(criticality_scores.keys(), key=lambda k: criticality_scores[k]['score'])
        confidence = criticality_scores[best_level]['confidence']
        
        return best_level, confidence
    
    async def _detect_environments(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect asset environments"""
        environment_results = {
            'asset_environments': [],
            'environment_summary': {},
            'environment_distribution': {}
        }
        
        for asset in assets:
            asset_id = self._get_asset_identifier(asset)
            environment, confidence = await self._determine_environment(asset)
            
            environment_detection = {
                'asset_id': asset_id,
                'detected_environment': environment,
                'environment_confidence': confidence,
                'environment_indicators': await self._get_environment_indicators(asset, environment)
            }
            
            environment_results['asset_environments'].append(environment_detection)
        
        # Create summary
        env_counts = {}
        for detection in environment_results['asset_environments']:
            env = detection['detected_environment']
            env_counts[env] = env_counts.get(env, 0) + 1
        
        environment_results['environment_summary'] = {
            'total_assets': len(assets),
            'environments_detected': len(env_counts),
            'environment_distribution': env_counts
        }
        
        return environment_results
    
    async def _determine_environment(self, asset: Dict[str, Any]) -> Tuple[str, float]:
        """Determine asset environment"""
        text_fields = []
        for key, value in asset.items():
            if isinstance(value, str):
                text_fields.append(f"{key}:{value}".lower())
        
        combined_text = " ".join(text_fields)
        
        # Score environments
        env_scores = {}
        for env, keywords in self.environment_patterns.items():
            score = 0
            matches = []
            
            for keyword in keywords:
                if keyword in combined_text:
                    score += 1
                    matches.append(keyword)
            
            if score > 0:
                # Boost for environment-specific fields
                if any(keyword in asset.get('environment', '').lower() for keyword in keywords):
                    score += 3
                if any(keyword in asset.get('hostname', '').lower() for keyword in keywords):
                    score += 2
                
                env_scores[env] = {
                    'score': score,
                    'matches': matches,
                    'confidence': min(score * 25, 95)
                }
        
        if not env_scores:
            return 'unknown', 30.0
        
        best_env = max(env_scores.keys(), key=lambda k: env_scores[k]['score'])
        confidence = env_scores[best_env]['confidence']
        
        return best_env, confidence
    
    async def _generate_asset_insights(self, assets: List[Dict[str, Any]], 
                                     classification_results: Dict[str, Any],
                                     criticality_results: Dict[str, Any],
                                     environment_results: Dict[str, Any]) -> List[AgentInsight]:
        """Generate insights about asset inventory"""
        insights = []
        
        # Classification insights
        classification_rate = classification_results['classification_rate']
        if classification_rate < 80:
            insights.append(AgentInsight(
                title="Low Asset Classification Rate",
                description=f"Only {classification_rate:.1f}% of assets were successfully classified. "
                           f"This may indicate incomplete or inconsistent asset data.",
                confidence_score=85.0,
                category="data_quality",
                actionable=True,
                action_items=[
                    "Review unclassified assets for missing type information",
                    "Standardize asset naming conventions",
                    "Consider manual classification for unclear assets"
                ]
            ))
        
        # Criticality insights
        high_risk_count = criticality_results['criticality_summary']['high_risk_count']
        if high_risk_count > len(assets) * 0.3:  # More than 30% high risk
            insights.append(AgentInsight(
                title="High Number of Critical Assets",
                description=f"{high_risk_count} assets ({high_risk_count/len(assets)*100:.1f}%) "
                           f"are classified as high-risk or critical.",
                confidence_score=90.0,
                category="risk_assessment",
                actionable=True,
                action_items=[
                    "Prioritize critical assets in migration planning",
                    "Implement additional monitoring for high-risk assets",
                    "Consider phased migration approach"
                ]
            ))
        
        # Environment insights
        env_distribution = environment_results['environment_summary']['environment_distribution']
        if 'production' in env_distribution and env_distribution['production'] > len(assets) * 0.5:
            insights.append(AgentInsight(
                title="Production-Heavy Environment",
                description=f"Over 50% of assets are in production environments. "
                           f"Migration planning should prioritize minimal downtime strategies.",
                confidence_score=95.0,
                category="migration_strategy",
                actionable=True,
                action_items=[
                    "Plan for zero-downtime migration strategies",
                    "Consider blue-green deployment patterns",
                    "Schedule migrations during maintenance windows"
                ]
            ))
        
        return insights
    
    async def _identify_clarifications(self, assets: List[Dict[str, Any]], 
                                     classification_results: Dict[str, Any],
                                     criticality_results: Dict[str, Any]) -> List[AgentClarificationRequest]:
        """Identify clarifications needed from user"""
        clarifications = []
        
        # Unclassified assets
        unclassified = classification_results['unclassified_assets']
        if unclassified and len(unclassified) <= 10:  # Only ask for small numbers
            asset_list = [asset['asset_id'] for asset in unclassified[:5]]
            clarifications.append(AgentClarificationRequest(
                question_id=f"asset_classification_{int(time.time())}",
                question="Some assets could not be automatically classified. Can you help identify their types?",
                question_type="multiple_choice",
                context={
                    'unclassified_assets': asset_list,
                    'asset_details': [asset['original_data'] for asset in unclassified[:5]]
                },
                options=[
                    "Server/Virtual Machine",
                    "Database System",
                    "Application/Service",
                    "Network Device",
                    "Storage System",
                    "Middleware/Other"
                ],
                required=False,
                confidence_impact=15.0
            ))
        
        # Ambiguous criticality
        low_confidence_criticality = [
            assessment for assessment in criticality_results['asset_criticality']
            if assessment['criticality_confidence'] < 60
        ]
        
        if low_confidence_criticality and len(low_confidence_criticality) <= 5:
            clarifications.append(AgentClarificationRequest(
                question_id=f"criticality_assessment_{int(time.time())}",
                question="The business criticality of some assets is unclear. Can you help assess their importance?",
                question_type="multiple_choice",
                context={
                    'unclear_assets': [a['asset_id'] for a in low_confidence_criticality[:3]]
                },
                options=[
                    "Critical - Business cannot function without it",
                    "High - Important for business operations",
                    "Medium - Standard business function",
                    "Low - Development/test/backup system"
                ],
                required=False,
                confidence_impact=20.0
            ))
        
        return clarifications
    
    async def _calculate_confidence(self, classification_results: Dict[str, Any],
                                  criticality_results: Dict[str, Any],
                                  environment_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        factors = []
        
        # Classification confidence
        if classification_results['classified_assets']:
            avg_classification_confidence = sum(
                asset['classification_confidence'] 
                for asset in classification_results['classified_assets']
            ) / len(classification_results['classified_assets'])
            factors.append(('classification', avg_classification_confidence, 0.4))
        
        # Criticality confidence
        if criticality_results['asset_criticality']:
            avg_criticality_confidence = sum(
                assessment['criticality_confidence']
                for assessment in criticality_results['asset_criticality']
            ) / len(criticality_results['asset_criticality'])
            factors.append(('criticality', avg_criticality_confidence, 0.3))
        
        # Environment confidence
        if environment_results['asset_environments']:
            avg_environment_confidence = sum(
                detection['environment_confidence']
                for detection in environment_results['asset_environments']
            ) / len(environment_results['asset_environments'])
            factors.append(('environment', avg_environment_confidence, 0.3))
        
        if not factors:
            return 50.0
        
        # Weighted average
        weighted_sum = sum(confidence * weight for _, confidence, weight in factors)
        total_weight = sum(weight for _, _, weight in factors)
        
        return weighted_sum / total_weight if total_weight > 0 else 50.0
    
    # Helper methods
    
    def _get_asset_identifier(self, asset: Dict[str, Any]) -> str:
        """Get unique identifier for asset"""
        for key in ['id', 'asset_id', 'hostname', 'name', 'server_name']:
            if key in asset and asset[key]:
                return str(asset[key])
        
        # Fallback to hash
        import hashlib
        asset_str = str(sorted(asset.items()))
        return f"asset_{hashlib.md5(asset_str.encode()).hexdigest()[:8]}"
    
    async def _get_classification_reasons(self, asset: Dict[str, Any], asset_type: str) -> List[str]:
        """Get reasons for classification"""
        reasons = []
        
        if asset_type in self.asset_types:
            keywords = self.asset_types[asset_type]
            for key, value in asset.items():
                if isinstance(value, str):
                    for keyword in keywords:
                        if keyword in value.lower():
                            reasons.append(f"'{keyword}' found in {key}")
        
        return reasons[:3]  # Limit to top 3 reasons
    
    async def _get_criticality_factors(self, asset: Dict[str, Any], criticality: str) -> List[str]:
        """Get factors that influenced criticality assessment"""
        factors = []
        
        if criticality in self.criticality_indicators:
            keywords = self.criticality_indicators[criticality]
            for key, value in asset.items():
                if isinstance(value, str):
                    for keyword in keywords:
                        if keyword in value.lower():
                            factors.append(f"'{keyword}' indicates {criticality} criticality")
        
        return factors[:3]
    
    async def _identify_risk_factors(self, asset: Dict[str, Any]) -> List[str]:
        """Identify risk factors for asset"""
        risk_factors = []
        
        # Check for production indicators
        text_fields = " ".join(str(v).lower() for v in asset.values() if isinstance(v, str))
        
        if any(prod in text_fields for prod in ['prod', 'production', 'live']):
            risk_factors.append("Production environment")
        
        if any(critical in text_fields for critical in ['critical', 'core', 'primary']):
            risk_factors.append("Critical system designation")
        
        if any(db in text_fields for db in ['database', 'db', 'sql']):
            risk_factors.append("Database system")
        
        return risk_factors
    
    async def _get_environment_indicators(self, asset: Dict[str, Any], environment: str) -> List[str]:
        """Get indicators that determined environment"""
        indicators = []
        
        if environment in self.environment_patterns:
            keywords = self.environment_patterns[environment]
            for key, value in asset.items():
                if isinstance(value, str):
                    for keyword in keywords:
                        if keyword in value.lower():
                            indicators.append(f"'{keyword}' in {key}")
        
        return indicators[:3]
    
    async def _create_asset_summary(self, assets: List[Dict[str, Any]], 
                                  classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create asset summary"""
        return {
            'total_assets': len(assets),
            'classified_assets': len(classification_results['classified_assets']),
            'unclassified_assets': len(classification_results['unclassified_assets']),
            'classification_rate': classification_results['classification_rate'],
            'asset_types_found': list(classification_results['asset_types_found']),
            'largest_asset_category': max(
                classification_results['asset_types_found'],
                key=lambda x: x[1],
                default=('unknown', 0)
            )[0] if classification_results['asset_types_found'] else 'none'
        }
    
    async def _get_confidence_factors(self, classification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get factors affecting confidence"""
        return {
            'classification_rate': classification_results['classification_rate'],
            'avg_classification_confidence': sum(
                asset['classification_confidence'] 
                for asset in classification_results['classified_assets']
            ) / len(classification_results['classified_assets']) if classification_results['classified_assets'] else 0,
            'unclassified_count': len(classification_results['unclassified_assets']),
            'confidence_factors': [
                'Pattern matching accuracy',
                'Asset naming consistency',
                'Data completeness'
            ]
        } 