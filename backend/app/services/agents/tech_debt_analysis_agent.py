"""
Tech Debt Analysis Agent - Specialized agent for modernization opportunity detection
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult, AgentClarificationRequest, AgentInsight

logger = logging.getLogger(__name__)

class TechDebtAnalysisAgent(BaseDiscoveryAgent):
    """Tech Debt Analysis Agent for modernization and 6R strategy recommendations"""
    
    def __init__(self):
        super().__init__(
            agent_id="tech_debt_analysis_001",
            name="Tech Debt Analysis Specialist", 
            role="Legacy Systems Modernization Expert",
            goal="Identify technical debt and modernization opportunities with 6R strategy recommendations",
            backstory="Expert in legacy system analysis and cloud migration strategy assessment"
        )
        
        # Tech debt indicators
        self.tech_debt_patterns = {
            'legacy_os': ['windows 2008', 'windows 2012', 'centos 6', 'rhel 6', 'ubuntu 14'],
            'legacy_database': ['sql server 2008', 'oracle 11g', 'mysql 5.5'],
            'legacy_middleware': ['jboss 6', 'websphere 8', 'weblogic 10'],
            'legacy_frameworks': ['.net 2.0', '.net 3.5', 'java 6', 'java 7', 'php 5'],
            'end_of_life': ['eol', 'end of life', 'unsupported', 'deprecated']
        }
        
        # 6R Strategy patterns
        self.sixr_indicators = {
            'rehost': ['vm', 'virtual machine', 'lift and shift'],
            'replatform': ['database', 'middleware', 'minor changes'],
            'refactor': ['monolith', 'microservices', 'cloud native'],
            'rearchitect': ['legacy', 'modernize', 'rebuild'],
            'retire': ['unused', 'redundant', 'obsolete'],
            'retain': ['compliance', 'regulatory', 'cannot migrate']
        }
        
        # Risk assessment factors
        self.risk_factors = {
            'high': ['production', 'critical', 'customer facing'],
            'medium': ['business', 'important', 'internal'],
            'low': ['test', 'development', 'backup']
        }
        
        self.logger.info(f"🔧 Tech Debt Analysis Agent initialized")
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute tech debt analysis"""
        start_time = time.time()
        
        try:
            assets = data.get('raw_data', [])
            if not assets:
                return self._create_error_result("No asset data provided")
            
            # Analyze tech debt
            tech_debt_results = await self._analyze_tech_debt(assets)
            
            # Generate 6R recommendations
            sixr_recommendations = await self._generate_sixr_recommendations(assets, tech_debt_results)
            
            # Assess risks
            risk_assessment = await self._assess_migration_risks(assets, tech_debt_results)
            
            # Generate insights
            insights = await self._generate_tech_debt_insights(tech_debt_results, sixr_recommendations, risk_assessment)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_id=self.agent_id,
                status='completed',
                confidence_score=82.0,
                data={
                    'tech_debt_analysis': tech_debt_results,
                    'sixr_recommendations': sixr_recommendations,
                    'risk_assessment': risk_assessment,
                    'modernization_summary': await self._create_modernization_summary(tech_debt_results, sixr_recommendations)
                },
                insights=insights,
                clarifications=[],
                execution_time=execution_time,
                metadata={'assets_analyzed': len(assets)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return self._create_error_result(f"Tech debt analysis failed: {str(e)}", execution_time)
    
    async def _analyze_tech_debt(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technical debt in assets"""
        tech_debt_items = []
        debt_summary = {'high': 0, 'medium': 0, 'low': 0}
        
        for asset in assets:
            asset_id = self._get_asset_id(asset)
            debt_items = await self._identify_tech_debt_items(asset)
            
            for item in debt_items:
                tech_debt_items.append({
                    'asset_id': asset_id,
                    'debt_type': item['type'],
                    'debt_description': item['description'],
                    'severity': item['severity'],
                    'modernization_effort': item['effort']
                })
                debt_summary[item['severity']] += 1
        
        return {
            'total_debt_items': len(tech_debt_items),
            'debt_items': tech_debt_items,
            'debt_summary': debt_summary,
            'debt_categories': await self._categorize_debt_items(tech_debt_items)
        }
    
    async def _identify_tech_debt_items(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify tech debt items for a single asset"""
        debt_items = []
        
        # Check for legacy patterns
        for debt_type, patterns in self.tech_debt_patterns.items():
            for key, value in asset.items():
                if isinstance(value, str):
                    for pattern in patterns:
                        if pattern in value.lower():
                            severity = 'high' if 'eol' in pattern or '2008' in pattern else 'medium'
                            debt_items.append({
                                'type': debt_type,
                                'description': f"Legacy {debt_type.replace('_', ' ')}: {value}",
                                'severity': severity,
                                'effort': 'high' if severity == 'high' else 'medium'
                            })
        
        return debt_items
    
    async def _generate_sixr_recommendations(self, assets: List[Dict[str, Any]], 
                                           tech_debt_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 6R strategy recommendations"""
        recommendations = []
        
        for asset in assets:
            asset_id = self._get_asset_id(asset)
            recommendation = await self._determine_sixr_strategy(asset, tech_debt_results)
            
            recommendations.append({
                'asset_id': asset_id,
                'recommended_strategy': recommendation['strategy'],
                'confidence': recommendation['confidence'],
                'rationale': recommendation['rationale'],
                'effort_estimate': recommendation['effort']
            })
        
        return recommendations
    
    async def _determine_sixr_strategy(self, asset: Dict[str, Any], 
                                     tech_debt_results: Dict[str, Any]) -> Dict[str, Any]:
        """Determine 6R strategy for an asset"""
        asset_text = " ".join(str(v).lower() for v in asset.values() if isinstance(v, str))
        
        # Score each strategy
        strategy_scores = {}
        for strategy, patterns in self.sixr_indicators.items():
            score = sum(1 for pattern in patterns if pattern in asset_text)
            if score > 0:
                strategy_scores[strategy] = score
        
        # Default strategy based on tech debt
        if not strategy_scores:
            # Check for high tech debt
            asset_id = self._get_asset_id(asset)
            high_debt_items = [
                item for item in tech_debt_results.get('debt_items', [])
                if item['asset_id'] == asset_id and item['severity'] == 'high'
            ]
            
            if high_debt_items:
                return {
                    'strategy': 'rearchitect',
                    'confidence': 75.0,
                    'rationale': f"High technical debt detected ({len(high_debt_items)} items)",
                    'effort': 'high'
                }
            else:
                return {
                    'strategy': 'rehost',
                    'confidence': 60.0,
                    'rationale': "No specific indicators found, defaulting to rehost",
                    'effort': 'low'
                }
        
        # Get best strategy
        best_strategy = max(strategy_scores.keys(), key=lambda k: strategy_scores[k])
        confidence = min(strategy_scores[best_strategy] * 20, 95)
        
        effort_map = {
            'rehost': 'low', 'retain': 'low',
            'replatform': 'medium',
            'refactor': 'high', 'rearchitect': 'high', 'retire': 'low'
        }
        
        return {
            'strategy': best_strategy,
            'confidence': confidence,
            'rationale': f"Indicators found: {strategy_scores[best_strategy]} matches",
            'effort': effort_map.get(best_strategy, 'medium')
        }
    
    async def _assess_migration_risks(self, assets: List[Dict[str, Any]], 
                                    tech_debt_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess migration risks"""
        risk_assessments = []
        
        for asset in assets:
            asset_id = self._get_asset_id(asset)
            risk_level = await self._determine_risk_level(asset, tech_debt_results, asset_id)
            
            risk_assessments.append({
                'asset_id': asset_id,
                'risk_level': risk_level['level'],
                'risk_factors': risk_level['factors'],
                'mitigation_strategies': risk_level['mitigations']
            })
        
        # Summary
        risk_summary = {'high': 0, 'medium': 0, 'low': 0}
        for assessment in risk_assessments:
            risk_summary[assessment['risk_level']] += 1
        
        return {
            'risk_assessments': risk_assessments,
            'risk_summary': risk_summary,
            'high_risk_assets': [a for a in risk_assessments if a['risk_level'] == 'high']
        }
    
    async def _determine_risk_level(self, asset: Dict[str, Any], 
                                  tech_debt_results: Dict[str, Any], 
                                  asset_id: str) -> Dict[str, Any]:
        """Determine risk level for an asset"""
        asset_text = " ".join(str(v).lower() for v in asset.values() if isinstance(v, str))
        
        # Check risk factors
        risk_score = 0
        risk_factors = []
        
        for risk_level, patterns in self.risk_factors.items():
            for pattern in patterns:
                if pattern in asset_text:
                    if risk_level == 'high':
                        risk_score += 3
                    elif risk_level == 'medium':
                        risk_score += 2
                    else:
                        risk_score += 1
                    risk_factors.append(f"{risk_level} risk: {pattern}")
        
        # Check tech debt impact
        high_debt_count = len([
            item for item in tech_debt_results.get('debt_items', [])
            if item['asset_id'] == asset_id and item['severity'] == 'high'
        ])
        
        if high_debt_count > 0:
            risk_score += high_debt_count * 2
            risk_factors.append(f"High technical debt: {high_debt_count} items")
        
        # Determine final risk level
        if risk_score >= 6:
            level = 'high'
        elif risk_score >= 3:
            level = 'medium'
        else:
            level = 'low'
        
        mitigations = {
            'high': ['Detailed migration planning', 'Extensive testing', 'Rollback procedures'],
            'medium': ['Standard testing procedures', 'Monitoring setup'],
            'low': ['Basic validation', 'Standard deployment']
        }
        
        return {
            'level': level,
            'factors': risk_factors,
            'mitigations': mitigations.get(level, [])
        }
    
    async def _generate_tech_debt_insights(self, tech_debt_results: Dict[str, Any],
                                         sixr_recommendations: List[Dict[str, Any]],
                                         risk_assessment: Dict[str, Any]) -> List[AgentInsight]:
        """Generate insights about tech debt"""
        insights = []
        
        # High tech debt insight
        high_debt_count = tech_debt_results['debt_summary'].get('high', 0)
        if high_debt_count > 0:
            insights.append(AgentInsight(
                title="High Technical Debt Detected",
                description=f"Found {high_debt_count} high-severity technical debt items requiring immediate attention.",
                confidence_score=90.0,
                category="tech_debt",
                actionable=True,
                action_items=[
                    "Prioritize high-debt assets for modernization",
                    "Consider rearchitecture for heavily indebted systems",
                    "Plan technical debt remediation timeline"
                ]
            ))
        
        # 6R strategy distribution insight
        strategy_counts = {}
        for rec in sixr_recommendations:
            strategy = rec['recommended_strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        if strategy_counts:
            most_common = max(strategy_counts.items(), key=lambda x: x[1])
            insights.append(AgentInsight(
                title="Migration Strategy Distribution",
                description=f"Most common recommended strategy is '{most_common[0]}' for {most_common[1]} assets.",
                confidence_score=85.0,
                category="migration_strategy",
                actionable=True,
                action_items=[
                    f"Develop expertise in {most_common[0]} migration patterns",
                    "Create templates for common migration scenarios",
                    "Plan resource allocation based on strategy distribution"
                ]
            ))
        
        # High risk assets insight
        high_risk_count = len(risk_assessment.get('high_risk_assets', []))
        if high_risk_count > 0:
            insights.append(AgentInsight(
                title="High-Risk Assets Identified",
                description=f"{high_risk_count} assets have been identified as high-risk for migration.",
                confidence_score=95.0,
                category="risk_assessment",
                actionable=True,
                action_items=[
                    "Develop detailed migration plans for high-risk assets",
                    "Implement additional testing and validation",
                    "Consider pilot migrations for risk mitigation"
                ]
            ))
        
        return insights
    
    async def _categorize_debt_items(self, debt_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize debt items by type"""
        categories = {}
        for item in debt_items:
            debt_type = item.get('debt_type', 'unknown')
            categories[debt_type] = categories.get(debt_type, 0) + 1
        return categories
    
    async def _create_modernization_summary(self, tech_debt_results: Dict[str, Any],
                                          sixr_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create modernization summary"""
        strategy_counts = {}
        for rec in sixr_recommendations:
            strategy = rec['recommended_strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_assets_analyzed': len(sixr_recommendations),
            'total_debt_items': tech_debt_results.get('total_debt_items', 0),
            'high_debt_items': tech_debt_results['debt_summary'].get('high', 0),
            'strategy_distribution': strategy_counts,
            'modernization_priority': 'high' if tech_debt_results['debt_summary'].get('high', 0) > 0 else 'medium'
        }
    
    def _get_asset_id(self, asset: Dict[str, Any]) -> str:
        """Get asset identifier"""
        for key in ['id', 'asset_id', 'hostname', 'name']:
            if key in asset and asset[key]:
                return str(asset[key])
        return f"asset_{hash(str(asset)) % 10000}" 