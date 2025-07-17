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

// Module boundary enforcement
declare global {
  namespace MigrationPlatform {
    namespace Modules {
      namespace Discovery {
        // Discovery module types are defined in ./discovery.ts
      }
      
      namespace Assessment {
        // Assessment module types are defined in ./assessment.ts
      }
      
      namespace Planning {
        // Planning module types are defined in ./planning.ts
      }
      
      namespace Execution {
        // Execution module types are defined in ./execution.ts
      }
      
      namespace Modernize {
        // Modernize module types are defined in ./modernize.ts
      }
      
      namespace FinOps {
        // FinOps module types are defined in ./finops.ts
      }
      
      namespace Observability {
        // Observability module types are defined in ./observability.ts
      }
      
      namespace Decommission {
        // Decommission module types are defined in ./decommission.ts
      }
    }
  }
}