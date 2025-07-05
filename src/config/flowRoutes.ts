/**
 * Centralized flow routing configuration for all flow types
 * Mirrors the backend RouteDecisionTool mapping for consistency
 * Supports discovery, assessment, planning, execution, and future flows
 */

export type FlowType = 'discovery' | 'assessment' | 'plan' | 'execute' | 'modernize' | 'finops' | 'observability' | 'decommission';

/**
 * Route mapping for all flow types - matches backend RouteDecisionTool.ROUTE_MAPPING
 * Each flow type has its phases mapped to frontend routes
 */
export const FLOW_PHASE_ROUTES: Record<FlowType, Record<string, (flowId: string) => string>> = {
  discovery: {
    // Initialization phases go to cmdb-import (no flowId in URL)
    'initialization': () => '/discovery/cmdb-import',
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
    
    // Completed flow
    'completed': (flowId: string) => `/discovery/tech-debt/${flowId}`,
    
    // Status-based routing
    'waiting_for_user_approval': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
    'paused': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
    'pending_approval': (flowId: string) => `/discovery/attribute-mapping/${flowId}`,
    
    // Error states - go back to import
    'failed': () => '/discovery/cmdb-import',
    'error': () => '/discovery/cmdb-import',
    'not_found': () => '/discovery/cmdb-import',
    
    // Unknown/undefined states - default to cmdb-import
    'unknown': () => '/discovery/cmdb-import',
    'undefined': () => '/discovery/cmdb-import',
    'current': () => '/discovery/cmdb-import',
  },
  
  assessment: {
    'migration_readiness': (flowId: string) => `/assess/migration-readiness/${flowId}`,
    'business_impact': (flowId: string) => `/assess/business-impact/${flowId}`,
    'technical_assessment': (flowId: string) => `/assess/technical-assessment/${flowId}`,
    'completed': (flowId: string) => `/assess/summary/${flowId}`,
    
    // Error states
    'failed': () => '/assess',
    'error': () => '/assess',
    'unknown': () => '/assess',
  },
  
  plan: {
    'wave_planning': (flowId: string) => `/plan/wave-planning/${flowId}`,
    'runbook_creation': (flowId: string) => `/plan/runbook-creation/${flowId}`,
    'resource_allocation': (flowId: string) => `/plan/resource-allocation/${flowId}`,
    'completed': (flowId: string) => `/plan/summary/${flowId}`,
    
    // Error states
    'failed': () => '/plan',
    'error': () => '/plan',
    'unknown': () => '/plan',
  },
  
  execute: {
    'pre_migration': (flowId: string) => `/execute/pre-migration/${flowId}`,
    'migration_execution': (flowId: string) => `/execute/migration-execution/${flowId}`,
    'post_migration': (flowId: string) => `/execute/post-migration/${flowId}`,
    'completed': (flowId: string) => `/execute/summary/${flowId}`,
    
    // Error states
    'failed': () => '/execute',
    'error': () => '/execute',
    'unknown': () => '/execute',
  },
  
  modernize: {
    'modernization_assessment': (flowId: string) => `/modernize/assessment/${flowId}`,
    'architecture_design': (flowId: string) => `/modernize/architecture-design/${flowId}`,
    'implementation_planning': (flowId: string) => `/modernize/implementation-planning/${flowId}`,
    'completed': (flowId: string) => `/modernize/summary/${flowId}`,
    
    // Error states
    'failed': () => '/modernize',
    'error': () => '/modernize',
    'unknown': () => '/modernize',
  },
  
  finops: {
    'cost_analysis': (flowId: string) => `/finops/cost-analysis/${flowId}`,
    'budget_planning': (flowId: string) => `/finops/budget-planning/${flowId}`,
    'completed': (flowId: string) => `/finops/summary/${flowId}`,
    
    // Error states
    'failed': () => '/finops',
    'error': () => '/finops',
    'unknown': () => '/finops',
  },
  
  observability: {
    'monitoring_setup': (flowId: string) => `/observability/monitoring-setup/${flowId}`,
    'performance_optimization': (flowId: string) => `/observability/performance-optimization/${flowId}`,
    'completed': (flowId: string) => `/observability/summary/${flowId}`,
    
    // Error states
    'failed': () => '/observability',
    'error': () => '/observability',
    'unknown': () => '/observability',
  },
  
  decommission: {
    'decommission_planning': (flowId: string) => `/decommission/planning/${flowId}`,
    'data_migration': (flowId: string) => `/decommission/data-migration/${flowId}`,
    'system_shutdown': (flowId: string) => `/decommission/system-shutdown/${flowId}`,
    'completed': (flowId: string) => `/decommission/summary/${flowId}`,
    
    // Error states
    'failed': () => '/decommission',
    'error': () => '/decommission',
    'unknown': () => '/decommission',
  }
};

/**
 * Phase sequences for determining next phase - matches backend phase_sequences
 */
export const PHASE_SEQUENCES: Record<FlowType, string[]> = {
  discovery: ['data_import', 'attribute_mapping', 'data_cleansing', 'inventory', 'dependencies', 'tech_debt'],
  assessment: ['migration_readiness', 'business_impact', 'technical_assessment'],
  plan: ['wave_planning', 'runbook_creation', 'resource_allocation'],
  execute: ['pre_migration', 'migration_execution', 'post_migration'],
  modernize: ['modernization_assessment', 'architecture_design', 'implementation_planning'],
  finops: ['cost_analysis', 'budget_planning'],
  observability: ['monitoring_setup', 'performance_optimization'],
  decommission: ['decommission_planning', 'data_migration', 'system_shutdown']
};

/**
 * Get the appropriate route for any flow type and phase
 * @param flowType - The type of flow (discovery, assess, etc.)
 * @param phase - The current phase of the flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getFlowPhaseRoute(flowType: FlowType, phase: string, flowId: string): string {
  const flowRoutes = FLOW_PHASE_ROUTES[flowType];
  if (!flowRoutes) {
    console.warn(`Unknown flow type: ${flowType}, defaulting to home`);
    return '/';
  }
  
  const routeFunction = flowRoutes[phase];
  if (routeFunction) {
    return routeFunction(flowId);
  }
  
  // Default to flow type's error route
  const errorRoute = flowRoutes['unknown'] || flowRoutes['error'];
  if (errorRoute) {
    return errorRoute(flowId);
  }
  
  console.warn(`Unknown phase: ${phase} for flow type: ${flowType}`);
  return `/${flowType}`;
}

/**
 * Get discovery flow route (backward compatibility)
 * @param phase - The current phase of the discovery flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getDiscoveryPhaseRoute(phase: string, flowId: string): string {
  return getFlowPhaseRoute('discovery', phase, flowId);
}

/**
 * Determine if a phase requires flowId in the URL
 * @param flowType - The type of flow
 * @param phase - The phase to check
 * @returns true if the phase requires flowId in URL
 */
export function phaseRequiresFlowId(flowType: FlowType, phase: string): boolean {
  const noFlowIdPhases: Record<FlowType, string[]> = {
    discovery: [
      'initialization',
      'data_import_validation',
      'data_import',
      'failed',
      'error',
      'not_found',
      'unknown',
      'undefined',
      'current'
    ],
    assessment: ['failed', 'error', 'unknown'],
    plan: ['failed', 'error', 'unknown'],
    execute: ['failed', 'error', 'unknown'],
    modernize: ['failed', 'error', 'unknown'],
    finops: ['failed', 'error', 'unknown'],
    observability: ['failed', 'error', 'unknown'],
    decommission: ['failed', 'error', 'unknown']
  };
  
  return !(noFlowIdPhases[flowType] || []).includes(phase);
}

/**
 * Get next phase for a flow
 * @param flowType - The type of flow
 * @param currentPhase - The current phase
 * @returns The next phase or 'completed'
 */
export function getNextPhase(flowType: FlowType, currentPhase: string): string {
  const sequence = PHASE_SEQUENCES[flowType];
  if (!sequence) return 'completed';
  
  const currentIndex = sequence.indexOf(currentPhase);
  if (currentIndex === -1 || currentIndex === sequence.length - 1) {
    return 'completed';
  }
  
  return sequence[currentIndex + 1];
}

/**
 * Determine flow type from current path
 * @param pathname - The current pathname
 * @returns The flow type or null
 */
export function getFlowTypeFromPath(pathname: string): FlowType | null {
  if (pathname.includes('/discovery/')) return 'discovery';
  if (pathname.includes('/assess/')) return 'assessment';
  if (pathname.includes('/plan/')) return 'plan';
  if (pathname.includes('/execute/')) return 'execute';
  if (pathname.includes('/modernize/')) return 'modernize';
  if (pathname.includes('/finops/')) return 'finops';
  if (pathname.includes('/observability/')) return 'observability';
  if (pathname.includes('/decommission/')) return 'decommission';
  return null;
}

/**
 * Get flow information from the backend flow state
 * MFO-086: Updated to use Master Flow Orchestrator API
 */
export async function getFlowInfo(flowId: string): Promise<{ flowType: FlowType; currentPhase: string } | null> {
  try {
    // Import FlowService dynamically to avoid circular dependencies
    const { FlowService } = await import('../../frontend/src/services/FlowService');
    const flowService = FlowService.getInstance();
    
    const flowStatus = await flowService.getFlowStatus(flowId);
    
    return {
      flowType: flowStatus.flow_type as FlowType,
      currentPhase: flowStatus.current_phase || 'unknown'
    };
  } catch (error) {
    console.error('Failed to get flow info:', error);
    return null;
  }
}

/**
 * Master flow dashboard route
 * MFO-086: Add route for unified flow dashboard
 */
export const MASTER_FLOW_DASHBOARD_ROUTE = '/flows';

/**
 * Get dashboard route for a specific flow type
 * MFO-086: Support flow type specific dashboards
 */
export function getFlowDashboardRoute(flowType?: FlowType): string {
  if (!flowType) return MASTER_FLOW_DASHBOARD_ROUTE;
  return `/${flowType}`;
}