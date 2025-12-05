# Railway/Azure Dockerfile Uses Different Requirements File

## Problem Pattern
Local development works but Railway/Azure deployment fails with `ModuleNotFoundError`.

## Root Cause
Railway Dockerfile uses `config/dependencies/requirements-docker.txt`, NOT `backend/requirements.txt`.

**From root Dockerfile (line 25)**:
```dockerfile
COPY config/dependencies/requirements-docker.txt requirements.txt
```

## Symptom
```
Background generation failed for flow ... (exception type: ModuleNotFoundError)
```

## Diagnosis Steps
1. Check which requirements file the Dockerfile uses
2. Compare with `backend/requirements.txt`
3. Look for missing packages

## Fix: December 2025
Added `dirtyjson==1.0.8` to `config/dependencies/requirements-docker.txt` which was missing.

The `dirtyjson` package is required by:
- `app/services/collection/gap_analysis/section_question_generator/generator.py`

## Prevention
When adding new Python dependencies:
1. Add to `backend/requirements.txt` (local dev)
2. **ALSO add to** `config/dependencies/requirements-docker.txt` (Railway/Azure deployment)

## Related Files
- `/Dockerfile` - Railway deployment (uses requirements-docker.txt)
- `/config/docker/Dockerfile.backend` - Local Docker (uses backend/requirements.txt)
- `/backend/requirements.txt` - Local development
- `/config/dependencies/requirements-docker.txt` - Production deployment
