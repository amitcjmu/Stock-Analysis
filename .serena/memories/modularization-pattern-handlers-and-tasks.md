# Code Modularization Pattern - Handlers and Background Tasks

## Problem
Large files (>400 lines) trigger pre-commit failures. Need to modularize while preserving backward compatibility and security fixes.

## Solution: Facade + Extraction Pattern

### Architecture
```
original_file.py (775 lines)
  ↓
main_router.py (235 lines) - Facade with route definitions
  ↓
handlers/ - HTTP endpoint logic
  ├── __init__.py - Public API exports
  ├── analysis_handlers.py (333 lines)
  ├── parameter_handlers.py (280 lines)
  ├── recommendation_handlers.py (84 lines)
  └── bulk_handlers.py (123 lines)

background_tasks/ - Async business logic
  ├── __init__.py - Public API exports
  ├── initial_analysis_task.py (272 lines)
  ├── parameter_update_task.py (128 lines)
  ├── question_processing_task.py (135 lines)
  ├── iteration_analysis_task.py (137 lines)
  └── bulk_analysis_task.py (44 lines)
```

### Step 1: Main Router (Facade Pattern)
```python
# backend/app/api/v1/endpoints/sixr_analysis.py (235 lines)
from app.api.v1.endpoints.sixr_analysis_modular.handlers import (
    create_sixr_analysis,
    get_analysis,
    update_sixr_parameters,
)

@router.post("/analyze", response_model=SixRAnalysisResponse)
async def create_analysis_endpoint(request, background_tasks, db, context):
    """Delegates to: handlers.analysis_handlers.create_sixr_analysis"""
    return await create_sixr_analysis(request, background_tasks, db, context)
```

### Step 2: Handler Extraction
```python
# backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers.py
async def create_sixr_analysis(request, background_tasks, db, context):
    """HTTP endpoint logic - validation, response formation"""
    service = AnalysisService(crewai_service=TenantScopedAgentPool)
    # ... endpoint logic ...
    background_tasks.add_task(
        service.run_initial_analysis,
        analysis.id,
        parameters.dict(),
        "system",
        context.client_account_id,  # SECURITY: Preserve tenant context
        context.engagement_id,
    )
    return await get_analysis(analysis.id, db)
```

### Step 3: Background Task Extraction
```python
# backend/app/api/v1/endpoints/sixr_analysis_modular/services/analysis_service.py (168 lines)
from .background_tasks import (
    run_initial_analysis as _run_initial_analysis,
)

class AnalysisService:
    async def run_initial_analysis(self, analysis_id, parameters, user,
                                   client_account_id=None, engagement_id=None):
        """Facade method - delegates to background task module"""
        return await _run_initial_analysis(
            decision_engine=self.decision_engine,
            analysis_id=analysis_id,
            parameters=parameters,
            user=user,
            client_account_id=client_account_id,  # Pass through
            engagement_id=engagement_id,
        )
```

### Step 4: Background Task Implementation
```python
# backend/app/api/v1/endpoints/sixr_analysis_modular/services/background_tasks/initial_analysis_task.py
async def run_initial_analysis(decision_engine, analysis_id, parameters, user,
                               client_account_id=None, engagement_id=None):
    """Actual business logic with security fixes preserved"""
    async with AsyncSessionLocal() as db:
        # SECURITY: Tenant-scoped query (preserved from original)
        query = select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
        if client_account_id is not None:
            query = query.where(SixRAnalysis.client_account_id == client_account_id)
        if engagement_id is not None:
            query = query.where(SixRAnalysis.engagement_id == engagement_id)
        # ... rest of logic ...
```

## Results
- `sixr_analysis.py`: 775 → 235 lines (70% reduction)
- `analysis_service.py`: 619 → 168 lines (73% reduction)
- All security fixes preserved with comments
- Backward compatibility via facade pattern
- Pre-commit file length check: PASSED ✅

## Key Principles
1. **Preserve security comments** - Mark with "SECURITY:" prefix
2. **Maintain signatures** - Don't drop tenant context parameters
3. **Facade pattern** - Main file delegates, doesn't reimplement
4. **Explicit imports** - Use `from .handlers import create_sixr_analysis`
5. **Test imports** - Verify `from app.api.v1.endpoints.sixr_analysis import router` still works

## Avoiding Regressions
When modularizing, preserve:
- All function parameters (especially tenant context)
- Security-related WHERE clauses
- Error handling and logging
- Transaction boundaries
- Type hints and Optional types
