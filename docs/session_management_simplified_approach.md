# Session Management - Simplified Single Default Session Approach

## Overview

Based on the analysis of the current implementation and the complexity of full session merging/combining functionality, we're implementing a **simplified approach**: **one single default session per user per engagement**.

This approach ensures:
- Every user has a default session they always operate within
- No complex session merging or combining logic needed
- Clear data isolation and context management
- Simplified frontend session management

## Core Principles

### 1. User Default Context
Every user must have:
- **Default Client Account ID**: The primary client they work with
- **Default Engagement ID**: The primary engagement within that client
- **Default Session ID**: The primary session within that engagement

### 2. Single Session Operation
- Users operate within their **single default session**
- All data imports, analysis, and processing happen within this session
- Session acts as the user's persistent workspace
- No session switching or multiple sessions per user

### 3. Automatic Session Management
- Sessions are **auto-created** when users are created or first access the system
- Session naming: `{client_name}-{engagement_name}-{user_name}-default`
- Sessions are marked as `is_default=true` and `auto_created=true`

## Database Schema Updates

### 1. Update Users Table
```sql
-- Add default context fields to users table
ALTER TABLE users 
ADD COLUMN default_client_account_id UUID REFERENCES client_accounts(id),
ADD COLUMN default_engagement_id UUID REFERENCES engagements(id),
ADD COLUMN default_session_id UUID REFERENCES data_import_sessions(id);

-- Add indexes for performance
CREATE INDEX idx_users_default_client ON users(default_client_account_id);
CREATE INDEX idx_users_default_engagement ON users(default_engagement_id);
CREATE INDEX idx_users_default_session ON users(default_session_id);
```

### 2. Ensure User-Session Association
```sql
-- Ensure every user has a user_account_association
-- This links users to their default client account with a role
INSERT INTO user_account_associations (user_id, client_account_id, role, created_by)
SELECT 
    u.id,
    u.default_client_account_id,
    'member',
    u.id
FROM users u
WHERE u.default_client_account_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM user_account_associations uaa 
    WHERE uaa.user_id = u.id AND uaa.client_account_id = u.default_client_account_id
);
```

## Implementation Steps

### Phase 1: Database Migration
1. **Update User Model** to include default context fields
2. **Create Migration Script** to add the new columns
3. **Backfill Existing Users** with default context (assign to demo client/engagement)
4. **Create Default Sessions** for all existing users

### Phase 2: Backend Service Updates
1. **Update User Service** to handle default context loading
2. **Update Session Service** to auto-create default sessions
3. **Update Context Service** to use user's default session
4. **Update Authentication** to load user's complete context

### Phase 3: Frontend Updates
1. **Remove Session Switching UI** (since users have one session)
2. **Update Context Loading** to use user's default session
3. **Simplify Data Import** to always use default session
4. **Update Breadcrumbs** to show current context without switching

### Phase 4: Data Import Fix
1. **Fix Session Creation** in data import workflow
2. **Use User's Default Session** instead of generating new UUIDs
3. **Update Analysis Workflow** to use consistent session IDs

## User Creation Workflow

### New User Registration
```python
async def create_user_with_defaults(
    email: str,
    client_account_id: UUID,
    engagement_id: UUID,
    role: str = "member"
) -> User:
    """Create a new user with default context and session."""
    
    # 1. Create the user
    user = User(email=email, ...)
    db.add(user)
    await db.flush()  # Get user ID
    
    # 2. Create default session for the user
    session_name = f"{client_name}-{engagement_name}-{user.email.split('@')[0]}-default"
    default_session = DataImportSession(
        session_name=session_name,
        session_display_name=f"{user.email}'s Default Session",
        engagement_id=engagement_id,
        client_account_id=client_account_id,
        is_default=True,
        auto_created=True,
        created_by=user.id
    )
    db.add(default_session)
    await db.flush()  # Get session ID
    
    # 3. Update user with default context
    user.default_client_account_id = client_account_id
    user.default_engagement_id = engagement_id
    user.default_session_id = default_session.id
    
    # 4. Create user-client association
    association = UserAccountAssociation(
        user_id=user.id,
        client_account_id=client_account_id,
        role=role,
        created_by=user.id
    )
    db.add(association)
    
    await db.commit()
    return user
```

### Existing User Context Loading
```python
async def get_user_context(user_id: UUID) -> UserContext:
    """Get user's complete context using their defaults."""
    
    user = await get_user_with_defaults(user_id)
    
    if not user.default_session_id:
        # Auto-create default session if missing
        await create_default_session_for_user(user)
    
    return UserContext(
        user=user,
        client_account_id=user.default_client_account_id,
        engagement_id=user.default_engagement_id,
        session_id=user.default_session_id
    )
```

## Data Import Workflow Fix

### Current Problem
- Frontend generates UUID for session
- Backend ignores it and uses demo session
- Analysis workflow fails due to session mismatch

### Solution
```python
async def initiate_data_source_analysis(
    context: RequestContext,
    analysis_type: str,
    data_source: Dict[str, Any]
) -> Dict[str, Any]:
    """Use user's default session for all analysis."""
    
    # Get user's default session (not demo session)
    user_context = await get_user_context(context.user_id)
    
    # Use user's actual default session
    session_id = user_context.session_id
    
    # Create workflow state with user's session
    flow_state = DiscoveryFlowState(
        session_id=session_id,
        flow_id=session_id,
        client_account_id=user_context.client_account_id,
        engagement_id=user_context.engagement_id,
        user_id=context.user_id,
        import_session_id=session_id,  # Same as session_id
        status="running",
        current_phase="initialization",
        metadata=metadata
    )
    
    # Continue with analysis...
```

## Benefits of This Approach

### 1. Simplicity
- No complex session merging logic
- No session switching UI complexity
- Clear single source of truth for user context

### 2. Data Consistency
- All user data lives in their default session
- No data fragmentation across multiple sessions
- Clear audit trail and data ownership

### 3. Performance
- No session switching overhead
- Simplified context loading
- Reduced database queries

### 4. User Experience
- Users don't need to manage multiple sessions
- Clear understanding of their workspace
- Consistent data view across all operations

## Migration Strategy

### For Existing Users
1. **Assign Default Context**: All existing users get assigned to demo client/engagement
2. **Create Default Sessions**: Auto-create default sessions for all users
3. **Update User Records**: Backfill default context fields
4. **Preserve Existing Data**: Migrate existing data to user's default session

### For New Users
1. **Registration Process**: Require client/engagement assignment during registration
2. **Auto-Session Creation**: Automatically create default session
3. **Context Enforcement**: Ensure all operations use user's default context

## Context Switcher Simplification

Since users operate within a single default session, the context switcher becomes:
- **Display Only**: Shows current client > engagement > session
- **No Switching**: Users can't switch sessions (they have only one)
- **Admin Function**: Only admins can reassign users to different contexts
- **Session Info**: Shows session statistics and metadata

## Future Enhancements (Optional)

If needed later, we can add:
1. **Session Snapshots**: Create read-only snapshots of sessions at specific points
2. **Session Cloning**: Allow users to create new sessions based on existing ones
3. **Multi-Engagement Access**: Allow users to have default sessions in multiple engagements
4. **Session Templates**: Pre-configured session setups for common scenarios

## Implementation Priority

### Immediate (Fix Current Issues)
1. Fix data import session creation bug
2. Update user context loading to use actual user defaults
3. Create default sessions for existing users

### Short Term (Complete Implementation)
1. Update database schema with user defaults
2. Implement auto-session creation for new users
3. Update frontend to use single session approach

### Long Term (Enhancements)
1. Admin interface for user context management
2. Session analytics and reporting
3. Advanced session configuration options

This simplified approach addresses the core issues while providing a solid foundation for future enhancements if needed. 