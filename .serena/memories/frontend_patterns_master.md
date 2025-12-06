# Frontend Patterns Master

**Last Updated**: 2025-12-05
**Version**: 1.0
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **State Recalculation**: Update derived state (summaries) inside `setState` callback after mutations
> 2. **Session Persistence**: Use `sessionStorage` for IDs, fetch history from backend API
> 3. **Navigation Messages**: Only show navigation context when user has actual conversation
> 4. **Page Context Registry**: ALL sidebar routes must have entries for chat context
> 5. **Field Naming**: Use `snake_case` for all API fields (matches backend)

---

## Table of Contents

1. [Overview](#overview)
2. [React State Patterns](#react-state-patterns)
3. [Chat Session Persistence](#chat-session-persistence)
4. [Page Context Registry](#page-context-registry)
5. [API Integration Patterns](#api-integration-patterns)
6. [Anti-Patterns](#anti-patterns)
7. [Code Templates](#code-templates)

---

## Overview

### What This Covers
Frontend patterns for React/Next.js components in the migration UI, including state management, chat persistence, and API integration.

### When to Reference
- Implementing list views with summary statistics
- Adding chat/conversation features
- Creating new sidebar navigation routes
- Handling API field naming

### Key Files
- `src/pages/FeedbackView.tsx` - State recalculation example
- `src/components/chat/ContextualChat.tsx` - Session persistence
- `src/config/pageContextRegistry.ts` - Route context definitions

---

## React State Patterns

### Pattern 1: State Recalculation After Deletion

**Problem**: Deleting item from list leaves summary statistics stale.

**Solution**: Recalculate derived state inside `setState` callback for atomicity.

```typescript
// Step 1: Extract summary calculation into reusable function
const calculateSummary = useCallback((items: FeedbackItem[]): void => {
  if (items.length > 0) {
    const total = items.length;
    const avgRating = items.reduce((sum, f) => sum + f.rating, 0) / total;
    const byStatus = items.reduce((acc, f) => {
      acc[f.status] = (acc[f.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    setSummary({
      total,
      avgRating,
      byStatus: {
        new: byStatus['new'] || 0,
        reviewed: byStatus['reviewed'] || 0,
        resolved: byStatus['resolved'] || 0
      },
    });
  } else {
    setSummary({ total: 0, avgRating: 0, byStatus: { new: 0, reviewed: 0, resolved: 0 } });
  }
}, []);

// Step 2: Call inside setState callback for atomicity
const handleDelete = useCallback(async (feedbackId: string): Promise<void> => {
  if (!window.confirm('Are you sure?')) return;

  try {
    await apiCall(`chat/feedback/${feedbackId}`, { method: 'DELETE' });

    // Remove AND recalculate atomically
    setFeedback(prev => {
      const updated = prev.filter(f => f.id !== feedbackId);
      calculateSummary(updated);  // Recalculate with filtered array
      return updated;
    });
  } catch (error) {
    console.error('Failed to delete:', error);
    alert('Failed to delete. Please try again.');
  }
}, [calculateSummary]);
```

**Why This Works**:
- Atomicity: Summary recalculation happens with updated array before React batches
- Reusability: `calculateSummary` works for fetch, delete, filter changes
- Immediate UI: Summary cards update instantly without re-fetch

---

## Chat Session Persistence

### Pattern 2: Redis-Backed Conversation Storage

**Problem**: Chat conversations lost when user navigates or refreshes.

**Solution**: Redis with in-memory fallback for persistence.

```python
# Backend key pattern (tenant-scoped)
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

### Pattern 3: Frontend sessionStorage + History Loading

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

### Pattern 4: Conditional Navigation Messages

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
          content: `You navigated to ${pageContext?.page_name}.\n\n${getInitialGreeting()}`,
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

### Pattern 5: Clear History

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

---

## Page Context Registry

### Pattern 6: Route Coverage

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

### Scaling Considerations

**Misconception**: Static pageContextRegistry flagged as "High" scaling concern.

**Reality**: Static TypeScript objects have NO scaling issues:
- ~100KB parsed once at bundle load
- No per-session memory allocation
- Supports unlimited concurrent sessions
- "High" concern is about **maintainability** (1400+ lines), not scalability

**When it becomes a problem**:
- Dynamic content per user/tenant → Move to API/database
- Frequent non-developer updates → Move to CMS
- 1000+ pages → Consider lazy loading chunks

---

## API Integration Patterns

### Pattern 7: Field Naming Convention

**Rule**: ALL fields use `snake_case` to match backend exactly.

```typescript
// CORRECT - snake_case matches backend
interface FlowData {
  flow_id: string;
  master_flow_id: string;
  client_account_id: number;
}

// WRONG - never create new camelCase interfaces
interface FlowData {
  flowId: string;  // NO!
  masterFlowId: string;  // NO!
}
```

### Pattern 8: API Request Body vs Query Parameters

**Rule**: POST/PUT/DELETE use request body, NEVER query parameters.

```typescript
// WRONG - Causes 422 errors
await apiCall(`/api/endpoint?param=value`, { method: 'POST' })

// CORRECT
await apiCall(`/api/endpoint`, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
})
```

---

## Anti-Patterns

### Don't: Fetch After Delete

```typescript
// WRONG - Unnecessary network call
const handleDelete = async (id: string) => {
  await apiCall(`/items/${id}`, { method: 'DELETE' });
  await fetchItems();  // Re-fetches entire list just to update summary
};

// CORRECT - Update locally
const handleDelete = async (id: string) => {
  await apiCall(`/items/${id}`, { method: 'DELETE' });
  setItems(prev => {
    const updated = prev.filter(item => item.id !== id);
    calculateSummary(updated);
    return updated;
  });
};
```

### Don't: Use camelCase for API Fields

```typescript
// WRONG
const { flowId, masterFlowId } = data;

// CORRECT
const { flow_id, master_flow_id } = data;
```

### Don't: Skip Page Context Registry

```typescript
// WRONG - Results in "Unknown Page" in chat
// Adding route to Sidebar.tsx without pageContextRegistry entry

// CORRECT - Always add both
// 1. Add to Sidebar.tsx
// 2. Add to pageContextRegistry.ts
```

---

## Code Templates

### Template 1: List View with Summary Cards

```typescript
interface SummaryData {
  total: number;
  avgRating: number;
  byStatus: Record<string, number>;
}

const ListViewWithSummary: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [summary, setSummary] = useState<SummaryData | null>(null);

  const calculateSummary = useCallback((data: Item[]): void => {
    if (data.length > 0) {
      setSummary({
        total: data.length,
        avgRating: data.reduce((s, i) => s + i.rating, 0) / data.length,
        byStatus: data.reduce((acc, i) => {
          acc[i.status] = (acc[i.status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
      });
    } else {
      setSummary({ total: 0, avgRating: 0, byStatus: {} });
    }
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    await apiCall(`/items/${id}`, { method: 'DELETE' });
    setItems(prev => {
      const updated = prev.filter(item => item.id !== id);
      calculateSummary(updated);
      return updated;
    });
  }, [calculateSummary]);

  // ... render with summary cards and item list
};
```

---

## Troubleshooting

### Issue: Summary cards show stale data after delete

**Cause**: Summary not recalculated after removing item from state.

**Fix**: Call `calculateSummary(updated)` inside `setItems` callback.

### Issue: Chat shows "Unknown Page"

**Cause**: Route missing from pageContextRegistry.

**Fix**: Add entry to `src/config/pageContextRegistry.ts` with all required fields.

### Issue: Conversation lost on page refresh

**Cause**: Using `localStorage` (persists) vs `sessionStorage` (tab-scoped).

**Fix**: Use `sessionStorage` for session continuity, backend API for history.

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `react-state-recalculation-after-deletion-pattern-2025-12` | 2025-12 | Delete + recalculate pattern |
| `contextual-chat-session-persistence-pattern-dec-2025` | 2025-12 | Chat persistence, navigation, registry |

---

## Search Keywords

react, state, delete, summary, recalculation, useCallback, chat, session, persistence, sessionStorage, redis, navigation, pageContextRegistry, snake_case, field_naming
