import React from 'react'
import { useCallback, useMemo } from 'react'
import ReactFlow from 'reactflow'
import type { Edge} from 'reactflow';
import { Node, MarkerType } from 'reactflow'
import { Controls, Background, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css';
import { Card } from '../../ui/card';
import type { DependencyData } from '../../../types/dependency';

// Dependency update interface
interface DependencyUpdate {
  id: string;
  sourceId: string;
  targetId: string;
  type: 'hosting' | 'communication' | 'data_flow';
  strength: 'weak' | 'medium' | 'strong';
  verified: boolean;
  metadata?: Record<string, unknown>;
}

interface DependencyGraphProps {
  data: DependencyData | null;
  activeView: 'app-server' | 'app-app';
  onUpdateDependency: (dependency: DependencyUpdate) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({
  data,
  activeView,
  onUpdateDependency
}) => {
  const createNodes = useCallback(() => {
    if (!data) return [];

    if (activeView === 'app-server') {
      const { hosting_relationships = [] } = data?.app_server_mapping || {};

      // Ensure we only show servers that actually have dependencies
      if (hosting_relationships.length === 0) {
        return []; // No dependencies means no graph to show
      }

      // CRITICAL FIX: Only extract apps and servers that are ACTUALLY in dependencies
      // Extract unique applications from actual relationships only
      const applications = Array.from(new Set(
        hosting_relationships.map(r => r?.application_name).filter(Boolean)
      ));

      // CRITICAL FIX: Extract server names from actual relationships only
      const servers = Array.from(new Set(
        hosting_relationships.map(r => {
          // Handle both direct server_name and nested server_info structure
          const serverName = r?.server_name || r?.server_info?.name || r?.server_info?.hostname;
          return serverName;
        }).filter(Boolean)
      ));

      // Double-check: ensure we have valid data
      if (applications.length === 0 || servers.length === 0) {
        console.warn('⚠️ DependencyGraph: No valid applications or servers found in relationships');
        return [];
      }

      // CRITICAL FIX: Position nodes based on actual relationships, not sequential order
      const appNodes = applications.map((app, index) => ({
        id: `app-${app}`,
        type: 'default',
        data: { label: app },
        position: { x: 100, y: 50 + index * 120 },
        style: {
          background: '#f0f9ff',
          border: '1px solid #93c5fd',
          borderRadius: '8px',
          padding: '10px'
        }
      }));

      // CRITICAL FIX: Position servers based on their relationships to apps
      const serverNodes = servers.map((server, index) => {
        // Find which apps connect to this server to determine positioning
        const connectedApps = hosting_relationships.filter(r => {
          const serverName = r?.server_name || r?.server_info?.name || r?.server_info?.hostname;
          return serverName === server;
        });

        // Use the average position of connected apps for better layout
        const avgAppIndex = connectedApps.length > 0
          ? connectedApps.reduce((sum, rel) => {
              const appIndex = applications.indexOf(rel?.application_name);
              return sum + (appIndex >= 0 ? appIndex : 0);
            }, 0) / connectedApps.length
          : index;

        return {
          id: `server-${server}`,
          type: 'default',
          data: { label: server },
          position: { x: 500, y: 50 + avgAppIndex * 120 },
          style: {
            background: '#f0fdf4',
            border: '1px solid #86efac',
            borderRadius: '8px',
            padding: '10px'
          }
        };
      });

      return [...appNodes, ...serverNodes];
    } else {
      const { cross_app_dependencies = [] } = data?.cross_application_mapping || {};
      const applications = Array.from(new Set([
        ...cross_app_dependencies.map(d => d?.source_app).filter(Boolean),
        ...cross_app_dependencies.map(d => d?.target_app).filter(Boolean)
      ]));

      return applications.map((app, index) => ({
        id: `app-${app}`,
        type: 'default',
        data: { label: app },
        position: { x: (index % 3) * 300, y: Math.floor(index / 3) * 150 },
        style: {
          background: '#f0f9ff',
          border: '1px solid #93c5fd',
          borderRadius: '8px',
          padding: '10px'
        }
      }));
    }
  }, [data, activeView]);

  const createEdges = useCallback(() => {
    if (!data) return [];

    if (activeView === 'app-server') {
      const { hosting_relationships = [] } = data?.app_server_mapping || {};
      return hosting_relationships.map((rel, index) => {
        // CRITICAL FIX: Extract server name from server_info object structure
        const serverName = rel?.server_name || rel?.server_info?.name || rel?.server_info?.hostname;
        return {
          id: `edge-${index}`,
          source: `app-${rel?.application_name}`,
          target: `server-${serverName}`,
          type: 'smoothstep',
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20
          },
          style: {
            stroke: (rel?.status === 'confirmed' || !rel?.status) ? '#22c55e' : '#94a3b8',
            strokeWidth: 2
          },
          data: {
            confidence: rel?.confidence,
            status: rel?.status
          }
        };
      });
    } else {
      const { cross_app_dependencies = [] } = data?.cross_application_mapping || {};
      return cross_app_dependencies.map((dep, index) => ({
        id: `edge-${index}`,
        source: `app-${dep?.source_app}`,
        target: `app-${dep?.target_app}`,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20
        },
        style: {
          stroke: (dep?.status === 'confirmed' || !dep?.status) ? '#22c55e' : '#94a3b8',
          strokeWidth: 2
        },
        data: {
          dependency_type: dep?.dependency_type,
          confidence: dep?.confidence,
          status: dep?.status
        }
      }));
    }
  }, [data, activeView]);

  const [nodes, setNodes, onNodesChange] = useNodesState(createNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(createEdges());

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    const dependency = activeView === 'app-server'
      ? data?.app_server_mapping?.hosting_relationships?.find(
          r => {
            const serverName = r?.server_name || r?.server_info?.name || r?.server_info?.hostname;
            return r?.application_name === edge.source.replace('app-', '') &&
                   serverName === edge.target.replace('server-', '');
          }
        )
      : data?.cross_application_mapping?.cross_app_dependencies?.find(
          d => d?.source_app === edge.source.replace('app-', '') &&
              d?.target_app === edge.target.replace('app-', '')
        );

    if (dependency) {
      onUpdateDependency(dependency);
    }
  }, [data, activeView, onUpdateDependency]);

  // Update nodes and edges when data changes
  React.useEffect(() => {
    setNodes(createNodes());
    setEdges(createEdges());
  }, [data, activeView, createNodes, createEdges, setNodes, setEdges]);

  return (
    <Card className="h-[600px]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgeClick={onEdgeClick}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
    </Card>
  );
};
