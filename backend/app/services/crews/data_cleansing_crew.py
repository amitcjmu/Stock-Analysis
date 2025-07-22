"""
Data Cleansing Crew - Converted to proper CrewAI pattern
"""

import logging
from typing import Any, Dict, List

from crewai import Process, Task

from app.services.crews.base_crew import BaseDiscoveryCrew
from app.services.crews.task_templates import TaskTemplates

logger = logging.getLogger(__name__)

class DataCleansingCrew(BaseDiscoveryCrew):
    """
    Crew for data quality assurance and standardization.
    
    Process:
    1. Data quality assessment
    2. Standardization and normalization
    3. Validation and cleansing
    4. Quality metrics generation
    """
    
    def __init__(self):
        """Initialize data cleansing crew"""
        super().__init__(
            name="data_cleansing_crew",
            description="Data quality assurance and standardization",
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True
        )
    
    def create_agents(self) -> List[Any]:
        """Create specialized agents for data cleansing"""
        agents = []
        
        try:
            # Import agent factory locally to avoid circular imports
            from app.services.agents.factory import agent_factory
            
            # Primary data cleansing agent
            cleansing_agent = agent_factory.create_agent("data_cleansing_agent")
            if cleansing_agent:
                agents.append(cleansing_agent)
            
            # Data validation agent for quality checks
            validation_agent = agent_factory.create_agent("data_validation_agent")
            if validation_agent:
                agents.append(validation_agent)
            
        except Exception as e:
            logger.warning(f"Agent factory creation failed: {e}")
        
        # Fallback agent if factory fails
        if not agents:
            logger.info("Creating fallback data cleansing agent")
            from crewai import Agent
            
            fallback_agent = Agent(
                role="Data Quality Specialist",
                goal="Cleanse and standardize data efficiently with quality validation",
                backstory="""You are an expert data quality specialist focused on:
                - Data type validation and standardization
                - Format consistency and normalization
                - Value cleaning and deduplication
                - Quality scoring and metrics
                - Efficient processing without extensive planning
                
                You work directly and provide comprehensive results.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[]
            )
            agents.append(fallback_agent)
        
        return agents
    
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create data cleansing tasks"""
        raw_data = inputs.get("raw_data", [])
        field_mappings = inputs.get("field_mappings", {})
        quality_rules = inputs.get("quality_rules", self._get_default_quality_rules())
        
        tasks = []
        
        # Task 1: Data Quality Assessment
        quality_assessment_task = TaskTemplates.create_quality_assessment_task(
            data_to_assess=raw_data[:10],  # Sample for assessment
            quality_metrics={
                "completeness": {"threshold": 0.8, "weight": 0.3},
                "validity": {"threshold": 0.9, "weight": 0.3},
                "consistency": {"threshold": 0.7, "weight": 0.2},
                "uniqueness": {"threshold": 0.95, "weight": 0.2}
            },
            agent=self.agents[0]
        )
        tasks.append(quality_assessment_task)
        
        # Task 2: Data Cleansing and Standardization
        cleansing_task = Task(
            description=f"""
            COMPREHENSIVE DATA CLEANSING TASK:
            
            Data to Process: {len(raw_data)} records
            Field Mappings: {field_mappings}
            Quality Rules: {quality_rules}
            
            Your cleansing objectives:
            
            1. DATA STANDARDIZATION:
               - Normalize field formats (dates, names, identifiers)
               - Standardize value representations
               - Apply consistent casing and formatting
               - Clean whitespace and special characters
            
            2. DATA VALIDATION:
               - Validate data types against expected formats
               - Check value ranges and constraints
               - Identify and flag invalid entries
               - Verify referential integrity where applicable
            
            3. DEDUPLICATION:
               - Identify duplicate records using key fields
               - Merge or mark duplicates appropriately
               - Preserve data completeness during deduplication
            
            4. QUALITY SCORING:
               - Calculate completeness scores per field
               - Assess data consistency across records
               - Generate overall quality metrics
               - Identify records requiring manual review
            
            5. OUTPUT FORMAT:
            Return JSON with:
            {{
                "cleansed_data": [cleaned_records],
                "quality_metrics": {{
                    "total_records": count,
                    "records_processed": count,
                    "issues_found": count,
                    "duplicates_removed": count,
                    "overall_quality_score": 0.85
                }},
                "issues_log": [
                    {{
                        "record_id": "id",
                        "field": "field_name",
                        "issue": "description",
                        "severity": "high|medium|low",
                        "action_taken": "description"
                    }}
                ],
                "recommendations": ["improvement suggestions"]
            }}
            """,
            agent=self.agents[0],  # Data cleansing agent
            expected_output="JSON with cleansed data, quality metrics, and issue log",
            context=[quality_assessment_task]
        )
        tasks.append(cleansing_task)
        
        # Task 3: Final Validation (if we have a validation agent)
        if len(self.agents) > 1:
            validation_task = Task(
                description="""
                FINAL VALIDATION TASK:
                
                Perform final validation of the cleansed data:
                
                1. Verify all cleansing operations were successful
                2. Validate data integrity and consistency
                3. Check that quality improvements were achieved
                4. Ensure no critical data was lost during cleansing
                5. Confirm readiness for next processing phase
                
                Provide validation summary with pass/fail status and any remaining issues.
                """,
                agent=self.agents[1],  # Validation agent
                expected_output="Final validation report with pass/fail status",
                context=[cleansing_task]
            )
            tasks.append(validation_task)
        
        return tasks
    
    def _get_default_quality_rules(self) -> Dict[str, Any]:
        """Get default data quality rules"""
        return {
            "required_fields": ["asset_name", "asset_type"],
            "data_types": {
                "asset_name": "string",
                "asset_type": "string",
                "ip_address": "ip",
                "cpu_count": "integer",
                "memory_gb": "float"
            },
            "value_constraints": {
                "environment": ["production", "staging", "development", "test"],
                "status": ["active", "inactive", "decommissioned"]
            },
            "format_rules": {
                "ip_address": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
                "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
            "uniqueness_fields": ["asset_id", "hostname", "serial_number"],
            "completeness_thresholds": {
                "critical": 1.0,  # 100% complete
                "important": 0.8,  # 80% complete
                "optional": 0.0   # Any level acceptable
            }
        }
    
    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process data cleansing results"""
        try:
            # Extract results from final task
            final_result = raw_results
            
            # Parse JSON if results are in string format
            if isinstance(final_result, str):
                try:
                    import re
                    json_match = re.search(r'\{.*\}', final_result, re.DOTALL)
                    if json_match:
                        import json
                        final_result = json.loads(json_match.group())
                    else:
                        final_result = self._parse_text_results(final_result)
                except Exception as e:
                    logger.warning(f"Could not parse JSON from results: {e}")
                    final_result = {"error": "Failed to parse results"}
            
            # Ensure expected structure
            if not isinstance(final_result, dict):
                final_result = {"error": "Unexpected result format"}
            
            cleansed_data = final_result.get("cleansed_data", [])
            quality_metrics = final_result.get("quality_metrics", {})
            issues_log = final_result.get("issues_log", [])
            
            return {
                "crew_name": self.name,
                "status": "completed",
                "cleansed_data": cleansed_data,
                "quality_metrics": {
                    "total_records": quality_metrics.get("total_records", 0),
                    "records_processed": quality_metrics.get("records_processed", 0),
                    "issues_found": quality_metrics.get("issues_found", 0),
                    "duplicates_removed": quality_metrics.get("duplicates_removed", 0),
                    "overall_quality_score": quality_metrics.get("overall_quality_score", 0.0),
                    "improvement_percentage": self._calculate_improvement(quality_metrics)
                },
                "issues": {
                    "total_issues": len(issues_log),
                    "high_severity": sum(1 for issue in issues_log if issue.get("severity") == "high"),
                    "medium_severity": sum(1 for issue in issues_log if issue.get("severity") == "medium"),
                    "low_severity": sum(1 for issue in issues_log if issue.get("severity") == "low"),
                    "issues_log": issues_log
                },
                "recommendations": final_result.get("recommendations", []),
                "context": {
                    "client_account_id": self.context.client_account_id if self.context else None,
                    "engagement_id": self.context.engagement_id if self.context else None
                },
                "metadata": {
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                    "processing_complete": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing data cleansing results: {e}")
            return {
                "crew_name": self.name,
                "status": "error",
                "error": str(e),
                "cleansed_data": [],
                "quality_metrics": {"error": True},
                "context": {
                    "client_account_id": self.context.client_account_id if self.context else None,
                    "engagement_id": self.context.engagement_id if self.context else None
                }
            }
    
    def _parse_text_results(self, text_result: str) -> Dict[str, Any]:
        """Parse cleansing results from text when JSON parsing fails"""
        result = {
            "cleansed_data": [],
            "quality_metrics": {"parsing_fallback": True},
            "issues_log": [],
            "recommendations": []
        }
        
        # Extract basic metrics from text
        lines = text_result.split('\n')
        for line in lines:
            line = line.strip().lower()
            if 'records processed' in line or 'total records' in line:
                try:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        result["quality_metrics"]["records_processed"] = int(numbers[0])
                except Exception:
                    pass
            elif 'quality score' in line:
                try:
                    import re
                    scores = re.findall(r'\d+\.?\d*', line)
                    if scores:
                        result["quality_metrics"]["overall_quality_score"] = float(scores[0])
                except Exception:
                    pass
        
        return result
    
    def _calculate_improvement(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate quality improvement percentage"""
        try:
            before_score = quality_metrics.get("initial_quality_score", 0.5)
            after_score = quality_metrics.get("overall_quality_score", 0.5)
            
            if before_score > 0:
                improvement = ((after_score - before_score) / before_score) * 100
                return max(0.0, min(100.0, improvement))  # Clamp between 0-100
            return 0.0
        except Exception:
            return 0.0