# Phase 2 - Agent D1: Tool System Implementation

## Context
You are part of Phase 2 remediation effort to transform the AI Force Migration Platform to proper CrewAI architecture. This is Track D focusing on implementing a comprehensive tool system with auto-discovery, context awareness, and proper agent-tool integration.

### Required Reading Before Starting
- `docs/planning/PHASE-2-REMEDIATION-PLAN.md` - Phase 2 objectives
- `AGENT_A1_AGENT_SYSTEM_CORE.md` - Agent infrastructure
- `AGENT_C1_CONTEXT_MANAGEMENT.md` - Context patterns
- CrewAI documentation on Tools

### Prerequisites
- Agent registry from Track A
- Context management from Track C
- Basic understanding of CrewAI tool patterns

### Phase 2 Goal
Create a robust tool system that provides reusable, context-aware tools for all CrewAI agents. Implement auto-discovery, proper tool-agent relationships, and ensure all tools respect multi-tenant boundaries.

## Your Specific Tasks

### 1. Create Tool Registry with Auto-Discovery
**File to create**: `backend/app/services/tools/registry.py`

```python
"""
Central Tool Registry with auto-discovery
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any, Set
from dataclasses import dataclass
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolMetadata:
    """Metadata for registered tools"""
    name: str
    description: str
    tool_class: Type[BaseTool]
    categories: List[str]
    required_params: List[str]
    optional_params: List[str]
    context_aware: bool = True
    async_tool: bool = False

class ToolRegistry:
    """
    Central registry for all CrewAI tools with auto-discovery.
    Features:
    - Automatic tool discovery on startup
    - Category-based tool organization
    - Dynamic tool instantiation
    - Parameter validation
    """
    
    _instance = None
    _tools: Dict[str, ToolMetadata] = {}
    _categories: Dict[str, Set[str]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.discover_tools()
    
    def discover_tools(self) -> None:
        """Auto-discover all tools in the tools directory"""
        tools_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(tools_dir):
            if filename.endswith('_tool.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(
                        f'.{module_name}', 
                        package='app.services.tools'
                    )
                    
                    # Find all Tool subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseTool) and 
                            obj != BaseTool and
                            hasattr(obj, 'tool_metadata')):
                            
                            metadata = obj.tool_metadata()
                            self.register_tool(metadata)
                            logger.info(f"Discovered tool: {metadata.name}")
                            
                except Exception as e:
                    logger.error(f"Failed to load tool module {module_name}: {e}")
    
    def register_tool(self, metadata: ToolMetadata) -> None:
        """Register a tool with the registry"""
        self._tools[metadata.name] = metadata
        
        # Update category index
        for category in metadata.categories:
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(metadata.name)
    
    def get_tool(
        self, 
        name: str,
        **kwargs
    ) -> Optional[BaseTool]:
        """Get an instantiated tool by name"""
        if name not in self._tools:
            logger.error(f"Tool {name} not found in registry")
            return None
        
        metadata = self._tools[name]
        
        try:
            # Validate required parameters
            missing_params = [
                param for param in metadata.required_params 
                if param not in kwargs
            ]
            if missing_params:
                raise ValueError(f"Missing required parameters: {missing_params}")
            
            # Instantiate tool
            tool = metadata.tool_class(**kwargs)
            logger.debug(f"Instantiated tool: {name}")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to instantiate tool {name}: {e}")
            return None
    
    def get_tools_by_category(self, category: str) -> List[ToolMetadata]:
        """Get all tools in a category"""
        tool_names = self._categories.get(category, set())
        return [self._tools[name] for name in tool_names]
    
    def get_tools_for_agent(self, required_tools: List[str]) -> List[BaseTool]:
        """Get instantiated tools for an agent"""
        tools = []
        for tool_name in required_tools:
            tool = self.get_tool(tool_name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Required tool {tool_name} not available")
        return tools
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """List all tool categories"""
        return list(self._categories.keys())

# Global registry instance
tool_registry = ToolRegistry()
```

### 2. Create Base Tool Classes
**File to create**: `backend/app/services/tools/base_tool.py`

```python
"""
Base tool classes for CrewAI integration
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional, Type
from crewai.tools import BaseTool
from pydantic import Field
from app.core.context_aware import ContextAwareTool
from app.services.tools.registry import ToolMetadata
import logging

logger = logging.getLogger(__name__)

class BaseDiscoveryTool(BaseTool, ContextAwareTool):
    """
    Base class for all discovery tools.
    Provides:
    - CrewAI tool integration
    - Context awareness
    - Standard error handling
    - Metadata registration
    """
    
    # Tool configuration
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    
    def __init__(self, **kwargs):
        """Initialize with both CrewAI and context awareness"""
        # Initialize CrewAI tool
        BaseTool.__init__(self)
        # Initialize context awareness
        ContextAwareTool.__init__(self, **kwargs)
    
    @classmethod
    @abstractmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        raise NotImplementedError("Each tool must define its metadata")
    
    def _run(self, *args, **kwargs) -> Any:
        """Execute tool with context and error handling"""
        try:
            self.log_with_context(
                'info', 
                f"Executing tool {self.name}",
                tool_params=kwargs
            )
            
            # Ensure context is available
            if not self.context:
                raise ValueError("No context available for tool execution")
            
            # Execute tool logic
            result = self.run(*args, **kwargs)
            
            self.log_with_context(
                'info',
                f"Tool {self.name} completed successfully"
            )
            
            return result
            
        except Exception as e:
            self.log_with_context(
                'error',
                f"Tool {self.name} failed: {e}",
                error_type=type(e).__name__
            )
            raise
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Implement tool logic in subclasses"""
        pass

class AsyncBaseDiscoveryTool(BaseDiscoveryTool):
    """Base class for async tools"""
    
    async def _arun(self, *args, **kwargs) -> Any:
        """Async execution wrapper"""
        try:
            self.log_with_context(
                'info',
                f"Executing async tool {self.name}",
                tool_params=kwargs
            )
            
            # Ensure context is available
            if not self.context:
                raise ValueError("No context available for tool execution")
            
            # Execute async tool logic
            result = await self.arun(*args, **kwargs)
            
            self.log_with_context(
                'info',
                f"Async tool {self.name} completed successfully"
            )
            
            return result
            
        except Exception as e:
            self.log_with_context(
                'error',
                f"Async tool {self.name} failed: {e}",
                error_type=type(e).__name__
            )
            raise
    
    @abstractmethod
    async def arun(self, *args, **kwargs) -> Any:
        """Implement async tool logic in subclasses"""
        pass
    
    def run(self, *args, **kwargs) -> Any:
        """Sync wrapper for async tools"""
        import asyncio
        return asyncio.run(self.arun(*args, **kwargs))
```

### 3. Implement Core Tools

#### Schema Analyzer Tool
**File to create**: `backend/app/services/tools/schema_analyzer_tool.py`

```python
"""
Schema Analyzer Tool for data structure analysis
"""

from typing import Dict, Any, List
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from app.core.database_context import get_context_db
from sqlalchemy import select, inspect
from app.models import RawImportRecord
import json

class SchemaAnalyzerTool(AsyncBaseDiscoveryTool):
    """Analyzes data schema and structure"""
    
    name: str = "schema_analyzer"
    description: str = "Analyze data schema, types, patterns, and quality"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="schema_analyzer",
            description="Comprehensive schema and data structure analysis",
            tool_class=cls,
            categories=["analysis", "validation", "data_quality"],
            required_params=[],
            optional_params=["import_id", "sample_size"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self, 
        import_id: str,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze schema of imported data.
        
        Args:
            import_id: ID of the data import to analyze
            sample_size: Number of records to sample
            
        Returns:
            Schema analysis with field characteristics
        """
        async with get_context_db() as db:
            # Get sample records
            result = await db.execute(
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == import_id)
                .limit(sample_size)
            )
            records = result.scalars().all()
            
            if not records:
                return {"error": "No records found for import"}
            
            # Analyze schema
            schema_analysis = {}
            
            for record in records:
                data = json.loads(record.raw_data) if isinstance(record.raw_data, str) else record.raw_data
                
                for field, value in data.items():
                    if field not in schema_analysis:
                        schema_analysis[field] = {
                            "field_name": field,
                            "data_types": set(),
                            "null_count": 0,
                            "unique_values": set(),
                            "min_length": float('inf'),
                            "max_length": 0,
                            "patterns": set(),
                            "sample_values": []
                        }
                    
                    field_info = schema_analysis[field]
                    
                    # Analyze value
                    if value is None:
                        field_info["null_count"] += 1
                    else:
                        # Data type
                        field_info["data_types"].add(type(value).__name__)
                        
                        # Unique values (limit to prevent memory issues)
                        if len(field_info["unique_values"]) < 100:
                            field_info["unique_values"].add(str(value))
                        
                        # String analysis
                        if isinstance(value, str):
                            field_info["min_length"] = min(
                                field_info["min_length"], 
                                len(value)
                            )
                            field_info["max_length"] = max(
                                field_info["max_length"], 
                                len(value)
                            )
                            
                            # Pattern detection
                            if value.isdigit():
                                field_info["patterns"].add("numeric_string")
                            if '@' in value:
                                field_info["patterns"].add("email_like")
                            if '-' in value and len(value.split('-')) == 3:
                                field_info["patterns"].add("date_like")
                        
                        # Sample values
                        if len(field_info["sample_values"]) < 5:
                            field_info["sample_values"].append(value)
            
            # Convert sets to lists for JSON serialization
            for field_info in schema_analysis.values():
                field_info["data_types"] = list(field_info["data_types"])
                field_info["unique_values"] = list(field_info["unique_values"])[:20]
                field_info["patterns"] = list(field_info["patterns"])
                field_info["null_percentage"] = (
                    field_info["null_count"] / len(records) * 100
                )
                field_info["unique_count"] = len(field_info["unique_values"])
                
                # Clean up infinity values
                if field_info["min_length"] == float('inf'):
                    field_info["min_length"] = 0
            
            return {
                "import_id": import_id,
                "records_analyzed": len(records),
                "field_count": len(schema_analysis),
                "schema": schema_analysis
            }
```

#### Field Matcher Tool
**File to create**: `backend/app/services/tools/field_matcher_tool.py`

```python
"""
Field Matcher Tool for intelligent field mapping
"""

from typing import Dict, Any, List, Tuple
from app.services.tools.base_tool import BaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from difflib import SequenceMatcher
import re

class FieldMatcherTool(BaseDiscoveryTool):
    """Matches source fields to target fields using various algorithms"""
    
    name: str = "field_matcher"
    description: str = "Match source fields to target fields using semantic and pattern matching"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="field_matcher",
            description="Intelligent field matching with multiple algorithms",
            tool_class=cls,
            categories=["mapping", "analysis"],
            required_params=[],
            optional_params=["threshold"],
            context_aware=True,
            async_tool=False
        )
    
    def run(
        self,
        source_fields: List[str],
        target_fields: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Match source fields to target fields.
        
        Args:
            source_fields: List of source field names
            target_fields: List of target field definitions
            threshold: Minimum confidence threshold
            
        Returns:
            List of field mappings with confidence scores
        """
        mappings = []
        
        for source_field in source_fields:
            best_match = None
            best_score = 0.0
            
            # Normalize source field name
            normalized_source = self._normalize_field_name(source_field)
            
            for target in target_fields:
                target_name = target.get("name", "")
                normalized_target = self._normalize_field_name(target_name)
                
                # Calculate match scores
                scores = []
                
                # Exact match
                if normalized_source == normalized_target:
                    scores.append(1.0)
                
                # Fuzzy string matching
                fuzzy_score = SequenceMatcher(
                    None, 
                    normalized_source, 
                    normalized_target
                ).ratio()
                scores.append(fuzzy_score)
                
                # Token-based matching
                source_tokens = self._tokenize(normalized_source)
                target_tokens = self._tokenize(normalized_target)
                token_score = self._calculate_token_similarity(
                    source_tokens, 
                    target_tokens
                )
                scores.append(token_score)
                
                # Semantic similarity (simplified)
                semantic_score = self._calculate_semantic_similarity(
                    source_field,
                    target_name,
                    target.get("description", "")
                )
                scores.append(semantic_score)
                
                # Overall score (weighted average)
                overall_score = (
                    scores[0] * 0.4 +  # Exact match weight
                    scores[1] * 0.3 +  # Fuzzy match weight
                    scores[2] * 0.2 +  # Token match weight
                    scores[3] * 0.1    # Semantic weight
                )
                
                if overall_score > best_score:
                    best_score = overall_score
                    best_match = target
            
            # Add mapping if above threshold
            if best_score >= threshold and best_match:
                mappings.append({
                    "source_field": source_field,
                    "target_field": best_match["name"],
                    "confidence": round(best_score, 3),
                    "match_type": self._determine_match_type(best_score),
                    "target_info": best_match
                })
        
        # Sort by confidence
        mappings.sort(key=lambda x: x["confidence"], reverse=True)
        
        return mappings
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison"""
        # Convert to lowercase
        normalized = field_name.lower()
        
        # Replace common separators with space
        normalized = re.sub(r'[_\-\.]', ' ', normalized)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Split on spaces and filter empty
        tokens = [t for t in text.split() if t]
        
        # Also split camelCase
        expanded_tokens = []
        for token in tokens:
            # Insert spaces before uppercase letters
            expanded = re.sub(r'([a-z])([A-Z])', r'\1 \2', token)
            expanded_tokens.extend(expanded.lower().split())
        
        return expanded_tokens
    
    def _calculate_token_similarity(
        self, 
        tokens1: List[str], 
        tokens2: List[str]
    ) -> float:
        """Calculate similarity between token lists"""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Find common tokens
        common = set(tokens1).intersection(set(tokens2))
        
        # Jaccard similarity
        union = set(tokens1).union(set(tokens2))
        
        return len(common) / len(union) if union else 0.0
    
    def _calculate_semantic_similarity(
        self,
        source: str,
        target: str,
        description: str
    ) -> float:
        """Calculate semantic similarity (simplified)"""
        # Common field name synonyms
        synonyms = {
            "id": ["identifier", "key", "code"],
            "name": ["title", "label", "description"],
            "date": ["time", "timestamp", "datetime"],
            "user": ["person", "individual", "account"],
            "status": ["state", "condition", "phase"],
            "type": ["category", "class", "kind"],
            "value": ["amount", "quantity", "measure"],
            "location": ["address", "place", "site"]
        }
        
        source_lower = source.lower()
        target_lower = target.lower()
        
        # Check if source and target are synonyms
        for key, syns in synonyms.items():
            all_terms = [key] + syns
            if source_lower in all_terms and target_lower in all_terms:
                return 0.9
        
        # Check if description contains source field
        if description and source_lower in description.lower():
            return 0.7
        
        return 0.0
    
    def _determine_match_type(self, score: float) -> str:
        """Determine match type based on score"""
        if score >= 0.95:
            return "exact"
        elif score >= 0.8:
            return "strong"
        elif score >= 0.6:
            return "moderate"
        else:
            return "weak"
```

#### PII Scanner Tool
**File to create**: `backend/app/services/tools/pii_scanner_tool.py`

```python
"""
PII Scanner Tool for sensitive data detection
"""

from typing import Dict, Any, List, Set
from app.services.tools.base_tool import BaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
import re

class PIIScannerTool(BaseDiscoveryTool):
    """Scans data for personally identifiable information"""
    
    name: str = "pii_scanner"
    description: str = "Detect PII and sensitive data in datasets"
    
    # PII patterns
    PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "date_of_birth": r'\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b'
    }
    
    # Sensitive field name indicators
    SENSITIVE_FIELD_NAMES = {
        "ssn", "social_security", "social_security_number",
        "credit_card", "card_number", "cc_number",
        "email", "email_address", "e_mail",
        "phone", "phone_number", "telephone", "mobile",
        "date_of_birth", "dob", "birth_date", "birthdate",
        "password", "pwd", "pass", "secret",
        "salary", "income", "wage", "compensation",
        "address", "street", "city", "zip", "postal_code"
    }
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="pii_scanner",
            description="Scan and detect PII in data",
            tool_class=cls,
            categories=["security", "validation", "compliance"],
            required_params=[],
            optional_params=["deep_scan"],
            context_aware=True,
            async_tool=False
        )
    
    def run(
        self,
        data: List[Dict[str, Any]],
        field_names: List[str],
        deep_scan: bool = True
    ) -> Dict[str, Any]:
        """
        Scan data for PII.
        
        Args:
            data: Sample data records to scan
            field_names: All field names in dataset
            deep_scan: Whether to scan actual values
            
        Returns:
            PII detection results
        """
        results = {
            "pii_fields": [],
            "sensitive_fields": [],
            "detection_details": {},
            "risk_level": "low",
            "recommendations": []
        }
        
        # Check field names
        for field in field_names:
            field_lower = field.lower()
            
            # Check against sensitive field names
            for sensitive_name in self.SENSITIVE_FIELD_NAMES:
                if sensitive_name in field_lower:
                    results["sensitive_fields"].append({
                        "field": field,
                        "type": sensitive_name,
                        "confidence": "high"
                    })
                    break
        
        # Deep scan actual values
        if deep_scan and data:
            pii_detections = {}
            
            for record in data[:100]:  # Limit scan size
                for field, value in record.items():
                    if value and isinstance(value, str):
                        # Check against PII patterns
                        for pii_type, pattern in self.PATTERNS.items():
                            if re.search(pattern, str(value)):
                                if field not in pii_detections:
                                    pii_detections[field] = set()
                                pii_detections[field].add(pii_type)
            
            # Convert to results format
            for field, pii_types in pii_detections.items():
                results["pii_fields"].append({
                    "field": field,
                    "pii_types": list(pii_types),
                    "confidence": "high" if len(pii_types) > 1 else "medium"
                })
        
        # Determine risk level
        total_sensitive = len(results["sensitive_fields"]) + len(results["pii_fields"])
        if total_sensitive >= 5:
            results["risk_level"] = "high"
        elif total_sensitive >= 2:
            results["risk_level"] = "medium"
        
        # Add recommendations
        if results["risk_level"] in ["medium", "high"]:
            results["recommendations"].extend([
                "Implement data masking for PII fields",
                "Ensure encryption at rest and in transit",
                "Limit access to sensitive fields",
                "Consider tokenization for highly sensitive data"
            ])
        
        return results
```

### 4. Create Tool Categories
**File to create**: `backend/app/services/tools/categories.py`

```python
"""
Tool category definitions and management
"""

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class ToolCategory:
    """Tool category definition"""
    name: str
    description: str
    typical_tools: List[str]
    required_for_phases: List[str]

# Define standard tool categories
TOOL_CATEGORIES = {
    "analysis": ToolCategory(
        name="analysis",
        description="Tools for data and structure analysis",
        typical_tools=["schema_analyzer", "data_profiler", "pattern_detector"],
        required_for_phases=["data_validation", "field_mapping"]
    ),
    "validation": ToolCategory(
        name="validation",
        description="Tools for data validation and quality checks",
        typical_tools=["schema_validator", "data_quality_checker", "constraint_validator"],
        required_for_phases=["data_validation", "data_cleansing"]
    ),
    "mapping": ToolCategory(
        name="mapping",
        description="Tools for field and data mapping",
        typical_tools=["field_matcher", "semantic_mapper", "mapping_validator"],
        required_for_phases=["field_mapping"]
    ),
    "security": ToolCategory(
        name="security",
        description="Security and compliance tools",
        typical_tools=["pii_scanner", "encryption_checker", "access_validator"],
        required_for_phases=["data_validation", "tech_debt_assessment"]
    ),
    "transformation": ToolCategory(
        name="transformation",
        description="Data transformation and cleansing tools",
        typical_tools=["data_cleanser", "format_converter", "normalizer"],
        required_for_phases=["data_cleansing"]
    ),
    "discovery": ToolCategory(
        name="discovery",
        description="Asset and dependency discovery tools",
        typical_tools=["asset_scanner", "dependency_analyzer", "relationship_mapper"],
        required_for_phases=["asset_inventory", "dependency_analysis"]
    )
}

def get_tools_for_phase(phase: str) -> Set[str]:
    """Get all tools typically needed for a phase"""
    tools = set()
    for category in TOOL_CATEGORIES.values():
        if phase in category.required_for_phases:
            tools.update(category.typical_tools)
    return tools
```

### 5. Create Tool Factory
**File to create**: `backend/app/services/tools/factory.py`

```python
"""
Tool Factory for dynamic tool creation and management
"""

from typing import List, Dict, Any, Optional, Set
from app.services.tools.registry import tool_registry
from app.services.tools.categories import get_tools_for_phase
import logging

logger = logging.getLogger(__name__)

class ToolFactory:
    """
    Factory for creating and managing tools.
    Provides:
    - Dynamic tool creation
    - Phase-based tool sets
    - Tool configuration management
    """
    
    def __init__(self):
        self.registry = tool_registry
        self.tool_instances: Dict[str, Any] = {}
    
    def create_tool(
        self,
        tool_name: str,
        **config
    ) -> Optional[Any]:
        """Create a single tool instance"""
        try:
            tool = self.registry.get_tool(tool_name, **config)
            if tool:
                self.tool_instances[tool_name] = tool
                logger.info(f"Created tool: {tool_name}")
            return tool
        except Exception as e:
            logger.error(f"Failed to create tool {tool_name}: {e}")
            return None
    
    def create_tools_for_phase(
        self,
        phase: str,
        additional_tools: Optional[List[str]] = None
    ) -> List[Any]:
        """Create all tools needed for a specific phase"""
        # Get standard tools for phase
        phase_tools = get_tools_for_phase(phase)
        
        # Add any additional requested tools
        if additional_tools:
            phase_tools.update(additional_tools)
        
        # Create tool instances
        tools = []
        for tool_name in phase_tools:
            tool = self.create_tool(tool_name)
            if tool:
                tools.append(tool)
        
        logger.info(f"Created {len(tools)} tools for phase {phase}")
        return tools
    
    def create_tools_for_agent(
        self,
        agent_name: str,
        required_tools: List[str]
    ) -> List[Any]:
        """Create tools required by a specific agent"""
        tools = []
        
        for tool_name in required_tools:
            # Check if already created
            if tool_name in self.tool_instances:
                tools.append(self.tool_instances[tool_name])
            else:
                tool = self.create_tool(tool_name)
                if tool:
                    tools.append(tool)
        
        logger.info(f"Created {len(tools)} tools for agent {agent_name}")
        return tools
    
    def get_tool_capabilities(self) -> Dict[str, List[str]]:
        """Get all available tools grouped by category"""
        capabilities = {}
        
        for category in self.registry.list_categories():
            tools = self.registry.get_tools_by_category(category)
            capabilities[category] = [tool.name for tool in tools]
        
        return capabilities

# Global factory instance
tool_factory = ToolFactory()
```

## Success Criteria
- [ ] Tool registry with auto-discovery working
- [ ] Base tool classes provide proper patterns
- [ ] Core tools implemented (schema, matcher, PII)
- [ ] Tools respect context boundaries
- [ ] Tool factory creates tools dynamically
- [ ] Tools integrate with agents properly
- [ ] All tools are properly categorized

## Interfaces with Other Agents
- **Agent A1** uses your tools in agents
- **Agent C1** provides context patterns you use
- **Agent B1** uses tools in flows
- Share tool registry with all tracks

## Implementation Guidelines

### 1. Tool Structure Pattern
```python
class MyTool(BaseDiscoveryTool):
    name = "my_tool"
    description = "What this tool does"
    
    @classmethod
    def tool_metadata(cls):
        return ToolMetadata(...)
    
    def run(self, **kwargs):
        # Tool logic here
```

### 2. Context Usage in Tools
- Never pass context explicitly
- Always check context availability
- Use context for all data access
- Log with context information

### 3. Error Handling
- Catch and log all errors
- Provide helpful error messages
- Don't swallow exceptions
- Clean up resources

## Commands to Run
```bash
# Test tool discovery
docker exec -it migration_backend python -c "from app.services.tools.registry import tool_registry; print(tool_registry.list_tools())"

# Test tool creation
docker exec -it migration_backend python -m pytest tests/tools/test_tool_factory.py -v

# Test context isolation in tools
docker exec -it migration_backend python -m tests.tools.test_context_isolation

# List tool capabilities
docker exec -it migration_backend python -m app.services.tools.list_capabilities
```

## Definition of Done
- [ ] Tool registry implemented with auto-discovery
- [ ] Base tool classes created
- [ ] Core tools implemented and tested
- [ ] Tools respect context boundaries
- [ ] Tool factory working properly
- [ ] Tool categories defined
- [ ] Unit tests >85% coverage
- [ ] Integration tests verify context isolation
- [ ] PR created with title: "feat: [Phase2-D1] Tool system implementation"

## Notes
- Start with registry and base classes
- Implement one tool at a time
- Test context isolation thoroughly
- Keep tools focused and reusable
- Document tool parameters clearly