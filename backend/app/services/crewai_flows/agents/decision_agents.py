"""
Agent Decision Framework

This module implements autonomous decision-making agents that replace hardcoded
business logic with intelligent, context-aware decisions.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

from crewai import Agent, Task, Crew
from crewai.agent import Agent as CrewAIAgent

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

logger = logging.getLogger(__name__)


class PhaseAction(Enum):
    """Actions that agents can recommend for phase transitions"""
    PROCEED = "proceed"
    PAUSE = "pause"
    SKIP = "skip"
    RETRY = "retry"
    FAIL = "fail"


class AgentDecision:
    """Structured decision from an agent"""
    
    def __init__(
        self,
        action: PhaseAction,
        next_phase: str,
        confidence: float,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.action = action
        self.next_phase = next_phase
        self.confidence = confidence
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for serialization"""
        return {
            "action": self.action.value,
            "next_phase": self.next_phase,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseDecisionAgent(Agent, ABC):
    """Base class for all decision-making agents"""
    
    def __init__(self, role: str, goal: str, backstory: str, **kwargs):
        """Initialize base decision agent"""
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )
        
    @abstractmethod
    async def analyze_phase_transition(
        self,
        current_phase: str,
        results: Any,
        state: UnifiedDiscoveryFlowState
    ) -> AgentDecision:
        """
        Analyze current state and results to decide next phase transition.
        
        Args:
            current_phase: Current phase name
            results: Results from current phase execution
            state: Current flow state
            
        Returns:
            AgentDecision with recommended action
        """
        pass
    
    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate overall confidence score from multiple factors.
        
        Args:
            factors: Dictionary of factor_name -> confidence (0-1)
            
        Returns:
            Weighted average confidence score
        """
        if not factors:
            return 0.0
            
        total_weight = sum(factors.values())
        if total_weight == 0:
            return 0.0
            
        return min(1.0, total_weight / len(factors))


class PhaseTransitionAgent(BaseDecisionAgent):
    """Agent that decides phase transitions based on data analysis and business context"""
    
    def __init__(self):
        super().__init__(
            role="Flow Orchestration Strategist",
            goal="Determine optimal phase transitions based on data quality, business context, and flow objectives",
            backstory="""You are an expert in workflow optimization with deep understanding of:
            - Data quality assessment and validation
            - Business process optimization
            - Risk management and decision theory
            - Migration best practices
            
            You make intelligent decisions about when to proceed, pause for human input, 
            or skip phases based on comprehensive analysis of the current situation."""
        )
        
    async def analyze_phase_transition(
        self,
        current_phase: str,
        results: Any,
        state: UnifiedDiscoveryFlowState
    ) -> AgentDecision:
        """Analyze and decide on phase transition"""
        logger.info(f"🤖 Analyzing phase transition from: {current_phase}")
        
        # Analyze current state
        analysis = self._analyze_current_state(current_phase, results, state)
        
        # Make decision based on analysis
        decision = self._make_transition_decision(current_phase, analysis)
        
        logger.info(f"📊 Decision: {decision.action.value} -> {decision.next_phase} (confidence: {decision.confidence})")
        
        return decision
    
    def _analyze_current_state(
        self,
        phase: str,
        results: Any,
        state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Comprehensive state analysis"""
        analysis = {
            "phase": phase,
            "has_errors": self._check_for_errors(state),
            "data_quality": self._assess_data_quality(state),
            "completeness": self._assess_completeness(phase, state),
            "complexity": self._assess_complexity(state),
            "risk_factors": self._identify_risk_factors(state)
        }
        
        # Phase-specific analysis
        if phase == "data_import":
            analysis["import_metrics"] = self._analyze_import_metrics(results, state)
        elif phase == "field_mapping":
            analysis["mapping_quality"] = self._analyze_mapping_quality(state)
        elif phase == "data_cleansing":
            analysis["cleansing_impact"] = self._analyze_cleansing_impact(results, state)
            
        return analysis
    
    def _make_transition_decision(
        self,
        current_phase: str,
        analysis: Dict[str, Any]
    ) -> AgentDecision:
        """Make decision based on analysis"""
        
        # Check for critical errors first
        if analysis["has_errors"]:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.95,
                reasoning=f"Critical errors detected in {current_phase} phase that prevent continuation",
                metadata={"errors": analysis.get("errors", [])}
            )
        
        # Phase-specific decision logic
        if current_phase == "data_import":
            return self._decide_after_import(analysis)
        elif current_phase == "field_mapping":
            return self._decide_after_mapping(analysis)
        elif current_phase == "data_cleansing":
            return self._decide_after_cleansing(analysis)
        else:
            # Default progression
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=self._get_next_phase(current_phase),
                confidence=0.8,
                reasoning=f"Phase {current_phase} completed successfully",
                metadata=analysis
            )
    
    def _decide_after_import(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after data import phase"""
        metrics = analysis.get("import_metrics", {})
        data_quality = analysis.get("data_quality", 0)
        
        if data_quality < 0.3:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.9,
                reasoning="Data quality is too poor to proceed with migration. "
                         "Source data needs to be cleaned or re-exported.",
                metadata={
                    "data_quality_score": data_quality,
                    "recommendations": [
                        "Review source data export process",
                        "Check for data corruption",
                        "Validate export format"
                    ]
                }
            )
        
        # Check if field mapping review is needed
        complexity = analysis.get("complexity", 0)
        if complexity > 0.7 or self._has_ambiguous_fields(analysis):
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=0.85,
                reasoning="Complex or ambiguous field mappings detected that require human review",
                metadata={
                    "complexity_score": complexity,
                    "ambiguous_fields": analysis.get("ambiguous_fields", [])
                }
            )
        
        # High quality data can skip manual review
        if data_quality > 0.9 and complexity < 0.3:
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="data_cleansing",
                confidence=0.95,
                reasoning="High quality data with clear field mappings. "
                         "Automated mapping is sufficient.",
                metadata={
                    "auto_mapped": True,
                    "quality_score": data_quality
                }
            )
        
        # Standard flow - generate suggestions
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="field_mapping",
            confidence=0.8,
            reasoning="Data imported successfully. Proceeding to field mapping.",
            metadata=metrics
        )
    
    def _decide_after_mapping(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after field mapping phase"""
        mapping_quality = analysis.get("mapping_quality", {})
        confidence = mapping_quality.get("confidence", 0)
        missing_critical = mapping_quality.get("missing_critical_fields", [])
        
        # Dynamic threshold based on data characteristics
        required_confidence = self._calculate_required_confidence(analysis)
        
        if missing_critical:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=0.95,
                reasoning=f"Critical fields are not mapped: {', '.join(missing_critical)}. "
                         "Human intervention required.",
                metadata={
                    "missing_fields": missing_critical,
                    "user_action": "map_critical_fields"
                }
            )
        
        if confidence < required_confidence:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=0.8,
                reasoning=f"Mapping confidence ({confidence:.1%}) is below required threshold ({required_confidence:.1%}). "
                         "Human review recommended.",
                metadata={
                    "current_confidence": confidence,
                    "required_confidence": required_confidence,
                    "user_action": "review_mappings"
                }
            )
        
        # High confidence - proceed automatically
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="data_cleansing",
            confidence=confidence,
            reasoning=f"Field mappings have high confidence ({confidence:.1%}). "
                     "Proceeding to data cleansing.",
            metadata=mapping_quality
        )
    
    def _decide_after_cleansing(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after data cleansing phase"""
        cleansing_impact = analysis.get("cleansing_impact", {})
        failure_rate = cleansing_impact.get("failure_rate", 0)
        
        if failure_rate > 0.1:  # More than 10% failures
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="data_cleansing",
                confidence=0.9,
                reasoning=f"High cleansing failure rate ({failure_rate:.1%}). "
                         "Manual review of failed records required.",
                metadata={
                    "failure_rate": failure_rate,
                    "failed_records": cleansing_impact.get("failed_records", []),
                    "user_action": "review_failures"
                }
            )
        
        # Successful cleansing - proceed to asset creation
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="asset_inventory",
            confidence=0.9,
            reasoning="Data cleansing completed successfully. "
                     "Proceeding to asset inventory creation.",
            metadata=cleansing_impact
        )
    
    # Helper methods
    
    def _check_for_errors(self, state: UnifiedDiscoveryFlowState) -> bool:
        """Check if there are critical errors in the state"""
        if hasattr(state, 'errors') and state.errors:
            return len([e for e in state.errors if e.get('severity') == 'critical']) > 0
        return False
    
    def _assess_data_quality(self, state: UnifiedDiscoveryFlowState) -> float:
        """Assess overall data quality (0-1)"""
        if not hasattr(state, 'raw_data') or not state.raw_data:
            return 0.0
            
        quality_score = 1.0
        sample_size = min(100, len(state.raw_data))
        
        for record in state.raw_data[:sample_size]:
            # Check for missing values
            missing_count = sum(1 for v in record.values() if v is None or v == "")
            if len(record) > 0:
                quality_score -= (missing_count / len(record)) * 0.01
                
        return max(0.0, min(1.0, quality_score))
    
    def _assess_completeness(self, phase: str, state: UnifiedDiscoveryFlowState) -> float:
        """Assess phase completeness"""
        if hasattr(state, 'phase_completion'):
            return 1.0 if state.phase_completion.get(phase, False) else 0.0
        return 0.0
    
    def _assess_complexity(self, state: UnifiedDiscoveryFlowState) -> float:
        """Assess data/mapping complexity"""
        if not hasattr(state, 'raw_data') or not state.raw_data:
            return 0.0
            
        # Analyze field names for complexity indicators
        complexity_score = 0.0
        if state.raw_data:
            field_names = list(state.raw_data[0].keys())
            for field in field_names:
                field_lower = field.lower()
                # Complex field indicators
                if any(ind in field_lower for ind in ['custom', 'legacy', 'temp', '_old']):
                    complexity_score += 0.1
                if len(field) > 30:
                    complexity_score += 0.05
                    
        return min(1.0, complexity_score)
    
    def _identify_risk_factors(self, state: UnifiedDiscoveryFlowState) -> List[str]:
        """Identify risk factors in current state"""
        risks = []
        
        # Check data volume
        if hasattr(state, 'raw_data') and len(state.raw_data) > 10000:
            risks.append("large_data_volume")
            
        # Check for sensitive data patterns
        if self._has_sensitive_data_patterns(state):
            risks.append("sensitive_data_detected")
            
        return risks
    
    def _analyze_import_metrics(self, results: Any, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Analyze data import metrics"""
        return {
            "total_records": len(state.raw_data) if hasattr(state, 'raw_data') else 0,
            "field_count": len(state.raw_data[0]) if state.raw_data else 0,
            "import_duration": results.get("duration", 0) if isinstance(results, dict) else 0
        }
    
    def _analyze_mapping_quality(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Analyze field mapping quality"""
        if not hasattr(state, 'field_mappings'):
            return {"confidence": 0, "missing_critical_fields": []}
            
        # Identify which fields are actually critical based on data
        critical_fields = self._identify_critical_fields(state)
        mapped_fields = set(state.field_mappings.keys())
        missing_critical = [f for f in critical_fields if f not in mapped_fields]
        
        confidence = getattr(state, 'field_mapping_confidence', 0.5)
        
        return {
            "confidence": confidence,
            "total_fields": len(state.field_mappings),
            "critical_fields": critical_fields,
            "missing_critical_fields": missing_critical
        }
    
    def _analyze_cleansing_impact(self, results: Any, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Analyze data cleansing impact"""
        if not isinstance(results, dict):
            return {"failure_rate": 0}
            
        total_records = results.get("total_records", 0)
        failed_records = results.get("failed_records", 0)
        
        failure_rate = failed_records / total_records if total_records > 0 else 0
        
        return {
            "failure_rate": failure_rate,
            "records_cleaned": results.get("records_cleaned", 0),
            "quality_improvement": results.get("quality_improvement", 0)
        }
    
    def _has_ambiguous_fields(self, analysis: Dict[str, Any]) -> bool:
        """Check for ambiguous field mappings"""
        # This would be implemented with actual field analysis
        return analysis.get("complexity", 0) > 0.6
    
    def _calculate_required_confidence(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate required confidence threshold dynamically based on:
        - Data quality
        - Complexity
        - Risk factors
        - Business criticality
        """
        base_threshold = 0.7
        
        # Adjust based on risk factors
        risk_adjustment = len(analysis.get("risk_factors", [])) * 0.05
        
        # Adjust based on data quality
        quality_adjustment = (1 - analysis.get("data_quality", 0.5)) * 0.1
        
        # Calculate final threshold
        required = base_threshold + risk_adjustment + quality_adjustment
        
        # Cap at reasonable maximum
        return min(0.95, required)
    
    def _has_sensitive_data_patterns(self, state: UnifiedDiscoveryFlowState) -> bool:
        """Check for sensitive data patterns"""
        if not hasattr(state, 'raw_data') or not state.raw_data:
            return False
            
        sensitive_patterns = ['ssn', 'social', 'tax', 'ein', 'credit', 'account']
        
        if state.raw_data:
            field_names = list(state.raw_data[0].keys())
            for field in field_names:
                if any(pattern in field.lower() for pattern in sensitive_patterns):
                    return True
                    
        return False
    
    def _identify_critical_fields(self, state: UnifiedDiscoveryFlowState) -> List[str]:
        """
        Dynamically identify critical fields based on data analysis.
        This replaces the hardcoded critical fields list.
        """
        if not hasattr(state, 'raw_data') or not state.raw_data:
            return []
            
        critical_fields = []
        field_names = list(state.raw_data[0].keys()) if state.raw_data else []
        
        for field in field_names:
            field_lower = field.lower()
            
            # Identity fields are always critical
            if any(id_pattern in field_lower for id_pattern in ['id', 'identifier', 'key']):
                critical_fields.append(field)
                
            # Name fields are critical
            elif any(name_pattern in field_lower for name_pattern in ['name', 'hostname']):
                critical_fields.append(field)
                
            # Network identifiers
            elif any(net_pattern in field_lower for net_pattern in ['ip', 'mac', 'address']):
                critical_fields.append(field)
                
            # Business context fields
            elif any(biz_pattern in field_lower for biz_pattern in ['owner', 'department', 'application']):
                critical_fields.append(field)
                
        return critical_fields
    
    def _get_next_phase(self, current_phase: str) -> str:
        """Get the next phase in the flow"""
        phase_order = [
            "data_import",
            "field_mapping", 
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_assessment"
        ]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
            
        return "complete"


class FieldMappingDecisionAgent(BaseDecisionAgent):
    """Specialized agent for field mapping decisions"""
    
    def __init__(self):
        super().__init__(
            role="Data Schema Expert",
            goal="Analyze source data schemas and determine optimal field mappings with appropriate confidence levels",
            backstory="""You are a data architecture expert specializing in:
            - Schema analysis and transformation
            - Data type compatibility
            - Business domain mapping
            - Migration best practices
            
            You determine which fields are critical, assess mapping confidence,
            and decide when human review is necessary."""
        )
        
    async def analyze_phase_transition(
        self,
        current_phase: str,
        results: Any,
        state: UnifiedDiscoveryFlowState
    ) -> AgentDecision:
        """Specialized analysis for field mapping phase"""
        
        # Analyze field mappings
        mapping_analysis = await self.analyze_field_mappings(state)
        
        # Determine critical fields dynamically
        critical_fields = self.identify_critical_fields_for_migration(state)
        
        # Calculate appropriate threshold
        threshold = self.calculate_approval_threshold(mapping_analysis, critical_fields)
        
        # Make decision
        if mapping_analysis["confidence"] >= threshold:
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="data_cleansing",
                confidence=mapping_analysis["confidence"],
                reasoning=f"Field mappings meet confidence threshold ({mapping_analysis['confidence']:.1%} >= {threshold:.1%})",
                metadata={
                    "threshold": threshold,
                    "critical_fields": critical_fields,
                    "mapping_analysis": mapping_analysis
                }
            )
        else:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=0.9,
                reasoning=f"Field mapping confidence ({mapping_analysis['confidence']:.1%}) "
                         f"below dynamic threshold ({threshold:.1%}). Human review required.",
                metadata={
                    "threshold": threshold,
                    "critical_fields": critical_fields,
                    "mapping_analysis": mapping_analysis,
                    "user_action": "review_and_approve_mappings"
                }
            )
    
    async def analyze_field_mappings(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Comprehensive field mapping analysis"""
        if not hasattr(state, 'field_mappings'):
            return {"confidence": 0, "analysis": "No field mappings found"}
            
        total_fields = len(state.field_mappings)
        high_confidence_mappings = 0
        ambiguous_mappings = []
        
        for source, target in state.field_mappings.items():
            confidence = self._assess_mapping_confidence(source, target)
            if confidence > 0.8:
                high_confidence_mappings += 1
            elif confidence < 0.5:
                ambiguous_mappings.append(source)
                
        overall_confidence = high_confidence_mappings / total_fields if total_fields > 0 else 0
        
        return {
            "confidence": overall_confidence,
            "total_fields": total_fields,
            "high_confidence_count": high_confidence_mappings,
            "ambiguous_mappings": ambiguous_mappings
        }
    
    def identify_critical_fields_for_migration(self, state: UnifiedDiscoveryFlowState) -> List[str]:
        """
        Dynamically identify critical fields based on migration context.
        This replaces the hardcoded list with intelligent analysis.
        """
        critical = []
        
        if not hasattr(state, 'raw_data') or not state.raw_data:
            return critical
            
        # Analyze data to determine critical fields
        field_stats = self._analyze_field_statistics(state.raw_data)
        
        for field, stats in field_stats.items():
            # High cardinality unique fields are likely identifiers
            if stats["uniqueness"] > 0.95:
                critical.append(field)
                
            # Fields with consistent non-null values are likely important
            elif stats["completeness"] > 0.98:
                if self._is_business_critical_pattern(field):
                    critical.append(field)
                    
        return critical
    
    def calculate_approval_threshold(
        self,
        mapping_analysis: Dict[str, Any],
        critical_fields: List[str]
    ) -> float:
        """
        Calculate dynamic approval threshold based on:
        - Data characteristics
        - Critical field coverage
        - Overall mapping quality
        
        This replaces the hardcoded 90% threshold.
        """
        base_threshold = 0.75
        
        # Adjust for critical field coverage
        if critical_fields:
            critical_mapped = sum(1 for f in critical_fields if f in mapping_analysis.get("mapped_fields", []))
            critical_coverage = critical_mapped / len(critical_fields)
            
            if critical_coverage < 1.0:
                # Increase threshold if critical fields are missing
                base_threshold += (1.0 - critical_coverage) * 0.15
                
        # Adjust for ambiguous mappings
        ambiguous_count = len(mapping_analysis.get("ambiguous_mappings", []))
        if ambiguous_count > 0:
            base_threshold += min(0.1, ambiguous_count * 0.02)
            
        # Cap at reasonable maximum
        return min(0.95, base_threshold)
    
    def _assess_mapping_confidence(self, source: str, target: str) -> float:
        """Assess confidence of individual field mapping"""
        confidence = 0.5  # Base confidence
        
        # Exact match
        if source.lower() == target.lower():
            confidence = 1.0
            
        # Common variations
        elif self._are_common_variations(source, target):
            confidence = 0.9
            
        # Semantic similarity
        elif self._check_semantic_similarity(source, target):
            confidence = 0.7
            
        return confidence
    
    def _analyze_field_statistics(self, raw_data: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Analyze statistical properties of fields"""
        stats = {}
        
        for field in raw_data[0].keys():
            values = [r.get(field) for r in raw_data]
            non_null = [v for v in values if v is not None and v != ""]
            unique_values = len(set(non_null))
            
            stats[field] = {
                "completeness": len(non_null) / len(values) if values else 0,
                "uniqueness": unique_values / len(non_null) if non_null else 0
            }
            
        return stats
    
    def _is_business_critical_pattern(self, field: str) -> bool:
        """Check if field name matches business-critical patterns"""
        critical_patterns = [
            'owner', 'department', 'application', 'environment',
            'criticality', 'priority', 'cost', 'location'
        ]
        field_lower = field.lower()
        return any(pattern in field_lower for pattern in critical_patterns)
    
    def _are_common_variations(self, source: str, target: str) -> bool:
        """Check if fields are common variations of each other"""
        variations = [
            ('hostname', 'host_name', 'host'),
            ('ipaddress', 'ip_address', 'ip'),
            ('macaddress', 'mac_address', 'mac'),
            ('environment', 'env', 'environment_name')
        ]
        
        source_lower = source.lower().replace('_', '').replace('-', '')
        target_lower = target.lower().replace('_', '').replace('-', '')
        
        for group in variations:
            normalized_group = [v.replace('_', '').replace('-', '') for v in group]
            if source_lower in normalized_group and target_lower in normalized_group:
                return True
                
        return False
    
    def _check_semantic_similarity(self, source: str, target: str) -> bool:
        """Check semantic similarity between field names"""
        # This is a simplified version - in production, could use embeddings
        source_tokens = set(source.lower().split('_'))
        target_tokens = set(target.lower().split('_'))
        
        common_tokens = source_tokens.intersection(target_tokens)
        if len(common_tokens) > 0:
            similarity = len(common_tokens) / max(len(source_tokens), len(target_tokens))
            return similarity > 0.5
            
        return False