"""
Reusable task templates for common operations
"""

from crewai import Task
from typing import Any, List, Dict
import json

class TaskTemplates:
    """
    Library of reusable task templates.
    Provides standard task patterns for common operations.
    """
    
    @staticmethod
    def create_analysis_task(
        description: str,
        agent: Any,
        data: Dict[str, Any],
        expected_output: str,
        context: List[Task] = None
    ) -> Task:
        """Create a standard analysis task"""
        return Task(
            description=f"""
            {description}
            
            Data to analyze:
            {json.dumps(data, indent=2)}
            
            Provide comprehensive analysis including:
            - Key findings and patterns identified
            - Data quality assessment
            - Potential issues or anomalies
            - Statistical insights
            - Recommendations for improvement
            - Confidence level in findings
            """,
            agent=agent,
            expected_output=expected_output,
            context=context or []
        )
    
    @staticmethod
    def create_validation_task(
        items_to_validate: List[Any],
        validation_rules: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a validation task"""
        return Task(
            description=f"""
            Validate the following items against specified rules:
            
            Items to Validate:
            {json.dumps(items_to_validate, indent=2)}
            
            Validation Rules:
            {json.dumps(validation_rules, indent=2)}
            
            For each item:
            1. Check against all applicable validation rules
            2. Identify any violations or issues
            3. Assign validation status (PASS/FAIL/WARNING)
            4. Provide detailed error messages for failures
            5. Suggest corrections for issues found
            6. Calculate overall validation score
            
            Output comprehensive validation report with pass/fail status and detailed findings.
            """,
            agent=agent,
            expected_output="Validation report with detailed findings, pass/fail status, and correction suggestions",
            context=context or []
        )
    
    @staticmethod
    def create_transformation_task(
        source_format: str,
        target_format: str,
        transformation_rules: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a data transformation task"""
        return Task(
            description=f"""
            Transform data from {source_format} to {target_format}:
            
            Transformation Rules:
            {json.dumps(transformation_rules, indent=2)}
            
            Transformation Steps:
            1. Parse and validate source format
            2. Apply transformation rules systematically
            3. Handle data type conversions
            4. Manage missing or null values
            5. Validate transformed data structure
            6. Format according to target specification
            7. Ensure no critical data loss
            8. Generate transformation report
            
            Ensure data integrity and completeness throughout the transformation process.
            """,
            agent=agent,
            expected_output=f"Data successfully transformed to {target_format} with transformation report",
            context=context or []
        )
    
    @staticmethod
    def create_classification_task(
        items_to_classify: List[Any],
        classification_schema: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a classification task"""
        return Task(
            description=f"""
            Classify items according to the provided schema:
            
            Items to Classify:
            {json.dumps(items_to_classify, indent=2)}
            
            Classification Schema:
            {json.dumps(classification_schema, indent=2)}
            
            Classification Process:
            1. Analyze each item's characteristics
            2. Apply classification rules systematically
            3. Assign appropriate categories/types
            4. Calculate confidence scores
            5. Handle edge cases and ambiguous items
            6. Provide reasoning for classifications
            7. Flag items requiring manual review
            
            Output classification results with confidence scores and reasoning.
            """,
            agent=agent,
            expected_output="Classification results with categories, confidence scores, and reasoning",
            context=context or []
        )
    
    @staticmethod
    def create_matching_task(
        source_items: List[Any],
        target_items: List[Any],
        matching_criteria: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a matching/mapping task"""
        return Task(
            description=f"""
            Match source items to target items based on specified criteria:
            
            Source Items:
            {json.dumps(source_items, indent=2)}
            
            Target Items:
            {json.dumps(target_items, indent=2)}
            
            Matching Criteria:
            {json.dumps(matching_criteria, indent=2)}
            
            Matching Process:
            1. Compare source and target items
            2. Apply matching criteria and algorithms
            3. Calculate similarity scores
            4. Create optimal matches
            5. Handle many-to-one and one-to-many cases
            6. Identify unmatched items
            7. Provide confidence scores for matches
            8. Flag ambiguous matches for review
            
            Output matching results with confidence scores and reasoning.
            """,
            agent=agent,
            expected_output="Matching results with confidence scores, unmatched items, and reasoning",
            context=context or []
        )
    
    @staticmethod
    def create_quality_assessment_task(
        data_to_assess: List[Any],
        quality_metrics: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a data quality assessment task"""
        return Task(
            description=f"""
            Assess data quality using specified metrics:
            
            Data to Assess:
            {json.dumps(data_to_assess, indent=2)}
            
            Quality Metrics:
            {json.dumps(quality_metrics, indent=2)}
            
            Assessment Areas:
            1. Completeness - Missing values and fields
            2. Accuracy - Data correctness and validity
            3. Consistency - Internal data consistency
            4. Timeliness - Data freshness and currency
            5. Uniqueness - Duplicate detection
            6. Validity - Format and constraint compliance
            7. Integrity - Referential integrity checks
            
            Provide detailed quality report with scores and improvement recommendations.
            """,
            agent=agent,
            expected_output="Data quality assessment report with scores, issues, and recommendations",
            context=context or []
        )
    
    @staticmethod
    def create_extraction_task(
        source_data: Any,
        extraction_rules: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a data extraction task"""
        return Task(
            description=f"""
            Extract specific information from source data:
            
            Source Data:
            {json.dumps(source_data, indent=2)}
            
            Extraction Rules:
            {json.dumps(extraction_rules, indent=2)}
            
            Extraction Process:
            1. Parse source data structure
            2. Apply extraction patterns and rules
            3. Handle different data formats
            4. Clean and normalize extracted data
            5. Validate extracted information
            6. Handle missing or malformed data
            7. Organize results by category
            
            Output extracted data in structured format with metadata.
            """,
            agent=agent,
            expected_output="Extracted data in structured format with extraction metadata",
            context=context or []
        )
    
    @staticmethod
    def create_summarization_task(
        data_to_summarize: Any,
        summarization_criteria: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a summarization task"""
        return Task(
            description=f"""
            Create comprehensive summary of the provided data:
            
            Data to Summarize:
            {json.dumps(data_to_summarize, indent=2)}
            
            Summarization Criteria:
            {json.dumps(summarization_criteria, indent=2)}
            
            Summary Components:
            1. Executive summary of key findings
            2. Statistical overview and metrics
            3. Major patterns and trends
            4. Significant outliers or anomalies
            5. Key insights and implications
            6. Recommendations for action
            7. Areas requiring further investigation
            
            Provide concise yet comprehensive summary with actionable insights.
            """,
            agent=agent,
            expected_output="Comprehensive summary with key findings, insights, and recommendations",
            context=context or []
        )
    
    @staticmethod
    def create_sequential_task_chain(
        task_definitions: List[Dict[str, Any]],
        agents: List[Any]
    ) -> List[Task]:
        """Create a chain of sequential tasks with proper context linking"""
        tasks = []
        previous_task = None
        
        for i, task_def in enumerate(task_definitions):
            agent = agents[i % len(agents)]  # Cycle through agents if fewer than tasks
            
            context = [previous_task] if previous_task else []
            
            task = Task(
                description=task_def.get("description", ""),
                agent=agent,
                expected_output=task_def.get("expected_output", "Task completion"),
                context=context
            )
            
            tasks.append(task)
            previous_task = task
        
        return tasks
    
    @staticmethod
    def create_parallel_task_group(
        task_definitions: List[Dict[str, Any]],
        agents: List[Any]
    ) -> List[Task]:
        """Create a group of parallel tasks (no context dependencies)"""
        tasks = []
        
        for i, task_def in enumerate(task_definitions):
            agent = agents[i % len(agents)]  # Cycle through agents if fewer than tasks
            
            task = Task(
                description=task_def.get("description", ""),
                agent=agent,
                expected_output=task_def.get("expected_output", "Task completion"),
                context=[]  # No dependencies for parallel execution
            )
            
            tasks.append(task)
        
        return tasks