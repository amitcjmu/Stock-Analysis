/**
 * Shared Types Index
 * 
 * Central export point for all shared type definitions used across the
 * AI agent swarm ESLint compliance project.
 */

// Metadata types
export type {
  BaseMetadata,
  AuditableMetadata,
  DomainMetadata
} from './metadata-types';

// API types  
export type {
  ApiResponse,
  ApiError,
  ResponseMetadata
} from './api-types';

// Configuration types
export type {
  ConfigurationValue,
  ConfigurationObject,
  TypedConstraint,
  ConfigurationCriteria
} from './config-types';

// Analysis types
export type {
  AnalysisResult,
  CostAnalysis,
  CostBreakdownItem,
  RiskAnalysis,
  RiskFactor,
  TimelineAnalysis,
  TimelineMilestone
} from './analysis-types';

// Form types
export type {
  FormFieldValue,
  ValidationResult,
  FormFieldConfig,
  FormState,
  FormHookConfig
} from './form-types';