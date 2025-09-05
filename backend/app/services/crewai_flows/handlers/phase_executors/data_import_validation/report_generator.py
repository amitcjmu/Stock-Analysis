"""
Report generation for data import validation.
Creates user-friendly reports and insights from validation results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates user-friendly reports from validation results"""

    def __init__(self, state):
        self.state = state

    def generate_user_report(
        self, validation_results: Dict[str, Any], file_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a user-friendly validation report"""
        try:
            # Extract key metrics
            total_records = validation_results.get("total_records", 0)
            is_valid = validation_results.get("is_valid", False)
            overall_score = validation_results.get("validation_summary", {}).get(
                "overall_quality_score", 0
            )

            # Generate status message
            status_message = (
                "✅ Validation Passed" if is_valid else "❌ Validation Failed"
            )

            # Create summary
            summary = {
                "status": "PASSED" if is_valid else "FAILED",
                "message": status_message,
                "total_records": total_records,
                "quality_score": f"{overall_score:.1%}",
                "file_type": file_analysis.get("detected_type", "unknown"),
                "confidence": f"{file_analysis.get('confidence', 0):.0%}",
                "recommended_agent": file_analysis.get(
                    "recommended_agent", "CMDB_Data_Analyst_Agent"
                ),
            }

            # Detailed findings
            findings = []

            # Structure findings
            structure_valid = validation_results.get("structure_validation", {}).get(
                "is_valid", False
            )
            if structure_valid:
                findings.append(
                    {
                        "category": "Data Structure",
                        "status": "PASSED",
                        "message": f"Valid data structure with {total_records} records",
                        "details": validation_results.get("structure_validation", {}),
                    }
                )
            else:
                reason = validation_results.get("structure_validation", {}).get(
                    "reason", "Unknown issue"
                )
                findings.append(
                    {
                        "category": "Data Structure",
                        "status": "FAILED",
                        "message": f"Structure validation failed: {reason}",
                        "details": validation_results.get("structure_validation", {}),
                    }
                )

            # PII findings
            pii_results = validation_results.get("pii_detection", {})
            if pii_results.get("pii_detected", False):
                findings.append(
                    {
                        "category": "Privacy (PII)",
                        "status": "WARNING",
                        "message": f"PII detected: {', '.join(pii_results.get('pii_types', []))}",
                        "details": pii_results,
                    }
                )
            else:
                findings.append(
                    {
                        "category": "Privacy (PII)",
                        "status": "PASSED",
                        "message": "No PII detected in sample data",
                        "details": pii_results,
                    }
                )

            # Security findings
            security_results = validation_results.get("security_scan", {})
            if security_results.get("malicious_content_detected", False):
                findings.append(
                    {
                        "category": "Security",
                        "status": "FAILED",
                        "message": "Malicious content detected - upload blocked",
                        "details": security_results,
                    }
                )
            else:
                findings.append(
                    {
                        "category": "Security",
                        "status": "PASSED",
                        "message": "No security threats detected",
                        "details": security_results,
                    }
                )

            # Data type findings
            type_results = validation_results.get("data_type_validation", {})
            type_score = type_results.get("quality_score", 0)
            findings.append(
                {
                    "category": "Data Types",
                    "status": "PASSED" if type_score > 0.7 else "WARNING",
                    "message": f"Data type quality: {type_score:.1%}",
                    "details": type_results,
                }
            )

            # Source findings
            source_results = validation_results.get("source_validation", {})
            if source_results.get("is_valid", False):
                findings.append(
                    {
                        "category": "Data Source",
                        "status": "PASSED",
                        "message": "Valid source information provided",
                        "details": source_results,
                    }
                )
            else:
                findings.append(
                    {
                        "category": "Data Source",
                        "status": "WARNING",
                        "message": "Limited source information available",
                        "details": source_results,
                    }
                )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                validation_results, file_analysis
            )

            return {
                "report_id": f"validation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": summary,
                "findings": findings,
                "recommendations": recommendations,
                "metadata": {
                    "validation_version": "1.0",
                    "total_checks": len(findings),
                    "passed_checks": len(
                        [f for f in findings if f["status"] == "PASSED"]
                    ),
                    "failed_checks": len(
                        [f for f in findings if f["status"] == "FAILED"]
                    ),
                    "warning_checks": len(
                        [f for f in findings if f["status"] == "WARNING"]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"❌ Report generation failed: {str(e)}", exc_info=True)
            return {
                "report_id": f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "status": "ERROR",
                    "message": f"Report generation failed: {str(e)}",
                },
                "error": str(e),
            }

    def _generate_recommendations(
        self, validation_results: Dict[str, Any], file_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []

        try:
            # Add recommendations based on analysis

            # File type recommendations
            detected_type = file_analysis.get("detected_type", "unknown")
            confidence = file_analysis.get("confidence", 0)

            if confidence > 0.7:
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "category": "Agent Routing",
                        "title": "Optimal Agent Routing Available",
                        "description": f"High confidence detection of {detected_type} data type",
                        "action": f"Route to {file_analysis.get('recommended_agent', 'default agent')} "
                        f"for specialized processing",
                    }
                )
            elif confidence < 0.5:
                recommendations.append(
                    {
                        "priority": "MEDIUM",
                        "category": "Data Quality",
                        "title": "Review Data Type Classification",
                        "description": "Low confidence in automatic data type detection",
                        "action": "Manual review recommended to optimize processing workflow",
                    }
                )

            # Structure recommendations
            if not validation_results.get("structure_validation", {}).get(
                "is_valid", False
            ):
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "category": "Data Structure",
                        "title": "Fix Data Structure Issues",
                        "description": "Data structure validation failed",
                        "action": "Review and correct data format before proceeding",
                    }
                )

            # PII recommendations
            pii_detected = validation_results.get("pii_detection", {}).get(
                "pii_detected", False
            )
            if pii_detected:
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "category": "Privacy & Compliance",
                        "title": "PII Handling Required",
                        "description": "Personally identifiable information detected in data",
                        "action": "Implement appropriate data protection measures and review compliance requirements",
                    }
                )

            # Security recommendations
            security_threats = validation_results.get("security_scan", {}).get(
                "malicious_content_detected", False
            )
            if security_threats:
                recommendations.append(
                    {
                        "priority": "CRITICAL",
                        "category": "Security",
                        "title": "Security Threat Detected",
                        "description": "Malicious content found in uploaded data",
                        "action": "Do not proceed with data processing. Review data source and sanitize content.",
                    }
                )

            # Quality recommendations
            overall_score = validation_results.get("validation_summary", {}).get(
                "overall_quality_score", 0
            )
            if overall_score < 0.7:
                recommendations.append(
                    {
                        "priority": "MEDIUM",
                        "category": "Data Quality",
                        "title": "Improve Data Quality",
                        "description": f"Overall quality score is {overall_score:.1%}",
                        "action": "Review data cleansing and standardization options to improve processing accuracy",
                    }
                )

            # Default recommendation if none generated
            if not recommendations:
                recommendations.append(
                    {
                        "priority": "LOW",
                        "category": "Next Steps",
                        "title": "Proceed with Standard Processing",
                        "description": "No critical issues detected",
                        "action": "Continue with normal data processing workflow",
                    }
                )

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {str(e)}")
            recommendations.append(
                {
                    "priority": "LOW",
                    "category": "System",
                    "title": "Review Validation Results",
                    "description": "Recommendation engine encountered an error",
                    "action": "Manually review validation results for next steps",
                }
            )

        return recommendations
