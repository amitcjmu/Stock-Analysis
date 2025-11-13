/**
 * Dependency Graph Visualization Component
 *
 * Displays application and server dependencies as a visual graph using React Flow.
 * Supports nodes (applications, servers, databases) and edges (dependency relationships).
 */

import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Network } from 'lucide-react';
import type { DependencyGraph as DependencyGraphData } from '@/lib/api/assessmentDependencyApi';

interface DependencyGraphProps {
  /** Dependency graph data from backend */
  dependencyGraph: DependencyGraphData;
  /** Height of the graph container in pixels */
  height?: number;
}

/**
 * Calculate node positions using a simple force-directed layout approximation
 * For production, consider using dagre or elk for more sophisticated layouts
 */
function calculateNodePositions(
  nodes: DependencyGraphData['nodes'],
  edges: DependencyGraphData['edges']
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const HORIZONTAL_SPACING = 300;
  const VERTICAL_SPACING = 150;

  // Group nodes by type
  const applications = nodes.filter(n => n.type === 'application');
  const servers = nodes.filter(n => n.type === 'server');
  const databases = nodes.filter(n => n.type === 'database');

  // Layout applications in the first column
  applications.forEach((node, index) => {
    positions.set(node.id, {
      x: 0,
      y: index * VERTICAL_SPACING,
    });
  });

  // Layout servers in the second column
  servers.forEach((node, index) => {
    positions.set(node.id, {
      x: HORIZONTAL_SPACING,
      y: index * VERTICAL_SPACING,
    });
  });

  // Layout databases in the third column
  databases.forEach((node, index) => {
    positions.set(node.id, {
      x: HORIZONTAL_SPACING * 2,
      y: index * VERTICAL_SPACING,
    });
  });

  return positions;
}

/**
 * Map node type to background color for visual distinction
 */
function getNodeColor(type: string): string {
  switch (type) {
    case 'application':
      return '#3b82f6'; // Blue
    case 'server':
      return '#10b981'; // Green
    case 'database':
      return '#f59e0b'; // Orange
    default:
      return '#6b7280'; // Gray
  }
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({
  dependencyGraph,
  height = 600,
}) => {
  // Calculate positions for nodes
  const positions = useMemo(
    () => calculateNodePositions(dependencyGraph.nodes, dependencyGraph.edges),
    [dependencyGraph.nodes, dependencyGraph.edges]
  );

  // Transform backend nodes to React Flow nodes
  const initialNodes: Node[] = useMemo(
    () =>
      dependencyGraph.nodes.map(node => {
        const position = positions.get(node.id) || { x: 0, y: 0 };
        return {
          id: node.id,
          type: 'default',
          data: {
            label: (
              <div className="text-center">
                <div className="font-semibold text-sm">{node.name}</div>
                {node.business_criticality && (
                  <div className="text-xs text-gray-500 mt-1">
                    {node.business_criticality}
                  </div>
                )}
                {node.hostname && (
                  <div className="text-xs text-gray-500 mt-1">{node.hostname}</div>
                )}
              </div>
            ),
          },
          position,
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          style: {
            background: getNodeColor(node.type),
            color: 'white',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '10px',
            minWidth: '150px',
          },
        };
      }),
    [dependencyGraph.nodes, positions]
  );

  // Transform backend edges to React Flow edges
  const initialEdges: Edge[] = useMemo(
    () =>
      dependencyGraph.edges.map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: true,
        label: edge.type,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#94a3b8',
        },
      })),
    [dependencyGraph.edges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when dependency graph changes
  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center">
          <Network className="mr-2 h-5 w-5" />
          <CardTitle>Dependency Graph Visualization</CardTitle>
        </div>
        <CardDescription>
          Visual representation of application dependencies. Blue nodes are applications, green nodes
          are servers, orange nodes are databases. Arrows show dependency relationships.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div style={{ height: `${height}px`, width: '100%' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-left"
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const originalNode = dependencyGraph.nodes.find(n => n.id === node.id);
                return getNodeColor(originalNode?.type || 'default');
              }}
              maskColor="rgb(240, 240, 240, 0.6)"
            />
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
};
