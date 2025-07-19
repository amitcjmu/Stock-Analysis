"""
Quality Scoring and Confidence Assessment Services

This module provides services for assessing data quality and confidence levels
for collected data, helping to identify gaps and areas needing improvement.
"""

import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.services.collection_flow.data_transformation import DataType

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Dimensions of data quality assessment"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"


class ConfidenceLevel(str, Enum):
    """Confidence levels for assessments"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


@dataclass
class QualityScore:
    """Data quality score result"""
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceScore:
    """Confidence assessment result"""
    overall_confidence: float
    confidence_level: ConfidenceLevel
    confidence_factors: Dict[str, float]
    risk_factors: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityAssessmentService:
    """
    Service for assessing data quality across multiple dimensions.
    
    This service evaluates:
    - Data completeness
    - Data accuracy
    - Data consistency
    - Data timeliness
    - Data validity
    - Data uniqueness
    """
    
    # Required fields by data type
    REQUIRED_FIELDS = {
        DataType.SERVER: {
            "critical": ["hostname", "ip_address", "operating_system"],
            "important": ["cpu_count", "memory_gb", "status", "environment"],
            "optional": ["serial_number", "model", "manufacturer", "location"]
        },
        DataType.APPLICATION: {
            "critical": ["app_name", "version", "status"],
            "important": ["environment", "owner", "technology"],
            "optional": ["url", "port", "criticality"]
        },
        DataType.DATABASE: {
            "critical": ["db_name", "db_type", "host"],
            "important": ["version", "port", "size_gb", "status"],
            "optional": ["connection_string", "backup_schedule"]
        }
    }
    
    # Field validation rules
    VALIDATION_RULES = {
        "hostname": {
            "pattern": r"^[a-zA-Z0-9\-\.]+$",
            "max_length": 255
        },
        "ip_address": {
            "pattern": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            "validator": "ip_address"
        },
        "port": {
            "type": "integer",
            "min": 1,
            "max": 65535
        },
        "memory_gb": {
            "type": "numeric",
            "min": 0
        },
        "cpu_count": {
            "type": "integer",
            "min": 1
        }
    }
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Quality Assessment Service.
        
        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        
    async def assess_data_quality(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        data_type: DataType,
        collection_metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Assess the quality of collected data.
        
        Args:
            data: Single record or list of records to assess
            data_type: Type of data being assessed
            collection_metadata: Optional metadata about collection
            
        Returns:
            QualityScore with detailed assessment
        """
        try:
            # Convert single record to list for uniform processing
            records = data if isinstance(data, list) else [data]
            
            # Assess each quality dimension
            completeness_score, completeness_issues = await self._assess_completeness(
                records, data_type
            )
            accuracy_score, accuracy_issues = await self._assess_accuracy(
                records, data_type
            )
            consistency_score, consistency_issues = await self._assess_consistency(
                records, data_type
            )
            timeliness_score, timeliness_issues = await self._assess_timeliness(
                records, collection_metadata
            )
            validity_score, validity_issues = await self._assess_validity(
                records, data_type
            )
            uniqueness_score, uniqueness_issues = await self._assess_uniqueness(
                records, data_type
            )
            
            # Calculate overall score
            dimension_scores = {
                QualityDimension.COMPLETENESS: completeness_score,
                QualityDimension.ACCURACY: accuracy_score,
                QualityDimension.CONSISTENCY: consistency_score,
                QualityDimension.TIMELINESS: timeliness_score,
                QualityDimension.VALIDITY: validity_score,
                QualityDimension.UNIQUENESS: uniqueness_score
            }
            
            # Weighted average (completeness and accuracy are more important)
            weights = {
                QualityDimension.COMPLETENESS: 0.25,
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.CONSISTENCY: 0.15,
                QualityDimension.TIMELINESS: 0.15,
                QualityDimension.VALIDITY: 0.10,
                QualityDimension.UNIQUENESS: 0.10
            }
            
            overall_score = sum(
                score * weights[dimension]
                for dimension, score in dimension_scores.items()
            )
            
            # Combine all issues
            all_issues = (
                completeness_issues + accuracy_issues + consistency_issues +
                timeliness_issues + validity_issues + uniqueness_issues
            )
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(
                dimension_scores, all_issues
            )
            
            return QualityScore(
                overall_score=round(overall_score, 2),
                dimension_scores=dimension_scores,
                issues_found=all_issues,
                recommendations=recommendations,
                metadata={
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                    "record_count": len(records),
                    "data_type": data_type.value
                }
            )
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            raise
    
    async def _assess_completeness(
        self,
        records: List[Dict[str, Any]],
        data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data completeness."""
        issues = []
        
        if data_type not in self.REQUIRED_FIELDS:
            return 100.0, issues
            
        required_fields = self.REQUIRED_FIELDS[data_type]
        total_fields = len(required_fields["critical"]) + len(required_fields["important"])
        
        if total_fields == 0:
            return 100.0, issues
        
        completeness_scores = []
        
        for idx, record in enumerate(records):
            missing_critical = []
            missing_important = []
            
            # Check critical fields
            for field in required_fields["critical"]:
                if field not in record or not record[field]:
                    missing_critical.append(field)
                    
            # Check important fields
            for field in required_fields["important"]:
                if field not in record or not record[field]:
                    missing_important.append(field)
            
            # Calculate completeness for this record
            missing_count = len(missing_critical) + len(missing_important)
            record_completeness = ((total_fields - missing_count) / total_fields) * 100
            
            # Weight critical fields more heavily
            if missing_critical:
                record_completeness *= 0.5  # 50% penalty for missing critical fields
                
            completeness_scores.append(record_completeness)
            
            # Log issues
            if missing_critical or missing_important:
                issues.append({
                    "dimension": QualityDimension.COMPLETENESS.value,
                    "severity": "high" if missing_critical else "medium",
                    "record_index": idx,
                    "description": f"Missing fields",
                    "details": {
                        "missing_critical": missing_critical,
                        "missing_important": missing_important
                    }
                })
        
        avg_completeness = statistics.mean(completeness_scores) if completeness_scores else 0
        return round(avg_completeness, 2), issues
    
    async def _assess_accuracy(
        self,
        records: List[Dict[str, Any]],
        data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data accuracy through validation and cross-reference checks."""
        issues = []
        accuracy_scores = []
        
        for idx, record in enumerate(records):
            record_issues = 0
            field_count = len(record)
            
            # Validate IP addresses
            if "ip_address" in record:
                if not self._validate_ip_address(record["ip_address"]):
                    record_issues += 1
                    issues.append({
                        "dimension": QualityDimension.ACCURACY.value,
                        "severity": "medium",
                        "record_index": idx,
                        "description": "Invalid IP address format",
                        "field": "ip_address",
                        "value": record["ip_address"]
                    })
            
            # Validate hostnames
            if "hostname" in record:
                if not self._validate_hostname(record["hostname"]):
                    record_issues += 1
                    issues.append({
                        "dimension": QualityDimension.ACCURACY.value,
                        "severity": "medium",
                        "record_index": idx,
                        "description": "Invalid hostname format",
                        "field": "hostname",
                        "value": record["hostname"]
                    })
            
            # Validate numeric ranges
            if "cpu_count" in record:
                try:
                    cpu = int(record["cpu_count"])
                    if cpu < 1 or cpu > 1024:  # Reasonable bounds
                        record_issues += 1
                        issues.append({
                            "dimension": QualityDimension.ACCURACY.value,
                            "severity": "low",
                            "record_index": idx,
                            "description": "CPU count out of reasonable range",
                            "field": "cpu_count",
                            "value": record["cpu_count"]
                        })
                except (ValueError, TypeError):
                    record_issues += 1
                    
            # Calculate accuracy score for this record
            if field_count > 0:
                accuracy = ((field_count - record_issues) / field_count) * 100
            else:
                accuracy = 100.0
                
            accuracy_scores.append(accuracy)
        
        avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0
        return round(avg_accuracy, 2), issues
    
    async def _assess_consistency(
        self,
        records: List[Dict[str, Any]],
        data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data consistency across records."""
        issues = []
        
        if len(records) < 2:
            return 100.0, issues  # Cannot assess consistency with single record
        
        # Check for consistent field naming
        all_fields = set()
        field_frequency = {}
        
        for record in records:
            for field in record.keys():
                all_fields.add(field)
                field_frequency[field] = field_frequency.get(field, 0) + 1
        
        # Fields that appear in some but not all records
        inconsistent_fields = [
            field for field, count in field_frequency.items()
            if count < len(records) and count > len(records) * 0.1
        ]
        
        if inconsistent_fields:
            issues.append({
                "dimension": QualityDimension.CONSISTENCY.value,
                "severity": "medium",
                "description": "Inconsistent field presence across records",
                "details": {
                    "fields": inconsistent_fields,
                    "total_records": len(records)
                }
            })
        
        # Check for value format consistency
        format_consistency = await self._check_format_consistency(records)
        
        # Calculate consistency score
        total_possible_issues = len(all_fields) + len(format_consistency)
        actual_issues = len(inconsistent_fields) + len(format_consistency)
        
        consistency_score = ((total_possible_issues - actual_issues) / total_possible_issues * 100) if total_possible_issues > 0 else 100.0
        
        issues.extend(format_consistency)
        
        return round(consistency_score, 2), issues
    
    async def _assess_timeliness(
        self,
        records: List[Dict[str, Any]],
        collection_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data timeliness and freshness."""
        issues = []
        
        # Check collection timestamp
        if collection_metadata:
            collection_time = collection_metadata.get("collection_timestamp")
            if collection_time:
                try:
                    collection_dt = datetime.fromisoformat(collection_time)
                    age_hours = (datetime.utcnow() - collection_dt).total_seconds() / 3600
                    
                    if age_hours > 24:
                        issues.append({
                            "dimension": QualityDimension.TIMELINESS.value,
                            "severity": "medium" if age_hours < 168 else "high",  # 7 days
                            "description": f"Data is {age_hours:.1f} hours old",
                            "details": {
                                "collection_timestamp": collection_time,
                                "age_hours": age_hours
                            }
                        })
                except Exception:
                    pass
        
        # Check for date fields in records
        date_fields = ["updated_at", "last_seen", "discovered_at", "last_modified"]
        old_data_count = 0
        
        for idx, record in enumerate(records):
            for field in date_fields:
                if field in record and record[field]:
                    try:
                        dt = datetime.fromisoformat(str(record[field]))
                        age_days = (datetime.utcnow() - dt).days
                        
                        if age_days > 30:
                            old_data_count += 1
                            if age_days > 90:
                                issues.append({
                                    "dimension": QualityDimension.TIMELINESS.value,
                                    "severity": "high",
                                    "record_index": idx,
                                    "description": f"Stale data in {field}",
                                    "details": {
                                        "field": field,
                                        "age_days": age_days,
                                        "value": record[field]
                                    }
                                })
                            break
                    except Exception:
                        pass
        
        # Calculate timeliness score
        if len(records) > 0:
            timeliness_score = ((len(records) - old_data_count) / len(records)) * 100
        else:
            timeliness_score = 100.0
            
        return round(timeliness_score, 2), issues
    
    async def _assess_validity(
        self,
        records: List[Dict[str, Any]],
        data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data validity against defined rules."""
        issues = []
        validity_scores = []
        
        for idx, record in enumerate(records):
            invalid_fields = 0
            total_validated_fields = 0
            
            for field, value in record.items():
                if field in self.VALIDATION_RULES:
                    total_validated_fields += 1
                    rule = self.VALIDATION_RULES[field]
                    
                    # Type validation
                    if "type" in rule:
                        if not self._validate_type(value, rule["type"]):
                            invalid_fields += 1
                            issues.append({
                                "dimension": QualityDimension.VALIDITY.value,
                                "severity": "medium",
                                "record_index": idx,
                                "description": f"Invalid type for {field}",
                                "expected_type": rule["type"],
                                "actual_value": str(value)
                            })
                    
                    # Range validation
                    if "min" in rule or "max" in rule:
                        try:
                            num_value = float(value)
                            if "min" in rule and num_value < rule["min"]:
                                invalid_fields += 1
                                issues.append({
                                    "dimension": QualityDimension.VALIDITY.value,
                                    "severity": "medium",
                                    "record_index": idx,
                                    "description": f"{field} below minimum value",
                                    "min_value": rule["min"],
                                    "actual_value": num_value
                                })
                            if "max" in rule and num_value > rule["max"]:
                                invalid_fields += 1
                                issues.append({
                                    "dimension": QualityDimension.VALIDITY.value,
                                    "severity": "medium",
                                    "record_index": idx,
                                    "description": f"{field} above maximum value",
                                    "max_value": rule["max"],
                                    "actual_value": num_value
                                })
                        except (ValueError, TypeError):
                            pass
            
            # Calculate validity score for this record
            if total_validated_fields > 0:
                validity = ((total_validated_fields - invalid_fields) / total_validated_fields) * 100
            else:
                validity = 100.0
                
            validity_scores.append(validity)
        
        avg_validity = statistics.mean(validity_scores) if validity_scores else 100.0
        return round(avg_validity, 2), issues
    
    async def _assess_uniqueness(
        self,
        records: List[Dict[str, Any]],
        data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data uniqueness and identify duplicates."""
        issues = []
        
        # Define key fields for uniqueness check
        key_fields = {
            DataType.SERVER: ["hostname", "ip_address"],
            DataType.APPLICATION: ["app_name", "environment"],
            DataType.DATABASE: ["db_name", "host", "port"]
        }
        
        if data_type not in key_fields:
            return 100.0, issues
        
        # Check for duplicates
        seen_keys = {}
        duplicate_count = 0
        
        for idx, record in enumerate(records):
            # Create composite key
            key_values = []
            for field in key_fields[data_type]:
                if field in record:
                    key_values.append(str(record.get(field, "")))
                    
            if key_values:
                key = "|".join(key_values)
                
                if key in seen_keys:
                    duplicate_count += 1
                    issues.append({
                        "dimension": QualityDimension.UNIQUENESS.value,
                        "severity": "high",
                        "record_index": idx,
                        "description": "Duplicate record found",
                        "details": {
                            "duplicate_of_index": seen_keys[key],
                            "key_fields": key_fields[data_type],
                            "key_value": key
                        }
                    })
                else:
                    seen_keys[key] = idx
        
        # Calculate uniqueness score
        if len(records) > 0:
            uniqueness_score = ((len(records) - duplicate_count) / len(records)) * 100
        else:
            uniqueness_score = 100.0
            
        return round(uniqueness_score, 2), issues
    
    async def _check_format_consistency(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for format consistency across records."""
        issues = []
        
        # Track format patterns for common fields
        format_patterns = {}
        
        for field in ["hostname", "ip_address", "environment", "status"]:
            patterns = {}
            
            for idx, record in enumerate(records):
                if field in record and record[field]:
                    value = str(record[field])
                    
                    # Detect format pattern
                    if field == "hostname":
                        if "." in value:
                            pattern = "fqdn"
                        else:
                            pattern = "short"
                    elif field == "environment":
                        pattern = "lowercase" if value.islower() else "mixed"
                    else:
                        pattern = "default"
                    
                    if pattern not in patterns:
                        patterns[pattern] = []
                    patterns[pattern].append(idx)
            
            # If multiple patterns found, it's inconsistent
            if len(patterns) > 1:
                format_patterns[field] = patterns
        
        # Create issues for inconsistent formats
        for field, patterns in format_patterns.items():
            issues.append({
                "dimension": QualityDimension.CONSISTENCY.value,
                "severity": "low",
                "description": f"Inconsistent format for {field}",
                "details": {
                    "field": field,
                    "format_patterns": {k: len(v) for k, v in patterns.items()}
                }
            })
        
        return issues
    
    def _validate_ip_address(self, ip: Any) -> bool:
        """Validate IP address format."""
        if not isinstance(ip, str):
            return False
            
        try:
            parts = ip.split(".")
            return (
                len(parts) == 4 and
                all(0 <= int(part) <= 255 for part in parts)
            )
        except (ValueError, AttributeError):
            return False
    
    def _validate_hostname(self, hostname: Any) -> bool:
        """Validate hostname format."""
        if not isinstance(hostname, str):
            return False
            
        import re
        pattern = r"^[a-zA-Z0-9\-\.]+$"
        return bool(re.match(pattern, hostname)) and len(hostname) <= 255
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_validators = {
            "integer": lambda v: isinstance(v, int) or (isinstance(v, str) and v.isdigit()),
            "numeric": lambda v: isinstance(v, (int, float)) or (isinstance(v, str) and self._is_numeric(v)),
            "string": lambda v: isinstance(v, str),
            "boolean": lambda v: isinstance(v, bool) or v in ["true", "false", "True", "False"]
        }
        
        validator = type_validators.get(expected_type)
        return validator(value) if validator else True
    
    def _is_numeric(self, value: str) -> bool:
        """Check if string value is numeric."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _generate_quality_recommendations(
        self,
        dimension_scores: Dict[QualityDimension, float],
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on quality assessment."""
        recommendations = []
        
        # Recommendations based on dimension scores
        for dimension, score in dimension_scores.items():
            if score < 70:
                if dimension == QualityDimension.COMPLETENESS:
                    recommendations.append(
                        "Implement mandatory field validation in collection process"
                    )
                    recommendations.append(
                        "Review and update collection templates to capture all required fields"
                    )
                elif dimension == QualityDimension.ACCURACY:
                    recommendations.append(
                        "Add data validation rules at collection time"
                    )
                    recommendations.append(
                        "Implement automated data verification checks"
                    )
                elif dimension == QualityDimension.CONSISTENCY:
                    recommendations.append(
                        "Standardize data collection formats across all sources"
                    )
                    recommendations.append(
                        "Implement data normalization pipeline"
                    )
                elif dimension == QualityDimension.TIMELINESS:
                    recommendations.append(
                        "Schedule more frequent data collection cycles"
                    )
                    recommendations.append(
                        "Implement real-time or near-real-time collection where possible"
                    )
                elif dimension == QualityDimension.UNIQUENESS:
                    recommendations.append(
                        "Implement deduplication logic in collection process"
                    )
                    recommendations.append(
                        "Define and enforce unique constraints on key fields"
                    )
        
        # Recommendations based on issue patterns
        high_severity_issues = [i for i in issues if i.get("severity") == "high"]
        if len(high_severity_issues) > 5:
            recommendations.append(
                "Critical data quality issues detected - review collection methodology"
            )
        
        return list(set(recommendations))  # Remove duplicates


class ConfidenceAssessmentService:
    """
    Service for assessing confidence levels in collected data.
    
    This service evaluates:
    - Source reliability
    - Collection method confidence
    - Data validation results
    - Historical accuracy
    """
    
    # Source reliability scores
    SOURCE_RELIABILITY = {
        "api": 0.95,
        "automated_script": 0.85,
        "export": 0.75,
        "manual_entry": 0.60,
        "template": 0.50
    }
    
    # Platform confidence multipliers
    PLATFORM_CONFIDENCE = {
        "servicenow": 0.95,
        "vmware_vcenter": 0.90,
        "aws": 0.95,
        "azure": 0.95,
        "excel": 0.60,
        "manual": 0.50
    }
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Confidence Assessment Service.
        
        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        
    async def assess_confidence(
        self,
        collection_metadata: Dict[str, Any],
        quality_score: QualityScore,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> ConfidenceScore:
        """
        Assess confidence level in collected data.
        
        Args:
            collection_metadata: Metadata about collection process
            quality_score: Quality assessment results
            validation_results: Optional validation results
            
        Returns:
            ConfidenceScore with detailed assessment
        """
        try:
            confidence_factors = {}
            
            # Assess source reliability
            source_confidence = self._assess_source_reliability(collection_metadata)
            confidence_factors["source_reliability"] = source_confidence
            
            # Assess collection method confidence
            method_confidence = self._assess_method_confidence(collection_metadata)
            confidence_factors["collection_method"] = method_confidence
            
            # Factor in quality score
            quality_confidence = self._calculate_quality_confidence(quality_score)
            confidence_factors["data_quality"] = quality_confidence
            
            # Assess validation confidence
            if validation_results:
                validation_confidence = self._assess_validation_confidence(validation_results)
                confidence_factors["validation"] = validation_confidence
            
            # Calculate historical confidence if available
            historical_confidence = await self._assess_historical_confidence(
                collection_metadata
            )
            if historical_confidence is not None:
                confidence_factors["historical_accuracy"] = historical_confidence
            
            # Calculate overall confidence (weighted average)
            weights = {
                "source_reliability": 0.30,
                "collection_method": 0.25,
                "data_quality": 0.30,
                "validation": 0.10,
                "historical_accuracy": 0.05
            }
            
            overall_confidence = 0.0
            total_weight = 0.0
            
            for factor, score in confidence_factors.items():
                if factor in weights:
                    overall_confidence += score * weights[factor]
                    total_weight += weights[factor]
            
            if total_weight > 0:
                overall_confidence = overall_confidence / total_weight
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                confidence_factors, collection_metadata, quality_score
            )
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                confidence_factors, risk_factors
            )
            
            return ConfidenceScore(
                overall_confidence=round(overall_confidence, 2),
                confidence_level=confidence_level,
                confidence_factors={k: round(v, 2) for k, v in confidence_factors.items()},
                risk_factors=risk_factors,
                improvement_suggestions=improvement_suggestions,
                metadata={
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                    "quality_score": quality_score.overall_score
                }
            )
            
        except Exception as e:
            logger.error(f"Confidence assessment failed: {str(e)}")
            raise
    
    def _assess_source_reliability(self, metadata: Dict[str, Any]) -> float:
        """Assess reliability of data source."""
        source = metadata.get("source", "").lower()
        platform = metadata.get("platform", "").lower()
        
        # Get base source reliability
        base_reliability = 0.5  # Default
        for source_type, reliability in self.SOURCE_RELIABILITY.items():
            if source_type in source:
                base_reliability = reliability
                break
        
        # Apply platform confidence multiplier
        platform_multiplier = 1.0
        for plat, multiplier in self.PLATFORM_CONFIDENCE.items():
            if plat in platform:
                platform_multiplier = multiplier
                break
        
        return base_reliability * platform_multiplier
    
    def _assess_method_confidence(self, metadata: Dict[str, Any]) -> float:
        """Assess confidence in collection method."""
        method = metadata.get("collection_method", "").lower()
        automation_tier = metadata.get("automation_tier", "tier_1")
        
        # Base confidence by automation tier
        tier_confidence = {
            "tier_4": 0.90,
            "tier_3": 0.75,
            "tier_2": 0.60,
            "tier_1": 0.45
        }
        
        base_confidence = tier_confidence.get(automation_tier, 0.50)
        
        # Adjust based on specific method characteristics
        if "real_time" in metadata.get("characteristics", []):
            base_confidence *= 1.1
        if "authenticated" in metadata.get("characteristics", []):
            base_confidence *= 1.05
        if "encrypted" in metadata.get("characteristics", []):
            base_confidence *= 1.05
            
        return min(base_confidence, 1.0)
    
    def _calculate_quality_confidence(self, quality_score: QualityScore) -> float:
        """Calculate confidence based on quality score."""
        # Map quality score to confidence
        if quality_score.overall_score >= 90:
            return 0.95
        elif quality_score.overall_score >= 80:
            return 0.85
        elif quality_score.overall_score >= 70:
            return 0.70
        elif quality_score.overall_score >= 60:
            return 0.55
        else:
            return 0.40
    
    def _assess_validation_confidence(self, validation_results: Dict[str, Any]) -> float:
        """Assess confidence based on validation results."""
        passed = validation_results.get("passed", 0)
        failed = validation_results.get("failed", 0)
        total = passed + failed
        
        if total == 0:
            return 0.5
            
        success_rate = passed / total
        
        # Factor in validation coverage
        coverage = validation_results.get("coverage_percentage", 100) / 100
        
        return success_rate * coverage
    
    async def _assess_historical_confidence(
        self,
        metadata: Dict[str, Any]
    ) -> Optional[float]:
        """Assess confidence based on historical accuracy."""
        # This would typically query historical collection accuracy
        # For now, return None to indicate no historical data
        return None
    
    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level based on score."""
        if confidence_score >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.70:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.CRITICAL
    
    def _identify_risk_factors(
        self,
        confidence_factors: Dict[str, float],
        metadata: Dict[str, Any],
        quality_score: QualityScore
    ) -> List[Dict[str, Any]]:
        """Identify risk factors affecting confidence."""
        risk_factors = []
        
        # Low confidence factors
        for factor, score in confidence_factors.items():
            if score < 0.60:
                risk_factors.append({
                    "factor": factor,
                    "severity": "high" if score < 0.40 else "medium",
                    "score": score,
                    "description": f"Low confidence in {factor.replace('_', ' ')}"
                })
        
        # Quality issues
        high_severity_issues = [
            i for i in quality_score.issues_found
            if i.get("severity") == "high"
        ]
        if high_severity_issues:
            risk_factors.append({
                "factor": "data_quality",
                "severity": "high",
                "description": f"{len(high_severity_issues)} high severity quality issues",
                "issue_count": len(high_severity_issues)
            })
        
        # Collection method risks
        if metadata.get("collection_method") == "manual":
            risk_factors.append({
                "factor": "collection_method",
                "severity": "medium",
                "description": "Manual data collection prone to human error"
            })
        
        # Age of data
        if "collection_timestamp" in metadata:
            try:
                collection_dt = datetime.fromisoformat(metadata["collection_timestamp"])
                age_days = (datetime.utcnow() - collection_dt).days
                if age_days > 30:
                    risk_factors.append({
                        "factor": "data_age",
                        "severity": "medium" if age_days < 90 else "high",
                        "description": f"Data is {age_days} days old",
                        "age_days": age_days
                    })
            except Exception:
                pass
        
        return risk_factors
    
    def _generate_improvement_suggestions(
        self,
        confidence_factors: Dict[str, float],
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate suggestions for improving confidence."""
        suggestions = []
        
        # Suggestions based on low confidence factors
        if confidence_factors.get("source_reliability", 1.0) < 0.70:
            suggestions.append(
                "Consider upgrading to API-based collection for higher reliability"
            )
            
        if confidence_factors.get("collection_method", 1.0) < 0.70:
            suggestions.append(
                "Implement automated collection methods to improve confidence"
            )
            
        if confidence_factors.get("data_quality", 1.0) < 0.70:
            suggestions.append(
                "Address data quality issues to improve overall confidence"
            )
        
        # Suggestions based on risk factors
        manual_risks = [r for r in risk_factors if "manual" in r.get("description", "").lower()]
        if manual_risks:
            suggestions.append(
                "Replace manual processes with automated collection where possible"
            )
        
        age_risks = [r for r in risk_factors if r.get("factor") == "data_age"]
        if age_risks:
            suggestions.append(
                "Implement more frequent data collection to ensure freshness"
            )
        
        # General suggestions
        if len(risk_factors) > 3:
            suggestions.append(
                "Consider a comprehensive review of the data collection strategy"
            )
        
        return list(set(suggestions))  # Remove duplicates