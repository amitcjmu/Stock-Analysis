/**
 * DependencyGraphVisualization Example Usage
 *
 * This file demonstrates how to use the DependencyGraphVisualization component
 * with sample data structures matching the assessment flow architecture.
 */

import React from 'react';
import { DependencyGraphVisualization } from '../DependencyGraphVisualization';

export const DependencyGraphVisualizationExample: React.FC = () => {
  // ============================================================================
  // Sample Data
  // ============================================================================

  // Sample applications (matches Application interface)
  const sampleApplications = [
    {
      id: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d',
      canonical_name: 'Customer Portal'
    },
    {
      id: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e',
      canonical_name: 'Payment Gateway'
    },
    {
      id: 'c3d4e5f6-a7b8-6c7d-0e9f-1a2b3c4d5e6f',
      canonical_name: 'Analytics Engine'
    }
  ];

  // Sample infrastructure (matches Infrastructure interface)
  const sampleInfrastructure = [
    {
      id: 'd4e5f6a7-b8c9-7d8e-1f0a-2b3c4d5e6f7a',
      name: 'web-server-01'
    },
    {
      id: 'e5f6a7b8-c9d0-8e9f-2a1b-3c4d5e6f7a8b',
      name: 'db-server-01'
    },
    {
      id: 'f6a7b8c9-d0e1-9f0a-3b2c-4d5e6f7a8b9c',
      name: 'cache-server-01'
    }
  ];

  // Sample dependency graph (matches DependencyGraph interface)
  const sampleDependencyGraph = {
    nodes: [
      // Application nodes
      {
        id: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d',
        name: 'Customer Portal', // Will be replaced by canonical_name from applications array
        type: 'application'
      },
      {
        id: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e',
        name: 'Payment Gateway',
        type: 'application'
      },
      {
        id: 'c3d4e5f6-a7b8-6c7d-0e9f-1a2b3c4d5e6f',
        name: 'Analytics Engine',
        type: 'application'
      },
      // Infrastructure nodes
      {
        id: 'd4e5f6a7-b8c9-7d8e-1f0a-2b3c4d5e6f7a',
        name: 'web-server-01', // Will be replaced by name from infrastructure array
        type: 'server'
      },
      {
        id: 'e5f6a7b8-c9d0-8e9f-2a1b-3c4d5e6f7a8b',
        name: 'db-server-01',
        type: 'server'
      },
      {
        id: 'f6a7b8c9-d0e1-9f0a-3b2c-4d5e6f7a8b9c',
        name: 'cache-server-01',
        type: 'server'
      }
    ],
    edges: [
      // Customer Portal dependencies
      {
        source: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d', // Customer Portal
        target: 'd4e5f6a7-b8c9-7d8e-1f0a-2b3c4d5e6f7a', // web-server-01
        type: 'hosting'
      },
      {
        source: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d', // Customer Portal
        target: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e', // Payment Gateway
        type: 'communication'
      },
      // Payment Gateway dependencies
      {
        source: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e', // Payment Gateway
        target: 'e5f6a7b8-c9d0-8e9f-2a1b-3c4d5e6f7a8b', // db-server-01
        type: 'data_flow'
      },
      {
        source: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e', // Payment Gateway
        target: 'f6a7b8c9-d0e1-9f0a-3b2c-4d5e6f7a8b9c', // cache-server-01
        type: 'communication'
      },
      // Analytics Engine dependencies
      {
        source: 'c3d4e5f6-a7b8-6c7d-0e9f-1a2b3c4d5e6f', // Analytics Engine
        target: 'e5f6a7b8-c9d0-8e9f-2a1b-3c4d5e6f7a8b', // db-server-01
        type: 'data_flow'
      },
      {
        source: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d', // Customer Portal
        target: 'c3d4e5f6-a7b8-6c7d-0e9f-1a2b3c4d5e6f', // Analytics Engine
        type: 'communication'
      }
    ],
    metadata: {
      dependency_count: 6,
      node_count: 6
    }
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Dependency Graph Visualization Example</h1>
        <p className="text-gray-600">
          This example demonstrates the D3.js force-directed graph component
          with sample application and infrastructure dependencies.
        </p>
      </div>

      {/* Example 1: Full Graph */}
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Example 1: Complete Dependency Graph</h2>
        <DependencyGraphVisualization
          dependency_graph={sampleDependencyGraph}
          applications={sampleApplications}
          infrastructure={sampleInfrastructure}
        />
      </div>

      {/* Example 2: Empty Graph */}
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Example 2: Empty Graph State</h2>
        <DependencyGraphVisualization
          dependency_graph={{
            nodes: [],
            edges: [],
            metadata: { dependency_count: 0, node_count: 0 }
          }}
          applications={[]}
          infrastructure={[]}
        />
      </div>

      {/* Example 3: Applications Only */}
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Example 3: Application Dependencies Only</h2>
        <DependencyGraphVisualization
          dependency_graph={{
            nodes: [
              {
                id: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d',
                name: 'Customer Portal',
                type: 'application'
              },
              {
                id: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e',
                name: 'Payment Gateway',
                type: 'application'
              }
            ],
            edges: [
              {
                source: 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d',
                target: 'b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e',
                type: 'communication'
              }
            ],
            metadata: { dependency_count: 1, node_count: 2 }
          }}
          applications={sampleApplications}
          infrastructure={[]}
        />
      </div>

      {/* Usage Instructions */}
      <div className="border border-blue-200 bg-blue-50 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-blue-900">Usage Instructions</h3>

        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>Component Props:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><code>dependency_graph</code>: Graph data with nodes, edges, and metadata</li>
            <li><code>applications</code>: Array of applications with id and canonical_name</li>
            <li><code>infrastructure</code>: Array of infrastructure with id and name</li>
          </ul>
        </div>

        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>UUID to Name Mapping:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Component builds a lookup map from applications and infrastructure arrays</li>
            <li>Node UUIDs are automatically resolved to human-readable names</li>
            <li>Falls back to node.name or node.id if UUID not found in lookup</li>
          </ul>
        </div>

        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>Interactive Features:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Drag nodes to reposition them in the graph</li>
            <li>Scroll to zoom in/out</li>
            <li>Hover over nodes to see full details (name, type, UUID)</li>
            <li>Force simulation automatically arranges nodes</li>
          </ul>
        </div>

        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>Visual Legend:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Blue circles = Applications</li>
            <li>Green squares = Servers/Infrastructure</li>
            <li>Gray arrows = Dependencies (thickness varies by type)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DependencyGraphVisualizationExample;
