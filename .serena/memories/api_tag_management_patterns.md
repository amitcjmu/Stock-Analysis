# API Tag Management Patterns

## Canonical Tag System
Use centralized APITags class for all endpoint categorization

### Structure
```python
# app/api/v1/api_tags.py
class APITags:
    """Centralized API tag constants to prevent drift."""

    # Authentication & User Management
    AUTHENTICATION = "Authentication"
    USER_MANAGEMENT = "User Management"

    # Data Import & Processing
    DATA_IMPORT_CORE = "Data Import Core"
    FIELD_MAPPING = "Field Mapping"

    @classmethod
    def get_all_tags(cls) -> list[str]:
        return [value for key, value in vars(cls).items()
                if not key.startswith("_") and isinstance(value, str)]

    @classmethod
    def validate_tag(cls, tag: str) -> bool:
        return tag in cls.get_all_tags()
```

## Tag Application Rules
**NEVER** apply tags in endpoint files, **ONLY** at router inclusion

```python
# WRONG - In endpoint file
router = APIRouter(tags=["Authentication"])

# CORRECT - In endpoint file
router = APIRouter()

# CORRECT - In router_registry.py or api.py
from app.api.v1.api_tags import APITags
api_router.include_router(auth_router, prefix="/auth", tags=[APITags.AUTHENTICATION])
```

## Validation Script
Use check_api_tags.py for enforcement:

```bash
# Check violations
python scripts/check_api_tags.py

# Auto-fix violations
python scripts/check_api_tags.py --fix

# Dry run
python scripts/check_api_tags.py --fix --dry-run
```

## Multi-line Detection Pattern
```python
# Detect APIRouter with tags across multiple lines
pattern = re.compile(
    r'APIRouter\s*\([^)]*tags\s*=\s*\[[^\]]*\][^)]*\)',
    re.MULTILINE | re.DOTALL
)
```

## Pre-commit Integration
```yaml
# .pre-commit-config.yaml
- id: check-api-tags
  name: Check API tag violations
  entry: python backend/scripts/check_api_tags.py
  language: system
  files: \.py$
```

## Adding New Tags
1. Add constant to APITags class
2. Update LEGACY_TAG_MAPPINGS if replacing old tags
3. Run validation script to ensure consistency
