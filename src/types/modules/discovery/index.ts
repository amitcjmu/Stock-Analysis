/**
 * Discovery Flow - Module Index
 * 
 * Centralized exports for all Discovery Flow type modules.
 * Provides a clean interface for importing Discovery Flow types throughout the application.
 * 
 * Generated with CC - Code Companion
 */

// Base types and foundational interfaces
export * from './base-types';

// React component prop interfaces
export * from './component-types';

// React hook interfaces and return types
export * from './hook-types';

// API request and response interfaces
export * from './api-types';

// Core business data models
export * from './data-models';

// Validation and business rule types
export * from './validation-types';

// Create the Discovery Flow namespace for backwards compatibility
import { Components } from './component-types';
import { Hooks } from './hook-types';
import { API } from './api-types';
import * as Models from './data-models';

/**
 * Discovery Flow namespace declaration for backwards compatibility
 */
export declare namespace DiscoveryFlow {
  export import Components = Components;
  export import Hooks = Hooks;
  export import API = API;
  export namespace Models {
    export type FieldMapping = Models.FieldMapping;
    export type CriticalAttribute = Models.CriticalAttribute;
    export type CrewAnalysis = Models.CrewAnalysis;
    export type MappingProgress = Models.MappingProgress;
    export type FlowState = Models.FlowState;
    export type DiscoveryFlowData = Models.DiscoveryFlowData;
    export type DataImport = Models.DataImport;
    export type AgentClarification = Models.AgentClarification;
    export type TrainingProgress = Models.TrainingProgress;
    export type MappingFilter = Models.MappingFilter;
    export type FieldMappingInput = Models.FieldMappingInput;
    export type BulkMappingUpdate = Models.BulkMappingUpdate;
    export type MappingApprovalStatus = Models.MappingApprovalStatus;
    export type AnalysisFinding = Models.AnalysisFinding;
  }
}

/**
 * Re-export Discovery Flow Types namespace for easier access
 */
export namespace DiscoveryFlowTypes {
  export import Models = DiscoveryFlow.Models;
  export import Components = DiscoveryFlow.Components;
  export import Hooks = DiscoveryFlow.Hooks;
  export import API = DiscoveryFlow.API;
}