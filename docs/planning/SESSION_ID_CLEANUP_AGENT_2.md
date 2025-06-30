# Agent 2: Database Models & Repositories Cleanup

## 🎯 **Your Mission**
Remove all session_id references from database models and repositories. Clean up the database schema completely.

## 📋 **Your Files**

### **1. Discovery Flow Model**
**File**: `/backend/app/models/discovery_flow.py`  
**Lines to modify**: 34, 86-88, 186

**Specific Changes**:
```python
# Line 34 - REMOVE this column:
import_session_id = Column(UUID(as_uuid=True), nullable=True, index=True)

# Lines 86-88 - REMOVE this property entirely:
@property
def session_id(self):
    return self.import_session_id

# Line 186 - REMOVE from to_dict():
"import_session_id": str(self.import_session_id) if self.import_session_id else None,
```

### **2. Asset Model**
**File**: `/backend/app/models/asset.py`  
**Lines to modify**: Check around lines 93, 118, 120-123

**Specific Changes**:
```python
# REMOVE session_id column:
session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id'))

# REMOVE legacy_session_id property:
@property
def legacy_session_id(self):
    return self.session_id
```

### **3. Discovery Flow Repository**
**File**: `/backend/app/repositories/discovery_flow_repository.py`  
**Lines to modify**: 45, 67, 89, 123, and any other session_id methods

**Specific Changes**:
```python
# REMOVE these methods entirely:
async def get_flow_by_session_id(self, session_id: str) -> Optional[DiscoveryFlow]:
    # Delete entire method

async def get_flows_for_session(self, session_id: str) -> List[DiscoveryFlow]:
    # Delete entire method

async def _filter_by_session(self, session_id: str):
    # Delete entire method

# REMOVE any queries using import_session_id:
.where(DiscoveryFlow.import_session_id == session_id)
```

### **4. Data Import Session Model**
**File**: `/backend/app/models/data_import_session.py`  
**Action**: Evaluate if this entire model is still needed

**If keeping the model**:
```python
# REMOVE session_id property:
@property
def session_id(self):
    return str(self.id)
```

**If removing the model**:
- Delete the entire file
- Update `__init__.py` to remove import

### **5. Data Import Session Repository**
**File**: `/backend/app/repositories/data_import_session_repository.py`  
**Action**: Update or remove based on model decision

**If keeping**:
```python
# Update all methods to remove session_id references
# Change method names from session to flow where appropriate
```

### **6. Asset Repository**
**File**: `/backend/app/repositories/asset_repository.py` (if exists)  
**Action**: Update queries to remove session_id

**Changes**:
```python
# REMOVE any queries like:
.where(Asset.session_id == session_id)

# UPDATE foreign key relationships to use flow_id
```

### **7. Create Database Migration**
**File**: `/backend/alembic/versions/xxx_remove_session_id_final_cleanup.py` (NEW FILE)  
**Action**: Create migration to drop columns

```python
"""Remove session_id final cleanup

Revision ID: [generate with alembic]
Revises: [previous migration]
Create Date: [current date]

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '[generate]'
down_revision = '[previous]'
branch_labels = None
depends_on = None

def upgrade():
    # Drop columns
    op.drop_column('discovery_flows', 'import_session_id')
    op.drop_column('assets', 'session_id')
    
    # Drop table if removing data_import_sessions
    op.drop_table('data_import_sessions')
    
    # Drop any indexes
    op.drop_index('idx_discovery_flows_import_session_id', table_name='discovery_flows', if_exists=True)
    op.drop_index('idx_assets_session_id', table_name='assets', if_exists=True)

def downgrade():
    # Not supporting downgrade - this is final cleanup
    raise NotImplementedError("Downgrade not supported for session_id cleanup")
```

### **8. Update Model Imports**
**File**: `/backend/app/models/__init__.py`  
**Action**: Remove any session model imports if deleting them

## ✅ **Verification Steps**

```bash
# Check each model file
docker exec -it migration_backend grep -n "session_id" app/models/discovery_flow.py
docker exec -it migration_backend grep -n "session_id" app/models/asset.py

# Check repositories
docker exec -it migration_backend grep -r "session_id" app/repositories/ --include="*.py"

# After creating migration
docker exec -it migration_backend alembic revision --autogenerate -m "Remove session_id final cleanup"

# Test migration
docker exec -it migration_backend alembic upgrade head
```

## 🚨 **Critical Notes**

1. **Wait for Agent 1 to complete context.py** before testing
2. **Create the migration LAST** after all model changes
3. **DO NOT run the migration** until Agent 6 coordinates final testing
4. Check for any SQLAlchemy relationships that might break

## 📝 **Progress Tracking**

Update the master plan tracker after each file:
- [ ] `/backend/app/models/discovery_flow.py`
- [ ] `/backend/app/models/asset.py`
- [ ] `/backend/app/repositories/discovery_flow_repository.py`
- [ ] `/backend/app/models/data_import_session.py` - Evaluate/Remove
- [ ] `/backend/app/repositories/data_import_session_repository.py`
- [ ] `/backend/app/repositories/asset_repository.py`
- [ ] Database migration created
- [ ] Model imports updated

## 🔄 **Commit Pattern**

```bash
git add app/models/discovery_flow.py
git commit -m "cleanup: Remove import_session_id from DiscoveryFlow model"

git add app/models/asset.py
git commit -m "cleanup: Remove session_id from Asset model"

git add app/repositories/discovery_flow_repository.py
git commit -m "cleanup: Remove session_id methods from repository"

# If removing files
git rm app/models/data_import_session.py app/repositories/data_import_session_repository.py
git commit -m "cleanup: Remove deprecated session models and repositories"
```

## ⚠️ **If You Get Stuck**

- Check if any other models have foreign keys to session_id
- Look for cascade delete implications
- Coordinate with Agent 3 if services depend on your models
- Don't run migrations without coordinating with Agent 6

---

**Remember**: This is permanent cleanup. Once we drop these columns, there's no going back!