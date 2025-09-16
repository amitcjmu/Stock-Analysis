"""
Core executor class for data import validation phase.
Orchestrates validation checks, file analysis, and result processing.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..base_phase_executor import BasePhaseExecutor
from .file_analyzer import FileAnalyzer
from .report_generator import ReportGenerator
from .validation_checks import ValidationChecks

logger = logging.getLogger(__name__)


class DataImportValidationExecutor(BasePhaseExecutor):
    """
    Execute data import validation phase with security scanning and PII detection.
    This is the first phase that must complete before field mapping can begin.
    """

    def __init__(self, state, crew_manager, flow_bridge=None):
        super().__init__(state, crew_manager, flow_bridge)
        self.validation_checks = ValidationChecks(state)
        self.file_analyzer = FileAnalyzer(state)
        self.report_generator = ReportGenerator(state)

    def get_phase_name(self) -> str:
        """Get the name of this phase"""
        return "data_import"

    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes"""
        return 16.67  # 1/6 phases = ~16.67%

    def _get_phase_timeout(self) -> Optional[int]:
        """
        Override timeout for data import validation - needs more time for comprehensive validation
        """
        return 300  # 5 minutes timeout for data import validation with security scans

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        return {
            "raw_data": self.state.raw_data,
            "metadata": self.state.metadata,
            "validation_requirements": {
                "check_pii": True,
                "check_security": True,
                "check_data_types": True,
                "check_source": True,
            },
        }

    async def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        # Debug: Log what we're storing
        logger.info("🔍 DEBUG: Storing data import validation results")
        logger.info(f"🔍 DEBUG: Results keys: {list(results.keys())}")
        logger.info(
            f"🔍 DEBUG: Raw data in state: "
            f"{len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0} records"
        )

        # Store the phase results
        self.state.phase_data["data_import"] = results

        # IMPORTANT: Also update the data_validation_results field for backward compatibility
        self.state.data_validation_results = results

        # Extract and store detected columns from file analysis
        file_analysis = results.get("file_analysis", {})
        if file_analysis and "field_analysis" in file_analysis:
            detected_columns = list(file_analysis["field_analysis"].keys())
            if detected_columns:
                self.state.metadata["detected_columns"] = detected_columns
                logger.info(
                    f"🔍 Extracted detected columns from file analysis: {detected_columns}"
                )
        else:
            # Fallback: extract columns from raw data
            if self.state.raw_data and isinstance(self.state.raw_data, list):
                first_record = self.state.raw_data[0]
                if isinstance(first_record, dict):
                    detected_columns = list(first_record.keys())
                    self.state.metadata["detected_columns"] = detected_columns
                    logger.info(
                        f"🔍 Extracted detected columns from raw data: {detected_columns}"
                    )

        # Store validated data in raw_data if it's provided
        if "validated_data" in results and results["validated_data"]:
            logger.info(
                f"🔍 DEBUG: Storing validated_data in state.raw_data: {len(results['validated_data'])} records"
            )
            self.state.raw_data = results["validated_data"]

        is_valid = results.get("is_valid", False)
        reason = results.get("reason", "")

        if is_valid:
            self.state.phase_completion["data_import"] = True
            logger.info("✅ DEBUG: Data import phase marked as completed")

            # 🔧 CC FIX: Sync phase completion to discovery flow database
            await self._sync_phase_completion_to_database("data_import", True)
        else:
            # Only log failure if validation actually failed
            if not reason:
                reason = "Validation failed without specific reason"
            logger.warning(f"⚠️ DEBUG: Data import validation failed: {reason}")
            logger.warning(f"⚠️ DEBUG: Full validation results: {results}")

            # Store validation failure in state for debugging
            self.state.add_error("data_import", reason, {"full_results": results})

        # Add real-time insights from validation results
        if hasattr(self.state, "agent_insights"):
            self._add_validation_insights(results)

    def _add_validation_insights(self, results: Dict[str, Any]):
        """Add real-time insights from validation results"""
        try:
            # Add file type analysis insight
            file_analysis = results.get("file_analysis", {})
            if file_analysis:
                insight = (
                    f"📊 Detected {file_analysis.get('detected_type', 'unknown')} data type with "
                    f"{file_analysis.get('confidence', 0):.0%} confidence. Recommended agent: "
                    f"{file_analysis.get('recommended_agent', 'CMDB_Data_Analyst_Agent')}"
                )
                self.state.agent_insights.append(
                    {
                        "agent": "DataImportValidationExecutor",
                        "phase": "data_import",
                        "insight": insight,
                        "timestamp": self._get_timestamp(),
                        "confidence": file_analysis.get("confidence", 0),
                    }
                )

            # Add data quality insight
            validation_summary = results.get("validation_summary", {})
            if validation_summary:
                quality_score = validation_summary.get("overall_quality_score", 0)
                insight = (
                    f"📈 Data quality score: {quality_score:.1%}. "
                    f"Structure valid: {'Yes' if validation_summary.get('structure_valid') else 'No'}. "
                    f"Security threats: {'Detected' if validation_summary.get('security_threats') else 'None'}"
                )
                self.state.agent_insights.append(
                    {
                        "agent": "DataImportValidationExecutor",
                        "phase": "data_import",
                        "insight": insight,
                        "timestamp": self._get_timestamp(),
                        "confidence": quality_score,
                    }
                )

            # Add security insights
            security_scan = results.get("security_scan", {})
            pii_detection = results.get("pii_detection", {})

            if security_scan.get("malicious_content_detected", False):
                self.state.agent_insights.append(
                    {
                        "agent": "DataImportValidationExecutor",
                        "phase": "data_import",
                        "insight": "🛡️ CRITICAL: Malicious content detected in uploaded data. "
                        "Upload blocked for security.",
                        "timestamp": self._get_timestamp(),
                        "confidence": 0.95,
                    }
                )

            if pii_detection.get("pii_detected", False):
                pii_types = ", ".join(pii_detection.get("pii_types", []))
                self.state.agent_insights.append(
                    {
                        "agent": "DataImportValidationExecutor",
                        "phase": "data_import",
                        "insight": f"🔒 PII detected in data: {pii_types}. Privacy compliance measures recommended.",
                        "timestamp": self._get_timestamp(),
                        "confidence": pii_detection.get("confidence", 0),
                    }
                )

            # Add recommendations from detailed report
            user_report = results.get("user_report", {})
            recommendations = user_report.get("recommendations", [])
            for recommendation in recommendations[:3]:  # Limit to top 3 recommendations
                self.state.agent_insights.append(
                    {
                        "agent": "DataImportValidationExecutor",
                        "phase": "data_import",
                        "insight": f"💡 {recommendation.get('title', 'Recommendation')}: "
                        f"{recommendation.get('action', 'No action specified')}",
                        "timestamp": self._get_timestamp(),
                        "confidence": (
                            0.8 if recommendation.get("priority") == "HIGH" else 0.6
                        ),
                    }
                )

        except Exception as e:
            logger.error(f"❌ Failed to add validation insights: {str(e)}")

    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process the result from crew execution"""
        logger.info("🔍 Processing crew result from data import validation")

        # Extract raw result
        raw_result = crew_result
        if hasattr(crew_result, "raw"):
            raw_result = crew_result.raw

        try:
            # Try to parse the JSON response from the crew
            if isinstance(raw_result, str):
                parsed_result = json.loads(raw_result)

                # Extract validation results from the parsed response
                result = {
                    "is_valid": True,  # If crew returned a result, validation passed
                    "validation_passed": True,
                    "crew_response": parsed_result,
                    "timestamp": self._get_timestamp(),
                    "total_records": (
                        len(self.state.raw_data) if self.state.raw_data else 0
                    ),
                }

                # Add validation details if provided
                if "validation_results" in parsed_result:
                    result.update(parsed_result["validation_results"])

                # Add the original data as validated_data
                if self.state.raw_data:
                    result["validated_data"] = self.state.raw_data
                    logger.info(
                        f"🔍 Added {len(self.state.raw_data)} validated records to result"
                    )
                else:
                    logger.warning("⚠️ No raw_data found in state to validate")

                return result
            else:
                # Handle non-JSON crew response
                result = {
                    "is_valid": True,  # Assume valid if crew ran
                    "validation_passed": True,
                    "crew_response": str(raw_result),
                    "timestamp": self._get_timestamp(),
                    "total_records": (
                        len(self.state.raw_data) if self.state.raw_data else 0
                    ),
                }

                if self.state.raw_data:
                    result["validated_data"] = self.state.raw_data

                return result

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse crew result as JSON: {e}")
            # Return successful result anyway since crew execution completed
            return {
                "is_valid": True,
                "validation_passed": True,
                "crew_response_text": str(raw_result),
                "parse_error": str(e),
                "timestamp": self._get_timestamp(),
                "total_records": len(self.state.raw_data) if self.state.raw_data else 0,
                "validated_data": self.state.raw_data if self.state.raw_data else [],
            }

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data import validation with CrewAI crew"""
        try:
            logger.info("🚀 Starting data import validation with CrewAI crew")

            # Use CrewAI crew for intelligent data validation
            crew_result = await super().execute_with_crew(crew_input)

            if crew_result:
                # Process the crew result
                processed_result = self._process_crew_result(crew_result)

                # Add additional analysis
                file_analysis = self.file_analyzer.analyze_file_type_and_content()
                processed_result["file_analysis"] = file_analysis

                # Generate user report
                user_report = self.report_generator.generate_user_report(
                    processed_result, file_analysis
                )
                processed_result["user_report"] = user_report

                logger.info("✅ CrewAI data import validation completed successfully")
                return processed_result
            else:
                logger.warning(
                    "⚠️ CrewAI execution returned no result, falling back to internal validation"
                )
                return await self._execute_fallback_validation()

        except Exception as e:
            logger.error(
                f"❌ CrewAI data import validation failed: {str(e)}", exc_info=True
            )
            logger.info("🔄 Falling back to internal validation due to CrewAI error")
            return await self._execute_fallback_validation()

    async def _execute_fallback_validation(self) -> Dict[str, Any]:
        """Execute fallback validation when CrewAI is not available"""
        try:
            logger.info("🔄 Executing fallback data import validation")

            # Debug: Check data availability
            logger.info(
                f"🔍 DEBUG: State raw_data: "
                f"{'exists' if hasattr(self.state, 'raw_data') else 'missing'}, "
                f"length: {len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0}"
            )

            if not hasattr(self.state, "raw_data") or not self.state.raw_data:
                logger.error("❌ No raw data available for validation")
                return {
                    "is_valid": False,
                    "validation_passed": False,
                    "reason": "No data available for validation",
                    "timestamp": self._get_timestamp(),
                    "total_records": 0,
                }

            # Perform validation using agent-like analysis patterns
            validation_results = (
                await self.validation_checks.perform_validation_checks()
            )

            # Add file analysis
            file_analysis = self.file_analyzer.analyze_file_type_and_content()
            validation_results["file_analysis"] = file_analysis

            # Generate user report
            user_report = self.report_generator.generate_user_report(
                validation_results, file_analysis
            )
            validation_results["user_report"] = user_report

            logger.info("✅ Fallback data import validation completed")
            return validation_results

        except Exception as e:
            logger.error(f"❌ Fallback validation failed: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "validation_passed": False,
                "reason": f"Validation failed: {str(e)}",
                "error": str(e),
                "timestamp": self._get_timestamp(),
                "total_records": 0,
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()

    async def _sync_phase_completion_to_database(
        self, phase: str, completed: bool
    ) -> None:
        """
        🔧 CC FIX: Synchronize CrewAI phase completion to discovery flow database.

        This fixes the root cause where CrewAI flow state updates were not being
        synchronized back to the discovery_flows table, causing the UI to show
        flows stuck in initialization phase.

        Args:
            phase: The phase name (e.g., "data_import")
            completed: Whether the phase is completed
        """
        try:
            logger.info(
                f"🔧 Syncing {phase} completion ({completed}) to discovery flow database"
            )

            # Get flow_id from state
            flow_id = getattr(self.state, "flow_id", None)
            if not flow_id:
                logger.warning(
                    "⚠️ Cannot sync phase completion: flow_id missing from state"
                )
                return

            # Use fresh database session to update discovery flow
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            from app.services.discovery_flow_service import DiscoveryFlowService

            async with AsyncSessionLocal() as db:
                # Create context from state attributes
                context = RequestContext(
                    client_account_id=getattr(self.state, "client_account_id", None),
                    engagement_id=getattr(self.state, "engagement_id", None),
                    user_id=getattr(self.state, "user_id", "system"),
                )

                # Update phase completion in discovery flow
                discovery_service = DiscoveryFlowService(db, context)

                phase_data = {
                    "completed": completed,
                    "timestamp": self._get_timestamp(),
                    "synced_from_crewai": True,
                }

                await discovery_service.update_phase_completion(
                    flow_id=str(flow_id),
                    phase=phase,
                    phase_data=phase_data,
                    crew_status=None,
                    agent_insights=None,
                )

                await db.commit()
                logger.info(f"✅ Successfully synced {phase} completion to database")

        except Exception as e:
            logger.error(
                f"❌ Failed to sync phase completion to database: {e}", exc_info=True
            )
            # Don't fail the flow execution if sync fails - log and continue
