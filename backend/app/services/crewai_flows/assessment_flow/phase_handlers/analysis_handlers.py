"""
Analysis phase handlers for Assessment Flow.

Contains technical debt analysis logic that integrates with
compliance validation results.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.assessment_flow import AssessmentPhase

logger = logging.getLogger(__name__)


class AnalysisHandlers:
    """Mixin class for technical debt and readiness analysis."""

    async def handle_technical_debt_analysis(self, previous_result) -> Dict[str, Any]:
        """
        Phase 3: Analyze technical debt across all applications.
        Evaluate each application component for technical debt.

        ADR-039 Enhancement:
        - Consume compliance validation from architecture_minimums phase
        - Include version compliance failures as tech debt items
        - Persist combined debt analysis to phase_results["tech_debt"]
        """
        logger.info("🔍 Analyzing technical debt")

        try:
            self.flow.state.transition_to_phase(AssessmentPhase.TECH_DEBT_ANALYSIS)
            self.flow.state.update_phase_progress(
                AssessmentPhase.TECH_DEBT_ANALYSIS.value, 10.0
            )

            # ADR-039: Load compliance validation from architecture_minimums phase
            arch_minimums = self.flow.state.metadata.get("architecture_minimums", {})
            compliance_validation = arch_minimums.get("compliance_validation", {})
            app_compliance_results = compliance_validation.get("applications", {})

            tech_debt_results = {}
            total_apps = len(self.flow.state.application_components)

            if total_apps == 0:
                logger.warning("No applications found for technical debt analysis")
                # Reset related state to a coherent empty baseline
                self.flow.state.tech_debt_analysis = {}
                self.flow.state.sixr_decisions = []
                self.flow.state.metadata.setdefault("app_assessments", {})
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

                # ADR-039: Merge version compliance failures into tech debt
                app_compliance = app_compliance_results.get(app_id, {})
                if app_compliance:
                    compliance_issues = app_compliance.get("issues", [])
                    if compliance_issues:
                        # Convert compliance issues to tech debt format
                        version_debt_items = [
                            {
                                "category": "version_compliance",
                                "severity": issue.get("severity", "medium"),
                                "description": (
                                    f"{issue.get('field', 'unknown')}: "
                                    f"{issue.get('current', 'N/A')} below "
                                    f"minimum {issue.get('required', 'N/A')}"
                                ),
                                "remediation": issue.get(
                                    "recommendation", "Upgrade to supported version"
                                ),
                            }
                            for issue in compliance_issues
                        ]
                        debt_analysis["version_compliance_debt"] = version_debt_items
                        debt_analysis["compliance_summary"] = {
                            "compliant": app_compliance.get("compliant", True),
                            "issue_count": len(compliance_issues),
                            "recommendations": app_compliance.get(
                                "recommendations", []
                            ),
                        }
                        # Adjust debt score based on compliance issues
                        if compliance_issues:
                            current_score = debt_analysis.get("overall_score", 5.0)
                            penalty = min(
                                len(compliance_issues) * 0.5, 2.0
                            )  # Cap penalty at 2.0
                            debt_analysis["overall_score"] = max(
                                current_score - penalty, 1.0
                            )

                tech_debt_results[app_id] = debt_analysis

                # Update progress
                progress = 10.0 + (80.0 * (i + 1) / total_apps)
                self.flow.state.update_phase_progress(
                    AssessmentPhase.TECH_DEBT_ANALYSIS.value, progress
                )

            # Store analysis results
            self.flow.state.tech_debt_analysis = tech_debt_results

            # ADR-039: Build tech_debt phase result structure
            non_compliant_count = sum(
                1
                for r in tech_debt_results.values()
                if not r.get("compliance_summary", {}).get("compliant", True)
            )
            total_version_issues = sum(
                len(r.get("version_compliance_debt", []))
                for r in tech_debt_results.values()
            )

            tech_debt_phase_data = {
                "applications": tech_debt_results,
                "summary": {
                    "total_applications": total_apps,
                    "average_debt_score": self._calculate_average_debt_score(
                        tech_debt_results
                    ),
                    "version_compliance_summary": {
                        "non_compliant_applications": non_compliant_count,
                        "total_version_issues": total_version_issues,
                    },
                },
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            # Store in in-memory state for downstream phases
            self.flow.state.metadata["tech_debt"] = tech_debt_phase_data

            # ADR-039: Persist to database phase_results JSONB
            await self._persist_phase_results_to_database(
                phase="tech_debt",
                phase_data=tech_debt_phase_data,
            )

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.TECH_DEBT_ANALYSIS.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Technical debt analysis completed for {total_apps} applications "
                f"({non_compliant_count} with version compliance issues)"
            )

            return {
                "phase": AssessmentPhase.TECH_DEBT_ANALYSIS.value,
                "applications_analyzed": total_apps,
                "average_debt_score": self._calculate_average_debt_score(
                    tech_debt_results
                ),
                "version_compliance_summary": {
                    "non_compliant_applications": non_compliant_count,
                    "total_version_issues": total_version_issues,
                },
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
