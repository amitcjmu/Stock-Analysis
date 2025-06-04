"""
Execution Handler for CrewAI Flow Service
Handles parallel execution, retry logic, agent task management, and async operations.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

logger = logging.getLogger(__name__)

class ExecutionHandler:
    """Handler for executing CrewAI agents with parallel processing and retry logic."""
    
    def __init__(self, config, agents: Dict[str, Any]):
        self.config = config
        self.agents = agents
        self.active_tasks = {}
        self.execution_metrics = {}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2), 
        reraise=True
    )
    async def execute_data_validation_async(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data validation with retry logic and enhanced prompts."""
        if 'data_validator' not in self.agents:
            raise Exception("Data validator agent not available")
        
        start_time = datetime.now()
        task_id = f"validation_{start_time.strftime('%H%M%S')}"
        
        try:
            # Enhanced validation prompt with specific instructions
            validation_task = self._create_validation_task(cmdb_data)
            
            # Create crew for async execution
            validation_crew = self._create_crew(
                agents=[self.agents['data_validator']],
                tasks=[validation_task],
                crew_name="data_validation"
            )
            
            # Execute with configurable timeout
            result = await asyncio.wait_for(
                validation_crew.kickoff_async(),
                timeout=self.config.timeout_data_validation
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            self._record_execution_metric(task_id, "data_validation", duration, "success")
            
            logger.info(f"Data validation completed in {duration:.2f} seconds")
            
            return {
                "validation_report": str(result),
                "validation_status": "completed",
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            }
            
        except asyncio.TimeoutError:
            self._record_execution_metric(task_id, "data_validation", 
                                        self.config.timeout_data_validation, "timeout")
            logger.warning(f"Data validation timed out after {self.config.timeout_data_validation}s")
            raise
        except Exception as e:
            self._record_execution_metric(task_id, "data_validation", 
                                        (datetime.now() - start_time).total_seconds(), "error")
            logger.error(f"Data validation failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True
    )
    async def execute_field_mapping_async(self, cmdb_data: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, str]:
        """Execute AI-powered field mapping with enhanced prompts and parsing."""
        if 'field_mapper' not in self.agents:
            raise Exception("Field mapper agent not available")
        
        start_time = datetime.now()
        task_id = f"mapping_{start_time.strftime('%H%M%S')}"
        
        try:
            # Enhanced field mapping prompt
            mapping_task = self._create_field_mapping_task(cmdb_data, validation_result)
            
            mapping_crew = self._create_crew(
                agents=[self.agents['field_mapper']],
                tasks=[mapping_task],
                crew_name="field_mapping"
            )
            
            result = await asyncio.wait_for(
                mapping_crew.kickoff_async(),
                timeout=self.config.timeout_field_mapping
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            self._record_execution_metric(task_id, "field_mapping", duration, "success")
            
            logger.info(f"Field mapping completed in {duration:.2f} seconds")
            
            return {
                "mapping_result": str(result),
                "mapping_status": "completed",
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            }
            
        except asyncio.TimeoutError:
            self._record_execution_metric(task_id, "field_mapping", 
                                        self.config.timeout_field_mapping, "timeout")
            logger.warning(f"Field mapping timed out after {self.config.timeout_field_mapping}s")
            raise
        except Exception as e:
            self._record_execution_metric(task_id, "field_mapping", 
                                        (datetime.now() - start_time).total_seconds(), "error")
            logger.error(f"Field mapping failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True
    )
    async def execute_asset_classification_async(self, cmdb_data: Dict[str, Any], field_mappings: Dict[str, str]) -> List[Dict[str, Any]]:
        """Execute asset classification with enhanced prompts and parsing."""
        if 'asset_classifier' not in self.agents:
            raise Exception("Asset classifier agent not available")
        
        start_time = datetime.now()
        task_id = f"classification_{start_time.strftime('%H%M%S')}"
        
        try:
            # Enhanced asset classification prompt
            classification_task = self._create_asset_classification_task(cmdb_data, field_mappings)
            
            classification_crew = self._create_crew(
                agents=[self.agents['asset_classifier']],
                tasks=[classification_task],
                crew_name="asset_classification"
            )
            
            result = await asyncio.wait_for(
                classification_crew.kickoff_async(),
                timeout=self.config.timeout_asset_classification
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            self._record_execution_metric(task_id, "asset_classification", duration, "success")
            
            logger.info(f"Asset classification completed in {duration:.2f} seconds")
            
            return {
                "classification_result": str(result),
                "classification_status": "completed",
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            }
            
        except asyncio.TimeoutError:
            self._record_execution_metric(task_id, "asset_classification", 
                                        self.config.timeout_asset_classification, "timeout")
            logger.warning(f"Asset classification timed out after {self.config.timeout_asset_classification}s")
            raise
        except Exception as e:
            self._record_execution_metric(task_id, "asset_classification", 
                                        (datetime.now() - start_time).total_seconds(), "error")
            logger.error(f"Asset classification failed: {e}")
            raise
    
    async def execute_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple tasks in parallel with error handling."""
        if not tasks:
            return []
        
        start_time = datetime.now()
        logger.info(f"🚀 Starting parallel execution of {len(tasks)} tasks")
        
        # Create coroutines for parallel execution
        coroutines = []
        task_names = []
        
        for task in tasks:
            task_type = task.get("type")
            task_data = task.get("data", {})
            
            if task_type == "field_mapping":
                coroutine = self.execute_field_mapping_async(
                    task_data.get("cmdb_data"),
                    task_data.get("validation_result")
                )
            elif task_type == "asset_classification":
                coroutine = self.execute_asset_classification_async(
                    task_data.get("cmdb_data"),
                    task_data.get("field_mappings", {})
                )
            else:
                logger.warning(f"Unknown task type: {task_type}")
                continue
            
            coroutines.append(coroutine)
            task_names.append(task_type)
        
        # Execute all tasks in parallel
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Parallel execution completed in {duration:.2f} seconds")
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Task {task_names[i]} failed: {result}")
                    processed_results.append({"status": "failed", "error": str(result)})
                else:
                    processed_results.append({"status": "success", "result": result})
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            raise
    
    def _create_validation_task(self, cmdb_data: Dict[str, Any]):
        """Create enhanced data validation task."""
        from crewai import Task
        
        description = f"""
        Perform comprehensive CMDB data validation for migration readiness:
        
        **Dataset Information:**
        - Filename: {cmdb_data.get('filename', 'unknown')}
        - Headers: {cmdb_data.get('headers', [])}
        - Records: {len(cmdb_data.get('sample_data', []))}
        - Sample Data: {cmdb_data.get('sample_data', [])[:2]}
        
        **Required Analysis:**
        1. Data Quality Score (1-10) based on completeness, consistency, format
        2. Critical Missing Fields (identify gaps for migration)
        3. Data Consistency Issues (format problems, duplicates, invalid values)
        4. Migration Readiness (Yes/No with specific reasons)
        5. Recommended Actions (prioritized list)
        
        **Output Format:**
        Provide structured analysis with:
        - QUALITY_SCORE: X/10
        - MISSING_FIELDS: [list]
        - ISSUES: [specific problems]
        - READY: Yes/No
        - ACTIONS: [recommended steps]
        
        Be specific, actionable, and concise.
        """
        
        return Task(
            description=description,
            agent=self.agents['data_validator'],
            expected_output="Structured data validation report with quality score and specific recommendations"
        )
    
    def _create_field_mapping_task(self, cmdb_data: Dict[str, Any], validation_result: Dict[str, Any]):
        """Create enhanced field mapping task."""
        from crewai import Task
        
        description = f"""
        Intelligently map CMDB fields to migration critical attributes using pattern recognition:
        
        **Available Fields:** {cmdb_data.get('headers', [])}
        **Sample Data:** {cmdb_data.get('sample_data', [])[:2]}
        **Data Quality:** {validation_result.get('data_quality_score', 'Unknown')}
        
        **Critical Migration Attributes to Map:**
        1. asset_name (primary identifier - server names, app names)
        2. ci_type (asset type - Server, Database, Application, Network)
        3. environment (prod, test, dev, staging)
        4. business_owner (responsible team/person)
        5. technical_owner (technical contact)
        6. location (datacenter, region, site)
        7. dependencies (related systems)
        8. risk_level (high, medium, low)
        9. compliance_zone (PCI, HIPAA, SOX, etc.)
        10. lifecycle_stage (active, deprecated, sunset)
        
        **Mapping Rules:**
        - Use exact field names where possible
        - Look for partial matches (e.g., "env" maps to "environment")
        - Consider data content patterns
        - Assign confidence scores (0.0-1.0)
        
        **Output Format:**
        For each field, provide:
        FIELD_NAME -> CRITICAL_ATTRIBUTE (confidence: X.X)
        
        Example:
        server_name -> asset_name (confidence: 0.95)
        type -> ci_type (confidence: 0.90)
        env -> environment (confidence: 0.85)
        
        Be precise and provide confidence scores.
        """
        
        return Task(
            description=description,
            agent=self.agents['field_mapper'],
            expected_output="Field mapping suggestions with confidence scores in structured format"
        )
    
    def _create_asset_classification_task(self, cmdb_data: Dict[str, Any], field_mappings: Dict[str, str]):
        """Create enhanced asset classification task."""
        from crewai import Task
        
        description = f"""
        Classify IT assets for migration planning with high accuracy and detail:
        
        **Assets to Classify:** {cmdb_data.get('sample_data', [])[:5]}
        **Field Mappings:** {field_mappings}
        **Headers:** {cmdb_data.get('headers', [])}
        
        **Classification Requirements:**
        For each asset, determine:
        
        1. **Asset Type** (choose from):
           - Server (physical/virtual servers)
           - Database (RDBMS, NoSQL, data warehouses)
           - Application (web apps, desktop apps, services)
           - Network (routers, switches, load balancers)
           - Storage (SAN, NAS, object storage)
           - Security (firewalls, IDS/IPS, access control)
           - Middleware (app servers, message queues)
        
        2. **Migration Priority** (High/Medium/Low):
           - High: Business critical, compliance requirements
           - Medium: Important but not critical
           - Low: Nice to have, legacy systems
        
        3. **Complexity Level** (Simple/Moderate/Complex):
           - Simple: Standalone, few dependencies
           - Moderate: Some dependencies, standard config
           - Complex: Many dependencies, custom config, integrations
        
        4. **Risk Assessment** (High/Medium/Low):
           - High: Business critical, compliance sensitive
           - Medium: Important but manageable impact
           - Low: Minimal business impact
        
        5. **Dependencies** (Yes/No + details):
           - Database connections
           - Network dependencies
           - Application integrations
        
        **Output Format:**
        For each asset:
        ASSET_INDEX: X
        NAME: [asset name]
        TYPE: [asset type]
        PRIORITY: [migration priority]
        COMPLEXITY: [complexity level]
        RISK: [risk level]
        DEPENDENCIES: [yes/no + details]
        CONFIDENCE: [0.0-1.0]
        
        Be specific and provide confidence scores.
        """
        
        return Task(
            description=description,
            agent=self.agents['asset_classifier'],
            expected_output="Detailed asset classifications with types, priorities, complexity, and confidence scores"
        )
    
    def _create_crew(self, agents: List[Any], tasks: List[Any], crew_name: str):
        """Create CrewAI crew with optimized settings."""
        from crewai import Crew, Process
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
            memory=False,  # Disabled for faster execution
            max_execution_time=max([
                self.config.timeout_data_validation,
                self.config.timeout_field_mapping,
                self.config.timeout_asset_classification
            ])
        )
    
    def _record_execution_metric(self, task_id: str, task_type: str, duration: float, status: str):
        """Record execution metrics for monitoring and optimization."""
        self.execution_metrics[task_id] = {
            "task_type": task_type,
            "duration_seconds": duration,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics and performance data."""
        if not self.execution_metrics:
            return {"total_tasks": 0, "metrics": {}}
        
        # Calculate aggregated metrics
        successful_tasks = [m for m in self.execution_metrics.values() if m["status"] == "success"]
        failed_tasks = [m for m in self.execution_metrics.values() if m["status"] in ["error", "timeout"]]
        
        total_duration = sum(m["duration_seconds"] for m in successful_tasks)
        avg_duration = total_duration / max(len(successful_tasks), 1)
        
        # Performance by task type
        task_type_metrics = {}
        for task_type in ["data_validation", "field_mapping", "asset_classification"]:
            type_tasks = [m for m in self.execution_metrics.values() if m["task_type"] == task_type]
            if type_tasks:
                type_successful = [m for m in type_tasks if m["status"] == "success"]
                task_type_metrics[task_type] = {
                    "total_executions": len(type_tasks),
                    "successful_executions": len(type_successful),
                    "success_rate": len(type_successful) / len(type_tasks),
                    "avg_duration": sum(m["duration_seconds"] for m in type_successful) / max(len(type_successful), 1)
                }
        
        return {
            "total_tasks": len(self.execution_metrics),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(self.execution_metrics),
            "total_duration_seconds": total_duration,
            "average_duration_seconds": avg_duration,
            "task_type_metrics": task_type_metrics,
            "recent_metrics": list(self.execution_metrics.values())[-10:]  # Last 10 tasks
        }
    
    def cleanup_metrics(self, max_age_hours: int = 24):
        """Clean up old execution metrics."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_task_ids = [
            task_id for task_id, metrics in self.execution_metrics.items()
            if datetime.fromisoformat(metrics["timestamp"]) < cutoff_time
        ]
        
        for task_id in old_task_ids:
            del self.execution_metrics[task_id]
        
        if old_task_ids:
            logger.info(f"Cleaned up {len(old_task_ids)} old execution metrics")
    
    def get_handler_summary(self) -> Dict[str, Any]:
        """Get execution handler summary."""
        return {
            "handler": "execution_handler",
            "version": "1.0.0",
            "available_agents": list(self.agents.keys()),
            "active_tasks": len(self.active_tasks),
            "total_executed_tasks": len(self.execution_metrics),
            "features": [
                "parallel_execution",
                "retry_logic",
                "timeout_management", 
                "performance_metrics",
                "error_handling"
            ],
            "configuration": {
                "retry_attempts": self.config.retry_attempts,
                "retry_wait_seconds": self.config.retry_wait_seconds,
                "timeouts": {
                    "data_validation": self.config.timeout_data_validation,
                    "field_mapping": self.config.timeout_field_mapping,
                    "asset_classification": self.config.timeout_asset_classification
                }
            }
        } 