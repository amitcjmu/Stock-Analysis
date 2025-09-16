# Field Mapping Approval Status Updates

## Insight 1: Update Approval Metadata on Status Change
**Problem**: Approved mappings not showing in correct column
**Solution**: Update approved_by and approved_at when status changes
**Code**:
```python
# In learning_service.py _update_mapping_status method
async def _update_mapping_status(self, mapping: ImportFieldMapping, status: str):
    """Update mapping status and commit to database."""
    from datetime import datetime

    mapping.status = status

    # If approving, also set approval metadata
    if status == "approved":
        mapping.approved_by = str(self.context.user_id) if self.context.user_id else "system"
        mapping.approved_at = datetime.utcnow()

    await self.db.flush()
```
**Usage**: When approving field mappings through learning service

## Files Fixed:
- `backend/app/api/v1/endpoints/data_import/field_mapping/services/learning_service.py`
