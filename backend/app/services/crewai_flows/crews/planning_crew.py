"""
Planning Crew - Migration Wave Planning and Resource Allocation

Orchestrates 4 specialized planning agents for comprehensive migration planning:
1. Wave Planning Specialist - Dependency-based wave sequencing
2. Resource Allocation Specialist - AI-driven resource recommendations
3. Timeline Generation Specialist - Critical path and Gantt chart creation
4. Cost Estimation Specialist - Multi-dimensional cost analysis

Architecture:
- Per ADR-024: CrewAI memory DISABLED (memory=False)
- Uses TenantMemoryManager for enterprise agent learning
- Follows crew_config.py performance optimizations
- Integration with PlanningFlowService via service layer

Related Issues:
- #689 (Wave Planning Flow)
- #690 (Resource Allocation AI)
- #695 (Timeline Generation)

ADRs:
- ADR-024: TenantMemoryManager (CrewAI memory DISABLED)
- ADR-015: Persistent Multi-Tenant Agent Architecture
- ADR-012: Flow Status Management Separation
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from crewai import Agent, Task

from app.core.logging import get_logger
from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)

logger = get_logger(__name__)


class PlanningCrew:
    """
    Orchestrates planning flow CrewAI agents.

    Coordinates 4 specialized agents to produce comprehensive migration plans:
    - Wave sequencing based on dependencies
    - AI-driven resource allocations
    - Timeline generation with critical path
    - Multi-dimensional cost estimation
    """

    def __init__(self, crewai_service=None):
        """
        Initialize planning crew with YAML configuration.

        Args:
            crewai_service: Optional CrewAI service instance for LLM access
        """
        self.crewai_service = crewai_service
        self.config_path = Path(__file__).parent / "config"

        # Load agent and task configurations from YAML
        self.agents_config = self._load_yaml("planning_agents.yaml")
        self.tasks_config = self._load_yaml("planning_tasks.yaml")

        # Get LLM configuration (per ADR-024: use configured DeepInfra LLM)
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ Planning Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = (
                getattr(crewai_service, "llm", None) if crewai_service else None
            )

        logger.info("✅ Planning Crew initialized with 4 specialized agents")

    def _load_yaml(self, filename: str) -> Dict:
        """
        Load YAML configuration file.

        Args:
            filename: YAML file name in config directory

        Returns:
            Parsed YAML dictionary

        Raises:
            FileNotFoundError: If YAML file not found
        """
        yaml_path = self.config_path / filename
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path) as f:
            return yaml.safe_load(f)

    def execute_wave_planning(
        self,
        client_account_id: int,
        engagement_id: int,
        selected_applications: List[Dict[str, Any]],
        planning_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute wave planning phase using WavePlanningSpecialist agent.

        Business Logic:
        1. Analyze dependency graph to identify critical paths
        2. Group applications into waves based on dependency chains
        3. Optimize wave sizes for resource utilization
        4. Minimize cross-wave dependencies
        5. Account for business criticality

        Args:
            client_account_id: Tenant client account ID
            engagement_id: Tenant engagement ID
            selected_applications: List of application dictionaries with metadata
            planning_config: Planning configuration (max_wave_size, etc.)

        Returns:
            Dict containing wave plan:
            {
                "waves": [
                    {
                        "wave_number": 1,
                        "wave_name": "Wave 1 - Quick Wins",
                        "applications": [UUID, ...],
                        "dependencies": [],
                        "estimated_duration_days": 90
                    }
                ],
                "total_waves": int,
                "planning_metadata": {...}
            }

        Raises:
            ValueError: If configuration invalid or agent execution fails
        """
        try:
            logger.info(
                f"🎯 Executing wave planning for {len(selected_applications)} applications "
                f"(Client: {client_account_id}, Engagement: {engagement_id})"
            )

            # Create wave planning agent from YAML config
            agent = self._create_agent("wave_planning_specialist")

            # Prepare context for task description formatting
            task_context = {
                "dependency_graph": self._build_dependency_graph(selected_applications),
                "applications": selected_applications,
                "constraints": planning_config.get("constraints", {}),
                "max_wave_size": planning_config.get("max_apps_per_wave", 5),
                "min_wave_size": planning_config.get("min_apps_per_wave", 1),
                "criticality_levels": planning_config.get("criticality_levels", {}),
                "compliance_constraints": planning_config.get(
                    "compliance_constraints", {}
                ),
            }

            # Create task from YAML config
            task = self._create_task(
                "wave_planning_task", agent=agent, context=task_context
            )

            # Execute crew (CRITICAL: memory=False per ADR-024)
            crew = create_crew(
                agents=[agent],
                tasks=[task],
                memory=False,  # Per ADR-024: Use TenantMemoryManager instead
                verbose=True,
            )

            result = crew.kickoff()

            # Parse and structure result
            wave_plan = self._parse_wave_plan_result(result, selected_applications)

            logger.info(
                f"✅ Wave planning completed: {wave_plan['total_waves']} waves generated"
            )

            return wave_plan

        except Exception as e:
            logger.error(f"❌ Wave planning execution failed: {e}", exc_info=True)
            raise ValueError(f"Wave planning failed: {str(e)}")

    def execute_resource_allocation(
        self,
        client_account_id: int,
        engagement_id: int,
        wave_plan: Dict[str, Any],
        resource_pools: List[Dict[str, Any]],
        planning_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute resource allocation phase using ResourceAllocationSpecialist.

        Business Logic:
        1. Analyze application complexity per wave
        2. Calculate role-based resource requirements
        3. Estimate effort in person-hours per role
        4. Optimize resource leveling across waves
        5. Generate cost estimates

        Args:
            client_account_id: Tenant client account ID
            engagement_id: Tenant engagement ID
            wave_plan: Output from wave planning phase
            resource_pools: Available resource pools with rates
            planning_config: Planning configuration

        Returns:
            Dict containing resource allocations:
            {
                "allocations": [
                    {
                        "wave_number": 1,
                        "resources": [
                            {
                                "role_name": "Cloud Architect",
                                "allocated_hours": 160,
                                "hourly_rate": 150.0,
                                "estimated_cost": 24000.0
                            }
                        ]
                    }
                ],
                "skill_gaps": [...],
                "total_cost_estimate": 125000.0
            }

        Raises:
            ValueError: If wave plan invalid or agent execution fails
        """
        try:
            logger.info(
                f"💼 Executing resource allocation for {wave_plan.get('total_waves', 0)} waves"
            )

            # Create resource allocation agent
            agent = self._create_agent("resource_allocation_specialist")

            # Prepare task context
            task_context = {
                "wave_plan": wave_plan,
                "complexity_scores": self._calculate_complexity_scores(wave_plan),
                "historical_data": {},  # TODO: Integrate with TenantMemoryManager
                "roles_and_rates": resource_pools,
                "required_roles": planning_config.get(
                    "required_roles",
                    ["Solution Architect", "Cloud Engineer", "QA Engineer"],
                ),
                "hourly_rates": self._extract_hourly_rates(resource_pools),
                "availability": planning_config.get("resource_availability", {}),
                "budget_limit": planning_config.get("budget_limit", 0),
            }

            # Create task
            task = self._create_task(
                "resource_allocation_task", agent=agent, context=task_context
            )

            # Execute crew (memory=False per ADR-024)
            crew = create_crew(
                agents=[agent],
                tasks=[task],
                memory=False,
                verbose=True,
            )

            result = crew.kickoff()

            # Parse result
            allocation_result = self._parse_resource_allocation_result(
                result, wave_plan
            )

            logger.info(
                f"✅ Resource allocation completed: ${allocation_result.get('total_cost_estimate', 0):,.2f}"
            )

            return allocation_result

        except Exception as e:
            logger.error(f"❌ Resource allocation failed: {e}", exc_info=True)
            raise ValueError(f"Resource allocation failed: {str(e)}")

    def execute_timeline_generation(
        self,
        client_account_id: int,
        engagement_id: int,
        wave_plan: Dict[str, Any],
        resource_allocation: Dict[str, Any],
        planning_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute timeline generation phase using TimelineGenerationSpecialist.

        Business Logic:
        1. Calculate wave durations based on workload and capacity
        2. Sequence waves based on dependencies
        3. Identify critical path
        4. Add buffer time for risks
        5. Generate calendar-based schedule

        Args:
            client_account_id: Tenant client account ID
            engagement_id: Tenant engagement ID
            wave_plan: Output from wave planning phase
            resource_allocation: Output from resource allocation phase
            planning_config: Planning configuration with start date

        Returns:
            Dict containing timeline data:
            {
                "overall_start_date": "2025-01-01",
                "overall_end_date": "2025-12-31",
                "phases": [...],
                "milestones": [...],
                "critical_path": [...],
                "optimization_score": 0.85
            }

        Raises:
            ValueError: If prerequisites invalid or agent execution fails
        """
        try:
            logger.info("📅 Executing timeline generation")

            # Create timeline generation agent
            agent = self._create_agent("timeline_generation_specialist")

            # Prepare task context
            task_context = {
                "wave_plan": wave_plan,
                "resource_allocations": resource_allocation,
                "project_start_date": planning_config.get("start_date", "2025-01-01"),
                "timeline_constraints": planning_config.get("timeline_constraints", {}),
                "working_days": planning_config.get("working_days_per_week", 5),
                "hours_per_day": planning_config.get("hours_per_working_day", 8),
                "risk_buffer": planning_config.get("risk_buffer_percentage", 20),
                "milestone_frequency": planning_config.get(
                    "milestone_frequency", "bi-weekly"
                ),
            }

            # Create task
            task = self._create_task(
                "timeline_generation_task", agent=agent, context=task_context
            )

            # Execute crew (memory=False per ADR-024)
            crew = create_crew(
                agents=[agent],
                tasks=[task],
                memory=False,
                verbose=True,
            )

            result = crew.kickoff()

            # Parse result
            timeline_result = self._parse_timeline_result(result)

            logger.info("✅ Timeline generation completed")

            return timeline_result

        except Exception as e:
            logger.error(f"❌ Timeline generation failed: {e}", exc_info=True)
            raise ValueError(f"Timeline generation failed: {str(e)}")

    def execute_cost_estimation(
        self,
        client_account_id: int,
        engagement_id: int,
        wave_plan: Dict[str, Any],
        resource_allocation: Dict[str, Any],
        timeline: Dict[str, Any],
        planning_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute cost estimation phase using CostEstimationSpecialist.

        Business Logic:
        1. Calculate labor costs from resource allocations
        2. Estimate infrastructure costs
        3. Add risk contingency
        4. Generate cost breakdown by wave and category

        Args:
            client_account_id: Tenant client account ID
            engagement_id: Tenant engagement ID
            wave_plan: Output from wave planning phase
            resource_allocation: Output from resource allocation phase
            timeline: Output from timeline generation phase
            planning_config: Planning configuration

        Returns:
            Dict containing cost estimates:
            {
                "labor_costs": {...},
                "infrastructure_costs": {...},
                "risk_contingency": float,
                "total_estimated_cost": float,
                "cost_breakdown_by_wave": [...]
            }

        Raises:
            ValueError: If prerequisites invalid or agent execution fails
        """
        try:
            logger.info("💰 Executing cost estimation")

            # Create cost estimation agent
            agent = self._create_agent("cost_estimation_specialist")

            # Prepare task context
            task_context = {
                "resource_allocations": resource_allocation,
                "hourly_rates": self._extract_hourly_rates_from_allocation(
                    resource_allocation
                ),
                "infrastructure": planning_config.get(
                    "infrastructure_requirements", {}
                ),
                "complexity_scores": self._calculate_complexity_scores(wave_plan),
                "rate_multiplier": planning_config.get("labor_rate_multiplier", 1.15),
                "infra_costs": planning_config.get("infrastructure_cost_models", {}),
                "tool_costs": planning_config.get("tooling_licenses", {}),
                "contingency": planning_config.get("contingency_percentage", 15.0),
            }

            # Create task
            task = self._create_task(
                "cost_estimation_task", agent=agent, context=task_context
            )

            # Execute crew (memory=False per ADR-024)
            crew = create_crew(
                agents=[agent],
                tasks=[task],
                memory=False,
                verbose=True,
            )

            result = crew.kickoff()

            # Parse result
            cost_result = self._parse_cost_estimation_result(result)

            logger.info(
                f"✅ Cost estimation completed: ${cost_result.get('total_estimated_cost', 0):,.2f}"
            )

            return cost_result

        except Exception as e:
            logger.error(f"❌ Cost estimation failed: {e}", exc_info=True)
            raise ValueError(f"Cost estimation failed: {str(e)}")

    def execute_planning_synthesis(
        self,
        client_account_id: int,
        engagement_id: int,
        wave_plan: Dict[str, Any],
        resource_allocation: Dict[str, Any],
        timeline: Dict[str, Any],
        costs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute synthesis phase - aggregate all planning results.

        Business Logic:
        1. Integrate all planning outputs
        2. Validate consistency across dimensions
        3. Generate executive summary
        4. Identify optimization opportunities

        Args:
            client_account_id: Tenant client account ID
            engagement_id: Tenant engagement ID
            wave_plan: Wave planning output
            resource_allocation: Resource allocation output
            timeline: Timeline generation output
            costs: Cost estimation output

        Returns:
            Dict containing comprehensive planning synthesis

        Raises:
            ValueError: If any input invalid or synthesis fails
        """
        try:
            logger.info("📊 Executing planning synthesis")

            # For synthesis, we don't necessarily need a dedicated agent
            # The synthesis can be done programmatically by aggregating results
            synthesis_result = {
                "executive_summary": {
                    "total_applications": len(wave_plan.get("waves", [])),
                    "total_waves": wave_plan.get("total_waves", 0),
                    "total_duration_days": self._calculate_duration_days(timeline),
                    "total_cost": costs.get("total_estimated_cost", 0.0),
                    "resource_count": len(resource_allocation.get("allocations", [])),
                },
                "wave_plan": wave_plan,
                "resource_allocation": resource_allocation,
                "timeline": timeline,
                "cost_estimation": costs,
                "recommendations": self._generate_recommendations(
                    wave_plan, resource_allocation, timeline, costs
                ),
                "key_metrics": {
                    "avg_cost_per_wave": (
                        costs.get("total_estimated_cost", 0.0)
                        / wave_plan.get("total_waves", 1)
                    ),
                    "avg_duration_per_wave": (
                        self._calculate_duration_days(timeline)
                        / wave_plan.get("total_waves", 1)
                    ),
                },
            }

            logger.info("✅ Planning synthesis completed")

            return synthesis_result

        except Exception as e:
            logger.error(f"❌ Planning synthesis failed: {e}", exc_info=True)
            raise ValueError(f"Planning synthesis failed: {str(e)}")

    # ========================================
    # HELPER METHODS
    # ========================================

    def _create_agent(self, agent_id: str) -> Agent:
        """
        Create agent from YAML configuration.

        Args:
            agent_id: Agent identifier in YAML config

        Returns:
            Configured Agent instance

        Raises:
            KeyError: If agent_id not found in configuration
        """
        if agent_id not in self.agents_config:
            raise KeyError(f"Agent '{agent_id}' not found in planning_agents.yaml")

        agent_config = self.agents_config[agent_id]

        return create_agent(
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            llm=self.llm_model,
            memory=False,  # Per ADR-024: Use TenantMemoryManager instead
            verbose=True,
            allow_delegation=False,  # Per crew_config.py: No delegation for performance
        )

    def _create_task(self, task_id: str, agent: Agent, context: Dict[str, Any]) -> Task:
        """
        Create task from YAML configuration with context injection.

        Args:
            task_id: Task identifier in YAML config
            agent: Agent assigned to task
            context: Context dictionary for description formatting

        Returns:
            Configured Task instance

        Raises:
            KeyError: If task_id not found in configuration
        """
        if task_id not in self.tasks_config:
            raise KeyError(f"Task '{task_id}' not found in planning_tasks.yaml")

        task_config = self.tasks_config[task_id]

        # Format description with context (handle missing keys gracefully)
        try:
            description = task_config["description"].format(**context)
        except KeyError as e:
            logger.warning(
                f"Missing context key {e} for task {task_id}, using unformatted description"
            )
            description = task_config["description"]

        return create_task(
            description=description,
            agent=agent,
            expected_output=task_config["expected_output"],
        )

    def _build_dependency_graph(
        self, selected_applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build dependency graph from selected applications.

        Args:
            selected_applications: List of application dictionaries

        Returns:
            Dependency graph structure
        """
        # Placeholder implementation - would integrate with dependency analysis service
        return {
            "nodes": [app.get("id") for app in selected_applications],
            "edges": [],  # Would contain actual dependencies
        }

    def _calculate_complexity_scores(
        self, wave_plan: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate complexity scores for applications.

        Args:
            wave_plan: Wave plan with application assignments

        Returns:
            Dictionary mapping application IDs to complexity scores
        """
        # Placeholder - would use actual complexity analysis
        complexity_scores = {}
        for wave in wave_plan.get("waves", []):
            for app_id in wave.get("applications", []):
                complexity_scores[str(app_id)] = 0.5  # Default medium complexity

        return complexity_scores

    def _extract_hourly_rates(
        self, resource_pools: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract hourly rates from resource pools."""
        rates = {}
        for pool in resource_pools:
            role = pool.get("role_name", "")
            rate = pool.get("hourly_rate", 100.0)
            if role:
                rates[role] = rate
        return rates

    def _extract_hourly_rates_from_allocation(
        self, resource_allocation: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract hourly rates from resource allocation data."""
        rates = {}
        for alloc in resource_allocation.get("allocations", []):
            for resource in alloc.get("resources", []):
                role = resource.get("role_name", "")
                rate = resource.get("hourly_rate", 100.0)
                if role:
                    rates[role] = rate
        return rates

    def _calculate_duration_days(self, timeline: Dict[str, Any]) -> int:
        """Calculate total duration in days from timeline data."""
        # Placeholder - would parse actual dates
        return 365

    def _generate_recommendations(
        self,
        wave_plan: Dict[str, Any],
        resource_allocation: Dict[str, Any],
        timeline: Dict[str, Any],
        costs: Dict[str, Any],
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Wave optimization
        if wave_plan.get("total_waves", 0) > 5:
            recommendations.append(
                "Consider parallelizing some waves to reduce total timeline"
            )

        # Cost optimization
        if costs.get("total_estimated_cost", 0) > 500000:
            recommendations.append(
                "Review resource allocations for potential cost savings opportunities"
            )

        # Resource optimization
        skill_gaps = resource_allocation.get("skill_gaps", [])
        if skill_gaps:
            recommendations.append(
                f"Address {len(skill_gaps)} identified skill gaps through training or hiring"
            )

        return recommendations

    # ========================================
    # RESULT PARSING METHODS
    # ========================================

    def _parse_wave_plan_result(
        self, result: Any, selected_applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse crew result into structured wave plan.

        Args:
            result: Raw crew execution result
            selected_applications: Original application list

        Returns:
            Structured wave plan dictionary
        """
        # Placeholder implementation - would parse actual agent output
        # For now, create a simple single-wave plan
        return {
            "waves": [
                {
                    "wave_number": 1,
                    "wave_name": "Wave 1 - Initial Migration",
                    "applications": [app.get("id") for app in selected_applications],
                    "dependencies": [],
                    "estimated_duration_days": 90,
                }
            ],
            "total_waves": 1,
            "planning_metadata": {
                "generated_by": "wave_planning_specialist",
                "generation_timestamp": "2025-10-29T00:00:00Z",
            },
        }

    def _parse_resource_allocation_result(
        self, result: Any, wave_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse resource allocation crew result."""
        # Placeholder - would parse actual agent output
        return {
            "allocations": [],
            "skill_gaps": [],
            "total_cost_estimate": 0.0,
        }

    def _parse_timeline_result(self, result: Any) -> Dict[str, Any]:
        """Parse timeline generation crew result."""
        # Placeholder - would parse actual agent output
        return {
            "overall_start_date": "2025-01-01",
            "overall_end_date": "2025-12-31",
            "phases": [],
            "milestones": [],
            "critical_path": [],
            "optimization_score": 0.85,
        }

    def _parse_cost_estimation_result(self, result: Any) -> Dict[str, Any]:
        """Parse cost estimation crew result."""
        # Placeholder - would parse actual agent output
        return {
            "labor_costs": 0.0,
            "infrastructure_costs": 0.0,
            "risk_contingency": 0.0,
            "total_estimated_cost": 0.0,
            "cost_breakdown_by_wave": [],
        }
