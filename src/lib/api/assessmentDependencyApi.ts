/**
 * Assessment Flow Dependency Analysis API Client
 *
 * Provides access to dependency analysis endpoints for assessment flows.
 * Uses snake_case field naming per CLAUDE.md field naming convention (Aug 2025).
 *
 * Endpoints:
 * - GET /api/v1/assessment-flow/{flow_id}/dependency/analysis - Get dependency graph
 *
 * NOTE: Manual execution endpoint removed per design.
 * The dependency_analysis phase auto-executes via MFO when navigating from
 * the complexity page. See complexity.tsx handleSubmit() for resumeFlow() call.
 *
 * Part of Assessment Flow MFO Integration (ADR-006, ADR-027)
 */

import { apiClient } from '@/lib/api/apiClient';

// =============================================================================
// Type Definitions (CRITICAL: All fields use snake_case)
// =============================================================================

/**
 * Dependency graph node representing an application or server.
 */
export interface DependencyNode {
  /** Node unique identifier */
  id: string;
  /** Node display name */
  name: string;
  /** Node type: application or server */
  type: 'application' | 'server';
  /** Business criticality level (for applications) */
  business_criticality?: string;
  /** Server hostname (for servers) */
  hostname?: string;
}

/**
 * Dependency graph edge representing a relationship between nodes.
 */
export interface DependencyEdge {
  /** Source node ID */
  source: string;
  /** Target node ID */
  target: string;
  /** Dependency type (e.g., 'hosts', 'api_call', 'database') */
  type: string;
  /** AI confidence score (0.0 to 1.0) */
  confidence_score?: number;
  /** Source node name (for display) */
  source_name?: string;
  /** Target node name (for display) */
  target_name?: string;
}

/**
 * Dependency graph structure with nodes and edges.
 */
export interface DependencyGraph {
  /** Array of nodes (applications and servers) */
  nodes: DependencyNode[];
  /** Array of edges (relationships) */
  edges: DependencyEdge[];
  /** Graph metadata and statistics */
  metadata: {
    /** Total number of dependencies */
    dependency_count: number;
    /** Total number of nodes */
    node_count: number;
    /** Number of application nodes */
    app_count: number;
    /** Number of server nodes */
    server_count: number;
  };
}

/**
 * Application metadata for dependency analysis.
 */
export interface ApplicationMetadata {
  /** Application unique identifier */
  id: string;
  /** Application name */
  name: string;
  /** Application display name */
  application_name?: string;
  /** Asset type */
  asset_type?: string;
  /** Business criticality level */
  business_criticality?: string;
}

/**
 * Agent analysis results from dependency phase execution.
 */
export interface AgentResults {
  /** Execution status */
  status: 'running' | 'completed' | 'failed';
  /** Phase name */
  phase: string;
  /** Analysis insights and recommendations */
  insights?: string[];
  /** Agent execution timestamp */
  executed_at?: string;
  /** Error message if failed */
  error?: string;
}

/**
 * Response from GET /dependency/analysis endpoint.
 *
 * CRITICAL: All field names use snake_case to match backend.
 * DO NOT transform field names - use exactly as received.
 */
export interface DependencyAnalysisResponse {
  /** Child flow ID (user-facing identifier) */
  flow_id: string;
  /** Application-to-server dependencies (raw data) */
  app_server_dependencies: any[];
  /** Application-to-application dependencies (raw data) */
  app_app_dependencies: any[];
  /** Metadata for all selected applications */
  applications: ApplicationMetadata[];
  /** Structured dependency graph for visualization */
  dependency_graph: DependencyGraph;
  /** Agent analysis results (if phase executed) */
  agent_results?: AgentResults;
  /** Analysis metadata */
  metadata?: {
    /** Total number of applications analyzed */
    total_applications: number;
    /** Total number of dependencies found */
    total_dependencies: number;
    /** Whether agent analysis has been executed */
    analysis_executed: boolean;
  };
  /** Status message */
  message?: string;
}

/**
 * Response from POST /dependency/execute endpoint.
 *
 * Returned when manually executing the dependency_analysis phase.
 */
export interface DependencyExecuteResponse {
  /** Child flow ID */
  flow_id: string;
  /** Phase name that was executed */
  phase: string;
  /** Execution status */
  status: 'started' | 'running' | 'completed' | 'failed';
  /** User-facing status message */
  message: string;
  /** MFO phase execution result (optional) */
  result?: any;
}

// =============================================================================
// API Client Class
// =============================================================================

/**
 * API client for Assessment Flow dependency analysis endpoints.
 *
 * All methods use:
 * - HTTP polling (NOT WebSockets) per coding-agent-guide.md
 * - snake_case field naming (NO transformation needed)
 * - Request bodies for POST (NOT query parameters)
 *
 * @example
 * ```typescript
 * import { assessmentDependencyApi } from '@/lib/api/assessmentDependencyApi';
 *
 * // Get dependency analysis (auto-executed via MFO)
 * const analysis = await assessmentDependencyApi.getDependencyAnalysis('flow-uuid');
 * console.log(`Dependencies: ${analysis.dependency_graph.metadata.dependency_count}`);
 * ```
 */
export class AssessmentDependencyApiClient {
  /**
   * Get dependency analysis graph and data for assessment flow.
   *
   * Returns:
   * - Application-to-server dependencies (hosting relationships)
   * - Application-to-application dependencies (communication patterns)
   * - Structured dependency graph for visualization
   * - Agent analysis results (if phase has been executed)
   *
   * @param flowId - Assessment flow identifier (child flow ID)
   * @returns Dependency analysis response with graph data
   *
   * @example
   * const analysis = await assessmentDependencyApi.getDependencyAnalysis('flow-uuid');
   * const graph = analysis.dependency_graph;
   * console.log(`Found ${graph.metadata.dependency_count} dependencies`);
   */
  async getDependencyAnalysis(flowId: string): Promise<DependencyAnalysisResponse> {
    try {
      console.log('[AssessmentDependencyApi] Getting dependency analysis:', flowId);

      const response = await apiClient.get<DependencyAnalysisResponse>(
        `/assessment-flow/${flowId}/dependency/analysis`
      );

      console.log('[AssessmentDependencyApi] Retrieved dependency analysis:', {
        flow_id: response.flow_id,
        app_count: response.applications?.length || 0,
        dependency_count: response.dependency_graph?.metadata?.dependency_count || 0,
        analysis_executed: response.metadata?.analysis_executed || false,
      });

      return response;
    } catch (error) {
      console.error('[AssessmentDependencyApi] Failed to get dependency analysis:', error);
      throw error;
    }
  }

  /**
   * Manually execute dependency analysis phase for assessment flow.
   *
   * This allows manual re-execution of the dependency_analysis phase:
   * - When the phase hasn't been run yet
   * - When the phase failed and needs to be retried
   * - When the user wants to refresh the analysis with updated data
   *
   * **NOTE**: Dependency analysis can also auto-execute via MFO when the user
   * clicks "Continue" from the complexity page. This method provides manual control.
   *
   * @param flowId - Assessment flow identifier (child flow ID)
   * @returns Execution response with status and results
   *
   * @example
   * await assessmentDependencyApi.executeDependencyAnalysis('flow-uuid');
   * // Poll getDependencyAnalysis() to check status and get results
   */
  async executeDependencyAnalysis(flowId: string): Promise<DependencyExecuteResponse> {
    try {
      console.log('[AssessmentDependencyApi] Executing dependency analysis:', flowId);

      const response = await apiClient.post<DependencyExecuteResponse>(
        `/assessment-flow/${flowId}/dependency/execute`,
        {} // Empty body - all params in URL
      );

      console.log('[AssessmentDependencyApi] Dependency analysis execution started:', {
        flow_id: response.flow_id,
        phase: response.phase,
        status: response.status,
      });

      return response;
    } catch (error) {
      console.error('[AssessmentDependencyApi] Failed to execute dependency analysis:', error);
      throw error;
    }
  }
}

// =============================================================================
// Export Singleton Instance
// =============================================================================

/**
 * Singleton instance of Assessment Dependency API client.
 *
 * Usage:
 * ```typescript
 * import { assessmentDependencyApi } from '@/lib/api/assessmentDependencyApi';
 *
 * // Get dependency analysis (auto-executed via MFO)
 * const analysis = await assessmentDependencyApi.getDependencyAnalysis('flow-uuid');
 * ```
 */
export const assessmentDependencyApi = new AssessmentDependencyApiClient();
