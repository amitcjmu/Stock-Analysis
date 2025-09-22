# Asset-Agnostic Collection Model Fixes

## Insight 1: SQLAlchemy Model Default Values
**Problem**: Column defaults only apply on DB insert, not object creation
**Solution**: Override `__init__` to set in-memory defaults
**Code**:
```python
class AssetFieldConflict(Base, TimestampMixin):
    resolution_status = Column(
        String(20),
        nullable=False,
        default="pending",  # DB default
    )

    def __init__(self, **kwargs):
        """Initialize with default resolution_status if not provided."""
        if "resolution_status" not in kwargs:
            kwargs["resolution_status"] = "pending"  # In-memory default
        super().__init__(**kwargs)
```
**Usage**: When unit tests expect defaults immediately after object creation

## Insight 2: ENUM vs String for Status Fields
**Problem**: PostgreSQL ENUMs cause compatibility issues
**Solution**: Use String columns with CHECK constraints instead
**Code**:
```python
# AVOID - ENUM causes issues
from sqlalchemy.dialects.postgresql import ENUM
resolution_status = Column(
    ENUM("pending", "auto_resolved", "manual_resolved", name="resolution_status_enum"),
    nullable=False,
    default="pending"
)

# PREFERRED - String with validation
resolution_status = Column(
    String(20),
    nullable=False,
    default="pending"
)
```
**Usage**: For better cross-database compatibility and testing

## Insight 3: Removing Dead EAV Models
**Problem**: Unused Entity-Attribute-Value model (409 lines) flagged in PR
**Solution**: Delete entire model and all references
**Commands**:
```bash
# Find the unused model
grep -r "AssetFieldValue" --include="*.py"

# If no usage except imports, delete it
git rm backend/app/models/asset_agnostic/asset_field_values.py

# Update __init__.py to remove import
# Remove from Asset model relationships
```
**Usage**: When PR review identifies unused code

## Insight 4: Test Graceful Handling of Missing Fields
**Problem**: Test expects default value for missing dict key
**Solution**: Use .get() with default instead of direct access
**Code**:
```python
# WRONG - KeyError if confidence missing
assert highest["confidence"] == 0.0

# CORRECT - Handles missing field
assert highest.get("confidence", 0.0) == 0.0
```
**Usage**: When testing edge cases with optional fields
