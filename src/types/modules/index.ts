/**
 * TypeScript Module Boundaries & Namespace Organization
 *
 * This file defines the module namespace organization for the AI Stock Assess Platform.
 * It provides clear architectural boundaries and enhanced type safety across the codebase.
 */

// Core namespace declarations
export type * from './discovery';
export type * from './assessment';
export type * from './planning';
export type * from './execution';
export type * from './modernize';
export type * from './finops';
export type * from './observability';
export type * from './decommission';

// Shared module types
export type * from './shared';

// Global module augmentations
export type * from './globals';

// Module type utilities
export type * from './utilities';

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
