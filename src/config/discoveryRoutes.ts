/**
 * Centralized discovery flow routing configuration
 * Maps backend phase names to frontend routes
 */

export const DISCOVERY_PHASE_ROUTES: Record<string, (flowId: string) => string> = {
  // Initialization phases go to monitoring view
  'initialization': (flowId: string) => `/discovery/monitor/${flowId}`,
  'data_import_validation': () => '/discovery/cmdb-import',
  'data_import': () => '/discovery/cmdb-import',

  // Field mapping phases
  'field_mapping': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
  'attribute_mapping': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,

  // Data cleansing phase
  'data_cleansing': (flowId: string) => `/discovery/data-cleansing/${flowId}`,

  // Asset inventory phases
  'asset_inventory': (flowId: string) => `/discovery/inventory/${flowId}`,
  'inventory': (flowId: string) => `/discovery/inventory/${flowId}`,

  // Dependency analysis phases
  'dependency_analysis': (flowId: string) => `/discovery/dependencies/${flowId}`,
  'dependencies': (flowId: string) => `/discovery/dependencies/${flowId}`,

  // Tech debt assessment phases
  'tech_debt_assessment': (flowId: string) => `/discovery/tech-debt/${flowId}`,
  'tech_debt_analysis': (flowId: string) => `/discovery/tech-debt/${flowId}`,
  'tech_debt': (flowId: string) => `/discovery/tech-debt/${flowId}`,
  'technical_debt': (flowId: string) => `/discovery/tech-debt/${flowId}`,

  // Completed flow - route to inventory
  'completed': (flowId: string) => `/discovery/inventory/${flowId}`,

  // Status-based routing
  'waiting_for_user_approval': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
  'paused': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
  'pending_approval': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,

  // Error states - route to monitoring for error details
  'failed': (flowId: string) => `/discovery/monitor/${flowId}`,
  'error': (flowId: string) => `/discovery/monitor/${flowId}`,
  'not_found': (flowId: string) => `/discovery/monitor/${flowId}`,

  // Unknown/undefined states - route to monitoring
  'unknown': (flowId: string) => `/discovery/monitor/${flowId}`,
  'undefined': (flowId: string) => `/discovery/monitor/${flowId}`,
  'current': (flowId: string) => `/discovery/monitor/${flowId}`,
};

/**
 * Get the appropriate route for a discovery flow phase
 * @param phase - The current phase of the flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getDiscoveryPhaseRoute(phase: string, flowId: string): string {
  const routeFunction = DISCOVERY_PHASE_ROUTES[phase];
  if (routeFunction) {
    return routeFunction(flowId);
  }

  // Default to cmdb-import for unknown phases
  console.warn(`Unknown discovery phase: ${phase}, defaulting to cmdb-import`);
  return '/discovery/cmdb-import';
}

/**
 * Determine if a phase requires flowId in the URL
 * @param phase - The phase to check
 * @returns true if the phase requires flowId in URL
 */
export function phaseRequiresFlowId(phase: string): boolean {
  const noFlowIdPhases = [
    'data_import_validation',
    'data_import'
  ];

  return !noFlowIdPhases.includes(phase);
}
