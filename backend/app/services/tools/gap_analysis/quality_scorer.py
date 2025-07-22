"""
Quality Scorer Tool - Scores data quality for critical attributes
"""

import logging
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import VALIDATION_RULES

logger = logging.getLogger(__name__)


class QualityScorerTool(AsyncBaseDiscoveryTool):
    """Scores data quality for critical attributes"""
    
    name: str = "quality_scorer"
    description: str = "Calculate quality scores for critical attribute data"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="quality_scorer",
            description="Calculate quality scores for critical attribute data",
            tool_class=cls,
            categories=["gap_analysis", "data_quality"],
            required_params=["data", "attribute_mapping"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, data: List[Dict[str, Any]], attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Calculate quality scores for mapped attributes"""
        try:
            self.log_with_context('info', "Calculating quality scores")
            
            quality_results = {
                "overall_quality_score": 0.0,
                "attribute_scores": {},
                "quality_dimensions": {
                    "accuracy": 0.0,
                    "completeness": 0.0,
                    "consistency": 0.0,
                    "timeliness": 0.0,
                    "validity": 0.0
                },
                "quality_issues": []
            }
            
            attribute_scores = []
            
            for attribute, field_name in attribute_mapping.items():
                attr_quality = self._assess_attribute_quality(data, field_name, attribute)
                quality_results["attribute_scores"][attribute] = attr_quality
                attribute_scores.append(attr_quality["overall_score"])
                
                # Track quality issues
                if attr_quality["overall_score"] < 60:
                    quality_results["quality_issues"].append({
                        "attribute": attribute,
                        "score": attr_quality["overall_score"],
                        "main_issues": attr_quality["issues"]
                    })
            
            # Calculate overall score
            if attribute_scores:
                quality_results["overall_quality_score"] = sum(attribute_scores) / len(attribute_scores)
            
            # Update quality dimensions
            quality_results["quality_dimensions"] = self._calculate_quality_dimensions(
                quality_results["attribute_scores"]
            )
            
            self.log_with_context(
                'info', 
                f"Quality scoring completed. Overall score: {quality_results['overall_quality_score']:.1f}"
            )
            
            return quality_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in quality scoring: {e}")
            return {"error": str(e)}
    
    def _assess_attribute_quality(self, data: List[Dict[str, Any]], field_name: str, attribute: str) -> Dict[str, Any]:
        """Assess quality for a single attribute"""
        quality_assessment = {
            "attribute": attribute,
            "field_name": field_name,
            "overall_score": 0.0,
            "issues": [],
            "metrics": {
                "completeness": 0.0,
                "validity": 0.0,
                "consistency": 0.0,
                "accuracy": 0.0
            }
        }
        
        if not data:
            return quality_assessment
        
        # Collect values
        values = []
        null_count = 0
        invalid_count = 0
        
        for record in data:
            value = record.get(field_name)
            if value is None:
                null_count += 1
            elif isinstance(value, str) and value.lower() in ["null", "n/a", "unknown", ""]:
                invalid_count += 1
            else:
                values.append(value)
        
        total_records = len(data)
        
        # Calculate completeness
        quality_assessment["metrics"]["completeness"] = (len(values) / total_records * 100) if total_records > 0 else 0
        
        # Calculate validity (basic checks)
        if values:
            quality_assessment["metrics"]["validity"] = self._calculate_validity(values, attribute)
        
        # Calculate consistency
        if values:
            quality_assessment["metrics"]["consistency"] = self._calculate_consistency(values)
        
        # Estimate accuracy (simplified)
        quality_assessment["metrics"]["accuracy"] = 80.0 if len(values) > total_records * 0.7 else 50.0
        
        # Calculate overall score
        metrics = quality_assessment["metrics"]
        quality_assessment["overall_score"] = (
            metrics["completeness"] * 0.4 +
            metrics["validity"] * 0.3 +
            metrics["consistency"] * 0.2 +
            metrics["accuracy"] * 0.1
        )
        
        # Identify issues
        if metrics["completeness"] < 50:
            quality_assessment["issues"].append("Low completeness")
        if metrics["validity"] < 70:
            quality_assessment["issues"].append("Validity concerns")
        if metrics["consistency"] < 80:
            quality_assessment["issues"].append("Inconsistent data")
        
        return quality_assessment
    
    def _calculate_validity(self, values: List[Any], attribute: str) -> float:
        """Calculate validity score for values"""
        valid_count = 0
        
        # Use validation rules from constants or default
        validation_func = VALIDATION_RULES.get(attribute, lambda v: v is not None and v != "")
        
        for value in values:
            try:
                if validation_func(value):
                    valid_count += 1
            except Exception:
                pass
        
        return (valid_count / len(values) * 100) if values else 0
    
    def _calculate_consistency(self, values: List[Any]) -> float:
        """Calculate consistency score for values"""
        if not values:
            return 0.0
        
        # Check data type consistency
        types = set(type(v) for v in values)
        if len(types) > 1:
            return 50.0  # Mixed types indicate inconsistency
        
        # For strings, check format consistency
        if all(isinstance(v, str) for v in values):
            # Check case consistency
            cases = set()
            for v in values:
                if v.isupper():
                    cases.add("upper")
                elif v.islower():
                    cases.add("lower")
                else:
                    cases.add("mixed")
            
            if len(cases) == 1:
                return 100.0
            else:
                return 70.0
        
        return 90.0  # Default for consistent types
    
    def _calculate_quality_dimensions(self, attribute_scores: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate overall quality dimensions from attribute scores"""
        dimensions = {
            "accuracy": [],
            "completeness": [],
            "consistency": [],
            "timeliness": [],
            "validity": []
        }
        
        for attr_data in attribute_scores.values():
            metrics = attr_data.get("metrics", {})
            dimensions["completeness"].append(metrics.get("completeness", 0))
            dimensions["validity"].append(metrics.get("validity", 0))
            dimensions["consistency"].append(metrics.get("consistency", 0))
            dimensions["accuracy"].append(metrics.get("accuracy", 0))
        
        # Calculate averages
        result = {}
        for dim, values in dimensions.items():
            if values:
                result[dim] = sum(values) / len(values)
            else:
                result[dim] = 0.0
        
        # Timeliness is estimated based on other factors
        result["timeliness"] = 85.0 if result["completeness"] > 70 else 60.0
        
        return result