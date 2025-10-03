"""
Modernization Agent - Crew Builder Module
Contains methods for creating tasks and crews.
"""

import json
import logging
from typing import Any, Dict

from crewai import Crew, Process, Task

logger = logging.getLogger(__name__)


class CrewBuilderMixin:
    """Mixin for creating tasks and crews"""

    def create_modernization_assessment_task(self, asset_data: Dict[str, Any]) -> Task:
        """Create a task for comprehensive modernization assessment of an asset"""

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

        asset_details_json = json.dumps(asset_summary, indent=2)
        task_description = (
            "Conduct a comprehensive modernization assessment for this asset using your cloud "
            "architecture intelligence and memory tools:\n\n"
            "Asset Details:\n" + asset_details_json + "\n\n"
            "Complete Modernization Assessment Process including pattern search, technology analysis,"
            " cloud readiness, modernization strategy, containerization potential, scoring (0-100),"
            " pattern discovery, and asset enrichment.\n"
        )

        task = Task(
            description=task_description,
            expected_output="""
            Comprehensive Modernization Assessment Report with cloud readiness score,
            modernization potential, technical architecture assessment, containerization readiness,
            migration effort estimation, new patterns discovered, asset enrichment confirmation,
            and detailed modernization roadmap.
            """,
            agent=self.create_modernization_agent(),
            max_execution_time=50,
        )

        return task

    def create_modernization_crew(self, asset_data: Dict[str, Any]) -> Crew:
        """Create a crew for comprehensive modernization assessment"""

        agent = self.create_modernization_agent()
        task = self.create_modernization_assessment_task(asset_data)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=False,
            max_execution_time=90,
        )

        return crew
