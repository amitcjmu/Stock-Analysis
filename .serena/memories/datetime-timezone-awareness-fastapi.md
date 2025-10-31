# DateTime Timezone Awareness in FastAPI/SQLAlchemy

## Problem
`TypeError: can't compare offset-naive and offset-aware datetimes` when validating token expiration or comparing timestamps.

## Root Cause
```python
# BAD: Naive datetime (no timezone info)
expires_at = datetime.utcnow() + timedelta(days=7)

# Database column definition
expires_at = Column(DateTime(timezone=True))  # Stores with timezone
```

**Mismatch**: Python creates naive, database stores aware → comparison fails.

## Solution
**Always use timezone-aware UTC datetimes**

```python
from datetime import datetime, timezone

# GOOD: Timezone-aware datetime
expires_at = datetime.now(timezone.utc) + timedelta(days=7)
last_used_at = datetime.now(timezone.utc)
```

## Common Locations to Fix
1. **Model validation methods**:
```python
def is_valid(self) -> bool:
    return not self.is_revoked and datetime.now(timezone.utc) < self.expires_at
```

2. **Token creation**:
```python
refresh_token = RefreshToken(
    user_id=user.id,
    token_hash=token_hash,
    expires_at=datetime.now(timezone.utc) + timedelta(days=7)
)
```

3. **Timestamp fields**:
```python
user.last_login_at = datetime.now(timezone.utc)
token.last_used_at = datetime.now(timezone.utc)
```

## Search Pattern
```bash
# Find all uses of naive datetime
grep -r "datetime.utcnow()" backend/
grep -r "datetime.now()" backend/ | grep -v "timezone.utc"
```

## Import Statement
```python
from datetime import datetime, timezone  # Always include 'timezone'
```

## Database Column Definition
```python
# SQLAlchemy models
created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

## When to Apply
- Any FastAPI project with DateTime columns
- Token expiration validation
- Timestamp comparisons
- Audit trail fields (created_at, updated_at, last_used_at)
