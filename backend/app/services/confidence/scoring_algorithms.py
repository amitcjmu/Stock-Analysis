"""
Confidence Scoring Algorithms - Advanced algorithms for calculating agent confidence
"""

import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ScoringAlgorithms:
    """
    Advanced scoring algorithms for agent confidence calculation
    """
    
    @staticmethod
    def pattern_matching_confidence(matches: List[Dict[str, Any]], total_items: int) -> float:
        """Calculate confidence based on pattern matching success rate"""
        if total_items == 0:
            return 0.0
        
        # Base confidence from match rate
        match_rate = len(matches) / total_items
        base_confidence = match_rate * 80  # Max 80% from match rate
        
        # Quality bonus based on match strength
        if matches:
            avg_strength = statistics.mean([match.get('strength', 0.5) for match in matches])
            quality_bonus = avg_strength * 20  # Max 20% bonus
        else:
            quality_bonus = 0
        
        return min(100.0, base_confidence + quality_bonus)
    
    @staticmethod
    def data_completeness_confidence(data: List[Dict[str, Any]], required_fields: List[str]) -> float:
        """Calculate confidence based on data completeness"""
        if not data or not required_fields:
            return 0.0
        
        completeness_scores = []
        
        for record in data:
            present_fields = sum(1 for field in required_fields if record.get(field) is not None)
            completeness = present_fields / len(required_fields)
            completeness_scores.append(completeness)
        
        avg_completeness = statistics.mean(completeness_scores)
        
        # Apply sigmoid curve for better distribution
        confidence = ScoringAlgorithms._sigmoid_transform(avg_completeness, midpoint=0.7, steepness=10)
        return confidence * 100
    
    @staticmethod
    def validation_success_confidence(validation_results: Dict[str, Any]) -> float:
        """Calculate confidence based on validation success metrics"""
        total_checks = validation_results.get('total_checks', 0)
        passed_checks = validation_results.get('passed_checks', 0)
        warnings = validation_results.get('warnings', 0)
        errors = validation_results.get('errors', 0)
        
        if total_checks == 0:
            return 50.0  # Neutral confidence when no validation
        
        # Base success rate
        success_rate = passed_checks / total_checks
        base_confidence = success_rate * 90  # Max 90% from success rate
        
        # Penalty for warnings and errors
        warning_penalty = (warnings / total_checks) * 15  # Max 15% penalty
        error_penalty = (errors / total_checks) * 25     # Max 25% penalty
        
        final_confidence = base_confidence - warning_penalty - error_penalty
        return max(0.0, min(100.0, final_confidence))
    
    @staticmethod
    def field_mapping_confidence(mappings: Dict[str, Any], source_fields: List[str]) -> float:
        """Calculate confidence for field mapping operations"""
        if not source_fields:
            return 0.0
        
        mapped_fields = len(mappings.get('mapped_fields', {}))
        unmapped_fields = len(mappings.get('unmapped_fields', []))
        total_fields = mapped_fields + unmapped_fields
        
        if total_fields == 0:
            return 0.0
        
        # Base mapping rate
        mapping_rate = mapped_fields / total_fields
        base_confidence = mapping_rate * 70  # Max 70% from mapping rate
        
        # Quality bonus from mapping confidence scores
        mapping_confidences = []
        for field_mapping in mappings.get('mapped_fields', {}).values():
            if isinstance(field_mapping, dict):
                mapping_confidences.append(field_mapping.get('confidence', 0.5))
        
        if mapping_confidences:
            avg_mapping_confidence = statistics.mean(mapping_confidences)
            quality_bonus = avg_mapping_confidence * 30  # Max 30% bonus
        else:
            quality_bonus = 0
        
        return min(100.0, base_confidence + quality_bonus)
    
    @staticmethod
    def classification_confidence(classifications: List[Dict[str, Any]]) -> float:
        """Calculate confidence for asset classification operations"""
        if not classifications:
            return 0.0
        
        # Collect classification confidence scores
        confidence_scores = []
        for classification in classifications:
            confidence_scores.append(classification.get('confidence', 0.5))
        
        # Calculate statistics
        avg_confidence = statistics.mean(confidence_scores)
        min_confidence = min(confidence_scores)
        std_dev = statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
        
        # Base confidence from average
        base_confidence = avg_confidence * 80
        
        # Penalty for low minimum confidence (weakest link)
        min_penalty = (0.8 - min_confidence) * 15 if min_confidence < 0.8 else 0
        
        # Penalty for high variance (inconsistent classifications)
        variance_penalty = std_dev * 10
        
        final_confidence = base_confidence - min_penalty - variance_penalty
        return max(0.0, min(100.0, final_confidence))
    
    @staticmethod
    def dependency_analysis_confidence(dependencies: List[Dict[str, Any]], 
                                     total_assets: int) -> float:
        """Calculate confidence for dependency analysis"""
        if total_assets == 0:
            return 0.0
        
        # Coverage confidence
        assets_with_deps = len(set(dep.get('source_asset') for dep in dependencies))
        coverage_rate = assets_with_deps / total_assets
        coverage_confidence = coverage_rate * 60  # Max 60% from coverage
        
        # Quality confidence from dependency confidence scores
        dep_confidences = [dep.get('confidence', 0.5) for dep in dependencies]
        if dep_confidences:
            quality_confidence = statistics.mean(dep_confidences) * 40  # Max 40% from quality
        else:
            quality_confidence = 0
        
        return min(100.0, coverage_confidence + quality_confidence)
    
    @staticmethod
    def risk_assessment_confidence(risk_assessments: List[Dict[str, Any]]) -> float:
        """Calculate confidence for risk assessment operations"""
        if not risk_assessments:
            return 0.0
        
        # Factor completeness
        risk_factors = []
        for assessment in risk_assessments:
            factors = assessment.get('risk_factors', [])
            risk_factors.append(len(factors))
        
        avg_factors = statistics.mean(risk_factors)
        factor_confidence = min(avg_factors / 3, 1.0) * 50  # Max 50% from factor completeness
        
        # Assessment confidence scores
        assessment_confidences = [
            assessment.get('confidence', 0.5) for assessment in risk_assessments
        ]
        
        quality_confidence = statistics.mean(assessment_confidences) * 50  # Max 50% from quality
        
        return min(100.0, factor_confidence + quality_confidence)
    
    @staticmethod
    def contextual_confidence_adjustment(base_confidence: float, 
                                       context_factors: Dict[str, Any]) -> float:
        """Apply contextual adjustments to base confidence score"""
        adjusted_confidence = base_confidence
        
        # Data volume factor
        data_volume = context_factors.get('data_volume', 'medium')
        if data_volume == 'large':
            adjusted_confidence += 5  # Bonus for large datasets
        elif data_volume == 'small':
            adjusted_confidence -= 10  # Penalty for small datasets
        
        # Data quality factor
        data_quality = context_factors.get('data_quality', 'medium')
        quality_adjustments = {
            'high': 10,
            'medium': 0,
            'low': -15,
            'poor': -25
        }
        adjusted_confidence += quality_adjustments.get(data_quality, 0)
        
        # Complexity factor
        complexity = context_factors.get('complexity', 'medium')
        complexity_adjustments = {
            'low': 5,
            'medium': 0,
            'high': -10,
            'very_high': -20
        }
        adjusted_confidence += complexity_adjustments.get(complexity, 0)
        
        # Experience factor (how many similar analyses have been done)
        experience_level = context_factors.get('experience_level', 0)
        if experience_level > 10:
            adjusted_confidence += 8
        elif experience_level > 5:
            adjusted_confidence += 4
        elif experience_level < 2:
            adjusted_confidence -= 5
        
        return max(0.0, min(100.0, adjusted_confidence))
    
    @staticmethod
    def temporal_confidence_decay(initial_confidence: float, 
                                hours_elapsed: float, 
                                decay_rate: float = 0.01) -> float:
        """Apply temporal decay to confidence scores"""
        # Exponential decay: confidence * e^(-decay_rate * time)
        decayed_confidence = initial_confidence * math.exp(-decay_rate * hours_elapsed)
        return max(0.0, decayed_confidence)
    
    @staticmethod
    def multi_agent_consensus_confidence(agent_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on consensus between multiple agents"""
        if len(agent_results) < 2:
            return agent_results[0].get('confidence', 50.0) if agent_results else 50.0
        
        confidences = [result.get('confidence', 50.0) for result in agent_results]
        
        # Base confidence from average
        avg_confidence = statistics.mean(confidences)
        
        # Consensus bonus (lower standard deviation = higher consensus)
        std_dev = statistics.stdev(confidences)
        max_std_dev = 30.0  # Maximum expected standard deviation
        consensus_factor = max(0, (max_std_dev - std_dev) / max_std_dev)
        consensus_bonus = consensus_factor * 15  # Max 15% bonus for consensus
        
        # Agreement threshold bonus
        agreement_threshold = 10.0  # Within 10 points is considered agreement
        agreements = 0
        total_pairs = 0
        
        for i in range(len(confidences)):
            for j in range(i + 1, len(confidences)):
                total_pairs += 1
                if abs(confidences[i] - confidences[j]) <= agreement_threshold:
                    agreements += 1
        
        agreement_rate = agreements / total_pairs if total_pairs > 0 else 0
        agreement_bonus = agreement_rate * 10  # Max 10% bonus for agreement
        
        final_confidence = avg_confidence + consensus_bonus + agreement_bonus
        return min(100.0, final_confidence)
    
    @staticmethod
    def _sigmoid_transform(x: float, midpoint: float = 0.5, steepness: float = 10) -> float:
        """Apply sigmoid transformation for smooth confidence curves"""
        return 1 / (1 + math.exp(-steepness * (x - midpoint)))
    
    @staticmethod
    def _normalize_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Normalize score to specified range"""
        return max(min_val, min(max_val, score)) 