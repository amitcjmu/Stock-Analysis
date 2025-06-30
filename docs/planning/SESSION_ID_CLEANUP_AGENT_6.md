# Agent 6: Testing & Final Cleanup

## 🎯 **Your Mission**
Run database migrations, update all tests, and perform final verification. You're the last line of defense!

## 📋 **Your Tasks**

### **1. Database Migration Execution**
**File**: The migration created by Agent 2  
**Location**: `/backend/alembic/versions/xxx_remove_session_id_final_cleanup.py`

**Steps**:
```bash
# First, verify the migration exists
docker exec -it migration_backend ls alembic/versions/

# Review the migration
docker exec -it migration_backend cat alembic/versions/*remove_session_id*.py

# Check current database state
docker exec -it migration_db psql -U postgres -d migration_db -c "\d discovery_flows"
docker exec -it migration_db psql -U postgres -d migration_db -c "\d assets"

# Run the migration
docker exec -it migration_backend alembic upgrade head

# Verify columns are dropped
docker exec -it migration_backend alembic current
```

### **2. Backend Test Updates**
**Files**: All test files containing session_id

**Find test files**:
```bash
docker exec -it migration_backend grep -r "session_id" tests/ --include="*.py" -l
```

**Common test updates**:
```python
# UPDATE test fixtures:
@pytest.fixture
def sample_flow():
    return {
        "flow_id": str(uuid.uuid4()),
        # REMOVE: "session_id": "disc_session_12345",
        "client_account_id": "test-client",
        "engagement_id": "test-engagement"
    }

# UPDATE test assertions:
# FROM: assert response.json()["session_id"] == "disc_session_12345"
# TO: assert response.json()["flow_id"] == flow_id

# UPDATE API test calls:
# FROM: response = client.get(f"/api/v1/flow/status/{session_id}")
# TO: response = client.get(f"/api/v1/flow/status/{flow_id}")
```

### **3. Frontend Test Updates**
**Files**: All test files containing sessionId

**Find test files**:
```bash
docker exec -it migration_frontend grep -r "sessionId" src/ --include="*.test.ts" --include="*.test.tsx" -l
```

**Common test updates**:
```typescript
// UPDATE mock data:
const mockFlow = {
  flowId: 'test-flow-123',
  // REMOVE: sessionId: 'disc_session_123',
  status: 'active'
};

// UPDATE test props:
render(<DiscoveryFlow flowId="test-123" />);
// NOT: render(<DiscoveryFlow sessionId="test-123" />);

// UPDATE route testing:
// FROM: expect(mockNavigate).toHaveBeenCalledWith('/discovery/flow?sessionId=123');
// TO: expect(mockNavigate).toHaveBeenCalledWith('/discovery/flow?flowId=123');
```

### **4. API Documentation Updates**
**Files**: 
- `/docs/api/` directory
- OpenAPI/Swagger specs
- README files

**Updates needed**:
```yaml
# OpenAPI spec example:
paths:
  /api/v1/flow/status/{flowId}:  # Not sessionId
    get:
      parameters:
        - name: flowId  # Not sessionId
          in: path
          required: true
          schema:
            type: string
```

### **5. Environment & Config Cleanup**
**Files**:
- `.env.example`
- `docker-compose.yml`
- Configuration files

**Remove**:
```bash
# From .env.example:
SESSION_ID_ENABLED=true  # REMOVE
SESSION_TIMEOUT=3600     # REMOVE

# From docker-compose.yml:
environment:
  - SESSION_ID_ENABLED=true  # REMOVE
```

## ✅ **Final Verification Checklist**

### **Backend Verification**
```bash
# 1. No session_id in code (should return 0)
docker exec -it migration_backend bash -c "grep -r 'session_id' app/ --include='*.py' | grep -v '__pycache__' | grep -v 'alembic/versions' | wc -l"

# 2. Run all backend tests
docker exec -it migration_backend pytest -v

# 3. Check database schema
docker exec -it migration_db psql -U postgres -d migration_db -c "\d+ discovery_flows" | grep session
docker exec -it migration_db psql -U postgres -d migration_db -c "\d+ assets" | grep session

# 4. Test API endpoints
curl -X POST http://localhost:8000/api/v3/discovery-flow/flows \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: test" \
  -H "X-Engagement-ID: test" \
  -d '{"flow_name": "Final Test Flow"}'
```

### **Frontend Verification**
```bash
# 1. No sessionId in code (should return 0)
docker exec -it migration_frontend bash -c "grep -r 'sessionId' src/ --include='*.ts' --include='*.tsx' | wc -l"

# 2. Run all frontend tests
docker exec -it migration_frontend npm test

# 3. Build check
docker exec -it migration_frontend npm run build

# 4. Type checking
docker exec -it migration_frontend npm run type-check
```

### **Integration Testing**
```bash
# Full flow test
1. Start the application
2. Create a new discovery flow
3. Import CMDB data
4. Map fields (verify "active flows" shows correctly)
5. Complete the flow
6. Verify no console errors
7. Check network tab for session_id (should be none)
```

## 📝 **Final Report Template**

Create a final report with:

```markdown
## Session ID Cleanup - Final Report

### Cleanup Statistics
- Files modified: XX
- Lines removed: XXX
- Tests updated: XX
- Database columns dropped: 2

### Verification Results
- [ ] Backend: 0 session_id references
- [ ] Frontend: 0 sessionId references
- [ ] All tests passing
- [ ] Manual testing completed
- [ ] Field mapping UI fixed
- [ ] Flow context sync working

### Known Issues
- None (or list any remaining issues)

### Performance Impact
- Database queries: No regression
- API response times: No regression
- Frontend build size: Reduced by X KB

### Completion Date: YYYY-MM-DD
```

## 🚨 **Critical Final Checks**

1. **The Field Mapping Bug**: Verify it shows active flows now
2. **Flow Context Sync**: Confirm data goes to correct tables
3. **No 404s**: Check browser console for missing endpoints
4. **No TypeScript Errors**: Build should complete cleanly

## 🔄 **If Issues Are Found**

1. **Don't panic** - Note which agent's work has issues
2. **Create specific fix tasks** in the master plan
3. **Run focused tests** on the problem area
4. **Communicate in Slack** for quick resolution

## 📊 **Success Metrics**

The cleanup is successful when:
- ✅ Zero grep results for session_id/sessionId
- ✅ All automated tests pass
- ✅ Manual testing shows no issues
- ✅ Field mapping UI displays active flows
- ✅ No console errors in browser
- ✅ Database has no session columns

---

**Remember**: You're the final quality gate. Be thorough in verification. This is the last chance to catch any issues!