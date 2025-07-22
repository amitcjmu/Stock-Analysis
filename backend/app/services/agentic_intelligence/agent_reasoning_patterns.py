"""
Agent Reasoning Patterns - Core Intelligence Architecture

This module defines the reasoning patterns that CrewAI agents use to analyze assets
and discover business value, risk factors, and modernization opportunities.

Instead of hard-coded rules, agents learn and apply insights through:
1. Pattern discovery and storage in Tier 3 memory
2. Evidence-based reasoning using discovered patterns
3. Continuous learning from user feedback and validation
4. Multi-dimensional analysis covering business, technical, and strategic factors
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ReasoningDimension(str, Enum):
    """Dimensions of asset analysis for agent reasoning"""
    BUSINESS_VALUE = "business_value"
    RISK_ASSESSMENT = "risk_assessment"
    MODERNIZATION_POTENTIAL = "modernization_potential"
    CLOUD_READINESS = "cloud_readiness"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    DEPENDENCY_IMPACT = "dependency_impact"


class ConfidenceLevel(str, Enum):
    """Agent confidence levels in reasoning"""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


class EvidenceType(str, Enum):
    """Types of evidence agents can discover"""
    TECHNOLOGY_STACK = "technology_stack"
    USAGE_PATTERNS = "usage_patterns"
    BUSINESS_CRITICALITY = "business_criticality"
    INTEGRATION_COMPLEXITY = "integration_complexity"
    PERFORMANCE_METRICS = "performance_metrics"
    NAMING_CONVENTIONS = "naming_conventions"
    ENVIRONMENT_CONTEXT = "environment_context"


@dataclass
class ReasoningEvidence:
    """Evidence piece used in agent reasoning"""
    evidence_type: EvidenceType
    field_name: str
    field_value: Any
    confidence: float
    reasoning: str
    supporting_patterns: List[str]  # Pattern IDs that support this evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type.value,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "supporting_patterns": self.supporting_patterns
        }


@dataclass
class AgentReasoning:
    """Complete reasoning result from an agent"""
    dimension: ReasoningDimension
    score: int  # 1-10 for business value, 0-100 for cloud readiness, etc.
    confidence: float  # 0.0 - 1.0
    reasoning_summary: str
    evidence_pieces: List[ReasoningEvidence]
    discovered_patterns: List[Dict[str, Any]]  # New patterns discovered during analysis
    applied_patterns: List[str]  # Pattern IDs that were used in reasoning
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning_summary": self.reasoning_summary,
            "evidence_pieces": [evidence.to_dict() for evidence in self.evidence_pieces],
            "discovered_patterns": self.discovered_patterns,
            "applied_patterns": self.applied_patterns,
            "recommendations": self.recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }


class AssetReasoningPatterns:
    """
    Core reasoning patterns that agents use to analyze assets.
    These patterns guide how agents think about different asset characteristics.
    """
    
    # Business Value Reasoning Indicators
    BUSINESS_VALUE_INDICATORS = {
        "production_database_high_usage": {
            "description": "Production databases with high utilization indicate critical business value",
            "criteria": {
                "environment": "production",
                "asset_type": ["database", "data"],
                "cpu_utilization_percent": ">= 70"
            },
            "confidence_boost": 0.3,
            "reasoning_template": "Production database with {cpu_utilization_percent}% CPU utilization suggests critical business usage and high value"
        },
        
        "customer_facing_applications": {
            "description": "Customer-facing applications typically have high business value",
            "criteria": {
                "naming_patterns": ["customer", "client", "portal", "web", "api", "service"],
                "environment": ["production", "prod"]
            },
            "confidence_boost": 0.25,
            "reasoning_template": "Asset named '{name}' in {environment} environment suggests customer-facing functionality with high business impact"
        },
        
        "financial_system_indicators": {
            "description": "Financial and transaction systems have inherently high business value",
            "criteria": {
                "naming_patterns": ["finance", "billing", "payment", "transaction", "accounting", "invoice"],
                "technology_stack": ["oracle", "sap", "peoplesoft"]
            },
            "confidence_boost": 0.4,
            "reasoning_template": "Financial system '{name}' using {technology_stack} indicates critical business operations"
        }
    }
    
    # Risk Assessment Reasoning Indicators
    RISK_INDICATORS = {
        "legacy_technology_risk": {
            "description": "Legacy technologies pose maintenance and security risks",
            "criteria": {
                "technology_stack": ["java 8", "windows server 2012", "oracle 11g", "sql server 2012", ".net framework 4"]
            },
            "risk_level": "medium",
            "confidence_boost": 0.2,
            "reasoning_template": "Legacy technology {technology_stack} poses maintenance and security risks"
        },
        
        "unsupported_platforms": {
            "description": "Unsupported platforms create significant operational risks",
            "criteria": {
                "technology_stack": ["centos 6", "ubuntu 14", "windows server 2008", "java 7"]
            },
            "risk_level": "high",
            "confidence_boost": 0.35,
            "reasoning_template": "Unsupported platform {technology_stack} creates critical security and compliance risks"
        },
        
        "single_point_of_failure": {
            "description": "Systems without redundancy pose availability risks",
            "criteria": {
                "naming_patterns": ["single", "standalone", "solo"],
                "environment": "production"
            },
            "risk_level": "medium",
            "confidence_boost": 0.2,
            "reasoning_template": "Single instance {name} in production environment poses availability risk"
        }
    }
    
    # Modernization Potential Indicators
    MODERNIZATION_INDICATORS = {
        "cloud_native_technologies": {
            "description": "Modern technologies are easier to modernize",
            "criteria": {
                "technology_stack": ["kubernetes", "docker", "microservices", "spring boot", ".net core", "nodejs"]
            },
            "modernization_potential": "high",
            "confidence_boost": 0.3,
            "reasoning_template": "Modern technology {technology_stack} has high cloud modernization potential"
        },
        
        "containerization_ready": {
            "description": "Stateless applications are ideal for containerization",
            "criteria": {
                "asset_type": ["web application", "api", "service"],
                "technology_stack": ["spring", "express", "flask", "fastapi"]
            },
            "modernization_potential": "high",
            "confidence_boost": 0.25,
            "reasoning_template": "Stateless {asset_type} using {technology_stack} is ideal for containerization"
        },
        
        "database_modernization": {
            "description": "Standard databases can be modernized to managed cloud services",
            "criteria": {
                "asset_type": "database",
                "technology_stack": ["postgresql", "mysql", "sql server", "oracle"]
            },
            "modernization_potential": "medium",
            "confidence_boost": 0.2,
            "reasoning_template": "{technology_stack} database can be migrated to managed cloud database services"
        }
    }


class AgentReasoningEngine:
    """
    Engine that powers agent reasoning using discovered patterns and evidence.
    This replaces hard-coded rules with dynamic, learning-based intelligence.
    """
    
    def __init__(self, memory_manager, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger
        
    async def analyze_asset_business_value(self, asset_data: Dict[str, Any], agent_name: str) -> AgentReasoning:
        """
        Analyze business value using agent reasoning instead of rules.
        Agents look for evidence and patterns, then reason about business impact.
        """
        evidence_pieces = []
        discovered_patterns = []
        applied_patterns = []
        
        # 1. Search for existing patterns that might apply
        from app.models.agent_memory import PatternType
        from app.services.agentic_memory import MemoryQuery
        
        search_query = MemoryQuery(
            query_text="business value database production critical",
            memory_tiers=['semantic'],
            pattern_types=[PatternType.BUSINESS_VALUE_INDICATOR],
            min_confidence=0.6,
            max_results=10
        )
        
        existing_patterns = await self.memory_manager.query_memory(search_query)
        
        # 2. Analyze evidence from the asset
        evidence_pieces.extend(await self._analyze_technology_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_usage_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_naming_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_environment_evidence(asset_data))
        
        # 3. Apply discovered patterns to evidence
        for pattern_result in existing_patterns:
            if pattern_result.tier == 'semantic':
                pattern_data = pattern_result.content
                pattern_logic = pattern_data.get('pattern_data', {})
                
                if self._pattern_matches_asset(pattern_logic, asset_data):
                    applied_patterns.append(pattern_data['id'])
                    confidence_boost = min(pattern_data['confidence'], 0.3)
                    
                    # Create evidence based on pattern match
                    evidence = ReasoningEvidence(
                        evidence_type=EvidenceType.BUSINESS_CRITICALITY,
                        field_name="pattern_match",
                        field_value=pattern_data['name'],
                        confidence=pattern_data['confidence'],
                        reasoning=f"Asset matches learned pattern: {pattern_data['description']}",
                        supporting_patterns=[pattern_data['id']]
                    )
                    evidence_pieces.append(evidence)
        
        # 4. Discover new patterns during analysis
        new_patterns = await self._discover_business_value_patterns(asset_data, evidence_pieces, agent_name)
        discovered_patterns.extend(new_patterns)
        
        # 5. Reason about business value score
        business_value_score, confidence, reasoning = self._calculate_business_value_reasoning(
            asset_data, evidence_pieces, applied_patterns
        )
        
        # 6. Generate recommendations
        recommendations = self._generate_business_value_recommendations(
            asset_data, evidence_pieces, business_value_score
        )
        
        return AgentReasoning(
            dimension=ReasoningDimension.BUSINESS_VALUE,
            score=business_value_score,
            confidence=confidence,
            reasoning_summary=reasoning,
            evidence_pieces=evidence_pieces,
            discovered_patterns=discovered_patterns,
            applied_patterns=applied_patterns,
            recommendations=recommendations
        )
    
    async def analyze_asset_risk_assessment(self, asset_data: Dict[str, Any], agent_name: str) -> AgentReasoning:
        """Analyze risk factors using agent reasoning and pattern matching"""
        evidence_pieces = []
        discovered_patterns = []
        applied_patterns = []
        
        # Search for risk patterns
        from app.models.agent_memory import PatternType
        from app.services.agentic_memory import MemoryQuery
        
        search_query = MemoryQuery(
            query_text="risk security legacy unsupported vulnerability",
            memory_tiers=['semantic'],
            pattern_types=[PatternType.RISK_FACTOR],
            min_confidence=0.5,
            max_results=10
        )
        
        existing_patterns = await self.memory_manager.query_memory(search_query)
        
        # Analyze risk evidence
        evidence_pieces.extend(await self._analyze_technology_risk_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_security_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_compliance_evidence(asset_data))
        
        # Apply risk patterns
        for pattern_result in existing_patterns:
            if pattern_result.tier == 'semantic':
                pattern_data = pattern_result.content
                pattern_logic = pattern_data.get('pattern_data', {})
                
                if self._pattern_matches_asset(pattern_logic, asset_data):
                    applied_patterns.append(pattern_data['id'])
                    
                    evidence = ReasoningEvidence(
                        evidence_type=EvidenceType.TECHNOLOGY_STACK,
                        field_name="risk_pattern_match",
                        field_value=pattern_data['name'],
                        confidence=pattern_data['confidence'],
                        reasoning=f"Asset matches risk pattern: {pattern_data['description']}",
                        supporting_patterns=[pattern_data['id']]
                    )
                    evidence_pieces.append(evidence)
        
        # Discover new risk patterns
        new_patterns = await self._discover_risk_patterns(asset_data, evidence_pieces, agent_name)
        discovered_patterns.extend(new_patterns)
        
        # Calculate risk assessment
        risk_level, confidence, reasoning = self._calculate_risk_reasoning(
            asset_data, evidence_pieces, applied_patterns
        )
        
        recommendations = self._generate_risk_recommendations(
            asset_data, evidence_pieces, risk_level
        )
        
        return AgentReasoning(
            dimension=ReasoningDimension.RISK_ASSESSMENT,
            score=self._risk_level_to_score(risk_level),
            confidence=confidence,
            reasoning_summary=reasoning,
            evidence_pieces=evidence_pieces,
            discovered_patterns=discovered_patterns,
            applied_patterns=applied_patterns,
            recommendations=recommendations
        )
    
    async def analyze_modernization_potential(self, asset_data: Dict[str, Any], agent_name: str) -> AgentReasoning:
        """Analyze modernization opportunities using agent reasoning"""
        evidence_pieces = []
        discovered_patterns = []
        applied_patterns = []
        
        # Search for modernization patterns
        from app.models.agent_memory import PatternType
        from app.services.agentic_memory import MemoryQuery
        
        search_query = MemoryQuery(
            query_text="modernization cloud migration containerization microservices",
            memory_tiers=['semantic'],
            pattern_types=[PatternType.MODERNIZATION_OPPORTUNITY],
            min_confidence=0.5,
            max_results=10
        )
        
        existing_patterns = await self.memory_manager.query_memory(search_query)
        
        # Analyze modernization evidence
        evidence_pieces.extend(await self._analyze_architecture_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_cloud_readiness_evidence(asset_data))
        evidence_pieces.extend(await self._analyze_technology_modernization_evidence(asset_data))
        
        # Apply modernization patterns
        for pattern_result in existing_patterns:
            if pattern_result.tier == 'semantic':
                pattern_data = pattern_result.content
                pattern_logic = pattern_data.get('pattern_data', {})
                
                if self._pattern_matches_asset(pattern_logic, asset_data):
                    applied_patterns.append(pattern_data['id'])
                    
                    evidence = ReasoningEvidence(
                        evidence_type=EvidenceType.TECHNOLOGY_STACK,
                        field_name="modernization_pattern_match",
                        field_value=pattern_data['name'],
                        confidence=pattern_data['confidence'],
                        reasoning=f"Asset matches modernization pattern: {pattern_data['description']}",
                        supporting_patterns=[pattern_data['id']]
                    )
                    evidence_pieces.append(evidence)
        
        # Discover new modernization patterns
        new_patterns = await self._discover_modernization_patterns(asset_data, evidence_pieces, agent_name)
        discovered_patterns.extend(new_patterns)
        
        # Calculate modernization potential
        modernization_score, confidence, reasoning = self._calculate_modernization_reasoning(
            asset_data, evidence_pieces, applied_patterns
        )
        
        recommendations = self._generate_modernization_recommendations(
            asset_data, evidence_pieces, modernization_score
        )
        
        return AgentReasoning(
            dimension=ReasoningDimension.MODERNIZATION_POTENTIAL,
            score=modernization_score,
            confidence=confidence,
            reasoning_summary=reasoning,
            evidence_pieces=evidence_pieces,
            discovered_patterns=discovered_patterns,
            applied_patterns=applied_patterns,
            recommendations=recommendations
        )
    
    # Evidence Analysis Methods
    
    async def _analyze_technology_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze technology stack for business value evidence"""
        evidence = []
        
        tech_stack = asset_data.get('technology_stack', '').lower()
        if not tech_stack:
            return evidence
        
        # High-value technology indicators
        high_value_techs = ['oracle', 'sap', 'peoplesoft', 'mainframe', 'postgresql', 'kubernetes']
        for tech in high_value_techs:
            if tech in tech_stack:
                evidence.append(ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="technology_stack",
                    field_value=tech,
                    confidence=0.7,
                    reasoning=f"Technology {tech} typically indicates high business value systems",
                    supporting_patterns=[]
                ))
        
        return evidence
    
    async def _analyze_usage_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze usage patterns for business value evidence"""
        evidence = []
        
        # CPU utilization indicates usage intensity
        cpu_util = asset_data.get('cpu_utilization_percent')
        if cpu_util is not None:
            if cpu_util >= 70:
                evidence.append(ReasoningEvidence(
                    evidence_type=EvidenceType.PERFORMANCE_METRICS,
                    field_name="cpu_utilization_percent",
                    field_value=cpu_util,
                    confidence=0.8,
                    reasoning=f"High CPU utilization ({cpu_util}%) indicates heavy business usage",
                    supporting_patterns=[]
                ))
        
        return evidence
    
    async def _analyze_naming_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze naming patterns for business value clues"""
        evidence = []
        
        name = asset_data.get('name', '').lower()
        if not name:
            return evidence
        
        # Business-critical naming patterns
        critical_keywords = ['prod', 'customer', 'financial', 'billing', 'payment', 'core', 'main']
        for keyword in critical_keywords:
            if keyword in name:
                evidence.append(ReasoningEvidence(
                    evidence_type=EvidenceType.NAMING_CONVENTIONS,
                    field_name="name",
                    field_value=keyword,
                    confidence=0.6,
                    reasoning=f"Name contains '{keyword}' suggesting business-critical functionality",
                    supporting_patterns=[]
                ))
        
        return evidence
    
    async def _analyze_environment_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze environment context for business value"""
        evidence = []
        
        environment = asset_data.get('environment', '').lower()
        if environment in ['production', 'prod']:
            evidence.append(ReasoningEvidence(
                evidence_type=EvidenceType.ENVIRONMENT_CONTEXT,
                field_name="environment",
                field_value=environment,
                confidence=0.9,
                reasoning="Production environment indicates live business operations",
                supporting_patterns=[]
            ))
        
        return evidence
    
    async def _analyze_technology_risk_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze technology stack for risk factors"""
        evidence = []
        
        tech_stack = asset_data.get('technology_stack', '').lower()
        if not tech_stack:
            return evidence
        
        # Legacy/risky technologies
        risky_techs = {
            'java 8': 'Legacy Java version with security vulnerabilities',
            'windows server 2012': 'End-of-life Windows Server version',
            'oracle 11g': 'Unsupported Oracle database version',
            'centos 6': 'End-of-life CentOS version'
        }
        
        for tech, risk_reason in risky_techs.items():
            if tech in tech_stack:
                evidence.append(ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="technology_stack",
                    field_value=tech,
                    confidence=0.8,
                    reasoning=risk_reason,
                    supporting_patterns=[]
                ))
        
        return evidence
    
    async def _analyze_security_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze security-related risk evidence"""
        # Placeholder for security analysis
        return []
    
    async def _analyze_compliance_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze compliance-related risk evidence"""
        # Placeholder for compliance analysis
        return []
    
    async def _analyze_architecture_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze architecture for modernization potential"""
        evidence = []
        
        asset_type = asset_data.get('asset_type', '').lower()
        tech_stack = asset_data.get('technology_stack', '').lower()
        
        # Modern architecture indicators
        modern_indicators = {
            'microservices': 'Microservices architecture is cloud-native ready',
            'kubernetes': 'Kubernetes indicates containerized, modern deployment',
            'docker': 'Docker containers enable cloud modernization',
            'spring boot': 'Spring Boot applications are modernization-friendly'
        }
        
        for indicator, reasoning in modern_indicators.items():
            if indicator in tech_stack:
                evidence.append(ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="technology_stack",
                    field_value=indicator,
                    confidence=0.8,
                    reasoning=reasoning,
                    supporting_patterns=[]
                ))
        
        return evidence
    
    async def _analyze_cloud_readiness_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze cloud readiness indicators"""
        evidence = []
        
        # Stateless applications are cloud-ready
        asset_type = asset_data.get('asset_type', '').lower()
        if 'api' in asset_type or 'service' in asset_type:
            evidence.append(ReasoningEvidence(
                evidence_type=EvidenceType.TECHNOLOGY_STACK,
                field_name="asset_type",
                field_value=asset_type,
                confidence=0.7,
                reasoning="Stateless services are ideal for cloud deployment",
                supporting_patterns=[]
            ))
        
        return evidence
    
    async def _analyze_technology_modernization_evidence(self, asset_data: Dict[str, Any]) -> List[ReasoningEvidence]:
        """Analyze technology modernization readiness"""
        # Placeholder for detailed technology modernization analysis
        return []
    
    # Pattern Discovery Methods
    
    async def _discover_business_value_patterns(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], agent_name: str) -> List[Dict[str, Any]]:
        """Discover new business value patterns during analysis"""
        patterns = []
        
        # Example: If we see high CPU + production + database, discover pattern
        has_high_cpu = any(e.field_name == "cpu_utilization_percent" and e.field_value >= 70 for e in evidence)
        has_production = any(e.field_value == "production" for e in evidence)
        is_database = asset_data.get('asset_type', '').lower() == 'database'
        
        if has_high_cpu and has_production and is_database:
            pattern = {
                "pattern_type": "business_value_indicator",
                "pattern_name": "High-Usage Production Database Pattern",
                "pattern_description": "Production databases with high CPU utilization indicate critical business systems",
                "pattern_logic": {
                    "environment": "production",
                    "asset_type": "database",
                    "cpu_utilization_percent": {"operator": ">=", "value": 70}
                },
                "confidence_score": 0.85,
                "evidence_assets": [asset_data.get('id')] if asset_data.get('id') else []
            }
            patterns.append(pattern)
        
        return patterns
    
    async def _discover_risk_patterns(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], agent_name: str) -> List[Dict[str, Any]]:
        """Discover new risk patterns during analysis"""
        patterns = []
        
        # Example: Legacy tech + production environment = high risk
        has_legacy_tech = any(e.evidence_type == EvidenceType.TECHNOLOGY_STACK and 
                            any(legacy in str(e.field_value) for legacy in ['java 8', 'windows server 2012']) 
                            for e in evidence)
        is_production = asset_data.get('environment', '').lower() in ['production', 'prod']
        
        if has_legacy_tech and is_production:
            pattern = {
                "pattern_type": "risk_factor",
                "pattern_name": "Legacy Technology in Production Risk",
                "pattern_description": "Legacy technologies in production environments pose significant operational risks",
                "pattern_logic": {
                    "environment": "production",
                    "technology_stack": {"contains_any": ["java 8", "windows server 2012", "oracle 11g"]}
                },
                "confidence_score": 0.8,
                "evidence_assets": [asset_data.get('id')] if asset_data.get('id') else []
            }
            patterns.append(pattern)
        
        return patterns
    
    async def _discover_modernization_patterns(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], agent_name: str) -> List[Dict[str, Any]]:
        """Discover new modernization patterns during analysis"""
        patterns = []
        
        # Example: Spring Boot + API = high modernization potential
        tech_stack = asset_data.get('technology_stack', '').lower()
        asset_type = asset_data.get('asset_type', '').lower()
        
        if 'spring boot' in tech_stack and 'api' in asset_type:
            pattern = {
                "pattern_type": "modernization_opportunity",
                "pattern_name": "Spring Boot API Modernization Ready",
                "pattern_description": "Spring Boot APIs are excellent candidates for containerization and cloud migration",
                "pattern_logic": {
                    "technology_stack": {"contains": "spring boot"},
                    "asset_type": {"contains": "api"}
                },
                "confidence_score": 0.9,
                "evidence_assets": [asset_data.get('id')] if asset_data.get('id') else []
            }
            patterns.append(pattern)
        
        return patterns
    
    # Reasoning Calculation Methods
    
    def _calculate_business_value_reasoning(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], 
                                          applied_patterns: List[str]) -> Tuple[int, float, str]:
        """Calculate business value score with reasoning"""
        base_score = 5  # Default medium value
        confidence_factors = []
        reasoning_parts = []
        
        # Analyze evidence for scoring
        for evidence_piece in evidence:
            if evidence_piece.evidence_type == EvidenceType.ENVIRONMENT_CONTEXT:
                if evidence_piece.field_value == "production":
                    base_score += 2
                    confidence_factors.append(evidence_piece.confidence)
                    reasoning_parts.append("Production environment (+2 points)")
            
            elif evidence_piece.evidence_type == EvidenceType.PERFORMANCE_METRICS:
                if evidence_piece.field_name == "cpu_utilization_percent" and evidence_piece.field_value >= 70:
                    base_score += 2
                    confidence_factors.append(evidence_piece.confidence)
                    reasoning_parts.append(f"High CPU utilization ({evidence_piece.field_value}%) (+2 points)")
            
            elif evidence_piece.evidence_type == EvidenceType.TECHNOLOGY_STACK:
                if evidence_piece.field_value in ['oracle', 'sap', 'mainframe']:
                    base_score += 1
                    confidence_factors.append(evidence_piece.confidence)
                    reasoning_parts.append(f"Enterprise technology {evidence_piece.field_value} (+1 point)")
        
        # Pattern bonuses
        if applied_patterns:
            base_score += len(applied_patterns)
            reasoning_parts.append(f"Applied {len(applied_patterns)} learned patterns (+{len(applied_patterns)} points)")
        
        # Ensure score is in valid range
        business_value_score = max(1, min(10, base_score))
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Generate reasoning summary
        reasoning_summary = f"Business value score: {business_value_score}/10. " + "; ".join(reasoning_parts)
        
        return business_value_score, overall_confidence, reasoning_summary
    
    def _calculate_risk_reasoning(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], 
                                applied_patterns: List[str]) -> Tuple[str, float, str]:
        """Calculate risk level with reasoning"""
        risk_factors = 0
        confidence_factors = []
        reasoning_parts = []
        
        # Analyze evidence for risk scoring
        for evidence_piece in evidence:
            if evidence_piece.evidence_type == EvidenceType.TECHNOLOGY_STACK:
                risk_factors += 1
                confidence_factors.append(evidence_piece.confidence)
                reasoning_parts.append(evidence_piece.reasoning)
        
        # Determine risk level
        if risk_factors >= 3:
            risk_level = "high"
        elif risk_factors >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        reasoning_summary = f"Risk level: {risk_level}. " + "; ".join(reasoning_parts)
        
        return risk_level, overall_confidence, reasoning_summary
    
    def _calculate_modernization_reasoning(self, asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], 
                                         applied_patterns: List[str]) -> Tuple[int, float, str]:
        """Calculate modernization score with reasoning"""
        base_score = 50  # Default medium modernization potential
        confidence_factors = []
        reasoning_parts = []
        
        # Analyze evidence for modernization scoring
        for evidence_piece in evidence:
            if evidence_piece.evidence_type == EvidenceType.TECHNOLOGY_STACK:
                modern_techs = ['kubernetes', 'docker', 'microservices', 'spring boot']
                if any(tech in str(evidence_piece.field_value) for tech in modern_techs):
                    base_score += 20
                    confidence_factors.append(evidence_piece.confidence)
                    reasoning_parts.append(f"Modern technology {evidence_piece.field_value} (+20 points)")
        
        modernization_score = max(0, min(100, base_score))
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        reasoning_summary = f"Modernization potential: {modernization_score}/100. " + "; ".join(reasoning_parts)
        
        return modernization_score, overall_confidence, reasoning_summary
    
    # Helper Methods
    
    def _pattern_matches_asset(self, pattern_logic: Dict[str, Any], asset_data: Dict[str, Any]) -> bool:
        """Check if a pattern matches an asset"""
        try:
            for field, criteria in pattern_logic.items():
                asset_value = asset_data.get(field)
                if asset_value is None:
                    continue
                
                if isinstance(criteria, dict):
                    if "operator" in criteria and "value" in criteria:
                        # Handle operator-based criteria
                        operator = criteria["operator"]
                        expected_value = criteria["value"]
                        
                        if operator == ">=" and isinstance(asset_value, (int, float)):
                            if asset_value < expected_value:
                                return False
                        elif operator == "contains" and isinstance(asset_value, str):
                            if expected_value.lower() not in asset_value.lower():
                                return False
                elif isinstance(criteria, list):
                    # Handle list-based criteria (any match)
                    if not any(str(item).lower() in str(asset_value).lower() for item in criteria):
                        return False
                else:
                    # Handle direct value match
                    if str(criteria).lower() != str(asset_value).lower():
                        return False
            
            return True
        except Exception as e:
            self.logger.warning(f"Pattern matching error: {e}")
            return False
    
    def _risk_level_to_score(self, risk_level: str) -> int:
        """Convert risk level to numeric score"""
        risk_mapping = {
            "low": 1,
            "medium": 5,
            "high": 8,
            "critical": 10
        }
        return risk_mapping.get(risk_level, 5)
    
    def _generate_business_value_recommendations(self, asset_data: Dict[str, Any], 
                                               evidence: List[ReasoningEvidence], score: int) -> List[str]:
        """Generate recommendations based on business value analysis"""
        recommendations = []
        
        if score >= 8:
            recommendations.append("High business value asset - prioritize for migration and ensure minimal downtime")
            recommendations.append("Consider implementing redundancy and backup strategies")
        elif score >= 6:
            recommendations.append("Medium-high business value - plan careful migration with testing phases")
        else:
            recommendations.append("Lower business impact - suitable for experimental migration approaches")
        
        return recommendations
    
    def _generate_risk_recommendations(self, asset_data: Dict[str, Any], 
                                     evidence: List[ReasoningEvidence], risk_level: str) -> List[str]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.append("High risk asset - prioritize security updates and migration")
            recommendations.append("Implement additional monitoring and security controls")
        elif risk_level == "medium":
            recommendations.append("Medium risk - plan migration to address security and compliance concerns")
        else:
            recommendations.append("Low risk asset - standard migration approach appropriate")
        
        return recommendations
    
    def _generate_modernization_recommendations(self, asset_data: Dict[str, Any], 
                                              evidence: List[ReasoningEvidence], score: int) -> List[str]:
        """Generate recommendations based on modernization analysis"""
        recommendations = []
        
        if score >= 80:
            recommendations.append("Excellent modernization candidate - consider containerization and cloud-native patterns")
            recommendations.append("Suitable for microservices architecture and DevOps practices")
        elif score >= 60:
            recommendations.append("Good modernization potential - plan phased approach to cloud adoption")
        else:
            recommendations.append("Limited modernization potential - consider lift-and-shift approach")
        
        return recommendations