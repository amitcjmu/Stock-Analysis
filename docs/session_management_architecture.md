# Session Management Architecture

## Overview
This document outlines the streamlined architecture for managing user sessions within the application, focusing on efficient context loading and minimal API calls. The system prioritizes performance by loading user context first, then their default engagement and session in a single flow.

## Core Concepts

### 1. User Context Hierarchy
1. **User Authentication**
   - User logs in or defaults to demo user
   - System loads user profile with default client/engagement
   - Default session is loaded with engagement data

2. **Session Definition**
   - A **Session** represents a user's workspace within an engagement
   - Each engagement has exactly one default session
   - Users can create additional sessions as needed

### 2. Key Properties

#### User Profile
- `id`: Unique user identifier
- `email`: User's email address
- `default_client_id`: User's primary client
- `default_engagement_id`: User's primary engagement

#### Engagement
- `id`: Unique identifier
- `name`: Engagement name
- `client_id`: Owning client
- `default_session`: The default session (embedded in engagement response)

#### Session
- `id`: Unique identifier (UUID)
- `name`: User-friendly name
- `engagement_id`: Owning engagement
- `is_default`: Boolean flag
- `created_at`: Timestamp
- `created_by`: User ID of creator

## Architecture

### 1. Database Schema
```sql
-- Users table (simplified)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    default_engagement_id UUID REFERENCES engagements(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Engagements Table
```sql
CREATE TABLE engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    client_id UUID NOT NULL REFERENCES clients(id),
    default_session_id UUID REFERENCES data_import_sessions(id),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Sessions Table
```sql
CREATE TABLE data_import_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT FALSE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT one_default_per_engagement 
        UNIQUE (engagement_id, is_default) 
        DEFERRABLE INITIALLY DEFERRED
);

-- Add foreign key after both tables exist
ALTER TABLE engagements 
    ADD CONSTRAINT fk_default_session 
    FOREIGN KEY (default_session_id) 
    REFERENCES data_import_sessions(id) 
    ON DELETE SET NULL;
```

## Backend Services

### User Service
```python
class UserService:
    async def get_current_user(self) -> User:
        """Get or create user session with fallback to demo user"""
        pass
        
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user details including default engagement and session"""
        pass
```

### Engagement Service
```python
class EngagementService:
    async def get_engagement(
        self, 
        engagement_id: UUID, 
        include_session: bool = True
    ) -> Engagement:
        """Get engagement with optional session inclusion"""
        pass
        
    async def get_user_default_engagement(
        self, 
        user_id: UUID
    ) -> Optional[Engagement]:
        """Get user's default engagement with default session"""
        pass
```

### Session Service
```python
class SessionService:
    async def get_session(
        self, 
        session_id: UUID, 
        user_id: UUID
    ) -> Session:
        """Get session with permission check"""
        pass
        
    async def switch_session(
        self, 
        user_id: UUID, 
        session_id: UUID
    ) -> UserProfile:
        """Update user's current session"""
        pass
```

## API Endpoints

### User API
```
GET    /api/v1/users/me              # Get current user context
PUT    /api/v1/users/me/preferences  # Update user preferences
```

### Engagement API
```
GET    /api/v1/engagements/me/default  # Get user's default engagement
GET    /api/v1/engagements/{id}       # Get engagement by ID
```

### Session API
```
GET    /api/v1/sessions/{id}          # Get session by ID
POST   /api/v1/sessions              # Create new session
PUT    /api/v1/sessions/{id}         # Update session
POST   /api/v1/sessions/{id}/switch  # Switch to session
```

## Frontend Architecture

### App Initialization Flow
1.  **Setup QueryClient**: Wrap the application in React Query's `QueryClientProvider`.
2.  **Load User Profile**: Fetch the user's profile to get their default engagement ID.
3.  **Load Initial Session Data**: Fetch the sessions for the default engagement and identify the default session ID.
4.  **Set Global Context**: Populate `AppContext` with the loaded IDs (`currentEngagementId`, `currentSessionId`).
5.  **Render Application**: Render the app with loading states. React Query will handle fetching data for the components based on the context IDs.
6.  **Handle Errors**: Implement robust error handling for the initial context load.

### Context Providers

#### AppContext (Single Source of Truth)
The `AppContext` is the central hub for the application's current context. It holds only the essential identifiers and state, delegating data fetching to React Query.

```typescript
interface AppContextType {
  // Current Context Identifiers
  currentEngagementId: string | null;
  currentSessionId: string | null;
  
  // Available options (optional, can also be fetched via hooks)
  availableEngagements: Engagement[];
  
  // State Management
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  
  // Actions
  setCurrentEngagement: (engagementId: string) => void;
  setCurrentSession: (sessionId: string) => void;
  refreshContext: () => Promise<void>;
}
```

#### SessionContext (Deprecated)
The `SessionContext` is deprecated. Its responsibilities are now handled by `AppContext` for state management and custom React Query hooks for data fetching (e.g., `useSessionsList`).

### Data Fetching Strategy: React Query Hooks
We will use **TanStack Query (React Query)** as the primary mechanism for fetching, caching, and synchronizing server state.

1.  **Context-Aware API Client**: A singleton `apiClient` will be used to automatically inject context headers (`X-Engagement-Id`, `X-Session-Id`) into every request.

2.  **Custom Hooks**: For each data type, we will create a custom hook that encapsulates the data fetching logic using `useQuery`.

3.  **Component-Level Data Fetching**: Components will use these custom hooks to fetch data declaratively. The hooks will get the required IDs from `AppContext`.

**Example Workflow:**
1.  A component calls `const { currentEngagementId, currentSessionId } = useAppContext()`.
2.  It then calls a custom hook: `const { data, isLoading } = useDiscoveryData(currentEngagementId, currentSessionId)`.
3.  The `useDiscoveryData` hook uses `useQuery` with a unique key like `['discoveryData', currentEngagementId, currentSessionId]`.
4.  React Query handles the API call via the `apiClient`, caching, deduplication, and background refetching.

### Key Components

1.  **AppInitializer**
   - Wraps the app in `QueryClientProvider`.
   - Handles initial data loading to populate `AppContext`.
   - Shows global loading/error states.
   - Renders the app when `AppContext` is initialized.

2.  **SessionSelector**
   - Uses a `useSessionsList` hook to fetch available sessions for the current engagement.
   - Calls `setCurrentSession` from `AppContext` on selection change.
   - Displays loading/error states from the hook.

3.  **SessionForm**
   - Uses React Query's `useMutation` hook to handle form submissions for creating/editing sessions.
   - Invalidates relevant queries upon successful mutation to refetch data automatically.

## Performance Considerations

### 1. Reduced API Calls
-   **Automatic Request Deduplication**: TanStack Query automatically deduplicates identical requests made in a short time window. If multiple components request the same data, only one API call is made.
-   **Client-side Caching**: Data is cached in memory, preventing redundant fetches when navigating between pages or re-rendering components.
-   Single API call for initial context.
-   Default session included in engagement.
-   Client-side caching with React Query
- Load only necessary data
- Use pagination for large lists
- Cache responses when possible

### 2. State Management
- Keep global state minimal
- Use React Query for server state
- Optimize re-renders

### 3. API Optimization
- Combine related requests
- Use GraphQL where appropriate
- Implement proper caching headers

## Security Considerations

### 1. Authentication
- JWT-based auth
- Short-lived access tokens
- Secure cookie storage

### 2. Authorization
- Role-based access control
- Session validation
- Permission checks on all operations

### 3. Data Protection
- Encrypt sensitive data
- Validate all inputs
- Sanitize outputs

### New Tables
```
session_data_mappings (
    id: UUID (PK)
    session_id: UUID (FK to data_import_sessions)
    entity_type: String  # 'asset', 'dependency', etc.
    entity_id: UUID
    data: JSONB
    created_at: Timestamp
)
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Update database schema
2. Implement SessionManagementService
3. Implement ContextService
4. Create basic API endpoints

### Phase 2: Frontend Integration
1. Build context switcher component
2. Implement session management UI
3. Update all data-fetching logic to respect session context

### Phase 3: Advanced Features
1. Implement session merging
2. Add conflict resolution UI
3. Add bulk operations

### Phase 4: Testing & Optimization
1. Performance testing with large datasets
2. Optimize session switching
3. Add caching where needed

## Security Considerations

1. **Data Isolation**: Ensure users can only access sessions for engagements they have access to
2. **Validation**: Validate all session operations on the server
3. **Audit Logging**: Log all session creation/modification
4. **Rate Limiting**: Prevent abuse of session operations

## Performance Considerations

1. **Indexing**: Ensure proper indexes on session lookups
2. **Caching**: Cache frequently accessed session data
3. **Lazy Loading**: Only load session data when needed
4. **Batch Operations**: Support batch operations for large merges

## Future Enhancements

1. **Session Templates**: Save session configurations as templates
2. **Versioning**: Track changes to sessions over time
3. **Collaboration**: Allow multiple users to work on the same session
4. **Scheduled Merges**: Schedule automatic merges from one session to another

# Session Management Refactoring & Developer Guide

## 1. Executive Summary

The application's session and context management architecture has been completely overhauled to address critical stability and performance issues. We have migrated from a complex, dual-context system to a streamlined, modern architecture centered around a single source of truth for context identifiers and a robust data-fetching layer powered by **TanStack Query (React Query)**.

This refactoring eliminates race conditions, reduces redundant API calls, simplifies component logic, and provides a clear, predictable pattern for developers to follow when interacting with server state. The legacy `AppContextProvider` (`useAppContext` hook) and `SessionProvider` (`useSession` hook) are now deprecated and have been replaced by this new system.

## 2. The Problem: A Dual-Context System

The previous architecture suffered from a fundamental flaw: **two parallel context systems were attempting to manage the same state.**

1.  **`AuthContext`**: Managed user authentication.
2.  **`AppContextProvider` / `useAppContext`**: Managed client, engagement, and session objects, fetching data and storing it in `localStorage`.
3.  **`SessionProvider` / `useSession`**: A third layer that specifically managed session state, often conflicting with `useAppContext`.

This resulted in:
*   **Race Conditions**: Multiple components trying to fetch and set the same data simultaneously on page load.
*   **Inconsistent State**: The UI could display data from different contexts at the same time, leading to confusing and unpredictable behavior.
*   **Redundant API Calls**: Without a centralized caching mechanism, the same data was fetched repeatedly across the application.
*   **Complex Component Logic**: Developers had to write complex `useEffect` hooks to manage data fetching, loading, and error states manually.

## 3. The New Architecture: A Single Source of Truth

The new architecture is built on two core principles: centralizing context *identifiers* and decentralizing *data fetching*.

### 3.1. Single Source of Truth: `AuthContext`

`AuthContext` (`/src/contexts/AuthContext.tsx`) is now the **single source of truth for the application's current context identifiers**. It holds and controls:

*   `user`: The authenticated user object.
*   `currentEngagementId: string | null`: The ID of the currently selected engagement.
*   `currentSessionId: string | null`: The ID of the currently selected session.

It provides functions like `setCurrentEngagementId` and `setCurrentSessionId` to modify this state. **No other part of the application should manage these IDs.**

### 3.2. Data Fetching: TanStack Query & Custom Hooks

All server state (data fetched from the API) is now managed by **TanStack Query**. We no longer store fetched data objects in React context. Instead, we have created a suite of simple, reusable **custom hooks**.

*   **`useClients()`**: Fetches the list of all clients.
*   **`useEngagements()`**: Fetches the list of engagements for the current client.
*   **`useSessions()`**: Fetches the list of sessions for the `currentEngagementId`.
*   **Mutation Hooks** (`useCreateSession`, `useUpdateSession`, etc.): Handle creating, updating, and deleting data on the server.

These hooks provide simple, declarative access to data, along with loading states, error states, and automatic caching, completely eliminating the need for manual data fetching in `useEffect`.

## 4. Developer's Guide: Working with the New System

As a developer, you will follow these patterns to interact with context and data.

### 4.1. How to Access the Current Context

To know which engagement or session is currently selected, use the `useAuth` hook.

```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, currentEngagementId, currentSessionId } = useAuth();

  // Now you have the IDs to pass to other hooks or services.
  // ...
}
```

### 4.2. How to Fetch Data (The Right Way)

Never fetch data manually in a `useEffect` hook. Instead, use the provided custom data-fetching hooks.

**Example: Displaying a list of sessions**

```typescript
import { useSessions } from '@/contexts/SessionContext';

function SessionListComponent() {
  // This hook gets the currentEngagementId from useAuth automatically.
  const { data: sessions = [], isLoading, isError, error } = useSessions();

  if (isLoading) {
    return <div>Loading sessions...</div>;
  }

  if (isError) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <ul>
      {sessions.map(session => (
        <li key={session.id}>{session.name}</li>
      ))}
    </ul>
  );
}
```

### 4.3. How to Create, Update, or Delete Data (Mutations)

To change data on the server, use the corresponding mutation hook. These hooks handle the API call, loading state, and automatically refetching related data upon success.

**Example: A form to create a new session**

```typescript
import { useCreateSession } from '@/contexts/SessionContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

function CreateSessionForm() {
  const [name, setName] = useState('');
  const createSessionMutation = useCreateSession();

  const handleSubmit = async () => {
    try {
      // Call the mutation
      await createSessionMutation.mutateAsync({ name });
      // On success, the hook automatically shows a toast and refetches the session list!
      setName('');
    } catch (e) {
      // The hook's onError callback handles showing an error toast.
      console.error(e);
    }
  };

  return (
    <div>
      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="New session name" />
      <Button onClick={handleSubmit} disabled={createSessionMutation.isPending}>
        {createSessionMutation.isPending ? 'Creating...' : 'Create Session'}
      </Button>
    </div>
  );
}
```

### 4.4. The Golden Rule: What NOT to Do

To maintain a stable and performant application, **AVOID** the following patterns:

*   **DON'T** use `useEffect` to fetch data from the API. Use the provided TanStack Query hooks.
*   **DON'T** store server state (arrays of sessions, engagements, etc.) in `useState`. Let React Query manage this data.
*   **DON'T** access `localStorage` directly to get or set context IDs. Use the functions from `useAuth` (`setCurrentSessionId`, etc.).
*   **DON'T** use the old `useAppContext` from `/src/hooks/useContext.tsx`. This is deprecated and will be removed. If you find a component using it, it needs to be refactored.
