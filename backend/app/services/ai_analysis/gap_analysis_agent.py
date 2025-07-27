"""
Gap Analysis AI Agent - B2.1
ADCS AI Analysis & Intelligence Service

This agent uses CrewAI framework to intelligently analyze data gaps in collected assets
and provide targeted recommendations for gap resolution.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from crewai import Agent, Process, Task

    from app.services.crews.base_crew import BaseDiscoveryCrew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create dummy classes for type hints
    Agent = Task = Process = object
    BaseDiscoveryCrew = object

logger = logging.getLogger(__name__)

# Critical attributes framework for 6R migration analysis
CRITICAL_ATTRIBUTES_FRAMEWORK = {
    "infrastructure": {
        "primary": [
            "hostname",
            "environment",
            "os_type",
            "os_version",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "network_zone",
        ],
        "business_impact": "high",
        "6r_relevance": ["rehost", "replatform", "refactor"],
    },
    "application": {
        "primary": [
            "application_name",
            "application_type",
            "technology_stack",
            "criticality_level",
            "data_classification",
            "compliance_scope",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "repurchase", "retire"],
    },
    "operational": {
        "primary": [
            "owner",
            "cost_center",
            "backup_strategy",
            "monitoring_status",
            "patch_level",
            "last_scan_date",
        ],
        "business_impact": "medium",
        "6r_relevance": ["retain", "rehost", "replatform"],
    },
    "dependencies": {
        "primary": [
            "application_dependencies",
            "database_dependencies",
            "integration_points",
            "data_flows",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "replatform", "repurchase"],
    },
}


class GapAnalysisAgent(BaseDiscoveryCrew):
    """
    AI-powered gap analysis agent using CrewAI framework.

    Analyzes collected data to identify missing critical attributes
    for 6R migration strategy recommendations.
    """

    def __init__(self):
        """Initialize gap analysis crew"""
        super().__init__(
            name="gap_analysis_crew",
            description="AI-powered gap analysis for critical migration attributes",
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
        )

    def create_agents(self) -> List[Any]:
        """Create specialized AI agents for gap analysis"""
        agents = []

        try:
            # Primary Gap Analysis Specialist
            gap_specialist = Agent(
                role="Data Gap Analysis Specialist",
                goal="Identify missing critical attributes that impact 6R migration strategy accuracy",
                backstory="""You are an expert AI agent specializing in migration data gap analysis.
                Your deep understanding of the 22 critical attributes framework enables you to:

                - Analyze collected asset data against the critical attributes framework
                - Identify gaps that impact 6R strategy recommendations (Rehost, Replatform, Refactor, Repurchase, Retire, Retain)
                - Prioritize gaps based on business impact and migration strategy requirements
                - Assess data quality and completeness for migration planning
                - Recommend targeted data collection strategies to fill critical gaps

                You understand that different migration strategies require different attributes:
                - Rehost needs infrastructure details (OS, dependencies, performance)
                - Replatform requires technology stack and architecture information
                - Refactor demands application complexity and code quality metrics
                - Repurchase needs business function and cost analysis
                - Retire requires business value and dependency assessment
                - Retain needs operational metrics and cost justification

                Your analysis directly improves migration recommendation confidence scores.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(gap_specialist)

            # Business Impact Assessor
            impact_assessor = Agent(
                role="Business Impact Assessment Agent",
                goal="Evaluate the business impact of identified data gaps on migration outcomes",
                backstory="""You are a business-focused AI agent that assesses how data gaps
                affect migration project success and business outcomes.

                Your expertise includes:
                - Understanding how missing data impacts migration strategy confidence
                - Evaluating business risk from incomplete asset information
                - Assessing cost implications of data gaps on migration planning
                - Prioritizing gap resolution based on business value and urgency
                - Connecting technical gaps to business consequences

                You work closely with the Gap Analysis Specialist to ensure that
                gap identification considers both technical accuracy and business impact.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(impact_assessor)

            # Data Quality Validator
            quality_validator = Agent(
                role="Data Quality Validation Expert",
                goal="Validate gap analysis accuracy and ensure comprehensive coverage",
                backstory="""You are a quality assurance AI agent specializing in data analysis validation.
                Your role is to ensure gap analysis is accurate, complete, and actionable.

                Your validation expertise covers:
                - Cross-referencing gap analysis against collected data patterns
                - Identifying false positives and false negatives in gap detection
                - Ensuring all critical attribute categories are properly analyzed
                - Validating business impact assessments for consistency
                - Confirming gap prioritization aligns with 6R strategy requirements

                You provide the final quality check before gap analysis results
                are used for questionnaire generation and collection planning.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(quality_validator)

        except Exception as e:
            logger.error(f"Failed to create gap analysis agents: {e}")
            # Create minimal fallback agent
            fallback_agent = Agent(
                role="Gap Analysis Agent",
                goal="Identify data gaps for migration planning",
                backstory="You analyze data gaps for migration planning.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[],
            )
            agents.append(fallback_agent)

        return agents

    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create gap analysis tasks"""
        collected_data = inputs.get("collected_data", [])
        collection_flow_id = inputs.get("collection_flow_id")
        automation_tier = inputs.get("automation_tier", "tier_2")
        business_context = inputs.get("business_context", {})

        tasks = []

        # Task 1: Primary Gap Analysis
        gap_analysis_task = Task(
            description=f"""
            CRITICAL ATTRIBUTES GAP ANALYSIS

            Collection Flow ID: {collection_flow_id}
            Automation Tier: {automation_tier}
            Assets Analyzed: {len(collected_data)}

            CRITICAL ATTRIBUTES FRAMEWORK (22 Core Attributes):
            {json.dumps(CRITICAL_ATTRIBUTES_FRAMEWORK, indent=2)}

            COLLECTED DATA SAMPLE:
            {json.dumps(collected_data[:5], indent=2) if collected_data else "No data collected"}

            ANALYSIS OBJECTIVES:

            1. ATTRIBUTE COVERAGE ANALYSIS:
               - Map collected data fields to the 22 critical attributes framework
               - Identify missing primary attributes in each category (infrastructure, application, operational, dependencies)
               - Calculate coverage percentage per category and overall
               - Assess data quality for available attributes

            2. 6R STRATEGY IMPACT ASSESSMENT:
               - Evaluate how missing attributes affect each 6R strategy confidence:
                 * Rehost: Infrastructure and operational attributes
                 * Replatform: Technology stack and architecture attributes
                 * Refactor: Application complexity and dependencies
                 * Repurchase: Business function and integration points
                 * Retire: Business value and dependency assessment
                 * Retain: Operational metrics and cost justification
               - Assign impact scores (critical, high, medium, low) per 6R strategy

            3. GAP PRIORITIZATION:
               - Priority 1 (Critical): Gaps blocking 6R strategy selection
               - Priority 2 (High): Gaps reducing confidence in recommendations
               - Priority 3 (Medium): Gaps affecting migration planning details
               - Priority 4 (Low): Nice-to-have attributes for optimization

            4. AUTOMATION TIER CONSIDERATIONS:
               Current Tier: {automation_tier}
               - Tier 1: Focus on API-collectable attributes, minimal manual gaps
               - Tier 2: Balance automated collection with strategic manual input
               - Tier 3: Expect more manual collection, prioritize business-critical gaps
               - Tier 4: Manual-heavy approach, focus on essential migration decisions

            OUTPUT FORMAT:
            Return detailed JSON analysis:
            {{
                "gap_analysis_summary": {{
                    "total_attributes_framework": 22,
                    "attributes_collected": <count>,
                    "overall_coverage_percentage": <0-100>,
                    "critical_gaps_count": <count>,
                    "automation_feasibility": "{automation_tier}"
                }},
                "category_analysis": {{
                    "infrastructure": {{
                        "coverage_percentage": <0-100>,
                        "missing_attributes": ["attr1", "attr2"],
                        "available_attributes": ["attr3", "attr4"],
                        "data_quality_score": <0-100>,
                        "business_impact": "high|medium|low"
                    }},
                    "application": {{ ... }},
                    "operational": {{ ... }},
                    "dependencies": {{ ... }}
                }},
                "sixr_strategy_impact": {{
                    "rehost": {{
                        "confidence_impact": <0-100>,
                        "blocking_gaps": ["attr1", "attr2"],
                        "impact_severity": "critical|high|medium|low"
                    }},
                    "replatform": {{ ... }},
                    "refactor": {{ ... }},
                    "repurchase": {{ ... }},
                    "retire": {{ ... }},
                    "retain": {{ ... }}
                }},
                "prioritized_gaps": [
                    {{
                        "gap_id": "gap-001",
                        "attribute_name": "technology_stack",
                        "category": "application",
                        "priority": 1,
                        "business_impact": "critical",
                        "affects_strategies": ["refactor", "repurchase"],
                        "collection_difficulty": "medium",
                        "estimated_effort": "2-4 hours",
                        "recommended_method": "SME interview",
                        "business_justification": "Required for accurate refactor vs repurchase decision"
                    }}
                ],
                "collection_recommendations": {{
                    "immediate_actions": ["action1", "action2"],
                    "manual_collection_required": true,
                    "automation_enhancement_opportunities": ["opportunity1"],
                    "estimated_effort_hours": <number>,
                    "recommended_sequence": ["step1", "step2", "step3"]
                }}
            }}
            """,
            agent=self.agents[0],
            expected_output="Comprehensive JSON gap analysis with 6R strategy impact assessment",
        )
        tasks.append(gap_analysis_task)

        # Task 2: Business Impact Assessment
        if len(self.agents) > 1:
            business_impact_task = Task(
                description=f"""
                BUSINESS IMPACT ASSESSMENT FOR IDENTIFIED GAPS

                Business Context: {json.dumps(business_context, indent=2)}

                Using the gap analysis results, assess business impact:

                1. MIGRATION PROJECT RISK ASSESSMENT:
                   - How do identified gaps affect migration timeline?
                   - What is the cost impact of incomplete 6R recommendations?
                   - Which gaps pose the highest business risk?
                   - How do gaps affect migration wave planning?

                2. DECISION-MAKING IMPACT:
                   - Which gaps block go/no-go migration decisions?
                   - How do gaps affect business case accuracy?
                   - What is the confidence impact on executive presentations?
                   - Which gaps affect vendor selection and procurement?

                3. COST-BENEFIT ANALYSIS:
                   - Effort required to fill each gap vs business value gained
                   - ROI of gap resolution activities
                   - Risk of proceeding with incomplete data
                   - Impact on migration success metrics

                4. STAKEHOLDER IMPACT:
                   - Which business stakeholders are affected by each gap?
                   - What decisions are blocked by missing information?
                   - How do gaps affect project timeline and budget?

                Provide business-focused gap prioritization and recommendations.
                """,
                agent=self.agents[1],
                expected_output="Business impact assessment with risk analysis and stakeholder implications",
                context=[gap_analysis_task],
            )
            tasks.append(business_impact_task)

        # Task 3: Quality Validation
        if len(self.agents) > 2:
            validation_task = Task(
                description="""
                GAP ANALYSIS QUALITY VALIDATION

                Validate the gap analysis for accuracy and completeness:

                1. COVERAGE VALIDATION:
                   - Verify all 22 critical attributes were considered
                   - Check for missed data in collected information
                   - Validate gap identification accuracy
                   - Ensure no false positives or negatives

                2. PRIORITIZATION REVIEW:
                   - Verify gap priorities align with 6R strategy requirements
                   - Check business impact assessments for consistency
                   - Validate effort estimates for gap resolution
                   - Review collection method recommendations

                3. RECOMMENDATION QUALITY:
                   - Ensure recommendations are actionable
                   - Verify technical feasibility of collection methods
                   - Check alignment with automation tier capabilities
                   - Validate business justifications

                4. COMPLETENESS CHECK:
                   - All critical gaps identified and documented
                   - Business impact properly assessed
                   - Collection strategies clearly defined
                   - Success metrics established

                Provide validation report with any corrections or enhancements.
                """,
                agent=self.agents[2],
                expected_output="Quality validation report with accuracy assessment and recommendations",
                context=(
                    [gap_analysis_task, business_impact_task]
                    if len(tasks) > 1
                    else [gap_analysis_task]
                ),
            )
            tasks.append(validation_task)

        return tasks

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process gap analysis results"""
        try:
            # Extract and parse results
            if isinstance(raw_results, str):
                try:
                    import re

                    json_match = re.search(r"\{.*\}", raw_results, re.DOTALL)
                    if json_match:
                        parsed_results = json.loads(json_match.group())
                    else:
                        parsed_results = self._parse_text_results(raw_results)
                except Exception as e:
                    logger.warning(
                        f"Could not parse JSON from gap analysis results: {e}"
                    )
                    parsed_results = self._parse_text_results(raw_results)
            else:
                parsed_results = raw_results

            # Ensure required structure
            if not isinstance(parsed_results, dict):
                parsed_results = {"error": "Unexpected result format"}

            # Extract key components
            gap_summary = parsed_results.get("gap_analysis_summary", {})
            category_analysis = parsed_results.get("category_analysis", {})
            sixr_impact = parsed_results.get("sixr_strategy_impact", {})
            prioritized_gaps = parsed_results.get("prioritized_gaps", [])
            recommendations = parsed_results.get("collection_recommendations", {})

            # Calculate additional metrics
            total_gaps = len(prioritized_gaps)
            critical_gaps = len(
                [gap for gap in prioritized_gaps if gap.get("priority") == 1]
            )
            high_priority_gaps = len(
                [gap for gap in prioritized_gaps if gap.get("priority") == 2]
            )

            # Calculate confidence impact on 6R strategies
            strategy_confidence_impact = {}
            for strategy, impact_data in sixr_impact.items():
                confidence_impact = impact_data.get("confidence_impact", 100)
                strategy_confidence_impact[strategy] = confidence_impact

            avg_confidence_impact = (
                sum(strategy_confidence_impact.values())
                / len(strategy_confidence_impact)
                if strategy_confidence_impact
                else 100
            )

            return {
                "crew_name": self.name,
                "status": "completed",
                "gap_analysis": {
                    "summary": {
                        "total_gaps_identified": total_gaps,
                        "critical_gaps": critical_gaps,
                        "high_priority_gaps": high_priority_gaps,
                        "overall_coverage": gap_summary.get(
                            "overall_coverage_percentage", 0
                        ),
                        "avg_confidence_impact": round(avg_confidence_impact, 2),
                    },
                    "category_breakdown": category_analysis,
                    "sixr_strategy_impact": sixr_impact,
                    "prioritized_gaps": prioritized_gaps,
                    "collection_recommendations": recommendations,
                },
                "business_intelligence": {
                    "migration_readiness_score": self._calculate_migration_readiness(
                        prioritized_gaps, strategy_confidence_impact
                    ),
                    "business_risk_level": self._assess_business_risk(
                        critical_gaps, high_priority_gaps
                    ),
                    "collection_effort_estimate": recommendations.get(
                        "estimated_effort_hours", 0
                    ),
                    "automation_enhancement_score": self._calculate_automation_score(
                        recommendations
                    ),
                },
                "recommendations": {
                    "immediate_actions": recommendations.get("immediate_actions", []),
                    "next_steps": recommendations.get("recommended_sequence", []),
                    "business_justification": "Gap analysis completed to enhance 6R migration strategy confidence",
                    "success_metrics": [
                        f"Fill {critical_gaps} critical gaps to improve strategy confidence",
                        f"Complete {high_priority_gaps} high-priority data collection activities",
                        "Achieve >85% coverage of critical attributes framework",
                    ],
                },
                "metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "framework_version": "critical_attributes_v1.0",
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                },
            }

        except Exception as e:
            logger.error(f"Error processing gap analysis results: {e}")
            return {
                "crew_name": self.name,
                "status": "error",
                "error": str(e),
                "gap_analysis": {"summary": {"error": True}},
                "metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                },
            }

    def _parse_text_results(self, text_result: str) -> Dict[str, Any]:
        """Parse gap analysis from text when JSON parsing fails"""
        result = {
            "gap_analysis_summary": {"parsing_fallback": True},
            "prioritized_gaps": [],
            "collection_recommendations": {},
        }

        # Extract basic metrics from text
        lines = text_result.split("\n")
        gap_count = 0

        for line in lines:
            line = line.strip().lower()
            if "gap" in line and (
                "critical" in line or "high" in line or "priority" in line
            ):
                gap_count += 1
            elif "coverage" in line or "percentage" in line:
                try:
                    import re

                    numbers = re.findall(r"\d+", line)
                    if numbers:
                        result["gap_analysis_summary"][
                            "overall_coverage_percentage"
                        ] = int(numbers[0])
                except Exception:
                    pass

        result["gap_analysis_summary"]["total_gaps_identified"] = gap_count
        return result

    def _calculate_migration_readiness(
        self, gaps: List[Dict[str, Any]], strategy_impact: Dict[str, float]
    ) -> float:
        """Calculate overall migration readiness score"""
        if not gaps:
            return 100.0

        # Weight gaps by priority
        priority_weights = {1: 0.5, 2: 0.3, 3: 0.15, 4: 0.05}
        total_impact = 0
        total_weight = 0

        for gap in gaps:
            priority = gap.get("priority", 4)
            weight = priority_weights.get(priority, 0.05)
            impact = 100 - (priority * 20)  # Higher priority = higher impact
            total_impact += impact * weight
            total_weight += weight

        if total_weight == 0:
            return 100.0

        readiness_score = 100 - (total_impact / total_weight)
        return max(0, min(100, readiness_score))

    def _assess_business_risk(self, critical_gaps: int, high_priority_gaps: int) -> str:
        """Assess business risk level based on gap analysis"""
        if critical_gaps >= 3:
            return "high"
        elif critical_gaps >= 1 or high_priority_gaps >= 5:
            return "medium"
        elif high_priority_gaps >= 2:
            return "low"
        else:
            return "minimal"

    def _calculate_automation_score(self, recommendations: Dict[str, Any]) -> float:
        """Calculate automation enhancement score"""
        opportunities = recommendations.get("automation_enhancement_opportunities", [])
        manual_required = recommendations.get("manual_collection_required", True)

        if not manual_required:
            return 100.0
        elif len(opportunities) >= 3:
            return 75.0
        elif len(opportunities) >= 1:
            return 50.0
        else:
            return 25.0

    async def analyze_data_gaps(
        self,
        collected_data: List[Dict[str, Any]],
        existing_gaps: List[Dict[str, Any]],
        sixr_requirements: Dict[str, Any],
        automation_tier: str,
    ) -> Dict[str, Any]:
        """
        Analyze data gaps for given collected data.

        Args:
            collected_data: List of collected asset data
            existing_gaps: List of existing gaps identified
            sixr_requirements: 6R strategy requirements
            automation_tier: Current automation tier

        Returns:
            Gap analysis results
        """
        try:
            # Prepare analysis inputs
            analysis_inputs = {
                "collected_data": collected_data,
                "existing_gaps": existing_gaps,
                "sixr_requirements": sixr_requirements,
                "automation_tier": automation_tier,
            }

            # Execute gap analysis
            logger.info(f"Starting gap analysis for {len(collected_data)} assets")
            results = await self.kickoff_async(analysis_inputs)

            logger.info("Gap analysis completed")
            return self.process_results(results)

        except Exception as e:
            logger.error(f"Failed to perform gap analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "gap_analysis": {"summary": {"error": True}},
                "metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                },
            }


async def analyze_collection_gaps(
    collection_flow_id: UUID,
    collected_data: List[Dict[str, Any]],
    automation_tier: str = "tier_2",
    business_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    High-level function to perform gap analysis using the AI agent.

    Args:
        collection_flow_id: UUID of the collection flow
        collected_data: List of collected asset data
        automation_tier: Current automation tier (tier_1, tier_2, tier_3, tier_4)
        business_context: Additional business context for analysis

    Returns:
        Comprehensive gap analysis results
    """
    try:
        # Initialize gap analysis agent
        gap_agent = GapAnalysisAgent()

        # Prepare analysis inputs
        analysis_inputs = {
            "collection_flow_id": str(collection_flow_id),
            "collected_data": collected_data,
            "automation_tier": automation_tier,
            "business_context": business_context or {},
        }

        # Execute gap analysis
        logger.info(f"Starting gap analysis for collection flow: {collection_flow_id}")
        results = await gap_agent.kickoff_async(analysis_inputs)

        logger.info(f"Gap analysis completed for collection flow: {collection_flow_id}")
        return gap_agent.process_results(results)

    except Exception as e:
        logger.error(f"Failed to perform gap analysis: {e}")
        return {
            "crew_name": "gap_analysis_crew",
            "status": "error",
            "error": str(e),
            "gap_analysis": {"summary": {"error": True}},
            "metadata": {"analysis_timestamp": datetime.now(timezone.utc).isoformat()},
        }
