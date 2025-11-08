"""
AI-Powered Gap Resolution Suggester

Optional LLM-based enhancement for gap resolution recommendations.
Uses multi_model_service for automatic LLM usage tracking (per CLAUDE.md).

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 17
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #7 (LLM tracking)
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from app.models.asset import Asset
from app.models.application_enrichment import ApplicationEnrichment
from app.services.gap_detection.schemas import ComprehensiveGapReport, FieldGap
from app.services.multi_model_service import TaskComplexity, multi_model_service

logger = logging.getLogger(__name__)


class GapResolutionSuggester:
    """
    AI-powered suggester for gap resolution strategies.

    This service provides optional, opt-in LLM-based suggestions for resolving
    identified data gaps. It uses the multi_model_service for automatic tracking
    to llm_usage_logs table.

    Features:
    - Context-aware suggestions based on asset type and environment
    - Prioritized recommendations (quick wins vs complex fixes)
    - Automated data source suggestions
    - Cost-benefit analysis for gap resolution

    Usage:
        suggester = GapResolutionSuggester()
        suggestions = await suggester.suggest_resolution_strategies(
            gap_report=report,
            asset=asset,
            application=app,
            ai_enhance=True,  # Opt-in via query param
        )
    """

    def __init__(self):
        """Initialize the suggester."""
        pass

    async def suggest_resolution_strategies(
        self,
        gap_report: ComprehensiveGapReport,
        asset: Asset,
        application: Optional[ApplicationEnrichment],
        client_account_id: UUID,
        engagement_id: UUID,
    ) -> Dict:
        """
        Generate AI-powered suggestions for resolving gaps.

        Args:
            gap_report: Comprehensive gap analysis report
            asset: Asset entity
            application: Application enrichment (optional)
            client_account_id: Client account UUID
            engagement_id: Engagement UUID

        Returns:
            Dict with ai_suggestions field
        """
        if not gap_report.all_gaps:
            return {"ai_suggestions": {"message": "No gaps identified"}}

        logger.info(
            f"Generating AI suggestions for {len(gap_report.all_gaps)} gaps "
            f"(asset: {asset.name})"
        )

        # Build context for LLM
        context = self._build_gap_context(gap_report, asset, application)

        # Generate suggestions using multi_model_service
        prompt = self._build_suggestion_prompt(context)

        try:
            response = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="gap_resolution_analysis",
                complexity=TaskComplexity.SIMPLE,  # Gemma 3 for quick suggestions
                context={
                    "client_account_id": str(client_account_id),
                    "engagement_id": str(engagement_id),
                    "asset_id": str(asset.id),
                    "asset_name": asset.name,
                },
            )

            # Parse LLM response into structured suggestions
            suggestions = self._parse_llm_response(response, gap_report.all_gaps)

            logger.info(
                f"Generated {len(suggestions.get('strategies', []))} AI suggestions"
            )

            return {"ai_suggestions": suggestions}

        except Exception as e:
            logger.error(f"AI suggestion generation failed: {e}", exc_info=True)
            return {
                "ai_suggestions": {
                    "error": "AI suggestions unavailable",
                    "fallback": self._generate_fallback_suggestions(gap_report),
                }
            }

    def _build_gap_context(
        self,
        gap_report: ComprehensiveGapReport,
        asset: Asset,
        application: Optional[ApplicationEnrichment],
    ) -> Dict:
        """Build context dict for LLM prompt."""
        return {
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "operating_system": asset.operating_system,
            "environment": asset.environment,
            "completeness": gap_report.overall_completeness,
            "assessment_ready": gap_report.assessment_ready,
            "total_gaps": len(gap_report.all_gaps),
            "critical_gaps": len(gap_report.blocking_gaps),
            "gaps_by_field": [
                {
                    "field": gap.field_name,
                    "priority": gap.priority.value,
                    "reason": gap.reason,
                }
                for gap in gap_report.all_gaps[:10]  # Limit to top 10
            ],
            "has_application_data": application is not None,
        }

    def _build_suggestion_prompt(self, context: Dict) -> str:
        """
        Build LLM prompt for gap resolution suggestions.

        The prompt is designed to elicit actionable, specific recommendations.
        """
        return f"""You are a migration expert analyzing data gaps for cloud assessment.

Asset: {context['asset_name']} ({context['asset_type']})
Operating System: {context['operating_system'] or 'Unknown'}
Environment: {context['environment'] or 'Unknown'}
Data Completeness: {context['completeness']:.1%}
Assessment Ready: {'Yes' if context['assessment_ready'] else 'No'}

Identified Gaps ({context['total_gaps']} total, {context['critical_gaps']} critical):
{self._format_gaps_for_prompt(context['gaps_by_field'])}

Task: Provide 3-5 actionable strategies for resolving these gaps, prioritizing:
1. Quick wins (data easily obtainable)
2. High-impact gaps (critical priority)
3. Automated data sources (APIs, scripts, discovery tools)

Format your response as:
1. [QUICK WIN / HIGH IMPACT / AUTOMATED] Strategy description
   - Specific steps to obtain missing data
   - Estimated effort (minutes/hours/days)
   - Data sources or tools to use

Keep suggestions practical and specific to this asset type and environment.
"""

    def _format_gaps_for_prompt(self, gaps: List[Dict]) -> str:
        """Format gaps list for inclusion in prompt."""
        lines = []
        for gap in gaps:
            lines.append(f"- {gap['field']} ({gap['priority']}): {gap['reason']}")
        return "\n".join(lines)

    def _parse_llm_response(self, llm_response: str, gaps: List[FieldGap]) -> Dict:
        """
        Parse LLM response into structured suggestions.

        Extracts strategies, categorizes them, and links to specific gaps.
        """
        strategies = []

        # Simple parsing: split by numbered lines
        lines = llm_response.strip().split("\n")
        current_strategy = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect strategy headers (e.g., "1. [QUICK WIN] ...")
            if line[0].isdigit() and (". [" in line or ". " in line):
                if current_strategy:
                    strategies.append(current_strategy)

                # Extract category and description
                category = "GENERAL"
                if "[QUICK WIN]" in line:
                    category = "QUICK_WIN"
                elif "[HIGH IMPACT]" in line:
                    category = "HIGH_IMPACT"
                elif "[AUTOMATED]" in line:
                    category = "AUTOMATED"

                description = line.split("] ", 1)[-1] if "]" in line else line[3:]

                current_strategy = {
                    "category": category,
                    "description": description,
                    "steps": [],
                    "estimated_effort": "Unknown",
                }
            elif current_strategy and line.startswith("- "):
                # Add step to current strategy
                step_text = line[2:]
                if "Estimated effort:" in step_text or "effort:" in step_text.lower():
                    # Extract effort estimate
                    effort_part = step_text.split("effort:", 1)[-1].strip()
                    current_strategy["estimated_effort"] = effort_part.split(")")[
                        0
                    ].strip("()")
                else:
                    current_strategy["steps"].append(step_text)

        # Add last strategy
        if current_strategy:
            strategies.append(current_strategy)

        return {
            "total_suggestions": len(strategies),
            "strategies": strategies,
            "quick_wins": [s for s in strategies if s["category"] == "QUICK_WIN"],
            "high_impact": [s for s in strategies if s["category"] == "HIGH_IMPACT"],
            "automated": [s for s in strategies if s["category"] == "AUTOMATED"],
        }

    def _generate_fallback_suggestions(
        self, gap_report: ComprehensiveGapReport
    ) -> Dict:
        """
        Generate rule-based fallback suggestions if LLM fails.

        These are deterministic, simple suggestions based on gap patterns.
        """
        strategies = []

        # Strategy 1: Focus on critical gaps first
        if gap_report.blocking_gaps:
            strategies.append(
                {
                    "category": "HIGH_IMPACT",
                    "description": "Prioritize resolving critical gaps that block assessment",
                    "steps": [
                        f"Collect missing field: {gap.field_name}"
                        for gap in gap_report.blocking_gaps[:5]
                    ],
                    "estimated_effort": "2-4 hours",
                }
            )

        # Strategy 2: Use automated discovery tools
        strategies.append(
            {
                "category": "AUTOMATED",
                "description": "Run automated discovery tools to collect system information",
                "steps": [
                    "Use discovery agents to scan assets",
                    "Import results into enrichment tables",
                    "Validate imported data quality",
                ],
                "estimated_effort": "30-60 minutes",
            }
        )

        # Strategy 3: Manual questionnaire
        strategies.append(
            {
                "category": "QUICK_WIN",
                "description": "Send targeted questionnaire to asset owners",
                "steps": [
                    "Generate questionnaire from gap analysis",
                    "Send to asset technical contacts",
                    "Review and import responses",
                ],
                "estimated_effort": "1-2 hours",
            }
        )

        return {
            "total_suggestions": len(strategies),
            "strategies": strategies,
            "note": "Fallback suggestions (AI unavailable)",
        }


__all__ = ["GapResolutionSuggester"]
