/**
 * Centralized discovery flow routing configuration
 * Maps backend phase names to frontend routes
 */

export const DISCOVERY_PHASE_ROUTES: Record<string, (flowId: string) => string> = {
  // Initialization phases go to monitoring view
  'initialization': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'data_import_validation': () => '/discovery/cmdb-import',
  'data_import': () => '/discovery/cmdb-import',

  // Field mapping phases
  'field_mapping': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'attribute_mapping': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',

  // Data cleansing phase
  'data_cleansing': (flowId: string) => flowId ? `/discovery/data-cleansing/${flowId}` : '/discovery/cmdb-import',

  // Asset inventory phases
  'asset_inventory': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',
  'inventory': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',

  // Dependency analysis phases
  'dependency_analysis': (flowId: string) => flowId ? `/discovery/dependencies/${flowId}` : '/discovery/cmdb-import',
  'dependencies': (flowId: string) => flowId ? `/discovery/dependencies/${flowId}` : '/discovery/cmdb-import',

  // Tech debt assessment phases
  'tech_debt_assessment': (flowId: string) => flowId ? `/discovery/tech-debt/${flowId}` : '/discovery/cmdb-import',
  'tech_debt_analysis': (flowId: string) => flowId ? `/discovery/tech-debt/${flowId}` : '/discovery/cmdb-import',
  'tech_debt': (flowId: string) => flowId ? `/discovery/tech-debt/${flowId}` : '/discovery/cmdb-import',
  'technical_debt': (flowId: string) => flowId ? `/discovery/tech-debt/${flowId}` : '/discovery/cmdb-import',

  // Completed flow - route to inventory
  'completed': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',

  // Status-based routing
  'waiting_for_user_approval': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'paused': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'pending_approval': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',

  // Error states - route to monitoring for error details
  'failed': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'error': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'not_found': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',

  // Unknown/undefined states - route to monitoring
  'unknown': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'undefined': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'current': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
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
