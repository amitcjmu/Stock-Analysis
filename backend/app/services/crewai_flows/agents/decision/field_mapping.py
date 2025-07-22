"""
Field Mapping Decision Agent

Specialized agent for making intelligent decisions about field mapping
validation and approval based on data analysis and business context.
"""

import logging
from typing import Any, Dict, List

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .base import AgentDecision, BaseDecisionAgent, PhaseAction
from .utils import DecisionUtils

logger = logging.getLogger(__name__)


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
        field_mappings = DecisionUtils.get_state_attribute(state, 'field_mappings', {})
        
        if not field_mappings:
            return {"confidence": 0, "analysis": "No field mappings found"}
            
        total_fields = len(field_mappings)
        high_confidence_mappings = 0
        ambiguous_mappings = []
        
        for source, target in field_mappings.items():
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
            "ambiguous_mappings": ambiguous_mappings,
            "mapped_fields": list(field_mappings.keys())  # Add this for critical field checking
        }
    
    def identify_critical_fields_for_migration(self, state: UnifiedDiscoveryFlowState) -> List[str]:
        """
        Dynamically identify critical fields based on migration context.
        This replaces the hardcoded list with intelligent analysis.
        """
        critical = []
        
        raw_data = DecisionUtils.get_state_attribute(state, 'raw_data', [])
        
        if not raw_data:
            return critical
            
        # Analyze data to determine critical fields
        field_stats = self._analyze_field_statistics(raw_data)
        
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
        
        if not raw_data or not isinstance(raw_data[0], dict):
            return stats
        
        for field in raw_data[0].keys():
            values = [r.get(field) for r in raw_data]
            non_null = [v for v in values if v is not None and v != ""]
            unique_values = len(set(str(v) for v in non_null))
            
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