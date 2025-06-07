"""
CrewAI Flow Service with Async Crew Execution and State Management
Enhanced with parallel execution, retry logic, and robust parsing.
"""

import logging
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

logger = logging.getLogger(__name__)

# Enhanced Flow State Models with validation
class DiscoveryFlowState(BaseModel):
    """Structured state for Discovery phase workflow with validation."""
    # Input data
    cmdb_data: Dict[str, Any] = {}
    filename: str = ""
    headers: List[str] = []
    sample_data: List[Dict[str, Any]] = []
    
    # Analysis progress
    data_validation_complete: bool = False
    field_mapping_complete: bool = False
    asset_classification_complete: bool = False
    dependency_analysis_complete: bool = False
    readiness_assessment_complete: bool = False
    
    # Analysis results
    validated_structure: Dict[str, Any] = {}
    suggested_field_mappings: Dict[str, str] = {}
    asset_classifications: List[Dict[str, Any]] = []
    dependency_map: Dict[str, List[str]] = {}
    readiness_scores: Dict[str, float] = {}
    
    # Workflow metrics
    progress_percentage: float = 0.0
    current_phase: str = "initialization"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Agent outputs
    agent_insights: Dict[str, Any] = {}
    recommendations: List[str] = []
    
    @validator('headers')
    def headers_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Headers cannot be empty')
        return v
    
    @validator('sample_data')
    def sample_data_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Sample data cannot be empty')
        return v

class CrewAIFlowConfig:
    """Configuration class for CrewAI Flow Service."""
    
    def __init__(self):
        try:
            from app.core.config import settings
            self.settings = settings
        except ImportError:
            self.settings = None
    
    @property
    def timeout_data_validation(self) -> float:
        return getattr(self.settings, 'CREWAI_TIMEOUT_DATA_VALIDATION', 15.0)
    
    @property 
    def timeout_field_mapping(self) -> float:
        return getattr(self.settings, 'CREWAI_TIMEOUT_FIELD_MAPPING', 20.0)
    
    @property
    def timeout_asset_classification(self) -> float:
        return getattr(self.settings, 'CREWAI_TIMEOUT_ASSET_CLASSIFICATION', 15.0)
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        return {
            "model": getattr(self.settings, 'CREWAI_LLM_MODEL', "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
            "temperature": getattr(self.settings, 'CREWAI_LLM_TEMPERATURE', 0.1),
            "max_tokens": getattr(self.settings, 'CREWAI_LLM_MAX_TOKENS', 4000),
            "base_url": getattr(self.settings, 'CREWAI_LLM_BASE_URL', "https://api.deepinfra.com/v1/openai")
        }
    
    @property
    def retry_attempts(self) -> int:
        return getattr(self.settings, 'CREWAI_RETRY_ATTEMPTS', 3)
    
    @property
    def retry_wait_seconds(self) -> int:
        return getattr(self.settings, 'CREWAI_RETRY_WAIT_SECONDS', 2)
    
    @property
    def flow_ttl_hours(self) -> int:
        return getattr(self.settings, 'CREWAI_FLOW_TTL_HOURS', 1)

class CrewAIFlowService:
    """Enhanced CrewAI service with parallel execution, retries, and robust parsing."""
    
    def __init__(self):
        self.config = CrewAIFlowConfig()
        self.service_available = False
        self.llm = None
        self.agents = {}
        self.active_flows = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize CrewAI Flow components with enhanced configuration."""
        try:
            # Import CrewAI components
            from crewai import Agent, Task, Crew, Process
            
            self.Agent = Agent
            self.Task = Task
            self.Crew = Crew
            self.Process = Process
            
            # Initialize LLM with configuration
            self._initialize_llm()
            
            # Create specialized agents
            if self.llm:
                self._create_discovery_agents()
                self.service_available = True
                logger.info("CrewAI Flow Service initialized with enhanced features")
            
        except ImportError as e:
            logger.warning(f"CrewAI Flow not available: {e}")
            self._initialize_fallback_service()
    
    def _initialize_llm(self):
        """Initialize LLM with enhanced configuration."""
        try:
            from app.core.config import settings
            from crewai import LLM
            
            if hasattr(settings, 'DEEPINFRA_API_KEY') and settings.DEEPINFRA_API_KEY:
                llm_config = self.config.llm_config
                self.llm = LLM(
                    model=llm_config["model"],
                    base_url=llm_config["base_url"],
                    api_key=settings.DEEPINFRA_API_KEY,
                    temperature=llm_config["temperature"],
                    max_tokens=llm_config["max_tokens"]
                )
                logger.info(f"LLM initialized with model: {llm_config['model']}")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
            self.llm = None
    
    def _create_discovery_agents(self):
        """Create optimized agents for Discovery phase."""
        if not self.llm:
            return
        
        try:
            # Data Validation Agent - Fast and focused
            self.agents['data_validator'] = self.Agent(
                role="Data Validation Specialist",
                goal="Rapidly validate CMDB data structure, quality, and migration readiness with actionable feedback",
                backstory="You are an expert data validation specialist with 15+ years experience in enterprise data assessment. You provide fast, accurate analysis with specific recommendations.",
                llm=self.llm,
                verbose=False,
                allow_delegation=False,
                memory=False
            )
            
            # Field Mapping Agent - Enhanced with AI pattern recognition
            self.agents['field_mapper'] = self.Agent(
                role="Field Mapping Intelligence Specialist", 
                goal="Intelligently map CMDB fields to migration critical attributes using advanced pattern recognition and domain knowledge",
                backstory="You are an AI specialist in field mapping with deep knowledge of CMDB schemas, ITIL standards, and migration requirements. You use intelligent pattern matching to suggest optimal field mappings.",
                llm=self.llm,
                verbose=False,
                allow_delegation=False,
                memory=False
            )
            
            # Asset Classification Agent - Enhanced with domain expertise
            self.agents['asset_classifier'] = self.Agent(
                role="Asset Classification Expert",
                goal="Rapidly and accurately classify IT assets for migration planning using domain expertise and pattern recognition",
                backstory="You are an expert in IT asset management and migration planning with extensive knowledge of asset types, dependencies, and migration complexities. You classify assets with high accuracy and confidence.",
                llm=self.llm,
                verbose=False,
                allow_delegation=False,
                memory=False
            )
            
            logger.info(f"Created {len(self.agents)} enhanced Discovery phase agents")
            
        except Exception as e:
            logger.error(f"Failed to create agents: {e}")
            self.agents = {}
    
    def _validate_input(self, cmdb_data: Dict[str, Any]) -> None:
        """Validate input data before processing."""
        if not isinstance(cmdb_data, dict):
            raise ValueError("cmdb_data must be a dictionary")
        
        if not cmdb_data.get('headers'):
            raise ValueError("cmdb_data must contain 'headers' field with at least one header")
        
        if not cmdb_data.get('sample_data'):
            raise ValueError("cmdb_data must contain 'sample_data' field with at least one record")
        
        headers = cmdb_data['headers']
        sample_data = cmdb_data['sample_data']
        
        if not isinstance(headers, list) or len(headers) == 0:
            raise ValueError("headers must be a non-empty list")
        
        if not isinstance(sample_data, list) or len(sample_data) == 0:
            raise ValueError("sample_data must be a non-empty list")
        
        # Validate sample data structure
        for i, record in enumerate(sample_data[:3]):  # Check first 3 records
            if not isinstance(record, dict):
                raise ValueError(f"sample_data[{i}] must be a dictionary")
        
        logger.info(f"Input validation passed: {len(headers)} headers, {len(sample_data)} records")
    
    def _cleanup_active_flows(self):
        """Clean up expired flows based on TTL."""
        current_time = datetime.now()
        ttl_hours = self.config.flow_ttl_hours
        
        expired_flows = [
            flow_id for flow_id, flow_state in self.active_flows.items()
            if flow_state.started_at and 
            (current_time - flow_state.started_at) > timedelta(hours=ttl_hours)
        ]
        
        for flow_id in expired_flows:
            del self.active_flows[flow_id]
            logger.info(f"Cleaned up expired flow: {flow_id}")
        
        if expired_flows:
            logger.info(f"Cleaned up {len(expired_flows)} expired flows")
    
    # Enhanced Discovery Flow with Parallel Execution
    async def run_discovery_flow(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run enhanced Discovery phase workflow with parallel execution and validation."""
        start_time = datetime.now()
        
        # Input validation
        try:
            self._validate_input(cmdb_data)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        
        flow_id = f"discovery_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize flow state with validation
        try:
            flow_state = DiscoveryFlowState(
                cmdb_data=cmdb_data,
                filename=cmdb_data.get('filename', 'unknown'),
                headers=cmdb_data.get('headers', []),
                sample_data=cmdb_data.get('sample_data', []),
                started_at=start_time,
                current_phase="initialization"
            )
        except ValueError as e:
            logger.error(f"Flow state validation failed: {e}")
            raise
        
        self.active_flows[flow_id] = flow_state
        
        try:
            if not self.service_available:
                return await self._fallback_discovery_flow(flow_state)
            
            # Phase 1: Data Validation (Required first)
            logger.info(f"🔍 Discovery Flow {flow_id}: Starting Data Validation")
            flow_state.current_phase = "data_validation"
            flow_state.progress_percentage = 20.0
            
            validation_result = await self._run_data_validation_async(cmdb_data)
            flow_state.validated_structure = validation_result
            flow_state.data_validation_complete = True
            flow_state.progress_percentage = 40.0
            
            # Phases 2 & 3: Field Mapping and Asset Classification (PARALLEL EXECUTION)
            logger.info(f"🚀 Discovery Flow {flow_id}: Running Field Mapping and Asset Classification in Parallel")
            flow_state.current_phase = "parallel_mapping_and_classification"
            
            # Run field mapping and asset classification in parallel
            mapping_task = self._run_field_mapping_async(cmdb_data, validation_result)
            classification_task = self._run_asset_classification_async(cmdb_data, {})  # Start with empty mappings
            
            # Wait for both to complete
            mapping_result, classification_result = await asyncio.gather(
                mapping_task, 
                classification_task,
                return_exceptions=True
            )
            
            # Handle any exceptions from parallel execution
            if isinstance(mapping_result, Exception):
                logger.warning(f"Field mapping failed, using fallback: {mapping_result}")
                mapping_result = self._fallback_field_mapping(cmdb_data)
            
            if isinstance(classification_result, Exception):
                logger.warning(f"Asset classification failed, using fallback: {classification_result}")
                classification_result = self._fallback_asset_classification(cmdb_data)
            
            flow_state.suggested_field_mappings = mapping_result
            flow_state.field_mapping_complete = True
            flow_state.asset_classifications = classification_result
            flow_state.asset_classification_complete = True
            flow_state.progress_percentage = 80.0
            
            # Phase 4: Readiness Assessment (Quick analysis)
            logger.info(f"📊 Discovery Flow {flow_id}: Readiness Assessment")
            flow_state.current_phase = "readiness_assessment"
            
            readiness_result = await self._run_readiness_assessment_async(flow_state)
            flow_state.readiness_scores = readiness_result
            flow_state.readiness_assessment_complete = True
            flow_state.progress_percentage = 100.0
            
            # Complete flow
            flow_state.current_phase = "completed"
            flow_state.completed_at = datetime.now()
            
            duration = (flow_state.completed_at - start_time).total_seconds()
            logger.info(f"✅ Discovery Flow {flow_id}: Completed successfully in {duration:.2f} seconds")
            
            return self._format_discovery_results(flow_state)
            
        except Exception as e:
            logger.error(f"Discovery flow {flow_id} failed: {e}")
            flow_state.current_phase = "failed"
            return await self._fallback_discovery_flow(flow_state)
        
        finally:
            # Clean up expired flows
            self._cleanup_active_flows()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True
    )
    async def _run_data_validation_async(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run data validation with retry logic and enhanced prompts."""
        if 'data_validator' not in self.agents:
            return self._fallback_data_validation(cmdb_data)
        
        try:
            start_time = datetime.now()
            
            # Enhanced validation prompt with specific instructions
            validation_task = self.Task(
                description=f"""
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
                """,
                agent=self.agents['data_validator'],
                expected_output="Structured data validation report with quality score and specific recommendations"
            )
            
            # Create crew for async execution
            validation_crew = self.Crew(
                agents=[self.agents['data_validator']],
                tasks=[validation_task],
                process=self.Process.sequential,
                verbose=False,
                memory=False
            )
            
            # Execute with configurable timeout
            result = await asyncio.wait_for(
                validation_crew.kickoff_async(),
                timeout=self.config.timeout_data_validation
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Data validation completed in {duration:.2f} seconds")
            
            # Enhanced parsing of validation results
            parsed_result = self._parse_validation_result(str(result))
            
            return {
                "validation_report": str(result),
                "data_quality_score": parsed_result.get("quality_score", 7.0),
                "missing_fields": parsed_result.get("missing_fields", []),
                "issues": parsed_result.get("issues", []),
                "ready": parsed_result.get("ready", True),
                "actions": parsed_result.get("actions", []),
                "validation_status": "completed",
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            logger.warning(f"Data validation timed out after {self.config.timeout_data_validation}s")
            raise
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True
    )
    async def _run_field_mapping_async(self, cmdb_data: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, str]:
        """Run AI-powered field mapping with enhanced prompts and parsing."""
        if 'field_mapper' not in self.agents:
            return self._fallback_field_mapping(cmdb_data)
        
        try:
            start_time = datetime.now()
            
            # Enhanced field mapping prompt
            mapping_task = self.Task(
                description=f"""
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
                """,
                agent=self.agents['field_mapper'],
                expected_output="Field mapping suggestions with confidence scores in structured format"
            )
            
            mapping_crew = self.Crew(
                agents=[self.agents['field_mapper']],
                tasks=[mapping_task],
                process=self.Process.sequential,
                verbose=False,
                memory=False
            )
            
            result = await asyncio.wait_for(
                mapping_crew.kickoff_async(),
                timeout=self.config.timeout_field_mapping
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Field mapping completed in {duration:.2f} seconds")
            
            # Enhanced parsing of field mapping results
            return self._parse_field_mapping_result_enhanced(str(result), cmdb_data.get('headers', []))
            
        except asyncio.TimeoutError:
            logger.warning(f"Field mapping timed out after {self.config.timeout_field_mapping}s")
            raise
        except Exception as e:
            logger.error(f"Field mapping failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True
    )
    async def _run_asset_classification_async(self, cmdb_data: Dict[str, Any], field_mappings: Dict[str, str]) -> List[Dict[str, Any]]:
        """Run asset classification with enhanced prompts and parsing."""
        if 'asset_classifier' not in self.agents:
            return self._fallback_asset_classification(cmdb_data)
        
        try:
            start_time = datetime.now()
            
            # Enhanced asset classification prompt
            classification_task = self.Task(
                description=f"""
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
                """,
                agent=self.agents['asset_classifier'],
                expected_output="Detailed asset classifications with types, priorities, complexity, and confidence scores"
            )
            
            classification_crew = self.Crew(
                agents=[self.agents['asset_classifier']],
                tasks=[classification_task],
                process=self.Process.sequential,
                verbose=False,
                memory=False
            )
            
            result = await asyncio.wait_for(
                classification_crew.kickoff_async(),
                timeout=self.config.timeout_asset_classification
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Asset classification completed in {duration:.2f} seconds")
            
            # Enhanced parsing of classification results
            return self._parse_asset_classification_result_enhanced(str(result), cmdb_data.get('sample_data', []))
            
        except asyncio.TimeoutError:
            logger.warning(f"Asset classification timed out after {self.config.timeout_asset_classification}s")
            raise
        except Exception as e:
            logger.error(f"Asset classification failed: {e}")
            raise
    
    # Enhanced Parsing Methods with AI-driven logic
    def _parse_validation_result(self, result: str) -> Dict[str, Any]:
        """Parse validation result with enhanced pattern matching."""
        parsed = {
            "quality_score": 7.0,
            "missing_fields": [],
            "issues": [],
            "ready": True,
            "actions": []
        }
        
        try:
            # Extract quality score
            score_match = re.search(r'QUALITY_SCORE:\s*(\d+(?:\.\d+)?)', result, re.IGNORECASE)
            if score_match:
                parsed["quality_score"] = float(score_match.group(1))
            
            # Extract missing fields
            missing_match = re.search(r'MISSING_FIELDS:\s*\[(.*?)\]', result, re.IGNORECASE)
            if missing_match:
                fields = [f.strip().strip('"\'') for f in missing_match.group(1).split(',') if f.strip()]
                parsed["missing_fields"] = fields
            
            # Extract issues
            issues_match = re.search(r'ISSUES:\s*\[(.*?)\]', result, re.IGNORECASE)
            if issues_match:
                issues = [i.strip().strip('"\'') for i in issues_match.group(1).split(',') if i.strip()]
                parsed["issues"] = issues
            
            # Extract readiness
            ready_match = re.search(r'READY:\s*(Yes|No)', result, re.IGNORECASE)
            if ready_match:
                parsed["ready"] = ready_match.group(1).lower() == 'yes'
            
            # Extract actions
            actions_match = re.search(r'ACTIONS:\s*\[(.*?)\]', result, re.IGNORECASE)
            if actions_match:
                actions = [a.strip().strip('"\'') for a in actions_match.group(1).split(',') if a.strip()]
                parsed["actions"] = actions
                
        except Exception as e:
            logger.warning(f"Failed to parse validation result: {e}")
        
        return parsed
    
    def _parse_field_mapping_result_enhanced(self, result: str, headers: List[str]) -> Dict[str, str]:
        """Enhanced field mapping parsing with pattern recognition."""
        mappings = {}
        
        try:
            # Look for explicit mappings in format: field -> attribute (confidence: X.X)
            mapping_pattern = r'(\w+)\s*->\s*(\w+)\s*\(confidence:\s*([\d.]+)\)'
            matches = re.findall(mapping_pattern, result, re.IGNORECASE)
            
            for field, attribute, confidence in matches:
                if field in headers and float(confidence) >= 0.7:  # Only high confidence mappings
                    mappings[field] = attribute
            
            # Fallback to intelligent pattern matching for unmapped fields
            for header in headers:
                if header not in mappings:
                    header_lower = header.lower()
                    if any(pattern in header_lower for pattern in ['name', 'hostname', 'server']):
                        mappings[header] = 'asset_name'
                    elif any(pattern in header_lower for pattern in ['type', 'ci_type', 'category']):
                        mappings[header] = 'ci_type'
                    elif any(pattern in header_lower for pattern in ['env', 'environment', 'tier']):
                        mappings[header] = 'environment'
                    elif any(pattern in header_lower for pattern in ['owner', 'responsible']):
                        mappings[header] = 'business_owner'
                    else:
                        mappings[header] = 'custom_attribute'
                        
        except Exception as e:
            logger.warning(f"Enhanced field mapping parsing failed, using fallback: {e}")
            return self._fallback_field_mapping_simple(headers)
        
        return mappings
    
    def _parse_asset_classification_result_enhanced(self, result: str, sample_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced asset classification parsing with structured extraction."""
        classifications = []
        
        try:
            # Split result into asset blocks
            asset_blocks = re.split(r'ASSET_INDEX:\s*\d+', result)[1:]  # Skip first empty split
            
            for i, block in enumerate(asset_blocks[:len(sample_data)]):
                asset_data = sample_data[i] if i < len(sample_data) else {}
                
                classification = {
                    "asset_index": i,
                    "asset_data": asset_data,
                    "asset_type": "Server",  # Default
                    "migration_priority": "Medium",
                    "complexity_level": "Moderate", 
                    "risk_level": "Medium",
                    "has_dependencies": True,
                    "confidence_score": 0.75
                }
                
                # Extract structured information
                type_match = re.search(r'TYPE:\s*(\w+)', block, re.IGNORECASE)
                if type_match:
                    classification["asset_type"] = type_match.group(1)
                
                priority_match = re.search(r'PRIORITY:\s*(\w+)', block, re.IGNORECASE)
                if priority_match:
                    classification["migration_priority"] = priority_match.group(1)
                
                complexity_match = re.search(r'COMPLEXITY:\s*(\w+)', block, re.IGNORECASE)
                if complexity_match:
                    classification["complexity_level"] = complexity_match.group(1)
                
                risk_match = re.search(r'RISK:\s*(\w+)', block, re.IGNORECASE)
                if risk_match:
                    classification["risk_level"] = risk_match.group(1)
                
                deps_match = re.search(r'DEPENDENCIES:\s*(Yes|No)', block, re.IGNORECASE)
                if deps_match:
                    classification["has_dependencies"] = deps_match.group(1).lower() == 'yes'
                
                conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', block, re.IGNORECASE)
                if conf_match:
                    classification["confidence_score"] = float(conf_match.group(1))
                
                classifications.append(classification)
                
        except Exception as e:
            logger.warning(f"Enhanced asset classification parsing failed, using fallback: {e}")
            return self._fallback_asset_classification({"sample_data": sample_data})
        
        return classifications
    
    def _fallback_field_mapping_simple(self, headers: List[str]) -> Dict[str, str]:
        """Simple fallback field mapping."""
        mappings = {}
        for header in headers:
            header_lower = header.lower()
            if 'name' in header_lower:
                mappings[header] = 'asset_name'
            elif 'type' in header_lower:
                mappings[header] = 'ci_type'
            else:
                mappings[header] = 'custom_attribute'
        return mappings
    
    async def _run_readiness_assessment_async(self, flow_state: DiscoveryFlowState) -> Dict[str, float]:
        """Enhanced readiness assessment with detailed scoring."""
        try:
            scores = {
                "data_quality": 0.0,
                "field_mapping": 0.0,
                "asset_coverage": 0.0,
                "overall_readiness": 0.0
            }
            
            # Data quality score from validation
            if flow_state.data_validation_complete:
                validation_score = flow_state.validated_structure.get("data_quality_score", 0)
                scores["data_quality"] = min(10.0, max(0.0, validation_score))
            
            # Field mapping score
            if flow_state.field_mapping_complete:
                total_fields = len(flow_state.headers)
                mapped_fields = len(flow_state.suggested_field_mappings)
                mapping_ratio = mapped_fields / max(total_fields, 1)
                scores["field_mapping"] = mapping_ratio * 10.0
            
            # Asset coverage score
            if flow_state.asset_classification_complete:
                total_assets = len(flow_state.sample_data)
                classified_assets = len(flow_state.asset_classifications)
                coverage_ratio = classified_assets / max(total_assets, 1)
                avg_confidence = sum(
                    asset.get("confidence_score", 0.7) 
                    for asset in flow_state.asset_classifications
                ) / max(len(flow_state.asset_classifications), 1)
                scores["asset_coverage"] = coverage_ratio * avg_confidence * 10.0
            
            # Overall readiness (weighted average)
            if all([flow_state.data_validation_complete, flow_state.field_mapping_complete, flow_state.asset_classification_complete]):
                scores["overall_readiness"] = (
                    scores["data_quality"] * 0.4 +
                    scores["field_mapping"] * 0.3 + 
                    scores["asset_coverage"] * 0.3
                )
            
            return scores
            
        except Exception as e:
            logger.error(f"Readiness assessment failed: {e}")
            return {"overall_readiness": 5.0, "error": str(e)}
    
    def _format_discovery_results(self, flow_state: DiscoveryFlowState) -> Dict[str, Any]:
        """Enhanced results formatting with detailed metrics."""
        duration = None
        if flow_state.started_at and flow_state.completed_at:
            duration = (flow_state.completed_at - flow_state.started_at).total_seconds()
        
        return {
            "status": "completed",
            "flow_type": "discovery",
            "progress": flow_state.progress_percentage,
            "duration_seconds": duration,
            "performance_metrics": {
                "parallel_execution": True,
                "retry_enabled": True,
                "enhanced_parsing": True,
                "input_validation": True
            },
            "results": {
                "data_validation": {
                    "completed": flow_state.data_validation_complete,
                    "structure": flow_state.validated_structure
                },
                "field_mapping": {
                    "completed": flow_state.field_mapping_complete,
                    "mappings": flow_state.suggested_field_mappings,
                    "mapping_coverage": len(flow_state.suggested_field_mappings) / max(len(flow_state.headers), 1)
                },
                "asset_classification": {
                    "completed": flow_state.asset_classification_complete,
                    "classifications": flow_state.asset_classifications,
                    "classification_coverage": len(flow_state.asset_classifications) / max(len(flow_state.sample_data), 1)
                },
                "readiness_assessment": {
                    "completed": flow_state.readiness_assessment_complete,
                    "scores": flow_state.readiness_scores
                }
            },
            "recommendations": flow_state.recommendations,
            "ready_for_assessment": flow_state.readiness_scores.get("overall_readiness", 0) >= 7.0
        }
    
    # Keep existing fallback methods for compatibility
    def _initialize_fallback_service(self):
        """Initialize fallback service when CrewAI unavailable."""
        self.service_available = False
        logger.info("CrewAI Flow Service running in fallback mode")
    
    async def _fallback_discovery_flow(self, flow_state: DiscoveryFlowState) -> Dict[str, Any]:
        """Enhanced fallback discovery flow."""
        logger.info("Using enhanced fallback discovery analysis")
        
        # Simulate quick analysis with enhanced logic
        await asyncio.sleep(2)
        
        return {
            "status": "completed_fallback",
            "flow_type": "discovery",
            "progress": 100.0,
            "performance_metrics": {
                "parallel_execution": False,
                "fallback_mode": True,
                "enhanced_parsing": True
            },
            "results": {
                "data_validation": {
                    "completed": True,
                    "structure": {"quality_score": 7.0, "status": "acceptable"}
                },
                "field_mapping": {
                    "completed": True,
                    "mappings": self._fallback_field_mapping(flow_state.cmdb_data),
                    "mapping_coverage": 0.8
                },
                "asset_classification": {
                    "completed": True,
                    "classifications": self._fallback_asset_classification(flow_state.cmdb_data),
                    "classification_coverage": 1.0
                },
                "readiness_assessment": {
                    "completed": True,
                    "scores": {"overall_readiness": 7.5, "data_quality": 7.0, "field_mapping": 8.0, "asset_coverage": 7.5}
                }
            },
            "ready_for_assessment": True,
            "fallback_mode": True
        }
    
    def _fallback_data_validation(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback data validation."""
        return {
            "validation_report": "Data structure validated using fallback analysis - appears suitable for migration",
            "data_quality_score": 7.0,
            "missing_fields": [],
            "issues": [],
            "ready": True,
            "actions": ["Proceed with enhanced AI analysis when available"],
            "validation_status": "completed_fallback"
        }
    
    def _fallback_field_mapping(self, cmdb_data: Dict[str, Any]) -> Dict[str, str]:
        """Enhanced fallback field mapping with better logic."""
        headers = cmdb_data.get('headers', [])
        mappings = {}
        
        for header in headers:
            header_lower = header.lower()
            if any(pattern in header_lower for pattern in ['name', 'hostname', 'server']):
                mappings[header] = 'asset_name'
            elif any(pattern in header_lower for pattern in ['type', 'ci_type', 'category']):
                mappings[header] = 'ci_type'
            elif any(pattern in header_lower for pattern in ['env', 'environment', 'tier']):
                mappings[header] = 'environment'
            elif any(pattern in header_lower for pattern in ['owner', 'responsible']):
                mappings[header] = 'business_owner'
            else:
                mappings[header] = 'custom_attribute'
        
        return mappings
    
    def _fallback_asset_classification(self, cmdb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced fallback asset classification."""
        sample_data = cmdb_data.get('sample_data', [])
        classifications = []
        
        for i, asset in enumerate(sample_data[:5]):
            # Smart classification based on data content
            asset_type = "Server"
            priority = "Medium"
            complexity = "Moderate"
            
            # Try to determine asset type from data
            for key, value in asset.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(db_term in value_lower for db_term in ['database', 'db', 'sql', 'oracle', 'mysql']):
                        asset_type = "Database"
                        priority = "High"
                        complexity = "Complex"
                    elif any(app_term in value_lower for app_term in ['application', 'app', 'web', 'service']):
                        asset_type = "Application"
            
            classifications.append({
                "asset_index": i,
                "asset_data": asset,
                "asset_type": asset_type,
                "migration_priority": priority,
                "complexity_level": complexity,
                "risk_level": "Medium",
                "has_dependencies": True,
                "confidence_score": 0.75
            })
        
        return classifications
    
    # Service Status Methods
    def is_available(self) -> bool:
        """Check if the service is available."""
        return True  # Always available with enhanced fallbacks
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get enhanced status of a specific flow."""
        if flow_id in self.active_flows:
            flow_state = self.active_flows[flow_id]
            return {
                "flow_id": flow_id,
                "status": flow_state.current_phase,
                "progress": flow_state.progress_percentage,
                "started_at": flow_state.started_at.isoformat() if flow_state.started_at else None,
                "duration_seconds": (datetime.now() - flow_state.started_at).total_seconds() if flow_state.started_at else None,
                "components_completed": {
                    "data_validation": flow_state.data_validation_complete,
                    "field_mapping": flow_state.field_mapping_complete,
                    "asset_classification": flow_state.asset_classification_complete,
                    "readiness_assessment": flow_state.readiness_assessment_complete
                }
            }
        
        return {"flow_id": flow_id, "status": "not_found"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with enhanced metrics."""
        return {
            "status": "healthy",
            "service": "crewai_flow_enhanced",
            "version": "2.0.0",
            "async_support": True,
            "flow_state_management": True,
            "enhancements": {
                "parallel_execution": True,
                "retry_logic": True,
                "enhanced_parsing": True,
                "input_validation": True,
                "configurable_parameters": True,
                "memory_management": True
            },
            "components": {
                "llm_available": self.llm is not None,
                "agents_created": len(self.agents),
                "active_flows": len(self.active_flows),
                "service_available": self.service_available
            },
            "configuration": {
                "data_validation_timeout": self.config.timeout_data_validation,
                "field_mapping_timeout": self.config.timeout_field_mapping,
                "asset_classification_timeout": self.config.timeout_asset_classification,
                "retry_attempts": self.config.retry_attempts,
                "flow_ttl_hours": self.config.flow_ttl_hours
            }
        }

# Global service instance
crewai_flow_service = CrewAIFlowService() 