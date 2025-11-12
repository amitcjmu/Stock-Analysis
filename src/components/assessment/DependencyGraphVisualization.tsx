/**
 * DependencyGraphVisualization Component
 *
 * D3.js force-directed graph visualization for dependency analysis.
 * Displays application and infrastructure dependencies with interactive nodes.
 *
 * Features:
 * - Force-directed graph layout using D3.js
 * - UUID to name resolution for readable node labels
 * - Color-coded nodes by type (application vs infrastructure)
 * - Draggable nodes with force simulation
 * - Interactive legend explaining node types
 * - Responsive design with Tailwind CSS
 * - Handles empty graph state gracefully
 *
 * @module DependencyGraphVisualization
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Network, Circle, Square } from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

interface GraphNode {
  id: string;
  name: string;
  type: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

interface GraphMetadata {
  dependency_count: number;
  node_count: number;
}

interface DependencyGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: GraphMetadata;
}

interface Application {
  id: string;
  canonical_name: string;
}

interface Infrastructure {
  id: string;
  name: string;
}

export interface DependencyGraphVisualizationProps {
  dependency_graph: DependencyGraph;
  applications: Application[];
  infrastructure: Infrastructure[];
}

// ============================================================================
// D3 Graph Node (extends GraphNode for simulation)
// ============================================================================

interface D3GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface D3GraphLink extends d3.SimulationLinkDatum<D3GraphNode> {
  source: string | D3GraphNode;
  target: string | D3GraphNode;
  type: string;
}

// ============================================================================
// Component
// ============================================================================

export const DependencyGraphVisualization: React.FC<DependencyGraphVisualizationProps> = ({
  dependency_graph,
  applications,
  infrastructure
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // ============================================================================
  // Build Name Lookup Map (UUID → Name)
  // ============================================================================

  const buildNameMap = (): Map<string, string> => {
    const nameMap = new Map<string, string>();

    // Add applications to lookup map
    applications?.forEach(app => {
      nameMap.set(app.id, app.canonical_name);
    });

    // Add infrastructure to lookup map
    infrastructure?.forEach(srv => {
      nameMap.set(srv.id, srv.name);
    });

    return nameMap;
  };

  // ============================================================================
  // D3 Force Graph Rendering
  // ============================================================================

  useEffect(() => {
    if (!svgRef.current || !dependency_graph) return;

    // Build UUID → name lookup
    const nameMap = buildNameMap();

    // Prepare nodes with names resolved from UUIDs
    const nodes: D3GraphNode[] = dependency_graph.nodes.map(node => ({
      id: node.id,
      name: nameMap.get(node.id) || node.name || node.id,
      type: node.type
    }));

    // Prepare edges
    const links: D3GraphLink[] = dependency_graph.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      type: edge.type
    }));

    // Handle empty graph state
    if (nodes.length === 0) {
      return;
    }

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Set up SVG dimensions
    const width = dimensions.width;
    const height = dimensions.height;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('class', 'bg-gray-50 rounded-lg');

    // Create container group for zoom/pan
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // ============================================================================
    // D3 Force Simulation
    // ============================================================================

    const simulation = d3.forceSimulation<D3GraphNode>(nodes)
      .force('link', d3.forceLink<D3GraphNode, D3GraphLink>(links)
        .id(d => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    // ============================================================================
    // Arrow Markers for Edges
    // ============================================================================

    svg.append('defs').selectAll('marker')
      .data(['application', 'server'])
      .enter().append('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 35)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#6b7280');

    // ============================================================================
    // Render Links (Edges)
    // ============================================================================

    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#6b7280')
      .attr('stroke-width', d => {
        // Vary thickness by edge type (example logic)
        return d.type === 'hosting' ? 2 : 1.5;
      })
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrow-application)');

    // ============================================================================
    // Render Nodes
    // ============================================================================

    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag<SVGGElement, D3GraphNode>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // Node shapes (circles for applications, rects for servers)
    node.each(function(d) {
      const nodeGroup = d3.select(this);

      if (d.type === 'application') {
        // Blue circle for applications
        nodeGroup.append('circle')
          .attr('r', 25)
          .attr('fill', '#3b82f6')
          .attr('stroke', '#1e40af')
          .attr('stroke-width', 2);
      } else {
        // Green square for servers/infrastructure
        nodeGroup.append('rect')
          .attr('x', -25)
          .attr('y', -25)
          .attr('width', 50)
          .attr('height', 50)
          .attr('rx', 5)
          .attr('fill', '#10b981')
          .attr('stroke', '#047857')
          .attr('stroke-width', 2);
      }
    });

    // Node labels
    node.append('text')
      .text(d => {
        // Truncate long names for readability
        const name = d.name;
        return name.length > 20 ? name.substring(0, 17) + '...' : name;
      })
      .attr('text-anchor', 'middle')
      .attr('dy', 40)
      .attr('font-size', '12px')
      .attr('fill', '#374151')
      .attr('font-weight', 500);

    // Tooltips on hover
    node.append('title')
      .text(d => `${d.name}\nType: ${d.type}\nID: ${d.id}`);

    // ============================================================================
    // Simulation Tick Function
    // ============================================================================

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as D3GraphNode).x ?? 0)
        .attr('y1', d => (d.source as D3GraphNode).y ?? 0)
        .attr('x2', d => (d.target as D3GraphNode).x ?? 0)
        .attr('y2', d => (d.target as D3GraphNode).y ?? 0);

      node
        .attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // ============================================================================
    // Drag Handlers
    // ============================================================================

    function dragStarted(event: d3.D3DragEvent<SVGGElement, D3GraphNode, D3GraphNode>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, D3GraphNode, D3GraphNode>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragEnded(event: d3.D3DragEvent<SVGGElement, D3GraphNode, D3GraphNode>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // ============================================================================
    // Cleanup
    // ============================================================================

    return () => {
      simulation.stop();
    };
  }, [dependency_graph, applications, infrastructure, dimensions]);

  // ============================================================================
  // Responsive Resize Handler
  // ============================================================================

  useEffect(() => {
    const handleResize = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: 600
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // ============================================================================
  // Render
  // ============================================================================

  // Handle empty graph state
  if (!dependency_graph || dependency_graph.nodes.length === 0) {
    return (
      <Card className="print:shadow-none print:border-2">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5" />
            <span>Dependency Graph Visualization</span>
          </CardTitle>
          <CardDescription>
            Interactive force-directed graph showing dependencies
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
            <Network className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium">No Dependencies Found</p>
            <p className="text-sm mt-2">Dependencies will appear here once discovered</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Network className="h-5 w-5" />
          <span>Dependency Graph Visualization</span>
        </CardTitle>
        <CardDescription>
          Interactive force-directed graph showing {dependency_graph.metadata.node_count} nodes
          and {dependency_graph.metadata.dependency_count} dependencies
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Legend */}
        <div className="flex items-center gap-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2">
            <Circle className="h-5 w-5 text-blue-600 fill-blue-600" />
            <span className="text-sm font-medium text-blue-900">Application</span>
          </div>
          <div className="flex items-center gap-2">
            <Square className="h-5 w-5 text-green-600 fill-green-600" />
            <span className="text-sm font-medium text-green-900">Server/Infrastructure</span>
          </div>
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {dependency_graph.metadata.node_count} Nodes
            </Badge>
            <Badge variant="outline">
              {dependency_graph.metadata.dependency_count} Dependencies
            </Badge>
          </div>
        </div>

        {/* Graph Container */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <svg
            ref={svgRef}
            className="w-full"
            style={{ minHeight: '600px' }}
          />
        </div>

        {/* Instructions */}
        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>Drag nodes</strong> to reposition them</p>
          <p><strong>Scroll</strong> to zoom in/out</p>
          <p><strong>Hover over nodes</strong> to see full details</p>
        </div>
      </CardContent>
    </Card>
  );
};
