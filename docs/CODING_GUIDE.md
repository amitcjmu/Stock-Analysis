# Development Guide

## Code Organization & Modularity Standards

### File Size Guidelines
- **Maximum 300-400 lines per Python file**
- **Maximum 50-100 lines per function/method**
- **Maximum 10-15 methods per class**

### When to Split Files
Split files when they exceed guidelines or have multiple responsibilities:

```python
# ❌ Bad: Large monolithic file
# discovery.py (1660 lines)

# ✅ Good: Modular structure
# discovery/
#   ├── __init__.py
#   ├── router.py (routing logic)
#   ├── processors.py (data processing)
#   ├── analyzers.py (analysis logic)
#   ├── formatters.py (data formatting)
#   └── validators.py (validation logic)
```

### Module Structure Standards

#### 1. API Endpoints (`/api/v1/endpoints/`)
```python
# Maximum 200 lines per router file
# Single responsibility: HTTP routing only

@router.post("/analyze-cmdb")
async def analyze_cmdb_data(request: CMDBAnalysisRequest):
    # Delegate to service layer
    return await cmdb_service.analyze_data(request)
```

#### 2. Service Layer (`/services/`)
```python
# Maximum 300 lines per service file
# Business logic and orchestration

class CMDBService:
    def __init__(self):
        self.processor = CMDBProcessor()
        self.analyzer = CMDBAnalyzer()
    
    async def analyze_data(self, request):
        # Orchestrate the workflow
        pass
```

#### 3. Core Logic (`/core/`)
```python
# Maximum 400 lines per core module
# Specific domain logic

class CMDBProcessor:
    def parse_file(self, content, file_type):
        # Single responsibility: file parsing
        pass
```

#### 4. Utilities (`/utils/`)
```python
# Maximum 200 lines per utility file
# Reusable helper functions

def validate_csv_format(content: str) -> bool:
    # Utility function
    pass
```

### Function Guidelines

#### Size Limits
```python
# ❌ Bad: Function too long (100+ lines)
def process_cmdb_data_monolithic():
    # ... 150 lines of mixed logic

# ✅ Good: Small, focused functions
def parse_cmdb_file(content: str) -> pd.DataFrame:
    # 10-20 lines: file parsing only
    pass

def apply_field_mappings(df: pd.DataFrame) -> pd.DataFrame:
    # 15-25 lines: field mapping only
    pass

def combine_os_fields(df: pd.DataFrame) -> pd.DataFrame:
    # 20-30 lines: OS combination only
    pass
```

#### Single Responsibility
```python
# ❌ Bad: Multiple responsibilities
def process_and_analyze_and_format_data():
    # Parsing, analysis, formatting in one function
    pass

# ✅ Good: Single responsibility
def parse_cmdb_data() -> pd.DataFrame:
    # Only parsing logic
    pass

def analyze_data_quality(df: pd.DataFrame) -> QualityReport:
    # Only analysis logic
    pass
```

### Class Guidelines

#### Size and Responsibility
```python
# ❌ Bad: God class
class CMDBEverything:
    # 50+ methods doing everything
    def parse_file(self): pass
    def analyze_data(self): pass
    def format_output(self): pass
    def send_email(self): pass
    def generate_reports(self): pass
    # ... 45+ more methods

# ✅ Good: Focused classes
class CMDBParser:
    def parse_csv(self): pass
    def parse_json(self): pass
    def validate_format(self): pass

class CMDBAnalyzer:
    def analyze_quality(self): pass
    def detect_asset_types(self): pass
    def identify_missing_fields(self): pass
```

### Error Handling Standards

```python
# ✅ Good: Specific error handling
try:
    result = process_data(input_data)
except ValidationError as e:
    logger.error(f"Data validation failed: {e}")
    raise HTTPException(400, f"Invalid data: {e}")
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise HTTPException(500, f"Processing error: {e}")
```

### Logging Standards

```python
# ✅ Good: Structured logging
logger.info(f"Processing CMDB file: {filename}")
logger.debug(f"Found {len(columns)} columns: {columns}")
logger.warning(f"Missing field detected: {field_name}")
logger.error(f"Processing failed: {error}", exc_info=True)
```

### Documentation Standards

#### Function Documentation
```python
def apply_field_mappings(df: pd.DataFrame, mappings: Dict[str, str]) -> pd.DataFrame:
    """
    Apply discovered field mappings to rename DataFrame columns.
    
    Args:
        df: Input DataFrame with original column names
        mappings: Dictionary mapping original names to canonical names
        
    Returns:
        DataFrame with renamed columns
        
    Raises:
        ValueError: If mappings contain invalid column names
        
    Example:
        >>> mappings = {"RAM (GB)": "memory_gb", "HOSTNAME": "asset_name"}
        >>> result_df = apply_field_mappings(original_df, mappings)
    """
```

#### Class Documentation
```python
class CMDBProcessor:
    """
    Handles CMDB data processing and transformation.
    
    This class is responsible for:
    - Parsing CMDB export files
    - Applying field mappings
    - Data validation and cleaning
    
    Attributes:
        field_mapper: Instance of FieldMappingTool
        validator: Instance of DataValidator
    """
```

### Testing Standards

#### Test Organization
```python
# tests/unit/services/test_cmdb_processor.py
class TestCMDBProcessor:
    def test_parse_csv_file(self):
        # Test single responsibility
        pass
    
    def test_apply_field_mappings(self):
        # Test field mapping logic
        pass
    
    def test_handle_invalid_format(self):
        # Test error handling
        pass
```

#### Test Size
- **Maximum 50 lines per test method**
- **Maximum 200 lines per test file**
- **Use fixtures for complex setup**

### Refactoring Guidelines

#### When to Refactor
1. **File exceeds 400 lines**
2. **Function exceeds 50 lines** 
3. **Class has more than 15 methods**
4. **Code duplication found**
5. **Complex nested conditions (>3 levels)**

#### How to Refactor
```python
# 1. Extract functions
def complex_logic():
    # 100 lines of code
    pass

# Becomes:
def complex_logic():
    step1_result = perform_step1()
    step2_result = perform_step2(step1_result)
    return finalize_result(step2_result)

# 2. Extract classes
class DataProcessor:
    def process_all(self): pass  # Extract specialized processors

# Becomes:
class CSVProcessor: pass
class JSONProcessor: pass
class ExcelProcessor: pass

# 3. Extract modules
# Large service file -> Multiple focused service files
```

### Import Organization

```python
# ✅ Good: Organized imports
# Standard library
import json
import logging
from typing import Dict, List, Optional

# Third-party
import pandas as pd
from fastapi import APIRouter, HTTPException

# Local application
from app.core.config import settings
from app.services.field_mapper import FieldMapper
from app.utils.validators import validate_csv_format
```

### Dependency Injection

```python
# ✅ Good: Dependency injection for testability
class CMDBService:
    def __init__(self, processor: CMDBProcessor, analyzer: CMDBAnalyzer):
        self.processor = processor
        self.analyzer = analyzer

# In main application
cmdb_service = CMDBService(
    processor=CMDBProcessor(),
    analyzer=CMDBAnalyzer()
)
```

### Configuration Management

```python
# ✅ Good: Centralized configuration
class CMDBConfig:
    MAX_FILE_SIZE = 100_000_000  # 100MB
    SUPPORTED_FORMATS = ["csv", "json", "xlsx"]
    DEFAULT_QUALITY_THRESHOLD = 70

# Usage
if file_size > CMDBConfig.MAX_FILE_SIZE:
    raise ValueError("File too large")
```

## Code Review Checklist

### Before Submitting
- [ ] File is under 400 lines
- [ ] Functions are under 50 lines
- [ ] Classes have single responsibility
- [ ] No code duplication
- [ ] Proper error handling
- [ ] Comprehensive logging
- [ ] Documentation included
- [ ] Tests written
- [ ] Imports organized

### Reviewer Checklist
- [ ] Code follows modularity guidelines
- [ ] Functions have single responsibility
- [ ] Error handling is appropriate
- [ ] Logging is structured and helpful
- [ ] Documentation is clear and complete
- [ ] Tests cover edge cases
- [ ] Performance considerations addressed

## Junior Developer Quick Reference

### Starting a New Feature
1. **Plan the module structure** - What classes/functions needed?
2. **Keep files small** - Split early, split often
3. **Write tests first** - TDD approach
4. **Single responsibility** - One thing per function/class
5. **Document as you go** - Don't leave it for later

### Common Patterns
```python
# Service Pattern
class SomeService:
    def __init__(self, dependencies):
        self.dependencies = dependencies
    
    def do_something(self, input_data):
        # Orchestrate workflow
        pass

# Repository Pattern  
class SomeRepository:
    def find_by_id(self, id): pass
    def save(self, entity): pass
    def delete(self, entity): pass

# Factory Pattern
class ProcessorFactory:
    @staticmethod
    def create_processor(file_type):
        if file_type == "csv":
            return CSVProcessor()
        elif file_type == "json":
            return JSONProcessor()
```

### Anti-Patterns to Avoid
```python
# ❌ God objects
class DoEverything: pass

# ❌ Long parameter lists
def process(a, b, c, d, e, f, g, h): pass

# ❌ Deep nesting
if condition1:
    if condition2:
        if condition3:
            if condition4:  # Too deep!

# ❌ Magic numbers
if score > 0.7:  # What is 0.7?

# ✅ Use constants
if score > QualityThresholds.ACCEPTABLE:
```

Remember: **Clean code is not written by following a set of rules. Clean code is written by cleanly applying a bunch of small techniques and principles.** 