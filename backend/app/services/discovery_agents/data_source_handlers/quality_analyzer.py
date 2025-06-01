"""
Quality Analyzer Handler
Analyzes data quality, completeness, and classification.
"""

import logging
from typing import Dict, List, Any, Optional
import math
import re

from app.services.models.agent_communication import ConfidenceLevel, DataClassification

logger = logging.getLogger(__name__)

class QualityAnalyzer:
    """Analyzes data quality and provides classification recommendations."""
    
    def __init__(self):
        self.analyzer_id = "quality_analyzer"
        
        # Quality assessment patterns
        self.critical_fields = ["hostname", "asset_name", "ip_address", "environment"]
        self.important_fields = ["department", "owner", "operating_system", "asset_type"]
        
        # Data quality patterns
        self.empty_value_patterns = ["", "n/a", "null", "none", "unknown", "tbd", "?"]
        self.placeholder_patterns = [
            r"^placeholder.*", r"^test.*", r"^sample.*", r"^dummy.*",
            r"^xxx+", r"^-+$", r"^\.+$"
        ]
    
    async def classify_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify data quality and provide detailed assessment."""
        
        if not data:
            return {
                "overall_classification": DataClassification.UNUSABLE,
                "confidence": ConfidenceLevel.HIGH,
                "reasoning": "No data provided for analysis"
            }
        
        total_rows = len(data)
        quality_metrics = {
            "completeness": await self._assess_completeness(data),
            "consistency": await self._assess_consistency(data),
            "validity": await self._assess_validity(data),
            "uniqueness": await self._assess_uniqueness(data)
        }
        
        # Calculate overall quality score
        overall_score = (
            quality_metrics["completeness"]["score"] * 0.3 +
            quality_metrics["consistency"]["score"] * 0.25 +
            quality_metrics["validity"]["score"] * 0.25 +
            quality_metrics["uniqueness"]["score"] * 0.2
        )
        
        # Determine classification based on score
        classification = self._score_to_classification(overall_score)
        confidence = self._calculate_classification_confidence(quality_metrics, total_rows)
        
        return {
            "overall_classification": classification,
            "confidence": confidence,
            "overall_score": overall_score,
            "quality_metrics": quality_metrics,
            "total_rows_analyzed": total_rows,
            "reasoning": self._generate_quality_reasoning(quality_metrics, overall_score)
        }
    
    async def identify_quality_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify specific quality indicators and issues."""
        
        if not data:
            return {"indicators": [], "issues": ["No data to analyze"]}
        
        indicators = []
        issues = []
        
        # Sample first few rows for analysis
        sample_size = min(10, len(data))
        sample_data = data[:sample_size]
        
        # Check for critical field presence
        all_columns = set()
        for row in sample_data:
            all_columns.update(row.keys())
        
        # Analyze critical field coverage
        critical_found = []
        for field in self.critical_fields:
            if any(field.lower() in col.lower() for col in all_columns):
                critical_found.append(field)
        
        if len(critical_found) >= 3:
            indicators.append(f"Good critical field coverage: {', '.join(critical_found)}")
        else:
            issues.append(f"Missing critical fields. Found only: {', '.join(critical_found)}")
        
        # Check for data completeness patterns
        empty_ratios = {}
        for column in all_columns:
            empty_count = 0
            total_count = 0
            
            for row in sample_data:
                if column in row:
                    total_count += 1
                    if self._is_empty_value(row[column]):
                        empty_count += 1
            
            if total_count > 0:
                empty_ratio = empty_count / total_count
                empty_ratios[column] = empty_ratio
                
                if empty_ratio > 0.8:
                    issues.append(f"Column '{column}' is mostly empty ({empty_ratio:.1%})")
                elif empty_ratio < 0.1:
                    indicators.append(f"Column '{column}' has good completeness")
        
        # Check for consistency patterns
        consistency_issues = await self._check_consistency_patterns(sample_data)
        issues.extend(consistency_issues)
        
        # Check for validity patterns
        validity_indicators = await self._check_validity_patterns(sample_data)
        indicators.extend(validity_indicators)
        
        return {
            "indicators": indicators,
            "issues": issues,
            "empty_ratios": empty_ratios,
            "sample_size": sample_size
        }
    
    async def _assess_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data completeness across all fields."""
        
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        column_completeness = {}
        total_completeness = 0
        
        for column in all_columns:
            non_empty_count = 0
            total_count = 0
            
            for row in data:
                if column in row:
                    total_count += 1
                    if not self._is_empty_value(row[column]):
                        non_empty_count += 1
            
            completeness = non_empty_count / total_count if total_count > 0 else 0
            column_completeness[column] = completeness
            total_completeness += completeness
        
        average_completeness = total_completeness / len(all_columns) if all_columns else 0
        
        return {
            "score": average_completeness,
            "column_completeness": column_completeness,
            "assessment": "High completeness" if average_completeness > 0.8 else 
                         "Medium completeness" if average_completeness > 0.6 else "Low completeness"
        }
    
    async def _assess_consistency(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data consistency patterns."""
        
        consistency_score = 1.0
        consistency_issues = []
        
        # Check for format consistency within columns
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        for column in all_columns:
            values = []
            for row in data:
                if column in row and not self._is_empty_value(row[column]):
                    values.append(str(row[column]))
            
            if len(values) > 1:
                # Check format consistency
                format_consistency = self._check_format_consistency(values)
                if format_consistency < 0.8:
                    consistency_score *= format_consistency
                    consistency_issues.append(f"Format inconsistency in column '{column}'")
        
        return {
            "score": consistency_score,
            "issues": consistency_issues,
            "assessment": "High consistency" if consistency_score > 0.8 else 
                         "Medium consistency" if consistency_score > 0.6 else "Low consistency"
        }
    
    async def _assess_validity(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data validity and format correctness."""
        
        validity_score = 1.0
        validity_issues = []
        
        # Sample data for validity checks
        sample_size = min(20, len(data))
        sample_data = data[:sample_size]
        
        for row in sample_data:
            for column, value in row.items():
                if not self._is_empty_value(value):
                    validity_check = self._check_value_validity(column, value)
                    if not validity_check["valid"]:
                        validity_score *= 0.95  # Small penalty for each invalid value
                        validity_issues.append(validity_check["issue"])
        
        return {
            "score": validity_score,
            "issues": validity_issues,
            "assessment": "High validity" if validity_score > 0.9 else 
                         "Medium validity" if validity_score > 0.7 else "Low validity"
        }
    
    async def _assess_uniqueness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data uniqueness and identify duplicates."""
        
        if len(data) <= 1:
            return {
                "score": 1.0,
                "duplicate_count": 0,
                "assessment": "High uniqueness"
            }
        
        # Create simple row signatures for duplicate detection
        row_signatures = []
        for row in data:
            # Create signature from first few values
            signature_values = []
            for key in sorted(row.keys())[:5]:  # Use first 5 columns for signature
                signature_values.append(str(row.get(key, "")))
            row_signatures.append("|".join(signature_values))
        
        unique_signatures = set(row_signatures)
        duplicate_count = len(row_signatures) - len(unique_signatures)
        uniqueness_score = len(unique_signatures) / len(row_signatures)
        
        return {
            "score": uniqueness_score,
            "duplicate_count": duplicate_count,
            "unique_rows": len(unique_signatures),
            "total_rows": len(row_signatures),
            "assessment": "High uniqueness" if uniqueness_score > 0.95 else 
                         "Medium uniqueness" if uniqueness_score > 0.85 else "Low uniqueness"
        }
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value should be considered empty."""
        if value is None:
            return True
        
        str_value = str(value).strip().lower()
        return str_value in self.empty_value_patterns
    
    def _check_format_consistency(self, values: List[str]) -> float:
        """Check format consistency within a list of values."""
        if len(values) <= 1:
            return 1.0
        
        # Group values by apparent format
        format_groups = {}
        for value in values:
            format_key = self._get_format_key(value)
            if format_key not in format_groups:
                format_groups[format_key] = 0
            format_groups[format_key] += 1
        
        # Calculate consistency as ratio of most common format
        max_count = max(format_groups.values())
        return max_count / len(values)
    
    def _get_format_key(self, value: str) -> str:
        """Get a format key for consistency checking."""
        # Simple format patterns
        if re.match(r'^\d+$', value):
            return "numeric"
        elif re.match(r'^\d+\.\d+$', value):
            return "decimal"
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
            return "ip_address"
        elif '@' in value:
            return "email"
        elif len(value) > 50:
            return "long_text"
        else:
            return "short_text"
    
    def _check_value_validity(self, column: str, value: Any) -> Dict[str, Any]:
        """Check if a value is valid for its apparent column type."""
        str_value = str(value).strip()
        column_lower = column.lower()
        
        # Check for placeholder patterns
        for pattern in self.placeholder_patterns:
            if re.match(pattern, str_value.lower()):
                return {
                    "valid": False,
                    "issue": f"Placeholder value in column '{column}': {str_value}"
                }
        
        # Basic validity checks based on column name
        if "ip" in column_lower and "address" in column_lower:
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', str_value):
                return {
                    "valid": False,
                    "issue": f"Invalid IP address format in '{column}': {str_value}"
                }
        
        if "email" in column_lower:
            if "@" not in str_value or "." not in str_value:
                return {
                    "valid": False,
                    "issue": f"Invalid email format in '{column}': {str_value}"
                }
        
        return {"valid": True, "issue": None}
    
    async def _check_consistency_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Check for consistency patterns in the data."""
        issues = []
        
        # Check environment consistency
        environments = set()
        for row in data:
            for key, value in row.items():
                if "environment" in key.lower() and not self._is_empty_value(value):
                    environments.add(str(value).lower())
        
        if len(environments) > 5:
            issues.append(f"Many different environment values ({len(environments)})")
        
        return issues
    
    async def _check_validity_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Check for validity patterns in the data."""
        indicators = []
        
        # Check for structured data
        structured_count = 0
        for row in data:
            if len(row) > 5:  # Has reasonable number of fields
                structured_count += 1
        
        if structured_count > len(data) * 0.8:
            indicators.append("Data appears well-structured with consistent field count")
        
        return indicators
    
    def _score_to_classification(self, score: float) -> DataClassification:
        """Convert quality score to data classification."""
        if score >= 0.8:
            return DataClassification.GOOD_DATA
        elif score >= 0.5:
            return DataClassification.NEEDS_CLARIFICATION
        else:
            return DataClassification.UNUSABLE
    
    def _calculate_classification_confidence(self, metrics: Dict[str, Any], 
                                           sample_size: int) -> ConfidenceLevel:
        """Calculate confidence in the classification."""
        # Higher sample size increases confidence
        size_factor = min(sample_size / 100, 1.0)
        
        # Consistency in metrics increases confidence
        scores = [metrics[key]["score"] for key in metrics]
        score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
        consistency_factor = max(0, 1 - score_variance)
        
        overall_confidence = (size_factor * 0.3) + (consistency_factor * 0.7)
        
        if overall_confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif overall_confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif overall_confidence >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    def _generate_quality_reasoning(self, metrics: Dict[str, Any], 
                                  overall_score: float) -> str:
        """Generate human-readable reasoning for quality assessment."""
        reasons = []
        
        for metric_name, metric_data in metrics.items():
            assessment = metric_data.get("assessment", "")
            if assessment:
                reasons.append(f"{metric_name}: {assessment}")
        
        score_description = (
            "Excellent" if overall_score >= 0.9 else
            "Good" if overall_score >= 0.8 else
            "Fair" if overall_score >= 0.6 else
            "Poor"
        )
        
        return f"{score_description} overall quality. " + "; ".join(reasons) 