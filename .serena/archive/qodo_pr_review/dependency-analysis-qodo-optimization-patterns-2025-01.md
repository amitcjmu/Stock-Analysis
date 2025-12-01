# Dependency Analysis Feature - Qodo Bot Optimization Patterns

## Session: January 2025 - PR #1029

### Problem 1: Bulk Database Operations (N+1 Query Prevention)

**Issue**: Creating multiple dependencies in a loop causes N+1 query problem.

**Solution**: Bulk operation with upfront validation.

```python
# backend/app/repositories/dependency_repository/generic_commands.py
async def bulk_create_dependencies(
    self,
    source_asset_id: str,
    target_asset_ids: list[str],
    dependency_type: str,
    confidence_score: float = 1.0,
) -> list[AssetDependency]:
    # Validate ALL asset IDs in single query
    all_ids = [UUID(source_asset_id)] + [UUID(tid) for tid in target_asset_ids]
    stmt = select(Asset).where(Asset.id.in_(all_ids))
    found_assets = {str(asset.id): asset for asset in result.scalars().all()}

    # Check for existing dependencies to avoid duplicates
    existing_stmt = select(AssetDependency).where(
        and_(
            AssetDependency.asset_id == UUID(source_asset_id),
            AssetDependency.depends_on_asset_id.in_([UUID(tid) for tid in target_asset_ids])
        )
    )

    # Create or update in batch
    for target_id in target_asset_ids:
        if target_id in existing_deps:
            existing_deps[target_id].confidence_score = confidence_score
        else:
            self.db.add(AssetDependency(...))

    await self.db.flush()
    return created_dependencies
```

**Usage**: Replace loops calling `create_dependency()` with single `bulk_create_dependencies()` call.

---

### Problem 2: TanStack Query Manual State Management

**Issue**: Manual `useState` for loading states causes race conditions.

**Solution**: Use `useMutation` hook with built-in state.

```typescript
// Before (manual state - BAD)
const [isAnalyzing, setIsAnalyzing] = useState(false);
const handleExecuteAnalysis = async () => {
  setIsAnalyzing(true);
  try {
    await api.execute();
    setTimeout(() => refetch(), 2000);
  } finally {
    setIsAnalyzing(false);
  }
};

// After (useMutation - GOOD)
const { mutate: executeAnalysis, isPending: isAnalyzing } = useMutation({
  mutationFn: () => api.execute(),
  onSuccess: () => {
    setTimeout(() => refetch(), 2000);
  },
  onError: (error) => {
    alert(`Failed: ${error.message}`);
  }
});

const handleExecuteAnalysis = () => executeAnalysis();
```

**Benefits**: Prevents race conditions, centralized error handling, idiomatic TanStack Query.

---

### Problem 3: Database Query Optimization (Python Filtering)

**Issue**: Fetching all rows then filtering in Python is inefficient.

**Solution**: Move filtering to SQL WHERE clause.

```python
# Before (Python filtering - BAD)
all_node_ids = {str(app.id) for app in applications} | {str(srv.id) for srv in servers}
result = await self.db.execute(query)  # Fetches ALL dependencies
rows = result.all()

for row in rows:
    source_id = str(row.asset_id)
    target_id = str(row.depends_on_asset_id)
    # Filter in Python
    if source_id in all_node_ids and target_id in all_node_ids:
        edges.append(...)

# After (Database filtering - GOOD)
all_node_ids = {app.id for app in applications} | {srv.id for srv in servers}
query = query.where(
    AssetDependency.asset_id.in_(all_node_ids),
    AssetDependency.depends_on_asset_id.in_(all_node_ids),
)
result = await self.db.execute(query)  # Fetches only relevant rows
rows = result.all()

# All rows guaranteed to match - no Python filtering needed
for row in rows:
    edges.append({
        "source": str(row.asset_id),
        "target": str(row.depends_on_asset_id),
        ...
    })
```

**Performance**: Reduces data transfer and processing overhead significantly.

---

### Problem 4: React Flow Node Overlapping (0,0 Coordinates)

**Issue**: Nodes positioned at (0,0) when type-based layout doesn't account for all nodes.

**Solution**: Hierarchical layout - pure source nodes left, all others right.

```typescript
// src/components/assessment/DependencyGraph.tsx
function calculateNodePositions(nodes, edges) {
  // Identify pure source nodes (ONLY outgoing edges, NO incoming)
  const sourceNodeIds = new Set(edges.map(e => e.source));
  const targetNodeIds = new Set(edges.map(e => e.target));

  const pureSourceNodes = nodes.filter(
    n => sourceNodeIds.has(n.id) && !targetNodeIds.has(n.id)
  );

  const rightColumnNodes = nodes.filter(
    n => !pureSourceNodes.some(source => source.id === n.id)
  );

  // Layout: pure sources at x=0, everything else at x=350
  pureSourceNodes.forEach((node, index) => {
    positions.set(node.id, { x: 0, y: index * 150 });
  });

  rightColumnNodes.forEach((node, index) => {
    positions.set(node.id, { x: 350, y: index * 150 });
  });

  return positions;
}
```

**Key Insight**: Every node MUST get a position. Pure sources = left, everything else = right.

---

### Problem 5: Polling on Query Errors

**Issue**: Infinite polling when query fails repeatedly.

**Solution**: Stop polling on error state.

```typescript
refetchInterval: (data, query) => {
  // CRITICAL: Stop on query error
  if (query.state.status === 'error') {
    return false;
  }

  if (!data) return 5000;
  const status = data.agent_results?.status;

  // Stop on completed OR failed
  if (status === 'completed' || status === 'failed') return false;

  return status === 'running' ? 5000 : 15000;
}
```

**Benefits**: Prevents network spam, improves UX on failures.
