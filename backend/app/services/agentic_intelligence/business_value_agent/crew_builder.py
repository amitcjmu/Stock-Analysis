"""
Business Value Agent - Crew Builder Module
Contains methods for creating tasks and crews.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from crewai import Crew, Process, Task

logger = logging.getLogger(__name__)


class CrewBuilderMixin:
    """Mixin for creating tasks and crews"""

    def create_business_value_analysis_task(
        self,
        asset_data: Dict[str, Any],
        historical_patterns: Optional[List[Dict[str, Any]]] = None,
    ) -> Task:
        """Create a task for analyzing business value of a specific asset"""

        asset_summary = {
            "name": asset_data.get("name"),
            "asset_type": asset_data.get("asset_type"),
            "technology_stack": asset_data.get("technology_stack"),
            "environment": asset_data.get("environment"),
            "cpu_utilization_percent": asset_data.get("cpu_utilization_percent"),
            "business_criticality": asset_data.get("business_criticality"),
        }

        # Build historical context if patterns exist
        context_addendum = ""
        if historical_patterns:
            pattern_count = len(historical_patterns)
            context_addendum = f"""

HISTORICAL CONTEXT:
- Found {pattern_count} similar past business value assessments
- Use these patterns to inform your analysis and validate your scoring
- Look for common trends and insights from previous work
- Compare the current asset characteristics with historical patterns
"""

        # This is not SQL - it's a task description for CrewAI agent
        asset_details_json = json.dumps(asset_summary, indent=2)
        task_description = (  # nosec B608
            "Analyze the business value of this asset using your agentic intelligence and memory tools:\n\n"
            "Asset Details:\n"
            + asset_details_json
            + "\n\n"  # nosec B608
            + context_addendum
            + "Complete Analysis Process:\n\n"
            "1. SEARCH FOR PATTERNS:\n"
            "   Use your pattern search tool to find relevant business value patterns from previous analyses.\n"
            "   Search for patterns related to: database business value, production systems, "
            "technology stack analysis.\n\n"
            "2. GATHER EVIDENCE:\n"
            "   Use your asset query tool to examine similar assets and gather comparative evidence.\n"
            "   Look for assets with similar characteristics to understand value patterns.\n\n"
            "3. ANALYZE BUSINESS VALUE:\n"
            "   Based on the evidence and patterns, analyze:\n"
            "   - Business criticality indicators (production environment, high usage, etc.)\n"
            "   - Technology value indicators (enterprise systems, databases, etc.)\n"
            "   - Usage patterns that suggest business importance\n"
            "   - Integration complexity that adds business value\n\n"
            "4. CALCULATE SCORE:\n"
            "   Provide a business value score from 1-10 where:\n"
            "   - 1-3: Low business value (test systems, non-critical applications)\n"
            "   - 4-6: Medium business value (important but replaceable systems)\n"
            "   - 7-8: High business value (critical business operations)\n"
            "   - 9-10: Very high business value (core business systems, revenue-generating)\n\n"
            "5. DISCOVER NEW PATTERNS:\n"
            "   If you identify a new business value pattern during your analysis, use your\n"
            "   pattern recording tool to save it for future analyses.\n\n"
            "6. ENRICH THE ASSET:\n"
            "   Use your asset enrichment tool to update the asset with:\n"
            "   - Your business value score\n"
            "   - Your detailed reasoning\n"
            "   - Confidence level in your analysis\n\n"
            "Provide your final analysis in this format:\n"
            "Business Value Score: [1-10]\n"
            "Confidence Level: [High/Medium/Low]\n"
            "Primary Reasoning: [Your main reasoning for the score]\n"
            "Evidence Found: [Key evidence that supported your decision]\n"
            "Patterns Applied: [Any patterns you used from memory]\n"
            "New Patterns Discovered: [Any new patterns you identified]\n"
            "Recommendations: [Specific recommendations based on the business value]\n"
        )

        task = Task(
            description=task_description,
            expected_output="""
            Business Value Analysis Report with:
            - Business Value Score (1-10)
            - Confidence Level assessment
            - Detailed reasoning explaining the score
            - Evidence summary from pattern search and asset analysis
            - New patterns discovered and recorded
            - Asset enrichment confirmation
            - Specific recommendations for this asset
            """,
            agent=self.create_business_value_agent(),  # Fix: Assign agent to task
            max_execution_time=50,
        )

        return task

    def create_business_value_crew(
        self,
        asset_data: Dict[str, Any],
        historical_patterns: Optional[List[Dict[str, Any]]] = None,
    ) -> Crew:
        """Create a crew for business value analysis"""

        agent = self.create_business_value_agent()
        task = self.create_business_value_analysis_task(asset_data, historical_patterns)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
            max_execution_time=90,
        )

        return crew
