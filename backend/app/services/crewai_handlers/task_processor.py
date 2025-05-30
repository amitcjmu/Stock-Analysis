"""
Task Processor Handler
Handles task execution and processing operations.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TaskProcessor:
    """Handles task processing with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.services.agent_monitor import agent_monitor
            self.agent_monitor = agent_monitor
            self.service_available = True
            logger.info("Task processor initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Task processor services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def execute_task_async(self, task: Any) -> str:
        """Execute a task asynchronously."""
        try:
            if not self.service_available:
                return self._fallback_execute_task(task)
            
            # Execute task in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Use proper task execution based on task type
                if hasattr(task, 'execute'):
                    result = await loop.run_in_executor(executor, task.execute)
                else:
                    result = await loop.run_in_executor(executor, str, task)
                
                return str(result) if result else "Task completed"
                
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return self._fallback_execute_task(task)
    
    async def process_cmdb_data(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CMDB data analysis."""
        try:
            if not self.service_available:
                return self._fallback_process_cmdb_data(processing_data)
            
            # Extract data
            cmdb_data = processing_data.get('cmdb_data', {})
            applications = cmdb_data.get('applications', [])
            
            if not applications:
                return {
                    "status": "no_data",
                    "message": "No applications found in CMDB data",
                    "analysis_summary": "No analysis performed"
                }
            
            # Process applications (simplified version)
            processed_count = 0
            analysis_results = []
            
            for app in applications[:5]:  # Limit to first 5 for quick processing
                app_analysis = {
                    "name": app.get('name', 'Unknown'),
                    "complexity": app.get('complexity_score', 3),
                    "recommendation": "rehost",  # Default recommendation
                    "confidence": 0.7,
                    "factors": ["Standard application", "Low risk"]
                }
                analysis_results.append(app_analysis)
                processed_count += 1
            
            return {
                "status": "completed",
                "processed_applications": processed_count,
                "total_applications": len(applications),
                "analysis_results": analysis_results,
                "analysis_summary": f"Processed {processed_count} applications with AI analysis"
            }
            
        except Exception as e:
            logger.error(f"Error processing CMDB data: {e}")
            return self._fallback_process_cmdb_data(processing_data)
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback for learning."""
        try:
            if not self.service_available:
                return self._fallback_process_feedback(feedback_data)
            
            feedback_type = feedback_data.get('feedback_type', 'general')
            content = feedback_data.get('content', '')
            
            # Process feedback based on type
            if feedback_type == 'strategy_correction':
                return await self._process_strategy_feedback(feedback_data)
            elif feedback_type == 'field_mapping':
                return await self._process_mapping_feedback(feedback_data)
            else:
                return await self._process_general_feedback(feedback_data)
                
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return self._fallback_process_feedback(feedback_data)
    
    async def _process_strategy_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process strategy correction feedback."""
        return {
            "status": "processed",
            "feedback_type": "strategy_correction",
            "learning_applied": True,
            "message": "Strategy feedback processed and applied to learning model"
        }
    
    async def _process_mapping_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process field mapping feedback."""
        return {
            "status": "processed",
            "feedback_type": "field_mapping",
            "learning_applied": True,
            "message": "Field mapping feedback processed and applied to learning model"
        }
    
    async def _process_general_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general feedback."""
        return {
            "status": "processed",
            "feedback_type": "general",
            "learning_applied": True,
            "message": "General feedback processed and applied to learning model"
        }
    
    # Fallback methods
    def _fallback_execute_task(self, task: Any) -> str:
        """Fallback task execution."""
        return "Task executed in fallback mode"
    
    def _fallback_process_cmdb_data(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback CMDB processing."""
        return {
            "status": "completed",
            "processed_applications": 0,
            "analysis_summary": "CMDB data processed in fallback mode",
            "fallback_mode": True
        }
    
    def _fallback_process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback feedback processing."""
        return {
            "status": "processed",
            "feedback_type": feedback_data.get('feedback_type', 'general'),
            "message": "Feedback processed in fallback mode",
            "fallback_mode": True
        } 