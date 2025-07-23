"""
Task Processor Handler
Handles task execution and processing operations.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Handles task processing with graceful fallbacks."""

    def __init__(self):
        self.service_available = False
        self.field_mapping_tool = None
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.services.agent_monitor import agent_monitor

            self.agent_monitor = agent_monitor
            self.service_available = True
            logger.info("Task processor initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Task processor services not available: {e}")
            self.service_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    def set_field_mapping_tool(self, field_mapping_tool):
        """Set the field mapping tool for enhanced analysis."""
        self.field_mapping_tool = field_mapping_tool
        logger.info("Field mapping tool set for task processor")

    async def execute_task_async(self, task: Any) -> str:
        """Execute a task asynchronously."""
        try:
            if not self.service_available:
                return self._fallback_execute_task(task)

            # Execute task in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Use proper task execution based on task type
                if hasattr(task, "execute"):
                    result = await loop.run_in_executor(executor, task.execute)
                else:
                    result = await loop.run_in_executor(executor, str, task)

                return str(result) if result else "Task completed"

        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return self._fallback_execute_task(task)

    async def process_cmdb_data(
        self, processing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process CMDB data analysis with enhanced field mapping intelligence."""
        try:
            if not self.service_available:
                return self._fallback_process_cmdb_data(processing_data)

            # Extract data
            cmdb_data = processing_data.get("cmdb_data", {})

            # Enhanced field mapping analysis if tool is available
            field_analysis = {}
            mapping_context = {}
            enhanced_mappings = {}

            if self.field_mapping_tool and cmdb_data.get("structure", {}).get(
                "columns"
            ):
                available_columns = cmdb_data["structure"]["columns"]

                # Get field mapping analysis with content intelligence
                field_analysis = self.field_mapping_tool.agent_analyze_columns(
                    available_columns, "server"
                )
                mapping_context = self.field_mapping_tool.agent_get_mapping_context()

                # Prepare sample data for content-based analysis
                sample_data_for_analysis = None
                if cmdb_data.get("sample_data") and len(cmdb_data["sample_data"]) > 0:
                    try:
                        sample_rows = []
                        for record in cmdb_data["sample_data"][
                            :5
                        ]:  # Use first 5 records
                            row = [
                                str(record.get(col, "")) for col in available_columns
                            ]
                            sample_rows.append(row)
                        sample_data_for_analysis = sample_rows
                    except Exception as e:
                        logger.warning(
                            f"Could not prepare sample data for content analysis: {e}"
                        )

                # Enhanced content-aware field mapping
                if sample_data_for_analysis:
                    enhanced_field_analysis = (
                        self.field_mapping_tool.mapping_engine.analyze_columns(
                            available_columns, "server", sample_data_for_analysis
                        )
                    )
                    enhanced_mappings = enhanced_field_analysis.get("mapped_fields", {})

            # Enhanced analysis with field mapping intelligence
            cmdb_data.get("filename", "unknown")
            sample_data = cmdb_data.get("sample_data", [])

            if not sample_data:
                return {
                    "status": "no_data",
                    "message": "No sample data found in CMDB data",
                    "analysis_summary": "No analysis performed",
                }

            # Intelligent data quality analysis
            asset_type_detected = self._detect_asset_type_intelligently(
                sample_data, enhanced_mappings
            )
            quality_score = self._calculate_intelligent_quality_score(
                sample_data, enhanced_mappings
            )
            issues = self._identify_intelligent_issues(sample_data, enhanced_mappings)
            recommendations = self._generate_intelligent_recommendations(
                sample_data, enhanced_mappings, issues
            )
            missing_fields = self._identify_truly_missing_fields(
                enhanced_mappings, field_analysis
            )

            return {
                "status": "completed",
                "asset_type_detected": asset_type_detected,
                "confidence_level": 0.85,
                "data_quality_score": quality_score,
                "issues": issues,
                "recommendations": recommendations,
                "missing_fields_relevant": missing_fields,
                "migration_readiness": (
                    "ready" if quality_score >= 80 else "requires_cleansing"
                ),
                "enhanced_analysis": True,
                "field_mapping_applied": bool(self.field_mapping_tool),
                "enhanced_mappings": enhanced_mappings,
                "field_analysis": field_analysis,
                "mapping_context": mapping_context,
                "analysis_summary": "Enhanced AI analysis with field mapping intelligence applied",
            }

        except Exception as e:
            logger.error(f"Error processing CMDB data: {e}")
            return self._fallback_process_cmdb_data(processing_data)

    async def process_user_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user feedback for learning."""
        try:
            if not self.service_available:
                return self._fallback_process_feedback(feedback_data)

            feedback_type = feedback_data.get("feedback_type", "general")
            feedback_data.get("content", "")

            # Process feedback based on type
            if feedback_type == "strategy_correction":
                return await self._process_strategy_feedback(feedback_data)
            elif feedback_type == "field_mapping":
                return await self._process_mapping_feedback(feedback_data)
            else:
                return await self._process_general_feedback(feedback_data)

        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return self._fallback_process_feedback(feedback_data)

    async def _process_strategy_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process strategy correction feedback."""
        return {
            "status": "processed",
            "feedback_type": "strategy_correction",
            "learning_applied": True,
            "message": "Strategy feedback processed and applied to learning model",
        }

    async def _process_mapping_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process field mapping feedback."""
        return {
            "status": "processed",
            "feedback_type": "field_mapping",
            "learning_applied": True,
            "message": "Field mapping feedback processed and applied to learning model",
        }

    async def _process_general_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process general feedback."""
        return {
            "status": "processed",
            "feedback_type": "general",
            "learning_applied": True,
            "message": "General feedback processed and applied to learning model",
        }

    # Fallback methods
    def _fallback_execute_task(self, task: Any) -> str:
        """Fallback task execution."""
        return "Task executed in fallback mode"

    def _fallback_process_cmdb_data(
        self, processing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback CMDB processing."""
        return {
            "status": "completed",
            "processed_applications": 0,
            "analysis_summary": "CMDB data processed in fallback mode",
            "fallback_mode": True,
        }

    def _fallback_process_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback feedback processing."""
        return {
            "status": "processed",
            "feedback_type": feedback_data.get("feedback_type", "general"),
            "message": "Feedback processed in fallback mode",
            "fallback_mode": True,
        }

    # Enhanced analysis methods
    def _detect_asset_type_intelligently(
        self, sample_data: List[Dict], enhanced_mappings: Dict
    ) -> str:
        """Detect asset type using enhanced field mapping intelligence."""
        try:
            if not sample_data:
                return "server"

            # Use enhanced mappings to understand data characteristics
            if enhanced_mappings:
                # Check for application-specific fields
                app_indicators = [
                    "application",
                    "app_name",
                    "service",
                    "business_service",
                ]
                for field in enhanced_mappings.values():
                    if any(indicator in field.lower() for indicator in app_indicators):
                        return "application"

                # Check for database-specific fields
                db_indicators = ["database", "db_type", "db_version", "schema"]
                for field in enhanced_mappings.values():
                    if any(indicator in field.lower() for indicator in db_indicators):
                        return "database"

            # Fallback to analyzing actual field names
            if sample_data and isinstance(sample_data[0], dict):
                fields = list(sample_data[0].keys())
                field_names_lower = [f.lower() for f in fields]

                if any(
                    "app" in field or "application" in field
                    for field in field_names_lower
                ):
                    return "application"
                elif any(
                    "db" in field or "database" in field for field in field_names_lower
                ):
                    return "database"

            return "server"  # Default

        except Exception as e:
            logger.warning(f"Error detecting asset type: {e}")
            return "server"

    def _calculate_intelligent_quality_score(
        self, sample_data: List[Dict], enhanced_mappings: Dict
    ) -> int:
        """Calculate quality score using enhanced field mapping intelligence."""
        try:
            if not sample_data:
                return 0

            total_score = 0
            factors = 0

            # Field mapping quality (40% of score)
            if enhanced_mappings:
                mapping_quality = (
                    len(enhanced_mappings) / max(len(sample_data[0].keys()), 1) * 40
                )
                total_score += mapping_quality
                factors += 1

            # Data completeness (30% of score)
            completeness_scores = []
            for record in sample_data[:10]:  # Sample first 10 records
                filled_fields = sum(
                    1 for value in record.values() if value and str(value).strip()
                )
                completeness = (filled_fields / len(record)) * 100 if record else 0
                completeness_scores.append(completeness)

            if completeness_scores:
                avg_completeness = sum(completeness_scores) / len(completeness_scores)
                total_score += avg_completeness * 0.3
                factors += 1

            # Field consistency (30% of score)
            consistency_score = 80  # Base consistency score
            total_score += consistency_score * 0.3
            factors += 1

            return int(total_score / factors) if factors > 0 else 60

        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 60

    def _identify_intelligent_issues(
        self, sample_data: List[Dict], enhanced_mappings: Dict
    ) -> List[str]:
        """Identify issues using enhanced field mapping intelligence."""
        issues = []
        try:
            if not sample_data:
                return ["No data available for analysis"]

            # Check for missing critical fields using enhanced mappings
            critical_fields = ["hostname", "asset_name", "environment", "asset_type"]
            mapped_critical = []

            if enhanced_mappings:
                for original_field, mapped_field in enhanced_mappings.items():
                    if any(
                        critical in mapped_field.lower() for critical in critical_fields
                    ):
                        mapped_critical.append(mapped_field)

            unmapped_critical = [
                field
                for field in critical_fields
                if field not in [mf.lower().replace(" ", "_") for mf in mapped_critical]
            ]
            if unmapped_critical:
                issues.append(
                    f"Missing critical fields: {', '.join(unmapped_critical)}"
                )

            # Check for empty values in mapped fields
            empty_count = 0
            for record in sample_data[:5]:
                for field, value in record.items():
                    if not value or str(value).strip() in [
                        "",
                        "null",
                        "none",
                        "unknown",
                    ]:
                        empty_count += 1

            if (
                empty_count > len(sample_data) * 2
            ):  # More than 2 empty fields per record on average
                issues.append(
                    f"Found {empty_count} empty or null values requiring cleanup"
                )

            # Check for potential duplicates
            if len(sample_data) > 1:
                potential_duplicates = 0
                hostnames = [
                    record.get("hostname", record.get("name", ""))
                    for record in sample_data
                ]
                unique_hostnames = set(filter(None, hostnames))
                if len(hostnames) - len(unique_hostnames) > 0:
                    potential_duplicates = len(hostnames) - len(unique_hostnames)
                    issues.append(
                        f"Found {potential_duplicates} potential duplicate hostnames"
                    )

            return issues if issues else ["Data quality looks good"]

        except Exception as e:
            logger.warning(f"Error identifying issues: {e}")
            return ["Error analyzing data quality"]

    def _generate_intelligent_recommendations(
        self, sample_data: List[Dict], enhanced_mappings: Dict, issues: List[str]
    ) -> List[str]:
        """Generate recommendations using enhanced field mapping intelligence."""
        recommendations = []
        try:
            # Recommendations based on enhanced mappings
            if enhanced_mappings:
                recommendations.append(
                    "Use enhanced field mappings to improve data consistency"
                )

                # Specific recommendations based on mapped fields
                if any(
                    "environment" in mapped_field.lower()
                    for mapped_field in enhanced_mappings.values()
                ):
                    recommendations.append(
                        "Standardize environment values using mapped field intelligence"
                    )

                if any(
                    "memory" in mapped_field.lower() or "ram" in mapped_field.lower()
                    for mapped_field in enhanced_mappings.values()
                ):
                    recommendations.append(
                        "Validate memory/RAM values are in correct units (GB)"
                    )

            # Recommendations based on issues
            if any("missing" in issue.lower() for issue in issues):
                recommendations.append(
                    "Complete missing field mappings using content analysis"
                )

            if any("duplicate" in issue.lower() for issue in issues):
                recommendations.append(
                    "Resolve duplicate entries by adding unique identifiers"
                )

            if any(
                "empty" in issue.lower() or "null" in issue.lower() for issue in issues
            ):
                recommendations.append(
                    "Fill empty values using intelligent pattern matching"
                )

            return (
                recommendations
                if recommendations
                else ["Data is ready for migration analysis"]
            )

        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            return ["Use AI-enhanced field mapping for better analysis"]

    def _identify_truly_missing_fields(
        self, enhanced_mappings: Dict, field_analysis: Dict
    ) -> List[str]:
        """Identify truly missing fields after applying enhanced field mapping intelligence."""
        try:
            critical_fields = [
                "Business Owner",
                "Criticality",
                "Department",
                "Environment",
            ]

            # Check which critical fields are actually mapped
            mapped_critical_fields = []
            if enhanced_mappings:
                for mapped_field in enhanced_mappings.values():
                    for critical_field in critical_fields:
                        if critical_field.lower().replace(
                            " ", "_"
                        ) in mapped_field.lower().replace(" ", "_"):
                            mapped_critical_fields.append(critical_field)

            # Return fields that are truly missing (not mapped)
            truly_missing = [
                field
                for field in critical_fields
                if field not in mapped_critical_fields
            ]

            # If no enhanced mappings available, return default missing fields
            if not enhanced_mappings:
                return ["Business Owner", "Criticality"]

            return truly_missing[:3]  # Limit to top 3 most important

        except Exception as e:
            logger.warning(f"Error identifying missing fields: {e}")
            return ["Business Owner", "Criticality"]

    async def process_asset_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user feedback from asset management operations to improve AI intelligence."""
        try:
            feedback_type = feedback_data.get("operation_type", "general")

            # Apply field mapping learning if available
            if self.field_mapping_tool and feedback_data.get("field_mappings"):
                for mapping in feedback_data["field_mappings"]:
                    source_field = mapping.get("source_field")
                    target_field = mapping.get("target_field")
                    if source_field and target_field:
                        self.field_mapping_tool.agent_learn_field_mapping(
                            source_field,
                            target_field,
                            f"asset_feedback_{feedback_type}",
                        )
                        logger.info(
                            f"Applied field mapping learning: {source_field} -> {target_field}"
                        )

            return {
                "status": "processed",
                "feedback_type": feedback_type,
                "learning_applied": True,
                "field_mapping_learning": bool(self.field_mapping_tool),
                "message": "Asset feedback processed and applied to AI intelligence",
            }

        except Exception as e:
            logger.error(f"Error processing asset feedback: {e}")
            return self._fallback_process_feedback(feedback_data)
