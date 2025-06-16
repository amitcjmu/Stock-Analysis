# Session Management - Multi-Tenant Default Session Approach

## Overview

The session management system implements a **multi-tenant default session approach** where:
- **Users can have multiple default sessions** - one per client+engagement combination
- **Frontend context switcher** determines which client+engagement context to use
- **Backend automatically resolves** the appropriate default session based on the client+engagement combination
- **Sessions are auto-created** when a user accesses a new client+engagement combination

This approach ensures:
- **Data isolation** between different client engagements
- **Seamless context switching** via frontend context switcher
- **Automatic session management** without user intervention
- **Multi-tenancy support** with proper data scoping

## Core Principles

### 1. Multi-Tenant Session Architecture
- **One default session per user per client+engagement combination**
- **Different engagement = Different default session** (for data isolation)
- **Frontend context switcher** controls which client+engagement context is active
- **Backend resolves** the appropriate default session based on context headers

### 2. Context-Driven Session Resolution
- **Frontend sends context headers**: `X-Client-Account-Id` and `X-Engagement-Id`
- **Backend finds/creates** the appropriate default session for that combination
- **Session auto-creation** when user accesses new client+engagement for the first time
- **Session reuse** for subsequent requests to the same client+engagement

### 3. Automatic Session Management
- **Sessions are auto-created** with proper naming: `{client-name}-{engagement-name}-{username}-default`
- **Sessions are marked** as `is_default=true` and `auto_created=true`
- **No manual session creation** required by users
- **Seamless experience** across different client engagements

## Implementation Details

### Frontend Context Switcher
The frontend context switcher component allows users to:
- **Select client account** from available options
- **Select engagement** within the chosen client
- **Switch between contexts** seamlessly
- **Send context headers** with every API request

```typescript
// Frontend sends these headers with API requests
const headers = {
  'X-Client-Account-Id': selectedClient.id,
  'X-Engagement-Id': selectedEngagement.id,
  'Authorization': `Bearer ${token}`
};
```

### Backend Context Resolution
The backend `get_context_from_user` function:
1. **Reads context headers** from the request
2. **Finds existing default session** for user+client+engagement combination
3. **Creates new default session** if none exists
4. **Returns appropriate RequestContext** with session ID

```python
async def get_context_from_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    # Extract client and engagement from request headers
    client_account_id = headers.get("x-client-account-id")
    engagement_id = headers.get("x-engagement-id")
    
    # Find user's default session for this client+engagement combination
    user_session = await find_default_session(
        user_id=current_user.id,
        client_account_id=client_account_id,
        engagement_id=engagement_id
    )
    
    if not user_session:
        # Auto-create default session for this combination
        user_session = await create_default_session(
            user=current_user,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
    
    return RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=str(current_user.id),
        session_id=str(user_session.id)
    )
```

### Session Auto-Creation
When a user accesses a new client+engagement combination:

```python
# Session naming convention
session_name = f"{client.name.lower().replace(' ', '-')}-{engagement.name.lower().replace(' ', '-')}-{user.email.split('@')[0]}-default"
session_display_name = f"{user.email}'s Default Session - {client.name} / {engagement.name}"

# Session creation
new_session = DataImportSession(
    session_name=session_name,
    session_display_name=session_display_name,
    description=f"Auto-created default session for {user.email} in {client.name} / {engagement.name}",
    engagement_id=engagement_id,
    client_account_id=client_account_id,
    is_default=True,
    auto_created=True,
    session_type='data_import',
    status='active',
    created_by=user.id,
    is_mock=False
)
```

## Data Isolation and Multi-Tenancy

### Client-Level Isolation
- **Different clients** = **Completely separate data**
- **User access control** enforced at client level
- **Session data scoped** to specific client account

### Engagement-Level Isolation
- **Different engagements within same client** = **Separate sessions**
- **Engagement-specific data** stored in separate sessions
- **Clear separation** of migration projects/phases

### Session-Level Data
- **All data imports** go to the user's default session for that client+engagement
- **Analysis results** stored within session context
- **Workflow states** tied to specific sessions

## User Experience

### Context Switching
1. **User selects client** from context switcher
2. **User selects engagement** within that client
3. **Frontend sends context headers** with subsequent requests
4. **Backend automatically uses** appropriate default session
5. **User sees data** specific to that client+engagement combination

### Seamless Operation
- **No session management UI** needed for users
- **Automatic session creation** when needed
- **Consistent data view** within each context
- **Clear separation** between different client engagements

## Example Scenarios

### Scenario 1: Consultant Working on Multiple Clients
```
User: consultant@company.com

Client A + Engagement 1 → Session: client-a-migration-consultant-default
Client A + Engagement 2 → Session: client-a-modernization-consultant-default  
Client B + Engagement 1 → Session: client-b-assessment-consultant-default
```

### Scenario 2: Client User with Multiple Engagements
```
User: admin@clientcorp.com

ClientCorp + Cloud Migration → Session: clientcorp-cloud-migration-admin-default
ClientCorp + Data Center Exit → Session: clientcorp-data-center-exit-admin-default
```

### Scenario 3: Context Switching
```
1. User selects "Client A" + "Migration Project" in context switcher
   → Backend uses session: client-a-migration-user-default
   → User sees migration-specific data

2. User switches to "Client A" + "Modernization Project"  
   → Backend uses session: client-a-modernization-user-default
   → User sees modernization-specific data

3. User switches to "Client B" + "Assessment Project"
   → Backend creates/uses session: client-b-assessment-user-default
   → User sees assessment-specific data
```

## Benefits of This Approach

### 1. Data Isolation
- **Clear separation** between different client engagements
- **No data mixing** between projects
- **Proper multi-tenancy** with context-aware data access

### 2. User Experience
- **Seamless context switching** via frontend UI
- **No manual session management** required
- **Automatic session creation** when needed
- **Consistent data view** within each context

### 3. Scalability
- **Supports multiple clients** per user
- **Supports multiple engagements** per client
- **Automatic session provisioning** as needed
- **Clean data organization** by context

### 4. Security
- **Context-aware access control** 
- **Proper tenant isolation**
- **Session-level data scoping**
- **Clear audit trail** per engagement

## Database Schema

### Sessions Table Structure
```sql
-- Each user can have multiple default sessions
-- One per client+engagement combination
CREATE TABLE data_import_sessions (
    id UUID PRIMARY KEY,
    session_name VARCHAR NOT NULL,
    session_display_name VARCHAR,
    description TEXT,
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    created_by UUID NOT NULL REFERENCES users(id),
    is_default BOOLEAN DEFAULT FALSE,
    auto_created BOOLEAN DEFAULT FALSE,
    session_type VARCHAR DEFAULT 'data_import',
    status VARCHAR DEFAULT 'active',
    is_mock BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure one default session per user per engagement
    UNIQUE(created_by, engagement_id, is_default) WHERE is_default = TRUE
);
```

### Context Resolution Query
```sql
-- Find user's default session for specific client+engagement
SELECT * FROM data_import_sessions 
WHERE created_by = :user_id 
  AND client_account_id = :client_id 
  AND engagement_id = :engagement_id 
  AND is_default = TRUE;
```

## Migration Strategy

### For Existing Users
1. **Existing sessions preserved** with current client+engagement associations
2. **New sessions auto-created** when users access different client+engagement combinations
3. **Gradual migration** as users switch contexts via frontend

### For New Users
1. **First session auto-created** when user first accesses any client+engagement
2. **Additional sessions created** as user accesses different contexts
3. **Seamless onboarding** with automatic session provisioning

## Context Switcher Integration

The context switcher component should:
- **Display current context** clearly (Client > Engagement)
- **Allow context switching** between available combinations
- **Send appropriate headers** with API requests
- **Handle context changes** smoothly

This approach provides the perfect balance between simplicity and functionality, supporting true multi-tenancy while maintaining a seamless user experience. 