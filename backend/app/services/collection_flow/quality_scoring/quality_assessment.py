"""
Quality Assessment Service

This module provides the service for assessing data quality across multiple dimensions.
"""

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.collection_flow.data_transformation import DataType

from .constants import DIMENSION_WEIGHTS, REQUIRED_FIELDS, VALIDATION_RULES
from .enums import QualityDimension
from .models import QualityScore
from .validators import validate_hostname, validate_ip_address, validate_type

logger = logging.getLogger(__name__)


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
        collection_metadata: Optional[Dict[str, Any]] = None,
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
                QualityDimension.UNIQUENESS: uniqueness_score,
            }

            # Weighted average
            overall_score = sum(
                score * DIMENSION_WEIGHTS[dimension.value]
                for dimension, score in dimension_scores.items()
            )

            # Combine all issues
            all_issues = (
                completeness_issues
                + accuracy_issues
                + consistency_issues
                + timeliness_issues
                + validity_issues
                + uniqueness_issues
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
                    "data_type": data_type.value,
                },
            )

        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            raise

    async def _assess_completeness(
        self, records: List[Dict[str, Any]], data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data completeness."""
        issues = []

        if data_type not in REQUIRED_FIELDS:
            return 100.0, issues

        required_fields = REQUIRED_FIELDS[data_type]
        total_fields = len(required_fields["critical"]) + len(
            required_fields["important"]
        )

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
                issues.append(
                    {
                        "dimension": QualityDimension.COMPLETENESS.value,
                        "severity": "high" if missing_critical else "medium",
                        "record_index": idx,
                        "description": "Missing fields",
                        "details": {
                            "missing_critical": missing_critical,
                            "missing_important": missing_important,
                        },
                    }
                )

        avg_completeness = (
            statistics.mean(completeness_scores) if completeness_scores else 0
        )
        return round(avg_completeness, 2), issues

    async def _assess_accuracy(
        self, records: List[Dict[str, Any]], data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data accuracy through validation and cross-reference checks."""
        issues = []
        accuracy_scores = []

        for idx, record in enumerate(records):
            record_issues = 0
            field_count = len(record)

            # Validate IP addresses
            if "ip_address" in record:
                if not validate_ip_address(record["ip_address"]):
                    record_issues += 1
                    issues.append(
                        {
                            "dimension": QualityDimension.ACCURACY.value,
                            "severity": "medium",
                            "record_index": idx,
                            "description": "Invalid IP address format",
                            "field": "ip_address",
                            "value": record["ip_address"],
                        }
                    )

            # Validate hostnames
            if "hostname" in record:
                if not validate_hostname(record["hostname"]):
                    record_issues += 1
                    issues.append(
                        {
                            "dimension": QualityDimension.ACCURACY.value,
                            "severity": "medium",
                            "record_index": idx,
                            "description": "Invalid hostname format",
                            "field": "hostname",
                            "value": record["hostname"],
                        }
                    )

            # Validate numeric ranges
            if "cpu_count" in record:
                try:
                    cpu = int(record["cpu_count"])
                    if cpu < 1 or cpu > 1024:  # Reasonable bounds
                        record_issues += 1
                        issues.append(
                            {
                                "dimension": QualityDimension.ACCURACY.value,
                                "severity": "low",
                                "record_index": idx,
                                "description": "CPU count out of reasonable range",
                                "field": "cpu_count",
                                "value": record["cpu_count"],
                            }
                        )
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
        self, records: List[Dict[str, Any]], data_type: DataType
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
            field
            for field, count in field_frequency.items()
            if count < len(records) and count > len(records) * 0.1
        ]

        if inconsistent_fields:
            issues.append(
                {
                    "dimension": QualityDimension.CONSISTENCY.value,
                    "severity": "medium",
                    "description": "Inconsistent field presence across records",
                    "details": {
                        "fields": inconsistent_fields,
                        "total_records": len(records),
                    },
                }
            )

        # Check for value format consistency
        format_consistency = await self._check_format_consistency(records)

        # Calculate consistency score
        total_possible_issues = len(all_fields) + len(format_consistency)
        actual_issues = len(inconsistent_fields) + len(format_consistency)

        consistency_score = (
            ((total_possible_issues - actual_issues) / total_possible_issues * 100)
            if total_possible_issues > 0
            else 100.0
        )

        issues.extend(format_consistency)

        return round(consistency_score, 2), issues

    async def _assess_timeliness(
        self,
        records: List[Dict[str, Any]],
        collection_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data timeliness and freshness."""
        issues = []

        # Check collection timestamp
        if collection_metadata:
            collection_time = collection_metadata.get("collection_timestamp")
            if collection_time:
                try:
                    collection_dt = datetime.fromisoformat(collection_time)
                    age_hours = (
                        datetime.utcnow() - collection_dt
                    ).total_seconds() / 3600

                    if age_hours > 24:
                        issues.append(
                            {
                                "dimension": QualityDimension.TIMELINESS.value,
                                "severity": (
                                    "medium" if age_hours < 168 else "high"
                                ),  # 7 days
                                "description": f"Data is {age_hours:.1f} hours old",
                                "details": {
                                    "collection_timestamp": collection_time,
                                    "age_hours": age_hours,
                                },
                            }
                        )
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
                                issues.append(
                                    {
                                        "dimension": QualityDimension.TIMELINESS.value,
                                        "severity": "high",
                                        "record_index": idx,
                                        "description": f"Stale data in {field}",
                                        "details": {
                                            "field": field,
                                            "age_days": age_days,
                                            "value": record[field],
                                        },
                                    }
                                )
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
        self, records: List[Dict[str, Any]], data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data validity against defined rules."""
        issues = []
        validity_scores = []

        for idx, record in enumerate(records):
            invalid_fields = 0
            total_validated_fields = 0

            for field, value in record.items():
                if field in VALIDATION_RULES:
                    total_validated_fields += 1
                    rule = VALIDATION_RULES[field]

                    # Type validation
                    if "type" in rule:
                        if not validate_type(value, rule["type"]):
                            invalid_fields += 1
                            issues.append(
                                {
                                    "dimension": QualityDimension.VALIDITY.value,
                                    "severity": "medium",
                                    "record_index": idx,
                                    "description": f"Invalid type for {field}",
                                    "expected_type": rule["type"],
                                    "actual_value": str(value),
                                }
                            )

                    # Range validation
                    if "min" in rule or "max" in rule:
                        try:
                            num_value = float(value)
                            if "min" in rule and num_value < rule["min"]:
                                invalid_fields += 1
                                issues.append(
                                    {
                                        "dimension": QualityDimension.VALIDITY.value,
                                        "severity": "medium",
                                        "record_index": idx,
                                        "description": f"{field} below minimum value",
                                        "min_value": rule["min"],
                                        "actual_value": num_value,
                                    }
                                )
                            if "max" in rule and num_value > rule["max"]:
                                invalid_fields += 1
                                issues.append(
                                    {
                                        "dimension": QualityDimension.VALIDITY.value,
                                        "severity": "medium",
                                        "record_index": idx,
                                        "description": f"{field} above maximum value",
                                        "max_value": rule["max"],
                                        "actual_value": num_value,
                                    }
                                )
                        except (ValueError, TypeError):
                            pass

            # Calculate validity score for this record
            if total_validated_fields > 0:
                validity = (
                    (total_validated_fields - invalid_fields) / total_validated_fields
                ) * 100
            else:
                validity = 100.0

            validity_scores.append(validity)

        avg_validity = statistics.mean(validity_scores) if validity_scores else 100.0
        return round(avg_validity, 2), issues

    async def _assess_uniqueness(
        self, records: List[Dict[str, Any]], data_type: DataType
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Assess data uniqueness and identify duplicates."""
        issues = []

        # Define key fields for uniqueness check
        key_fields = {
            DataType.SERVER: ["hostname", "ip_address"],
            DataType.APPLICATION: ["app_name", "environment"],
            DataType.DATABASE: ["db_name", "host", "port"],
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
                    issues.append(
                        {
                            "dimension": QualityDimension.UNIQUENESS.value,
                            "severity": "high",
                            "record_index": idx,
                            "description": "Duplicate record found",
                            "details": {
                                "duplicate_of_index": seen_keys[key],
                                "key_fields": key_fields[data_type],
                                "key_value": key,
                            },
                        }
                    )
                else:
                    seen_keys[key] = idx

        # Calculate uniqueness score
        if len(records) > 0:
            uniqueness_score = ((len(records) - duplicate_count) / len(records)) * 100
        else:
            uniqueness_score = 100.0

        return round(uniqueness_score, 2), issues

    async def _check_format_consistency(
        self, records: List[Dict[str, Any]]
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
            issues.append(
                {
                    "dimension": QualityDimension.CONSISTENCY.value,
                    "severity": "low",
                    "description": f"Inconsistent format for {field}",
                    "details": {
                        "field": field,
                        "format_patterns": {k: len(v) for k, v in patterns.items()},
                    },
                }
            )

        return issues

    def _generate_quality_recommendations(
        self,
        dimension_scores: Dict[QualityDimension, float],
        issues: List[Dict[str, Any]],
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
                    recommendations.append("Implement data normalization pipeline")
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
