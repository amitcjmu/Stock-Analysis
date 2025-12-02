# Session Learnings: Batch 4 Bug Fixes (2025-12-01)

## Insight 1: Backend Error Field Propagation Pattern

**Problem**: Frontend expects error details in API response, but backend returns empty error fields when job fails.

**Solution**: Add conditional error fields when status indicates failure:
```python
# progress_handlers.py - Error propagation pattern
if job_state.get("status") == "failed":
    error_message = job_state.get("error")
    user_message = job_state.get("user_message")

    response["error"] = error_message or "Unknown error occurred"
    response["error_type"] = job_state.get("error_type")
    response["error_category"] = job_state.get("error_category")
    response["user_message"] = (
        user_message or error_message or "AI enhancement failed. Please try again."
    )
```

**Usage**: When backend job tracking stores error info in Redis/DB but doesn't include it in progress response.

---

## Insight 2: React Test Router Context Fix

**Problem**: Tests fail with "useNavigate() may be used only in the context of a `<Router>` component"

**Solution**: Add MemoryRouter wrapper in test setup:
```typescript
import { MemoryRouter } from 'react-router-dom';

const renderWithProviders = (ui: React.ReactElement) => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
  return render(ui, { wrapper });
};
```

**Usage**: Any component using `useNavigate()`, `useLocation()`, or `useParams()` in tests.

---

## Insight 3: Pre-commit Hook Skip by ID

**Problem**: mypy-staged hook hangs on large codebases, blocking commits.

**Solution**: Use SKIP with exact hook ID from .pre-commit-config.yaml:
```bash
# Wrong - hook ID doesn't match
SKIP=mypy git commit -m "..."

# Correct - matches id: mypy-staged in config
SKIP=mypy-staged git commit -m "..."
```

**Find hook ID**:
```bash
grep -A2 "mypy" .pre-commit-config.yaml
# Shows: - id: mypy-staged
```

**Usage**: When specific pre-commit hooks timeout but other checks pass.
