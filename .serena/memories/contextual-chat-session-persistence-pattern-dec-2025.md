# Contextual Chat Session Persistence Pattern (December 2025)

## Overview
Pattern for persistent chat conversations with Redis backend and sessionStorage frontend, preserving history across page navigation.

## Backend: Redis-Backed Conversation Storage

**Problem**: Chat conversations lost when user navigates or refreshes.

**Solution**: Redis with in-memory fallback for persistence.

```python
# Key pattern (tenant-scoped)
REDIS_KEY_PREFIX = "chat:conversation:"
CONVERSATION_TTL_SECONDS = 86400 * 7  # 7 days

def _get_tenant_key(context: RequestContext, conversation_id: str) -> str:
    return f"{REDIS_KEY_PREFIX}{context.client_account_id}:{context.engagement_id}:{conversation_id}"

# Handle both Upstash (sync) and standard Redis (async)
async def _get_conversation(key: str) -> Optional[List[ChatMessage]]:
    redis = get_redis_manager()
    if redis.is_available():
        if redis.client_type == "upstash":
            data = redis.client.get(key)  # Sync
        else:
            data = await redis.client.get(key)  # Async
        if data:
            return [ChatMessage(**msg) for msg in json.loads(data)]
    return _fallback_store.get(key)  # In-memory fallback
```

**DoS Protection**:
```python
MAX_CONVERSATIONS_PER_TENANT = 100
MAX_MESSAGES_PER_CONVERSATION = 50
```

## Frontend: sessionStorage + History Loading

**Problem**: Need conversation continuity within browser session.

**Solution**: sessionStorage for ID, API for history.

```typescript
const CONVERSATION_ID_KEY = 'chat_conversation_id';

// Initialize conversation ID
const [conversationId] = useState<string>(() => {
  if (typeof window !== 'undefined') {
    const stored = sessionStorage.getItem(CONVERSATION_ID_KEY);
    if (stored) return stored;
    const newId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem(CONVERSATION_ID_KEY, newId);
    return newId;
  }
  return `chat-${Date.now()}`;
});

// Load history from backend
useEffect(() => {
  const loadHistory = async () => {
    const response = await apiCall(`/chat/conversation/${conversationId}`, { method: 'GET' });
    if (response.status === 'success' && response.messages?.length > 0) {
      setMessages(response.messages.map(msg => ({...msg})));
    }
  };
  loadHistory();
}, [conversationId]);
```

## Page Navigation: Conditional Navigation Messages

**Problem**: Navigation messages accumulated even when no actual conversation existed.

**Solution**: Only show navigation messages when user has sent messages.

```typescript
useEffect(() => {
  if (previousRouteRef.current !== currentRoute && historyLoaded) {
    setMessages(prev => {
      // Check if there are actual user messages
      const hasUserMessages = prev.some(msg => msg.role === 'user');

      if (hasUserMessages) {
        // APPEND navigation message only if actual conversation exists
        return [...prev, {
          role: 'assistant',
          content: `📍 *You navigated to ${pageContext?.page_name}.*\n\n${getInitialGreeting()}`,
          timestamp: new Date().toISOString(),
        }];
      } else {
        // No conversation - just replace greeting with fresh page context
        return [{
          id: '1',
          role: 'assistant',
          content: getInitialGreeting(),
          timestamp: new Date().toISOString(),
          suggested_actions: pageContext?.actions?.slice(0, 3) || [],
        }];
      }
    });
  }
  previousRouteRef.current = currentRoute;
}, [pageContext]);
```

## Page Context Registry: Route Coverage

**Problem**: "Unknown Page" shown in chat when route not in pageContextRegistry.

**Solution**: Ensure ALL sidebar routes are registered.

```typescript
// File: src/config/pageContextRegistry.ts
// Must include entries for ALL navigable routes

'/collection/overview': {
  page_name: 'Data Collection',
  route: '/collection/overview',
  route_pattern: '/collection/overview',
  flow_type: 'collection',
  // ... rest of context
},

'/assess/treatment': {
  page_name: 'Assessment Treatment',
  route: '/assess/treatment',
  route_pattern: '/assess/treatment',
  flow_type: 'assessment',
  // ... rest of context
},
```

**Checklist when adding new routes**:
1. Add sidebar menu item → Add pageContextRegistry entry
2. Check Sidebar.tsx for ALL flow routes
3. Test chat shows correct page name after navigation

## Clear History Pattern

```typescript
const clearHistory = (): void => {
  const newId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  sessionStorage.setItem(CONVERSATION_ID_KEY, newId);
  setConversationId(newId);
  setMessages([initialGreeting]);

  // Fire-and-forget backend cleanup
  apiCall(`/chat/conversation/${conversationId}`, { method: 'DELETE' }).catch(() => {});
};
```

## Static Context Registry Scaling

**Misconception**: Qodo Bot flagged pageContextRegistry as "High" scaling concern.

**Reality**: Static TypeScript objects have NO scaling issues:
- ~100KB parsed once at bundle load
- No per-session memory allocation
- Supports unlimited concurrent sessions
- "High" concern is about **maintainability** (1400+ lines), not scalability

**When it becomes a problem**:
- Dynamic content per user/tenant → Move to API/database
- Frequent non-developer updates → Move to CMS
- 1000+ pages → Consider lazy loading chunks
