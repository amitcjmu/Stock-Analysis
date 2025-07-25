/**
 * Platform Types - CC type definitions for the migration platform
 */

// Module type references
export type DiscoveryFlow = import('./modules/discovery').DiscoveryFlow;
export type FlowOrchestration = import('./modules/flow-orchestration').FlowOrchestration;
export type SharedUtilities = import('./modules/shared-utilities').SharedUtilities;

// Component type references
export type NavigationComponents = typeof import('./components/navigation');
export type DiscoveryComponents = typeof import('./components/discovery');
export type SharedComponents = typeof import('./components/shared');
export type FormComponents = typeof import('./components/forms');
export type LayoutComponents = typeof import('./components/layout');
export type DataDisplayComponents = typeof import('./components/data-display');
export type FeedbackComponents = typeof import('./components/feedback');
export type AdminComponents = typeof import('./components/admin');

// Hook type references
export type DiscoveryHooks = typeof import('./hooks/discovery');
export type SharedHooks = typeof import('./hooks/shared');
export type APIHooks = typeof import('./hooks/api');
export type StateManagementHooks = typeof import('./hooks/state-management');
export type FlowOrchestrationHooks = typeof import('./hooks/flow-orchestration');
export type AdminHooks = typeof import('./hooks/admin');

// API type references
export type DiscoveryAPI = typeof import('./api/discovery');
export type AssessmentAPI = typeof import('./api/assessment');
export type PlanningAPI = typeof import('./api/planning');
export type ExecutionAPI = typeof import('./api/execution');
export type ModernizeAPI = typeof import('./api/modernize');
export type FinOpsAPI = typeof import('./api/finops');
export type ObservabilityAPI = typeof import('./api/observability');
export type DecommissionAPI = typeof import('./api/decommission');
export type AdminAPI = typeof import('./api/admin');
export type AuthAPI = typeof import('./api/auth');
export type SharedAPI = typeof import('./api/shared');

// Utility types
export type TypeGuards = typeof import('./guards');
export type ModuleBoundaries = typeof import('./index').MODULE_BOUNDARIES;
