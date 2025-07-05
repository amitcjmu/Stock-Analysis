"""
Field Mapping Executor
Handles field mapping phase execution for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any, List
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI Flow not available")


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
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute field mapping using CrewAI crew - now properly async"""
        crew = self.crew_manager.create_crew_on_demand(
            "attribute_mapping",
            **self._get_crew_context()
        )
        
        if not crew:
            logger.warning("Field mapping crew creation failed - using fallback")
            return await self.execute_fallback()
        
        # Execute crew (this is synchronous)
        crew_result = crew.kickoff(inputs=crew_input)
        logger.info(f"Field mapping crew completed: {type(crew_result)}")
        
        # Process crew results
        return self._process_field_mapping_results(crew_result)
    
    async def execute_fallback(self) -> Dict[str, Any]:
        """Execute field mapping using fallback logic - now properly async"""
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
            # Look for different mapping formats
            # Format 1: source_field -> target_attribute
            if '->' in line:
                parts = line.split('->')
                if len(parts) == 2:
                    source = parts[0].strip().strip('"\'').strip(':').strip()
                    target = parts[1].strip().strip('"\'').strip()
                    if source and target:
                        mappings[source] = target
            # Format 2: source_field: target_attribute
            elif ':' in line and not any(skip in line.lower() for skip in ['confidence', 'status', 'clarification', 'question']):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    source = parts[0].strip().strip('"\'').strip()
                    target = parts[1].strip().strip('"\'').strip()
                    # Skip if it looks like a sentence or instruction
                    if source and target and not ' ' in source.strip() and len(source) < 50:
                        mappings[source] = target
        
        # If no mappings found from the crew, use the fallback based on the raw data
        if not mappings and hasattr(self.state, 'raw_data') and self.state.raw_data:
            logger.info("🔄 No mappings extracted from crew result, using fallback pattern matching")
            fallback_result = self._generate_fallback_suggestions()
            mappings = fallback_result.get('mappings', {})
        
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
    
    async def execute_suggestions_only(self, previous_result) -> Dict[str, Any]:
        """Execute field mapping in suggestions-only mode - generates mappings and clarifications"""
        logger.info("🔍 Executing field mapping in suggestions-only mode")
        
        # Update state
        self.state.current_phase = self.get_phase_name()
        
        try:
            # Generate mapping suggestions
            if CREWAI_FLOW_AVAILABLE and self.crew_manager:
                # Use CrewAI crew for intelligent mapping
                crew_input = self._prepare_crew_input()
                crew_input["mode"] = "suggestions_only"
                crew_input["generate_clarifications"] = True
                
                crew = self.crew_manager.create_crew_on_demand(
                    "attribute_mapping",
                    **self._get_crew_context()
                )
                
                if crew:
                    logger.info("🤖 Using CrewAI crew for mapping suggestions")
                    crew_result = crew.kickoff(inputs=crew_input)
                    results = self._process_mapping_suggestions(crew_result)
                else:
                    logger.warning("Field mapping crew not available - using fallback suggestions")
                    results = self._generate_fallback_suggestions()
            else:
                # Use fallback suggestions
                results = self._generate_fallback_suggestions()
            
            # Extract mappings, clarifications, and confidence scores
            mappings = results.get("mappings", {})
            clarifications = results.get("clarifications", [])
            confidence_scores = results.get("confidence_scores", {})
            
            # Add default clarifications if none were generated
            if not clarifications and mappings:
                clarifications = self._generate_default_clarifications(mappings, confidence_scores)
            
            result = {
                "mappings": mappings,
                "clarifications": clarifications,
                "confidence_scores": confidence_scores,
                "suggestions_generated": True,
                "execution_metadata": {
                    "timestamp": self._get_timestamp(),
                    "method": "suggestions_only",
                    "crew_used": CREWAI_FLOW_AVAILABLE and self.crew_manager is not None
                }
            }
            
            # Debug: Log the result structure being returned
            logger.info(f"🔍 DEBUG: execute_suggestions_only returning: {result}")
            logger.info(f"🔍 DEBUG: Result keys: {list(result.keys())}")
            logger.info(f"🔍 DEBUG: Mappings count: {len(mappings)}")
            logger.info(f"🔍 DEBUG: Clarifications count: {len(clarifications)}")
            logger.info(f"🔍 DEBUG: Confidence scores count: {len(confidence_scores)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate mapping suggestions: {e}")
            # Return minimal suggestions on error
            return {
                "mappings": {},
                "clarifications": ["Unable to generate automatic mapping suggestions. Please map fields manually."],
                "confidence_scores": {},
                "suggestions_generated": False,
                "error": str(e)
            }
    
    def _process_mapping_suggestions(self, crew_result) -> Dict[str, Any]:
        """Process crew result for mapping suggestions"""
        # Debug logging
        logger.info(f"🔍 DEBUG: Processing crew_result type: {type(crew_result)}")
        logger.info(f"🔍 DEBUG: crew_result value: {crew_result}")
        
        base_result = self._process_crew_result(crew_result)
        logger.info(f"🔍 DEBUG: base_result: {base_result}")
        
        # Extract suggestions from crew result
        if isinstance(base_result.get('raw_result'), dict):
            return base_result['raw_result']
        else:
            # Parse text result for suggestions
            text_result = str(base_result.get('raw_result', ''))
            logger.info(f"🔍 DEBUG: text_result to parse: {text_result[:500]}")  # First 500 chars
            
            mappings = self._extract_mappings_from_text(text_result)
            clarifications = self._extract_clarifications_from_text(text_result)
            confidence_scores = self._calculate_confidence_scores(mappings)
            
            logger.info(f"🔍 DEBUG: Extracted mappings: {mappings}")
            logger.info(f"🔍 DEBUG: Extracted clarifications: {clarifications}")
            
            return {
                "mappings": mappings,
                "clarifications": clarifications,
                "confidence_scores": confidence_scores
            }
    
    def _generate_fallback_suggestions(self) -> Dict[str, Any]:
        """Generate fallback mapping suggestions with clarifications"""
        if not self.state.raw_data:
            return {
                "mappings": {},
                "clarifications": ["No data available for mapping. Please upload data first."],
                "confidence_scores": {}
            }
        
        # Get first record to analyze fields
        sample_record = self.state.raw_data[0]
        columns = list(sample_record.keys())
        
        # Enhanced mapping logic with confidence scoring
        mappings = {}
        confidence_scores = {}
        clarifications = []
        
        # Critical fields we need to map
        critical_fields = {
            'name': ['name', 'hostname', 'server_name', 'app_name', 'application_name'],
            'asset_type': ['type', 'category', 'asset_category', 'resource_type'],
            'environment': ['env', 'environment', 'stage', 'tier'],
            'ip_address': ['ip', 'ip_address', 'address', 'network_address'],
            'operating_system': ['os', 'operating_system', 'platform'],
            'location': ['location', 'datacenter', 'region', 'zone'],
            'criticality': ['criticality', 'priority', 'importance'],
            'owner': ['owner', 'contact', 'responsible_party']
        }
        
        # Map columns to critical fields
        unmapped_columns = []
        for column in columns:
            column_lower = column.lower()
            mapped = False
            
            for target_field, patterns in critical_fields.items():
                for pattern in patterns:
                    if pattern in column_lower:
                        mappings[column] = target_field
                        # Calculate confidence based on exact match vs partial match
                        if column_lower == pattern:
                            confidence_scores[column] = 0.9
                        else:
                            confidence_scores[column] = 0.7
                        mapped = True
                        break
                if mapped:
                    break
            
            if not mapped:
                # Keep unmapped fields for clarification
                unmapped_columns.append(column)
                mappings[column] = column  # Default to same name
                confidence_scores[column] = 0.3
        
        # Generate clarifications
        if unmapped_columns:
            clarifications.append(
                f"Unable to automatically map {len(unmapped_columns)} fields: {', '.join(unmapped_columns[:5])}{'...' if len(unmapped_columns) > 5 else ''}. "
                "Please review these mappings carefully."
            )
        
        # Check for missing critical fields
        mapped_targets = set(mappings.values())
        missing_critical = [field for field in ['name', 'asset_type', 'environment'] if field not in mapped_targets]
        if missing_critical:
            clarifications.append(
                f"Critical fields not mapped: {', '.join(missing_critical)}. "
                "Please ensure these fields are properly mapped for accurate asset discovery."
            )
        
        # Add data quality clarification
        sample_values = {col: str(sample_record.get(col, ''))[:50] for col in columns[:3]}
        clarifications.append(
            f"Sample data detected: {sample_values}. "
            "Please verify the mappings match your data structure."
        )
        
        return {
            "mappings": mappings,
            "clarifications": clarifications,
            "confidence_scores": confidence_scores
        }
    
    def _extract_clarifications_from_text(self, text: str) -> List[str]:
        """Extract clarification questions from text result"""
        clarifications = []
        
        # Look for question patterns
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in ['clarification:', 'question:', 'please confirm:', 'verify:']):
                clarifications.append(line)
            elif line.endswith('?'):
                clarifications.append(line)
        
        return clarifications
    
    def _calculate_confidence_scores(self, mappings: Dict[str, str]) -> Dict[str, float]:
        """Calculate confidence scores for mappings"""
        confidence_scores = {}
        
        for source, target in mappings.items():
            # Simple heuristic - exact match = high confidence
            if source.lower() == target.lower():
                confidence_scores[source] = 0.9
            elif target.lower() in source.lower() or source.lower() in target.lower():
                confidence_scores[source] = 0.7
            else:
                confidence_scores[source] = 0.5
        
        return confidence_scores
    
    def _generate_default_clarifications(self, mappings: Dict[str, str], confidence_scores: Dict[str, float]) -> List[str]:
        """Generate default clarification questions based on mappings"""
        clarifications = []
        
        # Count low confidence mappings
        low_confidence = [field for field, score in confidence_scores.items() if score < 0.7]
        if low_confidence:
            clarifications.append(
                f"We have low confidence in {len(low_confidence)} field mappings. "
                "Please review and confirm these mappings are correct."
            )
        
        # Check if we have minimum required fields
        mapped_targets = set(mappings.values())
        if 'name' not in mapped_targets:
            clarifications.append(
                "No field was mapped to 'name'. This is required to identify assets. "
                "Which field contains the asset names?"
            )
        
        if 'asset_type' not in mapped_targets:
            clarifications.append(
                "No field was mapped to 'asset_type'. "
                "Do you have a field that indicates whether assets are servers, applications, or devices?"
            )
        
        # General review request
        clarifications.append(
            f"We've suggested mappings for {len(mappings)} fields. "
            "Please review and adjust as needed before proceeding."
        )
        
        return clarifications 