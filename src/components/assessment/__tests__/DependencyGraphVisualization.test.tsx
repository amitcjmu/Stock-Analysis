/**
 * DependencyGraphVisualization Component Tests
 *
 * Test suite for the D3.js force-directed graph component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DependencyGraphVisualization } from '../DependencyGraphVisualization';

// Mock D3.js to avoid DOM manipulation in tests
vi.mock('d3', () => ({
  select: vi.fn().mockReturnValue({
    selectAll: vi.fn().mockReturnValue({
      remove: vi.fn()
    }),
    attr: vi.fn().mockReturnThis(),
    call: vi.fn().mockReturnThis(),
    append: vi.fn().mockReturnThis()
  }),
  forceSimulation: vi.fn().mockReturnValue({
    force: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    stop: vi.fn()
  }),
  forceLink: vi.fn().mockReturnValue({
    id: vi.fn().mockReturnThis(),
    distance: vi.fn().mockReturnThis()
  }),
  forceManyBody: vi.fn().mockReturnValue({
    strength: vi.fn().mockReturnThis()
  }),
  forceCenter: vi.fn(),
  forceCollide: vi.fn().mockReturnValue({
    radius: vi.fn().mockReturnThis()
  }),
  zoom: vi.fn().mockReturnValue({
    scaleExtent: vi.fn().mockReturnValue({
      on: vi.fn().mockReturnThis()
    })
  }),
  drag: vi.fn().mockReturnValue({
    on: vi.fn().mockReturnThis()
  })
}));

describe('DependencyGraphVisualization', () => {
  const mockApplications = [
    { id: 'app-1', canonical_name: 'Customer Portal' },
    { id: 'app-2', canonical_name: 'Payment Gateway' }
  ];

  const mockInfrastructure = [
    { id: 'srv-1', name: 'web-server-01' },
    { id: 'srv-2', name: 'db-server-01' }
  ];

  const mockDependencyGraph = {
    nodes: [
      { id: 'app-1', name: 'App 1', type: 'application' },
      { id: 'app-2', name: 'App 2', type: 'application' },
      { id: 'srv-1', name: 'Server 1', type: 'server' },
      { id: 'srv-2', name: 'Server 2', type: 'server' }
    ],
    edges: [
      { source: 'app-1', target: 'srv-1', type: 'hosting' },
      { source: 'app-2', target: 'srv-2', type: 'hosting' },
      { source: 'app-1', target: 'app-2', type: 'communication' }
    ],
    metadata: {
      dependency_count: 3,
      node_count: 4
    }
  };

  it('renders the component with graph data', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    expect(screen.getByText('Dependency Graph Visualization')).toBeInTheDocument();
  });

  it('displays metadata information', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    expect(screen.getByText('4 Nodes')).toBeInTheDocument();
    expect(screen.getByText('3 Dependencies')).toBeInTheDocument();
  });

  it('shows legend with node types', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    expect(screen.getByText('Application')).toBeInTheDocument();
    expect(screen.getByText('Server/Infrastructure')).toBeInTheDocument();
  });

  it('renders empty state when no nodes exist', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={{
          nodes: [],
          edges: [],
          metadata: { dependency_count: 0, node_count: 0 }
        }}
        applications={[]}
        infrastructure={[]}
      />
    );

    expect(screen.getByText('No Dependencies Found')).toBeInTheDocument();
    expect(screen.getByText('Dependencies will appear here once discovered')).toBeInTheDocument();
  });

  it('renders empty state when dependency_graph is null', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={null as any}
        applications={[]}
        infrastructure={[]}
      />
    );

    expect(screen.getByText('No Dependencies Found')).toBeInTheDocument();
  });

  it('displays interaction instructions', () => {
    render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    expect(screen.getByText(/Drag nodes/i)).toBeInTheDocument();
    expect(screen.getByText(/Scroll/i)).toBeInTheDocument();
    expect(screen.getByText(/Hover over nodes/i)).toBeInTheDocument();
  });

  it('handles missing applications array gracefully', () => {
    const { container } = render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={undefined as any}
        infrastructure={mockInfrastructure}
      />
    );

    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('handles missing infrastructure array gracefully', () => {
    const { container } = render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={undefined as any}
      />
    );

    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders SVG element for graph', () => {
    const { container } = render(
      <DependencyGraphVisualization
        dependency_graph={mockDependencyGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('uses correct metadata values', () => {
    const customGraph = {
      ...mockDependencyGraph,
      metadata: {
        dependency_count: 10,
        node_count: 8
      }
    };

    render(
      <DependencyGraphVisualization
        dependency_graph={customGraph}
        applications={mockApplications}
        infrastructure={mockInfrastructure}
      />
    );

    expect(screen.getByText('8 Nodes')).toBeInTheDocument();
    expect(screen.getByText('10 Dependencies')).toBeInTheDocument();
  });
});
