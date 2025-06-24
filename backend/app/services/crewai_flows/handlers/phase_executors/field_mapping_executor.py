"""
Field Mapping Executor
Handles field mapping phase execution for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class FieldMappingExecutor(BasePhaseExecutor):
    """
    Executes field mapping phase for the Unified Discovery Flow.
    Maps source fields to critical attributes using CrewAI crew or fallback logic.
    """
    
    def get_phase_name(self) -> str:
        """Get the name of this phase"""
        return "attribute_mapping"
    
    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes"""
        return 16.7  # 1/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute field mapping using CrewAI crew"""
        crew = self.crew_manager.create_crew_on_demand(
            "attribute_mapping",
            **self._get_crew_context()
        )
        
        crew_result = crew.kickoff(inputs=crew_input)
        logger.info(f"Field mapping crew completed: {type(crew_result)}")
        
        # Process crew results
        return self._process_field_mapping_results(crew_result)
    
    def execute_fallback(self) -> Dict[str, Any]:
        """Execute field mapping using fallback logic"""
        logger.warning("Field mapping crew not available - using fallback")
        return self._fallback_field_mapping()
    
    def _get_crew_context(self) -> Dict[str, Any]:
        """Get context data for crew creation"""
        context = super()._get_crew_context()
        context.update({
            "sample_data": self.state.raw_data[:5] if self.state.raw_data else [],
        })
        return context
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        return {
            "columns": list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
            "sample_data": self.state.raw_data[:5] if self.state.raw_data else [],
            "mapping_type": "comprehensive_field_mapping"
        }
    
    def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        self.state.field_mappings = results
    
    def _process_field_mapping_results(self, crew_result) -> Dict[str, Any]:
        """Process field mapping crew results"""
        base_result = self._process_crew_result(crew_result)
        
        # Extract field mappings from crew result
        if isinstance(base_result.get('raw_result'), dict):
            mappings = base_result['raw_result'].get('field_mappings', {})
        else:
            # Parse string result for mappings
            mappings = self._extract_mappings_from_text(str(base_result.get('raw_result', '')))
        
        return {
            "mappings": mappings,
            "validation_results": {
                "total_fields": len(mappings),
                "mapped_fields": len([k for k, v in mappings.items() if v]),
                "mapping_confidence": 0.8,  # Default confidence
                "fallback_used": False
            },
            "crew_execution": True,
            "execution_metadata": {
                "timestamp": self._get_timestamp(),
                "method": "crewai_field_mapping"
            }
        }
    
    def _fallback_field_mapping(self) -> Dict[str, Any]:
        """Fallback field mapping logic"""
        if not self.state.raw_data:
            return {
                "mappings": {},
                "validation_results": {
                    "total_fields": 0,
                    "mapped_fields": 0,
                    "mapping_confidence": 0.0,
                    "fallback_used": True
                }
            }
        
        # Get first record to analyze fields
        sample_record = self.state.raw_data[0]
        columns = list(sample_record.keys())
        
        # Simple mapping logic based on common field patterns
        mappings = {}
        for column in columns:
            column_lower = column.lower()
            if 'name' in column_lower or 'hostname' in column_lower:
                mappings[column] = 'name'
            elif 'type' in column_lower or 'category' in column_lower:
                mappings[column] = 'asset_type'
            elif 'env' in column_lower or 'environment' in column_lower:
                mappings[column] = 'environment'
            elif 'ip' in column_lower or 'address' in column_lower:
                mappings[column] = 'ip_address'
            elif 'os' in column_lower or 'operating' in column_lower:
                mappings[column] = 'operating_system'
            else:
                mappings[column] = column  # Default to same name
        
        return {
            "mappings": mappings,
            "validation_results": {
                "total_fields": len(columns),
                "mapped_fields": len(mappings),
                "mapping_confidence": 0.6,  # Lower confidence for fallback
                "fallback_used": True
            },
            "crew_execution": False,
            "execution_metadata": {
                "timestamp": self._get_timestamp(),
                "method": "fallback_field_mapping"
            }
        }
    
    def _extract_mappings_from_text(self, text: str) -> Dict[str, str]:
        """Extract field mappings from text result"""
        mappings = {}
        
        # Simple text parsing for mappings
        lines = text.split('\n')
        for line in lines:
            if ':' in line and '->' in line:
                parts = line.split('->')
                if len(parts) == 2:
                    source = parts[0].strip().strip('"\'')
                    target = parts[1].strip().strip('"\'')
                    mappings[source] = target
        
        return mappings
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO format string"""
        from datetime import datetime
        try:
            if hasattr(self.state, 'updated_at') and self.state.updated_at:
                if hasattr(self.state.updated_at, 'isoformat'):
                    return self.state.updated_at.isoformat()
                else:
                    # If it's already a string, return it
                    return str(self.state.updated_at)
            else:
                # Fallback to current time
                return datetime.utcnow().isoformat()
        except Exception:
            # Final fallback
            return datetime.utcnow().isoformat() 