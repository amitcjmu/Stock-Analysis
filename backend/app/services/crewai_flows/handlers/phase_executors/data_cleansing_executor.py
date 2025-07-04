"""
Data Cleansing Executor
Handles data cleansing phase execution for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class DataCleansingExecutor(BasePhaseExecutor):
    """
    Executes data cleansing phase for the Unified Discovery Flow.
    Cleans and validates data using CrewAI crew or fallback logic.
    """
    
    def get_phase_name(self) -> str:
        return "data_cleansing"
    
    def get_progress_percentage(self) -> float:
        return 33.3  # 2/6 phases
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("data_cleansing", **self._get_crew_context())
        if not crew:
            logger.warning("Data cleansing crew creation failed - using fallback")
            return await self.execute_fallback()
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    async def execute_fallback(self) -> Dict[str, Any]:
        raw_data_count = len(self.state.raw_data) if self.state.raw_data else 0
        logger.info(f"🔍 Data cleansing fallback: Processing {raw_data_count} raw records")
        
        result = {
            "cleaned_data": self.state.raw_data,
            "quality_metrics": {"fallback_used": True, "records_processed": raw_data_count}
        }
        
        logger.info(f"✅ Data cleansing fallback: Returning {len(result['cleaned_data'])} cleaned records")
        return result
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, 'field_mappings', {}),
            "cleansing_type": "comprehensive_data_cleansing"
        }
    
    def _store_results(self, results: Dict[str, Any]):
        # Handle crew result that comes from _process_crew_result
        cleaned_data = results.get("cleaned_data", [])
        
        # If we have a raw_result from crew execution, try to use fallback data
        if not cleaned_data and "raw_result" in results:
            logger.warning(f"⚠️ Crew result processing failed - using fallback data from state")
            # Use the original raw_data as cleaned_data since crew processing didn't return structured data
            cleaned_data = getattr(self.state, 'raw_data', [])
        
        logger.info(f"🔍 Storing data cleansing results: {len(cleaned_data)} cleaned records")
        
        self.state.cleaned_data = cleaned_data
        self.state.data_quality_metrics = results.get("quality_metrics", {})
        
        logger.info(f"✅ Data cleansing state updated: cleaned_data has {len(self.state.cleaned_data)} records")
    
    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process data cleansing crew result and extract cleaned data"""
        logger.info(f"🔍 Processing data cleansing crew result: {type(crew_result)}")
        
        # For data cleansing, we need to ensure the data flows through
        # The crew should ideally return structured data, but as a fallback
        # we use the raw_data as cleaned_data
        if hasattr(crew_result, 'raw') and crew_result.raw:
            logger.info(f"📄 Crew raw output: {crew_result.raw[:200]}...")
            
            # Try to parse JSON from crew output if it contains structured data
            import json
            try:
                if '{' in crew_result.raw and '}' in crew_result.raw:
                    # Try to extract JSON from the output
                    start = crew_result.raw.find('{')
                    end = crew_result.raw.rfind('}') + 1
                    json_str = crew_result.raw[start:end]
                    parsed_result = json.loads(json_str)
                    
                    if 'cleaned_data' in parsed_result or 'standardized_data' in parsed_result:
                        logger.info("✅ Found structured data in crew output")
                        return {
                            "cleaned_data": parsed_result.get('cleaned_data', parsed_result.get('standardized_data', [])),
                            "quality_metrics": parsed_result.get('quality_metrics', {}),
                            "raw_result": crew_result.raw
                        }
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from crew output: {e}")
            
            # Fallback: Use original raw_data as cleaned_data
            logger.warning("⚠️ Crew did not return structured data - using raw_data as cleaned_data")
            return {
                "cleaned_data": getattr(self.state, 'raw_data', []),
                "quality_metrics": {"fallback_used": True, "crew_output": crew_result.raw[:100]},
                "raw_result": crew_result.raw
            }
        
        # If crew_result is already a dict, return it
        elif isinstance(crew_result, dict):
            return crew_result
        
        # Last resort fallback
        else:
            logger.warning("⚠️ Unexpected crew result format - using raw_data as cleaned_data")
            return {
                "cleaned_data": getattr(self.state, 'raw_data', []),
                "quality_metrics": {"fallback_used": True, "unexpected_format": True},
                "raw_result": str(crew_result)
            } 