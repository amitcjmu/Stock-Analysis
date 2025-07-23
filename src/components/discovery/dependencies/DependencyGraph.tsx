import React from 'react'
import { useCallback, useMemo } from 'react'
import ReactFlow from 'reactflow'
import { Node, Edge, MarkerType } from 'reactflow'
import { Controls, Background, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css';
import { Card } from '../../ui/card';
import { DependencyData } from '../../../types/dependency';

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
      const applications = Array.from(new Set(
        hosting_relationships.map(r => r?.application_name).filter(Boolean)
      ));
      const servers = Array.from(new Set(
        hosting_relationships.map(r => r?.server_name).filter(Boolean)
      ));

      const appNodes = applications.map((app, index) => ({
        id: `app-${app}`,
        type: 'default',
        data: { label: app },
        position: { x: 100, y: index * 100 },
        style: {
          background: '#f0f9ff',
          border: '1px solid #93c5fd',
          borderRadius: '8px',
          padding: '10px'
        }
      }));

      const serverNodes = servers.map((server, index) => ({
        id: `server-${server}`,
        type: 'default',
        data: { label: server },
        position: { x: 400, y: index * 100 },
        style: {
          background: '#f0fdf4',
          border: '1px solid #86efac',
          borderRadius: '8px',
          padding: '10px'
        }
      }));

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
      return hosting_relationships.map((rel, index) => ({
        id: `edge-${index}`,
        source: `app-${rel?.application_name}`,
        target: `server-${rel?.server_name}`,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20
        },
        style: {
          stroke: rel?.status === 'confirmed' ? '#22c55e' : '#94a3b8',
          strokeWidth: 2
        },
        data: {
          confidence: rel?.confidence,
          status: rel?.status
        }
      }));
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
          stroke: dep?.status === 'confirmed' ? '#22c55e' : '#94a3b8',
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
          r => r?.application_name === edge.source.replace('app-', '') &&
              r?.server_name === edge.target.replace('server-', '')
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