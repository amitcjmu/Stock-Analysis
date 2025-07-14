"""
Field Mapping Executor
Handles field mapping phase execution for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any, List
from .base_phase_executor import BasePhaseExecutor
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# CrewAI Flow imports with dynamic availability detection
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from app.services.llm_config import get_crewai_llm
    CREWAI_FLOW_AVAILABLE = True
    logger.info("✅ CrewAI Flow and LLM imports available")
except ImportError as e:
    logger.warning(f"CrewAI Flow not available: {e}")
except Exception as e:
    logger.warning(f"CrewAI imports failed: {e}")


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
        # Get data from multiple possible sources
        raw_data = None
        if hasattr(self.state, 'raw_data') and self.state.raw_data:
            raw_data = self.state.raw_data
        elif hasattr(self.state, 'phase_data') and 'data_import' in self.state.phase_data:
            data_import_results = self.state.phase_data['data_import']
            if isinstance(data_import_results, dict):
                raw_data = (data_import_results.get('validated_data') or 
                           data_import_results.get('raw_data') or 
                           data_import_results.get('records'))
        
        context.update({
            "sample_data": raw_data[:5] if raw_data else [],
        })
        return context
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        # Get data from multiple possible sources
        raw_data = None
        
        # Try raw_data attribute first
        if hasattr(self.state, 'raw_data') and self.state.raw_data:
            raw_data = self.state.raw_data
        # Try phase_data
        elif hasattr(self.state, 'phase_data') and 'data_import' in self.state.phase_data:
            data_import_results = self.state.phase_data['data_import']
            if isinstance(data_import_results, dict):
                raw_data = (data_import_results.get('validated_data') or 
                           data_import_results.get('raw_data') or 
                           data_import_results.get('records'))
        
        return {
            "columns": list(raw_data[0].keys()) if raw_data and len(raw_data) > 0 else [],
            "sample_data": raw_data[:5] if raw_data else [],
            "mapping_type": "comprehensive_field_mapping"
        }
    
    def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        self.state.field_mappings = results
        
        # Update database field mappings with the results
        self._update_database_field_mappings(results)
    
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
        """Fallback field mapping logic using intelligent mapping patterns"""
        # Get data from multiple possible sources
        raw_data = None
        
        # Try raw_data attribute first
        if hasattr(self.state, 'raw_data') and self.state.raw_data:
            raw_data = self.state.raw_data
        # Try phase_data
        elif hasattr(self.state, 'phase_data') and 'data_import' in self.state.phase_data:
            data_import_results = self.state.phase_data['data_import']
            if isinstance(data_import_results, dict):
                raw_data = (data_import_results.get('validated_data') or 
                           data_import_results.get('raw_data') or 
                           data_import_results.get('records'))
        
        if not raw_data:
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
        sample_record = raw_data[0]
        columns = list(sample_record.keys())
        
        # Import intelligent mapping helper
        try:
            from app.api.v1.endpoints.data_import.field_mapping.utils.mapping_helpers import intelligent_field_mapping, calculate_mapping_confidence
            
            mappings = {}
            mapping_details = {}
            skipped_fields = []
            
            for column in columns:
                # Skip metadata fields
                skip_fields = ['row_index', 'index', 'row_number', 'record_number', 'id']
                if column.lower() in skip_fields:
                    skipped_fields.append(column)
                    continue
                
                # Use intelligent mapping
                suggested_target = intelligent_field_mapping(column)
                
                if suggested_target:
                    mappings[column] = suggested_target
                    confidence = calculate_mapping_confidence(column, suggested_target)
                    mapping_details[column] = {
                        "target": suggested_target,
                        "confidence": confidence,
                        "method": "fallback_pattern_matching",
                        "reasoning": f"Pattern-based mapping: '{column}' → '{suggested_target}' (confidence: {confidence:.2f})"
                    }
                else:
                    # No mapping found
                    mapping_details[column] = {
                        "target": None,
                        "confidence": 0.0,
                        "method": "fallback_unmapped",
                        "reasoning": f"No suitable mapping found for '{column}'"
                    }
            
            logger.info(f"Fallback mapping: processed {len(columns)} fields, mapped {len(mappings)}, skipped {len(skipped_fields)}")
            
            return {
                "mappings": mappings,
                "mapping_details": mapping_details,
                "validation_results": {
                    "total_fields": len(columns) - len(skipped_fields),
                    "mapped_fields": len(mappings),
                    "skipped_fields": skipped_fields,
                    "mapping_confidence": 0.6,  # Lower confidence for fallback
                    "fallback_used": True
                },
                "crew_execution": False,
                "execution_metadata": {
                    "timestamp": self._get_timestamp(),
                    "method": "fallback_intelligent_mapping"
                }
            }
            
        except ImportError:
            logger.warning("Intelligent mapping helper not available, using basic patterns")
            # Basic fallback if import fails
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
            
            return {
                "mappings": mappings,
                "validation_results": {
                    "total_fields": len(columns),
                    "mapped_fields": len(mappings),
                    "mapping_confidence": 0.5,  # Even lower confidence for basic fallback
                    "fallback_used": True
                },
                "crew_execution": False,
                "execution_metadata": {
                    "timestamp": self._get_timestamp(),
                    "method": "basic_fallback_mapping"
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
    
    def _update_database_field_mappings(self, results: Dict[str, Any]):
        """Update field mappings in the database based on phase results"""
        try:
            # Get data_import_id from state
            data_import_id = getattr(self.state, 'data_import_id', None)
            if not data_import_id:
                logger.warning("No data_import_id in state - cannot update field mappings")
                return
            
            # Get mappings and details from results
            mappings = results.get("mappings", {})
            mapping_details = results.get("mapping_details", {})
            crew_execution = results.get("crew_execution", False)
            fallback_used = results.get("validation_results", {}).get("fallback_used", False)
            
            # Create async task to update database
            async def update_mappings():
                try:
                    from app.core.database import AsyncSessionLocal
                    from app.models.data_import import ImportFieldMapping
                    from sqlalchemy import select, update
                    import uuid as uuid_pkg
                    
                    async with AsyncSessionLocal() as db:
                        # Convert data_import_id to UUID if needed
                        if isinstance(data_import_id, str):
                            import_uuid = uuid_pkg.UUID(data_import_id)
                        else:
                            import_uuid = data_import_id
                        
                        # Get existing field mappings
                        query = select(ImportFieldMapping).where(
                            ImportFieldMapping.data_import_id == import_uuid
                        )
                        result = await db.execute(query)
                        existing_mappings = result.scalars().all()
                        
                        updated_count = 0
                        
                        # Update each mapping based on the results
                        for mapping_record in existing_mappings:
                            source_field = mapping_record.source_field
                            
                            # Check if we have a mapping for this field
                            if source_field in mappings:
                                new_target = mappings[source_field]
                                
                                # Get details if available
                                details = mapping_details.get(source_field, {})
                                confidence = details.get("confidence", 0.7)
                                reasoning = details.get("reasoning", "")
                                
                                # Update the mapping
                                mapping_record.target_field = new_target
                                mapping_record.confidence_score = confidence
                                mapping_record.match_type = "agent" if crew_execution else "intelligent"
                                mapping_record.transformation_rules = {
                                    "method": "agent_mapping" if crew_execution else "pattern_mapping",
                                    "reasoning": reasoning,
                                    "crew_execution": crew_execution,
                                    "fallback_used": fallback_used,
                                    "updated_at": datetime.utcnow().isoformat()
                                }
                                
                                updated_count += 1
                            elif source_field in mapping_details:
                                # Field was analyzed but no mapping found
                                details = mapping_details[source_field]
                                
                                mapping_record.target_field = "UNMAPPED"
                                mapping_record.confidence_score = 0.0
                                mapping_record.match_type = "unmapped"
                                mapping_record.transformation_rules = {
                                    "method": "no_mapping_found",
                                    "reasoning": details.get("reasoning", "No suitable mapping found"),
                                    "crew_execution": crew_execution,
                                    "fallback_used": fallback_used,
                                    "updated_at": datetime.utcnow().isoformat()
                                }
                                
                                updated_count += 1
                        
                        await db.commit()
                        logger.info(f"✅ Updated {updated_count} field mappings in database (agent: {crew_execution}, fallback: {fallback_used})")
                        
                except Exception as e:
                    logger.error(f"Failed to update field mappings in database: {e}")
            
            # Run the async update in the background
            asyncio.create_task(update_mappings())
            
        except Exception as e:
            logger.error(f"Error setting up field mapping database update: {e}")
    
    async def execute_suggestions_only(self, previous_result) -> Dict[str, Any]:
        """Execute field mapping in suggestions-only mode - generates mappings and clarifications"""
        logger.info("🔍 Executing field mapping in suggestions-only mode")
        logger.info(f"🔍 DEBUG: Previous result: {previous_result}")
        logger.info(f"🔍 DEBUG: State raw_data: {len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0} records")
        
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
                    try:
                        crew_result = crew.kickoff(inputs=crew_input)
                        results = self._process_mapping_suggestions(crew_result)
                    except Exception as crew_error:
                        logger.error(f"❌ Crew execution failed: {crew_error}")
                        error_msg = str(crew_error)
                        if "RateLimitError" in error_msg or "rate limit" in error_msg.lower():
                            logger.warning("⚠️ LLM rate limit hit during crew execution - using fallback")
                            results = await self._generate_fallback_suggestions()
                        else:
                            raise  # Re-raise non-rate-limit errors
                else:
                    logger.warning("Field mapping crew not available - using fallback suggestions")
                    results = await self._generate_fallback_suggestions()
            else:
                # Use fallback suggestions
                results = await self._generate_fallback_suggestions()
            
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
            
            # Check if it's a rate limit error
            error_msg = str(e)
            if "RateLimitError" in error_msg or "rate limit" in error_msg.lower():
                logger.warning("⚠️ LLM rate limit hit - falling back to rule-based mapping")
                # Use fallback suggestions without AI
                return await self._generate_fallback_suggestions()
            
            # For other errors, return minimal suggestions
            return {
                "mappings": {},
                "clarifications": ["Unable to generate automatic mapping suggestions. Please map fields manually."],
                "confidence_scores": {},
                "suggestions_generated": False,
                "error": error_msg
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
    
    async def _generate_fallback_suggestions(self) -> Dict[str, Any]:
        """Generate fallback mapping suggestions with clarifications"""
        # Debug logging
        logger.info(f"🔍 DEBUG: _generate_fallback_suggestions called")
        logger.info(f"🔍 DEBUG: self.state type: {type(self.state)}")
        logger.info(f"🔍 DEBUG: Has raw_data attr: {hasattr(self.state, 'raw_data')}")
        if hasattr(self.state, 'raw_data'):
            logger.info(f"🔍 DEBUG: raw_data type: {type(self.state.raw_data)}, length: {len(self.state.raw_data) if self.state.raw_data else 'None'}")
        
        # Try to get data from multiple sources
        raw_data = None
        
        # First try raw_data attribute
        if hasattr(self.state, 'raw_data') and self.state.raw_data:
            raw_data = self.state.raw_data
            logger.info(f"✅ Found raw_data in state: {len(raw_data)} records")
        
        # If not found, check phase_data for imported data
        elif hasattr(self.state, 'phase_data') and 'data_import' in self.state.phase_data:
            data_import_results = self.state.phase_data['data_import']
            logger.info(f"🔍 DEBUG: Data import phase_data available: {list(data_import_results.keys()) if isinstance(data_import_results, dict) else 'Not a dict'}")
            
            if isinstance(data_import_results, dict):
                # Try validated_data first
                if 'validated_data' in data_import_results and data_import_results['validated_data']:
                    raw_data = data_import_results['validated_data']
                    logger.info(f"✅ Found validated_data in phase_data: {len(raw_data)} records")
                # Then try raw_data
                elif 'raw_data' in data_import_results and data_import_results['raw_data']:
                    raw_data = data_import_results['raw_data']
                    logger.info(f"✅ Found raw_data in phase_data: {len(raw_data)} records")
                # Then try records
                elif 'records' in data_import_results and data_import_results['records']:
                    raw_data = data_import_results['records']
                    logger.info(f"✅ Found records in phase_data: {len(raw_data)} records")
        
        # Last resort: try to fetch data directly from database using data_import_id
        if not raw_data and hasattr(self.state, 'data_import_id') and self.state.data_import_id:
            logger.warning("⚠️ No raw_data in state, trying to fetch from database using data_import_id")
            try:
                raw_data = await self._fetch_raw_data_from_database(self.state.data_import_id)
                if raw_data:
                    logger.info(f"✅ Fetched raw_data from database: {len(raw_data)} records")
            except Exception as db_error:
                logger.error(f"❌ Failed to fetch raw_data from database: {db_error}")
        
        if not raw_data:
            logger.error("⚠️ No raw_data available in state for field mapping")
            logger.error(f"⚠️ State contents: {dir(self.state)}")
            if hasattr(self.state, '__dict__'):
                logger.error(f"⚠️ State attributes: {self.state.__dict__}")
            
            # Instead of returning a fallback, raise an error so the issue is visible
            raise ValueError("No raw CSV data available for field mapping. The flow state is missing the imported data. This indicates a data linkage issue between the flow and data import.")
        
        # Get first record to analyze fields
        sample_record = raw_data[0]
        columns = list(sample_record.keys())
        
        logger.info(f"🔍 Analyzing {len(columns)} columns from imported data: {columns}")
        
        # Enhanced mapping logic with confidence scoring
        mappings = {}
        confidence_scores = {}
        clarifications = []
        
        # Critical fields we need to map - expanded list
        critical_fields = {
            'name': ['name', 'hostname', 'server_name', 'app_name', 'application_name', 'asset_name'],
            'asset_type': ['type', 'category', 'asset_category', 'resource_type', 'asset_class'],
            'environment': ['env', 'environment', 'stage', 'tier', 'deployment_env'],
            'ip_address': ['ip', 'ip_address', 'address', 'network_address', 'private_ip', 'public_ip'],
            'operating_system': ['os', 'operating_system', 'platform', 'os_name', 'os_version'],
            'location': ['location', 'datacenter', 'region', 'zone', 'data_center', 'availability_zone'],
            'criticality': ['criticality', 'priority', 'importance', 'business_criticality', 'tier'],
            'owner': ['owner', 'contact', 'responsible_party', 'business_owner', 'technical_owner'],
            'status': ['status', 'state', 'operational_status', 'lifecycle_status'],
            'cost_center': ['cost_center', 'costcenter', 'cost_centre', 'department', 'business_unit'],
            'cpu_cores': ['cpu', 'cores', 'cpu_cores', 'vcpu', 'processors'],
            'memory_gb': ['memory', 'ram', 'memory_gb', 'mem_gb', 'total_memory'],
            'storage_gb': ['storage', 'disk', 'storage_gb', 'disk_space', 'total_storage'],
            'version': ['version', 'app_version', 'software_version', 'release'],
            'dependencies': ['dependencies', 'depends_on', 'requires', 'upstream'],
            'port': ['port', 'ports', 'service_port', 'listening_port'],
            'protocol': ['protocol', 'network_protocol', 'service_protocol'],
            'database': ['database', 'db', 'db_name', 'database_name'],
            'tech_stack': ['tech_stack', 'technology', 'stack', 'framework', 'platform']
        }
        
        # First, try to map columns to critical fields
        unmapped_columns = []
        for column in columns:
            column_lower = column.lower().replace('_', ' ').replace('-', ' ')
            mapped = False
            
            for target_field, patterns in critical_fields.items():
                for pattern in patterns:
                    pattern_normalized = pattern.lower().replace('_', ' ').replace('-', ' ')
                    if pattern_normalized in column_lower or column_lower in pattern_normalized:
                        mappings[column] = target_field
                        # Calculate confidence based on exact match vs partial match
                        if column_lower == pattern_normalized:
                            confidence_scores[column] = 0.9
                        else:
                            confidence_scores[column] = 0.7
                        mapped = True
                        break
                if mapped:
                    break
            
            if not mapped:
                # For unmapped fields, use the original column name as the target
                # This ensures ALL fields are included in the mapping
                unmapped_columns.append(column)
                mappings[column] = column  # Keep original name
                confidence_scores[column] = 0.5  # Medium confidence for unmapped fields
        
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
    
    async def _fetch_raw_data_from_database(self, data_import_id: str) -> List[Dict[str, Any]]:
        """Fetch raw data directly from database using data_import_id"""
        try:
            from app.models.data_import import RawImportRecord
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                # Query raw import records
                query = select(RawImportRecord.raw_data).where(
                    RawImportRecord.data_import_id == data_import_id
                )
                result = await db.execute(query)
                records = result.scalars().all()
                
                if records:
                    logger.info(f"✅ Found {len(records)} raw records in database")
                    return [record for record in records if record]
                else:
                    logger.warning(f"⚠️ No raw records found for data_import_id: {data_import_id}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error fetching raw data from database: {e}")
            return []
    
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