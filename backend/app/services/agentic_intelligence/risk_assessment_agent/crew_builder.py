"""
RiskAssessment Agent - Crew Builder Module
Contains methods for creating tasks and crews.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from crewai import Crew, Process, Task

logger = logging.getLogger(__name__)


class CrewBuilderMixin:
    """Mixin for creating tasks and crews"""

    def create_risk_assessment_assessment_task(
        self,
        asset_data: Dict[str, Any],
        historical_patterns: Optional[List[Dict[str, Any]]] = None,
    ) -> Task:
        """Create a task for comprehensive risk_assessment assessment of an asset"""

        asset_summary = {
            "name": asset_data.get("name"),
            "asset_type": asset_data.get("asset_type"),
            "technology_stack": asset_data.get("technology_stack"),
            "environment": asset_data.get("environment"),
            "business_criticality": asset_data.get("business_criticality"),
            "architecture_style": asset_data.get("architecture_style"),
            "integration_complexity": asset_data.get("integration_complexity"),
            "data_volume": asset_data.get("data_volume"),
        }

        # Build historical context if patterns exist
        context_addendum = ""
        if historical_patterns:
            pattern_count = len(historical_patterns)
            context_addendum = f"""

HISTORICAL CONTEXT:
- Found {pattern_count} similar past risk assessments
- Use these patterns to inform your analysis and validate your risk scoring
- Look for common trends and insights from previous risk assessments
- Compare the current asset characteristics with historical patterns
"""

        asset_details_json = json.dumps(asset_summary, indent=2)
        task_description = (
            "Conduct a comprehensive risk_assessment assessment for this asset using your cloud "
            "architecture intelligence and memory tools:\n\n"
            "Asset Details:\n"
            + asset_details_json
            + "\n\n"
            + context_addendum
            + "Complete RiskAssessment Assessment Process including pattern search, technology analysis,"
            " cloud readiness, risk_assessment strategy, containerization potential, scoring (0-100),"
            " pattern discovery, and asset enrichment.\n"
        )

        task = Task(
            description=task_description,
            expected_output="""
            Comprehensive RiskAssessment Assessment Report with cloud readiness score,
            risk_assessment potential, technical architecture assessment, containerization readiness,
            migration effort estimation, new patterns discovered, asset enrichment confirmation,
            and detailed risk_assessment roadmap.
            """,
            agent=self.create_risk_assessment_agent(),
            max_execution_time=50,
        )

        return task

    def create_risk_assessment_crew(
        self,
        asset_data: Dict[str, Any],
        historical_patterns: Optional[List[Dict[str, Any]]] = None,
    ) -> Crew:
        """Create a crew for comprehensive risk_assessment assessment"""

        agent = self.create_risk_assessment_agent()
        task = self.create_risk_assessment_assessment_task(
            asset_data, historical_patterns
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=False,
            max_execution_time=90,
        )

        return crew
