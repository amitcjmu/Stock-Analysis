# Agent 1: Core Backend Context Cleanup

## 🎯 **Your Mission**
Remove all session_id references from the core context system. This is CRITICAL - all other backend work depends on your changes to context.py.

## 📋 **Your Files**

### **1. CRITICAL - Must Complete First**
**File**: `/backend/app/core/context.py`  
**Lines to modify**: 27, 55, 82, 148-157, 162-164, 173, 217, 235, 242, 261, 279-281, 346-347

**Specific Changes**:
```python
# Line 27 - REMOVE:
_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

# Line 55 - REMOVE from RequestContext dataclass:
session_id: Optional[str] = None

# Line 82 - UPDATE __repr__ to remove session_id:
# FROM: f"RequestContext(client={self.client_account_id}, engagement={self.engagement_id}, user={self.user_id}, session={self.session_id})"
# TO: f"RequestContext(client={self.client_account_id}, engagement={self.engagement_id}, user={self.user_id}, flow={self.flow_id})"

# Lines 148-157 - REMOVE session_id header extraction:
session_id = (
    headers.get("X-Session-ID") or
    headers.get("x-session-id") or
    headers.get("X-Session-Id") or
    headers.get("x-context-session-id") or
    headers.get("session-id")
)
if session_id:
    session_id = clean_header_value(session_id)

# Lines 162-164 - REMOVE session_id generation:
if not session_id:
    session_id = str(uuid.uuid4())
    logger.debug(f"No session ID in headers, generated new one: {session_id}")

# Line 173 - REMOVE from context creation:
session_id=session_id

# Line 217 - REMOVE:
_session_id.set(context.session_id)

# Line 235 - REMOVE:
session_id = _session_id.get()

# Line 242 - REMOVE from RequestContext creation:
session_id=session_id

# Line 261 - REMOVE:
_session_id.set(None)

# Lines 279-281 - REMOVE entire function:
def get_session_id() -> Optional[str]:
    """Get current session ID."""
    return _session_id.get()

# Lines 346-347 - REMOVE from create_context_headers:
if context.session_id:
    headers["X-Session-Id"] = context.session_id

# ADD if missing:
# Add flow_id to RequestContext (around line 55)
flow_id: Optional[str] = None

# Add flow_id ContextVar (around line 27)
_flow_id: ContextVar[Optional[str]] = ContextVar('flow_id', default=None)

# Add get_flow_id function (after line 281)
def get_flow_id() -> Optional[str]:
    """Get current flow ID."""
    return _flow_id.get()

# Add flow_id to header extraction (in extract_context_from_request)
flow_id = (
    headers.get("X-Flow-ID") or
    headers.get("x-flow-id") or
    headers.get("X-Flow-Id")
)
if flow_id:
    flow_id = clean_header_value(flow_id)

# Add flow_id to context setting
_flow_id.set(context.flow_id)

# Add flow_id to header creation
if context.flow_id:
    headers["X-Flow-Id"] = context.flow_id
```

### **2. Remove Session Endpoints**
**File**: `/backend/app/api/v1/endpoints/sessions.py`  
**Action**: DELETE THE ENTIRE FILE

### **3. Update Main App**
**File**: `/backend/app/main.py` or `/backend/app/api/v1/main.py`  
**Action**: Remove sessions router registration
```python
# REMOVE:
# from app.api.v1.endpoints import sessions
# app.include_router(sessions.router)
```

### **4. Check Middleware**
**File**: `/backend/app/middleware/context_middleware.py` (if exists)  
**Action**: Replace any session_id references with flow_id

### **5. Update Config**
**File**: `/backend/app/core/config.py`  
**Action**: Remove any session-related configuration variables

### **6. Update Dependencies**
**File**: `/backend/app/core/dependencies.py` (if exists)  
**Action**: Update any session_id dependencies to use flow_id

## ✅ **Verification Steps**

After each file change:
```bash
# Check the specific file
docker exec -it migration_backend grep -n "session_id" /path/to/your/file.py

# After completing all files
docker exec -it migration_backend grep -r "session_id" app/core/ --include="*.py" | grep -v "__pycache__"

# Run core tests
docker exec -it migration_backend pytest tests/unit/test_context.py -v
```

## 🚨 **Critical Notes**

1. **context.py is THE MOST CRITICAL FILE** - Every other backend component depends on it
2. Make sure to ADD flow_id support if it's missing
3. Test thoroughly - a mistake here breaks everything
4. Complete context.py BEFORE moving to other files

## 📝 **Progress Tracking**

Update the master plan tracker after each file:
- [ ] `/backend/app/core/context.py` - CRITICAL
- [ ] `/backend/app/api/v1/endpoints/sessions.py` - DELETE
- [ ] Router registration removal
- [ ] Middleware check
- [ ] Config cleanup
- [ ] Dependencies update

## 🔄 **Commit Pattern**

```bash
git add app/core/context.py
git commit -m "cleanup: Remove session_id from RequestContext and context management"

git rm app/api/v1/endpoints/sessions.py
git commit -m "cleanup: Delete deprecated sessions endpoints"

# Continue with clear, specific commits
```

## ⚠️ **If You Get Stuck**

- Check if flow_id infrastructure exists before removing session_id
- Look for tests that might be expecting session_id
- Coordinate with Agent 3 if you find API dependencies
- Post in Slack with specific error messages

---

**Remember**: You're doing cleanup, not migration. Be aggressive in removing session_id - there's no going back!