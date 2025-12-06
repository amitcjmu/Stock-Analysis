"""
Recommendation and finalization handlers for Assessment Flow.

Contains 6R strategy determination, App on a Page generation,
and assessment finalization logic.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.assessment_flow import (
    AssessmentFlowStatus,
    AssessmentPhase,
)

logger = logging.getLogger(__name__)


class RecommendationHandlers:
    """Mixin class for 6R recommendations and finalization."""

    async def handle_sixr_strategies(self, previous_result) -> Dict[str, Any]:
        """
        Phase 4: Determine 6R strategies for each component.
        Analyze components and recommend migration strategies.

        ADR-039 Enhancement:
        - Load compliance and tech debt context from previous phases
        - Pass compliance_factors to strategy analysis for agentic decisions
        - Include compliance_factors in 6R decision output
        """
        logger.info("⚙️ Determining 6R strategies")

        try:
            from ..strategy_analysis_helper import StrategyAnalysisHelper

            self.flow.state.transition_to_phase(
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            )
            self.flow.state.update_phase_progress(
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES.value, 10.0
            )

            # ADR-039: Load compliance and tech debt context from previous phases
            arch_minimums = self.flow.state.metadata.get("architecture_minimums", {})
            compliance_validation = arch_minimums.get("compliance_validation", {})
            app_compliance_map = compliance_validation.get("applications", {})

            tech_debt_data = self.flow.state.metadata.get("tech_debt", {})
            tech_debt_apps = tech_debt_data.get("applications", {})

            # Initialize strategy helper
            strategy_helper = StrategyAnalysisHelper(self.flow.state)

            # Process each application
            total_components = 0
            processed_components = 0

            for app in self.flow.state.application_components:
                app_id = app.get("application_id")
                app_components = app.get("components", [])
                total_components += len(app_components)

                # ADR-039: Inject compliance and tech debt context into app
                app_compliance = app_compliance_map.get(app_id, {})
                app_tech_debt = tech_debt_apps.get(app_id, {})

                # Build compliance_factors list for 6R reasoning
                compliance_factors = []
                compliance_issues = app_compliance.get("issues", [])
                for issue in compliance_issues:
                    compliance_factors.append(
                        f"{issue.get('field', 'Unknown')}: {issue.get('current', 'N/A')} "
                        f"below minimum {issue.get('required', 'N/A')}"
                    )

                # Add EOL risks from tech debt (if available)
                version_debt = app_tech_debt.get("version_compliance_debt", [])
                for debt_item in version_debt:
                    if debt_item.get("category") == "version_compliance":
                        compliance_factors.append(debt_item.get("description", ""))

                # Create enriched app context for strategy analysis
                enriched_app_context = {
                    **app,
                    "compliance_issues": compliance_issues,
                    "compliance_factors": compliance_factors,
                    "is_compliant": app_compliance.get("compliant", True),
                    "tech_debt_score": app_tech_debt.get("overall_score", 5.0),
                }

                for component in app_components:
                    # Analyze component for 6R strategy with compliance context
                    decision = strategy_helper.analyze_component_for_sixr(
                        component, enriched_app_context
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
            from ..report_generation_helper import ReportGenerationHelper

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
                # Normalize component IDs to handle both raw and app-scoped IDs
                app_component_raw_ids = {
                    c.get("component_id") or c.get("name")
                    for c in app.get("components", [])
                }
                # Include app-scoped IDs (e.g., "app1:component1")
                app_scoped_ids = {
                    f"{app_id}:{rid}" for rid in app_component_raw_ids if rid
                }
                app_component_ids = app_component_raw_ids | app_scoped_ids

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
                "next_phase": AssessmentPhase.FINALIZATION.value,
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
            from ..report_generation_helper import ReportGenerationHelper

            self.flow.state.transition_to_phase(AssessmentPhase.FINALIZATION)
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINALIZATION.value, 25.0
            )

            # Generate overall assessment summary
            report_helper = ReportGenerationHelper(self.flow.state)
            assessment_summary = await report_helper.generate_assessment_summary()

            # Update progress
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINALIZATION.value, 75.0
            )

            # Mark assessment as completed - phase stays FINALIZATION, status changes to COMPLETED
            self.flow.state.status = AssessmentFlowStatus.COMPLETED
            self.flow.state.overall_progress = 100.0

            # Store final summary
            self.flow.state.metadata["assessment_summary"] = assessment_summary
            self.flow.state.metadata["completion_timestamp"] = (
                datetime.utcnow().isoformat()
            )

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.FINALIZATION.value, 100.0
            )

            # Save final state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Assessment finalized successfully for flow {self.flow.flow_id}"
            )

            return {
                "phase": AssessmentPhase.FINALIZATION.value,
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
