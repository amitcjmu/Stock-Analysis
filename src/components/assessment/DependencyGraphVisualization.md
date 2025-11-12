# DependencyGraphVisualization Component

## Overview

A D3.js force-directed graph visualization component for displaying application and infrastructure dependencies in the assessment flow.

## Features

- **Force-Directed Layout**: Uses D3.js force simulation for automatic node positioning
- **UUID Resolution**: Automatically converts UUIDs to human-readable names using lookup arrays
- **Interactive Nodes**: Drag to reposition, hover for details, zoom/pan support
- **Type-Based Styling**: Color-coded nodes (blue circles for applications, green squares for servers)
- **Responsive Design**: Adapts to container width with Tailwind CSS
- **Empty State Handling**: Graceful fallback when no dependencies exist
- **Legend**: Visual guide explaining node types and colors

## Installation

```bash
npm install d3 @types/d3
```

## Usage

```tsx
import { DependencyGraphVisualization } from '@/components/assessment/DependencyGraphVisualization';

// Define your data
const dependencyGraph = {
  nodes: [
    { id: 'uuid-1', name: 'App Name', type: 'application' },
    { id: 'uuid-2', name: 'Server Name', type: 'server' }
  ],
  edges: [
    { source: 'uuid-1', target: 'uuid-2', type: 'hosting' }
  ],
  metadata: {
    dependency_count: 1,
    node_count: 2
  }
};

const applications = [
  { id: 'uuid-1', canonical_name: 'Customer Portal' }
];

const infrastructure = [
  { id: 'uuid-2', name: 'web-server-01' }
];

// Render component
<DependencyGraphVisualization
  dependency_graph={dependencyGraph}
  applications={applications}
  infrastructure={infrastructure}
/>
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `dependency_graph` | `DependencyGraph` | Yes | Graph structure with nodes, edges, and metadata |
| `applications` | `Application[]` | Yes | Array of applications for UUID→name lookup |
| `infrastructure` | `Infrastructure[]` | Yes | Array of infrastructure for UUID→name lookup |

### Type Definitions

```typescript
interface DependencyGraph {
  nodes: Array<{
    id: string;        // UUID
    name: string;      // Fallback name
    type: string;      // 'application' or 'server'
  }>;
  edges: Array<{
    source: string;    // Source node UUID
    target: string;    // Target node UUID
    type: string;      // 'hosting', 'communication', 'data_flow'
  }>;
  metadata: {
    dependency_count: number;
    node_count: number;
  };
}

interface Application {
  id: string;              // UUID
  canonical_name: string;  // Display name
}

interface Infrastructure {
  id: string;  // UUID
  name: string; // Display name
}
```

## UUID to Name Mapping

The component builds an internal lookup map to resolve UUIDs to names:

1. **Applications**: Maps `application.id` → `application.canonical_name`
2. **Infrastructure**: Maps `infrastructure.id` → `infrastructure.name`
3. **Fallback**: If UUID not found, uses `node.name` or `node.id`

```typescript
// Internal mapping logic
const nameMap = new Map<string, string>();
applications?.forEach(app => nameMap.set(app.id, app.canonical_name));
infrastructure?.forEach(srv => nameMap.set(srv.id, srv.name));

// Resolves node names
const displayName = nameMap.get(node.id) || node.name || node.id;
```

## D3.js Force Simulation

The component uses D3's force-directed graph layout with:

- **Link Force**: Connects nodes with configurable distance (150px)
- **Charge Force**: Repulsion between nodes (-300 strength)
- **Center Force**: Gravitates nodes to graph center
- **Collision Force**: Prevents node overlap (50px radius)

```typescript
const simulation = d3.forceSimulation<D3GraphNode>(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(150))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(50));
```

## Visual Design

### Node Types

- **Applications**: Blue circles (`#3b82f6`) with 25px radius
- **Servers**: Green rounded squares (`#10b981`) with 50x50px dimensions

### Edge Types

- **All Edges**: Gray arrows (`#6b7280`) with varying thickness
  - `hosting`: 2px stroke width
  - Other types: 1.5px stroke width

### Legend

Displays at the top of the graph:
- Circle icon + "Application" label (blue)
- Square icon + "Server/Infrastructure" label (green)
- Node count badge
- Dependency count badge

## Interactions

| Action | Behavior |
|--------|----------|
| Drag node | Repositions node with force simulation |
| Hover node | Shows tooltip with name, type, and UUID |
| Scroll | Zoom in/out (0.5x to 3x scale) |
| Pan | Click and drag background to pan view |

## Empty State

When `nodes.length === 0`, displays:
- Large network icon (gray)
- "No Dependencies Found" heading
- Helper text: "Dependencies will appear here once discovered"

## Responsive Behavior

- **Width**: Adapts to parent container width
- **Height**: Fixed at 600px minimum
- **Resize Handling**: Re-renders on window resize events

## Performance

- **Node Limit**: Optimized for up to 100 nodes
- **Edge Limit**: Handles up to 200 edges efficiently
- **Simulation**: Auto-stops after stabilization
- **Cleanup**: Properly stops simulation on component unmount

## Example Use Cases

1. **Assessment Dependency Analysis**: Visualize application-to-server hosting relationships
2. **Cross-Application Mapping**: Show communication patterns between applications
3. **Infrastructure Dependencies**: Display server-to-server connections
4. **Migration Planning**: Identify tightly coupled systems before migration

## Integration with Assessment Flow

```tsx
// Fetch dependency data from assessment flow
const { sixrDecisions } = useAssessmentFlow();

// Extract dependency graph from assessment results
const dependencyGraph = sixrDecisions[applicationId]?.dependency_graph;

// Render visualization
<DependencyGraphVisualization
  dependency_graph={dependencyGraph}
  applications={selectedApplications}
  infrastructure={infrastructureList}
/>
```

## Accessibility

- **Keyboard**: Tab to focus nodes (future enhancement)
- **Screen Readers**: Node tooltips provide text descriptions
- **Color Blind**: Distinct shapes (circles vs squares) beyond color coding
- **High Contrast**: Strong border colors for better visibility

## Browser Compatibility

- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

Requires SVG and D3.js v7+ support.

## Known Limitations

1. **Large Graphs**: Performance degrades beyond 200 nodes (consider pagination)
2. **Mobile**: Touch drag may conflict with zoom gestures
3. **Print**: Force layout may vary between renders (consider static layout for print)

## Future Enhancements

- [ ] Clustering/grouping of related nodes
- [ ] Filter by node type or edge type
- [ ] Export graph as PNG/SVG
- [ ] Minimap for large graphs
- [ ] Search/highlight specific nodes
- [ ] Timeline view for dependency changes

## Related Components

- `DependencyVisualization.tsx`: List-based dependency view (non-graph)
- `DependencyGraph.tsx`: ReactFlow-based alternative in discovery flow
- `ApplicationDependencyMatrix.tsx`: Matrix view for dependencies

## References

- [D3.js Force Simulation Documentation](https://d3js.org/d3-force)
- [React + D3 Integration Best Practices](https://2019.wattenberger.com/blog/react-and-d3)
- ADR-012: Flow Status Management Separation
- Issue #980: Intelligent Multi-Layer Gap Detection System
