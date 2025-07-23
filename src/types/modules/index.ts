/**
 * TypeScript Module Boundaries & Namespace Organization
 * 
 * This file defines the module namespace organization for the AI Modernize Migration Platform.
 * It provides clear architectural boundaries and enhanced type safety across the codebase.
 */

// Core namespace declarations
export * from './discovery';
export * from './assessment';
export * from './planning';
export * from './execution';
export * from './modernize';
export * from './finops';
export * from './observability';
export * from './decommission';

// Shared module types
export * from './shared';

// Global module augmentations
export * from './globals';

// Module type utilities
export * from './utilities';

// Re-export existing types with namespace organization
export type {
  FlowType,
  FlowStatusType,
  PhaseStatusType,
  FlowConfiguration,
  FlowStatus,
  FlowPerformance,
  FlowError,
  FlowWarning,
  AgentCollaboration,
  CreateFlowRequest,
  ExecutePhaseRequest,
  FlowAnalytics,
  FlowUIState,
  FlowFilters,
  FlowSortOrder,
  FlowPagination,
  FlowCardProps,
  FlowListProps,
  FlowDetailsProps,
  FlowCreationProps,
  FlowTemplate,
  UseFlowReturn,
  UseFlowsReturn,
  ApiResponse,
  ApiError,
  PaginatedResponse,
  FlowEvent,
  ValidationResult,
  PhaseValidation,
  ValidationRule,
  FlowTypeConfig,
  FlowActionType,
  FlowPermission
} from '../flow';

