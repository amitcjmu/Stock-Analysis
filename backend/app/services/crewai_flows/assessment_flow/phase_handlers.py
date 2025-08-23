"""
Assessment Flow Phase Handlers

This module contains the individual phase handler methods extracted from
UnifiedAssessmentFlow to reduce file size and improve maintainability.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.assessment_flow import (
    AssessmentFlowStatus,
    AssessmentPhase,
)

logger = logging.getLogger(__name__)


class AssessmentPhaseHandlers:
    """Handler methods for individual assessment flow phases."""

    def __init__(self, flow_instance):
        self.flow = flow_instance

    async def handle_initialization(self) -> Dict[str, Any]:
        """
        Phase 1: Initialize the assessment flow.
        Load selected applications and prepare for assessment.
        """
        logger.info(
            f"🚀 Starting assessment initialization for flow {self.flow.flow_id}"
        )

        try:
            # Update phase and progress
            self.flow.state.transition_to_phase(AssessmentPhase.INITIALIZATION)
            self.flow.state.update_phase_progress(
                AssessmentPhase.INITIALIZATION.value, 10.0
            )

            # Load selected applications
            selected_apps = await self.flow.data_helper.load_selected_applications()
            self.flow.state.application_components = selected_apps

            # Load engagement architecture standards
            standards = await self.flow.data_helper.load_engagement_standards()
            if not standards:
                # Initialize default standards if none exist
                standards = await self.flow.data_helper.initialize_default_standards()

            self.flow.state.architecture_standards = standards

            # Update progress
            self.flow.state.update_phase_progress(
                AssessmentPhase.INITIALIZATION.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Assessment initialization completed for {len(selected_apps)} applications"
            )

            return {
                "phase": AssessmentPhase.INITIALIZATION.value,
                "applications_loaded": len(selected_apps),
                "standards_loaded": len(standards),
                "next_phase": AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                "requires_user_input": True,
                "user_input_prompt": "Please review and confirm the architecture standards for this engagement.",
            }

        except Exception as e:
            logger.error(f"❌ Assessment initialization failed: {str(e)}")
            self.flow.state.last_error = str(e)
            self.flow.state.status = AssessmentFlowStatus.ERROR
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    async def handle_architecture_minimums(self, previous_result) -> Dict[str, Any]:
        """
        Phase 2: Capture and validate architecture requirements.
        Allow user to review and modify architecture standards.
        """
        logger.info("📋 Capturing architecture minimums")

        try:
            self.flow.state.transition_to_phase(AssessmentPhase.ARCHITECTURE_MINIMUMS)
            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 25.0
            )

            # Apply any user modifications to architecture standards
            if previous_result and "user_input" in previous_result:
                await self._apply_architecture_modifications(
                    previous_result["user_input"]
                )

            # Validate architecture standards completeness
            standards_validation = self._validate_architecture_standards()

            # Update progress
            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info("✅ Architecture minimums captured successfully")

            return {
                "phase": AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                "standards_count": len(self.flow.state.architecture_standards),
                "validation_results": standards_validation,
                "next_phase": AssessmentPhase.TECH_DEBT_ANALYSIS.value,
                "requires_user_input": False,
            }

        except Exception as e:
            logger.error(f"❌ Architecture minimums capture failed: {str(e)}")
            self.flow.state.last_error = str(e)
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    async def handle_technical_debt_analysis(self, previous_result) -> Dict[str, Any]:
        """
        Phase 3: Analyze technical debt across all applications.
        Evaluate each application component for technical debt.
        """
        logger.info("🔍 Analyzing technical debt")

        try:
            self.flow.state.transition_to_phase(AssessmentPhase.TECH_DEBT_ANALYSIS)
            self.flow.state.update_phase_progress(
                AssessmentPhase.TECH_DEBT_ANALYSIS.value, 10.0
            )

            tech_debt_results = {}
            total_apps = len(self.flow.state.application_components)

            if total_apps == 0:
                logger.warning("No applications found for technical debt analysis")
                self.flow.state.tech_debt_analysis = {}
                self.flow.state.update_phase_progress(
                    AssessmentPhase.TECH_DEBT_ANALYSIS.value, 100.0
                )
                await self.flow.flow_state_manager.save_state(
                    self.flow.flow_id, self.flow.state.to_dict()
                )
                return {
                    "phase": AssessmentPhase.TECH_DEBT_ANALYSIS.value,
                    "applications_analyzed": 0,
                    "average_debt_score": 0.0,
                    "next_phase": AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value,
                    "requires_user_input": False,
                    "user_input_prompt": "No applications to analyze.",
                }

            for i, app in enumerate(self.flow.state.application_components):
                app_id = app.get("application_id")
                app_name = app.get("application_name", f"Application {app_id}")

                logger.info(f"Analyzing tech debt for {app_name} ({i+1}/{total_apps})")

                # Perform technical debt analysis
                debt_analysis = await self._analyze_app_technical_debt(app)
                tech_debt_results[app_id] = debt_analysis

                # Update progress
                progress = 10.0 + (80.0 * (i + 1) / total_apps)
                self.flow.state.update_phase_progress(
                    AssessmentPhase.TECH_DEBT_ANALYSIS.value, progress
                )

            # Store analysis results
            self.flow.state.tech_debt_analysis = tech_debt_results

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.TECH_DEBT_ANALYSIS.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Technical debt analysis completed for {total_apps} applications"
            )

            return {
                "phase": AssessmentPhase.TECH_DEBT_ANALYSIS.value,
                "applications_analyzed": total_apps,
                "average_debt_score": self._calculate_average_debt_score(
                    tech_debt_results
                ),
                "next_phase": AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value,
                "requires_user_input": True,
                "user_input_prompt": "Please review the technical debt analysis results.",
            }

        except Exception as e:
            logger.error(f"❌ Technical debt analysis failed: {str(e)}")
            self.flow.state.last_error = str(e)
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    async def handle_sixr_strategies(self, previous_result) -> Dict[str, Any]:
        """
        Phase 4: Determine 6R strategies for each component.
        Analyze components and recommend migration strategies.
        """
        logger.info("⚙️ Determining 6R strategies")

        try:
            from .strategy_analysis_helper import StrategyAnalysisHelper

            self.flow.state.transition_to_phase(
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            )
            self.flow.state.update_phase_progress(
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value, 10.0
            )

            # Initialize strategy helper
            strategy_helper = StrategyAnalysisHelper(self.flow.state)

            # Process each application
            total_components = 0
            processed_components = 0

            for app in self.flow.state.application_components:
                app_components = app.get("components", [])
                total_components += len(app_components)

                for component in app_components:
                    # Analyze component for 6R strategy
                    decision = strategy_helper.analyze_component_for_sixr(
                        component, app
                    )
                    self.flow.state.sixr_decisions.append(decision)

                    processed_components += 1
                    progress = 10.0 + (
                        80.0 * processed_components / max(total_components, 1)
                    )
                    self.flow.state.update_phase_progress(
                        AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value, progress
                    )

            # Validate strategy coherence
            validation_results = strategy_helper.validate_strategy_coherence()

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ 6R strategies determined for {len(self.flow.state.sixr_decisions)} components"
            )

            return {
                "phase": AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value,
                "components_analyzed": len(self.flow.state.sixr_decisions),
                "strategy_distribution": strategy_helper.get_strategy_distribution(),
                "validation_results": validation_results,
                "next_phase": AssessmentPhase.APP_ON_PAGE_GENERATION.value,
                "requires_user_input": True,
                "user_input_prompt": "Please review the 6R strategy recommendations.",
            }

        except Exception as e:
            logger.error(f"❌ 6R strategy determination failed: {str(e)}")
            self.flow.state.last_error = str(e)
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    async def handle_app_on_page_generation(self, previous_result) -> Dict[str, Any]:
        """
        Phase 5: Generate comprehensive "App on a Page" assessments.
        Create detailed assessment reports for each application.
        """
        logger.info("📊 Generating App on a Page assessments")

        try:
            from .report_generation_helper import ReportGenerationHelper

            self.flow.state.transition_to_phase(AssessmentPhase.APP_ON_PAGE_GENERATION)
            self.flow.state.update_phase_progress(
                AssessmentPhase.APP_ON_PAGE_GENERATION.value, 10.0
            )

            # Initialize report helper
            report_helper = ReportGenerationHelper(self.flow.state)

            app_assessments = {}
            total_apps = len(self.flow.state.application_components)

            for i, app in enumerate(self.flow.state.application_components):
                app_id = app.get("application_id")

                # Get related data for this application
                app_tech_debt = self.flow.state.tech_debt_analysis.get(app_id, {})

                # Filter decisions to only those belonging to this app's components
                app_component_ids = {
                    c.get("component_id") or c.get("name")
                    for c in app.get("components", [])
                }
                app_sixr_decisions = [
                    decision.to_dict()
                    for decision in self.flow.state.sixr_decisions
                    if decision.component_id in app_component_ids
                ]

                # Generate App on a Page
                app_assessment = await report_helper.generate_app_on_page_data(
                    app, app_tech_debt, app_sixr_decisions
                )
                app_assessments[app_id] = app_assessment

                # Update progress
                progress = 10.0 + (80.0 * (i + 1) / total_apps)
                self.flow.state.update_phase_progress(
                    AssessmentPhase.APP_ON_PAGE_GENERATION.value, progress
                )

            # Store assessments
            self.flow.state.metadata["app_assessments"] = app_assessments

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.APP_ON_PAGE_GENERATION.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(f"✅ App on a Page generated for {total_apps} applications")

            return {
                "phase": AssessmentPhase.APP_ON_PAGE_GENERATION.value,
                "assessments_generated": total_apps,
                "next_phase": AssessmentPhase.FINAL_REPORT_GENERATION.value,
                "requires_user_input": False,
                "app_assessments": list(app_assessments.keys()),
            }

        except Exception as e:
            logger.error(f"❌ App on a Page generation failed: {str(e)}")
            self.flow.state.last_error = str(e)
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    async def handle_finalization(self, previous_result) -> Dict[str, Any]:
        """
        Phase 6: Finalize assessment and prepare for planning.
        Generate overall summary and mark flow as completed.
        """
        logger.info("🎯 Finalizing assessment")

        try:
            from .report_generation_helper import ReportGenerationHelper

            self.flow.state.transition_to_phase(AssessmentPhase.FINAL_REPORT_GENERATION)
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINAL_REPORT_GENERATION.value, 25.0
            )

            # Generate overall assessment summary
            report_helper = ReportGenerationHelper(self.flow.state)
            assessment_summary = await report_helper.generate_assessment_summary()

            # Update progress
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINAL_REPORT_GENERATION.value, 75.0
            )

            # Mark assessment as completed
            self.flow.state.transition_to_phase(AssessmentPhase.COMPLETED)
            self.flow.state.status = AssessmentFlowStatus.COMPLETED
            self.flow.state.overall_progress = 100.0

            # Store final summary
            self.flow.state.metadata["assessment_summary"] = assessment_summary
            self.flow.state.metadata["completion_timestamp"] = (
                datetime.utcnow().isoformat()
            )

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINAL_REPORT_GENERATION.value, 100.0
            )

            # Save final state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Assessment finalized successfully for flow {self.flow.flow_id}"
            )

            return {
                "phase": AssessmentPhase.COMPLETED.value,
                "status": AssessmentFlowStatus.COMPLETED.value,
                "overall_progress": 100.0,
                "applications_assessed": len(self.flow.state.application_components),
                "sixr_decisions_count": len(self.flow.state.sixr_decisions),
                "assessment_summary": assessment_summary,
                "ready_for_planning": True,
            }

        except Exception as e:
            logger.error(f"❌ Assessment finalization failed: {str(e)}")
            self.flow.state.last_error = str(e)
            self.flow.state.status = AssessmentFlowStatus.ERROR
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise

    # Helper methods

    async def _analyze_app_technical_debt(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical debt for a single application."""
        # TODO: Placeholder implementation - replace with actual tech debt analysis
        # This should integrate with code analysis tools and metrics collection
        return {
            "overall_score": 6.5,
            "categories": {"maintainability": 7.0, "security": 6.0, "performance": 6.5},
            "critical_issues": [
                "Legacy authentication system",
                "Outdated dependencies",
            ],
            "remediation_effort": "medium",
        }

    def _validate_architecture_standards(self) -> Dict[str, Any]:
        """Validate architecture standards completeness."""
        # TODO: Placeholder implementation - replace with actual validation logic
        # This should check completeness of standards against requirements
        return {"is_valid": True, "missing_standards": [], "recommendations": []}

    def _calculate_average_debt_score(self, tech_debt_results: Dict[str, Any]) -> float:
        """Calculate average technical debt score across applications."""
        if not tech_debt_results:
            return 0.0

        scores = [
            result.get("overall_score", 0.0) for result in tech_debt_results.values()
        ]
        return sum(scores) / len(scores)

    async def _apply_architecture_modifications(self, user_input: Dict[str, Any]):
        """Apply user modifications to architecture standards."""
        # TODO: Placeholder implementation - replace with actual modification logic
        # This should apply user-provided modifications to architecture standards
        # and validate the changes before committing
        pass
