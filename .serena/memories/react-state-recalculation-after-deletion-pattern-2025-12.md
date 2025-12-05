# React State Recalculation After Deletion Pattern

**Date**: 2025-12-04
**Source**: Feedback feature PR #1228
**Context**: FeedbackView.tsx handleDelete function

---

## Problem

When deleting an item from a React list that has derived/summary state, the delete operation removes the item but the summary statistics (totals, averages, counts) become stale.

**Example Issue**: Delete feedback → item removed from list → summary cards still show old count

---

## Solution Pattern

### Step 1: Extract Summary Calculation into Reusable Hook/Function

```typescript
const calculateSummary = useCallback((feedbackItems: FeedbackItem[]): void => {
  if (feedbackItems.length > 0) {
    const total = feedbackItems.length;
    const avgRating = feedbackItems.reduce((sum, f) => sum + f.rating, 0) / total;
    const byStatus = feedbackItems.reduce((acc, f) => {
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
    // Handle empty state
    setSummary({
      total: 0,
      avgRating: 0,
      byStatus: { new: 0, reviewed: 0, resolved: 0 },
    });
  }
}, []);
```

### Step 2: Call Inside setState Callback for Atomicity

```typescript
const handleDelete = useCallback(async (feedbackId: string): Promise<void> => {
  if (!window.confirm('Are you sure you want to delete this item?')) {
    return;
  }

  try {
    await apiCall(`chat/feedback/${feedbackId}`, {
      method: 'DELETE',
    });

    // Remove from local state AND recalculate summary atomically
    setFeedback(prev => {
      const updated = prev.filter(f => f.id !== feedbackId);
      calculateSummary(updated);  // ← Recalculate with filtered array
      return updated;
    });
  } catch (error) {
    console.error('Failed to delete:', error);
    alert('Failed to delete. Please try again.');
  }
}, [calculateSummary]);  // ← Include calculateSummary in deps
```

---

## Why This Pattern Works

1. **Atomicity**: Summary recalculation happens inside `setFeedback` callback, ensuring it uses the updated array before React batches the state updates

2. **Reusability**: `calculateSummary` can be called from:
   - Initial data fetch
   - Delete operations
   - Filter changes
   - Bulk operations

3. **Immediate UI Update**: Summary cards update instantly without waiting for re-fetch

4. **Memory Efficiency**: No need to re-fetch data from server just to update summary

---

## When to Use

- Lists with summary/aggregate displays (counts, averages, totals)
- Dashboard cards showing derived statistics
- Any component with both list view and summary view

---

## Anti-Pattern: Don't Fetch After Delete

```typescript
// ❌ WRONG - Unnecessary network call
const handleDelete = async (id: string) => {
  await apiCall(`/items/${id}`, { method: 'DELETE' });
  await fetchItems();  // Re-fetches entire list just to update summary
};

// ✅ CORRECT - Update locally
const handleDelete = async (id: string) => {
  await apiCall(`/items/${id}`, { method: 'DELETE' });
  setItems(prev => {
    const updated = prev.filter(item => item.id !== id);
    calculateSummary(updated);
    return updated;
  });
};
```

---

## Files Affected

- `src/pages/FeedbackView.tsx` - Original implementation

---

## Keywords

react, state_management, delete, summary, recalculation, useCallback, derived_state, optimistic_update
